"""Ciclo por bloque del almacén de crudos (diseño del motor §6, M0-11): restaurar y liberar.

Un bloque es una encuesta y un año (`endes-2024`). Sus recursos son los de la fuente `INEI-<ENCUESTA>` cuyo nombre
empieza por `<encuesta>-<anio>-`. El respaldo vive en el release `crudos-<encuesta>-<anio>` del repo PRIVADO
`almacen.repo_crudos` (lo sube `scripts/respaldar_crudos.sh`).

- `restaurar` baja el release a un directorio temporal, comprueba SHA256SUMS y las huellas de los datapackage.json,
  reconvierte un archivo del manifiesto de microdatos y exige la misma `huella_contenido_v1`. Solo entonces marca el
  bloque como `respaldado` en `almacen_zst.json` (clave `bloques`), con la fecha, la URL del release y las huellas
  comprobadas. Los objetos del bloque que falten en el almacén (liberados) se vuelven a poner, ya comprobados.
- `liberar` borra del almacén solo los ZIP de un bloque `respaldado` cuya huella se comprobó al restaurar. Nunca toca
  los ZIP que lee `pap calcular`, ni los objetos que comparte otro recurso, ni nada que no sea un ZIP del almacén
  (Parquet, manifiesto, datapackage.json, insumos.lock.yaml, indice.duckdb, crudos de otras fuentes).

El token de `gh` (variable GH_TOKEN o Llavero de macOS) nunca se imprime.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import almacen, bitacora, capturas
from .config import Rutas
from .errores import PapError
from .util import ahora, escribir_json, leer_json

RAIZ_REPO = Path(__file__).resolve().parents[2]
RUTA_PARAMETROS = RAIZ_REPO / "curados" / "inferencia" / "parametros.yaml"
LLAVERO_SERVICIO = "pap-gh-crudos"
# ZIP que lee el motor actual (`pap calcular`, capa0/encuestas.py): nunca se liberan, de ningún año ni captura.
PROTEGIDOS_CALCULAR = (re.compile(r"^endes-\d{4}-(hogar|anemia)$"), re.compile(r"^enaho-\d{4}-sumaria$"))
SIN_SUMA = {"SHA256SUMS", "LEEME.txt"}


@dataclass(frozen=True)
class Bloque:
    encuesta: str   # ENDES
    anio: int

    @classmethod
    def desde_texto(cls, txt: str) -> "Bloque":
        m = re.fullmatch(r"([a-z]+)-(\d{4})", (txt or "").strip().lower())
        if not m:
            raise PapError(f"bloque {txt!r}: debe ser <encuesta>-<anio>, p. ej. endes-2024")
        return cls(m.group(1).upper(), int(m.group(2)))

    @property
    def id(self) -> str:
        return f"{self.encuesta.lower()}-{self.anio}"

    @property
    def fuente(self) -> str:
        return f"INEI-{self.encuesta}"

    @property
    def prefijo(self) -> str:
        return f"{self.id}-"

    @property
    def etiqueta(self) -> str:
        return f"crudos-{self.id}"


# ------------------------------------------------------------------ parámetros y registro

def parametro_almacen(clave: str, ruta: Path = RUTA_PARAMETROS):
    return yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))["almacen"][clave]["valor"]


def leer_bloques(rutas: Rutas) -> dict:
    p = almacen.ruta_registro(rutas)
    return (leer_json(p).get("bloques") or {}) if p.exists() else {}


def _escribir_bloque(rutas: Rutas, bloque_id: str, datos: dict) -> None:
    p = almacen.ruta_registro(rutas)
    reg = leer_json(p) if p.exists() else {}
    bloques = dict(reg.get("bloques") or {})
    bloques[bloque_id] = datos
    reg["bloques"] = dict(sorted(bloques.items()))
    reg.setdefault("objetos", {})
    escribir_json(p, reg)


def recursos_bloque(rutas: Rutas, b: Bloque) -> list[dict]:
    """Última captura de cada recurso del bloque, por nombre."""
    ultimos: dict[str, dict] = {}
    for _, rec in capturas.recursos(rutas, b.fuente):
        if rec.get("name", "").startswith(b.prefijo):
            ultimos[rec["name"]] = rec
    return [ultimos[k] for k in sorted(ultimos)]


def _hex(rec: dict) -> str:
    return rec["hash"].split(":", 1)[1]


def protegido_por_calcular(nombre: str) -> bool:
    return any(p.match(nombre) for p in PROTEGIDOS_CALCULAR)


def espacio_libre_gb(rutas: Rutas) -> float:
    return shutil.disk_usage(rutas.cruda if rutas.cruda.exists() else rutas.raiz).free / 1e9


def aviso_espacio(rutas: Rutas) -> str | None:
    minimo = float(parametro_almacen("espacio_libre_min_gb"))
    libre = espacio_libre_gb(rutas)
    if libre < minimo:
        return (f"Aviso: quedan {libre:.1f} GB libres, menos que el mínimo de {minimo:g} GB "
                f"(almacen.espacio_libre_min_gb).")
    return None


# ------------------------------------------------------------------ gh

def _token() -> str:
    tok = os.environ.get("GH_TOKEN", "").strip()
    if not tok and shutil.which("security"):
        r = subprocess.run(["security", "find-generic-password", "-s",
                            os.environ.get("PAP_LLAVERO_SERVICIO", LLAVERO_SERVICIO), "-w"],
                           capture_output=True, text=True)
        tok = r.stdout.strip() if r.returncode == 0 else ""
    if not tok:
        raise PapError("Falta GH_TOKEN (variable de entorno o Llavero de macOS; K-09).")
    return tok


def _gh(args: list[str], token: str) -> str:
    r = subprocess.run(["gh", *args], capture_output=True, text=True, env={**os.environ, "GH_TOKEN": token})
    if r.returncode != 0:
        err = r.stderr.replace(token, "***").strip()[-400:]
        raise PapError(f"gh {' '.join(args[:2])} falló: {err}")
    return r.stdout.replace(token, "***")


def _repo_privado(repo_pedido: str | None) -> tuple[str, str]:
    repo = parametro_almacen("repo_crudos")
    if repo_pedido and repo_pedido != repo:
        raise PapError(f"Me niego: el repo pedido ({repo_pedido}) no es el configurado ({repo}).")
    token = _token()
    vis = _gh(["repo", "view", repo, "--json", "visibility", "-q", ".visibility"], token).strip().upper()
    if vis != "PRIVATE":
        raise PapError(f"Me niego: {repo} no es privado (visibilidad: {vis or 'desconocida'}).")
    return repo, token


# ------------------------------------------------------------------ restaurar

def _sha256_partes(rutas_: list[Path]) -> str:
    h = hashlib.sha256()
    for p in rutas_:
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
    return h.hexdigest()


def _comprobar_sumas(d: Path) -> list[str]:
    sumas = d / "SHA256SUMS"
    if not sumas.exists():
        raise PapError("el release no trae SHA256SUMS")
    malos = []
    listados = set()
    for linea in sumas.read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        h, nombre = linea.split(None, 1)
        nombre = nombre.lstrip("*")
        listados.add(nombre)
        f = d / nombre
        if not f.exists() or _sha256_partes([f]) != h:
            malos.append(nombre)
    sin_listar = sorted(p.name for p in d.iterdir() if p.is_file() and p.name not in listados | SIN_SUMA)
    return malos + [f"{n} (no está en SHA256SUMS)" for n in sin_listar]


def _archivos_del_recurso(d: Path, rec: dict) -> list[Path]:
    f = d / rec["original_filename"]
    return [f] if f.exists() else sorted(d.glob(glob_escape(rec["original_filename"]) + ".parte-*"))


def glob_escape(s: str) -> str:
    return re.sub(r"([*?\[])", r"[\1]", s)


def _reponer_liberados(rutas: Rutas, d: Path, recs: list[dict]) -> list[dict]:
    """Vuelve a poner en el almacén los objetos del bloque que faltan (liberados), ya comprobados contra su huella."""
    repuestos = []
    for rec in recs:
        h = _hex(rec)
        if almacen.existe(rutas, h):
            continue
        destino = rutas.cruda / almacen.ruta_relativa(h)
        destino.parent.mkdir(parents=True, exist_ok=True)
        tmp = destino.with_name(destino.name + ".tmp")
        with open(tmp, "wb") as out:
            for parte in _archivos_del_recurso(d, rec):
                with open(parte, "rb") as f:
                    shutil.copyfileobj(f, out)
        if _sha256_partes([tmp]) != h:
            tmp.unlink()
            raise PapError(f"{rec['name']}: el archivo repuesto no da su huella")
        os.replace(tmp, destino)
        repuestos.append(rec)
    return repuestos


def _elegir_reconversion(rutas: Rutas, b: Bloque, por_hash: dict[str, dict]) -> tuple[str, dict]:
    from .inferencia.almacen import carpeta_salida

    man = carpeta_salida(rutas, b.encuesta, b.anio) / "manifiesto.json"
    if not man.exists():
        raise PapError(f"no hay manifiesto de microdatos en {man}: convierta el bloque antes de respaldarlo")
    archivos = leer_json(man).get("archivos") or {}
    opciones = sorted(((v.get("filas", 0), k, v) for k, v in archivos.items()
                       if (v.get("origen") or {}).get("zip_sha256") in por_hash), key=lambda t: (t[0], t[1]))
    if not opciones:
        raise PapError("ningún archivo del manifiesto sale de un ZIP del bloque")
    _, nombre, info = opciones[0]
    return nombre, info


def _reconvertir(d: Path, b: Bloque, nombre: str, info: dict, rec: dict, trabajo: Path) -> str:
    from .inferencia.almacen import Parametros, convertir_archivo, huella_contenido_v1
    from .zip_seguro import abrir_zip_seguro

    zip_ = trabajo / "unido.zip"
    with open(zip_, "wb") as out:
        for parte in _archivos_del_recurso(d, rec):
            with open(parte, "rb") as f:
                shutil.copyfileobj(f, out)
    miembro = info["origen"]["miembro"]
    formato = Path(miembro).suffix.lower().lstrip(".")
    entrada = trabajo / f"entrada.{formato}"
    with abrir_zip_seguro(zip_) as z, open(entrada, "wb") as f:
        z.copiar(miembro, f)
    salida = trabajo / f"{nombre}.parquet"
    convertir_archivo(entrada, salida, anio=b.anio, formato=formato, p=Parametros.desde_yaml())
    return huella_contenido_v1(salida)


def restaurar(rutas: Rutas, bloque: str, repo_pedido: str | None = None, emitir=print) -> dict:
    """Prueba la restauración del bloque. Devuelve el registro del bloque si todo cuadra; si no, lanza PapError."""
    b = Bloque.desde_texto(bloque)
    recs = recursos_bloque(rutas, b)
    if not recs:
        raise PapError(f"no hay recursos {b.prefijo}* registrados en {b.fuente}")
    repo, token = _repo_privado(repo_pedido)
    try:
        with tempfile.TemporaryDirectory(prefix="pap-restaurar-") as tmp:
            d = Path(tmp) / "release"
            d.mkdir()
            _gh(["release", "download", b.etiqueta, "--repo", repo, "--dir", str(d)], token)
            malos = _comprobar_sumas(d)
            if malos:
                raise PapError("SHA256SUMS no cuadra: " + ", ".join(malos))
            emitir(f"SHA256SUMS: OK ({len([p for p in d.iterdir() if p.name not in SIN_SUMA])} archivos)")
            fallos = []
            for rec in recs:
                partes = _archivos_del_recurso(d, rec)
                if not partes:
                    fallos.append(f"{rec['name']} (falta en el release)")
                    emitir(f"FALTA      {rec['name']}  {rec['original_filename']}")
                    continue
                ok = _sha256_partes(partes) == _hex(rec)
                emitir(f"{'OK' if ok else 'DIFERENTE':<10} {rec['name']}  {rec['original_filename']}")
                if not ok:
                    fallos.append(rec["name"])
            if fallos:
                raise PapError("la restauración no cuadra con los datapackage.json: " + ", ".join(fallos))
            por_hash = {_hex(r): r for r in recs}
            repuestos = _reponer_liberados(rutas, d, recs)
            for rec in repuestos:
                emitir(f"Repuesto en el almacén: {rec['name']}  {rec['original_filename']}")
            nombre, info = _elegir_reconversion(rutas, b, por_hash)
            trabajo = Path(tmp) / "trabajo"
            trabajo.mkdir()
            h = _reconvertir(d, b, nombre, info, por_hash[info["origen"]["zip_sha256"]], trabajo)
            igual = h == info.get("huella_contenido_v1")
            emitir(f"Reconversión de {nombre} ({info['origen']['miembro']}): huella_contenido_v1 "
                   f"{'igual' if igual else 'DIFERENTE'} a la del manifiesto ({h[:16]}…)")
            if not igual:
                raise PapError(f"{nombre}: la huella_contenido_v1 reconvertida no es la del manifiesto")
        url = _gh(["release", "view", b.etiqueta, "--repo", repo, "--json", "url", "-q", ".url"], token).strip()
    except PapError as e:
        bitacora.anotar(rutas, b.fuente, "restaurar", "fallo", detalle=f"{b.id}: {e}")
        raise
    datos = {"estado": "respaldado", "fecha": ahora(), "release": url, "etiqueta": b.etiqueta, "repo": repo,
             "huellas": sorted(por_hash),
             "reconvertido": {"archivo": nombre, "huella_contenido_v1": h}}
    previo = leer_bloques(rutas).get(b.id) or {}
    if "liberado" in previo:
        datos["liberado"] = previo["liberado"]
    _escribir_bloque(rutas, b.id, datos)
    bitacora.anotar(rutas, b.fuente, "restaurar", "ok",
                    detalle=f"{b.id}: {len(recs)} recursos, reconvertido {nombre}; {url}")
    emitir(f"Bloque {b.id} marcado como respaldado ({url}).")
    return datos


# ------------------------------------------------------------------ liberar

@dataclass
class Plan:
    liberar: list[tuple[dict, Path, int]]
    se_quedan: list[tuple[dict, str]]

    @property
    def bytes(self) -> int:
        return sum(t[2] for t in self.liberar)


def planear_liberacion(rutas: Rutas, bloque: str) -> tuple[Bloque, Plan]:
    b = Bloque.desde_texto(bloque)
    estado = leer_bloques(rutas).get(b.id) or {}
    if estado.get("estado") != "respaldado" or not (estado.get("reconvertido") or {}).get("huella_contenido_v1"):
        raise PapError(f"el bloque {b.id} no está respaldado con la restauración probada: "
                       f"corra antes `pap almacen restaurar --bloque {b.id}`")
    comprobadas = set(estado.get("huellas") or [])
    recs = recursos_bloque(rutas, b)
    # Huellas que usa cualquier recurso de fuera del bloque (otra fuente u otro año): ese objeto no se borra.
    otros = {_hex(rec) for _, rec in capturas.recursos(rutas)
             if not (rec.get("name", "").startswith(b.prefijo) and rec.get("source_id") == b.fuente)}
    plan = Plan([], [])
    for rec in recs:
        h = _hex(rec)
        if (rec.get("format") or "").lower() != "zip":
            plan.se_quedan.append((rec, "no es un ZIP"))
        elif protegido_por_calcular(rec["name"]):
            plan.se_quedan.append((rec, "lo lee `pap calcular`"))
        elif h not in comprobadas:
            plan.se_quedan.append((rec, "su huella no se comprobó al restaurar"))
        elif h in otros:
            plan.se_quedan.append((rec, "lo usa otro recurso"))
        else:
            p = almacen.ruta_objeto(rutas, h)
            dentro = p.resolve().is_relative_to(rutas.almacen.resolve())
            if not dentro:
                plan.se_quedan.append((rec, "fuera del almacén"))
            elif not p.exists():
                plan.se_quedan.append((rec, "ya liberado"))
            else:
                plan.liberar.append((rec, p, p.stat().st_size))
    return b, plan


def liberar(rutas: Rutas, bloque: str, *, ejecutar: bool = False, confirmar=None, emitir=print) -> Plan:
    """Con `ejecutar=False` (por defecto) solo muestra el plan. `confirmar()` debe devolver True para borrar."""
    b, plan = planear_liberacion(rutas, bloque)
    for rec, p, n in plan.liberar:
        emitir(f"liberaría  {rec['name']:<34} {rec['original_filename']:<28} {n / 1e6:9.1f} MB")
    for rec, motivo in plan.se_quedan:
        emitir(f"se queda   {rec['name']:<34} {rec['original_filename']:<28} ({motivo})")
    emitir(f"Total: {len(plan.liberar)} ZIP, {plan.bytes / 1e6:.1f} MB.")
    if not ejecutar:
        emitir("Simulación: no se borró nada. Para liberar: --ejecutar.")
    elif not plan.liberar:
        emitir("Nada que liberar.")
    elif not (confirmar and confirmar()):
        raise PapError("liberación no confirmada: no se borró nada")
    else:
        borrados = 0
        for rec, p, n in plan.liberar:
            p.unlink()
            borrados += n
            bitacora.anotar(rutas, rec.get("source_id"), "liberar", "ok", hash=rec["hash"],
                            detalle=f"{b.id}: {rec['original_filename']} ({n} bytes); respaldo en "
                                    f"{leer_bloques(rutas)[b.id].get('release')}")
        estado = leer_bloques(rutas)[b.id]
        estado["liberado"] = {"fecha": ahora(), "archivos": len(plan.liberar), "bytes": borrados}
        _escribir_bloque(rutas, b.id, estado)
        emitir(f"Liberados {len(plan.liberar)} ZIP ({borrados / 1e6:.1f} MB). Para volver a convertir el bloque: "
               f"pap almacen restaurar --bloque {b.id}.")
    aviso = aviso_espacio(rutas)
    if aviso:
        emitir(aviso)
    return plan


def confirmar_por_terminal(b: str) -> bool:
    if not sys.stdin.isatty():
        return False
    return input(f"Escriba «liberar {b}» para confirmar: ").strip() == f"liberar {b}"
