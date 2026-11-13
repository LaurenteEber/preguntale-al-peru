"""M0-05: índice de variables con archivos sintéticos (sin los datos reales del INEI)."""
from pap.inferencia.tablas_curadas import CARDINALIDADES
import json
import subprocess
from pathlib import Path

import pandas as pd
import polars as pl
import pyreadstat
import pytest
import yaml

from pap.config import Rutas
from pap.errores import PapError
from pap.inferencia import indice as ix
from pap.inferencia.almacen import Parametros
from pap.inferencia.indice import (Hallazgo, ParametrosIndice, construir, contar_codigos, contar_union, control_etiquetas_entre_anios,
                                   control_frecuencia_entre_anios, control_universo, coincidencia_universo,
                                   coincidencia_universo_parquet, curar_etiqueta, escribir, leer_metadatos_archivo,
                                   proponer_especiales, reparar_dos, tiene_mojibake, verificar_relaciones)

from conftest import RAIZ_REAL

P = Parametros.desde_yaml()
PI = ParametrosIndice.desde_yaml()


# ------------------------------------------------------------------ etiquetas

def test_etiqueta_con_mojibake_utf8_se_repara_y_la_original_se_conserva():
    original = "NiÃ±o menor de aÃ±os"          # UTF-8 leído como cp1252
    curada, hechas = curar_etiqueta(original)
    assert curada == "Niño menor de años" and "mojibake" in hechas
    assert not tiene_mojibake(curada) and tiene_mojibake(original)


def test_etiqueta_con_mojibake_de_dos_cp850_se_relee_como_cp850():
    assert reparar_dos("Ni¤o menor de 5 a¤os") == "Niño menor de 5 años" and reparar_dos("Educaci¢n") == "Educación"
    assert reparar_dos("Niño ¤") == "Niño ¤"           # ya trae tildes bien escritas: ambiguo, no se toca
    curada, hechas = curar_etiqueta("Ni¤o")
    assert curada == "Niño" and "mojibake" in hechas
    assert reparar_dos("日本 ¤") == "日本 ¤"        # si no se puede codificar en cp1252, queda igual
    assert tiene_mojibake("Ni¤o")


def test_reparar_dos_no_corrompe_signos_del_espanol_ni_otros_caracteres_H05_1():
    # H05-1: releer todo el texto como cp850 convertía «¿» en «┐» y «¡» en «í»
    assert reparar_dos("¿Ni¤o?") == "¿Niño?"
    assert reparar_dos("¡A¤o nuevo!") == "¡Año nuevo!"
    assert reparar_dos("Educaci¢n f¡sica") == "Educación física"      # «¡» dentro de la palabra sí es «í» de DOS
    assert reparar_dos("Beb‚ ¿ni¤o?") == "Bebé ¿niño?"
    assert reparar_dos("N£mero: 50 %") == "Número: 50 %"
    assert reparar_dos("Precio ¢ 5") == "Precio ¢ 5"                  # suelto, sin letra al lado: no se toca
    curada, hechas = curar_etiqueta("¿Cu ntos ni¤os?")
    assert "┐" not in curada and curada.startswith("¿") and "niños" in curada and "mojibake" in hechas


def test_control_de_mojibake_ve_los_dibujos_de_caja_de_una_relectura_cp850_H05_1():
    assert tiene_mojibake("┐Niño?") and tiene_mojibake("Educaci│n") and tiene_mojibake("Ni░o")
    assert not tiene_mojibake("¿Niño?")


def test_etiqueta_normaliza_espacios_nbsp_y_nfc_sin_tocar_comillas_ni_acentos():
    assert curar_etiqueta("\xa0Otro") == ("Otro", ("espacios",))
    assert curar_etiqueta("Día - Control  1") == ("Día - Control 1", ("espacios",))
    assert curar_etiqueta("Año") == ("Año", ())
    assert curar_etiqueta("ña")[0] == "ña"                      # n + tilde combinada → ñ (NFC)
    assert curar_etiqueta("dice “bebé llora”")[0] == "dice “bebé llora”"       # comillas tipográficas intactas
    assert curar_etiqueta("A &amp; B")[0] == "A &amp; B"                         # sin deshacer entidades HTML
    assert curar_etiqueta(None) == ("", ()) and curar_etiqueta("") == ("", ())


