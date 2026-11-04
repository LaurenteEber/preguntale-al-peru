"""Piloto P3: respuestas de las preguntas 1–4 por plantilla (sin LLM)."""
import json
import re

import pytest

from pap.config import Rutas
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL

ESPERADO = {"q1": "verde", "q2": "ambar", "q3": "rojo", "q4": "rojo"}  # semáforo de la respuesta (P3, 10/10/2026)


@pytest.fixture(scope="module")
def respuestas():
    import yaml
    raiz = Rutas(RAIZ_REAL).raiz
    if not (raiz / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists():
        pytest.skip("cubo sin construir (pap calcular)")
    m = Motor(cargar_contexto(raiz))
    return {q: m.responder(yaml.safe_load((raiz / "tests" / "fixtures" / "consultas_piloto" / f"{q}.yaml").read_text(encoding="utf-8")))
            for q in ESPERADO}


@pytest.mark.parametrize("q", list(ESPERADO))
def test_respuesta_completa(respuestas, q):
    r = respuestas[q]
    assert r["semaforo_respuesta"] == ESPERADO[q]
    assert r["texto"] and not re.search(r"\{\{|\}\}", r["texto"])          # sin marcadores sin rellenar
    assert len(r["ficha"]["corta"].splitlines()) <= 4                     # R-LENGUAJE-01
    bloqueos = [x for x in r["resultados_respuesta"] if x["regla"] in ("R-LENGUAJE-01", "R-LENGUAJE-02", "R-LENGUAJE-03",
                                                                       "R-GASTO-15") and x["accion"] != "rotular"]
    assert not bloqueos, bloqueos                                          # el corrector no pide regenerar ni bloquea
    assert not any(x.get("motivo") == "metadato_faltante" for x in r["resultados_respuesta"])
    # todo número del texto sale de una cifra del cubo (R-LENGUAJE-03): sin dígitos fuera de marcadores salvo años
    t = re.sub(r"\{\{[a-z]:[^}]+\}\}", "", r["texto_con_marcadores"])
    assert not [d for d in re.findall(r"\d+", t) if not re.fullmatch(r"(19|20)\d\d", d)]


def test_q3_estructura_de_efecto(respuestas):
    t = respuestas["q3"]["texto"]
    # AD-2 (dueño, 4/11/2026; S1-14): frase estándar de efecto de R-CRUCES-07
    assert "evaluación" in t and "no muestran si el gasto lo cambió" in t and "registrado por unidades ejecutoras con sede en" in t
    assert "cómo cambió el indicador" not in t


def test_q4_sin_ranking_puntual(respuestas):
    t = respuestas["q4"]["texto"].lower()
    assert "no se puede nombrar un solo distrito como el más pobre" in t
    assert "más pobre" not in t.replace("no se puede nombrar un solo distrito como el más pobre", "")


def test_ic_doble_propio_e_inei(respuestas):
    """Decisión del 11/10/2026: en el piloto se muestran el IC propio (Korn-Graubard) y el publicado por el INEI, con nota."""
    c = respuestas["q1"]["cifras"]["anemia_hvca_2025"]
    assert c["metodo_ic"] == "korn-graubard"
    assert (c["ic_inei"]["ic_inf"], c["ic_inei"]["ic_sup"]) == (32.0, 45.1)   # PPR ENDES 2025, Cuadro 06.1A
    prec = respuestas["q1"]["ficha"]["larga"]["cifras"]["anemia_hvca_2025"]["4_precision"]
    assert "El INEI publica para esta cifra un intervalo entre 32,0" in prec and "Cuadro N.º 06.1A" in prec
    # una cifra sin intervalo publicado por el INEI (2015, serie anterior): solo el propio. La de 2022 ya no se usa (C-01).
    sin = respuestas["q1"]["ficha"]["larga"]["cifras"]["anemia_hvca_2015_ant"]["4_precision"]
    assert respuestas["q1"]["cifras"]["anemia_hvca_2015_ant"]["ic_inei"] is None and "nuestro cálculo" in sin
    assert "anemia_hvca_2022_ant" not in respuestas["q1"]["cifras"]
    assert respuestas["q4"]["cifras"]["mapa_050410"]["ic_inei"] is None   # el Mapa ya es el intervalo del INEI


# ----------------------------------------------------------------- P4: decisiones del dueño del 11/10/2026

def test_q1_dos_criterios_en_paralelo(respuestas):
    """Q1: serie vigente 2024–2025 y serie anterior 2015–2025 (a través de 2020, sin ese punto), cada una con su alcance y
    contrastada con la cifra oficial de su mismo criterio."""
    r = respuestas["q1"]
    vig, ant = r["cifras"]["anemia_hvca_2025"], r["cifras"]["anemia_hvca_2025_ant"]
    assert vig["indicador_id"] == "endes_anemia_6_35m_oms2024" and ant["indicador_id"] == "endes_anemia_6_35m"
    assert ant["comparacion"]["anio"] == 2015 and "anemia_hvca_2025_ant" not in r["comparaciones_bloqueadas"]
    assert "entre 2015 y 2025 se mantuvo sin cambio estadísticamente claro" in r["texto"]
    assert "{{p:dos_formas}}" in r["texto_con_marcadores"]
    larga = {k: {s: str(t).replace("\u202f", " ") for s, t in v.items()} for k, v in r["ficha"]["larga"]["cifras"].items()}
    assert "38,6 % con la forma de medir vigente desde 2024" in larga["anemia_hvca_2025"]["6_contraste_oficial"]
    assert "54,5 % con la forma de medir anterior a 2024" in larga["anemia_hvca_2025_ant"]["6_contraste_oficial"]
    assert "Nuestra cifra coincide" in larga["anemia_hvca_2025_ant"]["6_contraste_oficial"]


def test_q3_compara_endes_lm_2024_2025(respuestas):
    r = respuestas["q3"]
    assert r["cifras"]["anemia_lm_2025"]["comparacion"]["anio"] == 2024
    assert "Entre 2024 y 2025, en Lima Metropolitana, la anemia" in r["texto"]
    assert r["semaforo_respuesta"] == "rojo"   # cobertura del SIEN en LM 2025 < 50 % (R-CRUCES-09)


def test_q4_grupo_oficial_del_inei(respuestas):
    """R-ENC-12: los grupos oficiales del INEI prevalecen (pobreza 2016–2025, § 4.2.5): grupo 1 de 2025 = 7 departamentos."""
    r = respuestas["q4"]
    enaho = {c["territorio_id"] for k, c in r["cifras"].items() if k.startswith("enaho_")}
    assert enaho == {"05", "06", "09", "10", "16", "19", "21"}
    assert "según el INEI, siete departamentos forman el grupo con la pobreza monetaria más alta" in r["texto"]


# ----------------------------------------------------------------- P4: hallazgos altos de la auditoría (11/10/2026)

def test_p4_01_q4_mapa_es_la_principal(respuestas):
    """R-CRUCES-08.parametros.jerarquias: con pedido distrital de pobreza manda el Mapa 2018 (R-EST-05), no la ENAHO."""
    r = respuestas["q4"]
    todo = str(r["ficha"]) + str(r["avisos_al_usuario"])
    assert "Usamos la ENAHO como cifra principal" not in todo
    comp = [x for x in r["resultados_respuesta"] if x["regla"] == "R-CRUCES-08" and x["motivo"] == "fuente_complementaria"]
    assert all(str(x.get("objetivo", "")).startswith("enaho_") for x in comp)


def test_p4_02_q3_muestra_la_cobertura_que_lo_pone_en_rojo(respuestas):
    r = respuestas["q3"]
    c = r["cifras"]["cobertura_lm_2025"]
    assert c["cota_sup"] < 50 and "En Lima Metropolitana, a menos de la mitad de los niños se les midió la hemoglobina" in r["texto"]


def test_p4_03_q2_cobertura_que_cruza_el_50(respuestas):
    t = respuestas["q2"]["texto"].replace(" ", " ")
    assert "entre 39,8 % y 50,5 %" in t
    assert "no podemos decir si se midió a más o a menos de la mitad de los niños" in t


def test_p4_10_sin_codigos_internos_en_la_ficha(respuestas):
    import json
    from pap.motor import formato as fmt
    for q, r in respuestas.items():
        larga = {k: v for k, v in r["ficha"]["larga"].items() if k != "reproducibilidad"}
        s = json.dumps(larga, ensure_ascii=False) + json.dumps(r["avisos_al_usuario"], ensure_ascii=False)
        assert not [k for k in fmt.HUMANO if k not in ("LM", "LR") and re.search(rf"(?<![\w-]){re.escape(k)}(?![\w-])", s)], q


def test_sien_contraste_oficial_ins(respuestas):
    """12/10/2026: las cifras del SIEN de Q2 y Q3 se contrastan con la publicación oficial del INS y coinciden."""
    for q, cid, val in (("q2", "sien_ayaviri_2025", "9,5"), ("q3", "sien_sjl_2025", "8,2")):
        c = respuestas[q]["cifras"][cid]
        assert c["validada_dorada"] and c["contraste_oficial"]["entidad"] == "INS"
        txt = respuestas[q]["ficha"]["larga"]["cifras"][cid]["6_contraste_oficial"]
        assert txt.startswith(f"El INS publica {val}") and "Nuestra cifra coincide." in txt


# ----------------------------------------------------------------- contrato de respuesta (12/10/2026)

@pytest.mark.parametrize("q", list(ESPERADO))
def test_contrato_respuesta_por_capas(respuestas, q):
    """Decisión del dueño (12/10/2026) tras la revisión de usuario: respuesta por capas, confianza sin colores, avisos que
    dicen qué no concluir, cita lista para copiar y glosario."""
    k = respuestas[q]["capas"]
    c1, c2, c3 = k["capa1"], k["capa2"], k["capa3"]
    assert c1["respuesta_corta"] and 1 <= len(c1["ojo_al_leer"]) <= 3
    assert all(t.startswith(("No ", "«", "Dato de")) for t in c1["ojo_al_leer"])
    assert c1["palabras"] <= 125                                       # capa visible corta (objetivo ≈ 100)
    assert c1["confianza"]["nivel"] in ("alta", "media", "baja")
    assert c1["confianza"]["texto"].startswith("Confianza en los datos: ")
    assert not re.search(r"\b(verde|ámbar|ambar|rojo)\b", json.dumps(k, ensure_ascii=False))  # sin colores
    assert respuestas[q]["ficha"]["corta"].startswith("Confianza en los datos: ")
    assert len(c3["para_citar"]) == len(respuestas[q]["cifras"]) and all("Fuente:" in x for x in c3["para_citar"])
    assert c3["glosario"] and not any("Este párrafo combina" in a for a in c2["avisos"])
    def textos(x):
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict):
            for v in x.values():
                yield from textos(v)
        elif isinstance(x, list):
            for v in x:
                yield from textos(v)
    assert not [t for t in textos(k) if re.search(r"\{\{|\}\}", t)]                # sin marcadores sin rellenar


