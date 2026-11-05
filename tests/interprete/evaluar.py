"""S2-04 y S2-09 — Corredor de grabaciones y evaluación en vivo del intérprete.

    uv run python tests/interprete/evaluar.py --grabar [--solo id1,id2] [--faltantes]
    uv run python tests/interprete/evaluar.py --evaluar [--modelo M] [--reporte <md>] [--tope-costo USD] [--solo ids]

`--grabar` graba la primera llamada al LLM de cada pregunta. `--evaluar` corre el conjunto de evaluación
(tests/interprete/evaluacion.yaml) por `interpretar()`, con el cliente en modo «completar»: usa la grabación si existe y si no
llama a la API y graba (también los reintentos, E-05). Así una corrida nueva solo paga lo que falta. Compara según S2-02 §4 y
mide los umbrales de `interprete.evaluacion`.

Solo preguntas del conjunto, de las pruebas (tests/interprete/preguntas_prueba.yaml) y de las revisiones de S2-07
(tests/interprete/preguntas_revision.yaml), nunca de usuarios (P-03). Necesita la clave en `interprete.variable_clave`.
`interprete.tope_por_corrida` (o `--tope-costo`) corta la corrida. El uso va a salidas/interprete/uso.jsonl (fuera de git)."""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "tests"))
sys.path.insert(0, str(RAIZ / "tests" / "interprete"))

from pap.interprete.limpiar import limpiar  # noqa: E402
from pap.interprete.llm import Cliente, NoDisponible, registrar_uso, ruta_grabacion  # noqa: E402
from pap.interprete.prompt import armar  # noqa: E402

ARCHIVOS = ("tests/interprete/evaluacion.yaml", "tests/interprete/preguntas_prueba.yaml", "tests/interprete/preguntas_revision.yaml")


def entradas(raiz: Path, archivos=ARCHIVOS) -> dict[str, dict]:
    out = {}
    for ruta in archivos:
        p = raiz / ruta
        if p.exists():
            out.update({e["id"]: e for e in yaml.safe_load(p.read_text(encoding="utf-8"))["entradas"]})
    return out


def preguntas(raiz: Path) -> dict[str, str]:
    return {i: e["pregunta"] for i, e in entradas(raiz).items()}


def estimar(raiz: Path, n: int) -> dict:
    """Costo máximo estimado de n llamadas, con los precios de `interprete`: entrada ≈ caracteres de las instrucciones / 3 (por
    exceso, sin contar el caché) y salida = `max_tokens` (el peor caso). Sirve para ver el tope antes de llamar."""
    c = Cliente(raiz, modo="reproducir")
    prompt, _ = armar(raiz)
    entrada = len(prompt) // 3 + 200
    salida = int(c.par["max_tokens"]["valor"])
    pr = c.par["precios_usd_por_millon"]
    una = entrada * float(pr["entrada"]) / 1e6 + salida * float(pr["salida"]) / 1e6
    return {"llamadas": n, "tokens_entrada_por_llamada": entrada, "tokens_salida_max": salida, "usd_por_llamada": round(una, 4),
            "usd_max": round(una * n, 4), "tope_usd": c.tope}


def grabada(raiz: Path, pregunta: str) -> bool:
    c = Cliente(raiz, modo="reproducir")
    _, version = armar(raiz)
    return ruta_grabacion(raiz, limpiar(pregunta, raiz).texto, c.par["modelo"]["valor"], version).exists()


