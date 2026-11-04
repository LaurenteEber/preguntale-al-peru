"""Correcciones a las reglas derivadas de la prueba con 12 preguntas reales (prueba/resultado_prueba.json, hallazgos PR-01..PR-38).
Validadas por el orquestador. Se aplican en consolida_reglas.py sobre las propuestas originales (que no se tocan)."""

def regla(id, ambito, titulo, enunciado, condicion, accion, parametros, mensaje, justificacion, implementacion, casos_borde,
          hallazgos, aplica_a=None, prioridad='mvp', ejemplo=''):
    return dict(id=id, ambito=ambito, titulo=titulo, enunciado=enunciado,
                aplica_a=aplica_a or {'naturaleza_dato': [], 'tipo_medida': [], 'base_geografica': [], 'fuentes': []},
                condicion=condicion, accion=accion, parametros=parametros, mensaje_usuario=mensaje, justificacion=justificacion,
                referencias=[], hallazgos_auditoria=[], hallazgos_prueba=hallazgos, ejemplo=ejemplo, implementacion=implementacion,
                casos_borde=casos_borde, prioridad=prioridad)

NUEVAS = [
 regla('R-DEP-01', 'motor', 'Insumos completos antes de calcular',
  'Cada indicador declara todos sus insumos (numerador, denominador y tablas curadas). Si alguno no aprobó la prueba de humo, la cifra no se calcula.',
  "ANY(insumo.compuerta_ingesta != 'aprobada' FOR insumo IN indicador.insumos) → estado_cifra = 'sin_datos', motivo = 'insumo_en_ingesta'",
  'suprimir', {'insumos_bloqueantes_mvp': ['INEI-PROYECCIONES-POBLACION-DISTRITAL', 'INEI-CPV2017', 'INEI-DIRECTORIO-MUNICIPALIDADES',
   'MINSA-POBLACION-ESTIMADA', 'INEI-CPV2025', 'MEF-PPR-PROGRAMAS-PRESUPUESTALES']},
  'Este dato todavía no está disponible en Pregúntale al Perú: una de las fuentes necesarias para calcularlo está en proceso de incorporación.',
  'Una tasa sin denominador validado no es publicable. Extiende a todos los insumos la decisión ya tomada de no ingerir sin prueba de humo.',
  'indicador.insumos: lista de IDs del catálogo y de tablas curadas. El validador consulta compuerta_ingesta de cada uno antes de la etapa 1.',
  'Si solo falta un insumo de contraste (no el principal), la cifra se calcula y se omite el contraste con nota en la ficha larga.',
  ['PR-01']),
 regla('R-MOTOR-01', 'motor', 'Secuencia única de degradación',
  'Cuando una cifra no supera las etapas 2 a 4, el motor la degrada siguiendo una sola secuencia por naturaleza del dato, y registra cada paso.',
  "estado_cifra IN ('suprimida') AND paso < max_pasos → aplicar siguiente paso de secuencia_degradacion[naturaleza_dato] y repetir etapas 2–4",
  'agregar_nivel', {'secuencia_degradacion': {
    'encuesta_muestral': ['anio', 'agrupar_3_anios', 'nivel_superior', 'nivel_superior_agrupado', 'suprimir'],
    'registro_administrativo': ['anio', 'agrupar_3_anios', 'nivel_superior', 'suprimir'],
    'estimacion_modelada': ['anio', 'suprimir'], 'gasto': ['nivel_atribuible', 'respuesta_parcial']}, 'max_pasos': 5},
  None, 'Las reglas de encuestas y registros proponían órdenes de degradación distintos; la prueba mostró que suprimir en la etapa 4 obliga a volver a la etapa 2.',
  'Bucle sobre las etapas 2–4. Cada paso se guarda en motivo_nivel (lista ordenada). El semáforo de cifra (etapa 7) se calcula sobre el resultado final.',
  'Si la secuencia termina en suprimir, la respuesta usa R-LENGUAJE-05 con la mejor alternativa encontrada en el camino (p. ej., la cifra departamental).',
  ['PR-04']),
 regla('R-TERRITORIO-09', 'territorio', 'Resolver el territorio pedido',
  'Antes de calcular, el texto del usuario se convierte en un ubigeo único. Si hay cero o varias coincidencias, o la pregunta no nombra un territorio, se pregunta al usuario.',
  "n_coincidencias(texto, dim_ubigeo_historico.nombre ∪ nombres_alternos, jerarquía) != 1 → preguntar; estado_ubigeo == 'pendiente' → responder con R-LENGUAJE-05 (distrito nuevo)",
  'revision_humana', {'motivos': ['territorio_no_identificado', 'territorio_ambiguo'], 'ambiguos_conocidos': {
    'Lima': ['departamento 15', 'provincia 1501', 'Lima Metropolitana (dominio, según encuesta)', 'Lima Provincias (región)'],
    'Callao': ['provincia constitucional 0701', 'distrito 070101']}},
  '¿A qué {territorio} te refieres? Encontramos varios: {opciones}.',
  'Sin una llave territorial única todas las reglas siguientes son indeterminadas (homónimos como Ayaviri en Puno y en Lima).',
  'Coincidencia exacta normalizada (sin tildes, mayúsculas) sobre nombre y nombres_alternos; si el usuario da provincia o departamento, filtrar por jerarquía. El intérprete (LLM) propone; el motor confirma.',
  'Preguntas sin territorio nombrado ("un distrito de 800 habitantes"): pedir el nombre; no elegir uno. Si el usuario no responde, ofrecer la cifra nacional o departamental rotulada.',
  ['PR-20']),
 regla('R-EST-05', 'estimaciones', 'Única fuente distrital modelada y antigua',
  'Si la pregunta es distrital y la única fuente a ese nivel es una estimación modelada con más de 5 años, esa estimación es la cifra principal con semáforo rojo fijo; la encuesta reciente del departamento va como contexto.',
  "nivel_pedido == 'distrito' AND fuentes_disponibles(nivel='distrito') == [estimacion_modelada] AND edad_dato > 5 → es_principal = true, semaforo_cifra = 'rojo'",
  'publicar_referencial', {'ranking': 'solo grupo_robusto (lista del grupo extremo, sin orden interno)', 'contexto_obligatorio': 'cifra departamental ENAHO del último año'},
  'Es la única estimación oficial por distrito y corresponde a {anio}, antes de la pandemia; la situación actual probablemente es distinta.',
  'Resuelve la contradicción entre R-CRUCES-08 (solo contexto) y R-EST-01 (referencial): sin esta regla la pregunta "¿cuál es el distrito más pobre?" no tiene respuesta.',
  'Se evalúa en la etapa 2 tras R-ENC-06. Distritos creados después del año del dato: mostrar la estimación de cada distrito de origen por separado con el rótulo "en {anio}, este territorio formaba parte de {origen}", sin promediar ni sumar.',
  'Si hay varios distritos de origen, se listan todos; nunca se imputa un valor al distrito nuevo.',
  ['PR-25', 'PR-26'], aplica_a={'naturaleza_dato': ['estimacion_modelada'], 'tipo_medida': [], 'base_geografica': [], 'fuentes': ['INEI-MAPA-POBREZA', 'INEI-MAPA-DCI-PROVINCIAL-2019']}),
 regla('R-REG-14', 'registros', 'Cambio entre años en registros',
  'Solo se dice que una tasa o proporción de registro cambió si pasa una prueba de diferencia y la cobertura del registro no varió más de 5 puntos entre los años comparados.',
  "test_cambio.p < alfa AND |cobertura_registro_estimada(t1) − cobertura_registro_estimada(t0)| <= 5 → test_cambio.significativo = true; si la cobertura es NULL o variable → 'no se puede afirmar que haya cambiado'",
  'advertir', {'prueba_tasas': 'razón de tasas, prueba exacta de Poisson', 'prueba_proporciones': 'diferencia de proporciones, IC de Newcombe (Wilson)', 'max_variacion_cobertura_pp': 5},
  'Con estos registros no se puede afirmar que haya cambiado: también cambió cuántos casos se registran.',
  'R-ENC-11 solo cubría encuestas; R-CRUCES-07 y R-LENGUAJE-02 exigen una prueba de cambio para usar "aumentó/disminuyó".',
  'Guarda test_cambio igual que R-ENC-11. Usa la tabla cobertura_registro_estimada; para SIEN, la cobertura de tamizaje.',
  'Con conteos < 20 en algún año, se agrupan 3 años antes de la prueba (R-REG-03).',
  ['PR-08', 'PR-09'], aplica_a={'naturaleza_dato': ['registro_administrativo'], 'tipo_medida': [], 'base_geografica': [], 'fuentes': []}),
 regla('R-GASTO-17', 'gasto', 'Periodo por defecto y listado de obras',
  'Si la pregunta de gasto no dice periodo, se usa el último año cerrado; si pide "en qué obras", se listan como máximo 10 proyectos ubicados por CUI.',
  "periodo_pedido IS NULL → anio = ultimo_anio_cerrado; intencion_pregunta == 'listar_obras' → top_n(dim_inversion WHERE ubigeo = pedido, orden = devengado_acumulado_constante DESC, n = 10)",
  'publicar', {'n_max_obras': 10, 'columnas': ['nombre', 'estado', 'avance_fisico', 'avance_financiero', 'devengado_acumulado'],
   'bloque_aparte': 'obras con varias ubicaciones', 'excluir': 'mantenimientos sin CUI (se mencionan en nota)'},
  'Se muestran las obras con mayor gasto acumulado registradas en {territorio}. Las obras que abarcan varios distritos van aparte.',
  'Sin periodo por defecto las respuestas no son reproducibles; el listado sin límites ni orden sería ilegible.',
  'Montos en soles constantes (R-GASTO-12). "Invertir", "obras", "construir" → genérica 2.6 y TIPO_ACT_PROY = proyecto; "gastar" → todo el gasto del tema.',
  'Si hay menos de 10 obras, se listan todas. Si ninguna, se dice "no se registran proyectos con ubicación en {territorio}".',
  ['PR-18', 'PR-34'], aplica_a={'naturaleza_dato': ['gasto'], 'tipo_medida': [], 'base_geografica': [], 'fuentes': ['MEF-DETALLE-INVERSIONES', 'MEF-DA-PRESUPUESTO-EJECUCION-GASTO']}),
]

