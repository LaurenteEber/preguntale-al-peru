"""Verificador base del plan (M0-07; diseño §12.1). Lo que necesitan las 3 recetas de M0; el resto del §12.1 va en M1.

`verificar(plan, ctx, con=None)` devuelve el `PlanCompleto` o una `Falla(tipo, dimension, motivo)`:
- **plan:** se descarta ese plan; **estructural:** alimenta la decisión de M1 (falta un insumo que nadie puede poner).

Qué comprueba y qué agrega, en este orden:
1. años: a lo más `anios_apilados_max_llamada`; en M0 solo uno; la medida debe estar en `medidas_disponibles`;
2. cada variable del plan existe en el índice de ese año; `en` solo con códigos que existen en las categorías; dentro de una
   receta se aceptan variables `propuesto` (§12.1: «la receta se revisa entera»), fuera de ella hace falta `revisado`; una
   variable `construida_inei` solo va en una receta; un `rol_faltante` no vacío no se resuelve en M0;
3. **agrega el universo analítico** de `universos_analiticos.yaml` (M1-03): si el plan es de una receta, el que ella nombra
   (`universo_analitico`), aplicado completo (si no existe, no es de la unidad, no cubre la tabla o no cubre la medición de sus variables,
   es falla del plan). **Por la tabla que interviene** (M1-07, `unidades.yaml`): solo cuentan los universos cuyos `aplica_a.archivos`
   incluyen las tablas del plan que son de la unidad, y el plan parte de su **tabla base** (no del primer archivo del universo);
   si es compuesto, según la **medición** de las variables que intervienen (`mediciones.yaml`): entre los universos de la unidad y el año
   cuyas `aplica_a.mediciones` cubren a todas, los de menos mediciones, y de ellos el contenido en todos los demás (hemoglobina →
   `nino_hecho_hb_medida`). Sin ninguna medición, la base común (población de hecho). Las restricciones del plan se suman a él;
4. **uniones:** *left join* de la unidad (el primer archivo del universo) hacia los archivos que necesitan `u`, `y`, los cortes,
   el territorio y el diseño, siguiendo las relaciones n:1 declaradas en `archivos_<encuesta>_<año>.yaml` hacia el padre y, desde el
   padre común, hacia un hermano que sea 1:1 o 1:0..1 con él (M1-03: región natural y quintil de un niño, que cuelgan de RECH23);
5. **agrega el diseño** de `diseno_muestral.csv`: gana la submuestra más restrictiva que interviene en `y`, `u` o los cortes
   (medición > individual > hogar; niño × madre × hogar, M1-07); si dos del mismo nivel traen pesos distintos, es falla;
6. **agrega el territorio** de `territorios.yaml`; un nivel que `catalogo/inferencia_verificada.csv` no verifica (o que está
   bajo el `ubigeo_minimo`) **sube al que lo contiene** (R-ENC-06; mismo orden `NIVEL_RANK` que el validador de reglas);
7. **cortes** de `cortes_estandar.yaml`, con la variable del archivo de la unidad (o de uno al que se une) y solo si describe a la
   unidad del plan o al hogar (`tablas_curadas.corte_aplica`: el grupo de edad de la madre no es el del hijo);
8. con una conexión: **controles de la unión** (filas de `u` antes y después —una pérdida mayor a `union_perdida_max` es
   falla—, filas de la unidad sin repetir, suma de pesos, conglomerados y estratos, nulos de `y` y del diseño dentro de `u`;
   las filas de `u` sin pareja en un hermano 1:0..1 cuentan como pérdida) y `dominios_max_llamada`.
"""
from __future__ import annotations

import csv
import json
from collections import deque
from dataclasses import dataclass, field, replace
from math import prod
from pathlib import Path
from types import SimpleNamespace
from typing import Literal

import yaml

