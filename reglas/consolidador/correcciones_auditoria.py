"""Correcciones v1.1: auditoría independiente de las reglas v1.0 (4 auditores, 59 hallazgos: EST, IMP, HEC, COM).
Cada hallazgo fue validado por el orquestador (VEREDICTOS). Las correcciones cambian la condición o los parámetros
(no solo el caso borde, IMP-09). Se aplican después de correcciones_prueba.py."""
from correcciones_prueba import regla

# ---------------------------------------------------------------- veredictos
# A = aceptado tal cual; AA = aceptado con ajuste del orquestador; R = rechazado; F = aceptado y se informa al dueño (toca una decisión)
VEREDICTOS = {
 'COM-01': ('A', 'Igual a IMP-01. Verificado: aplica_a.fuentes de R-REG-12 era lista cerrada de 9 fuentes.'),
 'COM-02': ('A', 'Las tasas con numerador pequeño revelan el conteo.'),
 'COM-03': ('AA', 'Se adopta el cubo protegido para fuentes sensibles; en el MVP basta con servirlas solo en geografía vigente, años sueltos cerrados y sin acumulados mensuales (sin GEO2017 ni ventanas móviles).'),
 'COM-04': ('AA', 'Se adopta; el umbral de 5 000 habitantes lo propuso el auditor sin norma que lo respalde: queda como parámetro revisable.'),
 'COM-05': ('A', 'Tabla de temas sensibles por CIE-10 y por fuente.'),
 'COM-06': ('A', 'RUC 10/15 incluye el DNI.'),
 'COM-07': ('AA', 'Su lista tenía 6 falsos positivos en un corpus de reserva del orquestador ("nivel bajo", "subsidio", "mejores datos", "subsector"). Se ajustaron los patrones de cambio y ranking; resultado: 0 falsos positivos en 49 oraciones correctas y 0 no detectadas en 57 que debían bloquearse (las 3 restantes son estructurales, COM-08). La frase estándar "estos datos no permiten saber si el gasto causó…" va como span protegido.'),
 'COM-08': ('A', 'Verificación estructural con marcadores {{v:id}}.'),
 'COM-09': ('A', 'Normalización explícita; el patrón de verbos de cambio se evalúa con tildes (bajó ≠ bajo).'),
 'COM-10': ('A', 'Regla nueva R-LENGUAJE-08 (neutralidad).'),
 'COM-11': ('AA', 'Se cambian los rótulos, pero el semáforo resume más que la precisión (vigencia, base geográfica, tipo de medida): "Dato sólido / Dato con limitaciones / Dato muy aproximado / Sin datos suficientes". Se informa al dueño.'),
 'COM-12': ('F', 'La prueba con usuarios pasa a ser condición antes del lanzamiento público (no de una beta cerrada). Se informa al dueño.'),
 'COM-13': ('A', 'Se reescriben los mensajes señalados.'),
 'COM-14': ('A', 'Accesibilidad de cifras y semáforo.'),
 'COM-15': ('A', 'Rango en la ficha corta para ámbar y rojo.'),
 'EST-01': ('A', 'CV sobre min(p, 1−p): la misma celda no puede publicarse como 85 % y suprimirse como 15 %.'),
 'EST-02': ('A', 'Se completa el estándar NCHS (ancho absoluto ≤ 0,05 se presenta).'),
 'EST-03': ('A', 'Cobertura específica de defunciones infantiles y criterio de cobertura en el semáforo.'),
 'EST-04': ('AA', 'Estandarización por edad: en el MVP solo a departamento (hay población por edad del INEI); bajo ese nivel, sin denominadores por edad aprobados, no se comparan tasas de todas las edades entre territorios.'),
 'EST-05': ('F', 'Igual a IMP-08. Se precisa D9: N = territorios del mismo nivel dentro de un departamento, o los 25 departamentos a nivel nacional; siempre ámbar. Se informa al dueño (aclara D9).'),
 'EST-06': ('A', 'Varianza de la agrupación de años en ENAHO.'),
 'EST-07': ('A', 'anio_referencia = año central del periodo agrupado.'),
 'EST-08': ('A', 'Relevancia mínima y sobredispersión en R-REG-14.'),
 'EST-09': ('A', 'Criterio denominador en el semáforo.'),
 'EST-10': ('A', 'Territorio contenido en otro: comparar contra el resto.'),
 'EST-11': ('F', 'Se mantiene D3 (5/20); con 5–10 casos se muestra solo el rango, sin valor puntual, en rojo, por coherencia con D2. Se informa al dueño.'),
 'EST-12': ('A', 'Clasificación de CV del INEI para el Mapa DCI.'),
 'EST-13': ('A', 'Fórmula de s² de Marshall.'),
 'HEC-01': ('A', 'Población censada ≠ población total; verificado (34 157 732 vs 32 706 028).'),
 'HEC-02': ('A', 'Verificado por el orquestador: el INEI publicó resultados distritales el 10-11/07/2026 (Canal N). Corrige la nota PR-24, que estaba equivocada.'),
 'HEC-03': ('A', 'Igual a parte de IMP-11.'),
 'HEC-04': ('A', 'Ajuste por omisión censal antes de comparar.'),
 'HEC-05': ('A', 'Plan si la base 2025 no trae retroproyección.'),
 'HEC-06': ('A', 'Verificado por el orquestador: ENLA 2024 4.º de primaria se aplicó a más de 532 mil estudiantes en más de 18 mil IIEE (La República, 14-04-2025).'),
 'HEC-07': ('A', 'Tabla de disponibilidad por criterio en lugar del corte fijo 2024; compatible con D1.'),
 'HEC-08': ('A', 'Periodo de referencia de la mortalidad ENDES.'),
 'HEC-09': ('A', 'Quiebre SINADEF hasta 2020 y cita corregida.'),
 'HEC-10': ('A', 'Santa Rosa de Loreto (Ley 32403, 2025) verificada; explica el distrito 1 892 (reemplaza la hipótesis de Alto Trujillo).'),
 'HEC-11': ('A', 'Dominios Lima/Callao por encuesta.'),
 'HEC-12': ('A', 'Citas de ENAHO 2021 y 2020.'),
 'IMP-01': ('A', 'Igual a COM-01; se aplica una sola corrección.'),
 'IMP-02': ('A', 'Se separan aplica_a (cifras evaluadas) e insumos_regla (tablas consultadas).'),
 'IMP-03': ('A', 'R-MOTOR-01 reescrita con estado único y secuencias por naturaleza del catálogo.'),
 'IMP-04': ('A', 'Regla nueva R-MOTOR-02 (precedencia).'),
 'IMP-05': ('AA', 'Renombres mecánicos solo para sinónimos reales; los campos que el diccionario fusionaba mal se conservan como campos propios.'),
 'IMP-06': ('A', 'D8 llevado a la matriz.'),
 'IMP-07': ('A', 'D4 llevado a la condición de R-REG-02.'),
 'IMP-08': ('A', 'Ver EST-05.'),
 'IMP-09': ('A', 'Condiciones reescritas donde el borde las contradecía.'),
 'IMP-10': ('A', 'R-TERRITORIO-08 deja de aplicar al gasto.'),
 'IMP-11': ('A', 'R-DEP-01 por rol del insumo; CPV2025 y MINSA salen de los bloqueantes.'),
 'IMP-12': ('A', 'Nulos → suprimir con motivo metadato_faltante; vocabulario sin tildes.'),
 'IMP-13': ('AA', 'Periodo por defecto → R-MOTOR-03 en la etapa 0. R-EST-05 se mantiene en la etapa 2: las fuentes disponibles por nivel salen de dim_indicador (catálogo), no de resultados posteriores.'),
 'IMP-14': ('A', 'Tablas curadas del MVP con especificación mínima.'),
 'IMP-15': ('A', 'R-TERRITORIO-07 pasa a MVP.'),
 'IMP-16': ('A', 'La semilla CPV2025 solo con la migración completa (D7).'),
 'IMP-17': ('A', 'Una sola tabla NIVEL_RANK.'),
 'IMP-18': ('A', 'Vocabulario de gasto.'),
 'IMP-19': ('A', 'Pruebas del consolidador reales y bloqueantes.'),
}

# ---------------------------------------------------------------- reglas nuevas
NUEVAS = [
 regla('R-MOTOR-02', 'motor', 'Precedencia, nulos y vocabulario de acciones',
  'Cuando varias reglas actúan sobre la misma cifra gana la acción más restrictiva; dentro de una regla gana la primera cláusula que se cumple; un metadato faltante nunca deja pasar una cifra.',
  "acciones(cifra, etapa) = {a_1..a_n} → accion_final = max_restriccion(a_i); campo_requerido IS NULL AND caso no definido → estado_cifra = 'suprimida', motivo = 'metadato_faltante'",
  'suprimir', {
   'orden_restriccion': ['bloquear_cruce', 'suprimir', 'agregar_nivel', 'agrupar_anios', 'publicar_referencial', 'publicar'],
   'agregar_nivel_multiple': 'se usa el nivel más grueso pedido',
   'acumulables': ['rotular', 'advertir', 'revision_humana'],
   'clausulas': 'se evalúan en el orden escrito; gana la primera que se cumple',
   'estado_cifra_vocabulario': ['publicable', 'referencial', 'suprimida', 'agregada', 'agrupada', 'sin_datos'],
   'tipo_estimacion_vocabulario': ['proporcion', 'total', 'media', 'razon', 'tasa', 'modelada', 'propia'],
   'normalizacion_salidas': {'bloquear': 'suprimir (cifra) o bloquear_cruce (cruce)', 'no_publicar': 'suprimir', 'publicar_solo_conteo': 'suprimir la tasa + publicar el conteo', 'publicar_rango': 'publicar_referencial (modo=rango)', 'mostrar_solo_el_intervalo': 'publicar_referencial (modo=rango)', 'publicar_tasa_suavizada': 'publicar_referencial (modo=suavizada)', 'nota': 'rotular', 'marcar_incompletas': 'rotular', 'revision_humana_del_denominador': 'revision_humana', 'fallo_de_ingesta': 'revision_humana', 'error_de_datos': 'revision_humana', 'preguntar': 'revision_humana (al usuario)', 'no_comparar': 'bloquear_cruce', 'sin_coeficiente': 'bloquear_cruce (solo el coeficiente)', 'regenerar': 'rotular (corrector)', 'plantilla_pasado': 'rotular', 'aviso_choque': 'advertir', 'top_n': 'publicar (modo=lista)', 'agregar_al_grupo': 'agregar_nivel (grupo_comparable)'}},
  None, 'Sin precedencia, dos programadores obtienen resultados distintos con las mismas reglas (IMP-04, IMP-12).',
  'Aplicar al cerrar cada etapa. Toda salida de una regla se normaliza con normalizacion_salidas antes de combinarse.',
  'Valores vacíos o cero no son nulos: p = 0 se trata en R-ENC-04 (numerador == 0).', ['IMP-04', 'IMP-12', 'IMP-03']),
 regla('R-MOTOR-03', 'motor', 'Resolver el periodo pedido',
  'Si la pregunta no indica año, se usa el último año cerrado con dato aprobado de cada fuente; esto se decide antes de ubicar y calcular.',
  "periodo_pedido IS NULL → anio(fuente) = max(anio con compuerta aprobada AND es_preliminar = false); gasto: último año cerrado + acumulado de cartera activa (R-GASTO-17)",
  'rotular', {'anio_en_curso': 'solo si la pregunta lo pide; se rotula "dato preliminar al {fecha_corte}"'},
  'Mostramos el último año completo disponible: {anio}.', 'El año se necesita desde la etapa 1 (ubigeo vigente) y la 3 (vintage de población) (IMP-13).',
  'Etapa 0. Cada fuente puede quedar con un año distinto; R-CRUCES-03 decide si son comparables.', 'Si dos fuentes de un cruce tienen años distintos, se rotula (R-CRUCES-03).', ['IMP-13']),
 regla('R-REG-15', 'registros', 'Tasas ajustadas por edad para comparar territorios o años',
  'Toda comparación entre territorios o años de una tasa de mortalidad o morbilidad de todas las edades usa la tasa ajustada por edad; la tasa bruta solo se muestra para un territorio aislado y rotulada.',
  "indicador.tipo_estimacion == 'tasa' AND indicador.poblacion_objetivo == 'todas_las_edades' AND salida.tipo IN (ranking, mapa, comparacion, asociacion) → usar tasa_ajustada_edad; si no hay denominador por edad aprobado a ese nivel → bloquear_cruce",
  'bloquear_cruce', {'metodo': 'directo', 'poblacion_estandar': 'Perú CPV2017 nacional por grupos quinquenales', 'ic': 'gamma (Fay-Feuer)', 'nivel_mvp': 'departamento (población por edad INEI)', 'exentas': 'tasas específicas por edad (TMI, TMN, RMM) y prevalencias de un grupo de edad definido'},
  'Para comparar lugares con distinta proporción de personas mayores, usamos tasas ajustadas por edad.',
  'Las estructuras de edad difieren mucho entre territorios (Lima vs Amazonía); comparar tasas brutas confunde edad con riesgo (OPS/ENLACE).',
  'Numerador por grupo quinquenal desde la fuente; denominador INEI-PROYECCIONES-DEPARTAMENTAL-EDAD. Bajo departamento solo cuando el prorrateo propio por edad esté aprobado (R-DENOMINADORES-03).',
  'Con < 20 eventos totales se agrupan años antes de ajustar (R-REG-03).', ['EST-04'], aplica_a={'naturaleza_dato': ['registro_administrativo', 'indicadores_derivados'], 'tipo_medida': ['registro_eventos', 'notificacion_vigilancia'], 'base_geografica': [], 'fuentes': []}),
 regla('R-LENGUAJE-08', 'lenguaje', 'Neutralidad: entidades, no personas',
  'Las cifras de gasto y resultados se atribuyen a entidades y años, nunca a autoridades, partidos o gestiones; las preguntas que piden juzgar a personas se reformulan.',
  "intencion_pregunta IN ('juicio_autoridad', 'causa_corrupcion', 'comparacion_gestiones') → reformular con plantilla_neutral; texto menciona autoridad|partido|gestión junto a una cifra → regenerar",
  'rotular', {
   'intenciones': {'juicio_autoridad': 'avance de ejecución por entidad, con PIM, fecha de corte y aviso de que la ejecución depende de muchos factores',
                   'causa_corrupcion': 'con los datos públicos que usamos no se puede responder; se muestran solo cifras de gasto',
                   'comparacion_gestiones': 'se comparan años, no gestiones'},
   'ranking_entidades': 'solo por grupos (R-ENC-12) y con la fecha de corte; nunca "la que peor gasta"',
   'periodo_electoral': 'sin cambios de regla; la neutralidad aplica siempre'},
  'Estos datos describen lo que registró la entidad; no permiten juzgar a sus autoridades.',
  'La web se usará en contexto político (elecciones regionales y municipales de octubre de 2026); sin una regla explícita podría usarse para atacar o elogiar autoridades sin base (COM-10).',
  'Clasificador de intención en el intérprete; patrón "acusación o atribución a personas" en lenguaje.prohibidas.',
  'Preguntas factuales sobre quién es la autoridad: fuera de alcance (no es un dato de la biblioteca).', ['COM-10']),
]

