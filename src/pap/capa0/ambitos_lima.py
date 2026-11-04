"""Ámbitos de Lima en los microdatos de encuestas: única fuente de la asignación (L1–L3, L5 y L8 del 9/10/2026).

Ámbitos (curados/capa0/ambitos.yaml):
- LIMA_METROPOLITANA: provincia 1501 (43 distritos, Ley 31140);
- LIMA_REGION: departamento 15 sin la 1501 (9 provincias), rótulo «Lima Región (Lima Provincias)»;
- CALLAO: departamento 07;
- AREA_METROPOLITANA_LIMA_CALLAO: 1501 + 07 = dominio 8 de la ENAHO, rótulo «Lima Metropolitana y Callao».

ENDES (endes_nino):
- desde 2018, por ubigeo del hogar (`provincia_hogar`, `departamento`) → método «ubigeo»;
- 2015–2017 (sin ubigeo en la base), por el estrato de diseño `id_estrato` = departamento × HV022: 15-1 = Sede =
  provincia de Lima; 15-2 y 15-3 = Resto urbano y Rural = Región Lima; 07-x = Callao → método «estrato_hv022».
  Base: Ficha técnica ENDES 2015/2016/2017, §3.6, Cuadro N.º 1 («Provincia de Lima 1/» 280/0/0, «Región Lima 2/»
  0/91/26) y su nota «Conglomerados de Sede, comprende a aquellos seleccionados en las capitales de departamento y la
  provincia de Lima» (auditoría de encuestas Lima, A3).

ENAHO (enaho_sumaria): columna `ambito_lima` (por ubigeo; ranking del INEI) y `lima_metropolitana_dominio8`
(variable DOMINIO = 8, verificado = 1501 + 07 en 2024–2025).

El motor, las cifras doradas y `encuestas.py` usan estas funciones; no se reimplementa la asignación en otro lado.
"""
from __future__ import annotations

import pandas as pd

LIMA_METROPOLITANA = "LIMA_METROPOLITANA"
LIMA_REGION = "LIMA_REGION"
CALLAO = "CALLAO"
AREA_METROPOLITANA_LIMA_CALLAO = "AREA_METROPOLITANA_LIMA_CALLAO"
AMBITOS = (LIMA_METROPOLITANA, LIMA_REGION, CALLAO)

METODO_UBIGEO = "ubigeo"
METODO_ESTRATO = "estrato_hv022"
METODO_DOMINIO = "variable_dominio"

ENDES_PRIMER_ANIO_UBIGEO = 2018
# Ficha ENDES 2015–2017, §3.6, Cuadro N.º 1: Sede (HV022 = 1) / Resto urbano (2) / Rural (3) del dpto 15
ENDES_ESTRATOS_2015_2017 = {"15-1": LIMA_METROPOLITANA, "15-2": LIMA_REGION, "15-3": LIMA_REGION}


def ambito_por_ubigeo(ubigeo: pd.Series) -> pd.Series:
    """LIMA_METROPOLITANA / LIMA_REGION / CALLAO / None a partir de un ubigeo INEI (≥ 4 dígitos) o su prefijo."""
    u = ubigeo.astype("string")
    out = pd.Series(pd.NA, index=ubigeo.index, dtype="object")
    out = out.mask(u.str.startswith("15").fillna(False), LIMA_REGION)
    out = out.mask(u.str.startswith("1501").fillna(False), LIMA_METROPOLITANA)
    out = out.mask(u.str.startswith("07").fillna(False), CALLAO)
    return out.where(out.notna(), None)


def _metodo_endes(df: pd.DataFrame) -> pd.Series:
    """Método con que se asigna cada fila de la ENDES: ubigeo si hay provincia del hogar; estrato en 2015–2017."""
    con_ubigeo = df["provincia_hogar"].notna() if "provincia_hogar" in df else pd.Series(False, index=df.index)
    metodo = pd.Series(None, index=df.index, dtype="object")
    metodo = metodo.mask(con_ubigeo, METODO_UBIGEO)
    metodo = metodo.mask(~con_ubigeo & (df["anio"] < ENDES_PRIMER_ANIO_UBIGEO), METODO_ESTRATO)
    return metodo


