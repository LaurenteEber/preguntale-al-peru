"""P3 – Lima en tres ámbitos (decisiones L1-L9 del dueño del 9/10/2026; L6, H-A2, H-A3, H-A4, H-A5): un solo mecanismo
de sesgo de sede para los dpto 15 y 07 (cuenta_en_ambito), GR Lima → Lima Región (Ley 31140), GR Callao con meta 15 →
07, vista v_gasto_por_ambito. Pruebas unitarias con datos sintéticos de las funciones de gasto.py, de los curados y de
las tablas construidas (se saltan si la fact publicada es anterior a P3). Evidencia:
curados/generadores/p3_gasto/."""
import json
import subprocess
import sys

import duckdb
import pytest
import yaml

from pap.capa0 import gasto as G
from pap.capa0 import guardia_gasto as gu
from pap.config import Rutas
from pap.errores import PapError

from conftest import RAIZ_REAL

DATOS = RAIZ_REAL / "curados" / "capa0"
DIM = RAIZ_REAL / "biblioteca" / "dimensiones"
P3 = RAIZ_REAL / "curados" / "generadores" / "p3_gasto"
YAML = yaml.safe_load((DATOS / "ejecutoras_alcance.yaml").read_text(encoding="utf-8"))
POR_SEC = {e["sec_ejec"]: e for e in YAML}
SEDE = yaml.safe_load((DATOS / "obras_sede_nacional.yaml").read_text(encoding="utf-8"))


# ======================= funciones de alcance (datos sintéticos)
@pytest.mark.parametrize("dpto, alcance, refnac, obra, esperado", [
    ("15", "lima_metropolitana", False, False, True),
    ("15", "nacional", False, False, False),            # GA-01
    ("15", "no_aplica", True, False, False),            # referencia nacional (con sus obras)
    ("15", "no_aplica", False, True, False),            # obra de sede o función nacional (E3)
    ("15", "sin_clasificar", False, False, True),
    ("07", "callao", False, False, True),               # L6: UNAC, fiscalías y policía del Callao
    ("07", "nacional", False, False, False),            # L6: Marina, APN, IMARPE, ENAMM, SUNAT
    ("07", "no_aplica", False, True, False),            # H-A5: obra nacional en el Callao
    ("07", "no_aplica", False, False, True),            # GR Callao, municipalidades
    ("08", "no_aplica", False, False, False),           # fuera del 15 y el 07 no hay cifra de ámbito
    ("00", "no_aplica", False, False, False),
])
def test_cuenta_en_ambito_python_y_sql_coinciden(dpto, alcance, refnac, obra, esperado):
    assert G.cuenta_en_ambito(dpto, alcance, refnac, obra) is esperado
    sql = G.sql_cuenta_en_ambito("d", "a", "r", "o")
    r = duckdb.execute(f"SELECT {sql} FROM (SELECT ?::VARCHAR d, ?::VARCHAR a, ?::BOOLEAN r, ?::BOOLEAN o)",
                       [dpto, alcance, refnac, obra]).fetchone()[0]
    assert r is esperado


@pytest.mark.parametrize("nivel, meta, ng, a15, a07, act, lista, esperado", [
    ("departamento_meta", "15", "E", "nacional", "callao", "1", None, "nacional"),
    ("departamento_meta", "15", "E", None, None, "1", None, "sin_clasificar"),
    ("departamento_meta", "07", "E", "nacional", "callao", "1", None, "callao"),     # el alcance depende de la meta
    ("departamento_meta", "07", "E", "nacional", None, "1", None, "sin_clasificar"),
    ("departamento_meta", "07", "R", None, None, "1", None, "no_aplica"),
    ("departamento_meta", "12", "E", "nacional", "callao", "1", None, "no_aplica"),
    ("distrito_inversion", "07", "E", "nacional", "nacional", "1", None, "no_aplica"),  # obras: obras_sede_nacional
    # auditoría de P3: la aviación policial de DIREFIN (mixta que cuenta) se separa por actividad como nacional
    ("departamento_meta", "07", "E", "nacional", "callao", "5001193", "5001193,5004067", "nacional"),
    ("departamento_meta", "07", "E", "nacional", "callao", "5000276", "5001193,5004067", "callao"),
    ("departamento_meta", "15", "E", "nacional", "callao", "5001193", "5001193,5004067", "nacional"),
    ("departamento_meta", "07", "E", "lima_callao", "lima_callao", "1", None, "lima_callao"),   # ATU (H-P3-3)
])
def test_alcance_fila_por_ejecutora_y_meta(nivel, meta, ng, a15, a07, act, lista, esperado):
    sql = G.sql_alcance_fila("n", "m", "g", "a", "b", "x", "l")
    r = duckdb.execute(f"""SELECT {sql} FROM (SELECT ?::VARCHAR n, ?::VARCHAR m, ?::VARCHAR g, ?::VARCHAR a, ?::VARCHAR b,
                                                     ?::VARCHAR x, ?::VARCHAR l)""",
                       [nivel, meta, ng, a15, a07, act, lista]).fetchone()[0]
    assert r == esperado


