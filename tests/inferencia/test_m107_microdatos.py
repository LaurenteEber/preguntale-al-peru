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

LOTE = ["RECH0", "RECH23", "RECH1", "RECH4", "RECH5", "RECH6", "REC21", "REC41", "REC43", "REC44", "REC94", "REC95", "DIT",
        "REC0111", "REC91", "RE223132", "REC42", "RE516171", "RE758081"]
PLANABLES = [a for a in LOTE if a != "REC21"]                     # REC21 solo es puente (C-M1-07-2): ningún plan parte de ella
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
    preferida = {"RECH6": "HC57", "REC44": "HW57", "REC41": "M17", "RECH5": "HA57A"}.get(tabla)
    nombre, codigos = _var(ctx, tabla, preferida, con)
    if tabla == "RECH6":
        codigos = [1.0, 2.0, 3.0]
    if tabla in ("REC44", "RECH5"):
        codigos = [1.0, 2.0, 3.0]
    var = f"ENDES·2024·{tabla}·{nombre}"
    restricciones = [{"var": var, "op": "no_es_nulo", "valores": []}]
    if tabla == "REC44":                      # C-M1-07-3: REC44 solo cuando el plan necesita una variable de la madre o del hijo de la entrevistada
        restricciones.append({"var": "ENDES·2024·REC0111·V012", "op": "entre", "valores": [15, 49]})
    return Plan.model_validate({
        "origen": "compuesto", "encuesta": "ENDES", "anios": [2024], "unidad": fila.unidad_plan, "medida": "proporcion",
        "indicador": {"combinar": "una", "condiciones": [{"var": var, "op": "en", "valores": codigos}]},
        "universo": {"restricciones": restricciones},
        "cortes": extra.get("cortes", []), "territorio": {"nivel": "nacional", "id": None}})


@pytest.mark.parametrize("tabla", PLANABLES)
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


@pytest.mark.parametrize("tabla", ["REC41", "REC43", "REC44", "REC94", "REC95", "DIT"])
def test_los_cortes_del_hogar_y_de_la_madre_llegan_a_cada_tabla_del_hijo(ctx, con, tabla):
    pc = verificar(plan_de_prueba(ctx, tabla, con, cortes=["area", "sexo", "quintil_riqueza"]), ctx, con)
    assert not isinstance(pc, Falla), (tabla, pc)
    assert {c.id: c.archivo for c in pc.cortes} == {"area": "RECH0", "sexo": "REC21", "quintil_riqueza": "RECH23"}
    assert pc.controles["perdida_u"] == 0 and pc.controles["filas_unidad"] == pc.controles["filas_tras_uniones"]


def test_rech5_entra_al_lote_con_el_factor_hogar_y_el_universo_de_hecho_de_15_a_49(ctx, con):
    """C-M1-07-1 (dueño, 13/11/2026): 38 488 mujeres de 12 a 49 años; de hecho de 15 a 49: 33 515; con hemoglobina medida y nivel de anemia: 30 290."""
    fila = tc.unidad_de(ctx.unidades, "ENDES", 2024, "RECH5")
    assert (fila.unidad_plan, fila.tabla_base, fila.peso.variable, fila.peso.en) == ("mujer", "RECH5", "HV005", "RECH0")
    assert {f.medicion for f in ctx.diseno if f.archivo == "RECH5"} == {"hemoglobina", "talla"}
    pc = verificar(Plan.model_validate({
        "origen": "compuesto", "encuesta": "ENDES", "anios": [2024], "unidad": "mujer", "medida": "proporcion",
        "indicador": {"combinar": "una", "condiciones": [{"var": "ENDES·2024·RECH5·HA1", "op": "entre", "valores": [15, 49]}]},
        "territorio": {"nivel": "nacional", "id": None}}), ctx, con)
    assert not isinstance(pc, Falla), pc
    assert pc.universo_analitico.id == "mujer_15_49_de_hecho" and (pc.controles["filas_unidad"], pc.controles["u_despues"]) == (38488, 33515)
    pc = verificar(Plan.model_validate({
        "origen": "compuesto", "encuesta": "ENDES", "anios": [2024], "unidad": "mujer", "medida": "proporcion",
        "indicador": {"combinar": "una", "condiciones": [{"var": "ENDES·2024·RECH5·HA57A", "op": "en", "valores": [1, 2, 3]}]},
        "universo": {"restricciones": [{"var": "ENDES·2024·RECH5·HA57A", "op": "en", "valores": [1, 2, 3, 4]}]},
        "territorio": {"nivel": "nacional", "id": None}}), ctx, con)
    assert not isinstance(pc, Falla), pc
    assert pc.universo_analitico.id == "mujer_15_49_de_hecho_hb_medida" and pc.controles["u_despues"] == 30290 and pc.controles["perdida_u"] == 0
    assert (pc.diseno.archivo, pc.diseno.nivel_submuestra, pc.diseno.peso_expr) == ("RECH5", "medicion", "HV005/1e6")


