"""M1-07, en el Mac: el diseño, los universos y las uniones del lote sobre los Parquet y el índice reales de la ENDES 2024.

Necesitan `biblioteca/microdatos/ENDES/2024/` y `biblioteca/variables/` (`pap microdatos convertir` y `pap variables indexar`): si faltan, FALLAN."""
from dataclasses import replace

import pytest

from pap.inferencia import tablas_curadas as tc
from pap.inferencia.duckdb_seguro import conexion_segura, ejecutar_select
from pap.inferencia.ejecutor import Ejecutor
from pap.inferencia.gramatica import citar
from pap.inferencia.plan import Plan
from pap.inferencia.verificador import Contexto, Falla, comprobar_cardinalidades, verificar

from conftest import RAIZ_REAL

pytestmark = [pytest.mark.regresion_microdatos, pytest.mark.solo_mac]

LOTE = ["RECH0", "RECH23", "RECH1", "RECH4", "RECH6", "REC21", "REC41", "REC43", "REC44", "REC94", "REC95", "DIT",
        "REC0111", "REC91", "RE223132", "REC42", "RE516171", "RE758081"]
NUEVAS_N_A_1 = [("REC41", "MIDX"), ("REC43", "HIDX"), ("REC44", "HWIDX"), ("REC94", "IDX94"), ("REC95", "IDX95"), ("DIT", "BIDX")]


@pytest.fixture(scope="module")
def ctx():
    for carpeta in ("biblioteca/variables", "biblioteca/microdatos/ENDES/2024"):
        assert (RAIZ_REAL / carpeta).is_dir(), f"falta {carpeta}"
    c = Contexto.cargar(RAIZ_REAL)
    # el lote queda `propuesto` hasta el visto del dueño; aquí se prueba como quedará con él
    variables = {k: {**v, "estado": "revisado"} for k, v in c.esquema.variables.items()}
    return replace(c, esquema=replace(c.esquema, variables=variables))


@pytest.fixture(scope="module")
def con():
    return conexion_segura(RAIZ_REAL)


def _var(ctx, tabla: str, preferida: str | None = None, con=None):
    """Una variable categórica del índice de la tabla, sin rol faltante ni origen del INEI, con respuestas en los datos, y su primer código con sentido."""
    cands = sorted(v["variable"] for v in ctx.esquema.variables.values()
                   if v["archivo"] == tabla and v.get("clase") == "categoria" and not v.get("rol_faltante") and v.get("tipo_origen") != "construida_inei")
    if preferida:
        cands = [preferida]
    for nombre in cands:
        cats = ctx.esquema.categorias.get(f"ENDES·2024·{tabla}·{nombre}", {})
        codigos = [k for k, r in cats.items() if r.get("es_especial") in (None, "no", False) and not r.get("rol_faltante")]
        if len(codigos) >= 2 and (con is None or ejecutar_select(con, f"SELECT count({citar(nombre)}) FROM read_parquet(?)", [_ruta(tabla)]).fetchone()[0] > 1000):
            return nombre, [float(codigos[0])]
    raise AssertionError(f"{tabla}: sin variable categórica utilizable")


def plan_de_prueba(ctx, tabla: str, con=None, **extra) -> Plan:
    """Un plan por tabla: la proporción de un código de una variable categórica, entre quienes la respondieron (restricción `no_es_nulo`)."""
    fila = tc.unidad_de(ctx.unidades, "ENDES", 2024, tabla)
    preferida = {"RECH6": "HC57", "REC44": "HW57", "REC41": "M17"}.get(tabla)
    nombre, codigos = _var(ctx, tabla, preferida, con)
    if tabla == "RECH6":
        codigos = [1.0, 2.0, 3.0]
    if tabla == "REC44":
        codigos = [1.0, 2.0, 3.0]
    var = f"ENDES·2024·{tabla}·{nombre}"
    return Plan.model_validate({
        "origen": "compuesto", "encuesta": "ENDES", "anios": [2024], "unidad": fila.unidad_plan, "medida": "proporcion",
        "indicador": {"combinar": "una", "condiciones": [{"var": var, "op": "en", "valores": codigos}]},
        "universo": {"restricciones": [{"var": var, "op": "no_es_nulo", "valores": []}]},
        "cortes": extra.get("cortes", []), "territorio": {"nivel": "nacional", "id": None}})


@pytest.mark.parametrize("tabla", LOTE)
def test_un_plan_de_prueba_por_cada_tabla_del_lote_pasa_el_verificador_y_calcula(ctx, con, tabla):
    pc = verificar(plan_de_prueba(ctx, tabla, con), ctx, con)
    assert not isinstance(pc, Falla), (tabla, pc)
    fila = tc.unidad_de(ctx.unidades, "ENDES", 2024, tabla)
    assert pc.archivo_unidad == fila.tabla_base == tabla
    assert pc.diseno.peso_expr == f"{fila.peso.variable}/1e6" or pc.diseno.nivel_submuestra == "medicion"
    c = pc.controles
    assert c["u_antes"] == c["u_despues"] > 0 and c["perdida_u"] == 0 and c["y_nulos_en_u"] == 0 and c["diseno_nulo_en_u"] == 0
    assert c["filas_unidad"] == c["filas_tras_uniones"] and c["conglomerados_u"] > 0 and c["estratos_u"] > 0
    (e,) = Ejecutor(raiz=RAIZ_REAL).ejecutar({2024: pc}, ctx)
    assert e.n == c["u_despues"] and e.valor is not None and 0 <= e.valor <= 1 and e.ee is not None


