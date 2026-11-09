"""Ejecutor del motor de inferencia (M0-08; diseño §14 y §21, `tecnologias.md` §4).

Dos capas:
1. **El cálculo** (`Tarea`): DuckDB endurecido → `.arrow()` → `polars.from_arrow` → `svy_adaptador`. Un nulo de `y` dentro de `u` es un
   error interno (se registra y se detiene). Con varios años, según `relacion_entre_anios.csv`: `independiente` = un cálculo por año;
   `conglomerados_repetidos` / `panel_parcial` = un solo `Sample` apilado, con la UPM estable y el estrato común.
2. **El pool** (`PoolEjecutor`): cada tarea corre en un proceso trabajador (`spawn`, `max_tasks_per_child`, precalentado).
   - tiempo **suave**: `signal.alarm(ejecutor_timeout_s)` dentro del trabajador (corta el código de Python);
   - tiempo **duro**: las señales no cortan el código nativo (`svy`, DuckDB), así que si no hay resultado en
     `ejecutor_timeout_s + ejecutor_gracia_s` el padre mata al trabajador y recrea el pool;
   - **memoria**: un hilo vigía dentro del trabajador hace `os._exit(137)` si `ru_maxrss` pasa `memoria_trabajador_mb`
     (bytes en macOS, KiB en Linux; `_rss_max_bytes` ya lo normaliza). No se usa `RLIMIT_AS` (tecnologias.md §4);
   - **hilos**: `POLARS_MAX_THREADS`, `RAYON_NUM_THREADS` (y los de BLAS) en 1 antes de importar `polars`, `duckdb` o `svy`; este
     módulo importa solo la biblioteca estándar arriba, y el iniciador del trabajador los fija antes que nada; DuckDB con
     `threads=1` y `memory_limit` propios.
   Todo fallo del pool es un `ErrorTemporal` (`causa`: `tiempo`, `memoria` o `caida`) y la tarea siguiente funciona.

`Ejecutor` une las dos: parte la llamada por bloques de dominios y la reintenta **una vez** si se excede el tiempo o la memoria.
Sin pool corre en el mismo proceso (para pruebas y desarrollo; sin aislamiento).
"""
from __future__ import annotations

import itertools
import logging
import math
import os
import signal
import threading
import time
from concurrent.futures import ProcessPoolExecutor, TimeoutError as TiempoAgotado
from concurrent.futures.process import BrokenProcessPool
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Mapping, Protocol, Sequence

import yaml

from ..errores import PapError
from ..zip_seguro import RUTA_PARAMETROS
from .estimacion import Estimacion

if TYPE_CHECKING:
    import polars as pl

    from .plan import PlanCompleto
    from .verificador import Contexto

RAIZ_REPO = Path(__file__).resolve().parents[3]
LOG = logging.getLogger("pap.inferencia.ejecutor")
SALIDA_MEMORIA = 137                      # código de salida del vigía (convención de «matado por memoria»)
VARIABLES_HILOS = ("POLARS_MAX_THREADS", "RAYON_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                   "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")
RELACIONES_APILADAS = ("conglomerados_repetidos", "panel_parcial")


# ------------------------------------------------------------------ errores

class ErrorEjecutor(PapError):
    """Un fallo del ejecutor. `codigo` lo traduce a texto de la persona quien lo muestra (M0-09/M1); `detalle` es técnico."""
    codigo = "ejecutor"

    def __init__(self, detalle: str):
        super().__init__(detalle)
        self.detalle = detalle


class ErrorInterno(ErrorEjecutor):
    """Error nuestro (p. ej. un nulo de `y` dentro de `u`, §14): «Algo salió mal de nuestro lado…». Siempre queda registrado."""
    codigo = "interno"


class ErrorTemporal(ErrorEjecutor):
    """Se excedió el tiempo o la memoria, o el trabajador cayó: «Inténtalo de nuevo en un momento»."""
    codigo = "temporal"

    def __init__(self, causa: str, detalle: str):
        super().__init__(detalle)
        self.causa = causa                # tiempo | memoria | caida


# ------------------------------------------------------------------ parámetros

@dataclass(frozen=True)
class ParametrosEjecutor:
    """`ejecutor.*` de curados/inferencia/parametros.yaml (ningún valor fijo en el código)."""
    timeout_s: float
    gracia_s: float
    memoria_trabajador_mb: int
    max_tareas_por_trabajador: int
    trabajadores: int
    duckdb_threads: int
    duckdb_memoria_mb: int
    vigia_sondeo_s: float
    arranque_max_s: float

    @classmethod
    def desde_yaml(cls, ruta: Path = RUTA_PARAMETROS) -> "ParametrosEjecutor":
        c = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))["ejecutor"]
        v = lambda k: c[k]["valor"]
        return cls(float(v("ejecutor_timeout_s")), float(v("ejecutor_gracia_s")), int(v("memoria_trabajador_mb")),
                   int(v("max_tareas_por_trabajador")), int(v("trabajadores")), int(v("duckdb_threads")), int(v("duckdb_memoria_mb")),
                   float(v("vigia_sondeo_s")), float(v("arranque_max_s")))


