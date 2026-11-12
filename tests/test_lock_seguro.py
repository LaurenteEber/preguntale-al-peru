"""Control C2 (M0-00b): `uv.lock` solo trae paquetes de PyPI, con hash en cada archivo y con al menos 14 días de publicados,
salvo las excepciones registradas en `curados/inferencia/parametros.yaml` (`seguridad.lock_excepciones`). Sin red."""
import tomllib
from datetime import datetime, timedelta, timezone

import pytest
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


# Las comprobaciones son funciones que reciben los paquetes: la prueba de control las usa con un lock falso (M1-02, H00b-1).

def paquetes_fuera_de_pypi(paquetes):
    return [f'{p["name"]} {p["source"]}' for p in paquetes if p["source"].get("registry") != PYPI]


def paquetes_sin_hash(paquetes):
    return [p["name"] for p in paquetes if not _archivos(p) or any(not a.get("hash", "").startswith("sha256:") for a in _archivos(p))]


def paquetes_recientes(paquetes, dias_min, excepciones=(), ahora=None):
    """`nombre==versión` de los paquetes con algún archivo publicado hace menos de `dias_min` días. Un archivo sin fecha es un error."""
    limite = (ahora or datetime.now(timezone.utc)) - timedelta(days=dias_min)
    recientes = []
    for p in paquetes:
        if f'{p["name"]}=={p["version"]}' in excepciones:
            continue
        fechas = [a.get("upload-time") for a in _archivos(p)]
        assert all(fechas), f'{p["name"]}: archivo sin fecha de publicación'
        if any(datetime.fromisoformat(f.replace("Z", "+00:00")) > limite for f in fechas):
            recientes.append(f'{p["name"]}=={p["version"]}')
    return recientes


def test_todo_paquete_viene_de_pypi_con_hash():
    paquetes = _de_terceros()
    assert len(paquetes) > 50
    assert not paquetes_fuera_de_pypi(paquetes)
    assert not paquetes_sin_hash(paquetes)


def test_ningun_paquete_con_menos_de_14_dias_sin_excepcion():
    par = _parametros()
    excepciones = {e["paquete"] for e in par["lock_excepciones"]}
    assert not paquetes_recientes(_de_terceros(), par["lock_dias_min"]["valor"], excepciones)


def test_las_comprobaciones_reales_detectan_un_lock_malo():
    """La prueba no es vacua: un lock sintético con un paquete de otra fuente y sin hash, y uno publicado hoy, pasa por las MISMAS
    funciones que revisan el lock real y las tres lo marcan."""
    hoy = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    antiguo = "2020-01-01T00:00:00Z"
    malo = {"name": "x", "version": "1", "source": {"registry": "https://otro.example/simple"}, "wheels": [{"url": "u", "upload-time": hoy}]}
    bueno = {"name": "y", "version": "2", "source": {"registry": PYPI}, "wheels": [{"url": "u", "hash": "sha256:ab", "upload-time": antiguo}]}
    assert paquetes_fuera_de_pypi([malo, bueno]) == ["x {'registry': 'https://otro.example/simple'}"]
    assert paquetes_sin_hash([malo, bueno]) == ["x"]
    assert paquetes_recientes([malo, bueno], 14) == ["x==1"]
    assert paquetes_recientes([malo, bueno], 14, excepciones={"x==1"}) == []          # la excepción registrada sí exime
    sin_fecha = {**bueno, "wheels": [{"url": "u", "hash": "sha256:ab"}]}
    with pytest.raises(AssertionError, match="sin fecha"):
        paquetes_recientes([sin_fecha], 14)


def test_el_lock_cumple_las_restricciones_de_seguridad():
    versiones = {p["name"]: tuple(int(x) for x in p["version"].split(".")[:3]) for p in _lock()}
    assert versiones["pillow"] >= (13, 0, 0)                       # A1
    assert versiones["certifi"] >= (2026, 10, 18)                 # A2 (2026.10.18 o más)
    assert versiones["python-multipart"] >= (0, 0, 32)            # A4
