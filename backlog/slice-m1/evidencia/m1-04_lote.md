# M1-04 — Lote con el LLM (Batch API): estado, costo y cómo reanudarlo

Fecha: 12/11/2026, corrida en vivo el 13/11/2026 · Quién: agente · C-M1-04-1 resuelta por el dueño (Workspace `pap-lotes`, clave en el Llavero, servicio `pap-anthropic-batch`).

## 0. Corrida en vivo de prueba (13/11/2026): RECH6, REC43 y REC0111

Comando (la clave se carga solo en el comando, desde el Llavero; nunca se imprimió ni se escribió en un archivo):
`PAP_ANTHROPIC_BATCH_KEY="$(security find-generic-password -s pap-anthropic-batch -w)" uv run pap cuestionarios lote --tablas RECH6,REC43,REC0111`

| Pasada | Lote | Peticiones | Costo máximo estimado | **Costo real** | Borrado |
|---|---|---|---|---|---|
| vincular | `msgbatch_019hZZCKRYGisxYRPK9rBNPe` | 271 | US$ 0,887 | **US$ 1,104** | sí |
| verificar | `msgbatch_01K4zpsXzbCKXvwo86fGWw41` | 42 | US$ 0,047 | **US$ 0,035** | sí |
| **Total** | | | | **US$ 1,139** | |

- **Borrado confirmado en Anthropic:** después de la corrida, `GET /v1/messages/batches/<id>` devuelve **404 `not_found_error`** para los dos lotes, y el listado del Workspace devuelve **0 lotes**.
- **El máximo estimado no fue un techo:** se midieron 0,58 tokens de entrada por carácter (1 038 426 tokens para 1 791 145 caracteres), no 0,45. El tope (US$ 20) no cambió; se subió `batch.tokens_por_caracter` a **0,65**, para que la revisión del tope antes de crear un lote vuelva a ser conservadora. Con 0,65, el máximo de todo lo pendiente sube a unos US$ 14, todavía bajo los US$ 20 por lote.
- **Resultado: solo 25 de 271 variables vinculadas por el LLM** (REC43 16, REC0111 9, RECH6 0). La causa principal no es el modelo eligiendo mal: **207 respuestas (76 %) vinieron en prosa** («La variable H37A … corresponde a la opción C…») en vez del JSON pedido, se cortaron en los 60 tokens de `max_tokens_vincular` y el código las descartó como `respuesta_invalida` (como debe: nunca se adivina un vínculo). Otras: `no_encontrada` 22, `error_del_lote` 12 (respuesta de verificación ilegible), `rechazada_por_verificacion` 5.
- **Primera corrida (sin salida estructurada):** el modelo respondió en prosa en 207 de 271 casos; se apartó en `lote_previos/20261113_prosa/` (fuera de git, no se borró).

### 0.1 Segunda corrida, con salida estructurada (13/11/2026, con el visto del dueño)

`batch.salida_estructurada: true`; mismas 271 variables.

| Pasada | Lote | Peticiones | Costo máximo estimado (0,65 tokens/carácter) | **Costo real** | Borrado |
|---|---|---|---|---|---|
| vincular | `msgbatch_01PeextaAcja6vgCmwMt1Kof` | 271 | US$ 1,246 | **US$ 1,104** | sí |
| verificar | `msgbatch_01V8qnX77CyWtnNtFXYiVn4C` | 163 | US$ 0,222 | **US$ 0,145** | sí |
| **Total** | | | | **US$ 1,249** | |

- **Borrado confirmado en Anthropic:** `GET` de los dos lotes → 404 `not_found_error`; el Workspace lista 0 lotes. Gasto acumulado de las dos corridas: **US$ 2,39** (de los US$ 30 del mes).
- **Las 271 respuestas vinieron en JSON** (163 eligieron una candidata, 108 dijeron «ninguna»). El máximo estimado ya fue un techo en las dos pasadas.
- **59 vinculadas** (REC43 41, REC0111 15, RECH6 3); `no_encontrada` 108; **`rechazada_por_verificacion` 104** (REC43 91).
- **Las rechazadas son, en buena parte, vínculos correctos:** en una muestra de 14, la mayoría eran respuestas de opción múltiple bien elegidas (H37M «Tomó ibuprofeno» → 471B «¿Qué le dieron para tratar la fiebre o la tos?»; H32T «curandero» → 469D «¿Dónde buscó consejo o tratamiento?»; H15J → 473D). Causa probable: la pasada de verificación muestra solo las primeras 8 opciones (`batch.opciones_en_prompt`) y su instrucción pide «mismo ítem»; si la opción de la variable (ibuprofeno, curandero) no está entre esas 8, el revisor dice que no. Es un error del lado seguro (nunca un vínculo falso), pero deja sin vincular casi todas las variables de opción múltiple.
- **Propuesta antes del lote completo:** en la verificación, mostrar todas las opciones de la pregunta (hasta `cuestionarios.opciones_max`) y decir que una variable que es una opción de una pregunta de respuesta múltiple sí coincide con esa pregunta; repetir REC43 (≈ US$ 0,6) para medir. Nada se aplicó como `revisado`: todo sigue en `propuesto`.

