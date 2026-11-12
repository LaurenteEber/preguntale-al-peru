"""Sprint S3 — Puentes del piloto (parte sin gasto): dim_ipc y dim_establecimiento_salud; ubicación de los
establecimientos del SIEN. La parte de gasto (dim_unidad_ejecutora, dim_tema_gasto, dim_inversion_ubicacion)
queda pendiente de los archivos del MEF (certificado vencido en fs.datosabiertos.mef.gob.pe, 6/10/2026)."""
from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from ..config import Rutas
from ..zip_seguro import abrir_zip_seguro
from . import insumos
from . import lectores as L
from . import territorio as T

# Ronda 3 (7/10/2026): dim_establecimiento_salud (corrección de 160109, GA-09) y fact_sien_hb_ubigeo (nueva, SP-03)
# pasan a 1.2.0. dim_ipc no cambia y conserva su versión (y su huella).
VERSION_TABLA = "1.2.0"
VERSION_TABLA_IPC = "1.1.0"
MESES = {"Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6, "Jul": 7, "Ago": 8, "Sep": 9, "Set": 9,
         "Oct": 10, "Nov": 11, "Dic": 12}


@dataclass
class Resultado:
    tablas: dict[str, pd.DataFrame] = field(default_factory=dict)
    pruebas: list[dict] = field(default_factory=list)
    revision: dict[str, pd.DataFrame] = field(default_factory=dict)
    insumos: list = field(default_factory=list)

    def prueba(self, id_, descripcion, ok, detalle=None, bloqueante=True):
        self.pruebas.append({"id": id_, "descripcion": descripcion, "ok": bool(ok), "bloqueante": bloqueante,
                             "detalle": detalle})

    @property
    def ok(self):
        return all(p["ok"] for p in self.pruebas if p["bloqueante"])


# ======================================================================= IPC

def construir_ipc(rutas: Rutas, res: Resultado) -> pd.DataFrame:
    ins = insumos.ultimo(rutas, "BCRP-IPC-LIMA")
    res.insumos.append(ins)
    datos = json.loads(ins.ruta.read_text(encoding="utf-8"))
    filas = []
    for p in datos["periods"]:
        mes_txt, anio = p["name"].split(".")
        v = p["values"][0]
        if v in ("n.d.", "", None):
            continue
        filas.append({"anio": int(anio), "mes": MESES[mes_txt], "indice": float(v)})
    df = pd.DataFrame(filas).sort_values(["anio", "mes"]).reset_index(drop=True)
    prom = df.groupby("anio").agg(ipc_prom_anual=("indice", "mean"), meses_con_dato=("mes", "count")).reset_index()
    df = df.merge(prom, on="anio")
    df["ipc_prom_anual"] = df.ipc_prom_anual.round(6)
    df["anio_completo"] = df.meses_con_dato == 12
    # SP-11: el promedio de un año incompleto no es un promedio anual: va aparte
    df["ipc_prom_parcial"] = df.ipc_prom_anual.where(~df.anio_completo)
    df["ipc_prom_anual"] = df.ipc_prom_anual.where(df.anio_completo)
    df["serie"] = "PN38705PM"
    df["base"] = "dic. 2021 = 100"
    df["version_tabla"] = VERSION_TABLA_IPC
    esperados = pd.period_range(f"{df.anio.min()}-01", f"{df.anio.max()}-{df[df.anio == df.anio.max()].mes.max():02d}", freq="M")
    reales = pd.PeriodIndex([f"{a}-{m:02d}" for a, m in zip(df.anio, df.mes)], freq="M")
    res.prueba("I-01", "IPC mensual sin huecos desde 2010-01 hasta el último mes publicado", len(esperados) == len(reales)
               and (esperados == reales).all(), {"desde": str(reales.min()), "hasta": str(reales.max()), "meses": len(reales)})
    dic21 = df[(df.anio == 2021) & (df.mes == 12)].indice
    res.prueba("I-02", "Base del índice: dic. 2021 = 100", len(dic21) == 1 and abs(float(dic21.iloc[0]) - 100) < 1e-9)
    return df


# ======================================================================= establecimientos de salud

