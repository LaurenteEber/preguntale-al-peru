"""Índice DuckDB (derivado, se reconstruye siempre desde capturas y verificaciones)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import duckdb

from . import bitacora, capturas
from .config import Rutas

COLUMNAS_RECURSOS = {
    "captura": "VARCHAR", "source_id": "VARCHAR", "name": "VARCHAR", "hash": "VARCHAR",
    "bytes": "BIGINT", "format": "VARCHAR", "original_filename": "VARCHAR", "publisher": "VARCHAR",
    "dataset_title": "VARCHAR", "method": "VARCHAR", "retrieved_at": "VARCHAR", "issued": "VARCHAR",
    "source_version": "VARCHAR", "data_cutoff": "VARCHAR", "change": "VARCHAR", "previous": "VARCHAR",
    "validacion": "VARCHAR", "recipe": "VARCHAR", "metadatos": "JSON",
}
COLUMNAS_VERIF = {
    "fecha": "VARCHAR", "source_id": "VARCHAR", "accion": "VARCHAR", "resultado": "VARCHAR",
    "hash": "VARCHAR", "captura": "VARCHAR", "detalle": "VARCHAR",
}


def _filas_recursos(rutas: Rutas) -> list[dict]:
    filas = []
    for ruta, rec in capturas.recursos(rutas):
        filas.append({
            "captura": rutas.relativa(ruta.parent),
            **{k: rec.get(k) for k in COLUMNAS_RECURSOS if k not in ("captura", "validacion", "metadatos")},
            "validacion": (rec.get("validation") or {}).get("estado"),
            "metadatos": json.dumps(rec, ensure_ascii=False),
        })
    return filas


def _cargar(con, tabla: str, filas: list[dict], columnas: dict, tmp: Path) -> None:
    archivo = tmp / f"{tabla}.jsonl"
    with open(archivo, "w", encoding="utf-8") as f:
        for fila in filas:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")
    cols = ", ".join(f"'{k}': '{v}'" for k, v in columnas.items())
    if filas:
        con.execute(f"CREATE OR REPLACE TABLE {tabla} AS SELECT * FROM read_json('{archivo}', "
                    f"format='newline_delimited', columns={{{cols}}})")
    else:
        defs = ", ".join(f"{k} {v}" for k, v in columnas.items())
        con.execute(f"CREATE OR REPLACE TABLE {tabla} ({defs})")


def reconstruir(rutas: Rutas) -> Path:
    rutas.indice.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as d, duckdb.connect(str(rutas.indice)) as con:
        tmp = Path(d)
        con.execute("BEGIN")
        _cargar(con, "recursos", _filas_recursos(rutas), COLUMNAS_RECURSOS, tmp)
        _cargar(con, "verificaciones", bitacora.leer(rutas), COLUMNAS_VERIF, tmp)
        con.execute("""
            CREATE OR REPLACE VIEW fuentes_estado AS
            SELECT r.source_id,
                   count(*)                         AS recursos,
                   max(r.retrieved_at)              AS ultima_captura,
                   max(v.ultima)                    AS ultima_revision,
                   date_diff('day', CAST(substr(max(v.ultima), 1, 10) AS DATE), current_date) AS dias_sin_revisar
            FROM recursos r
            LEFT JOIN (SELECT source_id, max(fecha) AS ultima FROM verificaciones GROUP BY 1) v USING (source_id)
            GROUP BY 1 ORDER BY 1
        """)
        con.execute("COMMIT")
    return rutas.indice
