#!/usr/bin/env bash
# Baja los Parquet de la biblioteca desde un release de GitHub y comprueba sus huellas (decisión F-05).
# Uso: scripts/bajar_biblioteca.sh [etiqueta]   (por defecto, biblioteca-010ea965)
# S3-01b (fila 10): el release `biblioteca-010ea965` (6/11/2026) trae la biblioteca del cubo actual; `biblioteca-ba1fbc55` es el
# anterior. DESPUÉS DE BAJAR el release hay que correr `uv run pap calcular`: reconstruye
# el cubo con el código de hoy; sin eso, pytest se detiene con «el cubo local no es el del manifiesto: corre `pap calcular`».
# Solo escribe dentro de biblioteca/ (archivos fuera de git). No toca los crudos, los manifiestos ni nada versionado.
set -euo pipefail

ETIQUETA="${1:-biblioteca-010ea965}"
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
# El paquete se armó en macOS: GNU tar avisa de sus atributos extendidos; se silencian solo esos avisos.
TAR_OPC=""
tar --version 2>/dev/null | grep -q GNU && TAR_OPC="--warning=no-unknown-keyword"
if command -v zstd >/dev/null 2>&1; then
  zstd -dc "$TMP/$ETIQUETA.tar.zst" | tar -x $TAR_OPC -C "$RAIZ"
else   # zstandard ya es dependencia del proyecto (uv.lock)
  (cd "$RAIZ" && uv run --frozen python -c "import sys,zstandard; zstandard.ZstdDecompressor().copy_stream(open(sys.argv[1],'rb'), sys.stdout.buffer)" "$TMP/$ETIQUETA.tar.zst") | tar -x $TAR_OPC -C "$RAIZ"
fi

# La etiqueta nombra la huella del cubo: se comprueba aquí; el resto de tablas lo comprueba insumos.tabla() al usarlas.
ESPERADA="${ETIQUETA#biblioteca-}"
REAL="$(sha256sum "$RAIZ/biblioteca/indicadores/fact_indicador.parquet" | cut -c1-${#ESPERADA})"
if [ "$REAL" != "$ESPERADA" ]; then
  echo "ERROR: la huella del cubo es $REAL y debía ser $ESPERADA" >&2
  exit 1
fi
echo "Siguiente paso: uv run pap calcular   (el cubo bajado es el anterior; pytest se detiene si no coincide con el manifiesto)"
echo "Listo: $(find "$RAIZ/biblioteca" -name '*.parquet' -not -path '*/_respaldo*' | wc -l | tr -d ' ') Parquet; cubo $REAL…"
