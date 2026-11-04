"""Pieza A de las decisiones del gasto (rondas 1-2, dueño 7/10/2026): ejecutoras_alcance.yaml v2 (criterio único,
reclasificaciones, referencia_nacional, verificar_procedencia, mixta) y fact_gasto_territorial v1.3.0 (actividad,
clasificador de gasto, fuente y rubro). Pruebas sobre el YAML y sobre las tablas publicadas (no reconstruye: el
constructor completo lo prueba test_gasto.py). Evidencia: 03_auditoria/ola0/decisiones_gasto/implementacion/pieza_a/.
E3 (decisiones del 8/10/2026; YAML v3, fact v1.4.0): se actualizan las cifras de Lima, las mixtas (25), el INPE ORL
(lima_departamento) y revisado_dueno (todas); sus pruebas propias están en test_gasto_e3.py."""
import csv
import json

import duckdb
import pytest
import yaml

from pap.capa0 import gasto as G
from pap.capa0 import salida
from pap.config import Rutas
from pap.errores import PapError

from conftest import RAIZ_REAL

DATOS = RAIZ_REAL / "curados" / "capa0"
DIM = RAIZ_REAL / "biblioteca" / "dimensiones"
R2 = RAIZ_REAL / "tests" / "fixtures" / "gasto"
YAML = yaml.safe_load((DATOS / "ejecutoras_alcance.yaml").read_text(encoding="utf-8"))
POR_SEC = {e["sec_ejec"]: e for e in YAML}
A_LIMA = {"127", "125", "78", "1636", "1635"}            # INMP, INR, Folklore, Arte Dramático, Ballet
REFNAC = {"1235", "1512"}                                 # INEN, INSN San Borja
SIN_DATO = {"126", "123", "124", "121"}                   # INSN Breña, INCN, INO, INSM
SE_MANTIENEN_LIMA = {"1700", "1465"}                      # Cortes de Lima Este y Lima Norte
INPE_ORL = "18"                                           # E3 (8/10/2026): lima_departamento
MIXTAS_E3 = {"17", "117", "1312"}                         # E3: INPE Sede Central, MINSA central, DIREICAJ
# devengado y PIM del archivo del MEF (base), por año: la fact los conserva exactos (R-GASTO-01)
TOTALES = {2023: ("223052121012.98", "249947413952.00"), 2024: ("238896702037.49", "262058019205.00"),
           2025: ("253675294538.35", "272450859407.00")}


# ---------------- YAML
def test_reclasificaciones_aprobadas():
    for s in A_LIMA:
        assert POR_SEC[s]["alcance"] == "lima_metropolitana", s
    for s in REFNAC:
        assert POR_SEC[s]["alcance"] == "nacional" and POR_SEC[s]["referencia_nacional"], s
    for s in SIN_DATO:
        e = POR_SEC[s]
        assert e["alcance"] == "nacional" and e["verificar_procedencia"] and not e["referencia_nacional"], s
    assert POR_SEC["151"]["alcance"] == "nacional" and POR_SEC["151"]["base_alcance"]["paso"] == "P1"   # INS
    for s in SE_MANTIENEN_LIMA:
        assert POR_SEC[s]["alcance"] == "lima_metropolitana" and POR_SEC[s]["revisado_dueno"], s
    assert POR_SEC[INPE_ORL]["alcance"] == "lima_departamento" and POR_SEC[INPE_ORL]["revisado_dueno"]
    assert POR_SEC["1067"]["alcance"] == "nacional" and POR_SEC["1067"]["revisado_dueno"]          # Sanidad PNP


def test_yaml_igual_a_tabla_final_aprobada():
    """Cada entidad de tabla_final_v2.csv tiene el alcance aprobado (los 4 institutos sin dato: nacional, decisión 8)."""
    with open(R2 / "ronda2" / "w3_ejecutoras" / "tabla_final_v2.csv", encoding="utf-8") as f:
        tabla = {r["sec_ejec"]: r for r in csv.DictReader(f)}
    for s, t in tabla.items():
        if s == "1741":  # solo obras; ya es nacional_multidepartamental en la fact, no está en el YAML
            assert s not in POR_SEC
            continue
        e = POR_SEC[s]
        esperado = "nacional" if s in SIN_DATO else "lima_departamento" if s == INPE_ORL else t["alcance_propuesto"]
        assert e["alcance"] == esperado, s
        assert e["referencia_nacional"] == (t["referencia_nacional"] == "True"), s
        assert e["verificar_procedencia"] == (t["verificar_procedencia"] == "True" or s in SIN_DATO), s
        assert e["revisado_dueno"] and e["base_alcance"]["confianza"] == t["confianza"], s
        if t["pct_usuarios_lima"]:
            assert e["base_alcance"]["L_pct"] == float(t["pct_usuarios_lima"]) and e["base_alcance"]["L_fuente"], s


