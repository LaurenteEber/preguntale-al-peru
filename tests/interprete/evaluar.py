"""S2-04 — Corredor mínimo de grabaciones (S2-09 lo amplía con la evaluación en vivo).

    uv run python tests/interprete/evaluar.py --grabar [--solo id1,id2]

Graba la respuesta del LLM para preguntas del conjunto de evaluación (tests/interprete/evaluacion.yaml) y de las pruebas
(tests/interprete/preguntas_prueba.yaml), nunca de usuarios. Necesita la clave en la variable `interprete.variable_clave`.
El tope `interprete.tope_por_corrida` corta la corrida."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

from pap.interprete.limpiar import limpiar  # noqa: E402
from pap.interprete.llm import Cliente, NoDisponible  # noqa: E402
from pap.interprete.prompt import armar  # noqa: E402


def preguntas(raiz: Path) -> dict[str, str]:
    out = {}
    for ruta in ("tests/interprete/evaluacion.yaml", "tests/interprete/preguntas_prueba.yaml"):
        p = raiz / ruta
        if p.exists():
            out.update({e["id"]: e["pregunta"] for e in yaml.safe_load(p.read_text(encoding="utf-8"))["entradas"]})
    return out


def grabar(raiz: Path, ids: list[str] | None, cliente: Cliente | None = None) -> dict:
    todas = preguntas(raiz)
    faltan = [i for i in ids or [] if i not in todas]
    if faltan:
        raise SystemExit(f"ids que no están en el conjunto ni en las pruebas: {faltan}")
    prompt, version = armar(raiz)
    cliente = cliente or Cliente(raiz, modo="grabar")
    hechas, cortado = [], None
    for i in ids or list(todas):
        try:
            r = cliente.interpretar_crudo(prompt, limpiar(todas[i], raiz).texto, version)
        except NoDisponible as e:
            cortado = e.motivo
            break
        hechas.append((i, r.grabacion, r.costo_usd))
    return {"hechas": hechas, "cortado": cortado, "gastado_usd": round(cliente.gastado, 6)}


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--grabar", action="store_true", required=True)
    a.add_argument("--solo", help="ids separados por coma")
    x = a.parse_args(argv)
    r = grabar(RAIZ, x.solo.split(",") if x.solo else None)
    for i, g, c in r["hechas"]:
        print(f"{i}: {g} (US$ {c:.4f})")
    print(f"gastado: US$ {r['gastado_usd']:.4f}" + (f" · cortado: {r['cortado']}" if r["cortado"] else ""))
    return 1 if r["cortado"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