from ..errores import PapError
from ..zip_seguro import RUTA_PARAMETROS
from . import tablas_curadas as tc
from .duckdb_seguro import ejecutar_select
from .gramatica import Esquema, ErrorGramatica, ARCHIVO_TERRITORIO, citar, compilar
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
    mediciones: list = field(default_factory=list)               # mediciones.yaml (M1-03): vacío = ninguna variable es una medición
    unidades: list = field(default_factory=list)                 # unidades.yaml (M1-07): vacío = el verificador parte del primer archivo del universo

    @classmethod
    def cargar(cls, raiz: Path = RAIZ_REPO) -> "Contexto":
        raiz = Path(raiz)
        relaciones = {}
        for ruta in sorted((raiz / tc.CARPETA).glob("archivos_*_*.yaml")):
            d = yaml.safe_load(ruta.read_text(encoding="utf-8"))
            relaciones[(d["encuesta"], int(d["anio"]))] = relaciones_desde_yaml(d)
        with open(raiz / "catalogo" / "inferencia_verificada.csv", encoding="utf-8", newline="") as f:
            verificada = {(r["fuente"], int(r["anio"]), r["modulo"]): r for r in csv.DictReader(f)}
        rank = json.loads((raiz / "reglas" / "reglas.json").read_text(encoding="utf-8"))["parametros_globales"]["NIVEL_RANK"]
        return cls(Esquema.desde_parquet(raiz / "biblioteca" / "variables"), tc.leer_universos(raiz), tc.leer_diseno_muestral(raiz),
                   tc.leer_territorios(raiz), tc.leer_cortes(raiz), tc.leer_perfil_anual(raiz), relaciones, verificada,
                   {k: v for k, v in rank.items() if isinstance(v, (int, float))}, ParametrosVerificador.desde_yaml(),
                   raiz / "biblioteca" / "microdatos", tc.leer_mediciones(raiz), tc.leer_unidades(raiz))


def relaciones_desde_yaml(d: dict) -> list[UnionPlan]:
    """Las relaciones de `archivos_<encuesta>_<año>.yaml` como uniones; una cardinalidad fuera de `tc.CARDINALIDADES` es un error."""
    out = []
    for r in d["relaciones"]:
        if r.get("cardinalidad") not in tc.CARDINALIDADES:
            raise PapError(f"la relación {r['hijo']}→{r['padre']} declara la cardinalidad {r.get('cardinalidad')!r}; las válidas son {list(tc.CARDINALIDADES)}")
        out.append(UnionPlan(r["hijo"], r["padre"], tuple((a, b) for a, b in r["por"]), r["cardinalidad"]))
    return out


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

def _mediciones_del_plan(ctx: Contexto, plan: Plan) -> set[str]:
    """Las mediciones (mediciones.yaml) de las variables que intervienen en el indicador y en las restricciones."""
    out = set()
    for c in _condiciones(plan):
        v = ctx.esquema.variables[c.var]
        m = tc.medicion_de(ctx.mediciones, plan.encuesta, plan.anios[0], v["archivo"], v["variable"])
        if m is not None:
            out.add(m)
    return out


def _base_comun(cand: list):
    """El universo contenido en todos los demás (sus predicados son un subconjunto de los de cada uno), o None."""
    conjuntos = [frozenset((p.var, p.op, tuple(p.valores)) for p in u.predicados) for u in cand]
    for u, s in zip(cand, conjuntos):
        if all(s <= o for o in conjuntos):
            return u
    return None


def _tablas_de_la_unidad(ctx: Contexto, plan: Plan) -> set[str] | Falla:
    """Las tablas de las variables del plan que son de la unidad del plan según `unidades.yaml` (M1-07). Vacío si ninguna tabla del plan
    está en el lote (el verificador conserva entonces el comportamiento de M0/M1-03). Si hay tablas del lote y ninguna es de la unidad del
    plan, el plan no es coherente: falla."""
    anio = plan.anios[0]
    filas = {}
    for c in _condiciones(plan):
        archivo = ctx.esquema.variables[c.var]["archivo"]
        fila = tc.unidad_de(ctx.unidades, plan.encuesta, anio, archivo)
        if fila is not None:
            filas[archivo] = fila
    propias = {a for a, f in filas.items() if f.unidad_plan == plan.unidad}
    if filas and not propias:
        return Falla("plan", "universo", f"las variables del plan son de tablas de la unidad {sorted({f.unidad_plan for f in filas.values()})} "
                     f"({sorted(filas)}), no de «{plan.unidad}»")
    return propias


