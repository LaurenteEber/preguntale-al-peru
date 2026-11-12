"""M1-02, tarea 6 (H00b-2): `scripts/auditar.sh` usa herramientas con versión fijada y huellas, y se detiene si la versión no es la auditada."""
import os
import re
import stat
import subprocess

import pytest

from conftest import RAIZ_REAL

SCRIPT = RAIZ_REAL / "scripts" / "auditar.sh"


def _texto():
    return SCRIPT.read_text(encoding="utf-8")


def test_el_script_no_usa_uvx_y_fija_las_tres_herramientas():
    t = _texto()
    assert "uvx" not in t
    for var in ("PIP_AUDIT_VERSION", "OSV_SCANNER_VERSION", "GITLEAKS_VERSION"):
        assert re.search(rf'^{var}="\d+\.\d+\.\d+"', t, re.M), var
    assert "--require-hashes" in t


def test_la_lista_de_pip_audit_fija_cada_paquete_con_huella_y_trae_pip_audit():
    t = _texto()
    lista = t.split("<<'REQUISITOS'\n")[1].split("\nREQUISITOS\n")[0]
    bloques = re.split(r"\n(?=[A-Za-z0-9_.-]+==)", lista)
    assert len(bloques) > 10
    for b in bloques:
        assert re.match(r"[A-Za-z0-9_.-]+==[\w.]+ \\\n", b) and re.search(r"--hash=sha256:[0-9a-f]{64}", b), b[:80]
    version = re.search(r'^PIP_AUDIT_VERSION="([\d.]+)"', t, re.M).group(1)
    assert f"pip-audit=={version} " in lista


def test_la_sintaxis_del_script_es_valida():
    assert subprocess.run(["bash", "-n", str(SCRIPT)]).returncode == 0
    assert os.stat(SCRIPT).st_mode & stat.S_IXUSR


@pytest.mark.parametrize("herramienta,argumentos,salida", [
    ("osv-scanner", [], "osv-scanner version: 0.0.1"),
    ("gitleaks", ["--secretos"], "0.0.1"),
])
def test_si_la_version_instalada_no_es_la_auditada_el_script_se_detiene_sin_correr_nada(tmp_path, herramienta, argumentos, salida):
    falsa = tmp_path / herramienta
    falsa.write_text(f'#!/bin/sh\necho "{salida}"\n')
    falsa.chmod(0o755)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}
    r = subprocess.run([str(SCRIPT), *argumentos], capture_output=True, text=True, env=env, cwd=RAIZ_REAL)
    assert r.returncode == 2 and "no es la versión auditada" in r.stderr
    assert "pip-audit" not in r.stdout
