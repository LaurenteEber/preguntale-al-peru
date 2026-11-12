"""Reglas de la etapa 4 (precisión y calidad de la cifra) del validador del piloto (P2, grupo B).

Fuente de verdad: reglas/reglas.json (condición, parámetros, mensajes, casos borde y decisiones posteriores).
Contrato de campos: docs/especificaciones/contrato_validador.md. Informe de interpretación:
00_proyecto/piloto/p2/informe_implementador_B.md.

Unidades (contrato §2): en el cubo `valor`, `ee`, `cv`, `ic_inf`, `ic_sup`, `cota_inf` y `cota_sup` están en %; el núcleo
crea `p`/`estimacion` en proporción (0–1) y `ee_prop` = ee/100 en proporciones. Los umbrales de las reglas de encuestas
están en proporción (0,15 = 15 %); los de registros y gasto, en % o en puntos porcentuales (pp), según su nombre.

Convención: las cláusulas que compiten (publicar, referencial, suprimir…) se evalúan en el orden escrito y gana la
primera; las marcadas «Modificador» o «Además» y las acumulables independientes (rotular, advertir, revision_humana)
se devuelven con `modificador=True`.
"""
from __future__ import annotations

import datetime as _dt
import json
import math
import re
from pathlib import Path

from .nucleo import CampoFaltante, Resultado, regla

# ======================================================================= ayudas comunes (también las usa reglas_etapa6_7)

_ORDEN_DEFECTO = ["bloquear_cruce", "suprimir", "agregar_nivel", "agrupar_anios", "publicar_referencial", "publicar"]
_MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
          "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}


def _f(x):
    """Número o None (acepta NA de pandas, cadenas vacías y NaN)."""
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


def _req_num(c, campo):
    v = _f(c.req(campo))
    if v is None:
        raise CampoFaltante(campo)
    return v


def fmt_num(x, dec: int = 1) -> str:
    """Formato con coma decimal (R-LENGUAJE-03 fija el formato final)."""
    if x is None:
        return "—"
    return f"{float(x):.{dec}f}".replace(".", ",")


def fmt_total(x) -> str:
    """Totales expandidos o montos: redondeo a miles con espacio de miles."""
    return f"{round(float(x), -3):,.0f}".replace(",", " ")


def partes_mensaje(ctx, rid: str) -> tuple[str, list[tuple[str, str]]]:
    """Separa mensaje_usuario en el texto general y las variantes «(etiqueta) «texto»» en su orden."""
    m = ctx.regla(rid).get("mensaje_usuario") or ""
    variantes = [(a.strip(), b.strip()) for a, b in re.findall(r"\(([^()]*)\)\s*«([^»]*)»", m)]
    general = re.split(r"\([^()]*\)\s*«", m)[0].strip()
    if general.startswith("«") and general.endswith("»"):
        general = general[1:-1]
    if not general and not variantes:
        general = m
    return general, variantes


def rellenar(texto: str | None, **vals) -> str | None:
    """Rellena los marcadores {x} conocidos; deja intactos los que no tienen valor."""
    if texto is None:
        return None
    def rep(mo):
        k = mo.group(1).strip()
        v = vals.get(k)
        return mo.group(0) if v is None else str(v)
    return re.sub(r"\{([^{}|]+)\}", rep, texto)


def mensaje(ctx, rid: str, etiqueta: str | None = None, **vals) -> str | None:
    """Texto de mensaje_usuario: la variante cuya etiqueta contiene `etiqueta` (o el general) con los marcadores."""
    general, variantes = partes_mensaje(ctx, rid)
    texto = general
    if etiqueta is not None:
        for et, t in variantes:
            if etiqueta in et:
                texto = t
                break
    return rellenar(texto or None, **vals)


def cita(ctx, rid: str, inicio: str) -> str | None:
    """Texto entre «» de la condición o del mensaje de una regla que empieza con `inicio`."""
    r = ctx.regla(rid)
    for campo in ("condicion", "mensaje_usuario", "implementacion"):
        for t in re.findall(r"«([^»]*)»", r.get(campo) or ""):
            if t.startswith(inicio):
                return t
    return None


def previos(c) -> list:
    """Resultados de las reglas ya corridas en la cifra (Resultado o dict, para los casos de prueba)."""
    out = []
    for r in c.resultados_previos or []:
        out.append(r if isinstance(r, dict) else r.__dict__)
    return out


def accion_previa(c, ctx) -> str:
    """Acción vigente (la fija el núcleo antes de cada regla; si falta, se recalcula de resultados_previos)."""
    if c.accion_previa:
        return c.accion_previa
    orden = ctx.param("R-MOTOR-02", "orden_restriccion", _ORDEN_DEFECTO)
    acc = [r.get("accion") for r in previos(c) if r.get("accion") in orden]
    return min(acc, key=orden.index) if acc else "publicar"


def fecha(x) -> _dt.date | None:
    if x is None:
        return None
    if isinstance(x, _dt.datetime):
        return x.date()
    if isinstance(x, _dt.date):
        return x
    s = str(x)[:10]
    try:
        return _dt.date.fromisoformat(s)
    except ValueError:
        return None


def fecha_de_texto(texto: str, anio: int) -> _dt.date | None:
    """«31 de marzo del año siguiente» / «30 de junio del año siguiente» → fecha para el año dado."""
    mo = re.search(r"(\d{1,2}) de (\w+)( del año siguiente)?", texto or "")
    if not mo or mo.group(2).lower() not in _MESES:
        return None
    return _dt.date(anio + (1 if mo.group(3) else 0), _MESES[mo.group(2).lower()], int(mo.group(1)))


def wilson(num: float, n: float, z: float = 1.959963984540054) -> tuple[float, float]:
    """IC de Wilson al 95 % en % (R-REG-03 para proporciones de registros)."""
    if n <= 0:
        return 0.0, 100.0
    p = num / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    medio = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centro - medio) * 100, min(1.0, centro + medio) * 100


def ventana_agrupable(c, ctx, k_max: int) -> list[int] | None:
    """Ventana más reciente de hasta k_max años consecutivos que termina en el año de la cifra (R-ENC-10, R-REG-03):
    todos con datos, sin cruzar un quiebre ni un año de choque (salvo quiebres[].comparable_con). None si no hay
    ventana de al menos 2 años o si la cifra ya es de un periodo agrupado."""
    if c.periodo_agrupado:
        return None
    anio = int(c.req("anio"))
    disponibles = set(int(a) for a in (c.anios_disponibles or []))
    quiebres = c.quiebres or []
    excepciones = set()
    for q in quiebres:
        excepciones.update(int(a) for a in (q.get("comparable_con") or []))
    choque = [int(a) for a in (ctx.pg.get("anios_choque") or [])]
    for k in range(int(k_max), 1, -1):
        anios = list(range(anio - k + 1, anio + 1))
        if disponibles and not set(anios) <= disponibles:
            continue
        a, b = anios[0], anios[-1]
        cruza = False
        for q in quiebres:
            qa = int(q["anio"])
            # caso borde de R-ENC-10 (auditoría H-17): el quiebre no corta si su propio año está en comparable_con
            if a < qa <= b and qa not in set(int(x) for x in (q.get("comparable_con") or [])):
                cruza = True
        for qa in (c.anios_con_quiebre or []):
            if a < int(qa) <= b and int(qa) not in excepciones:
                cruza = True
        if any(x in anios and x not in excepciones for x in choque):
            cruza = True
        if not cruza:
            return anios
    return None


