# Auditoría de dependencia — modelo `intfloat/multilingual-e5-small`

Plantilla de M0-00b. **Historia:** M1-00 (tarea 8) y M1-09b (tarea 2) · **Fecha:** 12/11/2026 · **Quién la hizo:** agente (consultas a la API de Hugging Face; no se bajó ningún peso del modelo, solo `tokenizer.json` y JSON chicos para medir y calcular huellas, en una carpeta temporal)

## 1. Qué es y por qué entra
- **Qué hace y para qué lo usamos:** convierte las etiquetas y preguntas de las encuestas (y la consulta del usuario) en vectores de 384 números, para la búsqueda por significado de M1-09. Es la **línea base** del banco de M1-09b.
- **Alternativa sin dependencia nueva:** solo búsqueda por palabras; no encuentra preguntas parecidas con otras palabras.
- **Dónde se usa:** `src/pap/inferencia/` (embeddings). Aprobado por F-05 (stack) y ya auditado el 9/11/2026 (`backlog/slice-m0/evidencia/auditoria_seguridad_previa.md`).

## 2. Origen y antigüedad
| Comprobación | Resultado |
|---|---|
| Fuente única y oficial | Sí. `https://huggingface.co/intfloat/multilingual-e5-small` |
| **Commit que se fija** | **`614241f622f53c4eeff9890bdc4f31cfecc418b3`** (fecha: 2/4/2026; 224 días; es la punta de `main` al 12/11/2026) |
| Versión fijada y con hash | Por commit y SHA-256, en §3 |
| Versión retirada / repo desactivado, privado o con acceso restringido | No (`gated: false`, `private: false`, `disabled: false`) |
| Mantenedor y repositorio público | Liang Wang et al. (Microsoft / `intfloat`); 9,4 millones de descargas; artículo arXiv 2402.05672. **El commit es el mismo que fijó la auditoría previa y sigue existiendo, sigue siendo la punta de `main`.** Los dos últimos commits solo agregan resultados de evaluación; los pesos no cambian desde febrero de 2025 |
| Licencia compatible | MIT |

## 3. Qué trae y qué se descarga
- **Código remoto (`trust_remote_code`):** no. Sin archivos `.py` en el árbol; `config.json` sin `auto_map` (arquitectura estándar `BertModel`).
- **ONNX oficial:** sí, `onnx/model.onnx` (fp32, 470 268 510 bytes). Otras variantes (**no se piden**): `onnx/model_O4.onnx` (235 MB, optimizada), `onnx/model_qint8_avx512_vnni.onnx` (118 MB, solo para procesadores x86 con AVX-512, no sirve en el Mac). `tecnologias.md` §7: por defecto fp32.
- **Dos copias del tokenizador:** `tokenizer.json` está en la raíz y en `onnx/`, con la misma huella. Se usa la de `onnx/`, como en la auditoría previa.

**Archivos que baja el dueño** (carpeta `biblioteca/cruda/bandeja/hf-multilingual-e5-small/`, conservando las subcarpetas; total 487.353.147 bytes). Las huellas de los archivos grandes son el `oid` de Git LFS (que es el SHA-256); las de los chicos las calculé yo bajando el archivo.

| Archivo | Bytes | SHA-256 | URL (fija al commit) |
|---|---|---|---|
| `onnx/model.onnx` | 470268510 | `ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/model.onnx |
| `onnx/tokenizer.json` | 17082730 | `0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/tokenizer.json |
| `onnx/tokenizer_config.json` | 443 | `a1d6bc8734a6f635dc158508bef000f8e2e5a759c7d92f984b2c86e5ff53425b` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/tokenizer_config.json |
| `onnx/special_tokens_map.json` | 167 | `d05497f1da52c5e09554c0cd874037a083e1dc1b9cfd48034d1c717f1afc07a7` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/special_tokens_map.json |
| `onnx/config.json` | 653 | `bbb7c1333fc4b3e27fbc9cd5d2070aabcc1d4dfb99917c3633e772f97545a6b6` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/config.json |
| `1_Pooling/config.json` | 200 | `987f7a67a38fa564c849bb5d277c52ab9088a84368fc0be31a354125aebb12a0` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/1_Pooling/config.json |
| `modules.json` | 387 | `c6e29747481e8b5dd2b58401966aeac910de39092f90cda9a704b1545f902b04` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/modules.json |
| `sentence_bert_config.json` | 57 | `948201d8329907aae938fa62f9ceeed53f5694dacc2b87b9f3b78b37ee986529` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/sentence_bert_config.json |

