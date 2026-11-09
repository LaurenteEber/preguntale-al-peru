# Tecnologías del motor de inferencia

Pregúntale al Perú · 9 de noviembre de 2026 · Complementa `docs/diseno/motor_inferencia.md`.

**En sencillo.** Esta es la lista de herramientas con las que se construye el motor y por qué se eligió cada una. El criterio fue:
- que funcionen en el Mac sin pagar por consulta;
- que sean pocas y estables;
- que sus resultados se puedan comprobar.

Cada elección trae su prueba de aceptación. Si no la pasa, se usa la alternativa indicada.

Las mediciones se hicieron en un contenedor Linux con 2 núcleos y 7 GB de RAM. **En el Mac se vuelven a medir en la fase 0 o en la 1**, según la pieza.

---

## 1. Resumen

| Pieza | Elección | Versión | Licencia | Dependencia | Fase |
|---|---|---|---|---|---|
| Estimación con diseño muestral | `svy` (con `svy-io` 0.7.1 y `svy-rs` 0.19.1; `svy_io` nunca lee archivos) | **0.35.0** (sube desde 0.32.1) | MIT | ya existe | 0 |
| Lectura de SPSS y Stata | `pyreadstat` | **1.3.7** (sube desde 1.3.6) | Apache-2.0 | ya existe | 0 |
| Escritura de Parquet | DuckDB `COPY … (FORMAT parquet, COMPRESSION zstd)` | 1.5.6 (sin cambio) | MIT | ya existe | 0 |
| Huella de contenido | `md5` de DuckDB por fila canónica, ordenado, más un sha256 final (`huella_contenido_v1`) | — | — | ninguna | 0 |
| Mojibake | `ftfy` | **6.3.1** | Apache-2.0 | **nueva**, liviana | 0 |
| Validación de la salida del LLM | `pydantic` | **2.13.5** (ya está en el lock; se declara directa) | MIT | declarar | 0 |
| Pool de cálculo | `concurrent.futures.ProcessPoolExecutor` (spawn), con un envoltorio propio | biblioteca estándar | — | ninguna | 0 |
| Verificador en R | `Rscript` como subproceso, `survey` y `renv` | R 4.5.x o 4.6.x (desde el 12/11); `survey` 4.5; `renv` **1.3.1**; `nanoparquet` **0.5.2**; CRAN con instantánea fija | GPL (fuera del proceso de Python) / MIT | herramienta aparte, no de Python | 0 |
| Texto de los cuestionarios PDF | `pdfplumber` + Sonnet fuera de línea + revisión | 0.11.10 (ya existe) | MIT | ya existe | 1 |
| Búsqueda por palabras | `bm25s` + `PyStemmer` | **0.3.15** / **3.1.0** | MIT / MIT | **nuevas** | 1 |
| Búsqueda por significado | `intfloat/multilingual-e5-small` (ONNX), con `onnxruntime` y `tokenizers` | **1.31.x** (la última con ≥ 2 semanas al empezar M1) / **0.23.3**; modelo fijado por commit y huella | MIT / Apache-2.0 / MIT (modelo) | **nuevas** (unos 155 MB) | 1 |
| Vectores | numpy por fuerza bruta (`.npy` fp16 en disco, float32 en memoria) | numpy del lock | — | ya existe | 1 |
| LLM | Cliente propio (`src/pap/interprete/llm.py`, con `httpx`) ampliado; sin el SDK `anthropic` | httpx 0.28.1 | — | ya existe | 1 |
| Llamadas en paralelo | `ThreadPoolExecutor` con un cliente HTTP por muestra | biblioteca estándar | — | ninguna | 1 |
| Enriquecimiento masivo del índice | Batch API de Anthropic, a través del cliente propio | — | — | ninguna | 1 |
| Grabaciones de pruebas del LLM | Esquema propio del repo, ampliado | — | — | ninguna | 1 |

