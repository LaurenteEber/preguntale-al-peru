"""Pieza C de las decisiones del gasto (rondas 1-2, aprobadas por el dueño el 7/10/2026): capa de trazabilidad de
programas presupuestales y sociales, dim_tema_gasto v1.2 y glosario v2. Lo llama gasto.construir() con la conexión
abierta (tablas `base`, `fact` y `dim_unidad_ejecutora`), antes de escribir la fact.

Tablas (biblioteca/dimensiones/, sprint s3_gasto):
  dim_programa, dim_producto, dim_actividad   programa / producto / nodo (año, PP, producto, actividad) por año: 2023-2025
                                              desde la base (solo filas de actividades) y, en dim_programa, los años
                                              anteriores documentados (origen documental, sin cifras)
  dim_concepto, rel_concepto_grupo            concepto estable (hoja o grupo) y la pertenencia N:M hoja → grupo
  rel_concepto_nodo                           nodos de cada hoja por año: 2023-2025 resueltos desde la base con la regla
                                              curada (map_concepto_nodo.csv; gana la fila más específica, escrita como
                                              exclusiones explícitas) y 2017-2022 documentales (W1 v2), sin montos
  rel_linaje                                  eventos (tipo, años como intervalo, norma, URL, confianza, comparabilidad)
  rel_programa_politica                       ancestro_de / categoria_de / contribuye_a (requisito 6 de W1)
  dim_programa_social, rel_programa_social_ejecutora, rel_programa_social_financiamiento
  rel_programa_social_linea_aparte            (E3, 8/10/2026) gasto del programa fuera del gasto final que se muestra
                                              siempre aparte (Llamkasun: transferido a municipalidades); vista
                                              v_programa_social_linea_aparte
  cobertura_por_anio                          (concepto, año) 2008-2025: estado de los datos y comparabilidad (§4.4 de W2)
  dim_tema_gasto (v1.2)                       temas con prefijo de cadena (fun_, div_, pp_, ppxfun_, cpt_, ps_)
  dim_glosario_gasto                          glosario v2 (42 términos)
Las cifras no se guardan en estas tablas (salvo rel_programa_social_financiamiento, automática): se leen con las vistas
de vistas_gasto_temas.sql (v_gasto_concepto y la macro gasto_tema('<tema_id>')), que solo usan el gasto final (R-GASTO-05).
Alcances: conceptos, programas sociales y temas por función etiquetan los mismos soles y no se suman entre sí.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yaml

from ..config import Rutas
from ..errores import PapError
from . import insumos

CARPETA = "trazabilidad"
ARCHIVOS = ["programas_presupuestales.csv", "programa_politica.csv", "conceptos.csv", "concepto_grupo.csv",
            "map_concepto_nodo.csv", "nodos_documentales.csv", "cobertura_anio.csv", "linaje.csv",
            "programas_sociales.yaml", "temas_gasto.yaml", "glosario_gasto.csv"]
VERSION_TRAZA = "1.0.0"
VERSION_TEMA = "1.2.0"
GRAMATICA_TEMA = re.compile(r"^(fun|div|pp|ppxfun|cpt|ps)_[0-9a-z_]+$")
PREFIJO_CADENA = {"fun": "funcion", "div": "division", "pp": "programa", "ppxfun": "programa_x_funcion",
                  "cpt": "concepto", "ps": "programa_social"}
NIVEL_CADENA = {"funcion": "funcion", "division": "division_funcional", "programa": "programa",
                "programa_x_funcion": "programa_y_funcion", "concepto": "concepto (nodo año-programa-producto-actividad)",
                "programa_social": "ejecutora_o_actividad"}
LLAVE_CADENA = {"funcion": "anio+funcion", "division": "anio+funcion+division_funcional",
                "programa": "anio+programa_ppto", "programa_x_funcion": "anio+programa_ppto+funcion",
                "concepto": "anio+concepto_grupo_id → rel_concepto_grupo → rel_concepto_nodo (programa_ppto+"
                            "producto_proyecto+actividad_accion_obra [+ sec_ejec | funcion])",
                "programa_social": "anio+nivel_gobierno+sec_ejec (ejecutora) | anio+nivel_gobierno+actividad_accion_obra"}
TIPOS_CAMBIO = {"alta", "baja", "renombre", "recodificacion", "traslado", "fusion", "division", "absorcion_total",
                "absorcion_parcial", "absorcion_no_separable", "cambio_de_alcance", "cambio_de_contenido", "reemplazo",
                "sucesion"}
ESTADOS_ANIO = {"con_montos", "documentado_sin_montos", "documentado_parcial", "estructura_no_comparable"}
UMBRAL_NODOS_NUEVOS = 0.05   # R-GASTO-09 (2)
ANIO_MIN_DOC = 2008
GENERICOS = {"3000001", "3999999"}
CADENA_GLOSARIO = {"programatica", "funcional", "ambas", "ninguna", "economica", "fuente", "institucional"}


# ------------------------------------------------------------------ lectura y validación de los curados
def _csv(ruta: Path) -> pd.DataFrame:
    df = pd.read_csv(ruta, dtype=str, keep_default_na=False)
    return pd.DataFrame({c: [None if v == "" else v for v in df[c]] for c in df.columns}, dtype=object)


def _nulo(x) -> bool:
    return x is None or x is pd.NA or (isinstance(x, float) and pd.isna(x))


def _bool(x):
    if x is None or x is pd.NA or (isinstance(x, float) and pd.isna(x)):
        return None
    if isinstance(x, bool):
        return x
    return {"true": True, "false": False}[str(x).strip().lower()]


def _lista(x) -> list[str]:
    if x is None or x is pd.NA or (isinstance(x, float) and pd.isna(x)):
        return []
    return [s.strip() for s in str(x).split(";") if s.strip()]


def cargar(rutas: Rutas) -> tuple[dict, list]:
    """Lee y valida los curados; devuelve (datos, insumos)."""
    ins = [insumos.curado(rutas, f"{CARPETA}/{a}") for a in ARCHIVOS]
    r = {i.nombre.split("/")[-1]: i.ruta for i in ins}
    d = {
        "programas": _csv(r["programas_presupuestales.csv"]),
        "politica": _csv(r["programa_politica.csv"]),
        "conceptos": _csv(r["conceptos.csv"]),
        "grupos": _csv(r["concepto_grupo.csv"]),
        "mapa": _csv(r["map_concepto_nodo.csv"]),
        "doc": _csv(r["nodos_documentales.csv"]),
        "cobertura": _csv(r["cobertura_anio.csv"]),
        "linaje": _csv(r["linaje.csv"]),
        "ps": yaml.safe_load(r["programas_sociales.yaml"].read_text(encoding="utf-8")),
        "temas": yaml.safe_load(r["temas_gasto.yaml"].read_text(encoding="utf-8")),
        "glosario": _csv(r["glosario_gasto.csv"]),
    }
    validar(d)
    return d, ins


def validar(d: dict) -> None:
    def falla(msg):
        raise PapError(f"trazabilidad: {msg}")
    pr = d["programas"]
    if pr.programa_ppto.duplicated().any() or not pr.programa_ppto.str.fullmatch(r"\d{4}").all():
        falla("programas_presupuestales.csv: código repetido o mal formado")
    co = d["conceptos"]
    if co.concepto_id.duplicated().any() or not co.nivel.isin(["hoja", "grupo"]).all():
        falla("conceptos.csv: concepto repetido o nivel desconocido")
    hojas = set(co.loc[co.nivel == "hoja", "concepto_id"])
    grupos = set(co.loc[co.nivel == "grupo", "concepto_id"])
    g = d["grupos"]
    if not (set(g.grupo_id) <= grupos and set(g.concepto_id) <= hojas) or g.duplicated(["grupo_id", "concepto_id"]).any():
        falla("concepto_grupo.csv: grupo u hoja inexistente, o par repetido")
    m = d["mapa"]
    if m.regla_id.duplicated().any() or not set(m.concepto_id) <= hojas:
        falla("map_concepto_nodo.csv: regla repetida o concepto que no es hoja")
    if not m.excluye_transferencias.eq("true").all():
        falla("map_concepto_nodo.csv: toda regla excluye transferencias (R-GASTO-05)")
    if m.duplicated(["programa_ppto", "producto_proyecto", "actividad_accion_obra", "filtro_sec_ejec", "filtro_funcion",
                     "anio_desde"]).any():
        falla("map_concepto_nodo.csv: dos reglas con la misma firma")
    if not set(d["doc"].concepto_estable) <= hojas:
        falla("nodos_documentales.csv: concepto inexistente")
    cob = d["cobertura"]
    if not cob.estado.isin(sorted(ESTADOS_ANIO)).all() or cob.anio.duplicated().any():
        falla("cobertura_anio.csv: estado desconocido o año repetido")
    li = d["linaje"]
    if li.id_evento.duplicated().any():
        falla("linaje.csv: id_evento repetido")
    for t in li.tipo_cambio:
        if not set(t.split("+")) <= TIPOS_CAMBIO:
            falla(f"linaje.csv: tipo de cambio desconocido {t!r}")
    for e in li.itertuples():
        if _nulo(e.anio_min) != _nulo(e.anio_max) or (not _nulo(e.anio_min) and int(e.anio_min) > int(e.anio_max)):
            falla(f"linaje.csv: intervalo de años inválido en {e.id_evento}")
        if _nulo(e.anio_min) and "por_verificar" not in str(e.confianza):
            falla(f"linaje.csv: {e.id_evento} sin años debe declararse por_verificar")
        if not set(_lista(e.conceptos_afectados)) <= hojas:
            falla(f"linaje.csv: concepto inexistente en {e.id_evento}")
        for c in ("comparable_por_concepto", "comparable_por_programa", "comparable_por_programa_social"):
            _bool(getattr(e, c))
    # auditoría de la pieza C, H4: el visto del dueño se declara explícitamente (pendiente o «Dueño, d/m/aaaa»)
    rev_ps = str(d["ps"].get("revisado_por", ""))
    if not (rev_ps.startswith("pendiente") or re.match(r"Dueño, \d{1,2}/\d{1,2}/\d{4}", rev_ps)):
        falla("programas_sociales.yaml: revisado_por debe ser «pendiente…» o «Dueño, d/m/aaaa …» (auditoría, H4)")
    ids_ps = [p["id"] for p in d["ps"]["programas"]]
    if len(ids_ps) != len(set(ids_ps)):
        falla("programas_sociales.yaml: id repetido")
    for p in d["ps"]["programas"]:
        idf = p["identificacion"]
        if not re.fullmatch(r"[0-9a-z_]+", p["id"]) or idf.get("nivel_gobierno") not in ("E", "M") or \
                bool(idf.get("sec_ejec")) == bool(idf.get("actividad_accion_obra")) or not p.get("nombres"):
            falla(f"programas_sociales.yaml: entrada inválida {p.get('id')}")
        la = p.get("linea_aparte")
        if la is not None and (not idf.get("sec_ejec") or not re.fullmatch(r"[a-z_]+", str(la.get("id", ""))) or
                               not la.get("rotulo") or not isinstance(la.get("obligatoria"), bool) or
                               not la.get("clasificadores") or
                               not all(re.fullmatch(r"2\.4\.\d\.\d\.\d\.\d", c) for c in la["clasificadores"])):
            falla(f"programas_sociales.yaml: linea_aparte inválida en {p['id']} (id, rótulo, obligatoria y "
                  "clasificadores 2.4 de específica de detalle; solo en programas definidos por ejecutora)")
        for n in p["nombres"]:
            if n.get("rotulo_fecha") not in (None, "mes", "dia"):
                falla(f"programas_sociales.yaml: rotulo_fecha desconocido en {p['id']}")
    for e in li.itertuples():
        if not set(_lista(e.programas_sociales_afectados)) <= set(ids_ps):
            falla(f"linaje.csv: programa social inexistente en {e.id_evento}")
    temas = d["temas"]["temas"]
    for t in temas:
        validar_tema_id(t["tema_id"], t["cadena"])
        if t["cadena"] == "concepto" and t.get("concepto_grupo_id") not in grupos:
            falla(f"temas_gasto.yaml: grupo inexistente en {t['tema_id']}")
    ids = [t["tema_id"] for t in temas] + ["ps_" + i for i in ids_ps]
    if len(ids) != len(set(ids)):
        falla("temas_gasto.yaml: tema repetido")
    for t in temas:
        if t.get("alternativa_de") and t["alternativa_de"] not in ids:
            falla(f"temas_gasto.yaml: alternativa_de inexistente en {t['tema_id']}")
    gl = d["glosario"]
    if gl.id.duplicated().any() or not gl.id.str.fullmatch(r"[a-z0-9_]+").all():
        falla("glosario_gasto.csv: id repetido o mal formado")


def validar_tema_id(tema_id: str, cadena: str) -> None:
    """R-GASTO-08b (1): gramática y prefijo = cadena; si no, la construcción falla."""
    if not GRAMATICA_TEMA.fullmatch(tema_id or ""):
        raise PapError(f"dim_tema_gasto: tema_id fuera de la gramática: {tema_id!r}")
    if PREFIJO_CADENA[tema_id.split("_", 1)[0]] != cadena:
        raise PapError(f"dim_tema_gasto: el prefijo de {tema_id} no corresponde a la cadena {cadena}")


# ------------------------------------------------------------------ nombres de programas sociales
def _fecha(s, fin=False) -> date | None:
    if s is None:
        return None
    p = [int(x) for x in str(s).split("-")]
    if len(p) == 1:
        return date(p[0], 12, 31) if fin else date(p[0], 1, 1)
    if len(p) == 2:
        return date(p[0], p[1], 1)
    return date(*p)


def nombres_del_anio(nombres: list[dict], anio: int) -> list[tuple[str, int, dict]]:
    """[(nombre, días vigente en el año, entrada)] de los nombres vigentes durante el año, en orden. Un nombre con
    `desde` nulo (por verificar) se toma vigente desde el inicio del nombre anterior (o desde siempre)."""
    ini, fin = date(anio, 1, 1), date(anio, 12, 31)
    efectivo, prev = [], date(1900, 1, 1)
    for n in nombres:
        prev = _fecha(n.get("desde")) or prev
        efectivo.append(prev)
    out = []
    for i, n in enumerate(nombres):
        h = efectivo[i + 1] - timedelta(days=1) if i + 1 < len(nombres) else date(9999, 12, 31)
        a, b = max(efectivo[i], ini), min(h, fin)
        if a <= b:
            out.append((n["nombre"], (b - a).days + 1, n, efectivo[i], h))
    return out


def tipo_del_anio(tipo: str | None, eventos: str | None, anio: int) -> str | None:
    """Tipo de la categoría en el año: los programas estratégicos de 2008 (Ley 29142) lo son hasta 2011 y desde 2012
    son programas presupuestales (W2 v2 §2.1; auditoría de la pieza C, H7)."""
    estrategico = "estratégico" in f"{tipo or ''} {eventos or ''}".lower()
    if estrategico and anio <= 2011:
        return "programa estratégico (2008-2011)"
    if tipo and tipo.startswith("PP (programa estratégico"):
        return "PP"
    return tipo


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s)).strip()


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "setiembre", "octubre", "noviembre",
         "diciembre"]


def _fecha_rotulo(d: date, por_mes: bool) -> str:
    """«el 9/8/2023» o, con rotulo_fecha: mes, «agosto de 2023» (decisión del dueño del 8/10/2026: el rótulo dice el
    mes del cambio, no el día; un decreto rige desde el día siguiente a su publicación)."""
    return f"{MESES[d.month - 1]} de {d.year}" if por_mes else f"el {d.day}/{d.month}/{d.year}"


def etiqueta_programa_social(nombres: list[dict], anio: int, nombre_mef: str | None) -> dict:
    vig = nombres_del_anio(nombres, anio)
    if not vig:
        return {}
    principal = max(vig, key=lambda x: x[1])  # el de más días; empate → el primero
    nombre, entrada, ini_p = principal[0], principal[2], principal[3]
    texto = nombre
    if len(vig) > 1:
        # la precisión del rótulo la da la entrada del nombre que empieza (rotulo_fecha: mes → sin día)
        sig = {i: (vig[i + 1][2] if i + 1 < len(vig) else {}) for i in range(len(vig))}
        otros = [(f"{n} hasta {_fecha_rotulo(fin, sig[i].get('rotulo_fecha') == 'mes')}" if ini < ini_p
                  else f"{n} desde {_fecha_rotulo(ini, e.get('rotulo_fecha') == 'mes')}")
                 for i, (n, _, e, ini, fin) in enumerate(vig) if n != nombre]
        texto = f"{nombre} ({'; '.join(otros)})"
    claves = [_norm(nombre.split(" (")[0])] + [_norm(a) for a in entrada.get("alias_mef", [])]
    difiere = bool(nombre_mef) and not any(k and k in _norm(nombre_mef) for k in claves)
    if difiere:
        texto += f" (en el presupuesto del MEF figura como «{re.sub(r'\s+', ' ', nombre_mef).strip()}»)"
    return {"nombre_propio": nombre, "nombres_en_el_anio": "; ".join(v[0] for v in vig),
            "nombre_cambia_en_anio": len(vig) > 1, "nombre_mef_difiere": difiere, "etiqueta": texto,
            "norma_nombre": entrada.get("norma"), "url_nombre": entrada.get("url") or None,
            "confianza_nombre": entrada.get("confianza")}


# ------------------------------------------------------------------ resolución de conceptos
def resolver_mapa(mapa: pd.DataFrame, nodos: pd.DataFrame) -> pd.DataFrame:
    """Aplica map_concepto_nodo a los nodos (anio, programa_ppto, producto_proyecto, actividad_accion_obra) de la base.
    En cada nodo gana la regla más específica (actividad 4, ejecutora 2, función 1). La precedencia se escribe como
    exclusiones explícitas (excluye_sec_ejec / excluye_funcion) para que la unión con la fact sea por igualdad y cada
    sol caiga, como máximo, en una hoja."""
    m = mapa.copy()
    m["anio_desde"] = m.anio_desde.astype(int)
    m["anio_hasta"] = m.anio_hasta.map(lambda x: int(x) if x else 9999)
    m["rango"] = (m.actividad_accion_obra.notna() * 4 + m.filtro_sec_ejec.notna() * 2 + m.filtro_funcion.notna() * 1)
    x = nodos.merge(m, on=["programa_ppto", "producto_proyecto"], suffixes=("", "_regla"))
    x = x[(x.anio >= x.anio_desde) & (x.anio <= x.anio_hasta)
          & (x.actividad_accion_obra_regla.isna() | (x.actividad_accion_obra_regla == x.actividad_accion_obra))]
    filas = []
    llave = ["anio", "programa_ppto", "producto_proyecto", "actividad_accion_obra"]
    for k, g in x.groupby(llave, sort=True):
        g = g.sort_values(["rango", "regla_id"], ascending=[False, True])
        if g.duplicated(["rango", "filtro_sec_ejec", "filtro_funcion"]).any():
            raise PapError(f"map_concepto_nodo: reglas ambiguas en el nodo {k}")
        for i, r in enumerate(g.itertuples()):
            mayores = g.iloc[:i]
            mayores = mayores[mayores.rango > r.rango]
            if (mayores.filtro_sec_ejec.isna() & mayores.filtro_funcion.isna()).any():
                continue  # una regla más específica sin filtros se lleva todo el nodo
            exc_s = sorted(set(mayores.filtro_sec_ejec.dropna()) - ({r.filtro_sec_ejec} if r.filtro_sec_ejec else set()))
            exc_f = sorted(set(mayores.filtro_funcion.dropna()) - ({r.filtro_funcion} if r.filtro_funcion else set()))
            mixtas = mayores[mayores.filtro_sec_ejec.notna() & mayores.filtro_funcion.notna()]
            if len(exc_s) > 1 or len(exc_f) > 1 or (exc_s and exc_f) or len(mixtas):
                raise PapError(f"map_concepto_nodo: precedencia no expresable con una exclusión en el nodo {k}")
            filas.append(dict(zip(llave, k), concepto_id=r.concepto_id, sec_ejec=r.filtro_sec_ejec,
                              excluye_sec_ejec=exc_s[0] if exc_s else None, funcion=r.filtro_funcion,
                              excluye_funcion=exc_f[0] if exc_f else None, regla_id=r.regla_id,
                              evidencia=r.evidencia, confianza=r.confianza))
    return pd.DataFrame(filas, columns=llave + ["concepto_id", "sec_ejec", "excluye_sec_ejec", "funcion",
                                               "excluye_funcion", "regla_id", "evidencia", "confianza"])


def _partir_codigos(prod: str | None, act: str | None) -> list[tuple[str, str | None]]:
    p, a = _lista(prod), _lista(act)
    if not p:
        return []
    if len(p) == len(a):
        return list(zip(p, a))
    if len(p) == 1:
        return [(p[0], x) for x in a] or [(p[0], None)]
    if len(a) == 1:
        return [(x, a[0]) for x in p]
    if not a:
        return [(x, None) for x in p]
    raise PapError(f"nodos_documentales.csv: no se pueden emparejar {prod} y {act}")


def nodos_documentales(doc: pd.DataFrame, hasta: int = 2022) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(nodos ≤ hasta, nodos > hasta para cotejar con la base). Nombres «idem» se completan con el del mismo código."""
    nom_p, nom_a = {}, {}
    for r in doc.itertuples():
        for cods, noms, dic in ((r.producto_codigo, r.producto_nombre, nom_p), (r.actividad_codigo, r.actividad_nombre, nom_a)):
            c, n = _lista(cods), [s.strip() for s in str(noms or "").split(";")]
            if len(c) == len(n):
                for ci, ni in zip(c, n):
                    if ni.lower() not in ("idem", "ídem", "") and not ni.startswith("("):
                        dic.setdefault(ci, ni)
    filas = []
    for r in doc.itertuples():
        for p, a in _partir_codigos(r.producto_codigo, r.actividad_codigo):
            for y in range(int(r.anio_desde), int(r.anio_hasta) + 1):
                filas.append(dict(anio=y, concepto_id=r.concepto_estable, programa_ppto=r.programa_ppto,
                                  producto_proyecto=p, actividad_accion_obra=a, programa_ppto_nombre=r.programa_nombre,
                                  producto_proyecto_nombre=nom_p.get(p), actividad_accion_obra_nombre=nom_a.get(a),
                                  tipo_cambio=r.tipo_cambio, url=r.fuente_url, confianza=r.confianza, nota=r.nota))
    df = pd.DataFrame(filas)
    return df[df.anio <= hasta].reset_index(drop=True), df[df.anio > hasta].reset_index(drop=True)


