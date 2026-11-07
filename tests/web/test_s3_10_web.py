"""S3-10 (T10b) — arreglos de la web tras la revisión del dueño (H-03, H-08, H-09, H-14), por la interfaz HTTP y, para el JavaScript,
con Chromium. Sin red ni clave. Los textos salen de curados/web/textos.yaml; la web no calcula nada."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from pap.web.app import crear_app

from ._html import leer
from .test_accesibilidad import navegador, servidor, _pagina          # noqa: F401 — fixtures de Chromium y del servidor

RAIZ = Path(__file__).resolve().parents[2]
TX = yaml.safe_load((RAIZ / "curados/web/textos.yaml").read_text(encoding="utf-8"))
PAR = yaml.safe_load((RAIZ / "curados/web/parametros.yaml").read_text(encoding="utf-8"))
Q1 = json.loads((RAIZ / "curados/motor/consultas_minimas/q1.json").read_text(encoding="utf-8"))
GUIADO = {"tema": "anemia", "intencion": "nivel_actual", "paso": "2"}


def _app(**kw):
    a = crear_app(RAIZ, llm=None, dir_cache=None, precalentar=False, registro_uso=None,
                  reloj=lambda: datetime(2026, 11, 7, 12, 0, tzinfo=timezone(timedelta(hours=-5))))
    a.state.limites.por_minuto = kw.get("por_minuto", 10 ** 9)
    return a


@pytest.fixture
def cli():
    return TestClient(_app())


# ---------------------------------------------------------------- H-03
def test_h03_que_puedo_hacer_no_se_muestra_sin_revision_pero_el_json_no_cambia(cli):
    assert PAR["paginas"]["mostrar_que_hacer_sin_revisar"]["valor"] is False
    api = cli.post("/api/preguntar", json={"consulta": Q1}).json()
    qh = api["capas"]["capa1"]["que_hacer"]
    assert qh and qh["revisado_dueno"] is False                      # el JSON (y la CLI) siguen igual
    r = cli.post("/preguntar", data={"consulta": json.dumps(Q1)})
    d = leer(r.text)
    assert r.status_code == 200 and d.buscar(**{"data-bloque": "cifra_clave"})
    assert not d.buscar(**{"data-bloque": "que_hacer"})
    assert qh["texto"] not in r.text


# ---------------------------------------------------------------- H-08
def test_h08_lugar_no_encontrado_vuelve_al_paso_2_con_el_lugar_vacio_y_repite_lo_escrito(cli):
    r = cli.post("/guiado", data={**GUIADO, "lugar": "Cuzko", "anio": "2023"})
    d = leer(r.text)
    f = d.buscar("form", **{"data-bloque": "guiado_paso2"})
    assert f, r.text[:600]
    assert f[0].buscar("input", name="lugar")[0].attrs.get("value", "") == ""
    ocultos = {n.attrs["name"]: n.attrs.get("value") for n in f[0].buscar("input", type="hidden")}
    assert ocultos == {"tema": "anemia", "intencion": "nivel_actual", "paso": "2"}
    assert f[0].buscar("input", name="anio")[0].attrs.get("value") == "2023"
    err = d.buscar(**{"data-bloque": "guiado_error"})[0].texto()
    assert err.strip() == TX["guiado"]["errores"]["lugar_no_encontrado"].format(lugar="Cuzko") and "«Cuzko»" in err
    assert "Revisa cómo está escrito o dinos" not in r.text           # ya no sale el texto del motor, que no repite lo escrito


def test_h08_con_sugerencias_se_siguen_mostrando_como_opciones(cli):
    r = cli.post("/guiado", data={**GUIADO, "lugar": "Huancabelica"})
    d = leer(r.text)
    assert "No encontramos «Huancabelica». ¿Quisiste decir" in d.buscar(**{"data-bloque": "pregunta"})[0].texto()
    assert len(d.buscar("button", name="n")) >= 1 and not d.buscar("form", **{"data-bloque": "guiado_paso2"})


def test_h08_por_escrito_la_aclaracion_sin_opciones_no_cambia(cli):
    """La caja de texto (sin guiado) conserva el comportamiento: el texto del motor."""
    ab = {**Q1, "territorio": {"texto": "Cuzko"}, "intencion": "nivel_actual"}
    r = cli.post("/preguntar", data={"consulta": json.dumps(ab)})
    assert "No encontramos ese lugar" in r.text


# ---------------------------------------------------------------- H-09
def test_h09_limite_conserva_lo_escrito_y_dice_cuanto_esperar(caplog):
    cli = TestClient(_app(por_minuto=1))
    assert cli.post("/preguntar", data={"consulta": json.dumps(Q1)}).status_code == 200
    escrito = "¿Cuánta anemia hay en Moquegua? zzmarca"
    with caplog.at_level(logging.DEBUG):
        r = cli.post("/preguntar", data={"texto": escrito})
    assert r.status_code == 429
    d = leer(r.text)
    assert d.buscar("textarea", name="texto")[0].texto() == escrito
    assert "Espera unos segundos y vuelve a intentar" in d.buscar(**{"data-bloque": "mensaje"})[0].texto()
    assert "zzmarca" not in caplog.text                                # P-03: el texto no va a los registros


def test_h09_limite_en_el_guiado_conserva_los_campos():
    cli = TestClient(_app(por_minuto=1))
    assert cli.post("/guiado", data={**GUIADO, "lugar": "Puno"}).status_code == 200
    r = cli.post("/guiado", data={**GUIADO, "lugar": "Moquegua", "anio": "2022"})
    assert r.status_code == 429
    f = leer(r.text).buscar("form", **{"data-bloque": "guiado_paso2"})[0]
    assert f.buscar("input", name="lugar")[0].attrs["value"] == "Moquegua" and f.buscar("input", name="anio")[0].attrs["value"] == "2022"
    assert "Espera unos segundos y vuelve a intentar" in r.text


def test_h09_la_api_sigue_igual():
    cli = TestClient(_app(por_minuto=1), client=("203.0.113.9", 1))
    cli.post("/api/preguntar", json={"consulta": Q1})
    r = cli.post("/api/preguntar", json={"consulta": Q1})
    assert r.status_code == 429 and r.json()["motivo"] == "espera_un_momento" and r.json()["texto"] == TX["mensajes"]["espera_un_momento"]


# ---------------------------------------------------------------- H-14
ABANCAY = {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Abancay"}, "periodo": {"tipo": "ultimo"},
           "pregunta_original": "prueba", "idioma": "es"}


def test_h14_el_boton_de_cada_opcion_recuerda_su_etiqueta_en_data_buscando(cli):
    r = cli.post("/preguntar", data={"consulta": json.dumps(ABANCAY)})
    botones = leer(r.text).buscar("button", name="n")
    assert len(botones) >= 2
    for b in botones:
        assert b.attrs["data-buscando"] == f"{TX['paginas']['buscando']} {b.texto().strip()}"


@pytest.mark.navegador
def test_h14_al_tocar_una_opcion_se_ve_cual_se_eligio(navegador, servidor):          # noqa: F811
    _, base = servidor
    ctx, pag = _pagina(navegador, base, "aclaracion")
    try:
        # la página siguiente reemplaza a esta: lo que se ve entre el toque y la respuesta se anota en sessionStorage
        pag.evaluate("""document.addEventListener('submit', () => setTimeout(() => {
            sessionStorage.setItem('vista', document.querySelector('button[name=n]').textContent); }, 50))""")
        boton = pag.locator("button[name=n]").first
        etiqueta = boton.inner_text().strip()
        with pag.expect_navigation():
            boton.click()
        assert pag.evaluate("sessionStorage.getItem('vista')").strip() == f"{TX['paginas']['buscando']} {etiqueta}"
    finally:
        ctx.close()
