"""S3-08 — Medición de rendimiento del servicio web. Comando aparte, fuera de pytest:

    uv run python tests/web/medir.py [--n 200] [--semilla 3008] [--vivo 20 --tope-costo 0.50] [--arranques 3] [--sin-uvicorn]

Con el servicio precalentado (como en producción: `crear_app` + hilo de precalentamiento) mide, en el mismo proceso por la app
ASGI (TestClient, sin red), p50, p95 y máximo de:
  1. `--n` respuestas por la vía estructurada: los casos de la matriz reducida repetidos, en orden aleatorio con semilla fija;
  2. el conjunto de evaluación por texto, con las grabaciones del intérprete (sin LLM: no se llama a ningún proveedor);
  3. con `--vivo N`: N preguntas del conjunto (elegidas con la semilla) por el LLM de verdad, con tope de costo.
Separa intérprete, motor y página. Además: una muestra corta con uvicorn de verdad (la sobrecarga de HTTP) y el tiempo de arranque
hasta que `/salud` responde 200, en un proceso nuevo.

La corrida en vivo usa el cliente en modo «vivo» (no graba): no agrega ni cambia nada en tests/interprete/grabaciones/. La clave se
lee de la variable de entorno que dice `interprete.variable_clave`; este script nunca la ve. El costo sale de lo que suma el cliente y
del cambio en salidas/interprete/uso.jsonl (fuera de git). El límite por IP se desactiva (como en tests/web/test_guiado.py)."""
from __future__ import annotations

import argparse
import json
import math
import random
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path[:0] = [str(RAIZ / "src"), str(RAIZ / "tests"), str(RAIZ / "tests" / "interprete")]

import httpx  # noqa: E402
import yaml  # noqa: E402

USO = RAIZ / "salidas" / "interprete" / "uso.jsonl"


def percentil(xs: list[float], p: float) -> float:
    """Rango más cercano: el valor en la posición ceil(p·n) de la lista ordenada."""
    s = sorted(xs)
    return s[max(0, math.ceil(p * len(s)) - 1)] if s else float("nan")


def resumen(xs: list[float]) -> dict:
    return {"n": len(xs), "p50": percentil(xs, 0.50), "p95": percentil(xs, 0.95), "max": max(xs) if xs else float("nan")}


def fila(nombre: str, xs: list[float]) -> str:
    r = resumen(xs)
    return f"| {nombre} | {r['n']} | {r['p50']:.3f} | {r['p95']:.3f} | {r['max']:.3f} |"


ENCABEZADO = "| medida | n | p50 (s) | p95 (s) | máx (s) |\n|---|---|---|---|---|"


class Cronos:
    """Envuelve `interpretar` y `preguntar_minima` para sumar, por petición, el tiempo del intérprete (todo `interpretar`) y el del motor."""

    def __init__(self):
        self.motor = self.interprete = 0.0

    def reiniciar(self):
        self.motor = self.interprete = 0.0

    def instalar(self):
        import pap.motor.preguntar as P
        import pap.web.app as app_mod
        orig_pm, orig_int = P.preguntar_minima, app_mod.interpretar

        def pm(*a, **k):
            t = time.perf_counter()
            try:
                return orig_pm(*a, **k)
            finally:
                self.motor += time.perf_counter() - t

        def it(*a, **k):
            t = time.perf_counter()
            try:
                return orig_int(*a, **k)
            finally:
                self.interprete += time.perf_counter() - t

        P.preguntar_minima = pm                 # `interpretar()` llama a `P.preguntar_minima` (texto)
        app_mod.preguntar_minima = pm           # la app llama a su propia referencia (vía estructurada)
        app_mod.interpretar = it


def crear_servicio(dir_cache, registro_uso=None):
    """La app como en producción (con precalentamiento); espera a que `/salud` dé 200 y devuelve (app, segundos de arranque)."""
    from pap.web.app import crear_app
    t0 = time.perf_counter()
    app = crear_app(RAIZ, llm=None, dir_cache=dir_cache, precalentar=True, registro_uso=registro_uso)
    app.state.limites.por_minuto = 10 ** 9           # el límite por IP (S3-07) no entra en la medición
    assert app.state.listo.wait(timeout=300), "el precalentamiento no terminó"
    assert app.state.error_precalentamiento is None, app.state.error_precalentamiento
    return app, time.perf_counter() - t0


