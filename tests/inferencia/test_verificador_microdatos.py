"""M0-07, en el Mac: el verificador y la gramática sobre los Parquet y el índice reales de la ENDES 2024.

Necesitan `biblioteca/microdatos/ENDES/2024/` y `biblioteca/variables/` (`pap microdatos convertir` y `pap variables indexar`):
si faltan, FALLAN (no se saltan)."""
import re

import polars as pl
import pytest

from pap.inferencia.duckdb_seguro import conexion_segura
from pap.inferencia.gramatica import compilar
from pap.inferencia.verificador import Contexto, Falla, verificar

from conftest import RAIZ_REAL

from .recetas_m0 import NIVELES, RECETAS

pytestmark = [pytest.mark.regresion_microdatos, pytest.mark.solo_mac]

# Casos de u de cada receta, medidos en M0-06 (tests/inferencia/test_tablas_curadas_microdatos.py)
CASOS_U = {"anemia": 9959, "anemia_oms2024": 9959, "dci": 19511}


@pytest.fixture(scope="module")
def ctx():
    for carpeta in ("biblioteca/variables", "biblioteca/microdatos/ENDES/2024"):
        assert (RAIZ_REAL / carpeta).is_dir(), f"falta {carpeta}"
    return Contexto.cargar(RAIZ_REAL)


@pytest.fixture(scope="module")
def con():
    return conexion_segura(RAIZ_REAL)


@pytest.mark.parametrize("receta", list(RECETAS))
def test_u_compilada_da_los_casos_de_m0_06(ctx, con, receta):
    pc = verificar(RECETAS[receta]("nacional"), ctx)
    assert not isinstance(pc, Falla), pc
    c = compilar(pc, ctx.esquema, ctx.carpeta_microdatos)
    df = pl.from_arrow(con.execute(c.sql, c.parametros).arrow())
    assert df["u"].sum() == CASOS_U[receta]
    assert df.filter(~pl.col("u"))["y"].null_count() == df.filter(~pl.col("u")).height       # fuera de u, y nulo
    assert df.filter(pl.col("u"))["y"].null_count() == 0 and set(df.filter(pl.col("u"))["y"].unique()) == {0, 1}


@pytest.mark.parametrize("receta", list(RECETAS))
def test_el_verificador_completa_las_recetas_con_diseno_universo_y_los_30_territorios(ctx, con, receta):
    unidades, controles = 0, {}
    for nivel in NIVELES:
        pc = verificar(RECETAS[receta](nivel), ctx, con)
        assert not isinstance(pc, Falla), (nivel, pc)
        assert pc.ajustes == () and pc.plan.territorio.nivel == nivel                      # los 6 niveles están verificados en 2024
        assert pc.universo_analitico.id == "nino_hecho" and pc.archivo_unidad == "RECH6"
        assert (pc.diseno.archivo, pc.diseno.nivel_submuestra, pc.diseno.peso_expr) == ("RECH6", "medicion", "HV005/1e6")
        c = pc.controles
        assert c["u_antes"] == c["u_despues"] == CASOS_U[receta] and c["perdida_u"] == 0
        assert c["filas_unidad"] == c["filas_tras_uniones"] == 20290
        assert c["y_nulos_en_u"] == 0 and c["diseno_nulo_en_u"] == 0
        assert c["conglomerados_u"] > 0 and c["estratos_u"] > 0 and c["suma_pesos_u"] > 0
        unidades += c["unidades_territorio"]
        controles[nivel] = c
    assert unidades == 30                                                                   # 1 + 2 + 24 + 1 + 1 + 1
    assert controles["nacional"]["unidades_territorio"] == 1 and controles["departamento"]["unidades_territorio"] == 24


def test_el_sql_real_solo_nombra_columnas_del_indice_y_los_valores_van_como_parametros(ctx):
    indice = pl.read_parquet(RAIZ_REAL / "biblioteca" / "variables" / "variables.parquet").filter(
        (pl.col("encuesta") == "ENDES") & (pl.col("anio") == 2024))
    pares = {(a, v) for a, v in zip(indice["archivo"], indice["variable"])}
    for receta in RECETAS.values():
        for nivel in NIVELES:
            c = compilar(verificar(receta(nivel, cortes=("area",)), ctx), ctx.esquema, ctx.carpeta_microdatos)
            assert c.identificadores and c.identificadores <= pares
            citados = re.findall(r'"([^"]+)"', c.sql)
            assert set(citados) <= {a for a, _ in pares} | {v for _, v in pares} | {"corte_area"}
            assert "'" not in c.sql and c.sql.count("?") == len(c.parametros)


def test_con_cortes_y_departamentos_el_plan_respeta_el_tope_de_dominios(ctx, con):
    ok = verificar(RECETAS["anemia"]("departamento", cortes=("area",)), ctx, con)            # 24 × 3 = 72 ≤ 100
    assert not isinstance(ok, Falla) and ok.controles["dominios"] == 72
    f = verificar(RECETAS["anemia"]("departamento", cortes=("area", "sexo")), ctx, con)       # 24 × 3 × 3 = 216
    assert isinstance(f, Falla) and f.dimension == "dominios"


def test_la_conexion_endurecida_lee_los_parquet_reales_y_nada_mas(con):
    ruta = RAIZ_REAL / "biblioteca" / "microdatos" / "ENDES" / "2024" / "RECH6.parquet"
    assert con.execute("SELECT count(*) FROM read_parquet(?)", [str(ruta)]).fetchone() == (20290,)
    import duckdb
    with pytest.raises(duckdb.Error):
        con.execute("SELECT * FROM read_text('/etc/hosts')")
    with pytest.raises(duckdb.Error):
        con.execute("SELECT * FROM read_parquet(?)", [str(RAIZ_REAL / "biblioteca" / "indicadores" / "fact_indicador.parquet")])
