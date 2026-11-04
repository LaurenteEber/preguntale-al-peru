"""Piloto: dim_indicador, cruces_permitidos y cifras_doradas (tablas curadas, 9/10/2026)."""
import copy

import pytest
import yaml

from pap.capa0 import indicadores as I
from pap.capa0 import insumos
from pap.capa0.encuestas import Resultado
from pap.config import Rutas
from pap.errores import PapError

from conftest import RAIZ_REAL


@pytest.fixture(scope="module")
def rutas():
    return Rutas(RAIZ_REAL)


@pytest.fixture(scope="module")
def res(rutas):
    try:
        return I.construir(rutas)
    except (PapError, FileNotFoundError) as e:
        pytest.skip(f"faltan tablas de la capa 0: {e}")


@pytest.fixture(scope="module")
def datos(rutas, res):
    ind = yaml.safe_load(insumos.curado(rutas, "dim_indicador.yaml").ruta.read_text(encoding="utf-8"))["indicadores"]
    cru = yaml.safe_load(insumos.curado(rutas, "cruces_permitidos.yaml").ruta.read_text(encoding="utf-8"))
    dor = res.tablas["cifras_doradas"].drop(columns="version_tabla").copy()
    dor["bloqueante"] = dor.bloqueante.astype(bool)
    tablas = {n: insumos.tabla(rutas, n) for n in ("endes_nino", "enaho_sumaria", "fact_mapa_pobreza",
                                                  "fact_sien_hb_ubigeo", "dim_tema_gasto", "fact_poblacion_grupo")}
    return ind, cru, dor, tablas


def _fallidas(r):
    return {p["id"] for p in r.pruebas if p["bloqueante"] and not p["ok"]}


def test_construccion_sin_bloqueantes(res):
    assert _fallidas(res) == set()
    assert len(res.tablas["dim_indicador"]) == 9
    assert res.tablas["dim_indicador"].indicador_id.is_unique


def test_nucleo_r_enc_18(res):
    d = res.tablas["cifras_doradas"]
    n = d[d.proposito == "R-ENC-18"]
    assert n.bloqueante.all() and (n.tipo_cita == "oficial_inei").all()
    for ind in ("endes_anemia_6_35m", "endes_anemia_6_35m_oms2024", "endes_dci_menores_5", "enaho_pobreza_monetaria"):
        m = n[n.indicador_id == ind]
        assert (m.nivel == "nacional").any()
        assert m[m.nivel == "departamento"].territorio.nunique() >= 3
    rep = res.revision["cifras_doradas_reproduccion"]
    assert (rep[rep.proposito == "R-ENC-18"].pasa == True).all()  # noqa: E712


def test_campo_faltante_suprime(rutas, datos):
    ind, _, _, tablas = datos
    malo = copy.deepcopy(ind)
    del malo[0]["velocidad_cambio"]
    malo[0]["variables_diseno"] = {k: v for k, v in malo[0]["variables_diseno"].items() if k != "factor"}
    r = Resultado()
    I._pruebas_indicadores(rutas, malo, r, tablas)
    assert "IND-03" in _fallidas(r)


def test_vocabulario_y_gasto_del_pan(rutas, datos):
    ind, _, _, tablas = datos
    malo = copy.deepcopy(ind)
    malo[0]["velocidad_cambio"] = "media"
    g = next(i for i in malo if i["id"] == "gasto_ex_pan")
    g["nombre_ciudadano"] = "Gasto del PAN en 2025"
    r = Resultado()
    I._pruebas_indicadores(rutas, malo, r, tablas)
    assert {"IND-04", "IND-11"} <= _fallidas(r)


def test_cruce_misma_medida_y_ventana(rutas, datos):
    ind, cru, _, _ = datos
    malo = copy.deepcopy(cru)
    malo["cruces"][0]["indicador_b"] = "sien_anemia_tamizados_6_35m"
    malo["cruces"][0]["indicador_a"] = "endes_anemia_6_35m_oms2024"  # mismo concepto: R-CRUCES-08, no cruce
    malo["cruces"][1]["ventana_anios"] = 3  # rápida → máx. 1
    r = Resultado()
    I._pruebas_cruces(rutas, malo, {i["id"]: i for i in ind}, r)
    assert "CRU-03" in _fallidas(r)


