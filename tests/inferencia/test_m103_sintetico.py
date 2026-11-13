"""M1-03, con datos sintéticos (sin microdatos reales): uniones por el padre común, cortes con tramos y categorías agrupadas,
universo analítico según la receta o la medición, y el control de HC55 = 0.

Las tablas curadas son las reales; los Parquet y el índice son los mínimos de `sintetico_m0` más una tabla RECH23 (región natural y
quintil). Las pruebas con la ENDES 2024 real están en `test_m103_microdatos.py`."""
import json
from dataclasses import replace

import polars as pl
import pytest

from pap.errores import PapError
from pap.inferencia import tablas_curadas as tc
from pap.inferencia.duckdb_seguro import conexion_segura, ejecutar_select
from pap.inferencia.gramatica import Esquema, compilar
from pap.inferencia.plan import Plan, UnionPlan
from pap.inferencia.verificador import (Contexto, Falla, comprobar_cardinalidades, relaciones_desde_yaml, ruta_de_uniones,
                                        verificar)

from conftest import RAIZ_REAL

from .recetas_m0 import plan_anemia, plan_dci
from .sintetico_m0 import RANK, RELACIONES, VERIFICADA_2024, escribir_parquets, variables_sinteticas
from pap.inferencia.verificador import ParametrosVerificador

R23 = UnionPlan("RECH23", "RECH0", (("HHID", "HHID"),), "1:1")
RH6_0 = UnionPlan("RECH6", "RECH0", (("HHID", "HHID"),))
RH6_1 = UnionPlan("RECH6", "RECH1", (("HHID", "HHID"), ("HC0", "HVIDX")))
CITA = "Ficha técnica ENDES 2024, §VI p. 11"


# ------------------------------------------------------------------ armado del contexto sintético

def _con_rech23(tmp_path, variante: str = "base", cardinalidad: str = "1:1", **cambios):
    """Contexto con RECH23 (SHREGION: h1 = 1, h2 = 2, h3 = 3, h4 = 4; HV270: 1, 2, 3, 5). `variante`: `base`; `repetido` (RECH23
    repite el hogar h1); `sin_h3` (RECH23 no trae a h3); `hb_no_medida` (un niño de 20 meses con HC55 = 1 y nivel de anemia)."""
    micro = escribir_parquets(tmp_path / "microdatos")
    destino = micro / "ENDES" / "2024"
    hogares = ["h1", "h2", "h3", "h4"]
    region, quintil = [1, 2, 3, 4], [1, 2, 3, 5]
    if variante == "repetido":
        hogares, region, quintil = hogares + ["h1"], region + [1], quintil + [1]
    if variante == "sin_h3":
        hogares, region, quintil = [h for h in hogares if h != "h3"], [1, 2, 4], [1, 2, 5]
    pl.DataFrame({"HHID": hogares, "SHREGION": [float(x) for x in region], "HV270": [float(x) for x in quintil]}).write_parquet(destino / "RECH23.parquet")
    if variante == "hb_no_medida":
        h6, h1 = pl.read_parquet(destino / "RECH6.parquet"), pl.read_parquet(destino / "RECH1.parquet")
        nuevo = {"HHID": "h2", "HC0": 2.0, "HC1": 20.0, "HC55": 1.0, "HC57": 1.0, "HC57A": 1.0, "HC70": -10.0}
        pl.concat([h6, pl.DataFrame([nuevo], schema=h6.schema)]).write_parquet(destino / "RECH6.parquet")
        pl.concat([h1, pl.DataFrame([{"HHID": "h2", "HVIDX": 2.0, "HV103": 1.0}], schema=h1.schema)]).write_parquet(destino / "RECH1.parquet")
    v, c, a = variables_sinteticas(cambios.pop("estado", "propuesto"))
    nuevas = [{"var_id": f"ENDES·2024·RECH23·{col}", "encuesta": "ENDES", "anio": 2024, "archivo": "RECH23", "variable": col,
               "tipo_valor": "categorica" if col != "HHID" else "texto", "estado": v["estado"][0], "tipo_origen": None, "rol_faltante": None}
              for col in ("HHID", "SHREGION", "HV270")]
    v = pl.concat([v, pl.DataFrame(nuevas, schema=v.schema)])
    a = pl.concat([a, pl.DataFrame([{"encuesta": "ENDES", "anio": 2024, "archivo": "RECH23", "unidad": "hogar", "llave": ["HHID"]}], schema=a.schema)])
    relaciones = [*RELACIONES, replace(R23, cardinalidad=cardinalidad)]
    ctx = Contexto(Esquema.desde_frames(v, c, a), tc.leer_universos(RAIZ_REAL), tc.leer_diseno_muestral(RAIZ_REAL),
                   tc.leer_territorios(RAIZ_REAL), tc.leer_cortes(RAIZ_REAL), tc.leer_perfil_anual(RAIZ_REAL),
                   {("ENDES", 2024): relaciones}, {("INEI-ENDES", 2024, "*"): VERIFICADA_2024}, RANK,
                   ParametrosVerificador.desde_yaml(), micro, tc.leer_mediciones(RAIZ_REAL), tc.leer_unidades(RAIZ_REAL))
    return replace(ctx, **cambios), conexion_segura(carpetas=[micro])


