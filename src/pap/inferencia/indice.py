"""Índice de variables de las encuestas (M0-05; diseño §7.1–7.3 y anexo A; tecnologias.md §5).

No confundir con `pap.indice`, que es el índice DuckDB de los crudos: este es el mapa de las variables de los microdatos.
Se importa con su ruta completa (`pap.inferencia.indice`).

`pap variables indexar --encuesta ENDES --anio 2024` recorre **todos** los DTA/SAV de los ZIP registrados con `pyreadstat`
(`metadataonly=True` y `user_missing=True`, sin tope de etiquetas), cada uno en el subproceso aislado de M0-04
(`lector_aislado.leer_metadatos`, con `abrir_zip_seguro`), y escribe en `biblioteca/variables/`:

- `archivos.parquet`: `encuesta`, `anio`, `archivo`, `unidad`, `llave` (lista de columnas), `n_filas`, `formato`,
  `huella_datos` (la del manifiesto de M0-04) y, además del anexo A, `zip`, `miembro`, `n_variables` y `relaciones`
  (uniones declaradas, en JSON). `unidad`, `llave` y `relaciones` salen de `curados/inferencia/archivos_endes_<año>.yaml`.
- `variables.parquet`: los campos del §7.2 con la llave `var_id` = `encuesta·año·archivo·código` (punto medio), más
  `posicion` (orden de la columna en el Parquet), `formato_origen`, `derivada_de`, `n_categorias` y `controles` (los
  controles del §7.3 que saltaron: la variable queda marcada para revisión). Hasta M1 quedan vacíos: `rango_valido`,
  `rol_faltante`, `texto_pregunta`, `universo_cuestionario`, `ventana_referencia`, `sujeto`, `informante`, `modo`,
  `tipo_origen`, `universo_corto` y `concepto_id`. `clase` viene de `curados/inferencia/clases_columnas.yaml` (vacía si la
  columna no está allí). `estado` es siempre `propuesto`.
- `categorias.parquet`: `var_id`, `codigo`, `etiqueta_original`, `etiqueta_curada`, `es_especial` (`propuesto` o `no`),
  `rol_faltante` (vacío hasta M1) y, además, `origen_especial` (`declarado`, `etiqueta` o ambos), `frecuencia`,
  `proporcion_filas` y `controles`.

**Variables = columnas del Parquet menos `anio`.** El índice incluye las columnas derivadas (HHID derivado de CASEID, ver
`clases_columnas.yaml`), con `derivada_de`. Nombres de variable en MAYÚSCULAS.

**Códigos especiales** (`es_especial = propuesto`; los confirma M1): (1) los que declara el archivo: `missing_ranges` de
SPSS, perdidos de usuario de Stata y los códigos que el manifiesto de M0-04 recogió en `perdidos.<COL>`; (2) los que
tienen etiqueta «no sabe», «no responde» o «no aplica», o un código de `indice.especiales_codigos` (98, 99…) con etiqueta.

**Etiquetas:** `etiqueta_curada` = ftfy + NFC + espacios normalizados (+ relectura de cp850 si aparece «Ni¤o»); la original
se conserva. **Controles** (§7.3): corren en 2024 la etiqueta vacía, el mojibake y la frecuencia de los códigos especiales
(se cuentan en el Parquet o, si el valor quedó nulo, en el manifiesto). Los controles que necesitan más de un año, o el
universo del cuestionario (M1), están programados aquí (`control_etiquetas_entre_anios`, `control_frecuencia_entre_anios`,
`control_universo`) y probados con datos sintéticos.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..config import Rutas
from ..errores import PapError
from ..util import sha256
from ..zip_seguro import RUTA_PARAMETROS, abrir_zip_seguro
from .almacen import Parametros, _insumo, carpeta_salida, ejecutar_aislado, nombre_parquet

RAIZ_REPO = Path(__file__).resolve().parents[3]
RUTA_CLASES = RAIZ_REPO / "curados" / "inferencia" / "clases_columnas.yaml"
SEP_ID = "·"
CONTROLES = ("etiqueta_vacia", "mojibake_reparado", "mojibake_sin_reparar", "etiqueta_acento_grave",
             "etiqueta_posible_corte", "especial_declarado_sin_filas")


def carpeta_indice(rutas: Rutas) -> Path:
    return rutas.raiz / "biblioteca" / "variables"


def ruta_curada_archivos(encuesta: str, anio: int, raiz: Path = RAIZ_REPO) -> Path:
    return raiz / "curados" / "inferencia" / f"archivos_{encuesta.lower()}_{anio}.yaml"


# ------------------------------------------------------------------ parámetros

@dataclass(frozen=True)
class ParametrosIndice:
    """`indice.*` de curados/inferencia/parametros.yaml (ningún valor fijo en el código)."""
    especiales_textos: tuple[str, ...]
    especiales_codigos: tuple[int, ...]
    universo_coincidencia_min: float
    frecuencia_razon: float
    frecuencia_cambio_min_pp: float
    vocales_acento_grave: str
    etiqueta_largo_posible_corte: int

    @classmethod
    def desde_yaml(cls, ruta: Path = RUTA_PARAMETROS) -> "ParametrosIndice":
        c = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))["indice"]
        v = lambda k: c[k]["valor"]
        return cls(especiales_textos=tuple(v("especiales_textos")), especiales_codigos=tuple(int(x) for x in v("especiales_codigos")),
                   universo_coincidencia_min=float(v("universo_coincidencia_min")),
                   frecuencia_razon=float(v("frecuencia_especial_razon")),
                   frecuencia_cambio_min_pp=float(v("frecuencia_especial_cambio_min_pp")),
                   vocales_acento_grave=str(v("vocales_acento_grave")),
                   etiqueta_largo_posible_corte=int(v("etiqueta_largo_posible_corte")))


@dataclass(frozen=True)
class Hallazgo:
    """Un control del §7.3 que saltó: marca la variable (o la categoría) para revisión."""
    control: str
    objeto: str          # var_id, o var_id + «=» + código
    detalle: str


# ------------------------------------------------------------------ etiquetas

def normalizar_texto(t: str | None) -> str:
    """Minúsculas, sin acentos y con espacios simples: para comparar etiquetas."""
    d = unicodedata.normalize("NFD", (t or "").casefold())
    return " ".join("".join(c for c in d if not unicodedata.combining(c)).split())


_DOS = "¤¥¢£"     # ñ, Ñ, ó y ú de cp850 leídas como cp1252 (en español no se usan solas)
_BIEN = "áéíóúñÁÉÍÓÚÑü"
# Carácter cp1252 → letra cp850 que representa. «¡» (í) solo se cambia detrás de una letra: delante de una palabra es el
# signo de exclamación. «¿», «¡» de apertura y lo demás quedan como están (H05-1: releer todo el texto como cp850
# convertía «¿» en «┐»).
_DOS_LETRA = {"¤": "ñ", "¥": "Ñ", "¢": "ó", "£": "ú", "‚": "é"}
_DOS_TRAS_LETRA = {"¡": "í"}


def reparar_dos(texto: str) -> str:
    """El mojibake de DOS (cp850: «Ni¤o», «Educaci¢n») no lo repara ftfy. Si el texto trae alguno de ¤ ¥ ¢ £, se
    cambia cada carácter de DOS pegado a una letra por la letra que representa (¤ ¥ ¢ £ ‚ a cualquier lado, ¡ solo
    detrás); el resto del texto no se toca. Un texto que ya trae vocales con tilde bien escritas es ambiguo y no se toca
    (el control de mojibake lo marca); tampoco uno que no es cp1252."""
    if not any(c in texto for c in _DOS) or any(c in texto for c in _BIEN):
        return texto
    try:
        texto.encode("cp1252")
    except UnicodeError:
        return texto
    letra = lambda i: 0 <= i < len(texto) and (texto[i].isalpha() and texto[i] not in _DOS_LETRA)
    salida = []
    for i, c in enumerate(texto):
        if c in _DOS_LETRA and (letra(i - 1) or letra(i + 1)):
            salida.append(_DOS_LETRA[c])
        elif c in _DOS_TRAS_LETRA and letra(i - 1):
            salida.append(_DOS_TRAS_LETRA[c])
        else:
            salida.append(c)
    return "".join(salida)


def curar_etiqueta(original: str | None) -> tuple[str, tuple[str, ...]]:
    """`etiqueta_curada` y qué se le hizo: `mojibake` (ftfy o cp850), `espacios`, `unicode` (otro cambio de ftfy o NFC).
    ftfy sin cambiar comillas tipográficas ni entidades HTML (la etiqueta es del INEI: se arregla la codificación, no el estilo)."""
    import ftfy

    if original is None:
        return "", ()
    cfg = ftfy.TextFixerConfig(uncurl_quotes=False, unescape_html=False, normalization="NFC")
    ex = ftfy.fix_and_explain(original, cfg)
    t, hechas = ex.text, []
    if any(paso.action in ("encode", "decode", "transcode") for paso in ex.explanation or []):
        hechas.append("mojibake")
    t2 = reparar_dos(t)
    if t2 != t:
        hechas.append("mojibake")
    t = unicodedata.normalize("NFC", t2)
    limpio = " ".join(t.replace("\xa0", " ").split())
    if limpio != t:
        hechas.append("espacios")
    if limpio != original and not hechas:
        hechas.append("unicode")
    return limpio, tuple(dict.fromkeys(hechas))


_MOJIBAKE = re.compile("[¤¥¢£�\u0080-\u009f─-▟]|Ã[\u0080-¿]|Â[ -¿]|â€|Ã©|Ã±")


def tiene_mojibake(texto: str) -> bool:
    """¿Quedó mojibake en el texto? Patrones típicos (UTF-8 leído como cp1252, cp850, caracteres de control) y el
    detector de ftfy. El control de 2024 exige 0 tras la reparación."""
    import ftfy.badness

    return bool(_MOJIBAKE.search(texto)) or ftfy.badness.is_bad(texto)


# ------------------------------------------------------------------ códigos

def codigo_texto(c) -> str:
    """Forma única del código: 98, 98.0 y «98.0» → «98»; 1.5 → «1.5»; «a» (perdido extendido de Stata) → «a»."""
    if isinstance(c, str):
        try:
            c = float(c)
        except ValueError:
            return c
    if isinstance(c, float) and c == int(c):
        return str(int(c))
    return str(c)


def _numero(c) -> float | None:
    try:
        return float(c)
    except (TypeError, ValueError):
        return None


def _declarados(col: dict, perdidos_manifiesto: dict | None) -> tuple[set[str], list[dict], dict[str, int]]:
    """Códigos sueltos, rangos y conteos que declara el archivo (metadatos) o recogió el manifiesto de M0-04."""
    sueltos: set[str] = {codigo_texto(c) for c in col.get("perdidos_usuario") or []}
    rangos: list[dict] = []
    conteo: dict[str, int] = {}
    for r in col.get("rangos_perdidos") or []:
        (sueltos.add(codigo_texto(r["lo"])) if r["lo"] == r["hi"] else rangos.append({"lo": r["lo"], "hi": r["hi"]}))
    if perdidos_manifiesto:
        for d in perdidos_manifiesto.get("declarados") or []:
            if isinstance(d, dict):
                (sueltos.add(codigo_texto(d["lo"])) if d["lo"] == d["hi"] else
                 rangos.append({"lo": d["lo"], "hi": d["hi"]}))
            else:
                sueltos.add(codigo_texto(d))
        for k, n in (perdidos_manifiesto.get("conteo") or {}).items():
            sueltos.add(codigo_texto(k))
            conteo[codigo_texto(k)] = conteo.get(codigo_texto(k), 0) + int(n)
    vistos, unicos = set(), []
    for r in rangos:
        if (r["lo"], r["hi"]) not in vistos:
            vistos.add((r["lo"], r["hi"]))
            unicos.append(r)
    return sueltos, unicos, conteo


def _en_rango(codigo: str, rangos: list[dict]) -> bool:
    n = _numero(codigo)
    return n is not None and any(isinstance(r["lo"], (int, float)) and r["lo"] <= n <= r["hi"] for r in rangos)


def proponer_especiales(col: dict, perdidos_manifiesto: dict | None, p: ParametrosIndice) -> list[dict]:
    """Códigos especiales propuestos de una variable: [{codigo, etiqueta, origen, declarado_conteo?}], origen ∈
    declarado | etiqueta | declarado+etiqueta. Son propuestas (`es_especial = propuesto`): las confirma M1."""
    sueltos, rangos, conteo = _declarados(col, perdidos_manifiesto)
    textos = [normalizar_texto(t) for t in p.especiales_textos]
    codigos = {str(c) for c in p.especiales_codigos}
    salida: list[dict] = []
    con_etiqueta: set[str] = set()
    for cod, etq in col.get("etiquetas_valor") or []:
        c = codigo_texto(cod)
        con_etiqueta.add(c)
        origen = []
        if c in sueltos or _en_rango(c, rangos):
            origen.append("declarado")
        n = normalizar_texto(etq)
        if any(t in n for t in textos) or c in codigos:
            origen.append("etiqueta")
        if origen:
            salida.append({"codigo": c, "etiqueta": etq, "origen": "+".join(origen)})
    for c in sorted(sueltos - con_etiqueta):       # declarado y sin etiqueta de valor (p. ej. .a de Stata)
        salida.append({"codigo": c, "etiqueta": "", "origen": "declarado"})
    for r in rangos:                                # rango de SPSS: se anota; sus códigos con etiqueta ya salieron arriba
        salida.append({"codigo": f"{r['lo']}..{r['hi']}", "etiqueta": "", "origen": "declarado", "rango": True})
    for s in salida:
        if s["codigo"] in conteo:
            s["declarado_conteo"] = conteo[s["codigo"]]
    return salida


# ------------------------------------------------------------------ construcción

def _tipo_valor(col: dict) -> str:
    f = col.get("formato") or ""
    if re.fullmatch(r"%-?\d+s", f) or f.startswith("A"):
        return "texto"
    if col.get("etiquetas_valor"):
        return "categorica"
    return "fecha" if f.startswith("%t") or f.startswith("%-t") else "numerica"


def _grupos(nombres: Sequence[str]) -> dict[str, str | None]:
    """Batería por prefijo (letras + dígitos: SH61A…SH61S → SH61; PS92_1A → PS92); solo si hay 2 o más en el archivo."""
    raiz = {n: (m.group(1) if (m := re.match(r"^([A-Z]+\d+)", n)) else None) for n in nombres}
    cuenta: dict[str, int] = {}
    for r in raiz.values():
        if r:
            cuenta[r] = cuenta.get(r, 0) + 1
    return {n: (r if r and cuenta[r] >= 2 else None) for n, r in raiz.items()}


def _columna_derivada(nombre: str, desde: str) -> dict:
    return {"nombre": nombre, "etiqueta": None, "formato": "%9s", "etiquetas_valor": [], "rangos_perdidos": [],
            "perdidos_usuario": [], "derivada_de": desde}


def variables_del_archivo(cols: list[dict], clases: dict) -> list[dict]:
    """Columnas del archivo (nombres en MAYÚSCULAS) y las derivadas de `clases_columnas.yaml`, en el orden del Parquet."""
    salida = [dict(c, nombre=c["nombre"].upper()) for c in cols]
    nombres = [c["nombre"] for c in salida]
    repetidos = sorted({n for n in nombres if nombres.count(n) > 1})
    if repetidos:
        raise PapError(f"columnas repetidas al pasar a mayúsculas: {repetidos}")
    for origen, cl in clases.items():
        for derivada in (cl.get("deriva") or {}):
            if origen in nombres and derivada not in nombres:
                salida.append(_columna_derivada(derivada, origen))
                nombres.append(derivada)
    return salida


def _revisar_curado(archivos: dict[str, list[str]], curado: dict) -> None:
    """La tabla curada de archivos, llaves y uniones tiene que cubrir exactamente los archivos indexados."""
    cur = curado["archivos"]
    if set(cur) != set(archivos):
        raise PapError(f"archivos_*.yaml no coincide con los archivos indexados: sobran {sorted(set(cur) - set(archivos))}, "
                       f"faltan {sorted(set(archivos) - set(cur))}")
    for a, e in cur.items():
        faltan = [c for c in e["llave"] if c not in archivos[a]]
        if faltan:
            raise PapError(f"{a}: la llave declarada usa columnas que el archivo no tiene: {faltan}")
    for r in curado.get("relaciones") or []:
        for lado, otro, i in (("hijo", "padre", 0), ("padre", "hijo", 1)):
            a = r[lado]
            if a not in archivos:
                raise PapError(f"relación {r['hijo']} → {r['padre']}: no existe el archivo {a}")
            faltan = [par[i] for par in r["por"] if par[i] not in archivos[a]]
            if faltan:
                raise PapError(f"relación {r['hijo']} → {r['padre']}: {a} no tiene {faltan}")


@dataclass
class Indice:
    archivos: "pl.DataFrame"
    variables: "pl.DataFrame"
    categorias: "pl.DataFrame"
    hallazgos: list[Hallazgo] = field(default_factory=list)


def _esquemas():
    import polars as pl

    S, L = pl.String, pl.List(pl.String)
    archivos = {"encuesta": S, "anio": pl.Int32, "archivo": S, "unidad": S, "llave": L, "n_filas": pl.Int64, "formato": S,
                "huella_datos": S, "zip": S, "miembro": S, "n_variables": pl.Int32, "relaciones": S}
    variables = {"var_id": S, "encuesta": S, "anio": pl.Int32, "archivo": S, "variable": S, "posicion": pl.Int32,
                 "clase": S, "tipo_valor": S, "formato_origen": S, "rango_valido": S, "codigos_especiales": S,
                 "rol_faltante": S, "etiqueta_original": S, "etiqueta_curada": S, "texto_pregunta": S,
                 "universo_cuestionario": S, "ventana_referencia": S, "sujeto": S, "informante": S, "modo": S,
                 "grupo": S, "tipo_origen": S, "universo_corto": S, "concepto_id": S, "estado": S,
                 "derivada_de": S, "n_categorias": pl.Int32, "controles": L}
    categorias = {"var_id": S, "codigo": S, "etiqueta_original": S, "etiqueta_curada": S, "es_especial": S,
                  "rol_faltante": S, "origen_especial": S, "frecuencia": pl.Int64, "proporcion_filas": pl.Float64,
                  "controles": L}
    return archivos, variables, categorias


def contar_codigos(parquet: Path, pedidos: dict[str, list[str]]) -> dict[tuple[str, str], int]:
    """Cuántas filas tienen cada código en cada columna del Parquet (una sola pasada con DuckDB). Los códigos van como
    texto («98»); en columnas numéricas se comparan como número, en las de texto como texto."""
    import duckdb

    if not pedidos:
        return {}
    ruta = str(parquet).replace("'", "''")
    con = duckdb.connect()
    tipos = {n: t for n, t, *_ in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{ruta}')").fetchall()}
    exprs, claves = [], []
    for col, codigos in pedidos.items():
        if col not in tipos:
            raise PapError(f"{Path(parquet).name}: no tiene la columna {col}")
        x = '"' + col.replace('"', '""') + '"'
        for c in codigos:
            if tipos[col] == "VARCHAR":
                lit = "'" + c.replace("'", "''") + "'"
            elif _numero(c) is None:
                continue                    # un código de texto («a») en una columna numérica no aparece: el valor es nulo
            else:
                lit = repr(float(c))
            exprs.append(f"count(*) FILTER (WHERE {x} = {lit})")
            claves.append((col, c))
    if not exprs:
        return {}
    fila = con.execute(f"SELECT {', '.join(exprs)} FROM read_parquet('{ruta}')").fetchone()
    return dict(zip(claves, (int(n) for n in fila)))


def construir(encuesta: str, anio: int, metas: dict[str, dict], manifiesto: dict, clases: dict, curado: dict,
              p: ParametrosIndice, *, parquet_dir: Path | None = None) -> Indice:
    """Arma las tres tablas. `metas[archivo]` = {filas, columnas, formato, miembro, zip} (lo que devuelve el lector de
    metadatos más el origen); `manifiesto` = el de M0-04. Con `parquet_dir` cuenta en los Parquet la frecuencia de los
    códigos especiales cuyo valor sigue en la columna."""
    import polars as pl

    esq_a, esq_v, esq_c = _esquemas()
    man = manifiesto["archivos"]
    if set(man) != set(metas):
        raise PapError(f"el manifiesto de M0-04 y los ZIP no tienen los mismos archivos: sobran en el manifiesto "
                       f"{sorted(set(man) - set(metas))}, faltan {sorted(set(metas) - set(man))}")
    por_archivo = {a: variables_del_archivo(m["columnas"], clases) for a, m in metas.items()}
    _revisar_curado({a: [c["nombre"] for c in cs] for a, cs in por_archivo.items()}, curado)

    filas_a, filas_v, filas_c, hallazgos = [], [], [], []
    for archivo in sorted(metas):
        m, cs = metas[archivo], por_archivo[archivo]
        if m["filas"] != man[archivo]["filas"]:
            raise PapError(f"{archivo}: el ZIP tiene {m['filas']} filas y el Parquet de M0-04 {man[archivo]['filas']}")
        cols_man = [c["nombre"] for c in man[archivo]["columnas"] if c["nombre"] != "anio"]
        if [c["nombre"] for c in cs] != cols_man:
            raise PapError(f"{archivo}: las variables del índice no son las columnas del Parquet de M0-04 "
                           f"(sobran {sorted(set(c['nombre'] for c in cs) - set(cols_man))}, "
                           f"faltan {sorted(set(cols_man) - set(c['nombre'] for c in cs))})")
        cur = curado["archivos"][archivo]
        rels = [r for r in curado.get("relaciones") or [] if r["hijo"] == archivo]
        filas_a.append({"encuesta": encuesta, "anio": anio, "archivo": archivo, "unidad": cur["unidad"],
                        "llave": list(cur["llave"]), "n_filas": m["filas"], "formato": m["formato"],
                        "huella_datos": man[archivo]["huella_datos"], "zip": m["zip"], "miembro": m["miembro"],
                        "n_variables": len(cs),
                        "relaciones": json.dumps([{"con": r["padre"], "por": r["por"], "cardinalidad": r["cardinalidad"]}
                                                  for r in rels], ensure_ascii=False)})
        grupos = _grupos([c["nombre"] for c in cs])
        pedidos: dict[str, list[str]] = {}
        especiales_por_var: dict[str, list[dict]] = {}
        for pos, c in enumerate(cs, start=1):
            vid = SEP_ID.join((encuesta, str(anio), archivo, c["nombre"]))
            cl = clases.get(c["nombre"], {})
            especiales = proponer_especiales(c, (man[archivo].get("perdidos") or {}).get(c["nombre"]), p)
            especiales_por_var[c["nombre"]] = especiales
            for s in especiales:
                if "rango" not in s and "declarado_conteo" not in s:
                    pedidos.setdefault(c["nombre"], []).append(s["codigo"])     # lo declarado con conteo ya no está en el Parquet
            derivada = c.get("derivada_de")
            if derivada:
                original, curada, hechas = None, f"Identificación del hogar, derivada de {derivada} (sin el número de línea)", ()
            else:
                original = c.get("etiqueta")
                curada, hechas = curar_etiqueta(original)
            ctl = _controles_etiqueta(original, curada, hechas, p, es_variable=True, derivada=bool(derivada))
            for k in ctl:
                hallazgos.append(Hallazgo(k, vid, f"etiqueta: {original!r}"))
            filas_v.append({
                "var_id": vid, "encuesta": encuesta, "anio": anio, "archivo": archivo, "variable": c["nombre"], "posicion": pos,
                "clase": cl.get("clase_indice") or cl.get("clase"), "tipo_valor": "texto" if derivada else _tipo_valor(c),
                "formato_origen": c.get("formato"), "rango_valido": None,
                "codigos_especiales": json.dumps(especiales, ensure_ascii=False),
                "rol_faltante": None, "etiqueta_original": original, "etiqueta_curada": curada, "texto_pregunta": None,
                "universo_cuestionario": None, "ventana_referencia": None, "sujeto": None, "informante": None, "modo": None,
                "grupo": grupos[c["nombre"]], "tipo_origen": None, "universo_corto": None, "concepto_id": None,
                "estado": "propuesto", "derivada_de": derivada, "n_categorias": len(c.get("etiquetas_valor") or []),
                "controles": ctl})
        frecuencias = (contar_codigos(Path(parquet_dir) / man[archivo]["parquet"], pedidos) if parquet_dir else {})
        for c in cs:
            vid = SEP_ID.join((encuesta, str(anio), archivo, c["nombre"]))
            esp = {s["codigo"]: s for s in especiales_por_var[c["nombre"]] if "rango" not in s}
            vistos = set()
            for cod, etq in c.get("etiquetas_valor") or []:
                cod = codigo_texto(cod)
                vistos.add(cod)
                filas_c.append(_fila_categoria(vid, cod, etq, esp.get(cod), frecuencias.get((c["nombre"], cod)),
                                               m["filas"], p, hallazgos))
            for cod, s in esp.items():
                if cod not in vistos:              # declarado por el archivo y sin etiqueta de valor
                    filas_c.append(_fila_categoria(vid, cod, "", s, frecuencias.get((c["nombre"], cod)),
                                                   m["filas"], p, hallazgos, con_etiqueta=False))
    return Indice(archivos=pl.DataFrame(filas_a, schema=esq_a), variables=pl.DataFrame(filas_v, schema=esq_v),
                  categorias=pl.DataFrame(filas_c, schema=esq_c), hallazgos=hallazgos)


def _controles_etiqueta(original, curada, hechas, p: ParametrosIndice, *, es_variable: bool, derivada: bool = False) -> list[str]:
    """Controles §7.3 sobre una etiqueta. «Vacía» incluye nula, solo espacios y una derivada que no existe en el archivo (no)."""
    if derivada:
        return []
    ctl = []
    if not (curada or "").strip():
        ctl.append("etiqueta_vacia")
    if "mojibake" in hechas:
        ctl.append("mojibake_reparado")
    if curada and tiene_mojibake(curada):
        ctl.append("mojibake_sin_reparar")
    if any(v in curada for v in p.vocales_acento_grave):
        ctl.append("etiqueta_acento_grave")
    if es_variable and original is not None and len(original) == p.etiqueta_largo_posible_corte:
        ctl.append("etiqueta_posible_corte")
    return ctl


def _fila_categoria(vid, cod, etq, esp, frecuencia, filas, p, hallazgos, *, con_etiqueta=True) -> dict:
    curada, hechas = curar_etiqueta(etq)
    ctl = _controles_etiqueta(etq, curada, hechas, p, es_variable=False)
    if not con_etiqueta:                     # código declarado que el archivo no etiqueta: no hay etiqueta que esté vacía
        ctl = [k for k in ctl if k != "etiqueta_vacia"]
    n = (esp or {}).get("declarado_conteo")
    if n is None:
        n = frecuencia
    if esp and esp["origen"].startswith("declarado") and n == 0 and filas:
        ctl.append("especial_declarado_sin_filas")
    for k in ctl:
        hallazgos.append(Hallazgo(k, f"{vid}={cod}", f"etiqueta: {etq!r}"))
    return {"var_id": vid, "codigo": cod, "etiqueta_original": etq, "etiqueta_curada": curada,
            "es_especial": "propuesto" if esp else "no", "rol_faltante": None,
            "origen_especial": esp["origen"] if esp else None, "frecuencia": n if esp else None,
            "proporcion_filas": (n / filas if (esp and n is not None and filas) else None), "controles": ctl}


# ------------------------------------------------------------------ controles que necesitan más de un año (M1 y M2)

def control_etiquetas_entre_anios(var_ref: str, etiquetas: dict[int, str | None]) -> Hallazgo | None:
    """«La misma variable tiene otra etiqueta en otro año» (§7.3). Se compara la etiqueta normalizada (sin mayúsculas,
    acentos ni espacios de más): solo salta un cambio de texto, no de estilo."""
    normales = {a: normalizar_texto(e) for a, e in etiquetas.items()}
    if len(set(normales.values())) <= 1:
        return None
    return Hallazgo("etiqueta_cambia_entre_anios", var_ref,
                    "; ".join(f"{a}: {etiquetas[a]!r}" for a in sorted(etiquetas)))


def control_frecuencia_entre_anios(objeto: str, proporciones: dict[int, float], p: ParametrosIndice) -> Hallazgo | None:
    """«La frecuencia de un código especial cambia mucho entre años» (§7.3). `proporciones[año]` = proporción de filas con
    ese código (0–1). Salta entre dos años si la mayor es al menos `razon` veces la menor Y la diferencia llega a
    `cambio_min_pp` puntos porcentuales. Un año en 0 cuenta como razón infinita."""
    anios = sorted(proporciones)
    for i, a in enumerate(anios):
        for b in anios[i + 1:]:
            lo, hi = sorted((proporciones[a], proporciones[b]))
            razon = float("inf") if lo == 0 and hi > 0 else (hi / lo if lo > 0 else 1.0)
            if razon >= p.frecuencia_razon and (hi - lo) * 100 >= p.frecuencia_cambio_min_pp:
                return Hallazgo("frecuencia_especial_cambia_entre_anios", objeto,
                                f"{a}: {proporciones[a]:.4%}; {b}: {proporciones[b]:.4%}")
    return None


def coincidencia_universo(en_universo: Sequence[bool], con_valor: Sequence[bool]) -> float:
    """Proporción de filas en que «está en el universo del cuestionario» coincide con «la variable tiene valor»."""
    if len(en_universo) != len(con_valor):
        raise PapError("el universo y los valores no tienen el mismo número de filas")
    if not en_universo:
        raise PapError("no hay filas para comparar el universo")
    return sum(1 for u, v in zip(en_universo, con_valor) if bool(u) == bool(v)) / len(en_universo)


def control_universo(var_id: str, en_universo: Sequence[bool], con_valor: Sequence[bool], p: ParametrosIndice) -> Hallazgo | None:
    """«El universo_cuestionario coincide con el patrón real de valores no vacíos en menos del 99,5 %» (§7.3)."""
    c = coincidencia_universo(en_universo, con_valor)
    if c >= p.universo_coincidencia_min:
        return None
    return Hallazgo("universo_no_coincide", var_id, f"coincide en {c:.3%} de las filas (mínimo {p.universo_coincidencia_min:.1%})")


def coincidencia_universo_parquet(parquet: Path, variable: str, predicado_sql: str) -> float:
    """Igual que `coincidencia_universo` sobre un Parquet: `predicado_sql` es el universo como expresión SQL de DuckDB."""
    import duckdb

    ruta = str(parquet).replace("'", "''")
    x = '"' + variable.replace('"', '""') + '"'
    r = duckdb.connect().execute(f"SELECT avg((({predicado_sql}) = ({x} IS NOT NULL))::INT) FROM read_parquet('{ruta}')").fetchone()[0]
    if r is None:
        raise PapError(f"{Path(parquet).name}: no hay filas para comparar el universo")
    return float(r)


# ------------------------------------------------------------------ uniones declaradas: filas antes y después

@dataclass(frozen=True)
class UnionContada:
    hijo: str
    padre: str
    filas_hijo: int
    filas_union: int            # unión izquierda del hijo con el padre
    filas_con_pareja: int       # unión interna: cuántas filas del hijo encontraron al padre
    llaves_repetidas_padre: int

    @property
    def sin_perdida_ni_duplicacion(self) -> bool:
        return self.filas_hijo == self.filas_union == self.filas_con_pareja and self.llaves_repetidas_padre == 0


def contar_union(hijo_parquet: Path, padre_parquet: Path, por: Sequence[Sequence[str]], *, hijo: str = "", padre: str = "") -> UnionContada:
    """Cuenta las filas del hijo antes y después de unirlo con el padre por `por` = [[col del hijo, col del padre], …]."""
    import duckdb

    q = lambda s: "'" + str(s).replace("'", "''") + "'"
    c = lambda s: '"' + s.replace('"', '""') + '"'
    con = duckdb.connect()
    h, pa = f"read_parquet({q(hijo_parquet)})", f"read_parquet({q(padre_parquet)})"
    on = " AND ".join(f"h.{c(x)} = p.{c(y)}" for x, y in por)
    n = con.execute(f"SELECT count(*) FROM {h}").fetchone()[0]
    izq = con.execute(f"SELECT count(*) FROM {h} h LEFT JOIN {pa} p ON {on}").fetchone()[0]
    inter = con.execute(f"SELECT count(*) FROM {h} h JOIN {pa} p ON {on}").fetchone()[0]
    cols_p = ", ".join(c(y) for _, y in por)
    rep = con.execute(f"SELECT count(*) - count(DISTINCT ({cols_p})) FROM {pa}").fetchone()[0]
    return UnionContada(hijo or Path(hijo_parquet).stem, padre or Path(padre_parquet).stem, n, izq, inter, rep)


def verificar_relaciones(curado: dict, carpeta_parquet: Path) -> list[UnionContada]:
    """Cuenta todas las uniones declaradas en la tabla curada, contra los Parquet de `carpeta_parquet`."""
    return [contar_union(Path(carpeta_parquet) / f"{r['hijo']}.parquet", Path(carpeta_parquet) / f"{r['padre']}.parquet",
                         r["por"], hijo=r["hijo"], padre=r["padre"]) for r in curado.get("relaciones") or []]


# ------------------------------------------------------------------ lectura de los ZIP y escritura

def leer_metadatos_archivo(entrada: Path, formato: str, p: Parametros) -> dict:
    """Metadatos de un SAV/DTA en el subproceso aislado de M0-04 (mismos topes), sin tope de etiquetas."""
    if formato not in ("dta", "sav"):
        raise PapError(f"formato no soportado: {formato!r}")
    with tempfile.TemporaryDirectory(prefix="pap-indice-") as d:
        d = Path(d)
        spec = {"modo": "metadatos", "entrada": str(entrada), "formato": formato,
                "codificacion_sin_declarar": p.codificacion_sin_declarar, "resultado": str(d / "resultado.json")}
        (d / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
        ej = ejecutar_aislado([sys.executable, "-I", "-m", "pap.inferencia.lector_aislado", str(d / "spec.json")], p, cwd=d)
        ruta = d / "resultado.json"
        res = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
        if ej.returncode != 0 or "error" in res:
            raise PapError(f"{Path(entrada).name}: " + (res.get("error") or
                           f"el lector terminó con código {ej.returncode}: {ej.stderr.strip()[-600:]}"))
    return res


def leer_zips(rutas: Rutas, encuesta: str, anio: int, p: Parametros, *, log=print) -> dict[str, dict]:
    """Recorre todos los DTA/SAV de los ZIP registrados de la encuesta y el año. Devuelve `metas` (ver `construir`)."""
    lista = rutas.raiz / "curados" / "inferencia" / "descargas" / f"{encuesta.lower()}_{anio}.yaml"
    if not lista.exists():
        raise PapError(f"No hay lista de descargas para {encuesta} {anio}: falta {rutas.relativa(lista)}")
    cfg = yaml.safe_load(lista.read_text(encoding="utf-8"))
    metas: dict[str, dict] = {}
    for mod in cfg["modulos"]:
        ins = _insumo(rutas, cfg["fuente"], mod["recurso"])
        if sha256(ins.ruta) != ins.hash.removeprefix("sha256:"):
            raise PapError(f"{mod['recurso']}: la huella del ZIP no coincide con la registrada; corre `pap verificar`")
        with abrir_zip_seguro(ins.ruta) as z, tempfile.TemporaryDirectory(prefix="pap-zip-") as d:
            datos = sorted(m for m in z.miembros() if m.lower().endswith((".dta", ".sav")))
            if not datos:
                raise PapError(f"{ins.original_filename}: el ZIP no trae ningún DTA ni SAV")
            for miembro in datos:
                nombre = nombre_parquet(miembro, anio)
                if nombre in metas:
                    raise PapError(f"{miembro}: el nombre {nombre!r} ya lo usa otro archivo de {encuesta} {anio}")
                formato = miembro.rsplit(".", 1)[-1].lower()
                local = Path(d) / Path(miembro).name
                with open(local, "wb") as f:
                    z.copiar(miembro, f)
                meta = leer_metadatos_archivo(local, formato, p)
                local.unlink()
                metas[nombre] = {"filas": meta["filas"], "columnas": meta["columnas"], "formato": formato,
                                 "miembro": miembro, "zip": ins.original_filename}
                log(f"✔ {nombre}: {len(meta['columnas'])} variables, {meta['filas']:,} filas")
    return metas


def cargar_clases(ruta: Path = RUTA_CLASES) -> dict:
    return yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))["columnas"]


def cargar_curado(encuesta: str, anio: int, raiz: Path = RAIZ_REPO) -> dict:
    ruta = ruta_curada_archivos(encuesta, anio, raiz)
    if not ruta.exists():
        raise PapError(f"Falta la tabla curada de archivos y llaves: {ruta}")
    return yaml.safe_load(ruta.read_text(encoding="utf-8"))


def escribir(indice: Indice, destino: Path) -> dict[str, Path]:
    """Escribe los tres Parquet (zstd) en `destino`; ordenados, para que dos corridas den lo mismo."""
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    salida = {}
    for nombre, df in (("archivos", indice.archivos.sort("archivo")), ("variables", indice.variables.sort("var_id")),
                       ("categorias", indice.categorias)):
        ruta = destino / f"{nombre}.parquet"
        tmp = ruta.with_name(f".{ruta.name}.tmp")
        df.write_parquet(tmp, compression="zstd", compression_level=3)
        tmp.replace(ruta)
        salida[nombre] = ruta
    return salida


def indexar(rutas: Rutas, encuesta: str, anio: int, *, p: Parametros | None = None, pi: ParametrosIndice | None = None,
            log=print) -> tuple[Indice, dict[str, Path]]:
    """`pap variables indexar`: lee los ZIP registrados, arma el índice y lo escribe en `biblioteca/variables/`."""
    p, pi = p or Parametros.desde_yaml(), pi or ParametrosIndice.desde_yaml()
    carpeta = carpeta_salida(rutas, encuesta, anio)
    ruta_man = carpeta / "manifiesto.json"
    if not ruta_man.exists():
        raise PapError(f"Falta {rutas.relativa(ruta_man)}: corre antes `pap microdatos convertir --encuesta {encuesta} --anio {anio}`")
    manifiesto = json.loads(ruta_man.read_text(encoding="utf-8"))
    faltan = [a["parquet"] for a in manifiesto["archivos"].values() if not (carpeta / a["parquet"]).exists()]
    if faltan:
        raise PapError(f"Faltan Parquet de {encuesta} {anio} ({len(faltan)}, p. ej. {faltan[0]}): corre `pap microdatos convertir`")
    metas = leer_zips(rutas, encuesta, anio, p, log=log)
    indice = construir(encuesta, anio, metas, manifiesto, cargar_clases(rutas.raiz / "curados" / "inferencia" / "clases_columnas.yaml"),
                       cargar_curado(encuesta, anio, rutas.raiz), pi, parquet_dir=carpeta)
    return indice, escribir(indice, carpeta_indice(rutas))


# ------------------------------------------------------------------ conteos (evidencia)

def _cuantil(valores: list[int], q: float) -> float:
    """Cuantil con interpolación lineal (el de NumPy por defecto), sin depender de NumPy."""
    if not valores:
        return 0.0
    v = sorted(valores)
    pos = (len(v) - 1) * q
    i = int(pos)
    return v[i] + (v[min(i + 1, len(v) - 1)] - v[i]) * (pos - i)


def conteos(indice: Indice) -> dict:
    """Conteos de la historia: filas del índice, textos de etiqueta distintos, «tokens» por texto (p50 y p95; aproximados
    por palabras, porque el tokenizer de e5-small es de M1) y variables por archivo."""
    textos = set()
    for df in (indice.variables, indice.categorias):
        textos.update(t for t in df["etiqueta_curada"].to_list() if t)
    palabras = [len(t.split()) for t in textos]
    return {"filas": {"archivos": indice.archivos.height, "variables": indice.variables.height,
                      "categorias": indice.categorias.height},
            "textos_distintos": len(textos),
            "tokens_por_texto": {"aproximacion": "palabras separadas por espacios", "p50": _cuantil(palabras, 0.5),
                                 "p95": _cuantil(palabras, 0.95), "max": max(palabras, default=0)},
            "variables_por_archivo": dict(sorted(zip(indice.archivos["archivo"].to_list(), indice.archivos["n_variables"].to_list()))),
            "especiales_propuestos": int((indice.categorias["es_especial"] == "propuesto").sum()),
            "controles": {k: sum(1 for h in indice.hallazgos if h.control == k) for k in CONTROLES}}
