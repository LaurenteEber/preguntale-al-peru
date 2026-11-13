"""M0-07: el verificador base, con datos sintéticos (tablas curadas reales; Parquet e índice mínimos)."""
import json
from dataclasses import replace

import pytest

from pap.inferencia.duckdb_seguro import conexion_segura
from pap.inferencia.gramatica import Esquema
from pap.inferencia.plan import Plan
from pap.inferencia.verificador import Contexto, Falla, ParametrosVerificador, verificar

from .recetas_m0 import RECETAS, plan_anemia, plan_dci
from .sintetico_m0 import VERIFICADA_2024, contexto_sintetico


def plan_de_la_receta(nombre: str) -> Plan:
    return RECETAS[nombre]("nacional")


def con_cambios(plan: Plan, **cambios) -> Plan:
    return Plan.model_validate({**json.loads(plan.model_dump_json()), **cambios})


@pytest.fixture(scope="module")
def sint(tmp_path_factory):
    ctx, micro = contexto_sintetico(tmp_path_factory.mktemp("v"))
    return ctx, conexion_segura(carpetas=[micro])


def test_las_tres_recetas_se_completan_con_universo_diseno_y_territorio(sint):
    ctx, con = sint
    esperado_u = {"anemia": 4, "anemia_oms2024": 4, "dci": 4}
    for nombre, receta in RECETAS.items():
        pc = verificar(receta("nacional"), ctx, con)
        assert not isinstance(pc, Falla), pc
        # M1-03: la receta nombra su universo y el verificador lo aplica (anemia: hemoglobina medida; DCI: la base común)
        assert pc.universo_analitico.id == plan_de_la_receta(nombre).universo_analitico and pc.archivo_unidad == "RECH6"
        assert pc.universo_analitico.id == {"anemia": "nino_hecho_hb_medida", "anemia_oms2024": "nino_hecho_hb_medida", "dci": "nino_hecho"}[nombre]
        assert (pc.diseno.archivo, pc.diseno.nivel_submuestra) == ("RECH6", "medicion")
        assert (pc.diseno.peso_expr, pc.diseno.psu_expr) == ("HV005/1e6", "HV021")
        assert pc.territorio.nivel == "nacional" and pc.ajustes == ()
        assert [(u.hijo, u.padre) for u in pc.uniones] == [("RECH6", "RECH0"), ("RECH6", "RECH1")]
        c = pc.controles
        assert c["u_antes"] == c["u_despues"] == esperado_u[nombre] and c["perdida_u"] == 0
        assert c["filas_unidad"] == c["filas_tras_uniones"] == 6
        assert c["y_nulos_en_u"] == 0 and c["diseno_nulo_en_u"] == 0 and c["suma_pesos_u"] > 0
        assert c["conglomerados_u"] >= 1 and c["estratos_u"] >= 1


def test_el_verificador_sin_conexion_no_corre_controles(sint):
    ctx, _ = sint
    pc = verificar(plan_anemia(), ctx)
    assert pc.controles is None and pc.id_plan == plan_anemia().id_plan


# ------------------------------------------------------------------ variables

def test_dentro_de_una_receta_se_acepta_propuesto_y_fuera_hace_falta_revisado(sint, tmp_path):
    ctx, _ = sint
    compuesto = con_cambios(plan_anemia(), origen="compuesto", receta_id=None, universo_analitico=None)
    f = verificar(compuesto, ctx)
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "variable") and "propuesto" in f.motivo
    ctx_rev, _ = contexto_sintetico(tmp_path, estado="revisado")
    assert not isinstance(verificar(compuesto, ctx_rev), Falla)


def test_una_variable_construida_inei_solo_va_en_una_receta(tmp_path):
    ctx, _ = contexto_sintetico(tmp_path, estado="revisado")
    vid = "ENDES·2024·RECH6·HC57"
    variables = {k: dict(v) for k, v in ctx.esquema.variables.items()}
    variables[vid]["tipo_origen"] = "construida_inei"
    ctx2 = replace(ctx, esquema=replace(ctx.esquema, variables=variables))
    assert not isinstance(verificar(plan_anemia(), ctx2), Falla)
    f = verificar(con_cambios(plan_anemia(), origen="compuesto", receta_id=None, universo_analitico=None), ctx2)
    assert isinstance(f, Falla) and "construida_inei" in f.motivo


def test_variable_o_categoria_inexistente(sint):
    ctx, _ = sint
    for var, op, valores, dim in [("ENDES·2024·RECH6·HC99", "en", [1], "variable"), ("ENDES·2024·RECH6·HC57", "en", [1, 7], "valores"),
                                  ("ENDES·2024·RECH6·HC1", "en", [6], "valores")]:
        p = con_cambios(plan_anemia(), indicador={"combinar": "una", "condiciones": [{"var": var, "op": op, "valores": valores}]})
        f = verificar(p, ctx)
        assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", dim), (var, f)


