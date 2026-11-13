# Auditoría de dependencia — tokenizers 0.23.3 (sin huggingface-hub)

Plantilla de M0-00b. **Historia:** M1-00 (tarea 8) · **Fecha:** 12/11/2026 · **Quién la hizo:** agente

## 1. Qué es y por qué entra
- **Qué hace y para qué la usamos:** convierte texto en los números que entiende el modelo, leyendo el `tokenizer.json` del modelo (solo `Tokenizer.from_file`).
- **Alternativa sin dependencia nueva:** reescribir el tokenizador de cada modelo (Unigram para e5, BPE para Granite). No es razonable ni seguro.
- **Dónde se usa:** `src/pap/inferencia/` (embeddings, M1-09).

## 2. Origen y antigüedad
| Comprobación | Resultado |
|---|---|
| Fuente única y oficial | Sí. PyPI `https://pypi.org/project/tokenizers/` (Hugging Face, `https://github.com/huggingface/tokenizers`) |
| Fecha de publicación (≥ 14 días) | **0.23.3:** 9/10/2026 (**34 días**). Hay `1.0.0rc1` a `rc4` (21/9 a 9/11/2026): son *pre-releases*, no se usan |
| Versión fijada y con hash | Todavía no está en el lock. Wheel `cp310-abi3` (sirve para cp312): macOS arm64 (`tokenizers-0.23.3-cp310-abi3-macosx_11_0_arm64.whl`, 3 101 381 bytes) `68649e97d5b43c44c031d8d848874a6eecae8f8fe40ea989aa777a5a83aca716`; manylinux x86_64 (`…-cp310-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl`, 3 396 193 bytes) `376851d22bcf9d650a5c3090bb83e6cf9e895fbf0595369fa4cd43c1f69b5f87` |
| Versión retirada (*yanked*) | No |
| Mantenedor y repositorio público | Hugging Face (Nicolas Patry, Anthony Moi); repo público |
| Licencia compatible | Apache 2.0 |

## 3. Qué trae
- **Dependencias nuevas que arrastra:** `Requires-Dist: huggingface-hub>=0.16.4,<3.0` es **obligatoria** en los metadatos. **No se instala**: se excluye con `override-dependencies` en `pyproject.toml`, como ya se probó en M0-00b (así tampoco entran `httpx2`, `hf-xet` ni su pila). El lock debe resolver sin ella y una prueba lo comprueba.
- **Binarios, extensiones de C o Rust, scripts de instalación:** extensión de Rust ya compilada en el wheel; hay wheel para las dos plataformas (`uv sync --no-build` funciona).
- **Qué hace en segundo plano:** con `Tokenizer.from_file` no hace red. Las funciones `from_pretrained` y `from_http` sí bajan de internet y están prohibidas (C6).

## 4. Vulnerabilidades conocidas
| Fuente | Cómo se consultó | Resultado |
|---|---|---|
| OSV | API `POST /v1/query`, paquete `tokenizers`, versiones 0.23.2 y 0.23.3 | 0 por versión de PyPI. **Pero** el registro `CVE-2026-85670` existe (consulta por ID) y no se asocia a versiones de PyPI, solo a un rango de git: ver más abajo |
| GitHub Advisories | `api.github.com/advisories?ecosystem=pip&affects=tokenizers` | 0 |
| `pip-audit` / `osv-scanner` | no disponible el primero (ver `auditoria_pip_audit.md`); el segundo no vería este CVE por lo anterior | **vigilar a mano** |
| Rust (RustSec) | no consultado de forma independiente (se vigila con `osv-scanner` sobre el SBOM por slice, control de la auditoría previa) | pendiente |
| Si aparece algo: ¿se alcanza? | Ver abajo | |

**CVE-2026-85670** («BpeBuilder: desborde de búfer al cargar un `tokenizer.json` manipulado»; solo denegación de servicio por aborto del proceso, más un desborde secundario si hay `continuing_subword_prefix`).
- El registro dice «último afectado: 0.23.2». La 0.23.3 sale del rango, **pero** el reporte upstream (huggingface/tokenizers#2094) se cerró el 31/10/2026, posterior a la 0.23.3 (9/10/2026): **no pude comprobar que 0.23.3 lleve la corrección.** Trato la 0.23.3 como **afectada, sin alcance con los archivos verificados** (el supervisor leyó el código fuente: la parte con el fallo es idéntica a la de la 0.23.2, y no existe una 0.23.x corregida).
- Solo se alcanza con un `tokenizer.json` **manipulado y de tipo BPE**. Medí los que vamos a cargar, en el commit fijado y con el SHA-256 verificado:
  - e5-small: tipo **Unigram** (no se alcanza);
  - granite-97m-r2: BPE, 413 540 reglas de fusión; **ninguna** regla supera el largo de la clave más larga del vocabulario; sin `continuing_subword_prefix`;
  - granite-311m-r2: BPE, 514 906 reglas; **ninguna** supera el largo máximo; sin prefijo.
- Conclusión: con los archivos de la lista no se dispara. Es una condición, no un bloqueo.

## 5. Condiciones de uso
1. Solo `Tokenizer.from_file(ruta)` con un archivo cuyo SHA-256 ya se verificó contra el valor fijado. Nunca `from_pretrained`, `from_str` con texto de afuera ni `from_http`.
2. Excluir `huggingface-hub` con `override-dependencies`; `HF_HUB_OFFLINE=1` (C5, C10). Prueba de que `huggingface_hub` no está en el lock.
3. Cargar el tokenizador y tokenizar dentro del proceso de indexación, no en el servicio web; un aborto (el efecto del CVE) solo detiene el trabajo de índice.
4. Si sale una versión posterior a 0.23.3 que cite la corrección de #2094 y tenga ≥ 14 días, subir a ella y repetir esta auditoría.

## 6. Veredicto
**aprobado con condiciones** (0.23.3, solo `from_file`, sin `huggingface-hub`). Las condiciones previas **siguen vigentes**; se confirma que el aviso a vigilar existe, que no se asocia a PyPI, y que los tokenizadores de la lista no lo activan. Dudas honestas: no se verificó que 0.23.3 contenga la corrección (ver arriba).
- **Revisión siguiente:** al salir una versión con ≥ 14 días posterior a 0.23.3, o al agregar un modelo con otro `tokenizer.json`.