**No se adoptan:**
- el SDK `anthropic` (sumaría `httpx2` y `opentelemetry`);
- `sentence-transformers` (pesa 5,5 GB con torch);
- `fastembed` (27 paquetes);
- la extensión FTS de DuckDB (no hay paquete para la 1.5.6 y hay que bajarla de internet);
- la extensión `vss` (es experimental y puede corromper el índice);
- PyMuPDF (licencia AGPL);
- `docling` y `marker` (traen torch y modelos, y uno tiene una licencia con tope de ingresos);
- `rpy2` (GPL dentro del proceso y difícil de instalar);
- `loky` y `pebble` (no los necesitamos o son LGPL);
- `vcrpy` (el esquema propio ya resuelve el problema).

---

## 2. Estimación: `svy` 0.35.0

**En sencillo.** Es la librería que calcula las cifras teniendo en cuenta cómo se eligió la muestra. La versión 0.35.0 da los mismos números que la actual y es hasta 10 veces más rápida cuando hay muchos grupos.

**Detalle técnico.**
- **Igualdad:**
  - las versiones 0.32.1, 0.35.0 y 0.36.0 dieron salidas idénticas en la ENDES 2023–2024 para `prop`, `contrast`, Rao-Scott y la mediana;
  - las tres coinciden con R `survey` en un microdato sintético, con una diferencia máxima de 4,6e-14.
- **Tiempos** (`prop(by=, where=)`, Korn-Graubard, `endes_nino`):

  | Caso | 0.32.1 | 0.35.0 |
  |---|---|---|
  | 1 año, 98 dominios | 291 ms | 117 ms |
  | 2 años apilados, 196 dominios | 1 345 ms | 333 ms |
  | 4 años apilados, 392 dominios | 8 690 ms | 848 ms |
  | 11 años, 275 dominios en 1 llamada | 15,4 s | 5,9 s |

- **Lo que se verificó de 0.35.0:**
  - `ci_method="korn-graubard"` es la variante NCHS: trunca el n efectivo en n y acota en p = 0 o 1;
  - entrega gl y n por dominio en `to_polars()`;
  - anida la UPM en el estrato de forma automática;
  - `contrast({(dominio, 1.0): 1, …})` incluye la covarianza, pero usa los gl del diseño completo, así que hay que recalcular p con mín(gl_a, gl_b);
  - Rao-Scott solo está en `categorical.tabulate(...)`;
  - la mediana usa Woodruff y no admite contrastes;
  - **un dominio vacío no aparece en la salida**, así que el ejecutor debe reindexar los dominios pedidos.
- **La 0.36.0 todavía no:** cumple 2 semanas el 11/11, cambia el espacio de nombres (de 115 a 39) y los errores, y el próximo «Unreleased» vuelve a cambiar las columnas de `to_polars()`.
  - **Regla:** solo `src/pap/inferencia/svy_adaptador.py` lee la salida de `svy`.
- **Política (F-05):** cada cambio de versión es una historia propia. Para aceptarla:
  - todas las filas del cubo deben quedar iguales (|dif| ≤ 1e-12);
  - los esperados de R deben quedar dentro de 1e-9.

## 3. Verificador en R

**En sencillo.** Una segunda implementación, en otro lenguaje, que calcula lo mismo. Si las dos coinciden, la cifra es confiable aunque no exista una cifra oficial con qué compararla.

