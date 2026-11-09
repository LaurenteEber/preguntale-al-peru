"""M0-10: las 3 recetas de 2024 por el camino nuevo contra las 90 filas del cubo, redondeadas (criterio de la definición de hecho,
punto 1) y sin redondear contra `calculo._svy_niveles` (|dif| ≤ 1e-12). Solo lectura de `endes_nino.parquet` y de los microdatos.

Uso (en el Mac): `uv run python tests/inferencia/comparar_m10.py` escribe `backlog/slice-m0/evidencia/m0-10_recetas_vs_cubo.csv`."""
import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RAIZ / "tests"), str(RAIZ / "src")]

from inferencia import equivalencia_m0 as eq                                          # noqa: E402
from pap.inferencia import recetas as rc                                              # noqa: E402
from pap.inferencia.ejecutor import Ejecutor, PoolEjecutor                            # noqa: E402
from pap.motor.calculo import ENDES_DEF                                               # noqa: E402

SALIDA = RAIZ / "backlog" / "slice-m0" / "evidencia" / "m0-10_recetas_vs_cubo.csv"


def dif_sin_redondear(e, o: dict) -> dict[str, float]:
    """Nueva estimación menos la fila de `_svy_niveles`, sin redondear (valor, ee, cv e IC en porcentaje, como el oráculo)."""
    nuevo = rc.en_unidades_del_cubo(e)
    ef_o = e.n if o["n_efectivo"] is None else min(e.n, o["n_efectivo"])
    dif = {"valor": nuevo["valor"] - o["valor"], "ee": nuevo["ee"] - o["ee"], "ic_inf": nuevo["ic_inf"] - o["ic_inf"],
           "ic_sup": nuevo["ic_sup"] - o["ic_sup"], "deff": nuevo["deff"] - o["deff"], "gl": e.gl - o["gl"], "n_muestra": e.n - o["n_muestra"],
           "n_efectivo": min(e.n, nuevo["n_efectivo"]) - ef_o}
    dif["cv"] = 0.0 if nuevo["cv"] is None and o["cv"] is None else nuevo["cv"] - o["cv"]
    return dif


def filas_90(raiz: Path = RAIZ) -> list[dict]:
    """Las 90 filas con todo lo comparado: por receta, la estimación, la fila del cubo, las diferencias, el oráculo y las compuertas."""
    p = rc.ParametrosRecetas.desde_yaml()
    cubo = rc.leer_csv(raiz / rc.FILAS_CUBO_2024, ("indicador_id", "nivel", "territorio_id"))
    estados = rc.leer_csv(raiz / rc.ESTADOS_CUBO_2024, ("indicador_id", "nivel", "territorio_id"))
    nino = eq.leer_endes_nino()
    salida = []
    with PoolEjecutor(raiz=raiz) as pool:
        ejecutor = Ejecutor(pool, raiz=raiz)
        for receta in rc.leer_recetas(raiz):
            estimaciones = rc.calcular(receta, 2024, raiz, ejecutor=ejecutor)
            doradas = rc.reproducir_doradas(receta, estimaciones)
            compuertas = {(f.nivel, f.territorio_id): f.compuerta for f in rc.compuertas_de(receta, estimaciones, doradas, raiz)}
            oraculo = eq.oraculo_completo(nino, 2024, ENDES_DEF[receta.id])
            for nivel, e in estimaciones:
                llave = (receta.indicador_id, nivel, e.dominio[0])
                g = compuertas[(nivel, e.dominio[0])]
                salida.append({"llave": llave, "estimacion": e, "cubo": cubo[llave], "estado_cubo": estados[llave],
                               "diferencias": rc.comparar_fila(e, cubo[llave], p), "sin_redondear": dif_sin_redondear(e, oraculo[(nivel, e.dominio[0])]),
                               "compuerta": g, "reglas": rc.firma_reglas(g)})
    return salida


def escribir_csv(filas: list[dict], ruta: Path = SALIDA) -> None:
    cols = ["indicador", "nivel", "territorio"]
    for c in rc.COLUMNAS:
        cols += [f"cubo_{c}", f"nuevo_{c}", f"dif_{c}", f"ok_{c}"]
    cols += [f"dif_sin_redondear_{c}" for c in rc.COLUMNAS] + ["ok_sin_redondear", "estado_cubo", "estado_nuevo", "reglas_cubo", "reglas_nuevo",
                                                             "ok_compuertas", "ok_fila"]
    tol = rc.ParametrosRecetas.desde_yaml().oraculo_tolerancia
    f = lambda x: "" if x is None else repr(x)                                          # noqa: E731
    with open(ruta, "w", encoding="utf-8", newline="") as sal:
        w = csv.writer(sal, lineterminator="\n")
        w.writerow(cols)
        for r in sorted(filas, key=lambda r: r["llave"]):
            fila = list(r["llave"])
            for d in r["diferencias"]:
                fila += [f(d.cubo), f(d.nuevo), f(d.dif), d.ok]
            fila += [f(r["sin_redondear"][c]) for c in rc.COLUMNAS]
            ok_sr = all(abs(v) <= tol for v in r["sin_redondear"].values())
            ok_c = r["compuerta"].estado == r["estado_cubo"]["estado"] and r["reglas"] == r["estado_cubo"]["reglas"]
            fila += [ok_sr, r["estado_cubo"]["estado"], r["compuerta"].estado, r["estado_cubo"]["reglas"], r["reglas"], ok_c,
                     ok_sr and ok_c and all(d.ok for d in r["diferencias"])]
            w.writerow(fila)


if __name__ == "__main__":
    filas = filas_90()
    escribir_csv(filas)
    print(f"{len(filas)} filas en {SALIDA.relative_to(RAIZ)}")