def casos_estructurados(n: int, semilla: int):
    """`n` casos: la matriz reducida repetida y mezclada con la semilla (la misma consulta que corre la matriz: consulta + elegir)."""
    from matriz import generar as G
    from pap.motor.respuesta import Motor
    from pap.motor.validador.contexto import cargar_contexto
    motor = Motor(cargar_contexto(RAIZ))
    par = G.parametros(RAIZ)
    base = G.reducida(G.casos(RAIZ, motor.ctx), par["casos_pytest"], par["semilla"])
    rng = random.Random(semilla)
    cola = []
    while len(cola) < n:
        lote = list(base)
        rng.shuffle(lote)
        cola += lote
    return base, cola[:n]


def pedir_html(cli, datos: dict):
    return cli.post("/preguntar", data=datos)


def medir_estructurada(app, cola, cron: Cronos) -> dict:
    from fastapi.testclient import TestClient
    cli = TestClient(app)
    out = {"html": [], "html_motor": [], "html_pagina": [], "api": [], "api_motor": [], "api_json": [], "estados": {}, "casos": []}
    for c in cola:
        elegir = c["elegir"]
        datos = {"consulta": json.dumps(c["consulta"], ensure_ascii=False)}
        if elegir:
            datos["elegir"] = ",".join(map(str, elegir if isinstance(elegir, list) else [elegir]))
        cron.reiniciar()
        t = time.perf_counter()
        r = pedir_html(cli, datos)
        total = time.perf_counter() - t
        out["html"].append(total)
        out["html_motor"].append(cron.motor)
        out["html_pagina"].append(total - cron.motor)
        out["estados"][r.status_code] = out["estados"].get(r.status_code, 0) + 1
        cuerpo = {"consulta": c["consulta"]}
        if elegir:
            cuerpo["elegir"] = elegir
        cron.reiniciar()
        t = time.perf_counter()
        r = cli.post("/api/preguntar", json=cuerpo)
        total = time.perf_counter() - t
        out["api"].append(total)
        out["api_motor"].append(cron.motor)
        out["api_json"].append(total - cron.motor)
        out["casos"].append((c["id"], total))
    return out


def preguntas_evaluacion() -> list[dict]:
    from evaluar import ARCHIVOS, entradas
    return list(entradas(RAIZ, ARCHIVOS[:1]).values())


def medir_texto(app, preguntas: list[dict], cron: Cronos, cliente, etiqueta: str) -> dict:
    """Cada pregunta del conjunto por la página (`POST /preguntar`, texto). `cliente`: grabaciones o en vivo. Sin caché de 24 h."""
    from fastapi.testclient import TestClient
    cli = TestClient(app)
    out = {"total": [], "interprete": [], "llm": [], "motor": [], "pagina": [], "estados": {}, "lentas": []}
    with tempfile.TemporaryDirectory() as cache:
        app.state.dir_cache, app.state.llm = Path(cache), cliente
        for e in preguntas:
            cron.reiniciar()
            antes = len(getattr(cliente, "llamadas", []))
            t = time.perf_counter()
            r = pedir_html(cli, {"texto": e["pregunta"]})
            total = time.perf_counter() - t
            llm = sum(x.latencia_s for x in getattr(cliente, "llamadas", [])[antes:])
            codigo_interp = max(0.0, cron.interprete - cron.motor - llm)
            out["total"].append(total)
            out["interprete"].append(codigo_interp)
            out["llm"].append(llm)
            out["motor"].append(cron.motor)
            out["pagina"].append(max(0.0, total - cron.interprete))
            out["estados"][r.status_code] = out["estados"].get(r.status_code, 0) + 1
            out["lentas"].append((e["id"], round(total, 3)))
        app.state.dir_cache = None
    out["lentas"].sort(key=lambda x: -x[1])
    return out


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def muestra_uvicorn(app, cola, n: int) -> dict:
    """`n` preguntas estructuradas (las primeras de `cola`) por HTTP real contra uvicorn en este proceso, API JSON y página."""
    import uvicorn
    puerto = puerto_libre()
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=puerto, log_level="warning"))
    hilo = threading.Thread(target=srv.run, daemon=True)
    hilo.start()
    while not srv.started:
        time.sleep(0.05)
    out = {"api": [], "html": []}
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{puerto}", timeout=30) as h:
            for c in cola[:n]:
                cuerpo = {"consulta": c["consulta"]}
                datos = {"consulta": json.dumps(c["consulta"], ensure_ascii=False)}
                if c["elegir"]:
                    cuerpo["elegir"] = c["elegir"]
                    datos["elegir"] = ",".join(map(str, c["elegir"] if isinstance(c["elegir"], list) else [c["elegir"]]))
                t = time.perf_counter()
                h.post("/api/preguntar", json=cuerpo)
                out["api"].append(time.perf_counter() - t)
                t = time.perf_counter()
                h.post("/preguntar", data=datos)
                out["html"].append(time.perf_counter() - t)
    finally:
        srv.should_exit = True
        hilo.join(timeout=10)
    return out