# (id, campo, operación, valor). Operaciones: set, borde (añade a casos_borde), param (clave, valor), replace (viejo, nuevo).
PARCHES = [
 # PR-02, PR-10: jerarquías faltantes
 ('R-CRUCES-08', 'param', ('jerarquias.vacunacion_infantil', 'departamento: INEI-ENDES principal; provincia/distrito: MINSA-INMUNIZACIONES rotulado "vacunas aplicadas en establecimientos ubicados en…"'), 'PR-02'),
 ('R-CRUCES-08', 'param', ('jerarquias.mortalidad_infantil', 'departamento: INEI-ENDES (periodo de 10 años previo a la encuesta) principal; MINSA-SINADEF/CNV registrada complementaria; provincia/distrito: solo registrada (R-REG-04, R-REG-07)'), 'PR-10'),
 ('R-CRUCES-08', 'param', ('jerarquias.pobreza_monetaria', 'departamento: INEI-ENAHO último año; distrito: INEI-MAPA-POBREZA 2018 como cifra principal en rojo solo si es la única fuente distrital (R-EST-05); nunca restada de ENAHO'), 'PR-25'),
 # PR-03: Lima Metropolitana
 ('R-ENC-06', 'replace', ("Provincia Lima (1501) con ENAHO: coincide con el dominio Lima Metropolitana → se publica como dominio, no como provincia genérica.",
   "Lima Metropolitana NO equivale a la provincia 1501: en los informes de pobreza ENAHO del INEI incluye la Provincia Constitucional del Callao (1501 + 0701). La composición se lee de dim_dominio por (encuesta, año, informe)."), 'PR-03'),
 ('R-ENC-07', 'borde', 'Lima Metropolitana se define por dim_dominio (encuesta, año, informe); en pobreza ENAHO = provincia de Lima + Callao. El mensaje muestra la composición. No sumar Callao por separado en la misma respuesta.', 'PR-03'),
 ('R-TERRITORIO-06', 'borde', 'Lima Metropolitana no es un ubigeo: es un dominio cuya composición depende de la encuesta (pobreza ENAHO: 1501 + 0701). Ver dim_dominio.', 'PR-03'),
 # PR-05, PR-06, PR-14: semáforo
 ('R-CRUCES-09', 'param', ('criterios.vigencia', 'solo para la cifra más reciente de cada indicador (estado actual): edad <=2 → 0; 3–5 → 1; >5 → 2. Los puntos de una serie heredan el semáforo de la comparación (precisión + quiebre)'), 'PR-05'),
 ('R-CRUCES-09', 'param', ('criterios.quiebre', 'usa es_comparable(fuente, indicador, anio_a, anio_b) sobre el campo quiebres (con comparable_con): comparable → 0; modalidad distinta → 1; definición distinta sin homologar → 3'), 'PR-06'),
 ('R-CRUCES-09', 'param', ('criterios_estructurales', ['tipo_medida_vs_concepto', 'base_geografica']), 'PR-14'),
 ('R-CRUCES-09', 'set', ('condicion', "puntaje_k ∈ {0,1,2,3} para cada criterio k. nivel = max_k(puntaje_k); si count(puntaje_k == 1 para k NO estructural) >= 3 → nivel = max(nivel, 2). Los criterios estructurales (tipo_medida_vs_concepto, base_geografica) cuentan como un solo criterio y su significado lo comunica el rótulo de R-REG-01. 0 → verde; 1 → ámbar; 2 → rojo; 3 → no_publicable. Se calcula en la etapa 7, antes de los cruces."), 'PR-14'),
 ('R-CRUCES-02', 'borde', 'B9 se aplica a cruces entre indicadores distintos, no a comparaciones entre años de un mismo indicador.', 'PR-05'),
 ('R-LENGUAJE-04', 'borde', 'No se aplica a las cifras que forman parte de una serie cuyo último año tiene edad <= 2.', 'PR-05'),
 ('R-CRUCES-04', 'borde', 'Prevalece R-ENC-13: 2020 se excluye de tendencias salvo que el campo quiebres declare comparable_con (pobreza monetaria ENAHO). Se usa es_comparable().', 'PR-06'),
 ('R-ENC-13', 'borde', 'Usa la función común es_comparable(fuente, indicador, anio_a, anio_b), compartida con R-CRUCES-03, R-CRUCES-04 y R-CRUCES-09.', 'PR-06'),
 # PR-07
 ('R-ENC-08', 'borde', 'inferencia_verificada se registra por (fuente, año, módulo) con la cita de la ficha técnica de ese año. Antes del MVP: ENDES y ENAHO 2015–2025 y ENLA 2019–2025. Una regla específica que fije el nivel desde la ficha oficial (R-ENC-15) registra inferencia_verificada = true.', 'PR-07'),
 # PR-09, PR-11
 ('R-REG-10', 'borde', 'Quiebre automático por cobertura: si |cobertura_registro_estimada(t) − cobertura(t0)| > 5 pp o algún año < 80 %, no se publica tendencia de la tasa registrada (solo conteos con nota).', 'PR-09'),
 ('R-REG-07', 'param', ('bandas_cobertura', {'>=90': "'tasa registrada', publicar", '80-89': "'tasa registrada', publicar_referencial", '60-79': 'publicar_referencial con advertencia de subregistro', '<60 o NULL': 'solo conteo, sin tasa'}), 'PR-11'),
 ('R-REG-07', 'borde', 'Tabla única de bandas (parametros.bandas_cobertura). R-REG-01 y R-REG-04 la referencian sin repetir umbrales. Cobertura NULL = banda más baja.', 'PR-11'),
 ('R-REG-01', 'borde', 'El uso de la palabra "tasa" y su calificación siguen las bandas de R-REG-07.', 'PR-11'),
 ('R-REG-04', 'borde', 'Umbrales de cobertura: los de R-REG-07 (bandas_cobertura).', 'PR-11'),
 # PR-12, PR-13, PR-30: lenguaje
 ('R-LENGUAJE-02', 'borde', 'El corrector solo revisa el texto que escribe el LLM. mensaje_usuario, frases_estandar y plantillas son spans protegidos marcados por el motor ({{p:id}}). "por eso" se permite cuando explica un método o una limitación de datos. "estadísticamente significativo" está permitido.', 'PR-12'),
 ('R-GASTO-15', 'param', ('bloqueo_con_contexto', "'redujo'/'logró reducir' solo se bloquean si el sujeto o complemento es gasto, programa o inversión; para describir el indicador se usan las fórmulas de R-ENC-11 y R-REG-14"), 'PR-30'),
 ('R-LENGUAJE-03', 'borde', 'Marcadores adicionales: {{e:id}} entidades (colegios, obras, normas) y {{u:id}} universo (desde indicador.poblacion_objetivo). Lista blanca de números no estadísticos: edades ("6 a 35 meses", "65 años o más"), "N.°", "Ley N.°", CUI. El corrector se aplica dos veces: al texto del LLM (prohibiciones de redacción) y al texto renderizado (patrones con dígitos).', 'PR-13'),
 # PR-15, PR-16, PR-17
 ('R-GASTO-03', 'borde', 'Departamento 15 (Lima): no se usa la cifra departamental como respaldo principal. Se muestra el gasto municipal y de obras como respuesta parcial con NC-GASTO-LUGAR; se excluyen las ejecutoras de alcance nacional (lista curada) y en el MVP se construye ambito_ejecutora solo para DIRIS y UGEL de Lima Metropolitana.', 'PR-15'),
 ('R-GASTO-03', 'param', ('filtro_igual_cifra', True), 'PR-16'),
 ('R-GASTO-03', 'borde', 'pct_gasto_atribuible se calcula con el mismo filtro de la cifra (tema × genérica o tipo de actividad/proyecto × fase × año).', 'PR-16'),
 ('R-GASTO-02', 'borde', 'Si la prueba de humo confirma una sola ubicación por CUI, toda cifra de inversión distrital pasa a referencial con el rótulo "ubicación principal registrada; la obra puede abarcar otros distritos" y su criterio base_geografica vale 1.', 'PR-17'),
 # PR-19
 ('R-GASTO-14', 'borde', 'PRONIED: proyectos solo por CUI; mantenimientos de locales escolares por código de local → ubigeo de MINEDU-ESCALE-PADRON. El emparejamiento por nombre solo con revisión humana.', 'PR-19'),
 ('R-TERRITORIO-08', 'borde', 'Para PRONIED prevalece R-GASTO-14: el emparejamiento por nombre no se usa de forma automática.', 'PR-19'),
 # PR-21
 # (semántica de aplica_a: se documenta en reglas.md, sección 1)
 # PR-22, PR-23, PR-24
 ('R-EST-04', 'borde', 'Si el denominador es un prorrateo propio de menos de 100 personas sin contraste por edad compatible: se publica el conteo de usuarios y la cobertura provincial, no el porcentaje distrital. No se inventan rangos para denominadores sin IC.', 'PR-22'),
 ('R-REG-08', 'borde', '"Avance de meta" solo se usa si la pregunta es por la meta del programa.', 'PR-22'),
 ('R-DENOMINADORES-01', 'borde', '"Cobertura recalculada" (denominador propio) y "cobertura publicada por el MINSA" son dos indicadores distintos del catálogo (concepto_medido distinto). La matriz se ajusta a las decisiones D4 y D8.', 'PR-23'),
 ('R-DENOMINADORES-05', 'borde', 'INEI-CPV2025: solo sirve de contraste para totales y 60+ y solo cuando haya resultados distritales publicados (verificar en cada carga). No sirve para < 1 año, < 5 años ni 65+ hasta que haya edades simples o quinquenales por distrito.', 'PR-24'),
 # PR-27, PR-28
 ('R-ENC-14', 'set', ('condicion', "tema == 'anemia' AND (criterio_medicion IS NULL → suprimir; COUNT(DISTINCT criterio_medicion) > 1 en la serie → bloquear la comparación entre tramos)"), 'PR-28'),
 ('R-ENC-14', 'borde', 'Se muestran dos tramos rotulados (A: criterio anterior hasta 2024; B: vigente desde 2024), cada uno con su prueba de cambio; la cifra principal es la más reciente del criterio vigente. En registros (SIEN, REUNIS) el criterio se asigna por fecha de tamizaje, y 2024 se publica solo por periodos homogéneos.', 'PR-27'),
 # PR-29: referencias rotas
 ('R-REG-03', 'replace', ('(R-REG-09)', '(R-REG-10)'), 'PR-29'),
 ('R-REG-04', 'replace', ('(R-REG-09)', '(R-REG-10)'), 'PR-29'),
 ('R-GASTO-07', 'replace', ('(ver R-GASTO-12)', '(ver R-GASTO-14)'), 'PR-29'),
 ('R-DENOMINADORES-05', 'replace', ('por R-DENOMINADORES-06', 'por R-REG-08'), 'PR-29'),
 ('R-GASTO-08', 'borde', 'Quiebre del PAN: PP 0001 migró a PPoR 1001 en dos pasos (2021 parcial, 2023 completo); PP 0002 no migró. El año se lee del campo quiebres de MEF-PPR-PROGRAMAS-PRESUPUESTALES, no se fija en cada regla.', 'PR-29'),
 ('R-CRUCES-04', 'borde', 'Quiebre PP 0001 → 1001: ver R-GASTO-08 (2021 y 2023).', 'PR-29'),
 # PR-31, PR-32, PR-33, PR-35, PR-36
 ('R-LENGUAJE-01', 'borde', 'Territorio admite una lista corta por cifra principal ("anemia: establecimientos de X · encuesta: Y") o "varios niveles, ver detalle". Se muestran hasta 2 códigos NC si la respuesta combina gasto y resultado. Ficha mínima válida: semáforo "Sin cifra disponible", fuentes consultadas y motivo codificado.', 'PR-31, PR-36'),
 ('R-CRUCES-10', 'borde', 'Sin cifra principal publicable, el semáforo de respuesta es "Sin cifra disponible" (ficha mínima de R-LENGUAJE-01).', 'PR-36'),
 ('R-CRUCES-05', 'param', ('compat_base_adicional', {'establecimiento×ejecutora_municipal': 'lado a lado a distrito, con rótulo, sin cociente', 'establecimiento×inversion_ubicacion': 'lado a lado a distrito, con rótulo, sin cociente', 'establecimiento×meta_departamento': 'solo a departamento'}), 'PR-32'),
 ('R-CRUCES-07', 'borde', 'Si la evolución del resultado está bloqueada por un quiebre, el paso 2 dice "no se puede mostrar la evolución porque {motivo_quiebre}" y da la cifra más reciente.', 'PR-32'),
 ('R-ENC-15', 'borde', 'Por defecto: grado(s) del último ENLA disponible y la competencia pedida; "Lima" = Lima Metropolitana y Lima Provincias por separado.', 'PR-33'),
 ('R-ENC-11', 'borde', 'El límite es 1 comparación por par de cifras, no por cifra.', 'PR-33'),
 ('R-ENC-06', 'borde', '(posterior) Si el territorio pedido es mayoritariamente rural (población urbana CPV2017 < 30 %) y la celda departamento × área pasa las reglas de precisión, se ofrece como segunda alternativa la cifra rural del departamento, rotulada.', 'PR-35'),
 ('R-GASTO-13', 'borde', 'El promedio de 3 años del gasto de capital se aplica a los cruces de asociación de cualquier nivel.', 'PR-34'),
 # PR-38
 ('R-EST-01', 'param', ('aviso_fijo_pobreza_2018', 'Foto de 2018, anterior a la pandemia; la situación actual probablemente es distinta.'), 'PR-38'),
 ('R-EST-01', 'replace', ("sin rótulo", "(ni con rótulo; ver R-EST-05)"), 'PR-26'),
]

