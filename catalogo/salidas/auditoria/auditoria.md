# Auditoría del catálogo y la priorización — Pregunta al Perú

5 de octubre de 2026 · alcance: `catalogo_fuentes` v0.3 (404 fuentes), `priorizacion.md` y `prioriza.py`.

## Resumen

**Veredicto:** el catálogo sirve como inventario general, pero **la Ola 0 y la Ola 1 todavía no están listas para ingerir**. Los problemas no están en la amplitud del catálogo sino en tres cosas que se descubren solo al mirar los archivos reales: (1) el gasto del MEF no se puede ubicar por distrito como se asumió; (2) varias fuentes de la Ola 1 no existen tal como se describen; (3) faltan las reglas y las tablas base (población por edad, ubigeo histórico, maestros presupuestales) que evitan publicar cifras engañosas.

**132 hallazgos** de 6 auditores independientes: 10 críticos, 49 altos, 52 medios y 21 bajos. Se consolidaron en **17 temas**, cada uno con su recomendación. Revisé por mi cuenta 26 hallazgos clave contra la fuente, el JSON o el código: 23 se confirmaron, 2 quedaron resueltos en parte (el SIS usa ubigeo INEI) y 1 se refutó en parte (RENIPRESS sí tiene un dataset vigente).

| Tema | Severidad | Hallazgos |
|---|---|---:|
| [C-01 · El gasto del MEF no se puede ubicar por distrito como dice el catálogo](#c-01) | Crítica | 3 |
| [C-02 · Faltan reglas para no publicar cifras engañosas](#c-02) | Crítica | 7 |
| [C-03 · El Mapa de Pobreza 2018 se trataría como cifra actual](#c-03) | Crítica | 3 |
| [C-04 · Cinco fuentes de la Ola 1 no existen como se describen](#c-04) | Crítica | 5 |
| [C-05 · La capa 0 no alcanza para cruzar](#c-05) | Crítica | 16 |
| [C-06 · Los enlaces de la Ola 0 y la Ola 1 no están listos para un cargador](#c-06) | Crítica | 8 |
| [A-01 · Duplicados de gasto en la Ola 1 que sumarían montos dos veces](#a-01) | Alta | 3 |
| [A-02 · Series cerradas o antiguas en la Ola 1](#a-02) | Alta | 4 |
| [A-03 · El código del embudo no hace lo que dice el documento](#a-03) | Alta | 7 |
| [A-04 · Fuentes del foco que quedaron fuera por un error en la regla de capa](#a-04) | Alta | 9 |
| [A-05 · Quiebres metodológicos que faltan en las limitaciones](#a-05) | Alta | 6 |
| [A-06 · Tipo de ubigeo (INEI o RENIEC) contradictorio en el SIS](#a-06) | Alta | 4 |
| [A-07 · Los registros administrativos tienen un "nivel de inferencia" que confunde](#a-07) | Alta | 8 |
| [A-08 · Vacíos de cobertura en el foco social, educación y salud](#a-08) | Alta | 11 |
| [A-09 · La Ola 1 es grande para un MVP y no parte de preguntas](#a-09) | Alta | 1 |
| [A-10 · Metadatos no tipados y sin pruebas automáticas](#a-10) | Alta | 11 |
| [A-11 · Correcciones puntuales en registros de las Olas 0 y 1](#a-11) | Alta | 26 |

## Cómo se hizo

| Auditor | Alcance | Hallazgos |
|---|---|---:|
| Exactitud (2 auditores) | Exactitud factual de los 55 registros de las Olas 0 y 1, contra fichas, diccionarios y portales | 43 |
| Inferencia | Representatividad, quiebres metodológicos y reglas de publicación | 26 |
| Embudo | Lógica de priorización: código, documento y datos | 24 |
| Cobertura | Fuentes faltantes para preguntas de desarrollo social, educación y salud | 15 |
| Integridad | Esquema, nulos, duplicados, consistencia JSON/CSV/MD y URLs | 24 |

Ningún auditor participó en la construcción del catálogo. Cada hallazgo trae evidencia, recomendación, esfuerzo y confianza. Los sitios .gob.pe que bloquean bots dejaron 16 registros solo parcialmente verificados; quedan marcados como "no verificable" en el anexo.

## Hallazgos consolidados

<a id="c-01"></a>
### C-01 · El gasto del MEF no se puede ubicar por distrito como dice el catálogo

**Severidad:** Crítica · **Hallazgos de origen:** EXA-A-01, INF-01, INF-21

**Qué pasa.** Los CSV de gasto solo traen el ubigeo de la **unidad ejecutora**; la ubicación de la meta llega a **departamento** (DEPARTAMENTO_META). No existen columnas de provincia o distrito de la meta. Un cruce "gasto por habitante vs. anemia por distrito" pondría en Lima o en la capital regional el gasto del Gobierno Nacional, de los Gobiernos Regionales, de las UGEL y de las redes de salud. Además, las transferencias se cuentan dos veces si se suman con el gasto del receptor.

**Recomendación.** Agregar el campo `base_geografica` (ejecutora / meta_departamento / inversion_cui). Regla de atribución: a distrito solo el gasto de municipalidades y las inversiones ubicadas por CUI → `MEF-DETALLE-INVERSIONES.UBIGEO`; el resto, a departamento por DEPARTAMENTO_META. Excluir transferencias al sumar gasto total. Corregir llaves y nivel en los 6 registros de gasto.

**Validación.** Confirmado en el diccionario oficial `Gastos_Diccionario.csv` del MEF.

<a id="c-02"></a>
### C-02 · Faltan reglas para no publicar cifras engañosas

**Severidad:** Crítica · **Hallazgos de origen:** INF-03, INF-04, INF-15, INF-16, INF-18, INF-20, INF-23

**Qué pasa.** La sección 8 de `priorizacion.md` pide guardar el coeficiente de variación pero no fija umbrales, ni casos mínimos, ni intervalos. No hay reglas contra la falacia ecológica, contra cruzar fuentes a niveles distintos, ni para números pequeños (1 o 2 muertes en un distrito de 800 habitantes encabezan cualquier ranking).

**Recomendación.** Encuestas: <25 casos suprimir; 25–49 o CV 15–30 % "referencial" con IC; CV >30 % suprimir o agrupar años; IC 95 % siempre con el diseño muestral. Cruces: calcular al nivel válido **más grueso** de las fuentes, rotular "asociación entre territorios" y prohibir lenguaje causal. Registros: suprimir tasas con numerador <5 o denominador <1 000; en mapas distritales, suavizar o agregar 3 años. Comparaciones entre años o territorios solo si los IC no se superponen.

**Validación.** Validado: la regla no existe en el documento.

<a id="c-03"></a>
### C-03 · El Mapa de Pobreza 2018 se trataría como cifra actual

**Severidad:** Crítica · **Hallazgos de origen:** INF-02, EMB-21, EXA-A-14

**Qué pasa.** Es la única pobreza distrital oficial, pero es de 2018: antes del salto de 2020 (20,2 % → 30,1 % a nivel nacional). Además el registro apunta a otra publicación (Lib1724 en lugar de Lib1718).

**Recomendación.** Mostrar siempre "2018", el intervalo de confianza y el grupo robusto del INEI; no hacer rankings puntuales; prohibir restarlo o combinarlo con la ENAHO de otros años. Corregir la URL a la publicación principal.

**Validación.** Validado por el auditor con la serie oficial de pobreza; URL sin revisar por mí.

<a id="c-04"></a>
### C-04 · Cinco fuentes de la Ola 1 no existen como se describen

**Severidad:** Crítica · **Hallazgos de origen:** EXA-B-01, EXA-B-02, EXA-B-04, EXA-A-02, EXA-A-03

**Qué pasa.** `MINSA-PADRON-NOMINAL`: el dataset abierto es un único CSV de un hackatón de 2017. `MINSA-HIS`: el enlace lleva a un dataset de salud mental de 2017; no hay descarga pública del HIS. `CONTIGO-USUARIOS`: el grupo en la plataforma no tiene ningún dataset. `MEF-DA-GASTO-PPR`: solo trae "Programas Estratégicos" 2009–2011. `MEF-DA-GASTO-DEVENGADO-SECTORES`: congelado en 2023 y solo 4 sectores.

**Recomendación.** Sacar las cinco de la Ola 1. Padrón Nominal y HIS: obtener agregados desde REUNIS o por transparencia. CONTIGO: solicitud de acceso. GASTO-PPR y SECTORES: a referencia; los programas presupuestales actuales se filtran por `PROGRAMA_PPTO` en el dataset de gasto completo.

**Validación.** Confirmado en las fichas de la PNDA (Padrón, CONTIGO, PPR) y en el catálogo (HIS).

<a id="c-05"></a>
### C-05 · La capa 0 no alcanza para cruzar

**Severidad:** Crítica · **Hallazgos de origen:** EMB-01, INF-14, EMB-02, INF-06, EMB-03, COB-10, EXA-A-08, EMB-04, EMB-05, INT-05, EXA-A-09, EXA-A-15, EXA-A-16, EXA-A-19, EMB-19, EXA-A-07

**Qué pasa.** Faltan: (a) población por **edad y sexo** por distrito (la proyección INEI es solo total; sin esto no hay coberturas en menores de 5 años, vacunación o Pensión 65); (b) ubigeo **histórico** (distritos creados después de 2017; ya son 1 892); (c) maestro de **unidades ejecutoras** y de **programas presupuestales** con el cambio 0001/0002 → 1001; (d) regla para elegir denominador. Además: el puente RENIPRESS apunta a un dataset viejo cuando existe uno mensual vigente; el puente de colegios depende de un sitio con anti-bot; la tabla de equivalencias INEI–RENIEC no tiene publicador confirmado; el Censo 2025 **ya publicó resultados distritales** (julio 2026, omisión 4,25 %).

**Recomendación.** Agregar a la Ola 0: población por edad y sexo (MINSA por distrito, INEI por grupos de edad), ubigeo con vigencia (RENLIM + INEI), dim_unidad_ejecutora derivada del gasto MEF y dim_programa_presupuestal versionada. Corregir RENIPRESS al dataset mensual de SUSALUD. Usar SIGMED como ruta primaria del padrón de colegios. Pasar el Censo 2025 a nivel distrito. Regla de denominador por indicador, versionada.

**Validación.** Confirmado: RENIPRESS vigente a sep-2026 y Censo 2025 con resultados distritales (presentación INEI). EMB-04 queda refutado en parte: el dataset vigente existe; lo que está mal es el enlace.

<a id="c-06"></a>
### C-06 · Los enlaces de la Ola 0 y la Ola 1 no están listos para un cargador

**Severidad:** Crítica · **Hallazgos de origen:** INT-01, INT-02, INT-09, EMB-11, INT-06, EXA-B-20, INT-13, INT-19

**Qué pasa.** 16 de 55 registros de las Olas 0 y 1 no tienen `url_datos`; algunos `url_datos` son texto con plantillas; 50 de 55 enlaces nunca se abrieron; varios usan `http` o el host `datosabiertos.gob.pe` sin `www.`, que no resuelve.

**Recomendación.** Prueba de humo obligatoria antes de ingerir: descargar un archivo real y registrar código HTTP, tamaño, columnas, presencia de ubigeo y fecha de corte. Separar `url_datos` (URL literal) de `url_patron` (plantilla). Normalizar a `https://www.`. Hasta pasar la prueba, la fuente queda "pendiente de verificación".

**Validación.** Validado en el JSON.

<a id="a-01"></a>
### A-01 · Duplicados de gasto en la Ola 1 que sumarían montos dos veces

**Severidad:** Alta · **Hallazgos de origen:** EXA-A-04, EMB-06, EMB-15

**Qué pasa.** "Devengado Mensual" es el mismo dato que "Presupuesto y Ejecución de Gasto" en formato ancho. En 2025–2026 cada año tiene un archivo -Mensual y otro -Diario. Cinco datasets de inversión ligados por CUI tienen poco valor adicional para el MVP.

**Recomendación.** Ingerir solo `MEF-DA-PRESUPUESTO-EJECUCION-GASTO` (anual hasta 2024; para 2025–2026 solo el -Mensual). Marcar los demás como ruta alterna. En inversión, dejar Detalle + Seguimiento en la Ola 1 y el resto en la Ola 2.

**Validación.** Sin validación independiente.

<a id="a-02"></a>
### A-02 · Series cerradas o antiguas en la Ola 1

**Severidad:** Alta · **Hallazgos de origen:** EMB-08, INF-09, INT-11, INT-21

**Qué pasa.** ENCO (2006), ENEDIS (2012), ENSUSALUD (2016), ENDO (2021) y la ECE censal (hasta 2019) entraron porque la vigencia no decide la ola.

**Recomendación.** Regla: último dato ≥ año actual − 5, salvo censos y líneas de base marcadas. Mover ENCO a referencia; ENEDIS, ENSUSALUD, ENDO y ENEDU a la Ola 2. Mostrar siempre el año junto a la cifra.

**Validación.** Validado en el JSON.

<a id="a-03"></a>
### A-03 · El código del embudo no hace lo que dice el documento

**Severidad:** Alta · **Hallazgos de origen:** EMB-09, INT-10, EMB-13, EMB-18, EMB-14, EMB-24, EMB-22

**Qué pasa.** El documento dice que en la Ola 1 entra "API o URL estable", pero el umbral deja pasar la descarga manual (10 fuentes). La cuenta "53 − 10 + 3 = 43" no cierra porque no descuenta 3 rutas alternas. Doce fuentes empatan en 100 puntos y el puntaje premia la facilidad de descarga más que la relevancia.

**Recomendación.** Decidir la regla de descarga y alinear código y documento; corregir la aritmética del embudo; subir el peso de la relevancia y desempatar por preguntas que habilita; agregar un test que compare las cifras del documento con el JSON.

**Validación.** Validado en `prioriza.py`.

<a id="a-04"></a>
### A-04 · Fuentes del foco que quedaron fuera por un error en la regla de capa

**Severidad:** Alta · **Hallazgos de origen:** COB-05, COB-06, COB-07, COB-08, EMB-10, EMB-16, EMB-17, EMB-20, EMB-23

**Qué pasa.** `capa()` solo mira los temas secundarios cuando el tema principal es "multitemática". Por eso quedaron en la Ola 3 o fuera de alcance: denuncias por violencia familiar (PNP), SIDPOL, SIRTOD, EstaDist, BDPI (pueblos indígenas), hechos vitales de RENIEC, y los propios portales de descarga (microdatos INEI, plataforma de datos abiertos). Todo lo geoespacial se marcó como derivado.

**Recomendación.** Corregir `capa()` para usar los temas secundarios siempre; crear la etiqueta "infraestructura de acceso" para portales y catálogos; tratar como primarias las capas geoespaciales que son registros (GeoInvierte, SIGMED); volver a correr el embudo.

**Validación.** Validado en `prioriza.py`.

<a id="a-05"></a>
### A-05 · Quiebres metodológicos que faltan en las limitaciones

**Severidad:** Alta · **Hallazgos de origen:** INF-08, INF-17, INF-19, EXA-A-13, INF-24, EXA-B-08

**Qué pasa.** Anemia: la ENDES 2024 publica con dos criterios (RM 363-2022 y RM 251-2024/OMS 2024); mezclarlos fabrica una caída. ENDES y ENAPRES 2020 cambiaron de modo de entrevista. La omisión del Censo 2017 fue 5,9 %, no 3–4 %. La ENDES 2025 ya se publicó.

**Recomendación.** Atributo obligatorio `criterio` en todo indicador de anemia y recálculo desde microdatos; campo `anios_con_quiebre` en cada encuesta; excluir 2020 de las tendencias por defecto; corregir cifras y coberturas.

**Validación.** Omisión 2017 validada por aritmética (29,38 M censados / 31,24 M estimados).

<a id="a-06"></a>
### A-06 · Tipo de ubigeo (INEI o RENIEC) contradictorio en el SIS

**Severidad:** Alta · **Hallazgos de origen:** INF-05, INT-03, EXA-B-06, INF-12

**Qué pasa.** SIS-AFILIADOS declara ubigeo INEI y su ruta alterna RENIEC. El diccionario de afiliados dice INEI; el de atenciones no lo aclara. Un error aquí asigna datos a otro distrito sin dar error. Tampoco existe el nivel "dominio" (Lima Metropolitana / Lima Provincias).

**Recomendación.** Validación empírica en la ingesta: porcentaje de códigos que existen en INEI y en RENIEC, más el nombre del distrito; rechazar la carga si no llega a 99 %. Corregir SIS-AFILIADOS (INEI, mensual, conteos agregados). Agregar "dominio" al vocabulario territorial.

**Validación.** Confirmado en el diccionario SIS de afiliados: "codificación de acuerdo al INEI".

<a id="a-07"></a>
### A-07 · Los registros administrativos tienen un "nivel de inferencia" que confunde

**Severidad:** Alta · **Hallazgos de origen:** INF-07, INT-17, INF-22, INF-25, INF-26, INF-10, INF-11, INF-13

**Qué pasa.** SIEN y el Padrón Nominal declaran inferencia "distrito", como si fueran representativos de la población. El problema de un registro es otro: quién acude, dónde se registra (establecimiento o residencia) y qué mide. Algunos niveles de encuestas son supuestos sin ficha (ENEDU, ENDO).

**Recomendación.** Para registros y presupuesto: `nivel_territorial_inferencia` vacío y tres campos nuevos: `base_geografica` (residencia / establecimiento / ejecutora / domicilio fiscal / ocurrencia), `tipo_medida` (prevalencia / cobertura / atenciones / notificación) y `cobertura_estimada`.

**Validación.** Validado en el JSON.

<a id="a-08"></a>
### A-08 · Vacíos de cobertura en el foco social, educación y salud

**Severidad:** Alta · **Hallazgos de origen:** COB-01, COB-02, COB-03, COB-04, COB-09, COB-11, COB-12, COB-13, COB-14, COB-15, EMB-07

**Qué pasa.** Vacunación por distrito solo en tableros REUNIS (quedó en la Ola 2 mientras HIS y REUNIS, la misma ruta, ocupan dos lugares en la Ola 1). Aprendizajes: falta la Evaluación Diagnóstica de MINEDU (por IE). Falta el **Mapa de Desnutrición Crónica provincial 2019** del INEI (confirmado), la vigilancia de mortalidad neonatal del CDC, el Vaso de Leche y comedores, trabajo infantil (ETI 2015) y recursos humanos en salud. El Censo Educativo sí tiene una ruta de descarga predecible.

**Recomendación.** Agregar: Mapa de DCI provincial (Ola 1 por excepción, como el de pobreza), Evaluación Diagnóstica, mortalidad neonatal CDC (referencia), RUBPVL/RENAMU-PVL (Ola 2), ETI 2015 y RRHH en salud (Ola 2). Fusionar HIS en REUNIS y llevar vacunación a la Ola 1 como módulo de REUNIS. Cambiar la ruta del Censo Educativo a la carpeta de descargas.

**Validación.** Mapa de DCI provincial 2019 confirmado (INEI, Lib1848).

<a id="a-09"></a>
### A-09 · La Ola 1 es grande para un MVP y no parte de preguntas

**Severidad:** Alta · **Hallazgos de origen:** EMB-12

**Qué pasa.** 43 fuentes, cada una con tres capas de curaduría y fichas de indicador. El embudo ordena por atributos de la fuente, no por las preguntas que el producto debe responder.

**Recomendación.** Definir 10–15 preguntas ancla y una matriz pregunta × fuente; formar una Ola 1a de 12–15 fuentes que respondan esas preguntas, y dejar el resto como Ola 1b.

**Validación.** Criterio de diseño; no requiere validación.

<a id="a-10"></a>
### A-10 · Metadatos no tipados y sin pruebas automáticas

**Severidad:** Alta · **Hallazgos de origen:** INT-07, INT-08, INT-12, INT-14, INT-15, INT-16, INT-18, INT-20, INT-22, INT-23, INT-24

**Qué pasa.** `cobertura_temporal` es texto libre en 123 registros; 163 licencias vacías y 34 variantes de escritura; en 91 registros `verificado=true` contradice notas que dicen "no verificado"; fusiones sin trazabilidad; algunos valores fuera de vocabulario. JSON, CSV y MD sí son consistentes entre sí.

**Recomendación.** Campos tipados: `anio_inicio`, `anio_fin`, `fecha_ultimo_dato`, `es_proyeccion`; licencias en códigos SPDX y `permite_redistribucion`; reemplazar `verificado` por `estado_portal` y `estado_datos` con fecha; campo `ids_fusionados`. Suite de validación (JSON Schema + pytest) que bloquee la regeneración del catálogo si falla.

**Validación.** Validado en el JSON.

<a id="a-11"></a>
### A-11 · Correcciones puntuales en registros de las Olas 0 y 1

**Severidad:** Alta · **Hallazgos de origen:** EXA-A-05, EXA-A-06, EXA-A-10, EXA-A-11, EXA-A-12, EXA-A-17, EXA-A-18, EXA-A-20, EXA-A-21, EXA-B-03, EXA-B-05, EXA-B-07, EXA-B-09, EXA-B-10, EXA-B-11, EXA-B-12, EXA-B-13, EXA-B-14, EXA-B-15, EXA-B-16, EXA-B-17, EXA-B-18, EXA-B-19, EXA-B-21, EXA-B-22, INT-04

**Qué pasa.** Ejemplos: SEGUIMIENTO-PI no trae SNIP ni ubigeo del proyecto (el CUI está en PRODUCTO_PROYECTO); INVERSIONES-BRECHAS no tiene ubigeo; el CSV de dengue es histórico 2000–2024 y sin código de establecimiento; SINADEF se descarga de un Nextcloud del MINSA, no de Google Drive; Pensión 65, FONCODES y Wasi Mikuna tienen enlaces a datasets viejos o privados; duplicados SUNASS y CEPLAN sin fusionar.

**Recomendación.** Aplicar los valores corregidos que cada hallazgo propone (ver anexo CSV) y volver a generar el catálogo.

**Validación.** Sin validación independiente, salvo lo cruzado con otros hallazgos.

## Plan de acción

**Fase 1 · Antes de ingerir (bloqueante)**
1. Corregir los registros señalados en C-04, C-05 y A-11, y sacar de la Ola 1 las fuentes que no existen como se describen.
2. Corregir `prioriza.py` (A-03, A-04, A-02): regla de capa, umbral de descarga, regla de vigencia, rutas alternas del MEF; volver a correr el embudo.
3. Completar la capa 0 (C-05): población por edad y sexo, ubigeo histórico, maestros de unidades ejecutoras y programas presupuestales, Censo 2025 distrital.
4. Prueba de humo a las Olas 0 y 1 (C-06), desde tu computadora o con navegador, que es donde los sitios .gob.pe sí responden.
5. Tipar metadatos y montar la suite de validación (A-10).

**Fase 2 · Diseño de la biblioteca**
6. Escribir las reglas de publicación (C-02, C-03, A-05, A-07) como parte de la ficha de cada indicador.
7. Regla de atribución territorial del gasto (C-01) y regla de denominador por indicador (C-05).
8. Validación empírica del tipo de ubigeo en cada carga (A-06).

**Fase 3 · Alcance**
9. Definir 10–15 preguntas ancla y la Ola 1a (A-09).
10. Cerrar los vacíos de cobertura (A-08).

## Anexo

El detalle de los 132 hallazgos (evidencia, recomendación, esfuerzo, confianza, tema consolidado y validación) está en `auditoria_hallazgos.csv`.

## Estado tras la fase 1 de corrección (5 de octubre de 2026)

| Estado | Hallazgos |
|---|---:|
| Corregido | 81 |
| Corregido en parte | 32 |
| Corregido en el catálogo; la regla de uso va en la Fase 2 | 12 |
| Pendiente de la Fase 2 (reglas de publicación) | 6 |
| Pendiente de la Fase 3 (preguntas ancla) | 1 |

El detalle por hallazgo está en `auditoria_estado.csv`; cada registro del catálogo indica en `correcciones` qué hallazgo lo modificó y cómo se validó.
