"""Control C2 (M0-00b): `uv.lock` solo trae paquetes de PyPI, con hash en cada archivo y con al menos 14 días de publicados,
salvo las excepciones registradas en `curados/inferencia/parametros.yaml` (`seguridad.lock_excepciones`). Sin red."""
import tomllib
from datetime import datetime, timedelta, timezone

import yaml

from conftest import RAIZ_REAL

PYPI = "https://pypi.org/simple"


def _lock():
    return tomllib.loads((RAIZ_REAL / "uv.lock").read_text(encoding="utf-8"))["package"]


def _parametros():
    return yaml.safe_load((RAIZ_REAL / "curados/inferencia/parametros.yaml").read_text(encoding="utf-8"))["seguridad"]


def _archivos(paquete):
    return ([paquete["sdist"]] if "sdist" in paquete else []) + list(paquete.get("wheels", []))


def _de_terceros():
    return [p for p in _lock() if "editable" not in p["source"] and "virtual" not in p["source"]]


def test_todo_paquete_viene_de_pypi_con_hash():
    paquetes = _de_terceros()
    assert len(paquetes) > 50
    fuera = [f'{p["name"]} {p["source"]}' for p in paquetes if p["source"].get("registry") != PYPI]
    assert not fuera, fuera
    sin_hash = [p["name"] for p in paquetes if not _archivos(p) or any(not a.get("hash", "").startswith("sha256:") for a in _archivos(p))]
    assert not sin_hash, sin_hash


def test_ningun_paquete_con_menos_de_14_dias_sin_excepcion():
    par = _parametros()
    limite = datetime.now(timezone.utc) - timedelta(days=par["lock_dias_min"]["valor"])
    excepciones = {e["paquete"] for e in par["lock_excepciones"]}
    recientes = []
    for p in _de_terceros():
        if f'{p["name"]}=={p["version"]}' in excepciones:
            continue
        fechas = [a.get("upload-time") for a in _archivos(p)]
        assert all(fechas), f'{p["name"]}: archivo sin fecha de publicación'
        if any(datetime.fromisoformat(f.replace("Z", "+00:00")) > limite for f in fechas):
            recientes.append(f'{p["name"]}=={p["version"]}')
    assert not recientes, recientes


def test_la_prueba_detecta_un_paquete_reciente_o_de_otra_fuente(monkeypatch):
    """La prueba no es vacua: con un lock sintético con un paquete de otra fuente y sin hash, y uno publicado hoy, falla."""
    import test_lock_seguro as t

    hoy = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    falso = [{"name": "x", "version": "1", "source": {"registry": "https://otro.example/simple"},
              "wheels": [{"url": "u", "upload-time": hoy}]}]
    monkeypatch.setattr(t, "_lock", lambda: falso)
    paquetes = t._de_terceros()
    assert paquetes[0]["source"]["registry"] != PYPI
    assert not t._archivos(paquetes[0])[0].get("hash")
    assert datetime.fromisoformat(t._archivos(paquetes[0])[0]["upload-time"].replace("Z", "+00:00")) > datetime.now(timezone.utc) - timedelta(days=14)


def test_el_lock_cumple_las_restricciones_de_seguridad():
    versiones = {p["name"]: tuple(int(x) for x in p["version"].split(".")[:3]) for p in _lock()}
    assert versiones["pillow"] >= (13, 0, 0)                       # A1
    assert versiones["certifi"] >= (2026, 10, 18)                 # A2 (2026.10.18 o más)
    assert versiones["python-multipart"] >= (0, 0, 32)            # A4
