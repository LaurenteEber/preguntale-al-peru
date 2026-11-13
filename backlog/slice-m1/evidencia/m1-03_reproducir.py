#!/usr/bin/env python3
"""M1-03: reproduce las doradas por corte con las recetas (camino nuevo) y escribe la tabla de evidencia en Markdown.
Uso (raíz del repo): uv run python backlog/slice-m1/evidencia/m1-03_reproducir.py > backlog/slice-m1/evidencia/m1-03_doradas_cortes.md"""
from pathlib import Path

from pap.inferencia import recetas as rc

RAIZ = Path(__file__).resolve().parents[3]
doradas = rc.leer_doradas_cortes(RAIZ)
print("| Receta | Corte | Categoría | Publicado (INEI) | Calculado | Diferencia (pp) | Casos publicados | Casos nuestros | Pasa |")
print("|---|---|---|---|---|---|---|---|---|")
total = malas = 0
mayor = 0.0
for receta in rc.leer_recetas(RAIZ):
    propias = [d for d in doradas if d.receta_id == receta.id]
    est, val = rc.calcular_cortes(receta, propias, RAIZ)
    for f in rc.reproducir_doradas_cortes(receta, propias, est, val):
        total += 1
        malas += not f["pasa"]
        mayor = max(mayor, abs(f["dif_pp"]))
        print(f"| {receta.id} | {f['corte']} | {f['categoria']} | {f['publicado']:.1f} | {f['nuestro']:.1f} | {f['dif_pp']:+.1f} | {f['casos_publicados']:,} | {f['n']:,} | {'sí' if f['pasa'] else 'NO'} |".replace(",", " "))
print(f"\n{total} doradas por corte, {total - malas} se reproducen, {malas} no; mayor |diferencia| = {mayor:.1f} pp (tolerancia 0,1 pp).")
