"""M1-04, decisiones del dueño del 13/11/2026: sinónimos de edad y fechas en el recorte de candidatos, y vínculos manuales
(`curados/inferencia/vinculos_manuales.yaml`) que mandan sobre la regla y el LLM y que el lote no manda al modelo."""
from __future__ import annotations

import json
from argparse import Namespace
from dataclasses import replace

import polars as pl
import pytest
import yaml

from pap.config import Rutas
from pap.errores import PapError
from pap.inferencia import cuestionarios as c
from pap.inferencia import cuestionarios_cli
from pap.inferencia.cuestionarios import Candidatos, Pregunta, VariableDic

from .fixtures_m104.proveedor_falso import ProveedorFalso, ServidorFalso


def _preguntas():
    relleno = [Pregunta("individual", str(200 + i), f"¿pregunta número {i} sobre la mes de otra cosa año?", "S", 3) for i in range(40)]
    return relleno + [Pregunta("individual", "105", "¿En qué día, mes y año nació Ud.?", "S", 3),
                      Pregunta("individual", "106", "¿Cuántos años cumplidos tiene?", "S", 3)]


# ------------------------------------------------------------------ sinónimos

def test_los_sinonimos_viven_en_el_yaml_con_la_decision_del_dueno_y_candidatos_k_sigue_en_20():
    cfg = c._config()
    assert cfg["sinonimos"]["decision"].startswith("dueño 13/11/2026")
    assert cfg["candidatos_k"]["valor"] == 20
    assert set(cfg["sinonimos"]["valor"]) >= {"edad", "nacimiento", "fecha"}


def test_edad_actual_llega_a_la_pregunta_de_anos_cumplidos_y_mes_de_nacimiento_a_la_de_dia_mes_y_ano():
    cand = Candidatos(_preguntas())
    top = lambda etiqueta: [q.id for q in cand.de(VariableDic("REC0111", "V0", etiqueta), ["individual"], 3)]
    assert "individual:106" in top("Edad actual - entrevistada")
    assert "individual:105" in top("Mes de nacimiento de la entrevistada")


def test_sin_sinonimos_en_la_configuracion_el_recorte_es_el_de_antes():
    cfg = {k: v for k, v in c._config().items() if k != "sinonimos"}
    cand = Candidatos(_preguntas(), cfg)
    assert "individual:106" not in [q.id for q in cand.de(VariableDic("REC0111", "V0", "Edad actual - entrevistada"), ["individual"], 3)]


def test_los_sinonimos_solo_ordenan_no_cambian_el_numero_de_candidatas():
    cand = Candidatos(_preguntas())
    assert len(cand.de(VariableDic("REC0111", "V0", "Edad actual"), ["individual"], 20)) == 20


# ------------------------------------------------------------------ vínculos manuales

@pytest.fixture
def raiz(tmp_path):
    r = Rutas(tmp_path)
    d = c.carpeta_cuestionarios(r)
    c.guardar_cuestionarios({"hogar": [], "salud": [],
                             "individual": [Pregunta("individual", "474C", "¿Dónde buscó consejo?", "S", 4), Pregunta("individual", "469F", "Otra", "S", 4)]}, d)
    c.guardar_diccionarios([c.VariableDic("REC43", "H44A", "Ibuprofeno"), c.VariableDic("REC43", "H99", "Otra cosa")], {"REC43": ["individual"]}, d)
    (tmp_path / "biblioteca/variables").mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"var_id": [c.var_id("REC43", x) for x in ("H44A", "H99")], "archivo": ["REC43"] * 2, "variable": ["H44A", "H99"],
                  "texto_pregunta": [None] * 2, "estado": ["propuesto"] * 2}, schema_overrides={"texto_pregunta": pl.String}
                 ).write_parquet(tmp_path / "biblioteca/variables/variables.parquet")
    return r


def _yaml(raiz, entradas):
    ruta = raiz.raiz / "curados/inferencia/vinculos_manuales.yaml"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(yaml.safe_dump({"vinculos": entradas}, allow_unicode=True), encoding="utf-8")
    return ruta


ENTRADA = {"tabla": "REC43", "codigo": "H44A", "pregunta": "individual:474C", "motivo": "el dueño lo vio", "quien": "dueño", "fecha": "2026-11-13"}


