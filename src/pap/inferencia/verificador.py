"""Verificador base del plan (M0-07; diseño §12.1). Lo que necesitan las 3 recetas de M0; el resto del §12.1 va en M1.

`verificar(plan, ctx, con=None)` devuelve el `PlanCompleto` o una `Falla(tipo, dimension, motivo)`:
- **plan:** se descarta ese plan; **estructural:** alimenta la decisión de M1 (falta un insumo que nadie puede poner).

Qué comprueba y qué agrega, en este orden:
1. años: a lo más `anios_apilados_max_llamada`; en M0 solo uno; la medida debe estar en `medidas_disponibles`;
2. cada variable del plan existe en el índice de ese año; `en` solo con códigos que existen en las categorías; dentro de una
   receta se aceptan variables `propuesto` (§12.1: «la receta se revisa entera»), fuera de ella hace falta `revisado`; una
   variable `construida_inei` solo va en una receta; un `rol_faltante` no vacío no se resuelve en M0;
3. **agrega el universo analítico** de `universos_analiticos.yaml`: entre los de la unidad y el año, el que está contenido en
   todos los demás (la base común: población de hecho). Las restricciones del plan se suman a él;
4. **uniones:** *left join* de la unidad (el primer archivo del universo) hacia los archivos que necesitan `u`, `y`, los cortes,
   el territorio y el diseño, siguiendo solo las relaciones n:1 declaradas en `archivos_<encuesta>_<año>.yaml`;
5. **agrega el diseño** de `diseno_muestral.csv`: gana la submuestra más restrictiva que interviene en `y`, `u` o los cortes
   (medición > individual > hogar); si dos del mismo nivel traen pesos distintos, es falla;
6. **agrega el territorio** de `territorios.yaml`; un nivel que `catalogo/inferencia_verificada.csv` no verifica (o que está
   bajo el `ubigeo_minimo`) **sube al que lo contiene** (R-ENC-06; mismo orden `NIVEL_RANK` que el validador de reglas);
7. **cortes** de `cortes_estandar.yaml`, con la variable del archivo de la unidad (o de uno al que se une);
8. con una conexión: **controles de la unión** (filas de `u` antes y después —una pérdida mayor a `union_perdida_max` es
   falla—, filas de la unidad sin repetir, suma de pesos, conglomerados y estratos, nulos de `y` y del diseño dentro de `u`)
   y `dominios_max_llamada`.
"""
from __future__ import annotations

import csv
import json
from collections import deque
from dataclasses import dataclass, replace
from math import prod
from pathlib import Path
from types import SimpleNamespace
from typing import Literal

import yaml

from ..zip_seguro import RUTA_PARAMETROS
from . import tablas_curadas as tc
from .duckdb_seguro import ejecutar_select
from .gramatica import Esquema, ErrorGramatica, ARCHIVO_TERRITORIO, compilar
from .indice import ruta_curada_archivos
from .plan import Condicion, CorteResuelto, Plan, PlanCompleto, UnionPlan

RAIZ_REPO = Path(__file__).resolve().parents[3]
RANGO_SUBMUESTRA = {"medicion": 3, "individual": 2, "hogar": 1}       # §12.1: medición > entrevista individual > hogar
ESTADOS_REVISADOS = ("revisado", "verificado")
TIPOS_VALOR_COMPARABLES = ("numerica", "categorica")


@dataclass(frozen=True)
class Falla:
    tipo: Literal["plan", "estructural"]
    dimension: str
    motivo: str


