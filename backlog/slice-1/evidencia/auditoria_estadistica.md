# Auditoría estadística S1-09 (rama `slice-1`, commit `cc7f58b`)

Auditor: subagente nuevo, independiente del implementador (P-06; encargo: `encargo_s1-09_auditor.md`). Sin leer los informes de los otros revisores. No editó ningún archivo del repositorio. Respuestas en `salidas/s1-09_auditor/` (fuera de git): `h2020/`, `a2020/`, `extra/`.

## Veredicto: **no apto**

Un hallazgo **bloqueante** (H1): cuando una serie de la ENDES termina en 2020, la respuesta compara con 2020, lo que E-07 prohíbe, y dice «pasó de 34,0 % a 32,4 %» aunque la prueba no muestra un cambio claro (p = 0,65). Dos **altos**: H2, la evolución del gasto omite 2023 pese a que G-07 fija la serie 2023–2025, sin avisar; H3, la capa 3 atribuye a un documento del INEI un valor que ese documento no publica. Todas las cifras verificadas coinciden con el cubo y, cuando la hay, con su dorada: el problema está en cómo se comparan y se citan, no en los números.

## Revisión del catálogo y del planificador (`intenciones.yaml`, `planificador.py`)

| Pregunta del encargo | Resultado | Evidencia |
|---|---|---|
| ¿Cobertura del SIEN por provincia o distrito? | **No.** Solo «regional» (departamento o ámbito de Lima); en el país se omite (`nacional` no está en sus niveles válidos). Con `--indicador` para un distrito, sube al departamento y dice «no se puede» | `intenciones.yaml:66-68, 89, 97`; sonda `--indicador sien_cobertura_tamizaje_6_35m --territorio "Ayaviri, Melgar"` |
| ¿Cruce fuera de CR-01? ¿Coeficientes? | **No.** `requiere_cruce` solo acepta el cruce `activo_piloto` (CR-01) y la cadena de gasto de R-GASTO-08b; otro cruce sale como cifras separadas, sin coeficientes | `planificador.py:188-194, 277-291`; sonda `cruce pobreza Cusco` |
| ¿Tendencia entre los dos criterios de anemia? | **No.** Cada serie se compara consigo misma; la ficha dice «No permite concluir… entre 2015 (anterior) y 2025 (vigente)» | `intenciones.yaml:150-156`; respuestas 1 y 4 |
| E-07: ¿se excluye solo 2020 y se cortan los demás quiebres? | **Parcialmente.** 2020 queda fuera como año de inicio, pero no como año final (H1). Los quiebres de programa, criterio y sistema sí cortan | `planificador.py:60-75` (`_comparable` solo mira el año inicial) |
| E-06: ¿dos formas solo en evolución, primer y último año, sin intermedios? | **Sí** | `intenciones.yaml:72-80, 150-156`; respuesta 1 |
| T-03: ¿Lima por ámbitos? | **Sí** | `planificador.py:115-116`; sondas «Lima», San Juan de Lurigancho |
| E-08: ¿grupo robusto del Mapa por distrito y grupos del INEI por departamento? | **Sí** (grupo robusto 1: 3 distritos, rojo; grupo 1 INEI 2025: 7 departamentos, 35,7–39,8) | `intenciones.yaml:185-197`; respuestas 10 y 11 |
| ¿El planificador se adelanta a supresiones del validador (E-02, E-03, P-04)? | **No.** Solo usa metadatos fijos | `planificador.py:10-11, 414-429` |
| S-01 | Se cumple (rótulo «en establecimientos…», dos cotas, semáforo por la cota superior, aviso si cruza el 50 %, no se compara con la ENDES) | Respuestas 3 y 14 |
| G-07 y R-03 | Cruce lado a lado y sin coeficiente; la serie 2023–2025 no se respeta en evolución (H2) | Respuestas 12 y 14 |

## Las 15 respuestas revisadas

Todas con `uv run pap preguntar --salida salidas/s1-09_auditor` más las opciones de cada fila; todas con código 0.

