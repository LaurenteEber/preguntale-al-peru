# M1-06 y M1-05 tarea 0 — Revisión del auditor-agente

**Veredicto final (12/11/2026, segunda revisión): aprobado con observaciones.** Primera revisión: «con hallazgos abiertos» (clases, páginas del cuestionario, bloques de DIT y de violencia); el implementador hizo una ronda de corrección con las pruebas del auditor primero (11 en rojo, luego en verde) y la segunda revisión dio todos los hallazgos por resueltos. Única consulta tipo C: C-M1-06-1 (llave de CSALUD01), sin aplicar hasta que decida el dueño.

## Segunda revisión (resumen)

- `pap fichas validar`: 34 fichas y 227 bloques cumplen las 8 reglas; `test_m105_*` y `test_m106_*`: 61 pasan; `pap fichas generar` reproducible; 2 036 de 2 036 variables `categoria` o `medida` con un bloque.
- Resueltos: páginas (REC84DV y REC93DVdisciplina pp. 72–81, REC82 calendario pp. 89–90, RECHM sección 1 p. 6); nombres y descripciones (REC41, REC94, REC43, CSALUD08 con `variable_edad: QS802D`, aviso 15–49 de REC84DV); bloques (tuberculosis en `salud_adultos/enfermedades_cronicas`, edades de los módulos E a J de DIT, castigo de 15 días, población 15–49 de violencia en REC91, variables movidas); clases (sin excepciones erróneas, ninguna `categoria` con 15 o más valores sin etiqueta, llaves, diseño y geografía, QHHOME y fechas de entrevista unificados).
- Regla nueva de clases: 111 variables `medida` con etiquetas de borde revisadas en muestra de más de 20: ningún falso positivo.
- Observaciones que no bloquean: V139 debería ser `geo` según la convención de M1-05-s4; SHREGION y SREGION (región natural) quedaron `categoria` (proponer `geo`, o `diseno` si el dueño la ve como dominio); SHSEMES, SSEMES, SHVER, V017 y V019A deberían ser `diseno`; `endes_dit_castigo_15_dias` puede declarar 24–71 meses; QH25A (nacionalidad) sigue `texto`; en el índice `llave` significa «se usa para unir», no «única» (HC60 trae 993 a 995, B16 = 0 se repite); el defecto de páginas de M1-04 queda en M1-06-s7.
- Lote para el visto del dueño: las 34 fichas, los 227 bloques, `temas.yaml`, `clases_excepciones.yaml` 0.2.0 con M1-05-s4 y M1-06-s3/s7, y C-M1-06-1.

## Lista de la primera ronda (histórica)

# M1-06, tarea 6 — Revisión del auditor-agente de fichas y bloques (lista en blanco)

> **Nota de la ronda de corrección (12/11/2026):** la lista de fichas y bloques de abajo se generó en la primera ronda. El auditor ya dio «con hallazgos abiertos»; los hallazgos se corrigieron (ver `m1-06.md`, «Ronda de corrección») y los bloques cambiaron (227 siguen, pero con ids nuevos —`endes_rec91_tuberculosis`, `endes_dit_castigo_15_dias`, `endes_rec43_vitamina_a_6_meses`, `endes_rech23_fallecidos`, `endes_rech23_enfermos_huerfanos`— y sin los tres bloques de RECH0 que quedaron vacíos). El padre pega aquí el informe del auditor; `pap fichas ver <tabla>` da la lista actual de cada tabla.

**Estado: SIN REVISAR.** Esta lista la dejó el agente implementador **sin llenar**; la llena el auditor-agente (no el implementador). El implementador no se revisa a sí mismo.

## Qué se revisa y contra qué

Contra el **diccionario de cada tabla** (PDF «Diccionario - <tabla>.pdf» dentro de su ZIP, o `biblioteca/variables/cuestionarios/ENDES/2024/diccionarios.parquet`), el **cuestionario** que corresponde (hogar, individual o salud; `hogar.parquet`, `individual.parquet`, `salud.parquet` de M1-04) y el documento n.º 11 ([`m1-06_identificadores.md`](m1-06_identificadores.md)). Fuentes de lo revisado: `curados/inferencia/fichas/ENDES.yaml`, `curados/inferencia/bloques/ENDES.yaml`, `curados/inferencia/temas.yaml` y los Parquet generados (`pap fichas ver <tabla>` muestra la ficha completa).

Reglas del implementador que conviene mirar con ojo (están en `consultas_al_dueno.md`, supuestos M1-06-s1 a s9 y C-M1-06-1):

- los nombres y descripciones de los bloques salen de las etiquetas de las variables, no de leer pregunta por pregunta el cuestionario (solo 304 variables tienen su pregunta vinculada);
- la asignación tabla → sección y páginas del cuestionario es del agente;
- las clases (`categoria` / `medida`) y las 105 excepciones de `clases_excepciones.yaml` deciden qué variables entran a un bloque;
- los módulos DIT (E a J) y REC95 (vacunas) se nombraron por la letra del módulo y las etiquetas.

