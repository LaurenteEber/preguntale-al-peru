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
from pap.interprete.llm import Cliente, NoDisponible, registrar_uso  # noqa: E402
from pap.interprete.prompt import armar  # noqa: E402


def preguntas(raiz: Path) -> dict[str, str]:
    out = {}
    for ruta in ("tests/interprete/evaluacion.yaml", "tests/interprete/preguntas_prueba.yaml"):
        p = raiz / ruta
        if p.exists():
            out.update({e["id"]: e["pregunta"] for e in yaml.safe_load(p.read_text(encoding="utf-8"))["entradas"]})
    return out


def estimar(raiz: Path, n: int) -> dict:
    """Costo máximo estimado de n llamadas, con los precios de `interprete`: entrada ≈ caracteres de las instrucciones y del
    esquema / 3 (por exceso) y salida = `max_tokens` (el peor caso). Sirve para no pasar `tope_por_corrida` antes de llamar."""
    import json
    c = Cliente(raiz, modo="reproducir")
    prompt, _ = armar(raiz)
    entrada = (len(prompt) + len(json.dumps(c._cuerpo(prompt, "x")["output_config"], ensure_ascii=False))) // 3 + 200
    salida = int(c.par["max_tokens"]["valor"])
    pr = c.par["precios_usd_por_millon"]
    una = entrada * float(pr["entrada"]) / 1e6 + salida * float(pr["salida"]) / 1e6
    return {"llamadas": n, "tokens_entrada_por_llamada": entrada, "tokens_salida_max": salida, "usd_por_llamada": round(una, 4),
            "usd_max": round(una * n, 4), "tope_usd": c.tope}


def grabar(raiz: Path, ids: list[str] | None, cliente: Cliente | None = None) -> dict:
    todas = preguntas(raiz)
    faltan = [i for i in ids or [] if i not in todas]
    if faltan:
        raise SystemExit(f"ids que no están en el conjunto ni en las pruebas: {faltan}")
    prompt, version = armar(raiz)
    cliente = cliente or Cliente(raiz, modo="grabar")
    hechas, cortado = [], None
    for i in ids or list(todas):
        limpia = limpiar(todas[i], raiz).texto
        try:
            r = cliente.interpretar_crudo(prompt, limpia, version)
        except NoDisponible as e:
            cortado = e.motivo
            break
        registrar_uso(raiz, limpia, None, "grabada", r)                # salidas/interprete/uso.jsonl, fuera de git (P-03)
        hechas.append((i, r.grabacion, r.costo_usd, r.tokens_entrada, r.tokens_salida))
    return {"hechas": hechas, "cortado": cortado, "gastado_usd": round(cliente.gastado, 6)}


def _grabada(raiz: Path, pregunta: str) -> bool:
    from pap.interprete.llm import ruta_grabacion
    c = Cliente(raiz, modo="reproducir")
    _, version = armar(raiz)
    return ruta_grabacion(raiz, limpiar(pregunta, raiz).texto, c.par["modelo"]["valor"], version).exists()


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--grabar", action="store_true", required=True)
    a.add_argument("--solo", help="ids separados por coma")
    a.add_argument("--faltantes", action="store_true", help="graba solo las que no tienen grabación")
    x = a.parse_args(argv)
    ids = x.solo.split(",") if x.solo else None
    if x.faltantes:
        ids = [i for i in (ids or list(preguntas(RAIZ))) if not _grabada(RAIZ, preguntas(RAIZ)[i])]
    e = estimar(RAIZ, len(ids) if ids is not None else len(preguntas(RAIZ)))
    print(f"estimado (máximo): {e['llamadas']} llamadas × US$ {e['usd_por_llamada']:.4f} = US$ {e['usd_max']:.4f} · tope US$ {e['tope_usd']:.2f}")
    if e["usd_max"] > e["tope_usd"]:
        print("el máximo estimado pasa el tope: la corrida se cortará al llegar al tope")
    r = grabar(RAIZ, ids)
    for i, g, c, te, ts in r["hechas"]:
        print(f"{i}: {g} · tokens {te} + {ts} · US$ {c:.4f}")
    print(f"gastado: US$ {r['gastado_usd']:.4f}" + (f" · cortado: {r['cortado']}" if r["cortado"] else ""))
    return 1 if r["cortado"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