# ------------------------------------------------------------------ comparabilidad (W2 §4.4, R-GASTO-09)
def _eventos(linaje: pd.DataFrame, anio: int, col: str, valores: set[str]) -> pd.DataFrame:
    e = linaje[linaje.anio_min.notna()]
    e = e[(e.anio_min.astype(int) <= anio) & (e.anio_max.astype(int) >= anio)]
    return e.loc[e[col].map(lambda x: bool(set(_lista(x)) & valores)).astype(bool)]


def comparabilidad(anio: int, anios_con_montos: list[int], eventos: pd.DataFrame, bandera: str,
                   peso_nuevos: float | None) -> tuple[str, str]:
    """(comparable_con_anio_anterior, motivo). bandera: columna de rel_linaje que decide (comparable_por_*)."""
    ev_txt = lambda df: "; ".join(f"{e.id_evento} {e.tipo_cambio} ({e.comparabilidad})" for e in df.itertuples())
    if anio not in anios_con_montos:
        return "sin_montos", ("eventos del año: " + ev_txt(eventos)) if len(eventos) else ""
    if anio - 1 not in anios_con_montos:
        return "sin_anio_anterior", (f"{anio - 1} sin montos en la base" +
                                     (f"; eventos del año: {ev_txt(eventos)}" if len(eventos) else ""))
    malos = eventos.loc[(eventos[bandera].map(_bool) == False).astype(bool)]  # noqa: E712
    buenos = eventos.loc[(eventos[bandera].map(_bool) == True).astype(bool)]  # noqa: E712
    if len(malos):
        return "no", "evento de linaje: " + ev_txt(malos)
    if peso_nuevos is not None and peso_nuevos > UMBRAL_NODOS_NUEVOS and not len(buenos):
        return "no", f"nodos nuevos: {peso_nuevos:.1%} del devengado del año (> {UMBRAL_NODOS_NUEVOS:.0%})"
    nota = []
    if peso_nuevos:
        nota.append(f"nodos nuevos: {peso_nuevos:.1%}")
    if len(buenos):
        nota.append("evento comparable: " + ev_txt(buenos))
    return "si", "; ".join(nota)