def test_rec21_es_solo_puente_en_los_datos_reales(ctx, con):
    plan = Plan.model_validate({
        "origen": "compuesto", "encuesta": "ENDES", "anios": [2024], "unidad": "nino", "medida": "proporcion",
        "indicador": {"combinar": "una", "condiciones": [{"var": "ENDES·2024·REC21·B4", "op": "en", "valores": [1]}]},
        "territorio": {"nivel": "nacional", "id": None}})
    f = verificar(plan, ctx, con)
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "tabla_base") and "puente" in f.motivo
    p41 = plan_de_prueba(ctx, "REC41", con).model_dump()                    # como restricción de un plan del hijo sí sirve
    p41["universo"]["restricciones"] = [*p41["universo"]["restricciones"], {"var": "ENDES·2024·REC21·B4", "op": "en", "valores": [1]}]
    pc = verificar(Plan.model_validate(p41), ctx, con)
    assert not isinstance(pc, Falla), pc
    assert pc.archivo_unidad == "REC41"


def test_el_nino_vivo_para_vacunas_diarrea_y_alimentacion_actual_y_todos_los_nacimientos_para_la_cesarea(ctx, con):
    """C-M1-07-2: de los 19 751 nacimientos, 169 están fallecidos (B5 = 0); con madres de 15 a 49: 19 737 todos y 19 568 vivos."""
    def plan(tabla, var, codigos):
        return Plan.model_validate({
            "origen": "compuesto", "encuesta": "ENDES", "anios": [2024], "unidad": "nino", "medida": "proporcion",
            "indicador": {"combinar": "una", "condiciones": [{"var": f"ENDES·2024·{tabla}·{var}", "op": "en", "valores": codigos}]},
            "territorio": {"nivel": "nacional", "id": None}})
    cesarea = verificar(plan("REC41", "M17", [1]), ctx, con)
    assert (cesarea.universo_analitico.id, cesarea.controles["filas_unidad"], cesarea.controles["u_despues"]) == ("nino_hijo_de_entrevistada", 19751, 19737)
    for tabla, var, codigos in (("REC43", "H11", [1]), ("REC41", "M38", [1]), ("REC95", "S466", [1])):     # diarrea, biberón de ayer, controles de crecimiento
        pc = verificar(plan(tabla, var, codigos), ctx, con)
        assert not isinstance(pc, Falla), (tabla, pc)
        assert pc.universo_analitico.id == "nino_vivo_hijo_de_entrevistada" and pc.controles["u_despues"] == 19568, tabla
        assert pc.controles["perdida_u"] == 0 and pc.controles["y_nulos_en_u"] == 0
    (e,) = Ejecutor(raiz=RAIZ_REAL).ejecutar({2024: verificar(plan("REC41", "M17", [1]), ctx, con)}, ctx)
    assert e.n == 19737 and round(e.valor * 100, 1) == 38.2                       # el control de cesárea no cambia