def _plan(base: Plan, **cambios) -> Plan:
    return Plan.model_validate({**json.loads(base.model_dump_json()), **cambios})


# ------------------------------------------------------------------ 1. unión por el padre común

def test_ruta_de_uniones_va_de_un_hijo_a_otro_por_el_padre_comun_si_es_1_a_1():
    ruta = ruta_de_uniones([RH6_0, R23], "RECH6", {"RECH23"})
    assert [(u.hijo, u.padre, u.hacia) for u in ruta] == [("RECH6", "RECH0", "padre"), ("RECH23", "RECH0", "hijo")]
    assert [u.unido for u in ruta] == ["RECH0", "RECH23"]
    assert [u.ancla for u in ruta] == ["RECH6", "RECH0"]                  # la segunda unión cuelga de lo que la primera trajo


def test_ruta_de_uniones_admite_1_a_0_o_1_y_rechaza_lo_que_no_es_1_a_1():
    assert ruta_de_uniones([RH6_0, replace(R23, cardinalidad="1:0..1")], "RECH6", {"RECH23"}) is not None
    # un hermano n:1 (varias filas por cada una del padre) repetiría las filas de la unidad: no se alcanza
    assert ruta_de_uniones([RH6_0, replace(R23, cardinalidad="n:1")], "RECH6", {"RECH23"}) is None
    assert ruta_de_uniones([RH6_0, UnionPlan("RECH4", "RECH0", (("HHID", "HHID"),), "n:1")], "RECH6", {"RECH4"}) is None


def test_ruta_de_uniones_solo_baja_un_nivel_desde_el_padre_comun():
    nieto = UnionPlan("NIETO", "RECH23", (("HHID", "HHID"),), "1:1")
    assert ruta_de_uniones([RH6_0, R23, nieto], "RECH6", {"NIETO"}) is None
    assert ruta_de_uniones([RH6_0, R23, nieto], "RECH23", {"NIETO"}) is not None          # directo: RECH23 es el padre de NIETO


def test_las_uniones_hacia_el_padre_siguen_igual():
    ruta = ruta_de_uniones(RELACIONES, "RECH6", {"RECH0", "RECH1"})
    assert [(u.hijo, u.padre, u.hacia, u.cardinalidad) for u in ruta] == [("RECH6", "RECH0", "padre", "n:1"), ("RECH6", "RECH1", "padre", "n:1")]


def test_la_cardinalidad_de_la_tabla_curada_pasa_al_plan_y_una_desconocida_se_rechaza():
    rel = relaciones_desde_yaml({"relaciones": [{"hijo": "A", "padre": "B", "por": [["X", "X"]], "cardinalidad": "1:0..1"}]})
    assert rel == [UnionPlan("A", "B", (("X", "X"),), "1:0..1")]
    for mala in ("1:n", "n:n", "uno", ""):
        with pytest.raises(PapError, match="cardinalidad"):
            relaciones_desde_yaml({"relaciones": [{"hijo": "A", "padre": "B", "por": [["X", "X"]], "cardinalidad": mala}]})