def test_dorada_de_prensa_o_mal_copiada_falla(rutas, datos):
    ind, _, dor, tablas = datos
    malo = dor.copy()
    i = malo.index[malo.id_cifra == "DOR-ANE-2024-PE"][0]
    malo.loc[i, "valor_publicado"] = 44.0  # cifra mal copiada
    j = malo.index[malo.id_cifra == "DOR-ANE-2025-PE"][0]
    malo.loc[j, "tipo_cita"] = "prensa"  # desde el 11/10/2026 solo valen documentos oficiales; la prensa tampoco bloquea
    r = Resultado()
    I._pruebas_doradas(rutas, malo, {x["id"]: x for x in ind}, r, tablas)
    assert {"DOR-04", "DOR-05", "DOR-07"} <= _fallidas(r)


def test_cobertura_insuficiente(rutas, datos):
    """Sin departamentos en el núcleo ENAHO falla DOR-06 aunque queden LM, LR y Callao: los ámbitos no son departamentos."""
    ind, _, dor, tablas = datos
    q = (dor.indicador_id == "enaho_pobreza_monetaria") & (dor.proposito == "R-ENC-18")
    assert dor[q].nivel.isin(I.AMBITOS_LIMA).sum() >= 3
    malo = dor[~(q & (dor.nivel == "departamento"))].copy()
    r = Resultado()
    I._pruebas_doradas(rutas, malo, {x["id"]: x for x in ind}, r, tablas)
    assert "DOR-06" in _fallidas(r)


# ----------------------------------------------------------------- Lima en tres ámbitos (P4, 9/10/2026)

def test_lima_niveles_y_pruebas_nuevas(res):
    ids = {p["id"]: p for p in res.pruebas}
    for k in ("IND-12", "IND-13", "CRU-06", "DOR-04", "DOR-06", "DOR-07"):
        assert ids[k]["ok"], k
    assert ids["DOR-10"]["bloqueante"] is False
    d = res.tablas["cifras_doradas"]
    amb = d[d.territorio.isin(I.AMBITOS_TODOS)]
    assert (amb.nivel == amb.territorio).all()
    n = d[d.proposito == "R-ENC-18"]
    for a in I.AMBITOS_LIMA:  # ENAHO 2024 y 2025 por ámbito, bloqueantes y oficiales
        m = n[(n.indicador_id == "enaho_pobreza_monetaria") & (n.nivel == a)]
        assert sorted(m.anio) == [2024, 2025] and (m.tipo_cita == "oficial_inei").all()
    assert float(d[d.id_cifra == "DOR-POB-2025-CALLAO"].valor_publicado.iloc[0]) == 32.1
    rep = res.revision["cifras_doradas_reproduccion"]
    assert bool(rep[rep.id_cifra == "DOR-ANE-2017-LM1501"].pasa.iloc[0])  # ENDES 2017 por estrato (L2)


def test_tolerancia_cv(datos):
    """D-ENA-1 (pendiente de visto): en la ENAHO el CV es dato y no bloquea; en la DCI 2024 sí."""
    _, _, dor, _ = datos
    en = dor[dor.fuente_id == "INEI-ENAHO"]
    assert en.tolerancia_cv.isna().all() and en.cv_publicado.notna().sum() >= 60
    dci = dor[(dor.indicador_id == "endes_dci_menores_5") & (dor.anio == 2024) & dor.bloqueante]
    assert dci.tolerancia_cv.notna().all() and len(dci) == 3


def test_dorada_lr_mal_copiada_falla(rutas, datos):
    ind, _, dor, tablas = datos
    malo = dor.copy()
    malo.loc[malo.id_cifra == "DOR-POB-2025-LIMA_REGION", "valor_publicado"] = 22.6
    r = Resultado()
    I._pruebas_doradas(rutas, malo, {x["id"]: x for x in ind}, r, tablas)
    assert "DOR-07" in _fallidas(r)


def test_dorada_ambito_con_nivel_viejo_falla(rutas, datos):
    ind, _, dor, tablas = datos
    malo = dor.copy()
    malo.loc[malo.id_cifra == "DOR-ANE-2024-LM1501", "nivel"] = "dominio_subnacional"
    r = Resultado()
    I._pruebas_doradas(rutas, malo, {x["id"]: x for x in ind}, r, tablas)
    assert "DOR-04" in _fallidas(r)


