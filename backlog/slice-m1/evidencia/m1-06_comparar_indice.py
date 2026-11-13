"""M1-05 tarea 0 y M1-06: compara columna por columna el variables.parquet de antes (copia guardada) y el de después.
Uso: uv run python backlog/slice-m1/evidencia/m1-06_comparar_indice.py <antes.parquet> <despues.parquet>"""
import sys
import polars as pl

a = pl.read_parquet(sys.argv[1]).sort("var_id")
b = pl.read_parquet(sys.argv[2]).sort("var_id")
print(f"Filas: antes {a.height}, después {b.height}; mismos var_id y mismo orden: {a['var_id'].to_list() == b['var_id'].to_list()}\n")
print("| Columna | Estado | Filas distintas |\n|---|---|---|")
for c in b.columns:
    if c not in a.columns:
        print(f"| `{c}` | **nueva** | {b[c].is_not_null().sum()} con valor |")
    else:
        d = sum(1 for x, y in zip(a[c].to_list(), b[c].to_list()) if x != y)
        print(f"| `{c}` | {'igual' if d == 0 else '**cambia**'} | {d} |")
print("\nColumnas que estaban y ya no están:", [c for c in a.columns if c not in b.columns] or "ninguna")
print(f"\n`clase` vacía antes: {a['clase'].null_count()}; después: {b['clase'].null_count()}")
