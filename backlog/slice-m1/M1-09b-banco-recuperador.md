# M1-09b — Banco de pruebas del recuperador

**Historia agregada por el supervisor el 12/11/2026,** con el visto del dueño. No cambia M1-09: la complementa. **Depende de** M1-09 (búsqueda por palabras y por significado funcionando) y del conjunto semilla de M1-00.

**Se deriva de** `tecnologias.md` §7 («si no se cumple, se prueba en este orden…») y de una revisión de la evidencia publicada a noviembre de 2026, encargada por el dueño.

## Por qué

`multilingual-e5-small` se eligió con cifras publicadas, sin medir en datos propios. La revisión encontró:

- **Por palabras:** `bm25s` con el stemmer en español sigue siendo buena elección. Las variantes de BM25 rinden casi igual; no hay motor alternativo que prometa más a este tamaño.
- **Por significado:** desde mayo de 2026 existe `ibm-granite/granite-embedding-97m-multilingual-r2`, del mismo tamaño que e5-small (384 dimensiones), con licencia Apache 2.0, ONNX oficial y sin prefijos. IBM informa 60,3 frente a 50,9 de e5-small en recuperación multilingüe (MTEB multilingüe v2). **Es un promedio multilingüe informado por el propio IBM, no una cifra en español.**
- **El texto que se indexa pesa tanto como el modelo:** en un estudio de portales de datos abiertos, agregar una descripción generada por un LLM subió el acierto más que cualquier cambio de modelo.
- **No existe un benchmark público** de búsqueda de variables de encuesta en español. Solo nuestros datos pueden decidir.

Fuentes: IBM, «Granite Embedding Multilingual R2» (blog y arXiv 2605.13521); Wang et al., «Multilingual E5 Text Embeddings» (arXiv 2402.05672); Lù, «BM25S» (arXiv 2407.03618); Bruch et al., «An Analysis of Fusion Functions for Hybrid Retrieval» (arXiv 2210.11934); «Keywords are not always the key» (arXiv 2509.14457).

## Tareas

1. **El modelo de significado se elige por parámetro** (`recuperador.modelo` en `curados/inferencia/parametros.yaml`): identificador de la fuente, dimensiones, prefijos de consulta y de documento (vacíos si no usa), longitud máxima y tipo de agregación. Cambiar de modelo no debe tocar código. Los vectores se guardan por modelo, con su huella.
2. **Modelos a comparar** (cada uno entra con su auditoría, plantilla y condiciones de `backlog/slice-m0/evidencia/auditoria_seguridad_previa.md`: solo ONNX y tokenizer, por commit, con SHA-256, solo CPU, sin código remoto):
   - `intfloat/multilingual-e5-small` — línea base (ya auditado);
   - `ibm-granite/granite-embedding-97m-multilingual-r2` — candidato a reemplazo;
   - `ibm-granite/granite-embedding-311m-multilingual-r2` — techo de calidad; se prueba a 768 y truncado a 256 dimensiones.
   - **Opcional,** solo si su auditoría lo aprueba: `hotchpotch/bekko-embedding-v1-a25m` (un solo autor, julio de 2026). Si la auditoría no lo aprueba, se anota y se sigue.
   - **Fuera:** modelos con licencia no comercial (Jina v3 y v5), los que exigen `trust_remote_code` (gte-multilingual, nomic v2, arctic v2) y los decodificadores con instrucciones (Qwen3, harrier).
   - Cada modelo es una fuente nueva del catálogo, con su receta de descarga manual (como en M1-00, tarea 9). **Los baja el dueño** y los deja en la bandeja.
3. **Comando** `pap variables evaluar-recuperador --banco`: corre todas las combinaciones sobre el conjunto de evaluación y escribe una tabla. Mide, en este orden:
   1. recall@20 y recall@50 de cada parte por separado: palabras, significado y fusión;
   2. **texto original frente a texto enriquecido:** al texto de cada variable se le agrega una descripción corta y términos coloquiales, propuestos por el LLM fuera de línea (Batch API, dentro del tope del lote) y revisados por muestreo por el auditor-agente. El texto enriquecido es **solo para buscar**: nunca se muestra ni entra a una respuesta, y se guarda en un campo aparte del índice (`texto_busqueda`), con `estado`;
   3. e5-small frente a granite-97m-r2 y granite-311m-r2;
   4. con y sin `sinonimos.yaml`; con y sin la segunda consulta (tema interpretado); con y sin el texto del bloque temático;
   5. RRF (k = 60) frente a combinación ponderada de puntajes normalizados (mín-máx, un solo peso). El peso se ajusta solo con la partición de desarrollo;
   6. si sobra tiempo: una tercera lista por 4-gramas de caracteres, sobre preguntas con errores de tipeo.
4. **Por cada combinación:** recall@20 y @50 con su intervalo de Wilson, en total y por estrato (vocabulario popular y pares casi iguales aparte); p95 de la consulta en el Mac; memoria con el modelo cargado; tiempo de indexar.
5. **Regla de decisión** (tipo B, con evidencia):
   - se cambia el modelo por defecto solo si el candidato mejora el recall@20 en 3 puntos o más en el total **y** no empeora en ningún estrato, con p95 ≤ 0,3 s;
   - con diferencias menores, se queda e5-small (ya auditado y medido);
   - el texto enriquecido y la combinación ponderada se adoptan con la misma regla;
   - el modelo de 311 M solo se adopta si su ventaja sobre el mejor pequeño es de 5 puntos o más.
   - Con el conjunto semilla (unas 30 preguntas) los intervalos son anchos: el resultado es **indicativo**. La decisión firme se toma al repetir el banco con el conjunto completo en M1-19, sobre la partición de desarrollo; la partición no vista no se usa aquí.
6. **Actualizar `docs/diseno/tecnologias.md` §7** con lo medido y el modelo elegido, y registrar el cambio en `decisiones.md` (fila F-05) si el modelo por defecto cambia.

## Criterios de aceptación

- [ ] Cambiar `recuperador.modelo` y recalcular los vectores no requiere tocar código (prueba con dos modelos).
- [ ] Auditoría de cada modelo en `evidencia/`, con commit y huellas; ninguno carga código remoto.
- [ ] `evidencia/m1-09b_banco.md` con la tabla completa y, en sencillo, qué se adopta y por qué.
- [ ] Ningún texto enriquecido aparece en una respuesta (prueba).
- [ ] El costo del lote de enriquecimiento informado y dentro de `batch.tope_lote_usd`.
- [ ] Las 90 filas y la suite sin cambios.

## Del dueño

Bajar de Hugging Face y dejar en `biblioteca/cruda/bandeja/`, en la carpeta de cada modelo, los archivos que indique la auditoría (el ONNX, `tokenizer.json` y los JSON de configuración), en el commit que la auditoría fije:

1. `intfloat/multilingual-e5-small` (ya previsto en M1-09);
2. `ibm-granite/granite-embedding-97m-multilingual-r2`;
3. `ibm-granite/granite-embedding-311m-multilingual-r2`.

El agente entrega antes la lista exacta de archivos y commits. Si falta alguno, el banco corre con los que haya.

## Fuera

Reordenadores (ninguno multilingüe con latencia publicada bajo 150 ms en CPU; el LLM ya elige entre 20 candidatos), modelos dispersos aprendidos y lematización: quedan anotados para M2 si el recall no alcanza.
