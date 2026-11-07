#!/usr/bin/env bash
# S3-09 — Arranque de la imagen: (1) baja la biblioteca si falta (o si no hay un volumen montado con ella), (2) corre
# `pap calcular` solo si el cubo no coincide con su manifiesto, (3) sirve la web. La clave del LLM llega solo por la variable de
# entorno PAP_ANTHROPIC_API_KEY; este script nunca la imprime. Sin despliegue público (P-05).
set -euo pipefail
cd "$(dirname "$0")/.."

PUERTO="${PAP_PUERTO:-8000}"
CUBO="biblioteca/indicadores/fact_indicador.parquet"
UVRUN=(uv run --frozen --no-dev)

if [ ! -f "$CUBO" ]; then
  echo "No hay biblioteca montada: se baja del release."
  bash scripts/bajar_biblioteca.sh ${PAP_BIBLIOTECA_ETIQUETA:+"$PAP_BIBLIOTECA_ETIQUETA"}
fi

# ¿El cubo es el del manifiesto? (misma comprobación que tests/conftest.py)
if "${UVRUN[@]}" python - <<'PY'
import hashlib, json, sys
ind = "biblioteca/indicadores/"
declarado = json.load(open(ind + "manifiesto_p1_indicadores.json"))["tablas"]["fact_indicador"]["hash"].removeprefix("sha256:")
h = hashlib.sha256()
with open(ind + "fact_indicador.parquet", "rb") as f:
    for bloque in iter(lambda: f.read(1 << 20), b""):
        h.update(bloque)
sys.exit(0 if h.hexdigest() == declarado else 1)
PY
then
  echo "El cubo coincide con el manifiesto."
else
  echo "El cubo no es el del manifiesto: se corre pap calcular."
  "${UVRUN[@]}" pap calcular --permitir-sucio   # la imagen no lleva .git: el manifiesto queda marcado «sucio»
fi

exec "${UVRUN[@]}" pap servir --red-local --puerto "$PUERTO"
