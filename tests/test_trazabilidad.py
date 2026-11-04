"""Pieza C de las decisiones del gasto (rondas 1-2, dueño 7/10/2026): capa de trazabilidad, dim_tema_gasto v1.2, glosario
v2 y guardia de alcances. Pruebas unitarias del módulo (sin reconstruir) y pruebas sobre las tablas publicadas en
biblioteca/dimensiones/ (se omiten si el gasto publicado es anterior a la pieza C). Evidencia:
03_auditoria/ola0/decisiones_gasto/implementacion/pieza_c/."""
import copy
import json

import duckdb
import pandas as pd
import pytest

from pap.capa0 import gasto as G
from pap.capa0 import guardia_gasto as gu
from pap.capa0 import salida
from pap.capa0 import trazabilidad as T
from pap.config import Rutas
from pap.errores import PapError

from conftest import RAIZ_REAL

DIM = RAIZ_REAL / "biblioteca" / "dimensiones"
DATOS = RAIZ_REAL / "curados" / "capa0"
TABLAS_C = ["dim_programa", "dim_producto", "dim_actividad", "dim_concepto", "rel_concepto_grupo", "rel_concepto_nodo",
            "rel_linaje", "rel_programa_politica", "dim_programa_social", "rel_programa_social_ejecutora",
            "rel_programa_social_financiamiento", "rel_programa_social_linea_aparte", "cobertura_por_anio",
            "dim_tema_gasto", "dim_glosario_gasto"]


# ======================= curados y reglas del módulo (sin datos del MEF)
@pytest.fixture(scope="module")
def cur():
    d, ins = T.cargar(Rutas(RAIZ_REAL))
    return d


def test_curados_validos_y_completos(cur):
    co = cur["conceptos"]
    assert (co.nivel == "hoja").sum() == 19 and (co.nivel == "grupo").sum() == 4
    assert len(cur["mapa"]) == 21 and cur["mapa"].excluye_transferencias.eq("true").all()
    assert len(cur["glosario"]) == 42 and len(cur["linaje"]) == 28 and len(cur["ps"]["programas"]) == 14   # E3: + Jóvenes Productivos
    assert set(cur["cobertura"].estado) == T.ESTADOS_ANIO
    # los ids de tema del YAML son exactamente los de R-GASTO-08 (reglas.json, pieza B)
    reglas = json.loads((RAIZ_REAL / "reglas" / "reglas.json").read_text(encoding="utf-8"))
    r08 = next(r for r in reglas["reglas"] if r["id"] == "R-GASTO-08")
    ini = r08["parametros"]["temas_iniciales"]
    yaml_t = {t["tema_id"]: t for t in cur["temas"]["temas"]}
    assert set(yaml_t) == set(ini)
    for k, v in ini.items():
        assert yaml_t[k]["cadena"] == v["cadena"] and yaml_t[k]["etiqueta_ciudadana"] == v["etiqueta_ciudadana"], k
        assert yaml_t[k].get("alternativa_de") == v["alternativa_de"], k
    assert "pendiente" not in cur["temas"]["revisado_por"] and "7/10/2026" in cur["temas"]["revisado_por"]


def test_glosario_igual_al_csv_de_la_ronda2(cur):
    w4 = pd.read_csv(RAIZ_REAL / "tests/fixtures/glosario_v2.csv",
                     dtype=str, keep_default_na=False)
    g = cur["glosario"].fillna("")
    assert list(g.columns) == list(w4.columns) and g.values.tolist() == w4.values.tolist()


@pytest.mark.parametrize("tid,cad", [("salud", "funcion"), ("pp_1001_dit", "funcion"), ("cpt_Grupo", "concepto"),
                                     ("ps-juntos", "programa_social"), ("ppxfun_1001_salud", "programa")])
def test_gramatica_y_prefijo_rechazan(tid, cad):
    with pytest.raises(PapError):
        T.validar_tema_id(tid, cad)


