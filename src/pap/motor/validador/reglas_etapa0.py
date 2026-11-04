"""Etapa 0 del validador (P2, grupo A): prerrequisitos y secuencia del motor.

Reglas: R-MOTOR-03 (periodo), R-DEP-01 (insumos aprobados), R-MOTOR-01 (secuencia de degradación; además
`siguiente_paso`, que usa `validador.evaluar_con_degradacion`) y R-MOTOR-02 (metadatos del indicador; la precedencia y
la normalización viven en el núcleo).

Fuente de verdad: reglas/reglas.json (condición, parámetros, mensajes) y las decisiones del dueño de 2026-10-08 a
2026-10-10. Umbrales y listas se leen con `ctx.param`; ningún valor de una regla se escribe aquí a mano. Este módulo
también trae ayudas territoriales que comparte con `reglas_etapa1_3.py` (departamento, contenedor, ámbitos de Lima).
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from .nucleo import CampoFaltante, Cifra, Contexto, Resultado, regla

# ======================================================================= ayudas compartidas (grupo A)

# Ámbitos de Lima (decisión del dueño, 9/10/2026): son valores de NIVEL_RANK y, en el cubo, territorio_id = nivel.
LM, LR, CALLAO, AMLC = "LIMA_METROPOLITANA", "LIMA_REGION", "CALLAO", "AREA_METROPOLITANA_LIMA_CALLAO"
AMBITOS = (LM, LR, CALLAO, AMLC)
# encuesta de dim_dominio (dominios.yaml) por fuente del catálogo
ENCUESTA = {"INEI-ENDES": "ENDES", "INEI-ENAHO": "ENAHO", "INEI-ENAPRES": "ENAPRES", "MINEDU-UMC-ENLA": "ENLA"}
# nivel del cubo → nombre en dominios_inferencia de dim_indicador
DOMINIO_DE_NIVEL = {"nacional": "nacional", "departamento": "departamento", CALLAO: "callao",
                    LM: "lima_metropolitana", LR: "lima_provincias", AMLC: "area_metropolitana_lima_callao"}


def nivel_de(c: Cifra) -> str | None:
    """Nivel que la regla evalúa: el pedido por la consulta o, si no lo hay, el de la fila."""
    return c.nivel_pedido or c.nivel


def rango(ctx: Contexto, nivel: str | None) -> float | None:
    return ctx.nivel_rank(nivel) if nivel else None


def mensaje(ctx: Contexto, rid: str, **valores) -> str | None:
    """mensaje_usuario de la regla con los marcadores {x} que se conocen rellenados (los demás quedan tal cual)."""
    m = ctx.regla(rid).get("mensaje_usuario")
    if not m:
        return None
    m = m.strip()
    if m.startswith("«") and m.endswith("»") and m.count("«") == 1:
        m = m[1:-1]  # el mensaje entero entre comillas: el texto al usuario va sin ellas
    return re.sub(r"\{(\w+)\}", lambda x: str(valores[x.group(1)]) if valores.get(x.group(1)) is not None
                  else x.group(0), m)


def ubigeo6(territorio_id: str | None) -> str | None:
    """Convención del cubo → ubigeo INEI de 6 dígitos: departamento '09' → '090000'; provincia y distrito sin cambio."""
    t = str(territorio_id or "")
    if re.fullmatch(r"\d{2}", t):
        return t + "0000"
    if re.fullmatch(r"\d{6}", t):
        return t
    return None


def departamento_de(territorio_id: str | None, nivel: str | None = None) -> str | None:
    """Departamento (2 dígitos) que contiene al territorio; LM y LR → 15, Callao → 07; dominio 8 y el resto → None."""
    t = str(territorio_id or "")
    if t in (LM, LR) or nivel in (LM, LR):
        return "15"
    if t == CALLAO or nivel == CALLAO:
        return "07"
    if re.fullmatch(r"\d{2}|\d{6}", t) and nivel != "establecimiento":
        return t[:2]
    return None


_UBIGEOS: dict = {}


def filas_ubigeo(ctx: Contexto, u: str | None):
    """Versiones de un ubigeo en dim_ubigeo_historico (DataFrame), con un índice en caché por tabla."""
    ub = ctx.ubigeos
    if ub is None or u is None:
        return None
    clave = id(ub)
    if clave not in _UBIGEOS:
        _UBIGEOS.clear()
        _UBIGEOS[clave] = {k: g for k, g in ub.groupby("ubigeo_inei", sort=False)}
    return _UBIGEOS[clave].get(str(u), ub.iloc[0:0])


def provincia_de(territorio_id: str, ctx: Contexto) -> str | None:
    """Provincia (6 dígitos, termina en 00) de un distrito; se lee de dim_ubigeo_historico (ubigeo_padre)."""
    t = str(territorio_id)
    if not re.fullmatch(r"\d{6}", t):
        return None
    if t.endswith("00"):
        return t
    f = filas_ubigeo(ctx, t)
    if f is not None:
        f = f[f.nivel == "distrito"]
        if not f.empty and isinstance(f.iloc[-1].ubigeo_padre, str):
            return f.iloc[-1].ubigeo_padre
    return t[:4] + "00"


def es_encuesta(c: Cifra) -> bool:
    return c.naturaleza_dato == "encuesta_muestral"


def contenedor(c: Cifra, nivel_destino: str, ctx: Contexto, territorio_id: str | None = None,
               nivel_actual: str | None = None) -> tuple[str, str] | None:
    """(nivel, territorio_id) del territorio de `nivel_destino` que contiene al territorio de la cifra, con las
    convenciones del cubo. En el departamento 15 las encuestas suben al ámbito (LM o LR, R-ENC-06, L1) y el Callao es
    el nivel CALLAO en todas las fuentes (el cubo no tiene departamento 07). El dominio 8 no baja a departamento."""
    t = str(territorio_id if territorio_id is not None else c.territorio_id or "")
    nv = nivel_actual or c.nivel
    if nivel_destino == "nacional":
        return "nacional", "PE"
    if nv == AMLC:
        return None  # R-MOTOR-01, casos_borde (9/10/2026): ningún departamento contiene al dominio 8
    if nivel_destino == "provincia":
        p = provincia_de(t, ctx)
        return ("provincia", p) if p else None
    if nivel_destino in ("departamento",) + AMBITOS:
        d = departamento_de(t, nv)
        if d is None:
            return None
        if d == "07":
            return CALLAO, CALLAO
        if d == "15" and nivel_destino == "departamento" and es_encuesta(c) and nv not in (LM, LR) \
                and re.fullmatch(r"\d{6}", t):
            return (LM, LM) if t.startswith("1501") else (LR, LR)
        if nivel_destino in (LM, LR):
            return nivel_destino, nivel_destino
        return "departamento", d
    return None


def regla_dominio(ctx: Contexto, encuesta: str | None, anio, nivel: str | None, territorio_id: str | None) -> dict | None:
    """Fila de dim_dominio (reglas de dominios.yaml) que usa la cifra: por ámbito (ambito_id = nivel) o por el
    dominio genérico del nivel (nacional, urbano/rural, departamento)."""
    if not encuesta or anio is None:
        return None
    a = int(anio)
    for r in ctx.dominios or []:
        a0, a1 = r.get("anios", [None, None])
        if r.get("encuesta") != encuesta or a0 is None or not (a0 <= a <= a1):
            continue
        if nivel in AMBITOS and r.get("ambito_id") == nivel:
            return r
        if nivel == "nacional" and r.get("dominio_id") == "nacional":
            return r
        if nivel == "dominio_subnacional" and r.get("dominio_id") == territorio_id:
            return r
        if nivel == "departamento" and r.get("dominio_id") == "departamento" \
                and str(territorio_id) not in (r.get("excluye") or []):
            return r
    return None


def anios_en_cubo(ctx: Contexto, indicador: str | None, nivel: str | None, territorio: str | None,
                  medida: str | None = None) -> set[int]:
    cu = ctx.cubo
    if cu is None or not indicador:
        return set()
    m = (cu.indicador_id == indicador) & (cu.nivel == nivel) & (cu.territorio_id == str(territorio)) & \
        (cu.linea == "cifra")
    if medida:
        m &= cu.medida == medida
    return {int(x) for x in cu[m].anio.unique()}


# ======================================================================= R-MOTOR-03

@regla("R-MOTOR-03")
def r_motor_03(c: Cifra, ctx: Contexto):
    """Periodo pedido nulo → último año cerrado con dato aprobado de la fuente (se rotula). Año en curso: solo si se
    pide, rotulado «dato preliminar al {fecha_corte}»."""
    rid = "R-MOTOR-03"
    anio = int(c.req("anio"))
    preliminar = anio >= ctx.anio_actual or c.anio_cerrado is False
    # periodo pedido: año, serie, comparación (auditoría P2, A-8) o periodo agrupado
    pedido = c.anio_pedido is not None or bool(c.serie) or c.comparacion is not None or c.periodo_agrupado is not None
    if pedido:
        if preliminar:  # parametros.anio_en_curso: solo si la pregunta lo pide
            corte = c.fecha_corte or ctx.fecha_referencia
            return Resultado(rid, "rotular", "anio_en_curso", clausula="año en curso pedido: dato preliminar",
                             rotulo=f"dato preliminar al {corte}", detalle={"anio": anio, "fecha_corte": corte,
                                                                          "regla_parametro": ctx.param(rid, "anio_en_curso")})
        return None
    # periodo_pedido IS NULL → anio(fuente) = max(anio con compuerta aprobada AND es_preliminar = false)
    comp = (ctx.catalogo.get(c.fuente_principal) or {}).get("compuerta_ingesta")
    disponibles = anios_en_cubo(ctx, c.indicador_id, c.nivel, c.territorio_id, c.medida) or \
        {int(x) for x in (c.anios_disponibles or [])}
    cerrados = sorted(a for a in disponibles if a < ctx.anio_actual)
    ultimo = cerrados[-1] if cerrados else None
    det = {"anio_cifra": anio, "ultimo_anio_cerrado": ultimo, "compuerta_fuente": comp,
           "nota_gasto": "gasto: último año cerrado + acumulado de cartera activa (R-GASTO-17)"
           if c.naturaleza_dato == "presupuestal_financiero" else None}
    if ultimo is None or anio != ultimo or preliminar:
        # lectura restrictiva: el motor resolvió un año distinto del que fija la regla → revisión
        return Resultado(rid, "revision_humana", "periodo_no_resuelto", clausula="periodo nulo: año ≠ último cerrado",
                         detalle=det)
    return Resultado(rid, "rotular", "periodo_por_defecto", clausula="periodo nulo → último año cerrado",
                     mensaje=mensaje(ctx, rid, anio=anio), detalle=det)


# ======================================================================= R-DEP-01

_TEMAS_CACHE: dict = {}


def _temas_aprobados(ctx: Contexto) -> dict | None:
    """tema_id → revisado_por de dim_tema_gasto (fuente curada: curados/capa0/trazabilidad). La tabla
    dim_tema_gasto no está en el contexto del validador; se lee de los YAML de los que se construye."""
    if isinstance(getattr(ctx, "temas_gasto", None), dict):
        return ctx.temas_gasto
    raiz = getattr(ctx, "raiz", None)
    if raiz is None:
        return None
    clave = str(raiz)
    if clave not in _TEMAS_CACHE:
        import yaml
        base = Path(raiz) / "curados" / "capa0" / "trazabilidad"
        out = {}
        for nombre, lista, pref in (("temas_gasto.yaml", "temas", ""), ("programas_sociales.yaml", "programas", "ps_")):
            p = base / nombre
            if not p.exists():
                continue
            d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            rev = str(d.get("revisado_por") or "")
            for t in d.get(lista) or []:
                tid = t.get("tema_id") or (pref + str(t.get("id")) if pref else None)
                if tid:
                    out[tid] = rev
        _TEMAS_CACHE[clave] = out
    return _TEMAS_CACHE[clave]


def _fila_curada_confirmada(tabla: str, c: Cifra, ctx: Contexto) -> tuple[bool, dict]:
    """fila_usada.confirmado de R-DEP-01 (D-AUD-1): dim_dominio → confirmado = true de la fila del dominio o ámbito
    de la cifra; dim_tema_gasto → tema aprobado por el dueño."""
    if tabla == "dim_dominio":
        enc = ENCUESTA.get(c.fuente_principal)
        nivel = c.req("nivel")
        if nivel not in ("nacional", "dominio_subnacional", "departamento") + AMBITOS:
            return True, {"encuesta": enc, "nota": f"el nivel {nivel} no usa filas de dim_dominio"}
        r = regla_dominio(ctx, enc, c.req("anio"), nivel, c.territorio_id)
        return (r is not None and r.get("confirmado") is True), {"encuesta": enc, "dominio": (r or {}).get("dominio_id")}
    if tabla == "dim_tema_gasto":
        if c.tema_aprobado is not None:
            return bool(c.tema_aprobado), {"tema_id": c.tema_id, "origen": "campo tema_aprobado"}
        tema = c.req("tema_id")
        tg = getattr(ctx, "tema_gasto", None)
        if tg is not None and not isinstance(tg, dict):  # dim_tema_gasto (contrato §5): fila del año y del tema
            anio = int(c.req("anio"))
            f = tg[(tg.tema_id == tema) & (tg.anio.astype(int) == anio)]
            rev = str(f.iloc[0].revisado_por) if not f.empty else None
            return (rev is not None and rev.strip().lower().startswith("dueño")), \
                {"tema_id": tema, "anio": anio, "revisado_por": rev, "origen": "ctx.tema_gasto"}
        temas = _temas_aprobados(ctx)
        if temas is None:
            raise CampoFaltante("tema_aprobado")
        rev = temas.get(tema)
        return (rev is not None and rev.strip().lower().startswith("dueño")), {"tema_id": tema, "revisado_por": rev}
    return False, {}


@regla("R-DEP-01")
def r_dep_01(c: Cifra, ctx: Contexto):
    """Insumos: numerador, denominador principal y crudos de tablas curadas con compuerta «aprobada» en el catálogo;
    contraste no aprobado → nota en la ficha larga; tablas solo curadas → su manifiesto (D-AUD-1)."""
    rid = "R-DEP-01"
    insumos = c.req("insumos")
    solo_curadas = ctx.param(rid, "tablas_solo_curadas") or {}
    salida, contraste = [], []
    malos, sin_respaldo = [], []
    for i in insumos:
        iid, rol = i.get("id"), i.get("rol")
        if iid in solo_curadas:
            continue
        comp = (ctx.catalogo.get(iid) or {}).get("compuerta_ingesta")
        if comp == "aprobada":
            continue
        if rol in ("numerador", "denominador_principal", "tabla_curada"):
            malos.append({"id": iid, "rol": rol, "compuerta": comp})
        elif rol == "contraste":
            contraste.append({"id": iid, "compuerta": comp})
    # cláusula 1: insumo bloqueante no aprobado
    if malos:
        salida.append(Resultado(rid, "suprimir", "insumo_en_ingesta", clausula="insumo no aprobado en el catálogo",
                                mensaje=mensaje(ctx, rid), detalle={"insumos": malos}))
    else:
        # cláusula 3: tablas solo curadas sin respaldo en su manifiesto o con la fila usada sin confirmar
        for i in insumos:
            t = i.get("id")
            if t not in solo_curadas:
                continue
            mf = str(solo_curadas[t]).replace("manifiesto_", "", 1)
            man = (ctx.manifiestos or {}).get(mf) or {}
            fallidas = ((man.get("pruebas") or {}).get("bloqueantes_fallidas"))
            en_man = t in (man.get("tablas") or {})
            ok_fila, det = _fila_curada_confirmada(t, c, ctx)
            if not en_man or fallidas or not ok_fila:
                sin_respaldo.append({"tabla": t, "manifiesto": solo_curadas[t], "en_manifiesto": en_man,
                                     "bloqueantes_fallidas": fallidas, "fila_confirmada": ok_fila, **det})
        if sin_respaldo:
            salida.append(Resultado(rid, "suprimir", "tabla_curada_sin_respaldo",
                                    clausula="tabla solo curada sin respaldo (D-AUD-1)", mensaje=mensaje(ctx, rid),
                                    detalle={"tablas": sin_respaldo}))
    # cláusula 2: contraste no aprobado → se omite con nota en la ficha larga (no cambia la acción)
    if contraste:
        salida.append(Resultado(rid, "nota", "contraste_no_aprobado", clausula="contraste no aprobado: se omite",
                                detalle={"contraste_omitido": contraste, "destino": "ficha_larga"}, modificador=True))
    return salida or None


# ======================================================================= R-MOTOR-01

def _secuencia(c: Cifra, ctx: Contexto) -> tuple[str, list[str]]:
    """parametros.prioridad_secuencia: celda sensible de registros, censos o derivados → fuente_sensible; encuestas,
    la suya; el resto, la de su naturaleza_dato."""
    rid = "R-MOTOR-01"
    sec = ctx.param(rid, "secuencia_degradacion") or {}
    nat = c.req("naturaleza_dato")
    if c.sensibilidad_divulgacion == "sensible" and nat in ("registro_administrativo", "censo", "indicadores_derivados"):
        return "fuente_sensible", sec["fuente_sensible"]
    if nat not in sec:
        raise CampoFaltante("naturaleza_dato")  # sin secuencia para su naturaleza: no se puede degradar
    return nat, sec[nat]


def _ventana(c: Cifra) -> int:
    pa = c.periodo_agrupado
    if pa and len(pa) == 2:
        return int(pa[1]) - int(pa[0]) + 1
    return 1


def _paso_destino(nombre: str, c: Cifra) -> tuple[str | None, int | str]:
    """Paso de la secuencia → (nivel destino o None = mismo nivel, ventana en años o 'fija3')."""
    if nombre in ("anio",):
        return None, 1
    m = re.fullmatch(r"agrupar_(\d)_anios", nombre)
    if m:
        return None, int(m.group(1))
    m = re.fullmatch(r"(provincia|departamento)(?:_(anio|(\d)_anios|ventana_fija_3_anios))?", nombre)
    if m:
        if m.group(2) == "ventana_fija_3_anios":
            return m.group(1), "fija3"
        return m.group(1), int(m.group(3)) if m.group(3) else (1 if m.group(2) == "anio" else _ventana(c))
    return None, 0


def _ventanas_fijas(ctx: Contexto) -> list[tuple[int, int]]:
    """Ventanas fijas no superpuestas de 3 años (prioridad_secuencia; D-R4-1 = C): se leen del texto del parámetro."""
    txt = str(ctx.param("R-MOTOR-01", "prioridad_secuencia") or "")
    return [(int(a), int(b)) for a, b in re.findall(r"(\d{4})\s*[–-]\s*(\d{4})", txt)]


def _satisface_minimo(ctx: Contexto, nivel: str, minimo: str | None) -> bool:
    if not minimo:
        return True
    r, rm = rango(ctx, nivel), rango(ctx, minimo)
    if r is None or rm is None:
        return nivel == minimo
    if minimo == "departamento" and nivel in (LM, LR):
        return True  # R-ENC-06 (L1): el ámbito de Lima que contiene al territorio hace las veces del departamento
    return r >= rm


@regla("R-MOTOR-01")
def r_motor_01(c: Cifra, ctx: Contexto):
    """Como regla de cifra: registra la degradación ya hecha (motivo_nivel) y comprueba que sea monótona (el nivel y
    la ventana nunca retroceden; el dominio 8 no baja a departamento). La degradación la pide `siguiente_paso`."""
    rid = "R-MOTOR-01"
    pasos = list(c.motivo_nivel or [])
    if not pasos:
        return None
    mal = [p for p in pasos if not isinstance(p, dict) or not isinstance(p.get("paso") or {}, dict)]
    if mal:  # auditoría P2, A-7 (H-19): un paso que no tiene la forma del contrato no hace caer la regla
        return Resultado(rid, "revision_humana", "motivo_nivel_mal_formado", clausula="paso de degradación sin forma de dict",
                         detalle={"pasos": [str(p) for p in mal]})
    orig = c.cifra_original
    estados = []
    if orig is not None:
        o = orig if isinstance(orig, Cifra) else Cifra(dict(orig))  # la cifra original o su registro (dict)
        estados.append((o.nivel, _ventana(o)))
    nivel_prev = estados[0][0] if estados else None
    for p in pasos:  # cada paso registrado por el motor: {"paso": {...}, "motivos": [...]}
        q = (p or {}).get("paso") or {}
        nivel_prev = q.get("nivel") or nivel_prev
        a = q.get("anios")
        estados.append((nivel_prev, int(a[1]) - int(a[0]) + 1 if a else 1))
    if not estados or estados[-1] != (c.nivel, _ventana(c)):
        estados.append((c.nivel, _ventana(c)))
    claves = [(rango(ctx, n) or 0, v) for n, v in estados]
    monotona = all(b > a for a, b in zip(claves, claves[1:]))
    if any(n == AMLC for n, _ in estados) and any(n == "departamento" for n, _ in estados):
        monotona = False  # el dominio 8 no baja a departamento (9/10/2026)
    det = {"pasos": pasos, "nivel_original": estados[0][0], "nivel_publicado": c.nivel,
           "periodo_agrupado": c.periodo_agrupado}
    if not monotona:
        return Resultado(rid, "suprimir", "degradacion_no_monotona", clausula="secuencia no monótona", detalle=det)
    return Resultado(rid, "rotular", "degradada", clausula="cifra degradada: pasos registrados",
                     rotulo=c.territorio_nombre, detalle=det)


def siguiente_paso(c: Cifra, ev, ctx: Contexto) -> dict | None:
    """Siguiente paso de la secuencia de degradación (R-MOTOR-01) o None.

    Corresponde cuando la cifra quedó suprimida por un motivo degradable (y por ninguno no degradable) o cuando pidió
    agregar_nivel / agrupar_anios por un motivo degradable. Pasos (contrato §6): {"tipo": "nivel", "nivel", "territorio_id"},
    {"tipo": "agrupar", "anios": [desde, hasta]}, {"tipo": "nivel_agrupar", "nivel", "territorio_id", "anios"} o
    {"tipo": "respuesta_parcial"}
    (gasto). La secuencia es monótona: el estado (rango del nivel, ventana) solo avanza; se saltan los pasos que no
    cumplen el nivel mínimo pedido o que el cubo no tiene."""
    rid = "R-MOTOR-01"
    degradables = set(ctx.param(rid, "motivos_degradables") or [])
    no_degradables = set(ctx.param(rid, "no_degradables") or [])
    final = ev.accion_final
    if final not in ("suprimir", "agregar_nivel", "agrupar_anios"):
        return None
    pide = [r for r in ev.resultados if r.accion == final]
    if any(r.motivo in no_degradables or r.motivo not in degradables for r in pide if final == "suprimir"):
        return None
    pide = [r for r in pide if r.motivo in degradables]
    if not pide:
        return None
    # agregar_nivel_multiple (R-MOTOR-02): el nivel más grueso pedido
    minimos = [r.nivel_minimo for r in ev.resultados if r.nivel_minimo and r.accion in ("agregar_nivel", "suprimir")]
    minimo = max(minimos, key=lambda n: rango(ctx, n) or 0) if minimos else None
    if final == "agregar_nivel" and (minimo is None or _satisface_minimo(ctx, c.nivel, minimo)):
        return None  # ya está en el nivel pedido: no hay nada que degradar
    try:
        nombre_sec, sec = _secuencia(c, ctx)
    except CampoFaltante:
        return None
    anio = int(c.periodo_agrupado[1]) if c.periodo_agrupado else int(c.anio)
    actual = (rango(ctx, c.nivel) or 0, _ventana(c))
    disponibles = {int(x) for x in (c.anios_disponibles or [])}

    if nombre_sec == "presupuestal_financiero":
        if minimo and not _satisface_minimo(ctx, c.nivel, minimo):
            dest = contenedor(c, minimo, ctx)
            if dest:
                return {"tipo": "nivel", "nivel": dest[0], "territorio_id": dest[1], "paso": "nivel_atribuible"}
        if c.respuesta_parcial:
            return None
        return {"tipo": "respuesta_parcial", "paso": "respuesta_parcial"}

    for nombre in sec:
        if nombre in ("anio", "suprimir", "nivel_atribuible", "respuesta_parcial"):
            continue
        nivel_dest, ventana = _paso_destino(nombre, c)
        # dominio 8 (9/10/2026): no baja a departamento; sigue con agrupar años y después nacional
        if c.nivel == AMLC and nivel_dest == "departamento":
            nivel_dest = "nacional"
        if nivel_dest is None:
            nivel, terr = c.nivel, c.territorio_id
        else:
            dest = contenedor(c, nivel_dest, ctx)
            if dest is None:
                continue
            nivel, terr = dest
        if ventana == "fija3":
            fija = next(((a, b) for a, b in _ventanas_fijas(ctx) if a <= anio <= b), None)
            if fija is None:
                continue
            anios = list(fija)
            v = 3
        else:
            v = int(ventana)
            anios = [anio - v + 1, anio] if v > 1 else None
        nuevo = (rango(ctx, nivel) or 0, v)
        if nuevo <= actual:
            continue  # monótona: el nivel y la ventana nunca retroceden (orden lexicográfico nivel, ventana)
        if not _satisface_minimo(ctx, nivel, minimo):
            continue
        # años: todos los de la ventana deben existir (en el cubo para ese nivel y territorio, si el cubo está)
        hay = anios_en_cubo(ctx, c.indicador_id, nivel, terr, c.medida) if ctx.cubo is not None else disponibles
        necesarios = set(range(anios[0], anios[1] + 1)) if anios else {anio}
        if not necesarios <= hay:
            continue
        paso = {"paso": nombre, "secuencia": nombre_sec}
        if (nivel, terr) != (c.nivel, c.territorio_id):
            paso.update({"tipo": "nivel_agrupar" if anios else "nivel", "nivel": nivel, "territorio_id": str(terr)})
            if anios:
                paso["anios"] = anios
        else:
            paso.update({"tipo": "agrupar", "anios": anios})
        return paso
    return None  # secuencia agotada → la cifra queda suprimida (sin_datos con R-LENGUAJE-05)


# ======================================================================= R-MOTOR-02

_OBLIG_CACHE: dict = {}


def _obligatorios() -> dict[str, list[str]]:
    """Campos obligatorios de dim_indicador según src/pap/capa0/indicadores.py (OBLIGATORIOS y
    OBLIGATORIOS_ENCUESTA). Se leen del fuente con ast para no importar la capa 0 (dependencias de ingesta)."""
    if not _OBLIG_CACHE:
        fuente = Path(__file__).resolve().parents[2] / "capa0" / "indicadores.py"
        arbol = ast.parse(fuente.read_text(encoding="utf-8"))
        for nodo in arbol.body:
            if isinstance(nodo, ast.Assign) and len(nodo.targets) == 1 and isinstance(nodo.targets[0], ast.Name) \
                    and nodo.targets[0].id in ("OBLIGATORIOS", "OBLIGATORIOS_ENCUESTA"):
                _OBLIG_CACHE[nodo.targets[0].id] = ast.literal_eval(nodo.value)
    return _OBLIG_CACHE


def _vacio(v) -> bool:
    return v is None or (isinstance(v, float) and v != v) or (isinstance(v, str) and not v.strip()) or \
        (isinstance(v, (list, dict)) and not v)


@regla("R-MOTOR-02")
def r_motor_02(c: Cifra, ctx: Contexto):
    """Un metadato del indicador faltante nunca deja pasar la cifra: campos obligatorios de dim_indicador (los de
    indicadores.py: OBLIGATORIOS; en encuestas, OBLIGATORIOS_ENCUESTA y el diseño; en modeladas,
    validado_contra_oficial) → suprimir por metadato_faltante."""
    rid = "R-MOTOR-02"
    ob = _obligatorios()
    req = list(ob.get("OBLIGATORIOS", []))
    if c.naturaleza_dato == "encuesta_muestral":
        req += ob.get("OBLIGATORIOS_ENCUESTA", [])
    if c.naturaleza_dato == "estimacion_modelada":
        req.append("validado_contra_oficial")
    faltan = []
    for campo in req:
        clave = "indicador_id" if campo == "id" else campo
        v = c.get(clave)
        if isinstance(v, bool):
            continue
        if _vacio(v):
            faltan.append(campo)
    if c.naturaleza_dato == "encuesta_muestral":
        vd = c.variables_diseno or {}
        faltan += [f"variables_diseno.{k}" for k in ("factor", "estrato", "conglomerado") if _vacio(vd.get(k))]
        if _vacio((c.dominios_inferencia or {}).get("anual") if isinstance(c.dominios_inferencia, dict) else None):
            faltan.append("dominios_inferencia.anual")
    if faltan:
        return Resultado(rid, "suprimir", "metadato_faltante", clausula="campo requerido nulo y caso no definido",
                         detalle={"campos": faltan})
    return None