@dataclass(frozen=True)
class ParametrosVerificador:
    """`verificador.*` de curados/inferencia/parametros.yaml (ningún valor fijo en el código)."""
    dominios_max_llamada: int
    anios_apilados_max_llamada: int
    union_perdida_max: float
    medidas_disponibles: tuple[str, ...]
    contencion_territorial: dict
    fuente_inferencia_verificada: dict
    corte_sin_dato: str

    @classmethod
    def desde_yaml(cls, ruta: Path = RUTA_PARAMETROS) -> "ParametrosVerificador":
        c = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))["verificador"]
        v = lambda k: c[k]["valor"]
        return cls(int(v("dominios_max_llamada")), int(v("anios_apilados_max_llamada")), float(v("union_perdida_max")),
                   tuple(v("medidas_disponibles")), dict(v("contencion_territorial")), dict(v("fuente_inferencia_verificada")),
                   str(v("corte_sin_dato")))


@dataclass(frozen=True)
class Contexto:
    """Todo lo que el verificador lee: el índice, las tablas curadas, las relaciones entre archivos y la verificación de niveles."""
    esquema: Esquema
    universos: list
    diseno: list
    territorios: list
    cortes: list
    perfil: list
    relaciones: dict[tuple[str, int], list[UnionPlan]]
    verificada: dict[tuple[str, int, str], dict]
    nivel_rank: dict[str, float]
    p: ParametrosVerificador
    carpeta_microdatos: Path

    @classmethod
    def cargar(cls, raiz: Path = RAIZ_REPO) -> "Contexto":
        raiz = Path(raiz)
        relaciones = {}
        for ruta in sorted((raiz / tc.CARPETA).glob("archivos_*_*.yaml")):
            d = yaml.safe_load(ruta.read_text(encoding="utf-8"))
            relaciones[(d["encuesta"], int(d["anio"]))] = [
                UnionPlan(r["hijo"], r["padre"], tuple((a, b) for a, b in r["por"])) for r in d["relaciones"]]
        with open(raiz / "catalogo" / "inferencia_verificada.csv", encoding="utf-8", newline="") as f:
            verificada = {(r["fuente"], int(r["anio"]), r["modulo"]): r for r in csv.DictReader(f)}
        rank = json.loads((raiz / "reglas" / "reglas.json").read_text(encoding="utf-8"))["parametros_globales"]["NIVEL_RANK"]
        return cls(Esquema.desde_parquet(raiz / "biblioteca" / "variables"), tc.leer_universos(raiz), tc.leer_diseno_muestral(raiz),
                   tc.leer_territorios(raiz), tc.leer_cortes(raiz), tc.leer_perfil_anual(raiz), relaciones, verificada,
                   {k: v for k, v in rank.items() if isinstance(v, (int, float))}, ParametrosVerificador.desde_yaml(),
                   raiz / "biblioteca" / "microdatos")


# ------------------------------------------------------------------ variables y categorías

def _codigos(ctx: Contexto, var_id: str) -> set[float]:
    out = set()
    for k in ctx.esquema.categorias.get(var_id, {}):
        try:
            out.add(float(k))
        except ValueError:
            pass
    return out


def _condiciones(plan: Plan) -> list[Condicion]:
    return [*plan.indicador.condiciones, *plan.universo.restricciones]


def _revisar_variables(ctx: Contexto, plan: Plan) -> Falla | None:
    anio = plan.anios[0]
    for c in _condiciones(plan):
        v = ctx.esquema.variables.get(c.var)
        if v is None:
            return Falla("plan", "variable", f"{c.var} no está en el índice")
        if (v["encuesta"], int(v["anio"])) != (plan.encuesta, anio):
            return Falla("estructural", "anio", f"{c.var} no es de {plan.encuesta} {anio}")
        if plan.origen != "receta":
            if v["estado"] not in ESTADOS_REVISADOS:
                return Falla("plan", "variable", f"{c.var} está «{v['estado']}»: fuera de una receta hace falta «revisado»")
            if v.get("tipo_origen") == "construida_inei":
                return Falla("plan", "variable", f"{c.var} es construida_inei: solo se usa dentro de una receta")
        if any(k["rol_faltante"] for k in ctx.esquema.categorias.get(c.var, {}).values()) or v.get("rol_faltante"):
            return Falla("plan", "rol_faltante", f"{c.var} declara rol_faltante: M0 no lo resuelve")
        if c.op == "en":
            existen = _codigos(ctx, c.var)
            malos = [x for x in c.valores if float(x) not in existen]
            if malos:
                return Falla("plan", "valores", f"{c.var}: los códigos {malos} no existen en sus categorías")
        elif c.op in ("entre", "<", "≥") and v["tipo_valor"] not in TIPOS_VALOR_COMPARABLES:
            return Falla("plan", "valores", f"{c.var} es de tipo «{v['tipo_valor']}»: no admite «{c.op}»")
    return None


