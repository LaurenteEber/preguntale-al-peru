# Auditoría de dependencias — M0-03 (svy 0.35.0, pyreadstat 1.3.7, svy-io 0.7.1, svy-rs 0.19.1, pydantic 2.13.5, ftfy 6.3.1, wcwidth 0.9.4)

**Historia:** M0-03 · **Fecha:** 9/11/2026 · **Quién la hizo:** agente (plantilla `backlog/plantillas/auditoria_dependencia.md`)

## 1. Qué es y por qué entra
| Paquete | Qué hace y dónde se usa | Alternativa |
|---|---|---|
| svy 0.35.0 | motor de encuestas (cifras, errores estándar); `src/pap` (cálculo) | sin alternativa: es el motor decidido (F-05); la versión 0.36 queda fuera |
| svy-io 0.7.1 | lectura de formatos de encuesta; la arrastra `svy` | — |
| svy-rs 0.19.1 | núcleo en Rust de `svy`; la arrastra `svy` | — |
| pyreadstat 1.3.7 | lectura de SPSS/Stata (ENDES, ENAHO) | ya estaba (1.3.6); solo sube |
| pydantic 2.13.5 | validación de datos (M0-08); ya estaba como transitiva en 2.13.5, ahora declarada | — |
| ftfy 6.3.1 | arreglo de texto mal codificado (nombres con tildes y ñ, T-02) | normalización manual: no cubre mojibake |
| wcwidth 0.9.4 | ancho de caracteres; única dependencia de `ftfy` | — |

## 2. Origen y antigüedad (hoy 9/11/2026)
| Paquete | Publicada (PyPI) | Días | Licencia | Mantenedor |
|---|---|---|---|---|
| svy 0.35.0 | 16/10/2026 | 24 | MIT | Samplics LLC (github.com/samplics-org/svy) |
| svy-io 0.7.1 | 16/10/2026 | 24 | MIT | Samplics LLC |
| svy-rs 0.19.1 | 15/10/2026 | 25 | MIT (clasificadores de PyPI sin licencia explícita; mismo proyecto svy) | Samplics LLC |
| pyreadstat 1.3.7 | 21/10/2026 | 19 | Apache-2.0 | Otto Fajardo (github.com/Roche/pyreadstat) |
| pydantic 2.13.5 | 28/8/2026 | 73 | MIT | github.com/pydantic/pydantic |
| ftfy 6.3.1 | 26/10/2024 | 379 | Apache-2.0 | github.com/rspeer/python-ftfy |
| wcwidth 0.9.4 | 24/10/2026 | 16 | MIT | github.com/jquast/wcwidth |

Todas desde PyPI, ninguna retirada (*yanked*), todas con hash en `uv.lock`; todas ≥ 14 días, sin excepciones.

## 3. Qué trae
- **Dependencias nuevas que arrastra:** solo `wcwidth` 0.9.4 (por `ftfy`; no estaba en la lista esperada de la historia, ver `m0-03_lock.md`). `svy` no agrega otras más allá de `svy-io` y `svy-rs`.
- **Binarios:** `svy-rs` (Rust), `svy-io` y `pyreadstat` (extensiones nativas) se instalan como *wheel*; `uv sync --locked --no-build --dry-run` sin cambios. `pydantic` usa `pydantic-core` (Rust), sin cambio de versión. `ftfy` y `wcwidth` son Python puro.
- **Segundo plano:** no se detectó red, telemetría ni descargas al importar en las pruebas (corren con `pytest-socket`, sin red); el código fuente de las dependencias no se auditó línea a línea.

## 4. Vulnerabilidades conocidas
| Fuente | Cómo | Resultado |
|---|---|---|
| OSV | `osv-scanner scan source -L uv.lock` (vía `scripts/auditar.sh`) | 0 (86 paquetes) |
| GitHub Advisories | `gh api "/advisories?ecosystem=pip&affects=<paquete>"` | svy, pyreadstat, svy-io, svy-rs, ftfy, wcwidth: 0; pydantic: 2 históricas (GHSA-mr82-8j83-vxmv < 2.4.0, GHSA-5jqp-qgf6-3pvh < 1.6.2), 0 para 2.13.5 |
| pip-audit | `scripts/auditar.sh` (pip-audit 2.10.1) | limpio |
| RustSec | incluido en OSV | 0 |

## 5. Condiciones de uso
- Versiones exactas (`==`) en `pyproject.toml`; subir `svy` es otra historia con regresión de cifras y errores estándar (F-05).
- Regresión del cubo antes de dar por buena la subida (M0-03 tarea 3) y comparación con R en M0-09.

## 6. Veredicto
**Aprobado** para los siete paquetes. `wcwidth` queda aprobado como dependencia inevitable de `ftfy`; el parent debe confirmarlo, porque la historia no la listaba.
**Revisión siguiente:** al subir cualquiera de las versiones (en particular `svy` 0.36).
