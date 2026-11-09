# Auditoría de seguridad previa — dependencias y procesos del motor de inferencia

**9/11/2026.** Tres auditores independientes:
- **S1 y S2:** bibliotecas de Python. Revisaron lo mismo por separado.
- **S3:** el modelo, R, los repos de terceros, los ZIP, el respaldo y los secretos.

El supervisor consolidó y comprobó los hallazgos marcados con **[C]**:
- Pillow y `certifi`, en el JSON de `pip-audit`;
- el trío de versiones de `svy`, en PyPI;
- `.gitignore` y los `z.read()`, en el repo del Mac.

Lo demás viene de los auditores, con su evidencia en los informes S1, S2 y S3 (carpeta temporal del Project).

**Lo que no se pudo verificar:** la API de OSV, GitHub Advisories y Sigstore estaban bloqueados por el proxy, y gitleaks no se pudo compilar. Por eso M0-00b **vuelve a correr** estas comprobaciones en el Mac.

## En sencillo

- Casi todo lo que entra es seguro **con condiciones**.
- **Tres cosas no pasan como están:**
  1. **`renv` 1.2.4:** un `renv.lock` manipulado podía ejecutar comandos. Se usa la 1.3.1.
  2. **La lectura de los ZIP del INEI:** el código actual lee cada archivo completo sin límite de tamaño, y un ZIP malicioso podría llenar la memoria.
  3. **La regla de «versiones con 2 semanas»:** hoy no se hace cumplir, y el lock ya tiene dos paquetes más nuevos.
- **Un error del documento de tecnologías:** `svy` 0.35.0 trae `svy-io` 0.7.1 y `svy-rs` 0.19.1, no 0.8 y 0.20.
- **Un problema ya presente en el repo:** Pillow, que entra con `pdfplumber`, tiene 39 vulnerabilidades conocidas. Hay que subirla a 13.0.0.

## Veredictos por componente

