#!/usr/bin/env bash
# M0-00b (C3): busca vulnerabilidades conocidas en uv.lock con dos fuentes: pip-audit (PyPI Advisory / OSV) y osv-scanner (OSV,
# que incluye los CVE de VulnCheck y RustSec). Sale con error si cualquiera encuentra algo. Necesita red.
# Uso: scripts/auditar.sh      (o: just auditar)   Instalación de osv-scanner: brew install osv-scanner
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ"
PIP_AUDIT="pip-audit==2.10.1"    # versión con > 2 semanas de publicada (10/6/2026)

command -v osv-scanner >/dev/null 2>&1 || { echo "ERROR: falta osv-scanner (brew install osv-scanner)" >&2; exit 2; }
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "== pip-audit sobre uv.lock =="
uv export --locked --no-emit-project --format requirements-txt -o "$TMP/requirements.txt" >/dev/null
uvx "$PIP_AUDIT" -r "$TMP/requirements.txt" --no-deps --disable-pip --progress-spinner off

echo "== osv-scanner sobre uv.lock =="
osv-scanner scan source -L uv.lock
echo "Auditoría limpia."
