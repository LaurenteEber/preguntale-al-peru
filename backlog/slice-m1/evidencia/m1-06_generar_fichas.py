"""M1-06: script con que el agente escribió la primera versión de curados/inferencia/fichas/ENDES.yaml (evidencia). Los YAML son la fuente de verdad: desde aquí se editan a mano o se regeneran sabiendo que se pierden las ediciones. La ruta de la raíz es la de este repo."""
import yaml, sys
from collections import OrderedDict
from pathlib import Path
raiz = str(Path(__file__).resolve().parents[3])
desc = yaml.safe_load(open(f"{raiz}/curados/inferencia/descargas/endes_2024.yaml", encoding="utf-8"))
mod = {}
for m in desc["modulos"]:
    for t in m["tablas"]:
        mod[t.replace(" ", "_")] = m["recurso"]
DOC11 = {"RECH0":1,"RECHM":2,"RECH1":3,"RECH4":4,"RECH23":5,"RECH5":6,"RECH6":7,"Programas_Sociales_x_Hogar":8,"PS_BECA18":9,"PS_COMEDOR":10,"PS_PENSION65":11,"PS_QALIWARMA":12,"PS_WAWAWASI":13,"PS_VL":14,"PS_TRABAJA":15,"REC0111":16,"REC21":17,"RE223132":18,"REC41":19,"REC42":20,"REC43":21,"REC44":22,"RE516171":23,"RE758081":24,"REC82":25,"REC83":26,"REC84DV":27,"REC91":28,"REC93DVdisciplina":29,"REC94":30,"REC95":31,"DIT":32,"CSALUD01":33,"CSALUD08":34}
CUEST = {"hogar": "endes-2024-cuestionario-hogar", "individual": "endes-2024-cuestionario-individual", "salud": "endes-2024-cuestionario-salud"}
MIEMBRO = {"Programas_Sociales_x_Hogar": "Diccionario - Programas Sociales x Hogar.pdf"}

# (tabla): dict de campos a mano. poblacion: texto, sujeto, edad_min, edad_max, edad_unidad, sexo, condicion, variable_edad
T = OrderedDict()
def add(t, nombre, desc_, cuest, secs, tipo, pob, quien, informante, modo, avisos=(), paginas=None):
    T[t] = dict(nombre_corto=nombre, descripcion=desc_, cuestionario=cuest, secciones=list(secs), tipo_tabla=tipo, poblacion=pob,
                quien_tiene_fila=quien, informante=informante, modo=modo, avisos=list(avisos), paginas=paginas)
P = lambda texto, sujeto, **kw: dict(texto=texto, sujeto=sujeto, **kw)
HOGAR_POB = "hogares particulares (residentes habituales y quienes pernoctaron la noche anterior)"
PERS_HOGAR = P("todas las personas del listado del hogar", "persona", edad_min=0, edad_unidad="anios", sexo="ambos", condicion="residentes habituales y visitantes que pernoctaron", variable_edad="HV105")

add("RECH0","Hogares de la muestra","Un registro por hogar: identificación, tamaño, número de personas elegibles, resultado de la entrevista y datos de la muestra.","hogar",["Sección 1. Características de los miembros del hogar"],"base",
    P(HOGAR_POB,"hogar"),"cada hogar de la muestra","persona adulta del hogar que responde por todos","declarado",paginas="Sección 1: pp. 2–6")
add("RECHM","Muertes en el hogar desde enero de 2019","Personas que vivían en el hogar y fallecieron: sexo, edad al morir, mes y año, y si fue por causas relacionadas con el embarazo.","hogar",["Sección 1. Características de los miembros del hogar"],"lista",
    P("personas del hogar fallecidas (mortalidad general y materna)","persona",sexo="ambos",condicion="fallecidas desde enero de 2019"),"cada persona que vivía en el hogar y falleció desde enero de 2019 (hasta 4 por hogar)","persona adulta del hogar","declarado",paginas="Sección 1: p. 6")
add("RECH1","Personas del hogar","Listado de las personas del hogar: parentesco, sexo, edad, educación, asistencia a la escuela, orden de la madre y del padre.","hogar",["Sección 1. Características de los miembros del hogar"],"lista",
    PERS_HOGAR,"cada persona del listado del hogar","persona adulta del hogar que responde por todos","declarado",paginas="Sección 1: pp. 2–6")