| # | Opciones | Resultado |
|---|---|---|
| 1 | `--intencion evolucion --tema anemia --territorio "Perú"` | Verde. Vigente 34,9 % (2025), sin cambio claro frente a 2024 (p = 0,62); anterior 43,4 % (2015) y 43,4 % (2025), sin cambio (p = 0,96). Ver H3 |
| 2 | `--intencion nivel_actual --tema anemia --territorio "Puno" --elegir 1` | Verde. 56,1 %, ENDES 2025 |
| 3 | `--intencion nivel_actual --tema anemia --territorio "Ayaviri, Melgar"` | Ámbar. Primero «no se puede saber»; SIEN ≈10 % (7–12 %) de 547; ENDES Puno 56,1 %; cobertura 39,8–50,5 % con aviso |
| 4 | `--intencion evolucion --tema anemia --territorio "Lima Metropolitana"` | Verde. Vigente 25,3 %, sin cambio (p = 0,57); anterior 35,5 → 35,0 %, sin cambio (p = 0,86) |
| 5 | `--intencion evolucion --tema desnutricion_cronica --territorio "Huancavelica" --elegir 1` | Verde. 34,0 % (2015) → 20,3 % (2025), bajó de forma clara (p = 3,3e-05); compara a través de 2020 (E-07) |
| 6 | `--intencion nivel_actual --tema desnutricion_cronica --territorio "Ayaviri, Melgar"` | No se puede (sin cifra por distrito); ofrece Puno |
| 7 | `--intencion nivel_actual --tema pobreza_monetaria --territorio "Cajamarca" --elegir 1` | Verde. 41,0 %, ENAHO 2025 |
| 8 | `--intencion evolucion --tema pobreza_monetaria --territorio "Perú"` | Verde. 27,6 → 25,7 %, bajó de forma clara (p = 0,0077) |
| 9 | `--intencion nivel_actual --tema pobreza_monetaria --territorio "Ayaviri, Melgar"` | Rojo fijo. Mapa 2018, 23–42 %. Texto redundante (H7) |
| 10 | `--intencion identificar_extremo --tema pobreza_monetaria --nivel distrito` | Rojo. Primero «no se puede nombrar un solo distrito»; grupo robusto 1 en orden alfabético; grupo 1 INEI 2025 como contexto |
| 11 | `--intencion identificar_extremo --tema pobreza_monetaria --nivel departamento` | Verde. Grupo 1 oficial INEI 2025: 7 departamentos; 35,7–39,8 % |
| 12 | `--intencion evolucion --tema gasto_publico --territorio "Perú"` | Verde. S/ 2 429,0 → 2 455,9 millones (2024–2025). **No aparece 2023** (H2) |
| 13 | `--intencion nivel_actual --tema gasto_publico --territorio "Callao"` | Verde. S/ 22,6 millones, 2025 |
| 14 | `--intencion efecto --tema anemia --territorio "Apurímac"` | Ámbar, parcial. Gasto S/ 78,7 M; SIEN 60–66 %; ENDES 40,6 %, sin cambio (p = 0,57); estructura de efecto sin causalidad |
| 15 | `--intencion cruce --tema pobreza_monetaria --territorio "Cusco" --elegir 1` | Ámbar. Cruce fuera de la lista blanca: solo pobreza 18,8 % |

**Sondas adicionales:** `nivel_actual anemia Perú --anio 2030` (H7); `comparacion anemia "Lima Región" --comparar-con Callao` (H4); `nivel_actual anemia "San Juan de Lurigancho"` (correcto); `evolucion desnutricion_cronica Perú --hasta 2020` y `Huancavelica --elegir 1 --anio 2020` (H1); `evolucion desnutricion_cronica Perú --desde 2020` (correcto, 2021–2025); `evolucion gasto_publico Perú --desde 2023` (H2); `evolucion anemia Perú --hasta 2020` (no se puede, correcto) y `--hasta 2024` (H6); `identificar_extremo anemia --nivel departamento` (H5); `--territorio "Lima"` (T-03 correcto); `nivel_actual --indicador endes_anemia_6_35m Perú` (H8).

## Cifras verificadas

