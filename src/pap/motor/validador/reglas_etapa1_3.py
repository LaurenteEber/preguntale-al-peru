"""Etapas 1 a 3 del validador (P2, grupo A): llave territorial, nivel válido de publicación y denominadores.

Etapa 1: R-TERRITORIO-09, R-TERRITORIO-01, R-TERRITORIO-02, R-TERRITORIO-08, R-TERRITORIO-06.
Etapa 2: R-ENC-06, R-ENC-07, R-ENC-08 (auditoría P2, A-6), R-REG-02, R-GASTO-01, R-GASTO-02, R-GASTO-03, R-TERRITORIO-04, R-EST-05.
Etapa 3: R-DENOMINADORES-01, R-DENOMINADORES-02, R-DENOMINADORES-05, R-DENOMINADORES-07, R-GASTO-12.

Fuente de verdad: reglas/reglas.json. Cada función sigue la `condicion` de su regla cláusula por cláusula y en
su orden; los umbrales y listas se leen con `ctx.param`. Las decisiones de lectura (cuando el texto es ambiguo o falta
un dato en el cubo) están en 00_proyecto/piloto/p2/informe_implementador_A.md.

Sobre `bloquear_cruce` en el ámbito «cifra»: cuando la regla habla de un cociente o de una cifra que «no puede
publicarse» (R-TERRITORIO-01, R-DENOMINADORES-01/02/07 en un cociente) se devuelve `bloquear`, que el núcleo normaliza
a `suprimir` en una cifra; cuando habla de un cruce o de una serie entre años (R-TERRITORIO-06, R-DENOMINADORES-02 en
series, R-GASTO-12) se devuelve `bloquear_cruce`.
"""
from __future__ import annotations

import re
import unicodedata

from .nucleo import CampoFaltante, Cifra, Contexto, Resultado, regla
from .reglas_etapa0 import (AMBITOS, AMLC, CALLAO, ENCUESTA, LM, LR, DOMINIO_DE_NIVEL, contenedor, departamento_de,
                            filas_ubigeo, mensaje, nivel_de, provincia_de, rango, regla_dominio, ubigeo6)

# ======================================================================= ayudas

def normalizar_texto(s: str | None) -> str:
    """Mayúsculas, sin tildes ni signos (salvo la coma, que separa la jerarquía), espacios colapsados."""
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9, ]", " ", s).upper()
    return re.sub(r"\s+", " ", s).strip()


def segmento(texto: str | None, etiqueta: str) -> str | None:
    """Del mensaje_usuario con variantes «(etiqueta) «…»», el texto entre comillas de la variante pedida."""
    if not texto:
        return None
    i = texto.find(etiqueta)
    if i < 0:
        return None
    a = texto.find("«", i + len(etiqueta))
    b = texto.find("»", a + 1)
    if a < 0 or b < 0:
        return None
    # comillas anidadas («…» dentro de «…»): se cierra en el » que equilibra
    prof, j = 0, a
    while j < len(texto):
        if texto[j] == "«":
            prof += 1
        elif texto[j] == "»":
            prof -= 1
            if prof == 0:
                return texto[a + 1:j]
        j += 1
    return texto[a + 1:b]


def rellenar(texto: str | None, **valores) -> str | None:
    if texto is None:
        return None
    return re.sub(r"\{(\w+)\}", lambda x: str(valores[x.group(1)]) if valores.get(x.group(1)) is not None
                  else x.group(0), texto)


def rotulos_lima(ctx: Contexto) -> dict:
    return ((ctx.param("R-ENC-07", "dominios_lima") or {}).get("rotulos")) or {}


def nombre_territorio(ctx: Contexto, nivel: str | None, territorio_id: str | None) -> str | None:
    """Nombre largo: rótulos de Lima (R-ENC-07, L4) o nombre mostrado de dim_ubigeo_historico."""
    rot = rotulos_lima(ctx)
    if nivel in AMBITOS or territorio_id in AMBITOS:
        return rot.get(territorio_id) or rot.get(nivel)
    if str(territorio_id) == "15" and nivel == "departamento":
        return rot.get("departamento_15")
    if nivel == "nacional" or territorio_id == "PE":
        return "Perú"
    u6 = ubigeo6(territorio_id)
    if u6:
        f = filas_ubigeo(ctx, u6)
        if f is not None and not f.empty:
            return str(f.iloc[-1].nombre_mostrado)
    return territorio_id


def avisos(c: Cifra) -> list:
    a = c.avisos
    return list(a) if isinstance(a, (list, tuple)) else []


def _lista(v) -> list:
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    try:
        return list(v)
    except TypeError:
        return [v]


# ======================================================================= etapa 1: territorio

_INDICE: dict = {}


def _indice_nombres(ub) -> dict:
    """nombre normalizado → filas vigentes de dim_ubigeo_historico (nombre, nombre_normalizado y nombres_alternos)."""
    clave = id(ub)
    if clave not in _INDICE:
        vig = ub[ub.vigente_hasta.isna()] if "vigente_hasta" in ub else ub
        idx: dict = {}
        for r in vig.itertuples(index=False):
            nombres = {normalizar_texto(r.nombre), normalizar_texto(getattr(r, "nombre_normalizado", None))}
            nombres |= {normalizar_texto(x) for x in _lista(getattr(r, "nombres_alternos", None))}
            for n in nombres - {""}:
                idx.setdefault(n, {})[r.ubigeo_inei] = r._asdict()
        _INDICE.clear()
        _INDICE[clave] = idx
    return _INDICE[clave]


def _candidatos(ctx: Contexto, nombre: str, padres: list[str]) -> list[dict]:
    """Coincidencia exacta normalizada sobre nombre y nombres_alternos de dim_ubigeo_historico (filas vigentes),
    filtrando por la jerarquía cuando el texto la da («Ayaviri, Melgar»)."""
    ub = ctx.ubigeos
    if ub is None:
        raise CampoFaltante("dim_ubigeo_historico")
    res = list(_indice_nombres(ub).get(nombre, {}).values())
    for p in padres:
        res = [r for r in res if p in _ancestros(ctx, r["ubigeo_inei"])]
    return res


def _ancestros(ctx: Contexto, u: str) -> set[str]:
    nombres = set()
    for pref in (u[:4] + "00", u[:2] + "0000"):
        if pref == u:
            continue
        f = filas_ubigeo(ctx, pref)
        for r in f.itertuples(index=False):
            nombres.add(normalizar_texto(r.nombre))
            nombres |= {normalizar_texto(x) for x in _lista(getattr(r, "nombres_alternos", None))}
    return nombres


NIVEL_PISTA = {"DEPARTAMENTO DE ": "departamento", "REGION ": "departamento", "PROVINCIA DE ": "provincia",
               "DISTRITO DE ": "distrito"}


