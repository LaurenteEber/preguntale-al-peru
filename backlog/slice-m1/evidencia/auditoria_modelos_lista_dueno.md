# Lista exacta de archivos de modelos para el dueño (M1-09b, «Del dueño»)

**Fecha:** 12/11/2026 · **Quién la hizo:** agente · **Auditorías:** `auditoria_multilingual_e5_small.md`, `auditoria_granite_97m_r2.md`, `auditoria_granite_311m_r2.md` (las tres «aprobado con condiciones»; la de `bekko` quedó fuera).

## En sencillo
- Son **tres modelos**, 26 archivos en total (8 + 9 + 9), unos **2,2 GB** (el de 311 M pesa 1,25 GB solo).
- Cada modelo va en **su propia carpeta** dentro de `biblioteca/cruda/bandeja/`, y los archivos conservan sus subcarpetas (`onnx/`, `1_Pooling/`).
- Se baja **por la URL con el commit** (no por `main`), así que el archivo no cambia aunque el autor publique algo nuevo.
- **Nunca** bajes `pytorch_model.bin`, `model.safetensors`, `openvino*` ni los `.onnx` cuantizados: no se usan.
- Después de bajar cada modelo, verifica con el bloque `SHA256SUMS` de su sección. Si una línea dice `FAILED`, borra ese archivo y avísame: no se registra.
- Si falta alguno, el banco corre con los que haya (M1-09b).
- Todos los modelos son de licencia **MIT** (e5-small) o **Apache 2.0** (Granite): permiten uso comercial. Ninguno trae código que se ejecute al cargarlo.

## Cómo bajarlos (ejemplo con curl, desde la carpeta del modelo)
```
cd biblioteca/cruda/bandeja/<carpeta>
curl -fL --create-dirs -o "<ruta del archivo>" "<URL>"     # una vez por archivo de la tabla
shasum -a 256 -c SHA256SUMS
```
(También sirve bajarlos desde el navegador con las URL de la tabla y ponerlos en la ruta indicada.)

## 1. `intfloat/multilingual-e5-small` (línea base; ya previsto en M1-09)

- **Repositorio:** `intfloat/multilingual-e5-small`
- **Commit fijado:** `614241f622f53c4eeff9890bdc4f31cfecc418b3`
- **Carpeta de destino:** `biblioteca/cruda/bandeja/hf-multilingual-e5-small/`
- **Total:** 487353147 bytes

| Archivo | Bytes | SHA-256 | URL |
|---|---|---|---|
| `onnx/model.onnx` | 470268510 | `ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/model.onnx |
| `onnx/tokenizer.json` | 17082730 | `0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/tokenizer.json |
| `onnx/tokenizer_config.json` | 443 | `a1d6bc8734a6f635dc158508bef000f8e2e5a759c7d92f984b2c86e5ff53425b` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/tokenizer_config.json |
| `onnx/special_tokens_map.json` | 167 | `d05497f1da52c5e09554c0cd874037a083e1dc1b9cfd48034d1c717f1afc07a7` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/special_tokens_map.json |
| `onnx/config.json` | 653 | `bbb7c1333fc4b3e27fbc9cd5d2070aabcc1d4dfb99917c3633e772f97545a6b6` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/config.json |
| `1_Pooling/config.json` | 200 | `987f7a67a38fa564c849bb5d277c52ab9088a84368fc0be31a354125aebb12a0` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/1_Pooling/config.json |
| `modules.json` | 387 | `c6e29747481e8b5dd2b58401966aeac910de39092f90cda9a704b1545f902b04` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/modules.json |
| `sentence_bert_config.json` | 57 | `948201d8329907aae938fa62f9ceeed53f5694dacc2b87b9f3b78b37ee986529` | https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/sentence_bert_config.json |

`SHA256SUMS` (guárdalo como `biblioteca/cruda/bandeja/hf-multilingual-e5-small/SHA256SUMS` y corre `shasum -a 256 -c SHA256SUMS` desde esa carpeta):
```
ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665  onnx/model.onnx
0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39  onnx/tokenizer.json
a1d6bc8734a6f635dc158508bef000f8e2e5a759c7d92f984b2c86e5ff53425b  onnx/tokenizer_config.json
d05497f1da52c5e09554c0cd874037a083e1dc1b9cfd48034d1c717f1afc07a7  onnx/special_tokens_map.json
bbb7c1333fc4b3e27fbc9cd5d2070aabcc1d4dfb99917c3633e772f97545a6b6  onnx/config.json
987f7a67a38fa564c849bb5d277c52ab9088a84368fc0be31a354125aebb12a0  1_Pooling/config.json
c6e29747481e8b5dd2b58401966aeac910de39092f90cda9a704b1545f902b04  modules.json
948201d8329907aae938fa62f9ceeed53f5694dacc2b87b9f3b78b37ee986529  sentence_bert_config.json
```

