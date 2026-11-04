"""P1 — cubo de indicadores del piloto: biblioteca/indicadores/fact_indicador.parquet (`pap calcular`).

Una fila por indicador × año × nivel × territorio × medida × línea (contrato en
docs/especificaciones/motor.md §3). El cubo calcula TODOS los niveles válidos de dim_indicador;
qué se publica lo decide el validador (P2). Estimadores:
- ENDES y ENAHO: svy (Taylor; singleton «center» = R lonely.psu «adjust»; estimación por subpoblación con `where`,
  conservando todos los conglomerados del año); IC Korn-Graubard (variante NCHS), CV, gl, casos y n efectivo.
- SIEN: suma de numeradores y denominadores por nivel; IC de Wilson (R-REG-03). Cobertura de tamizaje: dos cotas
  (R-REG-07 v3, L7) con la proyección departamental (D-IND-7) o el prorrateo propio en LM y LR.
- Gasto: gasto_tema('<tema_id>') con la guardia; LM, LR y Callao por ambito_gasto; líneas aparte del 15 y el 07.
- Mapa de Pobreza 2018: intervalo y grupos robustos publicados, sin cifra puntual.
Las cifras doradas bloqueantes (R-ENC-18) y los controles del gasto son pruebas bloqueantes de esta construcción.
"""
from __future__ import annotations

import json
import math

import duckdb
import numpy as np
import pandas as pd
import yaml

from ..capa0 import ambitos_lima, insumos
from ..capa0.encuestas import Resultado, _en_universo
from ..capa0.gasto import CONTROLES_R2
from ..config import Rutas
from . import biblioteca

VERSION_TABLA = "1.2.0"
Z95 = 1.959963984540054
DECIMALES = 8  # redondeo de las estadísticas: misma huella en macOS y Linux
COLUMNAS = [
    "indicador_id", "anio", "nivel", "territorio_id", "territorio_nombre", "medida", "linea", "criterio", "valor",
    "ee", "cv", "ic_inf", "ic_sup", "metodo_ic", "gl", "n_muestra", "n_efectivo", "deff", "numerador", "denominador",
    "cota_inf", "cota_sup", "grupo_robusto_nacional", "grupo_robusto_regional", "metodo_territorio", "avisos",
    "estado_calculo", "motivo_calculo", "validada_dorada", "indicador_validado",
    # v1.1.0 (P2, 10/10/2026): campos que piden las reglas (R-GASTO-03, R-REG-09, R-REG-12, R-GASTO-07)
    "poblacion", "ubigeo_inei", "fecha_corte", "fecha_descarga", "anio_cerrado", "pct_gasto_atribuible",
    # v1.2.0 (S1-12, 4/11/2026): soles constantes del gasto (G-01, R-GASTO-12); nulas fuera de `devengado_constante`
    "anio_base_deflactor", "factor_deflactor", "version_tabla"]
CLAVE = ["indicador_id", "anio", "nivel", "territorio_id", "medida", "linea"]
AMBITOS = (ambitos_lima.LIMA_METROPOLITANA, ambitos_lima.LIMA_REGION, ambitos_lima.CALLAO)
ROTULOS = {ambitos_lima.LIMA_METROPOLITANA: "Lima Metropolitana (provincia de Lima)",
           ambitos_lima.LIMA_REGION: "Lima Región (Lima Provincias)", ambitos_lima.CALLAO: "Callao",
           ambitos_lima.AREA_METROPOLITANA_LIMA_CALLAO: "Lima Metropolitana y Callao",
           "PE": "Perú", "urbano": "área urbana", "rural": "área rural"}
DPTO_15_ROTULO = "departamento de Lima (Lima Metropolitana + Lima Región)"
ENDES_DEF = {"endes_anemia_6_35m": "anemia_6_35m", "endes_anemia_6_35m_oms2024": "anemia_6_35m_oms2024",
             "endes_dci_menores_5": "dci_menores_5"}
ENAHO_VAR = {"enaho_pobreza_monetaria": "pobre"}
GASTO_TEMA = {"gasto_ex_pan": ("cpt_grupo_expan", "grupo_expan"),
              "gasto_ex_pan_opcion_c": ("cpt_grupo_opcion_c", "grupo_opcion_c")}
SIEN_GRUPOS = ("6-11m", "12-23m", "24-35m")
# Gasto del 15 y el 07 (ambito_gasto, macro de vistas_gasto.sql): qué cuenta en la cifra y qué va en línea aparte
CIFRA_DPTO = {"15": {"LIMA_METROPOLITANA", "LIMA_REGION", "NO_ASIGNABLE_DPTO_LIMA"}, "07": {"CALLAO"}}
LINEA = {"REFERENCIA_NACIONAL": "referencia_nacional", "SEDE_NACIONAL": "sede_nacional",
         "NO_ASIGNABLE_DPTO_LIMA": "no_asignable_dpto_lima", "NO_ASIGNABLE_LIMA_CALLAO": "no_asignable_lima_callao",
         "REVISAR": "revisar"}
NIVELES_MUNICIPALES = {"provincia": ("provincia_municipal", "distrito_municipal", "provincia_inversion", "distrito_inversion"),
                       "distrito": ("distrito_municipal", "distrito_inversion")}


# ======================================================================= utilidades

def _fila(**kw) -> dict:
    f = {c: None for c in COLUMNAS}
    f.update(kw)
    f["version_tabla"] = VERSION_TABLA
    return f


def _nombres(rutas: Rutas) -> dict[tuple[str, str], str]:
    ins = insumos.tabla(rutas, "dim_ubigeo_historico")
    d = duckdb.connect().execute(f"""SELECT nivel, ubigeo_inei, nombre_mostrado FROM read_parquet('{ins.ruta}')
                                     WHERE vigente_hasta IS NULL""").df()
    out = {}
    for r in d.itertuples():
        clave = r.ubigeo_inei[:2] if r.nivel == "departamento" else r.ubigeo_inei
        out[(r.nivel, clave)] = r.nombre_mostrado
    return out


def _nombre(nombres: dict, nivel: str, tid: str) -> str | None:
    if tid in ROTULOS:
        return ROTULOS[tid]
    if nivel == "departamento" and tid == "15":
        return DPTO_15_ROTULO
    return nombres.get((nivel, tid))


