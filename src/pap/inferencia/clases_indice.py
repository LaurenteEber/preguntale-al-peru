"""Clase de cada variable del índice (M1-05, tarea 0; diseño §6 y §7.2).

Hasta M1 el índice solo traía `clase` en las 86 columnas de `curados/inferencia/clases_columnas.yaml` (llaves, geografía, pesos y
diseño). Aquí se clasifica **solo el índice**: `clases_columnas.yaml` no se toca y los Parquet no se reconvierten (sus huellas de
contenido no cambian). El resultado es `variables.parquet` con la columna `clase` llena y ninguna otra columna distinta.

Orden de las reglas (la primera que aplica gana):

1. **Tabla curada** `clases_columnas.yaml` (`clase_indice` si existe, si no `clase`).
2. **Excepciones** de `curados/inferencia/clases_excepciones.yaml` (lista curada, cada una con su motivo).
3. **Llave del archivo** declarada en `archivos_<encuesta>_<año>.yaml` (`archivos.parquet`, columna `llave`) → `llave`.
4. **Por tipo de valor** (`tipo_valor` del índice) y número de categorías (`categorias.parquet`):
   - `texto` → `texto` (columna de texto que no es llave ni lugar: se queda fuera de las cuentas);
   - `categorica` con **dos o más** categorías con sentido (no especiales) → `categoria`;
   - `categorica` con una sola o ninguna (solo «no sabe», «inconsistente»…) → `medida`: el número es la medida y las etiquetas
     marcan sus bordes (edad «97 o más», día «97 = inconsistente»). Las marcas de una sola etiqueta («1 = Sí») van a excepciones;
   - `numerica` y `fecha` → `medida`.

Vocabulario: las seis clases del diseño más `texto` (supuesto M1-05-s1: el diseño no dice qué clase llevan las columnas de texto
libre o de respuesta múltiple guardadas como texto; el motor solo admite `categoria` y `medida`, así que `texto` las deja fuera).
"""
from __future__ import annotations

from pathlib import Path

import yaml

from ..errores import PapError

CLASES = ("llave", "geo", "categoria", "medida", "peso", "diseno", "texto")
RAIZ_REPO = Path(__file__).resolve().parents[3]
RUTA_EXCEPCIONES = RAIZ_REPO / "curados" / "inferencia" / "clases_excepciones.yaml"


def cargar_excepciones(ruta: Path = RUTA_EXCEPCIONES) -> list[dict]:
    return yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))["excepciones"]


def cargar_reglas(ruta: Path = RUTA_EXCEPCIONES) -> dict:
    return (yaml.safe_load(Path(ruta).read_text(encoding="utf-8")) or {}).get("reglas") or {}


