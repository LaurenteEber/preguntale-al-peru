"""S3-07 — Privacidad (P-03): ningún registro, archivo nuevo ni traza guarda el texto de la pregunta. La única excepción es la caché de
interpretaciones de 24 h (`salidas/interprete/cache/`, P-03), que la búsqueda deja fuera y la evidencia nombra. Sin red ni clave."""
from __future__ import annotations

import logging
import os
import socket
import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn
import yaml
from fastapi.testclient import TestClient

from pap.web.app import crear_app

from .test_limites import LlmFalso, hacer_app, pregunta

RAIZ = Path(__file__).resolve().parents[2]
TX = yaml.safe_load((RAIZ / "curados/web/textos.yaml").read_text(encoding="utf-8"))
MARCA = "ZORZALMARCADOR"                      # en una premisa: ni lugar, ni tema, ni año, así que no es un ancla del intérprete
MARCA_LUGAR = "QUETZALPRIVADO"                # en el lugar del formulario guiado y en una excepción forzada
NUEVAS = 50
SALTAR = {".git", ".venv", "__pycache__", ".pytest_cache", "biblioteca", "node_modules", ".codegraph", ".atl"}


class Recolector(logging.Handler):
    """Todo lo que se registra, con su traza formateada, desde la raíz, `pap.web` y los registros de uvicorn."""
    NOMBRES = ("",)                       # la raíz ve también lo que propagan pap.web y uvicorn

    def __init__(self):
        super().__init__(logging.DEBUG)
        self.setFormatter(logging.Formatter("%(name)s %(message)s"))
        self.lineas: list[str] = []
        self._previos: dict = {}

    def emit(self, record):
        if record.name.startswith(("httpx", "httpcore", "asyncio")):        # el cliente de la prueba, no el servidor
            return
        self.lineas.append(self.format(record))

    def __enter__(self):
        for n in self.NOMBRES:
            lg = logging.getLogger(n)
            self._previos[n] = lg.level
            lg.addHandler(self)
            lg.setLevel(logging.DEBUG)
        return self

    def __exit__(self, *a):
        for n in self.NOMBRES:
            logging.getLogger(n).removeHandler(self)
            logging.getLogger(n).setLevel(self._previos[n])

    def texto(self) -> str:
        return "\n".join(self.lineas)


def instantanea(*raices: Path) -> dict:
    visto = {}
    for raiz in raices:
        for dp, dns, fns in os.walk(raiz):
            dns[:] = [d for d in dns if d not in SALTAR]
            for f in fns:
                p = Path(dp) / f
                try:
                    st = p.stat()
                except OSError:
                    continue
                visto[p] = (st.st_size, st.st_mtime_ns)
    return visto


def archivos_nuevos(antes: dict, despues: dict) -> list[Path]:
    return [p for p, v in despues.items() if antes.get(p) != v]


def buscar(marcas, textos: dict[str, str]) -> list[tuple[str, str]]:
    return [(donde, m) for donde, t in textos.items() for m in marcas if m in t]


# ---------------------------------------------------------------- el marcador
def test_el_marcador_no_aparece_en_registros_trazas_ni_archivos_nuevos(tmp_path, monkeypatch, capfd):
    trabajo = tmp_path / "trabajo"
    trabajo.mkdir()
    monkeypatch.chdir(trabajo)
    uso = tmp_path / "salidas_prueba" / "uso.jsonl"                       # el registro de uso (P-03) de esta prueba
    llm = LlmFalso()
    app = crear_app(RAIZ, llm=llm, dir_cache=tmp_path / "cache_24h", precalentar=False, registro_uso=uso)
    app.state.limites.por_minuto = 10_000                                 # esta prueba no mide el límite por IP
    cli = TestClient(app)
    antes = instantanea(RAIZ, trabajo)
    with Recolector() as rec:
        for i in range(NUEVAS):
            premisa = pregunta(i).replace("Si hay", f"Si {MARCA} y hay")
            assert cli.post("/api/preguntar", json={"texto": premisa}).status_code == 200            # por texto
            assert cli.post("/preguntar", data={"texto": premisa + " "}).status_code == 200          # por el formulario de la caja
            guiado = cli.post("/guiado", data={"tema": "anemia", "intencion": "nivel_actual", "paso": "2", "lugar": f"{MARCA_LUGAR}{i}"})
            assert guiado.status_code in (200, 422)                                               # por el formulario guiado
    assert llm.llamadas == NUEVAS                                      # cada premisa llamó una vez al LLM falso (el formulario dio acierto de caché)
    salida = capfd.readouterr()
    despues = instantanea(RAIZ, trabajo)
    nuevos = archivos_nuevos(antes, despues)
    nuevos_texto = {str(p): p.read_text(encoding="utf-8", errors="ignore") for p in nuevos}
    assert not [p for p in nuevos if p.name == "respuesta.json"], nuevos                            # la web no escribe respuesta.json
    assert not [p for p in nuevos if str(p).startswith(str(trabajo))], nuevos                       # nada en el directorio de trabajo
    nuevos_texto["uso.jsonl"] = uso.read_text(encoding="utf-8") if uso.exists() else ""
    assert uso.exists() and len(uso.read_text(encoding="utf-8").splitlines()) >= NUEVAS             # el registro de uso sí se escribió
    nuevos_texto["registros"] = rec.texto()
    nuevos_texto["stdout"], nuevos_texto["stderr"] = salida.out, salida.err
    assert rec.lineas, "la prueba debe ver al menos el registro de acceso"
    assert buscar((MARCA, MARCA_LUGAR), nuevos_texto) == []
    # la caché de 24 h es el único lugar con rastro de la pregunta (P-03): queda fuera de la búsqueda
    assert list((tmp_path / "cache_24h").glob("*.json"))


