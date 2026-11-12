"""M0-09: las compuertas de proporciones (diseño §15.1 y §15.2), rama por rama, y las 90 filas del cubo 2024 contra el oráculo de M0-00."""
import csv
import json

import pytest

from conftest import RAIZ_REAL
from pap.inferencia import compuertas as cp
from pap.inferencia.estimacion import Estimacion
from pap.motor.validador.nucleo import Cifra

EVIDENCIA = RAIZ_REAL / "backlog" / "slice-m0" / "evidencia"


@pytest.fixture(scope="module")
def ctx():
    return cp.contexto_compuertas()


def est(p=0.3, ee=0.02, n=400, gl=50, n_ef=None, lo=None, hi=None, eventos=None, **kw) -> Estimacion:
    """Estimación en 0–1; el IC por defecto es p ± 2 ee (acotado)."""
    return Estimacion(dominio=("X",), anio=2024, n=n, valor=p, ee=ee, gl=gl, n_efectivo=n if n_ef is None else n_ef,
                      ic_inf=max(0.0, p - 2 * ee) if lo is None else lo, ic_sup=min(1.0, p + 2 * ee) if hi is None else hi,
                      eventos=round(p * n) if eventos is None else eventos, **kw)


def _ev(*a, verificada=True, **kw):
    """`verificada` es obligatorio en `compuertas.evaluar` (H09-2): las pruebas de reglas lo fijan aquí, una sola vez."""
    return cp.evaluar(*a, verificada=verificada, **kw)


def reglas(g: cp.Compuerta) -> list[tuple[str, str]]:
    return [(m.regla, m.accion) for m in g.motivos]


# ---------------------------------------------------------------------------------------------------- parámetros

def test_los_parametros_salen_de_reglas_json(ctx):
    rj = json.loads((RAIZ_REAL / "reglas" / "reglas.json").read_text(encoding="utf-8"))
    por_id = {r["id"]: r["parametros"] for r in rj["reglas"]}
    p = cp.parametros(ctx)
    assert set(p) == {"R-ENC-02", "R-ENC-03", "R-ENC-04", "R-ENC-19"}
    for rid in p:
        assert p[rid] == por_id[rid]
    assert (p["R-ENC-02"]["n_min_suprimir"], p["R-ENC-02"]["n_min_publicar"]) == (25, 50)
    assert (p["R-ENC-03"]["cv_publicar"], p["R-ENC-03"]["cv_suprimir"]) == (0.15, 0.30)
    assert (p["R-ENC-04"]["n_efectivo_suprimir"], p["R-ENC-04"]["gl_min"]) == (30, 8)


def test_cambiar_un_parametro_de_reglas_cambia_la_compuerta(ctx):
    e = est(p=0.3, ee=0.06)                                             # cv_ref = 0,2
    assert _ev(e, ctx).estado == "referencial"
    parametros = {**ctx.regla("R-ENC-03")["parametros"], "cv_publicar": 0.25}
    otro = ctx.con_sobrescrituras({"reglas": {"R-ENC-03": {"parametros": parametros}}})
    assert _ev(e, otro).estado == "publicable"


# ---------------------------------------------------------------------------------------------------- pasos 1 y 2: R-ENC-02

def test_paso1_menos_de_25_casos_suprime_y_corta(ctx):
    g = _ev(est(n=24, ee=0.12, gl=2), ctx)                       # además tendría cv > 30 %, pero el árbol se corta
    assert g.estado == "suprimida" and reglas(g) == [("R-ENC-02", "suprimir")] and g.confianza is None and not g.publicable
    assert g.motivos[0].codigo == "pocos_casos"


def test_paso2_de_25_a_49_casos_es_referencial_y_sigue(ctx):
    for n in (25, 49):
        g = _ev(est(n=n), ctx)
        assert g.estado == "referencial" and reglas(g) == [("R-ENC-02", "publicar_referencial")] and g.confianza == "baja"
    assert _ev(est(n=50), ctx).estado == "publicable"           # 50 ya no es referencial


