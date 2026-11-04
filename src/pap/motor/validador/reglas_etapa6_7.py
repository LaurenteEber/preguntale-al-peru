"""Reglas de las etapas 6 (divulgación, R-REG-12) y 7 (semáforo de cifra, R-CRUCES-09) del validador del piloto
(P2, grupo B). Fuente de verdad: reglas/reglas.json. Contrato: docs/especificaciones/contrato_validador.md.
"""
from __future__ import annotations

import re

from .nucleo import Resultado, regla
from .reglas_etapa0 import _satisface_minimo
from .reglas_etapa4 import _SIEN, _f, denominador_propio_lima, es_cobertura, mensaje, previos

# ======================================================================= etapa 6: divulgación

# RMM, TMI y TMN: la cláusula (1) las nombra en el texto (no hay parámetro con la lista)
_MORTALIDAD_SENSIBLE = ("rmm", "tmi", "tmn", "mortalidad_materna", "mortalidad_infantil", "mortalidad_neonatal")


def _en_rango_cie10(codigo: str, rangos: str) -> bool:
    """«A50-A64, B20-B24» contiene «B21»; también códigos sueltos («R45.8»)."""
    cod = codigo.upper().replace(".", "")
    for parte in rangos.split(","):
        parte = parte.strip().upper().replace(".", "")
        if "-" in parte:
            a, b = parte.split("-")
            if a[0] == cod[0] and a <= cod[:len(a)] <= b:
                return True
        elif cod.startswith(parte):
            return True
    return False


def sensibilidad(c, ctx) -> str:
    """'sensible' | 'normal' | 'ninguna' según la condición de R-REG-12 (catálogo primero; NULL = normal)."""
    rid = "R-REG-12"
    temas = ctx.param(rid, "temas_sensibles") or {}
    cat = ctx.catalogo.get(c.fuente) or {}
    if c.fuente in (ctx.param(rid, "fuentes_sensibles_por_tema") or []):
        return "sensible"
    if c.codigo_cie10 and any(_en_rango_cie10(str(c.codigo_cie10), r) for r in (temas.get("cie10") or {})):
        return "sensible"
    if c.evento and c.evento in (temas.get("eventos") or []):
        return "sensible"
    if c.tema and c.tema in (temas.get("cie10") or {}).values():
        return "sensible"
    if "sensible" in (cat.get("sensibilidad_divulgacion"), c.sensibilidad_divulgacion):
        return "sensible"
    s_cat = cat.get("sensibilidad_divulgacion")
    if s_cat == "ninguna" or (s_cat is None and c.sensibilidad_divulgacion == "ninguna") or c.cuenta_personas is False:
        return "ninguna"
    return "normal"


