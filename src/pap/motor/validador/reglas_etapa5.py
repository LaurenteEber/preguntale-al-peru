"""Etapa 5 del validador (grupo C): vigencia, series y quiebres.

Reglas: R-ENC-13, R-ENC-14, R-REG-10, R-GASTO-08, R-GASTO-09, R-CRUCES-04, R-LENGUAJE-04 (ámbito «cifra») y R-GASTO-08b
(ámbito «respuesta»: compara cifras de gasto entre sí, así que la corre `evaluar_respuesta`).

La serie de una cifra llega en `c.serie` (filas del cubo del mismo indicador, nivel y territorio) y la comparación en
`c.comparacion` (fila del año con que se compara, con `prueba_cambio`), contrato §2e. Los umbrales, listas y textos se leen
de `reglas.json` con `ctx.param`; nada de lo que decide una regla está escrito aquí a mano.

Las ayudas de este módulo (años de la consulta, quiebres tipados, cadena de un tema de gasto) las usa también
`reglas_etapa8_10.py`.
"""
from __future__ import annotations

import re

from .nucleo import CampoFaltante, Campos, Resultado, aplica, regla

# ======================================================================= ayudas comunes


def _dict(x) -> dict:
    """Fila de la serie o de la comparación como dict (puede llegar como dict o como Campos/Cifra)."""
    if x is None:
        return {}
    if isinstance(x, Campos):
        return x.datos()
    return dict(x)


def _int(v):
    try:
        return None if v is None else int(v)
    except (TypeError, ValueError):
        return None


def filas_serie(c) -> list[dict]:
    return [_dict(f) for f in (c.get("serie") or [])]


def fila_comparacion(c) -> dict:
    return _dict(c.get("comparacion"))


def anios_consulta(c) -> list[int]:
    """Años que toca la consulta de la cifra: su año, los de la serie, el de la comparación y el periodo agrupado."""
    anios = {_int(c.get("anio"))}
    anios |= {_int(f.get("anio")) for f in filas_serie(c)}
    anios.add(_int(fila_comparacion(c).get("anio")))
    for a in c.get("periodo_agrupado") or []:
        anios.add(_int(a))
    return sorted(a for a in anios if a is not None)


def anios_comparados(c) -> tuple[int, int] | None:
    """(anio_inicio, anio_fin) de la comparación o de la serie pedida; None si la cifra va sola."""
    comp = fila_comparacion(c)
    if comp.get("anio") is not None and c.get("anio") is not None:
        a, b = sorted((_int(comp["anio"]), _int(c.anio)))
        return a, b
    serie = [_int(f.get("anio")) for f in filas_serie(c)] + [_int(c.get("anio"))]
    serie = [a for a in serie if a is not None]
    if len(set(serie)) >= 2:
        return min(serie), max(serie)
    return None


def quiebres(c) -> list[dict]:
    """indicador.quiebres normalizado: [{anio, tipo, descripcion, comparable_con: [int]}]."""
    out = []
    for q in c.get("quiebres") or []:
        q = _dict(q)
        out.append({"anio": _int(q.get("anio")), "tipo": q.get("tipo"), "descripcion": q.get("descripcion"),
                    "comparable_con": [_int(x) for x in (q.get("comparable_con") or [])]})
    return [q for q in out if q["anio"] is not None]


def corta_comparacion(tipo: str | None, q: int, a: int, b: int) -> bool:
    """¿El quiebre del año q impide comparar a con b (a < b)? Decisión del dueño (11/10/2026, P4; cierra H7): un quiebre
    por modo de entrevista (ENDES 2020) solo excluye ese punto —no se compara con ese año, pero sí a través de él, como
    hace el INEI (2024/2019, 2025/2021) y el ejemplo de R-ENC-13—; los demás quiebres (criterio, marco, cuestionario)
    cortan la serie en tramos."""
    if (tipo or "modo") in ("modo", "modo_entrevista"):
        return q in (a, b)
    return a < q <= b


def anios_quiebre_indicador(c) -> set[int]:
    return {_int(a) for a in (c.get("anios_con_quiebre") or []) if _int(a) is not None} | {q["anio"] for q in quiebres(c)}


_RX_ANIO_CATALOGO = re.compile(r"\b((?:19|20)\d\d)\s*:")


def anios_quiebre_catalogo(c, ctx) -> set[int]:
    """parse(anios_con_quiebre) del catálogo: es texto libre («2020: …; 2024: …»); se toman los años que abren una
    entrada (seguidos de «:»), no los que aparecen dentro de una descripción (p. ej. «RM 363-2022»)."""
    fila = (ctx.catalogo or {}).get(c.get("fuente_principal")) or {}
    v = fila.get("anios_con_quiebre")
    if isinstance(v, list):
        return {_int(a) for a in v if _int(a) is not None}
    return {int(a) for a in _RX_ANIO_CATALOGO.findall(str(v or ""))}