@pytest.mark.parametrize("pliego, ng, esperado", [
    ("GOBIERNO REGIONAL DEL DEPARTAMENTO DE LIMA", "R", "LIMA_REGION"),
    ("MUNICIPALIDAD METROPOLITANA DE LIMA", "R", "LIMA_METROPOLITANA"),
    ("GOBIERNO REGIONAL DE LA PROVINCIA CONSTITUCIONAL DEL CALLAO", "R", "CALLAO"),
    ("GOBIERNO REGIONAL DEL DEPARTAMENTO DE JUNIN", "R", None),
    ("GOBIERNO REGIONAL DEL DEPARTAMENTO DE LIMA", "E", None),
])
def test_ambito_pliego_regional(pliego, ng, esperado):
    r = duckdb.execute(f"SELECT {G.sql_ambito_pliego_regional('g', 'p')} FROM (SELECT ?::VARCHAR g, ?::VARCHAR p)",
                       [ng, pliego]).fetchone()[0]
    assert r == esperado


@pytest.mark.parametrize("pliego, nivel, ubigeo, ambito_ue, ubigeo_final, dpto", [
    # H-A2 (Ley 31140): el GR Lima no sale de Lima Región
    ("LIMA_REGION", "distrito_inversion", "150101", None, "A-LIMA_REGION", "15"),       # CUI 2649748
    ("LIMA_REGION", "departamento_inversion", "150000", None, "A-LIMA_REGION", "15"),   # CUI 2288164
    ("LIMA_REGION", "departamento_meta", "120000", "LIMA_REGION", "120000", "12"),   # H-P3-6: se queda en Junín
    ("LIMA_REGION", "departamento_meta", "150000", "LIMA_REGION", "A-LIMA_REGION", "15"),
    ("LIMA_REGION", "distrito_inversion", "150201", None, "150201", "15"),
    ("LIMA_REGION", "nacional_no_territorializable", "000000", None, "000000", "00"),   # deuda: como todo GORE
    # H-08: el GR Callao con meta 15 va al 07
    ("CALLAO", "departamento_meta", "150000", None, "070000", "07"),
    ("CALLAO", "distrito_inversion", "070101", None, "070101", "07"),
    # simétrica para el pliego regional de la MML
    ("LIMA_METROPOLITANA", "distrito_inversion", "150201", None, "A-LIMA_METROPOLITANA", "15"),
    ("LIMA_METROPOLITANA", "departamento_meta", "150000", "LIMA_METROPOLITANA", "A-LIMA_METROPOLITANA", "15"),
    # resto: sin cambios
    (None, "departamento_meta", "150000", "LIMA_METROPOLITANA", "A-LIMA_METROPOLITANA", "15"),   # DIRIS, USE
    (None, "departamento_meta", "150000", None, "150000", "15"),                                  # INPE ORL
    (None, "distrito_inversion", "150101", None, "150101", "15"),
    (None, "departamento_meta", "070000", None, "070000", "07"),
    ("CALLAO", "departamento_meta", "070000", None, "070000", "07"),
])
def test_reatribucion_de_pliegos_regionales(pliego, nivel, ubigeo, ambito_ue, ubigeo_final, dpto):
    ub = G.sql_ubigeo_base_regional("u", "p")
    am = G.sql_ambito_id("n", "u", "a", "p", "al")
    r = duckdb.execute(f"""SELECT CASE WHEN amb IS NOT NULL THEN 'A-' || amb ELSE ub END, substr(ub, 1, 2) FROM (
                             SELECT {ub} AS ub, {am} AS amb
                             FROM (SELECT ?::VARCHAR p, ?::VARCHAR n, ?::VARCHAR u, ?::VARCHAR a, 'no_aplica' al))""",
                       [pliego, nivel, ubigeo, ambito_ue]).fetchone()
    assert r == (ubigeo_final, dpto)


