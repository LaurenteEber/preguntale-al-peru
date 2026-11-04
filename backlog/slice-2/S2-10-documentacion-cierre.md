# S2-10 — Documentación y cierre

## Tareas

1. **Pruebas finales:**
   - `uv run pytest -q` sin red y sin clave;
   - regresión Q1–Q4;
   - matriz reducida;
   - una evaluación final en vivo: `evidencia/s2-10_evaluacion_final.md`.

   Si la evaluación final baja de algún umbral, se vuelve a S2-09 (una ronda) y, si sigue bajando, consulta al dueño. No se cierra con un umbral incumplido.
2. **Documentos:**
   - `docs/manual_de_uso.md`:
     - «Escribir la pregunta con mis palabras» pasa a hecho, con ejemplos de `--texto`, de aclaraciones y de «Entendimos»;
     - quitar «Sin lenguaje libre»;
     - explicar cómo configurar la clave.
   - `docs/arquitectura.md`: el intérprete, la frontera con el LLM, las anclas y las grabaciones.
   - `docs/guia_de_operacion.md`: grabar, evaluar, ver el uso y el costo, y apagar el intérprete.
   - `docs/especificaciones/`: el contrato de la interpretación y lo de S2-06.
   - `docs/estado.md`: fase 5b hecha y la deuda nueva.
   - `backlog/plan_slices.md`: slice 2 hecho; ajustar el esbozo del slice 3 con lo medido (latencia del LLM frente a < 2 s; nombres de personas, de X-14).
3. **`evidencia/cierre.md`**, según `agents.md` §9:
   - costo medido por pregunta y proyección para 1 000 preguntas al mes;
   - supuestos `S2-xx`;
   - consultas abiertas;
   - lecciones para el slice 3.
4. **Cierre:**
   - historias marcadas en el README;
   - fusión de `slice-2` en `main` (PR si la nube no puede subir a `main`);
   - etiqueta `slice-2-cerrado`;
   - push sin `--force`.

## Criterios de aceptación

- [ ] La definición de hecho del slice está cumplida punto por punto, con enlace a la evidencia.
- [ ] `pytest` en verde en `main` tras la fusión (`evidencia/pytest_main.txt`).
- [ ] Ningún documento vigente dice «sin LLM» o «sin lenguaje libre» como estado actual.