def test_gramatica_acepta_los_seis_prefijos():
    for tid, cad in [("fun_salud", "funcion"), ("div_educacion_basica", "division"), ("pp_0082_0083_agua", "programa"),
                     ("ppxfun_1001_salud", "programa_x_funcion"), ("cpt_grupo_expan", "concepto"),
                     ("ps_juntos", "programa_social")]:
        T.validar_tema_id(tid, cad)


@pytest.mark.parametrize("cambio", ["transferencias", "concepto_linaje", "tipo_linaje", "alternativa", "intervalo"])
def test_validar_rechaza_curados_malos(cur, cambio):
    d = copy.deepcopy(cur)
    if cambio == "transferencias":
        d["mapa"].loc[0, "excluye_transferencias"] = "false"
    elif cambio == "concepto_linaje":
        d["linaje"].loc[0, "conceptos_afectados"] = "no_existe"
    elif cambio == "tipo_linaje":
        d["linaje"].loc[0, "tipo_cambio"] = "mudanza"
    elif cambio == "alternativa":
        d["temas"]["temas"][-1]["alternativa_de"] = "cpt_no_existe"
    elif cambio == "intervalo":
        d["linaje"].loc[0, "anio_min"] = "2022"
    with pytest.raises(PapError):
        T.validar(d)


def _mapa(filas):
    cols = ["regla_id", "concepto_id", "anio_desde", "anio_hasta", "programa_ppto", "producto_proyecto",
            "actividad_accion_obra", "filtro_sec_ejec", "filtro_funcion", "excluye_transferencias", "evidencia", "confianza"]
    return pd.DataFrame([dict(zip(cols, f)) for f in filas], columns=cols, dtype=object)


def test_resolver_mapa_precedencia_como_exclusion():
    m = _mapa([("M1", "cuna", "2023", None, "1001", "3000892", None, "1426", None, "true", "", ""),
               ("M2", "otros", "2023", None, "1001", "3000892", None, None, None, "true", "", ""),
               ("M3", "gestion_salud", "2023", None, "1001", "3000001", None, None, "SALUD", "true", "", ""),
               ("M4", "gestion_otra", "2023", None, "1001", "3000001", None, None, None, "true", "", ""),
               ("M5", "cred", "2023", None, "1001", "3033255", "5000018", None, None, "true", "", ""),
               ("M6", "agua", "2025", None, "1001", "3000927", None, None, None, "true", "", "")])
    nodos = pd.DataFrame([(2024, "1001", "3000892", "5004345"), (2024, "1001", "3000001", "5004424"),
                          (2024, "1001", "3033255", "5000018"), (2024, "1001", "3033255", "5000019"),
                          (2024, "1001", "3000927", "5004428")],
                         columns=["anio", "programa_ppto", "producto_proyecto", "actividad_accion_obra"])
    r = T.resolver_mapa(m, nodos).set_index("concepto_id")
    assert r.at["cuna", "sec_ejec"] == "1426" and pd.isna(r.at["cuna", "excluye_sec_ejec"])
    assert r.at["otros", "excluye_sec_ejec"] == "1426" and pd.isna(r.at["otros", "sec_ejec"])
    assert r.at["gestion_otra", "excluye_funcion"] == "SALUD" and r.at["gestion_salud", "funcion"] == "SALUD"
    assert "cred" in r.index and len(r.loc[["cred"]]) == 1          # 5000019 queda sin hoja en este mapa de prueba
    assert "agua" not in r.index                                      # la regla empieza en 2025


def test_resolver_mapa_rechaza_ambiguedad():
    m = _mapa([("M1", "a", "2023", None, "1001", "3000892", None, "1426", None, "true", "", ""),
               ("M2", "b", "2023", None, "1001", "3000892", None, "1427", None, "true", "", ""),
               ("M3", "c", "2023", None, "1001", "3000892", None, None, None, "true", "", "")])
    nodos = pd.DataFrame([(2024, "1001", "3000892", "5004345")],
                         columns=["anio", "programa_ppto", "producto_proyecto", "actividad_accion_obra"])
    with pytest.raises(PapError):   # «otros» necesitaría excluir dos ejecutoras
        T.resolver_mapa(m, nodos)


