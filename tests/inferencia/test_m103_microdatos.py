"""M1-03, en el Mac: las 3 recetas por región natural, quintil de bienestar y tramo de edad sobre la ENDES 2024 real; las doradas por
corte contra el informe del INEI; las cardinalidades declaradas contra los Parquet; y que exigir HC55 = 0 no mueve ninguna de las 90 filas.

Necesitan `biblioteca/microdatos/ENDES/2024/` y `biblioteca/variables/`: si faltan, FALLAN (no se saltan)."""
import pytest

from conftest import RAIZ_REAL
from pap.inferencia import recetas as rc
from pap.inferencia.duckdb_seguro import conexion_segura
from pap.inferencia.verificador import Contexto, Falla, comprobar_cardinalidades, verificar

from .recetas_m0 import RECETAS

pytestmark = [pytest.mark.regresion_microdatos, pytest.mark.solo_mac]

IDS = ("endes_anemia_6_35m", "endes_anemia_6_35m_oms2024", "endes_dci_menores_5")
PLAN_DE = {"endes_anemia_6_35m": "anemia", "endes_anemia_6_35m_oms2024": "anemia_oms2024", "endes_dci_menores_5": "dci"}
CASOS_U = {"endes_anemia_6_35m": 9959, "endes_anemia_6_35m_oms2024": 9959, "endes_dci_menores_5": 19511}


@pytest.fixture(scope="module")
def ctx():
    for carpeta in ("biblioteca/variables", "biblioteca/microdatos/ENDES/2024"):
        assert (RAIZ_REAL / carpeta).is_dir(), f"falta {carpeta}"
    return Contexto.cargar(RAIZ_REAL)


@pytest.fixture(scope="module")
def con():
    return conexion_segura(RAIZ_REAL)


def test_las_cardinalidades_declaradas_se_cumplen_en_los_parquet_de_2024(ctx, con):
    assert comprobar_cardinalidades(ctx.relaciones[("ENDES", 2024)], ctx.carpeta_microdatos, "ENDES", 2024, con) == []
    declaradas = {(u.hijo, u.padre): u.cardinalidad for u in ctx.relaciones[("ENDES", 2024)]}
    assert declaradas[("RECH23", "RECH0")] == "1:1"


def test_rech23_y_rech0_tienen_las_mismas_37390_filas_y_el_mismo_hogar(con):
    n = con.execute(f"SELECT (SELECT count(*) FROM read_parquet('{RAIZ_REAL}/biblioteca/microdatos/ENDES/2024/RECH23.parquet')), "
                    f"(SELECT count(*) FROM read_parquet('{RAIZ_REAL}/biblioteca/microdatos/ENDES/2024/RECH0.parquet')), "
                    f"(SELECT count(*) FROM read_parquet('{RAIZ_REAL}/biblioteca/microdatos/ENDES/2024/RECH23.parquet') a "
                    f" JOIN read_parquet('{RAIZ_REAL}/biblioteca/microdatos/ENDES/2024/RECH0.parquet') b USING (HHID))").fetchone()
    assert n == (37390, 37390, 37390)


@pytest.mark.parametrize("id_", IDS)
def test_el_verificador_deja_pasar_los_cinco_cortes_y_los_controles_de_la_union_pasan(ctx, con, id_):
    for corte in ("region_natural", "quintil_riqueza", "grupo_edad"):
        pc = verificar(RECETAS[PLAN_DE[id_]]("nacional", cortes=(corte,)), ctx, con)
        assert not isinstance(pc, Falla), (corte, pc)
        c = pc.controles
        assert c["filas_unidad"] == c["filas_tras_uniones"] == 20290 and c["u_antes"] == c["u_despues"] == CASOS_U[id_] and c["perdida_u"] == 0
        assert pc.universo_analitico.id == rc.leer_receta(RAIZ_REAL, id_).universo_analitico
    pc = verificar(RECETAS[PLAN_DE[id_]]("nacional", cortes=("region_natural", "quintil_riqueza")), ctx, con)
    assert not isinstance(pc, Falla), pc
    assert pc.controles["uniones"].count("RECH0→RECH23") == 1


@pytest.mark.parametrize("id_", IDS)
def test_exigir_hc55_igual_a_0_no_cambia_los_casos_de_ninguna_receta(ctx, con, id_):
    """Hoy no hay ningún niño de la receta con HC55 ≠ 0: el universo de la receta y la base común dan los mismos casos (0 filas afectadas)."""
    base = RECETAS[PLAN_DE[id_]]("nacional")
    a = verificar(base, ctx, con)
    b = verificar(base.model_copy(update={"universo_analitico": "nino_hecho"}), ctx, con)
    assert not isinstance(a, Falla) and not isinstance(b, Falla)
    assert a.controles["u_despues"] == b.controles["u_despues"] == CASOS_U[id_]


@pytest.mark.parametrize("id_", IDS)
def test_las_doradas_por_corte_se_reproducen_dentro_de_0_1_pp_y_con_los_mismos_casos(id_):
    receta = rc.leer_receta(RAIZ_REAL, id_)
    doradas = [d for d in rc.leer_doradas_cortes(RAIZ_REAL) if d.receta_id == id_]
    assert len(doradas) == {"endes_dci_menores_5": 10}.get(id_, 13)
    estimaciones, valores = rc.calcular_cortes(receta, doradas, RAIZ_REAL)
    filas = rc.reproducir_doradas_cortes(receta, doradas, estimaciones, valores)
    assert len(filas) == len(doradas)
    assert [(f["id_cifra"], f["publicado"], f["nuestro"], f["casos_publicados"], f["n"]) for f in filas if not f["pasa"]] == []
    assert max(abs(f["dif_pp"]) for f in filas) <= receta.tolerancia_pp
    assert all(f["n"] == f["casos_publicados"] for f in filas)


def test_las_cifras_de_referencia_del_auditor_del_supervisor():
    """Costa 7,3 / 36,1 / 27,0 y quintil inferior 22,4 / 54,8 / 47,5 (desnutrición crónica, anemia RM 363, anemia OMS 2024)."""
    esperado = {("endes_dci_menores_5", "Costa"): 7.3, ("endes_anemia_6_35m", "Costa"): 36.1, ("endes_anemia_6_35m_oms2024", "Costa"): 27.0,
                ("endes_dci_menores_5", "los más pobres"): 22.4, ("endes_anemia_6_35m", "los más pobres"): 54.8,
                ("endes_anemia_6_35m_oms2024", "los más pobres"): 47.5}
    for id_ in IDS:
        receta = rc.leer_receta(RAIZ_REAL, id_)
        doradas = [d for d in rc.leer_doradas_cortes(RAIZ_REAL) if d.receta_id == id_ and d.categoria in ("Costa", "los más pobres")]
        estimaciones, valores = rc.calcular_cortes(receta, doradas, RAIZ_REAL)
        for f in rc.reproducir_doradas_cortes(receta, doradas, estimaciones, valores):
            assert f["nuestro"] == esperado[(id_, f["categoria"])], f
