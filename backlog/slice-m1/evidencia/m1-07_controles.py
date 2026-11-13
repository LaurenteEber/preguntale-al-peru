#!/usr/bin/env python3
"""M1-07, tarea 6: imprime, para cada control de prueba, la cifra oficial (con su cuadro) frente a la que reproduce el motor.

Uso (desde la raíz del repositorio, en el Mac): uv run python backlog/slice-m1/evidencia/m1-07_controles.py"""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, "tests")
sys.path.insert(0, ".")
from inferencia.test_m107_controles import CONTROLES, cargar  # noqa: E402
from pap.inferencia import recetas  # noqa: E402
from pap.inferencia.duckdb_seguro import conexion_segura  # noqa: E402
from pap.inferencia.ejecutor import Ejecutor  # noqa: E402
from pap.inferencia.verificador import Contexto, verificar  # noqa: E402

RAIZ = Path(".").resolve()
ctx = Contexto.cargar(RAIZ)
ctx = replace(ctx, esquema=replace(ctx.esquema, variables={k: {**v, "estado": "revisado"} for k, v in ctx.esquema.variables.items()}))
con, ejecutor = conexion_segura(RAIZ), Ejecutor(raiz=RAIZ)
print(f"{'control':22} {'cifra':26} {'publicado':>9} {'nuestro':>8} {'dif pp':>7} {'casos INEI':>10} {'casos':>7}  pasa")
for id_ in CONTROLES:
    receta, por_area = cargar(id_)
    pc = verificar(receta.a_plan(2024, "nacional"), ctx, con)
    filas = recetas.reproducir_doradas(receta, [("nacional", e) for e in ejecutor.ejecutar({2024: pc}, ctx)])
    est, val = recetas.calcular_cortes(receta, por_area, RAIZ, ctx=ctx, ejecutor=ejecutor, con=con)
    filas += recetas.reproducir_doradas_cortes(receta, por_area, est, val)
    for f in filas:
        print(f"{id_:22} {f['id_cifra'].replace('CTL-' + id_.upper() + '-2024-', ''):26} {f['publicado']:>9} {f['nuestro']:>8} {f['dif_pp']:>7} {str(f['casos_publicados'] if f['casos_publicados'] is not None else '—'):>10} {f['n']:>7}  {f['pasa']}")
