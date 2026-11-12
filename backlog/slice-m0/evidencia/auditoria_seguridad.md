# Auditoría de seguridad verificada en el Mac (M0-00b, tarea 7)

**9/11/2026**, Mac del dueño (macOS, arm64). Verifica lo que la auditoría previa (`auditoria_seguridad_previa.md`) no pudo comprobar por el proxy: OSV, GitHub Advisories y gitleaks.

## Herramientas y versiones
| Herramienta | Versión | Cómo se instaló |
|---|---|---|
| gitleaks | 8.30.1 | `brew install gitleaks` (Homebrew ofrece 8.30.1, la versión pedida) |
| osv-scanner | 2.7.0 (osv-scalibr 0.5.3) | `brew install osv-scanner` |
| pip-audit | 2.10.1 (publicada el 10/6/2026) | `uvx pip-audit==2.10.1` desde `scripts/auditar.sh` |
| Python / uv (proyecto) | 3.12.16 / 0.13.7 local (imagen: 0.13.5) | `.python-version`, `uv.lock` |

## Resultados
- **`scripts/auditar.sh` (`just auditar`) sobre el `uv.lock` nuevo (84 paquetes):** pip-audit «No known vulnerabilities found»; osv-scanner «No issues found». En verde.
- **API de OSV (`/v1/querybatch`)** y **GitHub Advisories** (`gh api /advisories?ecosystem=pip&affects=<paquete>@<versión>`), con la versión exacta de cada componente: 0 hallazgos en todos los de la tabla, salvo los dos que ya figuraban como «no aprobado» en sus versiones viejas: Pillow 12.3.0 (OSV: 59 IDs; GitHub: 12 en la primera página; la auditoría previa contó 39) y `certifi` 2026.7.22 (GHSA-6q48-6c7w-9gw2 y PYSEC-2026-4320). Pillow 13.0.0 y `certifi` 2026.10.23: 0 en las dos fuentes.
- **Actualización 9/11/2026 (D-M0-00b-1 resuelta):** el dueño confirmó que es el enlace público de Power BI; quedó excluido por fingerprint en `.gitleaksignore` y gitleaks sobre el historial da 0 hallazgos.
- **gitleaks 8.30.1 sobre todo el historial** (`--log-opts=--all`, 83 commits): 2 coincidencias de la regla `grafana-api-key`, ambas del commit `f98fb753`, probablemente una URL pública de Power BI. **No se copia el valor.** Es la consulta tipo D `D-M0-00b-1` en `consultas_al_dueno.md`. El gancho antes de cada commit se probó en un repo temporal: deja pasar un commit limpio y detiene uno con un token de GitHub sintético.
- **Límites de esta verificación:** OSV y GitHub no cubren los avisos de `renv` ni `nanoparquet` (son issues de sus repos; OSV marca 0 para esas versiones, el veredicto sale de la auditoría previa); `osv-scanner` sobre `uv.lock` no mira los crates de Rust dentro de los wheels; las huellas del modelo e5-small se reconfirman en M1-03; CVE-2026-85670 de `tokenizers` no figura en OSV ni en GitHub Advisories para 0.23.3 (y tampoco para 0.23.2).

## Veredicto por componente
| Componente | Versión | Veredicto | Verificación en el Mac |
|---|---|---|---|
| `svy` / `svy-io` / `svy-rs` | 0.35.0 / 0.7.1 / 0.19.1 | aprobado con condiciones | OSV y GitHub: 0. (El lock actual aún tiene `svy` 0.32.1; sube en M0-03.) |
| `svy` 0.36 / `svy-io` 0.8 / `svy-rs` 0.20 | — | no aprobado por ahora | No consultado: menos de 14 días y cambia la API |
| `pyreadstat` | 1.3.7 | aprobado con condiciones | OSV y GitHub: 0 |
| Pillow | 13.0.0 (en el lock) | **aprobado** en 13.0.0 (12.3.0 sigue «no aprobado») | OSV y GitHub: 0 en 13.0.0 |
| `certifi` | 2026.10.23 (en el lock) | **aprobado** (2026.7.22 sigue «no aprobado») | OSV y GitHub: 0 |
| `pdfplumber` / `pdfminer.six` | 0.11.10 / 20260107 | aprobado con condiciones | 0 y 0 |
| `ftfy`, `pydantic`, `httpx` | 6.3.1, 2.13.5, 0.28.1 | aprobado | 0 |
| `duckdb` | 1.5.6 | aprobado con condiciones | 0 |
| `bm25s` / `PyStemmer` | 0.3.15 / 3.1.0 | aprobado con condiciones / aprobado | 0 |
| `onnxruntime` | 1.31.0 | aprobado con condiciones | 0 (M1-00 lo vuelve a mirar con la versión vigente) |
| `tokenizers` | 0.23.3 | aprobado con condiciones | 0; CVE-2026-85670 no figura |
| Modelo `multilingual-e5-small` | commit `614241f6…` | aprobado con condiciones | no aplica a OSV; huellas en M1-03 |
| R `survey` 4.5 | — | aprobado | OSV CRAN: 0 |
| R `renv` | 1.2.4 → 1.3.1 | no aprobado en 1.2.4 | OSV CRAN: 0 en ambas (el aviso no está en OSV); sigue 1.3.1 |
| R `nanoparquet` | 0.5.1 → 0.5.2 | no aprobado en 0.5.1 | OSV CRAN: 0 en ambas; sigue 0.5.2 |
| CRAN, `Rscript`, `inei-microdatos`, respaldo con `gh`, Batch API | — | aprobado con condiciones | no hay base de avisos que consultar; condiciones de la auditoría previa |
| ZIP del INEI | — | **aprobado con condiciones** (antes «no aprobado») | `abrir_zip_seguro` en `encuestas.py` e `insumos.py`; 12 pruebas en verde |
| Python | 3.12.16 | aprobado (≥ 3.12.12) | `.python-version` e imagen |
| Secretos | — | aprobado con condiciones | gitleaks: 2 coincidencias, tipo D; `.env`/`.env.*` en `.gitignore`; gancho instalable |
| `uv.lock` (proceso) | — | **aprobado** | `exclude-newer = "2 weeks"`, constraints, prueba C2 |
| `pytest-socket` (nuevo, dev) | 0.8.1 | aprobado | `auditoria_pytest-socket.md` |
| Crates de Rust dentro de los wheels | — | vigilar | `osv-scanner` sobre `uv.lock` no los ve; falta un SBOM por slice (queda abierto) |

**Ningún componente salió «no aprobado» en una versión que vaya a usarse**, así que no hay consulta tipo C por esta verificación.
