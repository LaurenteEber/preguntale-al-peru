"""S3-10, H-02 (parte A): la frase «Lo que sí se sabe es lo gastado …:» (efecto) y «Esto es lo que se gastó …:» (cruce)
nombran el lugar en todos los niveles que el motor puede producir; antes, en los ámbitos de Lima y el país quedaban
«lo gastado :». Por la interfaz pública (`preguntar_minima`)."""
import sys
from pathlib import Path

import pytest

sys.path[:0] = [str(Path(__file__).resolve().parent)]
from matriz.correr import cargar  # noqa: E402
from pap.motor.preguntar import preguntar_minima  # noqa: E402


@pytest.fixture(scope="module")
def motor():
    return cargar()[0]


def corta(motor, intencion, lugar) -> str:
    res = preguntar_minima(motor, {"intencion": intencion, "tema": "anemia", "territorio": {"texto": lugar},
                                   "periodo": {"tipo": "ultimo"}, "pregunta_original": f"¿Sirvió el gasto en {lugar}?", "idioma": "es"})
    assert res["tipo"] == "respuesta"
    return res["capas"]["capa1"]["respuesta_corta"]


@pytest.mark.parametrize("lugar, frase", [
    ("Lima Metropolitana", "lo gastado en Lima Metropolitana:"),
    ("Lima Región", "lo gastado en Lima Región:"),
    ("Callao", "lo gastado en Callao:"),
    ("Perú", "lo gastado en todo el país:"),
    ("departamento de Puno", "lo gastado en el departamento:"),
    ("provincia de Puno", "lo gastado en la provincia:"),
])
def test_efecto_nombra_el_lugar_de_lo_gastado(motor, lugar, frase):
    t = corta(motor, "efecto", lugar)
    assert frase in t and " :" not in t


@pytest.mark.parametrize("lugar, frase", [
    ("Lima Metropolitana", "lo que se gastó en Lima Metropolitana:"),
    ("Callao", "lo que se gastó en Callao:"),
    ("Perú", "lo que se gastó en todo el país:"),
    ("departamento de Puno", "lo que se gastó en el departamento:"),
])
def test_cruce_nombra_el_lugar_de_lo_gastado(motor, lugar, frase):
    t = corta(motor, "cruce", lugar)
    assert frase in t and " :" not in t
