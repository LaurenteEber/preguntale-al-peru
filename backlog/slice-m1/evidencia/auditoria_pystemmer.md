# Auditoría de dependencia — PyStemmer 3.1.0

Plantilla de M0-00b. **Historia:** M1-00 (tarea 8) · **Fecha:** 12/11/2026 · **Quién la hizo:** agente

## 1. Qué es y por qué entra
- **Qué hace y para qué la usamos:** reduce las palabras a su raíz (Snowball, español) antes de la búsqueda por palabras de `bm25s`.
- **Alternativa sin dependencia nueva:** escribir un *stemmer* propio, o buscar sin raíces (se pierde recall con plurales y conjugaciones). No alcanza.
- **Dónde se usa:** `src/pap/inferencia/` (tokenización del índice de variables, M1-09).

## 2. Origen y antigüedad
| Comprobación | Resultado |
|---|---|
| Fuente única y oficial | Sí. PyPI `https://pypi.org/project/PyStemmer/` (repo `https://github.com/snowballstem/pystemmer`) |
| Fecha de publicación | 3.1.0: 22/5/2026 (**174 días**). Es la última versión |
| Versión fijada y con hash | Todavía no está en el lock. cp312 macOS arm64 (`pystemmer-3.1.0-cp312-cp312-macosx_11_0_arm64.whl`, 247 353 bytes): `b40b669f121949bbbd97fe77a2606d46b14df9fcadabc9539982398772592ac4`. cp312 manylinux x86_64 (`…-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl`, 752 410 bytes): `550bd609aa8dc324033eb1c8d34bfd68649183bbdab871ff534332dcafdc5e5a`. Sdist (no se usa): `083cc3ed90f4c3b0668f8e31c2925cbb4db3bf0fd6d710e0ad0914f33685f7df` |
| Versión retirada (*yanked*) | No |
| Mantenedor y repositorio público | Richard Boulton (autor); proyecto del grupo Snowball (`snowballstem`), público |
| Licencia compatible | MIT y BSD |

## 3. Qué trae
- **Dependencias nuevas que arrastra:** ninguna (`Requires-Dist` vacío).
- **Binarios, extensiones de C o Rust, scripts de instalación:** extensión de C (Cython) ya compilada dentro del wheel; hay wheel para las dos plataformas, así que `uv sync --no-build` funciona.
- **Qué hace en segundo plano:** nada. Solo recibe texto y devuelve texto; sin red, sin archivos, sin `pickle`.

## 4. Vulnerabilidades conocidas
| Fuente | Cómo se consultó | Resultado |
|---|---|---|
| OSV | API `POST /v1/query`, paquete `PyStemmer`, versión 3.1.0 y sin versión | 0 |
| GitHub Advisories | `api.github.com/advisories?ecosystem=pip&affects=pystemmer` | 0 |
| `pip-audit` | no disponible (ver `auditoria_pip_audit.md`) | pendiente de M1-09 |
| Rust / CRAN | no aplica | — |
| Si aparece algo | no hay hallazgos | |

## 5. Condiciones de uso
1. Solo se le pasan cadenas de texto del índice (nunca archivos ni objetos serializados).
2. Fijar la 3.1.0 en el lock con hash. Nota (ya conocida): separa «anemia» → `anemi` de «anémicos» → `anem`; se compensa con `sinonimos.yaml`.

## 6. Veredicto
**aprobado.** La aprobación previa (3.1.0) **sigue vigente**; no hay versión más nueva.
- **Revisión siguiente:** al subir la versión.
