# M0-00b — Seguridad: correcciones del repo actual y controles

**Se deriva de** el diseño §22 y §26.5, y de F-04 (editada en M0-01).

**Decisiones del dueño del 9/11/2026:**
- nada externo entra sin auditoría;
- las correcciones de seguridad de lo que **ya está** en el repo se hacen en M0.

**Punto de partida:**
- la auditoría previa, con tres auditores independientes, en `evidencia/auditoria_seguridad_previa.md`, con un veredicto por componente y los controles C1–C14;
- la revisión del repo actual que hizo el supervisor el 9/11/2026, en la tabla de abajo.

**Esta historia** corrige lo existente, verifica la auditoría en el Mac y deja los controles funcionando. Va **antes** de M0-03, para que `svy` y `pyreadstat` suban ya con los controles activos.

## Lo que hay que corregir en el repo actual

| # | Qué | Dónde | Gravedad | Corrección |
|---|---|---|---|---|
| A1 | Pillow 12.3.0 con 39 advisories (escritura fuera de límites, use-after-free); entra con `pdfplumber` | `uv.lock` | alta | Pillow ≥ 13.0.0 (16/10/2026) |
| A2 | `certifi` 2026.7.22 con PYSEC-2026-4320 | `uv.lock` | media | `certifi` ≥ 2026.10.18 |
| A3 | Los ZIP se leen completos en memoria, sin límite de tamaño | `src/pap/capa0/encuestas.py:64` y `src/pap/capa0/insumos.py:105` y `:110` | alta | `abrir_zip_seguro` (tarea 3) |
| A4 | La regla de «versiones con ≥ 2 semanas» no se hace cumplir: `python-multipart` 0.0.33 (31/10) y `opentelemetry-api` 1.45.2 (29/10) | `pyproject.toml`, `uv.lock` | media | `exclude-newer = "2 weeks"` y `python-multipart>=0.0.32` |
| A5 | `.gitignore` no excluye `.env` (`.dockerignore` sí) | `.gitignore` | media | Agregar `.env` y `.env.*` |
| A6 | La imagen usa `python:3.12-slim` sin fijar la versión ni la huella, e instala `uv==0.13.7` con `pip` sin huella | `Dockerfile` | media | Imagen fijada por huella (`python:3.12.X-slim@sha256:…`, con X ≥ 12); `uv` desde su imagen oficial fijada por huella (`COPY --from=ghcr.io/astral-sh/uv:<versión>@sha256:…`) |
| A7 | `.python-version` dice `3.12`, sin parche (CVE-2024-0450 y CVE-2025-8291 en `zipfile`) | `.python-version` | media | La última 3.12.x disponible, ≥ 3.12.12 |
| A8 | `bajar_biblioteca.sh` baja el `SHA256SUMS` del mismo release que el paquete: comprueba la integridad, no el origen | `scripts/bajar_biblioteca.sh` | baja | Que la huella esperada del `.tar.zst` esté versionada en el repo (por ejemplo `curados/releases.yaml`) y se compare contra ella |
| A9 | `test_sin_secretos.py` busca solo claves de Anthropic; ahora habrá token de GitHub | `tests/test_sin_secretos.py` | baja | Agregar los prefijos `ghp_`, `github_pat_` y `gho_`, armados por partes como los actuales |

**Revisado sin hallazgos:**
- `.mcp.json` y `.claude/settings.json` no tienen secretos;
- Jinja usa `select_autoescape`;
- no hay workflows de GitHub Actions;
- `pip-audit` no da otras vulnerabilidades en el lock actual.

**Fuera de M0:** dos recetas de fuente (FONCODES y MINEDU-UMC-ENLA) usan URL `http://`. No las usa el motor. Se revisan cuando se vuelvan a descargar esas fuentes: preferir `https://`, y si no existe, registrar la huella al bajar.

## Tareas

1. **Dependencias** (A1, A2, A4), en `pyproject.toml`:
   - `[tool.uv] exclude-newer = "2 weeks"`;
   - `constraint-dependencies = ["pillow>=13.0.0", "certifi>=2026.10.18"]`, para que el lock no pueda volver atrás;
   - `python-multipart>=0.0.32`;
   - `uv lock`. No hace falta `exclude-newer-package`, porque Pillow 13.0.0 y `certifi` 2026.10.18 ya tienen más de 14 días.
2. **Python, `.gitignore` y la imagen** (A5, A6, A7):
   - `.python-version` con la última 3.12.x (≥ 3.12.12);
   - `.env` y `.env.*` en `.gitignore`;
   - `Dockerfile` con la imagen base y `uv` fijados por huella, y `uv sync --locked --no-build --no-dev`.
