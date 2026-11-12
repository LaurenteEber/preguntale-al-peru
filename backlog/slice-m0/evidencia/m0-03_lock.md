# M0-03 — Cambios en `uv.lock`

`uv lock` (86 paquetes; antes 84). `exclude-newer = "2 weeks"` activo, sin excepciones: todas las versiones pedidas cumplen los 14 días.

| Paquete | Antes → después | Motivo |
|---|---|---|
| svy | 0.32.1 → 0.35.0 | pedido (F-05) |
| pyreadstat | 1.3.6 → 1.3.7 | pedido |
| svy-io | 0.6.0 → 0.7.1 | esperado (arrastra `svy`) |
| svy-rs | 0.18.0 → 0.19.1 | esperado (arrastra `svy`) |
| ftfy | (nuevo) → 6.3.1 | declarada en M0-03 |
| wcwidth | (nuevo) → 0.9.4 | **no listada en la historia**: única dependencia de `ftfy` 6.3.1 |
| pydantic | 2.13.5 → 2.13.5 | solo se declara en `pyproject.toml`; ya estaba como transitiva |

Quitados: ninguno. Otros cambios: ninguno. `uv sync --locked --no-build --dry-run`: sin cambios (todo instalable desde *wheel*).
`scripts/auditar.sh`: pip-audit «No known vulnerabilities found»; osv-scanner «No issues found» (86 paquetes); «Auditoría limpia.»
