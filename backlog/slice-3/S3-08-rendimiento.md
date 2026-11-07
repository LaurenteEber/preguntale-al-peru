# S3-08 — Rendimiento

**Objetivo:** sin LLM, p95 < 2 s (`plan_slices.md`). Con texto libre, la latencia medida en S2-09 más 1 s y como máximo 10 s, como `supuesto: S3-08`.

## Tareas

1. **Medición** (`tests/web/medir.py`, comando aparte, fuera de pytest):
   - con el servicio precalentado, 200 respuestas por la vía estructurada: la matriz reducida repetida en orden aleatorio, con semilla fija;
   - el conjunto de evaluación por texto con grabaciones, que mide sin el LLM;
   - una corrida en vivo con tope de costo.

   Se informan p50, p95 y máximo, separando intérprete, motor y página.
2. **Objetivos** en `curados/web/parametros.yaml`: el de `plan_slices.md` con `decision:` y el del texto libre con `supuesto: S3-08`.
3. **Si no se cumplen**, en este orden:
   1. caché en memoria de respuestas, con clave = consulta mínima (o texto limpio) + `elegir` + versión de la biblioteca;
   2. más consultas de precalentamiento.

   No se cambia el motor ni el cubo; si hiciera falta, es una consulta al dueño.
4. **Arranque:** cuánto tarda en estar `ok` (supuesto: ≤ 30 s).

## Criterios de aceptación

- [x] `evidencia/s3-08_rendimiento.md` con la tabla y los objetivos cumplidos.
- [x] (No aplica: no hizo falta caché.) Si hay caché, una prueba de que la respuesta de la caché es igual a una recién calculada.
