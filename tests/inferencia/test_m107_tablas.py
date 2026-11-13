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
        "mujer": ["REC0111", "REC91", "RE223132", "REC42", "RE516171", "RE758081", "RECH5"]}
# README del slice: «Mujer: REC0111, REC91, RE223132, REC42, RE516171, RE758081, RECH5». RECH5 entró con el factor hogar por decisión del dueño (C-M1-07-1).
FUERA = {"REC82", "REC83", "REC84DV", "REC93DVdisciplina", "RECHM", "CSALUD01", "CSALUD08", "Programas_Sociales_x_Hogar", "PS_BECA18",
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

def test_unidades_cubre_las_19_tablas_del_lote_y_no_a_las_que_quedan_fuera():
    u = {x.archivo: x for x in tc.leer_unidades(RAIZ_REAL)}
    assert set(u) == {a for tablas in LOTE.values() for a in tablas} and len(u) == 19
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
    assert {a for a, p in pesos.items() if p == ("HV005", "RECH0")} == {"RECH0", "RECH23", "RECH1", "RECH4", "RECH6", "REC44", "RECH5"}
    assert {a for a, p in pesos.items() if p == ("V005", "REC0111")} == {
        "REC0111", "REC91", "RE223132", "REC42", "RE516171", "RE758081", "REC21", "REC41", "REC43", "REC94", "REC95", "DIT"}


def test_rech5_es_una_mujer_del_plan_con_el_factor_hogar_y_la_unidad_persona_del_hogar_del_indice():
    """C-M1-07-1 (dueño, 13/11/2026): RECH5 entra con HV005 de RECH0, como la medición del niño."""
    u = {x.archivo: x for x in tc.leer_unidades(RAIZ_REAL)}["RECH5"]
    assert (u.unidad_plan, u.unidad_archivo, u.tabla_base, u.peso.variable, u.peso.en) == ("mujer", "persona_del_hogar", "RECH5", "HV005", "RECH0")
    assert "C-M1-07-1" in u.cita and "p. 9" in u.cita and "p. 11" in u.cita
    d = {f.medicion: f for f in tc.leer_diseno_muestral(RAIZ_REAL) if f.archivo == "RECH5"}
    assert set(d) == {"hemoglobina", "talla"}
    for f in d.values():
        assert (f.nivel_submuestra, f.peso_expr, f.estrato_expr, f.psu_expr, f.upm_estable_expr) == (
            "medicion", "HV005/1e6", "printf('%02d-%d', HV024, HV022)", "HV021", "HV001")
        assert f.uniones == [("RECH5", "HHID", "RECH0", "HHID")] and "p. 9" in f.cita and "p. 11" in f.cita
    m = {(x.id, x.archivo): x for x in tc.leer_mediciones(RAIZ_REAL)}
    assert {"HA57A", "HA55"} <= set(m[("hemoglobina", "RECH5")].variables) and {"HA2", "HA3"} <= set(m[("talla", "RECH5")].variables)
    assert not {"HA52", "HA58", "HA61", "HA63", "HA69"} & {v for x in m.values() if x.archivo == "RECH5" for v in x.variables}      # consentimiento y VIH, fuera


def test_rec21_solo_es_puente_y_rec44_tiene_a_rech6_como_alternativa_de_medicion():
    u = {x.archivo: x for x in tc.leer_unidades(RAIZ_REAL)}
    assert [a for a, x in u.items() if x.solo_puente] == ["REC21"]
    assert {a: (x.alternativa_medicion.tabla, x.alternativa_medicion.desde, x.alternativa_medicion.hacia) for a, x in u.items() if x.alternativa_medicion} == {
        "REC44": ("RECH6", "HW", "HC")}


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
    assert res["unidades"] == (19, []) and "unidades" in tc.ARCHIVOS_TABLAS
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


def test_validar_detecta_una_alternativa_de_medicion_mal_declarada(copia):
    def cambio(us):
        fila = us[[u["archivo"] for u in us].index("REC44")]
        fila["alternativa_medicion"]["tabla"] = "REC0111"
    errores = _romper_unidades(copia, cambio)
    assert any("REC44" in e and "REC0111" in e and "no es de la unidad" in e for e in errores), errores

    def sin_fila(us):
        us[[u["archivo"] for u in us].index("REC44")]["alternativa_medicion"]["tabla"] = "RECXX"
    errores = _romper_unidades(copia, sin_fila)
    assert any("REC44" in e and "RECXX" in e and "no tiene fila" in e for e in errores), errores

    def puente_con_alternativa(us):
        us[[u["archivo"] for u in us].index("REC21")]["alternativa_medicion"] = {"tabla": "RECH6", "desde": "B", "hacia": "HC"}
    errores = _romper_unidades(copia, puente_con_alternativa)
    assert any("REC21" in e and "puente" in e for e in errores), errores


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
    assert not {a for a, _ in d} & {"REC82", "REC83", "REC84DV", "REC93DVdisciplina", "RECHM"}
    for f in d.values():
        assert "p. " in f.cita and "Ficha técnica ENDES 2024" in f.cita


# ------------------------------------------------------------------ universos y uniones

def test_los_universos_nuevos_con_sus_predicados_y_sus_tablas():
    u = {x.id: x for x in tc.leer_universos(RAIZ_REAL)}
    assert tc.sql_predicados(u["hogar"].predicados) == "HV015 IN (1)" and u["hogar"].unidad == "hogar"
    assert tc.sql_predicados(u["persona_de_hecho"].predicados) == "HV103 IN (1)" and u["persona_de_hecho"].unidad == "persona"
    # C-M1-07-3 (b): 15 a 49 años por defecto; 12 a 49 solo cuando se nombra
    assert tc.sql_predicados(u["mujer_15_49_entrevistada"].predicados) == "V015 IN (1) AND V012 BETWEEN 15 AND 49" and not u["mujer_15_49_entrevistada"].solo_por_nombre
    assert tc.sql_predicados(u["mujer_12_49_entrevistada"].predicados) == "V015 IN (1) AND V012 BETWEEN 12 AND 49" and u["mujer_12_49_entrevistada"].solo_por_nombre
    assert tc.sql_predicados(u["nino_hijo_de_entrevistada"].predicados) == "V015 IN (1) AND V012 BETWEEN 15 AND 49" and not u["nino_hijo_de_entrevistada"].solo_por_nombre
    assert tc.sql_predicados(u["nino_hijo_de_entrevistada_12_49"].predicados) == "V015 IN (1) AND V012 BETWEEN 12 AND 49" and u["nino_hijo_de_entrevistada_12_49"].solo_por_nombre
    assert sorted(x.id for x in u.values() if x.solo_por_nombre) == ["mujer_12_49_entrevistada", "nino_hijo_de_entrevistada_12_49"]
    assert "nino_hijo_de_entrevistada_15_49" not in u
    # C-M1-07-2: el niño vivo (B5 = 1) y su batería
    assert tc.sql_predicados(u["nino_vivo_hijo_de_entrevistada"].predicados) == "V015 IN (1) AND V012 BETWEEN 15 AND 49 AND B5 IN (1)"
    assert u["nino_vivo_hijo_de_entrevistada"].aplica_a.mediciones == ["nino_vivo"] and u["nino_hijo_de_entrevistada"].aplica_a.mediciones == []
    assert "REC44" not in u["nino_hijo_de_entrevistada"].aplica_a.archivos and "REC44" not in u["nino_vivo_hijo_de_entrevistada"].aplica_a.archivos
    # C-M1-07-3 (a): todo universo que cubre REC44 exige el pernocte del niño (HV103 de RECH1)
    de_rec44 = [x for x in u.values() if "REC44" in x.aplica_a.archivos]
    assert sorted(x.id for x in de_rec44) == ["nino_hijo_de_entrevistada_de_hecho", "nino_hijo_de_entrevistada_hb_medida", "nino_hijo_de_entrevistada_talla"]
    for x in de_rec44:
        assert "RECH1" in x.aplica_a.archivos and "HV103 IN (1)" in tc.sql_predicados(x.predicados) and "V012 BETWEEN 15 AND 49" in tc.sql_predicados(x.predicados)
    assert tc.sql_predicados(u["nino_hijo_de_entrevistada_hb_medida"].predicados).endswith("HW55 IN (0)")
    assert tc.sql_predicados(u["nino_hijo_de_entrevistada_talla"].predicados).endswith("HW1 BETWEEN 0 AND 59 AND HW70 BETWEEN -9989 AND 9989")
    # C-M1-07-1: la mujer de hecho de 15 a 49 de RECH5 y, para la hemoglobina, medida
    assert tc.sql_predicados(u["mujer_15_49_de_hecho"].predicados) == "HV103 IN (1) AND HA1 BETWEEN 15 AND 49"
    assert tc.sql_predicados(u["mujer_15_49_de_hecho_hb_medida"].predicados) == "HV103 IN (1) AND HA1 BETWEEN 15 AND 49 AND HA55 IN (0)"
    assert u["mujer_15_49_de_hecho"].aplica_a.archivos == ["RECH5", "RECH1"] and u["mujer_15_49_de_hecho_hb_medida"].aplica_a.mediciones == ["hemoglobina"]
    for x in u.values():
        assert tc._DONDE.search(x.fuente)
    # cada tabla del lote la cubre al menos un universo de su unidad que el verificador pueda elegir solo
    unidades = {x.archivo: x for x in tc.leer_unidades(RAIZ_REAL)}
    for a, x in unidades.items():
        if x.solo_puente:
            continue
        assert any(a in v.aplica_a.archivos for v in u.values() if v.unidad == x.unidad_plan and not v.solo_por_nombre), a


def test_la_bateria_del_nino_vivo_cubre_vacunas_diarrea_lactancia_suplementos_y_dit_y_no_el_parto():
    m = {(x.id, x.archivo): set(x.variables) for x in tc.leer_mediciones(RAIZ_REAL)}
    assert {a for (i, a) in m if i == "nino_vivo"} == {"REC43", "REC95", "DIT", "REC41", "REC94"}
    assert {"H1", "H11", "H22", "H42"} <= m[("nino_vivo", "REC43")]                                   # carné, diarrea, fiebre y tos, hierro
    assert {"S45B0", "S466", "S472AA", "S465EA"} <= m[("nino_vivo", "REC95")]                          # vacunas, control de crecimiento, diarrea, hierro
    assert {"M4", "M34"} <= m[("nino_vivo", "REC41")] and not {"M17", "M15", "M19"} & m[("nino_vivo", "REC41")]   # lactancia sí; cesárea, lugar y peso del parto no
    assert not {"S410B", "S426B"} & m[("nino_vivo", "REC94")]                                          # controles prenatales y complicaciones del parto, no
    assert len(m[("nino_vivo", "DIT")]) > 40


def test_las_uniones_nuevas_estan_declaradas_con_su_cardinalidad():
    d = yaml.safe_load((RAIZ_REAL / "curados/inferencia/archivos_endes_2024.yaml").read_text(encoding="utf-8"))
    rel = {(r["hijo"], r["padre"]): r for r in d["relaciones"]}
    for hijo, idx in (("REC41", "MIDX"), ("REC43", "HIDX"), ("REC44", "HWIDX"), ("REC94", "IDX94"), ("REC95", "IDX95"), ("DIT", "BIDX")):
        r = rel[(hijo, "REC21")]
        assert r["por"] == [["CASEID", "CASEID"], [idx, "BIDX"]] and r["cardinalidad"] == "1:0..1" and r["cita"] == "doc11_caseid"
    assert rel[("RECH4", "RECH1")]["cardinalidad"] == "1:1" and rel[("RECH4", "RECH1")]["por"] == [["HHID", "HHID"], ["IDXH4", "HVIDX"]]
    assert rel[("REC91", "REC0111")]["cardinalidad"] == "1:1"
    # C-M1-07-1 y -3: el pernocte de la mujer medida (HA0 = HVIDX) y el del niño (B16 = HVIDX), `n:1` hacia RECH1
    assert rel[("RECH5", "RECH1")]["por"] == [["HHID", "HHID"], ["HA0", "HVIDX"]] and rel[("RECH5", "RECH1")]["cardinalidad"] == "n:1"
    # la del niño tiene filas sin pareja (B16 = 0 o nulo): va en `relaciones_parciales`, que el índice no comprueba como «sin pérdida»
    parcial = {(r["hijo"], r["padre"]): r for r in d["relaciones_parciales"]}
    assert list(parcial) == [("REC21", "RECH1")] and ("REC21", "RECH1") not in rel
    assert parcial[("REC21", "RECH1")]["por"] == [["HHID", "HHID"], ["B16", "HVIDX"]]
    assert parcial[("REC21", "RECH1")]["cita"] == rel[("RECH5", "RECH1")]["cita"] == "doc11_hvidx"
    # las uniones del hijo con REC21 van antes que las del hijo con REC0111: a RECH1 se llega por la línea del niño y no por la de la madre (V003)
    orden = [(r["hijo"], r["padre"]) for r in d["relaciones"]]
    for hijo in ("REC41", "REC43", "REC44", "REC94", "REC95", "DIT"):
        assert orden.index((hijo, "REC21")) < orden.index((hijo, "REC0111"))
    assert orden.index(("RECH4", "RECH0")) < orden.index(("RECH4", "RECH1"))


def test_a_rech1_desde_las_tablas_del_nino_se_llega_por_la_linea_del_nino_y_no_por_la_de_la_madre():
    """C-M1-07-3: REC0111 → RECH1 (V003) es la fila de la madre; HV103 del niño sale de REC21 → RECH1 (B16). Fija el orden de las relaciones."""
    from pap.inferencia.verificador import relaciones_desde_yaml, ruta_de_uniones
    d = yaml.safe_load((RAIZ_REAL / "curados/inferencia/archivos_endes_2024.yaml").read_text(encoding="utf-8"))
    rels = relaciones_desde_yaml(d)
    for hijo in ("REC41", "REC43", "REC44", "REC94", "REC95", "DIT"):
        ruta = ruta_de_uniones(rels, hijo, {"RECH1"})
        assert [(u.hijo, u.padre) for u in ruta] == [(hijo, "REC21"), ("REC21", "RECH1")], hijo
    # la mujer medida y la mujer de REC0111 no cambian
    assert {(u.hijo, u.padre) for u in ruta_de_uniones(rels, "RECH5", {"RECH1", "RECH0"})} == {("RECH5", "RECH1"), ("RECH5", "RECH0")}
    assert [(u.hijo, u.padre) for u in ruta_de_uniones(rels, "REC41", {"RECH0", "REC0111"})] == [("REC41", "REC0111"), ("REC0111", "RECH0")]