def nivel_superior(c, ctx) -> str | None:
    """Nivel estándar inmediatamente más grueso (provincia, departamento, nacional) según NIVEL_RANK."""
    r = ctx.nivel_rank(c.nivel) if c.nivel else None
    if r is None:
        return None
    for niv in ("provincia", "departamento", "nacional"):
        rr = ctx.nivel_rank(niv)
        if rr is not None and rr > r:
            return niv
    return None


def _avisos(c) -> list:
    a = c.avisos or []
    if isinstance(a, str):
        try:
            a = json.loads(a)
        except ValueError:
            a = [a]
    return list(a)


# ======================================================================= encuestas

@regla("R-ENC-01")
def r_enc_01(c, ctx):
    """Diseño muestral completo: sin estrato, conglomerado o factor no se publica (suprimir + revisión humana)."""
    rid = "R-ENC-01"
    if c.naturaleza_dato != "encuesta_muestral":
        return None
    vd = c.variables_diseno if isinstance(c.variables_diseno, dict) else {}
    faltan = [k for k in ("estrato", "conglomerado", "factor") if not vd.get(k)]
    if faltan:
        return [Resultado(rid, "suprimir", "metadato_faltante", clausula="variables_diseno incompletas",
                          detalle={"faltan": faltan}),
                Resultado(rid, "revision_humana", "sin_diseno", clausula="caso borde: base sin estrato o conglomerado",
                          detalle={"faltan": faltan}, modificador=True)]
    # Salidas obligatorias por celda (enunciado e implementación); n efectivo y deff pueden faltar si ee = 0 (R-ENC-04).
    c.req("ee", "cv", "ic_inf", "ic_sup", "metodo_ic", "n_sin_ponderar", "gl")
    if (_f(c.ee) or 0) > 0:
        c.req("n_efectivo", "deff")
    return None


@regla("R-ENC-02")
def r_enc_02(c, ctx):
    rid = "R-ENC-02"
    n = _req_num(c, "n_sin_ponderar")
    n_sup, n_pub = ctx.param(rid, "n_min_suprimir"), ctx.param(rid, "n_min_publicar")
    if n < n_sup:
        return Resultado(rid, "suprimir", "pocos_casos", clausula=f"n_sin_ponderar < {n_sup}",
                         detalle={"n_sin_ponderar": n}, mensaje=mensaje(ctx, rid, f"<{n_sup}"))
    if n < n_pub:
        return Resultado(rid, "publicar_referencial", "pocos_casos", clausula=f"{n_sup} <= n_sin_ponderar <= {n_pub - 1}",
                         detalle={"n_sin_ponderar": n}, mensaje=mensaje(ctx, rid, f"{n_sup}–"),
                         rotulo=ctx.param("R-ENC-05", "formato_referencial"))
    return None


def _cv_ref_proporcion(c):
    p = _f(c.p)
    if p is None:
        p = _req_num(c, "valor") / 100
    ee = _f(c.ee_prop)
    if ee is None:
        ee = _req_num(c, "ee") / 100
    m = min(p, 1 - p)
    return p, ee, (ee / m if m > 0 else None)


@regla("R-ENC-03")
def r_enc_03(c, ctx):
    rid = "R-ENC-03"
    n = _req_num(c, "n_sin_ponderar")
    if n < ctx.param("R-ENC-02", "n_min_suprimir"):
        return None  # menos de 25 casos: R-ENC-02 suprime. Desde 25 casos rige también el CV (C-M0-11-2, dueño, 12/11/2026)
    te = c.req("tipo_estimacion")
    if te == "proporcion":
        p, _, cv_ref = _cv_ref_proporcion(c)
        if p < ctx.param(rid, "p_min_regla_cv") or p > ctx.param(rid, "p_max_regla_cv"):
            return None  # rige R-ENC-04 (bordes 0,10 y 0,90 quedan aquí)
        if cv_ref is None:
            return None
    elif te in ("media", "total", "razon"):
        est = _req_num(c, "estimacion")
        ee = _req_num(c, "ee")
        if est == 0:
            return Resultado(rid, "revision_humana", "precision", clausula="caso borde: CV no definido (estimación 0)",
                             detalle={"estimacion": est})
        cv_ref = ee / abs(est)
    else:
        return None
    cv_ref = round(cv_ref, 10)
    cv_pub, cv_sup = ctx.param(rid, "cv_publicar"), ctx.param(rid, "cv_suprimir")
    det = {"cv_ref": cv_ref, "n_sin_ponderar": n}
    if cv_ref <= cv_pub:
        gl = _req_num(c, "gl")
        if gl < ctx.param("R-ENC-04", "gl_min"):
            return Resultado(rid, "publicar_referencial", "precision", clausula="Modificador: publicar con gl < 8",
                             detalle={**det, "gl": gl}, modificador=True,
                             rotulo=ctx.param("R-ENC-05", "formato_referencial"))
        return None
    if cv_ref <= cv_sup:
        return Resultado(rid, "publicar_referencial", "precision", clausula=f"{cv_pub} < cv_ref <= {cv_sup}", detalle=det,
                         mensaje=mensaje(ctx, rid, "15–30", ic_inf=fmt_num(c.ic_inf), ic_sup=fmt_num(c.ic_sup)),
                         rotulo=ctx.param("R-ENC-05", "formato_referencial"))
    return Resultado(rid, "suprimir", "precision", clausula=f"cv_ref > {cv_sup}", detalle=det,
                     mensaje=mensaje(ctx, rid, ">30"))


@regla("R-ENC-04")
def r_enc_04(c, ctx):
    rid = "R-ENC-04"
    if c.req("tipo_estimacion") != "proporcion":
        return None
    n = _req_num(c, "n_sin_ponderar")
    p, ee, cv_ref = _cv_ref_proporcion(c)
    if not (p < ctx.param("R-ENC-03", "p_min_regla_cv") or p > ctx.param("R-ENC-03", "p_max_regla_cv")):
        return None
    if n < ctx.param("R-ENC-02", "n_min_suprimir"):
        return None  # menos de 25 casos: R-ENC-02 suprime. Desde 25 casos rige también el intervalo (C-M0-11-2, 12/11/2026)
    ic_inf, ic_sup = _req_num(c, "ic_inf"), _req_num(c, "ic_sup")
    gl = _req_num(c, "gl")
    n_ef = _f(c.n_efectivo)
    if n_ef is None:
        if ee == 0:
            n_ef = n  # caso borde: ee = 0 → n efectivo = n sin ponderar
        else:
            raise CampoFaltante("n_efectivo")
    n_ef = min(n_ef, n)
    ancho_abs = round((ic_sup - ic_inf) / 100, 10)
    ancho_rel = round(ancho_abs / min(p, 1 - p), 10) if 0 < p < 1 else None  # simétrico (justificación; H-9)
    P = lambda k: ctx.param(rid, k)  # noqa: E731
    det = {"p": p, "n_efectivo": n_ef, "ancho_abs": ancho_abs, "ancho_rel": ancho_rel, "gl": gl, "cv_ref": cv_ref}
    out = []
    ref = ctx.param("R-ENC-05", "formato_referencial")
    if n_ef < P("n_efectivo_suprimir"):
        out.append(Resultado(rid, "suprimir", "precision", clausula=f"n_efectivo < {P('n_efectivo_suprimir')}", detalle=det))
    elif ancho_abs >= P("ancho_abs_max"):
        out.append(Resultado(rid, "suprimir", "precision", clausula="ancho_abs >= 0.30", detalle=det))
    elif ancho_rel is not None and ancho_rel > P("ancho_rel_max") and ancho_abs > P("ancho_abs_presentar"):
        out.append(Resultado(rid, "suprimir", "precision", clausula="ancho_rel > 1.30 y ancho_abs > 0.05", detalle=det))
    elif ((ancho_rel is not None and ancho_rel > P("ancho_rel_referencial") and ancho_abs > P("ancho_abs_presentar"))
          or n_ef < P("n_efectivo_min") or gl < P("gl_min")):
        out.append(Resultado(rid, "publicar_referencial", "precision",
                             clausula="ancho_rel > 0.59 y ancho_abs > 0.05, n_efectivo < 50 o gl < 8", detalle=det,
                             mensaje=mensaje(ctx, rid, "referencial"), rotulo=ref))
    elif cv_ref is not None and round(cv_ref, 10) > P("cv_referencial_inei"):
        out.append(Resultado(rid, "publicar_referencial", "precision", clausula="L9: cv_ref > 0.15 (convención INEI)",
                             detalle=det, mensaje=mensaje(ctx, rid, "referencial"), rotulo=ref))
    # Además (no en lugar de): numerador 0 o igual al denominador → el límite del intervalo, nunca «0 %» ni «100 %».
    num = _f(c.numerador)
    cero = (num == 0) if num is not None else (p == 0)
    todo = (num is not None and num == _f(c.denominador if c.denominador is not None else n)) if num is not None else (p == 1)
    if cero:
        out.append(Resultado(rid, "rotular", "precision", clausula="Además: numerador == 0", modificador=True,
                             rotulo=f"menos de {fmt_num(ic_sup)} %", detalle={"ic_sup": ic_sup},
                             mensaje=mensaje(ctx, rid, "numerador 0", ic_sup=fmt_num(ic_sup))))
    elif todo:
        out.append(Resultado(rid, "rotular", "precision", clausula="Además: numerador == n", modificador=True,
                             rotulo=f"más de {fmt_num(ic_inf)} %", detalle={"ic_inf": ic_inf}))
    return out or None


