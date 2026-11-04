"""Ajustes a las especificaciones de la capa 0 por decisiones del dueño (6/10/2026).
Se aplican en consolida_reglas.py; especificaciones_capa0.md nunca se edita a mano."""

COLUMNAS_DIM_UBIGEO = [
 {'columna': 'nombre_oficial_inei', 'tipo': 'text', 'regla': 'Nombre tal como lo publica el INEI (mayúsculas, sin tildes). Se usa para emparejar fuentes.'},
 {'columna': 'nombre_mostrado', 'tipo': 'text', 'regla': 'Nombre con tildes y mayúsculas correctas para mostrar al usuario. Fuente (decisión del dueño, 6/10/2026): INEI, Directorio Nacional de Municipalidades 2025, que se cita como fuente (columna fuente_nombre_mostrado); si la unidad no figura en el Directorio (departamentos, distritos creados después de feb-2025), el archivo propio o la ley de creación.'},
 {'columna': 'capital_legal, lat_capital, lon_capital, altitud_capital', 'tipo': 'text, numeric', 'regla': 'Capital legal y su ubicación (no es el centro del territorio). Fuente primaria: INEI, Directorio Nacional de Municipalidades 2020 (Lib1725), vía el archivo propio.'},
 {'columna': 'tipologia_pcm', 'tipo': 'text', 'regla': 'Tipología de distrito de la PCM (RV N.° 005-2019-PCM/DVGT, anexo 2), vía el archivo propio; confirmar si hay versión más reciente.'},
]
DIM_AMBITO = {
 'proposito': 'Ámbitos territoriales que no son un ubigeo único pero sí unidades de gestión o de inferencia. Cada ámbito se define como lista de ubigeos y puede variar por fuente.',
 'columnas': [
  {'columna': 'ambito_id', 'tipo': 'text', 'regla': 'Clave estable (p. ej., LIMA_REGION).'},
  {'columna': 'nombre_mostrado', 'tipo': 'text', 'regla': 'Nombre para el usuario.'},
  {'columna': 'composicion', 'tipo': 'text[]', 'regla': 'Ubigeos (provincias o distritos) que lo forman.'},
  {'columna': 'gestion', 'tipo': 'text', 'regla': 'Entidad que lo gestiona, si aplica.'},
  {'columna': 'fuente_definicion', 'tipo': 'text', 'regla': 'Norma, ficha técnica o encuesta que lo define.'},
  {'columna': 'codigo_en_fuentes', 'tipo': 'jsonb', 'regla': 'Código que usa cada fuente (p. ej., archivo propio: 159999).'},
 ],
 'ambitos_iniciales': [
  'LIMA_METROPOLITANA: provincia de Lima (1501, 43 distritos), gestionada por la Municipalidad Metropolitana de Lima; sin el Callao.',
  'LIMA_REGION (Lima Provincias): departamento 15 sin la provincia de Lima = 9 provincias (Barranca, Cajatambo, Canta, Cañete, Huaral, Huarochirí, Huaura, Oyón, Yauyos), 128 distritos, gestionada por el Gobierno Regional de Lima (sede Huacho). En el archivo propio tiene el código 159999; su superficie (32 208,36 km²) coincide exactamente con departamento 15 menos provincia 1501.',
  'AREA_METROPOLITANA_LIMA_CALLAO: provincia de Lima + Callao (1501 + 0701), dominio de inferencia de la ENAHO en pobreza (ver R-ENC-07.dominios_lima).',
  'CALLAO: departamento y provincia 07, gestionado por el Gobierno Regional del Callao; dominio propio en la ENDES.',
 ],
 'uso': 'Para gasto: lo ejecutado por el Gobierno Regional de Lima se atribuye a LIMA_REGION, no al departamento 15 completo (complementa R-GASTO-03). Para encuestas: el dominio se toma de dim_dominio según encuesta y año.',
}

# Correcciones de texto en reglas por hallazgos de la construcción (S1, 6/10/2026). (regla, texto_anterior, texto_nuevo)
PARCHES_REGLAS = [
 ('R-TERRITORIO-05',
  'Denominador del hijo para años previos a su creación: solo si la fuente de población lo trae (las proyecciones 2018-2026 retroproyectan a los 1 892 distritos); nunca se divide el numerador histórico de la madre entre madre e hijo.',
  'Denominador del hijo para años previos a su creación: no existe. La proyección 2018-2026 (INEI, dic-2025) no retroproyecta a los distritos creados después de 2017: antes de su año de creación trae el texto «Distrito creado en …» y asigna población desde el mismo año de creación (verificado en S1). En esos años la cifra solo existe para el grupo comparable, cuya población es continua porque la madre incluye el territorio del hijo; nunca se divide el numerador ni el denominador histórico de la madre entre madre e hijo.'),
]


# Correcciones por la auditoría de la Ola 0 (6/10/2026) y decisiones del dueño del mismo día.
# (regla, campo, texto que se AGREGA al final del campo). Se aplican en consolida_reglas.py.
AGREGADOS_REGLAS = [
 ('R-TERRITORIO-01', 'implementacion',
  ' [Auditoría Ola 0, TE-02/SP-01] Datos anuales: la pertenencia se decide por año con dim_ubigeo_historico.anio_datos_desde/anio_datos_hasta (función vigentes_en_anio): un distrito nuevo y la versión recortada de su madre cuentan desde el primer año en que el INEI les asigna población (Lambras 2020; Alto Trujillo 2023, aunque la ley es de dic-2022); si el INEI aún no los tiene, desde el año siguiente al último de la proyección. Eventos (nacimientos, defunciones): fecha exacta con vigente_desde/vigente_hasta. Nacional (000000) y departamentos existen desde 1995-01-01; distritos y provincias desde GEO2017 (2017-10-22): antes de 2018 las composiciones (dim_dominio) usan la lista GEO2017 y se marcan composicion_aproximada_geo2017. Cronología: +Sangani (Ley 32729, 15-07-2026; código 120307 asignado provisionalmente por el dueño, estado_ubigeo = pendiente hasta que el INEI lo publique) = 1 893 distritos.'),
 ('R-TERRITORIO-04', 'condicion',
  ' [Auditoría Ola 0, TE-04] También pasa a GEO2017 si EXISTS d en el resultado con d.grupo_comparable_geo2017 <> d.ubigeo_inei (escisiones y distritos con ajuste de límites agrupados por decisión del dueño: Laredo, Florencia de Mora, Acarí, Bella Unión), aunque el distrito tenga una sola versión. Para cruzar con fuentes en geografía 2017 (Mapa de Pobreza 2018) se usa puente_geo2017 (pesos de población 2018 por grupo).'),
 ('R-TERRITORIO-05', 'implementacion',
  ' [Auditoría Ola 0, TE-05] La adopción del código nuevo no se supone (ventana fija): en cada carga se mide por fuente y año la proporción del numerador del grupo comparable que viene con el código del hijo (p. ej. SIEN 2025 por residencia: Alto Trujillo 921 frente a 1 176 aún codificados en El Porvenir). Si es menor a 90 %, hijo y madre se publican solo como grupo comparable; se guarda en fuente_ubigeo_transicion.'),
 ('R-REG-07', 'implementacion',
  ' [Auditoría Ola 0, SP-03/TE-08] SIEN: los tres ubigeos (Ubigeo_EESS, UbigeoPN, UbigeoREN) se normalizan a 6 dígitos (el CSV pierde el cero inicial en los departamentos 01-09). La proporción de anemia se calcula por establecimiento (Ubigeo_EESS). La cobertura de tamizaje usa el numerador por residencia (UbigeoPN), se publica desde provincia y el % sin residencia es residuo explícito; en departamentos con más de 20 % sin residencia, solo a nivel departamento. Con el ubigeo del establecimiento la cobertura supera 100 % en 223 distritos: no se usa para cobertura.'),
 ('R-DENOMINADORES-01', 'implementacion',
  ' [Auditoría Ola 0, PO-02] Grupos de edad en meses desde fact_poblacion_grupo (tabla aparte para no contar la edad 0 dos veces): 6-35 m = 0,5·P0 + P1 + P2 y 6-59 m = 0,5·P0 + P1..P4 (supuesto de nacimientos uniformes dentro del año, columnas derivacion y supuesto); 0-35 m y 0-59 m exactos. Nunca se aproxima 6-35 m con las edades 0-2 (+20 %) ni 1-2 (−20 %).'),
 ('R-GASTO-01', 'condicion',
  ' [Auditoría Ola 0] (a) En gobiernos locales PLIEGO_NOMBRE viene vacío: el tipo de municipalidad se toma de EJECUTORA_NOMBRE (MUNICIPALIDAD DISTRITAL / PROVINCIAL / METROPOLITANA). (b) GA-02: DETALLE_INVERSIONES trae solo la ubicación principal del CUI; si el proyecto es del GN o de un GORE y el departamento de esa ubicación difiere de DEPARTAMENTO_META → nacional_multidepartamental (obra que cruza departamentos; no se carga a un distrito ni vuelve a la meta). (c) TE-03: si el distrito del CUI aún no existía en el año del gasto, se usa su distrito de origen principal. (d) Ámbitos de Lima: el GR Lima → LIMA_REGION; el pliego regional de la Municipalidad Metropolitana de Lima → LIMA_METROPOLITANA (decisión del dueño, 6/10/2026); sus filas de departamento_meta usan ubigeo_atribucion A-LIMA_REGION / A-LIMA_METROPOLITANA, no 150000.'),
 ('R-GASTO-03', 'implementacion',
  ' [Auditoría Ola 0, GA-01, decisión del dueño 6/10/2026: marcar] Las ejecutoras del GN con meta en Lima llevan alcance_ejecutora (curados/capa0/ejecutoras_alcance.yaml): nacional (sedes centrales, PNP, FF. AA., CENARES, SIS, PRONABEC, Congreso…) se excluye de toda cifra del departamento 15, de Lima Metropolitana y de Lima Región; lima_metropolitana (DIRIS, UGEL de Lima, hospitales y cortes de Lima) y lima_region pasan a esos ámbitos. GA-03: no se calcula variación interanual del gasto distrital en inversiones si la cobertura por CUI (revision/cobertura_cui.csv) difiere más de 5 pp entre los años comparados.'),
]


# ---------------------------------------------------------------- ronda 3 (pendientes menores, 7/10/2026)
# SP-03 (SIEN), GA-09 (CUI sin ubicar) y GA-05 (transferencias), con las decisiones del dueño del 7/10/2026.
# Respaldo: 03_auditoria/ola0/pendientes_menores/ (informes v2/v3, auditorías e implementacion/implementacion.md).
# (regla, campo con ruta 'a.b', valor): el campo se REEMPLAZA entero. Se aplica en consolida_reglas.py después de
# PARCHES_REGLAS y AGREGADOS_REGLAS.
_R_GASTO_05_ENUNCIADO = (
    'Cada fila de la genérica 2.4 lleva categoria_transferencia según curados/capa0/lista_transferencias.yaml. La '
    'categoría sale del código exacto del clasificador económico de gastos; las excepciones, del código de actividad y, si '
    'hace falta, del pliego. Nunca de un texto: los nombres de actividad solo disparan una alarma de revisión (G-18b). '
    '(a) intergubernamental (2.4.x.3.1.1–.3): el receptor está en la base y vuelve a registrar el gasto; queda fuera de '
    'toda suma de más de una entidad. (b) publico_fuera_de_base (2.4.x.3.1.4 y .5, salvo los fondos por identificar; y, '
    'por decisión del dueño del 7/10/2026, las transferencias municipales a centros poblados —EX-01— y a institutos viales '
    'provinciales —EX-02, rotulado «probable IVP»—): nadie vuelve a registrar el gasto; queda fuera de las cifras temáticas '
    'y va en columna propia del consolidado. (b′) fondo_por_identificar, «posible doble conteo» (transferencias a fondos '
    'que podrían financiar después a pliegos de la base, EX-03): fuera de las cifras temáticas y fuera de las dos columnas '
    'del consolidado; solo como nota, hasta documentar el fondo de destino. (c) gasto_final_externo (2.4.x.1, 2.4.x.2: '
    'organismos internacionales, compras vía OPS, UNICEF o UNFPA): gasto final; se incluye. Una específica 2.4 fuera de la '
    'lista detiene la construcción (G-15). El motor solo consulta v_gasto_tematico, v_gasto_consolidado (agregada, sin '
    'columna única de devengado) y v_gasto_fondos_por_identificar, y toda consulta pasa por '
    'guardia_gasto.verificar_consulta(). Las subvenciones a personas (Pensión 65, Juntos, Contigo, becas) están en la '
    'genérica 2.5 y no son transferencias. Los montos de MEF-DA-TRANSFERENCIAS (caja) nunca se suman al gasto.')
CAMPOS_REGLAS = [
 ('R-GASTO-05', 'titulo', 'Donaciones y transferencias: lista curada y guardia del motor (v4)'),
 ('R-GASTO-05', 'enunciado', _R_GASTO_05_ENUNCIADO),
 ('R-GASTO-05', 'condicion',
  "(1) Consulta que suma MONTO_AUTORIZADO o MONTO_ACREDITADO (MEF-DA-TRANSFERENCIAS) con MONTO_DEVENGADO → bloquear_cruce. "
  "(2) categoria_transferencia := coalesce(excepción aplicada por (clasificador, nivel_gobierno, actividad_accion_obra[, "
  "pliego]), categoría del clasificador en la lista, 'por_revisar') para GENERICA = '4'; NULL fuera de la 2.4. "
  "bloque_consolidado: intergubernamental → excluir_intergubernamental; publico_fuera_de_base → "
  "entregado_fuera_del_presupuesto; fondo_por_identificar → posible_doble_conteo_fondo; gasto_final_externo y fuera de la "
  "2.4 → gasto_final. (3) Cifra temática (función, programa, tema, territorio): solo bloque_consolidado = 'gasto_final' "
  "(v_gasto_tematico). (4) Consolidado multinivel: dos columnas que no se suman (v_gasto_consolidado: "
  "gasto_final_devengado/pim y entregado_fuera_del_presupuesto_devengado/pim); los fondos, aparte "
  "(v_gasto_fondos_por_identificar). (5) Cifra de una sola entidad (sec_ejec o pliego): incluye (a), (b) y (b′), rotuladas. "
  "(6) La guardia rechaza: leer el fact o la base sin sec_ejec = … o pliego = … como conjunción de primer nivel; "
  "toda consulta que lea a la vez columnas del gasto final y de lo entregado fuera del presupuesto, en cualquier nivel "
  "(expresión, alias, subconsulta, CTE, UNION, UNPIVOT o SELECT * sobre v_gasto_consolidado): cada línea del consolidado "
  "se pide en una consulta aparte; y combinar los fondos con el gasto."),
 ('R-GASTO-05', 'accion', 'bloquear_cruce'),
 ('R-GASTO-05', 'parametros', {
   'lista': 'curados/capa0/lista_transferencias.yaml (versión y huella en el manifiesto; revisado_dueno: false hasta cotejar el Anexo 2 del clasificador de cada año)',
   'vistas': 'curados/capa0/vistas_gasto.sql',
   'guardia': 'src/pap/capa0/guardia_gasto.py',
   'bloquear_cruce_vigente': 'solo cuando la guardia esté conectada al ejecutor del motor; hasta entonces la protección es la vista agregada y las pruebas G-17c y test_transferencias',
   'umbral_por_revisar': 0,
   'pruebas': ['G-15', 'G-15b', 'G-17', 'G-17b', 'G-17c', 'G-18', 'G-18b'],
   'excepciones_aplicadas': {'EX-01': 'centros poblados → (b)', 'EX-02': 'probable IVP → (b)', 'EX-03': 'fondos → (b′)'},
   'monto_transferencia_publicable': 'MONTO_ACREDITADO'}),
 ('R-GASTO-05', 'mensaje_usuario',
  'Cifra temática: «No incluye S/ {b} millones que {entidad} entregó a fondos y entidades públicas fuera del presupuesto '
  '(por ejemplo, {principal})». Consolidado, en dos líneas que no se suman: «Gasto de las entidades del presupuesto: S/ '
  '{gasto_final}» y «Entregado a fondos y entidades públicas fuera del presupuesto: S/ {b}». Nota fija: «No sumamos las '
  'transferencias entre entidades del Estado, porque quien las recibe ya registra ese gasto». Fondos (b′), si existen en '
  'el año: «Además, S/ {f} se transfirieron a fondos cuyo uso final no está identificado; podrían reaparecer como gasto '
  'de otras entidades, por eso no se suman». (c), cuando pesa: «Incluye S/ {c} en vacunas y medicinas compradas a través '
  'de la OPS y otros organismos internacionales».'),
 ('R-GASTO-05', 'implementacion',
  'gasto.py (ronda 3, VERSION_TABLA 1.2.0): transferencias.registrar crea la vista base con categoria_transferencia, '
  'excepcion_transferencia, es_transferencia (a, b o b′), es_transferencia_intergub y bloque_consolidado; '
  'fact_gasto_territorial los lleva y su clave usa categoria_transferencia. Las vistas del motor se crean y se prueban en '
  'cada construcción (G-17c: temático = gasto final consolidado; gasto final + (b) + fondos + (a) = total del fact = '
  'total de la base, tolerancia 0). Territorio: el (b) del Gobierno Nacional con meta en Lima en 2025 (1 962,7) se reparte '
  'en 1 825,8 de alcance nacional (nunca van a Lima), 114,7 de lima_callao (Agua Segura, ejecutora 1691) y 22,2 no '
  'territorializable; aparte, fuera de (b), van 195,0 de fondos por identificar (b′: 100,0 con meta en Lima de alcance '
  'nacional y 95,0 no territorializable). El (b) municipal pertenece al territorio de la municipalidad que transfiere. Cada año fiscal nuevo se coteja la lista con '
  'el Anexo 2 del clasificador y se sube su versión.'),
 ('R-GASTO-05', 'casos_borde',
  'Transferencias a personas (subvenciones, Juntos, Pensión 65) son gasto final de la genérica 2.5: no se excluyen. '
  'MONTO_AUTORIZADO puede diferir del ACREDITADO; usar acreditado. EX-02 (institutos viales) tiene confianza media: se '
  'rotula «probable IVP» hasta cotejar con el registro de IVP de Provías Descentralizado. «MINSA 568 + CENARES 238» es el '
  'mismo dinero (CENARES es ejecutora del MINSA). La alarma G-18b solo avisa: una fila nueva con «CENTRO POBLADO», '
  '«CAMINOS VECINALES», «INSTITUTO VIAL» o «BENEFICENCIA» en (a) se revisa y, si corresponde, se agrega como excepción por '
  'código.'),
 ('R-GASTO-05', 'referencias', [
   {'titulo': 'MEF – Clasificadores presupuestarios (índice)', 'url': 'https://www.mef.gob.pe/es/clasificadores-presupuestarios'},
   {'titulo': 'MEF – Anexo 2, clasificador económico de gastos 2025 (RD 0039-2024-EF/50.01)', 'url': 'https://cdn.www.gob.pe/uploads/document/file/7405290/6312586-anexo_2_rd0039_2024ef5001.PDF'},
   {'titulo': 'MEF, DGCP – Transferencias financieras (ejercicio 2014): tipos de receptor', 'url': 'https://www.mef.gob.pe/contenidos/conta_publ/capacitaciones/seminario_dic2014/exposiciones/TRANSFERENCIAS_FINANCIERAS_CANORIO.pdf'},
   {'titulo': 'RM 555-2024/MINSA – CENARES transfiere a la OPS/OMS para comprar vacunas', 'url': 'https://busquedas.elperuano.pe/dispositivo/NL/2316660-1/'},
   {'titulo': 'MEF – Diccionario de datos: Transferencias (Transferencias_Diccionario.csv)', 'url': 'https://fs.datosabiertos.mef.gob.pe/datastorefiles/Transferencias_Diccionario.csv'},
   {'titulo': 'MEF – Diccionario de datos: Presupuesto y Ejecución de Gasto (Gastos_Diccionario.csv)', 'url': 'https://fs.datosabiertos.mef.gob.pe/datastorefiles/Gastos_Diccionario.csv'}]),
 ('R-TERRITORIO-08', 'parametros.sien_cobertura_tamizaje',
  'por departamento (extensión aprobada por el dueño el 7/10/2026): el % de niños de 6-35 m con procedencia (UbigeoPN) se '
  'mide por departamento del establecimiento (E-06, revision/sien_pn_6_35m_por_departamento.csv) solo como diagnóstico; '
  'la cobertura de tamizaje se publica únicamente por departamento, con dos cotas (R-REG-07), aunque un departamento '
  'supere el 95 %'),
 ('R-REG-07', 'parametros.sien_cobertura_cotas',
  'inferior = niños 6-35 m procedentes del departamento / población 6-35 m; superior = inferior + niños sin procedencia '
  'atendidos en establecimientos del departamento (no es una cota estricta: omite a los niños sin procedencia del '
  'departamento atendidos en otros departamentos); semáforo con la cota superior; aviso si el intervalo cruza '
  'sien_umbral_tamizaje_pct'),
]
# (regla, campo, texto que se AGREGA al final del campo)
AGREGADOS_REGLAS_R3 = [
 # R-GASTO-02 (GA-09): el texto de la ronda 3 se integró en la reescritura completa de la ronda 4 (CAMPOS_REGLAS, más abajo).
 ('R-TERRITORIO-08', 'enunciado',
  ' Extensión para la cobertura de tamizaje del SIEN (dueño, 7/10/2026): el % ubicado se mide por departamento y la '
  'cobertura se publica solo por departamento, con dos cotas (R-REG-07).'),
 ('R-TERRITORIO-08', 'implementacion',
  ' [Ronda 3, SP-03] SIEN-Hb 2025, niños de 6-35 m: procedencia (UbigeoPN) ubicada en el 84,6 % nacional; solo '
  'Huancavelica (97,7 %) y Ayacucho (96,0 %) llegan al 95 %. Aun así, la cobertura no se publica por provincia ni por '
  'distrito: el niño sin procedencia no falta al azar (más joven y con más anemia). La proporción de anemia sigue D4 '
  '(ubigeo del establecimiento).'),
]
# Reemplaza la frase de cobertura del agregado de R-REG-07 (auditoría Ola 0) por la decisión de la ronda 3.
R_REG_07_COBERTURA_OLA0 = (
 'La cobertura de tamizaje usa el numerador por residencia (UbigeoPN), se publica desde provincia y el % sin residencia es '
 'residuo explícito; en departamentos con más de 20 % sin residencia, solo a nivel departamento.')
R_REG_07_COBERTURA_R3 = (
 '[Ronda 3, SP-03 v3; decisión del dueño 7/10/2026] Según el diccionario oficial del INS, UbigeoPN es la procedencia del '
 'niño (no la residencia del Padrón Nominal) y UbigeoREN/AlturaREN son el ubigeo y la altitud del establecimiento según '
 'RENIPRESS (el ajuste de la hemoglobina usa la altitud del establecimiento). La cobertura de tamizaje de 6-35 m se '
 'publica solo por departamento, con dos cotas (parámetro sien_cobertura_cotas): «entre {inf} y {sup} de cada 100 niños»; '
 'el semáforo usa la cota superior y, si el intervalo cruza el 50 %, se avisa: «Con los datos disponibles no podemos '
 'decir si la cobertura supera o no la mitad de los niños» (2025: La Libertad, Loreto, Moquegua, Puno y Tacna). La cota '
 'superior no es estricta: no cuenta a los niños sin procedencia del departamento que se atendieron en establecimientos '
 'de otros departamentos (nota para la ficha).')

# Especificación nueva de la capa 0 (SP-03 v3, texto_receta_v3.md §2 y §3)
ESPECIFICACIONES_R3 = {
 'fact_sien_hb_ubigeo': {
  'proposito': 'SIEN-Hb (niños de 6 a 59 meses tamizados en EESS del MINSA y de los GORE) agregado por establecimiento, los tres ubigeos y grupo de edad. Lo construye puentes.py (sprint s3_puentes). Definiciones contrastadas con el diccionario oficial de la PNDA («2.Diccionarios HIS - 2025.xlsx», hoja Niños0a5) y con «Metadatos SIEN.docx».',
  'columnas': [
   {'columna': 'anio', 'tipo': 'int', 'regla': 'Año del ZIP (de la ruta interna; debe ser único).'},
   {'columna': 'id_insumo', 'tipo': 'text', 'regla': 'Hash sha256 del insumo.'},
   {'columna': 'cod_ipress', 'tipo': 'char(8)', 'regla': 'Renipress con ceros a la izquierda.'},
   {'columna': 'ubigeo_eess', 'tipo': 'char(6)', 'regla': 'Ubigeo_EESS con zfill(6). Base de la proporción de anemia (D4).'},
   {'columna': 'ubigeo_procedencia', 'tipo': 'char(6) null', 'regla': "UbigeoPN con zfill(6) («procedencia del niño», según el diccionario). NULL si viene '', '0' o '000000'."},
   {'columna': 'ubigeo_ref_altitud', 'tipo': 'char(6)', 'regla': 'UbigeoREN con zfill(6). Solo es metadato del ajuste por altitud; no sirve para ubicar al niño.'},
   {'columna': 'grupo_edad', 'tipo': 'text', 'regla': '6-11m, 12-23m, 24-35m, 36-59m o fuera_de_rango.'},
   {'columna': 'filas', 'tipo': 'int', 'regla': 'Filas del SIEN (supuesto: niños, con su última atención del año).'},
   {'columna': 'filas_dx_valido', 'tipo': 'int', 'regla': 'Filas con Dx en {Normal, Anemia Leve, Anemia Moderada, Anemia Severa}. Denominador de la anemia.'},
   {'columna': 'filas_con_anemia', 'tipo': 'int', 'regla': 'Dx válido distinto de Normal (RM 251-2024/OMS 2024).'},
   {'columna': 'unidad, criterio_anemia, version_tabla', 'tipo': 'text', 'regla': 'nino_ultima_evaluacion_anio, RM251-2024/OMS2024, 1.2.0.'},
  ],
  'clave': '(anio, id_insumo, cod_ipress, ubigeo_eess, ubigeo_procedencia, ubigeo_ref_altitud, grupo_edad)',
  'validacion': [
   'Bloqueantes: E-05 (ubigeo del establecimiento válido), E-10 (Dx válido y edad de 6-59 m) y E-11 (clave única, año único, Σ filas = filas Hb leídas del crudo).',
   'Avisos: E-06 (procedencia ubicada en 6-35 m, por carga y por departamento, en revision/sien_pn_6_35m_por_departamento.csv), E-07, E-08 (ajuste por altitud y cortes completos, sin NaN, en todo el ZIP) y E-09 (mismos archivos en Hb y en Pt).',
  ],
  'indicadores_piloto': [
   'Proporción de niños tamizados con anemia — ubigeo_eess (D4), denominador filas_dx_valido: «De los niños de 6 a 35 meses a los que se les midió la hemoglobina en 2025 en establecimientos del MINSA y del gobierno regional ubicados en {lugar}, el {x} % tenía anemia en su último control del año. Algunos viven en otros distritos. No es la anemia de todos los niños de {lugar}.»',
   'Cobertura de tamizaje, SOLO departamento (decisión del dueño, 7/10/2026) — cota inferior: procedencia en el departamento; cota superior: procedencia más los niños sin procedencia atendidos en EESS del departamento: «Entre {inf} y {sup} de cada 100 niños de 6 a 35 meses de {departamento} tuvieron al menos una medición de hemoglobina en 2025 en establecimientos del MINSA o del gobierno regional.» Si el intervalo cruza el 50 %: «Con los datos disponibles no podemos decir si la cobertura supera o no la mitad de los niños.» Nota de ficha: la cota superior no es estricta (no cuenta a los niños sin procedencia del departamento atendidos en establecimientos de otros departamentos).',
   'Cobertura de tamizaje por provincia o distrito: no se publica (ni siquiera en Huancavelica y Ayacucho, que superan el 95 % de procedencia ubicada).',
   'Altitud del ajuste — ubigeo_ref_altitud (metadato, no se publica como cifra): «La hemoglobina se corrigió según la altitud del distrito del establecimiento ({altitud} m), no la del lugar de donde procede el niño.»',
   'En la ficha, no en el texto ciudadano: «unidad = un niño con su último control del año (supuesto pendiente de confirmar con el INS)».',
  ],
 },
}
# (regla, texto_anterior, texto_nuevo): como PARCHES_REGLAS, pero después de los agregados
PARCHES_REGLAS_R3 = [('R-REG-07', R_REG_07_COBERTURA_OLA0, R_REG_07_COBERTURA_R3)]

# ---------------------------------------------------------------- ronda 4 (verificación de PARCHES_V3 y de la ronda 3, 7/10/2026)
# Respaldo: auditoria/verificacion_v11_ronda3.json (C-R3-1 a C-R3-6). No cambia ninguna decisión del dueño: solo hace que las
# condiciones digan lo mismo que los enunciados, parámetros y especificaciones de la ronda 3.

# C-R3-1. R-GASTO-02 reescrita entera (GA-09, opción B): sin las cláusulas originales que contradecían el texto de la ronda 3.
CAMPOS_REGLAS += [
 ('R-GASTO-02', 'enunciado',
  'Una inversión del detalle del MEF no se reparte entre distritos en el MVP: se atribuye al menor nivel que contiene '
  'todas sus ubicaciones (distrito, provincia o departamento); si es multidepartamental, su gasto va a '
  'nacional_multidepartamental o se queda en la meta, según la condición. Ningún CUI del detalle se pierde: los '
  '«-MUL.DEP-», los códigos antiguos y los UBIGEO nulos tienen un nivel o un motivo_sin_ubicacion (GA-09; decisión del '
  'dueño del 7/10/2026, opción B).'),
 ('R-GASTO-02', 'condicion',
  'Todo CUI del detalle MEF tiene una fila en dim_inversion_ubicacion con nivel_comun o con motivo_sin_ubicacion (G-10, '
  'bloqueante, conteo exacto). (1) Ubigeos efectivos: UBIGEO válido; código antiguo → alias solo si equivale a un único '
  'distrito (160114 → 160803, confianza alta; 030715 → 030703, media); código escindido (160109, Ley 30186) → tabla '
  'curada inversiones_ubicacion_curada.yaml por CUI o, si no está, la provincia que contiene a todos los sucesores '
  '(160800); UBIGEO con solo departamento → ese departamento. (2) nivel_comun: un distrito → distrito; varios con los '
  'mismos 4 primeros dígitos → provincia; con los mismos 2 → departamento; de varios departamentos o «-MUL.DEP-» '
  '(99xxxx, ubicaciones desconocidas; metodo_ubicacion_cui = multidepartamental_mef) → multidepartamental. (3) UBIGEO '
  'nulo: gobierno local → por nombre contra dim_ubigeo_historico solo si el resultado es único (metodo nombre_texto, '
  'confianza media); si no, motivo ubigeo_nulo_nombre_ambiguo, ubigeo_nulo_nombre_no_resuelto o ubigeo_nulo_sin_texto; '
  'GORE → motivo ubigeo_nulo_texto_gr_no_usado; Gobierno Nacional → motivo ubigeo_nulo_texto_gn_no_fiable (el texto '
  'suele ser la sede). Código que no existe → ubigeo_inexistente. nivel_comun es NULL si y solo si hay '
  'motivo_sin_ubicacion. (4) Atribución del gasto (nivel_atribucion_gasto): distrito → distrito_inversion; provincia → '
  'provincia_inversion; departamento → departamento_inversion (agregar_nivel; nunca se reparte); multidepartamental del '
  'GN o de un GORE → nacional_multidepartamental si la meta está en Lima; si la meta está en otro departamento, se queda '
  'en esa meta (departamento_meta) con el rótulo «proyecto multidepartamental; se muestra la parte registrada en este '
  'departamento»; gasto de una municipalidad → su sede (distrito_municipal o provincia_municipal); con '
  'motivo_sin_ubicacion → la meta (R-GASTO-01). Un CUI del GN o de un GORE con ubicación conocida en otro departamento '
  'que su meta va a nacional_multidepartamental (R-GASTO-01 (b), GA-02); los «-MUL.DEP-» (99xxxx) no entran en esa '
  'regla: siguen este punto (opción B del dueño). (5) El detalle trae una sola fila por CUI (ubicación principal): toda cifra distrital de '
  'inversión es publicar_referencial con el rótulo «ubicación principal registrada; la obra puede abarcar otros '
  'distritos» (parametros.inversion_ubicacion_unica). Pruebas: G-10, G-20 a G-24.'),
 ('R-GASTO-02', 'implementacion',
  'gasto.py (VERSION_TABLA 1.2.0) construye dim_inversion_ubicacion (columnas en especificaciones_capa0.md: cui, '
  'ubigeos, n_ubicaciones, ubicacion_principal, nivel_comun, ubigeo_atribucion, metodo_ubicacion, confianza_ubicacion, '
  'motivo_sin_ubicacion y los textos de origen) y lleva metodo_ubicacion_cui a fact_gasto_territorial. Verificado: '
  'DETALLE_INVERSIONES trae una fila por CUI (ubicación principal), de ahí la cláusula (5).'),
 ('R-GASTO-02', 'ejemplo',
  '[Casos ilustrativos] Un proyecto del GORE Cusco con UBIGEO «-MUL.DEP-» y meta en Cusco se cuenta en Cusco con el '
  'rótulo «proyecto multidepartamental; se muestra la parte registrada en este departamento». Uno del Gobierno Nacional '
  'con «-MUL.DEP-» y meta en Lima va a nacional_multidepartamental. Un CUI con UBIGEO 160109 (código escindido) sin '
  'curar se cuenta en la provincia 160800 (provincia_inversion).'),
 ('R-GASTO-02', 'mensaje_usuario',
  'Varios distritos: «Este proyecto abarca varios distritos; su gasto se cuenta en la provincia (o el departamento) y no '
  'se reparte entre ellos.» Varios departamentos, con meta fuera de Lima: «Proyecto multidepartamental; se muestra la '
  'parte registrada en este departamento.»'),
]