def test_atu_con_meta_07_va_a_lima_y_callao_sin_separar():
    """H-P3-3: el mismo trato que con meta 15 (A-AREA_METROPOLITANA_LIMA_CALLAO), sin cambiar el departamento."""
    am = G.sql_ambito_id("n", "u", "a", "p", "al")
    r = duckdb.execute(f"SELECT {am} FROM (SELECT 'departamento_meta' n, '070000' u, NULL a, NULL p, 'lima_callao' al)"
                       ).fetchone()[0]
    assert r == "AREA_METROPOLITANA_LIMA_CALLAO"


def test_sql_fact_sintetica():
    """H-P3-7: la SQL de construcción (gasto.sql_fact) sobre `atribuida`, `obras_sede` y `corte` sintéticas."""
    c = duckdb.connect()
    cols = ("anio INT, mes INT, sec_ejec VARCHAR, nivel_gobierno VARCHAR, departamento_meta VARCHAR, programa_ppto VARCHAR, "
            "producto_proyecto VARCHAR, actividad_accion_obra VARCHAR, funcion VARCHAR, division_funcional VARCHAR, "
            "grupo_funcional VARCHAR, categoria_gasto VARCHAR, generica VARCHAR, clasificador_gasto VARCHAR, "
            "nivel_clasificador VARCHAR, fuente_financiamiento VARCHAR, rubro VARCHAR, tipo_act_proy VARCHAR, "
            "categoria_transferencia VARCHAR, es_transferencia BOOLEAN, es_transferencia_intergub BOOLEAN, "
            "bloque_consolidado VARCHAR, pia DECIMAL(18,2), pim DECIMAL(18,2), devengado DECIMAL(18,2), "
            "nivel_atribucion VARCHAR, inv_ubigeo VARCHAR, ubigeo_sede VARCHAR, ambito_ue VARCHAR, alcance_ejecutora VARCHAR, "
            "referencia_nacional BOOLEAN, verificar_procedencia BOOLEAN, ejecutora_mixta BOOLEAN, "
            "alcance_ejecutora_callao VARCHAR, ejecutora_mixta_callao BOOLEAN, verificar_procedencia_callao BOOLEAN, "
            "actividades_nacionales_callao VARCHAR, ambito_pliego VARCHAR, consistencia_meta VARCHAR, "
            "metodo_ubicacion VARCHAR, inv_redirigido_origen BOOLEAN")
    c.execute(f"CREATE TABLE atribuida ({cols})")
    filas = [  # sec, ng, meta, proyecto, actividad, tipo, nivel, inv_ubigeo, ambito_ue, a15, a07, mixta07, lista, pliego
        ("471", "E", "07", "3999999", "1", "ACTIVIDAD", "departamento_meta", None, None, "nacional", "nacional", False, None, None),
        ("1340", "E", "07", "2392678", "2", "PROYECTO", "distrito_inversion", "070101", None, "nacional", "callao", False, None, None),
        ("900", "R", "15", "2649748", "3", "PROYECTO", "distrito_inversion", "150101", "LIMA_REGION", None, None, False, None, "LIMA_REGION"),
        ("900", "R", "15", "2288164", "4", "PROYECTO", "departamento_inversion", "150000", "LIMA_REGION", None, None, False, None, "LIMA_REGION"),
        ("901", "R", "15", "3999999", "5", "ACTIVIDAD", "departamento_meta", None, None, None, None, False, None, "CALLAO"),
        ("1717", "E", "07", "3999999", "6", "ACTIVIDAD", "departamento_meta", None, "AREA_METROPOLITANA_LIMA_CALLAO", "lima_callao", "lima_callao", False, None, None),
        ("26", "E", "07", "3999999", "5001193", "ACTIVIDAD", "departamento_meta", None, None, "nacional", "callao", True, "5001193,5004067", None),
        ("26", "E", "07", "3999999", "5000276", "ACTIVIDAD", "departamento_meta", None, None, "nacional", "callao", True, "5001193,5004067", None),
        ("900", "R", "12", "3999999", "7", "ACTIVIDAD", "departamento_meta", None, "LIMA_REGION", None, None, False, None, "LIMA_REGION"),
    ]
    for sec, ng, meta, pp, act, tipo, niv, inv, amb, a15, a07, m07, lista, pl in filas:
        c.execute("""INSERT INTO atribuida VALUES (2025, 12, ?, ?, ?, '9001', ?, ?, 'F', 'D', 'G', '5', '3', '2.3', 'generica',
                     '1', '00', ?, NULL, false, false, 'gasto_final', 0, 10, 10, ?, ?, NULL, ?, ?, false, false, false,
                     ?, ?, false, ?, ?, NULL, NULL, false)""",
                  [sec, ng, meta, pp, act, tipo, niv, inv, amb, a15, a07, m07, lista, pl])
    c.execute("CREATE TABLE obras_sede AS SELECT '2392678' AS cui, '1340' AS sec_ejec, 'sede_institucional' AS criterio")
    c.execute("CREATE TABLE corte AS SELECT 2025 AS anio, 12 AS mes_max, true AS es_anio_cerrado")
    c.execute(G.sql_fact())
    r = {(x[0], x[1]): x[2:] for x in c.execute("""
        SELECT sec_ejec, actividad_accion_obra, ubigeo_atribucion, departamento_atribucion, obra_sede_nacional,
               cuenta_en_ambito, cuenta_en_lima, alcance_ejecutora, ejecutora_mixta FROM fact""").fetchall()}
    assert r[("471", "1")] == ("070000", "07", False, False, False, "nacional", False)             # Marina
    assert r[("1340", "2")] == ("070101", "07", True, False, False, "no_aplica", False)            # obra SUNAT (H-A5)
    assert r[("900", "3")] == ("A-LIMA_REGION", "15", False, True, True, "no_aplica", False)       # GR Lima en 1501
    assert r[("900", "4")] == ("A-LIMA_REGION", "15", False, True, True, "no_aplica", False)       # GR Lima en 150000
    assert r[("901", "5")] == ("070000", "07", False, True, False, "no_aplica", False)             # GR Callao meta 15
    assert r[("1717", "6")] == ("A-AREA_METROPOLITANA_LIMA_CALLAO", "07", False, True, False, "lima_callao", False)
    assert r[("26", "5001193")] == ("070000", "07", False, False, False, "nacional", True)         # aviación DIREFIN
    assert r[("26", "5000276")] == ("070000", "07", False, True, False, "callao", True)            # policía del Callao
    assert r[("900", "7")] == ("120000", "12", False, False, False, "no_aplica", False)            # H-P3-6


