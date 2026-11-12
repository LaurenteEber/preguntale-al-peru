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


# ---- M1-02, tarea 1 (H08-1): el plazo cuenta desde que el trabajador está listo; y el vigía de memoria bajo presión

def test_el_arranque_lento_de_un_trabajador_nuevo_no_cuenta_contra_el_plazo_de_la_tarea():
    """El trabajador se reemplaza cada 2 tareas y cada arranque tarda 2,5 s a propósito (más que timeout + gracia = 2 s): ninguna
    tarea trivial puede fallar por «tiempo». No depende de la velocidad de la máquina: el retraso lo pone la prueba."""
    p = dataclasses.replace(PARAMETROS, max_tareas_por_trabajador=2)
    with PoolEjecutor(p, RAIZ_REAL, retraso_arranque_s=2.5) as pool:
        pids = [pool.ejecutar(Responder(i))[1] for i in range(4)]
    assert len(set(pids)) >= 2


def test_con_un_arranque_lento_el_tiempo_suave_y_el_duro_siguen_cortando_a_tiempo_y_el_trabajador_nuevo_tambien_queda_listo():
    with PoolEjecutor(PARAMETROS, RAIZ_REAL, retraso_arranque_s=2.5) as pool:
        pool.ejecutar(Responder())
        dt = _falla(pool, DormirPython(30), "tiempo")
        assert TIMEOUT <= dt < TIMEOUT + 1                                # cuenta desde que la tarea empieza, no desde el arranque
        dt = _falla(pool, Tarea(FuenteSintetica(), (2024,)), "tiempo", tope=TIMEOUT + GRACIA + 1)
        assert dt <= TIMEOUT + GRACIA + 1
        assert _sigue_funcionando(pool) is not None


@pytest.mark.skipif(sys.platform != "darwin", reason="huella física de macOS")
def test_la_memoria_del_vigia_en_macos_incluye_la_huella_fisica_y_la_ve_crecer():
    from pap.inferencia.ejecutor import _huella_fisica_macos, _memoria_bytes

    antes = _huella_fisica_macos()
    assert 10 * 1024 * 1024 < antes < 64 * 1024 ** 3
    grande = bytearray(b"\x01") * (300 * 1024 * 1024)                   # tocado: cuenta en la huella aunque el sistema lo comprima
    assert _huella_fisica_macos() - antes > 250 * 1024 * 1024
    assert _memoria_bytes() >= _huella_fisica_macos() - 50 * 1024 * 1024
    del grande


def test_la_memoria_del_vigia_es_la_mayor_de_las_medidas_aunque_el_pico_residente_quede_bajo(monkeypatch):
    """Bajo presión de memoria, `ru_maxrss` puede quedar por debajo de lo que el proceso realmente usa: manda la otra medida."""
    import pap.inferencia.ejecutor as ej

    monkeypatch.setattr("pap.inferencia.lector_aislado._rss_max_bytes", lambda: 100 * 1024 * 1024)
    monkeypatch.setattr(ej, "_huella_fisica_macos", lambda: 5000 * 1024 * 1024)
    monkeypatch.setattr(ej, "_memoria_en_uso_linux", lambda: 5000 * 1024 * 1024)
    if sys.platform in ("darwin", "linux"):
        assert ej._memoria_bytes() == 5000 * 1024 * 1024
    monkeypatch.setattr(ej, "_huella_fisica_macos", lambda: 0)
    monkeypatch.setattr(ej, "_memoria_en_uso_linux", lambda: 0)
    assert ej._memoria_bytes() == 100 * 1024 * 1024


def test_el_vigia_corta_al_trabajador_cuando_la_medida_pasa_el_tope_sin_depender_de_la_carga_de_la_maquina(monkeypatch):
    import pap.inferencia.ejecutor as ej

    salidas = []

    def salir(codigo):
        salidas.append(codigo)
        raise SystemExit                                              # termina el bucle del vigía, no el intérprete de la prueba

    monkeypatch.setattr(ej.os, "_exit", salir)
    medidas = iter([10, 20, 2000, 3000])
    with pytest.raises(SystemExit):
        ej._vigia(1000, 0, medir=lambda: next(medidas))
    assert salidas == [ej.SALIDA_MEMORIA]
    assert list(medidas) == [3000]                                    # cortó en la tercera medida, no antes ni después