def test_de_25_a_49_casos_rigen_tambien_r_enc_03_y_r_enc_04(ctx):
    """C-M0-11-2 (dueño, 12/11/2026): los límites de precisión se aplican desde 25 casos. Con 25 a 49 casos R-ENC-02 sigue marcando
    referencial y R-ENC-03/04 se acumulan: pueden dejar la cifra referencial (con su motivo) o suprimirla."""
    for n in (25, 40, 49):
        g = _ev(est(n=n, p=0.3, ee=0.06), ctx)                  # cv_ref = 0,2
        assert g.estado == "referencial" and reglas(g) == [("R-ENC-02", "publicar_referencial"), ("R-ENC-03", "publicar_referencial")]
        g = _ev(est(n=n, p=0.3, ee=0.12), ctx)                  # cv_ref = 0,4: suprime
        assert g.estado == "suprimida" and reglas(g) == [("R-ENC-02", "publicar_referencial"), ("R-ENC-03", "suprimir")]
        assert g.confianza is None and not g.publicable
    for n in (40, 49):
        g = _ev(est(n=n, p=0.05, ee=0.01), ctx)                 # n efectivo = n, entre 30 y 49 → referencial por R-ENC-04
        assert g.estado == "referencial" and reglas(g) == [("R-ENC-02", "publicar_referencial"), ("R-ENC-04", "publicar_referencial")]
    g = _ev(est(n=25, p=0.05, ee=0.01), ctx)                    # n efectivo = 25 < 30 → suprime
    assert g.estado == "suprimida" and reglas(g) == [("R-ENC-02", "publicar_referencial"), ("R-ENC-04", "suprimir")]
    g = _ev(est(n=40, p=0.05, ee=0.04, n_ef=29.7, lo=0.0, hi=0.13), ctx)       # n efectivo < 30: suprime
    assert g.estado == "suprimida" and reglas(g) == [("R-ENC-02", "publicar_referencial"), ("R-ENC-04", "suprimir")]


def test_de_25_a_49_casos_con_p_cero_rotula_y_sigue_referencial(ctx):
    g = _ev(est(n=40, p=0.0, ee=0.0, lo=0.0, hi=0.07, eventos=0), ctx)
    assert g.estado == "referencial" and g.rotulo == "menos de 7,0 %"
    assert reglas(g) == [("R-ENC-02", "publicar_referencial"), ("R-ENC-04", "publicar_referencial"), ("R-ENC-04", "rotular")]


def test_bajo_25_casos_sigue_cortando_en_r_enc_02(ctx):
    g = _ev(est(n=24, p=0.3, ee=0.12), ctx)
    assert reglas(g) == [("R-ENC-02", "suprimir")]


def test_el_rotulo_se_acumula_a_los_motivos_referenciales(ctx):
    g = _ev(est(p=0.0, ee=0.0, n=60, n_ef=45, lo=0.0, hi=0.06, eventos=0), ctx)
    assert g.estado == "referencial" and [m.regla for m in g.motivos] == ["R-ENC-04", "R-ENC-04"] and g.rotulo == "menos de 6,0 %"


# ---------------------------------------------------------------------------------------------------- pasos 3, 4 y 5: R-ENC-04

def test_paso3_n_efectivo_menor_de_30_suprime(ctx):
    g = _ev(est(p=0.05, ee=0.04, n=100, n_ef=29.7, lo=0.0, hi=0.13), ctx)
    assert g.estado == "suprimida" and reglas(g) == [("R-ENC-04", "suprimir")] and "n_efectivo < 30" in g.motivos[0].clausula


def test_paso3_ancho_de_30_pp_o_mas_suprime(ctx):
    g = _ev(est(p=0.08, ee=0.01, n=500, n_ef=100, lo=0.0, hi=0.31), ctx)
    assert g.estado == "suprimida" and g.motivos[0].clausula == "ancho_abs >= 0.30"


