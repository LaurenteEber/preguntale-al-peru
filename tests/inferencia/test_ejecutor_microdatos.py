"""M0-08, en el Mac: el ejecutor contra `calculo._svy_niveles` (equivalencia) y las 3 recetas contra las 90 filas de 2024 del cubo.

Necesitan `biblioteca/estandarizada/encuestas/endes_nino.parquet` (solo lectura), `biblioteca/microdatos/ENDES/2024/` y
`biblioteca/variables/`: si faltan, FALLAN (no se saltan). La comparación formal con el cubo es M0-10; aquí es la primera lectura."""
import csv

import pytest

from conftest import RAIZ_REAL
from pap.inferencia.duckdb_seguro import conexion_segura
from pap.inferencia.ejecutor import Ejecutor, FuenteMemoria, PoolEjecutor
from pap.inferencia.tablas_curadas import leer_relacion_entre_anios
from pap.inferencia.verificador import Contexto, Falla, verificar

from . import equivalencia_m0 as eq
from .pool_tareas import Responder
from .recetas_m0 import NIVELES, RECETAS

pytestmark = [pytest.mark.regresion_microdatos, pytest.mark.solo_mac]

TOL = 1e-12
FILAS_2024 = RAIZ_REAL / "backlog" / "slice-m0" / "evidencia" / "m0-00_filas_cubo_2024.csv"
INDICADOR = {"anemia": "endes_anemia_6_35m", "anemia_oms2024": "endes_anemia_6_35m_oms2024", "dci": "endes_dci_menores_5"}
REDONDEO_CUBO = 1e-8                        # el cubo guarda 8 decimales (calculo.DECIMALES): la diferencia por redondeo es ≤ 5e-9


@pytest.fixture(scope="module")
def nino():
    assert eq.ENDES_NINO.exists(), f"falta {eq.ENDES_NINO}"
    return eq.leer_endes_nino()


@pytest.fixture(scope="module")
def oraculo(nino):
    return eq.oraculo(nino, 2024)


@pytest.fixture(scope="module")
def pool():
    with PoolEjecutor(raiz=RAIZ_REAL) as p:
        p.ejecutar(Responder())                              # precalentado
        yield p


def _comparar(estimaciones, oraculo, nivel) -> dict[str, float]:
    """Máxima |dif| por campo contra `_svy_niveles` (que da porcentajes: valor y ee ×100). n efectivo = mín(n, el de calculo)."""
    mx = dict.fromkeys(("valor", "ee", "ic_inf", "ic_sup", "gl", "n", "deff", "n_efectivo"), 0.0)
    assert estimaciones, nivel
    for e in estimaciones:
        o = oraculo[(nivel, e.dominio[0])]
        assert not e.sin_datos
        dif = {"valor": 100 * e.valor - o["valor"], "ee": 100 * e.ee - o["ee"], "ic_inf": 100 * e.ic_inf - o["ic_inf"],
               "ic_sup": 100 * e.ic_sup - o["ic_sup"], "gl": e.gl - o["gl"], "n": e.n - o["n_muestra"], "deff": e.deff - o["deff"],
               "n_efectivo": e.n_efectivo - (min(e.n, o["n_efectivo"]) if o["n_efectivo"] is not None else e.n)}
        for k, v in dif.items():
            mx[k] = max(mx[k], abs(v))
    return mx


@pytest.mark.parametrize("nivel,dominios", [("nacional", 1), ("dominio_subnacional", 2), ("departamento", 24)])
def test_anemia_2024_en_proceso_igual_a_calculo_svy_niveles(nino, oraculo, nivel, dominios):
    ex = Ejecutor(relaciones=leer_relacion_entre_anios(RAIZ_REAL))
    res = ex.estimar(FuenteMemoria({2024: eq.marco(nino, 2024, nivel)}), "ENDES", [2024])
    assert len(res) == dominios == sum(1 for k in oraculo if k[0] == nivel)
    mx = _comparar(res, oraculo, nivel)
    assert all(v <= TOL for v in mx.values()), mx


@pytest.mark.parametrize("nivel", list(eq.NIVELES))
def test_anemia_2024_por_el_pool_igual_a_calculo_svy_niveles(nino, oraculo, pool, nivel):
    ex = Ejecutor(pool, relaciones=leer_relacion_entre_anios(RAIZ_REAL))
    res = ex.estimar(FuenteMemoria({2024: eq.marco(nino, 2024, nivel)}), "ENDES", [2024])
    mx = _comparar(res, oraculo, nivel)
    assert all(v <= TOL for v in mx.values()), mx