@regla("R-TERRITORIO-09")
def r_territorio_09(c: Cifra, ctx: Contexto):
    """Texto del usuario → ubigeo único; cero o varias coincidencias (o sin territorio) → preguntar; ubigeo
    pendiente → R-LENGUAJE-05 (distrito nuevo). «Lima» sola → preguntar (L4); «Callao» → 07 sin preguntar."""
    rid = "R-TERRITORIO-09"
    if c.rol == "contexto":
        return None  # el territorio de una cifra de contexto lo elige el motor, no el texto del usuario
    nv = c.nivel_pedido  # auditoría P2, A-1 (H-8): solo el nivel pedido o la pista del texto, nunca el de la fila
    texto = c.territorio_pedido
    msg = ctx.regla(rid).get("mensaje_usuario") or ""
    msg_base = msg.split(" (Lima)")[0]
    if not texto:
        if nv == "nacional" or c.territorio_id == "PE" or c.intencion_pregunta == "identificar_extremo":
            return None  # la pregunta es del país (o un ranking de todo el país): no hay territorio que resolver
        return Resultado(rid, "preguntar", "territorio_no_identificado", clausula="la pregunta no nombra territorio",
                         mensaje=rellenar(msg_base, territorio="territorio", opciones="—"))
    partes = [p.strip() for p in normalizar_texto(texto).split(",") if p.strip()]
    nombre, padres = partes[0], partes[1:]
    # ámbitos de Lima por su nombre largo (rótulos L4), y el país y las áreas, que no son ubigeos
    rot = ctx.param(rid, "rotulos_lima") or {}
    alias_amb = {normalizar_texto(v.split(" (")[0]): k for k, v in rot.items()}
    alias_amb.update({normalizar_texto(v): k for k, v in rot.items()})
    alias_amb.update({"LIMA PROVINCIAS": LR, "LIMA REGION": LR})
    no_ubigeo = {"PERU", "NACIONAL", "URBANO", "RURAL", "AREA URBANA", "AREA RURAL"}
    ambiguos = {normalizar_texto(k): k for k in (ctx.param(rid, "ambiguos_conocidos") or {})}
    if (nombre in alias_amb and nombre not in ambiguos) or nombre in no_ubigeo:
        return None  # ámbito, país o área nombrados sin ambigüedad
    pista = None
    for pref, nivel_p in NIVEL_PISTA.items():
        if nombre.startswith(pref):
            nombre, pista = nombre[len(pref):].strip(), nivel_p
    filtro_nivel = pista or (nv if nv in ("departamento", "provincia", "distrito") else None)
    if nombre in ambiguos:
        clave = ambiguos[nombre]
        if clave == "Callao":
            # parametros.sin_respuesta.Callao: no se pregunta (departamento 07); el distrito solo si se pide
            return None
        if clave == "Lima" and not (filtro_nivel or nv in AMBITOS):
            opciones = ctx.param(rid, "ambiguos_conocidos")[clave]
            return Resultado(rid, "preguntar", "territorio_ambiguo", clausula="«Lima» sola: preguntar (L4)",
                             mensaje=segmento(msg, "(Lima)") or rellenar(msg_base, territorio=texto,
                                                                         opciones="; ".join(opciones)),
                             detalle={"texto": texto, "opciones": opciones,
                                      "sin_respuesta": (ctx.param(rid, "sin_respuesta") or {}).get(clave)})
        if clave == "Lima":
            return None  # el nivel pedido resuelve «Lima» (departamento 15, provincia 1501, distrito 150101 o ámbito)
    cand = _candidatos(ctx, nombre, padres)
    if filtro_nivel:
        cand = [r for r in cand if r["nivel"] == filtro_nivel]
    if len(cand) != 1:
        motivo = "territorio_no_identificado" if not cand else "territorio_ambiguo"
        opciones = [f"{r['nombre_mostrado']} ({r['nivel']}, {r['ubigeo_inei']})" for r in cand]
        return Resultado(rid, "preguntar", motivo, clausula="coincidencias ≠ 1 → preguntar",
                         mensaje=rellenar(msg_base, territorio=texto, opciones=", ".join(opciones) or "—"),
                         detalle={"texto": texto, "n_coincidencias": len(cand), "opciones": opciones})
    r = cand[0]
    if r.get("estado_ubigeo") == "pendiente":
        return Resultado(rid, "suprimir", "sin_datos", clausula="estado_ubigeo pendiente → R-LENGUAJE-05",
                         detalle={"ubigeo": r["ubigeo_inei"], "respuesta": "R-LENGUAJE-05 (distrito nuevo)"})
    return None


@regla("R-TERRITORIO-01")
def r_territorio_01(c: Cifra, ctx: Contexto):
    """El territorio de la cifra resuelve contra dim_ubigeo_historico en su año: datos anuales por
    anio_datos_desde/anio_datos_hasta (TE-02); eventos con fecha por vigente_desde/vigente_hasta."""
    rid = "R-TERRITORIO-01"
    nivel = c.req("nivel")
    t = str(c.req("territorio_id"))
    reparado = None
    if re.fullmatch(r"\d{5}", t):  # casos_borde: cero inicial perdido → zfill(6), se registra
        reparado, t = t, t.zfill(6)
    u6 = ubigeo6(t)
    if u6 is None:
        if nivel in ("departamento", "provincia", "distrito"):
            return Resultado(rid, "bloquear", "ubigeo_no_resuelto", clausula="código no es ubigeo INEI",
                             detalle={"territorio_id": t})
        return None  # nacional, área, ámbitos de Lima o establecimiento: no son llaves de ubigeo
    f = filas_ubigeo(ctx, u6)
    if f is None:
        raise CampoFaltante("dim_ubigeo_historico")
    anio = int(c.req("anio"))
    if c.fecha_evento:  # eventos: fecha exacta
        fe = str(c.fecha_evento)
        ok = f[((f.vigente_desde.astype(str) <= fe) & (f.vigente_hasta.isna() | (f.vigente_hasta.astype(str) >= fe)))
               .fillna(False).astype(bool)]
    else:
        desde = (f.anio_datos_desde.astype("Float64") <= anio).fillna(False)
        hasta = f.anio_datos_hasta.isna() | (f.anio_datos_hasta.astype("Float64") >= anio).fillna(False)
        ok = f[(desde & hasta).astype(bool)]
    if ok.empty:
        return Resultado(rid, "bloquear", "ubigeo_no_resuelto", clausula="ubigeo sin versión vigente en el año",
                         detalle={"ubigeo": u6, "anio": anio, "versiones": len(f), "reparado_de": reparado})
    return None


@regla("R-TERRITORIO-02")
def r_territorio_02(c: Cifra, ctx: Contexto):
    """Sistema de ubigeo (INEI o RENIEC) detectado en la carga: aceptar si el ganador llega a 0,99 de coincidencia
    código+nombre con margen ≥ 0,20 (100 % si hay < 50 códigos); sin nombre, ≥ 95 % de códigos exclusivos de un
    sistema y 0 % del otro; si no, revisión humana. Lo declarado en el catálogo no basta."""
    rid = "R-TERRITORIO-02"
    p = lambda k: ctx.param(rid, k)  # noqa: E731
    carga = (getattr(ctx, "cargas", None) or {}).get(c.fuente_principal) or {}
    g = lambda k: c.get(k, carga.get(k))  # noqa: E731
    m_inei, m_reniec, n = g("m_inei"), g("m_reniec"), g("n_codigos")
    ex_inei, ex_reniec = g("pct_exclusivos_inei"), g("pct_exclusivos_reniec")
    det = {"m_inei": m_inei, "m_reniec": m_reniec, "n_codigos": n, "sistema_declarado": c.sistema_ubigeo}
    if m_inei is not None and m_reniec is not None:
        umbral = 1.0 if (n is not None and n < 50) else p("umbral_coincidencia_codigo_nombre")
        # redondeo a 9 decimales: 0,99 − 0,79 es 0,19999… en coma flotante y el borde 0,20 debe aceptarse
        if max(m_inei, m_reniec) >= umbral and round(abs(m_inei - m_reniec), 9) >= p("margen_minimo_entre_sistemas"):
            return None
        if m_inei > 0 and m_reniec > 0 and m_inei + m_reniec >= p("umbral_coincidencia_codigo_nombre"):
            return Resultado(rid, "revision_humana", "carga_mixta", clausula="carga mixta INEI/RENIEC", detalle=det)
        # enunciado: «la carga se rechaza» → la cifra que sale de ella no se publica (lectura restrictiva)
        return [Resultado(rid, "suprimir", "carga_rechazada", clausula="sistema ganador < umbral: carga rechazada",
                          detalle=det),
                Resultado(rid, "revision_humana", "sistema_ubigeo_no_concluyente", detalle=det)]
    if ex_inei is not None and ex_reniec is not None:
        u = p("umbral_sin_nombre_codigos_exclusivos")
        if (ex_inei >= u and ex_reniec == 0) or (ex_reniec >= u and ex_inei == 0):
            return None
        return Resultado(rid, "revision_humana", "sistema_ubigeo_no_concluyente",
                         clausula="sin nombre: códigos exclusivos no concluyentes", detalle=det)
    # pruebas de la construcción de la carga (ctx.pruebas, auditoría P2 N-6/H-11)
    ev = _evidencia_carga(c, ctx)
    if ev is not None:
        det.update(ev)
        if ev["ok"] and ev["coincidencia"] >= p("umbral_coincidencia_codigo_nombre"):
            return None
        return Resultado(rid, "revision_humana", "sistema_ubigeo_no_concluyente",
                         clausula="pruebas de la carga: coincidencia < 0,99", detalle=det)
    # implementación, paso 4: «si no, revisión humana». La detección no está registrada en el contexto.
    return Resultado(rid, "revision_humana", "sistema_ubigeo_sin_verificar",
                     clausula="detección del sistema no registrada en la carga", detalle=det)


# Pruebas de construcción que miden el sistema de ubigeo de una carga (auditoría P2, N-6/H-11): sprint, prueba de
# coincidencia del código con una fuente en sistema INEI (por identidad, más fuerte que el nombre) y prueba de existencia.
PRUEBAS_SISTEMA_UBIGEO = {"INS-CENAN-SIEN": ("s3_puentes", "E-04", "E-05")}


