# Cambios del prompt del intérprete

Cada cambio de `curados/interprete/prompt.md`, `ejemplos.yaml`, `intenciones_descripcion.yaml` o del vocabulario que entra al
prompt queda aquí, con la categoría del conjunto de evaluación que lo motivó (sin usar el conjunto para ajustar: README del
slice). La versión es la huella del prompt ya armado (`pap.interprete.prompt.armar`).

| Versión | Fecha | Huella | Qué cambió | Por qué (categoría) |
|---|---|---|---|---|
| 1 | 4/11/2026 | `sha256:cbd2df7823d63e4d177cea5842210e2f59cdb552bd2d89b6fb7514093e3187c8` | Primera versión (S2-03): temas, intenciones, lugares, reglas, 16 ejemplos y esquema | — |
| 2 | 4/11/2026 | `sha256:b07343d166e2915bf6330b94da4f96d0f89319a120a71cdee6640f81837160ca` | Cambia el ejemplo «¿cuánta anemia hay?» por «¿y cuánta desnutrición hay?» | Coincidía con una pregunta del conjunto (lo detectó la prueba de cruce de S2-03; no se miró el resto del conjunto) |
| 3 | 5/11/2026 | `sha256:8c92924a415154002a747e25666735adeb1fe807d9780d448038a46d6f9fd3cb` | Regla nueva: en `efecto` y `cruce`, si se nombra un problema que no es la anemia, el tema es ese problema (el gasto conocido es el que va contra la anemia) | Revisión de usuario de S2-07, categoría «reformulada» (efecto del gasto sobre otro problema) |
| 4 | 5/11/2026 | `sha256:56e8abc26bea4831e41cf36ef3a689e1de78a49952ee5884322df32d7049dfbf` | Cinco reglas: copiar la palabra del nivel junto al lugar y no el artículo (salvo que sea parte del nombre); «¿cómo está…?» es `nivel_actual` y «¿cuánto bajó…?» es `evolucion`; «lo gastado y si sirvió» es una sola pregunta de `efecto`; un lugar sin tema va sin `tema`; un pedido de otra tarea es `fuera_de_alcance` de tipo pregunta | Ronda 1 de S2-09, por categoría (sin copiar preguntas): lugares_dificiles, directa y reformulada (artículos y nivel), reformulada (cómo está), q1_q4 y directa (gasto y efecto), ambigua (lugar sin tema), inyeccion (otra tarea) |
