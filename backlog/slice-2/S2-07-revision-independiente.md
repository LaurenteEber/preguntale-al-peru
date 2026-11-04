# S2-07 — Revisión independiente temprana

## Por qué

En el slice 1, los revisores encontraron lo que las pruebas no cubrían (lección 3 del cierre). Aquí el riesgo nuevo es **una respuesta correcta a una pregunta que la persona no hizo.** Por eso se revisa en cuanto existe la CLI.

## Tareas

1. **Dos revisores**, subagentes nuevos, con sus encargos en `evidencia/encargo_s2-07_*.md`. Ninguno ve el prompt, el código del intérprete ni el conjunto de evaluación.
   - **Usuario:** escribe 20 preguntas propias, con los perfiles de la revisión del slice 1, y lee las respuestas. ¿«Entendimos» dice lo que preguntó? ¿Se entienden las aclaraciones y los mensajes? ¿Confunde algún «no se puede»?
   - **Adversario:** escribe 15 preguntas para hacerlo fallar y busca valores sin ancla y números que no vengan del cubo, según la métrica de la definición de hecho.
2. **Corrida en vivo** con el modelo provisional y el tope por corrida. Se graban todas.
3. **Lo que falle** entra al conjunto de evaluación como entrada nueva, con su categoría, y se anota en `cambios_prompt.md` como categoría, sin la pregunta.
4. **Informes:** `evidencia/revision_usuario_s2.md` y `evidencia/revision_adversaria_s2.md`, con hallazgos y severidad. Los altos se corrigen y se verifican de nuevo.

## Criterios de aceptación

- [ ] Los dos dan «apto» o «apto con observaciones», sin altos abiertos.
- [ ] Las preguntas que fallaron están en el conjunto con su resultado esperado.
