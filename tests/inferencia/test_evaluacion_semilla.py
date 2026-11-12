"""M1-00 tarea 11: el conjunto semilla de evaluación (`tests/inferencia/evaluacion.yaml`, formato de M1-19 / diseño §23.2).

Valida la estructura del archivo, que cada cifra oficial sea la del CSV de doradas (con su cita) y que cada variable esperada exista en el
índice de variables de la ENDES 2024. El índice sale de `pap variables indexar --encuesta ENDES --anio 2024` (en el Mac): si falta, las
pruebas FALLAN (no se saltan; un salto daría un falso verde)."""
import csv
import re
from pathlib import Path

import duckdb
import pytest
import yaml

from conftest import RAIZ_REAL

pytestmark = [pytest.mark.regresion_microdatos, pytest.mark.solo_mac]

ARCHIVO = RAIZ_REAL / "tests" / "inferencia" / "evaluacion.yaml"
INDICE = RAIZ_REAL / "biblioteca" / "variables" / "variables.parquet"
DORADAS = RAIZ_REAL / "curados" / "capa0" / "cifras_doradas.csv"

# Estratos de M1-19 / §23.2 + «vocabulario popular» (M1-09b) + «directa» (pregunta sin dificultad especial; supuesto M1-00-s4).
ESTRATOS = {"pares casi iguales", "universo con convención", "respuesta múltiple", "temas nuevos", "sin insumos",
            "parecen no tener insumos", "ambiguas", "vocabulario popular", "directa"}
SALIDAS = {"respuesta", "aclaracion", "no_se_puede", "indeterminado"}
PARTICIONES = {"desarrollo", "no_vista"}
REQUERIDOS = {"id", "pregunta", "estrato", "salida_esperada", "tabla_esperada", "variables_esperadas", "territorio", "periodo",
              "plan_esperado", "cifra_oficial", "particion", "autor", "estado"}
CAMPOS_CIFRA = {"id_cifra", "valor", "unidad", "documento", "cuadro_pagina", "url", "fuente_en_proyecto"}


@pytest.fixture(scope="module")
def preguntas():
    assert ARCHIVO.exists(), "falta tests/inferencia/evaluacion.yaml (conjunto semilla, M1-00 tarea 11)"
    datos = yaml.safe_load(ARCHIVO.read_text(encoding="utf-8"))
    return datos["preguntas"]


@pytest.fixture(scope="module")
def var_ids_2024():
    assert INDICE.exists(), "falta biblioteca/variables/variables.parquet: corre `pap variables indexar --encuesta ENDES --anio 2024`"
    filas = duckdb.connect().execute("select var_id from read_parquet(?) where anio = 2024", [str(INDICE)]).fetchall()
    return {f[0] for f in filas}


def test_estructura(preguntas):
    assert len(preguntas) >= 25
    ids = [p["id"] for p in preguntas]
    assert len(ids) == len(set(ids)), "ids repetidos"
    for p in preguntas:
        assert REQUERIDOS <= set(p), f"{p.get('id')}: faltan {REQUERIDOS - set(p)}"
        assert re.fullmatch(r"EV-\d{3}", p["id"]), p["id"]
        assert p["pregunta"].strip().startswith("¿") and p["pregunta"].strip().endswith("?"), p["id"]
        assert p["estrato"] in ESTRATOS, f"{p['id']}: estrato {p['estrato']!r}"
        assert p["salida_esperada"] in SALIDAS, p["id"]
        assert p["particion"] in PARTICIONES, p["id"]
        assert p["autor"] == "agente" and p["estado"] == "propuesto", p["id"]
        assert isinstance(p["variables_esperadas"], list), p["id"]
        if p["salida_esperada"] == "respuesta":
            assert p["variables_esperadas"] and p["tabla_esperada"], f"{p['id']}: una respuesta necesita variable y tabla"
        if p["salida_esperada"] in ("respuesta", "aclaracion") and p["variables_esperadas"]:
            assert any(f"·{p['tabla_esperada']}·" in v for v in p["variables_esperadas"]), f"{p['id']}: la tabla esperada no aparece en sus variables"


def test_cobertura_de_estratos_y_particion(preguntas):
    estratos = {p["estrato"] for p in preguntas}
    assert {"vocabulario popular", "pares casi iguales"} <= estratos
    assert len(estratos) >= 7
    no_vista = [p for p in preguntas if p["particion"] == "no_vista"]
    proporcion = len(no_vista) / len(preguntas)
    assert 0.25 <= proporcion <= 0.35, f"la partición no vista debe rondar el 30 % (hay {proporcion:.0%})"


def test_variables_existen_en_el_indice_2024(preguntas, var_ids_2024):
    faltan = [(p["id"], v) for p in preguntas for v in p["variables_esperadas"] + p.get("variables_apoyo", []) if v not in var_ids_2024]
    assert not faltan, f"variables que no están en el índice 2024: {faltan}"


def test_cifras_oficiales_son_las_de_las_doradas(preguntas):
    doradas = {f["id_cifra"]: f for f in csv.DictReader(DORADAS.open(encoding="utf-8"))}
    con_cifra = [p for p in preguntas if p["cifra_oficial"] is not None]
    assert len(con_cifra) >= 8, "la semilla debe aprovechar las cifras oficiales del proyecto"
    for p in con_cifra:
        c = p["cifra_oficial"]
        assert set(c) == CAMPOS_CIFRA, p["id"]
        d = doradas[c["id_cifra"]]
        assert c["valor"] == float(d["valor_publicado"]), p["id"]
        assert (c["documento"], c["cuadro_pagina"], c["url"]) == (d["documento"], d["cuadro_pagina"], d["url"]), f"{p['id']}: cita distinta de la dorada"
        assert d["anio"] == str(p["periodo"]) and d["fuente_id"] == "INEI-ENDES", p["id"]
        assert c["documento"].startswith("INEI,") and c["url"].startswith("https://proyectos.inei.gob.pe/"), p["id"]
