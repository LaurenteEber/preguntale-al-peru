"""S2-05 — Interpretar: validar, anclar, aclarar y «Entendimos», con un LLM FALSO inyectado (sin red ni grabaciones).

Una prueba por fila de la tabla del paso 7 y por regla del paso 4; el LLM falso adversario; `elegir` (2,1, números de más,
sin caché); y la equivalencia con la vía estructurada: la respuesta por texto es igual a `preguntar_minima(consulta +
misma pregunta_original)` salvo `interpretacion` y `entendimos`. Si falta el cubo, las pruebas FALLAN (agents.md §8)."""
import json
import re

import pytest
import yaml

from pap.config import Rutas
from pap.interprete import interpretar as I
from pap.interprete import llm as L
from pap.motor.preguntar import EleccionInvalida, preguntar_minima, texto_aclaracion
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL

RAIZ = Rutas(RAIZ_REAL).raiz
TX = yaml.safe_load((RAIZ / "curados/motor/textos/interprete.yaml").read_text(encoding="utf-8"))
CLI = yaml.safe_load((RAIZ / "curados/motor/textos/cli.yaml").read_text(encoding="utf-8"))["mensajes"]
ERR = yaml.safe_load((RAIZ / "curados/motor/textos/errores_consulta.yaml").read_text(encoding="utf-8"))["mensajes"]
NSP = yaml.safe_load((RAIZ / "curados/motor/textos/no_se_puede.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def motor():
    assert (RAIZ / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    return Motor(cargar_contexto(RAIZ))


class Falso:
    """LLM falso: devuelve en orden las interpretaciones dadas (la última se repite) o lanza la excepción dada."""

    def __init__(self, *respuestas):
        self.respuestas, self.llamadas = list(respuestas), []

    def interpretar_crudo(self, prompt, pregunta_limpia, version_prompt, error_previo=None):
        self.llamadas.append({"pregunta": pregunta_limpia, "error_previo": error_previo})
        x = self.respuestas[min(len(self.llamadas), len(self.respuestas)) - 1]
        if isinstance(x, Exception):
            raise x
        return L.RespuestaLLM(x, json.dumps(x, ensure_ascii=False), "falso", version_prompt=version_prompt)


def consulta(c, **anclas):
    return {"resultado": "consulta", "consulta": c, "anclas": anclas}


@pytest.fixture
def preguntar(motor, tmp_path):
    """interpretar() con la caché en una carpeta temporal y sin registro de uso."""
    def f(texto, llm=None, elegir=None):
        return I.interpretar(texto, motor, elegir=elegir, llm=llm, cache_dir=tmp_path / "cache", registro=None)
    return f


def sin_interprete(r):
    return {k: v for k, v in r.items() if k not in ("interpretacion", "entendimos")}


def igual(a, b):
    return json.dumps(sin_interprete(a), sort_keys=True, ensure_ascii=False, default=str) == \
        json.dumps(sin_interprete(b), sort_keys=True, ensure_ascii=False, default=str)


def numeros_no_anio(texto):
    return [d for d in re.findall(r"\d+", texto or "") if not re.fullmatch(r"(19|20)\d\d", d)]


def numeros_visibles(r):
    """Números de lo que ve la persona que no salen de un marcador del cubo ni son años: el texto (sin marcadores; en una
    aclaración, sin la numeración de las opciones) y `entendimos`, sin el eco de pregunta_original."""
    t = r.get("texto_con_marcadores") or r.get("texto") or ""
    t = re.sub(r"\{\{[a-z]:[^}]+\}\}", "", t)
    if r.get("tipo") == "aclaracion":
        t = re.sub(r"(?m)^\d+\) ", "", t)
    t = t.replace(((r.get("plan") or {}).get("pregunta")) or "\0", "")
    return numeros_no_anio(t) + numeros_no_anio(r.get("entendimos"))


# ------------------------------------------------------------------ paso 7, fila «consulta» y equivalencia

APURIMAC = "¿Cuánta anemia hay en Apurímac?"
EQUIVALENCIA = [
    (APURIMAC, consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac"}},
                        intencion="Cuánta", tema="anemia", territorio="Apurímac"),
     {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac"}}),
    ("¿Cuántos niños tienen anemia en Ayaviri (Melgar, Puno)?",
     consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Ayaviri (Melgar, Puno)"}},
              intencion="Cuántos", tema="anemia", territorio="Ayaviri (Melgar, Puno)"),
     {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Ayaviri, Melgar, Puno"}}),
    ("¿Cuál es el distrito más pobre del Perú?",
     consulta({"intencion": "identificar_extremo", "tema": "pobreza_monetaria",
               "territorio": {"nivel": "distrito", "dentro_de": {"nacional": True}}},
              intencion="más pobre", tema="pobre", nivel="distrito", dentro_de="del Perú"),
     {"intencion": "identificar_extremo", "tema": "pobreza_monetaria", "territorio": {"nivel": "distrito", "dentro_de": {"nacional": True}}}),
    ("¿Hay más desnutrición en Loreto que en Ucayali en 2022?",
     consulta({"intencion": "comparacion", "tema": "desnutricion_cronica", "territorio": {"texto": "Loreto"},
               "comparar_con": {"texto": "Ucayali"}, "periodo": {"tipo": "anio", "anio": 2022}},
              intencion="Hay más", tema="desnutrición", territorio="Loreto", comparar_con="Ucayali", anio="2022"),
     {"intencion": "comparacion", "tema": "desnutricion_cronica", "territorio": {"texto": "Loreto"},
      "comparar_con": {"texto": "Ucayali"}, "periodo": {"tipo": "anio", "anio": 2022}}),
    ("¿Cuánta anemia hay en Abancay?",
     consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Abancay"}},
              intencion="Cuánta", tema="anemia", territorio="Abancay"),
     {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Abancay"}}),
]


@pytest.mark.parametrize("pregunta,interp,esperada", EQUIVALENCIA, ids=["nivel", "parentesis", "extremo", "comparacion", "homonimo"])
def test_equivalencia_con_la_via_estructurada(motor, preguntar, pregunta, interp, esperada):
    r = preguntar(pregunta, Falso(interp))
    base = preguntar_minima(motor, {**esperada, "pregunta_original": pregunta, "idioma": "es"})
    assert igual(r, base)
    assert r["consulta_minima"] == {**esperada, "pregunta_original": pregunta, "idioma": "es"}
    assert r["interpretacion"]["resultado"] == "consulta" and r["interpretacion"]["descartados"] == []
    assert not numeros_no_anio(r["entendimos"])


def test_q1_homonimo_y_luego_elegir(motor, preguntar):
    pregunta, interp, esperada = EQUIVALENCIA[4]
    falso = Falso(interp)
    r = preguntar(pregunta, falso)
    assert r["tipo"] == "aclaracion" and r["aclaracion"]["motivo"] == "homonimo_niveles"
    assert r["entendimos"] == "Entendimos: cuánto hay de anemia en «Abancay»"
    r1 = preguntar(pregunta, falso, elegir=1)
    assert len(falso.llamadas) == 1                                                # la segunda vez, de la caché
    base = preguntar_minima(motor, {**esperada, "pregunta_original": pregunta, "idioma": "es"}, elegir=1)
    assert r1["tipo"] == "respuesta" and igual(r1, base) and r1["interpretacion"]["cache"] is True
    assert r1["entendimos"] == "Entendimos: cuánto hay de anemia en la provincia de Abancay (Apurímac)"


def test_entendimos_con_nombre_del_resolver_y_anios(preguntar):
    r = preguntar("¿Cómo cambió la anemia en Apurímac entre 2019 y 2024?",
                  Falso(consulta({"intencion": "evolucion", "tema": "anemia", "territorio": {"texto": "Apurímac"},
                                  "periodo": {"tipo": "serie", "desde": 2019, "hasta": 2024}},
                                 intencion="Cómo cambió", tema="anemia", territorio="Apurímac", desde="2019", hasta="2024")))
    assert r["entendimos"] == "Entendimos: cómo cambió la anemia en el departamento de Apurímac entre 2019 y 2024"


# ------------------------------------------------------------------ paso 7, fila «aclaracion»

TACNA = "¿Cómo va la anemia en Apurímac?"
AMBIGUA = {"resultado": "aclaracion", "motivo": "intencion_ambigua", "opciones": [
    {"consulta": {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac"}},
     "anclas": {"intencion": "Cómo va", "tema": "anemia", "territorio": "Apurímac"}},
    {"consulta": {"intencion": "evolucion", "tema": "anemia", "territorio": {"texto": "Apurímac"}},
     "anclas": {"intencion": "Cómo va", "tema": "anemia", "territorio": "Apurímac"}}]}


def test_aclaracion_del_llm_tiene_la_forma_de_respuesta_aclaracion(motor, preguntar):
    r = preguntar(TACNA, Falso(AMBIGUA))
    a = r["aclaracion"]
    assert r["tipo"] == "aclaracion" and a["motivo"] == "interprete_intencion_ambigua"
    assert a["pregunta"] == TX["aclaraciones"]["intencion_ambigua"]
    et = [o["etiqueta"] for o in a["opciones"]]
    assert et == ["Cómo cambió la anemia en el departamento de Apurímac", "Cuánto hay de anemia en el departamento de Apurímac"]
    assert et == sorted(et, key=I.normalizar) and [o["n"] for o in a["opciones"]] == [1, 2]
    assert r["texto"] == texto_aclaracion(motor, a) and r["cifras"] == {}
    assert set(r) >= {"tipo", "texto", "aclaracion", "consulta", "version_biblioteca", "cifras"}
    r2 = preguntar(TACNA, Falso(AMBIGUA), elegir=2)
    assert igual(r2, preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac"},
                                              "pregunta_original": TACNA, "idioma": "es"}))


def test_aclaracion_con_opciones_iguales_tras_anclar_no_pregunta(preguntar):
    x = json.loads(json.dumps(AMBIGUA))
    x["opciones"][1]["anclas"]["intencion"] = "ancla inventada"          # se descarta la intención → nivel_actual, igual a la 1
    x["opciones"][1]["consulta"]["intencion"] = "nivel_actual"
    r = preguntar(TACNA, Falso(x))
    assert r["tipo"] == "respuesta"


# ------------------------------------------------------------------ paso 7, filas «fuera de alcance» y mensajes fijos

def test_fuera_de_alcance_tema(preguntar):
    r = preguntar("¿Cuántos colegios hay en Arequipa?", Falso({"resultado": "fuera_de_alcance", "tipo": "tema", "pedido": "colegios"}))
    assert r["tipo"] == "no_se_puede" and r["motivo"]["codigo"] == "tema_fuera_del_piloto"
    assert r["motivo"]["detalle"]["tema_pedido"] == "colegios" and r["temas_disponibles"] and r["cifras"] == {}
    assert r["plan"]["id"] == "no_se_puede__tema_fuera_del_piloto"


def test_fuera_de_alcance_pregunta(preguntar):
    r = preguntar("¿Por qué hay tanta anemia en Puno?",
                  Falso({"resultado": "fuera_de_alcance", "tipo": "pregunta", "pedido": "Por qué hay tanta anemia"}))
    m = NSP["motivos"]["interprete_fuera_de_alcance"]
    assert m["regla"] is None and m["alcance"] == "total"
    assert r["tipo"] == "no_se_puede" and r["motivo"]["codigo"] == "interprete_fuera_de_alcance"
    assert r["motivo"]["regla_lenguaje_05"] is None and r["cifras"] == {} and not r["temas_disponibles"]
    assert r["capas"]["capa1"]["respuesta_corta"].startswith("Todavía no respondemos")
    assert "no tenemos datos de ese tema" not in r["texto"].lower()
    assert "cómo cambió" in r["texto"] and not numeros_visibles(r)
    assert not [x for x in r["corrector"] if x["accion"] != "rotular"]
    assert r["capas"]["capa1"]["palabras"] <= yaml.safe_load((RAIZ / "curados/motor/parametros_motor.yaml").read_text(
        encoding="utf-8"))["respuesta"]["capa1_palabras_max"]["valor"]


@pytest.mark.parametrize("resultado,texto", [("no_es_pregunta", TX["no_es_pregunta"]), ("otro_idioma", ERR["idioma_invalido"])])
def test_mensajes_fijos(preguntar, resultado, texto):
    r = preguntar("hola", Falso({"resultado": resultado}))
    assert r["tipo"] == "mensaje" and r["motivo"] == resultado and r["cifras"] == {}
    assert r["texto"].startswith(texto) and r["texto"].endswith(TX["via_estructurada"])
    assert r["entendimos"] is None


def test_no_valida_dos_veces_es_no_entendida_y_el_reintento_lleva_el_error(preguntar):
    falso = Falso({"resultado": "consulta"}, {"resultado": "nada"})
    r = preguntar(APURIMAC, falso)
    assert r["tipo"] == "mensaje" and r["motivo"] == "no_entendida"
    assert r["texto"] == f"{TX['no_entendida']} {TX['via_estructurada']}"
    assert len(falso.llamadas) == 2 and falso.llamadas[0]["error_previo"] is None
    assert "interpretacion_invalida" in falso.llamadas[1]["error_previo"]


def test_el_reintento_que_valida_se_usa(preguntar):
    bien = EQUIVALENCIA[0][1]
    falso = Falso(None, bien)
    r = preguntar(APURIMAC, falso)
    assert r["tipo"] == "respuesta" and r["interpretacion"]["reintentos"] == 1
    assert "no_es_objeto" in falso.llamadas[1]["error_previo"]


def test_no_disponible_no_adivina(preguntar, tmp_path):
    falso = Falso(L.NoDisponible("sin_clave"))
    r = preguntar(APURIMAC, falso)
    assert r == {**r, "tipo": "mensaje", "motivo": "no_disponible", "texto": TX["no_disponible"], "cifras": {}}
    with pytest.raises(EleccionInvalida, match="venció"):                         # una falla no se guarda en la caché
        preguntar(APURIMAC, falso, elegir=1)


# ------------------------------------------------------------------ paso 4: anclas

def test_normalizar():
    assert I.normalizar("  ¿Qué  ÑAÑO, Áncash?! ") == "que nano ancash"


def test_ancla_que_no_esta_en_la_pregunta_se_descarta(preguntar):
    r = preguntar(APURIMAC, Falso(consulta({"intencion": "nivel_actual", "tema": "pobreza_monetaria", "territorio": {"texto": "Apurímac"}},
                                           intencion="Cuánta", tema="pobreza", territorio="Apurímac")))
    assert r["interpretacion"]["descartados"] == ["tema"]
    assert r["tipo"] == "aclaracion" and r["aclaracion"]["motivo"] == "falta_tema"     # el motor pregunta el tema
    assert "tema" not in r["consulta_minima"]


def test_ancla_con_pedazo_de_palabra_no_vale():
    chk = I.Anclas(RAIZ, "¿Cuánta anemia hay en Apurímac?")
    assert chk.en_pregunta("anemia") and chk.en_pregunta("ANEMIA hay") and not chk.en_pregunta("anem")


def test_texto_del_lugar_debe_ser_su_ancla(preguntar):
    r = preguntar("¿Cuánta anemia hay en Huancavelica?",
                  Falso(consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "departamento de Huancavelica"}},
                                 intencion="Cuánta", tema="anemia", territorio="Huancavelica")))
    assert r["interpretacion"]["descartados"] == ["territorio"]
    assert r["tipo"] == "aclaracion" and r["aclaracion"]["motivo"] == "interprete_sin_lugar"
    assert "departamento" not in json.dumps(r, ensure_ascii=False)


def test_comparar_con_y_dentro_de_deben_ser_su_ancla(preguntar):
    q = "¿Hay más anemia en Loreto que en Ucayali?"
    r = preguntar(q, Falso(consulta({"intencion": "comparacion", "tema": "anemia", "territorio": {"texto": "Loreto"},
                                     "comparar_con": {"texto": "Ucayali y Pasco"}},
                                    intencion="Hay más", tema="anemia", territorio="Loreto", comparar_con="Ucayali")))
    assert r["interpretacion"]["descartados"] == ["comparar_con"]
    assert r["aclaracion"]["motivo"] == "interprete_sin_lugar" and r["aclaracion"]["pregunta"] == TX["aclaraciones"]["sin_lugar"]["comparar_con"]
    q = "¿Qué distrito de Puno tiene más anemia?"
    r = preguntar(q, Falso(consulta({"intencion": "identificar_extremo", "tema": "anemia",
                                     "territorio": {"nivel": "distrito", "dentro_de": {"texto": "Puno"}}},
                                    intencion="más", tema="anemia", nivel="distrito", dentro_de="Cusco")))
    assert r["interpretacion"]["descartados"] == ["dentro_de"]
    assert r["aclaracion"]["pregunta"] == TX["aclaraciones"]["sin_lugar"]["dentro_de"]


def test_nacional_necesita_un_ancla_de_la_lista(preguntar):
    chk = I.Anclas(RAIZ, "¿Cuál es el distrito más pobre del Perú en todo el país?")
    assert chk.lugar({"nacional": True}, "del Perú") and chk.lugar({"nacional": True}, "todo el país")
    assert not chk.lugar({"nacional": True}, "distrito")
    r = preguntar("¿Cuánta anemia hay en la sierra?",
                  Falso(consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"nacional": True}},
                                 intencion="Cuánta", tema="anemia", territorio="la sierra")))
    assert r["interpretacion"]["descartados"] == ["territorio"] and r["aclaracion"]["motivo"] == "interprete_sin_lugar"


