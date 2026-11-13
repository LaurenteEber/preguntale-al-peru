# M1-04 — Coherencia entre variables hermanas de REC43 (sin LLM)

Generado por `m1-04_coherencia.py` con `vinculos.parquet`, `vinculos_llm.parquet` y `curados/inferencia/vinculos_manuales.yaml`. Familia = variables con el mismo prefijo (letras + número: H12A, H12B… → H12); solo las de 3 o más. **18 familias; 8 marcadas** (3 con preguntas distintas, 6 con miembros vinculados y otros no). Una marca no es un error: es lo que hay que mirar.

| Familia | Miembros | Vinculados | Preguntas a las que apuntan | Marca |
|---|---|---|---|---|
| H0 | 4 | 0 | — | coherente |
| H2 | 4 | 1 | individual:459 ×1 | incompleta |
| H3 | 4 | 0 | — | coherente |
| H4 | 4 | 0 | — | coherente |
| H5 | 4 | 0 | — | coherente |
| H6 | 4 | 0 | — | coherente |
| H7 | 4 | 0 | — | coherente |
| H8 | 4 | 0 | — | coherente |
| H9 | 4 | 0 | — | coherente |
| H12 | 26 | 17 | individual:474A ×17 | incompleta |
| H15 | 14 | 14 | individual:473D ×14 | coherente |
| H31 | 5 | 5 | individual:468 ×1, individual:468A ×1, individual:468B ×1, individual:469A ×1, individual:469B ×1 | mezcla |
| H32 | 26 | 16 | individual:469D ×16 | incompleta |
| H33 | 4 | 3 | individual:456X ×2, individual:465 ×1 | mezcla, incompleta |
| H36 | 6 | 0 | — | coherente |
| H37 | 19 | 13 | individual:471B ×13 | incompleta |
| H40 | 4 | 2 | individual:456X ×2 | incompleta |
| H44 | 3 | 3 | individual:474C ×1, individual:474D ×1, individual:475B ×1 | mezcla |

**Cómo leerlo.** *Incompleta* es la marca que más importa: en una familia de opción múltiple (H12, H32, H37…) todos los miembros deberían apuntar a la misma pregunta, así que los que quedaron «rechazada_por_verificacion» o «no_encontrada» son candidatos a revisar a mano. *Mezcla* es normal cuando la familia es una secuencia de preguntas distintas (H31: tos, respiración, bebidas…; H44: lugar, días, sigue enfermo): ahí lo que se mira es que cada miembro caiga en la pregunta que le toca.


## Detalle de las familias marcadas

### H2 — incompleta

| Variable | Etiqueta | Pregunta | Cómo |
|---|---|---|---|
| H2 | Recibió vacuna BCG | individual:459 | llm |
| H2D | Día Vacuna BCG | — | sin_pregunta (no_encontrada) |
| H2M | Mes Vacuna BCG | — | sin_pregunta (no_encontrada) |
| H2Y | Año Vacuna BCG | — | sin_pregunta (no_encontrada) |

### H12 — incompleta