def test_partir_codigos_documentales():
    assert T._partir_codigos("3033313;3033314", "5000029;5000030") == [("3033313", "5000029"), ("3033314", "5000030")]
    assert T._partir_codigos("3000876", "5000027;5000028") == [("3000876", "5000027"), ("3000876", "5000028")]
    assert T._partir_codigos(None, None) == []
    with pytest.raises(PapError):
        T._partir_codigos("1;2", "3;4;5")


def test_nombre_vigente_del_anio_y_nombre_del_mef(cur):
    ps = {p["id"]: p for p in cur["ps"]["programas"]}
    ae = ps["alimentacion_escolar"]["nombres"]
    assert T.etiqueta_programa_social(ae, 2024, "PROGRAMA NACIONAL DE ALIMENTACION ESCOLAR QALI WARMA")["nombre_propio"] == "Qali Warma"
    e25 = T.etiqueta_programa_social(ae, 2025, "PROGRAMA NACIONAL DE ALIMENTACION ESCOLAR COMUNITARIA WASI MIKUNA")
    assert e25["etiqueta"] == "Wasi Mikuna" and not e25["nombre_mef_difiere"]
    lk = T.etiqueta_programa_social(ps["empleo_temporal"]["nombres"], 2024, "PROGRAMA  PARA LA GENERACION ... TRABAJA PERU")
    assert lk["etiqueta"] == "Llamkasun Perú (en el presupuesto del MEF figura como «PROGRAMA PARA LA GENERACION ... TRABAJA PERU»)"
    lk23 = T.etiqueta_programa_social(ps["empleo_temporal"]["nombres"], 2023, None)
    # E3 (dueño, 8/10/2026): rótulo de 2023 con el mes, no el día (el DS 009-2023-TR rige desde el 10/8/2023)
    assert lk23["nombre_cambia_en_anio"] and lk23["etiqueta"] == "Lurawi Perú (Llamkasun Perú desde agosto de 2023)"
    wn = T.etiqueta_programa_social(ps["warmi_nan"]["nombres"], 2025, "PROGRAMA NACIONAL CONTRA LA VIOLENCIA FAMILIAR Y SEXUAL (PNCVFS)")
    assert wn["nombre_propio"] == "Warmi Ñan" and wn["nombre_mef_difiere"]
    assert wn["etiqueta"].startswith("Warmi Ñan (AURORA hasta el 2/5/2025) (en el presupuesto del MEF")   # H5
    au = T.etiqueta_programa_social(ps["warmi_nan"]["nombres"], 2024, None)
    assert au["nombre_propio"] == "AURORA" and au["confianza_nombre"] == "media"
    assert T.etiqueta_programa_social(ae, 2024, None)["etiqueta"] == "Qali Warma (Wasi Mikuna desde el 4/12/2024)"
    assert T.etiqueta_programa_social(ps["pae"]["nombres"], 2024, None) == {}      # el PAE no existía en 2024


def test_tipo_por_anio():   # H7
    t = "PP (programa estratégico 2008-2011)"
    assert T.tipo_del_anio(t, "", 2010) == "programa estratégico (2008-2011)" and T.tipo_del_anio(t, "", 2012) == "PP"
    assert T.tipo_del_anio("PP", "Programa estratégico 2008 (Ley 29142)", 2009) == "programa estratégico (2008-2011)"
    assert T.tipo_del_anio("PP", "", 2009) == "PP" and T.tipo_del_anio("APNOP", None, 2024) == "APNOP"


