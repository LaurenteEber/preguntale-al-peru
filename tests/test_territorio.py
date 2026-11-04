"""S1 — territorio: reglas de grupos comparables y construcción completa con los crudos registrados."""
import pytest

from pap.capa0 import territorio as T
from pap.config import Rutas
from pap.errores import PapError

from conftest import RAIZ_REAL


def test_grupos_un_origen_y_varios():
    base = {"000101", "000102", "000103", "000201"}
    altas = [
        {"ubigeo": "000104", "origenes": [{"ubigeo": "000101"}]},
        {"ubigeo": "000105", "origenes": [{"ubigeo": "000101"}]},
        {"ubigeo": "000106", "origenes": [{"ubigeo": "000102"}, {"ubigeo": "000103"}]},
    ]
    g = T.grupos_comparables(base, altas, [])
    assert g["000104"] == g["000105"] == g["000101"] == "000101"
    assert g["000106"] == g["000102"] == g["000103"] == "G-000102"
    assert g["000201"] == "000201"


def test_grupo_sin_distrito_2017_falla():
    with pytest.raises(PapError):
        T.grupos_comparables({"000101"}, [{"ubigeo": "000104", "origenes": [{"ubigeo": "009999"}]}], [])


def test_expandir_composicion():
    d = ["150101", "150201", "150301", "070101", "010101"]
    assert T._expandir(["15", "-1501"], d) == ["150201", "150301"]
    assert T._expandir(["1501", "0701"], d) == ["070101", "150101"]
    assert T._expandir([""], d) == sorted(d)


def test_construccion_real():
    rutas = Rutas(RAIZ_REAL)
    try:
        res = T.construir(rutas)
    except (PapError, FileNotFoundError) as e:  # FileNotFoundError: el almacén de crudos no está en esta máquina
        pytest.skip(f"faltan insumos registrados: {e}")
    fallidas = [(p["id"], p["descripcion"], p["detalle"]) for p in res.pruebas if p["bloqueante"] and not p["ok"]]
    assert fallidas == []
    dim = res.tablas["dim_ubigeo_historico"]
    vig = dim[(dim.nivel == "distrito") & dim.vigente_hasta.isna()]
    assert len(vig) == 1893  # 1 874 de 2017 + 19 altas (Sangani, Ley 32729, 2026)
    assert set(dim.ubigeo_inei).isdisjoint({"150144", "160109", "160114"})
    assert dim.loc[dim.ubigeo_inei == "130112", "grupo_comparable_geo2017"].iloc[0] == "G-130102"
    assert dim.loc[dim.ubigeo_inei == "160405", "grupo_comparable_geo2017"].iloc[0] == "160403"
    assert not dim.nombre.str.contains("\n").any()
    grupo = dict(zip(dim.ubigeo_inei, dim.grupo_comparable_geo2017))
    assert {grupo[u] for u in ("130102", "130103", "130106", "130112")} == {"G-130102"}
    assert {grupo[u] for u in ("040302", "040305")} == {"G-040302"}
    assert all(p["ok"] for p in res.pruebas if p["id"] == "T-18")


@pytest.fixture(scope="module")
def dim_real():
    try:
        return T.construir(Rutas(RAIZ_REAL)).tablas
    except (PapError, FileNotFoundError) as e:
        pytest.skip(f"faltan insumos registrados: {e}")


def test_nacional_y_departamentos_desde_1995(dim_real):
    """SP-01: las series departamentales desde 2015 resuelven contra la tabla de ubigeo."""
    dim = dim_real["dim_ubigeo_historico"]
    nac = dim[dim.ubigeo_inei == "000000"]
    assert len(nac) == 1 and nac.nivel.iloc[0] == "nacional"
    dep = dim[dim.nivel == "departamento"]
    assert len(dep) == 25 and (dep.vigente_desde == T.INICIO_DEPARTAMENTOS).all()
    assert (dep.ubigeo_padre == "000000").all()
    for anio in (2015, 2016, 2017):
        assert len(T.vigentes_en_anio(dim, anio, "departamento")) == 25


def test_pertenencia_anual(dim_real):
    """TE-02: el año del dato decide la versión según el primer año con dato INEI."""
    dim = dim_real["dim_ubigeo_historico"]
    v22 = set(T.vigentes_en_anio(dim, 2022).ubigeo_inei)
    v23 = set(T.vigentes_en_anio(dim, 2023).ubigeo_inei)
    assert "130112" not in v22 and "130112" in v23            # Alto Trujillo: ley dic-2022, dato INEI desde 2023
    assert "090724" in set(T.vigentes_en_anio(dim, 2020).ubigeo_inei)   # Lambras: ley dic-2020, dato desde 2020
    assert "120307" not in set(T.vigentes_en_anio(dim, 2026).ubigeo_inei)  # Sangani: sin dato INEI aún
    for anio in range(2018, 2027):  # una sola versión por distrito y año
        v = T.vigentes_en_anio(dim, anio)
        assert not v.ubigeo_inei.duplicated().any()


def test_sangani_codigo_provisional(dim_real):
    dim = dim_real["dim_ubigeo_historico"]
    s = dim[dim.ubigeo_inei == "120307"].iloc[0]
    assert s.estado_verificacion == "codigo_provisional_dueno" and s.vigente_desde == "2026-07-16"
    per = dim[dim.ubigeo_inei == "120302"].sort_values("vigente_desde")
    assert len(per) == 2 and bool(per.territorio_modificado.iloc[1])
    rel = dim_real["rel_ubigeo_origen"]
    assert ((rel.ubigeo_hijo == "120307") & (rel.ubigeo_origen == "120302")).any()


def test_dominios_antes_de_2018_no_vacios(dim_real):
    dom = dim_real["dim_dominio"]
    d = dom[dom.dominio_id.str.startswith("departamento_") & (dom.anio < 2018)]
    assert len(d) > 0 and d.ubigeos.map(len).gt(0).all() and d.composicion_aproximada_geo2017.all()
    # TE-09 resuelto (Lima en tres ámbitos, L1, 9/10/2026): el informe técnico de pobreza 2016–2025 (Cuadro N.º III.1)
    # publica LM = 1501 de 2016 a 2025; es ámbito publicado, no dominio de la ficha
    lm = dom[(dom.encuesta_id == "ENAHO") & (dom.dominio_id == "lima_metropolitana") & dom.anio.between(2022, 2025)]
    assert lm.confirmado.all() and (lm.tipo == "ambito_publicado").all()


def test_nivel_y_ubigeo_normalizado():
    import pandas as pd
    from pap.capa0 import lectores as L
    assert [L.nivel_de(u) for u in ("000000", "150000", "159999", "150100", "150101")] == \
        ["nacional", "departamento", "ambito", "provincia", "distrito"]
    s = L.ubigeo_normalizado(pd.Series(["10101", "010101", "150101.0", "", "0", "000000", None, "ABC"]))
    assert s.tolist()[:3] == ["010101", "010101", "150101"] and s.iloc[3:].isna().all()