@regla("R-ENC-19")
def r_enc_19(c, ctx):
    """No respuesta del ítem (K-07, dueño, 12/11/2026): más de `tasa_referencial` → referencial; más de `tasa_aviso` → aviso en la
    capa 2 (`advertir`, no cambia el estado). La tasa (0–1) viene de la estimación; si no se midió, la regla no dispara: no se
    inventa una tasa. El interruptor `compuertas.paso_no_respuesta_activo` lo lee `inferencia/compuertas.py`, no esta función."""
    rid = "R-ENC-19"
    t = _f(c.tasa_no_respuesta_item)
    if t is None:
        return None
    t_aviso, t_ref = ctx.param(rid, "tasa_aviso"), ctx.param(rid, "tasa_referencial")
    det = {"tasa_no_respuesta_item": t}
    if t > t_ref:
        return Resultado(rid, "publicar_referencial", "no_respuesta", clausula=f"tasa_no_respuesta_item > {t_ref}", detalle=det,
                         mensaje=mensaje(ctx, rid, ">20"), rotulo=ctx.param("R-ENC-05", "formato_referencial"))
    if t > t_aviso:
        return Resultado(rid, "advertir", "no_respuesta", clausula=f"{t_aviso} < tasa_no_respuesta_item <= {t_ref}", detalle=det,
                         mensaje=mensaje(ctx, rid, "5–20"), aviso="no_respuesta_item")
    return None


@regla("R-ENC-05")
def r_enc_05(c, ctx):
    """Cómo se muestra: valor, IC, fuente, año, territorio y n; referenciales entre paréntesis."""
    rid = "R-ENC-05"
    acc = accion_previa(c, ctx)
    if acc not in ("publicar", "publicar_referencial"):
        return None
    valor, ic_inf, ic_sup = _req_num(c, "valor"), _req_num(c, "ic_inf"), _req_num(c, "ic_sup")
    n = _req_num(c, "n_sin_ponderar")
    if c.tipo_estimacion == "total":
        sv, si, ss = fmt_total(valor), fmt_total(ic_inf), fmt_total(ic_sup)
    else:
        dec = ctx.param(rid, "decimales_porcentaje")
        if round(ic_inf, dec) == round(valor, dec) or round(ic_sup, dec) == round(valor, dec):
            dec += 1  # caso borde: el IC redondeado colapsa → 2 decimales
        sv, si, ss = fmt_num(valor, dec), fmt_num(ic_inf, dec), fmt_num(ic_sup, dec)
    referencial = acc == "publicar_referencial"
    if referencial:
        sv = f"({sv})"
    fuente = (ctx.catalogo.get(c.fuente) or {}).get("sigla") or c.fuente
    unidad = {"persona": "personas", "hogar": "hogares"}.get(c.unidad_observacion, c.unidad_observacion)
    edad_max = ((c.get("poblacion_objetivo") or {}) if hasattr(c, "get") else {}).get("edad_max_meses")
    if c.unidad_observacion == "persona" and edad_max is not None and int(edad_max) <= 59:
        unidad = "niñas y niños"  # P4-13: «242 personas encuestados» → «242 niñas y niños encuestados»
    texto = mensaje(ctx, rid, valor=sv, ic_inf=si, ic_sup=ss, fuente=fuente, anio=c.anio,
                    territorio=c.territorio_nombre or c.territorio_id, n_sin_ponderar=int(n), unidad=unidad)
    return Resultado(rid, "rotular", "formato", clausula=f"estado {'referencial' if referencial else 'publicable'}",
                     rotulo=texto, mensaje=texto, detalle={"referencial": referencial})


