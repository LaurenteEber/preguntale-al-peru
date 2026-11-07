"""S3-01b (fila 10): el cubo local debe ser el del manifiesto. La comprobación vive en tests/conftest.py y detiene la sesión
con un solo mensaje antes de correr ninguna prueba; aquí se prueba el comparador y que el cubo de este equipo coincide."""
import hashlib
import json

import conftest
from conftest import MENSAJE_CUBO_DISTINTO, RAIZ_REAL, discrepancia_cubo


def _cubo_falso(tmp_path, contenido: bytes, hash_declarado: str):
    ind = tmp_path / "biblioteca" / "indicadores"
    ind.mkdir(parents=True)
    (ind / "fact_indicador.parquet").write_bytes(contenido)
    (ind / "manifiesto_p1_indicadores.json").write_text(
        json.dumps({"tablas": {"fact_indicador": {"hash": f"sha256:{hash_declarado}"}}}), encoding="utf-8")
    return tmp_path


def test_el_mensaje_es_el_acordado():
    assert MENSAJE_CUBO_DISTINTO == "el cubo local no es el del manifiesto: corre `pap calcular`"


def test_cubo_distinto_da_el_mensaje_unico(tmp_path):
    raiz = _cubo_falso(tmp_path, b"cubo viejo", hashlib.sha256(b"cubo nuevo").hexdigest())
    assert discrepancia_cubo(raiz) == MENSAJE_CUBO_DISTINTO


def test_cubo_igual_no_da_mensaje(tmp_path):
    raiz = _cubo_falso(tmp_path, b"cubo", hashlib.sha256(b"cubo").hexdigest())
    assert discrepancia_cubo(raiz) is None


def test_cubo_ausente_no_aborta(tmp_path):
    raiz = _cubo_falso(tmp_path, b"x", "0" * 64)
    (raiz / "biblioteca/indicadores/fact_indicador.parquet").unlink()
    assert discrepancia_cubo(raiz) is None


def test_la_sesion_se_detiene_con_ese_mensaje(tmp_path, monkeypatch):
    raiz = _cubo_falso(tmp_path, b"cubo viejo", hashlib.sha256(b"cubo nuevo").hexdigest())
    monkeypatch.setattr(conftest, "RAIZ_REAL", raiz)
    try:
        conftest.pytest_sessionstart(None)
    except BaseException as e:   # pytest.exit lanza Exit
        assert type(e).__name__ == "Exit" and e.returncode != 0 and MENSAJE_CUBO_DISTINTO in str(e)
    else:
        raise AssertionError("la sesión debía detenerse")


def test_el_cubo_local_es_el_del_manifiesto():
    assert discrepancia_cubo(RAIZ_REAL) is None