def grabar(raiz: Path, ids: list[str] | None, cliente: Cliente | None = None) -> dict:
    todas = preguntas(raiz)
    faltan = [i for i in ids or [] if i not in todas]
    if faltan:
        raise SystemExit(f"ids que no están en el conjunto ni en las pruebas: {faltan}")
    prompt, version = armar(raiz)
    cliente = cliente or Cliente(raiz, modo="grabar")
    hechas, cortado = [], None
    for i in ids or list(todas):
        limpia = limpiar(todas[i], raiz).texto
        try:
            r = cliente.interpretar_crudo(prompt, limpia, version)
        except NoDisponible as e:
            cortado = e.motivo
            break
        registrar_uso(raiz, limpia, None, "grabada", r)                # salidas/interprete/uso.jsonl, fuera de git (P-03)
        hechas.append((i, r.grabacion, r.costo_usd, r.tokens_entrada, r.tokens_salida))
    return {"hechas": hechas, "cortado": cortado, "gastado_usd": round(cliente.gastado, 6)}


# ======================================================================= evaluación (S2-09)

class Anotador:
    """Envuelve al cliente y guarda cada respuesta del LLM (grabada o en vivo) para el costo y la latencia."""

    def __init__(self, cliente: Cliente):
        self.cliente, self.respuestas = cliente, []

    def interpretar_crudo(self, *a, **k):
        r = self.cliente.interpretar_crudo(*a, **k)
        self.respuestas.append(r)
        return r


def _sin_defaults(c: dict, par: dict) -> dict:
    """La consulta en la forma de comparar: intención por defecto explícita y periodo por defecto quitado."""
    c = json.loads(json.dumps(c or {}))
    c.setdefault("intencion", par["interprete"]["sin_intencion"]["valor"])
    per = c.get("periodo")
    if per in ({"tipo": "ultimo"}, {"tipo": "serie"}):
        c.pop("periodo")
    return c


def _lugar(motor, x):
    from pap.motor import territorio as T
    if not x:
        return None
    if "nivel" in x:                                   # identificar_extremo
        return ("nivel", x["nivel"], _lugar(motor, x.get("dentro_de")))
    r = T.resolver(x, motor.ctx)
    if isinstance(r, T.Aclaracion):
        return ("aclaracion", r.motivo, tuple(sorted(o["territorio"].id for o in r.opciones)))
    return ("lugar", r.id)


def misma_consulta(motor, esperada: dict, producida: dict, par: dict) -> list[str]:
    """S2-02 §4: intención, tema, periodo y nivel iguales; los lugares, por lo que devuelve `territorio.resolver()`.
    Devuelve los campos que difieren."""
    e, p = _sin_defaults(esperada, par), _sin_defaults(producida, par)
    malos = [k for k in ("intencion", "tema", "periodo") if e.get(k) != p.get(k)]
    for k in ("territorio", "comparar_con"):
        if _lugar(motor, e.get(k)) != _lugar(motor, p.get(k)):
            malos.append(k)
    return malos


def juzgar(motor, e: dict, r: dict, par: dict) -> tuple[bool, str]:
    """(acierto, detalle) de una entrada del conjunto frente a la respuesta de `interpretar()`."""
    es, i = e["esperado"], r["interpretacion"]
    res = i["resultado"]
    validos = es.get("resultado_en") or [es["resultado"]]
    if res not in validos:
        return False, f"resultado {res} (se esperaba {'/'.join(validos)})"
    if res == "consulta" and "consulta" in es:
        malos = misma_consulta(motor, es["consulta"], i.get("consulta") or {}, par)
        return (not malos), (f"difiere en {', '.join(malos)}: {json.dumps(i.get('consulta'), ensure_ascii=False)}" if malos else "")
    if res == "aclaracion" and "motivo" in es:
        motivo = ((r.get("aclaracion") or {}).get("motivo") or "").removeprefix("interprete_")
        return motivo == es["motivo"], ("" if motivo == es["motivo"] else f"motivo {motivo}")
    if res == "fuera_de_alcance" and "tipo" in es:
        motivo = ((r.get("plan") or {}).get("no_se_puede") or {}).get("motivo")
        tipo = {"tema_fuera_del_piloto": "tema", "interprete_fuera_de_alcance": "pregunta"}.get(motivo)
        return tipo == es["tipo"], ("" if tipo == es["tipo"] else f"tipo {tipo}")
    return True, ""


