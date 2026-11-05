"""S1-03 — Planificador de cifras: consulta mínima + territorio resuelto → plan (misma estructura que los q*.yaml).

Las reglas viven en curados/motor/intenciones.yaml (cada fila cita su decisión). Si faltan las dimensiones
reconstruidas, las pruebas FALLAN (agents.md §8)."""
import copy
import re
from pathlib import Path

import pytest
import yaml

from pap.config import Rutas
from pap.motor import planificador as PL
from pap.motor.consulta import cargar
from pap.motor.planificador import anio_anterior, anio_primero, planificar
from pap.motor.respuesta import Motor
from pap.motor.territorio import Resuelto, resolver
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL

ENDES_V, ENDES_A = "endes_anemia_6_35m_oms2024", "endes_anemia_6_35m"
SIEN, COBERTURA = "sien_anemia_tamizados_6_35m", "sien_cobertura_tamizaje_6_35m"
DCI, ENAHO, MAPA, GASTO = "endes_dci_menores_5", "enaho_pobreza_monetaria", "mapa_pobreza_2018", "gasto_ex_pan"
LM = "LIMA_METROPOLITANA"


@pytest.fixture(scope="module")
def raiz():
    r = Rutas(RAIZ_REAL).raiz
    for t in ("dim_ubigeo_historico", "dim_ambito"):
        p = r / "biblioteca" / "dimensiones" / f"{t}.parquet"
        assert p.exists(), f"falta {p}: reconstruir con `pap construir territorio`"
    return r


@pytest.fixture(scope="module")
def ctx(raiz):
    return cargar_contexto(raiz, con_cubo=False)


@pytest.fixture(scope="module")
def motor(ctx):
    return Motor(ctx)


@pytest.fixture(scope="module")
def plan(raiz, ctx, motor):
    def _plan(intencion, tema=None, lugar=None, periodo=None, indicador=None, extremo=None, comparar_con=None,
              parametros=None):
        c = {"intencion": intencion, "pregunta_original": "pregunta de prueba"}
        if tema:
            c["tema"] = tema
        if indicador:
            c["indicador"] = indicador
        if periodo:
            c["periodo"] = periodo
        if extremo:
            c["territorio"] = extremo
        else:
            c["territorio"] = lugar if isinstance(lugar, dict) else {"texto": lugar}
        if comparar_con:
            c["comparar_con"] = comparar_con if isinstance(comparar_con, dict) else {"texto": comparar_con}
        cm = cargar(c, raiz)
        if extremo:
            dentro = extremo.get("dentro_de")
            res = resolver(dentro, ctx) if dentro else None
        else:
            res = resolver(cm["territorio"], ctx)
            if comparar_con:
                res = [res, resolver(cm["comparar_con"], ctx)]
        assert not (isinstance(res, list) and any(not isinstance(r, Resuelto) for r in res))
        return planificar(cm, res, motor, parametros=parametros)
    return _plan


def por_ind(p, ind, rol=None):
    return [c for c in p["cifras"] if c["indicador"] == ind and (rol is None or c["rol"] == rol)]


def uno(p, ind, rol=None, **kw):
    xs = [c for c in por_ind(p, ind, rol) if all(c.get(k) == v for k, v in kw.items())]
    assert len(xs) == 1, (ind, rol, kw, [(c["indicador"], c["nivel"], c["territorio"], c["anio"], c["rol"]) for c in p["cifras"]])
    return xs[0]


# ------------------------------------------------------------------ nivel_actual: anemia (S-01, E-06, T-03)

def test_anemia_distrito_es_sien_principal(plan, motor):
    p = plan("nivel_actual", "anemia", "Ayaviri, Melgar")
    c = uno(p, SIEN, "principal")
    assert (c["nivel"], c["territorio"], c["anio"]) == ("distrito", "210801", motor.anio(SIEN, None))
    assert p["no_se_puede"] is None and p["plantilla"] == "nivel_actual"
    assert p["territorio"] == {"nivel": "distrito", "id": "210801", "nombre_pedido": "Ayaviri"}


