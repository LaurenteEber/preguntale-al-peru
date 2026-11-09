#!/usr/bin/env bash
# Respalda los ZIP y PDF de la ENDES 2024 en el repo PRIVADO de crudos (M0-02; F-03; diseño §6).
# Uso: scripts/respaldar_crudos.sh [--repo DUEÑO/REPO] [--simular]
#   --repo     solo para comprobar que coincide con `almacen.repo_crudos` de curados/inferencia/parametros.yaml; si difiere, se niega.
#   --simular  hace todas las comprobaciones y arma el paquete, pero no sube nada.
# Se niega si `gh repo view --json visibility` no dice PRIVATE. El token (GH_TOKEN, o el Llavero de macOS) nunca se imprime (C12).
# Variables: PAP_RAIZ (raíz del repo, por defecto la de este script), PAP_LLAVERO_SERVICIO (servicio del Llavero).
set -euo pipefail

RAIZ="${PAP_RAIZ:-$(cd "$(dirname "$0")/.." && pwd)}"
ETIQUETA="crudos-endes-2024"
RECURSOS_PREFIJO="endes-2024-"
LIMITE_BYTES=$((2 * 1024 * 1024 * 1024))
PARTE="1900m"   # menos de 2 GiB por archivo (límite de GitHub)

repo_pedido=""; simular=0
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) repo_pedido="${2:?falta el repo}"; shift 2 ;;
    --simular) simular=1; shift ;;
    *) echo "Uso: $0 [--repo DUEÑO/REPO] [--simular]" >&2; exit 2 ;;
  esac
done

repo=$(sed -n 's/^[[:space:]]*repo_crudos:[[:space:]]*{valor:[[:space:]]*"\([^"]*\)".*/\1/p' "$RAIZ/curados/inferencia/parametros.yaml")
[ -n "$repo" ] || { echo "No se encontró almacen.repo_crudos en curados/inferencia/parametros.yaml" >&2; exit 1; }
if [ -n "$repo_pedido" ] && [ "$repo_pedido" != "$repo" ]; then
  echo "Me niego: el repo pedido ($repo_pedido) no es el configurado ($repo)." >&2; exit 1
fi

# El token solo viaja en el entorno de los comandos de gh; no se imprime.
if [ -z "${GH_TOKEN:-}" ] && command -v security >/dev/null 2>&1; then
  GH_TOKEN=$(security find-generic-password -s "${PAP_LLAVERO_SERVICIO:-pap-gh-crudos}" -w 2>/dev/null || true)
fi
export GH_TOKEN
[ -n "${GH_TOKEN:-}" ] || { echo "Falta GH_TOKEN (variable de entorno o Llavero de macOS; K-09)." >&2; exit 1; }

visibilidad=$(gh repo view "$repo" --json visibility -q .visibility 2>/dev/null | tr '[:lower:]' '[:upper:]' || true)
if [ "$visibilidad" != "PRIVATE" ]; then
  echo "Me niego: $repo no es privado (visibilidad: ${visibilidad:-desconocida}). Los crudos nunca van a un repo público." >&2; exit 1
fi

trabajo=$(mktemp -d)
trap 'rm -rf "$trabajo"' EXIT
paquete="$trabajo/paquete"; mkdir -p "$paquete"

# Archivos registrados de la ENDES 2024: ruta del almacén y nombre original, desde los datapackage.json.
python3 -I - "$RAIZ" "$RECURSOS_PREFIJO" "$paquete" <<'PY'
import glob, json, os, shutil, sys
raiz, prefijo, destino = sys.argv[1:4]
vistos = {}
for dp in sorted(glob.glob(os.path.join(raiz, "biblioteca/cruda/capturas/INEI-ENDES/*/datapackage.json"))):
    for r in json.load(open(dp, encoding="utf-8"))["resources"]:
        if r["name"].startswith(prefijo):
            vistos[r["name"]] = r
for nombre, r in sorted(vistos.items()):
    shutil.copyfile(os.path.join(raiz, "biblioteca/cruda", r["path"]), os.path.join(destino, r["original_filename"]))
    print(nombre, r["original_filename"])
PY
[ -n "$(ls -A "$paquete")" ] || { echo "No hay archivos ${RECURSOS_PREFIJO}* registrados." >&2; exit 1; }

# Partir lo que pase de 2 GB.
for f in "$paquete"/*; do
  if [ "$(wc -c < "$f")" -gt "$LIMITE_BYTES" ]; then
    split -b "$PARTE" -a 2 "$f" "$f.parte-"; rm "$f"
  fi
done

( cd "$paquete" && shasum -a 256 -- * > "$trabajo/SHA256SUMS" )
cat > "$trabajo/LEEME.txt" <<'TXT'
Crudos de la ENDES 2024 (INEI): microdatos en Stata (módulos 1629 a 1641) y documentos metodológicos en PDF.
Fuente: Instituto Nacional de Estadística e Informática (INEI), Encuesta Demográfica y de Salud Familiar (ENDES) 2024,
https://proyectos.inei.gob.pe/microdatos/ . Atribución al INEI. Licencia: ODbL 1.0.
Copia de respaldo de Pregúntale al Perú; no se modifica ningún archivo. Verificar con: shasum -a 256 -c SHA256SUMS
Los archivos de más de 2 GB se parten en `.parte-aa`, `.parte-ab`...; se unen con `cat`.
TXT
cp "$trabajo/SHA256SUMS" "$trabajo/LEEME.txt" "$paquete/"

echo "Destino: $repo (PRIVATE) · release $ETIQUETA · $(ls "$paquete" | wc -l | tr -d ' ') archivos"
if [ "$simular" -eq 1 ]; then echo "(simulación: no se sube nada)"; exit 0; fi

gh release view "$ETIQUETA" --repo "$repo" >/dev/null 2>&1 || \
  gh release create "$ETIQUETA" --repo "$repo" --title "Crudos ENDES 2024 (INEI)" \
     --notes "Respaldo de los ZIP y PDF de la ENDES 2024. Atribución al INEI; licencia ODbL 1.0. Ver LEEME.txt y SHA256SUMS."
gh release upload "$ETIQUETA" --repo "$repo" --clobber "$paquete"/*
echo "Listo: $ETIQUETA subido a $repo."
