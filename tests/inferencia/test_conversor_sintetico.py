"""M0-04: conversor de microdatos con archivos sintéticos (sin los datos reales del INEI)."""
import json
import stat
import zipfile
from dataclasses import replace
from pathlib import Path

import pandas as pd
import polars as pl
import pyreadstat
import pytest

from pap.config import Rutas
from pap.errores import PapError
from pap.inferencia import almacen
from pap.inferencia.almacen import LectorAbortado, Parametros, convertir_archivo, ejecutar_aislado, huella_contenido_v1
from pap.inferencia.lector_aislado import ErrorConversion, leer_y_escribir
from pap.zip_seguro import ZipInseguro, abrir_zip_seguro

P = Parametros.desde_yaml()


def _spec(tmp: Path, entrada: Path, formato: str, **cambios) -> dict:
    s = {"entrada": str(entrada), "formato": formato, "salida": str(tmp / "salida.parquet"), "anio": 2024,
         "clases": str(almacen.RUTA_CLASES), "bloques_desde_bytes": int(P.bloques_desde_mb * (1 << 20)),
         "bloques_filas": P.bloques_filas, "codificacion_sin_declarar": P.codificacion_sin_declarar,
         "parquet_compresion": "zstd", "parquet_nivel": 3, "parquet_grupo_filas": 122880, "duckdb_memoria_mb": 512,
         "base_temporal": str(tmp / "trabajo.duckdb"), "resultado": str(tmp / "r.json")}
    return s | cambios


def _hogar(n=5) -> pd.DataFrame:
    return pd.DataFrame({
        "HHID": [f"      {i:09d}" for i in range(123456, 123456 + n)],      # 15 caracteres, 6 espacios y ceros a la izquierda
        "UBIGEO": ["010101", "000102", "150101", "010101", "020301"][:n],
        "HV024": [1.0, 2.0, 15.0, 1.0, 2.0][:n],
        "HV005": [1234.5, 0.0, 99.25, 1.0, 7.0][:n],
        "NOMCCPP": ["BREÑA", "Ñaña", "LIMA", "Ñuñoa", "CUSCO"][:n]})


def _dta(ruta: Path, df: pd.DataFrame, **kw) -> Path:
    pyreadstat.write_dta(df, str(ruta), version=15, **kw)
    return ruta


# ------------------------------------------------------------------ ZIP maliciosos (C7)

def _zip(ruta, miembros):
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        for info, datos in miembros:
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, datos)
    return ruta


def test_zip_con_ruta_con_puntos_puntos_es_rechazado(tmp_path):
    z = _zip(tmp_path / "a.zip", [(zipfile.ZipInfo("../fuera.dta"), b"x")])
    with pytest.raises(ZipInseguro, match="ruta no permitida"), abrir_zip_seguro(z):
        pass


def test_zip_con_enlace_simbolico_es_rechazado(tmp_path):
    i = zipfile.ZipInfo("enlace.dta")
    i.external_attr = (stat.S_IFLNK | 0o777) << 16
    z = _zip(tmp_path / "b.zip", [(i, b"/etc/passwd")])
    with pytest.raises(ZipInseguro, match="enlace simbólico"), abrir_zip_seguro(z):
        pass


def test_zip_bomba_de_compresion_es_rechazado(tmp_path):
    z = _zip(tmp_path / "c.zip", [(zipfile.ZipInfo("bomba.dta"), bytes(64 << 20))])     # 64 MB de ceros → proporción > 1 000
    with pytest.raises(ZipInseguro, match="proporción de compresión"), abrir_zip_seguro(z):
        pass


# ------------------------------------------------------------------ DTA y SAV sintéticos

def test_dta_conserva_ceros_ancho_nombres_con_enie_y_clases(tmp_path):
    r = leer_y_escribir(_spec(tmp_path, _dta(tmp_path / "h.dta", _hogar()), "dta"))
    t = pl.read_parquet(tmp_path / "salida.parquet")
    assert t["HHID"].to_list() == ["000123456", "000123457", "000123458", "000123459", "000123460"]
    assert t["UBIGEO"].to_list() == ["010101", "000102", "150101", "010101", "020301"]
    assert t["NOMCCPP"].to_list() == ["BREÑA", "Ñaña", "LIMA", "Ñuñoa", "CUSCO"]
    assert t.schema["HV024"] == pl.Int32 and t.schema["HV005"] == pl.Float64 and t.schema["anio"] == pl.Int32
    assert t["anio"].unique().to_list() == [2024] and t["HV005"].to_list() == [1234.5, 0.0, 99.25, 1.0, 7.0]
    assert r["filas"] == 5 and r["columnas"][0] == {"nombre": "HHID", "tipo": "VARCHAR", "clase": "llave"}
    assert r["versiones"]["pyreadstat"] == "1.3.7" and r["perdidos"] == {}


