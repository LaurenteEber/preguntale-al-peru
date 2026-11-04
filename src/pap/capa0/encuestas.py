"""Sprint S4 — Insumos del piloto: microdatos de la ENDES (niños < 5 años, 2015–2025) y de la ENAHO (Sumarias,
2024–2025) estandarizados en biblioteca/estandarizada/encuestas/.

Una fila por unidad de la encuesta (niño o hogar), con las variables de diseño (peso, estrato, conglomerado), el
territorio validado contra dim_ubigeo_historico y las variables del piloto ya recodificadas (los códigos especiales
pasan a nulo). No se calcula ningún indicador: eso lo hace el motor con dim_indicador, aplicando las definiciones de
curados/capa0/definiciones_endes.yaml. Las pruebas sí reproducen las cifras nacionales publicadas por el INEI
(cifras_control_inei.yaml) como control de que la recodificación es la correcta.
"""
from __future__ import annotations

import os
import re
import tempfile
import zipfile
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import yaml

from ..config import Rutas
from ..errores import PapError
from . import ambitos_lima as AL
from . import insumos

VERSION_TABLA = "1.1.0"  # 1.1.0 (9/10/2026): endes_nino.ambito_lima y ambito_lima_metodo (Lima en tres ámbitos)
ANIOS_ENDES = list(range(2015, 2026))
UBIGEOS_AGRUPADOS_INEI = {"120699"}  # código del INEI que agrupa distritos de Satipo (Junín) en la ENDES 2018–2020
ANIOS_ENAHO = [2024, 2025]
DPTOS = [f"{i:02d}" for i in range(1, 26)]


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


# ======================================================================= lectura

def leer_miembro(ins: insumos.Insumo, patron: str, columnas: set[str] | None = None):
    """Lee un .sav o .dta del ZIP del almacén. Devuelve (datos con nombres en MAYÚSCULAS, metadatos, miembro).
    pyreadstat necesita un archivo: se escribe en un temporal que se borra al salir (no queda copia del crudo)."""
    import pyreadstat

    with zipfile.ZipFile(ins.ruta) as z:
        nombres = [n for n in z.namelist() if re.search(patron, n.rsplit("/", 1)[-1], re.I)]
        if len(nombres) != 1:
            raise PapError(f"{ins.nombre}: se esperaba 1 miembro que cumpla {patron!r}, hay {nombres}")
        miembro = nombres[0]
        sufijo = os.path.splitext(miembro)[1].lower()
        with tempfile.NamedTemporaryFile(suffix=sufijo) as t:
            t.write(z.read(miembro))
            t.flush()
            lector = pyreadstat.read_sav if sufijo == ".sav" else pyreadstat.read_dta
            _, meta = lector(t.name, metadataonly=True)
            usar = None if columnas is None else [c for c in meta.column_names if c.upper() in columnas]
            # Los perdidos de usuario de SPSS llegan como nulo (por defecto); los códigos especiales de Stata (9, 999,
            # 9996–9999) llegan como número y se recodifican abajo, variable por variable.
            df, meta = lector(t.name, usecols=usar, apply_value_formats=False)
    df.columns = [c.upper() for c in df.columns]
    etiquetas = {k.upper(): v for k, v in meta.column_names_to_labels.items()}
    return df, etiquetas, miembro


def _entero(s: pd.Series, validos=None) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    if validos is not None:
        x = x.where(x.isin(validos))
    return x.astype("Int64")


def _rango(s: pd.Series, lo: float, hi: float, escala: float = 1.0) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    return (x.where((x >= lo) & (x <= hi)) / escala).astype("Float64")


