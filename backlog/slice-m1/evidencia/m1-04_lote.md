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
