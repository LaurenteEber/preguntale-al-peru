"""M0-11 (tarea 3): mediciones del ejecutor que faltaban en M0-08. Imprime una tabla en Markdown.

    uv run python tests/inferencia/medir_m11.py [repeticiones]

1. Tiempo real de `ejecutor_gracia_s`: una llamada nativa de `svy` más larga que tiempo suave + gracia; se mide cuánto pasa
   desde el tiempo suave hasta que el padre devuelve la falla `tiempo` (trabajador muerto). Gracia = la de producción;
   tiempo suave = 1 s para no esperar 5 s por repetición (la gracia no depende del tiempo suave).
2. DuckDB con `threads` 1 frente a 2 en el caso de 99 dominios de M0-08.
3. Memoria residente del pool en reposo (trabajador precalentado)."""
import dataclasses
import statistics
import sys
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1])]

from conftest import RAIZ_REAL                                     # noqa: E402
from inferencia.medir_tiempos_m08 import medir, p95                # noqa: E402
from inferencia.pool_tareas import ConPico, Responder             # noqa: E402
from inferencia.recetas_m0 import plan_anemia                      # noqa: E402
from inferencia.sintetico_ejecutor import FuenteSintetica          # noqa: E402
from pap.inferencia.ejecutor import ErrorTemporal, Ejecutor, ParametrosEjecutor, PoolEjecutor, Tarea   # noqa: E402
from pap.inferencia.verificador import Contexto, Falla, verificar  # noqa: E402


def gracia_real(p, n):
    q = dataclasses.replace(p, timeout_s=1, memoria_trabajador_mb=4096)
    larga = Tarea(FuenteSintetica(n_filas=264_000, n_dominios=330), (2024,))   # ≈ 5 s nativos: más que 1 + gracia
    tiempos = []
    with PoolEjecutor(q, RAIZ_REAL) as pool:
        pool.ejecutar(Responder())
        for _ in range(n):
            t0 = time.monotonic()
            try:
                pool.ejecutar(larga)
                raise AssertionError("la llamada larga no se cortó")
            except ErrorTemporal as e:
                assert e.causa == "tiempo", e.detalle
            tiempos.append(time.monotonic() - t0 - q.timeout_s)
            pool.ejecutar(Responder())                              # el pool se recreó y sigue funcionando
    return tiempos


def hilos(p, n):
    ctx = Contexto.cargar(RAIZ_REAL)
    ex = Ejecutor(relaciones=[])
    pc = verificar(plan_anemia("departamento", cortes=("area", "sexo")), ctx)
    assert not isinstance(pc, Falla), pc
    fuente, _enc, _anios, por, cats = ex.preparar({2024: pc}, ctx)
    ids = tuple(f"{i:02d}" for i in range(1, 26) if i != 7)[:11]
    tarea = Tarea(fuente, (2024,), por, {**cats, "territorio": ids})
    out = {}
    for t in (1, 2):
        with PoolEjecutor(dataclasses.replace(p, duckdb_threads=t, memoria_trabajador_mb=4096), RAIZ_REAL) as pool:
            pool.ejecutar(Responder())
            ts, pico, res = medir(pool, tarea, n)
            out[t] = (len(res), statistics.median(ts), p95(ts), pico / 1024 ** 2)
    return out


def reposo(p):
    with PoolEjecutor(p, RAIZ_REAL) as pool:
        pool.ejecutar(Responder())
        _r, _d, rss = pool.ejecutar(ConPico(Responder()))
    return rss / 1024 ** 2


def main(n: int) -> None:
    p = ParametrosEjecutor.desde_yaml()
    g = gracia_real(p, max(3, n // 4))
    print(f"## Gracia real (tiempo suave 1 s, gracia {p.gracia_s} s, {len(g)} repeticiones)\n")
    print(f"tiempo desde el suave hasta la falla: p50 {statistics.median(g):.2f} s, máx. {max(g):.2f} s "
          f"(gracia configurada {p.gracia_s} s)\n")
    h = hilos(p, n)
    print(f"## DuckDB threads 1 frente a 2 (99 dominios, {n} repeticiones)\n")
    print("| threads | dominios | p50 (s) | p95 (s) | pico (MB) |\n|---:|---:|---:|---:|---:|")
    for t, (dom, p50, q95, pico) in h.items():
        print(f"| {t} | {dom} | {p50:.3f} | {q95:.3f} | {pico:.0f} |")
    print(f"\n## Pool en reposo\n\nmemoria residente del trabajador precalentado: {reposo(p):.0f} MB")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20)