def test_nivel_necesita_una_palabra_de_nivel(preguntar):
    chk = I.Anclas(RAIZ, "¿En qué provincias de Puno hay más anemia? ¿Y en qué región?")
    assert chk.nivel("provincia", "provincias") and chk.nivel("departamento", "región")
    assert not chk.nivel("distrito", "provincias") and not chk.nivel("provincia", "qué")
    r = preguntar("¿Dónde hay más anemia?",
                  Falso(consulta({"intencion": "identificar_extremo", "tema": "anemia", "territorio": {"nivel": "distrito"}},
                                 intencion="Dónde hay más", tema="anemia", nivel="Dónde")))
    assert r["tipo"] == "mensaje" and r["motivo"] == "no_entendida" and r["interpretacion"]["descartados"] == ["nivel"]


def test_anio_debe_ser_un_numero_de_su_ancla(preguntar):
    q = "¿Cuánta anemia había en Apurímac en 2019?"
    r = preguntar(q, Falso(consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac"},
                                     "periodo": {"tipo": "anio", "anio": 2019}},
                                    intencion="Cuánta", tema="anemia", territorio="Apurímac", anio="en 2019")))
    assert r["consulta_minima"]["periodo"] == {"tipo": "anio", "anio": 2019}
    r = preguntar("¿Y cuánta anemia había en Apurímac en el 2019?", Falso(consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac"},
                                           "periodo": {"tipo": "anio", "anio": 2018}},
                                          intencion="Cuánta", tema="anemia", territorio="Apurímac", anio="2019")))
    assert r["interpretacion"]["descartados"] == ["anio"] and r["aclaracion"]["motivo"] == "interprete_anio_relativo"