# ------------------------------------------------------------------ universo, uniones, diseño, territorio, cortes

def _universo_analitico(ctx: Contexto, plan: Plan):
    anio = plan.anios[0]
    cand = [u for u in ctx.universos if u.encuesta == plan.encuesta and u.unidad == plan.unidad and u.anios[0] <= anio <= u.anios[1]]
    if not cand:
        return Falla("plan", "universo", f"no hay universo analítico de {plan.encuesta} {anio} para la unidad «{plan.unidad}»")
    conjuntos = [frozenset((p.var, p.op, tuple(p.valores)) for p in u.predicados) for u in cand]
    for u, s in zip(cand, conjuntos):
        if all(s <= o for o in conjuntos):
            return u
    return Falla("plan", "universo", f"los universos de la unidad «{plan.unidad}» no tienen una base común: {[u.id for u in cand]}")


def _archivo_de(ctx: Contexto, plan: Plan, nombre: str, archivos: list[str]) -> str | None:
    return next((a for a in archivos if ctx.esquema.tiene(plan.encuesta, plan.anios[0], a, nombre)), None)


def ruta_de_uniones(relaciones: list[UnionPlan], origen: str, destinos: set[str]) -> tuple[UnionPlan, ...] | None:
    """Uniones izquierdas (hijo → padre, n:1) que llevan de `origen` a cada destino, padre antes que dependientes. None si alguno no se alcanza."""
    padres: dict[str, list[UnionPlan]] = {}
    for r in relaciones:
        padres.setdefault(r.hijo, []).append(r)
    llegada: dict[str, UnionPlan | None] = {origen: None}
    cola = deque([origen])
    while cola:
        a = cola.popleft()
        for r in padres.get(a, []):
            if r.padre not in llegada:
                llegada[r.padre] = r
                cola.append(r.padre)
    salida: list[UnionPlan] = []
    for d in sorted(destinos):
        if d not in llegada:
            return None
        cadena = []
        while llegada[d] is not None:
            cadena.append(llegada[d])
            d = llegada[d].hijo
        for r in reversed(cadena):
            if r not in salida:
                salida.append(r)
    return tuple(salida)


def _elegir_diseno(ctx: Contexto, plan: Plan, intervienen: set[str]):
    anio = plan.anios[0]
    filas = [f for f in ctx.diseno if f.encuesta == plan.encuesta and f.anio == anio and f.archivo in intervienen]
    if not filas:
        return Falla("plan", "diseno", f"diseno_muestral.csv no tiene fila de {plan.encuesta} {anio} para {sorted(intervienen)}")
    mayor = max(RANGO_SUBMUESTRA[f.nivel_submuestra] for f in filas)
    ganadoras = [f for f in filas if RANGO_SUBMUESTRA[f.nivel_submuestra] == mayor]
    if len({(f.peso_expr, f.estrato_expr, f.psu_expr) for f in ganadoras}) > 1:
        return Falla("plan", "peso", f"submuestras del mismo nivel con pesos distintos: {sorted({f.archivo for f in ganadoras})}")
    return ganadoras[0]


