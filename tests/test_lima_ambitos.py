"""Lima en tres ámbitos (P2, 9/10/2026): dim_dominio, ambitos_lima.py e inferencia_verificada.csv.

Las pruebas sobre microdatos usan los Parquet estandarizados de S4 (endes_nino, enaho_sumaria) y se saltan si no están.
La construcción completa de S1 necesita los crudos; aquí se prueba construir_dominios con dim_ubigeo_historico.parquet.
"""
import csv
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from pap.capa0 import ambitos_lima as AL
from pap.capa0 import territorio as T
from pap.config import Rutas
from pap.errores import PapError

from conftest import RAIZ_REAL

ENC = RAIZ_REAL / "biblioteca" / "estandarizada" / "encuestas"
DIM = RAIZ_REAL / "biblioteca" / "dimensiones"


def _parquet(ruta: Path) -> pd.DataFrame:
    if not ruta.exists():
        pytest.skip(f"falta {ruta.name}")
    import duckdb
    return duckdb.sql(f"SELECT * FROM '{ruta}'").df()


# ======================================================================= ambitos_lima (unidad)

def test_ambito_por_ubigeo():
    s = pd.Series(["150101", "150843", "070101", "010101", None, "1501", "07"])
    assert AL.ambito_por_ubigeo(s).tolist() == [AL.LIMA_METROPOLITANA, AL.LIMA_REGION, AL.CALLAO, None, None,
                                                 AL.LIMA_METROPOLITANA, AL.CALLAO]


def test_ambito_endes_metodo_por_anio():
    df = pd.DataFrame({
        "anio": [2016, 2016, 2016, 2016, 2016, 2019, 2019, 2019, 2019, 2016],
        "departamento": ["15", "15", "15", "07", "01", "15", "15", "07", "01", "15"],
        "id_estrato": ["15-1", "15-2", "15-3", "07-1", "01-1", "15-143", "15-150", "07-10", "01-3", "15-9"],
        "provincia_hogar": [None, None, None, None, None, "1501", "1508", "0701", "0101", None],
    })
    amb = AL.ambito_lima_endes(df).tolist()
    met = AL.metodo_ambito_lima_endes(df).tolist()
    assert amb == [AL.LIMA_METROPOLITANA, AL.LIMA_REGION, AL.LIMA_REGION, AL.CALLAO, None,
                   AL.LIMA_METROPOLITANA, AL.LIMA_REGION, AL.CALLAO, None, None]  # 15-9 no está en el Cuadro N.º 1
    assert met == ["estrato_hv022"] * 4 + [None] + ["ubigeo"] * 3 + [None, None]
    lmc = AL.mascara_ambito(df, "ENDES", AL.AREA_METROPOLITANA_LIMA_CALLAO).tolist()
    assert lmc == [True, False, False, True, False, True, False, True, False, False]


def test_mascara_enaho_dominio8_y_errores():
    df = pd.DataFrame({"ubigeo": ["150101", "070101", "150801"], "ambito_lima": ["LIMA_METROPOLITANA", "CALLAO",
                                                                               "LIMA_REGION"],
                       "lima_metropolitana_dominio8": [True, True, False]})
    assert AL.mascara_ambito(df, "ENAHO", AL.AREA_METROPOLITANA_LIMA_CALLAO).tolist() == [True, True, False]
    assert AL.mascara_ambito(df, "enaho", AL.LIMA_REGION).tolist() == [False, False, True]
    with pytest.raises(ValueError):
        AL.mascara_ambito(df, "ENAHO", "LIMA")
    with pytest.raises(ValueError):
        AL.mascara_ambito(df, "ENAPRES", AL.CALLAO)


# ======================================================================= dim_dominio

@pytest.fixture(scope="module")
def dom():
    ubi = _parquet(DIM / "dim_ubigeo_historico.parquet")
    return T.construir_dominios(Rutas(RAIZ_REAL), ubi)


def test_dim_dominio_pruebas_de_construccion(dom):
    fallidas = [(i, d, det) for i, d, ok, det in T.pruebas_dominios(dom) if not ok]
    assert fallidas == []


def test_dim_dominio_campos_nuevos(dom):
    for c in ("tipo", "metodo", "identificable_microdatos", "ambito_id", "rotulo", "codigo_verificado"):
        assert c in dom.columns
    assert set(dom.tipo) == {"dominio_diseno", "ambito_publicado"}
    assert set(dom.metodo.dropna()) <= T.METODOS_DOMINIO
    assert not dom.duplicated(["encuesta_id", "anio", "dominio_id"]).any()
    assert set(dom.anio) == set(range(2015, 2026)) and dom.confirmado.all()


