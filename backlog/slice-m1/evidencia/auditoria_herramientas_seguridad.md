# Auditoría de herramientas de seguridad — pip-audit 2.10.1, osv-scanner 2.7.1 y gitleaks 8.30.1

Plantilla de `backlog/plantillas/auditoria_dependencia.md`. **Historia:** M1-02 (tarea 6; H00b-2) · **Fecha:** 12/11/2026 · **Quién la hizo:** agente

## En sencillo
- Las tres herramientas que revisan el proyecto (vulnerabilidades en `uv.lock` y secretos en el historial) ahora tienen la versión fijada y su auditoría. Antes, `scripts/auditar.sh` descargaba `pip-audit` con `uvx` sin comprobar huellas.
- **`pip-audit`** se instala en un entorno temporal con `--require-hashes`, desde una lista de 29 paquetes con sus huellas SHA-256 que está dentro de `scripts/auditar.sh`. Todas las versiones de la lista tienen **más de 14 días** de publicadas (la lista se generó con `--exclude-newer 2026-10-29`).
- **`osv-scanner` y `gitleaks`** son binarios de Homebrew: el script se detiene (código 2) si la versión instalada no es la auditada.
- **Un punto que necesita el visto del dueño:** `osv-scanner 2.7.1` se publicó el **9/11/2026**, así que hoy tiene 3 días y no cumple la regla de 14. Es la versión instalada en el Mac y la última publicada. Queda como **excepción temporal**: cumple la regla el **23/11/2026**. El script avisa mientras tanto. Alternativa si el dueño no quiere excepción: esperar al 23/11 para fijarla (no cambia nada en el código).
- El `uv.lock` no cambió, no se agregó ninguna dependencia al proyecto: estas herramientas viven fuera del lock.

## 1. Qué es y por qué entra
- **Qué hacen:** `pip-audit` (PyPA / Trail of Bits, Apache-2.0) consulta avisos de PyPI y OSV sobre las versiones del lock. `osv-scanner` (Google, Apache-2.0) consulta OSV sobre el mismo lock. `gitleaks` (MIT) busca secretos en todo el historial de git.
- **Alternativa sin dependencia nueva:** ninguna; ya eran los controles C3 y C9 de M0-00b. Lo nuevo es fijarlos.
- **Dónde se usan:** solo desarrollo (`just auditar`, `just secretos`, gancho previo al commit). No están en `src/` ni en el lock.

## 2. Origen y antigüedad
| Comprobación | Resultado |
|---|---|
| Fuente única y oficial | pip-audit: PyPI; osv-scanner y gitleaks: Homebrew core (`brew info`), que empaqueta los releases oficiales de GitHub (`google/osv-scanner`, `gitleaks/gitleaks`) |
| Fecha de publicación (≥ 14 días) | pip-audit 2.10.1: 10/6/2026 (155 días). gitleaks 8.30.1: 21/3/2026 (236 días). **osv-scanner 2.7.1: 9/11/2026 (3 días): excepción temporal hasta el 23/11/2026.** |
| Versión fijada y con hash | pip-audit y sus 28 dependencias: sí, `--require-hashes` en `scripts/auditar.sh`. Binarios: versión exacta comprobada en cada corrida; SHA-256 del binario instalado hoy: osv-scanner `82b84b72f905ca09…`, gitleaks `052d18829513f92e…` |
| Versión retirada (*yanked*) | no (PyPI: `yanked: false`) |
| Mantenedor y repositorio público | PyPA (`pypa/pip-audit`); Google (`google/osv-scanner`); organización `gitleaks` (`gitleaks/gitleaks`) |
| Licencia | Apache-2.0, Apache-2.0, MIT: compatibles |

## 3. Qué trae
- **Dependencias que arrastra `pip-audit` 2.10.1** (29 con él): boolean-py 5.0, cachecontrol 0.14.4, certifi 2026.10.23, charset-normalizer 3.5.2, cyclonedx-python-lib 11.12.0, defusedxml 0.7.1, filelock 4.2.4, idna 3.20, license-expression 30.4.4, markdown-it-py 4.2.0, mdurl 0.1.2, msgpack 1.2.4, packageurl-python 0.17.6, packaging 26.3, pip 26.2.2, pip-api 0.0.35, pip-requirements-parser 32.0.1, platformdirs 4.14.0, py-serializable 2.1.0, pygments 2.21.0, pyparsing 3.3.3, requests 2.34.2, rich 15.0.0, sortedcontainers 2.4.0, tomli 2.5.0, tomli-w 1.2.0, typing-extensions 4.16.0, urllib3 2.8.0. Todas con ≥ 14 días (tope `--exclude-newer 2026-10-29`) y con huellas en la lista. No se auditan una por una con la plantilla porque no entran al proyecto: viven en un entorno temporal que el script borra al terminar; las consulté en bloque (sección 4).
- **Binarios, extensiones, scripts de instalación:** se instala solo desde *wheels* (`--only-binary :all:`), sin compilar nada. `osv-scanner` y `gitleaks` son binarios de Go.
- **Qué hacen en segundo plano:** `pip-audit` y `osv-scanner` consultan la red (APIs de PyPI y OSV) y por eso `just auditar` necesita red. No ejecutan código del lock: `pip-audit` corre con `--no-deps --disable-pip` sobre el archivo exportado. `gitleaks` no usa la red.

## 4. Vulnerabilidades conocidas (12/11/2026, en el Mac)
| Fuente | Cómo se consultó | Resultado |
|---|---|---|
| `pip-audit` sobre las 29 dependencias de la propia herramienta | entorno temporal con `--require-hashes` y `pip-audit -r lista` | «No known vulnerabilities found» |
| GitHub Advisories | `gh api "/advisories?ecosystem=pip&affects=pip-audit@2.10.1"` | 0 |
| `pip-audit` sobre el `uv.lock` (86 paquetes) | `scripts/auditar.sh` | «No known vulnerabilities found» |
| `osv-scanner` sobre el `uv.lock` | `scripts/auditar.sh` | «No issues found» (86 paquetes) |
| `gitleaks` sobre el historial | `scripts/auditar.sh --secretos` | 111 commits, «no leaks found» |

## 5. Condiciones de uso
- El script se detiene con código 2 si `osv-scanner` o `gitleaks` no son la versión auditada, o si la lista de huellas no es la de la versión de `pip-audit` (prueba: `tests/test_m102_auditar.py`).
- Para subir una versión: nueva auditoría con esta plantilla, versión con ≥ 14 días, y cambiar en `scripts/auditar.sh` la versión, su fecha y, en `pip-audit`, la lista (`uv pip compile --generate-hashes --no-annotate --exclude-newer <hoy − 14 días>`).
- `just secretos` ahora llama a `scripts/auditar.sh --secretos`. El gancho de `scripts/instalar_ganchos.sh` sigue llamando a `gitleaks` directo (ese archivo no es de esta historia): conviene que lo cambie la historia que toque ese script.

## 6. Veredicto
**Aprobado con condiciones.** Condición: la excepción temporal de `osv-scanner 2.7.1` (3 días de publicada) se acepta o se espera al 23/11/2026; el dueño decide en su revisión. **Revisión siguiente:** al subir cualquiera de las tres versiones, o por slice.
