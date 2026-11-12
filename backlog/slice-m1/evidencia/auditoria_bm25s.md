# Auditoría de dependencia — bm25s 0.3.16

Plantilla de M0-00b. **Historia:** M1-00 (tarea 8) · **Fecha:** 12/11/2026 · **Quién la hizo:** agente (consultas a PyPI, OSV y GitHub el mismo día)

## 1. Qué es y por qué entra
- **Qué hace y para qué la usamos:** búsqueda por palabras (BM25) sobre el texto de las variables de las encuestas, en el recuperador de M1-09.
- **Alternativa sin dependencia nueva:** DuckDB FTS (`docs/diseno/tecnologias.md` §7.1). Se mantiene `bm25s` porque ya está medida (indexa 300 000 filas en 18 s, responde en menos de 1 ms) y es la comparación de partida del banco de M1-09b.
- **Dónde se usa:** `src/pap/inferencia/` (índice de variables, M1-09). No se usa en el servicio web.

## 2. Origen y antigüedad
| Comprobación | Resultado |
|---|---|
| Fuente única y oficial | Sí. PyPI `https://pypi.org/project/bm25s/` (repo `https://github.com/xhluca/bm25s`) |
| Fecha de publicación (≥ 14 días al 12/11/2026) | **0.3.16:** 28/10/2026 (**15 días**, la más nueva que cumple). 0.3.15: 22/10/2026 (21 días, la de la auditoría previa) |
| Versión fijada y con hash en `uv.lock` | Todavía no está en el lock (entra con M1-09). Hash del *wheel* `py3-none-any` de 0.3.16: `65d973bd496de883ae525955379e3e7cf90a12c3d54ed175036315ae677512c9` (76 043 bytes). Es un solo wheel puro de Python, sirve para macOS arm64, cp312 y manylinux x86_64. El tar.gz (no se usa): `96301f99558c2318a889abfe1bc27cf53dc225f3860cdf03b0aaa5e72f8f4a2e` |
| Versión retirada (*yanked*) | No |
| Mantenedor y repositorio público | Xing Han Lù (un solo autor, publicó la 0.3.9 a la 0.3.16 en 5 meses). Repo público; artículo arXiv 2407.03618 |
| Licencia compatible | MIT (clasificador de PyPI; el wheel trae `LICENSE`) |

## 3. Qué trae
- **Dependencias nuevas que arrastra, sin extras:** solo `numpy` (ya en el lock: 2.5.3). Los extras `core`, `hf`, `mcp`, `cli`, `full`, `selection`, `indexing`, `evaluation` y `dev` **no** se instalan; el extra `hf` traería `huggingface_hub`, y `mcp` un servidor. `PyStemmer` se declara por separado (ver `auditoria_pystemmer.md`).
- **Binarios, extensiones de C o Rust, scripts de instalación:** ninguno. Wheel de Python puro.
- **Qué hace en segundo plano:** nada al importar. Revisé el wheel (leído, no ejecutado): sin `subprocess`, `os.system` ni `eval`. Solo guarda y carga arrays con `numpy.save`/`numpy.load`, con `allow_pickle=False` por defecto. `bm25s.hf` baja de Hugging Face y no se usa.
- **Diferencia 0.3.15 → 0.3.16:** comparé los dos wheels archivo por archivo. Cambia un solo archivo (`bm25s/__init__.py`): se agrega el parámetro `raise_on_serialization_error` a `save()` y un aviso en la documentación. Nada de red, de ejecución de código ni de dependencias.

## 4. Vulnerabilidades conocidas
| Fuente | Cómo se consultó | Resultado |
|---|---|---|
| OSV | API `POST /v1/query` con paquete `bm25s` (PyPI), versiones 0.3.15 y 0.3.16, y consulta sin versión | 0 (ningún aviso en ninguna versión) |
| GitHub Advisories | `api.github.com/advisories?ecosystem=pip&affects=bm25s` | 0 |
| `pip-audit` | no disponible (ver `auditoria_pip_audit.md`); `osv-scanner` sobre `uv.lock` actual: limpio. Se repite con la versión ya bloqueada en el lock | pendiente de M1-09 (al agregarla al lock) |
| Rust / CRAN | no aplica | — |
| Si aparece algo: ¿se alcanza? | no hay hallazgos | |

## 5. Condiciones de uso
1. Sin extras: `bm25s` a secas. Nada de `bm25s.hf`, `bm25s.utils.beir`, `mcp` ni `high_level` (control C6: un grep lo prohíbe).
2. Guardar y cargar el índice con `allow_pickle=False` (por defecto) y verificar el índice con SHA-256 antes de cargarlo.
3. Al guardar el corpus, pasar `raise_on_serialization_error=True` (existe desde 0.3.16): sin eso, un texto que no se serializa se omite con un aviso y el corpus guardado queda desalineado con el índice.
4. `HF_HUB_OFFLINE=1` en el entorno (C5).
5. Si se prefiere quedarse en 0.3.15 (la ya auditada), también está aprobada: la diferencia es la del punto anterior.

## 6. Veredicto
**aprobado con condiciones** (versión **0.3.16**, sin extras). Las condiciones previas de `auditoria_seguridad_previa.md` (0.3.15: sin extras, `allow_pickle=False`, índice verificado con SHA-256) **siguen vigentes**; se agrega la condición 3.
- **Revisión siguiente:** al subir la versión, o al cierre de M1.