def test_respuesta_corta_dice_primero_lo_que_no_se_puede(respuestas):
    assert respuestas["q2"]["capas"]["capa1"]["respuesta_corta"].startswith("No se puede saber cuántos niños de Ayaviri")
    assert respuestas["q3"]["capas"]["capa1"]["respuesta_corta"].startswith("No se puede saber si el gasto")
    assert respuestas["q4"]["capas"]["capa1"]["respuesta_corta"].startswith("No se puede nombrar un solo distrito")
    # Q4: los distritos del grupo en orden alfabético (no insinúan un ranking)
    t = respuestas["q4"]["capas"]["capa1"]["cifra_clave"]["texto"]
    assert t.index("Anguía") < t.index("Oxamarca") < t.index("Uchuraccay")


def test_que_hacer_solo_fuente_oficial(respuestas):
    """Decisión del dueño (12/10/2026): «¿Qué puedo hacer?» solo con texto fijo que enlaza una fuente oficial."""
    for q in ("q1", "q2", "q3"):
        qh = respuestas[q]["capas"]["capa1"]["que_hacer"]
        assert qh["url"].startswith("https://www.gob.pe/") and "Ministerio de Salud" in qh["fuente"]
    assert respuestas["q4"]["capas"]["capa1"]["que_hacer"] is None


def test_verificacion_usuario_13_10(respuestas):
    """Verificación independiente de la respuesta por capas (13/10/2026): observaciones de presentación."""
    c3 = respuestas["q3"]["capas"]
    assert "solo de la municipalidad" in c3["capa1"]["cifra_clave"]["texto"]
    assert any("solo de la municipalidad" in x for x in c3["capa3"]["para_citar"])
    assert "registro de los niños medidos" in c3["capa1"]["confianza"]["texto"]
    assert "no encontramos" in c3["capa1"]["respuesta_corta"]
    assert not any("anemia" in t for t in c3["capa1"]["ojo_al_leer"])     # el «Ojo» no habla de cifras ocultas
    q4 = respuestas["q4"]["capas"]
    assert all("Fuente: INEI, Mapa de Pobreza" in x for x in q4["capa3"]["para_citar"] if "pobreza en 2018" in x
               or x.startswith("entre"))
    assert "(9,5" in respuestas["q2"]["capas"]["capa1"]["cifra_clave"]["fuente"].replace("\u202f", " ")
    assert not any("tamizaron" in x for x in respuestas["q2"]["capas"]["capa2"]["limites"])