## 0.2 Antes del lote completo (13/11/2026)

Medido sin LLM ni red (`m1-04_recall.py`; funciones `recall_de_candidatos` y `recall_de_muestra` de `cuestionarios_medicion.py`).

**Cambios hechos antes de correr nada más en vivo** (con prueba cada uno):

- *Hallazgo 2:* `ClienteLote.resultados` exige que la `results_url` que devuelve la API sea https y del mismo servidor que `batch.api_url` (sin usuario ni puerto distinto); si no, falla con `url_de_resultados_ajena` **antes** de llamar, sin la URL ni la clave en el error. Pruebas con 6 URL ajenas (`tests/interprete/test_llm_lote.py`).
- *Hallazgo 6:* un vínculo rechazado por la verificación guarda en `evidencia` la pregunta que eligió el modelo («pregunta elegida por el modelo y rechazada en la verificación: individual:413»); una verificación ilegible guarda también la pregunta elegida, y una respuesta inválida guarda lo que dijo el modelo (`vinculos_llm.parquet`).
- *Propuesta del dueño para la verificación:* `peticiones_verificar` muestra **todas** las opciones de la pregunta (hasta `cuestionarios.opciones_max`, 60) y `SISTEMA_VERIFICAR` dice que una variable que es una opción o ítem de una pregunta de respuesta múltiple sí coincide con ella; sigue «si dudas, responde false». `batch.opciones_en_prompt` (8) queda solo para las candidatas de la pasada de vincular (supuesto M1-04, anotado en el YAML). **No se repitió REC43 en vivo**: el efecto sobre los 104 rechazos solo se mide corriendo el lote.

**Hallazgo 7 — ¿está la pregunta correcta entre las 20 candidatas?**

| Conjunto | Variables | Con la pregunta entre las 20 | % |
|---|---|---|---|
| Vinculadas por la regla del código (pregunta conocida por el número del código) | 319 | 289 | **90,6 %** (con 30 candidatas, 293 = 91,8 %; con 40, igual) |
| Muestra de REC0111 con pregunta conocida por etiqueta y texto (lista abajo) | 14 | 11 | **78,6 %** |

La muestra de REC0111 son las V1xx y V009, V010, V012 cuya etiqueta del diccionario y cuya pregunta del cuestionario individual dicen lo mismo (se compararon a mano; no se agregó ninguna dudosa; se dejaron fuera las del hogar —V113 a V129—, las construidas —V011, V013, V133, V149— y V130, religión, sin pregunta en el cuestionario individual extraído). Puesto = lugar de la pregunta correcta entre todas las del cuestionario individual (1 = la más parecida):

| Variable | Pregunta | Puesto | ¿Entre las 20? |
|---|---|---|---|
| V009 (mes de nacimiento) | 105 | 48 | **no** |
| V010 (año de nacimiento) | 105 | 46 | **no** |
| V012 (edad actual) | 106 | 21 | **no** (por uno) |
| V103 | 102 | 2 | sí |
| V104 | 103 | 1 | sí |
| V105 | 104 | 1 | sí |
| V106 | 108 | 2 | sí |
| V107 | 108 | 1 | sí |
| V131 (etnicidad) | 119D | 5 | sí |
| V155 | 114 | 1 | sí |
| V156 | 114A | 1 | sí |
| V157, V158, V159 | 115, 116, 117 | 1 | sí |

**Por qué V009, V010 y V012 no llegan:** el recorte compara palabras (las primeras 5 letras). La etiqueta «Mes de nacimiento de la entrevistada» no comparte palabras con «¿En qué día, mes y año nació Ud.?» (solo «mes», que es de las más comunes), ni «Edad actual» con «¿Cuántos años cumplidos tiene?». Las dos preguntas existen y se extrajeron bien; falta el parecido de palabras. **El 90,6 % de la regla puede ser optimista:** esas 319 variables se vincularon porque su código lleva el número de pregunta; las que quedan para el LLM no lo llevan, y la muestra de REC0111 (sin número en el código) da 78,6 %. Con 14 variables la muestra es pequeña: es una señal, no una cifra. Con k = 30 o 40 no mejora gran cosa en el conjunto de la regla (91,8 %).