def _universo_analitico(ctx: Contexto, plan: Plan, tablas: set[str] = frozenset()):
    anio = plan.anios[0]
    de_la_unidad = [u for u in ctx.universos if u.encuesta == plan.encuesta and u.unidad == plan.unidad and u.anios[0] <= anio <= u.anios[1]]
    medidas = _mediciones_del_plan(ctx, plan)
    cubre_tablas = lambda u: tablas <= set(u.aplica_a.archivos)             # por la tabla que interviene (M1-07)
    if plan.universo_analitico is not None:                     # la receta nombra su universo y se aplica completo
        nombrado = next((u for u in ctx.universos if u.id == plan.universo_analitico), None)
        if nombrado is None:
            return Falla("plan", "universo", f"el universo analítico «{plan.universo_analitico}» no existe en universos_analiticos.yaml")
        if nombrado not in de_la_unidad:
            return Falla("plan", "universo", f"el universo «{nombrado.id}» no es de {plan.encuesta} {anio} para la unidad «{plan.unidad}» "
                         f"(es de {nombrado.encuesta} {nombrado.anios[0]}–{nombrado.anios[1]}, unidad «{nombrado.unidad}»)")
        if not cubre_tablas(nombrado):
            return Falla("plan", "universo", f"el universo «{nombrado.id}» no cubre las tablas {sorted(tablas - set(nombrado.aplica_a.archivos))} "
                         f"del plan (cubre {nombrado.aplica_a.archivos})")
        falta = sorted(medidas - set(nombrado.aplica_a.mediciones))
        if falta:
            return Falla("plan", "universo", f"el universo «{nombrado.id}» no cubre la medición {falta} de las variables del plan "
                         f"(cubre {nombrado.aplica_a.mediciones})")
        return nombrado
    if not de_la_unidad:
        return Falla("plan", "universo", f"no hay universo analítico de {plan.encuesta} {anio} para la unidad «{plan.unidad}»")
    de_la_unidad = [u for u in de_la_unidad if cubre_tablas(u)]
    if not de_la_unidad:
        return Falla("plan", "universo", f"ningún universo de la unidad «{plan.unidad}» cubre a la vez las tablas {sorted(tablas)}")
    cand = de_la_unidad
    if medidas:                                                 # según la medición: los que la cubren, los más específicos
        cubren = [u for u in de_la_unidad if medidas <= set(u.aplica_a.mediciones)]
        if not cubren:
            return Falla("plan", "universo", f"ningún universo de la unidad «{plan.unidad}» cubre a la vez las mediciones {sorted(medidas)}")
        menos = min(len(u.aplica_a.mediciones) for u in cubren)
        cand = [u for u in cubren if len(u.aplica_a.mediciones) == menos]
    u = _base_comun(cand)
    if u is None:
        return Falla("plan", "universo", f"los universos de la unidad «{plan.unidad}» no tienen una base común: {[x.id for x in cand]}")
    return u


def _tabla_base(ctx: Contexto, plan: Plan, tablas: set[str], relaciones: list[UnionPlan], universo) -> str | Falla:
    """La tabla de la que parte el plan (M1-07): la `tabla_base` de `unidades.yaml` de las tablas del plan que son de la unidad. Si hay
    varias bases, la primera (por nombre) desde la que las demás se alcanzan por uniones declaradas; si ninguna, falla del plan. Sin tablas
    del lote, el primer archivo del universo (M0/M1-03)."""
    if not tablas:
        return universo.aplica_a.archivos[0]
    bases = sorted({tc.unidad_de(ctx.unidades, plan.encuesta, plan.anios[0], a).tabla_base for a in tablas})
    for b in bases:
        if ruta_de_uniones(relaciones, b, set(bases) - {b}) is not None:
            return b
    return Falla("plan", "uniones", f"las tablas {sorted(tablas)} de la unidad «{plan.unidad}» parten de {bases}, y ninguna se une a las otras "
                 "por una unión declarada")


def _archivo_de(ctx: Contexto, plan: Plan, nombre: str, archivos: list[str]) -> str | None:
    return next((a for a in archivos if ctx.esquema.tiene(plan.encuesta, plan.anios[0], a, nombre)), None)