3. **`abrir_zip_seguro`** (A3, control C7), en un módulo nuevo `src/pap/zip_seguro.py`:
   - rechaza rutas absolutas o con `..`, enlaces simbólicos, miembros cifrados, tamaños por encima de `zip_max_miembro_mb` o `zip_max_total_mb` y proporciones de compresión por encima de `zip_proporcion_max`;
   - lee en flujo, por bloques, y nunca hace un `z.read()` completo;
   - reemplaza los tres `z.read()` de `encuestas.py` e `insumos.py`;
   - los límites van en `curados/inferencia/parametros.yaml`, con margen sobre el ZIP más grande registrado (hoy, unos 15 MB), y llevan `supuesto: M0-00b`;
   - **pruebas:** ZIP sintéticos con `..`, enlace simbólico, miembro cifrado y bomba de compresión, que deben ser rechazados, más un ZIP real registrado, que debe seguir leyéndose igual.

   M0-04 lo reutiliza para los ZIP nuevos.
4. **Release de la biblioteca y prueba de secretos** (A8, A9):
   - la huella esperada del `.tar.zst` de `biblioteca-010ea965`, versionada y comparada;
   - los prefijos de GitHub en `test_sin_secretos.py`.
5. **Regresión, en un commit propio:**
   - `uv run pap calcular`, que compara con `evidencia/fact_indicador_010ea965.parquet` (|dif| ≤ 1e-12; huella esperada `010ea965`);
   - Q1–Q4, la matriz y la evaluación grabada, sin cambios;
   - suite completa.

   Si algo cambia, es tipo C y no se avanza.
6. **Controles automáticos:**
   - `just auditar`, que corre `pip-audit` sobre `uv.lock` y `osv-scanner` (OSV, que incluye CVE de VulnCheck y RustSec) (C3);
   - una prueba que falla si `uv.lock` tiene un paquete sin hash, de otra fuente que no sea PyPI o con menos de 14 días sin excepción registrada (C2);
   - pruebas sin red con `pytest-socket`, más las variables `HF_HUB_OFFLINE=1` y `SVYLAB_OFFLINE=1` en `tests/conftest.py` (C5);
   - una prueba que prohíbe en `src/` las llamadas `svy_io.read_*`, `from_pretrained`, `trust_remote_code`, `allow_pickle=True`, `pickle.load` y `bm25s.hf` (C6);
   - gitleaks 8.30.1 sobre **todo el historial** y como gancho antes de cada commit (C9). Si encuentra algo, es tipo D: se avisa al dueño sin copiar el secreto en la evidencia.
7. **Verificar en el Mac** lo que no se pudo verificar en la auditoría previa: OSV, GitHub Advisories y gitleaks. Si algún componente sale «no aprobado», es tipo C, con la alternativa.
8. **Plantilla** `backlog/plantillas/auditoria_dependencia.md`. La usa toda historia que agregue o suba una dependencia, un modelo, un paquete de R o un repo de terceros.
9. **Documentación:**
   - `docs/guia_de_operacion.md`: `just auditar`, el gancho de gitleaks y la instalación con `--locked --no-build`;
   - `docs/especificaciones/stack.md`: las versiones nuevas.

## Criterios de aceptación

- [ ] A1–A9 corregidos, cada uno con su diff en `evidencia/m0-00b_correcciones.md`.
- [ ] `pip-audit` y `osv-scanner` sin vulnerabilidades abiertas en el lock nuevo; `just auditar` en verde.
- [ ] Prueba del lock, prueba sin red y prueba de APIs prohibidas, en verde.
- [ ] gitleaks sobre todo el historial sin hallazgos, o con su consulta tipo D.
- [ ] Pruebas de `abrir_zip_seguro` en verde, y los ZIP registrados siguen leyéndose igual.
- [ ] La imagen se construye con el `Dockerfile` nuevo y `/salud` responde (en el Mac, si Docker está disponible; si no, queda anotado).
- [ ] Regresión: el cubo sigue siendo `010ea965`, y Q1–Q4, la matriz y la evaluación grabada no cambian.
- [ ] `evidencia/auditoria_seguridad.md`: la auditoría previa verificada en el Mac, con un veredicto por componente.

## Fuera

- Las dependencias de M1 (`bm25s`, `PyStemmer`, `onnxruntime`, `tokenizers` y el modelo e5-small). La auditoría previa ya las revisó; su verificación en el lock la hace M1-00, con las versiones vigentes al empezar M1.
- Activar Push protection en GitHub: lo hace el dueño (K-09).