def solo_arranque() -> None:
    """Proceso hijo: levanta el servicio con uvicorn y avisa («ok») cuando `/salud` responde 200."""
    import uvicorn
    from pap.web.app import crear_app
    puerto = puerto_libre()
    app = crear_app(RAIZ)
    srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=puerto, log_level="warning"))
    threading.Thread(target=srv.run, daemon=True).start()
    while True:
        try:
            if httpx.get(f"http://127.0.0.1:{puerto}/salud", timeout=2).status_code == 200:
                print("ok", flush=True)
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.05)


def arranques(k: int) -> list[float]:
    """Segundos desde lanzar el proceso (imports incluidos) hasta que `/salud` da 200, en procesos nuevos."""
    tiempos = []
    for _ in range(k):
        t = time.perf_counter()
        p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--solo-arranque"], stdout=subprocess.PIPE, text=True)
        linea = p.stdout.readline().strip()
        tiempos.append(time.perf_counter() - t)
        p.kill()
        p.wait()
        assert linea == "ok", linea
    return tiempos


def costo_uso(desde: int) -> tuple[float, int]:
    """(suma de costo_usd, líneas) de lo que se agregó a salidas/interprete/uso.jsonl después de `desde` bytes."""
    if not USO.exists():
        return 0.0, 0
    with USO.open("rb") as f:
        f.seek(desde)
        lineas = [json.loads(x) for x in f.read().decode("utf-8").splitlines() if x.strip()]
    return sum(float(x.get("costo_usd") or 0) for x in lineas), len(lineas)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--n", type=int, default=200, help="respuestas por la vía estructurada")
    ap.add_argument("--semilla", type=int, default=3008)
    ap.add_argument("--vivo", type=int, default=0, help="preguntas del conjunto por el LLM de verdad (0: no se hace la corrida en vivo)")
    ap.add_argument("--tope-costo", type=float, help="US$ que cortan la corrida en vivo (obligatorio con --vivo)")
    ap.add_argument("--arranques", type=int, default=3)
    ap.add_argument("--uvicorn", type=int, default=50, help="tamaño de la muestra con uvicorn de verdad")
    ap.add_argument("--sin-uvicorn", action="store_true")
    ap.add_argument("--json", help="guarda los números en bruto en este archivo")
    ap.add_argument("--solo-arranque", action="store_true", help="(interno) proceso hijo de la medición de arranque")
    a = ap.parse_args(argv)
    if a.solo_arranque:
        solo_arranque()
        return 0
    if a.vivo and a.tope_costo is None:
        ap.error("--vivo exige --tope-costo (US$)")
    bruto: dict = {}
    L: list[str] = []

    arr = arranques(a.arranques) if a.arranques else []
    bruto["arranque_s"] = arr

    app, t_crear = crear_servicio(dir_cache=None, registro_uso=USO)      # el uso se registra como en producción (P-03: sin el texto)
    bruto["crear_y_precalentar_s"] = t_crear
    cron = Cronos()
    cron.instalar()
    base, cola = casos_estructurados(a.n, a.semilla)
    L += [f"# S3-08 medición (semilla {a.semilla}) — segundos, servicio precalentado", ""]

    # 1. vía estructurada
    est = medir_estructurada(app, cola, cron)
    bruto["estructurada"] = {k: v for k, v in est.items() if k != "casos"}
    L += [f"## 1. Vía estructurada: {len(cola)} respuestas ({len(base)} casos de la matriz reducida, repetidos y mezclados)", "",
          ENCABEZADO,
          fila("página HTML, total (POST /preguntar)", est["html"]), fila("  · motor", est["html_motor"]),
          fila("  · página (render y validación = total − motor)", est["html_pagina"]),
          fila("API JSON, total (POST /api/preguntar)", est["api"]), fila("  · motor", est["api_motor"]),
          fila("  · JSON y validación (total − motor)", est["api_json"]), "",
          f"Estados HTTP de la página: {est['estados']}. Los más lentos por API: "
          + ", ".join(f"{i} {s:.3f}" for i, s in sorted(est["casos"], key=lambda x: -x[1])[:5]), ""]

    # 2. conjunto de evaluación por texto con grabaciones (sin LLM)
    from pap.interprete.llm import Cliente
    preguntas = preguntas_evaluacion()
    gr = medir_texto(app, preguntas, cron, Cliente(RAIZ, modo="reproducir"), "grabaciones")
    bruto["texto_grabado"] = gr
    L += [f"## 2. Conjunto de evaluación por texto con grabaciones, sin LLM ({len(preguntas)} preguntas)", "", ENCABEZADO,
          fila("total (POST /preguntar con texto)", gr["total"]), fila("  · intérprete (código propio, sin LLM)", gr["interprete"]),
          fila("  · motor", gr["motor"]), fila("  · página (total − intérprete)", gr["pagina"]), "",
          f"Estados HTTP: {gr['estados']} (un 500 sería una pregunta sin grabación). Las 5 más lentas: "
          + ", ".join(f"{i} {s}" for i, s in gr["lentas"][:5]), ""]

    # 3. en vivo
    if a.vivo:
        rng = random.Random(a.semilla)
        elegidas = rng.sample(preguntas, a.vivo)
        cliente = Cliente(RAIZ, modo="vivo", tope_usd=a.tope_costo)         # «vivo»: no graba; modelo y esfuerzo, los configurados
        app.state.error_precalentamiento = None
        tam = USO.stat().st_size if USO.exists() else 0
        vivo = medir_texto(app, elegidas, cron, cliente, "vivo")
        usd_uso, n_uso = costo_uso(tam)
        bruto["vivo"] = {**vivo, "gastado_cliente_usd": cliente.gastado, "uso_usd": usd_uso, "uso_lineas": n_uso,
                         "ids": [e["id"] for e in elegidas], "modelo": cliente.par["modelo"]["valor"],
                         "esfuerzo": cliente.par["esfuerzo"]["valor"]}
        L += [f"## 3. En vivo: {len(elegidas)} preguntas del conjunto (modelo `{cliente.par['modelo']['valor']}`, "
              f"esfuerzo `{cliente.par['esfuerzo']['valor']}`)", "", ENCABEZADO,
              fila("total (POST /preguntar con texto)", vivo["total"]), fila("  · LLM (latencia del proveedor)", vivo["llm"]),
              fila("  · intérprete (código propio)", vivo["interprete"]), fila("  · motor", vivo["motor"]),
              fila("  · página (total − intérprete)", vivo["pagina"]), "",
              f"Estados HTTP: {vivo['estados']}. Llamadas HTTP al proveedor: {cliente.intentos_http}. "
              f"Costo según el cliente: US$ {cliente.gastado:.4f}; según el cambio en uso.jsonl: US$ {usd_uso:.4f} en {n_uso} líneas "
              f"(tope US$ {a.tope_costo:.2f}). Ids: {', '.join(bruto['vivo']['ids'])}.", ""]

    # 4. HTTP real
    if not a.sin_uvicorn:
        app.state.llm = None
        u = muestra_uvicorn(app, cola, a.uvicorn)
        bruto["uvicorn"] = u
        L += [f"## 4. HTTP real con uvicorn ({a.uvicorn} preguntas estructuradas, las mismas primeras de la serie 1)", "", ENCABEZADO,
              fila("API JSON por HTTP", u["api"]), fila("página HTML por HTTP", u["html"]),
              fila("(en proceso) API JSON, mismas preguntas", est["api"][:a.uvicorn]),
              fila("(en proceso) página HTML, mismas preguntas", est["html"][:a.uvicorn]), ""]

    L += ["## 5. Arranque", "",
          f"`crear_app` + precalentamiento hasta `listo` (con los módulos ya cargados): {t_crear:.1f} s.",
          "Desde lanzar el proceso (imports, uvicorn) hasta `/salud` 200, en procesos nuevos: "
          + (", ".join(f"{x:.1f} s" for x in arr) if arr else "no medido") + ".", ""]
    texto = "\n".join(L)
    print(texto)
    if a.json:
        Path(a.json).write_text(json.dumps(bruto, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
