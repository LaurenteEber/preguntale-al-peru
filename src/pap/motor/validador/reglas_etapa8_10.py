"""Etapas 8–10 del validador (grupo C), ámbito «respuesta»: cruces y comparaciones, semáforo de la respuesta, ficha de
límites y lenguaje.

Cada regla recibe la respuesta (`Respuesta`, contrato §3) con sus cifras ya evaluadas, los cruces pedidos y el borrador
del texto con marcadores. El `objetivo` de cada Resultado es el `id_cifra`, `cruce:<id_cruce>` o `respuesta`.

El núcleo no comprueba `aplica_a` en las reglas de respuesta: aquí se comprueba cifra por cifra (`es_aplicable`). Un
campo requerido que falta en una cifra o en un cruce se resuelve en ese objetivo (suprimir o bloquear_cruce por
metadato_faltante) para no tumbar la respuesta entera.

El corrector léxico (R-LENGUAJE-02) aplica `lenguaje.prohibidas` como lo hace `reglas/consolidador/consolida_reglas.py`
(marcadores → «X», texto normalizado sin tildes salvo `normalizar = false`, y texto tal cual con `texto_original`); los
`avisos_pendientes_validacion` solo avisan. La parte estructural reutiliza `reglas/consolidador/corrector_estructural.py`.
"""
from __future__ import annotations

import importlib.util
import math
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from .nucleo import CampoFaltante, Resultado, regla
from .reglas_etapa5 import (MARCADOR_C, _int, anios_quiebre_indicador, cadena_de, es_aplicable, fila_comparacion,
                            gasto_08b_respuesta, mensaje, oraciones)

RAIZ = Path(__file__).resolve().parents[4]

# ======================================================================= ayudas


