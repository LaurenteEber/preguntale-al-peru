"""S1-13 — La evolución muestra los dos años que compara (H11 / AD-1, N-2, A-H6).

Si falta el cubo, las pruebas FALLAN (agents.md §8)."""
import pytest

from pap.config import Rutas
from pap.motor import preguntar as P
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL

VIGENTE, ANTERIOR = "endes_anemia_6_35m_oms2024", "endes_anemia_6_35m"


@pytest.fixture(scope="module")
def motor():
    r = Rutas(RAIZ_REAL).raiz
    assert (r / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    return Motor(cargar_contexto(r))


def evolucion(motor, tema="anemia", lugar="Perú", hasta=None, desde=None):
    e = {"intencion": "evolucion", "tema": tema, "territorio": {"texto": lugar}}
    if hasta or desde:
        e["periodo"] = {"tipo": "serie", **({"desde": desde} if desde else {}), **({"hasta": hasta} if hasta else {})}
    return P.preguntar_minima(motor, e)


def todo(r) -> str:
    c = r["capas"]
    return " ".join([c["capa1"]["respuesta_corta"], *c["capa1"]["ojo_al_leer"],
                     *(t["texto"] for t in c["capa2"]["mas_contexto"]), *c["capa3"]["para_citar"]])


def test_evolucion_anemia_muestra_2024_y_2025_con_la_forma_vigente(motor):
    """AD-1: «Más contexto» da la cifra vigente de 2024 junto a la de 2025, con su marcador y su cita."""
    r = evolucion(motor)
    v24 = [i for i, c in r["cifras"].items() if c["indicador_id"] == VIGENTE and c["anio"] == 2024]
    assert len(v24) == 1 and r["cifras"][v24[0]]["rol"] == "contexto"
    tarjeta = next(t for t in r["capas"]["capa2"]["mas_contexto"] if t["titulo"] == "2024 y 2025, con la forma de medir actual")
    assert tarjeta["texto"] == ("Con la forma de medir que usa hoy el Ministerio de Salud, la anemia fue 35,3 % en 2024 y "
                                "34,9 % en 2025.")
    assert "{{c:%s}}" % v24[0] in r["texto_con_marcadores"]
    assert any("(forma de medir vigente desde 2024), Perú, 2024." in x for x in r["capas"]["capa3"]["para_citar"])


def test_evolucion_generica_muestra_las_dos_cifras(motor):
    r = evolucion(motor, tema="pobreza_monetaria")
    t = r["capas"]["capa2"]["mas_contexto"][0]
    assert t["texto"] == "En Perú, la pobreza monetaria fue 27,6 % en 2024 y 25,7 % en 2025."
    assert t["etiqueta"] is None


def test_hasta_2024_responde_con_la_forma_anterior(motor):
    """A-H6 y N-2: la forma vigente solo tiene 2024 → serie de la anterior 2015–2024; la vigente de 2024 va en «Más
    contexto» con su cita; el «Ojo al leer» la nombra; nada se llama «la más reciente»."""
    r = evolucion(motor, hasta=2024)
    assert r["tipo"] == "respuesta"
    prin = [c for c in r["cifras"].values() if c["rol"] == "principal"]
    assert [(c["indicador_id"], c["anio"], c["comparacion"]["anio"]) for c in prin] == [(ANTERIOR, 2024, 2015)]
    ctx = {(c["indicador_id"], c["anio"]) for c in r["cifras"].values() if c["rol"] == "contexto"}
    assert ctx == {(ANTERIOR, 2015), (VIGENTE, 2024)}
    c1 = r["capas"]["capa1"]
    assert c1["respuesta_corta"].startswith("Entre 2015 y 2024, la anemia")
    assert "Con la forma de medir actual solo hay datos desde 2024. Esta serie usa la anterior, que no se compara con la de hoy." in c1["ojo_al_leer"]
    assert any("(forma de medir vigente desde 2024), Perú, 2024." in x for x in r["capas"]["capa3"]["para_citar"])
    assert "más reciente" not in todo(r)


def test_hasta_2018_responde_con_la_forma_anterior_sin_la_vigente(motor):
    r = evolucion(motor, hasta=2018)
    assert r["tipo"] == "respuesta"
    assert {(c["indicador_id"], c["anio"], c["rol"]) for c in r["cifras"].values()} == {(ANTERIOR, 2018, "principal"),
                                                                                       (ANTERIOR, 2015, "contexto")}
    assert "Con la forma de medir actual solo hay datos desde 2024. Esta serie usa la anterior, que no se compara con la de hoy." in \
        r["capas"]["capa1"]["ojo_al_leer"]


def test_sin_dos_anios_en_ninguna_forma_sigue_el_no_se_puede(motor):
    r = evolucion(motor, desde=2015, hasta=2015)
    assert r["tipo"] == "no_se_puede"


def test_la_mas_reciente_solo_para_el_ultimo_anio(motor):
    """N-2: con el periodo terminando antes del último año, el «no se puede» dice «hasta {año}»."""
    r = evolucion(motor, tema="pobreza_monetaria", hasta=2024)
    assert r["tipo"] == "no_se_puede"
    cercano = r["capas"]["capa1"]["lo_mas_cercano"]["texto"]
    assert cercano.startswith("Sí tenemos la cifra de 2024 para Perú, con datos hasta 2024.")
    assert "más reciente" not in cercano
