"""S3-03 — Servicio FastAPI sobre el mismo motor. Sin red ni clave: el LLM son las grabaciones (modo «reproducir»)."""
from __future__ import annotations

import ast
import json
import re
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pap.interprete.llm import Cliente
from pap.web.app import crear_app

RAIZ = Path(__file__).resolve().parents[2]
BASE = RAIZ / "backlog" / "slice-3" / "evidencia" / "base_api"


def _casos(grupo: str) -> list[Path]:
    return sorted((BASE / grupo).iterdir())


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    assert (RAIZ / "biblioteca/indicadores/fact_indicador.parquet").exists(), "falta el cubo"   # falla, no se salta
    a = crear_app(RAIZ, llm=Cliente(RAIZ, modo="reproducir"), dir_cache=tmp_path_factory.mktemp("cache"), precalentar=True)
    assert a.state.listo.wait(120)
    return a


@pytest.fixture(scope="module")
def cli(app):
    return TestClient(app)


def _leer(carpeta: Path) -> tuple[dict, dict]:
    return (json.loads((carpeta / "entrada.json").read_text(encoding="utf-8")),
            json.loads((carpeta / "respuesta.json").read_text(encoding="utf-8")))


def _cuerpo(ent: dict) -> dict:
    if "pregunta" in ent:
        return {"texto": ent["pregunta"]}
    c = {"consulta": ent["consulta"]}
    if ent.get("elegir") is not None:
        c["elegir"] = ent["elegir"]
    return c


# ---------------------------------------------------------------- equivalencia, sin exclusiones
@pytest.mark.parametrize("grupo", ["q", "matriz"])
def test_equivalencia_via_estructurada(cli, grupo):
    casos = _casos(grupo)
    assert casos
    for c in casos:
        ent, esperado = _leer(c)
        r = cli.post("/api/preguntar", json=_cuerpo(ent))
        assert r.json() == esperado, c.name


def test_equivalencia_via_texto_con_cache_nueva_por_comparacion(app, cli, tmp_path):
    casos = _casos("evaluacion")
    assert len(casos) == 140
    for i, c in enumerate(casos):
        ent, esperado = _leer(c)
        app.state.dir_cache = tmp_path / f"cache{i}"                 # carpeta nueva: «cache» sale igual que en la base
        r = cli.post("/api/preguntar", json=_cuerpo(ent))
        assert r.json() == esperado, c.name


# ---------------------------------------------------------------- elegir acumulado
def test_elegir_acumulado_dos_aclaraciones(cli):
    sin = {"intencion": "comparacion", "tema": "anemia", "territorio": {"texto": "Ayaviri"}, "comparar_con": {"texto": "Ayaviri"},
           "periodo": {"tipo": "ultimo"}, "pregunta_original": "prueba de elegir acumulado", "idioma": "es"}
    r0 = cli.post("/api/preguntar", json={"consulta": sin}).json()
    assert r0["tipo"] == "aclaracion"
    r1 = cli.post("/api/preguntar", json={"consulta": sin, "elegir": [1]}).json()
    assert r1["tipo"] == "aclaracion"                                 # falta la segunda aclaración
    r2 = cli.post("/api/preguntar", json={"consulta": sin, "elegir": [1, 2]}).json()
    assert r2["tipo"] != "aclaracion"


# ---------------------------------------------------------------- salud y precalentamiento
def test_salud_antes_y_despues_del_precalentamiento(tmp_path):
    a = crear_app(RAIZ, llm=Cliente(RAIZ, modo="reproducir"), dir_cache=tmp_path, precalentar=True)
    c = TestClient(a)
    assert a.state.listo.wait(120)
    assert c.get("/salud").status_code == 200 and c.get("/salud").json() == {"estado": "ok"}
    a.state.listo.clear()                                             # mientras corre el precalentamiento
    r = c.get("/salud")
    assert r.status_code == 503 and r.json() == {"estado": "preparando"}
    p = c.post("/api/preguntar", json={"texto": "hola"})
    assert p.status_code == 503 and p.json()["texto"].startswith("Estamos preparando el servicio…")
    a.state.listo.set()
    assert c.get("/salud").status_code == 200


def test_el_precalentamiento_corre_en_un_hilo_aparte(tmp_path):
    a = crear_app(RAIZ, dir_cache=tmp_path, precalentar=True)
    assert a.state.error_precalentamiento is None
    assert a.state.listo.wait(120)
    assert a.state.error_precalentamiento is None


