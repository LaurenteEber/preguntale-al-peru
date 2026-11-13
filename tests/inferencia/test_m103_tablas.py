"""M1-03, sin microdatos: la tabla de mediciones, la definición de cortes con tramos y categorías agrupadas, las doradas por corte
(esquema, validación y la comparación con estimaciones armadas a mano) y las recetas con los tres cortes habilitados."""
import csv
import shutil

import pytest
import yaml
from pydantic import ValidationError

from pap.config import Rutas
from pap.inferencia import recetas as rc
from pap.inferencia import tablas_curadas as tc
from pap.inferencia.estimacion import Estimacion

from conftest import RAIZ_REAL

CITA = "Ficha técnica ENDES 2024, §VI p. 11"
IDS = ("endes_anemia_6_35m", "endes_anemia_6_35m_oms2024", "endes_dci_menores_5")


@pytest.fixture
def copia(tmp_path):
    for rel in ("curados/inferencia", "curados/capa0/dim_indicador.yaml", "curados/capa0/cifras_doradas.csv"):
        origen, destino = RAIZ_REAL / rel, tmp_path / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(origen, destino, ignore=shutil.ignore_patterns("descargas")) if origen.is_dir() else shutil.copy(origen, destino)
    return tmp_path


def _sin_lineas(errores):
    return [e for e in errores if not e.startswith("cita con archivo:línea")]


def _corte(id_):
    return {c.id: c for c in tc.leer_cortes(RAIZ_REAL)}[id_]


def _variable(corte, archivo):
    return next(v for v in corte.por_encuesta["ENDES"] if v.archivo == archivo)


# ------------------------------------------------------------------ mediciones.yaml

def test_la_tabla_de_mediciones_declara_hemoglobina_y_talla_de_rech6_con_su_bateria():
    """M1-07 agregó las mismas dos mediciones para REC44 (los hijos de las entrevistadas): aquí se mira la de RECH6."""
    todas = tc.leer_mediciones(RAIZ_REAL)
    assert {(x.id, x.archivo) for x in todas} == {("hemoglobina", "RECH6"), ("talla", "RECH6"), ("hemoglobina", "REC44"), ("talla", "REC44")}
    m = {x.id: x for x in todas if x.archivo == "RECH6"}
    for x in todas:
        assert (x.encuesta, x.anios) == ("ENDES", (2024, 2024)) and x.bateria and tc._DONDE.search(x.cita)
    assert {"HC53", "HC55", "HC56", "HC56A", "HC57", "HC57A"} <= set(m["hemoglobina"].variables)
    assert {"HC70", "HC71", "HC72", "HC73"} <= set(m["talla"].variables)
    assert not set(m["hemoglobina"].variables) & set(m["talla"].variables)
    assert "HC1" not in m["hemoglobina"].variables + m["talla"].variables                    # la edad no es una medición


def test_medicion_de_busca_por_encuesta_anio_archivo_y_variable():
    m = tc.leer_mediciones(RAIZ_REAL)
    assert tc.medicion_de(m, "ENDES", 2024, "RECH6", "HC57") == "hemoglobina"
    assert tc.medicion_de(m, "ENDES", 2024, "RECH6", "HC70") == "talla"
    assert tc.medicion_de(m, "ENDES", 2024, "RECH6", "HC1") is None
    assert tc.medicion_de(m, "ENDES", 2024, "RECH1", "HC57") is None                       # otro archivo
    assert tc.medicion_de(m, "ENDES", 2023, "RECH6", "HC57") is None                       # otro año


def test_las_siete_tablas_validan_con_mediciones():
    res = tc.validar(Rutas(RAIZ_REAL))
    assert "mediciones" in res and res["mediciones"] == (4, [])
    assert tc.ARCHIVOS_TABLAS["mediciones"] == "mediciones.yaml" and "mediciones" in tc.LECTORES


def _medicion(**cambios):
    base = {"id": "hemoglobina", "encuesta": "ENDES", "anios": [2024, 2024], "archivo": "RECH6", "bateria": "Hemoglobina",
            "variables": ["HC55"], "cita": CITA}
    return {**base, **cambios}


