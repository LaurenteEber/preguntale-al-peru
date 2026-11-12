# Auditoría de dependencia — modelo `ibm-granite/granite-embedding-311m-multilingual-r2`

Plantilla de M0-00b. **Historia:** M1-00 (tarea 8) y M1-09b (tarea 2) · **Fecha:** 12/11/2026 · **Quién la hizo:** agente (consultas a la API de Hugging Face; no se bajó ningún peso del modelo, solo `tokenizer.json` y JSON chicos para medir y calcular huellas, en una carpeta temporal)

## 1. Qué es y por qué entra
- **Qué hace y para qué lo usamos:** igual que los otros, con 768 dimensiones (truncables). Es el **techo de calidad** del banco de M1-09b (la ficha informa 65,2 en recuperación multilingüe; cifra de los autores). Solo se adopta si supera por 5 puntos o más al mejor modelo pequeño (regla de M1-09b).
- **Alternativa sin dependencia nueva:** granite-97m-r2 o e5-small.
- **Dónde se usa:** `src/pap/inferencia/` (parámetro `recuperador.modelo`) y el banco de M1-09b, a 768 y truncado a 256 dimensiones.

## 2. Origen y antigüedad
| Comprobación | Resultado |
|---|---|
| Fuente única y oficial | Sí. `https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2` |
| **Commit que se fija** | **`44399559930365213510b1ee2eb15ded83374f0e`** (fecha: 18/5/2026; 178 días; es la punta de `main` al 12/11/2026) |
| Versión fijada y con hash | Por commit y SHA-256, en §3 |
| Versión retirada / repo desactivado, privado o con acceso restringido | No (`gated: false`, `private: false`, `disabled: false`) |
| Mantenedor y repositorio público | IBM (organización `ibm-granite`; 3 commits desde el 20/4/2026; ficha con arXiv 2605.13521). 84 mil descargas |
| Licencia compatible | Apache 2.0. Compatible; no choca con F-04 ni F-05 |

## 3. Qué trae y qué se descarga
- **Código remoto (`trust_remote_code`):** no. Sin archivos `.py`; `config.json` sin `auto_map`; arquitectura estándar `ModernBertModel`.
- **ONNX oficial:** sí, `onnx/model.onnx` (fp32, **1 247 170 481 bytes**, un solo archivo; sin `.onnx_data`). Variante cuantizada (**no se pide**): `onnx/model_quint8_avx2.onnx` (313 MB, x86 con AVX2).
- **Peso en memoria:** el archivo pesa 1,25 GB; al cargarlo desde bytes verificados hay un pico de unos 2,5 GB (los bytes más el modelo). El Mac del dueño debe tener memoria libre; es parte de lo que mide el banco (memoria con el modelo cargado).
- **El tokenizador está en la raíz** (`tokenizer.json`).

**Archivos que baja el dueño** (carpeta `biblioteca/cruda/bandeja/hf-granite-embedding-311m-multilingual-r2/`, conservando las subcarpetas; total 1.281.713.692 bytes). Las huellas de los archivos grandes son el `oid` de Git LFS (que es el SHA-256); las de los chicos las calculé yo bajando el archivo.

| Archivo | Bytes | SHA-256 | URL (fija al commit) |
|---|---|---|---|
| `onnx/model.onnx` | 1247170481 | `75f9f258bf5013f5fe8a4dad61dd0fd16ac0cbaa7a106e3d3f41c2d04a42d541` | https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/onnx/model.onnx |
| `tokenizer.json` | 33384821 | `0087c868b33bad550a78a08d19798cfd7f713cde4f020803b8f51f405503e15f` | https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/tokenizer.json |
| `tokenizer_config.json` | 1155500 | `7947bdf0378520e69ca412b8c4dacd1cffa8aef099f851fdd5c65aa27c6b36a0` | https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/tokenizer_config.json |
| `special_tokens_map.json` | 694 | `cb9e60dcf4d8d314315cb3e761fe4c2e664fda8dbf66d7815372b2639e381182` | https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/special_tokens_map.json |
| `config.json` | 1191 | `e1e3fc842a8e0537e25d6e4c93879698b92ae96722e8c162bef334b57978a3b0` | https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/config.json |
| `1_Pooling/config.json` | 313 | `781299da695e58439d70d491840da22ea0935d1d57d9646eb9725f1f19754e89` | https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/1_Pooling/config.json |
| `modules.json` | 349 | `84e40c8e006c9b1d6c122e02cba9b02458120b5fb0c87b746c41e0207cf642cf` | https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/modules.json |
| `sentence_bert_config.json` | 60 | `967ef958285e4a7a37d8ff1832473d967edd913b4e48572f31c3d3ea361d5327` | https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/sentence_bert_config.json |
| `config_sentence_transformers.json` | 283 | `f09adf93fcf868bb2fc3976a435d810b2ecdffa953d1da091d2a91168abab44b` | https://huggingface.co/ibm-granite/granite-embedding-311m-multilingual-r2/resolve/44399559930365213510b1ee2eb15ded83374f0e/config_sentence_transformers.json |

