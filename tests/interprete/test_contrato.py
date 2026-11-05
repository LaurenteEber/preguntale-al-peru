"""S2-01 — Contrato de la interpretación (curados/motor/esquemas/interpretacion.schema.json): un caso válido y uno inválido
por resultado y por restricción; Q1–Q4 como interpretación (sin pregunta_original ni idioma, con anclas de prueba)."""
import copy
import json

import pytest

from pap.config import Rutas
from pap.motor.interpretacion import InterpretacionInvalida, validar

from conftest import RAIZ_REAL

RAIZ = Rutas(RAIZ_REAL).raiz
CONSULTA = {"resultado": "consulta", "consulta": {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Puno"}},
            "anclas": {"intencion": "cuánta", "tema": "anemia", "territorio": "Puno"}}


def ok(d):
    assert validar(copy.deepcopy(d), RAIZ) == d


def mal(d, codigo=None):
    with pytest.raises(InterpretacionInvalida) as e:
        validar(copy.deepcopy(d), RAIZ)
    if codigo:
        assert codigo in e.value.codigos, e.value.codigos
    assert e.value.mensajes and all("{" not in m for m in e.value.mensajes)


def con(**cambios):
    d = copy.deepcopy(CONSULTA)
    for k, v in cambios.items():
        if v is None:
            d["consulta"].pop(k, None)
        else:
            d["consulta"][k] = v
    return d


# ------------------------------------------------------------------ los cinco resultados

def test_consulta_valida_e_invalida():
    ok(CONSULTA)
    mal({"resultado": "consulta", "consulta": CONSULTA["consulta"]})                      # sin anclas
    mal({"resultado": "nada"}, "resultado_invalido")


def test_aclaracion():
    op = {"consulta": CONSULTA["consulta"], "anclas": CONSULTA["anclas"]}
    otra = {"consulta": {**CONSULTA["consulta"], "intencion": "evolucion"}, "anclas": {**CONSULTA["anclas"], "intencion": "cambió"}}
    ok({"resultado": "aclaracion", "motivo": "intencion_ambigua", "opciones": [op, otra]})
    ok({"resultado": "aclaracion", "motivo": "varias_preguntas", "opciones": [op, otra]})
    mal({"resultado": "aclaracion", "motivo": "intencion_ambigua", "opciones": [op]}, "aclaracion_invalida")       # 1 opción
    mal({"resultado": "aclaracion", "motivo": "falta_lugar", "opciones": [op, otra]}, "aclaracion_invalida")       # lo arma el código
    mal({"resultado": "aclaracion", "motivo": "intencion_ambigua", "opciones": [op, otra, op, otra, op]},
        "aclaracion_demasiadas_opciones")                                                                       # tope en parámetros
    sin_ancla = {"consulta": CONSULTA["consulta"], "anclas": {"tema": "anemia"}}
    mal({"resultado": "aclaracion", "motivo": "intencion_ambigua", "opciones": [op, sin_ancla]})


def test_fuera_de_alcance():
    ok({"resultado": "fuera_de_alcance", "tipo": "tema", "pedido": "educación"})
    ok({"resultado": "fuera_de_alcance", "tipo": "pregunta", "pedido": "por qué hay tanta anemia"})
    mal({"resultado": "fuera_de_alcance", "tipo": "otro", "pedido": "educación"}, "fuera_de_alcance_invalido")
    mal({"resultado": "fuera_de_alcance", "tipo": "pregunta", "pedido": "anemia en 2030"}, "ancla_invalida")      # sin dígitos


def test_no_es_pregunta_y_otro_idioma():
    ok({"resultado": "no_es_pregunta"})
    ok({"resultado": "otro_idioma"})
    mal({"resultado": "no_es_pregunta", "consulta": CONSULTA["consulta"]})
    mal({"resultado": "otro_idioma", "pedido": "x"}, "idioma_invalido")


# ------------------------------------------------------------------ restricciones de la consulta (punto 3)

def test_intencion_y_tema_opcionales_con_el_mismo_vocabulario():
    d = con(intencion=None)
    d["anclas"].pop("intencion")
    ok(d)
    mal(con(intencion="ranking"), "intencion_invalida")
    d = con(tema=None)
    d["anclas"].pop("tema")
    ok(d)
    mal(con(tema="educacion"), "tema_invalido")


def test_sin_indicador_pregunta_original_ni_idioma():
    for campo, valor in (("indicador", "endes_anemia_6_35m"), ("pregunta_original", "¿cuánta anemia?"), ("idioma", "es")):
        mal(con(**{campo: valor}), "campo_desconocido")


def test_territorio_texto_o_nacional_sin_ubigeo_ni_ambito_ni_digitos():
    d = con(territorio={"nacional": True})
    ok(d)
    d = con(territorio=None)
    d["anclas"].pop("territorio")
    ok(d)                                                                                   # sin lugar: lo decide el código
    mal(con(territorio={"ubigeo": "21"}), "territorio_invalido")
    mal(con(territorio={"ambito": "LIMA_METROPOLITANA"}), "territorio_invalido")
    mal(con(territorio={"texto": "distrito 210801"}))


def test_comparar_con_solo_en_comparacion_y_sin_digitos():
    d = con(intencion="comparacion", comparar_con={"texto": "Cusco"})
    d["anclas"]["comparar_con"] = "Cusco"
    ok(d)
    d2 = copy.deepcopy(d)
    d2["consulta"]["comparar_con"] = {"texto": "08"}
    mal(d2)
    d3 = con(comparar_con={"texto": "Cusco"})
    d3["anclas"]["comparar_con"] = "Cusco"
    mal(d3, "comparar_con_sin_comparacion")


def test_extremo_nivel_y_dentro_de():
    d = {"resultado": "consulta", "consulta": {"intencion": "identificar_extremo", "tema": "pobreza_monetaria",
                                              "territorio": {"nivel": "distrito", "dentro_de": {"texto": "Puno"}}},
         "anclas": {"intencion": "más pobre", "tema": "pobre", "nivel": "distrito", "dentro_de": "Puno"}}
    ok(d)
    d2 = copy.deepcopy(d)
    d2["consulta"]["territorio"]["dentro_de"] = {"ubigeo": "21"}
    mal(d2, "territorio_extremo_invalido")
    d3 = copy.deepcopy(d)
    d3["consulta"]["territorio"] = {"texto": "Puno"}
    mal(d3, "territorio_extremo_invalido")


def test_periodo_formas_de_siempre():
    d = con(periodo={"tipo": "anio", "anio": 2024})
    d["anclas"]["anio"] = "2024"
    ok(d)
    d = con(periodo={"tipo": "serie", "desde": 2015, "hasta": 2024})
    d["anclas"].update(desde="2015", hasta="2024")
    ok(d)
    ok(con(periodo={"tipo": "ultimo"}))
    mal(con(periodo={"tipo": "anio", "anio": 1800}), "periodo_invalido")
    mal(con(periodo={"tipo": "relativo"}), "periodo_invalido")


# ------------------------------------------------------------------ anclas

def test_una_ancla_por_cada_valor_presente():
    for falta in ("intencion", "tema", "territorio"):
        d = copy.deepcopy(CONSULTA)
        d["anclas"].pop(falta)
        mal(d, "falta_ancla")
    d = con(periodo={"tipo": "anio", "anio": 2024})
    mal(d, "falta_ancla")                                                                   # el año sin su ancla
    d = copy.deepcopy(CONSULTA)
    d["anclas"]["periodo"] = "hoy"
    mal(d, "ancla_invalida")                                                                # ancla de un campo que no existe
    d = copy.deepcopy(CONSULTA)
    d["anclas"]["tema"] = "  "
    mal(d, "ancla_invalida")


# ------------------------------------------------------------------ Q1–Q4

@pytest.mark.parametrize("q", ["q1", "q2", "q3", "q4"])
def test_consultas_minimas_q1_q4_como_interpretacion(q):
    c = json.loads((RAIZ / "curados" / "motor" / "consultas_minimas" / f"{q}.json").read_text(encoding="utf-8"))
    c.pop("pregunta_original")
    c.pop("idioma")
    if "texto" in c["territorio"]:
        c["territorio"]["texto"] = c["territorio"]["texto"].replace("departamento de ", "")
    anclas = {"intencion": "ancla de prueba", "tema": "ancla de prueba"}
    t = c["territorio"]
    if "nivel" in t:
        anclas["nivel"] = "ancla de prueba"
        if "dentro_de" in t:
            anclas["dentro_de"] = "ancla de prueba"
    else:
        anclas["territorio"] = "ancla de prueba"
    if "anio" in c.get("periodo", {}):
        anclas["anio"] = "ancla de prueba"
    ok({"resultado": "consulta", "consulta": c, "anclas": anclas})


def test_q4_dentro_de_nacional_valida():
    c = json.loads((RAIZ / "curados" / "motor" / "consultas_minimas" / "q4.json").read_text(encoding="utf-8"))
    assert c["territorio"]["dentro_de"] == {"nacional": True}