# C-R3-2. R-TERRITORIO-08: la condición recoge la excepción del SIEN.
AGREGADOS_REGLAS_R3 += [
 ('R-TERRITORIO-08', 'condicion',
  ' Excepción SIEN, cobertura de tamizaje de 6-35 m (dueño, 7/10/2026): no se aplica la cascada; p se mide por '
  'departamento del establecimiento sobre ubigeo_procedencia (UbigeoPN) solo como diagnóstico (E-06), y la cobertura se '
  'publica únicamente por departamento con las dos cotas de R-REG-07 (parametros.sien_cobertura_tamizaje), aunque p ≥ '
  '0.95; nunca por provincia ni distrito. La proporción de anemia sigue la cascada sobre ubigeo_eess (D4).'),
 # C-R3-6. El cambio de R-REG-07 se ve en el enunciado (y en reglas.md)
 ('R-REG-07', 'enunciado',
  ' En el SIEN se usa la cobertura de tamizaje de 6-35 m: se publica solo por departamento, con dos cotas (niños '
  'procedentes del departamento y, como cota superior, más los niños sin procedencia atendidos en sus establecimientos), '
  'y se avisa cuando el intervalo cruza el 50 % (decisión del dueño, 7/10/2026).'),
]
# C-R3-3. R-REG-07 y R-CRUCES-09: qué cota se compara y que las bandas de cobertura de registro no se aplican al SIEN.
PARCHES_REGLAS_R3 += [
 # M1: R-GASTO-01 (b) (GA-02) no debe atrapar a los «-MUL.DEP-» (su «departamento» 99 siempre difiere de la meta)
 ('R-GASTO-01', 'difiere de DEPARTAMENTO_META → nacional_multidepartamental (obra que cruza departamentos; no se carga a un distrito ni vuelve a la meta)',
  'difiere de DEPARTAMENTO_META → nacional_multidepartamental (obra que cruza departamentos; no se carga a un distrito ni vuelve a la meta). Excepción: «-MUL.DEP-» (99xxxx, ubicaciones desconocidas) sigue R-GASTO-02 (4): con meta en Lima → nacional_multidepartamental; con meta en otro departamento se queda en la meta, rotulado (opción B del dueño, 7/10/2026)'),
 ('R-REG-07', 'cobertura_registro_estimada (o la de tamizaje en SIEN) por departamento', 'cobertura_registro_estimada por departamento'),
 ('R-REG-07', 'c := cobertura_registro_estimada(fuente, departamento, anio, grupo_edad);',
  'Registros de eventos y vigilancia, salvo el SIEN: c := cobertura_registro_estimada(fuente, departamento, anio, grupo_edad);'),
 ('R-REG-07', 'SIEN: cobertura_tamizaje = evaluados / poblacion_objetivo; < 50 % → publicar_referencial con advertencia de selección',
  'SIEN (cobertura de tamizaje de 6-35 m, solo por departamento; las bandas 60/80/90 no se aplican): cota_inf = niños de '
  '6-35 m con ubigeo_procedencia en el departamento / población de 6-35 m; cota_sup = cota_inf + niños de 6-35 m sin '
  'procedencia atendidos en establecimientos del departamento / población de 6-35 m (parametros.sien_cobertura_cotas); '
  'se publica «entre {inf} y {sup} de cada 100 niños»; cota_sup < sien_umbral_tamizaje_pct → publicar_referencial con '
  'advertencia de selección (la cobertura; la condición vigente no extiende esta marca a la anemia); cota_inf < sien_umbral_tamizaje_pct ≤ '
  'cota_sup → advertir «Con los datos disponibles no podemos decir si la cobertura supera o no la mitad de los niños»; '
  'el semáforo (R-CRUCES-09) usa cota_sup'),
 ('R-CRUCES-09', 'SIEN: tamizaje <50 % → 2', 'SIEN: cota superior de la cobertura de tamizaje (R-REG-07) < 50 % → 2'),
]

# C-R3-5. Diccionario: campos nuevos de R-GASTO-05 v4, R-GASTO-02 y R-REG-07; se retira el nombre viejo.
CAMPOS_R3 = [
 ('categoria_transferencia / excepcion_transferencia', 'cifra', '—',
  'intergubernamental | publico_fuera_de_base | fondo_por_identificar | gasto_final_externo | por_revisar; NULL fuera de la genérica 2.4. excepcion_transferencia: EX-01, EX-02, EX-03 o NULL (R-GASTO-05).'),
 ('bloque_consolidado', 'cifra', '—',
  'gasto_final | excluir_intergubernamental | entregado_fuera_del_presupuesto | posible_doble_conteo_fondo (R-GASTO-05).'),
 ('es_transferencia / es_transferencia_intergub', 'cifra', 'es_transferencia_intergubernamental',
  'es_transferencia = categoría (a), (b) o (b′); es_transferencia_intergub = categoría (a). Evitan el doble conteo (R-GASTO-05).'),
 ('nivel_comun / metodo_ubicacion_cui / motivo_sin_ubicacion', 'cifra', '—',
  'Ubicación de cada CUI en dim_inversion_ubicacion: nivel (distrito, provincia, departamento, multidepartamental o NULL), método y motivo cuando no se ubica (R-GASTO-02).'),
 ('ubigeo_procedencia / cota_inf / cota_sup', 'cifra', 'UbigeoPN',
  'Procedencia del niño en el SIEN y cotas de la cobertura de tamizaje por departamento (R-REG-07, R-TERRITORIO-08).'),
]
CAMPOS_R3_RETIRADOS = ['es_transferencia_intergubernamental']

# C-R3-6. Trazabilidad: hallazgos de la ronda 3 por regla, fecha de actualización y decisiones del dueño en reglas.md.
HALLAZGOS_R3 = {'R-GASTO-05': ['GA-05'], 'R-GASTO-02': ['GA-09'], 'R-TERRITORIO-08': ['SP-03'], 'R-REG-07': ['SP-03'], 'R-CRUCES-09': ['SP-03']}
FECHA_ACTUALIZACION = ('2026-10-07', '7 de octubre de 2026')
DECISIONES_R3 = [  # (id, tema, opciones, recomendación, reglas, decisión)
 ('D12', 'Transferencias (GA-05)', 'Excluir todas las transferencias o separarlas por categoría.', 'Lista curada: (a) fuera de sumas multientidad; (b) bloque aparte; (b′) solo nota; (c) gasto final.', 'R-GASTO-05', 'Adoptada (7/10/2026), con EX-01 y EX-02 en (b); lista con revisado_dueno: false hasta cotejar el Anexo 2.'),
 ('D13', 'CUI sin ubigeo válido (GA-09)', 'A: todo «-MUL.DEP-» a nacional_multidepartamental; B: solo con meta en Lima, el resto en su meta rotulado.', 'B; texto del UBIGEO nulo solo para gobiernos locales.', 'R-GASTO-02', 'Adoptada la opción B (7/10/2026).'),
 ('D14', 'Cobertura de tamizaje del SIEN (SP-03)', 'Por provincia donde la procedencia ubicada supera 95 % o solo por departamento.', 'Solo por departamento, con dos cotas y aviso cuando el intervalo cruza el 50 %.', 'R-TERRITORIO-08, R-REG-07', 'Adoptada (7/10/2026).'),
]

# Guardia: CAMPOS_REGLAS reemplaza campos enteros después de todas las capas (propuestas, prueba, auditoría, renombres,
# POST_RENOMBRE y capas del dueño). Si el campo ya no es el de la propuesta original, la sobrescritura debe estar aquí a
# propósito (consolida_reglas.py falla si no; prueba negativa: reglas/consolidador/pruebas/prueba_guardia.py). Se usa |= para no
# depender del orden de los bloques (la propuesta l_mensajes agrega los suyos).
SOBRESCRITURAS_CONSCIENTES = globals().get('SOBRESCRITURAS_CONSCIENTES', set()) | {
 ('R-GASTO-05', 'mensaje_usuario'),     # ronda 3 (v4) sobre PARCHES_V3 (COM-13); la reescribe l_mensajes
 ('R-DENOMINADORES-01', 'mensaje_usuario'), ('R-DENOMINADORES-02', 'mensaje_usuario'),   # l_mensajes (ronda 4)
 ('R-EST-04', 'mensaje_usuario'), ('R-GASTO-03', 'mensaje_usuario'),                     # l_mensajes (ronda 4)
}

# Auditoría final de la ronda 3 (hallazgo 10): columnas nuevas de dim_inversion_ubicacion y dim_establecimiento_salud
ESPECIFICACIONES_R3['dim_inversion_ubicacion'] = {
 'proposito': 'Ubicación de cada CUI del detalle de inversiones del MEF (R-GASTO-02, GA-09). Una fila por CUI; ninguno se pierde. La construye gasto.py (VERSION_TABLA 1.2.0). Aquí solo las columnas de ubicación; el resto son campos de obra del detalle (GA-10).',
 'columnas': [
  {'columna': 'cui', 'tipo': 'char(7)', 'regla': 'CODIGO_UNICO con ceros a la izquierda. Clave.'},
  {'columna': 'ubigeos, n_ubicaciones, ubicacion_principal', 'tipo': 'text[], int, bool', 'regla': 'Ubigeos efectivos (tras alias, curación o nombre); el detalle trae una sola fila por CUI (ubicación principal).'},
  {'columna': 'nivel_comun', 'tipo': 'text null', 'regla': 'distrito, provincia, departamento o multidepartamental («-MUL.DEP-» / 99xxxx); NULL si y solo si hay motivo_sin_ubicacion.'},
  {'columna': 'ubigeo_atribucion', 'tipo': 'char(6) null', 'regla': 'Ubigeo del nivel_comun (000000 si multidepartamental).'},
  {'columna': 'metodo_ubicacion', 'tipo': 'text', 'regla': 'ubigeo_valido, codigo_antiguo_alias (160114, 030715), curado_por_cui (inversiones_ubicacion_curada.yaml), codigo_escindido_contenedor (160109 → 160800), nombre_texto (UBIGEO nulo de un GL, nombre único), multidepartamental_mef o sin_ubicacion.'},
  {'columna': 'confianza_ubicacion', 'tipo': 'text', 'regla': 'alta, media o baja según el método.'},
  {'columna': 'motivo_sin_ubicacion', 'tipo': 'text null', 'regla': 'ubigeo_nulo_texto_gn_no_fiable, ubigeo_nulo_texto_gr_no_usado, ubigeo_nulo_sin_texto, ubigeo_nulo_nombre_ambiguo, ubigeo_nulo_nombre_no_resuelto o ubigeo_inexistente.'},
  {'columna': 'ubigeo_fuente, departamento_txt, provincia_txt, distrito_txt', 'tipo': 'text', 'regla': 'UBIGEO y textos tal como vienen en el detalle (trazabilidad).'},
 ],
 'fact_gasto_territorial': 'Columnas nuevas (1.2.0): metodo_ubicacion_cui (GA-09); categoria_transferencia, es_transferencia_intergub y bloque_consolidado (GA-05, R-GASTO-05 v4). La clave usa categoria_transferencia en lugar de es_transferencia.',
}
ESPECIFICACIONES_R3['dim_establecimiento_salud'] = {
 'proposito': 'Establecimientos de RENIPRESS con ubigeo INEI (puentes.py, VERSION_TABLA 1.2.0). Columnas nuevas de la ronda 3 (GA-09).',
 'columnas': [
  {'columna': 'ubigeo_fuente', 'tipo': 'char(6)', 'regla': 'UBIGEO tal como viene en RENIPRESS.'},
  {'columna': 'ubigeo_inei', 'tipo': 'char(6)', 'regla': 'Distrito vigente; para un código escindido no curado, la provincia contenedora (ubigeo_valido = False).'},
  {'columna': 'metodo_ubigeo', 'tipo': 'text', 'regla': 'fuente, codigo_antiguo_alias (solo códigos que equivalen a un distrito, p. ej. 160114), curado (renipress_ubicacion_curada.yaml) o codigo_escindido_contenedor (160109 → 160800).'},
  {'columna': 'evidencia_ubigeo', 'tipo': 'text null', 'regla': 'Evidencia de la curación (dirección, coordenadas, vecinos), solo si metodo_ubigeo = curado.'},
 ],
}

# ================================================================ ronda 4 · l_mensajes (v3, mensajes al usuario, 7/10/2026)
# Bloque propio de la propuesta l_mensajes (pendiente 2 de la auditoría, COM-13), corregido tras la auditoría independiente
# r4/aud_mensajes (M1-M8). Solo toca mensaje_usuario, el detector de mensajes, su lista de jerga y los avisos del corrector.
# Decisiones del orquestador (7/10/2026): cada «…» se mide aparte; se renombran marcadores y se corrige el detector; se amplía
# la lista de jerga; los 3 patrones ajustados del auditor entran solo como aviso; las comparaciones sin base no tienen patrón.

# -- 4.1 Los 5 mensajes que marcaba el detector anterior. Marcadores renombrados: {nombre_denominador} → {poblacion_base},
#    {fuente_denominador} → {fuente_poblacion}, {vintage_legible} → {edicion_poblacion}, {año} → {anio}.
CAMPOS_REGLAS += [
 # R-GASTO-05 (redefine la entrada de la ronda 3): cada «…» aparte; sin «por eso» ni «millones» fijo; {detalle_c}; nota fija solo entre entidades del presupuesto; variante sin {principal} (M6)
 ('R-GASTO-05', 'mensaje_usuario',
  'Cifra temática: «Esta cifra no incluye S/ {b} que {entidad} entregó a fondos y entidades públicas que no están '
  'en el presupuesto (por ejemplo, {principal}).» Si no se conoce el receptor principal: «Esta cifra no incluye S/ '
  '{b} que {entidad} entregó a fondos y entidades públicas que no están en el presupuesto.» Consolidado, en dos '
  'líneas que no se suman: «Gastado por las entidades del presupuesto: S/ {gasto_final}» y «Entregado a fondos y '
  'entidades públicas fuera del presupuesto: S/ {b}». Nota fija: «Cuando una entidad del presupuesto transfiere '
  'dinero a otra entidad del presupuesto, solo contamos el gasto de quien lo recibe, para no contarlo dos veces.» '
  'Fondos (b′), si existen en el año: «Además, S/ {f} fueron a fondos que aún no sabemos en qué se usaron. No los '
  'sumamos: podrían volver a aparecer como gasto de otra entidad.» (c), cuando pesa: «Incluye S/ {c} pagados a '
  'organismos internacionales: {detalle_c}.»'),
 ('R-DENOMINADORES-01', 'mensaje_usuario',
  'Calculado sobre la población {poblacion_base} ({fuente_poblacion}, {anio}).'),
 ('R-DENOMINADORES-02', 'mensaje_usuario',
  'Para todos los años usamos la misma estimación de población ({edicion_poblacion}). Así, un cambio de fuente no '
  'altera la comparación entre años.'),
 ('R-EST-04', 'mensaje_usuario',
  'Cuántas personas deberían recibir este programa es una estimación ({fuente_poblacion}, {anio}), no un conteo. '
  'Con ella, los usuarios equivalen a entre {cob_inf} % y {cob_sup} % de esa población.'),
 # R-GASTO-03 (M1): lo ubicable incluye proyectos de cualquier entidad (en Huancavelica 2025, 113,8 de 116,5 millones son del GORE); lo que falta es el gasto en servicios
 ('R-GASTO-03', 'mensaje_usuario',
  'Incluye el gasto de la municipalidad y de los proyectos de inversión ubicados aquí, de cualquier entidad. No '
  'incluye lo que el ministerio y el gobierno regional gastan en servicios (como personal de salud). En '
  '{departamento}, el {pct} % del gasto en este tema puede ubicarse por distrito o provincia.'),
]
# -- 4.2 Los 10 mensajes con jerga que el detector anterior no veía. Marcadores nuevos: {quien} y {accion_registro} (R-REG-01),
#    {nivel_referencia} (R-REG-06), {nivel_mostrado} (R-ENC-16), {mayor_menor} (R-DENOMINADORES-04), {fecha_corte_gasto}
#    (R-GASTO-14) y {ciudades} (R-ENC-08). Los textos entre «» con un caso entre paréntesis se muestran solo en ese caso.
CAMPOS_REGLAS += [
 # M5: censo + estimación de omisión; sentido de la diferencia
 ('R-DENOMINADORES-04', 'mensaje_usuario',
  'Esta cifra usa la población del distrito de {distrito} que el INEI calculó a partir del Censo 2017. Con el Censo '
  '2025, más una estimación de las personas que el censo no llegó a contar, esa población es {pct} % {mayor_menor}. Cuando el INEI '
  'publique sus nuevas estimaciones, recalcularemos la cifra.'),
 # M2: ENSUSALUD también entrevista al personal; texto para «ciudades estudiadas»
 ('R-ENC-08', 'mensaje_usuario',
  '«Por ahora solo mostramos la cifra nacional de esta encuesta. Todavía no hemos comprobado, en su ficha técnica, '
  'si alcanza para dar cifras por departamento.» (usuarios de servicios, p. ej. ENSUSALUD) «Esta encuesta '
  'entrevista a usuarios de servicios de salud y a su personal, no a toda la población.» (ciudades estudiadas) '
  '«Esta encuesta solo se hizo en algunas ciudades ({ciudades}); no describe al resto del país.»'),
 # M8: lugares o años
 ('R-REG-15', 'mensaje_usuario',
  'Algunos lugares o años tienen más personas mayores que otros. Para compararlos de forma justa, calculamos la '
  'tasa como si todos tuvieran las mismas edades que el Perú en el Censo 2017. Sirve para comparar, no para saber '
  'cuántos casos hubo.'),
 ('R-GASTO-10', 'mensaje_usuario',
  'Es una estimación del MEF, no un gasto registrado aparte. Suma lo que se gastó solo en niñas, niños y '
  'adolescentes y una parte de lo que se gastó para toda la población (por ejemplo, en salud), repartida según la '
  'edad de la población del Censo 2017.'),
 ('R-GASTO-15', 'mensaje_usuario',
  'Estos datos muestran cuánto se gastó, no si el gasto fue eficiente ni si produjo los cambios en {indicador}. '
  'Para saberlo se necesita una evaluación que compare con lo que habría pasado sin ese gasto.'),
 # M7
 ('R-REG-01', 'mensaje_usuario',
  'Este dato cuenta solo a {quien} que {accion_registro} {sistema}; no mide a toda la población. Quien no quedó '
  'registrado ahí no aparece en la cifra.'),
 # M4: la frase de la ENDES solo para mortalidad infantil o neonatal; «mayor o menor»
 ('R-REG-04', 'mensaje_usuario',
  '«Esta cifra solo cuenta los nacimientos y las muertes que quedaron registrados en los sistemas del MINSA. Como '
  'no todos se registran, la cifra real puede ser distinta.» (mortalidad infantil o neonatal) «La cifra oficial del '
  'país la estima el INEI con su encuesta de salud (ENDES).» (mortalidad materna) «El MINSA hace seguimiento de cada '
  'muerte materna y publica el número de casos del país.»'),
 # M3: devengado ≠ pagado; fecha de corte del gasto
 ('R-GASTO-14', 'mensaje_usuario',
  'La entidad informa que la obra avanzó {avance_fisico} % (dato al {fecha}). Al {fecha_corte_gasto}, ya se gastó '
  '(devengado) el {avance_financiero} % de lo que hoy cuesta la obra. Las dos cifras no tienen por qué coincidir: '
  'puede haberse gastado más de lo construido, o menos.'),
 ('R-REG-06', 'mensaje_usuario',
  'En un distrito pequeño, uno o dos casos cambian mucho la tasa. Para evitar valores extremos por azar, la '
  'acercamos al promedio de {nivel_referencia}: cuantos menos habitantes, más se acerca. Es un cálculo nuestro, no '
  'una cifra oficial; al lado va la cifra sin ajustar.'),
 # M8: caso de 10 a 19 evaluados y fin de la ECE en 2019
 ('R-ENC-16', 'mensaje_usuario',
  '(menos de 10) «En esta escuela solo se evaluó a {n} estudiantes: con tan pocos, uno o dos alumnos cambian mucho '
  'el porcentaje. Mostramos el resultado de {nivel_mostrado}.» (10 a 19) «En esta escuela se evaluó a {n} '
  'estudiantes: la cifra es aproximada, porque uno o dos alumnos pueden cambiarla bastante.» (siempre) «La prueba '
  'que se tomaba en todas las escuelas (ECE) llegó hasta 2019; no comparamos esos resultados con pruebas '
  'posteriores en cada escuela o distrito.»'),
]
# -- 4.3 Sobrescrituras conscientes (guardia de v_parches_v3, si está aplicada; funciona con o sin ella).
SOBRESCRITURAS_CONSCIENTES = globals().get('SOBRESCRITURAS_CONSCIENTES', set()) | {
 (r_, 'mensaje_usuario') for r_ in ['R-GASTO-05', 'R-DENOMINADORES-01', 'R-DENOMINADORES-02', 'R-EST-04', 'R-GASTO-03', 'R-DENOMINADORES-04', 'R-ENC-08', 'R-REG-15', 'R-GASTO-10', 'R-GASTO-15', 'R-REG-01', 'R-REG-04', 'R-GASTO-14', 'R-REG-06', 'R-ENC-16']}

# -- 4.4 Detector de mensajes (lo usa consolida_reglas.py): sin distinguir mayúsculas, sin mirar nombres de marcadores, cada «…»
#    por separado. BASE = la lista anterior con \b bien escrito; AMPLIADA = 6 términos de la ronda 4 (con plural) y los escapes
#    de la auditoría r4 (intervalo de confianza, estandarizada, prorrateo, factor de expansión, p-valor, CIE-10, persona-tiempo,
#    PPoR, GEO2017, bayesiano, DEPARTAMENTO_META).
JERGA_MENSAJES_BASE = r'significativ|margen de error|±|\bCV\b|\bIC\b|denominador|ubigeo|vintage|punto de corte|\bRM\b'
JERGA_MENSAJES_AMPLIADA = (r'omisi[óo]n censal|representativ|ajustad\w* por edad|evaluaci\w* de impacto|pesos por edad|registros? administrativ\w*'
                           r'|intervalo\w* de confianza|estandarizad\w*|prorrateo|factor\w* de expansi|p-valor|\bCIE-10\b|persona-tiempo|\bPPoR\b|\bGEO2017\b|bayes|departamento_meta')
JERGA_MENSAJES = JERGA_MENSAJES_BASE + '|' + JERGA_MENSAJES_AMPLIADA
MENSAJES_MAX_CARACTERES = 300

# -- 4.5 Avisos del corrector (no bloquean). consolida_reglas.py los publica en lenguaje.avisos_pendientes_validacion y los
#    prueba contra los mensajes vigentes y el corpus de la ronda 4. Pasan a bloquear solo tras validarlos con un corpus de terceros.
AVISOS_CORRECTOR = {'estado': 'pendiente validación por terceros',
 'efecto': 'aviso: se informa, no bloquea la consolidación ni la respuesta',
 'origen': 'auditoría independiente r4 (aud_mensajes/patrones_ajustados.json); decisión del orquestador 7/10/2026',
 'normalizar': True,
 'patrones': {'causal (ampliación, ajustado)': '\\bexplica(n|ria|rian)? (por que|(buena |gran |la mayor )?parte '
                                               'de|(el|la|los|las) '
                                               '(menor|mayor|baja|alta|caida|reduccion|aumento|mejora|disminucion|descenso))\\b|\\bdesde '
                                               'que (llego|llegaron|se (implemento|aplico))\\b|\\b(desde|con|tras) '
                                               'la (llegada|implementacion|puesta en marcha) de',
              'precisión excesiva (ajustado)': '\\d,\\d{3,}|\\d[.,]\\d{2,} ?(%|por ciento)|s/ ?\\d[\\d ]*,\\d{2,}',
              'juicio de valor (ampliación, ajustado)': '\\b(mala|buena|pesima|peor|mejor)s? ejecutora|(?:^|[.;:]) '
                                                        '?(?![^.;:]*\\bsi\\b)[^.;:]*\\b(gasta|gastan|ejecuta|ejecutan) '
                                                        '(muy )?(mal|bien)\\b|\\b(baja|alta|poca|mucha|buena|mala) '
                                                        'capacidad de gasto\\b'}}


# ---------------------------------------------------------------- auditoría final de la ronda 4 (7/10/2026)
# F7: un solo formato de comillas en los mensajes (lo aplica consolida_reglas.py; una prueba de consistencia impide que
# vuelvan las comillas simples). 'textos': cada '…' es un texto que ve el usuario → «…». 'terminos': '…' cita una palabra
# dentro de un texto → “…”.
COMILLAS_R4 = {
 'textos': ['R-ENC-06', 'R-ENC-07', 'R-ENC-09', 'R-ENC-15', 'R-ENC-02', 'R-ENC-03', 'R-ENC-04', 'R-ENC-05', 'R-ENC-10',
            'R-ENC-17', 'R-ENC-13', 'R-ENC-14', 'R-ENC-11', 'R-ENC-12'],
 'terminos': ['R-TERRITORIO-06', 'R-REG-05', 'R-GASTO-06', 'R-CRUCES-07'],
}
# M4 (aud_mensajes) / F7: para la RMM la referencia es la vigilancia del MINSA (CDC), no la ENDES. Se AGREGA a referencias.
REFERENCIAS_R4 = [
 ('R-REG-04', {'titulo': 'MINSA, CDC – Sala situacional de muerte materna (vigilancia epidemiológica; catálogo: CDC-SALA-MUERTE-MATERNA)',
               'url': 'https://www.dge.gob.pe/sala-situacional-muerte-materna/'}),
]


# ================================================================ decisiones del gasto, rondas 1–2 (pieza B: reglas)
# Aprobadas por el dueño el 7/10/2026 (docs/decisiones.md; 03_auditoria/ola0/decisiones_gasto/ronda2/README.md,
# decisiones 1–3, 5, 9, 10 y 11; ronda 1: decisiones_gasto_piloto.md, decisiones 1 y 3). Implementación: 8/10/2026;
# informe en 03_auditoria/ola0/decisiones_gasto/implementacion/pieza_b/implementacion.md. Reglas nuevas: R-GASTO-08b y
# R-GASTO-18 a 21 (NUEVAS_GASTO_R2, ETAPAS_GASTO_R2). Cambios: R-GASTO-05 (compatible con la v4 de la ronda 3), 07, 08, 09
# y 15 (CAMPOS_REGLAS y PARCHES_REGLAS_R3); patrones nuevos del corrector (PROHIBIDAS_GASTO_R2).
_R2 = '03_auditoria/ola0/decisiones_gasto/'
def _ref(titulo, ruta): return {'titulo': 'Pregunta al Perú – ' + titulo, 'url': None, 'ruta': _R2 + ruta}
REF_R2 = _ref('Decisiones del gasto, ronda 2 (aprobadas por el dueño el 7/10/2026)', 'ronda2/README.md')
REF_W4_REGLAS = _ref('Reglas propuestas v2 (W4, glosario y transferencias)', 'ronda2/w4_glosario_transferencias/reglas_propuestas_v2.csv')
REF_TRANSF = _ref('Transferencias, dinero que llega tarde y ejecución (v2)', 'ronda2/w4_glosario_transferencias/transferencias_v2.md')
REF_GLOS = _ref('Glosario del gasto público v2 (§2: programa frente a función)', 'ronda2/w4_glosario_transferencias/glosario_v2.md')
REF_AUD_GLOS = _ref('Auditoría independiente del glosario y las transferencias (ronda 2)', 'ronda2/aud_glosario/auditoria.md')
REF_W2 = _ref('Capa de trazabilidad de programas presupuestales y sociales (W2 v2)', 'ronda2/w2_trazabilidad/informe_v2.md')
REF_AUD_TRAZ = _ref('Auditoría independiente de la trazabilidad (ronda 2)', 'ronda2/aud_trazabilidad/auditoria.md')
REF_R1 = _ref('Decisiones del gasto, ronda 1 (piloto)', 'decisiones_gasto_piloto.md')
REF_TEMA = _ref('Propuesta dim_tema_gasto v1.2', 'tema_gasto/propuesta_dim_tema_gasto_v1_2.csv')
_GASTO_AA = {'naturaleza_dato': ['presupuestal_financiero'], 'tipo_medida': ['presupuesto_gasto'], 'base_geografica': [],
             'fuentes': ['MEF-DA-PRESUPUESTO-EJECUCION-GASTO']}
_PRE_DATOS = ('Datos (ronda 2, PRE-DATOS-01): fact_gasto_territorial ya trae actividad_accion_obra, fuente_financiamiento, '
              'rubro, grupo_funcional y clasificador_gasto (pieza A, 8/10/2026); el primer mes con devengado de cada línea se '
              'deriva de la columna mes. Si una de esas columnas falta para un año, la regla no se evalúa y la cifra que la '
              'necesita no se publica.')