**Antes del lote completo, el dueño decide** si se acepta ese techo (las variables como V009/V010/V012 salen «ninguna» y quedan `no_encontrada`, el lado seguro) o si se mejora el recorte (por ejemplo, un sinónimo de «edad» y «nacimiento» o más candidatas, p. ej. 30). No se cambió `batch.candidatos_k`.

**Hallazgo 8 — costo real contra lo facturado.** El «costo real» de las tablas de arriba se calcula con los precios configurados (`interprete.precios_usd_por_millon` con el 50 % de descuento) y los tokens que devuelve la API; no es lo facturado.
- Primera corrida: calculado **US$ 1,14** (tabla de §0). Gasto facturado según la consola: (lo anota el dueño)
- Segunda corrida: calculado **US$ 1,25** (tabla de §0.1). Gasto facturado según la consola: (lo anota el dueño)
- Dónde mirarlo: consola de Anthropic, Workspace `pap-lotes`, gasto del mes. Si difiere de US$ 2,39 de forma apreciable, se corrigen los precios o el descuento antes del lote completo.

## 0.3 Tercera corrida: REC43 con la verificación arreglada (13/11/2026)

La verificación ve todas las opciones de la pregunta y acepta una opción de una pregunta de respuesta múltiple (`0c2f70c`). Corrida previa apartada en `lote_previos/20261113_estructurada/` (fuera de git).

| Pasada | Lote | Peticiones | Costo máximo estimado | **Costo real** | Borrado |
|---|---|---|---|---|---|
| vincular | `msgbatch_01CNazZFmvZ5a9yb14RgcNnx` | 165 | US$ 0,745 | **US$ 0,666** | sí |
| verificar | `msgbatch_01RQfNg1nd4A5MMC9TwPeavD` | 131 | US$ 0,224 | **US$ 0,157** | sí |
| **Total** | | | | **US$ 0,823** | |

Gasto facturado según la consola: (lo anota el dueño).

- **Borrado confirmado en Anthropic:** los dos lotes dan 404 `not_found_error`; el Workspace lista 0 lotes. Gasto calculado de las tres corridas: **US$ 3,21**.
- **REC43: de 41 a 89 vínculos;** `rechazada_por_verificacion` baja de 91 a 41; `no_encontrada` 34; `error_del_lote` 1. De los 41 vínculos anteriores, 40 se repiten con la misma pregunta, 1 pasó a sin pregunta y ninguno cambió de pregunta.
- **Muestra a ojo** (12 vínculos nuevos y 6 rechazos): los 12 vínculos son correctos (p. ej. H37A FanSIDAr → 471B; H12A hospital MINSA → 474A; H45 veces que le dieron zinc → 473F). Entre los rechazos quedan algunos que parecen correctos (H9 sarampión → 463; H13 sales de rehidratación → 473B) y otros razonables (H6D, día de la 2.ª dosis de polio → 457, una pregunta distinta del carné). El error sigue del lado seguro.
- **Qué corrida es cada vínculo (hallazgo 13, dueño 13/11/2026):** los vínculos de **RECH6 y REC0111** que hoy están aplicados vienen de la **2.ª corrida**, hecha **antes** de arreglar la verificación (la que mostraba solo 8 opciones); **solo REC43 se repitió** con la verificación arreglada. Las 13 rechazadas de RECH6 y REC0111 de esa corrida (104 − 91 de REC43) pueden incluir rechazos por la verificación vieja que la nueva habría aceptado. Se corregirán, si hace falta, cuando el lote completo repita esas dos tablas.
- **Aplicado al índice (propuesto):** se unieron los vínculos del LLM de RECH6 y REC0111 (2.ª corrida) con los de REC43 (3.ª), se reindexó (`pap variables indexar`), se aplicaron (`pap cuestionarios aplicar --sobre-indice`: 426 variables con texto de pregunta) y se regeneraron las fichas (`pap fichas generar`; `pap fichas validar` cumple las 8 reglas).

## 0.4 Sinónimos y revisión antes del lote completo (13/11/2026, decisiones del dueño)

