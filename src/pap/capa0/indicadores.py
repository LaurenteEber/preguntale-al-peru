"""Piloto — tablas curadas de indicadores: dim_indicador, cruces_permitidos y cifras_doradas.

Fuentes de verdad (curadas a mano y versionadas en git, curados/capa0/):
- dim_indicador.yaml: los indicadores del piloto con todos los campos de nivel indicador (diccionario de reglas.md;
  R-MOTOR-02 suprime una cifra si falta un metadato). Nombres de campos y vocabularios: reglas/reglas.json.
- cruces_permitidos.yaml: lista blanca de cruces (R-CRUCES-11); solo los `activo_piloto` se calculan.
- cifras_doradas.csv: cifras publicadas por el INEI contra las que el motor se compara antes de publicar (R-ENC-18).

Las tres se propusieron por analistas y se revisaron por auditores independientes (03_auditoria/piloto_tablas_curadas/).
Este constructor no decide nada: valida y escribe. Comprueba que los campos que leen las reglas estén, que los
vocabularios sean los controlados, que los insumos estén aprobados en el catálogo (R-DEP-01), que años, definiciones
y temas existan en las tablas de la capa 0, y que nuestros datos estandarizados reproduzcan las cifras doradas.
La estimación con diseño (svy, IC Korn-Graubard, CV) es del motor; aquí solo la cifra puntual y los casos.
"""
from __future__ import annotations

import json
import re

import duckdb
import numpy as np
import pandas as pd
import yaml

from ..config import Rutas
from . import ambitos_lima, insumos, salida
from .encuestas import Resultado, _en_universo

VERSION_TABLA = "1.1.0"

# Estados de dim_indicador y de cruces_permitidos
ESTADOS_INDICADOR = {"activo_piloto", "piloto_ampliado"}
ESTADOS_CRUCE = {"activo_piloto", "opcion_dueno"}

# Campos que todo indicador debe traer no nulos (diccionario de reglas.md + alcance de las 68 reglas del validador:
# 04_reglas/auditoria/piloto_alcance/; completitud por regla en analista_indicadores/completitud_resultado.csv).
OBLIGATORIOS = [
    "id", "estado_propuesta", "preguntas", "nombre_ciudadano", "nombre_tecnico", "tema", "concepto_medido",
    "rank_concepto", "criterio_medicion", "fuente_principal", "naturaleza_dato", "tipo_medida", "base_geografica_usada",
    "tipo_estimacion", "unidad", "origen_cifra", "poblacion_objetivo", "universo", "unidad_observacion",
    "es_socioeconomico", "velocidad_cambio", "sensibilidad_divulgacion", "subregistro_conocido", "insumos",
    "requiere_denominador", "tipo_denominador", "denominador_principal", "requiere_estandarizacion",
    "n_desagregaciones_adicionales", "tasa_suavizada", "periodicidad_estimacion", "nivel_territorial_inferencia",
    "niveles_validos", "anios_disponibles", "tabla_origen", "definicion",
]
# Además, en las encuestas muestrales (R-ENC-01, R-ENC-06, R-ENC-08, R-ENC-14)
OBLIGATORIOS_ENCUESTA = ["variables_diseno", "dominios_inferencia", "tipo_aplicacion", "metodo_ic", "modulo_encuesta",
                         "validado_contra_oficial"]
# En el gasto no aplica R-ENC-18: su control es la conciliación con la Consulta Amigable (R-GASTO-04)

# Vocabularios controlados (reglas/reglas.json → campos y parametros_globales). Los de H1 (tema, universo,
# periodicidad_estimacion, concepto_medido) se leen de parametros_globales.VOCABULARIOS_INDICADOR (P0, 10/10/2026).
VOCAB_H1 = ("tema", "universo", "periodicidad_estimacion", "concepto_medido")
VOCAB = {
    "velocidad_cambio": {"rapida", "lenta"},
    "rank_concepto": {1, 2},
    "tipo_estimacion": {"proporcion", "total", "media", "razon", "tasa", "modelada", "propia"},
    "sensibilidad_divulgacion": {"ninguna", "normal", "sensible"},
    "unidad_observacion": {"persona", "hogar", "estudiante", "caso", "establecimiento", "entidad"},
    "tipo_aplicacion": {"censal", "muestral", None},
    "origen_cifra": {"oficial", "propio", "modelada"},
}
ROLES_INSUMO = {"numerador", "denominador_principal", "contraste", "tabla_curada"}
# Ámbitos de Lima (L1–L8, 9/10/2026): nivel = ambito_id, con su rango en NIVEL_RANK. La asignación es de ambitos_lima.py.
AMBITOS_LIMA = (ambitos_lima.LIMA_METROPOLITANA, ambitos_lima.LIMA_REGION, ambitos_lima.CALLAO)
AMBITOS_TODOS = AMBITOS_LIMA + (ambitos_lima.AREA_METROPOLITANA_LIMA_CALLAO,)
NIVELES_EXTENSION: set[str] = set()  # «establecimiento» entró a NIVEL_RANK en P0 (10/10/2026)
ENCUESTA_DE_FUENTE = {"INEI-ENDES": "ENDES", "INEI-ENAHO": "ENAHO"}
# Tablas solo curadas, sin crudo en el catálogo: R-DEP-01 las evalúa por su manifiesto (D-AUD-1, P0 10/10/2026;
# reglas.json → R-DEP-01.parametros.tablas_solo_curadas)
TABLAS_SOLO_CURADAS = {"dim_dominio", "dim_tema_gasto"}

TABLAS_POR_ORIGEN = {  # tabla_origen → tabla registrada en un manifiesto de la capa 0
    "endes_nino.parquet": "endes_nino", "enaho_sumaria.parquet": "enaho_sumaria",
    "fact_mapa_pobreza.parquet": "fact_mapa_pobreza", "fact_sien_hb_ubigeo.parquet": "fact_sien_hb_ubigeo",
}
DEF_ENDES = {"endes_anemia_6_35m": "anemia_6_35m", "endes_anemia_6_35m_oms2024": "anemia_6_35m_oms2024",
             "endes_dci_menores_5": "dci_menores_5"}
VAR_ENAHO = {"enaho_pobreza_monetaria": "pobre", "enaho_pobreza_extrema": "pobre_extremo"}