def _wilson(x: float, n: float) -> tuple[float, float]:
    if not n:
        return (math.nan, math.nan)
    p = x / n
    d = 1 + Z95 ** 2 / n
    c = (p + Z95 ** 2 / (2 * n)) / d
    h = Z95 * math.sqrt(p * (1 - p) / n + Z95 ** 2 / (4 * n ** 2)) / d
    return (100 * max(0.0, c - h), 100 * min(1.0, c + h))


def _f(x):
    return None if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))) else float(x)


# ======================================================================= encuestas (svy)

def _svy_niveles(d: pd.DataFrame, y: pd.Series, universo: pd.Series, etiquetas: dict[str, pd.Series],
                 estrato: str, psu: str, peso: str) -> list[dict]:
    """Proporción con diseño para cada nivel: `etiquetas[nivel]` asigna a cada fila su territorio (None = fuera)."""
    import polars as pl
    import svy

    base = pd.DataFrame({"y": y.astype(float).fillna(0.0).to_numpy(), "u": universo.fillna(False).astype(bool).to_numpy(),
                         "h": d[estrato].astype(str).to_numpy(), "c": d[psu].astype(str).to_numpy(),
                         "w": d[peso].astype(float).to_numpy()})
    for nivel, s in etiquetas.items():
        base[f"t_{nivel}"] = s.astype(object).where(s.notna(), None).to_numpy()
    pdf = pl.from_pandas(base)
    muestra = svy.Sample(pdf, svy.Design(stratum="h", psu="c", wgt="w", singleton=svy.Singleton("center", domains="standard")))
    filas = []
    for nivel in etiquetas:
        col = f"t_{nivel}"
        est = muestra.estimation.prop("y", by=col, where=pl.col("u") & pl.col(col).is_not_null(),
                                      ci_method="korn-graubard", deff="wr")
        tab = est.to_polars().to_pandas()
        for tid, g in tab.groupby(col):
            uno = g[g.y == 1.0]
            if len(uno):
                r = uno.iloc[0]
                p, lo, hi = float(r.est), float(r.lci), float(r.uci)
            else:  # ningún «sí» en el dominio: complemento de la fila y = 0 (Korn-Graubard es simétrico)
                r = g[g.y == 0.0].iloc[0]
                p, lo, hi = 1 - float(r.est), 1 - float(r.uci), 1 - float(r.lci)
            se = float(r.se)
            filas.append(dict(nivel=nivel, territorio_id=str(tid), valor=100 * p, ee=100 * se,
                              cv=_f(100 * se / p) if p > 0 else None, ic_inf=100 * lo, ic_sup=100 * hi,
                              gl=int(r.df), n_muestra=int(r.n), deff=_f(r.get("deff")),
                              n_efectivo=_f(p * (1 - p) / se ** 2) if se > 0 else None))
    return filas


def _calcular_endes(rutas: Rutas, inds: dict, nombres: dict, res: Resultado) -> list[dict]:
    t = insumos.tabla(rutas, "endes_nino")
    i_def = insumos.curado(rutas, "definiciones_endes.yaml")
    res.insumos += [t, i_def]
    defs = yaml.safe_load(i_def.ruta.read_text(encoding="utf-8"))["indicadores"]
    endes = duckdb.connect().execute(f"SELECT * FROM read_parquet('{t.ruta}')").df()
    filas = []
    for iid, dkey in ENDES_DEF.items():
        ind, defi = inds[iid], defs[dkey]
        for anio in ind["anios_disponibles"]:
            d = endes[endes.anio == anio].reset_index(drop=True)
            u = _en_universo(d, int(anio), defi)
            amb = ambitos_lima.ambito_lima_endes(d)
            met = ambitos_lima.metodo_ambito_lima_endes(d)
            etiquetas = {"nacional": pd.Series("PE", index=d.index),
                         "dominio_subnacional": d.area,
                         "departamento": d.departamento.where(d.departamento != "07"),
                         "AMBITOS": amb}
            for r in _svy_niveles(d, d[defi["variable"]], u, etiquetas, "id_estrato", "id_conglomerado", "peso"):
                nivel = r.pop("nivel")
                if nivel == "AMBITOS":
                    nivel = r["territorio_id"]
                    metodo = sorted(set(met[(amb == nivel) & u].dropna()))
                    avisos = (["ambito_no_dominio"] if nivel != ambitos_lima.CALLAO else []) + \
                             (["ambito_por_estrato"] if ambitos_lima.METODO_ESTRATO in metodo else [])
                    mt = ";".join(metodo)
                else:
                    avisos, mt = [], {"nacional": None, "dominio_subnacional": "area", "departamento": "departamento_hv024"}[nivel]
                filas.append(_fila(indicador_id=iid, anio=int(anio), nivel=nivel,
                                   territorio_nombre=_nombre(nombres, nivel, r["territorio_id"]), medida="proporcion",
                                   linea="cifra", criterio=ind["criterio_medicion"], metodo_ic="korn-graubard",
                                   metodo_territorio=mt, avisos=json.dumps(avisos), estado_calculo="calculada", **r))
    return filas


def _calcular_enaho(rutas: Rutas, inds: dict, nombres: dict, res: Resultado) -> list[dict]:
    t = insumos.tabla(rutas, "enaho_sumaria")
    res.insumos.append(t)
    enaho = duckdb.connect().execute(f"SELECT * FROM read_parquet('{t.ruta}')").df()
    filas = []
    for iid, var in ENAHO_VAR.items():
        ind = inds[iid]
        for anio in ind["anios_disponibles"]:
            d = enaho[enaho.anio == anio].reset_index(drop=True)
            u = pd.Series(True, index=d.index)
            amb = ambitos_lima.ambito_lima_enaho(d)
            d8 = ambitos_lima.dominio8_enaho(d)
            etiquetas = {"nacional": pd.Series("PE", index=d.index), "dominio_subnacional": d.area,
                         "departamento": d.departamento.where(d.departamento != "07"), "AMBITOS": amb,
                         "AREA_METROPOLITANA_LIMA_CALLAO": pd.Series(ambitos_lima.AREA_METROPOLITANA_LIMA_CALLAO,
                                                                     index=d.index).where(d8)}
            for r in _svy_niveles(d, d[var], u, etiquetas, "id_estrato_diseno", "id_conglomerado", "peso_persona"):
                nivel = r.pop("nivel")
                if nivel == "AMBITOS":
                    nivel, avisos, mt = r["territorio_id"], ["ambito_no_dominio"], "ubigeo"
                elif nivel == "AREA_METROPOLITANA_LIMA_CALLAO":
                    avisos, mt = [], "variable_dominio"
                elif nivel == "departamento" and r["territorio_id"] == "15":
                    avisos, mt = ["ambito_no_dominio"], "ubigeo"
                else:
                    avisos, mt = [], {"nacional": None, "dominio_subnacional": "area", "departamento": "ubigeo"}[nivel]
                filas.append(_fila(indicador_id=iid, anio=int(anio), nivel=nivel,
                                   territorio_nombre=_nombre(nombres, nivel, r["territorio_id"]), medida="proporcion",
                                   linea="cifra", criterio=ind["criterio_medicion"], metodo_ic="korn-graubard",
                                   metodo_territorio=mt, avisos=json.dumps(avisos), estado_calculo="calculada", **r))
    return filas