def test_dominio8_una_vez_y_rotulo(dom):
    enaho = dom[dom.encuesta_id == "ENAHO"]
    assert "lima_metropolitana_callao" not in set(enaho.dominio_id)  # el duplicado (A4) ya no existe
    d8 = enaho[enaho.dominio_id == "area_metropolitana_lima_callao"]
    assert len(d8) == 11 and (d8.rotulo == "Lima Metropolitana y Callao").all()
    assert (d8.tipo == "dominio_diseno").all() and (d8.metodo == "variable_dominio").all()
    assert d8.set_index("anio").codigo_verificado.to_dict() == {a: a >= 2024 for a in range(2015, 2026)}
    lm = set(enaho[(enaho.dominio_id == "lima_metropolitana") & (enaho.anio == 2024)].ubigeos.iloc[0])
    ca = set(enaho[(enaho.dominio_id == "callao") & (enaho.anio == 2024)].ubigeos.iloc[0])
    assert len(lm) == 43 and len(ca) == 7 and set(d8[d8.anio == 2024].ubigeos.iloc[0]) == lm | ca


def test_lm_nunca_dominio8(dom):
    lm = dom[dom.dominio_id == "lima_metropolitana"]
    cod = lm.codigo_en_microdatos.map(yaml.safe_load)
    assert not cod.map(lambda c: c.get("variable") == "dominio").any()
    enaho = lm[lm.encuesta_id == "ENAHO"]
    assert (cod[enaho.index].map(lambda c: c["variable"]) == "ubigeo").all()
    assert (enaho.tipo == "ambito_publicado").all()


def test_tipos_y_fuentes_lima(dom):
    r = dom.set_index(["encuesta_id", "dominio_id", "anio"])
    assert r.loc[("ENDES", "callao", 2016), "tipo"] == "dominio_diseno"
    assert r.loc[("ENAHO", "callao", 2024), "tipo"] == "ambito_publicado"
    assert r.loc[("ENAHO", "departamento_15", 2024), "tipo"] == "ambito_publicado"  # la «Lima» de la ficha incluye al Callao (A7)
    assert r.loc[("ENDES", "departamento_15", 2024), "tipo"] == "dominio_diseno"
    assert ("ENAHO", "departamento_07", 2024) not in r.index and ("ENDES", "departamento_07", 2024) not in r.index
    f = r.loc[("ENDES", "lima_metropolitana", 2016), "fuente_definicion"]
    assert "Cuadro N.º 1" in f and "548-Ficha" in f
    assert "§3.7" not in f.split("no es la sección")[0]
    c = yaml.safe_load(r.loc[("ENDES", "lima_provincias", 2017), "codigo_en_microdatos"])
    assert c == {**c, "variable": "id_estrato", "valor": ["15-2", "15-3"], "verificado": True}
    f25 = r.loc[("ENAHO", "lima_metropolitana", 2025), "fuente_definicion"]
    assert "2016-2025" in f25 and "p. 73" in f25 and "p. 232" in f25
    assert r.loc[("ENDES", "lima_metropolitana", 2025), "confirmado"]


def test_avisos_claves_de_r_enc_08(dom):
    import json
    reglas = json.loads((RAIZ_REAL / "reglas" / "reglas.json").read_text("utf-8"))
    reglas = reglas["reglas"] if isinstance(reglas, dict) else reglas
    claves = set(next(r for r in reglas if r["id"] == "R-ENC-08")["parametros"]["avisos"])
    usados = set().union(*dom.avisos.map(set))
    assert usados == {"ambito_no_dominio", "ambito_por_estrato"} and usados <= claves
    r = dom.set_index(["encuesta_id", "dominio_id", "anio"]).avisos
    assert r[("ENDES", "lima_metropolitana", 2016)] == ["ambito_no_dominio", "ambito_por_estrato"]
    assert r[("ENDES", "lima_metropolitana", 2018)] == ["ambito_no_dominio"]
    assert r[("ENDES", "callao", 2016)] == [] and r[("ENAHO", "callao", 2016)] == ["ambito_no_dominio"]
    assert r[("ENAHO", "departamento_15", 2024)] == ["ambito_no_dominio"]
    assert r[("ENAHO", "area_metropolitana_lima_callao", 2024)] == []


