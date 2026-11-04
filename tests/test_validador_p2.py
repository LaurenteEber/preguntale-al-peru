"""Piloto P2: validador de reglas (68 reglas del alcance; casos del analista independiente y de los implementadores)."""
import csv

import pytest

from pap.config import Rutas
from pap.motor.validador import REGISTRO, cargar, casos
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL


@pytest.fixture(scope="module")
def ctx():
    raiz = Rutas(RAIZ_REAL).raiz
    if not (raiz / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists():
        pytest.skip("cubo sin construir (pap calcular)")
    cargar()
    return cargar_contexto(raiz)


def _alcance(raiz):
    p = raiz / "reglas" / "alcance_piloto.csv"
    return [r["id"] for r in csv.DictReader(open(p, encoding="utf-8"))
            if r["necesaria_piloto"] in ("si", "solo_infraestructura")]


@pytest.mark.parametrize("carpeta", ["casos", "casos_implementador"])
def test_casos_pasan(ctx, carpeta):
    res = casos.correr(ctx, ctx.raiz / "tests" / "casos_validador" / carpeta)
    mal = [(r["id"], str(r.get("obtenido"))[:200]) for r in res if not r["ok"]]
    assert res and not mal, mal[:10]


def test_alcance_implementado_y_cubierto(ctx):
    alcance = _alcance(ctx.raiz)
    assert len(alcance) == 68
    res = casos.correr(ctx, ctx.raiz / "tests" / "casos_validador" / "casos")
    cob = casos.cobertura(res, alcance)
    sin_impl = [r for r, v in cob.items() if not v["implementada"]]
    sin_par = [r for r, v in cob.items() if not v["con_dispara"] or
               (not v["con_no_dispara"] and r != "R-CRUCES-10")]  # R-CRUCES-10: toda respuesta lleva semáforo (PR-36)
    assert not sin_impl and not sin_par, (sin_impl, sin_par)
    assert set(REGISTRO) >= set(alcance)