# ------------------------------------------------------------------ paso 5: lo que falta

def test_sin_intencion_es_nivel_actual(motor, preguntar):
    q = "anemia en Apurímac"
    r = preguntar(q, Falso(consulta({"tema": "anemia", "territorio": {"texto": "Apurímac"}}, tema="anemia", territorio="Apurímac")))
    assert r["consulta_minima"]["intencion"] == "nivel_actual"
    assert igual(r, preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac"},
                                             "pregunta_original": q, "idioma": "es"}))


SIN_LUGAR = consulta({"intencion": "nivel_actual", "tema": "anemia"}, intencion="cuánta", tema="anemia")


def test_sin_lugar_aclaracion_armada_por_el_codigo(motor, preguntar):
    q = "¿cuánta anemia hay?"
    r = preguntar(q, Falso(SIN_LUGAR))
    a = r["aclaracion"]
    assert r["tipo"] == "aclaracion" and a["motivo"] == "interprete_sin_lugar"
    assert [o["etiqueta"] for o in a["opciones"]] == ["Todo el Perú", "Escribe el lugar"]
    assert r["entendimos"] == "Entendimos: cuánto hay de anemia"
    r1 = preguntar(q, Falso(SIN_LUGAR), elegir=1)
    assert igual(r1, preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"nacional": True},
                                              "pregunta_original": q, "idioma": "es"}))
    assert r1["entendimos"] == "Entendimos: cuánto hay de anemia en todo el Perú"
    r2 = preguntar(q, Falso(SIN_LUGAR), elegir=2)
    assert r2 == {**r2, "tipo": "mensaje", "motivo": "volver_a_preguntar", "texto": TX["volver_a_preguntar"]}