def test_paginas_impresas_informe_2015_2024():
    f = yaml.safe_load((RAIZ_REAL / "curados/capa0/dominios.yaml").read_text("utf-8"))["fuentes"]
    assert "p. 72 (PDF 74)" in f["ENAHO_POBREZA_2015_2024_AMBITOS"]["pagina"]
    assert "p. 220 (PDF 222)" in f["ENAHO_POBREZA_2015_2024_AMBITOS"]["pagina"]
    assert f["ENAHO_POBREZA_2015_2024_D8"]["pagina"] == "Cuadro N.º 4.1, p. 68 (PDF 70)"


def test_regla_sin_tipo_falla(tmp_path):
    datos = tmp_path / "curados" / "capa0"
    datos.mkdir(parents=True)
    (datos / "ambitos.yaml").write_text("[]\n", encoding="utf-8")
    (datos / "dominios.yaml").write_text(textwrap.dedent("""
        fuentes: {F: {titulo: t, url: "https://x", pagina: p. 1}}
        reglas:
          - {encuesta: ENAHO, anios: [2024, 2024], dominio_id: x, nombre_publicado: X, nivel: provincia,
             composicion: ["1501"], metodo: ubigeo, identificable_microdatos: true, fuente: F, confirmado: true}
        """), encoding="utf-8")
    df = pd.DataFrame({"nivel": ["distrito"], "ubigeo_inei": ["150101"], "vigente_desde": ["2017-10-22"],
                       "vigente_hasta": [None], "anio_datos_desde": [2018], "anio_datos_hasta": [None], "nombre": ["Lima"]})
    with pytest.raises(PapError, match="tipo"):
        T.construir_dominios(Rutas(tmp_path), df)


def test_ambitos_yaml_rotulos():
    amb = {a["ambito_id"]: a for a in yaml.safe_load((RAIZ_REAL / "curados/capa0/ambitos.yaml").read_text("utf-8"))}
    assert amb["LIMA_REGION"]["nombre_mostrado"] == "Lima Región (Lima Provincias)"
    assert amb["AREA_METROPOLITANA_LIMA_CALLAO"]["nombre_mostrado"] == "Lima Metropolitana y Callao"
    assert set(amb["AREA_METROPOLITANA_LIMA_CALLAO"]["contiene"]) == {"LIMA_METROPOLITANA", "CALLAO"}


# ======================================================================= microdatos ENDES

@pytest.fixture(scope="module")
def endes():
    d = _parquet(ENC / "endes_nino.parquet")
    d["amb"] = AL.ambito_lima_endes(d)
    d["met"] = AL.metodo_ambito_lima_endes(d)
    return d


def test_endes_todo_lima_asignado(endes):
    lima = endes[endes.departamento.isin(["15", "07"])]
    assert lima.amb.notna().all()
    assert endes[~endes.departamento.isin(["15", "07"])].amb.isna().all()
    assert (lima.groupby("anio").met.agg(lambda m: set(m)).to_dict()
            == {a: {"estrato_hv022" if a <= 2017 else "ubigeo"} for a in range(2015, 2026)})


def test_endes_lm_es_provincia_1501_desde_2018(endes):
    d = endes[endes.anio >= 2018]
    assert ((d.amb == AL.LIMA_METROPOLITANA) == (d.provincia_hogar == "1501")).all()
    assert ((d.amb == AL.CALLAO) == (d.departamento == "07")).all()


@pytest.mark.parametrize("clave", ["id_estrato", "id_conglomerado"])
def test_endes_ningun_estrato_ni_conglomerado_mezcla_ambitos(endes, clave):
    d = endes.assign(amb=endes.amb.fillna("RESTO"))
    n = d.groupby(["anio", clave]).amb.nunique()
    assert int((n > 1).sum()) == 0


def test_endes_estrato_sede_88_por_ciento(endes):
    for anio in (2015, 2016, 2017):
        d = endes[(endes.anio == anio) & (endes.departamento == "15")]
        share = d[d.id_estrato == "15-1"].peso.sum() / d.peso.sum()
        assert 0.86 <= share <= 0.90, (anio, share)
    d = endes[(endes.anio == 2018) & (endes.departamento == "15")]
    assert 0.86 <= d[d.amb == AL.LIMA_METROPOLITANA].peso.sum() / d.peso.sum() <= 0.90