def test_el_contexto_real_declara_rech23_como_1_a_1_y_los_hermanos_de_rec0111_como_1_a_0_o_1():
    ctx = Contexto.cargar(RAIZ_REAL)
    card = {(u.hijo, u.padre): u.cardinalidad for u in ctx.relaciones[("ENDES", 2024)]}
    assert card[("RECH23", "RECH0")] == "1:1"
    for hijo in ("REC42", "RE223132", "RE516171", "RE758081"):
        assert card[(hijo, "REC0111")] == "1:0..1"
    assert card[("RECH6", "RECH0")] == "n:1" and card[("RECH1", "RECH0")] == "n:1"


def test_los_cortes_de_region_y_quintil_se_calculan_para_un_nino_por_el_padre_comun(tmp_path):
    ctx, con = _con_rech23(tmp_path)
    pc = verificar(_plan(plan_anemia(), cortes=["region_natural", "quintil_riqueza"]), ctx, con)
    assert not isinstance(pc, Falla), pc
    assert [(u.hijo, u.padre, u.hacia) for u in pc.uniones if "RECH23" in (u.hijo, u.padre)] == [("RECH23", "RECH0", "hijo")]
    assert pc.controles["uniones"].count("RECH0→RECH23") == 1 and pc.controles["filas_unidad"] == pc.controles["filas_tras_uniones"] == 6
    c = compilar(pc, ctx.esquema, ctx.carpeta_microdatos)
    df = pl.from_arrow(ejecutar_select(con, c.sql, c.parametros).arrow())
    dentro = df.filter(pl.col("u"))
    # los 4 niños de u están en h1 (2), h2 (1) y h3 (1): región 1, 1, 2 y 3; quintil 1, 1, 2 y 3
    assert sorted(dentro["corte_region_natural"].to_list()) == ["Costa", "Costa", "Costa", "Sierra"]
    assert sorted(v.removesuffix(".0") for v in dentro["corte_quintil_riqueza"].to_list()) == ["1", "1", "2", "3"]      # el ejecutor quita el «.0»


def test_una_tabla_hermana_declarada_n_a_1_no_se_alcanza_y_el_corte_falla(tmp_path):
    ctx, con = _con_rech23(tmp_path, cardinalidad="n:1")
    f = verificar(_plan(plan_anemia(), cortes=["region_natural"]), ctx, con)
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "cortes")


def test_una_tabla_declarada_1_a_1_que_repite_filas_detiene_el_plan_por_el_control_de_filas(tmp_path):
    ctx, con = _con_rech23(tmp_path, variante="repetido")
    f = verificar(_plan(plan_anemia(), cortes=["region_natural"]), ctx, con)
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "uniones") and "cambian las filas" in f.motivo


def test_comprobar_cardinalidades_contra_los_datos(tmp_path):
    ctx, con = _con_rech23(tmp_path)
    assert comprobar_cardinalidades([R23], ctx.carpeta_microdatos, "ENDES", 2024, con) == []
    ctx, con = _con_rech23(tmp_path / "r", variante="repetido")
    malos = comprobar_cardinalidades([R23], ctx.carpeta_microdatos, "ENDES", 2024, con)
    assert len(malos) == 1 and "RECH23" in malos[0] and "repite" in malos[0]
    ctx, con = _con_rech23(tmp_path / "s", variante="sin_h3")
    malos = comprobar_cardinalidades([R23], ctx.carpeta_microdatos, "ENDES", 2024, con)
    assert len(malos) == 1 and "1:1" in malos[0] and "sin pareja" in malos[0]                 # declarada 1:1 pero a RECH0 le falta un hogar
    assert comprobar_cardinalidades([replace(R23, cardinalidad="1:0..1")], ctx.carpeta_microdatos, "ENDES", 2024, con) == []
    # n:1 no se comprueba: es la dirección de siempre (hijo → padre)
    assert comprobar_cardinalidades([RH6_0], ctx.carpeta_microdatos, "ENDES", 2024, con) == []