@regla("R-REG-12")
def r_reg_12(c, ctx):
    rid = "R-REG-12"
    P = lambda k: ctx.param(rid, k)  # noqa: E731
    mort = any(t in str(c.concepto_medido or c.indicador_id or "").lower() for t in _MORTALIDAD_SENSIBLE)
    sens = "sensible" if mort else sensibilidad(c, ctx)  # RMM, TMI y TMN siempre son sensibles (R-MOTOR-01)
    if sens == "ninguna":
        return None
    umbral = P("umbral_celda_min_sensible") if sens == "sensible" else P("umbral_celda_min_normal")
    num = _f(c.numerador)
    den = _f(c.denominador)
    pob = _f(c.poblacion)
    n_desag = int(c.n_desagregaciones_adicionales or 0)
    rank = ctx.nivel_rank(c.nivel) if c.nivel else None
    r_dist, r_prov = ctx.nivel_rank("distrito"), ctx.nivel_rank("provincia")
    fino = rank is not None and rank <= r_dist  # distrito, centro poblado, establecimiento
    det = {"sensibilidad": sens, "umbral": umbral, "numerador": num, "poblacion": pob, "n_desagregaciones": n_desag}
    msg = lambda alt: mensaje(ctx, rid, umbral=umbral, alternativa=alt)  # noqa: E731
    out = []
    tope_umbral = int(re.search(r"(\d+)", str(P("umbral_sensible_distrito")["celda_min"])).group(1))
    if num is not None and 1 <= num < umbral and mort and sens == "sensible" and c.nivel == "departamento" \
            and not c.periodo_agrupado:
        out.append(Resultado(rid, "suprimir", "divulgacion_nivel", clausula="(1) RMM/TMI/TMN departamento-año con pocos casos",
                             detalle={**det, "ventana": P("cubo_protegido")["mvp"]}, nivel_minimo="departamento",
                             mensaje=msg("la cifra del periodo de 3 años")))
    elif num is not None and 1 <= num < umbral:
        out.append(Resultado(rid, "suprimir", "divulgacion", clausula="(1) 1 <= numerador < umbral",
                             detalle={**det, "complementaria": True, "presentacion": f"menos de {umbral}"},
                             mensaje=msg(f"menos de {umbral}")))
    elif sens == "sensible" and num is not None and den is not None and 1 <= den - num < umbral:
        out.append(Resultado(rid, "suprimir", "divulgacion", clausula="(2) sensible: 1 <= denominador − numerador < umbral",
                             detalle={**det, "complementaria": True}, mensaje=msg(f"menos de {umbral}")))
    elif sens == "sensible" and rank is not None and rank < r_prov and not (
            c.nivel == "distrito" and pob is not None and pob >= P("umbral_sensible_distrito")["poblacion_min"]
            and num is not None and num >= tope_umbral):
        out.append(Resultado(rid, "suprimir", "divulgacion_nivel", clausula="(3) sensible: nivel mínimo provincia",
                             detalle=det, nivel_minimo="provincia", mensaje=msg("la cifra de la provincia")))
    else:
        umb_pob = P("umbral_poblacion_desagregacion")
        # población del territorio: si el motor no la da en un nivel fino, se aplica el tramo más bajo (lectura restrictiva)
        pob_eval = pob if pob is not None else (0 if fino else None)
        total = den if den is not None else _f(c.total)
        if pob_eval is not None and pob_eval < umb_pob["solo_totales"] and (
                n_desag > 0 or (num is not None and (num == 0 or (total is not None and num == total)))):
            out.append(Resultado(rid, "suprimir", "divulgacion", clausula="(4) población < 1000: solo totales, sin celdas 0 ni iguales al total",
                                 detalle={**det, "poblacion_desconocida": pob is None}, mensaje=msg("el total sin desagregar")))
        elif pob_eval is not None and (
                (pob_eval < umb_pob["max_1_desagregacion"] and n_desag > 1) or n_desag > P("max_desagregaciones_distrito")):
            out.append(Resultado(rid, "suprimir", "divulgacion", clausula="(5) demasiadas desagregaciones para la población",
                                 detalle={**det, "poblacion_desconocida": pob is None}, mensaje=msg("el total sin desagregar")))
        elif c.nivel == "centro_poblado" and (n_desag > 0 or num is None or num < tope_umbral):
            out.append(Resultado(rid, "suprimir", "divulgacion", clausula="(6) centro poblado: solo total y >= 10",
                                 detalle=det, mensaje=msg("el total sin desagregar")))
    # (7) celda sensible: solo desde el cubo protegido; numerador redondeado
    if sens == "sensible" and not any(r.accion == "suprimir" for r in out):
        redondeado = None
        if num is not None and num < 100:
            redondeado = int(round(num, -1))
        out.append(Resultado(rid, "rotular", "divulgacion", clausula="(7) celda sensible: cubo protegido", modificador=True,
                             detalle={**det, "cubo_protegido": P("cubo_protegido")["mvp"], "numerador_redondeado": redondeado},
                             rotulo=(f"alrededor de {redondeado}" if redondeado is not None else None)))
    return out or None