GRAMATICA_TEMAS = r'^(fun|div|pp|ppxfun|cpt|ps)_[0-9a-z_]+$'
TEMAS_V12 = {  # glosario_v2.md §2.5 (ids, cadena, código de origen y etiqueta ciudadana)
 'fun_salud': ('funcion', 'SALUD', 'Gasto en el sector salud', None),
 'fun_saneamiento': ('funcion', 'SANEAMIENTO', 'Gasto en el sector saneamiento', None),
 'div_educacion_basica': ('division', 'EDUCACION / EDUCACION BASICA', 'Gasto en educación básica (subsector)', None),
 'fun_proteccion_social': ('funcion', 'PROTECCION SOCIAL', 'Gasto en el sector protección social', None),
 'pp_0082_0083_agua_saneamiento': ('programa', '0082, 0083', 'Programas de agua y saneamiento urbano y rural', None),
 'pp_0002_materno_neonatal': ('programa', '0002', 'Programa Salud Materno Neonatal', None),
 'pp_0090_logros_aprendizaje': ('programa', '0090', 'Programa de logros de aprendizaje (incluye sueldos docentes)', None),
 'pp_0150_acceso_educacion': ('programa', '0150', 'Programa de acceso a la educación básica', None),
 'pp_1001_dit': ('programa', '1001', 'Programa de Desarrollo Infantil Temprano completo (incluye Cuna Más)', None),
 'ppxfun_1001_salud': ('programa_x_funcion', '1001 × SALUD', 'Parte de salud del programa DIT (incluye proyectos de hospitales)', None),
 'ppxfun_1001_proteccion_social': ('programa_x_funcion', '1001 × PROTECCION SOCIAL', 'Parte de protección social del programa DIT: Cuna Más (cuidado diurno y acompañamiento familiar)', None),
 'ppxfun_1001_educacion': ('programa_x_funcion', '1001 × EDUCACION', 'Parte de educación del programa DIT (cuidado diurno registrado en educación)', None),
 'cpt_grupo_expan': ('concepto', 'grupo_expan (w2)', 'Servicios de salud y nutrición infantil que antes eran del PAN', None),
 'cpt_grupo_opcion_c': ('concepto', 'grupo_opcion_c (w2)', 'Los mismos servicios, solo dentro del PP 1001', 'cpt_grupo_expan'),
 'cpt_grupo_anemia_estricta': ('concepto', 'grupo_anemia_estricta (w2)', 'Hierro y atención de la anemia', 'cpt_grupo_expan'),
}
TEMAS_V12 = {k: dict(cadena=a, codigo_origen=b, etiqueta_ciudadana=c, alternativa_de=d) for k, (a, b, c, d) in TEMAS_V12.items()}
MAP_INTENCION_TEMA = {  # glosario_v2.md §2.3; ex-PAN según la decisión 3 de la ronda 2 (serie por concepto; opción C como desglose)
 'sector salud': {'defecto': 'fun_salud', 'contexto': []},
 'educación básica': {'defecto': 'div_educacion_basica', 'contexto': ['pp_0090_logros_aprendizaje']},
 'saneamiento / agua': {'defecto': 'fun_saneamiento', 'contexto': ['pp_0082_0083_agua_saneamiento']},
 'programa DIT / primera infancia': {'defecto': 'pp_1001_dit', 'contexto': ['ppxfun_1001_salud', 'ppxfun_1001_proteccion_social', 'ppxfun_1001_educacion']},
 'PAN / anemia / desnutrición': {'defecto': 'cpt_grupo_expan', 'desglose': 'cpt_grupo_opcion_c', 'contexto': ['cpt_grupo_anemia_estricta', 'pp_1001_dit']},
 'salud materna': {'defecto': 'pp_0002_materno_neonatal', 'contexto': ['fun_salud']},
 'programas sociales': {'defecto': 'ps_* (dim_programa_social)', 'contexto': ['fun_proteccion_social']},
}
NUEVAS_GASTO_R2 = [
 dict(id='R-GASTO-08b', ambito='gasto', titulo='Una cadena por cifra',
  enunciado=('Toda cifra de gasto declara de qué cadena sale: la funcional (una función o una división funcional), la '
   'programática (uno o varios programas presupuestales), el cruce programa × función, un grupo de conceptos estables o un '
   'programa social. Los temas de dim_tema_gasto llevan el prefijo de su cadena: fun_ (función), div_ (división funcional), '
   'pp_ (programa), ppxfun_ (un programa leído por función), cpt_ (grupo de conceptos estables) y ps_ (programa social). '
   'Cifras de cadenas distintas nunca se suman, restan ni promedian: los conceptos, los programas sociales y los temas por '
   'función son alcances distintos y no se suman entre sí. La cadena de cada pregunta la fija la tabla map_intencion_tema, '
   'no el LLM.'),
  aplica_a=dict(_GASTO_AA),
  condicion=('(1) tema_id cumple la gramática y su prefijo corresponde a tema.cadena ∈ {funcion, division, programa, '
   'programa_x_funcion, concepto, programa_social}; si no, la construcción de dim_tema_gasto falla y la cifra temática se '
   'bloquea. (2) Operación entre dos cifras (suma, resta, promedio, cociente o «X % de») con cadena distinta → bloquear_cruce. '
   'Única excepción al cociente: la fila ppxfun_ (calculada sobre las mismas filas que su programa), rotulada como cruce. '
   '(3) Dos cadenas en una misma respuesta → oraciones separadas, cada una con su rótulo, más la frase fija. (4) Series, '
   'rankings y comparaciones entre territorios → una sola cadena y la misma versión de dim_tema_gasto en todos los años '
   '(R-GASTO-09). (5) tema := map_intencion_tema[intencion_pregunta].defecto; los temas de contexto o de desglose van en '
   'una línea aparte y no se suman al principal. (6) Prueba bloqueante de no superposición (G-03, todos los alcances): '
   'dentro de una cadena cada sol de la fact pertenece como máximo a un tema; quedan fuera de la prueba los pares marcados '
   'con alternativa_de (lecturas alternativas del mismo gasto), que tampoco se suman entre sí.'),
  accion='bloquear_cruce',
  parametros={
   'gramatica_id': GRAMATICA_TEMAS,
   'prefijo_cadena': {'fun': 'funcion', 'div': 'division', 'pp': 'programa', 'ppxfun': 'programa_x_funcion', 'cpt': 'concepto', 'ps': 'programa_social'},
   'columnas_dim_tema_gasto': ['cadena', 'codigo_origen', 'nivel', 'llave_union', 'alternativa_de', 'etiqueta_ciudadana'],
   'map_intencion_tema': MAP_INTENCION_TEMA,
   'alternativas': {'cpt_grupo_opcion_c': 'cpt_grupo_expan', 'cpt_grupo_anemia_estricta': 'cpt_grupo_expan'},
   'frase_fija_dos_cadenas': 'Son dos formas de ordenar el mismo gasto; no se suman.',
   'vocabulario_redactor': {
    'funcion / division': {'formula': '«gasto en el sector salud (todo lo que el Estado clasifica como salud)»; «en educación básica (subsector)»', 'prohibido': ['programa de salud', 'gasto contra la anemia']},
    'programa': {'formula': '«gasto del programa de Desarrollo Infantil Temprano»', 'prohibido': ['gasto en salud infantil (incluye Cuna Más)']},
    'programa_x_funcion': {'formula': '«la parte de salud del programa de Desarrollo Infantil Temprano»', 'prohibido': ['gasto de salud del DIT, sin la palabra «parte»']},
    'concepto': {'formula': '«servicios de salud y nutrición infantil que antes eran del PAN»', 'prohibido': ['todo el gasto en anemia']}}},
  mensaje_usuario='Son dos formas de ordenar el mismo gasto; no se suman.',
  justificacion=('El programa y la función son dos cadenas que se cruzan: en 2025 la función salud suma 30 524 millones y el '
   '63 % no está en ningún programa presupuestal; el PP 1001 suma 3 867 y se reparte en salud (2 708), protección social '
   '(1 044) y educación (115). Con un mismo nombre en dos cadenas (agua_saneamiento) se sumaba dos veces el mismo sol: '
   '4 920 + 5 834 (2025, sin transferencias). «Núcleo» y «amplio» sugerían que uno está dentro del otro, y no es así.'),
  referencias=[REF_R2, REF_GLOS, REF_W4_REGLAS, REF_AUD_GLOS, REF_R1],
  hallazgos_auditoria=[], hallazgos_prueba=[],
  ejemplo=('GORE Huancavelica 2023: «gastó S/ 329 millones en el sector salud, el 92 % de su presupuesto final» (fun_salud) y, '
   'en otra oración, «en el programa de Desarrollo Infantil Temprano gastó el 82 % de S/ 113 millones» (pp_1001_dit), '
   'seguido de «Son dos formas de ordenar el mismo gasto; no se suman». Inválido: «el DIT es el 32 % de su gasto en salud».'),
  implementacion=('dim_tema_gasto v1.2 (capa 0) lleva las columnas de columnas_dim_tema_gasto; la construcción valida la '
   'gramática y la prueba G-03 de no superposición para todos los alcances (función, programa, cruce, conceptos y programas '
   'sociales). Cada cifra temática lleva tema_id y cadena en sus metadatos y se lee con la macro gasto_tema(\'<tema_id>\'), '
   'una llamada por consulta (guardia G4 en src/pap/capa0/guardia_gasto.py), así que dos temas no se combinan '
   'en una misma consulta; el validador rechaza toda operación entre cifras '
   'de cadena distinta. Los temas cpt_ apuntan a rel_concepto_grupo y rel_concepto_nodo; los ps_, a dim_programa_social.'),
  casos_borde=('La fila ppxfun_ es la única forma de decir «qué parte del programa es salud». cpt_grupo_opcion_c y '
   'cpt_grupo_anemia_estricta son lecturas alternativas de cpt_grupo_expan: se pueden mostrar como desglose, nunca sumadas. '
   'El gasto de acciones centrales y APNOP sin tema (cerca de la mitad del total) se declara, no se reparte entre temas. '
   'Los programas sociales se definen por ejecutora y actividad, no por programa presupuestal.'),
  prioridad='mvp', decisiones_gasto_r2=['ronda 2, decisión 9', 'ronda 2, decisión 3', 'ronda 1, decisión 3']),
]
NUEVAS_GASTO_R2 += [
 dict(id='R-GASTO-18', ambito='gasto', titulo='Cambio neto del presupuesto en el año',
  enunciado=('Toda cifra de avance de ejecución de una entidad en un tema muestra el presupuesto inicial (PIA), el final '
   '(PIM), el cambio neto en el año (PIM − PIA, con su monto), el devengado y el avance (devengado / PIM). El mensaje usa '
   'una sola medida, el cambio neto, también cuando el presupuesto bajó, y compara lo no ejecutado con el aumento. No se '
   'publica la «ejecución de lo añadido» como un valor único.'),
  aplica_a=dict(_GASTO_AA),
  condicion=('neto := PIM − PIA de la entidad × tema (mes 0; año cerrado o última descarga). no_ej := PIM − devengado. '
   'neto > 0 → texto (a) y, si no_ej ≤ neto, «menos»; si no_ej > neto, «más». neto < 0 → texto (b) con el monto de la '
   'reducción. neto = 0 → sin texto. Pedido de «cuánto de lo añadido se gastó» → solo un rango con las cotas «PIA '
   'primero» y «añadido primero» por pliego × fuente, rotulado como estimación; nunca un valor único. La cifra se calcula '
   'sobre la base por entidad × tema, no sobre la fact actual.'),
  accion='rotular',
  parametros={'medida': 'cambio_neto = PIM − PIA (entidad × tema)', 'casos': ['PIM > PIA', 'PIM < PIA', 'PIM = PIA'],
   'fuente_calculo': 'base por entidad × tema (no la fact actual)',
   'rango_opcional': 'cotas pia_primero / anadido_primero por pliego × fuente, rotuladas como estimación',
   'requiere': ['fuente_financiamiento', 'actividad_accion_obra', 'grupo_funcional']},
  mensaje_usuario=('(si aumentó) «Empezó el año con S/ {pia}; durante el año su presupuesto aumentó en S/ {neto}. Gastó '
   'S/ {dev}, el {avance} % del presupuesto final.» «Lo que no se gastó (S/ {no_ej}) es {menos_o_mas} que lo que se añadió '
   'en el año.» (si bajó) «Durante el año su presupuesto se redujo en S/ {reduccion}.»'),
  justificacion=('El PIM cambia durante el año: en los GORE, las líneas sin PIA son el 19–22 % del PIM y se ejecutan al '
   '80–91 %, frente al 95–98 % de las que tenían PIA. Sin el cambio neto, un avance bajo se lee como mala gestión. Medir '
   'qué parte de lo no ejecutado se explica por lo añadido da entre 11 % y 80 % según el método: no hay una cifra única '
   'honesta, por eso solo se da como rango.'),
  referencias=[REF_R2, REF_TRANSF, REF_W4_REGLAS, REF_AUD_GLOS],
  hallazgos_auditoria=[], hallazgos_prueba=[],
  ejemplo=('GORE Cajamarca, sector salud, 2023: «Empezó el año con S/ 740 millones; durante el año su presupuesto aumentó '
   'en S/ 309 millones. Gastó S/ 957 millones, el 91 % del presupuesto final. Lo que no se gastó (S/ 91 millones) es menos '
   'que lo que se añadió en el año.»'),
  implementacion=('Vista de ejecución por entidad × tema con PIA y PIM del mes 0 y devengado de los meses 1–12. ' + _PRE_DATOS +
   ' Se aplica junto con R-GASTO-07 (avance) y R-GASTO-19 (gasto que empezó tarde).'),
  casos_borde=('PIM = PIA no lleva texto. Una línea nueva puede ser dinero de fuera o una reasignación interna: la medida es '
   'el cambio neto de la entidad × tema, no la suma de líneas sin PIA. Un PIM menor que el PIA se informa con el mismo peso '
   'que un aumento.'),
  prioridad='mvp', decisiones_gasto_r2=['ronda 2, decisión 10']),
 dict(id='R-GASTO-19', ambito='gasto', titulo='Aviso de gasto que empezó tarde',
  enunciado=('Solo en años cerrados: si una parte importante de lo no ejecutado está en líneas que no tenían presupuesto '
   'inicial y que empezaron a gastarse entre octubre y diciembre (o no se gastaron), se avisa que parte del presupuesto se '
   'asignó durante el año y empezó a gastarse tarde. No se dice cuándo llegó el dinero: la base no lo permite.'),
  aplica_a=dict(_GASTO_AA),
  condicion=('anio_cerrado = false → no se evalúa. Línea := llave_linea. pista := líneas con PIA = 0 y (primer mes con '
   'devengado ∈ {10, 11, 12} o sin devengado). Si Σ (PIM − devengado) de la pista ≥ umbral_pct_no_ejecutado × Σ (PIM − '
   'devengado) de la entidad × tema → advertir con el mensaje. Afirmar «llegó en el último trimestre» o una fecha → solo '
   'con dim_modificacion_presupuestaria o con la serie propia de fotos mensuales del PIM; si no, bloquear esa frase.'),
  accion='advertir',
  parametros={'solo_anio_cerrado': True,
   'llave_linea': 'sec_ejec + programa + producto + actividad + funcion + division + grupo + departamento_meta + fuente + generica',
   'umbral_pct_no_ejecutado': 0.25,
   'fecha_de_llegada': 'solo con dim_modificacion_presupuestaria o fotos mensuales del PIM (desde 2026)'},
  mensaje_usuario=('Parte de este presupuesto se asignó durante el año y empezó a gastarse recién en los últimos meses (o '
   'no llegó a gastarse). No sabemos en qué fecha llegó.'),
  justificacion=('El PIA y el PIM son una sola cifra anual y solo el devengado es mensual: la base no dice cuándo llegó el '
   'dinero. El primer mes con devengado de una línea nueva es solo una pista; por eso se avisa sin fechar ni culpar. Caso '
   'real: el DS 243-2024-EF (28/11/2024) llevó 43,8 millones del FED a 25 GORE en diciembre.'),
  referencias=[REF_R2, REF_TRANSF, REF_W4_REGLAS, REF_AUD_GLOS],
  hallazgos_auditoria=[], hallazgos_prueba=[],
  ejemplo=('GORE La Libertad, sector salud, 2024 (sin tabla de modificaciones): «Una parte de este presupuesto se asignó '
   'durante el año y empezó a gastarse recién entre octubre y diciembre: S/ 37 millones, de los que se gastaron S/ 32 '
   'millones. No sabemos en qué fecha llegó cada aumento.»'),
  implementacion=_PRE_DATOS + ' El primer mes con devengado por línea se calcula de los meses 1–12 de la base.',
  casos_borde=('Año en curso: no se evalúa. La pista no es un umbral sobre el PIM total. Una línea sin PIA puede ser una '
   'reasignación interna: el texto dice «se asignó», no «se añadió». No se usa para excusar a la entidad (R-GASTO-15).'),
  prioridad='mvp', decisiones_gasto_r2=['ronda 2, decisión 10']),
]
NUEVAS_GASTO_R2 += [
 dict(id='R-GASTO-20', ambito='gasto', titulo='Lo no ejecutado es crédito, no caja',
  enunciado=('Lo que no se ejecutó de un presupuesto es una autorización de gasto que no se usó, no dinero en caja. Se '
   'desglosa por fuente de financiamiento y por tipo (actividades o proyectos). De recursos ordinarios se dice que ese '
   'presupuesto no puede usarse el año siguiente; de otras fuentes, que podría incorporarse al año siguiente si el dinero se '
   'recaudó o se recibió. Nunca se dice que el dinero «sobró», «se devolvió» o «se perdió».'),
  aplica_a=dict(_GASTO_AA),
  condicion=('no_ej := PIM − devengado (año cerrado) por fuente_financiamiento (recursos ordinarios frente al resto) y por '
   'tipo (actividad o proyecto). Recursos ordinarios → texto «no puede usarse el año siguiente». Otras fuentes → texto '
   'condicional «podría incorporarse… si el dinero se recaudó o se recibió»; mientras fuentes_arrastrables siga «a '
   'verificar» no se afirma que se incorporó. Borrador con «sobró», «devolvió» o «perdió» junto a una cifra de gasto → '
   'bloquear el enunciado (R-GASTO-15).'),
  accion='rotular',
  parametros={'desglose': ['fuente_financiamiento', 'tipo (actividad o proyecto)'],
   'fuentes_arrastrables': 'a verificar (el DL 1440, art. 50, habla de recursos financieros); hasta citar la norma de cierre, solo texto condicional',
   'expresiones_prohibidas': ['sobró', 'devolvió', 'perdió'], 'requiere': ['fuente_financiamiento']},
  mensaje_usuario=('De lo que no se gastó, S/ {x} era presupuesto de recursos ordinarios, que no puede usarse el año '
   'siguiente; S/ {y} era de otras fuentes, que podría incorporarse el año siguiente si el dinero se recaudó o se recibió.'),
  justificacion=('El PIM es crédito presupuestario: una autorización de gasto, no caja. Lo no ejecutado en obras y '
   'recursos determinados suele volver a asignarse al año siguiente (los equipos del Hospital Regional de Cajamarca, 39 '
   'millones, no se gastaron en 2023 y se gastaron completos en 2024); decir que «se perdió» es falso.'),
  referencias=[REF_R2, REF_TRANSF, REF_W4_REGLAS, REF_AUD_GLOS],
  hallazgos_auditoria=[], hallazgos_prueba=[],
  ejemplo=('Inválido: «el GORE perdió 91 millones». Válido: «lo no gastado está sobre todo en obras y compras de equipos, '
   'financiadas con recursos determinados; esa parte del presupuesto podría incorporarse al año siguiente si el dinero se '
   'recibió».'),
  implementacion=_PRE_DATOS,
  casos_borde=('Solo años cerrados. Si la fuente no se conoce, solo se dice cuánto no se gastó, sin rótulo de fuente. La '
   'ejecución del mismo proyecto el año siguiente se muestra con su CUI y no se presenta como el mismo dinero.'),
  prioridad='mvp', decisiones_gasto_r2=['ronda 2, decisión 10']),
 dict(id='R-GASTO-21', ambito='gasto', titulo='No sumar el PIM de distintos años',
  enunciado=('El PIM no se suma entre años distintos ni entre niveles de gobierno o entidades sin quitar las transferencias '
   '(R-GASTO-05). El presupuesto de cada año se muestra por separado. El PIM se lee del mes 0 de la base.'),
  aplica_a=dict(_GASTO_AA),
  condicion=('Consulta que agrega MONTO_PIM o MONTO_PIA sobre más de un ANO_EJE → bloquear_cruce. Suma de PIM entre '
   'entidades o niveles de gobierno fuera de v_gasto_tematico o v_gasto_consolidado (R-GASTO-05) → bloquear_cruce. PIM := '
   'valor de MES_EJE = 0; un PIM leído con MES_EJE ≠ 0 vale cero → error de consulta.'),
  accion='bloquear_cruce',
  parametros={'mes_pim': 0, 'agregacion_permitida': 'PIM de un solo año; varios años solo lado a lado'},
  # Sin mensaje: la propuesta v2 aprobada no trae uno («—») y la regla solo bloquea la operación (auditoría pieza B, hallazgo 5).
  mensaje_usuario=None,
  justificacion=('Lo no ejecutado de un año puede volver a asignarse al siguiente (por ejemplo, como saldo de balance), así '
   'que sumar el PIM de varios años cuenta dos veces el mismo crédito. Entre niveles, las transferencias intergubernamentales '
   'aparecen en el PIM de quien da y de quien recibe.'),
  referencias=[REF_R2, REF_TRANSF, REF_W4_REGLAS, REF_AUD_GLOS],
  hallazgos_auditoria=[], hallazgos_prueba=[],
  ejemplo='Inválido: «entre 2023 y 2025 el GORE tuvo un presupuesto de S/ 3 000 millones». Válido: el PIM de cada año, lado a lado.',
  implementacion=('Guardia del motor (guardia_gasto.verificar_consulta) y validador: rechazo de agregados de MONTO_PIM o '
   'MONTO_PIA con más de un ANO_EJE.'),
  casos_borde=('La suma del devengado de varios años sí es posible (en soles constantes, R-GASTO-12). Una suma de PIM entre '
   'entidades sale solo de las vistas de R-GASTO-05.'),
  prioridad='mvp', decisiones_gasto_r2=['ronda 2, decisión 10']),
]
# Etapa de cada regla nueva: (regla, etapa, insertar después de)
ETAPAS_GASTO_R2 = [('R-GASTO-08b', '5_series', 'R-GASTO-08'), ('R-GASTO-18', '4_precision', 'R-GASTO-07'),
                   ('R-GASTO-19', '4_precision', 'R-GASTO-18'), ('R-GASTO-20', '4_precision', 'R-GASTO-19'),
                   ('R-GASTO-21', '4_precision', 'R-GASTO-20')]

# -- Cambios en reglas existentes. R-GASTO-05: se conserva la v4 (ronda 3) y se agregan los tres significados de
#    «transferencia» y los bloques de «recursos recibidos» de la ronda 2 (decisión 11 y R-GASTO-05 v2).
_V4_05 = {ruta: val for rid, ruta, val in CAMPOS_REGLAS if rid == 'R-GASTO-05'}
CAMPOS_REGLAS += [
 ('R-GASTO-05', 'titulo', 'Donaciones y transferencias: lista curada y guardia del motor (v4) y recursos recibidos'),
 ('R-GASTO-05', 'enunciado', _V4_05['enunciado'] + (
  ' Tres cosas distintas se llaman «transferencia» (ronda 2): (i) la transferencia de partidas o el crédito suplementario, '
  'que aumenta durante el año el PIM de quien recibe y no genera doble conteo (se lee con R-GASTO-18); (ii) el gasto en la '
  'genérica 2.4 del lado de quien da, con las categorías de arriba; y (iii) las transferencias a otras entidades públicas y '
  'a fondos públicos fuera de la base (2.4.x.3.1.4 y .5), que no desaparecen al consolidar: se cuentan aparte, como gasto '
  'final de quien transfiere, en el bloque rotulado (b), salvo los fondos por identificar (b′). Lo que una entidad recibe '
  'se presenta en tres bloques que no se suman entre sí ni con su devengado: transferencias de partidas recibidas (crédito), '
  'transferencias financieras incorporadas (crédito; incluye saldos de años anteriores) y caja acreditada de recursos '
  'determinados del Tesoro (MONTO_ACREDITADO).')),
 ('R-GASTO-05', 'condicion', _V4_05['condicion'] + (
  ' (7) «Recursos recibidos» por una entidad: tres bloques que no se suman entre sí ni con el devengado — partidas recibidas '
  '(crédito; solo cuando exista dim_modificacion_presupuestaria), transferencias financieras incorporadas (crédito: PIM de '
  'la fuente de financiamiento donaciones y transferencias, que incluye saldos de balance) y caja acreditada de recursos '
  'determinados (MONTO_ACREDITADO de MEF-DA-TRANSFERENCIAS) —; cualquier suma entre ellos → bloquear_cruce. Requiere '
  'fuente_financiamiento en la fact o en una vista de ejecución.')),
 ('R-GASTO-05', 'parametros.recursos_recibidos', {
  'bloques': ['partidas_recibidas (crédito; requiere dim_modificacion_presupuestaria)',
              'transferencias_financieras_incorporadas (crédito; PIM de la fuente donaciones y transferencias; incluye saldos)',
              'caja_acreditada_rd (MONTO_ACREDITADO)'],
  'se_suman': False, 'requiere': ['fuente_financiamiento']}),
 ('R-GASTO-05', 'casos_borde', _V4_05['casos_borde'] + (
  ' [Ronda 2, decisión 11] El bloque rotulado de .4 y .5 que aprobó el dueño es la categoría (b) de la v4 (con EX-01 y '
  'EX-02); los fondos (b′, EX-03) quedan solo como nota hasta documentar su destino, por la decisión GA-05 de la ronda 3, '
  'posterior y más específica. Los receptores principales de (b) no son pliegos de la base: bonos de vivienda del MVCS, el '
  'FEPC del MINEM, fondos agrarios y EPS.')),
 ('R-GASTO-05', 'referencias', _V4_05['referencias'] + [REF_R2, REF_TRANSF, REF_W4_REGLAS, REF_AUD_GLOS]),
]

# R-GASTO-07 v2: avance sobre el PIM final, con rótulo (no hay PIM mensual).
_REFS_07 = [
 {'titulo': 'MEF – Anexo 08 RD 030-2019-EF/50.01: Ficha técnica de indicadores de evaluación institucional financiera (I = Devengado / PIM × 100)',
  'url': 'https://www.mef.gob.pe/contenidos/presu_publ/anexos/Anexo_08_Ficha_tecnica_indicadores_evaluacion_institucional_financiera_RD030_2019EF5001.pdf'},
 {'titulo': 'Plataforma Nacional de Datos Abiertos – Presupuesto y Ejecución de Gasto (recursos 2012–2024 anuales; 2025–2026 -Mensual y -Diario)',
  'url': 'https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto'}]
CAMPOS_REGLAS += [
 ('R-GASTO-07', 'titulo', 'Avance de ejecución sobre el presupuesto final y fecha de corte'),
 ('R-GASTO-07', 'enunciado',
  'El avance de ejecución es devengado / PIM y se muestra siempre con su fecha de corte. La base trae un solo PIM por año '
  '(no hay PIM mensual), así que: en años cerrados, devengado / PIM final; para comparar años al mismo mes, devengado '
  'acumulado al mes m / PIM final de cada año, con el rótulo «avance respecto del presupuesto final del año (no del vigente '
  'en ese mes)»; en el año en curso, devengado / PIM de la última descarga, con su fecha, rotulado «parcial». El devengado '
  'sobre el PIA nunca se llama «ejecución». Cuando existan fotos mensuales propias del PIM (desde 2026), el avance al mismo '
  'mes se calcula con el PIM vigente a ese corte.'),
 ('R-GASTO-07', 'condicion',
  "anio_cerrado = (fecha_extraccion ≥ fecha_cierre_param(anio)). Año cerrado: avance = Σ MONTO_DEVENGADO(anio) / PIM_final. "
  "Comparación al mismo mes m: avance_m = Σ MONTO_DEVENGADO(MES_EJE ≤ m) / PIM_final(anio) → rótulo rotulo_mismo_mes "
  "obligatorio (en el año en curso, el PIM final se aproxima con el de la última descarga). Año en curso: PIM := PIM de la última descarga "
  "(fecha_descarga) → rotular 'parcial'. Si existe foto_pim(anio, m) aprobada para todos los años comparados → avance_m = "
  "Σ MONTO_DEVENGADO(MES_EJE ≤ m) / foto_pim(anio, m), sin el rótulo. Suprimir avance si PIM < pim_minimo. Si avance > 100,5 "
  "→ error de datos (revision_humana). Cifra rotulada «ejecución» con denominador PIA → bloquear el rótulo."),
 ('R-GASTO-07', 'accion', 'rotular'),
 ('R-GASTO-07', 'parametros', {
  'pim_minimo_soles': 50000, 'tolerancia_sobre_100': 0.5,
  'fecha_cierre_param': '31 de marzo del año siguiente (provisional, a confirmar comparando descargas sucesivas)',
  'denominador': {'anio_cerrado': 'PIM final', 'mismo_mes_sin_fotos': 'PIM final del año', 'anio_en_curso': 'PIM de la última descarga', 'con_fotos': 'foto_pim(anio, m)'},
  'rotulo_mismo_mes': 'avance respecto del presupuesto final del año (no del vigente en ese mes)',
  'foto_pim_mensual': 'desde 2026 (decisión del dueño, 7/10/2026); hacia atrás no se puede reconstruir'}),
 ('R-GASTO-07', 'mensaje_usuario',
  '(año en curso) «Datos al {fecha_corte}. El año aún no termina y buena parte del gasto público se registra en los '
  'últimos meses, así que este avance no es el resultado final del año.» (comparación al mismo mes) «Avance respecto del '
  'presupuesto final del año (no del vigente en ese mes).»'),
 ('R-GASTO-07', 'implementacion',
  'fecha_corte = max(MES_EJE con MONTO_DEVENGADO ≠ 0) del archivo + fecha de descarga; guardar ambas en '
  'resultado.fecha_corte_datos y resultado.es_anio_cerrado. PIM y PIA del mes 0 (R-GASTO-21); devengado acumulado al mes m '
  'de los meses 1–12. Fotos del PIM: copia fechada del archivo del año en curso en cada descarga (desde 2026); '
  'resultado.denominador_avance indica cuál se usó. Se muestra junto con el cambio neto del presupuesto (R-GASTO-18).'),
 ('R-GASTO-07', 'ejemplo',
  "En octubre de 2026 (datos a agosto): 'GORE Loreto ejecutó el 48 % de su presupuesto del PP 1001 a agosto de 2026 (sobre "
  "el presupuesto de la última descarga); a agosto de 2025 había ejecutado el 51 % de su presupuesto final de 2025', con el "
  "rótulo del mismo mes."),
 ('R-GASTO-07', 'referencias', _REFS_07 + [REF_R2, REF_TRANSF, REF_AUD_GLOS]),
]
PARCHES_REGLAS_R3 += [
 ('R-GASTO-07', 'Ejecutoras con PIM recién incorporado en diciembre (transferencias tardías) muestran avance bajo: el mensaje de R-GASTO-15 aplica.',
  'Ejecutoras con PIM recién incorporado en diciembre (transferencias tardías) muestran avance bajo: se aplican R-GASTO-18 '
  '(cambio neto del presupuesto), R-GASTO-19 (gasto que empezó tarde) y R-GASTO-15 (sin juicios sobre la entidad).'),
]

# R-GASTO-08: dim_tema_gasto v1.2 con prefijos por cadena; concepto estable anclado en la actividad; sin «PP 0001 + PP 1001
# completo»; cifra principal del ex-PAN = serie por concepto (opción C como desglose); regla de nombres.
NOMBRES_PROGRAMAS = {
 'regla': 'Al usuario se le muestra el nombre propio vigente en el año de la cifra y, entre paréntesis, el nombre que usa el MEF cuando difiere.',
 'mef_vs_vigente': {'Trabaja Perú': 'Llamkasun Perú (DS 009-2023-TR)', 'PNCVFS': 'Warmi Ñan (DS 003-2025-MIMP)',
                    'Qali Warma': 'Wasi Mikuna (DS 010-2024-MIDIS; Qali Warma en 2024)', '—': 'PAE, programa nuevo con ejecutora propia (DS 008-2025-MIDIS)'},
 'ejemplo': '«Llamkasun Perú (en el presupuesto del MEF figura como “Programa para la Generación de Empleo Social Inclusivo – Trabaja Perú”)»',
 'pp_1001': 'programa presupuestal 1001 Productos Específicos para el Desarrollo Infantil Temprano (nunca «el DIT» ni «política de primera infancia»)',
 'ppor_dit': '«PPoR DIT» designa solo la política, que articula varios programas',
 'pan': 'No se dice «gasto del PAN» para años posteriores a 2022: se nombra el programa vigente (PP 1001) o el concepto («servicios que antes eran del PAN»).',
 'linaje': {'PP 0001 PAN': '2008–2022; sus productos de salud pasaron al PP 1001 en el año fiscal 2022 y el resto en 2023 (agua y comunicación sobre anemia a la APNOP)',
            'PP 0098 Cuna Más': '2013–2020; pasó al PP 1001 en 2021',
            'PP 1001': '2021–; ancestros: solo el PAN y Cuna Más'}}
CAMPOS_REGLAS += [
 ('R-GASTO-08', 'titulo', 'Etiquetado temático con dim_tema_gasto v1.2: cadenas, conceptos estables y nombres'),
 ('R-GASTO-08', 'enunciado',
  'El gasto por tema se asigna solo con dim_tema_gasto v1.2, una tabla curada y versionada por año, sin transferencias '
  '(R-GASTO-05). Cada tema tiene un nombre único con el prefijo de su cadena (R-GASTO-08b), una llave de unión explícita, '
  'su nivel (función, división, programa, producto o concepto), una etiqueta ciudadana y marcas de comparabilidad. Los '
  'temas cpt_ no mapean códigos: apuntan a grupos de conceptos estables, y cada concepto agrupa los nodos (año, programa, '
  'producto, actividad) de un mismo servicio a lo largo del tiempo, anclado en la actividad y con el producto como '
  'respaldo. El LLM no decide qué gasto pertenece a un tema. Para los servicios que antes eran del PAN, la cifra principal '
  'es la serie por concepto (cpt_grupo_expan, siguiéndolos a cualquier programa); la lectura «dentro del PP 1001» (opción '
  'C, cpt_grupo_opcion_c) va como desglose. Nombres: se muestra el nombre propio vigente en el año de la cifra, con el del '
  'MEF entre paréntesis cuando difiere; no se dice «gasto del PAN» para años posteriores a 2022.'),
 ('R-GASTO-08', 'condicion',
  "tema(fila) := lookup(dim_tema_gasto v1.2, anio, llave_union del tema): funcion → FUNCION; division → FUNCION + "
  "DIVISION_FUNCIONAL; programa → PROGRAMA_PPTO [+ PRODUCTO_PROYECTO]; programa_x_funcion → PROGRAMA_PPTO + FUNCION; "
  "concepto → rel_concepto_grupo → rel_concepto_nodo (anio, PROGRAMA_PPTO, PRODUCTO_PROYECTO, ACTIVIDAD_ACCION_OBRA; gana "
  "la fila más específica); programa_social → ejecutora o actividad municipal (dim_programa_social). Solo filas con "
  "bloque_consolidado = 'gasto_final'. Si el año no tiene versión aprobada de dim_tema_gasto, o se pide un tema cpt_ y la "
  "fact no trae ACTIVIDAD_ACCION_OBRA → bloquear la cifra temática. Toda cifra temática declara tema_id y cadena "
  "(R-GASTO-08b). El motor lee el gasto de un tema solo con la macro gasto_tema('<tema_id>'), una llamada por consulta; las "
  "hojas de concepto, con v_gasto_concepto; nunca v_gasto_tema_interna (guardia G4, src/pap/capa0/guardia_gasto.py). "
  "Rótulo := etiqueta_ciudadana; programa social := nombre_propio(programa, anio) [+ ' (en el presupuesto del "
  "MEF figura como ' + nombre_mef + ')' si difiere]. Borrador que llama «PAN» o «Programa Articulado Nutricional» al gasto "
  "de un año posterior a 2022 → regenerar."),
 ('R-GASTO-08', 'parametros', {
  'version_dim_tema_gasto': '1.2',
  'columnas': ['anio', 'tema_id', 'cadena', 'codigo_origen', 'nivel', 'llave_union', 'alternativa_de', 'etiqueta_ciudadana',
               'excluye_transferencias', 'comparable_con_anio_anterior', 'motivo_quiebre', 'version', 'revisado_por'],
  'temas_iniciales': TEMAS_V12,
  'expan': {'principal': 'cpt_grupo_expan (serie por concepto; 2023–2025: 2 179 / 2 429 / 2 456 millones, sin transferencias)',
            'desglose': 'cpt_grupo_opcion_c (dentro del PP 1001; 2 056 / 2 327 / 2 366)',
            'contexto': 'cpt_grupo_anemia_estricta (hierro y atención de la anemia; 138 / 184 / 208) y pp_1001_dit (2 750 / 3 607 / 3 867)'},
  'eslabon_concepto': {'llave': 'nodo (año, programa, producto, actividad)', 'ancla': 'actividad', 'respaldo': 'producto',
                       'tablas': ['dim_concepto', 'rel_concepto_grupo', 'rel_concepto_nodo', 'rel_linaje', 'cobertura_por_anio']},
  'nombres': NOMBRES_PROGRAMAS}),
 ('R-GASTO-08', 'mensaje_usuario',
  '(función) «Gasto en el sector {sector}: todo lo que el Estado clasifica como {sector}.» (programa) «Gasto del programa '
  '{programa}.» (concepto) «{etiqueta}.» (servicios que antes eran del PAN) «Los servicios de nutrición infantil (vacunas, '
  'controles de crecimiento, hierro, atención de la anemia, de diarreas e infecciones) se financiaron con el Programa '
  'Articulado Nutricional entre 2008 y 2021.» «Desde 2022 se financian con el programa Productos Específicos para el '
  'Desarrollo Infantil Temprano, que desde 2021 también incluye Cuna Más.»'),
 ('R-GASTO-08', 'justificacion',
  'Los programas presupuestales cambian de un año a otro y sus servicios cambian de programa (PAN → PP 1001), así que el '
  'programa no sirve como hilo de una serie. El código de actividad sobrevivió a las recodificaciones de 2021 (hierro '
  '5000019, IRA/EDA 5000027–30, Cuna Más): por eso el concepto estable se ancla en la actividad. La regla anterior, «PP '
  '0001 + PP 1001 completo», metía Cuna Más y obras de hospitales en «anemia». Con nombres iguales en dos cadenas se sumaba '
  'dos veces el mismo sol.'),
 ('R-GASTO-08', 'ejemplo',
  "'Gasto en los servicios que antes eran del PAN, Cusco 2023–2025' → cpt_grupo_expan por año (cifra principal), con el "
  "desglose cpt_grupo_opcion_c (dentro del PP 1001) en una línea aparte y la frase de linaje. Antes de 2023, solo el linaje "
  "documental, sin cifras (R-GASTO-09)."),
 ('R-GASTO-08', 'implementacion',
  'dim_tema_gasto v1.2 y las tablas de trazabilidad (dim_programa, dim_producto, dim_actividad, dim_concepto, '
  'rel_concepto_grupo, rel_concepto_nodo, rel_linaje, rel_programa_politica, dim_programa_social, rel_programa_social_ejecutora, '
  'rel_programa_social_financiamiento, cobertura_por_anio y dim_glosario_gasto; nombres publicados en '
  'biblioteca/dimensiones/manifiesto_s3_gasto.json; rel_concepto_nodo se publica resuelto desde el curado '
  'trazabilidad/map_concepto_nodo.csv) en la capa 0; requiere ACTIVIDAD_ACCION_OBRA en '
  'fact_gasto_territorial. Pruebas: (1) cada código PROGRAMA_PPTO del año está mapeado o marcado sin_tema; (2) G-03: '
  'dentro de cada cadena ninguna fila recibe dos temas, salvo alternativa_de; (3) gramática de tema_id; (4) las cifras '
  'de expan se reproducen exactamente; (5) rel_concepto_nodo excluye transferencias.'),
 ('R-GASTO-08', 'casos_borde',
  'El gasto de acciones centrales y APNOP (9001/9002) solo entra a un tema si se mapea por actividad; el resto se declara '
  'sin tema. Se baja a la actividad cuando un producto mezcla conceptos (el CRED 3033255 contiene CRED y hierro), en la '
  'APNOP, en los productos genéricos (3000001) y en los programas sociales. El hierro para gestantes (3033317) desaparece '
  'en 2021 absorbido en la atención prenatal del PP 0002: evento sin nodo ni montos; no se mapea 0002/3033172. La frase '
  '«Desde 2021 el Estado ya no tiene un PAN» es falsa y no se usa. Contigo, PAIS, Vaso de Leche y el PCA se pagan desde '
  'la APNOP: los programas sociales se definen por ejecutora y actividad.'),
 ('R-GASTO-08', 'referencias', [
  {'titulo': 'MEF – Estructura de los Programas Presupuestales por año (2012–2027)', 'url': 'https://www.mef.gob.pe/es/presupuesto-por-resultados/estructura-de-programas'},
  {'titulo': 'MEF (2023) – Criterios de programación de productos y proyectos del PP 1001 Desarrollo Infantil Temprano (migración de productos del PP 0001 y traslado a APNOP)', 'url': 'https://mef.gob.pe/contenidos/presu_publ/capacita/2023/08052023_CRITERIOS_PROG_PROD_PROY_PP_1001_DESARROLLO_INFANTIL_TEMPRANO.pdf'},
  {'titulo': 'MINSA – Reporte de seguimiento 2023-I del PPoR 1001 (6 productos del PP 0001 migrados en 2021; 4 en 2023 y 2 a APNOP)', 'url': 'https://www.minsa.gob.pe/presupuestales/doc2024/reporte-seguimiento/Reporte%202023-I_PPoR%201001.pdf'},
  {'titulo': 'MINSA – Reporte de seguimiento PP 0002 Salud Materno Neonatal 2026-I (el PP 0002 sigue vigente)', 'url': 'https://www.minsa.gob.pe/presupuestales/doc2026/reporte-seguimiento/Reporte_PP_0002_2026_I.pdf'},
  {'titulo': 'MEF – Estructura programática PP 0150 Incremento en el acceso de la población a los servicios educativos públicos de la Educación Básica (2026)', 'url': 'https://www.mef.gob.pe/contenidos/presu_publ/ppr/estr_program/PP_0150_PRODUCTO_2026.pdf'},
  REF_R2, REF_W2, REF_GLOS, REF_AUD_TRAZ, REF_R1, REF_TEMA]),
]

