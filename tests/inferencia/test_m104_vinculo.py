"""M1-04, tarea 3 y 6: vínculo variable ↔ pregunta sin LLM (diccionario y expresiones regulares), motivos de «sin pregunta» y
preguntas candidatas para el LLM."""
from __future__ import annotations

from pap.inferencia.cuestionarios import Pregunta, VariableDic


def _p(cuest, num, texto, seccion="SECCIÓN 1", opciones=None):
    return Pregunta(cuest, num, texto, seccion, 1, opciones or [], [])


def _v(tabla, cod, etq, cats=None):
    return VariableDic(tabla, cod, etq, categorias=cats or [])


PREGUNTAS = [_p("salud", "25", "¿Cuántos años cumplidos tiene?"), _p("salud", "25C", "A continuación le haré algunas preguntas"),
             _p("individual", "105", "¿En qué día, mes y año nació?"), _p("individual", "333", "¿Tuvo molestias?")]


def test_el_codigo_dice_la_pregunta_y_se_usa_el_numero_mas_largo_que_exista():
    from pap.inferencia.cuestionarios import vincular_por_regla

    vs = [_v("CSALUD01", "QS25C1", "Algo de la 25C"), _v("CSALUD01", "QS25", "Edad"), _v("REC0111", "Q105DD", "Día de nacimiento"),
          _v("REC0111", "QD333_1", "Molestia"), _v("CSALUD01", "QS999", "No existe")]
    r = vincular_por_regla(vs, PREGUNTAS)
    assert r[("CSALUD01", "QS25C1")].pregunta_id == "salud:25C"
    assert r[("CSALUD01", "QS25")].pregunta_id == "salud:25"
    assert r[("REC0111", "Q105DD")].pregunta_id == "individual:105"
    assert r[("REC0111", "QD333_1")].pregunta_id == "individual:333"
    assert ("CSALUD01", "QS999") not in r                      # el número no existe en el cuestionario: no se inventa
    assert {v.metodo for v in r.values()} == {"regla"} and all(v.estado == "propuesto" for v in r.values())


def test_un_numero_de_cuatro_digitos_que_no_existe_no_se_recorta_a_otra_pregunta():
    from pap.inferencia.cuestionarios import vincular_por_regla

    r = vincular_por_regla([_v("REC93DVdisciplina", "Q1040A", "x")], PREGUNTAS + [_p("individual", "104", "otra pregunta")])
    assert r == {}                                              # «1040A» no se vuelve la 104


def test_una_regla_solo_vale_en_sus_tablas():
    from pap.inferencia.cuestionarios import vincular_por_regla

    r = vincular_por_regla([_v("REC0111", "QS25", "otra cosa")], PREGUNTAS)       # QS… solo vale en las tablas de salud
    assert r == {}


def test_el_diccionario_que_trae_el_numero_de_pregunta_vincula_por_diccionario():
    from pap.inferencia.cuestionarios import vincular_por_regla

    r = vincular_por_regla([_v("RECX", "ABC", "Edad (pregunta 105)")], PREGUNTAS, cuestionarios_de_tabla={"RECX": ["individual"]})
    assert r[("RECX", "ABC")].pregunta_id == "individual:105" and r[("RECX", "ABC")].metodo == "diccionario"


def test_variables_sin_pregunta_con_su_motivo():
    from pap.inferencia.cuestionarios import motivo_sin_pregunta

    assert motivo_sin_pregunta(_v("RECH6", "HHID", "Identificación Cuestionario Individual")) == "administrativa"
    assert motivo_sin_pregunta(_v("REC0111", "V011", "Fecha de nacimiento, Codificación centenaria de meses (CMC)")) == "construida"
    assert motivo_sin_pregunta(_v("REC0111", "V013", "Edad actual por grupos de 5 años")) == "construida"
    assert motivo_sin_pregunta(_v("RECH6", "HC57", "Nivel de anemia")) is None                  # no se adivina: va al LLM


def test_los_candidatos_traen_primero_la_pregunta_parecida_y_se_limitan_a_k():
    from pap.inferencia.cuestionarios import Candidatos

    pregs = [_p("individual", str(100 + i), f"¿pregunta de relleno número {i} sobre otra cosa?") for i in range(30)]
    pregs.append(_p("individual", "412", "¿Le hicieron la prueba de papanicolaou?", opciones=["1 SI", "2 NO"]))
    pregs.append(_p("salud", "412", "¿Le hicieron la prueba de papanicolaou?"))
    c = Candidatos(pregs)
    top = c.de(_v("REC95", "S412", "Prueba de Papanicolaou"), ["individual"], k=5)
    assert top[0].id == "individual:412" and len(top) == 5
    assert all(q.cuestionario == "individual" for q in top)                 # solo los cuestionarios de la tabla
    assert c.de(_v("X", "Y", "zzz qqq"), ["individual"], k=5)[0].cuestionario == "individual"      # sin parecido igual da candidatos


def test_la_tabla_de_vinculos_trae_la_referencia_y_el_texto_de_la_pregunta():
    import pytest

    from pap.errores import PapError
    from pap.inferencia.cuestionarios import Vinculo, tabla_de_vinculos, vincular_sin_llm

    qs = [Pregunta("salud", "25", "¿Cuántos años cumplidos tiene?", "SECCIÓN 1. HIPERTENSIÓN", 4)]
    vs = [_v("CSALUD01", "QS25", "Edad"), _v("CSALUD01", "HHID", "Identificación"), _v("CSALUD01", "QS40", "Otra cosa")]
    vin = vincular_sin_llm(vs, qs, {"CSALUD01": ["salud"]})
    assert [(v.codigo, v.metodo, v.motivo) for v in vin] == [("QS25", "regla", "salud"), ("HHID", "sin_pregunta", "administrativa")]
    df = tabla_de_vinculos(vin, qs)
    f = {r["codigo"]: r for r in df.iter_rows(named=True)}
    assert f["QS25"]["var_id"] == "ENDES·2024·CSALUD01·QS25" and f["QS25"]["pagina"] == 4 and f["QS25"]["texto_pregunta"].startswith("¿Cuántos")
    assert f["HHID"]["pregunta_id"] is None and f["HHID"]["motivo"] == "administrativa"
    with pytest.raises(PapError, match="no está entre las extraídas"):
        tabla_de_vinculos([Vinculo("T", "X", "salud:999", "llm")], qs)
