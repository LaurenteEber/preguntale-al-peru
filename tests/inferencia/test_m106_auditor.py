"""Hallazgos del auditor independiente sobre M1-05 t0 y M1-06 (ronda de corrección). Sobre el índice real: FALLAN si falta (no se saltan)."""
import json

import polars as pl
import pytest

from conftest import RAIZ_REAL

IND = RAIZ_REAL / "biblioteca" / "variables"
pytestmark = [pytest.mark.regresion_microdatos, pytest.mark.solo_mac]


def _v():
    return pl.read_parquet(IND / "variables.parquet")


def _clase(a, x):
    return _v().filter((pl.col("archivo") == a) & (pl.col("variable") == x))["clase"][0]


@pytest.mark.parametrize("a,x", [("CSALUD01", "QS212AB"), ("CSALUD01", "QS212AV"), ("REC95", "S476AN1"), ("RECH23", "HV246A"),
                                 ("RE516171", "V527"), ("REC41", "M4")])
def test_los_conteos_y_cantidades_no_son_categoria(a, x):
    assert _clase(a, x) == "medida"


def test_llaves_y_geografia_del_auditor():
    assert _clase("CSALUD01", "QSNUMERO") == "llave"
    assert _clase("RECH0", "LATITUDY") == "geo" and _clase("RECH0", "LONGITUDX") == "geo"


def test_s489c_es_tuberculosis_no_vih():
    v, b = _v(), pl.read_parquet(IND / "bloques.parquet")
    bid = v.filter((pl.col("archivo") == "REC91") & (pl.col("variable") == "S489C"))["bloque_id"][0]
    fila = b.filter(pl.col("bloque_id") == bid).row(0, named=True)
    assert fila["subtema"] != "vih_its" and fila["subtema"] == "enfermedades_cronicas" and bid == "endes_rec91_tuberculosis"


def test_los_modulos_dit_declaran_la_edad():
    b = pl.read_parquet(IND / "bloques.parquet").filter(pl.col("bloque_id").str.starts_with("endes_dit_modulo_"))
    assert b.height == 6
    for r in b.iter_rows(named=True):
        p = json.loads(r["poblacion"] or "{}")
        assert p.get("edad_min") is not None and p.get("edad_unidad") == "meses", r["bloque_id"]


def test_paginas_de_violencia_y_calendario():
    f = pl.read_parquet(IND / "fichas_tabla.parquet")
    def pag(t, rec="endes-2024-cuestionario-individual"):
        d = json.loads(f.filter(pl.col("tabla") == t)["documentos"][0])
        return next(x for x in d if x["recurso"] == rec)["paginas"]
    assert "72" in pag("REC84DV") and "72" in pag("REC93DVdisciplina") and "82" not in pag("REC84DV")
    assert "89" in pag("REC82")


def test_otras_correcciones_de_clase_y_bloque():
    assert _clase("RE223132", "V215") == "medida" and _clase("REC95", "S466DC1") == "medida" and _clase("RECH23", "SH79") == "medida"
    assert _clase("RECH0", "HV002") == "llave" and _clase("RECH0", "HV004") == "diseno" and _clase("RECH0", "HV007") == "diseno"
    assert _clase("REC0111", "V003") == "llave" and _clase("RECH6", "HC60") != "medida"
    v, b = _v(), pl.read_parquet(IND / "bloques.parquet")
    blo = lambda a, x: v.filter((pl.col("archivo") == a) & (pl.col("variable") == x))["bloque_id"][0]
    assert blo("REC21", "BD") == "endes_rec21_nacimiento" and blo("REC94", "S431A") == "endes_rec94_lactancia"
    assert blo("RECH23", "SXH73") == "endes_rech23_mosquiteros" and blo("REC41", "M51A") == "endes_rec41_control_posparto_bebe"
    assert blo("RE516171", "V535") == "endes_re516171_estado_civil" and blo("RECH23", "HV248") != "endes_rech23_enfermos_fallecidos"
    assert blo("DIT", "QI478H12") == blo("DIT", "QI478I8") == blo("DIT", "QI478J8")
    ca = b.filter(pl.col("bloque_id") == blo("DIT", "QI478H12")).row(0, named=True)
    assert ca["subtema"] == "castigo_disciplina_infantil" and ca["ventana_referencia"] == "últimos 15 días"