# ======================================================================= SIEN

def _calcular_sien(rutas: Rutas, inds: dict, nombres: dict, res: Resultado) -> list[dict]:
    t = insumos.tabla(rutas, "fact_sien_hb_ubigeo")
    tp = insumos.tabla(rutas, "fact_poblacion_grupo")
    te = insumos.tabla(rutas, "dim_establecimiento_salud")
    res.insumos += [t, tp, te]
    con = duckdb.connect()
    s = con.execute(f"""SELECT * FROM read_parquet('{t.ruta}')
                        WHERE grupo_edad IN {SIEN_GRUPOS}""").df()
    est_nombre = dict(con.execute(f"SELECT cod_ipress, nombre FROM read_parquet('{te.ruta}')").fetchall())
    filas = []
    ubigeo_est = s.groupby("cod_ipress").ubigeo_eess.first().to_dict()
    # --- % de tamizados con anemia (por establecimiento y niveles superiores; base = ubicación del establecimiento)
    ind = inds["sien_anemia_tamizados_6_35m"]
    s["dpto"] = s.ubigeo_eess.str[:2]
    grupos = {"establecimiento": s.cod_ipress, "distrito": s.ubigeo_eess, "provincia": s.ubigeo_eess.str[:4] + "00",
              "departamento": s.dpto.where(s.dpto != "07"), "AMBITOS": ambitos_lima.ambito_por_ubigeo(s.ubigeo_eess),
              "nacional": pd.Series("PE", index=s.index)}
    for nivel, clave in grupos.items():
        g = s.assign(k=clave).dropna(subset=["k"]).groupby(["anio", "k"])[["filas_con_anemia", "filas_dx_valido"]].sum()
        for (anio, k), r in g.iterrows():
            nv = k if nivel == "AMBITOS" else nivel
            x, n = float(r.filas_con_anemia), float(r.filas_dx_valido)
            lo, hi = _wilson(x, n)
            nombre = est_nombre.get(k) if nivel == "establecimiento" else _nombre(nombres, nv, k)
            extra = {"ubigeo_inei": ubigeo_est.get(k)} if nivel == "establecimiento" else {}
            filas.append(_fila(**extra, indicador_id=ind["id"], anio=int(anio), nivel=nv, territorio_id=str(k),
                               territorio_nombre=nombre, medida="proporcion", linea="cifra",
                               criterio=ind["criterio_medicion"], valor=100 * x / n if n else None,
                               ic_inf=_f(lo), ic_sup=_f(hi), metodo_ic="wilson", n_muestra=int(n), numerador=x,
                               denominador=n, metodo_territorio="ubigeo_eess", avisos=json.dumps([]),
                               estado_calculo="calculada" if n else "sin_casos"))
    # --- cobertura de tamizaje (dos cotas; departamento, LM, LR y Callao)
    ind = inds["sien_cobertura_tamizaje_6_35m"]
    den = ind["denominador_ambitos_lima"]["propio"]
    pob = con.execute(f"""SELECT ubigeo_inei, anio, fuente_id, nivel, geografia_base, valor FROM read_parquet('{tp.ruta}')
                          WHERE grupo_id = '6-35m' AND sexo = 'T'""").df()
    s["proc_dpto"] = s.ubigeo_procedencia.str[:2]
    s["amb_proc"] = ambitos_lima.ambito_por_ubigeo(s.ubigeo_procedencia)
    s["amb_eess"] = ambitos_lima.ambito_por_ubigeo(s.ubigeo_eess)
    sin_proc = s.ubigeo_procedencia.isna()
    for anio in sorted(s.anio.unique()):
        sa, sp = s[s.anio == anio], sin_proc[s.anio == anio]
        of = pob[(pob.fuente_id == "INEI-PROYECCIONES-DEPARTAMENTAL-EDAD") & (pob.nivel == "departamento")
                 & (pob.anio == anio) & (pob.geografia_base == f"vigente_{anio}")]
        of = dict(zip(of.ubigeo_inei.str[:2], of.valor))
        ipf = pob[(pob.fuente_id == den["fuente_id"]) & (pob.nivel == "distrito") & (pob.anio == anio)
                  & (pob.geografia_base == f"vigente_{anio}")]
        pob_amb = {ambitos_lima.LIMA_METROPOLITANA: float(ipf[ipf.ubigeo_inei.str.startswith("1501")].valor.sum()),
                   ambitos_lima.LIMA_REGION: float(ipf[ipf.ubigeo_inei.str.startswith("15")
                                                       & ~ipf.ubigeo_inei.str.startswith("1501")].valor.sum()),
                   ambitos_lima.CALLAO: float(of.get("07", 0.0))}
        unidades = [("departamento", k, sa.proc_dpto == k, sp & (sa.dpto == k), of.get(k)) for k in sorted(of) if k != "07"]
        unidades += [(a, a, sa.amb_proc == a, sp & (sa.amb_eess == a), pob_amb[a]) for a in AMBITOS]
        for nivel, k, m_proc, m_eess, p in unidades:
            a, b = float(sa[m_proc.fillna(False)].filas.sum()), float(sa[m_eess.fillna(False)].filas.sum())
            ok = bool(p) and p > 0
            filas.append(_fila(indicador_id=ind["id"], anio=int(anio), nivel=nivel, territorio_id=k,
                               territorio_nombre=_nombre(nombres, nivel, k), medida="cobertura", linea="cifra",
                               criterio=ind["criterio_medicion"], valor=100 * (a + b) / p if ok else None,
                               numerador=a, denominador=p, cota_inf=100 * a / p if ok else None,
                               cota_sup=100 * (a + b) / p if ok else None, n_muestra=int(a + b),
                               metodo_territorio="ubigeo_procedencia",
                               avisos=json.dumps(["denominador_propio_ipf"] if k in (ambitos_lima.LIMA_METROPOLITANA,
                                                                                    ambitos_lima.LIMA_REGION) else []),
                               estado_calculo="calculada" if ok else "no_calculable",
                               motivo_calculo=None if ok else "sin_denominador"))
    return filas