def _peso_nuevos(montos: pd.DataFrame, anio: int) -> float | None:
    """montos: anio, programa_ppto, producto_proyecto, actividad_accion_obra, dev (de un concepto, grupo o programa)."""
    act = montos[montos.anio == anio]
    tot = float(act.dev.sum())
    if tot == 0:
        return None
    previos = set(map(tuple, montos.loc[montos.anio == anio - 1, ["programa_ppto", "producto_proyecto",
                                                                    "actividad_accion_obra"]].values))
    nuevos = act[[t not in previos for t in map(tuple, act[["programa_ppto", "producto_proyecto",
                                                              "actividad_accion_obra"]].values)]]
    return float(nuevos.dev.sum()) / tot


# ------------------------------------------------------------------ construcción
SQL_JOIN_CONCEPTO = """
    f.anio = r.anio AND f.programa_ppto = r.programa_ppto AND f.producto_proyecto = r.producto_proyecto
    AND f.actividad_accion_obra = r.actividad_accion_obra AND f.tipo_act_proy = 'ACTIVIDAD'
    AND (r.sec_ejec IS NULL OR (f.sec_ejec = r.sec_ejec AND f.nivel_gobierno = 'E'))
    AND (r.excluye_sec_ejec IS NULL OR NOT (f.sec_ejec = r.excluye_sec_ejec AND f.nivel_gobierno = 'E'))
    AND (r.funcion IS NULL OR f.funcion = r.funcion)
    AND (r.excluye_funcion IS NULL OR f.funcion <> r.excluye_funcion)"""


