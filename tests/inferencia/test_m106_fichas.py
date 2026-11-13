"""M1-06: fichas de tabla, bloques y las 8 reglas de validación de fichas.md §9, con un mundo sintético (sin almacén ni microdatos reales)."""
import copy
import hashlib
import json
import subprocess
import sys

import polars as pl
import pytest
import yaml

from pap.errores import PapError
from pap.inferencia import fichas as fi

from conftest import RAIZ_REAL

from . import test_m106_mundo as mw


@pytest.fixture()
def raiz(tmp_path):
    return mw.escribir_mundo(tmp_path)


def _editar(raiz, ruta, fn):
    p = raiz / "curados" / "inferencia" / ruta
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    fn(d)
    p.write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")


def _validar(raiz, **kw):
    kw.setdefault("buscar_recurso", mw.buscar)
    probs, info = fi.validar(raiz, "ENDES", 2024, **kw)
    return probs, info


def _reglas(probs):
    return sorted({p.regla for p in probs})


# ---------------------------------------------------------------- generar

def test_generar_escribe_fichas_bloques_y_bloque_id(raiz):
    res = fi.generar(raiz, "ENDES", 2024)
    ind = raiz / "biblioteca" / "variables"
    f, b, v = (pl.read_parquet(ind / n) for n in ("fichas_tabla.parquet", "bloques.parquet", "variables.parquet"))
    assert res["fichas"] == 2 and f["tabla"].to_list() == ["RECH0", "RECH6"] and b["bloque_id"].to_list() == ["endes_rech0_hogar", "endes_rech6_hemoglobina", "endes_rech6_medidas"]
    r6 = f.filter(pl.col("tabla") == "RECH6").row(0, named=True)
    assert r6["bloques"] == ["endes_rech6_hemoglobina", "endes_rech6_medidas"] and r6["temas"] == ["salud_infantil"]
    assert r6["modulo_codigo"] == 1638 and r6["codigo_encuesta"] == 968 and r6["recurso"] == "endes-2024-anemia" and r6["tabla_base"] == "RECH0"
    assert r6["tiene_diseno"] is False and r6["peso"] is None and r6["alcance_territorial"] is None
    r0 = f.filter(pl.col("tabla") == "RECH0").row(0, named=True)
    assert r0["tiene_diseno"] is True and r0["peso"] == "HV005/1e6" and r0["permite_totales"] == "no" and r0["alcance_territorial"].startswith("hasta departamento")
    por = dict(zip(v["var_id"], v["bloque_id"]))
    assert por["ENDES·2024·RECH6·HC1"] == "endes_rech6_medidas" and por["ENDES·2024·RECH6·HC53"] == "endes_rech6_hemoglobina"
    assert por["ENDES·2024·RECH6·HHID"] is None and por["ENDES·2024·RECH0·ID1"] is None and por["ENDES·2024·RECH0·HV005"] is None   # llaves, diseño y pesos sin bloque
    assert res["cobertura"]["RECH6"]["porcentaje"] == 100.0 and res["bloques_por_tabla"] == {"RECH0": 1, "RECH6": 2}


def test_generar_solo_cambia_la_columna_bloque_id(raiz):
    ind = raiz / "biblioteca" / "variables"
    antes = pl.read_parquet(ind / "variables.parquet")
    fi.generar(raiz, "ENDES", 2024)
    despues = pl.read_parquet(ind / "variables.parquet")
    assert despues.columns == antes.columns + ["bloque_id"] and despues["var_id"].to_list() == antes["var_id"].to_list()
    assert all(despues[c].equals(antes[c]) for c in antes.columns)
    fi.generar(raiz, "ENDES", 2024)                                        # con bloque_id ya escrito: lo reemplaza, no duplica
    assert pl.read_parquet(ind / "variables.parquet").columns == despues.columns