# ======================================================================= gasto

def _calcular_gasto(rutas: Rutas, inds: dict, nombres: dict, res: Resultado) -> list[dict]:
    con, usados = biblioteca.conectar_gasto(rutas)
    res.insumos += usados
    sql = ("SELECT anio, nivel_atribucion, ubigeo_atribucion, departamento_atribucion, ambito_gasto, "
           "sum(devengado)::DOUBLE AS devengado, sum(pim)::DOUBLE AS pim, sum(pia)::DOUBLE AS pia, "
           "max(fecha_corte_datos) AS fecha_corte_datos, bool_and(es_anio_cerrado) AS es_anio_cerrado "
           "FROM gasto_tema(?) GROUP BY anio, nivel_atribucion, ubigeo_atribucion, departamento_atribucion, ambito_gasto")
    filas = []
    fechas_gasto = {}
    for iid, (tema, _) in GASTO_TEMA.items():
        ind = inds[iid]
        g = biblioteca.consultar_gasto(con, sql, [tema])
        fechas_gasto.update({int(a_): (str(f_), bool(c_)) for a_, f_, c_ in
                             g.groupby("anio").agg(f=("fecha_corte_datos", "max"), c=("es_anio_cerrado", "all")).itertuples()})
        g["dpto"] = g.departamento_atribucion
        g["linea"] = "cifra"
        for dp, cifra in CIFRA_DPTO.items():
            m = (g.dpto == dp) & ~g.ambito_gasto.isin(cifra)
            g.loc[m, "linea"] = g.loc[m, "ambito_gasto"].map(LINEA).fillna("revisar")
        # pct_gasto_atribuible (R-GASTO-03): devengado (o PIM/PIA) municipal y de proyectos ubicados / todo lo atribuido
        # al departamento salvo lo no territorializable; mismo tema, año y fase que la cifra
        base = g[g.nivel_atribucion != "nacional_no_territorializable"]
        mun = base.nivel_atribucion.str.startswith(("distrito_", "provincia_"))
        pct = {}
        for med in ("devengado", "pim", "pia"):
            num = base[mun].groupby(["anio", "dpto"])[med].sum()
            den = base.groupby(["anio", "dpto"])[med].sum()
            for (a_, d_), v in (num.reindex(den.index).fillna(0) / den.where(den != 0)).items():
                pct[(int(a_), d_, med)] = None if pd.isna(v) else float(v)
            nn, dd = base[mun].groupby("anio")[med].sum(), base.groupby("anio")[med].sum()
            for a_, v in (nn.reindex(dd.index).fillna(0) / dd.where(dd != 0)).items():
                pct[(int(a_), "PE", med)] = None if pd.isna(v) else float(v)
        dpto_de = {ambitos_lima.LIMA_METROPOLITANA: "15", ambitos_lima.LIMA_REGION: "15", ambitos_lima.CALLAO: "07"}

        def _pct(nv, tid, anio_, med):
            d_ = "PE" if nv == "nacional" else dpto_de.get(nv) or (tid[:2] if nv in ("departamento", "provincia", "distrito") else None)
            return pct.get((int(anio_), d_, med))
        unidades = [("nacional", pd.Series("PE", index=g.index), True)]
        unidades += [("departamento", g.dpto.where(g.dpto.str.fullmatch(r"\d\d") & (g.dpto != "00") & (g.dpto != "07")), False)]
        unidades += [("AMBITOS", g.ambito_gasto.where(g.ambito_gasto.isin(AMBITOS)), False)]
        # líneas aparte del 15 (también junto a LM y LR) y del 07 (junto al Callao); lo no asignable entre LM y LR es
        # parte de la cifra del departamento 15 y línea aparte de LM y LR
        g["linea_amb"] = g.linea.where(~((g.dpto == "15") & (g.ambito_gasto == "NO_ASIGNABLE_DPTO_LIMA")), "no_asignable_dpto_lima")
        unidades += [("LINEAS", g.dpto.where(g.dpto.isin(["15", "07"]) & (g.linea_amb != "cifra")), False)]
        # gasto sin departamento (no territorializable, código 00): línea aparte del total nacional
        unidades += [("SIN_DPTO", pd.Series("PE", index=g.index).where(~g.dpto.fillna("").str.fullmatch(r"\d\d") | (g.dpto == "00")), False)]
        for nivel_m, filtro in NIVELES_MUNICIPALES.items():
            m = g.nivel_atribucion.isin(filtro)
            clave = g.ubigeo_atribucion.str[:4] + "00" if nivel_m == "provincia" else g.ubigeo_atribucion
            unidades.append((nivel_m, clave.where(m & g.ubigeo_atribucion.str.fullmatch(r"\d{6}")), False))
        for nivel, clave, todo in unidades:
            x = g.assign(k=clave).dropna(subset=["k"])
            if nivel not in ("nacional", "LINEAS", "SIN_DPTO"):
                x = x[x.linea == "cifra"]
            if nivel in ("LINEAS", "SIN_DPTO"):
                x = x.assign(linea=x.linea_amb if nivel == "LINEAS" else "sin_departamento")
                agg = x.groupby(["anio", "k", "linea"])[["devengado", "pim", "pia"]].sum().reset_index()
                destinos = {"15": [("departamento", "15"), (ambitos_lima.LIMA_METROPOLITANA,) * 2,
                                   (ambitos_lima.LIMA_REGION,) * 2], "07": [(ambitos_lima.CALLAO,) * 2],
                            "PE": [("nacional", "PE")]}
                for r in agg.itertuples():
                    for nv, tid in destinos[r.k]:
                        if nv == "departamento" and r.linea == "no_asignable_dpto_lima":
                            continue  # ya está dentro de la cifra del departamento 15
                        for med in ("devengado", "pim", "pia"):
                            filas.append(_fila(indicador_id=iid, anio=int(r.anio), nivel=nv, territorio_id=tid,
                                               pct_gasto_atribuible=_pct(nv, tid, r.anio, med),
                                               territorio_nombre=_nombre(nombres, nv, tid), medida=med, linea=r.linea,
                                               criterio=ind["criterio_medicion"], valor=float(getattr(r, med)),
                                               metodo_territorio="ambito_gasto", avisos=json.dumps([]),
                                               estado_calculo="calculada"))
                continue
            agg = x.groupby(["anio", "k"])[["devengado", "pim", "pia"]].sum().reset_index()
            for r in agg.itertuples():
                nv = r.k if nivel == "AMBITOS" else nivel
                mt = {"nacional": None, "departamento": "departamento_meta", "provincia": "municipal_o_cui",
                      "distrito": "municipal_o_cui"}.get(nivel, "ambito_gasto")
                avisos = []
                if nv in (ambitos_lima.LIMA_METROPOLITANA, ambitos_lima.LIMA_REGION, ambitos_lima.CALLAO) or \
                        (nv == "departamento" and r.k == "15"):
                    avisos = ["sesgo_sede", "linea_referencia_nacional", "ejecutoras_mixtas"]
                    if nv == ambitos_lima.CALLAO:
                        avisos.append("callao_canasta_no_comparable")
                for med in ("devengado", "pim", "pia"):
                    filas.append(_fila(indicador_id=iid, anio=int(r.anio), nivel=nv, territorio_id=str(r.k),
                                       pct_gasto_atribuible=_pct(nv, str(r.k), r.anio, med),
                                       territorio_nombre=_nombre(nombres, nv, str(r.k)), medida=med, linea="cifra",
                                       criterio=ind["criterio_medicion"], valor=float(getattr(r, med)),
                                       metodo_territorio=mt, avisos=json.dumps(avisos), estado_calculo="calculada"))
    con.close()
    for f in filas:  # fecha de corte del gasto: fin del último mes con datos (fecha_corte_datos = AAAA-MM)
        fc, cerrado = fechas_gasto.get(f["anio"], (None, None))
        if fc:
            y, m = map(int, fc.split("-")[:2])
            f["fecha_corte"] = (pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0)).date().isoformat()
        f["anio_cerrado"] = cerrado
    return filas + _deflactar(rutas, filas, res)