def test_1_a_0_o_1_deja_las_filas_sin_pareja_en_sin_dato_y_cuentan_para_la_perdida_de_u(tmp_path):
    ctx, con = _con_rech23(tmp_path, variante="sin_h3", cardinalidad="1:0..1")
    # 1 de los 4 niños de u (el de h3) no tiene pareja en RECH23: 25 % > el 1 % del tope
    f = verificar(_plan(plan_anemia(), cortes=["region_natural"]), ctx, con)
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "uniones") and "sin pareja" in f.motivo
    ctx = replace(ctx, p=replace(ctx.p, union_perdida_max=0.5))
    pc = verificar(_plan(plan_anemia(), cortes=["region_natural"]), ctx, con)
    assert not isinstance(pc, Falla), pc
    assert pc.controles["u_sin_pareja"] == 1 and pc.controles["perdida_u"] == 0.25
    c = compilar(pc, ctx.esquema, ctx.carpeta_microdatos, sin_dato=ctx.p.corte_sin_dato)
    dentro = pl.from_arrow(ejecutar_select(con, c.sql, c.parametros).arrow()).filter(pl.col("u"))
    assert sorted(dentro["corte_region_natural"].to_list()) == ["Costa", "Costa", "Costa", "sin dato"] and dentro["sin_pareja"].sum() == 1


# ------------------------------------------------------------------ 1b. cortes con tramos y categorías agrupadas

def test_region_natural_agrupa_costa_y_el_corte_lleva_sus_categorias_en_palabras(tmp_path):
    ctx, con = _con_rech23(tmp_path)
    pc = verificar(_plan(plan_anemia(), cortes=["region_natural"]), ctx)
    (c,) = pc.cortes
    assert (c.archivo, c.variable) == ("RECH23", "SHREGION")
    assert c.categorias == {"Costa": "Costa", "Sierra": "Sierra", "Selva": "Selva"}      # lo que devuelve la columna del dominio
    assert [(r.rotulo, r.codigos) for r in c.reglas] == [("Costa", (1, 2)), ("Sierra", (3,)), ("Selva", (4,))]


def test_el_quintil_y_los_cortes_simples_siguen_como_codigos(tmp_path):
    ctx, _ = _con_rech23(tmp_path)
    pc = verificar(_plan(plan_anemia(), cortes=["quintil_riqueza", "area"]), ctx)
    q, a = pc.cortes
    assert q.categorias == {1: "los más pobres", 2: "pobre", 3: "medio", 4: "rico", 5: "más rico"} and q.reglas == ()
    assert a.categorias == {1: "urbano", 2: "rural"} and a.reglas == ()


def test_grupo_edad_de_anemia_usa_los_5_tramos_del_inei_y_el_de_dci_los_2(tmp_path):
    ctx, con = _con_rech23(tmp_path)
    pc = verificar(_plan(plan_anemia(), cortes=["grupo_edad"]), ctx, con)
    assert not isinstance(pc, Falla), pc
    assert list(pc.cortes[0].categorias) == ["6 a 8 meses", "9 a 11 meses", "12 a 17 meses", "18 a 23 meses", "24 a 35 meses"]
    c = compilar(pc, ctx.esquema, ctx.carpeta_microdatos, sin_dato=ctx.p.corte_sin_dato)
    df = pl.from_arrow(ejecutar_select(con, c.sql, c.parametros).arrow()).filter(pl.col("u"))
    assert sorted(df["corte_grupo_edad"].to_list()) == ["18 a 23 meses", "24 a 35 meses", "6 a 8 meses", "9 a 11 meses"]       # 20, 30, 7 y 10 meses
    pc = verificar(_plan(plan_dci(), cortes=["grupo_edad"]), ctx, con)
    assert list(pc.cortes[0].categorias) == ["Menores de 36 meses", "De 36 a 59 meses"]
    c = compilar(pc, ctx.esquema, ctx.carpeta_microdatos, sin_dato=ctx.p.corte_sin_dato)
    df = pl.from_arrow(ejecutar_select(con, c.sql, c.parametros).arrow()).filter(pl.col("u"))
    assert sorted(df["corte_grupo_edad"].to_list()) == ["De 36 a 59 meses"] + ["Menores de 36 meses"] * 3          # 10, 20, 30 y 50 meses


