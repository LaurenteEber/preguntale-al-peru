"""M1-04: cliente de la Batch API (`ClienteLote` en interprete/llm.py), con un transporte falso (sin red, sin clave real)."""
from __future__ import annotations

import json
from dataclasses import replace

import httpx
import pytest

from pathlib import Path

from pap.inferencia.cuestionarios_lote import ESQUEMA_VINCULAR, Peticion
from pap.interprete.llm import NoDisponible

RAIZ = Path(__file__).resolve().parents[2]
CLAVE_DE_PRUEBA = "valor-de-prueba-no-es-una-clave"


def _cliente(handler, monkeypatch, clave=CLAVE_DE_PRUEBA):
    from pap.interprete.llm import ClienteLote

    if clave is None:
        monkeypatch.delenv("PAP_ANTHROPIC_BATCH_KEY", raising=False)
    else:
        monkeypatch.setenv("PAP_ANTHROPIC_BATCH_KEY", clave)
    return ClienteLote(RAIZ, transporte=httpx.MockTransport(handler))


def test_crear_lote_manda_las_peticiones_con_la_clave_del_workspace_de_lotes(monkeypatch):
    visto = {}

    def handler(req: httpx.Request):
        visto["metodo"], visto["url"] = req.method, str(req.url)
        visto["cabeceras"] = {k.lower(): v for k, v in req.headers.items()}
        visto["cuerpo"] = json.loads(req.content)
        return httpx.Response(200, json={"id": "msgbatch_01", "processing_status": "in_progress"})

    c = _cliente(handler, monkeypatch)
    c.par_lote = replace(c.par_lote, salida_estructurada=True)
    bid = c.crear_lote([Peticion("vin-1", "SISTEMA", "USUARIO", 60, ESQUEMA_VINCULAR)])
    assert bid == "msgbatch_01" and visto["metodo"] == "POST" and visto["url"].endswith("/v1/messages/batches")
    assert visto["cabeceras"]["x-" + "api-key"] == CLAVE_DE_PRUEBA and "anthropic-version" in visto["cabeceras"]
    [r] = visto["cuerpo"]["requests"]
    assert r["custom_id"] == "vin-1" and r["params"]["model"] == "claude-sonnet-5-5" and r["params"]["max_tokens"] == 60
    assert r["params"]["system"] == "SISTEMA" and r["params"]["messages"] == [{"role": "user", "content": "USUARIO"}]
    assert r["params"]["output_config"]["format"]["schema"] == ESQUEMA_VINCULAR


def test_sin_la_clave_de_lotes_no_se_llama_a_nada(monkeypatch):
    llamadas = []
    c = _cliente(lambda req: llamadas.append(req) or httpx.Response(200, json={}), monkeypatch, clave=None)
    with pytest.raises(NoDisponible) as e:
        c.crear_lote([Peticion("vin-1", "S", "U", 60)])
    assert e.value.motivo == "sin_clave_lote" and llamadas == []


def test_nunca_usa_la_clave_del_servicio_web(monkeypatch):
    monkeypatch.setenv("PAP_ANTHROPIC_API_KEY", "clave-del-servicio-web")
    llamadas = []
    c = _cliente(lambda req: llamadas.append(req) or httpx.Response(200, json={}), monkeypatch, clave=None)
    with pytest.raises(NoDisponible):
        c.crear_lote([Peticion("vin-1", "S", "U", 60)])
    assert llamadas == []                                           # con solo la clave del web, el cliente de lotes no corre


def test_se_niega_si_la_variable_de_lotes_fuera_la_del_servicio_web(monkeypatch):
    c = _cliente(lambda req: httpx.Response(200, json={}), monkeypatch)
    c.par_lote = replace(c.par_lote, variable_clave=c.par["variable_clave"]["valor"])
    with pytest.raises(NoDisponible) as e:
        c.crear_lote([Peticion("vin-1", "S", "U", 60)])
    assert e.value.motivo == "clave_compartida"


def test_estado_resultados_y_borrado(monkeypatch):
    jsonl = "\n".join(json.dumps(x) for x in [
        {"custom_id": "vin-1", "result": {"type": "succeeded", "message": {
            "content": [{"type": "text", "text": "{\"id\": \"c03\"}"}], "usage": {"input_tokens": 500, "output_tokens": 12}}}},
        {"custom_id": "vin-2", "result": {"type": "errored", "error": {"type": "error", "error": {"type": "invalid_request_error", "message": "x"}}}},
        {"custom_id": "vin-3", "result": {"type": "expired"}}])
    registro = []

    def handler(req: httpx.Request):
        registro.append((req.method, req.url.path))
        if req.method == "DELETE":
            return httpx.Response(200, json={"id": "msgbatch_01", "type": "message_batch_deleted"})
        if req.url.path.endswith("/results"):
            return httpx.Response(200, text=jsonl)
        return httpx.Response(200, json={"id": "msgbatch_01", "processing_status": "ended",
                                         "results_url": "https://api.anthropic.com/v1/messages/batches/msgbatch_01/results"})

    c = _cliente(handler, monkeypatch)
    assert c.estado("msgbatch_01") == "terminado"
    rs = list(c.resultados("msgbatch_01"))
    assert [(r.custom_id, r.texto, bool(r.error)) for r in rs] == [("vin-1", "{\"id\": \"c03\"}", False), ("vin-2", None, True), ("vin-3", None, True)]
    assert (rs[0].tokens_entrada, rs[0].tokens_salida) == (500, 12)
    c.borrar("msgbatch_01")
    assert registro[-1] == ("DELETE", "/v1/messages/batches/msgbatch_01")


def test_un_lote_en_proceso_se_reporta_en_proceso(monkeypatch):
    c = _cliente(lambda req: httpx.Response(200, json={"id": "m", "processing_status": "in_progress"}), monkeypatch)
    assert c.estado("m") == "en_proceso"


def test_un_error_del_servicio_no_filtra_la_clave(monkeypatch):
    c = _cliente(lambda req: httpx.Response(500, text="falló"), monkeypatch)
    with pytest.raises(NoDisponible) as e:
        c.estado("m")
    assert CLAVE_DE_PRUEBA not in str(e.value) and CLAVE_DE_PRUEBA not in repr(e.value)
    c2 = _cliente(lambda req: httpx.Response(401, text="no"), monkeypatch)
    with pytest.raises(NoDisponible) as e2:
        c2.crear_lote([Peticion("a", "S", "U", 10)])
    assert e2.value.motivo == "clave_rechazada"


def test_por_defecto_no_se_pide_salida_estructurada(monkeypatch):
    visto = {}

    def handler(req: httpx.Request):
        visto["cuerpo"] = json.loads(req.content)
        return httpx.Response(200, json={"id": "m"})

    _cliente(handler, monkeypatch).crear_lote([Peticion("vin-1", "S", "U", 60, ESQUEMA_VINCULAR)])
    assert "format" not in visto["cuerpo"]["requests"][0]["params"]["output_config"]