## Cómo llenarla

Marcar `[x]` lo que está bien. Cada hallazgo va en la tabla «Hallazgos» con: tabla o bloque, qué está mal, qué dice el diccionario o el cuestionario (con página) y qué se propone. Un hallazgo que cambiaría una cifra, una regla o una decisión es consulta tipo C (`consultas_al_dueno.md`); los demás los corrige el implementador. Al terminar, escribir el veredicto al final.

## 1. Fichas de tabla (34)

Para cada tabla: (a) nombre y descripción corresponden al diccionario; (b) `poblacion` (texto, sujeto, edad, sexo, condición) corresponde al diccionario y al cuestionario; (c) `quien_tiene_fila`, `informante` y `modo`; (d) `secciones` y páginas; (e) `avisos` completos; (f) `documentos`; (g) `tipo_tabla`.

| Tabla | Filas | Bloques | (a) nombre/desc. | (b) población | (c) fila/informante/modo | (d) secciones y páginas | (e) avisos | (f) documentos | (g) tipo | Observación |
|---|---|---|---|---|---|---|---|---|---|---|
| CSALUD01 | 34,018 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| CSALUD08 | 41,309 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| DIT | 19,245 | 7 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| PS_BECA18 | 48 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| PS_COMEDOR | 1,437 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| PS_PENSION65 | 2,745 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| PS_QALIWARMA | 18,984 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| PS_TRABAJA | 78 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| PS_VL | 9,824 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| PS_WAWAWASI | 725 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| Programas_Sociales_x_Hogar | 34,018 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| RE223132 | 34,252 | 12 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| RE516171 | 34,252 | 12 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| RE758081 | 34,252 | 10 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| REC0111 | 37,117 | 15 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| REC21 | 60,693 | 8 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| REC41 | 19,751 | 14 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| REC42 | 34,252 | 17 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| REC43 | 19,751 | 11 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| REC44 | 19,751 | 7 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| REC82 | 171,260 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| REC83 | 141,805 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| REC84DV | 34,252 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| REC91 | 37,117 | 37 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| REC93DVdisciplina | 15,462 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| REC94 | 19,751 | 8 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| REC95 | 19,751 | 16 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| RECH0 | 37,390 | 7 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| RECH1 | 135,045 | 8 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| RECH23 | 37,390 | 16 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| RECH4 | 135,045 | 5 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| RECH5 | 38,488 | 8 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| RECH6 | 20,290 | 9 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |
| RECHM | 3,002 | 0 | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | [ ] | |

## 2. Bloques (227, de las 19 tablas del lote)

Para cada bloque: (a) el nombre y la descripción corresponden a lo que dicen las etiquetas de sus variables y el diccionario; (b) ninguna variable parece de otro asunto (mirar la primera, la última y las del medio); (c) tema y subtema; (d) `papel`; (e) `ventana_referencia` y población solo si el cuestionario las confirma. Se muestran `primera … última` y el número de variables.


### DIT (7 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_dit_datos` — Orden, edad y condición para la entrevista | QI478 … QI478A (2) | salud_infantil / desarrollo_infantil_temprano | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_dit_modulo_e` — Módulo E: cuidado, comprensión y trato | QI478E1 … QI478E10 (10) | salud_infantil / desarrollo_infantil_temprano | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_dit_modulo_f` — Módulo F: juego, lenguaje y comprensión | QI478F1 … QI478F6 (10) | salud_infantil / desarrollo_infantil_temprano | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_dit_modulo_g` — Módulo G: lenguaje | QI478G1 … QI478G4 (6) | salud_infantil / desarrollo_infantil_temprano | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_dit_modulo_h` — Módulo H: lenguaje, juego, materiales y comportamiento | QI478H1 … QI478H12 (13) | salud_infantil / desarrollo_infantil_temprano | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_dit_modulo_i` — Módulo I: juego simbólico, materiales y comportamiento | QI478I1 … QI478I8 (9) | salud_infantil / desarrollo_infantil_temprano | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_dit_modulo_j` — Módulo J: juego, materiales y comportamiento | QI478J1 … QI478J8 (9) | salud_infantil / desarrollo_infantil_temprano | [ ] | [ ] | [ ] | [ ] | [ ] | |

### RE223132 (12 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_re223132_conocimiento_uso` — Conocimiento y uso de métodos anticonceptivos alguna vez | V301 … V305_16 (18) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re223132_costo_fuente` — Costo y fuente del método actual | V325A … V327 (3) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re223132_dejo_de_usar` — Dejó de usar el método e intención de uso | V359 … V367 (7) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re223132_embarazo_actual` — Embarazo actual, ciclo menstrual y si es deseado | V213 … V227 (8) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re223132_esterilizacion` — Esterilización | V319 … V322 (4) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re223132_hijos_nacidos` — Hijos nacidos vivos, vivos y fallecidos | V201 … V212 (12) | salud_materna_reproductiva / fecundidad_nacimientos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re223132_hijos_vivos_intervalos` — Hijos vivos e intervalos | V218 … V224 (7) | salud_materna_reproductiva / fecundidad_nacimientos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re223132_informacion_metodos` — Información recibida sobre métodos | V3A01 … V3A09B (34) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re223132_mensajes_consejeria` — Mensajes de planificación familiar y consejería | V384A … V395 (6) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re223132_perdidas` — Pérdidas de embarazo | V228 … V243 (15) | salud_materna_reproductiva / fecundidad_nacimientos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re223132_razones_no_uso` — Razones para no usar y fuentes conocidas | V372 … V380 (7) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re223132_uso_actual` — Método actual: cuál, inicio y duración | V310 … V307_16 (26) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |

