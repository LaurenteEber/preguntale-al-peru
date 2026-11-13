"""M1-04: acciones de `pap cuestionarios` sobre un almacén de juguete (sin PDF, sin red, sin clave)."""
from __future__ import annotations

from argparse import Namespace

import polars as pl
import pytest

from pap.config import Rutas
from pap.errores import PapError
from pap.inferencia import cuestionarios as c
from pap.inferencia import cuestionarios_cli


@pytest.fixture
def raiz(tmp_path):
    r = Rutas(tmp_path)
    d = c.carpeta_cuestionarios(r)
    c.guardar_cuestionarios({"hogar": [], "individual": [], "salud": [c.Pregunta("salud", "25", "¿Cuántos años cumplidos tiene?", "SECCIÓN 1", 4)]}, d)
    c.guardar_diccionarios([c.VariableDic("CSALUD01", "QS25", "Edad"), c.VariableDic("CSALUD01", "HHID", "Identificación"),
                            c.VariableDic("CSALUD01", "QS77", "Otra")], {"CSALUD01": ["salud"]}, d)
    (tmp_path / "biblioteca/variables").mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"var_id": [c.var_id("CSALUD01", x) for x in ("QS25", "HHID", "QS77")], "archivo": ["CSALUD01"] * 3,
                  "variable": ["QS25", "HHID", "QS77"], "texto_pregunta": [None] * 3, "estado": ["propuesto"] * 3},
                 schema_overrides={"texto_pregunta": pl.String}).write_parquet(tmp_path / "biblioteca/variables/variables.parquet")
    return r


def test_lote_sin_clave_se_niega_antes_de_llamar_a_nada(raiz, monkeypatch):
    monkeypatch.delenv("PAP_ANTHROPIC_BATCH_KEY", raising=False)
    monkeypatch.setenv("PAP_ANTHROPIC_API_KEY", "clave-del-servicio-web")
    with pytest.raises(PapError) as e:
        cuestionarios_cli.ejecutar(Namespace(accion="lote", tablas=None, max_variables=0, sobre_indice=False), raiz)
    assert "PAP_ANTHROPIC_BATCH_KEY" in str(e.value) and "clave-del-servicio-web" not in str(e.value)
    assert not (c.carpeta_cuestionarios(raiz) / "lote").exists()


def test_vincular_y_aplicar_dejan_el_texto_en_una_copia_del_indice(raiz):
    ns = Namespace(accion="vincular", tablas=None, max_variables=0, sobre_indice=False)
    cuestionarios_cli.ejecutar(ns, raiz)
    cuestionarios_cli.ejecutar(Namespace(accion="aplicar", tablas=None, max_variables=0, sobre_indice=False), raiz)
    df = pl.read_parquet(c.carpeta_cuestionarios(raiz) / "variables_con_pregunta.parquet")
    f = {r["variable"]: r for r in df.iter_rows(named=True)}
    assert f["QS25"]["texto_pregunta"].startswith("¿Cuántos") and f["QS25"]["estado"] == "propuesto"
    assert f["HHID"]["sin_pregunta"] == "administrativa" and f["QS77"]["sin_pregunta"] == "pendiente"
    original = pl.read_parquet(raiz.raiz / "biblioteca/variables/variables.parquet")
    assert "pregunta_ref" not in original.columns                  # el índice de M0 no se tocó (no se pidió --sobre-indice)