def test_anio_relativo_omitido_por_el_llm_igual_se_aclara(motor, preguntar):
    """S2-07 (revisión adversaria, x09): el prompt manda omitir los años relativos; si el LLM los omite (también dentro de una
    aclaración de intención), el código ve la frase relativa en la pregunta y aclara el año, sin responder el último en
    silencio (`interprete.anios_relativos`)."""
    q = "¿Cómo está la pobreza en Arequipa el año pasado?"
    x = consulta({"intencion": "nivel_actual", "tema": "pobreza_monetaria", "territorio": {"texto": "región Arequipa"}},
                 intencion="Cómo está", tema="pobreza", territorio="Arequipa")
    x["consulta"]["territorio"]["texto"] = "Arequipa"
    r = preguntar(q, Falso(x))
    assert r["tipo"] == "aclaracion" and r["aclaracion"]["motivo"] == "interprete_anio_relativo"
    assert [o["etiqueta"] for o in r["aclaracion"]["opciones"]] == ["El último año con datos", "Escribe el año"]
    sin = preguntar("¿Cómo está la pobreza en Arequipa?", Falso(x))                 # sin frase relativa: no se aclara el año
    assert not (sin["tipo"] == "aclaracion" and sin["aclaracion"]["motivo"] == "interprete_anio_relativo")
    con_anio = preguntar("¿Cómo estaba la pobreza en Arequipa en 2024, el año pasado?", Falso(consulta(
        {"intencion": "nivel_actual", "tema": "pobreza_monetaria", "territorio": {"texto": "Arequipa"}, "periodo": {"tipo": "anio", "anio": 2024}},
        intencion="Cómo estaba", tema="pobreza", territorio="Arequipa", anio="2024")))
    assert not (con_anio["tipo"] == "aclaracion" and con_anio["aclaracion"]["motivo"] == "interprete_anio_relativo")


