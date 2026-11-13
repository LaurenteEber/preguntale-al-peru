"""M0-07: modelos del plan, gramática y su compilación a SQL con parámetros. Sin datos reales (los Parquet son sintéticos)."""
import hashlib
import json
import re
from dataclasses import replace

import pytest
from pydantic import ValidationError

from conftest import RAIZ_REAL
from pap.inferencia.gramatica import ErrorGramatica, calificar_expresion, citar, compilar
from pap.inferencia.plan import Condicion, Indicador, Plan, Territorio, niveles_territorio
from pap.inferencia.tablas_curadas import leer_territorios
from pap.inferencia.verificador import Falla, verificar

from .recetas_m0 import NIVELES, plan_anemia, plan_anemia_oms2024, plan_dci
from .sintetico_m0 import contexto_sintetico

V = "ENDES·2024·RECH6·HC57"


def plan_json(**cambios) -> dict:
    base = json.loads(plan_anemia().model_dump_json())
    base.update(cambios)
    return base


# ------------------------------------------------------------------ modelos del plan

def test_el_plan_valido_pasa_y_los_modelos_no_aceptan_campos_extra():
    assert plan_anemia().encuesta == "ENDES"
    with pytest.raises(ValidationError):
        Plan.model_validate(plan_json(sql="SELECT 1"))
    with pytest.raises(ValidationError):
        Condicion.model_validate({"var": V, "op": "en", "valores": [1], "extra": 1})
    with pytest.raises(ValidationError):
        Territorio.model_validate({"nivel": "nacional", "ubigeo": "15"})


def test_el_nivel_del_territorio_sale_de_territorios_yaml():
    assert set(niveles_territorio()) == {t.nivel for t in leer_territorios(RAIZ_REAL)} == set(NIVELES)
    with pytest.raises(ValidationError):
        Territorio(nivel="distrito")


@pytest.mark.parametrize("cond", [
    {"var": V, "op": "en", "valores": []}, {"var": V, "op": "entre", "valores": [5]},
    {"var": V, "op": "entre", "valores": [9, 5]}, {"var": V, "op": "<", "valores": [1, 2]},
    {"var": V, "op": "≥", "valores": []}, {"var": V, "op": "es_nulo", "valores": [1]},
    {"var": V, "op": "no_es_nulo", "valores": [1]}, {"var": V, "op": "=", "valores": [1]},
    {"var": V, "op": "LIKE", "valores": [1]}, {"var": "HC57", "op": "en", "valores": [1]},
    {"var": V, "op": "en", "valores": [float("nan")]}, {"var": V, "op": "en", "valores": [True]},
])
def test_condiciones_invalidas(cond):
    with pytest.raises(ValidationError):
        Condicion.model_validate(cond)


@pytest.mark.parametrize("op,valores", [("en", [1, 2]), ("entre", [1, 4]), ("<", [-200]), ("≥", [3.5]), ("es_nulo", []), ("no_es_nulo", [])])
def test_los_seis_operadores_validos(op, valores):
    assert Condicion(var=V, op=op, valores=valores).op == op


def test_combinacion_con_un_maximo_de_tres_condiciones():
    c = lambda n: [{"var": V, "op": "en", "valores": [i + 1]} for i in range(n)]
    for comb in ("alguna_de", "todas_de"):
        assert len(Indicador.model_validate({"combinar": comb, "condiciones": c(3)}).condiciones) == 3
        with pytest.raises(ValidationError):
            Indicador.model_validate({"combinar": comb, "condiciones": c(4)})
    with pytest.raises(ValidationError):
        Indicador.model_validate({"combinar": "una", "condiciones": c(2)})
    with pytest.raises(ValidationError):
        Indicador.model_validate({"combinar": "ninguna", "condiciones": c(1)})
    with pytest.raises(ValidationError):
        Indicador.model_validate({"combinar": "alguna_de", "condiciones": []})


def test_receta_id_va_solo_con_el_origen_receta():
    with pytest.raises(ValidationError):
        Plan.model_validate(plan_json(receta_id=None))
    with pytest.raises(ValidationError):
        Plan.model_validate(plan_json(origen="compuesto"))
    assert Plan.model_validate(plan_json(origen="compuesto", receta_id=None, universo_analitico=None)).receta_id is None


