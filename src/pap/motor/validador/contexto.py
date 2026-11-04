"""Carga del contexto del validador desde la biblioteca (o desde una copia con la misma estructura)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import duckdb
import yaml

from .nucleo import Contexto


def cargar_contexto(raiz: Path, con_cubo: bool = True) -> Contexto:
    raiz = Path(raiz)
    rj = json.loads((raiz / "reglas" / "reglas.json").read_text(encoding="utf-8"))
    reglas = {r["id"]: r for r in rj["reglas"]}
    cat = {f["id"]: f for f in json.loads((raiz / "catalogo" / "catalogo_fuentes.json").read_text(encoding="utf-8"))}
    inf_p = raiz / "catalogo" / "inferencia_verificada.csv"
    inferencia = list(csv.DictReader(open(inf_p, encoding="utf-8"))) if inf_p.exists() else []
    datos = raiz / "curados" / "capa0"
    dom = yaml.safe_load((datos / "dominios.yaml").read_text(encoding="utf-8"))
    inds = {i["id"]: i for i in yaml.safe_load((datos / "dim_indicador.yaml").read_text(encoding="utf-8"))["indicadores"]}
    cruces = yaml.safe_load((datos / "cruces_permitidos.yaml").read_text(encoding="utf-8"))["cruces"]
    doradas = list(csv.DictReader(open(datos / "cifras_doradas.csv", encoding="utf-8")))
    man = {}
    for carpeta in ("biblioteca/dimensiones", "biblioteca/estandarizada/encuestas",
                    "biblioteca/estandarizada/mapa_pobreza", "biblioteca/indicadores"):
        for m in sorted((raiz / carpeta).glob("manifiesto_*.json")):
            man[m.stem.replace("manifiesto_", "")] = json.loads(m.read_text(encoding="utf-8"))
    con = duckdb.connect()
    ub = raiz / "biblioteca" / "dimensiones" / "dim_ubigeo_historico.parquet"
    ubigeos = con.execute(f"SELECT * FROM read_parquet('{ub}')").df() if ub.exists() else None
    cubo = None
    cp = raiz / "biblioteca" / "indicadores" / "fact_indicador.parquet"
    if con_cubo and cp.exists():
        cubo = con.execute(f"SELECT * FROM read_parquet('{cp}')").df()
    ctx = Contexto(reglas=reglas, pg=rj["parametros_globales"], catalogo=cat, inferencia=inferencia,
                   dominios=dom.get("reglas", []), ubigeos=ubigeos, manifiestos=man, doradas=doradas, cruces=cruces,
                   indicadores=inds, cubo=cubo, lenguaje=rj.get("lenguaje"), ficha=rj.get("ficha_limites"))
    ctx.etapas = rj["etapas"]
    # pruebas de cada construcción (p. ej. la carga del SIEN en s3_puentes: R-TERRITORIO-02, auditoría P2 N-6)
    ctx.pruebas = {}
    for carpeta in ("biblioteca/dimensiones", "biblioteca/estandarizada/encuestas",
                    "biblioteca/estandarizada/mapa_pobreza", "biblioteca/indicadores"):
        for pr in sorted((raiz / carpeta).glob("pruebas_*.json")):
            ctx.pruebas[pr.stem.replace("pruebas_", "")] = json.loads(pr.read_text(encoding="utf-8"))
    for nombre, attr in (("dim_ambito", "ambitos"), ("dim_tema_gasto", "tema_gasto")):
        p = raiz / "biblioteca" / "dimensiones" / f"{nombre}.parquet"
        setattr(ctx, attr, con.execute(f"SELECT * FROM read_parquet('{p}')").df() if p.exists() else None)
    ctx.raiz = raiz
    return ctx