def test_el_esquema_de_la_medicion_rechaza_lo_que_debe():
    assert tc.Medicion.model_validate(_medicion()).variables == ["HC55"]
    for cambio, texto in (({"variables": []}, "al menos una"), ({"variables": ["hc55"]}, "no permitido"), ({"variables": ["HC55", "HC55"]}, "repite"),
                          ({"cita": "sin dónde"}, "no dice dónde"), ({"anios": [2025, 2024]}, "primero"), ({"campo_nuevo": 1}, "Extra"),
                          ({"bateria": " "}, "batería")):
        with pytest.raises(ValidationError, match=texto):
            tc.Medicion.model_validate(_medicion(**cambio))


def _reescribir_mediciones(raiz, f):
    ruta = raiz / tc.CARPETA / "mediciones.yaml"
    d = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    f(d)
    ruta.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_validar_detecta_una_variable_en_dos_mediciones_un_archivo_inexistente_y_una_medicion_sin_universo(copia):
    _reescribir_mediciones(copia, lambda d: d["mediciones"][1]["variables"].append("HC57"))
    errores = _sin_lineas(tc.validar(Rutas(copia))["mediciones"][1])
    assert len(errores) == 1 and "HC57" in errores[0] and "hemoglobina" in errores[0] and "talla" in errores[0]
    _reescribir_mediciones(copia, lambda d: (d["mediciones"][1]["variables"].remove("HC57"), d["mediciones"][1].update(archivo="NO_EXISTE")))
    errores = _sin_lineas(tc.validar(Rutas(copia))["mediciones"][1])
    assert any("NO_EXISTE" in e and "archivos_endes_2024.yaml" in e for e in errores)
    _reescribir_mediciones(copia, lambda d: d["mediciones"][1].update(archivo="RECH6", id="peso_inventado"))
    errores = _sin_lineas(tc.validar(Rutas(copia))["mediciones"][1])
    assert any("peso_inventado" in e and "ningún universo" in e for e in errores)


# ------------------------------------------------------------------ definir_corte

def test_definir_corte_simple_deja_los_codigos():
    d = tc.definir_corte(_corte("quintil_riqueza"), _variable(_corte("quintil_riqueza"), "RECH23"), "endes_dci_menores_5")
    assert d.categorias == {1: "los más pobres", 2: "pobre", 3: "medio", 4: "rico", 5: "más rico"} and d.reglas == ()


def test_definir_corte_agrupado_une_costa_y_conserva_el_orden():
    c = _corte("region_natural")
    d = tc.definir_corte(c, _variable(c, "RECH23"), None)
    assert d.categorias == {"Costa": "Costa", "Sierra": "Sierra", "Selva": "Selva"}
    assert [(r.rotulo, r.codigos, r.rango) for r in d.reglas] == [("Costa", (1, 2), None), ("Sierra", (3,), None), ("Selva", (4,), None)]


def test_definir_corte_con_tramos_elige_el_juego_de_la_receta():
    c = _corte("grupo_edad")
    v = _variable(c, "RECH6")
    anemia = tc.definir_corte(c, v, "endes_anemia_6_35m_oms2024")
    assert [(r.rotulo, r.rango, r.codigos) for r in anemia.reglas][:2] == [("6 a 8 meses", (6, 8), ()), ("9 a 11 meses", (9, 11), ())]
    assert list(anemia.categorias) == [r.rotulo for r in anemia.reglas] and len(anemia.reglas) == 5
    dci = tc.definir_corte(c, v, "endes_dci_menores_5")
    assert [(r.rotulo, r.rango) for r in dci.reglas] == [("Menores de 36 meses", (0, 35)), ("De 36 a 59 meses", (36, 59))]


def test_definir_corte_con_tramos_sin_receta_o_con_receta_sin_juego_no_se_puede():
    c = _corte("grupo_edad")
    v = _variable(c, "RECH6")
    for receta in (None, "endes_otra"):
        with pytest.raises(tc.CorteNoCompilable, match="receta"):
            tc.definir_corte(c, v, receta)


def test_definir_corte_pendiente_no_se_puede():
    c = _corte("grupo_edad")
    with pytest.raises(tc.CorteNoCompilable, match="C-M0-06-2"):
        tc.definir_corte(c, _variable(c, "RECH1"), "endes_anemia_6_35m")


def test_los_tramos_del_nino_ya_no_estan_pendientes_de_m1_03():
    assert _variable(_corte("grupo_edad"), "RECH6").pendiente is None


# ------------------------------------------------------------------ las recetas con los tres cortes

