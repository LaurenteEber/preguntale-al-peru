"""Sprint S2 — Población: fact_poblacion (oficial, censado y prorrateo propio por IPF).

Reglas: R-DENOMINADORES-01/02/03/07, R-TERRITORIO-04/05. Decisiones del 6/10/2026 (series 2018-2026 por grupo
comparable; sin valores inventados para distritos antes de su creación).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..config import Rutas
from ..errores import PapError
from . import insumos
from . import lectores as L
from . import territorio as T

VERSION_TABLA = "1.1.0"
ANIOS = list(range(2018, 2027))
EDAD_MAX = 80  # 80 = «80 y más» (máxima edad simple común a las fuentes)
V_DIST = "INEI-PROY-DIST|base=CPV2017|ed=2025-12"
V_B25 = "INEI-PROY-DEP-EDAD|base=CPV2017|ed=2020-01"
V_B39 = "INEI-PROY-DEP-SEXO-QQ|base=CPV2017|ed=2019-10"
V_CENSO = "CPV2017|censada|ed=2018-10"
# PO-08: el vintage del prorrateo nombra las ediciones de los tres márgenes y de la semilla
V_IPF = "PROP-IPF|dist=INEI-ed2025-12|edad=B25-ed2020-01|sexo=B39-ed2019-10|semilla=CPV2017"
UMBRAL_QUIEBRE_TENDENCIA = 1.5  # PO-04: cambio de la tasa anual de crecimiento (puntos porcentuales)
TOL_IPF = 0.001        # tolerancia de aceptación (R-DENOMINADORES-03)
TOL_IPF_INTERNA = 1e-6  # se itera hasta aquí para que los márgenes cuadren casi exactos
MAX_IT = 100
SEMILLA_CERO = 0.5  # R-DENOMINADORES-03: las celdas censales vacías parten de 0,5 (no de 0)
# Grupos de edad en meses que el piloto necesita (anemia 6-35 y 6-59 meses; desnutrición 0-59 meses).
# Con edades simples en años, 6-35 m = 0,5·P0 + P1 + P2 suponiendo nacimientos uniformes dentro del año (PO-02).
GRUPOS_MESES = {
    "0-35m": (0, 35, {0: 1.0, 1: 1.0, 2: 1.0}, "exacta"),
    "6-35m": (6, 35, {0: 0.5, 1: 1.0, 2: 1.0}, "uniforme_edad0"),
    "0-59m": (0, 59, {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0}, "exacta"),
    "6-59m": (6, 59, {0: 0.5, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0}, "uniforme_edad0"),
}
SUPUESTO_UNIFORME = "Nacimientos uniformes dentro del año: la mitad de la población de edad 0 tiene 6-11 meses"
CENSADA_NACIONAL_2017 = 29_381_884  # INEI, Resultados definitivos CPV2017


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


def _fila(fuente, vintage, metodo, geo, ubigeo, anio, fecha, emin, emax, sexo, valor, semilla=None, it=None, err=None):
    return (fuente, vintage, metodo, geo, ubigeo, L.nivel_de(ubigeo) if not ubigeo.startswith("G-") else "distrito",
            anio, fecha, emin, emax, sexo, valor, semilla, it, err)


COLUMNAS = ["fuente_id", "vintage", "metodo", "geografia_base", "ubigeo_inei", "nivel", "anio", "fecha_referencia",
            "edad_min", "edad_max", "sexo", "valor", "semilla", "iteraciones_ipf", "error_max_ipf"]


def ipf(semilla: np.ndarray, m_dist: np.ndarray, m_edad: np.ndarray, m_sq: np.ndarray, grupo_q: np.ndarray):
    """Ajuste a tres márgenes: distrito (I), edad simple (A) y sexo×quinquenio (S,Q). semilla: (I, A, S)."""
    x = semilla.astype(float).copy()
    Q = m_sq.shape[1]
    onehot = np.zeros((x.shape[1], Q))
    onehot[np.arange(x.shape[1]), grupo_q] = 1.0
    err = np.inf
    for it in range(1, MAX_IT + 1):
        f = np.divide(m_dist, x.sum(axis=(1, 2)), out=np.zeros_like(m_dist, dtype=float), where=x.sum(axis=(1, 2)) > 0)
        x *= f[:, None, None]
        f = np.divide(m_edad, x.sum(axis=(0, 2)), out=np.zeros_like(m_edad, dtype=float), where=x.sum(axis=(0, 2)) > 0)
        x *= f[None, :, None]
        actual_sq = np.einsum("ias,aq->sq", x, onehot)
        f = np.divide(m_sq, actual_sq, out=np.zeros_like(m_sq, dtype=float), where=actual_sq > 0)
        x *= np.einsum("sq,aq->as", f, onehot)[None, :, :]
        e1 = np.abs(x.sum(axis=(1, 2)) - m_dist) / np.maximum(m_dist, 1)
        e2 = np.abs(x.sum(axis=(0, 2)) - m_edad) / np.maximum(m_edad, 1)
        e3 = np.abs(np.einsum("ias,aq->sq", x, onehot) - m_sq) / np.maximum(m_sq, 1)
        err = float(max(e1.max(), e2.max(), e3.max()))
        if err < TOL_IPF_INTERNA:
            break
    return x, it, err


def construir(rutas: Rutas) -> Resultado:
    res = Resultado()
    proy, _, i_proy = L.proyeccion(rutas, "INEI-PROYECCIONES-POBLACION-DISTRITAL")
    b25, i_b25 = L.dep_edad_simple(rutas)
    b39, i_b39 = L.dep_sexo_quinquenal(rutas)
    censo, i_censo = L.censo_edad_sexo(rutas)
    semilla_propia, i_sem = L.semilla_propio(rutas)
    i_dim = insumos.tabla(rutas, "dim_ubigeo_historico")
    altas = T.leer_yaml(rutas, "altas_post2017.yaml")
    res.insumos = [i_proy, i_b25, i_b39, *i_censo, i_sem, i_dim,
                   insumos.curado(rutas, "altas_post2017.yaml"), insumos.curado(rutas, "redatam_cpv2017_edad_sexo.txt")]

    proy = proy[proy.ubigeo != "000000"].copy()
    dist = proy[proy.nivel == "distrito"].copy()
    base2017 = set(censo.ubigeo)
    # Los grupos comparables se leen de la tabla de territorio (no se recalculan): una sola definición (RP-01)
    import duckdb
    dimu = duckdb.sql(f"SELECT DISTINCT ubigeo_inei, grupo_comparable_geo2017 FROM '{i_dim.ruta}' WHERE nivel = 'distrito'").df()
    if dimu.ubigeo_inei.duplicated().any():
        raise PapError("dim_ubigeo_historico: un distrito con dos grupos comparables")
    grupo = dict(zip(dimu.ubigeo_inei, dimu.grupo_comparable_geo2017))
    faltan_grupo = sorted(set(dist.ubigeo) - set(grupo))
    if faltan_grupo:
        raise PapError(f"Distritos de la proyección sin versión en dim_ubigeo_historico: {faltan_grupo[:10]}")
    origen_principal = {a["ubigeo"]: next((o["ubigeo"] for o in a["origenes"] if o.get("principal")), a["origenes"][0]["ubigeo"])
                        for a in altas}

    # ---------------- pruebas de consistencia de los insumos
    for anio in ANIOS:
        c = f"p{anio}"
        s_dep = dist.groupby(dist.ubigeo.str[:2])[c].sum()
        s_prov = dist.groupby(dist.ubigeo.str[:4])[c].sum()
        dep = proy[proy.nivel == "departamento"].set_index(proy[proy.nivel == "departamento"].ubigeo.str[:2])[c]
        prov = proy[proy.nivel == "provincia"].set_index(proy[proy.nivel == "provincia"].ubigeo.str[:4])[c]
        t25 = b25[(b25.anio == anio) & (b25.edad == -1) & (b25.dep != "00")].set_index("dep").valor
        t39 = b39[(b39.anio == anio) & (b39.edad_min == -1) & (b39.sexo == "T")].set_index("dep").valor
        res.prueba("P2-01", f"{anio}: Σ distritos = provincia y = departamento (exacto)",
                   (s_dep - dep).abs().max() == 0 and (s_prov - prov).abs().max() == 0)
        res.prueba("P2-02", f"{anio}: total departamental idéntico en proyección distrital, Boletín 25 y Boletín 39",
                   (s_dep - t25).abs().max() == 0 and (s_dep - t39).abs().max() == 0,
                   {"max_dif_b25": float((s_dep - t25).abs().max()), "max_dif_b39": float((s_dep - t39).abs().max())})
    tot25 = b25[b25.edad == -1].set_index(["dep", "anio"]).valor
    sum25 = b25[b25.edad >= 0].groupby(["dep", "anio"]).valor.sum()
    sx = b39[b39.edad_min == -1].pivot_table(index=["dep", "anio"], columns="sexo", values="valor")
    res.prueba("P2-03", "Boletines: edades suman al total (B25) y hombres + mujeres = total (B39)",
               (tot25 - sum25).abs().max() == 0 and (sx.M + sx.F - sx["T"]).abs().max() == 0)
    # coherencia B25 (edad simple) vs B39 (quinquenios) por grupo
    b25q = b25[b25.edad >= 0].assign(q=lambda d: np.minimum(d.edad // 5 * 5, EDAD_MAX)).groupby(["dep", "anio", "q"]).valor.sum()
    b39q = (b39[(b39.edad_min >= 0) & (b39.sexo == "T")].assign(q=lambda d: np.minimum(d.edad_min, EDAD_MAX))
            .groupby(["dep", "anio", "q"]).valor.sum())
    dq = (b25q - b39q).abs()
    res.prueba("P2-04", "Edad simple (B25) y quinquenios (B39) coinciden por grupo de edad", dq.max() <= 1,
               {"max_dif": float(dq.max())}, bloqueante=False)
    n_censo = int(censo.casos.sum())
    res.prueba("P2-05", f"Censo 2017 (REDATAM): {len(base2017)} distritos y total censado = {CENSADA_NACIONAL_2017:,}",
               len(base2017) == T.DISTRITOS_GEO2017 and n_censo == CENSADA_NACIONAL_2017, {"distritos": len(base2017), "total": n_censo})

    # ---------------- filas oficiales y censadas
    filas = []
    for r in proy.itertuples():
        for anio in ANIOS:
            v = getattr(r, f"p{anio}")
            if v is not None and not pd.isna(v):
                filas.append(_fila("INEI-PROYECCIONES-POBLACION-DISTRITAL", V_DIST, "oficial", f"vigente_{anio}",
                                   r.ubigeo, anio, f"{anio}-06-30", 0, 999, "T", float(v)))
    # Totales departamentales (0-999, ambos sexos): 2018-2026 desde la proyección distrital (idénticos, P2-02);
    # los boletines aportan solo la desagregación por edad/sexo y los totales de los demás años.
    for r in b25.itertuples():
        if r.edad == -1 and r.dep != "00" and r.anio in ANIOS:
            continue
        u = "000000" if r.dep == "00" else r.dep + "0000"
        emin, emax = (0, 999) if r.edad == -1 else (r.edad, 999 if r.edad == EDAD_MAX else r.edad)
        filas.append(_fila("INEI-PROYECCIONES-DEPARTAMENTAL-EDAD", V_B25, "oficial", f"vigente_{r.anio}", u, r.anio,
                           f"{r.anio}-06-30", emin, emax, "T", float(r.valor)))
    for r in b39.itertuples():
        if r.edad_min == -1 and r.sexo == "T":
            continue  # igual al total del Boletín 25 (P2-03)
        emin, emax = (0, 999) if r.edad_min == -1 else (r.edad_min, 999 if r.edad_min == 100 else r.edad_min + 4)
        filas.append(_fila("INEI-PROYECCIONES-DEPARTAMENTAL-EDAD", V_B39, "oficial", f"vigente_{r.anio}", r.dep + "0000",
                           r.anio, f"{r.anio}-06-30", emin, emax, r.sexo, float(r.valor)))
    # PO-06: el censo por distrito va como geografía vigente en 2017; la suma por grupo comparable se materializa
    # abajo con geografia_base='GEO2017', con los mismos códigos (G-…) que la proyección y el prorrateo
    for r in censo.itertuples():
        filas.append(_fila("INEI-CPV2017", V_CENSO, "censado", "vigente_2017", r.ubigeo, 2017, "2017-10-22",
                           int(r.edad), int(r.edad), "M" if r.sexo == 1 else "F", float(r.casos)))

    # ---------------- prorrateo propio (IPF) por departamento y año
    edades = np.arange(EDAD_MAX + 1)
    grupo_q = np.minimum(edades // 5, EDAD_MAX // 5)
    cz = censo.assign(edad=np.minimum(censo.edad, EDAD_MAX), s=censo.sexo - 1).groupby(["ubigeo", "edad", "s"]).casos.sum()
    cub = cz.unstack(["edad", "s"], fill_value=0)
    resumen_ipf = []
    bloques_ipf = []
    for anio in ANIOS:
        col = f"p{anio}"
        for dep in sorted(dist.ubigeo.str[:2].unique()):
            dd = dist[(dist.ubigeo.str[:2] == dep) & dist[col].notna()]
            ubis = dd.ubigeo.tolist()
            sem = np.zeros((len(ubis), len(edades), 2))
            semillas = []
            for k, u in enumerate(ubis):
                fuente_sem = u if u in cub.index else origen_principal.get(u)
                if fuente_sem not in cub.index:
                    raise PapError(f"Sin semilla censal para {u}")
                semillas.append("CPV2017" if fuente_sem == u else f"CPV2017:{fuente_sem}")
                v = cub.loc[fuente_sem]
                for (e, s), c in v.items():
                    sem[k, int(e), int(s)] = c
            sem[sem == 0] = SEMILLA_CERO
            m_dist = dd[col].to_numpy(float).copy()
            e25 = b25[(b25.dep == dep) & (b25.anio == anio) & (b25.edad >= 0)].set_index("edad").valor
            m_edad = e25.reindex(edades).to_numpy(float).copy()
            q39 = (b39[(b39.dep == dep) & (b39.anio == anio) & (b39.edad_min >= 0) & (b39.sexo.isin(["M", "F"]))]
                   .assign(q=lambda d: np.minimum(d.edad_min, EDAD_MAX) // 5)
                   .groupby(["sexo", "q"]).valor.sum().unstack("q"))
            m_sq = q39.reindex(["M", "F"]).to_numpy(float).copy()
            # ajustar B39 por grupo para que sea coherente con B25 (diferencias de redondeo de ±1)
            m_sq *= (np.bincount(grupo_q, weights=m_edad) / m_sq.sum(axis=0))[None, :]
            x, it, err = ipf(sem, m_dist, m_edad, m_sq, grupo_q)
            resumen_ipf.append({"anio": anio, "departamento": dep, "distritos": len(ubis), "iteraciones": it, "error_max": err})
            n_i, n_a, n_s = x.shape
            bloques_ipf.append(pd.DataFrame({
                "ubigeo_inei": np.repeat(ubis, n_a * n_s),
                "anio": anio,
                "edad_min": np.tile(np.repeat(edades, n_s), n_i),
                "sexo": np.tile(np.array(["M", "F"]), n_i * n_a),
                "valor": np.round(x.reshape(-1), 3),
                "semilla": np.repeat(semillas, n_a * n_s),
                "iteraciones_ipf": it,
                "error_max_ipf": round(err, 6),
            }))
    rip = pd.DataFrame(resumen_ipf)
    res.prueba("P2-06", f"IPF converge en todos los departamentos y años (tolerancia {TOL_IPF}, ≤ {MAX_IT} iteraciones)",
               (rip.error_max < TOL_IPF).all() and (rip.iteraciones <= MAX_IT).all(),
               {"peor_error": float(rip.error_max.max()), "max_iteraciones": int(rip.iteraciones.max())})
    res.revision["ipf_convergencia"] = rip

    pro = pd.concat(bloques_ipf, ignore_index=True)
    pro["edad_max"] = np.where(pro.edad_min == EDAD_MAX, 999, pro.edad_min)
    pro["fuente_id"] = "PROPIO-PRORRATEO-IPF"
    pro["vintage"] = V_IPF
    pro["metodo"] = "prorrateo_propio"
    pro["geografia_base"] = "vigente_" + pro.anio.astype(str)
    pro["nivel"] = "distrito"
    pro["fecha_referencia"] = pro.anio.astype(str) + "-06-30"
    del bloques_ipf
    fact = pd.concat([pd.DataFrame(filas, columns=COLUMNAS), pro[COLUMNAS]], ignore_index=True)
    del pro, filas
    for c in ("fuente_id", "vintage", "metodo", "geografia_base", "nivel", "fecha_referencia", "sexo", "semilla"):
        fact[c] = fact[c].astype("category")

    # ---------------- materialización GEO2017 (suma por grupo comparable)
    dist_rows = fact.loc[(fact.nivel == "distrito") & fact.metodo.isin(["oficial", "prorrateo_propio", "censado"])
                         & fact.geografia_base.astype(str).str.startswith("vigente_"),
                         ["fuente_id", "vintage", "metodo", "ubigeo_inei", "anio", "fecha_referencia", "edad_min",
                          "edad_max", "sexo", "valor"]].copy()
    dist_rows["ubigeo_inei"] = dist_rows.ubigeo_inei.map(lambda u: grupo.get(u, u))
    for c in ("fuente_id", "vintage", "metodo", "fecha_referencia", "sexo"):
        dist_rows[c] = dist_rows[c].astype(str)
    geo = (dist_rows.groupby(["fuente_id", "vintage", "metodo", "ubigeo_inei", "anio", "fecha_referencia",
                              "edad_min", "edad_max", "sexo"], as_index=False, sort=False).valor.sum())
    del dist_rows
    geo["nivel"] = "distrito"
    geo["geografia_base"] = "GEO2017"
    geo["valor"] = geo.valor.round(3)
    geo["semilla"] = np.where(geo.metodo == "prorrateo_propio", "CPV2017", None)
    geo["fecha_referencia"] = geo.fecha_referencia.astype(str)
    geo["iteraciones_ipf"] = None
    geo["error_max_ipf"] = None
    for c in ("fuente_id", "vintage", "metodo", "geografia_base", "nivel", "fecha_referencia", "sexo", "semilla"):
        fact[c] = fact[c].astype(str).replace("None", None)
    fact = pd.concat([fact, geo[COLUMNAS]], ignore_index=True)
    fact["version_tabla"] = VERSION_TABLA

    # ---------------- pruebas sobre la tabla final
    ofi = fact[(fact.metodo == "oficial") & (fact.fuente_id == "INEI-PROYECCIONES-POBLACION-DISTRITAL")]
    pro = fact[fact.metodo == "prorrateo_propio"]
    m = (pro[pro.geografia_base.astype(str).str.startswith("vigente_")].groupby(["ubigeo_inei", "anio"]).valor.sum()
         .to_frame("ipf").join(ofi[(ofi.nivel == "distrito") & ofi.geografia_base.astype(str).str.startswith("vigente_")]
                               .set_index(["ubigeo_inei", "anio"]).valor.rename("ofi")))
    rel = ((m.ipf - m.ofi).abs() / m.ofi.clip(lower=1))
    res.prueba("P2-07", "Prorrateo: cada distrito suma su total oficial (error relativo ≤ 0,001)", rel.max() <= TOL_IPF,
               {"max_error_relativo": float(rel.max())})
    g_ofi = ofi[ofi.geografia_base == "GEO2017"].groupby(["ubigeo_inei", "anio"]).valor.sum().unstack("anio")
    salto = []
    for g, fila in g_ofi.iterrows():
        v = (fila.pct_change().iloc[1:] * 100).tolist()
        med = float(np.median(v))
        salto += [(g, ANIOS[i + 1], round(x, 1)) for i, x in enumerate(v)
                  if abs(x - med) > 5 and all(abs(y - med) <= 3 for y in [v[j] for j in (i - 1, i + 1) if 0 <= j < len(v)])]
    res.prueba("P2-08", "Series GEO2017 2018-2026 sin saltos aislados (población continua por grupo)", not salto, salto[:10])
    # PO-04: cambios de tendencia (empalme de ediciones del INEI 2020→2021), no bloqueante, con lista de revisión
    tasas = g_ofi.pct_change(axis=1).iloc[:, 1:] * 100
    dtasa = tasas.diff(axis=1).iloc[:, 1:].abs()
    qt = dtasa.stack()
    qt = qt[qt > UMBRAL_QUIEBRE_TENDENCIA].rename("cambio_tasa_pp").reset_index()
    qt.columns = ["grupo_geo2017", "anio", "cambio_tasa_pp"]
    qt["cambio_tasa_pp"] = qt.cambio_tasa_pp.round(2)
    por_anio = qt.groupby("anio").size().to_dict()
    res.prueba("P2-08b", f"Cambios de tendencia > {UMBRAL_QUIEBRE_TENDENCIA} pp en la tasa anual por grupo (empalme de "
               "ediciones INEI: 2018-2020 = Lib1715, 2021+ = ediciones posteriores; las variaciones 2020→2021 se "
               "rotulan)", len(qt) == 0, {"grupos_por_anio": {int(k): int(v) for k, v in por_anio.items()}},
               bloqueante=False)
    res.revision["quiebres_tendencia_poblacion"] = qt
    cods = {m: set(fact.loc[(fact.geografia_base == "GEO2017") & (fact.metodo == m) & (fact.nivel == "distrito"),
                            "ubigeo_inei"]) for m in ("oficial", "prorrateo_propio", "censado")}
    res.prueba("P2-18", "GEO2017: los mismos códigos (grupos comparables) en oficial, prorrateo y censo (PO-06)",
               cods["oficial"] == cods["prorrateo_propio"] == cods["censado"],
               {m: len(c) for m, c in cods.items()})
    clave = ["metodo", "geografia_base", "ubigeo_inei", "anio", "edad_min", "edad_max", "sexo"]
    cruce = fact.groupby(clave, observed=True).vintage.nunique()
    res.prueba("P2-09", "Ninguna cifra (territorio, año, edad, sexo) existe en dos vintages: cada serie usa una sola edición",
               int((cruce > 1).sum()) == 0, {"celdas_con_dos_vintages": int((cruce > 1).sum()),
                                             "vintages": sorted(fact.vintage.astype(str).unique())})
    # Niveles: el ubigeo 000000 es nacional (PO-01) y hay exactamente 25 departamentos por serie
    dep_cnt = (fact[fact.nivel == "departamento"].groupby(["vintage", "metodo", "anio"], observed=True)
               .ubigeo_inei.nunique())
    nac_mal = int(((fact.ubigeo_inei == L.UBIGEO_NACIONAL) & (fact.nivel != "nacional")).sum())
    res.prueba("P2-13", "Niveles: 000000 = nacional y 25 departamentos en cada serie (vintage, método, año)",
               nac_mal == 0 and (dep_cnt == 25).all(),
               {"filas_000000_mal_etiquetadas": nac_mal, "series_con_otro_numero": dep_cnt[dep_cnt != 25].to_dict()})
    grupos = poblacion_grupos_meses(fact)
    pruebas_grupos(res, grupos)
    puente = puente_geo2017(dist, grupo, base2017)
    pw = puente.groupby("grupo_comparable_geo2017").peso_pob_2018.sum()
    res.prueba("P2-17", "puente_geo2017: 1 874 distritos de 2017 y pesos que suman 1 en cada grupo",
               len(puente) == T.DISTRITOS_GEO2017 and ((pw - 1).abs() < 1e-9).all(),
               {"filas": len(puente), "max_desvio": float((pw - 1).abs().max())})
    # PO-09: los distritos nuevos solo tienen valores desde su primer año con dato (anio_datos_desde, TE-02)
    desde = duckdb.sql(f"""SELECT ubigeo_inei, min(anio_datos_desde) AS a FROM '{i_dim.ruta}'
                           WHERE nivel = 'distrito' AND origen = 'escision' GROUP BY 1""").df()
    nuevos = dict(zip(desde.ubigeo_inei, desde.a.astype(int)))
    antes = fact[(fact.ubigeo_inei.isin(nuevos)) & (fact.anio < fact.ubigeo_inei.map(nuevos))]
    res.prueba("P2-10", "Ningún valor para distritos nuevos antes de su primer año de pertenencia (anio_datos_desde)",
               antes.empty, len(antes))

    # ---------------- controles contra el archivo propio (hoja 2)
    hoja2 = pd.read_excel(i_sem.ruta, sheet_name="2. Población-Pobreza-IDH", header=None, dtype=object)
    o = next(j for j, v in enumerate(hoja2.iloc[3].tolist()) if str(v).strip().upper() == "UBIGEO")
    h2 = pd.DataFrame({"ubigeo": hoja2.iloc[6:, o].astype(str), "p2020": pd.to_numeric(hoja2.iloc[6:, o + 2], errors="coerce"),
                       "p2019": pd.to_numeric(hoja2.iloc[6:, o + 3], errors="coerce"),
                       "p2018": pd.to_numeric(hoja2.iloc[6:, o + 4], errors="coerce"),
                       "pob2017": pd.to_numeric(hoja2.iloc[6:, o + 5], errors="coerce")})
    h2 = h2[h2.ubigeo.fillna("").str.fullmatch(r"\d{6}")]
    h2 = h2[(h2.ubigeo.map(L.nivel_de) == "distrito") & (h2.ubigeo != "159999")]
    cmp = h2.merge(dist[["ubigeo", "p2018", "p2019", "p2020"]], on="ubigeo", suffixes=("_propio", ""))
    difs = {a: int((cmp[f"p{a}_propio"] != cmp[f"p{a}"]).sum()) for a in (2018, 2019, 2020)}
    afectados_2020 = sorted(set(cmp.loc[cmp.p2020_propio != cmp.p2020, "ubigeo"]))
    res.prueba("P2-11", "Control: proyección 2018-2019 igual a la del archivo propio (Lib1715) en los 1 874 distritos",
               difs[2018] == 0 and difs[2019] == 0, {"distintos": difs, "2020_distintos": afectados_2020[:10]}, bloqueante=False)
    c17 = censo.groupby("ubigeo").casos.sum().rename("censada")
    ratio = h2.set_index("ubigeo").pob2017.div(c17).dropna()
    res.prueba("P2-12", "Control: población 2017 del archivo propio (censada + omisión) / censada REDATAM entre 1,00 y 1,30",
               ratio.between(1.0, 1.30).mean() >= 0.99,
               {"mediana": round(float(ratio.median()), 4), "fuera_de_rango": int((~ratio.between(1.0, 1.30)).sum())},
               bloqueante=False)
    res.revision["control_censo_propio"] = ratio.rename("ratio").reset_index().rename(columns={"index": "ubigeo"})
    res.tablas = {"fact_poblacion": fact, "fact_poblacion_grupo": grupos, "puente_geo2017": puente}
    return res


CLAVE_GRUPO = ["fuente_id", "vintage", "metodo", "geografia_base", "ubigeo_inei", "nivel", "anio", "fecha_referencia", "sexo"]


def poblacion_grupos_meses(fact: pd.DataFrame) -> pd.DataFrame:
    """Población por grupos de edad en meses, derivada de las edades simples 0-4 (tabla aparte: no se mezcla con
    fact_poblacion para que ninguna suma por edades cuente la edad 0 dos veces)."""
    e = fact[(fact.edad_min == fact.edad_max) & (fact.edad_min <= 4)].copy()
    for c in CLAVE_GRUPO:
        e[c] = e[c].astype(str)
    # ambos sexos donde la fuente viene por sexo (censo, prorrateo)
    por_sexo = e[e.sexo.isin(["M", "F"])]
    tot = por_sexo.groupby(CLAVE_GRUPO[:-1] + ["edad_min"], as_index=False, sort=False).valor.sum()
    tot["sexo"] = "T"
    ya_t = e[e.sexo == "T"][CLAVE_GRUPO[:-1]].drop_duplicates()
    tot = tot.merge(ya_t, how="left", indicator=True)
    tot = tot[tot._merge == "left_only"].drop(columns="_merge")
    e = pd.concat([e[CLAVE_GRUPO + ["edad_min", "valor"]], tot[CLAVE_GRUPO + ["edad_min", "valor"]]], ignore_index=True)
    w = e.pivot_table(index=CLAVE_GRUPO, columns="edad_min", values="valor", aggfunc="sum")
    # el censo no guarda las celdas en cero: una edad ausente vale 0 (no elimina el grupo)
    es_censo = w.index.get_level_values("metodo") == "censado"
    w.loc[es_censo] = w.loc[es_censo].fillna(0.0)
    w = w.dropna(subset=[0, 1, 2])
    salida = []
    for gid, (mmin, mmax, pesos, deriv) in GRUPOS_MESES.items():
        sub = w.dropna(subset=list(pesos))
        v = sum(sub[a] * p for a, p in pesos.items())
        d = sub.index.to_frame(index=False)
        d["grupo_id"] = gid
        d["meses_min"], d["meses_max"] = mmin, mmax
        d["valor"] = v.round(3).to_numpy()
        d["derivacion"] = deriv
        d["supuesto"] = SUPUESTO_UNIFORME if deriv == "uniforme_edad0" else None
        d["p0"], d["p1"], d["p2"] = sub[0].to_numpy(), sub[1].to_numpy(), sub[2].to_numpy()
        salida.append(d)
    g = pd.concat(salida, ignore_index=True)
    g["anio"] = g.anio.astype(int)
    g["version_tabla"] = VERSION_TABLA
    return g


def pruebas_grupos(res: Resultado, g: pd.DataFrame) -> None:
    s = g[g.grupo_id == "6-35m"]
    fuera = s[(s.valor < s.p1 + s.p2 - 1e-6) | (s.valor > s.p0 + s.p1 + s.p2 + 1e-6)]
    res.prueba("P2-14", "6-35 meses entre P1+P2 y P0+P1+P2 (cota) en cada territorio, año y sexo", fuera.empty, len(fuera))
    pro = s[(s.metodo == "prorrateo_propio") & s.geografia_base.str.startswith("vigente_") & (s.sexo == "T")]
    b25 = s[(s.vintage == V_B25) & (s.nivel == "departamento") & (s.sexo == "T")].set_index(["ubigeo_inei", "anio"]).valor
    sd = pro.assign(dep=pro.ubigeo_inei.str[:2] + "0000").groupby(["dep", "anio"]).valor.sum()
    sd.index.names = ["ubigeo_inei", "anio"]
    rel = ((sd - b25.reindex(sd.index)).abs() / b25.reindex(sd.index)).dropna()
    res.prueba("P2-15", "6-35 meses: Σ distritos (prorrateo) = departamento (Boletín 25), error ≤ 0,001",
               len(rel) == 25 * len(ANIOS) and rel.max() <= TOL_IPF, {"comparados": len(rel), "max_error": float(rel.max())})
    cob = g[(g.metodo == "prorrateo_propio") & (g.sexo == "T")].groupby(["geografia_base", "ubigeo_inei", "anio"]).grupo_id.nunique()
    res.prueba("P2-16", "Cada distrito-año del prorrateo tiene los 4 grupos en meses", (cob == len(GRUPOS_MESES)).all(),
               int((cob != len(GRUPOS_MESES)).sum()))


def puente_geo2017(dist: pd.DataFrame, grupo: dict, base2017: set) -> pd.DataFrame:
    """Pesos de población 2018 de cada distrito de 2017 dentro de su grupo comparable (TE-07): para cruzar fuentes
    en geografía 2017 (Mapa de Pobreza 2018) con los grupos que juntan varios distritos de 2017."""
    d = dist[dist.ubigeo.isin(base2017)][["ubigeo", "p2018"]].rename(columns={"ubigeo": "ubigeo_2017",
                                                                              "p2018": "poblacion_2018"})
    d["grupo_comparable_geo2017"] = d.ubigeo_2017.map(lambda u: grupo.get(u, u))
    tot = d.groupby("grupo_comparable_geo2017").poblacion_2018.transform("sum")
    d["peso_pob_2018"] = d.poblacion_2018 / tot
    d["n_miembros_2017"] = d.groupby("grupo_comparable_geo2017").ubigeo_2017.transform("count")
    d["fuente_peso"] = V_DIST + " (población 2018)"
    d["version_tabla"] = VERSION_TABLA
    return d[["grupo_comparable_geo2017", "ubigeo_2017", "n_miembros_2017", "poblacion_2018", "peso_pob_2018",
              "fuente_peso", "version_tabla"]]