def test_etiqueta_con_errata_de_acento_grave_no_se_corrige_sola_pero_se_marca():
    assert curar_etiqueta("Querìa esperar") == ("Querìa esperar", ())
    assert not tiene_mojibake("Querìa esperar")


# ------------------------------------------------------------------ códigos especiales

def _col(nombre="P1", etiquetas=(), rangos=(), usuario=()):
    return {"nombre": nombre, "etiqueta": "x", "formato": "%12.0g", "etiquetas_valor": [list(e) for e in etiquetas],
            "rangos_perdidos": list(rangos), "perdidos_usuario": list(usuario)}


def test_especiales_por_etiqueta_y_por_codigo_98_99_con_etiqueta():
    col = _col(etiquetas=[(1, "Sí"), (2, "No"), (8, "No sabe/No recuerda"), (9, "NO RESPONDE"), (7, "No aplicable"),
                          (98, "Otro"), (99, "Sin dato"), (3, "Cada día")])
    esp = {s["codigo"]: s for s in proponer_especiales(col, None, PI)}
    assert set(esp) == {"8", "9", "7", "98", "99"}                       # 1, 2 y 3 no
    assert all(s["origen"] == "etiqueta" for s in esp.values())


def test_especiales_declarados_por_rango_spss_perdidos_de_stata_y_manifiesto():
    col = _col(etiquetas=[(1, "Sí"), (98, "No sabe"), (997, "Otra")], rangos=[{"lo": 997, "hi": 999}, {"lo": 5, "hi": 5}],
               usuario=["a"])
    esp = {s["codigo"]: s for s in proponer_especiales(col, {"declarados": ["b"], "conteo": {"b": 3}}, PI)}
    assert esp["98"]["origen"] == "etiqueta"
    assert esp["997"]["origen"] == "declarado"                                # con etiqueta y dentro del rango
    assert esp["5"]["origen"] == "declarado" and esp["5"]["etiqueta"] == ""   # suelto, sin etiqueta de valor
    assert esp["a"]["origen"] == "declarado" and esp["b"]["declarado_conteo"] == 3
    assert esp["997..999"]["rango"] is True
    assert "1" not in esp


def test_codigo_texto_unifica_98_98punto0_y_texto():
    assert [ix.codigo_texto(x) for x in (98, 98.0, "98.0", "a", 1.5)] == ["98", "98", "98", "a", "1.5"]


# ------------------------------------------------------------------ controles de varios años y del universo

def test_control_de_etiqueta_distinta_entre_anios_ignora_estilo_pero_no_texto():
    assert control_etiquetas_entre_anios("v", {2023: "¿Vive aquí?", 2024: "¿vive  aqui?"}) is None
    h = control_etiquetas_entre_anios("ENDES·x·P1", {2023: "Tiene seguro", 2024: "Tiene seguro integral"})
    assert h.control == "etiqueta_cambia_entre_anios" and "2023" in h.detalle and "2024" in h.detalle


def test_control_de_frecuencia_de_especiales_entre_anios():
    assert control_frecuencia_entre_anios("c", {2023: 0.010, 2024: 0.012}, PI) is None
    assert control_frecuencia_entre_anios("c", {2023: 0.0001, 2024: 0.0003}, PI) is None            # ×3 pero 0,02 pp
    h = control_frecuencia_entre_anios("c", {2022: 0.010, 2023: 0.011, 2024: 0.050}, PI)
    assert h.control == "frecuencia_especial_cambia_entre_anios" and "2024" in h.detalle
    assert control_frecuencia_entre_anios("c", {2023: 0.0, 2024: 0.05}, PI) is not None              # aparece de la nada
    assert control_frecuencia_entre_anios("c", {2023: 0.0, 2024: 0.0}, PI) is None