def test_paso3_ancho_relativo_mayor_de_130_con_ancho_mayor_de_5_pp_suprime(ctx):
    g = _ev(est(p=0.05, ee=0.01, n=500, n_ef=100, lo=0.0, hi=0.08), ctx)       # ancho 0,08; relativo 1,6
    assert g.estado == "suprimida" and g.motivos[0].clausula == "ancho_rel > 1.30 y ancho_abs > 0.05"


def test_paso3_el_ancho_relativo_alto_con_ancho_de_5_pp_o_menos_no_suprime(ctx):
    g = _ev(est(p=0.02, ee=0.003, n=500, n_ef=100, lo=0.0, hi=0.05), ctx)      # relativo 2,5 pero ancho 0,05 (no > 0,05)
    assert g.estado == "publicable"


def test_paso4_ancho_relativo_mayor_de_59_con_ancho_mayor_de_5_pp_es_referencial(ctx):
    g = _ev(est(p=0.09, ee=0.02, n=500, n_ef=100, lo=0.04, hi=0.12), ctx)      # ancho 0,08; relativo 0,89
    assert g.estado == "referencial" and reglas(g) == [("R-ENC-04", "publicar_referencial")] and g.confianza == "baja"


def test_paso4_n_efectivo_menor_de_50_es_referencial(ctx):
    g = _ev(est(p=0.05, ee=0.01, n=200, n_ef=40, lo=0.04, hi=0.06), ctx)
    assert g.estado == "referencial" and reglas(g) == [("R-ENC-04", "publicar_referencial")]


def test_paso4_menos_de_8_gl_es_referencial(ctx):
    g = _ev(est(p=0.05, ee=0.005, n=200, gl=7, lo=0.04, hi=0.06), ctx)
    assert g.estado == "referencial" and g.motivos[0].regla == "R-ENC-04"
    assert _ev(est(p=0.05, ee=0.005, n=200, gl=8, lo=0.04, hi=0.06), ctx).estado == "publicable"


def test_paso4_cv_de_referencia_mayor_de_15_por_ciento_es_referencial_l9(ctx):
    g = _ev(est(p=0.05, ee=0.01, n=200, lo=0.04, hi=0.06), ctx)               # cv_ref = ee / mín(p, 1−p) = 0,2
    assert g.estado == "referencial" and g.motivos[0].clausula.startswith("L9")


def test_paso4_p_entre_10_y_90_no_pasa_por_r_enc_04(ctx):
    g = _ev(est(p=0.5, ee=0.02, n=100, n_ef=10, lo=0.46, hi=0.54), ctx)       # n efectivo 10 solo importa en los bordes
    assert g.estado == "publicable"


def test_paso5_p_igual_a_cero_rotula_menos_de_el_limite_superior(ctx):
    g = _ev(est(p=0.0, ee=0.0, n=100, n_ef=100, lo=0.0, hi=0.036, eventos=0), ctx)
    assert g.estado == "publicable" and g.rotulo == "menos de 3,6 %"
    assert reglas(g) == [("R-ENC-04", "rotular")] and g.motivos[0].rotulo == g.rotulo


def test_paso5_p_igual_a_uno_rotula_mas_de_el_limite_inferior(ctx):
    g = _ev(est(p=1.0, ee=0.0, n=100, n_ef=100, lo=0.964, hi=1.0, eventos=100), ctx)
    assert g.estado == "publicable" and g.rotulo == "más de 96,4 %" and reglas(g) == [("R-ENC-04", "rotular")]


def test_paso5_el_rotulo_no_cambia_el_estado_de_una_cifra_referencial(ctx):
    g = _ev(est(p=0.0, ee=0.0, n=100, n_ef=45, lo=0.0, hi=0.036, eventos=0), ctx)    # n efectivo 45 < 50 → referencial, y rotula
    assert g.estado == "referencial" and g.rotulo == "menos de 3,6 %" and [m.accion for m in g.motivos] == ["publicar_referencial", "rotular"]


# ---------------------------------------------------------------------------------------------------- pasos 6 y 7: R-ENC-03