# ---------------------------------------------------------------- parches
# op: set (ruta con puntos; reemplaza el valor), borde (nota no lógica), replace (campo, viejo, nuevo), etapa, prioridad
FUENTES_SENSIBLES = ['MINSA-REUNIS', 'CDC-VIGILANCIA-DATOS-ABIERTOS', 'ESSALUD-DATOS-ABIERTOS', 'SIS-ATENCIONES', 'INS-CENAN-SIEN',
                     'MINEDU-CENSO-EDUCATIVO', 'MIMP-WARMINAN-BANCO-DATOS', 'MININTER-VIOLENCIA-MUJER-PNP']
PARCHES = [
 # ---- divulgación (COM-01..06, IMP-01)
 ('R-REG-12', 'set', 'aplica_a', {'naturaleza_dato': ['registro_administrativo', 'censo', 'indicadores_derivados'],
   'tipo_medida': ['cobertura_programa', 'registro_eventos', 'padron_referencia', 'atenciones_produccion', 'notificacion_vigilancia'], 'base_geografica': [], 'fuentes': []}, 'COM-01, IMP-01'),
 ('R-REG-12', 'set', 'condicion',
  "Aplica a toda cifra (conteo, tasa o proporción) con unidad de observación persona, hogar, estudiante o caso. "
  "(1) 1 ≤ numerador < umbral(sensibilidad_divulgacion) → suprimir el valor (también la tasa o proporción) y aplicar supresión complementaria; "
  "(2) sensibilidad = sensible AND 1 ≤ denominador − numerador < umbral → suprimir; "
  "(3) poblacion < 1000 → solo totales anuales sin desagregar; no publicar celdas 0 ni celdas iguales al total; "
  "(4) 1000 ≤ poblacion < 5000 → máximo 1 desagregación; (5) en otro caso máximo 2; "
  "(6) centro poblado → solo total y solo si ≥ 10; "
  "(7) fuentes con sensibilidad != ninguna → servir solo desde el cubo protegido (parametros.cubo_protegido)", 'COM-02, COM-03, COM-04'),
 ('R-REG-12', 'set', 'parametros.desagregaciones_contables', ['sexo', 'edad (cualquier agrupación)', 'programa o servicio', 'causa o diagnóstico', 'periodo menor que el año', 'establecimiento', 'condición (discapacidad, lengua…)'], 'COM-04'),
 ('R-REG-12', 'set', 'parametros.umbral_poblacion_desagregacion', {'solo_totales': 1000, 'max_1_desagregacion': 5000, 'nota': '5 000 es propuesta del auditor sin norma; revisable'}, 'COM-04'),
 ('R-REG-12', 'set', 'parametros.temas_sensibles', {'cie10': {'F00-F99': 'salud mental y adicciones', 'A50-A64, B20-B24': 'ITS y VIH', 'A15-A19': 'tuberculosis', 'O00-O08': 'aborto y pérdida del embarazo', 'X60-X84, R45.8': 'lesiones autoinfligidas', 'T74, Y05-Y07': 'maltrato y violencia'},
   'eventos': ['muerte materna', 'defunción fetal o infantil', 'madre menor de 18 años', 'violencia sexual', 'trata'],
   'fuentes_completas': ['MIMP-WARMINAN-BANCO-DATOS', 'MININTER-VIOLENCIA-MUJER-PNP']}, 'COM-05'),
 ('R-REG-12', 'set', 'parametros.nunca_publicar', ['DNI', 'nombres', 'fecha de nacimiento exacta', 'dirección', 'RUC con prefijo 10 o 15 (persona natural)', 'nombre de contratista persona natural',
   'nombres de residentes, supervisores, inspectores y funcionarios', 'código de estudiante o de afiliado', 'coordenadas de vivienda o de centro poblado con < 50 viviendas'], 'COM-06'),
 ('R-REG-12', 'set', 'parametros.cubo_protegido', {'mvp': 'fuentes sensibles solo en geografía vigente, años cerrados sueltos; sin GEO2017, sin ventanas de 3 años ni acumulados mensuales',
   'posterior': 'cubo precalculado por (fuente, año o ventana fija, jerarquía vigente y GEO2017, desagregaciones permitidas) con supresión primaria y complementaria conjunta a todas las geografías y periodos'}, 'COM-03'),
 ('R-REG-12', 'set', 'parametros.fuentes_sensibles_ola1', FUENTES_SENSIBLES, 'COM-01'),
 ('R-REG-12', 'set', 'referencias', [{'titulo': 'DS 016-2024-JUS, Reglamento de la Ley 29733 (vigente desde 30-03-2025)', 'url': 'https://iapp.org/news/a/se-publica-el-nuevo-reglamento-de-protecci-n-de-datos-personales-en-per-'},
   {'titulo': 'DS 043-2001-PCM, art. 97 (secreto estadístico)', 'url': None}], 'COM-06'),
 # ---- lenguaje (COM-07..09, COM-13, COM-15)
 ('R-LENGUAJE-02', 'set', 'condicion',
  "texto_llm = texto del LLM sin spans protegidos {{p:id}}; normalizar NFC + minúsculas + sin diacríticos (texto y patrones) salvo patrones con normalizar=false; "
  "match(lenguaje.prohibidas) → regenerar con la lista de infracciones; tras 2 intentos → plantilla determinista. "
  "Verbos de cambio solo dentro de {{v:id}} (el renderizador escribe el verbo según test_cambio); "
  "cada {{c:id}} con edad_dato > 2 debe ir en una oración con su año ('en {anio}'); cifras de tamizaje solo con {{u:id}} de tamizados; gasto solo con 'registrado por entidades con sede en'", 'COM-08, COM-09'),
 ('R-LENGUAJE-02', 'set', 'parametros.prueba_corrector', {'corpus': 'auditoria/scripts/com_corpus_lenguaje.json + holdout_orquestador.py', 'resultado_v11': '0/49 falsos positivos, 0/57 no detectadas (3 estructurales cubiertas por marcadores)', 'meta_mvp': 'corpus ≥ 200 oraciones con 40 % de reserva'}, 'COM-07'),
 ('R-CRUCES-05', 'replace', 'mensaje_usuario', 'exactamente', 'del todo', 'COM-09'),
 ('R-ENC-11', 'set', 'mensaje_usuario', "(p<0,05) 'La cifra {{v}} de {a} % a {b} %, y el cambio es estadísticamente claro.' (p≥0,05) 'La cifra pasó de {a} % a {b} %, pero la diferencia es tan pequeña que puede deberse a qué hogares tocó encuestar: no se puede afirmar que haya cambiado.'", 'COM-13'),
 ('R-GASTO-06', 'set', 'mensaje_usuario', "'Gastado' es lo que la entidad ya debe pagar porque recibió el bien o servicio (el MEF lo llama devengado). 'Presupuesto' es lo que tiene autorizado gastar en el año (el MEF lo llama PIM).", 'COM-13'),
 # ---- semáforo (COM-11, COM-14, EST-03, EST-09)
 ('R-CRUCES-09', 'set', 'parametros.rotulos', {'verde': 'Dato sólido', 'ambar': 'Dato con limitaciones', 'rojo': 'Dato muy aproximado', 'no_publicable': 'Sin datos suficientes'}, 'COM-11'),
 ('R-CRUCES-09', 'set', 'parametros.motivo_verde', 'Hay suficientes datos y son de {anio}.', 'COM-11'),
 ('R-CRUCES-09', 'set', 'parametros.iconos', {'verde': '✓', 'ambar': '!', 'rojo': '?', 'no_publicable': '—', 'accesibilidad': 'forma distinta por nivel, aria-hidden; el rótulo de texto siempre visible'}, 'COM-14'),
 ('R-CRUCES-09', 'set', 'parametros.criterios.cobertura_registro', '≥90 → 0; 80–89 → 1; 60–79 → 2; <60 o NULL → 3 para tasas (solo conteo). SIEN: tamizaje <50 % → 2', 'EST-03'),
 ('R-CRUCES-09', 'set', 'parametros.criterios.denominador', 'oficial INEI/MINSA del mismo año → 0; prorrateo propio con contraste y s ≤ 0,10 → 0; prorrateo propio sin contraste o con t − anio_censo > 6 → 1; s > 0,10 → 1', 'EST-09'),
 ('R-CRUCES-09', 'set', 'parametros.criterios.quiebre', 'es_comparable(fuente, indicador, anio_a, anio_b) = false → 3; comparable por excepción declarada (quiebres[].comparable_con) → 0; modalidad distinta sin declaración → 1', 'IMP-09'),
 ('R-CRUCES-09', 'set', 'parametros.criterios.vigencia', 'edad = anio_actual − anio_referencia (año central si es periodo agrupado; fin del periodo de referencia si existe), solo para la cifra más reciente de cada indicador: <=2 → 0; 3–5 → 1; >5 → 2. Los puntos de una serie heredan el semáforo de la comparación', 'EST-07'),
 ('R-ENC-02', 'replace', 'mensaje_usuario', 'Cifra referencial', 'Cifra aproximada', 'COM-11'),
 ('R-ENC-03', 'replace', 'mensaje_usuario', 'Cifra referencial', 'Cifra aproximada', 'COM-11'),
 ('R-ENC-04', 'replace', 'mensaje_usuario', 'Cifra referencial', 'Cifra aproximada', 'COM-11'),
 ('R-LENGUAJE-03', 'set', 'parametros.formato_numerico', "coma decimal; separador de miles U+202F (espacio fino no separable), sin separador en años, CUI y códigos; '%' precedido de espacio fino; rangos en palabras ('entre X y Y'), nunca con guion; 'pp' se escribe 'puntos porcentuales'; montos con aria-label en palabras", 'COM-14'),
 ('R-LENGUAJE-07', 'set', 'prioridad', 'mvp', 'COM-12'),
 ('R-LENGUAJE-07', 'set', 'parametros.perfiles', ['funcionario municipal de fuera de Lima (≥2)', 'periodista regional (≥2)', 'usuario de lector de pantalla (≥1)', 'persona bilingüe quechua o aimara–castellano (≥1)', 'ciudadano'], 'COM-12'),
 ('R-LENGUAJE-07', 'set', 'parametros.momento', 'condición antes del lanzamiento público (no de una beta cerrada)', 'COM-12'),
 # ---- encuestas: precisión (EST-01, 02, 06, 10, IMP-12)
 ('R-ENC-03', 'set', 'condicion', "n_sin_ponderar >= 50 AND (tipo_estimacion IN ('media','total','razon') → cv_ref = ee/|estimacion|; tipo_estimacion = 'proporcion' AND 0.10 <= p <= 0.90 → cv_ref = ee/min(p, 1−p)): cv_ref <= 0.15 → publicar; 0.15 < cv_ref <= 0.30 → publicar_referencial; cv_ref > 0.30 → suprimir; gl < 8 → publicar_referencial", 'EST-01, EST-10'),
 ('R-ENC-04', 'set', 'condicion', "tipo_estimacion = 'proporcion' AND (p < 0.10 OR p > 0.90) AND n_sin_ponderar >= 50: numerador == 0 → rotular 'menos de {ic_sup}'; numerador == n → rotular 'más de {ic_inf}'; n_efectivo < 30 → suprimir; ancho_abs <= 0.05 → publicar; ancho_abs >= 0.30 → suprimir; ancho_rel(p) > 1.30 → suprimir; ancho_rel(p) > 0.59 OR n_efectivo < 50 OR gl < 8 → publicar_referencial; resto → publicar. ancho_rel se calcula solo si 0 < p < 1", 'EST-02, IMP-12'),
 ('R-ENC-04', 'set', 'parametros.ancho_abs_presentar', 0.05, 'EST-02'),
 ('R-ENC-04', 'set', 'parametros.ancho_rel_referencial', 0.59, 'EST-02'),
 ('R-ENC-10', 'set', 'parametros.estrato_agrupado', 'si la encuesta repite conglomerados entre años (ENAHO): estrato original y UPM = id de conglomerado estable; si no (ENDES): anio × estrato', 'EST-06'),
 ('R-ENC-10', 'set', 'parametros.n_agrupado', 'número de unidades distintas (hogar o persona panel contado una vez); observaciones apiladas aparte', 'EST-06'),
 ('R-ENC-10', 'set', 'parametros.anio_referencia', 'año central (redondeado hacia arriba con k par); el rótulo muestra "promedio {anio_ini}–{anio_fin}"', 'EST-07'),
 ('R-ENC-11', 'set', 'parametros.cov_ab', "0 entre departamentos distintos o entre años con muestras independientes; si un territorio contiene al otro (departamento vs nacional) → comparar contra el resto del país o estimar la covarianza (svyby covmat + svycontrast); con panel o conglomerados repetidos → base apilada", 'EST-10'),
 ('R-ENC-11', 'set', 'parametros.p_valor', '2·P(T_gl > |t|), gl = min(gl_a, gl_b)', 'EST-10'),
 ('R-ENC-11', 'set', 'parametros.comparaciones_multiples', 'máx. 1 comparación por par de cifras; tendencias: primer vs último año del tramo sin quiebre', 'PR-33'),
 ('R-ENC-18', 'replace', 'condicion', 'indicador.validado_contra_oficial == false', 'indicador.validado_contra_oficial IS NOT TRUE', 'IMP-12'),
 # ---- aprendizajes (HEC-06)
 ('R-ENC-15', 'set', 'condicion', "fuente == 'MINEDU-UMC-ENLA' AND tipo_aplicacion(anio, grado) == 'muestral' AND nivel_pedido IN ('provincia','distrito','ugel','establecimiento') → agregar_nivel a region_umc; tipo_aplicacion == 'censal' → regla R-ENC-16", 'HEC-06'),
 ('R-ENC-15', 'set', 'parametros.tipo_aplicacion', {'ENLA 2022': 'muestral', 'ENLA 2023': 'muestral', 'ENLA 2024 4.º primaria': 'censal', 'ENLA 2024 6.º primaria': 'muestral', 'ENLA 2025': 'por confirmar (tratar como muestral)'}, 'HEC-06'),
 ('R-ENC-15', 'replace', 'mensaje_usuario', 'Esta evaluación se aplica a una muestra de escuelas', 'Esta evaluación se aplicó a una muestra de escuelas en este grado y año', 'HEC-06'),
 ('R-ENC-16', 'set', 'titulo', 'Evaluaciones censales de aprendizaje (ECE 2007–2019 y ENLA censal)', 'HEC-06'),
 ('R-ENC-16', 'set', 'aplica_a.fuentes', ['MINEDU-UMC-ECE', 'MINEDU-UMC-ENLA'], 'HEC-06'),
 ('R-ENC-16', 'set', 'condicion', "(fuente == 'MINEDU-UMC-ECE' OR tipo_aplicacion(anio, grado) == 'censal') AND nivel IN ('establecimiento','ugel','distrito'): n_evaluados < 10 → agregar_nivel; 10 <= n_evaluados < 20 → publicar_referencial; tasa_evaluados/matricula < 0.80 → advertir", 'HEC-06'),
 ('R-ENC-16', 'set', 'parametros.anios_censales', {'ECE': '2007–2019 según grado', 'ENLA': {'2024': ['4P']}}, 'HEC-06'),
 ('R-ENC-16', 'set', 'prioridad', 'mvp', 'HEC-06'),
 ('R-ENC-16', 'set', 'mensaje_usuario', "'En esta escuela se evaluó a pocos estudiantes ({n}); un par de alumnos cambian mucho el porcentaje. Mostramos el resultado de {ugel/distrito}.'", 'HEC-06'),
 # ---- anemia (HEC-07)
 ('R-ENC-14', 'set', 'parametros.disponibilidad_criterio', {'INEI-ENDES': {'RM251-2024/OMS2024': '2023–último publicado (oficial INEI)', 'RM363-2022/OMS2001': 'hasta el último publicado (2025 incluido)'},
   'INS-CENAN-SIEN': {'OMS2024': '2023 (serie recalculada)–', 'OMS2001/2017': 'hasta el último publicado'}}, 'HEC-07'),
 ('R-ENC-14', 'set', 'parametros.criterio_por_defecto_desde', None, 'HEC-07'),
 ('R-ENC-14', 'set', 'parametros.regla_tramos', 'comparar solo dentro del mismo criterio, con todos los años en que la fuente lo publica; cifra principal = criterio RM 251-2024 del año más reciente; el criterio anterior como serie larga rotulada. Después del MVP: recalcular la serie histórica con el criterio vigente desde microdatos (decisión D1)', 'HEC-07'),
 ('R-ENC-14', 'set', 'mensaje_usuario', "'La anemia se mide hoy con un criterio nuevo (Norma del MINSA de 2024, basada en la OMS), que da cifras más bajas, sobre todo en zonas de altura. Solo comparamos años medidos con el mismo criterio.'", 'HEC-07'),
 ('R-REG-10', 'set', 'parametros.quiebres_a_registrar.INS-CENAN-SIEN', '2020: la vigilancia nutricional pasa a alimentarse del HIS; criterio de anemia: ver R-ENC-14.disponibilidad_criterio (no un año fijo)', 'HEC-07'),
 ('R-REG-10', 'set', 'parametros.quiebres_a_registrar.MINSA-SINADEF', '2017–2020: cobertura creciente por el certificado en línea (29 % en 2017 → 86 % en 2020); 2020–2021: exceso de mortalidad COVID-19', 'HEC-09'),
 # ---- registros: cobertura y cambio (EST-03, EST-08, EST-11, EST-13, IMP-09)
 ('R-REG-07', 'set', 'condicion', "c := cobertura_registro_estimada(fuente, departamento, anio, grupo_edad); c IS NULL OR c < 60 → suprimir la tasa y publicar solo el conteo; 60 ≤ c < 80 → publicar_referencial con advertencia de subregistro; 80 ≤ c < 90 → publicar_referencial como 'tasa registrada'; c ≥ 90 → publicar como 'tasa registrada'. SIEN: cobertura_tamizaje = evaluados / poblacion_objetivo; < 50 % → publicar_referencial con advertencia de selección", 'IMP-09, EST-03'),
 ('R-REG-07', 'set', 'parametros.fuente_cobertura_SINADEF_infantil', 'defunciones < 1 año registradas / (TMI estimada INEI-ENDES del departamento × nacidos vivos estimados)', 'EST-03'),
 ('R-REG-07', 'set', 'aplica_a.fuentes', ['MINSA-SINADEF', 'MINSA-CNV-NACIDOS-VIVOS', 'INS-CENAN-SIEN', 'CDC-VIGILANCIA-DATOS-ABIERTOS', 'MINSA-REUNIS'], 'IMP-02'),
 ('R-REG-04', 'set', 'condicion', "indicador IN (TMI, TMN, RMM) AND (nacidos_vivos_periodo < 1000 OR defunciones_periodo < 5) → agregar_nivel; 5 ≤ defunciones_periodo < 20 → publicar_referencial; nivel = 'distrito' AND periodo_agrupado = 1 año → suprimir. Cobertura: R-REG-07 con la cobertura infantil (fuente_cobertura_SINADEF_infantil)", 'IMP-09, EST-03'),
 ('R-REG-03', 'set', 'parametros.tramo_5_10', '5 ≤ numerador < 11 → mostrar solo el IC de Poisson, sin valor puntual, semáforo rojo; 11–19 → publicar_referencial (ámbar)', 'EST-11'),
 ('R-REG-03', 'set', 'parametros.nota_minimo_5', 'El mínimo de 5 es un criterio de confidencialidad (R-REG-12), no de fiabilidad (NY DOH respalda solo el umbral de 20).', 'EST-11'),
 ('R-REG-14', 'set', 'condicion', "significativo = p < alfa AND (|RR − 1| ≥ 0.10 para tasas OR |p1 − p0| ≥ 0.02 para proporciones) AND |diferencia| > 2 × sd(variaciones interanuales de los 5 años previos sin quiebre) AND |c(t1) − c(t0)| ≤ 5 pp AND min(c(t0), c(t1)) ≥ 80; si no → 'no se puede afirmar que haya cambiado'", 'EST-08, IMP-09'),
 ('R-REG-14', 'set', 'parametros.relevancia_minima', {'tasas_rr': 0.10, 'proporciones_pp': 2}, 'EST-08'),
 ('R-REG-14', 'set', 'parametros.sobredispersion', 'quasi-Poisson; sd de variaciones interanuales de 5 años sin quiebre', 'EST-08'),
 ('R-REG-06', 'set', 'parametros.s2', 's² = max(0, Σ n_i (r_i − m)² / Σ n_i − m / n̄), n̄ = Σ n_i / N; si s² = 0, θ_i = m', 'EST-13'),
 ('R-EST-01', 'set', 'parametros.dci_cv_publicar', 15, 'EST-12'),
 ('R-EST-01', 'replace', 'condicion', 'DCI: cv < 10 → publicar, 10 ≤ cv < 20', 'DCI: cv < 15 → publicar (confiable y aceptable INEI), 15 ≤ cv < 20', 'EST-12'),
 ('R-EST-01', 'replace', 'condicion', 'incertidumbre_publicada = false', 'incertidumbre_publicada IS NOT TRUE', 'IMP-12'),
 ('R-EST-01', 'set', 'aplica_a.fuentes', ['INEI-MAPA-POBREZA', 'INEI-MAPA-DCI-PROVINCIAL-2019', 'PNUD-IDH-DISTRITAL', 'MIDIS-PMA-MAPA-VULNERABILIDAD'], 'IMP-02'),
 # ---- asociación (EST-05, IMP-08)
 ('R-CRUCES-06', 'set', 'condicion', "N = territorios del mismo nivel con ambos valores publicables (semaforo_cifra in ('verde','ambar')): provincias o distritos dentro de un departamento, o los 25 departamentos a nivel nacional. N < 20 OR excluidos/(N+excluidos) > 0,20 → solo tabla y mapa lado a lado, sin coeficiente; N ≥ 20 → coeficiente con semáforo ámbar fijo. Fuerza según el límite del IC más cercano a 0 (|límite| < 0,30 → 'débil o nula'). IC95 que contiene 0 → 'no se observa una asociación clara'", 'EST-05, IMP-08'),
 ('R-CRUCES-06', 'set', 'parametros.n_min_coeficiente', 20, 'IMP-08'),
 ('R-CRUCES-06', 'set', 'parametros.n_min_no_referencial', None, 'IMP-08'),
 ('R-CRUCES-10', 'replace', 'condicion', 'OR (coeficiente con 10<=N<20) ', '', 'IMP-08'),
 # ---- denominadores y población (HEC-01, 04, 05, IMP-06, 07, 16)
 ('R-CRUCES-08', 'set', 'parametros.jerarquias.poblacion', "Conteo de habitantes: nacional y departamental 2025 = población total INEI (censada + omisión), rotulada 'población total estimada por el Censo 2025'; provincia y distrito 2025 = población censada, rotulada 'personas censadas (no incluye omisión censal, 4,25 % nacional)'. Denominadores de tasas de cualquier año = proyección INEI del vintage de la serie (R-DENOMINADORES-01/02); CPV2025 solo contraste ajustado por omisión. Edades a distrito: prorrateo propio (D8); MINSA contraste; RENIEC nunca como residentes", 'HEC-01, IMP-06'),
 ('R-CRUCES-08', 'set', 'aplica_a.fuentes', ['INEI-ENDES', 'INS-CENAN-SIEN', 'MINSA-REUNIS', 'INEI-ENAHO', 'INEI-MAPA-POBREZA', 'MINSA-INMUNIZACIONES', 'MINSA-SINADEF', 'MINSA-CNV-NACIDOS-VIVOS'], 'IMP-02'),
 ('R-CRUCES-08', 'set', 'insumos_regla', ['INEI-PROYECCIONES-POBLACION-DISTRITAL', 'INEI-CPV2025', 'MINSA-POBLACION-ESTIMADA', 'RENIEC-POBLACION-IDENTIFICADA'], 'IMP-02'),
 ('R-CRUCES-08', 'set', 'parametros.jerarquias.mortalidad_infantil', 'nacional: ENDES, 5 años previos a la encuesta; departamento: ENDES de dos rondas agrupadas por el INEI, 10 años previos (guardar periodo_referencia_ini/fin); MINSA-SINADEF/CNV registrada complementaria; provincia/distrito: solo registrada (R-REG-04, R-REG-07)', 'HEC-08'),
 ('R-CRUCES-03', 'replace', 'condicion', 'con anio_ref = año central si hay agrupación de años', 'con anio_ref = punto medio de [periodo_referencia_ini, periodo_referencia_fin] si existen; si no, anio_referencia (año central si hay agrupación); velocidad_cambio IS NULL → bloquear_cruce (metadato_faltante)', 'HEC-08, IMP-12'),
 ('R-DENOMINADORES-01', 'set', 'parametros.matriz.cobertura_salud_por_edad (vacunas <1 y <5, CRED, tamizaje, gestantes)', {'principal': 'prorrateo propio INEI (R-DENOMINADORES-03)', 'contraste': ['MINSA-POBLACION-ESTIMADA', 'Padrón Nominal agregado (<6 años)'], 'nivel_minimo': 'provincia si base_geografica_usada = establecimiento; distrito si residencia'}, 'IMP-06, IMP-07'),
 ('R-DENOMINADORES-01', 'set', 'parametros.matriz.cobertura_programa_por_edad_no_salud (Pensión 65 ≥65, matrícula 3-5/6-11/12-16)', {'principal': 'prorrateo propio INEI (R-DENOMINADORES-03)', 'contraste': ['MINSA-POBLACION-ESTIMADA', 'INEI-CPV2025 solo total y 60+ (ajustado por omisión)'], 'nivel_minimo': 'distrito (referencial)'}, 'IMP-09'),
 ('R-DENOMINADORES-04', 'set', 'condicion', "fuente_denominador = 'INEI-CPV2025' AND anio ≠ 2025 → suprimir; P_cpv2025_ajustada(d) = P_censada(d) / (1 − omision(d)), omision = departamental si el INEI la publica, si no 0.0425 (registrar cuál); |P_proy2017(d,2025) − P_cpv2025_ajustada(d)| / P_cpv2025_ajustada(d) > 0.10 → advertir en todas las tasas 2025 del distrito; existe vintage base CPV2025 → revision_humana (migrar): si incluye años anteriores a 2025 se migra toda la serie; si empieza en 2025, dos tramos rotulados (base 2017 hasta 2024; base 2025 desde 2025) sin variación entre tramos", 'HEC-04, HEC-05'),
 ('R-DENOMINADORES-04', 'set', 'parametros.estado_proyecciones_base2025', 'no publicadas (verificado 2026-10-05); revisar mensualmente', 'HEC-05'),
 ('R-DENOMINADORES-04', 'replace', 'mensaje_usuario', 'difiere en {pct} % de la contada en el Censo 2025', 'difiere en {pct} % de la población del Censo 2025 (personas censadas ajustadas por omisión censal)', 'HEC-04'),
 ('R-DENOMINADORES-03', 'set', 'implementacion', 'IPF: total distrital INEI (proyección del vintage) × estructura por edad y sexo del censo semilla. La semilla CPV2025 se adopta solo junto con la migración de base de R-DENOMINADORES-04, para todos los años de la serie a la vez; mientras tanto, semilla = CPV2017. La semilla forma parte del vintage ("|semilla=CPV2017").', 'IMP-16'),
 ('R-DENOMINADORES-05', 'replace', 'condicion', 's ≤ 0.10 → publicar;', 's ≤ 0.10 → publicar; s IS NULL AND metodo = prorrateo_propio → publicar_referencial con rótulo de estimación propia;', 'EST-09'),
 ('R-REG-02', 'set', 'condicion', "indicador.base_geografica_usada IN ('establecimiento','ocurrencia') AND indicador.tipo_estimacion IN ('tasa','cobertura','proporcion') AND denominador.tipo_poblacion = 'residente' AND nivel_pedido = 'distrito' → agregar_nivel('provincia'); denominador = personas atendidas en el mismo establecimiento (p. ej., tamizados) → publicar con rótulo de establecimiento; conteos → publicar por distrito con rótulo 'en establecimientos ubicados en' (D4)", 'IMP-07'),
 # ---- insumos vs cifras evaluadas (IMP-02)
 *[(rid, 'mover_fuentes_a_insumos', None, 'IMP-02') for rid in ['R-DENOMINADORES-01', 'R-DENOMINADORES-02', 'R-DENOMINADORES-03', 'R-DENOMINADORES-04', 'R-DENOMINADORES-05', 'R-DENOMINADORES-07', 'R-TERRITORIO-01', 'R-TERRITORIO-03']],
 ('R-GASTO-11', 'set', 'aplica_a.fuentes', ['MEF-DA-PRESUPUESTO-EJECUCION-GASTO', 'MEF-DA-GASTO-GPNNA'], 'IMP-02'),
 ('R-GASTO-11', 'set', 'insumos_regla', ['INEI-PROYECCIONES-POBLACION-DISTRITAL', 'INEI-PROYECCIONES-DEPARTAMENTAL-EDAD', 'MINSA-POBLACION-ESTIMADA'], 'IMP-02'),
 ('R-GASTO-12', 'set', 'aplica_a.fuentes', ['MEF-DA-PRESUPUESTO-EJECUCION-GASTO', 'MEF-DA-GASTO-GPNNA', 'MEF-SEGUIMIENTO-PI', 'MEF-DA-TRANSFERENCIAS'], 'IMP-02'),
 ('R-GASTO-12', 'set', 'insumos_regla', ['INEI-IPC (BCRP PN38705PM)'], 'IMP-02'),
 # ---- motor (IMP-03, IMP-11, IMP-13, IMP-17)
 ('R-MOTOR-01', 'set', 'condicion', "estado_cifra == 'suprimida' AND motivo IN motivos_degradables AND paso < len(secuencia[naturaleza_dato]) → siguiente paso de la secuencia que cumpla el nivel_minimo solicitado; las reglas de las etapas 2–4 no cambian el nivel: emiten solicitar_degradacion(motivo, nivel_minimo). La secuencia es monótona (el nivel y la ventana nunca retroceden)", 'IMP-03'),
 ('R-MOTOR-01', 'set', 'parametros', {'secuencia_degradacion': {
    'encuesta_muestral': ['anio', 'agrupar_3_anios', 'departamento_anio', 'departamento_3_anios', 'suprimir'],
    'registro_administrativo': ['anio', 'agrupar_3_anios', 'provincia_anio', 'provincia_3_anios', 'departamento', 'suprimir'],
    'indicadores_derivados': ['anio', 'agrupar_3_anios', 'provincia_anio', 'provincia_3_anios', 'departamento', 'suprimir'],
    'registro_eventos_mortalidad': ['anio', 'agrupar_3_anios', 'agrupar_5_anios', 'provincia_5_anios', 'departamento_5_anios', 'suprimir'],
    'estimacion_modelada': ['anio', 'suprimir'], 'censo': ['anio', 'suprimir'],
    'presupuestal_financiero': ['nivel_atribuible', 'respuesta_parcial']},
   'motivos_degradables': ['precision', 'pocos_casos', 'nivel_no_representativo', 'base_establecimiento', 'cobertura_mayor_110'],
   'no_degradables': ['sin_datos', 'metadato_faltante', 'divulgacion']}, 'IMP-03'),
 ('R-DEP-01', 'set', 'condicion', "ANY(i.compuerta_ingesta != 'aprobada' FOR i IN indicador.insumos WHERE i.rol IN ('numerador','denominador_principal','tabla_curada')) → estado_cifra = 'sin_datos', motivo = 'insumo_en_ingesta'; insumos con rol = 'contraste' no aprobados → se omiten y se anota en la ficha larga", 'IMP-11, HEC-03'),
 ('R-DEP-01', 'set', 'parametros.insumos_bloqueantes_mvp', ['INEI-PROYECCIONES-POBLACION-DISTRITAL', 'INEI-PROYECCIONES-DEPARTAMENTAL-EDAD', 'INEI-CPV2017', 'INEI-DIRECTORIO-MUNICIPALIDADES', 'MEF-PPR-PROGRAMAS-PRESUPUESTALES'], 'IMP-11, HEC-03, IMP-06'),
 ('R-DEP-01', 'set', 'parametros.insumos_contraste_opcionales', ['INEI-CPV2025', 'MINSA-POBLACION-ESTIMADA', 'RENIEC-POBLACION-IDENTIFICADA'], 'HEC-03'),
 ('R-GASTO-17', 'set', 'condicion', "intencion_pregunta == 'listar_obras' → top_n(dim_inversion WHERE ubigeo = pedido, orden = devengado_acumulado_constante DESC, n = 10). El periodo por defecto lo fija R-MOTOR-03", 'IMP-13'),
 ('R-GASTO-17', 'set', 'aplica_a.naturaleza_dato', ['presupuestal_financiero'], 'IMP-18'),
 ('R-CRUCES-01', 'set', 'parametros.orden_niveles', 'ver parametros_globales.NIVEL_RANK', 'IMP-17'),
 # ---- territorio y gasto (HEC-10, HEC-11, IMP-10, IMP-15, IMP-18)
 ('R-TERRITORIO-01', 'set', 'parametros.distritos_esperados_vigentes_2026', None, 'HEC-10'),
 ('R-TERRITORIO-01', 'set', 'parametros.distritos_esperados', "COUNT(estado_ubigeo = 'vigente') en la versión de la tabla; alerta si difiere del último listado INEI. Cronología: 1 874 (CPV2017) → +16 (2020–2021, Lib1860 Anexo 3) = 1 890 → +Alto Trujillo (Ley 31644, 2022) = 1 891 → +Santa Rosa de Loreto (Ley 32403, 2025; grupo comparable GEO2017 = Yavarí) = 1 892", 'HEC-10'),
 ('R-TERRITORIO-08', 'set', 'aplica_a.naturaleza_dato', ['registro_administrativo', 'indicadores_derivados'], 'IMP-10'),
 ('R-TERRITORIO-08', 'set', 'parametros.gasto', 'el control territorial del gasto es la conservación de R-GASTO-01 (suma de niveles = total nacional, tolerancia 0) y pct_proyectos_sin_ubicacion; R-GASTO-03 decide el nivel publicable', 'IMP-10'),
 ('R-TERRITORIO-07', 'set', 'prioridad', 'mvp', 'IMP-15'),
 ('R-ENC-07', 'set', 'parametros.dominios_lima', {'ENAHO 2019–2025': "'Área Metropolitana de Lima y Callao' = 1501 + 0701 (Callao no es dominio separado)", 'ENDES 2019–2025': "'Lima Metropolitana' = 1501 (43 distritos); 'Callao' = 07 dominio propio; 'Lima Región/Provincias' = 15 sin 1501"}, 'HEC-11'),
 ('R-ENC-13', 'set', 'justificacion', 'ENAHO 2020: modalidad mixta por la pandemia. ENAHO 2021: 95,6 % de entrevistas presenciales y 4,4 % telefónicas, con cuestionario reducido en 32 provincias en alerta extrema. La Comisión Consultiva para la Estimación de la Pobreza declaró la pobreza 2020 y 2021 comparable con los años anteriores.', 'HEC-12'),
 ('R-GASTO-13', 'set', 'parametros.lima_en_ranking', 'marcar', 'IMP-18'),
 ('R-GASTO-11', 'borde', 'Lima y Callao en rankings: se rotulan y marcan (R-GASTO-13), no se excluyen.', 'IMP-18'),
 ('R-GASTO-12', 'borde', 'Deflactor fijado por D6 (IPC Lima, base último año cerrado).', 'IMP-18'),
 ('R-GASTO-03', 'set', 'parametros.respaldo_departamental', "departamento == '15' → respuesta_parcial (gasto municipal y de obras) con NC-GASTO-LUGAR; en otro caso, cifra departamental", 'IMP-09, PR-15'),
 ('R-GASTO-02', 'set', 'parametros.inversion_ubicacion_unica', 'campo de catálogo (bool) de MEF-DETALLE-INVERSIONES; si true → cifra distrital referencial con rótulo de ubicación principal y criterio base_geografica = 1', 'IMP-09'),
]