@pytest.mark.parametrize("tabla", ["REC21", "REC41", "REC43", "REC44", "REC94", "REC95", "DIT"])
def test_los_cortes_del_hogar_y_de_la_madre_llegan_a_cada_tabla_del_hijo(ctx, con, tabla):
    pc = verificar(plan_de_prueba(ctx, tabla, con, cortes=["area", "sexo", "quintil_riqueza"]), ctx, con)
    assert not isinstance(pc, Falla), (tabla, pc)
    assert {c.id: c.archivo for c in pc.cortes} == {"area": "RECH0", "sexo": "REC21", "quintil_riqueza": "RECH23"}
    assert pc.controles["perdida_u"] == 0 and pc.controles["filas_unidad"] == pc.controles["filas_tras_uniones"]


def test_rech5_no_esta_en_el_lote_porque_la_ficha_no_dice_su_peso(ctx, con):
    assert tc.unidad_de(ctx.unidades, "ENDES", 2024, "RECH5") is None
    assert not [f for f in ctx.diseno if f.archivo == "RECH5"]
    f = verificar(Plan.model_validate({
        "origen": "compuesto", "encuesta": "ENDES", "anios": [2024], "unidad": "mujer", "medida": "proporcion",
        "indicador": {"combinar": "una", "condiciones": [{"var": "ENDES·2024·RECH5·HA57", "op": "en", "valores": [1]}]},
        "territorio": {"nivel": "nacional", "id": None}}), ctx, con)
    assert isinstance(f, Falla) and f.tipo == "plan"


# ------------------------------------------------------------------ uniones (tarea 4): sin pérdidas ni duplicados

def _ruta(a: str) -> str:
    return str(RAIZ_REAL / "biblioteca" / "microdatos" / "ENDES" / "2024" / f"{a}.parquet")


@pytest.mark.parametrize("hijo,indice", NUEVAS_N_A_1)
def test_la_union_del_hijo_con_rec21_no_pierde_ni_repite_filas(con, hijo, indice):
    n, con_pareja, sin_repetir = ejecutar_select(
        con, f"SELECT count(*), count(b.{citar('CASEID')}), count(DISTINCT (h.{citar('CASEID')}, h.{citar(indice)})) FROM read_parquet(?) h "
             f"LEFT JOIN read_parquet(?) b ON h.{citar('CASEID')} = b.{citar('CASEID')} AND h.{citar(indice)} = b.{citar('BIDX')}",
        [_ruta(hijo), _ruta("REC21")]).fetchone()
    assert n == con_pareja == sin_repetir and n > 0
    # y REC21 no repite su nacimiento: el left join desde el hijo deja las mismas filas
    assert ejecutar_select(con, "SELECT count(*), count(DISTINCT (CASEID, BIDX)) FROM read_parquet(?)", [_ruta("REC21")]).fetchone() == (60693, 60693)


def test_las_cardinalidades_declaradas_se_cumplen_en_los_datos(ctx, con):
    assert comprobar_cardinalidades(ctx.relaciones[("ENDES", 2024)], ctx.carpeta_microdatos, "ENDES", 2024, con) == []
    card = {(u.hijo, u.padre): u.cardinalidad for u in ctx.relaciones[("ENDES", 2024)]}
    assert card[("RECH4", "RECH1")] == "1:1" and card[("REC91", "REC0111")] == "1:1" and card[("REC44", "REC21")] == "1:0..1"


# ------------------------------------------------------------------ universos con sus casos (el INEI publica los casos sin ponderar)

def test_el_universo_del_hogar_da_los_34018_hogares_del_informe(ctx, con):
    n = ejecutar_select(con, "SELECT count(*) FILTER (WHERE HV015 = 1), count(*) FILTER (WHERE HV015 = 1 AND HV025 = 1), "
                             "count(*) FILTER (WHERE HV015 = 1 AND HV025 = 2), count(*) FROM read_parquet(?)", [_ruta("RECH0")]).fetchone()
    assert n == (34018, 22099, 11919, 37390)                                  # Cuadros N.º 1 y 2 del informe del INEI
    u = {x.id: x for x in tc.leer_universos(RAIZ_REAL)}["hogar"]
    assert tc.sql_predicados(u.predicados) == "HV015 IN (1)"


def test_los_universos_de_la_mujer_y_del_hijo_dan_los_casos_conocidos(ctx, con):
    # mujer_12_49_entrevistada: las 34 252 con entrevista completa de las 37 117 elegibles
    plan = Plan.model_validate({
        "origen": "compuesto", "encuesta": "ENDES", "anios": [2024], "unidad": "mujer", "medida": "proporcion",
        "indicador": {"combinar": "una", "condiciones": [{"var": "ENDES·2024·REC0111·V025", "op": "en", "valores": [2]}]},
        "territorio": {"nivel": "nacional", "id": None}})
    pc = verificar(plan, ctx, con)
    assert not isinstance(pc, Falla), pc
    assert pc.universo_analitico.id == "mujer_12_49_entrevistada" and (pc.controles["filas_unidad"], pc.controles["u_despues"]) == (37117, 34252)
    # el hijo de la entrevistada: todos los nacimientos de REC41 (19 751) y, con la madre de 15 a 49, 19 737 (Cuadro N.º 29 p. 105)
    p41 = plan_de_prueba(ctx, "REC41", con)
    pc = verificar(p41, ctx, con)
    assert pc.universo_analitico.id == "nino_hijo_de_entrevistada" and pc.controles["u_despues"] == 19751
    pc = verificar(p41.model_copy(update={"universo_analitico": "nino_hijo_de_entrevistada_15_49", "origen": "receta", "receta_id": "prueba_m107"}), ctx, con)
    assert not isinstance(pc, Falla), pc
    assert pc.controles["u_despues"] == 19737