def test_los_dominios_de_un_corte_con_tramos_cuentan_sus_categorias_mas_sin_dato(tmp_path):
    ctx, con = _con_rech23(tmp_path)
    pc = verificar(_plan(plan_anemia(), cortes=["grupo_edad", "region_natural"]), ctx, con)
    assert pc.controles["dominios"] == 6 * 4 and ctx.p.dominios_max_llamada >= 24


def test_el_corte_con_tramos_solo_va_dentro_de_una_receta_que_tenga_juego(tmp_path):
    ctx, _ = _con_rech23(tmp_path, estado="revisado")
    compuesto = _plan(plan_anemia(), origen="compuesto", receta_id=None, universo_analitico=None, cortes=["grupo_edad"])
    f = verificar(compuesto, ctx)
    assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "cortes") and "receta" in f.motivo
    # una receta que ningún juego nombra tampoco
    otra = _plan(plan_anemia(), receta_id="endes_otra", cortes=["grupo_edad"])
    f = verificar(otra, ctx)
    assert isinstance(f, Falla) and f.dimension == "cortes" and "endes_otra" in f.motivo
    assert verificar(_plan(plan_anemia(), cortes=["grupo_edad"]), ctx).cortes[0].archivo == "RECH6"


def test_los_rotulos_nunca_entran_al_sql_como_texto(tmp_path):
    """Cadenas maliciosas en los rótulos de tramos y de categorías agrupadas: van como parámetros; el SQL no las nombra y el resultado
    las devuelve como simples valores."""
    malos = ["x') OR 1=1; DROP TABLE RECH6; --", 'a"b\\c\nd', "'; SELECT * FROM read_text('/etc/hosts') --", "Costa'", "/* x */ y"]
    ctx, con = _con_rech23(tmp_path)
    tramos = [{"rotulo": malos[0], "desde": 6, "hasta": 11}, {"rotulo": malos[1], "desde": 12, "hasta": 35}]
    corte_edad = tc.CorteEstandar.model_validate({
        "id": "grupo_edad", "nombre": "x", "cita": CITA, "por_encuesta": {"ENDES": [{
            "archivo": "RECH6", "variable": "HC1", "unidad": "nino", "cita": CITA,
            "juegos_de_tramos": [{"id": "j", "aplica_a_recetas": ["endes_anemia_6_35m"], "tramos": tramos, "cita": CITA}]}]}})
    corte_region = tc.CorteEstandar.model_validate({
        "id": "region_natural", "nombre": "x", "cita": CITA, "categorias": {1: malos[2], 2: "a", 3: "b", 4: malos[4]},
        "agrupa": {malos[3]: [2, 3]},
        "por_encuesta": {"ENDES": [{"archivo": "RECH23", "variable": "SHREGION", "unidad": "hogar", "cita": CITA}]}})
    ctx = replace(ctx, cortes=[c for c in ctx.cortes if c.id not in ("grupo_edad", "region_natural")] + [corte_edad, corte_region])
    pc = verificar(_plan(plan_anemia(), cortes=["grupo_edad", "region_natural"]), ctx, con)
    assert not isinstance(pc, Falla), pc
    c = compilar(pc, ctx.esquema, ctx.carpeta_microdatos, sin_dato=ctx.p.corte_sin_dato)
    for malo in malos:
        assert malo not in c.sql and malo in c.parametros, malo
    assert "DROP" not in c.sql and "/etc/hosts" not in c.sql and "\\" not in c.sql and "\n\n" not in c.sql
    assert c.sql.count("?") == len(c.parametros)
    df = pl.from_arrow(ejecutar_select(con, c.sql, c.parametros).arrow()).filter(pl.col("u"))
    assert set(df["corte_grupo_edad"].to_list()) <= {malos[0], malos[1]} and malos[0] in df["corte_grupo_edad"].to_list()
    assert set(df["corte_region_natural"].to_list()) == {malos[2], malos[3]}                       # h1 → 1, h2 y h3 → el grupo
    # el diccionario del plan lleva el rótulo como valor, no como identificador de columna
    assert [r.rotulo for r in pc.cortes[0].reglas] == [malos[0], malos[1]]