def test_mixtas_y_revisado_dueno():
    with open(R2 / "ejecutoras" / "veredicto_231.csv", encoding="utf-8") as f:
        ver = {r["sec_ejec"]: r["veredicto"] for r in csv.DictReader(f)}
    mixtas = {e["sec_ejec"] for e in YAML if e["mixta"]}
    assert mixtas == {s for s, v in ver.items() if v == "mixta_mantener"} | MIXTAS_E3 and len(mixtas) == 25
    assert all(POR_SEC[s]["alcance"] == "nacional" and POR_SEC[s]["revisado_dueno"] for s in mixtas)
    # E3 (8/10/2026): las 171 sin decisión individual quedan decididas (166 en bloque y 5 una por una): todas revisadas
    # (auditoría de E3, H3: se agregan 20 ejecutoras sin meta 15, sin decisión del dueño)
    assert sum(e["revisado_dueno"] for e in YAML) == 231 and len(YAML) == 254   # P3: + 3 sin meta 15
    for e in YAML:
        assert {"referencia_nacional", "verificar_procedencia", "mixta", "base_alcance"} <= set(e)
        assert e["base_alcance"]["confianza"] in {"alta", "media", "baja"}
        assert (e["base_alcance"]["decision"] is not None) == e["revisado_dueno"]
        assert not e["referencia_nacional"] or e["alcance"] == "nacional"


def _raiz_con_yaml(tmp_path, entradas):
    (tmp_path / "curados" / "capa0").mkdir(parents=True)
    (tmp_path / "curados" / "capa0" / "ejecutoras_alcance.yaml").write_text(
        yaml.safe_dump(entradas, allow_unicode=True), encoding="utf-8")
    return Rutas(tmp_path)


def test_lector_rechaza_referencia_nacional_fuera_de_nacional(tmp_path):
    malo = [dict(e) for e in YAML]
    malo[[e["sec_ejec"] for e in malo].index("127")]["referencia_nacional"] = True   # INMP es lima_metropolitana
    with pytest.raises(PapError, match="referencia_nacional exige alcance nacional"):
        G._alcance_ejecutoras(_raiz_con_yaml(tmp_path, malo))


def test_lector_exige_campos_nuevos(tmp_path):
    malo = [{k: v for k, v in e.items() if k != "mixta"} for e in YAML]
    with pytest.raises(PapError, match="faltan campos"):
        G._alcance_ejecutoras(_raiz_con_yaml(tmp_path, malo))
    ok = G._alcance_ejecutoras(Rutas(RAIZ_REAL))
    assert set(ok.loc[ok.referencia_nacional, "sec_ejec"]) == REFNAC


def test_clave_fact_igual_en_constructor_y_salida():
    assert salida.CLAVES["fact_gasto_territorial"] == ", ".join(G.CLAVE_FACT)
    assert {"actividad_accion_obra", "clasificador_gasto", "fuente_financiamiento", "rubro"} <= set(G.CLAVE_FACT)


# ---------------- tablas publicadas
@pytest.fixture(scope="module")
def con():
    if not (DIM / "fact_gasto_territorial.parquet").exists():
        pytest.skip("gasto no construido")
    man = json.loads((DIM / "manifiesto_s3_gasto.json").read_text(encoding="utf-8"))
    if "actividad_accion_obra" not in man["tablas"]["fact_gasto_territorial"]["columnas"]:
        pytest.skip("la fact publicada es anterior a la pieza A")
    c = duckdb.connect()
    c.execute("SET enable_progress_bar=false; SET memory_limit='2GB'; SET threads=2")
    c.execute(f"CREATE VIEW fact AS SELECT * FROM '{DIM / 'fact_gasto_territorial.parquet'}'")
    c.execute(f"CREATE VIEW ue AS SELECT * FROM '{DIM / 'dim_unidad_ejecutora.parquet'}'")
    yield c
    c.close()


