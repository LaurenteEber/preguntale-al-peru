"""Ficha de límites (R-LENGUAJE-01): se genera por plantilla desde la salida del validador, nunca se redacta a mano.
Corta (máx. 4 líneas): confianza, fuentes, territorio y «no permite concluir» (códigos NC fijos de ficha_limites).
Larga: una sección por cifra principal y por cruce (secciones 1–8 de reglas.json → ficha_limites.larga)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from ..config import encontrar_raiz
from . import formato as fmt
from . import plantillas

FUENTE = {"INEI-ENDES": ("ENDES", "INEI", "una encuesta a una muestra de hogares"),
          "INEI-ENAHO": ("ENAHO", "INEI", "una encuesta a una muestra de hogares"),
          "INS-CENAN-SIEN": ("SIEN", "INS", "un registro de los niños atendidos en establecimientos de salud"),
          "MEF-DA-PRESUPUESTO-EJECUCION-GASTO": ("Gasto MEF", "MEF", "el gasto registrado por las entidades públicas"),
          "INEI-MAPA-POBREZA": ("Mapa de Pobreza", "INEI", "una estimación del INEI con un modelo")}
NIVEL_TXT = {"departamento": "departamento", "provincia": "provincia", "distrito": "distrito", "nacional": "país",
             "establecimiento": "establecimiento", "LIMA_METROPOLITANA": "Lima Metropolitana",
             "LIMA_REGION": "Lima Región", "CALLAO": "Callao"}


def _codigos(ctx) -> dict:
    sec = next(s for s in ctx.ficha["larga"]["secciones"] if s.get("codigos_no_concluir"))
    return sec["codigos_no_concluir"]


def _nc_texto(ctx, codigo: str, params: dict) -> str:
    t = _codigos(ctx)[codigo]
    if "{si choque" in t:
        t = t.replace("{si choque: ', antes de la pandemia'}", ", antes de la pandemia" if params.get("choque") else "")
    for k, v in params.items():
        t = t.replace("{" + k + "}", str(v))
    return t


def _fuentes(cifras) -> str:
    por = {}
    for c in cifras:
        sig, ent, _ = FUENTE.get(c.fuente_principal, (c.fuente_principal, "", ""))
        por.setdefault((sig, ent), set()).add(int(c.anio))
        if c.comparacion and c.comparacion.get("anio") is not None and not c.comparacion_bloqueada:
            por[(sig, ent)].add(int(c.comparacion["anio"]))
    partes = []
    for (sig, ent), anios in por.items():
        a = sorted(anios)
        per = str(a[0]) if a[0] == a[-1] else f"{a[0]}–{a[-1]}"
        partes.append(f"{sig} {per} (devengado)" if sig == "Gasto MEF" else f"{sig} {per} ({ent})")
    return " · ".join(partes)


def generar(motor, consulta, r, borrador, sem_r, res) -> dict:
    ctx = motor.ctx
    rot = ctx.param("R-CRUCES-09", "rotulos")
    sem = sem_r.get("semaforo_respuesta")
    cifras = list(r.cifras)
    principales = [c for c in cifras if c.rol == "principal" and c.estado_cifra not in ("suprimida", "sin_datos")]
    # motivo de la confianza: el de la peor cifra principal (R-CRUCES-09) o, si un piso ámbar subió la respuesta, ese piso
    peor = next((c for c in principales if c.semaforo_cifra == sem), principales[0] if principales else None)
    pisos = {"respuesta_parcial": "la respuesta es parcial", "nivel_distinto_al_pedido": "respondimos para un territorio "
             "más grande que el pedido", "coeficiente_asociacion": "incluye una asociación entre territorios"}
    piso = next((pisos[m] for m in (sem_r.get("motivos") or []) if m in pisos), None)
    if sem == "verde" and peor is not None:
        motivo = ctx.param("R-CRUCES-09", "motivo_verde").replace("{anio}", str(peor.anio)).rstrip(".")
    elif peor is not None and peor.semaforo_cifra == sem and peor.evaluacion:
        m = next((x.mensaje for x in peor.evaluacion.resultados if x.regla == "R-CRUCES-09"), "") or ""
        motivo = (m.split(":", 1)[1].strip() if ":" in m else m) or piso or ""
    else:
        motivo = piso or ""
    rotulo = rot.get(sem, "Sin cifra disponible") if sem != "sin_cifra" else "Sin cifra disponible"
    motivo = (motivo[0].lower() + motivo[1:]) if motivo else motivo
    # contrato de respuesta (12/10/2026): sin colores; el nivel habla de los datos, no de la situación
    nivel_conf = {"verde": "alta", "ambar": "media", "rojo": "baja"}.get(sem)
    cab = f"Confianza en los datos: {nivel_conf} ({rotulo[0].lower() + rotulo[1:]})" if nivel_conf else f"Confianza: {rotulo}"
    l1 = f"{cab}: {motivo}." if motivo else f"{cab}."
    l2 = f"Datos de: {_fuentes(cifras)}"
    nivel_resp = borrador.get("nivel_respuesta") or (principales[0].nivel if principales else None)
    nombre = borrador.get("territorio_nombre", "")
    if principales:                                 # S1-09 (H4): el homónimo que la persona aclaró se nombra con provincia y departamento
        nombre = (consulta.get("desambiguados") or {}).get(f"{principales[0].nivel}:{principales[0].territorio_id}", nombre)
    if borrador.get("territorio_ficha"):
        l3 = f"Territorio: {borrador['territorio_ficha']}"
    else:
        if nivel_resp == "nacional":                # A-H7: no «país de Perú»
            l3 = "Territorio: " + plantillas.textos(ctx.raiz, "plantillas/comunes.yaml")["lugar_ficha"]["nacional"]
        else:
            l3 = f"Territorio: {NIVEL_TXT.get(nivel_resp, nivel_resp)} de {nombre}" if nivel_resp not in (
                "LIMA_METROPOLITANA", "LIMA_REGION", "CALLAO") else f"Territorio: {NIVEL_TXT[nivel_resp]}"
        pedido = consulta["territorio"]["nivel"]
        otros = sorted({NIVEL_TXT.get(c.nivel, c.nivel) for c in cifras if c.nivel != pedido and c.nivel != "establecimiento"})
        if otros:
            l3 += f" (algunas cifras solo están por {', '.join(otros)})"
    prio = next(s for s in ctx.ficha["larga"]["secciones"] if s.get("codigos_no_concluir")).get("prioridad_codigos") or []
    ncs = sorted(borrador.get("nc") or [], key=lambda x: prio.index(x[0]) if x[0] in prio else len(prio))
    nc_txt = [_nc_texto(ctx, cod, prm) for cod, prm in ncs[:2]]
    l4 = "No permite concluir: " + " ".join((t[0].lower() + t[1:]) if i == 0 else t for i, t in enumerate(nc_txt))
    if not cifras and borrador.get("sin_cifras"):   # S1-05: una respuesta de «no se puede» no tiene cifras ni fuentes que citar
        sc = borrador["sin_cifras"]
        l2, l3, l4 = sc["datos"], sc["territorio"], sc["no_concluir"]
    corta = {"semaforo_respuesta": l1, "fuentes_anios": l2, "territorio": l3, "no_concluir_principal": [c for c, _ in ncs[:2]]}
    larga = {"cifras": {}, "cruces": {}, "no_concluir": [_nc_texto(ctx, c, p) for c, p in ncs],
             "reproducibilidad": (f"Cálculo con el cubo {motor.version()['cubo'][:19]}… (commit {motor.version()['commit_cubo']}) "
                                  f"y reglas {motor.version()['reglas']}. Indicadores: "
                                  f"{', '.join(sorted({c.indicador_id for c in cifras}))}.")}
    for c in cifras:
        sig, ent, nat = FUENTE.get(c.fuente_principal, (c.fuente_principal, "", ""))
        sec = {"1_origen": f"{c.nombre_ciudadano}. {sig} ({ent}), {c.anio}. Es {nat}."
                           + (f" Datos descargados el {c.fecha_descarga}." if c.fecha_descarga else ""),
               "2_territorio": (f"La cifra se presenta para {c.territorio_nombre}."
                                if str(c.territorio_nombre).startswith(NIVEL_TXT.get(c.nivel, c.nivel))
                                else f"La cifra se presenta por {NIVEL_TXT.get(c.nivel, c.nivel)} ({c.territorio_nombre}).")
                               + (f" Se pidió por {NIVEL_TXT.get(c.nivel_pedido, c.nivel_pedido)}; la fuente no alcanza ese nivel."
                                  if c.nivel_pedido and c.nivel_pedido != c.nivel and c.nivel != "establecimiento" else ""),
               "3_que_mide": "Mide " + _minus(c.rotulo_medida or c.nombre_ciudadano) + ".",
               "4_precision": _precision(c),
               "5_metodo": _metodo(c),
               "6_contraste_oficial": _contraste(c),
               "estado": c.estado_cifra, "semaforo": c.semaforo_cifra,
               "avisos": list(dict.fromkeys(m for m in (fmt.humanizar(x.mensaje, borrador.get("explicaciones"))
                                                       for x in (c.evaluacion.resultados if c.evaluacion else [])
                                                       if x.accion in ("advertir", "rotular") and x.regla != "R-CRUCES-09")
                                            if m))[:8]}
        larga["cifras"][c.id_cifra] = _ajustar_territorio(sec, c)
    for cr in r.cruces or []:
        pid = {c.id_cifra: c for c in cifras}
        nom = lambda k: (pid[k].nombre_ciudadano[0].lower() + pid[k].nombre_ciudadano[1:]) if k in pid else k
        larga["cruces"][cr["id_cruce"]] = (f"Se muestran lado a lado {nom(cr['a'])} y {nom(cr['b'])} para "
                                           f"{NIVEL_TXT.get(cr['nivel'], cr['nivel'])} en {', '.join(map(str, cr['anios']))}. "
                                           + ctx.lenguaje["frases_estandar"]["asociacion"])
    texto = "\n".join([l1, l2, l3, l4])
    larga = _humanizar_todo(larga)
    # el motivo, con mayúscula inicial, rellena {motivo_principal_respuesta} de R-CRUCES-10 en la 2.ª pasada
    return {"corta": corta, "larga": larga, "corta_texto": texto,
            "motivo": (motivo[0].upper() + motivo[1:] + ".") if motivo else None}


def _minus(t: str) -> str:
    """«Mide Servicios…» → «Mide servicios…» (revisión de usuario, 12/10/2026); respeta siglas (ENDES, PP)."""
    return t if not t or (len(t) > 1 and t[1].isupper()) else t[0].lower() + t[1:]


AMBITOS_TXT = "en el departamento o ámbito (Lima Metropolitana, Lima Región, Callao)"


def _ajustar_territorio(sec: dict, c) -> dict:
    """Revisión de usuario (12/10/2026) y N3 de P4: los rótulos genéricos nombran solo el territorio de la cifra (no Lima
    en una respuesta de Puno; no «del departamento» en una cifra de Lima Metropolitana)."""
    lugar = {"LIMA_METROPOLITANA": "en Lima Metropolitana", "LIMA_REGION": "en Lima Región", "CALLAO": "en el Callao"}
    def f(t):
        if not isinstance(t, str):
            return t
        t = t.replace(AMBITOS_TXT.replace("Lima Metropolitana, Lima Región, Callao", "LM, LR, Callao"), AMBITOS_TXT)
        t = t.replace(AMBITOS_TXT, lugar.get(c.nivel, "en el departamento"))
        if c.nivel in lugar:
            t = t.replace("niños de 6 a 35 meses del departamento", "niños de 6 a 35 meses de " + lugar[c.nivel][3:])
        return t
    return {k: ([f(x) for x in v] if isinstance(v, list) else f(v)) for k, v in sec.items()}


def _precision(c) -> str:
    if c.medida == "intervalo":
        return f"Estimación con modelo: la pobreza está probablemente {fmt.intervalo(c.ic_inf, c.ic_sup)}."
    if c.medida == "cobertura":
        return (f"Dos cotas: {fmt.pct(c.cota_inf)} contando a los niños por su procedencia y {fmt.pct(c.cota_sup)} "
                "sumando a los atendidos sin procedencia registrada.")
    if c.medida in fmt.MEDIDAS_MONTO:
        pa = c.pct_gasto_atribuible
        extra = f" El {fmt.pct(100 * pa, 0)} del gasto del departamento se puede ubicar en municipalidades y obras." if pa is not None else ""
        precios = (f"en soles de {c.anio_base_deflactor} (ajustado por inflación)" if c.get("precios") == "constantes"
                   else "en soles corrientes")                 # S1-12 (R-GASTO-12)
        return f"Monto registrado (devengado), {precios}." + extra
    if c.metodo_ic == "wilson":
        return f"Basado en {int(c.n_muestra):,} niños tamizados".replace(",", fmt.FINO) + \
            f"; el valor está probablemente entre {fmt.pct(c.ic_inf)} y {fmt.pct(c.ic_sup)}."
    if c.ic_inf is not None:
        base = (f"El valor real está probablemente entre {fmt.pct(c.ic_inf)} y {fmt.pct(c.ic_sup)} "
                f"(coeficiente de variación {fmt._num(c.cv, 1)}{fmt.FINO}%, {int(c.n_muestra)} casos en la muestra).")
        return base + " " + _nota_ic(c)
    return ""


def _humanizar_todo(x):
    """P4-10: ningún código interno a la vista en la ficha larga (cifras, cruces y avisos)."""
    if isinstance(x, str):
        return fmt.humanizar(x) or x
    if isinstance(x, list):
        return [_humanizar_todo(y) for y in x]
    if isinstance(x, dict):
        return {k: (_humanizar_todo(v) if k != "reproducibilidad" else v) for k, v in x.items()}
    return x


CRITERIO_TXT = {"RM363-2022/OMS2001": "con la forma de medir anterior a 2024",
                "RM251-2024/OMS2024": "con la forma de medir vigente desde 2024"}


def _contraste(c) -> str:
    """Decisión del 11/10/2026: la comparación con la cifra oficial se hace con el mismo criterio de medición."""
    if c.medida != "proporcion":
        return ""
    o = c.get("contraste_oficial")
    if not o or o.get("valor") is None:
        return "No tenemos registrada una cifra oficial para comparar esta cifra con la misma forma de medir."
    crit = CRITERIO_TXT.get(o["criterio"], "con la misma definición")
    ent = o.get("entidad", "INEI")
    doc = re.sub(r"^(INEI|INS),\s*", "", o["documento"])
    igual = abs(round(c.valor, 1) - o["valor"]) <= 0.1
    return (f"El {ent} publica {fmt.pct(o['valor'])} {crit} ({doc}, {o['cuadro_pagina']}). "
            + ("Nuestra cifra coincide." if igual else f"Nuestra cifra es {fmt.pct(c.valor)}: revisar la diferencia."))


def _nota_ic(c) -> str:
    """Decisión del 11/10/2026 (piloto): mostrar nuestro intervalo y el que publica el INEI, con sus diferencias."""
    ii = c.get("ic_inei")
    if not ii:
        return ("Este intervalo es nuestro cálculo (no tenemos registrado uno publicado por el INEI para esta cifra), con "
                "un método que se ajusta mejor cuando hay pocos casos o el porcentaje es muy alto o muy bajo.")
    doc = re.sub(r"^INEI,\s*", "", ii["documento"])
    return (f"El INEI publica para esta cifra un intervalo entre {fmt.pct(ii['ic_inf'])} y {fmt.pct(ii['ic_sup'])} "
            f"({doc}, {ii['cuadro_pagina']}). Los dos salen de los mismos datos y tienen la misma cifra central; "
            "cambia el método: el del INEI es simétrico alrededor de la cifra y el nuestro se ajusta mejor cuando hay "
            "pocos casos o el porcentaje es muy alto o muy bajo. Por eso pueden diferir en algunas décimas.")


def _metodo(c) -> str:
    comp = c.comparacion
    if not comp or not comp.get("prueba_cambio"):
        return ""
    if c.comparacion_bloqueada:
        return f"No se compara {comp['anio']} con {c.anio}: entre esos años cambió la forma de medir o de hacer la encuesta."
    pc = comp["prueba_cambio"]
    return (f"Entre {comp['anio']} y {c.anio}: " + ("cambio estadísticamente claro" if pc["significativa"]
                                                    else "sin cambio estadísticamente claro")
            + " (prueba de diferencia con el diseño de la encuesta, al 95 % de confianza).")


def _n(x, d=1) -> str:
    return fmt._num(float(x), d) if x is not None else "—"


def rotulos(raiz: Path | None = None) -> dict:
    """Rótulos de sección de la respuesta (S3-01, tarea 3): `curados/motor/textos/capas.yaml`, clave `rotulos`. Los leen el .md y la web."""
    return plantillas.textos(raiz or encontrar_raiz(), "capas.yaml")["rotulos"]


def markdown(res: dict, rot: dict | None = None) -> str:
    """Respuesta por capas (contrato de respuesta, 12/10/2026) y, al final, el detalle técnico. Los rótulos salen del YAML."""
    R = rot or rotulos()
    q, k = res["consulta"], res["capas"]
    c1, c2, c3 = k["capa1"], k["capa2"], k["capa3"]
    out = [f"# {q['id']} — {q['pregunta']}", "", c1["respuesta_corta"], ""]
    if res.get("entendimos"):  # S2-06: pregunta en texto libre; va primero y fuera de las capas
        out = [res["entendimos"], ""] + out
    cl = c1.get("cifra_clave")
    if cl:
        out += ([f"> **{cl['valor']}** {cl['texto']}  "] if cl["valor"] else [f"> **{cl['texto']}**  "]) + [f"> Fuente: {cl['fuente']}.", ""]
    if c1["ojo_al_leer"]:
        out += [f"**{R['ojo_al_leer']}**", ""] + [f"- {t}" for t in c1["ojo_al_leer"]] + [""]
    if c1.get("lo_mas_cercano"):  # S1-05: respuesta de «no se puede»
        out += [f"**{c1['lo_mas_cercano']['titulo']}**", "", c1["lo_mas_cercano"]["texto"], ""]
    out += [f"**{c1['confianza']['texto']}**", ""]
    qh = k["capa1"].get("que_hacer")
    if qh:  # verificación de usuario (13/10/2026): bloque propio bajo la confianza, no dentro de «Para citar»
        nota = "" if qh["revisado_dueno"] else f" *{R['texto_pendiente']}*"
        out += [f"**▸ {R['que_hacer']}**" + nota, "", f"{qh['texto']} Fuente: [{qh['fuente']}]({qh['url']}).", ""]
    out += ["---", "", f"## ▸ {R['mas_contexto']}", ""]
    for t in c2["mas_contexto"]:
        out += [f"**{t['titulo']}**", "", t["texto"]] + ([f"*{t['etiqueta']}*"] if t.get("etiqueta") else []) + [""]
    if c2["avisos"]:
        out += [f"**{R['avisos']}**", ""] + [f"- {a}" for a in c2["avisos"]] + [""]
    out += [f"**{R['limites']}**", ""] + [f"- {x}" for x in c2["limites"]] + ["", f"## ▸ {R['para_citar']}", "",
                                                                              f"**{R['como_citar']}**", ""]
    # S3-01 (plan_slices.md, slice 3; P-02): cada cita con su enlace al documento oficial, cuando existe
    out += [f"- {x['texto']}" + (f" [{R['enlace_oficial']}]({x['url']})" if x["url"] else "") for x in c3["citas"]] + [""]
    if c3["glosario"]:
        out += [f"**{R['glosario']}**", ""] + [f"- **{g['termino']}**: {g['definicion']}" for g in c3["glosario"]] + [""]
    sem = res["semaforo_respuesta"]
    out += ["---", "", "## Detalle técnico", "", f"Semáforo interno de la respuesta (R-CRUCES-10): {sem} "
            f"({', '.join(res.get('motivos_semaforo_respuesta') or [])}). Capa visible: {c1['palabras']} palabras.", "",
            "### Cifras", "",
            "| id | indicador | año | nivel | territorio | valor (IC propio) | IC del INEI | estado | semáforo |",
            "|---|---|---|---|---|---|---|---|---|"]
    for kk, c in res["cifras"].items():
        v = c.get("valor")
        if c["medida"] == "intervalo":
            vv = f"{_n(c['ic_inf'])}–{_n(c['ic_sup'])} %"
        elif c["medida"] == "cobertura":
            vv = f"{_n(c['cota_inf'])}–{_n(c['cota_sup'])} %"
        elif c["medida"] in fmt.MEDIDAS_MONTO:
            vv = f"S/ {_n(v / 1e6, 2)} M"
        else:
            vv = f"{_n(v)} % ({_n(c['ic_inf'])}–{_n(c['ic_sup'])})" if v is not None else "—"
        ii = c.get("ic_inei")
        vi = f"{_n(ii['ic_inf'])}–{_n(ii['ic_sup'])}" if ii else "—"
        out.append(f"| {kk} | {c['indicador_id']} | {c['anio']} | {c['nivel']} | {c['territorio_nombre']} | {vv} | {vi} | "
                   f"{c['estado_cifra']} | {c['semaforo_cifra']} |")
    out += ["", "### Ficha de límites", "", "```", res["ficha"]["corta"], "```", "", "### Ficha larga", "", "```json",
            json.dumps(res["ficha"]["larga"], ensure_ascii=False, indent=1), "```", "", "### Corrector y reglas de la respuesta", ""]
    for x in res["resultados_respuesta"]:
        out.append(f"- {x.get('regla')}: {x.get('accion')} · {x.get('motivo')}" + (f" → {x.get('objetivo')}" if x.get("objetivo") else ""))
    out += ["", "Texto validado (con marcadores):", "", "> " + res["texto_con_marcadores"]]
    return "\n".join(out) + "\n"