# Renombres mecánicos de sinónimos reales (IMP-05). Los campos que no son sinónimos se conservan (ver CAMPOS_CORREGIDOS).
RENOMBRES = {
 r'\bestado_precision\b': 'estado_cifra', r'\bestado_estabilidad\b': 'estado_cifra', r"'suprimido'": "'suprimida'",
 r'\bnivel_solicitado\b': 'nivel_pedido', r'\bdenominador_tipo\b': 'tipo_denominador', r'\banios_agrupados\b': 'periodo_agrupado',
 r'\bpoblacion_objetivo_dominio\b': 'poblacion_objetivo', r'\bcomparable_en_quiebre\b': 'quiebres[].comparable_con',
 r'\bfecha_cierre_fuente\b': 'fecha_corte', r'\bdenominador_fuente\b': 'vintage_denominador', r'\bnivel_valido\b': 'nivel_publicado',
}
CAMPOS_CORREGIDOS = [  # (campo, nivel, reemplaza, para qué)
 ('base_geografica_usada', 'indicador', '— (no se fusiona con nivel_publicado)', 'Base geográfica con la que se construye el indicador; las reglas la evalúan sobre el indicador, no sobre el catálogo.'),
 ('nivel_atribucion_gasto', 'fila de gasto', '—', 'Nivel al que se puede atribuir una fila de gasto (R-GASTO-01).'),
 ('incertidumbre_publicada', 'catálogo', '—', 'Si la fuente publica IC o CV (bool).'),
 ('rank_concepto', 'indicador', '—', '1 = mide el concepto; 2 = aproximación (R-CRUCES-08).'),
 ('grupo_robusto', 'cifra', '—', 'Grupo de territorios estadísticamente semejantes (R-EST-01, R-EST-05).'),
  ('tema / es_socioeconomico / universo / origen_cifra', 'indicador', 'tema, socioeconómico, universo, origen', 'Vocabularios controlados (IMP-05).'),
 ('ubicado_por_cui', 'fila de gasto', '—', 'Si la fila de inversión tiene ubigeo por CUI.'),
 ('insumos[] = {id, rol}', 'indicador', 'insumos', 'rol ∈ numerador | denominador_principal | contraste | tabla_curada (R-DEP-01).'),
 ('insumos_regla', 'regla', 'fuentes de aplica_a que eran insumos', 'Tablas que la regla consulta; aplica_a filtra las cifras evaluadas (IMP-02).'),
 ('tipo_aplicacion', 'catálogo (evaluación × año × grado)', '—', 'censal | muestral (ENLA/ECE, HEC-06).'),
  ('unidad_observacion', 'catálogo', '—', 'persona | hogar | estudiante | caso | establecimiento | entidad (R-REG-12).'),
 ('cv_ref', 'cifra', '—', 'CV de referencia (sobre min(p, 1−p) en proporciones, EST-01).'),
 ('tasa_ajustada_edad', 'cifra', '—', 'Tasa estandarizada por edad (R-REG-15).'),
]
TABLAS_MVP = {  # IMP-14
 'imprescindibles': ['dim_indicador (todos los campos de nivel indicador)', 'dim_ubigeo_historico', 'dim_dominio', 'fact_poblacion', 'dim_unidad_ejecutora', 'dim_tema_gasto',
                     'dim_inversion_ubicacion', 'dim_ipc (BCRP PN38705PM)', 'cobertura_registro_estimada (nombre único; insumos: nacimientos y defunciones estimados INEI por departamento y año)', 'validaciones', 'puente_ubigeo (si alguna fuente MVP resulta RENIEC)'],
 'con_respaldo_vacias': {'cruces_permitidos': 'sin fila → lado a lado', 'evaluaciones_relacionadas': 'frase fija', 'ambito_ejecutora': 'solo DIRIS y UGEL de Lima Metropolitana',
                         'explicaciones_divergencia': "texto por defecto: 'Las fuentes miden cosas distintas: {rotulo_a} y {rotulo_b}'"},
}
NIVEL_RANK = {'manzana_conglomerado': 0, 'centro_poblado': 1, 'distrito': 2, 'provincia': 3, 'departamento': 4, 'dominio_subnacional': 5, 'nacional': 6,
              'nota': 'dominio_subnacional = Lima Metropolitana, Lima Provincias, Callao (ENDES), regiones naturales, área. Dominio × departamento con ubigeos que no coinciden → re-estimar la encuesta para el departamento completo.'}
