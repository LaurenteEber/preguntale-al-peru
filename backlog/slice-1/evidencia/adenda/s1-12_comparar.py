"""S1-12: compara el cubo nuevo (soles constantes) con la copia previa a la adenda (biblioteca/_respaldo_pre_adenda/, S1-11).

Comprueba que las filas que ya existían son iguales en todas sus columnas anteriores salvo `version_tabla`, que las filas
nuevas son solo `devengado_constante` del gasto, y recalcula el factor del IPC desde dim_ipc.
Uso, desde la raíz: uv run python backlog/slice-1/evidencia/adenda/s1-12_comparar.py
"""
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
CLAVE = ["indicador_id", "anio", "nivel", "territorio_id", "medida", "linea"]

antes = pd.read_parquet(RAIZ / "biblioteca/_respaldo_pre_adenda/indicadores/fact_indicador.parquet")
ahora = pd.read_parquet(RAIZ / "biblioteca/indicadores/fact_indicador.parquet")
ipc = pd.read_parquet(RAIZ / "biblioteca/dimensiones/dim_ipc.parquet")
fallos = 0

print(f"Filas: antes {len(antes):,}, ahora {len(ahora):,}, nuevas {len(ahora) - len(antes):,}")
nuevas_cols = sorted(set(ahora.columns) - set(antes.columns))
print("Columnas nuevas:", nuevas_cols, "· quitadas:", sorted(set(antes.columns) - set(ahora.columns)))
print("version_tabla: antes", sorted(antes.version_tabla.unique()), "→ ahora", sorted(ahora.version_tabla.unique()))

m = antes.merge(ahora, on=CLAVE, how="outer", suffixes=("_a", "_n"), indicator=True)
perdidas = m[m._merge == "left_only"]
nuevas = m[m._merge == "right_only"]
print(f"Filas que ya existían y faltan ahora: {len(perdidas)}")
fallos += len(perdidas)
print("Filas nuevas por indicador y medida:",
      nuevas.groupby(["indicador_id", "medida"]).size().to_dict())
if set(nuevas.medida) != {"devengado_constante"} or set(nuevas.indicador_id) != {"gasto_ex_pan", "gasto_ex_pan_opcion_c"}:
    print("DIF: hay filas nuevas que no son devengado_constante del gasto")
    fallos += 1

ambas = m[m._merge == "both"]
comunes = [c for c in antes.columns if c not in CLAVE and c != "version_tabla"]
for c in comunes:
    a, n = ambas[f"{c}_a"], ambas[f"{c}_n"]
    distinta = ~((a == n) | (a.isna() & n.isna())).fillna(False).astype(bool)
    if distinta.any():
        print(f"DIF columna {c}: {int(distinta.sum())} filas")
        fallos += 1
print(f"Filas que ya existían: {len(ambas):,}; columnas comparadas: {len(comunes)} (todas salvo version_tabla): "
      f"{'iguales' if not fallos else 'con diferencias'}")
sobra = ahora.merge(antes[CLAVE], on=CLAVE, how="left", indicator=True)
viejas_ahora = sobra[sobra._merge == "both"]
if viejas_ahora[nuevas_cols].notna().any().any():
    print("DIF: columnas nuevas con valor en filas que ya existían")
    fallos += 1

prom = ipc.groupby("anio").agg(p=("ipc_prom_anual", "first"), completo=("anio_completo", "all"), meses=("mes", "count"))
print("\nIPC (dim_ipc, ipc_prom_anual):")
for a in (2023, 2024, 2025):
    print(f"  {a}: {prom.p[a]:.6f} (meses {prom.meses[a]}, completo {bool(prom.completo[a])})")
base = int(ahora.anio_base_deflactor.dropna().unique()[0])
f23 = prom.p[base] / prom.p[2023]
print(f"Año base: {base}; factor 2023→{base} = {prom.p[base]:.6f} / {prom.p[2023]:.6f} = {f23:.7f}")
fallos += round(f23, 7) != 1.0388706

nac = ahora[(ahora.indicador_id == "gasto_ex_pan") & (ahora.nivel == "nacional") & (ahora.linea == "cifra")]
print("\nGasto ex-PAN nacional (millones):")
for a in (2023, 2024, 2025):
    d = nac[(nac.anio == a) & (nac.medida == "devengado")].valor.iloc[0]
    k = nac[(nac.anio == a) & (nac.medida == "devengado_constante")]
    print(f"  {a}: devengado {d / 1e6:,.1f} · en soles de {base} {k.valor.iloc[0] / 1e6:,.1f} (factor {k.factor_deflactor.iloc[0]:.7f})")
cst = ahora[ahora.medida == "devengado_constante"].merge(
    ahora[ahora.medida == "devengado"], on=["indicador_id", "anio", "nivel", "territorio_id", "linea"], suffixes=("", "_d"))
dif = (cst.valor - cst.valor_d * cst.factor_deflactor).abs().max()
print(f"\nmáx |devengado_constante − devengado × factor| = {dif:.2e} soles en {len(cst):,} filas")
fallos += dif >= 1e-6
print("\nResultado:", "OK" if not fallos else f"{fallos} diferencias")
sys.exit(1 if fallos else 0)
