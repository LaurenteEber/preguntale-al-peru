"""M0-06, en el Mac: las tablas curadas aplicadas a los Parquet de la ENDES 2024 (y a la ficha técnica en el almacén de crudos).

Necesitan `pap microdatos convertir --encuesta ENDES --anio 2024`, la biblioteca estandarizada y el cubo local: si faltan,
FALLAN (no se saltan; un salto daría un falso verde). Si un conteo no coincide no se ajusta nada: se diagnostica y se
escribe la consulta tipo C (AGENTS.md §5)."""
import csv
import re
from pathlib import Path

import duckdb
import pytest
import yaml

from pap.config import Rutas
from pap.capa0 import ambitos_lima
from pap.inferencia import tablas_curadas as tc

from conftest import RAIZ_REAL

pytestmark = [pytest.mark.regresion_microdatos, pytest.mark.solo_mac]

D = RAIZ_REAL / "biblioteca" / "microdatos" / "ENDES" / "2024"
ENDES_NINO = RAIZ_REAL / "biblioteca" / "estandarizada" / "encuestas" / "endes_nino.parquet"
CUBO_2024 = RAIZ_REAL / "backlog" / "slice-m0" / "evidencia" / "m0-00_filas_cubo_2024.csv"
# receta (indicador del cubo) → universo analítico
INDICADORES = {"endes_anemia_6_35m": "nino_anemia_6_35m_rm363",
               "endes_anemia_6_35m_oms2024": "nino_anemia_6_35m_oms2024",
               "endes_dci_menores_5": "nino_dci_0_59m"}
ESPERADOS = {"nino_anemia_6_35m_rm363": 9959, "nino_anemia_6_35m_oms2024": 9959, "nino_dci_0_59m": 19511}
NINOS_2024 = 20290


@pytest.fixture(scope="module")
def con():
    faltan = [f for f in ("RECH0", "RECH1", "RECH6", "RECH23", "REC0111", "REC91", "CSALUD01", "CSALUD08") if not (D / f"{f}.parquet").exists()]
    assert not faltan, f"faltan Parquet de 2024 ({faltan}): corre `pap microdatos convertir --encuesta ENDES --anio 2024`"
    assert ENDES_NINO.exists(), "falta biblioteca/estandarizada/encuestas/endes_nino.parquet"
    c = duckdb.connect()
    for f in D.glob("*.parquet"):
        c.execute(f"CREATE VIEW {f.stem} AS SELECT * FROM read_parquet('{f}')")
    c.execute(f"CREATE VIEW endes_nino AS SELECT * FROM read_parquet('{ENDES_NINO}') WHERE anio = 2024")
    return c


@pytest.fixture(scope="module")
def universos():
    return {u.id: u for u in tc.leer_universos(RAIZ_REAL)}