**Detalle técnico.**
- **Cómo corre:** `verificador_r/verificar.R` se llama con `Rscript --vanilla` como subproceso, con lista de argumentos (sin shell), parámetros en un JSON y entorno mínimo sin claves (`PAP_ANTHROPIC_API_KEY`, `GH_TOKEN`); lee CSV y escribe CSV. Las versiones se fijan con `renv` (`verificador_r/renv.lock`).
- **Dónde:** R **no corre dentro de pytest**. Genera una vez `tests/esperados/r_survey_*.csv`, con las versiones de R y de `survey` en la cabecera, y pytest solo compara. Se regenera con `just esperados-r` en el Mac al subir `svy` o `survey`. En CI es un trabajo manual o semanal (`r-lib/actions/setup-r@v2`, `setup-renv@v2`).
- **Equivalencias con `svy`:**
  - diseño: `svydesign(ids=~upm, strata=~estrato, weights=~peso, nest=TRUE)`;
  - estratos con una sola UPM: `options(survey.lonely.psu="adjust", survey.adjust.domain.lonely=FALSE)`, que equivale a `Singleton("center", domains="standard")`;
  - dominios: `subset()` + `svymean` + `degf(subset)`;
  - contrastes: `svyby(covmat=TRUE)` + `svycontrast`;
  - Rao-Scott: `svychisq(statistic="F")`;
  - mediana: `svyquantile(qrule="math", interval.type="mean")`.
- **Korn-Graubard NCHS:** R no lo trae (`svyciprop(method="beta")` no trunca), así que se escribe a mano en unas 8 líneas.
- **Datos reales:** se leen con `nanoparquet` 0.5.2 (la 0.5.1 leía mal los perdidos con `col_select`), sin dependencias, en vez de `arrow`.
- **Versión de `survey`:** la 4.5 de CRAN es anterior a la corrección de la 4.5-2 (ee sobreestimado). Al crear el `renv.lock` se comprueba qué versión está en CRAN. Si la 4.5-2 o posterior no está, se documenta si la corrección afecta a los casos del verificador (dominios y contrastes) antes de usar la 4.5.
- **Prototipo existente:** `docs/especificaciones/stack.md` registra un prototipo del verificador (con el Korn-Graubard NCHS ya probado) en la carpeta de trabajo anterior. Se reutiliza su `verificar.R` si el dueño lo copia.

## 4. Ejecución aislada (pool de procesos)

**En sencillo.** Cada cálculo corre en un proceso aparte, con un tiempo y una memoria máximos. Así, una pregunta pesada no traba el servicio ni a las demás personas.

**Detalle técnico.**
- **Pool:** `ProcessPoolExecutor(mp_context=spawn, max_tasks_per_child=200)`, con precalentamiento (importar `svy` y abrir DuckDB) en el `initializer`.
- **Tiempo:** dos topes.
  - **Suave:** `signal.alarm(ejecutor_timeout_s)` dentro del trabajador.
  - **Duro:** el padre mata al trabajador si no hay resultado en `ejecutor_timeout_s + ejecutor_gracia_s` y recrea el pool. Las señales no cortan el código nativo: en una prueba, una alarma de 1 s devolvió el control a los 2,68 s.
- **Memoria:**
  - un hilo vigía dentro del trabajador hace `os._exit(137)` si `ru_maxrss` pasa `memoria_trabajador_mb` (ojo: el valor viene en bytes en macOS y en KiB en Linux). Probado: corta a 1 GB en 1,03 s;
  - **no se usa `RLIMIT_AS`**: en Linux aborta Rust (el trabajador reserva unos 2,75 GB virtuales para 240 MB reales) y en macOS no se aplica;
  - en la nube, además, un límite de cgroup para el servicio.
- **Hilos:**
  - se fijan `POLARS_MAX_THREADS=1` y `RAYON_NUM_THREADS=1` antes de importar;
  - DuckDB va con `threads=1` y `memory_limit=512MB` por trabajador;
  - en la fase 0 se mide 1 frente a 2 hilos.
- **Sin copias:** `con.sql(...).arrow()` → `pl.from_arrow` → `svy.Sample` conserva los buffers (9 ms para 236 869 filas). No usar `fetch_arrow_table()`, que DuckDB 2.0 elimina.

## 5. Ingesta y almacén

**En sencillo.** Leer los archivos del INEI sin perder los códigos de «no sabe», guardarlos comprimidos y poder demostrar que los datos no cambiaron aunque cambie la herramienta que los escribió.

