"""A8 (M0-00b): la huella esperada del paquete de la biblioteca está versionada en `curados/releases.yaml` y
`scripts/bajar_biblioteca.sh` la compara; un release sin huella registrada se rechaza antes de bajar nada. Sin red."""
import re
import subprocess

import yaml

from conftest import RAIZ_REAL

SCRIPT = RAIZ_REAL / "scripts" / "bajar_biblioteca.sh"


def test_el_release_actual_tiene_huella_versionada():
    r = yaml.safe_load((RAIZ_REAL / "curados/releases.yaml").read_text(encoding="utf-8"))["releases"]["biblioteca-010ea965"]
    assert re.fullmatch(r"[0-9a-f]{64}", r["sha256"])
    assert r["archivo"] == "biblioteca-010ea965.tar.zst"


def test_el_script_compara_contra_el_repo_y_no_contra_el_release():
    texto = SCRIPT.read_text(encoding="utf-8")
    assert "curados/releases.yaml" in texto
    assert "SHA256SUMS" not in texto.replace("# ", "").split("set -euo pipefail", 1)[1]


def test_un_release_sin_huella_se_rechaza_sin_bajar_nada():
    r = subprocess.run(["bash", str(SCRIPT), "biblioteca-00000000"], capture_output=True, text=True, timeout=30)
    assert r.returncode == 1
    assert "no tiene huella registrada" in r.stderr
    assert "Bajando" not in r.stdout
