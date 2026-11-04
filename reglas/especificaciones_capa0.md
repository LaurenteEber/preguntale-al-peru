# Especificaciones de tablas de la capa 0

Propuestas por el ámbito territorio y denominadores (fase 2). La tabla de ubigeo histórico la construye el proyecto (decisión del 5/10/2026).

## dim_ubigeo_historico

Dimensión territorial con vigencia (tipo SCD-2): una fila por versión de cada unidad (departamento, provincia, distrito) desde la geografía del CPV2017 hasta hoy; es la llave de todos los cruces (R-TERRITORIO-01) y la base de la geografía congelada (R-TERRITORIO-04).

| Columna | Tipo | Regla |
|---|---|---|
| `id_version` | int PK | sustituta; una por (ubigeo_inei, vigente_desde) |
| `ubigeo_inei` | char(6) | con ceros a la izquierda; 2 dígitos dpto + 2 prov + 2 dist; para provincia 'DDPP00', departamento 'DD0000' |
| `ubigeo_reniec` | char(6) null | desde puente_ubigeo (R-TERRITORIO-03); null mientras RENIEC no asigne |
| `nombre` | text | nombre oficial según la norma de creación/ el INEI, con tildes |
| `nombre_normalizado` | text | mayúsculas sin tildes ni signos (para emparejar) |
| `nombres_alternos` | text[] | variantes vistas en fuentes (p. ej. 'UNION ASHANINKA', 'UNIÓN ASHÁNINKA') |
| `nivel` | enum(departamento, provincia, distrito) | — |
| `ubigeo_padre` | char(6) | unidad jerárquica superior vigente en esa versión (provincia del distrito; departamento de la provincia) |
| `vigente_desde` | date | día siguiente a la publicación de la ley en El Peruano (vigencia legal); '2017-10-22' para unidades preexistentes al CPV2017 |
| `vigente_hasta` | date null | null si vigente; para el distrito madre NO se cierra la versión por perder territorio, se abre una nueva versión con territorio_modificado=true |
| `origen` | enum(preexistente_2017, creacion, escision, fusion, anexion, cambio_codigo, cambio_nombre, cambio_capital, cambio_provincia) | creacion = sobre territorio sin distrito (raro); escision = hijo segregado de uno o más distritos; cambio_provincia = distrito que pasa a provincia nueva (p. ej. Putumayo) |
| `territorio_modificado` | bool | true en la versión del distrito madre posterior a una escisión |
| `norma_legal` | text | 'Ley N.º 31644'; solo leyes que crean (las leyes declarativas de interés nacional, como la Ley 31513, NO crean distritos) |
| `fecha_publicacion_norma` | date | fecha en El Peruano |
| `url_norma` | url | El Peruano o leyes.congreso.gob.pe |
| `fecha_alta_inei` | date null | primera publicación INEI que trae el código (lista de ubigeos, proyecciones o Directorio) |
| `anio_primeros_datos_registros` | int null | primer año en que los registros principales (CNV, SIS, MEF) usan el código; se llena con R-TERRITORIO-05 |
| `grupo_comparable_geo2017` | char(6)\|'G-'+id | distrito 2017 del que procede o código de grupo si procede de varios |
| `fuente` | text[] | IDs del catálogo y documentos usados (INEI-PNDA-UBIGEOS, INEI-PROYECCIONES-POBLACION-DISTRITAL, INEI-DIRECTORIO-MUNICIPALIDADES, Lib1860 Anexo 3, ley) |
| `estado_verificacion` | enum(verificado_ley, verificado_inei, pendiente) | solo 'verificado_*' entra a producción |
| `version_tabla` | text | semver de la tabla (v1.0 = 1 892 distritos) |
| `region_natural_ref, pct_poblacion_urbana_cpv2017` | text, numeric | descriptivos opcionales (R-TERRITORIO-07) |
| `nombre_oficial_inei` | text | Nombre tal como lo publica el INEI (mayúsculas, sin tildes). Se usa para emparejar fuentes. |
| `nombre_mostrado` | text | Nombre con tildes y mayúsculas correctas para mostrar al usuario. Fuente (decisión del dueño, 6/10/2026): INEI, Directorio Nacional de Municipalidades 2025, que se cita como fuente (columna fuente_nombre_mostrado); si la unidad no figura en el Directorio (departamentos, distritos creados después de feb-2025), el archivo propio o la ley de creación. |
| `capital_legal, lat_capital, lon_capital, altitud_capital` | text, numeric | Capital legal y su ubicación (no es el centro del territorio). Fuente primaria: INEI, Directorio Nacional de Municipalidades 2020 (Lib1725), vía el archivo propio. |
| `tipologia_pcm` | text | Tipología de distrito de la PCM (RV N.° 005-2019-PCM/DVGT, anexo 2), vía el archivo propio; confirmar si hay versión más reciente. |

