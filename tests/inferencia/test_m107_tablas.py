"""M1-07 (sin microdatos): las tablas curadas del lote de niño, mujer y hogar — `unidades.yaml`, las filas nuevas de `diseno_muestral.csv`,
los universos nuevos, las uniones nuevas y la validación cruzada (`pap inferencia validar-tablas`). Con datos reales están en
`test_m107_microdatos.py`."""
import csv
import shutil

import pytest
import yaml
from pydantic import ValidationError

from pap.config import Rutas
from pap.inferencia import tablas_curadas as tc

from conftest import RAIZ_REAL

LOTE = {"hogar": ["RECH0", "RECH23", "RECH1", "RECH4"],
        "nino": ["RECH6", "REC21", "REC41", "REC43", "REC44", "REC94", "REC95", "DIT"],
        "mujer": ["REC0111", "REC91", "RE223132", "REC42", "RE516171", "RE758081"]}
# README del slice: «Mujer: REC0111, REC91, RE223132, REC42, RE516171, RE758081, RECH5». RECH5 sale: la ficha técnica no dice su peso (C-M1-07-1).
FUERA = {"REC82", "REC83", "REC84DV", "REC93DVdisciplina", "RECHM", "RECH5", "CSALUD01", "CSALUD08", "Programas_Sociales_x_Hogar", "PS_BECA18",
         "PS_COMEDOR", "PS_PENSION65", "PS_QALIWARMA", "PS_TRABAJA", "PS_VL", "PS_WAWAWASI"}


@pytest.fixture
def copia(tmp_path):
    for rel in ("curados/inferencia", "curados/capa0/dim_indicador.yaml"):
        origen, destino = RAIZ_REAL / rel, tmp_path / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        if origen.is_dir():
            shutil.copytree(origen, destino, ignore=shutil.ignore_patterns("descargas"))
        else:
            shutil.copy(origen, destino)
    return tmp_path


def _sin_lineas(errores):
    return [e for e in errores if not e.startswith("cita con archivo:línea")]


# ------------------------------------------------------------------ unidades.yaml

def test_unidades_cubre_las_18_tablas_del_lote_y_no_a_las_que_quedan_fuera():
    u = {x.archivo: x for x in tc.leer_unidades(RAIZ_REAL)}
    assert set(u) == {a for tablas in LOTE.values() for a in tablas} and len(u) == 18
    assert not set(u) & FUERA
    # el «Hogar» del README incluye a las personas del hogar (RECH1, RECH4), que son la unidad `persona` del plan
    assert {a: u[a].unidad_plan for a in LOTE["hogar"]} == {"RECH0": "hogar", "RECH23": "hogar", "RECH1": "persona", "RECH4": "persona"}
    assert {u[a].unidad_plan for a in LOTE["nino"]} == {"nino"} and {u[a].unidad_plan for a in LOTE["mujer"]} == {"mujer"}


def test_cada_tabla_dice_su_unidad_su_base_y_de_donde_sale_su_peso_con_cita_y_pagina():
    u = {x.archivo: x for x in tc.leer_unidades(RAIZ_REAL)}
    for x in u.values():
        assert tc._DONDE.search(x.cita) and "Ficha técnica ENDES 2024" in x.cita, x.archivo
        assert x.tabla_base in u and u[x.tabla_base].unidad_plan == x.unidad_plan
    pesos = {a: (x.peso.variable, x.peso.en) for a, x in u.items()}
    assert {a for a, p in pesos.items() if p == ("HV005", "RECH0")} == {"RECH0", "RECH23", "RECH1", "RECH4", "RECH6", "REC44"}
    assert {a for a, p in pesos.items() if p == ("V005", "REC0111")} == {
        "REC0111", "REC91", "RE223132", "REC42", "RE516171", "RE758081", "REC21", "REC41", "REC43", "REC94", "REC95", "DIT"}


def test_rech6_es_persona_del_hogar_para_el_indice_y_nino_para_el_plan():
    """Nota de C-M1-06-1: el corte del niño lleva `unidad: nino` y el índice declara RECH6 como persona_del_hogar; se resuelve aquí."""
    u = {x.archivo: x for x in tc.leer_unidades(RAIZ_REAL)}
    assert (u["RECH6"].unidad_plan, u["RECH6"].unidad_archivo) == ("nino", "persona_del_hogar")
    archivos = yaml.safe_load((RAIZ_REAL / "curados/inferencia/archivos_endes_2024.yaml").read_text(encoding="utf-8"))["archivos"]
    assert all(archivos[a]["unidad"] == x.unidad_archivo for a, x in u.items())
    cortes = {(v.archivo, v.variable): v for c in tc.leer_cortes(RAIZ_REAL) for v in c.por_encuesta["ENDES"]}
    assert cortes[("RECH6", "HC27")].unidad == "nino"                                 # sin renombrar la unidad del corte