Todo sin LLM ni red. Scripts: `m1-04_recall_sinonimos.py` (recall antes/después), `m1-04_coherencia.py` → `m1-04_coherencia.md`, `m1-04_costo_lote.py` (costo máximo). Pruebas: `tests/inferencia/test_m104_sinonimos_manuales.py` (15).

**Sinónimos en el recorte de candidatas (solo edad y fechas).** `cuestionarios.sinonimos` en `curados/inferencia/parametros.yaml` (`decision: "dueño 13/11/2026…"`): si la etiqueta de la variable lleva *edad*, se buscan también *años* y *cumplidos*; *nacimiento* ↔ *nació* (y *nacido*); *fecha* → *día*, *mes*, *año*. Solo amplían la consulta (las preguntas no cambian) y **`candidatos_k` sigue en 20**. «Antes» = la misma configuración sin ese bloque.

| Conjunto | Antes | Después |
|---|---|---|
| 319 vinculadas por regla (piso del dueño: 90,6 %) | 289 (**90,6 %**) | 290 (**90,9 %**) |
| 14 de REC0111 de §0.2 (la muestra que motivó los sinónimos) | 11 (78,6 %) | 14 (100 %) |
| **Muestra nueva** (18 variables, distintas de las 14) | 13 (**72,2 %**) | 15 (**83,3 %**) |

*La muestra de 14 no sirve para validar los sinónimos* (se miró para pedirlos); la de 18 es la medida honesta. Cómo se eligió: de las variables del diccionario con etiqueta de edad, nacimiento, día, mes, año o fecha se tomaron las que **no** están en las 14 y cuya pregunta se lee en el texto del cuestionario (la etiqueta y la pregunta dicen lo mismo); más 4 controles que no son de edad ni fechas (QS24, QS26, QS27, V702). Quedaron fuera por no ser seguras las construidas (REC21.B3, CMC), las fechas del carné de vacunas (REC43 H2D…, REC95) y casi todo lo que depende de la matriz del hogar. Lista y puestos en la salida de `m1-04_recall_sinonimos.py`. Mejoraron REC21.B8 (puesto 48 → 19, entra) y RECH1.HV105 (37 → 7, entra); QSDIA 7 → 1. **Siguen fuera REC21.BD, B1 y B2** (puestos 55, 43 y 38): su pregunta es el bloque extraído `individual:211` (historial de nacimientos, preguntas 212 a 219 en un solo texto largo), que por su longitud puntúa bajo. Con 20 candidatas no entran; es el techo conocido del recorte por palabras para los bloques largos (subir `candidatos_k` o separar el bloque en sus preguntas son las salidas, y ninguna se hizo).

**Hallazgo 10 (a): H44A → 474C a mano.** `curados/inferencia/vinculos_manuales.yaml` (cada entrada: tabla, codigo, pregunta `cuestionario:número`, motivo, quien, fecha). `pap cuestionarios aplicar` usa esos vínculos en lugar de los de la regla o del LLM (método `manual`, siguen en `propuesto`) y `pap cuestionarios lote` no manda esas variables al modelo. Una entrada incompleta, repetida, con pregunta mal escrita o con una variable que no está en los diccionarios falla. H44A: «Primer lugar buscado tratamiento para la diarrea» ↔ 474C «¿Dónde buscó usted primero consejo o tratamiento?»; el LLM la había enviado a 474A (todos los lugares). **Falta correr `pap cuestionarios aplicar --sobre-indice` y `pap fichas generar` para que el índice lo refleje** (no se hizo aquí: toca `variables.parquet`).

**Hallazgo 10 (b): H46A → 469F, revisado: el vínculo es correcto.** H46A «Lugar en el que se busca el tratamiento para la fiebre» (mismas 18 categorías de lugar que H44A); la 469F es «¿Dónde buscó primero consejo o tratamiento? ANOTE CÓDIGO REGISTRADO EN 469D» (fiebre o tos, el equivalente de 474C para la diarrea). Es coherente con la familia: H46B (días después) → 469G, igual que H44B → 474D. Hoy **H46A no está vinculada**: el LLM propuso 474A (una pregunta de diarrea, equivocada) y la verificación la rechazó, bien. Matiz: la 469F cubre fiebre *o tos*; la etiqueta del diccionario dice solo fiebre. **Propuesta:** el dueño la agrega a `vinculos_manuales.yaml` (una entrada igual a la de H44A); no la agregué porque la decisión fue solo para H44A.