def test_comparabilidad_reglas():
    ev = pd.DataFrame([dict(id_evento="X", tipo_cambio="division", comparabilidad="c", comparable_por_concepto=True,
                            comparable_por_programa=False)])
    vacio = ev.iloc[0:0]
    assert T.comparabilidad(2023, [2023, 2024, 2025], vacio, "comparable_por_concepto", None)[0] == "sin_anio_anterior"
    assert T.comparabilidad(2021, [2023, 2024, 2025], vacio, "comparable_por_concepto", None)[0] == "sin_montos"
    assert T.comparabilidad(2025, [2023, 2024, 2025], ev, "comparable_por_programa", 0.01)[0] == "no"
    assert T.comparabilidad(2025, [2023, 2024, 2025], ev, "comparable_por_concepto", 0.31)[0] == "si"
    assert T.comparabilidad(2025, [2023, 2024, 2025], vacio, "comparable_por_concepto", 0.31)[0] == "no"
    assert T.comparabilidad(2025, [2023, 2024, 2025], vacio, "comparable_por_concepto", 0.04)[0] == "si"


def test_claves_de_salida_para_todas_las_tablas():
    assert set(TABLAS_C) <= set(salida.CLAVES)


# ======================= guardia de alcances (R-GASTO-08b; diseño corregido tras la auditoría, H1)
@pytest.mark.parametrize("sql", [
    "SELECT anio, sum(devengado) FROM gasto_tema('cpt_grupo_expan') GROUP BY anio",
    "SELECT anio, sum(devengado) FROM gasto_tema(?) GROUP BY anio",
    "SELECT sum(devengado) FROM (SELECT * FROM gasto_tema('pp_1001_dit') WHERE anio = 2025)",
    "WITH x AS (SELECT * FROM gasto_tema('fun_salud')) SELECT a.anio, sum(a.devengado) FROM x a JOIN x b USING (anio) GROUP BY 1",
    "SELECT concepto_id, anio, sum(devengado) FROM v_gasto_concepto GROUP BY ALL",
    "SELECT * FROM dim_tema_gasto WHERE tema_id = 'fun_salud'",
    "SELECT departamento_atribucion, sum(devengado) FROM gasto_tema('fun_salud') WHERE anio = 2025 GROUP BY 1",
    "SELECT sum(devengado) FROM read_parquet('/x/fact_gasto_territorial.parquet') WHERE sec_ejec = '1426'",
    "SELECT x FROM range(3) t(x)",
])
def test_guardia_alcances_permite(sql):
    gu.verificar_consulta(sql)


