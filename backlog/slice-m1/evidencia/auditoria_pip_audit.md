# Auditoría de vulnerabilidades — `pip-audit` y OSV sobre el lock actual

**Historia:** M1-00 (tarea 8) · **Fecha:** 12/11/2026 · **Quién la hizo:** agente

## En sencillo
- **`pip-audit` no se pudo correr aquí.** No es una dependencia de desarrollo del proyecto (`pyproject.toml` solo trae `playwright`, `pytest` y `pytest-socket`) y no hay un `pip-audit` instalado en el entorno. `scripts/auditar.sh` lo lanza con `uvx pip-audit==2.10.1`, y `uvx` descarga e instala un paquete: eso quedó fuera de lo permitido en esta tarea. Se corrió después en el Mac con `scripts/auditar.sh`: ver «Corrida en el Mac» al final.
- **Sí corrí `osv-scanner`** (ya instalado en el Mac, versión 2.7.1) sobre el `uv.lock` actual: 86 paquetes, **«No issues found»** (sin hallazgos). Esto cubre el lock tal como está **hoy**, sin los paquetes nuevos de M1.
- Los paquetes nuevos de M1 (`bm25s`, `PyStemmer`, `onnxruntime`, `tokenizers`, más `flatbuffers` y `protobuf`) todavía **no están en el lock**. Los consulté directamente en la API de OSV por nombre y versión (0 avisos), pero hay que repetir `just auditar` cuando entren al lock (M1-09).

## Comandos y resultados
| Comando | Resultado |
|---|---|
| `command -v pip-audit` y `.venv/bin` | no instalado |
| `osv-scanner scan source -L uv.lock` | `Scanned …/uv.lock file and found 86 packages` → `No issues found` (código de salida 0) |
| API de OSV (`/v1/query`), paquete y versión: `bm25s` 0.3.15 y 0.3.16, `PyStemmer` 3.1.0, `onnxruntime` 1.31.1, `tokenizers` 0.23.2 y 0.23.3, `flatbuffers` 25.12.19, `protobuf` 7.36.2 | 0 avisos en todos |
| API de OSV por ID, `CVE-2026-85670` (tokenizers) | existe; solo rango de git (último afectado 0.23.2); `osv-scanner` no lo asocia a PyPI. Ver `auditoria_tokenizers.md` |
| API de GitHub Advisories (`ecosystem=pip&affects=<paquete>`) para los cuatro | 0 |

## Pendiente
1. ~~Correr `just auditar` en el Mac~~: hecho el 12/11/2026 (abajo).
2. Repetirlo al agregar los paquetes al lock (M1-09), y por slice.

## Corrida en el Mac (12/11/2026, agente principal)

`bash scripts/auditar.sh` (fija `pip-audit==2.10.1`, como en M0-00b) sobre `uv.lock` de la rama `slice-m1` (86 paquetes), salida código 0:

```
== pip-audit sobre uv.lock ==
No known vulnerabilities found
== osv-scanner sobre uv.lock ==
Scanned …/uv.lock file and found 86 packages
No issues found
Auditoría limpia.
```

**`pip-audit` en verde.** Los paquetes nuevos de M1 (`bm25s`, `PyStemmer`, `onnxruntime`, `tokenizers`) todavía no están en el lock: se repite al instalarlos en M1-09.