COLUMNAS_DORADAS = [
    "id_cifra", "indicador_id", "fuente_id", "anio", "nivel", "territorio", "definicion_lima", "criterio",
    "valor_publicado", "ic_inf_publicado", "ic_sup_publicado", "cv_publicado", "casos_publicados", "decimales",
    "comparacion", "tolerancia_pp", "tolerancia_cv", "bloqueante", "proposito", "documento", "url", "cuadro_pagina",
    "fecha_publicacion", "tipo_cita", "verificado_por", "nota"]


# ======================================================================= utilidades

def _json(v):
    """Campos anidados del YAML se guardan como JSON (orden de claves estable) para que el Parquet sea determinista."""
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return v


def _vacio(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip()) or (isinstance(v, (list, dict)) and not v)


def _a_tabla(registros: list[dict], clave: str, renombre: str) -> pd.DataFrame:
    columnas = []
    for r in registros:
        columnas += [k for k in r if k not in columnas]
    filas = [{c: _json(r.get(c)) for c in columnas} for r in registros]
    df = pd.DataFrame(filas, columns=columnas).rename(columns={clave: renombre})
    for c in df.columns:  # tipos homogéneos: booleanos y enteros puros se conservan; el resto, texto
        s = df[c]
        if s.map(lambda x: isinstance(x, bool) or x is None).all() and s.notna().any():
            df[c] = s.astype("boolean")
        elif s.map(lambda x: (isinstance(x, int) and not isinstance(x, bool)) or x is None).all() and s.notna().any():
            df[c] = s.astype("Int64")
        else:
            df[c] = s.map(lambda x: None if x is None else str(x)).astype("string")
    df["version_tabla"] = VERSION_TABLA
    return df


def _catalogo(rutas: Rutas) -> dict[str, dict]:
    return {f["id"]: f for f in json.loads(rutas.catalogo.read_text(encoding="utf-8"))}


def _leer(ins: insumos.Insumo, columnas: str = "*", donde: str = "") -> pd.DataFrame:
    con = duckdb.connect()
    try:
        return con.execute(f"SELECT {columnas} FROM '{ins.ruta}' {donde}").df()
    finally:
        con.close()


# ======================================================================= dim_indicador

