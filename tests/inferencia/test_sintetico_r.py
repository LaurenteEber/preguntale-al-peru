"""M0-09: el microdato sintético cubre cada caso que pide la historia, se regenera igual con la semilla fija y el adaptador se niega
al `y` nulo dentro de `u`. Sin datos reales."""
import polars as pl
import pytest

from pap.inferencia.svy_adaptador import estimar_proporciones

from .generar_sintetico import generar
from .sintetico_r import RUTA_SINTETICO, TERRITORIOS, marco


@pytest.fixture(scope="module")
def datos() -> pl.DataFrame:
    return pl.read_parquet(RUTA_SINTETICO)


def test_el_parquet_es_el_que_genera_el_script_con_la_semilla_fija(datos):
    assert generar().equals(datos)


def test_seis_estratos_con_1_a_8_upm_y_un_estrato_con_una_sola(datos):
    upm = datos.filter(pl.col("anio") == 2024).group_by("estrato").agg(pl.col("upm").n_unique().alias("k")).sort("estrato")
    assert upm["k"].to_list() == [1, 2, 3, 4, 6, 8] and upm.height == 6


def test_los_ids_de_upm_se_repiten_entre_estratos(datos):
    por_id = datos.group_by("upm").agg(pl.col("estrato").n_unique().alias("h"))
    assert por_id.filter(pl.col("h") > 1).height >= 3


def test_pesos_variables_y_dos_anios_con_las_mismas_upm(datos):
    assert datos["peso"].n_unique() > 100 and datos["peso"].min() > 0
    por_anio = {a: set(datos.filter(pl.col("anio") == a).select("estrato", "upm").unique().iter_rows()) for a in (2023, 2024)}
    assert set(por_anio) == {2023, 2024} and por_anio[2023] == por_anio[2024]


def test_dominios_p_cero_vacio_una_upm_por_estrato_pocos_casos_y_corte_de_5_grupos(datos):
    d = datos.filter(pl.col("u") & (pl.col("anio") == 2024) & (pl.col("terr") != "TN"))
    t = {r["terr"]: r for r in d.group_by("terr").agg(pl.len().alias("n"), pl.col("y").mean().alias("p"),
                                                       pl.struct("estrato", "upm").n_unique().alias("upm")).iter_rows(named=True)}
    assert t["T2"]["p"] == 0.0 and t["T2"]["n"] >= 50                                  # p = 0
    assert "T3" not in t and datos.filter(pl.col("terr") == "T3").height > 0            # dominio vacío: existe, pero ninguna fila entra a u
    assert t["T4"]["upm"] == d.filter(pl.col("terr") == "T4")["estrato"].n_unique() == 5      # una UPM por estrato dentro del dominio
    assert t["T5"]["n"] < 25                                                           # n < 25
    assert t["T7"]["p"] == 1.0
    assert sorted(datos["grupo"].unique()) == ["g1", "g2", "g3", "g4", "g5"]           # corte de 5 grupos


def test_cv_mayor_de_30_por_ciento_en_t6(datos):
    e = {x.dominio[0]: x for x in estimar_proporciones(marco(2024), ["terr"], [(t,) for t in TERRITORIOS], anio=2024)}["T6"]
    assert e.n >= 50 and 0.1 <= e.valor <= 0.9 and e.ee / min(e.valor, 1 - e.valor) > 0.30


def test_un_y_nulo_dentro_de_u_detiene_la_estimacion_y_el_dominio_tn_lo_trae(datos):
    nulos = datos.filter(pl.col("u") & pl.col("y").is_null())
    assert nulos.height == 3 and nulos["terr"].unique().to_list() == ["TN"] and nulos["anio"].unique().to_list() == [2024]
    with pytest.raises(ValueError, match="y nulo"):
        estimar_proporciones(datos.filter(pl.col("anio") == 2024), ["terr"], [("T1",)], anio=2024)
    assert marco(2024)["terr"].is_in(["TN"]).sum() == 0                                  # el marco de las comparaciones no la lleva