def test_el_archivo_del_repo_trae_h44a_a_474c_por_el_dueno():
    from pathlib import Path

    es = c.leer_vinculos_manuales(Path(__file__).resolve().parents[2] / "curados/inferencia/vinculos_manuales.yaml")
    h = [e for e in es if (e.tabla, e.codigo) == ("REC43", "H44A")]
    assert len(h) == 1 and h[0].pregunta_id == "individual:474C" and h[0].metodo == "manual" and h[0].estado == "propuesto"


def test_leer_vinculos_manuales_da_metodo_manual_y_guarda_motivo_y_quien(raiz):
    es = c.leer_vinculos_manuales(_yaml(raiz, [ENTRADA]))
    assert [(e.tabla, e.codigo, e.pregunta_id, e.metodo) for e in es] == [("REC43", "H44A", "individual:474C", "manual")]
    assert "el dueño lo vio" in es[0].evidencia and "dueño" in es[0].evidencia and "2026-11-13" in es[0].evidencia


@pytest.mark.parametrize("cambio", [{"pregunta": "474C"}, {"quien": ""}, {"motivo": ""}, {"fecha": ""}, {"codigo": None}])
def test_una_entrada_manual_incompleta_o_mal_formada_falla(raiz, cambio):
    with pytest.raises(PapError):
        c.leer_vinculos_manuales(_yaml(raiz, [{**ENTRADA, **cambio}]))


def test_dos_entradas_manuales_para_la_misma_variable_fallan(raiz):
    with pytest.raises(PapError):
        c.leer_vinculos_manuales(_yaml(raiz, [ENTRADA, {**ENTRADA, "pregunta": "individual:469F"}]))


def test_si_no_hay_archivo_no_hay_vinculos_manuales(raiz):
    assert c.leer_vinculos_manuales(raiz.raiz / "no_existe.yaml") == []


def test_aplicar_respeta_el_vinculo_manual_sobre_el_de_la_regla_y_el_del_llm(raiz):
    d = c.carpeta_cuestionarios(raiz)
    _yaml(raiz, [ENTRADA])
    qs = c.leer_cuestionarios(d)
    c._escribir_parquet(c.tabla_de_vinculos([c.Vinculo("REC43", "H99", None, "sin_pregunta", motivo="administrativa")], qs), d / "vinculos.parquet")
    c._escribir_parquet(c.tabla_de_vinculos([c.Vinculo("REC43", "H44A", "individual:469F", "llm", evidencia="LLM")], qs), d / "vinculos_llm.parquet")
    cuestionarios_cli.ejecutar(Namespace(accion="aplicar", tablas=None, max_variables=0, sobre_indice=False), raiz)
    df = pl.read_parquet(d / "variables_con_pregunta.parquet")
    f = {r["variable"]: r for r in df.iter_rows(named=True)}
    assert f["H44A"]["vinculo_metodo"] == "manual" and f["H44A"]["texto_pregunta"].startswith("¿Dónde buscó")
    assert json.loads(f["H44A"]["pregunta_ref"])["numero"] == "474C" and f["H44A"]["estado"] == "propuesto"
    assert f["H99"]["vinculo_metodo"] == "sin_pregunta"            # lo demás no se toca


def test_el_lote_no_manda_al_modelo_las_variables_con_vinculo_manual(raiz, monkeypatch):
    _yaml(raiz, [ENTRADA])
    monkeypatch.setenv("PAP_ANTHROPIC_BATCH_KEY", "clave-falsa-de-prueba")
    capturado = {}

    def falso(variables, *a, **k):
        capturado["vars"] = [(v.tabla, v.codigo) for v in variables]
        return []

    import pap.inferencia.cuestionarios_lote as lote
    import pap.interprete.llm as llm
    monkeypatch.setattr(lote, "vincular_con_llm", falso)
    monkeypatch.setattr(llm, "ClienteLote", lambda *a, **k: object())
    cuestionarios_cli.ejecutar(Namespace(accion="vincular", tablas=None, max_variables=0, sobre_indice=False), raiz)
    cuestionarios_cli.ejecutar(Namespace(accion="lote", tablas=None, max_variables=0, sobre_indice=False), raiz)
    assert capturado["vars"] == [("REC43", "H99")]
