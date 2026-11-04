# S1-14 — Correcciones menores de la revisión

## Tareas

1. **H10:** la aclaración de «Lima» dice «Si no eliges, usamos Lima Metropolitana», pero la CLI sale con código 2 sin responder. Se quita la frase de la aclaración (T-03 sigue fijando Lima Metropolitana como valor por defecto para la web del slice 3, en `parametros_motor.yaml`).
2. **N-3:** en una comparación, el «No permite concluir» de la ficha nombra los dos lugares, no solo uno.
3. **H8:** «Sí tenemos la cifra de 2018 para Uchuraccay. Puedes preguntar por cuánto hay ahora» pasa a «Puedes preguntar por la cifra de 2018, la última que hay por distrito» (`curados/motor/textos/no_se_puede.yaml`).
4. **H7 (observación pendiente):** con `--anio 2018` en anemia, la respuesta no debe decir primero «No tenemos datos de anemia de 2018» si después ofrece la forma anterior de 2018. Se ofrece primero la forma que sí tiene ese año.

## Criterios de aceptación

- [ ] Una prueba por punto; textos en `curados/motor/textos/`; corrector sin infracciones.
- [ ] Regresión Q1–Q4 sin cambios (ninguno de estos casos está en Q1–Q4).
