"""S1-05 y S1-06 — Del texto de la persona a la respuesta: consulta mínima → resolver territorio → planificador →
`Motor.responder`, y los dos tipos de respuesta que no calculan cifras: `no_se_puede` y `aclaracion`.

`no_se_puede`: sale por las mismas capas que una respuesta con cifras (respuesta corta que dice primero lo que no se puede,
«Lo más cercano que sí tenemos» y el motivo en «Más contexto»), pero sin ninguna cifra: ni la suprimida ni otra, porque un
número solo entra al texto por marcador desde el cubo (R-LENGUAJE-03). El motivo se detecta (a) en el plan del planificador
(`motivos_no_se_puede`, S1-03) o (b) en el `estado_cifra` y la traza que dejó el validador (E-02, E-03, P-04), y se dice con los
códigos de R-LENGUAJE-05 (`motivos_codificados`, `max_alternativas`) más los que esa regla no trae (campo `regla: null` de
curados/motor/textos/no_se_puede.yaml). La alternativa («lo más cercano») solo se ofrece si el validador la deja publicar.

Respuesta parcial (R-LENGUAJE-05): si alguna cifra principal es publicable, se sigue respondiendo y se dice lo que falta.

Todo texto sale de curados/motor/textos/no_se_puede.yaml; los valores por defecto, de parametros_motor.yaml (`no_se_puede`).
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from . import capas as K
from . import plantillas
from .consulta import ConsultaInvalida, cargar
from .planificador import cargar_intenciones, planificar
from .territorio import Aclaracion, Resuelto, resolver
from .validador.reglas_etapa0 import contenedor
from .validador.reglas_etapa1_3 import nombre_territorio

NO_PUBLICABLE = ("suprimida", "sin_datos")


class EleccionInvalida(ValueError):
    """`--elegir` no corresponde a ninguna opción: el mensaje es para la persona."""


# ======================================================================= textos y parámetros

def _tx(motor) -> dict:
    return plantillas.textos(motor.ctx.raiz, "no_se_puede.yaml")


def _par(motor) -> dict:
    return plantillas.parametros(motor.ctx.raiz)["no_se_puede"]


def _fmt(texto: str, v: dict) -> str:
    return texto.format_map(v)


def oraciones(texto: str) -> list[str]:
    return [x for x in re.split(r"(?<=[.!?])\s+", (texto or "").strip()) if x]


def _publicable(c) -> bool:
    return c is not None and not c.get("sin_fila") and c.estado_cifra not in NO_PUBLICABLE


def _limpio(nombre) -> str:
    return re.sub(r"\s*\([^)]*\)", "", str(nombre)).strip()


# ======================================================================= qué motivo y de qué alcance

def motivos_del_plan(plan: dict) -> list[dict]:
    return list(plan.get("motivos_no_se_puede") or ([plan["no_se_puede"]] if plan.get("no_se_puede") else []))


def motivo_total(motor, plan: dict) -> dict | None:
    """El primer motivo del plan con alcance `total` (no hay respuesta posible), o None."""
    t = _tx(motor)["motivos"]
    return next((m for m in motivos_del_plan(plan) if t.get(m["motivo"], {}).get("alcance") == "total"), None)


def principales(cifras: dict) -> list:
    return [c for c in cifras.values() if c.rol == "principal"]


def ninguna_principal_publicable(cifras: dict):
    """Si hay cifras principales y ninguna es publicable (R-LENGUAJE-05: 0 publicables → no_se_puede), la primera; si no, None."""
    p = principales(cifras)
    return p[0] if p and not any(_publicable(c) for c in p) else None


def motivo_de_cifra(motor, c) -> str:
    """Motivo de «no se puede» de una cifra que el validador no dejó publicar, según su `estado_cifra` y su traza (nunca su valor)."""
    tx = _tx(motor)
    mv = tx["motivos_validador"]
    if c.get("sin_fila"):
        return mv["sin_fila"]
    ev = c.evaluacion
    motivos = list(ev.motivos()) if ev else []
    if not motivos:
        for paso in reversed(c.traza or []):
            motivos = paso.get("motivos") or motivos
            if motivos:
                break
    if not motivos and c.estado_cifra == "sin_datos":
        return mv["sin_datos"]
    cand = {mv[k] for k in motivos if k in mv}
    return next((k for k in tx["prioridad_motivos"] if k in cand), mv["defecto"])


# ======================================================================= variables de los textos

def _anios_txt(tx, anios: list[int]) -> str:
    a = sorted(int(x) for x in anios)
    t = tx["anios_lista"]
    if len(a) == 1:
        return t["uno"].format(anio=a[0])
    if a == list(range(a[0], a[-1] + 1)):
        return t["rango"].format(desde=a[0], hasta=a[-1])
    return t["lista"].format(lista=", ".join(map(str, a[:-1])) + f" {tx['conjuncion']} {a[-1]}")


def _anios_corto(tx, anios: list[int]) -> str:
    a = sorted(int(x) for x in anios)
    t = tx["anios_corto"]
    if len(a) == 1:
        return t["uno"].format(anio=a[0])
    if len(a) == 2:
        return t["dos"].format(a=a[0], b=a[1])
    return t["rango"].format(desde=a[0], hasta=a[-1]) if a == list(range(a[0], a[-1] + 1)) else _anios_txt(tx, a)


def _lista_temas(motor) -> str:
    tx = _tx(motor)
    voc = plantillas.parametros(motor.ctx.raiz)["temas"]["vocabulario"]["valor"]
    n = [tx["temas"][t] for t in voc]
    return n[0] if len(n) == 1 else ", ".join(n[:-1]) + f" {tx['conjuncion']} {n[-1]}"


def _vars(motor, plan: dict, detalle: dict | None = None) -> dict:
    tx = _tx(motor)
    d = detalle or {}
    terr = plan.get("territorio") or {}
    lugar = terr.get("nombre_pedido") or tx["lugar_desconocido"]
    comp = (plan.get("territorio_comparado") or {}).get("nombre_pedido") or tx["lugar_desconocido"]
    nivel = d.get("nivel_pedido") or terr.get("nivel")
    nv = tx["niveles"]
    v = {"tema": tx["temas"].get(plan.get("tema"), tx["tema_desconocido"]),
         "tema_art": tx["temas_art"].get(plan.get("tema"), tx["tema_desconocido"]), "lugar": lugar, "lugar2": comp,
         "en_lugar": tx["en_lugar"].format(lugar=terr["nombre_pedido"]) if terr.get("nombre_pedido") else "",
         "nivel_palabra_pedido": nv["palabra"].get(nivel, nv["palabra"]["defecto"]),
         "nivel_plural_pedido": nv["plural"].get(nivel, nv["plural"]["defecto"]),
         "nivel_palabra_alternativo": nv["palabra"].get(d.get("nivel_planificado"), nv["palabra"]["defecto"]),
         "dentro_de": d.get("dentro_de") or tx["lugar_desconocido"], "temas": _lista_temas(motor),
         "anio_pedido": d.get("anio_pedido", ""), "anio": d.get("anio", ""), "anios": ""}
    if d.get("anios_disponibles"):
        v["anios"] = _anios_txt(tx, d["anios_disponibles"])
    if d.get("anios_por_indicador"):                       # S1-09 (H7): un tema con varias formas de medir dice los años de cada una
        f = tx["formas_de_medir"]
        partes = [f[i].format(anios=_anios_corto(tx, a)) for i, a in d["anios_por_indicador"].items() if i in f]
        if partes:
            v["anios"] = f["conjuncion"].join(partes)
    v["parte"] = tx["partes"].get(plan.get("intencion"), tx["partes"]["nivel_actual"]).format_map(v)
    return v


def _nombre_cifra(motor, c) -> str:
    return _limpio(c.get("territorio_nombre") or nombre_territorio(motor.ctx, c.nivel, c.territorio_id))


# ======================================================================= alternativas («lo más cercano»)

def _lugar_consulta(nivel: str, tid: str) -> dict:
    if nivel == "nacional":
        return {"nacional": True}
    if nivel in ("LIMA_METROPOLITANA", "LIMA_REGION", "CALLAO", "AREA_METROPOLITANA_LIMA_CALLAO"):
        return {"ambito": nivel}
    return {"ubigeo": str(tid)}


def _spec_principal(plan: dict, indicador: str | None = None) -> dict | None:
    ps = [s for s in plan.get("cifras") or [] if s.get("rol") == "principal"]
    return next((s for s in ps if indicador in (None, s["indicador"])), ps[0] if ps else None)


def _evaluar_spec(motor, plan: dict, spec: dict, **cambios):
    """La cifra de ese spec (sin la prueba de cambio) pasada por el validador, o None si el cubo no la tiene."""
    s = {k: v for k, v in spec.items() if k != "comparar_con"}
    s.update(id="alternativa", rol="principal", **cambios)
    s.pop("nivel_pedido", None)
    # la alternativa se pide por su propio lugar y nivel: sin el nombre que escribió la persona (R-TERRITORIO-09 lo volvería a resolver)
    c = motor.cifra(s, {**plan, "territorio": {"nivel": s["nivel"], "id": s["territorio"], "nombre_pedido": None}})
    return None if c is None or c.get("sin_fila") else motor.evaluar(c)


def _alt_de_cifra(motor, c, tx: dict) -> dict:
    nombre = _nombre_cifra(motor, c)
    texto = tx["territorio_alternativo"].get(c.nivel, tx["territorio_alternativo"]["defecto"]).format(nombre=nombre)
    return {"tipo": "nivel", "nivel": c.nivel, "territorio_id": str(c.territorio_id), "nombre": nombre, "anio": int(c.anio),
            "texto": texto, "lugar": _lugar_consulta(c.nivel, c.territorio_id)}


def _subir(motor, plan: dict, c, tx: dict) -> dict | None:
    """El nivel superior más cercano donde el indicador es válido y el validador deja publicar la cifra
    (`no_se_puede.nivel_alternativo`: superior_inmediato; R-REG-02)."""
    esc = cargar_intenciones(motor.ctx.raiz)["escalera_niveles"]
    pasos = esc["valor"]
    validos = {x["nivel"] for x in motor.ctx.indicadores[c.indicador_id].get("niveles_validos") or []}
    propio = c.nivel if c.nivel in pasos else esc["ambito_en"]
    spec = {"indicador": c.indicador_id, "anio": int(c.anio), "medida": c.get("medida")}
    for dest in pasos[pasos.index(propio) + 1:]:
        d = contenedor(c, dest, motor.ctx)
        if d is None or d[0] not in validos:
            continue
        c2 = _evaluar_spec(motor, plan, spec, nivel=d[0], territorio=d[1])
        if _publicable(c2):
            return _alt_de_cifra(motor, c2, tx)
    return None


def _origenes(motor, ubigeo: str) -> list[tuple[str, bool]]:
    if getattr(motor.ctx, "_rel_origen", None) is None:
        import duckdb
        ruta = motor.ctx.raiz / "biblioteca" / "dimensiones" / "rel_ubigeo_origen.parquet"
        filas = duckdb.connect().execute(
            "SELECT ubigeo_hijo, ubigeo_origen, es_origen_principal FROM read_parquet(?)", [str(ruta)]).fetchall() if ruta.exists() else []
        motor.ctx._rel_origen = filas
    return [(str(o), bool(p)) for h, o, p in motor.ctx._rel_origen if str(h) == str(ubigeo)]


def _alternativas(motor, plan: dict, codigo: str, detalle: dict, cifra_base=None) -> tuple[str, dict, list[dict]]:
    """(clave del texto «cercano», variables extra, alternativas). Una alternativa solo se ofrece si existe y el validador la
    deja publicar; si no hay, la clave es «ninguna». Como máximo `max_alternativas` de R-LENGUAJE-05."""
    tx = _tx(motor)
    tope = int(motor.ctx.param("R-LENGUAJE-05", "max_alternativas") or 2)
    ind = detalle.get("indicador")

    def uno(clave, alt, **extra):
        return (clave, {"alternativa": alt["texto"], **extra}, [alt]) if alt else ("ninguna", {}, [])

    if codigo == "tema_fuera_del_piloto":
        return "temas", {}, []                 # la lista de temas disponibles no es una alternativa: va en `temas_disponibles`
    if codigo == "anio_sin_datos":
        spec = _spec_principal(plan, ind)
        pedido = int(detalle["anio_pedido"])
        alt = _evolucion_hasta(motor, plan, detalle, pedido)
        if alt:                                # S1-15 (H7, E-06): el año solo está con otra forma de medir, en la evolución
            return "evolucion_hasta", {}, [alt]
        disp = sorted(int(a) for a in detalle["anios_disponibles"])
        orden = [y for y in reversed(disp) if y < pedido] + [y for y in reversed(disp) if y > pedido]   # anio_mas_cercano: anterior_primero; sin anterior, el último
        for y in orden if spec else []:
            c = _evaluar_spec(motor, plan, spec, anio=y)
            if _publicable(c):
                alt = {"tipo": "anio", "anio": y, "nivel": c.nivel, "territorio_id": str(c.territorio_id), "nombre": _nombre_cifra(motor, c),
                       "texto": str(y), "lugar": _lugar_consulta(c.nivel, c.territorio_id)}
                return "anio", {"anio": y, "lugar": alt["nombre"]}, [alt]
        return "ninguna", {}, []
    if codigo == "serie_un_solo_anio":
        spec = _spec_principal(plan, ind)
        c = _evaluar_spec(motor, plan, spec) if spec else None
        if not _publicable(c):
            return "ninguna", {}, []
        alt = {"tipo": "anio", "anio": int(c.anio), "nivel": c.nivel, "territorio_id": str(c.territorio_id),
               "nombre": _nombre_cifra(motor, c), "texto": str(int(c.anio)), "lugar": _lugar_consulta(c.nivel, c.territorio_id)}
        ultimo = max(int(a) for a in motor.ctx.indicadores[c.indicador_id]["anios_disponibles"])
        clave = "anio" if int(c.anio) == ultimo else "anio_hasta"     # S1-13 (N-2): «la más reciente» solo del último año
        return clave, {"anio": alt["anio"], "lugar": alt["nombre"]}, [alt]
    if codigo == "nivel_no_valido":
        if plan.get("intencion") == "identificar_extremo":
            if not detalle.get("nivel_planificado"):
                return "ninguna", {}, []
            return "extremo", {}, [{"tipo": "extremo", "nivel": detalle["nivel_planificado"], "nombre": detalle["nivel_planificado"],
                                    "texto": detalle["nivel_planificado"]}]
        spec = _spec_principal(plan)
        c = _evaluar_spec(motor, plan, spec) if spec and detalle.get("nivel_planificado") else None
        if c is None:
            return "ninguna", {}, []
        return uno("nivel", _alt_de_cifra(motor, c, tx) if _publicable(c) else _subir(motor, plan, c, tx))
    if codigo == "distrito_creado_despues":
        spec = _spec_principal(plan, ind)
        if spec is None:
            return "ninguna", {}, []
        encontrados = []
        origenes = _origenes(motor, detalle["ubigeo"])
        principales_ = [o for o, p in origenes if p] or ([origenes[0][0]] if len(origenes) == 1 else [])
        if len(principales_) == 1:
            c = _evaluar_spec(motor, plan, spec, nivel="distrito", territorio=principales_[0])
            if _publicable(c):
                a = _alt_de_cifra(motor, c, tx)
                a.update(tipo="origen", texto=motor.nombre_completo(principales_[0]))
                encontrados.append(a)
        if "provincia" in {x["nivel"] for x in motor.ctx.indicadores[spec["indicador"]].get("niveles_validos") or []}:
            c = _evaluar_spec(motor, plan, spec, nivel="provincia", territorio=str(detalle["ubigeo"])[:4] + "00")
            if _publicable(c):
                encontrados.append({**_alt_de_cifra(motor, c, tx), "tipo": "provincia"})
        encontrados = encontrados[:tope]
        claves = tuple(a["tipo"] for a in encontrados)
        clave = {("origen",): "origen", ("provincia",): "provincia", ("origen", "provincia"): "origen_y_provincia"}.get(claves, "ninguna")
        extra = {"alternativa": encontrados[0]["texto"]} if encontrados else {}
        if len(encontrados) > 1:
            extra["alternativa2"] = encontrados[1]["texto"]
        return clave, extra, encontrados
    if codigo == "intencion_no_soportada":
        return "lugar", {}, [{"tipo": "lugar", "texto": ""}]
    if codigo == "extremo_dentro_de_no_soportado":
        cm = copy.deepcopy(plan.get("consulta_minima") or {})
        if cm:
            cm["territorio"] = {k: v for k, v in cm["territorio"].items() if k != "dentro_de"}
            try:
                if not planificar(cm, None, motor)["motivos_no_se_puede"]:
                    return "pais", {}, [{"tipo": "pais", "texto": "", "consulta_minima": cm}]
            except (TypeError, KeyError):
                pass
        return "ninguna", {}, []
    # cifra suprimida o sin registros: lo más cercano es el nivel superior que el validador deja publicar
    if cifra_base is not None:
        return uno("nivel", _subir(motor, plan, cifra_base, tx))
    return "ninguna", {}, []


def _evolucion_hasta(motor, plan: dict, detalle: dict, pedido: int) -> dict | None:
    """S1-15 (H7): el año pedido no está en la forma de medir vigente pero sí en otra del mismo tema (`anios_por_indicador`).
    E-06 manda que «¿cuánta hay?» muestre solo la vigente; la otra se ve al preguntar cómo cambió. Se ofrece esa evolución
    hasta el año pedido, solo si se puede responder (S1-13, A-H6)."""
    otras = [i for i, a in (detalle.get("anios_por_indicador") or {}).items() if i != detalle.get("indicador") and pedido in a]
    cm = copy.deepcopy(plan.get("consulta_minima") or {})
    if not otras or not cm:
        return None
    cm.update(intencion="evolucion", periodo={"tipo": "serie", "hasta": pedido})
    try:
        p = preguntar_minima(motor, cm, solo_plan=True)
    except (ConsultaInvalida, TypeError, KeyError):
        return None
    p = p.get("plan", p)
    if p.get("aclaracion") or p.get("motivos_no_se_puede"):
        return None
    return {"tipo": "evolucion", "anio": pedido, "texto": str(pedido), "consulta_minima": cm}


# ======================================================================= respuesta «no se puede»

def respuesta_no_se_puede(motor, plan: dict, motivo: dict | str, *, cifras: dict | None = None, cifra_base=None) -> dict:
    """La respuesta de «no se puede» por las mismas capas (sin cifras). `motivo`: el dict del plan ({motivo, …}) o el código."""
    from . import ficha as F
    tx = _tx(motor)
    maxo = int(_par(motor)["respuesta_corta_max_oraciones"]["valor"])
    detalle = motivo if isinstance(motivo, dict) else {"motivo": motivo}
    codigo = detalle["motivo"]
    m = tx["motivos"][codigo]
    if cifra_base is None and cifras:
        cifra_base = next((c for c in principales(cifras) if not _publicable(c)), None)
    if cifra_base is not None:
        detalle = {**detalle, "anio": int(cifra_base.anio), "indicador": cifra_base.indicador_id}
    clave, extra, alternativas = _alternativas(motor, plan, codigo, detalle, cifra_base)
    v = {**_vars(motor, plan, detalle), **extra}
    if cifra_base is not None:
        v["lugar"] = _nombre_cifra(motor, cifra_base)
    if "tema" in v and v["tema"] == tx["tema_desconocido"] and cifra_base is not None:
        tid = motor.ctx.indicadores[cifra_base.indicador_id].get("tema")
        v["tema"], v["tema_art"] = tx["temas"].get(tid, v["tema"]), tx["temas_art"].get(tid, v["tema_art"])
    corta_txt = m["corta_formas"] if detalle.get("anios_por_indicador") and m.get("corta_formas") else m["corta"]   # S1-09 (H7): sin contradecir la forma anterior
    if codigo == "anio_sin_datos" and detalle.get("anios_por_indicador"):          # S1-15 (H7)
        en_alguna = any(int(detalle["anio_pedido"]) in a for a in detalle["anios_por_indicador"].values())
        corta_txt = m["corta_forma_anterior"] if clave == "evolucion_hasta" else corta_txt if en_alguna else m["corta_ninguna_forma"]
    corta = " ".join(oraciones(_fmt(corta_txt, v))[:maxo])
    cercano = _fmt(m["cercano"][clave], v)
    texto_motivo = _fmt(m["motivo"], v)
    lugar_ficha = ((plan.get("territorio") or {}).get("nombre_pedido") or (v["lugar"] if cifra_base is not None else None)
                   or detalle.get("dentro_de"))
    ficha_txt = {"datos": tx["ficha"]["datos"],
                 "territorio": tx["ficha"]["territorio"].format(lugar=lugar_ficha) if lugar_ficha else tx["ficha"]["territorio_sin_lugar"],
                 "no_concluir": tx["ficha"]["no_concluir"].format(tema=v["tema"])}
    borrador = {"corta": [corta], "clave": {"ids": [], "valor": "", "texto": ""}, "ojo": [],
                "contexto": [{"titulo": tx["titulos"]["motivo"], "texto": texto_motivo, "etiqueta": None}],
                "cifras_usadas": [], "verbos": {}, "universos": {}, "protegidos": {}, "entidades": {}, "glosario": [],
                "tema": None, "nc": [], "nivel_respuesta": None, "territorio_nombre": lugar_ficha or "",
                "respuesta_parcial": False, "opciones": {}, "sin_cifras": ficha_txt,
                "texto": " ".join([corta, cercano, texto_motivo])}
    consulta = {**plan, "pregunta": plan.get("pregunta") or "", "intencion": plan.get("intencion") or "nivel_actual",
                "territorio": plan.get("territorio") or {"nivel": "nacional", "id": None, "nombre_pedido": None}}
    r, res = motor._validar(consulta, borrador, {})
    sem_r = next(((x.detalle or {}) for x in res if x.regla == "R-CRUCES-10"), {})
    avisos = motor._avisos(res, borrador)
    capas = K.construir(motor, consulta, borrador, {}, {"corta": r.ficha["corta_texto"]}, sem_r.get("semaforo_respuesta"), avisos)
    if not capas["capa3"]["para_citar"]:
        capas["capa3"]["para_citar"] = [tx["sin_citas"]]                 # S1-09 (H16): sin cifras no hay qué citar, y se dice
        capas["capa3"]["citas"] = [{"texto": tx["sin_citas"], "url": "", "id_cifra": None}]
    capas["capa1"]["lo_mas_cercano"] = {"titulo": tx["titulos"]["lo_mas_cercano"], "texto": cercano}
    capas["capa1"]["palabras"] += K.palabras(cercano)
    no_pub = [{"id": c.id_cifra if c.get("id_cifra") else k, "indicador": c.indicador_id, "anio": int(c.anio), "nivel": c.nivel,
               "territorio": str(c.territorio_id), "estado": c.estado_cifra, "motivo": motivo_de_cifra(motor, c)}
              for k, c in (cifras or {}).items() if c.rol == "principal" and not _publicable(c)]
    otros = [x for x in motivos_del_plan(plan) if x is not detalle and x.get("motivo") != codigo]
    voc = plantillas.parametros(motor.ctx.raiz)["temas"]["vocabulario"]["valor"]
    temas = [{"tema": t, "nombre": tx["temas"][t]} for t in voc] if codigo == "tema_fuera_del_piloto" else []
    return {"tipo": "no_se_puede", "capas": capas, "temas_disponibles": temas, "consulta": plan, "version_biblioteca": motor.version(),
            "motivo": {"codigo": codigo, "regla_lenguaje_05": m.get("regla"), "detalle": detalle, "otros": otros},
            "alternativas": alternativas, "cifras": {}, "cifras_no_publicadas": no_pub, "cruces": [],
            "semaforo_respuesta": sem_r.get("semaforo_respuesta"), "motivos_semaforo_respuesta": sem_r.get("motivos"),
            "texto": " ".join([corta, cercano, texto_motivo]), "texto_con_marcadores": borrador["texto"],
            "ficha": {"corta": r.ficha["corta_texto"], "larga": r.ficha["larga"]}, "comparaciones_bloqueadas": [],
            "avisos_al_usuario": [{k: x for k, x in a.items() if k != "detalle"} for a in avisos],
            "resultados_respuesta": [x.a_dict() for x in res],
            "corrector": [x.a_dict() for x in res if x.regla in ("R-LENGUAJE-02", "R-LENGUAJE-03", "R-LENGUAJE-06", "R-GASTO-15")],
            "respuesta_parcial": False}


# ======================================================================= respuesta parcial (R-LENGUAJE-05)

def partes_faltantes(motor, plan: dict, cifras: dict) -> list[dict]:
    """Lo que falta en una respuesta que sí se da: los motivos de alcance `parcial` del plan y las cifras principales que el
    validador no dejó publicar mientras otra principal sí. Cada parte: {corta, motivo}."""
    tx = _tx(motor)
    t = tx["motivos"]
    out = []
    for m in motivos_del_plan(plan):
        s = t.get(m["motivo"], {})
        if s.get("alcance") == "parcial":
            out.append({"motivo": m["motivo"], "corta": _fmt(s["parcial"], _vars(motor, plan, m)), "explicacion": _fmt(s["motivo"], _vars(motor, plan, m))})
    ps = principales(cifras)
    if any(_publicable(c) for c in ps):
        bl = plantillas.textos(motor.ctx.raiz, "bloques.yaml")["indicadores"]
        for c in ps:
            if _publicable(c):
                continue
            cod = motivo_de_cifra(motor, c)
            s = t[cod]
            v = {**_vars(motor, plan), "sujeto": (bl.get(c.indicador_id) or {}).get("sujeto_corto") or str(c.nombre_ciudadano).lower(),
                 "lugar": _nombre_cifra(motor, c), "anio": int(c.anio), "parte": ""}
            out.append({"motivo": cod, "corta": _fmt(s["parcial"], v), "explicacion": _fmt(s["motivo"], v)})
    vistos, unicos = set(), []
    for p in out:
        if p["corta"] not in vistos:
            vistos.add(p["corta"])
            unicos.append(p)
    return unicos


def con_partes_faltantes(motor, borrador: dict, partes: list[dict]) -> dict:
    """Dice primero lo que falta (contrato de respuesta, regla 1) y deja el motivo en «Más contexto»; la respuesta queda parcial."""
    tx = _tx(motor)
    borrador["corta"] = [p["corta"] for p in partes] + list(borrador["corta"])
    borrador["contexto"] = list(borrador["contexto"]) + [
        {"titulo": tx["titulos"]["parte_faltante"], "texto": " ".join(dict.fromkeys(p["explicacion"] for p in partes)), "etiqueta": None}]
    borrador["respuesta_parcial"] = True
    borrador["texto"] = plantillas._armar(borrador)["texto"]
    return borrador


# ======================================================================= avisos de periodo (S1-09, A-H1 y A-H2)

def avisos_de_periodo(motor, plan: dict) -> list[str]:
    """Las fechas pedidas (o el inicio de la serie) que no se pudieron respetar por un quiebre, dichas con el año y la razón."""
    tx = _tx(motor)["avisos_periodo"]
    out = []
    for a in plan.get("avisos_periodo") or []:
        razon = tx["razon"].get(a["tipo_quiebre"], tx["razon"]["defecto"]).format_map(a)
        if a["aviso"] == "desde_no_comparable":
            t = tx["desde_no_comparable"]["pedido" if a["pedido"] else "inicial"]
        else:
            t = tx[a["aviso"]]
        out.append(t.format_map({**a, "razon": razon}))
    return list(dict.fromkeys(out))


def con_aviso_periodo(borrador: dict, avisos: list[str]) -> dict:
    """Dice primero lo que no se pudo respetar de las fechas pedidas. No vuelve parcial la respuesta: las cifras que se
    muestran son las que se pidieron, y el semáforo no cambia."""
    borrador["corta"] = list(avisos) + list(borrador["corta"])
    borrador["texto"] = plantillas._armar(borrador)["texto"]
    return borrador


# ======================================================================= aclaración

def _aclaracion_dict(a: Aclaracion) -> dict:
    d = a.a_dict()
    d["opciones"] = [{"n": i, **o} for i, o in enumerate(d["opciones"], 1)]
    return d


def texto_aclaracion(motor, a: dict) -> str:
    tx = _tx(motor)["aclaraciones"]
    lineas = [a["pregunta"]] + [tx["opcion_numero"].format(n=o["n"], etiqueta=o["etiqueta"]) for o in a["opciones"]]
    return "\n".join(lineas if a["opciones"] else lineas + [tx["sin_opciones"]])


def respuesta_aclaracion(motor, plan: dict) -> dict:
    """Aclaración (S1-02 o consulta incompleta): la pregunta y sus opciones numeradas. No calcula ninguna cifra."""
    a = plan["aclaracion"]
    return {"tipo": "aclaracion", "consulta": plan, "version_biblioteca": motor.version(), "aclaracion": a, "cifras": {},
            "texto": texto_aclaracion(motor, a)}


def _aclaracion_tema(motor) -> dict:
    tx = _tx(motor)
    voc = plantillas.parametros(motor.ctx.raiz)["temas"]["vocabulario"]["valor"]
    ops = sorted(({"etiqueta": tx["temas"][t][:1].upper() + tx["temas"][t][1:], "tema": t} for t in voc),
                 key=lambda o: o["etiqueta"].lower())                    # orden neutro: alfabético (R-04)
    return {"motivo": "falta_tema", "pregunta": tx["aclaraciones"]["falta_tema"]["pregunta"],
            "opciones": [{"n": i, **o} for i, o in enumerate(ops, 1)], "por_defecto": None}


def _elegir(motor, a: dict, n: int) -> dict:
    tx = _tx(motor)["mensajes"]
    if not a["opciones"]:
        raise EleccionInvalida(tx["elegir_sin_opciones"])
    if not 1 <= int(n) <= len(a["opciones"]):
        raise EleccionInvalida(tx["elegir_fuera_de_rango"].format(n=n, total=len(a["opciones"])))
    return a["opciones"][int(n) - 1]


def _numeros(elegir) -> list[int]:
    """`elegir`: None, un número o varios (S1-09, H3: uno por cada lugar que tenga opciones, en el orden en que se piden)."""
    if elegir is None:
        return []
    return [int(x) for x in elegir] if isinstance(elegir, (list, tuple)) else [int(elegir)]


def _plan_aparte(cm: dict | None, dato: dict, **claves) -> dict:
    base = {"id": claves.pop("id"), "pregunta": (cm or dato).get("pregunta_original") or "", "intencion": (cm or dato).get("intencion"),
            "tema": None, "territorio": None, "periodo": None, "cifras": [], "grupos": []}
    base.update(claves)
    base["consulta_minima"] = cm or dato
    return base


# ======================================================================= camino completo

def _resolver(motor, cm: dict, elegir):
    """(territorios resueltos del plan o None, aclaración pendiente o None, números de `elegir` que sobran, los lugares que salieron
    de una aclaración). Cada aclaración usa el siguiente número de `elegir`; sin número, se devuelve la aclaración."""
    t = cm["territorio"]
    if cm["intencion"] == "identificar_extremo":
        piezas = [t["dentro_de"]] if t.get("dentro_de") else []
    else:
        piezas = [t] + ([cm["comparar_con"]] if cm.get("comparar_con") else [])
    out, elegidos = [], []
    numeros = _numeros(elegir)
    for p in piezas:
        r = resolver(p, motor.ctx)
        if isinstance(r, Aclaracion):
            a = _aclaracion_dict(r)
            if not numeros:
                return None, a, numeros, elegidos
            n, numeros = numeros[0], numeros[1:]
            _elegir(motor, a, n)                                               # valida el número
            r = r.opciones[n - 1]["territorio"]
            elegidos.append(r)
        out.append(r)
    if cm["intencion"] == "identificar_extremo":
        return (out[0] if out else None), None, numeros, elegidos
    return (out if len(out) > 1 else out[0]), None, numeros, elegidos


def preguntar_minima(motor, entrada, *, elegir: int | None = None, solo_plan: bool = False) -> dict:
    """Responde una consulta mínima (dict o ruta a un JSON). Devuelve la respuesta (`tipo`: respuesta | no_se_puede) o la
    aclaración pendiente (`tipo`: aclaracion). `elegir`: número (desde 1) de la opción de la aclaración, para responderla sin
    modo interactivo; una lista de números responde una aclaración por lugar, en orden (comparaciones con dos lugares ambiguos). `solo_plan`: devuelve `{"tipo": "plan", "plan": …}` sin calcular nada (las aclaraciones se devuelven igual).
    Lanza ConsultaInvalida (mensajes en lenguaje sencillo, S1-01) y EleccionInvalida."""
    raiz = motor.ctx.raiz
    numeros_escritos = _numeros(elegir)
    dato = json.loads(Path(entrada).read_text(encoding="utf-8")) if isinstance(entrada, (str, Path)) else copy.deepcopy(entrada)
    try:
        cm = cargar(dato, raiz)
    except ConsultaInvalida as e:
        if e.codigos == ["tema_invalido"] and isinstance(dato, dict):         # tema fuera del piloto: se dice con la lista de temas
            plan = _plan_aparte(None, dato, id="no_se_puede__tema_fuera_del_piloto",
                                no_se_puede={"motivo": "tema_fuera_del_piloto", "tema_pedido": str(dato.get("tema"))},
                                motivos_no_se_puede=[{"motivo": "tema_fuera_del_piloto", "tema_pedido": str(dato.get("tema"))}])
            return _con_entrada({"tipo": "plan"} if solo_plan else motor.responder(plan), dato, plan)
        if e.codigos != ["tema_o_indicador"] or not isinstance(dato, dict):
            raise
        a = _aclaracion_tema(motor)                                            # consulta incompleta: se pregunta el tema
        numeros = _numeros(elegir)
        if not numeros:
            plan = _plan_aparte(None, dato, id="aclaracion__falta_tema", aclaracion=a)
            return _con_entrada(motor.responder(plan), dato, plan)
        dato = {**dato, "tema": _elegir(motor, a, numeros[0])["tema"]}
        elegir = numeros[1:]
        cm = cargar(dato, raiz)
    resuelto, aclaracion, sobran, elegidos = _resolver(motor, cm, elegir)
    if aclaracion is not None:
        plan = _plan_aparte(cm, dato, id=f"aclaracion__{aclaracion['motivo']}", aclaracion=aclaracion)
        return _con_entrada(motor.responder(plan), cm, plan)
    if sobran:                                                                 # S1-09 (N-1): un número que no se usa no se descarta en silencio
        msgs = plantillas.textos(raiz, "cli.yaml")["mensajes"]
        hay = len(numeros_escritos) - len(sobran)
        raise EleccionInvalida(msgs["elegir_de_mas_ninguna" if hay == 0 else "elegir_de_mas_una" if hay == 1 else "elegir_de_mas"]
                               .format(escritos=len(numeros_escritos), hay=hay))
    plan = planificar(cm, resuelto, motor)
    plan["consulta_minima"] = cm
    # S1-09 (H4): el lugar que la persona eligió entre homónimos conserva su nombre con provincia y departamento
    plan["desambiguados"] = {f"{r.nivel}:{r.id}": r.nombre_completo for r in elegidos if r.nivel in ("provincia", "distrito")}
    return _con_entrada({"tipo": "plan"} if solo_plan else motor.responder(plan), cm, plan)


def _con_entrada(res: dict, cm: dict, plan: dict) -> dict:
    """El JSON de salida lleva la consulta mínima, el plan generado y (ya traía) la versión de la biblioteca."""
    return {**res, "consulta_minima": cm, "plan": plan}
