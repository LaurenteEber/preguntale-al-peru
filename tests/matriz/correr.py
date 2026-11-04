"""S1-08 — Corredor de la matriz de cobertura: responde cada caso con el mismo camino que `pap preguntar`
(`pap.motor.preguntar.preguntar_minima`), lo clasifica y le aplica las comprobaciones de `comprobar.py`.

Clases: respondida | no_se_puede (con su motivo) | aclaracion | error (excepción). Un caso falla si es `error`, si una
comprobación falla, si una combinación sin datos no sale como `no_se_puede`, si una aclaración no era la esperada o si el
motivo de «no se puede» no es uno de S1-05 (curados/motor/textos/no_se_puede.yaml).

Corrida completa, a mano, con la salida fuera de git (`salidas/` está en .gitignore):

    uv run python tests/matriz/correr.py --salida salidas/matriz --reporte backlog/slice-1/evidencia/matriz.md

Escribe en `--salida`: `resultados.jsonl` (una línea por caso) y, de los casos con fallos y de los 20 más largos, la respuesta
en JSON y markdown. Opciones: `--reducida` (los `matriz_cobertura.casos_pytest` casos de pytest), `--limite N`."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import traceback
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path[:0] = [str(AQUI.parent), str(AQUI.parents[1] / "src")]            # `matriz` (tests/) y `pap` (src/)

from matriz import comprobar as C  # noqa: E402
from matriz import generar as G  # noqa: E402

RAIZ = AQUI.parents[1]


def cargar(raiz=RAIZ):
    """(motor, parámetros, nombres mostrados por ubigeo). Si falta el cubo, lanza AssertionError (no se salta)."""
    from pap.motor.respuesta import Motor
    from pap.motor.validador.contexto import cargar_contexto
    assert (raiz / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    motor = Motor(cargar_contexto(raiz))
    return motor, C.parametros(raiz), G.territorios(raiz, motor.ctx)["nombre"]


def lugares_de(res: dict, caso: dict, nombre: dict) -> list[str]:
    """Los nombres_mostrados de los lugares de la respuesta: el pedido, el comparado, los de sus cifras y los de su departamento
    y provincia (T-02)."""
    ids = [caso.get("ubigeo")]
    plan = res.get("plan") or {}
    for t in (plan.get("territorio"), plan.get("territorio_comparado")):
        if isinstance(t, dict) and t.get("id"):
            ids.append(str(t["id"]))
    ids += [str(c["territorio_id"]) for c in (res.get("cifras") or {}).values()]
    out = set()
    for i in ids:
        if not i or not i[0].isdigit():
            continue
        u = i + "0000" if len(i) == 2 else i
        for x in (u, u[:4] + "00", u[:2] + "0000"):
            if x in nombre:
                out.add(nombre[x])
    return sorted(out)


def correr_caso(motor, p: dict, nombre: dict, caso: dict) -> tuple[dict, dict | None]:
    """(resultado del caso, respuesta completa o None si hubo excepción)."""
    r = {"id": caso["id"], "tema": caso["tema"], "intencion": caso["intencion"], "lugar": caso["lugar"], "grupo": caso["grupo"],
         "periodo": caso["periodo"], "consulta": caso["consulta"], "elegir": caso["elegir"], "clase": None, "motivo": None,
         "palabras": None, "fallos": []}
    from pap.motor import preguntar as P
    t0 = time.time()
    try:
        res = P.preguntar_minima(motor, caso["consulta"], elegir=caso["elegir"])
        r["clase"] = C.clase(res)
    except Exception as e:                                           # noqa: BLE001 — cualquier excepción es un caso `error`
        r["clase"] = "error"
        r["fallos"].append({"codigo": "error", "detalle": f"{type(e).__name__}: {e}", "traza": traceback.format_exc()[-1500:]})
        r["segundos"] = round(time.time() - t0, 2)
        return r, None
    r["segundos"] = round(time.time() - t0, 2)
    if r["clase"] == "aclaracion":
        if caso["espera"] != "aclaracion":
            r["fallos"].append({"codigo": "aclaracion_inesperada", "detalle": res["aclaracion"]["motivo"]})
        return r, res
    if caso["espera"] == "aclaracion":
        r["fallos"].append({"codigo": "aclaracion_esperada_no_salio", "detalle": r["clase"]})
    r["palabras"] = res["capas"]["capa1"]["palabras"]
    if r["clase"] == "no_se_puede":
        r["motivo"] = res["motivo"]["codigo"]
        from pap.motor import plantillas
        if r["motivo"] not in plantillas.textos(motor.ctx.raiz, "no_se_puede.yaml")["motivos"]:
            r["fallos"].append({"codigo": "motivo_que_no_es_de_s1_05", "detalle": r["motivo"]})
    elif caso["espera"] == "no_se_puede":
        r["fallos"].append({"codigo": "sin_datos_no_es_no_se_puede", "detalle": "el año pedido no tiene datos y se respondió"})
    r["fallos"] += C.revisar(res, p, lugares_de(res, caso, nombre))
    return r, res


# ----------------------------------------------------------------------------------------------------- reporte

def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ, capture_output=True, text=True).stdout.strip() or "sin commit"
    except OSError:
        return "sin commit"


def _fila(*celdas) -> str:
    return "| " + " | ".join(str(c).replace("|", "\\|") for c in celdas) + " |"


def reporte(resultados: list[dict], reducida: bool, segundos: float, conocidos: str = "") -> str:
    n = len(resultados)
    por_clase = Counter(r["clase"] for r in resultados)
    fallidos = [r for r in resultados if r["fallos"]]
    L = [f"# {datetime.now():%Y-%m-%d %H:%M} commit {_commit()} — S1-08 matriz de cobertura" + (" (versión reducida)" if reducida else ""), "",
         f"Casos: {n} · con fallos: {len(fallidos)} · tiempo: {segundos / 60:.1f} min. "
         "Generado por `tests/matriz/correr.py`; las respuestas completas quedan fuera de git.", "",
         "## Totales por clase", "", _fila("clase", "casos"), _fila("---", "---")]
    L += [_fila(c, por_clase.get(c, 0)) for c in C.CLASES] + [_fila("**total**", n), ""]
    L += ["## Totales por tema", "", _fila("tema", *C.CLASES, "total", "con fallos"), _fila(*["---"] * 7)]
    for t in sorted({r["tema"] for r in resultados}):
        rs = [r for r in resultados if r["tema"] == t]
        k = Counter(r["clase"] for r in rs)
        L.append(_fila(t, *[k.get(c, 0) for c in C.CLASES], len(rs), sum(1 for r in rs if r["fallos"])))
    L += ["", "## Totales por intención", "", _fila("intención", *C.CLASES, "total"), _fila(*["---"] * 6)]
    for t in sorted({r["intencion"] for r in resultados}):
        rs = [r for r in resultados if r["intencion"] == t]
        k = Counter(r["clase"] for r in rs)
        L.append(_fila(t, *[k.get(c, 0) for c in C.CLASES], len(rs)))
    L += ["", "## «No se puede» por motivo (S1-05)", "", _fila("motivo", "casos"), _fila("---", "---")]
    L += [_fila(m, k) for m, k in sorted(Counter(r["motivo"] for r in resultados if r["clase"] == "no_se_puede").items())]
    L += ["", "## Los 20 casos con la capa 1 más larga", "", f"Máximo permitido: {C.parametros(RAIZ)['respuesta']['capa1_palabras_max']['valor']} palabras (R-04).", "",
          _fila("palabras", "clase", "caso"), _fila("---", "---", "---")]
    for r in sorted((r for r in resultados if r["palabras"]), key=lambda r: (-r["palabras"], r["id"]))[:20]:
        L.append(_fila(r["palabras"], r["clase"], f"`{r['id']}`"))
    L += ["", "## Fallos", ""]
    if not fallidos:
        L.append("Ninguno.")
    por_codigo: dict[str, list] = defaultdict(list)
    for r in fallidos:
        for f in r["fallos"]:
            por_codigo[f["codigo"]].append((r, f))
    if por_codigo:
        L += [_fila("tipo de fallo", "casos"), _fila("---", "---")] + [_fila(c, len({r["id"] for r, _ in v})) for c, v in sorted(por_codigo.items())] + [""]
    for r in fallidos:
        L += [f"### `{r['id']}`", "", f"- clase: {r['clase']}" + (f" ({r['motivo']})" if r["motivo"] else ""),
              f"- consulta: `{json.dumps(r['consulta'], ensure_ascii=False)}`" + (f" con `--elegir {r['elegir']}`" if r["elegir"] else "")]
        L += [f"- {f['codigo']}: {json.dumps(f['detalle'], ensure_ascii=False)[:400]}" for f in r["fallos"][:6]] + [""]
    if conocidos:
        L += ["## Conocidos (consultas tipo C abiertas)", "", conocidos.strip(), ""]
    return "\n".join(L)


# ----------------------------------------------------------------------------------------------------- principal

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--salida", help="carpeta fuera de git para resultados.jsonl y las respuestas (por defecto salidas/matriz)")
    ap.add_argument("--reporte", help="escribe el reporte markdown en esta ruta")
    ap.add_argument("--reducida", action="store_true", help="solo los casos_pytest fijos")
    ap.add_argument("--limite", type=int)
    ap.add_argument("--conocidos", help="archivo de texto que se agrega al reporte como «Conocidos»")
    a = ap.parse_args(argv)
    motor, p, nombre = cargar()
    todos = G.casos(RAIZ, motor.ctx)
    par = G.parametros(RAIZ)
    casos = G.reducida(todos, par["casos_pytest"], par["semilla"]) if a.reducida else todos
    casos = casos[: a.limite] if a.limite else casos
    salida = Path(a.salida) if a.salida else RAIZ / "salidas" / "matriz"
    salida.mkdir(parents=True, exist_ok=True)
    resultados, respuestas = [], {}
    t0 = time.time()
    with (salida / "resultados.jsonl").open("w", encoding="utf-8") as f:
        for i, caso in enumerate(casos, 1):
            r, res = correr_caso(motor, p, nombre, caso)
            resultados.append(r)
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
            if res is not None and (r["fallos"] or (r["palabras"] or 0) >= 100):
                respuestas[r["id"]] = res                                   # solo las que se van a mirar: no se guardan 4 000 respuestas
            if i % 200 == 0:
                print(f"{i}/{len(casos)} casos · {time.time() - t0:.0f} s", flush=True)
    from pap.motor import ficha as F
    vistos = {r["id"] for r in resultados if r["fallos"]} | {r["id"] for r in sorted((r for r in resultados if r["palabras"]), key=lambda r: (-r["palabras"], r["id"]))[:20]}
    (salida / "respuestas").mkdir(exist_ok=True)
    for k, i in enumerate(sorted(vistos), 1):
        res = respuestas.get(i)
        if res is not None and res["tipo"] != "aclaracion":
            base = salida / "respuestas" / f"{k:04d}"
            base.with_suffix(".json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
            base.with_suffix(".md").write_text(f"<!-- {i} -->\n" + F.markdown(res), encoding="utf-8")
    conocidos = Path(a.conocidos).read_text(encoding="utf-8") if a.conocidos else ""
    texto = reporte(resultados, a.reducida, time.time() - t0, conocidos)
    if a.reporte:
        Path(a.reporte).write_text(texto, encoding="utf-8")
    print(texto.split("## Los 20")[0])
    return 1 if any(r["fallos"] for r in resultados) else 0


if __name__ == "__main__":
    sys.exit(main())
