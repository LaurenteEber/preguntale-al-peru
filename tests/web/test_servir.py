"""S3-09 — `pap servir`: dirección elegida, texto impreso, ayuda y un arranque real (subprocess) que responde /salud."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
import yaml

from pap import cli

RAIZ = Path(__file__).resolve().parents[2]
MSGS = yaml.safe_load((RAIZ / "curados/motor/textos/cli.yaml").read_text(encoding="utf-8"))["mensajes"]
SERVICIO = yaml.safe_load((RAIZ / "curados/web/parametros.yaml").read_text(encoding="utf-8"))["servicio"]


@pytest.fixture
def corridas(monkeypatch):
    """Reemplaza el arranque real de uvicorn: guarda (host, puerto) y no bloquea."""
    vistas = []
    monkeypatch.setattr("pap.web.servir._correr", lambda app, host, puerto: vistas.append((host, puerto)))
    monkeypatch.setattr("pap.web.servir.crear_app", lambda raiz, **kw: object())
    return vistas


def test_por_defecto_solo_este_equipo_y_puerto_de_parametros(corridas, capsys):
    assert cli.main(["servir"]) == 0
    host, puerto = SERVICIO["host"]["valor"], SERVICIO["puerto"]["valor"]
    assert host == "127.0.0.1" and corridas == [(host, puerto)]
    assert MSGS["servir_local"].format(direccion=f"http://{host}:{puerto}") in capsys.readouterr().out


def test_puerto_elegido(corridas, capsys):
    assert cli.main(["servir", "--puerto", "8123"]) == 0
    assert corridas == [("127.0.0.1", 8123)]
    assert "http://127.0.0.1:8123" in capsys.readouterr().out


def test_red_local_escucha_en_todas_las_interfaces_y_lo_dice(corridas, capsys):
    assert cli.main(["servir", "--red-local", "--puerto", "8124"]) == 0
    assert corridas == [("0.0.0.0", 8124)]
    assert MSGS["servir_red_local"].format(direccion="http://0.0.0.0:8124", puerto=8124) in capsys.readouterr().out


@pytest.mark.parametrize("malo", ["0", "70000", "abc"])
def test_puerto_invalido_no_arranca(corridas, malo, capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["servir", "--puerto", malo])
    assert e.value.code == 2 and corridas == []


def test_la_ayuda_lista_servir_y_sus_opciones(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    assert "servir" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        cli.main(["servir", "--help"])
    ayuda = capsys.readouterr().out
    assert "--puerto" in ayuda and "--red-local" in ayuda


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_arranque_real_responde_salud_en_local():
    assert (RAIZ / "biblioteca/indicadores/fact_indicador.parquet").exists(), "falta el cubo"   # falla, no se salta
    puerto = _puerto_libre()
    env = {**os.environ, "PAP_RAIZ": str(RAIZ), "PYTHONUNBUFFERED": "1"}
    p = subprocess.Popen([sys.executable, "-m", "pap.cli", "servir", "--puerto", str(puerto)], cwd=RAIZ, env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        primera = p.stdout.readline()
        assert f"http://127.0.0.1:{puerto}" in primera
        estado, fin = None, time.monotonic() + 150
        while time.monotonic() < fin and p.poll() is None:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/salud", timeout=5) as r:
                    estado = r.status
                    break
            except Exception:  # noqa: BLE001 — 503 mientras precalienta, o aún no escucha
                time.sleep(1)
        assert estado == 200
    finally:
        p.terminate()
        try:
            p.wait(15)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
