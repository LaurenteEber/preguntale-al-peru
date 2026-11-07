"""S3-06 — Accesibilidad y celular: axe-core (versión fija, tests/web/vendor/) en Chromium con Playwright, más las comprobaciones
automáticas de la lista manual (teclado, foco, zoom 200 %, encabezados, <details>, enlaces, confianza sin color, peso).
Sin red ni clave: el intérprete se reemplaza por uno caído (los mensajes no dependen del LLM). Con PAP_CAPTURAS=1 guarda las capturas
a 360 px en backlog/slice-3/evidencia/s3-06/. Las pruebas con navegador llevan la marca `navegador`."""
from __future__ import annotations

import hashlib
import json
import os
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn
import yaml

from pap.interprete.llm import NoDisponible
from pap.web.app import crear_app

RAIZ = Path(__file__).resolve().parents[2]
AXE = Path(__file__).parent / "vendor" / "axe.min.js"
AXE_SHA256 = "20c09fe157a8a34a30e241aaa1fcdade657734f08ab379ecfbeb7d45cc46e878"
CAPTURAS = RAIZ / "backlog" / "slice-3" / "evidencia" / "s3-06"
TX = yaml.safe_load((RAIZ / "curados/web/textos.yaml").read_text(encoding="utf-8"))
ANCHOS = (360, 1280)
ESQUEMAS = ("light", "dark")
Q1 = json.loads((RAIZ / "curados/motor/consultas_minimas/q1.json").read_text(encoding="utf-8"))
Q3 = json.loads((RAIZ / "curados/motor/consultas_minimas/q3.json").read_text(encoding="utf-8"))
ABANCAY = {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Abancay"}, "periodo": {"tipo": "ultimo"},
           "pregunta_original": "prueba de accesibilidad", "idioma": "es"}                    # X-22: «Huancavelica» a secas ya no aclara
PUNO_CRUCE = {"intencion": "cruce", "tema": "anemia", "territorio": {"ubigeo": "21"}, "periodo": {"tipo": "ultimo"},
              "pregunta_original": "prueba de accesibilidad", "idioma": "es"}                # una respuesta «no se puede»
SIN_LLM_TEXTO = "¿Cuánta anemia hay en Puno?"


class _SinLLM:
    def interpretar_crudo(self, *a, **k):
        raise NoDisponible("caida")


def _cons(c: dict) -> dict:
    return {"consulta": json.dumps(c, ensure_ascii=False)}


# nombre → (método, ruta, datos). Las páginas de respuesta salen de un POST, igual que en un navegador sin JavaScript.
PAGINAS = {
    "inicio": ("GET", "/", None),
    "guiado_paso1": ("GET", "/guiado", None),
    "guiado_paso2": ("POST", "/guiado", {"tema": "anemia", "intencion": "nivel_actual"}),
    "respuesta_q1": ("POST", "/preguntar", _cons(Q1)),
    "respuesta_q3": ("POST", "/preguntar", _cons(Q3)),
    "aclaracion": ("POST", "/preguntar", _cons(ABANCAY)),
    "no_se_puede": ("POST", "/preguntar", _cons(PUNO_CRUCE)),
    "mensaje": ("POST", "/preguntar", {"texto": SIN_LLM_TEXTO}),
    "error": ("POST", "/preguntar", {**_cons(ABANCAY), "elegir": "9"}),
}


# la marca de cada página: así se sabe que el navegador llegó a la página pedida y no a otra (p. ej. un aviso de error)
MARCA = {"inicio": "ejemplos", "guiado_paso1": "guiado_paso1", "guiado_paso2": "guiado_paso2", "respuesta_q1": "cifra_clave",
         "respuesta_q3": "cifra_clave", "aclaracion": "aclaracion", "no_se_puede": "respuesta_corta", "mensaje": "mensaje", "error": "error"}


@pytest.fixture(scope="module")
def servidor(tmp_path_factory):
    assert (RAIZ / "biblioteca/indicadores/fact_indicador.parquet").exists(), "falta el cubo"          # falla, no se salta
    app = crear_app(RAIZ, llm=_SinLLM(), dir_cache=tmp_path_factory.mktemp("cache"), precalentar=False)
    app.state.limites.por_minuto = 10 ** 9                  # el límite por IP (S3-07) se prueba en test_limites.py
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        puerto = s.getsockname()[1]
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=puerto, log_level="warning", access_log=False))
    hilo = threading.Thread(target=srv.run, daemon=True)
    hilo.start()
    for _ in range(100):
        if srv.started:
            break
        time.sleep(0.1)
    assert srv.started, "el servidor no arrancó"
    yield app, f"http://127.0.0.1:{puerto}"
    srv.should_exit = True
    hilo.join(timeout=10)


