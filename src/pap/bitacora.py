"""Registro de verificaciones (verificaciones.jsonl): una línea por cada revisión, incluidas las «sin cambio»."""
from __future__ import annotations

import json

from .config import Rutas
from .util import ahora, anexar_jsonl

RESULTADOS = {"nuevo", "contenido", "sin_cambio", "ok", "fallo", "error"}


def anotar(rutas: Rutas, source_id: str | None, accion: str, resultado: str, *,
           hash: str | None = None, captura: str | None = None, detalle: str | None = None) -> dict:
    assert resultado in RESULTADOS, resultado
    linea = {
        "fecha": ahora(),
        "source_id": source_id,
        "accion": accion,
        "resultado": resultado,
        "hash": hash,
        "captura": captura,
        "detalle": detalle,
    }
    anexar_jsonl(rutas.verificaciones, linea)
    return linea


def leer(rutas: Rutas) -> list[dict]:
    if not rutas.verificaciones.exists():
        return []
    with open(rutas.verificaciones, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