**tabla_relacion**

{"rel_ubigeo_origen": "ubigeo_hijo, ubigeo_origen, tipo (escision\|fusion\|anexion\|cambio_codigo), es_origen_principal bool, poblacion_cedida_cpv2017 (suma de centros poblados transferidos, si se puede reconstruir), fuente; permite hijos con varios orígenes (Alto Trujillo)."}

**construccion**

- 1. Base 2017: lista de distritos del CPV2017 (REDATAM/tomos) → origen='preexistente_2017'. Comprobar que coincide con la lista de Lib1715 (1 874 distritos a dic-2019).
- 2. Altas 2018–2022: Anexo 3 de Lib1860 ('Dispositivos legales de modificación de ámbitos territoriales', 16 distritos creados 2020–2021) y Directorio Nacional de Municipalidades 2021 (sección 1.2, por nombre) → para cada uno, leer la ley en El Peruano: fecha de publicación, distrito(s) de origen (artículo de límites), capital.
- 3. Altas 2022–hoy: anti-join entre INEI-PNDA-UBIGEOS (corte 2022, 1 891) y la lista de INEI-PROYECCIONES-POBLACION-DISTRITAL (1 892) + Directorio 2025 (196 provinciales + 1 695 distritales = 1 891 municipalidades con autoridades); toda diferencia se documenta con su ley.
- 4. Cambios de código y de provincia: comparar la base 2017 con la lista vigente por nombre dentro de la provincia; los códigos que cambian (p. ej. 160109/160114 → 160801/160803 por la provincia de Putumayo) se cargan como cambio_codigo/cambio_provincia con vigente_hasta en el código anterior.
- 5. Grupos comparables: para cada hijo, grupo_comparable_geo2017 = su origen principal si tiene uno; si tiene varios, crear grupo 'G-' con la unión y asignarlo también a los orígenes.
- 6. Puente RENIEC: R-TERRITORIO-03.
- 7. Revisión humana de toda fila nueva antes de marcarla 'verificado_ley'.

**validacion**

- Conteo: distritos vigentes al 2026-10-05 = 1 892 (lista de proyecciones dic-2025); si la cuenta difiere, la carga de la tabla falla.
- Distrito 1 892: identificar con el anti-join del paso 3. Candidatos a verificar: Alto Trujillo (130112, Ley 31644, publicada 15-12-2022; ausente en el puente 2021) y San Antonio (Mariscal Nieto, Moquegua; Ley 31216 de 2021, ratificada por el TC el 05-10-2023; ausente con código INEI en el puente 2021). Notar que el puente 2021 ya trae 16 creaciones 2020–2021 (coherente con 1 890 en Lib1860), por lo que las altas 1 891 y 1 892 son posteriores a 2021.
- Unicidad: un solo registro vigente por ubigeo_inei y por ubigeo_reniec en cualquier fecha.
- Jerarquía: todo ubigeo_padre existe y está vigente en el mismo intervalo; los 4 primeros dígitos del distrito = provincia padre.
- Cobertura de grupos: todo distrito vigente tiene grupo_comparable_geo2017 y todo grupo contiene al menos un distrito de 2017.
- Conservación de población: Σ proyección INEI (año t) de los distritos de un grupo = proyección del grupo; Σ distritos de un departamento = total departamental publicado (tolerancia 0,1 %).
- Ningún código de la tabla puede ser un centro poblado (p. ej. 150144 'Santa María de Huachipa' del puente GitHub).

**mantenimiento**

- Mensual: búsqueda en El Peruano de 'Ley de creación del distrito' y de leyes de demarcación y organización territorial (SDOT-PCM); cada alta se carga como 'pendiente' con fecha de vigencia legal.
- Anual: al publicarse el Directorio Nacional de Municipalidades y la proyección distrital de diciembre, conciliar conteo y códigos; pasar las altas a 'verificado_inei' cuando el INEI publique el código.
- En cada carga de fuente: registrar los códigos no resueltos; si aparece un código desconocido en ≥ 2 fuentes, abrir revisión (posible distrito nuevo).
- Versionar la tabla (version_tabla) y guardar en cada resultado la versión usada; nunca editar una versión publicada (solo añadir filas).

