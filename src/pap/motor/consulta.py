"""Consulta mínima (S1-01): carga y valida lo que pregunta el usuario contra el esquema
curados/motor/esquemas/consulta_minima.schema.json y traduce cada error a un mensaje en lenguaje sencillo
(curados/motor/textos/errores_consulta.yaml). Sin cifras ni plan de cálculo: eso lo decide el planificador (S1-03)."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

RUTA_ESQUEMA = Path("curados/motor/esquemas/consulta_minima.schema.json")
RUTA_MENSAJES = Path("curados/motor/textos/errores_consulta.yaml")
RUTA_INDICADORES = Path("curados/capa0/dim_indicador.yaml")


class ConsultaInvalida(Exception):
    """La consulta no cumple el contrato. `mensajes`: textos para el usuario (únicos, orden estable); `codigos`: sus claves."""

    def __init__(self, codigos: list[str], mensajes: list[str]):
        self.codigos = codigos
        self.mensajes = mensajes
        super().__init__(" ".join(mensajes))


def _yaml(ruta: Path):
    return yaml.safe_load(ruta.read_text(encoding="utf-8"))


def _codigo_de(e, esquema: dict, dato) -> str:
    """Código del error: casos especiales y, si no, el «x-error» más cercano (e.schema, luego e.parent, luego el campo)."""
    if e.validator == "required" and not e.path and isinstance(dato, dict):
        faltan = [r for r in e.validator_value if r not in dato]
        if "territorio" in faltan:
            return "falta_territorio"
        if "intencion" in faltan:
            return "falta_intencion"
    n = e
    while n is not None:
        if isinstance(n.schema, dict) and "x-error" in n.schema:
            codigo = n.schema["x-error"]
            if codigo == "tema_o_indicador" and isinstance(dato, dict) and "tema" in dato and "indicador" in dato:
                return "tema_e_indicador"
            return codigo
        n = n.parent
    campo = e.path[0] if e.path else None
    if campo == "territorio" and isinstance(dato, dict) and dato.get("intencion") == "identificar_extremo":
        return "territorio_extremo_invalido"
    props = esquema.get("properties", {})
    if campo in props and "x-error" in props[campo]:
        return props[campo]["x-error"]
    return esquema.get("x-error", "consulta_invalida")


def _semanticos(dato: dict, raiz: Path, codigos: set) -> None:
    ind = dato.get("indicador")
    if isinstance(ind, str) and "indicador_invalido" not in codigos:
        ids = {i["id"] for i in _yaml(raiz / RUTA_INDICADORES)["indicadores"]}
        if ind not in ids:
            codigos.add("indicador_invalido")
    p = dato.get("periodo")
    if (isinstance(p, dict) and p.get("tipo") == "serie" and "periodo_invalido" not in codigos
            and isinstance(p.get("desde"), int) and isinstance(p.get("hasta"), int) and p["desde"] > p["hasta"]):
        codigos.add("periodo_imposible")


def cargar(origen, raiz) -> dict:
    """`origen`: dict o ruta a un JSON. Devuelve la consulta validada (con idioma «es» por defecto) o lanza ConsultaInvalida."""
    raiz = Path(raiz)
    dato = json.loads(Path(origen).read_text(encoding="utf-8")) if isinstance(origen, (str, Path)) else origen
    esquema = json.loads((raiz / RUTA_ESQUEMA).read_text(encoding="utf-8"))
    mensajes = _yaml(raiz / RUTA_MENSAJES)["mensajes"]
    codigos: set = set()
    if not isinstance(dato, dict):
        codigos.add("no_es_objeto")
    else:
        for e in Draft202012Validator(esquema).iter_errors(dato):
            codigos.add(_codigo_de(e, esquema, dato))
        _semanticos(dato, raiz, codigos)
    if codigos:
        orden = list(mensajes)
        cods = sorted(codigos, key=lambda c: orden.index(c) if c in orden else len(orden))
        raise ConsultaInvalida(cods, list(dict.fromkeys(mensajes[c] for c in cods)))
    r = copy.deepcopy(dato)
    r.setdefault("idioma", "es")
    return r