def numeros_nuevos(motor, r: dict, pregunta: str) -> list[str]:
    """Métrica 2 con la comparación diferencial de E-08: números visibles que no son años ni salen de un marcador, sin contar
    los que la vía estructurada también muestra para la misma consulta (textos fijos como «6 a 35 meses»)."""
    from pap.motor import preguntar as P
    from test_evaluacion_grabada import numeros_sueltos
    sueltos = numeros_sueltos(r, (r.get("plan") or {}).get("pregunta") or pregunta)
    cm = r.get("consulta_minima") or {}
    if sueltos and r.get("tipo") in ("respuesta", "no_se_puede") and cm.get("tema"):
        try:
            base = P.preguntar_minima(motor, {**cm, "pregunta_original": "consulta de control", "idioma": "es"})
            fijos = set(numeros_sueltos(base, "consulta de control"))
        except Exception:                      # noqa: BLE001 — si la vía estructurada no responde, no se descuenta nada
            fijos = set()
        sueltos = [n for n in sueltos if n not in fijos]
    return sueltos


def evaluar(raiz: Path, ids=None, modelo=None, tope=None, cliente=None, motor=None) -> dict:
    from pap.interprete.interpretar import interpretar
    from pap.motor.preguntar import EleccionInvalida
    from pap.motor.respuesta import Motor
    from pap.motor.validador.contexto import cargar_contexto
    from test_evaluacion_grabada import sin_ancla
    par = yaml.safe_load((raiz / "curados/motor/parametros_motor.yaml").read_text(encoding="utf-8"))
    conjunto = entradas(raiz, ARCHIVOS[:1])
    elegidas = [conjunto[i] for i in ids] if ids else list(conjunto.values())
    motor = motor or Motor(cargar_contexto(raiz))
    cliente = cliente or Cliente(raiz, modo="completar", modelo=modelo, tope_usd=tope)
    llm = Anotador(cliente)
    filas, cortado = [], None
    with tempfile.TemporaryDirectory() as cache:                     # sin la caché de 24 h: se mide el LLM, no la caché
        for e in elegidas:
            if cliente.detenido or cliente.gastado >= cliente.tope:
                cortado = cliente.detenido or "tope_por_corrida"
                break
            antes = len(llm.respuestas)
            t0 = time.monotonic()
            try:
                r = interpretar(e["pregunta"], motor, llm=llm, cache_dir=Path(cache), registro=raiz / "salidas/interprete/uso.jsonl")
            except EleccionInvalida as x:
                filas.append({"id": e["id"], "categoria": e["categoria"], "ok": False, "detalle": f"error de uso: {x}"})
                continue
            i = r["interpretacion"]
            ok, detalle = juzgar(motor, e, r, par)
            malos = sin_ancla(e["pregunta"], i["consulta"], i.get("anclas") or {}) if i.get("consulta") else []
            nums = numeros_nuevos(motor, r, e["pregunta"])
            usadas = llm.respuestas[antes:]
            filas.append({"id": e["id"], "categoria": e["categoria"], "ok": ok, "detalle": detalle, "resultado": i["resultado"],
                          "tipo": r["tipo"], "esperado": e["esperado"].get("resultado") or e["esperado"].get("resultado_en"),
                          "sin_ancla": malos, "numeros": nums, "reintentos": i.get("reintentos", 0),
                          "costo_usd": sum(x.costo_usd for x in usadas), "latencia_s": sum(x.latencia_s for x in usadas),
                          "tokens": sum(x.tokens_entrada + x.tokens_salida for x in usadas), "segundos": time.monotonic() - t0})
    return {"filas": filas, "cortado": cortado, "gastado_usd": round(cliente.gastado, 6), "llamadas_en_vivo": len(cliente.llamadas),
            "modelo": cliente.par["modelo"]["valor"], "esfuerzo": cliente.par.get("esfuerzo", {}).get("valor"),
            "version_prompt": armar(raiz)[1], "umbrales": par["interprete"]["evaluacion"]["valor"], "total": len(elegidas)}