def test_un_rol_faltante_no_vacio_no_se_resuelve_en_m0(sint):
    ctx, _ = sint
    categorias = {k: {c: dict(r) for c, r in v.items()} for k, v in ctx.esquema.categorias.items()}
    categorias["ENDES·2024·RECH6·HC57"]["4"]["rol_faltante"] = "faltante_excluye"
    f = verificar(plan_anemia(), replace(ctx, esquema=replace(ctx.esquema, categorias=categorias)))
    assert isinstance(f, Falla) and f.dimension == "rol_faltante"


def test_una_variable_de_otro_anio_es_falla_estructural(sint):
    ctx, _ = sint
    p = con_cambios(plan_anemia(), anios=[2023])
    f = verificar(p, ctx)
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("estructural", "anio")


# ------------------------------------------------------------------ parámetros de la llamada

def test_anios_apilados_y_medida(sint):
    ctx, _ = sint
    f = verificar(con_cambios(plan_anemia(), anios=[2020, 2021, 2022, 2023, 2024]), ctx)
    assert (f.tipo, f.dimension) == ("plan", "anios") and "4" in f.motivo
    f = verificar(con_cambios(plan_anemia(), anios=[2023, 2024]), ctx)
    assert (f.tipo, f.dimension) == ("estructural", "anio")
    f = verificar(con_cambios(plan_anemia(), medida="total"), ctx)
    assert (f.tipo, f.dimension) == ("estructural", "medida_no_disponible")


def test_los_topes_salen_del_yaml():
    p = ParametrosVerificador.desde_yaml()
    assert (p.dominios_max_llamada, p.anios_apilados_max_llamada, p.medidas_disponibles) == (100, 4, ("proporcion",))


def test_dominios_max_llamada(sint):
    ctx, con = sint
    chico = replace(ctx, p=replace(ctx.p, dominios_max_llamada=2))
    assert not isinstance(verificar(plan_anemia(), chico, con), Falla)                          # 1 unidad
    f = verificar(plan_anemia(cortes=("area",)), chico, con)                                     # 1 × (2 categorías + «sin dato»)
    assert (f.tipo, f.dimension) == ("plan", "dominios") and "3 dominios" in f.motivo
    f = verificar(plan_dci("departamento", cortes=("area",)), ctx, con)                          # 2 departamentos con niños × 3
    assert not isinstance(f, Falla) and f.controles["unidades_territorio"] == 2 and f.controles["dominios"] == 6
    f = verificar(plan_anemia("departamento", "15", cortes=("area",)), chico)                    # con id y sin conexión
    assert (f.tipo, f.dimension) == ("plan", "dominios")


# ------------------------------------------------------------------ universo, diseño, cortes

def test_unidad_sin_universo_analitico(sint):
    ctx, _ = sint
    f = verificar(con_cambios(plan_anemia(), unidad="mujer"), ctx)
    assert (f.tipo, f.dimension) == ("plan", "universo")


def test_peso_de_la_submuestra_mas_restrictiva(sint):
    ctx, _ = sint
    # RECH0 (hogar) con otro peso: gana RECH6 (medición) aunque el corte «área» venga de RECH0
    diseno = [d.model_copy(update={"peso_expr": "HV005/2e6"}) if d.archivo == "RECH0" else d for d in ctx.diseno]
    pc = verificar(plan_anemia(cortes=("area",)), replace(ctx, diseno=diseno))
    assert pc.diseno.archivo == "RECH6" and pc.diseno.peso_expr == "HV005/1e6"
    # dos de medición con pesos distintos: falla
    diseno = [d.model_copy(update={"peso_expr": "HV005/3e6"}) if (d.archivo, d.medicion) == ("RECH6", "talla") else d for d in ctx.diseno]
    f = verificar(plan_anemia(), replace(ctx, diseno=diseno))
    assert (f.tipo, f.dimension) == ("plan", "peso")
    # sin ninguna fila de diseño para los archivos que intervienen
    f = verificar(plan_anemia(), replace(ctx, diseno=[d for d in ctx.diseno if d.archivo != "RECH6"]))
    assert (f.tipo, f.dimension) == ("plan", "diseno")


