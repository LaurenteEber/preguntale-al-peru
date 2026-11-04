"""RP-01: coherencia entre sprints de la capa 0 ya construida (huellas de manifiestos = archivos; los insumos-tabla
de un sprint son exactamente las tablas que registró el sprint productor; grupos de población ⊂ territorio)."""
import json

import duckdb
import pytest

from pap.capa0 import insumos
from conftest import RAIZ_REAL

DIM = RAIZ_REAL / "biblioteca" / "dimensiones"


def _manifiestos():
    ms = {p.stem.replace("manifiesto_", ""): json.loads(p.read_text(encoding="utf-8")) for p in DIM.glob("manifiesto_*.json")}
    if not ms:
        pytest.skip("capa 0 no construida")
    return ms


def test_huellas_de_manifiestos_coinciden_con_los_parquet():
    malos = []
    for sprint, m in _manifiestos().items():
        for nombre, reg in m["tablas"].items():
            ruta = DIM / reg["archivo"]
            if not ruta.exists() or insumos._sha256(ruta) != reg["hash"]:
                malos.append((sprint, nombre))
    assert malos == []


def test_insumos_tabla_coinciden_con_el_productor():
    ms = _manifiestos()
    # los productores pueden estar fuera de dimensiones/ (S4 escribe en estandarizada/): se leen todas las carpetas
    todos = [json.loads(p.read_text(encoding="utf-8")) for c in {DIM, *(RAIZ_REAL / "biblioteca" / "estandarizada").glob("*")}
             for p in c.glob("manifiesto_*.json")]
    producidas = {n: r["hash"] for m in todos for n, r in m["tablas"].items()}
    malos = [(s, i["recurso"]) for s, m in ms.items() for i in m["insumos"]
             if i["source_id"].startswith("CAPA0:") and producidas.get(i["recurso"]) != i["hash"]]
    assert malos == []


def test_grupos_de_poblacion_existen_en_territorio():
    if not (DIM / "fact_poblacion.parquet").exists():
        pytest.skip("población no construida")
    huerfanos = duckdb.sql(f"""
        SELECT DISTINCT ubigeo_inei FROM '{DIM / 'fact_poblacion.parquet'}' WHERE ubigeo_inei LIKE 'G-%'
        EXCEPT SELECT DISTINCT grupo_comparable_geo2017 FROM '{DIM / 'dim_ubigeo_historico.parquet'}'""").fetchall()
    assert huerfanos == []