@pytest.fixture(scope="module")
def navegador():
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as pw:
        try:
            nav = pw.chromium.launch()
        except Exception as e:  # noqa: BLE001 — sin Chromium instalado: se informa, no es un falso verde
            pytest.fail(f"no se pudo abrir Chromium ({type(e).__name__}); corre `uv run playwright install chromium` o deja fuera -m navegador")
        yield nav
        nav.close()


def _pagina(nav, base, nombre, ancho=360, esquema="light", alto=800, escala=1.0):
    ctx = nav.new_context(viewport={"width": ancho, "height": alto}, color_scheme=esquema, device_scale_factor=escala,
                          bypass_csp=True)         # solo para inyectar axe y armar el formulario; la CSP de la app se prueba en test_paginas.py
    pag = ctx.new_page()
    metodo, ruta, datos = PAGINAS[nombre]
    if metodo == "GET":
        pag.goto(base + ruta)
    else:                                                    # se arma el formulario y se envía: es lo que hace un navegador
        pag.goto(base + "/")
        with pag.expect_navigation():
            pag.evaluate("""([ruta, datos]) => {
              const f = document.createElement('form'); f.method = 'post'; f.action = ruta;
              for (const [k, v] of Object.entries(datos)) { const i = document.createElement('input'); i.type = 'hidden'; i.name = k; i.value = v; f.appendChild(i); }
              document.body.appendChild(f); f.submit(); }""", [ruta, datos])
    pag.wait_for_load_state("load")
    return ctx, pag


def _axe(pag) -> list[dict]:
    pag.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")          # el contenido plegado también se revisa
    pag.add_script_tag(content=AXE.read_text(encoding="utf-8"))
    res = pag.evaluate("() => axe.run(document)")
    assert res["passes"], "axe no revisó ninguna regla: la prueba no probaría nada"      # S3-11: sin falso verde
    return [{"id": v["id"], "impacto": v["impact"], "nodos": [n["target"] for n in v["nodes"]][:5]} for v in res["violations"]]


# ---------------------------------------------------------------- herramienta
def test_axe_vendorizado_coincide_con_su_huella():
    assert hashlib.sha256(AXE.read_bytes()).hexdigest() == AXE_SHA256
    nota = (AXE.parent / "AXE_VERSION.txt").read_text(encoding="utf-8")
    assert AXE_SHA256 in nota and "4.14.0" in nota


# ---------------------------------------------------------------- axe: páginas × anchos × modos
@pytest.mark.navegador
@pytest.mark.parametrize("nombre", sorted(PAGINAS))
def test_axe_cero_graves_o_criticas(navegador, servidor, nombre):
    _, base = servidor
    graves = {}
    for ancho in ANCHOS:
        for esquema in ESQUEMAS:
            ctx, pag = _pagina(navegador, base, nombre, ancho, esquema)
            try:
                assert pag.locator(f"[data-bloque={MARCA[nombre]}]").count() >= 1, (nombre, pag.url)
                fondo = pag.evaluate("getComputedStyle(document.body).backgroundColor")
                assert fondo == ("rgb(18, 18, 18)" if esquema == "dark" else "rgb(255, 255, 255)"), fondo      # el modo oscuro sí se aplicó
                malas = [v for v in _axe(pag) if v["impacto"] in ("serious", "critical")]
            finally:
                ctx.close()
            if malas:
                graves[f"{ancho}px/{esquema}"] = malas
    assert not graves, json.dumps(graves, ensure_ascii=False, indent=1)


@pytest.mark.navegador
def test_axe_inicio_con_tope_diario(navegador, servidor):
    app, base = servidor
    app.state.limites.llamadas_hoy = app.state.limites.llamadas_por_dia
    try:
        for esquema in ESQUEMAS:
            ctx, pag = _pagina(navegador, base, "inicio", 360, esquema)
            try:
                assert pag.locator("[data-bloque=tope_diario]").count() == 1
                assert not [v for v in _axe(pag) if v["impacto"] in ("serious", "critical")]
            finally:
                ctx.close()
    finally:
        app.state.limites.llamadas_hoy = 0


