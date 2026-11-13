| Clase | Variables |
|---|---|
| llave | 100 |
| geo | 17 |
| categoria | 1,984 |
| medida | 625 |
| peso | 11 |
| diseno | 105 |
| texto | 14 |
| **Total** | **2,856** |

## Por tabla

| Tabla | llave | geo | categoria | medida | peso | diseno | texto | Total |
|---|---|---|---|---|---|---|---|---|
| CSALUD01 | 2 | 0 | 188 | 56 | 1 | 7 | 4 | 258 |
| CSALUD08 | 3 | 0 | 34 | 8 | 1 | 4 | 3 | 53 |
| DIT | 4 | 0 | 58 | 1 | 0 | 1 | 0 | 64 |
| PS_BECA18 | 3 | 0 | 1 | 2 | 0 | 4 | 0 | 10 |
| PS_COMEDOR | 3 | 0 | 1 | 2 | 0 | 4 | 0 | 10 |
| PS_PENSION65 | 3 | 0 | 1 | 2 | 0 | 4 | 0 | 10 |
| PS_QALIWARMA | 2 | 0 | 2 | 3 | 0 | 4 | 0 | 11 |
| PS_TRABAJA | 3 | 0 | 1 | 2 | 0 | 4 | 0 | 10 |
| PS_VL | 3 | 0 | 1 | 2 | 0 | 4 | 0 | 10 |
| PS_WAWAWASI | 3 | 0 | 1 | 2 | 0 | 4 | 0 | 10 |
| Programas_Sociales_x_Hogar | 1 | 0 | 9 | 6 | 0 | 4 | 0 | 20 |
| RE223132 | 2 | 0 | 108 | 39 | 0 | 1 | 0 | 150 |
| RE516171 | 2 | 0 | 60 | 22 | 0 | 1 | 0 | 85 |
| RE758081 | 2 | 0 | 185 | 11 | 0 | 1 | 0 | 199 |
| REC0111 | 4 | 6 | 48 | 22 | 6 | 18 | 0 | 104 |
| REC21 | 5 | 0 | 14 | 14 | 0 | 2 | 0 | 35 |
| REC41 | 3 | 0 | 124 | 20 | 0 | 1 | 0 | 148 |
| REC42 | 3 | 0 | 142 | 22 | 0 | 3 | 0 | 170 |
| REC43 | 3 | 0 | 129 | 36 | 0 | 1 | 0 | 169 |
| REC44 | 4 | 0 | 7 | 22 | 0 | 2 | 0 | 35 |
| REC82 | 3 | 0 | 0 | 0 | 0 | 1 | 1 | 5 |
| REC83 | 3 | 0 | 9 | 7 | 0 | 1 | 0 | 20 |
| REC84DV | 2 | 0 | 215 | 3 | 0 | 1 | 0 | 221 |
| REC91 | 2 | 2 | 320 | 18 | 0 | 2 | 0 | 344 |
| REC93DVdisciplina | 4 | 0 | 10 | 0 | 0 | 1 | 4 | 19 |
| REC94 | 3 | 0 | 47 | 11 | 0 | 1 | 0 | 62 |
| REC95 | 4 | 0 | 99 | 196 | 0 | 1 | 1 | 301 |
| RECH0 | 4 | 7 | 6 | 10 | 2 | 15 | 0 | 44 |
| RECH1 | 4 | 0 | 21 | 9 | 0 | 1 | 1 | 36 |
| RECH23 | 2 | 2 | 97 | 28 | 0 | 1 | 0 | 130 |
| RECH4 | 2 | 0 | 16 | 3 | 0 | 1 | 0 | 22 |
| RECH5 | 3 | 0 | 16 | 18 | 1 | 2 | 0 | 40 |
| RECH6 | 4 | 0 | 11 | 26 | 0 | 2 | 0 | 43 |
| RECHM | 2 | 0 | 3 | 2 | 0 | 1 | 0 | 8 |

## Excepciones aplicadas

