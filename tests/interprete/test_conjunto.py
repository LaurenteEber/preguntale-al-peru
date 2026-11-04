"""S2-02 — Comprobaciones del conjunto de evaluación (tests/interprete/evaluacion.yaml): consultas esperadas válidas según el
contrato (S2-01), Q1–Q4 resuelven como sus JSON (Q1, tras elegir el departamento), ids únicos y mínimos por categoría.
Si falta el conjunto o el cubo, las pruebas FALLAN (agents.md §8)."""
import json
from collections import Counter

import pytest
import yaml

from pap.config import Rutas
from pap.motor.interpretacion import validar
from pap.motor.territorio import Aclaracion, resolver
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL

RAIZ = Rutas(RAIZ_REAL).raiz
EVALUACION = RAIZ / "tests" / "interprete" / "evaluacion.yaml"
MINIMOS = {"directa": 24, "reformulada": 20, "tipeo": 10, "lugares_dificiles": 12, "anios": 10, "ambigua": 10,
           "fuera_tema": 6, "fuera_pregunta": 6, "enganosa": 8, "inyeccion": 6, "q1_q4": 4}


@pytest.fixture(scope="module")
def entradas():
    assert EVALUACION.exists(), f"falta {EVALUACION} (S2-02); no se salta"
    return yaml.safe_load(EVALUACION.read_text(encoding="utf-8"))["entradas"]


def anclas_de_prueba(c: dict) -> dict:
    """Las anclas no son parte del conjunto: para validar la forma, una de prueba por cada valor presente."""
    a = {k: "ancla" for k in ("intencion", "tema", "comparar_con") if k in c}
    t = c.get("territorio")
    if isinstance(t, dict) and "nivel" in t:
        a["nivel"] = "ancla"
        if "dentro_de" in t:
            a["dentro_de"] = "ancla"
    elif t is not None:
        a["territorio"] = "ancla"
    for k in ("anio", "desde", "hasta"):
        if k in (c.get("periodo") or {}):
            a[k] = "ancla"
    return a


def test_ids_unicos_y_minimos(entradas):
    ids = [e["id"] for e in entradas]
    assert len(ids) == len(set(ids)), [i for i, n in Counter(ids).items() if n > 1]
    assert len(entradas) >= 100
    n = Counter(e["categoria"] for e in entradas)
    assert set(n) <= set(MINIMOS), set(n) - set(MINIMOS)
    for cat, m in MINIMOS.items():
        assert n[cat] >= m, (cat, n[cat], m)
    for e in entradas:
        assert e["pregunta"].strip() and e["esperado"]["resultado"] in ("consulta", "aclaracion", "fuera_de_alcance",
                                                                        "no_es_pregunta", "otro_idioma"), e["id"]


def test_consultas_esperadas_validas(entradas):
    for e in entradas:
        x = e["esperado"]
        if x["resultado"] == "consulta":
            validar({"resultado": "consulta", "consulta": x["consulta"], "anclas": anclas_de_prueba(x["consulta"])}, RAIZ)
        elif x["resultado"] == "aclaracion":
            assert x.get("motivo") in ("intencion_ambigua", "varias_preguntas", "sin_lugar", "anio_relativo", "homonimo",
                                       None), e["id"]
        elif x["resultado"] == "fuera_de_alcance":
            assert x.get("tipo") in ("tema", "pregunta"), e["id"]


def _resuelto(r, nivel=None):
    if isinstance(r, Aclaracion):
        ops = [o["territorio"] for o in r.opciones if nivel is None or o["territorio"].nivel == nivel]
        assert ops, (r.motivo, nivel)
        r = ops[0]
    return (r.nivel, r.id)


@pytest.mark.parametrize("q", ["q1", "q2", "q3", "q4"])
def test_q1_q4_resuelven_como_sus_json(entradas, q):
    assert (RAIZ / "biblioteca/indicadores/fact_indicador.parquet").exists(), "falta el cubo (agents.md §8)"
    ctx = cargar_contexto(RAIZ)
    js = json.loads((RAIZ / "curados/motor/consultas_minimas" / f"{q}.json").read_text(encoding="utf-8"))
    e = next(x for x in entradas if x["pregunta"] == js["pregunta_original"])
    assert e["categoria"] == "q1_q4" and e["esperado"]["resultado"] == "consulta", e["id"]
    c = e["esperado"]["consulta"]
    for k in ("intencion", "tema"):
        assert c.get(k) == js[k], (q, k)
    assert (c.get("periodo") or {"tipo": "ultimo"}).get("tipo") == js["periodo"]["tipo"] or "periodo" not in c
    tj, tc = js["territorio"], c["territorio"]
    if "nivel" in tj:
        assert tc["nivel"] == tj["nivel"] and _resuelto(resolver(tc["dentro_de"], ctx)) == _resuelto(resolver(tj["dentro_de"], ctx))
    else:
        rj = resolver(tj, ctx)
        rc = resolver(tc, ctx)
        if q == "q1":                                       # «Huancavelica»: aclaración; con --elegir 1, el departamento
            assert isinstance(rc, Aclaracion)
        assert _resuelto(rc, rj.nivel) == _resuelto(rj)
