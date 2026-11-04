"""S2 — población: IPF a tres márgenes y construcción completa con los crudos registrados."""
import numpy as np
import pytest

from pap.capa0 import poblacion as P
from pap.config import Rutas
from pap.errores import PapError

from conftest import RAIZ_REAL


def test_ipf_tres_margenes_converge():
    rng = np.random.default_rng(7)
    semilla = rng.integers(1, 50, size=(4, 10, 2)).astype(float)
    grupo_q = np.arange(10) // 5          # 2 quinquenios
    verdad = rng.integers(10, 200, size=(4, 10, 2)).astype(float)
    m_dist = verdad.sum(axis=(1, 2))
    m_edad = verdad.sum(axis=(0, 2))
    onehot = np.eye(2)[grupo_q]
    m_sq = np.einsum("ias,aq->sq", verdad, onehot)
    x, it, err = P.ipf(semilla, m_dist, m_edad, m_sq, grupo_q)
    assert err < P.TOL_IPF and it <= P.MAX_IT
    assert np.allclose(x.sum(axis=(1, 2)), m_dist, rtol=1e-3)
    assert np.allclose(x.sum(axis=(0, 2)), m_edad, rtol=1e-3)
    assert np.allclose(np.einsum("ias,aq->sq", x, onehot), m_sq, rtol=1e-3)


@pytest.mark.solo_mac
def test_construccion_real():
    try:
        res = P.construir(Rutas(RAIZ_REAL))
    except PapError as e:
        pytest.skip(f"faltan insumos registrados: {e}")
    fallidas = [(p["id"], p["descripcion"], p["detalle"]) for p in res.pruebas if p["bloqueante"] and not p["ok"]]
    assert fallidas == []
    f = res.tablas["fact_poblacion"]
    assert set(f.metodo) == {"oficial", "censado", "prorrateo_propio"}
    assert f[(f.ubigeo_inei == "160405") & (f.anio < 2025)].empty
    # PO-01: el 000000 es nacional y hay 25 departamentos por serie
    assert (f.loc[f.ubigeo_inei == "000000", "nivel"] == "nacional").all()
    g = res.tablas["fact_poblacion_grupo"]
    # PO-02: 6-35 meses = 0,5·P0 + P1 + P2, en tabla aparte
    s = g[g.grupo_id == "6-35m"]
    assert ((s.valor - (0.5 * s.p0 + s.p1 + s.p2)).abs() <= 0.01).all()
    assert set(g.grupo_id) == {"0-35m", "6-35m", "0-59m", "6-59m"}
    pu = res.tablas["puente_geo2017"]
    assert len(pu) == 1874 and abs(pu.groupby("grupo_comparable_geo2017").peso_pob_2018.sum() - 1).max() < 1e-9
    assert all(p["ok"] for p in res.pruebas if p["id"] in ("P2-13", "P2-14", "P2-15", "P2-16", "P2-17"))