def _evidencia_carga(c: Cifra, ctx: Contexto) -> dict | None:
    """SIEN: E-04 = % de establecimientos cuyo ubigeo coincide con el de RENIPRESS (sistema INEI) y E-05 = 100 % de
    ubigeos existentes en dim_ubigeo_historico. Se toma E-04 como m_inei (código + identidad del establecimiento)."""
    spec = PRUEBAS_SISTEMA_UBIGEO.get(c.fuente_principal)
    pruebas = (getattr(ctx, "pruebas", None) or {}).get(spec[0]) if spec else None
    if not pruebas:
        return None
    por_id = {t.get("id"): t for t in pruebas}
    coinc, existe = por_id.get(spec[1]), por_id.get(spec[2])
    if not coinc or not existe or (coinc.get("detalle") or {}).get("pct") is None:
        return None
    return {"coincidencia": float(coinc["detalle"]["pct"]), "ok": bool(existe.get("ok")),
            "pruebas": f"{spec[0]}: {spec[1]}, {spec[2]}"}


def _p_ubicado(c: Cifra, ctx: Contexto) -> tuple[float | None, str]:
    """% del numerador ubicado en un distrito vigente (tabla de cargas). Si la cifra no lo trae: SIEN por ubigeo del
    establecimiento → 1,0 cuando la prueba E-05 de la capa (100 % de ubigeos del establecimiento existentes en
    dim_ubigeo_historico) no figura entre las fallidas de su manifiesto."""
    if c.pct_numerador_ubicado is not None:
        return float(c.pct_numerador_ubicado), "campo pct_numerador_ubicado"
    if c.fuente_principal == "INS-CENAN-SIEN" and c.metodo_territorio == "ubigeo_eess":
        man = (ctx.manifiestos or {}).get("s3_puentes") or {}
        if man and "fact_sien_hb_ubigeo" in (man.get("tablas") or {}) \
                and "E-05" not in ((man.get("pruebas") or {}).get("fallidas") or []):
            return 1.0, "manifiesto s3_puentes, prueba E-05 (ubigeo del establecimiento 100 %)"
    return None, ""


@regla("R-TERRITORIO-08")
def r_territorio_08(c: Cifra, ctx: Contexto):
    """Calidad territorial: p ≥ 0,99 → publicar; 0,95 ≤ p < 0,99 → advertir (residuo «sin ubicar»); p < 0,95 →
    agregar a departamento (si se resuelve en ≥ 0,99) o a nacional. Excepción SIEN cobertura de tamizaje: solo por
    departamento, LM, LR y Callao, con dos cotas, aunque p ≥ 0,95 (7/10 y L7)."""
    rid = "R-TERRITORIO-08"
    nivel = c.req("nivel")
    u_pub, u_adv = ctx.param(rid, "umbral_publicar"), ctx.param(rid, "umbral_advertir")
    # Excepción SIEN, cobertura de tamizaje (primera cláusula que se cumple para esa cifra)
    if c.fuente_principal == "INS-CENAN-SIEN" and c.tipo_medida == "cobertura_programa":
        validos = ("departamento", LM, LR, CALLAO)
        if nivel in validos:
            return None
        det = {"niveles_validos": list(validos), "parametro": ctx.param(rid, "sien_cobertura_tamizaje")}
        if (rango(ctx, nivel) or 0) < (rango(ctx, "departamento") or 0):
            return Resultado(rid, "agregar_nivel", "nivel_no_representativo",
                             clausula="SIEN cobertura: solo departamento, LM, LR y Callao",
                             nivel_minimo="departamento", detalle=det)
        return Resultado(rid, "suprimir", "nivel_no_valido", clausula="SIEN cobertura: nivel no publicable",
                         detalle=det)
    # cascada sobre el ubigeo (la proporción de anemia del SIEN, sobre ubigeo_eess: D4)
    rd = rango(ctx, "departamento") or 0
    if nivel == "departamento":
        pd_ = c.pct_numerador_ubicado_departamento
        if pd_ is not None and float(pd_) < u_pub:
            return Resultado(rid, "agregar_nivel", "nivel_no_representativo",
                             clausula="departamento resuelto < 0,99 → nacional", nivel_minimo="nacional",
                             detalle={"p_departamento": pd_})
        return None
    if (rango(ctx, nivel) or 0) >= rd or nivel in AMBITOS:
        return None  # la cascada decide la publicación por debajo del departamento
    p, origen = _p_ubicado(c, ctx)
    if p is None:
        p = c.req("pct_numerador_ubicado")
    det = {"p": p, "origen_p": origen}
    if p >= u_pub:
        return None
    pct = round(100 * (1 - p), 1)
    if p >= u_adv:
        return Resultado(rid, "advertir", "residuo_sin_ubicar", clausula="0,95 ≤ p < 0,99 → advertir",
                         mensaje=mensaje(ctx, rid, pct_sin_ubicar=pct), detalle=det)
    pdep = c.pct_numerador_ubicado_departamento
    destino = "departamento" if pdep is None or float(pdep) >= u_pub else "nacional"
    return Resultado(rid, "agregar_nivel", "nivel_no_representativo", clausula=f"p < 0,95 → {destino}",
                     nivel_minimo=destino, mensaje=mensaje(ctx, rid, pct_sin_ubicar=pct),
                     detalle={**det, "p_departamento": pdep})


def provincias_de_composicion(ctx: Contexto, comp: list) -> list[str]:
    """Composición de dim_dominio (['15', '-1501'], ['1501'], ['0701']) → nombres de las provincias que incluye."""
    ub = ctx.ubigeos
    incl, excl = [], set()
    for x in comp:
        x = str(x).strip()
        (excl.add(x[1:]) if x.startswith("-") else incl.append(x)) if x else None
    out = []
    for x in incl:
        if len(x) == 2 and ub is not None:
            provs = ub[(ub.nivel == "provincia") & ub.ubigeo_inei.str.startswith(x) & ub.vigente_hasta.isna()]
            codigos = sorted(provs.ubigeo_inei.unique())
        else:
            codigos = [x.ljust(6, "0")]
        for u in codigos:
            if u[:4] in excl:
                continue
            out.append(nombre_territorio(ctx, "provincia", u) or u)
    return out


@regla("R-TERRITORIO-06")
def r_territorio_06(c: Cifra, ctx: Contexto):
    """En un cruce de encuesta con datos administrativos en el 15, el 07 o con inferencia por dominio, se exige
    dim_dominio (encuesta, año, dominio) con lista explícita de ubigeos; si no existe → bloquear el cruce."""
    rid = "R-TERRITORIO-06"
    if c.intencion_pregunta != "cruce":
        return None
    nivel, t = c.req("nivel"), c.territorio_id
    deps = ctx.param(rid, "departamentos_con_dominio_especial") or []
    dpto = departamento_de(t, nivel)
    especial = nivel == AMLC or dpto in deps
    if not (especial or c.nivel_territorial_inferencia == "dominio"):
        return None
    enc = ENCUESTA.get(c.fuente_principal)
    r = regla_dominio(ctx, enc, c.req("anio"), nivel, t)
    comp = (r or {}).get("composicion")
    explicita = isinstance(comp, list) and any(str(x).strip() for x in comp)
    if nivel == "departamento" and r is not None and str(t) in ((r.get("por_departamento") or {})):
        explicita = True  # dim_dominio.por_departamento declara la composición del departamento
    rot = rotulos_lima(ctx)
    amb = rot.get(nivel) or rot.get("departamento_15" if str(t) == "15" else "") or nombre_territorio(ctx, nivel, t)
    if not explicita:
        return Resultado(rid, "bloquear_cruce", "dominio_no_definido",
                         clausula="cruce en 15/07 o por dominio sin dim_dominio explícito",
                         detalle={"encuesta": enc, "anio": c.anio, "nivel": nivel, "dominio": (r or {}).get("dominio_id")})
    if especial:
        return Resultado(rid, "rotular", "dominio_lima", clausula="cruce por dominio de dim_dominio",
                         mensaje=mensaje(ctx, rid, ambito_largo=amb,
                                         lista_provincias=", ".join(provincias_de_composicion(ctx, comp)))
                         if isinstance(comp, list) else None, rotulo=amb,
                         detalle={"dominio": r.get("dominio_id"), "composicion": comp})
    return None


