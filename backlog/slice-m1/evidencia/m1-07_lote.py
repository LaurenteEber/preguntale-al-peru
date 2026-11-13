#!/usr/bin/env python3
"""M1-07, tarea 8: resumen del lote para el visto del dueño. Cuenta las variables de las 18 tablas del lote (índice) y, para cada variable
`categoria`, corre el verificador con un plan sencillo (la proporción de su primer código con sentido, sin restricciones) y cuenta qué control
decide: pasa, o falla por `y` nulo, universo, diseño, uniones, etc. Un plan que falla aquí no es un error de las tablas: el planificador agregará
la restricción que haga falta (p. ej. `no_es_nulo`). No calcula ninguna estimación.

Uso (desde la raíz, en el Mac): uv run python backlog/slice-m1/evidencia/m1-07_lote.py > backlog/slice-m1/evidencia/m1-07_lote.txt"""
import collections
import sys
from dataclasses import replace
from pathlib import Path

import polars as pl

from pap.inferencia import tablas_curadas as tc
from pap.inferencia.duckdb_seguro import conexion_segura
from pap.inferencia.plan import Plan
from pap.inferencia.verificador import Contexto, Falla, verificar

RAIZ = Path(".").resolve()
ctx = Contexto.cargar(RAIZ)
ctx = replace(ctx, esquema=replace(ctx.esquema, variables={k: {**v, "estado": "revisado"} for k, v in ctx.esquema.variables.items()}))
con = conexion_segura(RAIZ)
LOTE = [u.archivo for u in ctx.unidades]
v = pl.read_parquet(RAIZ / "biblioteca/variables/variables.parquet").filter((pl.col("anio") == 2024) & pl.col("archivo").is_in(LOTE))
print(f"Tablas del lote: {len(LOTE)}  ·  variables del índice en esas tablas: {v.height}  ·  estado: {dict(v['estado'].value_counts().iter_rows())}")
print("Por clase:", dict(sorted(v["clase"].value_counts().iter_rows(), key=lambda x: -x[1])))
print(f"Bloques temáticos de esas tablas: {v.filter(pl.col('bloque_id').is_not_null())['bloque_id'].n_unique()}\n")
print(f"{'tabla':10} {'unidad':8} {'vars':>5} {'categoría':>9} {'pasan':>6}  controles que decidieron en las demás")
total = collections.Counter()
for t in LOTE:
    fila = tc.unidad_de(ctx.unidades, "ENDES", 2024, t)
    vt = v.filter(pl.col("archivo") == t)
    cat = vt.filter((pl.col("clase") == "categoria") & pl.col("rol_faltante").is_null() & (pl.col("tipo_origen").is_null() | (pl.col("tipo_origen") != "construida_inei")))
    c = collections.Counter()
    for nombre in cat["variable"]:
        cats = ctx.esquema.categorias.get(f"ENDES·2024·{t}·{nombre}", {})
        codigos = [k for k, r in cats.items() if r.get("es_especial") in (None, "no", False) and not r.get("rol_faltante")]
        if len(codigos) < 2:
            c["sin_dos_codigos"] += 1
            continue
        plan = Plan.model_validate({"origen": "compuesto", "encuesta": "ENDES", "anios": [2024], "unidad": fila.unidad_plan, "medida": "proporcion",
                                    "indicador": {"combinar": "una", "condiciones": [{"var": f"ENDES·2024·{t}·{nombre}", "op": "en", "valores": [float(codigos[0])]}]},
                                    "territorio": {"nivel": "nacional", "id": None}})
        r = verificar(plan, ctx, con)
        c["pasa" if not isinstance(r, Falla) else f"{r.tipo}/{r.dimension}"] += 1
    total += c
    print(f"{t:10} {fila.unidad_plan:8} {vt.height:>5} {cat.height:>9} {c['pasa']:>6}  " + ", ".join(f"{k}: {n}" for k, n in c.most_common() if k != "pasa"))
print("\nTotal de variables categoría probadas:", sum(total.values()), "·", dict(total.most_common()))