def criterio_de(fila: dict, c=None):
    """Criterio de medición de una fila (columna `criterio` del cubo o `criterio_medicion` del indicador). Si la fila es
    del mismo indicador que la cifra y no lo trae, hereda el de la cifra."""
    v = fila.get("criterio") or fila.get("criterio_medicion")
    if v is None and c is not None and fila.get("indicador_id") in (None, c.get("indicador_id")):
        v = c.get("criterio") or c.get("criterio_medicion")
    return v


def fila_del_anio(c, anio: int) -> dict:
    """La fila (de la serie, la comparación o la cifra misma) de un año."""
    if _int(c.get("anio")) == anio:
        return c.datos()
    comp = fila_comparacion(c)
    if _int(comp.get("anio")) == anio:
        return comp
    for f in filas_serie(c):
        if _int(f.get("anio")) == anio:
            return f
    return {}


def filas_tema_gasto(ctx, tema_id, anio=None) -> list[dict]:
    """Filas de dim_tema_gasto (ctx.tema_gasto) de un tema, y de un año si se da."""
    t = getattr(ctx, "tema_gasto", None)
    if t is None or not tema_id:
        return []
    m = t["tema_id"] == tema_id
    if anio is not None:
        m &= t["anio"] == int(anio)
    return t[m].to_dict("records")


def cadena_de(c, ctx) -> str | None:
    """Cadena de un tema de gasto: la declarada en la cifra; si no, la de dim_tema_gasto (ctx.tema_gasto); si no, la de
    temas_iniciales de R-GASTO-08; si no, la que implica el prefijo (R-GASTO-08b.prefijo_cadena)."""
    if isinstance(c, dict):
        c = Campos(c)
    if c.get("cadena"):
        return c.cadena
    tema = c.get("tema_id")
    if not tema:
        return None
    filas = filas_tema_gasto(ctx, tema)
    if filas and filas[0].get("cadena"):
        return filas[0]["cadena"]
    ini = (ctx.param("R-GASTO-08", "temas_iniciales") or {}).get(tema) or {}
    if ini.get("cadena"):
        return ini["cadena"]
    return (ctx.param("R-GASTO-08b", "prefijo_cadena") or {}).get(prefijo_tema(tema, ctx))


def prefijo_tema(tema_id: str, ctx) -> str | None:
    """Prefijo de un tema según la gramática de R-GASTO-08b (el más largo que calce: ppxfun_ antes que pp_)."""
    pref = sorted((ctx.param("R-GASTO-08b", "prefijo_cadena") or {}).keys(), key=len, reverse=True)
    return next((p for p in pref if str(tema_id).startswith(p + "_")), None)


def es_aplicable(rid: str, c, ctx) -> bool:
    """aplica_a de una regla sobre una cifra (las reglas de respuesta lo comprueban cifra por cifra)."""
    return aplica(ctx.regla(rid), c)


def mensaje(rid: str, ctx, **valores) -> str | None:
    """mensaje_usuario de la regla, con los {campos} que se conocen rellenados (los demás quedan para la plantilla)."""
    m = ctx.regla(rid).get("mensaje_usuario")
    if not m:
        return None
    m = m.strip()
    if m.startswith("«") and m.endswith("»") and m.count("«") == 1:
        m = m[1:-1]  # el mensaje entero entre comillas: al usuario va sin ellas (auditoría H-20)
    for k, v in valores.items():
        m = m.replace("{" + k + "}", str(v))
    return m


# ======================================================================= R-ENC-13

