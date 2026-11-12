"""M1-02, tarea 4 (H04-2): `convertir` escribe en una carpeta de preparación y cambia Parquet y manifiesto juntos."""
import json
import zipfile

import pytest
import yaml

from pap.capa0.insumos import Insumo
from pap.config import Rutas
from pap.errores import PapError
from pap.inferencia import almacen
from pap.util import sha256

from .test_conversor_sintetico import _dta, _hogar


def _proyecto(tmp_path, monkeypatch, *, segundo_roto: bool):
    (tmp_path / "curados" / "inferencia" / "descargas").mkdir(parents=True, exist_ok=True)
    (tmp_path / "curados" / "inferencia" / "descargas" / "endes_2099.yaml").write_text(yaml.safe_dump(
        {"fuente": "INEI-ENDES", "modulos": [{"codigo": 1, "formato": "STATA", "recurso": "r1"},
                                              {"codigo": 2, "formato": "STATA", "recurso": "r2"}]}))
    zips = {}
    for rec, nombre in (("r1", "RECH0"), ("r2", "RECH1")):
        z = tmp_path / f"{rec}.zip"
        with zipfile.ZipFile(z, "w") as zf:
            if rec == "r2" and segundo_roto:
                zf.writestr(f"m/{nombre}_2099.dta", b"esto no es un DTA")
            else:
                zf.write(_dta(tmp_path / f"{nombre}_2099.dta", _hogar()), f"m/{nombre}_2099.dta")
        zips[rec] = z
    monkeypatch.setattr(almacen, "_insumo", lambda rutas, fuente, recurso: Insumo(
        fuente, recurso, "sha256:" + sha256(zips[recurso]), zips[recurso], f"{recurso}.zip", None, "2026-11-09T10:00:00-05:00"))
    return tmp_path / "biblioteca" / "microdatos" / "ENDES" / "2099"


def _foto(carpeta):
    return {p.name: p.read_bytes() for p in sorted(carpeta.iterdir())} if carpeta.exists() else None


def test_una_falla_a_mitad_de_camino_deja_la_carpeta_anterior_intacta_y_sin_restos(tmp_path, monkeypatch):
    destino = _proyecto(tmp_path, monkeypatch, segundo_roto=False)
    almacen.convertir(Rutas(tmp_path), "ENDES", 2099, log=lambda *_: None)
    antes = _foto(destino)
    assert set(antes) == {"RECH0.parquet", "RECH1.parquet", "manifiesto.json"}
    _proyecto(tmp_path, monkeypatch, segundo_roto=True)
    with pytest.raises(PapError):
        almacen.convertir(Rutas(tmp_path), "ENDES", 2099, log=lambda *_: None)
    assert _foto(destino) == antes                                    # ni Parquet nuevos con el manifiesto viejo ni al revés
    assert sorted(p.name for p in destino.parent.iterdir()) == ["2099"]       # sin carpeta de preparación


def test_una_falla_sin_carpeta_previa_no_deja_nada(tmp_path, monkeypatch):
    destino = _proyecto(tmp_path, monkeypatch, segundo_roto=True)
    with pytest.raises(PapError):
        almacen.convertir(Rutas(tmp_path), "ENDES", 2099, log=lambda *_: None)
    assert not destino.exists()
    assert not destino.parent.exists() or not list(destino.parent.iterdir())


def test_una_conversion_buena_cambia_parquet_y_manifiesto_juntos_y_conserva_otros_archivos(tmp_path, monkeypatch):
    destino = _proyecto(tmp_path, monkeypatch, segundo_roto=False)
    destino.mkdir(parents=True)
    (destino / "otro.txt").write_text("de otro proceso")
    (destino / "RECH0.parquet").write_bytes(b"viejo")
    almacen.convertir(Rutas(tmp_path), "ENDES", 2099, log=lambda *_: None)
    man = json.loads((destino / "manifiesto.json").read_text())["archivos"]
    assert set(man) == {"RECH0", "RECH1"} and (destino / "RECH0.parquet").read_bytes() != b"viejo"
    assert (destino / "otro.txt").read_text() == "de otro proceso"
    assert sorted(p.name for p in destino.parent.iterdir()) == ["2099"]


def test_si_un_corte_dejo_la_carpeta_anterior_apartada_se_recupera_al_empezar(tmp_path, monkeypatch):
    destino = _proyecto(tmp_path, monkeypatch, segundo_roto=True)
    apartada = destino.with_name(".2099.anterior")
    apartada.mkdir(parents=True)
    (apartada / "manifiesto.json").write_text("{}")
    with pytest.raises(PapError):
        almacen.convertir(Rutas(tmp_path), "ENDES", 2099, log=lambda *_: None)
    assert (destino / "manifiesto.json").read_text() == "{}" and not apartada.exists()