| Variable | Etiqueta | Pregunta | Cómo |
|---|---|---|---|
| H12A | Busco D97:D148 para la diarrea: hospital MINSA | individual:474A | llm |
| H12B | Busco tratamiento para la diarrea: centro de salud MINSA | individual:474A | llm |
| H12C | Busco tratamiento para la diarrea: puesto de salud MINSA | individual:474A | llm |
| H12D | Busco tratamiento para la diarrea: clínica móvil | — | sin_pregunta (rechazada_por_verificacion) |
| H12E | Busco tratamiento para la diarrea: promotor de salud | — | sin_pregunta (rechazada_por_verificacion) |
| H12F | Busco tratamiento para la diarrea: hospital ESSALUD | individual:474A | llm |
| H12G | Busco tratamiento para la diarrea: hospital FF.AA. - P.N.P. | individual:474A | llm |
| H12H | Busco tratamiento para la diarrea: policlìnico/centro/posta ESSALUD | individual:474A | llm |
| H12I | Busco tratamiento para la diarrea: hospital/otro de la Municipalidad | individual:474A | llm |
| H12J | Busco tratamiento para la diarrea: clínica particular | individual:474A | llm |
| H12K | Busco tratamiento para la diarrea: farmacia/botica | individual:474A | llm |
| H12L | Busco tratamiento para la diarrea: consultorio médico particular | individual:474A | llm |
| H12M | Busco tratamiento para la diarrea: clínica móvil privado | individual:474A | llm |
| H12N | Busco tratamiento para la diarrea: trabajador de la salud | — | sin_pregunta (rechazada_por_verificacion) |
| H12O | Busco tratamiento para la diarrea: botiquín popular | individual:474A | llm |
| H12P | Busco tratamiento para la diarrea: clínica/Posta de ONG | individual:474A | llm |
| H12Q | Busco tratamiento para la diarrea: hospital/Otro de la iglesia | individual:474A | llm |
| H12R | Busco tratamiento para la diarrea: otra | — | sin_pregunta (rechazada_por_verificacion) |
| H12S | Busco tratamiento para la diarrea: comprar | — | sin_pregunta (rechazada_por_verificacion) |
| H12T | Busco tratamiento para la diarrea: curandero | individual:474A | llm |
| H12U | Busco tratamiento para la diarrea: amigo/pariente | — | sin_pregunta (rechazada_por_verificacion) |
| H12V | Busco tratamiento para la diarrea: CS oth.priv sector | individual:474A | llm |
| H12W | Busco tratamiento para la diarrea: CS oth.priv sector | individual:474A | llm |
| H12X | Busco tratamiento para la diarrea: Otro | — | sin_pregunta (rechazada_por_verificacion) |
| H12Y | Busco tratamiento para la diarrea: sin tratamiento | — | sin_pregunta (error_del_lote) |
| H12Z | Busco tratamiento para la diarrea: tratamiento médico | — | sin_pregunta (no_encontrada) |

### H31 — mezcla

| Variable | Etiqueta | Pregunta | Cómo |
|---|---|---|---|
| H31 | Ha tenido tos en las últimas dos semanas | individual:468 | llm |
| H31B | Cuando estuvo enfermo con tos, respiraba más rápido con respiraciones  | individual:468A | llm |
| H31C | La respiración rápida o difícil era por un problema en el pecho o porq | individual:468B | llm |
| H31D | Le dió usted la misma cantidad de bebidas que antes de la fiebre o tos | individual:469A | llm |
| H31E | Le dió la misma cantidad de comida que antes de la fiebre o tos, le di | individual:469B | llm |

### H32 — incompleta

| Variable | Etiqueta | Pregunta | Cómo |
|---|---|---|---|
| H32A | Dónde buscó tratamiento para la Fiebre/tos: Hospital MINSA | individual:469D | llm |
| H32B | Dónde buscó tratamiento para la Fiebre/tos: Centro de salud MINSA | individual:469D | llm |
| H32C | Dónde buscó tratamiento para la Fiebre/tos: Puesto de salud MINSA | individual:469D | llm |
| H32D | Dónde buscó tratamiento para la Fiebre/tos: Clínica móvil | individual:469D | llm |
| H32E | Dónde buscó tratamiento para la Fiebre/tos: Promotor de salud | individual:469D | llm |
| H32F | Dónde buscó tratamiento para la Fiebre/tos: Hospital ESSALUD | individual:469D | llm |
| H32G | Dónde buscó tratamiento para la Fiebre/tos: Hospital FF.A. y PNP. | individual:469D | llm |
| H32H | Dónde buscó tratamiento para la Fiebre/tos: Posta ESSALUD | individual:469D | llm |
| H32I | Dónde buscó tratamiento para la Fiebre/tos: Hospital/otro de la Munici | — | sin_pregunta (rechazada_por_verificacion) |
| H32J | Dónde buscó tratamiento para la Fiebre/tos: Hospital/clínica particula | individual:469D | llm |
| H32K | Dónde buscó tratamiento para la Fiebre/tos: Farmacia/botica | individual:469D | llm |
| H32L | Dónde buscó tratamiento para la Fiebre/tos: Consultorio médico particu | individual:469D | llm |
| H32M | Dónde buscó tratamiento para la Fiebre/tos: Móvil privado | — | sin_pregunta (rechazada_por_verificacion) |
| H32N | Dónde buscó tratamiento para la Fiebre/tos: Trabajador de salud | — | sin_pregunta (rechazada_por_verificacion) |
| H32O | Dónde buscó tratamiento para la Fiebre/tos: Botiquin popular | individual:469D | llm |
| H32P | Dónde buscó tratamiento para la Fiebre/tos: Clínica/posta de ONG | individual:469D | llm |
| H32Q | Dónde buscó tratamiento para la Fiebre/tos: Hospital/otro de la Iglesi | individual:469D | llm |
| H32R | Dónde buscó tratamiento para la Fiebre/tos: Otro médico privado | individual:469D | llm |
| H32S | Dónde buscó tratamiento para la Fiebre/tos: Comprar | — | sin_pregunta (rechazada_por_verificacion) |
| H32T | Dónde buscó tratamiento para la Fiebre/tos: Curandero | individual:469D | llm |
| H32U | Dónde buscó tratamiento para la Fiebre/tos: Amigo/pariente | — | sin_pregunta (rechazada_por_verificacion) |
| H32V | Dónde buscó tratamiento para la Fiebre/tos: CS Otros | — | sin_pregunta (rechazada_por_verificacion) |
| H32W | Dónde buscó tratamiento para la Fiebre/tos: CS Otros | — | sin_pregunta (rechazada_por_verificacion) |
| H32X | Dónde buscó tratamiento para la Fiebre/tos: Otros | — | sin_pregunta (no_encontrada) |
| H32Y | Dónde buscó tratamiento para la Fiebre/tos: Sin tratamiento | — | sin_pregunta (rechazada_por_verificacion) |
| H32Z | Dónde buscó tratamiento para la Fiebre/tos: Tratamiento médico | — | sin_pregunta (rechazada_por_verificacion) |