@regla("R-ENC-13")
def r_enc_13(c, ctx):
    """Quiebres metodológicos y el año 2020 en series de encuesta."""
    rid = "R-ENC-13"
    fuente = c.req("fuente_principal")
    c.req("anio")
    anios = anios_consulta(c)
    mixto = (ctx.param(rid, "anios_modo_mixto") or {}).get(fuente, [])
    con_quiebre = set(mixto) | anios_quiebre_indicador(c)
    lo, hi = min(anios), max(anios)
    en_serie = sorted(q for q in con_quiebre if lo <= q <= hi)
    if not en_serie:
        return None
    defecto = ctx.param(rid, "comparable_en_quiebre_por_defecto") or {}
    claves = [f"{fuente}.{c.get(k)}" for k in ("concepto_medido", "tema", "indicador_id") if c.get(k)]
    qs = quiebres(c)

    def comparable(a):
        if any(a in q["comparable_con"] for q in qs if q["anio"] == a):
            return True
        return any(a in (defecto.get(k) or []) for k in claves)

    no_comp = [a for a in en_serie if not comparable(a)]
    if no_comp:
        res = [Resultado(rid, "advertir", "quiebre", clausula="serie abarca un año con quiebre no comparable",
                         detalle={"anios_quiebre": no_comp, "excluir_de_tendencia": no_comp, "fuente": fuente},
                         mensaje=mensaje(rid, ctx), aviso="quiebre_modo_entrevista")]
        bio = ctx.param(rid, "biomedicos_endes_2020")
        mixto_endes = (ctx.param(rid, "anios_modo_mixto") or {}).get("INEI-ENDES", [])
        # H-20: solo si la cifra o una fila de la serie es del año biomédico afectado (no por abarcarlo)
        filas_bio = [a for a in no_comp if a in mixto_endes and a in anios]
        if bio and fuente == "INEI-ENDES" and filas_bio:
            res.append(Resultado(rid, bio, "quiebre", clausula="biomedicos_endes_2020: la cifra o fila de 2020",
                                 detalle={"anios": filas_bio}, modificador=True))
        return res
    # años con quiebre declarados comparables (pobreza monetaria ENAHO 2020–2021): entran a la serie, con marca
    return Resultado(rid, "rotular", "quiebre", clausula="quiebre declarado comparable: entra a la serie con marca",
                     detalle={"anios_quiebre_comparables": en_serie}, rotulo="quiebre_comparable")


# ======================================================================= R-ENC-14

@regla("R-ENC-14")
def r_enc_14(c, ctx):
    """Anemia: criterio obligatorio y series sin mezclar RM 363-2022 y RM 251-2024."""
    rid = "R-ENC-14"
    if c.req("tema") != "anemia":
        return None
    crit = c.get("criterio_medicion") or c.get("criterio")
    if crit is None:
        return Resultado(rid, "suprimir", "metadato_faltante", clausula="criterio_medicion IS NULL",
                         detalle={"campo": "criterio_medicion"})
    tramos: dict = {crit: [_int(c.get("anio"))]}
    for f in filas_serie(c) + ([fila_comparacion(c)] if fila_comparacion(c) else []):
        k = criterio_de(f, c)
        tramos.setdefault(k, []).append(_int(f.get("anio")))
    res = []
    if len(tramos) > 1:
        res.append(Resultado(rid, "bloquear_cruce", "criterio_distinto",
                             clausula="COUNT(DISTINCT criterio_medicion) > 1 en la serie",
                             detalle={"tramos": {str(k): sorted(a for a in v if a is not None) for k, v in tramos.items()},
                                      "regla_tramos": ctx.param(rid, "regla_tramos")},
                             mensaje=mensaje(rid, ctx)))
    # H-12 (enunciado y regla_tramos: «cifra principal = criterio RM 251-2024 del año más reciente»): una cifra principal
    # con el criterio anterior, si existe la del criterio vigente del mismo año y territorio, va solo como referencia.
    criterios = ctx.param(rid, "criterios") or []
    if len(criterios) >= 2 and crit == criterios[0] and (c.get("es_principal") or c.get("rol") == "principal"):
        vigente = _indicador_vigente(c, ctx, criterios[-1])
        if vigente:
            res.append(Resultado(rid, "advertir", "criterio_anterior",
                                 clausula="principal con criterio anterior y existe el vigente: solo como referencia",
                                 detalle={"criterio": crit, "principal_sugerida": vigente,
                                          "regla_tramos": ctx.param(rid, "regla_tramos")},
                                 aviso="criterio_anterior_referencia", modificador=bool(res)))
    return res or None


def _indicador_vigente(c, ctx, criterio_vigente) -> str | None:
    """Id del indicador del mismo concepto con el criterio vigente que tiene fila del mismo año, nivel y territorio."""
    for iid, ind in (ctx.indicadores or {}).items():
        if iid == c.get("indicador_id") or ind.get("criterio_medicion") != criterio_vigente:
            continue
        if ind.get("concepto_medido") != c.get("concepto_medido") or ind.get("fuente_principal") != c.get("fuente_principal"):
            continue
        anio = _int(c.get("anio"))
        if ctx.cubo is not None:
            if ctx.fila_cubo(iid, anio, c.get("nivel"), str(c.get("territorio_id"))):
                return iid
        elif anio in [_int(a) for a in (ind.get("anios_disponibles") or [])]:
            return iid
    return None


# ======================================================================= R-REG-10