def _norm(t: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", (t or "").lower()) if unicodedata.category(ch) != "Mn")


def _cifras(r) -> list:
    return list(r.get("cifras") or [])


def _por_id(r) -> dict:
    return {c.get("id_cifra"): c for c in _cifras(r)}


def _es_principal(c) -> bool:
    return bool(c.get("es_principal")) or c.get("rol") == "principal"


def _op(cr: dict) -> str | None:
    return cr.get("operacion") or cr.get("presentacion")


def _obj(cr: dict) -> str:
    return f"cruce:{cr.get('id_cruce')}"


def _componentes(r, cr):
    """Las dos cifras de un cruce. Un id que no está en la respuesta es un metadato faltante del cruce."""
    pid = _por_id(r)
    a, b = pid.get(cr.get("a")), pid.get(cr.get("b"))
    if a is None or b is None:
        raise CampoFaltante("a" if a is None else "b")
    return a, b


def _faltante(rid, e: CampoFaltante, objetivo, accion="bloquear_cruce"):
    return Resultado(rid, accion, "metadato_faltante", clausula="campo requerido vacío", detalle={"campo": e.campo},
                     objetivo=objetivo)


def _rank(ctx, nivel):
    return ctx.nivel_rank(nivel) if nivel is not None else None


def _nivel_publicado(c) -> str | None:
    return c.get("nivel_publicado") or c.get("nivel")


def _estado(c) -> str:
    return c.get("estado_cifra") or "publicable"


def _publicable(c) -> bool:
    return _estado(c) not in ("suprimida", "sin_datos")


def _fila_lista(ctx, ind_a, ind_b) -> dict | None:
    """Fila de cruces_permitidos para el par (en cualquier orden)."""
    for f in ctx.cruces or []:
        if {f.get("indicador_a"), f.get("indicador_b")} == {ind_a, ind_b}:
            return f
    return None


def _fila_activa(f) -> bool:
    """Una fila cuenta si está activa en el piloto y tiene el visto del dueño (cabecera de cruces_permitidos.yaml)."""
    return bool(f) and f.get("estado_propuesta") == "activo_piloto" and bool(f.get("aprobado_por"))


def _ambito_lima(cr, a, b, ctx) -> dict | None:
    """Ámbito de subdivision_lima (L5) que ampara al cruce: fila activa con subdivision_lima y el nivel del cruce (o de
    ambos componentes) es uno de sus ámbitos. En ese caso Lima y el Callao se cruzan ámbito a ámbito."""
    f = _fila_lista(ctx, a.get("indicador_id"), b.get("indicador_id"))
    if not _fila_activa(f):
        return None
    ambs = {x.get("nivel"): x for x in ((f.get("subdivision_lima") or {}).get("ambitos") or [])}
    nivel = cr.get("nivel")
    if nivel in ambs:
        return ambs[nivel]
    na, nb = _nivel_publicado(a), _nivel_publicado(b)
    if na == nb and na in ambs:
        return ambs[na]
    if a.get("territorio_id") == b.get("territorio_id") and a.get("territorio_id") in ambs:
        return ambs[a.get("territorio_id")]
    return None


def _ambitos_composicion(ctx) -> dict:
    """Composición de los ámbitos (ctx.ambitos = dim_ambito: prefijos de ubigeo, con «-» para excluir)."""
    df = getattr(ctx, "ambitos", None)
    if df is None:
        return {}
    return {r.ambito_id: [str(x) for x in r.composicion] for r in df.itertuples()}


def _prefijos(territorio, ctx) -> tuple[list[str], list[str]] | None:
    """Territorio → (prefijos de ubigeo incluidos, excluidos). None si no se puede ubicar (urbano/rural, establecimiento)."""
    t = str(territorio)
    if t == "PE":
        return [""], []
    amb = _ambitos_composicion(ctx).get(t)
    if amb:
        return [x for x in amb if not x.startswith("-")], [x[1:] for x in amb if x.startswith("-")]
    if t.isdigit() and len(t) == 2:
        return [t], []
    if t.isdigit() and len(t) == 6:
        return ([t[:4]] if t.endswith("00") else [t]), []
    return None


def _distritos(ctx) -> list[str]:
    u = ctx.ubigeos
    if u is None:
        return []
    d = u[u["nivel"] == "distrito"]
    if "estado_ubigeo" in d.columns:
        d = d[d["estado_ubigeo"] == "vigente"]
    return sorted(set(d["ubigeo_inei"].astype(str)))


def _contiene(ctx, A, B) -> bool:
    """contiene(A, B) := ubigeos(B) ⊆ ubigeos(A) (R-CRUCES-01.dominios_lima.contencion)."""
    if str(A) == str(B):
        return True
    pa, pb = _prefijos(A, ctx), _prefijos(B, ctx)
    if pa is None or pb is None:
        return str(A) == "PE"

    def en(p, u):
        return any(u.startswith(x) for x in p[0]) and not any(u.startswith(x) for x in p[1])

    dist = _distritos(ctx)
    if dist:
        db = [u for u in dist if en(pb, u)]
        return bool(db) and all(en(pa, u) for u in db)
    # sin dim_ubigeo: comparación de prefijos
    return all(any(x.startswith(y) for y in pa[0]) and not any(x.startswith(e) or e.startswith(x) for e in pa[1]
                                                               if e not in pb[1]) for x in pb[0])


def _territorio_cruce(ctx, ta, tb) -> str | None:
    """El menor territorio que contiene a ambos componentes; None si solo el nacional los contiene."""
    if _contiene(ctx, ta, tb):
        return str(ta)
    if _contiene(ctx, tb, ta):
        return str(tb)
    candidatos = list(_ambitos_composicion(ctx)) + [str(t)[:2] for t in (ta, tb) if str(t)[:2].isdigit()]
    def tam(t):  # noqa: E306
        p = _prefijos(t, ctx)
        return len([u for u in _distritos(ctx) if p and any(u.startswith(x) for x in p[0])]) or 999
    for cand in sorted(set(candidatos), key=tam):
        if _contiene(ctx, cand, ta) and _contiene(ctx, cand, tb):
            return cand
    return None


def _resultados_de(c) -> list:
    """Resultados de las etapas 0–7 de una cifra (evaluacion.resultados o resultados_previos)."""
    ev = c.get("evaluacion")
    res = getattr(ev, "resultados", None) if ev is not None else None
    res = res if res is not None else (c.get("resultados") or c.get("resultados_previos") or [])
    out = []
    for x in res:
        out.append(x if isinstance(x, dict) else x.a_dict())
    return out


def _p_valor(dif, ee, gl) -> float:
    """p bilateral con t de Student (gl) o normal si no hay gl."""
    if ee <= 0:
        return 0.0 if dif != 0 else 1.0
    t = abs(dif) / ee
    try:
        from scipy import stats
        return float(2 * (stats.t.sf(t, gl) if gl else stats.norm.sf(t)))
    except ImportError:  # pragma: no cover
        return math.erfc(t / math.sqrt(2))


def _prueba(a: dict, b: dict, ctx, prueba: dict | None = None) -> dict:
    """Prueba de diferencia de R-ENC-11 entre dos filas de encuesta (valores y ee en %). Usa la prueba del motor si
    viene; si no, la calcula con cov = 0 (años o departamentos independientes) y gl = min(gl_a, gl_b)."""
    if prueba and prueba.get("p_valor") is not None:
        return {"diferencia": prueba.get("diferencia"), "p_valor": float(prueba["p_valor"]),
                "significativa": prueba.get("significativa"), "origen": "motor"}
    for f, k in ((a, "valor"), (b, "valor"), (a, "ee"), (b, "ee")):
        if f.get(k) is None:
            raise CampoFaltante(k)
    dif = float(b["valor"]) - float(a["valor"])
    ee = math.sqrt(float(a["ee"]) ** 2 + float(b["ee"]) ** 2)
    gls = [g for g in (a.get("gl"), b.get("gl")) if g is not None]
    gl = min(gls) if gls else None
    p = _p_valor(dif, ee, gl)
    return {"diferencia": dif, "ee_diferencia": ee, "p_valor": p, "gl": gl, "origen": "validador_cov0"}


# ======================================================================= etapa 8: R-CRUCES-11

@regla("R-CRUCES-11", ambito="respuesta")
def r_cruces_11(r, ctx):
    """Solo se calculan los cruces de la lista blanca cruces_permitidos (con subdivision_lima, L5)."""
    rid = "R-CRUCES-11"
    res = []
    activas = [f for f in ctx.cruces or [] if _fila_activa(f)]
    tope = ctx.param(rid, "max_cruces_mvp")
    if tope is not None and len(activas) > tope:
        res.append(Resultado(rid, "revision_humana", "lista_cruces", clausula="más cruces activos que max_cruces_mvp",
                             detalle={"activos": len(activas), "max": tope}, objetivo="respuesta"))
    for cr in r.get("cruces") or []:
        obj = _obj(cr)
        try:
            a, b = _componentes(r, cr)
            ia, ib = a.req("indicador_id"), b.req("indicador_id")
        except CampoFaltante as e:
            res.append(_faltante(rid, e, obj))
            continue
        f = _fila_lista(ctx, ia, ib)
        if not _fila_activa(f):
            res += [Resultado(rid, "bloquear_cruce", "cruce_no_listado",
                              clausula="(indicador_a, indicador_b) not in cruces_permitidos → mostrar por separado",
                              detalle={"indicadores": [ia, ib], "fila": (f or {}).get("id_cruce"),
                                       "estado": (f or {}).get("estado_propuesta")}, objetivo=obj),
                    Resultado(rid, "revision_humana", "cruce_no_listado", clausula="registrar para ampliar la tabla",
                              detalle={"indicadores": [ia, ib]}, objetivo=obj, modificador=True)]
            continue
        if _op(cr) not in (None, f.get("presentacion")):
            res.append(Resultado(rid, "bloquear_cruce", "presentacion_no_listada",
                                 clausula="no calcular asociación ni cocientes no listados",
                                 detalle={"pedida": _op(cr), "listada": f.get("presentacion")}, objetivo=obj))
            continue
        anios = sorted({_int(x) for x in (cr.get("anios") or [a.get("anio"), b.get("anio")]) if _int(x) is not None})
        sub = f.get("subdivision_lima") or {}
        amb = _ambito_lima(cr, a, b, ctx)
        if amb is not None:
            permitidos = set(amb.get("anios") or [])
            for cond in sub.get("anios_condicionados") or []:
                if amb.get("ambito_id") in (cond.get("ambitos") or []) and cond.get("activo") is False:
                    permitidos.discard(cond.get("anio"))
            fuera = [x for x in anios if x not in permitidos]
            if fuera:
                res.append(Resultado(rid, "bloquear_cruce", "anio_fuera_de_lista",
                                     clausula="subdivision_lima: años del ámbito (anios, anios_condicionados)",
                                     detalle={"ambito": amb.get("ambito_id"), "anios": fuera,
                                              "permitidos": sorted(permitidos)}, objetivo=obj))
            continue
        nivel = cr.get("nivel") or _nivel_publicado(a)
        terr = {str(a.get("territorio_id")), str(b.get("territorio_id"))}
        if nivel == "departamento" and terr & set(str(x) for x in (sub.get("subdivide") or [])) - {"07"}:
            # el 15 entero solo como respaldo si falta LM o LR (si_falta_un_ambito); nunca junto con LM o LR
            rot = re.findall(r"«([^»]*)»", sub.get("si_falta_un_ambito") or "")
            res.append(Resultado(rid, "rotular", "lima_departamento",
                                 clausula="subdivision_lima: el 15 entero solo si falta un ámbito (si_falta_un_ambito)",
                                 detalle={"territorio": sorted(terr)}, rotulo=rot[0] if rot else None, objetivo=obj))
        rk, rmin = _rank(ctx, nivel), _rank(ctx, f.get("nivel_minimo"))
        if rk is not None and rmin is not None and rk < rmin:
            res.append(Resultado(rid, "agregar_nivel", "nivel_minimo_cruce", clausula="nivel del cruce < nivel_minimo",
                                 detalle={"nivel": nivel, "nivel_minimo": f.get("nivel_minimo")},
                                 nivel_minimo=f.get("nivel_minimo"), objetivo=obj))
            continue
        fuera = [x for x in anios if x not in (f.get("anios_comunes") or [])]
        if fuera:
            res.append(Resultado(rid, "bloquear_cruce", "anio_fuera_de_lista", clausula="años fuera de anios_comunes",
                                 detalle={"anios": fuera, "anios_comunes": f.get("anios_comunes")}, objetivo=obj))
    return res or None


# ======================================================================= R-CRUCES-01

def _nivel_de_territorio(t) -> str | None:
    """Nivel de un territorio_id: PE → nacional; ámbito → su id (que es su nivel en NIVEL_RANK); 2 dígitos →
    departamento; 6 dígitos → provincia (termina en 00) o distrito."""
    t = str(t)
    if t == "PE":
        return "nacional"
    if t.isdigit() and len(t) == 2:
        return "departamento"
    if t.isdigit() and len(t) == 6:
        return "provincia" if t.endswith("00") else "distrito"
    return t


@regla("R-CRUCES-01", ambito="respuesta")
def r_cruces_01(r, ctx):
    """Nivel del cruce = el más grueso de sus componentes (y del territorio que los contiene); además, contención."""
    rid = "R-CRUCES-01"
    res = []
    rk = lambda n: _rank(ctx, n) if _rank(ctx, n) is not None else -1  # noqa: E731
    for cr in r.get("cruces") or []:
        obj = _obj(cr)
        try:
            a, b = _componentes(r, cr)
            if not (es_aplicable(rid, a, ctx) or es_aplicable(rid, b, ctx)):
                continue
            amb = _ambito_lima(cr, a, b, ctx)
            niveles = {}
            for c in (a, b):
                nat = c.req("naturaleza_dato")
                if str(c.get("territorio_id")) in ("LIMA_METROPOLITANA", "LIMA_REGION", "CALLAO"):
                    # ámbito de Lima publicado (L1, verificado por R-ENC-08): su nivel es el propio ámbito (H-5)
                    niveles[c.get("id_cifra")] = str(c.get("territorio_id"))
                elif nat in ("encuesta_muestral", "estimacion_modelada") and amb is None:
                    niveles[c.get("id_cifra")] = c.req("nivel_territorial_inferencia")
                else:
                    niveles[c.get("id_cifra")] = _nivel_publicado(c) or c.req("nivel")
            ta, tb = a.req("territorio_id"), b.req("territorio_id")
            pedido = r.get("nivel_pedido") or cr.get("nivel")
        except CampoFaltante as e:
            res.append(_faltante(rid, e, obj))
            continue
        terr = _territorio_cruce(ctx, ta, tb) if str(ta) != str(tb) else str(ta)
        # H-5: el nivel del territorio que contiene a los componentes también cuenta (ámbitos de Lima incluidos:
        # gasto de LM con anemia del 15 entero → el cruce va al 15; SJL con LM → el cruce va a LM)
        candidatos = dict(niveles)
        if terr is not None:
            candidatos["territorio_cruce"] = _nivel_de_territorio(terr)
        nivel_cruce = max(candidatos.values(), key=rk)
        if pedido is not None and _rank(ctx, pedido) is not None and _rank(ctx, nivel_cruce) is not None \
                and _rank(ctx, pedido) < _rank(ctx, nivel_cruce):
            limitante = next((c for c in (a, b) if niveles[c.get("id_cifra")] == nivel_cruce), None)
            fuente = limitante.get("fuente_principal") if limitante else "la composición del territorio"
            res.append(Resultado(rid, "agregar_nivel", "nivel_no_representativo", clausula="nivel_pedido < nivel_cruce",
                                 detalle={"nivel_cruce": nivel_cruce, "nivel_pedido": pedido, "niveles": niveles,
                                          "territorio_cruce": terr},
                                 nivel_minimo=nivel_cruce, objetivo=obj,
                                 mensaje=mensaje(rid, ctx, nivel_cruce=nivel_cruce, nivel_pedido=pedido,
                                                 fuente_limitante=fuente)))
        # Además: contención territorial
        if terr is None or terr == "PE" or nivel_cruce == "nacional":
            acc = "rotular" if _op(cr) in (None, "lado_a_lado") else "bloquear_cruce"
            res.append(Resultado(rid, acc, "sin_cruce_territorial",
                                 clausula="solo el nacional contiene a todos: no hay cruce territorial (solo lado a lado)",
                                 detalle={"territorios": [ta, tb], "territorio_cruce": terr}, objetivo=obj,
                                 modificador=True))
        elif str(ta) != str(tb):
            res.append(Resultado(rid, "rotular", "contencion_territorial",
                                 clausula="territorio_cruce := menor territorio que contiene a los componentes",
                                 detalle={"territorios": [ta, tb], "territorio_cruce": terr}, objetivo=obj,
                                 modificador=True))
    return res or None


# ======================================================================= R-CRUCES-02

def _b(codigo, rid, ctx, obj, detalle):
    return Resultado(rid, "bloquear_cruce", "cruce_bloqueado", clausula=codigo, detalle={"codigo": codigo, **detalle},
                     objetivo=obj, mensaje=mensaje(rid, ctx, motivo_bloqueo_ciudadano=codigo, y_alternativa=""))


@regla("R-CRUCES-02", ambito="respuesta")
def r_cruces_02(r, ctx):
    """Lista B1–B9 de cruces bloqueados."""
    rid = "R-CRUCES-02"
    orden = ctx.param(rid, "lista_bloqueos") or []
    res = []
    for cr in r.get("cruces") or []:
        obj = _obj(cr)
        try:
            a, b = _componentes(r, cr)
        except CampoFaltante as e:
            res.append(_faltante(rid, e, obj))
            continue
        if not (es_aplicable(rid, a, ctx) or es_aplicable(rid, b, ctx)):
            continue
        op = _op(cr)
        comps = (a, b)
        nivel_cruce = cr.get("nivel") or max((_nivel_publicado(c) for c in comps),
                                            key=lambda n: _rank(ctx, n) if _rank(ctx, n) is not None else -1)
        f = lambda c: c.get("fuente_principal")  # noqa: E731
        fuentes = {f(c) for c in comps}
        gasto = [c for c in comps if c.get("naturaleza_dato") == "presupuestal_financiero"]
        hit = None
        for cod in orden:
            if hit:
                break
            if cod == "B1":
                for c in comps:
                    if c.get("base_geografica_usada") == "ejecutora" and nivel_cruce in ("distrito", "provincia") \
                            and not (c.get("nivel_gobierno") == "M" or c.get("ubicado_por_cui")):
                        hit = _b(cod, rid, ctx, obj, {"cifra": c.get("id_cifra"), "nivel_cruce": nivel_cruce})
            elif cod == "B2":
                if _ambito_lima(cr, a, b, ctx) is not None:
                    continue  # L5: Lima y el Callao ámbito a ámbito en un cruce de la lista blanca
                for c in comps:
                    nti = c.get("nivel_territorial_inferencia")
                    if c.get("naturaleza_dato") == "encuesta_muestral" and nti and _rank(ctx, nivel_cruce) is not None \
                            and _rank(ctx, nti) is not None and _rank(ctx, nivel_cruce) < _rank(ctx, nti):
                        hit = _b(cod, rid, ctx, obj, {"cifra": c.get("id_cifra"), "nivel_cruce": nivel_cruce,
                                                      "nivel_territorial_inferencia": nti})
            elif cod == "B3":
                mapa = next((c for c in comps if f(c) == "INEI-MAPA-POBREZA"), None)
                otro = next((c for c in comps if c is not mapa), None) if mapa else None
                if mapa and otro:
                    if f(otro) == "INEI-ENAHO" and otro.get("anio") != mapa.get("anio") and \
                            op in ("resta", "tendencia", "variacion", "actualizacion", "ajuste_por_variacion_encuesta"):
                        hit = _b(cod, rid, ctx, obj, {"operacion": op})
                    elif op in ("asociacion", "correlacion") and (_int(otro.get("anio")) or 0) >= 2020:
                        hit = _b(cod, rid, ctx, obj, {"operacion": op, "anio_otro": otro.get("anio")})
            elif cod == "B4":
                if {"INS-CENAN-SIEN", "INEI-ENDES"} <= fuentes and op in ("resta", "promedio", "suma", "variacion"):
                    hit = _b(cod, rid, ctx, obj, {"operacion": op})
                elif "INS-CENAN-SIEN" in fuentes and cr.get("rotulo") and "prevalencia" in _norm(cr.get("rotulo")):
                    hit = _b(cod, rid, ctx, obj, {"rotulo": cr.get("rotulo")})
            elif cod == "B5":
                pares = [{"MEF-DA-TRANSFERENCIAS"}, {"MEF-DA-GASTO-DEVENGADO-MENSUAL", "MEF-DA-PRESUPUESTO-EJECUCION-GASTO"},
                         {"MEF-SEGUIMIENTO-PI", "MEF-DA-PRESUPUESTO-EJECUCION-GASTO"},
                         {"MEF-OXI-BASE", "MEF-DA-PRESUPUESTO-EJECUCION-GASTO"}]
                if op == "suma" and len(gasto) == 2 and any(p <= fuentes and (len(p) == 2 or len(fuentes) == 2) for p in pares):
                    hit = _b(cod, rid, ctx, obj, {"fuentes": sorted(fuentes)})
            elif cod == "B6":
                otro = [c for c in comps if c.get("naturaleza_dato") != "presupuestal_financiero"]
                if op in ("cociente", "porcentaje_de") and gasto and otro and (
                        otro[0].get("comparacion") or cr.get("sobre_cambio")
                        or otro[0].get("tipo_medida") in ("prevalencia", "estimacion_modelada", "notificacion_vigilancia")):
                    hit = _b(cod, rid, ctx, obj, {"operacion": op})
            elif cod == "B7":
                if op in ("cociente", "porcentaje_de") and nivel_cruce == "distrito" and \
                        a.get("base_geografica_usada") == "establecimiento" and b.get("base_geografica_usada") == "residencia":
                    hit = _b(cod, rid, ctx, obj, {"nivel_cruce": nivel_cruce,
                                                  "nivel_minimo_permitido": ctx.param(rid, "B7_nivel_minimo_permitido")})
            elif cod == "B8":
                if op in ("cociente", "porcentaje_de") and f(b) == "RENIEC-POBLACION-IDENTIFICADA":
                    hit = _b(cod, rid, ctx, obj, {"denominador": f(b)})
            elif cod == "B9":
                if a.get("indicador_id") != b.get("indicador_id"):  # PR-05: no entre años del mismo indicador
                    rojos = [c.get("id_cifra") for c in comps if c.get("semaforo_cifra") in ("rojo", "no_publicable")]
                    if rojos:
                        hit = _b(cod, rid, ctx, obj, {"cifras_en_rojo": rojos})
        if hit:
            res.append(hit)
    return res or None


# ======================================================================= R-CRUCES-03

def _anio_ref(c) -> float:
    ini, fin = c.get("periodo_referencia_ini"), c.get("periodo_referencia_fin")
    if ini is not None and fin is not None:
        return (float(ini) + float(fin)) / 2
    per = [float(x) for x in (c.get("periodo_agrupado") or []) if x is not None]
    if len(per) >= 2:
        return (min(per) + max(per)) / 2
    return float(c.req("anio"))


@regla("R-CRUCES-03", ambito="respuesta")
def r_cruces_03(r, ctx):
    """Ventana de años entre los componentes de un cruce y años de choque."""
    rid = "R-CRUCES-03"
    p = ctx.regla(rid)["parametros"]
    res = []
    for cr in r.get("cruces") or []:
        obj = _obj(cr)
        try:
            a, b = _componentes(r, cr)
            ra, rb = _anio_ref(a), _anio_ref(b)
        except CampoFaltante as e:
            res.append(_faltante(rid, e, obj))
            continue
        vel = [a.get("velocidad_cambio"), b.get("velocidad_cambio")]
        if None in vel:
            res.append(Resultado(rid, "bloquear_cruce", "metadato_faltante", clausula="velocidad_cambio IS NULL",
                                 detalle={"campo": "velocidad_cambio"}, objetivo=obj))
            continue
        dist = abs(ra - rb)
        rez = cr.get("rezago_anios") or 0
        if rez:
            dist = max(0.0, dist - min(float(rez), float(p["rezago_declarado_max_anios"])))
        lenta = "lenta" in vel
        v = p["ventana_lenta_anios"] if lenta else p["ventana_rapida_anios"]
        det = {"anio_a": ra, "anio_b": rb, "dist": dist, "ventana": v, "velocidades": vel}
        if dist > v:
            res.append(Resultado(rid, "bloquear_cruce", "fuera_de_ventana", clausula="dist supera la ventana",
                                 detalle=det, objetivo=obj))
        elif lenta:
            res.append(Resultado(rid, "rotular", "anios_distintos", clausula="alguno lenta: dist <= ventana_lenta → rotular",
                                 detalle=det, objetivo=obj, mensaje=mensaje(rid, ctx, anio_a=a.get("anio"), anio_b=b.get("anio"))))
        elif dist > 0:
            res.append(Resultado(rid, "rotular", "anios_distintos", clausula="ambos rápida: dist = 1 → rotular",
                                 detalle=det, objetivo=obj, mensaje=mensaje(rid, ctx, anio_a=a.get("anio"), anio_b=b.get("anio"))))
        # Además: año de choque en (min, max] con algún componente socioeconómico
        anios = [_int(a.get("anio")), _int(b.get("anio"))]
        if None not in anios:
            lo, hi = min(anios), max(anios)
            choques = [x for x in (p.get("anios_choque") or ctx.pg.get("anios_choque") or []) if lo < x <= hi]
            socio = [c for c in (a, b) if c.get("es_socioeconomico")]
            # excepción (ajuste_consolidacion): el año de choque está declarado comparable en todos los socioeconómicos
            from .reglas_etapa5 import quiebres
            exentos = [x for x in choques if socio and all(any(q["anio"] == x and x in q["comparable_con"]
                                                                for q in quiebres(c)) for c in socio)]
            choques = [x for x in choques if x not in exentos]
            if choques and socio:
                res.append(Resultado(rid, "bloquear_cruce", "anio_choque",
                                     clausula="año de choque en (min, max] y componente socioeconómico",
                                     detalle={"anios_choque": choques, "exentos": exentos}, objetivo=obj, modificador=True))
        # caso borde (4): el año en curso (parcial) no se cruza con anuales cerrados
        cerr = [a.get("anio_cerrado"), b.get("anio_cerrado")]
        if False in cerr and cerr.count(False) == 1:
            res.append(Resultado(rid, "bloquear_cruce", "anio_parcial", clausula="año en curso (parcial) con anual cerrado",
                                 detalle={"anio_cerrado": cerr}, objetivo=obj, modificador=True))
    return res or None


# ======================================================================= R-CRUCES-05

def _veredicto_base(texto: str, nivel, comps, op, ctx) -> str:
    """Lee un valor de la matriz compat_base («ok», «rotular (provincia o más) / bloquear (distrito)», «bloquear salvo
    NIVEL_GOBIERNO=M o CUI», «ok solo a departamento», «lado a lado …, sin cociente», «según nivel_territorial_inferencia»)."""
    t = _norm(texto)
    rk, rdep = _rank(ctx, nivel), _rank(ctx, "departamento")
    if "segun nivel_territorial_inferencia" in t:
        for c in comps:
            nti = c.get("nivel_territorial_inferencia")
            if c.get("base_geografica_usada") == "muestra" and nti and rk is not None and _rank(ctx, nti) is not None \
                    and rk < _rank(ctx, nti):
                return "bloquear"
        return "ok"
    if "solo a departamento" in t:
        return "ok" if (rk is not None and rk >= rdep) else "bloquear"
    if "bloquear (distrito)" in t:
        return "bloquear" if nivel == "distrito" else "rotular"
    if t.startswith("bloquear salvo"):
        return "ok" if any(c.get("nivel_gobierno") == "M" or c.get("ubicado_por_cui") for c in comps) else "bloquear"
    if "sin cociente" in t:
        return "bloquear" if op not in (None, "lado_a_lado") else "rotular"
    if t.startswith("ok"):
        return "ok"
    if t.startswith("rotular"):
        return "rotular"
    return "bloquear"


def _rango_pob(po: dict, tol_m: float):
    lo = po.get("edad_min_meses")
    hi = po.get("edad_max_meses")
    return (float(lo) if lo is not None else 0.0), (float(hi) if hi is not None else math.inf)


@regla("R-CRUCES-05", ambito="respuesta")
def r_cruces_05(r, ctx):
    """Compatibilidad de base geográfica, población objetivo y universo de los componentes de un cruce."""
    rid = "R-CRUCES-05"
    p = ctx.regla(rid)["parametros"]
    matriz = {**(p.get("compat_base_distrito") or {}), **(p.get("compat_base_adicional") or {})}
    tol = float(p.get("tolerancia_edad_anios") or 0) * 12
    res = []
    for cr in r.get("cruces") or []:
        obj = _obj(cr)
        try:
            a, b = _componentes(r, cr)
            if not (es_aplicable(rid, a, ctx) or es_aplicable(rid, b, ctx)):
                continue
            ba, bb = a.req("base_geografica_usada"), b.req("base_geografica_usada")
            pa, pb = a.req("poblacion_objetivo"), b.req("poblacion_objetivo")
            ua, ub = a.req("universo"), b.req("universo")
        except CampoFaltante as e:
            res.append(_faltante(rid, e, obj))
            continue
        nivel = cr.get("nivel") or _nivel_publicado(a)
        op = _op(cr)
        motivos, peor = [], "ok"
        orden = ["ok", "rotular", "bloquear"]

        def subir(v, m):
            nonlocal peor
            motivos.append(m)
            if orden.index(v) > orden.index(peor):
                peor = v

        # base geográfica
        def nombre(base, c):
            return "ejecutora_municipal" if base == "ejecutora" and c.get("nivel_gobierno") == "M" else base
        claves = [f"{nombre(ba, a)}×{nombre(bb, b)}", f"{nombre(bb, b)}×{nombre(ba, a)}", f"{ba}×{bb}", f"{bb}×{ba}"]
        val = next((matriz[k] for k in claves if k in matriz), None)
        if val is None and "muestra" in (ba, bb):
            val = matriz.get("muestra×cualquiera")
        if _ambito_lima(cr, a, b, ctx) is not None and val and "nivel_territorial_inferencia" in val:
            ver = "ok"  # L5: ámbitos de Lima de la lista blanca
        elif val is not None:
            ver = _veredicto_base(val, nivel, (a, b), op, ctx)
        else:
            ver = "ok" if ba == bb else "bloquear"  # par fuera de la matriz: lectura restrictiva
        if ver != "ok":
            subir(ver, {"base": [ba, bb], "matriz": val, "nivel": nivel})
        # población objetivo (±tolerancia de edad, mismo sexo, misma área; anidada → rotular)
        la, ha = _rango_pob(pa, tol)
        lb, hb = _rango_pob(pb, tol)
        sexo_igual = pa.get("sexo") == pb.get("sexo")
        area_igual = pa.get("area") == pb.get("area")
        igual = abs(la - lb) <= tol and (abs(ha - hb) <= tol or ha == hb) and sexo_igual and area_igual

        def dentro(x, y):  # x ⊆ y
            (lx, hx, sx, ax), (ly, hy, sy, ay) = x, y
            return ly <= lx and hx <= hy and (sy == sx or sy in ("T", None)) and (ay == ax or ay in ("total", None))
        xa = (la, ha, pa.get("sexo"), pa.get("area"))
        xb = (lb, hb, pb.get("sexo"), pb.get("area"))
        if not igual:
            if dentro(xa, xb) or dentro(xb, xa):
                subir("rotular", {"poblacion": "anidada", "a": pa.get("descripcion"), "b": pb.get("descripcion")})
            else:
                subir("bloquear", {"poblacion": "incompatible", "a": pa.get("descripcion"), "b": pb.get("descripcion")})
        if ua != ub:
            subir("rotular", {"universo": [ua, ub]})
        if peor == "ok":
            continue
        res.append(Resultado(rid, "bloquear_cruce" if peor == "bloquear" else "rotular",
                             "compatibilidad" if peor == "bloquear" else "poblacion_distinta",
                             clausula="compat_base AND compat_poblacion AND universo compatible", detalle={"motivos": motivos},
                             objetivo=obj, mensaje=mensaje(rid, ctx, indicador_a=a.get("nombre_ciudadano") or a.get("indicador_id"),
                                                           indicador_b=b.get("nombre_ciudadano") or b.get("indicador_id"),
                                                           poblacion_a=pa.get("descripcion"), poblacion_b=pb.get("descripcion"))))
    return res or None


# ======================================================================= R-CRUCES-08

_JERARQUIA_SUBNACIONAL = {  # R-CRUCES-08.parametros.jerarquias, nivel provincia/distrito (texto de la regla)
    "pobreza_monetaria": "INEI-MAPA-POBREZA", "anemia_6_35m": "INS-CENAN-SIEN", "anemia_infantil": "INS-CENAN-SIEN"}


@regla("R-CRUCES-08", ambito="respuesta")
def r_cruces_08(r, ctx):
    """Jerarquía cuando dos o más fuentes miden el mismo concepto; bloque de divergencia; una vintage por respuesta."""
    rid = "R-CRUCES-08"
    p = ctx.regla(rid)["parametros"]
    res = []
    grupos: dict = {}
    for c in _cifras(r):
        if es_aplicable(rid, c, ctx) and c.get("concepto_medido"):
            grupos.setdefault(c.concepto_medido, []).append(c)
    for concepto, todas in grupos.items():
        pedido = r.get("nivel_pedido")
        cs = [c for c in todas if _publicable(c)]
        # caso borde (1): la fuente que encabeza la jerarquía no es publicable y hay otra que sí → se avisa y la otra
        # queda como complementaria, sin promoverla a «la cifra del concepto»
        caidas = [c for c in todas if not _publicable(c)]
        if caidas and cs and len({c.get("fuente_principal") for c in todas}) >= 2:
            caida = caidas[0]
            mejor = sorted(todas, key=lambda c: (c.get("rank_concepto") or 9,
                                                 not str(c.get("fuente_principal") or "").startswith("INEI-")))[0]
            if not _publicable(mejor) or _es_principal(caida):
                res.append(Resultado(rid, "advertir", "principal_no_alcanza",
                                     clausula="caso borde (1): la fuente principal está suprimida; la otra no la reemplaza",
                                     detalle={"concepto": concepto, "principal": caida.get("id_cifra"),
                                              "estado": _estado(caida)}, objetivo=caida.get("id_cifra")))
                for c in cs:
                    res.append(Resultado(rid, "rotular", "fuente_complementaria",
                                         clausula="caso borde (1): se muestra con su rótulo, como complementaria",
                                         detalle={"concepto": concepto, "principal_no_publicable": caida.get("id_cifra")},
                                         rotulo="complementaria", objetivo=c.get("id_cifra")))
                continue
        if len({c.get("fuente_principal") for c in cs}) < 2:
            continue

        # parametros.jerarquias (P4-01, 11/10/2026): con pedido de distrito o provincia manda la fuente que la jerarquía
        # fija para ese nivel (pobreza: Mapa 2018, R-EST-05; anemia: SIEN con rótulo), aunque otra sea más reciente
        pref = _JERARQUIA_SUBNACIONAL.get(concepto) if pedido in ("distrito", "provincia", "establecimiento") else None

        def clave(c):
            np_, rp = _rank(ctx, _nivel_publicado(c)), _rank(ctx, c.get("nivel_pedido") or pedido)
            valida = np_ is not None and rp is not None and np_ <= rp
            con_quiebre = _int(c.get("anio")) in anios_quiebre_indicador(c)
            return (pref is not None and c.get("fuente_principal") != pref, not valida, c.get("rank_concepto") or 9,
                    -(_int(c.get("anio")) or 0), con_quiebre, not str(c.get("fuente_principal") or "").startswith("INEI-"))
        orden = sorted(cs, key=clave)
        principal = orden[0]
        marcadas = [c for c in cs if _es_principal(c)]
        if marcadas and principal not in marcadas:
            res.append(Resultado(rid, "advertir", "jerarquia_fuentes",
                                 clausula="principal = primera según (válida al nivel, rank_concepto, año, sin quiebre, INEI)",
                                 detalle={"concepto": concepto, "principal_esperada": principal.get("id_cifra"),
                                          "marcadas": [c.get("id_cifra") for c in marcadas]},
                                 objetivo=marcadas[0].get("id_cifra")))
        for c in orden[1:]:
            if c.get("fuente_principal") == principal.get("fuente_principal") and _es_principal(c):
                continue  # P4: misma fuente que la principal y también principal (p. ej. los distritos de un grupo del Mapa)
            res.append(Resultado(rid, "rotular", "fuente_complementaria", clausula="las demás como complementarias",
                                 detalle={"concepto": concepto, "principal": principal.get("id_cifra")},
                                 rotulo="complementaria", objetivo=c.get("id_cifra")))
            vp, vs = principal.get("valor"), c.get("valor")
            if vp is None or vs is None:
                continue
            if (principal.get("criterio_medicion") or principal.get("criterio")) != (c.get("criterio_medicion") or c.get("criterio")):
                continue  # caso borde 3: la divergencia por criterio la resuelve R-CRUCES-04
            if principal.get("tipo_estimacion") == "proporcion":
                div, umbral = abs(float(vp) - float(vs)), float(p["umbral_divergencia_pp"])
            else:
                div = abs(float(vp) - float(vs)) / abs(float(vp)) * 100 if float(vp) else math.inf
                umbral = float(p["umbral_divergencia_poblacion_pct"])
            if div > umbral:
                res.append(Resultado(rid, "rotular", "divergencia_fuentes",
                                     clausula="|valor_principal − valor_secundaria| > umbral_divergencia",
                                     detalle={"concepto": concepto, "divergencia": round(div, 3), "umbral": umbral,
                                              "bloque": "Por qué las cifras no coinciden"},
                                     mensaje=mensaje(rid, ctx, concepto=concepto, principal=principal.get("fuente_principal")),
                                     objetivo=c.get("id_cifra"), modificador=True))
    if p.get("una_vintage_por_respuesta"):
        vint = {str(c.get("vintage_denominador")) for c in _cifras(r) if c.get("vintage_denominador")}
        if len(vint) > 1:
            res.append(Resultado(rid, "advertir", "vintage_distinta", clausula="una_vintage_por_respuesta",
                                 detalle={"vintages": sorted(vint)}, objetivo="respuesta"))
    return res or None


# ======================================================================= R-CRUCES-07

def _disparadores(ctx) -> list[str]:
    cond = ctx.regla("R-CRUCES-07").get("condicion") or ""
    m = re.search(r"disparadores:\s*([^+)]*)", cond)
    return [x.strip() for x in (m.group(1).split(",") if m else []) if x.strip()]


@regla("R-CRUCES-07", ambito="respuesta")
def r_cruces_07(r, ctx):
    """Preguntas de efecto: gasto y resultado lado a lado, sin afirmar ni negar el efecto, con evaluaciones."""
    rid = "R-CRUCES-07"
    gasto = [c for c in _cifras(r) if es_aplicable(rid, c, ctx)]
    if not gasto:
        return None
    preg = _norm(r.get("pregunta") or "")
    disp = [d for d in _disparadores(ctx) if re.search(r"\b" + re.escape(_norm(d)) + r"\b", preg)]
    if r.get("intencion_pregunta") != "efecto" and not disp:
        return None
    return Resultado(rid, "rotular", "pregunta_de_efecto",
                     clausula="intencion_pregunta == 'efecto'" if r.get("intencion_pregunta") == "efecto"
                     else "disparadores de efecto en la pregunta",
                     detalle={"estructura_respuesta": ctx.param(rid, "estructura_respuesta"),
                              "evaluaciones_fuente": ctx.param(rid, "evaluaciones_fuente"), "disparadores": disp,
                              "gasto_descriptivo_solo": True, "no_concluir": "NC-EFICIENCIA"},
                     mensaje=mensaje(rid, ctx), objetivo="respuesta")


# ======================================================================= R-ENC-11

def _bloqueada_por_quiebre(c, anio_a, anio_b) -> str | None:
    """Comparación a través de un quiebre (R-ENC-13/14; H-4): resultados previos de R-ENC-14 o R-REG-10
    (bloquear_cruce), R-CRUCES-04 (advertir) o R-ENC-13 (quiebre no comparable entre los dos años o en uno de ellos)
    y, sin resultados previos, los quiebres del indicador: q con anio_a < q <= anio_b y sin anio_a ni anio_b en
    q.comparable_con."""
    lo, hi = sorted((anio_a, anio_b))
    from .reglas_etapa5 import corta_comparacion, quiebres
    tipo_de = {q["anio"]: q["tipo"] for q in quiebres(c)}
    for x in _resultados_de(c):
        if x.get("regla") in ("R-ENC-14", "R-REG-10") and x.get("accion") == "bloquear_cruce":
            return x["regla"]
        if x.get("regla") == "R-CRUCES-04" and x.get("accion") == "advertir":
            return x["regla"]
        if x.get("regla") == "R-ENC-13" and x.get("accion") == "advertir":
            anios_q = [_int(q) for q in (x.get("detalle") or {}).get("anios_quiebre") or []]
            if any((lo <= q <= hi) and (q in (lo, hi) or corta_comparacion(tipo_de.get(q), q, lo, hi)) for q in anios_q):
                return x["regla"]
    for q in quiebres(c):
        if corta_comparacion(q["tipo"], q["anio"], lo, hi) and lo not in q["comparable_con"] and hi not in q["comparable_con"]:
            return "quiebres_indicador"
    return None


def _comparaciones(r, ctx, rid):
    """Pares (cifra, fila de comparación, objetivo) de R-ENC-11: `cifras[i].comparacion` (contrato §2e) y los cruces
    con presentación «comparacion» entre dos cifras (auditoría C-7)."""
    out = []
    for c in _cifras(r):
        comp = fila_comparacion(c)
        if comp and es_aplicable(rid, c, ctx):
            out.append((c, comp, c.get("id_cifra")))
    pid = _por_id(r)
    for cr in r.get("cruces") or []:
        if _op(cr) != "comparacion":
            continue
        a, b = pid.get(cr.get("a")), pid.get(cr.get("b"))
        if a is None or b is None or not es_aplicable(rid, b, ctx):
            continue
        comp = a.datos()
        if cr.get("prueba_cambio") and not comp.get("prueba_cambio"):
            comp["prueba_cambio"] = cr["prueba_cambio"]
        out.append((b, comp, _obj(cr)))
    return out


@regla("R-ENC-11", ambito="respuesta")
def r_enc_11(r, ctx):
    """Prueba de diferencia con diseño complejo antes de afirmar que una cifra subió, bajó o es mayor/menor."""
    rid = "R-ENC-11"
    alfa = float(ctx.param(rid, "alfa"))
    res = []
    for c, comp, cid in _comparaciones(r, ctx, rid):
        if "suprimida" in (_estado(c), comp.get("estado_cifra")) or "sin_datos" in (_estado(c), comp.get("estado_cifra")):
            res.append(Resultado(rid, "no_comparar", "suprimida", clausula="cualquiera con estado 'suprimida' → no comparar",
                                 objetivo=cid))
            continue
        ca = comp.get("criterio") or comp.get("criterio_medicion")
        cb = c.get("criterio") or c.get("criterio_medicion")
        aa, ab = _int(comp.get("anio")), _int(c.get("anio"))
        q = _bloqueada_por_quiebre(c, aa, ab) if None not in (aa, ab) and aa != ab else None
        if q or (ca and cb and ca != cb):
            res.append(Resultado(rid, "no_comparar", "quiebre", clausula="comparación a través de un quiebre (R-ENC-13/14)",
                                 detalle={"regla": q, "criterios": [ca, cb], "anios": [aa, ab]}, objetivo=cid))
            continue
        ta, tb = comp.get("territorio_id", c.get("territorio_id")), c.get("territorio_id")
        prueba = comp.get("prueba_cambio") or c.get("prueba_cambio")
        if str(ta) != str(tb) and (_contiene(ctx, ta, tb) or _contiene(ctx, tb, ta)) and not (prueba and prueba.get("p_valor") is not None):
            res.append(Resultado(rid, "no_comparar", "covarianza_no_estimada",
                                 clausula="un territorio contiene al otro: cov ≠ 0 y el motor no la estimó",
                                 detalle={"territorios": [ta, tb], "cov_ab": ctx.param(rid, "cov_ab")}, objetivo=cid))
            continue
        try:
            pr = _prueba(comp, c.datos(), ctx, prueba)
        except CampoFaltante as e:
            res.append(_faltante(rid, e, cid, accion="no_comparar"))
            continue
        refer = "referencial" in (_estado(c), comp.get("estado_cifra"))
        sig = pr["p_valor"] < alfa
        dif = pr.get("diferencia")
        rot = ("cambio estadísticamente claro" if sig else "sin cambio estadísticamente claro") + \
              (" (con cifras referenciales)" if refer else "")
        res.append(Resultado(rid, "rotular", "prueba_cambio",
                             clausula="p < alfa → declarar dirección" if sig else "p >= alfa → significativo = false",
                             detalle={**pr, "alfa": alfa, "significativa": sig,
                                      "direccion": (("aumento" if dif > 0 else "disminucion") if sig and dif else None),
                                      "anios": [comp.get("anio"), c.get("anio")]},
                             rotulo=rot, objetivo=cid))
    return res or None


# ======================================================================= R-ENC-12

@regla("R-ENC-12", ambito="respuesta")
def r_enc_12(r, ctx):
    """Rankings de encuesta por grupos estadísticamente semejantes (26 unidades, L8)."""
    rid = "R-ENC-12"
    p = ctx.regla(rid)["parametros"]
    enc = [c for c in _cifras(r) if es_aplicable(rid, c, ctx)]
    terr = {str(c.get("territorio_id")) for c in enc}
    if not (r.get("intencion_pregunta") in ("ranking", "identificar_extremo") or len(terr) >= 3):
        return None
    if not enc:
        return None
    res = []
    u = p.get("unidades_ranking_departamental") or {}
    lima = {"LIMA_METROPOLITANA", "LIMA_REGION"}
    if ("15" in terr and terr & lima) or "AREA_METROPOLITANA_LIMA_CALLAO" in terr:
        res.append(Resultado(rid, "bloquear_cruce", "unidades_ranking",
                             clausula="nunca el departamento 15 entero junto con LM o LR, ni el dominio 8",
                             detalle={"territorios": sorted(terr), "nunca": u.get("nunca")}, objetivo="respuesta"))
        return res
    validas = [c for c in enc if _estado(c) not in ("suprimida", "sin_datos")]
    validas.sort(key=lambda c: -(float(c.get("valor")) if c.get("valor") is not None else -math.inf))
    grupos, actual = [], []
    for c in validas:
        if not actual:
            actual = [c]
            continue
        try:
            pr = _prueba(c.datos(), actual[0].datos(), ctx)
            sig = pr["p_valor"] < float(ctx.pg.get("alfa", 0.05))
        except CampoFaltante:
            sig = False
        if sig:
            grupos.append(actual)
            actual = [c]
        else:
            actual.append(c)
    if actual:
        grupos.append(actual)
    fuera = sorted(t for t in terr if u.get("unidades") and t not in u["unidades"] and t != "15")
    det = {"grupos": [[{"id": c.get("id_cifra"), "territorio": c.get("territorio_id"),
                        "referencial": _estado(c) == "referencial"} for c in g] for g in grupos],
           "excluidas": [c.get("id_cifra") for c in enc if c not in validas],
           "puede_decir_el_mas_alto": bool(grupos) and len(grupos[0]) == 1 and len(grupos) > 1,
           "max_grupos": p.get("max_grupos"), "excede_max_grupos": len(grupos) > (p.get("max_grupos") or math.inf),
           "unidades_fuera_de_lista": fuera,
           "todas_en_un_grupo": len(grupos) == 1 and len(validas) > 1}
    if "15" in terr:
        det["nota_lima"] = u.get("sin_LM_o_LR")
    res.append(Resultado(rid, "rotular", "ranking_por_grupos",
                         clausula="pregunta de ranking u orden de >= 3 territorios con cifras de encuesta",
                         detalle=det, mensaje=mensaje(rid, ctx), objetivo="respuesta"))
    return res


# ======================================================================= R-EST-02

def _covariables(ctx, fuente) -> list[str]:
    vals = (ctx.param("R-EST-02", "covariables_conocidas") or {}).get(fuente) or []
    return [v.split(" ")[0] for v in vals]


@regla("R-EST-02", ambito="respuesta")
def r_est_02(r, ctx):
    """La estimación modelada no se resta, no se actualiza con variaciones de encuesta ni se cruza con sus covariables."""
    rid = "R-EST-02"
    res = []
    for cr in r.get("cruces") or []:
        obj = _obj(cr)
        try:
            a, b = _componentes(r, cr)
        except CampoFaltante as e:
            res.append(_faltante(rid, e, obj))
            continue
        mod = [c for c in (a, b) if es_aplicable(rid, c, ctx)]
        if not mod:
            continue
        m = mod[0]
        otro = b if m is a else a
        op = _op(cr)
        es_mod = [c.get("naturaleza_dato") == "estimacion_modelada" for c in (a, b)]
        if op in ("resta", "variacion", "tendencia") and (es_mod[0] != es_mod[1] or a.get("anio") != b.get("anio")):
            res.append(Resultado(rid, "bloquear_cruce", "modelada_vs_otra",
                                 clausula="resta/variación/tendencia con otra fuente u otro año",
                                 detalle={"operacion": op}, objetivo=obj, mensaje=mensaje(rid, ctx, **{"año": otro.get("anio")})))
        elif op == "ajuste_por_variacion_encuesta":
            res.append(Resultado(rid, "bloquear_cruce", "actualizacion_prohibida", clausula="ajuste_por_variacion_encuesta",
                                 detalle={"operacion": op}, objetivo=obj, mensaje=mensaje(rid, ctx, **{"año": otro.get("anio")})))
        elif op in ("asociacion", "correlacion") and otro.get("fuente_principal") in _covariables(ctx, m.get("fuente_principal")):
            res.append(Resultado(rid, "bloquear_cruce", "covariable_del_modelo",
                                 clausula="correlación con una covariable del propio modelo",
                                 detalle={"covariable": otro.get("fuente_principal")}, objetivo=obj))
        elif otro.get("naturaleza_dato") == "presupuestal_financiero" and otro.get("anio") != m.get("anio"):
            res.append(Resultado(rid, "advertir", "anios_distintos", clausula="cruce con gasto de años ≠ anio_referencia",
                                 detalle={"anio_modelada": m.get("anio"), "anio_gasto": otro.get("anio")}, objetivo=obj))
    # comparación entre ediciones de la misma estimación (c.comparacion)
    for c in _cifras(r):
        comp = fila_comparacion(c)
        if not comp or not es_aplicable(rid, c, ctx) or comp.get("anio") == c.get("anio"):
            continue
        from .reglas_etapa5 import quiebres
        declarada = any(_int(comp.get("anio")) in q["comparable_con"] for q in quiebres(c)) or \
            _int(comp.get("anio")) in [_int(x) for x in (c.get("comparable_con") or [])]
        if declarada:
            res.append(Resultado(rid, "rotular", "comparacion_ediciones",
                                 clausula="comparacion_entre_ediciones: declarada comparable, solo por IC",
                                 detalle={"anios": [comp.get("anio"), c.get("anio")]}, objetivo=c.get("id_cifra")))
        else:
            res.append(Resultado(rid, "bloquear_cruce", "comparacion_ediciones",
                                 clausula="comparación entre ediciones sin comparabilidad declarada",
                                 detalle={"anios": [comp.get("anio"), c.get("anio")],
                                          "regla": ctx.param(rid, "comparacion_entre_ediciones")},
                                 objetivo=c.get("id_cifra")))
    return res or None


# ======================================================================= corrector léxico (R-LENGUAJE-02, R-GASTO-15)

_MARCADOR = re.compile(r"\{\{[^}]*\}\}")


def _compilar(lista: list[dict]) -> list[tuple]:
    out = []
    for x in lista or []:
        modo = "original" if x.get("texto_original") else ("norm" if x.get("normalizar", True) else "minus")
        pat = _norm(x["patron"]) if modo == "norm" else x["patron"]
        out.append((x.get("categoria"), re.compile(pat, re.I), modo, x))
    return out


def _texto_modo(t: str, modo: str) -> str:
    return t if modo == "original" else (_norm(t) if modo == "norm" else t.lower())


def corrector(texto: str, ctx, categorias: set | None = None) -> tuple[list[dict], list[dict]]:
    """Corre lenguaje.prohibidas (bloquean) y lenguaje.avisos_pendientes_validacion (solo avisan) sobre el texto del LLM,
    con los marcadores y spans protegidos {{p:id}} reemplazados por «X». Devuelve (infracciones, avisos)."""
    t = _MARCADOR.sub("X", texto or "")
    infr, avisos = [], []
    for cat, rx, modo, _ in _compilar(ctx.lenguaje.get("prohibidas")):
        if categorias is not None and cat not in categorias:
            continue
        m = rx.search(_texto_modo(t, modo))
        if m:
            infr.append({"categoria": cat, "fragmento": m.group(0)})
    if categorias is None:
        for cat, rx, modo, _ in _compilar(ctx.lenguaje.get("avisos_pendientes_validacion")):
            m = rx.search(_texto_modo(t, modo))
            if m:
                avisos.append({"categoria": cat, "fragmento": m.group(0)})
    return infr, avisos


@lru_cache(maxsize=1)
def _corrector_estructural():
    p = RAIZ / "reglas" / "consolidador" / "corrector_estructural.py"
    spec = importlib.util.spec_from_file_location("corrector_estructural", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ======================================================================= R-GASTO-15

@regla("R-GASTO-15", ambito="respuesta")
def r_gasto_15(r, ctx):
    """Lista bloqueada simétrica en respuestas con gasto: ni juicios de valor (acusación o excusa) ni causalidad
    gasto → resultado."""
    rid = "R-GASTO-15"
    p = ctx.regla(rid)["parametros"]
    # R-GASTO-08b (etapa 5) tiene cláusulas de respuesta que el núcleo no corre en esa etapa: van aquí (H-7)
    previas = gasto_08b_respuesta(r, ctx)
    gasto = {c.get("id_cifra") for c in _cifras(r) if es_aplicable(rid, c, ctx)}
    if not gasto:
        return previas or None
    texto = r.get("texto") or ""
    infr = []
    # (a) lenguaje.prohibidas, categoría «juicio de valor» (la del gasto r2 y la general)
    jv, _ = corrector(texto, ctx, categorias={"juicio de valor"})
    infr += [{"tipo": "juicio de valor", **x} for x in jv]
    # (b) términos de lista_bloqueada y verbos causales en oraciones cuyo sujeto o complemento es gasto/programa/inversión
    ctxt = p.get("bloqueo_con_contexto") or ""
    m = re.search(r"es ([^;]+);", ctxt)
    sujetos = [_norm(w) for w in re.split(r",\s*|\s+o\s+", m.group(1))] if m else []
    for o in oraciones(texto):
        on = _norm(_MARCADOR.sub(" X ", o))
        con_gasto = bool(set(MARCADOR_C.findall(o)) & gasto) or any(re.search(r"\b" + re.escape(s), on) for s in sujetos)
        if not con_gasto:
            continue
        for term in p.get("lista_bloqueada") or []:
            if re.search(r"\b" + re.escape(_norm(term)) + r"\b", on):
                infr.append({"tipo": "lista_bloqueada", "fragmento": term, "oracion": o})
        causal, _ = corrector(o, ctx, categorias={"causal", "causal/evaluativa"})
        infr += [{"tipo": "causal", "oracion": o, **x} for x in causal]
    if not infr:
        return previas or None
    return previas + [Resultado(rid, "bloquear_cruce", "juicio_o_causalidad_gasto",
                     clausula="cifra de gasto + término de la lista bloqueada o verbo causal gasto → resultado",
                     detalle={"infracciones": infr, "plantilla": p.get("plantilla"), "gasto_descriptivo_solo": True},
                     mensaje=mensaje(rid, ctx), objetivo="respuesta")]


# ======================================================================= etapa 9: R-CRUCES-10

@regla("R-CRUCES-10", ambito="respuesta")
def r_cruces_10(r, ctx):
    """Semáforo de la respuesta: peor semáforo de las cifras principales, pisos ámbar y techo ámbar del contexto."""
    rid = "R-CRUCES-10"
    p = ctx.regla(rid)["parametros"]
    rotulos = ctx.param("R-CRUCES-09", "rotulos") or {}
    orden = [k for k in rotulos]  # verde < ambar < rojo < no_publicable
    techo = p.get("techo_contexto")

    def peor(xs):
        return max(xs, key=orden.index) if xs else None

    cifras = _cifras(r)
    principales = [c for c in cifras if _es_principal(c) and _publicable(c)]
    contexto = [c for c in cifras if not _es_principal(c) and _publicable(c)]
    if not principales:
        cb = ctx.regla(rid).get("casos_borde") or ""
        sin = re.findall(r'es \\?"([^"\\]+)\\?"', cb)
        return Resultado(rid, "rotular", "sin_cifra_principal", clausula="sin cifra principal publicable",
                         detalle={"semaforo_respuesta": "sin_cifra", "motivos": ["sin_cifra_principal"]},
                         rotulo=sin[0] if sin else None, objetivo="respuesta")
    sems = {}
    for c in principales:
        s = c.req("semaforo_cifra")
        if s not in orden:
            raise CampoFaltante("semaforo_cifra")
        sems[c.get("id_cifra")] = s
    sem = peor(list(sems.values()))
    motivos = [f"peor_cifra_principal:{k}" for k, v in sems.items() if v == sem]
    for c in contexto:
        s = c.get("semaforo_cifra")
        if s in orden:
            s2 = min(s, techo, key=orden.index) if techo in orden else s
            if orden.index(s2) > orden.index(sem):
                sem = s2
                motivos.append(f"contexto:{c.get('id_cifra')}")
    pisos = p.get("pisos_ambar") or []
    pedido = r.get("nivel_pedido")
    nivel_resp = r.get("nivel_respuesta")
    distinto = (nivel_resp is not None and pedido is not None and nivel_resp != pedido) or \
        (nivel_resp is None and pedido is not None and any(_nivel_publicado(c) != pedido for c in principales))
    coef = any(_op(cr) in ("asociacion", "correlacion") or cr.get("coeficiente") is not None for cr in r.get("cruces") or [])
    activos = {"respuesta_parcial": bool(r.get("respuesta_parcial")), "nivel_distinto_al_pedido": distinto,
               "coeficiente_asociacion": coef}
    for piso in pisos:
        if activos.get(piso):
            motivos.append(piso)
            if orden.index(sem) < orden.index("ambar"):
                sem = "ambar"
    sem_cruces = {}
    pid = _por_id(r)
    for cr in r.get("cruces") or []:
        xs = [pid[k].get("semaforo_cifra") for k in (cr.get("a"), cr.get("b")) if k in pid and pid[k].get("semaforo_cifra") in orden]
        asoc = "ambar" if (_op(cr) in ("asociacion", "correlacion") or cr.get("coeficiente") is not None) else "verde"
        sem_cruces[str(cr.get("id_cruce"))] = peor(xs + [asoc])
    return Resultado(rid, "rotular", "semaforo_respuesta", clausula="sem_resp = max(principales) con pisos ámbar",
                     detalle={"semaforo_respuesta": sem, "motivos": motivos, "semaforo_cruces": sem_cruces},
                     rotulo=rotulos.get(sem), mensaje=mensaje(rid, ctx, rotulo=rotulos.get(sem),
                                                         motivo_principal_respuesta=((r.get("ficha") or {}).get("motivo"))),
                     objetivo="respuesta")


# ======================================================================= etapa 10: R-LENGUAJE-01

def _prefijo_campo(campo: dict) -> str:
    return _norm(re.split(r"[:{]", campo.get("texto") or "")[0]).strip()


@regla("R-LENGUAJE-01", ambito="respuesta")
def r_lenguaje_01(r, ctx):
    """Ficha de límites corta y larga, con los campos obligatorios de ficha_limites (la genera el motor)."""
    rid = "R-LENGUAJE-01"
    ficha = r.get("ficha") or {}
    corta, larga = ficha.get("corta"), ficha.get("larga")
    faltan = []
    if not corta:
        faltan.append("corta")
    if not larga:
        faltan.append("larga")
    campos = (ctx.ficha.get("corta") or {}).get("campos") or []
    principales = [c for c in _cifras(r) if _es_principal(c) and _publicable(c)]
    obligatorios = [x["campo"] for x in campos]
    if not principales:  # ficha mínima: semáforo «Sin cifra disponible», fuentes consultadas y motivo
        obligatorios = [k for k in obligatorios if k in ("semaforo_respuesta", "fuentes_anios")]
    max_l = ctx.param(rid, "max_lineas_ficha_corta")
    codigos = set(((next((s for s in (ctx.ficha.get("larga") or {}).get("secciones", []) if s.get("codigos_no_concluir")),
                         {}) or {}).get("codigos_no_concluir") or {}).keys())
    if corta:
        if isinstance(corta, dict):
            faltan += [f"corta.{k}" for k in obligatorios if not corta.get(k)]
            lineas = [v for v in corta.values() if v]
            nc = corta.get("no_concluir_principal")
            if isinstance(nc, list):
                if len(nc) > 2:
                    faltan.append("corta.no_concluir_principal: más de 2 códigos")
                faltan += [f"código NC desconocido: {x}" for x in nc if codigos and x not in codigos]
        else:
            lineas = [x for x in str(corta).splitlines() if x.strip()]
            pref = {x["campo"]: _prefijo_campo(x) for x in campos}
            faltan += [f"corta.{k}" for k in obligatorios if pref.get(k) and not any(_norm(l).strip().startswith(pref[k]) for l in lineas)]
        if max_l is not None and len(lineas) > max_l:
            faltan.append(f"corta: {len(lineas)} líneas > {max_l}")
    if isinstance(larga, dict):
        por_cifra = larga.get("cifras")
        if isinstance(por_cifra, dict):
            faltan += [f"larga.cifras.{c.get('id_cifra')}" for c in principales if not por_cifra.get(c.get("id_cifra"))]
        por_cruce = larga.get("cruces")
        if isinstance(por_cruce, dict):
            faltan += [f"larga.cruces.{cr.get('id_cruce')}" for cr in r.get("cruces") or [] if not por_cruce.get(cr.get("id_cruce"))]
    if not faltan:
        return None
    return Resultado(rid, "suprimir", "ficha_incompleta", clausula="ficha corta y larga no nulas con todos los campos obligatorios",
                     detalle={"faltan": faltan}, objetivo="respuesta")


# ======================================================================= R-LENGUAJE-03

def _numeros_permitidos(ctx) -> set[str]:
    """Números de programa presupuestal listados (R-GASTO-08: codigo_origen de los temas y linaje de nombres)."""
    p = ctx.regla("R-GASTO-08").get("parametros") or {}
    txt = " ".join(str(d.get("codigo_origen") or "") for d in (p.get("temas_iniciales") or {}).values())
    txt += " " + " ".join(((p.get("nombres") or {}).get("linaje") or {}).keys())
    return set(re.findall(r"\b\d{4}\b", txt))


_RX_NUM = re.compile(r"\d+(?:[.,]\d+)*")


def _digitos_sueltos(texto: str, ctx) -> list[str]:
    t = _MARCADOR.sub(" ", texto or "")
    progs = _numeros_permitidos(ctx)
    malos = []
    for m in _RX_NUM.finditer(t):
        n = m.group(0)
        antes, despues = t[max(0, m.start() - 12):m.start()], t[m.end():m.end() + 20]
        if re.fullmatch(r"(19|20)\d\d", n) and not re.match(r"\s*%", despues):
            continue  # año
        if n in progs:
            continue  # programa presupuestal listado
        if re.match(r"\s*(?:a\s+\d+\s+)?(meses|años|año)\b", despues) or re.match(r"\s*(?:y|o)\s+más\b", despues):
            continue  # edad («6 a 35 meses», «65 años o más»)
        if re.search(r"(N\.\s?°|N°|Nº|N\.º|CUI)\s*$", antes):
            continue  # N.°, Ley N.°, CUI
        malos.append(n)
    return malos


@regla("R-LENGUAJE-03", ambito="respuesta")
def r_lenguaje_03(r, ctx):
    """El texto no escribe números: solo marcadores {{c:id}} que existan en cifras_permitidas."""
    rid = "R-LENGUAJE-03"
    texto = r.get("texto") or ""
    res = []
    malos = _digitos_sueltos(texto, ctx)
    if malos:
        res.append(Resultado(rid, "regenerar", "numero_fuera_de_marcador",
                             clausula="dígitos fuera de marcadores (salvo años y programas listados)",
                             detalle={"numeros": malos}, objetivo="respuesta"))
    ids = MARCADOR_C.findall(texto)
    if ids:
        permitidas = r.req("cifras_permitidas")
        pid = _por_id(r)
        no = [i for i in ids if i not in permitidas]
        suprimidas = [i for i in ids if i in pid and not _publicable(pid[i])]
        if no or suprimidas:
            res.append(Resultado(rid, "regenerar", "marcador_no_permitido",
                                 clausula="cada marcador debe existir en cifras_permitidas",
                                 detalle={"no_permitidos": no, "suprimidas": suprimidas}, objetivo="respuesta"))
    return res or None


# ======================================================================= R-LENGUAJE-06

def _parrafos(texto: str) -> list[str]:
    return [p for p in re.split(r"\n\s*\n|\n", texto or "") if p.strip()]


@regla("R-LENGUAJE-06", ambito="respuesta")
def r_lenguaje_06(r, ctx):
    """Párrafos que combinan datos de distinta naturaleza: una cifra por oración, verbo propio, conectores neutrales,
    sin aritmética entre cifras y año explícito si los años difieren."""
    rid = "R-LENGUAJE-06"
    p = ctx.regla(rid)["parametros"]
    verbos = {k: [_norm(v.split(" (")[0]) for v in vs] for k, vs in (p.get("verbos_por_naturaleza") or {}).items()}
    pid = _por_id(r)
    causales = _compilar([x for x in ctx.lenguaje.get("prohibidas") or [] if x.get("categoria") == "causal"])
    res = []
    for par in _parrafos(r.get("texto") or ""):
        ors = oraciones(par)
        nat_or = []
        for o in ors:
            cs = [pid[i] for i in MARCADOR_C.findall(o) if i in pid and es_aplicable(rid, pid[i], ctx)]
            nat_or.append((o, cs))
        nats = {c.get("naturaleza_dato") for _, cs in nat_or for c in cs}
        if len(nats) < 2:
            continue
        anios = {_int(c.get("anio")) for _, cs in nat_or for c in cs}
        fallas = []
        prev_nat = None
        for o, cs in nat_or:
            if not cs:
                continue
            on = _norm(o)
            ns = {c.get("naturaleza_dato") for c in cs}
            if len(ns) > 1:
                fallas.append({"a": "una cifra (una naturaleza) por oración", "oracion": o})
            for n in ns:
                vs = verbos.get(n)
                if vs and not any(v in on for v in vs):
                    fallas.append({"b": f"verbo de {n} ∉ {vs}", "oracion": o})
            if prev_nat is not None and ns != prev_nat:
                inicio = _MARCADOR.sub("X", o)[:60]
                if any(rx.search(_texto_modo(inicio, modo)) for _, rx, modo, _ in causales):
                    fallas.append({"c": "conector causal entre oraciones de distinta naturaleza", "oracion": o})
            if re.search(r"\}\}\s*(\+|−|-|×|/|más|menos)\s*\{\{c:", o) or \
                    (len(cs) > 1 and re.search(r"\b(la suma|la diferencia|veces)\b", on)):
                fallas.append({"d": "aritmética entre cifras", "oracion": o})
            if len(anios - {None}) > 1:
                for c in cs:
                    if c.get("anio") is not None and str(c.get("anio")) not in o:
                        fallas.append({"e": f"falta el año {c.get('anio')} en la oración", "oracion": o})
            prev_nat = ns
        res.append(Resultado(rid, "rotular", "naturalezas_mezcladas", clausula="párrafo con >= 2 naturaleza_dato",
                             detalle={"naturalezas": sorted(nats)}, mensaje=mensaje(rid, ctx, tipos=", ".join(sorted(nats))),
                             objetivo="respuesta"))
        if fallas:
            res.append(Resultado(rid, "regenerar", "naturalezas_mezcladas", clausula="(a)–(e) del párrafo mixto",
                                 detalle={"fallas": fallas}, objetivo="respuesta"))
    return res or None


# ======================================================================= R-LENGUAJE-02

def _frases_condicion(rid: str, ctx, antes: str) -> list[str]:
    """Frases entre comillas simples que siguen a `antes` en la condición de la regla."""
    cond = ctx.regla(rid).get("condicion") or ""
    i = cond.find(antes)
    if i < 0:
        return []
    tramo = cond[i + len(antes):].split(";")[0]
    return re.findall(r"'([^']+)'", tramo)


@regla("R-LENGUAJE-02", ambito="respuesta")
def r_lenguaje_02(r, ctx):
    """Corrector léxico y estructural del texto del LLM."""
    rid = "R-LENGUAJE-02"
    texto = r.get("texto") or ""
    infr, avisos = corrector(texto, ctx)
    pid = _por_id(r)
    estructurales = []
    vig = ctx.param("R-LENGUAJE-04", "vigencia_max_presente_anios")
    plant_anio = (_frases_condicion(rid, ctx, "edad_dato > 2 va en una oración con") or ["en {anio}"])[0]
    frases_ejec = _frases_condicion(rid, ctx, "gasto con base ejecutora →")
    frases_cui = _frases_condicion(rid, ctx, "gasto por CUI →")
    for o in oraciones(texto):
        on = _norm(o)
        for i in MARCADOR_C.findall(o):
            c = pid.get(i)
            if c is None:
                continue
            anio = _int(c.get("anio"))
            if anio is not None and vig is not None and ctx.anio_actual - anio > vig and \
                    _norm(plant_anio.replace("{anio}", str(anio))) not in on:
                estructurales.append({"regla": "edad_dato > 2 sin 'en {anio}'", "cifra": i, "oracion": o})
            if (c.get("poblacion_objetivo") or {}).get("marcador_u") and "{{u:" not in o:
                estructurales.append({"regla": "tamizaje sin {{u:id}}", "cifra": i, "oracion": o})
            if c.get("naturaleza_dato") == "presupuestal_financiero":
                if c.get("ubicado_por_cui") and frases_cui and not any(_norm(f) in on for f in frases_cui):
                    estructurales.append({"regla": f"gasto por CUI sin {frases_cui}", "cifra": i, "oracion": o})
                elif c.get("base_geografica_usada") == "ejecutora" and frases_ejec and \
                        not any(_norm(f) in on for f in frases_ejec):
                    estructurales.append({"regla": f"gasto con base ejecutora sin {frases_ejec}", "cifra": i, "oracion": o})
    censadas = {i: {"fuente": c.get("fuente_principal"), "nivel": _nivel_publicado(c)} for i, c in pid.items() if i}
    for o in _corrector_estructural().personas_censadas(texto, censadas):
        estructurales.append({"regla": "INEI-CPV2025 sin {{u:personas_censadas}}", "oracion": o})
    res = []
    if infr or estructurales:
        intentos = int(r.get("intentos_regeneracion") or 0)
        maxr = ctx.param(rid, "max_regeneraciones")
        det = {"infracciones": infr, "estructurales": estructurales, "intentos": intentos}
        if maxr is not None and intentos >= maxr:
            res.append(Resultado(rid, "revision_humana", "lenguaje_prohibido",
                                 clausula="tras max_regeneraciones intentos → plantilla determinista y revisión humana",
                                 detalle={**det, "plantilla_determinista": True}, objetivo="respuesta"))
        else:
            res.append(Resultado(rid, "regenerar", "lenguaje_prohibido",
                                 clausula="match(lenguaje.prohibidas) o regla estructural → regenerar", detalle=det,
                                 objetivo="respuesta"))
    if avisos:
        res.append(Resultado(rid, "advertir", "aviso_corrector", clausula="avisos_pendientes_validacion (solo avisan)",
                             detalle={"avisos": avisos}, aviso="corrector_pendiente_validacion", objetivo="respuesta",
                             modificador=True))
    return res or None


# ======================================================================= R-LENGUAJE-05

def _intenciones_rechazo(ctx) -> list[str]:
    cond = ctx.regla("R-LENGUAJE-05").get("condicion") or ""
    m = re.search(r"intencion in \(([^)]*)\)\s*→\s*rechazo", cond)
    return re.findall(r"'([^']+)'", m.group(1)) if m else []


@regla("R-LENGUAJE-05", ambito="respuesta")
def r_lenguaje_05(r, ctx):
    """Respuesta completa, parcial, alternativa, sin datos o rechazo, con la fórmula estándar."""
    rid = "R-LENGUAJE-05"
    fr = ctx.lenguaje.get("frases_estandar") or {}
    if r.get("intencion_pregunta") in _intenciones_rechazo(ctx):
        return Resultado(rid, "rotular", "fuera_de_alcance", clausula="intención fuera de alcance → rechazo",
                         detalle={"estado_respuesta": "rechazo"}, mensaje=fr.get("fuera_alcance"), objetivo="respuesta")
    estados = {}
    for c in _cifras(r):
        if not _es_principal(c):
            continue
        e = _estado(c)
        estados[c.get("id_cifra")] = "publicable" if e in ("publicable", "referencial") else \
            ("alternativa" if e in ("agregada", "agrupada") else "sin_datos")
    bloqueados = [x.objetivo for x in (r.get("resultados_previos") or [])
                  if getattr(x, "accion", None) == "bloquear_cruce" and str(getattr(x, "objetivo", "")).startswith("cruce:")]
    for cr in r.get("cruces") or []:
        if _obj(cr) in bloqueados:
            estados[_obj(cr)] = "sin_datos"
    if not estados:
        return None
    vals = list(estados.values())
    faltan = [k for k, v in estados.items() if v != "publicable"]
    alternativas = [k for k, v in estados.items() if v == "alternativa"]
    det = {"componentes": estados, "faltantes": faltan, "max_alternativas": ctx.param(rid, "max_alternativas")}
    if all(v == "publicable" for v in vals):
        return None
    if "publicable" in vals:
        res = [Resultado(rid, "rotular", "respuesta_parcial", clausula=">= 1 publicable → parcial (listar faltantes)",
                         detalle={**det, "estado_respuesta": "parcial"}, mensaje=mensaje(rid, ctx), objetivo="respuesta")]
        if not r.get("respuesta_parcial"):
            res.append(Resultado(rid, "advertir", "respuesta_parcial", clausula="respuesta_parcial no marcada",
                                 detalle={"respuesta_parcial": r.get("respuesta_parcial")}, objetivo="respuesta",
                                 modificador=True))
        return res
    if alternativas:
        res = [Resultado(rid, "rotular", "alternativa", clausula="0 publicables y >= 1 alternativa",
                         detalle={**det, "estado_respuesta": "alternativa"}, mensaje=mensaje(rid, ctx), objetivo="respuesta")]
        if len(alternativas) > (ctx.param(rid, "max_alternativas") or math.inf):
            res.append(Resultado(rid, "advertir", "alternativa", clausula="más alternativas que max_alternativas",
                                 detalle={"alternativas": alternativas}, objetivo="respuesta", modificador=True))
        return res
    return Resultado(rid, "rotular", "sin_datos", clausula="0 publicables y 0 alternativas → sin_datos",
                     detalle={**det, "estado_respuesta": "sin_datos"}, mensaje=fr.get("sin_datos"), objetivo="respuesta")


# ======================================================================= R-LENGUAJE-08

@regla("R-LENGUAJE-08", ambito="respuesta")
def r_lenguaje_08(r, ctx):
    """Neutralidad: cifras atribuidas a entidades y años, nunca a autoridades, partidos o gestiones."""
    rid = "R-LENGUAJE-08"
    p = ctx.regla(rid)["parametros"]
    intenciones = p.get("intenciones") or {}
    res = []
    if r.get("intencion_pregunta") in intenciones:
        res.append(Resultado(rid, "rotular", "reformular", clausula="intención de juicio → reformular con plantilla neutral",
                             detalle={"intencion": r.intencion_pregunta, "plantilla_neutral": intenciones[r.intencion_pregunta]},
                             mensaje=mensaje(rid, ctx), objetivo="respuesta"))
    cond = ctx.regla(rid).get("condicion") or ""
    m = re.search(r"texto menciona ([\w|áéíóúñ]+) junto", cond)
    palabras = [_norm(w) for w in (m.group(1).split("|") if m else [])]
    malas = []
    for o in oraciones(r.get("texto") or ""):
        if not MARCADOR_C.search(o):
            continue
        on = _norm(_MARCADOR.sub(" ", o))
        hit = [w for w in palabras if re.search(r"\b" + re.escape(w) + r"\w*", on)]
        if hit:
            malas.append({"oracion": o, "palabras": hit})
    if malas:
        res.append(Resultado(rid, "regenerar", "atribucion_a_personas",
                             clausula="texto menciona autoridad|partido|gestión junto a una cifra → regenerar",
                             detalle={"oraciones": malas}, objetivo="respuesta"))
    return res or None