def metricas(ev: dict) -> dict:
    u, filas = ev["umbrales"], ev["filas"]

    def frac(cats, cond=lambda f: f["ok"]):
        fs = [f for f in filas if f["categoria"] in cats]
        return (sum(cond(f) for f in fs) / len(fs)) if fs else None, len(fs)
    m = {}
    for k in ("consulta_exacta", "aclaracion_esperada", "fuera_de_alcance", "inyeccion_sin_efecto"):
        v, n = frac(u[k]["categorias"], (lambda f: f["ok"] and not f["numeros"]) if k == "inyeccion_sin_efecto" else (lambda f: f["ok"]))
        m[k] = {"valor": v, "n": n, "umbral": f"≥ {u[k]['minimo']:.0%}", "cumple": v is not None and v >= u[k]["minimo"]}
    consultas = [f for f in filas if f.get("esperado") == "consulta" and f["categoria"] not in u["aclaracion_esperada"]["categorias"]]
    v = sum(f.get("resultado") == "aclaracion" for f in consultas) / len(consultas) if consultas else None
    m["aclaracion_innecesaria"] = {"valor": v, "n": len(consultas), "umbral": f"≤ {u['aclaracion_innecesaria']['maximo']:.0%}",
                                   "cumple": v is not None and v <= u["aclaracion_innecesaria"]["maximo"]}
    for k, campo in (("valores_sin_ancla", "sin_ancla"), ("numeros_fuera_de_marcadores", "numeros")):
        n = sum(len(f.get(campo) or []) for f in filas)
        m[k] = {"valor": n, "n": len(filas), "umbral": "0", "cumple": n == 0}
    lat = sorted(f["latencia_s"] for f in filas if f.get("latencia_s"))
    m["costo_medio_usd"] = sum(f.get("costo_usd", 0) for f in filas) / len(filas) if filas else 0
    m["latencia_p95_s"] = lat[min(len(lat) - 1, int(0.95 * len(lat)))] if lat else None
    m["cumple_todo"] = all(x["cumple"] for x in m.values() if isinstance(x, dict) and "cumple" in x) and \
        ev["cortado"] is None and len(filas) == ev["total"]
    return m