def _texto_id(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    if x.notna().all():
        return x.astype("int64").astype(str)
    return s.astype(str).str.strip()


def _ubigeos_vigentes(rutas: Rutas, anio: int) -> tuple[set[str], insumos.Insumo]:
    import duckdb

    dim = insumos.tabla(rutas, "dim_ubigeo_historico")
    fecha = f"{anio}-06-30"
    q = (f"SELECT ubigeo_inei FROM '{dim.ruta}' WHERE vigente_desde <= '{fecha}' "
         f"AND (vigente_hasta IS NULL OR vigente_hasta >= '{fecha}')")
    return {r[0] for r in duckdb.sql(q).fetchall()}, dim


# ======================================================================= ENDES

def _endes_anio(rutas: Rutas, anio: int, res: Resultado, etiquetas_out: list) -> pd.DataFrame:
    hog = insumos.ultimo(rutas, "INEI-ENDES", recurso=f"endes-{anio}-hogar")
    ane = insumos.ultimo(rutas, "INEI-ENDES", recurso=f"endes-{anio}-anemia")
    res.insumos += [hog, ane]
    d0, e0, m0 = leer_miembro(hog, r"^RECH0(_\d{4})?\.(sav|dta)$",
                              {"HHID", "HV005", "HV021", "HV022", "HV024", "HV025", "UBIGEO"})
    d1, _, m1 = leer_miembro(hog, r"^RECH1(_\d{4})?\.(sav|dta)$", {"HHID", "HVIDX", "HV102", "HV103"})
    d6, e6, m6 = leer_miembro(ane, r"^RECH6(_\d{4})?\.(sav|dta)$",
                              {"HHID", "HC0", "HC1", "HC13", "HC27", "HC53", "HC55", "HC56", "HC56A", "HC57", "HC57A",
                               "HC70", "HV005A"})
    for v in ("HC56", "HC56A", "HC57", "HC57A", "HC70", "HV005A"):
        if v in e6:
            etiquetas_out.append({"anio": anio, "archivo": m6, "variable": v, "etiqueta": e6[v]})
    for d in (d0, d1, d6):
        d["HHID"] = d.HHID.astype(str).str.strip()
    d6["HC0"] = pd.to_numeric(d6.HC0).astype("int64")
    d1["HVIDX"] = pd.to_numeric(d1.HVIDX).astype("int64")
    n6 = len(d6)
    m = d6.merge(d1, left_on=["HHID", "HC0"], right_on=["HHID", "HVIDX"], how="left", indicator="_r1")
    m = m.merge(d0, on="HHID", how="left", indicator="_r0")
    sin_r1, sin_r0 = int((m._r1 != "both").sum()), int((m._r0 != "both").sum())
    res.prueba(f"E-{anio}-01", f"ENDES {anio}: cada niño de RECH6 se une a RECH1 (miembro) y a RECH0 (hogar)",
               len(m) == n6 and sin_r1 == 0 and sin_r0 == 0, {"filas": n6, "sin_rech1": sin_r1, "sin_rech0": sin_r0})

    out = pd.DataFrame({
        "fuente_id": "INEI-ENDES",
        "anio": anio,
        "id_hogar": m.HHID,
        "idx_nino": m.HC0.astype("int64"),
        "id_conglomerado": _texto_id(m.HV021),
        # H-01 (auditoría S4): en 2015–2017 HV022 solo tiene 3 valores que cruzan departamentos; el estrato de diseño
        # es departamento × HV022 (en 2018+ HV022 ya está anidado en el departamento: el prefijo no cambia nada)
        "id_estrato": pd.to_numeric(m.HV024).astype("int64").map(lambda x: f"{x:02d}") + "-" + _texto_id(m.HV022),
        "departamento": pd.to_numeric(m.HV024).astype("int64").map(lambda x: f"{x:02d}"),
        "area": _entero(m.HV025, [1, 2]).map({1: "urbano", 2: "rural"}),
        "ubigeo_hogar": m.UBIGEO.astype(str).str.strip().str.zfill(6) if "UBIGEO" in m else None,
        "peso_hogar": pd.to_numeric(m.HV005) / 1e6,
        "peso_medicion": (pd.to_numeric(m.HV005A) / 1e6) if "HV005A" in m else np.nan,
        "pernocto": pd.to_numeric(m.HV103) == 1,
        "residente_habitual": pd.to_numeric(m.HV102) == 1,
        "edad_meses": _entero(m.HC1),
        "sexo": _entero(m.HC27, [1, 2]).map({1: "hombre", 2: "mujer"}),
        "hb_resultado": _entero(m.HC55, [0, 1, 2, 3, 4, 5, 6]),
        "hb_observada": _rango(m.HC53, 30, 250, 10),
        "hb_ajustada_hist": _rango(m.HC56, 30, 250, 10),
        "hb_ajustada_oms2024": _rango(m.HC56A, 30, 250, 10) if "HC56A" in m else pd.NA,
        "anemia_hist_nivel": _entero(m.HC57, [1, 2, 3, 4]),
        "anemia_oms2024_nivel": _entero(m.HC57A, [1, 2, 3, 4]) if "HC57A" in m else pd.NA,
        "talla_resultado": _entero(m.HC13, [0, 1, 2, 3, 4, 5, 6]),
        "haz": _rango(m.HC70, -9989, 9989, 100),
        "haz_bandera": _entero(m.HC70.where(pd.to_numeric(m.HC70, errors="coerce") >= 9990)),
    })
    out["provincia_hogar"] = out.ubigeo_hogar.str[:4]
    # H-04: 120699 (2018–2020) agrupa distritos de Satipo (VRAEM); solo es agregable a provincia
    out["ubigeo_agrupado_inei"] = out.ubigeo_hogar.isin(UBIGEOS_AGRUPADOS_INEI)
    out["peso"] = out.peso_medicion.where(out.peso_medicion.notna(), out.peso_hogar)
    out["fuente_peso"] = np.where(out.peso_medicion.notna(), "HV005A/1e6 (mediciones 2020)", "HV005/1e6")
    out["hb_medida"] = out.hb_resultado == 0
    for crit in ("hist", "oms2024"):
        niv = out[f"anemia_{crit}_nivel"]
        out[f"anemia_{crit}"] = (niv <= 3).astype("boolean").where(niv.notna())
    out["haz_valido"] = out.haz.notna()
    out["dci"] = (out.haz < -2).astype("boolean").where(out.haz_valido)
    out["dci_severa"] = (out.haz < -3).astype("boolean").where(out.haz_valido)
    out["version_tabla"] = VERSION_TABLA
    for c in ("hb_resultado", "anemia_hist_nivel", "anemia_oms2024_nivel", "talla_resultado", "edad_meses", "haz_bandera"):
        out[c] = out[c].astype("Int64")
    for c in ("hb_ajustada_oms2024",):
        out[c] = out[c].astype("Float64")
    out["ubigeo_hogar"] = out.ubigeo_hogar.astype("string")

    # pruebas por año
    res.prueba(f"E-{anio}-02", f"ENDES {anio}: clave (id_hogar, idx_nino) única",
               not out.duplicated(["id_hogar", "idx_nino"]).any())
    res.prueba(f"E-{anio}-03", f"ENDES {anio}: 25 departamentos (HV024) y pesos positivos",
               set(out.departamento) == set(DPTOS) and (out.peso > 0).all(),
               {"departamentos": sorted(set(out.departamento) ^ set(DPTOS)), "pesos_no_positivos": int((out.peso <= 0).sum())})
    inc = out[out.hb_medida & out.anemia_hist_nivel.isna()]
    res.prueba(f"E-{anio}-04", f"ENDES {anio}: todo niño con hemoglobina medida tiene nivel de anemia (HC57)",
               len(inc) <= max(2, 0.001 * out.hb_medida.sum()), {"medidos_sin_nivel": len(inc)})
    edad_ok = out.edad_meses.between(0, 59).all()
    res.prueba(f"E-{anio}-05", f"ENDES {anio}: edades entre 0 y 59 meses", bool(edad_ok))
    if out.ubigeo_hogar.notna().any():
        vig, dim = _ubigeos_vigentes(rutas, anio)
        if dim not in res.insumos:
            res.insumos.append(dim)
        fuera = sorted(set(out.ubigeo_hogar.dropna()) - vig - UBIGEOS_AGRUPADOS_INEI)
        res.prueba(f"E-{anio}-06", f"ENDES {anio}: el ubigeo del hogar existe en dim_ubigeo_historico ese año",
                   len(fuera) == 0, {"fuera": fuera[:20], "n": len(fuera)}, bloqueante=False)
        dp = (out.ubigeo_hogar.str[:2] != out.departamento) & out.ubigeo_hogar.notna()
        res.prueba(f"E-{anio}-07", f"ENDES {anio}: el ubigeo del hogar es del mismo departamento que HV024",
                   int(dp.sum()) == 0, {"distintos": int(dp.sum())})
    # H-01/H-02: cada estrato en un solo departamento y una sola área; se cuentan los estratos con un conglomerado
    por_estrato = out.groupby("id_estrato").agg(dptos=("departamento", "nunique"), areas=("area", "nunique"),
                                                conglomerados=("id_conglomerado", "nunique"))
    res.prueba(f"E-{anio}-08", f"ENDES {anio}: cada estrato de diseño cae en un solo departamento y una sola área",
               bool((por_estrato.dptos == 1).all() and (por_estrato.areas == 1).all()),
               {"estratos": len(por_estrato), "mezclados": int(((por_estrato.dptos > 1) | (por_estrato.areas > 1)).sum())})
    cong_estrato = out.groupby("id_conglomerado").id_estrato.nunique()
    res.prueba(f"E-{anio}-09", f"ENDES {anio}: cada conglomerado está en un solo estrato", bool((cong_estrato == 1).all()))
    etiquetas_out.append({"anio": anio, "archivo": "(diseño)", "variable": "estratos_con_un_conglomerado",
                          "etiqueta": str(int((por_estrato.conglomerados == 1).sum())) + f" de {len(por_estrato)}"})
    return out


def _en_universo(df: pd.DataFrame, anio: int, defi: dict) -> pd.Series:
    u = dict(defi["universo"])
    u.update((defi.get("excepciones") or {}).get(anio, {}))
    mask = pd.Series(True, index=df.index)
    lo, hi = u["edad_meses"]
    mask &= df.edad_meses.between(lo, hi).fillna(False)
    if u.get("hb_medida"):
        mask &= df.hb_medida.fillna(False)
    if u.get("variable_no_nula"):
        mask &= df[defi["variable"]].notna()
    if u.get("haz_valido"):
        mask &= df.haz_valido
    if u.get("pernocto"):
        mask &= df.pernocto
    return mask.astype(bool)


def proporcion_puntual(df: pd.DataFrame, variable: str, peso: str = "peso") -> float:
    """Solo la cifra puntual, para el control contra el INEI (la estimación con diseño la hace el motor)."""
    x = df[variable].astype(float)
    return float(100 * np.average(x, weights=df[peso]))


def _controles_endes(rutas: Rutas, endes: pd.DataFrame, res: Resultado) -> pd.DataFrame:
    defs = yaml.safe_load(insumos.curado(rutas, "definiciones_endes.yaml").ruta.read_text(encoding="utf-8"))
    ctrl = yaml.safe_load(insumos.curado(rutas, "cifras_control_inei.yaml").ruta.read_text(encoding="utf-8"))
    res.insumos += [insumos.curado(rutas, "definiciones_endes.yaml"), insumos.curado(rutas, "cifras_control_inei.yaml")]
    tol = float(ctrl["tolerancia_pp"])
    filas = []
    c = ctrl["endes"]

    def agrega(ind, anio, ambito, s, var, pub, informativo=False):
        if len(s) == 0:
            return
        est = proporcion_puntual(s, var)
        filas.append({"fuente": "ENDES", "indicador": ind, "anio": anio, "ambito": ambito, "n": len(s),
                      "estimacion_pct": round(est, 2), "publicado_inei_pct": pub, "informativo": informativo,
                      "diferencia_pp": None if pub is None else round(round(est, 1) - pub, 2)})
    for ind, defi in defs["indicadores"].items():
        for anio in ANIOS_ENDES:
            d = endes[endes.anio == anio]
            if defi["variable"] not in d or d[defi["variable"]].isna().all():
                continue
            s = d[_en_universo(d, anio, defi)]
            v = defi["variable"]
            agrega(ind, anio, "nacional", s, v, (c.get(ind) or {}).get(anio))
            for area, valor in (("urbana", "urbano"), ("rural", "rural")):
                agrega(ind, anio, area, s[s.area == valor], v, (c.get(f"{ind}_{area}") or {}).get(anio))
            for clave, informativo in ((f"{ind}_departamento_{anio}", False),
                                       (f"{ind}_departamento_{anio}_informativo", True)):
                for dp, pub in (c.get(clave) or {}).items():
                    agrega(ind, anio, f"departamento_{dp}", s[s.departamento == dp], v, pub, informativo)
    t = pd.DataFrame(filas)
    con = t.dropna(subset=["publicado_inei_pct"])
    con = con[~con.informativo]
    malas = con[con.diferencia_pp.abs() > tol + 1e-9]
    res.prueba("E-10", f"ENDES: las cifras nacionales reproducen las publicadas por el INEI (±{tol} pp)",
               malas.empty, {"comparadas": len(con), "fuera": malas[["indicador", "anio", "estimacion_pct",
                                                                    "publicado_inei_pct"]].to_dict("records")})
    return t


def _pruebas_ambito_endes(endes: pd.DataFrame, res: Resultado) -> None:
    """E-11/E-12: la asignación de LM, LR y Callao es completa y no parte ningún estrato ni conglomerado."""
    lima = endes[endes.departamento.isin(["15", "07"])]
    sin = lima[lima.ambito_lima.isna()].groupby("anio").size().to_dict()
    desde18 = endes[endes.anio >= AL.ENDES_PRIMER_ANIO_UBIGEO]
    lm_ok = bool(((desde18.ambito_lima == AL.LIMA_METROPOLITANA) == (desde18.provincia_hogar == "1501")).all())
    res.prueba("E-11", "ENDES: todo niño de los dpto 15 y 07 tiene ámbito de Lima; desde 2018 LM ⇔ provincia 1501",
               not sin and lm_ok, {"sin_ambito_por_anio": sin, "lm_igual_1501": lm_ok})
    amb = lima.ambito_lima.fillna("-")
    mezcla = {}
    for clave in ("id_estrato", "id_conglomerado"):
        n = amb.groupby([lima.anio, lima[clave]]).nunique()
        mezcla[clave] = int((n > 1).sum())
    res.prueba("E-12", "ENDES: ningún estrato ni conglomerado de los dpto 15 y 07 mezcla ámbitos (todos los años)",
               mezcla["id_estrato"] == 0 and mezcla["id_conglomerado"] == 0, mezcla)


def construir_endes(rutas: Rutas) -> Resultado:
    res = Resultado()
    partes, etiquetas = [], []
    for anio in ANIOS_ENDES:
        partes.append(_endes_anio(rutas, anio, res, etiquetas))
    endes = pd.concat(partes, ignore_index=True)
    # Lima en tres ámbitos (L2, 9/10/2026): una sola función asigna el ámbito (ambitos_lima.py)
    endes["ambito_lima"] = AL.ambito_lima_endes(endes)
    endes["ambito_lima_metodo"] = AL.metodo_ambito_lima_endes(endes)
    _pruebas_ambito_endes(endes, res)
    endes = endes[[
        "fuente_id", "anio", "id_hogar", "idx_nino", "id_conglomerado", "id_estrato", "departamento", "area",
        "ubigeo_hogar", "provincia_hogar", "ambito_lima", "ambito_lima_metodo", "ubigeo_agrupado_inei", "peso", "fuente_peso", "peso_hogar", "peso_medicion", "pernocto", "residente_habitual",
        "edad_meses", "sexo", "hb_resultado", "hb_medida", "hb_observada", "hb_ajustada_hist", "anemia_hist_nivel",
        "anemia_hist", "hb_ajustada_oms2024", "anemia_oms2024_nivel", "anemia_oms2024", "talla_resultado", "haz",
        "haz_bandera", "haz_valido", "dci", "dci_severa", "version_tabla"]]
    res.prueba("E-08", "ENDES: la nueva directriz OMS 2024 (HC57A) solo existe desde 2024",
               endes[endes.anio < 2024].anemia_oms2024_nivel.isna().all()
               and endes[endes.anio >= 2024].anemia_oms2024_nivel.notna().any())
    res.prueba("E-09", "ENDES: el peso de las mediciones (HV005A) solo se usa en 2020",
               set(endes[endes.peso_medicion.notna()].anio) == {2020})
    res.revision["endes_controles_inei"] = _controles_endes(rutas, endes, res)
    res.revision["endes_etiquetas"] = pd.DataFrame(etiquetas)
    res.tablas["endes_nino"] = endes
    return res


# ======================================================================= ENAHO


def _enaho_anio(rutas: Rutas, anio: int, res: Resultado) -> pd.DataFrame:
    ins = insumos.ultimo(rutas, "INEI-ENAHO", recurso=f"enaho-{anio}-sumaria")
    res.insumos.append(ins)
    d, _, miembro = leer_miembro(ins, rf"^sumaria-{anio}\.dta$", {
        "MES", "CONGLOME", "VIVIENDA", "HOGAR", "UBIGEO", "DOMINIO", "ESTRATO", "MIEPERHO", "TOTMIEHO", "FACTOR07",
        "POBREZA", "LINEA", "LINPE", "GASHOG2D", "INGHOG2D"})
    out = pd.DataFrame({
        "fuente_id": "INEI-ENAHO",
        "anio": anio,
        "mes": _entero(d.MES),
        "id_conglomerado": d.CONGLOME.astype(str).str.strip(),
        "vivienda": d.VIVIENDA.astype(str).str.strip(),
        "hogar": d.HOGAR.astype(str).str.strip(),
        "ubigeo": d.UBIGEO.astype(str).str.strip().str.zfill(6),
        "dominio": _entero(d.DOMINIO, list(range(1, 9))),
        "estrato": _entero(d.ESTRATO, list(range(1, 9))),
        "mieperho": _entero(d.MIEPERHO),
        "totmieho": _entero(d.TOTMIEHO),
        "factor07": pd.to_numeric(d.FACTOR07),
        "pobreza": _entero(d.POBREZA, [1, 2, 3]),
        "linea": pd.to_numeric(d.LINEA),
        "linpe": pd.to_numeric(d.LINPE),
        "gashog2d": pd.to_numeric(d.GASHOG2D),
        "inghog2d": pd.to_numeric(d.INGHOG2D),
    })
    out["departamento"] = out.ubigeo.str[:2]
    out["provincia"] = out.ubigeo.str[:4]
    # Diseño: la muestra es «independiente en cada departamento» (ficha técnica), así que el estrato de diseño es
    # departamento × estrato (auditoría del oráculo, A3, 9/10/2026); se conserva el estrato original
    out["id_estrato_diseno"] = out.departamento + "-" + out.estrato.astype(str)
    out["area"] = np.where(out.estrato <= 5, "urbano", "rural")  # INEI: estratos 1–5 urbano, 6–8 rural
    # ranking departamental del INEI: Lima Metropolitana = provincia 1501 (ambitos_lima.py, única asignación)
    out["ambito_lima"] = AL.ambito_por_ubigeo(out.ubigeo)
    # H-05: en las tablas por área o dominio, «Lima Metropolitana» es el dominio 8 (provincia de Lima + Callao)
    out["lima_metropolitana_dominio8"] = out.dominio == 8
    out["peso_persona"] = out.factor07 * out.mieperho
    out["pobre"] = out.pobreza <= 2
    out["pobre_extremo"] = out.pobreza == 1
    out["version_tabla"] = VERSION_TABLA
    vig, dim = _ubigeos_vigentes(rutas, anio)
    if dim not in res.insumos:
        res.insumos.append(dim)
    fuera = sorted(set(out.ubigeo) - vig)
    res.prueba(f"H-{anio}-01", f"ENAHO {anio}: clave (conglomerado, vivienda, hogar) única y sin nulos en diseño",
               not out.duplicated(["id_conglomerado", "vivienda", "hogar"]).any()
               and out[["factor07", "mieperho", "estrato", "pobreza"]].notna().all().all())
    res.prueba(f"H-{anio}-02", f"ENAHO {anio}: el ubigeo existe en dim_ubigeo_historico ese año", len(fuera) == 0,
               {"fuera": fuera[:20], "n": len(fuera)})
    res.prueba(f"H-{anio}-03", f"ENAHO {anio}: 25 departamentos y factor positivo",
               set(out.departamento) == set(DPTOS) and (out.factor07 > 0).all())
    # D-01 (auditoría Lima, A4): el dominio 8 es exactamente la provincia 1501 más el Callao
    lm_c = out.ambito_lima.isin([AL.LIMA_METROPOLITANA, AL.CALLAO])
    res.prueba(f"H-{anio}-04", f"ENAHO {anio}: dominio 8 = provincia 1501 + Callao (07)",
               bool((out.lima_metropolitana_dominio8 == lm_c).all()),
               {"d8_fuera": int((out.lima_metropolitana_dominio8 & ~lm_c).sum()),
                "faltan_en_d8": int((~out.lima_metropolitana_dominio8 & lm_c).sum())})
    return out


def _controles_enaho(rutas: Rutas, enaho: pd.DataFrame, res: Resultado) -> pd.DataFrame:
    ctrl = yaml.safe_load(insumos.curado(rutas, "cifras_control_inei.yaml").ruta.read_text(encoding="utf-8"))
    res.insumos.append(insumos.curado(rutas, "cifras_control_inei.yaml"))
    tol = float(ctrl["tolerancia_pp"])
    c = ctrl["enaho"]
    filas = []

    def agrega(ind, anio, ambito, d, var, pub):
        est = proporcion_puntual(d, var, "peso_persona")
        filas.append({"fuente": "ENAHO", "indicador": ind, "anio": anio, "ambito": ambito, "n": len(d),
                      "estimacion_pct": round(est, 2), "publicado_inei_pct": pub,
                      "diferencia_pp": None if pub is None else round(round(est, 1) - pub, 2)})
    for anio in ANIOS_ENAHO:
        d = enaho[enaho.anio == anio]
        agrega("pobreza_monetaria", anio, "nacional", d, "pobre", c["pobreza_monetaria"].get(anio))
        agrega("pobreza_extrema", anio, "nacional", d, "pobre_extremo", c["pobreza_extrema"].get(anio))
        for area, valor in (("urbana", "urbano"), ("rural", "rural")):
            agrega(f"pobreza_monetaria_{area}", anio, area, d[d.area == valor], "pobre",
                   (c.get(f"pobreza_monetaria_{area}") or {}).get(anio))
        for dp in DPTOS:
            agrega("pobreza_monetaria", anio, f"departamento_{dp}", d[d.departamento == dp], "pobre",
                   (c.get(f"pobreza_monetaria_departamento_{anio}") or {}).get(dp))
        for amb, pub in (c.get(f"pobreza_monetaria_lima_{anio}") or {}).items():
            agrega("pobreza_monetaria", anio, f"ambito_{amb}", d[d.ambito_lima == amb], "pobre", pub)
        d8 = d.lima_metropolitana_dominio8
        agrega("pobreza_extrema", anio, "lima_metropolitana_dominio8", d[d8], "pobre_extremo",
               (c.get("pobreza_extrema_lima_metropolitana_dominio8") or {}).get(anio))
        agrega("pobreza_extrema", anio, "resto_urbano", d[(d.area == "urbano") & ~d8], "pobre_extremo",
               (c.get("pobreza_extrema_resto_urbano") or {}).get(anio))
        agrega("pobreza_extrema", anio, "rural", d[d.area == "rural"], "pobre_extremo",
               (c.get("pobreza_extrema_rural") or {}).get(anio))
    t = pd.DataFrame(filas)
    con = t.dropna(subset=["publicado_inei_pct"])
    malas = con[con.diferencia_pp.abs() > tol + 1e-9]
    res.prueba("H-10", f"ENAHO: las cifras reproducen las publicadas por el INEI (±{tol} pp)", malas.empty,
               {"comparadas": len(con), "fuera": malas[["indicador", "anio", "ambito", "estimacion_pct",
                                                       "publicado_inei_pct"]].to_dict("records")})
    return t


def construir_enaho(rutas: Rutas) -> Resultado:
    res = Resultado()
    enaho = pd.concat([_enaho_anio(rutas, a, res) for a in ANIOS_ENAHO], ignore_index=True)
    enaho = enaho[[
        "fuente_id", "anio", "mes", "id_conglomerado", "vivienda", "hogar", "ubigeo", "departamento", "provincia",
        "ambito_lima", "lima_metropolitana_dominio8", "dominio", "estrato", "id_estrato_diseno", "area", "mieperho", "totmieho", "factor07",
        "peso_persona", "pobreza", "pobre", "pobre_extremo", "linea", "linpe", "gashog2d", "inghog2d",
        "version_tabla"]]
    res.revision["enaho_controles_inei"] = _controles_enaho(rutas, enaho, res)
    res.tablas["enaho_sumaria"] = enaho
    return res
