"""S2-04 — Limpieza de la pregunta (P-03), antes del LLM, de la caché, del registro y de `pregunta_original`: recorte a
`interprete.pregunta_max_caracteres` con aviso fijo, sin caracteres de control, y los números con forma de DNI, RUC o celular
y los correos reemplazados por `[dato personal]` (patrones en `interprete.datos_personales`). Los años no se tocan."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Limpia:
    texto: str
    avisos: list[str] = field(default_factory=list)
    reemplazos: int = 0


def _yaml(raiz, ruta):
    return yaml.safe_load((Path(raiz) / ruta).read_text(encoding="utf-8"))


def limpiar(pregunta: str, raiz) -> Limpia:
    par = _yaml(raiz, "curados/motor/parametros_motor.yaml")["interprete"]
    tx = _yaml(raiz, "curados/motor/textos/interprete.yaml")
    t = "".join(c if c in "\n\t" or unicodedata.category(c)[0] != "C" else " " for c in str(pregunta))
    t = " ".join(t.split())
    dp = par["datos_personales"]
    n = 0
    for patron in dp["valor"].values():
        t, k = re.subn(patron, dp["reemplazo"], t)
        n += k
    avisos = []
    tope = int(par["pregunta_max_caracteres"]["valor"])
    if len(t) > tope:
        t = t[:tope]
        avisos.append(tx["pregunta_recortada"].format(n=tope))
    return Limpia(t, avisos, n)
