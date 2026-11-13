"""M1-04 sobre los PDF reales de la ENDES 2024 (necesita el almacén y `pap cuestionarios extraer`): solo en el Mac del dueño.
Falla (no se salta) si faltan los Parquet: un salto daría un falso verde (AGENTS.md §8)."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from pap.config import Rutas
from pap.inferencia import cuestionarios as c
from pap.inferencia import cuestionarios_medicion as m

pytestmark = pytest.mark.solo_mac
RAIZ = Rutas(Path(__file__).resolve().parents[2])


@pytest.fixture(scope="module")
def datos():
    d = c.carpeta_cuestionarios(RAIZ)
    qs = c.leer_cuestionarios(d)
    vs, cuests = c.leer_diccionarios(d)
    return qs, vs, cuests


def test_los_tres_cuestionarios_traen_todas_sus_secciones(datos):
    qs, _, _ = datos
    secciones = {cu: Counter(q.seccion[:12] for q in qs if q.cuestionario == cu and q.tipo == "pregunta") for cu in c.CUESTIONARIOS}
    assert sum(secciones["individual"].values()) >= 450 and len([s for s in secciones["individual"] if s.startswith("SECCIÓN")]) >= 11
    assert sum(secciones["salud"].values()) >= 170 and len([s for s in secciones["salud"] if s.startswith("SECCIÓN")]) >= 9
    assert sum(secciones["hogar"].values()) >= 60


def test_los_diccionarios_cubren_las_34_tablas_y_casi_todo_el_indice(datos):
    _, vs, cuests = datos
    assert len({v.tabla for v in vs}) == 34 and len(vs) >= 2800
    assert cuests["RECH6"] == ["hogar", "individual"] and cuests["CSALUD01"] == ["salud"]


def test_la_hipotesis_de_tecnologias_6_se_confirma_en_las_tres_tablas(datos):
    """Sin LLM, el diccionario y las expresiones regulares no vinculan casi nada en RECH6, REC43 y REC0111 (informe m1-04_vinculos.md)."""
    qs, vs, cuests = datos
    vin = {(v.tabla, v.codigo): v for v in c.vincular_sin_llm(vs, qs, cuests)}
    for f in m.medir(vs, vin, list(m.TABLAS_DE_LA_MEDICION)):
        assert f.pct_sin_llm < 5 and f.pendientes > 0.5 * f.total, f