def _fact_sintetica(c):
    """Fact mínima con las columnas que leen las vistas del motor."""
    filas = [  # (ubigeo, dpto, cuenta_en_ambito, referencia_nacional, devengado, alcance)
        ("150101", "15", True, False, 100, "no_aplica"),         # LM por ubigeo
        ("A-LIMA_METROPOLITANA", "15", True, False, 50, "lima_metropolitana"),
        ("150101", "15", False, False, 30, "no_aplica"),         # obra de sede en 1501: NO es LM (H-A4)
        ("A-LIMA_REGION", "15", True, False, 20, "no_aplica"),
        ("150201", "15", True, False, 10, "no_aplica"),
        ("150000", "15", True, False, 5, "lima_departamento"),
        ("A-AREA_METROPOLITANA_LIMA_CALLAO", "15", True, False, 4, "lima_callao"),
        ("150000", "15", False, True, 7, "no_aplica"),           # referencia nacional
        ("150000", "15", False, False, 300, "nacional"),          # sede nacional
        ("070000", "07", True, False, 60, "callao"),
        ("070000", "07", False, False, 200, "nacional"),          # Marina
        ("A-AREA_METROPOLITANA_LIMA_CALLAO", "07", True, False, 3, "lima_callao"),   # ATU con meta 07 (H-P3-3)
        ("080000", "08", False, False, 9, "no_aplica"),
    ]
    c.execute("""CREATE TABLE fact_gasto_territorial (anio INT, mes INT, nivel_atribucion VARCHAR, ubigeo_atribucion VARCHAR,
                 departamento_atribucion VARCHAR, ambito_id VARCHAR, alcance_ejecutora VARCHAR, cuenta_en_lima BOOLEAN,
                 cuenta_en_ambito BOOLEAN, referencia_nacional BOOLEAN, ejecutora_mixta BOOLEAN, obra_sede_nacional BOOLEAN,
                 nivel_gobierno VARCHAR, departamento_meta VARCHAR, funcion VARCHAR, division_funcional VARCHAR,
                 programa_ppto VARCHAR, sec_ejec VARCHAR, producto_proyecto VARCHAR, categoria_transferencia VARCHAR,
                 es_transferencia BOOLEAN, es_transferencia_intergub BOOLEAN, bloque_consolidado VARCHAR,
                 fecha_corte_datos VARCHAR, es_anio_cerrado BOOLEAN, pim DECIMAL(18,2), devengado DECIMAL(18,2))""")
    for u, d, ca, rn, dev, al in filas:
        c.execute("""INSERT INTO fact_gasto_territorial VALUES (2025, 12, 'departamento_meta', ?, ?, NULL, ?, ?, ?, ?,
                     false, false, 'E', ?, 'F', 'D', '9001', '1', '1', NULL, false, false, 'gasto_final', '2025-12', true,
                     ?, ?)""", [u, d, al, ca and d == "15", ca, rn, d, dev, dev])
    c.execute((DATOS / "vistas_gasto.sql").read_text(encoding="utf-8"))


