"""GA-09: ningún CUI del detalle MEF se pierde en dim_inversion_ubicacion (G-10, G-20 a G-24, pruebas sobre las tablas
construidas). Decisión del dueño del 7/10/2026: opción B para los «-MUL.DEP-» (solo los del GN/GORE con meta en Lima
van a nacional_multidepartamental; con meta fuera de Lima se quedan en su meta, rotulados multidepartamental_mef).
Origen: 03_auditoria/ola0/pendientes_menores/ga09_cui/test_v2.py (sin la parametrización A/B)."""
import duckdb
import pytest
import yaml

from pap.capa0 import gasto as G
from pap.config import Rutas

from conftest import RAIZ_REAL

DIM = RAIZ_REAL / "biblioteca" / "dimensiones"
BASE = RAIZ_REAL / "biblioteca" / "estandarizada" / "gasto"
CURADA = RAIZ_REAL / "curados" / "capa0" / "inversiones_ubicacion_curada.yaml"
MOTIVOS = {"ubigeo_nulo_texto_gn_no_fiable", "ubigeo_nulo_texto_gr_no_usado", "ubigeo_nulo_sin_texto", "ubigeo_nulo_nombre_ambiguo",
           "ubigeo_nulo_nombre_no_resuelto", "ubigeo_inexistente"}
METODOS = {"ubigeo_valido", "codigo_antiguo_alias", "curado_por_cui", "codigo_escindido_contenedor", "nombre_texto",
           "multidepartamental_mef", "sin_ubicacion"}
ALIAS_ESPERADO = {"160114": "160803", "030715": "030703"}   # un código → un distrito
ESCINDIDO_CONTENEDOR = {"160109": "160800"}                 # un código → varios distritos (Ley 30186)


@pytest.fixture(scope="module")
def con():
    from pap.capa0 import insumos
    from pap.config import Rutas
    from pap.errores import PapError
    try:
        detalle = insumos.ultimo(Rutas(RAIZ_REAL), "MEF-DETALLE-INVERSIONES").ruta
    except PapError as e:
        pytest.skip(f"falta el crudo del detalle de inversiones: {e}")
    if not (DIM / "dim_inversion_ubicacion.parquet").exists():
        pytest.skip("gasto no construido")
    c = duckdb.connect()
    c.execute("SET enable_progress_bar=false")
    c.execute("SET memory_limit='3GB'")
    c.execute(f"CREATE VIEW dim AS SELECT * FROM '{DIM / 'dim_inversion_ubicacion.parquet'}'")
    c.execute(f"CREATE VIEW fact AS SELECT * FROM '{DIM / 'fact_gasto_territorial.parquet'}'")
    c.execute(f"CREATE VIEW ubig AS SELECT * FROM '{DIM / 'dim_ubigeo_historico.parquet'}'")
    bases = ", ".join(f"'{b}'" for b in G.bases_vigentes(Rutas(RAIZ_REAL)))  # H3: huella vigente, no glob
    c.execute(f"CREATE VIEW base AS SELECT * FROM read_parquet([{bases}])")
    # el detalle se lee aparte y se compara como número, sin el lpad que usa gasto.py
    c.execute(f"""CREATE TABLE det AS SELECT TRY_CAST(trim(CODIGO_UNICO) AS BIGINT) AS cui_n, trim(UBIGEO) AS ubigeo
                  FROM read_csv('{detalle}', header=true, all_varchar=true, quote='"', escape='"', delim=',',
                                strict_mode=true) WHERE CODIGO_UNICO IS NOT NULL""")
    return c


def test_ningun_cui_del_detalle_se_pierde(con):
    faltan, sobran = con.execute("""
        SELECT (SELECT count(DISTINCT cui_n) FROM det WHERE cui_n NOT IN (SELECT cui::BIGINT FROM dim)),
               (SELECT count(*) FROM dim WHERE cui::BIGINT NOT IN (SELECT cui_n FROM det))""").fetchone()
    assert (faltan, sobran) == (0, 0)


def test_nivel_o_motivo_exclusivos_y_listas_cerradas(con):
    assert con.execute("SELECT count(*) FROM dim WHERE (nivel_comun IS NULL) = (motivo_sin_ubicacion IS NULL)").fetchone()[0] == 0
    motivos = {r[0] for r in con.execute("SELECT DISTINCT motivo_sin_ubicacion FROM dim WHERE motivo_sin_ubicacion IS NOT NULL").fetchall()}
    metodos = {r[0] for r in con.execute("SELECT DISTINCT metodo_ubicacion FROM dim").fetchall()}
    assert motivos <= MOTIVOS and metodos <= METODOS


def test_proyectos_del_detalle_llegan_al_fact_con_metodo(con):
    # no tautológica: se une por número contra el crudo, no por la clave que construye gasto.py
    n = con.execute("""SELECT count(*) FROM fact WHERE tipo_act_proy ILIKE 'PROYECTO%'
                       AND TRY_CAST(trim(producto_proyecto) AS BIGINT) IN (SELECT cui_n FROM det)
                       AND metodo_ubicacion_cui IS NULL""").fetchone()[0]
    assert n == 0


