"""M0-08, tarea 4: el pool de procesos. Exceso de tiempo en Python, llamada nativa larga (275 dominios), exceso de memoria y
caída del trabajador: en cada caso un error controlado en ≤ timeout + 3 s y la tarea siguiente funciona.

Sin datos reales ni plataforma fija (macOS y Linux): la memoria se mide con `ru_maxrss` normalizado a bytes. Las corridas en
Linux están pendientes (el desarrollo fue en macOS); ver backlog/slice-m0/evidencia/m0-08_pool.md."""
import dataclasses
import sys
import time

import polars as pl
import pytest

from conftest import RAIZ_REAL
from pap.inferencia.ejecutor import Ejecutor, ErrorInterno, ErrorTemporal, FuenteMemoria, ParametrosEjecutor, PoolEjecutor, Tarea
from pap.inferencia.tablas_curadas import leer_relacion_entre_anios

from .pool_tareas import Caer, ConsumirMemoria, DormirPython, Responder, VerDuckdb, VerEntorno
from .sintetico_ejecutor import FuenteSintetica, marco_sintetico

TIMEOUT, GRACIA = 1, 1
MARGEN = 3.0                         # «error controlado en ≤ timeout + 3 s»
PARAMETROS = ParametrosEjecutor(timeout_s=TIMEOUT, gracia_s=GRACIA, memoria_trabajador_mb=3000, max_tareas_por_trabajador=200,
                                trabajadores=1, duckdb_threads=1, duckdb_memoria_mb=512, vigia_sondeo_s=0.05, arranque_max_s=120)


@pytest.fixture
def pool():
    with PoolEjecutor(PARAMETROS, RAIZ_REAL) as p:
        p.ejecutar(Responder())                           # precalentado: lo que se mide después no incluye el arranque
        yield p


def _falla(pool, trabajo, causa, tope=TIMEOUT + MARGEN):
    t0 = time.monotonic()
    with pytest.raises(ErrorTemporal) as e:
        pool.ejecutar(trabajo)
    dt = time.monotonic() - t0
    assert e.value.causa == causa, e.value.detalle
    assert dt <= tope, f"{dt:.2f} s > {tope} s"
    return dt


def _sigue_funcionando(pool, pid_anterior=None):
    valor, pid = pool.ejecutar(Responder(7))
    assert valor == 7
    return pid


def test_una_tarea_normal_vuelve_con_su_resultado(pool):
    assert pool.ejecutar(Responder(3))[0] == 3


def test_el_exceso_de_tiempo_en_python_lo_corta_la_alarma_suave_y_el_trabajador_sigue_vivo(pool):
    pid = pool.ejecutar(Responder())[1]
    dt = _falla(pool, DormirPython(30), "tiempo")
    assert TIMEOUT <= dt < TIMEOUT + 1                    # la alarma (tiempo suave) corta antes que el tiempo duro
    assert _sigue_funcionando(pool) == pid                # el mismo proceso: no hizo falta matarlo


def test_una_llamada_nativa_larga_de_275_dominios_la_corta_el_tiempo_duro_y_la_tarea_siguiente_funciona(pool):
    pid = pool.ejecutar(Responder())[1]
    larga = Tarea(FuenteSintetica(), (2024,))             # 220 000 filas × 275 dominios en una llamada (≈ 4 s en el Mac)
    dt = _falla(pool, larga, "tiempo")
    assert dt <= TIMEOUT + GRACIA + 1                     # el padre mató al trabajador: la señal no corta código nativo
    assert _sigue_funcionando(pool) != pid                # trabajador nuevo (el pool se recreó)


def test_el_exceso_de_memoria_lo_corta_el_vigia_y_la_tarea_siguiente_funciona():
    p = dataclasses.replace(PARAMETROS, timeout_s=4, gracia_s=2, memoria_trabajador_mb=1100)      # holgura: el vigía debe ganarle a la alarma
    with PoolEjecutor(p, RAIZ_REAL) as pool:
        pool.ejecutar(Responder())
        pid = pool.ejecutar(Responder())[1]
        _falla(pool, ConsumirMemoria(2000), "memoria", tope=4 + MARGEN)
        assert _sigue_funcionando(pool) != pid


def test_la_caida_del_trabajador_es_un_error_controlado_y_la_tarea_siguiente_funciona(pool):
    pid = pool.ejecutar(Responder())[1]
    _falla(pool, Caer(), "caida")
    assert _sigue_funcionando(pool) != pid


def test_un_error_de_la_tarea_no_mata_al_trabajador(pool):
    m = marco_sintetico(n_filas=500, n_dominios=3, semilla=1, n_estratos=4, upm_por_estrato=10)
    mal = m.with_columns(y=pl.when(pl.int_range(pl.len()) == 0).then(None).otherwise(pl.col("y")),
                         u=pl.when(pl.int_range(pl.len()) == 0).then(True).otherwise(pl.col("u")))
    pid = pool.ejecutar(Responder())[1]
    with pytest.raises(ErrorInterno, match="y nulo"):
        pool.ejecutar(Tarea(FuenteMemoria({2024: mal}), (2024,)))
    assert _sigue_funcionando(pool) == pid


def test_los_hilos_y_duckdb_del_trabajador_van_con_los_topes(pool):
    env, hilos_polars = pool.ejecutar(VerEntorno())
    assert env == {"POLARS_MAX_THREADS": "1", "RAYON_NUM_THREADS": "1"} and hilos_polars == 1
    threads, memoria = pool.ejecutar(VerDuckdb(str(RAIZ_REAL)))
    assert int(threads) == 1 and memoria == "488.2 MiB"            # 512 MB (decimales) = 488,2 MiB


def test_max_tasks_per_child_reemplaza_al_trabajador_y_el_pool_sigue():
    with PoolEjecutor(dataclasses.replace(PARAMETROS, max_tareas_por_trabajador=3), RAIZ_REAL) as pool:
        pids = [pool.ejecutar(Responder())[1] for _ in range(6)]
        assert len(set(pids)) >= 2 and all(isinstance(x, int) for x in pids)


def test_el_ejecutor_calcula_por_el_pool_lo_mismo_que_en_el_proceso(pool):
    relaciones = leer_relacion_entre_anios(RAIZ_REAL)
    fuente = FuenteMemoria({2024: marco_sintetico(n_filas=3000, n_dominios=4, semilla=2, n_estratos=5, upm_por_estrato=10)})
    local = Ejecutor(relaciones=relaciones).estimar(fuente, "ENDES", [2024])
    remoto = Ejecutor(pool, relaciones=relaciones).estimar(fuente, "ENDES", [2024])
    assert remoto == local and len(local) == 4


@pytest.mark.skipif(sys.platform not in ("darwin", "linux"), reason="macOS y Linux")
def test_ru_maxrss_se_normaliza_a_bytes_en_las_dos_plataformas():
    from pap.inferencia.lector_aislado import _rss_max_bytes

    rss = _rss_max_bytes()
    assert 10 * 1024 * 1024 < rss < 64 * 1024 ** 3        # un intérprete con pandas pesa decenas de MB: ni KiB leídos como bytes ni al revés