@pytest.fixture(scope="module")
def cubo():
    with open(CUBO_2024, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# RECH6 (un niño por fila) con lo de su fila de RECH1 (pernoctó) y de RECH0 (ubigeo, departamento, área, diseño)
NINO = """(SELECT c.*, p.HV103, h.HV001, h.HV021, h.HV022, h.HV024, h.HV025, h.HV005, h.UBIGEO
           FROM RECH6 c
           LEFT JOIN RECH1 p ON c.HHID = p.HHID AND c.HC0 = p.HVIDX
           LEFT JOIN RECH0 h ON c.HHID = h.HHID)"""


def _universo(con, u) -> str:
    return f"SELECT * FROM {NINO} WHERE {tc.sql_predicados(u.predicados)}"


# ------------------------------------------------------------------ universos: 9 959 / 19 511 sobre 20 290

def test_la_union_de_los_ninos_con_su_hogar_y_su_miembro_no_pierde_ni_repite_filas(con):
    assert con.execute("SELECT count(*) FROM RECH6").fetchone()[0] == NINOS_2024
    assert con.execute(f"SELECT count(*) FROM {NINO}").fetchone()[0] == NINOS_2024
    assert con.execute(f"SELECT count(*) FROM {NINO} WHERE HV103 IS NULL OR HV021 IS NULL OR UBIGEO IS NULL").fetchone()[0] == 0


def test_los_universos_dan_9959_anemia_en_los_dos_criterios_y_19511_dci_sobre_20290_ninos(con, universos):
    n = {i: con.execute(f"SELECT count(*) FROM ({_universo(con, universos[i])})").fetchone()[0] for i in ESPERADOS}
    assert n == ESPERADOS
    assert con.execute("SELECT count(*) FROM endes_nino").fetchone()[0] == NINOS_2024


def test_los_universos_son_los_mismos_ninos_que_endes_nino_parquet(con, universos):
    """Mismos niños, no solo el mismo conteo: (id_hogar, idx_nino) de endes_nino con el universo de `encuestas._en_universo`."""
    reglas = {"nino_anemia_6_35m_rm363": "edad_meses BETWEEN 6 AND 35 AND hb_medida AND anemia_hist_nivel IS NOT NULL AND pernocto",
              "nino_anemia_6_35m_oms2024": "edad_meses BETWEEN 6 AND 35 AND hb_medida AND anemia_oms2024_nivel IS NOT NULL AND pernocto",
              "nino_dci_0_59m": "edad_meses BETWEEN 0 AND 59 AND haz_valido AND pernocto"}
    for uid, regla in reglas.items():
        mios = set(con.execute(f"SELECT HHID, HC0 FROM ({_universo(con, universos[uid])})").fetchall())
        # id_hogar es el HHID de 9 caracteres; idx_nino es HC0
        suyos = set(con.execute(f"SELECT id_hogar, idx_nino FROM endes_nino WHERE {regla}").fetchall())
        assert len(mios) == len(suyos) == ESPERADOS[uid]
        assert mios == suyos, uid


def test_los_universos_dan_el_n_muestra_nacional_del_cubo(con, universos, cubo):
    for ind, uid in INDICADORES.items():
        nac = [f for f in cubo if f["indicador_id"] == ind and f["nivel"] == "nacional"]
        assert len(nac) == 1 and int(nac[0]["n_muestra"]) == ESPERADOS[uid], ind


# ------------------------------------------------------------------ territorios: 30 unidades por indicador

def _unidades(con, universos, territorios, uid):
    """{(nivel, unidad): n niños del universo} aplicando cada nivel de territorios.yaml."""
    out = {}
    for t in territorios:
        filas = con.execute(f"SELECT {t.unidad_expr} AS u, count(*) FROM ({_universo(con, universos[uid])}) "
                            f"WHERE {t.expr} GROUP BY 1 HAVING u IS NOT NULL").fetchall()
        out.update({(t.nivel, u): n for u, n in filas})
    return out


def test_territorios_produce_las_30_unidades_por_indicador(con, universos):
    territorios = tc.leer_territorios(RAIZ_REAL)
    for ind, uid in INDICADORES.items():
        unidades = _unidades(con, universos, territorios, uid)
        por_nivel = {}
        for nivel, _ in unidades:
            por_nivel[nivel] = por_nivel.get(nivel, 0) + 1
        assert por_nivel == {"nacional": 1, "dominio_subnacional": 2, "departamento": 24, "CALLAO": 1, "LIMA_METROPOLITANA": 1,
                             "LIMA_REGION": 1}, ind
        assert len(unidades) == 30, ind
        assert ("departamento", "07") not in unidades and ("departamento", "15") in unidades


def test_cada_unidad_tiene_el_mismo_n_muestra_que_el_cubo(con, universos, cubo):
    territorios = tc.leer_territorios(RAIZ_REAL)
    for ind, uid in INDICADORES.items():
        mias = {(nivel, unidad): n for (nivel, unidad), n in _unidades(con, universos, territorios, uid).items()}
        del_cubo = {(f["nivel"], f["territorio_id"]): int(f["n_muestra"]) for f in cubo if f["indicador_id"] == ind}
        # el cubo rotula igual los tres ámbitos de Lima, el área y el nacional («PE»)
        del_cubo = {(n, {"PE": "PE"}.get(t, t)): v for (n, t), v in del_cubo.items()}
        assert mias == del_cubo, ind


def test_callao_y_lima_region_por_hv024_dan_las_mismas_filas_que_el_ubigeo_del_hogar(con, universos):
    """Las dos formas de decirlo (HV024 de territorios.yaml y el prefijo del UBIGEO de ambitos_lima.py) coinciden en 2024."""
    filas = con.execute(f"SELECT UBIGEO, HV024 FROM {NINO}").fetchall()
    import pandas as pd
    ub = pd.Series([f[0] for f in filas])
    por_ubigeo = ambitos_lima.ambito_por_ubigeo(ub)
    t = {x.nivel: x for x in tc.leer_territorios(RAIZ_REAL)}
    for nivel in ("CALLAO", "LIMA_METROPOLITANA", "LIMA_REGION"):
        mias = con.execute(f"SELECT count(*) FROM {NINO} WHERE {t[nivel].expr}").fetchone()[0]
        assert mias == int((por_ubigeo == nivel).sum()) > 0, nivel
    assert con.execute(f"SELECT count(*) FROM RECH0 WHERE substr(UBIGEO, 1, 2) <> printf('%02d', HV024)").fetchone()[0] == 0


# ------------------------------------------------------------------ diseño muestral

def test_el_peso_el_estrato_y_la_upm_de_la_tabla_dan_lo_que_endes_nino_parquet(con):
    d = {(f.archivo, f.medicion): f for f in tc.leer_diseno_muestral(RAIZ_REAL)}[("RECH6", "hemoglobina")]
    peso = con.execute(f"""SELECT count(*), sum((abs(n.peso - ({d.peso_expr.replace('HV005', 'x.HV005')})) < 1e-12)::int)
                           FROM endes_nino n JOIN {NINO} x ON n.id_hogar = x.HHID AND n.idx_nino = x.HC0""").fetchone()
    assert peso == (NINOS_2024, NINOS_2024)
    estrato = con.execute(f"""SELECT sum((n.id_estrato = ({d.estrato_expr.replace('HV024', 'x.HV024').replace('HV022', 'x.HV022')}))::int)
                              FROM endes_nino n JOIN {NINO} x ON n.id_hogar = x.HHID AND n.idx_nino = x.HC0""").fetchone()[0]
    assert estrato == NINOS_2024
    upm = con.execute(f"""SELECT sum((n.id_conglomerado = CAST({d.psu_expr.replace('HV021', 'x.HV021')} AS VARCHAR))::int)
                          FROM endes_nino n JOIN {NINO} x ON n.id_hogar = x.HHID AND n.idx_nino = x.HC0""").fetchone()[0]
    assert upm == NINOS_2024


def test_hv001_es_igual_a_hv021_en_2024(con):
    """La ficha declara el panel por HV001 y el código usa HV021 como UPM. Esta prueba constata qué pasa en 2024 (no decide nada)."""
    filas, distintas, iguales, u001, u021 = con.execute(
        "SELECT count(*), count(*) FILTER (WHERE HV001 IS DISTINCT FROM HV021), count(*) FILTER (WHERE HV001 = HV021), "
        "count(DISTINCT HV001), count(DISTINCT HV021) FROM RECH0").fetchone()
    assert (filas, distintas, iguales) == (37390, 0, 37390)
    assert u001 == u021 == 3254
    # las demás variables de conglomerado que la tabla usa (mujer: V001/V021; salud: QHCLUSTER) dicen lo mismo, hogar por hogar
    assert con.execute("SELECT count(*) FROM REC0111 m JOIN RECH0 h USING (HHID) WHERE m.V001 <> h.HV001 OR m.V021 <> h.HV021").fetchone()[0] == 0
    for salud in ("CSALUD01", "CSALUD08"):
        assert con.execute(f"SELECT count(*) FROM {salud} s JOIN RECH0 h USING (HHID) WHERE s.QHCLUSTER <> h.HV001").fetchone()[0] == 0, salud


def test_el_estrato_de_la_mujer_es_el_del_hogar(con):
    d = {(f.archivo, f.medicion): f for f in tc.leer_diseno_muestral(RAIZ_REAL)}[("REC0111", "individual_mujer")]
    malas = con.execute(f"SELECT count(*) FROM REC0111 m JOIN RECH0 h USING (HHID) "
                        f"WHERE ({d.estrato_expr.replace('V024', 'm.V024').replace('V022', 'm.V022')}) "
                        f"<> printf('%02d-%d', h.HV024, h.HV022)").fetchone()[0]
    assert malas == 0


def test_las_variables_de_diseno_de_la_tabla_existen_en_su_archivo_o_en_el_que_se_une(con):
    """Cada columna de peso, estrato y UPM está en el archivo de la fila o en el padre de sus `uniones_para_diseno`."""
    for f in tc.leer_diseno_muestral(RAIZ_REAL):
        archivos = [f.archivo] + [padre for _, _, padre, _ in f.uniones]
        cols = set()
        for a in archivos:
            cols |= {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {a}").fetchall()}
        usadas = set(re.findall(r"[A-Z][A-Z0-9_]{2,}", " ".join([f.peso_expr, f.estrato_expr, f.psu_expr, f.upm_estable_expr])))
        usadas -= {"CASE", "WHEN", "THEN", "END"}
        assert usadas <= cols, f"{f.llave}: {sorted(usadas - cols)}"
        peso = f.peso_expr.split("/")[0]
        assert con.execute(f"SELECT count({peso}) FROM {[a for a in archivos if peso in {r[0] for r in con.execute(f'DESCRIBE SELECT * FROM {a}').fetchall()}][0]}").fetchone()[0] > 0


# ------------------------------------------------------------------ perfil anual

def test_perfil_2024_estratos_conglomerados_y_ubigeo(con):
    p = tc.leer_perfil_anual(RAIZ_REAL)[0]
    estratos, upm, ancho_min, ancho_max = con.execute(
        "SELECT count(DISTINCT printf('%02d-%d', HV024, HV022)), count(DISTINCT HV021), min(length(UBIGEO)), max(length(UBIGEO)) FROM RECH0").fetchone()
    assert (p.n_estratos, p.n_upm) == (estratos, upm) == (240, 3254)
    assert p.ubigeo_minimo == "distrito" and ancho_min == ancho_max == 6


# ------------------------------------------------------------------ cortes

def test_cada_variable_de_los_cortes_existe_y_sus_codigos_estan_en_las_categorias(con):
    for c in tc.leer_cortes(RAIZ_REAL):
        for v in c.por_encuesta["ENDES"]:
            cols = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {v.archivo}").fetchall()}
            assert v.variable in cols, f"{v.archivo}.{v.variable}"
            cats = v.categorias or c.categorias
            if cats:
                vistos = {int(r[0]) for r in con.execute(f"SELECT DISTINCT {v.variable} FROM {v.archivo} WHERE {v.variable} IS NOT NULL").fetchall()}
                assert vistos <= set(cats), f"{v.archivo}.{v.variable}: códigos {sorted(vistos - set(cats))} sin categoría"


def test_los_cortes_de_otros_archivos_se_unen_a_los_ninos_por_hhid_sin_perder_ni_repetir_filas(con):
    for archivo in {v.archivo for c in tc.leer_cortes(RAIZ_REAL) for v in c.por_encuesta["ENDES"] if v.unidad == "hogar"}:
        assert con.execute(f"SELECT count(*) FROM RECH6 c LEFT JOIN {archivo} a ON c.HHID = a.HHID").fetchone()[0] == NINOS_2024, archivo


def test_las_categorias_de_los_cortes_son_las_etiquetas_de_valor_del_indice(con):
    """Las palabras de `categorias` salen de las etiquetas de valor de cada archivo (biblioteca/variables/categorias.parquet)."""
    ruta = RAIZ_REAL / "biblioteca" / "variables"
    assert (ruta / "categorias.parquet").exists(), "falta el índice de variables: `pap variables indexar --encuesta ENDES --anio 2024`"
    etiquetas = {(a, v, int(float(cod))): e for a, v, cod, e in duckdb.sql(
        f"SELECT v.archivo, v.variable, c.codigo, c.etiqueta_curada FROM read_parquet('{ruta / 'categorias.parquet'}') c "
        f"JOIN read_parquet('{ruta / 'variables.parquet'}') v USING (var_id)").fetchall()}
    for c in tc.leer_cortes(RAIZ_REAL):
        for v in c.por_encuesta["ENDES"]:
            for cod in v.categorias or c.categorias or {}:
                assert (v.archivo, v.variable, cod) in etiquetas, f"{v.archivo}.{v.variable} código {cod} no está en el índice"


# ------------------------------------------------------------------ la ficha técnica

FICHA = {  # página (como la numera el PDF) → frases que la cita dice textualmente (sin tildes de espacios ni saltos de línea)
    2: ["Los hogares particulares y sus miembros", "Todas las mujeres de 12 a 49 años de edad", "Una persona de 15 años a más de edad por cada hogar",
        "Todos los niños menores de 12 años"],
    3: ["misma numeración en la variable HV001 (conglomerado) en los años 2023 y 2024 son paneles", "de enero a diciembre",
        "Censos Nacionales XII de Población y VII de Vivienda del año 2017 (CPV 2017)"],
    4: ["3 254 1 484 926 844", "Comprende los 43 distritos que conforman Lima Metropolitana", "Barranca, Cajatambo, Canta, Cañete, Huaral, Huarochirí, Huaura, Oyón y Yauyos",
        "Provincia Constitucional"],
    7: ["Región Natural: Costa, Sierra y Selva", "Cada uno de los 24 departamentos del país y la Provincia Constitucional del Callao",
        "se mantendrá el 66.7% de muestra de conglomerados de un año a otro", "Para el año 2025 se deberán seleccionar una nueva muestra maestra",
        "6 submuestras", "Nacional Urbana", "Nacional Rural"],
    8: ["hayan pernoctado"],
    9: ["niveles de hemoglobina niños de 4 meses a menores de 6 años", "antropométrica (peso y talla) en niños menores de 6 años"],
    10: ["ENTREVISTA DIRECTA (presencial)", "Tablet"],
    11: ["HV001: conglomerado, HV022: estrato, peso=HV005/1000000", "se encuentra en el módulo RECH0", "V001: conglomerado, V022: estrato, peso=V005/1000000",
         "se encuentra en el módulo REC0111", "qhcluster: conglomerado, HV022: estrato, peso= PESO15_AMAS /1000000",
         "qhcluster: conglomerado, HV022: estrato, peso= Pesomen12/1000000", "desnutrición y anemia en menores de 5 años"],
    13: ["1.6 Índice de Bienestar"],
    14: ["1.7 Quintil de Riqueza", "dos versiones"],
    15: ["4. PORCENTAJE DE MENORES DE CINCO AÑOS CON DESNUTRICIÓN CRÓNICA"],
    16: ["6. PORCENTAJE DE NIÑOS DE 6 A 35 MESES DE EDAD (RM 363-2022-MINSA)", "7. PORCENTAJE DE NIÑOS DE 6 A 35 MESES DE EDAD CON ANEMIA (Nueva directriz OMS 2024"],
}


def test_las_citas_a_la_ficha_tecnica_dicen_lo_que_la_ficha_dice_en_esa_pagina():
    import pdfplumber
    from pap.inferencia import almacen

    ins = almacen._insumo(Rutas(RAIZ_REAL), "INEI-ENDES", "endes-2024-ficha-tecnica")
    with pdfplumber.open(ins.ruta) as pdf:
        assert len(pdf.pages) == 21
        textos = {i: re.sub(r"\s+", " ", pdf.pages[i - 1].extract_text() or "") for i in FICHA}
    for pagina, frases in FICHA.items():
        for frase in frases:
            assert re.sub(r"\s+", " ", frase) in textos[pagina], f"p. {pagina}: «{frase}»"