## 2. `ibm-granite/granite-embedding-97m-multilingual-r2` (candidato a reemplazo)

- **Repositorio:** `ibm-granite/granite-embedding-97m-multilingual-r2`
- **Commit fijado:** `835ad14087e140460703cf0fae09f97d469d65c2`
- **Carpeta de destino:** `biblioteca/cruda/bandeja/hf-granite-embedding-97m-multilingual-r2/`
- **Total:** 415322232 bytes

| Archivo | Bytes | SHA-256 | URL |
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

`SHA256SUMS` (guárdalo como `biblioteca/cruda/bandeja/hf-granite-embedding-97m-multilingual-r2/SHA256SUMS` y corre `shasum -a 256 -c SHA256SUMS` desde esa carpeta):
```
68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70  onnx/model.onnx
4f2842d568e2724370aec203652a42ac783c7937f8347a1a2cc7506d71f1582f  tokenizer.json
6ed69389e30a8ecabfce2f9ebcdf0c908b34056f24d994340f2f216521c057d5  tokenizer_config.json
013787ee251ff611722479197c00853b62113ad303cb0a36524231783c676c69  special_tokens_map.json
de948b0bdc6f356afad7a84b276d8dd7e7fe10fb9add1bb5e610621c28e41ebc  config.json
8bc5c9a40814fcf48d2fbe7cfeff4bee6736c3c2a823ba0ce098985c59d12ab7  1_Pooling/config.json
84e40c8e006c9b1d6c122e02cba9b02458120b5fb0c87b746c41e0207cf642cf  modules.json
967ef958285e4a7a37d8ff1832473d967edd913b4e48572f31c3d3ea361d5327  sentence_bert_config.json
93a59cbc7d82a47a7148719d9b21c0f2f111121e495b3918143184f4cd0ea25e  config_sentence_transformers.json
```

## 3. `ibm-granite/granite-embedding-311m-multilingual-r2` (techo de calidad; ojo: 1,25 GB)

- **Repositorio:** `ibm-granite/granite-embedding-311m-multilingual-r2`
- **Commit fijado:** `44399559930365213510b1ee2eb15ded83374f0e`
- **Carpeta de destino:** `biblioteca/cruda/bandeja/hf-granite-embedding-311m-multilingual-r2/`
- **Total:** 1281713692 bytes

| Archivo | Bytes | SHA-256 | URL |
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

`SHA256SUMS` (guárdalo como `biblioteca/cruda/bandeja/hf-granite-embedding-311m-multilingual-r2/SHA256SUMS` y corre `shasum -a 256 -c SHA256SUMS` desde esa carpeta):
```
75f9f258bf5013f5fe8a4dad61dd0fd16ac0cbaa7a106e3d3f41c2d04a42d541  onnx/model.onnx
0087c868b33bad550a78a08d19798cfd7f713cde4f020803b8f51f405503e15f  tokenizer.json
7947bdf0378520e69ca412b8c4dacd1cffa8aef099f851fdd5c65aa27c6b36a0  tokenizer_config.json
cb9e60dcf4d8d314315cb3e761fe4c2e664fda8dbf66d7815372b2639e381182  special_tokens_map.json
e1e3fc842a8e0537e25d6e4c93879698b92ae96722e8c162bef334b57978a3b0  config.json
781299da695e58439d70d491840da22ea0935d1d57d9646eb9725f1f19754e89  1_Pooling/config.json
84e40c8e006c9b1d6c122e02cba9b02458120b5fb0c87b746c41e0207cf642cf  modules.json
967ef958285e4a7a37d8ff1832473d967edd913b4e48572f31c3d3ea361d5327  sentence_bert_config.json
f09adf93fcf868bb2fc3976a435d810b2ecdffa953d1da091d2a91168abab44b  config_sentence_transformers.json
```

## Resumen de commits

| Modelo | Carpeta | Commit | Fecha del commit |
|---|---|---|---|
| `intfloat/multilingual-e5-small` | `hf-multilingual-e5-small` | `614241f622f53c4eeff9890bdc4f31cfecc418b3` | 2/4/2026 |
| `ibm-granite/granite-embedding-97m-multilingual-r2` | `hf-granite-embedding-97m-multilingual-r2` | `835ad14087e140460703cf0fae09f97d469d65c2` | 18/5/2026 |
| `ibm-granite/granite-embedding-311m-multilingual-r2` | `hf-granite-embedding-311m-multilingual-r2` | `44399559930365213510b1ee2eb15ded83374f0e` | 18/5/2026 |

Las huellas de los archivos grandes (`.onnx`, `tokenizer.json` de e5/Granite) son el identificador SHA-256 que publica Hugging Face para cada archivo (Git LFS). Los `tokenizer.json` de los tres los bajé y recalculé: coinciden. Los archivos chicos los bajé por la URL con el commit y calculé su SHA-256.
