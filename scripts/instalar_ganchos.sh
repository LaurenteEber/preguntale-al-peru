#!/usr/bin/env bash
# M0-00b (C9): instala el gancho antes de cada commit (scripts/ganchos/pre-commit) apuntando git a scripts/ganchos/.
# Uso: scripts/instalar_ganchos.sh      Requiere gitleaks (brew install gitleaks). Para quitarlo: git config --unset core.hooksPath
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
command -v gitleaks >/dev/null 2>&1 || { echo "ERROR: falta gitleaks (brew install gitleaks)" >&2; exit 1; }
chmod +x "$RAIZ/scripts/ganchos/pre-commit"
git -C "$RAIZ" config core.hooksPath scripts/ganchos
echo "Gancho instalado: gitleaks $(gitleaks version) revisará cada commit."
