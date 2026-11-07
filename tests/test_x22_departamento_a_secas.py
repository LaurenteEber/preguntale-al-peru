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
    """H-01 (S3-10): la frase va en «Ojo al leer» (capa 1), no en «Avisos» (capa 2)."""
    return [a for a in res["capas"]["capa1"]["ojo_al_leer"] if a.startswith("Respondimos por el departamento")]


@pytest.mark.parametrize("lugar, nombre", [("Puno", "Puno"), ("cusco", "Cusco"), ("Huancavelica", "Huancavelica")])
def test_departamento_a_secas_se_responde_y_ofrece_alternativa(motor, lugar, nombre):
    res = preguntar_minima(motor, consulta(lugar))
    assert res["tipo"] == "respuesta"
    assert res["plan"]["territorio"]["nivel"] == "departamento"
    assert alternativas(res) == [f"Respondimos por el departamento de {nombre}. Si buscabas la provincia o el distrito de {nombre}, "
                                 f"pregúntalo así: «provincia de {nombre}» o «distrito de {nombre}»."]
    assert res["capas"]["capa1"]["ojo_al_leer"][0] == alternativas(res)[0]          # H-01: es lo PRIMERO que se lee en «Ojo al leer»
    assert not any("Respondimos por el departamento" in t for t in
                   [res["capas"]["capa1"]["respuesta_corta"], *res["capas"]["capa2"]["avisos"]])    # y no se repite en «Avisos»


def test_la_alternativa_solo_agrega_la_frase_al_inicio_de_ojo_al_leer(motor):
    con = preguntar_minima(motor, consulta("Puno"))
    sin = preguntar_minima(motor, consulta("departamento de Puno"))
    assert alternativas(sin) == []
    c, s = con["capas"]["capa1"], sin["capas"]["capa1"]
    assert c["ojo_al_leer"][1:] == s["ojo_al_leer"] and c["ojo_al_leer"][0] == alternativas(con)[0]
    assert {k: v for k, v in c.items() if k not in ("ojo_al_leer", "palabras")} == {k: v for k, v in s.items() if k not in ("ojo_al_leer", "palabras")}
    assert con["capas"]["capa2"] == sin["capas"]["capa2"]


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


def test_comparacion_con_dos_departamentos_a_secas_deja_las_ofertas_en_avisos(motor):
    """S3-10: en comparaciones la oferta sigue en «Avisos» (capa 2); la capa 1 no pasa del tope ni de 3 «Ojo al leer»."""
    from pap.motor import plantillas
    tope = plantillas.parametros(motor.ctx.raiz)["respuesta"]["capa1_palabras_max"]["valor"]
    c = {**consulta("Puno"), "intencion": "comparacion", "comparar_con": {"texto": "Cusco"}}
    res = preguntar_minima(motor, c)
    assert res["tipo"] == "respuesta"
    avisos = res["capas"]["capa2"]["avisos"]
    assert [a for a in avisos if a.startswith("Respondimos por el departamento")][:2] == avisos[:2] and len(avisos) >= 2
    assert alternativas(res) == []
    assert res["capas"]["capa1"]["palabras"] <= tope and len(res["capas"]["capa1"]["ojo_al_leer"]) <= 3


def test_evolucion_de_anemia_deja_la_oferta_en_avisos_y_la_capa1_dentro_del_tope(motor):
    """S3-10: en evolución (Q1) con «Huancavelica» a secas la oferta va en «Avisos»; en «Ojo al leer» la capa 1 pasaba de 125 palabras."""
    from pap.motor import plantillas
    tope = plantillas.parametros(motor.ctx.raiz)["respuesta"]["capa1_palabras_max"]["valor"]
    res = preguntar_minima(motor, {**consulta("Huancavelica"), "intencion": "evolucion", "periodo": {"tipo": "serie"}})
    assert res["tipo"] == "respuesta" and alternativas(res) == []
    assert res["capas"]["capa2"]["avisos"][0].startswith("Respondimos por el departamento de Huancavelica")
    assert res["capas"]["capa1"]["palabras"] <= tope