def construir(con, rutas: Rutas, res, anios: list[int], controles: dict) -> dict[str, pd.DataFrame]:
    d, ins = cargar(rutas)
    res.insumos += ins
    anios = sorted(int(a) for a in anios)
    cob = d["cobertura"].assign(anio=lambda x: x.anio.astype(int))
    estado_anio = dict(zip(cob.anio, cob.estado))
    anios_con_montos = sorted(a for a, e in estado_anio.items() if e == "con_montos")
    res.prueba("G-34", "cobertura_anio: los años con montos son exactamente los años de la base (2023-2025)",
               anios_con_montos == anios, {"cobertura": anios_con_montos, "base": anios})

    # ---------------- nodos de la base (solo filas de actividades: en los proyectos el producto es el CUI)
    con.execute("""
        CREATE OR REPLACE TABLE traza_nodos AS
        SELECT anio, programa_ppto, tipo_act_proy, producto_proyecto, actividad_accion_obra,
               min(programa_ppto_nombre) AS programa_ppto_nombre, count(DISTINCT programa_ppto_nombre) AS n_nom_pp,
               min(producto_proyecto_nombre) AS producto_proyecto_nombre,
               count(DISTINCT producto_proyecto_nombre) AS n_nom_prod,
               min(actividad_accion_obra_nombre) AS actividad_accion_obra_nombre,
               count(DISTINCT actividad_accion_obra_nombre) AS n_nom_act,
               count(DISTINCT sec_ejec) AS n_ejecutoras
        FROM base GROUP BY ALL""")
    nodos = con.execute("""SELECT * FROM traza_nodos WHERE tipo_act_proy = 'ACTIVIDAD'
                           ORDER BY anio, programa_ppto, producto_proyecto, actividad_accion_obra""").df()
    progs_base = con.execute("""SELECT anio, programa_ppto, min(programa_ppto_nombre) AS nombre_mef,
                                       count(DISTINCT programa_ppto_nombre) AS n_nom,
                                       count(DISTINCT producto_proyecto) FILTER (WHERE tipo_act_proy = 'ACTIVIDAD') AS n_productos,
                                       count(*) FILTER (WHERE tipo_act_proy = 'ACTIVIDAD') AS n_nodos_actividad,
                                       bool_or(tipo_act_proy = 'PROYECTO') AS tiene_proyectos
                                FROM traza_nodos GROUP BY 1, 2 ORDER BY 1, 2""").df()
    varios = int((nodos.n_nom_prod > 1).sum() + (nodos.n_nom_act > 1).sum() + (progs_base.n_nom > 1).sum())
    res.prueba("G-35", "Un nombre por año y código de programa, producto y nodo (si no, se publica el menor y se avisa)",
               varios == 0, {"codigos_con_varios_nombres": varios}, bloqueante=False)

    # ---------------- temas de programa (para «mapeado o sin_tema»)
    temas = d["temas"]["temas"]
    tema_pp = {c: t["tema_id"] for t in temas if t["cadena"] == "programa" for c in t["programa_ppto"]}

    # ---------------- dim_programa (base 2023-2025 + años documentados)
    pr = {r["programa_ppto"]: {k: (None if _nulo(v) else v) for k, v in r.items()}
          for r in d["programas"].to_dict("records")}

    def rotulo(c, nombre):
        if c in pr and pr[c]["rotulo"]:
            return pr[c]["rotulo"]
        return f"PP {c} {nombre.title()}" if nombre else f"PP {c}"
    filas = []
    previo = {}
    for r in progs_base.itertuples():
        cur = pr.get(r.programa_ppto, {})
        y = int(r.anio)
        filas.append(dict(
            programa_ppto=r.programa_ppto, anio=y, origen="base", estado_anio=estado_anio.get(y),
            nombre_mef=r.nombre_mef, nombre_oficial=cur.get("nombre_oficial") or r.nombre_mef,
            rotulo=rotulo(r.programa_ppto, r.nombre_mef),
            tipo=tipo_del_anio(cur.get("tipo") or {"9001": "acciones centrales", "9002": "APNOP"}.get(r.programa_ppto, "PP"),
                               cur.get("eventos"), y),
            tipo_historico=cur.get("tipo"),
            anio_desde=cur.get("anio_desde"), anio_hasta=cur.get("anio_hasta"),
            n_productos=int(r.n_productos), n_nodos_actividad=int(r.n_nodos_actividad), tiene_proyectos=bool(r.tiene_proyectos),
            presente_anio_anterior=(r.programa_ppto in previo.get(y - 1, set())) if y - 1 in anios else None,
            tema_programa=tema_pp.get(r.programa_ppto, "sin_tema"),
            estado=cur.get("estado"), eventos=cur.get("eventos"),
            evidencia=cur.get("evidencia") or "[dato] base MEF", url=cur.get("url"), confianza=cur.get("confianza") or "alta"))
        previo.setdefault(y, set()).add(r.programa_ppto)
    for c, cur in sorted(pr.items()):
        if not cur["anio_desde"]:
            continue
        a0 = max(int(cur["anio_desde"]), ANIO_MIN_DOC)
        a1 = min(int(cur["anio_hasta"]) if cur["anio_hasta"] else 9999, min(anios) - 1)
        for y in range(a0, a1 + 1):
            filas.append(dict(programa_ppto=c, anio=y, origen="documental", estado_anio=estado_anio.get(y),
                              nombre_mef=None, nombre_oficial=cur["nombre_oficial"], rotulo=rotulo(c, cur["nombre_oficial"]),
                              tipo=tipo_del_anio(cur["tipo"], cur["eventos"], y), tipo_historico=cur["tipo"],
                              anio_desde=cur["anio_desde"], anio_hasta=cur["anio_hasta"], n_productos=None,
                              n_nodos_actividad=None, tiene_proyectos=None, presente_anio_anterior=None,
                              tema_programa=None, estado=cur["estado"], eventos=cur["eventos"], evidencia=cur["evidencia"],
                              url=cur["url"], confianza=cur["confianza"]))
    dim_programa = pd.DataFrame(filas)
    for col in ("anio_desde", "anio_hasta", "n_productos", "n_nodos_actividad"):
        dim_programa[col] = pd.to_numeric(dim_programa[col]).astype("Int64")
    dim_programa["version_tabla"] = VERSION_TRAZA

    # ---------------- dim_producto y dim_actividad (nodo) por año
    nodos["anio"] = nodos.anio.astype(int)
    prod = (nodos.groupby(["anio", "programa_ppto", "producto_proyecto"], as_index=False)
            .agg(producto_proyecto_nombre=("producto_proyecto_nombre", "min"),
                 n_actividades=("actividad_accion_obra", "nunique")))
    llp = set(map(tuple, prod[["anio", "programa_ppto", "producto_proyecto"]].values))
    prod["presente_anio_anterior"] = [((a - 1, p, c) in llp) if a - 1 in anios else None
                                      for a, p, c in prod[["anio", "programa_ppto", "producto_proyecto"]].values]
    prod["codigo_generico"] = prod.producto_proyecto.isin(GENERICOS)
    prod["version_tabla"] = VERSION_TRAZA
    act = nodos[["anio", "programa_ppto", "producto_proyecto", "actividad_accion_obra", "actividad_accion_obra_nombre",
                 "n_ejecutoras"]].copy()
    lla = set(map(tuple, act[["anio", "programa_ppto", "producto_proyecto", "actividad_accion_obra"]].values))
    act["presente_anio_anterior"] = [((a - 1, p, c, x) in lla) if a - 1 in anios else None for a, p, c, x in
                                     act[["anio", "programa_ppto", "producto_proyecto", "actividad_accion_obra"]].values]
    pp_de_act = nodos.groupby(["anio", "actividad_accion_obra"]).programa_ppto.agg(lambda s: ";".join(sorted(set(s))))
    act["programas_de_la_actividad_anio_anterior"] = [pp_de_act.get((a - 1, x)) for a, x in
                                                      act[["anio", "actividad_accion_obra"]].values]
    act["n_ejecutoras"] = act.n_ejecutoras.astype("Int64")
    act["version_tabla"] = VERSION_TRAZA

    # ---------------- conceptos: nodos de la base (regla curada) y documentales
    rel_base = resolver_mapa(d["mapa"], nodos[["anio", "programa_ppto", "producto_proyecto", "actividad_accion_obra"]])
    rel_base = rel_base.merge(nodos[["anio", "programa_ppto", "producto_proyecto", "actividad_accion_obra",
                                     "programa_ppto_nombre", "producto_proyecto_nombre", "actividad_accion_obra_nombre"]],
                              how="left")
    rel_base["origen"] = "base"
    rel_base["tipo_cambio"] = None
    rel_base["url"] = None
    rel_base["nota"] = None
    doc_ant, doc_post = nodos_documentales(d["doc"], hasta=min(anios) - 1)
    for c in ("sec_ejec", "excluye_sec_ejec", "funcion", "excluye_funcion", "regla_id"):
        doc_ant[c] = None
    doc_ant["origen"] = "documental"
    doc_ant["evidencia"] = "[fuente] W1 v2 (linaje_productos_anemia_v2.csv)"
    rel = pd.concat([rel_base, doc_ant], ignore_index=True)
    rot = dim_programa.drop_duplicates("programa_ppto").set_index("programa_ppto").rotulo
    rel["rotulo_programa"] = rel.programa_ppto.map(rot)
    rel["anio"] = rel.anio.astype(int)
    rel["version_tabla"] = VERSION_TRAZA
    cols_rel = ["anio", "concepto_id", "programa_ppto", "producto_proyecto", "actividad_accion_obra", "sec_ejec",
                "excluye_sec_ejec", "funcion", "excluye_funcion", "origen", "regla_id", "rotulo_programa",
                "programa_ppto_nombre", "producto_proyecto_nombre", "actividad_accion_obra_nombre", "tipo_cambio",
                "evidencia", "url", "confianza", "nota", "version_tabla"]
    rel = rel[cols_rel]
    dup = int(rel.duplicated(["anio", "concepto_id", "programa_ppto", "producto_proyecto", "actividad_accion_obra",
                              "sec_ejec", "funcion"]).sum())
    res.prueba("G-28b", "rel_concepto_nodo: clave única (año, concepto, nodo, filtros)", dup == 0, {"repetidas": dup})
    # coteja los nodos que W1 documenta para 2023+ con los resueltos desde la base
    base_set = set(map(tuple, rel_base[["anio", "concepto_id", "programa_ppto", "producto_proyecto",
                                        "actividad_accion_obra"]].values))
    falt = [t for t in map(tuple, doc_post[["anio", "concepto_id", "programa_ppto", "producto_proyecto",
                                            "actividad_accion_obra"]].values) if t not in base_set]
    res.prueba("G-31", "Los nodos que W1 v2 documenta para 2023-2025 están entre los resueltos desde la base para el "
               "mismo concepto", not falt, {"nodos_w1": len(doc_post), "faltan": [list(map(str, t)) for t in falt[:20]]})

    # asignación sobre la fact: cada sol, como máximo en una hoja (todas las filas, cualquier bloque)
    con.register("rel_df", rel[rel.origen == "base"])
    con.execute("CREATE OR REPLACE TABLE rel_concepto_nodo AS SELECT * FROM rel_df")
    con.unregister("rel_df")
    from .gasto import CLAVE_FACT  # import diferido (gasto importa este módulo)
    clave = ", ".join(f"f.{c}" for c in CLAVE_FACT)
    sup = con.execute(f"""SELECT count(*), coalesce(sum(dev), 0) FROM (
                            SELECT {clave}, count(*) AS n, any_value(f.devengado) AS dev
                            FROM fact f JOIN rel_concepto_nodo r ON {SQL_JOIN_CONCEPTO} GROUP BY ALL HAVING n > 1)""").fetchone()
    res.prueba("G-28", "Conceptos: cada fila de la fact cae como máximo en una hoja (alcance concepto, todos los bloques)",
               sup[0] == 0, {"filas_en_dos_hojas": sup[0], "devengado": str(sup[1])})
    montos = con.execute(f"""
        SELECT f.anio, r.concepto_id, f.programa_ppto, f.producto_proyecto, f.actividad_accion_obra,
               sum(f.devengado) FILTER (WHERE f.bloque_consolidado = 'gasto_final')::DOUBLE AS dev,
               sum(f.devengado) FILTER (WHERE NOT f.es_transferencia)::DOUBLE AS dev_sin_transf,
               sum(f.devengado)::DOUBLE AS dev_todos
        FROM fact f JOIN rel_concepto_nodo r ON {SQL_JOIN_CONCEPTO} GROUP BY ALL""").df().fillna(0)
    montos["anio"] = montos.anio.astype(int)
    dif = float((montos.dev - montos.dev_sin_transf).abs().sum())
    res.prueba("G-36", "Conceptos: gasto final (bloque_consolidado) = devengado sin transferencias (es_transferencia)",
               dif < 0.005, {"diferencia_soles": round(dif, 2)}, bloqueante=False)
    tot_1001 = dict(con.execute("""SELECT anio, sum(devengado)::DOUBLE FROM fact WHERE programa_ppto = '1001'
                                     AND tipo_act_proy = 'ACTIVIDAD' AND bloque_consolidado = 'gasto_final'
                                     GROUP BY 1""").fetchall())
    cub_1001 = montos[montos.programa_ppto == "1001"].groupby("anio").dev.sum()
    cobertura_1001 = [(int(a), float(t), float(cub_1001.get(int(a), 0.0))) for a, t in sorted(tot_1001.items())]
    res.prueba("G-33", "Conceptos: todo el gasto final de actividades del PP 1001 está en alguna hoja (cobertura 100 %)",
               all(abs(t - (c or 0)) < 0.005 for _, t, c in cobertura_1001),
               {str(a): round((c or 0) / t, 6) for a, t, c in cobertura_1001})

    # ---------------- dim_concepto, rel_concepto_grupo, montos por grupo
    co = d["conceptos"].copy()
    gr = d["grupos"].copy()
    tema_grupo = {t["concepto_grupo_id"]: t["tema_id"] for t in temas if t["cadena"] == "concepto"}
    co["grupos"] = co.concepto_id.map(gr.groupby("concepto_id").grupo_id.agg(lambda s: ";".join(sorted(s))))
    co["tema_id"] = co.concepto_id.map(tema_grupo)
    co["anio_primer_nodo"] = co.concepto_id.map(rel.groupby("concepto_id").anio.min()).astype("Int64")
    co["anio_ultimo_nodo"] = co.concepto_id.map(rel.groupby("concepto_id").anio.max()).astype("Int64")
    co["version_tabla"] = VERSION_TRAZA

    def montos_grupo(gid):
        g = gr[gr.grupo_id == gid]
        x = montos[montos.concepto_id.isin(set(g.concepto_id))]
        restr = set(g.restriccion_programa_ppto.dropna())
        return x[x.programa_ppto.isin(restr)] if restr else x
    serie = {}
    for gid in sorted(set(gr.grupo_id)):
        x = montos_grupo(gid)
        serie[gid] = {a: round(float(x.loc[x.anio == a, "dev"].sum()) / 1e6) for a in anios}
    pp1001 = {int(a): round(float(v) / 1e6) for a, v in con.execute(
        """SELECT anio, sum(devengado) FROM fact WHERE programa_ppto = '1001' AND bloque_consolidado = 'gasto_final'
           GROUP BY 1""").fetchall()}
    obtenido = {"grupo_expan": serie.get("grupo_expan"), "grupo_opcion_c": serie.get("grupo_opcion_c"),
                "grupo_anemia_estricta": serie.get("grupo_anemia_estricta"), "pp_1001_dit": pp1001}
    res.prueba("G-30", "Cifras aprobadas (millones, sin transferencias): serie por concepto ex-PAN, opción C, opción D y "
               "PP 1001 completo", obtenido == controles, {"obtenido": obtenido, "aprobado": controles})

    # ---------------- rel_linaje y rel_programa_politica
    li = d["linaje"].copy()
    for c in ("anio_min", "anio_max"):
        li[c] = pd.to_numeric(li[c]).astype("Int64")
    for c in ("comparable_por_concepto", "comparable_por_programa", "comparable_por_programa_social"):
        li[c] = li[c].map(_bool).astype("boolean")
    li["version_tabla"] = VERSION_TRAZA
    pol = d["politica"].assign(version_tabla=VERSION_TRAZA)

    # ---------------- cobertura_por_anio (concepto × año) con comparabilidad
    anios_todos = sorted(estado_anio)
    filas = []
    nodos_doc = set(zip(doc_ant.concepto_id, doc_ant.anio))
    nodos_base = set(zip(rel_base.concepto_id, rel_base.anio.astype(int)))
    for c in co.itertuples():
        es_grupo = c.nivel == "grupo"
        hojas = set(gr.loc[gr.grupo_id == c.concepto_id, "concepto_id"]) if es_grupo else {c.concepto_id}
        restr = set(gr.loc[gr.grupo_id == c.concepto_id, "restriccion_programa_ppto"].dropna()) if es_grupo else set()
        x = montos_grupo(c.concepto_id) if es_grupo else montos[montos.concepto_id == c.concepto_id]
        bandera = "comparable_por_programa" if restr else "comparable_por_concepto"
        for y in anios_todos:
            ev = _eventos(li, y, "conceptos_afectados", hojas)
            if restr and len(ev):
                ev = ev.loc[ev.programas_afectados.map(lambda s: bool(set(_lista(s)) & restr)).astype(bool) |
                        (ev[bandera].map(_bool) != False).astype(bool)]  # noqa: E712
            tiene_b = any((h, y) in nodos_base for h in hojas)
            tiene_d = any((h, y) in nodos_doc for h in hojas)
            peso = _peso_nuevos(x, y) if (y in anios_con_montos and y - 1 in anios_con_montos and tiene_b) else None
            comp, motivo = comparabilidad(y, anios_con_montos, ev, bandera, peso)
            if y in anios_con_montos and not tiene_b:
                comp = "sin_montos"
                motivo = ("; ".join(f"{e.id_evento} {e.tipo_cambio}" for e in
                                    li.loc[li.conceptos_afectados.map(lambda s: bool(set(_lista(s)) & hojas)).astype(bool)
                                           & (li.anio_min.fillna(9999) <= y).astype(bool)].itertuples())
                          or "sin nodo en la base")
            filas.append(dict(concepto_id=c.concepto_id, anio=y, nivel=c.nivel, estado_anio=estado_anio[y],
                              origen_nodos=("base" if tiene_b else "documental" if tiene_d else "sin_nodo"),
                              con_montos=bool(y in anios_con_montos and tiene_b),
                              comparable_con_anio_anterior=comp, motivo_quiebre=motivo or None,
                              peso_nodos_nuevos=(round(peso, 4) if peso is not None else None),
                              eventos_linaje=";".join(ev.id_evento) or None))
    cobertura = pd.DataFrame(filas)
    cobertura["version_tabla"] = VERSION_TRAZA

    # ---------------- programas sociales
    ue = con.execute("SELECT anio, sec_ejec, nivel_gobierno, ejecutora_nombre FROM dim_unidad_ejecutora").df()
    ue["anio"] = ue.anio.astype(int)
    nom_act = con.execute("SELECT anio, actividad_accion_obra, actividad_accion_obra_nombre FROM nom_actividad").df()
    nom_act["anio"] = nom_act.anio.astype(int)
    ps_rows, ps_ue, ps_la = [], [], []
    for p in d["ps"]["programas"]:
        idf = p["identificacion"]
        crit = "ejecutora" if idf.get("sec_ejec") else "actividad_municipal"
        cods = idf.get("sec_ejec") or idf.get("actividad_accion_obra")
        la = p.get("linea_aparte") or {}
        for cod in (cods if la else []):   # E3: línea aparte (p. ej. transferido a municipalidades)
            for cl in la["clasificadores"]:
                ps_la.append(dict(id_programa_social=p["id"], tema_id="ps_" + p["id"], linea_aparte_id=la["id"],
                                  rotulo=la["rotulo"], obligatoria=la["obligatoria"],
                                  nivel_gobierno=idf["nivel_gobierno"], sec_ejec=cod, clasificador_gasto=cl,
                                  version_tabla=VERSION_TRAZA))
        for cod in cods:
            ps_ue.append(dict(id_programa_social=p["id"], criterio=crit, nivel_gobierno=idf["nivel_gobierno"],
                              sec_ejec=cod if crit == "ejecutora" else None,
                              actividad_accion_obra=cod if crit != "ejecutora" else None,
                              tema_id="ps_" + p["id"], version_tabla=VERSION_TRAZA))
        for y in anios:
            if crit == "ejecutora":
                n = ue[(ue.anio == y) & ue.sec_ejec.isin(cods) & (ue.nivel_gobierno == idf["nivel_gobierno"])].ejecutora_nombre
            else:
                n = nom_act[(nom_act.anio == y) & nom_act.actividad_accion_obra.isin(cods)].actividad_accion_obra_nombre
            nombre_mef = n.iloc[0] if len(n) else None
            et = etiqueta_programa_social(p["nombres"], y, nombre_mef)
            if not et:
                continue  # el programa no existía ese año
            ps_rows.append(dict(id_programa_social=p["id"], anio=y, tema_id="ps_" + p["id"], alcance="programa_social",
                                criterio=crit, nivel_gobierno=idf["nivel_gobierno"], codigos=";".join(cods),
                                nombre_mef=nombre_mef, con_registro_en_anio=bool(len(n)), **et,
                                nombre_oficial=p.get("nombre_oficial"), sector_adscripcion=p.get("sector_adscripcion"),
                                vigencia_hasta=p.get("hasta"), financiamiento_w2=p.get("financiamiento_w2"),
                                nota=p.get("nota"), id_w2=p.get("id_w2"),
                                linea_aparte_id=la.get("id"), linea_aparte_rotulo=la.get("rotulo"),
                                linea_aparte_obligatoria=bool(la.get("obligatoria", False)),
                                revisado_por=d["ps"]["revisado_por"], version_tabla=VERSION_TRAZA))
    dim_ps = pd.DataFrame(ps_rows)
    rel_ps = pd.DataFrame(ps_ue)
    rel_la = pd.DataFrame(ps_la, columns=["id_programa_social", "tema_id", "linea_aparte_id", "rotulo", "obligatoria",
                                          "nivel_gobierno", "sec_ejec", "clasificador_gasto", "version_tabla"])
    con.register("rel_ps_df", rel_ps)
    con.execute("CREATE OR REPLACE TABLE rel_programa_social_ejecutora AS SELECT * FROM rel_ps_df")
    con.unregister("rel_ps_df")
    JOIN_PS = """f.nivel_gobierno = p.nivel_gobierno AND ((p.sec_ejec IS NOT NULL AND f.sec_ejec = p.sec_ejec)
                 OR (p.actividad_accion_obra IS NOT NULL AND f.actividad_accion_obra = p.actividad_accion_obra))"""
    fin = con.execute(f"""
        SELECT f.anio, p.id_programa_social, f.programa_ppto, f.producto_proyecto, f.tipo_act_proy,
               count(DISTINCT f.sec_ejec) AS n_ejecutoras,
               sum(f.devengado) FILTER (WHERE f.bloque_consolidado = 'gasto_final')::DOUBLE AS devengado_gasto_final,
               sum(f.pim) FILTER (WHERE f.bloque_consolidado = 'gasto_final')::DOUBLE AS pim_gasto_final,
               sum(f.devengado) FILTER (WHERE f.bloque_consolidado <> 'gasto_final')::DOUBLE AS devengado_fuera_del_gasto_final
        FROM fact f JOIN rel_programa_social_ejecutora p ON {JOIN_PS}
        GROUP BY ALL ORDER BY 1, 2, 3, 4, 5""").df()
    fin = fin.fillna({"devengado_gasto_final": 0.0, "pim_gasto_final": 0.0, "devengado_fuera_del_gasto_final": 0.0})
    fin["anio"] = fin.anio.astype(int)
    nprod = con.execute("""SELECT anio, programa_ppto, producto_proyecto, min(producto_proyecto_nombre) AS producto_proyecto_nombre,
                                  min(programa_ppto_nombre) AS programa_ppto_nombre
                           FROM traza_nodos GROUP BY 1, 2, 3""").df()
    nprod["anio"] = nprod.anio.astype(int)
    fin = fin.merge(nprod, how="left", on=["anio", "programa_ppto", "producto_proyecto"])
    fin.loc[fin.tipo_act_proy == "PROYECTO", "producto_proyecto_nombre"] = None
    fin["alcance"] = "programa_social"
    fin["nota_suma"] = "no se suma con conceptos ni con temas por función (R-GASTO-08b)"
    fin["version_tabla"] = VERSION_TRAZA
    sup_ps = con.execute(f"""SELECT count(*) FROM (SELECT {clave}, count(DISTINCT p.id_programa_social) n
                             FROM fact f JOIN rel_programa_social_ejecutora p ON {JOIN_PS} GROUP BY ALL HAVING n > 1)""").fetchone()[0]
    res.prueba("G-29", "Programas sociales: cada fila de la fact pertenece como máximo a un programa social",
               sup_ps == 0, {"filas_en_dos_programas": sup_ps})

    # ---------------- dim_tema_gasto v1.2
    conc_fun = set(map(tuple, con.execute(f"""SELECT DISTINCT f.anio::INTEGER, r.concepto_id, f.programa_ppto, f.funcion
                                              FROM fact f JOIN rel_concepto_nodo r ON {SQL_JOIN_CONCEPTO}""").fetchall()))
    tema = _dim_tema(con, d, temas, dim_ps, rel_ps, li, anios, anios_con_montos, montos_grupo, gr, nodos, conc_fun)
    for r in tema.drop_duplicates("tema_id").itertuples():
        validar_tema_id(r.tema_id, r.cadena)

    # ---------------- glosario
    glos = d["glosario"].copy()
    glos["version_glosario"] = "v2 (ronda2/w4_glosario_transferencias, adoptado por el dueño el 7/10/2026)"
    glos["version_tabla"] = VERSION_TRAZA

    return {"dim_programa": dim_programa, "dim_producto": prod, "dim_actividad": act, "dim_concepto": co,
            "rel_concepto_grupo": gr.assign(version_tabla=VERSION_TRAZA), "rel_concepto_nodo": rel,
            "rel_linaje": li, "rel_programa_politica": pol, "dim_programa_social": dim_ps,
            "rel_programa_social_ejecutora": rel_ps, "rel_programa_social_financiamiento": fin,
            "rel_programa_social_linea_aparte": rel_la,
            "cobertura_por_anio": cobertura, "dim_tema_gasto": tema, "dim_glosario_gasto": glos}