@regla("R-REG-10")
def r_reg_10(c, ctx):
    """Quiebres de serie en registros: no se calcula variación ni se agrupan años a través de un quiebre."""
    rid = "R-REG-10"
    c.req("anio")
    qs = sorted(anios_quiebre_indicador(c) | anios_quiebre_catalogo(c, ctx))
    desc = {q["anio"]: q.get("descripcion") for q in quiebres(c)}
    par = anios_comparados(c)
    if par:
        ini, fin = par
        cruzan = [q for q in qs if ini < q <= fin]
        if cruzan:
            q = cruzan[0]
            return Resultado(rid, "bloquear_cruce", "quiebre", clausula="serie.anio_ini < quiebre <= serie.anio_fin",
                             detalle={"anio_ini": ini, "anio_fin": fin, "quiebres": cruzan},
                             mensaje=mensaje(rid, ctx, **{"año": q, "motivo": desc.get(q) or "cambio de registro"}))
    per = [_int(a) for a in (c.get("periodo_agrupado") or []) if _int(a) is not None]
    if len(per) >= 2:
        d, h = min(per), max(per)
        cruzan = [q for q in qs if d < q <= h]
        if cruzan:
            # una cifra agrupada con años de los dos tramos no es una cifra válida: se suprime (lectura restrictiva)
            return Resultado(rid, "bloquear", "quiebre", clausula="agrupar_anios incluye años de ambos tramos",
                             detalle={"periodo_agrupado": [d, h], "quiebres": cruzan})
    return None


# ======================================================================= R-GASTO-08

def _transferido(c):
    """Monto «transferido a municipalidades» (nombre del contrato; se acepta el alias del analista)."""
    v = c.get("transferido_municipalidades")
    return v if v is not None else c.get("monto_transferido_municipalidades")

@regla("R-GASTO-08")
def r_gasto_08(c, ctx):
    """Etiquetado temático con dim_tema_gasto v1.2: tema y cadena declarados, rótulo ciudadano y nombre por año."""
    rid = "R-GASTO-08"
    p = ctx.regla(rid)["parametros"]
    bloque = c.get("bloque_consolidado")
    if bloque is not None and bloque != "gasto_final":
        return Resultado(rid, "bloquear", "fuera_de_tema", clausula="solo filas con bloque_consolidado = 'gasto_final'",
                         detalle={"bloque_consolidado": bloque})
    tema = c.req("tema_id")
    anio = c.req("anio")
    # versión aprobada de dim_tema_gasto POR AÑO (H-10): (anio, tema_id) en ctx.tema_gasto con versión mayor.menor igual a
    # parametros.version_dim_tema_gasto («1.2» ≈ «1.2.0»); la versión que traiga la fila también se compara así
    esperada = str(p["version_dim_tema_gasto"])

    def aprobada(v) -> bool:
        return v is not None and (str(v) == esperada or str(v).startswith(esperada + "."))

    tablas = ((ctx.manifiestos or {}).get("s3_gasto") or {}).get("tablas") or {}
    version = c.get("version_tema") or c.get("version_dim_tema_gasto")
    if getattr(ctx, "tema_gasto", None) is not None:
        filas_v = filas_tema_gasto(ctx, tema, anio)
        sin_version = not filas_v or not any(aprobada(f.get("version")) for f in filas_v)
    else:  # sin la tabla en el contexto: al menos que esté publicada en el manifiesto del gasto
        filas_v, sin_version = [], "dim_tema_gasto" not in tablas
    if sin_version or (version is not None and not aprobada(version)):
        return Resultado(rid, "bloquear", "tema_sin_version", clausula="el año no tiene versión aprobada de dim_tema_gasto",
                         detalle={"anio": anio, "tema_id": tema, "version_fila": version,
                                  "versiones_tabla": sorted({str(f.get("version")) for f in filas_v}),
                                  "version_esperada": esperada})
    if prefijo_tema(tema, ctx) == "cpt":
        cols = [x.lower() for x in ((tablas.get("fact_gasto_territorial") or {}).get("columnas") or [])]
        trae = c.get("trae_actividad") if c.get("trae_actividad") is not None else c.get("tiene_actividad")
        if trae is False or (trae is None and "actividad_accion_obra" not in cols):
            return Resultado(rid, "bloquear", "tema_sin_actividad",
                             clausula="tema cpt_ y la fact no trae ACTIVIDAD_ACCION_OBRA", detalle={"tema_id": tema})
    cadena = cadena_de(c, ctx)
    if cadena is None:
        raise CampoFaltante("cadena")
    # programa social con línea aparte obligatoria (ps_empleo_temporal: «transferido a municipalidades»)
    tps = (p.get("temas_ps") or {}).get(tema)
    if tps:
        transferido = _transferido(c)
        if transferido is None:
            return Resultado(rid, "bloquear", "linea_aparte_faltante",
                             clausula=f"{tema}: falta el monto «{tps.get('linea_obligatoria')}»",
                             detalle={"tema_id": tema, "linea_obligatoria": tps.get("linea_obligatoria")})
    ini = (p.get("temas_iniciales") or {}).get(tema) or {}
    tg = filas_tema_gasto(ctx, tema, anio)
    rotulo = c.get("etiqueta_ciudadana") or (tg[0].get("etiqueta_ciudadana") if tg else None) or ini.get("etiqueta_ciudadana")
    detalle = {"tema_id": tema, "cadena": cadena, "version": p["version_dim_tema_gasto"]}
    if prefijo_tema(tema, ctx) == "ps":
        prog = c.get("programa_social") or tema.split("_", 1)[1]
        nom = ((p.get("nombres") or {}).get("mef_vs_vigente") or {}).get(prog) or {}
        propio = (nom.get("por_anio") or {}).get(str(anio))
        if propio:
            rotulo = propio
            mef = nom.get("nombre_mef")
            if mef and mef.lower() != propio.lower():
                rotulo += f" (en el presupuesto del MEF figura como {mef})"
        if tps:
            detalle["linea_aparte"] = {"texto": tps.get("linea_obligatoria"), "monto": _transferido(c),
                                       "se_suma": False}
    if rotulo is None:
        raise CampoFaltante("etiqueta_ciudadana")
    return Resultado(rid, "rotular", "tema_gasto", clausula="rótulo := etiqueta_ciudadana / nombre propio por año",
                     detalle=detalle, rotulo=rotulo)


