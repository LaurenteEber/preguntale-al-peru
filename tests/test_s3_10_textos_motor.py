"""S3-10 (dueño, 7/11/2026; L14 de odd/tasks/slice-3.md): textos del motor tras la revisión de usuario.
W-10 (apertura u13 del gasto también en «¿sirvió?» y en cruce), H-04 (tarjeta de cobertura), H-05 (gasto del año comparado
en soles constantes), H-06 (glosario según el tema), H-07 (citas de cálculo propio con microdatos) y H-10 (la aclaración
no repite la palabra de nivel). Por la interfaz pública (`preguntar_minima`)."""
import sys
from pathlib import Path

import pytest
import yaml

sys.path[:0] = [str(Path(__file__).resolve().parent)]
from matriz.correr import cargar  # noqa: E402
from pap.motor.preguntar import preguntar_minima  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
BLOQUES = yaml.safe_load((RAIZ / "curados/motor/textos/bloques.yaml").read_text(encoding="utf-8"))["bloques"]
APERTURA = BLOQUES["gasto"]["nivel_actual"]["gasto"]["apertura"]
APERTURA_LIMA = BLOQUES["sesgo_sede_lima"]["nivel_actual"]["gasto_lima"]["apertura"]
MAX_PALABRAS = yaml.safe_load((RAIZ / "curados/motor/parametros_motor.yaml").read_text(encoding="utf-8"))["respuesta"]["capa1_palabras_max"]


@pytest.fixture(scope="module")
def motor():
    return cargar()[0]


def preg(motor, intencion, tema, lugar):
    return preguntar_minima(motor, {"intencion": intencion, "tema": tema, "territorio": {"texto": lugar},
                                    "periodo": {"tipo": "ultimo"}, "pregunta_original": "¿?", "idioma": "es"})


def _max_palabras():
    v = MAX_PALABRAS
    return v["valor"] if isinstance(v, dict) else v


# ---------------------------------------------------------------- W-10

@pytest.mark.parametrize("intencion", ["efecto", "cruce"])
@pytest.mark.parametrize("lugar, esperada", [
    ("departamento de Puno", APERTURA["regional"].format(lugar="Puno")),
    ("Lima Metropolitana", APERTURA_LIMA),
    ("Perú", APERTURA["nacional"]),
])
def test_w10_apertura_del_gasto_en_efecto_y_cruce(motor, intencion, lugar, esperada):
    r = preg(motor, intencion, "anemia", lugar)
    assert r["tipo"] == "respuesta"
    c1 = r["capas"]["capa1"]
    corta = c1["respuesta_corta"]
    assert esperada in corta
    assert corta.index(esperada) > 0                         # «No se puede» / la cifra clave del cruce va primero
    assert c1["palabras"] <= _max_palabras()


@pytest.mark.parametrize("intencion", ["efecto", "cruce"])
@pytest.mark.parametrize("lugar", ["San Juan de Lurigancho", "provincia de Puno"])
def test_w10_sin_apertura_en_provincia_y_distrito(motor, intencion, lugar):
    """Dueño, 7/11/2026: en lo local la frase de la cifra ya dice qué cubre y la apertura pasaría el tope de R-04."""
    r = preg(motor, intencion, "anemia", lugar)
    c1 = r["capas"]["capa1"]
    assert "Esta cifra no es solo de anemia" not in c1["respuesta_corta"]
    assert "solo de la municipalidad y de obras ubicadas" in c1["cifra_clave"]["texto"]


@pytest.mark.parametrize("intencion", ["efecto", "cruce"])
def test_w10_oferta_x22_en_avisos(motor, intencion):
    r = preg(motor, intencion, "anemia", "Puno")
    oferta = "Respondimos por el departamento de Puno."
    assert not any(x.startswith(oferta) for x in r["capas"]["capa1"]["ojo_al_leer"])
    assert r["capas"]["capa2"]["avisos"][0].startswith(oferta)
    assert r["capas"]["capa1"]["palabras"] <= _max_palabras()


# ---------------------------------------------------------------- H-04 y H-05

def _tarjetas(r):
    return r["capas"]["capa2"]["mas_contexto"]


def test_h04_tarjeta_de_cobertura_abre_con_cuantos_se_midieron(motor):
    r = preg(motor, "efecto", "gasto_publico", "departamento de Puno")
    t = [x for x in _tarjetas(r) if "39,8" in x["texto"]]
    assert len(t) == 1
    assert t[0]["titulo"].startswith("Cuántos se midieron la hemoglobina")
    assert "(de cada 100)" not in t[0]["titulo"] + t[0]["texto"]


def test_h05_gasto_del_anio_comparado_en_soles_constantes(motor):
    r = preg(motor, "efecto", "gasto_publico", "departamento de Puno")
    t = [x for x in _tarjetas(r) if "121,9" in x["texto"]]
    assert len(t) == 1
    assert t[0]["texto"].replace("\u202f", " ").startswith("Para comparar con la anemia de 2024: S/ 121,9 millones (en soles de 2025)")
    assert "el mismo año con el que se compara" not in t[0]["texto"]


# ---------------------------------------------------------------- H-06

def _glosario(r):
    return {g["termino"]: g["definicion"] for g in r["capas"]["capa3"]["glosario"]}


def test_h06_endes_en_desnutricion_no_habla_de_hemoglobina(motor):
    g = _glosario(preg(motor, "evolucion", "desnutricion_cronica", "Puno"))
    assert "ENDES" in g and "hemoglobina" not in g["ENDES"]


def test_h06_endes_en_anemia_sigue_hablando_de_hemoglobina(motor):
    g = _glosario(preg(motor, "nivel_actual", "anemia", "departamento de Puno"))
    assert "hemoglobina" in g["ENDES"]


def test_h06_gasto_sin_cambio_estadisticamente_claro(motor):
    g = _glosario(preg(motor, "evolucion", "gasto_publico", "Puno"))
    assert "cambio estadísticamente claro" not in g
    assert "soles constantes (ajustados por inflación)" in g


def test_h06_encuesta_conserva_cambio_estadisticamente_claro(motor):
    g = _glosario(preg(motor, "evolucion", "desnutricion_cronica", "Puno"))
    assert "cambio estadísticamente claro" in g


# ---------------------------------------------------------------- H-07

SIN_TABLA = "no hay tabla publicada con esta cifra; se calcula de microdatos"


def test_h07_cita_de_calculo_propio_con_microdatos(motor):
    r = preg(motor, "evolucion", "desnutricion_cronica", "Puno")
    citas = r["capas"]["capa3"]["citas"]
    propias = [c for c in citas if "cálculo propio con ENDES" in c["texto"]]
    assert propias and all(SIN_TABLA in c["texto"] for c in propias)
    assert all(c["url"] for c in propias)
    assert r["capas"]["capa3"]["para_citar"] == [c["texto"] for c in citas]


def test_h07_cita_oficial_no_cambia(motor):
    r = preg(motor, "nivel_actual", "anemia", "departamento de Puno")
    oficiales = [c for c in r["capas"]["capa3"]["citas"] if "Fuente: INEI" in c["texto"]]
    assert oficiales and not any(SIN_TABLA in c["texto"] for c in oficiales)


# ---------------------------------------------------------------- H-10

def test_h10_aclaracion_no_repite_la_palabra_de_nivel(motor):
    r = preg(motor, "nivel_actual", "anemia", "distrito Ayaviri")
    assert r["tipo"] == "aclaracion"
    assert r["aclaracion"]["pregunta"] == "Hay varios lugares llamados «Ayaviri». ¿Cuál quieres?"