SUBSECTOR = [  # SP-05: subsector desde la institución de RENIPRESS (primera coincidencia)
    (r"ESSALUD", "ESSALUD"), (r"SANIDAD|FUERZA|EJERCITO|MARINA|NAVAL|POLICIA|AEREA", "FFAA_PNP"),
    (r"MUNICIPAL", "MUNICIPAL"), (r"PRIVAD", "PRIVADO"), (r"GOBIERNO REGIONAL|MINSA|MINISTERIO DE SALUD|DIRESA|DISA", "MINSA_GORE"),
]


# GA-09 (ronda 3): un código antiguo se traduce por alias solo si equivale a UN distrito. 160109 Putumayo se escindió
# (Ley 30186, 2014) en 160801, 160802 y 160804: no tiene alias. Los establecimientos con 160109 se ubican con la tabla
# curada renipress_ubicacion_curada.yaml (evidencia: dirección, coordenadas, vecinos) o, si no están curados, en la
# provincia que contiene a todos los sucesores (ubigeo_valido = False: quedan en revision/renipress_ubigeo_invalido).
ALIAS_RENIPRESS = {k: v for k, v in T.CODIGOS_ANTIGUOS.items() if k not in T.CODIGOS_ESCINDIDOS}
METODOS_UBIGEO_EESS = {"fuente", "codigo_antiguo_alias", "curado", "codigo_escindido_contenedor"}


def _curada_renipress(rutas: Rutas, res: Resultado) -> pd.DataFrame:
    import yaml
    i_cur = insumos.curado(rutas, "renipress_ubicacion_curada.yaml")
    res.insumos.append(i_cur)
    cur = pd.DataFrame(yaml.safe_load(i_cur.ruta.read_text(encoding="utf-8")) or [],
                       columns=["cod_ipress", "ubigeo_fuente", "ubigeo_inei", "confianza", "evidencia", "revisado_dueno"])
    cur = cur.astype({"cod_ipress": str, "ubigeo_fuente": str, "ubigeo_inei": str})
    if cur.cod_ipress.duplicated().any():
        raise ValueError("renipress_ubicacion_curada.yaml: cod_ipress repetido")
    return cur