**Detalle técnico.**
- **Lectura** (`pyreadstat` 1.3.7):
  - `user_missing=True` siempre, porque sin eso los perdidos de usuario de SPSS se vuelven nulos y «no sabe» queda igual que «no se le preguntó»;
  - `apply_value_formats=False`, `output_format="polars"` y `encoding=None` (la del archivo); en un DTA sin codificación declarada, `WINDOWS-1252`;
  - archivos de más de 200 MB, en bloques de 25 000 filas (`read_file_in_chunks`). Un SAV de 576 MB leído completo llegó a 3,4 GB de memoria; en bloques, a 0,96 GB;
  - para el índice: `metadataonly=True` **y** `user_missing=True`, porque sin esto último `missing_ranges` sale vacío.
  - `pandas.read_spss` no sirve: pierde los códigos especiales.
  - Nota: el lector actual (`src/pap/capa0/encuestas.py:71`) no usa `user_missing`, y eso es intencional para las recetas de hoy, que excluyen los vacíos. El motor nuevo usa su propio lector.
  - **Formato por año:** lo fija la consulta K-06 (recomendación: Stata donde exista y SPSS en la ENDES 2015–2020). Con `user_missing=True`, los perdidos extendidos de Stata (.a–.z) y los de usuario de SPSS se normalizan igual: nulo en la columna y código en el índice.
- **Escritura:**
  - DuckDB `COPY … TO … (FORMAT parquet, COMPRESSION zstd, COMPRESSION_LEVEL 3, ROW_GROUP_SIZE 122880)`;
  - un archivo por encuesta, año y archivo, sin particiones, con la columna `anio` dentro;
  - tipos: llaves y geo en VARCHAR normalizado con su longitud verificada, categorías en INTEGER y medidas en DOUBLE.
- **Huellas:**
  - `huella_datos` (identidad, para citar y para la caché) = sha256 del ZIP + versión del conversor;
  - `huella_contenido_v1` (integridad, estable entre versiones del escritor):
    1. md5 de cada fila en forma canónica: columnas en orden alfabético, separador `\x1f`, nulo como `\x00` y decimales con `printf('%.17g')`;
    2. las filas se ordenan;
    3. sha256 del conjunto.

    Dio la misma huella en 8 reescrituras (polars, pyarrow, filas barajadas; DuckDB 1.5.6 y 2.0). Tarda unos 0,7–1 s en `endes_nino`.
  - No se usa `hash()` de DuckDB, porque puede cambiar entre versiones.
- **Respaldo y espacio local:** `gh` CLI contra el repo privado `LaurenteEber/preguntale-al-peru-crudos`, con un token de grano fino solo para ese repo. Comandos nuevos `pap almacen restaurar` y `pap almacen liberar` (simulación por defecto). El ciclo por bloque y lo que nunca se libera están en el §6 del diseño.
- **Etiquetas:**
  - `ftfy.fix_text` (repara UTF-8 leído como cp1252, incluso dos veces), luego NFC y limpieza de espacios;
  - se guardan la etiqueta original y la curada;
  - el mojibake de DOS (cp850: «Ni¤o») no lo repara ftfy: se relee con `encoding="CP850"` si aparece.

## 6. Cuestionarios PDF (fase 1)

**En sencillo.** El texto exacto de cada pregunta está en el cuestionario en PDF. Se extrae con una herramienta, un LLM propone a qué variable corresponde y una persona lo aprueba.

**Detalle técnico.**
- La extracción se hace con `pdfplumber` 0.11.10, que ya está en el lock.
- **Vínculo pregunta ↔ variable:**
  - en la ENAHO, por expresión regular (P203 ↔ pregunta 203);
  - en la ENDES, los códigos (HC57, V…, S…) no siguen el número de pregunta: Sonnet propone el vínculo fuera de línea y el auditor-agente y el dueño lo aprueban por lote.