def test_s01_sien_distrito_lleva_endes_y_cobertura_de_su_departamento(plan):
    p = plan("nivel_actual", "anemia", "Ayaviri, Melgar")
    e = uno(p, ENDES_V, "contexto")
    k = uno(p, COBERTURA, "contexto")
    assert (e["nivel"], e["territorio"]) == ("departamento", "21") and "comparar_con" not in e
    assert (k["nivel"], k["territorio"]) == ("departamento", "21")
    assert len(p["cifras"]) == 3


def test_s01_en_lima_el_contexto_va_por_ambito_y_no_por_departamento_15(plan):
    p = plan("nivel_actual", "anemia", "San Juan de Lurigancho")
    for ind in (ENDES_V, COBERTURA):
        c = uno(p, ind, "contexto")
        assert (c["nivel"], c["territorio"]) == (LM, LM)
    assert not [c for c in p["cifras"] if c["territorio"] == "15"]


def test_t03_lima_region_y_callao_usan_su_ambito(plan):
    p = plan("nivel_actual", "anemia", {"ubigeo": "150801"})            # Huacho (Lima Región)
    assert uno(p, ENDES_V, "contexto")["territorio"] == "LIMA_REGION"
    p = plan("evolucion", "anemia", {"ambito": "CALLAO"})
    assert {(c["nivel"], c["territorio"]) for c in p["cifras"]} == {("CALLAO", "CALLAO")}


def test_anemia_departamento_es_endes_vigente_sola(plan):
    p = plan("nivel_actual", "anemia", "departamento de Puno")
    assert [(c["indicador"], c["rol"], c["nivel"], c["territorio"]) for c in p["cifras"]] == \
        [(ENDES_V, "principal", "departamento", "21")]
    assert "comparar_con" not in p["cifras"][0]


def test_s01_cobertura_nunca_por_provincia_ni_distrito(plan):
    casos = [("nivel_actual", "Ayaviri, Melgar"), ("evolucion", "Ayaviri, Melgar"), ("efecto", "San Juan de Lurigancho"),
             ("cruce", "provincia de Melgar"), ("nivel_actual", "provincia de Melgar")]
    for intencion, lugar in casos:
        for c in plan(intencion, "anemia" if intencion != "efecto" else "gasto_publico", lugar)["cifras"]:
            assert not (c["indicador"] == COBERTURA and c["nivel"] in ("provincia", "distrito")), (intencion, lugar, c)
    p = plan("nivel_actual", indicador=COBERTURA, lugar="Ayaviri, Melgar")
    c = uno(p, COBERTURA, "principal")
    assert (c["nivel"], c["territorio"], c["nivel_pedido"]) == ("departamento", "21", "distrito")
    assert p["no_se_puede"] == {"motivo": "nivel_no_valido", "nivel_pedido": "distrito", "nivel_planificado": "departamento",
                                "indicador": COBERTURA}


# ------------------------------------------------------------------ evolución: E-06, E-07

def test_e06_evolucion_endes_dos_criterios_en_paralelo(plan, motor):
    p = plan("evolucion", "anemia", "departamento de Huancavelica")
    v = uno(p, ENDES_V, "principal")
    a = uno(p, ENDES_A, "principal")
    primero = uno(p, ENDES_A, "contexto")
    assert (v["anio"], v["comparar_con"]) == (motor.anio(ENDES_V, None), 2024)        # el año anterior disponible
    assert (a["anio"], a["comparar_con"]) == (motor.anio(ENDES_A, None), 2015)        # el primer año de la serie
    assert primero["anio"] == 2015 and "comparar_con" not in primero
    comparada = uno(p, ENDES_V, "contexto")                                          # AD-1 (S1-13): el año con el que se compara
    assert comparada["anio"] == v["comparar_con"] and "comparar_con" not in comparada
    assert len(p["cifras"]) == 4                                                     # sin años intermedios (C-01)
    assert all(c["territorio"] == "09" and c["nivel"] == "departamento" for c in p["cifras"])
    assert not [c for c in p["cifras"] if c["anio"] == 2022]


