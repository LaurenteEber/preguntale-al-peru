"""M1-05, tarea 0: la clase de cada variable del índice (regla por tipo de valor y número de categorías + lista curada de excepciones).

Las pruebas con datos sintéticos corren en cualquier equipo; las del índice real (`biblioteca/variables/`) llevan las marcas
`solo_mac` y `regresion_microdatos` y FALLAN si el índice falta (no se saltan)."""
import hashlib
import json
from pathlib import Path

import polars as pl
import pytest
import yaml

from pap.errores import PapError
from pap.inferencia import clases_indice as ci

from conftest import RAIZ_REAL

INDICE = RAIZ_REAL / "biblioteca" / "variables"
RUTA_EXC = RAIZ_REAL / "curados" / "inferencia" / "clases_excepciones.yaml"


def _v(archivo, variable, tipo, n_cat=0, clase=None):
    return {"var_id": f"ENDES·2024·{archivo}·{variable}", "archivo": archivo, "variable": variable, "tipo_valor": tipo,
            "n_categorias": n_cat, "clase": clase, "etiqueta_curada": f"etq {variable}"}


def _c(archivo, variable, codigo, especial):
    return {"var_id": f"ENDES·2024·{archivo}·{variable}", "codigo": codigo, "es_especial": "propuesto" if especial else "no"}


def _datos():
    vs = pl.DataFrame([
        _v("T1", "HHID", "texto"), _v("T1", "IDX", "numerica"), _v("T1", "P1", "categorica", 3), _v("T1", "P2", "categorica", 2),
        _v("T1", "EDAD", "categorica", 1), _v("T1", "FLAG", "categorica", 2), _v("T1", "PESO", "numerica"), _v("T1", "OBS", "texto"),
        _v("T1", "ID1", "numerica"), _v("T1", "NOMBRE", "texto"), _v("T1", "FEC", "fecha"), _v("T1", "HV005", "numerica")],
        schema={"var_id": pl.String, "archivo": pl.String, "variable": pl.String, "tipo_valor": pl.String, "n_categorias": pl.Int32,
                "clase": pl.String, "etiqueta_curada": pl.String})
    cs = pl.DataFrame([
        _c("T1", "P1", "1", False), _c("T1", "P1", "2", False), _c("T1", "P1", "9", True),
        _c("T1", "P2", "1", False), _c("T1", "P2", "2", False), _c("T1", "P2", "8", True),
        _c("T1", "EDAD", "98", True),
        _c("T1", "FLAG", "1", False), _c("T1", "FLAG", "8", True)],
        schema={"var_id": pl.String, "codigo": pl.String, "es_especial": pl.String})
    ar = pl.DataFrame([{"archivo": "T1", "llave": ["HHID", "IDX"]}], schema={"archivo": pl.String, "llave": pl.List(pl.String)})
    curadas = {"HV005": {"clase": "peso"}, "HHID": {"clase": "llave"}}
    exc = [{"variables": ["FLAG"], "archivos": ["T1"], "clase": "categoria", "motivo": "marca de una sola etiqueta"},
           {"variables": ["ID1"], "archivos": "*", "clase": "diseno", "motivo": "año de la encuesta"},
           {"variables": ["NOMBRE"], "archivos": ["T1"], "clase": "geo", "motivo": "nombre de lugar"}]
    return vs, cs, ar, curadas, exc


def _clase(df):
    return {r["variable"]: r["clase"] for r in df.iter_rows(named=True)}


def test_reglas_por_tipo_de_valor_y_numero_de_categorias():
    vs, cs, ar, curadas, exc = _datos()
    k = _clase(ci.clasificar(vs, cs, ar, curadas, exc))
    assert k["P1"] == "categoria" and k["P2"] == "categoria"        # dos o más categorías con sentido
    assert k["EDAD"] == "medida"                                   # solo códigos especiales: el número es la medida
    assert k["PESO"] == "medida" and k["FEC"] == "medida"          # numérica sin etiquetas
    assert k["OBS"] == "texto"                                     # texto que no es llave ni lugar


def test_la_llave_del_archivo_y_la_tabla_curada_ganan_a_la_regla():
    vs, cs, ar, curadas, exc = _datos()
    k = _clase(ci.clasificar(vs, cs, ar, curadas, exc))
    assert k["HHID"] == "llave" and k["IDX"] == "llave"            # IDX: llave declarada en archivos_*.yaml aunque no esté en clases_columnas
    assert k["HV005"] == "peso"