def test_anio_fuera_de_rango_se_aclara_sin_reintento(motor, preguntar):
    """S2-09 (revisión adversaria repetida, y08): un año que el esquema rechaza («3025») no se reintenta (el LLM lo quitaba y
    se respondía el último año en silencio): se descarta y se aclara el año, como un año sin ancla (S2-05-a)."""
    q = "¿Cuánta anemia había en Puno en el año 3025?"
    con = consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Puno"}, "periodo": {"tipo": "anio", "anio": 3025}},
                   intencion="Cuánta", tema="anemia", territorio="Puno", anio="3025")
    sin = consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Puno"}},
                   intencion="Cuánta", tema="anemia", territorio="Puno")
    llm = Falso(con, sin)
    r = preguntar(q, llm)
    assert len(llm.llamadas) == 1
    assert r["tipo"] == "aclaracion" and r["aclaracion"]["motivo"] == "interprete_anio_relativo"
    assert r["interpretacion"]["descartados"] == ["anio"]
    assert "2025" not in json.dumps(r, ensure_ascii=False)


def test_anio_relativo_descartado(motor, preguntar):
    q = "¿Cuánta anemia hubo el año pasado en Apurímac?"
    x = consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac"}, "periodo": {"tipo": "anio", "anio": 2025}},
                 intencion="Cuánta", tema="anemia", territorio="Apurímac", anio="el año pasado")
    r = preguntar(q, Falso(x))
    assert [o["etiqueta"] for o in r["aclaracion"]["opciones"]] == ["El último año con datos", "Escribe el año"]
    assert "2025" not in json.dumps(r, ensure_ascii=False)
    r1 = preguntar(q, Falso(x), elegir=1)
    assert igual(r1, preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac"},
                                              "periodo": {"tipo": "ultimo"}, "pregunta_original": q, "idioma": "es"}))
    assert preguntar(q, Falso(x), elegir=2)["motivo"] == "volver_a_preguntar"