def _dim_tema(con, d, temas, dim_ps, rel_ps, li, anios, anios_con_montos, montos_grupo, gr, nodos,
              conc_fun) -> pd.DataFrame:
    rev = d["temas"]["revisado_por"]
    claves = con.execute("""SELECT DISTINCT anio, funcion, division_funcional, programa_ppto FROM fact
                            WHERE bloque_consolidado = 'gasto_final'""").df()
    claves["anio"] = claves.anio.astype(int)
    # montos de actividades por nodo y programa (para el peso de los nodos nuevos de los temas pp_)
    mpp = con.execute("""SELECT anio, programa_ppto, producto_proyecto, actividad_accion_obra, funcion,
                                sum(devengado)::DOUBLE AS dev FROM fact
                         WHERE bloque_consolidado = 'gasto_final' AND tipo_act_proy = 'ACTIVIDAD'
                           AND programa_ppto IN (SELECT unnest(?)) GROUP BY ALL""",
                      [sorted({c for t in temas if t["cadena"] in ("programa", "programa_x_funcion")
                               for c in t["programa_ppto"]})]).df()
    mpp["anio"] = mpp.anio.astype(int)
    filas = []
    base_cols = dict(programa_ppto=None, funcion=None, division_funcional=None, concepto_grupo_id=None,
                     nivel_gobierno=None, sec_ejec=None, actividad_accion_obra=None)
    for t in temas:
        cad = t["cadena"]
        for y in anios:
            k = claves[claves.anio == y]
            if cad == "funcion":
                vals = [dict(funcion=f) for f in t["funcion"] if f in set(k.funcion)]
                origen = ", ".join(t["funcion"])
            elif cad == "division":
                vals = [dict(funcion=f, division_funcional=v) for f in t["funcion"] for v in t["division_funcional"]
                        if ((k.funcion == f) & (k.division_funcional == v)).any()]
                origen = " / ".join(t["funcion"] + t["division_funcional"])
            elif cad == "programa":
                vals = [dict(programa_ppto=c) for c in t["programa_ppto"] if c in set(k.programa_ppto)]
                origen = ", ".join(t["programa_ppto"])
            elif cad == "programa_x_funcion":
                vals = [dict(programa_ppto=c, funcion=f) for c in t["programa_ppto"] for f in t["funcion"]
                        if ((k.programa_ppto == c) & (k.funcion == f)).any()]
                origen = " × ".join([", ".join(t["programa_ppto"]), ", ".join(t["funcion"])])
            elif cad == "concepto":
                vals = [dict(concepto_grupo_id=t["concepto_grupo_id"])]
                origen = t["concepto_grupo_id"] + " (ronda 2, W2)"
            # comparabilidad
            if cad in ("funcion", "division"):
                comp, mot = ("sin_anio_anterior", f"{y - 1} sin montos en la base") if y - 1 not in anios_con_montos \
                    else ("si", "temas por función: los quiebres de programas no aplican (R-GASTO-09)")
            elif cad == "concepto":
                hojas = set(gr.loc[gr.grupo_id == t["concepto_grupo_id"], "concepto_id"])
                restr = set(gr.loc[gr.grupo_id == t["concepto_grupo_id"], "restriccion_programa_ppto"].dropna())
                band = "comparable_por_programa" if restr else "comparable_por_concepto"
                ev = _eventos(li, y, "conceptos_afectados", hojas)
                if restr and len(ev):
                    ev = ev.loc[ev.programas_afectados.map(lambda s: bool(set(_lista(s)) & restr)).astype(bool) |
                            (ev[band].map(_bool) != False).astype(bool)]  # noqa: E712
                comp, mot = comparabilidad(y, anios_con_montos, ev, band, _peso_nuevos(montos_grupo(t["concepto_grupo_id"]), y))
            else:
                cods = set(t["programa_ppto"])
                ev = _eventos(li, y, "programas_afectados", cods)
                x = mpp[mpp.programa_ppto.isin(cods)]
                if cad == "programa_x_funcion":
                    x = x[x.funcion.isin(t["funcion"])]
                    # un evento con conceptos afecta al cruce solo si esos conceptos tienen gasto en esa función
                    rel_ev = ev.conceptos_afectados.map(lambda s: not _lista(s) or any(
                        (y, c, p, f) in conc_fun for c in _lista(s) for p in cods for f in t["funcion"]))
                    ev = ev.loc[rel_ev.astype(bool)]
                x = x.groupby(["anio", "programa_ppto", "producto_proyecto", "actividad_accion_obra"], as_index=False).dev.sum()
                if y - 1 in anios_con_montos and x[x.anio == y - 1].dev.sum() == 0 and x[x.anio == y].dev.sum() != 0:
                    comp, mot = "sin_anio_anterior", f"sin gasto del tema en {y - 1}"
                else:
                    comp, mot = comparabilidad(y, anios_con_montos, ev, "comparable_por_programa", _peso_nuevos(x, y))
            for v in vals:
                filas.append({**base_cols, **v, "anio": y, "tema_id": t["tema_id"], "cadena": cad,
                              "codigo_origen": origen, "nivel": NIVEL_CADENA[cad], "llave_union": LLAVE_CADENA[cad],
                              "alternativa_de": t.get("alternativa_de"), "etiqueta_ciudadana": t["etiqueta_ciudadana"],
                              "excluye_transferencias": True, "comparable_con_anio_anterior": comp,
                              "motivo_quiebre": mot or None})
    # programas sociales
    for r in dim_ps.itertuples():
        if not r.con_registro_en_anio:
            continue
        ev = _eventos(li, r.anio, "programas_sociales_afectados", {r.id_programa_social})
        primero = not ((dim_ps.id_programa_social == r.id_programa_social) & (dim_ps.anio == r.anio - 1)
                       & dim_ps.con_registro_en_anio).any()
        if primero and r.anio - 1 in anios_con_montos:
            comp, mot = "sin_anio_anterior", "primer año del programa social en la base"
        else:
            comp, mot = comparabilidad(r.anio, anios_con_montos, ev, "comparable_por_programa_social", None)
        for u in rel_ps[rel_ps.id_programa_social == r.id_programa_social].itertuples():
            filas.append({**base_cols, "anio": r.anio, "tema_id": r.tema_id, "cadena": "programa_social",
                          "codigo_origen": (f"ejecutora {u.sec_ejec}" if u.sec_ejec else f"actividad {u.actividad_accion_obra}"),
                          "nivel": NIVEL_CADENA["programa_social"], "llave_union": LLAVE_CADENA["programa_social"],
                          "nivel_gobierno": u.nivel_gobierno, "sec_ejec": u.sec_ejec,
                          "actividad_accion_obra": u.actividad_accion_obra, "alternativa_de": None,
                          "etiqueta_ciudadana": r.etiqueta, "excluye_transferencias": True,
                          "comparable_con_anio_anterior": comp, "motivo_quiebre": mot or None,
                          "revisado_por": d["ps"]["revisado_por"]})
    tema = pd.DataFrame(filas)
    tema["version"] = VERSION_TEMA
    tema["revisado_por"] = tema.get("revisado_por").fillna(rev) if "revisado_por" in tema else rev
    cols = ["anio", "tema_id", "cadena", "codigo_origen", "nivel", "llave_union", "programa_ppto", "funcion",
            "division_funcional", "concepto_grupo_id", "nivel_gobierno", "sec_ejec", "actividad_accion_obra",
            "alternativa_de", "etiqueta_ciudadana", "excluye_transferencias", "comparable_con_anio_anterior",
            "motivo_quiebre", "version", "revisado_por"]
    return tema[cols]


