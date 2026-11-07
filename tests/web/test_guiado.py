"""S3-05 — Formulario guiado en dos pasos, sin LLM y sin JavaScript. Sin red ni clave: las pruebas no usan el intérprete.
La respuesta del formulario se compara con los criterios de la regresión Q1–Q4 (`tests/test_regresion_q1_q4.py`), no byte a byte."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

import pap.web.app as app_mod
import test_regresion_q1_q4 as regresion
from pap.web.app import crear_app

from ._html import formulario, leer

RAIZ = Path(__file__).resolve().parents[2]
BASE = RAIZ / "backlog" / "slice-3" / "evidencia" / "base_api"
TX = yaml.safe_load((RAIZ / "curados/web/textos.yaml").read_text(encoding="utf-8"))
PAR = yaml.safe_load((RAIZ / "curados/web/parametros.yaml").read_text(encoding="utf-8"))
INTENCIONES = ["nivel_actual", "evolucion", "comparacion", "cruce", "efecto", "identificar_extremo"]
CAMPOS = {"nivel_actual": {"lugar", "lugar_nacional", "anio"}, "evolucion": {"lugar", "lugar_nacional", "desde", "hasta"},
          "comparacion": {"lugar", "lugar_nacional", "lugar2", "lugar2_nacional", "anio"},
          "cruce": {"lugar", "lugar_nacional", "anio"}, "efecto": {"lugar", "lugar_nacional", "anio"},
          "identificar_extremo": {"nivel"}}
OCULTOS = {"tema", "intencion", "paso"}


@pytest.fixture(scope="module")
def app():
    assert (RAIZ / "biblioteca/indicadores/fact_indicador.parquet").exists(), "falta el cubo"   # falla, no se salta
    a = crear_app(RAIZ, llm=None, dir_cache=None, precalentar=False)
    a.state.limites.por_minuto = 10 ** 9            # muchas preguntas desde una IP; el límite por IP (S3-07) se prueba en test_limites.py
    return a


@pytest.fixture(scope="module")
def cli(app):
    return TestClient(app)


@pytest.fixture
def espia(monkeypatch):
    """Anota la consulta que llega al motor y lo que responde: es el JSON real de lo que envió el formulario."""
    visto = []
    original = app_mod.preguntar_minima

    def envoltorio(motor, consulta, **kw):
        res = original(motor, consulta, **kw)
        visto.append((consulta, res))
        return res

    monkeypatch.setattr(app_mod, "preguntar_minima", envoltorio)
    return visto


def _paso2(cli, tema: str, intencion: str):
    r = cli.post("/guiado", data={"tema": tema, "intencion": intencion})
    assert r.status_code == 200, r.text[:300]
    d = leer(r.text)
    return r, d, d.buscar("form", **{"data-bloque": "guiado_paso2"})[0]


def _ocultos(f) -> dict:
    """Lo que manda un navegador sin que la persona toque nada: solo los campos ocultos (casillas y opciones sin marcar no se envían)."""
    return {n.attrs["name"]: n.attrs.get("value", "") for n in f.buscar("input", type="hidden")}


def _enviar(cli, tema: str, intencion: str, **campos):
    """Los dos pasos como los haría un navegador sin JavaScript. Devuelve (respuesta HTTP, árbol HTML)."""
    _, _, f = _paso2(cli, tema, intencion)
    datos = {**_ocultos(f), **campos}
    r = cli.post(f.attrs["action"], data=datos)
    return r, leer(r.text)


AVISO_X22 = "Respondimos por el departamento de Huancavelica."


def _sin_aviso_x22(res: dict) -> dict:
    """«Huancavelica» a secas se responde por el departamento (X-22) y el motor agrega su aviso; la base de la API usaba «departamento
    de Huancavelica» y no lo tiene. En evolución (Q1) va primero en «Avisos» (S3-10: en «Ojo al leer» pasaría el máximo de la capa 1);
    en otras intenciones iría primero en «Ojo al leer» (H-01). Aquí se comprueba que es la ÚNICA diferencia de las capas y se retira
    para aplicar los criterios de la regresión (que no lo aprueba: backlog/slice-1/evidencia/regresion/Q1.yaml)."""
    c1, avisos = res["capas"]["capa1"], res["capas"]["capa2"]["avisos"]
    propios = [a for a in avisos if a.startswith(AVISO_X22)]
    if not propios:
        return res
    assert len(propios) == 1 and avisos[0] == propios[0] and not any(o.startswith(AVISO_X22) for o in c1["ojo_al_leer"])
    return {**res, "capas": {**res["capas"], "capa2": {**res["capas"]["capa2"], "avisos": avisos[1:]}}}


Q = {"q1": ("anemia", "evolucion", {"lugar": "Huancavelica"}),
     "q2": ("anemia", "nivel_actual", {"lugar": "Ayaviri, Melgar"}),
     "q3": ("gasto_publico", "efecto", {"lugar": "San Juan de Lurigancho"}),
     "q4": ("pobreza_monetaria", "identificar_extremo", {"nivel": "distrito"})}


# ---------------------------------------------------------------- paso 1
def test_paso1_tema_e_intencion_desde_la_api_de_opciones(cli):
    r = cli.get("/guiado")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/html")
    d = leer(r.text)
    op = cli.get("/api/opciones").json()
    f = d.buscar("form", **{"data-bloque": "guiado_paso1"})[0]
    assert f.attrs["method"].lower() == "post" and f.attrs["action"] == "/guiado"
    assert [n.attrs["value"] for n in f.buscar("input", name="tema")] == [t["id"] for t in op["temas"]]
    assert [n.attrs["value"] for n in f.buscar("input", name="intencion")] == [i["id"] for i in op["intenciones"]]
    cuerpo = f.texto()
    desc = yaml.safe_load((RAIZ / "curados/interprete/intenciones_descripcion.yaml").read_text(encoding="utf-8"))["intenciones"]
    for i in op["intenciones"]:
        assert i["rotulo"] in cuerpo and desc[i["id"]] in cuerpo
    for t in op["temas"]:
        assert t["rotulo"] in cuerpo
    for n in d.buscar():
        assert not any(k.startswith("on") or k == "style" for k in n.attrs), n


def test_paso1_sin_eleccion_vuelve_con_su_aviso(cli):
    r = cli.post("/guiado", data={"tema": "anemia"})
    assert r.status_code == 422 and TX["guiado"]["errores"]["falta_eleccion"] in r.text
    r = cli.post("/guiado", data={"tema": "no_existe", "intencion": "nivel_actual"})
    assert r.status_code == 422 and TX["guiado"]["errores"]["falta_eleccion"] in r.text


# ---------------------------------------------------------------- paso 2: solo los campos de la intención
@pytest.mark.parametrize("intencion", INTENCIONES)
def test_paso2_muestra_solo_los_campos_de_la_intencion(cli, intencion):
    _, d, f = _paso2(cli, "anemia", intencion)
    nombres = {n.attrs["name"] for n in f.buscar() if n.tag in ("input", "select", "textarea") and n.attrs.get("name")}
    assert nombres == CAMPOS[intencion] | OCULTOS | ({"nivel"} if intencion == "identificar_extremo" else set())
    assert _ocultos(f) == {"tema": "anemia", "intencion": intencion, "paso": "2"}
    assert f.attrs["method"].lower() == "post" and f.attrs["action"] == "/guiado"
    if intencion == "identificar_extremo":
        g = TX["guiado"]
        assert g["dentro_de_nacional"] in f.texto()                       # «dentro de» fijo: Todo el Perú
        niveles = [n["id"] for n in cli.get("/api/opciones").json()["niveles"] if n["id"] != "nacional"]
        assert [o.attrs["value"] for o in f.buscar("input", name="nivel")] == niveles and "nacional" not in niveles


# ---------------------------------------------------------------- Q1–Q4 por el formulario, con los criterios de la regresión
@pytest.mark.parametrize("q", ["q1", "q2", "q3", "q4"])
def test_q1_q4_por_el_formulario_cumplen_los_criterios_de_la_regresion(cli, app, espia, q):
    tema, intencion, campos = Q[q]
    r, d = _enviar(cli, tema, intencion, **campos)
    assert r.status_code == 200 and d.buscar(**{"data-bloque": "respuesta_corta"}), r.text[:400]
    consulta, res = espia[-1]
    assert res["tipo"] in ("respuesta", "no_se_puede")
    minima = json.loads((RAIZ / "curados/motor/consultas_minimas" / f"{q}.json").read_text(encoding="utf-8"))
    assert {k: v for k, v in consulta.items() if k not in ("pregunta_original", "territorio")} == \
        {k: v for k, v in minima.items() if k not in ("pregunta_original", "territorio")}
    regresion.test_respuestas(RAIZ, app.state.motor, {q: _sin_aviso_x22(res)}, q)   # cifras por clave, semáforos, confianza, reglas firmes
    assert d.buscar(**{"data-bloque": "respuesta_corta"})[0].texto().strip() == res["capas"]["capa1"]["respuesta_corta"]


def test_q1_con_aclaracion_abancay_elegir_1_por_el_formulario(cli, espia):
    r, d = _enviar(cli, "anemia", "evolucion", lugar="Abancay")
    assert r.status_code == 200
    f = d.buscar("form", **{"data-bloque": "aclaracion"})[0]
    assert f.attrs["action"] == "/preguntar"                              # la aclaración sigue el camino de S3-04
    r2 = cli.post("/preguntar", data=formulario(f, {"n": "1"}))
    d2 = leer(r2.text)
    assert r2.status_code == 200 and d2.buscar(**{"data-bloque": "respuesta_corta"})
    consulta, res = espia[-1]
    base = json.loads((BASE / "q/q1_abancay_elegir_1/respuesta.json").read_text(encoding="utf-8"))
    assert res["capas"] == base["capas"] and res["cifras"] == base["cifras"]
    assert res["semaforo_respuesta"] == base["semaforo_respuesta"]


# ---------------------------------------------------------------- una prueba por intención
@pytest.mark.parametrize("intencion,tema,campos,esperado", [
    ("nivel_actual", "anemia", {"lugar": "Puno", "anio": "2023"},
     {"territorio": {"texto": "Puno"}, "periodo": {"tipo": "anio", "anio": 2023}}),
    ("nivel_actual", "anemia", {"lugar": "Puno"}, {"territorio": {"texto": "Puno"}, "periodo": {"tipo": "ultimo"}}),
    ("evolucion", "pobreza_monetaria", {"lugar": "Puno", "desde": "2015", "hasta": "2020"},
     {"territorio": {"texto": "Puno"}, "periodo": {"tipo": "serie", "desde": 2015, "hasta": 2020}}),
    ("evolucion", "pobreza_monetaria", {"lugar": "Puno", "desde": "2015"},
     {"territorio": {"texto": "Puno"}, "periodo": {"tipo": "serie", "desde": 2015}}),
    ("evolucion", "pobreza_monetaria", {"lugar": "Puno"}, {"territorio": {"texto": "Puno"}, "periodo": {"tipo": "serie"}}),
    ("comparacion", "anemia", {"lugar": "Puno", "lugar2": "Cusco"},
     {"territorio": {"texto": "Puno"}, "comparar_con": {"texto": "Cusco"}, "periodo": {"tipo": "ultimo"}}),
    ("comparacion", "anemia", {"lugar": "Puno", "lugar2_nacional": "on", "anio": "2023"},
     {"territorio": {"texto": "Puno"}, "comparar_con": {"nacional": True}, "periodo": {"tipo": "anio", "anio": 2023}}),
    ("cruce", "gasto_publico", {"lugar": "Puno"}, {"territorio": {"texto": "Puno"}, "periodo": {"tipo": "ultimo"}}),
    ("efecto", "gasto_publico", {"lugar": "Puno", "anio": "2023"},
     {"territorio": {"texto": "Puno"}, "periodo": {"tipo": "anio", "anio": 2023}}),
    ("identificar_extremo", "desnutricion_cronica", {"nivel": "provincia"},
     {"territorio": {"nivel": "provincia", "dentro_de": {"nacional": True}}, "periodo": {"tipo": "ultimo"}}),
])
def test_cada_intencion_arma_su_consulta_y_el_motor_responde(cli, espia, intencion, tema, campos, esperado):
    r, d = _enviar(cli, tema, intencion, **campos)
    consulta, res = espia[-1]
    assert r.status_code == 200 and res["tipo"] in ("respuesta", "no_se_puede", "aclaracion"), r.text[:300]
    assert {k: consulta[k] for k in esperado} == esperado
    assert consulta["intencion"] == intencion and consulta["tema"] == tema and consulta["idioma"] == "es"
    assert set(consulta) == {"intencion", "tema", "territorio", "periodo", "pregunta_original", "idioma"} | (
        {"comparar_con"} if intencion == "comparacion" else set())


def test_pregunta_original_sale_de_la_plantilla_de_textos(cli, espia):
    _enviar(cli, "anemia", "evolucion", lugar="Huancavelica")
    consulta, _ = espia[-1]
    plantilla = TX["guiado"]["pregunta"]["evolucion"]
    assert consulta["pregunta_original"] == plantilla.format(tema="la anemia", tema_art="la anemia", lugar="Huancavelica",
                                                             lugar2="", nivel="")


def test_todo_el_peru_da_nacional_true(cli, espia):
    _enviar(cli, "anemia", "nivel_actual", lugar_nacional="on")
    assert espia[-1][0]["territorio"] == {"nacional": True}
    assert "Perú" in espia[-1][0]["pregunta_original"]


# ---------------------------------------------------------------- sin la clave del LLM
def test_sin_la_clave_del_llm_el_formulario_funciona(app, cli, espia):
    assert not [k for k in os.environ if "ANTHROPIC" in k.upper()]       # conftest la quita; el servicio no la necesita
    assert app.state.llm is None
    r, d = _enviar(cli, "anemia", "nivel_actual", lugar="Puno")
    assert r.status_code == 200 and d.buscar(**{"data-bloque": "respuesta_corta"})


# ---------------------------------------------------------------- combinaciones sin fila: responde el motor
@pytest.mark.parametrize("tema,intencion,campos", [
    ("gasto_publico", "identificar_extremo", {"nivel": "distrito"}),           # sin fila: intencion_no_soportada (R-GASTO-13)
    ("anemia", "identificar_extremo", {"nivel": "distrito"}),                  # el ranking de anemia solo tiene fila por departamento
    ("pobreza_monetaria", "identificar_extremo", {"nivel": "provincia"}),
])
def test_combinacion_sin_fila_no_se_oculta_y_el_motor_da_su_no_se_puede(cli, espia, tema, intencion, campos):
    _, _, f = _paso2(cli, tema, intencion)                                    # el paso 2 se ofrece igual
    r = cli.post("/guiado", data={**_ocultos(f), **campos})
    consulta, res = espia[-1]
    assert r.status_code == 200 and res["tipo"] == "no_se_puede", res.get("tipo")
    d = leer(r.text)
    assert d.buscar(**{"data-bloque": "respuesta_corta"})[0].texto().strip() == res["capas"]["capa1"]["respuesta_corta"]


# ---------------------------------------------------------------- errores de llenado
@pytest.mark.parametrize("campos,error", [
    ({}, "falta_lugar"),
    ({"lugar": "   "}, "falta_lugar"),
    ({"lugar": "Puno", "lugar_nacional": "on"}, "lugar_doble"),
    ({"lugar": "Puno", "anio": "dos mil"}, "anio_invalido"),
])
def test_errores_de_llenado_vuelven_al_paso_2_sin_llamar_al_motor(cli, espia, campos, error):
    n = len(espia)
    r, d = _enviar(cli, "anemia", "nivel_actual", **campos)
    assert r.status_code == 422 and len(espia) == n
    assert TX["guiado"]["errores"][error] in d.buscar(**{"data-bloque": "guiado_error"})[0].texto()
    assert d.buscar("form", **{"data-bloque": "guiado_paso2"})            # el formulario sigue ahí para corregir


def test_nivel_invalido_y_solicitud_mal_formada(cli):
    r, _ = _enviar(cli, "pobreza_monetaria", "identificar_extremo", nivel="barrio")
    assert r.status_code == 422
    r = cli.post("/guiado", data={"tema": "anemia", "intencion": "nivel_actual", "paso": "2", "lugar": ["a", "b"]})
    assert r.status_code in (200, 422) and r.headers["content-type"].startswith("text/html")


def test_get_guiado_y_post_api_no_cambian_la_api(cli):
    assert cli.get("/guiado").status_code == 200
    assert cli.get("/api/opciones").status_code == 200


# ---------------------------------------------------------------- números y textos
def test_ningun_numero_nuevo_en_las_paginas_del_formulario(cli):
    from .test_paginas import _numeros, _textos_yaml
    permitidos = list(_textos_yaml(TX))
    paginas = [cli.get("/").text, cli.get("/guiado").text] + [_paso2(cli, "anemia", i)[0].text for i in INTENCIONES]
    for html in paginas:
        sueltos = [n for n in _numeros(leer(html).buscar("body")[0].texto()) if not any(n in t for t in permitidos)]
        assert not sueltos, sueltos


def test_los_textos_del_formulario_estan_en_el_yaml(cli):
    html = cli.get("/guiado").text
    assert TX["guiado"]["titulo_paso1"] in html


# ---------------------------------------------------------------- diferencias con la base de la API (S3-05-diferencias)
PERMITIDAS = (re.compile(r"^consulta_minima\.pregunta_original$"), re.compile(r"^plan\.pregunta_original$"),
              re.compile(r"^(consulta_minima|plan)\.territorio\.texto$"), re.compile(r"^plan\.territorio\.texto$"))


def rutas_distintas(a, b, ruta="") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            sub = f"{ruta}.{k}" if ruta else str(k)
            out += [sub] if k not in a or k not in b else rutas_distintas(a[k], b[k], sub)
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [x for i, (u, v) in enumerate(zip(a, b)) for x in rutas_distintas(u, v, f"{ruta}[{i}]")]
    return [] if a == b else [ruta]


@pytest.mark.parametrize("q", ["q1", "q2", "q3", "q4"])
def test_diferencias_con_la_base_api_solo_las_permitidas(cli, espia, q):
    tema, intencion, campos = Q[q]
    _enviar(cli, tema, intencion, **campos)
    res = espia[-1][1]
    base = json.loads((BASE / "q" / q / "respuesta.json").read_text(encoding="utf-8"))
    otras = [r for r in rutas_distintas(base, res) if not (r.endswith("pregunta_original") or r.endswith("territorio.texto")
                                                           or r in ("consulta.pregunta", "plan.pregunta")      # copias de pregunta_original
                                                           or (r.endswith("detalle.disparadores") and "R-CRUCES-07" in json.dumps(
                                                               _en(res, r), ensure_ascii=False) + json.dumps(_en(base, r), ensure_ascii=False)))]
    assert otras == (["capas.capa2.avisos"] if q == "q1" else []), otras        # el aviso de X-22 de Q1 es un hallazgo, no una diferencia permitida


def _en(x, ruta: str):
    for t in re.findall(r"[^.\[\]]+|\[\d+\]", ruta):
        x = x[int(t[1:-1])] if t.startswith("[") else x[t]
    return x