# R-GASTO-09: series por concepto estable; linaje anterior a 2023 solo documental; quiebres calculados (W2 v2 §4.4).
CAMPOS_REGLAS += [
 ('R-GASTO-09', 'titulo', 'Series del gasto por concepto estable y advertencia de quiebre'),
 ('R-GASTO-09', 'enunciado',
  'Una serie temática de gasto sigue un concepto estable, o un tema de una sola cadena (R-GASTO-08b), con la misma versión '
  'de dim_tema_gasto en todos los años. Las series con cifras de gasto son 2023–2025; el linaje anterior a 2023 (PAN y '
  'Cuna Más → PP 1001) se documenta desde normas y reportes del MINSA y del MEF, sin cifras de gasto y con su grado de '
  'confianza. Un año marcado como no comparable muestra el quiebre en el gráfico y en el texto, y no se calcula la '
  'variación entre ese año y el anterior como si fuera un cambio real del gasto.'),
 ('R-GASTO-09', 'condicion',
  "no_comparable(concepto, t) si: (1) hay un evento de rel_linaje con anio_min ≤ t ≤ anio_max y comparabilidad = 'no "
  "comparable' (si el año del evento es un intervalo, se marcan todos sus años); (2) los nodos nuevos del concepto en t "
  "pesan más que umbral_nodos_nuevos_pct del devengado del concepto y ningún evento los declara comparables; o (3) "
  "cobertura_por_anio(t) ≠ 'con_montos'. Caso (3) → no se publica cifra de gasto de ese año, solo el texto de linaje con su "
  "confianza. Si no_comparable en t y se pide la variación t-1 → t → advertir y no presentar variación porcentual. Temas "
  "fun_ y div_: los quiebres de programas no aplican; los cambios del clasificador funcional van a revisión humana."),
 ('R-GASTO-09', 'parametros', {
  'umbral_nodos_nuevos_pct': 0.05, 'anios_con_montos': [2023, 2024, 2025],
  'cobertura_por_anio': {'con_montos': '2023–2025', 'documentado_sin_montos': '2017–2022', 'documentado_parcial': '2012–2016', 'estructura_no_comparable': '2008–2011'},
  'linaje_previo_2023': 'solo documental (normas, reportes del MINSA y del MEF), sin cifras de gasto y con confianza (decisión del dueño, 7/10/2026: por ahora no se descarga el gasto de 2022 ni de años anteriores)'}),
 ('R-GASTO-09', 'mensaje_usuario',
  '(quiebre) «En {anio} el MEF reorganizó los programas de este tema; parte del cambio que se ve ese año se debe a la '
  'nueva clasificación y no a más o menos gasto.» (años anteriores a 2023) «Antes de 2023 solo describimos en qué '
  'programa estaba este servicio; no mostramos cifras de gasto de esos años.»'),
 ('R-GASTO-09', 'justificacion',
  'Entre 2023 y 2025 ningún programa cambió de nombre y entre 98 % y 99 % de los productos conservan su código (99,87 % del '
  'gasto); en el PP 1001 hay una sola alta, el agua, en 2025. Los quiebres grandes (traslado del PAN al PP 1001 en el año '
  'fiscal 2022, recodificaciones de 2021) caen en años que la base no tiene. Seguir el concepto, y no el programa, evita '
  'que un traslado entre programas parezca un cambio del gasto.'),
 ('R-GASTO-09', 'ejemplo',
  "Serie 'servicios que antes eran del PAN' en Apurímac, 2023–2025: tres años con cifra y, si un nodo nuevo pesa más del 5 % "
  "sin un evento que lo declare comparable, marca de quiebre en ese año. Antes de 2023: el texto de linaje (traslado del PAN "
  "al PP 1001 en el año fiscal 2022), sin cifras."),
 ('R-GASTO-09', 'implementacion',
  'anios_quiebre se deriva de rel_linaje, cobertura_por_anio y el peso de los nodos nuevos de rel_concepto_nodo, y se guarda en '
  'indicador.anios_con_quiebre (campo existente) y en dim_tema_gasto.comparable_con_anio_anterior / motivo_quiebre. GPNNA: '
  'la serie de datos abiertos empieza en 2023 (no empalmar con reportes PDF anteriores).'),
 ('R-GASTO-09', 'casos_borde',
  'Un cambio de nombre sin cambio de código no es quiebre. Un traslado de un servicio entre programas con su actividad '
  'intacta no rompe la serie por concepto, pero sí la del programa (pp_). Si en el futuro se cargan años anteriores a 2023, '
  'los quiebres de 2021–2022 se marcan desde rel_linaje.'),
 ('R-GASTO-09', 'referencias', [
  {'titulo': 'MEF (2023) – Criterios de programación de productos y proyectos del PP 1001 Desarrollo Infantil Temprano (migración de productos del PP 0001 y traslado a APNOP)', 'url': 'https://mef.gob.pe/contenidos/presu_publ/capacita/2023/08052023_CRITERIOS_PROG_PROD_PROY_PP_1001_DESARROLLO_INFANTIL_TEMPRANO.pdf'},
  {'titulo': 'MINSA – Reporte de seguimiento 2023-I del PPoR 1001 (6 productos del PP 0001 migrados en 2021; 4 en 2023 y 2 a APNOP)', 'url': 'https://www.minsa.gob.pe/presupuestales/doc2024/reporte-seguimiento/Reporte%202023-I_PPoR%201001.pdf'},
  {'titulo': 'MEF – Estructura de los Programas Presupuestales por año (2012–2027)', 'url': 'https://www.mef.gob.pe/es/presupuesto-por-resultados/estructura-de-programas'},
  REF_R2, REF_W2, REF_AUD_TRAZ]),
]

# R-GASTO-15: lista bloqueada simétrica (acusaciones y excusas sobre la ejecución).
LISTA_BLOQUEADA_R2 = ['mala ejecutora', 'buena ejecutora', 'no supo gastar', 'incapacidad de gasto', 'dejó de gastar',
                      'devolvió el dinero', 'perdió el presupuesto', 'sobró', 'baja capacidad de ejecución',
                      'es normal que no se gaste']
CAMPOS_REGLAS += [
 ('R-GASTO-15', 'enunciado',
  'Las respuestas no deben calificar el gasto como eficiente, ineficiente, suficiente, bien o mal usado, ni atribuirle '
  'efectos sobre indicadores de resultado (anemia, aprendizaje, pobreza); solo pueden describir montos, fases, avance y su '
  'coincidencia temporal con los indicadores. Tampoco califican a la entidad por su ejecución («mala ejecutora», «no supo '
  'gastar») ni la excusan («es normal que no se gaste»): la lista bloqueada es simétrica.'),
 ('R-GASTO-15', 'condicion',
  'Si la respuesta incluye una cifra de gasto y el borrador contiene términos de la lista_bloqueada o un verbo causal que '
  'vincule gasto con resultado → bloquear_cruce del enunciado y reemplazar por plantilla descriptiva. La lista es simétrica: '
  'bloquea tanto las acusaciones («mala ejecutora», «no supo gastar», «mala gestión») como las excusas («es normal que no '
  'se gaste»). Lo no ejecutado se describe con R-GASTO-18, R-GASTO-19 y R-GASTO-20, nunca como dinero que «sobró», «se '
  'devolvió» o «se perdió».'),
 ('R-GASTO-15', 'parametros.lista_bloqueada', ['eficiente', 'ineficiente', 'despilfarro', 'mal gasto', 'bien invertido',
  'suficiente', 'insuficiente', 'gracias al gasto', 'por el gasto', 'redujo', 'logró reducir', 'no sirvió',
  'incapacidad de gasto', 'mala gestión'] + [x for x in LISTA_BLOQUEADA_R2 if x != 'incapacidad de gasto']),
 ('R-GASTO-15', 'parametros.corrector',
  'Las expresiones de la ronda 2 están en lenguaje.prohibidas (categoría «juicio de valor», origen «decisiones del gasto r2»): '
  'cada forma exige un sujeto público (municipalidad, gobierno regional, GORE, ministerio, ejecutora, pliego, entidad, región…) o un '
  'objeto presupuestal (presupuesto, recursos, fondos) en la misma oración, porque el corrector léxico se aplica a toda respuesta; '
  '«mala gestión» e «incapacidad» ya estaban.'),
 ('R-GASTO-15', 'referencias', [
  {'titulo': 'MEF – Anexo 08 RD 030-2019-EF/50.01: Ficha técnica de indicadores de evaluación institucional financiera (I = Devengado / PIM × 100)',
   'url': 'https://www.mef.gob.pe/contenidos/presu_publ/anexos/Anexo_08_Ficha_tecnica_indicadores_evaluacion_institucional_financiera_RD030_2019EF5001.pdf'},
  REF_R2, REF_TRANSF, REF_W4_REGLAS, REF_AUD_GLOS]),
]
HALLAZGOS_GASTO_R2 = {'R-GASTO-05': ['ronda 2, decisión 11', 'R-GASTO-05 v2 (M6, M8)'], 'R-GASTO-07': ['ronda 2, decisión 10', 'R-GASTO-07 v2 (M5)'],
                      'R-GASTO-08': ['ronda 1, decisiones 1 y 3', 'ronda 2, decisiones 1, 2, 3, 4 y 9'],
                      'R-GASTO-09': ['ronda 2, decisiones 2 y 5', 'W2 v2 §4.4'], 'R-GASTO-15': ['ronda 2, decisión 10', 'R-GASTO-15 (M7)']}

# -- Corrector: expresiones de R-GASTO-15 (ronda 2) y regla de nombres del PAN. Corrección tras la auditoría de la pieza B
#    (hallazgos 1 y 4): R-GASTO-15 solo pide bloquear en respuestas con cifras de gasto público, y el corrector léxico se
#    aplica a toda respuesta; por eso cada forma exige un sujeto público (_ENT) o un objeto presupuestal en la misma
#    oración, y «capacidad» queda solo en la expresión aprobada («baja capacidad de ejecución»). Texto normalizado.
_ENT = (r'\b(municipalidad\w*|municipios?|gobiernos? (regional|regionales|local|locales|nacional)|gores?|ministerios?|'
        r'ejecutoras?|pliegos?|entidad(es)?|region(es)?|alcaldias?|diresas?|ugel(es)?)\b')
_OBJ = r'(presupuesto|recursos|fondos)'
_PAN = r'(?:\b(?-i:PAN)\b|programa articulado nutricional)'
_HASTA_2022 = (r'(?!\s*(?:entre (?:19|20)\d\d y |de (?:19|20)\d\d a |hasta |\(\s*(?:19|20)\d\d\s*[–-]\s*|(?:19|20)\d\d\s*[–-]\s*)'
               r'(?:19\d\d|20(?:0\d|1\d|2[0-2]))\b)')
_PAN_DUENO = (r'(?:\b(?:gastos?|presupuestos?|ejecuci[oó]n|devengados?|inversi[oó]n|lo ejecutado|lo gastado|lo devengado)'
              r'(?: total)? (?:del|en el|por el) ' + _PAN + _HASTA_2022 +
              r'|\bel ' + _PAN + r' (?:gast[oó]|ejecut[oó]|deveng[oó]|invirti[oó]|recibi[oó]|cost[oó]|tuvo)\b'
              r'|\bse (?:gast[oó]|gastaron|ejecut[oó]|ejecutaron|invirti[oó]|invirtieron|destin[oó]|destinaron)\b[^.;]{0,40}\ben el ' + _PAN + r')')
PATRON_PAN_R2 = (r'(?:^|[.;])(?=[^.;]*' + _PAN_DUENO + r')'
                 r'[^.;]*(?<!desde )(?<!partir de )(?<!despues de )(?<!después de )\b20(?:2[3-9]|[3-9]\d)\b')
PROHIBIDAS_GASTO_R2 = [
 {'categoria': 'juicio de valor', 'origen': 'decisiones del gasto r2 (R-GASTO-15)',
  'contexto': 'respuestas con cifras de gasto público: cada forma exige un sujeto público o un objeto presupuestal en la misma oración',
  'patron': (r'\b(mala|buena)s? ejecutoras?\b'
             r'|' + _ENT + r'[^.;]{0,40}\bno (supo|supieron) (gastar|ejecutar)\b'
             r'|\bno (supo|supieron) (gastar|ejecutar) (el|su|sus|los) ' + _OBJ + r'\b'
             r'|\bincapacidad de (gasto|gastar|ejecucion|ejecutar)\b'
             r'|' + _ENT + r'[^.;]{0,40}\bdej(o|aron) de (gastar|ejecutar)\b'
             r'|\bdevolvi(o|eron) (el|la|los|las|su|sus) (dinero|presupuesto|recursos|fondos|plata)\b'
             r'|\bdevolvi(o|eron)\b[^.;]{0,40}\bal tesoro\b'
             r'|\bperdi(o|eron) (el|la|los|las|su|sus) ' + _OBJ + r'\b'
             r'|\bse perdi(o|eron)\b[^.;]{0,40}\b(del|de su|de sus|de los) ' + _OBJ + r'\b'
             r'|\b' + _OBJ + r'\b[^.;]{0,30}\bse perdi(o|eron)\b'
             r'|' + _ENT + r'[^.;]{0,40}\bperdi(o|eron)\b[^.;]{0,30}\b(millones|soles|dinero|' + _OBJ[1:-1] + r')\b'
             r'|\bsobr(o|aron)\b[^.;]{0,30}\b' + _OBJ + r'\b|\b' + _OBJ + r'\b[^.;]{0,30}\bsobr(o|aron)\b'
             r'|' + _ENT + r'[^.;]{0,40}\b(le |les )?sobr(o|aron)\b'
             r'|\bles? sobr(o|aron)\b[^.;]{0,20}\b(millones|soles)\b'
             r'|\bbaja capacidad de ejecucion\b'
             r'|\bes normal que no se (gaste|gasten|ejecute|ejecuten)\b')},
 # «PAN» solo en mayúsculas (el pan es un alimento): se evalúa sobre el texto original (texto_original), sin normalizar.
 # Verificación de las correcciones (N1): solo bloquea cuando el PAN es el dueño o el sujeto del gasto («gasto/presupuesto
 # del PAN», «lo ejecutado por el PAN», «el PAN gastó», «se gastó en el PAN») y la misma oración (entre «.» y «;») tiene un
 # año ≥ 2023 no precedido de «desde», «a partir de» o «después de». Las menciones históricas o aprobadas no bloquean:
 # «servicios que antes eran del PAN», «ex-PAN», «heredados del PAN», «el PAN (2008–2022)», «gasto del PAN entre 2008 y 2022».
 {'categoria': 'nombre de programa vencido', 'origen': 'decisiones del gasto r2 (R-GASTO-08, regla de nombres)',
  'normalizar': False, 'texto_original': True, 'patron': PATRON_PAN_R2},
]
# Pruebas de los patrones nuevos (consistencia: gasto_r2_no_detectada / gasto_r2_falso_positivo). Incluyen las 30 frases
# del auditor de la pieza B (auditoria/corrector_adversario_resultado.json). No entran al corpus.
CASOS_CORRECTOR_GASTO_R2 = {
 'bloquear': ['La municipalidad es una mala ejecutora.', 'El gobierno regional es una buena ejecutora.',
              'La región no supo gastar su presupuesto.', 'Hay incapacidad de gasto en la provincia.',
              'La municipalidad dejó de gastar en obras.', 'El gobierno regional devolvió el dinero al Tesoro.',
              'La entidad perdió el presupuesto de salud.', 'Al final del año sobró presupuesto.',
              'A la municipalidad le sobraron 5 millones del presupuesto.',
              'La región tiene baja capacidad de ejecución.', 'Con tan poco tiempo, es normal que no se gaste.',
              'Se perdieron 91 millones del presupuesto.', 'El gasto del PAN en 2024 fue de S/ 2 456 millones.',
              'En 2025, el gasto del Programa Articulado Nutricional llegó a S/ 2 456 millones.',
              # auditor (debe bloquear)
              'La municipalidad fue una pésima ejecutora en 2024.', 'Los gobiernos regionales no supieron gastar el presupuesto.',
              'Al cierre del año le sobraron 20 millones.', 'El GORE perdió 91 millones.',
              'La región devolvió al Tesoro 15 millones de soles.', 'Es normal que no se ejecute todo el presupuesto.',
              'Tiene baja capacidad de ejecución.', 'El gasto del PAN en 2023 fue de S/ 2 179 millones.',
              'En 2024 el PAN gastó S/ 2 429 millones.', 'El presupuesto del PAN en 2025 fue de S/ 2 456 millones.',
              'El gasto del PAN fue de S/ 2 456 millones (2025).',
              'Gasto del Programa Articulado Nutricional, 2023–2025: 2 179, 2 429 y 2 456 millones.',
              'Lo ejecutado por el PAN en 2024 llegó a S/ 2 429 millones.',
              # verificación de las correcciones (N1): el PAN como dueño o sujeto del gasto, con año ≥ 2023
              'En 2025 se gastó en el PAN S/ 2 456 millones.', 'El gasto del PAN en 2024 llegó a S/ 2 429 millones.',
              'El PAN ejecutó S/ 2 429 millones en 2024.', 'En 2024 el gasto total del PAN fue de S/ 2 429 millones.'],
 'pasar': ['Lo que no se gastó (S/ 91 millones) es menos que lo que se añadió en el año.',
           'De lo que no se gastó, S/ 10 millones era presupuesto de recursos ordinarios, que no puede usarse el año siguiente.',
           'Los servicios de nutrición infantil se financiaron con el Programa Articulado Nutricional entre 2008 y 2021.',
           'La unidad ejecutora registró el gasto en 2024.', 'El gasto del PAN en 2021 incluía las vacunas.',
           'La ejecución del presupuesto municipal llegó al 91 % del presupuesto final.',
           'Parte de este presupuesto se asignó durante el año y empezó a gastarse recién en los últimos meses.',
           # auditor (debe pasar)
           'El PAN de 2008–2022 financió las vacunas; desde 2023 el PP 1001 las financia.',
           'El gasto del PAN entre 2008 y 2022 no está en la base; las cifras de 2023 a 2025 son del PP 1001.',
           'El gasto del PAN se reporta solo hasta 2022; para 2023 usamos el programa vigente.',
           'Los hogares del quintil más alto tienen mayor capacidad de gasto; los del quintil 1, baja capacidad de gasto.',
           'Las familias con alta capacidad de gasto compran más alimentos procesados.',
           'En 2020 el país perdió 2 millones de empleos según el INEI.',
           'Se perdieron 2 millones de hectáreas de bosque entre 2001 y 2022.',
           'La SUNAT devolvió 9 000 millones de soles en impuestos en 2024.',
           'El hogar dejó de gastar en educación cuando el jefe de hogar perdió el empleo.',
           'La mala alimentación y la mala calidad del agua se asocian con anemia.',
           'Sobró tiempo en la consulta para revisar los datos del SIEN.',
           'La madre perdió el seguro y dejó de gastar en controles.',
           'El gasto del PAN llegó hasta 2022, y desde 2023 esos servicios los financia el PP 1001.',
           'Los servicios que antes eran del PAN costaron S/ 2 456 millones en 2025.',
           'El niño perdió peso y la familia perdió 300 soles de ingreso.',
           'Le sobró la mitad de la ración de hierro.',
           # verificación de las correcciones (N1): menciones históricas o aprobadas con año ≥ 2023
           'En 2024, el gasto en los servicios que antes eran del PAN fue de S/ 2 429 millones.',
           'Gasto en los servicios que antes eran del PAN, Cusco 2023–2025.',
           'La serie por concepto sigue el gasto de los servicios del PAN también en 2023, 2024 y 2025.',
           'El gasto del PAN entre 2008 y 2022 no está en la base, pero sí las cifras de 2023 a 2025 del PP 1001.',
           'El gasto ex-PAN fue de S/ 2 429 millones en 2024.',
           'Los servicios heredados del PAN costaron S/ 2 456 millones en 2025.',
           'El PAN (2008–2022) financió las vacunas, que en 2024 costaron S/ 664 millones dentro del PP 1001.',
           'El presupuesto del PAN (2008–2022) no es comparable con el gasto de 2023 del PP 1001.'],
 # Debe pasar los patrones nuevos, pero ya la bloqueaba un patrón anterior («subió»: cambio sin significancia, sin prueba).
 'pasar_solo_patrones_nuevos': ['En 2024 el gasto en el pan de los hogares subió 4 % según la ENAHO.'],
}
CAMPOS_GASTO_R2 = [
 ('tema_id / cadena', 'cifra', 'tema, alcance (nucleo / amplio)', 'Tema de dim_tema_gasto v1.2 con el prefijo de su cadena (fun_, div_, pp_, ppxfun_, cpt_, ps_) y cadena de la cifra; cifras de cadenas distintas no se suman (R-GASTO-08b).'),
 ('llave_union / codigo_origen / nivel / alternativa_de / etiqueta_ciudadana', 'tabla', '—', 'Columnas de dim_tema_gasto v1.2 (R-GASTO-08, R-GASTO-08b).'),
 ('concepto_id / grupo_id', 'cifra', '—', 'Concepto estable (anclado en la actividad) y grupo de conceptos de una serie (R-GASTO-08, R-GASTO-09).'),
 ('cambio_neto_presupuesto', 'cifra', '—', 'PIM − PIA de la entidad × tema, con signo (R-GASTO-18).'),
 ('pista_gasto_tardio', 'cifra', '—', 'Parte de lo no ejecutado en líneas sin PIA con primer devengado de octubre a diciembre o sin devengado; solo años cerrados (R-GASTO-19).'),
 ('no_ejecutado_por_fuente', 'cifra', '—', 'Lo no ejecutado por fuente de financiamiento y tipo; es crédito, no caja (R-GASTO-20).'),
 ('denominador_avance', 'cifra', '—', 'PIM final, PIM de la última descarga o foto mensual del PIM (R-GASTO-07).'),
]
DECISIONES_GASTO_R2 = [  # (id, tema, opciones, recomendación, reglas, decisión)
 ('D15', 'Cifra principal de los servicios ex-PAN (rondas 1 y 2)', 'Opción C (dentro del PP 1001) o serie por concepto (siguiéndolos a cualquier programa).', 'Serie por concepto como cifra principal; opción C como desglose.', 'R-GASTO-08, R-GASTO-08b', 'Adoptada (dueño, 7/10/2026).'),
 ('D16', 'Eslabón de las series y nombres (ronda 2, decisiones 1, 2 y 5)', 'Programa, producto o actividad como hilo; descargar o no 2012–2022.', 'Concepto estable anclado en la actividad; nombre propio vigente; sin «gasto del PAN» después de 2022.', 'R-GASTO-08, R-GASTO-09', 'Adoptada; por ahora no se descarga el gasto de 2022 ni de años anteriores: series 2023–2025 y linaje anterior solo documental.'),
 ('D17', 'Una cadena por cifra (ronda 2, decisión 9)', 'Mantener «núcleo / amplio» o declarar la cadena con prefijos.', 'Prefijos por cadena y tabla fija de intenciones.', 'R-GASTO-08b', 'Adoptada (dueño, 7/10/2026).'),
 ('D18', 'Ejecución y transferencias (ronda 2, decisiones 10 y 11)', 'Avance sobre el PIM vigente o sobre el final; cómo contar lo añadido y las transferencias .4/.5.', 'R-GASTO-18 a 21; R-GASTO-07 sobre el PIM final con rótulo; lista simétrica en R-GASTO-15; .4/.5 en bloque rotulado aparte.', 'R-GASTO-05, 07, 15, 18, 19, 20, 21', 'Adoptada (dueño, 7/10/2026); .4/.5 ya estaba en la v4 de R-GASTO-05 (ronda 3).'),
]
# Sobrescritura consciente: R-GASTO-08.casos_borde llevaba la nota PR-29 («PP 0001 migró a PPoR 1001 en dos pasos, 2021
# parcial y 2023 completo»), que la ronda 2 corrige (año fiscal 2022 para los productos de salud) y que ahora documentan
# rel_linaje y R-GASTO-09. hallazgos_prueba conserva PR-29.
SOBRESCRITURAS_CONSCIENTES = globals().get('SOBRESCRITURAS_CONSCIENTES', set()) | {('R-GASTO-08', 'casos_borde')}

# ================================================================ correcciones tras la auditoría de la pieza B (8/10/2026)
# 03_auditoria/ola0/decisiones_gasto/implementacion/pieza_b/auditoria/auditoria.md (hallazgos 1–6). Los patrones del
# corrector (hallazgos 1 y 4) y el mensaje de R-GASTO-21 (hallazgo 5) se corrigieron arriba, en su propio bloque.

# Hallazgo 2. R-GASTO-03 usa las marcas de la pieza A (criterio único de ejecutoras, decisiones 6 y 7 de la ronda 2, y
# decisión de la ronda 1 sobre las 22 ejecutoras mixtas): cuenta_en_lima, referencia_nacional (línea aparte) y la
# advertencia de mixtas. verificar_procedencia no lleva texto al usuario: su redacción no está decidida.
_GA01_VIEJO = ('nacional (sedes centrales, PNP, FF. AA., CENARES, SIS, PRONABEC, Congreso…) se excluye de toda cifra del '
               'departamento 15, de Lima Metropolitana y de Lima Región; lima_metropolitana (DIRIS, UGEL de Lima, hospitales y '
               'cortes de Lima) y lima_region pasan a esos ámbitos.')
_GA01_NUEVO = ('nacional (sedes centrales, PNP, FF. AA., CENARES, SIS, PRONABEC, Congreso…), lima_metropolitana (DIRIS, UGEL '
               'de Lima, hospitales y cortes de Lima) o lima_region. [Decisiones del gasto, ronda 2: criterio único de '
               'ejecutoras] Las cifras del departamento 15, de Lima Metropolitana y de Lima Región se calculan solo con las '
               'filas cuenta_en_lima = true de fact_gasto_territorial: atribuidas al departamento 15, sin el alcance nacional '
               'y sin los centros de referencia_nacional (INEN, INSN San Borja), incluidas sus obras. El gasto con '
               'referencia_nacional atribuido al departamento 15 va en una línea aparte que nunca se suma a la cifra de Lima. '
               'Las marcas referencia_nacional, verificar_procedencia y ejecutora_mixta vienen de ejecutoras_alcance.yaml '
               '(dim_unidad_ejecutora y la fact).')
_PR15_VIEJO = ('se excluyen las ejecutoras de alcance nacional (lista curada) y en el MVP se construye ambito_ejecutora solo '
               'para DIRIS y UGEL de Lima Metropolitana.')
_PR15_NUEVO = ('la cifra de Lima usa cuenta_en_lima (sin las ejecutoras de alcance nacional ni los centros de referencia '
               'nacional) y lleva la línea aparte de referencia nacional y la advertencia de ejecutoras mixtas. Las '
               'ejecutoras con verificar_procedencia conservan el alcance que tienen en ejecutoras_alcance.yaml hasta contar '
               'con su procedencia de pacientes; la marca no lleva texto al usuario mientras el dueño no lo decida.')
PARCHES_REGLAS_R3 += [('R-GASTO-03', _GA01_VIEJO, _GA01_NUEVO), ('R-GASTO-03', _PR15_VIEJO, _PR15_NUEVO)]
AGREGADOS_REGLAS_R3 += [
 ('R-GASTO-03', 'condicion',
  " [Ronda 2, criterio único de ejecutoras] Lima (departamento 15, Lima Metropolitana, Lima Región): cifra := Σ devengado "
  "WHERE cuenta_en_lima. refnac := Σ devengado WHERE referencia_nacional AND departamento_atribucion = '15' (mismo tema, "
  "año y fase) → línea aparte si refnac > 0, nunca sumada a la cifra. Toda cifra de Lima → advertencia de ejecutoras "
  "mixtas, hasta que se separen por producto (decisión del 7/10/2026)."),
]
_M03 = [v for r_, c_, v in CAMPOS_REGLAS if r_ == 'R-GASTO-03' and c_ == 'mensaje_usuario'][-1]
CAMPOS_REGLAS += [
 ('R-GASTO-03', 'mensaje_usuario',
  '(distrito o provincia) «' + _M03 + '» (cifras de Lima, si hay gasto de referencia nacional) «Además, S/ {refnac} '
  'millones en institutos de referencia nacional ubicados en Lima.» (cifras de Lima) «El gasto en Lima no incluye la '
  'parte local de programas nacionales ({programas_mixtos}).»'),
 ('R-GASTO-03', 'parametros.lima', {
  'cifra': 'cuenta_en_lima = true',
  'linea_aparte': "referencia_nacional AND departamento_atribucion = '15' (no se suma)",
  'advertencia_mixtas': 'siempre en las cifras de Lima, hasta separar por producto las 22 ejecutoras mixtas (decisión del 7/10/2026)',
  'programas_mixtos': 'PNP, Qali Warma o Wasi Mikuna (nombre vigente en el año, R-GASTO-08), Pensión 65… (texto de la ronda 1, decisiones_gasto_piloto.md)',
  'verificar_procedencia': 'marca interna; sin texto al usuario (pendiente del dueño)'}),
]
HALLAZGOS_GASTO_R2['R-GASTO-03'] = ['ronda 2, decisiones 6 y 7', 'ronda 1, decisión 2c', 'auditoría pieza B, hallazgo 2']
CAMPOS_GASTO_R2 += [
 ('cuenta_en_lima', 'fila de gasto', 'exclusión por alcance_ejecutora = nacional (GA-01)', 'La fila entra en las cifras del departamento 15, Lima Metropolitana y Lima Región: atribuida al dpto 15, sin alcance nacional ni referencia nacional (R-GASTO-03).'),
 ('referencia_nacional', 'ejecutora', '—', 'Centro de referencia nacional en Lima (INEN, INSN San Borja): su gasto, con sus obras, sale de Lima y va en una línea aparte (R-GASTO-03).'),
 ('verificar_procedencia', 'ejecutora', '—', 'Alcance sin dato de procedencia de pacientes; se conserva hasta tenerlo (Ley 27806). Sin texto al usuario (R-GASTO-03).'),
 ('ejecutora_mixta', 'ejecutora', '—', 'Programa nacional que también presta servicio en Lima (PNP, Pensión 65…); las cifras de Lima llevan advertencia hasta separarlo por producto (R-GASTO-03).'),
]