def _pruebas_indicadores(rutas: Rutas, inds: list[dict], res: Resultado, tablas: dict) -> None:
    ids = [i.get("id") for i in inds]
    res.prueba("IND-01", "dim_indicador: id único y en snake_case",
               len(ids) == len(set(ids)) and all(re.fullmatch(r"[a-z][a-z0-9_]*", str(i)) for i in ids),
               {"ids": ids})
    res.prueba("IND-02", "dim_indicador: estado válido (activo_piloto | piloto_ampliado)",
               all(i.get("estado_propuesta") in ESTADOS_INDICADOR for i in inds))

    faltan = {}
    for i in inds:
        req = OBLIGATORIOS + (OBLIGATORIOS_ENCUESTA if i.get("naturaleza_dato") == "encuesta_muestral" else [])
        if i.get("naturaleza_dato") == "estimacion_modelada":
            req = req + ["validado_contra_oficial"]
        f = [c for c in req if c not in i or (_vacio(i[c]) and not isinstance(i[c], bool))]
        if i.get("naturaleza_dato") == "encuesta_muestral":
            vd = i.get("variables_diseno") or {}
            f += [f"variables_diseno.{k}" for k in ("factor", "estrato", "conglomerado") if _vacio(vd.get(k))]
            if _vacio((i.get("dominios_inferencia") or {}).get("anual")):
                f.append("dominios_inferencia.anual")
        if f:
            faltan[i["id"]] = f
    res.prueba("IND-03", "dim_indicador: ningún campo obligatorio vacío (R-MOTOR-02 suprimiría la cifra); en las "
               "encuestas, variables_diseno.factor/estrato/conglomerado (R-ENC-01) y dominios_inferencia.anual (R-ENC-06)",
               not faltan, {"faltan": faltan})

    reglas = json.loads((rutas.raiz / "reglas" / "reglas.json").read_text(encoding="utf-8"))
    vh1 = reglas["parametros_globales"].get("VOCABULARIOS_INDICADOR", {})
    vocab = {**VOCAB, **{c: set(vh1.get(c) or []) for c in VOCAB_H1}}
    fuera = {}
    for i in inds:
        for campo, voc in vocab.items():
            if campo in i and i[campo] not in voc:
                fuera.setdefault(i["id"], {})[campo] = i[campo]
        if not isinstance(i.get("es_socioeconomico"), bool):
            fuera.setdefault(i["id"], {})["es_socioeconomico"] = i.get("es_socioeconomico")
        roles = {r.get("rol") for r in i.get("insumos") or []}
        if roles - ROLES_INSUMO:
            fuera.setdefault(i["id"], {})["insumos.rol"] = sorted(roles - ROLES_INSUMO)
    res.prueba("IND-04", "dim_indicador: valores dentro de los vocabularios controlados (reglas.json, con VOCABULARIOS_INDICADOR)",
               not fuera, {"fuera": fuera})

    # R-DEP-01: insumos del catálogo con compuerta «aprobada»; los de contraste solo avisan
    cat = _catalogo(rutas)
    malos, contraste, curadas = {}, {}, {}
    for i in inds:
        for r in i.get("insumos") or []:
            iid = r.get("id")
            if iid in TABLAS_SOLO_CURADAS:
                curadas.setdefault(i["id"], []).append(iid)
                continue
            comp = (cat.get(iid) or {}).get("compuerta_ingesta")
            if comp != "aprobada":
                (contraste if r.get("rol") == "contraste" else malos).setdefault(i["id"], []).append(f"{iid}={comp}")
    res.prueba("IND-05", "R-DEP-01: todo insumo (numerador, denominador o crudo de tabla curada) está en el catálogo "
               "con compuerta «aprobada»", not malos, {"no_aprobados": malos})
    res.prueba("IND-06", "R-DEP-01: insumos de contraste no aprobados (se omiten con nota; no hacen caer la cifra)",
               not contraste, {"contraste": contraste}, bloqueante=False)
    # D-AUD-1 (P0, 10/10/2026): la tabla solo curada pasa si está en su manifiesto sin pruebas bloqueantes fallidas
    p_dep = next(r for r in json.loads((rutas.raiz / "reglas" / "reglas.json").read_text(encoding="utf-8"))["reglas"]
                 if r["id"] == "R-DEP-01")["parametros"]
    sin_respaldo = {}
    for t, mf in p_dep["tablas_solo_curadas"].items():
        ruta = next((c / f"{mf}.json" for c in salida.carpetas_con_manifiesto(rutas) if (c / f"{mf}.json").exists()), None)
        man = json.loads(ruta.read_text(encoding="utf-8")) if ruta else {}
        if t not in man.get("tablas", {}) or man.get("pruebas", {}).get("bloqueantes_fallidas"):
            sin_respaldo[t] = mf
    res.prueba("IND-07", "R-DEP-01 (D-AUD-1): cada tabla solo curada que usa un indicador (dim_dominio, dim_tema_gasto) está en su "
               "manifiesto de la capa 0 sin pruebas bloqueantes fallidas",
               not (set(sin_respaldo) & {t for v in curadas.values() for t in v}),
               {"usadas": curadas, "sin_respaldo": sin_respaldo})

    # tabla de origen registrada en un manifiesto; definición o tema existente; años con datos
    defs = yaml.safe_load(insumos.curado(rutas, "definiciones_endes.yaml").ruta.read_text(encoding="utf-8"))["indicadores"]
    tema = _leer(tablas["dim_tema_gasto"], "DISTINCT tema_id, anio")
    problemas, anios_mal = {}, {}
    for i in inds:
        to = str(i.get("tabla_origen"))
        defi = i.get("definicion") or {}
        if i["id"] in DEF_ENDES:
            ref = str(defi.get("ref", ""))
            if not ref.endswith(f"indicadores.{DEF_ENDES[i['id']]}") or DEF_ENDES[i["id"]] not in defs:
                problemas[i["id"]] = f"definición {ref!r} no está en definiciones_endes.yaml"
            d = _leer(tablas["endes_nino"], "DISTINCT anio",
                      f"WHERE {defs[DEF_ENDES[i['id']]]['variable']} IS NOT NULL")
            reales = sorted(int(a) for a in d.anio)
        elif i["id"] in VAR_ENAHO:
            reales = sorted(int(a) for a in _leer(tablas["enaho_sumaria"], "DISTINCT anio").anio)
        elif "fact_sien_hb_ubigeo" in to:
            reales = sorted(int(a) for a in _leer(tablas["fact_sien_hb_ubigeo"], "DISTINCT anio").anio)
        elif "fact_mapa_pobreza" in to:
            reales = sorted(int(a) for a in _leer(tablas["fact_mapa_pobreza"], "DISTINCT edicion").edicion)
        elif str(i.get("tema_id", "")).startswith(("cpt_", "pp_", "fun_", "div_", "ppxfun_", "ps_")):
            t = tema[tema.tema_id == i["tema_id"]]
            if t.empty:
                problemas[i["id"]] = f"tema_id {i['tema_id']} no está en dim_tema_gasto"
            if i["tema_id"] not in str(defi.get("consulta", "")):
                problemas[i["id"]] = "la consulta no usa gasto_tema('<tema_id>') con su propio tema_id"
            reales = sorted(int(a) for a in t.anio.unique())
        else:
            problemas[i["id"]] = f"tabla de origen sin comprobación: {to}"
            continue
        if not any(k in to for k in TABLAS_POR_ORIGEN) and "v_gasto_tematico" not in to:
            problemas[i["id"]] = f"tabla de origen desconocida: {to}"
        if sorted(int(a) for a in i.get("anios_disponibles") or []) != reales:
            anios_mal[i["id"]] = {"declarados": i.get("anios_disponibles"), "en_datos": reales}
    res.prueba("IND-08", "dim_indicador: la definición (definiciones_endes.yaml) o el tema (dim_tema_gasto) existen y la "
               "tabla de origen está registrada en un manifiesto de la capa 0", not problemas, {"problemas": problemas})
    res.prueba("IND-09", "dim_indicador: anios_disponibles = años con dato en la tabla de origen", not anios_mal,
               {"distintos": anios_mal})
    enc = [i for i in inds if i.get("naturaleza_dato") == "encuesta_muestral"]
    res.prueba("IND-10", "Encuestas: validado_contra_oficial = false hasta que el motor pase las cifras doradas (R-ENC-18)",
               all(i.get("validado_contra_oficial") is False for i in enc))
    gasto = [i for i in inds if i.get("naturaleza_dato") == "presupuestal_financiero"]
    # la frase solo puede aparecer dentro de la propia prohibición («Nunca «gasto del PAN»…»)
    prohibido = [i["id"] for i in gasto if re.search(r"gasto del PAN", re.sub(r"Nunca «gasto del PAN»", "",
                                                                             json.dumps(i, ensure_ascii=False)), re.I)]
    res.prueba("IND-11", "Gasto: ningún texto dice «gasto del PAN» (decisión del 7/10/2026: el PAN termina en 2022)",
               not prohibido, {"con_texto": prohibido})
    _pruebas_ambitos(rutas, inds, res)


def _sql_poblacion(spec: dict, prefijos: list[str]) -> str:
    """SQL (duckdb) del denominador declarado en dim_indicador: filtros de la especificación + prefijos de ubigeo
    ('-x' excluye). Devuelve (anio, valor) sumando por año en una sola geografía."""
    f = spec["filtro"]
    cond = [f"fuente_id = '{spec['fuente_id']}'"]
    for k, v in f.items():
        cond.append(f"{k} = 'vigente_' || anio" if v == "vigente_{anio}" else f"{k} = '{v}'")
    inc = [p for p in prefijos if not p.startswith("-")]
    cond.append("(" + " OR ".join(f"ubigeo_inei LIKE '{p}%'" for p in inc) + ")")
    cond += [f"ubigeo_inei NOT LIKE '{p[1:]}%'" for p in prefijos if p.startswith("-")]
    return "SELECT anio, sum(valor) AS valor FROM {tabla} WHERE " + " AND ".join(cond) + " GROUP BY anio"


