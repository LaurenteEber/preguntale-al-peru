"""M1-04: lo extraído se guarda y se vuelve a leer igual (Parquet fuera de git)."""
from pap.inferencia.cuestionarios import (Pregunta, VariableDic, guardar_cuestionarios, guardar_diccionarios, leer_cuestionarios,
                                          leer_diccionarios, var_id)


def test_ida_y_vuelta_de_preguntas_y_diccionarios(tmp_path):
    qs = {"hogar": [Pregunta("hogar", "49", "¿Qué tipo de envase?", "SECCIÓN 2", 8, ["01 OLLA"], ["50"])],
          "individual": [Pregunta("individual", "325B", "¿Qué método quería?", "SECCIÓN 3", 20)],
          "salud": []}
    guardar_cuestionarios(qs, tmp_path)
    leidas = leer_cuestionarios(tmp_path)
    assert [q.id for q in leidas] == ["hogar:49", "individual:325B"]
    assert leidas[0].opciones == ["01 OLLA"] and leidas[0].saltos == ["50"] and leidas[0].pagina == 8
    vs = [VariableDic("RECH6", "HC57", "Nivel de anemia", "1:4", "", [("1", "Grave")], 31)]
    guardar_diccionarios(vs, {"RECH6": ["hogar", "individual"]}, tmp_path)
    vs2, cuests = leer_diccionarios(tmp_path)
    assert vs2 == vs and cuests == {"RECH6": ["hogar", "individual"]}


def test_la_llave_de_la_variable_es_la_del_indice():
    assert var_id("RECH6", "HC57") == "ENDES·2024·RECH6·HC57"
