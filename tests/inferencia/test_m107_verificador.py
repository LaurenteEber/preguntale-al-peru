"""M1-07, con datos sintéticos (sin microdatos reales): el verificador elige el universo, la tabla base y el diseño por la **tabla que
interviene** (no por el primer archivo de la unidad), y el peso al unir tablas sigue la submuestra más restrictiva
(niño × madre × hogar). Las tablas curadas, las relaciones y las unidades son las reales; los Parquet son los de `sintetico_m107`."""
import json
from dataclasses import replace

import pytest

from pap.inferencia import tablas_curadas as tc
from pap.inferencia.duckdb_seguro import conexion_segura
from pap.inferencia.plan import Plan
from pap.inferencia.verificador import Falla, verificar

from conftest import RAIZ_REAL

from .sintetico_m107 import contexto


def v(archivo: str, variable: str) -> str:
    return f"ENDES·2024·{archivo}·{variable}"


def cond(archivo: str, variable: str, op: str = "en", valores: tuple = ()) -> dict:
    return {"var": v(archivo, variable), "op": op, "valores": list(valores)}


def plan(unidad: str, indicador: dict, restricciones=(), cortes=(), nivel="nacional", universo_analitico=None) -> Plan:
    receta = universo_analitico is not None
    return Plan.model_validate({
        "origen": "receta" if receta else "compuesto", "receta_id": "prueba_m107" if receta else None, "encuesta": "ENDES", "anios": [2024],
        "unidad": unidad, "medida": "proporcion", "universo_analitico": universo_analitico,
        "indicador": {"combinar": "una", "condiciones": [indicador]}, "universo": {"restricciones": list(restricciones)},
        "cortes": list(cortes), "territorio": {"nivel": nivel, "id": None}})


@pytest.fixture(scope="module")
def mundo(tmp_path_factory):
    ctx, micro = contexto(tmp_path_factory.mktemp("m107"))
    return ctx, conexion_segura(carpetas=[micro])


def ok(pc):
    assert not isinstance(pc, Falla), pc
    return pc


# ------------------------------------------------------------------ universo y tabla base por la tabla que interviene

def test_un_plan_de_nino_sobre_rec41_usa_el_universo_del_hijo_de_la_entrevistada_y_parte_de_rec41(mundo):
    ctx, con = mundo
    pc = ok(verificar(plan("nino", cond("REC41", "M17", "en", (1,))), ctx, con))
    assert pc.universo_analitico.id == "nino_hijo_de_entrevistada" and pc.archivo_unidad == "REC41"
    assert (pc.diseno.nivel_submuestra, pc.diseno.peso_expr, pc.diseno.psu_expr) == ("individual", "V005/1e6", "V021")
    assert [(u.hijo, u.padre) for u in pc.uniones][:2] == [("REC41", "REC0111"), ("REC0111", "RECH0")]
    c = pc.controles                                                      # C-M1-07-3 (b): por defecto, madres de 15 a 49 (la de 14 años, afuera)
    assert c["filas_unidad"] == c["filas_tras_uniones"] == 5 and c["u_antes"] == c["u_despues"] == 4 and c["perdida_u"] == 0


def test_un_plan_de_nino_sobre_rech6_sigue_usando_el_universo_del_nino_medido(mundo):
    ctx, con = mundo
    pc = ok(verificar(plan("nino", cond("RECH6", "HC57", "en", (1, 2, 3)), [cond("RECH6", "HC57", "en", (1, 2, 3, 4))]), ctx, con))
    assert pc.universo_analitico.id == "nino_hecho_hb_medida" and pc.archivo_unidad == "RECH6"
    assert (pc.diseno.archivo, pc.diseno.nivel_submuestra, pc.diseno.peso_expr) == ("RECH6", "medicion", "HV005/1e6")


def test_el_universo_nombrado_por_una_receta_debe_cubrir_la_tabla_del_plan(mundo):
    ctx, _ = mundo
    f = verificar(plan("nino", cond("REC41", "M17", "en", (1,)), universo_analitico="nino_hecho"), ctx)
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "universo") and "REC41" in f.motivo
    pc = ok(verificar(plan("nino", cond("REC41", "M17", "en", (1,)), universo_analitico="nino_hijo_de_entrevistada_12_49"), ctx))
    assert pc.universo_analitico.id == "nino_hijo_de_entrevistada_12_49"


