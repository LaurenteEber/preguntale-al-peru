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
CLAVE = "sk-prueba-" + "0123456789-no-es-real"          # por partes: tests/test_sin_secretos.py busca el valor entero
VAR = L.parametros(RAIZ)["variable_clave"]["valor"]
INTERP = {"resultado": "consulta", "consulta": {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Puno"}},
          "anclas": {"intencion": "Cuánta", "tema": "anemia", "territorio": "Puno"}}


def respuesta_api(dato=INTERP, entrada=1000, salida=100):
    return {"id": "msg_prueba", "type": "message", "role": "assistant", "model": "claude-sonnet-5-5",
            "content": [{"type": "text", "text": json.dumps(dato, ensure_ascii=False)}],
            "usage": {"input_tokens": entrada, "output_tokens": salida}}


def transporte(fn):
    return httpx.MockTransport(fn)


@pytest.fixture(autouse=True)
def sin_esperas(monkeypatch):
    esperas = []
    monkeypatch.setattr(L.time, "sleep", esperas.append)
    return esperas


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


@pytest.mark.parametrize("texto", ["987 654 321", "987-654-321", "987.654.321", "987654321", "DNI 45.871.236", "D.N.I. 45 871 236",
                                   "mi documento es 45-871-236", "DNI: 45.871.236"])
def test_limpieza_celular_en_grupos_y_dni_con_separadores_tras_dni(texto):
    """P-03 (dueño, 5/11/2026): celular 3-3-3 con espacio, guion o punto, siempre; DNI con separadores solo tras «DNI»,
    «D.N.I.» o «documento», y la palabra se conserva."""
    t = limpiar(f"Hola, {texto}. ¿Anemia en Puno en 2024?", RAIZ)
    import re
    previo = re.match(r"[^\d]*", texto).group()
    assert t.texto == f"Hola, {previo}[dato personal]. ¿Anemia en Puno en 2024?" and t.reemplazos == 1


@pytest.mark.parametrize("texto", ["S/ 45.871.236", "2 263,9 millones", "S/ 1.987.654.321", "población de 45.871.236 personas",
                                   "entre 2018 y 2024"])
def test_limpieza_no_borra_montos_ni_poblaciones_ni_anios(texto):
    t = limpiar(f"¿El gasto fue {texto}?", RAIZ)
    assert t.texto == f"¿El gasto fue {texto}?" and t.reemplazos == 0


def test_limpieza_recorta_y_quita_caracteres_de_control():
    t = limpiar("anemia\x00 en\x07 Puno " + "x" * 2000, RAIZ)
    assert len(t.texto) == 1000 and "\x00" not in t.texto and "\x07" not in t.texto
    assert t.avisos == ["Tu pregunta era muy larga: usamos solo sus primeros 1000 caracteres."]


# ------------------------------------------------------------------ cliente

def test_grabar_y_reproducir_byte_a_byte(raiz_tmp, monkeypatch):
    monkeypatch.setenv(VAR, CLAVE)
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
    assert (r.tokens_entrada, r.tokens_salida, r.costo_usd) == (1000, 100, 0.003)          # 1000 × 2 + 100 × 10 por millón
    cuerpo = json.loads(pedidos[0].content)
    assert cuerpo["model"] == "claude-sonnet-5-5" and "temperature" not in cuerpo           # P-07; 2026-10-21 rechaza temperature
    assert cuerpo["output_config"]["effort"] == "low"
    assert "format" not in cuerpo["output_config"]                                             # S2-04-d: la API no acepta el esquema
    assert "<pregunta>\n¿Cuánta anemia hay en Puno?\n</pregunta>" == cuerpo["messages"][0]["content"]
    assert "¿Cuánta anemia hay en Puno?" not in json.dumps(cuerpo["system"], ensure_ascii=False)                               # la pregunta, fuera de las instrucciones



def test_falta_la_grabacion_dice_como_grabarla(raiz_tmp):
    prompt, version = armar(raiz_tmp)
    with pytest.raises(L.FaltaGrabacion, match=r"evaluar\.py --grabar --solo"):
        L.Cliente(raiz_tmp, modo="reproducir").interpretar_crudo(prompt, "pregunta sin grabar", version)


def test_la_clave_no_aparece_en_ningun_archivo(raiz_tmp, monkeypatch):
    monkeypatch.setenv(VAR, CLAVE)
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
    monkeypatch.setenv(VAR, CLAVE)
    (raiz_tmp / "tests/interprete").mkdir(parents=True, exist_ok=True)
    (raiz_tmp / "tests/interprete/preguntas_prueba.yaml").write_text(
        "entradas:\n" + "".join(f"  - {{id: p{i}, pregunta: 'anemia en lugar {chr(65 + i)}'}}\n" for i in range(5)), encoding="utf-8")
    api = transporte(lambda req: httpx.Response(200, json=respuesta_api(entrada=100_000, salida=10_000)))   # US$ 0,30 cada una
    r = evaluar.grabar(raiz_tmp, None, L.Cliente(raiz_tmp, modo="grabar", transporte=api, tope_usd=0.5))
    assert len(r["hechas"]) == 2 and r["cortado"] == "tope_por_corrida"


@pytest.mark.parametrize("caso,motivo", [("tiempo", "tiempo_agotado"), ("limite", "limite_de_ritmo"), ("caida", "caida"),
                                         ("sin_clave", "sin_clave")])
def test_fallas_dan_no_disponible(raiz_tmp, monkeypatch, caso, motivo):
    if caso == "sin_clave":
        monkeypatch.delenv(VAR, raising=False)
    else:
        monkeypatch.setenv(VAR, CLAVE)

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


def test_el_reintento_lleva_el_error_y_tiene_su_propia_grabacion(raiz_tmp, monkeypatch):
    """S2-05: el reintento manda el error en el mensaje del usuario (no en las instrucciones) y se graba aparte."""
    monkeypatch.setenv(VAR, CLAVE)
    pedidos = []

    def api(req):
        pedidos.append(json.loads(req.content))
        return httpx.Response(200, json=respuesta_api())
    prompt, version = armar(raiz_tmp)
    c = L.Cliente(raiz_tmp, modo="grabar", transporte=transporte(api))
    a = c.interpretar_crudo(prompt, "anemia en Puno", version)
    b = c.interpretar_crudo(prompt, "anemia en Puno", version, error_previo="falta_ancla: falta un ancla")
    assert a.grabacion != b.grabacion
    assert pedidos[0]["messages"][0]["content"] == "<pregunta>\nanemia en Puno\n</pregunta>"
    assert pedidos[1]["messages"][0]["content"].startswith("<pregunta>\nanemia en Puno\n</pregunta>\n\n")
    assert "falta_ancla: falta un ancla" in pedidos[1]["messages"][0]["content"] and "falta un ancla" not in json.dumps(pedidos[1]["system"], ensure_ascii=False)
    r = L.Cliente(raiz_tmp, modo="reproducir").interpretar_crudo(prompt, "anemia en Puno", version, error_previo="falta_ancla: falta un ancla")
    assert r.grabacion == b.grabacion
    assert L.huella_grabacion("x", "m", "v") == L.huella_grabacion("x", "m", "v", None)        # sin error, la huella de S2-04


# ------------------------------------------------------------------ proveedor: reintentos, detención y secretos (dueño, 5/11/2026)

def _contar(estado, cuerpo=None, cabeceras=None):
    llamadas = []

    def api(req):
        llamadas.append(req)
        return httpx.Response(estado, json=cuerpo or {"type": "error", "error": {"type": "x", "message": "x"}}, headers=cabeceras)
    return llamadas, transporte(api)


@pytest.mark.parametrize("estado", [401, 403])
def test_clave_rechazada_no_se_reintenta_y_detiene_el_cliente(raiz_tmp, monkeypatch, sin_esperas, estado):
    monkeypatch.setenv(VAR, CLAVE)
    llamadas, api = _contar(estado)
    prompt, version = armar(raiz_tmp)
    c = L.Cliente(raiz_tmp, modo="vivo", transporte=api)
    for _ in range(2):
        with pytest.raises(L.NoDisponible) as e:
            c.interpretar_crudo(prompt, "anemia en Puno", version)
        assert e.value.motivo == "clave_rechazada"
    assert len(llamadas) == 1 and sin_esperas == [] and c.detenido == "clave_rechazada"


@pytest.mark.parametrize("estado,motivo", [(429, "limite_de_ritmo"), (500, "caida"), (529, "caida")])
def test_429_y_5xx_un_solo_reintento_con_espera(raiz_tmp, monkeypatch, sin_esperas, estado, motivo):
    monkeypatch.setenv(VAR, CLAVE)
    llamadas, api = _contar(estado, cabeceras={"retry-after": "120"})
    prompt, version = armar(raiz_tmp)
    with pytest.raises(L.NoDisponible) as e:
        L.Cliente(raiz_tmp, modo="vivo", transporte=api).interpretar_crudo(prompt, "anemia en Puno", version)
    assert e.value.motivo == motivo and len(llamadas) == 2 and sin_esperas == [30.0]      # retry-after con tope de 30 s


def test_429_y_luego_bien_responde(raiz_tmp, monkeypatch, sin_esperas):
    monkeypatch.setenv(VAR, CLAVE)
    estados = iter([httpx.Response(429, json={"type": "error"}), httpx.Response(200, json=respuesta_api())])
    prompt, version = armar(raiz_tmp)
    r = L.Cliente(raiz_tmp, modo="vivo", transporte=transporte(lambda req: next(estados))).interpretar_crudo(prompt, "anemia en Puno", version)
    assert r.json == INTERP and sin_esperas == [5.0]


@pytest.mark.parametrize("estado,mensaje", [(402, "billing"), (400, "You have reached your specified API usage limits."),
                                            (429, "Your credit balance is too low to access the API.")])
def test_limite_de_gasto_agotado_detiene_sin_reintentar(raiz_tmp, monkeypatch, sin_esperas, estado, mensaje):
    monkeypatch.setenv(VAR, CLAVE)
    llamadas, api = _contar(estado, {"type": "error", "error": {"type": "billing_error", "message": mensaje}})
    prompt, version = armar(raiz_tmp)
    c = L.Cliente(raiz_tmp, modo="grabar", transporte=api)
    for _ in range(2):
        with pytest.raises(L.NoDisponible) as e:
            c.interpretar_crudo(prompt, "anemia en Puno", version)
        assert e.value.motivo == "limite_agotado"
    assert len(llamadas) == 1 and sin_esperas == []


def test_el_error_no_lleva_la_peticion_ni_la_clave(raiz_tmp, monkeypatch):
    monkeypatch.setenv(VAR, CLAVE)

    def api(req):
        raise httpx.ConnectError("sin red", request=req)
    prompt, version = armar(raiz_tmp)
    with pytest.raises(L.NoDisponible) as e:
        L.Cliente(raiz_tmp, modo="vivo", transporte=transporte(api)).interpretar_crudo(prompt, "anemia en Puno", version)
    assert e.value.__cause__ is None and e.value.__context__ is None and CLAVE not in repr(e.value)


def test_la_grabacion_no_guarda_encabezados_y_si_los_metadatos(raiz_tmp, monkeypatch):
    monkeypatch.setenv(VAR, CLAVE)
    api = transporte(lambda req: httpx.Response(200, json=respuesta_api(), headers={"request-id": "req_x", "anthropic-ratelimit": "1"}))
    prompt, version = armar(raiz_tmp)
    g = L.Cliente(raiz_tmp, modo="grabar", transporte=api).interpretar_crudo(prompt, "anemia en Puno", version)
    dato = json.loads((raiz_tmp / "tests/interprete/grabaciones" / g.grabacion).read_text(encoding="utf-8"))
    assert set(dato) == {"pregunta_limpia", "modelo", "version_prompt", "tokens_entrada", "tokens_salida", "costo_usd", "latencia_s",
                         "respuesta"}
    texto = json.dumps(dato).lower()
    assert "req_x" not in texto and "ratelimit" not in texto and L.CABECERA_CLAVE not in texto and CLAVE not in texto


def test_httpx_y_httpcore_no_registran_peticiones():
    import logging
    assert all(logging.getLogger(n).getEffectiveLevel() >= logging.WARNING for n in ("httpx", "httpcore"))


def test_esquema_para_api_sin_lo_que_la_api_rechaza():
    """Si `interprete.salida_estructurada` vuelve a true: lo que la API rechazó en vivo el 5/11/2026 no está."""
    from pap.motor.interpretacion import RUTA_CONSULTA, RUTA_ESQUEMA
    esq = json.loads((RAIZ / RUTA_ESQUEMA).read_text(encoding="utf-8"))
    cm = json.loads((RAIZ / RUTA_CONSULTA).read_text(encoding="utf-8"))
    s = L.esquema_para_api(esq, {"consulta_minima.schema.json": cm})
    texto = json.dumps(s)
    assert '"oneOf"' not in texto and '"$ref"' not in texto and '"minLength"' not in texto and "{}" not in texto
    assert list(s) == ["anyOf"]

    def nodos(n):
        if isinstance(n, dict):
            yield n
            for v in n.values():
                yield from nodos(v)
        elif isinstance(n, list):
            for v in n:
                yield from nodos(v)
    assert not [n for n in nodos(s) if "anyOf" in n and set(n) - {"anyOf"}]


@pytest.mark.parametrize("texto,esperado", [('{"resultado": "no_es_pregunta"}', {"resultado": "no_es_pregunta"}),
                                            ('```json\n{"resultado": "otro_idioma", "x": null}\n```', {"resultado": "otro_idioma"}),
                                            ("no sé", None), ("[1, 2]", None)])
def test_leer_json_sin_salida_estructurada(texto, esperado):
    assert L.leer_json(texto) == esperado


def test_costo_cuenta_el_cache_del_proveedor():
    cuerpo = respuesta_api(entrada=100, salida=100)
    cuerpo["usage"].update(cache_creation_input_tokens=1000, cache_read_input_tokens=10_000)
    r = L._de_cuerpo(cuerpo, "m", "v", 0.0, L.parametros(RAIZ))
    # 100 × 2 + 1000 × 2 × 1,25 + 10 000 × 2 × 0,05 + 100 × 10, por millón
    assert r.tokens_entrada == 11_100 and r.costo_usd == round((200 + 2500 + 1000 + 1000) / 1e6, 6)