- **Hipótesis por verificar con los PDF reales** (no se pudieron bajar en el contenedor): el formato de las tablas y de los saltos.
- **Para aceptarlo:** ≥ 95 % de las variables de las recetas y del conjunto de evaluación con su texto vinculado y revisado.

## 7. Búsqueda de variables (fase 1)

**En sencillo.** Dos buscadores que se complementan:
- uno por palabras, que es rápido y encuentra términos exactos;
- otro por significado, que encuentra preguntas parecidas aunque usen otras palabras.

Más una tabla de sinónimos peruanos («chispitas», «posta»), que ningún modelo conoce.

**Detalle técnico.**
- **Por palabras:** `bm25s` 0.3.15 con `PyStemmer` 3.1.0 (español), minúsculas, sin acentos y con stopwords en español.
  - Con 100 000 / 300 000 filas, indexa en 6,3 / 17,9 s y responde en 0,5 / 0,9 ms.
  - El índice se guarda con mmap junto al índice de variables.
  - Ojo: el stemmer separa «anemia» → `anemi` de «anémicos» → `anem`, y eso se compensa con los sinónimos.
- **Por significado:** `intfloat/multilingual-e5-small` (384 dimensiones), con `onnxruntime` 1.31.x y `tokenizers` 0.23.3 y unas 40 líneas propias (tokenizar, inferir, promedio y L2).
  - Prefijos obligatorios: `query: ` y `passage: `.
  - Hasta 128 tokens por texto: etiqueta, pregunta, universo y como máximo 15 categorías.
  - **Calidad publicada en español** (MIRACL es, nDCG@10): small 51,2, base 51,5, BGE-M3 55,5–56,1 (según la tabla citada).
  - **Costo medido:**

    | Precisión | Consulta | 100 000 textos | Memoria |
    |---|---|---|---|
    | fp32 | 7–12 ms | 29–37 min (64–96 tokens); 58–85 min (128 tokens) | ~690–870 MB |
    | int8 | 4 ms | 11–16 min (64–96 tokens); ~32 min (128 tokens) | ~280–510 MB |

  - **Por defecto fp32.** int8 solo si, cuantizado por nosotros con `quantize_dynamic`, pierde ≤ 1 punto de recall. El int8 publicado es para x86.
  - **Un vector por texto distinto**, no por variable × año.
  - **El modelo lo baja el dueño**, porque los agentes no llegan a Hugging Face. Se registra con `pap registrar` como un insumo más (fuente `HF-MULTILINGUAL-E5-SMALL`), y su commit y la huella del `.onnx` y del tokenizer quedan en su `datapackage.json` y en el manifiesto de `biblioteca/variables/`. Si cambian, se recalculan todos los vectores.
- **Vectores:** numpy por fuerza bruta. 300 000 × 384 en float32 ocupan 461 MB y responden en 38 ms. Se guardan como `.npy` fp16 y se cargan en float32 (en fp16 el cálculo es 7–9 veces más lento).
- **Fusión:**
  - RRF con k = 60 y 50 resultados por lista;
  - dos consultas, la pregunta original y el tema interpretado;
  - se agrupa por código de variable y `grupo`;
  - salen de 10 a 20 candidatos.
- **Reordenador:** ninguno en la fase 1. Si hiciera falta, `mmarco-mMiniLMv2-L12` (unos 300 ms con 20 pares), solo si sube el recall@20 en 5 puntos o más. Excluidos `bge-reranker-v2-m3` (6,5 s) y `jina-reranker` (no comercial).
- **Para aceptarlo** (en el Mac). En la fase 1 los umbrales de recall son **indicativos** y se informan con su intervalo (diseño §23.3); en la fase 2 se vuelven exigibles:
  - recall@20 ≥ 0,95 en el total y ≥ 0,90 en vocabulario popular y en pares casi iguales;
  - p95 del recuperador ≤ 0,3 s. Un reordenador, por sí solo, ya rompe este tope.

  Si no se cumple, se prueba en este orden:
  1. más sinónimos;
  2. e5-base int8 (o `granite-embedding-107m-multilingual` en A/B);
  3. BGE-M3;
  4. el reordenador.

