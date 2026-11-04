"""SP-03/TE-08 (ronda 3): fact_sien_hb_ubigeo y la cobertura de tamizaje del SIEN.

Origen: 03_auditoria/ola0/pendientes_menores/sp03_sien/pruebas_v3.py. Decisión del dueño (7/10/2026): la cobertura de
tamizaje se publica SOLO por departamento, con dos cotas (inferior: niños procedentes del departamento; superior: más los
niños sin procedencia atendidos en establecimientos del departamento); el semáforo usa la cota superior y se avisa
cuando el intervalo cruza el 50 % (R-REG-07, sien_umbral_tamizaje_pct). R-TERRITORIO-08 se evalúa por departamento
solo como diagnóstico (E-06). UbigeoPN es «procedencia del niño» (diccionario oficial), no residencia del Padrón."""
import io
import zipfile

import duckdb
import pandas as pd
import pytest

from pap.capa0 import puentes as P

from conftest import RAIZ_REAL

DIM = RAIZ_REAL / "biblioteca" / "dimensiones"
FACT = DIM / "fact_sien_hb_ubigeo.parquet"
POB = DIM / "fact_poblacion_grupo.parquet"
UMBRAL_SEMAFORO = 0.50  # R-REG-07 sien_umbral_tamizaje_pct
F635 = "grupo_edad IN ('6-11m', '12-23m', '24-35m')"


# ----------------------------------------------------------------- unitarias del parche (U-01 a U-04)
def test_dx_esperado_cortes_completos():
    hbc = pd.Series([10.5, 10.49, 9.5, 9.49, 7.0, 6.99, 11.0, 10.99, 10.0, 9.99, 7.0, 6.99, float("nan"), 12.0])
    edad = pd.Series([6, 6, 23.9, 23.9, 23.9, 23.9, 24, 24, 59.9, 59.9, 59.9, 59.9, 30, 5.9])
    esp = ["Normal", "Anemia Leve", "Anemia Leve", "Anemia Moderada", "Anemia Moderada", "Anemia Severa",
           "Normal", "Anemia Leve", "Anemia Leve", "Anemia Moderada", "Anemia Moderada", "Anemia Severa", None, None]
    got = P.dx_esperado(hbc, edad).tolist()
    for g, e in zip(got, esp):
        assert (pd.isna(g) if e is None else g == e), (g, e)


def test_ajuste_altitud_oms2024_y_nan():
    aj = P.ajuste_hb_oms2024(pd.Series(["499", "500", None, "x"]))
    assert aj.iloc[0] == 0
    assert abs(aj.iloc[1] - (0.0056384 * 500 + 0.0000003 * 500 ** 2) / 10) < 1e-12
    assert aj.iloc[2:].isna().all()


def test_dx_nulo_no_es_anemia():
    """Llama a la función de puentes.py (auditoría final, hallazgo 4: la versión anterior reimplementaba la lógica)."""
    dx = pd.Series(["Normal", None, "Anemia Leve", "", " Anemia Severa ", "Otro", float("nan")], dtype=object)
    valido, anemia = P.marcar_anemia(dx)
    assert valido.tolist() == [True, False, True, False, True, False, False]
    assert anemia.tolist() == [False, False, True, False, True, False, False]
    assert not (anemia & ~valido).any()


def test_etiquetas_r_territorio_08():
    assert P.nivel_r_territorio_08(0.995) == "distrito"
    assert P.nivel_r_territorio_08(0.9773) == "distrito_con_advertencia"
    assert P.nivel_r_territorio_08(0.846) == "solo_departamento_o_nacional"
    assert P.nivel_r_territorio_08(float("nan")) == "sin_dato"


def test_roles_de_los_tres_ubigeos():
    assert P.UBIGEOS_SIEN == {"Ubigeo_EESS": "establecimiento", "UbigeoPN": "procedencia_nino",
                              "UbigeoREN": "referencia_altitud_ajuste_hb"}


# ----------------------------------------------------------------- tabla construida (S-02, S-04, S-06, S-07)
@pytest.fixture(scope="module")
def con():
    if not FACT.exists() or not POB.exists():
        pytest.skip("fact_sien_hb_ubigeo o fact_poblacion_grupo no construidos")
    c = duckdb.connect()
    c.execute(f"CREATE VIEW f AS SELECT * FROM '{FACT}'")
    c.execute(f"""CREATE VIEW pob AS SELECT ubigeo_inei, nivel, valor FROM '{POB}'
                  WHERE anio = 2025 AND grupo_id = '6-35m' AND sexo = 'T' AND geografia_base = 'vigente_2025'""")
    c.execute(f"CREATE VIEW f635 AS SELECT * FROM f WHERE {F635}")
    return c


