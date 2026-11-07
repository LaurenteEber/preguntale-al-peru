"""S3-04 — Páginas: inicio, respuesta, aclaración y mensajes. Sin red ni clave: el LLM son las grabaciones (modo «reproducir»).
La web no tiene lógica de respuesta: cada bloque sale de un campo de `respuesta.json` o de un YAML de textos."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from pap.interprete.llm import Cliente, NoDisponible
from pap.web.app import crear_app

from ._html import formulario, leer

RAIZ = Path(__file__).resolve().parents[2]
BASE = RAIZ / "backlog" / "slice-3" / "evidencia" / "base_api"
TX = yaml.safe_load((RAIZ / "curados/web/textos.yaml").read_text(encoding="utf-8"))
PAR = yaml.safe_load((RAIZ / "curados/web/parametros.yaml").read_text(encoding="utf-8"))
ROT = yaml.safe_load((RAIZ / "curados/motor/textos/capas.yaml").read_text(encoding="utf-8"))["rotulos"]
Q1_Q4 = ["q1", "q2", "q3", "q4"]
ORDEN = ["entendimos", "respuesta_corta", "cifra_clave", "lo_mas_cercano", "ojo_al_leer", "confianza", "que_hacer",
         "mas_contexto", "para_citar"]


def _casos(grupo: str) -> list[Path]:
    return sorted((BASE / grupo).iterdir())


def _leer(carpeta: Path) -> tuple[dict, dict]:
    return (json.loads((carpeta / "entrada.json").read_text(encoding="utf-8")),
            json.loads((carpeta / "respuesta.json").read_text(encoding="utf-8")))


def _sin_limite(app):
    """Estas pruebas hacen cientos de preguntas desde una misma IP; el límite por IP (S3-07) se prueba en test_limites.py."""
    app.state.limites.por_minuto = 10 ** 9
    return app


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    assert (RAIZ / "biblioteca/indicadores/fact_indicador.parquet").exists(), "falta el cubo"   # falla, no se salta
    return _sin_limite(crear_app(RAIZ, llm=Cliente(RAIZ, modo="reproducir"), dir_cache=tmp_path_factory.mktemp("cache"), precalentar=False))


@pytest.fixture(scope="module")
def cli(app):
    return TestClient(app)


def _formulario_de(ent: dict) -> dict:
    """Lo que manda el formulario HTML para esa entrada (los mismos datos que el cuerpo de /api/preguntar)."""
    d = {"texto": ent["pregunta"]} if "pregunta" in ent else {"consulta": json.dumps(ent["consulta"], ensure_ascii=False)}
    if ent.get("elegir") is not None:
        d["elegir"] = ",".join(str(n) for n in ([ent["elegir"]] if isinstance(ent["elegir"], int) else ent["elegir"]))
    return d


def _pagina(cli, datos: dict):
    r = cli.post("/preguntar", data=datos)
    assert r.headers["content-type"].startswith("text/html"), r.text[:300]
    return r, leer(r.text)


def _bloques(raiz) -> list[str]:
    return [n.attrs["data-bloque"] for n in raiz.buscar(**{"data-bloque": True}) if n.attrs["data-bloque"] in ORDEN]


def _orden_esperado(res: dict) -> list[str]:
    c1, c2 = res["capas"]["capa1"], res["capas"]["capa2"]
    hay = {
        "entendimos": bool(res.get("entendimos")),
        "respuesta_corta": bool(c1.get("respuesta_corta")),
        "cifra_clave": bool(c1.get("cifra_clave")),
        "lo_mas_cercano": bool(c1.get("lo_mas_cercano") or res.get("alternativas") or res.get("temas_disponibles")),
        "ojo_al_leer": bool(c1.get("ojo_al_leer")),
        "confianza": bool((c1.get("confianza") or {}).get("texto")),
        "que_hacer": bool(c1.get("que_hacer") and (c1["que_hacer"].get("revisado_dueno") or PAR["paginas"]["mostrar_que_hacer_sin_revisar"]["valor"])),      # H-03
        "mas_contexto": bool(c2.get("mas_contexto") or c2.get("avisos") or c2.get("limites")),
        "para_citar": True,                                             # lleva siempre el rótulo de versión
    }
    orden = list(ORDEN)
    if res["tipo"] == "no_se_puede":                                    # R-04: lo que no se puede, primero
        orden.remove("respuesta_corta")
        orden.insert(0, "respuesta_corta")
    return [b for b in orden if hay[b]]


# ---------------------------------------------------------------- inicio
def test_inicio_caja_ejemplos_temas_y_enlace_guiado(cli):
    r = cli.get("/")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/html")
    d = leer(r.text)
    forms = [f for f in d.buscar("form") if f.attrs.get("action") == "/preguntar"]
    assert forms and all(f.attrs["method"].lower() == "post" for f in forms)
    caja = d.buscar("textarea", name="texto")
    assert len(caja) == 1 and d.buscar("label")                         # la caja tiene su etiqueta
    ejemplos = [b for b in d.buscar("button", name="texto")]
    assert [b.attrs["value"] for b in ejemplos] == TX["ejemplos"] and 3 <= len(ejemplos) <= 4
    cuerpo = d.buscar("body")[0].texto()
    for t in TX["rotulos_temas"].values():
        assert t.lower() in cuerpo.lower()
    assert TX["paginas"]["fuentes_hoy"] in cuerpo
    assert [a.attrs["href"] for a in d.buscar("a", href="/guiado")]      # lo construye S3-05; se enlaza igual


def test_titulos_y_lengua(cli):
    d = leer(cli.get("/").text)
    assert d.buscar("html")[0].attrs["lang"] == "es"
    assert d.buscar("title")[0].texto().strip() == TX["paginas"]["titulo_sitio"]
    assert len(d.buscar("h1")) == 1


# ---------------------------------------------------------------- seguridad
def _todas_las_paginas(cli):
    yield "GET /", cli.get("/")
    ent, _ = _leer(_casos("q")[0])
    yield "POST respuesta", cli.post("/preguntar", data=_formulario_de(ent))
    yield "POST aclaración", cli.post("/preguntar", data={"texto": "¿Cuánta anemia hay en Lima?"})
    yield "POST error", cli.post("/preguntar", data={"consulta": "no es json"})
    yield "estático js", cli.get("/estatico/app.js")
    yield "estático css", cli.get("/estatico/estilo.css")


def test_cabecera_csp_sin_cookies_y_sin_origenes_externos(cli):
    for nombre, r in _todas_las_paginas(cli):
        assert "set-cookie" not in {k.lower() for k in r.headers}, nombre
        if r.headers["content-type"].startswith("text/html"):
            csp = r.headers["content-security-policy"]
            assert "default-src 'self'" in csp, nombre
            assert not re.search(r"https?:|\*", csp), nombre
            d = leer(r.text)
            for n in d.buscar():
                for atributo in ("src", "href", "action", "srcset", "poster"):
                    v = n.attrs.get(atributo, "")
                    if n.tag == "a" and atributo == "href":
                        continue                                        # los enlaces a documentos oficiales no cargan nada
                    assert not re.match(r"(https?:)?//", v), (nombre, n)
            assert not re.search(r"@import|url\(\s*['\"]?https?:", r.text), nombre


def test_un_solo_js_y_un_solo_css_propios(cli):
    d = leer(cli.get("/").text)
    scripts = d.buscar("script")
    assert [s.attrs.get("src") for s in scripts] == ["/estatico/app.js"] and all(not s.texto().strip() for s in scripts)
    assert [h.attrs["href"] for h in d.buscar("link", rel="stylesheet")] == ["/estatico/estilo.css"]
    assert not d.buscar("style")                                        # nada de estilos en la página
    for n in d.buscar():
        assert not any(k.startswith("on") or k == "style" for k in n.attrs), n   # ni manejadores ni estilos en línea
    js, css = cli.get("/estatico/app.js"), cli.get("/estatico/estilo.css")
    assert js.status_code == 200 and "javascript" in js.headers["content-type"]
    assert css.status_code == 200 and css.headers["content-type"].startswith("text/css")


def test_estilo_movil_primero_letra_base_y_modo_oscuro(cli):
    css = cli.get("/estatico/estilo.css").text
    assert "prefers-color-scheme: dark" in css
    m = re.search(r"html\s*\{[^}]*font-size:\s*(\d+(?:\.\d+)?)(px|rem|%)", css)
    assert m, "la letra base va en `html`"
    px = {"px": 1, "rem": 16, "%": 0.16}[m.group(2)] * float(m.group(1))
    assert px >= 16
    assert "max-width" not in " ".join(re.findall(r"@media[^{]*", css)), "móvil primero: las consultas de medios usan min-width"
    assert not re.search(r"\.(alta|media|baja|verde|ambar|ámbar|rojo)\b", css)      # R-05: sin color por nivel de confianza


def test_los_textos_visibles_no_estan_en_el_js_ni_en_las_plantillas(cli):
    js = re.sub(r"/\*.*?\*/", "", cli.get("/estatico/app.js").text, flags=re.S)          # sin comentarios
    assert js.isascii() and "Buscando" not in js                        # el texto viaja en un atributo que pone la plantilla
    literales = re.findall(r"\"(?:[^\"\\\n]|\\.)*\"|'(?:[^'\\\n]|\\.)*'", js)
    assert literales and not [x for x in literales if re.search(r"\s", x)], "cadenas con espacios: ¿texto visible?"
    for f in (RAIZ / "src/pap/web/plantillas").glob("*.html"):
        sin_jinja = re.sub(r"\{[{%#].*?[}%#]\}", "", f.read_text(encoding="utf-8"), flags=re.S)
        sin_etiquetas = re.sub(r"<[^>]*>", "", sin_jinja)
        assert not re.search(r"[A-Za-zÁÉÍÓÚáéíóúñ]{2,}", sin_etiquetas), f"{f.name}: texto visible escrito en la plantilla"


# ---------------------------------------------------------------- orden de los bloques
@pytest.mark.parametrize("q", Q1_Q4)
def test_orden_de_bloques_q1_q4(cli, q):
    ent, res = _leer(BASE / "q" / q)
    assert res["tipo"] == "respuesta"
    r, d = _pagina(cli, _formulario_de(ent))
    assert r.status_code == 200
    assert _bloques(d) == _orden_esperado(res)
    assert _bloques(d)[:2] == ["respuesta_corta", "cifra_clave"]         # Q1–Q4 por consulta: no hay «Entendimos»
    for b in ("mas_contexto", "para_citar"):                             # desplegables, cerrados
        det = d.buscar("details", **{"data-bloque": b})
        assert len(det) == 1 and "open" not in det[0].attrs and det[0].buscar("summary")
    assert res["capas"]["capa1"]["respuesta_corta"] in d.buscar(**{"data-bloque": "respuesta_corta"})[0].texto()


def test_orden_de_bloques_con_entendimos_por_texto(cli, tmp_path, app):
    app.state.dir_cache = tmp_path
    ent, res = _leer(BASE / "evaluacion" / "d01")
    r, d = _pagina(cli, _formulario_de(ent))
    assert res["entendimos"] and _bloques(d) == _orden_esperado(res) and _bloques(d)[0] == "entendimos"
    assert d.buscar(**{"data-bloque": "entendimos"})[0].texto().strip() == res["entendimos"]
    assert not d.buscar(**{"data-eco": True})                            # la pregunta escrita solo se repite en la aclaración


def test_orden_de_bloques_en_toda_la_matriz_y_la_base_q(cli):
    n = {"respuesta": 0, "no_se_puede": 0}
    for c in _casos("q") + _casos("matriz"):
        ent, res = _leer(c)
        if res["tipo"] not in n:
            continue
        r, d = _pagina(cli, _formulario_de(ent))
        assert _bloques(d) == _orden_esperado(res), c.name
        n[res["tipo"]] += 1
    assert n["respuesta"] >= 4 and n["no_se_puede"] >= 4, n


def test_no_se_puede_pone_primero_lo_que_no_se_puede(cli):
    visto = 0
    for c in _casos("matriz"):
        ent, res = _leer(c)
        if res["tipo"] != "no_se_puede":
            continue
        r, d = _pagina(cli, _formulario_de(ent))
        assert _bloques(d)[0] == "respuesta_corta", c.name
        assert d.buscar(**{"data-bloque": "respuesta_corta"})[0].texto().strip() == res["capas"]["capa1"]["respuesta_corta"]
        lc = d.buscar(**{"data-bloque": "lo_mas_cercano"})[0].texto()
        assert res["capas"]["capa1"]["lo_mas_cercano"]["titulo"] in lc and res["capas"]["capa1"]["lo_mas_cercano"]["texto"] in lc
        visto += 1
    assert visto


def test_no_se_puede_por_texto_con_entendimos_y_temas_disponibles(cli, app, tmp_path):
    for caso, tema_lista in (("a02", False), ("ft01", True)):
        app.state.dir_cache = tmp_path / caso
        ent, res = _leer(BASE / "evaluacion" / caso)
        assert res["tipo"] == "no_se_puede"
        r, d = _pagina(cli, _formulario_de(ent))
        assert _bloques(d) == _orden_esperado(res) and _bloques(d)[0] == "respuesta_corta"
        lc = d.buscar(**{"data-bloque": "lo_mas_cercano"})[0]
        if tema_lista:
            assert [li.texto().strip() for li in lc.buscar("li")] == [t["nombre"] for t in res["temas_disponibles"]]
        else:                                                            # una alternativa con consulta: botón que la reenvía
            botones = lc.buscar("button")
            assert len(botones) == len(res["alternativas"])
            f = [x for x in lc.buscar("form")][0]
            assert json.loads(formulario(f)["consulta"]) == res["alternativas"][0]["consulta_minima"]


def test_cada_bloque_sale_de_su_campo_y_el_enlace_oficial_es_un_ancla(cli):
    ent, res = _leer(BASE / "q" / "q1")
    r, d = _pagina(cli, _formulario_de(ent))
    c1, c3 = res["capas"]["capa1"], res["capas"]["capa3"]
    ck = d.buscar(**{"data-bloque": "cifra_clave"})[0].texto()
    assert c1["cifra_clave"]["valor"] in ck and c1["cifra_clave"]["texto"] in ck and c1["cifra_clave"]["fuente"] in ck
    ojo = d.buscar(**{"data-bloque": "ojo_al_leer"})[0]
    assert ROT["ojo_al_leer"] in ojo.texto() and [li.texto().strip() for li in ojo.buscar("li")] == c1["ojo_al_leer"]
    assert c1["que_hacer"]["revisado_dueno"] is False and not d.buscar(**{"data-bloque": "que_hacer"})      # H-03: oculto hasta que el dueño apruebe X-01
    pc = d.buscar(**{"data-bloque": "para_citar"})[0]
    assert [a.attrs["href"] for a in pc.buscar("a") if a.texto().strip() == ROT["enlace_oficial"]] \
        == [x["url"] for x in c3["citas"] if x["url"]]
    for x in c3["citas"]:
        assert x["texto"] in pc.texto()
    for g in c3["glosario"]:
        assert g["termino"] in pc.texto() and g["definicion"] in pc.texto()
    v = json.loads(cli.get("/api/version").text)["rotulo"]
    assert v in pc.texto()
    mc = d.buscar(**{"data-bloque": "mas_contexto"})[0].texto()
    for t in res["capas"]["capa2"]["mas_contexto"]:
        assert t["titulo"] in mc and t["texto"] in mc
    for x in res["capas"]["capa2"]["limites"]:
        assert x in mc


def test_sin_bloque_de_ficha_tecnica(cli):
    ent, res = _leer(BASE / "q" / "q1")
    r, d = _pagina(cli, _formulario_de(ent))
    for prohibido in (res["ficha"]["corta"], "Detalle técnico", "Semáforo", "semáforo"):
        assert prohibido not in r.text
    assert res["semaforo_respuesta"] and f'"{res["semaforo_respuesta"]}"' not in r.text


# ---------------------------------------------------------------- confianza (R-05)
@pytest.mark.parametrize("q", Q1_Q4)
def test_confianza_solo_el_texto_sin_clase_por_nivel_ni_rotulo_de_ficha(cli, q):
    ent, res = _leer(BASE / "q" / q)
    conf = res["capas"]["capa1"]["confianza"]
    r, d = _pagina(cli, _formulario_de(ent))
    bloque = d.buscar(**{"data-bloque": "confianza"})[0]
    assert bloque.texto().strip() == conf["texto"]
    for n in bloque.recorrer():                                          # ni clase ni atributo ni elemento por nivel
        assert set(n.attrs) <= {"data-bloque", "class"}, n
        for v in (n.attrs.get("class") or "").split():
            assert v not in {conf["nivel"], "alta", "media", "baja", "verde", "ambar", "ámbar", "rojo"}
    assert conf["ficha"] not in r.text
    assert conf["ficha"].split(":")[1].split("):")[0].strip() not in r.text   # el rótulo técnico («alta (dato sólido)…»)
    assert not re.search(r"dato (sólido|aproximado|muy aproximado)", r.text)


# ---------------------------------------------------------------- aclaración
def _elegir(cli, pagina_html: str, n: int):
    d = leer(pagina_html)
    f = d.buscar("form", **{"data-bloque": "aclaracion"})[0]
    assert f.attrs["method"].lower() == "post" and f.attrs["action"] == "/preguntar"
    botones = {b.attrs["value"] for b in f.buscar("button", name="n")}
    assert str(n) in botones
    return _pagina(cli, formulario(f, {"n": str(n)})), d, f


SIN_LUGAR = {"intencion": "comparacion", "tema": "anemia", "territorio": {"texto": "Ayaviri"}, "comparar_con": {"texto": "Ayaviri"},
             "periodo": {"tipo": "ultimo"}, "pregunta_original": "prueba de elegir acumulado", "idioma": "es"}


def test_aclaracion_dos_lugares_elegir_acumulado_con_consulta(cli):
    r0, d0 = _pagina(cli, {"consulta": json.dumps(SIN_LUGAR)})
    api0 = cli.post("/api/preguntar", json={"consulta": SIN_LUGAR}).json()
    assert api0["tipo"] == "aclaracion" and r0.status_code == 200
    f0 = d0.buscar("form", **{"data-bloque": "aclaracion"})[0]
    assert d0.buscar(**{"data-bloque": "pregunta"})[0].texto().strip() == api0["aclaracion"]["pregunta"]
    assert [b.texto().strip() for b in f0.buscar("button", name="n")] == [o["etiqueta"] for o in api0["aclaracion"]["opciones"]]
    assert formulario(f0)["elegir"] == "" and json.loads(formulario(f0)["consulta"]) == SIN_LUGAR
    assert "texto" not in formulario(f0)
    (r1, d1), _, _ = _elegir(cli, r0.text, 1)
    f1 = d1.buscar("form", **{"data-bloque": "aclaracion"})[0]
    assert formulario(f1)["elegir"] == "1"                               # «1» acumulado en un campo oculto
    (r2, d2), _, _ = _elegir(cli, r1.text, 2)
    api2 = cli.post("/api/preguntar", json={"consulta": SIN_LUGAR, "elegir": [1, 2]}).json()
    assert api2["tipo"] != "aclaracion" and _bloques(d2) == _orden_esperado(api2)
    assert d2.buscar(**{"data-bloque": "respuesta_corta"})[0].texto().strip() == api2["capas"]["capa1"]["respuesta_corta"]


def test_aclaracion_dos_lugares_elegir_acumulado_con_texto_y_entendimos(cli, app, tmp_path):
    app.state.dir_cache = tmp_path
    ent, esperado = _leer(BASE / "evaluacion" / "m11")
    texto = ent["pregunta"]
    r0, d0 = _pagina(cli, {"texto": texto})                              # primero: ¿de qué problema?
    f0 = d0.buscar("form", **{"data-bloque": "aclaracion"})[0]
    assert formulario(f0)["texto"] == texto and formulario(f0)["elegir"] == "" and "consulta" not in formulario(f0)
    eco = d0.buscar(**{"data-eco": True})
    assert len(eco) == 1 and eco[0].texto().strip() == texto            # lo que ella escribió, marcado
    (r1, d1), _, _ = _elegir(cli, r0.text, 1)
    f1 = d1.buscar("form", **{"data-bloque": "aclaracion"})[0]
    assert formulario(f1)["elegir"] == "1" and formulario(f1)["texto"] == texto
    assert d1.buscar(**{"data-bloque": "pregunta"})[0].texto().strip() == "Hay varios lugares llamados «Lima». ¿Cuál quieres?"
    (r2, d2), _, _ = _elegir(cli, r1.text, 2)                            # segundo: ¿qué Lima?
    api = cli.post("/api/preguntar", json={"texto": texto, "elegir": [1, 2]}).json()
    assert api["tipo"] in ("respuesta", "no_se_puede") and api["entendimos"]
    assert _bloques(d2) == _orden_esperado(api)
    assert d2.buscar(**{"data-bloque": "entendimos"})[0].texto().strip() == api["entendimos"]   # conserva «Entendimos»
    assert d2.buscar(**{"data-bloque": "respuesta_corta"})[0].texto().strip() == api["capas"]["capa1"]["respuesta_corta"]
    assert not d2.buscar(**{"data-eco": True})


def test_aclaracion_sin_opciones_ofrece_la_caja_de_texto(cli, app, tmp_path):
    app.state.dir_cache = tmp_path
    ent, res = _leer(BASE / "evaluacion" / "l10")
    assert res["aclaracion"]["opciones"] == []
    r, d = _pagina(cli, _formulario_de(ent))
    assert d.buscar("textarea", name="texto") and not d.buscar("button", name="n")
    assert d.buscar(**{"data-bloque": "pregunta"})[0].texto().strip() == res["aclaracion"]["pregunta"]


# ---------------------------------------------------------------- mensajes y errores
def test_mensajes_fijos_de_la_web_sin_texto_de_terminal(cli, app, tmp_path):
    visto = set()
    for caso in ("fp07", "fp09"):
        app.state.dir_cache = tmp_path / caso
        ent, res = _leer(BASE / "evaluacion" / caso)
        assert res["tipo"] == "mensaje"
        r, d = _pagina(cli, _formulario_de(ent))
        m = d.buscar(**{"data-bloque": "mensaje"})[0].texto().strip()
        assert m == TX["mensajes"][res["motivo"]]
        assert "uv run" not in r.text and "--" not in m and "pap preguntar" not in r.text
        assert d.buscar("textarea", name="texto")                       # puede volver a escribir
        visto.add(res["motivo"])
    assert visto == {"no_es_pregunta", "otro_idioma"}


class _SinLLM:
    def interpretar_crudo(self, *a, **k):
        raise NoDisponible("caida")


def test_sin_llm_el_mensaje_lleva_el_enlace_al_formulario_guiado(app, tmp_path):
    a = _sin_limite(crear_app(RAIZ, llm=_SinLLM(), dir_cache=tmp_path, precalentar=False))
    c = TestClient(a)
    r, d = _pagina(c, {"texto": "¿Cuánta anemia hay en Puno?"})
    assert r.status_code == 503                                          # el mismo estado que /api/preguntar
    assert d.buscar(**{"data-bloque": "mensaje"})[0].texto().strip() == TX["mensajes"]["no_disponible"]
    assert [a_.attrs["href"] for a_ in d.buscar("a", href="/guiado")]
    assert "uv run" not in r.text


def test_cache_vencida_muestra_el_mensaje_con_la_caja_de_texto(cli, app, tmp_path):
    app.state.dir_cache = tmp_path / "vacia"                             # no hay pregunta guardada: «elegir» no reinterpreta
    r, d = _pagina(cli, {"texto": "¿Cuánta anemia hay en Lima?", "elegir": "1"})
    assert r.status_code == 422
    assert d.buscar(**{"data-bloque": "error"})[0].texto().strip() == TX["errores"]["eleccion_invalida"]
    assert d.buscar("textarea", name="texto")


def test_errores_de_forma_con_texto_de_la_web_y_estado_de_la_api(cli):
    casos = [({"consulta": "no es json"}, "solicitud_invalida", 422),
             ({"consulta": "[1]"}, "solicitud_invalida", 422),
             ({"texto": "x" * 5000}, "texto_muy_largo", 422),
             ({"texto": "hola", "consulta": "{}"}, "solicitud_invalida", 422),
             ({"texto": "hola", "elegir": "a"}, "solicitud_invalida", 422),
             ({"texto": "hola", "elegir": "1,2,3,4,5"}, "solicitud_invalida", 422),
             ({}, "solicitud_invalida", 422),
             ({"consulta": json.dumps({"intencion": "no_existe"})}, "consulta_invalida", 422)]
    for datos, clave, estado in casos:
        r, d = _pagina(cli, datos)
        assert r.status_code == estado, datos
        assert d.buscar(**{"data-bloque": "error"})[0].texto().strip() == TX["errores"][clave], datos
        assert "--elegir" not in r.text and "x" * 50 not in r.text      # nunca se devuelve lo que mandó la persona


def test_texto_vacio_vuelve_al_inicio_con_su_aviso(cli):
    r, d = _pagina(cli, {"texto": "   "})
    assert r.status_code == 422
    assert d.buscar(**{"data-bloque": "error"})[0].texto().strip() == TX["paginas"]["texto_vacio"]


def test_la_pagina_de_preparacion_usa_el_texto_de_la_web(tmp_path):
    a = _sin_limite(crear_app(RAIZ, llm=Cliente(RAIZ, modo="reproducir"), dir_cache=tmp_path, precalentar=True))
    assert a.state.listo.wait(120)
    a.state.listo.clear()
    r, d = _pagina(TestClient(a), {"texto": "hola"})
    assert r.status_code == 503 and d.buscar(**{"data-bloque": "mensaje"})[0].texto().strip() == TX["preparando"]


def test_get_de_preguntar_no_existe(cli):
    r = cli.get("/preguntar", params={"texto": "hola"})
    assert r.status_code == 405 and "hola" not in r.text


# ---------------------------------------------------------------- las páginas no cambian la API
def test_la_api_no_cambia_por_las_paginas(cli, app):
    ent, res = _leer(BASE / "q" / "q1")
    cli.post("/preguntar", data=_formulario_de(ent))
    r = cli.post("/api/preguntar", json={"consulta": ent["consulta"]})
    assert r.json() == res and r.headers["content-type"] == "application/json"


# ---------------------------------------------------------------- ningún número fuera del JSON
NUMERO = re.compile(r"\d[\d\u00a0\u202f .,]*")        # espacio, espacio duro y espacio fino
CLAVES_NO_TEXTO = {"ids", "id_cifra", "url", "ficha", "nivel", "tipo"}


def _textos_json(x, fuera=CLAVES_NO_TEXTO):
    """Las cadenas ya escritas de una parte del JSON (nunca los números crudos ni los identificadores)."""
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for k, v in x.items():
            if k not in fuera:
                yield from _textos_json(v, fuera)
    elif isinstance(x, list):
        for v in x:
            yield from _textos_json(v, fuera)


def _textos_yaml(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from _textos_yaml(v)
    elif isinstance(x, list):
        for v in x:
            yield from _textos_yaml(v)


def _permitidos(res: dict, rotulo: str) -> list[str]:
    t = list(_textos_yaml(TX)) + list(_textos_yaml(ROT)) + [rotulo, res.get("entendimos") or ""]
    t += list(_textos_json(res.get("capas") or {}))
    t += list(_textos_json({k: res[k] for k in ("alternativas", "temas_disponibles", "aclaracion") if k in res}, CLAVES_NO_TEXTO | {"territorio", "consulta"}))
    return [x for x in t if x]


def _numeros(texto: str) -> list[str]:
    return [n for n in (m.strip("\u00a0\u202f .,") for m in NUMERO.findall(texto)) if n]


def _verificar(cli, ent: dict, res: dict, rotulo: str, nombre: str, cuenta: dict) -> None:
    r, d = _pagina(cli, _formulario_de(ent))
    cuerpo = d.buscar("body")[0]
    permitidos = _permitidos(res, rotulo)
    sueltos = [n for n in _numeros(cuerpo.texto(sin_eco=True)) if not any(n in t for t in permitidos)]
    assert not sueltos, (nombre, sueltos)
    cuenta["paginas"] += 1
    cuenta["numeros"] += len(_numeros(cuerpo.texto(sin_eco=True)))
    eco = cuerpo.buscar(**{"data-eco": True})                            # lo que repite la pregunta, aparte
    if res["tipo"] == "aclaracion" and "pregunta" in ent:
        assert len(eco) == 1 and eco[0].texto().strip() == ent["pregunta"].strip(), nombre
        cuenta["ecos"] += 1
    else:
        assert not eco, nombre                                           # solo la aclaración repite lo que escribió la persona


def _rotulo(cli) -> str:
    return cli.get("/api/version").json()["rotulo"]


def test_ningun_numero_fuera_del_json_q1_q4(cli):
    cuenta = {"paginas": 0, "numeros": 0, "ecos": 0}
    for q in Q1_Q4:
        ent, res = _leer(BASE / "q" / q)
        _verificar(cli, ent, res, _rotulo(cli), q, cuenta)
    assert cuenta["paginas"] == 4 and cuenta["numeros"] > 40
    print("números Q1–Q4:", cuenta)


def test_ningun_numero_fuera_del_json_matriz_reducida(cli):
    cuenta = {"paginas": 0, "numeros": 0, "ecos": 0}
    casos = [c for c in _casos("q") if c.name not in Q1_Q4] + _casos("matriz")        # q1_abancay_elegir_1 y la matriz
    for c in casos:
        ent, res = _leer(c)
        _verificar(cli, ent, res, _rotulo(cli), c.name, cuenta)
    assert cuenta["paginas"] == len(casos) == 1 + len(_casos("matriz"))
    print("números matriz:", cuenta)


def test_ningun_numero_fuera_del_json_conjunto_con_grabaciones(cli, app, tmp_path):
    cuenta = {"paginas": 0, "numeros": 0, "ecos": 0}
    casos = _casos("evaluacion")
    for i, c in enumerate(casos):
        app.state.dir_cache = tmp_path / f"cache{i}"
        ent, res = _leer(c)
        _verificar(cli, ent, res, _rotulo(cli), c.name, cuenta)
    assert cuenta["paginas"] == len(casos) == 158 and cuenta["ecos"] > 10
    print("números evaluación:", cuenta)


def test_el_detector_de_numeros_atrapa_un_numero_inventado():
    permitidos = ["38,6 % en 2025", "Biblioteca 010ea9, construida el 2026-11-05"]
    assert [n for n in _numeros("Subió a 41,2 % en 2025.") if not any(n in t for t in permitidos)] == ["41,2"]
    assert [n for n in _numeros("38,6 % en 2025") if not any(n in t for t in permitidos)] == []