add("RECH4","Seguro de salud, actividad y educación de las personas del hogar","Por persona del hogar: qué seguros de salud tiene, actividad de la última semana, nivel de educación aprobado y al que asiste.","hogar",["Sección 1. Características de los miembros del hogar"],"detalle",
    P("todas las personas del listado del hogar","persona",sexo="ambos"),"cada persona del listado del hogar","persona adulta del hogar que responde por todos","declarado",paginas="Sección 1: pp. 2–6")
add("RECH23","Vivienda, servicios y bienes del hogar","Características de la vivienda (agua, saneamiento, materiales, combustible), bienes del hogar, índice de riqueza y región natural.","hogar",["Sección 2. Características de la vivienda","Sección 6. Prueba de yodo en la sal y de cloro residual en el agua"],"detalle",
    P(HOGAR_POB,"hogar"),"cada hogar de la muestra","persona adulta del hogar; la prueba de yodo y de cloro la hace el personal de campo","mixto",paginas="Sección 2: pp. 7–10; Sección 6: pp. 15–16")
add("RECH5","Peso, talla, hemoglobina y VIH de mujeres","Mediciones de las mujeres del hogar: edad, peso, talla, hemoglobina (ajustada por altitud), nivel de anemia, resultado de la prueba de VIH y educación.","hogar",["Sección 4. Peso y talla (formulario de tabla)","Sección 5. Prueba de hemoglobina"],"medicion",
    P("mujeres de 12 a 49 años del hogar","mujer",edad_min=12,edad_max=49,edad_unidad="anios",sexo="mujer",condicion="listadas en el hogar",variable_edad="HA1"),"cada mujer de 12 a 49 años listada en el hogar, con o sin medición","personal de campo (medición)","medido",paginas="Sección 5: p. 14")
add("RECH6","Peso, talla y hemoglobina de niñas y niños","Mediciones de los menores del hogar: edad en meses, peso, talla, indicadores de talla y peso para la edad, hemoglobina (ajustada por altitud) y nivel de anemia.","hogar",["Sección 4. Peso y talla (formulario de tabla)","Sección 5. Prueba de hemoglobina"],"medicion",
    P("niñas y niños menores de 5 años (0 a 59 meses)","nino",edad_min=0,edad_max=59,edad_unidad="meses",sexo="ambos",condicion="listados en el hogar",variable_edad="HC1"),"todos los menores de 5 años listados, con o sin medición","personal de campo (medición)","medido",
    avisos=["La ficha técnica (p. 9) describe el registro como «niños menores de 6 años»; en los datos de 2024 las edades van de 0 a 59 meses (menores de 5 años)."],paginas="Sección 5: p. 14")
add("Programas_Sociales_x_Hogar","Programas sociales del hogar","Si algún miembro del hogar es beneficiario de Beca 18, Trabaja Perú, Juntos, Pensión 65, Vaso de Leche, comedor popular o Wawa Wasi / Cuna Más.","hogar",["Sección 3A. Programas sociales no alimentarios","Sección 3.B Programas sociales alimentarios"],"detalle",
    P(HOGAR_POB,"hogar"),"cada hogar de la muestra con la sección de programas sociales (34 018 de 37 390)","persona adulta del hogar","declarado",paginas="Sección 3A: p. 11; Sección 3.B: p. 12")
for t, prog in (("PS_BECA18","Beca 18"),("PS_COMEDOR","comedor popular"),("PS_PENSION65","Pensión 65"),("PS_QALIWARMA","Qali Warma"),("PS_TRABAJA","Trabaja Perú"),("PS_VL","Vaso de Leche"),("PS_WAWAWASI","Wawa Wasi / Cuna Más")):
    sec = ["Sección 3A. Programas sociales no alimentarios"] if t in ("PS_BECA18","PS_PENSION65","PS_TRABAJA") else ["Sección 3.B Programas sociales alimentarios"]
    pg = "Sección 3A: p. 11" if t in ("PS_BECA18","PS_PENSION65","PS_TRABAJA") else "Sección 3.B: p. 12"
    add(t,f"Beneficiarios de {prog}",f"Personas del hogar que son beneficiarias de {prog}: desde cuándo y quién más del hogar lo es.","hogar",sec,"detalle",
        P(f"personas del hogar beneficiarias de {prog}","persona",sexo="ambos"),f"cada persona del hogar que recibe {prog} (puede haber varias por hogar)","persona adulta del hogar","declarado",paginas=pg)