def _deflactar(rutas: Rutas, filas: list[dict], res: Resultado) -> list[dict]:
    """S1-12 (G-01, R-GASTO-12): una fila `devengado_constante` por cada fila `devengado` del gasto, en soles del último
    año cerrado. Año base: el mayor año con el IPC completo (`anio_completo`) y con gasto en el cubo. Factor:
    ipc_prom_anual(base) / ipc_prom_anual(año). El PIM y el PIA no se deflactan. Sin el IPC completo de un año del gasto,
    se detiene con error."""
    ins = insumos.tabla(rutas, "dim_ipc")
    res.insumos.append(ins)
    ipc = pd.read_parquet(ins.ruta)
    return filas_constantes(filas, ipc)


def anio_base_deflactor(ipc: pd.DataFrame, anios_gasto) -> int:
    completos = set(ipc[ipc.anio_completo.astype(bool)].anio.astype(int))
    con_gasto = sorted(a for a in {int(a) for a in anios_gasto} if a in completos)
    if not con_gasto:
        raise ValueError("S1-12: ningún año del gasto tiene el IPC completo (dim_ipc.anio_completo)")
    return con_gasto[-1]


def factores_deflactor(ipc: pd.DataFrame, anios_gasto) -> tuple[int, dict[int, float]]:
    """(año base, {año: factor}) para los años del gasto. Lee `ipc_prom_anual` tal cual (no recalcula el promedio)."""
    anios = sorted({int(a) for a in anios_gasto})
    base = anio_base_deflactor(ipc, anios)
    prom = {}
    for a in anios:
        x = ipc[ipc.anio.astype(int) == a]
        if x.empty or not bool(x.anio_completo.astype(bool).all()) or x.ipc_prom_anual.isna().any():
            raise ValueError(f"S1-12: falta el IPC completo de {a} en dim_ipc (meses con dato: "
                             f"{int(x.meses_con_dato.max()) if not x.empty else 0}); no se puede deflactar el gasto")
        prom[a] = float(x.ipc_prom_anual.iloc[0])
    return base, {a: prom[base] / prom[a] for a in anios if a <= base}


def filas_constantes(filas: list[dict], ipc: pd.DataFrame) -> list[dict]:
    dev = [f for f in filas if f["medida"] == "devengado" and f["indicador_id"] in GASTO_TEMA]
    base, factor = factores_deflactor(ipc, [f["anio"] for f in dev])
    out = []
    for f in dev:
        if f["anio"] not in factor:
            continue  # un año posterior al base (aún sin IPC completo) no se expresa en soles del base
        g = dict(f)
        g.update(medida="devengado_constante", valor=f["valor"] * factor[f["anio"]], anio_base_deflactor=base,
                 factor_deflactor=factor[f["anio"]])
        out.append(g)
    return out


# ======================================================================= Mapa de Pobreza 2018

def _calcular_mapa(rutas: Rutas, inds: dict, nombres: dict, res: Resultado) -> list[dict]:
    t = insumos.tabla(rutas, "fact_mapa_pobreza")
    res.insumos.append(t)
    m = duckdb.connect().execute(f"SELECT * FROM read_parquet('{t.ruta}')").df()
    ind = inds["mapa_pobreza_2018"]
    filas = []
    for r in m.itertuples():
        avisos = ["estimado_en_agrupamiento"] if bool(r.estimado_en_agrupamiento) else []
        if bool(r.grupo_nacional_inferido):
            avisos.append("grupo_nacional_inferido")
        filas.append(_fila(indicador_id=ind["id"], anio=int(r.edicion), nivel=r.nivel, territorio_id=r.ubigeo_inei,
                           territorio_nombre=r.nombre_mostrado, medida="intervalo", linea="cifra",
                           criterio=ind["criterio_medicion"], ic_inf=float(r.pobreza_ic_inf), ic_sup=float(r.pobreza_ic_sup),
                           metodo_ic="publicado_inei",
                           grupo_robusto_nacional=None if pd.isna(r.grupo_robusto_nacional) else int(r.grupo_robusto_nacional),
                           grupo_robusto_regional=None if pd.isna(r.grupo_robusto_regional) else int(r.grupo_robusto_regional),
                           metodo_territorio="ubigeo", avisos=json.dumps(avisos), estado_calculo="calculada"))
    return filas