FICHA = {  # COM-02, COM-15
 'corta_confianza': "Confianza: {rotulo} — {motivo}. {si ambar/rojo y hay rango: 'La cifra real puede estar entre {inf} y {sup}.'}",
 'corta_no_concluir': 'No permite concluir: {hasta 2 códigos: NC-ACTUAL si está activo + el de mayor prioridad}',
 'larga_precision': "{rotulo}. {si encuesta: 'El valor real está probablemente entre {ic_inf} y {ic_sup}.'} {si registro: 'Basado en {numerador_redondeado} casos registrados' (con numerador < umbral de R-REG-12: 'menos de {umbral} casos')} {motivos_semaforo en texto}",
}
AJUSTES_DECISIONES = {
 'D9': 'MVP: tabla y mapa lado a lado. Coeficiente solo con N ≥ 20 territorios del mismo nivel (provincias o distritos dentro de un departamento, o los 25 departamentos a nivel nacional) y siempre en ámbar.',
}
CATALOGO = [  # correcciones al catálogo (se aplican en catalogo/scripts/correcciones_src.py)
 ('INEI-CPV2025', 'HEC-02', 'Publicado: 29-05-2026 primeros resultados (nacional y departamental; total con omisión 34 157 732; censada 32 706 028; omisión 4,25 %). 10-07-2026: población censada por provincia y distrito (sexo y grandes grupos de edad 0–14/15–59/60+) en tablero y PDF de presentación (con grupos quinquenales). No publicados al 05-10-2026: REDATAM, microdatos, Excel, edad simple o quinquenal por distrito, omisión subnacional, proyecciones base 2025.'),
 ('GITHUB-UBIGEO-PERU-AUMENTADO', 'HEC-10', 'Falta también Santa Rosa de Loreto (Ley 32403, 2025, segregado de Yavarí).'),
 ('MINEDU-UMC-ENLA', 'HEC-06', 'ENLA 2024 4.º de primaria fue censal (más de 532 mil estudiantes en más de 18 mil IIEE), con resultados por región, UGEL e IE; 6.º de primaria muestral. ENLA 2022–2023 muestrales.'),
 ('MINSA-SINADEF', 'HEC-09', 'Quiebre 2017–2020 por implementación del certificado en línea (29 % en 2017 → 86 % en 2020); el "~49 %" era la proporción de certificados en línea a julio de 2018, no la cobertura del registro (71,6 % con certificación médica en 2019).'),
]