def test_control_universo_contra_los_datos_con_el_umbral_de_99_5():
    n = 1000
    universo = [True] * 600 + [False] * 400
    con_valor = list(universo)
    assert coincidencia_universo(universo, con_valor) == 1.0
    assert control_universo("v", universo, con_valor, PI) is None
    con_valor[0] = False; con_valor[1] = False; con_valor[999] = True            # 3 de 1000 = 99,7 %
    assert control_universo("v", universo, con_valor, PI) is None
    for i in range(2, 8):
        con_valor[i] = False                                                      # 9 de 1000 = 99,1 %
    h = control_universo("ENDES·x·P1", universo, con_valor, PI)
    assert h.control == "universo_no_coincide" and "99.1" in h.detalle
    with pytest.raises(PapError):
        coincidencia_universo([True], [True, False])


def test_control_universo_sobre_un_parquet(tmp_path):
    ruta = tmp_path / "u.parquet"
    pl.DataFrame({"EDAD": [0, 1, 5, 20, 30], "P1": [None, None, 1.0, 2.0, None]}).write_parquet(ruta)
    assert coincidencia_universo_parquet(ruta, "P1", "EDAD >= 5") == pytest.approx(0.8)      # la fila de 30 años no responde
    assert coincidencia_universo_parquet(ruta, "P1", "EDAD >= 5 AND EDAD < 30") == 1.0


# ------------------------------------------------------------------ lector aislado de metadatos

def test_lector_aislado_ve_missing_ranges_de_un_sav(tmp_path):
    """Sin user_missing=True, `missing_ranges` sale vacío: este es el mecanismo del criterio «missing_ranges no vacío»."""
    df = pd.DataFrame({"AÑO_NAC": [1990.0, 98.0, 99.0, 2001.0], "SEXO": [1.0, 2.0, 1.0, 2.0]})
    ruta = tmp_path / "s.sav"
    pyreadstat.write_sav(df, str(ruta), missing_ranges={"AÑO_NAC": [98, 99]}, variable_value_labels={"SEXO": {1: "Hombre", 2: "Mujer"}},
                         column_labels=["Año de nacimiento", "Sexo"])
    _, sin = pyreadstat.read_sav(str(ruta), metadataonly=True)
    assert not sin.missing_ranges                                                # sin la opción, vacío
    m = leer_metadatos_archivo(ruta, "sav", P)
    por = {c["nombre"]: c for c in m["columnas"]}
    assert m["filas"] == 4 and por["AÑO_NAC"]["rangos_perdidos"] == [{"lo": 98.0, "hi": 98.0}, {"lo": 99.0, "hi": 99.0}]
    assert por["AÑO_NAC"]["etiqueta"] == "Año de nacimiento"
    assert por["SEXO"]["etiquetas_valor"] == [[1, "Hombre"], [2, "Mujer"]] and por["SEXO"]["rangos_perdidos"] == []
    esp = {s["codigo"]: s for s in proponer_especiales(por["AÑO_NAC"], None, PI)}
    assert esp and all(s["origen"] == "declarado" for s in esp.values())


def test_lector_aislado_sin_tope_de_etiquetas_y_con_dta(tmp_path):
    n = 2500
    df = pd.DataFrame({"P1": [float(i % n + 1) for i in range(n)]})
    ruta = tmp_path / "e.dta"
    pyreadstat.write_dta(df, str(ruta), version=15, variable_value_labels={"P1": {i + 1: f"Opción {i + 1}" for i in range(n)}})
    m = leer_metadatos_archivo(ruta, "dta", P)
    assert len(m["columnas"][0]["etiquetas_valor"]) == n and m["filas"] == n and m["release_dta"] >= 118


def test_lector_de_metadatos_rechaza_un_formato_desconocido(tmp_path):
    with pytest.raises(PapError, match="formato no soportado"):
        leer_metadatos_archivo(tmp_path / "x.csv", "csv", P)


# ------------------------------------------------------------------ construcción del índice

CLASES = {"HHID": {"clase": "llave", "ancho": 9}, "CASEID": {"clase": "llave", "ancho": 12, "deriva": {"HHID": {"quitar_final": 3}}},
          "HV005": {"clase": "peso"}, "HVIDX": {"clase": "categoria", "clase_indice": "llave"}}