def test_vista_por_ambito_filtra_cuenta_en_ambito_y_separa_lineas():
    c = duckdb.connect()
    _fact_sintetica(c)
    r = dict(c.execute("SELECT ambito_gasto, sum(devengado)::INT FROM v_gasto_por_ambito GROUP BY 1").fetchall())
    assert r == {"LIMA_METROPOLITANA": 150, "LIMA_REGION": 30, "CALLAO": 60, "NO_ASIGNABLE_DPTO_LIMA": 5,
                 "NO_ASIGNABLE_LIMA_CALLAO": 7, "REFERENCIA_NACIONAL": 7, "SEDE_NACIONAL": 530}
    # cada sol del 15 y el 07 cae en una sola línea; el 08 no está
    assert c.execute("SELECT sum(devengado)::INT FROM v_gasto_por_ambito").fetchone()[0] == 789
    # H-P3-1: aviso obligatorio en la cifra del Callao (y solo en ella)
    av = dict(c.execute("SELECT ambito_gasto, any_value(aviso) FROM v_gasto_por_ambito GROUP BY 1").fetchall())
    assert "≈ 15-17 %" in av["CALLAO"] and "2473375" in av["CALLAO"] and "2407158" in av["CALLAO"]
    assert all(v is None for k, v in av.items() if k != "CALLAO")
    lineas = dict(c.execute("SELECT ambito_gasto, any_value(linea) FROM v_gasto_por_ambito GROUP BY 1").fetchall())
    assert {k for k, v in lineas.items() if v == "cifra_ambito"} == {"LIMA_METROPOLITANA", "LIMA_REGION", "CALLAO"}
    # la columna ambito_gasto llega a v_gasto_tematico (y por ella a gasto_tema) y a v_gasto_consolidado
    assert c.execute("SELECT count(*) FROM v_gasto_tematico WHERE ambito_gasto IS NULL").fetchone()[0] == 1
    assert "ambito_gasto" in {x[0] for x in c.execute("DESCRIBE v_gasto_consolidado").fetchall()}


def test_lector_rechaza_alcance_callao_invalido(tmp_path):
    def raiz(entradas):
        (tmp_path / "curados" / "capa0").mkdir(parents=True, exist_ok=True)
        (tmp_path / "curados" / "capa0" / "ejecutoras_alcance.yaml").write_text(
            yaml.safe_dump(entradas, allow_unicode=True), encoding="utf-8")
        return Rutas(tmp_path)
    ok = G._alcance_ejecutoras(Rutas(RAIZ_REAL))
    assert ok.loc[ok.sec_ejec == "471", "alcance_callao"].item() == "nacional"
    malo = [dict(e) for e in YAML]
    malo[0] = {**malo[0], "alcance_callao": {**malo[0]["alcance_callao"], "alcance": "lima_metropolitana"}}
    with pytest.raises(PapError, match="alcance_callao desconocido"):
        G._alcance_ejecutoras(raiz(malo))
    malo[0] = {**malo[0], "alcance_callao": {**YAML[0]["alcance_callao"], "actividades_nacionales": ["50011a"]}}
    with pytest.raises(PapError, match="actividades_nacionales mal formado"):
        G._alcance_ejecutoras(raiz(malo))
    malo[0] = {**malo[0], "alcance_callao": {**YAML[0]["alcance_callao"], "criterio": " "}}
    with pytest.raises(PapError, match="sin criterio"):
        G._alcance_ejecutoras(raiz(malo))
    malo[0] = {**malo[0], "alcance_callao": {**YAML[0]["alcance_callao"], "mixta": None}}
    with pytest.raises(PapError, match="mixta debe ser"):
        G._alcance_ejecutoras(raiz(malo))