def test_las_tres_recetas_permiten_area_sexo_grupo_edad_region_natural_y_quintil():
    for r in rc.leer_recetas(RAIZ_REAL):
        assert r.cortes_permitidos == ("area", "sexo", "grupo_edad", "region_natural", "quintil_riqueza"), r.id
        assert r.cortes_no_permitidos == ()
        p = r.a_plan(2024, cortes=("grupo_edad", "region_natural", "quintil_riqueza"))
        assert p.cortes == ("grupo_edad", "region_natural", "quintil_riqueza") and p.universo_analitico == r.universo_analitico


def test_a_plan_aun_rechaza_un_corte_que_no_esta_permitido():
    with pytest.raises(rc.PapError, match="no permite los cortes"):
        rc.leer_receta(RAIZ_REAL, "endes_dci_menores_5").a_plan(2024, cortes=("lengua_materna",))


# ------------------------------------------------------------------ doradas por corte: esquema y archivo

def _fila(**cambios):
    base = {"id_cifra": "DOR-X-1", "receta_id": "endes_dci_menores_5", "anio": 2024, "nivel": "nacional", "territorio": "PE",
            "corte": "region_natural", "categoria": "Costa", "valor_publicado": 7.3, "decimales": 1, "casos_publicados": 8047,
            "cita": "INEI, Cuadro N.º 04 p. 49 (PDF 51)"}
    return {**base, **cambios}


def test_el_esquema_de_la_dorada_por_corte_rechaza_lo_que_debe():
    d = rc.DoradaCorte.model_validate(_fila())
    assert (d.corte, d.categoria, d.valor_publicado, d.casos_publicados) == ("region_natural", "Costa", 7.3, 8047)
    for cambio, texto in (({"cita": "Cuadro 4"}, "no dice dónde"), ({"campo": 1}, "Extra"), ({"decimales": -1}, "greater"),
                          ({"casos_publicados": 0}, "greater"), ({"categoria": " "}, "categoría")):
        with pytest.raises(ValidationError, match=texto):
            rc.DoradaCorte.model_validate(_fila(**cambio))


def test_las_doradas_por_corte_del_repo_son_36_y_tienen_cuadro_y_pagina():
    doradas = rc.leer_doradas_cortes(RAIZ_REAL)
    assert len(doradas) == 36 and len({d.id_cifra for d in doradas}) == 36
    por = {}
    for d in doradas:
        por.setdefault((d.receta_id, d.corte), []).append(d)
        assert "Cuadro" in d.cita and "p. " in d.cita and "PDF" in d.cita and d.casos_publicados and d.anio == 2024
        assert (d.nivel, d.territorio) == ("nacional", "PE")
    assert {k: len(v) for k, v in por.items()} == {
        ("endes_dci_menores_5", "region_natural"): 3, ("endes_dci_menores_5", "quintil_riqueza"): 5, ("endes_dci_menores_5", "grupo_edad"): 2,
        ("endes_anemia_6_35m", "region_natural"): 3, ("endes_anemia_6_35m", "quintil_riqueza"): 5, ("endes_anemia_6_35m", "grupo_edad"): 5,
        ("endes_anemia_6_35m_oms2024", "region_natural"): 3, ("endes_anemia_6_35m_oms2024", "quintil_riqueza"): 5,
        ("endes_anemia_6_35m_oms2024", "grupo_edad"): 5}


def test_cifras_doradas_csv_no_se_toca():
    ids = {r["id_cifra"] for r in csv.DictReader(open(RAIZ_REAL / rc.DORADAS, encoding="utf-8", newline=""))}
    assert not {d.id_cifra for d in rc.leer_doradas_cortes(RAIZ_REAL)} & ids


def test_validar_recetas_del_repo_sigue_sin_errores_con_las_doradas_por_corte():
    res = rc.validar(Rutas(RAIZ_REAL))
    assert sorted(res) == sorted(IDS) and all(ok == 1 and not e for ok, e in res.values()), res


def _reescribir_doradas_cortes(raiz, f):
    ruta = raiz / rc.DORADAS_CORTES
    with open(ruta, encoding="utf-8", newline="") as h:
        lector = csv.DictReader(h)
        campos, filas = lector.fieldnames, list(lector)
    f(filas)
    with open(ruta, "w", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, campos)
        w.writeheader()
        w.writerows(filas)