def construir_establecimientos(rutas: Rutas, res: Resultado, dim: pd.DataFrame) -> pd.DataFrame:
    ins = insumos.ultimo(rutas, "SUSALUD-RENIPRESS")
    res.insumos.append(ins)
    curada = _curada_renipress(rutas, res)
    # SP-10: validez del ubigeo a la fecha de corte del insumo, no a la fecha de construcción
    corte = ins.corte or ins.issued or (ins.retrieved_at or "")[:10]
    vigentes = set(dim[(dim.nivel == "distrito") & (dim.vigente_desde <= corte)
                       & (dim.vigente_hasta.isna() | (dim.vigente_hasta >= corte))].ubigeo_inei)
    r = pd.read_csv(ins.ruta, sep=";", dtype=str, encoding="utf-8-sig")
    r = r.apply(lambda s: s.str.strip() if s.dtype == object else s)
    df = pd.DataFrame({
        "cod_ipress": r.COD_IPRESS.str.zfill(8),
        "nombre": r.NOMBRE,
        "institucion": r.INSTITUCION,
        "clasificacion": r.CLASIFICACION,
        "tipo_establecimiento": r.TIPO_ESTABLECIMIENTO,
        "categoria": r.CATEGORIA.where(~r.CATEGORIA.isin(["0", "", "SIN CATEGORIA"])),
        "categoria_fuente": r.CATEGORIA,
        "estado": r.ESTADO,
        "ubigeo_inei": r.UBIGEO.str.zfill(6),
        "diris_diresa": r.DISA,
        "red": r.RED,
        "microred": r.MICRORED,
        "cod_ue": r.COD_UE.str.replace(r"\.0$", "", regex=True),
        "unidad_ejecutora": r.UNIDAD_EJECUTORA,
        "lat": pd.to_numeric(r.NORTE, errors="coerce"),
        "lon": pd.to_numeric(r.ESTE, errors="coerce"),
        "inicio_actividad": r.INICIO_ACTIVIDAD.str[:10],
    })
    # coordenadas fuera del Perú → nulas (se conservan como dato faltante, no se corrigen)
    fuera = ~(df.lat.between(-18.5, 0.1) & df.lon.between(-81.5, -68.5))
    df.loc[fuera & df.lat.notna(), ["lat", "lon"]] = None
    # códigos antiguos con equivalencia conocida (R-TERRITORIO-03): se redirigen y se marca la corrección.
    # GA-09: alias solo para códigos que equivalen a un distrito; los escindidos, por la tabla curada o al contenedor.
    df["ubigeo_fuente"] = df.ubigeo_inei
    df["metodo_ubigeo"] = "fuente"
    es_alias = df.ubigeo_fuente.isin(ALIAS_RENIPRESS)
    df.loc[es_alias, "ubigeo_inei"] = df.loc[es_alias, "ubigeo_fuente"].map(ALIAS_RENIPRESS)
    df.loc[es_alias, "metodo_ubigeo"] = "codigo_antiguo_alias"
    cur = df[["cod_ipress", "ubigeo_fuente"]].reset_index().merge(curada, on=["cod_ipress", "ubigeo_fuente"]).set_index("index")
    df.loc[cur.index, "ubigeo_inei"] = cur.ubigeo_inei
    df.loc[cur.index, "metodo_ubigeo"] = "curado"
    escindido = df.ubigeo_fuente.isin(T.CODIGOS_ESCINDIDOS) & (df.metodo_ubigeo == "fuente")
    df.loc[escindido, "ubigeo_inei"] = df.loc[escindido, "ubigeo_fuente"].map(T.CODIGOS_ESCINDIDOS)
    df.loc[escindido, "metodo_ubigeo"] = "codigo_escindido_contenedor"
    df["evidencia_ubigeo"] = df.cod_ipress.map(curada.set_index("cod_ipress").evidencia).where(df.metodo_ubigeo == "curado")
    df["ubigeo_corregido"] = df.ubigeo_inei != df.ubigeo_fuente
    df["ubigeo_valido"] = df.ubigeo_inei.isin(vigentes)
    inst = df.institucion.fillna("").str.upper()
    df["subsector"] = "OTRO"
    for pat, sub in reversed(SUBSECTOR):
        df.loc[inst.str.contains(pat, regex=True), "subsector"] = sub
    df["activo_al_corte"] = df.estado.fillna("").str.upper().str.startswith("ACTIV")
    df["fecha_corte"] = corte
    df["fuente_corte"] = ins.original_filename
    df["version_tabla"] = VERSION_TABLA
    res.prueba("E-01", "RENIPRESS: código IPRESS único (8 dígitos)", not df.cod_ipress.duplicated().any()
               and df.cod_ipress.str.fullmatch(r"\d{8}").all())
    pct = float(df.ubigeo_valido.mean())
    res.prueba("E-02", "RENIPRESS: ubigeo de cada establecimiento es un distrito vigente (≥ 99 %)", pct >= 0.99,
               {"pct_valido": round(pct, 5), "invalidos": sorted(df.loc[~df.ubigeo_valido, "ubigeo_inei"].unique())[:15],
                "corregidos_codigo_antiguo": int(df.ubigeo_corregido.sum())})
    res.revision["renipress_ubigeo_invalido"] = df.loc[~df.ubigeo_valido, ["cod_ipress", "nombre", "ubigeo_fuente",
                                                                       "ubigeo_inei", "metodo_ubigeo", "estado"]]
    # E-12 (GA-09): ningún código escindido pasa por alias; la tabla curada es coherente con el crudo y con el territorio
    distritos = set(dim[dim.nivel == "distrito"].ubigeo_inei)
    usadas = set(cur.cod_ipress)
    mal_cur = sorted(set(curada.cod_ipress) - usadas) + sorted(curada.loc[~curada.ubigeo_inei.isin(distritos), "cod_ipress"])
    alias_escindido = int((es_alias & df.ubigeo_fuente.isin(T.CODIGOS_ESCINDIDOS)).sum())
    res.prueba("E-12", "RENIPRESS: un código escindido (160109) nunca se redirige por alias; cada fila curada existe en el "
               "crudo con ese ubigeo y apunta a un distrito; el resto queda en la provincia contenedora",
               not mal_cur and alias_escindido == 0 and set(df.metodo_ubigeo) <= METODOS_UBIGEO_EESS,
               {"curados_no_aplicados_o_destino_invalido": mal_cur, "escindidos_por_alias": alias_escindido,
                "por_metodo": df.metodo_ubigeo.value_counts().to_dict()})
    res.revision["renipress_ubigeo_corregido"] = df.loc[df.metodo_ubigeo != "fuente",
                                                        ["cod_ipress", "nombre", "institucion", "ubigeo_fuente", "ubigeo_inei",
                                                         "metodo_ubigeo", "evidencia_ubigeo", "lat", "lon", "estado"]]
    return df


