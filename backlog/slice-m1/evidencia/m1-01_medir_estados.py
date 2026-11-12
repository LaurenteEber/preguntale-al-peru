"""M1-01 (C-M0-11-2): medir qué filas cambian de estado de publicación al aplicar R-ENC-03 y R-ENC-04 desde 25 casos (y R-ENC-19).

Uso (desde la raíz del repositorio):
    uv run python backlog/slice-m1/evidencia/m1-01_medir_estados.py antes     # con las reglas y el código vigentes
    uv run python backlog/slice-m1/evidencia/m1-01_medir_estados.py despues   # con las reglas nuevas
    uv run python backlog/slice-m1/evidencia/m1-01_medir_estados.py comparar  # lista de cambios

Mide dos conjuntos, cada uno por el camino del validador (etapas 0–7, sin degradación: el estado de la fila misma):
1. **El cubo completo:** todas las filas de encuesta (`naturaleza_dato = encuesta_muestral`, línea «cifra») de `fact_indicador.parquet`.
2. **Las 90 filas de las recetas** (ENDES 2024), por el camino nuevo: plan → ejecutor → compuertas (`recetas.compuertas_de`).
   Necesita los microdatos del Mac; si faltan, se anota y se sigue con el cubo.

Solo lee: no recalcula el cubo ni escribe en `biblioteca/`. Lo que escribe va a `backlog/slice-m1/evidencia/m1-01_estados_<fase>.csv`."""
import csv
import hashlib
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
EVIDENCIA = RAIZ / "backlog" / "slice-m1" / "evidencia"
sys.path[:0] = [str(RAIZ / "src"), str(RAIZ / "tests")]

COLUMNAS = ["conjunto", "indicador_id", "anio", "nivel", "territorio_id", "n_muestra", "valor", "ee", "cv", "estado", "accion_final", "reglas"]


def _firma(resultados) -> str:
    return ";".join(f"{r.regla}:{r.accion}:{r.motivo}" for r in resultados if r.regla in ("R-ENC-02", "R-ENC-03", "R-ENC-04", "R-ENC-19"))


def filas_cubo() -> list[dict]:
    from pap.motor.validador.contexto import cargar_contexto
    from pap.motor.validador.nucleo import Cifra
    from pap.motor.validador.validador import evaluar_cifra
    from pap.motor.validador import cargar
    cargar()
    ctx = cargar_contexto(RAIZ)
    cubo = ctx.cubo
    enc = {i for i, d in ctx.indicadores.items() if d.get("naturaleza_dato") == "encuesta_muestral"}
    x = cubo[cubo.indicador_id.isin(enc) & (cubo.linea == "cifra")].sort_values(["indicador_id", "anio", "nivel", "territorio_id"])
    out = []
    for r in x.to_dict("records"):
        fila = {k: (None if v != v else v) for k, v in r.items()}
        q = {"nivel_pedido": fila["nivel"], "territorio_pedido": fila["territorio_nombre"], "anio_pedido": int(fila["anio"]), "rol": "principal",
             "es_principal": True, "intencion_pregunta": "nivel_actual", "id_cifra": "medicion"}
        c = Cifra.desde(fila, ctx.indicadores[fila["indicador_id"]], q)
        ev = evaluar_cifra(c, ctx)
        out.append({"conjunto": "cubo", "indicador_id": fila["indicador_id"], "anio": int(fila["anio"]), "nivel": fila["nivel"],
                    "territorio_id": fila["territorio_id"], "n_muestra": fila["n_muestra"], "valor": fila["valor"], "ee": fila["ee"], "cv": fila["cv"],
                    "estado": ev.estado_cifra, "accion_final": ev.accion_final, "reglas": _firma(ev.resultados)})
    return out


