# M1-04 — Cuestionarios y diccionarios de la ENDES 2024 (extracción)

Generado el 2026-11-12 por `pap cuestionarios informe`. Los textos salen de los PDF oficiales registrados (`endes-2024-cuestionario-*` y los «Diccionario - <tabla>.pdf» dentro de cada ZIP), leídos con `pdfplumber` en el lector aislado (tiempo y memoria acotados). Todo queda en `propuesto`.

## Cuestionario hogar: 68 preguntas y 5 páginas de matriz (columnas del listado, no separables)

| Sección | Preguntas |
|---|---|
| SECCIÓN 1. CARACTERÍSTICAS DE LOS MIEMBROS DEL HOGAR | 2 |
| SECCIÓN 2. CARACTERÍSTICAS DE LA VIVIENDA | 28 |
| SECCIÓN 3A. PROGRAMAS SOCIALES - NO ALIMENTARIOS | 11 |
| SECCIÓN 3.B PROGRAMAS SOCIALES - ALIMENTARIOS | 11 |
| SECCIÓN 5. PRUEBA DE HEMOGLOBINA | 2 |
| SECCIÓN 6. PRUEBA DE YODO EN LA SAL Y DE CLORO RESIDUAL EN EL AGUA | 10 |
| SECCIÓN 8. ENTREGA DE INCENTIVOS | 4 |

## Cuestionario individual: 500 preguntas y 2 páginas de matriz (columnas del listado, no separables)

| Sección | Preguntas |
|---|---|
| SECCIÓN 1. ANTECEDENTES DE LA ENTREVISTADA | 22 |
| SECCIÓN 2. REPRODUCCIÓN | 41 |
| SECCIÓN 3. ANTICONCEPCIÓN | 50 |
| SECCIÓN 4A. EMBARAZO, PARTO, PUERPERIO Y LACTANCIA | 90 |
| SECCIÓN 4B. INMUNIZACIÓN Y SALUD | 153 |
| SECCIÓN 5. NUPCIALIDAD | 36 |
| SECCIÓN 6. PREFERENCIAS DE FECUNDIDAD | 26 |
| SECCIÓN 7. ANTECEDENTES DEL CÓNYUGE Y TRABAJO DE LA MUJER | 23 |
| SECCIÓN 8. SIDA Y OTRAS I.T.S. | 40 |
| SECCIÓN 9: MORTALIDAD MATERNA | 17 |
| SECCIÓN 10. VIOLENCIA DOMÉSTICA | 2 |

## Cuestionario salud: 190 preguntas

| Sección | Preguntas |
|---|---|
| (sin sección) | 13 |
| SECCIÓN 1. HIPERTENSIÓN Y DIABETES | 12 |
| SECCIÓN 2. FACTORES DE RIESGO DE ENFERMEDADES NO TRASMISIBLES | 21 |
| SECCIÓN 3. SALUD OCULAR Y BUCAL EN ADULTOS | 10 |
| SECCIÓN 4. PREVENCIÓN Y CONTROL DE CÁNCER | 20 |
| SECCIÓN 5. TUBERCULOSIS | 9 |
| SECCIÓN 6. VIH / SIDA | 12 |
| SECCIÓN 7. SALUD MENTAL | 33 |
| SECCIÓN 8. SALUD BUCAL, OCULAR Y MENTAL EN NIÑAS Y NIÑOS | 45 |
| SECCIÓN 9. MEDICIONES DE ANTROPOMETRÍA Y PRESIÓN ARTERIAL | 15 |

## Diccionarios por tabla frente al índice de variables

| Tabla | Variables en el índice | En el diccionario | Sin diccionario | Cuáles |
|---|---|---|---|---|
| CSALUD01 | 258 | 258 | 0 |  |
| CSALUD08 | 53 | 53 | 0 |  |
| DIT | 64 | 63 | 1 | HHID |
| PS_BECA18 | 10 | 10 | 0 |  |
| PS_COMEDOR | 10 | 10 | 0 |  |
| PS_PENSION65 | 10 | 10 | 0 |  |
| PS_QALIWARMA | 11 | 11 | 0 |  |
| PS_TRABAJA | 10 | 10 | 0 |  |
| PS_VL | 10 | 10 | 0 |  |
| PS_WAWAWASI | 10 | 10 | 0 |  |
| Programas_Sociales_x_Hogar | 20 | 20 | 0 |  |
| RE223132 | 150 | 149 | 1 | HHID |
| RE516171 | 85 | 82 | 3 | HHID, V704, V716 |
| RE758081 | 199 | 198 | 1 | HHID |
| REC0111 | 104 | 103 | 1 | V160 |
| REC21 | 35 | 33 | 2 | BEDAD, HHID |
| REC41 | 148 | 147 | 1 | HHID |
| REC42 | 170 | 169 | 1 | HHID |
| REC43 | 169 | 168 | 1 | HHID |
| REC44 | 35 | 34 | 1 | HHID |
| REC82 | 5 | 4 | 1 | HHID |
| REC83 | 20 | 19 | 1 | HHID |
| REC84DV | 221 | 218 | 3 | D103E, D105N, HHID |
| REC91 | 344 | 343 | 1 | HHID |
| REC93DVdisciplina | 19 | 18 | 1 | HHID |
| REC94 | 62 | 61 | 1 | HHID |
| REC95 | 301 | 299 | 2 | HHID, Q465EC_A9 |
| RECH0 | 44 | 44 | 1 | NCONGLOME1 |
| RECH1 | 36 | 36 | 0 |  |
| RECH23 | 130 | 130 | 0 |  |
| RECH4 | 22 | 21 | 2 | SH11B, SH11C |
| RECH5 | 40 | 40 | 0 |  |
| RECH6 | 43 | 43 | 0 |  |
| RECHM | 8 | 8 | 0 |  |

Total: 2856 variables en el índice, 2832 en los diccionarios, 26 del índice sin entrada de diccionario (columnas derivadas por el almacén, como `HHID`, y algunas que el INEI no documenta).

## Límites de esta extracción (para quien revise)

- El diseño de los PDF cambia entre cuestionarios y páginas; el lector se guía por la posición de las palabras (valores en `cuestionarios.*` de `curados/inferencia/parametros.yaml`). Las **opciones** de respuesta pueden traer ruido (por ejemplo un «(PASE A 413)» como si fuera una opción) y los **saltos** solo valen si nombran una pregunta que existe en el mismo cuestionario.
- Las **matrices** (las columnas «(1) (2) …» del listado del hogar y tablas parecidas) no se separan en preguntas: cada página es una sola entrada de tipo `matriz` con su encabezado. Los vínculos de esas variables serán a nivel de página.
- Si una pregunta aparece en varias páginas (la misma tabla para la 1.ª, 2.ª y 3.ª persona) queda una vez, con el texto más largo.
- En el hogar, la sección 4 (peso y talla) y casi toda la 5 (hemoglobina) son formularios de tabla, sin el encabezado de preguntas: dan pocas o ninguna pregunta. Ahí están las mediciones de los niños (HC53 a HC57A, HC70…) que usan las recetas; su vínculo, si lo hay, será a las pocas preguntas extraídas o `sin_pregunta` con su motivo. No se corrigió a mano (AGENTS.md §7).
- Todo queda en `propuesto`; el visto es de M1-07.