def test_ambito_sin_dorada_avisa(rutas, datos):
    ind, _, dor, tablas = datos
    malo = dor[~((dor.indicador_id == "enaho_pobreza_monetaria") & (dor.nivel == "LIMA_REGION"))].copy()
    r = Resultado()
    I._pruebas_doradas(rutas, malo, {x["id"]: x for x in ind}, r, tablas)
    p = next(x for x in r.pruebas if x["id"] == "DOR-10")
    assert not p["ok"] and "DOR-10" not in _fallidas(r)


def test_ambito_no_mapeado_en_cr01_falla(rutas, datos):
    ind, cru, _, _ = datos
    por_id = {i["id"]: i for i in ind}
    malo = copy.deepcopy(cru)
    s = next(c for c in malo["cruces"] if c["id_cruce"] == "CR-01")["subdivision_lima"]
    s["ambitos"] = [a for a in s["ambitos"] if a["ambito_id"] != "LIMA_REGION"]
    r = Resultado()
    I._pruebas_cruces(rutas, malo, por_id, r)
    assert "CRU-06" in _fallidas(r)
    malo = copy.deepcopy(cru)
    s = next(c for c in malo["cruces"] if c["id_cruce"] == "CR-01")["subdivision_lima"]
    s["ambitos"][0]["gasto"]["valor"] = "LIMA_REGION"  # mapeo cruzado LM ↔ LR
    r = Resultado()
    I._pruebas_cruces(rutas, malo, por_id, r)
    assert "CRU-06" in _fallidas(r)
    malo = copy.deepcopy(cru)
    del next(c for c in malo["cruces"] if c["id_cruce"] == "CR-01")["subdivision_lima"]
    r = Resultado()
    I._pruebas_cruces(rutas, malo, por_id, r)
    assert "CRU-06" in _fallidas(r)


def test_cr01_2025_condicionado(rutas, datos, monkeypatch):
    """2025 de LM y LR en CR-01 y en dim_indicador solo con dim_dominio ENDES 2025 confirmado y el condicionado activo."""
    ind, cru, _, _ = datos
    por_id = {i["id"]: i for i in ind}
    malo = copy.deepcopy(cru)
    next(c for c in malo["cruces"] if c["id_cruce"] == "CR-01")["subdivision_lima"]["anios_condicionados"][0]["activo"] = False
    r = Resultado()
    I._pruebas_cruces(rutas, malo, por_id, r)
    assert "CRU-06" in _fallidas(r)
    monkeypatch.setattr(I, "_dominio_confirmado", lambda *a: False)
    r = Resultado()
    I._pruebas_cruces(rutas, cru, por_id, r)
    I._pruebas_ambitos(rutas, ind, r)
    assert {"CRU-06", "IND-13"} <= _fallidas(r)


def test_ranking_y_rango_de_ambitos(rutas, datos):
    ind, _, _, _ = datos
    malo = copy.deepcopy(ind)
    e = next(i for i in malo if i["id"] == "enaho_pobreza_monetaria")
    e["ranking"]["unidades"] = [u for u in e["ranking"]["unidades"] if u != "CALLAO"]  # 25 unidades
    r = Resultado()
    I._pruebas_ambitos(rutas, malo, r)
    assert "IND-12" in _fallidas(r)
    malo = copy.deepcopy(ind)
    nv = next(n for n in next(i for i in malo if i["id"] == "endes_anemia_6_35m")["niveles_validos"]
              if n["nivel"] == "LIMA_REGION")
    nv["rango"] = 3  # NIVEL_RANK nuevo: 3,5
    r = Resultado()
    I._pruebas_ambitos(rutas, malo, r)
    assert "IND-12" in _fallidas(r)
    malo = copy.deepcopy(ind)
    next(i for i in malo if i["id"] == "endes_dci_menores_5")["niveles_validos"].append(
        {"nivel": "dominio_subnacional", "dominios": ["LIMA_METROPOLITANA"]})  # forma vieja
    r = Resultado()
    I._pruebas_ambitos(rutas, malo, r)
    assert "IND-12" in _fallidas(r)


