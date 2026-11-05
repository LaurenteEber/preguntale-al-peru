# S3-11 — Documentación y cierre

## Tareas

1. **Pruebas finales:**
   - `pytest` (con `navegador` si el entorno puede);
   - regresión Q1–Q4;
   - matriz reducida;
   - equivalencia web;
   - medición de S3-08.
2. **Documentos:**
   - `docs/manual_de_uso.md`: la web (abrirla en local y en el celular, cómo leer cada bloque) y el formulario guiado.
   - `docs/guia_de_operacion.md`: `pap servir`, imagen, variables de entorno, límites y cómo comprobar que no se registra la pregunta.
   - `docs/arquitectura.md`: el servicio, el precalentamiento, el candado y la frontera con el motor.
   - `docs/especificaciones/api.md` (S3-03) y `contrato_respuesta.md`: rótulos en YAML, `url` de la cita y la web como presentación del JSON. Corregir que «¿Qué puedo hacer?» está en la capa 1, como ya está en el JSON.
   - `docs/estado.md`: fase 5c hecha.
   - `backlog/plan_slices.md`: slice 3 hecho; ajustar el slice 4 con:
     - despliegue, dominio y HTTPS;
     - contadores fuera de memoria;
     - candado y LLM con varios usuarios;
     - la revisión de P-03 (nombres de personas en las preguntas);
     - X-05 y X-07 antes de que entre gente de fuera.
3. **`evidencia/cierre.md`**, según `agents.md` §9:
   - tiempos;
   - peso de las páginas;
   - accesibilidad;
   - supuestos `S3-xx`;
   - consultas abiertas;
   - lecciones para el slice 4.
4. **Cierre:**
   - historias marcadas;
   - fusión o PR;
   - etiqueta `slice-3-cerrado`;
   - push sin `--force`.

## Criterios de aceptación

- [ ] Definición de hecho del slice cumplida punto por punto, con enlace a la evidencia.
- [ ] `pytest` en verde en `main` tras la fusión.