**Datos para `recuperador.modelo`:**
| Dato | Valor |
|---|---|
| Dimensiones | 768 (completo) |
| Matryoshka | **sí**, según la ficha: 768, 512, 384, 256 y 128 «con degradación suave». Truncar a **256** está soportado: se toman las primeras 256 componentes del vector de 768 y **se vuelve a normalizar con L2** (el ejemplo de la ficha, `truncate_dim=256`, trunca; la re-normalización la hace nuestro código) |
| Largo máximo | 32 768 tokens; en nuestro uso se limita (128–512) activando el truncado en el código |
| Prefijos | **ninguno** (`prompts` vacíos) |
| Agregación | **vector CLS** y luego L2 (ficha: «uses CLS Pooling») |
| Tokenizador | BPE, 262 144 piezas y 514 906 reglas |
| Nota | `tokenizer_config.json` pesa 1,1 MB (es el único archivo chico grande; no es LFS) |

## 4. Vulnerabilidades conocidas
| Fuente | Cómo se consultó | Resultado |
|---|---|---|
| OSV / GitHub Advisories / `pip-audit` | no aplican a un modelo (no son paquetes de PyPI) | — |
| Código remoto | árbol del commit (`/tree/44399559930365213510b1ee2eb15ded83374f0e?recursive=true`): sin ningún `.py`; `config.json` sin `auto_map` | **ninguno** |
| Formatos con `pickle` | el repo trae solo `model.safetensors` (formato seguro; no se descarga) y OpenVINO; **no se descargan** | no se alcanzan |
| Firma | trae `model.sig` (11 953 bytes). **No la verifiqué** (sin herramienta de firma en el proyecto). La integridad se asegura con el SHA-256 por commit | — |
| Si aparece algo: ¿se alcanza? | no hay hallazgos | |

## 5. Condiciones de uso
1. Se descargan **solo** los archivos de la tabla de §3, por la URL con el commit. Nunca `pytorch_model.bin` ni otros `.bin`, `.pt`, `.pkl` (formatos con `pickle`); nunca `from_pretrained` ni `trust_remote_code` (control C6).
2. Cada archivo se verifica con `shasum -a 256 -c SHA256SUMS` al bajarlo, de nuevo en `pap registrar` (queda en `datapackage.json` junto con el commit) y antes de cargarlo (C10). Si cambia una huella, se recalculan todos los vectores.
3. `onnxruntime` solo con `CPUExecutionProvider`, sin operadores personalizados, el modelo desde bytes ya verificados (`auditoria_onnxruntime.md`).
4. `tokenizers` con `Tokenizer.from_file` sobre el `tokenizer.json` verificado (`auditoria_tokenizers.md`). Los `.json` de configuración **no los carga ningún código de terceros**: los lee nuestro código para fijar `recuperador.modelo` (dimensiones, agregación, prefijos, longitud).
5. `HF_HUB_OFFLINE=1`; las pruebas corren sin red.
6. **No verificado desde aquí:** igual que en granite-97m-r2, los nombres de entradas y salidas del grafo y si la salida ya trae el vector agregado. Se comprueba al primer arranque en M1-09b.

## 6. Veredicto
**aprobado con condiciones** (las de §5). Sin código remoto, licencia Apache 2.0, ONNX oficial, commit con 178 días.
- **Revisión siguiente:** al cerrar el banco de M1-09b, o si cambia el commit.