Q_IND = "mujer entrevistada"
MUJ = lambda texto, **kw: P(texto, "mujer", edad_min=12, edad_max=49, edad_unidad="anios", sexo="mujer", **kw)
add("REC0111","Mujeres de 12 a 49 años: datos básicos","Registro de cada mujer elegible: identificación, resultado de la entrevista individual, edad, educación, religión, etnicidad, vivienda y riqueza del hogar.","individual",["Sección 1. Antecedentes de la entrevistada"],"base",
    MUJ("mujeres de 12 a 49 años (residentes habituales o visitantes que pernoctaron)",condicion="elegibles para la entrevista individual",variable_edad="V012"),"cada mujer elegible, haya completado o no la entrevista (la completaron 34 252 de 37 117)","la mujer entrevistada","declarado",paginas="Sección 1: pp. 5–7")
add("REC21","Historia de nacimientos de la mujer","Un registro por cada hijo nacido vivo de la mujer: fecha de nacimiento, sexo, si vive, edad actual o a la muerte, intervalo y si está listado en el hogar.","individual",["Sección 2. Reproducción"],"lista",
    P("hijos nacidos vivos de las mujeres de 12 a 49 años","nino",sexo="ambos",condicion="nacidos vivos de la mujer entrevistada, de cualquier año"),"cada hijo nacido vivo de cada mujer con historia de nacimientos","la mujer entrevistada","declarado",paginas="Sección 2: pp. 8–14")
add("REC41","Embarazo, parto y lactancia de los nacimientos de los últimos cinco años","Control prenatal, atención del parto, lactancia, amenorrea y abstinencia, y control después del parto, de cada uno de los nacimientos de los últimos cinco años (hasta cuatro por mujer; MIDX va de 1 a 4, empezando por el último nacimiento).","individual",["Sección 4A. Embarazo, parto, puerperio y lactancia"],"detalle",
    P("hijos nacidos vivos en los últimos cinco años","nino",edad_min=0,edad_max=59,edad_unidad="meses",sexo="ambos",condicion="nacidos en los últimos cinco años de las mujeres entrevistadas"),"cada nacimiento de los últimos cinco años de cada mujer (19 751)","la mujer entrevistada","declarado",paginas="Sección 4A: pp. 22–30")
add("REC42","Mujer: lactancia actual, mediciones y conocimientos varios","Datos de la mujer: si amamanta ahora, alimentos que dio ayer al último hijo, peso y talla de la mujer, hemoglobina, mosquiteros, tuberculosis, seguro de salud y otros.","individual",["Sección 4A. Embarazo, parto, puerperio y lactancia","Sección 4B. Inmunización y salud"],"detalle",
    MUJ("mujeres de 12 a 49 años con entrevista individual completa",condicion="entrevista individual completa",variable_edad="V447A"),"cada mujer con entrevista individual completa (34 252)","la mujer entrevistada; peso, talla y hemoglobina los mide el personal de campo","mixto",paginas="Sección 4A: pp. 22–30; Sección 4B: pp. 31–55")
add("REC43","Vacunas, diarrea, fiebre y tos de niñas y niños","Carné y vacunas, diarrea en las dos últimas semanas y su tratamiento, fiebre y tos, vitamina A, hierro y desparasitación de cada nacimiento de los últimos cinco años (HIDX va de 1 a 4, empezando por el último).","individual",["Sección 4B. Inmunización y salud"],"detalle",
    P("hijos menores de 5 años de las mujeres entrevistadas","nino",edad_min=0,edad_max=59,edad_unidad="meses",sexo="ambos",condicion="nacidos en los últimos cinco años"),"cada hijo menor de 5 años de cada mujer entrevistada (19 751)","la madre","declarado",
    avisos=["La etiqueta del archivo de H12A está dañada («Busco D97:D148 para la diarrea: hospital MINSA»; debería decir «Buscó tratamiento para la diarrea: hospital MINSA»). Es la etiqueta original del INEI: no se corrige en el índice (etiqueta_original), solo se anota."],paginas="Sección 4B: pp. 31–55")
