# Priorización de fuentes v2: embudo para la biblioteca de datos curados

Versión 2.0 · 8 de octubre de 2026 · 418 fuentes · corrige la v1 según la auditoría (temas A-01 a A-04, C-01, C-04 a C-06). Código: `prioriza_v2.py`; las cifras de este documento se calculan del JSON y se verifican al generarlo.

## 1. Qué cambió frente a la v1

| Cambio | Hallazgo |
|---|---|
| La Ola 1 exige **API, URL estable o geoservicio**; lo manual entra solo como excepción indispensable | A-03 |
| La Ola 1 exige **vigencia**: último dato ≥ 2021 (salvo líneas de base); sin año confirmado va a la Ola 2 | A-02 |
| La regla de capa mira **siempre las temáticas secundarias**; los portales pasan a "infraestructura de acceso" | A-04 |
| El gasto MEF cuenta como cruzable solo hasta el nivel de su **base geográfica** (ejecutora → municipalidad o departamento) | C-01 |
| Duplicados MEF (devengado mensual, sectores) y HIS → **rutas alternas**; inversión de bajo valor marginal a la Ola 2 | A-01 |
| Fuentes que no existen como se describían salen de la Ola 1 (Padrón Nominal, HIS, CONTIGO, PpR, sectores) | C-04 |
| **Compuerta de ingesta**: cada fuente de las Olas 0 y 1 lleva el resultado de la prueba de humo | C-06 |
| Pesos del puntaje: relevancia 30 %, cruzabilidad 30 %, descarga 25 %, vigencia 15 % | EMB-18 |

## 2. El embudo

```
 418  fuentes en el catálogo
  22  → rutas alternas (misma información por otra vía)
  19  → capa 0 · base de cruce (se construye primero)
  15  → infraestructura de acceso (portales y catálogos)
 222  1. Origen primario oficial
 128  2. Del foco social o del gasto asociado
 116  3. Con descarga pública
  69  4. Vigentes (último dato ≥ 2021)
  62  5. Cruzables (llave territorial y nivel útil)
  46  6. Descargables por API, URL estable o geoservicio
  30  7. Del foco duro (salud, educación, pobreza, nutrición, programas sociales) o su gasto
  29  Ola 1 = 30 − 7 bajadas a la Ola 2 por revisión + 6 indispensables por excepción
```

| Ola | Fuentes | Qué es |
|---|---:|---|
| 0 · Base | 19 | Tablas de referencia, denominadores y puentes |
| 1 · Núcleo | 29 | Primera ingesta: foco duro y gasto asociado |
| 2 · Expansión | 95 | Foco ampliado, descarga manual o por tableros, sin descarga pública o sin vigencia confirmada |
| 3 · Complementaria | 71 | Primarias y cruzables de otros temas |
| Referencia | 86 | Cifras procesadas, secundarias y series cerradas: para validar y contexto |
| Ruta alterna | 22 | Misma información que otra fuente preferida |
| Infraestructura de acceso | 15 | Portales por los que se descargan otras fuentes: se monitorean |
| Fuera de alcance | 81 | Otros temas sin dato primario cruzable |

**Compuerta de ingesta (Olas 0 y 1):** 38 aprobadas (17 por captura completa verificada y 21 solo por la muestra de la prueba de humo; columna `base_aprobacion`), 10 con enlace confirmado sin descargar, 0 pendientes, 0 bloqueadas. Ninguna fuente entra a la biblioteca hasta estar "aprobada".

## 3. Ola 0 · Base de cruce