def test_el_esquema_de_unidades_rechaza_lo_que_debe():
    base = {"archivo": "RECH6", "encuesta": "ENDES", "anios": [2024, 2024], "unidad_plan": "nino", "unidad_archivo": "persona_del_hogar",
            "tabla_base": "RECH6", "peso": {"variable": "HV005", "en": "RECH0"}, "cita": "Ficha técnica ENDES 2024, §VI p. 11"}
    assert tc.UnidadTabla.model_validate(base).peso.en == "RECH0"
    for cambio in ({"unidad_plan": "ninio"}, {"cita": "la ficha técnica"}, {"cita": ""}, {"peso": {"variable": "hv005", "en": "RECH0"}},
                   {"anios": [2025, 2024]}, {"extra": 1}):
        with pytest.raises(ValidationError):
            tc.UnidadTabla.model_validate({**base, **cambio})


def test_validar_tablas_con_las_unidades_reales_sale_sin_errores():
    res = tc.validar(Rutas(RAIZ_REAL))
    assert res["unidades"] == (18, []) and "unidades" in tc.ARCHIVOS_TABLAS
    assert all(errores == [] for _, errores in res.values())


def _romper_unidades(copia, cambio):
    ruta = copia / "curados/inferencia/unidades.yaml"
    d = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    cambio(d["unidades"])
    ruta.write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")
    return _sin_lineas(tc.validar(Rutas(copia))["unidades"][1])


def test_validar_detecta_una_unidad_de_archivo_distinta_de_la_del_indice(copia):
    errores = _romper_unidades(copia, lambda us: us[[u["archivo"] for u in us].index("RECH6")].update(unidad_archivo="hogar"))
    assert any("RECH6" in e and "archivos_endes_2024.yaml declara «persona_del_hogar»" in e for e in errores), errores


def test_validar_detecta_una_tabla_base_de_otra_unidad_o_sin_fila(copia):
    errores = _romper_unidades(copia, lambda us: us[[u["archivo"] for u in us].index("REC41")].update(tabla_base="REC0111"))
    assert any("REC41" in e and "no de «nino»" in e for e in errores), errores
    errores = _romper_unidades(copia, lambda us: us[[u["archivo"] for u in us].index("REC41")].update(tabla_base="RECH5"))
    assert any("REC41" in e and "RECH5" in e for e in errores), errores


def test_validar_detecta_un_peso_que_no_es_el_del_diseno(copia):
    errores = _romper_unidades(copia, lambda us: us[[u["archivo"] for u in us].index("REC41")].update(peso={"variable": "HV005", "en": "RECH0"}))
    assert any("REC41" in e and "peso declarado es HV005" in e for e in errores), errores
    errores = _romper_unidades(copia, lambda us: us[[u["archivo"] for u in us].index("REC41")].update(peso={"variable": "V005", "en": "RECH0"}))
    assert any("REC41" in e and "no es la tabla ni un padre" in e for e in errores), errores


def test_validar_detecta_una_tabla_sin_fila_de_diseno(copia):
    ruta = copia / "curados/inferencia/diseno_muestral.csv"
    filas = list(csv.DictReader(ruta.open(encoding="utf-8", newline="")))
    with ruta.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(x for x in filas if x["archivo"] != "RE223132")
    errores = _sin_lineas(tc.validar(Rutas(copia))["unidades"][1])
    assert any("RE223132" in e and "no tiene fila en diseno_muestral.csv" in e for e in errores), errores


def test_validar_detecta_una_unidad_de_corte_que_no_es_la_de_su_tabla(copia):
    ruta = copia / "curados/inferencia/cortes_estandar.yaml"
    ruta.write_text(ruta.read_text(encoding="utf-8").replace("variable: HC27\n          unidad: nino", "variable: HC27\n          unidad: mujer"),
                    encoding="utf-8")
    errores = _sin_lineas(tc.validar(Rutas(copia))["unidades"][1])
    assert any("sexo" in e and "HC27" in e and "«mujer»" in e for e in errores), errores


# ------------------------------------------------------------------ diseno_muestral.csv