| Componente | Versión | Veredicto | Condiciones |
|---|---|---|---|
| `svy` / `svy-io` / `svy-rs` | **0.35.0 / 0.7.1 / 0.19.1** [C] | aprobado con condiciones | `svy_io` **nunca** lee archivos: su copia de ReadStat (v1.1.9) no tiene la corrección de OSV-2024-118. `SVYLAB_OFFLINE=1`. No ejecutar la CLI `svy-skills` |
| `svy` 0.36 / `svy-io` 0.8 / `svy-rs` 0.20 | — | no aprobado por ahora | Menos de 14 días (28/10/2026) y cambia la API |
| `pyreadstat` | 1.3.7 | aprobado con condiciones | Es el **único** lector de SAV y DTA. Trae las correcciones de ReadStat OSV-2024-118, 2024-1150, 2024-1332, 2025-408 y 2026-1303. Lectura en un subproceso por archivo, con límites de memoria, CPU y tiempo |
| Pillow (vía `pdfplumber`) | 12.3.0 → **13.0.0** | no aprobado en 12.3.0 [C] | 39 advisories (escritura fuera de límites, use-after-free); se corrigen en 13.0.0 |
| `certifi` | → **2026.10.18** | subir [C] | PYSEC-2026-4320 |
| `pdfplumber` / `pdfminer.six` | 0.11.10 / 20260107 | aprobado con condiciones | `pdfminer.six` ya corrige CVE-2025-64512 y CVE-2025-70559. Lectura en un subproceso con límites |
| `ftfy` | 6.3.1 | aprobado | — |
| `pydantic` | 2.13.5 | aprobado | — |
| `httpx` | 0.28.1 | aprobado | — |
| `duckdb` | 1.5.6 | aprobado con condiciones | El endurecimiento funciona, probado. Tres matices: los `SET` van en orden después de conectar (pasar la configuración en `connect` no sirve); `COPY` puede escribir dentro del directorio permitido; `temp_directory` debe apuntar dentro de un directorio controlado |
| `bm25s` | 0.3.15 | aprobado con condiciones | Sin extras; nada de `bm25s.hf`, `utils.beir`, `mcp` ni `high_level`. Índice con `allow_pickle=False` y verificado con SHA-256 |
| `PyStemmer` | 3.1.0 | aprobado | — |
| `onnxruntime` | 1.31.x | aprobado con condiciones | `providers=["CPUExecutionProvider"]`, porque trae activo el proveedor de Azure. Sin operadores personalizados. El modelo se carga desde bytes con SHA-256 verificado. Necesita macOS 14 o superior |
| `tokenizers` | 0.23.3 | aprobado con condiciones | Solo `Tokenizer.from_file` con el archivo verificado. Excluir `huggingface-hub` (y su pila: `httpx2`, `hf-xet`…) con `override-dependencies`, ya probado. `HF_HUB_OFFLINE=1`. Vigilar CVE-2026-85670 (`tokenizer.json` manipulado; según la ficha, afecta hasta la 0.23.2) |
| Modelo `intfloat/multilingual-e5-small` | commit `614241f622f53c4eeff9890bdc4f31cfecc418b3` | aprobado con condiciones | Solo `onnx/model.onnx`, `onnx/tokenizer.json` y 3 JSON chicos, con SHA-256 verificado (las huellas se reconfirman en el Mac). Nunca `pytorch_model.bin` ni `trust_remote_code`. Licencia MIT |
| R `survey` | 4.5 | aprobado | — |
| R `renv` | 1.2.4 → **1.3.1** | no aprobado en 1.2.4 | Hasta la 1.3.0, un `renv.lock` manipulado podía ejecutar comandos de shell (#2389) |
| R `nanoparquet` | 0.5.1 → **0.5.2** | no aprobado en 0.5.1 | Leía mal los valores perdidos con `col_select` (#170): da cifras falsas en el verificador |
| CRAN | — | aprobado con condiciones | Repositorio fijado a una instantánea con fecha (Posit Package Manager). Una prueba que valida `renv.lock` |
| `Rscript` como subproceso | — | aprobado con condiciones | Lista de argumentos sin shell; `--vanilla` con renv activado de forma explícita; parámetros por un JSON; entorno mínimo **sin** `PAP_ANTHROPIC_API_KEY` ni `GH_TOKEN` |
| `inei-microdatos` | commit `f2b05e2…`, `catalog.json` | aprobado con condiciones | Solo el JSON, con su huella. Las URL las arma nuestro código, con el dominio fijo `https://proyectos.inei.gob.pe`. Se rechazan las 72 rutas truncadas y las 197 URL `http://` |
| ZIP del INEI | — | **no aprobado como está** [C] | `encuestas.py:64` e `insumos.py:105` y `:110` leen el miembro completo sin límite. Hace falta `abrir_zip_seguro` |
| Python | ≥ **3.12.12** | condición | Por CVE-2024-0450 (ZIP superpuestos) y CVE-2025-8291 (`zipfile`) |
| Respaldo con `gh` | — | aprobado con condiciones | Límites oficiales de GitHub: menos de 2 GiB por archivo y 1 000 archivos por release, sin tope total ni de ancho de banda. Token de grano fino solo para `-crudos` con `contents: write`, guardado en el Llavero de macOS y pasado solo como `GH_TOKEN` del comando. Siempre `--repo` explícito y guarda de visibilidad |
| Secretos | — | aprobado con condiciones [C] | No se hallaron claves en los 80 commits (con grep). `.gitignore` no excluye `.env`. gitleaks 8.30.1 sobre todo el historial, en cada commit y en CI, más Push protection de GitHub |
| Batch API de Anthropic | — | aprobado con condiciones | Guarda los datos 29 días, sin retención cero. Solo textos públicos de los cuestionarios. Clave y Workspace aparte del servicio. Borrar cada lote después de bajar los resultados |
| `uv.lock` (proceso) | — | aprobado con condiciones | Todas las entradas tienen sha256, una sola fuente (PyPI) y solo wheels. **La regla de 14 días no se hace cumplir:** `python-multipart` 0.0.33 (31/10) y `opentelemetry-api` 1.45.2 (29/10) [C: `pyproject.toml` pide `>=0.0.33`] |
| Crates de Rust dentro de los wheels | — | vigilar | Advisories de RustSec (zstd-safe, rustls, quinn-proto, pyo3) en `svy-rs`, `hf-xet` y `pydantic-core`; probablemente no se alcanzan, pero no está verificado. `osv-scanner` sobre el SBOM, por slice |

## Controles para el backlog

| # | Control | Dónde | Cuándo |
|---|---|---|---|
| C1 | `[tool.uv] exclude-newer = "2 weeks"`; `exclude-newer-package` solo con justificación escrita; bajar a `python-multipart>=0.0.32` | `pyproject.toml` | M0-00b |
| C2 | Prueba que falla si el lock tiene un paquete sin hash, de otra fuente o con menos de 14 días sin excepción | `tests/` | M0-00b y siempre |
| C3 | `just auditar`: `pip-audit` sobre `uv.lock` más `osv-scanner` (OSV, incluye CVE de VulnCheck y RustSec) | `justfile` | en cada cambio de dependencias y por slice |
| C4 | Instalar con `uv sync --locked --no-build`; en la nube, `--require-hashes --only-binary :all:` | guía de operación, imagen | M0-00b y M4 |
| C5 | Pruebas sin red (`pytest-socket`) y variables `HF_HUB_OFFLINE=1`, `SVYLAB_OFFLINE=1` | `tests/conftest.py`, entorno | M0-00b |
| C6 | Un grep que prohíbe APIs peligrosas: `svy_io.read_*`, `from_pretrained`, `trust_remote_code`, `allow_pickle=True`, `pickle.load`, `bm25s.hf` | prueba | M0-00b |
| C7 | `abrir_zip_seguro`: tope por miembro y total, tope de proporción de compresión, sin cifrados, sin enlaces, sin `..` ni rutas absolutas, extracción en flujo a un temporal. También en `encuestas.py` e `insumos.py` | `src/pap/` | M0-04 |
| C8 | Lectura de SAV, DTA y PDF en un subproceso por archivo con límites (RLIMIT_AS, CPU, tiempo) | conversor e índice | M0-04, M0-05 |
| C9 | gitleaks 8.30.1 sobre todo el historial; antes de cada commit; Push protection; `.env` en `.gitignore` | repo | M0-00b |
| C10 | Modelo: descarga por commit con SHA256SUMS; ONNX solo con CPU; tokenizer con `from_file` | M1-03 | M1 |
| C11 | R: `renv` 1.3.1, `nanoparquet` 0.5.2, CRAN con instantánea fija; `Rscript` sin shell y con entorno mínimo | `verificador_r/` | M0-09 |
| C12 | `gh`: token de grano fino en el Llavero; `--repo` explícito; guarda de visibilidad | `scripts/respaldar_crudos.sh` | M0-02 |
| C13 | Batch API: Workspace y clave aparte; borrar los lotes | M1-01 | M1 |
| C14 | Python ≥ 3.12.12 en `.python-version` y en la imagen | repo | M0-00b |