def test_dominio_usa_ambitos_lima(rutas, datos):
    """La reproducción no reimplementa la asignación: _dominio_endes/_dominio_enaho = ambitos_lima.mascara_ambito."""
    from pap.capa0 import ambitos_lima
    _, _, _, tablas = datos
    e = I._leer(tablas["endes_nino"], "*", "WHERE anio IN (2017, 2024)")
    for a in I.AMBITOS_TODOS:
        assert I._dominio_endes(e, a, a).equals(ambitos_lima.mascara_ambito(e, "ENDES", a))
    assert I._dominio_endes(e[e.anio == 2017], "LIMA_METROPOLITANA", "LIMA_METROPOLITANA").sum() > 0
    h = I._leer(tablas["enaho_sumaria"], "*", "WHERE anio = 2025")
    for a in I.AMBITOS_TODOS:
        assert I._dominio_enaho(h, a, a).equals(ambitos_lima.mascara_ambito(h, "ENAHO", a))


def test_parquet_determinista(res, tmp_path):
    from pap.capa0.salida import escribir_parquet
    from pap.util import sha256
    t = res.tablas["dim_indicador"]
    a, b = tmp_path / "a.parquet", tmp_path / "b.parquet"
    escribir_parquet(t, a, "indicador_id")
    escribir_parquet(t.sample(frac=1, random_state=1), b, "indicador_id")
    assert sha256(a) == sha256(b)


# ----------------------------------------------------------------- correcciones de la auditoría P2+P4 (H1–H3, H7–H9)

def _doradas_con_cv(rutas, ind, dor, tablas):
    r = Resultado()
    I._pruebas_doradas(rutas, dor, {x["id"]: x for x in ind}, r, tablas)
    return r


def test_h1_ic_o_cv_mal_copiado_falla(rutas, datos):
    """M4 de la auditoría: IC superior 25,9 y CV 5,8 en LR 2025 (publicado 25,2 y 8,5) → DOR-11."""
    ind, _, dor, tablas = datos
    for col, val in (("ic_sup_publicado", 25.9), ("cv_publicado", 5.8), ("ic_inf_publicado", 22.0)):
        malo = dor.copy()
        malo.loc[malo.id_cifra == "DOR-POB-2025-LIMA_REGION", col] = val
        assert "DOR-11" in _fallidas(_doradas_con_cv(rutas, ind, malo, tablas)), col


def test_h1_cv_dci_con_tolerancia_bloquea(rutas, datos):
    ind, _, dor, tablas = datos
    malo = dor.copy()
    malo.loc[malo.id_cifra == "DOR-DCI-2024-PE", ["cv_publicado", "ic_inf_publicado", "ic_sup_publicado"]] = [3.4, 11.3, 12.9]
    assert "DOR-11" in _fallidas(_doradas_con_cv(rutas, ind, malo, tablas))  # IC coherente con el CV, pero CV ≠ el nuestro


def test_h1_cv_enaho_solo_avisa(rutas, datos):
    """D-ENA-1: el CV de la ENAHO no bloquea; si nuestro CV difiere > 0,5 puntos, DOR-12 avisa."""
    ind, _, dor, tablas = datos
    malo = dor.copy()
    i = malo.id_cifra == "DOR-POB-2025-LIMA_REGION"
    malo.loc[i, ["cv_publicado", "ic_inf_publicado", "ic_sup_publicado"]] = [9.5, 17.6, 25.6]  # coherente, CV lejos del nuestro
    r = _doradas_con_cv(rutas, ind, malo, tablas)
    p = next(x for x in r.pruebas if x["id"] == "DOR-12")
    assert not p["ok"] and not p["bloqueante"] and "DOR-11" not in _fallidas(r)


def test_h1_doradas_iguales_a_la_extraccion_oficial(rutas, datos):
    """Las 72 cifras ENAHO (valor, IC, CV) son las de la extracción del PDF registrado (doradas/extraccion_oficial.csv)."""
    import pandas as pd
    ruta = rutas.raiz / "tests/fixtures/extraccion_oficial.csv"
    if not ruta.exists():
        pytest.skip("falta doradas/extraccion_oficial.csv")
    _, _, dor, _ = datos
    e = pd.read_csv(ruta, dtype={"territorio": str})
    m = dor[dor.fuente_id == "INEI-ENAHO"].merge(e, on=["indicador_id", "anio", "territorio"], how="left")
    assert len(m) == 72 and m.estimacion.notna().all()
    for a, b in (("valor_publicado", "estimacion"), ("ic_inf_publicado", "ic_inf"), ("ic_sup_publicado", "ic_sup"),
                 ("cv_publicado", "cv")):
        assert (m[a].astype(float) - m[b].astype(float)).abs().max() < 1e-9, a