# SP-03/TE-08 (ronda 3, v3). Definiciones del diccionario oficial (PNDA, «2.Diccionarios HIS - 2025.xlsx», hoja Niños0a5)
# y de «Metadatos SIEN.docx», contrastadas con el crudo 2025:
# - Ubigeo_EESS: «Código UBIGEO del establecimiento de salud». Base de la proporción de anemia (D4).
# - UbigeoPN: «Código UBIGEO según procedencia del niño». El diccionario no dice «Padrón Nominal»; vacío en el 11,8 %
#   de las filas Hb (en esas filas SIS y Juntos también vienen en blanco). Base de la cobertura de tamizaje.
# - UbigeoREN: «Código UBIGEO según código RENIPRESS»; AlturaREN: «Altitud según código RENIPRESS» (Metadatos: «Altitud
#   (según el EESS Renipress)»). En el dato: uno por establecimiento, = Ubigeo_EESS en el 99,4 %, altitud = la de la
#   capital del distrito; en 46 EESS el REN no es el ubigeo vigente de RENIPRESS (distritos nuevos → madre; 20 EESS de
#   distritos preexistentes → otro distrito).
# La fuente INS-CENAN-SIEN también tiene registrada su documentación (recursos diccionario-datos-2012-2026 y
# metadatos-sien, capturas del 7/10/2026): el ZIP de datos se elige por nombre de recurso (auditoría final, hallazgo 6).
RECURSO_SIEN = "ins-cenan-sien"
UBIGEOS_SIEN = {"Ubigeo_EESS": "establecimiento", "UbigeoPN": "procedencia_nino",
                "UbigeoREN": "referencia_altitud_ajuste_hb"}
COLS_HB = ["EdadMeses", "Hemoglobina", "Hbc", "AlturaREN", "Dx_anemia"]
# OMS 2024 / NTS 213-MINSA/DGIESP-2024, Hb ajustada (g/dL): (edad_min, edad_max) -> límites inferiores de leve y moderada
# y corte de anemia; severa < 7,0.
CORTES_HB = {(6, 24): {"normal": 10.5, "leve": 9.5, "moderada": 7.0},
             (24, 60): {"normal": 11.0, "leve": 10.0, "moderada": 7.0}}
DX_VALIDOS = {"Normal", "Anemia Leve", "Anemia Moderada", "Anemia Severa"}
EDADES = ([6, 12, 24, 36, 60], ["6-11m", "12-23m", "24-35m", "36-59m"])
TOL_HB = 1e-6


def marcar_anemia(dx: pd.Series) -> tuple[pd.Series, pd.Series]:
    """(dx_valido, con_anemia) a partir de Dx_anemia: solo un Dx válido (Normal, Anemia Leve/Moderada/Severa) cuenta en
    el denominador, y solo un Dx válido distinto de Normal cuenta como anemia (un Dx nulo, vacío o desconocido, no)."""
    dx = dx.astype("string").str.strip()
    valido = dx.isin(DX_VALIDOS).fillna(False).astype(bool)
    return valido, valido & (dx != "Normal").fillna(False).astype(bool)


def ajuste_hb_oms2024(altitud: pd.Series) -> pd.Series:
    """Ajuste de Hb por altitud (g/dL), OMS 2024 / NTS 213: ((0,0056384·A) + (0,0000003·A²)) / 10 desde 500 m."""
    a = pd.to_numeric(altitud, errors="coerce")
    return ((0.0056384 * a + 0.0000003 * a ** 2) / 10).where(a >= 500, 0.0).where(a.notna())


def dx_esperado(hbc: pd.Series, edad: pd.Series) -> pd.Series:
    """Diagnóstico OMS 2024 a partir de la Hb ajustada y la edad en meses; NaN si falta dato o la edad está fuera de 6-59 m."""
    out = pd.Series(pd.NA, index=hbc.index, dtype="object")
    for (lo, hi), c in CORTES_HB.items():
        m = (edad >= lo) & (edad < hi) & hbc.notna()
        out = out.mask(m & (hbc >= c["normal"]), "Normal")
        out = out.mask(m & (hbc < c["normal"]) & (hbc >= c["leve"]), "Anemia Leve")
        out = out.mask(m & (hbc < c["leve"]) & (hbc >= c["moderada"]), "Anemia Moderada")
        out = out.mask(m & (hbc < c["moderada"]), "Anemia Severa")
    return out