Cubo `05_biblioteca/indicadores/fact_indicador.parquet` (DuckDB); doradas `codigo/capa0/datos/cifras_doradas.csv`.

| Fuente | Indicador | Año | Nivel | Territorio | En la respuesta | Cubo / dorada | ¿Coincide? |
|---|---|---|---|---|---|---|---|
| ENDES | anemia vigente | 2025 | nacional | Perú | 34,9 % (INEI 33,7–36,1) | cubo 34,895; DOR-OMS-2025-PE 34,9 (33,7–36,1) | Sí |
| ENDES | anemia vigente | 2024 | nacional | Perú | comparada 35,3 | cubo 35,327; DOR-OMS-2024-PE 35,3 | Sí; sin cambio, p = 0,618 ✓ |
| ENDES | anemia vigente | 2025 | departamento | Puno | 56,1 % | cubo 56,069; DOR-OMS-2025-21 56,1 | Sí |
| ENDES | anemia vigente | 2025 | ámbito | Lima Metropolitana | 25,3 % (21,9–28,7) | cubo 25,321; DOR-OMS-2025-LM1501 25,3 | Sí; p = 0,569 ✓ |
| ENDES | anemia vigente | 2025 | departamento | Apurímac | 40,6 % | cubo 40,564 (2024: 43,006) | Sí; p = 0,568 ✓ |
| ENDES | anemia vigente | 2025 | ámbito | Lima Región / Callao | 32,2 % / 28,4 % | cubo 32,221 / 28,406 | Sí |
| ENDES | anemia anterior | 2025 | nacional | Perú | 43,4 % (42,1–44,7) | cubo 43,395; DOR-ANE-2025-PE 43,4 | Sí |
| ENDES | anemia anterior | 2015 | nacional | Perú | 43,4 %, citado a la Nota de prensa 094-2016 | cubo 43,353; **DOR-ANE-2015-PE 43,5** (informativa) | Valor dentro de lo esperado (E-05), **cita no** (H3); p = 0,962 ✓ |
| ENDES | anemia anterior | 2015 / 2025 | ámbito | Lima Metropolitana | 35,5 % / 35,0 % | cubo 35,483 / 35,049 | Sí; p = 0,860 ✓ |
| ENDES | desnutrición crónica | 2025 | departamento | Huancavelica | 20,3 % (15,9–24,7) | cubo 20,284; DOR-DCI-2025-09 20,3 | Sí |
| ENDES | desnutrición crónica | 2015 | departamento | Huancavelica | 34,0 % | cubo 34,006 | Sí; bajó, p = 3,3e-05 ✓ |
| ENDES | desnutrición crónica | 2021 / 2025 | nacional | Perú | 11,5 % / 12,1 % | cubo 11,468 / 12,057; doradas 11,5 / 12,1 | Sí; p = 0,207 ✓ |
| ENDES | desnutrición crónica | 2015 / 2020 | nacional | Perú | 14,3 % / 12,1 % | cubo 14,253 / 12,083; **DOR-DCI-2015-PE 14,4**, DOR-DCI-2020-PE 12,1 | Valores sí; **cita de 2015 no** (H3); comparación con 2020 prohibida (H1) |
| ENDES | desnutrición crónica | 2015 / 2020 | departamento | Huancavelica | «pasó de 34,0 % a 32,4 %» | cubo 34,006 / 32,442; p = 0,655 | Cifras sí; **la frase no** (H1) |
| ENAHO | pobreza monetaria | 2025 / 2024 | nacional | Perú | 25,7 % / 27,6 % | cubo 25,667 / 27,579; doradas 25,7 / 27,6 | Sí; p = 0,0077 ✓ |
| ENAHO | pobreza monetaria | 2025 | departamento | Cajamarca | 41,0 % | cubo 41,036; DOR-POB-2025-06 41,0 | Sí |
| ENAHO | pobreza monetaria | 2025 | departamento | Cusco | 18,8 % | cubo 18,776; DOR-POB-2025-08 18,8 | Sí |
| ENAHO | grupo 1 INEI | 2025 | departamento | 05, 06, 09, 10, 16, 19, 21 | 7 departamentos; 35,7–39,8 % | `grupos_oficiales_inei.csv` idéntico; valores = doradas | Sí |
| SIEN | anemia en tamizados | 2025 | distrito | Ayaviri | ≈10 % (7–12 %), 547 | cubo 9,506 (7,32–12,25), 52/547; DOR-SIEN-2025-210801 9,5 | Sí |
| SIEN | anemia en tamizados | 2025 | distrito | San Juan de Lurigancho | ≈8 % (7,8–8,6 %), 19 750 | cubo 8,208, 1 621/19 750; DOR-SIEN-2025-150132 8,2 | Sí |
| SIEN | cobertura | 2025 | departamento | Puno / Apurímac | 39,8–50,5 % / 60–66 % | cotas 39,82–50,50 / 60,17–65,76 | Sí |
| SIEN | cobertura | 2025 | ámbito | Lima Metropolitana | 30–38 % | cotas 30,26–37,71 | Sí |
| Gasto MEF | ex-PAN devengado | 2025 / 2024 | nacional | Perú | S/ 2 455,9 M / 2 429,0 M | cubo 2 455 856 886 / 2 429 016 663; G-07 2 456 / 2 429 | Sí; falta 2023 (2 179,2; G-07: 2 179), H2 |
| Gasto MEF | ex-PAN devengado | 2025 | ámbito / departamento | Callao / Apurímac | S/ 22,6 M / 78,7 M | cubo 22 627 969 / 78 699 163 | Sí |
| Mapa | intervalo | 2018 | distrito | Ayaviri | 23–42 % | cubo 23,30–42,27 | Sí |
| Mapa | grupo robusto 1 | 2018 | distrito | Uchuraccay / Oxamarca / Anguía | 73–89 / 75–87 / 72–86 % | cubo grupo 1 solo 050410, 060308, 060402; doradas coinciden | Sí |