# ======================= curados
def test_alcance_callao_decisiones_l6_y_ha3():
    cal = {s: e["alcance_callao"] for s, e in POR_SEC.items() if "alcance_callao" in e}
    assert len(cal) == 67
    # nacional solo donde no hay servicio directo a residentes del Callao (H-A3)
    for s in ("471", "1205", "193", "1123", "1273"):   # Marina, APN, IMARPE, ENAMM, SUNAT-Aduanas
        assert cal[s]["alcance"] == "nacional" and cal[s]["revisado_dueno"] and cal[s]["paso"] == "decision_L6_HA3", s
    for s in ("200", "26"):                              # MP-Gerencia General, DIREFIN PNP: mixtas que cuentan
        assert cal[s]["alcance"] == "callao" and cal[s]["mixta"] and cal[s]["revisado_dueno"], s
    assert cal["12"]["alcance"] == "callao" and cal["12"]["mixta"] and cal["12"]["verificar_procedencia"]  # PJ-GG
    for s in ("107", "1467"):                            # UNAC, CSJ Callao
        assert cal[s]["alcance"] == "callao" and not cal[s]["mixta"], s
    assert cal["107"]["verificar_procedencia"]            # auditoría de P3: UNAC sin dato de residencia
    # auditoría de P3: ATU → Lima y Callao sin separar (H-P3-3); sin servicio directo → nacional (H-P3-4); aviación DIREFIN
    assert cal["1717"]["alcance"] == "lima_callao"
    assert cal["26"]["actividades_nacionales"] == ["5001193", "5004067"]
    assert {s for s, b in cal.items() if b["alcance"] == "nacional"} == {
        "471", "1205", "193", "1123", "1273", "1588", "194", "1520", "42", "1072", "470", "472", "1343",
        "196", "1698", "1745", "1267"}
    assert all((b["decision"] is not None) == b["revisado_dueno"] for b in cal.values())
    # el alcance de la meta 15 no cambia (GA-01, decisiones del 7 y 8/10): mismas entradas que la v3 más 3 sin meta 15
    nuevas = [e for e in YAML if e["base_alcance"]["paso"] == "agregada_p3_sin_meta_lima"]
    assert {e["sec_ejec"] for e in nuevas} == {"1467", "480", "479"} and not any(e["revisado_dueno"] for e in nuevas)


def test_obras_del_callao():
    o = [x for x in SEDE["obras"] if x["origen"] == "callao_p3"]
    assert len(o) == 12 and SEDE["version"] == "1.2.0" and all(x["departamento"] == "07" for x in o)
    assert round(sum(x["devengado_2023_2025_millones"] for x in o), 1) == 58.6
    import re
    for x in o:
        assert not re.search(r"I\.E\.|INSTITUCI[OÓ]N EDUCATIVA|COLEGIO|HOSPITAL|COMISAR|UNIVERSIDAD", x["nombre_inversion"].upper())
    rev = (P3 / "obras_callao_revision.csv").read_text(encoding="utf-8")
    import csv as _csv
    dec = {r["cui"]: r["decision"] for r in _csv.DictReader((P3 / "obras_callao_revision.csv").open(encoding="utf-8"))}
    assert dec["2473375"] == dec["2407158"] == "queda_con_rotulo" and dec["2145423"] == "revisar"   # auditoría de P3
    for cui in ("2473375", "2407158", "2145423"):   # siguen contando en el Callao
        assert f"{cui}," in rev and cui not in {x["cui"] for x in SEDE["obras"]}


def test_curados_reproducibles(tmp_path):
    """generar_p3.py corre los generadores de E3 sin cambios y reproduce los dos YAML vigentes byte a byte."""
    a, o = tmp_path / "a.yaml", tmp_path / "o.yaml"
    subprocess.run([sys.executable, str(P3 / "generar_p3.py"), str(RAIZ_REAL), "--salida-alcance", str(a),
                    "--salida-obras", str(o)], check=True, capture_output=True)
    assert a.read_bytes() == (DATOS / "ejecutoras_alcance.yaml").read_bytes()
    assert o.read_bytes() == (DATOS / "obras_sede_nacional.yaml").read_bytes()