def test_la_madre_de_14_anos_entra_solo_al_universo_12_49_que_hay_que_nombrar(mundo):
    """C-M1-07-3 (b): el universo por defecto es el de 15 a 49; el de 12 a 49 solo cuando se nombra (nunca lo elige el verificador)."""
    ctx, con = mundo
    base = ok(verificar(plan("nino", cond("REC41", "M17", "en", (1,))), ctx, con))
    doce = ok(verificar(plan("nino", cond("REC41", "M17", "en", (1,)), universo_analitico="nino_hijo_de_entrevistada_12_49"), ctx, con))
    assert (base.universo_analitico.id, base.controles["u_despues"]) == ("nino_hijo_de_entrevistada", 4)
    assert (doce.universo_analitico.id, doce.controles["u_despues"]) == ("nino_hijo_de_entrevistada_12_49", 5)
    for u in ctx.universos:                                               # ningún plan sin receta cae en un universo «solo por nombre»
        if u.solo_por_nombre:
            assert "_12_49" in u.id
    m = ok(verificar(plan("mujer", cond("RE223132", "V313", "en", (1, 2, 3))), ctx, con))
    assert m.universo_analitico.id == "mujer_15_49_entrevistada"
    m12 = ok(verificar(plan("mujer", cond("RE223132", "V313", "en", (1, 2, 3)), universo_analitico="mujer_12_49_entrevistada"), ctx, con))
    assert m12.universo_analitico.id == "mujer_12_49_entrevistada"


def test_la_medicion_de_rec44_elige_su_universo_y_su_peso_de_medicion(mundo):
    ctx, con = mundo
    mas = [cond("REC0111", "V012", "entre", (15, 49))]                     # con una variable de la madre REC44 sí vale (C-M1-07-3)
    pc = ok(verificar(plan("nino", cond("REC44", "HW57", "en", (1, 2, 3)), mas), ctx, con))
    assert pc.universo_analitico.id == "nino_hijo_de_entrevistada_hb_medida" and pc.archivo_unidad == "REC44"
    assert (pc.diseno.archivo, pc.diseno.nivel_submuestra, pc.diseno.peso_expr, pc.diseno.psu_expr) == ("REC44", "medicion", "HV005/1e6", "HV021")
    assert any(u.padre == "RECH0" for u in pc.uniones)                    # el peso del hogar viene por la madre: REC44 → REC0111 → RECH0
    pc = ok(verificar(plan("nino", cond("REC44", "HW70", "<", (-200,)), mas), ctx, con))
    assert pc.universo_analitico.id == "nino_hijo_de_entrevistada_talla"


def test_la_medicion_de_rec44_se_conserva_al_juntar_otra_tabla_del_hijo(mundo):
    """Hallazgo 5 del auditor: con una restricción de REC41 el plan de anemia de REC44 no pierde HW55 = 0."""
    ctx, con = mundo
    p = plan("nino", cond("REC44", "HW57", "en", (1, 2, 3)), [cond("REC41", "M17", "en", (0, 1))])
    pc = ok(verificar(p, ctx, con))
    assert pc.universo_analitico.id == "nino_hijo_de_entrevistada_hb_medida"
    assert pc.diseno.nivel_submuestra == "medicion" and pc.controles["y_nulos_en_u"] == 0


def test_los_caminos_cortos_no_dependen_del_orden_de_las_relaciones(mundo):
    """Hallazgo 9: REC41 llega a la mujer y al hogar por REC0111, aunque las relaciones vengan en el orden inverso."""
    from pap.inferencia.verificador import ruta_de_uniones
    ctx, _ = mundo
    rels = ctx.relaciones[("ENDES", 2024)]
    for r in (rels, list(reversed(rels))):
        for hijo in ("REC41", "REC43", "REC44", "REC94", "REC95", "DIT"):
            ruta = ruta_de_uniones(r, hijo, {"RECH0", "REC0111"})
            assert [(u.hijo, u.padre) for u in ruta] == [(hijo, "REC0111"), ("REC0111", "RECH0")], hijo


