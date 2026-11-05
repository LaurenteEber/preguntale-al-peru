"""Interpretación de una pregunta en texto libre (slice 2, S2-01): valida contra
curados/motor/esquemas/interpretacion.schema.json lo que devuelve el LLM y traduce cada error a un código y un mensaje en
lenguaje sencillo (curados/motor/textos/errores_consulta.yaml), con el mismo mecanismo que la consulta mínima (consulta.py).

El esquema solo comprueba la forma: que cada ancla sea un fragmento literal de la pregunta, el vocabulario y el resto los
comprueba el código que interpreta (S2-05)."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .consulta import RUTA_MENSAJES, ConsultaInvalida, _codigo_de, _yaml

RUTA_ESQUEMA = Path("curados/motor/esquemas/interpretacion.schema.json")
RUTA_CONSULTA = Path("curados/motor/esquemas/consulta_minima.schema.json")
RUTA_PARAMETROS = Path("curados/motor/parametros_motor.yaml")
RESULTADOS = ("consulta", "aclaracion", "fuera_de_alcance", "no_es_pregunta", "otro_idioma")


class InterpretacionInvalida(ConsultaInvalida):
    """La interpretación no cumple el contrato. `codigos` y `mensajes` como en ConsultaInvalida."""


def validador(raiz) -> Draft202012Validator:
    raiz = Path(raiz)
    esquema = json.loads((raiz / RUTA_ESQUEMA).read_text(encoding="utf-8"))
    cm = json.loads((raiz / RUTA_CONSULTA).read_text(encoding="utf-8"))
    reg = Registry().with_resources([(cm["$id"], Resource.from_contents(cm)),
                                     ("consulta_minima.schema.json", Resource.from_contents(cm))])
    return Draft202012Validator(esquema, registry=reg)


def _resolver(esquemas: dict, base: str, ref: str) -> tuple[str, dict]:
    doc, _, frag = ref.partition("#")
    doc = doc or base
    nodo = esquemas[doc]
    for k in [x for x in frag.split("/") if x]:
        nodo = nodo[k]
    return doc, nodo


def _x_error(esquemas: dict, ruta) -> str | None:
    """El «x-error» más profundo a lo largo de la ruta del esquema del error, siguiendo los `$ref` (también al esquema de la
    consulta mínima)."""
    doc, nodo, codigo = "interpretacion", esquemas["interpretacion"], None
    for k in ruta:
        if isinstance(nodo, dict) and "x-error" in nodo:
            codigo = nodo["x-error"]
        # la ruta del error no trae los `$ref`: se resuelven cuando la clave no está en el nodo
        while isinstance(nodo, dict) and k not in nodo and "$ref" in nodo:
            doc, nodo = _resolver(esquemas, doc, nodo["$ref"])
            if "x-error" in nodo:
                codigo = nodo["x-error"]
        try:
            nodo = nodo[k]
        except (KeyError, IndexError, TypeError):
            break
    if isinstance(nodo, dict) and "x-error" in nodo:
        codigo = nodo["x-error"]
    return codigo


def _hojas(e):
    """Los errores más profundos de un `oneOf`/`anyOf` (los que explican por qué falló cada rama)."""
    if not e.context:
        return [e]
    return [h for c in e.context for h in _hojas(c)]


def _codigos(v: Draft202012Validator, dato, esquemas: dict) -> set[str]:
    """Códigos de error. Un `oneOf` de nivel superior se explica por la rama del `resultado` que trae el dato; dentro de
    ella, por el «x-error» más profundo de cada error."""
    out: set[str] = set()
    for e in v.iter_errors(dato):
        errores = [e]
        if e.validator == "oneOf" and not e.path and isinstance(dato, dict) and dato.get("resultado") in RESULTADOS:
            i = RESULTADOS.index(dato["resultado"])
            errores = [c for c in e.context if c.relative_schema_path and c.relative_schema_path[0] == i]
        for x in errores:
            hojas = _hojas(x)
            cods = {_x_error(esquemas, list(h.absolute_schema_path)) for h in hojas} - {None}
            out |= cods or {_codigo_de(x, v.schema, dato)}
        if not errores:
            out.add("interpretacion_invalida")
    return out


def validar(dato, raiz) -> dict:
    """Devuelve la interpretación si cumple el contrato (esquema y máximo de opciones de una aclaración) o lanza
    InterpretacionInvalida."""
    raiz = Path(raiz)
    codigos: set[str] = set()
    if not isinstance(dato, dict):
        codigos.add("no_es_objeto")
    else:
        v = validador(raiz)
        esquemas = {"interpretacion": v.schema,
                    "consulta_minima.schema.json": json.loads((raiz / RUTA_CONSULTA).read_text(encoding="utf-8"))}
        codigos |= _codigos(v, dato, esquemas)
        tope = _yaml(raiz / RUTA_PARAMETROS)["interprete"]["aclaracion_max_opciones"]["valor"]
        if dato.get("resultado") == "aclaracion" and isinstance(dato.get("opciones"), list) and len(dato["opciones"]) > tope:
            codigos.add("aclaracion_demasiadas_opciones")
    if codigos:
        mensajes = _yaml(raiz / RUTA_MENSAJES)["mensajes"]
        orden = list(mensajes)
        cods = sorted(codigos, key=lambda c: orden.index(c) if c in orden else len(orden))
        raise InterpretacionInvalida(cods, list(dict.fromkeys(mensajes.get(c, mensajes["interpretacion_invalida"]) for c in cods)))
    return dato
