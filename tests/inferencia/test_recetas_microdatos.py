"""M0-10, en el Mac: las 3 recetas de 2024 por el camino nuevo (plan → verificador → ejecutor → compuertas) contra el cubo `010ea965`.

Criterios de la definición de hecho del slice, punto 1: en las 90 filas, valor, ee, IC, CV y deff redondeados a 8 decimales con
|dif| ≤ 1e-8; n_muestra y gl idénticos; n efectivo = mín(n, el del cubo); sin redondear, contra `calculo._svy_niveles`, |dif| ≤ 1e-12.
Además: las doradas de 2024 con ±0,1 pp (E-05), las compuertas contra `m0-00_estados_cubo.csv` y los cortes de cada receta.

Necesitan `endes_nino.parquet` (solo lectura), `biblioteca/microdatos/ENDES/2024/` y `biblioteca/variables/`: si faltan, FALLAN."""
import duckdb
import pytest

from conftest import RAIZ_REAL
from pap.cli import main
from pap.inferencia import recetas as rc
from pap.inferencia.verificador import Contexto, Falla, verificar

from . import comparar_m10 as cm
from .recetas_m0 import RECETAS

pytestmark = [pytest.mark.regresion_microdatos, pytest.mark.solo_mac]

IDS = ("endes_anemia_6_35m", "endes_anemia_6_35m_oms2024", "endes_dci_menores_5")
PLAN_DE = {"endes_anemia_6_35m": "anemia", "endes_anemia_6_35m_oms2024": "anemia_oms2024", "endes_dci_menores_5": "dci"}
MICRODATOS = RAIZ_REAL / "biblioteca" / "microdatos" / "ENDES" / "2024"


@pytest.fixture(scope="module")
def filas():
    assert cm.eq.ENDES_NINO.exists(), f"falta {cm.eq.ENDES_NINO}"
    assert MICRODATOS.is_dir() and (RAIZ_REAL / "biblioteca" / "variables").is_dir()
    return cm.filas_90(RAIZ_REAL)


def test_son_las_90_filas_del_cubo_30_por_receta(filas):
    assert len(filas) == len({f["llave"] for f in filas}) == 90
    assert {i: sum(f["llave"][0] == i for f in filas) for i in IDS} == dict.fromkeys(IDS, 30)
    assert {f["llave"][1] for f in filas} == {"nacional", "dominio_subnacional", "departamento", "CALLAO", "LIMA_METROPOLITANA", "LIMA_REGION"}


def test_las_90_filas_igualan_al_cubo_redondeadas_a_8_decimales(filas):
    malas = [(f["llave"], d.columna, d.cubo, d.nuevo) for f in filas for d in f["diferencias"] if not d.ok]
    assert not malas, malas
    for f in filas:
        d = {x.columna: x for x in f["diferencias"]}
        assert d["gl"].dif == 0 and d["n_muestra"].dif == 0
        assert d["n_efectivo"].cubo == min(float(f["cubo"]["n_muestra"]), float(f["cubo"]["n_efectivo"]))


def test_las_90_filas_sin_redondear_igualan_a_calculo_svy_niveles(filas):
    tol = rc.ParametrosRecetas.desde_yaml().oraculo_tolerancia
    malas = [(f["llave"], c, v) for f in filas for c, v in f["sin_redondear"].items() if abs(v) > tol]
    assert not malas, malas


def test_las_compuertas_dan_el_estado_y_las_reglas_del_cubo_en_las_90_filas(filas):
    malas = [(f["llave"], f["compuerta"].estado, f["estado_cubo"]["estado"], f["reglas"]) for f in filas
             if f["compuerta"].estado != f["estado_cubo"]["estado"] or f["reglas"] != f["estado_cubo"]["reglas"]]
    assert not malas, malas
    estados = {}
    for f in filas:
        estados[f["compuerta"].estado] = estados.get(f["compuerta"].estado, 0) + 1
    assert estados == {"publicable": 85, "referencial": 5}
    # recetas «revisadas», no «verificadas»: la confianza de lo publicable es la más baja (supuesto M0-09), nunca «alta»
    assert {f["compuerta"].confianza for f in filas if f["compuerta"].estado == "publicable"} == {"baja"}