# ======================================================================= etapa 2: nivel

def _nombre_dominio(nivel: str, territorio_id: str | None) -> str | None:
    if nivel == "dominio_subnacional":
        return str(territorio_id) if territorio_id else None
    return DOMINIO_DE_NIVEL.get(nivel, nivel)


@regla("R-ENC-06")
def r_enc_06(c: Cifra, ctx: Contexto):
    """Encuesta: no se publica a un nivel más fino que su nivel_territorial_inferencia ni fuera de sus
    dominios_inferencia; se responde con el departamento (o dominio) que contiene al territorio. Excepción L1/L2: los
    ámbitos de Lima de dim_dominio no se degradan por rango (decide R-ENC-08); en el 15 se sube a LM o LR."""
    rid = "R-ENC-06"
    nv = nivel_de(c)
    inferencia = c.req("nivel_territorial_inferencia")
    anio = c.req("anio")
    enc = ENCUESTA.get(c.fuente_principal)
    t = c.territorio_id
    if nv in AMBITOS and regla_dominio(ctx, enc, anio, nv, nv) is not None:
        return None  # excepción L1 y L2: lo decide R-ENC-08
    per = c.periodicidad_estimacion or "anual"
    dom = c.req("dominios_inferencia")
    lista = list((dom or {}).get(per) or []) if isinstance(dom, dict) else list(dom or [])
    if per == "anual" and isinstance(dom, dict):
        lista += list(dom.get("ambitos_publicados") or [])
    r_nv, r_inf = rango(ctx, nv), rango(ctx, inferencia)
    fino = r_nv is not None and r_inf is not None and r_nv < r_inf
    nombre = _nombre_dominio(nv, t if nv == c.nivel else None)
    fuera = nombre not in lista and nv not in ("provincia", "distrito", "establecimiento")
    if not (fino or fuera):
        return None
    if fino:
        dest = contenedor(c, inferencia, ctx, territorio_id=t, nivel_actual=c.nivel if c.nivel != nv else nv)
    else:
        dest = ("nacional", "PE")  # fuera de los dominios (p. ej. dominio 8 en un año sin él): solo el nacional lo contiene
    nivel_min = dest[0] if dest else inferencia
    ped = c.territorio_pedido or c.territorio_nombre or nombre_territorio(ctx, c.nivel, t)
    largo = nombre_territorio(ctx, dest[0], dest[1]) if dest else None
    return Resultado(rid, "agregar_nivel", "nivel_no_representativo",
                     clausula="nivel pedido más fino que la inferencia" if fino else "nivel fuera de dominios_inferencia",
                     nivel_minimo=nivel_min, mensaje=mensaje(ctx, rid, territorio_pedido=ped,
                                                             territorio_contenedor_largo=largo),
                     detalle={"nivel_pedido": nv, "nivel_territorial_inferencia": inferencia, "contenedor": dest,
                              "periodicidad": per})


@regla("R-ENC-07")
def r_enc_07(c: Cifra, ctx: Contexto):
    """Cifra de encuesta del 15 o del 07 (o de sus ámbitos) o de un indicador solo urbano o de ciudades → rótulo del
    dominio con su nombre largo (L4)."""
    rid = "R-ENC-07"
    nivel, t = c.req("nivel"), c.territorio_id
    dpto = departamento_de(t, nivel)
    lima = nivel == AMLC or dpto in ("15", "07")
    po = c.poblacion_objetivo
    area = po.get("area") if isinstance(po, dict) else po
    urbano = area in ("urbano", "ciudades")
    if not (lima or urbano):
        return None
    texto = ctx.regla(rid).get("mensaje_usuario")
    rot = rotulos_lima(ctx)
    partes, rotulo = [], None
    if lima:
        clave = nivel if nivel in AMBITOS else ("departamento_15" if dpto == "15" else CALLAO)
        rotulo = rot.get(clave)
        if clave in (LM, LR, AMLC):  # la advertencia «no a todo el departamento de Lima» solo vale para estos ámbitos
            partes.append(rellenar(segmento(texto, "(Lima)"), ambito_largo=rotulo))
    if urbano:
        partes.append(rellenar(segmento(texto, "(urbano)"), territorio=c.territorio_nombre or t))
    return Resultado(rid, "rotular", "dominio_lima" if lima else "solo_urbano",
                     clausula="departamento 15/07" if lima else "población objetivo urbana",
                     rotulo=rotulo, mensaje=" ".join(p for p in partes if p) or None,
                     detalle={"nivel": nivel, "territorio_id": t, "area": area})


def _fila_inferencia(ctx: Contexto, fuente: str | None, anio, modulo: str | None) -> dict | None:
    """Fila de inferencia_verificada.csv por (fuente, anio, modulo) o (fuente, anio, '*')."""
    filas = [f for f in ctx.inferencia or [] if f.get("fuente") == fuente and str(f.get("anio")) == str(anio)]
    for m in ([modulo] if modulo and modulo != "*" else []) + ["*"]:
        for f in filas:
            if f.get("modulo") == m:
                return f
    return None


def _verdadero(v) -> bool:
    return str(v).strip().lower() in ("true", "1", "si", "sí")


def _cita(f: dict, pref: str = "") -> bool:
    return all(str(f.get(pref + k) or "").strip() for k in ("cita_url", "cita_documento", "cita_ubicacion"))


