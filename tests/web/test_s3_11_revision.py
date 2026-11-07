"""S3-11: arreglos de la revisión por partes (evidencia/revision_por_partes.md) que el dueño pidió antes del cierre (L17).
1. `/salud` no dice «ok» si el precalentamiento falló.
2. Al volver atrás (caché del navegador), los botones no quedan desactivados ni en «Buscando…».
(3, la prueba de axe que podía pasar sin revisar nada, está en test_accesibilidad.py.)"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

import pap.web.app as app_mod
from pap.web.app import crear_app

from .test_accesibilidad import navegador, servidor, _pagina          # noqa: F401 — fixtures de Chromium y del servidor

RAIZ = Path(__file__).resolve().parents[2]
TX = yaml.safe_load((RAIZ / "curados/web/textos.yaml").read_text(encoding="utf-8"))


def test_salud_no_dice_ok_si_el_precalentamiento_fallo(tmp_path, monkeypatch):
    def falla(*a, **k):
        raise RuntimeError("falla de prueba")
    monkeypatch.setattr(app_mod, "preguntar_minima", falla)
    a = crear_app(RAIZ, dir_cache=tmp_path, precalentar=True)
    assert a.state.listo.wait(120)
    assert a.state.error_precalentamiento == "RuntimeError"
    r = TestClient(a).get("/salud")
    assert r.status_code == 503
    assert r.json() == {"estado": "error_precalentamiento"}


def test_salud_ok_si_el_precalentamiento_salio_bien(tmp_path):
    """PRESERVE: sin fallo, /salud sigue en 200 «ok»."""
    a = crear_app(RAIZ, dir_cache=tmp_path, precalentar=True)
    assert a.state.listo.wait(120)
    r = TestClient(a).get("/salud")
    assert r.status_code == 200 and r.json() == {"estado": "ok"}


@pytest.mark.navegador
def test_al_volver_atras_los_botones_quedan_activos_y_con_su_etiqueta(navegador, servidor):          # noqa: F811
    _, base = servidor
    ctx, pag = _pagina(navegador, base, "aclaracion")
    try:
        pag.evaluate("document.addEventListener('submit', e => e.preventDefault(), true)")   # se queda en la página
        boton = pag.locator("button[name=n]").first
        etiqueta = boton.inner_text().strip()
        boton.click()
        pag.wait_for_function("document.querySelector('button[name=n]').disabled")
        assert boton.inner_text().strip() == f"{TX['paginas']['buscando']} {etiqueta}"
        # lo que hace el navegador al volver atrás con la página en caché (bfcache)
        pag.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}))")
        assert pag.evaluate("[...document.querySelectorAll('button[type=submit]')].every(b => !b.disabled)")
        assert boton.inner_text().strip() == etiqueta
    finally:
        ctx.close()