def nivel_r_territorio_08(pct_ubicado: float) -> str:
    """Etiquetas de R-TERRITORIO-08 (umbrales 99 % y 95 %). Para la cobertura de tamizaje del SIEN se evalúan por
    departamento (extensión aprobada por el dueño el 7/10/2026) solo como diagnóstico: la cobertura se publica únicamente
    por departamento, con dos cotas y aviso cuando el intervalo cruza el 50 % (R-REG-07)."""
    if pd.isna(pct_ubicado):
        return "sin_dato"
    return "distrito" if pct_ubicado >= 0.99 else ("distrito_con_advertencia" if pct_ubicado >= 0.95
                                                    else "solo_departamento_o_nacional")


def _base_sien(nombre: str) -> str:
    partes = nombre.replace("\\", "/").split("/")
    return "Hb" if "Hb" in partes else ("Pt" if "Pt" in partes else "otro")


def establecimientos_sien(rutas: Rutas, res: Resultado, alguna_vez: set[str],
                          geo2017: set[str] | None = None) -> pd.DataFrame:
    """Códigos RENIPRESS y ubigeo del establecimiento presentes en el SIEN (todos los CSV del ZIP); calidad de sus tres
    columnas de ubigeo por base (Hb, Pt) y departamento (SP-03, TE-08); controles del ajuste por altitud; y agregado
    del SIEN-Hb por los tres ubigeos (fact_sien_hb_ubigeo). Los CSV traen el ubigeo sin el cero inicial en los
    departamentos 01-09: se normaliza a 6 dígitos antes de cualquier cruce."""
    ins = insumos.ultimo(rutas, "INS-CENAN-SIEN", recurso=RECURSO_SIEN)
    res.insumos.append(ins)
    id_insumo = str(getattr(ins, "hash", None) or getattr(ins.ruta, "name", str(ins.ruta)))
    partes, conteos, agregados, chequeos_hb, ren_eess, pn_635 = [], [], [], [], [], []
    archivos = {"Hb": [], "Pt": [], "otro": []}
    filas_hb_crudo, anios = 0, set()
    with abrir_zip_seguro(ins.ruta) as z:          # C7: rutas, enlaces, tamaños y proporciones revisados antes de leer (M1-02, H00b-7)
        for n in z.miembros():
            if not n.lower().endswith(".csv"):
                continue
            base = _base_sien(n)
            archivos[base].append(n.rsplit("/", 1)[-1])
            anios.update(re.findall(r"(20\d\d)", n))
            with tempfile.TemporaryFile() as f:      # el miembro se copia por bloques con tope y se lee del disco, no de memoria
                z.copiar(n, f)
                f.seek(0)
                cab = pd.read_csv(f, encoding="utf-8-sig", nrows=0).columns
                extra = [c for c in COLS_HB if c in cab] if base == "Hb" else []
                cols = ["Renipress", "EESS"] + [c for c in UBIGEOS_SIEN if c in cab] + extra
                f.seek(0)
                d = pd.read_csv(f, encoding="utf-8-sig", usecols=cols, dtype=str)
            crudo_5 = {c: int(d[c].str.strip().str.fullmatch(r"\d{5}").fillna(False).sum()) for c in UBIGEOS_SIEN if c in d}
            for c in UBIGEOS_SIEN:
                if c in d:
                    d[c] = L.ubigeo_normalizado(d[c])
            g = d.groupby([c for c in UBIGEOS_SIEN if c in d], dropna=False).size().rename("filas").reset_index()
            g["archivo"], g["base"] = n.split("/", 1)[-1], base
            conteos.append((g, crudo_5))
            partes.append(d[["Renipress", "Ubigeo_EESS", "EESS"]].drop_duplicates())
            if base == "Hb" and set(COLS_HB) <= set(d.columns):
                filas_hb_crudo += len(d)
                hb, hbc = pd.to_numeric(d.Hemoglobina, errors="coerce"), pd.to_numeric(d.Hbc, errors="coerce")
                edad = pd.to_numeric(d.EdadMeses, errors="coerce")
                dx = d.Dx_anemia.str.strip()
                esperado = dx_esperado(hbc, edad)
                hbc_calc = hb - ajuste_hb_oms2024(d.AlturaREN)
                edad_ok = edad.notna() & (edad >= 6) & (edad < 60)
                chequeos_hb.append(pd.DataFrame({
                    "archivo": [n.split("/", 1)[-1]], "filas": [len(d)],
                    # NaN cuenta como fallo: ~(|dif| <= tol)
                    "hbc_distinta_de_oms2024_o_nan": [int((~((hbc_calc - hbc).abs() <= TOL_HB)).sum())],
                    "dx_nulo_o_no_valido": [int((~dx.isin(DX_VALIDOS)).sum())],
                    "dx_distinto_de_cortes_oms2024": [int((esperado.isna() | (esperado != dx)).sum())],
                    "edad_fuera_de_6_59m_o_nula": [int((~edad_ok).sum())],
                    "altura_ren_cero": [int((pd.to_numeric(d.AlturaREN, errors="coerce") == 0).sum())]}))
                ren_eess.append(d[["Renipress", "UbigeoREN", "AlturaREN"]].drop_duplicates())
                # PN sobre la población del indicador de cobertura (6-35 m), por departamento del establecimiento
                m635 = edad_ok & (edad < 36)
                pn_635.append(pd.DataFrame({"departamento_eess": d.Ubigeo_EESS.str[:2], "filas": m635.astype(int),
                                            "sin_pn": (m635 & d.UbigeoPN.isna()).astype(int)})
                              .groupby("departamento_eess", as_index=False).sum())
                d["grupo_edad"] = pd.cut(edad, EDADES[0], right=False, labels=EDADES[1]).astype("object") \
                    .where(edad_ok, "fuera_de_rango")
                d["dx_valido"], d["con_anemia"] = marcar_anemia(d.Dx_anemia)
                a = d.groupby(["Renipress", "Ubigeo_EESS", "UbigeoPN", "UbigeoREN", "grupo_edad"], dropna=False) \
                     .agg(filas=("con_anemia", "size"), filas_con_anemia=("con_anemia", "sum"),
                          filas_dx_valido=("dx_valido", "sum")).reset_index()
                agregados.append(a)
    s = pd.concat(partes, ignore_index=True)
    s["cod_ipress"] = s.Renipress.str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(8)
    s["ubigeo_eess"] = s.Ubigeo_EESS
    # calidad por base, columna y departamento del establecimiento (todas las edades)
    filas = []
    for g, _ in conteos:
        dep = g.Ubigeo_EESS.str[:2].fillna("??")
        for c, rol in UBIGEOS_SIEN.items():
            if c not in g:
                continue
            nulo = g[c].isna()
            invalido = g[c].notna() & ~g[c].isin(alguna_vez)
            fuera_geo2017 = g[c].notna() & ~g[c].isin(geo2017) if geo2017 else pd.Series(False, index=g.index)
            distinto_eess = g[c].notna() & (g[c] != g.Ubigeo_EESS)
            t = pd.DataFrame({"base": g.base, "departamento_eess": dep, "filas": g.filas, "nulo": g.filas * nulo,
                              "invalido": g.filas * invalido, "fuera_geo2017": g.filas * fuera_geo2017,
                              "distinto_de_eess": g.filas * distinto_eess})
            t = t.groupby(["base", "departamento_eess"], as_index=False).sum()
            t["columna"], t["rol"] = c, rol
            filas.append(t)
    cal = pd.concat(filas).groupby(["base", "columna", "rol", "departamento_eess"], as_index=False).sum()
    for c in ["nulo", "invalido", "fuera_geo2017", "distinto_de_eess"]:
        cal[f"pct_{c}"] = (cal[c] / cal.filas).round(4)
    res.revision["sien_calidad_ubigeo"] = cal
    tot = cal[cal.base == "Hb"].groupby("columna")[["filas", "nulo", "invalido", "fuera_geo2017"]].sum()
    eess = cal.groupby("columna")[["filas", "nulo", "invalido"]].sum().loc["Ubigeo_EESS"]
    cinco = {c: sum(c5.get(c, 0) for _, c5 in conteos) for c in UBIGEOS_SIEN}
    res.prueba("E-05", "SIEN: ubigeo del establecimiento con 6 dígitos y existente en dim_ubigeo_historico en el 100 % de las filas",
               eess.nulo == 0 and eess.invalido == 0,
               {"filas": int(eess.filas), "nulos": int(eess.nulo), "invalidos": int(eess.invalido),
                "filas_con_5_digitos_en_el_crudo": cinco})
    if pn_635:
        p = pd.concat(pn_635).groupby("departamento_eess", as_index=False).sum()
        p["pct_pn_ubicado"] = (1 - p.sin_pn / p.filas).round(4)
        p["nivel_r_territorio_08"] = p.pct_pn_ubicado.map(nivel_r_territorio_08)
        res.revision["sien_pn_6_35m_por_departamento"] = p
        nac = 1 - p.sin_pn.sum() / p.filas.sum()
        res.prueba("E-06", "SIEN-Hb 6-35 m: procedencia del niño (UbigeoPN) ubicada ≥ 95 % (R-TERRITORIO-08, por carga). "
                   "Si no, la cobertura por procedencia va solo a departamento o nacional, con el % sin procedencia como residuo",
                   nac >= 0.95,
                   {"pct_pn_ubicado_nacional": round(float(nac), 4), "nivel_carga": nivel_r_territorio_08(nac),
                    "departamentos_por_nivel": p.nivel_r_territorio_08.value_counts().to_dict()}, bloqueante=False)
    if "UbigeoREN" in tot.index:
        ren = tot.loc["UbigeoREN"]
        res.prueba("E-07", "SIEN-Hb: UbigeoREN informado en el 100 % y existente en dim_ubigeo_historico",
                   ren.nulo == 0 and ren.invalido == 0,
                   {"nulos": int(ren.nulo), "invalidos": int(ren.invalido), "fuera_geo2017": int(ren.fuera_geo2017)},
                   bloqueante=False)
    if chequeos_hb:
        ch = pd.concat(chequeos_hb, ignore_index=True)
        res.revision["sien_hb_ajuste_altitud"] = ch
        sm = ch.drop(columns="archivo").sum()
        re_ = pd.concat(ren_eess).drop_duplicates()
        varios_ren = int(re_.groupby("Renipress").UbigeoREN.nunique(dropna=False).gt(1).sum())
        varias_alt = int(re_.groupby("UbigeoREN").AlturaREN.nunique(dropna=False).gt(1).sum())
        res.prueba("E-08", "SIEN-Hb (todo el ZIP): Hbc = Hemoglobina − ajuste OMS 2024 por AlturaREN (≥ 500 m), sin NaN; "
                   "Dx_anemia (normal/leve/moderada/severa) igual al de los cortes OMS 2024; un REN por establecimiento "
                   "y una altitud por REN",
                   sm.hbc_distinta_de_oms2024_o_nan == 0 and sm.dx_distinto_de_cortes_oms2024 == 0
                   and varios_ren == 0 and varias_alt == 0,
                   {**{k: int(v) for k, v in sm.items()}, "eess_con_varios_ren": varios_ren,
                    "ren_con_varias_altitudes": varias_alt}, bloqueante=False)
        res.prueba("E-10", "SIEN-Hb: Dx_anemia válido y edad en 6-59 m en el 100 % de las filas (si no, esas filas van a "
                   "grupo_edad='fuera_de_rango' y no cuentan como anemia)",
                   sm.dx_nulo_o_no_valido == 0 and sm.edad_fuera_de_6_59m_o_nula == 0,
                   {"dx_nulo_o_no_valido": int(sm.dx_nulo_o_no_valido),
                    "edad_fuera_de_6_59m_o_nula": int(sm.edad_fuera_de_6_59m_o_nula)})
    # E-09: completitud del ZIP. El número esperado sale de Hb (mismas DIRESA en Hb y Pt), no de una constante.
    n_hb, n_pt = len(archivos["Hb"]), len(archivos["Pt"])
    res.prueba("E-09", "SIEN: el ZIP trae los mismos archivos por DIRESA en Hb y en Pt",
               set(archivos["Hb"]) == set(archivos["Pt"]),
               {"Hb": n_hb, "Pt": n_pt, "faltan_en_Pt": sorted(set(archivos["Hb"]) - set(archivos["Pt"]))},
               bloqueante=False)
    if agregados:
        f = pd.concat(agregados, ignore_index=True)
        f["cod_ipress"] = f.Renipress.str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(8)
        f = f.rename(columns={"Ubigeo_EESS": "ubigeo_eess", "UbigeoPN": "ubigeo_procedencia",
                              "UbigeoREN": "ubigeo_ref_altitud"})
        clave = ["cod_ipress", "ubigeo_eess", "ubigeo_procedencia", "ubigeo_ref_altitud", "grupo_edad"]
        f = f.groupby(clave, dropna=False, as_index=False)[["filas", "filas_con_anemia", "filas_dx_valido"]].sum()
        f.insert(0, "anio", int(anios.pop()) if len(anios) == 1 else pd.NA)
        f.insert(1, "id_insumo", id_insumo)
        f["unidad"] = "nino_ultima_evaluacion_anio"  # supuesto, ver receta (pendiente de confirmar con el INS)
        f["criterio_anemia"] = "RM251-2024/OMS2024"
        f["version_tabla"] = VERSION_TABLA
        dup = int(f.duplicated(["anio", "id_insumo"] + clave).sum())
        res.prueba("E-11", "fact_sien_hb_ubigeo: clave única (anio, id_insumo, cod_ipress, 3 ubigeos, grupo_edad), anio "
                   "único en el ZIP y Σ filas = filas Hb leídas del crudo en esta corrida",
                   dup == 0 and f.anio.notna().all() and int(f.filas.sum()) == filas_hb_crudo,
                   {"duplicados_clave": dup, "anio": None if f.anio.isna().any() else int(f.anio.iloc[0]),
                    "filas_tabla": int(f.filas.sum()), "filas_crudo": filas_hb_crudo})
        res.tablas["fact_sien_hb_ubigeo"] = f
    return s.drop_duplicates(["cod_ipress", "ubigeo_eess"])[["cod_ipress", "ubigeo_eess", "EESS"]]