# ======================================================================= etapa 7: semáforo de cifra

def _tramos(texto: str, patron: str) -> tuple[float, ...]:
    mo = re.search(patron, texto or "")
    if not mo:
        raise ValueError(f"R-CRUCES-09: no se pudo leer el criterio «{texto}»")
    return tuple(float(x.replace(",", ".")) for x in mo.groups())


def _cota_sup_sien(c, ctx) -> float | None:
    """Cota superior de la cobertura de tamizaje del territorio (R-REG-07) para una cifra del SIEN. En la anemia en
    tamizados se busca la fila de cobertura del departamento o ámbito de Lima que la contiene (L7)."""
    if c.fuente != _SIEN:
        return None
    if es_cobertura(c):
        return _f(c.cota_sup)
    cov = next((i for i, d in ctx.indicadores.items() if d.get("fuente_principal") == _SIEN
                and d.get("tipo_medida") == "cobertura_programa"), None)
    if cov is None or ctx.cubo is None:
        return None
    niv, tid = c.nivel, str(c.territorio_id or "")
    if niv in ("provincia", "distrito") and len(tid) == 6 and tid.isdigit():
        dep = tid[:2]
        if dep == "07":
            niv, tid = "CALLAO", "CALLAO"
        elif dep == "15":
            niv = tid = "LIMA_METROPOLITANA" if tid[:4] == "1501" else "LIMA_REGION"
        else:
            niv, tid = "departamento", dep
    elif niv not in ("departamento", "LIMA_METROPOLITANA", "LIMA_REGION", "CALLAO"):
        return None  # nacional (sin cobertura publicada) o establecimiento (el cubo no trae su ubigeo)
    fila = ctx.fila_cubo(cov, c.anio, niv, tid, medida="cobertura")
    return _f((fila or {}).get("cota_sup"))


_MOTIVO_CIUDADANO = {  # diccionario fijo del motivo principal (implementación de R-CRUCES-09)
    "precision": "hay pocos datos para esta cifra",
    "ancho_ic_modelada": "la estimación tiene un margen de error amplio",
    "vigencia": "dato exacto pero de {anio}",
    "tipo_medida_vs_concepto": "mide algo cercano, no exactamente lo preguntado",
    "base_geografica": "cuenta a quienes se atendieron en el lugar, no a quienes viven ahí",
    "quiebre": "la forma de medir cambió entre los años comparados",
    "subregistro": "el registro no capta todos los casos",
    "dato_preliminar": "son datos preliminares y pueden cambiar",
    "cobertura_registro": "el registro cubre solo a una parte de la población",
    "denominador": "la población de referencia es una estimación",
}