@pytest.mark.parametrize("sql", [
    # los 4 agujeros de la auditoría (a4_guardia.py), escritos con el nombre anterior y con la vista interna
    "SELECT a.anio, sum(a.devengado) FROM v_gasto_tema a JOIN v_gasto_tema b ON a.anio = b.anio "
    "WHERE a.tema_id = 'fun_salud' AND b.tema_id = 'pp_1001_dit' GROUP BY 1",
    "SELECT count(*) FROM v_gasto_tema a, v_gasto_tema b WHERE a.tema_id = 'fun_salud' AND b.tema_id = 'cpt_grupo_expan'",
    "SELECT sum(t.devengado) FROM v_gasto_tema t JOIN dim_tema_gasto d ON d.anio = t.anio WHERE d.tema_id = 'fun_salud'",
    "SELECT sum(t.devengado) FROM v_gasto_tema t JOIN (SELECT 'x' AS tema_id) s ON true WHERE s.tema_id = 'x'",
    "SELECT sum(devengado) FROM v_gasto_tema_interna WHERE tema_id = 'fun_salud'",
    # los mismos intentos con la macro
    "SELECT a.anio, sum(a.devengado) FROM gasto_tema('fun_salud') a JOIN gasto_tema('pp_1001_dit') b ON a.anio = b.anio GROUP BY 1",
    "SELECT count(*) FROM gasto_tema('fun_salud'), gasto_tema('cpt_grupo_expan')",
    "SELECT (SELECT sum(devengado) FROM gasto_tema('cpt_grupo_expan')) + (SELECT sum(devengado) FROM gasto_tema('ps_cuna_mas'))",
    "SELECT sum(devengado) FROM (SELECT devengado FROM gasto_tema('fun_salud') UNION ALL "
    "SELECT devengado FROM gasto_tema('pp_1001_dit'))",
    "SELECT sum(devengado) FROM gasto_tema(t.tema_id), dim_tema_gasto t",
    "SELECT sum(devengado) FROM gasto_tema(lower('FUN_SALUD'))",
    # H1b (verificación del auditor, a6_guardia_v2.py): lectura por texto o por ruta
    "SELECT sum(devengado) FROM query_table('v_gasto_tema_interna')",
    "SELECT sum(devengado) FROM query('SELECT * FROM v_gasto_tema_interna')",
    "SELECT sum(f.devengado) FROM v_gasto_tematico f JOIN '/r/biblioteca/dimensiones/dim_tema_gasto.parquet' d "
    "ON d.anio = f.anio AND d.funcion = f.funcion",
    "SELECT sum(f.devengado) FROM v_gasto_tematico f JOIN read_parquet('/r/biblioteca/dimensiones/dim_tema_gasto.parquet') d "
    "ON d.anio = f.anio AND d.funcion = f.funcion",
    "SELECT * FROM glob('/r/biblioteca/dimensiones/*')",
    "SELECT sum(devengado) FROM read_parquet(['/x/fact_gasto_territorial.parquet', '/x/dim_tema_gasto.parquet']) "
    "WHERE sec_ejec = '1426'",
    "SELECT sum(devengado) FROM read_csv('/r/curados/capa0/trazabilidad/map_concepto_nodo.csv')",
    "SELECT sum(devengado) FROM MAIN.V_GASTO_TEMA_INTERNA",
    # alcances con otras vistas o con las tablas que definen los temas
    "SELECT (SELECT sum(devengado) FROM v_gasto_concepto) / (SELECT sum(devengado) FROM v_gasto_tematico WHERE funcion = 'SALUD')",
    "SELECT sum(devengado) FROM gasto_tema('pp_1001_dit') UNION ALL SELECT sum(devengado) FROM v_gasto_tematico",
    "SELECT sum(c.devengado) FROM v_gasto_concepto c JOIN rel_concepto_grupo g USING (concepto_id)",
    "SELECT sum(c.devengado) FROM v_gasto_concepto c JOIN dim_tema_gasto d ON d.anio = c.anio WHERE d.tema_id = 'fun_salud'",
    "SELECT sum(f.devengado) FROM v_gasto_tematico f JOIN dim_tema_gasto d ON d.funcion = f.funcion",
])
def test_guardia_alcances_rechaza(sql):
    with pytest.raises(gu.GuardiaGasto):
        gu.verificar_consulta(sql)


# ======================= tablas publicadas
@pytest.fixture(scope="module")
def con():
    man_p = DIM / "manifiesto_s3_gasto.json"
    if not man_p.exists():
        pytest.skip("gasto no construido")
    man = json.loads(man_p.read_text(encoding="utf-8"))
    if not set(TABLAS_C) <= set(man["tablas"]):
        pytest.skip("el gasto publicado es anterior a la pieza C")
    c = duckdb.connect()
    c.execute("SET enable_progress_bar=false; SET memory_limit='2GB'; SET threads=2")
    # P3 (9/10/2026): hasta reconstruir, la fact v1.4.0 no trae cuenta_en_ambito (en el 15 equivale a cuenta_en_lima)
    p3 = "cuenta_en_ambito" in man["tablas"]["fact_gasto_territorial"]["columnas"]
    c.execute("CREATE VIEW fact_gasto_territorial AS SELECT * " + ("" if p3 else ", cuenta_en_lima AS cuenta_en_ambito")
              + f" FROM '{DIM / 'fact_gasto_territorial.parquet'}'")
    for t in TABLAS_C:
        c.execute(f"CREATE VIEW {t} AS SELECT * FROM '{DIM / (t + '.parquet')}'")
    c.execute((DATOS / "vistas_gasto.sql").read_text(encoding="utf-8"))
    c.execute((DATOS / "vistas_gasto_temas.sql").read_text(encoding="utf-8"))
    yield c
    c.close()