# Hallazgo 3. Ids de tema viejos: renombre mecánico (sin cambiar el fondo de R-GASTO-11) y prueba de consistencia.
PARCHES_REGLAS_R3 += [('R-GASTO-06', 'tema=agua_saneamiento', 'tema=fun_saneamiento')]
CAMPOS_REGLAS += [
 ('R-GASTO-11', 'parametros.grupos_objetivo', {'pp_1001_dit': '0-5', 'gpnna': '0-17', 'div_educacion_basica': '3-16',
                                               'pp_0002_materno_neonatal': 'nacidos vivos o mujeres 15-49 (decisión abierta)'}),
]
AGREGADOS_REGLAS_R3 += [
 ('R-GASTO-11', 'casos_borde',
  ' [Decisiones del gasto r2] Las llaves de grupos_objetivo pasaron a los ids de dim_tema_gasto v1.2 sin cambiar las edades '
  '(gpnna es la fuente MEF-DA-GASTO-GPNNA, no un tema). Pendiente (glosario v2, E8; no decidido): población por cadena; el '
  'PP 1001 completo incluye gestantes y Cuna Más, así que dividirlo solo entre niños de 0 a 5 años es una aproximación.'),
]
CLAVES_NO_TEMA = ['gpnna']   # llaves de grupos_objetivo que son una fuente, no un tema de dim_tema_gasto
TEMAS_VIEJOS = ['desarrollo_infantil_anemia_dci', 'salud_materna_neonatal', 'educacion_basica_aprendizajes',
                'educacion_basica_acceso', 'educacion_basica', 'agua_saneamiento', 'dit_salud', 'dit_proteccion_social',
                'dit_educacion', 'programas_sociales']

# ================================================================ nombres publicados de la capa de trazabilidad (8/10/2026)
# Hallazgo H8 del auditor de la pieza C: las reglas usan los nombres que publicó la pieza C (manifiesto_s3_gasto.json):
# rel_concepto_nodo (antes map_concepto_nodo, que es el curado), cobertura_por_anio (antes cobertura_anio), dim_producto y
# dim_actividad (antes dim_programa_anio y dim_nodo_anio). El acceso por tema es la macro gasto_tema('<tema_id>').
# Prueba de consistencia tabla_gasto_no_publicada: toda tabla o vista de gasto que nombre una regla R-GASTO-* está aquí;
# y estas listas deben coincidir con el manifiesto y con las vistas SQL cuando esos archivos existen.
TABLAS_GASTO_PUBLICADAS = ['dim_unidad_ejecutora', 'dim_inversion_ubicacion', 'dim_programa', 'dim_producto', 'dim_actividad',
                           'dim_concepto', 'rel_concepto_grupo', 'rel_concepto_nodo', 'rel_linaje', 'rel_programa_politica',
                           'dim_programa_social', 'rel_programa_social_ejecutora', 'rel_programa_social_financiamiento',
                           'cobertura_por_anio', 'dim_tema_gasto', 'dim_glosario_gasto', 'fact_gasto_territorial']
VISTAS_GASTO_PUBLICADAS = ['v_gasto_tematico', 'v_gasto_consolidado', 'v_gasto_fondos_por_identificar', 'v_gasto_concepto',
                           'v_gasto_tema_interna', 'gasto_tema']
TABLAS_GASTO_NO_PUBLICADAS = {  # nombradas por reglas, a propósito fuera del manifiesto del gasto
 'map_intencion_tema': 'tabla fija del validador; vive en reglas.json (R-GASTO-08b, parámetros)',
 'dim_modificacion_presupuestaria': 'futura; las reglas la condicionan a «cuando exista» (R-GASTO-05, 19)',
 'dim_inversion': 'detalle de inversiones de R-GASTO-14 y 17 (anteriores a esta pieza); aún no construida',
 'dim_ipc': 'deflactor (R-GASTO-12); otra capa de la biblioteca',
 'dim_ubigeo_historico': 'capa territorial (S1)',
}

# ================================================================ decisiones del dueño del 8/10/2026 (E1: reglas)
# docs/decisiones.md (filas del 8/10/2026) y 00_proyecto/analisis_2026-10-08/ (README, catalogo/, gasto/ y
# auditoria/). Informe: 00_proyecto/analisis_2026-10-08/implementacion/e1_reglas/implementacion.md. Cambios: R-ENC-08
# (toda encuesta muestral; inferencia_verificada por fuente × año × módulo), R-DEP-01 (sin MEF-PPR; compuerta leída solo
# del catálogo), R-GASTO-08 (nombres por año; línea «transferido a municipalidades» de Llamkasun), R-GASTO-03 (advertencia
# de mixtas obligatoria en 5 funciones; línea aparte y aviso de sesgo de sede siempre), R-GASTO-07, 18 y 19 (sin foto
# mensual del PIM), más una nota en R-ENC-15.
_D8 = 'decisión del dueño, 8/10/2026'
def _ultimo(rid, ruta):  # último valor que CAMPOS_REGLAS fija para (regla, ruta)
    return [v for r_, c_, v in CAMPOS_REGLAS if (r_, c_) == (rid, ruta)][-1]
def _cambia(texto, viejo, nuevo):  # reemplazo que debe ocurrir exactamente una vez
    assert texto.count(viejo) == 1, viejo[:50]
    return texto.replace(viejo, nuevo)
REF_ANALISIS_D8 = {'titulo': 'Pregunta al Perú – Análisis para decidir, 8/10/2026 (catálogo, gasto y auditoría)', 'url': None,
                   'ruta': '00_proyecto/analisis_2026-10-08/README.md'}

# -- 1. R-ENC-08: toda encuesta muestral (aplica_a.fuentes vacía). tipo_medida y base_geografica también quedan vacías: con
#    la semántica de aplica_a, 'prevalencia' dejaría fuera los promedios de ENAHO (ingreso, gasto) y los puntajes de ENLA,
#    y 'muestra' los indicadores construidos por residencia; el riesgo de publicar un supuesto como cifra departamental es
#    el mismo en todos esos casos.
CAMPOS_REGLAS += [
 ('R-ENC-08', 'enunciado',
  'Una cifra de encuesta muestral se publica por debajo del nivel nacional solo si su nivel de inferencia está verificado '
  'en la ficha técnica de esa encuesta, año y módulo (inferencia_verificada). Sin esa verificación se publica solo la cifra '
  'nacional. Si la encuesta representa a usuarios de servicios o solo a algunas ciudades, se rotula así.'),
 ('R-ENC-08', 'aplica_a', {'naturaleza_dato': ['encuesta_muestral'], 'tipo_medida': [], 'base_geografica': [], 'fuentes': []}),
 ('R-ENC-08', 'condicion',
  "naturaleza_dato == 'encuesta_muestral' AND tipo_aplicacion != 'censal' (la ENLA censal va por R-ENC-16). nivel := nivel al "
  "que se publicaría la cifra después de R-ENC-06 y R-ENC-07 (incluye los dominios: Lima Metropolitana, área urbana o rural, "
  "región natural). Si nivel != 'nacional' AND NOT verificado(fuente, anio, modulo, nivel) → agregar_nivel a 'nacional'. "
  "verificado(f, a, m, n) := existe en el catálogo (catalogo/inferencia_verificada.csv) la fila (f, a, m), o (f, a, '*') "
  "si la ficha de ese año declara lo mismo para todos los módulos, con inferencia_verificada = true, la cita completa "
  "(cita_url, cita_documento y cita_ubicacion), n no más fino que nivel_maximo (parametros_globales.NIVEL_RANK) y, si n es "
  "un dominio, n en dominios_anuales y no en excepciones; sin fila, o con inferencia_verificada vacía o false → false."),
 ('R-ENC-08', 'parametros', {
  'nivel_maximo_sin_verificar': 'nacional',
  'registro_inferencia_verificada': {
   'donde': 'catalogo/inferencia_verificada.csv (fuente curada: catalogo/scripts/inferencia_verificada.csv; esquema en docs/especificaciones/catalogo.md)',
   'llave': ['fuente', 'anio', 'modulo'],
   'modulo_todos': "'*': todos los módulos de esa encuesta y año, solo si la ficha declara lo mismo para todos",
   'campos_que_usa_la_regla': ['inferencia_verificada', 'nivel_maximo', 'dominios_anuales', 'excepciones', 'cita_url',
                               'cita_documento', 'cita_ubicacion'],
   'sin_registro': 'false: la cifra se publica solo a nivel nacional'},
  'verificar_antes_del_mvp': {'INEI-ENDES': '2015–2025: nivel departamental y dominios de R-ENC-07',
                              'INEI-ENAHO': '2015–2025: nivel departamental y dominios de R-ENC-07',
                              'MINEDU-UMC-ENLA': 'años y grados de aplicación muestral (R-ENC-15): region_umc'},
  'decision': _D8}),
 ('R-ENC-08', 'implementacion',
  'El validador lee inferencia_verificada.csv del catálogo por (fuente, año, módulo). La compuerta de ingesta no la exige, pero '
  'sin registro la cifra sale solo a nivel nacional. tipo_medida y base_geografica no restringen la regla: el riesgo de '
  'publicar un supuesto como cifra departamental es el mismo para una proporción, un promedio (ingreso, puntaje) o un '
  'total, y para indicadores construidos por residencia o por muestra.'),
 ('R-ENC-08', 'casos_borde',
  'Encuestas con inferencia distinta por módulo o cuestionario (ENSUSALUD, ENAPRES): un registro por módulo. Diseño no '
  'probabilístico (p. ej., ediciones remotas por autoselección): bloquear toda cifra (revisión humana). [PR-07] La '
  'verificación es por (fuente, año, módulo) con la cita de la ficha técnica de ese año: verificar una edición no verifica '
  'las demás. Antes del MVP: ENDES y ENAHO 2015–2025 (departamento y dominios) y la ENLA en sus años y grados muestrales. '
  'Orden en la etapa 2: R-ENC-06 baja al nivel de inferencia declarado en el catálogo y R-ENC-07 fija el dominio; R-ENC-08 '
  'exige además que ese nivel esté verificado. ENLA: R-ENC-15 fija el techo (region_umc) y no reemplaza la verificación; '
  'hace falta el registro de la ENLA por año y grado con la cita del informe técnico de la UMC. La aplicación censal '
  '(R-ENC-16) no es muestral y no entra en esta regla. Las desagregaciones que no son territorio ni dominio (sexo, edad, '
  'gestión de la escuela) no cambian el nivel: las cubren las reglas de precisión.'),
 ('R-ENC-08', 'ejemplo',
  "ENDES 2024, anemia en Apurímac: si existe el registro (INEI-ENDES, 2024, módulo de salud infantil) con nivel "
  "departamental y la cita de la ficha técnica, se publica el dato de Apurímac; si no, el nacional con el aviso. EPEN: hasta "
  "verificar su ficha, 'informalidad laboral en Apurímac' devuelve el dato nacional con el aviso."),
 ('R-ENC-08', 'referencias', [REF_ANALISIS_D8]),
]
AGREGADOS_REGLAS_R3 += [
 ('R-ENC-08', 'justificacion',
  ' La lista cerrada original (ENEDU, ENDO, EPEN, ENSUSALUD…) dejaba fuera a ENDES y ENAHO, las encuestas más usadas: el '
  'riesgo existe en toda encuesta muestral (' + _D8 + ').'),
 ('R-ENC-15', 'casos_borde',
  ' [Decisión del dueño, 8/10/2026] niveles_validos es el techo: para publicar por region_umc se exige además el registro '
  'inferencia_verificada de la ENLA por año y grado, con la cita del informe técnico de la UMC (R-ENC-08); sin él, solo el '
  'nivel nacional.'),
]
SOBRESCRITURAS_CONSCIENTES = globals().get('SOBRESCRITURAS_CONSCIENTES', set()) | {
 ('R-ENC-08', 'casos_borde'),  # traía [PR-07] (correcciones_prueba): se reescribe entero y PR-07 queda en hallazgos_prueba
 ('R-DEP-01', 'parametros.insumos_bloqueantes_mvp'),  # lista de la auditoría v1.1 (IMP-11): el dueño saca MEF-PPR (8/10/2026)
}

# -- 2. R-DEP-01: sin MEF-PPR; la compuerta se lee solo del catálogo (criterio «aprobada» del catálogo, 8/10/2026). Los
#    bloqueantes son los crudos de las tablas curadas del MVP fijados en curados/insumos.lock.yaml: dim_ubigeo_historico
#    (manifiesto_s1_territorio), fact_poblacion (manifiesto_s2_poblacion) y dim_ipc (BCRP-IPC-LIMA); RENIEC sigue como contraste.
BLOQUEANTES_MVP_D8 = ['BCRP-IPC-LIMA', 'GITHUB-UBIGEO-PERU-AUMENTADO', 'INEI-CPV2017', 'INEI-DIRECTORIO-MUNICIPALIDADES',
                      'INEI-PNDA-UBIGEOS', 'INEI-PROYECCIONES-DEPARTAMENTAL-EDAD', 'INEI-PROYECCIONES-DISTRITAL-2018-2022',
                      'INEI-PROYECCIONES-POBLACION-DISTRITAL', 'PROPIO-ESTADISTICAS-SOCIALES-2020']
TABLAS_CURADAS_BLOQUEANTES_D8 = {  # tabla curada → manifiesto de la capa 0 (o lista fija de insumos crudos)
 'dim_ubigeo_historico': 'manifiesto_s1_territorio.json', 'fact_poblacion': 'manifiesto_s2_poblacion.json',
 'dim_ipc': ['BCRP-IPC-LIMA']}
CAMPOS_REGLAS += [
 ('R-DEP-01', 'enunciado',
  'Cada indicador declara todos sus insumos (numerador, denominador y tablas curadas). Si alguno no figura como «aprobada» '
  'en el catálogo de fuentes, la cifra no se calcula.'),
 ('R-DEP-01', 'parametros.insumos_bloqueantes_mvp', BLOQUEANTES_MVP_D8),
 ('R-DEP-01', 'parametros.criterio_aprobada',
  'Lo fija el catálogo (' + _D8 + '): «aprobada» si pasó la prueba de humo, o si tiene una captura con su última '
  'verificación en «ok» y, cuando la capa 0 la usa, todas sus huellas de curados/insumos.lock.yaml coinciden.'),
 ('R-DEP-01', 'parametros.origen_bloqueantes',
  'Crudos de las tablas curadas del MVP fijados en curados/insumos.lock.yaml: dim_ubigeo_historico '
  '(manifiesto_s1_territorio), fact_poblacion (manifiesto_s2_poblacion) y dim_ipc (BCRP-IPC-LIMA). '
  'RENIEC-POBLACION-IDENTIFICADA queda como contraste.'),
 ('R-DEP-01', 'parametros.retirados', {
  'MEF-PPR-PROGRAMAS-PRESUPUESTALES': 'no lo usa la capa 0: dim_tema_gasto sale del código de programa de la base de gasto '
                                      'y de una tabla curada (' + _D8 + '); queda como referencia documental'}),
 ('R-DEP-01', 'implementacion',
  'indicador.insumos: lista de IDs del catálogo y de tablas curadas. El validador consulta compuerta_ingesta de cada uno '
  'en el catálogo publicado (catalogo/catalogo_fuentes.json), única fuente de verdad, antes de la etapa 1; no lee el '
  'bloque catalogo de las recetas ni otra copia de la lista. Las listas de bloqueantes de la ingesta (BLOQUEAN_MVP) deben '
  'leerse de insumos_bloqueantes_mvp.'),
 ('R-DEP-01', 'referencias', [REF_ANALISIS_D8,
  {'titulo': 'Pregunta al Perú – Catálogo de fuentes: validación y propuesta de actualización (8/10/2026)', 'url': None,
   'ruta': '00_proyecto/analisis_2026-10-08/catalogo/informe.md'}]),
]
PARCHES_REGLAS_R3 += [
 ('R-DEP-01', 'Extiende a todos los insumos la decisión ya tomada de no ingerir sin prueba de humo.',
  'Extiende a todos los insumos la decisión de no usar una fuente que no esté aprobada en el catálogo.'),
]

# -- 3. Nombres MEF → vigente, resueltos por año (coherente con curados/capa0/trazabilidad/programas_sociales.yaml y la
#    pieza C). Si el nombre cambió en el año: el de más días y, entre paréntesis, el otro con el mes y el año del cambio.
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'setiembre', 'octubre', 'noviembre', 'diciembre']  # como trazabilidad.py
MEF_VS_VIGENTE_D8 = {
 'empleo_temporal': {
  'programa_social': 'empleo_temporal', 'ue': '1066', 'nombre_mef': 'PROGRAMA PARA LA GENERACION DE EMPLEO SOCIAL INCLUSIVO TRABAJA PERU (PP 0073)',
  'por_anio': {'2023': 'Lurawi Perú (Llamkasun Perú desde agosto de 2023)', '2024': 'Llamkasun Perú', '2025': 'Llamkasun Perú'},
  'normas': 'DS 002-2022-TR (Trabaja Perú → Lurawi Perú); DS 009-2023-TR, El Peruano 9/8/2023 (Lurawi Perú → Llamkasun Perú)'},
 'warmi_nan': {
  'programa_social': 'warmi_nan', 'ue': '1232', 'nombre_mef': 'PROGRAMA NACIONAL CONTRA LA VIOLENCIA FAMILIAR Y SEXUAL (PNCVFS)',
  'por_anio': {'2023': 'AURORA', '2024': 'AURORA', '2025': 'Warmi Ñan (AURORA hasta el 2/5/2025)'},
  'normas': 'AURORA: norma de creación por verificar (nombre en uso en 2021 y 2023); DS 003-2025-MIMP, 3/5/2025 (Warmi Ñan)'},
 'alimentacion_escolar': {
  'programa_social': 'alimentacion_escolar', 'ue': '1456', 'nombre_mef': 'PROGRAMA NACIONAL DE ALIMENTACION ESCOLAR QALI WARMA (2025: … COMUNITARIA WASI MIKUNA)',
  'por_anio': {'2023': 'Qali Warma', '2024': 'Qali Warma (Wasi Mikuna desde el 4/12/2024)', '2025': 'Wasi Mikuna'},
  'normas': 'DS 008-2012-MIDIS (Qali Warma); DS 010-2024-MIDIS, 4/12/2024 (Wasi Mikuna)'},
 'pae': {
  'programa_social': 'pae', 'ue': '1786', 'nombre_mef': 'programa nuevo desde 2025', 'por_anio': {'2025': 'Programa de Alimentación Escolar (PAE)'},
  'normas': 'DS 008-2025-MIDIS, 16/8/2025'},
}
NOMBRES_PROGRAMAS_D8 = dict(NOMBRES_PROGRAMAS,
 regla=('Al usuario se le muestra el nombre propio vigente en el año de la cifra y, entre paréntesis, el nombre que usa el '
        'MEF cuando difiere. Si el nombre cambió durante el año, se usa el que estuvo vigente más días y se agrega entre '
        'paréntesis el otro con la fecha del cambio (una norma rige desde el día siguiente a su publicación): el mes y el '
        'año cuando la tabla curada de programas sociales lo marca (rotulo_fecha = mes; así decidió el dueño para 2023: «Lurawi Perú '
        '(Llamkasun Perú desde agosto de 2023)»), si no el día. Los nombres se resuelven por año con mef_vs_vigente, '
        'que debe coincidir con dim_programa_social.'),
 mef_vs_vigente=MEF_VS_VIGENTE_D8)

# -- 6. ps_empleo_temporal (Lurawi / Llamkasun): siempre con la línea «transferido a municipalidades» (los datos los prepara
#    la capa de gasto; aquí solo el texto y la condición).
PROGRAMAS_SOCIALES_D8 = {
 'ps_empleo_temporal': {
  'linea_obligatoria': 'transferido a municipalidades',
  'que_es': ('transferencias de la UE 1066 (Lurawi / Llamkasun) a municipalidades: no entran al tema (R-GASTO-05) y se '
             'muestran siempre en una línea aparte, que no se suma'),
  'motivo': ('el gasto final del tema es solo el 6–8 % del programa: 40,6 / 34,5 / 37,6 millones frente a 605,6 / 535,7 / '
             '409,0 millones transferidos a municipalidades en 2023–2025'),
  'sin_dato': 'si falta el monto transferido del mismo año y territorio, la cifra del tema no se publica',
  'decision': _D8}}
CAMPOS_REGLAS += [
 ('R-GASTO-08', 'parametros.nombres', NOMBRES_PROGRAMAS_D8),
 ('R-GASTO-08', 'parametros.temas_ps', PROGRAMAS_SOCIALES_D8),
 ('R-GASTO-08', 'condicion', _ultimo('R-GASTO-08', 'condicion') + (
  " Nombre por año := parametros.nombres.mef_vs_vigente[id_programa_social].por_anio[anio] (llave: el programa social, "
  "identificado por su UE; no el nombre del MEF, cuya escritura cambia entre años) = dim_programa_social.etiqueta. "
  "Tema ps_empleo_temporal → toda cifra lleva la línea aparte «transferido a municipalidades» (v_programa_social_linea_aparte: "
  "transferencias del programa a municipalidades, mismo año y territorio), que no se suma al tema ni se combina con "
  "gasto_tema en la misma consulta (guardia G6); si falta ese monto, la cifra del tema no se publica.")),
 ('R-GASTO-08', 'mensaje_usuario', _ultimo('R-GASTO-08', 'mensaje_usuario') + (
  ' (Llamkasun, tema ps_empleo_temporal) «Transferido a municipalidades: S/ {transferido} millones. Ese dinero lo gastan '
  'las municipalidades en obras de empleo temporal y no se suma a la cifra del programa.»')),
]

# -- 4. R-GASTO-03: advertencia de mixtas obligatoria en 5 funciones (códigos y nombres del MEF verificados en el CSV de
#    gasto 2023 y en fact_gasto_territorial, que guarda el nombre); línea aparte de referencia nacional y aviso de sesgo de
#    sede siempre con la cifra de Lima.
FUNCIONES_MEF = {'01': 'LEGISLATIVA', '02': 'RELACIONES EXTERIORES', '03': 'PLANEAMIENTO, GESTION Y RESERVA DE CONTINGENCIA',
                 '04': 'DEFENSA Y SEGURIDAD NACIONAL', '05': 'ORDEN PUBLICO Y SEGURIDAD', '06': 'JUSTICIA', '07': 'TRABAJO',
                 '08': 'COMERCIO', '09': 'TURISMO', '10': 'AGROPECUARIA', '11': 'PESCA', '12': 'ENERGIA', '13': 'MINERIA',
                 '14': 'INDUSTRIA', '15': 'TRANSPORTE', '16': 'COMUNICACIONES', '17': 'AMBIENTE', '18': 'SANEAMIENTO',
                 '19': 'VIVIENDA Y DESARROLLO URBANO', '20': 'SALUD', '21': 'CULTURA Y DEPORTE', '22': 'EDUCACION',
                 '23': 'PROTECCION SOCIAL', '24': 'PREVISION SOCIAL', '25': 'DEUDA PUBLICA'}
FUNCIONES_MIXTAS_OBLIGATORIA = {k: FUNCIONES_MEF[k] for k in ('05', '06', '15', '20', '23')}
CAMPOS_REGLAS += [
 ('R-GASTO-03', 'parametros.lima.linea_aparte',
  "referencia_nacional AND departamento_atribucion = '15' (no se suma); va siempre con toda cifra de Lima, también cuando "
  "es 0 (" + _D8 + ")"),
 ('R-GASTO-03', 'parametros.lima.advertencia_mixtas',
  'Obligatoria cuando la cifra incluye gasto de las funciones de funciones_advertencia_obligatoria; en las demás, solo si '
  'hay gasto de ejecutoras mixtas con meta en Lima en el mismo tema, año y fase. Hasta separar por producto las ejecutoras '
  'mixtas (decisiones del dueño del 7/10 y del 8/10/2026).'),
 ('R-GASTO-03', 'parametros.lima.funciones_advertencia_obligatoria', FUNCIONES_MIXTAS_OBLIGATORIA),
 ('R-GASTO-03', 'parametros.lima.aviso_sesgo_sede', {
  'siempre': True, 'pct_sede': 38,
  'que_mide': ('parte del gasto que se asigna por el departamento de la meta (ministerios, programas y gobiernos regionales) '
               'que es del Gobierno Nacional con meta en Lima: 37,4 / 37,3 / 38,2 % en 2023–2025'),
  'fuente': '00_proyecto/analisis_2026-10-08/gasto/sesgo_sede.csv', 'actualizar': 'recalcular al cargar un año nuevo'}),
 ('R-GASTO-03', 'mensaje_usuario',
  '(distrito o provincia) «Incluye el gasto de la municipalidad y de los proyectos de inversión ubicados aquí, de cualquier '
  'entidad. No incluye lo que el ministerio y el gobierno regional gastan en servicios (como personal de salud). En '
  '{departamento}, el {pct} % del gasto en este tema puede ubicarse por distrito o provincia.» '
  '(cifras de Lima, siempre, en una línea aparte) «Aparte, sin sumar: S/ {refnac} millones de institutos de referencia '
  'nacional ubicados en Lima, que atienden a pacientes de todo el país.» (si es 0) «Aparte: los institutos de referencia '
  'nacional ubicados en Lima no tienen gasto en este tema.» '
  '(cifras de Lima, siempre) «Muchas entidades nacionales tienen su sede en Lima: cerca del {pct_sede} % del gasto que el '
  'Estado ubica por departamento lo registran entidades nacionales en Lima. Lo que atiende a todo el país no se cuenta '
  'aquí. Comparar Lima con otras regiones tiene límites.» '
  '(cifras de Lima; obligatoria en seguridad, justicia, transporte, salud y protección social) «El gasto en Lima no incluye '
  'la parte local de programas nacionales ({programas_mixtos}), porque sus cuentas no separan Lima del resto del país.»'),
]
AGREGADOS_REGLAS_R3 += [
 ('R-GASTO-03', 'implementacion',
  ' [' + _D8 + '] Funciones con advertencia de mixtas obligatoria: FUNCION ∈ {05 ORDEN PUBLICO Y SEGURIDAD, 06 JUSTICIA, '
  '15 TRANSPORTE, 20 SALUD, 23 PROTECCION SOCIAL} (código y nombre del MEF; fact_gasto_territorial.funcion guarda el '
  'nombre); para un tema de otra cadena, si alguna fila de la cifra cae en esas funciones. {programas_mixtos} := las '
  'ejecutoras mixtas con más gasto con meta en Lima en el mismo tema y año (hasta 3), con su nombre vigente (R-GASTO-08); '
  'si no hay ninguna, las de la misma función y año; si tampoco hay, se usa el texto sin lista (parametros.lima.'
  'programas_mixtos_respaldo). '
  'pct_sede sale de parametros.lima.aviso_sesgo_sede.'),
]
PARCHES_REGLAS_R3 += [
 ('R-GASTO-03', '→ línea aparte si refnac > 0, nunca sumada a la cifra. Toda cifra de Lima → advertencia de ejecutoras '
                'mixtas, hasta que se separen por producto (decisión del 7/10/2026).',
  '→ línea aparte siempre (también si refnac = 0), nunca sumada a la cifra. Toda cifra de Lima → aviso de sesgo de sede. '
  'Advertencia de ejecutoras mixtas: obligatoria si alguna fila de la cifra tiene FUNCION ∈ '
  'funciones_advertencia_obligatoria (seguridad, justicia, transporte, salud y protección social); en otro caso, si hay '
  'devengado de ejecutora_mixta con departamento_meta = \'15\' en el mismo tema, año y fase; hasta que se separen por '
  'producto (decisiones del 7/10 y del 8/10/2026).'),
]

# -- 5. Sin foto mensual del PIM (decisión del 8/10/2026, que deja sin efecto la del 7/10/2026): R-GASTO-07, 18 y 19 trabajan
#    con el PIM final del año; R-GASTO-19 se basa en el devengado mensual.
_SIN_FOTO = 'no hay fotos mensuales del PIM (' + _D8 + ', que deja sin efecto la del 7/10/2026)'
_P07 = dict(_ultimo('R-GASTO-07', 'parametros'))
_P07['denominador'] = {('mismo_mes' if k == 'mismo_mes_sin_fotos' else k): v for k, v in _P07['denominador'].items() if k != 'con_fotos'}
_P07['foto_pim_mensual'] = 'no disponible: ' + _SIN_FOTO
_NUEVA = {r_['id']: r_ for r_ in NUEVAS_GASTO_R2}
CAMPOS_REGLAS += [
 ('R-GASTO-07', 'enunciado', _cambia(_ultimo('R-GASTO-07', 'enunciado'),
  ' Cuando existan fotos mensuales propias del PIM (desde 2026), el avance al mismo mes se calcula con el PIM vigente a ese corte.',
  ' No hay fotos mensuales del PIM: el PIM vigente en un mes pasado no está disponible, así que la comparación al mismo mes '
  'lleva siempre su rótulo.')),
 ('R-GASTO-07', 'condicion', _cambia(_ultimo('R-GASTO-07', 'condicion'),
  ' Si existe foto_pim(anio, m) aprobada para todos los años comparados → avance_m = Σ MONTO_DEVENGADO(MES_EJE ≤ m) / '
  'foto_pim(anio, m), sin el rótulo.', ' No se usa ningún PIM mensual: ' + _SIN_FOTO + '.')),
 ('R-GASTO-07', 'parametros', _P07),
 ('R-GASTO-07', 'implementacion', _cambia(_ultimo('R-GASTO-07', 'implementacion'),
  'Fotos del PIM: copia fechada del archivo del año en curso en cada descarga (desde 2026); resultado.denominador_avance '
  'indica cuál se usó.',
  'resultado.denominador_avance indica cuál se usó (PIM final o PIM de la última descarga).')),
 ('R-GASTO-18', 'condicion', _cambia(_NUEVA['R-GASTO-18']['condicion'],
  'neto := PIM − PIA de la entidad × tema (mes 0; año cerrado o última descarga).',
  'neto := PIM − PIA de la entidad × tema, con el PIA y el PIM finales del año (mes 0); en el año en curso, el PIM de la '
  'última descarga, rotulado «parcial» con su fecha (R-GASTO-07). No se usa ningún PIM mensual: ' + _SIN_FOTO + '.')),
 ('R-GASTO-18', 'parametros.pim_usado', 'PIM final del año (mes 0); en el año en curso, el de la última descarga con su fecha'),
 ('R-GASTO-19', 'condicion', _cambia(_NUEVA['R-GASTO-19']['condicion'],
  'Afirmar «llegó en el último trimestre» o una fecha → solo con dim_modificacion_presupuestaria o con la serie propia de '
  'fotos mensuales del PIM; si no, bloquear esa frase.',
  'PIA y PIM := los finales del año (mes 0); el único dato mensual es el devengado (primer mes con devengado de cada '
  'línea). Afirmar «llegó en el último trimestre» o una fecha → solo con dim_modificacion_presupuestaria; sin ella, '
  'bloquear esa frase; ' + _SIN_FOTO + '.')),
 ('R-GASTO-19', 'parametros.fecha_de_llegada', 'solo con dim_modificacion_presupuestaria; fotos mensuales del PIM: no disponibles (' + _D8 + ')'),
 ('R-GASTO-19', 'parametros.dato_mensual', 'devengado de los meses 1–12; PIA y PIM finales del año (mes 0)'),
]
HALLAZGOS_D8 = {
 'R-ENC-08': ['toda encuesta muestral; inferencia_verificada por fuente × año × módulo'],
 'R-ENC-15': ['ENLA: el techo region_umc exige el registro inferencia_verificada'],
 'R-DEP-01': ['compuerta leída solo del catálogo; MEF-PPR fuera de los bloqueantes'],
 'R-GASTO-03': ['mixtas: advertencia obligatoria en 5 funciones; línea aparte y aviso de sesgo de sede siempre'],
 'R-GASTO-07': ['sin foto mensual del PIM'], 'R-GASTO-18': ['sin foto mensual del PIM'],
 'R-GASTO-19': ['sin foto mensual del PIM; se basa en el devengado mensual'],
 'R-GASTO-08': ['nombres por año («Lurawi Perú (Llamkasun Perú desde agosto de 2023)»)',
                'ps_empleo_temporal con la línea «transferido a municipalidades»'],
}
CAMPOS_D8 = [  # reemplazan la entrada del mismo nombre en el diccionario
 ('inferencia_verificada', 'catálogo (fuente × año × módulo)', 'inferencia_verificada, cita_ficha_inferencia',
  'Fila de catalogo/inferencia_verificada.csv por fuente, año y módulo («*» = todos): nivel más fino y dominios anuales según la ficha técnica, excepciones y cita (URL, documento, sección y página). Sin fila verificada, la cifra de una encuesta muestral se publica solo a nivel nacional (R-ENC-08).'),
 ('denominador_avance', 'cifra', '—', 'PIM final o PIM de la última descarga (R-GASTO-07); no hay foto mensual del PIM.'),
]
AJUSTES_CONSOLIDACION_D8 = {  # reemplazan la nota de consolidación (AJUSTES de consolida_reglas.py)
 'R-ENC-08': ('Requiere el registro inferencia_verificada por (fuente, año, módulo) en el catálogo. Las verificaciones '
              'anteriores (ENAHO 2024, ENDES 2024, ENAPRES por confirmar) cuentan solo cuando se registren con su cita.'),
}
DECISIONES_D8 = [  # (id, tema, opciones, recomendación, reglas, decisión)
 ('D19', 'R-ENC-08: a qué encuestas se aplica', 'Lista cerrada de encuestas poco usadas o toda encuesta muestral.', 'Toda encuesta muestral, con inferencia_verificada por fuente × año × módulo.', 'R-ENC-08, R-ENC-15', 'Adoptada (dueño, 8/10/2026). Se verifican ENDES y ENAHO 2015–2025 (departamental) y la ENLA.'),
 ('D20', 'Compuerta de R-DEP-01', 'Prueba de humo o captura verificada con huellas del lock; lista de bloqueantes.', 'Lee solo el catálogo; MEF-PPR fuera de los bloqueantes.', 'R-DEP-01', 'Adoptada (dueño, 8/10/2026).'),
 ('D21', 'Nombres de programas en años de cambio', '«Lurawi Perú (Llamkasun Perú desde agosto de 2023)» o «Llamkasun Perú».', 'El de más días en el año, con el otro entre paréntesis.', 'R-GASTO-08', 'Adoptada (dueño, 8/10/2026); los nombres MEF → vigente se resuelven por año.'),
 ('D22', 'Ejecutoras mixtas y cifra de Lima', 'Advertencia en toda cifra de Lima u obligatoria por función; línea aparte y sesgo de sede.', 'Obligatoria en seguridad, protección social, justicia, transporte y salud; cifra de Lima siempre con la línea aparte y el aviso de sesgo de sede.', 'R-GASTO-03', 'Adoptada (dueño, 8/10/2026).'),
 ('D23', 'Foto mensual del PIM', 'Guardar una foto mensual desde 2026 o no guardarla.', 'No guardarla.', 'R-GASTO-07, 18, 19', 'Adoptada (dueño, 8/10/2026): deja sin efecto la del 7/10/2026; las reglas usan el PIM final del año.'),
 ('D24', 'Temas ps_ (programas sociales)', 'Aprobar los 13 temas con o sin condiciones.', 'Aprobar con condiciones.', 'R-GASTO-08', 'Adoptada (dueño, 8/10/2026): ps_empleo_temporal muestra siempre la línea «transferido a municipalidades»; Jóvenes Productivos y el aumento del PCA en 2025 van en los datos.'),
]
FECHA_ACTUALIZACION = ('2026-10-08', '8 de octubre de 2026')