**Datos para `recuperador.modelo`:**
| Dato | Valor |
|---|---|
| Dimensiones | 384 |
| Largo máximo | 512 tokens (`max_position_embeddings`, `model_max_length`); en nuestro uso se limita a 128 (tecnologias §7) |
| Prefijos | consulta: `query: ` · documento: `passage: ` (con el espacio; obligatorios) |
| Agregación | promedio de tokens (*mean pooling*) con la máscara de atención, y luego normalización L2 (`1_Pooling/config.json` y `modules.json`) |
| Tokenizador | Unigram (SentencePiece), 250 002 piezas en `tokenizer.json` |
| Matryoshka | no |

## 4. Vulnerabilidades conocidas
| Fuente | Cómo se consultó | Resultado |
|---|---|---|
| OSV / GitHub Advisories / `pip-audit` | no aplican a un modelo (no son paquetes de PyPI) | — |
| Código remoto | árbol del commit (`/tree/614241f622f53c4eeff9890bdc4f31cfecc418b3?recursive=true`): sin ningún `.py`; `config.json` sin `auto_map` | **ninguno** |
| Formatos con `pickle` | el repo trae `pytorch_model.bin` (470 681 649 bytes); **no se descargan** | no se alcanzan |
| Firma | no trae firma de modelo | — |
| Si aparece algo: ¿se alcanza? | no hay hallazgos | |

## 5. Condiciones de uso
1. Se descargan **solo** los archivos de la tabla de §3, por la URL con el commit. Nunca `pytorch_model.bin` ni otros `.bin`, `.pt`, `.pkl` (formatos con `pickle`); nunca `from_pretrained` ni `trust_remote_code` (control C6).
2. Cada archivo se verifica con `shasum -a 256 -c SHA256SUMS` al bajarlo, de nuevo en `pap registrar` (queda en `datapackage.json` junto con el commit) y antes de cargarlo (C10). Si cambia una huella, se recalculan todos los vectores.
3. `onnxruntime` solo con `CPUExecutionProvider`, sin operadores personalizados, el modelo desde bytes ya verificados (`auditoria_onnxruntime.md`).
4. `tokenizers` con `Tokenizer.from_file` sobre el `tokenizer.json` verificado (`auditoria_tokenizers.md`). Los `.json` de configuración **no los carga ningún código de terceros**: los lee nuestro código para fijar `recuperador.modelo` (dimensiones, agregación, prefijos, longitud).
5. `HF_HUB_OFFLINE=1`; las pruebas corren sin red.
6. Se mantiene la condición de la auditoría previa: «solo `onnx/model.onnx`, `onnx/tokenizer.json` y JSON chicos». Esta lista agrega `modules.json`, `sentence_bert_config.json` y `1_Pooling/config.json` solo para dejar en el registro cómo se agrega y normaliza.

## 6. Veredicto
**aprobado con condiciones** (las de §5). Las condiciones de `auditoria_seguridad_previa.md` **siguen vigentes**: mismo commit, misma licencia, sin código remoto. Las huellas quedan reconfirmadas contra la API de Hugging Face el 12/11/2026 (el `tokenizer.json` lo bajé y su SHA-256 coincide con el `oid` de LFS).
- **Revisión siguiente:** si cambia el commit o la versión de `onnxruntime`/`tokenizers`.