def test_un_plan_de_mujer_parte_de_la_tabla_que_interviene_y_baja_a_su_hermana_por_rec0111(mundo):
    ctx, con = mundo
    pc = ok(verificar(plan("mujer", cond("RE223132", "V313", "en", (1, 2, 3)), [cond("RE516171", "V502", "en", (1,))]), ctx, con))
    assert pc.universo_analitico.id == "mujer_15_49_entrevistada" and pc.archivo_unidad == "RE223132"
    assert (pc.diseno.nivel_submuestra, pc.diseno.peso_expr) == ("individual", "V005/1e6")
    assert pc.controles["filas_unidad"] == pc.controles["filas_tras_uniones"] == 4 and pc.controles["u_despues"] == 2
    pc = ok(verificar(plan("mujer", cond("REC0111", "V012", "entre", (15, 49))), ctx, con))
    assert pc.archivo_unidad == "REC0111" and pc.controles["filas_unidad"] == 5


def test_el_hogar_y_la_persona_tambien_se_eligen_por_la_tabla(mundo):
    ctx, con = mundo
    pc = ok(verificar(plan("persona", cond("RECH4", "SH11Z", "en", (1,))), ctx, con))
    assert pc.universo_analitico.id == "persona_de_hecho" and pc.archivo_unidad == "RECH4"
    assert (pc.diseno.nivel_submuestra, pc.diseno.peso_expr) == ("hogar", "HV005/1e6") and pc.uniones[0].texto == "RECH4→RECH0"
    pc = ok(verificar(plan("hogar", cond("RECH23", "HV270", "en", (4, 5))), ctx, con))
    assert pc.universo_analitico.id == "hogar" and pc.archivo_unidad == "RECH23"


def test_la_tabla_base_viene_de_unidades_yaml_y_no_del_primer_archivo(mundo):
    ctx, con = mundo
    unidades = [u.model_copy(update={"tabla_base": "RECH0"}) if u.archivo == "RECH23" else u for u in ctx.unidades]
    pc = ok(verificar(plan("hogar", cond("RECH23", "HV270", "en", (4, 5))), replace(ctx, unidades=unidades), con))
    assert pc.archivo_unidad == "RECH0" and [(u.unido, u.hacia) for u in pc.uniones][-1] == ("RECH23", "hijo")
    assert ok(verificar(plan("hogar", cond("RECH23", "HV270", "en", (4, 5))), ctx, con)).archivo_unidad == "RECH23"


def test_dos_tablas_de_la_unidad_con_bases_que_no_se_unen_son_falla_del_plan(mundo):
    ctx, _ = mundo
    # RECH6 (niño medido) y REC41 (hijo de la entrevistada) son de la misma unidad pero no se unen: ninguna cuelga de la otra
    p = plan("nino", cond("REC41", "M17", "en", (1,)), [cond("RECH6", "HC1", "entre", (0, 59))])
    f = verificar(p, ctx)
    assert isinstance(f, Falla) and f.tipo == "plan" and f.dimension in ("uniones", "universo")


def test_una_unidad_que_no_es_la_de_las_variables_es_falla_del_plan(mundo):
    ctx, _ = mundo
    f = verificar(plan("mujer", cond("RECH6", "HC57", "en", (1,))), ctx)
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "universo") and "mujer" in f.motivo


# ------------------------------------------------------------------ peso: la submuestra más restrictiva (niño × madre × hogar)

def test_nino_madre_hogar_gana_la_medicion_sobre_la_entrevista_individual_y_el_hogar(mundo):
    ctx, con = mundo
    p = plan("nino", cond("REC44", "HW57", "en", (1, 2, 3)), [cond("REC0111", "V012", "entre", (15, 49))], cortes=["area"])
    pc = ok(verificar(p, ctx, con))
    assert pc.cortes[0].archivo == "RECH0"                                   # el hogar
    assert {"REC0111", "RECH0", "REC44"} <= {u.ancla for u in pc.uniones} | {u.unido for u in pc.uniones}
    assert (pc.diseno.archivo, pc.diseno.nivel_submuestra, pc.diseno.peso_expr) == ("REC44", "medicion", "HV005/1e6")


def test_nino_madre_hogar_sin_medicion_gana_la_entrevista_individual(mundo):
    ctx, con = mundo
    p = plan("nino", cond("REC41", "M17", "en", (1,)), [cond("REC0111", "V012", "entre", (15, 49))], cortes=["area"])
    pc = ok(verificar(p, ctx, con))
    assert pc.diseno.nivel_submuestra == "individual" and pc.diseno.peso_expr == "V005/1e6"
    assert pc.cortes[0].archivo == "RECH0"
    # solo el hogar interviene (sin madre): el peso es el del niño, individual
    assert ok(verificar(plan("nino", cond("REC41", "M17", "en", (1,))), ctx, con)).diseno.nivel_submuestra == "individual"