def _col_meta(n, etq, valores=(), formato="%12.0g", **kw):
    return {"nombre": n, "etiqueta": etq, "formato": formato, "etiquetas_valor": [list(v) for v in valores],
            "rangos_perdidos": kw.get("rangos", []), "perdidos_usuario": kw.get("usuario", [])}


def _sintetico(tmp_path):
    """Un hogar (RECH0), sus personas (RECH1) y las mujeres (REC0111, solo CASEID: HHID se deriva)."""
    metas = {
        "RECH0": {"filas": 3, "formato": "dta", "miembro": "z/RECH0_2024.dta", "zip": "z.zip",
                  "columnas": [_col_meta("hhid", "Identificación del hogar", formato="%15s"), _col_meta("hv005", "Factor  de ponderación"),
                               _col_meta("sh61a", "Tiene radio"), _col_meta("sh61b", "Tiene tele")]},
        "RECH1": {"filas": 4, "formato": "dta", "miembro": "z/RECH1_2024.dta", "zip": "z.zip",
                  "columnas": [_col_meta("HHID", "Id", formato="%15s"), _col_meta("HVIDX", "Orden"),
                               _col_meta("HV108", "Educaci¢n", [(1, "Primaria"), (8, "No sabe"), (98, "Otro"), (3, "Superior")]),
                               _col_meta("HV109", None, [(1, "Sí"), (9, "No responde")], usuario=["a"])]},
        "REC0111": {"filas": 2, "formato": "dta", "miembro": "z/REC0111_2024.dta", "zip": "z.zip",
                    "columnas": [_col_meta("CASEID", "Id mujer", formato="%18s"), _col_meta("V012", "Edad")]},
    }
    parq = {"RECH0": pl.DataFrame({"HHID": ["000000001", "000000002", "000000003"], "HV005": [1.0, 2.0, 3.0], "SH61A": [1.0, 2.0, None],
                                   "SH61B": [1.0, None, None], "anio": [2024] * 3}),
            "RECH1": pl.DataFrame({"HHID": ["000000001", "000000001", "000000002", "000000003"], "HVIDX": [1, 2, 1, 1],
                                   "HV108": [1.0, 8.0, 98.0, 8.0], "HV109": [1.0, 9.0, None, None], "anio": [2024] * 4}),
            "REC0111": pl.DataFrame({"CASEID": ["000000001  1", "000000002  1"], "V012": [30.0, 40.0], "HHID": ["000000001", "000000002"],
                                     "anio": [2024] * 2})}
    for n, df in parq.items():
        df.write_parquet(tmp_path / f"{n}.parquet")
    man = {"archivos": {n: {"filas": metas[n]["filas"], "huella_datos": "h" * 64, "parquet": f"{n}.parquet",
                            "columnas": [{"nombre": c, "tipo": "x", "clase": None} for c in parq[n].columns],
                            "perdidos": {"HV109": {"origen": "stata_extendido", "declarados": ["a"], "conteo": {"a": 2}}} if n == "RECH1" else {}}
                        for n in metas}}
    curado = {"archivos": {"RECH0": {"unidad": "hogar", "llave": ["HHID"]}, "RECH1": {"unidad": "persona_del_hogar", "llave": ["HHID", "HVIDX"]},
                           "REC0111": {"unidad": "mujer", "llave": ["CASEID"]}},
              "relaciones": [{"hijo": "RECH1", "padre": "RECH0", "por": [["HHID", "HHID"]], "cardinalidad": "n:1"},
                             {"hijo": "REC0111", "padre": "RECH0", "por": [["HHID", "HHID"]], "cardinalidad": "n:1"}]}
    return metas, man, curado