def _nivel_publicable(ctx: Contexto, plan: Plan, archivo_unidad: str):
    """R-ENC-06: devuelve (nivel, id, aviso). Un nivel no verificado sube al que lo contiene, hasta el nacional."""
    from ..motor.validador.reglas_etapa4 import nivel_superior       # el mismo «nivel que lo contiene» del validador de reglas

    anio, nivel, id_ = plan.anios[0], plan.territorio.nivel, plan.territorio.id
    fuente = ctx.p.fuente_inferencia_verificada.get(plan.encuesta, plan.encuesta)
    fila = ctx.verificada.get((fuente, anio, archivo_unidad)) or ctx.verificada.get((fuente, anio, "*"))
    perfil = next((f for f in ctx.perfil if f.encuesta == plan.encuesta and f.anio == anio), None)
    rank = ctx.nivel_rank.get
    ambitos = set(filter(None, (fila or {}).get("ambitos_publicados", "").split(";")))
    sombra = SimpleNamespace(nivel_rank=rank)

    def verificado(n: str) -> bool:
        if n == "nacional":
            return True
        if perfil is not None and rank(n) is not None and rank(perfil.ubigeo_minimo) is not None and rank(n) < rank(perfil.ubigeo_minimo):
            return False
        if not fila or fila.get("inferencia_verificada", "").lower() != "true":
            return False
        return n in ambitos or (rank(n) is not None and rank(fila["nivel_maximo"]) is not None and rank(n) >= rank(fila["nivel_maximo"]))

    original, cambios = nivel, []
    while not verificado(nivel):
        cont = ctx.p.contencion_territorial.get(nivel)
        if cont:
            nivel, id_ = cont["nivel"], cont["id"]
        else:
            nivel, id_ = nivel_superior(SimpleNamespace(nivel=nivel), sombra) or "nacional", None
        cambios.append(nivel)
    if cambios:
        return nivel, id_ if nivel != "nacional" else None, (
            f"el nivel {original} no está verificado en inferencia_verificada para {plan.encuesta} {anio}: sube a {nivel} (R-ENC-06)")
    return nivel, id_, None


def _resolver_cortes(ctx: Contexto, plan: Plan, archivo_unidad: str, relaciones: list[UnionPlan]):
    por_id = {c.id: c for c in ctx.cortes}
    out = []
    for cid in plan.cortes:
        c = por_id.get(cid)
        if c is None:
            return Falla("plan", "cortes", f"el corte «{cid}» no está en cortes_estandar.yaml")
        opciones = c.por_encuesta.get(plan.encuesta, [])
        elegida = next((o for o in opciones if o.archivo == archivo_unidad), None) or next(
            (o for o in opciones if ruta_de_uniones(relaciones, archivo_unidad, {o.archivo}) is not None), None)
        if elegida is None:
            return Falla("plan", "cortes", f"el corte «{cid}» no tiene variable en un archivo al que se una {archivo_unidad}")
        if elegida.pendiente:
            return Falla("plan", "cortes", f"el corte «{cid}» tiene sus categorías pendientes ({elegida.pendiente})")
        cats = elegida.categorias or c.categorias or {}
        if not ctx.esquema.tiene(plan.encuesta, plan.anios[0], elegida.archivo, elegida.variable):
            return Falla("plan", "cortes", f"{elegida.archivo}.{elegida.variable} no está en el índice")
        out.append(CorteResuelto(cid, elegida.archivo, elegida.variable, dict(cats)))
    return tuple(out)


# ------------------------------------------------------------------ verificación