@pytest.mark.parametrize("id_", IDS)
def test_las_doradas_de_2024_se_reproducen_dentro_de_0_1_pp(id_):
    receta = rc.leer_receta(RAIZ_REAL, id_)
    doradas = rc.reproducir_doradas(receta, rc.calcular(receta, 2024, RAIZ_REAL))
    assert len(doradas) == len(receta.doradas) == {"endes_dci_menores_5": 3}.get(id_, 9)
    assert [d for d in doradas if not d["pasa"]] == []
    assert max(abs(d["dif_pp"]) for d in doradas) <= receta.tolerancia_pp


# ------------------------------------------------------------------ universos y cortes de las recetas

@pytest.mark.parametrize("variable", ["HC57", "HC57A"])
def test_la_condicion_de_hemoglobina_medida_no_agrega_ni_quita_filas_a_la_receta_de_anemia(variable):
    """La receta declara `nino_hecho_hb_medida` (HC55 = 0) pero el verificador agrega la base común `nino_hecho`: lo que sobra es
    que HC55 = 0 ya lo implica tener HC57 (o HC57A) en 1–4. Sin ningún niño de 6 a 35 meses con nivel de anemia y HC55 ≠ 0."""
    n = duckdb.sql(f"SELECT count(*) FROM read_parquet('{MICRODATOS / 'RECH6.parquet'}') "
                   f"WHERE HC1 BETWEEN 6 AND 35 AND {variable} IN (1, 2, 3, 4) AND (HC55 IS NULL OR HC55 <> 0)").fetchone()[0]
    assert n == 0


@pytest.mark.parametrize("id_", IDS)
def test_el_verificador_deja_pasar_los_cortes_permitidos_y_rechaza_los_demas(id_):
    ctx, receta = Contexto.cargar(RAIZ_REAL), rc.leer_receta(RAIZ_REAL, id_)
    for corte in receta.cortes_permitidos:
        pc = verificar(RECETAS[PLAN_DE[id_]]("nacional", cortes=(corte,)), ctx)
        assert not isinstance(pc, Falla), (corte, pc)
        assert pc.universo_analitico.id in ("nino_hecho", receta.universo_analitico)
    for c in receta.cortes_no_permitidos:
        f = verificar(RECETAS[PLAN_DE[id_]]("nacional", cortes=(c.id,)), ctx)
        assert isinstance(f, Falla) and f.dimension == "cortes", (c.id, f)


# ------------------------------------------------------------------ comando

@pytest.mark.parametrize("id_", IDS)
def test_pap_inferencia_receta_comparar_cubo_sale_con_0(id_, capsys):
    assert main(["inferencia", "receta", id_, "--anio", "2024", "--comparar-cubo"]) == 0
    salida = capsys.readouterr().out
    assert "30 territorio(s)" in salida and "Compuertas: 0 fila(s)" in salida and "✘" not in salida
    assert "Contra el cubo (30 de 30 filas)" in salida


def test_pap_inferencia_receta_sin_comparar_lista_los_30_territorios(capsys):
    assert main(["inferencia", "receta", "endes_dci_menores_5", "--anio", "2024"]) == 0
    salida = capsys.readouterr().out
    assert salida.count(" % (IC ") == 30 and "Doradas (E-05): 3 de 3 se reproducen" in salida


def test_pap_inferencia_receta_de_otro_anio_falla_con_mensaje(capsys):
    assert main(["inferencia", "receta", "endes_dci_menores_5", "--anio", "2023"]) != 0
    assert "vale para 2024–2024, no para 2023" in capsys.readouterr().err


def test_el_csv_de_evidencia_tiene_las_90_filas_y_ninguna_fuera_de_tolerancia(filas, tmp_path):
    salida = tmp_path / "m0-10.csv"
    cm.escribir_csv(filas, salida)
    import csv

    r = list(csv.DictReader(open(salida, encoding="utf-8")))
    assert len(r) == 90 and all(x["ok_fila"] == "True" for x in r)
