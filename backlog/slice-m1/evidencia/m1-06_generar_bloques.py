"""M1-06: script con que el agente escribió la primera versión de curados/inferencia/bloques/ENDES.yaml (evidencia). Los YAML son la fuente de verdad: desde aquí se editan a mano o se regeneran sabiendo que se pierden las ediciones. La ruta de la raíz es la de este repo."""
import yaml
from collections import OrderedDict
from pathlib import Path
raiz = str(Path(__file__).resolve().parents[3])
fichas = yaml.safe_load(open(f"{raiz}/curados/inferencia/fichas/ENDES.yaml", encoding="utf-8"))["tablas"]
B = []
def b(tabla, slug, nombre, desc, tema, sub, papel, ventana=None, pob=None, **spec):
    spec = {k: v for k, v in spec.items() if v}
    B.append(dict(tabla=tabla, slug=slug, nombre=nombre, desc=desc, tema=tema, sub=sub, papel=papel, ventana=ventana, pob=pob or {}, spec=spec))
R = lambda a, z: [a, z]
HV, CO, CF, SV, RC, SALUD = "hogar_vivienda", "composicion_hogar", "campo_y_muestra", "servicio", "resultado", "contexto"
ID = "identificacion_encuesta"

# ---------------------------------------------------------------- RECH0
t = "RECH0"
b(t,"composicion","Tamaño y composición del hogar","Total de personas, mujeres y hombres elegibles, miembros residentes y presentes, y niños menores de 5 años.",HV,CO,SALUD,rango=R("HV009","HV014"))
b(t,"resultado_entrevista","Resultado de la entrevista del hogar y visitas","Si se completó la entrevista del hogar y cuántas visitas hicieron falta.",ID,CF,SALUD,rango=R("HV015","HV017"))
b(t,"muestra_dominio","Muestra, dominio y lugar de residencia","Marcas de la muestra: alguna vez en unión, dominio, lugar de residencia y selección para hombres.",ID,CF,SALUD,rango=R("HV020","HV027"))
b(t,"selecciones","Selección de niños y mujeres para mediciones y módulos, y altitud","Cuántos niños y mujeres se miden, qué hogares tienen hemoglobina, módulo de mujeres y de violencia, y altitud del conglomerado.",ID,CF,SALUD,rango=R("HV035","HV044"))
# ---------------------------------------------------------------- RECH1
t = "RECH1"
b(t,"parentesco_presencia","Parentesco con el jefe del hogar y presencia en el hogar","Parentesco, si vive habitualmente en el hogar y si durmió allí anoche.",HV,CO,SALUD,rango=R("HV101","HV103"))
b(t,"sexo_edad","Sexo y edad de las personas del hogar","Sexo y edad en años de cada persona del listado.",HV,CO,SALUD,rango=R("HV104","HV105"))
b(t,"educacion_alcanzada","Educación alcanzada","Nivel y año o grado más alto aprobado, años de estudio y nivel educativo alcanzado.","educacion","nivel_educativo_asistencia",RC,rango=R("HV106","HV109"))
b(t,"asistencia_escolar","Asistencia a la escuela","Si asiste ahora, a qué nivel y grado asiste o asistió el año pasado, y condición de asistencia.","educacion","nivel_educativo_asistencia",RC,lista=["HV110"],rango=R("HV121","QH21A"))
b(t,"padres","Madre y padre: si viven y su número de orden","Si la madre y el padre naturales están vivos y su número de orden en el hogar.",HV,CO,SALUD,rango=R("HV111","HV114"))
b(t,"estado_civil","Estado civil o conyugal","Estado civil actual y si estuvo unida anteriormente.","familia_pareja","union_convivencia",SALUD,rango=R("HV115","HV116"))
b(t,"elegibilidad","Elegibilidad para entrevistas y mediciones","Si la persona es elegible para la entrevista de mujeres, de hombres o para peso y talla.",ID,CF,SALUD,rango=R("HV117","HV120"))
b(t,"nacionalidad","Nacionalidad y tiempo de residencia en el Perú","Si vive permanentemente en el Perú y desde qué mes y año.",HV,CO,SALUD,rango=R("QH25B","QH25CA"))
# ---------------------------------------------------------------- RECH4
t = "RECH4"
b(t,"seguro_salud","Seguro de salud de las personas del hogar","Qué seguros tiene cada persona (EsSalud, militar, SIS, privado, otros) y si alguno está a su nombre.","acceso_salud","seguro_salud",SV,rango=R("SH11A","SH12"))
b(t,"actividad","Actividad de la última semana","A qué se dedicó la persona la última semana.","trabajo","actividad_ocupacion",SALUD,ventana="última semana",lista=["SH13"])
b(t,"educacion_aprobada","Nivel de educación aprobado","Nivel, años y grados de educación aprobados.","educacion","nivel_educativo_asistencia",RC,rango=R("SH15N","SH15G"))
b(t,"educacion_actual","Nivel de educación al que asiste ahora","Nivel, año y grado al que asiste o se matriculó este año.","educacion","nivel_educativo_asistencia",RC,rango=R("SH18N","SH18G"))
b(t,"educacion_anio_pasado","Educación el año pasado","Nivel, año y grado al que asistió el año pasado y resultado del año escolar.","educacion","nivel_educativo_asistencia",RC,rango=R("SH20N","SH21"))
# ---------------------------------------------------------------- RECH23
t = "RECH23"
b(t,"agua_acceso","Fuente de agua, tiempo para obtenerla y pago","Fuente principal de agua para beber y otros usos, tiempo para ir a buscarla, ubicación, quién recoge, disponibilidad y pago.",HV,"vivienda_agua_saneamiento",SV,rango=R("HV201","HV204"),lista=["HV235","HV236","SH42","SH43","SH51","SH52"])
b(t,"agua_tratamiento","Tratamiento y almacenamiento del agua para beber","Qué hace el hogar para hacer segura el agua (hervir, lejía, filtro…) y cómo la guarda.",HV,"vivienda_agua_saneamiento",SV,rango=R("HV237","HV237Z"),lista=["SH48","SH49","SH50"])
b(t,"cloro_agua","Prueba de cloro en el agua","Quién tomó la muestra de agua, de dónde se extrajo y resultado de la prueba de cloro.",HV,"vivienda_agua_saneamiento",RC,rango=R("SH227","QH227B"))
b(t,"saneamiento","Servicio higiénico","Tipo de servicio higiénico, si se comparte, con cuántos hogares y cada cuánto se limpia.",HV,"vivienda_agua_saneamiento",SV,lista=["HV205","HV225","HV238","SH56"])
b(t,"basura","Eliminación de la basura","Dónde tira la basura, cada cuánto se recoge y dónde la guarda.",HV,"vivienda_agua_saneamiento",SV,rango=R("SH58","SH60"))
b(t,"electricidad_alumbrado","Electricidad y alumbrado","Si el hogar tiene electricidad y qué tipo de alumbrado usa.",HV,"vivienda_agua_saneamiento",SV,lista=["HV206","SH70"])
b(t,"materiales_vivienda","Materiales y espacios de la vivienda","Material del piso, paredes y techo, habitaciones, ventanas y red.",HV,"vivienda_agua_saneamiento",SALUD,rango=R("HV213","HV216"),rangos=[R("SH71","SH72"),R("SH76A","SH76E")])
b(t,"combustible_cocina","Combustible y cocina","Combustible para cocinar, dónde se cocina, chimenea o campana y si el hogar compra combustible.",HV,"vivienda_agua_saneamiento",SALUD,lista=["HV226","SH63","SH64","SH66","SH69"],rango=R("HV239","HV242"))
b(t,"jefe_hogar","Jefe del hogar y composición","Número de orden, sexo y edad del jefe, y estructura de relaciones del hogar.",HV,CO,SALUD,rango=R("HV217","HV220"))
b(t,"bienes","Bienes del hogar","Radio, televisor, refrigeradora, bicicleta, moto, carro, teléfono, celular, computadora, internet y otros bienes.",HV,"bienes_riqueza",SALUD,rangos=[R("HV207","HV212"),R("HV243A","HV243D"),R("SH61A","SH61S")],lista=["HV221","SH77F"])
b(t,"tierras_ganado_cuenta","Tierras, ganado y cuenta bancaria","Tierras agrícolas, hectáreas, ganado por tipo y si alguien tiene cuenta bancaria.",HV,"bienes_riqueza",SALUD,rango=R("HV244","HV247"),lista=["SH78","SH79"])
b(t,"fallecidos","Miembros del hogar fallecidos","Si murió algún miembro del hogar en los últimos 12 meses y cuántos.","mortalidad","muertes_hogar",SALUD,ventana="últimos 12 meses",rango=R("HV249","HV250"))
b(t,"enfermos_huerfanos","Personas enfermas y huérfanos o niños vulnerables","Número de personas enfermas de 18 a 59 años y de huérfanos o niños vulnerables.",HV,CO,SALUD,lista=["HV248","HV251"])
b(t,"mosquiteros","Mosquiteros","Mosquiteros del hogar y si los menores de 5 años durmieron bajo uno.","salud_infantil","enfermedades_suplementos",SV,lista=["HV227","HV228","HML1","HML1A","HML2","SXH73"])
b(t,"yodo_sal","Yodo en la sal","Prueba de yodo, marca de sal y cómo se vio la bolsa.",HV,"vivienda_agua_saneamiento",RC,lista=["HV234","SH224","SH225U","SH225"])
b(t,"ubicacion_version","Región natural, semestre, provincia, distrito y versión","Datos de ubicación y de la versión del cuestionario.",ID,CF,SALUD,rango=R("SHVER","SHTOTH"))
b(t,"riqueza","Índice de riqueza","Índice de riqueza (quintil de bienestar) y su factor de puntuación.",HV,"bienes_riqueza",RC,rango=R("HV270","HV271"))
# ---------------------------------------------------------------- RECH5
t = "RECH5"
MPA = "salud_adultos"
b(t,"edad_nacimiento","Edad, fecha de nacimiento y grupo de la mujer","Edad en años, fecha de nacimiento y grupos de mujeres de 12 a 49 años.",HV,CO,SALUD,lista=["HA1","HA32","HA33","HA50"])
b(t,"peso_talla","Peso, talla e indicadores nutricionales de la mujer","Peso, talla, percentiles y desviaciones estándar, índice de masa corporal y resultado de la medición.",MPA,"mujeres_peso_anemia",RC,rango=R("HA2","HA13"),lista=["HA40","HA41"])
b(t,"tabaco","Cigarrillos fumados en las últimas 24 horas","Cuántos cigarrillos fumó la mujer en las últimas 24 horas.",MPA,"tabaco_alcohol",RC,ventana="últimas 24 horas",lista=["HA35"])
b(t,"hemoglobina","Hemoglobina y anemia de la mujer","Nivel de hemoglobina (ajustado por altitud), si estaba embarazada, resultado y nivel de anemia con las dos normas.",MPA,"mujeres_peso_anemia",RC,rango=R("HA53","HA58"))
b(t,"consentimientos","Responsable, consentimientos y resultado de la entrevista individual","Número de orden del padre o responsable, consentimientos y resultado de la entrevista.",ID,CF,SALUD,lista=["HA52","HA61","HA64","HA65"])
b(t,"vih","Resultado de la prueba de VIH","Resultado de la medición de VIH.",MPA,"vih_its",RC,lista=["HA63"])
b(t,"estado_civil","Estado civil","Estado civil de la mujer.","familia_pareja","union_convivencia",SALUD,lista=["HA60"])
b(t,"educacion","Educación de la mujer","Nivel educativo más alto, año más alto y nivel para informes.","educacion","nivel_educativo_asistencia",RC,rango=R("HA66","HA68"))
# ---------------------------------------------------------------- RECH6
t = "RECH6"
AN = "anemia_desnutricion"
b(t,"edad_peso_talla","Edad, peso y talla de la niña o el niño","Edad en meses, peso y altura medidos.","salud_infantil",AN,RC,rango=R("HC1","HC3"))
b(t,"indicadores_referencia_anterior","Talla y peso para la edad (referencia anterior)","Percentiles, desviaciones estándar y porcentaje de la mediana de talla/edad, peso/edad y peso/talla.","salud_infantil",AN,RC,rango=R("HC4","HC12"))
b(t,"indicadores_oms","Talla y peso para la edad (patrón OMS 2006)","Desviaciones estándar de talla/edad, peso/edad, peso/talla e IMC según la OMS (las que usan las recetas de desnutrición).","salud_infantil",AN,RC,rango=R("HC70","HC73"))
b(t,"medicion_razon","Razón por la que no se midió y posición de la medición","Por qué no se midió al niño y si se midió acostado o de pie.","salud_infantil",AN,SALUD,rango=R("HC13","HC15"))
b(t,"fechas","Fecha de nacimiento y año de la medición","Día, mes, año y fecha completa de nacimiento, y año de la medición.","salud_infantil",AN,SALUD,rango=R("HC16","HC19"),lista=["HC30","HC31","HC32","HC33"])
b(t,"sexo","Sexo","Sexo de la niña o el niño.",HV,CO,SALUD,lista=["HC27"])
b(t,"responsable_consentimiento","Responsable y consentimiento","Número de orden del padre o responsable y lectura de la declaración de consentimiento.",ID,CF,SALUD,rango=R("HC51","HC52"))
b(t,"hemoglobina","Hemoglobina y anemia","Nivel de hemoglobina (ajustado por altitud), resultado de la medición, nivel de anemia con las dos normas y acuerdo para enviar datos a un especialista.","salud_infantil",AN,RC,rango=R("HC53","HC58"))
b(t,"madre","Madre: orden, educación, intervalo y orden de nacimiento","Número de orden y nivel educativo de la madre, intervalo con el nacimiento anterior y orden de nacimiento.",HV,CO,SALUD,rango=R("HC60","HC68"))
# ---------------------------------------------------------------- REC44
t = "REC44"
b(t,"edad_peso_talla","Edad, peso y talla del hijo","Edad en meses, peso y talla medidos.","salud_infantil",AN,RC,rango=R("HW1","HW3"))
b(t,"indicadores_referencia_anterior","Talla y peso para la edad (referencia anterior)","Percentiles, desviaciones estándar y porcentaje de la mediana.","salud_infantil",AN,RC,rango=R("HW4","HW12"))
b(t,"indicadores_oms","Talla y peso para la edad (patrón OMS 2006)","Desviaciones estándar de talla/edad, peso/edad, peso/talla e IMC según la OMS.","salud_infantil",AN,RC,rango=R("HW70","HW73"))
b(t,"medicion_razon","Razón por la que no se midió y posición","Por qué no se midió al niño y si se midió acostado o de pie.","salud_infantil",AN,SALUD,rango=R("HW13","HW15"))
b(t,"fechas","Fecha de nacimiento y de la medición","Día de nacimiento y día, mes y año de la medición.","salud_infantil",AN,SALUD,rango=R("HW16","HW19"))
b(t,"responsable_consentimiento","Responsable y consentimiento","Número de orden del padre o responsable y consentimiento.",ID,CF,SALUD,rango=R("HW51","HW52"))
b(t,"hemoglobina","Hemoglobina y anemia","Nivel de hemoglobina (ajustado por altitud), resultado, nivel de anemia con las dos normas y acuerdo de envío a especialista.","salud_infantil",AN,RC,rango=R("HW53","HW58"))
# ---------------------------------------------------------------- REC21
t = "REC21"
b(t,"nacimiento","Nacimiento: orden, tipo de parto, fecha y sexo","Orden del nacimiento, parto único o múltiple, día, mes, año y fecha del nacimiento, y sexo del niño.","salud_materna_reproductiva","fecundidad_nacimientos",SALUD,rango=R("BORD","B4"),lista=["BD"])
b(t,"supervivencia","Si el niño vive, edad actual y edad a la muerte","Si está vivo, edad a la muerte (y su corrección) y edad actual.","mortalidad","mortalidad_infantil",RC,rango=R("B5","B8"))
b(t,"vive_con","Con quién vive","Con quién vive el niño.",HV,CO,SALUD,lista=["B9"])
b(t,"intervalos","Intervalos entre nacimientos","Intervalo con el nacimiento anterior, si es satisfactorio y nacimiento vivo entre nacimientos.","salud_materna_reproductiva","fecundidad_nacimientos",SALUD,lista=["B11","B12","B15"])
b(t,"calidad_informacion","Calidad de la información de la historia","Exhaustividad de la información y marca de la edad a la muerte.",ID,CF,SALUD,lista=["B10","B13"])
b(t,"fecha_apertura","Fecha de apertura de la historia","Día, mes, año y fecha de apertura de la historia de nacimientos, y meses desde el nacimiento.",ID,CF,SALUD,rango=R("BDD","BEDAD"))
b(t,"discapacidad","Dificultades o limitaciones permanentes del niño","Si el niño tiene alguna dificultad o limitación permanente (seis tipos).","salud_infantil","discapacidad_infantil",RC,rango=R("QD333_1","QD333_6"))
b(t,"embarazo","Duración del embarazo y nacimiento reciente","Duración del embarazo y marca de nacimiento en los últimos 5 años.","salud_materna_reproductiva","fecundidad_nacimientos",SALUD,lista=["Q220A","QULT5"])
# ---------------------------------------------------------------- DIT
t = "DIT"
D = "desarrollo_infantil_temprano"
b(t,"datos","Orden, edad y condición para la entrevista","Orden del nacimiento, edad en meses y si vive con la madre y no tiene discapacidad.","salud_infantil",D,SALUD,rango=R("BORD","QI478A"))
b(t,"modulo_e","Módulo E: cuidado, comprensión y trato","Figuras de cuidado, estimulación en el lugar donde pasa más tiempo, comprensión de órdenes y reacciones del niño.","salud_infantil",D,RC,pob={"edad_min":9,"edad_max":12,"edad_unidad":"meses"},rango=R("QI478E1","QI478E10"))
b(t,"modulo_f","Módulo F: juego, lenguaje y comprensión","Dónde juega, objetos a su alcance, cómo pide lo que quiere y qué órdenes cumple.","salud_infantil",D,RC,pob={"edad_min":13,"edad_max":18,"edad_unidad":"meses"},rango=R("QI478F1","QI478F6"))
b(t,"modulo_g","Módulo G: lenguaje","Nombra partes del cuerpo, usa palabras y frases, sigue pedidos y participa en conversaciones.","salud_infantil",D,RC,pob={"edad_min":19,"edad_max":23,"edad_unidad":"meses"},rango=R("QI478G1","QI478G4"))
b(t,"modulo_h","Módulo H: lenguaje, juego, materiales y comportamiento","Frases, imitación, juego con muñecos, materiales en casa y pataletas.","salud_infantil",D,RC,pob={"edad_min":24,"edad_max":36,"edad_unidad":"meses"},rango=R("QI478H1","QI478H11"))
b(t,"modulo_i","Módulo I: juego simbólico, materiales y comportamiento","Dibujo, juego con personajes, materiales en casa y pataletas.","salud_infantil",D,RC,pob={"edad_min":37,"edad_max":54,"edad_unidad":"meses"},rango=R("QI478I1","QI478I7"))
b(t,"castigo_15_dias","Castigo físico en los últimos 15 días","Veces que la madre o el cuidador le dio un palmazo, le jaló de las orejas u otro castigo físico en los últimos 15 días (una pregunta por tramo de edad: 24–36, 37–54 y 55–71 meses).","violencia","castigo_disciplina_infantil",RC,ventana="últimos 15 días",lista=["QI478H12","QI478I8","QI478J8"])
b(t,"modulo_j","Módulo J: juego, materiales y comportamiento","Juego de mentirita, juego con otros niños, materiales en casa y pataletas.","salud_infantil",D,RC,pob={"edad_min":55,"edad_max":71,"edad_unidad":"meses"},rango=R("QI478J1","QI478J7"))
# ---------------------------------------------------------------- REC43
t = "REC43"
INF = "enfermedades_suplementos"
b(t,"carne_vacunas","Carné de atención integral y vacunas","Si tiene carné, vacunas BCG, DPT, polio y sarampión con sus fechas, y si alguna vez tuvo vacunación.","salud_infantil","vacunas",SV,rango=R("H1","H10"))
b(t,"diarrea","Diarrea en los últimos 14 días","Si tuvo diarrea en los últimos 14 días y si había sangre en las deposiciones.","salud_infantil",INF,RC,ventana="últimos 14 días",rango=R("H11","H11B"))
b(t,"diarrea_donde_busco","Dónde buscó tratamiento para la diarrea","Lugar o persona donde buscó tratamiento (hospital, centro de salud, farmacia, casa…).","salud_infantil",INF,SV,rango=R("H12A","H12Z"))
b(t,"diarrea_tratamiento","Qué se le dio para tratar la diarrea","Sales de rehidratación, suero casero y otros tratamientos, lugar buscado, si sigue con diarrea y veces que le dieron zinc.","salud_infantil",INF,SV,rangos=[R("H13","H21"),R("H44A","H45")])
b(t,"fiebre_tos","Fiebre y tos en las dos últimas semanas","Si tuvo fiebre o tos y cuánto se le dio de beber y comer.","salud_infantil",INF,RC,ventana="últimas dos semanas",lista=["H22"],rangos=[R("H31","H31E")])
b(t,"fiebre_tos_donde_busco","Dónde buscó tratamiento para la fiebre o la tos","Lugar donde buscó tratamiento y cuántos días después de que apareció.","salud_infantil",INF,SV,rangos=[R("H32A","H32Z"),R("H46A","H46B")])
b(t,"fiebre_tos_tratamiento","Qué se le dio para la fiebre o la tos","Medicamentos y remedios que tomó el niño para la fiebre o la tos.","salud_infantil",INF,SV,rango=R("H37A","H37Z"))
b(t,"bebidas_comida_enfermedad","Bebidas y comida durante la enfermedad","Si se le dio la misma cantidad de bebidas y comida que antes.","salud_infantil",INF,SALUD,rango=R("H38","H39"))
b(t,"vitamina_a","Vitamina A","Dosis de vitamina A (más reciente y anterior) con su fecha.","salud_infantil",INF,SV,rangos=[R("H33","H33Y"),R("H40","H41B")])
b(t,"vitamina_a_6_meses","Vitamina A en los últimos 6 meses","Si recibió vitamina A en los últimos 6 meses.","salud_infantil",INF,SV,ventana="últimos 6 meses",lista=["H34"])
b(t,"campanas","Vacunas en campañas","Cualquier vacuna en los últimos 2 años y vacunas recibidas en campañas.","salud_infantil","vacunas",SV,rango=R("H35","H36F"))
b(t,"hierro_antiparasitarios","Hierro y antiparasitarios","Si toma píldoras de hierro o jarabe y medicamentos para parásitos intestinales.","salud_infantil",INF,SV,rango=R("H42","H43"))
# ---------------------------------------------------------------- REC95
t = "REC95"
b(t,"vacunas_refuerzos","Refuerzos de DPT y polio","Recibió el 1.er y 2.º refuerzo de DPT y de polio, con día, mes y año.","salud_infantil","vacunas",SV,rango=R("S45D4","S45P5Y"))
b(t,"vacunas_hepatitis_b","Vacuna contra la hepatitis B","Dosis al nacer y 1.ª a 3.ª dosis, con fecha, y cuándo se dio la primera.","salud_infantil","vacunas",SV,rango=R("S45B0","S45B3Y"),lista=["S459B"])
b(t,"vacunas_hib_penta_tetra","Vacunas Hib, pentavalente y tetravalente","Antihaemophilus, pentavalente y tetravalente, cada dosis con fecha.","salud_infantil","vacunas",SV,rango=R("S45F1","S45TTY"))
b(t,"vacunas_amarilica_sarampion","Vacunas antiamarílica, SPR y SR","Antiamarílica, antisarampionosa/SPR (1.ª y 2.ª dosis) y SR, con fecha.","salud_infantil","vacunas",SV,rango=R("S45ML","S45SRY"))
b(t,"vacunas_neumo_rota_influenza","Vacunas contra neumococo, rotavirus e influenza","Neumococo (3 dosis), rotavirus (2) e influenza (2), con fecha.","salud_infantil","vacunas",SV,rango=R("S45NM1","S45IF2Y"))
b(t,"vitamina_a","Vitamina A (tercera dosis) y número de vacunas con vitamina A","Tercera dosis de vitamina A con fecha y número de vacunas con vitamina A.","salud_infantil",INF,SV,rango=R("S45VA3","S45VA3Y"),lista=["S462E"])
b(t,"control_crecimiento","Control de crecimiento y desarrollo: si, dónde, cuántos y qué practicó","Si le hicieron control de crecimiento, dónde, cantidad de controles y consejería recibida.","salud_infantil",AN,SV,rango=R("S466","S466GC"))
b(t,"cred_menor_un_mes","Controles CRED del menor de un mes","Hasta cuatro controles: día, mes, año, peso y talla.","salud_infantil",AN,SV,rango=R("QI_CTRL_DIA_01","QI_CTRL_TALLA_04"))
b(t,"controles_crecimiento_detalle","Controles de crecimiento: fecha, peso y talla","Día, mes, año, peso y talla de cada control de crecimiento.","salud_infantil",AN,SV,rango=R("S466DC1","S466HC12"))
b(t,"fiebre_tos","Fiebre o tos: por qué no acudió y qué tenía en casa","Si sigue con fiebre o tos, por qué no acudió a un centro de salud y qué medicamentos tenía.","salud_infantil",INF,SV,rango=R("S470","S471CF"))
b(t,"diarrea","Diarrea: síntomas, deposiciones y tratamiento","Síntomas durante la diarrea, cantidad de deposiciones, pastillas y tabletas de zinc, y por qué no acudió.","salud_infantil",INF,SV,rango=R("S472AA","S475"))
b(t,"sintomas_diarios","Síntomas día a día en la última semana","Deposiciones líquidas, sangrado, tos y dificultad para respirar ayer y hasta hace siete días.","salud_infantil",INF,RC,ventana="últimos 7 días",rango=R("S476AN1","S476AR7"))
b(t,"hierro_7_dias","Hierro y micronutrientes en los últimos 7 días","Si tomó hierro en jarabe, gotas, chispitas u otra presentación en los últimos 7 días.","salud_infantil",AN,SV,ventana="últimos 7 días",rango=R("S465EA","S465ED"))
b(t,"hierro_12_meses","Hierro y micronutrientes en los últimos 12 meses","Frascos y sobres recibidos y consumidos en los últimos 12 meses por presentación.","salud_infantil",AN,SV,ventana="últimos 12 meses",rango=R("S465DB_A","S465DD_DC"))
b(t,"micronutrientes","Micronutrientes: razones de no consumo y entregas","Razón por la que no recibió o no consumió hierro o micronutrientes, forma de consumo y fecha de cada entrega.","salud_infantil",AN,SV,rango=R("Q465DF","Q465EC_Y6"))
b(t,"hemoglobina_tamizaje","Examen de hemoglobina, diagnóstico de anemia y tratamiento","Si le hicieron examen de hemoglobina, resultado, si le diagnosticaron anemia, tratamiento indicado y consumo de hierro.","salud_infantil",AN,SV,rango=R("QI465ED_CC_A","QI465ED_CC_D"))
# ---------------------------------------------------------------- REC94
t = "REC94"
E = "embarazo_control_parto"; LP = "lactancia_posparto"; MR = "salud_materna_reproductiva"
b(t,"controles_prenatales","Controles prenatales: pruebas y meses de embarazo","Meses de embarazo en la última revisión y en cada prueba (presión, orina, sangre, sífilis, VIH, hepatitis B).",MR,E,SV,rangos=[R("S410B","S411EA"),R("QI411_M","QI411F")])
b(t,"seguro","Seguro de salud de la madre y del niño","Si estaba afiliada al SIS o a otro seguro durante el embarazo y si el niño está afiliado al SIS.","acceso_salud","seguro_salud",SV,lista=["S413","S425A"],rango=R("S432","S432AY"))
b(t,"hierro_embarazo","Hierro durante el embarazo","Inyecciones de hierro y consumo de hierro indicado durante el embarazo.",MR,E,SV,lista=["S422I"],rango=R("QI422A_A","QI422A_D"))
b(t,"complicaciones_parto","Complicaciones del parto y razones para no acudir","Razón por la que no acudió a un establecimiento y complicaciones del parto.",MR,E,RC,rango=R("S426B","S426GE"))
b(t,"inscripcion_nino","Inscripción del niño","Inscripción en la municipalidad y partida con código único.",MR,E,SV,rango=R("S430C","S430D"))
b(t,"complicaciones_posparto","Complicaciones después del parto","Sangrado, fiebre y otras complicaciones después del parto y cuándo ocurrieron.",MR,LP,RC,rango=R("S427DA","S427F"))
b(t,"lactancia","Lactancia materna: biberón, contacto piel a piel, motivos y capacitación","Biberón en el establecimiento, contacto piel a piel, por qué no dio pecho o dejó de darlo, capacitación sobre lactancia y lactancia exclusiva.",MR,LP,SV,rango=R("S435","S442"),lista=["QI440B","S431A"])
b(t,"preparacion_alimentos","Preparación y almacenamiento de alimentos del niño","Anticipación con que se preparó, azúcar agregada, tiempo y lugar de almacenamiento.","salud_infantil","alimentacion_infantil",SALUD,rango=R("S446AA","S448B"))
# ---------------------------------------------------------------- REC41
t = "REC41"
b(t,"antitetanica","Vacuna antitetánica durante el embarazo","Dosis contra el tétano durante el embarazo y la última antes del embarazo.",MR,E,SV,rango=R("M1","M1E"))
b(t,"quien_control_prenatal","Quién hizo el control prenatal","Médico, obstetra, enfermera, partera u otra persona que la chequeó.",MR,E,SV,rango=R("M2A","M2N"))
b(t,"quien_atendio_parto","Quién atendió el parto","Médico, obstetra, enfermera, partera, familiar u otra persona.",MR,E,SV,rango=R("M3A","M3N"))
b(t,"lactancia_duracion","Duración de la lactancia, la amenorrea y la abstinencia","Duración y meses de lactancia, amenorrea y abstinencia, y sus marcas.",MR,LP,RC,rango=R("M4","M9"),lista=["M27","M28","M29"])
b(t,"lactancia_inicio_tomas","Lactancia: inicio, tomas y biberón","Cuándo empezó a darle el pecho, veces que lo amamantó ayer y si usó biberón.",MR,LP,RC,rango=R("M34","M39"))
b(t,"embarazo_deseado","Momento del embarazo y tiempo que hubiera querido esperar","Si quería quedar embarazada entonces y cuánto hubiera querido esperar.",MR,"fecundidad_nacimientos",SALUD,rango=R("M10","M11"))
b(t,"control_prenatal","Control prenatal: inicio, visitas y exámenes","Momento del primer control, número de visitas, exámenes, información sobre complicaciones y adónde acudir.",MR,E,SV,rangos=[R("M13","M14"),R("M42A","M42E"),R("M43","M44")])
b(t,"hierro_medicamentos","Hierro y medicamentos en el embarazo","Tabletas de hierro, días que las tomó, fansidar y medicamentos contra parásitos.",MR,E,SV,rangos=[R("M45","M46"),R("M49A","M49Z")],lista=["M60"])
b(t,"vision_nocturna","Dificultad para ver de noche en el embarazo","Si tuvo dificultad para ver de noche o con poca luz durante el embarazo.",MR,E,RC,rango=R("M47","M48"))
b(t,"parto_nacimiento","Parto y nacimiento: lugar, cesárea, tamaño y peso","Lugar del parto, cesárea, tamaño del niño al nacer y peso al nacer.",MR,E,RC,rango=R("M15","M19A"))
b(t,"control_posparto_vitamina_a","Vitamina A y atención en los primeros días después del parto","Vitamina A en los primeros días y atención de los tres primeros días.",MR,LP,SV,rango=R("M54","M55Z"))
b(t,"lugar_cuidado_prenatal","Lugar del cuidado prenatal","Dónde recibió el cuidado prenatal (su hogar, hospital, centro de salud, otro).",MR,E,SV,rango=R("M57A","M57X"))
b(t,"parto_estadia_alta","Parto: estadía, chequeo antes del alta y razones de no ir","Cuánto tiempo estuvo en el lugar del parto, quién verificó su salud antes del alta y por qué no fue a un centro de salud.",MR,E,SV,rango=R("M61","M65X"))
b(t,"control_posparto_bebe","Chequeo posparto de la madre y control del bebé","Tiempo hasta el primer control, chequeo después del parto, quién lo hizo, dónde y control posnatal del bebé.",MR,LP,SV,rango=R("M66","M73"),lista=["M51A"])
# ---------------------------------------------------------------- REC42
t = "REC42"
b(t,"lactancia_actual","Último parto y lactancia actual","Cesárea en el último parto, si amamanta, está amenorreica o en abstinencia, veces que amamanta y cuándo empezó.",MR,LP,RC,rango=R("V401","V408"),lista=["V426"])
b(t,"alimentos_ayer","Qué comió o bebió el niño ayer","Agua, jugo, leche, otros líquidos y alimentos que recibió el último hijo ayer, y biberón.","salud_infantil","alimentacion_infantil",RC,ventana="ayer (día y noche)",rangos=[R("V409","V415"),R("V414H1","V414H2")])
b(t,"higiene_sro","Higiene y sales de rehidratación","Conocimiento de sales de rehidratación oral, lavado de manos antes de preparar comida y eliminación de heces del niño.",HV,"vivienda_agua_saneamiento",SALUD,lista=["V416","V462","V465"])
b(t,"registro","Datos administrativos de registro","Ingreso en las tablas de maternidad, salud y altura/peso, y registradores.",ID,CF,SALUD,rango=R("V417","V421"))
b(t,"peso_talla_mujer","Peso, talla e indicadores de la mujer","Peso, talla, percentiles, índice de masa corporal y resultado de la medición de la mujer.",MPA,"mujeres_peso_anemia",RC,rango=R("V437","V447A"))
b(t,"consentimiento","Menores de 18, responsable y consentimiento","Informe del hogar sobre menores de 18, número de orden del responsable y lectura del consentimiento.",ID,CF,SALUD,rango=R("V452A","V452C"))
b(t,"hemoglobina","Hemoglobina y anemia de la mujer","Hemoglobina (ajustada por altitud), embarazo según el hogar, resultado y nivel de anemia con las dos normas.",MPA,"mujeres_peso_anemia",RC,rango=R("V453","V458"))
b(t,"mosquiteros","Mosquiteros","Mosquiteros del hogar y quiénes durmieron bajo uno.","salud_infantil",INF,SV,rango=R("V459","V461"))
b(t,"tabaco","Tabaco","Si fuma cigarrillos u otros productos y cuántos fumó en las últimas 24 horas.",MPA,"tabaco_alcohol",RC,rango=R("V463A","V464"))
b(t,"barreras_acceso","Problemas para atenderse cuando se enferma","Si podría llevar al niño enfermo y qué problemas tendría ella para atenderse (permiso, dinero, distancia…).","acceso_salud","barreras_acceso",SALUD,rango=R("V466","V467M"))
b(t,"marca_ultimo_nacimiento","Marca de variables del último nacimiento","Columnas usadas solo para variables del último nacimiento.",ID,CF,SALUD,lista=["V468"])
b(t,"alimentos_en_casa","Alimentos y líquidos que había en casa para el niño","Leche enlatada, en polvo, líquidos y alimentos que tenía la madre.","salud_infantil","alimentacion_infantil",SALUD,rango=R("V471A","V472U"))
b(t,"vih_prueba","VIH: consentimiento y resultado","Lectura del consentimiento y resultado de la prueba de VIH.",MPA,"vih_its",RC,rango=R("V473A","V473B"))
b(t,"tuberculosis","Tuberculosis: conocimientos y actitudes","Si escuchó hablar de la tuberculosis, cómo se transmite, si se cura y si guardaría el secreto.",MPA,"enfermedades_cronicas",SALUD,rango=R("V474","V476"))
b(t,"inyecciones","Inyecciones: número, quién las administró y seguridad","Inyecciones en los últimos 12 meses, si las puso un trabajador de salud, fuente y jeringa nueva.","acceso_salud","uso_servicios",SV,ventana="últimos 12 meses",rango=R("V477","V480"))
b(t,"seguro_salud","Seguro de salud de la mujer","Cobertura de seguro de salud y tipo de seguro.","acceso_salud","seguro_salud",SV,rango=R("V481","V481X"))
b(t,"cuidado_ninos","Quién cuida a los niños","Quién organiza el cuidado de los niños pequeños.","familia_pareja","trabajo_mujer_pareja",SALUD,rango=R("V482A","V482C"))
# ---------------------------------------------------------------- REC0111
t = "REC0111"
b(t,"identificacion","Identificación de la vivienda y la entrevistada","Número de vivienda, línea de la entrevistada, unidad de área final, año y fecha de la entrevista.",ID,CF,SALUD,rango=R("V002","V008"))
b(t,"edad_nacimiento","Edad y fecha de nacimiento","Mes, año y fecha de nacimiento, edad actual, grupo de 5 años e integridad de la información.",HV,CO,SALUD,rango=R("V009","V014"),lista=["Q105DD"])
b(t,"resultado_entrevista","Resultado de la entrevista individual y calendario","Resultado de la entrevista individual, inicio y duración del calendario.",ID,CF,SALUD,rango=R("V015","V019A"))
b(t,"pareja","Unión y esposo en el hogar","Si estuvo casada o unida alguna vez y el número de orden del esposo en el hogar.","familia_pareja","union_convivencia",SALUD,lista=["V020"])
b(t,"selecciones","Visitas, altitud y selección para módulos","Número de visitas, altitud del conglomerado y selección para hemoglobina, módulo de mujeres y de violencia.",ID,CF,SALUD,lista=["V027","V040"],rango=R("V042","V044"))
b(t,"residencia","Dominio, residencia actual, en la infancia y viajes","Dominio, lugar de residencia, de la infancia y anterior, tiempo viviendo allí y viajes en los últimos 12 meses.",HV,CO,SALUD,lista=["V167","V168"],rango=R("V101","V105"))
b(t,"educacion","Educación de la entrevistada","Nivel más alto, año o grado, años simples y logro educativo.","educacion","nivel_educativo_asistencia",RC,lista=["V106","V107","V133","V149"])
b(t,"vivienda_servicios","Vivienda y servicios del hogar","Agua, tiempo a la fuente, servicio higiénico, materiales de la vivienda, baño compartido, combustible, yodo en la sal y mosquitero.",HV,"vivienda_agua_saneamiento",SALUD,rangos=[R("V113","V116"),R("V127","V129")],lista=["V160","V161","V166","ML101"])
b(t,"bienes","Bienes del hogar","Electricidad, radio, televisión, refrigerador, bicicleta, motocicleta, coche y teléfono.",HV,"bienes_riqueza",SALUD,rango=R("V119","V125"),lista=["V153"])
b(t,"religion_etnia","Religión y etnicidad","Religión y autoidentificación étnica.","identidad_cultura","lengua_etnia",SALUD,rango=R("V130","V131"))
b(t,"hogar_composicion","Composición del hogar y jefe del hogar","Lugar de la entrevista, residente habitual o visitante, número de miembros, niños y mujeres elegibles, y relación, sexo y edad del jefe.",HV,CO,SALUD,rangos=[R("V134","V141"),R("V150","V152")])
b(t,"alfabetizacion_medios","Alfabetización y exposición a medios","Si sabe leer, programa de alfabetización y frecuencia con que lee, oye radio o ve televisión.","educacion","nivel_educativo_asistencia",SALUD,rango=R("V155","V159"))
b(t,"discapacidad","Dificultades o limitaciones permanentes","Si tiene alguna dificultad o limitación permanente (seis tipos).",MPA,"discapacidad",RC,rango=R("QD333_1","QD333_6"))
b(t,"riqueza","Índice de riqueza","Índice de riqueza (quintil de bienestar) y su factor de puntuación.",HV,"bienes_riqueza",RC,rango=R("V190","V191"))
b(t,"elegibilidad","Mujeres de 12 a 49 años","Marca de elegibilidad de la mujer.",ID,CF,SALUD,lista=["MUJERES12A49"])
# ---------------------------------------------------------------- RE223132
t = "RE223132"
b(t,"hijos_nacidos","Hijos nacidos vivos, vivos y fallecidos","Total de hijos e hijas nacidos, que viven con ella o no, fallecidos, nacimientos recientes y fecha y edad al primer nacimiento.",MR,"fecundidad_nacimientos",RC,rango=R("V201","V212"))
b(t,"embarazo_actual","Embarazo actual, ciclo menstrual y si es deseado","Embarazo actual, su duración, tiempo desde la última menstruación, conocimiento del ciclo y si es deseado.",MR,E,RC,rangos=[R("V213","V217"),R("V225","V227")])
b(t,"hijos_vivos_intervalos","Hijos vivos e intervalos","Número de hijos vivos, intervalos entre la unión y el primer nacimiento y desde el último nacimiento, e integridad de la fecha.",MR,"fecundidad_nacimientos",RC,rango=R("V218","V224"))
b(t,"perdidas","Pérdidas de embarazo","Embarazos terminados en aborto, pérdida o nacido muerto, y cuándo ocurrió el último.",MR,"fecundidad_nacimientos",RC,rango=R("V228","V243"))
b(t,"conocimiento_uso","Conocimiento y uso de métodos anticonceptivos alguna vez","Si conoce y alguna vez usó algún método, incluida la píldora y la inyección.",MR,"planificacion_familiar",RC,rangos=[R("V301","V302"),R("V305_01","V305_16"),R("QI302_05A","QI302_05B")])
b(t,"uso_actual","Método actual: cuál, inicio y duración","Método anticonceptivo actual, tipo, mes y año de inicio, marca de píldora, meses de uso y píldoras por marca.",MR,"planificacion_familiar",RC,rango=R("V310","V318"),lista=["V323","V337"],rangos=[R("V307_01","V307_16")])
b(t,"esterilizacion","Esterilización","Años desde la esterilización, edad, duración conyugal y número de niños al esterilizarse.",MR,"planificacion_familiar",RC,rango=R("V319","V322"))
b(t,"costo_fuente","Costo y fuente del método actual","Costo del método actual y de dónde lo obtiene.",MR,"planificacion_familiar",SV,rango=R("V325A","V327"))
b(t,"dejo_de_usar","Dejó de usar el método e intención de uso","Última discontinuidad, motivo, patrón de uso, intención y método futuro preferido.",MR,"planificacion_familiar",RC,rango=R("V359","V364"),lista=["V367"])
b(t,"razones_no_uso","Razones para no usar y fuentes conocidas","Paquete mostrado, razón principal para no usar, si usaría un método y fuente conocida.",MR,"planificacion_familiar",RC,rango=R("V372","V380"))
b(t,"mensajes_consejeria","Mensajes de planificación familiar y consejería","Mensajes oídos o leídos, visita de un trabajador de salud, consulta y consejería en el centro de salud.",MR,"planificacion_familiar",SV,rango=R("V384A","V395"))
b(t,"informacion_metodos","Información recibida sobre métodos","Información dada antes de la esterilización, uso de píldora y condón, y cuántos obtuvo la última vez.",MR,"planificacion_familiar",SV,rango=R("V3A01","V3A09B"))
# ---------------------------------------------------------------- RE516171
t = "RE516171"
UC = "union_convivencia"; TM = "trabajo_mujer_pareja"; FP = "familia_pareja"
b(t,"estado_civil","Estado civil y primera unión","Estado civil actual, número de uniones, esposo en el hogar, otras esposas, fecha y edad al primer matrimonio, y si ha estado casada o conviviendo.",FP,UC,RC,rango=R("V501","V513"),lista=["V535"])
b(t,"actividad_sexual","Primera relación y actividad sexual reciente","Edad en la primera relación, tiempo desde la última, actividad reciente, abstinencia y si piensa esperar hasta casarse.",FP,UC,RC,rangos=[R("V525","V532"),R("V536","V537")],lista=["V541"])
b(t,"fin_union","Fin de la unión anterior y bienes","Cómo terminó la unión anterior y quién recibió los bienes.",FP,UC,RC,rango=R("V538","V540"))
b(t,"deseo_hijos","Deseo de más hijos y tiempo de espera","Si quiere otro hijo, cuánto esperar, deseo de tener más y tiempo para el futuro nacimiento.","salud_materna_reproductiva","fecundidad_nacimientos",RC,rango=R("V602","V605"),lista=["V616","V621"])
b(t,"numero_ideal","Número ideal de hijos","Número ideal de niños, hijos, hijas o de cualquier sexo.","salud_materna_reproductiva","fecundidad_nacimientos",RC,rango=R("V613","V614"),rangos=[R("V627","V629")])
b(t,"necesidad_insatisfecha","Exposición y necesidad insatisfecha de planificación","Exposición al embarazo y necesidad insatisfecha con dos definiciones.","salud_materna_reproductiva","planificacion_familiar",RC,rango=R("V623","V626"))
b(t,"decision_anticonceptivos","Decisión sobre anticonceptivos y razones para no tener relaciones","Quién tomó la decisión de usar anticonceptivos, si el esposo lo sabe y razones para no tener relaciones.","salud_materna_reproductiva","planificacion_familiar",RC,rango=R("V631","V634"))
b(t,"esposo_educacion","Educación del esposo o compañero","Nivel, año o grado y años de educación del esposo o compañero.","educacion","nivel_educativo_asistencia",RC,lista=["V701","V702","V715","V729"])
b(t,"esposo_trabajo","Edad y ocupación del esposo o compañero","Edad, ocupación y grupo de ocupación del esposo o compañero.",FP,TM,RC,lista=["V730","V704","V705"])
b(t,"trabajo_mujer","Trabajo de la entrevistada","Si trabaja, para quién, dónde, todo el año o por temporada, tipo de ingresos, quién decide el gasto y cuánto gana frente a su esposo.",FP,TM,RC,rango=R("V714","V714A"),lista=["V719","V721","V731","V732","V739","V740","V741","V746","V716","V717"])
b(t,"decisiones_hogar","Quién tiene la última palabra en el hogar","Quién decide sobre cuidado de la salud, compras, visitas y gasto del dinero.",FP,TM,RC,rango=R("V743A","V743F"))
b(t,"actitudes_violencia","Actitudes ante el maltrato de la esposa","Si está de acuerdo con que el esposo golpee a su esposa en cada situación.","violencia","violencia_contra_mujer",RC,rango=R("V744A","V744E"))
# ---------------------------------------------------------------- RE758081
t = "RE758081"
VI = "vih_its"
b(t,"conocimiento_vih","Conocimiento sobre el VIH/SIDA","Si oyó hablar del VIH y del SIDA, formas de transmisión, mitos y si una persona saludable puede tener el virus.",MPA,VI,RC,rango=R("V750","V756"),lista=["V823","V825"])
b(t,"transmision_madre_hijo","Transmisión de madre a hijo y tratamiento","En qué etapa la madre con SIDA puede infectar al hijo, medicamentos para evitarlo y charla en el control prenatal.",MPA,VI,RC,rango=R("V774A","V774C"),lista=["V824","V837"],rangos=[R("V838A","V838C")])
b(t,"condon","Condón: uso y dónde conseguirlo","Uso de condón en la última y en la primera relación, dónde se consigue, si podría conseguirlo y uso con cada pareja.",MPA,VI,RC,rangos=[R("V761","V762BZ"),R("V769","V769A"),R("V833A","V833C")],lista=["V820","V822"])
b(t,"its","Otras infecciones de transmisión sexual","Diagnóstico de ITS en los últimos 12 meses, dónde buscó atención y si oyó hablar de otras ITS.",MPA,VI,RC,ventana="últimos 12 meses",rangos=[R("V763A","V763G"),R("V770","V770X")],lista=["V785"])
b(t,"parejas","Parejas sexuales","Número de parejas, relación, tiempo de conocerlas, edad, última relación y condón con cada una.",MPA,VI,RC,rangos=[R("V766A","V768C"),R("V821A","V821C"),R("V832B","V832C"),R("V834A","V836")],lista=["V830","V831"])
b(t,"prueba_vih","Prueba de VIH: si se la hizo, dónde y resultados","Si se hizo la prueba, dónde, cuándo, si la pidió ella y si obtuvo el resultado.",MPA,VI,RC,rangos=[R("V781","V784X"),R("V826","V829")])
b(t,"prueba_prenatal","Prueba de VIH en el control prenatal","Si le ofrecieron y le hicieron la prueba en el control prenatal, resultados y lugar.",MPA,VI,SV,rango=R("V839","V843"))
b(t,"estigma","Actitudes y estigma hacia las personas con VIH","Si mantendría el secreto, cuidaría a familiares, y conocimiento de rechazo o abuso a personas con VIH.",MPA,VI,SALUD,rangos=[R("V775","V780"),R("V844","V848")])
b(t,"normas_sexuales","Normas sobre relaciones sexuales y poder de decisión","Edad para esperar, rechazar el sexo, pedir condón y normas sobre jóvenes y mujeres casadas.",MPA,VI,SALUD,rango=R("V849","V851L"))
b(t,"presencia_entrevista","Presencia de otras personas durante la entrevista","Presencia de niños, del marido, de otros hombres y de otras mujeres.",ID,CF,SALUD,rango=R("V811","V814"))
# ---------------------------------------------------------------- REC91
t = "REC91"
b(t,"ubicacion","Región natural, semestre, provincia y distrito","Región natural, semestre, provincia y distrito de la entrevista.",ID,CF,SALUD,rango=R("SREGION","SDISTRI"))
b(t,"educacion","Educación: nivel, asistencia y razón de abandono","Nivel y último grado aprobado, si asiste y por qué dejó de asistir.","educacion","nivel_educativo_asistencia",RC,rango=R("S108N","S112"))
b(t,"lengua","Lengua materna y autoidentificación","Idioma o lengua materna que aprendió a hablar y autoidentificación por antepasados y costumbres.","identidad_cultura","lengua_etnia",RC,rango=R("S119","S119D"))
b(t,"control_embarazo_lugar","Dónde fue el control del embarazo","Hospital, centro de salud, puesto, clínica, consultorio, casa u otro; o sin control.",MR,E,SV,rango=R("S229A","S229Y"))
b(t,"primer_control","Meses de embarazo al primer control","Meses de embarazo al primer control prenatal.",MR,E,SV,lista=["S229A1"])
b(t,"afiliacion_seguro","Afiliación a un seguro de salud","Si está afiliada y la fecha de afiliación.","acceso_salud","seguro_salud",SV,rango=R("S229B1","S229CY"))
b(t,"conocimiento_sis","Conocimiento del Seguro Integral de Salud","Cómo se enteró y qué conoce del SIS.","acceso_salud","seguro_salud",SALUD,rango=R("S229DA","S229DX"))
b(t,"documentos_identidad","Documentos de identificación","Partida de nacimiento, DNI u otro documento.","identidad_cultura","documentos_identidad",SALUD,rango=R("S239A","S239X"))
b(t,"esterilizacion_pago","Esterilización: pago y momento","Monto pagado y momento en que se esterilizó.",MR,"planificacion_familiar",SV,rango=R("S314","S315B"))
b(t,"metodos_naturales","Métodos vaginales y determinación de días fértiles","Marca de métodos vaginales y cómo determinar los días fértiles.",MR,"planificacion_familiar",SALUD,rango=R("S317AC","S317C"))
b(t,"metodo_actual","Método actual: fuente, decisión y opinión de la atención","Primera fuente, si es el método que quería, problemas para obtenerlo, quién decidió y opinión de la atención recibida.",MR,"planificacion_familiar",SV,rango=R("S321A","S325GK"))
b(t,"controles_diu","Controles de DIU o implante","Si fue a controles de DIU o implante y cuántos.",MR,"planificacion_familiar",SV,rango=R("S327B","S327C"))
b(t,"llevaria_nino","Si llevaría al niño al centro de salud","A qué síntomas del niño lo llevaría de inmediato al centro de salud.","salud_infantil",INF,SALUD,rango=R("S481AA","S481AZ"))
b(t,"juntos","Programa Juntos","Si está afiliada o incorporada al programa Juntos y desde cuándo.","programas_sociales","juntos",SV,rango=R("S484","S484Y"))
b(t,"papanicolau_mama","Papanicolaou y examen de mama","Si oyó hablar del Papanicolaou, si le hicieron la prueba y los exámenes de mama.",MPA,"prevencion_cancer",SV,rango=R("S485","S486B"))
b(t,"tuberculosis","Actitud ante familiares con tuberculosis","Si cuidaría a parientes enfermos de tuberculosis y si mantendría en secreto la enfermedad de un familiar.",MPA,"enfermedades_cronicas",SALUD,rango=R("S489C","S489D"))
b(t,"lavado_manos","Lavado de manos","Cuántas veces al día y en qué momentos se lava las manos, y con qué.",HV,"vivienda_agua_saneamiento",SALUD,rango=R("S490","S490BX"))
b(t,"liquidos_ayer","Líquidos que tomó el niño ayer","Qué bebió el niño durante el día o la noche de ayer.","salud_infantil","alimentacion_infantil",RC,ventana="ayer (día y noche)",rango=R("S492A","S492G"))
b(t,"alimentos_ayer","Alimentos que comió el niño ayer","Qué alimentos comió el niño durante el día o la noche de ayer.","salud_infantil","alimentacion_infantil",RC,ventana="ayer (día y noche)",rango=R("S493A","S493P"))
b(t,"papilla_programas","Papilla de programas sociales","Si recibe papilla de los programas sociales y si el niño la come.","programas_sociales","hogar_programas",SV,rango=R("S494","S494B"))
b(t,"quien_alimenta","Quién alimenta al niño","Persona que normalmente alimenta al niño y si ayer no recibió líquidos o sólidos.","salud_infantil","alimentacion_infantil",SALUD,rango=R("S495A","S496"))
b(t,"presencia_entrevista","Presencia de otras personas durante la entrevista","Presencia de niños menores de 10 años, del esposo y de otras personas en la entrevista.",ID,CF,SALUD,rangos=[R("S500A","S500D"),R("S1034A","S1034B")])
b(t,"divorcio_primera_pareja","Causa del divorcio y relación con la primera pareja sexual","Principal causa del último divorcio y relación con la primera pareja sexual.",FP,UC,RC,lista=["S508A","S512C"])
b(t,"actitud_planificacion","Actitud hacia la planificación familiar","Si aprueba que las parejas usen métodos, si ha comentado sobre planificación y si su esposo aprueba.",MR,"planificacion_familiar",SALUD,rango=R("S616","S621A"))
b(t,"esposo_educacion","Educación del esposo o compañero","Nivel educativo y último grado aprobado del esposo o compañero.","educacion","nivel_educativo_asistencia",RC,rango=R("S704N","S704G"))
b(t,"ingresos_cuidado","Ingresos de la entrevistada y quién cuida a los niños","Uso de los ingresos de la entrevistada y quién cuida de los niños cuando sale.",FP,TM,SALUD,rango=R("S718","S720A"))
b(t,"vih_conocimiento","Conocimiento sobre el VIH/SIDA","Qué se puede hacer para evitar el SIDA, cómo se transmite y actitudes hacia las personas con el virus.",MPA,VI,RC,rangos=[R("S802","S802I"),R("S806AX","S806AZ"),R("S807","S811")])
b(t,"vih_prueba","Prueba de VIH","Dónde hacerse la prueba, si recibió asesoría y resultados.",MPA,VI,RC,rango=R("S803AF","S804C"))
b(t,"its","Infecciones de transmisión sexual","Qué ETS conoce, síntomas en hombres y mujeres, diagnóstico en los últimos 12 meses, tratamiento y relaciones sexuales por dinero.",MPA,VI,RC,rango=R("S815AA","S818"))
b(t,"violencia_pareja","Control y agresiones de la pareja","Conductas de control y agresiones del esposo o compañero en la última relación.","violencia","violencia_contra_mujer",RC,pob={"edad_min":15,"edad_max":49,"edad_unidad":"anios","condicion":"mujeres seleccionadas para el módulo de violencia familiar"},rango=R("S1002A","S1002E"))
b(t,"violencia_consecuencias","Consecuencias de la agresión y quién agredió","Resultados de las agresiones en los últimos 12 meses y quién pegó con mayor frecuencia.","violencia","violencia_contra_mujer",RC,ventana="últimos 12 meses",pob={"edad_min":15,"edad_max":49,"edad_unidad":"anios","condicion":"mujeres seleccionadas para el módulo de violencia familiar"},rango=R("S1008AN","S1017"))
b(t,"violencia_ayuda","Búsqueda de ayuda ante la violencia","A quién acudió, si nunca buscó ayuda y si conoce casos.","violencia","violencia_contra_mujer",SV,pob={"edad_min":15,"edad_max":49,"edad_unidad":"anios","condicion":"mujeres seleccionadas para el módulo de violencia familiar"},rango=R("S1023AA","S1026"))
b(t,"castigo_hijos","Cómo castiga el padre y la madre a sus hijos","Formas de castigo del padre biológico, la madre y otras personas, y si los hijos fueron castigados.","violencia","castigo_disciplina_infantil",RC,pob={"edad_min":15,"edad_max":49,"edad_unidad":"anios","condicion":"mujeres seleccionadas para el módulo de violencia familiar"},rango=R("S1030AA","S1031"))
b(t,"castigo_infancia","Cómo la castigaban a ella y opinión sobre el castigo","Formas de castigo que recibió de niña y si cree que es necesario castigar.","violencia","castigo_disciplina_infantil",RC,pob={"edad_min":15,"edad_max":49,"edad_unidad":"anios","condicion":"mujeres seleccionadas para el módulo de violencia familiar"},rango=R("S1032A","S1033"))
b(t,"castigo_quien","Quién reprende o castiga a los hijos","Quién reprende o castiga a sus hijas e hijos en el hogar.","violencia","castigo_disciplina_infantil",RC,pob={"edad_min":15,"edad_max":49,"edad_unidad":"anios","condicion":"mujeres seleccionadas para el módulo de violencia familiar"},rango=R("S1028A","S1028Y"))
b(t,"anemia_conocimiento","Qué síntomas y alimentos asocia con la anemia","Síntomas que tendría su niño si tuviera anemia y alimentos que le ofrecería.","salud_infantil",AN,SALUD,rango=R("QI479E_A","QI479F_Y"))
b(t,"reuniones_sesiones","Reuniones y sesiones en los últimos 12 meses","Si participó en reuniones o sesiones, en cuántas y qué recibió.","salud_infantil",AN,SV,ventana="últimos 12 meses",rango=R("Q479A","Q479D"))