def test_guardia_cubre_la_vista_por_ambito():
    gu.verificar_consulta("SELECT anio, ambito_gasto, sum(devengado) FROM v_gasto_por_ambito "
                          "WHERE linea = 'cifra_ambito' GROUP BY ALL")
    with pytest.raises(gu.GuardiaGasto):
        gu.verificar_consulta("SELECT * FROM v_gasto_por_ambito, v_gasto_fondos_por_identificar")
    with pytest.raises(gu.GuardiaGasto):
        gu.verificar_consulta("SELECT * FROM gasto_tema('cpt_grupo_expan') g, v_gasto_por_ambito v")
    # el gasto de un tema por ámbito sale de gasto_tema() (L5: ex-PAN por LM, LR y Callao)
    gu.verificar_consulta("SELECT ambito_gasto, sum(devengado) FROM gasto_tema('cpt_grupo_expan') GROUP BY 1")
    # G7 (auditoría de P3, H-P3-2): el 15 y el 07 sin ambito_gasto ni cuenta_en_ambito se rechazan
    for q in ("SELECT sum(devengado) FROM gasto_tema('cpt_grupo_expan') WHERE departamento_atribucion = '07'",
              "SELECT sum(devengado) FROM v_gasto_tematico WHERE ubigeo_atribucion LIKE '1501%'",
              "SELECT sum(gasto_final_devengado) FROM v_gasto_consolidado WHERE departamento_meta IN ('15', '07')",
              "SELECT sum(devengado) FROM v_gasto_por_ambito WHERE departamento_atribucion = '07'"):
        with pytest.raises(gu.GuardiaGasto, match="por ámbito"):
            gu.verificar_consulta(q)
    gu.verificar_consulta("SELECT sum(devengado) FROM v_gasto_tematico WHERE departamento_atribucion = '07' "
                          "AND cuenta_en_ambito")
    gu.verificar_consulta("SELECT sum(devengado) FROM v_gasto_tematico WHERE departamento_atribucion = '08'")


# ======================= tablas construidas (P3)
@pytest.fixture(scope="module")
def con():
    man_p = DIM / "manifiesto_s3_gasto.json"
    if not man_p.exists():
        pytest.skip("gasto no construido")
    man = json.loads(man_p.read_text(encoding="utf-8"))
    if "cuenta_en_ambito" not in man["tablas"]["fact_gasto_territorial"]["columnas"]:
        pytest.skip("la fact publicada es anterior a P3 (reconstruir con `pap construir gasto`)")
    c = duckdb.connect()
    c.execute("SET enable_progress_bar=false; SET memory_limit='2GB'; SET threads=2")
    c.execute(f"CREATE VIEW fact AS SELECT * FROM '{DIM / 'fact_gasto_territorial.parquet'}'")
    c.execute("CREATE VIEW fact_gasto_territorial AS SELECT * FROM fact")
    c.execute(f"CREATE VIEW ue AS SELECT * FROM '{DIM / 'dim_unidad_ejecutora.parquet'}'")
    for t in ("dim_tema_gasto", "rel_concepto_grupo", "rel_concepto_nodo", "rel_programa_social_ejecutora",
              "rel_programa_social_linea_aparte"):
        c.execute(f"CREATE VIEW {t} AS SELECT * FROM '{DIM / (t + '.parquet')}'")
    c.execute((DATOS / "vistas_gasto.sql").read_text(encoding="utf-8"))
    c.execute((DATOS / "vistas_gasto_temas.sql").read_text(encoding="utf-8"))
    yield c
    c.close()


def test_pruebas_publicadas_p3(con):
    pr = {p["id"]: p for p in json.loads((DIM / "pruebas_s3_gasto.json").read_text(encoding="utf-8"))}
    for i in ("G-01", "G-12", "G-26", "G-27", "G-37", "G-39", "G-40", "G-41"):
        assert pr[i]["ok"] and pr[i]["bloqueante"], i
    assert pr["G-42"]["ok"]   # canasta comparable del Callao (H-P3-1), no bloqueante


