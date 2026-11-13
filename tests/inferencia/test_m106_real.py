"""M1-06 sobre la ENDES 2024 real. Las del índice y los microdatos llevan `solo_mac` y `regresion_microdatos` y FALLAN si faltan; la de las citas del
documento n.º 11 solo lee tablas curadas y corre en cualquier equipo."""
import tempfile
from pathlib import Path

import polars as pl
import pytest
import yaml

from pap.inferencia import fichas as fi

from conftest import RAIZ_REAL

LOTE = ("RECH0 RECH23 RECH1 RECH4 RECH6 REC21 REC41 REC43 REC44 REC94 REC95 DIT REC0111 REC91 RE223132 REC42 RE516171 RE758081 RECH5").split()
IND = RAIZ_REAL / "biblioteca" / "variables"
marcas = [pytest.mark.regresion_microdatos, pytest.mark.solo_mac]


def test_cada_union_declarada_cita_el_documento_n11_o_dice_que_solo_son_datos():
    y = yaml.safe_load((RAIZ_REAL / "curados" / "inferencia" / "archivos_endes_2024.yaml").read_text(encoding="utf-8"))
    assert set(y["citas"]) == {"doc11_hhid", "doc11_hvidx", "doc11_caseid", "solo_datos"}
    assert all(r["cita"] in y["citas"] for r in y["relaciones"])
    solo = [(r["hijo"], r["padre"]) for r in y["relaciones"] if r["cita"] == "solo_datos"]
    assert solo == [("REC0111", "RECH1")]                                   # el documento no menciona V003
    filas = {t: d["fila"] for t, d in y["llaves_cita"].items()}
    assert set(filas) == set(y["archivos"]) and sorted(filas.values()) == list(range(1, 35))
    assert "C-M1-06-1" in y["llaves_cita"]["CSALUD01"]["nota"]


@pytest.mark.regresion_microdatos
@pytest.mark.solo_mac
def test_34_fichas_y_cobertura_100_de_las_19_tablas_del_lote():
    f = pl.read_parquet(IND / "fichas_tabla.parquet")
    b = pl.read_parquet(IND / "bloques.parquet")
    v = pl.read_parquet(IND / "variables.parquet")
    assert f.height == 34 and sorted(f["tabla"].to_list()) == sorted(pl.read_parquet(IND / "archivos.parquet")["archivo"].to_list())
    cm = v.filter(pl.col("clase").is_in(["categoria", "medida"]))
    for t in LOTE:
        x = cm.filter(pl.col("archivo") == t)
        assert x.height > 0 and x["bloque_id"].null_count() == 0, t           # 100 % de las categoria y medida con bloque
        assert set(x["bloque_id"]) <= set(b.filter(pl.col("tabla") == t)["bloque_id"]), t
    assert v.filter(~pl.col("clase").is_in(["categoria", "medida"]))["bloque_id"].null_count() == v.filter(~pl.col("clase").is_in(["categoria", "medida"])).height
    assert b.height == 227 and b["n_variables"].sum() == cm.filter(pl.col("archivo").is_in(LOTE)).height


@pytest.mark.regresion_microdatos
@pytest.mark.solo_mac
def test_pap_fichas_validar_con_datos_y_zip_reales_sin_problemas():
    probs, info = fi.validar(RAIZ_REAL, "ENDES", 2024)
    assert probs == [] and info["fichas"] == 34 and info["bloques"] == 227 and info["no_comprobado"] == []
    assert any("RECH6" in x for x in info["edades"])


@pytest.mark.regresion_microdatos
@pytest.mark.solo_mac
def test_ver_rech6_es_legible_y_completa():
    txt = fi.ver(RAIZ_REAL, "ENDES", 2024, "RECH6")
    for frag in ("RECH6", "A quién describe", "0–59 meses", "Módulo 1638", "HHID, HC0", "Unión → RECH1 por HHID = HHID, HC0 = HVIDX",
                 "Cobertura de bloques: 37 de 37", "endes_rech6_hemoglobina", "Diccionario - RECH6.pdf", "fila 7"):
        assert frag in txt, frag


@pytest.mark.regresion_microdatos
@pytest.mark.solo_mac
def test_generar_dos_veces_da_los_mismos_archivos_que_hay_escritos():
    with tempfile.TemporaryDirectory(prefix="pap-fichas-test-") as d:
        a, b = Path(d) / "a", Path(d) / "b"
        fi.generar(RAIZ_REAL, "ENDES", 2024, a)
        fi.generar(RAIZ_REAL, "ENDES", 2024, b)
        for n in ("fichas_tabla.parquet", "bloques.parquet", "variables.parquet"):
            assert (a / n).read_bytes() == (b / n).read_bytes() == (IND / n).read_bytes(), n
