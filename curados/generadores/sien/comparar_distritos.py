"""Compara el SIEN del cubo con el Cuadro N.º 15 del INS (distrito del establecimiento), 2025, anemia 6–35 m.
Uso: python comparar_distritos.py <xlsx INS> <salida.csv>"""
import sys

import duckdb
import openpyxl
import pandas as pd

wb = openpyxl.load_workbook(sys.argv[1], read_only=True, data_only=True)
ins = pd.DataFrame([r[1:8] for r in wb["Anemia 6-35m x DISTRITO"].iter_rows(min_row=6, values_only=True)
                    if r[4] and isinstance(r[5], (int, float))],
                   columns=["dep", "prov", "dist", "ubigeo", "den_ins", "num_ins", "pct_ins"])
ins["ubigeo"] = ins.ubigeo.astype(str).str.zfill(6)
cubo = duckdb.sql("select territorio_id ubigeo, territorio_nombre, numerador num_cubo, denominador den_cubo "
                  "from 'biblioteca/indicadores/fact_indicador.parquet' where indicador_id='sien_anemia_tamizados_6_35m' "
                  "and linea='cifra' and nivel='distrito'").df()
rel = duckdb.sql("select * from 'biblioteca/dimensiones/rel_ubigeo_origen.parquet'").df()
nuevos = set(rel[[c for c in rel.columns if "ubigeo" in c]].astype(str).values.ravel())
m = ins.merge(cubo, on="ubigeo", how="outer", indicator=True)
m["igual"] = (m.num_ins == m.num_cubo) & (m.den_ins == m.den_cubo)
m["creado_o_madre"] = m.ubigeo.isin(nuevos)
m["dup_ins"] = m.ubigeo.duplicated(keep=False) & m.den_ins.notna()
m.to_csv(sys.argv[2], index=False)
b = m[m._merge == "both"]
print(f"INS: {len(ins)} filas ({ins.ubigeo.nunique()} ubigeos; {int(ins.den_ins.sum())} evaluados) | cubo: {len(cubo)} "
      f"distritos ({int(cubo.den_cubo.sum())} evaluados)")
print(f"en ambos: {len(b)}; idénticos: {int(b.igual.sum())}; distintos: {int((~b.igual).sum())} "
      f"(de ellos creados o madre: {int((~b.igual & b.creado_o_madre).sum())}; fila duplicada en el INS: {int((~b.igual & b.dup_ins).sum())})")
s = m[m._merge == "right_only"]
print(f"solo en el cubo: {len(s)} distritos, {int(s.den_cubo.sum())} evaluados (creados: {int(s.creado_o_madre.sum())}; "
      f"mediana {s.den_cubo.median():.0f} evaluados)")
for u in ("210801", "150132"):
    r = m[m.ubigeo == u].iloc[0]
    print(u, r.dist, "INS", int(r.num_ins), "/", int(r.den_ins), "cubo", int(r.num_cubo), "/", int(r.den_cubo))