# ======================================================================= campos para las reglas (v1.1.0)

def _enriquecer(cubo: pd.DataFrame, rutas: Rutas, res: Resultado) -> None:
    """Población total del territorio (R-REG-12, R-REG-03; proyección distrital oficial del INEI, geografía vigente del
    año), ubigeo INEI de 6 dígitos (el del distrito del establecimiento), fecha de corte/descarga y año cerrado
    (R-REG-09, R-GASTO-07). El gasto ya trae su fecha de corte desde gasto_tema()."""
    tp = insumos.tabla(rutas, "fact_poblacion")
    res.insumos.append(tp)
    pob = duckdb.connect().execute(f"""SELECT ubigeo_inei, anio, valor FROM read_parquet('{tp.ruta}')
        WHERE fuente_id = 'INEI-PROYECCIONES-POBLACION-DISTRITAL' AND metodo = 'oficial' AND sexo = 'T'
          AND edad_min = 0 AND edad_max = 999 AND geografia_base = 'vigente_' || anio""").df()
    P = {(int(a), u): float(v) for u, a, v in pob.itertuples(index=False)}
    for a in {a for a, _ in P}:  # nacional = suma de los 25 departamentos (la proyección distrital no trae el total)
        if (a, "000000") not in P:
            P[(a, "000000")] = sum(v for (a2, u), v in P.items() if a2 == a and u.endswith("0000") and u != "000000")
    ub = []
    for nv, tid, u in zip(cubo.nivel, cubo.territorio_id, cubo.ubigeo_inei):
        if nv == "departamento":
            ub.append(tid + "0000")
        elif nv in ("provincia", "distrito"):
            ub.append(tid)
        elif nv == "nacional":
            ub.append("000000")
        else:
            ub.append(u)  # establecimiento: su distrito; ámbitos de Lima: sin ubigeo único
    cubo["ubigeo_inei"] = ub
    compuestos = {ambitos_lima.LIMA_METROPOLITANA: [("150100", 1)], ambitos_lima.LIMA_REGION: [("150000", 1), ("150100", -1)],
                  ambitos_lima.CALLAO: [("070000", 1)], ambitos_lima.AREA_METROPOLITANA_LIMA_CALLAO: [("150100", 1), ("070000", 1)]}

    def _pob(nv, u, a):
        partes = compuestos.get(nv) or ([(u, 1)] if u else None)
        if not partes or any((int(a), x) not in P for x, _ in partes):
            return None
        return sum(P[(int(a), x)] * s_ for x, s_ in partes)
    cubo["poblacion"] = [_pob(nv, u, a) for nv, u, a in zip(cubo.nivel, cubo.ubigeo_inei, cubo.anio)]
    # SIEN: el archivo no declara corte (data_cutoff): fecha de descarga de la captura fijada en el lock (R-REG-09)
    sien = insumos.ultimo(rutas, "INS-CENAN-SIEN", recurso="ins-cenan-sien")
    res.insumos.append(sien)
    m = cubo.indicador_id.str.startswith("sien_")
    cubo.loc[m, "fecha_corte"] = sien.corte
    cubo.loc[m, "fecha_descarga"] = str(sien.retrieved_at)[:10]
    cubo.loc[m, "anio_cerrado"] = cubo.loc[m, "anio"].astype(int) < int(str(sien.retrieved_at)[:4])
    enc = cubo.indicador_id.str.startswith(("endes_", "enaho_", "mapa_"))
    cubo.loc[enc, "anio_cerrado"] = True


# ======================================================================= pruebas

def _doradas(cubo: pd.DataFrame, dor: pd.DataFrame) -> pd.DataFrame:
    """Compara cada cifra dorada con la fila del cubo (misma llave). Encuestas: cifra redondeada ± tolerancia, casos
    exactos y CV ± tolerancia_cv donde se publican. Mapa: intervalo a 1 decimal."""
    c = cubo[cubo.linea == "cifra"].set_index(["indicador_id", "anio", "nivel", "territorio_id"]).sort_index()
    out = []
    for d in dor.itertuples():
        k = (d.indicador_id, int(d.anio), d.nivel, d.territorio)
        base = dict(id_cifra=d.id_cifra, indicador_id=d.indicador_id, anio=int(d.anio), nivel=d.nivel,
                    territorio=d.territorio, proposito=d.proposito, bloqueante=bool(d.bloqueante),
                    valor_publicado=d.valor_publicado)
        if k not in c.index:
            out.append({**base, "pasa": None, "nota": "sin fila en el cubo"})
            continue
        r = c.loc[[k]].iloc[0]
        if d.indicador_id == "mapa_pobreza_2018":
            ok = round(r.ic_inf, 1) == float(d.ic_inf_publicado) and round(r.ic_sup, 1) == float(d.ic_sup_publicado)
            out.append({**base, "ic_inf": r.ic_inf, "ic_sup": r.ic_sup, "pasa": ok})
            continue
        dif = round(round(float(r.valor), int(d.decimales)) - float(d.valor_publicado), 3)
        casos_ok = pd.isna(d.casos_publicados) or int(d.casos_publicados) == int(r.n_muestra)
        cv_dif = None if pd.isna(d.cv_publicado) else round(round(float(r.cv), 1) - float(d.cv_publicado), 2)
        cv_ok = pd.isna(d.tolerancia_cv) or cv_dif is None or abs(cv_dif) <= float(d.tolerancia_cv) + 1e-9
        out.append({**base, "valor": round(float(r.valor), 4), "diferencia_pp": dif, "n_muestra": int(r.n_muestra),
                    "casos_publicados": None if pd.isna(d.casos_publicados) else int(d.casos_publicados),
                    "cv": round(float(r.cv), 3) if r.cv is not None and not pd.isna(r.cv) else None,
                    "cv_publicado": d.cv_publicado, "cv_dif": cv_dif, "ic_inf": round(float(r.ic_inf), 3),
                    "ic_sup": round(float(r.ic_sup), 3), "ic_inf_publicado": d.ic_inf_publicado,
                    "ic_sup_publicado": d.ic_sup_publicado,
                    "pasa": abs(dif) <= float(d.tolerancia_pp) + 1e-9 and casos_ok and cv_ok})
    return pd.DataFrame(out)