def test_dos_corridas_dan_los_mismos_archivos(raiz, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    fi.generar(raiz, "ENDES", 2024, a)
    fi.generar(raiz, "ENDES", 2024, b)
    for n in ("fichas_tabla.parquet", "bloques.parquet", "variables.parquet"):
        assert hashlib.sha256((a / n).read_bytes()).hexdigest() == hashlib.sha256((b / n).read_bytes()).hexdigest()


def test_las_tres_formas_de_declarar_variables(raiz):
    _editar(raiz, "bloques/ENDES.yaml", lambda d: d["bloques"][1].update(variables={"prefijos": ["HC1"], "lista": ["HC27"], "rango": ["HC53", "HC55"]}))
    _editar(raiz, "bloques/ENDES.yaml", lambda d: d["bloques"].pop(2))
    res = fi.generar(raiz, "ENDES", 2024)
    b = pl.read_parquet(raiz / "biblioteca" / "variables" / "bloques.parquet").filter(pl.col("bloque_id") == "endes_rech6_medidas").row(0, named=True)
    assert b["variables"] == ["HC1", "HC27", "HC53", "HC55"] and b["primera_variable"] == "HC1" and b["ultima_variable"] == "HC55"


# ---------------------------------------------------------------- reglas 1 a 8

def test_sin_problemas_el_mundo_sintetico_valida(raiz):
    fi.generar(raiz, "ENDES", 2024)
    probs, info = _validar(raiz)
    assert probs == [] and info["fichas"] == 2 and info["bloques"] == 3 and info["no_comprobado"] == []
    assert info["edades"] and "0–71" in info["edades"][0]


def test_regla_1_toda_tabla_tiene_ficha_y_toda_ficha_una_tabla(raiz):
    _editar(raiz, "fichas/ENDES.yaml", lambda d: d["tablas"].pop("RECH0"))
    _editar(raiz, "bloques/ENDES.yaml", lambda d: d["bloques"].pop(0))
    probs, _ = _validar(raiz)
    assert any(p.regla == 1 and p.objeto == "RECH0" and "no tiene ficha" in p.mensaje for p in probs)
    _editar(raiz, "fichas/ENDES.yaml", lambda d: d["tablas"].update(NOEXISTE=mw.ficha_rech0()))
    probs, _ = _validar(raiz)
    assert any(p.regla == 1 and p.objeto == "NOEXISTE" for p in probs)


def test_regla_2_las_tablas_del_modulo_son_los_datos_del_zip(raiz):
    _editar(raiz, "descargas/endes_2024.yaml", lambda d: d["modulos"][1].update(tablas=["RECH6", "RECH9"]))
    probs, _ = _validar(raiz)
    assert any(p.regla == 2 and "1638" in p.objeto for p in probs)
    _editar(raiz, "descargas/endes_2024.yaml", lambda d: d["modulos"].pop(1))
    probs, _ = _validar(raiz)
    assert any(p.regla == 2 and p.objeto == "RECH6" for p in probs)


@pytest.mark.parametrize("cambio,texto", [
    (lambda d: d["tablas"]["RECH6"].update(tipo_tabla="inventada"), "tipo_tabla"),
    (lambda d: d["tablas"]["RECH6"].update(modo="adivinado"), "modo"),
    (lambda d: d["tablas"]["RECH6"]["poblacion"].update(sujeto="marciano"), "sujeto"),
    (lambda d: d["tablas"]["RECH6"]["poblacion"].update(edad_unidad="dias"), "edad_unidad"),
    (lambda d: d["tablas"]["RECH6"]["poblacion"].update(sexo="otro"), "sexo"),
    (lambda d: d["tablas"]["RECH6"].update(cuestionario="rural"), "cuestionario"),
    (lambda d: d.update(tipo_fuente="rumor"), "tipo_fuente"),
])
def test_regla_3_vocabularios_de_la_ficha(raiz, cambio, texto):
    _editar(raiz, "fichas/ENDES.yaml", cambio)
    probs, _ = _validar(raiz)
    assert any(p.regla == 3 and texto in p.mensaje for p in probs), [str(p) for p in probs]


@pytest.mark.parametrize("cambio,texto", [
    (lambda d: d["bloques"][1].update(papel="estrella"), "papel"),
    (lambda d: d["bloques"][1].update(tema="no_existe"), "temas.yaml"),
    (lambda d: d["bloques"][1].update(subtema="otro_tema"), "subtema"),
    (lambda d: d["bloques"][1].update(tema_estado="a_medias"), "tema_estado"),
])
def test_regla_3_vocabularios_del_bloque_y_los_temas(raiz, cambio, texto):
    _editar(raiz, "bloques/ENDES.yaml", cambio)
    probs, _ = _validar(raiz)
    assert any(p.regla == 3 and texto in p.mensaje for p in probs), [str(p) for p in probs]


def test_regla_4_variable_en_dos_bloques_y_variable_sin_bloque(raiz):
    _editar(raiz, "bloques/ENDES.yaml", lambda d: d["bloques"][2].update(variables={"lista": ["HC53", "HC55", "HC27"]}))
    with pytest.raises(PapError, match="dos bloques"):
        fi.generar(raiz, "ENDES", 2024)
    probs, _ = _validar(raiz)
    assert any(p.regla == 4 and "HC27" in p.objeto and "dos bloques" in p.mensaje for p in probs)
    _editar(raiz, "bloques/ENDES.yaml", lambda d: d["bloques"][2].update(variables={"lista": ["HC53"]}))
    probs, info = _validar(raiz)
    assert any(p.regla == 4 and "HC55" in p.mensaje and "sin bloque" in p.mensaje for p in probs)
    assert info["cobertura"]["RECH6"]["porcentaje"] < 100 and info["cobertura"]["RECH6"]["sin_bloque"] == ["HC55"]


def test_regla_4_una_llave_en_la_lista_es_error_y_en_un_rango_se_salta(raiz):
    _editar(raiz, "bloques/ENDES.yaml", lambda d: d["bloques"][2].update(variables={"lista": ["HC53", "HC55", "HC0"]}))
    probs, _ = _validar(raiz)
    assert any(p.regla == 4 and "HC0" in p.mensaje and "llave" in p.mensaje for p in probs)


def test_regla_4_tabla_sin_bloques_no_exige_cobertura_salvo_que_este_revisada(raiz):
    _editar(raiz, "bloques/ENDES.yaml", lambda d: d["bloques"].pop(0))
    fi.generar(raiz, "ENDES", 2024)
    probs, info = _validar(raiz)
    assert not [p for p in probs if p.regla == 4] and info["cobertura"]["RECH0"]["porcentaje"] == 0.0
    _editar(raiz, "fichas/ENDES.yaml", lambda d: d["tablas"]["RECH0"].update(estado="revisado"))
    probs, _ = _validar(raiz)
    assert any(p.regla == 4 and p.objeto == "RECH0" for p in probs)


def test_regla_5_la_poblacion_del_bloque_no_es_mas_amplia(raiz):
    _editar(raiz, "bloques/ENDES.yaml", lambda d: d["bloques"][1].update(poblacion={"edad_min": 0, "edad_max": 100, "edad_unidad": "meses"}))
    probs, _ = _validar(raiz)
    assert any(p.regla == 5 and "edad_max" in p.mensaje for p in probs)
    _editar(raiz, "bloques/ENDES.yaml", lambda d: d["bloques"][1].update(poblacion={"edad_min": 6, "edad_max": 35, "edad_unidad": "meses"}))
    probs, _ = _validar(raiz)
    assert not [p for p in probs if p.regla == 5]                       # más estrecha: bien
    _editar(raiz, "bloques/ENDES.yaml", lambda d: d["bloques"][1].update(poblacion={"edad_min": 0, "edad_max": 5, "edad_unidad": "anios"}))
    probs, _ = _validar(raiz)
    assert any(p.regla == 5 and "no se pueden comparar" in p.mensaje for p in probs)


def test_regla_5_sexo_del_bloque_distinto_al_de_la_tabla(raiz):
    _editar(raiz, "fichas/ENDES.yaml", lambda d: d["tablas"]["RECH6"]["poblacion"].update(sexo="mujer"))
    _editar(raiz, "bloques/ENDES.yaml", lambda d: d["bloques"][1].update(poblacion={"sexo": "hombre"}))
    probs, _ = _validar(raiz)
    assert any(p.regla == 5 and "sexo" in p.mensaje for p in probs)


def test_regla_6_edad_min_mayor_que_edad_max(raiz):
    _editar(raiz, "fichas/ENDES.yaml", lambda d: d["tablas"]["RECH6"]["poblacion"].update(edad_min=80))
    probs, _ = _validar(raiz)
    assert any(p.regla == 6 and "edad_min 80" in p.mensaje for p in probs)


def test_regla_6_la_edad_observada_cae_dentro_de_la_declarada_y_se_informa(tmp_path):
    raiz = mw.escribir_mundo(tmp_path, edades=(0, 12, 80))               # 80 meses > 71 declarados
    fi.generar(raiz, "ENDES", 2024)
    probs, info = _validar(raiz)
    assert any(p.regla == 6 and "80" in p.mensaje and "máximo 71" in p.mensaje and "diferencia 9" in p.mensaje for p in probs)
    assert "0–80" in info["edades"][0]


def test_regla_6_sin_microdatos_lo_dice_y_con_microdatos_faltantes_falla(raiz, tmp_path):
    probs, info = _validar(raiz, con_microdatos=False)
    assert not [p for p in probs if p.regla == 6] and any("regla 6" in x for x in info["no_comprobado"])
    (raiz / "biblioteca" / "microdatos" / "ENDES" / "2024" / "RECH6.parquet").unlink()
    with pytest.raises(PapError, match="microdatos"):
        _validar(raiz)


def test_regla_7_documento_registrado_y_miembro_en_el_zip(raiz):
    _editar(raiz, "fichas/ENDES.yaml", lambda d: d["tablas"]["RECH6"]["documentos"].append({"recurso": "endes-2024-nada"}))
    probs, _ = _validar(raiz)
    assert any(p.regla == 7 and "endes-2024-nada" in p.mensaje and "no está registrado" in p.mensaje for p in probs)
    _editar(raiz, "fichas/ENDES.yaml", lambda d: d["tablas"]["RECH6"].update(documentos=[{"recurso": "endes-2024-anemia", "miembro": "Diccionario - RECH7.pdf"}]))
    probs, _ = _validar(raiz)
    assert any(p.regla == 7 and "RECH7" in p.mensaje for p in probs)


def test_regla_8_reproducible_y_sin_archivos_viejos(raiz):
    probs, _ = _validar(raiz)                                              # sin haber corrido `generar`
    assert any(p.regla == 8 and "no está generado" in p.mensaje for p in probs)
    fi.generar(raiz, "ENDES", 2024)
    assert _reglas(_validar(raiz)[0]) == []
    _editar(raiz, "bloques/ENDES.yaml", lambda d: d["bloques"][0].update(nombre="Otro nombre"))
    probs, _ = _validar(raiz)
    assert any(p.regla == 8 and "no es lo que da una corrida hoy" in p.mensaje for p in probs)


# ---------------------------------------------------------------- ver y CLI

def test_ver_muestra_la_ficha_completa_en_texto(raiz):
    txt = fi.ver(raiz, "ENDES", 2024, "rech6")
    for frag in ("RECH6", "Peso, talla y hemoglobina", "niñas y niños menores de 6 años", "0–71 meses", "Módulo 1638", "968",
                 "Unión → RECH0 por HHID = HHID (n:1)", "Todavía no", "endes_rech6_medidas", "aviso de prueba", "Diccionario - RECH6.pdf",
                 "100.0 %", "salud_infantil"):
        assert frag in txt, frag
    with pytest.raises(PapError, match="No hay ficha de XYZ"):
        fi.ver(raiz, "ENDES", 2024, "XYZ")


def test_ayuda_de_pap_fichas():
    r = subprocess.run([sys.executable, "-c", "import sys; from pap.cli import main; sys.exit(main(['fichas', '--help']))"],
                       capture_output=True, text=True, cwd=RAIZ_REAL)
    assert r.returncode == 0 and all(x in r.stdout for x in ("generar", "validar", "ver", "--sin-microdatos", "--anio"))


def test_pap_fichas_validar_sale_con_1_si_alguna_regla_falla(raiz, capsys):
    from pap.cli import main
    import pap.config as cfg
    from unittest import mock

    _editar(raiz, "fichas/ENDES.yaml", lambda d: d["tablas"]["RECH6"].update(tipo_tabla="inventada"))
    with mock.patch.object(cfg, "rutas", return_value=cfg.Rutas(raiz)), mock.patch("pap.cli.obtener_rutas", return_value=cfg.Rutas(raiz)), \
            mock.patch.object(fi, "_miembros_zip_real", side_effect=lambda r, f, rec: mw.buscar(rec)):
        assert main(["fichas", "validar", "--sin-microdatos"]) == 1
    assert "tipo_tabla" in capsys.readouterr().out