def filas_recetas() -> list[dict]:
    from inferencia import comparar_m10 as cm
    out = []
    for f in cm.filas_90(RAIZ):
        e, g = f["estimacion"], f["compuerta"]
        ind, nivel, terr = f["llave"]
        out.append({"conjunto": "receta", "indicador_id": ind, "anio": 2024, "nivel": nivel, "territorio_id": terr, "n_muestra": e.n,
                    "valor": e.valor * 100, "ee": e.ee * 100, "cv": (e.ee / e.valor if e.valor else None), "estado": g.estado,
                    "accion_final": "", "reglas": ";".join(f"{m.regla}:{m.accion}:{m.codigo}" for m in g.motivos)})
    return out


def medir(fase: str) -> None:
    filas = filas_cubo()
    try:
        filas += filas_recetas()
    except (AssertionError, FileNotFoundError) as e:                       # sin microdatos (otro equipo)
        print(f"recetas no medidas: {type(e).__name__}: {e}")
    ruta = EVIDENCIA / f"m1-01_estados_{fase}.csv"
    with open(ruta, "w", encoding="utf-8", newline="") as sal:
        w = csv.DictWriter(sal, COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows({k: ("" if v is None else v) for k, v in f.items()} for f in filas)
    cubo = RAIZ / "biblioteca" / "indicadores" / "fact_indicador.parquet"
    print(f"{len(filas)} filas ({sum(f['conjunto'] == 'cubo' for f in filas)} del cubo, {sum(f['conjunto'] == 'receta' for f in filas)} de recetas) "
          f"en {ruta.relative_to(RAIZ)}; cubo sha256 {hashlib.sha256(cubo.read_bytes()).hexdigest()[:12]}")
    n = [int(f["n_muestra"]) for f in filas if f["n_muestra"] is not None]
    print(f"n_muestra mínimo {min(n)}; filas con 25 ≤ n ≤ 49: {sum(25 <= v <= 49 for v in n)}; con n < 25: {sum(v < 25 for v in n)}")


def leer(fase: str) -> dict:
    with open(EVIDENCIA / f"m1-01_estados_{fase}.csv", encoding="utf-8", newline="") as f:
        return {(r["conjunto"], r["indicador_id"], r["anio"], r["nivel"], r["territorio_id"]): r for r in csv.DictReader(f)}


def comparar() -> None:
    a, d = leer("antes"), leer("despues")
    assert a.keys() == d.keys(), "no son las mismas filas"
    cambian, valores = [], []
    for k in sorted(a):
        if any(a[k][c] != d[k][c] for c in ("n_muestra", "valor", "ee", "cv")):
            valores.append(k)
        if any(a[k][c] != d[k][c] for c in ("estado", "accion_final", "reglas")):
            cambian.append({"conjunto": k[0], "indicador_id": k[1], "anio": k[2], "nivel": k[3], "territorio_id": k[4],
                            "n_muestra": a[k]["n_muestra"], "valor": a[k]["valor"], "cv": a[k]["cv"],
                            "estado_antes": a[k]["estado"], "estado_despues": d[k]["estado"],
                            "reglas_antes": a[k]["reglas"], "reglas_despues": d[k]["reglas"]})
    cols = ["conjunto", "indicador_id", "anio", "nivel", "territorio_id", "n_muestra", "valor", "cv", "estado_antes", "estado_despues",
            "reglas_antes", "reglas_despues"]
    ruta = EVIDENCIA / "m1-01_cambios_de_estado.csv"
    with open(ruta, "w", encoding="utf-8", newline="") as sal:
        w = csv.DictWriter(sal, cols, lineterminator="\n")
        w.writeheader()
        w.writerows(cambian)
    conj = lambda c: sum(k[0] == c for k in a)                                           # noqa: E731
    print(f"filas medidas: cubo {conj('cubo')}, recetas {conj('receta')}; con cambio de estado o de reglas: {len(cambian)}; "
          f"con cambio de valor, n, ee o cv: {len(valores)}")
    for c in cambian:
        print(" ", c)


if __name__ == "__main__":
    fase = sys.argv[1] if len(sys.argv) > 1 else ""
    if fase in ("antes", "despues"):
        medir(fase)
    elif fase == "comparar":
        comparar()
    else:
        raise SystemExit(__doc__)