def verificar(plan: Plan, ctx: Contexto, con=None) -> PlanCompleto | Falla:
    p, anio = ctx.p, plan.anios[0]
    if len(plan.anios) > p.anios_apilados_max_llamada:
        return Falla("plan", "anios", f"{len(plan.anios)} años en una llamada; el máximo es {p.anios_apilados_max_llamada}")
    if len(plan.anios) > 1:
        return Falla("estructural", "anio", "apilar años no está en M0 (M2)")
    if plan.medida not in p.medidas_disponibles:
        return Falla("estructural", "medida_no_disponible", f"la medida «{plan.medida}» no existe en esta fase (solo {list(p.medidas_disponibles)})")
    if (plan.encuesta, anio) not in ctx.relaciones:
        return Falla("estructural", "anio", f"no hay índice ni relaciones de {plan.encuesta} {anio}")
    if (f := _revisar_variables(ctx, plan)) is not None:
        return f

    ua = _universo_analitico(ctx, plan)
    if isinstance(ua, Falla):
        return ua
    relaciones = ctx.relaciones[(plan.encuesta, anio)]
    archivo_unidad = ua.aplica_a.archivos[0]
    if (plan.encuesta, anio, archivo_unidad) not in ctx.esquema.archivos:
        return Falla("estructural", "anio", f"{archivo_unidad} no está en el índice de {plan.encuesta} {anio}")

    # archivos que necesitan u e y, y los cortes
    archivos_u_y = {archivo_unidad}
    for pr in ua.predicados:
        a = _archivo_de(ctx, plan, pr.var, ua.aplica_a.archivos)
        if a is None:
            return Falla("plan", "universo", f"{pr.var} del universo {ua.id} no está en {ua.aplica_a.archivos}")
        archivos_u_y.add(a)
    archivos_u_y |= {ctx.esquema.variables[c.var]["archivo"] for c in _condiciones(plan)}
    uniones_u_y = ruta_de_uniones(relaciones, archivo_unidad, archivos_u_y)
    if uniones_u_y is None:
        return Falla("plan", "uniones", f"no hay unión declarada de {archivo_unidad} hacia {sorted(archivos_u_y)}")
    cortes = _resolver_cortes(ctx, plan, archivo_unidad, relaciones)
    if isinstance(cortes, Falla):
        return cortes

    diseno = _elegir_diseno(ctx, plan, archivos_u_y | {c.archivo for c in cortes})
    if isinstance(diseno, Falla):
        return diseno
    nivel, id_, aviso = _nivel_publicable(ctx, plan, archivo_unidad)
    ajustes = (aviso,) if aviso else ()
    if aviso:
        plan = plan.model_copy(update={"territorio": plan.territorio.model_copy(update={"nivel": nivel, "id": id_})})
    terr = next((t for t in ctx.territorios if t.encuesta == plan.encuesta and t.nivel == nivel and t.anios[0] <= anio <= t.anios[1]), None)
    if terr is None:
        return Falla("plan", "territorio", f"territorios.yaml no tiene el nivel {nivel} de {plan.encuesta} {anio}")
    falta = [c for c in terr.columnas if not ctx.esquema.tiene(plan.encuesta, anio, ARCHIVO_TERRITORIO, c)]
    if falta:
        return Falla("plan", "territorio", f"{ARCHIVO_TERRITORIO} no tiene las columnas {falta} en el índice")

    destinos = archivos_u_y | {c.archivo for c in cortes} | {ARCHIVO_TERRITORIO, diseno.archivo} | {pa for _, _, pa, _ in diseno.uniones}
    uniones = ruta_de_uniones(relaciones, archivo_unidad, destinos)
    if uniones is None:
        return Falla("plan", "uniones", f"no hay unión declarada de {archivo_unidad} hacia {sorted(destinos)}")

    pc = PlanCompleto(plan, ua, diseno, terr, archivo_unidad, uniones, uniones_u_y, cortes, ajustes)
    if con is None:
        return pc if plan.territorio.id is None else _con_dominios(ctx, pc, None)
    try:
        return _controles(ctx, pc, con)
    except ErrorGramatica as e:
        return Falla("plan", "gramatica", str(e))


def _celdas_de_cortes(pc: PlanCompleto) -> int:
    return prod(len(c.categorias) + 1 for c in pc.cortes)                # +1: la categoría «sin dato»