def reporte(ev: dict, m: dict, titulo: str) -> str:
    filas = ev["filas"]
    por_cat = defaultdict(lambda: [0, 0])
    for f in filas:
        por_cat[f["categoria"]][0] += f["ok"]
        por_cat[f["categoria"]][1] += 1

    def pct(v):
        return "—" if v is None else (f"{v:.0%}" if isinstance(v, float) else str(v))
    lat = "—" if m["latencia_p95_s"] is None else f"{m['latencia_p95_s']:.1f} s"
    out = [f"# {titulo}", "",
           f"Modelo `{ev['modelo']}`, esfuerzo `{ev['esfuerzo']}`, `version_prompt` `{ev['version_prompt'][:19]}…`. "
           f"{len(filas)} de {ev['total']} preguntas corridas" + (f"; **cortada: {ev['cortado']}**" if ev["cortado"] else "") + ".",
           f"Costo de esta corrida (llamadas en vivo): US$ {ev['gastado_usd']:.4f} en {ev['llamadas_en_vivo']} llamadas. "
           f"Costo medio por pregunta (en vivo o grabado): US$ {m['costo_medio_usd']:.4f}; latencia p95 del LLM: {lat}.", "",
           "## Métricas", "", "| Métrica | Valor | Sobre | Umbral | Cumple |", "|---|---|---|---|---|"]
    for k in ("consulta_exacta", "aclaracion_esperada", "aclaracion_innecesaria", "fuera_de_alcance", "inyeccion_sin_efecto",
              "valores_sin_ancla", "numeros_fuera_de_marcadores"):
        x = m[k]
        out.append(f"| {k} | {pct(x['valor'])} | {x['n']} | {x['umbral']} | {'sí' if x['cumple'] else '**no**'} |")
    out += ["", f"**Cumple todos los umbrales: {'sí' if m['cumple_todo'] else 'no'}.**", "", "## Por categoría", "",
            "| Categoría | Aciertos | Total |", "|---|---|---|"]
    out += [f"| {c} | {a} | {n} |" for c, (a, n) in sorted(por_cat.items())]
    fallas = [f for f in filas if not f["ok"] or f.get("sin_ancla") or f.get("numeros")]
    grupos = Counter(re.sub(r":.*", "", f["detalle"] or ("sin ancla" if f.get("sin_ancla") else "números"))
                     for f in fallas)
    out += ["", "## Fallas agrupadas", ""] + [f"- {g}: {n}" for g, n in grupos.most_common()] + ["", "## Fallas", "",
            "| id | categoría | detalle | sin ancla | números |", "|---|---|---|---|---|"]
    out += [f"| {f['id']} | {f['categoria']} | {f['detalle'].replace('|', '/')} | {', '.join(f.get('sin_ancla') or [])} | "
            f"{', '.join(f.get('numeros') or [])} |" for f in fallas]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    modo = a.add_mutually_exclusive_group(required=True)
    modo.add_argument("--grabar", action="store_true", help="graba la primera llamada de cada pregunta")
    modo.add_argument("--evaluar", action="store_true", help="corre el conjunto por interpretar() y mide los umbrales")
    a.add_argument("--solo", help="ids separados por coma")
    a.add_argument("--faltantes", action="store_true", help="con --grabar: solo las que no tienen grabación")
    a.add_argument("--modelo", help="identificador del modelo (por defecto interprete.modelo)")
    a.add_argument("--reporte", help="archivo .md del reporte (con --evaluar)")
    a.add_argument("--tope-costo", type=float, help="US$ que cortan la corrida (por defecto interprete.tope_por_corrida)")
    x = a.parse_args(argv)
    ids = x.solo.split(",") if x.solo else None
    if x.grabar:
        if x.faltantes:
            ids = [i for i in (ids or list(preguntas(RAIZ))) if not grabada(RAIZ, preguntas(RAIZ)[i])]
        e = estimar(RAIZ, len(ids) if ids is not None else len(preguntas(RAIZ)))
        print(f"estimado (máximo): {e['llamadas']} llamadas × US$ {e['usd_por_llamada']:.4f} = US$ {e['usd_max']:.4f} · "
              f"tope US$ {e['tope_usd']:.2f}")
        r = grabar(RAIZ, ids, Cliente(RAIZ, modo="grabar", modelo=x.modelo, tope_usd=x.tope_costo))
        for i, g, c, te, ts in r["hechas"]:
            print(f"{i}: {g} · tokens {te} + {ts} · US$ {c:.4f}")
        print(f"gastado: US$ {r['gastado_usd']:.4f}" + (f" · cortado: {r['cortado']}" if r["cortado"] else ""))
        return 1 if r["cortado"] else 0
    conjunto = entradas(RAIZ, ARCHIVOS[:1])
    faltan = [i for i, e in conjunto.items() if (not ids or i in ids) and not grabada(RAIZ, e["pregunta"])]
    e = estimar(RAIZ, len(faltan))
    print(f"sin grabar: {len(faltan)} · estimado (máximo, sin reintentos ni caché): US$ {e['usd_max']:.4f} · "
          f"tope US$ {x.tope_costo or e['tope_usd']:.2f}")
    ev = evaluar(RAIZ, ids, x.modelo, x.tope_costo)
    m = metricas(ev)
    texto = reporte(ev, m, "Evaluación del intérprete")
    if x.reporte:
        Path(x.reporte).write_text(texto, encoding="utf-8")
    print(texto)
    return 0 if m["cumple_todo"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
