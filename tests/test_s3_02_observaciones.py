"""S3-02 — Observaciones bajas aprobadas por el agente (agents.md §5.1): H14 y H15. H21 NO se hace: quitar los porcentajes de «Más contexto» de Q4 también hace desaparecer el aviso
de R-LENGUAJE-06 («Estas cifras vienen de fuentes de distinto tipo…»), lo que no cumple §5.1 (consulta W-02).

Una prueba por observación. El corrector no debe dar infracciones y la capa 1 queda dentro de R-04. H17 y H18 (caso B) no se
hacen: el dueño no los marcó. Si falta el cubo, las pruebas FALLAN (agents.md §8)."""
import pytest
import yaml

from pap.config import Rutas
from pap.motor import preguntar as PRE
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL
from test_regresion_q1_q4 import generado


@pytest.fixture(scope="module")
def raiz():
    r = Rutas(RAIZ_REAL).raiz
    assert (r / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    return r


@pytest.fixture(scope="module")
def motor(raiz):
    return Motor(cargar_contexto(raiz))


@pytest.fixture(scope="module")
def q(raiz, motor):
    return {k: motor.responder(generado(raiz, motor, k)) for k in ("q1", "q2", "q3", "q4")}


def sin_infracciones(raiz, r):
    p = yaml.safe_load((raiz / "curados" / "motor" / "parametros_motor.yaml").read_text(encoding="utf-8"))["respuesta"]
    assert r["capas"]["capa1"]["palabras"] <= p["capa1_palabras_max"]["valor"]
    infr = [x for x in r["resultados_respuesta"] if x["regla"] in p["infracciones_corrector"]["valor"] and x["accion"] != "rotular"]
    assert not infr, infr


def n(t):
    """Los espacios finos (U+202F) antes del % se leen como espacios normales."""
    return t.replace("\u202f", " ").replace("\u00a0", " ")


def terminos(r):
    return [g["termino"] for g in r["capas"]["capa3"]["glosario"]]


# ------------------------------------------------------------------------------------------------------------ H14

def test_h14_la_corta_dice_el_sujeto_una_sola_vez(raiz, motor):
    r = PRE.preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Huancavelica"}})     # X-22: el departamento a secas no pide elegir
    k = r["capas"]["capa1"]
    assert k["respuesta_corta"] == "En 2025, en Huancavelica, la anemia en niñas y niños de 6 a 35 meses fue:"
    assert not k["respuesta_corta"].startswith("Esto es lo que dicen")
    assert n(k["cifra_clave"]["valor"]) == "38,6 %"                       # la cifra no cambia
    sin_infracciones(raiz, r)


def test_h14_otros_temas_de_nivel_actual_usan_la_misma_forma(raiz, motor):
    r = PRE.preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "pobreza_monetaria", "territorio": {"texto": "Lima"}}, elegir=1)
    assert r["capas"]["capa1"]["respuesta_corta"] == "En 2025, en Lima Metropolitana, la pobreza monetaria fue:"
    sin_infracciones(raiz, r)


# ------------------------------------------------------------------------------------------------------------ H15

def test_h15_toda_respuesta_con_la_forma_de_medir_trae_su_glosario(raiz, motor, q):
    r = PRE.preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Huancavelica"}})     # X-22: el departamento a secas no pide elegir
    for nombre, x in [("nivel_actual", r), ("q1", q["q1"]), ("q2", q["q2"]), ("q3", q["q3"])]:
        assert "forma de medir la anemia" in terminos(x), nombre
        assert "forma de medir" in " ".join(x["capas"]["capa3"]["para_citar"]), nombre
        sin_infracciones(raiz, x)
    assert terminos(q["q1"]).count("forma de medir la anemia") == 1      # no se repite donde ya estaba
    assert "forma de medir la anemia" not in terminos(q["q4"])           # y no aparece donde no se usa