def _prueba_denominador_ipf(inds: list[dict], tabla: insumos.Insumo, res: Resultado) -> None:
    """H3: el denominador propio de L7 se ejecuta tal como está declarado y debe cuadrar con la cifra oficial."""
    malos, detalle = {}, {}
    con = duckdb.connect()
    try:
        con.execute(f"CREATE VIEW t AS SELECT * FROM '{tabla.ruta}'")
        for i in inds:
            den = i.get("denominador_ambitos_lima")
            if den is None:
                continue
            pr, of, ctl = den["propio"], den["oficial"], den["control"]
            q = lambda spec, pref: con.execute(_sql_poblacion(spec, pref).format(tabla="t")).df().set_index("anio").valor
            suma = sum(q(pr, pr["prefijos"][a]) for a in ctl["suma"])
            ofi15 = q(of, [ctl["igual_a_oficial_prefijo"]])
            anios = _anios(pr["anios"])
            dif = (suma.reindex(anios) - ofi15.reindex(anios)).abs()
            if dif.isna().any() or (dif > ctl["tolerancia"]).any():
                malos[i["id"]] = {"LM+LR vs dpto 15": {int(a): (None if pd.isna(x) else round(float(x), 3)) for a, x in dif.items()}}
            if ctl.get("callao_propio_igual_a_oficial"):
                dc = (q(pr, of["prefijos"]["CALLAO"]).reindex(anios) - q(of, of["prefijos"]["CALLAO"]).reindex(anios)).abs()
                if dc.isna().any() or (dc > ctl["tolerancia"]).any():
                    malos.setdefault(i["id"], {})["Callao IPF vs oficial"] = dc.round(3).to_dict()
            detalle[i["id"]] = {"max_dif_15": round(float(dif.max()), 4), "anios": [min(anios), max(anios)]}
    finally:
        con.close()
    res.prueba("IND-14", "L7: el denominador propio (IPF) declarado en dim_indicador, ejecutado tal cual, cuadra: LM + LR = "
               "departamento 15 oficial y el Callao del IPF = oficial del 07 (H3)", not malos, {"malos": malos, **detalle})


def _anios(v) -> list[int]:
    """'2015-2025' | 2024 | [2024, 2025] → lista de años."""
    if v is None:
        return []
    if isinstance(v, list):
        return [int(a) for a in v]
    s = str(v)
    if "-" in s:
        a, b = s.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(s)]


def _dominio_confirmado(rutas: Rutas, encuesta: str, dominio_id: str, anio: int) -> bool:
    """confirmado de la regla de dominios.yaml (fuente de dim_dominio) que cubre (encuesta, dominio_id, año)."""
    dom = yaml.safe_load(insumos.curado(rutas, "dominios.yaml").ruta.read_text(encoding="utf-8"))
    for r in dom["reglas"]:
        a0, a1 = r["anios"]
        if r["encuesta"] == encuesta and r["dominio_id"] == dominio_id and a0 <= anio <= a1:
            return r.get("confirmado") is True
    return False


def _pruebas_ambitos(rutas: Rutas, inds: list[dict], res: Resultado) -> None:
    """Lima en tres ámbitos: vocabulario de niveles (NIVEL_RANK), rango y rótulo de los ámbitos, ranking de 26 unidades (L8)
    y años condicionados a dim_dominio (ENDES 2025)."""
    reglas = json.loads((rutas.raiz / "reglas" / "reglas.json").read_text(encoding="utf-8"))
    rank = reglas["parametros_globales"]["NIVEL_RANK"]
    p = {r["id"]: r for r in reglas["reglas"]}
    rotulos = p["R-ENC-07"]["parametros"]["dominios_lima"]["rotulos"]
    u12 = p["R-ENC-12"]["parametros"]["unidades_ranking_departamental"]
    claves_aviso = set(p["R-ENC-08"]["parametros"]["avisos"])
    malos = {}
    for i in inds:
        for nv in i.get("niveles_validos") or []:
            n = nv.get("nivel")
            if i.get("naturaleza_dato") == "encuesta_muestral" and set(nv.get("avisos") or []) - claves_aviso:
                malos.setdefault(i["id"], []).append(f"{n}: avisos fuera de R-ENC-08.avisos "
                                                     f"{sorted(set(nv['avisos']) - claves_aviso)}")
            if n not in rank and n not in NIVELES_EXTENSION:
                malos.setdefault(i["id"], []).append(f"nivel {n!r} fuera de NIVEL_RANK")
            if set(nv.get("dominios") or []) & set(AMBITOS_TODOS):
                malos.setdefault(i["id"], []).append("ámbito de Lima como dominio de dominio_subnacional (nivel = ambito_id)")
            if n in AMBITOS_TODOS:
                if nv.get("rango") != rank[n]:
                    malos.setdefault(i["id"], []).append(f"{n}: rango {nv.get('rango')} ≠ NIVEL_RANK {rank[n]}")
                if nv.get("rotulo") != rotulos[n]:
                    malos.setdefault(i["id"], []).append(f"{n}: rótulo distinto de R-ENC-07")
                if i.get("naturaleza_dato") == "encuesta_muestral" and "mascara_ambito" not in str(nv.get("asignacion")):
                    malos.setdefault(i["id"], []).append(f"{n}: asignación fuera de ambitos_lima.mascara_ambito")
        rk = i.get("ranking")
        if rk is not None and (rk.get("unidades") != u12["unidades"] or rk.get("total") != u12["total"]):
            malos.setdefault(i["id"], []).append("ranking distinto de R-ENC-12.unidades_ranking_departamental (26)")
    res.prueba("IND-12", "dim_indicador: niveles en NIVEL_RANK (incluye «establecimiento» desde P0); ámbitos de Lima con nivel = ambito_id, "
               "su rango y su rótulo; asignación con ambitos_lima; ranking = 26 unidades de R-ENC-12 (L8)",
               not malos, {"malos": malos})
    cond = {}
    for i in inds:
        enc = ENCUESTA_DE_FUENTE.get(i.get("fuente_principal"))
        if i.get("naturaleza_dato") != "encuesta_muestral":
            continue
        for nv in i.get("niveles_validos") or []:
            if nv.get("nivel") not in AMBITOS_TODOS:
                continue
            if not enc or _vacio(nv.get("dominio_id")):
                cond.setdefault(i["id"], []).append(f"{nv['nivel']}: sin encuesta o sin dominio_id")
                continue
            for a in _anios(nv.get("anios")) or [int(x) for x in i.get("anios_disponibles") or []]:
                if not _dominio_confirmado(rutas, enc, nv["dominio_id"], a):
                    cond.setdefault(i["id"], []).append(f"{nv['nivel']} {a}: dim_dominio sin confirmar")
    res.prueba("IND-13", "dim_indicador: TODOS los años de cada nivel de Lima de una encuesta tienen en dominios.yaml (dim_dominio) "
               "una regla confirmada, con o sin marca anios_condicionados (H2)", not cond, {"sin_confirmar": cond})


# ======================================================================= cruces_permitidos

