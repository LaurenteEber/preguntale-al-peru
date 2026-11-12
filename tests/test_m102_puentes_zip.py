"""M1-02, tarea 7 (H00b-7): el ZIP del SIEN se abre con `abrir_zip_seguro`."""
import zipfile
from types import SimpleNamespace

import pytest

from pap.capa0 import puentes
from pap.config import Rutas
from pap.zip_seguro import ZipInseguro

CSV = "Renipress,EESS,Ubigeo_EESS\n00001234,Posta,010101\n"


def _insumo(zip_):
    return SimpleNamespace(ruta=zip_, hash="sha256:abc", nombre="sien")


def _llamar(monkeypatch, zip_):
    monkeypatch.setattr(puentes.insumos, "ultimo", lambda *a, **k: _insumo(zip_))
    res = puentes.Resultado()
    return puentes.establecimientos_sien(Rutas(zip_.parent), res, {"010101"}), res


def test_un_zip_del_sien_con_ruta_con_puntos_puntos_se_rechaza(tmp_path, monkeypatch):
    z = tmp_path / "sien.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("Hb/../../fuera.csv", CSV)
    with pytest.raises(ZipInseguro):
        _llamar(monkeypatch, z)


def test_un_zip_del_sien_bueno_se_lee_como_antes(tmp_path, monkeypatch):
    z = tmp_path / "sien.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("Pt/DIRESA1.csv", CSV)
        zf.writestr("LEEME.txt", "no es un CSV")
    sien, _ = _llamar(monkeypatch, z)
    assert sien.to_dict("records") == [{"cod_ipress": "00001234", "ubigeo_eess": "010101", "EESS": "Posta"}]
