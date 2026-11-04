"""S1-15 — Correcciones menores de la revisión (N-3, H7).

Si falta el cubo, las pruebas FALLAN (agents.md §8)."""
import yaml
import pytest

from pap.config import Rutas
from pap.motor import preguntar as P
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL

RAIZ = Rutas(RAIZ_REAL).raiz
NC = "nada sobre provincias o distritos concretos: la fuente solo da cifras con suficiente precisión para "


@pytest.fixture(scope="module")
def motor():
    assert (RAIZ / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    return Motor(cargar_contexto(RAIZ))


@pytest.fixture(scope="module")
def parametros():
    return yaml.safe_load((RAIZ / "curados" / "motor" / "parametros_motor.yaml").read_text(encoding="utf-8"))


def comparar(motor, a, b):
    return P.preguntar_minima(motor, {"intencion": "comparacion", "tema": "anemia", "territorio": {"texto": a},
                                      "comparar_con": {"texto": b}})


def limites(r):
    return next(x for x in r["capas"]["capa2"]["limites"] if x.startswith("No permite concluir"))


def infracciones(r, parametros):
    regs = parametros["respuesta"]["infracciones_corrector"]["valor"]
    return [x for x in r["resultados_respuesta"] if x["regla"] in regs and x["accion"] != "rotular"]


def test_n3_comparacion_nombra_los_dos_lugares(motor, parametros):
    r = comparar(motor, "Lima Metropolitana", "Lima Región")
    assert limites(r) == "No permite concluir: " + NC + "Lima Metropolitana y Lima Región."
    assert not infracciones(r, parametros)


def test_n3_niveles_distintos_un_no_permite_concluir_por_lugar(motor):
    r = comparar(motor, "Perú", "departamento de Puno")
    t = limites(r)
    assert t == "No permite concluir: " + NC + "todo el país. " + NC[0].upper() + NC[1:] + "el departamento."


def test_n3_fuera_de_una_comparacion_no_cambia(motor):
    r = P.preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Lima Metropolitana"}})
    assert limites(r) == "No permite concluir: " + NC + "Lima Metropolitana."


def test_h7_anio_solo_con_la_forma_anterior_ofrece_la_evolucion(motor, parametros):
    r = P.preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Perú"},
                                   "periodo": {"tipo": "anio", "anio": 2018}})
    assert r["tipo"] == "no_se_puede"
    c1 = r["capas"]["capa1"]
    assert c1["respuesta_corta"] == ("No hay datos de anemia de 2018 con la forma de medir actual. La cifra de 2018 solo existe "
                                     "con la forma de medir anterior, que se muestra al preguntar cómo cambió la anemia.")
    assert c1["lo_mas_cercano"]["texto"] == "Puedes preguntar cómo cambió la anemia en Perú hasta 2018."
    (alt,) = r["alternativas"]
    assert alt["tipo"] == "evolucion" and alt["consulta_minima"]["periodo"] == {"tipo": "serie", "hasta": 2018}
    evo = P.preguntar_minima(motor, alt["consulta_minima"])          # la evolución ofrecida sí responde (S1-13, A-H6)
    assert evo["tipo"] == "respuesta"
    assert not infracciones(r, parametros)


def test_h7_anio_sin_ninguna_serie(motor):
    r = P.preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Perú"},
                                   "periodo": {"tipo": "anio", "anio": 2010}})
    assert r["tipo"] == "no_se_puede"
    assert r["capas"]["capa1"]["respuesta_corta"] == "No hay datos de anemia de 2010."
    assert "forma de medir actual" not in r["capas"]["capa1"]["respuesta_corta"]