def _con_dominios(ctx: Contexto, pc: PlanCompleto, n_unidades: int | None):
    n = 1 if pc.plan.territorio.id is not None else n_unidades
    if n is None:
        return pc
    dominios = n * _celdas_de_cortes(pc)
    if dominios > ctx.p.dominios_max_llamada:
        return Falla("plan", "dominios", f"{dominios} dominios; el máximo por llamada es {ctx.p.dominios_max_llamada} (se parte el cálculo, §14)")
    return pc if pc.controles is not None else replace(pc, controles={"dominios": dominios})


def _controles(ctx: Contexto, pc: PlanCompleto, con) -> PlanCompleto | Falla:
    plan, anio = pc.plan, pc.plan.anios[0]
    ruta_unidad = str(ctx.carpeta_microdatos / plan.encuesta / str(anio) / f"{pc.archivo_unidad}.parquet")
    filas_unidad = ejecutar_select(con, "SELECT count(*) FROM read_parquet(?)", [ruta_unidad]).fetchone()[0]
    antes = compilar(pc, ctx.esquema, ctx.carpeta_microdatos, solo_u_y=True, sin_dato=ctx.p.corte_sin_dato)
    n_antes = ejecutar_select(con, f"SELECT count(*) FILTER (WHERE u) FROM ({antes.sql})", antes.parametros).fetchone()[0]
    d = compilar(pc, ctx.esquema, ctx.carpeta_microdatos, sin_dato=ctx.p.corte_sin_dato)
    r = ejecutar_select(
        con, "SELECT count(*), count(*) FILTER (WHERE u), sum(peso) FILTER (WHERE u), count(DISTINCT upm) FILTER (WHERE u), "
        "count(DISTINCT estrato) FILTER (WHERE u), count(*) FILTER (WHERE u AND y IS NULL), "
        "count(*) FILTER (WHERE u AND (peso IS NULL OR estrato IS NULL OR upm IS NULL)), "
        f"count(DISTINCT territorio) FILTER (WHERE u) FROM ({d.sql})", d.parametros).fetchone()
    filas_union, n_despues, suma_pesos, n_upm, n_estratos, y_nulos, diseno_nulos, n_unidades = r
    c = {"filas_unidad": filas_unidad, "filas_tras_uniones": filas_union, "u_antes": n_antes, "u_despues": n_despues,
         "suma_pesos_u": float(suma_pesos) if suma_pesos is not None else None, "conglomerados_u": n_upm, "estratos_u": n_estratos,
         "y_nulos_en_u": y_nulos, "diseno_nulo_en_u": diseno_nulos, "unidades_territorio": n_unidades,
         "uniones": [f"{u.hijo}→{u.padre}" for u in pc.uniones]}
    if filas_union != filas_unidad:
        return Falla("plan", "uniones", f"las uniones cambian las filas de {pc.archivo_unidad}: {filas_unidad} → {filas_union}")
    if n_antes == 0:
        return Falla("plan", "universo", "u queda vacío")
    perdida = (n_antes - n_despues) / n_antes
    c["perdida_u"] = perdida
    if perdida > ctx.p.union_perdida_max:
        return Falla("plan", "uniones", f"las uniones pierden {perdida:.2%} de las filas de u (máximo {ctx.p.union_perdida_max:.2%})")
    if y_nulos:
        return Falla("plan", "y", f"{y_nulos} filas de u con y nulo (un nulo dentro de u es un error)")
    if diseno_nulos:
        return Falla("plan", "diseno", f"{diseno_nulos} filas de u sin peso, estrato o conglomerado")
    c["dominios"] = (1 if plan.territorio.id is not None else n_unidades) * _celdas_de_cortes(pc)
    out = _con_dominios(ctx, replace(pc, controles=c), n_unidades)
    return replace(out, controles=c | {"dominios": c["dominios"]}) if isinstance(out, PlanCompleto) else out