def test_indice_sintetico_tiene_los_campos_del_anexo_a_y_deja_vacio_lo_de_m1(tmp_path):
    metas, man, curado = _sintetico(tmp_path)
    ind = construir("ENDES", 2024, metas, man, CLASES, curado, PI, parquet_dir=tmp_path)
    a, v, c = ind.archivos, ind.variables, ind.categorias
    assert set(["encuesta", "anio", "archivo", "unidad", "llave", "n_filas", "formato", "huella_datos"]) <= set(a.columns)
    assert set(["var_id", "clase", "tipo_valor", "rango_valido", "codigos_especiales", "rol_faltante", "etiqueta_original", "etiqueta_curada",
                "texto_pregunta", "universo_cuestionario", "ventana_referencia", "sujeto", "informante", "modo", "grupo", "tipo_origen",
                "universo_corto", "concepto_id", "estado"]) <= set(v.columns)
    assert c.columns[:6] == ["var_id", "codigo", "etiqueta_original", "etiqueta_curada", "es_especial", "rol_faltante"]
    assert a["archivo"].to_list() == ["REC0111", "RECH0", "RECH1"] and a.filter(pl.col("archivo") == "RECH1")["llave"][0].to_list() == ["HHID", "HVIDX"]
    for vacio in ("texto_pregunta", "universo_cuestionario", "ventana_referencia", "sujeto", "informante", "modo", "universo_corto",
                  "rol_faltante", "tipo_origen", "concepto_id", "rango_valido"):
        assert v[vacio].null_count() == v.height, vacio
    assert c["rol_faltante"].null_count() == c.height
    assert set(v["estado"]) == {"propuesto"}
    assert "ENDES·2024·RECH0·HV005" in v["var_id"].to_list() and all(n == n.upper() for n in v["variable"])


def test_variables_del_indice_son_las_columnas_del_parquet_menos_anio_con_la_derivada(tmp_path):
    metas, man, curado = _sintetico(tmp_path)
    ind = construir("ENDES", 2024, metas, man, CLASES, curado, PI, parquet_dir=tmp_path)
    for n in metas:
        cols = [c for c in pl.read_parquet(tmp_path / f"{n}.parquet").columns if c != "anio"]
        assert ind.variables.filter(pl.col("archivo") == n).sort("posicion")["variable"].to_list() == cols
    d = ind.variables.filter(pl.col("var_id") == "ENDES·2024·REC0111·HHID").row(0, named=True)
    assert d["derivada_de"] == "CASEID" and d["clase"] == "llave" and d["etiqueta_original"] is None and d["controles"] == []


def test_clases_y_grupos_y_tipo_de_valor(tmp_path):
    metas, man, curado = _sintetico(tmp_path)
    v = construir("ENDES", 2024, metas, man, CLASES, curado, PI, parquet_dir=tmp_path).variables
    por = {r["var_id"].split("·")[-1] + "@" + r["archivo"]: r for r in v.iter_rows(named=True)}
    assert por["HV005@RECH0"]["clase"] == "peso" and por["HVIDX@RECH1"]["clase"] == "llave" and por["HV108@RECH1"]["clase"] is None
    assert por["SH61A@RECH0"]["grupo"] == "SH61" == por["SH61B@RECH0"]["grupo"] and por["HV005@RECH0"]["grupo"] is None
    assert por["HV108@RECH1"]["tipo_valor"] == "categorica" and por["HHID@RECH1"]["tipo_valor"] == "texto" and por["HV005@RECH0"]["tipo_valor"] == "numerica"


def test_etiquetas_curadas_conservan_la_original_y_los_controles_marcan_la_variable(tmp_path):
    metas, man, curado = _sintetico(tmp_path)
    ind = construir("ENDES", 2024, metas, man, CLASES, curado, PI, parquet_dir=tmp_path)
    r = ind.variables.filter(pl.col("var_id") == "ENDES·2024·RECH0·HV005").row(0, named=True)
    assert r["etiqueta_original"] == "Factor  de ponderación" and r["etiqueta_curada"] == "Factor de ponderación"
    r = ind.variables.filter(pl.col("var_id") == "ENDES·2024·RECH1·HV108").row(0, named=True)
    assert r["etiqueta_original"] == "Educaci¢n" and r["etiqueta_curada"] == "Educación" and r["controles"] == ["mojibake_reparado"]
    r = ind.variables.filter(pl.col("var_id") == "ENDES·2024·RECH1·HV109").row(0, named=True)
    assert r["etiqueta_curada"] == "" and r["controles"] == ["etiqueta_vacia"]
    assert {h.control for h in ind.hallazgos} == {"mojibake_reparado", "etiqueta_vacia"}


