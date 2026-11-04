# S3-10 — Revisión independiente en el celular

## Tareas

1. **Revisor de usuario:** un subagente nuevo, con su encargo en `evidencia/encargo_s3-10.md`. No ve el código de la web ni el backlog.
   - Usa la web con Playwright a 360 px, con los perfiles de las revisiones anteriores.
   - Hace 20 preguntas propias: 10 por texto (**en vivo**, porque no tienen grabación, con tope de costo) y 10 por el formulario.
   - Toma capturas.
   - Preguntas que guían la revisión: ¿Entiende qué se le respondió? ¿Encuentra la fuente? ¿Entiende la confianza sin color? ¿Sabe qué hacer con una aclaración o con un «no se puede»? ¿Algo lo lleva a una conclusión falsa?
2. **Informe** `evidencia/revision_usuario_s3.md`, con hallazgos por severidad y capturas. Los altos y bloqueantes se corrigen y se verifican de nuevo.
3. **Preguntas que fallen:** se agregan al conjunto de evaluación del slice 2, con su resultado esperado y su grabación.
4. **Supervisor:** corre las pruebas `navegador` si el agente no pudo (S3-06).

## Criterios de aceptación

- [ ] «Apto» o «apto con observaciones», sin altos abiertos.
