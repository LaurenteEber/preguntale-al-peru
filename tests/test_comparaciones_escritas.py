"""S3-01b (punto 9): toda comparación escrita («más alta», «más baja», «mayor», «menor») coincide con las cifras de la misma
respuesta (`tests/matriz/comprobar.py`, `comparaciones`). Los dos casos reales son los de H-A (Cajamarca: la forma anterior da
una cifra más baja en 2025) y H-F (Lurigancho: el SIEN es más alto que la ENDES). Necesitan el cubo: si falta, fallan."""
from __future__ import annotations

import pytest

from matriz import comprobar as C
from matriz.correr import cargar
from pap.motor.preguntar import preguntar_minima


@pytest.fixture(scope="module")
def motor():
    return cargar()[0]


def _responder(motor, intencion, territorio, periodo):
    r = preguntar_minima(motor, {"intencion": intencion, "tema": "anemia", "territorio": territorio, "periodo": periodo,
                                 "pregunta_original": "prueba de comparaciones", "idioma": "es"})
    assert r["tipo"] == "respuesta"
    return r


def test_h_a_cajamarca_no_afirma_que_la_forma_anterior_da_mas(motor):
    r = _responder(motor, "evolucion", {"texto": "departamento de Cajamarca"}, {"tipo": "serie"})
    assert C.comparaciones(r) == []


def test_h_f_lurigancho_no_afirma_que_el_sien_es_mas_bajo(motor):
    r = _responder(motor, "nivel_actual", {"ubigeo": "150118"}, {"tipo": "ultimo"})
    assert C.comparaciones(r) == []


def _respuesta(texto: str, cifras: dict) -> dict:
    """Una respuesta mínima con `texto` como respuesta corta: solo lo que lee `visible()`."""
    capa1 = {"respuesta_corta": texto, "confianza": {"texto": ""}, "ojo_al_leer": [], "cifra_clave": None}
    return {"tipo": "respuesta", "cifras": cifras,
            "capas": {"capa1": capa1, "capa2": {"mas_contexto": [], "avisos": [], "limites": []},
                      "capa3": {"para_citar": [], "glosario": []}}}


def _cifra(lugar, valor, anio=2025, indicador="endes_anemia_6_35m_oms2024", rol="principal"):
    return {"indicador_id": indicador, "territorio_id": lugar, "territorio_nombre": lugar, "anio": anio, "valor": valor, "rol": rol}


def test_detecta_mayor_en_al_reves():
    r = _respuesta("En 2025, la anemia fue mayor en Puno que en Cusco, con una diferencia clara.",
                   {"a": _cifra("Puno", 30.0), "b": _cifra("Cusco", 40.0)})
    assert [f["codigo"] for f in C.comparaciones(r)] == ["comparacion_contradice_cifras"]


def test_acepta_mayor_en_cuando_coincide():
    r = _respuesta("En 2025, la anemia fue mayor en Puno que en Cusco, con una diferencia clara.",
                   {"a": _cifra("Puno", 50.0), "b": _cifra("Cusco", 40.0)})
    assert C.comparaciones(r) == []


def test_acepta_mayor_en_con_nombres_con_rotulo():
    """S3-11: la cifra se llama «Lima Región (Lima Provincias)» y el texto dice «Lima Región» (como `_lugar` de plantillas.py)."""
    r = _respuesta("En 2025, la anemia fue mayor en Lima Región que en Lima Metropolitana, con una diferencia clara.",
                   {"a": _cifra("Lima Región (Lima Provincias)", 32.2), "b": _cifra("Lima Metropolitana (provincia de Lima)", 25.3)})
    assert C.comparaciones(r) == []


def test_detecta_mayor_en_al_reves_con_nombres_con_rotulo():
    r = _respuesta("En 2025, la anemia fue mayor en Lima Metropolitana que en Lima Región, con una diferencia clara.",
                   {"a": _cifra("Lima Región (Lima Provincias)", 32.2), "b": _cifra("Lima Metropolitana (provincia de Lima)", 25.3)})
    assert [f["codigo"] for f in C.comparaciones(r)] == ["comparacion_contradice_cifras"]


def test_una_comparacion_desconocida_falla():
    r = _respuesta("La anemia es menor que antes.", {"a": _cifra("Puno", 50.0)})
    assert [f["codigo"] for f in C.comparaciones(r)] == ["comparacion_sin_comprobar"]


def test_frases_sin_comparacion_no_fallan():
    r = _respuesta("Niñas y niños menores de 5 años. Podemos decirte dónde es más alto.", {})
    assert C.comparaciones(r) == []