def _pruebas_cruces(rutas: Rutas, cru: dict, inds: dict[str, dict], res: Resultado) -> None:
    reglas = json.loads((rutas.raiz / "reglas" / "reglas.json").read_text(encoding="utf-8"))
    p = {r["id"]: r for r in reglas["reglas"]}
    par03 = p["R-CRUCES-03"]["parametros"]
    ventana = {"rapida": par03["ventana_rapida_anios"], "lenta": par03["ventana_lenta_anios"]}
    campos = [k.split(" ")[0] for k in p["R-CRUCES-11"]["parametros"]["campos_tabla"]]
    aprobacion = ["aprobado_por", "fecha_aprobacion"]
    cs = cru["cruces"]
    ids = [c["id_cruce"] for c in cs]
    activos = [c for c in cs if c.get("estado_propuesta") == "activo_piloto"]
    res.prueba("CRU-01", "cruces_permitidos: id único, estado válido y a lo sumo max_cruces_mvp activos (R-CRUCES-11)",
               len(ids) == len(set(ids)) and all(c.get("estado_propuesta") in ESTADOS_CRUCE for c in cs)
               and len(activos) <= p["R-CRUCES-11"]["parametros"]["max_cruces_mvp"], {"activos": len(activos)})
    faltan = {c["id_cruce"]: [k for k in campos if k not in aprobacion and k not in c
                              or (k not in aprobacion and _vacio(c.get(k)) and not isinstance(c.get(k), (int, bool)))]
              for c in cs}
    faltan = {k: v for k, v in faltan.items() if v}
    res.prueba("CRU-02", "cruces_permitidos: trae los campos de R-CRUCES-11.campos_tabla", not faltan, {"faltan": faltan})
    sin_visto = [c["id_cruce"] for c in activos if _vacio(c.get("aprobado_por")) or _vacio(c.get("fecha_aprobacion"))]
    res.prueba("CRU-04", "cruces_permitidos: los cruces activos tienen el visto del dueño (aprobado_por, fecha_aprobacion)",
               not sin_visto, {"sin_visto": sin_visto}, bloqueante=False)
    presentaciones = {c.get("presentacion") for c in cs}
    res.prueba("CRU-05", "cruces_permitidos: presentación válida (lado_a_lado | asociacion | cociente)",
               presentaciones <= {"lado_a_lado", "asociacion", "cociente"}, {"presentaciones": sorted(map(str, presentaciones))})
    malos = {}
    for c in cs:
        a, b = inds.get(c["indicador_a"]), inds.get(c["indicador_b"])
        if a is None or b is None:
            malos[c["id_cruce"]] = "indicador inexistente en dim_indicador"
            continue
        if a["concepto_medido"] == b["concepto_medido"]:
            malos[c["id_cruce"]] = "miden el mismo concepto: es R-CRUCES-08, no un cruce"
        v = min(ventana[a["velocidad_cambio"]], ventana[b["velocidad_cambio"]])
        if int(c["ventana_anios"]) > v or int(c["rezago_anios"]) > par03["rezago_declarado_max_anios"]:
            malos[c["id_cruce"]] = f"ventana {c['ventana_anios']} > {v} o rezago fuera de R-CRUCES-03"
        comunes = set(c.get("anios_comunes") or [])
        disp = set(a["anios_disponibles"]) & set(b["anios_disponibles"])
        if not comunes or not comunes <= disp:
            malos[c["id_cruce"]] = f"anios_comunes {sorted(comunes)} fuera de los años de ambos ({sorted(disp)})"
    res.prueba("CRU-03", "cruces_permitidos: indicadores existentes, conceptos distintos, ventana y rezago dentro de "
               "R-CRUCES-03 y años comunes con dato en ambos", not malos, {"malos": malos})
    _prueba_subdivision_lima(rutas, cs, inds, res, reglas)


def _valores_ambito_gasto(rutas: Rutas) -> set[str]:
    """Valores que produce la macro ambito_gasto() de vistas_gasto.sql (única definición del reparto del gasto, P3)."""
    sql = insumos.curado(rutas, "vistas_gasto.sql").ruta.read_text(encoding="utf-8")
    m = re.search(r"MACRO ambito_gasto\(.*?END;", sql, re.S)
    return set(re.findall(r"THEN '([A-Z_]+)'", m.group(0))) if m else set()


def _prueba_subdivision_lima(rutas: Rutas, cs: list[dict], inds: dict[str, dict], res: Resultado, reglas: dict) -> None:
    """L5: CR-01 (y CR-02) con nivel_minimo departamento para los otros 24 y la subdivisión del 15 (LM, LR) y el Callao con su
    mapeo explícito resultado ↔ gasto (ambito_lima ↔ ambito_gasto). 2025 de LM y LR, solo con dim_dominio ENDES confirmado."""
    rank = reglas["parametros_globales"]["NIVEL_RANK"]
    vals_gasto = _valores_ambito_gasto(rutas)
    malos = {}
    for c in cs:
        s = c.get("subdivision_lima")
        if c["id_cruce"] == "CR-01" and s is None:
            malos["CR-01"] = ["sin subdivision_lima (L5)"]
        if s is None:
            continue
        m = malos.setdefault(c["id_cruce"], [])
        if c.get("nivel_minimo") != "departamento":
            m.append("nivel_minimo de los otros 24 debe seguir en departamento")
        amb = {a.get("ambito_id"): a for a in s.get("ambitos") or []}
        if set(amb) != set(AMBITOS_LIMA):
            m.append(f"ámbitos {sorted(map(str, amb))} ≠ LM, LR, Callao")
        a_ind, b_ind = inds.get(c["indicador_a"], {}), inds.get(c["indicador_b"], {})
        cond = {a: x for x in s.get("anios_condicionados") or [] for a in x.get("ambitos") or []}
        for aid, a in amb.items():
            r, g = a.get("resultado") or {}, a.get("gasto") or {}
            if aid not in rank or a.get("nivel") != aid:
                m.append(f"{aid}: nivel ≠ ambito_id o fuera de NIVEL_RANK")
            if g.get("campo") != "ambito_gasto" or g.get("valor") != aid or aid not in vals_gasto:
                m.append(f"{aid}: gasto sin mapeo ambito_gasto = '{aid}' (macro ambito_gasto)")
            if _vacio(r.get("campo")) or r.get("valor") != aid:
                m.append(f"{aid}: resultado sin mapeo al mismo ámbito")
            enc = [x for x in (a_ind, b_ind) if x.get("naturaleza_dato") == "encuesta_muestral"]
            if enc and r.get("campo") != "ambito_lima":
                m.append(f"{aid}: en la ENDES el mapeo es la columna/función ambito_lima")
            for ind in (a_ind, b_ind):
                if aid not in {nv.get("nivel") for nv in ind.get("niveles_validos") or []}:
                    m.append(f"{aid}: no es nivel válido de {ind.get('id')}")
            anios = _anios(a.get("anios"))
            if not anios or not set(anios) <= set(c.get("anios_comunes") or []):
                m.append(f"{aid}: años {anios} fuera de anios_comunes")
            for an in anios:
                for ind in enc:
                    nv = next((n for n in ind.get("niveles_validos") or [] if n.get("nivel") == aid), {})
                    if not _dominio_confirmado(rutas, ENCUESTA_DE_FUENTE[ind["fuente_principal"]], nv.get("dominio_id"), an):
                        m.append(f"{aid} {an}: dim_dominio de {ind['id']} sin confirmar")
                x = cond.get(aid)
                if x and int(x["anio"]) == an:
                    ok = x.get("activo") is True and all(
                        _dominio_confirmado(rutas, ENCUESTA_DE_FUENTE[i["fuente_principal"]], d, an)
                        for i in enc for d in ({ambitos_lima.LIMA_METROPOLITANA: "lima_metropolitana",
                                                ambitos_lima.LIMA_REGION: "lima_provincias"}.get(aid),) if d)
                    if not ok:
                        m.append(f"{aid} {an}: año condicionado sin activar o sin dim_dominio confirmado")
        if not m:
            del malos[c["id_cruce"]]
    res.prueba("CRU-06", "cruces_permitidos (L5): nivel_minimo departamento y subdivisión LM, LR y Callao con mapeo completo "
               "resultado ↔ gasto (ambito_lima ↔ ambito_gasto), niveles válidos en ambos indicadores y años condicionados "
               "solo con dim_dominio confirmado", not malos, {"malos": malos})


