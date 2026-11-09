#!/usr/bin/env bash
# Restaura los ZIP y PDF de la ENDES 2024 desde el release `crudos-endes-2024` del repo PRIVADO de crudos (M0-02; en M0-11 pasa a
# `pap almacen restaurar`). Baja a un directorio temporal, comprueba SHA256SUMS y compara con las huellas de los datapackage.json.
# Uso: scripts/restaurar_crudos.sh [--repo DUEÑO/REPO]    Resultado: imprime OK/DIFERENTE por archivo; sale con 1 si algo difiere.
# Misma guardia que respaldar_crudos.sh: repo igual al configurado y PRIVATE. El token nunca se imprime (C12).
set -euo pipefail

RAIZ="${PAP_RAIZ:-$(cd "$(dirname "$0")/.." && pwd)}"
ETIQUETA="crudos-endes-2024"

repo_pedido=""
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) repo_pedido="${2:?falta el repo}"; shift 2 ;;
    *) echo "Uso: $0 [--repo DUEÑO/REPO]" >&2; exit 2 ;;
  esac
done

repo=$(sed -n 's/^[[:space:]]*repo_crudos:[[:space:]]*{valor:[[:space:]]*"\([^"]*\)".*/\1/p' "$RAIZ/curados/inferencia/parametros.yaml")
[ -n "$repo" ] || { echo "No se encontró almacen.repo_crudos en curados/inferencia/parametros.yaml" >&2; exit 1; }
if [ -n "$repo_pedido" ] && [ "$repo_pedido" != "$repo" ]; then
  echo "Me niego: el repo pedido ($repo_pedido) no es el configurado ($repo)." >&2; exit 1
fi

if [ -z "${GH_TOKEN:-}" ] && command -v security >/dev/null 2>&1; then
  GH_TOKEN=$(security find-generic-password -s "${PAP_LLAVERO_SERVICIO:-pap-gh-crudos}" -w 2>/dev/null || true)
fi
export GH_TOKEN
[ -n "${GH_TOKEN:-}" ] || { echo "Falta GH_TOKEN (variable de entorno o Llavero de macOS; K-09)." >&2; exit 1; }

visibilidad=$(gh repo view "$repo" --json visibility -q .visibility 2>/dev/null | tr '[:lower:]' '[:upper:]' || true)
if [ "$visibilidad" != "PRIVATE" ]; then
  echo "Me niego: $repo no es privado (visibilidad: ${visibilidad:-desconocida})." >&2; exit 1
fi

trabajo=$(mktemp -d)
trap 'rm -rf "$trabajo"' EXIT
gh release download "$ETIQUETA" --repo "$repo" --dir "$trabajo"
( cd "$trabajo" && shasum -a 256 -c SHA256SUMS )

# Unir las partes y comparar con las huellas registradas.
python3 -I - "$RAIZ" "$trabajo" <<'PY'
import glob, hashlib, json, os, sys
raiz, d = sys.argv[1:3]
malo = 0
for dp in sorted(glob.glob(os.path.join(raiz, "biblioteca/cruda/capturas/INEI-ENDES/*/datapackage.json"))):
    for r in json.load(open(dp, encoding="utf-8"))["resources"]:
        if not r["name"].startswith("endes-2024-"):
            continue
        f = os.path.join(d, r["original_filename"])
        partes = sorted(glob.glob(f + ".parte-*"))
        if not os.path.exists(f) and not partes:
            continue   # 1629 y 1638 no se respaldan de nuevo si ya estaban en otro release
        h = hashlib.sha256()
        for p in ([f] if os.path.exists(f) else partes):
            with open(p, "rb") as fh:
                for b in iter(lambda: fh.read(1 << 20), b""):
                    h.update(b)
        ok = "sha256:" + h.hexdigest() == r["hash"]
        malo += not ok
        print(("OK" if ok else "DIFERENTE"), r["name"])
sys.exit(1 if malo else 0)
PY