def ambito_lima_endes(df: pd.DataFrame) -> pd.Series:
    """Ámbito de Lima de cada niño de `endes_nino` (LIMA_METROPOLITANA / LIMA_REGION / CALLAO / None).

    Columnas usadas: anio, departamento, id_estrato y provincia_hogar. Fuera de los dpto 15 y 07 devuelve None.
    En 2015–2017 un estrato del dpto 15 fuera del Cuadro N.º 1 (15-1, 15-2, 15-3) queda en None: no se adivina."""
    metodo = _metodo_endes(df)
    por_ubigeo = ambito_por_ubigeo(df["provincia_hogar"]) if "provincia_hogar" in df else pd.Series(None, index=df.index)
    por_estrato = df["id_estrato"].map(ENDES_ESTRATOS_2015_2017)
    por_estrato = por_estrato.mask(df["departamento"] == "07", CALLAO)
    out = pd.Series(None, index=df.index, dtype="object", name="ambito_lima")
    out = out.mask(metodo == METODO_UBIGEO, por_ubigeo)
    out = out.mask(metodo == METODO_ESTRATO, por_estrato)
    return out.where(out.notna(), None).rename("ambito_lima")


def metodo_ambito_lima_endes(df: pd.DataFrame) -> pd.Series:
    """Método de `ambito_lima_endes` por fila (ubigeo / estrato_hv022), solo donde hay ámbito; None en el resto."""
    amb = ambito_lima_endes(df)
    return _metodo_endes(df).where(amb.notna(), None).rename("ambito_lima_metodo")


def ambito_lima_enaho(df: pd.DataFrame) -> pd.Series:
    """Ámbito de Lima de cada hogar de `enaho_sumaria`: la columna `ambito_lima` (si falta, se deriva del ubigeo).
    El ranking departamental del INEI publica estos tres ámbitos (informe técnico de pobreza; aviso ambito_no_dominio)."""
    if "ambito_lima" in df:
        return df["ambito_lima"].where(df["ambito_lima"].notna(), None).rename("ambito_lima")
    return ambito_por_ubigeo(df["ubigeo"]).rename("ambito_lima")


def dominio8_enaho(df: pd.DataFrame) -> pd.Series:
    """Hogares del dominio 8 de la ENAHO («Lima Metropolitana y Callao» = 1501 + 07): columna
    `lima_metropolitana_dominio8` (DOMINIO = 8), o la variable `dominio` si la columna no está."""
    if "lima_metropolitana_dominio8" in df:
        return df["lima_metropolitana_dominio8"].fillna(False).astype(bool)
    return (df["dominio"] == 8).fillna(False).astype(bool)


def mascara_ambito(df: pd.DataFrame, encuesta: str, ambito_id: str) -> pd.Series:
    """Filas que pertenecen a `ambito_id` (incluye AREA_METROPOLITANA_LIMA_CALLAO) en ENDES o ENAHO.
    Para estimar por dominio se usa como indicador z (z = 0 fuera), nunca para filtrar antes del diseño (R-ENC-01)."""
    encuesta = encuesta.upper()
    if encuesta == "ENAHO":
        if ambito_id == AREA_METROPOLITANA_LIMA_CALLAO:
            return dominio8_enaho(df)
        amb = ambito_lima_enaho(df)
    elif encuesta == "ENDES":
        amb = ambito_lima_endes(df)
        if ambito_id == AREA_METROPOLITANA_LIMA_CALLAO:
            return amb.isin([LIMA_METROPOLITANA, CALLAO])
    else:
        raise ValueError(f"encuesta sin ámbitos de Lima: {encuesta}")
    if ambito_id not in AMBITOS:
        raise ValueError(f"ámbito desconocido: {ambito_id}")
    return (amb == ambito_id).fillna(False).astype(bool)
