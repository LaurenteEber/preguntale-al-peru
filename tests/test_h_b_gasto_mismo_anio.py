"""S3-01b punto 2 (H-B, dueño, 6/11/2026): en Q3 la tarjeta del gasto de 2024 va en soles de 2025 (R-GASTO-12, X-03), con el
monto nominal en la cita; no queda junto a la de 2025 cada una en soles de su año. Si falta el cubo, la prueba FALLA."""
import pytest

from pap.config import Rutas
from pap.motor import preguntar as P
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL

RAIZ = Rutas(RAIZ_REAL).raiz


@pytest.fixture(scope="module")
def motor():
    assert (RAIZ / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    return Motor(cargar_contexto(RAIZ))


def test_gasto_2024_de_q3_va_en_soles_de_2025_y_la_cita_trae_el_nominal(motor):
    r = P.preguntar_minima(motor, {"intencion": "efecto", "tema": "gasto_publico",
                                   "territorio": {"texto": "Lima Metropolitana"}, "periodo": {"tipo": "ultimo"}})
    assert r["tipo"] == "respuesta"
    c24 = next(c for c in r["cifras"].values() if c["indicador_id"] == "gasto_ex_pan" and int(c["anio"]) == 2024)
    assert c24["medida"] == "devengado_constante" and c24["precios"] == "constantes"
    nominal = c24["devengado"]
    assert c24["valor"] == pytest.approx(nominal * {int(k): v for k, v in c24["factores_deflactor"].items()}[2024]) and c24["valor"] > nominal
    t24 = next(t for t in r["capas"]["capa2"]["mas_contexto"] if t["titulo"].startswith("Gasto en ") and t["titulo"].endswith("en 2024"))
    assert "S/ 264,6 millones" in t24["texto"].replace("\u202f", " ") and "260,7" not in t24["texto"]
    citas = " ".join(r["capas"]["capa3"]["para_citar"]).replace("\u202f", " ")
    assert "en soles de 2025 (monto registrado en 2024: S/ 260,7 millones" in citas