def test_porcentaje_por_metodo(con):
    df = con.execute("SELECT metodo_ubicacion, count(*) n, count(*) / sum(count(*)) OVER () p FROM dim GROUP BY 1").df()
    print(df.to_string())
    ok = df.loc[df.metodo_ubicacion.isin(["ubigeo_valido", "codigo_antiguo_alias", "curado_por_cui"]), "p"].sum()
    assert ok >= 0.99
    # referencia 7/10/2026 (detalle sha256:0fb1d61d…): 149 861 válidos, 102 multidep., 21 por texto, 9 curados,
    # 5 alias, 1 escindido a provincia, 139 sin ubicación. Si cambia el crudo, revisar antes de ampliar el umbral.
    assert df.loc[df.metodo_ubicacion == "nombre_texto", "n"].sum() < 200


def test_solo_gl_por_texto(con):
    """Decisión del dueño: el UBIGEO nulo se ubica por nombre solo en gobiernos locales (ni GN ni GORE)."""
    assert G.NIVELES_UBICACION_POR_NOMBRE == ("GL",)
    assert con.execute("""SELECT count(*) FROM dim WHERE metodo_ubicacion = 'nombre_texto'
                          AND nivel_gobierno_inv <> 'GL'""").fetchone()[0] == 0


def test_alias_al_distrito_correcto(con):
    filas = con.execute("""SELECT d.cui, d.ubigeo_fuente, d.ubigeo_atribucion FROM dim d
                           WHERE metodo_ubicacion = 'codigo_antiguo_alias'""").fetchall()
    assert filas, "se esperaba al menos un alias"
    for cui, fuente, destino in filas:
        assert ALIAS_ESPERADO.get(fuente) == destino, (cui, fuente, destino)


def test_codigo_escindido_nunca_por_alias(con):
    # 160109 se dividió en tres distritos: solo curado por CUI (a un sucesor) o la provincia que los contiene
    filas = con.execute("""SELECT cui, metodo_ubicacion, ubigeo_atribucion FROM dim
                           WHERE ubigeo_fuente IN ('160109')""").fetchall()
    for cui, metodo, destino in filas:
        assert metodo in ("curado_por_cui", "codigo_escindido_contenedor"), (cui, metodo)
        assert destino[:4] == ESCINDIDO_CONTENEDOR["160109"][:4], (cui, destino)


def test_tabla_curada_coherente(con):
    assert CURADA.exists(), CURADA
    cur = yaml.safe_load(CURADA.read_text(encoding="utf-8")) or []
    assert len({c["cui"] for c in cur}) == len(cur)
    for c in cur:
        fila = con.execute("SELECT ubigeo_fuente, metodo_ubicacion, ubigeo_atribucion FROM dim WHERE cui = ?",
                           [c["cui"]]).fetchone()
        assert fila == (c["codigo_fuente"], "curado_por_cui", c["ubigeo_inei"]), (c["cui"], fila)
        assert con.execute("SELECT count(*) FROM ubig WHERE ubigeo_inei = ? AND nivel = 'distrito'",
                           [c["ubigeo_inei"]]).fetchone()[0] > 0


def test_suma_se_conserva_devengado_y_pim(con):
    for anio, bd, fd, bp, fp in con.execute("""
            SELECT anio, b.dev, f.dev, b.pim, f.pim
            FROM (SELECT anio, sum(devengado) dev, sum(pim) pim FROM base GROUP BY 1) b
            JOIN (SELECT anio, sum(devengado) dev, sum(pim) pim FROM fact GROUP BY 1) f USING (anio)""").fetchall():
        assert (bd, bp) == (fd, fp), anio


def test_opcion_b_configurada():
    assert G.MULTIDEP_SOLO_META_LIMA is True, "decisión del dueño (7/10/2026): opción B"


def test_multidep_del_gn_opcion_b(con):
    sql = """SELECT f.departamento_meta = '15' AS meta_lima, f.nivel_atribucion, count(*) n
             FROM fact f JOIN dim d ON d.cui = lpad(f.producto_proyecto, 7, '0')
             WHERE f.tipo_act_proy ILIKE 'PROYECTO%' AND d.nivel_comun = 'multidepartamental'
               AND f.nivel_gobierno IN ('E', 'R') AND f.devengado <> 0 GROUP BY ALL"""
    filas = con.execute(sql).fetchall()
    assert filas
    for meta_lima, nivel, n in filas:
        if meta_lima:
            assert nivel in {"nacional_multidepartamental", "nacional_no_territorializable"}, (meta_lima, nivel, n)
        else:  # fuera de Lima se respeta la meta (rotulada con metodo_ubicacion_cui), nunca a multidepartamental
            assert nivel in {"departamento_meta", "nacional_no_territorializable"}, (meta_lima, nivel, n)
    rot = con.execute("""SELECT count(*) FROM fact f JOIN dim d ON d.cui = lpad(f.producto_proyecto, 7, '0')
                         WHERE d.nivel_comun = 'multidepartamental' AND f.nivel_atribucion = 'departamento_meta'
                           AND f.nivel_gobierno IN ('E', 'R')
                           AND coalesce(f.metodo_ubicacion_cui, '') <> 'multidepartamental_mef'""").fetchone()[0]
    assert rot == 0


def test_municipalidades_con_cui_multidep_siguen_en_su_sede(con):
    n = con.execute("""SELECT count(*) FROM fact WHERE lpad(producto_proyecto, 7, '0') = '2340601'
                       AND nivel_gobierno = 'M' AND nivel_atribucion NOT LIKE '%municipal'""").fetchone()[0]
    assert n == 0
