"""S3-02, tarea 4 — Regenera la base de la web: `backlog/slice-3/evidencia/base_api/`.

Guarda el `respuesta.json` completo (la respuesta del motor tal cual) de:
  - Q1–Q4 con `preguntar_minima` (curados/motor/consultas_minimas/), y Q1 también con «Abancay» + elegir=[1] (X-22, S3-01b)  -> q/
  - cada caso de la matriz reducida, con el mismo código que `tests/matriz/correr.py --reducida` (`correr_caso`),
    incluidas las aclaraciones, que la CLI no escribe                                                              -> matriz/
  - el conjunto de evaluación (tests/interprete/evaluacion.yaml) con `interpretar()` y las grabaciones (modo
    «reproducir»; nunca la red ni la clave), caché en una carpeta temporal fuera del repositorio, sin registro      -> evaluacion/

Cada carpeta lleva `respuesta.json` y `entrada.json` (lo que se preguntó). `MANIFIESTO.txt` dice de qué commit salió y cuántos
archivos hay. Las rutas no llevan fechas y el JSON va con `ensure_ascii=False, indent=1, sort_keys=True`: correrlo dos veces
seguidas no cambia ningún archivo. Es el patrón de equivalencia de S3-03 (la web debe dar lo mismo que el motor).

    uv run python backlog/slice-3/evidencia/s3-02_generar_base.py
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
SALIDA = Path(__file__).resolve().parent / "base_api"
sys.path[:0] = [str(RAIZ / "tests"), str(RAIZ / "src")]            # `matriz` (tests/) y `pap` (src/)

import yaml  # noqa: E402

from matriz import correr as R  # noqa: E402
from matriz import generar as G  # noqa: E402
from pap.interprete import llm as L  # noqa: E402
from pap.interprete.interpretar import interpretar  # noqa: E402
from pap.motor import preguntar as P  # noqa: E402

CONSULTAS = RAIZ / "curados" / "motor" / "consultas_minimas"
EVALUACION = RAIZ / "tests" / "interprete" / "evaluacion.yaml"


def slug(texto: str) -> str:
    """Nombre de carpeta estable: conserva letras (con tildes y ñ), cifras, «_» y «-»; el resto pasa a «_»."""
    s = unicodedata.normalize("NFC", texto).replace("|", "__")
    return re.sub(r"[^\w.-]+", "_", s, flags=re.UNICODE).strip("_")


def escribir(carpeta: Path, entrada: dict, respuesta: dict) -> int:
    carpeta.mkdir(parents=True, exist_ok=True)
    for nombre, dato in (("respuesta.json", respuesta), ("entrada.json", entrada)):
        (carpeta / nombre).write_text(json.dumps(dato, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return 2


def commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip()


def cambios_sin_commit() -> int:
    out = subprocess.run(["git", "status", "--porcelain", "--", ".", f":(exclude){SALIDA.relative_to(RAIZ)}"],
                         cwd=RAIZ, capture_output=True, text=True, check=True).stdout
    return len([x for x in out.splitlines() if x.strip()])


def main() -> int:
    motor, p, nombre = R.cargar()
    if SALIDA.exists():
        shutil.rmtree(SALIDA)                                         # se regenera entera: no quedan restos de una corrida anterior
    usados: set[str] = set()
    n = {"q": 0, "matriz": 0, "evaluacion": 0}

    def carpeta(grupo: str, nombre_: str) -> Path:
        c = SALIDA / grupo / slug(nombre_)
        assert str(c) not in usados, f"nombre de carpeta repetido: {c}"
        usados.add(str(c))
        return c

    # --- Q1–Q4 (y Q1 con «Abancay» + elegir=[1]: desde X-22 «Huancavelica» a secas ya no aclara)
    for f in sorted(CONSULTAS.glob("q*.json")):
        entrada = json.loads(f.read_text(encoding="utf-8"))
        n["q"] += escribir(carpeta("q", f.stem), {"consulta": entrada, "elegir": None}, P.preguntar_minima(motor, entrada))
    q1 = json.loads((CONSULTAS / "q1.json").read_text(encoding="utf-8"))
    q1["territorio"] = {"texto": "Abancay"}
    n["q"] += escribir(carpeta("q", "q1_abancay_elegir_1"), {"consulta": q1, "elegir": [1]}, P.preguntar_minima(motor, q1, elegir=[1]))

    # --- matriz reducida, con el mismo código que `tests/matriz/correr.py --reducida` (incluidas las aclaraciones)
    par = G.parametros(RAIZ)
    casos = G.reducida(G.casos(RAIZ, motor.ctx), par["casos_pytest"], par["semilla"])
    for caso in casos:
        r, res = R.correr_caso(motor, p, nombre, caso)
        assert res is not None, f"{caso['id']}: {r['fallos']}"
        n["matriz"] += escribir(carpeta("matriz", caso["id"]),
                                {"id": caso["id"], "consulta": caso["consulta"], "elegir": caso["elegir"], "clase": r["clase"]}, res)

    # --- conjunto de evaluación con grabaciones: nunca la red ni la clave
    cliente = L.Cliente(RAIZ, modo="reproducir")
    cache = Path(tempfile.mkdtemp(prefix="pap-s3-02-cache-"))         # fuera del repositorio
    try:
        for e in yaml.safe_load(EVALUACION.read_text(encoding="utf-8"))["entradas"]:
            res = interpretar(e["pregunta"], motor, llm=cliente, cache_dir=cache, registro=None)
            n["evaluacion"] += escribir(carpeta("evaluacion", e["id"]), {"id": e["id"], "pregunta": e["pregunta"]}, res)
    finally:
        shutil.rmtree(cache, ignore_errors=True)

    total = sum(n.values())
    (SALIDA / "MANIFIESTO.txt").write_text(
        "Base de la web (S3-02, tarea 4). La genera backlog/slice-3/evidencia/s3-02_generar_base.py.\n"
        f"commit: {commit()}\n"
        f"cambios sin commit en el resto del árbol: {cambios_sin_commit()} archivos\n"
        f"casos: q={n['q'] // 2} matriz={n['matriz'] // 2} evaluacion={n['evaluacion'] // 2}\n"
        f"archivos (sin este): {total}\n", encoding="utf-8")
    print(f"{total + 1} archivos en {SALIDA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