@regla("R-CRUCES-09")
def r_cruces_09(c, ctx):
    rid = "R-CRUCES-09"
    if c.rol == "denominador":
        return None  # caso borde (1): las cifras de padrón usadas como denominador no llevan semáforo propio
    crit = ctx.param(rid, "criterios")
    prev = previos(c)
    puntajes: dict[str, int] = {}

    # precisión: acción vigente (las de cruce no cuentan sobre la cifra, H-1). Auditoría H-2: un agregar_nivel ya
    # cumplido (la cifra está en el nivel_minimo pedido o más grueso, tras degradar) y un agrupar_anios de una cifra
    # que ya es un periodo agrupado no cuentan; la precisión sale de las demás acciones.
    orden = ctx.param("R-MOTOR-02", "orden_restriccion")

    def cuenta(r):
        a = r.get("accion")
        if a not in orden or a == "bloquear_cruce":
            return False
        if a == "agregar_nivel":
            # misma equivalencia que siguiente_paso (L1: LM y LR cumplen «departamento»); sin nivel_minimo, cuenta 3
            minimo = r.get("nivel_minimo")
            return not minimo or not c.nivel or not _satisface_minimo(ctx, c.nivel, minimo)
        if a == "agrupar_anios":
            return not c.periodo_agrupado
        return True

    acc = [r.get("accion") for r in prev if cuenta(r)]
    if not prev and c.accion_previa and c.accion_previa != "bloquear_cruce":
        acc = [c.accion_previa]  # sin resultados previos (casos), la acción vigente que da el núcleo
    vigente = min(acc, key=orden.index) if acc else "publicar"
    rango = any(r.get("accion") == "publicar_referencial" and r.get("modo") == "rango" for r in prev)
    if vigente in ("suprimir", "agregar_nivel", "agrupar_anios"):
        puntajes["precision"] = 3
    elif vigente == "publicar_referencial":
        puntajes["precision"] = 2 if rango else 1
    else:
        puntajes["precision"] = 0

    # ancho del IC de una estimación modelada
    if c.naturaleza_dato == "estimacion_modelada" and c.ic_inf is not None and c.ic_sup is not None:
        a0, a1, a2, a3 = _tramos(crit["ancho_ic_modelada"], r"<=(\d+) pp → 0; (\d+)–(\d+) pp → 1; >(\d+) pp → 2")
        ancho = _f(c.ic_sup) - _f(c.ic_inf)
        puntajes["ancho_ic_modelada"] = 0 if ancho <= a0 else (1 if ancho <= a2 else 2)

    # vigencia: solo para la cifra más reciente de cada indicador
    anio_ref = c.anio_referencia or c.anio
    disponibles = [int(a) for a in (c.anios_disponibles or [])]
    if anio_ref is not None and (not disponibles or int(c.anio) >= max(disponibles)):
        v0, v1, v2, v3 = _tramos(crit["vigencia"], r"<=(\d+) → 0; (\d+)–(\d+) → 1; >(\d+) → 2")
        edad = ctx.anio_actual - int(anio_ref)
        puntajes["vigencia"] = 0 if edad <= v0 else (1 if edad <= v2 else 2)

    # estructurales: tipo de medida frente al concepto y base geográfica
    puntajes["tipo_medida_vs_concepto"] = 0 if int(c.rank_concepto or 1) == 1 else 1
    base = c.base_geografica_usada or c.base_geografica
    if c.atribuible is False:
        puntajes["base_geografica"] = 3
    elif base == "establecimiento":
        puntajes["base_geografica"] = 1
    else:
        puntajes["base_geografica"] = 0

    # quiebre: es de la comparación, no de la cifra (auditoría H-3). Va en semaforo_comparacion y no sube el
    # semáforo de la cifra; la comparación no comparable la bloquea R-ENC-11.
    comp = c.comparacion if isinstance(c.comparacion, dict) else None
    quiebre = None
    if any(r.get("motivo") == "quiebre" and r.get("accion") in ("bloquear_cruce", "suprimir") for r in prev):
        quiebre = 3
    elif comp and comp.get("anio") is not None:
        a, b = sorted((int(c.anio), int(comp["anio"])))
        quiebre = 0
        from .reglas_etapa5 import corta_comparacion
        for q in c.quiebres or []:
            qa = int(q["anio"])
            if (a < qa <= b or qa == a) and corta_comparacion(q.get("tipo"), qa, a, b):
                declarado = set(int(x) for x in (q.get("comparable_con") or []))
                quiebre = max(quiebre, 0 if (a in declarado or b in declarado) else 3)

    if c.subregistro_conocido is True:
        puntajes["subregistro"] = 1
    if c.preliminar is True or c.es_preliminar is True or any((r.get("detalle") or {}).get("es_preliminar") for r in prev):
        puntajes["dato_preliminar"] = 1

    # cobertura del registro
    cs = _cota_sup_sien(c, ctx)
    if cs is not None:
        puntajes["cobertura_registro"] = 2 if cs < ctx.param("R-REG-07", "sien_umbral_tamizaje_pct") else 0
    elif c.fuente != _SIEN and c.naturaleza_dato == "registro_administrativo" and c.tipo_estimacion == "tasa" \
            and c.tipo_medida in ("registro_eventos", "notificacion_vigilancia"):
        (alto,) = _tramos(crit["cobertura_registro"], r"≥(\d+) → 0")
        cob = _f(c.cobertura_registro_estimada)
        ref, conteo = ctx.param("R-REG-07", "umbral_referencial_pct"), ctx.param("R-REG-07", "umbral_solo_conteo_pct")
        puntajes["cobertura_registro"] = 3 if (cob is None or cob < conteo) else (2 if cob < ref else (1 if cob < alto else 0))

    # denominador (solo si la cifra usa uno)
    if c.requiere_denominador is True:
        s_max, = _tramos(crit["denominador"], r"s ≤ (\d+,\d+)")
        dt_max, = _tramos(crit["denominador"], r"anio_censo > (\d+)")
        propio = denominador_propio_lima(c, ctx) or c.metodo_denominador == "propio"
        if not propio:
            puntajes["denominador"] = 0
        else:
            s = _f(c.s_denominador)
            mo = re.search(r"CPV(\d{4})", str(c.vintage_denominador or ""))
            censo = int(mo.group(1)) if mo else None
            viejo = censo is not None and int(c.anio) - censo > dt_max
            puntajes["denominador"] = 1 if (s is None or s > s_max or viejo) else 0

    nivel = max(puntajes.values())
    estructurales = set(ctx.param(rid, "criterios_estructurales") or [])
    unos = sum(1 for k, v in puntajes.items() if v == 1 and k not in estructurales)
    escalado = unos >= ctx.param(rid, "escalamiento_acumulacion") and nivel < 2
    if escalado:
        nivel = 2
    semaforo = ["verde", "ambar", "rojo", "no_publicable"][nivel]
    motivos = sorted(({"criterio": k, "puntaje": v} for k, v in puntajes.items() if v > 0),
                     key=lambda m: (-m["puntaje"], list(puntajes).index(m["criterio"])))
    colores = ["verde", "ambar", "rojo", "no_publicable"]
    comparacion = None
    if quiebre is not None:  # los puntos de una serie heredan el semáforo de la comparación (precisión + quiebre)
        nc = max(nivel, quiebre)
        comparacion = {"semaforo": colores[nc], "puntajes": {"precision_cifra": nivel, "quiebre": quiebre},
                       "motivos": [{"criterio": "quiebre", "puntaje": quiebre}] if quiebre else []}
    rotulo = ctx.param(rid, "rotulos")[semaforo]
    anio_txt = anio_ref if anio_ref is not None else c.anio
    if semaforo == "verde":
        motivo_txt = ctx.param(rid, "motivo_verde").replace("{anio}", str(anio_txt))
    elif semaforo == "no_publicable":
        motivo_txt = None
    else:
        motivo_txt = _MOTIVO_CIUDADANO.get(motivos[0]["criterio"], motivos[0]["criterio"]).replace("{anio}", str(anio_txt))
        if motivos[0]["criterio"] == "vigencia" and c.get("naturaleza_dato") == "estimacion_modelada":  # P4-07
            motivo_txt = f"es una estimación con modelo, de {anio_txt}"
    return Resultado(rid, "rotular", "semaforo", clausula=f"nivel {nivel}" + (" (escalado por acumulación)" if escalado else ""),
                     rotulo=rotulo, mensaje=(mensaje(ctx, rid, rotulo_semaforo=rotulo, motivo_principal_ciudadano=motivo_txt)
                                             if motivo_txt else rotulo),
                     detalle={"semaforo": semaforo, "puntajes": puntajes, "motivos": motivos, "escalado": escalado,
                              "accion_vigente": vigente,
                              **({"semaforo_comparacion": comparacion} if comparacion else {})})