### H33 — mezcla, incompleta

| Variable | Etiqueta | Pregunta | Cómo |
|---|---|---|---|
| H33 | Recibió vitamina A1 (más reciente) | individual:465 | llm |
| H33D | Vitamina A1 día | individual:456X | llm |
| H33M | Vitamina A1 mes | — | sin_pregunta (rechazada_por_verificacion) |
| H33Y | Vitamina A1 año | individual:456X | llm |

### H37 — incompleta

| Variable | Etiqueta | Pregunta | Cómo |
|---|---|---|---|
| H37A | Tomó FanSIDAr para la fiebre/tos | individual:471B | llm |
| H37B | Tomó Cloroquina para fiebre/tos | — | sin_pregunta (rechazada_por_verificacion) |
| H37C | Tomó Amodiaquina para fiebre/tos | — | sin_pregunta (rechazada_por_verificacion) |
| H37D | Tomó Quinina para la fiebre/tos | individual:471B | llm |
| H37E | Tomó artemisinina para la fiebre/tos | individual:471B | llm |
| H37F | Tomó Antihistanimico para la fiebre/tos | individual:471B | llm |
| H37G | Tomó Antibiótico para la fiebre/tos | individual:471B | llm |
| H37H | Tomó Otro antipalúdico para fiebre/tos | individual:471B | llm |
| H37I | Tomó Pastillas/jarabe para fiebre/tos | — | sin_pregunta (rechazada_por_verificacion) |
| H37J | Inyección para fiebre/tos | — | sin_pregunta (rechazada_por_verificacion) |
| H37K | Tomó Aspirina para la fiebre/tos | individual:471B | llm |
| H37L | Tomó Acetaminofeno para fiebre/tos | individual:471B | llm |
| H37M | Tomó Ibuprofeno para la fiebre/tos | individual:471B | llm |
| H37N | Tomó remedio casero para fiebre/tos | individual:471B | llm |
| H37O | Tomó Analgésico, antinflamatorio para fiebre/tos | individual:471B | llm |
| H37P | CS otro para fiebre/tos | — | sin_pregunta (rechazada_por_verificacion) |
| H37X | Tomó otro para fiebre/tos | individual:471B | llm |
| H37Y | No tomó nada para fiebre/tos | individual:471B | llm |
| H37Z | Tomó algo para fiebre/tos: No sabe | — | sin_pregunta (rechazada_por_verificacion) |

### H40 — incompleta

| Variable | Etiqueta | Pregunta | Cómo |
|---|---|---|---|
| H40 | Recibió Vitamina A (2da más reciente) | — | sin_pregunta (rechazada_por_verificacion) |
| H40D | Día de la vitamina A2 | individual:456X | llm |
| H40M | Vitamina A2 mes | individual:456X | llm |
| H40Y | Vitamina A2 año | — | sin_pregunta (rechazada_por_verificacion) |

### H44 — mezcla

| Variable | Etiqueta | Pregunta | Cómo |
|---|---|---|---|
| H44A | Primer lugar buscado tratamiento para la diarrea | individual:474C | manual |
| H44B | Cuántos días después de que la diarrea buscó consejo o tratamiento | individual:474D | llm |
| H44C | Todavía tiene diarrea | individual:475B | llm |

