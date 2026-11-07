#!/usr/bin/env bash
# Lista el código HTTP de cada enlace que el motor puede poner en una cita (S3-01b, fila 8; supuesto S3-01-b).
# Uso: scripts/comprobar_enlaces.sh      (necesita red; se corre en el Mac antes de cada cierre)
# Los enlaces salen igual que en src/pap/motor/capas.py `_url`: la columna `url` de curados/capa0/cifras_doradas.csv
# y, para las fuentes que el motor cita (indicadores, doradas y las que nombra el código del motor), `url_portal`
# (si no, `url_datos`) de catalogo/catalogo_fuentes.csv. Sin deduplicar a mano: se quitan los repetidos.
# Una línea por enlace: «código  enlace». Sale con error si alguno no es 2xx/3xx (un error de certificado cuenta
# como falla: nunca se usa -k). Se manda un User-Agent de navegador porque datosabiertos.gob.pe responde 418 al de curl.
# Solo lee archivos del repositorio.
set -uo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"

ENLACES="$(python3 -I - "$RAIZ" <<'PY'
import csv, re, sys
from pathlib import Path

raiz = Path(sys.argv[1])
urls = []
fuentes = set(re.findall(r"fuente_principal:\s*(\S+)", (raiz / "curados/capa0/dim_indicador.yaml").read_text(encoding="utf-8")))
with open(raiz / "curados/capa0/cifras_doradas.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        if (r.get("url") or "").strip():
            urls.append(r["url"].strip())
        fuentes.add(r["fuente_id"])
codigo = "\n".join(p.read_text(encoding="utf-8") for p in (raiz / "src/pap/motor").rglob("*.py"))
with open(raiz / "catalogo/catalogo_fuentes.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        if r["id"] in fuentes or f'"{r["id"]}"' in codigo:
            u = (r.get("url_portal") or r.get("url_datos") or "").strip()
            if u:
                urls.append(u)
print("\n".join(dict.fromkeys(urls)))
PY
)"

fallas=0
total=0
while IFS= read -r url; do
  [ -z "$url" ] && continue
  total=$((total + 1))
  codigo="$(curl -sS -o /dev/null -w '%{http_code}' -L -A 'Mozilla/5.0' --max-time 20 "$url" 2>/dev/null)" || true
  codigo="${codigo:-000}"
  echo "$codigo  $url"
  case "$codigo" in
    2??|3??) ;;
    *) fallas=$((fallas + 1)) ;;
  esac
done <<< "$ENLACES"

echo "---"
echo "$total enlaces; $fallas con falla"
[ "$fallas" -eq 0 ]