def test_e06_sin_tendencia_entre_criterios(plan, motor):
    p = plan("evolucion", "anemia", "departamento de Huancavelica")
    for c in p["cifras"]:
        if "comparar_con" in c:
            disp = [int(x) for x in motor.ctx.indicadores[c["indicador"]]["anios_disponibles"]]
            assert c["comparar_con"] in disp, c                 # el año comparado es del mismo indicador
    assert uno(p, ENDES_V, "principal")["comparar_con"] >= 2024     # la forma vigente no se compara con años de la anterior


def test_e06_nivel_actual_y_contexto_solo_forma_vigente(plan):
    for intencion, tema, lugar in (("nivel_actual", "anemia", "departamento de Puno"),
                                   ("nivel_actual", "anemia", "Ayaviri, Melgar"),
                                   ("efecto", "gasto_publico", "San Juan de Lurigancho"),
                                   ("comparacion", "anemia", "departamento de Puno")):
        kw = {"comparar_con": "departamento de Cusco"} if intencion == "comparacion" else {}
        assert not por_ind(plan(intencion, tema, lugar, **kw), ENDES_A), (intencion, lugar)


def test_e07_modo_excluye_solo_ese_punto(motor):
    assert anio_anterior(motor, DCI, 2021) == 2019             # no se compara con 2020 (modo)…
    assert anio_anterior(motor, DCI, 2025) == 2024
    assert anio_primero(motor, DCI, 2025, 2020) == 2021        # …ni arranca la serie en él
    assert anio_primero(motor, DCI, 2025, None) == 2015        # pero sí se compara a través de él


def test_e07_otros_quiebres_cortan_la_serie(motor):
    assert anio_primero(motor, GASTO, 2025, None) == 2023      # C-05: el quiebre de programa de 2025 (L11) enlaza con 2023 y 2024
    assert anio_primero(motor, ENAHO, 2025, None) == 2024


def test_evolucion_generica_primer_y_ultimo_anio(plan, motor):
    p = plan("evolucion", "desnutricion_cronica", "departamento de Puno")
    a = uno(p, DCI, "principal")
    assert (a["comparar_con"], a["anio"]) == (2015, motor.anio(DCI, None))
    assert uno(p, DCI, "contexto")["anio"] == 2015


def test_serie_de_un_solo_anio_no_se_puede(plan):
    p = plan("evolucion", "anemia", "Ayaviri, Melgar")           # el SIEN solo tiene 2025
    assert p["no_se_puede"]["motivo"] == "serie_un_solo_anio" and p["no_se_puede"]["indicador"] == SIEN


# ------------------------------------------------------------------ periodo

def test_periodo_por_defecto_segun_intencion(plan):
    assert plan("evolucion", "anemia", "departamento de Huancavelica")["periodo"] == \
        {"tipo": "serie", "desde": 2015, "hasta": "ultimo"}
    assert plan("nivel_actual", "anemia", "departamento de Puno")["periodo"] == {"tipo": "ultimo"}
    assert plan("evolucion", "anemia", "departamento de Huancavelica",
                periodo={"tipo": "serie", "desde": 2018})["periodo"] == {"tipo": "serie", "desde": 2018, "hasta": "ultimo"}


