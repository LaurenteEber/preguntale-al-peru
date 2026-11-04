"""S3 (parte sin gasto): IPC, establecimientos de salud y SIEN con los crudos registrados."""
import pytest

from pap.capa0 import puentes as P
from pap.config import Rutas
from pap.errores import PapError

from conftest import RAIZ_REAL


@pytest.fixture(scope="module")
def res():
    try:
        return P.construir(Rutas(RAIZ_REAL))
    except (PapError, FileNotFoundError) as e:
        pytest.skip(f"faltan insumos: {e}")


@pytest.mark.solo_mac
def test_construccion_real(res):
    assert [p["id"] for p in res.pruebas if p["bloqueante"] and not p["ok"]] == []
    ipc = res.tablas["dim_ipc"]
    assert ipc[(ipc.anio == 2021) & (ipc.mes == 12)].indice.iloc[0] == 100
    est = res.tablas["dim_establecimiento_salud"]
    # GA-09 (ronda 3): solo un código escindido no curado queda sin distrito (en la provincia contenedora)
    assert est.cod_ipress.is_unique and (est.ubigeo_valido | (est.metodo_ubigeo == "codigo_escindido_contenedor")).all()
    assert set(est.metodo_ubigeo) <= P.METODOS_UBIGEO_EESS
    assert "fact_sien_hb_ubigeo" in res.tablas


@pytest.mark.solo_mac
def test_renipress_160109_no_va_por_alias(res):
    """GA-09: 160109 (Putumayo, escindido por la Ley 30186) ya no se redirige a 160801. Cachuy está en Iquitos
    (Punchana, curado con evidencia); Yabuyanos no se puede ubicar a distrito y queda en la provincia 160800."""
    est = res.tablas["dim_establecimiento_salud"].set_index("cod_ipress")
    x = est[est.ubigeo_fuente == "160109"]
    assert len(x) == 2 and (x.ubigeo_inei != "160801").all()
    assert est.loc["00031444", ["ubigeo_inei", "metodo_ubigeo"]].tolist() == ["160108", "curado"]
    assert est.loc["00037475", ["ubigeo_inei", "metodo_ubigeo"]].tolist() == ["160800", "codigo_escindido_contenedor"]
    assert est[est.ubigeo_fuente == "160114"].ubigeo_inei.eq("160803").all()
    e12 = next(p for p in res.pruebas if p["id"] == "E-12")
    assert e12["ok"], e12["detalle"]


@pytest.mark.solo_mac
def test_sien_pruebas_bloqueantes_y_avisos(res):
    pr = {p["id"]: p for p in res.pruebas}
    for i in ("E-05", "E-10", "E-11"):
        assert pr[i]["ok"] and pr[i]["bloqueante"], pr[i]
    for i in ("E-06", "E-07", "E-08", "E-09"):
        assert not pr[i]["bloqueante"], i
    assert pr["E-08"]["ok"], pr["E-08"]["detalle"]  # Hbc y Dx reproducidos en el 100 % (OMS 2024, AlturaREN)