@pytest.mark.parametrize("cambio,texto", [
    ({"corte": "sexo"}, "no está entre los cortes permitidos|categoría"),
    ({"categoria": "Lima"}, "categoría «Lima»"),
    ({"anio": "2023"}, "año 2023"),
    ({"receta_id": "endes_inventada"}, "endes_inventada"),
    ({"nivel": "planeta"}, "nivel «planeta»"),
    ({"id_cifra": "DOR-DCI-2024-PE"}, "cifras_doradas.csv"),
])
def test_validar_detecta_una_dorada_por_corte_mal_puesta(copia, cambio, texto):
    _reescribir_doradas_cortes(copia, lambda filas: filas[0].update(cambio))
    res = rc.validar(Rutas(copia))
    errores = _sin_lineas([e for ok, es in res.values() for e in es])
    assert errores and any(__import__("re").search(texto, e) for e in errores), errores


def test_validar_detecta_una_dorada_repetida(copia):
    _reescribir_doradas_cortes(copia, lambda filas: filas.append({**filas[0], "id_cifra": "DOR-REPETIDA"}))
    errores = _sin_lineas([e for ok, es in rc.validar(Rutas(copia)).values() for e in es])
    assert any("repite" in e for e in errores), errores


# ------------------------------------------------------------------ comparar con estimaciones armadas a mano

def _est(dominio, valor, n, ee=0.01):
    return Estimacion(dominio=dominio, anio=2024, n=n, valor=valor, ee=ee, gl=100, n_efectivo=300.0, deff=1.0, ic_inf=valor - 0.02,
                      ic_sup=valor + 0.02, eventos=int(n * valor))


def _doradas(*filas):
    return [rc.DoradaCorte.model_validate(_fila(**f)) for f in filas]


def test_reproducir_doradas_cortes_pasa_dentro_de_la_tolerancia_y_con_los_casos_exactos():
    r = rc.leer_receta(RAIZ_REAL, "endes_dci_menores_5")
    doradas = _doradas({}, {"id_cifra": "DOR-X-2", "categoria": "Sierra", "valor_publicado": 17.6, "casos_publicados": 6162})
    est = {"region_natural": [("nacional", _est(("PE", "Costa"), 0.0734, 8047)), ("nacional", _est(("PE", "Sierra"), 0.176, 6162))]}
    filas = rc.reproducir_doradas_cortes(r, doradas, est, {"region_natural": {"Costa": "Costa", "Sierra": "Sierra"}})
    assert [f["pasa"] for f in filas] == [True, True]
    assert filas[0]["nuestro"] == 7.3 and filas[0]["dif_pp"] == 0.0 and filas[0]["corte"] == "region_natural" and filas[0]["categoria"] == "Costa"


def test_reproducir_doradas_cortes_falla_por_valor_fuera_de_tolerancia_por_casos_o_sin_dominio():
    r = rc.leer_receta(RAIZ_REAL, "endes_dci_menores_5")
    mapa = {"region_natural": {"Costa": "Costa"}}
    lejos = {"region_natural": [("nacional", _est(("PE", "Costa"), 0.0760, 8047))]}                    # 7,6 frente a 7,3: 0,3 pp
    assert rc.reproducir_doradas_cortes(r, _doradas({}), lejos, mapa)[0]["pasa"] is False
    otros_casos = {"region_natural": [("nacional", _est(("PE", "Costa"), 0.073, 8046))]}
    assert rc.reproducir_doradas_cortes(r, _doradas({}), otros_casos, mapa)[0]["pasa"] is False
    assert rc.reproducir_doradas_cortes(r, _doradas({}), {"region_natural": []}, mapa)[0]["pasa"] is False         # sin el dominio
    en_el_borde = {"region_natural": [("nacional", _est(("PE", "Costa"), 0.074, 8047))]}                     # 7,4: 0,1 pp justos
    assert rc.reproducir_doradas_cortes(r, _doradas({}), en_el_borde, mapa)[0]["pasa"] is True


def test_reproducir_doradas_cortes_traduce_la_categoria_al_valor_del_dominio():
    """El quintil devuelve su código («1») en el dominio, pero la dorada lleva su rótulo."""
    r = rc.leer_receta(RAIZ_REAL, "endes_dci_menores_5")
    d = _doradas({"corte": "quintil_riqueza", "categoria": "los más pobres", "valor_publicado": 22.4, "casos_publicados": 5991})
    est = {"quintil_riqueza": [("nacional", _est(("PE", "1"), 0.224, 5991))]}
    assert rc.reproducir_doradas_cortes(r, d, est, {"quintil_riqueza": {"los más pobres": "1"}})[0]["pasa"] is True