**Verbos de cambio:** coinciden con `prueba_cambio` en todos los casos, salvo H1.

## Hallazgos

**H1 — Bloqueante. Serie ENDES que termina en 2020: compara con 2020 y dice «pasó de…» sin cambio claro.** `evolucion --tema desnutricion_cronica --territorio "Huancavelica" --elegir 1 --anio 2020` → «Entre 2015 y 2020, la desnutrición crónica… pasó de 34,0 % a 32,4 % en Huancavelica», verde. E-07: 2020 «no se compara»; p = 0,655 (R-ENC-11 pide «sin cambio claro»); el aviso de R-ENC-13 no llega (`avisos` vacío); la tarjeta de 2015 dice «no se compara», contra la capa 1. También con `--hasta 2020` (Perú: «pasó de 14,3 % a 12,1 %»), y en toda la franja «intermedio» de desnutrición de la matriz (`generar.py:127`). Evidencia: `planificador.py:67-75` (`_comparable(a, b)` no descarta el año final `b`); `plantillas.py:499-503` (`corta_sin_prueba` con la comparación bloqueada; `textos/plantillas/evolucion.yaml:5`); `comparaciones_bloqueadas = [...__09__2020__principal]`. Corrección: tratar como no comparable un año final excluido (en `_comparable`, `anio_anterior`, `anio_primero`); con comparación bloqueada usar `corta_sin_comparacion` y mostrar el aviso de R-ENC-13; pruebas con `--anio 2020` y `--hasta 2020`.

**H2 — Alto. La evolución del gasto ex-PAN omite 2023 (G-07: serie 2023–2025) e ignora `--desde 2023` sin avisar.** `dim_indicador.yaml:1173-1177`: el quiebre de 2025 (L11, «comparable por concepto») tiene `comparable_con: [2024]`, y `planificador.py:73` exige el año inicial en esa lista: 2023–2025 no es comparable. La tabla curada admite dos lecturas → **tipo C** (`consultas_al_dueno.md`); propuesta: `comparable_con` de L11 con 2023, en línea con G-07. En todo caso, cuando un `--desde` no se pueda respetar, la respuesta debe decirlo.