def test_endes_reproduce_2017_lm_y_callao(endes):
    d = endes[(endes.anio == 2017) & endes.edad_meses.between(6, 35) & endes.hb_medida.fillna(False)
              & endes.anemia_hist.notna() & endes.pernocto]
    publicado = {AL.LIMA_METROPOLITANA: 33.3, AL.CALLAO: 32.4}  # nota de prensa INEI 088-2018 (criterio anterior)
    for amb, pub in publicado.items():
        s = d[d.amb == amb]
        est = 100 * np.average(s.anemia_hist.astype(float), weights=s.peso)
        assert abs(round(est, 1) - pub) <= 0.1 + 1e-9, (amb, est)


# ======================================================================= microdatos ENAHO

def test_enaho_ambitos_y_dominio8():
    e = _parquet(ENC / "enaho_sumaria.parquet")
    amb = AL.ambito_lima_enaho(e)
    assert (amb.fillna("-") == AL.ambito_por_ubigeo(e.ubigeo).fillna("-")).all()
    assert (AL.dominio8_enaho(e) == amb.isin([AL.LIMA_METROPOLITANA, AL.CALLAO])).all()
    # Informe técnico: 2015-2024 (Cuadro N.º III.1, p. 222) y 2016-2025 (Cuadro N.º III.1, p. 232; Cuadro N.º 4.1, p. 72)
    publicado = {2024: {AL.LIMA_METROPOLITANA: 27.6, AL.LIMA_REGION: 21.7, AL.CALLAO: 33.9,
                        AL.AREA_METROPOLITANA_LIMA_CALLAO: 28.2},
                 2025: {AL.LIMA_METROPOLITANA: 26.8, AL.LIMA_REGION: 21.6, AL.CALLAO: 32.1,
                        AL.AREA_METROPOLITANA_LIMA_CALLAO: 27.3}}
    for anio, cifras in publicado.items():
        x = e[e.anio == anio]
        for a, pub in cifras.items():
            s = x[AL.mascara_ambito(x, "ENAHO", a)]
            est = 100 * np.average(s.pobre.astype(float), weights=s.peso_persona)
            assert abs(round(est, 1) - pub) <= 0.1 + 1e-9, (anio, a, est)


# ======================================================================= inferencia_verificada.csv

def _inferencia(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_inferencia_ambitos_publicados(dom):
    cur = RAIZ_REAL / "catalogo" / "scripts" / "inferencia_verificada.csv"
    assert cur.read_bytes() == (RAIZ_REAL / "catalogo" / "inferencia_verificada.csv").read_bytes()
    filas = {(f["fuente"], int(f["anio"])): f for f in _inferencia(cur)}
    # ENAHO 2015–2025 coherente con dim_dominio (auditoría P2–P4, H6): los tres ámbitos publicados y el Callao no excluido
    for anio in range(2015, 2026):
        f = filas[("INEI-ENAHO", anio)]
        assert f["ambitos_publicados"] == "LIMA_METROPOLITANA;LIMA_REGION;CALLAO"
        assert "07" not in f["excluye_departamentos"].split(";")
        assert "Pobreza Monetaria" in f["ambitos_cita_documento"] and "Cuadro N.º III.1" in f["ambitos_cita_ubicacion"]
        tipos = set(dom[(dom.encuesta_id == "ENAHO") & (dom.anio == anio)
                        & dom.dominio_id.isin(["lima_metropolitana", "lima_provincias", "callao"])].tipo)
        assert tipos == {"ambito_publicado"}
    # Informe 2015-2024: página impresa y la del PDF aparte (H5)
    assert "p. 220 (PDF 222)" in filas[("INEI-ENAHO", 2024)]["ambitos_cita_ubicacion"]
    assert "p. 72 (PDF 74)" in filas[("INEI-ENAHO", 2024)]["ambitos_cita_ubicacion"]
    assert "1038-Modulo1629" in filas[("INEI-ENDES", 2025)]["cita_documento"]  # H10
    met_dom = (dom[(dom.encuesta_id == "ENDES") & (dom.dominio_id == "lima_metropolitana")]
               .set_index("anio").metodo.to_dict())
    for anio in range(2015, 2026):
        f = filas[("INEI-ENDES", anio)]
        assert f["ambitos_publicados"] == "LIMA_METROPOLITANA;LIMA_REGION"
        assert f["ambitos_metodo"] == met_dom[anio]
        assert "Cuadro N.º 1" in f["ambitos_cita_ubicacion"]