# ======================================================================= R-GASTO-09

def _no_comparable_gasto(c, ctx, t: int, funcional: bool) -> tuple[bool, str | None]:
    """no_comparable(concepto, t) de R-GASTO-09 con lo que trae la cifra y dim_tema_gasto: comparable_con_anio_anterior
    (de ctx.tema_gasto para el tema y el año, o de la fila), peso de nodos nuevos, quiebres tipados del indicador
    (rel_linaje) y anios_con_quiebre. En temas fun_/div_ los quiebres de programas no aplican: no se usan los quiebres
    de tipo programa ni anios_con_quiebre (derivado de rel_linaje), auditoría C-3."""
    fila = fila_del_anio(c, t)
    tg = filas_tema_gasto(ctx, c.get("tema_id"), t)
    marca = fila.get("comparable_con_anio_anterior")
    if marca is None and tg:
        marca = tg[0].get("comparable_con_anio_anterior")
    if marca is False or str(marca).lower() == "no":
        motivo = tg[0].get("motivo_quiebre") if tg else None
        return True, motivo or "comparable_con_anio_anterior = no"
    umbral = ctx.param("R-GASTO-09", "umbral_nodos_nuevos_pct")
    peso = fila.get("peso_nodos_nuevos") if fila.get("peso_nodos_nuevos") is not None else fila.get("pct_nodos_nuevos")
    declarado = any(q["anio"] == t and (t - 1) in q["comparable_con"] for q in quiebres(c))
    if peso is not None and umbral is not None and float(peso) > float(umbral) and not declarado:
        return True, "nodos nuevos sobre el umbral"
    if funcional:
        return False, None
    for q in quiebres(c):
        if q["anio"] == t and (t - 1) not in q["comparable_con"]:
            return True, q.get("descripcion")
    if t in {_int(a) for a in (c.get("anios_con_quiebre") or [])}:
        return True, "anios_con_quiebre"
    return False, None


@regla("R-GASTO-09")
def r_gasto_09(c, ctx):
    """Series del gasto por concepto estable: años sin montos y variación a través de un año no comparable."""
    rid = "R-GASTO-09"
    anio = c.req("anio")
    con_montos = ctx.param(rid, "anios_con_montos") or []
    msg_q, msg_prev = None, None
    m = ctx.regla(rid).get("mensaje_usuario") or ""
    partes = re.findall(r"«([^»]*)»", m)
    if partes:
        msg_q, msg_prev = partes[0], partes[-1]
    if int(anio) not in con_montos:
        return Resultado(rid, "suprimir", "fuera_de_cobertura", clausula="(3) cobertura_por_anio(t) != 'con_montos'",
                         detalle={"anio": anio, "anios_con_montos": con_montos,
                                  "cobertura_por_anio": ctx.param(rid, "cobertura_por_anio")}, mensaje=msg_prev)
    tema = c.get("tema_id") or ""
    cad = (ctx.param("R-GASTO-08b", "prefijo_cadena") or {}).get(prefijo_tema(tema, ctx)) if tema else None
    funcional = cad in ("funcion", "division")
    res = []
    anios = anios_consulta(c)
    sin_montos = [a for a in anios if a not in con_montos]
    par = anios_comparados(c)
    if par:
        ini, fin = par
        cortes = []
        for t in range(ini + 1, fin + 1):
            nc, motivo = _no_comparable_gasto(c, ctx, t, funcional)
            if nc:
                cortes.append({"anio": t, "motivo": motivo})
        if cortes:
            res.append(Resultado(rid, "advertir", "quiebre",
                                 clausula="no_comparable en t y se pide la variación t-1 → t",
                                 detalle={"anio_ini": ini, "anio_fin": fin, "anios_no_comparables": cortes,
                                          "sin_variacion_porcentual": True, "excluir_anios_sin_montos": sin_montos},
                                 mensaje=(msg_q or "").replace("{anio}", str(cortes[0]["anio"])) or None))
        elif sin_montos:
            res.append(Resultado(rid, "advertir", "fuera_de_cobertura",
                                 clausula="(3) años de la serie sin montos: solo linaje",
                                 detalle={"excluir_anios_sin_montos": sin_montos}, mensaje=msg_prev))
        if funcional:
            otros = [q for q in quiebres(c) if ini < q["anio"] <= fin and q["tipo"] != "programa"]
            if otros:
                res.append(Resultado(rid, "revision_humana", "quiebre",
                                     clausula="fun_/div_: cambio del clasificador funcional → revisión humana",
                                     detalle={"quiebres": otros}, modificador=True))
    return res or None


