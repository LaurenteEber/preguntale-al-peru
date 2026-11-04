"""S1-00, tarea 6: comprueba que la reconstrucción solo cambió nombres. Compara contra 05_biblioteca/_respaldo_pre_s1-00/.

Uso: uv run python backlog/slice-1/evidencia/s1-00_comparar.py > backlog/slice-1/evidencia/s1-00_comparacion_cubo.txt
"""
import subprocess
from datetime import datetime
from pathlib import Path

import duckdb
import yaml

R = Path(__file__).resolve().parents[3]
B = R / "05_biblioteca"
A = B / "_respaldo_pre_s1-00"
con = duckdb.connect()
commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=R, capture_output=True, text=True).stdout.strip()
print(f"# {datetime.now():%Y-%m-%d %H:%M} commit {commit} — S1-00, comparación antes (respaldo) / después (reconstrucción)\n")

NOMBRES_CUBO = {"territorio_nombre"}  # columnas de nombre de territorio
CLAVE = ["indicador_id", "anio", "nivel", "territorio_id", "medida", "linea"]  # calculo.CLAVE


def cols(p):
    return [d[0] for d in con.execute(f"DESCRIBE SELECT * FROM '{p}'").fetchall()]


def distintos(a, b, clave, excluir):
    ca = cols(a)
    comunes = [c for c in ca if c in cols(b) and c not in clave and c not in excluir]
    k = " AND ".join(f"x.{c} IS NOT DISTINCT FROM y.{c}" for c in clave)
    na = con.execute(f"SELECT count(*) FROM '{a}'").fetchone()[0]
    nb = con.execute(f"SELECT count(*) FROM '{b}'").fetchone()[0]
    solo_a = con.execute(f"SELECT count(*) FROM '{a}' x ANTI JOIN '{b}' y ON {k}").fetchone()[0]
    solo_b = con.execute(f"SELECT count(*) FROM '{b}' y ANTI JOIN '{a}' x ON {k}").fetchone()[0]
    por_col = {}
    for c in comunes:
        n = con.execute(f"SELECT count(*) FROM '{a}' x JOIN '{b}' y ON {k} WHERE x.{c} IS DISTINCT FROM y.{c}").fetchone()[0]
        if n:
            por_col[c] = n
    return na, nb, solo_a, solo_b, por_col, sorted(set(cols(a)) ^ set(cols(b)))


# --- cubo
a, b = A / "indicadores/fact_indicador.parquet", B / "indicadores/fact_indicador.parquet"
na, nb, sa, sb, pc, cx = distintos(a, b, CLAVE, NOMBRES_CUBO)
print("## fact_indicador (cubo)")
print(f"filas antes {na}, después {nb}; solo antes {sa}; solo después {sb}; columnas distintas en el esquema: {cx}")
print(f"diferencias en columnas que no son nombre: {pc or 0}")
k = " AND ".join(f"x.{c} IS NOT DISTINCT FROM y.{c}" for c in CLAVE)
cambios = con.execute(f"""SELECT DISTINCT x.territorio_id, x.territorio_nombre AS antes, y.territorio_nombre AS despues
    FROM '{a}' x JOIN '{b}' y ON {k} WHERE x.territorio_nombre IS DISTINCT FROM y.territorio_nombre ORDER BY 1""").fetchall()
print(f"nombres de territorio cambiados en el cubo: {len(cambios)}")
for t in cambios:
    print(f"  {t[0]}: {t[1]} → {t[2]}")

# --- gasto
a, b = A / "dimensiones/fact_gasto_territorial.parquet", B / "dimensiones/fact_gasto_territorial.parquet"
q = """SELECT anio, nivel_atribucion, departamento_atribucion, metodo_ubicacion_cui, count(*) n,
       round(sum(pia), 2) pia, round(sum(pim), 2) pim, round(sum(devengado), 2) dev FROM '{}' GROUP BY ALL"""
g = con.execute(f"""SELECT coalesce(x.anio, y.anio), coalesce(x.nivel_atribucion, y.nivel_atribucion),
    coalesce(x.departamento_atribucion, y.departamento_atribucion), coalesce(x.metodo_ubicacion_cui, y.metodo_ubicacion_cui),
    x.n, y.n, x.pim, y.pim, x.dev, y.dev
    FROM ({q.format(a)}) x FULL JOIN ({q.format(b)}) y
    ON x.anio = y.anio AND x.nivel_atribucion IS NOT DISTINCT FROM y.nivel_atribucion
       AND x.departamento_atribucion IS NOT DISTINCT FROM y.departamento_atribucion
       AND x.metodo_ubicacion_cui IS NOT DISTINCT FROM y.metodo_ubicacion_cui
    WHERE x.n IS DISTINCT FROM y.n OR x.pia IS DISTINCT FROM y.pia OR x.pim IS DISTINCT FROM y.pim
       OR x.dev IS DISTINCT FROM y.dev""").fetchall()
grupos = con.execute(f"SELECT count(*) FROM ({q.format(b)})").fetchone()[0]
print("\n## fact_gasto_territorial: totales por año, nivel, departamento y método de ubicación")
print(f"grupos comparados: {grupos}; grupos con diferencias: {len(g)}")
for r in g[:50]:
    print("  ", r)

# --- dim_ubigeo_historico
a, b = A / "dimensiones/dim_ubigeo_historico.parquet", B / "dimensiones/dim_ubigeo_historico.parquet"
PERMITIDAS = {"nombre", "nombre_mostrado", "nombre_normalizado", "nombres_alternos", "fuente_nombre_mostrado", "version_tabla"}
na, nb, sa, sb, pc, cx = distintos(a, b, ["id_version"], set())
print("\n## dim_ubigeo_historico")
print(f"filas antes {na}, después {nb}; solo antes {sa}; solo después {sb}; columnas distintas en el esquema: {cx}")
print(f"filas distintas por columna: {pc}")
fuera = {c: n for c, n in pc.items() if c not in PERMITIDAS}
print(f"columnas que no debían cambiar y cambiaron: {fuera or 'ninguna'}")
esperados = {c["ubigeo"] for c in yaml.safe_load((R / "codigo/capa0/datos/nombres_mostrados.yaml").read_text())["correcciones"]}
cond = " OR ".join(f"x.{c} IS DISTINCT FROM y.{c}" for c in PERMITIDAS - {"version_tabla"} if c in pc)
cambiados = set()
if cond:
    cambiados = {r[0] for r in con.execute(
        f"SELECT DISTINCT x.ubigeo_inei FROM '{a}' x JOIN '{b}' y ON x.id_version = y.id_version WHERE {cond}").fetchall()}
print(f"ubigeos con nombre cambiado: {len(cambiados)}; en nombres_mostrados.yaml: {len(esperados)}")
print(f"cambiados fuera del YAML: {sorted(cambiados - esperados) or 'ninguno'}")
print(f"del YAML sin cambio (ya estaban bien escritos en la fuente): {sorted(esperados - cambiados) or 'ninguno'}")
for r in con.execute(f"""SELECT x.ubigeo_inei, x.nombre_mostrado, y.nombre_mostrado FROM '{a}' x JOIN '{b}' y
        ON x.id_version = y.id_version WHERE x.nombre_mostrado IS DISTINCT FROM y.nombre_mostrado ORDER BY 1""").fetchall():
    print(f"  {r[0]}: {r[1]} → {r[2]}")