def _pruebas(cubo: pd.DataFrame, inds: dict, rep: pd.DataFrame, res: Resultado) -> None:
    res.prueba("CAL-01", "fact_indicador: la clave (indicador, año, nivel, territorio, medida, línea) es única",
               not cubo.duplicated(CLAVE).any(), {"repetidas": int(cubo.duplicated(CLAVE).sum())})
    huecos = {}
    for iid, i in inds.items():
        for nv in i["niveles_validos"]:
            n = nv["nivel"]
            for a in i["anios_disponibles"]:
                if not ((cubo.indicador_id == iid) & (cubo.anio == a) & (cubo.nivel == n)).any():
                    huecos.setdefault(iid, []).append(f"{n} {a}")
    res.prueba("CAL-02", "fact_indicador: cada indicador tiene filas en todos sus niveles válidos y años disponibles "
               "(dim_indicador)", not huecos, {"huecos": huecos})
    blo = rep[rep.bloqueante & (rep.proposito == "R-ENC-18")]
    res.prueba("CAL-03", "R-ENC-18: el cubo reproduce TODAS las cifras doradas bloqueantes de encuestas (cifra a ± 0,1 pp, "
               "casos exactos y CV ± tolerancia donde el INEI los publica)", len(blo) > 0 and (blo.pasa == True).all(),  # noqa: E712
               {"comparadas": len(blo), "fallan": blo[blo.pasa != True].to_dict("records")})  # noqa: E712
    mapa = rep[rep.proposito == "control_ingesta"]
    res.prueba("CAL-04", "Mapa de Pobreza 2018: el intervalo del cubo es el publicado (control de ingesta)",
               len(mapa) > 0 and (mapa.pasa == True).all(), {"fallan": mapa[mapa.pasa != True].id_cifra.tolist()})  # noqa: E712
    ctrl = rep[(rep.proposito == "control") & rep.pasa.notna()]
    res.prueba("CAL-05", "Cifras doradas de control (no bloqueantes) que tienen fila en el cubo: se reproducen",
               (ctrl.pasa == True).all(), {"comparadas": len(ctrl), "fallan": ctrl[ctrl.pasa != True].id_cifra.tolist(),  # noqa: E712
                                           "sin_fila": rep[rep.pasa.isna()].id_cifra.tolist()}, bloqueante=False)
    reg = rep[rep.bloqueante & (rep.proposito == "control_registro")]
    res.prueba("CAL-10", "Registros (SIEN): el cubo reproduce las cifras oficiales del INS (cifra a 1 decimal y número de "
               "evaluados exactos; 12/10/2026)", len(reg) > 0 and (reg.pasa == True).all(),  # noqa: E712
               {"comparadas": len(reg), "fallan": reg[reg.pasa != True].to_dict("records")})  # noqa: E712
    # V4 (D-ENA-1): CV de la ENAHO calculado con svy frente al publicado
    e = rep[(rep.indicador_id == "enaho_pobreza_monetaria") & rep.cv_publicado.notna() & rep.cv.notna()] \
        if "cv_publicado" in rep else rep.iloc[0:0]
    dif = (e.cv.astype(float) - e.cv_publicado.astype(float)).abs()
    res.prueba("CAL-06", "V4: el CV de la ENAHO con svy difiere ≤ 0,5 puntos del publicado (aviso, no bloquea)",
               bool((dif <= 0.5).all()), {"comparadas": len(e), "max_dif": round(float(dif.max()), 3) if len(e) else None},
               bloqueante=False)
    # gasto: controles de las rondas 1–2 y conservación (R-GASTO-01)
    obt, mal = {}, {}
    for iid, (_, k) in GASTO_TEMA.items():
        n = cubo[(cubo.indicador_id == iid) & (cubo.nivel == "nacional") & (cubo.medida == "devengado")]
        obt[k] = {int(a): round(v / 1e6) for a, v in zip(n.anio, n.valor)}
        if obt[k] != CONTROLES_R2[k]:
            mal[k] = obt[k]
    res.prueba("CAL-07", "Gasto: el devengado nacional del cubo reproduce los controles aprobados (ex-PAN por concepto y "
               "opción C, 2023–2025, millones)", not mal, {"obtenido": obt, "control": {k: CONTROLES_R2[k] for k in obt}})
    malos = {}
    for iid in GASTO_TEMA:
        g = cubo[(cubo.indicador_id == iid) & (cubo.medida == "devengado")]
        for a in sorted(g.anio.unique()):
            ga = g[g.anio == a]
            nac = float(ga[(ga.nivel == "nacional") & (ga.linea == "cifra")].valor.sum())
            partes = float(ga[(ga.nivel == "nacional") & (ga.linea == "sin_departamento")].valor.sum()) \
                + float(ga[(ga.nivel == "departamento") & (ga.linea == "cifra")].valor.sum()) \
                + float(ga[(ga.nivel == ambitos_lima.CALLAO) & (ga.linea == "cifra")].valor.sum()) \
                + float(ga[(ga.nivel == "departamento") & (ga.territorio_id == "15") & (ga.linea != "cifra")].valor.sum()) \
                + float(ga[(ga.nivel == ambitos_lima.CALLAO) & (ga.linea != "cifra")].valor.sum())
            lm_lr = float(ga[ga.nivel.isin([ambitos_lima.LIMA_METROPOLITANA, ambitos_lima.LIMA_REGION]) & (ga.linea == "cifra")].valor.sum()) \
                + float(ga[(ga.nivel == ambitos_lima.LIMA_METROPOLITANA) & (ga.linea == "no_asignable_dpto_lima")].valor.sum())
            d15 = float(ga[(ga.nivel == "departamento") & (ga.territorio_id == "15") & (ga.linea == "cifra")].valor.sum())
            if abs(nac - partes) > 1 or abs(lm_lr - d15) > 1:
                malos[f"{iid} {a}"] = {"nacional": nac, "suma_partes": partes, "lm_lr_noasig": lm_lr, "dpto15": d15}
    res.prueba("CAL-08", "Gasto (R-GASTO-01): nacional = departamentos + Callao + líneas aparte del 15 y el 07 (los "
               "gasto sin departamento, en su línea del nacional); LM + LR + no asignable = departamento 15 "
               "(±1 sol)", not malos, {"malos": malos})
    # S1-12: soles constantes (R-GASTO-12): solo del devengado del gasto, una por cada fila devengado, valor = devengado × factor
    k = ["indicador_id", "anio", "nivel", "territorio_id", "linea"]
    cst = cubo[cubo.medida == "devengado_constante"]
    dev = cubo[(cubo.medida == "devengado") & cubo.indicador_id.isin(list(GASTO_TEMA))]
    dev = dev[dev.anio <= (cst.anio_base_deflactor.max() if len(cst) else -1)]
    par = dev.merge(cst, on=k, how="outer", suffixes=("_d", "_c"), indicator=True)
    dif = (par.valor_c - par.valor_d * par.factor_deflactor_c).abs()
    res.prueba("CAL-11", "Gasto (R-GASTO-12, S1-12): cada fila devengado hasta el año base tiene su fila devengado_constante "
               "(solo en el gasto) con valor = devengado × factor del IPC", len(cst) > 0 and bool((par._merge == "both").all())
               and set(cst.indicador_id) <= set(GASTO_TEMA) and bool((dif < 1e-4).all()) and cst.anio_base_deflactor.nunique() == 1,
               {"filas": len(cst), "sin_par": int((par._merge != "both").sum()), "max_dif": float(dif.max()) if len(dif) else None,
                "anio_base": sorted(int(x) for x in cst.anio_base_deflactor.dropna().unique())})
    sien = cubo[(cubo.indicador_id == "sien_anemia_tamizados_6_35m")]
    nac = sien[sien.nivel == "nacional"].set_index("anio").numerador
    suma = sien[sien.nivel.isin(["departamento", ambitos_lima.CALLAO])].groupby("anio").numerador.sum()
    cob = cubo[cubo.indicador_id == "sien_cobertura_tamizaje_6_35m"]
    res.prueba("CAL-09", "SIEN: numerador nacional = suma de departamentos + Callao; en la cobertura, cota_inf ≤ cota_sup",
               bool((nac - suma.reindex(nac.index)).abs().max() < 1e-6) and bool((cob.cota_inf <= cob.cota_sup + 1e-9).all()),
               {"nacional": nac.to_dict(), "suma": suma.to_dict()})


