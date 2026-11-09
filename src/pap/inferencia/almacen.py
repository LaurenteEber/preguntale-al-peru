"""Conversor y almacén de microdatos (M0-04; diseño §6, tecnologias.md §5).

No confundir con `pap.almacen`, que es el almacén de crudos: este guarda los microdatos ya convertidos, uno por
encuesta, año y archivo: `biblioteca/microdatos/{encuesta}/{anio}/{archivo}.parquet` más un `manifiesto.json` por año.

`pap microdatos convertir --encuesta ENDES --anio 2024` toma los ZIP registrados de `curados/inferencia/descargas/`,
los abre con `abrir_zip_seguro` (C7), lee cada SAV/DTA en un subproceso con topes de memoria, procesador y tiempo (C8;
`lector_aislado.py`) y deja el Parquet y el manifiesto. Al terminar agrega las huellas de los ZIP usados a
`curados/insumos.lock.yaml`.

**Manifiesto** (`archivos.<archivo>`): `origen` (ZIP, huella del ZIP, recurso y miembro), `huella_datos`,
`huella_contenido_v1`, `filas`, `columnas` (nombre, tipo, clase), `perdidos` (por columna: origen, códigos declarados y
cuántas veces apareció cada código; **de aquí lo toma M0-05** para `categorias.parquet`, `es_especial`), `versiones`
(pyreadstat, pyarrow, polars, duckdb, svy) y las mediciones (`rss_max_mb`, `segundos_conversion`, `segundos_huella`).

**Huellas.**
- `huella_datos` = sha256 de «huella del ZIP, miembro, versión del conversor». El diseño dice «ZIP + versión»; se agrega
  el miembro para que dos archivos del mismo ZIP no compartan identidad (la caché los confundiría).
- `huella_contenido_v1`: ver `huella_contenido_v1()`.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

import yaml

from ..config import Rutas
from ..errores import PapError
from ..util import ahora, sha256
from ..zip_seguro import RUTA_PARAMETROS, abrir_zip_seguro

VERSION_CONVERSOR = "1"      # súbela cuando el conversor cambie lo que escribe: cambia la huella_datos
MB = 1 << 20
RAIZ_REPO = Path(__file__).resolve().parents[3]
RUTA_CLASES = RAIZ_REPO / "curados" / "inferencia" / "clases_columnas.yaml"
PAQUETES = ("pyreadstat", "pyarrow", "polars", "duckdb", "svy")


class LectorAbortado(PapError):
    """El subproceso lector pasó uno de sus topes (memoria, procesador o tiempo) o murió."""


def versiones() -> dict[str, str]:
    return {p: metadata.version(p) for p in PAQUETES} | {"python": sys.version.split()[0]}


# ------------------------------------------------------------------ parámetros

@dataclass(frozen=True)
class Parametros:
    """`conversion.*` de curados/inferencia/parametros.yaml (ningún valor fijo en el código)."""
    as_mb: int
    cpu_s: int
    tiempo_s: float
    rss_max_mb: int
    sondeo_s: float
    criterio_rss_max_mb: int
    criterio_huella_s: float
    bloques_desde_mb: float
    bloques_filas: int
    codificacion_sin_declarar: str
    parquet_compresion: str
    parquet_nivel: int
    parquet_grupo_filas: int
    duckdb_memoria_mb: int
    espacio: str

    @classmethod
    def desde_yaml(cls, ruta: Path = RUTA_PARAMETROS) -> "Parametros":
        c = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))["conversion"]
        v = lambda k: c[k]["valor"]
        return cls(as_mb=int(v("lector_as_mb")), cpu_s=int(v("lector_cpu_s")), tiempo_s=float(v("lector_tiempo_s")),
                   rss_max_mb=int(v("lector_rss_max_mb")), sondeo_s=float(v("lector_sondeo_s")),
                   criterio_rss_max_mb=int(v("criterio_rss_max_mb")), criterio_huella_s=float(v("criterio_huella_s")),
                   bloques_desde_mb=float(v("bloques_desde_mb")), bloques_filas=int(v("bloques_filas")),
                   codificacion_sin_declarar=str(v("dta_codificacion_sin_declarar")),
                   parquet_compresion=str(v("parquet_compresion")), parquet_nivel=int(v("parquet_nivel")),
                   parquet_grupo_filas=int(v("parquet_grupo_filas")), duckdb_memoria_mb=int(v("duckdb_memoria_mb")),
                   espacio=str(v("nombre_parquet_espacio")))


# ------------------------------------------------------------------ huella de contenido

def _expr_celda(col: str, tipo: str) -> str:
    x = '"' + col.replace('"', '""') + '"'
    if tipo in ("DOUBLE", "FLOAT"):
        # -0.0 y 0.0 son la misma celda; todos los NaN, también (cada escritor guarda su propio NaN).
        return (f"CASE WHEN {x} IS NULL THEN chr(0) WHEN isnan({x}::DOUBLE) THEN 'nan' WHEN {x} = 0 THEN '0' "
                f"ELSE printf('%.17g', {x}::DOUBLE) END")
    return f"coalesce(CAST({x} AS VARCHAR), chr(0))"


def huella_contenido_v1(ruta: Path | str, con=None) -> str:
    """Huella de integridad de un Parquet que **no depende del escritor** (tecnologias.md §5).

    1. md5 de cada fila en forma canónica: columnas en orden alfabético, separador `\\x1f`, nulo como `\\x00`,
       decimales con `printf('%.17g')`, -0.0 como 0 y todo NaN como «nan»;
    2. se ordenan esos md5;
    3. sha256 del conjunto (los md5 unidos por salto de línea).
    No usa `hash()` de DuckDB, porque puede cambiar entre versiones. Se calcula sobre las filas, no sobre los nombres:
    los nombres y tipos van aparte en el manifiesto.
    """
    import duckdb

    c = con or duckdb.connect()
    ruta_sql = str(ruta).replace("'", "''")
    desc = c.execute(f"DESCRIBE SELECT * FROM read_parquet('{ruta_sql}')").fetchall()
    celdas = [_expr_celda(n, t) for n, t, *_ in sorted(desc, key=lambda d: d[0])]
    fila = "concat_ws(chr(31), " + ", ".join(celdas) + ")"
    r = c.execute(f"SELECT coalesce(sha256(string_agg(h, chr(10) ORDER BY h)), sha256('')) FROM "
                  f"(SELECT md5({fila}) AS h FROM read_parquet('{ruta_sql}'))").fetchone()
    return r[0]


# ------------------------------------------------------------------ ejecución aislada (C8)

def _poner_limites(as_mb: int, cpu_s: int) -> None:
    """En el subproceso, antes de ejecutar. RLIMIT_AS puede no existir o no hacerse cumplir (macOS): se intenta."""
    import resource

    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s + 5))      # SIGXCPU a los cpu_s; SIGKILL 5 s después
    try:
        resource.setrlimit(resource.RLIMIT_AS, (as_mb * MB, as_mb * MB))
    except (ValueError, OSError):
        pass


def _entorno() -> dict[str, str]:
    """El subproceso solo ve lo mínimo: ni claves ni variables del dueño."""
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
    return env


def _rss_kb(pid: int) -> int:
    r = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)], capture_output=True, text=True)
    try:
        return int(r.stdout.strip())
    except ValueError:
        return 0


@dataclass(frozen=True)
class Ejecucion:
    returncode: int
    stderr: str
    rss_sondeado_kb: int
    segundos: float


def ejecutar_aislado(cmd: list[str], p: Parametros, *, cwd: Path) -> Ejecucion:
    """Corre `cmd` con RLIMIT_AS y RLIMIT_CPU, un tope de tiempo de pared y un vigilante de memoria residente.

    El vigilante sondea el RSS del subproceso con `ps` (RLIMIT_AS no se hace cumplir en macOS). Si algún tope se pasa,
    mata el subproceso y lanza `LectorAbortado`."""
    with tempfile.TemporaryFile() as err:
        inicio = time.monotonic()
        proc = subprocess.Popen(cmd, cwd=cwd, env=_entorno(), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=err, close_fds=True, preexec_fn=lambda: _poner_limites(p.as_mb, p.cpu_s))
        rss_max, motivo = 0, None
        while True:
            try:
                proc.wait(timeout=p.sondeo_s)
                break
            except subprocess.TimeoutExpired:
                pass
            rss_max = max(rss_max, _rss_kb(proc.pid))
            if rss_max > p.rss_max_mb * 1024:
                motivo = f"memoria residente de {rss_max / 1024:.0f} MB sobre el tope de {p.rss_max_mb} MB"
            elif time.monotonic() - inicio > p.tiempo_s:
                motivo = f"más de {p.tiempo_s:g} s de tiempo"
            if motivo:
                proc.kill()
                proc.wait()
                raise LectorAbortado(f"lector abortado: {motivo}")
        err.seek(0)
        stderr = err.read().decode("utf-8", "replace")
    if proc.returncode == -signal.SIGXCPU or proc.returncode == -signal.SIGKILL:
        raise LectorAbortado(f"lector abortado: pasó el tope de {p.cpu_s} s de procesador (señal {-proc.returncode})")
    return Ejecucion(proc.returncode, stderr, rss_max, time.monotonic() - inicio)


def rlimit_as_se_aplica() -> bool:
    """¿El sistema hace cumplir RLIMIT_AS? Se prueba en un subproceso que intenta reservar 1 GB con un tope de 256 MB.
    En macOS da False: allí el único tope real de memoria es el vigilante de RSS de `ejecutar_aislado`."""
    codigo = ("import resource,mmap\n"
              "try:\n resource.setrlimit(resource.RLIMIT_AS,(256<<20,256<<20))\n"
              "except (ValueError,OSError):\n print('no'); raise SystemExit\n"
              "try:\n mmap.mmap(-1, 1<<30)\nexcept (MemoryError,OSError):\n print('si')\nelse:\n print('no')\n")
    r = subprocess.run([sys.executable, "-I", "-c", codigo], capture_output=True, text=True, timeout=60)
    return r.stdout.strip() == "si"


# ------------------------------------------------------------------ un archivo

def nombre_parquet(miembro: str, anio: int, espacio: str = "_") -> str:
    """`968-Modulo1629/RECH0_2024.dta` → `RECH0`; `…/Programas Sociales x Hogar_2024.dta` → `Programas_Sociales_x_Hogar`."""
    base = Path(miembro.replace("\\", "/")).stem
    base = re.sub(rf"_{anio}$", "", base)
    return base.replace(" ", espacio)


def convertir_archivo(entrada: Path, salida: Path, *, anio: int, formato: str, p: Parametros,
                      clases: Path = RUTA_CLASES) -> dict:
    """Lee `entrada` (SAV/DTA) en un subproceso aislado y escribe `salida` (Parquet). Devuelve el resultado del lector."""
    if formato not in ("dta", "sav"):
        raise PapError(f"formato no soportado: {formato!r}")
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    tmp_salida = salida.with_name(f".{salida.name}.tmp")
    with tempfile.TemporaryDirectory(prefix="pap-lector-") as d:
        d = Path(d)
        spec = {"entrada": str(entrada), "formato": formato, "salida": str(tmp_salida), "anio": anio,
                "clases": str(clases), "bloques_desde_bytes": int(p.bloques_desde_mb * MB),
                "bloques_filas": p.bloques_filas, "codificacion_sin_declarar": p.codificacion_sin_declarar,
                "parquet_compresion": p.parquet_compresion, "parquet_nivel": p.parquet_nivel,
                "parquet_grupo_filas": p.parquet_grupo_filas, "duckdb_memoria_mb": p.duckdb_memoria_mb,
                "base_temporal": str(d / "trabajo.duckdb"), "resultado": str(d / "resultado.json")}
        (d / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
        try:
            ej = ejecutar_aislado([sys.executable, "-I", "-m", "pap.inferencia.lector_aislado", str(d / "spec.json")],
                                  p, cwd=d)
            res_ruta = d / "resultado.json"
            res = json.loads(res_ruta.read_text(encoding="utf-8")) if res_ruta.exists() else {}
            if ej.returncode != 0 or "error" in res:
                raise PapError(f"{Path(entrada).name}: " + (res.get("error") or
                               f"el lector terminó con código {ej.returncode}: {ej.stderr.strip()[-600:]}"))
            os.replace(tmp_salida, salida)
        finally:
            tmp_salida.unlink(missing_ok=True)
    res["rss_max_mb"] = round(max(res["rss_max_bytes"], ej.rss_sondeado_kb * 1024) / MB, 1)
    return res


# ------------------------------------------------------------------ una encuesta y un año

def _insumo(rutas: Rutas, fuente: str, recurso: str):
    """Última captura del recurso, sin el filtro del lock: este comando es quien agrega al lock las huellas que usa."""
    from ..capa0 import insumos

    previo = insumos.ACTUALIZAR_LOCK
    insumos.ACTUALIZAR_LOCK = True
    try:
        return insumos.ultimo(rutas, fuente, recurso=recurso)
    finally:
        insumos.ACTUALIZAR_LOCK = previo


def carpeta_salida(rutas: Rutas, encuesta: str, anio: int) -> Path:
    return rutas.raiz / "biblioteca" / "microdatos" / encuesta / str(anio)


def convertir(rutas: Rutas, encuesta: str, anio: int, *, p: Parametros | None = None, log=print) -> dict:
    """Convierte todos los archivos de datos de los ZIP registrados de la encuesta y el año. Devuelve el manifiesto."""
    from ..capa0 import insumos

    p = p or Parametros.desde_yaml()
    lista = rutas.raiz / "curados" / "inferencia" / "descargas" / f"{encuesta.lower()}_{anio}.yaml"
    if not lista.exists():
        raise PapError(f"No hay lista de descargas para {encuesta} {anio}: falta {rutas.relativa(lista)}")
    cfg = yaml.safe_load(lista.read_text(encoding="utf-8"))
    fuente, destino = cfg["fuente"], carpeta_salida(rutas, encuesta, anio)
    destino.mkdir(parents=True, exist_ok=True)
    manifiesto = {"encuesta": encuesta, "anio": anio, "version_conversor": VERSION_CONVERSOR,
                  "generado": ahora(), "rlimit_as_aplicado": rlimit_as_se_aplica(), "archivos": {}}
    if not manifiesto["rlimit_as_aplicado"]:
        log("⚠ Este sistema no hace cumplir RLIMIT_AS: la memoria del lector la vigila el sondeo de RSS "
            f"(tope {p.rss_max_mb} MB).")
    usados = []
    for mod in cfg["modulos"]:
        ins = _insumo(rutas, fuente, mod["recurso"])
        if ins.ruta.suffix == ".zst":
            raise PapError(f"{ins.ruta.name}: el ZIP está comprimido con zstd; no es el caso esperado")
        if sha256(ins.ruta) != ins.hash.removeprefix("sha256:"):
            raise PapError(f"{mod['recurso']}: la huella del ZIP no coincide con la registrada; corre `pap verificar`")
        usados.append(ins)
        with abrir_zip_seguro(ins.ruta) as z, tempfile.TemporaryDirectory(prefix="pap-zip-") as d:
            datos = [m for m in z.miembros() if m.lower().endswith((".dta", ".sav"))]
            if not datos:
                raise PapError(f"{ins.original_filename}: el ZIP no trae ningún DTA ni SAV")
            for miembro in sorted(datos):
                nombre = nombre_parquet(miembro, anio, p.espacio)
                if nombre in manifiesto["archivos"]:
                    raise PapError(f"{miembro}: el nombre {nombre!r} ya lo usa otro archivo de {encuesta} {anio}")
                local = Path(d) / Path(miembro).name
                with open(local, "wb") as f:
                    z.copiar(miembro, f)
                res = convertir_archivo(local, destino / f"{nombre}.parquet", anio=anio,
                                        formato=miembro.rsplit(".", 1)[-1].lower(), p=p)
                local.unlink()
                zip_sha = ins.hash.removeprefix("sha256:")
                res["origen"] = {"zip": ins.original_filename, "zip_sha256": zip_sha, "recurso": ins.nombre,
                                 "miembro": miembro}
                res["huella_datos"] = hashlib.sha256(f"{zip_sha}\n{miembro}\n{VERSION_CONVERSOR}".encode()).hexdigest()
                res["parquet"] = f"{nombre}.parquet"
                res["huella_parquet"] = sha256(destino / f"{nombre}.parquet")   # solo integridad: cambia con el escritor
                res["n_columnas"] = len(res["columnas"])
                res.pop("rss_max_bytes")
                manifiesto["archivos"][nombre] = res
                log(f"✔ {nombre}: {res['filas']:,} filas × {res['n_columnas']} columnas, "
                    f"{res['bytes_parquet'] / MB:.1f} MB, RSS máx. {res['rss_max_mb']:.0f} MB, "
                    f"huella {res['segundos_huella']:.1f} s" + (" (por bloques)" if res["leido_en_bloques"] else ""))
                for tope, valor, limite, ud in (("RSS", res["rss_max_mb"], p.criterio_rss_max_mb, "MB"),
                                                ("huella", res["segundos_huella"], p.criterio_huella_s, "s")):
                    if valor >= limite:
                        log(f"  ⚠ criterio de M0-04 no cumplido en {nombre}: {tope} {valor:g} {ud} (límite {limite:g} {ud})")
    ruta_manifiesto = destino / "manifiesto.json"
    ruta_manifiesto.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                               encoding="utf-8")
    insumos.escribir_lock(rutas, usados)
    return manifiesto