def test_dos_submuestras_individuales_con_pesos_distintos_son_falla_del_plan(mundo):
    ctx, _ = mundo
    diseno = [d.model_copy(update={"peso_expr": "V005/2e6"}) if d.archivo == "REC0111" else d for d in ctx.diseno]
    p = plan("nino", cond("REC41", "M17", "en", (1,)), [cond("REC0111", "V012", "entre", (15, 49))])
    f = verificar(p, replace(ctx, diseno=diseno))
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "peso")
    # con la medición de por medio, gana la medición y no hay conflicto
    p = plan("nino", cond("REC44", "HW57", "en", (1, 2, 3)), [cond("REC0111", "V012", "entre", (15, 49))])
    assert ok(verificar(p, replace(ctx, diseno=diseno))).diseno.nivel_submuestra == "medicion"


def test_una_tabla_sin_fila_de_diseno_es_falla_del_plan(mundo):
    ctx, _ = mundo
    diseno = [d for d in ctx.diseno if d.archivo not in ("REC41", "REC0111")]
    f = verificar(plan("nino", cond("REC41", "M17", "en", (1,))), replace(ctx, diseno=diseno))
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "diseno")


# ------------------------------------------------------------------ cortes: hogar, madre y la unidad del corte

def test_los_cortes_del_hogar_y_el_sexo_llegan_a_la_tabla_del_hijo_por_rec0111_y_rec21(mundo):
    ctx, con = mundo
    pc = ok(verificar(plan("nino", cond("REC41", "M17", "en", (1,)), cortes=["area", "sexo", "quintil_riqueza"]), ctx, con))
    assert {c.id: (c.archivo, c.variable) for c in pc.cortes} == {
        "area": ("RECH0", "HV025"), "sexo": ("REC21", "B4"), "quintil_riqueza": ("RECH23", "HV270")}
    assert pc.controles["filas_unidad"] == pc.controles["filas_tras_uniones"] == 5 and pc.controles["perdida_u"] == 0


def test_el_grupo_de_edad_de_la_madre_no_se_ofrece_como_el_del_nino(mundo):
    ctx, _ = mundo
    f = verificar(plan("nino", cond("REC41", "M17", "en", (1,)), cortes=["grupo_edad"]), ctx)
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "cortes")
    # para la mujer sí: V013 es su grupo de edad (no está en el índice sintético, así que la falla es esa y no la unidad)
    f = verificar(plan("mujer", cond("REC0111", "V012", "entre", (15, 49)), cortes=["grupo_edad"]), ctx)
    assert isinstance(f, Falla) and "V013" in f.motivo


def test_el_corte_de_unidad_nino_de_rech6_sigue_valiendo_para_el_plan_nino(mundo):
    ctx, _ = mundo
    # RECH6 declara `persona_del_hogar` en archivos_endes_2024.yaml y los cortes del niño llevan `unidad: nino` (nota de C-M1-06-1)
    filas = {u.archivo: u for u in ctx.unidades}
    assert (filas["RECH6"].unidad_archivo, filas["RECH6"].unidad_plan) == ("persona_del_hogar", "nino")
    sexo = {(x.archivo, x.variable): x for c in ctx.cortes if c.id == "sexo" for x in c.por_encuesta["ENDES"]}
    assert sexo[("RECH6", "HC27")].unidad == "nino"
    assert tc.corte_aplica(ctx.unidades, "ENDES", 2024, "nino", sexo[("RECH6", "HC27")])
    assert not tc.corte_aplica(ctx.unidades, "ENDES", 2024, "mujer", sexo[("RECH6", "HC27")])


def test_los_datos_reales_de_las_tablas_curadas_cargan():
    assert {u.archivo for u in tc.leer_unidades(RAIZ_REAL)} >= {"RECH6", "REC41", "REC0111"}


# ------------------------------------------------------------------ C-M1-07-1: RECH5 (mujeres medidas) con el factor hogar