# ---------------------------------------------------------------- lista manual, automatizada
@pytest.mark.navegador
@pytest.mark.parametrize("nombre", sorted(PAGINAS))
def test_lengua_titulo_y_encabezados_en_orden(navegador, servidor, nombre):
    _, base = servidor
    ctx, pag = _pagina(navegador, base, nombre)
    try:
        assert pag.evaluate("document.documentElement.lang") == "es"
        assert pag.title().strip()
        niveles = pag.evaluate("[...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => +h.tagName[1])")
        assert niveles and niveles[0] == 1 and niveles.count(1) == 1, niveles
        assert all(b - a <= 1 for a, b in zip(niveles, niveles[1:])), niveles                   # no se salta de nivel hacia abajo
        assert pag.locator("main").count() == 1
    finally:
        ctx.close()


@pytest.mark.navegador
@pytest.mark.parametrize("nombre", sorted(PAGINAS))
def test_los_enlaces_dicen_a_donde_llevan(navegador, servidor, nombre):
    _, base = servidor
    ctx, pag = _pagina(navegador, base, nombre)
    try:
        textos = pag.evaluate("[...document.querySelectorAll('a')].map(a => a.textContent.trim().toLowerCase())")
        assert textos and all(len(t) >= 6 for t in textos), textos
        assert not {"aquí", "click", "clic", "más", "ver"} & set(textos), textos
    finally:
        ctx.close()


@pytest.mark.navegador
def test_details_tienen_summary_y_se_abren_con_el_teclado(navegador, servidor):
    _, base = servidor
    ctx, pag = _pagina(navegador, base, "respuesta_q1")
    try:
        n = pag.locator("details").count()
        assert n >= 2
        assert pag.evaluate("[...document.querySelectorAll('details')].every(d => d.firstElementChild.tagName === 'SUMMARY')")
        resumen = pag.locator("details[data-bloque=para_citar] > summary")
        resumen.focus()
        assert pag.evaluate("document.querySelector('details[data-bloque=para_citar]').open") is False
        pag.keyboard.press("Enter")
        assert pag.evaluate("document.querySelector('details[data-bloque=para_citar]').open") is True
        pag.keyboard.press("Enter")
        assert pag.evaluate("document.querySelector('details[data-bloque=para_citar]').open") is False
        snap = pag.locator("details[data-bloque=para_citar]").aria_snapshot()
        assert "group" in snap or "button" in snap, snap          # se anuncia como grupo/botón desplegable
    finally:
        ctx.close()


@pytest.mark.navegador
@pytest.mark.parametrize("q", ["respuesta_q1", "respuesta_q3"])
def test_la_confianza_se_entiende_sin_color(navegador, servidor, q):
    """R-05: es una frase dentro de la respuesta, con el mismo color, peso de letra y ningún ícono que los demás textos de la cifra."""
    _, base = servidor
    ctx, pag = _pagina(navegador, base, q)
    try:
        c = pag.locator("[data-bloque=confianza]")
        assert c.count() == 1 and len(c.inner_text().split()) >= 5
        assert c.evaluate("e => getComputedStyle(e).color") == pag.locator("[data-bloque=respuesta_corta], [data-bloque=cifra_clave] p").first.evaluate("e => getComputedStyle(e).color")
        assert c.locator("img, svg, [class]").count() == 0
        assert c.evaluate("e => e.className") == "confianza"
    finally:
        ctx.close()


@pytest.mark.navegador
@pytest.mark.parametrize("nombre", ["inicio", "guiado_paso2", "respuesta_q1", "aclaracion", "mensaje"])
def test_todo_se_alcanza_con_el_teclado_y_el_foco_se_ve(navegador, servidor, nombre):
    _, base = servidor
    ctx, pag = _pagina(navegador, base, nombre)
    try:
        esperados = pag.evaluate("""[...document.querySelectorAll('a[href],button,textarea,input:not([type=hidden]),summary,select')]
            .filter(e => !e.disabled && e.offsetParent !== null).length""")
        vistos = []
        for _ in range(esperados + 2):
            pag.keyboard.press("Tab")
            info = pag.evaluate("""() => { const e = document.activeElement; const s = getComputedStyle(e);
                return {tag: e.tagName, clave: e.tagName + (e.id ? '#' + e.id : '') + (e.name ? '[' + e.name + (e.type == 'radio' ? '=' + e.value : '') + ']' : '') + (e.textContent.trim().slice(0, 20)),
                        contorno: s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) >= 2}; }""")
            if info["tag"] == "BODY" or info["clave"] in [v["clave"] for v in vistos]:
                break
            vistos.append(info)
        assert len(vistos) >= esperados - 6, (len(vistos), esperados)                 # un grupo de opciones (radio) se recorre como uno solo
        assert all(v["contorno"] for v in vistos), [v["clave"] for v in vistos if not v["contorno"]]
    finally:
        ctx.close()


