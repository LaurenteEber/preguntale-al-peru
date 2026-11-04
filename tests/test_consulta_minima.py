"""S1-01: la consulta mínima se valida contra el esquema y cada error sale en lenguaje sencillo."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest
import yaml

from pap.motor import consulta
from pap.motor.consulta import ConsultaInvalida, cargar

RAIZ = Path(__file__).resolve().parents[1]
ESQUEMA = json.loads((RAIZ / "curados/motor/esquemas/consulta_minima.schema.json").read_text(encoding="utf-8"))
MENSAJES = yaml.safe_load((RAIZ / "curados/motor/textos/errores_consulta.yaml").read_text(encoding="utf-8"))["mensajes"]
PARAMETROS = yaml.safe_load((RAIZ / "curados/motor/parametros_motor.yaml").read_text(encoding="utf-8"))
PROHIBIDAS = ["intencion", "tema", "indicador", "territorio", "periodo", "comparar_con", "ubigeo", "ambito", "nivel",
              "anio", "desde", "hasta", "schema", "json", "required", "additionalProperties"]

BASE = {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Puno"}, "periodo": {"tipo": "ultimo"}}


def _con(**cambios):
    d = copy.deepcopy(BASE)
    for k, v in cambios.items():
        if v is None:
            d.pop(k, None)
        else:
            d[k] = v
    return d


def _errores(datos):
    with pytest.raises(ConsultaInvalida) as e:
        cargar(datos, RAIZ)
    return e.value


@pytest.mark.parametrize("q", ["q1", "q2", "q3", "q4"])
def test_consultas_q1_q4_validan(q):
    ruta = RAIZ / "curados/motor/consultas_minimas" / f"{q}.json"
    r = cargar(ruta, RAIZ)
    assert r == cargar(json.loads(ruta.read_text(encoding="utf-8")), RAIZ)
    assert r["idioma"] == "es" and r["pregunta_original"]
    assert "(reconstruida)" not in r["pregunta_original"]


def test_idioma_por_defecto():
    assert cargar(copy.deepcopy(BASE), RAIZ)["idioma"] == "es"


def test_cargar_no_modifica_la_entrada():
    d = copy.deepcopy(BASE)
    cargar(d, RAIZ)
    assert d == BASE


CASOS = [
    ("intencion_fuera_vocabulario", _con(intencion="predecir"), "intencion_invalida"),
    ("tema_e_indicador", _con(indicador="endes_anemia_6_35m"), "tema_e_indicador"),
    ("ni_tema_ni_indicador", _con(tema=None), "tema_o_indicador"),
    ("periodo_imposible", _con(periodo={"tipo": "serie", "desde": 2024, "hasta": 2015}), "periodo_imposible"),
    ("anio_fuera_de_rango", _con(periodo={"tipo": "anio", "anio": 1800}), "periodo_invalido"),
    ("territorio_vacio", _con(territorio={}), "territorio_invalido"),
    ("territorio_texto_en_blanco", _con(territorio={"texto": "   "}), "territorio_invalido"),
    ("falta_territorio", _con(territorio=None), "falta_territorio"),
    ("falta_intencion", _con(intencion=None), "falta_intencion"),
    ("comparar_con_sin_comparacion", _con(comparar_con={"texto": "Cusco"}), "comparar_con_sin_comparacion"),
    ("campo_no_declarado_raiz", _con(cifras=[1]), "campo_desconocido"),
    ("campo_no_declarado_territorio", _con(territorio={"texto": "Puno", "id": "21"}), "territorio_invalido"),
    ("indicador_inexistente", _con(tema=None, indicador="no_existe_este"), "indicador_invalido"),
    ("extremo_con_texto", _con(intencion="identificar_extremo", territorio={"texto": "Puno"}),
     "territorio_extremo_invalido"),
    ("tema_fuera_vocabulario", _con(tema="educacion"), "tema_invalido"),
    ("comparar_con_mal_formado", _con(intencion="comparacion", comparar_con={"texto": ""}), "comparar_con_invalido"),
    ("no_es_objeto", ["anemia"], "no_es_objeto"),
]


@pytest.mark.parametrize("datos,codigo", [c[1:] for c in CASOS], ids=[c[0] for c in CASOS])
def test_invalidas(datos, codigo):
    e = _errores(datos)
    assert e.codigos == [codigo]
    assert e.mensajes == [MENSAJES[codigo]]
    for m in e.mensajes:
        for p in PROHIBIDAS:
            assert not re.search(rf"\b{p}\b", m, re.I), (p, m)


def test_varios_errores_mensajes_unicos_y_estables():
    d = _con(intencion="predecir", tema="educacion", territorio=None)
    e1, e2 = _errores(d), _errores(d)
    assert e1.mensajes == e2.mensajes and e1.codigos == e2.codigos
    assert len(set(e1.mensajes)) == len(e1.mensajes) == len(e1.codigos) >= 3


def test_extremo_valido_y_comparacion_valida():
    cargar(_con(intencion="identificar_extremo", territorio={"nivel": "distrito"}), RAIZ)
    cargar(_con(intencion="comparacion", comparar_con={"texto": "Cusco"}), RAIZ)


def test_todo_codigo_del_esquema_tiene_mensaje():
    codigos = set()

    def rec(n):
        if isinstance(n, dict):
            if "x-error" in n:
                codigos.add(n["x-error"])
            for v in n.values():
                rec(v)
        elif isinstance(n, list):
            for v in n:
                rec(v)
    rec(ESQUEMA)
    assert codigos and not codigos - set(MENSAJES)
    for c in ("periodo_imposible", "falta_territorio", "falta_intencion", "tema_e_indicador", "tema_o_indicador"):
        assert c in MENSAJES


def test_mensajes_sin_jerga():
    for c, m in MENSAJES.items():
        for p in PROHIBIDAS:
            assert not re.search(rf"\b{p}\b", m, re.I), (c, p)


def test_esquema_raiz_cerrado():
    assert ESQUEMA["additionalProperties"] is False


def test_vocabulario_de_temas_igual_a_parametros():
    assert ESQUEMA["properties"]["tema"]["enum"] == PARAMETROS["temas"]["vocabulario"]["valor"]