def test_el_n_efectivo_del_ejecutor_nunca_pasa_de_n(nino):
    ex = Ejecutor(relaciones=leer_relacion_entre_anios(RAIZ_REAL))
    res = [e for nivel in eq.NIVELES for e in ex.estimar(FuenteMemoria({2024: eq.marco(nino, 2024, nivel)}), "ENDES", [2024])]
    assert len(res) == 27 and all(e.n_efectivo <= e.n for e in res)


@pytest.fixture(scope="module")
def cubo_2024():
    with open(FILAS_2024, encoding="utf-8", newline="") as f:
        filas = {(r["indicador_id"], r["nivel"], r["territorio_id"]): r for r in csv.DictReader(f)}
    assert len(filas) == 90
    return filas


@pytest.fixture(scope="module")
def ctx():
    for carpeta in ("biblioteca/variables", "biblioteca/microdatos/ENDES/2024"):
        assert (RAIZ_REAL / carpeta).is_dir(), f"falta {carpeta}"
    return Contexto.cargar(RAIZ_REAL)


def _diferencias_con_el_cubo(receta, ctx, cubo, ejecutor):
    con = conexion_segura(RAIZ_REAL)
    mx, n = dict.fromkeys(("valor", "ee", "ic_inf", "ic_sup", "gl", "n", "deff", "n_efectivo"), 0.0), 0
    for nivel in NIVELES:
        pc = verificar(RECETAS[receta](nivel), ctx, con)
        assert not isinstance(pc, Falla), pc
        for e in ejecutor.ejecutar({2024: pc}, ctx):
            f = cubo[(INDICADOR[receta], nivel, e.dominio[0])]
            n += 1
            c = lambda k: float(f[k])
            dif = {"valor": 100 * e.valor - c("valor"), "ee": 100 * e.ee - c("ee"), "ic_inf": 100 * e.ic_inf - c("ic_inf"),
                   "ic_sup": 100 * e.ic_sup - c("ic_sup"), "gl": e.gl - c("gl"), "n": e.n - c("n_muestra"), "deff": e.deff - c("deff"),
                   "n_efectivo": e.n_efectivo - min(e.n, c("n_efectivo"))}
            for k, v in dif.items():
                mx[k] = max(mx[k], abs(v))
    return n, mx


@pytest.mark.parametrize("receta", list(RECETAS))
def test_las_recetas_de_2024_sobre_los_microdatos_igualan_las_30_filas_del_cubo(ctx, cubo_2024, receta):
    n, mx = _diferencias_con_el_cubo(receta, ctx, cubo_2024, Ejecutor(relaciones=leer_relacion_entre_anios(RAIZ_REAL)))
    assert n == 30
    assert mx["gl"] == 0 and mx["n"] == 0
    assert all(v <= REDONDEO_CUBO for v in mx.values()), mx


def test_la_upm_estable_de_2024_es_la_misma_que_la_del_diseno(ctx):
    con = conexion_segura(RAIZ_REAL)
    pc = verificar(RECETAS["anemia"]("nacional"), ctx, con)
    fuente, *_ = Ejecutor(relaciones=leer_relacion_entre_anios(RAIZ_REAL)).preparar({2024: pc, 2025: pc}, ctx)
    a, b = fuente.cargar(2024), fuente.cargar(2024, upm_estable=True)
    # Dos cargas tienen las mismas filas pero no garantizan el mismo orden (Parquet con hilos: hallazgo 1 del supervisor): se comparan ordenadas.
    par = lambda d: sorted(zip(d["upm"].cast(str).to_list(), d["u"].to_list()))
    assert par(a) == par(b) and a["u"].sum() == b["u"].sum() == 9959


def test_el_cubo_no_topa_el_n_efectivo_y_el_ejecutor_si(cubo_2024):
    """La historia: «en 2024 hay 12 filas con n efectivo > n» en el cubo; el ejecutor las deja en n."""
    sin_tope = [k for k, f in cubo_2024.items() if float(f["n_efectivo"]) > float(f["n_muestra"])]
    assert len(sin_tope) == 12