def test_campos_nuevos_presentes_y_no_nulos(con):
    cols = {r[0] for r in con.execute("DESCRIBE fact").fetchall()}
    nuevos = {"actividad_accion_obra", "actividad_accion_obra_nombre", "grupo_funcional", "categoria_gasto",
              "clasificador_gasto", "nivel_clasificador", "clasificador_gasto_nombre", "generica_nombre",
              "fuente_financiamiento", "fuente_financiamiento_nombre", "rubro", "rubro_nombre",
              "referencia_nacional", "verificar_procedencia", "ejecutora_mixta", "cuenta_en_lima"}
    assert nuevos <= cols
    r = con.execute("""SELECT count(*) FILTER (WHERE actividad_accion_obra IS NULL OR actividad_accion_obra_nombre IS NULL
                                              OR clasificador_gasto IS NULL OR generica_nombre IS NULL
                                              OR fuente_financiamiento IS NULL OR fuente_financiamiento_nombre IS NULL
                                              OR rubro IS NULL OR rubro_nombre IS NULL OR grupo_funcional IS NULL
                                              OR referencia_nacional IS NULL OR cuenta_en_lima IS NULL),
                              count(*) FILTER (WHERE (generica = '4') <> (nivel_clasificador = 'especifica_detalle')),
                              count(*) FILTER (WHERE generica = '4' AND (clasificador_gasto NOT LIKE '2.4.%'
                                                                         OR clasificador_gasto_nombre IS NULL)),
                              count(*) FILTER (WHERE generica <> '4' AND clasificador_gasto <> '2.' || generica),
                              count(DISTINCT version_tabla), any_value(version_tabla)
                       FROM fact""").fetchone()
    assert r == (0, 0, 0, 0, 1, G.VERSION_TABLA)


def test_conservacion_exacta_por_anio(con):
    tot = {a: (str(d), str(p)) for a, d, p in con.execute(
        "SELECT anio, sum(devengado), sum(pim) FROM fact GROUP BY 1 ORDER BY 1").fetchall()}
    assert tot == TOTALES


def test_clave_unica_y_orden_2025(con):
    clave = ", ".join(G.CLAVE_FACT)
    assert con.execute(f"SELECT count(*) FROM (SELECT hash({clave}) h, count(*) n FROM fact GROUP BY h HAVING n > 1)"
                       ).fetchone()[0] == 0
    # el Parquet está ordenado por la clave (se comprueba en un año: anio es la primera columna de la clave)
    malos = con.execute(f"""
        SELECT count(*) FROM (
          SELECT file_row_number, row_number() OVER (ORDER BY {clave}) - 1 AS pos
          FROM read_parquet('{DIM / 'fact_gasto_territorial.parquet'}', file_row_number = true) WHERE anio = 2025)
        WHERE file_row_number - pos <> (SELECT min(file_row_number) FROM read_parquet(
              '{DIM / 'fact_gasto_territorial.parquet'}', file_row_number = true) WHERE anio = 2025)""").fetchone()[0]
    assert malos == 0


def test_referencia_nacional_fuera_de_lima_con_sus_obras(con):
    r = con.execute("""SELECT sec_ejec, nivel_atribucion, bool_or(cuenta_en_lima), round(sum(devengado)/1e6, 1)
                       FROM fact WHERE referencia_nacional AND departamento_atribucion = '15' AND NOT es_transferencia
                       GROUP BY 1, 2 ORDER BY 1, 2""").fetchall()
    assert r == [("1235", "departamento_meta", False, 1351.9), ("1235", "distrito_inversion", False, 57.7),
                 ("1512", "departamento_meta", False, 708.9), ("1512", "distrito_inversion", False, 4.6)]
    assert con.execute("SELECT count(*) FROM fact WHERE referencia_nacional AND cuenta_en_lima").fetchone()[0] == 0
    assert con.execute("SELECT count(*) FROM fact WHERE cuenta_en_lima AND departamento_atribucion <> '15'").fetchone()[0] == 0
    assert con.execute("""SELECT count(*) FROM fact WHERE cuenta_en_lima AND alcance_ejecutora = 'nacional'""").fetchone()[0] == 0