def test_gr_lima_siempre_en_lima_region(con):
    """H-A2 (Ley 31140): ninguna fila del pliego GR Lima atribuida al dpto 15 fuera de Lima Región (H-P3-6: el gasto con
    meta en otro departamento, la deuda y lo multidepartamental se quedan donde están)."""
    r = con.execute("""
        SELECT count(*) FILTER (WHERE f.departamento_atribucion = '15' AND NOT (f.ubigeo_atribucion = 'A-LIMA_REGION'
                   OR (f.ubigeo_atribucion LIKE '15%' AND f.ubigeo_atribucion NOT LIKE '1501%'
                       AND f.ubigeo_atribucion <> '150000'))),
               list(DISTINCT f.ubigeo_atribucion) FILTER (WHERE lpad(f.producto_proyecto, 7, '0') IN ('2649748', '2288164'))
        FROM fact f JOIN ue u USING (anio, sec_ejec)
        WHERE f.nivel_gobierno = 'R' AND u.pliego_nombre LIKE 'GOBIERNO REGIONAL%LIMA%'
          AND u.pliego_nombre NOT LIKE '%METROPOLITANA%'""").fetchone()
    assert r == (0, ["A-LIMA_REGION"])


def test_gr_callao_nunca_en_el_15(con):
    """H-08: ninguna fila de un pliego GR Callao con departamento de atribución 15 (9,2 millones de 2025 → 07)."""
    r = con.execute("""
        SELECT count(*) FILTER (WHERE f.departamento_atribucion = '15'),
               count(*) FILTER (WHERE f.departamento_atribucion NOT IN ('07', '00')),
               round(sum(f.devengado) FILTER (WHERE f.departamento_meta = '15') / 1e6, 2)
        FROM fact f JOIN ue u USING (anio, sec_ejec)
        WHERE f.nivel_gobierno = 'R' AND u.pliego_nombre LIKE 'GOBIERNO REGIONAL%CALLAO%'""").fetchone()
    assert r == (0, 0, 9.22)


def test_cuenta_en_lima_es_alias_en_el_15(con):
    r = con.execute("""SELECT count(*) FILTER (WHERE cuenta_en_lima IS DISTINCT FROM
                                                (cuenta_en_ambito AND departamento_atribucion = '15')),
                              count(*) FILTER (WHERE cuenta_en_ambito AND departamento_atribucion NOT IN ('15', '07'))
                       FROM fact""").fetchone()
    assert r == (0, 0)


def test_cifras_por_ambito(con):
    """Simulación de P3 sobre la fact v1.4.0 (p3_gasto/efecto_por_ambito.csv), gasto final en millones."""
    r = {(a, m): float(v) for a, m, v in con.execute(
        "SELECT anio, ambito_gasto, round(sum(devengado)/1e6, 1) FROM v_gasto_por_ambito GROUP BY 1, 2").fetchall()}
    esperado = {(2023, "LIMA_METROPOLITANA"): 16998.3, (2024, "LIMA_METROPOLITANA"): 20771.7,
                (2025, "LIMA_METROPOLITANA"): 22106.2, (2023, "LIMA_REGION"): 3679.3, (2024, "LIMA_REGION"): 4567.6,
                (2025, "LIMA_REGION"): 4459.5, (2023, "CALLAO"): 3006.4, (2024, "CALLAO"): 3496.3,
                (2025, "CALLAO"): 3514.1, (2023, "NO_ASIGNABLE_LIMA_CALLAO"): 1005.7,
                (2024, "NO_ASIGNABLE_LIMA_CALLAO"): 1242.5, (2025, "NO_ASIGNABLE_LIMA_CALLAO"): 1180.7}
    assert {k: r[k] for k in esperado} == esperado
    # controles nacionales: no cambian (ronda 2, 7/10/2026)
    for tid, s in (("cpt_grupo_expan", [2179, 2429, 2456]), ("cpt_grupo_opcion_c", [2056, 2327, 2366])):
        assert [x[1] for x in con.execute(f"SELECT anio, round(sum(devengado)/1e6) FROM gasto_tema('{tid}') "
                                          "GROUP BY 1 ORDER BY 1").fetchall()] == s
    # ex-PAN por ámbito (L5): Callao 33,6 / 32,4 / 22,6 (CENARES cuenta, rotulado)
    ca = [x[1] for x in con.execute("""SELECT anio, round(sum(devengado)/1e6, 1) FROM gasto_tema('cpt_grupo_expan')
                                       WHERE ambito_gasto = 'CALLAO' GROUP BY 1 ORDER BY 1""").fetchall()]
    assert ca == [33.6, 32.4, 22.6]