# ======================================================================= R-CRUCES-04

@regla("R-CRUCES-04")
def r_cruces_04(c, ctx):
    """Quiebres metodológicos en comparaciones y series: no se declara un cambio a través de un quiebre si la
    definición no es la misma en ambos años."""
    rid = "R-CRUCES-04"
    c.req("anio")
    par = anios_comparados(c)
    if not par:
        return None
    ini, fin = par
    qs = sorted(anios_quiebre_indicador(c) | anios_quiebre_catalogo(c, ctx))
    cruzan = [q for q in qs if ini < q <= fin]
    if not cruzan:
        return None
    crit_a = criterio_de(fila_del_anio(c, ini), c)
    crit_b = criterio_de(fila_del_anio(c, fin), c)
    misma = crit_a is not None and crit_a == crit_b
    tipos = {q["anio"]: q["tipo"] for q in quiebres(c)}
    desc = {q["anio"]: q.get("descripcion") for q in quiebres(c)}
    if not misma:
        q = cruzan[0]
        return Resultado(rid, "advertir", "quiebre", clausula="quiebre entre los años AND NOT misma_definicion",
                         detalle={"anio_a": ini, "anio_b": fin, "quiebres": cruzan, "criterio_a": crit_a,
                                  "criterio_b": crit_b, "cortar_serie_en": q},
                         mensaje=mensaje(rid, ctx, anio_quiebre=q, anio_a=ini, anio_b=fin,
                                         indicador=c.get("nombre_ciudadano") or c.get("indicador_id"),
                                         motivo=desc.get(q) or "cambio de definición"))
    # misma definición en ambos años: versión homologada → se usa y se rotula; 2020 (modo) lo trata R-ENC-13
    if any(tipos.get(q) != "modo" for q in cruzan):
        return Resultado(rid, "rotular", "quiebre", clausula="hay quiebre pero misma definición (versión homologada)",
                         detalle={"anio_a": ini, "anio_b": fin, "quiebres": cruzan, "criterio": crit_a},
                         rotulo="misma_definicion_en_ambos_anios")
    return None


# ======================================================================= R-LENGUAJE-04

@regla("R-LENGUAJE-04")
def r_lenguaje_04(c, ctx):
    """Cifras antiguas o anteriores a un choque: año en la misma oración, tiempo pasado y aviso de desactualización."""
    rid = "R-LENGUAJE-04"
    anio = int(c.req("anio"))
    vig = ctx.param(rid, "vigencia_max_presente_anios")
    choques = ctx.param(rid, "anios_choque") or ctx.pg.get("anios_choque") or []
    serie = [_int(f.get("anio")) for f in filas_serie(c) if _int(f.get("anio")) is not None]
    if serie and ctx.anio_actual - max(serie + [anio]) <= vig:
        return None  # PR-05: la cifra es parte de una serie cuyo último año está vigente
    edad = ctx.anio_actual - anio
    choque = [a for a in choques if anio < a <= ctx.anio_actual]
    socio = bool(c.req("es_socioeconomico"))
    msg = mensaje(rid, ctx, anio_dato=anio)
    aviso = Resultado(rid, "aviso_choque", "dato_antiguo", clausula="anio_choque entre el dato y el presente, socioeconómico",
                      detalle={"anios_choque": choque}, mensaje=msg, aviso="dato_anterior_a_choque",
                      modificador=True) if (choque and socio) else None
    if edad > vig:
        res = [Resultado(rid, "plantilla_pasado", "dato_antiguo", clausula="edad_dato > vigencia_max_presente_anios",
                         detalle={"edad_dato": edad, "anio_dato": anio, "plantilla": f"en {anio} se estimaba"},
                         rotulo="tiempo_pasado_con_anio")]
        return res + ([aviso] if aviso else [])
    return aviso