# ---------------------------------------------------------------- escritura
seccion = lambda t: " / ".join(fichas[t]["secciones"]) if fichas[t]["secciones"] else None
out = ["# Bloques temáticos de la ENDES 2024 (M1-06, tarea 3; docs/diseno/fichas.md §6).",
       "# Un bloque es un grupo de preguntas del mismo asunto dentro de una tabla. Lote: las 19 tablas de niño, mujer y hogar de M1 (README «Lote de tablas de M1»).",
       "# Las variables se declaran por prefijo, por rango de posición entre dos códigos (`rango`; `rangos` si son varios pares) o por lista; solo cuentan las de clase",
       "# categoria o medida (las llaves, pesos, diseño y geografía no llevan bloque). Cada una de ellas está en un solo bloque: `pap fichas validar` (regla 4) lo comprueba.",
       "# Punto de partida: las baterías del índice (`grupo`) y las secciones del cuestionario (M1-04); los nombres salen de las etiquetas de las variables.",
       "# Todo en `propuesto`; el auditor-agente los revisa contra el diccionario (evidencia/m1-06_revision.md) y el dueño da el visto por lote. Los temas son provisionales (temas.yaml).",
       ""]
doc = OrderedDict(version="0.1.0", fecha="2026-11-12", encuesta="ENDES", bloques=[])
ids = set()
for x in B:
    i = f"endes_{x['tabla'].lower()}_{x['slug']}"
    assert i not in ids, i
    ids.add(i)
    d = OrderedDict(id=i, tabla=x["tabla"], anios=[2024, 2024], nombre=x["nombre"], descripcion=x["desc"], variables=OrderedDict(x["spec"]),
                    tema=x["tema"], subtema=x["sub"], tema_estado="provisional", papel=x["papel"], poblacion=x["pob"])
    if x["ventana"]: d["ventana_referencia"] = x["ventana"]
    if seccion(x["tabla"]): d["seccion_cuestionario"] = seccion(x["tabla"])
    d["estado"] = "propuesto"
    doc["bloques"].append(d)
class D(yaml.SafeDumper): pass
D.add_representer(OrderedDict, lambda dumper, data: dumper.represent_mapping("tag:yaml.org,2002:map", data.items()))
D.add_representer(list, lambda dumper, data: dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=all(isinstance(v, str) or isinstance(v, int) for v in data) and len(data) <= 3 and len(data) > 0))
open(f"{raiz}/curados/inferencia/bloques/ENDES.yaml", "w", encoding="utf-8").write("\n".join(out) + yaml.dump(doc, Dumper=D, allow_unicode=True, sort_keys=False, width=200))
print(len(B))
