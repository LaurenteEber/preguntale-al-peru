"""S4: insumos del piloto estandarizados (ENDES, ENAHO, Mapa de Pobreza 2018) con los crudos registrados."""
import pytest

from pap.capa0 import encuestas as E
from pap.capa0 import mapa_pobreza as M
from pap.config import Rutas
from pap.errores import PapError

from conftest import RAIZ_REAL


def _construir(fn):
    try:
        return fn(Rutas(RAIZ_REAL))
    except (PapError, FileNotFoundError, ImportError) as e:
        pytest.skip(f"faltan insumos: {e}")


@pytest.fixture(scope="module")
def endes():
    return _construir(E.construir_endes)


@pytest.fixture(scope="module")
def enaho():
    return _construir(E.construir_enaho)


@pytest.fixture(scope="module")
def mapa():
    return _construir(M.construir)


def _bloqueantes(res):
    return [p["id"] for p in res.pruebas if p["bloqueante"] and not p["ok"]]


@pytest.mark.solo_mac
def test_endes(endes):
    assert _bloqueantes(endes) == []
    t = endes.tablas["endes_nino"]
    assert set(t.anio) == set(range(2015, 2026))
    assert not t.duplicated(["anio", "id_hogar", "idx_nino"]).any()
    # los códigos especiales no sobreviven a la recodificación
    assert t.hb_ajustada_hist.dropna().between(3, 25).all() and t.haz.dropna().abs().lt(99.9).all()
    ctrl = endes.revision["endes_controles_inei"].dropna(subset=["publicado_inei_pct"])
    ctrl = ctrl[~ctrl.informativo.astype(bool)]
    assert len(ctrl) >= 60 and ctrl.diferencia_pp.abs().max() <= 0.1 + 1e-9


@pytest.mark.solo_mac
def test_endes_universo_unico_y_estrato_anidado(endes):
    import yaml
    defs = yaml.safe_load((RAIZ_REAL / "curados/capa0/definiciones_endes.yaml").read_text(encoding="utf-8"))
    # H-03 (auditoría S4): mismo universo todos los años, sin excepción de 2015
    assert all(not d.get("excepciones") for d in defs["indicadores"].values())
    t = endes.tablas["endes_nino"]
    # H-01: el estrato de diseño lleva el departamento y no cruza departamentos
    assert (t.id_estrato.str[:2] == t.departamento).all()
    assert t.groupby(["anio", "id_estrato"]).departamento.nunique().max() == 1
    assert set(t[t.ubigeo_agrupado_inei].ubigeo_hogar) <= {"120699"}


@pytest.mark.solo_mac
def test_enaho(enaho):
    assert _bloqueantes(enaho) == []
    t = enaho.tablas["enaho_sumaria"]
    assert set(t.area) == {"urbano", "rural"}
    assert set(t.ambito_lima.dropna()) == {"LIMA_METROPOLITANA", "LIMA_REGION", "CALLAO"}
    assert (t.id_estrato_diseno.str.len() >= 4).all()
    assert (t.lima_metropolitana_dominio8 == (t.dominio == 8)).all()


@pytest.mark.solo_mac
def test_mapa(mapa):
    assert _bloqueantes(mapa) == []
    t = mapa.tablas["fact_mapa_pobreza"]
    assert (t.nivel == "distrito").sum() == 1874 and (t.nivel == "provincia").sum() == 196
    assert "pobreza_puntual" not in t.columns  # el INEI no publica punto: no se inventa
    d = t[t.nivel == "distrito"]
    assert d.grupo_robusto_nacional.notna().all() and d[d.grupo_nacional_inferido].ubigeo_inei.tolist() == ["150906"]