POST_RENOMBRE = [  # ajustes de valor tras renombrar (estado_estabilidad no tenía equivalente directo en estado_cifra)
 ('R-REG-05', 'condicion', "estado_cifra != 'estable'", "'pocos_casos' IN motivos (numerador < 20, R-REG-03)"),
 ('R-REG-05', 'enunciado', "estado_estabilidad distinto de 'estable'", "motivo 'pocos_casos' (numerador < 20)"),
]

# ---------------------------------------------------------------- segunda ronda (verificación independiente de la v1.1)
# auditoria/verificacion_v11.json: 25 aplicados, 28 parciales, 5 con error, 1 no aplicado y 20 contradicciones nuevas. Todo aceptado.
SENSIBLES_V2 = ['MINSA-REUNIS', 'CDC-VIGILANCIA-DATOS-ABIERTOS', 'ESSALUD-DATOS-ABIERTOS', 'SIS-ATENCIONES', 'INS-CENAN-SIEN', 'MINEDU-CENSO-EDUCATIVO',
                'MIMP-WARMINAN-BANCO-DATOS', 'MININTER-VIOLENCIA-MUJER-PNP', 'MINEDU-SISEVE', 'CONADIS-RNPCD', 'CONTIGO-USUARIOS', 'CDC-SALA-MUERTE-MATERNA', 'INSM-EESM']
