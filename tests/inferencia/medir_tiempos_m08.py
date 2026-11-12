"""M0-08: mide el p95 del ejecutor en el Mac y escribe backlog/slice-m0/evidencia/m0-08_tiempos.md.

    uv run python tests/inferencia/medir_tiempos_m08.py [repeticiones]

Método: un pool precalentado (spawn, el de `curados/inferencia/parametros.yaml`); cada caso se corre una vez de descarte y luego N veces;
el tiempo es el de pared de `pool.ejecutar(tarea)` (viaje de la tarea, lectura en el trabajador, estimación y viaje del resultado). El pico de
memoria es `ru_maxrss` del trabajador tras cada caso (normalizado a bytes)."""
import dataclasses
import platform
import statistics
import sys
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1])]          # tests/ (para `conftest` y el paquete `inferencia`)

from conftest import RAIZ_REAL                                     # noqa: E402
from inferencia import equivalencia_m0 as eq                       # noqa: E402
from inferencia.pool_tareas import ConPico, Responder             # noqa: E402
from inferencia.recetas_m0 import plan_anemia                      # noqa: E402
from inferencia.sintetico_ejecutor import FuenteSintetica          # noqa: E402
from pap.inferencia.ejecutor import Ejecutor, FuenteMemoria, ParametrosEjecutor, PoolEjecutor, Tarea   # noqa: E402
from pap.inferencia.verificador import Contexto, Falla, verificar  # noqa: E402

SALIDA = RAIZ_REAL / "backlog" / "slice-m0" / "evidencia" / "m0-08_tiempos.md"


def p95(xs):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, math.ceil(0.95 * len(xs)) - 1)]


import math  # noqa: E402


def medir(pool, tarea, n):
    pool.ejecutar(ConPico(tarea))                                  # descarte
    tiempos, pico, resultado = [], 0, None
    for _ in range(n):
        t0 = time.monotonic()
        resultado, _dentro, rss = pool.ejecutar(ConPico(tarea))
        tiempos.append(time.monotonic() - t0)
        pico = max(pico, rss)
    return tiempos, pico, resultado


def marcos_apilados(nino, anios):
    """endes_nino por departamento × área (≈ 48 dominios por año); la UPM estable es la del diseño."""
    out = {}
    for a in anios:
        m = eq.marco(nino, a, "departamento")
        out[a] = m.with_columns(territorio=m["territorio"] + "-" + _area(nino, a), upm_estable=m["upm"])
    return out


def _area(nino, a):
    import polars as pl

    return pl.Series(nino[nino.anio == a].reset_index(drop=True).area.astype(str).to_list())


def main(n: int) -> None:
    ctx = Contexto.cargar(RAIZ_REAL)
    ex = Ejecutor(relaciones=[])
    nino = eq.leer_endes_nino()
    p = ParametrosEjecutor.desde_yaml()
    casos = []
    pc = verificar(plan_anemia("departamento", cortes=("area", "sexo")), ctx)
    assert not isinstance(pc, Falla), pc
    fuente, enc, anios, por, cats = ex.preparar({2024: pc}, ctx)
    for etiqueta, k in (("microdatos 2024, 27 dominios (≈ 25: 3 departamentos × 9 de área × sexo)", 3),
                        ("microdatos 2024, 99 dominios (≈ 100: 11 departamentos × 9 de área × sexo)", 11)):
        ids = tuple(f"{i:02d}" for i in range(1, 26) if i != 7)[:k]
        casos.append((etiqueta, Tarea(fuente, (2024,), por, {**cats, "territorio": ids}), 1))
    for anios_ in ((2023, 2024), (2021, 2022, 2023, 2024)):
        marcos = marcos_apilados(nino, anios_)
        casos.append((f"endes_nino {anios_[0]}–{anios_[-1]} apilados ({len(anios_)} años, departamento × área)",
                      Tarea(FuenteMemoria(marcos), anios_, apilado=True), len(anios_)))
    casos.append(("sintético, 275 dominios en una llamada (220 000 filas)", Tarea(FuenteSintetica(), (2024,)), 1))

    filas = []
    for etiqueta, tarea, _ in casos:
        # Un pool nuevo por caso: ru_maxrss es el máximo histórico del proceso, y así el pico es el de ese caso. El tope de memoria se
        # sube para medir (el sintético de 275 dominios llega a ≈ 1,4 GB, cerca del tope de 1 536 MB): lo medido va en el informe.
        with PoolEjecutor(dataclasses.replace(p, memoria_trabajador_mb=4096), RAIZ_REAL) as pool:
            pool.ejecutar(Responder())
            print("caso:", etiqueta, flush=True)
            ts, pico, res = medir(pool, tarea, n)
            filas.append((etiqueta, len(res), n, statistics.median(ts), p95(ts), max(ts), pico / 1024 ** 2))
            print(filas[-1], flush=True)
    SALIDA.write_text(redactar(filas, n, p), encoding="utf-8")


def redactar(filas, n, p) -> str:
    r = [f"# M0-08 — Tiempos del ejecutor en el Mac", "",
         f"Medido el {time.strftime('%d/%m/%Y')} en {platform.platform()} ({platform.machine()}), Python {platform.python_version()}, "
         f"`svy` 0.35.0. **Linux: pendiente** (no se pudo correr aquí).", "",
         "**Método.** Pool precalentado (spawn) con los valores de `curados/inferencia/parametros.yaml` "
         f"(`ejecutor.*`: {p.trabajadores} trabajador, DuckDB `threads={p.duckdb_threads}` y `memory_limit={p.duckdb_memoria_mb}MB`, "
         "`POLARS_MAX_THREADS=RAYON_NUM_THREADS=1`). Cada caso: una corrida de descarte y luego "
         f"{n} repeticiones; tiempo de pared de `pool.ejecutar(tarea)` (envío de la tarea, lectura de los datos en el trabajador, "
         "estimación con `svy` y retorno de las `Estimacion`). Los casos de microdatos pasan por DuckDB endurecido → `.arrow()` → "
         "`pl.from_arrow`; los de `endes_nino` y el sintético arman el marco en memoria. El pico es el `ru_maxrss` del trabajador; "
         "cada caso corre en un pool nuevo (con el tope subido a 4 096 MB solo para medir; el vigente es "
         f"{p.memoria_trabajador_mb} MB).", "",
         "| Caso | Dominios devueltos | Rep. | p50 (s) | p95 (s) | máx. (s) | Pico de memoria (MB) |", "|---|---:|---:|---:|---:|---:|---:|"]
    for etiqueta, dom, rep, p50, q95, mx, pico in filas:
        r.append(f"| {etiqueta} | {dom} | {rep} | {p50:.3f} | {q95:.3f} | {mx:.3f} | {pico:.0f} |")
    return "\n".join(r) + "\n"


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20)