def test_categorias_marcan_especiales_propuestos_con_frecuencia(tmp_path):
    metas, man, curado = _sintetico(tmp_path)
    c = construir("ENDES", 2024, metas, man, CLASES, curado, PI, parquet_dir=tmp_path).categorias
    f = c.filter(pl.col("var_id") == "ENDES·2024·RECH1·HV108").sort("codigo")
    assert dict(zip(f["codigo"], f["es_especial"])) == {"1": "no", "3": "no", "8": "propuesto", "98": "propuesto"}
    ocho = f.filter(pl.col("codigo") == "8").row(0, named=True)
    assert ocho["frecuencia"] == 2 and ocho["proporcion_filas"] == 0.5 and ocho["origen_especial"] == "etiqueta"
    h9 = c.filter(pl.col("var_id") == "ENDES·2024·RECH1·HV109").sort("codigo")
    assert h9["codigo"].to_list() == ["1", "9", "a"]                       # «a»: perdido de Stata sin etiqueta de valor
    a = h9.filter(pl.col("codigo") == "a").row(0, named=True)
    assert a["origen_especial"] == "declarado" and a["frecuencia"] == 2 and a["etiqueta_original"] == ""     # del manifiesto, no del Parquet
    assert contar_codigos(tmp_path / "RECH1.parquet", {"HV108": ["8", "98", "a"]}) == {("HV108", "8"): 2, ("HV108", "98"): 1}


def test_especial_declarado_sin_filas_salta_el_control(tmp_path):
    metas, man, curado = _sintetico(tmp_path)
    man["archivos"]["RECH1"]["perdidos"]["HV109"]["conteo"] = {"a": 0}
    ind = construir("ENDES", 2024, metas, man, CLASES, curado, PI, parquet_dir=tmp_path)
    assert [h.control for h in ind.hallazgos if h.objeto.endswith("HV109=a")] == ["especial_declarado_sin_filas"]


def test_construir_se_detiene_si_el_indice_no_cuadra_con_los_datos(tmp_path):
    metas, man, curado = _sintetico(tmp_path)
    m2 = json.loads(json.dumps(man)); m2["archivos"]["RECH0"]["columnas"].append({"nombre": "EXTRA", "tipo": "x", "clase": None})
    with pytest.raises(PapError, match="no son las columnas del Parquet"):
        construir("ENDES", 2024, metas, m2, CLASES, curado, PI)
    m3 = json.loads(json.dumps(man)); m3["archivos"]["RECH0"]["filas"] = 99
    with pytest.raises(PapError, match="3 filas"):
        construir("ENDES", 2024, metas, m3, CLASES, curado, PI)
    del man["archivos"]["REC0111"]
    with pytest.raises(PapError, match="no tienen los mismos archivos"):
        construir("ENDES", 2024, metas, man, CLASES, curado, PI)


def test_la_tabla_curada_tiene_que_cubrir_los_archivos_y_sus_columnas(tmp_path):
    metas, man, curado = _sintetico(tmp_path)
    mal = json.loads(json.dumps(curado)); del mal["archivos"]["REC0111"]
    with pytest.raises(PapError, match="faltan"):
        construir("ENDES", 2024, metas, man, CLASES, mal, PI)
    mal = json.loads(json.dumps(curado)); mal["archivos"]["RECH1"]["llave"] = ["HHID", "NOEXISTE"]
    with pytest.raises(PapError, match="NOEXISTE"):
        construir("ENDES", 2024, metas, man, CLASES, mal, PI)
    mal = json.loads(json.dumps(curado)); mal["relaciones"][0]["por"] = [["HHID", "NOEXISTE"]]
    with pytest.raises(PapError, match="NOEXISTE"):
        construir("ENDES", 2024, metas, man, CLASES, mal, PI)