@regla("R-ENC-08")
def r_enc_08(c: Cifra, ctx: Contexto):
    """Encuesta muestral: se publica por debajo del nacional solo con el nivel de inferencia verificado en la ficha
    técnica (inferencia_verificada.csv por fuente, año y módulo). Ámbito publicado (L1, L2) → aviso ambito_no_dominio
    (y ambito_por_estrato cuando el ámbito se asigna por estrato). Sin verificación → agregar_nivel al nivel verificado
    más fino que contiene al territorio, o a nacional. fila.aviso → aviso de parametros.avisos."""
    rid = "R-ENC-08"
    if c.tipo_aplicacion == "censal":
        return None  # la ENLA censal va por R-ENC-16
    avisos_p = ctx.param(rid, "avisos") or {}
    texto = ctx.regla(rid).get("mensaje_usuario")
    anio = int(c.req("anio"))
    enc = ENCUESTA.get(c.fuente_principal)
    # nivel al que se publicaría la cifra después de R-ENC-06 y R-ENC-07
    n, t = c.req("nivel"), str(c.territorio_id or "")
    inferencia = c.nivel_territorial_inferencia
    if inferencia and n not in AMBITOS and (rango(ctx, n) or 0) < (rango(ctx, inferencia) or 0):  # ámbitos: L1
        dest = contenedor(c, inferencia, ctx)
        if dest:
            n, t = dest
    if t in ("07",) or (n == "departamento" and t == "07"):
        n, t = CALLAO, CALLAO  # 07 ≡ CALLAO: va por la rama del ámbito publicado
    if n == "provincia" and t == "150100":
        n, t = LM, LM  # 1501 ≡ LIMA_METROPOLITANA
    fila = _fila_inferencia(ctx, c.fuente_principal, anio, c.modulo_encuesta)
    salida = []
    if fila and str(fila.get("aviso") or "").strip():  # fila.aviso → texto de parametros.avisos, junto a la cifra
        cod = fila["aviso"].strip()
        salida.append(Resultado(rid, "advertir", cod, clausula="aviso de la fila de inferencia_verificada",
                                aviso=cod, mensaje=rellenar(avisos_p.get(cod), anio=anio), modificador=True,
                                detalle={"fila": f"{fila.get('fuente')} {fila.get('anio')} {fila.get('modulo')}"}))
    if n == "nacional":
        return salida or None
    base_ok = bool(fila) and _verdadero(fila.get("inferencia_verificada")) and _cita(fila)
    amb_pub = {x.strip() for x in str((fila or {}).get("ambitos_publicados") or "").split(";") if x.strip()}
    excl = {x.strip() for x in str((fila or {}).get("excluye_departamentos") or "").split(";") if x.strip()}
    nivel_max = (fila or {}).get("nivel_maximo")
    rot = rotulos_lima(ctx)

    def es_ambito_publicado(nv: str) -> bool:
        r = regla_dominio(ctx, enc, anio, nv, nv) if nv in AMBITOS else None
        return r is not None and r.get("tipo") == "ambito_publicado"

    def verificado(nv: str, terr: str) -> bool:
        if nv == "nacional":
            return True
        if es_ambito_publicado(nv):  # rama del ámbito publicado: antes que excluye_departamentos y sin nivel_maximo
            return base_ok and nv in amb_pub and _cita(fila, "ambitos_")
        if not base_ok or (rango(ctx, nv) or 0) < (rango(ctx, nivel_max) or 99):
            return False
        d = departamento_de(terr, nv)
        if d in excl and nv != AMLC:
            return False
        if nv in ("dominio_subnacional", AMLC, CALLAO):  # dominio: tiene que estar en dim_dominio (R-ENC-07)
            return regla_dominio(ctx, enc, anio, nv, terr) is not None
        return True

    if verificado(n, t):
        if es_ambito_publicado(n) or (n == "departamento" and t == "15" and
                                      "15" in ((regla_dominio(ctx, enc, anio, n, t) or {}).get("por_departamento") or {})):
            amb = rot.get(n) if n in AMBITOS else rot.get("departamento_15")
            salida.insert(0, Resultado(rid, "advertir", "ambito_no_dominio", clausula="ámbito publicado (L1)",
                                       aviso="ambito_no_dominio",
                                       mensaje=rellenar(avisos_p.get("ambito_no_dominio"), ambito=amb),
                                       detalle={"ambito": n, "cita": (fila or {}).get("ambitos_cita_documento")}))
            if es_ambito_publicado(n) and str(fila.get("ambitos_metodo") or "").startswith("estrato"):
                salida.append(Resultado(rid, "advertir", "ambito_por_estrato", clausula="ámbito asignado por estrato (L2)",
                                        aviso="ambito_por_estrato",
                                        mensaje=rellenar(avisos_p.get("ambito_por_estrato"), anio=anio),
                                        detalle={"ambitos_metodo": fila.get("ambitos_metodo")}))
        return salida or None
    # no verificado: nivel verificado más fino que contiene al territorio; si no hay, nacional
    candidatos = []
    if n in (LM, LR) or (rango(ctx, n) or 0) < (rango(ctx, "departamento") or 0):
        d = departamento_de(t, n)
        if d and d != "07":
            candidatos.append(("departamento", d))
    if departamento_de(t, n) in ("07", "15") and n != AMLC:
        candidatos.append((AMLC, AMLC))  # su dominio de R-ENC-07 (Lima Metropolitana y Callao)
    destino = next(((nv, tt) for nv, tt in candidatos if verificado(nv, tt)), ("nacional", "PE"))
    sin_fila = not base_ok
    salida.insert(0, Resultado(rid, "agregar_nivel", "nivel_no_representativo",
                               clausula="sin registro de inferencia verificada" if sin_fila
                               else "nivel no verificado en la ficha técnica",
                               nivel_minimo=destino[0],
                               mensaje=(texto.split("»")[0].lstrip("«") if destino[0] == "nacional" and texto else None),
                               detalle={"nivel": n, "territorio_id": t, "destino": list(destino),
                                        "fila": None if not fila else f"{fila.get('fuente')} {fila.get('anio')} {fila.get('modulo')}",
                                        "nivel_maximo": nivel_max, "excluye_departamentos": sorted(excl)}))
    return salida


@regla("R-REG-02")
def r_reg_02(c: Cifra, ctx: Contexto):
    """Base establecimiento u ocurrencia: tasa o proporción con denominador residente pedida por distrito → provincia;
    denominador de personas atendidas en el mismo establecimiento → rótulo «en establecimientos ubicados en»;
    conteos → por distrito con ese rótulo (D4)."""
    rid = "R-REG-02"
    base = c.req("base_geografica_usada")
    if base not in ("establecimiento", "ocurrencia"):
        return None
    nv = nivel_de(c)
    tipo = c.req("tipo_estimacion")
    tipo_pob = c.req("denominador_tipo_poblacion")
    if tipo in ("tasa", "proporcion") and tipo_pob == "residente" and nv == "distrito":
        prov = provincia_de(c.territorio_id, ctx) if c.territorio_id else None
        return Resultado(rid, "agregar_nivel", "base_establecimiento", clausula="tasa base establecimiento por distrito",
                         nivel_minimo=ctx.param(rid, "nivel_minimo_tasa_base_establecimiento"),
                         mensaje=mensaje(ctx, rid, provincia=nombre_territorio(ctx, "provincia", prov)),
                         detalle={"provincia": prov})
    lugar = c.territorio_nombre or nombre_territorio(ctx, c.nivel, c.territorio_id)
    if tipo_pob == "personas_atendidas":
        rot = (f"en el establecimiento {lugar}" if c.nivel == "establecimiento"
               else f"en establecimientos ubicados en {lugar}")
        return Resultado(rid, "rotular", "base_establecimiento", clausula="denominador atendido en el establecimiento",
                         rotulo=rot, detalle={"base": base})
    if tipo == "total":
        return Resultado(rid, "rotular", "base_establecimiento", clausula="conteo por establecimiento (D4)",
                         rotulo=f"en establecimientos ubicados en {lugar}", detalle={"base": base})
    return None


@regla("R-GASTO-01")
def r_gasto_01(c: Cifra, ctx: Contexto):
    """Gasto solo en el nivel de atribución asignado o en uno superior: por debajo del departamento solo entra lo
    municipal y lo ubicado por CUI (metodo_territorio = municipal_o_cui); si la cifra trae su nivel de atribución,
    nivel_maximo_publicable lo acota."""
    rid = "R-GASTO-01"
    c.req("nivel")
    nivel = nivel_de(c)  # auditoría P2, A-2: el nivel pedido (el mensaje habla de «bajar» la cifra)
    maximos = ctx.param(rid, "nivel_maximo_publicable") or {}
    # rótulo estándar por nivel: diccionario rotulo_nivel de la implementación de R-GASTO-03
    rotulos = dict(re.findall(r"(\w+)='([^']+)'", ctx.regla("R-GASTO-03").get("implementacion") or ""))
    nat = c.nivel_atribucion_gasto
    if nat:
        tope = maximos.get(nat)
        if tope is None:
            raise CampoFaltante("nivel_atribucion_gasto")
        if (rango(ctx, nivel) or 0) < (rango(ctx, tope) or 0):
            return Resultado(rid, "agregar_nivel", "nivel_no_representativo",
                             clausula=f"{nat}: nivel máximo {tope}", nivel_minimo=tope,
                             mensaje=mensaje(ctx, rid, rotulo_nivel=rotulos.get(nat)), detalle={"nivel_atribucion": nat})
        return None
    if nivel in ("distrito", "provincia"):
        metodo = c.req("metodo_territorio")
        if metodo != "municipal_o_cui":
            return Resultado(rid, "agregar_nivel", "nivel_no_representativo",
                             clausula="gasto de ministerios/GORE solo por departamento", nivel_minimo="departamento",
                             mensaje=mensaje(ctx, rid, rotulo_nivel=metodo), detalle={"metodo_territorio": metodo})
    return None


def _rotulo_inversion(ctx: Contexto) -> str | None:
    m = re.search(r"«([^»]*ubicación principal[^»]*)»", ctx.regla("R-GASTO-02").get("condicion") or "")
    return m.group(1) if m else None


