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
# Verificador en R (M0-09; tecnologias.md §3): regenera los esperados de R survey que usa pytest. Corre en el Mac, nunca en pytest.
# Primero, una sola vez: cd verificador_r && Rscript -e 'source("renv/activate.R"); renv::restore()'
# Equivale a: uv run python -m pap.inferencia.verificador_r esperados
esperados-r:
    uv run python -m pap.inferencia.verificador_r esperados