### RE516171 (12 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_re516171_actitudes_violencia` — Actitudes ante el maltrato de la esposa | V744A … V744E (5) | violencia / violencia_contra_mujer | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re516171_actividad_sexual` — Primera relación y actividad sexual reciente | V525 … V541 (11) | familia_pareja / union_convivencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re516171_decision_anticonceptivos` — Decisión sobre anticonceptivos y razones para no tener relaciones | V631 … V634 (10) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re516171_decisiones_hogar` — Quién tiene la última palabra en el hogar | V743A … V743F (6) | familia_pareja / trabajo_mujer_pareja | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re516171_deseo_hijos` — Deseo de más hijos y tiempo de espera | V602 … V621 (6) | salud_materna_reproductiva / fecundidad_nacimientos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re516171_esposo_educacion` — Educación del esposo o compañero | V701 … V729 (4) | educacion / nivel_educativo_asistencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re516171_esposo_trabajo` — Edad y ocupación del esposo o compañero | V730 … V705 (3) | familia_pareja / trabajo_mujer_pareja | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re516171_estado_civil` — Estado civil y primera unión | V501 … V513 (13) | familia_pareja / union_convivencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re516171_fin_union` — Fin de la unión anterior y bienes | V538 … V540 (3) | familia_pareja / union_convivencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re516171_necesidad_insatisfecha` — Exposición y necesidad insatisfecha de planificación | V623 … V626 (4) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re516171_numero_ideal` — Número ideal de hijos | V613 … V629 (5) | salud_materna_reproductiva / fecundidad_nacimientos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re516171_trabajo_mujer` — Trabajo de la entrevistada | V714 … V717 (12) | familia_pareja / trabajo_mujer_pareja | [ ] | [ ] | [ ] | [ ] | [ ] | |

### RE758081 (10 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_re758081_condon` — Condón: uso y dónde conseguirlo | V761 … V833C (60) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re758081_conocimiento_vih` — Conocimiento sobre el VIH/SIDA | V750 … V825 (10) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re758081_estigma` — Actitudes y estigma hacia las personas con VIH | V775 … V848 (10) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re758081_its` — Otras infecciones de transmisión sexual | V763A … V785 (33) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re758081_normas_sexuales` — Normas sobre relaciones sexuales y poder de decisión | V849 … V851L (15) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re758081_parejas` — Parejas sexuales | V766A … V836 (22) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re758081_presencia_entrevista` — Presencia de otras personas durante la entrevista | V811 … V814 (4) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re758081_prueba_prenatal` — Prueba de VIH en el control prenatal | V839 … V843 (5) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re758081_prueba_vih` — Prueba de VIH: si se la hizo, dónde y resultados | V781 … V829 (29) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_re758081_transmision_madre_hijo` — Transmisión de madre a hijo y tratamiento | V774A … V838C (8) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |

### REC0111 (15 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rec0111_alfabetizacion_medios` — Alfabetización y exposición a medios | V155 … V159 (5) | educacion / nivel_educativo_asistencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec0111_bienes` — Bienes del hogar | V119 … V153 (8) | hogar_vivienda / bienes_riqueza | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec0111_discapacidad` — Dificultades o limitaciones permanentes | QD333_1 … QD333_6 (6) | salud_adultos / discapacidad | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec0111_edad_nacimiento` — Edad y fecha de nacimiento | V009 … Q105DD (7) | hogar_vivienda / composicion_hogar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec0111_educacion` — Educación de la entrevistada | V106 … V149 (4) | educacion / nivel_educativo_asistencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec0111_elegibilidad` — Mujeres de 12 a 49 años | MUJERES12A49 … MUJERES12A49 (1) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec0111_hogar_composicion` — Composición del hogar y jefe del hogar | V134 … V152 (11) | hogar_vivienda / composicion_hogar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec0111_identificacion` — Identificación de la vivienda y la entrevistada | V002 … V008 (4) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec0111_pareja` — Unión y esposo en el hogar | V020 … V034 (2) | familia_pareja / union_convivencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec0111_religion_etnia` — Religión y etnicidad | V130 … V131 (2) | identidad_cultura / lengua_etnia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec0111_residencia` — Dominio, residencia actual, en la infancia y viajes | V023 … V168 (9) | hogar_vivienda / composicion_hogar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec0111_resultado_entrevista` — Resultado de la entrevista individual y calendario | V015 … V019A (5) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec0111_riqueza` — Índice de riqueza | V190 … V191 (2) | hogar_vivienda / bienes_riqueza | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec0111_selecciones` — Visitas, altitud y selección para módulos | V027 … V044 (5) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec0111_vivienda_servicios` — Vivienda y servicios del hogar | V113 … ML101 (10) | hogar_vivienda / vivienda_agua_saneamiento | [ ] | [ ] | [ ] | [ ] | [ ] | |