def ruta_de_uniones(relaciones: list[UnionPlan], origen: str, destinos: set[str]) -> tuple[UnionPlan, ...] | None:
    """Uniones izquierdas que llevan de `origen` a cada destino, la que trae un archivo después de la que trae de lo que cuelga. None si
    alguno no se alcanza. Dos tipos de paso (M1-03):
    - hacia el padre (hijo → padre, de cualquier cardinalidad): el de siempre;
    - hacia un hermano: desde un archivo al que se llegó hacia el padre (o desde el origen), a un hijo suyo con cardinalidad `1:1` o `1:0..1`
      por su llave (el hijo no repite filas del padre). Se baja un solo nivel desde el padre común: el hermano no es punto de partida de otros."""
    sube: dict[str, list[UnionPlan]] = {}
    baja: dict[str, list[UnionPlan]] = {}
    for r in relaciones:
        sube.setdefault(r.hijo, []).append(r)
        if r.cardinalidad in ("1:1", "1:0..1"):
            baja.setdefault(r.padre, []).append(replace(r, hacia="hijo"))
    llegada: dict[str, UnionPlan | None] = {origen: None}
    cola = deque([origen])
    while cola:
        a = cola.popleft()
        for r in sube.get(a, []):
            if r.padre not in llegada:
                llegada[r.padre] = r
                cola.append(r.padre)
    for a in list(llegada):                                     # hermanos: solo desde lo alcanzado hacia el padre
        for r in baja.get(a, []):
            if r.hijo not in llegada:
                llegada[r.hijo] = r
    salida: list[UnionPlan] = []
    for d in sorted(destinos):
        if d not in llegada:
            return None
        cadena = []
        while llegada[d] is not None:
            cadena.append(llegada[d])
            d = llegada[d].ancla
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
        opciones = [o for o in c.por_encuesta.get(plan.encuesta, [])
                    if not ctx.unidades or tc.corte_aplica(ctx.unidades, plan.encuesta, plan.anios[0], plan.unidad, o)]
        elegida = next((o for o in opciones if o.archivo == archivo_unidad), None) or next(
            (o for o in opciones if ruta_de_uniones(relaciones, archivo_unidad, {o.archivo}) is not None), None)
        if elegida is None:
            return Falla("plan", "cortes", f"el corte «{cid}» no tiene variable en un archivo al que se una {archivo_unidad}")
        try:
            definicion = tc.definir_corte(c, elegida, plan.receta_id)
        except tc.CorteNoCompilable as e:
            return Falla("plan", "cortes", str(e))
        if not ctx.esquema.tiene(plan.encuesta, plan.anios[0], elegida.archivo, elegida.variable):
            return Falla("plan", "cortes", f"{elegida.archivo}.{elegida.variable} no está en el índice")
        out.append(CorteResuelto(cid, elegida.archivo, elegida.variable, definicion.categorias, definicion.reglas))
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

    tablas = _tablas_de_la_unidad(ctx, plan)
    if isinstance(tablas, Falla):
        return tablas
    ua = _universo_analitico(ctx, plan, tablas)
    if isinstance(ua, Falla):
        return ua
    relaciones = ctx.relaciones[(plan.encuesta, anio)]
    archivo_unidad = _tabla_base(ctx, plan, tablas, relaciones, ua)
    if isinstance(archivo_unidad, Falla):
        return archivo_unidad
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
    hay_sin_pareja = any(u.hacia == "hijo" and u.cardinalidad == "1:0..1" for u in pc.uniones)
    r = ejecutar_select(
        con, "SELECT count(*), count(*) FILTER (WHERE u), sum(peso) FILTER (WHERE u), count(DISTINCT upm) FILTER (WHERE u), "
        "count(DISTINCT estrato) FILTER (WHERE u), count(*) FILTER (WHERE u AND y IS NULL), "
        "count(*) FILTER (WHERE u AND (peso IS NULL OR estrato IS NULL OR upm IS NULL)), "
        "count(DISTINCT territorio) FILTER (WHERE u), "
        + ("count(*) FILTER (WHERE u AND sin_pareja)" if hay_sin_pareja else "0")
        + f" FROM ({d.sql})", d.parametros).fetchone()
    filas_union, n_despues, suma_pesos, n_upm, n_estratos, y_nulos, diseno_nulos, n_unidades, n_sin_pareja = r
    c = {"filas_unidad": filas_unidad, "filas_tras_uniones": filas_union, "u_antes": n_antes, "u_despues": n_despues,
         "suma_pesos_u": float(suma_pesos) if suma_pesos is not None else None, "conglomerados_u": n_upm, "estratos_u": n_estratos,
         "y_nulos_en_u": y_nulos, "diseno_nulo_en_u": diseno_nulos, "unidades_territorio": n_unidades,
         "uniones": [u.texto for u in pc.uniones]}
    if hay_sin_pareja:
        c["u_sin_pareja"] = n_sin_pareja
    if filas_union != filas_unidad:
        return Falla("plan", "uniones", f"las uniones cambian las filas de {pc.archivo_unidad}: {filas_unidad} → {filas_union}")
    if n_antes == 0:
        return Falla("plan", "universo", "u queda vacío")
    perdida = (n_antes - n_despues + n_sin_pareja) / n_antes           # las filas de u sin pareja en un hermano 1:0..1 cuentan como perdidas
    c["perdida_u"] = perdida
    if perdida > ctx.p.union_perdida_max:
        sin = f", de ellas {n_sin_pareja} sin pareja en el archivo hermano" if n_sin_pareja else ""
        return Falla("plan", "uniones", f"las uniones pierden {perdida:.2%} de las filas de u{sin} (máximo {ctx.p.union_perdida_max:.2%})")
    if y_nulos:
        return Falla("plan", "y", f"{y_nulos} filas de u con y nulo (un nulo dentro de u es un error)")
    if diseno_nulos:
        return Falla("plan", "diseno", f"{diseno_nulos} filas de u sin peso, estrato o conglomerado")
    c["dominios"] = (1 if plan.territorio.id is not None else n_unidades) * _celdas_de_cortes(pc)
    out = _con_dominios(ctx, replace(pc, controles=c), n_unidades)
    return replace(out, controles=c | {"dominios": c["dominios"]}) if isinstance(out, PlanCompleto) else out