# ---------------------------------------------------------------- errores con textos de la web
def test_errores_con_textos_de_la_web_sin_texto_de_terminal(cli):
    malas = [
        {"consulta": {"intencion": "no_existe"}},
        {"consulta": {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Puno"}, "periodo": {"tipo": "ultimo"},
                      "pregunta_original": "x"}, "elegir": [1]},
        {"consulta": {}},
        {"texto": "x" * 5000},
        {"texto": 3},
        {"texto": "hola", "consulta": {}},
        {},
        {"texto": "hola", "elegir": ["a"]},
        {"consulta": {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Huancavelica"},
                      "periodo": {"tipo": "ultimo"}, "pregunta_original": "x"}, "elegir": [9]},
    ]
    for cuerpo in malas:
        r = cli.post("/api/preguntar", json=cuerpo)
        assert r.status_code in (200, 422), cuerpo
        texto = r.text.lower()
        for prohibido in ("--elegir", "repite el comando", "comando"):
            assert prohibido not in texto, (cuerpo, r.text)
    r = cli.post("/api/preguntar", content="no es json", headers={"content-type": "application/json"})
    assert r.status_code == 422 and "--elegir" not in r.text and r.json()["motivo"] == "solicitud_invalida"
    r = cli.post("/api/preguntar", json={"consulta": {"intencion": "no_existe"}})
    assert r.status_code == 422 and r.json()["motivo"] == "consulta_invalida"


def test_eleccion_invalida_usa_el_texto_de_la_web(cli):
    c = {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Huancavelica"}, "periodo": {"tipo": "ultimo"},
         "pregunta_original": "x", "idioma": "es"}
    r = cli.post("/api/preguntar", json={"consulta": c, "elegir": [9]})
    assert r.status_code == 422 and r.json()["motivo"] == "eleccion_invalida"
    assert "--" not in r.json()["texto"]


# ---------------------------------------------------------------- sin GET con la pregunta
def test_no_hay_get_que_lleve_la_pregunta(app, cli):
    for ruta in app.routes:
        if "GET" in getattr(ruta, "methods", ()):
            assert ruta.path in ("/salud", "/api/opciones", "/api/version"), ruta.path
    r = cli.get("/api/preguntar", params={"texto": "hola"})
    assert r.status_code == 405 and "--elegir" not in r.text


# ---------------------------------------------------------------- opciones y versión
def test_opciones_y_version(cli):
    o = cli.get("/api/opciones").json()
    assert {"anemia", "gasto_publico"} <= {t["id"] for t in o["temas"]}
    assert "nivel_actual" in {i["id"] for i in o["intenciones"]} and o["niveles"] and o["ejemplos"]
    v = cli.get("/api/version").json()
    assert {"cubo", "commit_cubo", "reglas", "rotulo"} <= set(v)
    assert re.fullmatch(r"Biblioteca [0-9a-f]{12}, construida el \d{4}-\d{2}-\d{2}", v["rotulo"])


# ---------------------------------------------------------------- candado
def test_dos_peticiones_simultaneas_dan_lo_mismo_que_en_serie(app, cli):
    casos = [_leer(c) for c in _casos("q")[:4]]
    enserie = [cli.post("/api/preguntar", json=_cuerpo(e)).json() for e, _ in casos]
    resultados: dict[int, dict] = {}

    def pedir(i: int, ent: dict) -> None:
        resultados[i] = TestClient(app).post("/api/preguntar", json=_cuerpo(ent)).json()

    hilos = [threading.Thread(target=pedir, args=(i, e)) for i, (e, _) in enumerate(casos + casos)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    for i, esperado in enumerate(enserie + enserie):
        assert resultados[i] == esperado


def test_el_candado_envuelve_la_llamada_al_motor(app, cli, monkeypatch):
    import pap.web.app as W
    visto = []
    original = W.preguntar_minima

    def espia(*a, **k):
        visto.append(app.state.candado.locked())
        return original(*a, **k)

    monkeypatch.setattr(W, "preguntar_minima", espia)
    ent, _ = _leer(_casos("q")[0])
    cli.post("/api/preguntar", json=_cuerpo(ent))
    assert visto == [True]


# ---------------------------------------------------------------- imports permitidos
PERMITIDOS = {
    "pap.motor.validador.contexto": {"cargar_contexto"},
    "pap.motor.respuesta": {"Motor"},
    "pap.motor.preguntar": {"preguntar_minima", "EleccionInvalida"},
    "pap.motor.consulta": {"ConsultaInvalida"},
    "pap.motor.plantillas": {"textos", "parametros"},
    "pap.motor.formato": None,                                        # solo S3-04
    "pap.interprete.interpretar": {"interpretar"},
    "pap.interprete.llm": None,                                       # el adaptador del intérprete
}


def test_imports_permitidos_en_pap_web():
    for f in sorted((RAIZ / "src/pap/web").glob("*.py")):
        for nodo in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0 and nodo.module.startswith("pap"):
                assert nodo.module in PERMITIDOS, f"{f.name}: import no permitido de {nodo.module}"
                ok = PERMITIDOS[nodo.module]
                assert ok is None or {a.name for a in nodo.names} <= ok, f"{f.name}: {nodo.module} {[a.name for a in nodo.names]}"
            elif isinstance(nodo, ast.Import):
                for a in nodo.names:
                    assert not a.name.startswith(("pap.motor", "pap.capa0")), f"{f.name}: import {a.name}"
            elif isinstance(nodo, ast.ImportFrom) and nodo.level:
                pytest.fail(f"{f.name}: import relativo no previsto")