## puente_ubigeo

Ver R-TERRITORIO-03 (esquema y pasos).

## dim_dominio

Ver R-TERRITORIO-06 (esquema).

## fact_poblacion

fuente_id, vintage, metodo (oficial\|prorrateo_propio\|censado), geografia_base (vigente_AAAA\|GEO2017), ubigeo_inei, anio, fecha_referencia, edad_min, edad_max, sexo (T\|M\|F), valor, semilla, iteraciones_ipf, error_max_ipf.

## tablas_curadas_mvp

**imprescindibles**

- dim_indicador (todos los campos de nivel indicador)
- dim_ubigeo_historico
- dim_dominio
- fact_poblacion
- dim_unidad_ejecutora
- dim_tema_gasto
- dim_inversion_ubicacion
- dim_ipc (BCRP PN38705PM)
- cobertura_registro_estimada (nombre único; insumos: nacimientos y defunciones estimados INEI por departamento y año)
- validaciones
- puente_ubigeo (si alguna fuente MVP resulta RENIEC)

**con_respaldo_vacias**

{"cruces_permitidos": "sin fila → lado a lado", "evaluaciones_relacionadas": "frase fija", "ambito_ejecutora": "ya no está vacía: curados/capa0/ejecutoras_alcance.yaml (ejecutoras del Gobierno Nacional con meta en Lima; L6 la extiende a las de meta 07), leída por dim_unidad_ejecutora y la fact (R-GASTO-03)", "explicaciones_divergencia": "texto por defecto: 'Las fuentes miden cosas distintas: {rotulo_a} y {rotulo_b}'"}

## dim_ambito

Ámbitos territoriales que no son un ubigeo único pero sí unidades de gestión o de inferencia. Cada ámbito se define como lista de ubigeos y puede variar por fuente.

| Columna | Tipo | Regla |
|---|---|---|
| `ambito_id` | text | Clave estable (p. ej., LIMA_REGION). |
| `nombre_mostrado` | text | Nombre para el usuario. |
| `composicion` | text[] | Ubigeos (provincias o distritos) que lo forman. |
| `gestion` | text | Entidad que lo gestiona, si aplica. |
| `fuente_definicion` | text | Norma, ficha técnica o encuesta que lo define. |
| `codigo_en_fuentes` | jsonb | Código que usa cada fuente (p. ej., archivo propio: 159999). |

**ambitos_iniciales**

- LIMA_METROPOLITANA: provincia de Lima (1501, 43 distritos), gestionada por la Municipalidad Metropolitana de Lima; sin el Callao. Rótulo: «Lima Metropolitana (provincia de Lima)».
- LIMA_REGION (Lima Provincias): departamento 15 sin la provincia de Lima = 9 provincias (Barranca, Cajatambo, Canta, Cañete, Huaral, Huarochirí, Huaura, Oyón, Yauyos), 128 distritos, gestionada por el Gobierno Regional de Lima (sede Huacho); es el «departamento de Lima» de la Ley 31140 (DCF a) para fines estadísticos y presupuestales. Rótulo: «Lima Región (Lima Provincias)». En el archivo propio tiene el código 159999; su superficie (32 208,36 km²) coincide exactamente con departamento 15 menos provincia 1501.
- AREA_METROPOLITANA_LIMA_CALLAO: provincia de Lima + Callao (1501 + 07). Es el dominio 8 de la ENAHO («Área Metropolitana de Lima y Callao» en la ficha) y la región natural «Lima Metropolitana» de la ENDES hasta 2019. Se rotula siempre «Lima Metropolitana y Callao» (decisión del dueño, 9/10/2026, L3; anula PR-03 del 5/10).
- CALLAO: departamento y provincia 07, gestionado por el Gobierno Regional del Callao; dominio propio en la ENDES; en la ENAHO no es dominio: se publica como ámbito con aviso (L1). Rótulo: «Callao».
- Departamento 15 entero (no es un ámbito de esta tabla: es el ubigeo 15): rótulo «departamento de Lima (Lima Metropolitana + Lima Región)». Ley 31140: «departamento de Lima» tiene dos sentidos; nunca se usa sin decir cuál.

**uso**