def test_periodo_anio_explicito_y_anio_sin_datos(plan):
    p = plan("nivel_actual", "desnutricion_cronica", "departamento de Puno", periodo={"tipo": "anio", "anio": 2022})
    assert uno(p, DCI, "principal")["anio"] == 2022 and p["periodo"] == {"tipo": "anio", "anio": 2022}
    assert p["no_se_puede"] is None
    p = plan("nivel_actual", "anemia", "departamento de Puno", periodo={"tipo": "anio", "anio": 2022})
    assert p["no_se_puede"]["motivo"] == "anio_sin_datos" and p["no_se_puede"]["anio_pedido"] == 2022
    assert p["no_se_puede"]["anios_disponibles"] == [2024, 2025]


# ------------------------------------------------------------------ nivel superior (R-REG-02)

def test_nivel_invalido_planifica_el_nivel_superior(plan):
    p = plan("nivel_actual", "desnutricion_cronica", "Ayaviri, Melgar")
    c = uno(p, DCI, "principal")
    assert (c["nivel"], c["territorio"], c["nivel_pedido"]) == ("departamento", "21", "distrito")
    assert p["no_se_puede"] == {"motivo": "nivel_no_valido", "nivel_pedido": "distrito", "nivel_planificado": "departamento",
                                "indicador": DCI}
    assert p["territorio"]["nivel"] == "distrito"                  # el plan conserva lo que se pidió
    p = plan("nivel_actual", "desnutricion_cronica", "San Juan de Lurigancho")
    assert uno(p, DCI, "principal")["territorio"] == LM            # T-03: ámbito, no departamento 15
    p = plan("nivel_actual", indicador=ENDES_V, lugar="provincia de Melgar")
    assert p["no_se_puede"]["nivel_planificado"] == "departamento"


# ------------------------------------------------------------------ gasto, efecto y cruce (G-07, R-03, R-CRUCES-07)

def test_efecto_q3_estructura_y_cifras(plan, motor):
    p = plan("efecto", "gasto_publico", "San Juan de Lurigancho")
    a = motor.anio(GASTO, None)
    got = {(c["indicador"], c["nivel"], c["territorio"], c["rol"], c.get("comparar_con")) for c in p["cifras"]}
    assert got == {(GASTO, "distrito", "150132", "principal", None), (GASTO, LM, LM, "contexto", None),
                   (SIEN, "distrito", "150132", "principal", None), (ENDES_V, LM, LM, "contexto", 2024),
                   (COBERTURA, LM, LM, "contexto", None)}
    assert {c["anio"] for c in p["cifras"]} == {a, 2024}             # X-03 (S3-01): además, el gasto de 2024 (mismo año que la anemia)
    assert p["respuesta_parcial"] is True and p["estructura_efecto"] is True
    assert p["plantilla"] == "cruce_efecto" and p["cruce"] == "CR-01" and p["lado_a_lado"] is True


def test_cruce_es_solo_lado_a_lado(plan):
    pe = plan("efecto", "gasto_publico", "San Juan de Lurigancho")
    pc = plan("cruce", "gasto_publico", "San Juan de Lurigancho")
    assert pc["cifras"] == pe["cifras"]
    assert pc["respuesta_parcial"] is False and pc["estructura_efecto"] is False
    assert pc["lado_a_lado"] is True and pc["cruce"] == "CR-01" and pc["plantilla"] == "cruce_efecto"


def test_efecto_con_tema_anemia_y_por_departamento(plan):
    p = plan("efecto", "anemia", "departamento de Puno")
    assert uno(p, GASTO, "principal")["territorio"] == "21"
    assert uno(p, ENDES_V, "principal")["comparar_con"] == 2024
    assert uno(p, COBERTURA, "contexto")["territorio"] == "21"
    assert not por_ind(p, SIEN) and p["cruce"] == "CR-01"


def test_cruce_fuera_de_la_lista_blanca(plan):
    for tema in ("desnutricion_cronica", "pobreza_monetaria"):
        p = plan("cruce", tema, "departamento de Puno")
        assert p["cruce"] is None and p["lado_a_lado"] is False and p["respuesta_parcial"] is False
        assert p["no_se_puede"]["motivo"] == "cruce_fuera_de_lista_blanca"
        assert not por_ind(p, GASTO)
        assert len(p["cifras"]) == 1