# ------------------------------------------------------------------ paso 6: paréntesis

@pytest.mark.parametrize("antes,despues", [("Ayaviri (Melgar, Puno)", "Ayaviri, Melgar, Puno"), ("Ayaviri (Melgar)", "Ayaviri, Melgar"),
                                           ("Ayaviri ( Melgar ,Puno )", "Ayaviri, Melgar, Puno"), ("San Juan de Lurigancho", "San Juan de Lurigancho")])
def test_forma_con_comas(antes, despues):
    assert I.forma_con_comas(antes) == despues


# ------------------------------------------------------------------ LLM falso adversario

ADVERSARIO = [
    ("¿Cuánta anemia hay en Huancavelica?",
     consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "departamento de Huancavelica"}},
              intencion="Cuánta", tema="anemia", territorio="Huancavelica"), "departamento de Huancavelica"),
    ("¿Cuánta anemia hay en Apurímac?",
     consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac"}, "periodo": {"tipo": "anio", "anio": 2017}},
              intencion="Cuánta", tema="anemia", territorio="Apurímac", anio="2017"), "2017"),
    ("¿Cuánta anemia hay en Apurímac?",
     {"resultado": "consulta", "consulta": {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"ubigeo": "030000"}},
      "anclas": {"intencion": "Cuánta", "tema": "anemia", "territorio": "Apurímac"}}, "030000"),
    ("¿Cuánta anemia hay en Apurímac?",
     consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac 03"}},
              intencion="Cuánta", tema="anemia", territorio="Apurímac 03"), "03"),
    ("¿Qué distrito tiene más anemia?",
     consulta({"intencion": "identificar_extremo", "tema": "anemia", "territorio": {"nivel": "provincia"}},
              intencion="más", tema="anemia", nivel="Qué"), "provincia"),
]