def construir(rutas: Rutas) -> Resultado:
    res = Resultado()
    import duckdb

    i_dim = insumos.tabla(rutas, "dim_ubigeo_historico")
    res.insumos.append(i_dim)
    dim = duckdb.sql(f"SELECT ubigeo_inei, nivel, vigente_desde, vigente_hasta FROM '{i_dim.ruta}'").df()
    alguna_vez = set(dim[dim.nivel == "distrito"].ubigeo_inei)
    geo2017 = set(duckdb.sql(f"SELECT DISTINCT ubigeo_inei FROM '{i_dim.ruta}' WHERE nivel = 'distrito' "
                             "AND origen = 'preexistente_2017'").df().ubigeo_inei)

    ipc = construir_ipc(rutas, res)
    est = construir_establecimientos(rutas, res, dim)
    sien = establecimientos_sien(rutas, res, alguna_vez, geo2017)
    por_cod = est.set_index("cod_ipress")
    sien["en_renipress"] = sien.cod_ipress.isin(por_cod.index)
    sien["ubigeo_renipress"] = sien.cod_ipress.map(por_cod.ubigeo_inei)
    sien["ubigeo_sien_valido"] = sien.ubigeo_eess.isin(alguna_vez)
    sien["ubicado"] = sien.en_renipress | sien.ubigeo_sien_valido
    sien["ubigeo_coincide"] = sien.ubigeo_renipress == sien.ubigeo_eess
    n = sien.cod_ipress.nunique()
    no_ubic = sien.loc[~sien.ubicado, "cod_ipress"].unique()
    res.prueba("E-03", "SIEN 2025: el 100 % de los establecimientos se ubica (código RENIPRESS o ubigeo válido)",
               len(no_ubic) == 0, {"establecimientos": n, "no_ubicados": list(no_ubic[:15]),
                                   "pct_en_renipress": round(float(sien.drop_duplicates('cod_ipress').en_renipress.mean()), 5)})
    con = sien[sien.en_renipress]
    pct_coinc = float(con.ubigeo_coincide.mean()) if len(con) else 0.0
    res.prueba("E-04", "SIEN 2025: el ubigeo del establecimiento coincide con el de RENIPRESS (≥ 98 %)", pct_coinc >= 0.98,
               {"pct": round(pct_coinc, 5), "distintos": int((~con.ubigeo_coincide).sum())}, bloqueante=False)
    res.revision["sien_ubigeo_distinto"] = con.loc[~con.ubigeo_coincide, ["cod_ipress", "EESS", "ubigeo_eess", "ubigeo_renipress"]]
    res.tablas = {"dim_ipc": ipc, "dim_establecimiento_salud": est, **res.tablas}
    return res