## 8. LLM: cliente, paralelo, costo y pruebas (fase 1)

**En sencillo.** Se amplía el cliente propio que ya existe, en lugar de sumar el de Anthropic, que trae dependencias nuevas. Las tres consultas del planificador corren al mismo tiempo, y el costo se lleva por pregunta y por día.

**Detalle técnico.**
- **Paralelo:**
  - `ThreadPoolExecutor`, con un `httpx.Client` por muestra (no se verificó si uno compartido es seguro entre hilos);
  - plazo común de 9 s para las 3 muestras (`wait(timeout=…)`);
  - si 2 muestras válidas coinciden en `huella_uy`, se decide sin esperar la tercera.
- **Validación:** `pydantic` 2.13.5 con `extra="forbid"` y `strict`.
  - IDs: `^c(0[1-9]|1\d|20)$` para candidatos y `^k([1-9]|[12]\d|30)$` para categorías.
  - Un validador con contexto comprueba que el ID esté en la lista de esa pregunta.
  - Un reintento con el error resumido.
  - La permutación de candidatos usa una semilla determinista (la `id` de la interpretación), para que la grabación sea reproducible.
- **Caché del proveedor** (verificado en la documentación oficial):
  - mínimo de 512 tokens para Sonnet 5.5;
  - escritura a 1,25× (5 min) o 2× (1 h); lectura a US$ 0,10/MTok.
  - El prompt fijo va en `system` con caché de 1 h. Los candidatos permutados van sin caché.
  - Con la caché fría, se lanza la muestra 1, se espera su primer byte y después las otras dos.
  - **Corrección necesaria:** `_de_cuerpo` en `llm.py` aplica una sola tarifa de escritura; hay que separar `ephemeral_1h_input_tokens` de los de 5 minutos.
- **Costo estimado:**

  | Caso | Por pregunta |
  |---|---|
  | Con plan compuesto | ~US$ 0,04 |
  | Con receta | ~US$ 0,002 |
  | Peor caso | ~US$ 0,18 |

  **`tope_llm_usd_dia` propuesto: US$ 5** (unas 100 preguntas compuestas y 500 con receta).
  - El contador es por petición, en el día de Lima, y reserva el peor caso antes de llamar.
  - Se reconstruye desde `uso.jsonl` al arrancar, para que un reinicio no lo ponga en cero.
- **Enriquecimiento del índice** (Batch API): 50 % de descuento, hasta 100 000 peticiones o 256 MB por lote, vence a las 24 h y empareja por `custom_id`.
  - Unas 40 000 variables costarían ≈ US$ 30. Es una estimación: el número real se cuenta en la fase 0.
  - Es reanudable: se guarda el `batch_id` antes de consultar su estado y las salidas se escriben de forma idempotente.
- **Grabaciones:**
  - la llave es (etapa, modelo, versión del prompt, hash de los candidatos, número de muestra, variante, error previo);
  - cada grabación guarda un `cuerpo_sha256`: si el prompt cambia sin subir de versión, la prueba falla.
- **No determinismo:** se prueba en tres partes: un LLM falso, que la decisión no dependa del orden de llegada y una corrida de estabilidad en vivo (fase 1).
- **Concurrencia web:**
  - el LLM sale del candado global;
  - `Cliente.gastado`, `intentos_http` y `LlmContado.tope_visto` pasan a ser por petición (`ContextVar`);
  - la caché del intérprete se escribe de forma atómica (archivo temporal + `os.replace`);
  - el cálculo va al pool, con un `BoundedSemaphore` de 2 × trabajadores; si se llena, 503.

## 8b. Seguridad de la cadena de suministro

**En sencillo.** Todo lo que entra al proyecto se audita antes, y unos controles automáticos impiden que entre algo sin revisar o demasiado nuevo.