### REC21 (8 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rec21_calidad_informacion` — Calidad de la información de la historia | B10 … B13 (2) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec21_discapacidad` — Dificultades o limitaciones permanentes del niño | QD333_1 … QD333_6 (6) | salud_infantil / discapacidad_infantil | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec21_embarazo` — Duración del embarazo y nacimiento reciente | Q220A … QULT5 (2) | salud_materna_reproductiva / fecundidad_nacimientos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec21_fecha_apertura` — Fecha de apertura de la historia y día de nacimiento | BD … BEDAD (6) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec21_intervalos` — Intervalos entre nacimientos | B11 … B15 (3) | salud_materna_reproductiva / fecundidad_nacimientos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec21_nacimiento` — Nacimiento: orden, tipo de parto, fecha y sexo | B0 … B4 (5) | salud_materna_reproductiva / fecundidad_nacimientos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec21_supervivencia` — Si el niño vive, edad actual y edad a la muerte | B5 … B8 (4) | mortalidad / mortalidad_infantil | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec21_vive_con` — Con quién vive y número de línea en el hogar | B9 … B16 (2) | hogar_vivienda / composicion_hogar | [ ] | [ ] | [ ] | [ ] | [ ] | |

### REC41 (14 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rec41_antitetanica` — Vacuna antitetánica durante el embarazo | M1 … M1E (6) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec41_control_posparto_bebe` — Chequeo posparto de la madre y control del bebé | M66 … M73 (8) | salud_materna_reproductiva / lactancia_posparto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec41_control_posparto_vitamina_a` — Control y vitamina A después del parto | M51A … M55Z (18) | salud_materna_reproductiva / lactancia_posparto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec41_control_prenatal` — Control prenatal: inicio, visitas y exámenes | M13 … M44 (9) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec41_embarazo_deseado` — Momento del embarazo y tiempo que hubiera querido esperar | M10 … M11 (2) | salud_materna_reproductiva / fecundidad_nacimientos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec41_hierro_medicamentos` — Hierro y medicamentos en el embarazo | M45 … M60 (12) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec41_lactancia_duracion` — Duración de la lactancia, la amenorrea y la abstinencia | M4 … M29 (9) | salud_materna_reproductiva / lactancia_posparto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec41_lactancia_inicio_tomas` — Lactancia: inicio, tomas y biberón | M34 … M39 (5) | salud_materna_reproductiva / lactancia_posparto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec41_lugar_cuidado_prenatal` — Lugar del cuidado prenatal | M57A … M57X (23) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec41_parto_estadia_alta` — Parto: estadía, chequeo antes del alta y razones de no ir | M61 … M65X (17) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec41_parto_nacimiento` — Parto y nacimiento: lugar, cesárea, tamaño y peso | M15 … M19A (5) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec41_quien_atendio_parto` — Quién atendió el parto | M3A … M3N (14) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec41_quien_control_prenatal` — Quién hizo el control prenatal | M2A … M2N (14) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec41_vision_nocturna` — Dificultad para ver de noche en el embarazo | M47 … M48 (2) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |

### REC42 (17 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rec42_alimentos_ayer` — Qué comió o bebió el niño ayer | V409 … V414H2 (38) | salud_infantil / alimentacion_infantil | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_alimentos_en_casa` — Alimentos y líquidos que había en casa para el niño | V471A … V472U (28) | salud_infantil / alimentacion_infantil | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_barreras_acceso` — Problemas para atenderse cuando se enferma | V466 … V467M (14) | acceso_salud / barreras_acceso | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_consentimiento` — Menores de 18, responsable y consentimiento | V452A … V452C (3) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_cuidado_ninos` — Quién cuida a los niños | V482A … V482C (3) | familia_pareja / trabajo_mujer_pareja | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_hemoglobina` — Hemoglobina y anemia de la mujer | V453 … V458 (8) | salud_adultos / mujeres_peso_anemia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_higiene_sro` — Higiene y sales de rehidratación | V416 … V465 (3) | hogar_vivienda / vivienda_agua_saneamiento | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_inyecciones` — Inyecciones: número, quién las administró y seguridad | V477 … V480 (4) | acceso_salud / uso_servicios | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_lactancia_actual` — Último parto y lactancia actual | V401 … V426 (7) | salud_materna_reproductiva / lactancia_posparto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_marca_ultimo_nacimiento` — Marca de variables del último nacimiento | V468 … V468 (1) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_mosquiteros` — Mosquiteros | V459 … V461 (3) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_peso_talla_mujer` — Peso, talla e indicadores de la mujer | V437 … V447A (13) | salud_adultos / mujeres_peso_anemia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_registro` — Datos administrativos de registro | V417 … V419 (3) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_seguro_salud` — Seguro de salud de la mujer | V481 … V481X (10) | acceso_salud / seguro_salud | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_tabaco` — Tabaco | V463A … V464 (10) | salud_adultos / tabaco_alcohol | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_tuberculosis` — Tuberculosis: conocimientos y actitudes | V474 … V476 (15) | salud_adultos / enfermedades_cronicas | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec42_vih_prueba` — VIH: consentimiento y resultado | V473A … V473B (2) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |

### REC43 (11 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rec43_bebidas_comida_enfermedad` — Bebidas y comida durante la enfermedad | H38 … H39 (2) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec43_campanas` — Vacunas en campañas | H35 … H36F (7) | salud_infantil / vacunas | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec43_carne_vacunas` — Carné de atención integral y vacunas | H1 … H10 (38) | salud_infantil / vacunas | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec43_diarrea` — Diarrea en los últimos 14 días | H11 … H11B (2) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec43_diarrea_donde_busco` — Dónde buscó tratamiento para la diarrea | H12A … H12Z (26) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec43_diarrea_tratamiento` — Qué se le dio para tratar la diarrea | H13 … H45 (24) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec43_fiebre_tos` — Fiebre y tos en las dos últimas semanas | H22 … H31E (6) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec43_fiebre_tos_donde_busco` — Dónde buscó tratamiento para la fiebre o la tos | H32A … H46B (28) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec43_fiebre_tos_tratamiento` — Qué se le dio para la fiebre o la tos | H37A … H37Z (19) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec43_hierro_antiparasitarios` — Hierro y antiparasitarios | H42 … H43 (2) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec43_vitamina_a` — Vitamina A | H33 … H41B (11) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |

### REC44 (7 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rec44_edad_peso_talla` — Edad, peso y talla del hijo | HW1 … HW3 (3) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec44_fechas` — Fecha de nacimiento y de la medición | HW16 … HW19 (4) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec44_hemoglobina` — Hemoglobina y anemia | HW53 … HW58 (7) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec44_indicadores_oms` — Talla y peso para la edad (patrón OMS 2006) | HW70 … HW73 (4) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec44_indicadores_referencia_anterior` — Talla y peso para la edad (referencia anterior) | HW4 … HW12 (9) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec44_medicion_razon` — Razón por la que no se midió y posición | HW13 … HW15 (2) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec44_responsable_consentimiento` — Responsable y consentimiento | HW51 … HW52 (2) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |

### REC91 (37 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rec91_actitud_planificacion` — Actitud hacia la planificación familiar | S616 … S621A (17) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_afiliacion_seguro` — Afiliación a un seguro de salud | S229B1 … S229CY (4) | acceso_salud / seguro_salud | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_alimentos_ayer` — Alimentos que comió el niño ayer | S493A … S493P (16) | salud_infantil / alimentacion_infantil | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_anemia_conocimiento` — Qué síntomas y alimentos asocia con la anemia | QI479E_A … QI479F_Y (27) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_castigo_hijos` — Cómo castiga el padre y la madre a sus hijos | S1030AA … S1031 (43) | violencia / castigo_disciplina_infantil | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_castigo_infancia` — Cómo la castigaban a ella y opinión sobre el castigo | S1032A … S1033 (17) | violencia / castigo_disciplina_infantil | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_castigo_quien` — Quién reprende o castiga a los hijos | S1028A … S1028Y (4) | violencia / castigo_disciplina_infantil | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_conocimiento_sis` — Conocimiento del Seguro Integral de Salud | S229DA … S229DX (7) | acceso_salud / seguro_salud | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_control_embarazo_lugar` — Dónde fue el control del embarazo | S229A … S229Y (14) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_controles_diu` — Controles de DIU o implante | S327B … S327C (2) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_cuidaria_sida` — Actitud ante familiares con SIDA | S489C … S489D (2) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_divorcio_primera_pareja` — Causa del divorcio y relación con la primera pareja sexual | S508A … S512C (2) | familia_pareja / union_convivencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_documentos_identidad` — Documentos de identificación | S239A … S239X (7) | identidad_cultura / documentos_identidad | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_educacion` — Educación: nivel, asistencia y razón de abandono | S108N … S112 (5) | educacion / nivel_educativo_asistencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_esposo_educacion` — Educación del esposo o compañero | S704N … S704G (3) | educacion / nivel_educativo_asistencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_esterilizacion_pago` — Esterilización: pago y momento | S314 … S315B (2) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_ingresos_cuidado` — Ingresos de la entrevistada y quién cuida a los niños | S718 … S720A (2) | familia_pareja / trabajo_mujer_pareja | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_its` — Infecciones de transmisión sexual | S815AA … S818 (41) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_juntos` — Programa Juntos | S484 … S484Y (4) | programas_sociales / juntos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_lavado_manos` — Lavado de manos | S490 … S490BX (14) | hogar_vivienda / vivienda_agua_saneamiento | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_lengua` — Lengua materna y autoidentificación | S119 … S119D (4) | identidad_cultura / lengua_etnia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_liquidos_ayer` — Líquidos que tomó el niño ayer | S492A … S492G (7) | salud_infantil / alimentacion_infantil | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_llevaria_nino` — Si llevaría al niño al centro de salud | S481AA … S481AZ (9) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_metodo_actual` — Método actual: fuente, decisión y opinión de la atención | S321A … S325GK (19) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_metodos_naturales` — Métodos vaginales y determinación de días fértiles | S317AC … S317C (3) | salud_materna_reproductiva / planificacion_familiar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_papanicolau_mama` — Papanicolaou y examen de mama | S485 … S486B (5) | salud_adultos / prevencion_cancer | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_papilla_programas` — Papilla de programas sociales | S494 … S494B (3) | programas_sociales / hogar_programas | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_presencia_entrevista` — Presencia de otras personas durante la entrevista | S500A … S1034B (6) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_primer_control` — Meses de embarazo al primer control | S229A1 … S229A1 (1) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_quien_alimenta` — Quién alimenta al niño | S495A … S496 (2) | salud_infantil / alimentacion_infantil | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_reuniones_sesiones` — Reuniones y sesiones en los últimos 12 meses | Q479A … Q479D (4) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_ubicacion` — Región natural, semestre, provincia y distrito | SREGION … SDISTRI (4) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_vih_conocimiento` — Conocimiento sobre el VIH/SIDA | S802 … S811 (12) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_vih_prueba` — Prueba de VIH | S803AF … S804C (5) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_violencia_ayuda` — Búsqueda de ayuda ante la violencia | S1023AA … S1026 (11) | violencia / violencia_contra_mujer | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_violencia_consecuencias` — Consecuencias de la agresión y quién agredió | S1008AN … S1017 (7) | violencia / violencia_contra_mujer | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec91_violencia_pareja` — Control y agresiones de la pareja | S1002A … S1002E (5) | violencia / violencia_contra_mujer | [ ] | [ ] | [ ] | [ ] | [ ] | |

### REC94 (8 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rec94_complicaciones_parto` — Complicaciones del parto y razones para no acudir | S426B … S426GE (9) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec94_complicaciones_posparto` — Complicaciones después del parto | S427DA … S427F (8) | salud_materna_reproductiva / lactancia_posparto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec94_controles_prenatales` — Controles prenatales: pruebas y meses de embarazo | S410B … QI411F (15) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec94_hierro_embarazo` — Hierro durante el embarazo | S422I … QI422A_D (5) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec94_inscripcion_nino` — Inscripción del niño y atención al nacer | S430C … S431A (3) | salud_materna_reproductiva / embarazo_control_parto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec94_lactancia` — Lactancia materna: contacto piel a piel, motivos y capacitación | S435 … QI440B (6) | salud_materna_reproductiva / lactancia_posparto | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec94_preparacion_alimentos` — Preparación y almacenamiento de alimentos del niño | S446AA … S448B (6) | salud_infantil / alimentacion_infantil | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec94_seguro` — Seguro de salud de la madre y del niño | S413 … S432AY (6) | acceso_salud / seguro_salud | [ ] | [ ] | [ ] | [ ] | [ ] | |

### REC95 (16 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rec95_control_crecimiento` — Control de crecimiento y desarrollo: si, dónde, cuántos y qué practicó | S466 … S466GC (12) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_controles_crecimiento_detalle` — Controles de crecimiento: fecha, peso y talla | S466DC1 … S466HC12 (60) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_cred_menor_un_mes` — Controles CRED del menor de un mes | QI_CTRL_DIA_01 … QI_CTRL_TALLA_04 (20) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_diarrea` — Diarrea: síntomas, deposiciones y tratamiento | S472AA … S475 (9) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_fiebre_tos` — Fiebre o tos: por qué no acudió y qué tenía en casa | S470 … S471CF (8) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_hemoglobina_tamizaje` — Examen de hemoglobina, diagnóstico de anemia y tratamiento | QI465ED_CC_A … QI465ED_CC_D (10) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_hierro_12_meses` — Hierro y micronutrientes en los últimos 12 meses | S465DB_A … S465DD_DC (12) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_hierro_7_dias` — Hierro y micronutrientes en los últimos 7 días | S465EA … S465ED (4) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_micronutrientes` — Micronutrientes: razones de no consumo y entregas | Q465DF … Q465EC_Y6 (22) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_sintomas_diarios` — Síntomas día a día en la última semana | S476AN1 … S476AR7 (28) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_vacunas_amarilica_sarampion` — Vacunas antiamarílica, SPR y SR | S45ML … S45SRY (16) | salud_infantil / vacunas | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_vacunas_hepatitis_b` — Vacuna contra la hepatitis B | S45B0 … S459B (17) | salud_infantil / vacunas | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_vacunas_hib_penta_tetra` — Vacunas Hib, pentavalente y tetravalente | S45F1 … S45TTY (28) | salud_infantil / vacunas | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_vacunas_neumo_rota_influenza` — Vacunas contra neumococo, rotavirus e influenza | S45NM1 … S45IF2Y (28) | salud_infantil / vacunas | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_vacunas_refuerzos` — Refuerzos de DPT y polio | S45D4 … S45P5Y (16) | salud_infantil / vacunas | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rec95_vitamina_a` — Vitamina A (tercera dosis) y número de vacunas con vitamina A | S45VA3 … S462E (5) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |

