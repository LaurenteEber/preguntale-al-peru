# M1-09 — Recuperador

**Se deriva de** el diseño §10, `tecnologias.md` §7 y `fichas.md` §7.

## Antes de empezar

El dueño deja el modelo en la bandeja; se registra con `pap registrar` como fuente `HF-MULTILINGUAL-E5-SMALL`, con su commit y huellas en `insumos.lock.yaml`. Mientras no esté, se avanza con la búsqueda por palabras.

## Tareas

1. **Dependencias** (ya auditadas en M1-00): `bm25s`, `PyStemmer`, `onnxruntime` y `tokenizers`, con versión exacta en el lock.
2. **Búsqueda por palabras:** BM25 con stemmer en español, minúsculas y sin acentos, sobre etiqueta curada, texto de la pregunta, etiquetas de las categorías, universo corto, **nombre y descripción del bloque**, y sinónimos expandidos.
3. **Búsqueda por significado:** e5-small en ONNX, con los prefijos `query:` y `passage:`; un vector por texto distinto; vectores calculados fuera de línea y guardados con la huella del modelo.
4. **Fusión:** RRF (k = 60) de las dos búsquedas y de dos consultas (pregunta original y tema interpretado); agrupar por `grupo` y por `bloque_id` (bloque temático); salen de 10 a 20 candidatos con ID corto (`c01`…).
5. **Sin filtro previo** de año, lugar ni nivel. Filtros de significado por `sujeto` y `periodo_referencia` solo cuando la pregunta los trae.
6. **Estado:** solo entran variables `revisado` de clase `categoria` o `medida` (o `propuesto` con `inferencia.admitir_propuesto_en_sombra`).
7. **Dos pasos** (`recuperador.dos_pasos`, inicial `false`): paso 1 sobre bloques, conceptos y recetas; paso 2 sobre las variables de los bloques elegidos. Se implementa y se mide contra el modo de un paso.
8. **`pap variables evaluar-recuperador`:** recall@20 sobre el conjunto semilla de M1-00 (se repite con el conjunto completo en M1-19), en total y por estrato, con y sin sinónimos, con y sin bloques, y un paso frente a dos.

## Criterios de aceptación

- [ ] recall@20 informado por estrato, con su intervalo (umbrales indicativos en M1: ≥ 0,95 en el total y ≥ 0,90 en vocabulario popular y en pares casi iguales).
- [ ] p95 ≤ 0,3 s en el Mac.
- [ ] La comparación un paso / dos pasos y con / sin bloques está en `evidencia/m1-09_recall.md`, con una recomendación.
- [ ] Si cambia la huella del modelo, los vectores se recalculan (prueba).
- [ ] Memoria del servicio con el modelo cargado medida y anotada en `docs/especificaciones/stack.md`.

## Fuera

Reordenador; modelos mayores (solo si el recall no alcanza, como consulta).