@regla("R-GASTO-02")
def r_gasto_02(c: Cifra, ctx: Contexto):
    """Inversiones: nunca se reparten; varios distritos → provincia o departamento; multidepartamental con meta fuera
    de Lima → rótulo; (5) toda cifra distrital de inversión es referencial («ubicación principal registrada»)."""
    rid = "R-GASTO-02"
    nivel = c.req("nivel")
    texto = ctx.regla(rid).get("mensaje_usuario")
    nat = c.nivel_atribucion_gasto
    destino = {"provincia_inversion": "provincia", "departamento_inversion": "departamento"}.get(nat) or \
        {"provincia": "provincia", "departamento": "departamento"}.get(c.nivel_comun)
    if destino and (rango(ctx, nivel) or 0) < (rango(ctx, destino) or 0):
        return Resultado(rid, "agregar_nivel", "nivel_no_representativo", clausula=f"(4) {nat}: no se reparte",
                         nivel_minimo=destino, mensaje=segmento(texto, "Varios distritos:"), detalle={"nivel_comun": nat})
    if nivel == "distrito":
        # (5) el detalle trae una fila por CUI (verificado en la implementación); el catálogo no trae la marca:
        # si falta, vale true (lectura restrictiva). La cifra distrital incluye lo ubicado por CUI salvo que se diga
        unica = (ctx.catalogo.get("MEF-DETALLE-INVERSIONES") or {}).get("inversion_ubicacion_unica")
        incluye = c.incluye_inversion_cui
        if unica is not False and incluye is not False:
            return Resultado(rid, "publicar_referencial", "ubicacion_principal",
                             clausula="(5) inversión distrital: ubicación principal", rotulo=_rotulo_inversion(ctx),
                             detalle={"inversion_ubicacion_unica": unica, "incluye_inversion_cui": incluye})
    # (4) multidepartamental del GN o de un GORE (campos del diccionario: auditoría P2, A-3 / H-14)
    multi = c.nivel_comun == "multidepartamental" or c.metodo_ubicacion_cui == "multidepartamental_mef"
    if multi and c.nivel_gobierno in ("E", "R"):
        meta = str(c.req("departamento_meta")).zfill(2)
        if meta == "15":
            return Resultado(rid, "agregar_nivel", "nivel_no_representativo",
                             clausula="(4) multidepartamental con meta en Lima → nacional_multidepartamental",
                             nivel_minimo="nacional", detalle={"departamento_meta": meta})
        return Resultado(rid, "rotular", "multidepartamental", clausula="(4) multidepartamental con meta fuera de Lima",
                         rotulo=segmento(texto, "con meta fuera de Lima:"),
                         mensaje=segmento(texto, "con meta fuera de Lima:"), detalle={"departamento_meta": meta})
    return None


def _linea_refnac(c: Cifra, ctx: Contexto) -> float:
    if c.refnac is not None:
        return float(c.refnac)
    f = ctx.fila_cubo(c.indicador_id, c.anio, c.nivel, c.territorio_id, c.medida, linea="referencia_nacional")
    if f is None or f.get("valor") is None:
        raise CampoFaltante("linea_referencia_nacional")
    return float(f["valor"])


@regla("R-GASTO-03")
def r_gasto_03(c: Cifra, ctx: Contexto):
    """Distrito o provincia: rótulo «gasto municipal y de proyectos…» con el % atribuible; < 0,50 → referencial y la
    respuesta principal es el departamento (en el 15, respuesta parcial). Lima (15, LM, LR): línea aparte de
    referencia nacional siempre, aviso de sesgo de sede siempre y advertencia de ejecutoras mixtas. Callao: aviso de
    sede siempre; sin cuenta_en_ambito no hay per cápita ni comparación."""
    rid = "R-GASTO-03"
    nivel, t = c.req("nivel"), str(c.req("territorio_id"))
    texto = ctx.regla(rid).get("mensaje_usuario")
    p_lima = ctx.param(rid, "lima") or {}
    p_callao = ctx.param(rid, "callao") or {}
    dpto = departamento_de(t, nivel)
    if nivel in ("distrito", "provincia"):
        pct = float(c.req("pct_gasto_atribuible"))
        umbral = ctx.param(rid, "umbral_pct_atribuible")
        rot = "gasto municipal y de proyectos ubicados en el territorio"
        msg = rellenar(segmento(texto, "(distrito o provincia)"),
                       departamento=nombre_territorio(ctx, "departamento", dpto), pct=int(100 * pct))  # truncado: 49,99 → 49
        det = {"pct_gasto_atribuible": pct, "umbral": umbral, "mostrar_siempre_pct": ctx.param(rid, "mostrar_siempre_pct")}
        if pct < umbral:
            respaldo = ctx.param(rid, "respaldo_departamental")
            principal = ({"respuesta_parcial": True, "nota": "NC-GASTO-LUGAR"} if dpto == "15"
                         else {"nivel": "departamento", "territorio_id": dpto})
            return Resultado(rid, "publicar_referencial", "pct_atribuible_bajo", clausula="pct_gasto_atribuible < 0,50",
                             rotulo=rot, mensaje=msg, detalle={**det, "respuesta_principal": principal,
                                                               "respaldo": respaldo})
        return Resultado(rid, "rotular", "gasto_subdepartamental", clausula="pct_gasto_atribuible ≥ 0,50",
                         rotulo=rot, mensaje=msg, detalle=det)
    salida = []
    if nivel in (LM, LR) or (nivel == "departamento" and dpto == "15"):
        refnac = _linea_refnac(c, ctx)
        millones = round(refnac / 1e6, 1)
        if refnac:
            linea = rellenar(segmento(texto, "(cifras de Lima, siempre, en una línea aparte)"),
                             refnac=f"{millones:,.1f}".replace(",", " ").replace(".", ","))
        else:
            linea = segmento(texto, "(si es 0)")
        salida.append(Resultado(rid, "rotular", "linea_referencia_nacional", clausula="Lima: línea aparte de refnac",
                                mensaje=linea, detalle={"refnac": refnac, "linea": p_lima.get("linea_aparte")}))
        sede = p_lima.get("aviso_sesgo_sede") or {}
        salida.append(Resultado(rid, "advertir", "sesgo_sede", clausula="Lima: aviso de sesgo de sede",
                                aviso="sesgo_sede",
                                mensaje=rellenar(segmento(texto, "(cifras de Lima, siempre)"), pct_sede=sede.get("pct_sede")),
                                detalle={"pct_sede": sede.get("pct_sede")}))
        oblig = p_lima.get("funciones_advertencia_obligatoria") or {}
        funciones = {str(x).upper() for x in _lista(c.funciones) + _lista(c.funcion)}
        obligatoria = "ejecutoras_mixtas" in avisos(c) or bool(funciones & {v.upper() for v in oblig.values()})
        if obligatoria or c.hay_mixtas_lima is not False:
            progs = _lista(c.programas_mixtos)[:3]
            if progs:
                m = rellenar(segmento(texto, "obligatoria en seguridad, justicia, transporte, salud y protección social)"),
                             programas_mixtos=", ".join(progs))
            else:
                m = segmento(texto, "(sin mixtas en el tema ni en la función)")
            salida.append(Resultado(rid, "advertir", "ejecutoras_mixtas", clausula="Lima: advertencia de mixtas",
                                    aviso="ejecutoras_mixtas", mensaje=m,
                                    detalle={"obligatoria": obligatoria, "programas_mixtos": progs}))
        return salida
    if nivel == CALLAO or dpto == "07":
        sede = p_callao.get("aviso_sesgo_sede") or {}
        salida.append(Resultado(rid, "advertir", "sesgo_sede", clausula="Callao: aviso de sede", aviso="sesgo_sede",
                                mensaje=segmento(texto, "(cifras del Callao, siempre)"),
                                detalle={"pct_sede": sede.get("pct_sede"), "avisos_cubo": avisos(c)}))
        compara = c.intencion_pregunta in ("comparacion", "identificar_extremo") or bool(c.per_capita)
        if compara and c.metodo_territorio != "ambito_gasto":
            salida.append(Resultado(rid, "bloquear_cruce", "callao_sin_separar",
                                    clausula="Callao sin cuenta_en_ambito: sin per cápita ni comparación",
                                    mensaje=segmento(texto, "si aún no se separa ese gasto)"),
                                    detalle={"per_capita_y_ranking": p_callao.get("per_capita_y_ranking")}))
        return salida
    return None


@regla("R-TERRITORIO-04")
def r_territorio_04(c: Cifra, ctx: Contexto):
    """Serie distrital que cruza la creación de un distrito (o con grupo comparable ≠ ubigeo) → geografía GEO2017
    (grupo comparable); un solo año → geografía vigente."""
    rid = "R-TERRITORIO-04"
    if nivel_de(c) != "distrito":
        return None
    anios = {int(c.req("anio"))}
    for s in _lista(c.serie):
        a = s.get("anio") if isinstance(s, dict) else getattr(s, "anio", None)
        if a is not None:
            anios.add(int(a))
    if c.comparacion:
        a = c.comparacion.get("anio") if isinstance(c.comparacion, dict) else getattr(c.comparacion, "anio", None)
        if a is not None:
            anios.add(int(a))
    if c.periodo_agrupado:
        anios |= set(range(int(c.periodo_agrupado[0]), int(c.periodo_agrupado[1]) + 1))
    if len(anios) < 2:
        return None  # n = 1 → geografía vigente del año
    a1, an = min(anios), max(anios)
    u = str(c.req("territorio_id"))
    ub = ctx.ubigeos
    f = filas_ubigeo(ctx, u)
    if f is None:
        raise CampoFaltante("dim_ubigeo_historico")
    if f.empty:
        return None  # sin ubigeo no hay geografía que elegir: lo decide R-TERRITORIO-01
    grupo = f.iloc[-1].grupo_comparable_geo2017
    nuevo = bool((f.anio_datos_desde.astype("Float64") > a1).fillna(False).any())
    hermanos = ub[(ub.grupo_comparable_geo2017 == grupo) & (ub.ubigeo_inei != u) & (ub.nivel == "distrito")]
    dd = hermanos.anio_datos_desde.astype("Float64")
    hijos = hermanos[((dd > a1) & (dd <= an)).fillna(False).astype(bool)]
    agrupado = isinstance(grupo, str) and grupo != u
    if not (nuevo or not hijos.empty or agrupado):
        return None
    nombres = ", ".join(sorted(set(map(str, hijos.nombre_mostrado)))) or None
    return Resultado(rid, "agregar_al_grupo", "geografia_geo2017", clausula="serie distrital → GEO2017",
                     modo="grupo_comparable", mensaje=mensaje(ctx, rid, nombre=c.territorio_nombre, hijos=nombres),
                     detalle={"geografia_base": ctx.param(rid, "geografia_congelada"), "grupo_comparable": grupo,
                              "anios": [a1, an]})


