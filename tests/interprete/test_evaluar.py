"""S2-09 — El corredor de la evaluación en vivo (tests/interprete/evaluar.py), sin red: comparador de S2-02 §4, métricas y
reporte, con el cliente en modo «reproducir»."""
import sys

import pytest
import yaml

from pap.config import Rutas
from pap.interprete import llm as L
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL

RAIZ = Rutas(RAIZ_REAL).raiz
sys.path.insert(0, str(RAIZ / "tests" / "interprete"))
import evaluar as E  # noqa: E402

PAR = yaml.safe_load((RAIZ / "curados/motor/parametros_motor.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def motor():
    assert (RAIZ / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    return Motor(cargar_contexto(RAIZ))


def test_misma_consulta_compara_lugares_por_lo_que_resuelve(motor):
    esperada = {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "región Apurímac"}}
    assert E.misma_consulta(motor, esperada, {"tema": "anemia", "territorio": {"texto": "Apurímac"}, "periodo": {"tipo": "ultimo"}},
                            PAR) == []                                     # intención y periodo por defecto; el mismo departamento
    assert E.misma_consulta(motor, esperada, {"tema": "anemia", "territorio": {"texto": "Puno"}}, PAR) == ["territorio"]
    assert E.misma_consulta(motor, esperada, {"intencion": "evolucion", "tema": "anemia", "territorio": {"texto": "Apurímac"}},
                            PAR) == ["intencion"]
    h = {"intencion": "evolucion", "tema": "anemia", "territorio": {"texto": "Huancavelica"}}
    assert E.misma_consulta(motor, h, h, PAR) == []                        # la misma aclaración de homónimo


def test_juzgar_resultado_y_motivo(motor):
    e = {"esperado": {"resultado": "aclaracion", "motivo": "varias_preguntas"}}
    r = {"interpretacion": {"resultado": "aclaracion"}, "aclaracion": {"motivo": "interprete_varias_preguntas"}}
    assert E.juzgar(motor, e, r, PAR) == (True, "")
    assert E.juzgar(motor, {"esperado": {"resultado": "otro_idioma"}}, r, PAR)[0] is False
    assert E.juzgar(motor, {"esperado": {"resultado_en": ["aclaracion", "consulta"]}}, r, PAR)[0] is True


def test_evaluar_q2_grabada_y_reporte(motor):
    ev = E.evaluar(RAIZ, ["q2"], cliente=L.Cliente(RAIZ, modo="reproducir"), motor=motor)
    [f] = ev["filas"]
    assert f["ok"] and f["sin_ancla"] == [] and f["numeros"] == [] and ev["llamadas_en_vivo"] == 0 and ev["gastado_usd"] == 0
    m = E.metricas(ev)
    assert m["valores_sin_ancla"]["cumple"] and m["numeros_fuera_de_marcadores"]["cumple"] and not m["cumple_todo"]
    texto = E.reporte(ev, m, "prueba")
    assert "| q2 |" not in texto and "claude-sonnet-5-5" in texto and "Cumple todos los umbrales: no" in texto


def test_el_tope_corta_la_evaluacion(motor, tmp_path):
    c = L.Cliente(RAIZ, modo="reproducir", tope_usd=0.0)
    ev = E.evaluar(RAIZ, ["q2", "q3"], cliente=c, motor=motor)
    assert ev["cortado"] == "tope_por_corrida" and ev["filas"] == [] and not E.metricas(ev)["cumple_todo"]