def _q(con, sql, *p):
    gu.verificar_consulta(sql)   # toda consulta de las pruebas pasa la guardia, como en el motor
    return con.execute(sql, list(p)).fetchall()


def test_manifiesto_y_pruebas_de_la_pieza_c(con):
    man = json.loads((DIM / "manifiesto_s3_gasto.json").read_text(encoding="utf-8"))
    pr = {p["id"]: p for p in json.loads((DIM / "pruebas_s3_gasto.json").read_text(encoding="utf-8"))}
    for i in ("G-03", "G-28", "G-28b", "G-29", "G-30", "G-31", "G-32", "G-33", "G-34"):
        assert pr[i]["ok"] and pr[i]["bloqueante"], i
    for t in TABLAS_C:
        assert man["tablas"][t]["filas"] > 0, t
    nombres = {i["recurso"] for i in man["insumos"]}
    assert {"vistas_gasto_temas.sql", "trazabilidad/linaje.csv", "trazabilidad/temas_gasto.yaml"} <= nombres


@pytest.mark.parametrize("tema,esperado", list({
    "cpt_grupo_expan": [(2023, 2179), (2024, 2429), (2025, 2456)],
    "cpt_grupo_opcion_c": [(2023, 2056), (2024, 2327), (2025, 2366)],
    "cpt_grupo_anemia_estricta": [(2023, 138), (2024, 184), (2025, 208)],
    "pp_1001_dit": [(2023, 2750), (2024, 3607), (2025, 3867)]}.items()))
def test_cifras_aprobadas_desde_las_vistas(con, tema, esperado):
    r = _q(con, "SELECT anio, round(sum(devengado)/1e6)::INTEGER FROM gasto_tema(?) GROUP BY 1 ORDER BY 1", tema)
    assert r == esperado


def test_hojas_no_se_superponen_y_conservan(con):
    # la suma de las hojas del grupo ex-PAN por la vista de conceptos = el tema (no hay doble conteo entre hojas)
    hojas = [h for (h,) in con.execute("SELECT concepto_id FROM rel_concepto_grupo WHERE grupo_id = 'grupo_expan'").fetchall()]
    r = _q(con, "SELECT anio, round(sum(devengado)/1e6)::INTEGER FROM v_gasto_concepto WHERE concepto_id IN ("
           + ", ".join(f"'{h}'" for h in hojas) + ") GROUP BY 1 ORDER BY 1")
    assert r == [(2023, 2179), (2024, 2429), (2025, 2456)]
    n = con.execute("""SELECT count(*) FROM (SELECT anio, sec_ejec, mes, ubigeo_atribucion, programa_ppto, producto_proyecto,
                              actividad_accion_obra, funcion, clasificador_gasto, fuente_financiamiento, rubro, ambito_id,
                              nivel_atribucion, departamento_meta, division_funcional, grupo_funcional, categoria_gasto,
                              generica, tipo_act_proy, count(DISTINCT concepto_id) k
                       FROM v_gasto_concepto GROUP BY ALL HAVING k > 1)""").fetchone()[0]
    assert n == 0


def test_consulta_a_hierro_programa_por_anio(con):
    r = con.execute("""SELECT anio, string_agg(DISTINCT programa_ppto || '/' || producto_proyecto || '/' || actividad_accion_obra, ';')
                       FROM rel_concepto_nodo WHERE concepto_id = 'suplemento_hierro_vitA_nino' GROUP BY 1 ORDER BY 1""").fetchall()
    d = dict(r)
    assert all(d[a] == "0001/3033256/5000019" for a in range(2017, 2021))
    assert d[2021] == "0001/3033255/5000019"
    assert all(d[a] == "1001/3033255/5000019" for a in range(2022, 2026))
    assert set(d) == set(range(2017, 2026))
    ori = dict(con.execute("""SELECT anio, any_value(origen) FROM rel_concepto_nodo
                              WHERE concepto_id = 'suplemento_hierro_vitA_nino' GROUP BY 1""").fetchall())
    assert ori[2022] == "documental" and ori[2023] == "base"