def pruebas_temas(con, res, tema: pd.DataFrame, anios: list[int], dim_programa: pd.DataFrame, controles: dict) -> None:
    """G-03 v1.2 (todos los alcances) y G-32 (las vistas reproducen las cifras aprobadas). Requiere las tablas
    dim_tema_gasto, rel_concepto_nodo, rel_concepto_grupo y rel_programa_social_ejecutora y las vistas cargadas."""
    det = {}
    ok = True
    # (1) gramática, prefijo = cadena y una sola definición por tema
    malos = [t for t in tema.drop_duplicates(["tema_id", "cadena"]).itertuples()
             if not GRAMATICA_TEMA.fullmatch(t.tema_id) or PREFIJO_CADENA[t.tema_id.split("_", 1)[0]] != t.cadena]
    defs = tema.groupby("tema_id")[["cadena", "etiqueta_ciudadana", "alternativa_de"]].nunique(dropna=False)
    det["gramatica_o_prefijo"] = [t.tema_id for t in malos]
    det["temas_con_varias_cadenas"] = list(defs[defs.cadena > 1].index)
    ok &= not malos and not len(det["temas_con_varias_cadenas"])
    # (2) cada tema tiene filas en algún año; los años sin filas (sus códigos no existen ese año) se informan
    det["tema_sin_filas_en_anio"] = [(t, a) for t in sorted(set(tema.tema_id)) for a in anios
                                     if not ((tema.tema_id == t) & (tema.anio == a)).any()]
    vacios = [t for t in sorted(set(tema.tema_id)) if not (tema.tema_id == t).any()]
    ok &= not vacios
    # (3) clave única de la tabla
    dup = int(tema.duplicated(["anio", "tema_id", "programa_ppto", "funcion", "division_funcional", "sec_ejec",
                               "actividad_accion_obra"]).sum())
    det["filas_repetidas"] = dup
    ok &= dup == 0
    # (4) no superposición estructural dentro de cada cadena (llaves por igualdad), salvo alternativa_de
    princ = tema[tema.alternativa_de.isna()]
    llaves = {"funcion": ["funcion"], "division": ["funcion", "division_funcional"], "programa": ["programa_ppto"],
              "programa_x_funcion": ["programa_ppto", "funcion"],
              "programa_social": ["nivel_gobierno", "sec_ejec", "actividad_accion_obra"]}
    choques = {}
    for cad, ll in llaves.items():
        x = princ[princ.cadena == cad]
        c = x.groupby(["anio"] + ll, dropna=False).tema_id.nunique()
        if (c > 1).any():
            choques[cad] = [list(map(str, i)) for i in c[c > 1].index]
    # (5) no superposición con datos: conceptos (grupos no alternativos) y programas sociales sobre la fact
    from .gasto import CLAVE_FACT
    # v_gasto_tematico no trae categoria_transferencia (en el gasto final es nula o gasto_final_externo y no cambia el tema)
    clave = ", ".join(c for c in CLAVE_FACT if c != "categoria_transferencia")
    for cad in ("concepto", "programa_social"):
        n = con.execute(f"""SELECT count(*) FROM (SELECT {clave}, count(DISTINCT tema_id) n FROM v_gasto_tema_interna
                            WHERE cadena = '{cad}' AND tema_id IN (SELECT DISTINCT tema_id FROM dim_tema_gasto
                                                                  WHERE alternativa_de IS NULL)
                            GROUP BY ALL HAVING n > 1)""").fetchone()[0]
        if n:
            choques[cad + "_datos"] = n
    det["superposicion"] = choques
    ok &= not choques
    # (6) cada programa presupuestal del año está mapeado a un tema pp_ o marcado sin_tema
    dp = dim_programa[dim_programa.origen == "base"]
    sin = dp[dp.tema_programa.isna()]
    det["programas_sin_marca"] = len(sin)
    ok &= len(sin) == 0
    res.prueba("G-03", "dim_tema_gasto v1.2, todos los alcances: gramática y prefijo = cadena; cada tema en cada año; "
               "clave única; dentro de cada cadena ningún sol en dos temas (salvo alternativa_de); cada programa del "
               "año con tema pp_ o sin_tema", ok, det)
    # G-32: las vistas reproducen las cifras aprobadas
    obt = {}
    for tid, k in (("cpt_grupo_expan", "grupo_expan"), ("cpt_grupo_opcion_c", "grupo_opcion_c"),
                   ("cpt_grupo_anemia_estricta", "grupo_anemia_estricta"), ("pp_1001_dit", "pp_1001_dit")):
        obt[k] = {int(a): round(float(v) / 1e6) for a, v in con.execute(
            "SELECT anio, sum(devengado) FROM gasto_tema(?) GROUP BY 1", [tid]).fetchall()}
    res.prueba("G-32", "El acceso del motor (macro gasto_tema) reproduce las cifras aprobadas", obt == controles,
               {"obtenido": obt})
    # G-38 (E3, 8/10/2026): línea aparte de los programas sociales. La vista reproduce, por programa y año, todo lo que
    # la ejecutora registra con esos clasificadores (fuera del gasto final) y no comparte ninguna fila con el gasto
    # final (no se puede sumar a gasto_tema). Cifras del análisis del 8/10 para Llamkasun: 605,6 / 535,7 / 409,0.
    la = con.execute("""
        WITH v AS (SELECT id_programa_social, anio, sum(devengado) AS d FROM v_programa_social_linea_aparte GROUP BY 1, 2),
             f AS (SELECT p.id_programa_social, f.anio, sum(f.devengado) AS d,
                          count(*) FILTER (WHERE f.bloque_consolidado = 'gasto_final') AS en_gasto_final
                   FROM fact f JOIN (SELECT DISTINCT id_programa_social, nivel_gobierno, sec_ejec, clasificador_gasto
                                     FROM rel_programa_social_linea_aparte) p
                     ON f.nivel_gobierno = p.nivel_gobierno AND f.sec_ejec = p.sec_ejec
                    AND f.clasificador_gasto = p.clasificador_gasto GROUP BY 1, 2)
        SELECT coalesce(v.id_programa_social, f.id_programa_social), coalesce(v.anio, f.anio), v.d, f.d, f.en_gasto_final
        FROM v FULL JOIN f USING (id_programa_social, anio) ORDER BY 1, 2""").fetchall()
    res.prueba("G-38", "Línea aparte de los programas sociales (v_programa_social_linea_aparte) = lo registrado por la "
               "ejecutora con esos clasificadores, sin filas del gasto final (tolerancia 0)",
               len(la) > 0 and all(vd == fd and not n for _, _, vd, fd, n in la),
               {f"{i}/{a}": round(float(vd or 0) / 1e6, 1) for i, a, vd, _, _ in la})
