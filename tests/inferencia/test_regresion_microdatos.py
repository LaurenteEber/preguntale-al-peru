"""M0-04, en el Mac: los Parquet de la ENDES 2024 contra los miembros de los ZIP registrados.

Necesitan los ZIP del almacén de crudos y `pap microdatos convertir --encuesta ENDES --anio 2024` ya corrido: si faltan,
FALLAN (no se saltan; un salto daría un falso verde)."""
import json
import tempfile
from pathlib import Path

import duckdb
import pyreadstat
import pytest

from pap.config import Rutas
from pap.inferencia import almacen
from pap.inferencia.almacen import Parametros, huella_contenido_v1
from pap.zip_seguro import abrir_zip_seguro

from conftest import RAIZ_REAL

pytestmark = [pytest.mark.regresion_microdatos, pytest.mark.solo_mac]

SALIDA = RAIZ_REAL / "biblioteca" / "microdatos" / "ENDES" / "2024"


@pytest.fixture(scope="module")
def manifiesto():
    ruta = SALIDA / "manifiesto.json"
    assert ruta.exists(), "falta biblioteca/microdatos/ENDES/2024/manifiesto.json: corre `pap microdatos convertir --encuesta ENDES --anio 2024`"
    return json.loads(ruta.read_text(encoding="utf-8"))


def test_estan_todos_los_archivos_de_2024(manifiesto):
    esperados = 34       # los DTA de los 13 ZIP registrados en M0-02
    assert len(manifiesto["archivos"]) == esperados
    for nombre, e in manifiesto["archivos"].items():
        assert (SALIDA / e["parquet"]).exists(), nombre
        assert len(e["huella_contenido_v1"]) == 64 and len(e["huella_datos"]) == 64 and e["filas"] > 0


def test_las_filas_de_cada_parquet_son_las_del_miembro_del_zip(manifiesto):
    rutas = Rutas(RAIZ_REAL)
    for nombre, e in manifiesto["archivos"].items():
        o = e["origen"]
        ins = almacen._insumo(rutas, "INEI-ENDES", o["recurso"])
        assert ins.hash == "sha256:" + o["zip_sha256"], f"{nombre}: el ZIP registrado cambió"
        with abrir_zip_seguro(ins.ruta) as z, tempfile.TemporaryDirectory() as d:
            local = Path(d) / "m.dta"
            with open(local, "wb") as f:
                z.copiar(o["miembro"], f)
            _, meta = pyreadstat.read_dta(str(local), metadataonly=True, user_missing=True)
        n = duckdb.sql(f"SELECT count(*) FROM read_parquet('{SALIDA / e['parquet']}')").fetchone()[0]
        assert n == meta.number_rows == e["filas"], nombre


def test_ubigeo_y_hhid_conservan_su_ancho(manifiesto):
    con_hhid = 0
    for nombre, e in manifiesto["archivos"].items():
        cols = {c["nombre"] for c in e["columnas"]}
        for col, ancho in (("HHID", 9), ("UBIGEO", 6), ("CASEID", 12)):
            if col not in cols:
                continue
            mn, mx, nulos = duckdb.sql(f"SELECT min(length({col})), max(length({col})), count(*) FILTER (WHERE {col} IS NULL) "
                                       f"FROM read_parquet('{SALIDA / e['parquet']}')").fetchone()
            assert (mn, mx, nulos) == (ancho, ancho, 0), f"{nombre}.{col}"
            con_hhid += col == "HHID"
    assert con_hhid == len(manifiesto["archivos"])       # todos traen HHID (propio o derivado de CASEID)


def test_nombre_con_enie_no_se_estropea(manifiesto):
    p = SALIDA / manifiesto["archivos"]["RECH0"]["parquet"]
    nombres = {r[0] for r in duckdb.sql(f"SELECT DISTINCT NOMCCPP FROM read_parquet('{p}')").fetchall()}
    assert "BREÑA" in nombres
    assert not any("Ã" in n for n in nombres if n)


def test_la_huella_de_contenido_del_manifiesto_se_reproduce(manifiesto):
    for nombre in ("RECH0", "REC44", "PS_VL"):
        e = manifiesto["archivos"][nombre]
        assert huella_contenido_v1(SALIDA / e["parquet"]) == e["huella_contenido_v1"]


def test_criterios_de_memoria_y_tiempo_de_m0_04(manifiesto):
    p = Parametros.desde_yaml()
    for nombre, e in manifiesto["archivos"].items():
        assert e["rss_max_mb"] < p.criterio_rss_max_mb, nombre
        assert e["segundos_huella"] < p.criterio_huella_s, nombre