| Variables | Tablas | Clase | Motivo |
|---|---|---|---|
| BORD | REC21 | llave | Documento n.º 11, fila 17: REC21 se identifica por CASEID + BIDX o CASEID + BORD (comprobado: única en las 60 693 filas). La tercera, CASEID + B16, no es única en los datos (B16 = 0 se repite): no se trata como llave. |
| BORD | DIT | llave | Documento n.º 11, fila 32: DIT se identifica por CASEID + BIDX o CASEID + BORD (orden del hijo según el nacimiento). |
| Q452 | REC95 | llave | Documento n.º 11, fila 31: REC95 se identifica por CASEID + IDX95 o CASEID + Q452 (BORD = Q1035NO = Q452). |
| Q1035NO | REC93DVdisciplina | llave | Documento n.º 11, fila 29: REC93DVdisciplina se identifica por CASEID + QCOL93 o CASEID + Q1035NO. |
| QS203U, QS204U, QS205U, QS207U, QS211U, QS214U, QS216U, QS218U | CSALUD01 | categoria | Unidad en que se contesta la pregunta anterior (1 = años, número de veces…): la etiqueta nombra la unidad, el valor no se promedia. |
| QS212Z | CSALUD01 | categoria | Marca «no sabe/no recuerda» (1 = sí sabe o recuerda): respuesta de dos opciones con una sola etiqueta. |
| V3A08Z | RE223132 | categoria | Marca de una respuesta («No sabe») con una sola etiqueta. |
| V042, V043, V130 | REC0111 | categoria | V042 y V043: marcas de selección (1 = seleccionada); V130: religión, sus códigos son categorías aunque el archivo solo etiquete «Otra». |
| V454, V468 | REC42 | categoria | V454: embarazada según el hogar (1 = sí); V468: marca de qué nacimientos entran (1 = solo el último). |
| MM10 | REC83 | categoria | Si la muerte y el embarazo están relacionados (1 = sí, y otras dos respuestas): respuesta de opciones. |
| ID1 | todas | diseno | Año de la encuesta (2024 en todas las filas): identifica la encuesta, no mide nada. |
| V028, V029, V030, V031, V032, V033, V420, V421 | REC0111, REC42 | diseno | Códigos del equipo de campo (entrevistador, digitador, supervisor, editor, registrador) y selección final del área: operación de campo. |
| SVER | REC91 | diseno | Versión del cuestionario (0 en todas las filas). |
| NCONGLOME1 | RECH0 | diseno | Número de conglomerado del marco muestral. |
| HA62 | RECH5 | diseno | Número de identificación de la muestra de sangre (código del laboratorio). |
| QFIN, QS8INICIO | CSALUD01 | diseno | Marcas de la entrevista (final del informante, indicación de inicio de capítulo): flujo del cuestionario. |
| AWFACTE, AWFACTR, AWFACTT, AWFACTU, AWFACTW | REC0111 | peso | Factores «todas las mujeres» (100 en todas las filas): factores de ponderación de la muestra. |
| HV028 | RECH0 | peso | Peso de muestra masculino (factor de ponderación; vacío en la ENDES). |
| HA69 | RECH5 | peso | Peso del VIH (factor de ponderación con 6 decimales; vacío en la ENDES). |
| CODCCPP, NOMCCPP | RECH0 | geo | Código y nombre del centro poblado. |
| V000, HV000 | REC0111, RECH0 | diseno | Código y fase del país (texto fijo). |
| QSNUMERO | CSALUD01 | llave | Documento n.º 11, fila 33 y «Precisiones» (HVIDX = QSNUMERO); el diccionario de CSALUD01 lo marca como llave. Solo el índice: la llave declarada en archivos_endes_2024.yaml no se cambia (consulta C-M1-06-1). |
| V003 | REC0111 | llave | Número de línea de la entrevistada en el hogar (une REC0111 con RECH1 por V003 = HVIDX). |
| HV002, HV002A | RECH0 | llave | Número de vivienda y de hogar: forman HHID (documento n.º 11, «Precisiones»: HHID = HV001 + HV002 + HV002A). |
| HV003 | RECH0 | llave | Número de línea de una persona del hogar (referencia a HVIDX; documento n.º 11, «Precisiones»: HVIDX = IDXH4 = B16 = HA0 = HC0 = QSNUMERO = QS801): sirve para unir, no para medir (informante). |
| HC60, HC51 | RECH6 | llave | Número de línea de una persona del hogar (referencia a HVIDX; documento n.º 11, «Precisiones»: HVIDX = IDXH4 = B16 = HA0 = HC0 = QSNUMERO = QS801): sirve para unir, no para medir (madre y padre o responsable). |
| HA51 | RECH5 | llave | Número de línea de una persona del hogar (referencia a HVIDX; documento n.º 11, «Precisiones»: HVIDX = IDXH4 = B16 = HA0 = HC0 = QSNUMERO = QS801): sirve para unir, no para medir (padre o responsable). |
| HW51 | REC44 | llave | Número de línea de una persona del hogar (referencia a HVIDX; documento n.º 11, «Precisiones»: HVIDX = IDXH4 = B16 = HA0 = HC0 = QSNUMERO = QS801): sirve para unir, no para medir (padre o responsable). |
| HV112, HV114 | RECH1 | llave | Número de línea de una persona del hogar (referencia a HVIDX; documento n.º 11, «Precisiones»: HVIDX = IDXH4 = B16 = HA0 = HC0 = QSNUMERO = QS801): sirve para unir, no para medir (madre y padre). |
| HV218 | RECH23 | llave | Número de línea de una persona del hogar (referencia a HVIDX; documento n.º 11, «Precisiones»: HVIDX = IDXH4 = B16 = HA0 = HC0 = QSNUMERO = QS801): sirve para unir, no para medir (jefe del hogar). |
| V034 | REC0111 | llave | Número de línea de una persona del hogar (referencia a HVIDX; documento n.º 11, «Precisiones»: HVIDX = IDXH4 = B16 = HA0 = HC0 = QSNUMERO = QS801): sirve para unir, no para medir (esposo). |
| V452B | REC42 | llave | Número de línea de una persona del hogar (referencia a HVIDX; documento n.º 11, «Precisiones»: HVIDX = IDXH4 = B16 = HA0 = HC0 = QSNUMERO = QS801): sirve para unir, no para medir (padre o apoderado). |
| QS800 | CSALUD08 | llave | Línea de la niña o el niño en el hogar (QS801 = HVIDX, documento n.º 11). |
| B16 | REC21 | llave | Línea del niño en el hogar (B16 = HVIDX; 0 = no listado). Sirve para unir; no es única (el documento n.º 11 la da como identificador alterno pero el 0 se repite). |
| PS1, PS2, PS3, PS4, PS5, PS6 | PS_BECA18, PS_TRABAJA, PS_PENSION65, PS_VL, PS_COMEDOR, PS_WAWAWASI | llave | Número de orden de la persona beneficiaria en el listado del hogar (= HVIDX). |
| HV004 | RECH0 | diseno | Unidad última de muestreo: dato de la muestra. |
| V004 | REC0111 | diseno | Unidad de área final: dato de la muestra. |
| HV007, HV008 | RECH0 | diseno | Año y fecha de la entrevista: identifican la encuesta, no miden a las personas. |
| V007, V008 | REC0111 | diseno | Año y fecha de la entrevista: identifican la encuesta, no miden a las personas. |
| HC19 | RECH6 | diseno | Año de la medición (2024 en todas las filas). |
| HW19 | REC44 | diseno | Año de la medición (2024 en todas las filas). |
| BAA | REC21 | diseno | Año de apertura de la historia de nacimientos (2024). |
| QSINTY | CSALUD01 | diseno | Año de la visita final (2017 en todas las filas). |
| HV030, HV031, HV032, HV033 | RECH0 | diseno | Supervisor, editor de campo, editor de la oficina y probabilidad de selección del área: operación de campo y diseño (misma regla que V028–V033). |
| QHHOME, QHNUMBER | todas | diseno | Hogar y vivienda seleccionados (marcas de la muestra): misma clase en todas las tablas. |
| HV023 | RECH0 | diseno | Dominio de la muestra. Regla de geografía: lo que define la muestra (región HV024, dominio, región de residencia) es `diseno`; el tipo y el lugar de residencia (urbano/rural, capital, ciudad, pueblo) son `geo`. |
| V023, V101, V139 | REC0111 | diseno | Dominio y región de la muestra o de residencia (regla de geografía: lo que define la muestra es `diseno`). |
| V102, V140, V141, V026 | REC0111 | geo | Tipo y lugar de residencia (regla de geografía: igual que V025, que es `geo`). |
| HV026 | RECH0 | geo | Lugar de residencia (capital, ciudad, pueblo, campo): regla de geografía. |
| LATITUDY, LONGITUDX | RECH0 | geo | Coordenadas del conglomerado. |
| SHPROVIN, SHDISTRI | RECH23 | geo | Provincia y distrito del hogar (códigos de ubicación). |
| SPROVIN, SDISTRI | REC91 | geo | Provincia y distrito de la entrevistada (códigos de ubicación). |
| HV246B, HV246F | RECH23 | medida | Cantidad de vacas/toros y de pollos: conteos como las demás cantidades de ganado HV246A–J (la regla de valores sin etiqueta no las alcanza por tener menos de 15 valores distintos). |
