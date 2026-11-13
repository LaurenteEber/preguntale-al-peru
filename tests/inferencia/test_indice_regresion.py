"""M0-05, en el Mac: el índice de variables de la ENDES 2024 contra los ZIP registrados y los Parquet de M0-04.

Necesitan los ZIP del almacén de crudos y `pap microdatos convertir` + `pap variables indexar --encuesta ENDES --anio 2024`
ya corridos: si faltan, FALLAN (no se saltan; un salto daría un falso verde)."""
import json
from pathlib import Path

import duckdb
import polars as pl
import pytest
import yaml

from pap.config import Rutas
from pap.inferencia import almacen
from pap.inferencia import indice as ix
from pap.inferencia.almacen import Parametros, nombre_parquet
from pap.inferencia.indice import ParametrosIndice, construir, contar_union, verificar_relaciones
from pap.zip_seguro import abrir_zip_seguro

from conftest import RAIZ_REAL

pytestmark = [pytest.mark.regresion_microdatos, pytest.mark.solo_mac]

RUTAS = Rutas(RAIZ_REAL)
PARQUET = RAIZ_REAL / "biblioteca" / "microdatos" / "ENDES" / "2024"
INDICE = RAIZ_REAL / "biblioteca" / "variables"

REQUERIDAS = {                      # historia M0-05, tarea 8
    "RECH0": ["HHID", "HV005", "HV021", "HV022", "HV024", "HV025", "UBIGEO", "HV001"],       # HV001: «como control»
    "RECH1": ["HVIDX", "HV103"],
    "RECH6": ["HC0", "HC1", "HC55", "HC57", "HC57A", "HC70"],
    "REC0111": ["V005"],                                                                       # «como control»
}