def test_cortes_pendientes_o_desconocidos(sint):
    ctx, _ = sint
    # grupo_edad: los tramos del niño (C-M0-06-2) los compila M1-03, pero solo dentro de una receta que tenga juego de tramos
    pc = verificar(plan_anemia(cortes=("grupo_edad",)), ctx)
    assert len(pc.cortes[0].categorias) == 5
    f = verificar(plan_anemia(cortes=("no_existe",)), ctx)
    assert (f.tipo, f.dimension) == ("plan", "cortes")
    pc = verificar(plan_anemia(cortes=("area",)), ctx)
    assert [(c.id, c.archivo, c.variable) for c in pc.cortes] == [("area", "RECH0", "HV025")] and pc.cortes[0].categorias == {1: "urbano", 2: "rural"}


# ------------------------------------------------------------------ nivel fuera de inferencia_verificada (R-ENC-06)

@pytest.mark.parametrize("verificada,pedido,esperado", [
    (VERIFICADA_2024, ("LIMA_REGION", None), ("LIMA_REGION", None)),                               # ámbito publicado
    (VERIFICADA_2024, ("departamento", None), ("departamento", None)),
    (VERIFICADA_2024, ("CALLAO", None), ("CALLAO", None)),                                          # rango del departamento
    (VERIFICADA_2024 | {"ambitos_publicados": ""}, ("LIMA_REGION", None), ("departamento", "15")),
    (VERIFICADA_2024 | {"ambitos_publicados": ""}, ("LIMA_METROPOLITANA", "LIMA_METROPOLITANA"), ("departamento", "15")),
    (VERIFICADA_2024 | {"nivel_maximo": "dominio_subnacional", "ambitos_publicados": ""}, ("departamento", "15"), ("nacional", None)),
    (VERIFICADA_2024 | {"nivel_maximo": "dominio_subnacional", "ambitos_publicados": ""}, ("LIMA_REGION", None), ("nacional", None)),
    (VERIFICADA_2024 | {"inferencia_verificada": "false"}, ("dominio_subnacional", None), ("nacional", None)),
    (None, ("departamento", "15"), ("nacional", None)),                                             # sin fila: solo la cifra nacional
])
def test_un_nivel_no_verificado_sube_al_que_lo_contiene(sint, verificada, pedido, esperado):
    ctx, _ = sint
    ctx = replace(ctx, verificada={} if verificada is None else {("INEI-ENDES", 2024, "*"): verificada})
    pc = verificar(plan_anemia(*pedido), ctx)
    assert not isinstance(pc, Falla), pc
    assert (pc.plan.territorio.nivel, pc.plan.territorio.id) == esperado
    assert pc.territorio.nivel == esperado[0]
    assert bool(pc.ajustes) == (esperado[0] != pedido[0]) and (not pc.ajustes or "R-ENC-06" in pc.ajustes[0])


def test_el_plan_subido_de_nivel_tiene_otro_id_plan(sint):
    ctx, _ = sint
    ctx = replace(ctx, verificada={})
    pc = verificar(plan_anemia("departamento"), ctx)
    assert pc.id_plan != plan_anemia("departamento").id_plan and pc.id_plan == plan_anemia("nacional").id_plan


# ------------------------------------------------------------------ controles de las uniones

@pytest.mark.parametrize("variante,plan,dimension", [
    ("huerfano", plan_anemia(), "diseno"),                                  # un niño de u sin hogar: peso, estrato y conglomerado nulos
    ("duplicado", plan_anemia(), "uniones"),                                # una unión que repite filas de la unidad
    ("nulo", con_cambios(plan_anemia(), indicador={"combinar": "una", "condiciones": [{"var": "ENDES·2024·RECH6·HC57A", "op": "en", "valores": [1]}]},
                         universo={"restricciones": [{"var": "ENDES·2024·RECH6·HC1", "op": "entre", "valores": [6, 35]}]}), "y"),
])
def test_los_controles_de_la_union_detienen_el_plan(tmp_path, variante, plan, dimension):
    ctx, micro = contexto_sintetico(tmp_path, variante=variante)
    f = verificar(plan, ctx, conexion_segura(carpetas=[micro]))
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", dimension), f


def test_la_perdida_de_filas_de_u_mayor_al_tope_es_falla(sint, monkeypatch):
    ctx, con = sint
    import pap.inferencia.verificador as v

    original = v.compilar

    def compilar_que_pierde(pc, esquema, carpeta, *, solo_u_y=False, **kw):
        c = original(pc, esquema, carpeta, solo_u_y=solo_u_y, **kw)
        if not solo_u_y:                                    # el «después» deja fuera de u a las filas sin territorio (las del resto del país)
            c.sql = f"SELECT (u AND territorio IS NOT NULL) AS u, y, territorio, peso, estrato, upm FROM ({c.sql})"
        return c

    monkeypatch.setattr(v, "compilar", compilar_que_pierde)
    f = verificar(plan_anemia("CALLAO"), ctx, con)
    assert isinstance(f, Falla) and f.dimension == "uniones" and "pierden" in f.motivo
