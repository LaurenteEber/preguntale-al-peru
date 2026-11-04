"""Ejecutor de los casos de prueba del validador (contrato §6): `pap validar-reglas`."""
from __future__ import annotations

from pathlib import Path

import yaml

from . import cargar
from .nucleo import REGISTRO, Cifra, Contexto, Respuesta
from .validador import correr_regla, evaluar_cifra


def _cifra(caso: dict, ctx: Contexto) -> Cifra:
    b = caso.get("base") or {}
    fila, ind = {}, {}
    if b:
        ind = ctx.indicadores.get(b.get("indicador"), {})
        if b.get("anio") is not None:
            fila = ctx.fila_cubo(b["indicador"], b["anio"], b["nivel"], str(b["territorio"]), b.get("medida"),
                                 b.get("linea", "cifra")) or {}
    datos = {**fila, **(caso.get("cifra") or {})}
    # si el caso cambia valor/ee/n, los alias se recalculan
    return Cifra.desde(datos, ind, caso.get("consulta"))


def _respuesta(caso: dict, ctx: Contexto) -> Respuesta:
    r = dict(caso.get("respuesta") or {})
    cifras = []
    for x in r.get("cifras") or []:
        x = dict(x)
        sub = {"base": x.pop("base", None), "cifra": x, "consulta": x.pop("consulta", None)}
        cifras.append(_cifra(sub, ctx))
    r["cifras"] = cifras
    return Respuesta({**(caso.get("consulta") or {}), **r})


def correr_caso(caso: dict, ctx: Contexto) -> dict:
    ctx2 = ctx.con_sobrescrituras(caso.get("contexto"))
    esp = caso.get("espera") or {}
    rid = caso["regla"]
    if rid == "PIPELINE":
        c = _cifra(caso, ctx2)
        ev = evaluar_cifra(c, ctx2)
        ok = all(esp.get(k) is None or esp[k] == v for k, v in (("accion_final", ev.accion_final),
                                                                ("estado_cifra", ev.estado_cifra)))
        return {"id": caso["id"], "regla": rid, "ok": ok, "obtenido": {"accion_final": ev.accion_final,
                "estado_cifra": ev.estado_cifra, "resultados": [r.a_dict() for r in ev.resultados]}}
    if rid == "R-MOTOR-01" and caso.get("evaluacion") is not None:  # N-1: el paso de degradación es siguiente_paso
        from .reglas_etapa0 import siguiente_paso
        from .validador import Evaluacion
        from .nucleo import Resultado as _R
        e = caso["evaluacion"]
        ev = Evaluacion(resultados=[_R(x.get("regla", "X"), x["accion"], x.get("motivo", ""), nivel_minimo=x.get("nivel_minimo"))
                                    for x in e.get("resultados", [])], accion_final=e.get("accion_final", "publicar"))
        ev.estado_cifra = e.get("estado_cifra", "publicable")
        paso = siguiente_paso(_cifra(caso, ctx2), ev, ctx2)
        dispara = paso is not None
        ok = dispara == bool(esp.get("dispara", True))
        if ok and dispara and esp.get("paso"):
            ok = all(paso.get(k) == v for k, v in esp["paso"].items())
        return {"id": caso["id"], "regla": rid, "ok": ok, "esperado": esp, "obtenido": paso or "sin paso"}
    if rid not in REGISTRO:
        return {"id": caso["id"], "regla": rid, "ok": False, "obtenido": "regla sin implementar"}
    impl = REGISTRO[rid]
    obj = _respuesta(caso, ctx2) if impl.ambito == "respuesta" else _cifra(caso, ctx2)
    try:
        res = correr_regla(rid, obj, ctx2)
    except Exception as e:  # un error de la implementación es un fallo del caso, no del ejecutor
        return {"id": caso["id"], "regla": rid, "ok": False, "obtenido": f"error: {type(e).__name__}: {e}"}
    principales = [r for r in res if not r.modificador] or res
    dispara = bool(res)
    ok = dispara == bool(esp.get("dispara", True))
    if ok and dispara:
        for k in ("accion", "motivo", "modo", "objetivo", "nivel_minimo"):
            if esp.get(k) is not None:
                ok &= any(getattr(r, k) == esp[k] for r in res)
        if esp.get("periodo_esperado") is not None:  # agrupar años (R-ENC-10, R-REG-03): ventana elegida
            ok &= any(list(esp["periodo_esperado"]) in (list(r.detalle.get("periodo") or []), list(r.detalle.get("anios") or []),
                                                         list(r.detalle.get("periodo_agrupado") or [])) for r in res)
        if esp.get("semaforo") is not None:  # R-CRUCES-09, R-CRUCES-10 y R-EST-05: color en el detalle
            ok &= any(esp["semaforo"] in (r.detalle.get("semaforo"), r.detalle.get("semaforo_respuesta"),
                                          r.detalle.get("semaforo_cifra")) for r in res)
    return {"id": caso["id"], "regla": rid, "ok": ok, "esperado": esp,
            "obtenido": [r.a_dict() for r in res] if res else "no dispara",
            "principal": principales[0].accion if res else None}


def correr(ctx: Contexto, carpeta: Path) -> list[dict]:
    cargar()
    salida = []
    for f in sorted(Path(carpeta).glob("*.yaml")):
        for caso in yaml.safe_load(f.read_text(encoding="utf-8")) or []:
            r = correr_caso(caso, ctx)
            r["archivo"] = f.name
            salida.append(r)
    return salida


def cobertura(casos: list[dict], alcance: list[str]) -> dict:
    """Por regla del alcance: ¿implementada?, ¿hay un caso que dispara y uno que no?"""
    import collections
    por = collections.defaultdict(list)
    for c in casos:
        por[c["regla"]].append(c)
    out = {}
    for rid in alcance:
        cs = por.get(rid, [])
        out[rid] = {"implementada": rid in REGISTRO, "casos": len(cs), "ok": sum(c["ok"] for c in cs),
                    "con_dispara": any((c.get("esperado") or {}).get("dispara", True) for c in cs),
                    "con_no_dispara": any((c.get("esperado") or {}).get("dispara", True) is False for c in cs)}
    return out
