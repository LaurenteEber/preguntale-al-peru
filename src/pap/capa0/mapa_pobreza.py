"""Sprint S4 — Mapa de Pobreza Monetaria Provincial y Distrital 2018 (INEI), Anexo Estadístico, estandarizado en
biblioteca/estandarizada/mapa_pobreza/fact_mapa_pobreza.parquet.

El Excel tiene 29 hojas con encabezados de varias filas, notas al pie dentro de los datos y nombres con espacios:
- Anexo2: base completa (departamento → provincia → distrito), con el intervalo de confianza al 95 % y el «sufijo»
  de agrupamiento: los distritos chicos se estimaron juntos y comparten intervalo (Libro.pdf, cap. 5);
- Anexo1: los 28 grupos robustos nacionales de distritos (le falta Pachangara, 150906: queda sin grupo nacional);
- A3.1–A3.27: grupos robustos dentro de cada departamento (Lima en dos: provincia de Lima y Región Lima; no hay A3.15);
- A4: las 196 provincias con sus 16 grupos robustos.
Los «distritos desagregados» que mencionan las notas no son los agrupados: el Libro se refiere a una desagregación por
debajo del distrito aún no publicada (en revisión por la Comisión Consultiva); no afecta a la tabla.
El INEI no publica una cifra puntual: solo el intervalo. No se calcula un punto medio. La población que trae es la
proyectada a 2020. La geografía es la vigente en 2018 (1 874 distritos): los distritos creados después no tienen dato.
"""
from __future__ import annotations

import io
import re

import duckdb
import pandas as pd

from ..config import Rutas
from . import insumos
from .encuestas import Resultado

VERSION_TABLA = "1.0.0"
EDICION = 2018
FECHA_GEOGRAFIA = "2018-06-30"
# Cuadro N.º 5 del Libro (pp. 40–41): número de grupos robustos por departamento
GRUPOS_POR_DPTO = {"01": 6, "02": 9, "03": 3, "04": 8, "05": 7, "06": 7, "07": 4, "08": 9, "09": 7, "10": 5, "11": 4, "12": 6,
                   "13": 9, "14": 6, "16": 7, "17": 3, "18": 4, "19": 4, "20": 7, "21": 9, "22": 6, "23": 4, "24": 2,
                   "25": 4}
GRUPOS_LIMA = {"provincia_lima": 13, "region_lima": 9}


def _es_ubigeo(v) -> bool:
    return v is not None and bool(re.fullmatch(r"\d{6}", str(v).strip()))


def _filas(wb, hoja: str):
    for i, r in enumerate(wb[hoja].iter_rows(min_row=1, values_only=True), start=1):
        if i >= 8 and _es_ubigeo(r[0]):
            yield i, r


def _txt(v) -> str | None:
    s = None if v is None else str(v).strip()
    return s or None


def _int(v):
    s = _txt(v)
    return None if s is None else int(float(s))