def test_g07_el_tema_de_gasto_sale_de_map_intencion_tema(plan, motor):
    p = plan("nivel_actual", "gasto_publico", "departamento de Puno")
    assert p["tema_gasto"] == "cpt_grupo_expan"
    c = uno(p, GASTO, "principal")
    assert motor.ctx.indicadores[c["indicador"]]["tema_id"] == p["tema_gasto"]
    assert not por_ind(p, "gasto_ex_pan_opcion_c")                  # el desglose no es la cifra principal


def test_x03_cr01_mismo_anio_detras_de_parametro(plan, raiz, motor):
    """X-03 está decidida (S3-01: `cr01_mismo_anio` = true en el YAML); el parámetro sigue siendo editable: en false, el plan de antes."""
    par = copy.deepcopy(PL.cargar_parametros(raiz))
    par["pendientes_dueno"]["cr01_mismo_anio"]["valor"] = False
    hoy = plan("efecto", "gasto_publico", "San Juan de Lurigancho", parametros=par)
    assert not [c for c in hoy["cifras"] if c["indicador"] == GASTO and c["anio"] == 2024]
    par = copy.deepcopy(PL.cargar_parametros(raiz))
    par["pendientes_dueno"]["cr01_mismo_anio"]["valor"] = True
    p = plan("efecto", "gasto_publico", "San Juan de Lurigancho", parametros=par)
    extra = [c for c in p["cifras"] if c["indicador"] == GASTO and c["anio"] == 2024]
    assert [(c["nivel"], c["territorio"], c["rol"]) for c in extra] == [(LM, LM, "contexto")]
    assert len(p["cifras"]) == len(hoy["cifras"]) + 1


# ------------------------------------------------------------------ identificar_extremo (E-08)

def test_extremo_pobreza_por_distrito_usa_grupo_robusto(plan):
    p = plan("identificar_extremo", "pobreza_monetaria", extremo={"nivel": "distrito", "dentro_de": {"nacional": True}})
    assert p["cifras"] == [] and p["plantilla"] == "identificar_extremo"
    assert p["grupos"] == [{"tipo": "mapa_grupo_robusto", "grupo": 1, "rol": "principal"},
                           {"tipo": "ranking_departamental", "indicador": ENAHO, "anio": "ultimo", "prefijo": "enaho",
                            "rol": "contexto"}]
    assert p["territorio"]["nivel"] == "distrito" and p["territorio"]["id"] is None and not p["territorio"]["nombre_pedido"]


def test_extremo_pobreza_por_departamento_usa_grupos_oficiales_inei(plan):
    p = plan("identificar_extremo", "pobreza_monetaria", extremo={"nivel": "departamento"})
    assert [g["tipo"] for g in p["grupos"]] == ["ranking_departamental"]
    assert p["grupos"][0]["indicador"] == ENAHO and p["grupos"][0]["rol"] == "principal"
    assert p["grupos_estadisticos"] == "oficiales_inei" and p["no_se_puede"] is None


def test_extremo_nivel_sin_regla_sube_y_lo_registra(plan):
    p = plan("identificar_extremo", "pobreza_monetaria", extremo={"nivel": "provincia"})
    assert p["grupos"][0]["tipo"] == "ranking_departamental"
    assert p["no_se_puede"] == {"motivo": "nivel_no_valido", "nivel_pedido": "provincia", "nivel_planificado": "departamento"}


def test_extremo_gasto_no_tiene_ranking_y_dentro_de_un_lugar_no_se_puede(plan):
    p = plan("identificar_extremo", "gasto_publico", extremo={"nivel": "departamento"})
    assert p["cifras"] == [] and p["grupos"] == [] and p["no_se_puede"]["motivo"] == "intencion_no_soportada"
    p = plan("identificar_extremo", "pobreza_monetaria", extremo={"nivel": "distrito", "dentro_de": {"texto": "departamento de Puno"}})
    assert p["grupos"] == [] and p["no_se_puede"]["motivo"] == "extremo_dentro_de_no_soportado"


