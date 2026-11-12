# Auditoría de dependencia — modelo `ibm-granite/granite-embedding-97m-multilingual-r2`

Plantilla de M0-00b. **Historia:** M1-00 (tarea 8) y M1-09b (tarea 2) · **Fecha:** 12/11/2026 · **Quién la hizo:** agente (consultas a la API de Hugging Face; no se bajó ningún peso del modelo, solo `tokenizer.json` y JSON chicos para medir y calcular huellas, en una carpeta temporal)

## 1. Qué es y por qué entra
- **Qué hace y para qué lo usamos:** igual que e5-small (vectores para la búsqueda por significado), con 384 dimensiones. Es el **candidato a reemplazo** de e5-small en el banco de M1-09b; la ficha informa 60,3 en recuperación multilingüe frente a 50,9 de e5-small (cifras de los autores, no medidas en español).
- **Alternativa sin dependencia nueva:** quedarse con e5-small (ya auditado).
- **Dónde se usa:** `src/pap/inferencia/` (embeddings, parámetro `recuperador.modelo`) y el banco `pap variables evaluar-recuperador --banco`.

## 2. Origen y antigüedad
| Comprobación | Resultado |
|---|---|
| Fuente única y oficial | Sí. `https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2` |
| **Commit que se fija** | **`835ad14087e140460703cf0fae09f97d469d65c2`** (fecha: 18/5/2026; 178 días; es la punta de `main` al 12/11/2026) |
| Versión fijada y con hash | Por commit y SHA-256, en §3 |
| Versión retirada / repo desactivado, privado o con acceso restringido | No (`gated: false`, `private: false`, `disabled: false`) |
| Mantenedor y repositorio público | IBM (organización `ibm-granite`; 4 commits desde el 20/4/2026; los modelos R2 se anunciaron el 14/5/2026). 160 mil descargas. Artículo arXiv 2605.13521 |
| Licencia compatible | Apache 2.0 (permite uso comercial). Compatible; no choca con F-04 ni F-05 |

## 3. Qué trae y qué se descarga
- **Código remoto (`trust_remote_code`):** no. Sin archivos `.py`; `config.json` sin `auto_map`; arquitectura estándar `ModernBertModel`.
- **ONNX oficial:** sí, `onnx/model.onnx` (fp32, 390 004 608 bytes, un solo archivo; sin `.onnx_data`). Variante cuantizada (**no se pide**): `onnx/model_quint8_avx2.onnx` (98 MB, para x86 con AVX2; no sirve en el Mac).
- **El tokenizador está en la raíz** (`tokenizer.json`), no en `onnx/`.

**Archivos que baja el dueño** (carpeta `biblioteca/cruda/bandeja/hf-granite-embedding-97m-multilingual-r2/`, conservando las subcarpetas; total 415.322.232 bytes). Las huellas de los archivos grandes son el `oid` de Git LFS (que es el SHA-256); las de los chicos las calculé yo bajando el archivo.

| Archivo | Bytes | SHA-256 | URL (fija al commit) |
|---|---|---|---|
| `onnx/model.onnx` | 390004608 | `68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70` | https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/onnx/model.onnx |
| `tokenizer.json` | 25301672 | `4f2842d568e2724370aec203652a42ac783c7937f8347a1a2cc7506d71f1582f` | https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/tokenizer.json |
| `tokenizer_config.json` | 12860 | `6ed69389e30a8ecabfce2f9ebcdf0c908b34056f24d994340f2f216521c057d5` | https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/tokenizer_config.json |
| `special_tokens_map.json` | 871 | `013787ee251ff611722479197c00853b62113ad303cb0a36524231783c676c69` | https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/special_tokens_map.json |
| `config.json` | 1216 | `de948b0bdc6f356afad7a84b276d8dd7e7fe10fb9add1bb5e610621c28e41ebc` | https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/config.json |
| `1_Pooling/config.json` | 313 | `8bc5c9a40814fcf48d2fbe7cfeff4bee6736c3c2a823ba0ce098985c59d12ab7` | https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/1_Pooling/config.json |
| `modules.json` | 349 | `84e40c8e006c9b1d6c122e02cba9b02458120b5fb0c87b746c41e0207cf642cf` | https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/modules.json |
| `sentence_bert_config.json` | 60 | `967ef958285e4a7a37d8ff1832473d967edd913b4e48572f31c3d3ea361d5327` | https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/sentence_bert_config.json |
| `config_sentence_transformers.json` | 283 | `93a59cbc7d82a47a7148719d9b21c0f2f111121e495b3918143184f4cd0ea25e` | https://huggingface.co/ibm-granite/granite-embedding-97m-multilingual-r2/resolve/835ad14087e140460703cf0fae09f97d469d65c2/config_sentence_transformers.json |