**Detalle técnico.** La auditoría previa del 9/11/2026 está en `backlog/slice-m0/evidencia/auditoria_seguridad_previa.md`, con un veredicto por componente y los controles C1–C14. Lo principal:
- **`uv`:**
  - `exclude-newer = "2 weeks"`;
  - un lock con hashes, una sola fuente y solo wheels (`uv sync --locked --no-build`);
  - `pip-audit` y `osv-scanner` (`just auditar`).
- **Versiones corregidas por seguridad:** Pillow 13.0.0, `certifi` 2026.10.18, `renv` 1.3.1, `nanoparquet` 0.5.2 y Python ≥ 3.12.12.
- **Lectores aislados:** solo `pyreadstat` lee SAV y DTA, y `svy_io` nunca. ZIP, SAV, DTA y PDF se leen en un subproceso por archivo con límites, y los ZIP se abren con `abrir_zip_seguro`.
- **Sin red al ejecutar:**
  - `HF_HUB_OFFLINE=1` y `SVYLAB_OFFLINE=1`;
  - pruebas con `pytest-socket`;
  - `onnxruntime` solo con `CPUExecutionProvider`;
  - `tokenizers` con `from_file`, sin `huggingface-hub` (`override-dependencies`).
- **Secretos:** gitleaks sobre todo el historial y antes de cada commit; Push protection; `.env` en `.gitignore`.

## 9. Valores por defecto

Los valores entran en el anexo B del diseño, que dice en qué archivo vive cada uno: la mayoría en `curados/inferencia/parametros.yaml`; `tope_llm_usd_dia` y `trabajadores` en `curados/web/parametros.yaml`.

| Parámetro | Valor |
|---|---|
| `dominios_max_llamada` | 100 |
| `anios_apilados_max_llamada` | 4 |
| `ejecutor_timeout_s` / `ejecutor_gracia_s` | 5 / 2 |
| `trabajadores` | Mac: mín(núcleos − 1, 4); nube: máx(1, vCPU − 1) |
| `memoria_trabajador_mb` | 1 536 |
| DuckDB por trabajador | `memory_limit=512MB`, `threads=1` |
| `max_tasks_per_child` | 200 |
| Cola | 2 × trabajadores; si se llena, 503 |
| Lectura por bloques | > 200 MB → 25 000 filas |
| Parquet | zstd 3; grupos de 122 880 filas |
| Recuperador | 50 por lista; RRF k = 60; de 10 a 20 candidatos; 128 tokens por texto |
| Planificador | 3 muestras; plazo de 9 s; 1 reintento; `max_tokens` 800 |
| Intérprete | tiempo máximo de 10 s |
| Batch API | lotes de ≤ 5 000 peticiones; `tope_lote_usd` 50 (propuesta) |
| `tope_llm_usd_dia` | 5 (propuesto) |
| `almacen.espacio_libre_min_gb` | 50 |
| Seguridad de dependencias | auditoría antes de entrar; `pip-audit` en verde; versiones con ≥ 2 semanas |

## 10. Fuentes

- **`svy`:** https://pypi.org/pypi/svy/json; CHANGELOG en github.com/samplics-org/svy.
- **R `survey`:** r-observatory (versiones); NEWS en r-forge.r-universe.dev/survey.
- **`pyreadstat`:** https://pypi.org/project/pyreadstat/; DuckDB COPY/Parquet en duckdb.org/docs.
- **Modelo e5:** https://huggingface.co/intfloat/multilingual-e5-small; arXiv 2402.05672 (mE5); arXiv 2402.03216 (BGE-M3).
- **`bm25s`:** https://github.com/xhluca/bm25s.
- **Extensiones de DuckDB:** duckdb.org/docs (FTS y VSS).
- **Anthropic:** documentación oficial de prompt caching, Batch API y precios.
- **Pool de procesos:** CPython issue 142317 (macOS y `RLIMIT`).
