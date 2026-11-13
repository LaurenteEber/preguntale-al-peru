"""Lector aislado de SAV y DTA (M0-04; diseño §6, tecnologias.md §5).

Se corre como subproceso (`python -I -m pap.inferencia.lector_aislado <spec.json>`) lanzado por
`pap.inferencia.almacen.ejecutar_aislado`, con topes de memoria, procesador y tiempo (C8). Lee **solo con pyreadstat**
(nunca `svy_io`), aplica las clases de `curados/inferencia/clases_columnas.yaml`, escribe el Parquet con DuckDB `COPY`
y calcula la huella de contenido. Deja un JSON con el resultado (o con el error).

Los perdidos se normalizan a nulo en la columna y su código queda en `perdidos` (lo recoge el manifiesto; M0-05 lo
lleva a `categorias.parquet`, columna `es_especial`):
- DTA: con `user_missing=True` los perdidos extendidos (.a–.z) llegan como texto «a»…«z» en una columna de objetos;
- SAV: llegan como los números de siempre y `meta.missing_ranges` dice cuáles son perdidos de usuario.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import yaml

from ..errores import PapError

INT32_MAX = 2**31 - 1


class ErrorConversion(PapError):
    """El archivo no se puede convertir sin perder o inventar datos."""


# ------------------------------------------------------------------ clases de columna

def cargar_clases(ruta: Path) -> dict:
    return yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))["columnas"]


def release_dta(ruta: Path) -> int | None:
    """Versión de formato del DTA (117, 118…) o None si no se reconoce. Desde la 118 es UTF-8; antes no se declara."""
    with open(ruta, "rb") as f:
        cab = f.read(64)
    if cab.startswith(b"<stata_dta>"):
        m = re.search(rb"<release>(\d+)</release>", cab)
        return int(m.group(1)) if m else None
    return cab[0] if cab else None


def _codificacion(formato: str, ruta: Path, sin_declarar: str) -> tuple[str | None, int | None]:
    if formato != "dta":
        return None, None
    rel = release_dta(ruta)
    return (None if rel is not None and rel >= 118 else sin_declarar), rel


# ------------------------------------------------------------------ perdidos

def _perdidos_dta(df, meta, acum: dict):
    """Objetos con códigos «a»…«z» (perdidos extendidos de Stata) → nulo en la columna; el código se cuenta."""
    import polars as pl

    for col in df.columns:
        if df.schema[col] != pl.Object:
            continue
        valores, nuevos = df[col].to_list(), []
        cuenta = Counter()
        for v in valores:
            if isinstance(v, str):
                if not re.fullmatch(r"[a-z]", v):
                    raise ErrorConversion(f"{col}: valor de texto inesperado en una columna numérica: {v!r}")
                cuenta[v] += 1
                nuevos.append(None)
            else:
                nuevos.append(v)
        df = df.with_columns(pl.Series(col, nuevos, dtype=pl.Float64))
        _sumar(acum, col, "stata_extendido", cuenta, meta.missing_user_values.get(col))
    return df


def _perdidos_sav(df, meta, acum: dict):
    """Valores dentro de `missing_ranges` (perdidos de usuario de SPSS) → nulo; cada código distinto se cuenta."""
    import polars as pl

    for col, rangos in (meta.missing_ranges or {}).items():
        if col not in df.columns or not rangos:
            continue
        mascara = pl.lit(False)
        for r in rangos:
            lo, hi = r["lo"], r["hi"]
            mascara = mascara | ((pl.col(col) == lo) if lo == hi or isinstance(lo, str)
                                 else (pl.col(col) >= lo) & (pl.col(col) <= hi))
        presentes = df.filter(mascara.fill_null(False))[col]
        cuenta = Counter(str(v) for v in presentes.to_list())
        if cuenta:
            df = df.with_columns(pl.when(mascara.fill_null(False)).then(None).otherwise(pl.col(col)).alias(col))
        _sumar(acum, col, "spss_usuario", cuenta, [{"lo": r["lo"], "hi": r["hi"]} for r in rangos])
    return df


def _sumar(acum: dict, col: str, origen: str, cuenta: Counter, declarados) -> None:
    e = acum.setdefault(col, {"origen": origen, "declarados": declarados or [], "conteo": {}})
    for k, n in cuenta.items():
        e["conteo"][k] = e["conteo"].get(k, 0) + n


# ------------------------------------------------------------------ clases

def _normalizar(df, clases: dict, anio: int, formato: str, meta, perdidos: dict):
    """Pasa un bloque leído al esquema final: nombres en MAYÚSCULAS, clases, HHID derivado y `anio`."""
    import polars as pl

    df = _perdidos_dta(df, meta, perdidos) if formato == "dta" else _perdidos_sav(df, meta, perdidos)
    mayus = [c.upper() for c in df.columns]
    repetidos = [c for c, n in Counter(mayus).items() if n > 1]
    if repetidos:
        raise ErrorConversion(f"columnas repetidas al pasar a mayúsculas: {repetidos}")
    df = df.rename(dict(zip(df.columns, mayus)))
    if "ANIO" in mayus:
        raise ErrorConversion("el archivo ya trae una columna ANIO, que choca con la columna `anio` del almacén")

    crudos = {c: df[c] for c in df.columns}      # valores sin recortar: de aquí se deriva
    salidas = []
    for col in df.columns:
        cl = clases.get(col, {})
        clase, s = cl.get("clase"), df[col]
        if clase in ("llave", "geo"):
            s = _texto_fijo(s, col, cl.get("ancho"))
        elif clase in ("categoria", "diseno"):
            s = _entero(s, col)
        elif clase in ("medida", "peso") or (clase is None and (s.dtype.is_numeric() or s.dtype == pl.Null)):
            s = _doble(s, col)
        salidas.append(s.alias(col))
    for col, cl in clases.items():
        for derivada, regla in (cl.get("deriva") or {}).items():
            if col not in crudos:
                continue
            crudo = crudos[col]
            if crudo.dtype not in (pl.String, pl.Null):
                raise ErrorConversion(f"{col}: se esperaba texto para derivar {derivada} y llegó {crudo.dtype}")
            n = int(regla["quitar_final"])
            largo = crudo.cast(pl.String).str.len_chars()
            if crudo.cast(pl.String).is_not_null().any() and (largo.drop_nulls() <= n).any():
                raise ErrorConversion(f"{col}: hay valores de {n} caracteres o menos; no se puede derivar {derivada}")
            der = crudo.cast(pl.String).str.slice(0, largo - n)
            der = _texto_fijo(der, derivada, clases.get(derivada, {}).get("ancho"))
            if derivada in df.columns:
                iguales = (der.fill_null("") == salidas[df.columns.index(derivada)].fill_null(""))
                if not iguales.all():
                    raise ErrorConversion(f"{derivada} derivado de {col} no coincide con la columna {derivada} del "
                                          f"archivo en {int((~iguales).sum())} fila(s)")
            else:
                salidas.append(der.alias(derivada))
    out = pl.DataFrame(salidas)
    return out.with_columns(pl.lit(anio, dtype=pl.Int32).alias("anio"))


def _texto_fijo(s, col: str, ancho: int | None):
    """Texto recortado solo por fuera (espacios internos y ceros intactos) con el ancho verificado."""
    import polars as pl

    if s.dtype not in (pl.String, pl.Null):
        raise ErrorConversion(f"{col}: llave o geo que llega como {s.dtype}, no como texto; se perderían los ceros")
    s = s.cast(pl.String).str.strip_chars()
    if ancho is not None:
        malos = s.drop_nulls().str.len_chars() != ancho
        if malos.any():
            ej = s.drop_nulls().filter(malos).head(3).to_list()
            raise ErrorConversion(f"{col}: ancho distinto de {ancho} en {int(malos.sum())} valor(es), p. ej. {ej}; "
                                  "no se corta ni se rellena")
    return s


def _entero(s, col: str):
    import polars as pl

    if s.dtype == pl.Null:
        return s.cast(pl.Int32)
    if not (s.dtype.is_numeric()):
        raise ErrorConversion(f"{col}: categoría que llega como {s.dtype}, no como número")
    x = s.cast(pl.Float64).drop_nulls()
    if x.is_nan().any() or (x != x.floor()).any() or (x.abs() > INT32_MAX).any():
        raise ErrorConversion(f"{col}: categoría con valores que no son enteros de 32 bits; no se redondea")
    return s.cast(pl.Float64).cast(pl.Int32)


def _doble(s, col: str):
    import polars as pl

    if s.dtype != pl.Null and not s.dtype.is_numeric():
        raise ErrorConversion(f"{col}: medida que llega como {s.dtype}, no como número")
    return s.cast(pl.Float64)


# ------------------------------------------------------------------ lectura y escritura

def _bloques(spec: dict, formato: str, codificacion: str | None):
    import pyreadstat

    leer = pyreadstat.read_dta if formato == "dta" else pyreadstat.read_sav
    # Las opciones son fijas (tecnologias.md §5): sin user_missing los perdidos de usuario se confundirían con «no se preguntó».
    opc = dict(user_missing=True, apply_value_formats=False, output_format="polars", encoding=codificacion)
    ruta = spec["entrada"]
    if Path(ruta).stat().st_size > int(spec["bloques_desde_bytes"]):
        yield from pyreadstat.read_file_in_chunks(leer, ruta, chunksize=int(spec["bloques_filas"]), **opc)
    else:
        yield leer(ruta, **opc)


def _rss_max_bytes() -> int:
    import resource

    m = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return m if sys.platform == "darwin" else m * 1024    # macOS lo da en bytes; Linux, en KB


def leer_y_escribir(spec: dict) -> dict:
    """Lee `spec['entrada']` y escribe `spec['salida']` (Parquet). Devuelve el resultado que va al manifiesto."""
    import duckdb
    import polars as pl

    from .almacen import huella_contenido_v1, versiones

    formato = spec["formato"]
    codificacion, release = _codificacion(formato, Path(spec["entrada"]), spec["codificacion_sin_declarar"])
    clases = cargar_clases(spec["clases"])
    perdidos: dict = {}
    esquema, filas, bloques = None, 0, 0
    salida = Path(spec["salida"])
    t0 = time.monotonic()
    con = duckdb.connect(str(spec["base_temporal"]))
    con.execute(f"SET memory_limit='{int(spec['duckdb_memoria_mb'])}MB'")
    for df, meta in _bloques(spec, formato, codificacion):
        bloques += 1
        out = _normalizar(df, clases, int(spec["anio"]), formato, meta, perdidos)
        if esquema is None:
            esquema = out.schema
            con.register("bloque", out.to_arrow())
            con.execute("CREATE TABLE t AS SELECT * FROM bloque")
        else:
            if out.schema != esquema:
                raise ErrorConversion(f"el bloque {bloques} cambia el esquema: {out.schema} ≠ {esquema}")
            con.register("bloque", out.to_arrow())
            con.execute("INSERT INTO t SELECT * FROM bloque")
        con.unregister("bloque")
        filas += out.height
        del df, out
    if esquema is None or filas == 0:
        raise ErrorConversion("el archivo no tiene filas")
    q = lambda p: str(p).replace("'", "''")
    con.execute(f"COPY t TO '{q(salida)}' (FORMAT parquet, COMPRESSION {spec['parquet_compresion']}, "
                f"COMPRESSION_LEVEL {int(spec['parquet_nivel'])}, ROW_GROUP_SIZE {int(spec['parquet_grupo_filas'])})")
    columnas = [{"nombre": n, "tipo": t, "clase": (clases.get(n) or {}).get("clase")}
                for n, t, *_ in con.execute("DESCRIBE t").fetchall()]
    con.close()
    seg_conversion = time.monotonic() - t0
    t1 = time.monotonic()
    huella = huella_contenido_v1(salida)
    seg_huella = time.monotonic() - t1
    return {"filas": filas, "columnas": columnas, "perdidos": perdidos, "huella_contenido_v1": huella,
            "segundos_conversion": round(seg_conversion, 3), "segundos_huella": round(seg_huella, 3),
            "rss_max_bytes": _rss_max_bytes(), "bytes_parquet": salida.stat().st_size,
            "leido_en_bloques": bloques > 1 or Path(spec["entrada"]).stat().st_size > int(spec["bloques_desde_bytes"]),
            "codificacion": codificacion or "declarada por el archivo", "release_dta": release,
            "versiones": versiones()}


# ------------------------------------------------------------------ metadatos para el índice (M0-05)

def _clave_json(v):
    """Código de una etiqueta de valor: entero si lo es (1.0 → 1); texto o decimal se conservan."""
    return int(v) if isinstance(v, float) and v == int(v) else v


def leer_metadatos(spec: dict) -> dict:
    """Metadatos de un SAV/DTA para `pap variables indexar`: `metadataonly=True` **y** `user_missing=True` (sin lo
    segundo `missing_ranges` sale vacío; tecnologias.md §5), sin tope de etiquetas. Las columnas conservan el orden
    del archivo. Devuelve solo tipos de JSON (los códigos de las etiquetas de valor, como pares [código, etiqueta])."""
    import pyreadstat

    formato = spec["formato"]
    codificacion, release = _codificacion(formato, Path(spec["entrada"]), spec["codificacion_sin_declarar"])
    leer = pyreadstat.read_dta if formato == "dta" else pyreadstat.read_sav
    _, meta = leer(spec["entrada"], metadataonly=True, user_missing=True, encoding=codificacion)
    cols = []
    for nombre in meta.column_names:
        conjunto = meta.variable_to_label.get(nombre)
        etiquetas = meta.variable_value_labels.get(nombre) or {}
        cols.append({
            "nombre": nombre,
            "etiqueta": meta.column_names_to_labels.get(nombre),
            "formato": meta.original_variable_types.get(nombre),
            "conjunto_etiquetas": conjunto,
            "etiquetas_valor": [[_clave_json(k), v] for k, v in etiquetas.items()],
            "rangos_perdidos": [{"lo": r["lo"], "hi": r["hi"]} for r in (meta.missing_ranges or {}).get(nombre, [])],
            "perdidos_usuario": [_clave_json(v) if not isinstance(v, str) else v
                                 for v in (meta.missing_user_values or {}).get(nombre, [])],
        })
    return {"filas": int(meta.number_rows), "columnas": cols, "codificacion": codificacion or "declarada por el archivo",
            "release_dta": release, "versiones": versiones_lector()}


# ------------------------------------------------------------------ texto de PDF (M1-04)

def leer_pdf(spec: dict) -> dict:
    """Palabras con su posición (y, si se pide, las tablas) de cada página de un PDF, solo con pdfplumber. Cada palabra es
    [texto, x0, arriba]; las coordenadas van redondeadas a 0,1 punto. Las líneas y el diseño los interpreta quien llama."""
    import pdfplumber

    try:
        with pdfplumber.open(spec["entrada"]) as pdf:
            tope = int(spec.get("max_paginas") or 0)
            paginas = []
            for n, pag in enumerate(pdf.pages, start=1):
                if tope and n > tope:
                    break
                palabras = [[w["text"], round(float(w["x0"]), 1), round(float(w["top"]), 1)] for w in pag.extract_words()]
                tablas = pag.extract_tables() if spec.get("tablas") else []
                paginas.append({"n": n, "ancho": round(float(pag.width), 1), "alto": round(float(pag.height), 1),
                                "palabras": palabras, "tablas": tablas})
    except MemoryError:
        raise
    except Exception as e:           # pdfminer lanza muchas clases distintas ante un PDF dañado
        raise ErrorConversion(f"no se pudo leer el PDF ({type(e).__name__})") from None
    return {"paginas": paginas, "versiones": {"pdfplumber": pdfplumber.__version__, "python": sys.version.split()[0]}}


def versiones_lector() -> dict:
    from .almacen import versiones

    return versiones()


# ------------------------------------------------------------------ punto de entrada del subproceso

def main(argv: list[str]) -> int:
    spec = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    resultado_ruta = Path(spec["resultado"])
    try:
        modo = spec.get("modo")
        res = leer_metadatos(spec) if modo == "metadatos" else leer_pdf(spec) if modo == "pdf" else leer_y_escribir(spec)
    except ErrorConversion as e:
        resultado_ruta.write_text(json.dumps({"error": str(e)}, ensure_ascii=False), encoding="utf-8")
        return 3
    except MemoryError:
        resultado_ruta.write_text(json.dumps({"error": "sin memoria dentro del límite del lector"}), encoding="utf-8")
        return 4
    resultado_ruta.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