def test_rech5_pasa_el_verificador_con_el_peso_de_la_medicion_y_el_universo_de_hecho_de_15_a_49(mundo):
    ctx, con = mundo
    p = plan("mujer", cond("RECH5", "HA57A", "en", (1, 2, 3)), [cond("RECH5", "HA57A", "en", (1, 2, 3, 4))], cortes=["area"])
    pc = ok(verificar(p, ctx, con))
    assert pc.universo_analitico.id == "mujer_15_49_de_hecho_hb_medida" and pc.archivo_unidad == "RECH5"
    assert (pc.diseno.archivo, pc.diseno.nivel_submuestra, pc.diseno.peso_expr, pc.diseno.psu_expr) == ("RECH5", "medicion", "HV005/1e6", "HV021")
    textos = {u.texto for u in pc.uniones}
    assert "RECH5→RECH1" in textos and "RECH5→RECH0" in textos                    # el pernocte viene de la línea de la mujer (HA0 = HVIDX)
    assert next(u for u in pc.uniones if u.texto == "RECH5→RECH1").pares == (("HHID", "HHID"), ("HA0", "HVIDX"))
    c = pc.controles
    assert c["filas_unidad"] == c["filas_tras_uniones"] == 4 and c["u_antes"] == c["u_despues"] == 1 and c["perdida_u"] == 0
    # sin una variable de la medición, el universo es el de hecho de 15 a 49 (la de 14 años y la que no durmió en el hogar, afuera)
    pc = ok(verificar(plan("mujer", cond("RECH5", "HA1", "entre", (15, 49))), ctx, con))
    assert pc.universo_analitico.id == "mujer_15_49_de_hecho" and pc.controles["u_despues"] == 2


def test_la_unidad_de_rech5_es_la_mujer_y_no_se_mezcla_con_las_tablas_del_cuestionario_individual(mundo):
    ctx, _ = mundo
    fila = next(u for u in ctx.unidades if u.archivo == "RECH5")
    assert (fila.unidad_plan, fila.unidad_archivo, fila.tabla_base, fila.peso.variable, fila.peso.en) == ("mujer", "persona_del_hogar", "RECH5", "HV005", "RECH0")
    f = verificar(plan("mujer", cond("RECH5", "HA57A", "en", (1, 2, 3)), [cond("REC0111", "V012", "entre", (15, 49))]), ctx)
    assert isinstance(f, Falla) and f.tipo == "plan"                             # dos pesos: no hay unión declarada entre las dos tablas


# ------------------------------------------------------------------ C-M1-07-2: el niño vivo y REC21 solo de puente

def test_el_universo_del_nino_vivo_es_el_de_vacunas_diarrea_lactancia_y_el_de_la_cesarea_cuenta_todos_los_nacimientos(mundo):
    ctx, con = mundo
    diarrea = ok(verificar(plan("nino", cond("REC43", "H11", "en", (1,))), ctx, con))
    assert diarrea.universo_analitico.id == "nino_vivo_hijo_de_entrevistada" and diarrea.controles["u_despues"] == 4
    lactancia = ok(verificar(plan("nino", cond("REC41", "M4", "en", (95,))), ctx, con))
    assert lactancia.universo_analitico.id == "nino_vivo_hijo_de_entrevistada" and lactancia.archivo_unidad == "REC41"
    cesarea = ok(verificar(plan("nino", cond("REC41", "M17", "en", (1,))), ctx, con))
    assert cesarea.universo_analitico.id == "nino_hijo_de_entrevistada" and cesarea.controles["u_despues"] == 4
    # una receta que nombra el universo de todos los nacimientos para una variable del niño vivo no pasa: no cubre su batería
    f = verificar(plan("nino", cond("REC43", "H11", "en", (1,)), universo_analitico="nino_hijo_de_entrevistada"), ctx, con)
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "universo") and "nino_vivo" in f.motivo
    vivos = ok(verificar(plan("nino", cond("REC43", "H11", "en", (1,)), universo_analitico="nino_vivo_hijo_de_entrevistada"), ctx, con))
    assert vivos.controles["u_despues"] == 4
    # una restricción de la batería del niño vivo en un plan de parto lo lleva al universo de vivos
    mixto = ok(verificar(plan("nino", cond("REC41", "M17", "en", (1,)), [cond("REC43", "H11", "en", (0, 1))]), ctx, con))
    assert mixto.universo_analitico.id == "nino_vivo_hijo_de_entrevistada"