add("REC44","Peso, talla y hemoglobina de los hijos de la mujer","Mediciones de los hijos menores de 5 años de las mujeres entrevistadas: edad, peso, talla, indicadores de crecimiento y hemoglobina.","individual",["Sección 4B. Inmunización y salud"],"medicion",
    P("hijos menores de 5 años de las mujeres entrevistadas","nino",edad_min=0,edad_max=59,edad_unidad="meses",sexo="ambos",condicion="nacidos en los últimos cinco años",variable_edad="HW1"),"cada hijo menor de 5 años de cada mujer entrevistada, con o sin medición (19 751)","personal de campo (medición)","medido",paginas="Sección 4B: pp. 31–55")
add("REC82","Calendario mensual de la mujer","Una fila por cada columna del calendario de la mujer (mes a mes): historia de embarazos, anticoncepción y otros hechos.","individual",["Calendario de la mujer"],"calendario",
    MUJ("mujeres de 12 a 49 años con entrevista individual completa",condicion="entrevista individual completa"),"cada columna del calendario de cada mujer entrevistada (171 260 filas de 34 252 mujeres)","la mujer entrevistada","declarado",
    avisos=["La columna VCAL junta todo el calendario en un solo texto; no se separa mes a mes en el índice."],paginas="Calendario: pp. 89–90")
add("REC83","Hermanas y hermanos de la mujer (mortalidad materna)","Una fila por hermana u hermano de la mujer: sexo, si vive, edad actual o al morir, año de la muerte y si fue por embarazo o parto.","individual",["Sección 9. Mortalidad materna"],"lista",
    P("hermanas y hermanos de las mujeres entrevistadas","hermano",sexo="ambos"),"cada hermana o hermano nacido de la misma madre que la mujer (141 805 de 33 276 mujeres)","la mujer entrevistada","declarado",paginas="Sección 9: pp. 70–71")
add("REC84DV","Violencia contra la mujer","Violencia emocional, física y sexual de la pareja y de otras personas, consecuencias, búsqueda de ayuda y violencia en el embarazo.","individual",["Sección 10. Violencia doméstica"],"detalle",
    MUJ("mujeres de 12 a 49 años con entrevista individual completa (se contesta en las seleccionadas para el módulo de violencia)",condicion="seleccionadas para el módulo de violencia familiar"),"cada mujer con entrevista individual completa (34 252); las preguntas de violencia las contestan 20 398","la mujer entrevistada (a solas)","declarado",
    avisos=["La tabla trae 34 252 filas pero solo 20 398 tienen respuestas de violencia: las demás no fueron seleccionadas para el módulo.","Las mujeres seleccionadas para el módulo tienen de 15 a 49 años (observado en los datos), aunque la tabla describe a las de 12 a 49."],paginas="Sección 10: pp. 72–81")
add("REC91","Mujer: módulo de preguntas adicionales","Preguntas propias de la ENDES 2024: educación, lengua materna y etnia, control del embarazo y seguro, anticoncepción, programas sociales, lavado de manos, alimentación del niño, ITS, violencia y castigo infantil.","individual",["Varias secciones del cuestionario individual"],"detalle",
    MUJ("mujeres de 12 a 49 años (residentes habituales o visitantes que pernoctaron)",condicion="elegibles para la entrevista individual"),"cada mujer elegible (37 117), haya completado o no la entrevista","la mujer entrevistada","declarado",
    avisos=["El tema de la tabla era «por confirmar» en fichas.md §8; se reparte en bloques de salud, familia, violencia e identidad."])
add("REC93DVdisciplina","Disciplina y castigo de los hijos","Quién corrige a cada niño, cómo, y si el niño estuvo presente en situaciones de violencia en el hogar.","individual",["Sección 10. Violencia doméstica"],"detalle",
    P("hijos de las mujeres entrevistadas sobre los que se pregunta la disciplina","nino",sexo="ambos"),"cada niño sobre el que se preguntó la disciplina (15 462 filas de 13 938 mujeres)","la madre","declarado",
    avisos=["341 filas no tienen a la mujer en REC0111 (C-M0-05-2): se excluyen de todo cálculo de disciplina infantil, con nota (decisión del dueño, 12/11/2026)."],paginas="Sección 10: pp. 72–81")