def test_consulta_a_cuna_mas_cuidado_diurno(con):
    d = dict(con.execute("""SELECT anio, string_agg(DISTINCT programa_ppto || '/' || producto_proyecto, ';')
                            FROM rel_concepto_nodo WHERE concepto_id = 'cuna_mas_cuidado_diurno' GROUP BY 1""").fetchall())
    assert all(d[a] == "0098/3000584" for a in range(2013, 2021))
    assert all(d[a] == "1001/3000892" for a in range(2021, 2026))
    s = con.execute("""SELECT DISTINCT sec_ejec FROM rel_concepto_nodo WHERE concepto_id = 'cuna_mas_cuidado_diurno'
                       AND origen = 'base'""").fetchall()
    assert s == [("1426",)]
    ev = con.execute("""SELECT id_evento FROM rel_linaje WHERE contains(conceptos_afectados, 'cuna_mas_cuidado_diurno')
                        ORDER BY 1""").fetchall()
    assert [e for (e,) in ev] == ["L07", "L21"]


def test_consulta_b_series_y_comparabilidad(con):
    hierro = _q(con, """SELECT anio, round(sum(devengado)/1e6, 1) FROM v_gasto_concepto
                        WHERE concepto_id = 'suplemento_hierro_vitA_nino' GROUP BY 1 ORDER BY 1""")
    assert hierro == [(2023, 97.5), (2024, 113.6), (2025, 107.5)]
    cuna = _q(con, """SELECT anio, round(sum(devengado)/1e6, 1) FROM v_gasto_concepto
                      WHERE concepto_id = 'cuna_mas_cuidado_diurno' GROUP BY 1 ORDER BY 1""")
    assert cuna == [(2023, 294.7), (2024, 365.7), (2025, 446.5)]
    comp = dict(((c, a), v) for c, a, v in con.execute(
        """SELECT concepto_id, anio, comparable_con_anio_anterior FROM cobertura_por_anio""").fetchall())
    for c in ("suplemento_hierro_vitA_nino", "cuna_mas_cuidado_diurno"):
        assert comp[(c, 2023)] == "sin_anio_anterior" and comp[(c, 2024)] == "si" and comp[(c, 2025)] == "si"
        assert all(comp[(c, a)] == "sin_montos" for a in range(2008, 2023))
    assert comp[("cuidado_diurno_otros_ejecutores", 2024)] == "no"
    assert comp[("grupo_expan", 2025)] == "si" and comp[("grupo_opcion_c", 2025)] == "no"   # el agua (L11)
    assert all(comp[("suplemento_hierro_gestante", a)] == "sin_montos" for a in range(2021, 2026))


def test_gestantes_sin_nodo_desde_2021_y_no_se_mapea_prenatal(con):
    r = con.execute("""SELECT max(anio), count(*) FILTER (WHERE programa_ppto = '0002')
                       FROM rel_concepto_nodo WHERE concepto_id = 'suplemento_hierro_gestante'""").fetchone()
    assert r == (2020, 0)
    assert con.execute("SELECT count(*) FROM rel_concepto_nodo WHERE producto_proyecto = '3033172'").fetchone()[0] == 0