def test_rec21_es_solo_un_puente_y_no_puede_ser_la_tabla_base_de_un_plan_del_nino(mundo):
    ctx, con = mundo
    f = verificar(plan("nino", cond("REC21", "B4", "en", (1,))), ctx, con)
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "tabla_base")
    assert "REC21" in f.motivo and "puente" in f.motivo
    f = verificar(plan("nino", cond("REC21", "B5", "en", (1,)), [cond("REC21", "B4", "en", (1, 2))]), ctx, con)
    assert isinstance(f, Falla) and "puente" in f.motivo
    # sí sirve de puente: el sexo o la sobrevivencia del niño como condición o restricción de un plan que parte de otra tabla del hijo
    pc = ok(verificar(plan("nino", cond("REC41", "M17", "en", (1,)), [cond("REC21", "B4", "en", (1,))]), ctx, con))
    assert pc.archivo_unidad == "REC41" and any(u.texto == "REC41→REC21" for u in pc.uniones)
    assert ctx.unidades and next(u for u in ctx.unidades if u.archivo == "REC21").solo_puente


# ------------------------------------------------------------------ C-M1-07-3 (a): REC44 con el pernocte y RECH6 para solo mediciones

def test_los_universos_de_rec44_exigen_el_pernocte_por_la_linea_del_nino_sin_contarlo_como_perdida(mundo):
    ctx, con = mundo
    p = plan("nino", cond("REC44", "HW57", "en", (1, 2, 3)), [cond("REC0111", "V012", "entre", (15, 49))])
    pc = ok(verificar(p, ctx, con))
    assert pc.universo_analitico.id == "nino_hijo_de_entrevistada_hb_medida" and pc.archivo_unidad == "REC44"
    hv103 = next(pr for pr in pc.universo_analitico.predicados if pr.var == "HV103")
    assert hv103.valores == [1.0]
    textos = [u.texto for u in pc.uniones]
    assert "REC21→RECH1" in textos and "REC0111→RECH1" not in textos            # el pernocte es el del niño (B16 = HVIDX), no el de la madre
    assert next(u for u in pc.uniones if u.texto == "REC21→RECH1").pares == (("HHID", "HHID"), ("B16", "HVIDX"))
    c = pc.controles                                                           # c2 (B16 = 0) y c5 (no durmió en el hogar) quedan fuera del universo
    assert c["filas_unidad"] == c["filas_tras_uniones"] == 4 and c["u_antes"] == 2 and c["u_despues"] == 2 and c["perdida_u"] == 0
    assert pc.diseno.nivel_submuestra == "medicion" and pc.diseno.peso_expr == "HV005/1e6"
    # todo universo que cubre REC44 lleva el pernocte
    for u in ctx.universos:
        if "REC44" in u.aplica_a.archivos:
            assert any(pr.var == "HV103" for pr in u.predicados), u.id


def test_un_plan_de_solo_medicion_sobre_rec44_se_rechaza_a_favor_de_rech6(mundo):
    ctx, con = mundo
    for p in (plan("nino", cond("REC44", "HW57", "en", (1, 2, 3)), [cond("REC44", "HW55", "en", (0,))]),
              plan("nino", cond("REC44", "HW70", "<", (-200,)), [cond("REC44", "HW1", "entre", (0, 59))], cortes=["area", "sexo"]),
              plan("nino", cond("REC44", "HW70", "entre", (-600, -200)))):
        f = verificar(p, ctx, con)
        assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "tabla_preferida"), f
        assert "RECH6" in f.motivo and "REC44" in f.motivo
    # REC44 sí cuando el plan necesita una variable de la madre o del hijo de la entrevistada
    for restr in ([cond("REC0111", "V012", "entre", (15, 49))], [cond("REC41", "M17", "en", (0, 1))], [cond("REC21", "B4", "en", (1,))]):
        ok(verificar(plan("nino", cond("REC44", "HW57", "en", (1, 2, 3)), restr), ctx, con))
    # y RECH6 sigue sin cambios para el mismo indicador
    pc = ok(verificar(plan("nino", cond("RECH6", "HC57", "en", (1, 2, 3)), [cond("RECH6", "HC57", "en", (1, 2, 3, 4))]), ctx, con))
    assert pc.universo_analitico.id == "nino_hecho_hb_medida"
