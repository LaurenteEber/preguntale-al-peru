"""M1-02 (H00b-2): el gancho antes de cada commit exige la versión de gitleaks que fija scripts/auditar.sh."""
import os
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
GANCHO = RAIZ / "scripts/ganchos/pre-commit"


def _version_auditada() -> str:
    return re.search(r'^GITLEAKS_VERSION="([^"]+)"', (RAIZ / "scripts/auditar.sh").read_text(), re.M).group(1)


def _correr_con_gitleaks_falso(tmp_path: Path, version: str) -> subprocess.CompletedProcess:
    falso = tmp_path / "bin" / "gitleaks"
    falso.parent.mkdir()
    falso.write_text(f'#!/bin/sh\nif [ "$1" = version ]; then echo {version}; else echo "revisado $*"; fi\n')
    falso.chmod(0o755)
    entorno = {**os.environ, "PATH": f"{falso.parent}{os.pathsep}{os.environ['PATH']}"}
    return subprocess.run(["bash", str(GANCHO)], cwd=RAIZ, env=entorno, capture_output=True, text=True)


def test_el_gancho_se_detiene_si_gitleaks_no_es_la_version_auditada(tmp_path):
    r = _correr_con_gitleaks_falso(tmp_path, "0.0.1")
    assert r.returncode == 1
    assert f"gitleaks 0.0.1 no es la versión auditada ({_version_auditada()}" in r.stderr
    assert "revisado" not in r.stdout


def test_el_gancho_revisa_lo_preparado_con_la_version_auditada(tmp_path):
    r = _correr_con_gitleaks_falso(tmp_path, _version_auditada())
    assert r.returncode == 0
    assert r.stdout.strip() == "revisado git --pre-commit --staged --redact --no-banner"
