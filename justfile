# Tareas frecuentes (opcional: requiere `just`; todo se puede correr con `uv run ...`)
sync:
    uv sync
test:
    uv run pytest -q
verificar:
    uv run pap verificar
revisar:
    uv run pap revisar
# Catálogo: tras `pap registrar` o `pap verificar`, recalcular la compuerta por captura verificada y publicar
catalogo:
    cd catalogo/scripts && uv run python ingesta_src.py && python3 run.py && python3 test_catalogo.py && python3 render.py
    uv run pap recetas sincronizar
# Seguridad (M0-00b, C3): vulnerabilidades conocidas en uv.lock con pip-audit y osv-scanner (necesita red)
auditar:
    scripts/auditar.sh
# Seguridad (M0-00b, C9): gitleaks sobre todo el historial; el gancho antes de cada commit se instala con scripts/instalar_ganchos.sh
secretos:
    gitleaks git --redact --no-banner .