# ======================================================================= R-GASTO-08b (ámbito respuesta)

def _alternativas(ctx) -> dict:
    """tema → tema del que es lectura alternativa (R-GASTO-08b.alternativas y temas_iniciales.alternativa_de)."""
    alt = dict(ctx.param("R-GASTO-08b", "alternativas") or {})
    for t, d in (ctx.param("R-GASTO-08", "temas_iniciales") or {}).items():
        if d.get("alternativa_de"):
            alt.setdefault(t, d["alternativa_de"])
    return alt


def son_alternativas(t1, t2, ctx) -> bool:
    """Dos temas que son lecturas alternativas del mismo gasto (uno alternativa del otro, o ambos del mismo)."""
    alt = _alternativas(ctx)
    raiz1, raiz2 = alt.get(t1, t1), alt.get(t2, t2)
    return t1 != t2 and raiz1 == raiz2


def oraciones(texto: str) -> list[str]:
    return [o for o in re.split(r"(?<=[.!?;])\s+", texto or "") if o.strip()]


MARCADOR_C = re.compile(r"\{\{c:([^}]+)\}\}")


def _operacion_entre(rid, ta, tb, ca, cb, op, ctx, objetivo=None) -> Resultado | None:
    """(2) y (6) de R-GASTO-08b para una operación entre dos temas de gasto."""
    p = ctx.regla(rid)["parametros"]
    if op in (None, "lado_a_lado"):
        return None
    if ca != cb:
        pa, pb = prefijo_tema(ta, ctx), prefijo_tema(tb, ctx)
        cod = lambda t: (re.findall(r"_(\d{4})", t or "") or [None])[0]  # noqa: E731
        if {pa, pb} == {"ppxfun", "pp"} and cod(ta) == cod(tb) and op in ("cociente", "porcentaje_de"):
            return Resultado(rid, "rotular", "cadena_distinta",
                             clausula="(2) excepción: cociente ppxfun_ sobre su programa, rotulado como cruce",
                             detalle={"temas": [ta, tb], "operacion": op}, objetivo=objetivo)
        return Resultado(rid, "bloquear_cruce", "cadena_distinta", clausula="(2) operación entre cifras de cadena distinta",
                         detalle={"temas": [ta, tb], "cadenas": [ca, cb], "operacion": op},
                         mensaje=p.get("frase_fija_dos_cadenas"), objetivo=objetivo)
    if son_alternativas(ta, tb, ctx):
        return Resultado(rid, "bloquear_cruce", "lecturas_alternativas",
                         clausula="(6) lecturas alternativas (alternativa_de): no se suman ni operan",
                         detalle={"temas": [ta, tb], "operacion": op}, mensaje=p.get("frase_fija_dos_cadenas"),
                         objetivo=objetivo)
    return None


@regla("R-GASTO-08b")
def r_gasto_08b(c, ctx):
    """Una cadena por cifra (parte de cifra, etapa 5): (1) gramática del tema y prefijo ↔ cadena; (2)/(6) operación con
    la cifra de comparación; (4) serie de una sola cadena y versión. Las cláusulas que miran la respuesta entera
    ((2)/(6) entre cruces, (3) oraciones y frase fija, (4) rankings, (5) temas de contexto) las corre
    `gasto_08b_respuesta`, desde R-GASTO-15 (etapa 8), con regla = R-GASTO-08b."""
    rid = "R-GASTO-08b"
    p = ctx.regla(rid)["parametros"]
    tema = c.req("tema_id")
    cad = cadena_de(c, ctx)
    if cad is None:
        raise CampoFaltante("cadena")
    if not re.match(p["gramatica_id"], tema) or (p.get("prefijo_cadena") or {}).get(prefijo_tema(tema, ctx)) != cad:
        return Resultado(rid, "bloquear", "tema_fuera_de_gramatica",
                         clausula="(1) tema_id no cumple la gramática o su prefijo no corresponde a la cadena",
                         detalle={"tema_id": tema, "cadena": cad})
    res = []
    comp = fila_comparacion(c)
    if comp and (comp.get("tema_id") or comp.get("cadena")):
        op = comp.get("operacion") or comp.get("presentacion")
        tb = comp.get("tema_id")
        r2 = _operacion_entre(rid, tema, tb, cad, cadena_de(comp, ctx), op, ctx)
        if r2:
            res.append(r2)
    temas = {f.get("tema_id") for f in filas_serie(c) if f.get("tema_id")} | {tema}
    cads = {f.get("cadena") for f in filas_serie(c) if f.get("cadena")} | {cad}
    vers = {".".join(str(f.get(k)).split(".")[:2]) for f in filas_serie(c) + [c.datos()]
            for k in ("version_tema", "version_dim_tema_gasto") if f.get(k) is not None}
    if len(temas) > 1 or len(cads) > 1 or len(vers) > 1:
        res.append(Resultado(rid, "bloquear_cruce", "cadena_distinta",
                             clausula="(4) serie con más de una cadena o versión de dim_tema_gasto",
                             detalle={"temas": sorted(temas), "cadenas": sorted(cads), "versiones": sorted(vers)}))
    return res or None