# ======================================================================= construcción

def construir(rutas: Rutas) -> Resultado:
    res = Resultado()
    i_ind = insumos.curado(rutas, "dim_indicador.yaml")
    i_dor = insumos.curado(rutas, "cifras_doradas.csv")
    res.insumos += [i_ind, i_dor, insumos.tabla(rutas, "dim_ubigeo_historico")]
    inds = {i["id"]: i for i in yaml.safe_load(i_ind.ruta.read_text(encoding="utf-8"))["indicadores"]}
    nombres = _nombres(rutas)
    filas = []
    for paso in (_calcular_endes, _calcular_enaho, _calcular_sien, _calcular_gasto, _calcular_mapa):
        filas += paso(rutas, inds, nombres, res)
    cubo = pd.DataFrame(filas, columns=COLUMNAS)
    _enriquecer(cubo, rutas, res)
    dor = pd.read_csv(i_dor.ruta, dtype={"territorio": str, "id_cifra": str})
    dor["bloqueante"] = dor.bloqueante.astype(bool)
    rep = _doradas(cubo, dor[dor.indicador_id.isin(list(inds))])
    # cifra validada por una dorada bloqueante; indicador validado si pasan todas sus bloqueantes (R-ENC-18)
    ok = rep[rep.bloqueante & (rep.pasa == True)]  # noqa: E712
    llave = {(r.indicador_id, r.anio, r.nivel, r.territorio): r.id_cifra for r in ok.itertuples()}
    cubo["validada_dorada"] = [llave.get((a, b, c, d)) if m == "cifra" else None
                               for a, b, c, d, m in zip(cubo.indicador_id, cubo.anio, cubo.nivel, cubo.territorio_id, cubo.linea)]
    blo = rep[rep.bloqueante]
    validados = {i for i in inds if (blo.indicador_id == i).any() and (blo[blo.indicador_id == i].pasa == True).all()}  # noqa: E712
    cubo["indicador_validado"] = cubo.indicador_id.isin(validados)
    _pruebas(cubo, inds, rep, res)
    for c in ("anio", "gl", "n_muestra", "grupo_robusto_nacional", "grupo_robusto_regional"):
        cubo[c] = cubo[c].astype("Int64")
    # Redondeo a 8 decimales (P2, 10/10/2026): la cuantila beta de Korn-Graubard difiere ~1e-14 entre macOS y Linux
    # (libm), y eso cambiaba la huella del Parquet entre máquinas. 8 decimales sobran (cifras en % y soles).
    for c in ("valor", "ee", "cv", "ic_inf", "ic_sup", "n_efectivo", "deff", "numerador", "denominador", "cota_inf", "cota_sup"):
        cubo[c] = cubo[c].astype("Float64").round(DECIMALES)
    for c in ("poblacion", "pct_gasto_atribuible"):
        cubo[c] = cubo[c].astype("Float64").round(DECIMALES)
    cubo["anio_base_deflactor"] = cubo.anio_base_deflactor.astype("Int64")
    cubo["factor_deflactor"] = cubo.factor_deflactor.astype("Float64")    # sin redondear: valor = devengado × factor
    cubo["anio_cerrado"] = cubo.anio_cerrado.astype("boolean")
    for c in ("ubigeo_inei", "fecha_corte", "fecha_descarga"):
        cubo[c] = cubo[c].astype("string")
    for c in ("indicador_id", "nivel", "territorio_id", "territorio_nombre", "medida", "linea", "criterio", "metodo_ic",
              "metodo_territorio", "avisos", "estado_calculo", "motivo_calculo", "validada_dorada", "version_tabla"):
        cubo[c] = cubo[c].astype("string")
    cubo["indicador_validado"] = cubo.indicador_validado.astype("boolean")
    res.tablas["fact_indicador"] = cubo
    res.revision["doradas_reproduccion_p1"] = rep
    res.revision["resumen_cubo"] = cubo.groupby(["indicador_id", "nivel", "medida", "linea"]).size().rename("filas").reset_index()
    return res