def test_lima_igual_a_escenario_aprobado(con):
    """Dpto 15, sin transferencias, 2023-2025 (millones). Pieza A: impacto_v2.csv S3v2 menos los 4 institutos sin dato
    (decisión 8): todo 77 689,0 y salud 17 083,5. E3 (8/10/2026): − 1 682,8 de obras de sede o función nacional
    (salud − 47,5) + 148,8 de COAR Lima y CENFOTUR = 76 155,0; tras la auditoría de E3 (H1) el Hospital PNP vuelve a
    Lima (+17,4): 76 172,4. La línea aparte no cambia. Ver
    curados/generadores/e3_gasto/verificar.py."""
    r = dict((p, (l, rn)) for p, l, rn in con.execute("""
        SELECT p, round(sum(devengado) FILTER (WHERE cuenta_en_lima)/1e6, 1),
                  round(sum(devengado) FILTER (WHERE referencia_nacional)/1e6, 1)
        FROM (SELECT *, unnest(list_filter(['salud', 'pp0002', 'pp0024', 'todo'],
                 x -> (x = 'salud' AND funcion = 'SALUD') OR (x = 'pp0002' AND programa_ppto = '0002')
                      OR (x = 'pp0024' AND programa_ppto = '0024') OR x = 'todo')) AS p
              FROM fact WHERE departamento_atribucion = '15' AND NOT es_transferencia)
        GROUP BY p""").fetchall())
    # P3 (fact v1.5.0): el GR Callao con meta 15 sale al 07 (salud −6,4; todo −9,2)
    if "cuenta_en_ambito" in {x[0] for x in con.execute("DESCRIBE fact").fetchall()}:
        assert r == {"salud": (17029.7, 2117.3), "pp0002": (1449.3, 30.9), "pp0024": (475.0, 845.3),
                     "todo": (76163.1, 2123.1)}
        return
    assert r == {"salud": (17036.1, 2117.3), "pp0002": (1449.3, 30.9), "pp0024": (475.0, 845.3),
                 "todo": (76172.4, 2123.1)}


def test_cifras_nacionales_de_los_casos_de_prueba(con):
    """casos_prueba_alcance.json G3: PP 0024 país 2023-2025 = 3 433, INEN 759 (el alcance no cambia el total)."""
    casos = json.loads((R2 / "ronda2" / "w3_ejecutoras" / "casos_prueba_alcance.json").read_text(encoding="utf-8"))
    assert "3 433" in next(c for c in casos["casos"] if c["id"] == "G3")["decision"]
    r = con.execute("""SELECT round(sum(devengado)/1e6, 0), round(sum(devengado) FILTER (WHERE sec_ejec = '1235')/1e6, 0)
                       FROM fact WHERE programa_ppto = '0024' AND NOT es_transferencia""").fetchone()
    assert r == (3433, 759)


def test_series_ex_pan_con_la_nueva_fact(con):
    """Control (no es dim_tema_gasto v1.2): PP 1001, opción C y serie por concepto (esta usa la actividad)."""
    C = """programa_ppto = '1001' AND tipo_act_proy = 'ACTIVIDAD' AND producto_proyecto NOT IN ('3000891', '3000892')
           AND NOT (producto_proyecto = '3000001' AND funcion <> 'SALUD')"""
    APN = "programa_ppto = '9002' AND actividad_accion_obra IN ('5004428', '5004429', '5005326')"
    r = con.execute(f"""SELECT anio, round(sum(devengado) FILTER (WHERE programa_ppto = '1001')/1e6, 0),
                               round(sum(devengado) FILTER (WHERE {C})/1e6, 0),
                               round(sum(devengado) FILTER (WHERE ({C}) OR ({APN}))/1e6, 0)
                        FROM fact WHERE NOT es_transferencia GROUP BY 1 ORDER BY 1""").fetchall()
    assert r == [(2023, 2750, 2056, 2179), (2024, 3607, 2327, 2429), (2025, 3867, 2366, 2456)]


def test_dim_unidad_ejecutora_lleva_las_marcas(con):
    r = con.execute("""SELECT count(DISTINCT sec_ejec) FILTER (WHERE referencia_nacional),
                              count(DISTINCT sec_ejec) FILTER (WHERE ejecutora_mixta),
                              count(DISTINCT sec_ejec) FILTER (WHERE verificar_procedencia),
                              count(*) FILTER (WHERE referencia_nacional IS NULL OR ejecutora_mixta IS NULL
                                               OR verificar_procedencia IS NULL OR alcance_revisado_dueno IS NULL),
                              count(*) FILTER (WHERE nivel_gobierno <> 'E' AND (referencia_nacional OR ejecutora_mixta
                                                                                 OR verificar_procedencia))
                       FROM ue""").fetchone()
    assert r == (2, 25, 35, 0, 0)   # E3: + 3 mixtas; + COAR Lima y CENFOTUR con verificar_procedencia
    inmp = con.execute("SELECT DISTINCT alcance_ejecutora, ambito_id FROM ue WHERE sec_ejec = '127'").fetchall()
    assert inmp == [("lima_metropolitana", "LIMA_METROPOLITANA")]