def construir(rutas: Rutas) -> Resultado:
    import openpyxl

    res = Resultado()
    ins = insumos.ultimo(rutas, "INEI-MAPA-POBREZA", recurso="mapa-pobreza-2018-anexo")
    res.insumos.append(ins)
    wb = openpyxl.load_workbook(io.BytesIO(ins.ruta.read_bytes()), read_only=True, data_only=True)

    # ---- Anexo2: base
    dist, prov = [], []
    for fila, r in _filas(wb, "Anexo2"):
        u = str(r[0]).strip()
        if u.endswith("0000"):
            continue  # Perú y departamentos: sin intervalo publicado
        base = {"ubigeo_inei": u, "nombre_fuente": _txt(r[2]), "poblacion_proyectada_2020": _int(r[3]),
                "pobreza_ic_inf": r[4], "pobreza_ic_sup": r[5], "fila_anexo2": fila}
        if u.endswith("00"):
            prov.append(base)
        else:
            suf = _txt(r[1])
            dist.append({**base, "id_agrupamiento": None if suf in (None, "000") else suf,
                         "orden_nacional_anexo2": _int(r[6])})
    d = pd.DataFrame(dist)
    p = pd.DataFrame(prov)

    # ---- Anexo1: grupos robustos nacionales de distritos
    a1 = pd.DataFrame([{"ubigeo_inei": str(r[0]).strip(), "a1_ic_inf": r[5], "a1_ic_sup": r[6],
                        "grupo_robusto_nacional": _int(r[7]), "orden_nacional": _int(r[8])}
                       for _, r in _filas(wb, "Anexo1")])
    d = d.merge(a1, on="ubigeo_inei", how="left")
    # H-08: Pachangara (150906) falta en el Anexo1; su agrupamiento (128, con Andajes) está en el grupo 16 y el
    # Cuadro N.º 4 cuenta 106 distritos en el grupo 16: se infiere y se marca
    d["grupo_nacional_inferido"] = False
    for i in d.index[d.grupo_robusto_nacional.isna() & d.id_agrupamiento.notna()]:
        pares = d[(d.id_agrupamiento == d.at[i, "id_agrupamiento"]) & d.grupo_robusto_nacional.notna()]
        if pares.grupo_robusto_nacional.nunique() == 1:
            d.at[i, "grupo_robusto_nacional"] = int(pares.grupo_robusto_nacional.iloc[0])
            d.at[i, "grupo_nacional_inferido"] = True

    # ---- A3.x: grupos robustos regionales
    a3 = []
    for ws in wb.worksheets:
        if not ws.title.startswith("A3."):
            continue
        ambito = {"A3.16": "provincia_lima", "A3.17": "region_lima"}.get(ws.title, "departamento")
        for _, r in _filas(wb, ws.title):
            a3.append({"ubigeo_inei": str(r[0]).strip(), "a3_ic_inf": r[5], "a3_ic_sup": r[6],
                       "grupo_robusto_regional": _int(r[7]), "orden_regional": _int(r[8]),
                       "ambito_grupo_regional": ambito, "hoja_regional": ws.title})
    a3 = pd.DataFrame(a3)
    d = d.merge(a3, on="ubigeo_inei", how="left")

    # ---- A4: provincias
    a4 = pd.DataFrame([{"ubigeo_inei": str(r[0]).strip(), "a4_ic_inf": r[4], "a4_ic_sup": r[5],
                        "grupo_robusto_nacional": _int(r[6]), "orden_nacional": _int(r[7])}
                       for _, r in _filas(wb, "A4")])
    p = p.merge(a4, on="ubigeo_inei", how="left")

    # ---- territorio
    dim = insumos.tabla(rutas, "dim_ubigeo_historico")
    res.insumos.append(dim)
    vig = duckdb.sql(
        f"SELECT ubigeo_inei, nivel, nombre_mostrado, grupo_comparable_geo2017 FROM '{dim.ruta}' "
        f"WHERE vigente_desde <= '{FECHA_GEOGRAFIA}' AND (vigente_hasta IS NULL OR vigente_hasta >= '{FECHA_GEOGRAFIA}')"
    ).df()
    vd = vig[vig.nivel == "distrito"]
    vp = vig[vig.nivel == "provincia"]

    # ---- pruebas
    tol = 1e-9
    res.prueba("M-01", "Los distritos del Mapa son exactamente los vigentes al 30/6/2018 en dim_ubigeo_historico",
               set(d.ubigeo_inei) == set(vd.ubigeo_inei) and d.ubigeo_inei.is_unique,
               {"mapa": len(d), "dim": len(vd), "solo_mapa": sorted(set(d.ubigeo_inei) - set(vd.ubigeo_inei))[:10],
                "solo_dim": sorted(set(vd.ubigeo_inei) - set(d.ubigeo_inei))[:10]})
    res.prueba("M-02", "Las 196 provincias del Mapa son las vigentes en 2018 y cada distrito tiene su provincia",
               len(p) == 196 and set(p.ubigeo_inei) == set(vp.ubigeo_inei)
               and set(d.ubigeo_inei.str[:4] + "00") <= set(p.ubigeo_inei), {"provincias": len(p)})
    ics = pd.concat([d[["pobreza_ic_inf", "pobreza_ic_sup"]], p[["pobreza_ic_inf", "pobreza_ic_sup"]]])
    res.prueba("M-03", "Intervalos completos y coherentes: 0 ≤ inferior ≤ superior ≤ 100",
               ics.notna().all().all() and ((ics.pobreza_ic_inf >= 0) & (ics.pobreza_ic_inf <= ics.pobreza_ic_sup)
                                            & (ics.pobreza_ic_sup <= 100)).all())
    con_a1 = d.dropna(subset=["a1_ic_inf"])
    dif = max((con_a1.a1_ic_inf - con_a1.pobreza_ic_inf).abs().max(), (con_a1.a1_ic_sup - con_a1.pobreza_ic_sup).abs().max(),
              (d.a3_ic_inf - d.pobreza_ic_inf).abs().max(), (d.a3_ic_sup - d.pobreza_ic_sup).abs().max(),
              (p.a4_ic_inf - p.pobreza_ic_inf).abs().max(), (p.a4_ic_sup - p.pobreza_ic_sup).abs().max())
    res.prueba("M-04", "Anexo1, Anexo2, A3 y A4 traen el mismo intervalo para cada territorio", dif <= tol,
               {"diferencia_maxima": float(dif)})
    ag = d.dropna(subset=["id_agrupamiento"]).groupby("id_agrupamiento")
    res.prueba("M-05", "Los distritos de un mismo agrupamiento comparten intervalo y provincia",
               bool((ag.pobreza_ic_inf.nunique() == 1).all() and (ag.pobreza_ic_sup.nunique() == 1).all()
                    and (ag.ubigeo_inei.agg(lambda s: s.str[:4].nunique()) == 1).all()),
               {"agrupamientos": int(ag.ngroups), "distritos": int(d.id_agrupamiento.notna().sum())})
    sin_a1 = sorted(d[d.grupo_robusto_nacional.isna()].ubigeo_inei)
    inferidos = sorted(d[d.grupo_nacional_inferido].ubigeo_inei)
    n16 = int((d.grupo_robusto_nacional == 16).sum())
    res.prueba("M-06", "Grupos robustos nacionales de distritos: 28, todos con grupo; solo Pachangara (150906) "
               "inferido por su agrupamiento (grupo 16 con 106 distritos, Cuadro N.º 4)",
               set(d.grupo_robusto_nacional.dropna().astype(int)) == set(range(1, 29)) and not sin_a1
               and inferidos == ["150906"] and n16 == 106, {"sin_grupo": sin_a1, "inferidos": inferidos, "grupo_16": n16})
    res.prueba("M-07", "Grupos robustos provinciales: 16, del 1 al 16 (A4)",
               set(p.grupo_robusto_nacional.dropna().astype(int)) == set(range(1, 17)) and p.grupo_robusto_nacional.notna().all())
    d["dpto"] = d.ubigeo_inei.str[:2]
    por_dpto = d[d.ambito_grupo_regional == "departamento"].groupby("dpto").grupo_robusto_regional.nunique().to_dict()
    por_lima = d[d.ambito_grupo_regional != "departamento"].groupby("ambito_grupo_regional").grupo_robusto_regional.nunique().to_dict()
    malos = {k: (por_dpto.get(k), v) for k, v in GRUPOS_POR_DPTO.items() if por_dpto.get(k) != v}
    malos |= {k: (por_lima.get(k), v) for k, v in GRUPOS_LIMA.items() if por_lima.get(k) != v}
    res.prueba("M-08", "Grupos robustos regionales: cada distrito tiene uno y el número por departamento es el del "
               "Cuadro N.º 5 del Libro", d.grupo_robusto_regional.notna().all() and not malos, {"distintos": malos})
    orden = sorted(d.orden_nacional_anexo2.dropna().astype(int))
    res.prueba("M-09", "La ubicación nacional (Anexo2) es un orden completo de 1 a 1 874", orden == list(range(1, len(d) + 1)))
    pob = d.groupby(d.ubigeo_inei.str[:4] + "00").poblacion_proyectada_2020.sum()
    dif_pob = (p.set_index("ubigeo_inei").poblacion_proyectada_2020 - pob).abs().max()
    res.prueba("M-10", "La población 2020 de los distritos suma la de su provincia (±1 por redondeo)", dif_pob <= 1,
               {"diferencia_maxima": float(dif_pob)}, bloqueante=False)

    # ---- tabla
    comun = {"fuente_id": "INEI-MAPA-POBREZA", "edicion": EDICION, "anio_referencia": EDICION,
             "geografia_base": "vigente_2018", "version_tabla": VERSION_TABLA}
    td = pd.DataFrame({
        **comun, "nivel": "distrito", "ubigeo_inei": d.ubigeo_inei, "nombre_fuente": d.nombre_fuente,
        "poblacion_proyectada_2020": d.poblacion_proyectada_2020, "pobreza_ic_inf": d.pobreza_ic_inf,
        "pobreza_ic_sup": d.pobreza_ic_sup, "id_agrupamiento": d.id_agrupamiento,
        "estimado_en_agrupamiento": d.id_agrupamiento.notna(), "grupo_robusto_nacional": d.grupo_robusto_nacional,
        "grupo_nacional_inferido": d.grupo_nacional_inferido,
        "orden_nacional": d.orden_nacional_anexo2, "grupo_robusto_regional": d.grupo_robusto_regional,
        "ambito_grupo_regional": d.ambito_grupo_regional, "orden_regional": d.orden_regional,
        "hoja_origen": "Anexo2+Anexo1+" + d.hoja_regional, "fila_anexo2": d.fila_anexo2})
    tp = pd.DataFrame({
        **comun, "nivel": "provincia", "ubigeo_inei": p.ubigeo_inei, "nombre_fuente": p.nombre_fuente,
        "poblacion_proyectada_2020": p.poblacion_proyectada_2020, "pobreza_ic_inf": p.pobreza_ic_inf,
        "pobreza_ic_sup": p.pobreza_ic_sup, "id_agrupamiento": None, "estimado_en_agrupamiento": False,
        "grupo_robusto_nacional": p.grupo_robusto_nacional, "grupo_nacional_inferido": False,
        "orden_nacional": p.orden_nacional,
        "grupo_robusto_regional": pd.NA, "ambito_grupo_regional": None, "orden_regional": pd.NA,
        "hoja_origen": "Anexo2+A4", "fila_anexo2": p.fila_anexo2})
    t = pd.concat([td, tp], ignore_index=True)
    t = t.merge(vig[["ubigeo_inei", "nombre_mostrado", "grupo_comparable_geo2017"]], on="ubigeo_inei", how="left")
    for c in ("poblacion_proyectada_2020", "grupo_robusto_nacional", "orden_nacional", "grupo_robusto_regional",
              "orden_regional", "fila_anexo2"):
        t[c] = t[c].astype("Int64")
    t["pobreza_ic_inf"] = t.pobreza_ic_inf.astype(float).round(6)
    t["pobreza_ic_sup"] = t.pobreza_ic_sup.astype(float).round(6)
    res.prueba("M-11", "Todo territorio tiene nombre vigente y grupo comparable GEO2017",
               t.nombre_mostrado.notna().all() and t.grupo_comparable_geo2017.notna().all())
    res.tablas["fact_mapa_pobreza"] = t[[
        "fuente_id", "edicion", "anio_referencia", "geografia_base", "nivel", "ubigeo_inei", "nombre_mostrado",
        "nombre_fuente", "grupo_comparable_geo2017", "poblacion_proyectada_2020", "pobreza_ic_inf", "pobreza_ic_sup",
        "id_agrupamiento", "estimado_en_agrupamiento", "grupo_robusto_nacional", "grupo_nacional_inferido", "orden_nacional",
        "grupo_robusto_regional", "ambito_grupo_regional", "orden_regional", "hoja_origen", "fila_anexo2",
        "version_tabla"]]
    res.revision["mapa_pobreza_agrupamientos"] = (
        d.dropna(subset=["id_agrupamiento"]).sort_values(["id_agrupamiento", "ubigeo_inei"])
        [["id_agrupamiento", "ubigeo_inei", "nombre_fuente", "pobreza_ic_inf", "pobreza_ic_sup"]])
    return res