**H3 — Alto. La capa 3 atribuye al INEI un valor que su documento no publica.** Perú, anemia anterior 2015: «43,4 % (intervalo: 42,2 % a 44,5 %)… Fuente: INEI, Nota de prensa N.º 094-2016 (ENDES 2015), p. 1», que publica 43,5 % (DOR-ANE-2015-PE); desnutrición 2015: 14,3 % frente a 14,4 % (DOR-DCI-2015-PE). Evidencia: `capas.py:68-71` (`_cita` usa el documento oficial siempre que hay `contraste_oficial`), frente a `_fuente` (`capas.py:47-49`, solo «el INEI publica la misma cifra» con diferencia ≤ 0,1). Corrección: citar el documento del INEI solo si el valor redondeado coincide; si no, «Pregunta al Perú, cálculo propio con ENDES 2015 (INEI); el INEI publicó 43,5 %».

**H4 — Medio.** Comparación Lima Región–Callao: «Territorio: Lima Región (algunas cifras solo están por Callao)». La línea de territorio de una comparación debe nombrar los dos lugares.

**H5 — Medio.** Lugar más alto de anemia por departamento con grupo de uno: «son un departamentos, sin diferencias estadísticamente claras entre ellos… en Puno (56,1 %)». Estadística correcta (Puno supera a todos, p ≤ 0,019), texto equivocado: forma en singular. Observación: el grupo se arma con pruebas de a dos sin ajuste por comparaciones múltiples (`plantillas.py:612-617`), método de R-ENC-12; no se propone cambiarlo.

**H6 — Bajo.** `evolucion anemia Perú --hasta 2024` → «no se puede» aunque la forma anterior tiene serie 2015–2024; además «Puedes preguntar por cuánto hay ahora» (2025).

**H7 — Bajo.** «son de de 2024 a 2025» (`textos/no_se_puede.yaml:78`); «Territorio: país de Perú» / «departamento de Perú»; Mapa «…en 2018 (estimación del INEI) en Ayaviri en 2018»; SJL «alrededor de 8 % (entre 7,8 % y 8,6 %)».

**H8 — Bajo.** `nivel_actual --indicador endes_anemia_6_35m --territorio "Perú"` responde con la forma anterior en un «¿cuánta hay?» (E-06: solo la vigente); lo pidió el usuario y va rotulado. Mostrar al lado la vigente o una nota.

## Lo que no verifiqué

- La nota de privacidad de P-04 (casos de 5 a 10 como rango) no apareció en estas respuestas.
- La covarianza entre años de la ENAHO (panel): la prueba usa covarianza 0; si es positiva, es conservadora y no cambia el «bajó» de la respuesta 8.

## Segunda revisión (tras las correcciones)

HEAD de `slice-1` con las correcciones `018b186`, `5d9542c`, `5b51c3b` y `1603698` y la decisión C-05; huella del cubo `ba1fbc55`. Se volvieron a correr los comandos de A-H1 a A-H8 y siete de las 15 respuestas (1, 3, 5, 8, 10, 14 y la evolución del gasto de Apurímac), con `--salida salidas/s1-09_auditor_r2/<carpeta>`; todos con código 0. Sin pytest ni ediciones.

### Veredicto: **apto con observaciones**

Ningún hallazgo bloqueante ni alto abierto. Las cifras siguen coincidiendo con el cubo y las doradas, y los verbos de cambio con `prueba_cambio`. Quedan observaciones medias o bajas (N-1 a N-3 y lo pendiente de A-H6, A-H7 y A-H8).

### Estado de los hallazgos

