"""Escritura determinista de tablas curadas: Parquet (zstd, ordenado por clave) + manifiesto con huellas."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import duckdb
import pandas as pd

from .. import __version__
from ..config import Rutas
from ..util import ahora, escribir_json, git, sha256

CLAVES = {
    "dim_ubigeo_historico": "ubigeo_inei, vigente_desde",
    "rel_ubigeo_origen": "ubigeo_hijo, ubigeo_origen",
    "puente_ubigeo": "ubigeo_inei",
    "dim_ambito": "ambito_id",
    "dim_dominio": "encuesta_id, anio, dominio_id",
    "dim_ipc": "anio, mes",
    "dim_establecimiento_salud": "cod_ipress",
    "dim_unidad_ejecutora": "anio, sec_ejec",
    "dim_inversion_ubicacion": "cui",
    # pieza C (rondas 1-2): dim_tema_gasto v1.2 y capa de trazabilidad
    "dim_tema_gasto": "anio, tema_id, programa_ppto, funcion, division_funcional, sec_ejec, actividad_accion_obra",
    "dim_programa": "programa_ppto, anio",
    "dim_producto": "anio, programa_ppto, producto_proyecto",
    "dim_actividad": "anio, programa_ppto, producto_proyecto, actividad_accion_obra",
    "dim_concepto": "concepto_id",
    "rel_concepto_grupo": "grupo_id, concepto_id",
    "rel_concepto_nodo": "anio, concepto_id, programa_ppto, producto_proyecto, actividad_accion_obra, sec_ejec, funcion",
    "rel_linaje": "id_evento",
    "rel_programa_politica": "origen, destino, relacion",
    "dim_programa_social": "id_programa_social, anio",
    "rel_programa_social_ejecutora": "id_programa_social, sec_ejec, actividad_accion_obra",
    "rel_programa_social_linea_aparte": "id_programa_social, linea_aparte_id, sec_ejec, clasificador_gasto",
    "rel_programa_social_financiamiento": "anio, id_programa_social, programa_ppto, producto_proyecto, tipo_act_proy",
    "cobertura_por_anio": "concepto_id, anio",
    "dim_glosario_gasto": "id",
    "fact_gasto_territorial": "anio, mes, nivel_atribucion, ubigeo_atribucion, ambito_id, sec_ejec, departamento_meta, programa_ppto, producto_proyecto, actividad_accion_obra, funcion, division_funcional, grupo_funcional, categoria_gasto, generica, clasificador_gasto, fuente_financiamiento, rubro, tipo_act_proy, categoria_transferencia",
    "fact_sien_hb_ubigeo": "anio, id_insumo, cod_ipress, ubigeo_eess, ubigeo_procedencia, ubigeo_ref_altitud, grupo_edad",
    "fact_poblacion": "fuente_id, vintage, metodo, geografia_base, ubigeo_inei, anio, sexo, edad_min, edad_max",
    "fact_poblacion_grupo": "fuente_id, vintage, metodo, geografia_base, ubigeo_inei, anio, sexo, grupo_id",
    "puente_geo2017": "grupo_comparable_geo2017, ubigeo_2017",
    # S4 (9/10/2026): insumos del piloto estandarizados (biblioteca/estandarizada/)
    "endes_nino": "anio, id_hogar, idx_nino",
    "enaho_sumaria": "anio, id_conglomerado, vivienda, hogar",
    "fact_mapa_pobreza": "edicion, nivel, ubigeo_inei",
    # Piloto (9/10/2026): tablas curadas de indicadores (biblioteca/dimensiones/)
    "dim_indicador": "indicador_id",
    "cruces_permitidos": "id_cruce",
    "cifras_doradas": "id_cifra",
    # Piloto P1 (10/10/2026): cubo de indicadores (biblioteca/indicadores/)
    "fact_indicador": "indicador_id, anio, nivel, territorio_id, medida, linea",
}

# Carpeta de destino por sprint: la capa 0 va a dimensiones/; los insumos estandarizados, a estandarizada/<tema>/
DESTINOS = {
    "s4_endes": ("estandarizada", "encuestas"),
    "s4_enaho": ("estandarizada", "encuestas"),
    "s4_mapa_pobreza": ("estandarizada", "mapa_pobreza"),
    "p1_indicadores": ("indicadores",),
}


def carpeta(rutas: Rutas, sprint: str | None = None) -> Path:
    if sprint in DESTINOS:
        return rutas.raiz / "biblioteca" / Path(*DESTINOS[sprint])
    return rutas.raiz / "biblioteca" / "dimensiones"


def carpetas_con_manifiesto(rutas: Rutas) -> list[Path]:
    """Todas las carpetas donde un sprint deja tablas y manifiesto (para insumos.tabla)."""
    vistas = [carpeta(rutas)] + [carpeta(rutas, s) for s in DESTINOS]
    return list(dict.fromkeys(vistas))


ENTEROS = ("anio", "mes", "edad_min", "edad_max", "anio_datos_desde", "anio_datos_hasta", "meses_min", "meses_max")


def escribir_parquet(df: pd.DataFrame, ruta: Path, orden: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_name(ruta.name + ".tmp")
    # Tipos homogéneos entre tablas (SP-07): años, meses y edades como INTEGER; el cast se hace en DuckDB para no
    # copiar en memoria tablas grandes (fact_poblacion tiene ~6 M de filas)
    cols = ", ".join(f'CAST("{c}" AS INTEGER) AS "{c}"' if c in ENTEROS else f'"{c}"' for c in df.columns)
    con = duckdb.connect()
    try:
        con.execute("SET threads TO 1")
        con.register("t", df)
        con.execute(f"COPY (SELECT {cols} FROM t ORDER BY {orden}) TO '{tmp}' (FORMAT parquet, COMPRESSION zstd)")
    finally:
        con.close()
    tmp.replace(ruta)


def guardar(rutas: Rutas, sprint: str, tablas: dict[str, pd.DataFrame], pruebas: list[dict],
            revision: dict[str, pd.DataFrame], insumos: list) -> Path:
    base = carpeta(rutas, sprint)
    base.mkdir(parents=True, exist_ok=True)
    # RP-07: todo se escribe primero en una carpeta de preparación y se mueve al final (manifiesto el último);
    # una construcción interrumpida no deja una mezcla de tablas nuevas y viejas.
    prep = base / f".preparacion_{sprint}_{os.getpid()}"
    if prep.exists():
        shutil.rmtree(prep)
    (prep / "revision").mkdir(parents=True)
    try:
        return _guardar(rutas, sprint, tablas, pruebas, revision, insumos, base, prep)
    finally:
        shutil.rmtree(prep, ignore_errors=True)
        for t in tablas.values():  # temporales de constructores (p. ej. gasto) que no llegaron a moverse
            if isinstance(t, Path):
                t.unlink(missing_ok=True)


def _guardar(rutas, sprint, tablas, pruebas, revision, insumos, base, prep) -> Path:
    registro = {}
    for nombre, df in tablas.items():
        ruta = prep / f"{nombre}.parquet"
        if isinstance(df, Path):
            # Parquet ya escrito y ordenado por el constructor (tablas grandes con montos DECIMAL)
            df.replace(ruta)
            con = duckdb.connect()
            try:
                filas = con.execute(f"SELECT count(*) FROM '{ruta}'").fetchone()[0]
                columnas = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM '{ruta}'").fetchall()]
            finally:
                con.close()
        else:
            escribir_parquet(df, ruta, CLAVES[nombre])
            filas, columnas = len(df), list(df.columns)
        registro[nombre] = {"archivo": ruta.name, "filas": int(filas), "hash": f"sha256:{sha256(ruta)}",
                            "columnas": columnas, "orden": CLAVES[nombre]}
    for nombre, df in revision.items():
        df.to_csv(prep / "revision" / f"{nombre}.csv", index=False, encoding="utf-8")
    manifiesto = {
        "sprint": sprint,
        "construido": ahora(),
        "codigo": {"pap": __version__, "commit": git(rutas.raiz, "rev-parse", "--short", "HEAD"),
                   "sucio": bool(git(rutas.raiz, "status", "--porcelain", "--", "src", "curados", "tests", "catalogo/scripts", ":!curados/insumos.lock.yaml"))},
        # RP-12: la huella de un Parquet depende de la versión de DuckDB (created_by)
        "bibliotecas": {"duckdb": duckdb.__version__, "pandas": pd.__version__},
        "insumos": [{"source_id": i.source_id, "recurso": i.nombre, "hash": i.hash,
                     "archivo_original": i.original_filename} for i in insumos],
        "tablas": registro,
        "pruebas": {"total": len(pruebas), "fallidas": [p["id"] for p in pruebas if not p["ok"]],
                    "bloqueantes_fallidas": [p["id"] for p in pruebas if not p["ok"] and p["bloqueante"]]},
    }
    escribir_json(prep / f"pruebas_{sprint}.json", json.loads(json.dumps(pruebas, default=str)))
    escribir_json(prep / f"manifiesto_{sprint}.json", manifiesto)
    # mover: tablas, revisión, pruebas y, al final, el manifiesto (el anterior queda en historial/)
    anterior = base / f"manifiesto_{sprint}.json"
    if anterior.exists():
        (base / "historial").mkdir(exist_ok=True)
        previo = json.loads(anterior.read_text(encoding="utf-8"))
        marca = previo.get("construido", "sin_fecha").replace(":", "")
        shutil.copyfile(anterior, base / "historial" / f"manifiesto_{sprint}_{marca}.json")
    (base / "revision").mkdir(exist_ok=True)
    for r in sorted(registro):
        os.replace(prep / f"{r}.parquet", base / f"{r}.parquet")
    for f in sorted((prep / "revision").iterdir()):
        os.replace(f, base / "revision" / f.name)
    os.replace(prep / f"pruebas_{sprint}.json", base / f"pruebas_{sprint}.json")
    os.replace(prep / f"manifiesto_{sprint}.json", base / f"manifiesto_{sprint}.json")
    shutil.rmtree(prep, ignore_errors=True)
    return base / f"manifiesto_{sprint}.json"