add("REC94","Control prenatal, lactancia y alimentación de los nacimientos de los últimos cinco años","De cada nacimiento de los últimos cinco años (IDX94 va de 1 a 4, empezando por el último): meses de embarazo en los controles y pruebas, hierro, complicaciones del parto, seguro, inscripción del niño, lactancia y preparación de alimentos.","individual",["Sección 4A. Embarazo, parto, puerperio y lactancia"],"detalle",
    P("hijos nacidos vivos en los últimos cinco años","nino",edad_min=0,edad_max=59,edad_unidad="meses",sexo="ambos",condicion="nacidos en los últimos cinco años"),"cada nacimiento de los últimos cinco años de cada mujer (19 751)","la mujer entrevistada","declarado",paginas="Sección 4A: pp. 22–30")
add("REC95","Vacunas con fechas, controles de crecimiento, anemia y suplementos","Fechas de cada vacuna del carné, controles de crecimiento (CRED), diarrea día a día, hierro y micronutrientes y sus entregas.","individual",["Sección 4B. Inmunización y salud"],"detalle",
    P("hijos menores de 5 años de las mujeres entrevistadas","nino",edad_min=0,edad_max=59,edad_unidad="meses",sexo="ambos",condicion="nacidos en los últimos cinco años"),"cada hijo menor de 5 años de cada mujer entrevistada (19 751)","la madre; las fechas se copian del carné","mixto",paginas="Sección 4B: pp. 31–55")
add("DIT","Desarrollo infantil temprano","Preguntas sobre juego, lenguaje, comportamiento y materiales de aprendizaje en casa para niñas y niños de 9 a 71 meses.","individual",["Sección 4B. Inmunización y salud"],"detalle",
    P("niñas y niños de 9 a 71 meses","nino",edad_min=9,edad_max=71,edad_unidad="meses",sexo="ambos",condicion="hijos de las mujeres entrevistadas",variable_edad="QI478"),"cada niña o niño de 9 a 71 meses seleccionado (19 245)","la madre o cuidadora","declarado",paginas="Sección 4B: pp. 31–55")
add("RE223132","Fecundidad, embarazo actual y anticoncepción","Hijos nacidos, embarazo actual y pérdidas, conocimiento y uso de métodos anticonceptivos, fuentes y razones para no usarlos.","individual",["Sección 2. Reproducción","Sección 3. Anticoncepción"],"detalle",
    MUJ("mujeres de 12 a 49 años con entrevista individual completa",condicion="entrevista individual completa"),"cada mujer con entrevista individual completa (34 252)","la mujer entrevistada","declarado",paginas="Sección 2: pp. 8–14; Sección 3: pp. 15–21")
add("RE516171","Unión, preferencias de fecundidad y trabajo de la pareja","Estado civil, primera relación sexual, deseo de hijos, necesidad insatisfecha de planificación, nivel educativo y trabajo del esposo o compañero, decisiones en el hogar.","individual",["Sección 5. Nupcialidad","Sección 6. Preferencias de fecundidad","Sección 7. Antecedentes del cónyuge y trabajo de la mujer"],"detalle",
    MUJ("mujeres de 12 a 49 años con entrevista individual completa",condicion="entrevista individual completa"),"cada mujer con entrevista individual completa (34 252)","la mujer entrevistada","declarado",paginas="Sección 5: pp. 56–59; Sección 6: pp. 60–63; Sección 7: pp. 64–65")
add("RE758081","VIH/SIDA, otras ITS y conductas sexuales","Conocimiento sobre el VIH y otras ITS, uso de condón, parejas sexuales, pruebas de VIH, estigma y actitudes.","individual",["Sección 8. SIDA y otras I.T.S."],"detalle",
    MUJ("mujeres de 12 a 49 años con entrevista individual completa",condicion="entrevista individual completa"),"cada mujer con entrevista individual completa (34 252)","la mujer entrevistada","declarado",paginas="Sección 8: pp. 66–69")
