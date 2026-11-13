"""M1-03, revisión del auditor-agente: las cardinalidades declaradas en archivos_endes_2024.yaml, medidas contra los Parquet."""
from pathlib import Path

import duckdb
import pytest

RAIZ = Path(__file__).resolve().parents[2]
M = RAIZ / "biblioteca/microdatos/ENDES/2024"
pytestmark = [pytest.mark.regresion_microdatos, pytest.mark.solo_mac]


def _p(t: str) -> str:
    ruta = M / f"{t}.parquet"
    assert ruta.exists(), f"falta {ruta}"          # falla, no se salta
    return f"read_parquet('{ruta}')"


def test_rech23_es_1_a_1_con_rech0():
    c = duckdb.connect()
    assert c.sql(f"select count(*), count(distinct HHID) from {_p('RECH23')}").fetchone() == (37390, 37390)
    assert c.sql(f"select count(*) from {_p('RECH23')} a anti join {_p('RECH0')} b using (HHID)").fetchone()[0] == 0
    assert c.sql(f"select count(*) from {_p('RECH0')} a anti join {_p('RECH23')} b using (HHID)").fetchone()[0] == 0


@pytest.mark.parametrize("tabla", ["REC42", "RE223132", "RE516171", "RE758081"])
def test_hermanas_de_rec0111_son_1_a_0_o_1(tabla):
    c = duckdb.connect()
    assert c.sql(f"select count(*), count(distinct CASEID) from {_p(tabla)}").fetchone() == (34252, 34252)
    assert c.sql(f"select count(*) from {_p(tabla)} a anti join {_p('REC0111')} b using (CASEID)").fetchone()[0] == 0