def test_escribir_deja_tres_parquet_y_dos_corridas_dan_lo_mismo(tmp_path):
    metas, man, curado = _sintetico(tmp_path)
    ind = construir("ENDES", 2024, metas, man, CLASES, curado, PI, parquet_dir=tmp_path)
    r1 = escribir(ind, tmp_path / "v1")
    r2 = escribir(construir("ENDES", 2024, metas, man, CLASES, curado, PI, parquet_dir=tmp_path), tmp_path / "v2")
    assert set(r1) == {"archivos", "variables", "categorias"}
    for k in r1:
        assert pl.read_parquet(r1[k]).equals(pl.read_parquet(r2[k]))
    assert pl.read_parquet(r1["archivos"])["llave"].dtype == pl.List(pl.String)
    rel = json.loads(pl.read_parquet(r1["archivos"]).filter(pl.col("archivo") == "RECH1")["relaciones"][0])
    assert rel == [{"con": "RECH0", "por": [["HHID", "HHID"]], "cardinalidad": "n:1"}]


def test_los_parquet_del_indice_no_van_a_git():
    r = subprocess.run(["git", "check-ignore", "-q", "biblioteca/variables/variables.parquet"], cwd=RAIZ_REAL)
    assert r.returncode == 0


# ------------------------------------------------------------------ uniones: filas antes y después

def test_union_sin_perdida_ni_duplicacion(tmp_path):
    metas, man, curado = _sintetico(tmp_path)
    u = verificar_relaciones(curado, tmp_path)
    assert [(x.hijo, x.padre, x.filas_hijo, x.filas_union, x.filas_con_pareja) for x in u] == \
        [("RECH1", "RECH0", 4, 4, 4), ("REC0111", "RECH0", 2, 2, 2)]
    assert all(x.sin_perdida_ni_duplicacion for x in u)


def test_union_que_duplica_filas_porque_el_padre_repite_la_llave_se_detecta(tmp_path):
    pl.DataFrame({"HHID": ["1", "1", "2"]}).write_parquet(tmp_path / "padre.parquet")
    pl.DataFrame({"HHID": ["1", "2"]}).write_parquet(tmp_path / "hijo.parquet")
    u = contar_union(tmp_path / "hijo.parquet", tmp_path / "padre.parquet", [["HHID", "HHID"]])
    assert (u.filas_hijo, u.filas_union, u.llaves_repetidas_padre) == (2, 3, 1) and not u.sin_perdida_ni_duplicacion


def test_union_que_pierde_filas_porque_el_hijo_no_tiene_pareja_se_detecta(tmp_path):
    pl.DataFrame({"HHID": ["1", "2"]}).write_parquet(tmp_path / "padre.parquet")
    pl.DataFrame({"HHID": ["1", "2", "3"], "HC0": [1, 1, 1]}).write_parquet(tmp_path / "hijo.parquet")
    u = contar_union(tmp_path / "hijo.parquet", tmp_path / "padre.parquet", [["HHID", "HHID"]])
    assert (u.filas_hijo, u.filas_union, u.filas_con_pareja) == (3, 3, 2) and not u.sin_perdida_ni_duplicacion


def test_union_por_dos_columnas_hhid_y_hc0_con_hvidx(tmp_path):
    pl.DataFrame({"HHID": ["1", "1", "2"], "HVIDX": [1, 2, 1]}).write_parquet(tmp_path / "rech1.parquet")
    pl.DataFrame({"HHID": ["1", "2"], "HC0": [2, 1]}).write_parquet(tmp_path / "rech6.parquet")
    u = contar_union(tmp_path / "rech6.parquet", tmp_path / "rech1.parquet", [["HHID", "HHID"], ["HC0", "HVIDX"]])
    assert u.sin_perdida_ni_duplicacion and u.filas_hijo == 2


# ------------------------------------------------------------------ CLI

def test_pap_variables_indexar_pide_antes_pap_microdatos_convertir(tmp_path):
    with pytest.raises(PapError, match="pap microdatos convertir"):
        ix.indexar(Rutas(tmp_path), "ENDES", 2024)


