"""Acceso de solo lectura a la biblioteca para el motor.

El gasto se lee solo por las vistas de vistas_gasto.sql y la macro gasto_tema() de vistas_gasto_temas.sql, y cada
consulta pasa antes por guardia_gasto.verificar_consulta() (R-GASTO-05, R-GASTO-08b, G7). Las tablas se abren con
insumos.tabla(), que exige que el Parquet en disco sea el que registró su manifiesto.
"""
from __future__ import annotations

import duckdb

from ..capa0 import guardia_gasto, insumos
from ..config import Rutas

TABLAS_GASTO = ("fact_gasto_territorial", "dim_tema_gasto", "rel_concepto_grupo", "rel_concepto_nodo",
                "rel_programa_social_ejecutora", "rel_programa_social_linea_aparte")
SQL_GASTO = ("vistas_gasto.sql", "vistas_gasto_temas.sql")


def conectar_gasto(rutas: Rutas) -> tuple[duckdb.DuckDBPyConnection, list[insumos.Insumo]]:
    """Conexión en memoria con las tablas del gasto como vistas sobre sus Parquet y las vistas del motor creadas."""
    con = duckdb.connect()
    con.execute("SET threads TO 1")
    usados = []
    for t in TABLAS_GASTO:
        ins = insumos.tabla(rutas, t)
        con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_parquet('{ins.ruta}')")
        usados.append(ins)
    for s in SQL_GASTO:
        ins = insumos.curado(rutas, s)
        con.execute(ins.ruta.read_text(encoding="utf-8"))
        usados.append(ins)
    return con, usados


def consultar_gasto(con: duckdb.DuckDBPyConnection, sql: str, params: list | None = None):
    """Ejecuta una consulta de gasto solo si la guardia la acepta (lanza GuardiaGasto si no)."""
    guardia_gasto.verificar_consulta(sql)
    return con.execute(sql, params or []).df()
