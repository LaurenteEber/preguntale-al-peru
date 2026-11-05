# Hoja de ruta

## Fases

| Fase | Qué | Estado |
|---|---|---|
| 0 | Diseño: idea, fases, catálogo de fuentes | hecho |
| 1 | Catálogo v2: esquema, correcciones trazables, prueba de humo, priorización por olas | hecho (5/10/2026) |
| 2 | Reglas de publicación y atribución v1.1, probadas con 12 preguntas y auditadas | hecho (7/10/2026) |
| 3 | Capa 0 de la biblioteca (territorio, población, gasto, salud), auditada | hecho (7/10/2026) |
| 4 | Piloto de punta a punta (anemia, desnutrición, gasto ex-PAN, pobreza): cubo, validador de 68 reglas, respuesta por capas | cerrado (13/10/2026) |
| 5a | Motor por intenciones (slice 1) | hecho (3/11/2026); adenda cerrada (4/11/2026) |
| 5b | Intérprete de preguntas en lenguaje natural (slice 2) | hecho (5/11/2026) |
| 5c | API y web mínima (slice 3) | en curso |
| — | Beta cerrada (slice 4) y Ola 1 de datos (slice 5) | pendiente |

El detalle de cada slice: [../backlog/plan_slices.md](../backlog/plan_slices.md). El estado al día: [estado.md](estado.md).

## Cómo se trabaja

Un slice es un corte vertical: al terminarlo, el usuario puede hacer algo que antes no podía, con sus pruebas. Solo se detalla el slice en curso. Cada slice tiene su rama, su backlog en `backlog/slice-N/`, su evidencia y una revisión independiente antes de cerrarse. Reglas del agente implementador: [../agents.md](../agents.md).