def test_cli_registra_pap_variables_indexar():
    from pap.cli import construir_parser

    a = construir_parser().parse_args(["variables", "indexar", "--encuesta", "ENDES", "--anio", "2024"])
    assert (a.accion, a.encuesta, a.anio) == ("indexar", "ENDES", 2024) and a.fn.__name__ == "cmd_variables"
    with pytest.raises(SystemExit):
        construir_parser().parse_args(["variables", "indexar", "--encuesta", "NOEXISTE", "--anio", "2024"])


# ------------------------------------------------------------------ tablas curadas

def test_clases_columnas_trae_llaves_geo_pesos_y_diseno_cada_una_con_su_cita():
    y = yaml.safe_load((RAIZ_REAL / "curados" / "inferencia" / "clases_columnas.yaml").read_text(encoding="utf-8"))
    cols, citas = y["columnas"], y["citas"]
    assert y["provisional"] is False
    for nombre, c in cols.items():
        assert c.get("cita") in citas, f"{nombre}: sin cita"
        assert (c.get("clase_indice") or c["clase"]) in {"llave", "geo", "peso", "diseno", "categoria", "medida"}
    final = {n: c.get("clase_indice") or c["clase"] for n, c in cols.items()}
    assert {n for n, k in final.items() if k == "peso"} == {"HV005", "V005", "PESO15_AMAS", "PESOMEN12"}
    assert {"HHID", "CASEID", "HVIDX", "HC0"} <= {n for n, k in final.items() if k == "llave"}
    assert {"UBIGEO", "HV025", "V025"} <= {n for n, k in final.items() if k == "geo"}
    assert {"HV001", "HV021", "HV022", "HV024", "V001", "V021", "V022", "V024", "QHCLUSTER"} <= {n for n, k in final.items() if k == "diseno"}
    assert "Ficha técnica ENDES 2024" in citas["ficha_hogar"] and "HV005/1000000" in citas["ficha_hogar"]


def test_el_conversor_guarda_peso_como_doble_y_diseno_como_entero(tmp_path):
    from pap.inferencia.almacen import convertir_archivo

    ruta = tmp_path / "h.dta"
    pyreadstat.write_dta(pd.DataFrame({"HHID": ["      000000001"], "HV005": [1234.0], "HV021": [7.0], "QHCLUSTER": [7.0]}), str(ruta), version=15)
    convertir_archivo(ruta, tmp_path / "h.parquet", anio=2024, formato="dta", p=P)
    t = pl.read_parquet(tmp_path / "h.parquet")
    assert t.schema["HV005"] == pl.Float64 and t.schema["HV021"] == pl.Int32 and t.schema["QHCLUSTER"] == pl.Int32


def test_archivos_endes_2024_declara_unidad_llave_y_uniones_de_cada_archivo():
    y = yaml.safe_load((RAIZ_REAL / "curados" / "inferencia" / "archivos_endes_2024.yaml").read_text(encoding="utf-8"))
    assert len(y["archivos"]) == 34 and all(set(a) == {"unidad", "llave"} for a in y["archivos"].values())
    for r in y["relaciones"]:
        assert r["hijo"] in y["archivos"] and r["padre"] in y["archivos"] and r["cardinalidad"] in CARDINALIDADES          # M1-03: también 1:1 y 1:0..1, medidas contra los datos
    pares = {(r["hijo"], r["padre"]): r["por"] for r in y["relaciones"]}
    assert pares[("RECH1", "RECH0")] == [["HHID", "HHID"]]
    assert pares[("RECH6", "RECH1")] == [["HHID", "HHID"], ["HC0", "HVIDX"]]
    assert pares[("REC0111", "RECH0")] == [["HHID", "HHID"]]
    assert ("REC93DVdisciplina", "REC0111") not in pares and ("REC93DVdisciplina", "RECH0") in pares


def test_parametros_del_indice_vienen_del_yaml_con_su_origen():
    y = yaml.safe_load((RAIZ_REAL / "curados" / "inferencia" / "parametros.yaml").read_text(encoding="utf-8"))["indice"]
    assert all("valor" in v and v.get("supuesto") == "M0-05" for v in y.values())
    assert PI.universo_coincidencia_min == 0.995 and "no sabe" in PI.especiales_textos and 98 in PI.especiales_codigos