**Datos para `recuperador.modelo`:**
| Dato | Valor |
|---|---|
| Dimensiones | 384 |
| Largo máximo | 32 768 tokens (`max_position_embeddings`, `sentence_bert_config.json`); en nuestro uso se limita (128–512) activando el truncado en el código, porque el `tokenizer.json` trae truncado a 32 768 |
| Prefijos | **ninguno**: `prompts.query` y `prompts.document` vacíos en `config_sentence_transformers.json` |
| Agregación | **vector CLS** (primer token), y luego normalización L2 (`1_Pooling/config.json`, `modules.json`; la ficha: «uses CLS Pooling») |
| Tokenizador | BPE, 179 934 piezas y 413 540 reglas de fusión; relleno con `<|endoftext|>` (id 179 935) |
| Matryoshka | **no** (la ficha lo marca «—» para este modelo) |

## 4. Vulnerabilidades conocidas
| Fuente | Cómo se consultó | Resultado |
|---|---|---|
| OSV / GitHub Advisories / `pip-audit` | no aplican a un modelo (no son paquetes de PyPI) | — |
| Código remoto | árbol del commit (`/tree/835ad14087e140460703cf0fae09f97d469d65c2?recursive=true`): sin ningún `.py`; `config.json` sin `auto_map` | **ninguno** |
| Formatos con `pickle` | el repo trae solo `model.safetensors` (formato seguro, sin `pickle`; no se descarga) y OpenVINO; **no se descargan** | no se alcanzan |
| Firma | trae `model.sig` (firma de modelo, 11 884 bytes). **No la verifiqué** (haría falta una herramienta de firma que no está en el proyecto y no se agregan dependencias). La integridad se asegura con el SHA-256 por commit | — |
| Si aparece algo: ¿se alcanza? | no hay hallazgos | |

## 5. Condiciones de uso
1. Se descargan **solo** los archivos de la tabla de §3, por la URL con el commit. Nunca `pytorch_model.bin` ni otros `.bin`, `.pt`, `.pkl` (formatos con `pickle`); nunca `from_pretrained` ni `trust_remote_code` (control C6).
2. Cada archivo se verifica con `shasum -a 256 -c SHA256SUMS` al bajarlo, de nuevo en `pap registrar` (queda en `datapackage.json` junto con el commit) y antes de cargarlo (C10). Si cambia una huella, se recalculan todos los vectores.
3. `onnxruntime` solo con `CPUExecutionProvider`, sin operadores personalizados, el modelo desde bytes ya verificados (`auditoria_onnxruntime.md`).
4. `tokenizers` con `Tokenizer.from_file` sobre el `tokenizer.json` verificado (`auditoria_tokenizers.md`). Los `.json` de configuración **no los carga ningún código de terceros**: los lee nuestro código para fijar `recuperador.modelo` (dimensiones, agregación, prefijos, longitud).
5. `HF_HUB_OFFLINE=1`; las pruebas corren sin red.
6. **No verificado desde aquí** (hace falta abrir el ONNX; no bajé pesos): los nombres de entradas y salidas del grafo y si la salida ya trae el vector agregado o solo los vectores por token. M1-09b lo comprueba al primer arranque: entradas esperadas `input_ids` y `attention_mask` (ModernBERT no usa `token_type_ids`); si la salida son vectores por token, el código aplica CLS y L2. Si el grafo pide un operador personalizado, no carga y el modelo queda fuera.

## 6. Veredicto
**aprobado con condiciones** (las de §5). Sin código remoto, licencia Apache 2.0, ONNX oficial en un solo archivo, commit con 178 días.
- **Revisión siguiente:** al cerrar el banco de M1-09b (si no gana, se descarta), o si cambia el commit.