def test_las_excepciones_mandan_sobre_la_regla():
    vs, cs, ar, curadas, exc = _datos()
    k = _clase(ci.clasificar(vs, cs, ar, curadas, exc))
    assert k["FLAG"] == "categoria" and k["ID1"] == "diseno" and k["NOMBRE"] == "geo"
    k2 = _clase(ci.clasificar(vs, cs, ar, curadas, []))
    assert k2["FLAG"] == "medida" and k2["NOMBRE"] == "texto"      # sin la excepción, la regla da otra clase


def test_ninguna_variable_queda_sin_clase_y_solo_cambia_la_columna_clase():
    vs, cs, ar, curadas, exc = _datos()
    out = ci.clasificar(vs, cs, ar, curadas, exc)
    assert out["clase"].null_count() == 0 and set(out["clase"]) <= set(ci.CLASES)
    assert out.drop("clase").equals(vs.drop("clase")) and out.columns == vs.columns


def test_clasificar_es_idempotente_y_no_depende_de_la_clase_que_ya_traia():
    vs, cs, ar, curadas, exc = _datos()
    una = ci.clasificar(vs, cs, ar, curadas, exc)
    otra = ci.clasificar(una, cs, ar, curadas, exc)
    assert una.equals(otra)
    sucia = vs.with_columns(pl.lit("medida").alias("clase"))
    assert ci.clasificar(sucia, cs, ar, curadas, exc).equals(una)


def test_excepciones_validas(tmp_path):
    vs, cs, ar, curadas, exc = _datos()
    ci.validar_excepciones(vs, exc)
    with pytest.raises(PapError, match="clase"):
        ci.validar_excepciones(vs, [{"variables": ["P1"], "archivos": ["T1"], "clase": "inventada", "motivo": "x"}])
    with pytest.raises(PapError, match="motivo"):
        ci.validar_excepciones(vs, [{"variables": ["P1"], "archivos": ["T1"], "clase": "medida", "motivo": ""}])
    with pytest.raises(PapError, match="no existe"):
        ci.validar_excepciones(vs, [{"variables": ["NOEXISTE"], "archivos": ["T1"], "clase": "medida", "motivo": "x"}])
    with pytest.raises(PapError, match="dos excepciones"):
        ci.validar_excepciones(vs, exc + [{"variables": ["FLAG"], "archivos": "*", "clase": "medida", "motivo": "x"}])


def test_conteos_por_clase_y_por_tabla():
    vs, cs, ar, curadas, exc = _datos()
    c = ci.conteos(ci.clasificar(vs, cs, ar, curadas, exc))
    assert c["total"]["categoria"] == 3 and c["total"]["medida"] == 3 and sum(c["total"].values()) == vs.height
    assert c["por_tabla"]["T1"]["llave"] == 2 and sum(c["por_tabla"]["T1"].values()) == vs.height


def test_informe_en_texto_trae_los_conteos_y_las_excepciones():
    vs, cs, ar, curadas, exc = _datos()
    out = ci.clasificar(vs, cs, ar, curadas, exc)
    txt = ci.informe(out, exc)
    assert "| T1 |" in txt and "categoria" in txt and "marca de una sola etiqueta" in txt


def test_construir_deja_clase_en_todas_las_variables(tmp_path):
    # `indice.construir` aplica la misma clasificación: reindexar da lo mismo que `pap variables clasificar`.
    from .test_indice_sintetico import CLASES, PI, _sintetico
    from pap.inferencia.indice import construir

    metas, man, curado = _sintetico(tmp_path)
    v = construir("ENDES", 2024, metas, man, CLASES, curado, PI, parquet_dir=tmp_path).variables
    assert v["clase"].null_count() == 0
    por = {(r["archivo"], r["variable"]): r["clase"] for r in v.iter_rows(named=True)}
    assert por[("RECH1", "HV108")] == "categoria"        # 1, 3 y 8 con sentido (y 98 especial)
    assert por[("RECH1", "HV109")] == "medida"           # una sola etiqueta con sentido («Sí») y un especial: la regla lo deja como medida
    assert por[("RECH0", "SH61A")] == "medida"           # numérica sin etiquetas


def test_aplicar_al_indice_cambia_solo_clase_y_dos_corridas_dan_el_mismo_archivo(tmp_path):
    vs, cs, ar, curadas, exc = _datos()
    extra = vs.with_columns(pl.lit("x").alias("pregunta_ref")).sort("var_id", descending=True)    # columna de M1-04 y otro orden
    extra.write_parquet(tmp_path / "variables.parquet")
    cs.write_parquet(tmp_path / "categorias.parquet")
    ar.write_parquet(tmp_path / "archivos.parquet")
    informe = tmp_path / "clases.md"
    c = ci.aplicar_al_indice(tmp_path, curadas, exc, informe)
    primero = (tmp_path / "variables.parquet").read_bytes()
    ci.aplicar_al_indice(tmp_path, curadas, exc)
    assert (tmp_path / "variables.parquet").read_bytes() == primero
    despues = pl.read_parquet(tmp_path / "variables.parquet")
    assert despues["pregunta_ref"].to_list() == ["x"] * vs.height and despues["clase"].null_count() == 0
    assert despues.drop("clase").equals(extra.sort("var_id").drop("clase"))
    assert c["total"]["categoria"] == 3 and informe.read_text(encoding="utf-8").startswith("| Clase |")