def test_dta_perdidos_extendidos_van_a_nulo_con_su_codigo(tmp_path):
    df = pd.DataFrame({"HHID": ["      000000001"] * 5, "P1": pd.Series([1.0, "a", None, "b", "a"], dtype=object),
                       "HV024": [1.0] * 5})
    r = leer_y_escribir(_spec(tmp_path, _dta(tmp_path / "e.dta", df, missing_user_values={"P1": ["a", "b"]}), "dta"))
    t = pl.read_parquet(tmp_path / "salida.parquet")
    assert t.schema["P1"] == pl.Float64 and t["P1"].to_list() == [1.0, None, None, None, None]
    assert r["perdidos"]["P1"]["origen"] == "stata_extendido" and r["perdidos"]["P1"]["conteo"] == {"a": 2, "b": 1}


def test_sav_perdidos_de_usuario_van_a_nulo_con_su_codigo_y_nombre_con_enie(tmp_path):
    df = pd.DataFrame({"AÑO_NAC": [1990.0, 98.0, 99.0, 2001.0, 98.0, None], "HV024": [1.0, 2, 3, 4, 5, 6]})
    ruta = tmp_path / "s.sav"
    pyreadstat.write_sav(df, str(ruta), missing_ranges={"AÑO_NAC": [98, 99]})
    r = leer_y_escribir(_spec(tmp_path, ruta, "sav"))
    t = pl.read_parquet(tmp_path / "salida.parquet")
    assert "AÑO_NAC" in t.columns and t["AÑO_NAC"].to_list() == [1990.0, None, None, 2001.0, None, None]
    assert r["perdidos"]["AÑO_NAC"]["origen"] == "spss_usuario"
    assert r["perdidos"]["AÑO_NAC"]["conteo"] == {"98.0": 2, "99.0": 1}


def test_dta_antiguo_sin_codificacion_se_lee_como_windows_1252(tmp_path):
    df = pd.DataFrame({"HHID": ["      000000001"], "NOM": ["BREÑA"], "HV024": [1.0]})
    ruta = tmp_path / "viejo.dta"
    pyreadstat.write_dta(df, str(ruta), version=12)          # formato 115: no declara codificación
    datos = ruta.read_bytes()
    assert b"BRE\xc3\x91A\x00" in datos
    ruta.write_bytes(datos.replace(b"BRE\xc3\x91A\x00", b"BRE\xd1A\x00\x00"))     # el mismo ancho, ahora en cp1252
    r = leer_y_escribir(_spec(tmp_path, ruta, "dta"))
    assert pl.read_parquet(tmp_path / "salida.parquet")["NOM"].to_list() == ["BREÑA"]
    assert r["codificacion"] == "WINDOWS-1252" and r["release_dta"] == 115


def test_caseid_con_espacios_se_recorta_solo_por_fuera_y_deriva_hhid_del_crudo(tmp_path):
    df = pd.DataFrame({"CASEID": ["      000123456  1", "      000123457 12"], "HV024": [1.0, 2.0]})
    leer_y_escribir(_spec(tmp_path, _dta(tmp_path / "c.dta", df), "dta"))
    t = pl.read_parquet(tmp_path / "salida.parquet")
    assert t["CASEID"].to_list() == ["000123456  1", "000123457 12"]       # espacios internos intactos
    assert t["HHID"].to_list() == ["000123456", "000123457"]


def test_hhid_derivado_que_no_coincide_con_la_columna_es_error(tmp_path):
    df = pd.DataFrame({"CASEID": ["      000123456  1"], "HHID": ["      000123499"]})
    with pytest.raises(ErrorConversion, match="no coincide"):
        leer_y_escribir(_spec(tmp_path, _dta(tmp_path / "c.dta", df), "dta"))


def test_ancho_distinto_es_error_y_no_se_corta(tmp_path):
    df = pd.DataFrame({"HHID": ["      0001234567"], "HV024": [1.0]})          # 10 dígitos
    with pytest.raises(ErrorConversion, match="ancho distinto de 9"):
        leer_y_escribir(_spec(tmp_path, _dta(tmp_path / "w.dta", df), "dta"))
    assert not (tmp_path / "salida.parquet").exists()


def test_llave_numerica_y_categoria_con_decimales_son_errores(tmp_path):
    with pytest.raises(ErrorConversion, match="no como texto"):
        leer_y_escribir(_spec(tmp_path, _dta(tmp_path / "n.dta", pd.DataFrame({"HHID": [123456789.0]})), "dta"))
    with pytest.raises(ErrorConversion, match="no son enteros"):
        leer_y_escribir(_spec(tmp_path, _dta(tmp_path / "d.dta", pd.DataFrame({"HV024": [1.0, 2.5]})), "dta"))


