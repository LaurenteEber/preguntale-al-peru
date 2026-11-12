# M1-20 — Revisión independiente y cierre

## Tareas

1. **Revisión independiente por partes,** una por historia con código, con las lentes de riesgo, confiabilidad y seguridad → `evidencia/revision_por_partes.md`. En seguridad: cadenas maliciosas en la pregunta y en cada campo que devuelve el LLM; ningún camino ejecuta SQL fuera de `ejecutar_select`; ningún registro guarda el texto de la pregunta.
2. **Regresión completa:** suite, `regresion_microdatos`, las 90 filas, las doradas nuevas, Q1–Q4 y la matriz.
3. **Seguridad:** `just auditar`, gitleaks sobre todo el historial y `pip-audit`.
4. **Respaldo:** bloque `endes-2024` al día en el repo privado, con la restauración probada.
5. **Documentación:** `docs/diseno/motor_inferencia.md` y `fichas.md` al día con lo construido, `docs/estado.md`, `docs/hoja_de_ruta.md`, `docs/especificaciones/` (motor, intérprete, contrato, stack) y `backlog/plan_slices.md`.
6. **Cierre** → `evidencia/cierre.md`: definición de hecho punto por punto, supuestos aplicados, consultas abiertas y lo aprendido para M2 (tamaños, tiempos, costo del enriquecimiento por variable, qué funcionó del vínculo pregunta–variable).
7. **PR a `main` y etiqueta `slice-m1-cerrado`** cuando el dueño escriba «fusiona».

## Criterios de aceptación

- [ ] La definición de hecho del README, punto por punto, con su evidencia.
- [ ] Sin hallazgos altos abiertos.
- [ ] El cierre separa lo verificado de lo declarado.
