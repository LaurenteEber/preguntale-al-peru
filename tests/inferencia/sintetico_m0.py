"""Contexto sintético para las pruebas de la gramática y del verificador: un índice mínimo y tres Parquet pequeños
(RECH0, RECH1, RECH6) con las columnas que usan las tablas curadas de la ENDES 2024. Las tablas curadas son las reales."""
from pathlib import Path

import polars as pl

from conftest import RAIZ_REAL
from pap.inferencia import tablas_curadas as tc
from pap.inferencia.gramatica import Esquema
from pap.inferencia.plan import UnionPlan
from pap.inferencia.verificador import Contexto, ParametrosVerificador

RELACIONES = [UnionPlan("RECH1", "RECH0", (("HHID", "HHID"),)), UnionPlan("RECH6", "RECH0", (("HHID", "HHID"),)),
              UnionPlan("RECH6", "RECH1", (("HHID", "HHID"), ("HC0", "HVIDX")))]
COLUMNAS = {
    "RECH0": ["HHID", "HV001", "HV005", "HV021", "HV022", "HV024", "HV025", "UBIGEO"],
    "RECH1": ["HHID", "HVIDX", "HV103"],
    "RECH6": ["HHID", "HC0", "HC1", "HC55", "HC57", "HC57A", "HC70"],
}
CATEGORICAS = {"HV024", "HV025", "HV103", "HC55", "HC57", "HC57A", "HC70", "HV022"}
CATEGORIAS = {"HC57": [1, 2, 3, 4], "HC57A": [1, 2, 3, 4], "HV103": [0, 1], "HC55": [0, 1, 2]}


def variables_sinteticas(estado: str = "propuesto") -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    vs, cs, ar = [], [], []
    for a, cols in COLUMNAS.items():
        ar.append({"encuesta": "ENDES", "anio": 2024, "archivo": a, "unidad": "x", "llave": ["HHID"]})
        for c in cols:
            vid = f"ENDES·2024·{a}·{c}"
            vs.append({"var_id": vid, "encuesta": "ENDES", "anio": 2024, "archivo": a, "variable": c,
                       "tipo_valor": "categorica" if c in CATEGORICAS else "numerica", "estado": estado,
                       "tipo_origen": None, "rol_faltante": None})
            for k in CATEGORIAS.get(c, []):
                cs.append({"var_id": vid, "codigo": str(k), "rol_faltante": None})
    esq = lambda d, m: pl.DataFrame(d, schema_overrides=m, infer_schema_length=None)
    return (esq(vs, {"tipo_origen": pl.String, "rol_faltante": pl.String}), esq(cs, {"rol_faltante": pl.String}), esq(ar, {}))


def escribir_parquets(carpeta: Path, variante: str = "base") -> Path:
    """Dos hogares en Lima región (HV024 = 15), uno en el Callao (7), uno en Cusco (8). Variantes que rompen algo a propósito:
    `huerfano` (un niño de universo cuyo hogar no está en RECH0), `duplicado` (RECH1 repite una persona: la unión n:1 duplicaría
    filas) y `nulo` (un niño con HC57A nulo)."""
    destino = carpeta / "ENDES" / "2024"
    destino.mkdir(parents=True, exist_ok=True)
    hogares = [("h1", 15, 2, "150101"), ("h2", 15, 1, "150201"), ("h3", 7, 1, "070101"), ("h4", 8, 2, "080101")]
    pl.DataFrame({"HHID": [h[0] for h in hogares], "HV001": [1, 1, 2, 3], "HV005": [1_000_000.0, 2_000_000.0, 1_500_000.0, 500_000.0],
                  "HV021": [1, 1, 2, 3], "HV022": [1, 1, 2, 3], "HV024": [h[1] for h in hogares],
                  "HV025": [h[2] for h in hogares], "UBIGEO": [h[3] for h in hogares]}).write_parquet(destino / "RECH0.parquet")
    personas = [("h1", 1, 1), ("h1", 2, 1), ("h2", 1, 1), ("h3", 1, 1), ("h4", 1, 0), ("h4", 2, 1)]
    # (hogar, línea, edad, HC55, HC57, HC57A, HC70)
    ninos = [("h1", 1, 10, 0, 1, 1, -250), ("h1", 2, 20, 0, 4, 4, -100), ("h2", 1, 30, 0, 3, 2, -300), ("h3", 1, 7, 0, 2, 3, 9996),
             ("h4", 1, 12, 0, 4, 4, -50), ("h4", 2, 50, 1, 9, 9, -400)]
    if variante == "huerfano":
        personas.append(("h9", 1, 1))
        ninos.append(("h9", 1, 15, 0, 4, 4, 0))
    if variante == "duplicado":
        personas.append(personas[0])
    if variante == "nulo":
        ninos.append(("h2", 2, 20, 0, 4, None, -10))
        personas.append(("h2", 2, 1))
    pl.DataFrame({"HHID": [p[0] for p in personas], "HVIDX": [float(p[1]) for p in personas],
                  "HV103": [float(p[2]) for p in personas]}).write_parquet(destino / "RECH1.parquet")
    pl.DataFrame({"HHID": [n[0] for n in ninos], "HC0": [float(n[1]) for n in ninos], "HC1": [float(n[2]) for n in ninos],
                  "HC55": [float(n[3]) for n in ninos], "HC57": [float(n[4]) for n in ninos], "HC57A": [None if n[5] is None else float(n[5]) for n in ninos],
                  "HC70": [float(n[6]) for n in ninos]}).write_parquet(destino / "RECH6.parquet")
    return carpeta


VERIFICADA_2024 = {"fuente": "INEI-ENDES", "anio": "2024", "modulo": "*", "inferencia_verificada": "true",
                   "nivel_maximo": "departamento", "ambitos_publicados": "LIMA_METROPOLITANA;LIMA_REGION"}
RANK = {"provincia": 3, "departamento": 4, "dominio_subnacional": 5, "nacional": 6, "LIMA_METROPOLITANA": 3, "LIMA_REGION": 3.5,
        "CALLAO": 4, "distrito": 2}


def contexto_sintetico(carpeta: Path, estado: str = "propuesto", variante: str = "base") -> tuple[Contexto, Path]:
    micro = escribir_parquets(carpeta / "microdatos", variante)
    v, c, a = variables_sinteticas(estado)
    ctx = Contexto(Esquema.desde_frames(v, c, a), tc.leer_universos(RAIZ_REAL), tc.leer_diseno_muestral(RAIZ_REAL),
                   tc.leer_territorios(RAIZ_REAL), tc.leer_cortes(RAIZ_REAL), tc.leer_perfil_anual(RAIZ_REAL),
                   {("ENDES", 2024): RELACIONES}, {("INEI-ENDES", 2024, "*"): VERIFICADA_2024}, RANK,
                   ParametrosVerificador.desde_yaml(), micro)
    return ctx, micro
