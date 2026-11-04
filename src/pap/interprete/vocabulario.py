"""S2-03 — Vocabulario del intérprete, leído de los mismos datos curados que usa el motor (temas, alias, intenciones, nombres de
Lima y palabras de nivel). No incluye años, cifras, nombres de distritos ni ningún dato de la biblioteca: si se agrega un tema
en dim_indicador y parametros_motor.yaml, el intérprete lo conoce sin tocar Python."""
from __future__ import annotations

from pathlib import Path

import yaml


def _yaml(raiz: Path, ruta: str):
    return yaml.safe_load((Path(raiz) / ruta).read_text(encoding="utf-8"))


def vocabulario(raiz) -> dict:
    par = _yaml(raiz, "curados/motor/parametros_motor.yaml")
    nsp = _yaml(raiz, "curados/motor/textos/no_se_puede.yaml")
    terr = _yaml(raiz, "curados/motor/textos/territorio.yaml")
    intenciones = list(_yaml(raiz, "curados/motor/intenciones.yaml")["intenciones"])
    desc = _yaml(raiz, "curados/interprete/intenciones_descripcion.yaml")["intenciones"]
    faltan = [i for i in intenciones if i not in desc]
    if faltan:
        raise ValueError(f"intenciones sin descripción en curados/interprete/intenciones_descripcion.yaml: {faltan}")
    temas = par["temas"]["vocabulario"]["valor"]
    alias = par["temas"]["alias_cli"]["valor"]
    return {
        "temas": {t: {"nombre": nsp["temas"].get(t, t), "alias": sorted(a for a, v in alias.items() if v == t)} for t in temas},
        "intenciones": {i: desc[i] for i in intenciones},
        "lima": list(terr["lima_opciones"].values()) + sorted(terr["alias_ambito"]),
        "niveles": par["territorio"]["palabras_que_fijan_nivel"]["valor"],
        "nacional": par["territorio"]["textos_nacional"]["valor"],
    }