def gasto_08b_respuesta(r, ctx) -> list[Resultado]:
    """Cláusulas de R-GASTO-08b que miran la respuesta entera. El núcleo solo corre reglas de respuesta en las etapas
    8–10 y R-GASTO-08b está en la etapa 5: por eso las llama R-GASTO-15 (etapa 8, la regla de redacción del gasto)."""
    rid = "R-GASTO-08b"
    p = ctx.regla(rid)["parametros"]
    res = []
    gasto = {}
    for c in r.get("cifras") or []:
        if es_aplicable(rid, c, ctx) and c.get("tema_id") and cadena_de(c, ctx):
            gasto[c.get("id_cifra")] = c
    # (2)/(6) operaciones entre cifras de gasto declaradas como cruces
    for cr in r.get("cruces") or []:
        a, b = gasto.get(cr.get("a")), gasto.get(cr.get("b"))
        if a is None or b is None:
            continue
        x = _operacion_entre(rid, a.tema_id, b.tema_id, cadena_de(a, ctx), cadena_de(b, ctx),
                             cr.get("operacion") or cr.get("presentacion"), ctx, objetivo=f"cruce:{cr.get('id_cruce')}")
        if x:
            res.append(x)
    # (3) dos cadenas (o un tema y su lectura alternativa) en la misma respuesta
    ids = list(gasto)
    pares = [(x, y) for i, x in enumerate(ids) for y in ids[i + 1:]
             if cadena_de(gasto[x], ctx) != cadena_de(gasto[y], ctx) or son_alternativas(gasto[x].tema_id, gasto[y].tema_id, ctx)]
    if pares:
        texto = r.get("texto") or ""
        juntas = []
        for o in oraciones(texto):
            en = set(MARCADOR_C.findall(o))
            juntas += [o for x, y in pares if x in en and y in en][:1]
        if juntas:
            res.append(Resultado(rid, "regenerar", "cadena_distinta",
                                 clausula="(3) dos cadenas en la misma oración: van en oraciones separadas",
                                 detalle={"oraciones": juntas}, objetivo="respuesta"))
        frase = p.get("frase_fija_dos_cadenas") or ""
        tiene = _norm(frase) in _norm(texto) or re.search(r"\{\{p:[^}]*(dos_cadenas|no_se_suman|08b)[^}]*\}\}", texto, re.I)
        if not tiene:
            res.append(Resultado(rid, "rotular", "cadena_distinta", clausula="(3) dos cadenas: falta la frase fija",
                                 detalle={"pares": [list(x) for x in pares]}, mensaje=frase, rotulo=frase,
                                 objetivo="respuesta"))
    # (4) rankings y comparaciones entre territorios: una sola cadena
    cads = {cadena_de(c, ctx) for c in gasto.values()}
    if r.get("intencion_pregunta") in ("comparacion", "identificar_extremo") and len(cads) > 1:
        res.append(Resultado(rid, "bloquear_cruce", "cadena_distinta",
                             clausula="(4) ranking o comparación entre territorios con más de una cadena",
                             detalle={"cadenas": sorted(cads)}, objetivo="respuesta"))
    # (5) temas de contexto o de desglose: línea aparte, no como cifra principal junto a su tema por defecto
    temas_pres = {c.tema_id: cid for cid, c in gasto.items()}
    for intencion, m in (p.get("map_intencion_tema") or {}).items():
        if m.get("defecto") not in temas_pres:
            continue
        for t in list(m.get("contexto") or []) + ([m["desglose"]] if m.get("desglose") else []):
            cid = temas_pres.get(t)
            if cid and (gasto[cid].get("es_principal") or gasto[cid].get("rol") == "principal"):
                res.append(Resultado(rid, "advertir", "tema_de_contexto",
                                     clausula="(5) tema de contexto o desglose en línea aparte, no como principal",
                                     detalle={"intencion_tema": intencion, "defecto": m.get("defecto"), "tema": t},
                                     objetivo=cid))
    return res


def _norm(t: str) -> str:
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(ch) != "Mn")
