"""S2-03 — Instrucciones del intérprete: curados/interprete/prompt.md con sus marcadores rellenados desde el vocabulario, los
ejemplos (curados/interprete/ejemplos.yaml) y el esquema de la interpretación. `version_prompt` es la huella SHA-256 del texto
ya armado (esquema incluido): viaja en cada interpretación y en las grabaciones."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from .vocabulario import vocabulario

RUTA_PROMPT = Path("curados/interprete/prompt.md")
RUTA_EJEMPLOS = Path("curados/interprete/ejemplos.yaml")
RUTA_ESQUEMA = Path("curados/motor/esquemas/interpretacion.schema.json")


def ejemplos(raiz) -> list[dict]:
    return yaml.safe_load((Path(raiz) / RUTA_EJEMPLOS).read_text(encoding="utf-8"))["ejemplos"]


def _temas(v: dict) -> str:
    return "\n".join(f"- `{t}`: {x['nombre']}" + (f" (también: {', '.join(x['alias'])})" if x["alias"] else "")
                     for t, x in v["temas"].items())


def _intenciones(v: dict) -> str:
    return "\n".join(f"- `{i}`: {d}" for i, d in v["intenciones"].items())


def _lugares(v: dict) -> str:
    niveles = "; ".join(f"{n}: {', '.join(p)}" for n, p in v["niveles"].items())
    return ("- En «¿dónde es más alto?» (`identificar_extremo`), `territorio` es `{\"nivel\": …}` con el nivel que se ordena "
            f"(palabras: {niveles}) y, si la persona lo dice, `dentro_de`.\n"
            f"- Nombres de Lima que se copian tal cual: {', '.join(v['lima'])}.\n"
            f"- Todo el país: {', '.join(v['nacional'])}.")


def _ejemplos(raiz) -> str:
    return "\n".join(f"Pregunta: {e['pregunta']}\nInterpretación: {json.dumps(e['interpretacion'], ensure_ascii=False)}\n"
                     for e in ejemplos(raiz))


def armar(raiz) -> tuple[str, str]:
    """(instrucciones, version_prompt)."""
    raiz = Path(raiz)
    v = vocabulario(raiz)
    esquema = json.dumps(json.loads((raiz / RUTA_ESQUEMA).read_text(encoding="utf-8")), ensure_ascii=False, indent=1)
    texto = (raiz / RUTA_PROMPT).read_text(encoding="utf-8")
    for k, x in {"{temas}": _temas(v), "{intenciones}": _intenciones(v), "{lugares}": _lugares(v),
                 "{ejemplos}": _ejemplos(raiz), "{esquema}": esquema}.items():
        assert k in texto, f"falta el marcador {k} en {RUTA_PROMPT}"
        texto = texto.replace(k, x)
    return texto, "sha256:" + hashlib.sha256(texto.encode("utf-8")).hexdigest()