@pytest.fixture(scope="module")
def semaforo(con):
    d = con.execute("""
        WITH den AS (SELECT substr(ubigeo_inei, 1, 2) u, sum(valor) p FROM pob WHERE nivel = 'distrito' GROUP BY 1),
        inf AS (SELECT substr(ubigeo_procedencia, 1, 2) u, sum(filas) n FROM f635 WHERE ubigeo_procedencia IS NOT NULL GROUP BY 1),
        sinpn AS (SELECT substr(ubigeo_eess, 1, 2) u, sum(filas) n FROM f635 WHERE ubigeo_procedencia IS NULL GROUP BY 1)
        SELECT den.u dpto, inf.n / p cob_inf, (inf.n + coalesce(sinpn.n, 0)) / p cob_sup
        FROM den JOIN inf USING (u) LEFT JOIN sinpn USING (u) ORDER BY 1""").df()
    d["aviso_intervalo_cruza_umbral"] = (d.cob_inf < UMBRAL_SEMAFORO) & (d.cob_sup >= UMBRAL_SEMAFORO)
    return d


def test_s07_clave_unica(con):
    dup = con.execute("""SELECT count(*) - count(DISTINCT (anio, id_insumo, cod_ipress, ubigeo_eess,
        coalesce(ubigeo_procedencia, '-'), ubigeo_ref_altitud, grupo_edad)) FROM f""").fetchone()[0]
    assert dup == 0


@pytest.mark.solo_mac
def test_s04_conservacion_contra_el_crudo(con):
    from pap.capa0 import insumos
    from pap.config import Rutas
    ins = insumos.ultimo(Rutas(RAIZ_REAL), "INS-CENAN-SIEN", recurso=P.RECURSO_SIEN)
    crudo = 0
    with zipfile.ZipFile(ins.ruta) as z:
        for nom in z.namelist():
            if nom.lower().endswith(".csv") and "/Hb/" in "/" + nom.replace("\\", "/"):
                with z.open(nom) as fh:
                    crudo += sum(1 for _ in io.TextIOWrapper(fh, encoding="utf-8-sig")) - 1
    filas, anemia, validos, insumo = con.execute(
        "SELECT sum(filas), sum(filas_con_anemia), sum(filas_dx_valido), any_value(id_insumo) FROM f").fetchone()
    assert filas == crudo and anemia <= validos
    assert insumo == ins.hash


def test_columnas_y_rotulos(con):
    cols = {r[0] for r in con.execute("DESCRIBE f").fetchall()}
    assert {"ubigeo_eess", "ubigeo_procedencia", "ubigeo_ref_altitud"} <= cols
    assert "ubigeo_residencia_pn" not in cols  # UbigeoPN es procedencia (diccionario oficial), no residencia
    assert con.execute("SELECT count(*) FROM f WHERE ubigeo_eess IS NULL OR ubigeo_ref_altitud IS NULL").fetchone()[0] == 0


def test_s02_cobertura_publicada_solo_por_departamento_y_no_mayor_a_1(semaforo):
    assert len(semaforo) == 25 and semaforo.dpto.str.fullmatch(r"\d{2}").all()
    assert (semaforo.cob_inf <= semaforo.cob_sup).all()
    assert (semaforo.cob_sup <= 1).all(), semaforo[semaforo.cob_sup > 1]


def test_s06_aviso_cuando_el_intervalo_cruza_el_50(semaforo):
    cruza = set(semaforo.loc[semaforo.aviso_intervalo_cruza_umbral, "dpto"])
    # referencia 7/10/2026 (ZIP sha256:b05f29b1…): La Libertad, Loreto, Moquegua, Puno y Tacna
    assert cruza == {"13", "16", "18", "21", "23"}, sorted(cruza)


def test_e06_procedencia_por_departamento_en_revision():
    r = DIM / "revision" / "sien_pn_6_35m_por_departamento.csv"
    if not r.exists():
        pytest.skip("puentes no construido")
    d = pd.read_csv(r, dtype={"departamento_eess": str})
    assert set(d.nivel_r_territorio_08) <= {"distrito", "distrito_con_advertencia", "solo_departamento_o_nacional"}
    # solo Huancavelica (09) y Ayacucho (05) llegan al 95 %; aun así, la cobertura no se publica bajo departamento
    assert set(d.loc[d.pct_pn_ubicado >= 0.95, "departamento_eess"].str.zfill(2)) == {"05", "09"}


def test_documentacion_no_se_toma_como_datos(monkeypatch):
    """Con --actualizar-insumos (lock ignorado), la última captura de INS-CENAN-SIEN es documentación (.docx);
    puentes.py elige el ZIP de datos por nombre de recurso (auditoría final, hallazgo 6)."""
    from pap.capa0 import insumos
    from pap.config import Rutas
    monkeypatch.setattr(insumos, "ACTUALIZAR_LOCK", True)
    rutas = Rutas(RAIZ_REAL)
    sin_filtro = insumos.ultimo(rutas, "INS-CENAN-SIEN")
    con_filtro = insumos.ultimo(rutas, "INS-CENAN-SIEN", recurso=P.RECURSO_SIEN)
    assert not sin_filtro.original_filename.lower().endswith(".zip") or "diccionario" in sin_filtro.original_filename.lower()
    assert con_filtro.original_filename.startswith("BD SIEN-HIS") and con_filtro.original_filename.endswith(".zip")
