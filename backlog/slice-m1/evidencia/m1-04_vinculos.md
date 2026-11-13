# M1-04 — Cuántas variables se vinculan sin LLM (tarea 3)

Generado el 2026-11-13 por `pap cuestionarios informe`. **Hipótesis de `tecnologias.md` §6:** en la ENDES los códigos no siguen el número de pregunta, así que el diccionario y las expresiones regulares vinculan poco y el resto lo propone Sonnet fuera de línea. Se midió antes de usar el LLM.

## Las tres tablas pedidas

| Tabla | Variables | Por diccionario | Por regla del código | Sin pregunta (administrativa o construida) | Quedan para el LLM | Por LLM |
|---|---|---|---|---|---|---|
| REC0111 | 103 | 0 (0.0 %) | 1 (1.0 %) | 32 | 70 | no corrido |
| REC43 | 168 | 0 (0.0 %) | 0 (0.0 %) | 3 | 165 | no corrido |
| RECH6 | 43 | 0 (0.0 %) | 0 (0.0 %) | 7 | 36 | no corrido |

## Las variables de las 3 recetas

Variables que usan las recetas (indicador, universo, universo analítico, diseño muestral y cortes permitidos): `RECH0.HV005`, `RECH0.HV021`, `RECH0.HV022`, `RECH0.HV024`, `RECH0.HV025`, `RECH1.HV103`, `RECH23.HV270`, `RECH23.SHREGION`, `RECH6.HC1`, `RECH6.HC27`, `RECH6.HC55`, `RECH6.HC57`, `RECH6.HC57A`, `RECH6.HC70`.

| Tabla | Variables | Por diccionario | Por regla del código | Sin pregunta (administrativa o construida) | Quedan para el LLM | Por LLM |
|---|---|---|---|---|---|---|
| RECH0 | 5 | 0 (0.0 %) | 0 (0.0 %) | 4 | 1 | no corrido |
| RECH1 | 1 | 0 (0.0 %) | 0 (0.0 %) | 0 | 1 | no corrido |
| RECH23 | 2 | 0 (0.0 %) | 0 (0.0 %) | 2 | 0 | no corrido |
| RECH6 | 6 | 0 (0.0 %) | 0 (0.0 %) | 0 | 6 | no corrido |

En conjunto: 14 variables; 0 vinculadas sin LLM; 6 sin pregunta por ser administrativas o construidas; 8 esperan al LLM. **Meta (≥ 95 % con su texto vinculado): no se puede decir que se cumple** hasta correr el lote.

## Las 34 tablas

| Tabla | Variables | Por diccionario | Por regla del código | Sin pregunta (administrativa o construida) | Quedan para el LLM | Por LLM |
|---|---|---|---|---|---|---|
| CSALUD01 | 258 | 0 (0.0 %) | 230 (89.1 %) | 5 | 23 | no corrido |
| CSALUD08 | 53 | 0 (0.0 %) | 47 (88.7 %) | 5 | 1 | no corrido |
| DIT | 63 | 0 (0.0 %) | 0 (0.0 %) | 4 | 59 | no corrido |
| PS_BECA18 | 10 | 0 (0.0 %) | 0 (0.0 %) | 6 | 4 | no corrido |
| PS_COMEDOR | 10 | 0 (0.0 %) | 0 (0.0 %) | 6 | 4 | no corrido |
| PS_PENSION65 | 10 | 0 (0.0 %) | 0 (0.0 %) | 6 | 4 | no corrido |
| PS_QALIWARMA | 11 | 0 (0.0 %) | 0 (0.0 %) | 6 | 5 | no corrido |
| PS_TRABAJA | 10 | 0 (0.0 %) | 0 (0.0 %) | 6 | 4 | no corrido |
| PS_VL | 10 | 0 (0.0 %) | 0 (0.0 %) | 6 | 4 | no corrido |
| PS_WAWAWASI | 10 | 0 (0.0 %) | 0 (0.0 %) | 6 | 4 | no corrido |
| Programas_Sociales_x_Hogar | 20 | 0 (0.0 %) | 0 (0.0 %) | 5 | 15 | no corrido |
| RE223132 | 149 | 0 (0.0 %) | 0 (0.0 %) | 8 | 141 | no corrido |
| RE516171 | 82 | 0 (0.0 %) | 0 (0.0 %) | 3 | 79 | no corrido |
| RE758081 | 198 | 0 (0.0 %) | 0 (0.0 %) | 2 | 196 | no corrido |
| REC0111 | 103 | 0 (0.0 %) | 1 (1.0 %) | 32 | 70 | no corrido |
| REC21 | 33 | 0 (0.0 %) | 0 (0.0 %) | 7 | 26 | no corrido |
| REC41 | 147 | 0 (0.0 %) | 0 (0.0 %) | 3 | 144 | no corrido |
| REC42 | 169 | 0 (0.0 %) | 0 (0.0 %) | 2 | 167 | no corrido |
| REC43 | 168 | 0 (0.0 %) | 0 (0.0 %) | 3 | 165 | no corrido |
| REC44 | 34 | 0 (0.0 %) | 0 (0.0 %) | 4 | 30 | no corrido |
| REC82 | 4 | 0 (0.0 %) | 0 (0.0 %) | 2 | 2 | no corrido |
| REC83 | 19 | 0 (0.0 %) | 0 (0.0 %) | 4 | 15 | no corrido |
| REC84DV | 218 | 0 (0.0 %) | 0 (0.0 %) | 2 | 216 | no corrido |
| REC91 | 343 | 0 (0.0 %) | 4 (1.2 %) | 3 | 336 | no corrido |
| REC93DVdisciplina | 18 | 0 (0.0 %) | 15 (83.3 %) | 2 | 1 | no corrido |
| REC94 | 61 | 0 (0.0 %) | 0 (0.0 %) | 2 | 59 | no corrido |
| REC95 | 299 | 0 (0.0 %) | 22 (7.4 %) | 2 | 275 | no corrido |
| RECH0 | 44 | 0 (0.0 %) | 0 (0.0 %) | 16 | 28 | no corrido |
| RECH1 | 36 | 0 (0.0 %) | 0 (0.0 %) | 5 | 31 | no corrido |
| RECH23 | 130 | 0 (0.0 %) | 0 (0.0 %) | 7 | 123 | no corrido |
| RECH4 | 21 | 0 (0.0 %) | 0 (0.0 %) | 3 | 18 | no corrido |
| RECH5 | 40 | 0 (0.0 %) | 0 (0.0 %) | 5 | 35 | no corrido |
| RECH6 | 43 | 0 (0.0 %) | 0 (0.0 %) | 7 | 36 | no corrido |
| RECHM | 8 | 0 (0.0 %) | 0 (0.0 %) | 3 | 5 | no corrido |

Total: 2832 variables; por diccionario 0; por regla 319 (11.3 %); sin pregunta 188; para el LLM 2325.

## ¿Están las preguntas correctas entre las candidatas que verá el LLM?

Con las 319 variables vinculadas por regla (su pregunta se conoce) se probó el recorte a 20 candidatas por palabras en común: la pregunta correcta está entre ellas en 289 (90.6 %). Es un piso para el LLM: nunca podrá acertar una pregunta que no le llegue. No es una cifra de acierto del LLM.
