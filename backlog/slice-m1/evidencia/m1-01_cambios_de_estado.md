# M1-01 — Cambios de estado por C-M0-11-2 (medir, informar y aplicar)

12/11/2026, Mac. Permiso del dueño (L6): cuando el cambio afecta solo el estado de publicación, «Medir, informar y aplicar».

## Qué cambia

Los límites de precisión de **R-ENC-03** (coeficiente de variación) y **R-ENC-04** (intervalo en proporciones cerca de 0 % o 100 %) se aplican también con **25 a 49 casos**. Antes solo corrían desde 50 casos; entre 25 y 49 casos la cifra quedaba «referencial» por R-ENC-02 y nada más. Los umbrales de R-ENC-02 no cambian (menos de 25 casos suprime; de 25 a 49 marca referencial). El código ya no compara con `n_min_publicar` (50) sino con `n_min_suprimir` (25).

Además se agrega **R-ENC-19** (no respuesta del ítem: más de 5 % avisa, más de 20 % hace la cifra referencial) y se enciende `compuertas.paso_no_respuesta_activo`.

## Qué se midió (antes de aplicar)

Script: `m1-01_medir_estados.py`. Mide cada fila por el camino del validador (etapas 0–7, sin degradar) y, para las recetas, por plan → ejecutor → compuertas con los microdatos del Mac.

| Conjunto | Filas | Con 25 ≤ n ≤ 49 | Con n < 25 | Menor n |
|---|---|---|---|---|
| Cubo `010ea965`, filas de encuesta (ENDES: anemia criterio anterior, anemia OMS 2024 y desnutrición crónica, 2015–2025; ENAHO: pobreza monetaria 2024–2025) | 782 | **0** | 0 | 139 |
| Las 90 filas de las recetas (ENDES 2024) | 90 | **0** | 0 | 266 |

Resultado del antes y el después (`m1-01_estados_antes.csv`, `m1-01_estados_despues.csv`, idénticos byte a byte):

- **Filas que cambian de estado o de reglas disparadas: 0** (lista en `m1-01_cambios_de_estado.csv`, solo con la cabecera).
- Filas que cambian de valor, n, error estándar o CV: 0.
- Estados del cubo (782 filas): 709 publicable, 72 referencial, 1 suprimida, igual antes y después. Estados de las recetas (90 filas): 85 publicable, 5 referencial, igual antes y después.

Por qué no cambia nada: ninguna fila de encuesta del cubo ni de las recetas tiene menos de 139 casos, así que la zona de 25 a 49 casos no tiene filas hoy. Los registros administrativos del cubo con 25 a 49 casos (SIEN, 1 819 filas) no son encuesta y R-ENC-03/04 no se les aplican (`aplica_a`).

R-ENC-19 tampoco mueve nada hoy: el cubo no trae la tasa de no respuesta, y las recetas de M0 no la calculan (la estimación sale con `tasa_no_respuesta = None` en las 90 filas), así que la regla no dispara.

## Qué se aplicó

- `reglas/reglas.json` regenerado con el consolidador (nunca a mano). Huella de reglas que llevan las respuestas: **`14b83c8814a7` → `f4233fd56056`**.
- Las respuestas grabadas de `backlog/slice-2/evidencia/base_estructurada/` y `backlog/slice-3/evidencia/base_api/` se regrabaron cambiando **solo esa huella** (238 archivos, 438 reemplazos; ninguna línea más). Autorizado por el backlog porque nada más cambia: las pruebas que comparan la respuesta completa con esas bases pasan (`test_regresion_q1_q4`, `test_cli_preguntar`, `tests/web`).
- `src/pap/motor/validador/reglas_etapa4.py` (R-ENC-03 y R-ENC-04) y `src/pap/inferencia/compuertas.py` (paso 8).

## Lo que sí cambia, y no es estado de publicación

Las 3 recetas pasan a `verificado` (K-03, visto del dueño). En el camino de las recetas, la **confianza** de las 85 filas publicables deja de ser «baja» (supuesto M0-09 para recetas sin verificar): 21 filas quedan en «alta» (coinciden con su cifra oficial de 2024) y 64 en «media». Las 5 referenciales siguen en «baja». Esto lo decide K-03, no C-M0-11-2; solo afecta al motor nuevo, que corre a la sombra: el cubo y la web no cambian.
