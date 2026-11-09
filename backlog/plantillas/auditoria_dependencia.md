# Auditoría de dependencia — <nombre> <versión>

Plantilla de M0-00b. La llena toda historia que **agregue o suba** una dependencia de Python, un modelo, un paquete de R, una imagen o un repo de terceros. Se guarda como `backlog/slice-N/evidencia/auditoria_<nombre>.md` y se enlaza desde la historia. Nada externo entra sin esta auditoría (decisión del dueño, 9/11/2026).

**Historia:** <M?-??> · **Fecha:** <d/m/aaaa> · **Quién la hizo:** <agente o persona>

## 1. Qué es y por qué entra
- **Qué hace y para qué la usamos:** <una frase>.
- **Alternativa sin dependencia nueva:** <qué se evaluó y por qué no alcanza>.
- **Dónde se usa:** <archivos de `src/`, o «solo desarrollo y pruebas»>.

## 2. Origen y antigüedad
| Comprobación | Resultado |
|---|---|
| Fuente única y oficial (PyPI, CRAN con instantánea, release por commit) | <sí/no, URL> |
| Fecha de publicación de la versión (debe tener **≥ 14 días**; si no, excepción escrita en `curados/inferencia/parametros.yaml`) | <fecha, días> |
| Versión fijada y con hash en `uv.lock` (o en `renv.lock`, o por commit y SHA-256) | <sí/no> |
| Versión retirada (*yanked*) | <no> |
| Mantenedor y repositorio público | <quién, URL> |
| Licencia compatible | <licencia> |

## 3. Qué trae
- **Dependencias nuevas que arrastra:** <lista con versión; cada una pasa por esta misma plantilla o se cita su auditoría>.
- **Binarios, extensiones de C o Rust, scripts de instalación:** <qué hay; `uv sync --no-build` debe poder instalarla desde *wheel*>.
- **Qué hace en segundo plano:** <accesos a red, descargas al importar, telemetría, carga de modelos, `pickle`, `eval`, ejecución de código, procesos externos>.

## 4. Vulnerabilidades conocidas (se corren en el Mac, con la versión exacta)
| Fuente | Cómo se consultó | Resultado |
|---|---|---|
| OSV | `osv-scanner scan source -L uv.lock` y la API de OSV | <0 / lista de IDs> |
| GitHub Advisories | `gh api "/advisories?ecosystem=pip&affects=<paquete>@<versión>"` | <0 / lista> |
| `pip-audit` | `just auditar` | <limpio / hallazgos> |
| Rust (RustSec) o CRAN, si aplica | <cómo> | <resultado> |
| Si aparece algo: ¿se alcanza desde nuestro uso? | <sí/no y por qué> | |

## 5. Condiciones de uso
<Lo que el código debe cumplir para que sea seguro: por ejemplo «solo se lee con X», «nunca con Y», «en un subproceso con límites». Cada condición lleva su prueba o su control (C1–C14) o dice por qué no hace falta.>

## 6. Veredicto
**<aprobado | aprobado con condiciones | no aprobado>**
- **Si es «no aprobado»:** es una consulta tipo C en `consultas_al_dueno.md`, con la alternativa propuesta. La dependencia no entra mientras tanto.
- **Revisión siguiente:** <cuándo se vuelve a auditar: al subir la versión, o por slice>.
