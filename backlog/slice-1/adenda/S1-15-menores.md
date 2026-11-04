# S1-15 — Correcciones menores de la revisión

H8 y H10 ya están corregidas: la revisión las dio por cerradas y se comprobó de nuevo el 4/11/2026 (`../evidencia/revision_usuario.md`, «Estado de los hallazgos»). Quedan dos.

## Tareas

1. **N-3:** en una comparación, el «No permite concluir» de la ficha nombra solo uno de los dos lugares.
   - Hoy (4/11/2026), `--intencion comparacion --tema anemia --territorio "Lima Metropolitana" --comparar-con "Lima Región"` dice «…con suficiente precisión para Lima Metropolitana».
   - El texto viene del código NC-NIVEL (`reglas/reglas.json`), con el lugar que pone `nc_respaldo` en `src/pap/motor/plantillas.py`, que hoy toma solo la primera cifra. El formato del límite está en `curados/motor/parametros_motor.yaml` (entrada marcada `decision:`, que no se cambia).
   - En una comparación se unen los dos lugares con « y »: «…con suficiente precisión para Lima Metropolitana y Lima Región».
   - Si las dos cifras tienen límites de nivel distintos, va un «No permite concluir» por lugar.
2. **H7 (observación pendiente):** `--intencion nivel_actual --tema anemia --territorio "Perú" --anio 2018` dice «No hay datos de anemia de 2018 con la forma de medir actual», lo que sugiere que sí hay datos con la anterior, sin decir cómo obtenerlos.
   - E-06 manda que en «¿cuánta hay?» se muestre solo la forma vigente, así que la respuesta sigue siendo «no se puede».
   - Cambia el texto: decir que la cifra de 2018 solo existe con la forma de medir anterior, que se muestra al preguntar cómo cambió la anemia, y ofrecer esa pregunta (la evolución hasta 2018).
   - Con S1-13 (A-H6), esa evolución debe responder.
   - Para años sin ninguna serie (p. ej. 2010) se dice «No hay datos de anemia de 2010», sin «con la forma de medir actual» (N1 de la revisión).

## Criterios de aceptación

- [ ] Una prueba por punto; textos nuevos en `curados/motor/textos/` (N-3 es código, no texto); corrector sin infracciones.
- [ ] Regresión Q1–Q4 sin cambios (ninguno de estos casos está en Q1–Q4).