# ======================================================================= cifras_doradas

def _dominio_endes(d: pd.DataFrame, nivel: str, terr: str) -> pd.Series:
    if nivel == "nacional":
        return pd.Series(True, index=d.index)
    if nivel == "departamento":
        return d.departamento == terr
    if terr in ("urbano", "rural"):
        return d.area == terr
    if terr in AMBITOS_TODOS:  # nivel = ambito_id; ubigeo desde 2018, estrato en 2015–2017 (L2): solo ambitos_lima
        return ambitos_lima.mascara_ambito(d, "ENDES", terr)
    raise ValueError(f"territorio ENDES no soportado: {nivel}/{terr}")


def _dominio_enaho(d: pd.DataFrame, nivel: str, terr: str) -> pd.Series:
    if nivel == "nacional":
        return pd.Series(True, index=d.index)
    if nivel == "departamento":
        return d.departamento == terr
    if terr in ("urbano", "rural"):
        return d.area == terr
    if terr in AMBITOS_TODOS:  # LM, LR, Callao (ámbitos publicados, L1) y dominio 8: solo ambitos_lima
        return ambitos_lima.mascara_ambito(d, "ENAHO", terr)
    if terr == "resto_urbano":
        return (d.area == "urbano") & ~ambitos_lima.dominio8_enaho(d)
    raise ValueError(f"territorio ENAHO no soportado: {nivel}/{terr}")


DISENO = {"ENDES": ("id_estrato", "id_conglomerado"), "ENAHO": ("id_estrato_diseno", "id_conglomerado")}
# IC publicado ≈ valor ± 1,96·CV·valor (Wald, como el INEI): holgura por redondeo a 1 decimal de IC y CV (D-ENA-1, H1)
HOLGURA_IC_PP, HOLGURA_IC_REL, Z95 = 0.15, 0.001, 1.96
AVISO_CV_PUNTOS = 0.5  # D-ENA-1 (orquestador, 9/10/2026): aviso si nuestro CV difiere > 0,5 puntos del publicado


def _cv_taylor(d: pd.DataFrame, dominio: pd.Series, var: str, peso: str, estrato: str, conglomerado: str) -> float:
    """CV (%) de una proporción por dominio con linealización de Taylor (z = 0 fuera del dominio; conglomerados con
    reemplazo dentro del estrato; estratos con un solo conglomerado no aportan). Estimador puntual de varianza para
    controlar el CV transcrito; la inferencia de publicación es del motor (svy)."""
    y = d[var].astype(float).fillna(0).to_numpy()
    w = d[peso].astype(float).to_numpy()
    m = dominio.fillna(False).to_numpy(bool)
    n = (w * m).sum()
    p = (w * m * y).sum() / n
    z = w * m * (y - p) / n
    g = pd.DataFrame({"h": d[estrato].to_numpy(), "c": d[conglomerado].to_numpy(), "z": z}).groupby(["h", "c"]).z.sum()
    g = g.reset_index()
    nh = g.groupby("h").z.transform("size")
    v = ((nh / (nh - 1)) * (g.z - g.groupby("h").z.transform("mean")) ** 2)[nh > 1].sum()
    return float(100 * np.sqrt(v) / p)


def _reproducir(rutas: Rutas, dor: pd.DataFrame, tablas: dict) -> pd.DataFrame:
    defs = yaml.safe_load(insumos.curado(rutas, "definiciones_endes.yaml").ruta.read_text(encoding="utf-8"))["indicadores"]
    endes = _leer(tablas["endes_nino"])
    enaho = _leer(tablas["enaho_sumaria"])
    mapa = _leer(tablas["fact_mapa_pobreza"])
    filas = []
    for c in dor.itertuples():
        base = {"id_cifra": c.id_cifra, "indicador_id": c.indicador_id, "anio": c.anio, "nivel": c.nivel,
                "territorio": c.territorio, "proposito": c.proposito, "bloqueante": c.bloqueante,
                "tipo_cita": c.tipo_cita, "valor_publicado": c.valor_publicado}
        if c.indicador_id == "mapa_pobreza_2018":
            m = mapa[(mapa.ubigeo_inei == c.territorio) & (mapa.nivel == c.nivel)]
            lo, hi = (round(float(m.pobreza_ic_inf.iloc[0]), 1), round(float(m.pobreza_ic_sup.iloc[0]), 1)) \
                if len(m) == 1 else (None, None)
            filas.append({**base, "estimacion": None, "ic_inf_nuestro": lo, "ic_sup_nuestro": hi,
                          "pasa": lo == c.ic_inf_publicado and hi == c.ic_sup_publicado})
            continue
        if c.indicador_id in DEF_ENDES:
            defi = defs[DEF_ENDES[c.indicador_id]]
            d = endes[endes.anio == c.anio]
            var, peso = defi["variable"], "peso"
            if d[var].isna().all():
                filas.append({**base, "estimacion": None, "pasa": None, "nota": "variable inexistente ese año"})
                continue
            dom = _en_universo(d, int(c.anio), defi) & _dominio_endes(d, c.nivel, c.territorio).fillna(False)
            s, enc = d[dom], "ENDES"
        elif c.indicador_id in VAR_ENAHO:
            d = enaho[enaho.anio == c.anio]
            var, peso = VAR_ENAHO[c.indicador_id], "peso_persona"
            dom = _dominio_enaho(d, c.nivel, c.territorio).fillna(False)
            s, enc = d[dom], "ENAHO"
        else:
            filas.append({**base, "estimacion": None, "pasa": None, "nota": "indicador sin reproducción"})
            continue
        if s.empty or (c.indicador_id in VAR_ENAHO and int(c.anio) not in set(enaho.anio)):
            filas.append({**base, "estimacion": None, "pasa": None, "nota": "sin datos ese año"})
            continue
        est = float(100 * np.average(s[var].astype(float), weights=s[peso]))
        dif = round(round(est, int(c.decimales)) - float(c.valor_publicado), 2)
        casos = None if pd.isna(c.casos_publicados) else int(c.casos_publicados)
        cv = round(_cv_taylor(d, dom, var, peso, *DISENO[enc]), 3) if pd.notna(c.cv_publicado) else None
        filas.append({**base, "estimacion": round(est, 3), "diferencia_pp": dif, "n": len(s),
                      "casos_publicados": casos, "cv_publicado": c.cv_publicado, "cv_nuestro": cv,
                      "pasa": abs(dif) <= float(c.tolerancia_pp) + 1e-9 and (casos is None or casos == len(s))})
    return pd.DataFrame(filas)