@pytest.mark.parametrize("pregunta,interp,veneno", ADVERSARIO, ids=["texto_agregado", "anio_inventado", "ubigeo", "cifra_en_lugar", "nivel_sin_ancla"])
def test_llm_falso_adversario(preguntar, pregunta, interp, veneno):
    r = preguntar(pregunta, Falso(interp))
    llega = json.dumps({k: r.get(k) for k in ("consulta_minima", "texto", "capas", "aclaracion", "entendimos")}, ensure_ascii=False)
    assert veneno not in llega, (veneno, r["tipo"])
    i = r["interpretacion"]
    assert veneno not in json.dumps([i["consulta"], i["anclas"]], ensure_ascii=False)
    assert not numeros_visibles(r)


def test_llm_falso_adversario_todo_junto(preguntar):
    x = {"resultado": "consulta", "consulta": {"intencion": "comparacion", "tema": "anemia",
                                               "territorio": {"texto": "departamento de Huancavelica"},
                                               "comparar_con": {"ubigeo": "030000"}, "periodo": {"tipo": "anio", "anio": 2017}},
         "anclas": {"intencion": "más", "tema": "anemia", "territorio": "Huancavelica", "comparar_con": "Apurímac", "anio": "2017"}}
    r = preguntar("¿Hay más anemia en Huancavelica que en Apurímac?", Falso(x))
    assert r["tipo"] == "mensaje" and r["motivo"] == "no_entendida"


# ------------------------------------------------------------------ --elegir

LUGAR_AMBIGUO = "¿Cómo va la anemia en Abancay?"
AMBIGUA_HV = {"resultado": "aclaracion", "motivo": "intencion_ambigua", "opciones": [
    {"consulta": {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Abancay"}},
     "anclas": {"intencion": "Cómo va", "tema": "anemia", "territorio": "Abancay"}},
    {"consulta": {"intencion": "evolucion", "tema": "anemia", "territorio": {"texto": "Abancay"}},
     "anclas": {"intencion": "Cómo va", "tema": "anemia", "territorio": "Abancay"}}]}


def test_elegir_2_1_interprete_y_luego_territorio(motor, preguntar):
    falso = Falso(AMBIGUA_HV)
    r = preguntar(LUGAR_AMBIGUO, falso)
    assert r["aclaracion"]["motivo"] == "interprete_intencion_ambigua"
    assert r["aclaracion"]["opciones"][1]["etiqueta"] == "Cuánto hay de anemia en «Abancay»"
    r2 = preguntar(LUGAR_AMBIGUO, falso, elegir=[2])
    assert r2["aclaracion"]["motivo"] == "homonimo_niveles"
    r21 = preguntar(LUGAR_AMBIGUO, falso, elegir=[2, 1])
    base = preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Abancay"},
                                    "pregunta_original": LUGAR_AMBIGUO, "idioma": "es"}, elegir=[1])
    assert r21["tipo"] == "respuesta" and igual(r21, base) and len(falso.llamadas) == 1
    assert r21["entendimos"] == "Entendimos: cuánto hay de anemia en la provincia de Abancay (Apurímac)"