def test_vistas_del_motor_traen_marcas_y_actividad(con):
    # P3: hasta reconstruir, la fact v1.4.0 no trae cuenta_en_ambito (en el 15 equivale a cuenta_en_lima)
    p3 = "cuenta_en_ambito" in {x[0] for x in con.execute("DESCRIBE fact").fetchall()}
    con.execute("CREATE OR REPLACE VIEW fact_gasto_territorial AS SELECT * "
                + ("" if p3 else ", cuenta_en_lima AS cuenta_en_ambito") + " FROM fact")
    con.execute((DATOS / "vistas_gasto.sql").read_text(encoding="utf-8"))
    tem = {r[0] for r in con.execute("DESCRIBE v_gasto_tematico").fetchall()}
    cons = {r[0] for r in con.execute("DESCRIBE v_gasto_consolidado").fetchall()}
    assert {"actividad_accion_obra", "fuente_financiamiento", "rubro", "clasificador_gasto", "cuenta_en_lima",
            "referencia_nacional"} <= tem
    assert {"cuenta_en_lima", "referencia_nacional", "ejecutora_mixta"} <= cons


# ---------------- H3 (auditoría de la pieza A): las bases se eligen por huella, nunca con un glob
def test_filtrar_bases_descarta_huella_vieja_y_falla_con_duplicados(tmp_path):
    h = G.HUELLA_SQL
    for n in (f"gasto_base_2025_aaaaaaaaaaaa_{h}", "gasto_base_2025_aaaaaaaaaaaa_6391c407",   # base vieja, mismo año
              f"gasto_base_2024_bbbbbbbbbbbb_{h}", f"gasto_base_2024_cccccccccccc_{h}"):    # otro CSV del mismo año
        (tmp_path / f"{n}.parquet").write_bytes(b"")
    todas = sorted(tmp_path.glob("gasto_base_*.parquet"))
    assert len([p for p in todas if "_2025_" in p.name]) == 2       # un glob sumaría 2025 dos veces
    vig = G.filtrar_bases(todas, h, {2025: "aaaaaaaaaaaa", 2024: "bbbbbbbbbbbb"})
    assert [p.name for p in vig] == [f"gasto_base_2024_bbbbbbbbbbbb_{h}.parquet", f"gasto_base_2025_aaaaaaaaaaaa_{h}.parquet"]
    with pytest.raises(PapError, match="Más de una base"):
        G.filtrar_bases(todas, h)                                    # sin huellas de CSV: 2024 queda repetido


def test_bases_vigentes_una_por_anio_y_lectores_sin_glob():
    try:
        vig = G.bases_vigentes(Rutas(RAIZ_REAL))
    except PapError as e:
        pytest.skip(f"sin base vigente: {e}")
    anios = [int(p.stem.split("_")[2]) for p in vig]
    assert anios == sorted(set(anios)) and all(p.stem.endswith(G.HUELLA_SQL) for p in vig)
    # ningún lector de las pruebas ni del código vivo lee la base con un glob
    for f in [*(RAIZ_REAL / "tests").glob("test_*.py"),
              *(RAIZ_REAL / "src" / "pap").rglob("*.py")]:
        if f.name == "test_gasto_pieza_a.py":  # esta prueba usa un glob a propósito sobre una carpeta temporal
            continue
        txt = f.read_text(encoding="utf-8")
        assert "gasto_base_*.parquet'" not in txt and 'glob("gasto_base_' not in txt.replace(
            'carpeta_base(rutas).glob("gasto_base_*.parquet")', ""), f.name


def test_cuenta_en_lima_fila_a_fila(con):
    """H5: cuenta_en_lima = dpto 15 ∧ alcance ≠ nacional ∧ ¬referencia_nacional ∧ ¬obra_sede_nacional (E3), sin depender
    de la agregación."""
    assert con.execute("""SELECT count(*) FROM fact WHERE cuenta_en_lima IS DISTINCT FROM
                          (departamento_atribucion = '15' AND alcance_ejecutora <> 'nacional'
                           AND NOT referencia_nacional AND NOT obra_sede_nacional)""").fetchone()[0] == 0