Para gasto: todo el pliego del Gobierno Regional de Lima se atribuye a LIMA_REGION (Ley 31140), también sus obras ubicadas en la provincia 1501; el pliego regional de la Municipalidad Metropolitana de Lima a LIMA_METROPOLITANA; el Gobierno Regional del Callao al 07. Las cifras por ámbito usan las filas cuenta_en_ambito (R-GASTO-03). Para encuestas: el dominio o ámbito se toma de dim_dominio según encuesta y año (tipo dominio_diseno o ambito_publicado; ámbito en ambito_id).

## fact_sien_hb_ubigeo

SIEN-Hb (niños de 6 a 59 meses tamizados en EESS del MINSA y de los GORE) agregado por establecimiento, los tres ubigeos y grupo de edad. Lo construye puentes.py (sprint s3_puentes). Definiciones contrastadas con el diccionario oficial de la PNDA («2.Diccionarios HIS - 2025.xlsx», hoja Niños0a5) y con «Metadatos SIEN.docx».

| Columna | Tipo | Regla |
|---|---|---|
| `anio` | int | Año del ZIP (de la ruta interna; debe ser único). |
| `id_insumo` | text | Hash sha256 del insumo. |
| `cod_ipress` | char(8) | Renipress con ceros a la izquierda. |
| `ubigeo_eess` | char(6) | Ubigeo_EESS con zfill(6). Base de la proporción de anemia (D4). |
| `ubigeo_procedencia` | char(6) null | UbigeoPN con zfill(6) («procedencia del niño», según el diccionario). NULL si viene '', '0' o '000000'. |
| `ubigeo_ref_altitud` | char(6) | UbigeoREN con zfill(6). Solo es metadato del ajuste por altitud; no sirve para ubicar al niño. |
| `grupo_edad` | text | 6-11m, 12-23m, 24-35m, 36-59m o fuera_de_rango. |
| `filas` | int | Filas del SIEN (supuesto: niños, con su última atención del año). |
| `filas_dx_valido` | int | Filas con Dx en {Normal, Anemia Leve, Anemia Moderada, Anemia Severa}. Denominador de la anemia. |
| `filas_con_anemia` | int | Dx válido distinto de Normal (RM 251-2024/OMS 2024). |
| `unidad, criterio_anemia, version_tabla` | text | nino_ultima_evaluacion_anio, RM251-2024/OMS2024, 1.2.0. |

**clave**

(anio, id_insumo, cod_ipress, ubigeo_eess, ubigeo_procedencia, ubigeo_ref_altitud, grupo_edad)

**validacion**

- Bloqueantes: E-05 (ubigeo del establecimiento válido), E-10 (Dx válido y edad de 6-59 m) y E-11 (clave única, año único, Σ filas = filas Hb leídas del crudo).
- Avisos: E-06 (procedencia ubicada en 6-35 m, por carga y por departamento, en revision/sien_pn_6_35m_por_departamento.csv), E-07, E-08 (ajuste por altitud y cortes completos, sin NaN, en todo el ZIP) y E-09 (mismos archivos en Hb y en Pt).

**indicadores_piloto**

- Proporción de niños tamizados con anemia — ubigeo_eess (D4), denominador filas_dx_valido: «De los niños de 6 a 35 meses a los que se les midió la hemoglobina en 2025 en establecimientos del MINSA y del gobierno regional ubicados en {lugar}, el {x} % tenía anemia en su último control del año. Algunos viven en otros distritos. No es la anemia de todos los niños de {lugar}.»
- Cobertura de tamizaje, SOLO departamento (decisión del dueño, 7/10/2026) — cota inferior: procedencia en el departamento; cota superior: procedencia más los niños sin procedencia atendidos en EESS del departamento: «Entre {inf} y {sup} de cada 100 niños de 6 a 35 meses de {departamento} tuvieron al menos una medición de hemoglobina en 2025 en establecimientos del MINSA o del gobierno regional.» Si el intervalo cruza el 50 %: «Con los datos disponibles no podemos decir si la cobertura supera o no la mitad de los niños.» Nota de ficha: la cota superior no es estricta (no cuenta a los niños sin procedencia del departamento atendidos en establecimientos de otros departamentos).
- Cobertura de tamizaje por provincia o distrito: no se publica (ni siquiera en Huancavelica y Ayacucho, que superan el 95 % de procedencia ubicada).
- Altitud del ajuste — ubigeo_ref_altitud (metadato, no se publica como cifra): «La hemoglobina se corrigió según la altitud del distrito del establecimiento ({altitud} m), no la del lugar de donde procede el niño.»
- En la ficha, no en el texto ciudadano: «unidad = un niño con su último control del año (supuesto pendiente de confirmar con el INS)».

