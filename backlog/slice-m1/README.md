# Slice M1 — Planificador (spike) · BORRADOR

> **Borrador.** Se divide en historias (un archivo por historia) al cerrar M0, con lo que se haya aprendido y medido allí: tamaños, conteos del índice y tiempos. Mientras tanto sirve para planificar y para que el dueño vea el alcance.

- **Rama:** `slice-m1`, desde `main` en `slice-m0-cerrado`.
- **Fase 1** del diseño.
- **Referencias:**
  - `docs/diseno/motor_inferencia.md`, §4, §9–§13, §16–§21, §23 y §24;
  - `docs/diseno/tecnologias.md`, §6–§8.

## Objetivo

Que el motor responda **a la sombra** preguntas nuevas sobre la ENDES 2024 (archivos de niño, mujer y hogar):
- elige el dato;
- pregunta cuando duda;
- dice «no puedo» con alternativas.

Se mide con un conjunto de unas 100 preguntas. La web sigue respondiendo con el motor actual.

## Historias previstas

| ID | Historia | Tareas clave | Hecha cuando |
|---|---|---|---|
| M1-00 | Preparación | Base de pytest; latencias base del intérprete; conteos de M0; verificación en el lock de la auditoría de seguridad de `bm25s`, `PyStemmer`, `onnxruntime`, `tokenizers` y el modelo e5-small (plantilla de M0-00b; condiciones en `auditoria_seguridad_previa.md`: `tokenizers` sin `huggingface-hub` vía `override-dependencies`, solo `from_file`; `onnxruntime` solo con CPU; modelo por commit `614241f…` con SHA256SUMS; Batch API con Workspace y clave aparte, lotes borrados al bajar los resultados) | Base guardada; auditoría aprobada |
| M1-01 | Enriquecimiento del índice (lote ENDES 2024) | Extraer el texto de los cuestionarios con `pdfplumber`; vincular cada pregunta con su variable (regex o Sonnet fuera de línea); redactar universo, ventana, sujeto, informante, modo, grupo, universo corto, `rol_faltante` y `tipo_origen` con la **Batch API** (reanudable, `custom_id`; tope por lote de US$ 50); confirmar los códigos especiales propuestos en M0-05; segunda llamada que verifica; correr el control del universo contra los datos (≥ 99,5 % de los casos con dato dentro del universo redactado, diseño §7.3); marcar las dudas; revisión del auditor-agente y visto del dueño por lote → `revisado` para los archivos de niño, mujer y hogar | ≥ 95 % de las variables del conjunto de evaluación con su texto vinculado y en `revisado`; costo dentro del tope del catálogo |
| M1-02 | Intérprete en modo motor | `tema_texto` anclado; ranuras `poblacion`, `periodo_referencia`, `sujeto`, `medida` y `cortes`; sin `fuera_de_alcance` por tema; aviso de quechua; coincidencia con receta (§9) | Conjunto del slice 2 sin pérdidas; pruebas de las ranuras |
| M1-03 | Recuperador | `bm25s` + PyStemmer; e5-small en ONNX (modelo bajado por el dueño y registrado con `pap registrar` como fuente `HF-MULTILINGUAL-E5-SMALL`, con su huella en `insumos.lock.yaml`); vectores por texto distinto; RRF k = 60; `sinonimos.yaml`; filtros de sujeto y ventana; `pap variables evaluar-recuperador` con las comparaciones de §7 de tecnologías | recall@20 informado por estrato; p95 ≤ 0,3 s en el Mac |
| M1-04 | Planificador | Cliente propio ampliado; 3 muestras en paralelo (hilos, plazo de 9 s, cierre anticipado con 2 iguales); esquema fijo con IDs y pydantic; un reintento; semilla de la permutación; caché del proveedor con TTL de 1 h; corrección de `_de_cuerpo` | Pruebas con LLM falso y con grabaciones; el costo por pregunta medido |
| M1-05 | Verificador completo, huellas y decisión 1 | Resto de las reglas del §12.1; `huella_uy`; diferencia material; tabla de decisión del §12.3; certezas del §12.4; `no_cubre.yaml` | Pruebas por fila de la tabla de decisión |
| M1-06 | Aclaraciones | Tope común de 2; una dimensión por pregunta; opciones ya calculadas y que pasaron las compuertas; `elegir_plan` con `id_plan`; caché de planes ofrecidos (llave: la interpretación) | Prueba con LLM falso que cambia el orden: la cifra elegida no cambia |
| M1-07 | Sustitución y alternativas | Decisión 2 (R-ENC-06, R-ENC-09, R-ENC-10, R-ENC-13); alternativas hasta 3, calculadas, con el texto de lo que cambia | Casos de Huancavelica rural, Ate y un año sin ronda |
| M1-07b | Comparaciones entre grupos | Cortes de hasta 5 grupos con `contrast` de `svy`; prueba global Rao-Scott y luego pares con Benjamini-Hochberg al 5 % (R-ENC-11); textos «es mayor» / «no hay diferencia clara»; prueba contra R en el sintético | Las comparaciones del conjunto de evaluación salen con su prueba; coinciden con R (1e-9) |
| M1-08 | Contraste, sellos y confianza | §18 y §15.2 | Las recetas salen con «Cifra oficial del INEI»; los planes compuestos, con su sello |
| M1-09 | Contrato v2 y respuesta | `version_contrato: 2`; bloques que nunca se pliegan; cifra clave por grupos; capa 3 en palabras; validador y corrector | Q1–Q4 por las recetas con contrato v2 válido; la web actual no se rompe |
| M1-10 | Caché, costo y concurrencia | Caché de estimaciones (§20); contador de US$ por petición y por día que se reconstruye desde `uso.jsonl`; registro por petición sin el texto de la pregunta (`id_plan`, `huella_datos`, versiones, costo y tiempos por etapa); LLM fuera del candado; pool con cola acotada; estado por petición (`ContextVar`); escritura atómica de la caché del intérprete | p95 medido con 5 y 10 clientes; 503 cuando la cola se llena |
| M1-11 | Modo sombra | `motor.version: sombra` por tema; registro de diferencias sin el texto de la pregunta | Corre sobre Q1–Q4, la matriz y la evaluación sin errores |
| M1-12 | Conjunto de evaluación y medición | `tests/inferencia/evaluacion.yaml` con unas 100 preguntas: el agente genera las que tienen cifra oficial (aprobadas si reproducen); el dueño escribe de 40 a 60; doble anotación del universo; 30 % no vista. Métricas del §23.3 con su intervalo de Wilson | Informe de métricas; decisión sobre el número de muestras y el esfuerzo del planificador |
| M1-13 | Revisión independiente y cierre | Por partes; cierre; etiqueta | — |

## Del dueño, antes de M1

- **Bajar el modelo `intfloat/multilingual-e5-small`** (ONNX y tokenizer) de Hugging Face, con su commit, para registrarlo.
- **Confirmar el tope diario del LLM** (K-05) y el tope del enriquecimiento del índice (se estiman unos US$ 30 para unas 40 000 variables con la Batch API; el número real sale de M0).
- **Escribir las 40 a 60 preguntas a mano** del conjunto de evaluación (M1-12).

## Dependencias nuevas de M1

`bm25s==0.3.15`, `PyStemmer==3.1.0`, `onnxruntime==1.31.1` y `tokenizers==0.23.3`. Cada versión se revisa al empezar, con al menos 2 semanas de antigüedad.