@regla("R-EST-05")
def r_est_05(c: Cifra, ctx: Contexto):
    """Pregunta distrital cuya única fuente distrital es una estimación modelada de más de 5 años → cifra principal,
    publicar_referencial con semáforo rojo fijo; contexto obligatorio: la ENAHO departamental (o del ámbito en Lima)."""
    rid = "R-EST-05"
    if nivel_de(c) != "distrito":
        return None
    tema = c.req("tema")
    naturalezas = set()
    for i in ctx.indicadores.values():
        if i.get("tema") != tema:
            continue
        if any((nv or {}).get("nivel") == "distrito" for nv in i.get("niveles_validos") or []):
            naturalezas.add(i.get("naturaleza_dato"))
    edad = ctx.anio_actual - int(c.req("anio"))
    limite = ctx.param(rid, "edad_maxima_anios")
    if limite is None:
        raise CampoFaltante("R-EST-05.parametros.edad_maxima_anios")
    if naturalezas != {"estimacion_modelada"} or edad <= limite:
        return None
    dpto = departamento_de(c.territorio_id, "distrito")
    ctx_nivel = (LM if str(c.territorio_id).startswith("1501") else LR) if dpto == "15" else \
        (CALLAO if dpto == "07" else "departamento")
    return Resultado(rid, "publicar_referencial", "modelada_antigua", clausula="única fuente distrital modelada > 5 años",
                     mensaje=mensaje(ctx, rid, anio=c.anio),
                     detalle={"es_principal": True, "semaforo_cifra": "rojo", "edad_dato": edad,
                              "contexto_obligatorio": ctx.param(rid, "contexto_obligatorio"),
                              "contexto": {"nivel": ctx_nivel, "territorio_id": ctx_nivel if ctx_nivel != "departamento"
                                           else dpto},
                              "ranking": ctx.param(rid, "ranking")})


# ======================================================================= etapa 3: denominadores

def denominador_efectivo(c: Cifra) -> dict:
    """Denominador que usa la cifra: el principal de dim_indicador o, en los ámbitos de Lima, el de
    denominador_ambitos_lima (propio IPF en LM y LR; oficial en el Callao; D-IND-7, L7)."""
    dal = c.denominador_ambitos_lima or {}
    for clase in ("propio", "oficial"):
        d = dal.get(clase) or {}
        if c.nivel in (d.get("ambitos") or []):
            return {"fuente_id": d.get("fuente_id"), "metodo": d.get("metodo_denominador"),
                    "geografia_base": str(d.get("filtro", {}).get("geografia_base", "")).replace("{anio}", str(c.anio)),
                    "rotulo": d.get("rotulo"), "vintage": c.vintage_denominador if clase == "oficial" else
                    f"{d.get('fuente_id')}|crudos={'+'.join(d.get('crudos') or [])}"}
    dp = c.denominador_principal
    return {"fuente_id": str(dp).split("|")[0] if dp else None, "metodo": c.metodo_denominador,
            "geografia_base": f"vigente_{c.anio}", "rotulo": None, "vintage": c.vintage_denominador}


def _entrada_matriz(ctx: Contexto, tipo: str) -> dict | None:
    for k, v in (ctx.param("R-DENOMINADORES-01", "matriz") or {}).items():
        if k == tipo or k.split(" (")[0] == tipo:
            return v
    return None


@regla("R-DENOMINADORES-01")
def r_denominadores_01(c: Cifra, ctx: Contexto):
    """requiere_denominador = true y denominador principal nulo o fuera de la matriz de su tipo → la cifra no se
    publica; RENIEC nunca es principal. Válido → rótulo de la población usada."""
    rid = "R-DENOMINADORES-01"
    if c.req("requiere_denominador") is not True:
        return None
    tipo = c.req("tipo_denominador")
    dp = c.denominador_principal
    entrada = _entrada_matriz(ctx, tipo)
    efectivo = denominador_efectivo(c)
    det = {"tipo_denominador": tipo, "denominador_principal": dp, "efectivo": efectivo}
    if not dp or entrada is None or "RENIEC" in str(dp).upper():
        return Resultado(rid, "bloquear", "denominador_no_valido", clausula="principal nulo, fuera de la matriz o RENIEC",
                         detalle=det)
    textos = [str(entrada.get("principal") or "")]
    if c.nivel in ("departamento", CALLAO, LM, LR):
        textos.append(str(entrada.get("principal_por_departamento") or ""))
    fuente = efectivo["fuente_id"] or ""
    valido = any(fuente and fuente in tx for tx in textos)
    if not valido and efectivo["metodo"] in ("propio", "prorrateo_propio"):
        valido = any("prorrateo propio" in tx for tx in textos)
    if not valido:
        return Resultado(rid, "bloquear", "denominador_no_valido", clausula="denominador ∉ matriz[tipo_denominador]",
                         detalle=det)
    # casos_borde: principal no disponible para el año → primer contraste, «población alternativa», referencial
    usado = c.denominador_usado
    if usado and str(usado).split("|")[0] != fuente:
        return Resultado(rid, "publicar_referencial", "denominador_alternativo", clausula="principal no disponible",
                         rotulo="población alternativa", detalle={**det, "usado": usado})
    po = c.poblacion_objetivo
    base = po.get("descripcion") if isinstance(po, dict) else po
    return Resultado(rid, "rotular", "denominador", clausula="denominador de la matriz", rotulo=efectivo.get("rotulo"),
                     mensaje=mensaje(ctx, rid, poblacion_base=(base if str(base).startswith("de ") else f"de {base}"), fuente_poblacion=efectivo.get("rotulo") or fuente,
                                     anio=c.anio), detalle=det)


@regla("R-DENOMINADORES-02")
def r_denominadores_02(c: Cifra, ctx: Contexto):
    """Un solo vintage del denominador por serie (si no → bloquear la serie) y, en un cociente con numerador
    poblacional, el mismo vintage arriba y abajo (si no → la cifra no se publica)."""
    rid = "R-DENOMINADORES-02"
    if c.req("requiere_denominador") is not True:
        return None
    ef = denominador_efectivo(c)
    vintage = ef.get("vintage")
    if not vintage or str(vintage) == "no_aplica":
        raise CampoFaltante("vintage_denominador")
    if c.numerador_es_poblacion and c.vintage_numerador and c.vintage_numerador != vintage:
        return Resultado(rid, "bloquear", "vintage_distinto", clausula="cociente: vintage numerador ≠ denominador",
                         detalle={"numerador": c.vintage_numerador, "denominador": vintage})
    serie = _lista(c.serie)
    if len(serie) > 1:
        vs = set()
        for s in serie:  # auditoría P2, A-9 (H-21): cada fila de la serie declara su vintage; no se hereda
            v = s.get("vintage_denominador") if isinstance(s, dict) else getattr(s, "vintage_denominador", None)
            if not v:
                raise CampoFaltante("vintage_denominador")
            vs.add(str(v))
        if len(vs) > 1:
            return Resultado(rid, "bloquear_cruce", "vintage_distinto", clausula="serie con más de un vintage",
                             detalle={"vintages": sorted(vs)})
        return Resultado(rid, "rotular", "vintage_unico", clausula="serie con un solo vintage",
                         mensaje=mensaje(ctx, rid, edicion_poblacion=vintage), detalle={"vintage_denominador": vintage})
    return None