def contar_sin_etiqueta(carpeta_parquet: Path, variables, categorias) -> dict[str, int]:
    """Por `var_id` de las categóricas con etiquetas: cuántos valores distintos del Parquet no tienen etiqueta (nulos aparte). Una sola
    consulta por tabla. Una columna de texto o sin Parquet cuenta 0 (la regla no actúa)."""
    import duckdb

    etiquetadas: dict[str, list[float]] = {}
    for vid, cod in zip(categorias["var_id"].to_list(), categorias["codigo"].to_list()):
        try:
            etiquetadas.setdefault(vid, []).append(float(cod))
        except (TypeError, ValueError):
            etiquetadas.setdefault(vid, [])
    out: dict[str, int] = {}
    con = duckdb.connect()
    cat = variables.filter(variables["tipo_valor"] == "categorica")
    for archivo in sorted(set(cat["archivo"].to_list())):
        ruta = Path(carpeta_parquet) / f"{archivo}.parquet"
        if not ruta.exists():
            continue
        tipos = {n: t for n, t, *_ in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{str(ruta).replace(chr(39), chr(39) * 2)}')").fetchall()}
        filas = [r for r in cat.filter(cat["archivo"] == archivo).iter_rows(named=True) if tipos.get(r["variable"], "VARCHAR") != "VARCHAR"]
        if not filas:
            continue
        exprs = []
        for r in filas:
            lst = ", ".join(repr(x) for x in etiquetadas.get(r["var_id"], [])) or "NULL"
            x = '"' + r["variable"].replace('"', '""') + '"'
            exprs.append(f"count(DISTINCT {x}) FILTER (WHERE {x} IS NOT NULL AND {x} NOT IN ({lst}))")
        res = con.execute(f"SELECT {', '.join(exprs)} FROM read_parquet('{str(ruta).replace(chr(39), chr(39) * 2)}')").fetchone()
        out.update({r["var_id"]: int(n) for r, n in zip(filas, res)})
    return out


def _aplica(e: dict, archivo: str, variable: str) -> bool:
    arch = e["archivos"]
    return variable in e["variables"] and (arch == "*" or archivo in arch)


def validar_excepciones(variables, excepciones: list[dict]) -> None:
    """Cada excepción: clase del vocabulario, motivo escrito, y que toque al menos una variable del índice; ninguna variable
    puede estar en dos excepciones. Una excepción vieja que ya no toca nada es un error, no un adorno."""
    pares = list(zip(variables["archivo"].to_list(), variables["variable"].to_list()))
    tocadas: dict[tuple[str, str], int] = {}
    for i, e in enumerate(excepciones):
        if e.get("clase") not in CLASES:
            raise PapError(f"excepción {i + 1} ({e.get('variables')}): clase {e.get('clase')!r} fuera del vocabulario {CLASES}")
        if not str(e.get("motivo") or "").strip():
            raise PapError(f"excepción {i + 1} ({e.get('variables')}): falta el motivo")
        if not (e.get("archivos") == "*" or (isinstance(e.get("archivos"), list) and e["archivos"])):
            raise PapError(f"excepción {i + 1} ({e.get('variables')}): `archivos` debe ser «*» o una lista")
        for v in e["variables"]:
            hit = [p for p in pares if p[1] == v and (e["archivos"] == "*" or p[0] in e["archivos"])]
            if not hit:
                raise PapError(f"excepción {i + 1}: la variable {v} no existe en {e['archivos']}")
            for p in hit:
                if p in tocadas:
                    raise PapError(f"dos excepciones tocan {p[0]}.{p[1]} (la {tocadas[p] + 1} y la {i + 1})")
                tocadas[p] = i


def clasificar(variables, categorias, archivos, curadas: dict, excepciones: list[dict], sin_etiqueta: dict[str, int] | None = None,
               minimo_sin_etiqueta: int | None = None):
    """`variables` (el DataFrame de `variables.parquet`) con la columna `clase` calculada desde cero. `curadas` = lo que devuelve
    `indice.cargar_clases()`. `sin_etiqueta` (de `contar_sin_etiqueta`) y `minimo_sin_etiqueta` activan la regla de los valores sin etiqueta;
    sin ellos solo cuentan las etiquetas. No cambia ninguna otra columna ni el orden de las filas."""
    import polars as pl

    con_sentido: dict[str, int] = {}
    for vid, esp in zip(categorias["var_id"].to_list(), categorias["es_especial"].to_list()):
        if esp == "no":
            con_sentido[vid] = con_sentido.get(vid, 0) + 1
    llaves = {a: set(ll or []) for a, ll in zip(archivos["archivo"].to_list(), archivos["llave"].to_list())}
    clases = []
    for r in variables.select("var_id", "archivo", "variable", "tipo_valor").iter_rows(named=True):
        a, v = r["archivo"], r["variable"]
        cur = curadas.get(v)
        exc = next((e for e in excepciones if _aplica(e, a, v)), None)
        if cur:
            k = cur.get("clase_indice") or cur["clase"]
        elif exc:
            k = exc["clase"]
        elif v in llaves.get(a, ()):
            k = "llave"
        elif r["tipo_valor"] == "texto":
            k = "texto"
        elif r["tipo_valor"] == "categorica":
            muchos = bool(sin_etiqueta and minimo_sin_etiqueta and sin_etiqueta.get(r["var_id"], 0) >= minimo_sin_etiqueta)
            k = "categoria" if con_sentido.get(r["var_id"], 0) >= 2 and not muchos else "medida"
        else:
            k = "medida"
        clases.append(k)
    return variables.with_columns(pl.Series("clase", clases, dtype=pl.String))


def conteos(variables) -> dict:
    """Cuántas variables hay por clase, en total y por tabla (archivo)."""
    total = {k: 0 for k in CLASES}
    por_tabla: dict[str, dict[str, int]] = {}
    for a, k in zip(variables["archivo"].to_list(), variables["clase"].to_list()):
        total[k] += 1
        por_tabla.setdefault(a, {c: 0 for c in CLASES})[k] += 1
    return {"total": total, "por_tabla": dict(sorted(por_tabla.items()))}


def informe(variables, excepciones: list[dict]) -> str:
    """Texto del informe (Markdown) para `evidencia/m1-05_clases.md`."""
    c = conteos(variables)
    t = c["total"]
    L = ["| Clase | Variables |", "|---|---|"] + [f"| {k} | {t[k]:,} |" for k in CLASES] + [f"| **Total** | **{sum(t.values()):,}** |", ""]
    L += ["## Por tabla", "", "| Tabla | " + " | ".join(CLASES) + " | Total |", "|---|" + "---|" * (len(CLASES) + 1)]
    for a, d in c["por_tabla"].items():
        L.append(f"| {a} | " + " | ".join(str(d[k]) for k in CLASES) + f" | {sum(d.values())} |")
    L += ["", "## Excepciones aplicadas", "", "| Variables | Tablas | Clase | Motivo |", "|---|---|---|---|"]
    for e in excepciones:
        arch = "todas" if e["archivos"] == "*" else ", ".join(e["archivos"])
        L.append(f"| {', '.join(e['variables'])} | {arch} | {e['clase']} | {e['motivo']} |")
    return "\n".join(L) + "\n"


def aplicar_al_indice(carpeta: Path, curadas: dict, excepciones: list[dict], ruta_informe: Path | None = None,
                      microdatos: Path | None = None, reglas: dict | None = None) -> dict:
    """`pap variables clasificar`: lee `variables.parquet`, `categorias.parquet` y `archivos.parquet` de `carpeta`, recalcula
    `clase` y reescribe **solo** `variables.parquet` (mismo orden y compresión que `indice.escribir`: dos corridas dan el mismo
    archivo). Las demás columnas, incluidas las que agregó `pap cuestionarios aplicar`, quedan como estaban. Devuelve los conteos."""
    import polars as pl

    carpeta = Path(carpeta)
    ruta = carpeta / "variables.parquet"
    if not ruta.exists():
        raise PapError(f"Falta {ruta}: corre antes `pap variables indexar`")
    v = pl.read_parquet(ruta)
    validar_excepciones(v, excepciones)
    cats = pl.read_parquet(carpeta / "categorias.parquet")
    minimo = (reglas or {}).get("min_valores_sin_etiqueta")
    sin = contar_sin_etiqueta(microdatos, v, cats) if (microdatos and minimo) else None
    nuevo = clasificar(v, cats, pl.read_parquet(carpeta / "archivos.parquet"), curadas, excepciones, sin, minimo).sort("var_id")
    tmp = ruta.with_name(f".{ruta.name}.tmp")
    nuevo.write_parquet(tmp, compression="zstd", compression_level=3)
    tmp.replace(ruta)
    if ruta_informe:
        Path(ruta_informe).write_text(informe(nuevo, excepciones), encoding="utf-8")
    return conteos(nuevo)
