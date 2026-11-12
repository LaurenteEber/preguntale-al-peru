# Auditoría de dependencia — pytest-socket 0.8.1

Con la plantilla `backlog/plantillas/auditoria_dependencia.md`.

**Historia:** M0-00b (control C5) · **Fecha:** 9/11/2026 · **Quién la hizo:** agente implementador (worker T2)

## 1. Qué es y por qué entra
- **Qué hace y para qué la usamos:** bloquea los sockets de red durante las pruebas, para que ninguna prueba salga a internet (C5).
- **Alternativa sin dependencia nueva:** un `monkeypatch` de `socket.socket` en `conftest.py`; se descartó porque `pytest-socket` ya resuelve los permisos (bucle local, sockets Unix) y es de uso muy extendido.
- **Dónde se usa:** solo desarrollo y pruebas (grupo `dev` de `pyproject.toml`); no entra a la imagen (`--no-dev`).

## 2. Origen y antigüedad
| Comprobación | Resultado |
|---|---|
| Fuente única y oficial | sí, PyPI (`https://pypi.org/simple`) |
| Fecha de publicación (≥ 14 días) | 19/8/2026, 82 días |
| Versión fijada y con hash en `uv.lock` | sí (wheel y sdist con `sha256`) |
| Versión retirada (*yanked*) | no |
| Mantenedor y repositorio público | Mike Fiedler (`miketheman`), https://github.com/miketheman/pytest-socket |
| Licencia compatible | MIT |

## 3. Qué trae
- **Dependencias nuevas que arrastra:** ninguna (solo `pytest>=7`, que ya está).
- **Binarios, extensiones de C o Rust, scripts de instalación:** ninguno; wheel `py3-none-any`.
- **Qué hace en segundo plano:** es un plugin de `pytest` en Python puro; parchea `socket.socket` y `socket.socket.connect` mientras corren las pruebas. No hace red, ni `pickle`, ni ejecuta procesos.

## 4. Vulnerabilidades conocidas (en el Mac, 9/11/2026)
| Fuente | Cómo se consultó | Resultado |
|---|---|---|
| OSV | `osv-scanner scan source -L uv.lock` (2.7.0) y API `querybatch` | 0 |
| GitHub Advisories | `gh api "/advisories?ecosystem=pip&affects=pytest-socket@0.8.1"` | 0 |
| `pip-audit` | `scripts/auditar.sh` (pip-audit 2.10.1) | limpio |

## 5. Condiciones de uso
- Se activa con `addopts` en `pyproject.toml`: `--disable-socket --allow-unix-socket --allow-hosts=127.0.0.1,::1,localhost`. Solo se permite el bucle local (servidor de pruebas, Chromium) y los sockets Unix.
- Si falta el plugin, `pytest` falla al arrancar por la opción desconocida (no se salta en silencio).
- Es un control de pruebas, no de producción: no reemplaza a las guardas de red del código.

## 6. Veredicto
**aprobado**
- **Revisión siguiente:** al subir la versión.