# ------------------------------------------------------------------ fuentes de datos

class Fuente(Protocol):
    """De dónde sale el marco de un año: columnas `u`, `y`, `peso`, `estrato`, `upm` y las de dominio (`territorio`, `corte_<id>`…)."""

    def cargar(self, anio: int, *, upm_estable: bool = False) -> "pl.DataFrame": ...


# La conexión DuckDB del proceso: la crea el iniciador del trabajador (con sus topes) o, sin pool, la primera lectura.
_ESTADO: dict = {"con": None, "clave": None, "p": None}


def _conexion(raiz: Path, carpetas: Sequence[Path] | None = None):
    """La conexión endurecida del proceso. En un trabajador usa los topes de `ejecutor.*` (los fija `_iniciar_trabajador`)."""
    clave = (str(raiz), tuple(str(c) for c in carpetas) if carpetas else None)
    if _ESTADO["con"] is None or _ESTADO["clave"] != clave:
        from .duckdb_seguro import conexion_segura

        _ESTADO["con"] = conexion_segura(raiz, p=_ESTADO["p"], carpetas=list(carpetas) if carpetas else None)
        _ESTADO["clave"] = clave
    return _ESTADO["con"]


@dataclass(frozen=True)
class FuenteSql:
    """Consultas compiladas por la gramática (el SQL ya con parámetros), una por año. El trabajador las corre en su conexión endurecida.
    `estables`: las mismas con la UPM estable (`upm_estable_expr`), para apilar años."""
    consultas: Mapping[int, tuple[str, list]]
    estables: Mapping[int, tuple[str, list]] = field(default_factory=dict)
    raiz: Path = RAIZ_REPO
    carpetas: tuple[Path, ...] | None = None          # solo pruebas: carpetas permitidas distintas de las del YAML

    def cargar(self, anio: int, *, upm_estable: bool = False):
        import polars as pl

        sql, parametros = (self.estables if upm_estable else self.consultas)[anio]
        df = pl.from_arrow(_conexion(self.raiz, self.carpetas).execute(sql, parametros).arrow())
        # Un corte numérico llega como «1.0» si la columna es DOUBLE: se deja en «1», como las categorías del plan.
        return df.with_columns([pl.col(c).str.replace(r"\.0$", "") for c in df.columns if c.startswith("corte_")])


@dataclass(frozen=True)
class FuenteMemoria:
    """Marcos ya armados (pruebas y datos fuera de la biblioteca). Con `upm_estable`, usa la columna `upm_estable` si la trae."""
    marcos: Mapping[int, "pl.DataFrame"]

    def cargar(self, anio: int, *, upm_estable: bool = False):
        df = self.marcos[anio]
        return df.drop("upm").rename({"upm_estable": "upm"}) if upm_estable and "upm_estable" in df.columns else df