### RECH0 (7 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rech0_campo` — Supervisión y edición en campo | HV030 … HV032 (2) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech0_composicion` — Tamaño y composición del hogar | HV009 … HV014 (6) | hogar_vivienda / composicion_hogar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech0_coordenadas` — Coordenadas del conglomerado | LATITUDY … LONGITUDX (2) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech0_identificacion` — Identificación de la vivienda, el hogar y la entrevista | HV002 … HV008 (6) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech0_muestra_dominio` — Muestra, dominio y lugar de residencia | HV020 … HV027 (4) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech0_resultado_entrevista` — Resultado de la entrevista del hogar y visitas | HV015 … HV017 (2) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech0_selecciones` — Selección de niños y mujeres para mediciones y módulos, y altitud | HV035 … HV044 (6) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |

### RECH1 (8 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rech1_asistencia_escolar` — Asistencia a la escuela | HV110 … QH21A (11) | educacion / nivel_educativo_asistencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech1_educacion_alcanzada` — Educación alcanzada | HV106 … HV109 (4) | educacion / nivel_educativo_asistencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech1_elegibilidad` — Elegibilidad para entrevistas y mediciones | HV117 … HV120 (3) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech1_estado_civil` — Estado civil o conyugal | HV115 … HV116 (2) | familia_pareja / union_convivencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech1_nacionalidad` — Nacionalidad y tiempo de residencia en el Perú | QH25B … QH25CA (3) | hogar_vivienda / composicion_hogar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech1_padres` — Madre y padre: si viven y su número de orden | HV111 … HV114 (4) | hogar_vivienda / composicion_hogar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech1_parentesco_presencia` — Parentesco con el jefe del hogar y presencia en el hogar | HV101 … HV103 (3) | hogar_vivienda / composicion_hogar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech1_sexo_edad` — Sexo y edad de las personas del hogar | HV104 … HV105 (2) | hogar_vivienda / composicion_hogar | [ ] | [ ] | [ ] | [ ] | [ ] | |

### RECH23 (16 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rech23_agua_acceso` — Fuente de agua, tiempo para obtenerla y pago | HV201 … SH52 (9) | hogar_vivienda / vivienda_agua_saneamiento | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_agua_tratamiento` — Tratamiento y almacenamiento del agua para beber | HV237 … SH50 (17) | hogar_vivienda / vivienda_agua_saneamiento | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_basura` — Eliminación de la basura | SH58 … SH60 (3) | hogar_vivienda / vivienda_agua_saneamiento | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_bienes` — Bienes del hogar | HV207 … SH77F (27) | hogar_vivienda / bienes_riqueza | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_cloro_agua` — Prueba de cloro en el agua | SH227 … QH227B (3) | hogar_vivienda / vivienda_agua_saneamiento | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_combustible_cocina` — Combustible y cocina | HV226 … SH69 (9) | hogar_vivienda / vivienda_agua_saneamiento | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_electricidad_alumbrado` — Electricidad y alumbrado | HV206 … SH70 (2) | hogar_vivienda / vivienda_agua_saneamiento | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_enfermos_fallecidos` — Personas enfermas, fallecidas y huérfanos del hogar | HV248 … HV251 (4) | mortalidad / muertes_hogar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_jefe_hogar` — Jefe del hogar y composición | HV217 … HV220 (4) | hogar_vivienda / composicion_hogar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_materiales_vivienda` — Materiales y espacios de la vivienda | HV213 … SH76E (12) | hogar_vivienda / vivienda_agua_saneamiento | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_mosquiteros` — Mosquiteros | HV227 … HML2 (5) | salud_infantil / enfermedades_suplementos | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_riqueza` — Índice de riqueza | HV270 … HV271 (2) | hogar_vivienda / bienes_riqueza | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_saneamiento` — Servicio higiénico | HV205 … SH56 (4) | hogar_vivienda / vivienda_agua_saneamiento | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_tierras_ganado_cuenta` — Tierras, ganado y cuenta bancaria | HV244 … SH79 (17) | hogar_vivienda / bienes_riqueza | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_ubicacion_version` — Región natural, semestre, provincia, distrito y versión | SHVER … SHTOTH (6) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech23_yodo_sal` — Yodo en la sal | HV234 … SH225 (4) | hogar_vivienda / vivienda_agua_saneamiento | [ ] | [ ] | [ ] | [ ] | [ ] | |