PARCHES_V2 = [
 # privacidad (COM-01..05, IMP-01; contradicciones 2, 3, 20)
 ('R-REG-12', 'set', 'aplica_a', {'naturaleza_dato': [], 'tipo_medida': [], 'base_geografica': [], 'fuentes': []}, 'COM-01'),
 ('R-REG-12', 'set', 'enunciado', 'Ninguna cifra (conteo, tasa o proporción) puede permitir identificar a una persona: se suprimen numeradores pequeños y sus complementos, se limitan las desagregaciones según la población del territorio, los temas sensibles se publican desde la provincia, y las fuentes sensibles se sirven solo desde un cubo protegido.', 'COM-01'),
 ('R-REG-12', 'set', 'condicion',
  "Aplica si sensibilidad_divulgacion(fuente, celda) != 'ninguna' (campo obligatorio del catálogo; NULL se trata como 'normal'; fuente ∈ fuentes_sensibles o celda con código ∈ temas_sensibles → 'sensible'). "
  "(1) 1 ≤ numerador < umbral(sensibilidad) → suprimir el valor, su IC y su rango (también la tasa o proporción) y aplicar supresión complementaria entre la celda y sus niveles superior e inferior; "
  "(2) sensibilidad = 'sensible' AND 1 ≤ denominador − numerador < umbral → suprimir; "
  "(3) sensibilidad = 'sensible' → nivel mínimo provincia, salvo distrito con población ≥ 20 000 y celda ≥ 10; "
  "(4) poblacion < 1000 → solo totales anuales sin desagregar; no publicar celdas 0 ni celdas iguales al total; "
  "(5) 1000 ≤ poblacion < 5000 → máximo 1 desagregación; en otro caso máximo 2; "
  "(6) centro poblado → solo total y solo si ≥ 10; "
  "(7) fuentes sensibles → solo cubo protegido (parametros.cubo_protegido); numerador publicado = numerador_redondeado", 'COM-02, COM-03, COM-04'),
 ('R-REG-12', 'set', 'parametros.fuentes_sensibles_ola1', SENSIBLES_V2, 'COM-05'),
 ('R-REG-12', 'set', 'parametros.temas_sensibles.cie10.O95-O99', 'muerte materna', 'COM-05'),
 ('R-REG-12', 'set', 'parametros.umbral_sensible_distrito', {'poblacion_min': 20000, 'celda_min': 10, 'respaldo': 'CHHS (11 casos / 20 000 personas)'}, 'COM-04'),
 ('R-REG-12', 'set', 'parametros.numerador_redondeado', "numerador < umbral → 'menos de {umbral}'; sensible y numerador < 100 → redondeo a la decena; resto sin cambio", 'COM-02'),
 ('R-REG-12', 'set', 'parametros.prueba_restas', 'antes de publicar una celda de fuente sensible, comprobar que no se obtiene por diferencia con otras celdas publicadas del mismo cubo (niveles superior/inferior, desagregaciones, años)', 'COM-03'),
 ('R-REG-12', 'replace', 'casos_borde', 'registrar las consultas servidas por sesión y negar la que complete la diferencia (posterior)', 'se evita sirviendo las fuentes sensibles solo desde el cubo protegido con supresión complementaria conjunta (parametros.cubo_protegido); el control por sesión no sirve en una web sin login', 'COM-03'),
 ('R-MOTOR-01', 'set', 'parametros.secuencia_degradacion.fuente_sensible', ['anio', 'provincia_anio', 'departamento_anio', 'suprimir'], 'COM-03'),
 ('R-MOTOR-01', 'set', 'parametros.prioridad_secuencia', "sensibilidad_divulgacion = 'sensible' → secuencia fuente_sensible (sin agrupar años ni GEO2017); si no, la de su naturaleza_dato", 'COM-03'),
 ('R-TERRITORIO-04', 'set', 'parametros.fuentes_sensibles', 'geografía vigente del último año; series solo con años sueltos (R-REG-12 cubo protegido)', 'COM-03'),
 # lenguaje (COM-08..13; contradicciones 8, 9, 10, 11, 12, 19)
 ('R-LENGUAJE-02', 'set', 'condicion',
  "texto_llm = texto del LLM sin spans protegidos {{p:id}} (todo mensaje_usuario, frase_estandar y texto de ficha se inserta como {{p:id}}); normalizar NFC + minúsculas + sin diacríticos (texto y patrones) salvo patrones con normalizar=false; "
  "match(lenguaje.prohibidas) → regenerar con la lista de infracciones; tras 2 intentos → plantilla determinista; tasa de regeneración por categoría > 5 % en producción → esa categoría pasa a plantilla. "
  "Verbos de cambio solo dentro de {{v:id}}; cada {{c:id}} con edad_dato > 2 va en una oración con 'en {anio}'; cifras de tamizaje solo con {{u:id}}; gasto con base ejecutora → 'registrado por unidades ejecutoras con sede en' o 'la municipalidad'; gasto por CUI → 'obras ubicadas en'", 'COM-08'),
 ('R-LENGUAJE-02', 'set', 'implementacion', "Lista de regex en lenguaje.prohibidas (sin excepciones léxicas: los verbos de cambio y los montos van en marcadores). Revisión humana de un 5 % de respuestas publicadas y de todas las que fueron regeneradas 2 veces.", 'COM-08'),
 ('R-LENGUAJE-02', 'replace', 'casos_borde', '"estadísticamente significativo" está permitido.', 'Se usa "estadísticamente claro"; "significativo" queda prohibido para evitar dos vocabularios.', 'COM-13'),
 ('R-LENGUAJE-03', 'set', 'parametros.marcadores', {'{{c:id}}': 'cifra', '{{v:id}}': 'verbo de cambio según test_cambio', '{{u:id}}': 'universo (tamizados, atendidos, notificados, usuarios) desde indicador.poblacion_objetivo', '{{e:id}}': 'entidad (colegio, obra, norma)', '{{p:id}}': 'texto fijo protegido del sistema'}, 'COM-08'),
 ('R-LENGUAJE-05', 'replace', 'condicion', "'juicio_personas'", "'juicio_personas_privadas'", 'COM-10'),
 ('R-LENGUAJE-08', 'set', 'parametros.ranking_entidades', 'por quintiles de avance de ejecución con fecha de corte, sin orden interno; nunca "la que peor gasta"', 'COM-10'),
 ('R-LENGUAJE-08', 'set', 'parametros.pruebas', 'pares simétricos ataque/elogio en el corpus del corrector; revisión humana del 100 % de juicio_autoridad durante los 3 meses posteriores a las elecciones', 'COM-10'),
 ('R-LENGUAJE-07', 'set', 'condicion', "prueba_usuarios.n >= 8 AND por cada tarea (¿la cifra dice que el gasto causó el resultado? / ¿qué significa el rótulo de confianza? / ¿la cifra es de este año? / ¿qué no permite concluir?) tasa_aciertos >= 0.75", 'COM-12'),
 ('R-CRUCES-09', 'replace', 'ejemplo', "rojo 'Solo como referencia'", "rojo 'Dato muy aproximado'", 'COM-11'),
 ('R-CRUCES-09', 'set', 'parametros.ayuda_rotulo', 'La confianza indica si hay suficientes datos y si son recientes. No indica qué causó el problema. Si el motivo es la antigüedad, se dice: "dato exacto pero de {anio}".', 'COM-11'),
 ('R-ENC-06', 'replace', 'mensaje_usuario', 'dar una cifra confiable para', 'dar una cifra con suficiente precisión para', 'COM-11'),
 ('R-ENC-02', 'replace', 'mensaje_usuario', 'para dar una cifra confiable', 'para dar una cifra con suficiente precisión', 'COM-11'),
 ('R-CRUCES-01', 'replace', 'mensaje_usuario', 'solo es confiable hasta ese nivel', 'solo da cifras con suficiente precisión hasta ese nivel', 'COM-11'),
 ('R-REG-03', 'set', 'mensaje_usuario', 'Hay pocos casos en este territorio, así que la cifra puede variar mucho de un año a otro por azar. Por eso {sumamos 3 años | mostramos la provincia}. La cifra real está probablemente entre {ic_inf} y {ic_sup}.', 'COM-14'),
 ('R-EST-03', 'set', 'mensaje_usuario', 'Esta cifra es un cálculo propio de Pregunta al Perú combinando {fuentes}; no es una cifra oficial. El valor real está probablemente entre {inf} % y {sup} %.', 'COM-14'),
 ('R-GASTO-03', 'replace', 'mensaje_usuario', '{pct}%', '{pct} %', 'COM-14'),
 ('R-ENC-03', 'set', 'mensaje_usuario', "(15–30 %) 'Cifra aproximada: la encuesta tiene pocos datos para este grupo; el valor real podría estar entre {ic_inf} y {ic_sup}.' (>30 %) 'La encuesta no tiene precisión suficiente para dar esta cifra en este territorio o grupo.'", 'COM-13'),
 ('R-ENC-11', 'replace', 'condicion', "p >= 0.05 → rotular 'sin diferencia significativa'", "p >= 0.05 → test_cambio.significativo = false (rótulo 'sin cambio estadísticamente claro')", 'COM-13'),
 ('R-CRUCES-09', 'set', 'parametros.mapas', 'paleta apta para daltónicos con trama por categoría y tabla alternativa accesible', 'COM-14'),
 # precisión y orden de cláusulas (EST-02, EST-10, EST-11; contradicciones 1 y 5)
 ('R-ENC-03', 'set', 'condicion', "n_sin_ponderar >= 50 AND (tipo_estimacion IN ('media','total','razon') → cv_ref = ee/|estimacion|; tipo_estimacion = 'proporcion' AND 0.10 <= p <= 0.90 → cv_ref = ee/min(p, 1−p)): cv_ref <= 0.15 → publicar; 0.15 < cv_ref <= 0.30 → publicar_referencial; cv_ref > 0.30 → suprimir. Modificador: si la acción resultante es publicar y gl < 8 → publicar_referencial", 'EST-10'),
 ('R-ENC-04', 'set', 'condicion', "tipo_estimacion = 'proporcion' AND (p < 0.10 OR p > 0.90) AND n_sin_ponderar >= 50: n_efectivo < 30 → suprimir; ancho_abs >= 0.30 → suprimir; ancho_rel(p) > 1.30 AND ancho_abs > 0.05 → suprimir; (ancho_rel(p) > 0.59 AND ancho_abs > 0.05) OR n_efectivo < 50 OR gl < 8 → publicar_referencial; resto → publicar. Además (no en lugar de): numerador == 0 → rotular 'menos de {ic_sup}'; numerador == n → rotular 'más de {ic_inf}'. ancho_rel se calcula sobre p solo si 0 < p < 1", 'EST-02'),
 ('R-REG-03', 'set', 'condicion', "TASAS (denominador = población): numerador < 5 OR poblacion < 1000 → no publicar a ese nivel (suprimir); 5 ≤ numerador < 11 → publicar_referencial(modo=rango): solo IC de Poisson, sin valor puntual, puntaje de precisión 2 (rojo); 11 ≤ numerador < 20 → publicar_referencial (motivo pocos_casos) y excluir de rankings; numerador ≥ 20 AND poblacion ≥ 1000 → publicar. PROPORCIONES (denominador = personas evaluadas/objetivo): n_denominador < 30 → suprimir; 30 ≤ n < 100 OR numerador < 5 OR (n − numerador) < 5 OR (ic_sup − ic_inf) > 0.20 → publicar_referencial; resto → publicar", 'EST-11'),
 ('R-REG-03', 'set', 'implementacion', "resultado.estado_cifra ∈ {publicable, referencial, suprimida}; motivos incluye 'pocos_casos' si numerador < 20; resultado.ic_metodo. IC con scipy.stats.chi2.ppf; para persona-tiempo agrupado usar la suma de poblaciones anuales. Al agrupar años el rótulo es 'promedio {anio_ini}–{anio_fin}'.", 'EST-07, IMP-05'),
 ('R-REG-05', 'set', 'implementacion', "El validador recibe la lista de resultados para un ranking; si alguna unidad tiene 'pocos_casos' en motivos, sustituye por el nivel superior o por tasa_suavizada (cuando R-REG-06 esté implementada) con rótulo 'tasa ajustada por pocos casos'.", 'IMP-05'),
 ('R-ENC-03', 'replace', 'implementacion', '{publicable, referencial, suprimido}', '{publicable, referencial, suprimida}', 'IMP-05'),
 ('R-ENC-03', 'replace', 'implementacion', 'si suprimido,', 'si suprimida,', 'IMP-05'),
 ('R-CRUCES-09', 'set', 'parametros.criterios.precision', 'publicar = 0; publicar_referencial = 1; publicar_referencial(modo=rango) = 2; suprimir = 3', 'EST-11'),
 ('R-MOTOR-02', 'set', 'parametros.normalizacion_salidas.mostrar_solo_el_intervalo', 'publicar_referencial (modo=rango; precisión 2 en el semáforo)', 'EST-11'),
 ('R-MOTOR-02', 'set', 'parametros.normalizacion_salidas.publicar_rango', 'publicar_referencial (modo=rango; precisión 2 en el semáforo)', 'EST-11'),
 ('R-MOTOR-02', 'set', 'parametros.modificadores', 'una cláusula marcada "Modificador" o "Además" se aplica sobre la acción resultante, no compite con las demás', 'EST-02, EST-10'),
 # encuestas, aprendizajes, anemia, series
 ('R-ENC-16', 'set', 'aplica_a', {'naturaleza_dato': [], 'tipo_medida': [], 'base_geografica': [], 'fuentes': ['MINEDU-UMC-ECE', 'MINEDU-UMC-ENLA']}, 'HEC-06'),
 ('R-ENC-16', 'set', 'parametros.ultimo_anio', None, 'HEC-06'),
 ('R-ENC-10', 'set', 'implementacion', 'Apilar las bases de los k años más recientes; factor_k = factor/k; estrato y UPM según parametros.estrato_agrupado (ENAHO: estrato original y conglomerado estable; ENDES: anio × estrato). Re-evaluar R-ENC-02..04 sobre la celda agrupada. Guardar resultado.periodo_agrupado=[anios] y anio_referencia = año central.', 'EST-06'),
 ('R-CRUCES-04', 'set', 'parametros.quiebres_conocidos.anemia (ENDES, SIEN, REUNIS)', 'cambio de criterio según R-ENC-14.disponibilidad_criterio (no es un año fijo)', 'HEC-07'),
 ('R-REG-10', 'set', 'parametros.quiebres_a_registrar.MINSA-REUNIS', 'criterio de anemia según R-ENC-14.disponibilidad_criterio (no es un año fijo)', 'HEC-07'),
 ('R-REG-04', 'replace', 'justificacion', 'SINADEF captaba ~49 % de las defunciones estimadas en 2018', 'los certificados en línea de SINADEF cubrían 49 % de las defunciones estimadas a julio de 2018 (la cobertura con certificación médica fue 71,6 % en 2019)', 'HEC-09'),
 ('R-REG-07', 'replace', 'justificacion', 'SINADEF registraba ~49 % de las defunciones estimadas a mediados de 2018 (Vargas-Herrera et al.)', 'los certificados en línea de SINADEF cubrían 49 % de las defunciones estimadas a julio de 2018 (Vargas-Herrera et al.); la cobertura con certificación médica fue 71,6 % en 2019', 'HEC-09'),
 ('R-ENC-06', 'replace', 'casos_borde', 'Provincia Constitucional del Callao: es departamento en las encuestas.', 'Callao: dominio propio en ENDES; en ENAHO forma parte del dominio Área Metropolitana de Lima y Callao (ver R-ENC-07.dominios_lima).', 'HEC-11'),
 ('R-ENC-06', 'set', 'parametros.jerarquia', 'ver parametros_globales.NIVEL_RANK', 'IMP-17'),
 # denominadores (HEC-02, HEC-04, IMP-06; contradicciones 13, 14)
 ('R-DENOMINADORES-01', 'set', 'parametros.matriz.tasa_poblacion_total (por 1 000 / 100 000 hab., gasto per cápita)', {'principal': 'INEI-PROYECCIONES-POBLACION-DISTRITAL (30-jun del año, mismo vintage en toda la serie)', 'contraste': ['INEI-CPV2025 ajustado por omisión (P_censada / (1 − omision)), solo año 2025'], 'nivel_minimo': 'distrito'}, 'HEC-04'),
 ('R-DENOMINADORES-04', 'set', 'aplica_a', {'naturaleza_dato': [], 'tipo_medida': [], 'base_geografica': [], 'fuentes': []}, 'HEC-04'),
 ('R-DENOMINADORES-04', 'replace', 'condicion', '→ advertir en todas las tasas 2025 del distrito', '→ advertir en toda cifra cuyo denominador sea la población 2025 del distrito', 'HEC-04'),
 ('R-DENOMINADORES-04', 'replace', 'justificacion', 'Los resultados definitivos del CPV2025 (jul-2026) ya están por distrito', 'El INEI publicó la población censada del CPV2025 por distrito el 10-07-2026 (sin rótulo de definitiva ni bases descargables)', 'HEC-02'),
 ('R-GASTO-11', 'replace', 'condicion', 'grupo de edad distrital -> solo si R-DEN lo habilita (MINSA o Censo 2025) y como referencial', 'grupo de edad distrital -> prorrateo propio (R-DENOMINADORES-03), publicar_referencial', 'IMP-06'),
 ('R-GASTO-11', 'replace', 'casos_borde', 'rotular y excluir de rankings (R-GASTO-13)', 'rotular y marcar en rankings (R-GASTO-13)', 'IMP-18'),
 ('R-GASTO-12', 'replace', 'casos_borde', 'Si se decide IPC nacional o deflactor del PBI (pregunta abierta), cambiar solo el parámetro.', 'Para cambiar de deflactor basta cambiar el parámetro.', 'IMP-18'),
 ('R-REG-07', 'replace', 'implementacion', 'población MINSA del grupo de edad (dependencia: ámbito denominadores)', 'denominador principal de R-DENOMINADORES-01 para el grupo de edad', 'IMP-06'),
 ('R-REG-01', 'set', 'parametros.excepcion_prohibicion', "registro_eventos con base residencia puede usar 'tasa registrada' según bandas_cobertura de R-REG-07 (cobertura ≥ 80 %)", 'IMP-09'),
 ('R-REG-04', 'set', 'parametros.min_cobertura_registro_pct', None, 'IMP-09'),
 ('R-TERRITORIO-08', 'replace', 'casos_borde', 'Fuentes que solo traen nombres (PRONIED-INTERVENCIONES): p se calcula tras el emparejamiento por nombre con similitud ≥ 0,90 dentro de la provincia; los empates van a revisión humana. ', '', 'IMP-09'),
 # vocabulario (IMP-07, contradicción 6)
 ('R-REG-02', 'replace', 'condicion', "IN ('tasa','cobertura','proporcion')", "IN ('tasa','proporcion')", 'IMP-07'),
 ('R-REG-15', 'set', 'condicion', "indicador.requiere_estandarizacion = true AND salida.tipo IN (ranking, mapa, comparacion, asociacion) → usar tasa_ajustada_edad; si no hay denominador por edad aprobado a ese nivel → bloquear_cruce", 'EST-04'),
 # año de la cifra (EST-07, contradicción 18)
 ('R-LENGUAJE-04', 'replace', 'condicion', 'anio_actual - anio_dato > 2', 'edad_dato > 2', 'EST-07'),
 ('R-LENGUAJE-04', 'replace', 'condicion', 'con anio_dato < a', 'con anio_referencia < a', 'EST-07'),
]
CAMPOS_V2 = [
 ('estado_cifra', 'cifra', 'estado_precision, estado_estabilidad', "publicable | referencial | suprimida | agregada | agrupada | sin_datos, con motivos[] (p. ej., pocos_casos, metadato_faltante)."),
 ('tipo_estimacion', 'indicador', '—', 'proporcion | total | media | razon | tasa | modelada | propia (sin tildes; las coberturas son proporciones).'),
 ('anio_referencia / edad_dato', 'cifra', 'anio_dato, año del dato', 'anio_referencia = punto medio del periodo de referencia si existe; si no, año central del periodo agrupado; si no, año del dato. edad_dato = anio_actual − anio_referencia. Lo usan R-CRUCES-03, R-CRUCES-09, R-LENGUAJE-02, R-LENGUAJE-04 y R-EST-05.'),
 ('sensibilidad_divulgacion', 'catálogo, indicador y cifra', '—', "ninguna | normal | sensible; obligatorio en el catálogo (NULL = normal). Define el umbral de R-REG-12."),
 ('requiere_estandarizacion', 'indicador', '—', 'true para tasas de mortalidad o morbilidad de todas las edades (R-REG-15).'),
]