LENGUAJE = {  # cambios a lenguaje.prohibidas (PR-12)
 r'\bgracias a\b|\bdebido a\b|\bpor efecto de\b|\bcomo resultado de\b|\bpor eso\b|\blo que explica\b|\ben consecuencia\b':
   (r'\bgracias a\b|\bdebido a\b|\bpor efecto de\b|\bcomo resultado de\b|\bpor eso\b|\blo que explica\b|\ben consecuencia\b',
    "'debido a' y 'por eso' para explicar un cambio de método o una limitación de datos; spans protegidos {{p:id}}"),
 r'\bsignificativ[oa]\b(?! estad)': (r'(?<!estadísticamente )\bsignificativ[oa]\b(?! estad)', 'tras "estadísticamente"'),
}

CAMPOS_NUEVOS = [
 ('insumos', 'indicador', '—', 'Fuentes y tablas de las que depende la cifra (R-DEP-01).'),
 ('periodo_referencia_ini / periodo_referencia_fin', 'cifra', 'anio_referencia', 'Periodo al que se refiere la cifra cuando difiere del año de la encuesta (mortalidad ENDES, R-CRUCES-08).'),
 ('nivel_pedido', 'respuesta', 'nivel_solicitado, nivel_pedido', 'Nivel territorial que pidió el usuario (R-ENC-06, R-TERRITORIO-09).'),
 ('subregistro_conocido', 'indicador', 'idem', 'Fuente con subregistro documentado (R-CRUCES-09).'),
 ('covariables_modelo / validado_contra_oficial', 'catálogo', 'idem', 'Metadatos de estimaciones modeladas (R-EST-02, R-ENC-18).'),
 ('requiere_denominador / n_desagregaciones_adicionales / tasa_suavizada / periodicidad_estimacion', 'indicador', 'idem', 'Campos usados en condiciones de R-DENOMINADORES-01, R-ENC-09, R-REG-06 y R-ENC-06.'),
 ('estado_ubigeo', 'tabla', '—', 'vigente | pendiente | suprimido en dim_ubigeo_historico (R-TERRITORIO-09).'),
 ('ambito_ejecutora', 'tabla', '—', 'Alcance real de una unidad ejecutora (nacional, departamental, DIRIS/UGEL) para el gasto en Lima (R-GASTO-03).'),
]

AJUSTES_DECISIONES = {
 'D5': 'Para preguntas departamentales, contexto con aviso. Para preguntas distritales sin otra fuente, cifra principal en rojo fijo y ranking solo por grupos (R-EST-05).',
 'D1': 'MVP: dos tramos separados y rotulados (criterio anterior hasta 2024; vigente desde 2024), sin tendencia cruzada; recalcular con el criterio vigente en la fase 4.',
}

SEMANTICA_APLICA_A = ('Semántica de aplica_a: si "fuentes" no está vacía es una lista cerrada (la regla solo aplica a esas fuentes); '
  'si está vacía, se exige que se cumplan a la vez todas las listas de atributos no vacías (naturaleza_dato, tipo_medida, base_geografica).')
