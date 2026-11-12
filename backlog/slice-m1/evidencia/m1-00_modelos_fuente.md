# M1-00 t9 / M1-09b t2 — Los tres modelos como fuentes del catálogo

**Fecha:** 12/11/2026 · **Quién:** agente · **Historias:** M1-00 tarea 9 (e5-small), M1-09b tarea 2 (Granite 97 M y 311 M).

## En sencillo
- Los tres modelos ya son **fuentes del catálogo** (`catalogo/catalogo_fuentes.{json,csv,md}`, generadas con `catalogo/scripts/run.py` + `render.py` desde `nuevas_fuentes.json`) y tienen **receta** de descarga manual en `curados/recetas/HF-*.yaml`: `HF-MULTILINGUAL-E5-SMALL`, `HF-GRANITE-EMBEDDING-97M-MULTILINGUAL-R2`, `HF-GRANITE-EMBEDDING-311M-MULTILINGUAL-R2`.
- Cada receta fija: editor, licencia (MIT / Apache-2.0), la página del modelo **en el commit fijado** (`access_url`), y la lista exacta de archivos con tamaño, SHA-256 y URL (en los `pasos` de la receta; la prueba comprueba que coinciden con `auditoria_modelos_lista_dueno.md`).
- `pap registrar` ahora acepta `.onnx` (tipo `application/octet-stream`, sin firma fija) y `.json`. Cualquier otro formato (`.safetensors`, `.bin`) se rechaza porque la receta solo espera `onnx` y `json`.
- En el catálogo quedan en la ola «fuera de alcance» (no son datos del país) y la compuerta de ingesta vacía; no bloquean el MVP.

## Cómo registrar los archivos que bajó el dueño
Primero verificar con el `SHA256SUMS` de cada carpeta. Los archivos se pasan **uno por uno** con su ruta (`pap registrar` solo lista la carpeta raíz de la bandeja, sin subcarpetas) y cada uno lleva su nombre de recurso y su URL con el commit. Desde la raíz del repositorio:


### `HF-MULTILINGUAL-E5-SMALL` — carpeta `biblioteca/cruda/bandeja/hf-multilingual-e5-small/`
```
uv run pap registrar HF-MULTILINGUAL-E5-SMALL biblioteca/cruda/bandeja/hf-multilingual-e5-small/onnx/model.onnx --recurso e5-small-onnx-model --url-descarga https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/model.onnx
uv run pap registrar HF-MULTILINGUAL-E5-SMALL biblioteca/cruda/bandeja/hf-multilingual-e5-small/onnx/tokenizer.json --recurso e5-small-onnx-tokenizer --url-descarga https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/tokenizer.json
uv run pap registrar HF-MULTILINGUAL-E5-SMALL biblioteca/cruda/bandeja/hf-multilingual-e5-small/onnx/tokenizer_config.json --recurso e5-small-onnx-tokenizer-config --url-descarga https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/tokenizer_config.json
uv run pap registrar HF-MULTILINGUAL-E5-SMALL biblioteca/cruda/bandeja/hf-multilingual-e5-small/onnx/special_tokens_map.json --recurso e5-small-onnx-special-tokens-map --url-descarga https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/special_tokens_map.json
uv run pap registrar HF-MULTILINGUAL-E5-SMALL biblioteca/cruda/bandeja/hf-multilingual-e5-small/onnx/config.json --recurso e5-small-onnx-config --url-descarga https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/config.json
uv run pap registrar HF-MULTILINGUAL-E5-SMALL biblioteca/cruda/bandeja/hf-multilingual-e5-small/1_Pooling/config.json --recurso e5-small-1-pooling-config --url-descarga https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/1_Pooling/config.json
uv run pap registrar HF-MULTILINGUAL-E5-SMALL biblioteca/cruda/bandeja/hf-multilingual-e5-small/modules.json --recurso e5-small-modules --url-descarga https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/modules.json
uv run pap registrar HF-MULTILINGUAL-E5-SMALL biblioteca/cruda/bandeja/hf-multilingual-e5-small/sentence_bert_config.json --recurso e5-small-sentence-bert-config --url-descarga https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/sentence_bert_config.json

### `HF-GRANITE-EMBEDDING-97M-MULTILINGUAL-R2` — carpeta `biblioteca/cruda/bandeja/hf-granite-embedding-97m-multilingual-r2/`
```
uv run pap registrar HF-GRANITE-EMBEDDING-97M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-97m-multilingual-r2/onnx/model.onnx --recurso granite-97m-onnx-model --url-descarga https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/onnx/model.onnx
uv run pap registrar HF-GRANITE-EMBEDDING-97M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-97m-multilingual-r2/tokenizer.json --recurso granite-97m-tokenizer --url-descarga https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/tokenizer.json
uv run pap registrar HF-GRANITE-EMBEDDING-97M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-97m-multilingual-r2/tokenizer_config.json --recurso granite-97m-tokenizer-config --url-descarga https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/tokenizer_config.json
uv run pap registrar HF-GRANITE-EMBEDDING-97M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-97m-multilingual-r2/special_tokens_map.json --recurso granite-97m-special-tokens-map --url-descarga https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/special_tokens_map.json
uv run pap registrar HF-GRANITE-EMBEDDING-97M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-97m-multilingual-r2/config.json --recurso granite-97m-config --url-descarga https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/config.json
uv run pap registrar HF-GRANITE-EMBEDDING-97M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-97m-multilingual-r2/1_Pooling/config.json --recurso granite-97m-1-pooling-config --url-descarga https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/1_Pooling/config.json
uv run pap registrar HF-GRANITE-EMBEDDING-97M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-97m-multilingual-r2/modules.json --recurso granite-97m-modules --url-descarga https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/modules.json
uv run pap registrar HF-GRANITE-EMBEDDING-97M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-97m-multilingual-r2/sentence_bert_config.json --recurso granite-97m-sentence-bert-config --url-descarga https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/sentence_bert_config.json
uv run pap registrar HF-GRANITE-EMBEDDING-97M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-97m-multilingual-r2/config_sentence_transformers.json --recurso granite-97m-config-sentence-transformers --url-descarga https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/config_sentence_transformers.json