def test_paso6_cv_mayor_de_30_por_ciento_suprime(ctx):
    g = _ev(est(p=0.3, ee=0.12), ctx)
    assert g.estado == "suprimida" and reglas(g) == [("R-ENC-03", "suprimir")] and g.motivos[0].codigo == "precision"
    assert _ev(est(p=0.3, ee=0.09), ctx).estado == "referencial"              # cv_ref = 0,30 exacto no suprime


def test_paso7_cv_entre_15_y_30_por_ciento_es_referencial(ctx):
    g = _ev(est(p=0.3, ee=0.06), ctx)
    assert g.estado == "referencial" and reglas(g) == [("R-ENC-03", "publicar_referencial")]
    assert _ev(est(p=0.3, ee=0.045), ctx).estado == "publicable"              # cv_ref = 0,15 exacto se publica


def test_paso7_menos_de_8_gl_con_cv_bajo_es_referencial(ctx):
    g = _ev(est(p=0.3, ee=0.02, gl=7), ctx)
    assert g.estado == "referencial" and g.motivos[0].clausula == "Modificador: publicar con gl < 8"


def test_el_cv_de_referencia_usa_el_menor_entre_p_y_1_menos_p(ctx):
    assert _ev(est(p=0.7, ee=0.06), ctx).estado == "referencial"              # 0,06 / 0,3 = 0,2, no 0,06 / 0,7


# ---------------------------------------------------------------------------------------------------- paso 8 y bordes del árbol

def test_paso8_sin_tasa_o_hasta_5_por_ciento_no_dispara(ctx):
    for t in (None, 0.0, 0.05):                                                  # 5 % exacto no avisa
        g = _ev(est(tasa_no_respuesta=t, tasa_no_respuesta_ponderada=t), ctx)
        assert g.estado == "publicable" and g.motivos == () and g.tasa_no_respuesta == t


def test_paso8_de_5_a_20_por_ciento_avisa_sin_cambiar_el_estado(ctx):
    for t in (0.0501, 0.12, 0.20):                                               # 20 % exacto sigue siendo aviso
        g = _ev(est(tasa_no_respuesta=t), ctx)
        assert g.estado == "publicable" and reglas(g) == [("R-ENC-19", "advertir")] and g.confianza == "media"
        assert g.motivos[0].codigo == "no_respuesta" and g.tasa_no_respuesta == t


def test_paso8_mas_de_20_por_ciento_es_referencial_y_de_confianza_baja(ctx):
    g = _ev(est(tasa_no_respuesta=0.2001), ctx)
    assert g.estado == "referencial" and reglas(g) == [("R-ENC-19", "publicar_referencial")] and g.confianza == "baja" and g.publicable
    g = _ev(est(tasa_no_respuesta=0.6, tasa_no_respuesta_ponderada=0.6), ctx)
    assert g.estado == "referencial" and g.tasa_no_respuesta == 0.6


def test_paso8_se_acumula_a_los_pasos_anteriores_y_no_corre_si_el_arbol_se_corto(ctx):
    g = _ev(est(p=0.3, ee=0.06, tasa_no_respuesta=0.1), ctx)                    # cv_ref 0,2 → referencial, y además el aviso
    assert g.estado == "referencial" and reglas(g) == [("R-ENC-03", "publicar_referencial"), ("R-ENC-19", "advertir")]
    g = _ev(est(n=24, tasa_no_respuesta=0.5), ctx)                              # suprimida en el paso 1: el árbol se corta
    assert g.estado == "suprimida" and reglas(g) == [("R-ENC-02", "suprimir")]
    g = _ev(est(p=0.3, ee=0.12, tasa_no_respuesta=0.5), ctx)                    # suprimida por CV: tampoco corre
    assert reglas(g) == [("R-ENC-03", "suprimir")]


def test_paso8_lee_compuertas_paso_no_respuesta_activo_de_parametros_yaml(ctx, monkeypatch):
    """H09-3: el interruptor del YAML se lee (antes nadie lo leía). Apagado, la tasa solo se informa."""
    assert cp.paso_no_respuesta_activo() is True                                 # K-07 aprobada el 12/11/2026
    monkeypatch.setattr(cp, "paso_no_respuesta_activo", lambda: False)
    g = _ev(est(tasa_no_respuesta=0.6), ctx)
    assert g.estado == "publicable" and g.motivos == () and g.tasa_no_respuesta == 0.6