def test_un_tramo_fuera_de_todos_los_rangos_y_un_valor_nulo_van_a_sin_dato(tmp_path):
    ctx, con = _con_rech23(tmp_path)
    pc = verificar(_plan(plan_anemia(), cortes=["grupo_edad"]), ctx, con)
    c = compilar(pc, ctx.esquema, ctx.carpeta_microdatos, sin_dato="sin dato")
    df = pl.from_arrow(ejecutar_select(con, c.sql, c.parametros).arrow())
    assert set(df["corte_grupo_edad"].to_list()) == {"6 a 8 meses", "9 a 11 meses", "12 a 17 meses", "18 a 23 meses", "24 a 35 meses", "sin dato"}      # el de 50 meses
    con_nulo = pl.read_parquet(ctx.carpeta_microdatos / "ENDES" / "2024" / "RECH6.parquet").with_columns(
        pl.when(pl.col("HC0") == 1.0).then(None).otherwise(pl.col("HC1")).alias("HC1"))
    con_nulo.write_parquet(ctx.carpeta_microdatos / "ENDES" / "2024" / "RECH6.parquet")
    df = pl.from_arrow(ejecutar_select(con, c.sql, c.parametros).arrow())
    assert "sin dato" in df["corte_grupo_edad"].to_list()


# ------------------------------------------------------------------ 2. universo analítico según la receta o la medición

def test_la_receta_nombra_su_universo_y_el_verificador_lo_aplica_completo(tmp_path):
    ctx, con = _con_rech23(tmp_path)
    assert plan_anemia().universo_analitico == "nino_hecho_hb_medida" and plan_dci().universo_analitico == "nino_hecho"
    pc = verificar(plan_anemia(), ctx, con)
    assert pc.universo_analitico.id == "nino_hecho_hb_medida"
    pc = verificar(plan_dci(), ctx, con)
    assert pc.universo_analitico.id == "nino_hecho"


def test_un_universo_que_no_existe_o_no_es_de_la_unidad_es_falla_del_plan(tmp_path):
    ctx, _ = _con_rech23(tmp_path)
    for nombre, texto in (("nino_inventado", "no existe"), ("hijo_disciplina_con_madre", "unidad")):
        f = verificar(_plan(plan_anemia(), universo_analitico=nombre), ctx)
        assert isinstance(f, Falla) and (f.tipo, f.dimension) == ("plan", "universo") and texto in f.motivo, f


def test_un_universo_sin_la_medicion_de_las_variables_del_plan_es_falla(tmp_path):
    ctx, _ = _con_rech23(tmp_path)
    f = verificar(_plan(plan_anemia(), universo_analitico="nino_dci_0_59m"), ctx)          # hemoglobina en un universo de talla
    assert isinstance(f, Falla) and f.dimension == "universo" and "hemoglobina" in f.motivo


def test_solo_una_receta_puede_nombrar_el_universo():
    with pytest.raises(ValueError, match="universo_analitico"):
        _plan(plan_anemia(), origen="compuesto", receta_id=None)             # compuesto con universo nombrado
    p = _plan(plan_anemia(), origen="compuesto", receta_id=None, universo_analitico=None)
    assert p.universo_analitico is None


def test_el_id_del_plan_no_cambia_para_los_planes_que_no_nombran_universo():
    compuesto = _plan(plan_anemia(), origen="compuesto", receta_id=None, universo_analitico=None)
    assert "universo_analitico" not in compuesto.canonico()
    assert "universo_analitico" in plan_anemia().canonico()
    assert _plan(plan_anemia(), universo_analitico="nino_hecho").id_plan != plan_anemia().id_plan


