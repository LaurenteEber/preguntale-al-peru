"""S2-04 — Limpieza, cliente del LLM, grabaciones y tope, sin red: los transportes de httpx son de prueba
(httpx.MockTransport) y la clave es inventada."""
import json

import httpx
import pytest

from pap.config import Rutas
from pap.interprete import llm as L
from pap.interprete.limpiar import limpiar
from pap.interprete.prompt import armar

from conftest import RAIZ_REAL

RAIZ = Rutas(RAIZ_REAL).raiz
CLAVE = "sk-prueba-0123456789-no-es-real"
INTERP = {"resultado": "consulta", "consulta": {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Puno"}},
          "anclas": {"intencion": "Cuánta", "tema": "anemia", "territorio": "Puno"}}


def respuesta_api(dato=INTERP, entrada=1000, salida=100):
    return {"id": "msg_prueba", "type": "message", "role": "assistant", "model": "claude-opus-5-5",
            "content": [{"type": "text", "text": json.dumps(dato, ensure_ascii=False)}],
            "usage": {"input_tokens": entrada, "output_tokens": salida}}


def transporte(fn):
    return httpx.MockTransport(fn)


@pytest.fixture
def raiz_tmp(tmp_path):
    """Copia mínima de la raíz para que las grabaciones y el registro de uso de la prueba no toquen el repositorio."""
    import shutil
    for d in ("curados/motor", "curados/interprete"):
        shutil.copytree(RAIZ / d, tmp_path / d)
    return tmp_path


# ------------------------------------------------------------------ limpieza (P-03)

def test_limpieza_quita_dni_ruc_celular_y_correo_pero_no_los_anios():
    t = limpiar("Mi DNI es 45678912, RUC 20123456789, cel 987654321, correo ana.p@mail.com: ¿anemia en Puno en 2024?", RAIZ)
    assert "45678912" not in t.texto and "20123456789" not in t.texto and "987654321" not in t.texto
    assert "ana.p@mail.com" not in t.texto and t.texto.count("[dato personal]") == 4 and t.reemplazos == 4
    assert "2024" in t.texto


def test_limpieza_recorta_y_quita_caracteres_de_control():
    t = limpiar("anemia\x00 en\x07 Puno " + "x" * 2000, RAIZ)
    assert len(t.texto) == 1000 and "\x00" not in t.texto and "\x07" not in t.texto
    assert t.avisos == ["Tu pregunta era muy larga: usamos solo sus primeros 1000 caracteres."]


# ------------------------------------------------------------------ cliente

def test_grabar_y_reproducir_byte_a_byte(raiz_tmp, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", CLAVE)
    pedidos = []

    def api(req):
        pedidos.append(req)
        return httpx.Response(200, json=respuesta_api())
    prompt, version = armar(raiz_tmp)
    g = L.Cliente(raiz_tmp, modo="grabar", transporte=transporte(api)).interpretar_crudo(prompt, "¿Cuánta anemia hay en Puno?", version)
    ruta = raiz_tmp / "tests/interprete/grabaciones" / g.grabacion
    antes = ruta.read_bytes()
    r = L.Cliente(raiz_tmp, modo="reproducir").interpretar_crudo(prompt, "¿Cuánta anemia hay en Puno?", version)
    assert ruta.read_bytes() == antes and r.json == g.json == INTERP and r.texto == g.texto
    assert (r.tokens_entrada, r.tokens_salida, r.costo_usd) == (1000, 100, 0.006)          # 1000 × 4 + 100 × 20 por millón
    cuerpo = json.loads(pedidos[0].content)
    assert cuerpo["model"] == "claude-opus-5-5" and cuerpo["temperature"] == 0
    assert cuerpo["output_config"]["format"]["type"] == "json_schema"
    assert "<pregunta>\n¿Cuánta anemia hay en Puno?\n</pregunta>" == cuerpo["messages"][0]["content"]
    assert "¿Cuánta anemia hay en Puno?" not in cuerpo["system"]                               # la pregunta, fuera de las instrucciones
    esq = json.dumps(cuerpo["output_config"]["format"]["schema"])
    assert '"oneOf"' not in esq and '"$ref"' not in esq and '"minLength"' not in esq


def test_falta_la_grabacion_dice_como_grabarla(raiz_tmp):
    prompt, version = armar(raiz_tmp)
    with pytest.raises(L.FaltaGrabacion, match=r"evaluar\.py --grabar --solo"):
        L.Cliente(raiz_tmp, modo="reproducir").interpretar_crudo(prompt, "pregunta sin grabar", version)


def test_la_clave_no_aparece_en_ningun_archivo(raiz_tmp, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", CLAVE)
    prompt, version = armar(raiz_tmp)
    c = L.Cliente(raiz_tmp, modo="grabar", transporte=transporte(lambda req: httpx.Response(200, json=respuesta_api())))
    r = c.interpretar_crudo(prompt, "¿Cuánta anemia hay en Puno?", version)
    L.registrar_uso(raiz_tmp, "¿Cuánta anemia hay en Puno?", INTERP["consulta"], "consulta", r)
    for p in raiz_tmp.rglob("*"):
        if p.is_file():
            assert CLAVE not in p.read_text(encoding="utf-8", errors="ignore"), p
    uso = json.loads((raiz_tmp / "salidas/interprete/uso.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert set(uso) == {"fecha", "pregunta_sha256", "consulta", "resultado", "modelo", "tokens_entrada", "tokens_salida", "costo_usd"}
    assert "Puno" not in json.dumps(uso, ensure_ascii=False)                                   # sin textos de lugar (P-03)


def test_el_tope_corta_la_corrida(raiz_tmp, monkeypatch):
    import sys
    sys.path.insert(0, str(RAIZ / "tests" / "interprete"))
    import evaluar
    monkeypatch.setenv("ANTHROPIC_API_KEY", CLAVE)
    (raiz_tmp / "tests/interprete").mkdir(parents=True, exist_ok=True)
    (raiz_tmp / "tests/interprete/preguntas_prueba.yaml").write_text(
        "entradas:\n" + "".join(f"  - {{id: p{i}, pregunta: 'anemia en lugar {chr(65 + i)}'}}\n" for i in range(5)), encoding="utf-8")
    api = transporte(lambda req: httpx.Response(200, json=respuesta_api(entrada=100_000, salida=10_000)))   # US$ 0,60 cada una
    r = evaluar.grabar(raiz_tmp, None, L.Cliente(raiz_tmp, modo="grabar", transporte=api, tope_usd=1.0))
    assert len(r["hechas"]) == 2 and r["cortado"] == "tope_por_corrida"


@pytest.mark.parametrize("caso,motivo", [("tiempo", "tiempo_agotado"), ("limite", "limite_agotado"), ("caida", "caida"),
                                         ("sin_clave", "sin_clave")])
def test_fallas_dan_no_disponible(raiz_tmp, monkeypatch, caso, motivo):
    if caso == "sin_clave":
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    else:
        monkeypatch.setenv("ANTHROPIC_API_KEY", CLAVE)

    def api(req):
        if caso == "tiempo":
            raise httpx.ReadTimeout("tiempo", request=req)
        if caso == "limite":
            return httpx.Response(429, json={"type": "error", "error": {"type": "rate_limit_error"}})
        return httpx.Response(500, json={"type": "error"})
    prompt, version = armar(raiz_tmp)
    with pytest.raises(L.NoDisponible) as e:
        L.Cliente(raiz_tmp, modo="vivo", transporte=transporte(api)).interpretar_crudo(prompt, "anemia en Puno", version)
    assert e.value.motivo == motivo and CLAVE not in str(e.value)