| ID | Fuente | Para qué | Territorio | Años | Compuerta |
|---|---|---|---|---|---|
| `MEF-DETALLE-INVERSIONES` | [Detalle de inversiones (Banco de Inversiones – SNIP/Invierte.pe)](https://www.datosabiertos.gob.pe/dataset/detalle-de-inversiones) | Maestro de inversiones: CUI → ubigeo, función y sector. | distrito | 2001–2026 | ✅ aprobada |
| `MINEDU-ESCALE-PADRON` | [Padrón de Servicios Educativos (Instituciones y Programas Educativos) – ESCALE](https://escale.minedu.gob.pe/padron-de-iiee) | Puente institución educativa (código modular) → ubigeo y coordenadas. | punto_coordenadas | 2004–2025 | 🔗 enlace_confirmado |
| `RENIEC-POBLACION-IDENTIFICADA` | [Población identificada con DNI (RENIEC – Portal Estadístico)](https://portales.reniec.gob.pe/web/estadistica/identificada) | Población identificada con DNI por distrito, edad y sexo (contraste; no es población residente). | distrito | 2012–2026 | ✅ aprobada |
| `SUSALUD-RENIPRESS` | [Registro Nacional de Instituciones Prestadoras de Servicios de Salud](https://www.datosabiertos.gob.pe/dataset/registro-nacional-de-entidades-prestadoras-de-servicios-de-salud-renipress) | Puente establecimiento de salud → ubigeo (mensual). | establecimiento | 2026 | ✅ aprobada |
| `GITHUB-UBIGEO-PERU-AUMENTADO` | [ubigeo-peru-aumentado (jmcastagnetto)](https://github.com/jmcastagnetto/ubigeo-peru-aumentado) | Puente INEI↔RENIEC y centro poblado con coordenadas (secundaria, corte 2021; solo como herramienta validada). | centro_poblado | 2021 | ✅ aprobada |
| `INEI-PNDA-UBIGEOS` | [Ubigeos (Códigos de Ubicación Geográfica) – INEI (PNDA)](https://www.datosabiertos.gob.pe/dataset/ubigeos-c%C3%B3digos-de-ubicaci%C3%B3n-geogr%C3%A1fica-instituto-nacional-de-estad%C3%ADstica-e-inform%C3%A1tica-inei) | Lista oficial de ubigeos INEI (corte 2022; completar con 1 892 distritos). | distrito | 2022 | ✅ aprobada |
| `INEI-IDE-LIMITES` | [IDE INEI – Límites censales, centros poblados y manzanas (descargas y WMS/WFS)](https://ide.inei.gob.pe/) | Límites censales (distritos, centros poblados, manzanas) para mapas. | manzana_conglomerado | 2017–2023 | 🔗 enlace_confirmado |
| `INEI-PROYECCIONES-POBLACION-DISTRITAL` | [Perú: Población total proyectada al 30 de junio de cada año, según departamento, provincia y distrito, 2018-2026](https://www.gob.pe/institucion/inei/colecciones/71202-estimaciones-y-proyecciones-de-poblacion-nacional-departamental-provincial-y-distrital) | Población total proyectada por distrito y año 2018–2026. | distrito | 2018–2026 | ✅ aprobada |
| `INEI-PROYECCIONES-DEPARTAMENTAL-EDAD` | [Perú: Estimaciones y Proyecciones de Población Departamental por Años Calendario y Edad Simple 1995-2030 (Boletín Especial N.º 25)](https://www.inei.gob.pe/media/MenuRecursivo/publicaciones_digitales/Est/Lib1722/libro.pdf) | Población por edad simple y sexo, departamental, 1995–2030. | departamento | 1995–2030 | ✅ aprobada |
| `INEI-PROYECCIONES-DISTRITAL-2018-2022` | [Perú: Proyecciones de población total según departamento, provincia y distrito, 2018-2022 (Boletín Especial N.º 27)](https://www.gob.pe/institucion/inei/informes-publicaciones/3464927-peru-proyecciones-de-poblacion-total-segun-departamento-provincia-y-distrito-2018-2022) | Boletín 27: altas de distritos 2018–2022 para el ubigeo histórico. | distrito | 2018–2022 | ✅ aprobada |
| `MEF-MAESTRO-EJECUTORAS-DERIVADO` | [Maestro de unidades ejecutoras y pliegos con ubigeo y nivel de gobierno (derivado del dataset de gasto MEF)](https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto) | Maestro de unidades ejecutoras con ubigeo y nivel de gobierno (derivado del gasto MEF). | distrito | 2012–2026 | ✅ aprobada |
| `INEI-CPV2025` | [Censos Nacionales 2025: XIII de Población, VIII de Vivienda y IV de Comunidades Indígenas](https://censos2025.inei.gob.pe/) | Nuevo denominador censal: resultados por distrito desde jul-2026 (consulta en línea; aún sin bases). | distrito | 2025 | 🔗 enlace_confirmado |
| `MINSA-POBLACION-ESTIMADA` | [Población estimada MINSA por edades simples y grupos de edad (distrito / establecimiento de salud)](https://www.minsa.gob.pe/reunis/) | Denominador oficial del MINSA por distrito y edad (coberturas de salud). | distrito | 2026 | 🔗 enlace_confirmado |
| `INEI-DIRECTORIO-CCPP` | [Directorio Nacional de Centros Poblados (Censos 2017)](https://www.inei.gob.pe/media/MenuRecursivo/publicaciones_digitales/Est/Lib1541/index.htm) | Centros poblados con ubigeo de 10 dígitos. | centro_poblado | 2017 | 🔗 enlace_confirmado |
| `PROPIO-ESTADISTICAS-SOCIALES-2020` | Estadísticas sociales nacionales por distrito (compilación propia, 24-08-2020) | Archivo propio: semilla GEO2017 del ubigeo histórico (no redistribuible). | distrito | 2017–2020 | ✅ aprobada |
| `INEI-DIRECTORIO-MUNICIPALIDADES` | [Directorio Nacional de Gobiernos Regionales, Municipalidades Provinciales, Distritales y de Centros Poblados](https://www.gob.pe/en/institucion/inei/informes-publicaciones/6722617-national-directory-of-regional-governments-provincial-municipalities-district-and-of-populates-centers-2025) | Ley y fecha de creación de cada distrito: base del ubigeo histórico. | distrito | 2003–2025 | ✅ aprobada |
| `BCRP-IPC-LIMA` | [Índice de precios al consumidor de Lima Metropolitana (dic. 2021 = 100), serie mensual PN38705PM](https://estadisticas.bcrp.gob.pe/estadisticas/series/mensuales/resultados/PN38705PM/html) | Deflactor del gasto a soles constantes (IPC Lima Metropolitana, BCRP PN38705PM). | nacional | 2010–2026 | ✅ aprobada |
| `INEI-CPV2017` | [Censos Nacionales 2017: XII de Población, VII de Vivienda y III de Comunidades Indígenas](https://censo2017.inei.gob.pe/) | Línea de base de población y vivienda; distrito × sexo × edad simple. | manzana_conglomerado | 2017 | ✅ aprobada |
| `MEF-PPR-PROGRAMAS-PRESUPUESTALES` | [Programas Presupuestales – relación, fichas y estructura programática (PpR)](https://www.mef.gob.pe/index.php?option=com_content&view=article&id=5337&Itemid=101530&lang=es) | Estructura programática versionada por año (PP → producto → actividad), con el cambio 0001/0002 → 1001. | nacional | 2012–2026 | 🔗 enlace_confirmado |

## 4. Ola 1 · Núcleo

### Pobreza y condiciones de vida (2)

| ID | Fuente | Territorio | Base | Llaves | Años | Compuerta | Nota |
|---|---|---|---|---|---|---|---|
| `INEI-ENAHO` | [Encuesta Nacional de Hogares sobre Condiciones de Vida y Pobreza](https://proyectos.inei.gob.pe/microdatos/) | manzana_conglomerado / **departamento** | muestra | ubigeo_inei, conglomerado_vivienda | 1997–2025 | ✅ aprobada |  |
| `INEI-MAPA-POBREZA` | [Mapa de Pobreza Monetaria Provincial y Distrital](https://www.gob.pe/institucion/inei/informes-publicaciones/3204872-mapa-de-pobreza-provincial-y-distrital-2018) | distrito | residencia | ubigeo_inei | 2007–2018 | ✅ aprobada | Única pobreza oficial por distrito (2018, estimación con IC); publicar con las reglas de C-03. |

### Salud (8)

| ID | Fuente | Territorio | Base | Llaves | Años | Compuerta | Nota |
|---|---|---|---|---|---|---|---|
| `CDC-VIGILANCIA-DATOS-ABIERTOS` | [Vigilancia epidemiológica – datasets abiertos CDC-MINSA (dengue, malaria, leishmaniosis, EDA, IRA, zoonosis, Carrión)](https://www.datosabiertos.gob.pe/users/dgeminsa) | distrito | residencia | ubigeo_inei | 2000–2024 | ✅ aprobada |  |
| `MINSA-SINADEF` | [Sistema Informático Nacional de Defunciones – Información de fallecidos](https://www.minsa.gob.pe/defunciones/) | distrito | residencia | ubigeo_inei, otro | 2017–2026 | 🔗 enlace_confirmado |  |
| `SIS-AFILIADOS` | [Datos de afiliados al Seguro Integral de Salud en estado activo](https://www.datosabiertos.gob.pe/group/seguro-integral-de-salud-sis) | establecimiento | residencia | ubigeo_inei, codigo_renipress_ipress, pliego_unidad_ejecutora (sec_ejec) | 2021–2026 | ✅ aprobada |  |
| `SIS-ATENCIONES` | [Datos de atenciones realizadas a los asegurados del SIS](https://www.datosabiertos.gob.pe/group/seguro-integral-de-salud-sis) | establecimiento | establecimiento | codigo_renipress_ipress, ubigeo_inei, pliego_unidad_ejecutora (sec_ejec) | 2017–2025 | ✅ aprobada |  |
| `ESSALUD-DATOS-ABIERTOS` | [Datos abiertos EsSalud (consulta externa, emergencias, inmunizaciones, laboratorio)](https://www.datosabiertos.gob.pe/group/seguro-social-de-salud-essalud) | establecimiento | establecimiento | codigo_renipress_ipress, ubigeo_inei | 2015–2022 | ✅ aprobada |  |
| `SUSALUD-DATOS-ABIERTOS` | [Datos abiertos SUSALUD (producción asistencial, recursos, camas, atenciones del sector privado)](https://www.datosabiertos.gob.pe/group/superintendencia-nacional-de-salud-susalud) | establecimiento | establecimiento | codigo_renipress_ipress, ubigeo_inei | 2025–2026 | ✅ aprobada |  |
| `MINSA-REUNIS` | [Repositorio Único Nacional de Información en Salud](https://www.minsa.gob.pe/reunis/) | establecimiento | establecimiento | ubigeo_inei, codigo_renipress_ipress | 2015–2026 | 🔗 enlace_confirmado | Concentra indicadores por EESS (HIS, CRED, anemia) sin otra vía pública; requiere extraer de tableros. |
| `MINSA-INMUNIZACIONES` | [Coberturas de vacunación del esquema regular (REUNIS / Tablero virtual)](https://www.minsa.gob.pe/reunis/?op=2&niv=9) | establecimiento | establecimiento | ubigeo_inei, codigo_renipress_ipress | 2026 | 🔗 enlace_confirmado | Vacunación por distrito/EESS: sin dataset abierto, solo tablero REUNIS o transparencia. |

### Nutrición y primera infancia (4)

| ID | Fuente | Territorio | Base | Llaves | Años | Compuerta | Nota |
|---|---|---|---|---|---|---|---|
| `MINSA-CNV-NACIDOS-VIVOS` | [Registros de Nacidos Vivos en el Perú (2015–2025) – Certificado de Nacido Vivo](https://www.datosabiertos.gob.pe/dataset/registros-de-nacidos-vivos-en-el-per%C3%BA-2015%E2%80%932025) | establecimiento | establecimiento | ubigeo_inei, codigo_renipress_ipress | 2015–2025 | ✅ aprobada |  |
| `INS-CENAN-SIEN` | [Sistema de Información del Estado Nutricional de niños y gestantes](https://web.ins.gob.pe/es/alimentacion-y-nutricion/vigilancia-alimentaria-y-nutricional/sala-nutricional) | establecimiento | establecimiento | codigo_renipress_ipress, ubigeo_inei | 2012–2026 | ✅ aprobada |  |
| `INEI-ENDES` | [Encuesta Demográfica y de Salud Familiar](https://proyectos.inei.gob.pe/microdatos/) | manzana_conglomerado / **departamento** | muestra | ubigeo_inei, conglomerado_vivienda | 1986–2025 | ✅ aprobada |  |
| `INEI-MAPA-DCI-PROVINCIAL-2019` | [Aproximación al Mapa de Desnutrición Crónica Infantil a Nivel Provincial 2019](https://www.inei.gob.pe/media/MenuRecursivo/publicaciones_digitales/Est/Lib1848/libro.pdf) | provincia | residencia | — | 2019 | ✅ aprobada | Única desnutrición crónica oficial bajo el departamento (196 provincias, 2019, con IC). |

### Educación (4)

| ID | Fuente | Territorio | Base | Llaves | Años | Compuerta | Nota |
|---|---|---|---|---|---|---|---|
| `MINEDU-SIAGIE-DATOS-ABIERTOS` | [Matriculación y Trayectoria Estudiantil (SIAGIE) – datos abiertos](https://www.datosabiertos.gob.pe/group/ministerio-de-educaci%C3%B3n-minedu) | establecimiento | establecimiento | codigo_modular_ie | 2021–2024 | ✅ aprobada |  |
| `PRONIED-INTERVENCIONES` | [PRONIED – Intervenciones en infraestructura educativa y mantenimiento de locales escolares](https://www.gob.pe/14357-acceder-a-informacion-de-las-intervenciones-para-el-mejoramiento-de-los-colegios-publicos-a-nivel-nacional) | establecimiento | inversion_ubicacion | cui_inversion, codigo_local_escolar | 2024–2026 | ✅ aprobada |  |
| `MINEDU-CENSO-EDUCATIVO` | [Censo Educativo (ex Censo Escolar) – bases de datos por IE](https://escale.minedu.gob.pe/) | establecimiento | establecimiento | codigo_modular_ie, codigo_local_escolar, ubigeo_inei | 1998–2025 | ✅ aprobada | Única fuente de matrícula, docentes y servicios por IE; ESCALE exige navegador automatizado. |
| `MINEDU-UMC-ENLA` | [Evaluación Nacional de Logros de Aprendizaje (ENLA) / Evaluación Muestral (EM)](http://umc.minedu.gob.pe/resultadosenla2025/) | establecimiento / **departamento** | muestra | codigo_modular_ie, ubigeo_inei | 2019–2025 | 🔗 enlace_confirmado | Única medición vigente de aprendizajes (2022–2025), representativa por departamento; descarga manual. |

### Programas sociales (7)

| ID | Fuente | Territorio | Base | Llaves | Años | Compuerta | Nota |
|---|---|---|---|---|---|---|---|
| `FONCODES-PROYECTOS` | [FONCODES – Proyectos productivos (Haku Wiñay / Noa Jayatai)](http://www.foncodes.gob.pe/portal/index.php/proyectos/haku-winay-noa-jayatai) | distrito | inversion_ubicacion | ubigeo_inei, codigo_centro_poblado | 2018–2024 | ✅ aprobada |  |
| `PAIS-TAMBOS-ATENCIONES` | [Programa PAIS – Atenciones y beneficiarios en Tambos (plataformas fijas)](https://www.datosabiertos.gob.pe/dataset/atenciones-realizadas-en-los-tambos-programa-nacional-plataformas-de-acci%C3%B3n-para-la) | centro_poblado | establecimiento | ubigeo_inei, codigo_centro_poblado | 2020–2026 | ✅ aprobada |  |
| `JUNTOS-HOGARES-UBIGEO` | [Resumen de hogares afiliados y abonados por ubigeo – Programa JUNTOS](https://www.datosabiertos.gob.pe/group/programa-nacional-de-apoyo-directo-los-m%C3%A1s-pobres-juntos-juntos) | distrito | residencia | ubigeo_inei | 2023–2025 | ✅ aprobada |  |
| `PENSION65-USUARIOS` | [Pensión 65 – Información de usuarios](https://www.datosabiertos.gob.pe/dataset/informaci%C3%B3n-de-usuarios-del-programa-pensi%C3%B3n-65) | distrito | residencia | ubigeo_inei, dni (restringido) | 2023–2025 | ✅ aprobada |  |
| `CUNAMAS-USUARIOS` | [Cuna Más – Servicio de Acompañamiento a Familias y Servicio de Cuidado Diurno (usuarios)](https://www.datosabiertos.gob.pe/group/ministerio-de-desarrollo-e-inclusi%C3%B3n-social-midis) | centro_poblado | residencia | ubigeo_inei, codigo_centro_poblado | 2019–2023 | ✅ aprobada |  |
| `WASIMIKUNA-IIEE` | [Programa Nacional de Alimentación Escolar (Qali Warma / Wasi Mikuna) – IIEE atendidas](https://www.gob.pe/wasimikuna) | establecimiento | establecimiento | ubigeo_inei, codigo_modular_ie | 2021 | ✅ aprobada |  |
| `INEI-ENAPRES` | [Encuesta Nacional de Programas Presupuestales](https://proyectos.inei.gob.pe/microdatos/) | manzana_conglomerado / **departamento** | muestra | ubigeo_inei, conglomerado_vivienda | 2010–2024 | ✅ aprobada |  |

### Gasto e inversión pública (4)

| ID | Fuente | Territorio | Base | Llaves | Años | Compuerta | Nota |
|---|---|---|---|---|---|---|---|
| `MEF-DA-PRESUPUESTO-EJECUCION-GASTO` | [Presupuesto y Ejecución de Gasto (datos abiertos MEF)](https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto) | distrito | ejecutora | pliego_unidad_ejecutora (sec_ejec), clasificador_presupuestal (función/programa/genérica), ubigeo_inei, cui_inversion | 2012–2026 | ✅ aprobada |  |
| `MEF-DA-TRANSFERENCIAS` | [Transferencias de fondos y asignaciones financieras (datos abiertos MEF)](https://www.datosabiertos.gob.pe/dataset/transferencias-de-fondos-y-asignaciones-financieras) | distrito | ejecutora | pliego_unidad_ejecutora (sec_ejec), ubigeo_inei | 2004–2026 | ✅ aprobada |  |
| `MEF-SEGUIMIENTO-PI` | [Seguimiento de Proyectos de Inversión (datos abiertos MEF)](https://www.datosabiertos.gob.pe/dataset/seguimiento-de-proyectos-de-inversi%C3%B3n) | distrito | ejecutora | cui_inversion, pliego_unidad_ejecutora (sec_ejec), ubigeo_inei | 2014–2026 | ✅ aprobada |  |
| `MEF-DA-GASTO-GPNNA` | [Gasto en niñez y adolescencia (GPNNA)](https://www.datosabiertos.gob.pe/dataset/gasto-en-ni%C3%B1ez-y-adolescencia-gpnna) | distrito | ejecutora | pliego_unidad_ejecutora (sec_ejec), clasificador_presupuestal (función/programa/genérica), ubigeo_inei | 2023–2026 | ✅ aprobada |  |

## 5. Ola 2 · Expansión

| ID | Fuente | Tema | Por qué no está en la Ola 1 | Puntaje |
|---|---|---|---|---|
| `PRONABEC-DATOS-ABIERTOS` | [PRONABEC – Portal de Datos Abiertos (becarios, beneficiarios, convocatorias)](https://datosabiertos.pronabec.gob.pe/) | educacion | Educación superior: segunda prioridad. | 100 |
| `SUNEDU-LICENCIAMIENTO` | [SUNEDU – Licenciamiento Institucional (datos abiertos)](https://www.datosabiertos.gob.pe/dataset/sunedu-licenciamiento-institucional) | educacion | Educación superior: segunda prioridad. | 100 |
| `MINSA-COVID-DATOS-ABIERTOS` | [Datos abiertos COVID-19 (casos positivos, fallecidos, vacunación, centros de vacunación)](https://www.datosabiertos.gob.pe/group/datos-abiertos-de-covid-19) | salud | Serie cerrada de la pandemia. | 96 |
| `FMV-TECHO-PROPIO-DESEMBOLSOS` | [Desembolsos Techo Propio – Bonos Familiares Habitacionales](https://www.datosabiertos.gob.pe/dataset/desembolsos-techo-propio-bonos-familiares-habitacionales) | vivienda_servicios_basicos | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 96 |
| `MEF-CIERRE-INVERSIONES` | [Cierre de inversiones](https://www.datosabiertos.gob.pe/dataset/cierre-de-inversiones) | inversion_publica | Valor marginal bajo para el MVP (EMB-15). | 93 |
| `MINSA-FALLECIDOS-COVID19` | [Fallecidos por COVID-19 – MINSA](https://www.datosabiertos.gob.pe/dataset/fallecidos-por-covid-19-ministerio-de-salud-minsa) | salud | Serie cerrada de la pandemia. | 92 |
| `MININTER-SIDPOL-DENUNCIAS` | [Denuncias policiales registradas a nivel nacional (base SIDPOL)](https://www.datosabiertos.gob.pe/group/ministerio-del-interior-mininter) | seguridad_ciudadana_justicia | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 92 |
| `INEI-RENAMU` | [Registro Nacional de Municipalidades](https://proyectos.inei.gob.pe/microdatos/) | gobernanza_transparencia_corrupcion | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 92 |
| `MINCUL-BDPI` | [Base de Datos Oficial de Pueblos Indígenas u Originarios – Buscador de localidades](https://bdpi.cultura.gob.pe/) | pueblos_indigenas_cultura | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 92 |
| `MIDIS-GEOPORTAL` | [Geoportal MIDIS (incl. GeoSISFOH)](https://geoportal.midis.gob.pe/) | programas_sociales | Indicador oficial ya procesado con detalle fino que no se puede reconstruir desde microdatos. | 91 |
| `MTC-ONSV-SINIESTROS` | [Datos abiertos del Observatorio Nacional de Seguridad Vial (siniestros de tránsito)](https://www.onsv.gob.pe/datosabiertos) | transporte_infraestructura | Primaria y cruzable, pero su descarga es manual o exige automatizar tableros. | 90 |
| `MTPE-PLANILLA-ELECTRONICA-DA` | [Planilla Electrónica – datasets abiertos de empleo formal privado (puestos, empresas, remuneraciones por distrito)](https://www.datosabiertos.gob.pe/group/ministerio-de-trabajo-y-promoci%C3%B3n-del-empleo?sort_by=changed&sort_order=DESC&page=1) | empleo_ingresos | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 89 |
| `SUNAT-PADRON-RUC-PNDA` | [Padrón RUC – SUNAT (publicación mensual en PNDA)](https://www.datosabiertos.gob.pe/dataset/padr%C3%B3n-ruc-superintendencia-nacional-de-aduanas-y-de-administraci%C3%B3n-tributaria-sunat-46) | economia_empresas_produccion | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 89 |
| `MEF-OXI-BASE` | [Base de datos de Obras por Impuestos (adjudicaciones, ranking de empresas, convenios resueltos)](https://www.mef.gob.pe/es/obras-por-impuestos/estadisticas) | inversion_publica | Valor marginal bajo para el MVP: ya cubierto por Detalle y Seguimiento de inversiones (EMB-15). | 87 |
| `CENEPRED-SIGRID` | [Sistema de Información para la Gestión del Riesgo de Desastres (SIGRID)](https://sigrid.cenepred.gob.pe/sigridv3/) | riesgo_desastres_clima | Indicador oficial ya procesado con detalle fino que no se puede reconstruir desde microdatos. | 87 |
| `CONADIS-RNPCD` | [Registro Nacional de la Persona con Discapacidad](https://observatorio.conadisperu.gob.pe/) | salud | Registro voluntario con subregistro alto; usar Censo como cifra principal. | 86 |
| `DEVIDA-OPD` | [Observatorio Peruano de Drogas – reportes y estudios nacionales](https://sistemas.devida.gob.pe/siscod/descargarDocu?idArchivo=103) | salud | Reportes de estudios, no base estructurada por ubigeo. | 86 |
| `MINEDU-UMC-ECE` | [Evaluación Censal de Estudiantes (ECE) – resultados y bases de datos](http://umc.minedu.gob.pe/) | educacion | Primaria y cruzable, pero su descarga es manual o exige automatizar tableros. | 86 |
| `INEI-ENARES` | [Encuesta Nacional sobre Relaciones Sociales](https://proyectos.inei.gob.pe/microdatos/) | genero_violencia | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 86 |
| `SUNEDU-PROGRAMAS` | [SUNEDU – Programas Académicos (datos abiertos)](https://www.datosabiertos.gob.pe/dataset/sunedu-programas-acad%C3%A9micos) | educacion | Educación superior: segunda prioridad. | 85 |
| `MVCS-PNSU-PROYECTOS` | [Proyectos de agua y saneamiento del PNSU (modalidades transferencia, contrata, núcleo ejecutor y obras por impuestos)](https://www.datosabiertos.gob.pe/dataset/proyectos-de-agua-y-saneamiento-en-la-modalidad-de-transferencia-pnsu) | vivienda_servicios_basicos | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 85 |
| `OSIPTEL-COBERTURA-MOVIL-CCPP` | [Cobertura de servicio móvil por empresa operadora (por centro poblado)](https://www.datosabiertos.gob.pe/dataset/cobertura-de-servicio-m%C3%B3vil-por-empresa-operadora) | vivienda_servicios_basicos | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 85 |
| `SUNASS-ADP` | [Área de la prestación de servicios de saneamiento (ADP)](https://www.datosabiertos.gob.pe/dataset/%C3%A1rea-de-la-prestaci%C3%B3n-de-servicios-de-saneamiento-sunass) | vivienda_servicios_basicos | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 85 |
| `GRP-VIOLENCIA-EESS` | [Casos agrupados mensualmente de violencia contra la mujer y los integrantes del grupo familiar atendidos por establecimiento de salud – Región Piura](https://www.datosabiertos.gob.pe/dataset/casos-agrupados-mensualmente-de-violencia-contra-la-mujer-y-los-integrantes-del-grupo) | genero_violencia | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 85 |
| `INEI-CENEC2022` | [Censo Nacional Económico 2022](https://proyectos.inei.gob.pe/microdatos/) | economia_empresas_produccion | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 85 |
| `MINCUL-VISITAS-MUSEOS` | [Ministerio de Cultura – Visitas a museos y sitios arqueológicos (datos abiertos / Patrimonio Cultural en Cifras)](https://www.datosabiertos.gob.pe/dataset/visitas-museos) | turismo | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 85 |
| `FMV-TECHO-PROPIO-BENEFICIARIOS` | [Población y hogares beneficiados por el programa Techo Propio del Fondo Mivivienda](https://www.datosabiertos.gob.pe/dataset/poblacion-beneficiada-por-el-programa-techo-propio-del-fondo-mivivienda-fmv) | vivienda_servicios_basicos | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 83 |
| `MEF-FORMATO-12B` | [Formato 12B de inversiones (seguimiento de la ejecución)](https://www.datosabiertos.gob.pe/dataset/formato-12b-de-de-inversiones) | inversion_publica | Valor marginal bajo para el MVP (EMB-15). | 82 |
| `MINEDU-ESCALE-INDICADORES` | [Indicadores educativos – ESCALE (Estadística de la Calidad Educativa)](https://escale.minedu.gob.pe/indicadores) | educacion | Indicador oficial ya procesado con detalle fino que no se puede reconstruir desde microdatos. | 82 |
| `MINEDU-ESCALE-MAGNITUDES` | [Magnitudes de la Educación – ESCALE](https://escale.minedu.gob.pe/magnitudes) | educacion | Indicador oficial ya procesado con detalle fino que no se puede reconstruir desde microdatos. | 82 |
| `MIMP-WARMINAN-BANCO-DATOS` | [Portal Estadístico Warmi Ñan (ex AURORA) – Banco de datos CEM, Línea 100, SAU, CAI](https://portalestadistico.warminan.gob.pe/) | genero_violencia | Primaria y cruzable, pero su descarga es manual o exige automatizar tableros. | 82 |
| `MINEM-ESTADISTICA-MINERA` | [Estadística minera MINEM – Producción minera mensual/anual (Boletín Estadístico Minero y Anuario Minero)](https://www.minem.gob.pe/_estadisticaSector.php?idSector=1) | mineria_energia_hidrocarburos | Primaria y cruzable, pero su descarga es manual o exige automatizar tableros. | 82 |
| `MEF-PI-INCENTIVOS-MUNICIPALES` | [Programa de Incentivos a la Mejora de la Gestión Municipal – Consulta histórica](https://www.mef.gob.pe/es/incentivos-para-gobiernos-locales-y-regionales/programa-de-incentivos-a-la-mejora-de-la-gestion-municipal) | presupuesto_finanzas_publicas | Primaria y cruzable, pero su descarga es manual o exige automatizar tableros. | 80 |
| `INGEMMET-PASIVOS-AMBIENTALES` | [Inventario de Pasivos Ambientales Mineros (capa GEOCATMIN)](https://geocatmin.ingemmet.gob.pe/geocatmin/) | ambiente_recursos_naturales | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 80 |
| `MPFN-OBSERVATORIO-CRIMINALIDAD` | [Observatorio de Criminalidad del Ministerio Público](https://www.mpfn.gob.pe/observatorio/) | seguridad_ciudadana_justicia | Indicador oficial ya procesado con detalle fino que no se puede reconstruir desde microdatos. | 80 |
| `INEI-EPE-LIMA` | [Encuesta Permanente de Empleo – Lima Metropolitana y Callao](https://proyectos.inei.gob.pe/microdatos/) | empleo_ingresos | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 79 |
| `INEI-EPEN` | [Encuesta Permanente de Empleo Nacional](https://proyectos.inei.gob.pe/microdatos/) | empleo_ingresos | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 79 |
| `FMV-COLOCACIONES-MIVIVIENDA` | [Colocaciones de los Créditos Mivivienda](https://www.datosabiertos.gob.pe/dataset/colocaciones-de-los-cr%C3%A9ditos-mivivienda) | vivienda_servicios_basicos | Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas). | 79 |
| `CDC-SALA-MORTALIDAD-FETAL-NEONATAL` | [Sala situacional de mortalidad fetal y neonatal – Vigilancia epidemiológica perinatal (CDC-MINSA)](https://www.dge.gob.pe/portalnuevo/?p=14633) | salud | Primaria y relevante, pero sin llave o nivel territorial útil para cruzar. | 78 |
| `MVCS-DATASS` | [Diagnóstico sobre Abastecimiento de Agua y Saneamiento en el Ámbito Rural](https://rural.vivienda.gob.pe/login.aspx) | vivienda_servicios_basicos | Primaria y relevante, pero hoy sin descarga pública (sitio caído, login, sin datasets o solo por transparencia). | 78 |
| `SUNASS-CONEXIONES-ACTIVAS` | [Número de conexiones activas de agua potable – SUNASS](https://www.datosabiertos.gob.pe/dataset/n%C3%BAmero-de-conexiones-activas-de-agua-potable-sunass) | vivienda_servicios_basicos | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 77 |
| `SUNASS-INTERRUPCIONES` | [Registro de interrupciones del servicio de agua y alcantarillado imprevistas y programadas](https://www.datosabiertos.gob.pe/dataset/registro-de-interrupciones-del-servicio-de-agua-y-alcantarillado-imprevistas-y-programadas) | vivienda_servicios_basicos | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 77 |
| `RENIEC-REGISTROS-CIVILES-ELECTORAL` | [Estadísticas de registros civiles y población electoral (RENIEC – datos abiertos)](https://identidad.reniec.gob.pe/estadisticas) | identidad_migracion | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 77 |
| `MEF-PMI-CARTERA` | [Consulta de la cartera de inversiones del Programa Multianual de Inversiones (PMI)](https://ofi5.mef.gob.pe/invierte/pmi/consultapmi) | inversion_publica | Primaria y cruzable, pero su descarga es manual o exige automatizar tableros. | 76 |
| `MEF-DA-GASTO-COVID19` | [Presupuesto y Ejecución de Gasto – COVID-19](https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto-covid-19) | salud | Serie cerrada de la pandemia. | 76 |
| `CGR-INFOBRAS` | [Sistema de Información de Obras Públicas](https://www.gob.pe/10795-conocer-el-estado-de-las-obras-publicas-en-todo-el-peru-infobras) | inversion_publica | Primaria y relevante, pero hoy sin descarga pública (sitio caído, login, sin datasets o solo por transparencia). | 75 |
| `DIRESA-CALLAO-OPENDATA` | [Portal de datos abiertos DIRESA Callao (OITE) – Padrón Nominal y otros](http://oiteopendata.diresacallao.gob.pe/) | salud | Cobertura solo Callao. | 75 |
| `SUSALUD-PNDA-COBERTURA-PRIVADA` | [Registro de datos de atenciones de la cobertura prestacional de salud del sector privado](https://www.datosabiertos.gob.pe/node/23176/revisions/55400/view) | salud | Solo sector privado. | 75 |
| `OTASS-EPS-RAT` | [Empresas Prestadoras de Servicios de Saneamiento bajo RAT/No RAT](https://catalogo.geoidep.gob.pe/metadatos/srv/api/records/167084bf-3dd3-41cf-9f1b-7385399bf355?language=spa) | vivienda_servicios_basicos | Indicador oficial ya procesado con detalle fino que no se puede reconstruir desde microdatos. | 75 |
| `INEI-DATACRIM` | [Sistema Integrado de Estadísticas de la Criminalidad y Seguridad Ciudadana](https://datacrim.inei.gob.pe/) | seguridad_ciudadana_justicia | Primaria y cruzable, pero su descarga es manual o exige automatizar tableros. | 75 |
| `MINEDU-EVALUACION-DIAGNOSTICA` | Evaluación Diagnóstica de Aprendizajes (Estrategia Nacional de Refuerzo Escolar) | educacion | Primaria y relevante, pero hoy sin descarga pública (sitio caído, login, sin datasets o solo por transparencia). | 74 |
| `MINEDU-SISEVE` | [SíseVe – Sistema Especializado en Reporte de Casos sobre Violencia Escolar](https://siseve.minedu.gob.pe/web/) | educacion | Primaria y cruzable, pero su descarga es manual o exige automatizar tableros. | 74 |
| `INEI-ENAHO-PANEL` | [Encuesta Nacional de Hogares – Panel](https://proyectos.inei.gob.pe/microdatos/) | pobreza_condiciones_vida | Primaria y relevante, pero sin llave o nivel territorial útil para cruzar. | 73 |
| `MINEDU-ENDO` | [Encuesta Nacional a Docentes de Instituciones Educativas Públicas](https://escale.minedu.gob.pe/uee/-/document_library_display/GMv7/view/) | educacion | Primaria y cruzable, pero su descarga es manual o exige automatizar tableros. | 73 |
| `INEI-ENEDU` | [Encuesta Nacional a Instituciones Educativas](https://proyectos.inei.gob.pe/microdatos/) | educacion | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 72 |
| `CGBVP-EMERGENCIAS-24H` | [Emergencias atendidas en las últimas 24 horas – Cuerpo General de Bomberos Voluntarios del Perú](https://sgonorte.bomberosperu.gob.pe/24horas/) | riesgo_desastres_clima | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 72 |
| `CONCYTEC-RENACYT` | [Registro Nacional Científico, Tecnológico y de Innovación Tecnológica (RENACYT)](https://www.datosabiertos.gob.pe/dataset/registro-nacional-de-investigadores-renacyt) | ciencia_tecnologia_digital | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 72 |
| `OSIPTEL-CHECATUSENAL` | [Checa tu señal – Mapa de cobertura móvil](https://checatusenal.osiptel.gob.pe/) | vivienda_servicios_basicos | Indicador oficial ya procesado con detalle fino que no se puede reconstruir desde microdatos. | 71 |
| `INDECI-SINPAD` | [Sistema de Información Nacional para la Respuesta y Rehabilitación (SINPAD) – Registro de emergencias](https://sinpad.indeci.gob.pe/) | riesgo_desastres_clima | Primaria y relevante, pero hoy sin descarga pública (sitio caído, login, sin datasets o solo por transparencia). | 70 |
| `MTPE-EDO` | [Encuesta de Demanda Ocupacional](https://www.gob.pe/institucion/mtpe/informes-publicaciones/21764-resultados-de-la-encuesta-de-demanda-ocupacional) | empleo_ingresos | Primaria y cruzable, pero su descarga es manual o exige automatizar tableros. | 69 |
| `OSIPTEL-ERESTEL` | [Encuesta Residencial de Servicios de Telecomunicaciones](https://repositorio.osiptel.gob.pe/handle/20.500.12630/936) | vivienda_servicios_basicos | Primaria y cruzable, pero su descarga es manual o exige automatizar tableros. | 69 |
| `DIGEMID-OBSERVATORIO-PRECIOS` | [Observatorio Peruano de Productos Farmacéuticos – precios de medicamentos](https://www.digemid.minsa.gob.pe/webDigemid/acceso-y-uso/) | salud | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 68 |
| `MVCS-PNSR-PROYECTOS` | [Proyectos de inversión del ámbito rural ejecutados por gobiernos subnacionales financiados por transferencia de partidas – PNSR](https://www.datosabiertos.gob.pe/dataset/proyectos-de-inversi%C3%B3n-del-%C3%A1mbito-rural-ejecutados-por-los-gobiernos-sub-nacionales-y) | vivienda_servicios_basicos | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 68 |
| `SENAMHI-INFOAIRE` | [Vigilancia de la calidad del aire – SENAMHI / MINAM (INFOAIRE)](https://www.senamhi.gob.pe/?p=calidad-del-aire) | ambiente_recursos_naturales | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 68 |
| `MINCETUR-SIET-DATATUR` | [Sistema de Información Estadística de Turismo (datosturismo / DATATUR MINCETUR)](https://datosturismo.mincetur.gob.pe/appdatosTurismo/index.html) | turismo | Primaria y cruzable, pero su descarga es manual o exige automatizar tableros. | 66 |
| `SERVIR-DATOS-ABIERTOS` | [SERVIR – Datos abiertos del servicio civil (servidores civiles e ingresos)](https://www.servir.gob.pe/prensa-y-publicaciones/datos-abiertos/) | empleo_ingresos | Primaria y cruzable, pero su descarga es manual o exige automatizar tableros. | 65 |
| `INEI-ENPOVE` | [Encuesta dirigida a la Población Venezolana que reside en el país](https://proyectos.inei.gob.pe/microdatos/) | identidad_migracion | Primaria y relevante, pero sin llave o nivel territorial útil para cruzar. | 65 |
| `SUNAFIL-DATOS-ABIERTOS` | [SUNAFIL – Datos abiertos del sistema inspectivo (órdenes de inspección, resoluciones, multas)](https://www.datosabiertos.gob.pe/group/superintendencia-nacional-de-fiscalizaci%C3%B3n-laboral-sunafil) | empleo_ingresos | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 64 |
| `MIDIS-SISFOH-PGH` | [Padrón General de Hogares – Clasificación Socioeconómica (SISFOH)](https://www.gob.pe/es/43472-ministerio-de-desarrollo-e-inclusion-social-sisfoh) | pobreza_condiciones_vida | Primaria y relevante, pero hoy sin descarga pública (sitio caído, login, sin datasets o solo por transparencia). | 62 |
| `MIDIS-RUBPVL` | [Registro Único de Beneficiarios del Programa del Vaso de Leche (RUBPVL)](http://www.midis.gob.pe/index.php/rubpvl-2-0/) | programas_sociales | Primaria y relevante, pero hoy sin descarga pública (sitio caído, login, sin datasets o solo por transparencia). | 62 |
| `MML-PNDA-LICENCIAS-EDIFICACION` | [Resoluciones de Licencias de Edificación – Municipalidad Metropolitana de Lima](https://www.datosabiertos.gob.pe/dataset/resoluciones-de-licencias-de-edificaci%C3%B3n-municipalidad-metropolitana-de-lima) | vivienda_servicios_basicos | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 62 |
| `MIDAGRI-AGRORURAL` | [AGRO RURAL – Intervenciones y beneficiarios (kits de heladas, cosecha de agua, cobertizos)](https://www.gob.pe/agrorural) | agricultura_desarrollo_rural | Primaria y relevante, pero hoy sin descarga pública (sitio caído, login, sin datasets o solo por transparencia). | 62 |
| `PNDA-VIOLENCIA-CONTRA-LA-MUJER` | [Violencia contra la mujer (enero 2018 – agosto …)](https://www.datosabiertos.gob.pe/dataset/violencia-contra-la-mujer) | genero_violencia | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 62 |
| `MDSMP-PNDA-DEPORTE` | [Infraestructura, actividades y eventos deportivos – Municipalidad Distrital de San Martín de Porres](https://www.datosabiertos.gob.pe/) | pueblos_indigenas_cultura | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 62 |
| `INEI-EEA` | [Encuesta Económica Anual](https://proyectos.inei.gob.pe/microdatos/) | economia_empresas_produccion | Primaria y relevante, pero sin llave o nivel territorial útil para cruzar. | 62 |
| `MEF-INVERSIONES-BRECHAS` | [Indicadores de brechas (vinculación inversión–brecha del Banco de Inversiones)](https://www.datosabiertos.gob.pe/dataset/indicadores-de-brechas) | inversion_publica | Primaria y relevante, pero sin llave o nivel territorial útil para cruzar. | 60 |
| `ANA-SNIRH` | [Sistema Nacional de Información de Recursos Hídricos (SNIRH)](https://snirh.ana.gob.pe/SNIRHPortal/) | ambiente_recursos_naturales | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 60 |
| `OSINERGMIN-FACILITO` | [FACILITO – Precios de combustibles y GLP por establecimiento](https://www.facilito.gob.pe/facilito/pages/facilito/menuPrecios.jsp) | mineria_energia_hidrocarburos | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 60 |
| `MIGRACIONES-DATOS-ABIERTOS` | [Datos abiertos de la Superintendencia Nacional de Migraciones (carnés de extranjería, calidades migratorias, pasaportes, nacionalización)](https://www.datosabiertos.gob.pe/group/superintendencia-nacional-de-migraciones-migraciones) | identidad_migracion | Primaria y relevante, pero sin llave o nivel territorial útil para cruzar. | 59 |
| `SUNASS-CONEXIONES-TOTALES` | [Conexiones totales de agua potable – SUNASS](https://www.datosabiertos.gob.pe/dataset/conexiones-totales-de-agua-potable-sunass) | vivienda_servicios_basicos | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 58 |
| `CSJPIURA-MEDIDAS-PROTECCION` | [Medidas de protección por procesos de violencia contra las mujeres e integrantes del grupo familiar – Expediente Judicial Electrónico, Corte Superior de Justicia de Piura](https://www.datosabiertos.gob.pe/dataset/medidas-de-proteccion-por-procesos-de-violencia-contra-las-mujeres-e-integrantes-del-grupo) | genero_violencia | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 58 |
| `PROINVERSION-CARTERA-APP` | [Cartera de proyectos de Asociaciones Público-Privadas y Proyectos en Activos (ProInversión)](https://www.gob.pe/proinversion) | inversion_publica | Primaria y relevante, pero sin llave o nivel territorial útil para cruzar. | 57 |
| `INSM-EESM` | [Estudios Epidemiológicos de Salud Mental (INSM Honorio Delgado – Hideyo Noguchi)](https://www.insm.gob.pe/investigacion/estudios.html) | salud | Primaria y relevante, pero hoy sin descarga pública (sitio caído, login, sin datasets o solo por transparencia). | 56 |
| `MEF-AIRHSP` | [Aplicativo Informático para el Registro Centralizado de Planillas y de Datos de los Recursos Humanos del Sector Público](https://www.gob.pe/71708-ministerio-de-economia-y-finanzas-airhsp-aplicativo-informatico-para-el-registro-centralizado-de-planillas-y-de-datos-de-los-recursos-humanos-del-sector-publico) | presupuesto_finanzas_publicas | Primaria y relevante, pero hoy sin descarga pública (sitio caído, login, sin datasets o solo por transparencia). | 55 |
| `SERVIR-DATOS-SERVICIO-CIVIL` | [SERVIR – Estadísticas del servicio civil y Registro Nacional de Sanciones contra Servidores Civiles](https://www.gob.pe/servir) | gobernanza_transparencia_corrupcion | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 54 |
| `SINEACE-ACREDITACION` | [SINEACE – Instituciones y programas acreditados / certificación de competencias](https://www.sineace.gob.pe/normas-sobre-acreditacion/) | educacion | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 51 |
| `MINSA-INFORHUS` | [INFORHUS – Registro Nacional del Personal de la Salud](https://www.gob.pe/institucion/minsa/informes-publicaciones/393874-compendio-estadistico-informacion-de-recursos-humanos-del-sector-salud-peru-2013-2018) | salud | Primaria y relevante, pero hoy sin descarga pública (sitio caído, login, sin datasets o solo por transparencia). | 48 |
| `MININTER-DESAPARECIDOS` | [Denuncias por desaparición de personas](https://www.datosabiertos.gob.pe/group/ministerio-del-interior-mininter) | seguridad_ciudadana_justicia | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 48 |
| `MININTER-TRATA-PERSONAS` | [Información sobre trata de personas a nivel nacional](https://www.datosabiertos.gob.pe/group/ministerio-del-interior-mininter) | seguridad_ciudadana_justicia | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 48 |
| `MININTER-VIOLENCIA-MUJER-PNP` | [Violencia contra la mujer y los integrantes del grupo familiar registrada por la PNP](https://www.datosabiertos.gob.pe/group/ministerio-del-interior-mininter) | seguridad_ciudadana_justicia | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 48 |
| `COFOPRI-TITULACION` | [Estadísticas de formalización y titulación de predios urbanos y rurales](https://www.gob.pe/organismo-de-formalizacion-de-la-propiedad-informal) | vivienda_servicios_basicos | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 38 |
| `MTC-PRONATEL-PROYECTOS` | [Proyectos regionales de banda ancha y localidades beneficiarias (PRONATEL)](https://www.gob.pe/pronatel) | vivienda_servicios_basicos | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 38 |
| `SUNARP-ESTADISTICAS` | [Estadísticas registrales de SUNARP (inscripciones de predios)](https://www.gob.pe/institucion/sunarp/colecciones/2048-estadisticas-sunarp) | vivienda_servicios_basicos | Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1. | 38 |
| `SUNEDU-GRADOS-TITULOS` | [Registro Nacional de Grados y Títulos – SUNEDU](https://www.sunedu.gob.pe/inscripcion-de-grados-y-titulos/) | educacion | Primaria y relevante, pero hoy sin descarga pública (sitio caído, login, sin datasets o solo por transparencia). | 34 |
| `CONTIGO-USUARIOS` | [Programa CONTIGO – Pensión no contributiva a personas con discapacidad severa en pobreza](https://www.gob.pe/contigo) | programas_sociales | Primaria y relevante, pero hoy sin descarga pública (sitio caído, login, sin datasets o solo por transparencia). | 32 |

## 6. Referencia, rutas alternas e infraestructura de acceso

**Rutas alternas** — no se ingieren:

| ID | Fuente | Usar en su lugar |
|---|---|---|
| `SIS-ATENCIONES-PNDA` | [Datos de Atenciones realizadas a los asegurados – SIS](https://www.datosabiertos.gob.pe/dataset/datos-de-atenciones-realizadas-los-asegurados-sis) | `SIS-ATENCIONES` |
| `RENIEC-POBLACION-IDENTIFICADA-DNI` | [RENIEC – Población identificada con DNI](https://www.datosabiertos.gob.pe/dataset/reniec-poblaci%C3%B3n-identificada-con-dni-registro-nacional-de-identificaci%C3%B3n-y-estado-civil) | `RENIEC-POBLACION-IDENTIFICADA` |
| `MEF-DA-GASTO-DEVENGADO-MENSUAL` | [Presupuesto y Ejecución de Gasto – Devengado Mensual](https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto-%E2%80%93-devengado-mensual) | `MEF-DA-PRESUPUESTO-EJECUCION-GASTO` |
| `ESSALUD-EMERGENCIAS-PNDA` | [Atenciones de emergencias en EsSalud](https://www.datosabiertos.gob.pe/dataset/atenciones-de-emergencias-en-essalud) | `ESSALUD-DATOS-ABIERTOS` |
| `SIS-AFILIADOS-PNDA` | [Afiliados al Seguro Integral de Salud (PNDA)](https://www.datosabiertos.gob.pe/node/7635/download) | `SIS-AFILIADOS` |
| `MEF-DA-GASTO-DEVENGADO-SECTORES` | [Presupuesto y Ejecución de Gasto – Devengado por Sectores](https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto-%E2%80%93-devengado-sectores) | `MEF-DA-PRESUPUESTO-EJECUCION-GASTO` |
| `CENEPRED-SIGRID-IIEE` | [Capa 'Instituciones Educativas' (Padrón MINEDU) en el ArcGIS REST de SIGRID – CENEPRED](https://sigrid.cenepred.gob.pe/arcgis/rest/services/Elementos_Expuestos/MapServer/2030000) | `MINEDU-ESCALE-PADRON` |
| `MINSA-CNV` | [Sistema de Registro del Certificado de Nacido Vivo en Línea](https://www.minsa.gob.pe/cnv/) | `MINSA-CNV-NACIDOS-VIVOS` |
| `MEF-CONSULTA-INVERSIONES` | [Consulta de inversiones del Banco de Inversiones (consulta pública por CUI)](https://ofi5.mef.gob.pe/invierte/consultapublica/consultainversiones) | `MEF-DETALLE-INVERSIONES` |
| `MINEDU-SIGMED-DESCARGAS` | [SIGMED – Descarga de información espacial del MINEDU y Mapa Educativo](https://sigmed.minedu.gob.pe/mapaeducativo/) | `MINEDU-ESCALE-PADRON` |
| `CEPLAN-INFO-DEPARTAMENTAL-BRECHAS` | [CEPLAN – Información para el planeamiento y brechas de servicios a nivel departamental, provincial y distrital](https://www.ceplan.gob.pe/informacion-de-brechas-territoriales/) | `CEPLAN-BRECHAS-TERRITORIALES` |
| `MEF-CONSULTA-AMIGABLE-GASTO-DIARIA` | [Consulta Amigable – Seguimiento de la Ejecución Presupuestal (Gasto), actualización diaria](https://www.mef.gob.pe/es/seguimiento-de-la-ejecucion-presupuestal-consulta-amigable) | `MEF-DA-PRESUPUESTO-EJECUCION-GASTO` |
| `MEF-CONSULTA-AMIGABLE-GASTO-MENSUAL` | [Consulta Amigable – Gasto Presupuestal, versión mensual](https://www.mef.gob.pe/es/seguimiento-de-la-ejecucion-presupuestal-consulta-amigable) | `MEF-DA-PRESUPUESTO-EJECUCION-GASTO` |
| `MEF-CONSULTA-TRANSFERENCIAS` | [Consulta de Transferencias a los Gobiernos Nacional, Regional y Local](https://www.mef.gob.pe/es/transferencias-a-gobierno-nacional-regional-y-locales/que-es-y-como-muestra-la-consulta) | `MEF-DA-TRANSFERENCIAS` |
| `MEF-SSI` | [Sistema de Seguimiento de Inversiones](https://ofi5.mef.gob.pe/ssi/) | `MEF-SEGUIMIENTO-PI` |
| `SUNASS-AREA-PRESTACION` | [Área de la prestación de servicios de saneamiento – SUNASS](https://www.datosabiertos.gob.pe/dataset/%C3%A1rea-de-la-prestaci%C3%B3n-de-servicios-de-saneamiento-sunass) | `SUNASS-ADP` |
| `INEI-CPV2017-MANZANA` | [Sistema de Consulta de Base de Datos a nivel de Manzana – REDATAM (Censos 2017)](https://censos2017.inei.gob.pe/pubinei/index.asp) | `INEI-CPV2017` |
| `MINSA-HIS` | [Sistema de Información HIS-MINSA (registro de atenciones de consulta externa)](https://www.minsa.gob.pe/reunis/?op=3&niv=6&tbl=2) | `MINSA-REUNIS` |
| `INEI-UBIGEO-CODIGOS` | [Sistema de Consulta de Códigos y Clasificaciones (UBIGEO, centros poblados, CIIU, ocupaciones)](https://webapp.inei.gob.pe:8443/sisconcode/publico.htm) | `INEI-PNDA-UBIGEOS` |
| `INEI-IPC` | [Índice de Precios al Consumidor (Lima Metropolitana y Nacional)](https://webapp.inei.gob.pe:8443/sirtod-series/) | `BCRP-IPC-LIMA` |
| `MEF-CONSULTA-AMIGABLE-SEGUIMIENTO-PI` | [Consulta Amigable – Seguimiento de la Ejecución de Proyectos de Inversión](https://www.mef.gob.pe/es/ejecucion-de-proyectos-de-inversion) | `MEF-SEGUIMIENTO-PI` |
| `PNDA-UBIGEO-EQUIVALENCIAS` | [Códigos equivalentes de UBIGEO del Perú](https://www.datosabiertos.gob.pe/dataset/codigos-equivalentes-de-ubigeo-del-peru) | `GITHUB-UBIGEO-PERU-AUMENTADO` |

**Infraestructura de acceso** — se monitorean sus fechas de actualización:

| ID | Fuente |
|---|---|
| `MEF-DATOS-ABIERTOS-PORTAL` | [Portal de Datos Abiertos del MEF](https://datosabiertos.mef.gob.pe/) |
| `INEI-MICRODATOS` | [Portal de Microdatos del INEI (Consulta por Encuestas)](https://proyectos.inei.gob.pe/microdatos/) |
| `SGTD-PNDA` | [Plataforma Nacional de Datos Abiertos](https://www.datosabiertos.gob.pe/) |
| `INEI-DATOS-ABIERTOS` | [Conjuntos de datos del INEI en la Plataforma Nacional de Datos Abiertos](https://www.datosabiertos.gob.pe/) |
| `MINEDU-DATOS-ABIERTOS` | [MINEDU en la Plataforma Nacional de Datos Abiertos (catálogo)](https://www.datosabiertos.gob.pe/group/ministerio-de-educaci%C3%B3n-minedu) |
| `PRODUCE-DATOS-ABIERTOS` | [PRODUCE en la Plataforma Nacional de Datos Abiertos (directorio MIPYME, acuicultura, transmisiones satelitales, etc.)](https://www.datosabiertos.gob.pe/group/ministerio-de-la-producci%C3%B3n) |
| `PCM-GEOPERU` | [GEO PERÚ – Plataforma Nacional de Datos Georreferenciados](https://visor.geoperu.gob.pe/) |
| `PCM-PORTAL-TRANSPARENCIA-ESTANDAR` | [Portal de Transparencia Estándar (PTE)](https://www.transparencia.gob.pe/) |
| `CONCYTEC-ALICIA` | [ALICIA – Acceso Libre a Información Científica para la Innovación (Repositorio Nacional Digital)](https://alicia.concytec.gob.pe/vufind/) |
| `IGN-GEOIDEP` | [Geoportal de la Infraestructura de Datos Espaciales del Perú (GEOIDEP) – Catálogo Nacional de Servicios Web](https://www.geoidep.gob.pe/) |
| `MINCETUR-DATOS-ABIERTOS` | [MINCETUR en la Plataforma Nacional de Datos Abiertos](https://www.datosabiertos.gob.pe/group/ministerio-de-comercio-exterior-y-turismo) |
| `MUNI-MIRAFLORES-DATOS-ABIERTOS` | [Portal de Datos Abiertos de la Municipalidad de Miraflores](https://www.miraflores.gob.pe/datos-abiertos/) |
| `PCM-MAPAINVERSIONES-TERRITORIO` | [MapaInversiones desde el Territorio](https://mapainversionesterritorio.descentralizacion.gob.pe/) |
| `INEI-ANDA` | [Archivo Nacional de Datos – Sistema de Documentación Virtual (ANDA/NADA)](https://webinei.inei.gob.pe/anda_inei/index.php/catalog/) |
| `PCM-GOBPE` | [Plataforma Digital Única del Estado Peruano (gob.pe) – Informes y publicaciones](https://www.gob.pe/) |

**Referencia** (86), **Ola 3** (71) y **fuera de alcance** (81): filtrar por la columna `ola` en `catalogo_fuentes.csv`.

## 7. Vacíos sin fuente pública

Se buscaron y no existen como datos abiertos; quedan como solicitudes de acceso a la información o como tablas a construir:

- **Vacío 1.** (b) Proyecciones INEI por sexo y edad a nivel provincial o distrital: no existen. La ficha 2018-2026 dice expresamente que a nivel provincial y distrital solo se proyecta población total; por edad y sexo solo hay departamento (Boletín 25). (d) Censo 2025: no hay aún bases/REDATAM ni tabla descargable distrito×edad simple; solo plataforma web y PDF de presentación.
- **Vacío 2.** No hay dataset oficial legible por máquina (PNDA, INEI, PCM) con distritos creados después de 2017, su ley y su distrito de origen. Se buscó en PNDA, RENLIM (solo límites), INEI ubigeos (versión 2022 sin fecha de creación). Fuentes oficiales disponibles son PDF/Excel: Directorio Nacional de Municipalidades (ley y fecha de creación por distrito) y Anexo 3 de Lib1860; el distrito de origen hay que leerlo en cada ley (El Peruano). No se identificó cuál es el distrito 1 892 (posterior a la tabla 2022 de 1 891).
- **Vacío 3.** El MEF no publica una relación descargable de unidades ejecutoras con ubigeo y nivel de gobierno (ni en datosabiertos.mef.gob.pe ni en Consulta Amigable como archivo). Se deriva del CSV de gasto (registro MEF-MAESTRO-EJECUTORAS-DERIVADO).
- **Vacío 4.** No se halló un crosswalk oficial completo y tabular PP 0001/PP 0002 → PPoR 1001 por producto y actividad. Solo hay la lista parcial del documento MEF de criterios 2023 y las estructuras programáticas anuales en PDF; el empalme debe hacerse por código de producto/actividad en el CSV de gasto.
- **Vacío 10.** RUBPVL (MIDIS): no se publica (aplicativo con credenciales municipales; envío semestral a INEI/MIDIS). No se halló módulo público ni dataset PNDA. Ruta pública: RENAMU (INEI) por municipalidad.
- **Vacío 12.** No hay dataset abierto de recursos humanos en salud por establecimiento (INFORHUS). Solo compendios PDF departamentales de DIGEP (2013–2020) y posible tablero REUNIS no verificado (WAF). Por IPRESS requiere solicitud de acceso a la información.
- **Vacío 13.** No existe dataset abierto (PNDA) de vacunación del esquema regular por distrito o EESS; búsquedas en PNDA solo devuelven COVID-19. Ruta: tablero REUNIS de inmunizaciones (op=2&niv=9, bloqueado al fetch) o solicitud de acceso a la información (como hizo ECData en 2025).

## 8. Qué significa "curado" en cada ola

- **Ola 0:** tablas de dimensión versionadas: ubigeo con vigencia (construida desde el Directorio de Municipalidades, por no existir una tabla oficial legible por máquina), equivalencias INEI–RENIEC validadas, población por distrito y año (total) y por edad (departamento INEI, distrito MINSA), puentes IPRESS, IE, CUI y unidad ejecutora, estructura programática por año.
- **Ola 1:** cada fuente pasa por tres capas: **cruda** (archivo original con fecha de descarga), **estandarizada** (ubigeo INEI validado empíricamente, año, nombres comunes) e **indicadores** con ficha (fórmula, numerador, denominador, base geográfica, tipo de medida, nivel válido, quiebres).
- **Datos personales:** Pensión 65 publica DNI y nombres; Cuna Más, fechas de nacimiento. Se ingieren solo agregados por ubigeo; los datos personales no se almacenan.
- **Archivos grandes:** el gasto MEF y el GPNNA pesan 7–17 GB por año: ingesta por streaming y particionada por año.
- **Reglas de publicación** (precisión de encuestas, números pequeños, falacia ecológica, atribución territorial del gasto, Mapa de Pobreza 2018, criterio de anemia): se definen en la Fase 2 (auditoría C-01, C-02, C-03, A-05).
