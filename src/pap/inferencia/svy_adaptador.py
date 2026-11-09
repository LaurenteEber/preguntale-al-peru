"""Adaptador de `svy` (M0-08; `tecnologias.md` §2 y diseño §14). **El único módulo de `src/pap/inferencia` que importa `svy`**
(lo comprueba `tests/inferencia/test_svy_adaptador.py`; `src/pap/motor/calculo.py` sigue con su propia llamada y es el oráculo).

Mismo cálculo que `calculo._svy_niveles`, llamada por llamada: `Design(stratum, psu, wgt)` con `Singleton("center", domains="standard")`,
`estimation.prop(y, by=, where=u, ci_method="korn-graubard", deff="wr")` sobre **todos** los conglomerados (nunca se recorta el marco antes
de declarar el diseño) y, si un dominio no tiene ningún «sí», el complemento de la fila `y = 0` (Korn-Graubard es simétrico).

Lo que agrega sobre el cubo:
- **reindexa los dominios pedidos:** `svy` no devuelve un dominio vacío; aquí sale con `n = 0` («sin datos»);
- n efectivo = mín(n, p(1−p)/ee²), y n si ee = 0;
- eventos (casos con y = 1) y tasa de no respuesta del ítem, ponderada y sin ponderar.

`svy` se lee solo aquí: la salida de `to_polars()` cambia entre versiones (la 0.36 cambia las columnas), así que un cambio de versión
toca únicamente este archivo.
"""
from __future__ import annotations

import math
from typing import Sequence

from .estimacion import Estimacion

_SEP = "\x1f"


def _f(x) -> float | None:
    """Mismo criterio que `calculo._f`: nulo, NaN o infinito no son una cifra."""
    return None if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))) else float(x)


def n_efectivo(p: float | None, ee: float | None, n: int) -> float | None:
    """Mín(n, p(1−p)/ee²); n si ee = 0 (§14). El cubo no lo topa; el ejecutor sí."""
    if p is None or ee is None or math.isnan(ee):
        return None
    if ee == 0:
        return float(n)
    return min(float(n), p * (1 - p) / ee ** 2)


def estimar_proporciones(marco, por: Sequence[str], dominios: Sequence[tuple[str, ...]] | None = None, *, u: str = "u", y: str = "y",
                         estrato: str = "estrato", upm: str = "upm", peso: str = "peso", faltante: str | None = None,
                         solo: Sequence[tuple[str, ...]] | None = None, anio: int | None = None) -> list[Estimacion]:
    """Una `Estimacion` por dominio de `por` (columnas de `marco`, un `polars.DataFrame`).

    - `u`: booleano; `y`: 0/1 dentro de `u` (nulo fuera). Un nulo de `y` dentro de `u` es un error del llamador (`ValueError`);
    - `dominios`: los pedidos, cada uno una tupla de textos en el orden de `por`. Sin ellos, los que `svy` devuelve;
    - `solo`: subconjunto de `dominios` que se calcula (un bloque de la llamada partida): se restringe el `where`, no el marco;
    - `faltante`: columna booleana de las filas que habrían entrado a `u` pero se excluyeron por falta de respuesta del ítem
      (`faltante_excluye`); sin ella la tasa de no respuesta queda en None (no se midió).
    """
    import polars as pl
    import svy

    por = list(por)
    nulos = marco.filter(pl.col(u).fill_null(False) & pl.col(y).is_null()).height
    if nulos:
        raise ValueError(f"{nulos} filas de u con y nulo")
    cols = [pl.col(c).cast(pl.String) for c in por]
    base = marco.select(
        pl.when(pl.col(u).fill_null(False)).then(pl.col(y)).otherwise(0).cast(pl.Float64).alias("_y"),
        pl.col(u).fill_null(False).alias("_u"),
        pl.col(estrato).cast(pl.String).alias("_h"), pl.col(upm).cast(pl.String).alias("_c"), pl.col(peso).cast(pl.Float64).alias("_w"),
        *(c.alias(n) for c, n in zip(cols, por)),
        *([pl.col(faltante).fill_null(False).alias("_f")] if faltante else []))
    en_dominio = pl.all_horizontal(*(pl.col(c).is_not_null() for c in por))
    donde = pl.col("_u") & en_dominio
    if solo is not None:
        donde = donde & pl.concat_str(por, separator=_SEP).is_in([_SEP.join(d) for d in solo])
    muestra = svy.Sample(base, svy.Design(stratum="_h", psu="_c", wgt="_w", singleton=svy.Singleton("center", domains="standard")))
    est = muestra.estimation.prop("_y", by=por, where=donde, ci_method="korn-graubard", deff="wr")

    filas: dict[tuple, dict[float, dict]] = {}
    for r in est.to_polars().iter_rows(named=True):
        filas.setdefault(tuple(r[c] for c in por), {})[float(r["_y"])] = r
    dentro = base.filter(donde)
    conteo = {tuple(r[c] for c in por): r["ev"] for r in
              dentro.group_by(por).agg((pl.col("_y") == 1).sum().alias("ev")).iter_rows(named=True)}
    nr = _tasas_no_respuesta(base, por, en_dominio) if faltante else {}

    pedidos = list(dominios) if dominios is not None else sorted(filas)
    if solo is not None:
        permitidos = set(solo)
        pedidos = [d for d in pedidos if d in permitidos]
    salida = []
    for d in pedidos:
        g = filas.get(tuple(d))
        t_nr, t_nr_p = nr.get(tuple(d), (None, None))
        if not g:
            salida.append(Estimacion(dominio=tuple(d), anio=anio, n=0, tasa_no_respuesta=t_nr, tasa_no_respuesta_ponderada=t_nr_p))
            continue
        if 1.0 in g:
            r = g[1.0]
            p, lo, hi = float(r["est"]), float(r["lci"]), float(r["uci"])
        else:                                       # ningún «sí» en el dominio: complemento de la fila y = 0
            r = g[0.0]
            p, lo, hi = 1 - float(r["est"]), 1 - float(r["uci"]), 1 - float(r["lci"])
        n, ee = int(r["n"]), float(r["se"])
        salida.append(Estimacion(dominio=tuple(d), anio=anio, n=n, valor=p, ee=_f(ee), gl=int(r["df"]), n_efectivo=n_efectivo(p, ee, n),
                                 deff=_f(r.get("deff")), ic_inf=_f(lo), ic_sup=_f(hi), eventos=int(conteo.get(tuple(d), 0)),
                                 tasa_no_respuesta=t_nr, tasa_no_respuesta_ponderada=t_nr_p))
    return salida


def _tasas_no_respuesta(base, por: list[str], en_dominio) -> dict[tuple, tuple[float, float]]:
    """Por dominio: filas con `faltante` entre las que serían del universo (las de `u` más las excluidas por faltante)."""
    import polars as pl

    elegibles = base.filter(en_dominio & (pl.col("_u") | pl.col("_f")))
    agg = elegibles.group_by(por).agg(
        pl.col("_f").sum().alias("nr"), pl.len().alias("t"),
        (pl.col("_w") * pl.col("_f")).sum().alias("wnr"), pl.col("_w").sum().alias("wt"))
    return {tuple(r[c] for c in por): (r["nr"] / r["t"], (r["wnr"] / r["wt"]) if r["wt"] else None) for r in agg.iter_rows(named=True)}