def test_archivo_grande_se_lee_por_bloques_y_da_el_mismo_contenido(tmp_path):
    n = 1000
    df = pd.DataFrame({"HHID": [f"      {i:09d}" for i in range(n)], "HV024": [float(i % 25 + 1) for i in range(n)],
                       "HV005": [i / 7 for i in range(n)], "NOM": [f"Ñ{i}" for i in range(n)]})
    ruta = _dta(tmp_path / "g.dta", df)
    entero = leer_y_escribir(_spec(tmp_path, ruta, "dta", salida=str(tmp_path / "entero.parquet"),
                                   base_temporal=str(tmp_path / "t1.duckdb")))
    trozos = leer_y_escribir(_spec(tmp_path, ruta, "dta", salida=str(tmp_path / "bloques.parquet"),
                                   base_temporal=str(tmp_path / "t2.duckdb"), bloques_desde_bytes=1000, bloques_filas=300))
    assert not entero["leido_en_bloques"] and trozos["leido_en_bloques"]
    assert trozos["filas"] == n and trozos["huella_contenido_v1"] == entero["huella_contenido_v1"]
    assert pl.read_parquet(tmp_path / "bloques.parquet")["HHID"].to_list()[:2] == ["000000000", "000000001"]


def test_parquet_usa_zstd_y_grupos_de_filas_pedidos(tmp_path):
    import pyarrow.parquet as pq

    leer_y_escribir(_spec(tmp_path, _dta(tmp_path / "h.dta", _hogar(5)), "dta", parquet_grupo_filas=2048))
    md = pq.ParquetFile(tmp_path / "salida.parquet").metadata
    assert md.row_group(0).column(0).compression == "ZSTD" and md.num_row_groups == 1


# ------------------------------------------------------------------ huella de contenido

def _tabla_con_casos_raros() -> pl.DataFrame:
    return pl.DataFrame({"B": [1.5, -0.0, float("nan"), None, 0.1 + 0.2], "A": ["Ñandú", None, "x", "y\x1fz", ""],
                         "C": [1, 2, 3, None, 5]}, schema={"B": pl.Float64, "A": pl.String, "C": pl.Int32})


def test_huella_estable_al_reescribir_con_polars_pyarrow_y_barajar(tmp_path):
    import pyarrow.parquet as pq

    t = _tabla_con_casos_raros()
    t.write_parquet(tmp_path / "pl.parquet")
    pq.write_table(t.to_arrow(), tmp_path / "pa.parquet", compression="snappy")
    t.sample(fraction=1.0, shuffle=True, seed=7).write_parquet(tmp_path / "bar.parquet", compression="zstd")
    h = huella_contenido_v1(tmp_path / "pl.parquet")
    assert len(h) == 64 and huella_contenido_v1(tmp_path / "pa.parquet") == h == huella_contenido_v1(tmp_path / "bar.parquet")


def test_huella_trata_igual_menos_cero_y_cero_y_todo_nan(tmp_path):
    import struct

    nan_neg = struct.unpack("<d", struct.pack("<Q", 0xFFF8000000000001))[0]
    base = pl.DataFrame({"x": [0.0, float("nan"), 2.0]})
    otra = pl.DataFrame({"x": [-0.0, nan_neg, 2.0]})
    base.write_parquet(tmp_path / "a.parquet")
    otra.write_parquet(tmp_path / "b.parquet")
    assert huella_contenido_v1(tmp_path / "a.parquet") == huella_contenido_v1(tmp_path / "b.parquet")


def test_huella_cambia_si_cambia_un_valor_o_un_nulo(tmp_path):
    t = _tabla_con_casos_raros()
    t.write_parquet(tmp_path / "a.parquet")
    t.with_columns(pl.when(pl.col("C") == 2).then(9).otherwise(pl.col("C")).alias("C")).write_parquet(tmp_path / "b.parquet")
    t.with_columns(pl.col("A").fill_null("")).write_parquet(tmp_path / "c.parquet")      # nulo ≠ cadena vacía
    h = {huella_contenido_v1(tmp_path / f"{x}.parquet") for x in "abc"}
    assert len(h) == 3


# ------------------------------------------------------------------ subproceso aislado (C8)

def test_el_lector_corre_aislado_y_devuelve_las_mediciones(tmp_path):
    entrada = _dta(tmp_path / "h.dta", _hogar())
    salida = tmp_path / "out" / "H.parquet"
    r = convertir_archivo(entrada, salida, anio=2024, formato="dta", p=P)
    assert salida.exists() and not list((tmp_path / "out").glob(".*.tmp"))
    assert r["filas"] == 5 and r["rss_max_mb"] > 10 and r["huella_contenido_v1"] == huella_contenido_v1(salida)


