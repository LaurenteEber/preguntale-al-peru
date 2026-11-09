"""M0-02 (tarea 5/7): los scripts de respaldo y restauración se niegan ante un repo público o distinto del configurado.
`gh` se reemplaza por un programa falso en PATH: no hay red ni token real."""
import os
import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import RAIZ_REAL

REPO = yaml.safe_load((RAIZ_REAL / "curados/inferencia/parametros.yaml").read_text(encoding="utf-8"))["almacen"]["repo_crudos"]["valor"]
SCRIPTS = ["scripts/respaldar_crudos.sh", "scripts/restaurar_crudos.sh"]
SECRETO = "gh" + "p_" + "SECRETO_DE_PRUEBA_123"   # token falso, armado por partes para que gitleaks no lo tome por uno real


@pytest.fixture
def entorno(tmp_path):
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    registro = tmp_path / "llamadas.txt"
    gh = bin_ / "gh"
    gh.write_text(
        '#!/usr/bin/env bash\necho "$*" >> "$GH_REGISTRO"\n'
        'if [ "$1 $2" = "repo view" ]; then echo "$GH_VISIBILIDAD"; exit 0; fi\n'
        'exit 0\n'
    )
    gh.chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_}:{os.environ['PATH']}", "GH_REGISTRO": str(registro), "GH_TOKEN": SECRETO, "GH_VISIBILIDAD": "PRIVATE"}
    return env, registro


def _correr(script, env, *args):
    return subprocess.run(["bash", str(RAIZ_REAL / script), *args], env=env, capture_output=True, text=True, cwd=RAIZ_REAL)


def _llamadas(registro):
    return registro.read_text().splitlines() if registro.exists() else []


@pytest.mark.parametrize("script", SCRIPTS)
def test_se_niega_ante_un_repo_publico(script, entorno):
    env, registro = entorno
    env["GH_VISIBILIDAD"] = "PUBLIC"
    r = _correr(script, env)
    assert r.returncode == 1 and "no es privado" in r.stderr
    assert SECRETO not in r.stdout + r.stderr
    assert not [x for x in _llamadas(registro) if "release" in x]


@pytest.mark.parametrize("script", SCRIPTS)
def test_se_niega_ante_otro_repo(script, entorno):
    env, registro = entorno
    r = _correr(script, env, "--repo", "otro/repositorio")
    assert r.returncode == 1 and "no es el configurado" in r.stderr
    assert _llamadas(registro) == []


@pytest.mark.parametrize("script", SCRIPTS)
def test_se_niega_sin_token(script, entorno):
    env, registro = entorno
    del env["GH_TOKEN"]
    env["PAP_LLAVERO_SERVICIO"] = "pap-servicio-que-no-existe"
    r = _correr(script, env)
    assert r.returncode == 1 and "Falta GH_TOKEN" in r.stderr
    assert [x for x in _llamadas(registro) if "release" in x] == []


def test_simulacion_privada_arma_paquete_y_no_sube(entorno):
    env, registro = entorno
    r = _correr("scripts/respaldar_crudos.sh", env, "--repo", REPO, "--simular")
    assert r.returncode == 0, r.stderr
    assert "simulación" in r.stdout and SECRETO not in r.stdout + r.stderr
    llamadas = _llamadas(registro)
    assert llamadas == [f"repo view {REPO} --json visibility -q .visibility"]
