"""S3 gasto: atribución territorial del devengado MEF (R-GASTO-01/02/04/08)."""
import pytest

from pap.capa0 import gasto as G
from pap.config import Rutas
from pap.errores import PapError

from conftest import RAIZ_REAL


@pytest.fixture(scope="module")
def res():
    try:
        r = G.construir(Rutas(RAIZ_REAL))
    except (PapError, FileNotFoundError) as e:
        pytest.skip(f"faltan insumos: {e}")
    yield r
    r.tablas["fact_gasto_territorial"].unlink(missing_ok=True)  # Parquet temporal no publicado


def test_sin_pruebas_bloqueantes_fallidas(res):
    assert [p["id"] for p in res.pruebas if p["bloqueante"] and not p["ok"]] == []


def test_conservacion_exacta(res):
    assert all(p["ok"] for p in res.pruebas if p["id"] == "G-01")


def test_pia_igual_a_ley(res):
    g07 = next(p for p in res.pruebas if p["id"] == "G-07")
    assert g07["ok"], g07["detalle"]


def test_municipalidades_por_nombre_de_ejecutora(res):  # noqa
    ue = res.tablas["dim_unidad_ejecutora"]
    m = ue[ue.nivel_gobierno == "M"]
    # PLIEGO_NOMBRE viene vacío en gobiernos locales: el tipo sale de EJECUTORA_NOMBRE
    assert (m.tipo_entidad_local == "distrital").sum() > 1500
    assert (m.tipo_entidad_local == "provincial").sum() > 150


def test_niveles_de_atribucion_validos(res):
    import duckdb
    f = duckdb.sql(f"SELECT DISTINCT nivel_atribucion, ubigeo_atribucion, ambito_id "
                   f"FROM read_parquet('{res.tablas['fact_gasto_territorial']}')").df()
    assert set(f.nivel_atribucion) <= {
        "distrito_inversion", "provincia_inversion", "departamento_inversion", "distrito_municipal",
        "provincia_municipal", "departamento_meta", "nacional_no_territorializable", "nacional_multidepartamental"}
    amb = f[f.ambito_id.notna()]
    assert set(amb.ambito_id) == {"LIMA_REGION", "LIMA_METROPOLITANA", "AREA_METROPOLITANA_LIMA_CALLAO"}
    assert set(amb.ubigeo_atribucion) == {"A-" + a for a in amb.ambito_id}
    otros = f[f.ambito_id.isna()].ubigeo_atribucion
    assert (otros.str.len() == 6).all() and otros.str.isdigit().all()


def test_base_csv_escape_y_montos_invalidos(tmp_path):
    """El CSV del MEF se lee con escape '"' y en modo estricto; un monto con texto se cuenta (RP-08)."""
    import duckdb
    cab = ("ANO_EJE MES_EJE NIVEL_GOBIERNO NIVEL_GOBIERNO_NOMBRE SECTOR SECTOR_NOMBRE PLIEGO PLIEGO_NOMBRE SEC_EJEC "
           "EJECUTORA EJECUTORA_NOMBRE DEPARTAMENTO_EJECUTORA DEPARTAMENTO_EJECUTORA_NOMBRE PROVINCIA_EJECUTORA "
           "PROVINCIA_EJECUTORA_NOMBRE DISTRITO_EJECUTORA DISTRITO_EJECUTORA_NOMBRE SEC_FUNC PROGRAMA_PPTO "
           "PROGRAMA_PPTO_NOMBRE TIPO_ACT_PROY TIPO_ACT_PROY_NOMBRE PRODUCTO_PROYECTO PRODUCTO_PROYECTO_NOMBRE "
           "ACTIVIDAD_ACCION_OBRA ACTIVIDAD_ACCION_OBRA_NOMBRE FUNCION FUNCION_NOMBRE DIVISION_FUNCIONAL "
           "DIVISION_FUNCIONAL_NOMBRE GRUPO_FUNCIONAL GRUPO_FUNCIONAL_NOMBRE META FINALIDAD META_NOMBRE "
           "DEPARTAMENTO_META DEPARTAMENTO_META_NOMBRE FUENTE_FINANCIAMIENTO FUENTE_FINANCIAMIENTO_NOMBRE RUBRO "
           "RUBRO_NOMBRE TIPO_RECURSO TIPO_RECURSO_NOMBRE CATEGORIA_GASTO CATEGORIA_GASTO_NOMBRE TIPO_TRANSACCION "
           "GENERICA GENERICA_NOMBRE SUBGENERICA SUBGENERICA_NOMBRE SUBGENERICA_DET SUBGENERICA_DET_NOMBRE ESPECIFICA "
           "ESPECIFICA_NOMBRE ESPECIFICA_DET ESPECIFICA_DET_NOMBRE MONTO_PIA MONTO_PIM MONTO_CERTIFICADO "
           "MONTO_COMPROMETIDO_ANUAL MONTO_COMPROMETIDO MONTO_DEVENGADO MONTO_GIRADO").split()

    def fila(nombre_meta, pim, transf=False):
        v = {c: "1" for c in cab}
        v.update(ANO_EJE="2025", MES_EJE="1", NIVEL_GOBIERNO="R", PROGRAMA_PPTO="1001", META_NOMBRE=nombre_meta,
                 DEPARTAMENTO_EJECUTORA="01", PROVINCIA_EJECUTORA="01", DISTRITO_EJECUTORA="01",
                 GENERICA="4" if transf else "3", SUBGENERICA_DET="3", MONTO_PIA="0", MONTO_PIM=pim,
                 MONTO_DEVENGADO="10.50")
        return ",".join('"' + v[c].replace('"', '""') + '"' for c in cab)
    csv = tmp_path / "g.csv"
    # un nombre con comillas dobladas y comas: no debe correr columnas
    csv.write_text(",".join(f'"{c}"' for c in cab) + "\n" + fila('META "A", B', "100") + "\n"
                   + fila("META C", "1,234.50") + "\n" + fila("T", "5", transf=True) + "\n", encoding="utf-8")
    out = tmp_path / "b.parquet"
    duckdb.execute(G.SQL_BASE.replace("{destino}", str(out)), [str(csv)])
    r = duckdb.sql(f"SELECT sum(filas), sum(montos_invalidos), sum(pim), sum(devengado), "
                   f"sum(filas) FILTER (WHERE es_transferencia) FROM '{out}'").fetchone()
    assert r[0] == 3 and r[1] == 1 and float(r[2]) == 105.0 and float(r[3]) == 31.5 and r[4] == 1


