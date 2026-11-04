"""GA-05 (R-GASTO-05 v4): lista curada de la genérica 2.4, vistas del motor y guardia de consultas.

Cubre: la lista (esquema, transiciones, excepciones por código), su aplicación sobre la base real (G-15 a G-18b), las
vistas del motor sobre un fact simulado a partir de la base (conservación, columnas separadas) y la guardia (pruebas
positivas y negativas). Origen: 03_auditoria/ola0/pendientes_menores/ga05_transferencias/v2/test_v2.py, con la decisión
del dueño del 7/10/2026 (EX-01 centros poblados y EX-02 probable IVP aplicadas al bloque (b), con la alarma G-18b).
"""
import duckdb
import pytest
import yaml

from pap.capa0 import gasto as G
from pap.capa0 import guardia_gasto as gu
from pap.capa0 import transferencias as tr
from pap.config import Rutas
from pap.errores import PapError

from conftest import RAIZ_REAL

LISTA = RAIZ_REAL / "curados" / "capa0" / "lista_transferencias.yaml"
VISTAS = RAIZ_REAL / "curados" / "capa0" / "vistas_gasto.sql"
BASE = RAIZ_REAL / "biblioteca" / "estandarizada" / "gasto"


# ======================= la lista
@pytest.fixture(scope="module")
def doc():
    return yaml.safe_load(LISTA.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def lista():
    return tr.cargar_lista(LISTA)


def test_lista_valida_y_versionada(lista, doc):
    assert lista["version"] and len(lista["clasificadores"]) == 18
    assert doc["revisado_dueno"] is False, "no marcar revisada hasta cotejar el Anexo 2 de cada año"
    assert "presentacion_mef_2014" in doc["fuentes"]


def test_excepciones_por_codigo_y_transiciones(lista):
    ex = lista["excepciones"]
    assert ex.actividad_accion_obra.str.fullmatch(r"\d{7}").all()
    assert set(ex.estado) <= {"aplicada", "pendiente_decision_dueno"}
    # decisión del dueño (7/10/2026): EX-01 (centros poblados) y EX-02 (probable IVP) al bloque (b); EX-03 (fondos)
    assert set(ex.loc[ex.estado == "aplicada", "id"]) == {"EX-01", "EX-02", "EX-03"}


def test_lista_rechaza_transicion_invalida(tmp_path, doc):
    malo = dict(doc)
    malo["excepciones"] = [{"id": "X", "estado": "aplicada", "categoria": "gasto_final_externo",
                            "combinaciones": [{"clasificador": "2.4.1.3.1.1", "nivel_gobierno": "E",
                                               "actividad_accion_obra": "5000001"}]}]
    p = tmp_path / "l.yaml"
    p.write_text(yaml.safe_dump(malo, allow_unicode=True), encoding="utf-8")
    with pytest.raises(tr.ListaInvalida):
        tr.cargar_lista(p)


def test_lista_rechaza_codigo_repetido(tmp_path, doc):
    malo = dict(doc)
    malo["clasificadores"] = doc["clasificadores"] + [doc["clasificadores"][0]]
    p = tmp_path / "l.yaml"
    p.write_text(yaml.safe_dump(malo, allow_unicode=True), encoding="utf-8")
    with pytest.raises(tr.ListaInvalida):
        tr.cargar_lista(p)


# ======================= aplicación sobre la base real
@pytest.fixture(scope="module")
def con(lista):
    try:  # H3 (auditoría de la pieza A): solo las bases de la huella vigente, nunca un glob
        bases = G.bases_vigentes(Rutas(RAIZ_REAL))
    except PapError as e:
        pytest.skip(f"no hay base de gasto vigente: {e}")
    lista_bases = ", ".join(f"'{b}'" for b in bases)
    c = duckdb.connect()
    c.execute("SET memory_limit='3GB'")
    c.execute(f"CREATE VIEW base_cruda AS SELECT * FROM read_parquet([{lista_bases}])")
    tr.registrar(c, lista)
    # fact simulado: mismas columnas que usan las vistas (la atribución territorial no importa aquí)
    c.execute("""CREATE TABLE fact_gasto_territorial AS
                 SELECT anio, mes, 'departamento_meta' AS nivel_atribucion, departamento_meta || '0000' AS ubigeo_atribucion,
                        departamento_meta AS departamento_atribucion, NULL::VARCHAR AS ambito_id, 'no_aplica' AS alcance_ejecutora,
                        sec_ejec, nivel_gobierno, departamento_meta, programa_ppto, producto_proyecto, funcion,
                        division_funcional, generica, tipo_act_proy, categoria_transferencia, es_transferencia,
                        es_transferencia_intergub, bloque_consolidado,
                        -- pieza A (rondas 1-2): marcas de alcance que el consolidado agrupa
                        departamento_meta = '15' AS cuenta_en_lima, false AS referencia_nacional, false AS ejecutora_mixta,
                        departamento_meta IN ('15', '07') AS cuenta_en_ambito,   -- P3 (9/10/2026)
                        false AS obra_sede_nacional,   -- E3 (8/10/2026)
                        sum(pia) pia, sum(pim) pim, sum(devengado) devengado,
                        anio::VARCHAR || '-12' AS fecha_corte_datos, true AS es_anio_cerrado
                 FROM base GROUP BY ALL""")
    c.execute(VISTAS.read_text(encoding="utf-8"))
    return c


@pytest.fixture(scope="module")
def resultados(con, lista):
    out = {}
    tr.pruebas(con, lista, lambda i, d, ok, det=None, b=True: out.__setitem__(i, (ok, b, det)))
    return out


@pytest.mark.parametrize("pid", ["G-15", "G-15b", "G-17", "G-17b", "G-18"])
def test_pruebas_de_construccion_pasan(resultados, pid):
    ok, _, det = resultados[pid]
    assert ok, det


def test_alarma_por_nombre_no_clasifica_y_ve_lo_no_cubierto(resultados, lista):
    """G-18b solo avisa. Con EX-01 y EX-02 aplicadas, no lista las combinaciones exactas que esas excepciones ya
    cubren, pero sigue viendo lo que quedó fuera (p. ej. caminos vecinales en la 2.4.2.3.1.3, de capital)."""
    ok, bloq, det = resultados["G-18b"]
    assert not bloq
    ex = lista["excepciones"]
    cubiertas = set(zip(ex.clasificador, ex.nivel_gobierno, ex.actividad_accion_obra))
    vistas = {(d["clasificador_transferencia"], d["nivel_gobierno"], d["actividad_accion_obra"]) for d in det}
    assert not (vistas & cubiertas)
    assert any(d["clasificador_transferencia"] == "2.4.2.3.1.3" for d in det)


def test_alarma_por_nombre_detecta_si_la_excepcion_no_se_aplica(con, lista):
    """Si EX-01 y EX-02 volvieran a quedar pendientes, la alarma debe avisar (centros poblados y caminos vecinales)."""
    pend = dict(lista)
    pend["excepciones"] = lista["excepciones"].assign(
        estado=lista["excepciones"].estado.where(lista["excepciones"].id == "EX-03", "pendiente_decision_dueno"))
    c = duckdb.connect()
    c.execute("SET memory_limit='3GB'")
    bases = ", ".join(f"'{b}'" for b in G.bases_vigentes(Rutas(RAIZ_REAL)))
    c.execute(f"CREATE VIEW base_cruda AS SELECT * FROM read_parquet([{bases}])")
    tr.registrar(c, pend)
    out = {}
    tr.pruebas(c, pend, lambda i, d, ok, det=None, b=True: out.__setitem__(i, (ok, b, det)))
    ok, bloq, det = out["G-18b"]
    assert not bloq and not ok
    assert {"5001267", "5001452"} <= {d["actividad_accion_obra"] for d in det}


def test_tematica_igual_a_la_marca_anterior(con):
    dif = con.execute("""SELECT count(*) FROM base b JOIN base_cruda c USING (anio, mes, sec_ejec, programa_ppto,
                         producto_proyecto, actividad_accion_obra, clasificador_transferencia, fuente_financiamiento,
                         funcion, division_funcional, grupo_funcional, departamento_meta, categoria_gasto)
                         WHERE b.generica = '4' AND b.es_transferencia <> c.es_transferencia""").fetchone()[0]
    assert dif == 0


def test_conservacion_vistas(con):
    for anio, total, tem, cf, cb, fo, it in con.execute("""
        SELECT anio, sum(devengado),
               (SELECT sum(devengado) FROM v_gasto_tematico v WHERE v.anio = f.anio),
               (SELECT sum(gasto_final_devengado) FROM v_gasto_consolidado v WHERE v.anio = f.anio),
               (SELECT sum(entregado_fuera_del_presupuesto_devengado) FROM v_gasto_consolidado v WHERE v.anio = f.anio),
               (SELECT coalesce(sum(devengado), 0) FROM v_gasto_fondos_por_identificar v WHERE v.anio = f.anio),
               sum(devengado) FILTER (WHERE bloque_consolidado = 'excluir_intergubernamental')
        FROM fact_gasto_territorial f GROUP BY anio""").fetchall():
        assert tem == cf and total == cf + cb + fo + it, anio


def test_consolidado_no_tiene_columna_unica_de_devengado(con):
    cols = {r[0] for r in con.execute("DESCRIBE v_gasto_consolidado").fetchall()}
    assert "devengado" not in cols and "pim" not in cols
    assert {"gasto_final_devengado", "entregado_fuera_del_presupuesto_devengado"} <= cols


def test_cifras_piloto_sin_cambio(con):
    """Salud, PP 1001 y salud con meta en Lima (2025) son iguales a las publicadas (sin transferencias)."""
    r = dict(con.execute("""SELECT 'salud', round(sum(devengado)/1e6, 1) FROM v_gasto_tematico WHERE anio = 2025 AND funcion = 'SALUD'
                            UNION ALL SELECT 'pp1001', round(sum(devengado)/1e6, 1) FROM v_gasto_tematico WHERE anio = 2025 AND programa_ppto = '1001'
                            UNION ALL SELECT 'lima_salud', round(sum(devengado)/1e6, 1) FROM v_gasto_tematico
                                      WHERE anio = 2025 AND funcion = 'SALUD' AND departamento_meta = '15'""").fetchall())
    assert r == {"salud": 30524.3, "pp1001": 3866.8, "lima_salud": 12247.1}


def test_bloque_b_2025(con):
    b = con.execute("""SELECT round(sum(entregado_fuera_del_presupuesto_devengado)/1e6, 1) FROM v_gasto_consolidado
                       WHERE anio = 2025""").fetchone()[0]
    # .4 completo (2 500,3) + EX-01 centros poblados (240,8) + EX-02 probable IVP (78,9); el .5 de 2025 está todo en
    # fondos por identificar (EX-03)
    assert b == 2820.0


# ======================= guardia del motor
PERMITIDAS = [
    "SELECT funcion, sum(devengado) FROM v_gasto_tematico WHERE anio = 2025 GROUP BY 1",
    "SELECT anio, sum(gasto_final_devengado) AS g FROM v_gasto_consolidado GROUP BY 1",
    "SELECT anio, sum(entregado_fuera_del_presupuesto_devengado) AS e FROM v_gasto_consolidado GROUP BY 1",
    "SELECT sum(devengado) FROM fact_gasto_territorial WHERE sec_ejec = '1691' AND anio = 2025",
    "SELECT bloque_consolidado, sum(devengado) FROM fact_gasto_territorial f WHERE anio = 2025 AND sec_ejec = '46' GROUP BY 1",
    "WITH x AS (SELECT * FROM fact_gasto_territorial WHERE pliego = '011') SELECT count(*) FROM x",
    "SELECT sum(devengado) FROM v_gasto_fondos_por_identificar",
]
RECHAZADAS = [
    "SELECT sum(devengado) FROM fact_gasto_territorial WHERE anio = 2025",
    "SELECT sum(devengado) FROM fact_gasto_territorial WHERE sec_ejec = '1' OR anio = 2025",
    "SELECT sum(devengado) FROM read_parquet('/x/fact_gasto_territorial.parquet')",
    "SELECT sum(devengado) FROM '/x/gasto_base_2025_a_b.parquet' WHERE funcion = 'SALUD'",
    "WITH x AS (SELECT * FROM fact_gasto_territorial) SELECT sum(devengado) FROM x",
    "SELECT sum(gasto_final_devengado + entregado_fuera_del_presupuesto_devengado) FROM v_gasto_consolidado",
    "SELECT sum(gasto_final_devengado) + sum(entregado_fuera_del_presupuesto_devengado) FROM v_gasto_consolidado",
    "SELECT sum(v) FROM (SELECT gasto_final_devengado v FROM v_gasto_consolidado "
    "UNION ALL SELECT entregado_fuera_del_presupuesto_devengado FROM v_gasto_consolidado)",
    "SELECT sum(v) FROM (UNPIVOT v_gasto_consolidado ON gasto_final_devengado, entregado_fuera_del_presupuesto_devengado "
    "INTO NAME k VALUE v)",
    "SELECT (SELECT sum(devengado) FROM v_gasto_tematico) + (SELECT sum(devengado) FROM v_gasto_fondos_por_identificar)",
    # auditoría final de la ronda 3 (hallazgo 1): el caso exacto del auditor, con alias en una subconsulta
    "SELECT a+b FROM (SELECT sum(gasto_final_devengado) a, sum(entregado_fuera_del_presupuesto_devengado) b "
    "FROM v_gasto_consolidado)",
    "WITH x AS (SELECT sum(gasto_final_devengado) a FROM v_gasto_consolidado), "
    "y AS (SELECT sum(entregado_fuera_del_presupuesto_devengado) b FROM v_gasto_consolidado) SELECT a + b FROM x, y",
    "SELECT anio, sum(gasto_final_devengado) AS g, sum(entregado_fuera_del_presupuesto_devengado) AS e "
    "FROM v_gasto_consolidado GROUP BY 1",
    "SELECT * FROM v_gasto_consolidado WHERE anio = 2025",
]


@pytest.mark.parametrize("sql", PERMITIDAS)
def test_guardia_permite(sql):
    gu.verificar_consulta(sql)


@pytest.mark.parametrize("sql", RECHAZADAS)
def test_guardia_rechaza(sql):
    with pytest.raises(gu.GuardiaGasto):
        gu.verificar_consulta(sql)


def test_guardia_permitidas_se_ejecutan(con):
    """Lo que la guardia deja pasar también corre sobre las vistas reales (no es una guardia de papel)."""
    for sql in PERMITIDAS:
        if "pliego" in sql:
            continue  # el fact simulado no trae pliego
        gu.verificar_consulta(sql)
        con.execute(sql).fetchall()