def test_el_diseno_tiene_una_fila_por_tabla_y_medicion_del_lote_con_su_peso():
    d = {(f.archivo, f.medicion): f for f in tc.leer_diseno_muestral(RAIZ_REAL)}
    esperadas = {("RECH1", "miembros_del_hogar"): "hogar", ("RECH4", "miembros_del_hogar"): "hogar", ("REC44", "hemoglobina"): "medicion",
                 ("REC44", "talla"): "medicion"}
    esperadas |= {(a, "individual_mujer"): "individual" for a in ("REC91", "RE223132", "REC42", "RE516171", "RE758081")}
    esperadas |= {(a, "individual_hijo"): "individual" for a in ("REC21", "REC41", "REC43", "REC94", "REC95", "DIT")}
    for k, nivel in esperadas.items():
        assert d[k].nivel_submuestra == nivel, k
    # las tablas del cuestionario individual usan el peso de la mujer (V005) por REC0111
    for a, m in [*((a, "individual_mujer") for a in ("REC91", "RE223132", "REC42", "RE516171", "RE758081")),
                 *((a, "individual_hijo") for a in ("REC21", "REC41", "REC43", "REC94", "REC95", "DIT"))]:
        f = d[(a, m)]
        assert (f.peso_expr, f.psu_expr, f.upm_estable_expr) == ("V005/1e6", "V021", "V001"), a
        assert f.uniones == [(a, "CASEID", "REC0111", "CASEID")], a
    # REC44 repite las mediciones del niño: el factor hogar, por la madre
    for m in ("hemoglobina", "talla"):
        f = d[("REC44", m)]
        assert (f.peso_expr, f.psu_expr) == ("HV005/1e6", "HV021")
        assert f.uniones == [("REC44", "CASEID", "REC0111", "CASEID"), ("REC0111", "HHID", "RECH0", "HHID")]
    assert d[("RECH1", "miembros_del_hogar")].uniones == [("RECH1", "HHID", "RECH0", "HHID")]
    assert not {a for a, _ in d} & {"RECH5", "REC82", "REC83", "REC84DV", "REC93DVdisciplina", "RECHM"}
    for f in d.values():
        assert "p. " in f.cita and "Ficha técnica ENDES 2024" in f.cita


# ------------------------------------------------------------------ universos y uniones

def test_los_universos_nuevos_con_sus_predicados_y_sus_tablas():
    u = {x.id: x for x in tc.leer_universos(RAIZ_REAL)}
    assert tc.sql_predicados(u["hogar"].predicados) == "HV015 IN (1)" and u["hogar"].unidad == "hogar"
    assert tc.sql_predicados(u["persona_de_hecho"].predicados) == "HV103 IN (1)" and u["persona_de_hecho"].unidad == "persona"
    assert tc.sql_predicados(u["mujer_12_49_entrevistada"].predicados) == "V015 IN (1) AND V012 BETWEEN 12 AND 49"
    assert tc.sql_predicados(u["mujer_15_49_entrevistada"].predicados) == "V015 IN (1) AND V012 BETWEEN 12 AND 49 AND V012 BETWEEN 15 AND 49"
    assert tc.sql_predicados(u["nino_hijo_de_entrevistada"].predicados) == "V015 IN (1) AND V012 BETWEEN 12 AND 49"
    assert tc.sql_predicados(u["nino_hijo_de_entrevistada_hb_medida"].predicados).endswith("HW55 IN (0)")
    assert tc.sql_predicados(u["nino_hijo_de_entrevistada_talla"].predicados).endswith("HW1 BETWEEN 0 AND 59 AND HW70 BETWEEN -9989 AND 9989")
    # el de 12 a 49 está contenido en el de 15 a 49 (la regla de la base común elige el más amplio sin que nadie lo diga)
    for ancho, angosto in (("mujer_12_49_entrevistada", "mujer_15_49_entrevistada"), ("nino_hijo_de_entrevistada", "nino_hijo_de_entrevistada_15_49")):
        a = {(p.var, p.op, tuple(p.valores)) for p in u[ancho].predicados}
        b = {(p.var, p.op, tuple(p.valores)) for p in u[angosto].predicados}
        assert a < b
    for x in u.values():
        assert tc._DONDE.search(x.fuente)
    # cada tabla del lote la cubre al menos un universo de su unidad
    unidades = {x.archivo: x for x in tc.leer_unidades(RAIZ_REAL)}
    for a, x in unidades.items():
        assert any(a in v.aplica_a.archivos for v in u.values() if v.unidad == x.unidad_plan), a


def test_las_uniones_nuevas_estan_declaradas_con_su_cardinalidad():
    d = yaml.safe_load((RAIZ_REAL / "curados/inferencia/archivos_endes_2024.yaml").read_text(encoding="utf-8"))
    rel = {(r["hijo"], r["padre"]): r for r in d["relaciones"]}
    for hijo, idx in (("REC41", "MIDX"), ("REC43", "HIDX"), ("REC44", "HWIDX"), ("REC94", "IDX94"), ("REC95", "IDX95"), ("DIT", "BIDX")):
        r = rel[(hijo, "REC21")]
        assert r["por"] == [["CASEID", "CASEID"], [idx, "BIDX"]] and r["cardinalidad"] == "1:0..1" and r["cita"] == "doc11_caseid"
    assert rel[("RECH4", "RECH1")]["cardinalidad"] == "1:1" and rel[("RECH4", "RECH1")]["por"] == [["HHID", "HHID"], ["IDXH4", "HVIDX"]]
    assert rel[("REC91", "REC0111")]["cardinalidad"] == "1:1"
    # las uniones de siempre hacia la mujer y el hogar siguen antes que las nuevas (el camino corto no cambia)
    orden = [(r["hijo"], r["padre"]) for r in d["relaciones"]]
    for hijo in ("REC41", "REC43", "REC44", "REC94", "REC95", "DIT"):
        assert orden.index((hijo, "REC0111")) < orden.index((hijo, "REC21"))
    assert orden.index(("RECH4", "RECH0")) < orden.index(("RECH4", "RECH1"))