add("CSALUD01","Salud de una persona de 15 años a más por hogar","Hipertensión y diabetes, factores de riesgo (tabaco, alcohol, frutas y verduras), salud ocular y bucal, prevención del cáncer, tuberculosis, VIH, salud mental y mediciones.","salud",["Secciones 1 a 7 y 9 del cuestionario de salud"],"detalle",
    P("una persona de 15 años a más seleccionada por hogar","adulto",edad_min=15,edad_unidad="anios",sexo="ambos",condicion="seleccionada para el cuestionario de salud",variable_edad="QS23"),"cada hogar con persona seleccionada (34 018 de 37 390)","la persona seleccionada","mixto",
    avisos=["El documento «Identificadores de las bases de datos» (fila 33) da la llave HHID + QSNUMERO; el índice declara HHID y se comprobó que es única (34 018 filas, 34 018 hogares): consulta C-M1-06-1."],paginas="Sección 1: pp. 4–5; Sección 2: pp. 6–7; Sección 3: pp. 8–9; Sección 4: pp. 10–11; Sección 5: p. 12; Sección 6: p. 13; Sección 7: pp. 14–18; Sección 9: p. 31")
add("CSALUD08","Salud bucal, ocular y mental de niñas y niños","Atención y cuidado de los dientes, problemas de visión y uso de lentes, hábitos de pantalla y lectura, y asistencia a la escuela y apoyo ante la violencia en el colegio (QS833 a QS838) de niñas y niños menores de 12 años.","salud",["Sección 8. Salud bucal, ocular y mental en niñas y niños"],"detalle",
    P("niñas y niños menores de 12 años","nino",edad_min=0,edad_max=11,edad_unidad="anios",sexo="ambos",condicion="listados en el hogar",variable_edad="QS802D"),"cada niña o niño menor de 12 años seleccionado (41 309 en 24 172 hogares)","la persona responsable de la niña o el niño","declarado",paginas="Sección 8: pp. 19–29")

bloque_doc = {}
out = ["# Fichas de tabla de la ENDES 2024: los campos a mano (M1-06, tarea 2; docs/diseno/fichas.md §5.1).",
       "# Las escribió el agente (estado `propuesto`) leyendo el diccionario de cada tabla, los cuestionarios (M1-04) y el documento n.º 11",
       "# «Identificadores de las bases de datos» (recurso endes-2024-identificadores-bd); la población (edad y sexo) se comprobó contra los datos",
       "# con `pap fichas validar` (regla 6). `variable_edad` (agregado, M1-06-s3) es la columna de edad con que se comprueba. Lo que no aplica va",
       "# vacío, nunca inventado. Los derivados (módulo, huella, llave, uniones, diseño, bloques…) los arma `pap fichas generar`. El auditor-agente",
       "# revisa cada ficha contra el diccionario (evidencia/m1-06_revision.md) y el dueño da el visto por lote.", ""]
doc = OrderedDict()
doc["version"] = "0.1.0"
doc["fecha"] = "2026-11-12"
doc["encuesta"] = "ENDES"
doc["tipo_fuente"] = "muestra"
doc["vocabularios"] = OrderedDict(cuestionario=["hogar","individual","salud"], sujeto=["hogar","persona","adulto","mujer","madre","embarazo","nino","hermano"])
tablas = OrderedDict()
for t, d in T.items():
    docs = [OrderedDict(recurso=mod[t], miembro=MIEMBRO.get(t, f"Diccionario - {t}.pdf"))]
    q = OrderedDict(recurso=CUEST[d["cuestionario"]])
    if d["paginas"]: q["paginas"] = d["paginas"]
    docs.append(q)
    docs.append(OrderedDict(recurso="endes-2024-identificadores-bd", paginas=f"fila {DOC11[t]} de la tabla de identificadores"))
    f = OrderedDict(anios=[2024,2024], nombre_corto=d["nombre_corto"], descripcion=d["descripcion"], cuestionario=d["cuestionario"], secciones=d["secciones"],
                    tipo_tabla=d["tipo_tabla"], poblacion=OrderedDict((k, v) for k, v in d["poblacion"].items()), quien_tiene_fila=d["quien_tiene_fila"],
                    informante=d["informante"], modo=d["modo"], avisos=d["avisos"], documentos=docs, estado="propuesto")
    tablas[t] = f
doc["tablas"] = tablas
class D(yaml.SafeDumper):
    pass
D.add_representer(OrderedDict, lambda dumper, data: dumper.represent_mapping("tag:yaml.org,2002:map", data.items()))
open(f"{raiz}/curados/inferencia/fichas/ENDES.yaml","w",encoding="utf-8").write("\n".join(out) + yaml.dump(doc, Dumper=D, allow_unicode=True, sort_keys=False, width=140))
print(len(tablas))
