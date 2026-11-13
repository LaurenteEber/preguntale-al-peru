"""M1-04, tarea 3: la medición por tabla (diccionario y regex, sin LLM) y las variables de las recetas."""
from pap.inferencia.cuestionarios import Candidatos, Pregunta, VariableDic, Vinculo, vincular_por_regla
from pap.inferencia.cuestionarios_medicion import medir, recall_de_candidatos, variables_de_recetas


def _v(t, c, e):
    return VariableDic(t, c, e)


def test_la_medicion_separa_diccionario_regla_sin_pregunta_y_pendientes():
    vs = [_v("T", "QS25", "Edad"), _v("T", "AB", "Algo (pregunta 7)"), _v("T", "HHID", "Identificación"), _v("T", "V011", "Fecha (CMC)"),
          _v("T", "HC57", "Nivel de anemia")]
    vin = {("T", "QS25"): Vinculo("T", "QS25", "salud:25", "regla"), ("T", "AB"): Vinculo("T", "AB", "salud:7", "diccionario")}
    [f] = medir(vs, vin)
    assert (f.total, f.por_regla, f.por_diccionario, f.sin_pregunta_administrativa, f.sin_pregunta_construida, f.pendientes) == (5, 1, 1, 1, 1, 1)
    assert f.pct_sin_llm == 40.0 and f.por_llm is None
    [g] = medir(vs, vin, solo={("T", "HC57")})
    assert (g.total, g.pendientes) == (1, 1)


def test_las_variables_de_las_recetas_salen_de_los_yaml(tmp_path):
    import yaml
    (tmp_path / "curados/inferencia/recetas").mkdir(parents=True)
    (tmp_path / "curados/inferencia/recetas/r.yaml").write_text(yaml.safe_dump({
        "id": "r", "encuesta": "ENDES", "unidad": "nino", "universo_analitico": "u", "cortes_permitidos": ["sexo"],
        "indicador": {"condiciones": [{"archivo": "RECH6", "variable": "HC57", "op": "en", "valores": [1]}]},
        "universo": {"restricciones": [{"archivo": "RECH6", "variable": "HC1", "op": "entre", "valores": [6, 35]}]}}))
    (tmp_path / "curados/inferencia/universos_analiticos.yaml").write_text(yaml.safe_dump({"universos": [
        {"id": "u", "aplica_a": {"archivos": ["RECH6", "RECH1"]}, "predicados": [{"var": "HV103", "op": "en", "valores": [1]}]}]}))
    (tmp_path / "curados/inferencia/cortes_estandar.yaml").write_text(yaml.safe_dump({"cortes": [
        {"id": "sexo", "por_encuesta": {"ENDES": [{"archivo": "RECH6", "variable": "HC27", "unidad": "nino"},
                                                  {"archivo": "RECH1", "variable": "HV104", "unidad": "persona_del_hogar"}]}}]}))
    (tmp_path / "curados/inferencia/diseno_muestral.csv").write_text(
        "encuesta,anio,archivo,medicion,poblacion,peso_expr,estrato_expr,psu_expr\n"
        "ENDES,2024,RECH0,hogar,x,HV005/1e6,\"printf('%02d-%d', HV024, HV022)\",HV021\n")
    vs = [_v("RECH6", "HC57", ""), _v("RECH6", "HC1", ""), _v("RECH1", "HV103", ""), _v("RECH6", "HC27", ""), _v("RECH1", "HV104", ""),
          _v("RECH0", "HV005", ""), _v("RECH0", "HV024", ""), _v("RECH0", "HV022", ""), _v("RECH0", "HV021", ""), _v("RECH6", "HC99", "")]
    got = variables_de_recetas(tmp_path, vs)
    assert got == {("RECH6", "HC57"), ("RECH6", "HC1"), ("RECH1", "HV103"), ("RECH6", "HC27"),
                   ("RECH0", "HV005"), ("RECH0", "HV024"), ("RECH0", "HV022"), ("RECH0", "HV021")}


def test_recall_de_candidatos_se_mide_con_las_variables_de_respuesta_conocida():
    preg = [Pregunta("salud", "25", "¿Cuántos años cumplidos tiene?", "S", 1), Pregunta("salud", "26", "¿Fuma usted cigarrillos?", "S", 1),
            Pregunta("salud", "27", "¿Toma bebidas alcohólicas?", "S", 1)]
    vs = [_v("CSALUD01", "QS25", "Años cumplidos"), _v("CSALUD01", "QS26", "Fuma cigarrillos")]
    vin = vincular_por_regla(vs, preg)
    r = recall_de_candidatos(vs, vin, Candidatos(preg), {"CSALUD01": ["salud"]}, k=1)
    assert r == {"k": 1, "variables_con_respuesta_conocida": 2, "con_la_pregunta_entre_los_candidatos": 2, "porcentaje": 100.0}
