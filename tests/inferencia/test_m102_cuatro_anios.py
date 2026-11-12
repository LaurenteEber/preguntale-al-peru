"""M1-02, tarea 2 (H08-2): el caso de 4 años apilados con 192 dominios por el pool, con los topes de `parametros.yaml`.
Corre igual en el Mac y en Linux (imagen Docker): sin ErrorTemporal, 192 dominios y el pico de memoria bajo el tope del vigía."""
import polars as pl

from conftest import RAIZ_REAL

from . import equivalencia_m0 as eq
from .pool_tareas import ConPico, Responder
from pap.inferencia.ejecutor import FuenteMemoria, ParametrosEjecutor, PoolEjecutor, Tarea

ANIOS = (2021, 2022, 2023, 2024)


def _marcos(nino):
    out = {}
    for a in ANIOS:
        m = eq.marco(nino, a, "departamento")
        area = pl.Series(nino[nino.anio == a].reset_index(drop=True).area.astype(str).to_list())
        out[a] = m.with_columns(territorio=m["territorio"] + "-" + area, upm_estable=m["upm"])
    return out


def test_cuatro_anios_apilados_con_192_dominios_caben_en_los_topes_del_pool():
    p = ParametrosEjecutor.desde_yaml()
    tarea = Tarea(FuenteMemoria(_marcos(eq.leer_endes_nino())), ANIOS, apilado=True)
    with PoolEjecutor(p, RAIZ_REAL) as pool:
        pool.ejecutar(Responder())
        resultado, segundos, pico = pool.ejecutar(ConPico(tarea))
    print(f"\n4 años, {len(resultado)} dominios: {segundos:.3f} s dentro del trabajador, pico {pico / 1024 ** 2:.0f} MB")
    assert len(resultado) == 192
    assert segundos < p.timeout_s and pico < p.memoria_trabajador_mb * 1024 ** 2