def test_id_plan_es_el_sha256_del_json_canonico():
    p = plan_anemia()
    canonico = json.dumps(json.loads(p.model_dump_json()), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert p.canonico() == canonico and ", " not in canonico and ": " not in canonico
    assert p.id_plan == hashlib.sha256(canonico.encode("utf-8")).hexdigest()
    # el orden de las claves de entrada no cambia el id; 6 y 6.0 son lo mismo; otro valor cambia el id
    desordenado = json.loads(json.dumps(plan_json(), sort_keys=True))
    assert Plan.model_validate(desordenado).id_plan == p.id_plan
    d = plan_json()
    d["universo"]["restricciones"][0]["valores"] = [6.0, 35.0]
    assert Plan.model_validate(d).id_plan == p.id_plan
    d["universo"]["restricciones"][0]["valores"] = [7, 35]
    assert Plan.model_validate(d).id_plan != p.id_plan


# ------------------------------------------------------------------ cadenas maliciosas en cada campo

MALICIOSAS = ["x' UNION SELECT 1 --", "read_text('/etc/hosts')", "COPY t TO '/tmp/x'", "a; DROP TABLE t", 'a"b', "a'b", "1 OR 1=1"]


def _con_campo(ruta: tuple, valor) -> dict:
    d = plan_json()
    o = d
    for k in ruta[:-1]:
        o = o[k]
    o[ruta[-1]] = valor
    return d


CAMPOS_TEXTO = [("encuesta",), ("anios", 0), ("unidad",), ("medida",), ("receta_id",), ("origen",), ("territorio", "nivel"),
                ("territorio", "id"), ("cortes", 0), ("indicador", "combinar"), ("indicador", "condiciones", 0, "var"),
                ("indicador", "condiciones", 0, "op"), ("indicador", "condiciones", 0, "valores", 0),
                ("universo", "restricciones", 0, "var"), ("universo", "restricciones", 0, "op"),
                ("universo", "restricciones", 0, "valores", 0)]


@pytest.mark.parametrize("mala", MALICIOSAS)
@pytest.mark.parametrize("ruta", CAMPOS_TEXTO, ids=lambda r: ".".join(map(str, r)))
def test_una_cadena_maliciosa_en_cualquier_campo_del_plan_se_rechaza(ruta, mala):
    d = plan_json(cortes=["area"])
    if ruta[0] == "cortes":
        d["cortes"] = ["area"]
    o = d
    for k in ruta[:-1]:
        o = o[k]
    o[ruta[-1]] = mala
    with pytest.raises(ValidationError):
        Plan.model_validate(d)


def test_un_var_id_con_forma_valida_pero_fuera_del_indice_queda_inerte(tmp_path):
    """La forma del var_id solo deja letras, dígitos y «_»; si no está en el índice, el verificador lo descarta y no se compila nada."""
    ctx, _ = contexto_sintetico(tmp_path)
    for nombre in ("UNION_SELECT", "read_text", "COPY_t", "OR_1_1"):
        d = plan_json()
        d["indicador"]["condiciones"][0]["var"] = f"ENDES·2024·RECH6·{nombre}"
        r = verificar(Plan.model_validate(d), ctx)
        assert isinstance(r, Falla) and r.dimension == "variable"


# ------------------------------------------------------------------ expresiones curadas

def _resolver(nombre):
    if nombre not in {"HV024", "HV022", "HV005", "UBIGEO"}:
        raise ErrorGramatica(f"{nombre} no está en el índice")
    return f'"RECH0"."{nombre}"'


def test_expresion_curada_con_texto_pasa_a_parametros():
    par = []
    sql = calificar_expresion("printf('%02d-%d', HV024, HV022)", _resolver, lambda v: par.append(v) or "?")
    assert sql == 'printf(?, "RECH0"."HV024", "RECH0"."HV022")' and par == ["%02d-%d"]
    par.clear()
    sql = calificar_expresion("HV005/1e6", _resolver, lambda v: par.append(v) or "?")
    assert sql == '"RECH0"."HV005"/1e6' and par == []
    par.clear()
    sql = calificar_expresion("CASE HV025 WHEN 1 THEN 'urbano' END", lambda n: f'"RECH0"."{n}"', lambda v: par.append(v) or "?")
    assert sql == 'CASE "RECH0"."HV025" WHEN 1 THEN ? END' and par == ["urbano"]


@pytest.mark.parametrize("expr", ["read_text('/etc/hosts')", "HV024; DROP TABLE x", "HV024 -- c", "(SELECT 1)", "HV024 UNION SELECT 1",
                                  "HV999", 'HV024"', "HV024 || 'x'", "system('ls')", "HV024 /* x */"])
def test_expresion_curada_maliciosa_se_rechaza(expr):
    with pytest.raises(ErrorGramatica):
        calificar_expresion(expr, _resolver, lambda v: "?")


def test_un_texto_entre_comillas_con_sql_dentro_es_solo_un_valor():
    par = []
    sql = calificar_expresion("HV024 = '1; DROP TABLE x; --'", _resolver, lambda v: par.append(v) or "?")
    assert sql == '"RECH0"."HV024" = ?' and par == ["1; DROP TABLE x; --"]


def test_citar_solo_acepta_nombres_simples():
    assert citar("HC57") == '"HC57"'
    for malo in ('a"b', "a b", "a;b", "a'b", "", "x" * 65):
        with pytest.raises(ErrorGramatica):
            citar(malo)


# ------------------------------------------------------------------ compilación

@pytest.fixture(scope="module")
def ctx_sint(tmp_path_factory):
    return contexto_sintetico(tmp_path_factory.mktemp("sint"))


def _completo(ctx, plan):
    pc = verificar(plan, ctx)
    assert not isinstance(pc, Falla), pc
    return pc


def _plan_con_indicador(base: Plan, ind: dict) -> Plan:
    return Plan.model_validate({**json.loads(base.model_dump_json()), "indicador": ind})


@pytest.mark.parametrize("cond,sql,params", [
    ({"op": "en", "valores": [1, 2]}, '"RECH6"."HC57" IN (?, ?)', [1, 2]),
    ({"op": "entre", "valores": [1, 3]}, '"RECH6"."HC57" BETWEEN ? AND ?', [1, 3]),
    ({"op": "<", "valores": [-200]}, '"RECH6"."HC57" < ?', [-200]),
    ({"op": "≥", "valores": [3]}, '"RECH6"."HC57" >= ?', [3]),
    ({"op": "es_nulo", "valores": []}, '"RECH6"."HC57" IS NULL', []),
    ({"op": "no_es_nulo", "valores": []}, '"RECH6"."HC57" IS NOT NULL', []),
])
def test_cada_operador_compila_con_parametros(ctx_sint, cond, sql, params):
    ctx, _ = ctx_sint
    pc = _completo(ctx, plan_anemia())
    plan = _plan_con_indicador(pc.plan, {"combinar": "una", "condiciones": [{"var": V, **cond}]})
    c = compilar(replace(pc, plan=plan), ctx.esquema, ctx.carpeta_microdatos)
    ind = re.search(r"\n  (.*) AS ind", c.sql).group(1)
    assert ind == sql
    assert c.sql.count("?") == len(c.parametros)
    assert all(str(p) not in c.sql for p in params if len(str(p)) > 1)         # el valor no está en el texto: va como parámetro


def test_alguna_de_y_todas_de_unen_con_or_y_and(ctx_sint):
    ctx, _ = ctx_sint
    pc = _completo(ctx, plan_anemia())
    conds = [{"var": V, "op": "en", "valores": [1]}, {"var": "ENDES·2024·RECH6·HC57A", "op": "en", "valores": [2]}]
    for comb, unir in (("alguna_de", " OR "), ("todas_de", " AND ")):
        plan = _plan_con_indicador(pc.plan, {"combinar": comb, "condiciones": conds})
        c = compilar(replace(pc, plan=plan), ctx.esquema, ctx.carpeta_microdatos)
        assert f'(("RECH6"."HC57" IN (?)){unir}("RECH6"."HC57A" IN (?))) AS ind' in c.sql


def test_el_sql_solo_usa_nombres_del_indice_y_los_valores_van_como_parametros(ctx_sint):
    ctx, _ = ctx_sint
    nombres_indice = {a for (_, _, a) in ctx.esquema.archivos} | {v for cols in ctx.esquema.columnas.values() for v in cols}
    for plan in (plan_anemia("departamento", cortes=("area",)), plan_anemia_oms2024("LIMA_REGION"), plan_dci("dominio_subnacional")):
        pc = _completo(ctx, plan)
        c = compilar(pc, ctx.esquema, ctx.carpeta_microdatos)
        citados = set(re.findall(r'"([^"]*)"', c.sql))
        assert citados <= nombres_indice | {"corte_area"}, citados - nombres_indice
        assert {a for a, _ in c.identificadores} <= {a for (_, _, a) in ctx.esquema.archivos}
        assert all(col in ctx.esquema.columnas[("ENDES", 2024, a)] for a, col in c.identificadores)
        assert "'" not in c.sql and ";" not in c.sql and "--" not in c.sql                 # ningún texto literal
        assert c.sql.count("?") == len(c.parametros)
        # los únicos números escritos en el SQL son los de las expresiones curadas (territorio y diseño), nunca los del plan
        sin_ident = re.sub(r'"[^"]*"', "", c.sql)
        escritos = set(re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?:e\d+)?(?![\w.])", sin_ident))
        curados = set(re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?:e\d+)?(?![\w.])", " ".join([pc.territorio.expr, pc.territorio.unidad_expr, pc.diseno.peso_expr])))
        assert escritos <= curados, escritos - curados


def test_u_e_y_con_rol_faltante_vacio(ctx_sint):
    """y es nulo solo fuera de u; dentro de u vale 0 o 1. HC57 = 4 (sin anemia) cuenta 0; 9 queda fuera del universo."""
    ctx, _ = ctx_sint
    from pap.inferencia.duckdb_seguro import conexion_segura

    c = compilar(_completo(ctx, plan_anemia()), ctx.esquema, ctx.carpeta_microdatos)
    con = conexion_segura(carpetas=[ctx.carpeta_microdatos])
    filas = con.execute(c.sql, c.parametros).fetchall()
    cols = [d[0] for d in con.description] if con.description else None
    assert cols == ["u", "y", "territorio", "peso", "estrato", "upm"]
    en_u = [f for f in filas if f[0]]
    assert en_u and all(f[1] in (0, 1) for f in en_u)
    assert all(f[1] is None for f in filas if not f[0])
    assert {f[1] for f in en_u} == {0, 1}


def test_el_territorio_con_id_filtra_la_unidad(ctx_sint):
    ctx, _ = ctx_sint
    from pap.inferencia.duckdb_seguro import conexion_segura

    con = conexion_segura(carpetas=[ctx.carpeta_microdatos])
    c = compilar(_completo(ctx, plan_anemia("departamento", "15")), ctx.esquema, ctx.carpeta_microdatos)
    assert {f[2] for f in con.execute(c.sql, c.parametros).fetchall()} <= {"15", None}
    assert "15" in c.parametros


@pytest.mark.parametrize("expr", ["HV024 -- resto", "HV024 /* x */ + 1", "HV024 + 1 --", "1 /*"])
def test_calificar_expresion_rechaza_comentarios_sql(expr):
    """H07-2: `--` y `/*` no son parte de la gramática (los tokens `-` y `/` sueltos sí)."""
    with pytest.raises(ErrorGramatica, match="comentario"):
        calificar_expresion(expr, _resolver, lambda v: "?")


def test_calificar_expresion_admite_guiones_y_barras_sueltos_y_comentarios_dentro_de_un_texto():
    par = []
    assert calificar_expresion("HV005/1e6", _resolver, lambda v: par.append(v) or "?").endswith("/1e6")
    assert calificar_expresion("HV024 - 1", _resolver, lambda v: "?").endswith("- 1")
    assert calificar_expresion("HV024 = 'a -- b /* c'", _resolver, lambda v: par.append(v) or "?").endswith("= ?")
    assert par[-1] == "a -- b /* c"