**Hallazgo 10 (c): coherencia entre hermanas de REC43** (`m1-04_coherencia.md`): 18 familias de 3 o más variables; 8 marcadas. *Incompleta* (algunos miembros vinculados y otros no): **H12** (17 de 26 → 474A; 9 sin pregunta: H12D, E, N, R, S, U, X por rechazo; Y, Z), **H32** (16 de 26 → 469D; 10 sin pregunta, casi todas rechazadas), **H37** (13 de 19 → 471B; 6 rechazadas) y H2, H33, H40 (fechas de vacunas). *Mezcla* (preguntas distintas): H31 y H44, que son secuencias de preguntas distintas y están bien; **H33** (H33 → 465, H33D/H33Y → 456X, H33M rechazada) sí merece mirarse. Las familias **H12, H32 y H37 (y H15, que apunta entera a 473D)** son las que el lote completo de REC43 debería cerrar: sus miembros rechazados son opciones de la misma pregunta que sus hermanos. Ninguna se corrigió: es lista de trabajo para el dueño.

**Costo máximo del lote completo pendiente** (`m1-04_costo_lote.py`: mismas peticiones y `costo_maximo_usd` que el lote, 0,65 tokens por carácter; excluye vinculadas por regla, diccionario, administrativas, construidas y la manual):

| Alcance | Variables | Peticiones pasada 1 | Peticiones pasada 2 (peor caso) | Máximo |
|---|---|---|---|---|
| Todas las pendientes (incluye las 270 de RECH6, REC43 y REC0111 que ya pasaron por el LLM) | 2 324 | 2 324 | 2 324 | pasada 1 US$ 10,36 + pasada 2 US$ 4,37 = **US$ 14,72** |
| Sin esas 270 (lote con `--tablas` de las otras 31) | 2 054 | 2 054 | 2 054 | US$ 9,11 + US$ 3,87 = **US$ 12,98** |

Cada lote queda bajo el tope de US$ 20. El real fue ~89 % del máximo en la pasada 1 y ~65–70 % en la 2 (en la pasada 2 solo se verifican las que el modelo eligió: 60 % en la 2.ª corrida). **Ojo:** `pap cuestionarios lote` sin `--tablas` vuelve a mandar las 270 ya hechas y reescribe `vinculos_llm.parquet`; además la carpeta `lote/` guarda el estado de la corrida de las 3 tablas y el código se niega a mezclarlo (`el estado guardado … es de otra corrida`). Para el lote completo hay que apartar `lote/` (como en las corridas anteriores) y decidir si se repiten esas 270 (≈ US$ 1,7 de máximo, y arreglaría lo del hallazgo 13) o se hace por tablas.

## 1. Por qué no se llamó a la Batch API

La auditoría (`auditoria_batch_api.md`, condición 1) exige una **clave y un Workspace aparte** del servicio web, solo para los lotes. Se revisó, sin mostrar ningún valor:

- el cliente del LLM (`src/pap/interprete/llm.py`) solo lee la variable del servicio web (`interprete.variable_clave`);
- en la configuración del proyecto no había **ninguna** variable para la clave de lotes (ni en `parametros_motor.yaml`, ni en `curados/inferencia/parametros.yaml`, ni en el `justfile` o el `Dockerfile`);
- en el entorno de esta sesión no existe ninguna variable con ese propósito.

Reutilizar la clave del servicio web habría roto la condición 1, así que **no se llamó a nada**. Lo que sí quedó listo:

- `batch.variable_clave` en `curados/inferencia/parametros.yaml`: nombre propuesto `PAP_ANTHROPIC_BATCH_KEY` (supuesto M1-04). El dueño crea la clave en un Workspace aparte de la consola de Anthropic y la pone con ese nombre en su entorno o su Llavero; nunca en un archivo del repo.
- `ClienteLote` (`src/pap/interprete/llm.py`): se niega a correr sin esa clave (`sin_clave_lote`) y también si el nombre de la variable fuera el del servicio web (`clave_compartida`). Prueba: `tests/interprete/test_llm_lote.py`.
- `pap cuestionarios lote` revisa que la variable exista **antes de hacer nada** y, si falta, lo dice y termina sin llamar.

## 2. Costo (estimado, no real)

Costo máximo calculado con los textos reales (precios de Sonnet 5.5 con el 50 % de descuento de la Batch API; entrada estimada por caracteres con margen; salida al máximo de tokens):

| Alcance | Variables | Pasada 1 (vincular) | Pasada 2 (verificar), peor caso | Total máximo |
|---|---|---|---|---|
| RECH6, REC43 y REC0111 | 271 | US$ 0,88 | US$ 0,33 | **≈ US$ 1,2** |
| Todas las pendientes de las 34 tablas | 2 339 | US$ 7,22 | US$ 2,83 | **≈ US$ 10** |