| Hallazgo | Estado | Evidencia |
|---|---|---|
| A-H1 (bloqueante) | **Corregido** | `evolucion desnutricion_cronica "Huancavelica" --elegir 1 --anio 2020` y `"Perú" --hasta 2020`: «No podemos decir cómo cambió hasta 2020: en 2020 la encuesta se hizo en parte por teléfono por la pandemia, y 2020 no se compara con otros años», solo la cifra de 2020 (32,4 % y 12,1 %). `--desde 2020`: «…Empezamos en 2021» |
| A-H2 (alto) | **Corregido con observación** | `evolucion gasto_publico "Perú"` (y `--desde 2023`): «Datos de: Gasto MEF 2023–2025», 2025 (S/ 2 455,9 M) y 2023 (S/ 2 179,2 M). La capa 1 ya no dice cómo cambió y la tarjeta de 2023 dice «Otro año: no se compara con la cifra clave», sin el porqué (N-1) |
| A-H3 (alto) | **Corregido** | «…2015. Fuente: Pregunta al Perú, cálculo propio con ENDES 2015 (INEI); el INEI publicó 43,5 %»; desnutrición «…el INEI publicó 14,4 %». Las que coinciden siguen atribuidas al INEI (11,5 % 2021; 12,1 % 2020) |
| A-H4 (medio) | **Corregido** | «Territorio: Lima Región y Callao»; «sin diferencia estadísticamente clara» (z = −1,03, p = 0,30). Resto bajo: «No permite concluir… para Lima Región» nombra uno solo |
| A-H5 (medio) | **Corregido** | «Puno es el departamento con la anemia… más alta, con diferencia estadísticamente clara frente a los demás» (p ≤ 0,019); «Territorio: todos los departamentos del país» |
| A-H6 (bajo) | **No corregido** (bajo) | `evolucion anemia "Perú" --hasta 2024` sigue «no se puede»; el texto dice «la cifra de 2024…, la más reciente» (N-2) |
| A-H7 (bajo) | **Corregido en parte** | Sin «de de»; «todo el país»; Mapa sin año repetido. Sigue «alrededor de 8 % (entre 7,8 % y 8,6 %)» |
| A-H8 (bajo) | **No corregido** (bajo; pedido explícito) | `nivel_actual --indicador endes_anemia_6_35m "Perú"` → «43,4 %… (forma de medir anterior a 2024)» sin la vigente al lado |

### Cifras verificadas de nuevo

Iguales a la primera revisión: ENDES anemia vigente 2025 Perú 34,9, Puno 56,1, Apurímac 40,6 (p = 0,568); desnutrición Huancavelica 34,0 → 20,3 (p = 3,3e-05), Perú 2021 → 2025 11,5 → 12,1 (p = 0,207); ENAHO Perú 27,6 → 25,7 (p = 0,0077), grupo 1 INEI 2025 (7 departamentos, 35,7–39,8); SIEN Ayaviri 9,5, San Juan de Lurigancho 8,2, coberturas de Puno 39,8–50,5, Apurímac 60,2–65,8 y Lima Metropolitana 30,3–37,7; Mapa 2018 grupo robusto 1 y Ayaviri 23,3–42,3. Nuevas por C-05: gasto ex-PAN 2023 Perú S/ 2 179,2 M = cubo 2 179 204 678 = G-07; Apurímac 2023 S/ 83,1 M = cubo 83 091 061. 2020 sin comparación: desnutrición Perú 12,1 % = DOR-DCI-2020-PE; Huancavelica 32,4 % = cubo 32,442.

### Hallazgos nuevos

**N-1 — Medio. La evolución del gasto ya no responde «¿cómo cambió?» ni explica por qué.** `evolucion gasto_publico "Perú"` (y `"Apurímac"`): la capa 1 da solo 2025 y 2023 va en una tarjeta «Otro año: no se compara con la cifra clave». La causa es legítima: R-GASTO-12 bloquea la comparación (`bloqueos_cruce`: `serie_sin_deflactar`, años [2023, 2025]) y la plantilla la respeta (`plantillas.py:531`); ninguna cifra queda mal. Pero el motivo no llega al usuario (`avisos` vacío). Propuesta: mostrar el motivo de R-GASTO-12 en la capa 1 o el «Ojo al leer» («No comparamos montos de 2023 y 2025 porque están en soles de cada año, sin descontar la inflación»); llevar al dueño (tipo C) si la serie 2023–2025 debe mostrarse en soles constantes.

**N-2 — Bajo.** `evolucion anemia "Perú" --hasta 2024`: dice que 2024 es «la más reciente», pero hay 2025.

**N-3 — Bajo.** Comparación: «No permite concluir… para Lima Región» nombra solo uno de los dos lugares.