def test_dim_tema_gasto_v12(con):
    cols = {c for (c, *_) in con.execute("DESCRIBE dim_tema_gasto").fetchall()}
    reglas = json.loads((RAIZ_REAL / "reglas" / "reglas.json").read_text(encoding="utf-8"))
    r08 = next(r for r in reglas["reglas"] if r["id"] == "R-GASTO-08")
    assert set(r08["parametros"]["columnas"]) <= cols
    r = con.execute("""SELECT count(*) FILTER (WHERE NOT regexp_full_match(tema_id, '(fun|div|pp|ppxfun|cpt|ps)_[0-9a-z_]+')),
                              count(*) FILTER (WHERE NOT excluye_transferencias), count(DISTINCT version),
                              any_value(version),
                              count(*) FILTER (WHERE contains(revisado_por, 'pendiente') AND NOT starts_with(tema_id, 'ps_')),
                              count(DISTINCT tema_id) FILTER (WHERE starts_with(tema_id, 'ps_')
                                                              AND starts_with(revisado_por, 'Dueño, 8/10/2026')),
                              count(*) FILTER (WHERE comparable_con_anio_anterior NOT IN ('si', 'no', 'sin_anio_anterior'))
                       FROM dim_tema_gasto""").fetchone()
    assert r == (0, 0, 1, "1.2.0", 0, 14, 0)   # E3: 13 + Jóvenes Productivos, revisados por el dueño
    sin = con.execute("""SELECT count(*) FROM dim_programa WHERE origen = 'base' AND tema_programa IS NULL""").fetchone()[0]
    assert sin == 0
    assert con.execute("SELECT DISTINCT tema_programa FROM dim_programa WHERE programa_ppto = '0001' AND origen = 'base'"
                       ).fetchall() == [("sin_tema",)]


def test_programas_sociales_nombres_y_alcance(con):
    et = dict(((i, a), e) for i, a, e in con.execute(
        "SELECT id_programa_social, anio, etiqueta FROM dim_programa_social").fetchall())
    assert et[("alimentacion_escolar", 2025)] == "Wasi Mikuna"
    assert et[("alimentacion_escolar", 2024)].startswith("Qali Warma")
    assert et[("empleo_temporal", 2025)].startswith("Llamkasun Perú (en el presupuesto del MEF figura como «")
    assert et[("warmi_nan", 2025)].startswith("Warmi Ñan")
    assert ("pae", 2024) not in et and ("pae", 2025) in et
    # Contigo, PAIS, Vaso de Leche y el PCA no tienen programa presupuestal propio: se pagan desde la APNOP
    r = dict(con.execute("""SELECT id_programa_social, sum(devengado_gasto_final) FILTER (WHERE programa_ppto IN ('9001', '9002'))
                                   / sum(devengado_gasto_final) >= 0.995
                            FROM rel_programa_social_financiamiento
                            WHERE id_programa_social IN ('contigo', 'pais', 'vaso_de_leche', 'pca') GROUP BY 1""").fetchall())
    assert r == {"contigo": True, "pais": True, "vaso_de_leche": True, "pca": True}   # PAIS: 0,06 M en el PP 0068 (2023)


def test_glosario_publicado(con):
    r = con.execute("SELECT count(*), count(DISTINCT id), count(*) FILTER (WHERE definicion_simple IS NULL) "
                    "FROM dim_glosario_gasto").fetchone()
    assert r == (42, 42, 0)


def test_dimensiones_por_anio(con):
    tipos = dict(con.execute("SELECT anio, tipo FROM dim_programa WHERE programa_ppto = '0001'").fetchall())   # H7
    assert tipos[2010] == "programa estratégico (2008-2011)" and tipos[2012] == "PP" and tipos[2023] == "PP"
    r = con.execute("""SELECT origen, min(anio), max(anio) FROM dim_programa GROUP BY 1 ORDER BY 1""").fetchall()
    assert r == [("base", 2023, 2025), ("documental", 2008, 2022)]
    assert con.execute("SELECT min(anio), max(anio) FROM dim_actividad").fetchone() == (2023, 2025)
    assert con.execute("""SELECT rotulo FROM dim_programa WHERE programa_ppto = '1001' AND anio = 2025""").fetchone()[0] \
        == "PP 1001 Productos Específicos para el Desarrollo Infantil Temprano"
    # nodo = (año, programa, producto, actividad) único; la actividad del hierro existe los tres años
    assert con.execute("""SELECT count(*) FROM (SELECT anio, programa_ppto, producto_proyecto, actividad_accion_obra,
                          count(*) n FROM dim_actividad GROUP BY ALL HAVING n > 1)""").fetchone()[0] == 0
    assert con.execute("""SELECT count(*) FROM dim_actividad WHERE actividad_accion_obra = '5000019'
                          AND programa_ppto = '1001'""").fetchone()[0] == 3
