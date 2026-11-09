"""M0-09: `svy` (el adaptador) frente a R `survey` sobre el microdato sintético. Esto cierra la política de versiones de M0-03:
mientras `svy` 0.35.0 coincida con los esperados de R, subir `svy` solo exige regenerar los esperados y volver a correr esta prueba.

R no corre aquí: `tests/esperados/r_survey_sintetico.csv` lo genera `just esperados-r` en el Mac (con `verificador_r/renv.lock`).
Si el archivo falta, estas pruebas **fallan** (no se saltan): sin él no se comparó nada."""
import csv
import math
import re
from pathlib import Path

import pytest

from conftest import RAIZ_REAL
from pap.inferencia.svy_adaptador import estimar_proporciones

from .sintetico_r import CASOS, marco

ESPERADOS = RAIZ_REAL / "tests" / "esperados" / "r_survey_sintetico.csv"
TOLERANCIA = 1e-9              # est, ee e IC; gl y n son exactos. Nunca se afloja para que una prueba pase (M0-09)
CAMPOS = ("est", "ee", "ic_inf", "ic_sup")


def leer_esperados(ruta: Path = ESPERADOS) -> tuple[dict[str, str], list[dict]]:
    """Cabecera `# clave: valor` y filas del CSV de R. Falla (no salta) si el archivo no está."""
    assert ruta.exists(), f"faltan los esperados de R: {ruta} (se generan con `just esperados-r` en el Mac; ver verificador_r/README.md)"
    cabecera, lineas = {}, []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        m = re.match(r"# (\w+): (.*)", linea)
        if m:
            cabecera[m.group(1)] = m.group(2)
        elif not linea.startswith("#"):
            lineas.append(linea)
    return cabecera, list(csv.DictReader(lineas))


def _num(x: str) -> float | None:
    return None if x == "NA" else float(x)


def comparar(ruta: Path = ESPERADOS) -> list[dict]:
    """Una fila por dominio: lo que dice R, lo que dice `svy` y la diferencia máxima de est, ee e IC (None si algún lado no tiene cifra)."""
    _, filas = leer_esperados(ruta)
    por_caso = {c["caso"]: c for c in CASOS}
    estimaciones = {}
    for caso in por_caso.values():
        for e in estimar_proporciones(marco(caso["anio"]), caso["por"], [tuple(d) for d in caso["dominios"]], anio=caso["anio"]):
            estimaciones[(caso["caso"], "|".join(e.dominio))] = e
    salida = []
    for f in filas:
        e = estimaciones[(f["caso"], f["dominio"])]
        svy = {"est": e.valor, "ee": e.ee, "ic_inf": e.ic_inf, "ic_sup": e.ic_sup}
        diffs = {k: (None if _num(f[k]) is None or svy[k] is None else abs(svy[k] - _num(f[k]))) for k in CAMPOS}
        salida.append({"caso": f["caso"], "dominio": f["dominio"], "n_r": int(f["n"]), "n_svy": e.n,
                       "gl_r": None if _num(f["gl"]) is None else int(float(f["gl"])), "gl_svy": e.gl,
                       "r": {k: _num(f[k]) for k in CAMPOS}, "svy": svy, "diff": diffs})
    return salida


def test_los_esperados_de_r_traen_las_versiones_en_la_cabecera_y_cubren_todos_los_casos():
    cabecera, filas = leer_esperados()
    for clave in ("r", "survey", "nanoparquet", "renv", "opciones", "ic", "md5_datos"):
        assert cabecera.get(clave), clave
    assert cabecera["survey"] and cabecera["renv"] == "1.3.1" and cabecera["nanoparquet"] == "0.5.2"
    assert "survey.lonely.psu=adjust" in cabecera["opciones"] and "survey.adjust.domain.lonely=FALSE" in cabecera["opciones"]
    esperados = {(c["caso"], "|".join(d)) for c in CASOS for d in c["dominios"]}
    assert {(f["caso"], f["dominio"]) for f in filas} == esperados and len(filas) == len(esperados)


def test_el_adaptador_coincide_con_r_en_n_y_gl_exactos_y_en_est_ee_e_ic_a_1e_9():
    mal = []
    for r in comparar():
        if r["n_r"] != r["n_svy"]:
            mal.append((r["caso"], r["dominio"], "n", r["n_r"], r["n_svy"]))
        if r["n_r"] and r["gl_r"] != r["gl_svy"]:
            mal.append((r["caso"], r["dominio"], "gl", r["gl_r"], r["gl_svy"]))
        for k in CAMPOS:
            a, b = r["r"][k], r["svy"][k]
            if (a is None) != (b is None):
                mal.append((r["caso"], r["dominio"], k, a, b))
            elif a is not None and not math.isclose(a, b, rel_tol=0, abs_tol=TOLERANCIA):
                mal.append((r["caso"], r["dominio"], k, a, b))
    assert not mal, mal


def test_los_casos_del_sintetico_incluyen_dominio_vacio_cero_y_dominio_con_pocos_casos():
    """No necesita los esperados: mira lo que el adaptador devuelve para los casos que se comparan con R."""
    caso = next(c for c in CASOS if c["caso"] == "terr_2024")
    e = {x.dominio[0]: x for x in estimar_proporciones(marco(caso["anio"]), caso["por"], [tuple(d) for d in caso["dominios"]], anio=caso["anio"])}
    assert e["T3"].n == 0 and e["T3"].valor is None          # dominio vacío: sale con n = 0
    assert e["T2"].valor == 0.0 and e["T2"].gl == 1          # p = 0 con gl > 0
    assert e["T5"].n < 25