# ---------------------------------------------------------------- tercera ronda (re-verificación: auditoria/verificacion_v11_ronda2.json)
SENSIBLES_POR_TEMA = ['MIMP-WARMINAN-BANCO-DATOS', 'MININTER-VIOLENCIA-MUJER-PNP', 'MINEDU-SISEVE', 'CDC-SALA-MUERTE-MATERNA', 'CONADIS-RNPCD']
PARCHES_V3 = [
 # R-REG-12 se había sobrecorregido: aplicaba a encuestas, gasto y estimaciones, y dejaba a SIEN sin distritos
 ('R-REG-12', 'set', 'aplica_a', {'naturaleza_dato': ['registro_administrativo', 'censo', 'indicadores_derivados'], 'tipo_medida': [], 'base_geografica': [], 'fuentes': []}, 'COM-01'),
 ('R-REG-12', 'replace', 'condicion', "Aplica si sensibilidad_divulgacion(fuente, celda) != 'ninguna' (campo obligatorio del catálogo; NULL se trata como 'normal'; fuente ∈ fuentes_sensibles o celda con código ∈ temas_sensibles → 'sensible'). ",
  "Aplica a registros, censos e indicadores derivados que cuentan personas (las encuestas se protegen con el n mínimo de R-ENC-02; gasto y estimaciones modeladas tienen sensibilidad 'ninguna'). sensibilidad de la celda: 'sensible' si la fuente ∈ fuentes_sensibles_por_tema o la celda tiene tema o código ∈ temas_sensibles; si no, 'normal' (NULL en el catálogo = 'normal'); fuentes que no cuentan personas (locales, establecimientos) = 'ninguna'. ", 'COM-01'),
 ('R-REG-12', 'set', 'parametros.fuentes_sensibles_ola1', None, 'COM-01'),
 ('R-REG-12', 'set', 'parametros.fuentes_sensibles_por_tema', SENSIBLES_POR_TEMA, 'COM-01'),
 ('R-REG-12', 'set', 'parametros.fuentes_con_personas_celda_a_celda', ['MINSA-REUNIS', 'CDC-VIGILANCIA-DATOS-ABIERTOS', 'ESSALUD-DATOS-ABIERTOS', 'SIS-ATENCIONES', 'INS-CENAN-SIEN', 'MINEDU-CENSO-EDUCATIVO (matrícula)', 'CONTIGO-USUARIOS'], 'COM-01'),
 ('R-REG-12', 'replace', 'implementacion', '(normal|sensible)', '(ninguna|normal|sensible)', 'IMP-05'),
 ('R-REG-12', 'set', 'mensaje_usuario', 'Para que nadie pueda ser identificado, no mostramos cifras de menos de {umbral} personas. Mostramos {alternativa}.', 'COM-13'),
 ('R-MOTOR-01', 'set', 'parametros.secuencia_degradacion.fuente_sensible', ['anio', 'provincia_anio', 'departamento_anio', 'departamento_ventana_fija_5_anios', 'suprimir'], 'COM-03'),
 ('R-MOTOR-01', 'set', 'parametros.prioridad_secuencia', "celda con sensibilidad 'sensible' de registros o indicadores derivados → secuencia fuente_sensible (sin GEO2017; solo ventanas fijas no superpuestas, p. ej. 2020–2024); encuestas siguen su propia secuencia (R-ENC-06); el resto, la de su naturaleza_dato", 'COM-03'),
 # referencias (HEC-12): se restituyen las originales y se agregan las nuevas
 ('R-ENC-13', 'append', 'referencias', {'titulo': 'INEI – Declaración de la Comisión Consultiva para la estimación de la pobreza monetaria 2021 (misma metodología 2004-2020; las variaciones 2021/2020/2019 son cambios en las condiciones de vida)', 'url': 'https://www.inei.gob.pe/media/cifras_de_pobreza/declaracion_estimacion_pobreza_monetaria_2021.pdf'}, 'HEC-12'),
 ('R-CRUCES-03', 'append', 'referencias', {'titulo': 'INEI – Declaración de la Comisión Consultiva para la estimación de la pobreza monetaria 2020', 'url': 'https://www.inei.gob.pe/media/MenuRecursivo/publicaciones_digitales/Est/pobreza2020/Declaracion_Estimacion_Pobreza_Monetaria_2020.pdf'}, 'HEC-12'),
 # año de la cifra (EST-07)
 ('R-CRUCES-09', 'set', 'parametros.criterios.vigencia', 'edad_dato = anio_actual − anio_referencia (ver diccionario), solo para la cifra más reciente de cada indicador: <=2 → 0; 3–5 → 1; >5 → 2. Los puntos de una serie heredan el semáforo de la comparación', 'EST-07'),
 # mensajes (COM-13)
 ('R-GASTO-05', 'set', 'mensaje_usuario', 'Las transferencias (como el canon o el FONCOMUN) son dinero que la municipalidad recibe de otras entidades. No las sumamos, porque lo que gasta con ese dinero ya está en su gasto.', 'COM-13'),
 ('R-CRUCES-06', 'replace', 'mensaje_usuario', 'Con otra división territorial el resultado podría cambiar.', 'Si se comparara por provincias en vez de departamentos, el resultado podría ser otro.', 'COM-13'),
 ('R-DENOMINADORES-03', 'set', 'mensaje_usuario', 'No hay cifra oficial de cuántas personas de esta edad viven en el distrito; la calculamos con el censo {anio_censo}. Puede no coincidir si el distrito cambió mucho.', 'COM-13'),
 # población censada (HEC-01)
 ('R-LENGUAJE-02', 'set', 'parametros.poblacion_censada', "cifras de INEI-CPV2025 por provincia o distrito van siempre con {{u:personas_censadas}}; la palabra 'población' sola solo para la población total con omisión o la proyección", 'HEC-01'),
 # puerta de calidad del corrector (COM-07)
 ('R-LENGUAJE-02', 'set', 'parametros.puerta_ci', 'el consolidador falla si el corrector tiene algún falso positivo o no detectada en los corpus de prueba (tolerancia 0; más estricta que el 5 % propuesto); meta MVP: corpus ≥ 200 oraciones con 40 % de reserva', 'COM-07'),
]

# ---------------------------------------------------------------- cuarta ronda (verificación v_parches_v3: auditoria/verificacion_v11_ronda3.json; v2 tras la auditoría aud_correcciones)
# Operaciones: 'set' (con assert), 'replace', 'append' y 'borrar' (quita una clave; la ruta debe existir).
# SIN_PERSONAS: dentro del alcance de R-REG-12, qué variables de cada fuente no cuentan personas ni hogares ('ninguna'). Las
# variables que sí cuentan personas o hogares siguen 'normal' (criterio M2: matrícula, docentes, usuarios, hogares,
# beneficiarios, población, autoridades).
SIN_PERSONAS = [
 {'fuente': 'MINEDU-CENSO-EDUCATIVO', 'ninguna': 'locales, aulas, secciones, servicios básicos, conectividad e infraestructura', 'normal': 'matrícula, docentes y resultados del ejercicio (aprobados, desaprobados, retirados)'},
 {'fuente': 'MINEDU-ESCALE-PADRON', 'ninguna': 'datos del servicio educativo (códigos, nivel, gestión, área, ubicación, coordenadas)', 'normal': 'matrícula y docentes del último censo'},
 {'fuente': 'SUSALUD-RENIPRESS', 'ninguna': 'todas (establecimientos: categoría, institución, ubicación, estado)', 'normal': '—'},
 {'fuente': 'MEF-DETALLE-INVERSIONES', 'ninguna': 'montos, estado, avance y atributos de la obra', 'normal': 'NUM_HABITANTES_BENEF (beneficiarios); los nombres de personas siguen en nunca_publicar'},
 {'fuente': 'MEF-MAESTRO-EJECUTORAS-DERIVADO', 'ninguna': 'todas (entidades)', 'normal': '—'},
 {'fuente': 'MEF-PPR-PROGRAMAS-PRESUPUESTALES', 'ninguna': 'estructura programática (programas, productos, actividades) y textos de diseño', 'normal': 'metas físicas o indicadores que cuenten personas'},
 {'fuente': 'PRONIED-INTERVENCIONES', 'ninguna': 'intervenciones y locales escolares (montos, estado, ubicación)', 'normal': 'estudiantes beneficiarios, si los trae'},
 {'fuente': 'FONCODES-PROYECTOS', 'ninguna': 'monto, estado y ubicación del proyecto', 'normal': 'hogares usuarios'},
 {'fuente': 'WASIMIKUNA-IIEE', 'ninguna': 'listado de instituciones educativas atendidas (código, nivel, modalidad, ubicación)', 'normal': 'número de usuarios'},
 {'fuente': 'INEI-PNDA-UBIGEOS', 'ninguna': 'todas (códigos)', 'normal': '—'},
 {'fuente': 'GITHUB-UBIGEO-PERU-AUMENTADO', 'ninguna': 'códigos, equivalencias INEI-RENIEC, coordenadas, superficie y altitud', 'normal': 'población, densidad e indicadores derivados (se citan las fuentes originales)'},
 {'fuente': 'INEI-DIRECTORIO-MUNICIPALIDADES', 'ninguna': 'datos de la municipalidad y dispositivo legal de creación', 'normal': 'autoridades (nombres: nunca_publicar)'},
]
PARCHES_V4 = [
 # R-REG-12: una sola lista de fuentes sensibles, mecanismo para 'ninguna', término "celdas sensibles" (C-V3-3, N2, M2)
 ('R-REG-12', 'borrar', 'parametros.fuentes_sensibles_ola1', 'C-V3-3'),
 ('R-REG-12', 'borrar', 'parametros.temas_sensibles.fuentes_completas', 'C-V3-3'),
 ('R-REG-12', 'borrar', 'parametros.fuentes_con_personas_celda_a_celda', 'C-V3-3'),
 ('R-REG-12', 'set', 'parametros.sin_personas', SIN_PERSONAS, 'N2, C-V3-3'),
 ('R-REG-12', 'replace', 'condicion',
  "si no, 'normal' (NULL en el catálogo = 'normal'); fuentes que no cuentan personas (locales, establecimientos) = 'ninguna'. ",
  "si no, 'ninguna' si sensibilidad_divulgacion(fuente) = 'ninguna' en el catálogo o la variable está en sin_personas[fuente].ninguna (no cuenta personas ni hogares: locales, establecimientos, proyectos, entidades); si no, 'normal' (NULL en el catálogo = 'normal'; las variables de sin_personas[fuente].normal también). Con 'ninguna' esta regla no se aplica. ", 'N2, C-V3-3'),
 ('R-REG-12', 'replace', 'condicion', "(7) fuentes sensibles → solo cubo protegido (parametros.cubo_protegido)",
  "(7) celda sensible → solo desde el cubo protegido (parametros.cubo_protegido)", 'C-V3-3'),
 ('R-REG-12', 'replace', 'enunciado', 'las fuentes sensibles se sirven solo desde un cubo protegido', 'las celdas sensibles se sirven solo desde un cubo protegido', 'C-V3-3'),
 ('R-REG-12', 'replace', 'casos_borde', 'sirviendo las fuentes sensibles solo desde el cubo protegido', 'sirviendo las celdas sensibles solo desde el cubo protegido', 'C-V3-3'),
 ('R-REG-12', 'set', 'parametros.prueba_restas', 'antes de publicar una celda sensible, comprobar que no se obtiene por diferencia con otras celdas publicadas del mismo cubo (niveles superior/inferior, desagregaciones, años)', 'C-V3-3'),
 ('R-REG-12', 'set', 'parametros.cubo_protegido.mvp', 'celdas sensibles solo en geografía vigente, años cerrados sueltos; sin GEO2017, sin ventanas de 3 años ni acumulados mensuales', 'C-V3-3'),
 # R-REG-12 → R-MOTOR-01: la supresión por nivel mínimo (cláusula 3) sí busca la provincia (C-V3-2, B1)
 ('R-REG-12', 'replace', 'condicion', "(3) sensibilidad = 'sensible' → nivel mínimo provincia, salvo distrito con población ≥ 20 000 y celda ≥ 10;",
  "(3) sensibilidad = 'sensible' → nivel mínimo provincia, salvo distrito con población ≥ 20 000 y celda ≥ 10: la celda distrital se suprime con motivo divulgacion_nivel y la regla emite solicitar_degradacion(divulgacion_nivel, nivel_minimo = provincia), que R-MOTOR-01 resuelve con la secuencia fuente_sensible;", 'C-V3-2'),
 ('R-REG-12', 'set', 'parametros.alternativa', "valor de {alternativa} en el mensaje: (1)-(2) 'menos de {umbral}' (numerador_redondeado); (3) la provincia o el periodo que devuelva R-MOTOR-01; (4)-(6) el total sin desagregar; si no queda ninguna, R-LENGUAJE-05 (sin_datos)", 'C-V3-2'),
 ('R-MOTOR-01', 'set', 'parametros.motivos_degradables', ['precision', 'pocos_casos', 'nivel_no_representativo', 'base_establecimiento', 'cobertura_mayor_110', 'divulgacion_nivel'], 'C-V3-2'),
 ('R-MOTOR-01', 'set', 'parametros.nota_divulgacion', "'divulgacion' (supresión primaria y complementaria de R-REG-12, cláusulas 1, 2, 4-6) no se degrada; 'divulgacion_nivel' (cláusula 3, nivel mínimo provincia) sí", 'C-V3-2'),
 ('R-MOTOR-01', 'set', 'parametros.prioridad_secuencia', "celda con sensibilidad 'sensible' de registros, censos o indicadores derivados → secuencia fuente_sensible (sin GEO2017; la agrupación de años depende de la decisión D-R4-1, pendiente); encuestas siguen su propia secuencia (R-ENC-06); el resto, la de su naturaleza_dato", 'C-V3-2, B1'),
 ('R-MOTOR-01', 'replace', 'condicion', 'AND paso < len(secuencia[naturaleza_dato])', 'AND paso < len(secuencia[s]) con s elegida por parametros.prioridad_secuencia', 'C-V3-2'),
 ('R-MOTOR-01', 'replace', 'condicion', 'las reglas de las etapas 2–4 no cambian el nivel', 'las reglas de las etapas 2–4, y R-REG-12 (etapa 6) con el motivo divulgacion_nivel, no cambian el nivel', 'C-V3-2'),
 ('R-MOTOR-01', 'replace', 'implementacion', 'Bucle sobre las etapas 2–4.', 'Bucle sobre las etapas 2–6 (la 6 solo puede pedir degradación con divulgacion_nivel); tras cada paso se vuelven a evaluar las etapas 2–6.', 'C-V3-2'),
 ('R-MOTOR-01', 'replace', 'enunciado', 'Cuando una cifra no supera las etapas 2 a 4,', 'Cuando una cifra no supera las etapas 2 a 4, o R-REG-12 (etapa 6) le exige un nivel mínimo por privacidad,', 'B1'),
 # R-GASTO-01: el nivel nacional_multidepartamental existe en el vocabulario de niveles publicables (B2)
 ('R-GASTO-01', 'set', 'parametros.nivel_maximo_publicable.nacional_multidepartamental', 'nacional', 'B2'),
 # R-CRUCES-06: mensaje válido para cualquier nivel y enunciado con el mínimo vigente (C-V3-4)
 ('R-CRUCES-06', 'replace', 'mensaje_usuario', 'Si se comparara por provincias en vez de departamentos, el resultado podría ser otro.', 'Si se comparara con territorios más grandes o más pequeños, el resultado podría ser otro.', 'C-V3-4'),
 ('R-CRUCES-06', 'replace', 'enunciado', 'con al menos 10 territorios válidos', 'con al menos 20 territorios válidos', 'C-V3-4'),
 ('R-CRUCES-06', 'replace', 'enunciado', 'Con menos de 10 territorios', 'Con menos de 20 territorios', 'C-V3-4'),
 # población censada (HEC-01, C-V3-5): regla estructural ejecutable (reglas/consolidador/corrector_estructural.py) y universo en el diccionario
 ('R-LENGUAJE-02', 'replace', 'condicion', "gasto por CUI → 'obras ubicadas en'",
  "gasto por CUI → 'obras ubicadas en'; cada {{c:id}} de INEI-CPV2025 por provincia o distrito va en una oración con {{u:personas_censadas}} (parametros.poblacion_censada), si no → regenerar", 'HEC-01, C-V3-5'),
 ('R-LENGUAJE-02', 'set', 'parametros.poblacion_censada_verificacion', {'funcion': 'reglas/consolidador/corrector_estructural.py: personas_censadas(texto, cifras)', 'patron_cifra': r'\{\{c:([^}]+)\}\}', 'marcador_exigido': '{{u:personas_censadas}}', 'casos': 'reglas/consolidador/pruebas/casos_personas_censadas.json (los corre consolida_reglas.py; un fallo es una prueba de consistencia fallida)'}, 'HEC-01, C-V3-5'),
 # corrector (COM-07): la referencia apunta a los corpus que de verdad lee el consolidador
 ('R-LENGUAJE-02', 'set', 'parametros.prueba_corrector', {'corpus': 'reglas/consolidador/pruebas/corpus_reserva.json + reglas/consolidador/pruebas/corpus_auditor.json (los que lee consolida_reglas.py)', 'resultado': 'se recalcula en cada consolidación; el consolidador falla con cualquier falso positivo o no detectada (parametros.puerta_ci)', 'meta_mvp': 'corpus ≥ 200 oraciones con 40 % de reserva'}, 'COM-07'),
]
CAMPOS_V4 = [
 ('poblacion_objetivo', 'indicador', 'poblacion_objetivo, poblacion_objetivo_dominio, universo', 'Grupo al que se refiere la cifra y universo (p. ej., niños 6–35 meses; solo atendidos). Valores del marcador {{u:id}}: tamizados, atendidos, notificados, usuarios y personas_censadas (cifras del INEI-CPV2025 sin ajuste por omisión; R-LENGUAJE-02).'),
]

