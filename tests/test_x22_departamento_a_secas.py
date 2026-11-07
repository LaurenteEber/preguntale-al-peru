"""X-22 (6/11/2026) y H-J (S3-01b): el nombre a secas de un departamento se responde como departamento y se ofrece la provincia
o el distrito como alternativa; Lima sigue con T-03; «Lurigancho Chosica» se reconoce. Por la interfaz pública
(`preguntar_minima`)."""
import sys
from pathlib import Path

import pytest

sys.path[:0] = [str(Path(__file__).resolve().parent)]
from matriz.correr import cargar  # noqa: E402
from pap.motor.preguntar import preguntar_minima  # noqa: E402


@pytest.fixture(scope="module")
def motor():
    return cargar()[0]


def consulta(lugar: str, intencion="nivel_actual", tema="anemia") -> dict:
    return {"intencion": intencion, "tema": tema, "territorio": {"texto": lugar}, "periodo": {"tipo": "ultimo"},
            "pregunta_original": f"¿Cuánta anemia hay en {lugar}?", "idioma": "es"}


def alternativas(res: dict) -> list[str]:
    return [a for a in res["capas"]["capa2"]["avisos"] if a.startswith("Respondimos por el departamento")]


@pytest.mark.parametrize("lugar, nombre", [("Puno", "Puno"), ("cusco", "Cusco"), ("Huancavelica", "Huancavelica")])
def test_departamento_a_secas_se_responde_y_ofrece_alternativa(motor, lugar, nombre):
    res = preguntar_minima(motor, consulta(lugar))
    assert res["tipo"] == "respuesta"
    assert res["plan"]["territorio"]["nivel"] == "departamento"
    assert alternativas(res) == [f"Respondimos por el departamento de {nombre}. Si buscabas la provincia o el distrito de {nombre}, "
                                 f"pregúntalo así: «provincia de {nombre}» o «distrito de {nombre}»."]
    assert not any("Respondimos por el departamento" in t for t in
                   [res["capas"]["capa1"]["respuesta_corta"], *res["capas"]["capa1"]["ojo_al_leer"]])


def test_la_alternativa_no_cambia_la_capa1(motor):
    con = preguntar_minima(motor, consulta("Puno"))
    sin = preguntar_minima(motor, consulta("departamento de Puno"))
    assert alternativas(sin) == []
    assert con["capas"]["capa1"] == sin["capas"]["capa1"]


def test_provincia_de_puno_sigue_siendo_provincia(motor):
    res = preguntar_minima(motor, consulta("provincia de Puno"))
    assert res["plan"]["territorio"]["nivel"] == "provincia"
    assert alternativas(res) == []


def test_distrito_de_puno_sigue_siendo_distrito(motor):
    res = preguntar_minima(motor, consulta("distrito de Puno"), elegir=None)
    assert res["tipo"] != "aclaracion" or res["aclaracion"]["motivo"] == "homonimo_mismo_nivel"
    if res["tipo"] == "respuesta":
        assert res["plan"]["territorio"]["nivel"] == "distrito"
    assert alternativas(res) == []


def test_lima_a_secas_sigue_con_t03(motor):
    res = preguntar_minima(motor, consulta("Lima"))
    assert res["tipo"] == "aclaracion" and res["aclaracion"]["motivo"] == "lima_a_secas"


def test_homonimo_del_mismo_nivel_sigue_aclarando(motor):
    res = preguntar_minima(motor, consulta("San Pedro"))
    assert res["tipo"] == "aclaracion" and res["aclaracion"]["motivo"] in ("homonimo_mismo_nivel", "homonimo_niveles",
                                                                          "demasiadas_opciones")


@pytest.mark.parametrize("lugar", ["Lurigancho Chosica", "Lurigancho-Chosica", "lurigancho chosica"])
def test_alias_lurigancho_chosica(motor, lugar):
    res = preguntar_minima(motor, consulta(lugar))
    assert res["tipo"] != "aclaracion", res.get("texto")
    assert res["plan"]["territorio"]["id"] == "150118"