# Coordinación con la capa de gasto (E3, 8/10/2026): la vista v_programa_social_linea_aparte ya está en vistas_gasto_temas.sql;
# la tabla rel_programa_social_linea_aparte entra al manifiesto en la próxima construcción de la capa 0. Mientras tanto la
# prueba manifiesto_gasto_distinto admite que esté o no esté; luego hay que moverla a TABLAS_GASTO_PUBLICADAS.
VISTAS_GASTO_PUBLICADAS = VISTAS_GASTO_PUBLICADAS + ['v_programa_social_linea_aparte']
TABLAS_GASTO_EN_CONSTRUCCION = {'rel_programa_social_linea_aparte': 'capa de gasto (E3, 8/10/2026): línea aparte de los programas sociales'}

# ---------------------------------------------------------------- cierre E1 tras E3 (8/10/2026, commits f4db168 y c8e82b3)
# curados/generadores/e3_gasto/implementacion.md: fact v1.4.0 con obra_sede_nacional (lista curada
# curados/capa0/obras_sede_nacional.yaml) y alcance lima_departamento (INPE Oficina Regional Lima: sin ámbito, ubigeo
# 150000 «Lima sin separar»); rel_programa_social_linea_aparte ya está en el manifiesto.
TABLAS_GASTO_PUBLICADAS = TABLAS_GASTO_PUBLICADAS + ['rel_programa_social_linea_aparte']
TABLAS_GASTO_EN_CONSTRUCCION = {}
_CUENTA_LIMA_D8 = ("cuenta_en_lima (columna de fact_gasto_territorial; el validador la lee, no la recalcula) := "
                   "departamento_atribucion = '15' AND NOT referencia_nacional AND NOT obra_sede_nacional AND NOT "
                   "(nivel_atribucion = 'departamento_meta' AND departamento_meta = '15' AND nivel_gobierno = 'E' AND "
                   "alcance_ejecutora = 'nacional'), con el alcance_ejecutora de la fila de la fact (vale 'no_aplica' "
                   "fuera de departamento_meta: las obras ubicadas por CUI de ejecutoras nacionales se quedan en Lima, "
                   "salvo las de sede)")
AGREGADOS_REGLAS_R3 += [
 ('R-GASTO-01', 'condicion',
  ' (e) [E3, 8/10/2026] Alcance lima_departamento (INPE Oficina Regional Lima, que cubre penales de Lima Metropolitana, '
  'Lima Provincias, Callao, Ica y Áncash): sin ámbito; sus filas con meta 15 van a ubigeo_atribucion 150000 («Lima sin '
  'separar»): cuentan en el departamento de Lima, no en Lima Metropolitana ni en Lima Región.'),
 ('R-GASTO-03', 'condicion',
  ' [E3, 8/10/2026] ' + _CUENTA_LIMA_D8 + '. Las filas con alcance lima_departamento (ubigeo 150000) entran en la cifra '
  'del departamento 15, no en las de Lima Metropolitana ni Lima Región. Las obras de sede o función nacional '
  '(obra_sede_nacional, lista curada obras_sede_nacional.yaml) salen de la cifra de Lima, también las de una ejecutora '
  'mixta (su advertencia las cubre); los colegios y hospitales de residentes se quedan.'),
]
PARCHES_REGLAS_R3 += [
 ('R-GASTO-03', 'sin el alcance nacional y sin los centros de referencia_nacional (INEN, INSN San Borja), incluidas sus obras.',
  'sin el alcance nacional, sin los centros de referencia_nacional (INEN, INSN San Borja), incluidas sus obras, y sin las '
  'obras de sede o función nacional (obra_sede_nacional; E3, 8/10/2026). El alcance lima_departamento (INPE Oficina '
  'Regional Lima) no tiene ámbito: con meta 15 va a 150000 («Lima sin separar»).'),
]
CAMPOS_REGLAS += [
 ('R-GASTO-03', 'parametros.lima.cifra',
  'cuenta_en_lima = true (atribuida al dpto 15, sin alcance nacional, sin referencia_nacional y sin obra_sede_nacional); '
  'lima_departamento → solo en el total del departamento («Lima sin separar», 150000)'),
]
CAMPOS_D8 += [
 ('cuenta_en_lima', 'fila de gasto', 'exclusión por alcance_ejecutora = nacional (GA-01)',
  'La fila entra en las cifras del departamento 15 (y, según su ámbito, de Lima Metropolitana o Lima Región): atribuida al dpto 15, sin alcance nacional, sin referencia nacional y sin obras de sede o función nacional (obra_sede_nacional). El alcance lima_departamento cuenta solo en el departamento («Lima sin separar», 150000) (R-GASTO-03).'),
 ('obra_sede_nacional', 'fila de gasto', '—',
  'Obra de sede o de función nacional de una ejecutora nacional (lista curada obras_sede_nacional.yaml): sale de la cifra de Lima (R-GASTO-03).'),
]
HALLAZGOS_D8['R-GASTO-01'] = ['alcance lima_departamento (150000, «Lima sin separar»)']
HALLAZGOS_D8['R-GASTO-03'] = HALLAZGOS_D8['R-GASTO-03'] + ['cuenta_en_lima sin obras de sede nacional; alcance lima_departamento']

# ---------------------------------------------------------------- correcciones tras la auditoría de E1 (8/10/2026)
# 00_proyecto/analisis_2026-10-08/implementacion/e1_reglas/auditoria/auditoria.md (H1–H10).
# H1. region_umc (ENLA) entra al vocabulario de niveles con el rango del departamento (una región por DRE).
NIVEL_RANK_D8 = {'region_umc': 4}
NOTA_NIVEL_RANK_D8 = ' region_umc (ENLA: región de la UMC, una por DRE) tiene el rango del departamento.'
# H2. Mismo alcance en R-ENC-06, 07 y 15 que en R-ENC-08: el riesgo es el mismo para una proporción, un promedio o un total.
CAMPOS_REGLAS += [(r_, 'aplica_a.' + k_, []) for r_ in ('R-ENC-06', 'R-ENC-07', 'R-ENC-15') for k_ in ('tipo_medida', 'base_geografica')]
# H2, H3 y H9. R-ENC-08 baja al nivel más fino verificado (no siempre a nacional), lee excluye_departamentos y aviso, y el
# dominio se compara por dim_dominio (dominios_anuales es la cita, no la llave).
AVISOS_INFERENCIA = {'entrevista_telefonica': 'En {anio} la encuesta se hizo en parte por teléfono por la pandemia; la cifra no es del todo comparable con la de otros años.'}
_P08 = _ultimo('R-ENC-08', 'parametros')
_P08['registro_inferencia_verificada']['campos_que_usa_la_regla'] = ['inferencia_verificada', 'nivel_maximo', 'dominios_anuales',
    'excepciones', 'excluye_departamentos', 'aviso', 'cita_url', 'cita_documento', 'cita_ubicacion']
_P08['avisos'] = AVISOS_INFERENCIA
_P08['excluye_departamentos'] = "códigos de 2 dígitos separados por «;» (ENAHO: 07, el Callao, que va en el dominio «Área Metropolitana de Lima y Callao»)"
CAMPOS_REGLAS += [
 ('R-ENC-08', 'condicion',
  "naturaleza_dato == 'encuesta_muestral' AND tipo_aplicacion != 'censal' (la ENLA censal va por R-ENC-16). nivel := nivel al "
  "que se publicaría la cifra después de R-ENC-06 y R-ENC-07 (incluye los dominios: Lima Metropolitana, área urbana o rural, "
  "región natural). fila := la de catalogo/inferencia_verificada.csv con llave (fuente, anio, modulo), o (fuente, anio, '*') "
  "si la ficha de ese año declara lo mismo para todos los módulos. verificado(n) := fila con inferencia_verificada = true, la "
  "cita completa (cita_url, cita_documento y cita_ubicacion), n no más fino que nivel_maximo (parametros_globales.NIVEL_RANK; "
  "region_umc tiene el rango del departamento), el departamento del territorio fuera de excluye_departamentos y, si n es un "
  "dominio, el dominio en dim_dominio para esa encuesta y año (R-ENC-07; dominios_anuales y excepciones son la cita, no la "
  "llave). Si nivel != 'nacional' AND NOT verificado(nivel) → agregar_nivel al nivel más fino verificado que contiene al "
  "territorio (departamento o dominio); si no hay ninguno, a 'nacional'. Departamento en excluye_departamentos (ENAHO: 07, "
  "el Callao) → su dominio de R-ENC-07 si está verificado; si no, 'nacional'. fila.aviso no vacío → se agrega el texto de "
  "parametros.avisos[aviso] junto a la cifra."),
 ('R-ENC-08', 'parametros', _P08),
 ('R-ENC-08', 'mensaje_usuario', _ultimo('R-ENC-08', 'mensaje_usuario') +
  ' (año con entrevista telefónica) «' + AVISOS_INFERENCIA['entrevista_telefonica'] + '»'),
]
# H6. Los crudos del gasto del piloto también bloquean (manifiesto_s3_gasto).
BLOQUEANTES_MVP_D8_V2 = sorted(BLOQUEANTES_MVP_D8 + ['MEF-DA-PRESUPUESTO-EJECUCION-GASTO', 'MEF-DETALLE-INVERSIONES'])
TABLAS_CURADAS_BLOQUEANTES_D8['fact_gasto_territorial'] = 'manifiesto_s3_gasto.json'
CAMPOS_REGLAS += [
 ('R-DEP-01', 'parametros.insumos_bloqueantes_mvp', BLOQUEANTES_MVP_D8_V2),
 ('R-DEP-01', 'parametros.origen_bloqueantes',
  'Crudos de las tablas curadas del MVP fijados en curados/insumos.lock.yaml: dim_ubigeo_historico '
  '(manifiesto_s1_territorio), fact_poblacion (manifiesto_s2_poblacion), dim_ipc (BCRP-IPC-LIMA) y fact_gasto_territorial '
  '(manifiesto_s3_gasto: gasto MEF y detalle de inversiones). RENIEC-POBLACION-IDENTIFICADA queda como contraste: en la '
  'capa territorial su uso es opcional. SIEN y RENIPRESS se declaran como insumos de sus indicadores.'),
]
# H4 (fórmula) y H5 (respaldo de mixtas) se corrigieron arriba en su bloque; aquí el parámetro, la cifra de control y el texto.
CAMPOS_REGLAS += [
 ('R-GASTO-03', 'parametros.lima.cifra', 'columna cuenta_en_lima de fact_gasto_territorial (fórmula en la condición); '
  'lima_departamento → solo en el total del departamento («Lima sin separar», 150000)'),
 ('R-GASTO-03', 'parametros.lima.control_cuenta_en_lima',
  '76 172,4 millones en 2023–2025, devengado sin transferencias (fact v1.4.0, commit e6d6a57); la fórmula de la condición '
  'da 0 filas distintas de la columna (verificado con DuckDB el 8/10/2026)'),
 ('R-GASTO-03', 'parametros.lima.programas_mixtos_respaldo',
  'si no hay mixtas con gasto con meta en Lima en el mismo tema y año: las de la misma función y año; si tampoco hay, el '
  'texto sin lista'),
 ('R-GASTO-03', 'mensaje_usuario', _cambia(_cambia(_ultimo('R-GASTO-03', 'mensaje_usuario'),
  'Muchas entidades nacionales tienen su sede en Lima: cerca del {pct_sede} % del gasto que el Estado ubica por departamento lo '
  'registran entidades nacionales en Lima.',
  'Cerca del {pct_sede} % del gasto de ministerios, programas y gobiernos regionales que se ubica por departamento lo '
  'registran entidades nacionales con sede en Lima.'),
  'porque sus cuentas no separan Lima del resto del país.»',
  'porque sus cuentas no separan Lima del resto del país.» (sin mixtas en el tema ni en la función) «El gasto en Lima '
  'no incluye la parte local de algunos programas nacionales, porque sus cuentas no separan Lima del resto del país.»')),
]
HALLAZGOS_D8['R-ENC-06'] = ['auditoría E1, H2: alcance igual al de R-ENC-08 (promedios y totales)']
HALLAZGOS_D8['R-ENC-07'] = ['auditoría E1, H2: alcance igual al de R-ENC-08 (promedios y totales)']
HALLAZGOS_D8['R-ENC-15'] = HALLAZGOS_D8['R-ENC-15'] + ['auditoría E1, H1 y H2: region_umc en NIVEL_RANK; alcance igual al de R-ENC-08']
HALLAZGOS_D8['R-ENC-08'] = HALLAZGOS_D8['R-ENC-08'] + ['auditoría E1, H2, H3 y H9: nivel más fino verificado; excluye_departamentos y aviso']

# ================================================================ Lima en tres ámbitos (decisiones del dueño, 9/10/2026)
# 03_auditoria/lima_tres_ambitos/ (README, análisis y auditorías; las correcciones del auditor mandan) e implementacion/
# CONTEXTO.md. Decisiones L1–L9 aprobadas el 9/10/2026; se anula PR-03 del 5/10. Informe de esta pieza (P1, reglas):
# 03_auditoria/lima_tres_ambitos/implementacion/p1_reglas/implementacion.md. Ámbitos (curados/capa0/ambitos.yaml):
# LIMA_METROPOLITANA = provincia 1501; LIMA_REGION = dpto 15 sin la 1501; CALLAO = 07; AREA_METROPOLITANA_LIMA_CALLAO =
# 1501 + 07 = dominio 8 de la ENAHO, rotulado siempre «Lima Metropolitana y Callao». Cambios: NIVEL_RANK, R-CRUCES-01,
# R-TERRITORIO-06, 08 y 09, R-ENC-04, 06, 07, 08 y 12, R-GASTO-01, 03 y 13, R-REG-07, R-EST-01 y 05, R-CRUCES-06,
# especificaciones (dim_ambito, tablas de respaldo y anexo S4) y 18 tipos de prueba de consistencia (PRUEBAS_LIMA_L).
import copy as _copy
_L = 'decisión del dueño, 9/10/2026'
REF_LIMA_L = {'titulo': 'Pregunta al Perú – Lima en tres ámbitos: Lima Metropolitana, Lima Región y Callao (9/10/2026)', 'url': None,
              'ruta': '03_auditoria/lima_tres_ambitos/README.md'}
ROTULOS_LIMA = {
 'LIMA_METROPOLITANA': 'Lima Metropolitana (provincia de Lima)',
 'LIMA_REGION': 'Lima Región (Lima Provincias)',
 'CALLAO': 'Callao',
 'AREA_METROPOLITANA_LIMA_CALLAO': 'Lima Metropolitana y Callao',
 'departamento_15': 'departamento de Lima (Lima Metropolitana + Lima Región)'}
_ROT = ('Toda cifra lleva el nombre largo del ámbito (L4): «Lima Metropolitana (provincia de Lima)», «Lima Región (Lima '
        'Provincias)», «Callao», «Lima Metropolitana y Callao» (dominio 8) y «departamento de Lima (Lima Metropolitana + Lima '
        'Región)». Ley 31140: «departamento de Lima» tiene dos sentidos; nunca se usa sin decir cuál.')

# -- 1. NIVEL_RANK (auditoría de encuestas, A2). El rango solo ordena; R-CRUCES-01 compara además la contención territorial.
NIVEL_RANK_D8 = dict(NIVEL_RANK_D8, LIMA_METROPOLITANA=3, LIMA_REGION=3.5, CALLAO=4, AREA_METROPOLITANA_LIMA_CALLAO=4.5)
NOTA_NIVEL_RANK_BASE = (
 'dominio_subnacional = área (urbano o rural) y región natural (Costa, Sierra, Selva). La región natural 1501 + 07 de la '
 'ENDES (hasta 2019) tiene el rango de AREA_METROPOLITANA_LIMA_CALLAO (4,5) y se rotula «Lima Metropolitana y Callao». Ámbitos de Lima (' + _L + '): LIMA_METROPOLITANA (provincia '
 '1501) = 3, LIMA_REGION (9 provincias del departamento 15) = 3,5, CALLAO (departamento 07) = 4 y '
 'AREA_METROPOLITANA_LIMA_CALLAO (dominio 8 de la ENAHO, 1501 + 07, «Lima Metropolitana y Callao») = 4,5. El rango solo '
 'ordena: R-CRUCES-01 decide además qué territorio contiene a cuál (dim_ambito, dim_dominio). Dominio × departamento con '
 'ubigeos que no coinciden → re-estimar la encuesta para el menor territorio que contiene a ambos.')

# -- 2. R-CRUCES-01: sin fusión obligatoria LM + LR (L5; auditorías: H-03, H6, A2).
_DOMINIOS_LIMA_C01 = {
 'regla': ('Sin fusión obligatoria (' + _L + ', L5): el gasto distingue LIMA_METROPOLITANA, LIMA_REGION y CALLAO '
           '(cuenta_en_ambito, R-GASTO-03), así que cada componente va al mismo ámbito.'),
 'encuesta_da_LM_LR_Callao': 'no se fusiona: cada componente se calcula para el ámbito pedido',
 'encuesta_solo_dominio_8': ('el componente administrativo := LIMA_METROPOLITANA + CALLAO (1501 + 07), rotulado «Lima '
                             'Metropolitana y Callao»'),
 'componente_solo_departamento_15': ('si un componente solo existe para el departamento 15 entero (p. ej., la población '
                                     'oficial de 6–35 meses o el alcance lima_departamento del gasto), el cruce va al '
                                     'departamento 15, rotulado «departamento de Lima (Lima Metropolitana + Lima Región)», '
                                     're-estimando la encuesta para ese territorio'),
 'contencion': ('contiene(A, B) := ubigeos(B) ⊆ ubigeos(A), con la composición de dim_ambito y dim_dominio: el '
                'departamento 15 contiene a LIMA_METROPOLITANA y LIMA_REGION; AREA_METROPOLITANA_LIMA_CALLAO contiene a '
                'LIMA_METROPOLITANA y CALLAO; LIMA_REGION y CALLAO no se contienen; el dominio 8 y el departamento 15 '
                'tampoco')}
CAMPOS_REGLAS += [('R-CRUCES-01', 'parametros.dominios_lima', _DOMINIOS_LIMA_C01)]
AGREGADOS_REGLAS_R3 += [
 ('R-CRUCES-01', 'condicion',
  ' [' + _L + ', L5; auditoría de encuestas, A2] Además del rango, contención territorial: territorio_cruce := el menor '
  'territorio que contiene al de cada componente (parametros.dominios_lima.contencion); el rango de NIVEL_RANK no basta '
  'cuando dos niveles empatan o no se contienen. Si ningún territorio salvo el nacional contiene a todos (p. ej., '
  'LIMA_REGION con CALLAO, o el dominio 8 con el departamento 15), no hay cruce territorial (caso borde 3).'),
]
PARCHES_REGLAS_R3 += [
 ('R-CRUCES-01', '(1) Dominio vs departamento: ENAHO separa Lima Metropolitana y Lima Región; si el otro componente no '
                 'distingue, ambos pasan a Lima (15) re-estimando la encuesta para el departamento completo. (2) Callao '
                 'siempre aparte.',
  '(1) Lima (' + _L + ', L5): el gasto y la población total distinguen Lima Metropolitana, Lima Región y el Callao: no se '
  'fusionan. Si la encuesta solo da el dominio 8, el componente administrativo suma Lima Metropolitana + Callao; si un '
  'componente solo existe para el departamento 15 entero, el cruce va a ese departamento, re-estimando la encuesta. '
  '(2) Callao siempre aparte, salvo dentro del dominio 8 («Lima Metropolitana y Callao»).'),
 ('R-CRUCES-01', 'gasto: sumar devengado por DEPARTAMENTO_META)',
  'gasto: sumar devengado por DEPARTAMENTO_META; en Lima y el Callao, por ámbito con cuenta_en_ambito, R-GASTO-03)'),
]

# -- 3. R-TERRITORIO-06, R-ENC-06, R-ENC-07, R-GASTO-01 y especificaciones: textos obsoletos (L3 anula PR-03).
SOBRESCRITURAS_CONSCIENTES = globals().get('SOBRESCRITURAS_CONSCIENTES', set()) | {
 ('R-TERRITORIO-06', 'casos_borde'),  # traía [PR-03] (correcciones_prueba): L3 la anula; PR-03 queda en hallazgos_prueba
 ('R-ENC-07', 'casos_borde'),         # traía [PR-03]: idem
 ('R-ENC-07', 'parametros.dominios_lima'),  # HEC-11 (auditoría v1.1): L1 y L3 la reemplazan
}
CAMPOS_REGLAS += [
 ('R-TERRITORIO-06', 'ejemplo',
  "Anemia 6–35 meses ENDES 2024 para 'Lima Metropolitana' cruzada con el gasto del PP de anemia: el gasto se suma sobre "
  "las filas cuenta_en_ambito del ámbito LIMA_METROPOLITANA (R-GASTO-03), no sobre las ejecutoras con sede en la "
  "provincia 1501 (eso es el sesgo de sede que prohíbe R-GASTO-01) ni sobre todo el departamento 15. Si la encuesta solo da "
  "el dominio 8 (ENAHO), el gasto suma LIMA_METROPOLITANA + CALLAO y se rotula «Lima Metropolitana y Callao» (R-CRUCES-01)."),
 ('R-TERRITORIO-06', 'casos_borde',
  'Dominios por área (urbano/rural) no se pueden reconstruir con ubigeo (ver R-TERRITORIO-07). ENAPRES victimización solo '
  'urbana: el cruce con registros distritales se limita a distritos con población urbana y se rotula. Si la ficha técnica '
  'de un año no es clara sobre Callao, revisión humana antes de habilitar el cruce. [' + _L + ', L3; anula PR-03 del '
  '5/10] Lima Metropolitana es siempre la provincia 1501 (43 distritos); el dominio 8 de la ENAHO (1501 + 07) se rotula '
  'siempre «Lima Metropolitana y Callao». La composición de cada dominio o ámbito se lee en dim_dominio por encuesta y '
  'año (tipo dominio_diseno o ambito_publicado).'),
 ('R-ENC-07', 'parametros.dominios_lima', {
  'ENAHO 2015–2025': ('dominio de la ficha: «Área Metropolitana de Lima y Callao» = dominio 8 = 1501 + 07, rotulado siempre '
                      '«Lima Metropolitana y Callao». LIMA_METROPOLITANA (1501), LIMA_REGION (15 sin 1501) y CALLAO (07) no '
                      'son dominios de la ficha: son ámbitos que el INEI publica (informe técnico de pobreza) y uniones de '
                      'estratos completos → se publican con el aviso ambito_no_dominio (R-ENC-08, L1)'),
  'ENDES 2015–2025': ('CALLAO (07) es dominio de la ficha. LIMA_METROPOLITANA y LIMA_REGION son ámbitos de asignación de la '
                      'muestra (Cuadro N.º 1 de la ficha) que el INEI publica: desde 2018 por ubigeo; en 2015–2017 por '
                      'estrato (LM = 15-1; LR = 15-2 y 15-3; L2, con aviso de método)'),
  'rotulos': ROTULOS_LIMA}),
 ('R-ENC-07', 'casos_borde',
  'Lima (' + _L + ', L1 y L3): se publica el ámbito pedido (Lima Metropolitana, Lima Región o Callao) con su aviso '
  '(R-ENC-08); el dominio 8 solo cuando se pide Lima + Callao, rotulado «Lima Metropolitana y Callao». No se suma el Callao '
  'a Lima Metropolitana ni se resta del dominio 8: cada cifra se estima con el diseño. Cambios de dominio entre años → la '
  'serie se corta (ver R-ENC-13). El mensaje muestra la composición del ámbito. ' + _ROT),
]
PARCHES_REGLAS_R3 += [
 ('R-TERRITORIO-06', "Lima Metropolitana = provincia 1501 (INEI) y, en algunas publicaciones, también Callao (07);",
  'Lima Metropolitana = provincia 1501 (INEI); el dominio 8 de la ENAHO (1501 + 07) se rotula «Lima Metropolitana y '
  'Callao» (' + _L + ', L3);'),
 ('R-TERRITORIO-06', 'Catálogo de dominios controlado: nacional, urbano, rural, costa, sierra, selva, departamento, '
                     'lima_metropolitana, lima_provincias, callao, ciudades_principales.',
  'Catálogo de dominios controlado: nacional, urbano, rural, costa, sierra, selva, departamento, lima_metropolitana, '
  'lima_provincias, callao, area_metropolitana_lima_callao (dominio 8; alias lima_metropolitana_callao), '
  'ciudades_principales; tipo ∈ {dominio_diseno, ambito_publicado}; ámbito en la columna ambito_id (' + _L + ').'),
 ('R-ENC-07', "La ENAHO 2021 define como dominio el 'Área Metropolitana de Lima y Callao' y en otros años separa Lima "
              "Metropolitana, Lima Provincias y Callao;",
  "La ENAHO (fichas 2015–2025) define como dominio el 'Área Metropolitana de Lima y Callao' (dominio 8 = 1501 + 07); "
  "ninguna ficha declara como dominio a Lima Metropolitana, Lima Región ni el Callao, pero el INEI los publica por "
  "separado (informe técnico de pobreza) y son uniones de estratos completos; en la ENDES el Callao es dominio y Lima "
  "Metropolitana y Lima Región son ámbitos de asignación de la muestra (Cuadro N.º 1);"),
 ('R-ENC-06', 'en ENAHO forma parte del dominio Área Metropolitana de Lima y Callao (ver R-ENC-07.dominios_lima).',
  'en ENAHO forma parte del dominio Área Metropolitana de Lima y Callao («Lima Metropolitana y Callao») y además se publica '
  'aparte como ámbito, con aviso (R-ENC-08; ver R-ENC-07.dominios_lima).'),
 ('R-ENC-06', '24 departamentos (más Lima Metropolitana y Callao según el año)',
  '24 departamentos (su «Lima» incluye al Callao) y el dominio «Área Metropolitana de Lima y Callao»; Lima Metropolitana, '
  'Lima Región y el Callao se publican como ámbitos con aviso (R-ENC-08)'),
 ('R-GASTO-01', "Lima: DEPARTAMENTO_META=15 mezcla Lima Metropolitana y Lima Provincias y recibe gasto de sedes centrales; "
                "rotular 'incluye gasto de entidades nacionales con sede en Lima'. Callao=07.",
  'Lima y Callao (decisiones del 6/10 y del 9/10/2026): el gasto con meta 15 se separa por ámbito (LIMA_METROPOLITANA, '
  'LIMA_REGION) y el de las entidades nacionales con sede en Lima o en el Callao sale de la cifra (cuenta_en_ambito, '
  'R-GASTO-03); Callao = 07, con su propio aviso de sede.'),
]
AGREGADOS_REGLAS_R3 += [
 ('R-GASTO-01', 'condicion',
  ' (f) [' + _L + ', Ley 31140] Todo el pliego del GR Lima → LIMA_REGION, también sus obras ubicadas por CUI en la '
  'provincia 1501 o en 150000 (el GR Lima no tiene competencia en la provincia de Lima); el pliego del GR Callao → 07 '
  'aunque la meta sea 15.'),
]
DIM_AMBITO = dict(DIM_AMBITO,
 ambitos_iniciales=[
  'LIMA_METROPOLITANA: provincia de Lima (1501, 43 distritos), gestionada por la Municipalidad Metropolitana de Lima; sin '
  'el Callao. Rótulo: «Lima Metropolitana (provincia de Lima)».',
  'LIMA_REGION (Lima Provincias): departamento 15 sin la provincia de Lima = 9 provincias (Barranca, Cajatambo, Canta, '
  'Cañete, Huaral, Huarochirí, Huaura, Oyón, Yauyos), 128 distritos, gestionada por el Gobierno Regional de Lima (sede '
  'Huacho); es el «departamento de Lima» de la Ley 31140 (DCF a) para fines estadísticos y presupuestales. Rótulo: «Lima '
  'Región (Lima Provincias)». En el archivo propio tiene el código 159999; su superficie (32 208,36 km²) coincide '
  'exactamente con departamento 15 menos provincia 1501.',
  'AREA_METROPOLITANA_LIMA_CALLAO: provincia de Lima + Callao (1501 + 07). Es el dominio 8 de la ENAHO («Área Metropolitana '
  'de Lima y Callao» en la ficha) y la región natural «Lima Metropolitana» de la ENDES hasta 2019. Se rotula siempre «Lima '
  'Metropolitana y Callao» (' + _L + ', L3; anula PR-03 del 5/10).',
  'CALLAO: departamento y provincia 07, gestionado por el Gobierno Regional del Callao; dominio propio en la ENDES; en la '
  'ENAHO no es dominio: se publica como ámbito con aviso (L1). Rótulo: «Callao».',
  'Departamento 15 entero (no es un ámbito de esta tabla: es el ubigeo 15): rótulo «departamento de Lima (Lima '
  'Metropolitana + Lima Región)». Ley 31140: «departamento de Lima» tiene dos sentidos; nunca se usa sin decir cuál.'],
 uso=('Para gasto: todo el pliego del Gobierno Regional de Lima se atribuye a LIMA_REGION (Ley 31140), también sus obras '
      'ubicadas en la provincia 1501; el pliego regional de la Municipalidad Metropolitana de Lima a LIMA_METROPOLITANA; el '
      'Gobierno Regional del Callao al 07. Las cifras por ámbito usan las filas cuenta_en_ambito (R-GASTO-03). Para '
      'encuestas: el dominio o ámbito se toma de dim_dominio según encuesta y año (tipo dominio_diseno o ambito_publicado; '
      'ámbito en ambito_id).'))
TABLAS_MVP_RESPALDO_L = {
 'ambito_ejecutora': ('ya no está vacía: curados/capa0/ejecutoras_alcance.yaml (ejecutoras del Gobierno Nacional con '
                      'meta en Lima; L6 la extiende a las de meta 07), leída por dim_unidad_ejecutora y la fact (R-GASTO-03)')}

# -- 4. R-ENC-08: rama «ámbito publicado» (L1; auditoría de encuestas, A1 y A5).
AVISOS_INFERENCIA_L = {
 'ambito_no_dominio': ('El INEI publica esta cifra para {ambito}, aunque la encuesta no se diseñó para dar resultados de '
                       'ese ámbito por separado. Calculamos aparte qué tan precisa es.'),
 'ambito_por_estrato': ('En {anio} la encuesta no registró el distrito de cada hogar: separamos Lima Metropolitana y Lima '
                        'Región según cómo se eligió la muestra en cada zona.')}
_P08L = _copy.deepcopy(_ultimo('R-ENC-08', 'parametros'))
_P08L['avisos'] = dict(_P08L['avisos'], **AVISOS_INFERENCIA_L)
_P08L['registro_inferencia_verificada']['campos_que_usa_la_regla'] = _P08L['registro_inferencia_verificada']['campos_que_usa_la_regla'] + [
 'ambitos_publicados', 'ambitos_cita_url', 'ambitos_cita_documento', 'ambitos_cita_ubicacion']  # columnas de P2 (9/10/2026)
_P08L['excluye_departamentos'] = (
 'códigos de 2 dígitos separados por «;». ENAHO 2015–2023: 07 (el Callao va en el dominio «Lima Metropolitana y Callao»); '
 '2024–2025: vacío, porque el Callao es ámbito publicado (L1, ambitos_publicados). No se aplica a un ámbito publicado: si '
 'CALLAO está en ambitos_publicados de la fila, el Callao se publica como ámbito con el aviso ambito_no_dominio')
_P08L['ambito_publicado'] = {
 'que_es': ('ámbito que el INEI publica y que es unión de estratos completos de la encuesta, aunque la ficha no lo declare '
            'como dominio (ENAHO: LIMA_METROPOLITANA, LIMA_REGION y CALLAO; ENDES: LIMA_METROPOLITANA y LIMA_REGION)'),
 'requisitos': ["fila de dim_dominio (encuesta, anio) con ambito_id = el ámbito y tipo = 'ambito_publicado' (llave dominio_id)",
                'fila de inferencia_verificada.csv con inferencia_verificada = true, la cita completa y el ámbito en su '
                'columna ambitos_publicados (ids de ambitos.yaml separados por «;»), con su propia cita completa '
                '(ambitos_cita_url, ambitos_cita_documento, ambitos_cita_ubicacion): el informe técnico que publica el '
                'ámbito (ENAHO: informe técnico de pobreza, no la prensa); ambitos_metodo dice cómo se asigna (ubigeo o estrato)'],
 'sin_columna_o_sin_fila': 'false: el ámbito no se publica y la cifra sube al menor nivel verificado que lo contiene',
 'aviso': 'ambito_no_dominio; en la ENDES 2015–2017 también ambito_por_estrato (L2)',
 'decision': _L + ', L1 y L2'}
