# S1-10 — Documentación y cierre

## Tareas

1. Actualizar:
   - `docs/arquitectura.md`: el flujo nuevo (consulta mínima → resolver → planificador → plantillas → capas);
   - `docs/guia_de_operacion.md`: cómo preguntar con la CLI y cómo leer una aclaración;
   - `docs/especificaciones/contrato_respuesta.md`: agregar los tipos `no_se_puede` y `aclaracion`;
   - `docs/estado.md` y `docs/hoja_de_ruta.md` (fase 5a hecha);
   - `README.md` (estado y estructura).
2. Archivar `tests/fixtures/consultas_piloto/q*.yaml` en `tests/fixtures/consultas_piloto/` (la regresión usa las consultas mínimas) y actualizar `tests/test_respuesta_p3.py`, que hoy lee `tests/fixtures/consultas_piloto/{q}.yaml`: apuntarlo a las consultas mínimas o a la carpeta archivada.
3. Si durante el slice el dueño tomó alguna decisión (X-02, X-03, X-04 u otra), editar su fila en `docs/decisiones.md`; nunca agregar filas que aclaren otras.
4. Marcar todas las historias como hechas en `README.md` del slice, fusionar `slice-1` a `main` y etiquetar `slice-1-cerrado` (no `slice-1`, para no chocar con el nombre de la rama). Nota del 4/11/2026: esa rama y esa etiqueta son de la carpeta de trabajo anterior y no existen en este repositorio (`docs/historia.md`).
5. Escribir en `backlog/slice-1/evidencia/cierre.md`, en una página: qué puede hacer ahora el usuario, qué quedó fuera, los supuestos aplicados que el dueño debe revisar, las consultas abiertas y qué aprendimos para detallar el slice 2 (lo que pide `agents.md` §9).

## Criterios de aceptación

- [ ] La definición de hecho del slice se cumple punto por punto, con enlace a su evidencia.
- [ ] `uv run pytest -q` en verde en `main` tras la fusión.
