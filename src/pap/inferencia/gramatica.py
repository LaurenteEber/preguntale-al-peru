"""Gramática de predicados y compilación a SQL con parámetros (M0-07; diseño §11.3 y §22).

**El plan no contiene SQL.** Este módulo es el único lugar que arma texto SQL a partir de un plan, y lo hace así:
- los **nombres de columna y de archivo salen del índice** (`Esquema`): cada uno se comprueba contra `variables.parquet` y se
  escribe entre comillas dobles, calificado con su archivo: `"RECH6"."HC57"`. Un nombre que no está en el índice detiene la
  compilación (`ErrorGramatica`);
- los **valores** (números del plan, textos de las expresiones curadas, la ruta de cada Parquet) van **siempre como `?`**;
- los operadores son los seis del §11.3 y las combinaciones, `una`, `alguna_de` y `todas_de`, con un máximo de 3 condiciones.

Las expresiones de `diseno_muestral.csv` y `territorios.yaml` (`peso_expr`, `unidad_expr`…) son texto de una tabla curada, no del
plan; igual se pasan por `calificar_expresion`: cada identificador debe ser una columna del índice, cada función debe estar en
la lista corta, y cada texto entre comillas simples pasa a ser un parámetro.

`compilar` arma una sola consulta con las columnas `u`, `y`, `corte_<id>`, `territorio`, `peso`, `estrato` y `upm`:
- `u` (verdadero/falso): la fila está en el universo (universo analítico y restricciones del plan); un nulo no cumple nada;
- `y` (0/1): vale solo dentro de `u`; fuera de `u` es nulo. Con `rol_faltante` vacío (M0) ningún código sale del denominador
  ni cuenta como «no», así que `y` es nulo únicamente fuera del universo; un nulo **dentro** de `u` es un error y lo cuenta el
  verificador. Por eso el universo de la receta debe excluir los códigos no válidos (HC57 en 1–4);
- `territorio`: el identificador de la unidad del nivel (nulo si la fila no entra al nivel);
- `peso`, `estrato`, `upm`: el diseño de la submuestra.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping

from ..errores import PapError
from .duckdb_seguro import ejecutar_select
from .plan import MAX_CONDICIONES, Condicion, Indicador, PlanCompleto, UnionPlan

_NOMBRE = re.compile(r"^[A-Za-z0-9_]{1,64}$")
# Palabras SQL que pueden aparecer en las expresiones curadas, y funciones permitidas (lista corta, revisada con las tablas).
PALABRAS = frozenset({"CASE", "WHEN", "THEN", "ELSE", "END", "IN", "AND", "OR", "NOT", "TRUE", "FALSE", "NULL", "IS", "BETWEEN"})
# Los niveles de territorios.yaml se arman sobre RECH0 (un hogar por fila; los niños se ubican por el hogar).
ARCHIVO_TERRITORIO = "RECH0"
FUNCIONES = frozenset({"printf", "substr"})
_TOKEN = re.compile(r"'(?:[^']|'')*'|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|[A-Za-z_]\w*|\s+|[(),<>=+*/%.-]")


class ErrorGramatica(PapError):
    """El plan o una expresión curada pide algo que no cabe en la gramática o que no está en el índice."""


def citar(nombre: str) -> str:
    """Identificador entre comillas dobles. Solo letras, dígitos y «_»: cualquier otra cosa no es un nombre del índice."""
    if not _NOMBRE.match(nombre):
        raise ErrorGramatica(f"nombre no permitido: {nombre!r}")
    return f'"{nombre}"'


# ------------------------------------------------------------------ índice

@dataclass(frozen=True)
class Esquema:
    """Lo que dice el índice de variables (`biblioteca/variables/*.parquet`): la única fuente de nombres de columna."""
    variables: Mapping[str, Mapping]                                  # var_id → fila de variables.parquet
    categorias: Mapping[str, Mapping[str, Mapping]]                   # var_id → código (texto) → fila de categorias.parquet
    archivos: Mapping[tuple[str, int, str], Mapping]                  # (encuesta, año, archivo) → fila de archivos.parquet
    columnas: Mapping[tuple[str, int, str], frozenset[str]] = field(default_factory=dict)   # (encuesta, año, archivo) → columnas

    @classmethod
    def desde_frames(cls, variables, categorias, archivos) -> "Esquema":
        vs = {r["var_id"]: r for r in variables.to_dicts()}
        cats: dict[str, dict] = {}
        for r in categorias.to_dicts():
            cats.setdefault(r["var_id"], {})[str(r["codigo"])] = r
        cols: dict[tuple, set] = {}
        for r in vs.values():
            cols.setdefault((r["encuesta"], int(r["anio"]), r["archivo"]), set()).add(r["variable"])
        return cls(vs, cats, {(r["encuesta"], int(r["anio"]), r["archivo"]): r for r in archivos.to_dicts()},
                   {k: frozenset(v) for k, v in cols.items()})

    @classmethod
    def desde_parquet(cls, carpeta: Path) -> "Esquema":
        import polars as pl

        leer = lambda n: pl.read_parquet(Path(carpeta) / f"{n}.parquet")
        return cls.desde_frames(leer("variables"), leer("categorias"), leer("archivos"))

    def tiene(self, encuesta: str, anio: int, archivo: str, columna: str) -> bool:
        return columna in self.columnas.get((encuesta, anio, archivo), ())

    def ident(self, encuesta: str, anio: int, archivo: str, columna: str) -> str:
        """`"ARCHIVO"."COLUMNA"`, solo si el índice tiene esa columna en ese archivo y año."""
        if not self.tiene(encuesta, anio, archivo, columna):
            raise ErrorGramatica(f"{archivo}.{columna} no está en el índice de {encuesta} {anio}")
        return f"{citar(archivo)}.{citar(columna)}"

    def variable(self, var_id: str) -> Mapping:
        if var_id not in self.variables:
            raise ErrorGramatica(f"la variable {var_id!r} no está en el índice")
        return self.variables[var_id]


# ------------------------------------------------------------------ constructor con parámetros

@dataclass
class Compilado:
    sql: str
    parametros: list
    identificadores: frozenset[tuple[str, str]]                       # (archivo, columna) que la consulta nombra
    archivos: tuple[str, ...]                                         # archivos leídos, en orden

    def ejecutar(self, con):
        return ejecutar_select(con, self.sql, self.parametros)


class _Constructor:
    """Junta los parámetros en el orden en que aparecen en el texto: cada fragmento se pide en el orden en que se escribe."""

    def __init__(self, esquema: Esquema, encuesta: str, anio: int):
        self.esquema, self.encuesta, self.anio = esquema, encuesta, anio
        self.parametros: list = []
        self.usados: set[tuple[str, str]] = set()

    def par(self, valor) -> str:
        self.parametros.append(valor)
        return "?"

    def col(self, archivo: str, columna: str) -> str:
        self.usados.add((archivo, columna))
        return self.esquema.ident(self.encuesta, self.anio, archivo, columna)

    def var(self, var_id: str) -> str:
        v = self.esquema.variable(var_id)
        if (v["encuesta"], int(v["anio"])) != (self.encuesta, self.anio):
            raise ErrorGramatica(f"{var_id}: no es de {self.encuesta} {self.anio}")
        return self.col(v["archivo"], v["variable"])

    def condicion(self, c: Condicion) -> str:
        x = self.var(c.var)
        if c.op == "en":
            return f"{x} IN ({', '.join(self.par(v) for v in c.valores)})"
        if c.op == "entre":
            return f"{x} BETWEEN {self.par(c.valores[0])} AND {self.par(c.valores[1])}"
        if c.op == "<":
            return f"{x} < {self.par(c.valores[0])}"
        if c.op == "≥":
            return f"{x} >= {self.par(c.valores[0])}"
        if c.op == "es_nulo":
            return f"{x} IS NULL"
        if c.op == "no_es_nulo":
            return f"{x} IS NOT NULL"
        raise ErrorGramatica(f"operador fuera de la gramática: {c.op!r}")

    def indicador(self, ind: Indicador) -> str:
        if not 1 <= len(ind.condiciones) <= MAX_CONDICIONES:
            raise ErrorGramatica(f"entre 1 y {MAX_CONDICIONES} condiciones")
        partes = [self.condicion(c) for c in ind.condiciones]
        if ind.combinar == "una":
            if len(partes) != 1:
                raise ErrorGramatica("«una» lleva exactamente una condición")
            return partes[0]
        unir = {"alguna_de": " OR ", "todas_de": " AND "}.get(ind.combinar)
        if unir is None:
            raise ErrorGramatica(f"combinación fuera de la gramática: {ind.combinar!r}")
        return "(" + unir.join(f"({p})" for p in partes) + ")"

    def expresion(self, expr: str, resolver: Callable[[str], str]) -> str:
        """Pasa una expresión curada a SQL con parámetros (ver `calificar_expresion`)."""
        return calificar_expresion(expr, resolver, self.par)


def calificar_expresion(expr: str, resolver: Callable[[str], str], par: Callable[[object], str]) -> str:
    """Expresión de una tabla curada → SQL: identificadores por `resolver` (que exige que estén en el índice), números tal
    cual (ya verificados por el alfabeto del token), textos entre comillas simples como parámetro (`par`)."""
    salida, pos = [], 0
    while pos < len(expr):
        m = _TOKEN.match(expr, pos)
        if not m:
            raise ErrorGramatica(f"expresión con un símbolo que la gramática no admite: {expr[pos:pos + 10]!r}")
        t, pos = m.group(0), m.end()
        if (t == "-" and expr[pos:pos + 1] == "-") or (t == "/" and expr[pos:pos + 1] == "*"):
            raise ErrorGramatica(f"expresión con un comentario SQL («--» o «/*»): {expr!r}")        # H07-2
        if t.startswith("'"):
            salida.append(par(t[1:-1].replace("''", "'")))
        elif t[0].isalpha() or t[0] == "_":
            if t.upper() in PALABRAS:
                salida.append(t.upper())
            elif expr[pos:].lstrip().startswith("("):
                if t.lower() not in FUNCIONES:
                    raise ErrorGramatica(f"función no permitida: {t!r}")
                salida.append(t.lower())
            else:
                salida.append(resolver(t))
        else:
            salida.append(t)
    return "".join(salida)


# ------------------------------------------------------------------ compilación

def _ruta_parquet(carpeta: Path, encuesta: str, anio: int, archivo: str) -> str:
    return str(Path(carpeta) / encuesta / str(anio) / f"{archivo}.parquet")


def _desde(b: _Constructor, archivo_unidad: str, uniones: tuple[UnionPlan, ...], carpeta: Path) -> str:
    """`FROM` con la unidad y las uniones izquierdas hacia sus padres (n:1: no repiten ni quitan filas de la unidad)."""
    partes = [f"FROM read_parquet({b.par(_ruta_parquet(carpeta, b.encuesta, b.anio, archivo_unidad))}) AS {citar(archivo_unidad)}"]
    for u in uniones:
        on = " AND ".join(f"{b.col(u.hijo, ch)} = {b.col(u.padre, cp)}" for ch, cp in u.pares)
        partes.append(f"LEFT JOIN read_parquet({b.par(_ruta_parquet(carpeta, b.encuesta, b.anio, u.padre))}) AS {citar(u.padre)} ON {on}")
    return "\n".join(partes)


def _resolver_diseno(pc: PlanCompleto, b: _Constructor, archivos_union: set[str]) -> Callable[[str], str]:
    """Las columnas del diseño se buscan en el archivo de la fila de `diseno_muestral.csv` y en sus padres declarados."""
    candidatos = [pc.diseno.archivo] + [p for _, _, p, _ in pc.diseno.uniones]

    def resolver(nombre: str) -> str:
        for a in candidatos:
            if a in archivos_union and b.esquema.tiene(b.encuesta, b.anio, a, nombre):
                return b.col(a, nombre)
        raise ErrorGramatica(f"la columna {nombre!r} del diseño no está en el índice de {candidatos} (o su archivo no está unido)")
    return resolver


def _resolver_territorio(b: _Constructor, archivos_union: set[str], archivo: str = ARCHIVO_TERRITORIO) -> Callable[[str], str]:
    def resolver(nombre: str) -> str:
        if archivo not in archivos_union:
            raise ErrorGramatica(f"el territorio se arma sobre {archivo} y ese archivo no está unido")
        return b.col(archivo, nombre)
    return resolver


def compilar(pc: PlanCompleto, esquema: Esquema, carpeta_microdatos: Path, *, solo_u_y: bool = False,
             sin_dato: str = "sin dato") -> Compilado:
    """SQL con parámetros del plan completo. Con `solo_u_y=True` arma solo `u` e `y` (sin cortes, territorio ni diseño):
    es el «antes» del control de uniones del verificador."""
    plan = pc.plan
    anio = plan.anios[0]
    b = _Constructor(esquema, plan.encuesta, anio)
    uniones = pc.uniones_u_y if solo_u_y else pc.uniones
    archivos_union = {pc.archivo_unidad} | {u.padre for u in uniones}

    # SELECT interior, en el orden en que se escribe: u, ind, cortes, territorio, peso, estrato, upm.
    ua = pc.universo_analitico
    donde_ua = [a for a in ua.aplica_a.archivos]

    def col_ua(nombre: str) -> str:
        for a in donde_ua:
            if esquema.tiene(plan.encuesta, anio, a, nombre):
                return b.col(a, nombre)
        raise ErrorGramatica(f"{nombre!r} no está en {donde_ua}")

    preds = []
    for p in ua.predicados:
        v = [int(x) if float(x).is_integer() else x for x in p.valores]
        x = col_ua(p.var)
        preds.append(f"{x} BETWEEN {b.par(v[0])} AND {b.par(v[1])}" if p.op == "entre"
                     else f"{x} IN ({', '.join(b.par(z) for z in v)})")
    preds += [b.condicion(c) for c in plan.universo.restricciones]
    u = "COALESCE(" + " AND ".join(f"({p})" for p in preds) + ", FALSE) AS u"
    ind = f"{b.indicador(plan.indicador)} AS ind"
    cols_int = [u, ind]

    if solo_u_y:
        cols_ext = ["u", "CASE WHEN u THEN CAST(ind AS INTEGER) END AS y"]
    else:
        cols_ext = ["u", "CASE WHEN u THEN CAST(ind AS INTEGER) END AS y"]
        for c in pc.cortes:
            cols_int.append(f"COALESCE(CAST({b.col(c.archivo, c.variable)} AS VARCHAR), {b.par(sin_dato)}) AS {citar('corte_' + c.id)}")
            cols_ext.append(citar("corte_" + c.id))
        t = pc.territorio
        res_t = _resolver_territorio(b, archivos_union)
        cond_t = b.expresion(t.expr, res_t)
        if plan.territorio.id is not None:
            unidad_cmp = b.expresion(t.unidad_expr, res_t)
            cond_t = f"({cond_t}) AND ({unidad_cmp}) = {b.par(plan.territorio.id)}"
        cols_int.append(f"CASE WHEN {cond_t} THEN {b.expresion(t.unidad_expr, res_t)} END AS territorio")
        rd = _resolver_diseno(pc, b, archivos_union)
        cols_int.append(f"({b.expresion(pc.diseno.peso_expr, rd)}) AS peso")
        cols_int.append(f"{b.expresion(pc.diseno.estrato_expr, rd)} AS estrato")
        cols_int.append(f"{b.expresion(pc.diseno.psu_expr, rd)} AS upm")
        cols_ext += ["territorio", "peso", "estrato", "upm"]

    desde = _desde(b, pc.archivo_unidad, uniones, carpeta_microdatos)
    sql = "SELECT " + ", ".join(cols_ext) + "\nFROM (SELECT " + ",\n  ".join(cols_int) + "\n" + desde + ")"
    return Compilado(sql, b.parametros, frozenset(b.usados), (pc.archivo_unidad, *(u.padre for u in uniones)))