def test_r_enc_19_sale_de_reglas_json(ctx):
    r = ctx.regla("R-ENC-19")
    assert (r["parametros"]["tasa_aviso"], r["parametros"]["tasa_referencial"]) == (0.05, 0.20) and r["etapa"] == "4_precision"
    otro = ctx.con_sobrescrituras({"reglas": {"R-ENC-19": {"parametros": {**r["parametros"], "tasa_aviso": 0.15}}}})
    assert _ev(est(tasa_no_respuesta=0.10), otro).motivos == ()                  # el umbral viene de la regla, no del código


def test_dominio_vacio_es_sin_datos(ctx):
    g = _ev(Estimacion(dominio=("T3",), anio=2024, n=0), ctx)
    assert g.estado == "sin_datos" and g.confianza is None and g.motivos[0].codigo == "sin_datos" and not g.publicable


def test_un_dato_que_falta_suprime_por_metadato_faltante(ctx):
    g = _ev(est(lo=0.26, hi=0.34, ee=None) if False else Estimacion(dominio=("X",), anio=2024, n=400, valor=0.3, ee=None, gl=50, n_efectivo=400,
                                                                     ic_inf=0.26, ic_sup=0.34, eventos=120), ctx)
    assert g.estado == "suprimida" and g.motivos[0].codigo == "metadato_faltante"


# ---------------------------------------------------------------------------------------------------- §15.2: confianza

def test_confianza_alta_media_y_baja(ctx):
    e = est()
    assert cp.evaluar(e, ctx, verificada=True, coincide_oficial=True).confianza == "alta"
    assert cp.evaluar(e, ctx, verificada=True, coincide_oficial=False).confianza == "media"
    assert cp.evaluar(e, ctx, verificada=True, coincide_oficial=True, compuesto=True).confianza == "media"
    for kw in ({"coincide_oficial": True}, {"compuesto": True}, {}):
        g = _ev(est(n=40), ctx, **kw)                                         # referencial: siempre baja
        assert g.confianza == "baja" and g.motivo_confianza
    assert cp.evaluar(e, ctx, verificada=False).confianza == "baja"                  # supuesto M0-09
    assert all(_ev(e, ctx, coincide_oficial=True).motivo_confianza for _ in "x")


# ---------------------------------------------------------------------------------------------------- 90 filas del cubo

def _fila(r: dict) -> dict:
    f = {k: (None if v == "" else v) for k, v in r.items()}
    for k in ("valor", "ee", "cv", "ic_inf", "ic_sup", "gl", "n_muestra", "n_efectivo", "deff", "numerador"):
        if f.get(k) is not None:
            f[k] = float(f[k])
    return f


def test_las_90_filas_del_cubo_dan_el_mismo_estado_que_el_oraculo_de_m0_00(ctx):
    """Las compuertas (con las funciones de `reglas_etapa4.py`) frente a `m0-00_estados_cubo.csv`: mismo estado, misma acción final
    y las mismas reglas disparadas, fila por fila. Los metadatos del indicador salen de `dim_indicador.yaml`."""
    import yaml
    from pap.motor.validador.nucleo import accion_final

    inds = {i["id"]: i for i in yaml.safe_load((RAIZ_REAL / "curados" / "capa0" / "dim_indicador.yaml").read_text(encoding="utf-8"))["indicadores"]}
    filas = list(csv.DictReader(open(EVIDENCIA / "m0-00_filas_cubo_2024.csv", encoding="utf-8")))
    esperado = {(r["indicador_id"], r["nivel"], r["territorio_id"]): r
                for r in csv.DictReader(open(EVIDENCIA / "m0-00_estados_cubo.csv", encoding="utf-8"))}
    assert len(filas) == len(esperado) == 90
    estados: dict[str, int] = {}
    for r in filas:
        e = esperado[(r["indicador_id"], r["nivel"], r["territorio_id"])]
        g = cp.evaluar_cifra(Cifra.desde(_fila(r), inds[r["indicador_id"]]), ctx, verificada=True)
        assert g.estado == e["estado"], (r["indicador_id"], r["territorio_id"])
        assert accion_final(list(g.resultados), ctx) == e["accion_final"]
        assert ";".join(f"{x.regla}:{x.accion}:{x.motivo}" for x in g.resultados) == e["reglas"]
        estados[g.estado] = estados.get(g.estado, 0) + 1
    assert estados == {"publicable": 85, "referencial": 5}