# ------------------------------------------------------------------ comparación, plantillas, ids

def test_comparacion_planifica_cada_territorio(plan):
    p = plan("comparacion", "anemia", "departamento de Puno", comparar_con="departamento de Cusco")
    assert {(c["territorio"], c["rol"]) for c in p["cifras"]} == {("21", "principal"), ("08", "principal")}
    assert p["territorio_comparado"] == {"nivel": "departamento", "id": "08", "nombre_pedido": "Cusco"}
    assert p["plantilla"] == "comparacion"


@pytest.mark.parametrize("intencion,esperada", [("nivel_actual", "nivel_actual"), ("evolucion", "evolucion"),
                                                ("efecto", "cruce_efecto"), ("cruce", "cruce_efecto")])
def test_plantilla_generica_por_intencion(plan, intencion, esperada):
    tema = "gasto_publico" if intencion in ("efecto", "cruce") else "anemia"
    assert plan(intencion, tema, "departamento de Puno")["plantilla"] == esperada


def test_ids_de_cifra_estables_y_con_el_formato_del_yaml(plan, raiz, motor):
    fmt = PL.cargar_parametros(raiz)["planificador"]["formato_id_cifra"]["valor"]
    p1 = plan("efecto", "gasto_publico", "San Juan de Lurigancho")
    p2 = plan("efecto", "gasto_publico", "San Juan de Lurigancho")
    ids = [c["id"] for c in p1["cifras"]]
    assert ids == [c["id"] for c in p2["cifras"]] and len(set(ids)) == len(ids)
    for c in p1["cifras"]:
        assert c["id"] == fmt.format(indicador=c["indicador"], medida=motor.medida(c["indicador"]), nivel=c["nivel"],
                                     territorio=c["territorio"], anio=c["anio"], rol=c["rol"])
    assert PL.formato_id_cifra(indicador="a", medida="m", nivel="n", territorio="t", anio=1, rol="r", raiz=raiz) == "a__m__n__t__1__r"


def test_la_consulta_no_produce_cifras_si_el_territorio_es_una_aclaracion(raiz, ctx, motor):
    cm = cargar({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Lima"}}, raiz)
    a = resolver(cm["territorio"], ctx)
    with pytest.raises(TypeError):
        planificar(cm, a, motor)


# ------------------------------------------------------------------ la tabla declarativa

def test_cada_fila_de_intenciones_cita_su_decision(raiz):
    t = yaml.safe_load((raiz / "curados" / "motor" / "intenciones.yaml").read_text(encoding="utf-8"))
    filas = []

    def recorre(x, ruta=""):
        if isinstance(x, dict):
            if {"indicador", "tipo", "casos", "plantilla", "principal", "valor"} & set(x):
                filas.append((ruta, x))
            for k, v in x.items():
                if k != "cuando":                      # `cuando` son condiciones, no filas
                    recorre(v, f"{ruta}/{k}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                recorre(v, f"{ruta}[{i}]")
    recorre(t)
    assert len(filas) >= 40
    for ruta, f in filas:
        assert re.search(r"[A-Z]+(-[A-Z]+)*-\d+[a-z]?", str(f.get("decision", ""))), f"sin decisión citada: {ruta}"


def test_el_planificador_es_generico_sin_reglas_de_tema_en_python():
    fuente = (Path(PL.__file__)).read_text(encoding="utf-8").lower()
    for palabra in ("anemia", "sien", "endes", "enaho", "gasto_ex_pan", "cobertura", "huancavelica", "cr-01",
                    "lima_metropolitana", "pobreza", "mapa_"):
        assert palabra not in fuente, palabra