def test_el_acceso_guarda_solo_metodo_ruta_codigo_y_tiempo(tmp_path):
    app, _ = hacer_app(tmp_path)
    cli = TestClient(app)
    with Recolector() as rec:
        cli.post("/api/preguntar", json={"texto": pregunta(1)})
        cli.get("/salud")
        cli.get(f"/no-existe?q={MARCA}")
    acceso = [x for x in rec.lineas if "pap.web.acceso" in x]
    assert len(acceso) == 3, rec.lineas
    assert acceso[0].endswith("POST /api/preguntar 200") or " POST /api/preguntar 200 " in acceso[0]
    assert any(" GET /salud 200 " in x for x in acceso) and any(" GET /no-existe 404 " in x for x in acceso)
    assert MARCA not in rec.texto() and "anemia" not in rec.texto().lower()


# ---------------------------------------------------------------- excepciones forzadas
def test_excepcion_en_la_consulta_registra_el_tipo_y_no_el_texto(tmp_path, monkeypatch):
    import pap.web.app as W
    app, _ = hacer_app(tmp_path)
    cli = TestClient(app)

    def explota(*a, **k):
        raise ValueError(f"no entendí el lugar {MARCA_LUGAR}")

    monkeypatch.setattr(W, "interpretar", explota)
    monkeypatch.setattr(W, "preguntar_minima", explota)
    with Recolector() as rec:
        r1 = cli.post("/api/preguntar", json={"texto": f"anemia en {MARCA_LUGAR}"})
        r2 = cli.post("/api/preguntar", json={"consulta": {"territorio": {"texto": MARCA_LUGAR}}})
    assert r1.status_code == r2.status_code == 500 and MARCA_LUGAR not in r1.text + r2.text
    assert "ValueError" in rec.texto() and MARCA_LUGAR not in rec.texto()
    assert "Traceback" not in rec.texto()


def test_excepcion_no_capturada_la_atrapa_el_manejador_global(tmp_path, monkeypatch):
    import jinja2
    app, _ = hacer_app(tmp_path)
    cli = TestClient(app, raise_server_exceptions=True)

    def explota(*a, **k):
        raise RuntimeError(f"plantilla rota con {MARCA_LUGAR}")

    monkeypatch.setattr(jinja2.Environment, "get_template", explota)
    with Recolector() as rec:
        r = cli.post("/preguntar", data={"texto": f"anemia en {MARCA_LUGAR}"})
        g = cli.get("/")
        a = cli.post("/api/preguntar", json={"texto": "x"})
    assert r.status_code == g.status_code == 500
    assert TX["errores"]["error_interno"] in r.text and MARCA_LUGAR not in r.text + g.text
    assert r.headers["referrer-policy"] == "no-referrer" and r.headers["x-content-type-options"] == "nosniff"
    assert "RuntimeError" in rec.texto() and MARCA_LUGAR not in rec.texto() and "Traceback" not in rec.texto()
    assert a.status_code in (200, 422, 500)


def _servidor(app):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        puerto = s.getsockname()[1]
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=puerto, log_config=None, log_level="debug"))
    hilo = threading.Thread(target=srv.run, daemon=True)
    hilo.start()
    for _ in range(100):
        if srv.started:
            break
        time.sleep(0.05)
    assert srv.started
    return srv, hilo, f"http://127.0.0.1:{puerto}"


def test_con_uvicorn_de_verdad_no_queda_la_entrada_en_sus_registros(tmp_path, monkeypatch):
    import jinja2
    app, _ = hacer_app(tmp_path)

    def explota(*a, **k):
        raise RuntimeError(f"plantilla rota con {MARCA_LUGAR}")

    srv, hilo, url = _servidor(app)
    try:
        with Recolector() as rec:
            ok = httpx.post(f"{url}/api/preguntar", json={"texto": pregunta(1).replace("Si hay", f"Si {MARCA} y hay")})
            httpx.get(f"{url}/salud?x={MARCA}")
            monkeypatch.setattr(jinja2.Environment, "get_template", explota)
            malo = httpx.post(f"{url}/preguntar", data={"texto": f"anemia en {MARCA_LUGAR}"})
            monkeypatch.undo()
    finally:
        srv.should_exit = True
        hilo.join(10)
    assert ok.status_code == 200 and malo.status_code == 500
    assert rec.lineas
    assert buscar((MARCA, MARCA_LUGAR), {"registros": rec.texto(), "respuesta": malo.text}) == []
    assert "RuntimeError" in rec.texto() and "Traceback" not in rec.texto()
    assert not [x for x in rec.lineas if x.startswith("uvicorn.access") or "HTTP/1.1" in x]      # el acceso de uvicorn no se usa


def test_sin_cookies_ni_terceros(tmp_path):
    app, _ = hacer_app(tmp_path)
    r = TestClient(app).get("/")
    assert "set-cookie" not in r.headers and "http://" not in r.text.replace("http://www.w3.org", "") and "https://" not in r.text