def comprobar_cardinalidades(relaciones: list[UnionPlan], carpeta_microdatos: Path, encuesta: str, anio: int, con) -> list[str]:
    """Comprueba contra los Parquet las relaciones declaradas `1:1` y `1:0..1` (las que permiten ir de hermano a hermano por el padre
    común): el hijo no repite su llave (`pares`), y si es `1:1` toda fila del padre tiene su pareja. Devuelve los problemas ([] = todo
    en orden). Las `n:1` no se comprueban aquí: son la dirección de siempre (los controles de la unión miran las filas de la unidad)."""
    problemas = []
    for r in relaciones:
        if r.cardinalidad not in ("1:1", "1:0..1"):
            continue
        ruta = lambda a: str(Path(carpeta_microdatos) / encuesta / str(anio) / f"{a}.parquet")
        cols_h = ", ".join(citar(ch) for ch, _ in r.pares)
        cols_p = " AND ".join(f"h.{citar(ch)} = p.{citar(cp)}" for ch, cp in r.pares)
        n_h, n_h_dist = ejecutar_select(con, f"SELECT count(*), count(DISTINCT ({cols_h})) FROM read_parquet(?)", [ruta(r.hijo)]).fetchone()
        n_p, sin_pareja = ejecutar_select(
            con, f"SELECT count(*), count(*) FILTER (WHERE h.{citar(r.pares[0][0])} IS NULL) FROM read_parquet(?) p "
                 f"LEFT JOIN read_parquet(?) h ON {cols_p}", [ruta(r.padre), ruta(r.hijo)]).fetchone()
        if n_h != n_h_dist:
            problemas.append(f"{r.hijo}→{r.padre} ({r.cardinalidad}): {r.hijo} repite su llave ({n_h} filas, {n_h_dist} distintas)")
        if r.cardinalidad == "1:1" and sin_pareja:
            problemas.append(f"{r.hijo}→{r.padre} (1:1): {sin_pareja} de {n_p} filas de {r.padre} quedan sin pareja en {r.hijo}")
    return problemas