@regla("R-DENOMINADORES-05")
def r_denominadores_05(c: Cifra, ctx: Contexto):
    """Sensibilidad al denominador s (contrastes aprobados, sin RENIEC): s ≤ 0,10 → publicar; s nulo con prorrateo
    propio → referencial con rótulo; 0,10 < s ≤ 0,25 → referencial con rango; s > 0,25 → provincia (rango distrital
    solo en la ficha). Además: RENIEC difiere > 0,20 → nota."""
    rid = "R-DENOMINADORES-05"
    if c.req("requiere_denominador") is not True:
        return None
    if c.valor is not None and float(c.valor) > 100:
        return None  # casos_borde: coberturas > 100 % se rigen por R-REG-08 antes que por esta regla
    u_rango, u_sup, u_ren = (ctx.param(rid, k) for k in ("umbral_rango", "umbral_suprimir_puntual", "umbral_nota_reniec"))
    ef = denominador_efectivo(c)
    d_ppal = c.denominador
    s = c.sensibilidad_denominador
    rango_i = c.rango_indicador
    usados = _lista(c.denominadores_usados) or _lista(c.denominadores)  # auditoría P2, A-5: denominadores_usados
    denoms = [d for d in usados if "RENIEC" not in str(d.get("fuente", "")).upper()]
    reniec = [d for d in usados if "RENIEC" in str(d.get("fuente", "")).upper()]
    if s is None and denoms and d_ppal:
        s = max(abs(float(d["valor"]) - float(d_ppal)) / float(d_ppal) for d in denoms)
        if c.numerador is not None:
            vals = [100 * float(c.numerador) / float(d["valor"]) for d in denoms] + [100 * float(c.numerador) / float(d_ppal)]
            rango_i = [min(vals), max(vals)]
    if s is None:
        aprobados = [j for j in _lista(c.denominadores_contraste) if "RENIEC" not in str(j).upper() and
                     (ctx.catalogo.get(str(j).split("|")[0]) or {}).get("compuerta_ingesta") == "aprobada"]
        if aprobados:
            s = c.req("sensibilidad_denominador")  # hay contrastes utilizables y no se midió s
    salida = []
    det = {"s": s, "metodo": ef.get("metodo"), "rango_indicador": rango_i}
    if s is not None and float(s) <= u_rango:
        pass
    elif s is None and ef.get("metodo") in ("prorrateo_propio", "propio"):
        salida.append(Resultado(rid, "publicar_referencial", "denominador_propio", clausula="s nulo y prorrateo propio",
                                rotulo=ef.get("rotulo") or "estimación propia", detalle=det))
    elif s is not None and float(s) <= u_sup:
        mn, mx = (rango_i or [None, None])[:2]
        salida.append(Resultado(rid, "publicar_rango", "sensibilidad_denominador", clausula="0,10 < s ≤ 0,25 → rango",
                                mensaje=mensaje(ctx, rid, min=mn, max=mx, valor=c.valor,
                                                fuente_principal=ef.get("fuente_id")), detalle=det))
    elif s is not None:
        if (rango(ctx, nivel_de(c)) or 0) <= (rango(ctx, "distrito") or 0):
            salida.append(Resultado(rid, "agregar_nivel", "precision", clausula="s > 0,25 → provincia",
                                    nivel_minimo="provincia", detalle={**det, "rango_distrital": "solo en la ficha"}))
        else:  # no es distrital: se mantiene el rango (lectura restrictiva)
            salida.append(Resultado(rid, "publicar_rango", "sensibilidad_denominador", clausula="s > 0,25 (no distrital)",
                                    detalle=det))
    d_ren = c.denominador_reniec if c.denominador_reniec is not None else (reniec[0].get("valor") if reniec else None)
    if d_ren is not None and d_ppal and abs(float(d_ren) - float(d_ppal)) / float(d_ppal) > u_ren:
        salida.append(Resultado(rid, "nota", "reniec_difiere", clausula="Además: RENIEC difiere > 0,20",
                                detalle={"reniec": d_ren}, modificador=True))
    return salida or None


def _anio_de(fecha) -> int | None:
    m = re.match(r"(\d{4})", str(fecha or ""))
    return int(m.group(1)) if m else None


@regla("R-DENOMINADORES-07")
def r_denominadores_07(c: Cifra, ctx: Contexto):
    """Numerador y denominador en la misma geografía y con la misma fecha de referencia (desfase máximo 0 años; para
    stocks con corte en el primer trimestre se admite el año anterior, rotulado)."""
    rid = "R-DENOMINADORES-07"
    if c.req("requiere_denominador") is not True:
        return None
    ef = denominador_efectivo(c)
    serie = _lista(c.serie)
    if len(serie) > 1:  # en una serie la geografía no se deduce del año: tiene que venir en la cifra
        g_num, g_den = c.req("geografia_base_numerador"), c.req("geografia_base_denominador")
    else:  # una cifra del cubo: numerador y denominador en geografía vigente del año (calculo.py)
        g_num = c.geografia_base_numerador or f"vigente_{c.req('anio')}"
        g_den = c.geografia_base_denominador or ef.get("geografia_base")
    # auditoría P2, A-4 (H-15): años de fecha_ref_numerador y fecha_ref_denominador (respaldo: anio, anio_denominador)
    anio = _anio_de(c.fecha_ref_numerador) or int(c.req("anio"))
    a_den = _anio_de(c.fecha_ref_denominador) or (int(c.anio_denominador) if c.anio_denominador is not None else anio)
    det = {"geografia_numerador": g_num, "geografia_denominador": g_den, "anio": anio, "anio_denominador": a_den,
           "fecha_ref_numerador": c.fecha_ref_numerador, "fecha_ref_denominador": c.fecha_ref_denominador}
    if g_num != g_den:
        return Resultado(rid, "bloquear", "denominador_desalineado", clausula="geografía numerador ≠ denominador",
                         detalle=det)
    if abs(anio - a_den) > ctx.param(rid, "desfase_maximo_anios"):
        corte = str(c.fecha_ref_numerador or c.fecha_corte or "")
        if c.es_stock and a_den == anio - 1 and re.fullmatch(r"\d{4}-0[1-3]-\d{2}", corte):
            return Resultado(rid, "rotular", "denominador_anio_anterior", clausula="stock con corte en el 1.er trimestre",
                             rotulo=f"población de {a_den}", detalle=det)
        return Resultado(rid, "bloquear", "denominador_desalineado", clausula="año numerador ≠ denominador", detalle=det)
    return None


@regla("R-GASTO-12")
def r_gasto_12(c: Cifra, ctx: Contexto):
    """Montos de más de un año → soles constantes del último año cerrado (IPC Lima, promedio anual); un solo año →
    soles corrientes, rotulado. Los ratios no se deflactan."""
    rid = "R-GASTO-12"
    if c.tipo_estimacion in ("razon", "proporcion", "tasa"):
        return None
    anios = {int(c.req("anio"))}
    for s in _lista(c.serie):
        a = s.get("anio") if isinstance(s, dict) else getattr(s, "anio", None)
        if a is not None:
            anios.add(int(a))
    if c.comparacion:
        a = c.comparacion.get("anio") if isinstance(c.comparacion, dict) else getattr(c.comparacion, "anio", None)
        if a is not None:
            anios.add(int(a))
    base = ctx.anio_actual - 1  # parametros.anio_base: último año cerrado
    if len(anios) > 1:
        if c.precios != "constantes" or (c.anio_base_deflactor is not None and int(c.anio_base_deflactor) != base):
            return Resultado(rid, "bloquear_cruce", "serie_sin_deflactar",
                             clausula="montos de > 1 año sin soles constantes del último año cerrado",
                             detalle={"anios": sorted(anios), "precios": c.precios, "anio_base": base,
                                      "serie_ipc": ctx.param(rid, "serie_ipc")})
        return Resultado(rid, "rotular", "soles_constantes", clausula="> 1 año → soles constantes",
                         rotulo=f"soles constantes de {base}", mensaje=mensaje(ctx, rid, anio_base=base),
                         detalle={"anio_base": base, "factores": c.factores_deflactor, "serie_ipc": ctx.param(rid, "serie_ipc")})
    return Resultado(rid, "rotular", "soles_corrientes", clausula="un solo año → soles corrientes",
                     rotulo=f"soles corrientes de {min(anios)}", detalle={"precios": "corrientes"})