# ---------------------------------------------------------------- Decisión del dueño D-R4-1: años de las celdas sensibles de mortalidad
# Alcance: celdas sensibles de registros (temas_sensibles: muerte materna O95-O99 y «defunción fetal o infantil») → RMM, TMI y
# TMN de R-REG-04, más cualquier otra celda sensible.
# Decisión del dueño (7/10/2026): opción C, periodos fijos de 3 años («por ahora 3 años, luego podemos ampliarlo»).
# Valores válidos: 'A', 'B' o 'C'. None = sin decidir: se aplica PENDIENTE_D_R4_1 (sin ventanas multianuales de RMM, TMI ni
# TMN por debajo del nivel nacional) y reglas.json lo expone en `decisiones_pendientes` (auditoría final r4, F1). Cualquier
# otro valor detiene la consolidación (F6).
# Ventanas (F3): el SINADEF empieza en 2017 (catálogo: cobertura_temporal 2017–2026), así que toda ventana empieza en 2017,
# no se superpone con otra y no parte años. C: 2017–2019, 2020–2022 y 2023–2025. Ampliación a 5 años = opción B:
# 2017–2021 y 2022–2026 (la segunda solo cuando 2026 esté cerrado); al cambiar, se retiran las ventanas de 3 años (no se
# publican ventanas de 3 y de 5 años a la vez: 2017–2021 menos 2017–2019 revelaría 2020–2021). Explicación:
# auditoria/ronda4/explicacion_D-R4-1.md.
D_R4_1 = 'C'
_PRIO = ("celda con sensibilidad 'sensible' de registros, censos o indicadores derivados (entre ellas RMM, TMI y TMN, que "
         "siempre son sensibles) → secuencia fuente_sensible (sin GEO2017; {años}); la secuencia registro_eventos_mortalidad "
         "no se usa para celdas sensibles; encuestas siguen su propia secuencia (R-ENC-06); el resto, la de su naturaleza_dato")
_RESTAS = ("antes de publicar una celda sensible, comprobar que no se obtiene por diferencia con otras celdas publicadas del "
           "mismo cubo: (a) niveles superior/inferior, desagregaciones y años{b}; (c) entre territorios: si un "
           "departamento-año se suprime{c}, se suprime también el departamento-año con menos casos del mismo año "
           "(supresión complementaria), para que el nacional anual menos los demás departamentos no lo revele")
_REG04_BASE = ("Las tasas de mortalidad infantil, neonatal o materna calculadas con SINADEF/CNV deben usar residencia en ambos "
               "registros, rotularse 'registrada', y solo publicarse si hay al menos 1 000 nacidos vivos y 20 defunciones en "
               "el periodo; nunca a nivel distrital. ")
_REG04_IMPL = ("Numerador: SINADEF por ubigeo de residencia, edad < 1 año (o < 28 días), año de defunción; RMM: muertes "
               "maternas por 100 000 nacidos vivos. Denominador: CNV por residencia de la madre, mismo periodo. IC Poisson "
               "exacto sobre defunciones / NV. Marcar si numerador y denominador provienen de coberturas distintas. ")
_REG04_COND = ("indicador IN (TMI, TMN, RMM) AND (nacidos_vivos_periodo < 1000 OR defunciones_periodo < 5) → agregar_nivel "
               "(secuencia fuente_sensible de R-MOTOR-01); 5 ≤ defunciones_periodo < 20 → publicar_referencial; "
               "nivel = 'distrito' → suprimir; periodo ∈ {periodos} (parámetro periodos_permitidos). Cobertura: R-REG-07 "
               "con la cobertura infantil (fuente_cobertura_SINADEF_infantil)")


def _comun(secuencia, prio_anios, cubo, restas_b, restas_c, t04, enunciado_sens, impl_sens, rmm, nivel_agr, max_agr,
           periodos, ejemplo):
    """Campos que toda opción (y el estado pendiente) deja coherentes en R-MOTOR-01, R-REG-04, R-REG-12 y R-TERRITORIO-04
    (F1 y F4: R-REG-04 ya no dice «agrupando hasta 5 años» ni tiene una rama de celdas no sensibles sin casos)."""
    return [
     ('R-MOTOR-01', 'set', 'parametros.secuencia_degradacion.fuente_sensible', secuencia, 'D-R4-1'),
     ('R-MOTOR-01', 'set', 'parametros.prioridad_secuencia', _PRIO.format(años=prio_anios), 'D-R4-1'),
     ('R-REG-12', 'set', 'parametros.cubo_protegido.mvp', cubo, 'D-R4-1'),
     ('R-REG-12', 'set', 'parametros.prueba_restas', _RESTAS.format(b=restas_b, c=restas_c), 'D-R4-1'),
     ('R-TERRITORIO-04', 'set', 'parametros.fuentes_sensibles', t04, 'D-R4-1'),
     ('R-REG-04', 'set', 'enunciado', _REG04_BASE + enunciado_sens, 'D-R4-1'),
     ('R-REG-04', 'set', 'condicion', _REG04_COND.format(periodos=', '.join(periodos)), 'D-R4-1'),
     ('R-REG-04', 'set', 'implementacion', _REG04_IMPL + impl_sens, 'D-R4-1'),
     ('R-REG-04', 'set', 'parametros.rmm_nivel_minimo', rmm, 'D-R4-1'),
     ('R-REG-04', 'set', 'parametros.nivel_minimo_agrupado', nivel_agr, 'D-R4-1'),
     ('R-REG-04', 'set', 'parametros.max_anios_agrupados', max_agr, 'D-R4-1'),
     ('R-REG-04', 'set', 'parametros.periodos_permitidos', periodos, 'D-R4-1'),
     ('R-REG-04', 'set', 'ejemplo', ejemplo, 'D-R4-1'),
    ]


_EJ = ("[Cifras ilustrativas, no verificadas] Provincia de Purús: ~150 NV/año → no llega a 1 000 NV ni sumando años → {d} "
       "con rótulo 'registrada' y, al lado, la TMI ENDES departamental como referencia oficial.")


def _opcion_sin_ventana(cuando):  # A y estado pendiente: ninguna ventana multianual de RMM, TMI ni TMN bajo el nivel nacional
    return _comun(
        ['anio', 'provincia_anio', 'departamento_anio', 'suprimir'],
        f'{cuando} sin agrupar años: celdas sensibles solo por año suelto',
        f'celdas sensibles solo en geografía vigente, años cerrados sueltos ({cuando}); sin ventanas de varios años, sin '
        'GEO2017, sin acumulados mensuales',
        '', ' o no alcanza',
        f'geografía vigente del último año; series solo con años sueltos ({cuando}; R-REG-12 cubo protegido)',
        f'Celdas sensibles (RMM, TMI, TMN; R-REG-12): {cuando}, solo años sueltos (provincia-año o departamento-año; si '
        'no alcanza, solo la cifra nacional); no se suman años.',
        f'Celdas sensibles (RMM, TMI, TMN): secuencia fuente_sensible de R-MOTOR-01 sin ventanas ({cuando}): año, '
        'provincia-año, departamento-año; si no cumple, solo la cifra nacional.',
        f'departamento-año o nacional ({cuando}; sin sumar años)',
        f'celdas sensibles (RMM, TMI, TMN): no se agrupan años ({cuando})',
        f'1 (celdas sensibles, {cuando})',
        ['año suelto'],
        _EJ.format(d=f'{cuando} se publica Ucayali por año, si alcanza, o solo la cifra nacional'))


def _opcion_ventana(n, ventanas, choque, nota=''):  # B y C: ventanas fijas no superpuestas de n años, solo a nivel departamento
    paso = f'departamento_ventana_fija_{n}_anios'
    v = ', '.join(ventanas)
    return _comun(
        ['anio', 'provincia_anio', 'departamento_anio', paso, 'suprimir'],
        f'años sueltos o ventanas fijas no superpuestas de {n} años: {v}{nota}',
        f'celdas sensibles solo en geografía vigente; años cerrados sueltos o ventanas fijas no superpuestas de {n} años '
        f'({v}) a nivel departamento; dentro de una ventana publicada no se publican años sueltos del mismo tema y '
        'departamento; sin GEO2017, sin ventanas móviles, sin acumulados mensuales',
        '; (b) ventana menos los años sueltos publicados', ' o solo sale en ventana',
        f'geografía vigente del último año; series con años sueltos o ventanas fijas no superpuestas de {n} años ({v}) a '
        'nivel departamento (R-REG-12 cubo protegido)',
        f'Celdas sensibles (RMM, TMI, TMN; R-REG-12): solo años sueltos o ventanas fijas de {n} años ({v}) a nivel '
        'departamento.',
        f'Celdas sensibles (RMM, TMI, TMN): secuencia fuente_sensible de R-MOTOR-01 (año, provincia-año, departamento-año, '
        f'ventana fija de {n} años por departamento: {v}); si no cumple, solo la cifra nacional. No hay ventanas móviles '
        f'ni de otra longitud.{nota}',
        f'departamento con ventana fija de {n} años ({v}); si no alcanza, nacional',
        f'departamento con ventana fija de {n} años (celdas sensibles: RMM, TMI, TMN)',
        f'{n}, en ventana fija (celdas sensibles)',
        ['año suelto'] + ventanas,
        _EJ.format(d=f'se publica solo el departamento de Ucayali en la ventana {ventanas[-1]}')) + [
     ('R-REG-12', 'replace', 'condicion', '(1) 1 ≤ numerador < umbral(sensibilidad) → suprimir el valor',
      f'(1) RMM, TMI o TMN sensibles a nivel departamento-año con 1 ≤ numerador < umbral → no se muestra «menos de»: se '
      f'suprime con motivo divulgacion_nivel y se pide la ventana fija de {n} años (R-MOTOR-01); en otro caso, '
      '1 ≤ numerador < umbral(sensibilidad) → suprimir el valor', 'D-R4-1'),
     ('R-MOTOR-01', 'set', 'parametros.nota_divulgacion', f"'divulgacion' (supresión primaria y complementaria de R-REG-12, "
      f"cláusulas 1, 2, 4-6) no se degrada; 'divulgacion_nivel' (cláusula 3, y cláusula 1 para RMM, TMI y TMN "
      f"departamento-año → ventana de {n} años) sí", 'D-R4-1'),
     ('R-REG-04', 'set', 'parametros.ventana_con_choque', f'una ventana que incluye {choque} lleva el aviso de años de '
      'choque (anios_choque; R-LENGUAJE-04) y no se compara con otra ventana sin ese aviso', 'D-R4-1'),
     ('R-REG-04', 'set', 'parametros.ventanas_fijas', ventanas, 'D-R4-1'),
    ]


OPCIONES_D_R4_1 = {
 'A': _opcion_sin_ventana('en el MVP'),
 'B': _opcion_ventana(5, ['2017–2021', '2022–2026'], '2020 o 2021',
                      '; 2022–2026 solo cuando 2026 esté cerrado; no se publica a la vez que las ventanas de 3 años'),
 'C': _opcion_ventana(3, ['2017–2019', '2020–2022', '2023–2025'], '2020 o 2021',
                      '; 2017–2019 tiene el registro incompleto y no se usa para tendencia (R-REG-10)'),
}
# Estado seguro si D_R4_1 vuelve a quedar sin decidir (F1): igual que A, rotulado como pendiente
PENDIENTE_D_R4_1 = _opcion_sin_ventana('D-R4-1 pendiente')
D_R4_1_REGLAS = ['R-MOTOR-01', 'R-REG-04', 'R-REG-12', 'R-TERRITORIO-04']
D_R4_1_TEXTO = {
 'A': 'Opción A aplicada: celdas sensibles de RMM, TMI y TMN solo por año suelto en el MVP.',
 'B': 'Opción B aplicada: ventanas fijas de 5 años (2017–2021 y 2022–2026, esta solo con 2026 cerrado).',
 'C': ('Opción C aplicada (decisión del dueño, 7/10/2026): ventanas fijas de 3 años 2017–2019, 2020–2022 y 2023–2025 a '
       'nivel departamento. Ampliable a 5 años (opción B: 2017–2021 y 2022–2026), retirando las de 3 años.'),
}
