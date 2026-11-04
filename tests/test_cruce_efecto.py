"""S1-14 — Cruce y efecto: textos que no prometen ni contradicen (H9, H12 / AD-2, D-01).

Si falta el cubo, las pruebas FALLAN (agents.md §8)."""
import json

import pytest

from pap.config import Rutas
from pap.motor import preguntar as P
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL
from matriz import comprobar as C

RAIZ = Rutas(RAIZ_REAL).raiz
AD2 = "Estos datos muestran qué se gastó y cómo está el indicador; no muestran si el gasto lo cambió."


@pytest.fixture(scope="module")
def motor():
    assert (RAIZ / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    return Motor(cargar_contexto(RAIZ))


@pytest.fixture(scope="module")
def reglas():
    return json.loads((RAIZ / "reglas" / "reglas.json").read_text(encoding="utf-8"))


def _r(motor, intencion, lugar):
    return P.preguntar_minima(motor, {"intencion": intencion, "tema": "anemia", "territorio": {"texto": lugar}})


@pytest.mark.parametrize("lugar", ["departamento de Puno", "Lima Metropolitana", "Perú"])
def test_cruce_sin_lado_a_lado_en_la_capa_1(motor, lugar):
    r = _r(motor, "cruce", lugar)
    assert r["tipo"] == "respuesta"
    assert C.cruce(r) == []
    c1 = r["capas"]["capa1"]["respuesta_corta"]
    assert c1.startswith("La cifra clave es el gasto en servicios de salud y nutrición infantil. La de la anemia")
    assert "está en «Más contexto»" in c1
    endes = [t for t in r["capas"]["capa2"]["mas_contexto"] if t["titulo"].endswith("(encuesta a hogares)")]
    assert endes and all(t["etiqueta"] == "Otra fuente: se muestra junto, no explica la cifra clave." for t in endes)


def test_la_comprobacion_detecta_lado_a_lado(motor):
    r = _r(motor, "cruce", "departamento de Puno")
    malo = json.loads(json.dumps(r))
    malo["capas"]["capa1"]["respuesta_corta"] = "Estas cifras se muestran lado a lado."
    assert [f["codigo"] for f in C.cruce(malo)] == ["cruce_lado_a_lado_en_capa1"]


def test_efecto_usa_la_frase_de_ad2_y_no_la_etiqueta_del_cruce(motor):
    r = _r(motor, "efecto", "San Juan de Lurigancho")
    t = r["texto"]
    assert AD2 in t and "cómo cambió el indicador" not in t
    assert all(x["etiqueta"] != "Otra fuente: se muestra junto, no explica la cifra clave."
               for x in r["capas"]["capa2"]["mas_contexto"])


def test_ad2_en_reglas_json_con_la_primera_oracion_igual(reglas):
    r07 = next(x for x in reglas["reglas"] if x["id"] == "R-CRUCES-07")
    assert r07["mensaje_usuario"] == ("Saber si un gasto “sirvió” requiere una evaluación que compare con lo que habría pasado sin él. "
                                      + AD2)
    assert reglas["lenguaje"]["frases_estandar"]["efecto"] == (
        "Saber si un gasto o programa funcionó requiere una evaluación que compare con lo que habría pasado sin él. " + AD2)


def test_porcentaje_atribuible_dice_de_que_total_es(motor):
    r = _r(motor, "efecto", "San Juan de Lurigancho")
    t = r["texto"]
    assert "del gasto atribuido al departamento de Lima se puede ubicar en municipalidades y obras" in t
    assert "de este gasto se puede ubicar" not in t


def test_d01_lima_ofrece_las_tres_opciones_de_t03(reglas):
    r09 = next(x for x in reglas["reglas"] if x["id"] == "R-TERRITORIO-09")
    lima = r09["parametros"]["ambiguos_conocidos"]["Lima"]
    assert [o.split(" (")[0] for o in lima] == ["Lima Metropolitana", "Lima Región", "Callao"]
    assert "los otros dos" in r09["parametros"]["sin_respuesta"]["Lima"]
    assert "departamento de Lima completo" not in r09["casos_borde"] and "o el Callao" in r09["mensaje_usuario"]