def test_error_del_lector_no_deja_parquet_y_se_informa(tmp_path):
    entrada = _dta(tmp_path / "w.dta", pd.DataFrame({"HHID": ["      0001234567"]}))
    with pytest.raises(PapError, match="ancho distinto de 9"):
        convertir_archivo(entrada, tmp_path / "out" / "W.parquet", anio=2024, formato="dta", p=P)
    assert not (tmp_path / "out" / "W.parquet").exists() and not list((tmp_path / "out").glob(".*.tmp"))


def test_vigilante_mata_al_subproceso_que_pasa_el_tope_de_memoria(tmp_path):
    p = replace(P, rss_max_mb=150, sondeo_s=0.05, tiempo_s=60)
    with pytest.raises(LectorAbortado, match="memoria residente"):
        ejecutar_aislado(["python3", "-c", "import time;b=bytearray(600<<20);time.sleep(30)"], p, cwd=tmp_path)


def test_tope_de_tiempo_mata_al_subproceso(tmp_path):
    p = replace(P, tiempo_s=0.5, sondeo_s=0.05)
    with pytest.raises(LectorAbortado, match="de tiempo"):
        ejecutar_aislado(["python3", "-c", "import time;time.sleep(30)"], p, cwd=tmp_path)


def test_tope_de_procesador_mata_al_subproceso(tmp_path):
    p = replace(P, cpu_s=1, sondeo_s=0.05, tiempo_s=60)
    with pytest.raises(LectorAbortado, match="procesador"):
        ejecutar_aislado(["python3", "-c", "while True: pass"], p, cwd=tmp_path)


def test_el_subproceso_no_hereda_el_entorno_del_dueno(tmp_path, monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "no-debe-verse")
    assert "GH_TOKEN" not in almacen._entorno()


def test_rlimit_as_se_detecta_sin_afirmar_de_mas():
    assert isinstance(almacen.rlimit_as_se_aplica(), bool)


def test_nombre_del_parquet():
    assert almacen.nombre_parquet("968-Modulo1629/RECH0_2024.dta", 2024) == "RECH0"
    assert almacen.nombre_parquet("968-Modulo1641/Programas Sociales x Hogar_2024.dta", 2024) == "Programas_Sociales_x_Hogar"


# ------------------------------------------------------------------ de punta a punta, con un proyecto de juguete

def test_convertir_escribe_parquet_manifiesto_y_lock(tmp_path, monkeypatch):
    import yaml
    from pap.capa0.insumos import Insumo
    from pap.util import sha256

    (tmp_path / "curados" / "inferencia" / "descargas").mkdir(parents=True)
    (tmp_path / "curados" / "inferencia" / "descargas" / "endes_2099.yaml").write_text(yaml.safe_dump(
        {"fuente": "INEI-ENDES", "modulos": [{"codigo": 1, "formato": "STATA", "recurso": "endes-2099-hogar"}]}))
    dta = _dta(tmp_path / "RECH0_2099.dta", _hogar())
    zip_ = tmp_path / "968-Modulo1.zip"
    with zipfile.ZipFile(zip_, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(dta, "968-Modulo1/RECH0_2099.dta")
        z.writestr("968-Modulo1/Diccionario.pdf", b"%PDF-1.4")
    h = sha256(zip_)
    monkeypatch.setattr(almacen, "_insumo", lambda rutas, fuente, recurso: Insumo(
        fuente, recurso, "sha256:" + h, zip_, "968-Modulo1.zip", None, "2026-11-09T10:00:00-05:00"))
    mensajes = []
    m = almacen.convertir(Rutas(tmp_path), "ENDES", 2099, log=mensajes.append)
    sal = tmp_path / "biblioteca" / "microdatos" / "ENDES" / "2099"
    e = json.loads((sal / "manifiesto.json").read_text(encoding="utf-8"))["archivos"]["RECH0"]
    assert list(m["archivos"]) == ["RECH0"] and (sal / "RECH0.parquet").exists()
    assert e["origen"] == {"zip": "968-Modulo1.zip", "zip_sha256": h, "recurso": "endes-2099-hogar",
                           "miembro": "968-Modulo1/RECH0_2099.dta"}
    assert e["filas"] == 5 and e["n_columnas"] == 6 and e["huella_contenido_v1"] == huella_contenido_v1(sal / "RECH0.parquet")
    assert len(e["huella_datos"]) == 64 and set(e["versiones"]) >= {"pyreadstat", "pyarrow", "polars", "duckdb", "svy"}
    lock = yaml.safe_load((tmp_path / "curados" / "insumos.lock.yaml").read_text())
    assert lock == {"INEI-ENDES": ["sha256:" + h]}