def test_h2_anios_sin_confirmar_fallan_sin_marca(rutas, datos, monkeypatch):
    """M9: se borran las marcas anios_condicionados y la ENDES 2025 queda sin confirmar → IND-13 y CRU-06 fallan igual."""
    ind, cru, _, _ = datos
    malo_i, malo_c = copy.deepcopy(ind), copy.deepcopy(cru)
    for i in malo_i:
        for nv in i.get("niveles_validos") or []:
            nv.pop("anios_condicionados", None)
    for c in malo_c["cruces"]:
        (c.get("subdivision_lima") or {}).pop("anios_condicionados", None)
    real = I._dominio_confirmado
    monkeypatch.setattr(I, "_dominio_confirmado", lambda r, e, d, a: real(r, e, d, a) and not (e == "ENDES" and a == 2025
                                                                                               and d != "callao"))
    r = Resultado()
    I._pruebas_ambitos(rutas, malo_i, r)
    I._pruebas_cruces(rutas, malo_c, {i["id"]: i for i in malo_i}, r)
    assert {"IND-13", "CRU-06"} <= _fallidas(r)


def test_h3_denominador_ipf_sin_geografia_falla(rutas, datos):
    """M6: sin el filtro de geografía la suma sale ×2 → IND-14."""
    ind, _, _, tablas = datos
    r = Resultado()
    I._prueba_denominador_ipf(ind, tablas["fact_poblacion_grupo"], r)
    assert "IND-14" not in _fallidas(r)
    malo = copy.deepcopy(ind)
    c = next(i for i in malo if i["id"] == "sien_cobertura_tamizaje_6_35m")
    del c["denominador_ambitos_lima"]["propio"]["filtro"]["geografia_base"]
    r = Resultado()
    I._prueba_denominador_ipf(malo, tablas["fact_poblacion_grupo"], r)
    assert "IND-14" in _fallidas(r)
    malo = copy.deepcopy(ind)
    c = next(i for i in malo if i["id"] == "sien_cobertura_tamizaje_6_35m")
    c["denominador_ambitos_lima"]["propio"]["prefijos"]["LIMA_REGION"] = ["15"]  # LR sin quitar la 1501
    r = Resultado()
    I._prueba_denominador_ipf(malo, tablas["fact_poblacion_grupo"], r)
    assert "IND-14" in _fallidas(r)


def test_h8_aviso_fuera_de_r_enc_08_falla(rutas, datos):
    ind, _, _, _ = datos
    malo = copy.deepcopy(ind)
    nv = next(n for n in next(i for i in malo if i["id"] == "endes_anemia_6_35m")["niveles_validos"]
              if n["nivel"] == "LIMA_METROPOLITANA")
    nv["avisos"] = ["ambito_no_dominio", "ambito_por_estrato (2015–2017)"]
    r = Resultado()
    I._pruebas_ambitos(rutas, malo, r)
    assert "IND-12" in _fallidas(r)


def test_h7_h9_notas_y_dominio8(datos):
    _, _, dor, _ = datos
    d8 = dor[(dor.indicador_id == "enaho_pobreza_monetaria") & (dor.nivel == "AREA_METROPOLITANA_LIMA_CALLAO")]
    assert sorted(d8[d8.bloqueante & (d8.proposito == "R-ENC-18")].anio) == [2024, 2025]
    assert not dor.nota.fillna("").str.contains("salvo el dominio 8").any()
    ca = dor[(dor.fuente_id == "INEI-ENDES") & (dor.territorio == "CALLAO")]
    assert ca.nota.str.contains("dominio de la ficha").all() and not ca.nota.str.contains("ambito_no_dominio").any()
    assert "ambito_por_estrato" in dor[dor.id_cifra == "DOR-ANE-2017-LM1501"].nota.iloc[0]