# ---------------------------------------------------------------------------------------------------- sobre el sintético (adaptador + compuertas)

def test_las_compuertas_sobre_el_sintetico_dan_el_estado_que_describe_cada_dominio(ctx):
    from pap.inferencia.svy_adaptador import estimar_proporciones

    from .sintetico_r import TERRITORIOS, marco

    por_dominio = {e.dominio[0]: _ev(e, ctx) for e in estimar_proporciones(marco(2024), ["terr"], [(t,) for t in TERRITORIOS], anio=2024)}
    assert por_dominio["T1"].estado == "publicable"                                  # grande, p ≈ 0,29
    assert por_dominio["T3"].estado == "sin_datos"                                   # ninguna fila entra a u
    assert por_dominio["T5"].estado == "suprimida" and por_dominio["T5"].motivos[0].regla == "R-ENC-02"      # n < 25
    assert por_dominio["T6"].estado == "suprimida" and por_dominio["T6"].motivos[0].regla == "R-ENC-03"      # CV > 30 %
    assert por_dominio["T4"].estado == "suprimida" and por_dominio["T4"].motivos[0].regla == "R-ENC-03"      # una UPM por estrato: gl = 0 y CV > 30 %
    for t, clausula in (("T2", "Además: numerador == 0"), ("T7", "Además: numerador == n")):                 # p = 0 y p = 1 con solo 1 gl: IC ancho
        g = por_dominio[t]
        assert g.estado == "suprimida" and g.motivos[0].clausula == "ancho_abs >= 0.30" and g.motivos[1].clausula == clausula and g.rotulo is None


def test_verificada_es_obligatoria_y_solo_por_nombre(ctx):
    """H09-2: sin `verificada` no hay confianza que valga; por posición tampoco."""
    e = est()
    with pytest.raises(TypeError):
        cp.evaluar(e, ctx)
    with pytest.raises(TypeError):
        cp.evaluar(e, ctx, meta=None, coincide_oficial=True)
    with pytest.raises(TypeError):
        cp.evaluar_cifra(cp.cifra_desde_estimacion(e, None), ctx)
    with pytest.raises(TypeError):
        cp.evaluar(e, ctx, None, True)


def test_suprimida_no_deja_ningun_rotulo_en_los_motivos(ctx):
    """H09-4: p = 0 sin eventos rotula (R-ENC-18), pero si el estado final es suprimida no sale ningún rótulo."""
    g = _ev(est(p=0.0, ee=0.0, n=400, gl=1, lo=0.0, hi=0.5, eventos=0), ctx)
    assert g.estado == "suprimida"
    assert g.rotulo is None and all(m.rotulo is None for m in g.motivos)


def test_n_40_con_cv_alto_se_suprime_desde_c_m0_11_2(ctx):
    """C-M0-11-2 (dueño, 12/11/2026): antes R-ENC-03/04 exigían n ≥ 50 y una cifra de 40 casos con CV alto quedaba referencial;
    ahora el CV > 30 % la suprime también con 25 a 49 casos."""
    g = _ev(est(p=0.3, ee=0.2, n=40, lo=0.0, hi=0.7), ctx)
    assert g.estado == "suprimida" and g.confianza is None
    assert reglas(g) == [("R-ENC-02", "publicar_referencial"), ("R-ENC-03", "suprimir")]
