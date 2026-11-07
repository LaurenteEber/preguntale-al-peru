"""S3-07 — Límites de abuso y costo: por IP, tope diario de llamadas al LLM (día de Lima), tamaño del cuerpo y cabeceras.
Sin red ni clave: el LLM es falso o el cliente real con un transporte de prueba."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
import yaml
from fastapi.testclient import TestClient

from pap.interprete import llm as L
from pap.interprete.llm import RespuestaLLM
from pap.web.app import crear_app

from interprete.test_llm import CLAVE, INTERP, VAR, respuesta_api

from ._html import leer

RAIZ = Path(__file__).resolve().parents[2]
TX = yaml.safe_load((RAIZ / "curados/web/textos.yaml").read_text(encoding="utf-8"))
PAR = yaml.safe_load((RAIZ / "curados/web/parametros.yaml").read_text(encoding="utf-8"))
CONSULTA = json.loads((RAIZ / "backlog/slice-3/evidencia/base_api/q/q1/entrada.json").read_text(encoding="utf-8"))["consulta"]
LIMA = timezone(timedelta(hours=-5))


class Reloj:
    """Reloj falso: devuelve un instante con zona; `avanzar` lo mueve."""

    def __init__(self, ahora: datetime):
        self.ahora = ahora

    def __call__(self) -> datetime:
        return self.ahora

    def avanzar(self, **kw) -> None:
        self.ahora += timedelta(**kw)


class LlmFalso:
    """Devuelve siempre la misma interpretación válida (anemia en Puno); cuenta cuántas veces lo llamaron."""

    def __init__(self, extra_http: int = 0):
        self.llamadas, self.intentos_http, self.extra_http = 0, 0, extra_http

    def interpretar_crudo(self, prompt, limpia, version, error_previo=None) -> RespuestaLLM:
        self.llamadas += 1
        self.intentos_http += 1 + self.extra_http          # `extra_http`: reintentos del proveedor dentro de la misma llamada
        return RespuestaLLM(INTERP, "", "falso", version_prompt=version)


def pregunta(i: int) -> str:
    """Una pregunta distinta por `i` (otra huella de caché): ¿Cuánta anemia hay en Puno? con una premisa que cambia."""
    letras = "".join(chr(97 + int(d)) for d in str(i))
    return f"Si hay {letras} personas, ¿Cuánta anemia hay en Puno?"


def hacer_app(tmp_path, llm=None, ahora=None, **kw):
    reloj = Reloj(ahora or datetime(2026, 11, 6, 12, 0, tzinfo=LIMA))
    app = crear_app(RAIZ, llm=llm or LlmFalso(), dir_cache=tmp_path / "cache", precalentar=False, reloj=reloj,
                    registro_uso=None, **kw)
    return app, reloj


def texto_api(cli, i: int):
    return cli.post("/api/preguntar", json={"texto": pregunta(i)})


# ---------------------------------------------------------------- por IP
def test_limite_por_ip_mensaje_fijo_y_ventana(tmp_path):
    app, reloj = hacer_app(tmp_path)
    app.state.limites.por_minuto = 3
    cli = TestClient(app, client=("203.0.113.5", 1000))
    for _ in range(3):
        assert cli.post("/api/preguntar", json={"consulta": CONSULTA}).status_code == 200
    r = cli.post("/api/preguntar", json={"consulta": CONSULTA})
    assert r.status_code == 429
    assert r.json() == {"tipo": "mensaje", "motivo": "espera_un_momento", "texto": TX["mensajes"]["espera_un_momento"], "cifras": {}}
    assert "Espera un momento" in r.json()["texto"]
    otra = TestClient(app, client=("203.0.113.6", 1000))                 # otra IP no se ve afectada
    assert otra.post("/api/preguntar", json={"consulta": CONSULTA}).status_code == 200
    reloj.avanzar(seconds=PAR["limites"]["ventana_segundos"]["valor"] + 1)
    assert cli.post("/api/preguntar", json={"consulta": CONSULTA}).status_code == 200


def test_limite_por_ip_tambien_en_las_paginas_y_el_formulario_guiado(tmp_path):
    app, _ = hacer_app(tmp_path)
    app.state.limites.por_minuto = 2
    cli = TestClient(app, client=("203.0.113.7", 1000))
    assert cli.post("/preguntar", data={"consulta": json.dumps(CONSULTA)}).status_code == 200
    assert cli.post("/guiado", data={"tema": "anemia", "intencion": "nivel_actual"}).status_code == 200    # el paso 1 no es una pregunta
    assert cli.post("/guiado", data={"tema": "anemia", "intencion": "nivel_actual", "paso": "2", "lugar": "Puno"}).status_code == 200
    r = cli.post("/preguntar", data={"consulta": json.dumps(CONSULTA)})
    assert r.status_code == 429 and r.headers["content-type"].startswith("text/html")
    assert TX["mensajes"]["espera_un_momento"] in leer(r.text).buscar("body")[0].texto()
    r = cli.post("/guiado", data={"tema": "anemia", "intencion": "nivel_actual", "paso": "2", "lugar": "Puno"})
    assert r.status_code == 429


def test_los_parametros_de_limites_son_supuestos_de_s3_07():
    for k in ("preguntas_por_minuto_por_ip", "ventana_segundos", "llamadas_llm_por_dia", "zona_horaria", "cuerpo_max_bytes"):
        assert PAR["limites"][k]["supuesto"] == "S3-07", k
    assert PAR["limites"]["preguntas_por_minuto_por_ip"]["valor"] == 10
    assert PAR["limites"]["llamadas_llm_por_dia"]["valor"] == 300
    assert PAR["limites"]["zona_horaria"]["valor"] == "America/Lima"
    assert PAR["limites"]["cuerpo_max_bytes"]["valor"] == 8192


# ---------------------------------------------------------------- tope diario
def test_tope_diario_cuenta_llamadas_y_no_los_aciertos_de_cache(tmp_path):
    llm = LlmFalso()
    app, _ = hacer_app(tmp_path, llm)
    app.state.limites.llamadas_por_dia = 3
    cli = TestClient(app)
    for i in range(3):
        assert texto_api(cli, i).status_code == 200
    assert texto_api(cli, 0).status_code == 200                           # acierto de caché: responde y no cuenta
    assert llm.llamadas == 3 and app.state.limites.llamadas_hoy == 3
    r = texto_api(cli, 99)
    assert r.status_code == 503 and r.json()["motivo"] == "tope_diario"
    assert r.json()["texto"] == TX["mensajes"]["tope_diario"]
    assert llm.llamadas == 3                                              # al tope no se llama al LLM


def test_tope_diario_cuenta_reintentos_del_proveedor(tmp_path):
    llm = LlmFalso(extra_http=1)                                          # cada llamada gasta dos intentos HTTP
    app, _ = hacer_app(tmp_path, llm)
    app.state.limites.llamadas_por_dia = 4
    cli = TestClient(app)
    assert texto_api(cli, 1).status_code == 200 and app.state.limites.llamadas_hoy == 2
    assert texto_api(cli, 2).status_code == 200 and app.state.limites.llamadas_hoy == 4
    assert texto_api(cli, 3).json()["motivo"] == "tope_diario"


def test_tope_diario_con_el_cliente_real_cuenta_el_reintento_http(tmp_path, monkeypatch):
    monkeypatch.setenv(VAR, CLAVE)
    respuestas = iter([httpx.Response(529, json={"error": {"message": "sobrecargado"}}), httpx.Response(200, json=respuesta_api())])
    cliente = L.Cliente(RAIZ, modo="vivo", transporte=httpx.MockTransport(lambda _req: next(respuestas)))
    cliente.espera = lambda _s: None
    app, _ = hacer_app(tmp_path, cliente)
    r = texto_api(TestClient(app), 1)
    assert r.status_code == 200 and r.json()["tipo"] == "respuesta"
    assert app.state.limites.llamadas_hoy == 2                           # una petición + su reintento


def test_tope_diario_cuenta_el_reintento_por_interpretacion_invalida(tmp_path):
    class Malo(LlmFalso):
        def interpretar_crudo(self, prompt, limpia, version, error_previo=None):
            r = super().interpretar_crudo(prompt, limpia, version, error_previo)
            return r if error_previo else RespuestaLLM({"resultado": "no_valido"}, "", "falso", version_prompt=version)
    llm = Malo()
    app, _ = hacer_app(tmp_path, llm)
    assert texto_api(TestClient(app), 1).status_code == 200
    assert llm.llamadas == 2 and app.state.limites.llamadas_hoy == 2


def test_el_tope_diario_se_reinicia_con_el_dia_de_lima_no_con_el_de_utc(tmp_path):
    llm = LlmFalso()
    app, reloj = hacer_app(tmp_path, llm, ahora=datetime(2026, 11, 6, 23, 58, tzinfo=LIMA))
    app.state.limites.llamadas_por_dia = 1
    cli = TestClient(app)
    assert texto_api(cli, 1).status_code == 200
    assert texto_api(cli, 2).json()["motivo"] == "tope_diario"
    reloj.ahora = datetime(2026, 11, 7, 3, 0, tzinfo=LIMA)                # ya es 7/11 en Lima
    assert texto_api(cli, 2).status_code == 200 and llm.llamadas == 2


def test_la_medianoche_de_utc_no_reinicia_el_tope(tmp_path):
    app, reloj = hacer_app(tmp_path, ahora=datetime(2026, 11, 6, 18, 58, tzinfo=LIMA))   # 23:58 UTC
    app.state.limites.llamadas_por_dia = 1
    cli = TestClient(app)
    assert texto_api(cli, 1).status_code == 200
    reloj.avanzar(minutes=5)                                              # 19:03 en Lima, 00:03 del día siguiente en UTC
    assert texto_api(cli, 2).json()["motivo"] == "tope_diario"
    assert reloj().astimezone(timezone.utc).date() != datetime(2026, 11, 6).date()


def test_al_tope_la_caja_se_desactiva_con_mensaje_y_enlace_y_el_formulario_guiado_sigue(tmp_path):
    app, _ = hacer_app(tmp_path)
    app.state.limites.llamadas_por_dia = 1
    cli = TestClient(app)
    d = leer(cli.get("/").text)
    assert "disabled" not in d.buscar("textarea", name="texto")[0].attrs and not d.buscar(**{"data-bloque": "tope_diario"})
    assert texto_api(cli, 1).status_code == 200
    for ruta in ("/", "/guiado"):
        d = leer(cli.get(ruta).text)
        if ruta == "/guiado":
            assert d.buscar("form") and not d.buscar("textarea")           # el formulario guiado no usa la caja
            continue
        caja = d.buscar("textarea", name="texto")[0]
        assert "disabled" in caja.attrs
        assert all("disabled" in b.attrs for b in d.buscar("button", name="texto"))        # también los ejemplos
        assert all("disabled" in c.attrs for f in d.buscar("form", **{"class": "caja"}) for c in f.buscar("button") + f.buscar("textarea"))
        aviso = d.buscar(**{"data-bloque": "tope_diario"})
        assert aviso and TX["mensajes"]["tope_diario"] in aviso[0].texto()
        assert [a for a in d.buscar("a", href="/guiado") if TX["paginas"]["guiado_enlace"] in a.texto()]
    r = cli.post("/preguntar", data={"texto": pregunta(50)})              # texto nuevo: sin caché → tope
    assert r.status_code == 503
    cuerpo = leer(r.text).buscar("body")[0].texto()
    assert TX["mensajes"]["tope_diario"] in cuerpo and cuerpo.count(TX["mensajes"]["tope_diario"]) == 1
    assert leer(r.text).buscar("a", href="/guiado")
    g = cli.post("/guiado", data={"tema": "anemia", "intencion": "nivel_actual", "paso": "2", "lugar": "Puno"})
    assert g.status_code == 200 and g.headers["content-type"].startswith("text/html")
    assert leer(g.text).buscar(**{"data-bloque": "respuesta_corta"})
    assert cli.post("/api/preguntar", json={"consulta": CONSULTA}).status_code == 200


def test_el_motivo_del_tope_es_el_de_los_mensajes_con_enlace_guiado():
    assert "tope_diario" in PAR["paginas"]["mensajes_con_enlace_guiado"]["valor"]
    assert PAR["http"]["estado_por_motivo"]["valor"]["tope_diario"] == 503
    assert PAR["http"]["estado_por_motivo"]["valor"]["espera_un_momento"] == 429
    assert TX["mensajes"]["tope_diario"] and TX["mensajes"]["espera_un_momento"]


# ---------------------------------------------------------------- tamaño del cuerpo
@pytest.mark.parametrize("ruta,args", [("/api/preguntar", {"json": {"texto": "a" * 9000}}),
                                       ("/preguntar", {"data": {"texto": "a" * 9000}}),
                                       ("/guiado", {"data": {"tema": "anemia", "intencion": "nivel_actual", "paso": "2", "lugar": "a" * 9000}})])
def test_cuerpo_grande_se_rechaza_con_413_y_sin_eco(tmp_path, ruta, args):
    llm = LlmFalso()
    app, _ = hacer_app(tmp_path, llm)
    r = TestClient(app).post(ruta, **args)
    assert r.status_code == 413 and "aaaa" not in r.text
    assert TX["errores"]["cuerpo_muy_grande"] in r.text
    assert llm.llamadas == 0
    assert r.headers["referrer-policy"] == "no-referrer" and r.headers["x-content-type-options"] == "nosniff"


def test_cuerpo_grande_sin_content_length_tambien_se_rechaza(tmp_path):
    app, _ = hacer_app(tmp_path)
    def cuerpo():
        yield b'{"texto": "'
        for _ in range(12):
            yield b"a" * 1000
        yield b'"}'
    r = TestClient(app).post("/api/preguntar", content=cuerpo(), headers={"content-type": "application/json"})
    assert r.status_code == 413


def test_cuerpo_dentro_del_limite_pasa(tmp_path):
    app, _ = hacer_app(tmp_path)
    r = TestClient(app).post("/api/preguntar", json={"texto": pregunta(1) + " " + "a" * 1500})
    assert r.status_code == 200


# ---------------------------------------------------------------- cabeceras (S3-04)
def test_cabeceras_en_paginas_avisos_y_respuestas_de_limite(tmp_path):
    app, _ = hacer_app(tmp_path)
    app.state.limites.por_minuto = 1
    cli = TestClient(app)
    respuestas = [cli.get("/"), cli.post("/preguntar", data={"consulta": json.dumps(CONSULTA)}),
                  cli.post("/preguntar", data={"consulta": json.dumps(CONSULTA)})]
    assert respuestas[2].status_code == 429
    for r in respuestas:
        assert r.headers["referrer-policy"] == "no-referrer" and r.headers["x-content-type-options"] == "nosniff"
        assert r.headers["content-security-policy"] == PAR["paginas"]["csp"]["valor"]
        assert not r.cookies and "set-cookie" not in r.headers