@pytest.mark.navegador
@pytest.mark.parametrize("nombre", sorted(PAGINAS))
def test_zoom_200_por_ciento_sin_perder_contenido(navegador, servidor, nombre):
    """Un celular de 360 px al 200 % de zoom ve 180 px CSS; y 1280 px al 200 % son 640 px. Sin barra horizontal en ninguno."""
    _, base = servidor
    for ancho in (180, 640):
        ctx, pag = _pagina(navegador, base, nombre, ancho=ancho, escala=2.0)
        try:
            sobra = pag.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            assert sobra <= 0, (ancho, sobra)
            fuera = pag.evaluate("""(w) => [...document.querySelectorAll('main *')].filter(e => e.getBoundingClientRect().right > w + 1
                && getComputedStyle(e).display !== 'none').map(e => e.tagName).slice(0, 5)""", ancho)
            assert not fuera, (ancho, fuera)
        finally:
            ctx.close()


@pytest.mark.navegador
def test_tamano_de_letra_al_200_por_ciento_sigue_legible(navegador, servidor):
    """El texto crece con la preferencia del navegador (rem, no px): con la letra base al doble, la respuesta no se corta a 360 px."""
    _, base = servidor
    ctx, pag = _pagina(navegador, base, "respuesta_q1", 360)
    try:
        pag.add_style_tag(content="html { font-size: 200% !important; }")
        assert pag.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth") <= 0
    finally:
        ctx.close()


@pytest.mark.navegador
def test_objetivos_tactiles_de_44_px(navegador, servidor):
    _, base = servidor
    for nombre in ("inicio", "guiado_paso2", "aclaracion"):
        ctx, pag = _pagina(navegador, base, nombre, 360)
        try:
            chicos = pag.evaluate("""[...document.querySelectorAll('button, textarea, input[type=text], summary')]
                .filter(e => e.offsetParent !== null && e.getBoundingClientRect().height < 43.5).map(e => e.tagName + ' ' + e.getBoundingClientRect().height)""")
            assert not chicos, (nombre, chicos)
        finally:
            ctx.close()


# ---------------------------------------------------------------- peso
def test_q1_pesa_menos_de_100_kb_y_no_hay_imagenes(servidor):
    import urllib.parse
    import urllib.request
    _, base = servidor
    req = urllib.request.Request(base + "/preguntar", data=urllib.parse.urlencode(_cons(Q1)).encode(), method="POST")
    with urllib.request.urlopen(req) as r:
        cuerpo = r.read()
    assert 0 < len(cuerpo) <= 100 * 1024, len(cuerpo)
    assert b"<img" not in cuerpo and b"<svg" not in cuerpo and b"url(" not in cuerpo


# ---------------------------------------------------------------- capturas (evidencia)
@pytest.mark.navegador
@pytest.mark.skipif(os.environ.get("PAP_CAPTURAS") != "1", reason="solo al generar la evidencia (PAP_CAPTURAS=1)")
def test_capturas_a_360_px(navegador, servidor):
    _, base = servidor
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    for nombre in PAGINAS:
        for esquema in ESQUEMAS:
            ctx, pag = _pagina(navegador, base, nombre, 360, esquema)
            try:
                pag.screenshot(path=str(CAPTURAS / f"{nombre}_{esquema}_360.png"), full_page=True)
            finally:
                ctx.close()
    ctx, pag = _pagina(navegador, base, "inicio", 360)
    try:
        for _ in range(3):
            pag.keyboard.press("Tab")
        pag.screenshot(path=str(CAPTURAS / "foco_inicio_360.png"))
    finally:
        ctx.close()
    ctx, pag = _pagina(navegador, base, "respuesta_q1", 180, escala=2.0)
    try:
        pag.screenshot(path=str(CAPTURAS / "zoom200_respuesta_q1_360.png"), full_page=True)
    finally:
        ctx.close()