def test_los_universos_de_rec44_exigen_el_pernocte_y_dan_la_desnutricion_cronica_del_informe(ctx, con):
    """C-M1-07-3 (a): REC44 → REC21 → RECH1 por B16 = HVIDX. Con los niños de 0 a 59 meses con talla válida y madre de 15 a 49: 18 861 y 12,12 %
    de desnutrición crónica (HW70 < −200) con HV005 (el informe, Cuadro N.º 04 p. 49: 12,1 %)."""
    madre = {"var": "ENDES·2024·REC0111·V012", "op": "entre", "valores": [15, 49]}
    plan = Plan.model_validate({
        "origen": "compuesto", "encuesta": "ENDES", "anios": [2024], "unidad": "nino", "medida": "proporcion",
        "indicador": {"combinar": "una", "condiciones": [{"var": "ENDES·2024·REC44·HW70", "op": "<", "valores": [-200]}]},
        "universo": {"restricciones": [madre]}, "territorio": {"nivel": "nacional", "id": None}})
    pc = verificar(plan, ctx, con)
    assert not isinstance(pc, Falla), pc
    assert pc.universo_analitico.id == "nino_hijo_de_entrevistada_talla" and pc.archivo_unidad == "REC44"
    assert "REC21→RECH1" in [u.texto for u in pc.uniones] and "REC0111→RECH1" not in [u.texto for u in pc.uniones]
    assert pc.controles["u_despues"] == 18861 and pc.controles["perdida_u"] == 0 and pc.controles["filas_unidad"] == pc.controles["filas_tras_uniones"]
    (e,) = Ejecutor(raiz=RAIZ_REAL).ejecutar({2024: pc}, ctx)
    assert abs(e.valor * 100 - 12.1) <= 0.1 and e.n == 18861
    # sin la madre el plan es de solo medición: se rechaza a favor de RECH6
    f = verificar(plan.model_copy(update={"universo": plan.universo.model_copy(update={"restricciones": []})}), ctx, con)
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "tabla_preferida") and "RECH6" in f.motivo


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
    # C-M1-07-3 (b): por defecto la mujer entrevistada de 15 a 49 (30 872 de las 34 252 con entrevista completa); la de 12 a 49 solo nombrada
    plan = Plan.model_validate({
        "origen": "compuesto", "encuesta": "ENDES", "anios": [2024], "unidad": "mujer", "medida": "proporcion",
        "indicador": {"combinar": "una", "condiciones": [{"var": "ENDES·2024·REC0111·V025", "op": "en", "valores": [2]}]},
        "territorio": {"nivel": "nacional", "id": None}})
    pc = verificar(plan, ctx, con)
    assert not isinstance(pc, Falla), pc
    assert pc.universo_analitico.id == "mujer_15_49_entrevistada" and (pc.controles["filas_unidad"], pc.controles["u_despues"]) == (37117, 30872)
    pc = verificar(plan.model_copy(update={"universo_analitico": "mujer_12_49_entrevistada", "origen": "receta", "receta_id": "prueba_m107"}), ctx, con)
    assert pc.universo_analitico.id == "mujer_12_49_entrevistada" and pc.controles["u_despues"] == 34252
    # el hijo de la entrevistada: con la madre de 15 a 49, 19 737 de los 19 751 de REC41 (Cuadro N.º 29 p. 105); con la de 12 a 49, los 19 751
    p41 = plan_de_prueba(ctx, "REC41", con)
    pc = verificar(p41, ctx, con)
    assert pc.universo_analitico.id == "nino_hijo_de_entrevistada" and pc.controles["u_despues"] == 19737
    pc = verificar(p41.model_copy(update={"universo_analitico": "nino_hijo_de_entrevistada_12_49", "origen": "receta", "receta_id": "prueba_m107"}), ctx, con)
    assert not isinstance(pc, Falla), pc
    assert pc.controles["u_despues"] == 19751


def test_la_union_del_nino_con_su_fila_en_rech1_deja_fuera_del_universo_a_los_que_no_viven_en_el_hogar(con):
    """C-M1-07-3 (a): REC21 → RECH1 por (HHID, B16 = HVIDX), en `relaciones_parciales`. Los 169 fallecidos (B16 nulo) y los 82 con B16 = 0 no tienen pareja."""
    n, con_pareja, repetidas = ejecutar_select(
        con, f"SELECT count(*), count(p.{citar('HVIDX')}), count(*) - count(DISTINCT (r.{citar('CASEID')}, r.{citar('BIDX')})) FROM read_parquet(?) r "
             f"LEFT JOIN read_parquet(?) p ON r.{citar('HHID')} = p.{citar('HHID')} AND r.{citar('B16')} = p.{citar('HVIDX')}", [_ruta("REC21"), _ruta("RECH1")]).fetchone()
    assert (n, con_pareja, repetidas) == (60693, 50050, 0)
    r44 = ejecutar_select(
        con, f"SELECT count(*), count(p.{citar('HVIDX')}), count(*) FILTER (WHERE p.{citar('HV103')} = 1), count(*) FILTER (WHERE r.{citar('B16')} IS NULL), "
             f"count(*) FILTER (WHERE r.{citar('B16')} = 0) FROM read_parquet(?) m JOIN read_parquet(?) r ON m.{citar('CASEID')} = r.{citar('CASEID')} AND m.{citar('HWIDX')} = r.{citar('BIDX')} "
             f"LEFT JOIN read_parquet(?) p ON r.{citar('HHID')} = p.{citar('HHID')} AND r.{citar('B16')} = p.{citar('HVIDX')}",
        [_ruta("REC44"), _ruta("REC21"), _ruta("RECH1")]).fetchone()
    assert r44 == (19751, 19500, 19429, 169, 82)
    # RECH5 → RECH1 (HA0 = HVIDX), esta sí sin pérdida: las 38 488 mujeres encuentran su fila
    assert ejecutar_select(con, f"SELECT count(*), count(p.{citar('HVIDX')}) FROM read_parquet(?) r LEFT JOIN read_parquet(?) p ON r.{citar('HHID')} = p.{citar('HHID')} "
                                f"AND r.{citar('HA0')} = p.{citar('HVIDX')}", [_ruta("RECH5"), _ruta("RECH1")]).fetchone() == (38488, 38488)