def test_pap_variables_clasificar_figura_en_la_ayuda():
    import subprocess, sys
    r = subprocess.run([sys.executable, "-c", "import sys; from pap.cli import main; sys.exit(main(['variables', '--help']))"],
                       capture_output=True, text=True, cwd=RAIZ_REAL)
    assert r.returncode == 0 and "clasificar" in r.stdout and "--informe" in r.stdout


def test_categorica_con_muchos_valores_sin_etiqueta_es_medida(tmp_path):
    # Ronda del auditor: solo están etiquetados los bordes (0, 95, 98); el número es la medida.
    vs = pl.DataFrame([_v("T1", "CANT", "categorica", 3), _v("T1", "FUM", "categorica", 3)],
                      schema={"var_id": pl.String, "archivo": pl.String, "variable": pl.String, "tipo_valor": pl.String, "n_categorias": pl.Int32,
                              "clase": pl.String, "etiqueta_curada": pl.String})
    cs = pl.DataFrame([_c("T1", "CANT", "0", False), _c("T1", "CANT", "1", False), _c("T1", "CANT", "98", True),
                       _c("T1", "FUM", "1", False), _c("T1", "FUM", "2", False), _c("T1", "FUM", "9", True)],
                      schema={"var_id": pl.String, "codigo": pl.String, "es_especial": pl.String})
    ar = pl.DataFrame([{"archivo": "T1", "llave": []}], schema={"archivo": pl.String, "llave": pl.List(pl.String)})
    pl.DataFrame({"CANT": [float(i) for i in range(20)] + [98.0, None], "FUM": [1.0, 2.0] * 11}).write_parquet(tmp_path / "T1.parquet")
    sin = ci.contar_sin_etiqueta(tmp_path, vs, cs)
    assert sin == {"ENDES·2024·T1·CANT": 18, "ENDES·2024·T1·FUM": 0}
    k = _clase(ci.clasificar(vs, cs, ar, {}, [], sin, 15))
    assert k == {"CANT": "medida", "FUM": "categoria"}
    assert _clase(ci.clasificar(vs, cs, ar, {}, []))["CANT"] == "categoria"        # sin datos la regla no actúa


# ------------------------------------------------------------------ el índice real (Mac)

real = [pytest.mark.regresion_microdatos, pytest.mark.solo_mac]


@pytest.mark.regresion_microdatos
@pytest.mark.solo_mac
def test_indice_real_sin_variables_sin_clase_y_con_las_excepciones_aplicadas():
    v = pl.read_parquet(INDICE / "variables.parquet")
    c = pl.read_parquet(INDICE / "categorias.parquet")
    a = pl.read_parquet(INDICE / "archivos.parquet")
    exc = ci.cargar_excepciones(RUTA_EXC)
    ci.validar_excepciones(v, exc)
    from pap.inferencia import indice as ix
    reglas = ci.cargar_reglas(RUTA_EXC)
    sin = ci.contar_sin_etiqueta(RAIZ_REAL / "biblioteca" / "microdatos" / "ENDES" / "2024", v, c)
    esperado = ci.clasificar(v, c, a, ix.cargar_clases(), exc, sin, reglas["min_valores_sin_etiqueta"])
    assert v["clase"].null_count() == 0 and set(v["clase"]) <= set(ci.CLASES)
    assert v["clase"].to_list() == esperado["clase"].to_list()                  # lo guardado es lo que da la regla hoy
    cuenta = ci.conteos(v)["total"]
    assert sum(cuenta.values()) == 2856
    assert cuenta["categoria"] + cuenta["medida"] > 2500


@pytest.mark.regresion_microdatos
@pytest.mark.solo_mac
def test_las_clases_de_la_tabla_curada_no_cambiaron():
    # No se toca clases_columnas.yaml: las 86 variables con clase curada la conservan en el índice.
    from pap.inferencia import indice as ix
    v = pl.read_parquet(INDICE / "variables.parquet")
    cur = ix.cargar_clases()
    for r in v.iter_rows(named=True):
        k = cur.get(r["variable"])
        if k:
            assert r["clase"] == (k.get("clase_indice") or k["clase"]), r["var_id"]