@pytest.mark.parametrize("elegir,clave,hay", [([2, 1, 1], "elegir_de_mas", 2), ([1, 1], "elegir_de_mas_una", 1)])
def test_elegir_numeros_de_mas_con_la_cuenta_total(preguntar, elegir, clave, hay):
    q, x = (LUGAR_AMBIGUO, AMBIGUA_HV) if hay == 2 else ("¿cuánta anemia hay?", SIN_LUGAR)
    preguntar(q, Falso(x))
    with pytest.raises(EleccionInvalida) as e:
        preguntar(q, Falso(x), elegir=elegir)
    assert str(e.value) == CLI[clave].format(escritos=len(elegir), hay=hay)


def test_elegir_sin_nada_que_elegir(preguntar):
    preguntar(APURIMAC, Falso(EQUIVALENCIA[0][1]))
    with pytest.raises(EleccionInvalida) as e:
        preguntar(APURIMAC, Falso(EQUIVALENCIA[0][1]), elegir=1)
    assert str(e.value) == CLI["elegir_de_mas_ninguna"]


def test_elegir_fuera_de_rango(preguntar):
    preguntar(TACNA, Falso(AMBIGUA))
    with pytest.raises(EleccionInvalida, match="La opción 5 no existe"):
        preguntar(TACNA, Falso(AMBIGUA), elegir=5)


def test_elegir_sin_cache_es_error_sin_llamar_al_llm(preguntar):
    falso = Falso(AMBIGUA)
    with pytest.raises(EleccionInvalida) as e:
        preguntar(TACNA, falso, elegir=1)
    assert str(e.value) == TX["elegir_vencida"] and falso.llamadas == []


def test_cache_vencida_vuelve_a_llamar(motor, tmp_path):
    falso = Falso(SIN_LUGAR)
    I.interpretar("¿cuánta anemia hay?", motor, llm=falso, cache_dir=tmp_path, registro=None)
    (archivo,) = list(tmp_path.glob("*.json"))
    g = json.loads(archivo.read_text(encoding="utf-8"))
    g["creada"] -= 25 * 3600
    archivo.write_text(json.dumps(g), encoding="utf-8")
    with pytest.raises(EleccionInvalida, match="venció"):
        I.interpretar("¿cuánta anemia hay?", motor, llm=falso, cache_dir=tmp_path, registro=None, elegir=1)
    I.interpretar("¿cuánta anemia hay?", motor, llm=falso, cache_dir=tmp_path, registro=None)
    assert len(falso.llamadas) == 2


# ------------------------------------------------------------------ registro de uso (P-03) y limpieza

def test_registro_de_uso_sin_texto_y_pregunta_limpia(motor, tmp_path):
    reg = tmp_path / "uso.jsonl"
    falso = Falso(SIN_LUGAR)
    r = I.interpretar("¿cuánta anemia hay? mi DNI 45678912", motor, llm=falso, cache_dir=tmp_path / "c", registro=reg)
    assert "45678912" not in falso.llamadas[0]["pregunta"] and r["interpretacion"]["datos_personales_quitados"] == 1
    fila = json.loads(reg.read_text(encoding="utf-8").splitlines()[0])
    assert fila["resultado"] == "consulta" and "anemia hay" not in json.dumps(fila, ensure_ascii=False)
    assert "45678912" not in "".join(p.read_text(encoding="utf-8") for p in (tmp_path / "c").glob("*.json"))


def test_ningun_texto_visible_nuevo_en_python():
    fuente = (RAIZ / "src/pap/interprete/interpretar.py").read_text(encoding="utf-8")
    fuente = re.sub(r"#[^\n]*", "", re.sub(r'"""[\s\S]*?"""', "", fuente))            # sin docstrings ni comentarios
    for t in [TX["no_entendida"], TX["volver_a_preguntar"], TX["elegir_vencida"], TX["aclaraciones"]["sin_lugar"]["territorio"],
              "Todo el Perú", "Entendimos", "Escribe el"]:
        assert t not in fuente, t