def _pruebas_doradas(rutas: Rutas, dor: pd.DataFrame, inds: dict[str, dict], res: Resultado, tablas: dict) -> pd.DataFrame:
    reglas = json.loads((rutas.raiz / "reglas" / "reglas.json").read_text(encoding="utf-8"))
    r18 = next(r for r in reglas["reglas"] if r["id"] == "R-ENC-18")["parametros"]
    rank = reglas["parametros_globales"]["NIVEL_RANK"]
    res.prueba("DOR-01", "cifras_doradas: columnas esperadas, id_cifra único", list(dor.columns) == COLUMNAS_DORADAS
               and dor.id_cifra.is_unique, {"columnas": list(dor.columns)})
    blo = dor[dor.bloqueante]
    llave = ["indicador_id", "anio", "nivel", "territorio", "criterio"]
    dup = blo[blo.duplicated(llave, keep=False)]
    res.prueba("DOR-02", "cifras_doradas: sin llaves (indicador, año, nivel, territorio, criterio) repetidas entre "
               "bloqueantes", dup.empty, {"repetidas": dup.id_cifra.tolist()})
    malos = dor[~dor.indicador_id.isin(list(inds)) & (dor.indicador_id != "enaho_pobreza_extrema")]
    crit = dor[dor.indicador_id.isin(list(inds))]
    crit = crit[crit.apply(lambda c: c.criterio != inds[c.indicador_id]["criterio_medicion"], axis=1)]
    res.prueba("DOR-03", "cifras_doradas: indicador_id y criterio casan con dim_indicador (pobreza extrema = control)",
               malos.empty and crit.empty, {"sin_indicador": malos.id_cifra.tolist(), "criterio": crit.id_cifra.tolist()})
    amb = dor[dor.territorio.isin(AMBITOS_TODOS) | dor.nivel.isin(AMBITOS_TODOS)]
    res.prueba("DOR-04", "cifras_doradas: nivel dentro de NIVEL_RANK (ámbitos de Lima: nivel = territorio = ambito_id); "
               "propósito válido y cita solo de documentos oficiales (INEI; INS para el SIEN, 12/10/2026)",
               dor.nivel.isin(list(rank)).all() and dor.proposito.isin(["R-ENC-18", "control", "control_ingesta", "control_registro"]).all()
               and dor.tipo_cita.isin(["oficial_inei", "oficial_ins"]).all() and (amb.nivel == amb.territorio).all(),
               {"nivel_fuera": dor[~dor.nivel.isin(list(rank))].id_cifra.tolist(),
                "ambito_mal_nivel": amb[amb.nivel != amb.territorio].id_cifra.tolist()})
    nucleo = dor[dor.proposito == "R-ENC-18"]
    res.prueba("DOR-05", "R-ENC-18: el núcleo es bloqueante, solo con cita oficial del INEI y con la tolerancia de la "
               f"regla ({r18['tolerancia_pp']} pp)", nucleo.bloqueante.all() and (nucleo.tipo_cita == "oficial_inei").all()
               and (nucleo.tolerancia_pp == float(r18["tolerancia_pp"])).all()
               and not (dor.bloqueante & (dor.tipo_cita == "prensa")).any())
    cobertura, huecos = {}, {}
    for iid, i in inds.items():
        if i.get("naturaleza_dato") != "encuesta_muestral":
            continue
        n = nucleo[nucleo.indicador_id == iid]
        nac, dptos = int((n.nivel == "nacional").sum()), sorted(n[n.nivel == "departamento"].territorio.unique())
        cobertura[iid] = {"nacional": nac, "departamentos": dptos}
        if nac < 1 or len(dptos) < int(r18["departamentos_validacion_min"]):
            huecos[iid] = cobertura[iid]
    res.prueba("DOR-06", f"R-ENC-18: cada indicador de encuesta tiene en el núcleo la cifra nacional y ≥ "
               f"{r18['departamentos_validacion_min']} departamentos (un ámbito como Lima Metropolitana no cuenta)",
               not huecos, {"cobertura": cobertura, "huecos": huecos})
    faltan_amb = {}
    for iid, i in inds.items():
        if i.get("naturaleza_dato") != "encuesta_muestral":
            continue
        validos = {nv.get("nivel") for nv in i.get("niveles_validos") or []} & set(AMBITOS_LIMA)
        f = sorted(a for a in validos if not ((dor.indicador_id == iid) & dor.bloqueante & (dor.nivel == a)).any())
        if f:
            faltan_amb[iid] = f
    res.prueba("DOR-10", "Lima en tres ámbitos: cada indicador de encuesta con LM, LR o Callao válidos tiene al menos una cifra "
               "dorada bloqueante por ámbito en algún año (aviso)", not faltan_amb, {"sin_dorada": faltan_amb}, bloqueante=False)
    rep = _reproducir(rutas, dor, tablas)
    m = rep.merge(dor[["id_cifra"]], on="id_cifra")
    def fallan(df):
        return df[df.pasa != True][["id_cifra", "estimacion", "valor_publicado"]].to_dict("records")  # noqa: E712
    res.prueba("DOR-07", "R-ENC-18: nuestros datos estandarizados reproducen todas las cifras del núcleo (cifra puntual "
               "redondeada ± tolerancia y casos exactos donde el INEI los publica)",
               (m[m.proposito == "R-ENC-18"].pasa == True).all(), {"fallan": fallan(m[m.proposito == "R-ENC-18"])})  # noqa: E712
    res.prueba("DOR-08", "Mapa de Pobreza 2018: el intervalo de la tabla es el publicado (control de ingesta, a 1 decimal)",
               (m[m.proposito == "control_ingesta"].pasa == True).all(), {"fallan": fallan(m[m.proposito == "control_ingesta"])})  # noqa: E712
    _pruebas_ic_cv(dor, rep, res)
    ctrl = m[(m.proposito == "control") & m.pasa.notna()]
    res.prueba("DOR-09", "Cifras de control (no bloqueantes): las calculables se reproducen", (ctrl.pasa == True).all(),  # noqa: E712
               {"comparadas": len(ctrl), "fallan": fallan(ctrl),
                "no_calculables": m[m.pasa.isna()].id_cifra.tolist()}, bloqueante=False)
    return rep


