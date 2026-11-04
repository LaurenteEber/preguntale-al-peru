import textwrap
from pathlib import Path

import os

import pytest

from pap.config import Rutas

RAIZ_REAL = Path(__file__).resolve().parents[1]

RECETA_CSV = """
id: PRUEBA-CSV
strategy: manual
publisher: INEI
dataset_title: Tabla de prueba por distrito
access_url: https://example.org/ficha
temporal: {inicio: 2020, fin: 2024}
spatial: {ambito: PE, nivel_minimo: distrito}
licenses: [{name: ODC-By-1.0}]
license_basis: declarada_en_pagina
manual:
  pasos: [Descargar de la ficha, Guardar en la bandeja]
espera:
  formato: [csv]
  bytes: [10, 1000000]
  columnas: [ubigeo, distrito, poblacion]
"""

RECETA_HTTP = """
id: PRUEBA-HTTP
strategy: http_file
publisher: MEF
dataset_title: Archivo HTTP de prueba
access_url: https://example.org/ficha
download_url: http://127.0.0.1:1/datos.csv
temporal: {inicio: 2024, fin: 2024}
spatial: {ambito: PE, nivel_minimo: distrito}
licenses: [{name: ODC-By-1.0}]
license_basis: declarada_en_pagina
espera:
  formato: [csv]
"""


@pytest.fixture
def proyecto(tmp_path, monkeypatch):
    (tmp_path / "biblioteca" / "cruda").mkdir(parents=True)
    recetas = tmp_path / "curados" / "recetas"
    recetas.mkdir(parents=True)
    (recetas / "PRUEBA-CSV.yaml").write_text(textwrap.dedent(RECETA_CSV), encoding="utf-8")
    (recetas / "PRUEBA-HTTP.yaml").write_text(textwrap.dedent(RECETA_HTTP), encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    monkeypatch.setenv("PAP_RAIZ", str(tmp_path))
    monkeypatch.setenv("PAP_RESPONSABLE", "Prueba")
    return Rutas(tmp_path)


@pytest.fixture
def csv_valido(tmp_path):
    p = tmp_path / "entrada" / "poblacion_distrital.csv"
    p.parent.mkdir()
    p.write_text("ubigeo;distrito;poblacion\n010101;Chachapoyas;32000\n150101;Lima;270000\n", encoding="utf-8")
    return p


# RP-09: con PAP_EXIGIR_INSUMOS=1, una prueba con datos reales que no encuentra sus insumos falla en vez de saltarse
# (para que la suite no termine en verde sin haber probado la capa 0).
if os.environ.get("PAP_EXIGIR_INSUMOS") == "1":
    _skip_original = pytest.skip

    def _skip_estricto(motivo="", **kw):
        pytest.fail(f"PAP_EXIGIR_INSUMOS=1 y la prueba se saltaría: {motivo}")
    pytest.skip = _skip_estricto
