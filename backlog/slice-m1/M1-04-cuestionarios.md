# M1-04 — Texto de los cuestionarios y vínculo con las variables

**Se deriva de** el diseño §7.2 y `tecnologias.md` §6.

## Tareas

1. **Extraer el texto** de los tres cuestionarios de la ENDES 2024 (hogar, individual y salud) con `pdfplumber`, en el lector aislado (tiempo y memoria acotados): número de pregunta, texto, opciones, saltos y sección. Salida en `biblioteca/variables/cuestionarios/ENDES/2024/*.parquet` (no va a git).
2. **Extraer los diccionarios por tabla** (los PDF «Diccionario - <tabla>.pdf» que vienen dentro de cada ZIP): variable, etiqueta, categorías y, si lo trae, el número de pregunta. Son la primera fuente del vínculo.
3. **Medir primero** (hipótesis de `tecnologias.md` §6): en 3 tablas (RECH6, REC43 y REC0111), cuántas variables se vinculan solo con el diccionario y expresiones regulares. Informar el porcentaje antes de usar el LLM.
4. **Vínculo pregunta ↔ variable** para lo que falte, con Sonnet fuera de línea por la **Batch API**:
   - el LLM recibe la variable (código, etiqueta, categorías) y las preguntas candidatas de la sección, con IDs; devuelve un ID o «ninguna»;
   - segunda llamada que verifica el vínculo propuesto;
   - reanudable (`custom_id`, `batch_id` guardado antes de consultar el estado), con el tope `batch.tope_lote_usd`;
   - cliente propio ampliado (`interprete/llm.py`), sin dependencias nuevas.
5. **Manual de la Entrevistadora** (documento n.º 8): se usa como apoyo para los saltos cuando el cuestionario no basta. No se indexa entero.
6. **Guardar** en el índice `texto_pregunta` y la referencia (cuestionario, sección, número de pregunta, página), con `estado: propuesto`. Las variables sin vínculo quedan marcadas `sin_pregunta` con su motivo (construida, administrativa, no encontrada).

## Criterios de aceptación

- [ ] Los tres cuestionarios extraídos; conteo de preguntas por sección en `evidencia/m1-04_cuestionarios.md`.
- [ ] Porcentaje de variables vinculadas por tabla, separando «por diccionario» y «por LLM». Meta de `tecnologias.md` §6: ≥ 95 % de las variables de las recetas (y, en M1-19, de las del conjunto de evaluación) con su texto vinculado.
- [ ] Costo real del lote informado y dentro del tope.
- [ ] El lote se puede reanudar: prueba con un proveedor falso que corta a la mitad.
- [ ] Ningún texto de pregunta entra a una respuesta pública mientras esté en `propuesto`.

## Fuera

Otros años. Decidir `revisado` (M1-07).