@regla("R-ENC-10")
def r_enc_10(c, ctx):
    """Pide agrupar hasta 3 años si la celda anual se suprimió por n o CV. El cubo no trae años agrupados: la
    estimación agrupada y su reevaluación (R-ENC-02..04) las hace el motor (R-MOTOR-01)."""
    rid = "R-ENC-10"
    supr = [r for r in previos(c) if r.get("regla") in ("R-ENC-02", "R-ENC-03", "R-ENC-04")
            and r.get("accion") == "suprimir"]
    if not supr or accion_previa(c, ctx) != "suprimir":
        return None
    anios = ventana_agrupable(c, ctx, ctx.param(rid, "k_max"))
    if not anios:
        return None  # sin ventana válida (quiebre, choque, sin años o ya agrupada): sigue agregar_nivel (R-MOTOR-01)
    a, b = anios[0], anios[-1]
    ref = anios[len(anios) // 2]  # año central; con k par, redondeado hacia arriba
    return Resultado(rid, "agrupar_anios", supr[0].get("motivo") or "precision", clausula="celda anual suprimida por n o CV",
                     detalle={"periodo": [a, b], "anios": anios, "k": len(anios), "anio_referencia": ref,
                              "factor": ctx.param(rid, "factor_agrupado"),
                              "estrato": ctx.param(rid, "estrato_agrupado"), "suprimida_por": supr[0].get("regla")},
                     rotulo=f"promedio {a}–{b}",
                     mensaje=mensaje(ctx, rid, anio_ini=a, anio_fin=b, territorio=c.territorio_nombre or c.territorio_id))


def _tolerancia_dorada(c, ctx, fila: dict) -> float:
    rid = "R-ENC-18"
    t = _f(fila.get("tolerancia_pp"))
    if t is not None:
        return t
    if c.fuente == "MINEDU-UMC-ENLA":
        return ctx.param(rid, "tolerancia_pp_enla")
    if c.fuente == "INEI-ENDES" and c.tema == "anemia":
        return ctx.param(rid, "tolerancia_pp_anemia_endes")
    return ctx.param(rid, "tolerancia_pp")


def _es_true(v) -> bool:
    return v is True or str(v).strip().lower() in ("true", "1", "si", "sí")


@regla("R-ENC-18")
def r_enc_18(c, ctx):
    """Validación contra lo oficial. «validado_contra_oficial» del indicador se lee del cubo (indicador_validado: todas
    las doradas bloqueantes reproducidas en P1); dim_indicador.validado_contra_oficial queda en false a propósito."""
    rid = "R-ENC-18"
    out = []
    ind = c.indicador_id
    doradas = [d for d in ctx.doradas if d.get("indicador_id") == ind]
    bloq = [d for d in doradas if _es_true(d.get("bloqueante"))]
    # (1) indicador validado: P1 reprodujo todas sus doradas bloqueantes, con nacional y ≥ 3 departamentos
    n_dep = len({d["territorio"] for d in bloq if d.get("nivel") == "departamento"})
    n_nac = sum(1 for d in bloq if d.get("nivel") == "nacional")
    validado = c.indicador_validado is True or _es_true(c.indicador_validado)
    minimo = ctx.param(rid, "departamentos_validacion_min")
    if not validado or n_nac < 1 or n_dep < minimo:
        out.append(Resultado(rid, "revision_humana", "validacion_oficial", clausula="indicador no validado contra lo oficial",
                             detalle={"indicador_validado": c.indicador_validado, "doradas_nacionales": n_nac,
                                      "doradas_departamentales": n_dep, "minimo_departamentos": minimo}))
    # (2) |estimación − cifra oficial| > tolerancia en la celda que tiene dorada bloqueante
    propias = [d for d in bloq if str(d.get("anio")) == str(c.anio) and d.get("nivel") == c.nivel
               and str(d.get("territorio")) == str(c.territorio_id)]
    if c.validada_dorada:
        propias += [d for d in bloq if d.get("id_cifra") == c.validada_dorada and d not in propias]
    valor = _f(c.valor)
    for d in propias:
        of = _f(d.get("valor_publicado"))
        if of is None or valor is None:
            continue
        dec = int(_f(d.get("decimales")) or 1)
        dif = round(abs(round(valor, dec) - of), 6)
        tol = _tolerancia_dorada(c, ctx, d)
        if dif > tol + 1e-9:
            out.append(Resultado(rid, "revision_humana", "validacion_oficial", clausula="|estimacion − cifra_oficial| > tolerancia",
                                 detalle={"dorada": d.get("id_cifra"), "oficial": of, "motor": valor, "diferencia": dif,
                                          "tolerancia": tol}))
        # V4 (10/10/2026): el CV publicado de la ENAHO es dato y no bloquea; aviso si difiere más de lo tolerado
        cvp, cv = _f(d.get("cv_publicado")), _f(c.cv)
        if cvp is not None and cv is not None:
            tcv = _f(d.get("tolerancia_cv"))
            if tcv is None:
                mo = re.search(r"difiere en más de ([\d,\.]+) puntos", ctx.param(rid, "tolerancia_nota") or "")
                tcv = float(mo.group(1).replace(",", ".")) if mo else None
            if tcv is not None and abs(cv - cvp) > tcv + 1e-9:
                out.append(Resultado(rid, "advertir", "validacion_oficial", clausula="V4: CV distinto del publicado",
                                     aviso="cv_difiere_publicado", modificador=True,
                                     detalle={"dorada": d.get("id_cifra"), "cv_publicado": cvp, "cv_motor": cv,
                                              "tolerancia": tcv}))
    # (3) versión de la base distinta de la vigente del INEI (si el motor trae ambas)
    if c.version_base is not None and c.version_vigente_inei is not None and c.version_base != c.version_vigente_inei:
        out.append(Resultado(rid, "revision_humana", "validacion_oficial", clausula="version_base != version_vigente_inei",
                             detalle={"version_base": c.version_base, "version_vigente_inei": c.version_vigente_inei}))
    # (4) caso borde: construcción propia sin cifra oficial → revisión de un segundo analista y rótulo
    if c.origen_cifra == "propio":
        fuente = (ctx.catalogo.get(c.fuente) or {}).get("sigla") or c.fuente
        out.append(Resultado(rid, "revision_humana", "validacion_oficial", clausula="caso borde: construcción propia",
                             modificador=True))
        out.append(Resultado(rid, "rotular", "validacion_oficial", clausula="caso borde: construcción propia", modificador=True,
                             rotulo=f"cálculo propio de Pregúntale al Perú con datos de {fuente}"))
    # (5) P1: Lima Región y Callao de la ENDES no tienen dorada propia (DOR-10): aviso en el registro, no al usuario
    if c.fuente == "INEI-ENDES" and c.nivel in ("LIMA_REGION", "CALLAO") and not c.validada_dorada and not propias:
        out.append(Resultado(rid, "advertir", "validacion_oficial", clausula="DOR-10: ámbito sin dorada propia",
                             aviso="DOR-10", modificador=True, detalle={"al_usuario": False}))
    return out or None


# ======================================================================= registros administrativos

@regla("R-REG-01")
def r_reg_01(c, ctx):
    rid = "R-REG-01"
    if c.tipo_medida is None:  # caso borde: no publicar hasta asignar tipo_medida (revisión humana)
        return [Resultado(rid, "suprimir", "metadato_faltante", clausula="caso borde: tipo_medida nulo",
                          detalle={"campo": "tipo_medida"}),
                Resultado(rid, "revision_humana", "metadato_faltante", clausula="caso borde: tipo_medida nulo", modificador=True)]
    if c.tipo_medida == "prevalencia" or c.naturaleza_dato not in ("registro_administrativo", "indicadores_derivados"):
        return None
    rotulo = c.req("rotulo_medida")
    return Resultado(rid, "rotular", "tipo_medida", clausula="registro: rótulo de tipo_medida obligatorio", rotulo=rotulo,
                     mensaje=mensaje(ctx, rid), detalle={"tipo_medida": c.tipo_medida,
                                                         "lista_prohibida": ctx.param(rid, "lista_prohibida"),
                                                         "marcadores_pendientes": ["quien", "accion_registro", "sistema"]})


_ALTERNATIVA_REG03 = "{sumamos 3 años | mostramos la provincia}"


@regla("R-REG-03")
def r_reg_03(c, ctx):
    """IC y umbrales mínimos de numerador y denominador. Si la celda no se puede publicar a ese nivel, la regla
    suprime con motivo degradable y pide agrupar 3 años cuando la ventana es válida (R-MOTOR-01 sigue la secuencia)."""
    rid = "R-REG-03"
    P = lambda k: ctx.param(rid, k)  # noqa: E731
    te = c.req("tipo_estimacion")
    out = []

    def pedir_agrupar(motivo):
        anios = ventana_agrupable(c, ctx, P("periodo_agrupado"))
        if anios:
            out.append(Resultado(rid, "agrupar_anios", motivo, clausula="secuencia: agrupar 3 años",
                                 detalle={"periodo": [anios[0], anios[-1]], "anios": anios},
                                 rotulo=f"promedio {anios[0]}–{anios[-1]}",
                                 mensaje=(mensaje(ctx, rid) or "").replace(_ALTERNATIVA_REG03, "sumamos 3 años")))

    if te == "tasa":
        tope_rango = int(re.search(r"numerador < (\d+)", P("tramo_5_10")).group(1))
        num = _req_num(c, "numerador")
        pob = _f(c.poblacion) if c.poblacion is not None else _req_num(c, "denominador")
        det = {"numerador": num, "poblacion": pob}
        if num < P("tasa_min_numerador_publicar") or pob < P("tasa_min_poblacion"):
            out.append(Resultado(rid, "suprimir", "pocos_casos", clausula="tasa: numerador < 5 o población < 1000", detalle=det))
            pedir_agrupar("pocos_casos")
        elif num < tope_rango:  # parametros.tramo_5_10: «5 ≤ numerador < 11»
            out.append(Resultado(rid, "publicar_rango", "pocos_casos", clausula="tasa: 5 <= numerador < 11", detalle=det))
        elif num < P("tasa_numerador_estable"):
            out.append(Resultado(rid, "publicar_referencial", "pocos_casos", clausula="tasa: 11 <= numerador < 20",
                                 detalle={**det, "excluir_ranking": True}))
        return out or None
    if te != "proporcion":
        return None
    num = _req_num(c, "numerador")
    n = _req_num(c, "denominador")
    ic_inf, ic_sup = _f(c.ic_inf), _f(c.ic_sup)
    metodo_ic = c.metodo_ic
    if ic_inf is None or ic_sup is None:  # p. ej. la cobertura del SIEN (dos cotas, sin IC): Wilson sobre num/n
        ic_inf, ic_sup = wilson(num, n)
        metodo_ic = "wilson (validador)"
    ancho = round(ic_sup - ic_inf, 10)
    det = {"numerador": num, "n_denominador": n, "ancho_ic_pp": ancho, "metodo_ic": metodo_ic}
    if num < P("tasa_numerador_estable"):
        det["pocos_casos"] = True  # implementación: motivos incluye pocos_casos si numerador < 20
    msg = (mensaje(ctx, rid) or "").replace(_ALTERNATIVA_REG03, "mostramos un rango")
    msg = rellenar(msg, ic_inf=fmt_num(ic_inf), ic_sup=fmt_num(ic_sup))
    if n < P("prop_min_denominador"):
        out.append(Resultado(rid, "suprimir", "pocos_casos", clausula="proporción: n_denominador < 30", detalle=det))
        pedir_agrupar("pocos_casos")
    elif n < P("prop_denominador_estable"):
        out.append(Resultado(rid, "publicar_referencial", "pocos_casos", clausula="proporción: 30 <= n < 100", detalle=det,
                             mensaje=msg))
    elif num < P("prop_min_celda_extremos"):
        out.append(Resultado(rid, "publicar_referencial", "pocos_casos", clausula="proporción: numerador < 5", detalle=det,
                             mensaje=msg))
    elif n - num < P("prop_min_celda_extremos"):
        out.append(Resultado(rid, "publicar_referencial", "pocos_casos", clausula="proporción: n − numerador < 5",
                             detalle=det, mensaje=msg))
    elif ancho > P("ancho_ic_max_pp"):
        out.append(Resultado(rid, "publicar_referencial", "precision", clausula="proporción: ancho del IC > 20 pp",
                             detalle=det, mensaje=msg))
    return out or None


_SIEN = "INS-CENAN-SIEN"  # «salvo el SIEN» (condición de R-REG-07): la fuente se nombra en el texto, no en un parámetro


def es_cobertura(c) -> bool:
    return c.medida == "cobertura" or c.tipo_medida == "cobertura_programa"


def denominador_propio_lima(c, ctx) -> bool:
    """LM y LR de la cobertura SIEN usan la población del prorrateo IPF (L7); el Callao, la oficial."""
    if "denominador_propio_ipf" in _avisos(c):
        return True
    d = c.denominador_ambitos_lima if isinstance(c.denominador_ambitos_lima, dict) else {}
    return c.nivel in ((d.get("propio") or {}).get("ambitos") or [])


@regla("R-REG-07")
def r_reg_07(c, ctx):
    rid = "R-REG-07"
    P = lambda k: ctx.param(rid, k)  # noqa: E731
    if c.fuente == _SIEN:
        if not es_cobertura(c):
            return None  # la anemia en tamizados: la condición vigente no le extiende la marca (ni las bandas)
        u = P("sien_umbral_tamizaje_pct")
        ci, cs = _req_num(c, "cota_inf"), _req_num(c, "cota_sup")
        det = {"cota_inf": ci, "cota_sup": cs, "umbral_pct": u, "semaforo_usa": "cota_sup"}
        out = [Resultado(rid, "rotular", "cobertura_registro", clausula="SIEN: dos cotas", modificador=True, detalle=det,
                         rotulo=f"entre {round(ci)} y {round(cs)} de cada 100 niños")]
        if cs < u:
            out.append(Resultado(rid, "publicar_referencial", "seleccion", clausula="SIEN: cota_sup < umbral", detalle=det,
                                 aviso="advertencia_seleccion"))
        elif ci < u <= cs:
            out.append(Resultado(rid, "advertir", "cobertura_registro", clausula="SIEN: el intervalo cruza el umbral",
                                 detalle=det, aviso="cruza_mitad",
                                 mensaje=cita(ctx, rid, "Con los datos disponibles")))
        # [L7] ámbitos de Lima: denominador propio rotulado (LM y LR); aviso de margen sobre la mitad. El aviso de
        # margen se aplica a toda cobertura SIEN (lectura más restrictiva; «más de la mitad» solo con cota_inf ≥ umbral).
        lima = (P("sien_ambitos_lima") or {})
        if c.nivel in (lima.get("ambitos") or []) and denominador_propio_lima(c, ctx):
            out.append(Resultado(rid, "rotular", "denominador", clausula="L7: denominador propio (LM y LR)", modificador=True,
                                 rotulo=lima.get("rotulo_denominador_propio"),
                                 mensaje=mensaje(ctx, rid, "SIEN, Lima"), detalle={"ambito": c.nivel}))
        margen = lima.get("margen_umbral_pp")
        if margen is not None and 0 <= ci - u < margen:
            out.append(Resultado(rid, "advertir", "cobertura_registro", clausula="L7: cota_inf a menos de 1 punto sobre el umbral",
                                 modificador=True, detalle=det, aviso="apenas_supera_mitad",
                                 mensaje=mensaje(ctx, rid, "cota inferior a menos de 1 punto")))
        return out
    if c.tipo_medida not in ("registro_eventos", "notificacion_vigilancia"):
        return None
    cob = _f(c.cobertura_registro_estimada)
    det = {"cobertura_registro_estimada": cob}
    sin_tasa, ref = P("umbral_solo_conteo_pct"), P("umbral_referencial_pct")
    alto = int(re.search(r"(\d+)", next(k for k in P("bandas_cobertura") if k.startswith(">="))).group(1))
    msg = mensaje(ctx, rid, cobertura=fmt_num(cob, 0) if cob is not None else None, departamento=c.territorio_nombre,
                  **{"año": c.anio})
    if cob is None or cob < sin_tasa:
        return Resultado(rid, "publicar_solo_conteo", "cobertura_registro", clausula="cobertura NULL o < 60", detalle=det,
                         mensaje=msg)
    if cob < ref:
        return Resultado(rid, "publicar_referencial", "cobertura_registro", clausula="60 <= cobertura < 80", detalle=det,
                         aviso="subregistro", mensaje=msg)
    if cob < alto:
        return Resultado(rid, "publicar_referencial", "cobertura_registro", clausula="80 <= cobertura < 90", detalle=det,
                         rotulo="tasa registrada")
    return Resultado(rid, "rotular", "cobertura_registro", clausula="cobertura >= 90", detalle=det, rotulo="tasa registrada")


@regla("R-REG-08")
def r_reg_08(c, ctx):
    rid = "R-REG-08"
    if not es_cobertura(c):
        return None
    # Con dos cotas (SIEN) se usa la superior: es la que puede pasar de 100 % (lectura más restrictiva).
    if c.cota_sup is not None:
        cob = _req_num(c, "cota_sup")
    elif c.medida == "cobertura" and c.valor is not None:
        cob = _req_num(c, "valor")
    else:
        cob = _req_num(c, "numerador") / _req_num(c, "denominador") * 100
    lim = ctx.param(rid, "limite_referencial_pct")
    det = {"cobertura_pct": cob, "numerador": _f(c.numerador), "denominador": _f(c.denominador),
           "mostrar": ctx.param(rid, "mostrar"), "truncar": ctx.param(rid, "truncar")}
    out = []
    if cob > 100 and c.base_geografica_usada == "establecimiento":  # ajuste de consolidación (R-DENOMINADORES-06)
        out.append(Resultado(rid, "rotular", "denominador", clausula="ajuste: numerador por establecimiento", modificador=True,
                             rotulo=f"atenciones en establecimientos ubicados en {c.territorio_nombre or c.territorio_id}"))
    if cob > lim:
        ya = any(isinstance(p, dict) and "cobertura_mayor_110" in json.dumps(p, ensure_ascii=False, default=str)
                 for p in (c.motivo_nivel or []))
        if ya:
            out += [Resultado(rid, "suprimir", "denominador_en_revision", clausula="sigue > 110 en el nivel superior",
                              detalle=det, mensaje=mensaje(ctx, rid)),
                    Resultado(rid, "revision_humana", "denominador_en_revision", clausula="revisión humana del denominador",
                              detalle=det)]
        else:
            sup = nivel_superior(c, ctx)
            out += [Resultado(rid, "suprimir", "cobertura_mayor_110", clausula="cobertura > 110: suprimir el %",
                              detalle=det, nivel_minimo=sup, mensaje=mensaje(ctx, rid)),
                    Resultado(rid, "agregar_nivel", "cobertura_mayor_110", clausula="cobertura > 110: agregar_nivel",
                              detalle=det, nivel_minimo=sup)]
    elif cob > 100:
        out.append(Resultado(rid, "publicar_referencial", "cobertura_mayor_100", clausula="100 < cobertura <= 110",
                             detalle=det, mensaje=mensaje(ctx, rid)))
    return out or None


@regla("R-REG-09")
def r_reg_09(c, ctx):
    rid = "R-REG-09"
    anio = int(c.req("anio"))
    out = []
    fc = fecha(c.fecha_corte)
    if fc is None:
        fc = fecha(c.fecha_descarga)  # caso borde: sin fecha de corte declarada → fecha de descarga y advertir
        if fc is None:
            raise CampoFaltante("fecha_corte")
        out.append(Resultado(rid, "advertir", "fecha_corte", clausula="caso borde: sin fecha de corte declarada",
                             modificador=True, detalle={"fecha_descarga": str(fc)}, aviso="sin_fecha_corte"))
    cierre = fecha(c.fecha_cierre_fuente) or fecha_de_texto(ctx.param(rid, "cierre_por_defecto"), anio)
    preliminar = anio == ctx.anio_actual or (anio == ctx.anio_actual - 1 and cierre is not None and fc < cierre)
    datos_al = rellenar(ctx.param(rid, "mostrar"), fecha_corte=fc.isoformat()).strip("'")
    det = {"fecha_corte": fc.isoformat(), "cierre": cierre.isoformat() if cierre else None, "es_preliminar": preliminar}
    if preliminar:
        mes = fc.month if fc.year == anio else 12
        out.append(Resultado(rid, "rotular", "dato_preliminar", clausula="año en curso o anterior antes del cierre",
                             rotulo=f"preliminar, {datos_al}", detalle=det,
                             mensaje=mensaje(ctx, rid, fecha_corte=fc.isoformat(),
                                             mes=[k for k, v in _MESES.items() if v == mes][0])))
        comp = c.comparacion
        if comp and not c.mismo_periodo_acumulado and not (isinstance(comp, dict) and comp.get("mismo_periodo_acumulado")):
            out.append(Resultado(rid, "no_comparar", "dato_preliminar", clausula="comparación preliminar vs año completo",
                                 detalle=det))
    else:
        out.append(Resultado(rid, "rotular", "fecha_corte", clausula="fecha de corte", rotulo=datos_al, detalle=det))
    if c.tipo_medida == "notificacion_vigilancia":
        fin = fecha(c.periodo_fin) or _dt.date(anio, 12, 31)
        semanas = ctx.param(rid, "semanas_incompletas_vigilancia")
        if (fc - fin).days < 7 * semanas:
            out.append(Resultado(rid, "marcar_incompletas", "dato_preliminar", modificador=True,
                                 clausula="vigilancia: últimas 4 semanas antes del corte", detalle=det))
    return out


# ======================================================================= estimaciones modeladas

@regla("R-EST-01")
def r_est_01(c, ctx):
    """Estimación modelada: IC o CV, grupo robusto, sin ranking puntual ni nivel más fino que la inferencia.
    Las cláusulas de publicación (incertidumbre, ancho, CV del DCI) compiten en su orden; el bloqueo por nivel, el
    ranking y la antigüedad son independientes (se aplican además)."""
    rid = "R-EST-01"
    P = lambda k: ctx.param(rid, k)  # noqa: E731
    out = []
    inc = c.incertidumbre_publicada
    if inc is None:  # derivado: hay IC o CV publicado por la fuente
        inc = (c.ic_inf is not None and c.ic_sup is not None and c.metodo_ic == "publicado_inei") or c.cv is not None
    ancho = (_f(c.ic_sup) - _f(c.ic_inf)) if (c.ic_inf is not None and c.ic_sup is not None) else None
    if inc is not True:
        out.append(Resultado(rid, "publicar_referencial", "precision", clausula="incertidumbre no publicada",
                             aviso="sin margen de error publicado"))
    elif ancho is not None and ancho > P("ancho_ic_max_pp"):
        out.append(Resultado(rid, "mostrar_solo_el_intervalo", "precision", clausula="ancho IC > 20 pp",
                             detalle={"ancho_ic_pp": round(ancho, 4)}))
    elif c.fuente == "INEI-MAPA-DCI-PROVINCIAL-2019" and c.cv is not None:
        cv = _f(c.cv)
        if cv >= P("dci_cv_suprimir"):
            out.append(Resultado(rid, "suprimir", "precision", clausula="DCI: cv >= 20", detalle={"cv": cv}))
        elif cv >= P("dci_cv_publicar"):
            out.append(Resultado(rid, "publicar_referencial", "precision", clausula="DCI: 15 <= cv < 20", detalle={"cv": cv}))
    # nivel pedido más fino que el de inferencia → bloquear
    np_, ni = c.nivel_pedido, c.nivel_territorial_inferencia
    rp, ri = (ctx.nivel_rank(np_) if np_ else None), (ctx.nivel_rank(ni) if ni else None)
    if rp is not None and ri is not None and rp < ri:
        out.append(Resultado(rid, "bloquear", "nivel_no_representativo", clausula="nivel_pedido más fino que la inferencia",
                             detalle={"nivel_pedido": np_, "nivel_territorial_inferencia": ni}))
    # ranking → solo por grupo robusto o categorías
    if c.intencion_pregunta == "identificar_extremo":
        out.append(Resultado(rid, "rotular", "ranking", clausula="ranking solo por grupo_robusto", modificador=True,
                             detalle={"ordenar_por": "grupo_robusto", "grupo_robusto_nacional": c.grupo_robusto_nacional,
                                      "grupo_robusto_regional": c.grupo_robusto_regional}))
    # antigüedad
    anio_ref = int(c.anio_referencia or c.req("anio"))
    edad = ctx.anio_actual - anio_ref
    if edad > P("antiguedad_max_sin_aviso_anios"):
        aviso_ant = P("aviso_fijo_pobreza_2018") if (c.fuente == "INEI-MAPA-POBREZA" and anio_ref == 2018) else \
            f"Dato de {anio_ref}; la situación actual puede ser distinta."
        out.append(Resultado(rid, "advertir", "vigencia", clausula="anio_actual − anio_referencia > 3", modificador=True,
                             detalle={"edad_dato": edad}, aviso="antiguedad",
                             mensaje=mensaje(ctx, rid, **{"año": anio_ref, "ic_inf": fmt_num(c.ic_inf),
                                                         "ic_sup": fmt_num(c.ic_sup), "aviso_antigüedad": aviso_ant})))
    return out or None


# ======================================================================= gasto

_GASTO_CANONICA = "canonica"  # valor de rol_gasto de la fuente canónica (implementación de R-GASTO-04)


def _pruebas_gasto(ctx) -> dict:
    """Prueba G-08 (conciliación con la Consulta Amigable): pruebas_s3_gasto.json si está en la biblioteca; si no,
    el resumen de pruebas del manifiesto s3_gasto."""
    man = (ctx.manifiestos or {}).get("s3_gasto")
    if not man:
        raise CampoFaltante("manifiesto_s3_gasto")
    if "pruebas" not in man:
        raise CampoFaltante("manifiesto_s3_gasto.pruebas")
    res = {"fallidas": list((man.get("pruebas") or {}).get("fallidas") or []), "detalle": None}
    pruebas = (getattr(ctx, "pruebas", None) or {}).get("s3_gasto")
    if pruebas is None:  # contexto anterior a ctx.pruebas: se lee el archivo de la biblioteca si existe
        raiz = getattr(ctx, "raiz", None)
        f = Path(raiz) / "biblioteca" / "dimensiones" / "pruebas_s3_gasto.json" if raiz is not None else None
        pruebas = json.loads(f.read_text(encoding="utf-8")) if f is not None and f.exists() else []
    res["detalle"] = {p["id"]: p for p in pruebas}.get("G-08")
    return res


@regla("R-GASTO-04")
def r_gasto_04(c, ctx):
    rid = "R-GASTO-04"
    fuentes_gasto = set((ctx.regla(rid).get("aplica_a") or {}).get("fuentes") or [])
    # (1) montos de más de una fuente, o de una fuente que no es la canónica → bloquear
    rol = c.rol_gasto or (ctx.catalogo.get(c.fuente) or {}).get("rol_gasto")
    if rol is None:
        rol = c.req("rol_gasto")
    montos = {i.get("id") for i in (c.insumos or []) if i.get("rol") in ("numerador", "denominador")
              and i.get("id") in fuentes_gasto}
    montos |= set(c.fuentes_montos or [])  # fuentes de los montos que agrega la consulta (las pone el motor; B-2)
    montos.add(c.fuente)
    no_canonicas = {f for f in montos if f != c.fuente and (ctx.catalogo.get(f) or {}).get("rol_gasto", "no_canonica") != _GASTO_CANONICA}
    if rol != _GASTO_CANONICA or len(montos) > 1 or no_canonicas:
        return Resultado(rid, "bloquear", "fuente_no_canonica", clausula="montos de fuente no canónica o de varias fuentes",
                         detalle={"rol_gasto": rol, "fuentes_montos": sorted(montos)})
    # (2) un solo archivo por año: {anio}-Gasto.csv hasta 2024; {anio}-Gasto-Mensual.csv desde 2025
    anio = int(c.req("anio"))
    man = (ctx.manifiestos or {}).get("s3_gasto") or {}
    if not man:
        raise CampoFaltante("manifiesto_s3_gasto")
    cargados = sorted({i.get("archivo_original") for i in man.get("insumos") or []
                       if i.get("source_id") == c.fuente and str(i.get("archivo_original", "")).startswith(f"{anio}-")})
    esperado = f"{anio}-Gasto.csv" if anio <= ctx.param(rid, "anio_ultimo_archivo_anual") else \
        f"{anio}-Gasto{ctx.param(rid, 'sufijo_anio_en_curso')}.csv"
    if cargados != [esperado]:
        return Resultado(rid, "fallo_de_ingesta", "fallo_de_ingesta", clausula="archivos cargados del año distintos del canónico",
                         detalle={"anio": anio, "cargados": cargados, "esperado": esperado})
    # (3) conciliación con la Consulta Amigable (G-08): diferencia ≤ tolerancia o se bloquea la carga
    pr = _pruebas_gasto(ctx)
    tol = ctx.param(rid, "tolerancia_conciliacion")
    det = pr["detalle"] or {}
    dif = _f(((det.get("detalle") or {}) if isinstance(det, dict) else {}).get("max_dif_relativa"))
    falla = "G-08" in pr["fallidas"] or (det and det.get("ok") is False) or (dif is not None and dif > tol)
    if falla:
        return Resultado(rid, "bloquear", "conciliacion_gasto", clausula="conciliación G-08 fuera de tolerancia",
                         detalle={"max_dif_relativa": dif, "tolerancia": tol, "fallidas": pr["fallidas"]})
    return None


def _bloque(c) -> str | None:
    if c.bloque_consolidado:
        return c.bloque_consolidado
    filtro = (c.definicion or {}).get("filtro") if isinstance(c.definicion, dict) else None
    mo = re.search(r"bloque_consolidado\s*=\s*'([a-z_]+)'", filtro or "")
    return mo.group(1) if mo else None


@regla("R-GASTO-05")
def r_gasto_05(c, ctx):
    """Transferencias: cláusulas por cifra (1, 3, 4 y 5). Las cláusulas 2, 6 y 7 son de construcción (vistas) y de la
    guardia del motor (guardia_gasto.verificar_consulta), no de una cifra."""
    rid = "R-GASTO-05"
    sumadas = set(m.lower() for m in (c.medidas_sumadas or []))
    if sumadas & {"monto_autorizado", "monto_acreditado", "autorizado", "acreditado"} and sumadas & {"monto_devengado", "devengado"}:
        return Resultado(rid, "bloquear_cruce", "transferencias", clausula="(1) suma de transferencias (caja) con devengado",
                         detalle={"medidas_sumadas": sorted(sumadas)})
    # (7) «Recursos recibidos»: tres bloques que no se suman entre sí ni con el devengado (auditoría H-16)
    bloques_rec = {"partidas_recibidas", "transferencias_financieras_incorporadas", "caja_acreditada_rd"}
    bloques_par = {str(b).split(" ")[0] for b in ((ctx.param(rid, "recursos_recibidos") or {}).get("bloques") or [])}
    bloques_rec |= bloques_par
    n_rec = len(sumadas & bloques_rec)
    if n_rec >= 2 or (n_rec >= 1 and sumadas & {"monto_devengado", "devengado"}):
        return Resultado(rid, "bloquear_cruce", "transferencias", clausula="(7) suma entre bloques de recursos recibidos",
                         detalle={"medidas_sumadas": sorted(sumadas)})
    bloque = _bloque(c)
    if bloque is None:
        bloque = c.req("bloque_consolidado")
    # textos de mensaje_usuario en su orden: 0-1 cifra temática (con y sin receptor), 2-3 las dos líneas del
    # consolidado, 4 nota fija, 5 fondos (b′), 6 organismos internacionales (c)
    textos = re.findall(r"«([^»]*)»", ctx.regla(rid).get("mensaje_usuario") or "")
    entidad = c.nivel in ("sec_ejec", "pliego", "entidad")
    tematica = c.tema_id is not None and not entidad
    det = {"bloque_consolidado": bloque, "tema_id": c.tema_id}
    if entidad:  # (5) una sola entidad: incluye (a), (b) y (b′), rotuladas
        return Resultado(rid, "rotular", "transferencias", clausula="(5) cifra de una sola entidad", detalle=det,
                         rotulo="incluye transferencias rotuladas (a), (b) y (b′)")
    if bloque == "gasto_final":
        b = _f(c.monto_entregado_fuera)
        if tematica:
            msg = None
            if b is not None:
                plantilla = textos[0] if c.receptor_principal else textos[1]
                msg = rellenar(plantilla, b=fmt_total(b), entidad=c.entidad_nombre or c.territorio_nombre,
                               principal=c.receptor_principal)
            return Resultado(rid, "rotular", "transferencias", clausula="(3) cifra temática: solo gasto final", detalle={
                **det, **({} if b is not None else {"pendiente": "monto (b) no disponible en el cubo"})},
                rotulo="sin transferencias", mensaje=msg)
        return Resultado(rid, "rotular", "transferencias", clausula="(4) consolidado: línea de gasto final", detalle=det,
                         rotulo="Gastado por las entidades del presupuesto",
                         mensaje=" ".join(t for t in (rellenar(textos[2], gasto_final=fmt_total(c.valor) if c.valor is not None else None),
                                                      textos[4]) if t) if len(textos) > 4 else None)
    if tematica:  # (3) una cifra temática con otro bloque → no se publica
        return Resultado(rid, "bloquear", "transferencias", clausula="(3) cifra temática con bloque distinto de gasto_final",
                         detalle=det)
    if bloque == "entregado_fuera_del_presupuesto":
        return Resultado(rid, "rotular", "transferencias", clausula="(4) consolidado: línea aparte (b)", detalle=det,
                         rotulo="Entregado a fondos y entidades públicas fuera del presupuesto (no se suma)",
                         mensaje=rellenar(textos[3], b=fmt_total(c.valor) if c.valor is not None else None) if len(textos) > 3 else None)
    if bloque == "posible_doble_conteo_fondo":
        return Resultado(rid, "nota", "transferencias", clausula="(b′) fondos: solo como nota", detalle=det,
                         mensaje=rellenar(textos[5] if len(textos) > 5 else None, f=fmt_total(c.valor) if c.valor is not None else None))
    if bloque == "excluir_intergubernamental":
        return Resultado(rid, "bloquear", "transferencias", clausula="(a) intergubernamental fuera de toda suma de varias entidades",
                         detalle=det)
    return Resultado(rid, "bloquear", "transferencias", clausula="bloque_consolidado desconocido", detalle=det)


_FASES_NO_MVP = ("CERTIFICADO", "COMPROMETIDO", "GIRADO")  # condición de R-GASTO-06


@regla("R-GASTO-06")
def r_gasto_06(c, ctx):
    rid = "R-GASTO-06"
    fase = (c.fase_gasto or c.medida or ctx.param(rid, "fase_default"))
    fase = str(fase).upper()
    publicables = [f.upper() for f in ctx.param(rid, "fases_publicables_mvp")]
    sumadas = {str(m).upper() for m in (c.medidas_sumadas or [])}
    if len(sumadas & set(publicables + list(_FASES_NO_MVP))) > 1:
        return Resultado(rid, "suprimir", "fase_gasto", clausula="suma entre fases", detalle={"fases": sorted(sumadas)})
    if fase in _FASES_NO_MVP:
        return Resultado(rid, "no_publicar", "fase_gasto", clausula="fase no publicable en el MVP", detalle={"fase_gasto": fase})
    if fase not in publicables:
        return None  # no es una cifra de una fase (p. ej. el avance: R-GASTO-07)
    out = []
    if fase == "DEVENGADO" and _f(c.valor) is not None and _f(c.valor) < 0 and not c.mes:
        out.append(Resultado(rid, "error_de_datos", "fase_gasto", clausula="caso borde: devengado anual negativo",
                             detalle={"valor": _f(c.valor)}))
    rot = {"DEVENGADO": "gastado (devengado)", "PIM": "presupuesto (PIM)", "PIA": "presupuesto inicial (PIA)"}[fase]
    out.append(Resultado(rid, "rotular", "fase_gasto", clausula="fase en el rótulo", rotulo=rot,
                         detalle={"fase_gasto": fase, "columna": ctx.param(rid, "columnas").get(fase)},
                         mensaje=mensaje(ctx, rid), modificador=bool(out)))
    return out


@regla("R-GASTO-07")
def r_gasto_07(c, ctx):
    """Avance de ejecución = devengado / PIM. Solo dispara en una cifra de avance (medida «avance» o devengado y PIM
    juntos en la cifra); las cifras de una sola fase las rotula R-GASTO-06."""
    rid = "R-GASTO-07"
    es_avance = c.medida == "avance" or (c.devengado is not None and c.pim is not None)
    if not es_avance:
        return None
    pim = _req_num(c, "pim")
    det = {"pim": pim}
    if pim <= 0:
        return Resultado(rid, "suprimir", "pim_no_positivo", clausula="caso borde: PIM <= 0", detalle=det)
    if pim < ctx.param(rid, "pim_minimo_soles"):
        return Resultado(rid, "suprimir", "pim_menor_minimo", clausula="PIM < pim_minimo", detalle=det)
    avance = _f(c.valor) if c.medida == "avance" else _req_num(c, "devengado") / pim * 100
    det["avance_pct"] = avance
    if avance > 100 + ctx.param(rid, "tolerancia_sobre_100"):
        return Resultado(rid, "error_de_datos", "avance_mayor_100", clausula="avance > 100,5", detalle=det)
    den = str(c.denominador_avance or "pim").lower()
    if den == "pia" and "ejecuci" in str(c.rotulo_cifra or "").lower():
        return Resultado(rid, "bloquear", "rotulo_prohibido", clausula="«ejecución» con denominador PIA", detalle=det)
    anio = int(c.req("anio"))
    cerrado = c.anio_cerrado
    if cerrado is None:
        fx = fecha(c.fecha_extraccion)
        if fx is None:
            cerrado = c.req("anio_cerrado")
        else:
            cerrado = fx >= fecha_de_texto(ctx.param(rid, "fecha_cierre_param"), anio)
    fc = fecha(c.req("fecha_corte"))
    det.update({"anio_cerrado": bool(cerrado), "fecha_corte": fc.isoformat() if fc else str(c.fecha_corte),
                "denominador": ctx.param(rid, "denominador")["anio_cerrado" if cerrado else "anio_en_curso"]})
    out = []
    if not cerrado:
        out.append(Resultado(rid, "rotular", "dato_preliminar", clausula="año en curso: PIM de la última descarga",
                             rotulo="parcial", detalle={**det, "es_preliminar": True},
                             mensaje=mensaje(ctx, rid, "año en curso", fecha_corte=det["fecha_corte"])))
    else:
        out.append(Resultado(rid, "rotular", "avance", clausula="año cerrado: PIM final", detalle=det,
                             rotulo=f"avance respecto del PIM final, datos al {det['fecha_corte']}"))
    mes = c.mes_corte
    if mes is not None and int(mes) < 12:
        out.append(Resultado(rid, "rotular", "avance", clausula="comparación al mismo mes", modificador=True,
                             rotulo=ctx.param(rid, "rotulo_mismo_mes"), detalle={**det, "mes_corte": int(mes)},
                             mensaje=mensaje(ctx, rid, "mismo mes")))
    return out
