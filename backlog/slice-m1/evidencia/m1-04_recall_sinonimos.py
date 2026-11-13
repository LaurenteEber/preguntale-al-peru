"""M1-04, §0.4: recall del recorte de candidatas ANTES y DESPUÉS de los sinónimos (dueño, 13/11/2026). Sin LLM, sin red.
Uso: `uv run python backlog/slice-m1/evidencia/m1-04_recall_sinonimos.py`.

«Antes» = la misma configuración sin `cuestionarios.sinonimos`; «después» = la del YAML. `candidatos_k` (20) no cambia.

Tres conjuntos:
1. las 319 variables vinculadas por la regla del código (pregunta conocida por el número del código);
2. la muestra de 14 de REC0111 de §0.2 (`m1-04_recall.py`);
3. la muestra NUEVA (abajo), distinta de las 14.

**Cómo se eligió la muestra nueva.** Se listaron las variables del diccionario cuya etiqueta habla de edad, fecha de nacimiento, día, mes o año
(`edad|años cumplidos|nacimiento|nació|mes|año|día|fecha`) y de ellas se tomaron solo las que NO están en las 14 y cuya pregunta se puede
leer en el texto del cuestionario extraído (no por el código ni por parecido de etiqueta): la etiqueta de la variable y la pregunta
dicen lo mismo. Se agregaron algunos controles que no son de edad ni fechas (QS24, QS26, QS27, V702) para ver que los sinónimos no los
perjudican. Quedaron fuera por no ser seguras: las variables construidas (REC21.B3, CMC), las fechas del carné de vacunas (REC43 H2D…,
REC95: la pregunta de cada dosis no está separada en el cuestionario extraído), las del calendario y las que dependen de la matriz del
hogar salvo HV105 (la columna «¿Cuántos años cumplidos tiene?» de la página M2 del listado del hogar). Las de bloque (REC21.BD/B1/B2/B8)
apuntan a la pregunta extraída 211, que contiene las preguntas 212 a 219 del historial de nacimientos (incluye «¿En qué día, mes y año
nació (NOMBRE)?» y «¿Cuántos años cumplidos tiene?»)."""
import importlib.util
from pathlib import Path

from pap.config import Rutas
from pap.inferencia import cuestionarios as c
from pap.inferencia import cuestionarios_medicion as m

AQUI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("m104_recall", AQUI / "m1-04_recall.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
MUESTRA_14 = _mod.MUESTRA

MUESTRA_NUEVA = {
    ("REC21", "BD"): "individual:211", ("REC21", "B1"): "individual:211", ("REC21", "B2"): "individual:211", ("REC21", "B8"): "individual:211",
    ("RECH1", "HV105"): "hogar:M2",
    ("CSALUD01", "QSDIA"): "salud:22", ("CSALUD01", "QS22M"): "salud:22", ("CSALUD01", "QS22A"): "salud:22", ("CSALUD01", "QS23"): "salud:23",
    ("RE516171", "V507"): "individual:509", ("RE516171", "V508"): "individual:509", ("RE516171", "V730"): "individual:702",
    ("REC41", "M1B"): "individual:419", ("REC41", "M1C"): "individual:419",
    # controles (no son de edad ni de fechas)
    ("CSALUD01", "QS24"): "salud:24", ("CSALUD01", "QS26"): "salud:26", ("CSALUD01", "QS27"): "salud:27", ("RE516171", "V702"): "individual:704",
}


def _cfg_sin_sinonimos() -> dict:
    return {k: v for k, v in c._config().items() if k != "sinonimos"}


if __name__ == "__main__":
    R = Rutas(AQUI.parents[2])
    d = c.carpeta_cuestionarios(R)
    qs = c.leer_cuestionarios(d)
    vs, cu = c.leer_diccionarios(d)
    vin = {(v.tabla, v.codigo): v for v in c.vincular_sin_llm(vs, qs, cu)}
    antes, despues = c.Candidatos(qs, _cfg_sin_sinonimos()), c.Candidatos(qs)
    k = m.k_candidatos()
    print(f"k = {k}")
    for nombre, cand in (("antes", antes), ("después", despues)):
        r = m.recall_de_candidatos(vs, vin, cand, cu, k)
        print(f"regla ({nombre}): {r['con_la_pregunta_entre_los_candidatos']}/{r['variables_con_respuesta_conocida']} = {r['porcentaje']} %")
    for titulo, muestra in (("14 de REC0111 (§0.2)", MUESTRA_14), ("muestra nueva", MUESTRA_NUEVA)):
        a, b = (m.recall_de_muestra(vs, muestra, cand, cu, k) for cand in (antes, despues))
        print(f"\n{titulo}: antes {a['entre_los_candidatos']}/{a['total']} = {a['porcentaje']} %; después {b['entre_los_candidatos']}/{b['total']} = {b['porcentaje']} %")
        print("| Variable | Etiqueta | Pregunta | Puesto antes | Puesto después | ¿Entre las 20 antes? | ¿Entre las 20 después? |\n|---|---|---|---|---|---|---|")
        for fa, fb in zip(a["filas"], b["filas"]):
            sn = lambda x: "sí" if x else "no"
            print(f"| {fa['variable']} | {fa['etiqueta'][:48]} | {fa['pregunta']} | {fa['puesto']} | {fb['puesto']} | {sn(fa['entre_los_candidatos'])} | {sn(fb['entre_los_candidatos'])} |")
        faltan = [f"{t}.{v}" for (t, v) in muestra if (t, v) not in {(x.tabla, x.codigo) for x in vs}]
        if faltan:
            print("NO ESTÁN EN EL DICCIONARIO:", faltan)
