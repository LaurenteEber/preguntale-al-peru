"""Lectores de los insumos del sprint S1. Cada uno devuelve un DataFrame limpio con ubigeo de 6 caracteres."""
from __future__ import annotations

import io
import re
import unicodedata

import pandas as pd

from ..config import Rutas
from ..errores import PapError
from .. import almacen
from . import insumos

RE_UBIGEO = re.compile(r"^\d{6}$")
RE_NOTA = re.compile(r"\s*\d+/\s*")


def normalizar(nombre) -> str:
    """Mayúsculas, sin tildes ni signos, espacios colapsados (para emparejar)."""
    if nombre is None or (isinstance(nombre, float) and pd.isna(nombre)):
        return ""
    t = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode().upper()
    t = re.sub(r"[^A-Z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def quitar_notas(nombre: str) -> tuple[str, list[str]]:
    notas = re.findall(r"(\d+)/", str(nombre))
    return re.sub(r"\s+", " ", RE_NOTA.sub(" ", str(nombre))).strip(), notas


UBIGEO_NACIONAL = "000000"
UBIGEO_LIMA_REGION_PROPIO = "159999"  # «Región Lima» del archivo propio = ámbito LIMA_REGION, no es un ubigeo INEI


def nivel_de(ubigeo: str) -> str:
    if ubigeo == UBIGEO_NACIONAL:
        return "nacional"
    if ubigeo == UBIGEO_LIMA_REGION_PROPIO:
        return "ambito"
    if ubigeo.endswith("0000"):
        return "departamento"
    if ubigeo.endswith("00"):
        return "provincia"
    return "distrito"


def ubigeo_normalizado(serie: pd.Series) -> pd.Series:
    """Ubigeo de 6 dígitos desde texto de fuentes (quita '.0', completa el cero inicial que pierden los CSV
    leídos como número); vacíos, '0' y '000000' → nulo. No valida contra la tabla de ubigeo."""
    s = serie.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    s = s.where(s.str.fullmatch(r"\d{1,6}").fillna(False))
    s = s.str.zfill(6)
    return s.mask(s == UBIGEO_NACIONAL)


def ubigeo6(valor) -> str | None:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    s = str(valor).strip()
    if re.fullmatch(r"\d{2}", s):
        return s + "0000"
    if re.fullmatch(r"\d{4}", s):
        return s + "00"
    return s if RE_UBIGEO.match(s) else None


# ------------------------------------------------------------------ archivo propio (semilla GEO2017)

def semilla_propio(rutas: Rutas) -> tuple[pd.DataFrame, insumos.Insumo]:
    ins = insumos.ultimo(rutas, "PROPIO-ESTADISTICAS-SOCIALES-2020")
    crudo = pd.read_excel(ins.ruta, sheet_name="1. Info_General", header=None, dtype=object)
    # Cabecera en la fila 4 (índice 3): UBIGEO, nombre, capital, lat, lon, altitud, superficie, densidad,
    # nº prov, nº dist, nº CCPP, tipología, frontera, país fronterizo.
    o = next(j for j, v in enumerate(crudo.iloc[3].tolist()) if str(v).strip().upper() == "UBIGEO")
    filas = []
    for _, r in crudo.iloc[5:].iterrows():
        u = str(r[o]).strip() if pd.notna(r[o]) else ""
        if not RE_UBIGEO.match(u):
            continue
        filas.append({
            "ubigeo": u, "nombre_mostrado": str(r[o + 1]).strip(), "capital_legal": _txt(r[o + 2]),
            "lat_capital": _num(r[o + 3]), "lon_capital": _num(r[o + 4]), "altitud_capital": _num(r[o + 5]),
            "superficie_km2": _num(r[o + 6]), "tipologia_pcm": _txt(r[o + 11]), "frontera": _txt(r[o + 12]),
        })
    df = pd.DataFrame(filas)
    if df.ubigeo.duplicated().any():
        raise PapError("Semilla: ubigeos repetidos en la hoja 1")
    return df, ins


def _txt(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    return None if s in ("", "-", "nan") else s


def _num(v):
    try:
        f = float(v)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ proyecciones distritales

def proyeccion(rutas: Rutas, source_id: str, patron: str | None = None) -> tuple[pd.DataFrame, list[str], insumos.Insumo]:
    """Filas con ubigeo, nombre (sin marcas de nota), notas y población por año; más las notas al pie."""
    ins = insumos.ultimo(rutas, source_id, patron)
    crudo = pd.read_excel(ins.ruta, header=None, dtype=object)
    cab = None
    for i in range(12):
        fila = [str(x).strip() for x in crudo.iloc[i].tolist()]
        if fila[0].upper() == "UBIGEO":
            cab = i
            break
    if cab is None:
        raise PapError(f"{source_id}: no encuentro la fila de cabecera UBIGEO")
    anios = {}
    for i in (cab, cab + 1):
        for j, v in enumerate(crudo.iloc[i].tolist()):
            m = re.fullmatch(r"(20\d\d)(\.0)?", str(v).strip())
            if m:
                anios[j] = int(m.group(1))
    filas, notas = [], []
    for _, r in crudo.iloc[cab + 1:].iterrows():
        u = str(r[0]).strip() if pd.notna(r[0]) else ""
        if RE_UBIGEO.match(u):
            nombre, marcas = quitar_notas(r[1])
            fila = {"ubigeo": u, "nombre": nombre, "notas": marcas, "nivel": nivel_de(u)}
            textos = []
            for j, a in anios.items():
                v = _num(r[j])
                fila[f"p{a}"] = None if v is None else round(v)
                if v is None and pd.notna(r[j]):
                    textos.append(f"{a}: {str(r[j]).strip()}")
            fila["texto_celdas"] = textos
            filas.append(fila)
        elif pd.notna(r[0]) and re.match(r"^\d+/", str(r[0]).strip()):
            notas.append(str(r[0]).strip())
    df = pd.DataFrame(filas)
    if df.ubigeo.duplicated().any():
        raise PapError(f"{source_id}: ubigeos repetidos")
    return df, notas, ins


# ------------------------------------------------------------------ ubigeos PNDA (INEI 2022)

def pnda(rutas: Rutas) -> tuple[pd.DataFrame, insumos.Insumo]:
    ins = insumos.ultimo(rutas, "INEI-PNDA-UBIGEOS")
    _, datos = insumos.miembro_zip(ins, r"\.csv$")
    texto = _decodificar(datos)
    df = pd.read_csv(io.StringIO(texto), sep=";", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df[df["IDDIST"].fillna("").str.strip().str.fullmatch(r"\d{6}")]
    out = pd.DataFrame({
        "ubigeo": df["IDDIST"].str.strip().str.zfill(6),
        "departamento": df["NOMBDEP"].str.strip(),
        "provincia": df["NOMBPROV"].str.strip(),
        "nombre": df["NOMBDIST"].str.strip(),
        "capital": df[[c for c in df.columns if c.startswith("NOM_CAPITAL")][0]].str.strip(),
        "region_natural": df["REGION NATURAL"].str.strip(),
    })
    return out, ins


def _decodificar(datos: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return datos.decode(enc)
        except UnicodeDecodeError:
            continue
    raise PapError("No se pudo decodificar el CSV")


# ------------------------------------------------------------------ puente GitHub (corte 2021)

def github(rutas: Rutas) -> tuple[pd.DataFrame, insumos.Insumo]:
    ins = insumos.ultimo(rutas, "GITHUB-UBIGEO-PERU-AUMENTADO")
    df = pd.read_csv(ins.ruta, dtype=str, keep_default_na=False)
    df = df.replace({"NA": None, "": None})
    return df[["inei", "reniec", "departamento", "provincia", "distrito", "capital"]].copy(), ins


# ------------------------------------------------------------------ Directorio Nacional de Municipalidades 2025

def _dms(v):
    m = re.match(r"\s*(\d+)\D+(\d+)\D+(\d+(?:[.,]\d+)?)", str(v or ""))
    if not m:
        return None
    g, mi, s = float(m.group(1)), float(m.group(2)), float(m.group(3).replace(",", "."))
    return -(g + mi / 60 + s / 3600)  # oeste y sur → negativos


def directorio(rutas: Rutas) -> tuple[pd.DataFrame, insumos.Insumo]:
    ins = insumos.ultimo(rutas, "INEI-DIRECTORIO-MUNICIPALIDADES")
    filas = []
    for nombre_miembro, datos in insumos.miembros_zip(ins, r"1\.Directorio-MPyMD-2025/.*\.xlsx?$"):
        crudo = pd.read_excel(io.BytesIO(datos), header=None, dtype=object)
        cab = next(i for i in range(10) if str(crudo.iloc[i, 0]).strip().lower() == "ubigeo")
        c = {}
        for j, v in enumerate(crudo.iloc[cab].tolist()):
            t = re.sub(r"\s+", " ", str(v).lower())
            if "provincia y distrito" in t:
                c["nombre"] = j
            elif "dispositivo legal" in t:
                c["dispositivo"] = j
            elif "capital legal" in t:
                c["capital"] = j
        for j, v in enumerate(crudo.iloc[cab + 1].tolist()):
            if str(v).strip().lower().startswith("categor"):
                c["categoria"] = j
        for j, v in enumerate(crudo.iloc[cab + 2].tolist()):
            t = str(v).lower()
            if t.startswith("altitud"):
                c["altitud"] = j
            elif t.startswith("longitud"):
                c["lon"] = j
            elif t.startswith("latitud"):
                c["lat"] = j
        for _, r in crudo.iloc[cab + 3:].iterrows():
            u = ubigeo6(r[0])
            if not u or str(r[c["nombre"]]).strip().lower() == "total":
                continue
            filas.append({
                "ubigeo": u, "nombre": quitar_notas(str(r[c["nombre"]]).strip())[0],
                "dispositivo_legal": re.sub(r"\s+", " ", str(r[c["dispositivo"]])).strip() if pd.notna(r[c["dispositivo"]]) else None,
                "capital": quitar_notas(_txt(r[c["capital"]]))[0] if _txt(r[c["capital"]]) else None, "categoria": _txt(r[c["categoria"]]),
                "altitud": _num(r[c["altitud"]]), "lon": _dms(r[c["lon"]]), "lat": _dms(r[c["lat"]]),
                "archivo": nombre_miembro,
            })
    df = pd.DataFrame(filas)
    df = df[df.ubigeo.map(nivel_de) != "departamento"]
    if df.ubigeo.duplicated().any():
        raise PapError("Directorio: ubigeos repetidos: " + ", ".join(df[df.ubigeo.duplicated()].ubigeo))
    return df.reset_index(drop=True), ins


# ------------------------------------------------------------------ RENIEC población identificada

def reniec(rutas: Rutas) -> tuple[pd.DataFrame, insumos.Insumo] | tuple[None, None]:
    """Pares distintos (ubigeo_reniec, ubigeo_inei, departamento, provincia, distrito) de residentes en el Perú."""
    import duckdb

    try:
        ins = insumos.ultimo(rutas, "RENIEC-POBLACION-IDENTIFICADA")
    except PapError:
        return None, None
    con = duckdb.connect()
    try:
        df = con.execute(
            "SELECT DISTINCT lpad(CAST(UBIGEO_RENIEC AS VARCHAR), 6, '0') AS ubigeo_reniec, "
            "lpad(CAST(UBIGEO_INEI AS VARCHAR), 6, '0') AS ubigeo_inei, Departamento AS departamento, "
            "Provincia AS provincia, Distrito AS distrito "
            "FROM read_csv(?, header=true, all_varchar=true, quote='\"', escape='\"', delim=',', strict_mode=true) WHERE Residencia = 'Nacional'",
            [str(ins.ruta)]).df()
    finally:
        con.close()
    return df.sort_values("ubigeo_reniec").reset_index(drop=True), ins


# ------------------------------------------------------------------ proyecciones departamentales por edad (PDF)

DEPARTAMENTOS_PDF = {
    "AMAZONAS": "01", "ANCASH": "02", "APURIMAC": "03", "AREQUIPA": "04", "AYACUCHO": "05", "CAJAMARCA": "06",
    "CALLAO": "07", "PROV DEL CALLAO": "07", "PROVINCIA CONSTITUCIONAL DEL CALLAO": "07", "PROV CONST DEL CALLAO": "07",
    "CUSCO": "08", "HUANCAVELICA": "09", "HUANUCO": "10", "ICA": "11", "JUNIN": "12", "LA LIBERTAD": "13",
    "LAMBAYEQUE": "14", "LIMA": "15", "LORETO": "16", "MADRE DE DIOS": "17", "MOQUEGUA": "18", "PASCO": "19",
    "PIURA": "20", "PUNO": "21", "SAN MARTIN": "22", "TACNA": "23", "TUMBES": "24", "UCAYALI": "25", "PERU": "00",
}


def _dep_de_titulo(titulo: str) -> str | None:
    m = re.search(r"CUADRO N\S*\s*[\d.]+\s+([A-ZÁÉÍÓÚÑ .]+?):", titulo.upper())
    if m:
        return DEPARTAMENTOS_PDF.get(normalizar(m.group(1)))
    m = re.search(r"(?:CUADRO N\S* [\d.]+\s+)?([A-ZÁÉÍÓÚÑ .]+?):\s+(?:ESTIMACIONES|POBLACI)", titulo.upper())
    if not m:
        return None
    return DEPARTAMENTOS_PDF.get(normalizar(m.group(1)))


def _cache(rutas: Rutas, ins, nombre: str, fn):
    """Caché derivada (no va a git): el resultado de leer un PDF, identificado por la huella del crudo."""
    ruta = rutas.cruda / "cache" / f"{nombre}-{ins.hash[7:23]}.csv"
    if ruta.exists():
        return pd.read_csv(ruta, dtype={"dep": str})
    df = fn()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False)
    return df


def dep_edad_simple(rutas: Rutas):
    ins = insumos.ultimo(rutas, "INEI-PROYECCIONES-DEPARTAMENTAL-EDAD", r"edad-simple|6855196")
    return _cache(rutas, ins, "b25", lambda: _dep_edad_simple(ins)), ins


def _dep_edad_simple(ins):
    """Boletín Especial 25: población por departamento, edad simple (0-79, 80+) y año, ambos sexos."""
    import pdfplumber

    from .pdf_tablas import cuadro

    filas = []
    with pdfplumber.open(ins.ruta) as pdf:
        for page in pdf.pages:
            anios, cuadros, titulo = cuadro(page)
            if not anios or "EDADES SIMPLES" not in titulo.upper():
                continue
            dep = _dep_de_titulo(titulo)
            if dep is None:
                continue
            for etiqueta, valores in cuadros:
                e = etiqueta.strip().upper()
                if re.fullmatch(r"\d+", e):
                    edad = int(e)
                elif e.startswith("80"):
                    edad = 80
                elif e == "TOTAL":
                    edad = -1
                else:
                    continue
                for a, v in zip(anios, valores):
                    if v is not None:
                        filas.append({"dep": dep, "anio": a, "edad": edad, "valor": v})
    df = pd.DataFrame(filas).drop_duplicates()
    if df.duplicated(["dep", "anio", "edad"]).any():
        raise PapError("Boletín 25: valores repetidos con cifras distintas")
    return df


QUINQUENIOS = [(0, 4), (5, 9), (10, 14), (15, 19), (20, 24), (25, 29), (30, 34), (35, 39), (40, 44), (45, 49),
               (50, 54), (55, 59), (60, 64), (65, 69), (70, 74), (75, 79), (80, 84), (85, 89), (90, 94), (95, 99), (100, 999)]


def dep_sexo_quinquenal(rutas: Rutas):
    ins = insumos.ultimo(rutas, "INEI-PROYECCIONES-DEPARTAMENTAL-EDAD", r"departamento-1995|6855233")
    return _cache(rutas, ins, "b39", lambda: _dep_sexo_quinquenal(ins)), ins


def _dep_sexo_quinquenal(ins):
    """Boletín de Análisis Demográfico 39: población por departamento, sexo, grupo quinquenal y año."""
    import pdfplumber

    from .pdf_tablas import cuadro

    filas = []
    with pdfplumber.open(ins.ruta) as pdf:
        for page in pdf.pages:
            anios, cuadros, titulo = cuadro(page)
            if not anios or "QUINQUENALES" not in titulo.upper():
                continue
            dep = _dep_de_titulo(titulo)
            if dep is None:
                continue
            sexo = "T"
            for etiqueta, valores in cuadros:
                e = normalizar(etiqueta)
                if e.startswith("TOTAL"):
                    sexo, edad_min = "T", -1
                elif e.startswith("HOMBRE"):
                    sexo, edad_min = "M", -1
                elif e.startswith("MUJER"):
                    sexo, edad_min = "F", -1
                else:
                    m = re.match(r"(\d+)\s*(\d+)?", e)
                    if not m:
                        continue
                    edad_min = int(m.group(1))
                for a, v in zip(anios, valores):
                    if v is not None:
                        filas.append({"dep": dep, "anio": a, "sexo": sexo, "edad_min": edad_min, "valor": v})
    df = pd.DataFrame(filas).drop_duplicates()
    if df.duplicated(["dep", "anio", "sexo", "edad_min"]).any():
        raise PapError("Boletín 39: valores repetidos con cifras distintas")
    return df


# ------------------------------------------------------------------ Censo 2017 por distrito, sexo y edad simple (REDATAM)

def censo_edad_sexo(rutas: Rutas):
    """Población censada 2017 por distrito, sexo (1 hombre, 2 mujer) y edad simple, desde las exportaciones REDATAM."""
    from .. import capturas

    recs = insumos.filtrar_por_lock(rutas, "INEI-CPV2017", [rec for _, rec in capturas.recursos(rutas, "INEI-CPV2017")
                                                            if rec["original_filename"].startswith("cpv2017_edad_simple")])
    if not recs:
        raise PapError("Falta el insumo INEI-CPV2017 (exportaciones REDATAM por edad simple). Regístralo: pap revisar INEI-CPV2017")
    ultimo_por_archivo = {}
    for rec in recs:
        ultimo_por_archivo[rec["original_filename"]] = rec
    partes = [pd.read_csv(almacen.resolver(rutas, r["path"]), dtype={"ubigeo": str}) for r in ultimo_por_archivo.values()]
    df = pd.concat(partes, ignore_index=True)
    df["ubigeo"] = df.ubigeo.str.zfill(6)
    df = df[df.ubigeo != "000000"]  # bloque nacional de REDATAM: solo control
    if df.duplicated(["ubigeo", "sexo", "edad"]).any():
        raise PapError("Censo 2017: filas repetidas entre exportaciones (rangos de edad solapados)")
    # Una entrada de insumo por exportación, con su huella completa (trazable hasta su captura)
    ins = [insumos.Insumo("INEI-CPV2017", r["name"], r["hash"], almacen.resolver(rutas, r["path"]), r["original_filename"],
                          r.get("issued"), r["retrieved_at"])
           for _, r in sorted(ultimo_por_archivo.items())]
    return df, ins