def test_alcance_y_ambitos_de_lima(res):
    ue = res.tablas["dim_unidad_ejecutora"]
    e = ue[ue.nivel_gobierno == "E"]
    assert e.alcance_ejecutora.notna().all()
    mml = ue[(ue.nivel_gobierno == "R") & ue.pliego_nombre.str.startswith("MUNICIPALIDAD METROPOLITANA DE LIMA")]
    assert (mml.ambito_id == "LIMA_METROPOLITANA").all() and len(mml) > 0


def test_alcance_solo_con_meta_lima(res):
    import duckdb
    r = duckdb.sql(f"""SELECT count(*) FILTER (WHERE alcance_ejecutora IS NULL),
                              count(*) FILTER (WHERE alcance_ejecutora <> 'no_aplica'   -- P3: meta 15 o 07
                                               AND NOT (departamento_meta IN ('15', '07') AND nivel_atribucion = 'departamento_meta'))
                       FROM read_parquet('{res.tablas['fact_gasto_territorial']}')""").fetchone()
    assert r == (0, 0)


def test_pruebas_de_la_pieza_a(res):
    """Rondas 1-2 (pieza A): campos nuevos no nulos, conservación por actividad × fuente × rubro × clasificador y
    reparto de Lima con la línea aparte de referencia nacional (incluidas sus obras)."""
    ids = {p["id"]: p for p in res.pruebas}
    for i in ("G-25", "G-26", "G-27", "G-37", "G-39", "G-40", "G-41"):   # G-37: E3; G-39 a G-41: P3
        assert ids[i]["ok"] and ids[i]["bloqueante"], ids[i]["detalle"]
    assert ids["G-25b"]["ok"]
    ue = res.tablas["dim_unidad_ejecutora"]
    assert set(ue.loc[ue.referencia_nacional, "sec_ejec"]) == {"1235", "1512"}


def test_pruebas_de_la_pieza_c(res):
    """Rondas 1-2 (pieza C): capa de trazabilidad y dim_tema_gasto v1.2 (G-03 para todos los alcances; cifras
    aprobadas desde la capa y desde las vistas; cada sol en ≤ 1 hoja y en ≤ 1 programa social)."""
    ids = {p["id"]: p for p in res.pruebas}
    for i in ("G-03", "G-28", "G-28b", "G-29", "G-30", "G-31", "G-32", "G-33", "G-34", "G-38"):   # G-38: E3
        assert ids[i]["ok"] and ids[i]["bloqueante"], (i, ids[i]["detalle"])
    tema = res.tablas["dim_tema_gasto"]
    assert set(tema.cadena) == {"funcion", "division", "programa", "programa_x_funcion", "concepto", "programa_social"}
    assert (tema.version == G.VERSION_TEMA).all()
    ps = tema.tema_id.str.startswith("ps_")
    assert not tema[~ps].revisado_por.str.contains("pendiente").any()
    # auditoría de la pieza C, H4: el visto se declara; el dueño aprobó los temas ps_ el 8/10/2026 (E3)
    assert tema[ps].revisado_por.str.startswith("Dueño, 8/10/2026").all() and tema[ps].tema_id.nunique() == 14
    ids = {p["id"]: p for p in res.pruebas}
    assert ids["G-38"]["detalle"] == {"empleo_temporal/2023": 605.6, "empleo_temporal/2024": 535.7,
                                      "empleo_temporal/2025": 409.0}