CAMPOS_REGLAS += [
 ('R-ENC-08', 'condicion', _cambia(_cambia(_cambia(_ultimo('R-ENC-08', 'condicion'),
  "(incluye los dominios: Lima Metropolitana, área urbana o rural, región natural)",
  "(incluye los dominios —área urbana o rural, región natural, «Lima Metropolitana y Callao» (dominio 8)— y los ámbitos "
  "LIMA_METROPOLITANA, LIMA_REGION y CALLAO, por su ambito_id)"),
  "dominios_anuales y excepciones son la cita, no la llave).",
  "dominios_anuales y excepciones son la cita, no la llave). Ámbito publicado (" + _L + ", L1): si n es un ámbito con "
  "una fila de dim_dominio (fuente, anio) con ambito_id = n y tipo = 'ambito_publicado' (unión de estratos completos que "
  "el INEI publica; los dominios de la ficha tienen tipo = 'dominio_diseno'), verificado(n) "
  ":= fila con inferencia_verificada = true, n en fila.ambitos_publicados y la cita del ámbito completa "
  "(ambitos_cita_url, ambitos_cita_documento y ambitos_cita_ubicacion: el informe técnico que lo publica); no se compara con "
  "nivel_maximo y se evalúa antes que excluye_departamentos; si es verdadero → publicar con el aviso ambito_no_dominio "
  "(parametros.avisos), y en la ENDES 2015–2017 también ambito_por_estrato. Un territorio cuyo ubigeo coincide con un "
  "ámbito publicado (07 ≡ CALLAO; 1501 ≡ LIMA_METROPOLITANA) va por esta rama aunque se haya resuelto como departamento o "
  "provincia. Un departamento con dim_dominio.por_departamento[d].tipo = 'ambito_publicado' (ENAHO: 15, sin el Callao) se "
  "verifica por la rama general y lleva el aviso ambito_no_dominio con {ambito} = «departamento de Lima (Lima "
  "Metropolitana + Lima Región)»."),
  "Departamento en excluye_departamentos (ENAHO: 07, el Callao) → su dominio de R-ENC-07 si está verificado; si no, "
  "'nacional'.",
  "Departamento en excluye_departamentos (ENAHO 2015–2023: 07, el Callao) y no publicado como ámbito → su dominio de R-ENC-07 si "
  "está verificado; si no, 'nacional'.")),
 ('R-ENC-08', 'parametros', _P08L),
 ('R-ENC-08', 'mensaje_usuario', _ultimo('R-ENC-08', 'mensaje_usuario') +
  ' (ámbito publicado por el INEI) «' + AVISOS_INFERENCIA_L['ambito_no_dominio'] + '» (Lima en 2015–2017) «' +
  AVISOS_INFERENCIA_L['ambito_por_estrato'] + '»'),
]
AGREGADOS_REGLAS_R3 += [
 ('R-ENC-08', 'justificacion',
  ' Lima Metropolitana, Lima Región y el Callao no son dominios de la ficha ENAHO, pero son uniones de estratos completos '
  'que el INEI publica, con CV de 4,7–8,5 % y gl ≥ 167 en pobreza 2024–2025: se publican con aviso (' + _L + ', L1).'),
]

# -- 5. R-TERRITORIO-09: «Lima» → preguntar (L4); «Callao» → departamento 07 (auditoría de maquinaria, D1: nombres de la DCF).
CAMPOS_REGLAS += [
 ('R-TERRITORIO-09', 'parametros.ambiguos_conocidos', {
  'Lima': ['Lima Metropolitana (provincia de Lima, 1501, 43 distritos)',
           'Lima Región (Lima Provincias): las 9 provincias del departamento sin la provincia de Lima',
           'departamento de Lima completo (Lima Metropolitana + Lima Región, departamento 15)',
           'Lima Metropolitana y Callao (1501 + 07; solo encuestas: dominio 8 de la ENAHO)'],
  'Callao': ['departamento 07 (Callao, 7 distritos)']}),
 ('R-TERRITORIO-09', 'parametros.sin_respuesta', {
  'Lima': 'LIMA_METROPOLITANA, ofreciendo los otros tres (L4)',
  'Callao': 'no se pregunta: departamento 07; el distrito 070101 solo si se pide «distrito del Callao» o «Callao Cercado»'}),
 ('R-TERRITORIO-09', 'parametros.rotulos_lima', ROTULOS_LIMA),
]
AGREGADOS_REGLAS_R3 += [
 ('R-TERRITORIO-09', 'casos_borde',
  ' [' + _L + ', L4] «Lima» sola: se pregunta en este orden: Lima Metropolitana (provincia de Lima), Lima Región (Lima '
  'Provincias), el departamento de Lima completo y, solo en cifras de encuestas, Lima Metropolitana y Callao. Sin respuesta: '
  'Lima Metropolitana, ofreciendo los otros. «Callao» sin más: el departamento 07, sin preguntar. ' + _ROT),
 ('R-TERRITORIO-09', 'mensaje_usuario',
  ' (Lima) «¿Qué Lima te interesa? Lima Metropolitana (la provincia de Lima), Lima Región (las otras 9 provincias del '
  'departamento), todo el departamento de Lima (las dos juntas) o, en datos de encuestas, Lima Metropolitana y Callao juntos.» (Lima, sin '
  'respuesta) «Mostramos Lima Metropolitana (la provincia de Lima). También podemos darte Lima Región, todo el departamento '
  'de Lima (las dos juntas) o Lima Metropolitana y Callao.»'),
]

# -- 6. R-GASTO-03 (L6): un solo mecanismo de sesgo de sede para los departamentos 15 y 07 (auditoría de maquinaria, H-A3–H-A5).
_CUENTA_AMBITO_L = (
 "cuenta_en_ambito (columna booleana de fact_gasto_territorial que define la capa de gasto; el validador la lee, no la "
 "recalcula) := la fila entra en las cifras de su ámbito (LIMA_METROPOLITANA, LIMA_REGION o CALLAO; las filas de "
 "150000, «Lima sin separar», solo en el total del departamento 15): departamento_atribucion ∈ {'15', '07'} AND NOT "
 "referencia_nacional AND NOT obra_sede_nacional (también las ubicadas en el 07) AND NOT (nivel_atribucion = "
 "'departamento_meta' AND nivel_gobierno = 'E' AND alcance_ejecutora = 'nacional'). cuenta_en_lima es su alias para el "
 "departamento 15 (= cuenta_en_ambito AND departamento_atribucion = '15'). Meta 07: alcance nacional solo donde no hay "
 "servicio directo en el Callao (Marina de Guerra, APN, IMARPE, ENAMM, SUNAT-Aduanas); MP-Gerencia General y DIREFIN PNP "
 "son mixtas; la UNAC y la Corte Superior del Callao cuentan en el Callao.")
CAMPOS_REGLAS += [
 ('R-GASTO-03', 'parametros.lima.cifra',
  'columna cuenta_en_ambito de fact_gasto_territorial (alias cuenta_en_lima para el 15; fórmula en la condición); '
  'lima_departamento → solo en el total del departamento («Lima sin separar», 150000)'),
 ('R-GASTO-03', 'parametros.marca_sede', {
  'columna': 'cuenta_en_ambito', 'alias': {'cuenta_en_lima': 'cuenta_en_ambito AND departamento_atribucion = 15'},
  'departamentos': ['15', '07'], 'que_es': 'un solo mecanismo de sesgo de sede para Lima y el Callao (no se duplica la lógica)',
  'formulas_por_ambito': {
   'LIMA_METROPOLITANA': "cuenta_en_ambito AND (ubigeo_atribucion = 'A-LIMA_METROPOLITANA' OR ubigeo_atribucion LIKE '1501%')",
   'LIMA_REGION': ("cuenta_en_ambito AND (ubigeo_atribucion = 'A-LIMA_REGION' OR (ubigeo_atribucion LIKE '15%' AND "
                   "ubigeo_atribucion NOT LIKE '1501%' AND ubigeo_atribucion != '150000'))"),
   'CALLAO': "cuenta_en_ambito AND departamento_atribucion = '07'",
   'departamento_15': "cuenta_en_ambito AND departamento_atribucion = '15' (incluye 150000)"},
  'implementacion_capa0': ('macro ambito_gasto(departamento_atribucion, ubigeo_atribucion, cuenta_en_ambito, '
                           'referencia_nacional) de vistas_gasto.sql (única definición del reparto; equivale a '
                           'formulas_por_ambito) y vista v_gasto_por_ambito, con líneas aparte que no se suman a ningún '
                           'ámbito: no asignable (150000; A-AREA_METROPOLITANA_LIMA_CALLAO), referencia nacional y gasto '
                           'nacional con sede en Lima o el Callao'),
  'decision': _L + ', L6'}),
 ('R-GASTO-03', 'parametros.callao', {
  'cifra': "cuenta_en_ambito AND departamento_atribucion = '07'",
  'aviso_sesgo_sede': {'siempre': True, 'pct_sede': None,
                       'pct_sede_pendiente': ('lo calcula la capa de gasto con cuenta_en_ambito (gasto nacional con '
                                              'meta 07 sobre el gasto del 07 asignado por meta), al cargar cada año'),
                       'contexto': ('la Marina de Guerra es el 50,5 / 37,5 / 33,5 % del gasto del Callao en 2023–2025; '
                                    'también SUNAT-Aduanas, APN e IMARPE')},
  'per_capita_y_ranking': ('nunca sin el aviso de sede; si la fact no trae cuenta_en_ambito, no se publican gasto per '
                           'cápita ni ranking del gasto del Callao'),
  'decision': _L + ', L6'}),
 ('R-GASTO-03', 'mensaje_usuario', _ultimo('R-GASTO-03', 'mensaje_usuario') + (
  ' (cifras del Callao, siempre) «En el Callao tienen su sede entidades nacionales como la Marina de Guerra, la autoridad '
  'portuaria y la aduana. Lo que gastan para todo el país no se cuenta aquí. Comparar el Callao con otras regiones tiene '
  'límites.» (gasto por habitante o comparación del Callao, si aún no se separa ese gasto) «El gasto del Callao incluye '
  'el de entidades nacionales con sede ahí, que atienden a todo el país. Mientras no se separe, no mostramos el gasto '
  'por habitante del Callao ni lo comparamos con otras regiones.»')),
]
AGREGADOS_REGLAS_R3 += [
 ('R-GASTO-03', 'condicion',
  ' [' + _L + ', L6] Un solo mecanismo de sesgo de sede para los departamentos 15 y 07: ' + _CUENTA_AMBITO_L + ' Cifra '
  'por ámbito: parametros.marca_sede.formulas_por_ambito (Lima Metropolitana con cuenta_en_ambito: sin ese filtro se '
  'inflaría con las obras de sede y de referencia nacional). Toda cifra del Callao lleva el aviso de sede '
  '(parametros.callao); sin cuenta_en_ambito en la fact no se publican gasto per cápita ni ranking del Callao.'),
 ('R-GASTO-03', 'implementacion',
  ' [' + _L + ', L6] La marca es una sola columna, cuenta_en_ambito, para los departamentos 15 y 07 (la define la capa de '
  'gasto; ejecutoras_alcance.yaml y obras_sede_nacional.yaml se extienden a la meta 07); cuenta_en_lima queda como alias '
  'para el 15. pct_sede del Callao: parametros.callao.aviso_sesgo_sede.'),
]

# -- 7. L7: cobertura de tamizaje del SIEN por departamento y además por LM, LR y Callao (auditoría de maquinaria, H-A6).
_SIEN_L7 = {
 'ambitos': ['LIMA_METROPOLITANA', 'LIMA_REGION', 'CALLAO'],
 'numerador': 'niños de 6-35 m con ubigeo_procedencia en el ámbito (provincia 1501 → LM; resto del 15 → LR; 07 → Callao)',
 'cota_superior': '+ niños sin procedencia atendidos en establecimientos del ámbito',
 'denominador': ('LM y LR: población de 6-35 m del ámbito según el prorrateo propio (IPF, cuadra con el departamento 15), '
                 'rotulada «población estimada (cálculo propio)»; Callao: población oficial del departamento 07'),
 'rotulo_denominador_propio': 'población estimada (cálculo propio)',
 'margen_umbral_pp': 1,
 'aviso_margen': ('si 0 ≤ cota_inf − sien_umbral_tamizaje_pct < margen_umbral_pp → aviso «apenas supera la mitad» (2025: '
                  'Lima Región, cota inferior 50,6 %); «más de la mitad» solo si cota_inf ≥ sien_umbral_tamizaje_pct'),
 'decision': _L + ', L7 (reemplaza «solo por departamento» del 7/10/2026)'}
CAMPOS_REGLAS += [
 ('R-REG-07', 'parametros.sien_ambitos_lima', _SIEN_L7),
 ('R-REG-07', 'parametros.sien_cobertura_cotas', _ultimo('R-REG-07', 'parametros.sien_cobertura_cotas') +
  '; también por LIMA_METROPOLITANA, LIMA_REGION y CALLAO (sien_ambitos_lima, L7)'),
 ('R-TERRITORIO-08', 'parametros.sien_cobertura_tamizaje', _ultimo('R-TERRITORIO-08', 'parametros.sien_cobertura_tamizaje') +
  '. Además por Lima Metropolitana, Lima Región y el Callao (' + _L + ', L7), con el denominador «población estimada '
  '(cálculo propio)» en Lima Metropolitana y Lima Región (R-REG-07.parametros.sien_ambitos_lima)'),
]
PARCHES_REGLAS_R3 += [
 ('R-REG-07', 'En el SIEN se usa la cobertura de tamizaje de 6-35 m: se publica solo por departamento,',
  'En el SIEN se usa la cobertura de tamizaje de 6-35 m: se publica por departamento y además por Lima Metropolitana, '
  'Lima Región y el Callao (' + _L + ', L7),'),
 ('R-REG-07', 'SIEN (cobertura de tamizaje de 6-35 m, solo por departamento;',
  'SIEN (cobertura de tamizaje de 6-35 m, por departamento y por LIMA_METROPOLITANA, LIMA_REGION y CALLAO —L7—;'),
 ('R-TERRITORIO-08', 'el % ubicado se mide por departamento y la cobertura se publica solo por departamento, con dos cotas (R-REG-07).',
  'el % ubicado se mide por departamento y la cobertura se publica por departamento y además por Lima Metropolitana, Lima '
  'Región y el Callao (' + _L + ', L7), con dos cotas (R-REG-07).'),
 ('R-TERRITORIO-08', 'la cobertura se publica únicamente por departamento con las dos cotas de R-REG-07',
  'la cobertura se publica únicamente por departamento —y por LIMA_METROPOLITANA, LIMA_REGION y CALLAO (L7)— con las dos '
  'cotas de R-REG-07'),
]
AGREGADOS_REGLAS_R3 += [
 ('R-REG-07', 'condicion',
  '. [' + _L + ', L7] Ámbitos de Lima: numerador, cotas y denominador según parametros.sien_ambitos_lima (LM y LR con '
  '«población estimada (cálculo propio)»); 0 ≤ cota_inf − sien_umbral_tamizaje_pct < 1 → advertir «La cobertura apenas '
  'supera la mitad de los niños»; «más de la mitad» solo si cota_inf ≥ sien_umbral_tamizaje_pct.'),
 ('R-REG-07', 'mensaje_usuario',
  ' (SIEN, Lima Metropolitana o Lima Región) «La población de niños de este ámbito es una estimación propia.» (cota '
  'inferior a menos de 1 punto de la mitad) «La cobertura apenas supera la mitad de los niños: la diferencia es menor de '
  '1 punto y la población es una estimación.»'),
]

# -- 8. L8: ranking territorial de 26 unidades (23 departamentos + LM + LR + Callao); en el gasto, solo con L6.
DEPARTAMENTOS_RANKING_L8 = [f'{i:02d}' for i in range(1, 26) if i not in (7, 15)]
UNIDADES_RANKING_L8 = {
 'unidades': DEPARTAMENTOS_RANKING_L8 + ['LIMA_METROPOLITANA', 'LIMA_REGION', 'CALLAO'],
 'total': 26, 'aplica': 'encuestas y población; gasto solo con cuenta_en_ambito (L6, R-GASTO-13)',
 'sin_LM_o_LR': ('si en esa encuesta y año LM o LR no tienen cifra publicable (R-ENC-08), el ranking usa el departamento 15 '
                 'entero, rotulado «departamento de Lima (Lima Metropolitana + Lima Región)», con nota (25 unidades)'),
 'nunca': 'el departamento 15 entero junto con LM o LR (se superponen); el dominio 8',
 'decision': _L + ', L8 (reemplaza D-AUD-2: «24 departamentos + el Callao en una nota»)'}
CAMPOS_REGLAS += [
 ('R-ENC-12', 'parametros.unidades_ranking_departamental', UNIDADES_RANKING_L8),
 ('R-GASTO-13', 'parametros.unidades_ranking_departamental',
  {'con_cuenta_en_ambito': ('26 unidades (23 departamentos + LIMA_METROPOLITANA + LIMA_REGION + CALLAO), solo si la fact '
                            'trae cuenta_en_ambito para todos los años comparados (L6)'),
   'sin_cuenta_en_ambito': ('24 departamentos + Callao, con Lima y el Callao marcados «incluye sedes nacionales» (d); el '
                            'Callao sin gasto per cápita ni puesto (R-GASTO-03.parametros.callao)'),
   'decision': _L + ', L8'}),
]
AGREGADOS_REGLAS_R3 += [
 ('R-ENC-12', 'casos_borde',
  ' [' + _L + ', L8; reemplaza D-AUD-2] Unidades del ranking departamental: 26 (23 departamentos + Lima Metropolitana + '
  'Lima Región + Callao), como el ranking del INEI, con sus nombres largos (parametros.unidades_ranking_departamental). '
  'Sin cifra publicable de LM o LR → el departamento 15 entero con nota; nunca el departamento 15 junto con LM o LR, ni el '
  'dominio 8.'),
 ('R-EST-01', 'casos_borde',
  ' [' + _L + ', L8] Ranking departamental de una estimación modelada: las 26 unidades de R-ENC-12 cuando la fuente las '
  'publica (Mapa de Pobreza 2018: grupos «provincia de Lima» y «Región Lima»); si no, el departamento 15 entero con nota.'),
 ('R-EST-05', 'casos_borde',
  ' [' + _L + ', L1 y L8] En distritos de Lima y del Callao, el contexto es la cifra ENAHO de su ámbito (Lima '
  'Metropolitana, Lima Región o Callao, con aviso), no la del departamento 15 entero.'),
 ('R-GASTO-13', 'condicion',
  ' [' + _L + ', L8] Ranking departamental de gasto: 26 unidades (23 + Lima Metropolitana + Lima Región + Callao) solo con '
  'cuenta_en_ambito en la fact para todos los años (L6); si no, (d) con la marca. El Callao nunca va con gasto per cápita '
  'ni puesto sin el aviso de sede (R-GASTO-03).'),
 ('R-CRUCES-06', 'casos_borde',
  ' (4) [' + _L + ', L8] A nivel nacional, las unidades departamentales son las 26 de R-ENC-12 si ambos componentes '
  'distinguen Lima Metropolitana, Lima Región y el Callao (encuestas y población; el gasto solo con cuenta_en_ambito); si '
  'no, los 25 departamentos.'),
]

# -- 9. L9: R-ENC-04, CV > 15 % → referencial (convención del INEI), aunque el IC mida menos de 5 pp (auditoría, A8).
#    Impacto medido (p1_reglas/impacto_L9.csv): 868 celdas, 80 pasan de publicar a referencial.
IMPACTO_L9 = {
 'archivo': '03_auditoria/lima_tres_ambitos/implementacion/p1_reglas/impacto_L9.csv (l9_impacto.py)',
 'celdas': 868, 'cambian_publicar_a_referencial': 80,
 'por_indicador': {'DCI ENDES 2015–2025': '42 de 341', 'pobreza extrema ENAHO 2024–2025': '36 de 62',
                   'pobreza ENAHO 2024–2025': '2 de 62 (Ica)', 'anemia ENDES (RM 363-2022 y OMS 2024)': '0 de 403'},
 'alcance': 'indicadores del piloto (anemia, DCI, pobreza, pobreza extrema); ENAHO solo 2024–2025 (años cargados)',
 'nacional_y_area': 0, 'en_lima': '16 de 140 celdas de Lima (DCI Callao 7 años; pobreza extrema LM, LR, Callao, D8 y dpto 15)'}
CAMPOS_REGLAS += [
 ('R-ENC-04', 'parametros.cv_referencial_inei', 0.15),
 ('R-ENC-04', 'parametros.impacto_L9', IMPACTO_L9),
]
PARCHES_REGLAS_R3 += [
 ('R-ENC-04', 'referencial si n efectivo < 50 o gl < 8;',
  'referencial si n efectivo < 50, gl < 8 o el CV (ee/min(p, 1−p)) supera 15 % (convención del INEI), aunque el '
  'intervalo mida menos de 5 puntos;'),
 ('R-ENC-04', 'OR n_efectivo < 50 OR gl < 8 → publicar_referencial; resto → publicar.',
  'OR n_efectivo < 50 OR gl < 8 → publicar_referencial; resto → publicar, salvo cv_ref = ee/min(p, 1−p) > '
  'cv_referencial_inei (0.15) → publicar_referencial (convención del INEI; ' + _L + ', L9), aunque ancho_abs ≤ 0.05.'),
]
AGREGADOS_REGLAS_R3 += [
 ('R-ENC-04', 'justificacion',
  ' L9 (' + _L + '): la regla NCHS sola dejaba pasar CV de 15–100 % con IC de menos de 5 pp (p. ej., p = 9 % y CV 26 % '
  'se publicaba, y p = 11 % y CV 16 % era referencial); el INEI marca referencial toda cifra con CV > 15 %. Impacto: '
  'parametros.impacto_L9.'),
 ('R-ENC-04', 'casos_borde',
  ' [' + _L + ', L9] Con CV > 30 % y ancho ≤ 5 pp (p. ej., pobreza extrema de Ica 2024: 0,1 %, CV 100 %) la cifra es '
  'referencial, no suprimida: la supresión sigue los anchos absoluto y relativo.'),
]

# -- 10. Decisiones, trazabilidad y fecha.
HALLAZGOS_L = {
 'R-CRUCES-01': ['L5: sin fusión obligatoria LM + LR; dominio 8 → LM + Callao; contención territorial'],
 'R-TERRITORIO-06': ['L3: anula PR-03; ejemplo sin sede de la ejecutora'],
 'R-TERRITORIO-08': ['L7: cobertura SIEN también por LM, LR y Callao'],
 'R-TERRITORIO-09': ['L4: «Lima» → preguntar (LM, LR, departamento, LM + Callao); «Callao» → 07'],
 'R-ENC-04': ['L9: CV > 15 % → referencial'], 'R-ENC-06': ['L1: ámbitos publicados'],
 'R-ENC-07': ['L1 y L3: ámbito pedido con aviso; dominio 8 = «Lima Metropolitana y Callao»'],
 'R-ENC-08': ['L1 y L2: rama ámbito publicado (ambito_no_dominio)'], 'R-ENC-12': ['L8: 26 unidades'],
 'R-GASTO-01': ['L6 y Ley 31140: GR Lima → LR; GR Callao → 07'],
 'R-GASTO-03': ['L6: cuenta_en_ambito para 15 y 07; aviso de sede del Callao'], 'R-GASTO-13': ['L8: 26 unidades solo con L6'],
 'R-REG-07': ['L7: cobertura SIEN por LM, LR y Callao; aviso a < 1 punto del 50 %'],
 'R-EST-01': ['L8: 26 unidades'], 'R-EST-05': ['L1 y L8: contexto por ámbito'], 'R-CRUCES-06': ['L8: 26 unidades'],
}
CAMPOS_D8 += [
 ('cuenta_en_ambito', 'fila de gasto', 'cuenta_en_lima (ahora su alias para el 15)',
  'La fila entra en las cifras de su ámbito (Lima Metropolitana, Lima Región o Callao; las de 150000 solo en el total del departamento 15): atribuida al 15 o al 07, sin alcance nacional, sin referencia nacional y sin obras de sede o función nacional. Un solo mecanismo de sesgo de sede para Lima y el Callao (R-GASTO-03, L6).'),
 ('cuenta_en_lima', 'fila de gasto', 'exclusión por alcance_ejecutora = nacional (GA-01)',
  'Alias de cuenta_en_ambito para el departamento 15 (L6, 9/10/2026): atribuida al dpto 15, sin alcance nacional, sin referencia nacional y sin obras de sede o función nacional (obra_sede_nacional). El alcance lima_departamento cuenta solo en el departamento («Lima sin separar», 150000) (R-GASTO-03).'),
 ('ambitos_publicados', 'catálogo (fuente × año × módulo)', '—',
  'Columna de catalogo/inferencia_verificada.csv: ámbitos que el INEI publica y que son unión de estratos completos (LIMA_METROPOLITANA; LIMA_REGION; CALLAO), con la cita del informe técnico. R-ENC-08 los publica con el aviso ambito_no_dominio (L1).'),
]
DECISIONES_D8 += [
 ('L1', 'ENAHO: Lima Metropolitana, Lima Región y Callao por separado', 'Publicar con aviso o solo el dominio 8.', 'Publicar con el aviso ambito_no_dominio y la cita del informe técnico.', 'R-ENC-08, R-ENC-07', 'Adoptada (dueño, 9/10/2026). Rama nueva de R-ENC-08 (ámbito publicado).'),
 ('L2', 'ENDES 2015–2017: Lima Metropolitana y Lima Región', 'Por estrato (Cuadro N.º 1 de la ficha) o no publicar.', 'Por estrato, con aviso de método.', 'R-ENC-07, R-ENC-08', 'Adoptada (dueño, 9/10/2026). LM = estrato 15-1; LR = 15-2 y 15-3; desde 2018 por ubigeo.'),
 ('L3', 'Rótulo del dominio 8 de la ENAHO', '«Lima Metropolitana» o «Lima Metropolitana y Callao».', 'Siempre «Lima Metropolitana y Callao».', 'R-TERRITORIO-06, R-ENC-07', 'Adoptada (dueño, 9/10/2026). Anula PR-03 del 5/10 («Lima Metropolitana» = Lima + Callao en pobreza ENAHO).'),
 ('L4', 'El usuario escribe solo «Lima»', 'Preguntar o elegir uno.', 'Preguntar; sin respuesta, Lima Metropolitana y ofrecer los otros.', 'R-TERRITORIO-09', 'Adoptada (dueño, 9/10/2026). Toda cifra lleva el nombre largo del ámbito.'),
 ('L5', 'Cruce gasto ex-PAN × anemia (CR-01) en Lima', 'Departamento 15 entero o los tres ámbitos.', 'Los tres ámbitos, como subdivisión del departamento 15.', 'R-CRUCES-01', 'Adoptada (dueño, 9/10/2026). Reemplaza D-IND-4; R-CRUCES-01 sin fusión obligatoria; 2025 solo con dim_dominio ENDES 2025 confirmado.'),
 ('L6', 'Sesgo de sede en el Callao', 'Extender GA-01 al Callao o solo rotular.', 'Una sola marca para 15 y 07 (cuenta_en_ambito); MP-GG y DIREFIN mixtas; UNAC en el Callao.', 'R-GASTO-03, R-GASTO-13', 'Adoptada (dueño, 9/10/2026). Sin gasto per cápita ni ranking del Callao sin aviso.'),
 ('L7', 'Cobertura de tamizaje del SIEN en Lima', 'Solo departamento o también LM, LR y Callao.', 'Por LM, LR y Callao con «población estimada (cálculo propio)».', 'R-REG-07, R-TERRITORIO-08', 'Adoptada (dueño, 9/10/2026). Aviso si la cota inferior queda a menos de 1 punto del 50 %; reemplaza «solo por departamento» del 7/10.'),
 ('L8', 'Ranking territorial', '24 departamentos + Callao en nota, o 26 unidades.', '26: 23 departamentos + LM + LR + Callao.', 'R-ENC-12, R-EST-01, R-GASTO-13, R-CRUCES-06', 'Adoptada (dueño, 9/10/2026). Reemplaza D-AUD-2; en el gasto, solo con L6.'),
 ('L9', 'Proporciones con CV > 15 % e IC < 5 pp', 'Publicar (NCHS) o referencial (INEI).', 'Referencial (convención del INEI).', 'R-ENC-04', 'Adoptada (dueño, 9/10/2026). Impacto: 80 de 868 celdas pasan a referencial (impacto_L9.csv).'),
]
FECHA_ACTUALIZACION = ('2026-10-09', '9 de octubre de 2026')
# Coordinación con la capa de gasto (P3, 9/10/2026): macro ambito_gasto y vista v_gasto_por_ambito en vistas_gasto.sql.
VISTAS_GASTO_PUBLICADAS = VISTAS_GASTO_PUBLICADAS + ['ambito_gasto', 'v_gasto_por_ambito']

# -- 11. Anexo de especificaciones: «Insumos estandarizados del piloto (S4)», que se había agregado a mano a
#    especificaciones_capa0.md (el consolidador lo borraba al regenerar). Pasa a generarse desde aquí, con los rótulos de L3.
ANEXO_ESPECIFICACIONES = """## Insumos estandarizados del piloto (S4, 9/10/2026)

Se construyen con `pap construir endes|enaho|mapa_pobreza` y quedan en `biblioteca/estandarizada/` (Parquet ordenado por clave + manifiesto con huellas, pruebas y tablas de revisión). Una fila por unidad de la fuente; **no traen indicadores calculados**: eso lo hace el motor con `dim_indicador`. Auditoría: `03_auditoria/s4_insumos/auditoria.md` (apto con correcciones, todas aplicadas).

### endes_nino (`encuestas/endes_nino.parquet`)

Niñas y niños menores de 5 años del RECH6 de la ENDES 2015–2025 (236 869 filas), unidos a RECH1 (miembro) y RECH0 (hogar). Clave: `anio, id_hogar, idx_nino`.

| Columna | Origen | Regla |
|---|---|---|
| `id_conglomerado`, `id_estrato` | HV021; HV024 × HV022 | Estrato de diseño = departamento × HV022 (en 2015–2017 HV022 solo tiene 3 valores). Cada estrato cae en un solo departamento y una sola área (prueba E-AAAA-08) |
| `peso` | HV005/1e6; en 2020 HV005A/1e6 | `fuente_peso` dice cuál. Pesos normalizados: no sirven para totales |
| `departamento`, `area`, `ubigeo_hogar`, `provincia_hogar` | HV024, HV025, UBIGEO | Ubigeo solo desde 2018. `ubigeo_agrupado_inei` = 120699 (2018–2020, distritos de Satipo agrupados): solo agregable a provincia |
| `ambito_lima`, `ambito_lima_metodo` | provincia_hogar; id_estrato | LIMA_METROPOLITANA, LIMA_REGION o CALLAO (corrección 8 de Lima en tres ámbitos, 9/10/2026). Método `ubigeo` desde 2018; `estrato` en 2015–2017 (LM = estrato 15-1; LR = 15-2 y 15-3; Ficha ENDES 2015–2017, Cuadro N.º 1; decisión L2), con aviso de método |
| `pernocto`, `residente_habitual` | HV103, HV102 | |
| `edad_meses`, `sexo` | HC1, HC27 | |
| `hb_resultado`, `hb_medida` | HC55 | `hb_medida` = HC55 = 0 |
| `hb_observada`, `hb_ajustada_hist`, `anemia_hist_nivel`, `anemia_hist` | HC53, HC56, HC57 | Serie con el criterio anterior (RM 363-2022 desde 2024). Nivel 1 grave, 2 moderada, 3 leve, 4 sin anemia |
| `hb_ajustada_oms2024`, `anemia_oms2024_nivel`, `anemia_oms2024` | HC56A, HC57A | Solo desde 2024 (RM 251-2024-MINSA) |
| `haz`, `haz_bandera`, `haz_valido`, `dci`, `dci_severa` | HC70 | `haz` = HC70/100 si HC70 < 9990; `dci` = haz < −2; `dci_severa` = haz < −3 |

Los códigos especiales (9, 999, 9996–9999 y perdidos de SPSS) pasan a nulo. Definiciones del INEI para cada indicador: `curados/capa0/definiciones_endes.yaml`.

### enaho_sumaria (`encuestas/enaho_sumaria.parquet`)

Hogares de la ENAHO, módulo 34 «Sumarias», 2024 y 2025 (67 393 filas). Clave: `anio, id_conglomerado, vivienda, hogar`.

| Columna | Regla |
|---|---|
| `id_estrato_diseno` | departamento × estrato: la muestra es independiente en cada departamento (ficha técnica). Se conserva `estrato` (1–8) |
| `area` | urbano = estratos 1–5; rural = 6–8 (definición del INEI) |
| `ambito_lima` | LIMA_METROPOLITANA (provincia 1501), CALLAO, LIMA_REGION: el ranking departamental del INEI (26 ámbitos, L8). Se publican con el aviso `ambito_no_dominio` (L1, R-ENC-08) |
| `lima_metropolitana_dominio8` | dominio 8 = provincia de Lima + Callao: el de las tablas por área o dominio; se rotula siempre «Lima Metropolitana y Callao» (L3, 9/10/2026) |
| `peso_persona` | factor07 × mieperho (cifras de personas) |
| `pobre`, `pobre_extremo` | pobreza ≤ 2; pobreza = 1 |
| `linea`, `linpe`, `gashog2d`, `inghog2d` | Tal como vienen |

### fact_mapa_pobreza (`mapa_pobreza/fact_mapa_pobreza.parquet`)

Mapa de Pobreza Monetaria Provincial y Distrital 2018 (Anexo Estadístico): 1 874 distritos y 196 provincias, en la geografía vigente en 2018. Clave: `edicion, nivel, ubigeo_inei`.

| Columna | Regla |
|---|---|
| `pobreza_ic_inf`, `pobreza_ic_sup` | Intervalo al 95 % (%). **El INEI no publica una cifra puntual y no se calcula un punto medio** |
| `id_agrupamiento`, `estimado_en_agrupamiento` | 476 distritos chicos estimados juntos en 197 agrupamientos (comparten intervalo) |
| `grupo_robusto_nacional`, `orden_nacional` | 28 grupos de distritos (Anexo1) y 16 de provincias (A4). Pachangara (150906) falta en el Anexo1: su grupo (16) se infiere de su agrupamiento (`grupo_nacional_inferido`) |
| `grupo_robusto_regional`, `ambito_grupo_regional`, `orden_regional` | Grupos dentro de cada departamento (A3.x); Lima en dos ámbitos: provincia de Lima y Región Lima |
| `poblacion_proyectada_2020` | La que trae el anexo (proyectada a 2020, no a 2018) |
| `grupo_comparable_geo2017` | Desde `dim_ubigeo_historico`, para cruzar con otras fuentes |
"""