### `HF-GRANITE-EMBEDDING-311M-MULTILINGUAL-R2` — carpeta `biblioteca/cruda/bandeja/hf-granite-embedding-311m-multilingual-r2/`
```
uv run pap registrar HF-GRANITE-EMBEDDING-311M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-311m-multilingual-r2/onnx/model.onnx --recurso granite-311m-onnx-model --url-descarga https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/onnx/model.onnx
uv run pap registrar HF-GRANITE-EMBEDDING-311M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-311m-multilingual-r2/tokenizer.json --recurso granite-311m-tokenizer --url-descarga https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/tokenizer.json
uv run pap registrar HF-GRANITE-EMBEDDING-311M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-311m-multilingual-r2/tokenizer_config.json --recurso granite-311m-tokenizer-config --url-descarga https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/tokenizer_config.json
uv run pap registrar HF-GRANITE-EMBEDDING-311M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-311m-multilingual-r2/special_tokens_map.json --recurso granite-311m-special-tokens-map --url-descarga https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/special_tokens_map.json
uv run pap registrar HF-GRANITE-EMBEDDING-311M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-311m-multilingual-r2/config.json --recurso granite-311m-config --url-descarga https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/config.json
uv run pap registrar HF-GRANITE-EMBEDDING-311M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-311m-multilingual-r2/1_Pooling/config.json --recurso granite-311m-1-pooling-config --url-descarga https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/1_Pooling/config.json
uv run pap registrar HF-GRANITE-EMBEDDING-311M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-311m-multilingual-r2/modules.json --recurso granite-311m-modules --url-descarga https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/modules.json
uv run pap registrar HF-GRANITE-EMBEDDING-311M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-311m-multilingual-r2/sentence_bert_config.json --recurso granite-311m-sentence-bert-config --url-descarga https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/sentence_bert_config.json
uv run pap registrar HF-GRANITE-EMBEDDING-311M-MULTILINGUAL-R2 biblioteca/cruda/bandeja/hf-granite-embedding-311m-multilingual-r2/config_sentence_transformers.json --recurso granite-311m-config-sentence-transformers --url-descarga https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/config_sentence_transformers.json

Notas: se puede añadir `--consultado AAAA-MM-DDThh:mm:ss-05:00` con la hora real de la descarga (si no, queda `retrieved_at` de la receta, 2026-11-12). No se usa `--mover` aquí para no tocar la bandeja hasta confirmar el registro.

## Qué se cambió
- `catalogo/scripts/nuevas_fuentes.json`: 3 fuentes nuevas. `catalogo/catalogo_fuentes.{json,csv,md}`: 418 → 421 fuentes (aplicado como diferencia del resultado de `run.py` + `render.py`; el catálogo publicado ya traía un cambio manual de `url_portal` de `INS-CENAN-…` que la regeneración completa habría revertido, y no se tocó). `catalogo/salidas/priorizacion.md` y `auditoria_estado.csv` quedan sin regenerar (fuera de lo permitido): conviene correr `render.py` completo en la próxima historia que toque el catálogo.
- `curados/recetas/HF-*.yaml`: 3 recetas `owner_file`.
- `src/pap/util.py`: `MEDIATYPES["onnx"]`. `src/pap/validacion.py`: sin cambios (el formato ya sale de la extensión y `espera.formato` decide).
- `tests/test_recetas_modelos_hf.py`: 11 pruebas.

## Pendiente (bloquea el verde completo)
El bloque `catalogo:` de las recetas copia `compuerta_ingesta` del catálogo, y para estas fuentes es `null` (solo las olas 0 y 1 la tienen). `src/pap/esquemas/receta.schema.json` exige `string`, así que las 3 recetas no pasan su esquema (y con ellas `test_todas_las_recetas_pasan_su_esquema`). Solución mínima, fuera de las rutas permitidas a este trabajo: en el esquema, `"compuerta_ingesta": {"type": ["string", "null"]}`.

## Pruebas
- RED (antes de las recetas y de `onnx`): `uv run pytest -q tests/test_recetas_modelos_hf.py` → 8 failed, 3 passed.
- Estado actual: `uv run pytest -q tests/test_recetas_modelos_hf.py` → 7 pasan, 4 fallan solo por el esquema descrito arriba. Con ese campo aceptando `null` (simulado en memoria con un plugin temporal): 11 passed.
- `uv run pytest -q tests/ -k "receta or catalogo or registrar or validacion"` → 5 failed (los 4 de arriba + `test_recetas_reales::test_todas_las_recetas_pasan_su_esquema`, mismo motivo), 105 passed.
- `test_catalogo.py` sobre el catálogo regenerado: pasa salvo `test_ingesta_verificada_al_dia`, que en la copia temporal no encuentra `biblioteca/`.
