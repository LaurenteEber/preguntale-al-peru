#!/usr/bin/env bash
# Baja los Parquet de la biblioteca desde un release de GitHub y comprueba sus huellas (decisión X-11).
# Uso: scripts/bajar_biblioteca.sh [etiqueta]   (por defecto, biblioteca-ba1fbc55)
# Solo escribe dentro de biblioteca/ (archivos fuera de git). No toca los crudos, los manifiestos ni nada versionado.
set -euo pipefail

ETIQUETA="${1:-biblioteca-ba1fbc55}"
REPO="LaurenteEber/preguntale-al-peru"
BASE="https://github.com/$REPO/releases/download/$ETIQUETA"
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Bajando $ETIQUETA…"
curl -fsSL --retry 3 -o "$TMP/SHA256SUMS" "$BASE/SHA256SUMS"
curl -fsSL --retry 3 -o "$TMP/$ETIQUETA.tar.zst" "$BASE/$ETIQUETA.tar.zst"
(cd "$TMP" && sha256sum -c SHA256SUMS)

echo "Descomprimiendo en $RAIZ/biblioteca…"
if command -v zstd >/dev/null 2>&1; then
  zstd -dc "$TMP/$ETIQUETA.tar.zst" | tar -x -C "$RAIZ"
else   # zstandard ya es dependencia del proyecto (uv.lock)
  (cd "$RAIZ" && uv run --frozen python -c "import sys,zstandard; zstandard.ZstdDecompressor().copy_stream(open(sys.argv[1],'rb'), sys.stdout.buffer)" "$TMP/$ETIQUETA.tar.zst") | tar -x -C "$RAIZ"
fi

# La etiqueta nombra la huella del cubo: se comprueba aquí; el resto de tablas lo comprueba insumos.tabla() al usarlas.
ESPERADA="${ETIQUETA#biblioteca-}"
REAL="$(sha256sum "$RAIZ/biblioteca/indicadores/fact_indicador.parquet" | cut -c1-${#ESPERADA})"
if [ "$REAL" != "$ESPERADA" ]; then
  echo "ERROR: la huella del cubo es $REAL y debía ser $ESPERADA" >&2
  exit 1
fi
echo "Listo: $(find "$RAIZ/biblioteca" -name '*.parquet' -not -path '*/_respaldo*' | wc -l | tr -d ' ') Parquet; cubo $REAL…"