# -- 12. Pruebas de consistencia (las llama consolida_reglas.py; cada falla es (tipo, regla, valor)).
TEXTOS_LIMA_OBSOLETOS = [  # no deben quedar en reglas vigentes ni en especificaciones
 r"se fusionan en 'Lima \(departamento 15\)'", r'ambos pasan a Lima \(15\)', r'ejecutoras con sede en provincia 1501',
 r'en pobreza ENAHO = provincia de Lima \+ Callao', r'pobreza ENAHO: 1501 \+ 0701', r'solo DIRIS y UGEL',
 r'en otros años separa Lima Metropolitana', r'si se pide Callao, publicar el agregado', r'DEPARTAMENTO_META=15 mezcla']
MENSAJES_LIMA_L = ['R-ENC-07', 'R-ENC-08', 'R-TERRITORIO-06', 'R-TERRITORIO-09', 'R-GASTO-03', 'R-REG-07']
def PRUEBAS_LIMA_L(by, vig, NR, CAMPOS, DECISIONES, E, JERGA, MAX, textos, sin_marcas, raiz):
    import json as _j, os as _o, re as _r
    F = []
    esp = {'LIMA_METROPOLITANA': 3, 'LIMA_REGION': 3.5, 'CALLAO': 4, 'AREA_METROPOLITANA_LIMA_CALLAO': 4.5,
           'departamento': 4, 'provincia': 3, 'dominio_subnacional': 5}
    for k, v in esp.items():
        if NR.get(k) != v: F.append(('lima_nivel_rank', 'NIVEL_RANK', f'{k}={NR.get(k)}'))
    if 'Lima Metropolitana, Lima Provincias, Callao (ENDES)' in NR.get('nota', ''): F.append(('lima_nivel_rank', 'NIVEL_RANK', 'nota vieja'))
    txt = {i: _j.dumps({k: v for k, v in by[i].items() if not k.startswith('_') and not k.startswith('hallazgos')
                        and not k.startswith('decisiones_')}, ensure_ascii=False) for i in vig}
    txt['especificaciones'] = _j.dumps(E, ensure_ascii=False)
    for i, s in txt.items():
        for p in TEXTOS_LIMA_OBSOLETOS:
            if _r.search(p, s): F.append(('lima_texto_obsoleto', i, p))
    c01 = by['R-CRUCES-01']
    if 'contencion' not in c01['parametros'].get('dominios_lima', {}) or 'contiene' not in c01['condicion']:
        F.append(('cruces01_sin_contencion', 'R-CRUCES-01', ''))
    if 'LIMA_METROPOLITANA + CALLAO' not in _j.dumps(c01['parametros']['dominios_lima'], ensure_ascii=False):
        F.append(('cruces01_sin_dominio8', 'R-CRUCES-01', ''))
    e08 = by['R-ENC-08']
    if not all(x in e08['condicion'] for x in ('ambito_publicado', 'ambitos_publicados', 'ambito_no_dominio')) \
            or 'ambito_no_dominio' not in e08['parametros'].get('avisos', {}):
        F.append(('enc08_sin_rama_ambito_publicado', 'R-ENC-08', ''))
    for k, t in e08['parametros']['avisos'].items():  # cada aviso, medido como mensaje ciudadano
        if len(t) > MAX or JERGA.search(sin_marcas(t)): F.append(('aviso_con_jerga_o_largo', 'R-ENC-08', k))
    for i in MENSAJES_LIMA_L:
        for t in textos(by[i].get('mensaje_usuario') or ''):
            if len(t) > MAX or JERGA.search(sin_marcas(t)): F.append(('mensaje_lima_con_jerga_o_largo', i, t[:60]))
    rot = by['R-ENC-07']['parametros']['dominios_lima'].get('rotulos', {})
    if rot.get('AREA_METROPOLITANA_LIMA_CALLAO') != 'Lima Metropolitana y Callao' or 'Lima Metropolitana y Callao' not in _j.dumps(E['dim_ambito'], ensure_ascii=False):
        F.append(('rotulo_dominio8', 'R-ENC-07/dim_ambito', str(rot)))
    amb = by['R-TERRITORIO-09']['parametros']['ambiguos_conocidos']
    orden = ['Lima Metropolitana (provincia', 'Lima Región', 'departamento de Lima completo', 'Lima Metropolitana y Callao']
    if len(amb.get('Lima', [])) != 4 or not all(a.startswith(o) for a, o in zip(amb['Lima'], orden)) \
            or amb.get('Callao') != ['departamento 07 (Callao, 7 distritos)']:
        F.append(('territorio09_lima_orden', 'R-TERRITORIO-09', str(amb)))
    g03 = _j.dumps({k: by['R-GASTO-03'].get(k) for k in ('condicion', 'parametros', 'implementacion')}, ensure_ascii=False)
    cam = {x[0]: x[3] for x in CAMPOS}
    if 'cuenta_en_ambito' not in g03 or "'07'" not in g03 or 'alias' not in cam.get('cuenta_en_lima', '').lower() \
            or 'cuenta_en_ambito' not in cam or 'Callao' not in by['R-GASTO-03']['mensaje_usuario']:
        F.append(('gasto03_sin_marca_unica', 'R-GASTO-03', ''))
    p03, p04 = by['R-ENC-03']['parametros'], by['R-ENC-04']['parametros']
    if p04.get('cv_referencial_inei') != p03['cv_publicar'] or 'cv_referencial_inei' not in by['R-ENC-04']['condicion']:
        F.append(('enc04_sin_cv_inei', 'R-ENC-04', str(p04.get('cv_referencial_inei'))))
    u = by['R-ENC-12']['parametros'].get('unidades_ranking_departamental', {}).get('unidades', [])
    if len(u) != 26 or len(set(u)) != 26 or '07' in u or '15' in u or sum(x.isdigit() for x in u) != 23:
        F.append(('ranking_no_26', 'R-ENC-12', str(len(u))))
    sien = by['R-REG-07']['parametros'].get('sien_ambitos_lima', {})
    if sien.get('rotulo_denominador_propio') != 'población estimada (cálculo propio)' or sien.get('margen_umbral_pp') != 1:
        F.append(('sien_l7_incompleto', 'R-REG-07', ''))
    ids = {d[0] for d in DECISIONES}
    for k in ('L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9'):
        if k not in ids: F.append(('decision_lima_faltante', '-', k))
    if not any('PR-03' in d[5] for d in DECISIONES if d[0] == 'L3'): F.append(('pr03_no_anulada', 'L3', ''))
    ya = _o.path.join(raiz, 'curados', 'capa0', 'ambitos.yaml')
    if _o.path.exists(ya):
        import yaml as _y
        ids_a = {a['ambito_id'] for a in _y.safe_load(open(ya))}
        for k in ROTULOS_LIMA:
            if k != 'departamento_15' and k not in ids_a: F.append(('ambito_inexistente', 'ambitos.yaml', k))
    inf = _o.path.join(raiz, 'catalogo', 'inferencia_verificada.csv')
    if _o.path.exists(inf):
        import csv as _c
        for x in _c.DictReader(open(inf, encoding='utf-8')):
            for a in [t.strip() for t in (x.get('ambitos_publicados') or '').split(';') if t.strip()]:
                if a not in ('LIMA_METROPOLITANA', 'LIMA_REGION', 'CALLAO'): F.append(('ambito_publicado_invalido', 'R-ENC-08', f"{x['fuente']} {x['anio']}: {a}"))
                elif x.get('inferencia_verificada') != 'true' or not all(x.get(k) for k in ('ambitos_cita_url', 'ambitos_cita_documento', 'ambitos_cita_ubicacion')): F.append(('ambito_publicado_sin_verificar', 'R-ENC-08', f"{x['fuente']} {x['anio']}: {a}"))
    return F

# ---------------------------------------------------------------- correcciones de la auditoría de P1 (9/10/2026)
# 03_auditoria/lima_tres_ambitos/implementacion/auditoria_p1/auditoria.md (H1–H10). H3, H8 (b), H9 y H11 (alcance de
# impacto_L9) se corrigieron arriba, en su propio bloque; aquí el resto y las pruebas nuevas.
# H1. PR-03 seguía en R-ENC-06.casos_borde.
PARCHES_REGLAS_R3 += [
 ('R-ENC-06', 'Lima Metropolitana NO equivale a la provincia 1501: en los informes de pobreza ENAHO del INEI incluye la '
              'Provincia Constitucional del Callao (1501 + 0701).',
  'Lima Metropolitana es la provincia 1501 (43 distritos); el dominio 8 de la ENAHO (1501 + 07) se rotula siempre «Lima '
  'Metropolitana y Callao» (' + _L + ', L3; anula PR-03 del 5/10).'),
]
TEXTOS_LIMA_OBSOLETOS += [r'NO equivale a la provincia 1501', r'Provincia Constitucional del Callao \(1501 \+ 0701\)']
# H2. R-ENC-06 no baja al dpto 15 los ámbitos de Lima antes de la rama de R-ENC-08.
AGREGADOS_REGLAS_R3 += [
 ('R-ENC-06', 'condicion',
  ' Excepción (' + _L + ', L1 y L2): si nivel_pedido es un ámbito de dim_dominio (encuesta, año) con ambito_id ∈ '
  '{LIMA_METROPOLITANA, LIMA_REGION, CALLAO, AREA_METROPOLITANA_LIMA_CALLAO} (tipo dominio_diseno o ambito_publicado), no '
  'se degrada por rango: lo decide R-ENC-08. Una provincia o un distrito del departamento 15 se lleva al ámbito que lo '
  'contiene (LM o LR), no al departamento.'),
]
# H4. R-CRUCES-11 conoce subdivision_lima de cruces_permitidos.yaml (CR-01, L5).
CAMPOS_REGLAS += [('R-CRUCES-11', 'parametros.campos_tabla',
                   ['id_cruce', 'indicador_a', 'indicador_b', 'nivel_minimo', 'ventana_anios', 'rezago_anios',
                    'presentacion (lado_a_lado|asociacion|cociente)', 'poblacion_objetivo_comun', 'nota_metodologica',
                    'aprobado_por', 'fecha_aprobacion', 'subdivision_lima'])]
AGREGADOS_REGLAS_R3 += [
 ('R-CRUCES-11', 'condicion',
  '. Si la fila trae subdivision_lima (' + _L + ', L5), sus ámbitos reemplazan a los departamentos que subdividen (15 → '
  'LIMA_METROPOLITANA, LIMA_REGION; 07 → CALLAO) y no se comparan con nivel_minimo, que sigue rigiendo para los demás '
  'departamentos; los años de cada ámbito son los de su lista anios (L5: 2025 solo con dim_dominio ENDES 2025 '
  'confirmado; anios_condicionados con activo = false lo excluyen ese año).'),
 ('R-CRUCES-01', 'implementacion',
  ' Cruces de la lista blanca con subdivision_lima (CR-01 y los que la declaren, R-CRUCES-11): Lima y el Callao se cruzan '
  'ámbito a ámbito con el mapeo de la fila (' + _L + ', L5).'),
]
# H5. L7 en la implementación de R-REG-07; D14 reemplazada en parte por L7.
PARCHES_REGLAS_R3 += [
 ('R-REG-07', 'se publica solo por departamento, con dos cotas',
  'se publica por departamento y por LIMA_METROPOLITANA, LIMA_REGION y CALLAO (L7), con dos cotas'),
]
DECISIONES_R3 = [(d[:5] + ('Adoptada (7/10/2026); reemplazada en parte por L7 (9/10/2026): también por Lima Metropolitana, '
                           'Lima Región y Callao.',)) if d[0] == 'D14' else d for d in DECISIONES_R3]
# H6. «departamento de Lima» siempre con su sentido; «Lima Región (Lima Provincias)».
PARCHES_REGLAS_R3 += [
 ('R-ENC-07', 'Esta cifra corresponde a {dominio} (definido por la encuesta), no a todo el departamento de Lima.',
  'Esta cifra corresponde a {ambito_largo}, no a todo el departamento de Lima (Lima Metropolitana + Lima Región).'),
 ('R-ENC-07', 'Dominios: Lima Metropolitana, Lima Provincias, Callao y ámbitos solo urbanos',
  'Dominios: Lima Metropolitana, Lima Región (Lima Provincias), Callao y ámbitos solo urbanos'),
 ('R-ENC-06', 'Mostramos la del departamento de {departamento}, que incluye',
  'Mostramos la de {territorio_contenedor_largo}, que incluye'),
 ('R-TERRITORIO-06', "Esta encuesta divide Lima en 'Lima Metropolitana' y 'Lima Provincias' (y trata el Callao aparte o "
                     "junto, según el año). La cifra corresponde a {dominio}, que incluye",
  "La encuesta separa 'Lima Metropolitana' (provincia de Lima) y 'Lima Región' (Lima Provincias); el Callao va aparte o "
  "junto con Lima Metropolitana, según la encuesta y el año. La cifra corresponde a {ambito_largo}, que incluye"),
 ('R-TERRITORIO-06', 'Dominios de encuesta: Lima Metropolitana, Lima Provincias y Callao no se derivan',
  'Dominios de encuesta: Lima Metropolitana, Lima Región (Lima Provincias) y Callao no se derivan'),
 ('R-GASTO-01', 'cuentan en el departamento de Lima, no en Lima Metropolitana ni en Lima Región.',
  'cuentan en el departamento 15 entero (Lima Metropolitana + Lima Región), no en Lima Metropolitana ni en Lima Región.'),
]
# H7. R-CRUCES-06: las 26 unidades de L8 son un solo nivel.
AGREGADOS_REGLAS_R3 += [
 ('R-CRUCES-06', 'implementacion',
  ' Excepción (' + _L + ', L8): las 26 unidades de R-ENC-12 (23 departamentos + Lima Metropolitana + Lima Región + Callao) '
  'cuentan como un solo nivel para la correlación nacional.'),
]
# H8 (a). R-MOTOR-01: el dominio 8 no retrocede a departamento.
AGREGADOS_REGLAS_R3 += [
 ('R-MOTOR-01', 'casos_borde',
  ' [' + _L + '] El dominio 8 (AREA_METROPOLITANA_LIMA_CALLAO, rango 4,5) no baja a departamento, que no lo contiene: sigue '
  'con agrupar años y después nacional.'),
]
# H10. Una sola definición de cuenta_en_lima (alias de cuenta_en_ambito en el 15).
PARCHES_REGLAS_R3 += [
 ('R-GASTO-03', '[E3, 8/10/2026] cuenta_en_lima (columna de fact_gasto_territorial; el validador la lee, no la recalcula) :=',
  '[E3, 8/10/2026; sustituida por L6: cuenta_en_lima := cuenta_en_ambito AND departamento_atribucion = \'15\'; se conserva '
  'como historia] cuenta_en_lima (columna de fact_gasto_territorial; el validador la lee, no la recalcula) :='),
]
for _k in ('R-ENC-06', 'R-CRUCES-11', 'R-MOTOR-01'):
    HALLAZGOS_L.setdefault(_k, [])
HALLAZGOS_L['R-ENC-06'] += ['L1 y L3: ámbitos de Lima sin degradar antes de R-ENC-08; anula PR-03']
HALLAZGOS_L['R-CRUCES-11'] += ['L5: subdivision_lima de cruces_permitidos']
HALLAZGOS_L['R-MOTOR-01'] += ['dominio 8 sin retroceso a departamento']
MENSAJES_LIMA_L = MENSAJES_LIMA_L + ['R-ENC-06']

_PRUEBAS_LIMA_BASE = PRUEBAS_LIMA_L
def PRUEBAS_LIMA_L(by, vig, NR, CAMPOS, DECISIONES, E, JERGA, MAX, textos, sin_marcas, raiz):
    import json as _j, os as _o, re as _r, csv as _c
    F = _PRUEBAS_LIMA_BASE(by, vig, NR, CAMPOS, DECISIONES, E, JERGA, MAX, textos, sin_marcas, raiz)
    # H2
    if not all(x in by['R-ENC-06']['condicion'] for x in ('R-ENC-08', 'ambito_id')): F.append(('enc06_degrada_ambitos', 'R-ENC-06', ''))
    # H6: «departamento de Lima» sin decir en qué sentido
    for i in MENSAJES_LIMA_L:
        for t in textos(by[i].get('mensaje_usuario') or ''):
            if _r.search(r'departamento de Lima(?! \()', t): F.append(('departamento_de_lima_sin_sentido', i, t[:60]))
    # H3: ENAHO sin 07 en excluye_departamentos → CALLAO en ambitos_publicados
    inf = _o.path.join(raiz, 'catalogo', 'inferencia_verificada.csv')
    if _o.path.exists(inf):
        for x in _c.DictReader(open(inf, encoding='utf-8')):
            if x['fuente'] == 'INEI-ENAHO' and x.get('inferencia_verificada') == 'true' and '07' not in (x.get('excluye_departamentos') or '') \
                    and 'CALLAO' not in (x.get('ambitos_publicados') or ''):
                F.append(('enaho_callao_sin_rama', 'R-ENC-08', x['anio']))
    if 'por_departamento' not in by['R-ENC-08']['condicion']: F.append(('enc08_sin_dpto15_enaho', 'R-ENC-08', ''))
    # H4: subdivision_lima de cruces_permitidos.yaml
    cy = _o.path.join(raiz, 'curados', 'capa0', 'cruces_permitidos.yaml')
    if _o.path.exists(cy):
        import yaml as _y
        for cr in _y.safe_load(open(cy)).get('cruces', []):
            sub = cr.get('subdivision_lima')
            if not sub: continue
            if 'subdivision_lima' not in by['R-CRUCES-11']['parametros']['campos_tabla'] or 'subdivision_lima' not in by['R-CRUCES-11']['condicion']:
                F.append(('cruces11_sin_subdivision_lima', 'R-CRUCES-11', cr['id_cruce']))
            for a in sub.get('ambitos', []):
                if NR.get(a.get('nivel')) != a.get('rango'): F.append(('subdivision_rango_distinto', cr['id_cruce'], f"{a.get('nivel')}={a.get('rango')}"))
    # H9: vocabulario de dim_dominio.tipo igual al de P2 (territorio.TIPOS_DOMINIO)
    tp = _o.path.join(raiz, 'src', 'pap', 'capa0', 'territorio.py')
    if _o.path.exists(tp):
        m = _r.search(r'TIPOS_DOMINIO\s*=\s*\{([^}]*)\}', open(tp, encoding='utf-8').read())
        tipos = set(_r.findall(r'"([a-z_]+)"', m.group(1))) if m else set()
        s_ = _j.dumps({i: by[i] for i in ('R-TERRITORIO-06', 'R-ENC-08', 'R-ENC-06')}, ensure_ascii=False) + _j.dumps(E['dim_ambito'], ensure_ascii=False)
        if tipos != {'dominio_diseno', 'ambito_publicado'} or _r.search(r'tipo ∈ \{dominio,|tipo dominio o', s_):
            F.append(('vocabulario_tipo_dominio', 'R-TERRITORIO-06/R-ENC-08', str(sorted(tipos))))
    # H10
    g = by['R-GASTO-03']['condicion']
    if 'sustituida por L6' not in g: F.append(('cuenta_en_lima_dos_definiciones', 'R-GASTO-03', ''))
    # H5
    if 'se publica solo por departamento' in json_dumps_safe(by['R-REG-07']): F.append(('reg07_solo_departamento', 'R-REG-07', ''))
    if not any(d[0] == 'D14' and 'L7' in d[5] for d in DECISIONES): F.append(('d14_sin_l7', 'D14', ''))
    return F
def json_dumps_safe(x):
    import json as _j
    return _j.dumps(x, ensure_ascii=False)

# ================================================================ Piloto, sprint P0 (decisiones del dueño, 10/10/2026)
# El dueño aprueba las recomendaciones pendientes de las tablas curadas (D-IND, D-AUD, D-DOR) y de Lima en tres ámbitos
# (V1–V6) «con cargo a revisarlas después del piloto». Aquí solo lo que toca las reglas; el resto vive en
# docs/decisiones.md y en curados/capa0/. Especificación del validador y el motor:
# docs/especificaciones/motor.md. Cambios:
#  - H1: vocabularios de tema, universo, periodicidad_estimacion y concepto_medido en parametros_globales.
#  - NIVEL_RANK: «establecimiento» = 1 (SIEN por establecimiento; antes era una extensión de dim_indicador).
#  - D-DOR-4: R-ENC-18 parte su tolerancia: 0,1 pp para la anemia de la ENDES y 0,5 pp solo para la ENLA.
#  - D-IND-7: matriz de R-DENOMINADORES-01 acepta la proyección departamental por edad para coberturas por departamento.
#  - D-AUD-1: R-DEP-01 evalúa las tablas solo curadas (dim_dominio, dim_tema_gasto) por su manifiesto.
#  - Corrección: la fila HEC-04 de la matriz de R-DENOMINADORES-01 quedó en una clave rota (la ruta tenía un punto).
_P0 = 'decisión del dueño del 10/10/2026, aprobada con cargo a revisión después del piloto'
NIVEL_RANK_D8 = dict(NIVEL_RANK_D8, establecimiento=1)
NOTA_NIVEL_RANK_D8 = NOTA_NIVEL_RANK_D8 + (' establecimiento (SIEN: establecimiento de salud) = 1, por debajo del distrito; '
                                           'una cifra por establecimiento lleva el rótulo «en el establecimiento…» (' + _P0 + ').')
PARAMETROS_GLOBALES_P0 = {'VOCABULARIOS_INDICADOR': {
    'nota': ('Vocabularios controlados de dim_indicador que no estaban en las reglas (hallazgo H1 de la auditoría de las tablas '
             'curadas; ' + _P0 + '). Un valor fuera de la lista detiene la carga de dim_indicador (prueba IND-04). Se amplían '
             'aquí, con el indicador que lo necesita.'),
    'tema': ['anemia', 'desnutricion_cronica', 'gasto_publico', 'pobreza_monetaria'],
    'universo': ['total', 'sector_publico', 'sector_publico_minsa'],
    'periodicidad_estimacion': ['anual', 'unica'],
    'concepto_medido': ['anemia_6_35m', 'cobertura_tamizaje_hb_6_35m', 'dci_menor5', 'gasto_servicios_ex_pan',
                        'pobreza_monetaria'],
}}
_CLAVE_ROTA = 'tasa_poblacion_total (por 1 000 / 100 000 hab'
_CLAVE_BUENA = 'tasa_poblacion_total (por 1 000 / 100 000 hab., gasto per cápita)'
_CLAVE_COB = 'cobertura_salud_por_edad (vacunas <1 y <5, CRED, tamizaje, gestantes)'
TABLAS_SOLO_CURADAS_P0 = {'dim_dominio': 'manifiesto_s1_territorio', 'dim_tema_gasto': 'manifiesto_s3_gasto'}


def _p0_enc18(by):
    p = by['R-ENC-18']['parametros']
    assert p.pop('tolerancia_pp_anemia_enla') == 0.5
    p['tolerancia_pp_anemia_endes'] = 0.1
    p['tolerancia_pp_enla'] = 0.5
    p['tolerancia_nota'] = ('D-DOR-4 (' + _P0 + '): la anemia de la ENDES se compara con la misma tolerancia que el resto '
                            '(0,1 pp); 0,5 pp queda solo para la ENLA (medida de rendimiento). El CV publicado de la ENAHO es '
                            'dato y no bloquea (V4): aviso si el nuestro difiere en más de 0,5 puntos.')


def _p0_denominadores(by):
    m = by['R-DENOMINADORES-01']['parametros']['matriz']
    rota = m.pop(_CLAVE_ROTA)
    m[_CLAVE_BUENA] = rota[', gasto per cápita)']  # HEC-04 (auditoría v1.1): la fila que se quiso escribir
    m[_CLAVE_COB]['principal_por_departamento'] = (
        'INEI-PROYECCIONES-DEPARTAMENTAL-EDAD (mismo grupo de edad y año; 6-35 m = 0,5·P0 + P1 + P2 desde fact_poblacion_grupo) '
        'cuando la cobertura se publica solo por departamento (SIEN, R-REG-07). En los ámbitos de Lima (LM, LR) el denominador '
        'es el prorrateo propio (IPF) rotulado como tal (L7); el Callao, la proyección oficial del 07. D-IND-7, ' + _P0 + '.')


def _p0_dep01(by):
    r = by['R-DEP-01']
    r['parametros']['tablas_solo_curadas'] = dict(TABLAS_SOLO_CURADAS_P0)
    r['parametros']['criterio_tablas_solo_curadas'] = (
        'D-AUD-1 (' + _P0 + '): una tabla curada sin crudo propio en el catálogo pasa si está registrada en su manifiesto de la '
        'capa 0, ese manifiesto no tiene pruebas bloqueantes fallidas y las filas que usa la cifra están revisadas o confirmadas '
        '(dim_dominio: confirmado = true; dim_tema_gasto: tema aprobado por el dueño). Si no, estado_cifra = sin_datos.')
    r['condicion'] = r['condicion'].rstrip() + (
        '; ANY(t FOR t IN indicador.insumos WHERE t.id IN parametros.tablas_solo_curadas AND (t NOT IN manifiesto '
        'OR manifiesto.bloqueantes_fallidas != [] OR fila_usada.confirmado IS NOT TRUE)) → estado_cifra = \'sin_datos\', '
        'motivo = \'tabla_curada_sin_respaldo\'')


TRANSFORMACIONES_P0 = [_p0_enc18, _p0_denominadores, _p0_dep01]
HALLAZGOS_P0 = {
    'R-ENC-18': ['D-DOR-4: tolerancia partida (anemia ENDES 0,1 pp; ENLA 0,5 pp); V4: CV de la ENAHO como aviso'],
    'R-DENOMINADORES-01': ['D-IND-7: proyección departamental por edad para coberturas por departamento',
                           'Corrección P0: fila HEC-04 de la matriz en su clave correcta'],
    'R-DEP-01': ['D-AUD-1: tablas solo curadas evaluadas por su manifiesto'],
}
DECISIONES_D8 += [
 ('D-IND-7', 'Denominador de la cobertura de tamizaje del SIEN por departamento',
  'Prorrateo propio (IPF) o proyección departamental por edad.', 'Proyección departamental; IPF rotulado en LM y LR.',
  'R-DENOMINADORES-01, R-REG-07', 'Adoptada (' + _P0 + ').'),
 ('D-AUD-1', 'R-DEP-01 con tablas solo curadas (dim_dominio, dim_tema_gasto)',
  'Exigir un crudo en el catálogo o evaluarlas por su manifiesto.',
  'Por su manifiesto, sin bloqueantes fallidas y con filas revisadas.', 'R-DEP-01', 'Adoptada (' + _P0 + ').'),
 ('D-DOR-4', 'Tolerancia de R-ENC-18 para la anemia', '0,5 pp (como la ENLA) o 0,1 pp.',
  '0,1 pp para la ENDES; 0,5 pp solo para la ENLA.', 'R-ENC-18', 'Adoptada (' + _P0 + ').'),
 ('V4', 'CV de la ENAHO (D-ENA-1)', 'Bloquear por CV o solo por la cifra puntual.',
  'La cifra puntual bloquea; el CV avisa si difiere > 0,5 puntos.', 'R-ENC-18',
  'Adoptada (' + _P0 + '). En P1 se compara con el CV de svy.'),
 ('V6', 'Simetría de L9 (CV > 30 % en proporciones < 10 %)', 'Suprimir también o dejar referencial.',
  'Sin recomendación explícita: se mantiene lo implementado (referencial).', 'R-ENC-03, R-ENC-04',
  'Se mantiene lo implementado (' + _P0 + '); 13 celdas afectadas; se revisa después del piloto.'),
]
FECHA_ACTUALIZACION = ('2026-10-10', '10 de octubre de 2026')


def PRUEBAS_P0(by, raiz):
    """Consistencia del bloque P0: claves de la matriz sin rotas, tolerancias de R-ENC-18 iguales a las de cifras_doradas y
    vocabularios de dim_indicador dentro de VOCABULARIOS_INDICADOR."""
    import os as _o, csv as _c
    F = []
    m = by['R-DENOMINADORES-01']['parametros']['matriz']
    for k, v in m.items():
        if not isinstance(v, dict) or not any(x in v for x in ('principal', 'nota')):
            F.append(('matriz_clave_rota', 'R-DENOMINADORES-01', k[:60]))
    p = by['R-ENC-18']['parametros']
    if 'tolerancia_pp_anemia_enla' in p or p.get('tolerancia_pp_anemia_endes') != p.get('tolerancia_pp'):
        F.append(('enc18_tolerancia_anemia', 'R-ENC-18', ''))
    dor = _o.path.join(raiz, 'curados', 'capa0', 'cifras_doradas.csv')
    if _o.path.exists(dor):
        for x in _c.DictReader(open(dor, encoding='utf-8')):
            if x['proposito'] == 'R-ENC-18' and x['fuente_id'] == 'INEI-ENDES' and float(x['tolerancia_pp']) != p['tolerancia_pp_anemia_endes']:
                F.append(('dorada_tolerancia_distinta', 'R-ENC-18', x['id_cifra']))
    di = _o.path.join(raiz, 'curados', 'capa0', 'dim_indicador.yaml')
    if _o.path.exists(di):
        import yaml as _y
        voc = PARAMETROS_GLOBALES_P0['VOCABULARIOS_INDICADOR']
        for i in _y.safe_load(open(di, encoding='utf-8'))['indicadores']:
            for campo in ('tema', 'universo', 'periodicidad_estimacion', 'concepto_medido'):
                if i.get(campo) not in voc[campo]:
                    F.append(('vocabulario_indicador', i['id'], f'{campo}={i.get(campo)}'))
    return F

# ================================================================ Piloto, sprint P2 (auditoría del validador, 10/10/2026)
# H-18/N-7 de 00_proyecto/piloto/p2/auditoria/dictamen.md: umbrales que estaban solo en el texto de la condición pasan a
# `parametros` para que el validador no los escriba a mano. No cambian ninguna regla (mismos valores que el texto).
def _p2_parametros(by):
    by['R-EST-05']['parametros']['edad_maxima_anios'] = 5
    by['R-ENC-04']['parametros']['n_efectivo_suprimir'] = 30


TRANSFORMACIONES_P0 = TRANSFORMACIONES_P0 + [_p2_parametros]
HALLAZGOS_P0 = dict(HALLAZGOS_P0)
HALLAZGOS_P0['R-EST-05'] = ['P2 (auditoría N-7): edad_maxima_anios = 5 en parametros (estaba solo en el texto)']
HALLAZGOS_P0['R-ENC-04'] = ['P2 (auditoría N-7): n_efectivo_suprimir = 30 en parametros (estaba solo en el texto)']

# ================================================================ Piloto, P4 (decisión del dueño, 11/10/2026; cierra H7)
# Un quiebre por modo de entrevista (ENDES 2020) excluye solo ese punto: no se compara con ese año, pero sí a través de él,
# como hace el INEI (Indicadores PPR 2024, Cuadro 06A: 2024/2019; PPR 2025: 2025/2021) y como ya decía el ejemplo de
# R-ENC-13 («la tendencia se informa 2019 vs 2024»). Los quiebres de criterio, marco o cuestionario siguen cortando la
# serie en tramos. ENDES 2021 es comparable (el INEI solo marca 2020). Análisis: 00_proyecto/piloto/p4/analisis_5_decisiones.md
_P4 = 'decisión del dueño, 11/10/2026, P4'


def _p4_quiebre_modo(by):
    r = by['R-ENC-11']
    r['casos_borde'] = _cambia(r['casos_borde'], 'Comparación a través de un quiebre (R-ENC-13/14): bloqueada.',
                               'Comparación a través de un quiebre de criterio, marco o cuestionario (R-ENC-13/14): '
                               'bloqueada. Quiebre por modo de entrevista (ENDES 2020): se bloquea solo la comparación con '
                               'ese año; a través de él se compara, con el punto excluido (' + _P4 + ').')
    r = by['R-ENC-13']
    r['implementacion'] = r['implementacion'].rstrip() + (
        ' [' + _P4 + '] Un quiebre de tipo modo (modo de entrevista) no corta la serie: excluye ese año de la tendencia y '
        'de las comparaciones con él, y permite comparar años de ambos lados (2019 vs 2024, como el INEI). Los demás tipos '
        'cortan la serie en tramos. ENDES 2021 se trata como comparable (H7 cerrado: el INEI solo marca 2020).')


TRANSFORMACIONES_P0 = TRANSFORMACIONES_P0 + [_p4_quiebre_modo]
HALLAZGOS_P0['R-ENC-11'] = HALLAZGOS_P0.get('R-ENC-11', []) + ['P4 (11/10/2026): el quiebre por modo de entrevista bloquea solo la comparación con ese año']
HALLAZGOS_P0['R-ENC-13'] = HALLAZGOS_P0.get('R-ENC-13', []) + ['P4 (11/10/2026): el quiebre de modo no corta la serie; ENDES 2021 comparable (cierra H7)']