### RECH4 (5 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rech4_actividad` — Actividad de la última semana | SH13 … SH13 (1) | trabajo / actividad_ocupacion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech4_educacion_actual` — Nivel de educación al que asiste ahora | SH18N … SH18G (3) | educacion / nivel_educativo_asistencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech4_educacion_anio_pasado` — Educación el año pasado | SH20N … SH21 (4) | educacion / nivel_educativo_asistencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech4_educacion_aprobada` — Nivel de educación aprobado | SH15N … SH15G (3) | educacion / nivel_educativo_asistencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech4_seguro_salud` — Seguro de salud de las personas del hogar | SH11A … SH12 (8) | acceso_salud / seguro_salud | [ ] | [ ] | [ ] | [ ] | [ ] | |

### RECH5 (8 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rech5_consentimientos` — Responsable, consentimientos y resultado de la entrevista individual | HA51 … HA65 (5) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech5_edad_nacimiento` — Edad, fecha de nacimiento y grupo de la mujer | HA1 … HA50 (4) | hogar_vivienda / composicion_hogar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech5_educacion` — Educación de la mujer | HA66 … HA68 (3) | educacion / nivel_educativo_asistencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech5_estado_civil` — Estado civil | HA60 … HA60 (1) | familia_pareja / union_convivencia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech5_hemoglobina` — Hemoglobina y anemia de la mujer | HA53 … HA58 (8) | salud_adultos / mujeres_peso_anemia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech5_peso_talla` — Peso, talla e indicadores nutricionales de la mujer | HA2 … HA41 (12) | salud_adultos / mujeres_peso_anemia | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech5_tabaco` — Cigarrillos fumados en las últimas 24 horas | HA35 … HA35 (1) | salud_adultos / tabaco_alcohol | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech5_vih` — Resultado de la prueba de VIH | HA63 … HA63 (1) | salud_adultos / vih_its | [ ] | [ ] | [ ] | [ ] | [ ] | |

### RECH6 (9 bloques)

| Bloque | Variables | Tema / subtema | (a) | (b) | (c) | (d) | (e) | Observación |
|---|---|---|---|---|---|---|---|---|
| `endes_rech6_edad_peso_talla` — Edad, peso y talla de la niña o el niño | HC1 … HC3 (3) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech6_fechas` — Fecha de nacimiento y año de la medición | HC16 … HC33 (6) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech6_hemoglobina` — Hemoglobina y anemia | HC53 … HC58 (7) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech6_indicadores_oms` — Talla y peso para la edad (patrón OMS 2006) | HC70 … HC73 (4) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech6_indicadores_referencia_anterior` — Talla y peso para la edad (referencia anterior) | HC4 … HC12 (9) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech6_madre` — Madre: orden, educación, intervalo y orden de nacimiento | HC60 … HC68 (6) | hogar_vivienda / composicion_hogar | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech6_medicion_razon` — Razón por la que no se midió y posición de la medición | HC13 … HC15 (2) | salud_infantil / anemia_desnutricion | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech6_responsable_consentimiento` — Responsable y consentimiento | HC51 … HC52 (2) | identificacion_encuesta / campo_y_muestra | [ ] | [ ] | [ ] | [ ] | [ ] | |
| `endes_rech6_sexo` — Sexo | HC27 … HC27 (1) | hogar_vivienda / composicion_hogar | [ ] | [ ] | [ ] | [ ] | [ ] | |

## 3. Cosas generales

- [ ] La taxonomía de `temas.yaml` (incluidos los temas y subtemas agregados en M1-06-s1) es coherente; ningún bloque en un subtema que no corresponde.
- [ ] Las 105 excepciones de `clases_excepciones.yaml` son correctas (cada una con su motivo); las variables `medida` que en realidad son marcas de sí/no y las `categoria` que en realidad son medidas.
- [ ] Las 14 variables `texto` y las `diseno` del campo (códigos del equipo, versiones) están bien clasificadas.
- [ ] La llave de cada tabla y las uniones con su `cita` del documento n.º 11 (`archivos_endes_2024.yaml`); C-M1-06-1 (`CSALUD01`).
- [ ] Las 15 tablas sin bloques (CSALUD01, CSALUD08, PS_*, Programas_Sociales_x_Hogar, REC82, REC83, REC84DV, REC93DVdisciplina, RECHM) tienen su ficha correcta aunque no tengan bloques.

## Hallazgos

| # | Tabla o bloque | Qué está mal | Qué dice el diccionario o el cuestionario (página) | Propuesta | ¿Tipo C? | Estado |
|---|---|---|---|---|---|---|
| | | | | | | |

## Veredicto

(Rellena el auditor-agente: «aprobado», «aprobado con observaciones» o «con hallazgos abiertos», con la lista de consultas anotadas. Aquí también se anota el lote que se propone al dueño para el visto.)
