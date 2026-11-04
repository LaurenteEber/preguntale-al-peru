"""Sprint S1 — Territorio: dim_ubigeo_historico, rel_ubigeo_origen, dim_ambito, puente_ubigeo, dim_dominio.

Especificación: reglas/especificaciones_capa0.md y reglas R-TERRITORIO-01..07.
Insumos: crudos registrados (última captura) + datos curados versionados en curados/capa0/.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from difflib import SequenceMatcher

import pandas as pd
import yaml

from ..config import Rutas
from ..util import hoy as hoy_lima
from ..errores import PapError
from . import insumos
from . import lectores as L

VERSION_TABLA = "1.3.0"  # 1.3.0 (2/11/2026): nombre_mostrado con ortografía corregida (nombres_mostrados.yaml, T-02). # 1.2.0 (9/10/2026): dim_dominio con tipo, metodo, identificable_microdatos (Lima en tres ámbitos)
INICIO_GEO2017 = "2017-10-22"
# Departamentos y nacional existen con su código actual desde antes de la serie del Boletín 25 (1995); se usan para
# resolver series departamentales de encuestas desde 2015 (SP-01). Distritos y provincias empiezan en GEO2017.
INICIO_DEPARTAMENTOS = "1995-01-01"
DISTRITOS_GEO2017 = 1874
ANIOS_PROYECCION = range(2018, 2027)
CODIGOS_NO_DISTRITO = {"150144": "centro poblado Santa María de Huachipa (Lurigancho), no es distrito"}
CODIGOS_ANTIGUOS = {"160109": "160801", "160114": "160803"}  # Putumayo y Teniente Manuel Clavero (antes de 2014)
# GA-09 (ronda 3): 160109 no equivale a un solo distrito. La Ley 30186 (2014) escindió el antiguo Putumayo en 160801,
# 160802 y 160804; 160114 sí pasó entero a 160803. Para ubicar datos (RENIPRESS, inversiones), un código escindido no
# se traduce por alias: va a la tabla curada o a la provincia que contiene a todos sus sucesores. CODIGOS_ANTIGUOS se
# conserva para el territorio (descartar el código antiguo del puente RENIEC y la prueba T-14).
CODIGOS_ESCINDIDOS = {"160109": "160800"}


def sim(a: str, b: str) -> float:
    return round(SequenceMatcher(None, L.normalizar(a), L.normalizar(b)).ratio(), 4)


def _dia_siguiente(iso: str) -> str:
    return (date.fromisoformat(iso) + timedelta(days=1)).isoformat()


def _dia_anterior(iso: str) -> str:
    return (date.fromisoformat(iso) - timedelta(days=1)).isoformat()


def vigentes_en_anio(df: pd.DataFrame, anio: int, nivel: str = "distrito") -> pd.DataFrame:
    """Versiones a las que pertenece un dato ANUAL del año dado (TE-02). Se decide por los años con dato del INEI:
    un distrito nuevo (y la versión recortada de su madre) cuenta desde el primer año en que el INEI le asigna
    población; si el INEI aún no lo tiene, desde el año siguiente al último de la proyección. Para datos fechados
    (eventos) se usa la fecha exacta con vigente_desde/vigente_hasta."""
    v = df[(df.nivel == nivel) & (df.anio_datos_desde <= anio)
           & (df.anio_datos_hasta.isna() | (df.anio_datos_hasta >= anio))]
    return v


def leer_yaml(rutas: Rutas, nombre: str):
    ruta = rutas.raiz / "curados" / "capa0" / nombre
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class Resultado:
    tablas: dict[str, pd.DataFrame] = field(default_factory=dict)
    pruebas: list[dict] = field(default_factory=list)
    revision: dict[str, pd.DataFrame] = field(default_factory=dict)
    insumos: list = field(default_factory=list)

    def prueba(self, id_: str, descripcion: str, ok: bool, detalle=None, bloqueante: bool = True):
        self.pruebas.append({"id": id_, "descripcion": descripcion, "ok": bool(ok),
                             "bloqueante": bloqueante, "detalle": detalle})

    @property
    def ok(self) -> bool:
        return all(p["ok"] for p in self.pruebas if p["bloqueante"])


# ======================================================================= grupos comparables

def grupos_comparables(base2017: set[str], altas: list[dict], ajustes: list[dict]) -> dict[str, str]:
    """Unión de conjuntos: cada hijo se une a sus orígenes; con varios orígenes, todos al mismo grupo."""
    padre: dict[str, str] = {}

    def raiz(x):
        padre.setdefault(x, x)
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    def unir(a, b):
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            padre[max(ra, rb)] = min(ra, rb)

    for a in altas:
        for o in a["origenes"]:
            unir(a["ubigeo"], o["ubigeo"])
    for aj in ajustes:
        if aj.get("fusionar_en_grupo"):
            for u in aj["ubigeos"][1:]:
                unir(aj["ubigeos"][0], u)
    conjuntos: dict[str, list[str]] = {}
    for u in list(padre):
        conjuntos.setdefault(raiz(u), []).append(u)
    grupo = {u: u for u in base2017}
    for miembros in conjuntos.values():
        de2017 = sorted(m for m in miembros if m in base2017)
        if not de2017:
            raise PapError(f"Grupo sin distrito de 2017: {miembros}")
        gid = de2017[0] if len(de2017) == 1 else "G-" + de2017[0]
        for m in miembros:
            grupo[m] = gid
    return grupo


# ======================================================================= construcción

def construir(rutas: Rutas) -> Resultado:
    res = Resultado()
    semilla, i_sem = L.semilla_propio(rutas)
    proy, notas_proy, i_proy = L.proyeccion(rutas, "INEI-PROYECCIONES-POBLACION-DISTRITAL")
    anexo, _, i_anexo = L.proyeccion(rutas, "INEI-PROYECCIONES-DISTRITAL-2018-2022", r"anexo")
    pnda, i_pnda = L.pnda(rutas)
    gh, i_gh = L.github(rutas)
    dire, i_dir = L.directorio(rutas)
    ren, i_ren = L.reniec(rutas)
    res.insumos = [i for i in (i_sem, i_proy, i_anexo, i_pnda, i_gh, i_dir, i_ren) if i is not None]
    res.insumos += [insumos.curado(rutas, n) for n in ("altas_post2017.yaml", "ajustes_limites.yaml",
                                                         "ambitos.yaml", "dominios.yaml", "nombres_mostrados.yaml")]
    altas = leer_yaml(rutas, "altas_post2017.yaml")
    # Ortografía del nombre mostrado (T-02): tildes y ñ con evidencia oficial; nunca cambia el nombre legal.
    orto = {c["ubigeo"]: c for c in leer_yaml(rutas, "nombres_mostrados.yaml")["correcciones"]}
    orto_sin_aplicar = dict(orto)
    ajustes = leer_yaml(rutas, "ajustes_limites.yaml")
    alta_por = {a["ubigeo"]: a for a in altas}

    # ---------------- base GEO2017 = semilla (sin 000000 ni 159999)
    sem = semilla[(semilla.ubigeo != "000000") & (semilla.ubigeo != "159999")].copy()
    sem["nivel"] = sem.ubigeo.map(L.nivel_de)
    base2017 = set(sem[sem.nivel == "distrito"].ubigeo)
    res.prueba("T-01", f"La base GEO2017 tiene {DISTRITOS_GEO2017} distritos", len(base2017) == DISTRITOS_GEO2017, len(base2017))

    proy_u = proy[proy.ubigeo != "000000"].copy()
    vig_proy = set(proy_u[proy_u.nivel == "distrito"].ubigeo)
    # Altas posteriores al corte de la proyección (p. ej. Sangani, 2026): aún sin dato INEI
    altas_post = {u for u, a in alta_por.items() if u not in vig_proy}
    altas_proy = set(alta_por) - altas_post
    mal_post = sorted(u for u in altas_post if alta_por[u]["fecha_publicacion"] <= (i_proy.issued or ""))
    res.prueba("T-02", "Proyección 2018-2026 = base GEO2017 + altas documentadas anteriores a su corte (por código)",
               vig_proy == base2017 | altas_proy and not mal_post,
               {"sobran": sorted(vig_proy - base2017 - altas_proy), "faltan": sorted((base2017 | altas_proy) - vig_proy),
                "altas_posteriores_al_corte": sorted(altas_post), "altas_anteriores_al_corte_sin_dato": mal_post})
    res.prueba("T-03", "Provincias y departamentos iguales en la semilla y en la proyección",
               set(sem[sem.nivel != "distrito"].ubigeo) == set(proy_u[proy_u.nivel != "distrito"].ubigeo))
    cruces = {
        "PNDA 2022 (1 891)": set(pnda.ubigeo),
        "Directorio 2025": set(dire[dire.ubigeo.map(L.nivel_de) == "distrito"].ubigeo),
        "Boletín 27 (1 890)": set(anexo[anexo.nivel == "distrito"].ubigeo),
    }
    esperado_falta = {"PNDA 2022 (1 891)": {"160405"}, "Directorio 2025": {"160405"},
                      "Boletín 27 (1 890)": {"130112", "160405"}}
    for k, s in cruces.items():
        res.prueba("T-04", f"{k}: difiere de la proyección solo en los distritos creados después de su corte",
                   (vig_proy - s) == esperado_falta[k] and not (s - vig_proy),
                   {"faltan": sorted(vig_proy - s), "sobran": sorted(s - vig_proy)})

    # ---------------- nombres
    nom_pnda = dict(zip(pnda.ubigeo, pnda.nombre))
    prov_pnda = {u[:4] + "00": n for u, n in zip(pnda.ubigeo, pnda.provincia)}
    dep_pnda = {u[:2] + "0000": n for u, n in zip(pnda.ubigeo, pnda.departamento)}
    nom_proy = dict(zip(proy_u.ubigeo, proy_u.nombre))
    nom_dir = dict(zip(dire.ubigeo, dire.nombre))
    nom_sem = dict(zip(sem.ubigeo, sem.nombre_mostrado))
    nom_gh = {r.inei: r.distrito for r in gh.itertuples() if r.inei}
    reg_nat = dict(zip(pnda.ubigeo, pnda.region_natural))
    dir_por = dire.set_index("ubigeo").to_dict("index")
    sem_por = sem.set_index("ubigeo").to_dict("index")

    unidades = sorted(set(proy_u.ubigeo) | altas_post)
    grupo = grupos_comparables(base2017, altas, ajustes)

    filas = []
    for u in unidades:
        nivel = L.nivel_de(u)
        alta = alta_por.get(u)
        oficial = (nom_pnda.get(u) or prov_pnda.get(u) or dep_pnda.get(u)
                   or (L.normalizar(nom_proy[u]) if u in nom_proy else L.normalizar(alta["nombre"])))
        # Nombre mostrado: Directorio 2025 (decisión del dueño); si no figura, ley de creación o archivo propio.
        if u in nom_dir:
            mostrado, fuente_mostrado = nom_dir[u], "INEI, Directorio Nacional de Municipalidades 2025"
        elif alta:
            mostrado, fuente_mostrado = alta["nombre"], f"Ley N.º {alta['ley']}"
        else:
            mostrado, fuente_mostrado = nom_sem.get(u), "Archivo propio (Estadísticas sociales 2020)"
        c = orto.get(u)
        if c and c["nombre_fuente"] == mostrado:
            orto_sin_aplicar.pop(u, None)
            mostrado = c["nombre_mostrado"]
            fuente_mostrado = f"{fuente_mostrado}; ortografía corregida ({c['motivo']}; evidencia en nombres_mostrados.yaml)"
        nombre = mostrado
        variantes = {nom_pnda.get(u), nom_proy.get(u), nom_dir.get(u), nom_sem.get(u), nom_gh.get(u),
                     alta["nombre"] if alta else None, (c or {}).get("alterno")}
        alternos = sorted(v for v in variantes if v and v != nombre)
        d, s = dir_por.get(u, {}), sem_por.get(u, {})
        fuentes = ["INEI-PROYECCIONES-POBLACION-DISTRITAL"]
        if u in nom_pnda:
            fuentes.append("INEI-PNDA-UBIGEOS")
        if u in nom_dir:
            fuentes.append("INEI-DIRECTORIO-MUNICIPALIDADES")
        if u in sem_por:
            fuentes.append("PROPIO-ESTADISTICAS-SOCIALES-2020")
        comun = {
            "ubigeo_inei": u, "nivel": nivel,
            "ubigeo_padre": (L.UBIGEO_NACIONAL if nivel == "departamento" else
                             u[:2] + "0000" if nivel == "provincia" else u[:4] + "00"),
            "nombre": nombre, "nombre_normalizado": L.normalizar(nombre), "nombres_alternos": alternos,
            "nombre_oficial_inei": oficial, "nombre_mostrado": mostrado, "fuente_nombre_mostrado": fuente_mostrado,
            "grupo_comparable_geo2017": grupo.get(u, u) if nivel == "distrito" else u,
            "region_natural_ref": reg_nat.get(u), "pct_poblacion_urbana_cpv2017": None,
            "tipologia_pcm": s.get("tipologia_pcm"), "anio_primeros_datos_registros": None,
            "version_tabla": VERSION_TABLA,
        }
        if alta:
            fecha_alta = ("2022-04-15" if u in cruces["Boletín 27 (1 890)"]
                          else "2025-04-29" if u in cruces["Directorio 2025"]
                          else i_proy.issued if u in vig_proy else None)
            if alta.get("codigo_inei_confirmado") is False:
                estado = "codigo_provisional_dueno"
            else:
                estado = "verificado_ley" if alta.get("revisado_dueno") else "verificado_inei"
            filas.append({**comun, "vigente_desde": _dia_siguiente(alta["fecha_publicacion"]), "vigente_hasta": None,
                          "origen": "escision", "territorio_modificado": False,
                          "norma_legal": f"Ley N.º {alta['ley']}", "fecha_publicacion_norma": alta["fecha_publicacion"],
                          "url_norma": alta["url_norma"], "fecha_alta_inei": fecha_alta,
                          "capital_legal": alta["capital"], "lat_capital": d.get("lat"), "lon_capital": d.get("lon"),
                          "altitud_capital": d.get("altitud"),
                          "fuente": fuentes + ["ley"],
                          "estado_verificacion": estado})
        else:
            antiguo = nivel == "departamento"
            filas.append({**comun, "vigente_desde": INICIO_DEPARTAMENTOS if antiguo else INICIO_GEO2017,
                          "vigente_hasta": None,
                          "origen": "preexistente_anterior" if antiguo else "preexistente_2017",
                          "territorio_modificado": False,
                          "norma_legal": None, "fecha_publicacion_norma": None, "url_norma": None,
                          "fecha_alta_inei": None,
                          "capital_legal": s.get("capital_legal"), "lat_capital": s.get("lat_capital"),
                          "lon_capital": s.get("lon_capital"), "altitud_capital": s.get("altitud_capital"),
                          "fuente": fuentes, "estado_verificacion": "verificado_inei"})

    # ---------------- versiones del distrito madre (territorio modificado por una escisión)
    eventos: dict[tuple[str, str], list[dict]] = {}
    for a in altas:
        desde = _dia_siguiente(a["fecha_publicacion"])
        for o in a["origenes"]:
            eventos.setdefault((o["ubigeo"], desde), []).append(a)
    df = pd.DataFrame(filas)
    nuevas = []
    for (madre, desde), causas in sorted(eventos.items()):
        idx = df.index[(df.ubigeo_inei == madre) & df.vigente_hasta.isna()]
        if len(idx) != 1:
            raise PapError(f"Distrito madre {madre} sin versión vigente única")
        actual = df.loc[idx[0]].to_dict()
        df.loc[idx[0], "vigente_hasta"] = _dia_anterior(desde)
        leyes = sorted({c["ley"] for c in causas})
        nueva = {**actual, "vigente_desde": desde, "vigente_hasta": None, "territorio_modificado": True,
                 "norma_legal": "; ".join(f"Ley N.º {l}" for l in leyes),
                 "fecha_publicacion_norma": causas[0]["fecha_publicacion"],
                 "url_norma": "; ".join(sorted({c["url_norma"] for c in causas})),
                 "fuente": sorted(set(actual["fuente"]) | {"ley"})}
        df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
        nuevas.append((madre, desde))
    nacional = {**{c: None for c in df.columns}, "ubigeo_inei": L.UBIGEO_NACIONAL, "nivel": "nacional",
                "nombre": "Perú", "nombre_normalizado": "PERU", "nombres_alternos": [], "nombre_oficial_inei": "PERU",
                "nombre_mostrado": "Perú", "fuente_nombre_mostrado": "INEI", "grupo_comparable_geo2017": L.UBIGEO_NACIONAL,
                "version_tabla": VERSION_TABLA, "vigente_desde": INICIO_DEPARTAMENTOS, "origen": "preexistente_anterior",
                "territorio_modificado": False, "fuente": ["INEI-PROYECCIONES-POBLACION-DISTRITAL"],
                "estado_verificacion": "verificado_inei"}
    df = pd.concat([df, pd.DataFrame([nacional])], ignore_index=True)
    df = df.sort_values(["ubigeo_inei", "vigente_desde"]).reset_index(drop=True)
    df.insert(0, "id_version", range(1, len(df) + 1))
    anios_con_dato(df, proy_u, alta_por, eventos)

    # ---------------- puente INEI–RENIEC
    puente, excepciones = construir_puente(df, gh, ren, alta_por, res)
    mapa_reniec = dict(zip(puente.ubigeo_inei, puente.ubigeo_reniec))
    df.insert(df.columns.get_loc("ubigeo_inei") + 1, "ubigeo_reniec", df.ubigeo_inei.map(mapa_reniec))
    # TE-12: estado que consultan R-TERRITORIO-01/09 (vigente, pendiente = código aún no publicado por el INEI,
    # historica = versión anterior de un distrito recortado)
    df["estado_ubigeo"] = "vigente"
    df.loc[df.vigente_hasta.notna(), "estado_ubigeo"] = "historica"
    df.loc[df.estado_verificacion == "codigo_provisional_dueno", "estado_ubigeo"] = "pendiente"

    # ---------------- pruebas de la tabla
    hoy = hoy_lima()
    vigentes = df[(df.nivel == "distrito") & (df.vigente_desde <= hoy) & (df.vigente_hasta.isna() | (df.vigente_hasta >= hoy))]
    esperados = DISTRITOS_GEO2017 + sum(1 for a in altas if _dia_siguiente(a["fecha_publicacion"]) <= hoy)
    res.prueba("T-19", "Ortografía del nombre mostrado: cada corrección de nombres_mostrados.yaml coincide con su fuente "
               "y se aplicó (si la fuente cambió, revisar la fila)", not orto_sin_aplicar, sorted(orto_sin_aplicar))
    res.prueba("T-20", "Ningún nombre mostrado con tilde grave, abreviatura «Prov.» ni «Del» en mayúscula dentro del nombre",
               not df.nombre_mostrado.fillna("").str.contains(r"[àèìòùÀÈÌÒÙ]|Prov\.| Del ", regex=True).any(),
               sorted(df[df.nombre_mostrado.fillna("").str.contains(r"[àèìòùÀÈÌÒÙ]|Prov\.| Del ", regex=True)]
                      .nombre_mostrado.unique())[:10])
    res.prueba("T-10", f"Distritos vigentes hoy = GEO2017 ({DISTRITOS_GEO2017}) + altas con ley vigente ({esperados})",
               len(vigentes) == esperados, {"vigentes": len(vigentes), "esperados": esperados})
    fechas = sorted(set(df.vigente_desde) | {hoy})
    dobles = []
    for f in fechas:
        v = df[(df.vigente_desde <= f) & (df.vigente_hasta.isna() | (df.vigente_hasta >= f))]
        dobles += [(f, u) for u in v.ubigeo_inei[v.ubigeo_inei.duplicated()]]
    res.prueba("T-11", "Un solo registro vigente por ubigeo en cualquier fecha", not dobles, dobles[:10])
    activos = set(vigentes.ubigeo_inei) | set(df[df.nivel != "distrito"].ubigeo_inei)
    sin_padre = df[df.ubigeo_padre.notna() & ~df.ubigeo_padre.isin(activos)].ubigeo_inei.tolist()
    res.prueba("T-12", "Jerarquía: todo padre existe y está vigente; prefijo del distrito = provincia", not sin_padre and
               all(r.ubigeo_padre[:4] == r.ubigeo_inei[:4] for r in df[df.nivel == "distrito"].itertuples()), sin_padre)
    gr = vigentes.grupo_comparable_geo2017
    grupos_validos = all(g in base2017 or (g.startswith("G-") and g[2:] in base2017) for g in gr)
    res.prueba("T-13", "Todo distrito vigente tiene grupo comparable y todo grupo contiene un distrito de 2017",
               gr.notna().all() and grupos_validos)
    res.prueba("T-14", "Ningún código es un centro poblado ni un código antiguo",
               not (set(df.ubigeo_inei) & (set(CODIGOS_NO_DISTRITO) | set(CODIGOS_ANTIGUOS))))
    res.prueba("T-15", "Toda alta tiene ley, fecha de publicación y origen", all(
        a.get("ley") and a.get("fecha_publicacion") and a.get("origenes") for a in altas), len(altas))
    for anio in range(2018, 2027):
        col = f"p{anio}"
        dist = proy_u[proy_u.nivel == "distrito"]
        sum_dep = dist.groupby(dist.ubigeo.str[:2])[col].sum()
        dep = proy_u[proy_u.nivel == "departamento"].set_index(proy_u[proy_u.nivel == "departamento"].ubigeo.str[:2])[col]
        sum_prov = dist.groupby(dist.ubigeo.str[:4])[col].sum()
        prov = proy_u[proy_u.nivel == "provincia"].set_index(proy_u[proy_u.nivel == "provincia"].ubigeo.str[:4])[col]
        dif_d = (sum_dep - dep).abs().max()
        dif_p = (sum_prov - prov).abs().max()
        res.prueba("T-16", f"Proyección {anio}: Σ distritos = provincia y = departamento", dif_d == 0 and dif_p == 0,
                   {"max_dif_departamento": int(dif_d), "max_dif_provincia": int(dif_p)}, bloqueante=False)
    # La proyección se resuelve al 100 % contra la tabla vigente en algún momento del año del dato
    # (el INEI asigna población al distrito desde su año de creación: Lambras 2020, Santa Rosa de Loreto 2025).
    no_resueltos, sin_dato = [], []
    for anio in ANIOS_PROYECCION:
        v = set(vigentes_en_anio(df, anio).ubigeo_inei) | set(df[df.nivel != "distrito"].ubigeo_inei)
        con_dato = set(proy_u[proy_u[f"p{anio}"].notna()].ubigeo)
        no_resueltos += [(anio, u) for u in sorted(con_dato - v)]
        sin_dato += [(anio, u) for u in sorted(v - con_dato) if L.nivel_de(u) == "distrito"]
    # Continuidad: la población de cada grupo comparable no debe tener saltos de un año (traspasos no agrupados)
    dist = proy_u[proy_u.nivel == "distrito"].copy()
    dist["grupo"] = dist.ubigeo.map(lambda u: grupo.get(u, u))
    anios_p = [f"p{a}" for a in range(2018, 2027)]
    gser = dist.groupby("grupo")[anios_p].sum(min_count=1)
    quiebres = []
    for g, fila in gser.iterrows():
        v = (fila.pct_change().iloc[1:] * 100).tolist()
        med = float(pd.Series(v).median())
        for i, x in enumerate(v):
            vecinos = [v[j] for j in (i - 1, i + 1) if 0 <= j < len(v)]
            # quiebre = salto aislado de un año (los años vecinos siguen la tendencia), no una tendencia fuerte
            if abs(x - med) > 5 and all(abs(y - med) <= 3 for y in vecinos):
                a = anios_p[i + 1]
                quiebres.append({"grupo": g, "anio": int(a[1:]), "variacion_pct": round(float(x), 1),
                                 "tendencia_pct": round(float(med), 1)})
    res.prueba("T-18", "Población continua por grupo comparable (sin saltos aislados de un año > 5 pp sobre su tendencia)",
               not quiebres, quiebres, bloqueante=False)
    res.revision["quiebres_poblacion"] = pd.DataFrame(quiebres)

    res.prueba("T-17", "Pertenencia anual: cada año, los distritos con dato en la proyección = los de vigentes_en_anio()",
               not no_resueltos and not sin_dato, {"con_dato_sin_version": no_resueltos[:20],
                                                   "version_sin_dato": sin_dato[:20]})

    # ---------------- relaciones, ámbitos, dominios
    rel = pd.DataFrame([{
        "ubigeo_hijo": a["ubigeo"], "ubigeo_origen": o["ubigeo"], "tipo": "escision",
        "es_origen_principal": bool(o.get("principal")), "poblacion_cedida_cpv2017": None,
        "norma_legal": f"Ley N.º {a['ley']}",
        "fuente": (f"Ley N.º {a['ley']}; código provisional asignado por el dueño (el INEI aún no lo publica)"
                   if a.get("codigo_inei_confirmado") is False else "ley + nota INEI (proyección 2018-2026)"),
        "version_tabla": VERSION_TABLA,
    } for a in altas for o in a["origenes"]]).sort_values(["ubigeo_hijo", "ubigeo_origen"])
    ambitos = construir_ambitos(rutas, df, semilla, res)
    dominios = construir_dominios(rutas, df)
    for id_, descripcion, ok, detalle in pruebas_dominios(dominios):
        res.prueba(id_, descripcion, ok, detalle)

    res.tablas = {"dim_ubigeo_historico": df, "rel_ubigeo_origen": rel, "puente_ubigeo": puente,
                  "dim_ambito": ambitos, "dim_dominio": dominios}

    # ---------------- revisión humana
    filas_rev = []
    for a in altas:
        d = dir_por.get(a["ubigeo"], {})
        filas_rev.append({
            "ubigeo": a["ubigeo"], "distrito": a["nombre"],
            "provincia": nom_dir.get(a["ubigeo"][:4] + "00") or nom_proy.get(a["ubigeo"][:4] + "00"),
            "departamento": nom_sem.get(a["ubigeo"][:2] + "0000"),
            "ley": a["ley"], "publicada": a["fecha_publicacion"], "vigente_desde": _dia_siguiente(a["fecha_publicacion"]),
            "capital_segun_ley": a["capital"], "capital_segun_directorio_2025": d.get("capital"),
            "origenes": "; ".join(f"{o['nombre']} ({o['ubigeo']})" + (" [principal]" if o.get("principal") else "") for o in a["origenes"]),
            "grupo_comparable": grupo[a["ubigeo"]], "ubigeo_reniec": mapa_reniec.get(a["ubigeo"]),
            "nota": a.get("nota"), "url_norma": a["url_norma"], "revisado_dueno": a.get("revisado_dueno", False),
        })
    res.revision["distritos_nuevos"] = pd.DataFrame(filas_rev)
    res.revision["puente_excepciones"] = excepciones
    nombres = []
    for r in df[(df.nivel == "distrito") & df.vigente_hasta.isna()].itertuples():
        if r.nombre_mostrado and r.nombre and L.normalizar(r.nombre_mostrado) != L.normalizar(r.nombre):
            nombres.append({"ubigeo": r.ubigeo_inei, "nombre_mostrado (archivo propio)": r.nombre_mostrado,
                            "nombre (Directorio 2025)": r.nombre, "nombre_oficial_inei": r.nombre_oficial_inei,
                            "similitud": sim(r.nombre_mostrado, r.nombre)})
    res.revision["nombres_distintos"] = pd.DataFrame(nombres)
    return res


def anios_con_dato(df: pd.DataFrame, proy_u: pd.DataFrame, alta_por: dict, eventos: dict) -> None:
    """Agrega anio_datos_desde / anio_datos_hasta (pertenencia de los datos anuales, TE-02)."""
    ultimo = max(ANIOS_PROYECCION)
    primer = {}
    for r in proy_u.itertuples():
        anios = [a for a in ANIOS_PROYECCION if pd.notna(getattr(r, f"p{a}"))]
        if anios:
            primer[r.ubigeo] = anios[0]

    def desde_alta(u):
        return primer.get(u) or max(int(_dia_siguiente(alta_por[u]["fecha_publicacion"])[:4]), ultimo + 1)

    df["anio_datos_desde"] = None
    df["anio_datos_hasta"] = None
    for i, r in df.iterrows():
        if r.nivel in ("nacional", "departamento"):
            df.at[i, "anio_datos_desde"] = int(INICIO_DEPARTAMENTOS[:4])
        elif r.nivel == "provincia":
            df.at[i, "anio_datos_desde"] = int(INICIO_GEO2017[:4])
        elif r.ubigeo_inei in alta_por and r.origen == "escision":
            df.at[i, "anio_datos_desde"] = desde_alta(r.ubigeo_inei)
        elif r.territorio_modificado:
            hijos = eventos[(r.ubigeo_inei, r.vigente_desde)]
            df.at[i, "anio_datos_desde"] = min(desde_alta(h["ubigeo"]) for h in hijos)
        else:
            df.at[i, "anio_datos_desde"] = int(INICIO_GEO2017[:4])
    # la versión anterior de cada madre termina el año antes de que empiece la siguiente
    for u, g in df[df.nivel == "distrito"].groupby("ubigeo_inei"):
        idx = g.sort_values("vigente_desde").index.tolist()
        for a, b in zip(idx, idx[1:]):
            df.at[a, "anio_datos_hasta"] = int(df.at[b, "anio_datos_desde"]) - 1
    df["anio_datos_desde"] = df.anio_datos_desde.astype("Int64")
    df["anio_datos_hasta"] = df.anio_datos_hasta.astype("Int64")


def construir_puente(df: pd.DataFrame, gh: pd.DataFrame, ren, alta_por: dict, res: Resultado):
    vig = df[(df.nivel == "distrito") & df.vigente_hasta.isna()].set_index("ubigeo_inei").copy()
    # TE-06: el par INEI–RENIEC rige desde que existe el código, no desde el último recorte del distrito madre
    vig["vigente_desde"] = df[df.nivel == "distrito"].groupby("ubigeo_inei").vigente_desde.min()
    filas, excepciones = [], []
    for r in gh.itertuples():
        if r.inei in CODIGOS_NO_DISTRITO:
            excepciones.append({"ubigeo_inei": r.inei, "ubigeo_reniec": r.reniec, "nombre": r.distrito,
                                "decision": "descartado", "motivo": CODIGOS_NO_DISTRITO[r.inei]})
            continue
        if r.inei in CODIGOS_ANTIGUOS:
            excepciones.append({"ubigeo_inei": r.inei, "ubigeo_reniec": r.reniec, "nombre": r.distrito,
                                "decision": "descartado",
                                "motivo": f"código INEI anterior a la provincia de Putumayo (2014); vigente: {CODIGOS_ANTIGUOS[r.inei]}"})
            continue
        inei, metodo = r.inei, "github_2021"
        if inei is None:
            cand = vig[(vig.nombre_normalizado == L.normalizar(r.distrito)) &
                       (vig.index.str[:2].map(lambda d: True))]
            cand = cand[[L.normalizar(r.provincia) == L.normalizar(df.loc[df.ubigeo_inei == u[:4] + "00", "nombre"].iloc[0]) for u in cand.index]]
            if len(cand) != 1:
                excepciones.append({"ubigeo_inei": None, "ubigeo_reniec": r.reniec, "nombre": r.distrito,
                                    "decision": "sin_par", "motivo": "sin código INEI en GitHub y sin coincidencia única por provincia+nombre"})
                continue
            inei, metodo = cand.index[0], "nombre_exacto"
            excepciones.append({"ubigeo_inei": inei, "ubigeo_reniec": r.reniec, "nombre": r.distrito,
                                "decision": "emparejado_por_nombre", "motivo": "GitHub sin código INEI (Ley 31216); se asigna por provincia + nombre exacto"})
        if inei not in vig.index:
            excepciones.append({"ubigeo_inei": inei, "ubigeo_reniec": r.reniec, "nombre": r.distrito,
                                "decision": "descartado", "motivo": "código INEI no vigente"})
            continue
        filas.append({"ubigeo_inei": inei, "ubigeo_reniec": r.reniec, "nivel": "distrito",
                      "vigente_desde": vig.loc[inei, "vigente_desde"], "vigente_hasta": None,
                      "metodo_emparejamiento": metodo, "nombre_inei": vig.loc[inei, "nombre_oficial_inei"],
                      "nombre_reniec": r.distrito, "sim_nombre": sim(vig.loc[inei, "nombre_oficial_inei"], r.distrito),
                      "fuente": "GITHUB-UBIGEO-PERU-AUMENTADO", "version": VERSION_TABLA})
    puente = pd.DataFrame(filas)
    faltan = sorted(set(vig.index) - set(puente.ubigeo_inei))
    # RENIEC: buscar en el dataset de población identificada (si está registrado)
    if ren is not None and faltan:
        ren_pares = _pares_reniec(ren)
        for u in faltan:
            prov_nom = L.normalizar(df.loc[df.ubigeo_inei == u[:4] + "00", "nombre"].iloc[0])
            nom = vig.loc[u, "nombre_normalizado"]
            cand = ren_pares[(ren_pares.distrito_n == nom) & (ren_pares.provincia_n == prov_nom)]
            if len(cand) == 1:
                rr = cand.iloc[0]
                puente = pd.concat([puente, pd.DataFrame([{
                    "ubigeo_inei": u, "ubigeo_reniec": rr.ubigeo, "nivel": "distrito",
                    "vigente_desde": vig.loc[u, "vigente_desde"], "vigente_hasta": None,
                    "metodo_emparejamiento": "nombre_exacto", "nombre_inei": vig.loc[u, "nombre_oficial_inei"],
                    "nombre_reniec": rr.distrito, "sim_nombre": 1.0, "fuente": "RENIEC-POBLACION-IDENTIFICADA",
                    "version": VERSION_TABLA}])], ignore_index=True)
                excepciones.append({"ubigeo_inei": u, "ubigeo_reniec": rr.ubigeo, "nombre": rr.distrito,
                                    "decision": "emparejado_por_nombre", "motivo": "ausente en GitHub 2021; tomado de RENIEC (provincia + nombre exacto)"})
        faltan = sorted(set(vig.index) - set(puente.ubigeo_inei))
    for u in faltan:
        excepciones.append({"ubigeo_inei": u, "ubigeo_reniec": None, "nombre": vig.loc[u, "nombre"],
                            "decision": "pendiente", "motivo": "sin código RENIEC conocido (distrito posterior al corte de GitHub 2021)"})
    puente = puente.sort_values("ubigeo_inei").reset_index(drop=True)
    exc = pd.DataFrame(excepciones)
    n_vig = len(vig)
    dup_inei = puente.ubigeo_inei[puente.ubigeo_inei.duplicated()].tolist()
    dup_ren = puente.ubigeo_reniec[puente.ubigeo_reniec.duplicated()].tolist()
    res.prueba("P-01", "Puente: biyección (ningún código INEI ni RENIEC repetido)", not dup_inei and not dup_ren,
               {"inei": dup_inei, "reniec": dup_ren})
    pct = float((puente.sim_nombre >= 0.90).mean()) if len(puente) else 0.0
    res.prueba("P-02", "Puente: nombre coincidente (similitud ≥ 0,90) en ≥ 99,5 % de los pares", pct >= 0.995, round(pct, 4))
    res.prueba("P-03", "Puente: 0 códigos INEI no vigentes", puente.ubigeo_inei.isin(vig.index).all())
    cobertura = len(puente) / n_vig
    res.prueba("P-04", "Puente: cobertura = 1 o cada faltante documentado como excepción",
               cobertura == 1 or set(faltan) <= set(exc[exc.decision == "pendiente"].ubigeo_inei),
               {"cobertura": round(cobertura, 5), "pendientes": faltan})
    if ren is not None:
        rp = _pares_reniec(ren).drop_duplicates("ubigeo").set_index("ubigeo")
        cruzan = puente[puente.ubigeo_reniec.isin(rp.index)]
        malos = [(r.ubigeo_inei, r.ubigeo_reniec, r.nombre_inei, rp.loc[r.ubigeo_reniec, "distrito"])
                 for r in cruzan.itertuples() if sim(r.nombre_inei, rp.loc[r.ubigeo_reniec, "distrito"]) < 0.90]
        res.prueba("P-05", "Puente validado contra el listado de RENIEC (código y nombre)",
                   len(cruzan) / len(puente) >= 0.995 and len(malos) <= 0.005 * len(puente),
                   {"pares_en_reniec": len(cruzan), "pares": len(puente), "nombre_distinto": malos[:15]})
        propio = rp[rp.ubigeo_inei.str.fullmatch(r"\d{6}")]
        cruz = puente.merge(propio[["ubigeo_inei"]].reset_index().rename(columns={"ubigeo": "ubigeo_reniec_dataset"}),
                            on="ubigeo_inei", how="inner")
        difieren = cruz[cruz.ubigeo_reniec != cruz.ubigeo_reniec_dataset]
        res.prueba("P-06", "Puente = equivalencia INEI–RENIEC que publica la propia RENIEC en su dataset",
                   difieren.empty, {"comparados": len(cruz),
                                    "difieren": difieren[["ubigeo_inei", "ubigeo_reniec", "ubigeo_reniec_dataset"]].values.tolist()[:20]})
    return puente, exc


def _pares_reniec(ren: pd.DataFrame) -> pd.DataFrame:
    p = ren.rename(columns={"ubigeo_reniec": "ubigeo"}).copy()
    p["distrito_n"] = p.distrito.map(L.normalizar)
    p["provincia_n"] = p.provincia.map(L.normalizar)
    return p


# ======================================================================= ámbitos y dominios

def _expandir(composicion: list[str], distritos: list[str]) -> list[str]:
    incluye = [c for c in composicion if not c.startswith("-")]
    excluye = [c[1:] for c in composicion if c.startswith("-")]
    return sorted(u for u in distritos if any(u.startswith(i) for i in incluye)
                  and not any(u.startswith(e) for e in excluye))


def _vigentes_en(df: pd.DataFrame, fecha: str) -> list[str]:
    v = df[(df.nivel == "distrito") & (df.vigente_desde <= fecha) & (df.vigente_hasta.isna() | (df.vigente_hasta >= fecha))]
    return sorted(v.ubigeo_inei)


def construir_ambitos(rutas: Rutas, df: pd.DataFrame, semilla: pd.DataFrame, res: Resultado) -> pd.DataFrame:
    hoy = hoy_lima()
    vig = _vigentes_en(df, hoy)
    filas = []
    for a in leer_yaml(rutas, "ambitos.yaml"):
        dist = _expandir(a["composicion"], vig)
        filas.append({"ambito_id": a["ambito_id"], "nombre_mostrado": a["nombre_mostrado"],
                      "nombre_largo": a.get("nombre_largo") or a["nombre_mostrado"],
                      "alias": "; ".join(a.get("alias") or []) or None, "contiene": list(a.get("contiene") or []),
                      "composicion": a["composicion"], "distritos_vigentes": dist, "n_distritos": len(dist),
                      "gestion": a.get("gestion"), "fuente_definicion": a["fuente_definicion"],
                      "codigo_en_fuentes": yaml.safe_dump(a.get("codigo_en_fuentes") or {}, allow_unicode=True).strip(),
                      "version_tabla": VERSION_TABLA})
    amb = pd.DataFrame(filas)
    n = dict(zip(amb.ambito_id, amb.n_distritos))
    res.prueba("A-01", "Lima Metropolitana = 43 distritos; Lima Región = 128; Callao = 7",
               n.get("LIMA_METROPOLITANA") == 43 and n.get("LIMA_REGION") == 128 and n.get("CALLAO") == 7, n)
    sup = semilla.set_index("ubigeo").superficie_km2
    lr = _expandir(["15", "-1501"], sorted(semilla[(semilla.ubigeo.map(L.nivel_de) == "distrito")
                                                   & (semilla.ubigeo != "159999")].ubigeo))
    total = round(float(sup.loc[lr].sum()), 2)
    res.prueba("A-02", "Superficie de Lima Región (suma de sus distritos) = fila 159999 del archivo propio",
               abs(total - float(sup.loc["159999"])) < 0.05, {"suma": total, "159999": float(sup.loc["159999"])})
    return amb


AVISO_AMBITO = "ambito_no_dominio"     # R-ENC-08.parametros.avisos
AVISO_ESTRATO = "ambito_por_estrato"   # R-ENC-08.parametros.avisos (ENDES 2015–2017, L2)
TIPOS_DOMINIO = {"dominio_diseno", "ambito_publicado"}
METODOS_DOMINIO = {"ubigeo", "estrato_hv022", "variable_dominio", "variable_area", "variable_departamento", "todos", None}
CAMPOS_REGLA = ("encuesta", "anios", "dominio_id", "nombre_publicado", "nivel", "composicion", "tipo", "metodo",
                "identificable_microdatos", "fuente", "confirmado")


def _validar_regla(regla: dict, fuentes: dict) -> None:
    claves = regla.get("fuente")
    claves = claves if isinstance(claves, list) else [claves]
    errores = []
    falta = [c for c in CAMPOS_REGLA if c not in regla]
    if falta:
        errores.append(f"faltan {falta}")
    if regla.get("tipo") not in TIPOS_DOMINIO:
        errores.append(f"tipo {regla.get('tipo')!r} fuera de {sorted(TIPOS_DOMINIO)}")
    if regla.get("metodo") not in METODOS_DOMINIO:
        errores.append(f"metodo {regla.get('metodo')!r}")
    errores += [f"fuente {c!r} fuera de `fuentes`" for c in claves if c not in fuentes]
    if errores:
        raise PapError(f"dominios.yaml, regla {regla.get('encuesta')} {regla.get('dominio_id')} {regla.get('anios')}: "
                       + "; ".join(errores))


def construir_dominios(rutas: Rutas, df: pd.DataFrame) -> pd.DataFrame:
    cfg = leer_yaml(rutas, "dominios.yaml")
    fuentes = cfg["fuentes"]
    deps = df[df.nivel == "departamento"].drop_duplicates("ubigeo_inei")
    reglas = list(cfg["reglas"])
    copia = cfg.get("copiar_sin_confirmar") or {}
    rotulos = {a["ambito_id"]: a["nombre_mostrado"] for a in leer_yaml(rutas, "ambitos.yaml")}
    filas = []

    def fuente_txt(clave, anio):
        if isinstance(clave, list):
            return " | ".join(fuente_txt(c, anio) for c in clave)
        f = fuentes[clave]
        url = f["url"]
        if "{codigo}" in url:
            cod = f["codigos"].get(anio)
            url = url.replace("{codigo}", str(cod)) if cod else None
        return f"{f['titulo'].replace('<año>', str(anio))} — {url or 'sin URL para este año'} ({f.get('pagina', '')})"

    for regla in reglas:
        _validar_regla(regla, fuentes)
        anios = list(range(regla["anios"][0], regla["anios"][1] + 1))
        if copia and regla["anios"][1] == copia["desde"]:
            anios_extra = copia["hacia"]
        else:
            anios_extra = []
        for anio in anios + anios_extra:
            confirmado = regla["confirmado"] and anio not in anios_extra
            # Antes de 2018 no hay versiones distritales: se usa la lista GEO2017 (composición aproximada, SP-01)
            aproximada = anio < min(ANIOS_PROYECCION)
            vig = (_vigentes_en(df, INICIO_GEO2017) if aproximada
                   else sorted(vigentes_en_anio(df, anio).ubigeo_inei))
            src_anio = min(anio, copia.get("desde", anio)) if anio in anios_extra else anio
            base = {"encuesta_id": regla["encuesta"], "anio": anio, "nivel_definicion": regla["nivel"],
                    "incluye_callao": regla.get("incluye_callao"), "confirmado": confirmado,
                    "fuente_definicion": fuente_txt(regla["fuente"], src_anio),
                    "nota": " ".join(filter(None, [regla.get("nota"),
                                                   None if confirmado or regla["confirmado"] is False
                                                   else "Sin ficha técnica confirmada; copiado del año anterior.",
                                                   "Composición con la lista de distritos GEO2017 (no hay versiones "
                                                   "distritales antes de 2017)." if aproximada else None])) or None,
                    "composicion_aproximada_geo2017": aproximada,
                    "codigo_en_microdatos": yaml.safe_dump(regla["codigo_en_microdatos"], allow_unicode=True,
                                                           default_flow_style=True, width=10**6).strip()
                                            if regla.get("codigo_en_microdatos") else None,
                    "codigo_verificado": bool((regla.get("codigo_en_microdatos") or {}).get("verificado", False)),
                    "tipo": regla["tipo"], "metodo": regla["metodo"],
                    "identificable_microdatos": bool(regla["identificable_microdatos"]),
                    "ambito_id": regla.get("ambito_id"),
                    "rotulo": rotulos.get(regla.get("ambito_id"), regla["nombre_publicado"]),
                    "alias": "; ".join(regla.get("alias") or []) or None,
                    "version_tabla": VERSION_TABLA}
            if regla["composicion"] == "departamentos":
                excluye = set(regla.get("excluye") or [])
                for d in deps.itertuples():
                    dp = d.ubigeo_inei[:2]
                    if dp in excluye:
                        continue
                    extra = (regla.get("por_departamento") or {}).get(dp, {})
                    nota = " ".join(filter(None, [base["nota"], extra.get("nota")])) or None
                    filas.append({**base, **{k: v for k, v in extra.items() if k in ("tipo", "metodo")}, "nota": nota,
                                  "dominio_id": f"departamento_{dp}", "dominio_nombre": d.nombre,
                                  "rotulo": ROTULO_DPTO_15 if dp == "15" else d.nombre, "composicion": [dp],
                                  "reconstruible_con_ubigeo": True, "ubigeos": _expandir([dp], vig)})
            else:
                comp = regla["composicion"]
                filas.append({**base, "dominio_id": regla["dominio_id"], "dominio_nombre": regla["nombre_publicado"],
                              "composicion": comp, "reconstruible_con_ubigeo": comp is not None,
                              "ubigeos": _expandir(comp, vig) if comp is not None else None})
    dom = pd.DataFrame(filas).sort_values(["encuesta_id", "anio", "dominio_id"]).reset_index(drop=True)
    # Avisos de R-ENC-08 (claves exactas de parametros.avisos; el año es la fila, nunca parte de la clave)
    dom["avisos"] = [[k for k, si in ((AVISO_AMBITO, t == "ambito_publicado"), (AVISO_ESTRATO, m == "estrato_hv022")) if si]
                     for t, m in zip(dom.tipo, dom.metodo)]
    dup = dom[dom.duplicated(["encuesta_id", "anio", "dominio_id"], keep=False)]
    if not dup.empty:
        raise PapError(f"dominios.yaml: dominio repetido en una encuesta-año: "
                       f"{dup[['encuesta_id', 'anio', 'dominio_id']].drop_duplicates().values.tolist()[:10]}")
    return dom


ROTULO_DPTO_15 = "departamento de Lima (Lima Metropolitana + Lima Región)"


def pruebas_dominios(dom: pd.DataFrame) -> list[tuple]:
    """D-01…D-06 (Lima en tres ámbitos, 9/10/2026): pruebas de construcción de dim_dominio."""
    out = []
    rec = dom[dom.reconstruible_con_ubigeo].copy()
    rec["clave"] = rec.ubigeos.map(lambda u: tuple(sorted(u)))
    dup = rec[rec.duplicated(["encuesta_id", "anio", "clave"], keep=False)]
    out.append(("D-01", "dim_dominio: ninguna encuesta-año tiene dos dominios con los mismos distritos",
                dup.empty, dup[["encuesta_id", "anio", "dominio_id"]].values.tolist()[:10]))
    cod = dom.codigo_en_microdatos.map(lambda c: yaml.safe_load(c) if isinstance(c, str) and c else {})
    d8 = dom[cod.map(lambda c: c.get("variable") == "dominio" and c.get("valor") == 8)]
    malos = d8[~d8.composicion.map(lambda c: sorted(c) == ["0701", "1501"])
               | (d8.dominio_id != "area_metropolitana_lima_callao") | (d8.encuesta_id != "ENAHO")]
    n_d8 = d8.groupby("anio").size()
    out.append(("D-02", "dim_dominio: el dominio 8 de la ENAHO es solo area_metropolitana_lima_callao = 1501 + 0701, "
                "una vez por año 2015–2025", malos.empty and (n_d8 == 1).all() and set(n_d8.index) == set(range(2015, 2026)),
                {"mal_definidos": malos[["anio", "dominio_id"]].values.tolist()[:10], "por_anio": n_d8.to_dict()}))
    lm = dom[dom.dominio_id == "lima_metropolitana"]
    lm_mal = lm[cod[lm.index].map(lambda c: c.get("variable") == "dominio") | lm.composicion.map(lambda c: c != ["1501"])]
    out.append(("D-03", "dim_dominio: Lima Metropolitana (1501) nunca se codifica como dominio 8 ni incluye al Callao",
                lm_mal.empty, lm_mal[["encuesta_id", "anio"]].values.tolist()))
    tipos = {(e, d): set(g.tipo) for (e, d), g in dom[dom.dominio_id.isin(
        ["lima_metropolitana", "lima_provincias", "callao"])].groupby(["encuesta_id", "dominio_id"])}
    esperado = {("ENAHO", "lima_metropolitana"): {"ambito_publicado"}, ("ENAHO", "lima_provincias"): {"ambito_publicado"},
                ("ENAHO", "callao"): {"ambito_publicado"}, ("ENDES", "lima_metropolitana"): {"ambito_publicado"},
                ("ENDES", "lima_provincias"): {"ambito_publicado"}, ("ENDES", "callao"): {"dominio_diseno"}}
    out.append(("D-04", "dim_dominio: LM y LR son ámbito publicado en ENDES y ENAHO; el Callao es dominio de diseño en "
                "la ENDES y ámbito publicado en la ENAHO", tipos == esperado, {str(k): sorted(v) for k, v in tipos.items()}))
    cob = {(e, d): sorted(set(g.anio)) for (e, d), g in dom[dom.dominio_id.isin(
        ["lima_metropolitana", "lima_provincias", "callao"]) & dom.confirmado].groupby(["encuesta_id", "dominio_id"])}
    out.append(("D-05", "dim_dominio: LM, LR y Callao confirmados 2015–2025 en ENDES y ENAHO, identificables en microdatos",
                all(v == list(range(2015, 2026)) for v in cob.values()) and len(cob) == 6
                and bool(dom[dom.dominio_id.isin(["lima_metropolitana", "lima_provincias", "callao"])].identificable_microdatos.all()),
                {str(k): (v[0], v[-1], len(v)) for k, v in cob.items()}))
    endes = dom[(dom.encuesta_id == "ENDES") & dom.dominio_id.isin(["lima_metropolitana", "lima_provincias"])]
    met = endes.groupby("anio").metodo.agg(lambda m: sorted(set(m))).to_dict()
    ok = all(v == (["estrato_hv022"] if a <= 2017 else ["ubigeo"]) for a, v in met.items())
    out.append(("D-06", "dim_dominio: ENDES LM/LR por estrato en 2015–2017 y por ubigeo desde 2018; fuente = Cuadro N.º 1",
                ok and bool(endes.fuente_definicion.str.contains("Cuadro N.º 1").all()), met))
    return out