## dim_inversion_ubicacion

Ubicación de cada CUI del detalle de inversiones del MEF (R-GASTO-02, GA-09). Una fila por CUI; ninguno se pierde. La construye gasto.py (VERSION_TABLA 1.2.0). Aquí solo las columnas de ubicación; el resto son campos de obra del detalle (GA-10).

| Columna | Tipo | Regla |
|---|---|---|
| `cui` | char(7) | CODIGO_UNICO con ceros a la izquierda. Clave. |
| `ubigeos, n_ubicaciones, ubicacion_principal` | text[], int, bool | Ubigeos efectivos (tras alias, curación o nombre); el detalle trae una sola fila por CUI (ubicación principal). |
| `nivel_comun` | text null | distrito, provincia, departamento o multidepartamental («-MUL.DEP-» / 99xxxx); NULL si y solo si hay motivo_sin_ubicacion. |
| `ubigeo_atribucion` | char(6) null | Ubigeo del nivel_comun (000000 si multidepartamental). |
| `metodo_ubicacion` | text | ubigeo_valido, codigo_antiguo_alias (160114, 030715), curado_por_cui (inversiones_ubicacion_curada.yaml), codigo_escindido_contenedor (160109 → 160800), nombre_texto (UBIGEO nulo de un GL, nombre único), multidepartamental_mef o sin_ubicacion. |
| `confianza_ubicacion` | text | alta, media o baja según el método. |
| `motivo_sin_ubicacion` | text null | ubigeo_nulo_texto_gn_no_fiable, ubigeo_nulo_texto_gr_no_usado, ubigeo_nulo_sin_texto, ubigeo_nulo_nombre_ambiguo, ubigeo_nulo_nombre_no_resuelto o ubigeo_inexistente. |
| `ubigeo_fuente, departamento_txt, provincia_txt, distrito_txt` | text | UBIGEO y textos tal como vienen en el detalle (trazabilidad). |

**fact_gasto_territorial**

Columnas nuevas (1.2.0): metodo_ubicacion_cui (GA-09); categoria_transferencia, es_transferencia_intergub y bloque_consolidado (GA-05, R-GASTO-05 v4). La clave usa categoria_transferencia en lugar de es_transferencia.

## dim_establecimiento_salud

Establecimientos de RENIPRESS con ubigeo INEI (puentes.py, VERSION_TABLA 1.2.0). Columnas nuevas de la ronda 3 (GA-09).

| Columna | Tipo | Regla |
|---|---|---|
| `ubigeo_fuente` | char(6) | UBIGEO tal como viene en RENIPRESS. |
| `ubigeo_inei` | char(6) | Distrito vigente; para un código escindido no curado, la provincia contenedora (ubigeo_valido = False). |
| `metodo_ubigeo` | text | fuente, codigo_antiguo_alias (solo códigos que equivalen a un distrito, p. ej. 160114), curado (renipress_ubicacion_curada.yaml) o codigo_escindido_contenedor (160109 → 160800). |
| `evidencia_ubigeo` | text null | Evidencia de la curación (dirección, coordenadas, vecinos), solo si metodo_ubigeo = curado. |

## Notas de verificación

- Análisis propio de GITHUB-UBIGEO-PERU-AUMENTADO/ubigeo_distrito.csv (descargado 2026-10-05): 1 893 filas; 111 códigos idénticos INEI=RENIEC; 997 códigos presentes en ambos sistemas con distinto distrito; filas anómalas 150144 (Santa María de Huachipa, centro poblado), NA INEI para San Antonio (Moquegua), códigos antiguos 160109/160114.
- No se pudo descargar desde este entorno la lista INEI 2022 ni el XLSX de proyecciones 2018–2026 (proxy 403 a inei.gob.pe/gob.pe): el distrito 1 892 queda como hipótesis a confirmar con el anti-join de la especificación.
- Ley 27795 no menciona al INEI; la asignación de códigos sigue la Norma del Código UBIGEO del INEI (correlativo dentro de la provincia, sin reutilización).
## Insumos estandarizados del piloto (S4, 9/10/2026)

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