Cada pasada es un lote y el tope `batch.tope_lote_usd` (US$ 20) se revisa **antes de crear** cada uno: si el máximo lo pasa, el lote no se crea (prueba `test_un_lote_que_pasa_el_tope_no_se_crea`). El costo real queda en `estado_lote.json` (campo `gasto_usd`): **US$ 1,139 en la corrida de prueba del 13/11/2026** (sección 0). Esta tabla es la estimación original con 0,45 tokens por carácter.

## 3. Cómo se corre cuando exista la clave

```
PAP_ANTHROPIC_BATCH_KEY="$(security find-generic-password -s pap-anthropic-batch -w)" uv run pap cuestionarios lote --tablas RECH6,REC43,REC0111
PAP_ANTHROPIC_BATCH_KEY="$(security find-generic-password -s pap-anthropic-batch -w)" uv run pap cuestionarios lote   # después, todo lo pendiente
uv run pap cuestionarios aplicar && uv run pap cuestionarios informe
```

Si el proceso se corta, se vuelve a correr **el mismo comando**: retoma el lote ya creado (no crea otro), baja solo lo que falte y borra el lote en Anthropic al final. Si el borrado falla, el comando termina con error y la siguiente corrida solo repite el borrado.

## 4. Lo que se probó (proveedor falso, sin red ni clave)

`tests/inferencia/test_m104_lote.py` (8 pruebas) y `tests/interprete/test_llm_lote.py` (8 pruebas):

| Comportamiento | Prueba |
|---|---|
| Dos lotes (vincular y verificar); ambos borrados; costo guardado | `test_el_lote_completo_vincula_verifica_y_borra_los_dos_lotes` |
| El `batch_id` ya está guardado cuando muere la consulta de estado; la reanudación no crea otro lote | `test_el_batch_id_queda_guardado_antes_de_consultar_el_estado_y_la_corrida_se_reanuda` |
| **Corte a la mitad** de la descarga de resultados (1 de 3): no se borra el lote; al reanudar sin duplicados y con el mismo resultado que una corrida entera | `test_si_se_corta_a_la_mitad_de_los_resultados_la_reanudacion_da_lo_mismo_que_una_corrida_entera` |
| Falla el borrado: no se da por terminado; la reanudación solo borra | `test_si_falla_el_borrado_el_trabajo_no_se_da_por_terminado_y_la_reanudacion_solo_borra` |
| Un lote sobre el tope no se crea | `test_un_lote_que_pasa_el_tope_no_se_crea` |
| Un ID que el modelo inventa vale «ninguna», nunca un vínculo | `test_un_id_que_el_modelo_inventa_…` |
| Sin secretos en los archivos; estado de otra corrida no se mezcla | `test_las_peticiones_solo_llevan_…`, `test_el_estado_de_otra_corrida_…` |
| Cliente HTTP: forma de las peticiones, estado, resultados, borrado, sin clave, sin filtrar la clave en errores | `tests/interprete/test_llm_lote.py` |

**RED y GREEN:** las pruebas de lote, de `ClienteLote` y de la puerta de publicación (`texto_publicable`) se escribieron antes del código y se vio el rojo (módulo o clase inexistente) antes de implementar. **Excepción honesta:** en las piezas de extracción y medición (`test_m104_parquet.py`, `test_m104_medicion.py`, la parte de matrices de `test_m104_pdf.py`) el código se escribió antes que la prueba, así que para ellas no hay rojo observado; sí quedaron probadas en verde.

## 5. Lo que el LLM puede y no puede hacer aquí

- Solo elige entre IDs de una lista (c01…c20) o dice «ninguna»; el código descarta cualquier ID que no esté en la lista.
- Una segunda llamada verifica; sin las dos, no hay vínculo.
- Todo vínculo queda `propuesto`. Ningún texto de pregunta entra a una respuesta pública: `indice.texto_publicable` solo lo entrega si la variable está `revisado` o `verificado`, y una prueba vigila que `motor/`, `web/` e `interprete/` no lean esos campos.
- Solo viajan textos públicos (etiquetas, categorías y preguntas de los cuestionarios oficiales). Nunca microdatos.

## 6. Pendiente

Ver `m1-04_vinculos.md`: sin el lote, las variables de las recetas no llegan al 95 % de texto vinculado (la meta de `tecnologias.md` §6 queda **sin medir**, no incumplida).