@pytest.fixture(scope="module")
def manifiesto():
    ruta = PARQUET / "manifiesto.json"
    assert ruta.exists(), "falta biblioteca/microdatos/ENDES/2024/manifiesto.json: corre `pap microdatos convertir --encuesta ENDES --anio 2024`"
    return json.loads(ruta.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def curado():
    return ix.cargar_curado("ENDES", 2024)


@pytest.fixture(scope="module")
def metas():
    return ix.leer_zips(RUTAS, "ENDES", 2024, Parametros.desde_yaml(), log=lambda *_: None)


@pytest.fixture(scope="module")
def indice(metas, manifiesto, curado):
    return construir("ENDES", 2024, metas, manifiesto, ix.cargar_clases(), curado, ParametrosIndice.desde_yaml(), parquet_dir=PARQUET)


def _miembros_de_los_zip() -> set[str]:
    cfg = yaml.safe_load((RAIZ_REAL / "curados" / "inferencia" / "descargas" / "endes_2024.yaml").read_text(encoding="utf-8"))
    nombres = set()
    for mod in cfg["modulos"]:
        ins = almacen._insumo(RUTAS, cfg["fuente"], mod["recurso"])
        with abrir_zip_seguro(ins.ruta) as z:
            nombres |= {nombre_parquet(m, 2024) for m in z.miembros() if m.lower().endswith((".dta", ".sav"))}
    return nombres


def test_completitud_los_miembros_de_los_zip_son_los_archivos_indexados(indice, manifiesto):
    miembros = _miembros_de_los_zip()
    assert len(miembros) == 34
    assert set(indice.archivos["archivo"]) == miembros == set(manifiesto["archivos"])
    assert set(indice.variables["archivo"]) == miembros


def test_completitud_las_variables_del_indice_son_las_columnas_del_parquet_menos_anio(indice):
    for archivo in sorted(indice.archivos["archivo"]):
        cols = [c for c in duckdb.sql(f"SELECT * FROM read_parquet('{PARQUET / (archivo + '.parquet')}') LIMIT 0").columns]
        assert cols[-1] == "anio"
        en_indice = indice.variables.filter(pl.col("archivo") == archivo).sort("posicion")["variable"].to_list()
        assert en_indice == cols[:-1], archivo
        n = duckdb.sql(f"SELECT count(*) FROM read_parquet('{PARQUET / (archivo + '.parquet')}')").fetchone()[0]
        assert n == indice.archivos.filter(pl.col("archivo") == archivo)["n_filas"][0], archivo


def test_completitud_estan_las_variables_que_pide_la_historia(indice):
    for archivo, variables in REQUERIDAS.items():
        presentes = set(indice.variables.filter(pl.col("archivo") == archivo)["variable"])
        assert set(variables) <= presentes, f"{archivo}: faltan {sorted(set(variables) - presentes)}"


def test_clases_de_las_variables_clave_vienen_de_la_tabla_curada(indice):
    clase = lambda a, v: indice.variables.filter((pl.col("archivo") == a) & (pl.col("variable") == v))["clase"][0]
    assert [clase("RECH0", v) for v in ("HHID", "HV005", "HV021", "HV022", "HV024", "HV025", "UBIGEO", "HV001")] == \
        ["llave", "peso", "diseno", "diseno", "diseno", "geo", "geo", "diseno"]
    assert clase("REC0111", "V005") == "peso" and clase("REC0111", "HHID") == "llave" and clase("RECH6", "HC0") == "llave"


def test_todo_en_propuesto_y_lo_de_m1_vacio(indice):
    v = indice.variables
    assert set(v["estado"]) == {"propuesto"}
    for campo in ("texto_pregunta", "universo_cuestionario", "ventana_referencia", "sujeto", "informante", "modo",
                  "universo_corto", "rol_faltante", "tipo_origen"):
        assert v[campo].null_count() == v.height, campo
    assert indice.variables["var_id"].n_unique() == indice.variables.height


def test_cero_mojibake_sin_reparar_y_cada_reparacion_conserva_la_original(indice):
    for df in (indice.variables, indice.categorias):
        assert not [t for t in df["etiqueta_curada"] if t and ix.tiene_mojibake(t)]
        assert all("mojibake_sin_reparar" not in c for c in df["controles"])
        cambiadas = df.filter(pl.col("etiqueta_original").is_not_null() & (pl.col("etiqueta_original") != pl.col("etiqueta_curada")))
        assert cambiadas.height > 0 and all(o for o in cambiadas["etiqueta_original"])
    assert not [h for h in indice.hallazgos if h.control == "mojibake_sin_reparar"]


def test_etiqueta_vacia_solo_en_las_tres_conocidas_de_2024(indice):
    vacias = sorted({h.objeto for h in indice.hallazgos if h.control == "etiqueta_vacia"})
    assert vacias == ["ENDES·2024·RECH0·LATITUDY", "ENDES·2024·RECH0·LONGITUDX", "ENDES·2024·RECH6·HC33=5"]


def test_la_frecuencia_de_los_especiales_propuestos_se_midio_en_todos(indice):
    esp = indice.categorias.filter(pl.col("es_especial") == "propuesto")
    assert esp.height > 0 and esp["frecuencia"].null_count() == 0 and esp["origen_especial"].null_count() == 0
    assert esp["proporcion_filas"].min() >= 0 and esp["proporcion_filas"].max() <= 1
    assert indice.categorias.filter(pl.col("es_especial") == "no")["frecuencia"].null_count() == indice.categorias.filter(pl.col("es_especial") == "no").height


def test_ningun_archivo_de_2024_trae_perdidos_declarados_ni_missing_ranges(metas, manifiesto):
    """Hecho medido, no una exigencia: los 34 archivos son Stata sin .a–.z y sin rangos. El criterio «missing_ranges no vacío»
    se evidencia con un SAV sintético (tests/inferencia/test_indice_sintetico.py) y queda como consulta D-M0-05-1."""
    assert {m["formato"] for m in metas.values()} == {"dta"}
    assert not [(a, c["nombre"]) for a, m in metas.items() for c in m["columnas"] if c["rangos_perdidos"] or c["perdidos_usuario"]]
    assert not [a for a, e in manifiesto["archivos"].items() if e["perdidos"]]


def test_las_llaves_declaradas_no_se_repiten_en_ningun_archivo(curado):
    for archivo, e in curado["archivos"].items():
        cols = ", ".join(f'"{c}"' for c in e["llave"])
        n, d = duckdb.sql(f"SELECT count(*), count(DISTINCT ({cols})) FROM read_parquet('{PARQUET / (archivo + '.parquet')}')").fetchone()
        assert n == d, f"{archivo}: la llave {e['llave']} se repite ({n} filas, {d} distintas)"


def test_uniones_declaradas_sin_perdida_ni_duplicacion(curado):
    uniones = verificar_relaciones(curado, PARQUET)
    assert len(uniones) == len(curado["relaciones"]) == 52   # 44 + CSALUD01 → RECH1 (C-M1-06-1) + 6 hijos → REC21 y RECH4 → RECH1 (M1-07)
    malas = [u for u in uniones if not u.sin_perdida_ni_duplicacion]
    assert not malas, malas
    por = {(u.hijo, u.padre): u for u in uniones}
    u = por[("RECH6", "RECH1")]
    assert (u.filas_hijo, u.filas_union, u.filas_con_pareja) == (20290, 20290, 20290)       # HHID + HC0 = HVIDX
    u = por[("RECH1", "RECH0")]
    assert (u.filas_hijo, u.filas_union, u.llaves_repetidas_padre) == (135045, 135045, 0)   # HHID
    u = por[("REC0111", "RECH0")]
    assert (u.filas_hijo, u.filas_union, u.filas_con_pareja) == (37117, 37117, 37117)       # HHID derivado de CASEID


def test_rec93_no_se_une_a_rec0111_porque_341_filas_no_tienen_a_la_mujer():
    """C-M0-05-2: se mide y se deja anotado; la unión no se declara."""
    u = contar_union(PARQUET / "REC93DVdisciplina.parquet", PARQUET / "REC0111.parquet", [["CASEID", "CASEID"]])
    assert (u.filas_hijo, u.filas_union, u.filas_con_pareja) == (15462, 15462, 15121)
    assert not u.sin_perdida_ni_duplicacion


def test_los_archivos_escritos_son_los_del_indice_calculado(indice):
    for nombre in ("archivos", "variables", "categorias"):
        ruta = INDICE / f"{nombre}.parquet"
        assert ruta.exists(), f"falta {ruta}: corre `pap variables indexar --encuesta ENDES --anio 2024`"
        calculado = (getattr(indice, nombre).sort("archivo") if nombre == "archivos" else
                     getattr(indice, nombre).sort("var_id") if nombre == "variables" else getattr(indice, nombre))
        escrito = pl.read_parquet(ruta)
        # Columnas que agregan otros comandos al índice ya escrito: `bloque_id` (pap fichas generar, M1-06) y las tres de
        # `pap cuestionarios aplicar` (M1-04). Las demás, incluida `clase` (M1-05 tarea 0), son exactamente las que da la reindexación.
        extras = set(escrito.columns) - set(calculado.columns)
        assert extras <= {"bloque_id", "pregunta_ref", "vinculo_metodo", "sin_pregunta"}, extras
        if "vinculo_metodo" in escrito.columns:
            # `pap cuestionarios aplicar` además llena `texto_pregunta` en las variables vinculadas (M1-04); las demás quedan como
            # las da la reindexación, y todas las otras columnas son idénticas
            escrito = escrito.sort("var_id")
            sin_vinculo = escrito["pregunta_ref"].is_null().to_list()
            assert [t for t, s in zip(escrito["texto_pregunta"], sin_vinculo) if s] == \
                [t for t, s in zip(calculado["texto_pregunta"], sin_vinculo) if s]
            cols = [c for c in calculado.columns if c != "texto_pregunta"]
            assert escrito.select(cols).equals(calculado.select(cols))
            continue
        assert escrito.select(calculado.columns).equals(calculado)