def _pruebas_ic_cv(dor: pd.DataFrame, rep: pd.DataFrame, res: Resultado) -> None:
    """H1 de la auditoría P2–P4: un IC o un CV mal copiado tiene que hacer fallar algo."""
    x = dor[dor.ic_inf_publicado.notna() & dor.valor_publicado.notna()].copy()
    v, lo, hi = (x[c].astype(float) for c in ("valor_publicado", "ic_inf_publicado", "ic_sup_publicado"))
    malos = x[(lo > v) | (v > hi) | (((hi - v) - (v - lo)).abs() > HOLGURA_IC_PP)].id_cifra.tolist()
    y = x[x.cv_publicado.notna()]
    v, lo, hi, cv = (y[c].astype(float) for c in ("valor_publicado", "ic_inf_publicado", "ic_sup_publicado", "cv_publicado"))
    malos += y[((hi - lo) / 2 - Z95 * cv / 100 * v).abs() > HOLGURA_IC_PP + HOLGURA_IC_REL * v].id_cifra.tolist()
    t = rep.merge(dor[["id_cifra", "tolerancia_cv"]], on="id_cifra")
    t = t[t.tolerancia_cv.notna() & t.cv_publicado.notna()] if "cv_nuestro" in t else t.iloc[0:0]
    malos_cv = t[(t.cv_nuestro.astype(float).round(1) - t.cv_publicado.astype(float)).abs()
                 > t.tolerancia_cv.astype(float) + 1e-9][["id_cifra", "cv_publicado", "cv_nuestro"]].to_dict("records")
    res.prueba("DOR-11", "cifras_doradas: IC publicado coherente (ic_inf ≤ valor ≤ ic_sup, simétrico, semiancho ≈ 1,96·CV·valor "
               "con la holgura del redondeo) y, donde hay tolerancia_cv, nuestro CV (Taylor) igual al publicado",
               not malos and not malos_cv, {"ic_incoherente": malos, "cv_fuera_de_tolerancia": malos_cv})
    e = rep[rep.indicador_id.isin(list(VAR_ENAHO)) & rep.get("cv_nuestro", pd.Series(dtype=float)).notna()] \
        if "cv_nuestro" in rep else rep.iloc[0:0]
    lejos = e[(e.cv_nuestro.astype(float) - e.cv_publicado.astype(float)).abs() > AVISO_CV_PUNTOS]
    res.prueba("DOR-12", f"ENAHO (D-ENA-1): el CV publicado es dato y no bloquea; aviso si nuestro CV difiere > "
               f"{AVISO_CV_PUNTOS} puntos", lejos.empty,
               {"comparadas": len(e), "max_dif": round(float((e.cv_nuestro - e.cv_publicado).abs().max()), 3) if len(e) else None,
                "lejos": lejos[["id_cifra", "cv_publicado", "cv_nuestro"]].to_dict("records")}, bloqueante=False)


# ======================================================================= construcción

def construir(rutas: Rutas) -> Resultado:
    res = Resultado()
    i_ind = insumos.curado(rutas, "dim_indicador.yaml")
    i_cru = insumos.curado(rutas, "cruces_permitidos.yaml")
    i_dor = insumos.curado(rutas, "cifras_doradas.csv")
    tablas = {n: insumos.tabla(rutas, n) for n in ("endes_nino", "enaho_sumaria", "fact_mapa_pobreza",
                                                  "fact_sien_hb_ubigeo", "dim_tema_gasto", "fact_poblacion_grupo")}
    res.insumos += [i_ind, i_cru, i_dor, insumos.curado(rutas, "definiciones_endes.yaml"),
                    insumos.curado(rutas, "dominios.yaml"), insumos.curado(rutas, "vistas_gasto.sql"), *tablas.values()]

    ind = yaml.safe_load(i_ind.ruta.read_text(encoding="utf-8"))
    cru = yaml.safe_load(i_cru.ruta.read_text(encoding="utf-8"))
    dor = pd.read_csv(i_dor.ruta, dtype={"territorio": str, "id_cifra": str}, keep_default_na=True)
    dor["bloqueante"] = dor.bloqueante.astype(bool)
    dor["anio"] = dor.anio.astype(int)

    inds = ind["indicadores"]
    _pruebas_indicadores(rutas, inds, res, tablas)
    _prueba_denominador_ipf(inds, tablas["fact_poblacion_grupo"], res)
    por_id = {i["id"]: i for i in inds}
    _pruebas_cruces(rutas, cru, por_id, res)
    rep = _pruebas_doradas(rutas, dor, por_id, res, tablas)

    res.tablas["dim_indicador"] = _a_tabla(inds, "id", "indicador_id")
    res.tablas["cruces_permitidos"] = _a_tabla(cru["cruces"], "id_cruce", "id_cruce")
    t = dor.copy()
    t["casos_publicados"] = t.casos_publicados.astype("Int64")
    t["decimales"] = t.decimales.astype("Int64")
    for c in ("nota", "ic_inf_publicado", "ic_sup_publicado", "cv_publicado", "tolerancia_cv"):
        if t[c].dtype == object:
            t[c] = t[c].astype("string")
    t["version_tabla"] = VERSION_TABLA
    res.tablas["cifras_doradas"] = t
    res.revision["cifras_doradas_reproduccion"] = rep
    return res