# ------------------------------------------------------------------ la tarea

@dataclass(frozen=True)
class Tarea:
    """Un cálculo completo. Es invocable sin argumentos: así el pool corre lo mismo en el trabajador que en el proceso."""
    fuente: Fuente
    anios: tuple[int, ...]
    por: tuple[str, ...] = ("territorio",)
    categorias: Mapping[str, tuple[str, ...] | None] = field(default_factory=dict)    # columna → valores pedidos; None = los observados
    apilado: bool = False                      # un solo Sample con todos los años (UPM estable) o un año
    bloque: tuple[int, int] | None = None      # (i, k): solo el i-ésimo de k bloques contiguos de los dominios pedidos (llamada partida)

    def __call__(self) -> list[Estimacion]:
        import polars as pl

        from .svy_adaptador import estimar_proporciones

        marcos = []
        for a in self.anios:
            df = self.fuente.cargar(a, upm_estable=self.apilado and len(self.anios) > 1)
            self._revisar_y(df, a)
            falta = ["faltante"] if "faltante" in df.columns else []
            marcos.append(df.select(["u", "y", "peso", "estrato", "upm", *self.por, *falta]).with_columns(pl.lit(str(a)).alias("anio")))
        multi = self.apilado and len(self.anios) > 1
        marco = pl.concat(marcos, how="vertical_relaxed") if multi else marcos[0]
        por = (("anio", *self.por) if multi else self.por)

        valores = []
        for c in self.por:
            pedidos = self.categorias.get(c)
            valores.append(tuple(sorted(marco[c].drop_nulls().unique().cast(pl.String).to_list())) if pedidos is None else tuple(pedidos))
        anios = [str(a) for a in self.anios] if multi else [None]
        dominios = [(a, *d) if a else d for a in anios for d in itertools.product(*valores)]
        solo = None
        if self.bloque is not None:
            i, k = self.bloque
            solo = dominios[i * len(dominios) // k:(i + 1) * len(dominios) // k]
        elif any(self.categorias.get(c) is not None for c in self.por):
            solo = dominios                 # dominios fijados por quien llama: solo esos entran al `where` (el marco queda entero)
        res = estimar_proporciones(marco, por, dominios, faltante="faltante" if "faltante" in marco.columns else None, solo=solo,
                                   anio=None if multi else self.anios[0])
        return [replace(e, anio=int(e.dominio[0]), dominio=e.dominio[1:]) for e in res] if multi else res

    @staticmethod
    def _revisar_y(df, anio: int) -> None:
        import polars as pl

        malos = df.filter(pl.col("u").fill_null(False) & pl.col("y").is_null()).height
        if malos:
            LOG.error("error interno: %d filas de u con y nulo en el año %s (un nulo de y dentro de u es un error del índice, §14)", malos, anio)
            raise ErrorInterno(f"{malos} filas de u con y nulo en {anio}")

    def partir(self) -> tuple["Tarea", "Tarea"]:
        i, k = self.bloque or (0, 1)
        return replace(self, bloque=(2 * i, 2 * k)), replace(self, bloque=(2 * i + 1, 2 * k))


# ------------------------------------------------------------------ el trabajador

class _AlarmaSuave(BaseException):
    """La señal de `signal.alarm` llegó mientras corría código de Python. BaseException: ningún `except Exception` la traga."""


@dataclass(frozen=True)
class ConfigTrabajador:
    raiz: Path
    memoria_mb: int
    duckdb_memoria_mb: int
    duckdb_threads: int
    sondeo_s: float
    calentar: bool = True


def _vigia(limite_bytes: int, sondeo_s: float) -> None:
    from .lector_aislado import _rss_max_bytes          # ru_maxrss normalizado a bytes (macOS: bytes; Linux: KiB)

    while True:
        time.sleep(sondeo_s)
        if _rss_max_bytes() > limite_bytes:
            os._exit(SALIDA_MEMORIA)


def _iniciar_trabajador(cfg: ConfigTrabajador) -> None:
    """`initializer` del pool: hilos, vigía de memoria y precalentamiento (importar `svy` y abrir DuckDB)."""
    for v in VARIABLES_HILOS:
        os.environ[v] = "1"                              # antes de importar polars, duckdb y svy
    threading.Thread(target=_vigia, args=(cfg.memoria_mb * 1024 * 1024, cfg.sondeo_s), daemon=True, name="vigia-memoria").start()
    if not cfg.calentar:
        return
    import pyarrow
    import polars as pl

    pyarrow.set_cpu_count(1)
    from .duckdb_seguro import ParametrosDuckdb
    from .svy_adaptador import estimar_proporciones

    base = ParametrosDuckdb.desde_yaml()
    _ESTADO["p"] = replace(base, memoria_mb=cfg.duckdb_memoria_mb, threads=cfg.duckdb_threads)
    _conexion(cfg.raiz).execute("SELECT 1").arrow()
    marco = pl.DataFrame({"u": [True] * 8, "y": [0, 1] * 4, "peso": [1.0] * 8, "estrato": ["a"] * 4 + ["b"] * 4,
                          "upm": ["1", "1", "2", "2", "3", "3", "4", "4"], "t": ["x"] * 8})
    estimar_proporciones(marco, ["t"], [("x",)])


def _correr(trabajo, timeout_s: float):
    """Corre `trabajo()` con el tiempo suave. Devuelve (etiqueta, valor): los errores viajan como datos, no como excepciones."""
    def alarma(_signum, _frame):
        raise _AlarmaSuave()

    signal.signal(signal.SIGALRM, alarma)
    signal.alarm(max(1, math.ceil(timeout_s)))
    try:
        return ("ok", trabajo())
    except _AlarmaSuave:
        return ("tiempo", None)
    except ErrorInterno as e:
        return ("interno", e.detalle)
    except Exception as e:                                # noqa: BLE001 — lo que no esperamos también es un error interno
        LOG.exception("error inesperado en el trabajador")
        return ("interno", f"{type(e).__name__}: {e}")
    finally:
        signal.alarm(0)


def _ping() -> int:
    return os.getpid()


# ------------------------------------------------------------------ el pool

class PoolEjecutor:
    """Pool de procesos trabajadores con tiempo suave y duro, vigía de memoria y recreación tras cada fallo."""

    def __init__(self, p: ParametrosEjecutor | None = None, raiz: Path = RAIZ_REPO, *, calentar: bool = True):
        self.p = p or ParametrosEjecutor.desde_yaml()
        self.cfg = ConfigTrabajador(Path(raiz), self.p.memoria_trabajador_mb, self.p.duckdb_memoria_mb, self.p.duckdb_threads,
                                    self.p.vigia_sondeo_s, calentar)
        self._lock = threading.Lock()
        self._cupo = threading.BoundedSemaphore(self.p.trabajadores)     # el tiempo duro cuenta desde que hay un trabajador libre
        self._generacion = 0
        self._pool: ProcessPoolExecutor | None = None
        self._calentando: list = []
        self._crear()

    # -- ciclo de vida
    def _crear(self) -> None:
        import multiprocessing

        self._pool = ProcessPoolExecutor(max_workers=self.p.trabajadores, mp_context=multiprocessing.get_context("spawn"),
                                         max_tasks_per_child=self.p.max_tareas_por_trabajador, initializer=_iniciar_trabajador,
                                         initargs=(self.cfg,))
        self._calentando = [self._pool.submit(_ping) for _ in range(self.p.trabajadores)]      # arranca los procesos y corre el iniciador

    def _esperar_calentamiento(self) -> None:
        pendientes, self._calentando = self._calentando, []
        for f in pendientes:
            try:
                f.result(timeout=self.p.arranque_max_s)
            except (TiempoAgotado, BrokenProcessPool) as e:
                raise ErrorTemporal("caida", f"el pool no arrancó en {self.p.arranque_max_s} s: {type(e).__name__}") from e

    def _retirar(self, generacion: int) -> list | None:
        """Mata el pool de esa generación y crea otro. None si otro hilo ya lo hizo. Devuelve los procesos del pool viejo."""
        with self._lock:
            if generacion != self._generacion:
                return None
            self._generacion += 1                         # antes de matar: los demás hilos ven que el fallo ya se atendió
            viejo = self._pool
            procesos = list(getattr(viejo, "_processes", {}).values())      # atributo privado: Python 3.12 no trae terminate_workers()
            for pr in procesos:
                if pr.is_alive():
                    pr.kill()
            viejo.shutdown(wait=False, cancel_futures=True)
            for pr in procesos:
                pr.join(2)
            self._crear()
            return procesos

    def cerrar(self) -> None:
        with self._lock:
            self._generacion += 1
            viejo, self._pool = self._pool, None
        if viejo is not None:
            procesos = list(getattr(viejo, "_processes", {}).values())
            for pr in procesos:
                if pr.is_alive():
                    pr.kill()
            viejo.shutdown(wait=False, cancel_futures=True)
            for pr in procesos:
                pr.join(2)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cerrar()

    # -- ejecución
    def ejecutar(self, trabajo):
        """Corre `trabajo()` en un trabajador. Devuelve su resultado, o levanta `ErrorTemporal` / `ErrorInterno`."""
        with self._cupo:
            for intento in (0, 1):
                with self._lock:
                    generacion, pool = self._generacion, self._pool
                if pool is None:
                    raise ErrorTemporal("caida", "el pool está cerrado")
                try:
                    self._esperar_calentamiento()
                except ErrorTemporal:
                    self._retirar(generacion)
                    raise
                inicio = time.monotonic()
                try:
                    futuro = pool.submit(_correr, trabajo, self.p.timeout_s)
                    etiqueta, valor = futuro.result(timeout=self.p.timeout_s + self.p.gracia_s)
                except TiempoAgotado:
                    self._retirar(generacion)
                    raise ErrorTemporal("tiempo", f"sin resultado en {time.monotonic() - inicio:.1f} s: trabajador terminado") from None
                except BrokenProcessPool:
                    procesos = self._retirar(generacion)
                    if procesos is None:                 # otro hilo mató el pool (su tiempo duro): esta tarea no tuvo la culpa
                        if intento == 0:
                            continue
                        raise ErrorTemporal("caida", "el pool se recreó dos veces seguidas") from None
                    codigos = [pr.exitcode for pr in procesos]
                    if SALIDA_MEMORIA in codigos:
                        raise ErrorTemporal("memoria", f"el trabajador pasó {self.p.memoria_trabajador_mb} MB (salida {SALIDA_MEMORIA})") from None
                    raise ErrorTemporal("caida", f"el trabajador cayó (códigos de salida {codigos})") from None
                if etiqueta == "ok":
                    return valor
                if etiqueta == "tiempo":
                    raise ErrorTemporal("tiempo", f"excedió {self.p.timeout_s:g} s (tiempo suave)")
                LOG.error("error interno en el trabajador: %s", valor)
                raise ErrorInterno(str(valor))


# ------------------------------------------------------------------ el ejecutor

def grupos_de_anios(encuesta: str, anios: Sequence[int], relaciones) -> list[tuple[int, ...]]:
    """Agrupa los años de la llamada según `relacion_entre_anios.csv`: años consecutivos con relación `conglomerados_repetidos` o
    `panel_parcial` van en un mismo grupo (un `Sample` apilado); el resto, cada uno aparte. Un par sin fila es `independiente` (§7.4)."""
    rel = {(r.anio_a, r.anio_b): r.relacion for r in relaciones if r.encuesta == encuesta}
    grupos: list[list[int]] = []
    for a in sorted(set(anios)):
        if grupos and rel.get((grupos[-1][-1], a), "independiente") in RELACIONES_APILADAS:
            grupos[-1].append(a)
        else:
            grupos.append([a])
    return [tuple(g) for g in grupos]


class Ejecutor:
    """Calcula las proporciones de un plan. Sin `pool` corre en este proceso (sin aislamiento ni tiempos)."""

    def __init__(self, pool: PoolEjecutor | None = None, *, relaciones=None, raiz: Path = RAIZ_REPO):
        self.pool, self.raiz = pool, Path(raiz)
        if relaciones is None:
            from .tablas_curadas import leer_relacion_entre_anios

            relaciones = leer_relacion_entre_anios(self.raiz)
        self.relaciones = relaciones

    def _correr(self, tarea: Tarea) -> list[Estimacion]:
        if self.pool is not None:
            return self.pool.ejecutar(tarea)
        return tarea()

    def _con_reintento(self, tarea: Tarea) -> list[Estimacion]:
        """Si se excede el tiempo o la memoria, se parte en dos bloques de dominios y se reintenta una vez (no hay segundo nivel)."""
        try:
            return self._correr(tarea)
        except ErrorTemporal as e:
            if e.causa not in ("tiempo", "memoria"):
                raise
            LOG.warning("llamada partida tras exceder %s (%s); se reintenta una vez", e.causa, e.detalle)
        salida = []
        for mitad in tarea.partir():
            salida += self._correr(mitad)
        return salida

    def estimar(self, fuente: Fuente, encuesta: str, anios: Sequence[int], *, por: Sequence[str] = ("territorio",),
                categorias: Mapping[str, tuple[str, ...] | None] | None = None) -> list[Estimacion]:
        """`independiente`: una tarea por año, resultados unidos. `conglomerados_repetidos`: una tarea con los años apilados."""
        salida: list[Estimacion] = []
        for grupo in grupos_de_anios(encuesta, anios, self.relaciones):
            salida += self._con_reintento(Tarea(fuente, grupo, tuple(por), dict(categorias or {}), apilado=len(grupo) > 1))
        return salida

    def preparar(self, planes: Mapping[int, "PlanCompleto"], ctx: "Contexto", *, carpetas: Sequence[Path] | None = None):
        """Compila el plan de cada año (`planes`: año → plan completo, el mismo plan). Devuelve lo que pide `estimar`:
        (fuente, encuesta, años, columnas de dominio, categorías pedidas)."""
        from .gramatica import compilar

        anios = sorted(planes)
        primero = planes[anios[0]]
        sin_dato = ctx.p.corte_sin_dato
        consultas, estables = {}, {}
        for a in anios:
            pc = planes[a]
            c = compilar(pc, ctx.esquema, ctx.carpeta_microdatos, sin_dato=sin_dato)
            consultas[a] = (c.sql, c.parametros)
            if len(anios) > 1:
                pe = replace(pc, diseno=pc.diseno.model_copy(update={"psu_expr": pc.diseno.upm_estable_expr}))
                ce = compilar(pe, ctx.esquema, ctx.carpeta_microdatos, sin_dato=sin_dato)
                estables[a] = (ce.sql, ce.parametros)
        categorias = {"territorio": (primero.plan.territorio.id,) if primero.plan.territorio.id is not None else None}
        for c in primero.cortes:
            categorias["corte_" + c.id] = tuple(sorted({str(k) for k in c.categorias} | {sin_dato}))
        por = ("territorio", *("corte_" + c.id for c in primero.cortes))
        fuente = FuenteSql(consultas, estables, self.raiz, tuple(carpetas) if carpetas else None)
        return fuente, primero.plan.encuesta, anios, por, categorias

    def ejecutar(self, planes: Mapping[int, "PlanCompleto"], ctx: "Contexto", *, carpetas: Sequence[Path] | None = None) -> list[Estimacion]:
        """Compila y calcula el plan. En M0 el verificador solo deja pasar un año; con más, los planes por año los arma quien llama."""
        fuente, encuesta, anios, por, categorias = self.preparar(planes, ctx, carpetas=carpetas)
        return self.estimar(fuente, encuesta, anios, por=por, categorias=categorias)