def _compuesto(variable: str, restricciones=(), op: str = "en", valores=(1, 2, 3), **extra) -> Plan:
    base = plan_anemia()
    d = json.loads(base.model_dump_json())
    d.update(origen="compuesto", receta_id=None, universo_analitico=None, **extra)
    d["indicador"] = {"combinar": "una", "condiciones": [{"var": f"ENDES·2024·RECH6·{variable}", "op": op, "valores": list(valores)}]}
    d["universo"] = {"restricciones": list(restricciones)}
    return Plan.model_validate(d)


def test_un_plan_compuesto_con_hemoglobina_exige_nino_hecho_hb_medida(tmp_path):
    ctx, con = _con_rech23(tmp_path, variante="hb_no_medida", estado="revisado")
    restr = [{"var": "ENDES·2024·RECH6·HC1", "op": "entre", "valores": [6, 35]}, {"var": "ENDES·2024·RECH6·HC57", "op": "en", "valores": [1, 2, 3, 4]}]
    pc = verificar(_compuesto("HC57", restr), ctx, con)
    assert not isinstance(pc, Falla), pc
    assert pc.universo_analitico.id == "nino_hecho_hb_medida"
    assert pc.controles["u_despues"] == 4                                      # el niño con HC55 = 1 queda fuera
    pc = verificar(_compuesto("HC57A", restr), ctx, con)
    assert pc.universo_analitico.id == "nino_hecho_hb_medida"


def test_un_plan_compuesto_de_talla_o_sin_medicion_toma_el_universo_que_corresponde(tmp_path):
    ctx, _ = _con_rech23(tmp_path, estado="revisado")
    assert verificar(_compuesto("HC70", op="<", valores=(-200,)), ctx).universo_analitico.id == "nino_dci_0_59m"            # talla
    sin_medicion = _compuesto("HC1", op="entre", valores=(6, 35))                                                                # edad: no es una medición
    assert verificar(sin_medicion, ctx).universo_analitico.id == "nino_hecho"
    mezcla = _compuesto("HC57", [{"var": "ENDES·2024·RECH6·HC70", "op": "<", "valores": [-200]}])    # hemoglobina y talla a la vez
    assert verificar(mezcla, ctx).universo_analitico.id == "nino_hecho"


def test_sin_tabla_de_mediciones_el_plan_compuesto_cae_en_la_base_comun(tmp_path):
    ctx, _ = _con_rech23(tmp_path, estado="revisado", mediciones=[])
    assert verificar(_compuesto("HC57"), ctx).universo_analitico.id == "nino_hecho"


# ------------------------------------------------------------------ 5. HC55 = 0

def test_exigir_hc55_igual_a_0_excluye_al_nino_con_otro_resultado_de_medicion(tmp_path):
    """Prueba sintética de la nota de la historia: con HC55 ≠ 0 el niño sale de u; con el universo sin HC55 = 0 (`nino_hecho`) entra."""
    ctx, con = _con_rech23(tmp_path, variante="hb_no_medida")
    con_hc55 = verificar(plan_anemia(), ctx, con)
    sin_hc55 = verificar(_plan(plan_anemia(), universo_analitico="nino_hecho"), ctx, con)
    assert (con_hc55.controles["u_despues"], sin_hc55.controles["u_despues"]) == (4, 5)
    assert sin_hc55.universo_analitico.id == "nino_hecho" and con_hc55.universo_analitico.id == "nino_hecho_hb_medida"


def test_sin_ningun_hc55_distinto_de_cero_los_dos_universos_dan_lo_mismo(tmp_path):
    ctx, con = _con_rech23(tmp_path)
    a = verificar(plan_anemia(), ctx, con)
    b = verificar(_plan(plan_anemia(), universo_analitico="nino_hecho"), ctx, con)
    assert a.controles["u_despues"] == b.controles["u_despues"] == 4
