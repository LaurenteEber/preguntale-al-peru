"""Mundo sintético de M1-07: hogares, personas, niños con RECH6, mujeres (REC0111 y RECH5) y los hijos de las entrevistadas (REC21, REC41, REC43, REC44) con las
columnas mínimas que usan las tablas curadas del lote. Las tablas curadas, las relaciones y las unidades son las reales
(`curados/inferencia/`); los Parquet y el índice son los de este archivo.

Hogares h1–h4 (como `sintetico_m0`). Mujeres: m1 y m2 en h1 (30 y 25 años), m3 en h2 (14 años: sin fila en RE516171 ni en RE223132,
como las 12–14 años de la ENDES real), m4 en h3 (40) y m5 en h4 (20). Cada una tiene un hijo (m1 dos) en REC21; los de la
última fila de REC41 son los nacidos en los últimos cinco años; REC44 tiene las mediciones de cuatro de ellos.

C-M1-07-1/2/3 (13/11/2026): RECH5 trae a las mujeres medidas (hemoglobina) de h1–h4; REC21 trae la línea del niño en el hogar (B16: 0 = no vive en
el hogar, nulo = fallecido) y un segundo hijo fallecido de m5 (c5, BIDX 2); REC43 trae a los nacidos de los últimos cinco años de las mujeres (seis,
entre ellos los dos fallecidos) con la diarrea."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import polars as pl
import yaml

from conftest import RAIZ_REAL
from pap.inferencia import tablas_curadas as tc
from pap.inferencia.gramatica import Esquema
from pap.inferencia.verificador import Contexto, ParametrosVerificador, relaciones_desde_yaml

from .sintetico_m0 import RANK, VERIFICADA_2024

COLUMNAS = {
    "RECH0": ["HHID", "HV001", "HV005", "HV015", "HV021", "HV022", "HV024", "HV025", "UBIGEO"],
    "RECH23": ["HHID", "SHREGION", "HV270"],
    "RECH1": ["HHID", "HVIDX", "HV103", "HV104"],
    "RECH4": ["HHID", "IDXH4", "SH11Z"],
    "RECH6": ["HHID", "HC0", "HC1", "HC27", "HC55", "HC57", "HC57A", "HC70"],
    "REC0111": ["CASEID", "HHID", "V003", "V005", "V012", "V015", "V021", "V022", "V024", "V025", "V190"],
    "REC21": ["CASEID", "HHID", "BIDX", "B4", "B5", "B16"],
    "REC41": ["CASEID", "HHID", "MIDX", "M4", "M15", "M17", "M35"],
    "REC43": ["CASEID", "HHID", "HIDX", "H11"],
    "RECH5": ["HHID", "HA0", "HA1", "HA55", "HA57A"],
    "REC44": ["CASEID", "HHID", "HWIDX", "HW1", "HW55", "HW57", "HW70"],
    "RE516171": ["CASEID", "HHID", "V502"],
    "RE223132": ["CASEID", "HHID", "V313"],
}
NUMERICAS = {"HA0", "HA1", "B16", "HIDX", "HV005", "V005", "V012", "HC1", "HC70", "HW1", "HW70", "HV001", "HV021", "V021", "BIDX", "MIDX", "HWIDX", "HVIDX", "HC0",
             "IDXH4", "V003"}
TEXTO = {"HHID", "CASEID", "UBIGEO"}
CATEGORIAS = {"HC57": [1, 2, 3, 4], "HC57A": [1, 2, 3, 4], "HV103": [0, 1], "HC27": [1, 2], "HC55": [0, 1, 2], "HV015": [1, 2, 3], "HV104": [1, 2],
              "SH11Z": [0, 1], "B4": [1, 2], "B5": [0, 1], "M17": [0, 1], "M4": [93, 94, 95], "M35": [0, 1, 2], "H11": [0, 1, 2], "HA55": [0, 3, 4, 6], "HA57A": [1, 2, 3, 4, 9], "M15": [11, 21, 31], "HW55": [0, 1, 2], "HW57": [1, 2, 3, 4],
              "V015": [1, 2, 3, 4, 5, 6, 7], "V502": [0, 1, 2], "V313": [0, 1, 2, 3], "V025": [1, 2], "HV025": [1, 2], "V190": [1, 2, 3, 4, 5], "HV270": [1, 2, 3, 4, 5],
              "SHREGION": [1, 2, 3, 4], "HV024": list(range(1, 26)), "HV022": [1, 2, 3], "V024": list(range(1, 26)), "V022": [1, 2, 3]}


def _tipo(col: str) -> str:
    return "texto" if col in TEXTO else "numerica" if col in NUMERICAS else "categorica"


def variables(estado: str = "revisado") -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    vs, cs, ar = [], [], []
    for a, cols in COLUMNAS.items():
        ar.append({"encuesta": "ENDES", "anio": 2024, "archivo": a, "unidad": "x", "llave": ["HHID"]})
        for c in cols:
            vid = f"ENDES·2024·{a}·{c}"
            vs.append({"var_id": vid, "encuesta": "ENDES", "anio": 2024, "archivo": a, "variable": c, "tipo_valor": _tipo(c),
                       "estado": estado, "tipo_origen": None, "rol_faltante": None})
            cs += [{"var_id": vid, "codigo": str(k), "rol_faltante": None} for k in CATEGORIAS.get(c, [])]
    esq = lambda d, m: pl.DataFrame(d, schema_overrides=m, infer_schema_length=None)
    return (esq(vs, {"tipo_origen": pl.String, "rol_faltante": pl.String}), esq(cs, {"rol_faltante": pl.String}), esq(ar, {}))


def escribir_parquets(carpeta: Path) -> Path:
    d = carpeta / "ENDES" / "2024"
    d.mkdir(parents=True, exist_ok=True)
    hogares = [("h1", 15, 2, "150101"), ("h2", 15, 1, "150201"), ("h3", 7, 1, "070101"), ("h4", 8, 2, "080101")]
    pl.DataFrame({"HHID": [h[0] for h in hogares], "HV001": [1, 1, 2, 3], "HV005": [1_000_000.0, 2_000_000.0, 1_500_000.0, 500_000.0],
                  "HV015": [1.0] * 4, "HV021": [1, 1, 2, 3], "HV022": [1, 1, 2, 3], "HV024": [h[1] for h in hogares],
                  "HV025": [h[2] for h in hogares], "UBIGEO": [h[3] for h in hogares]}).write_parquet(d / "RECH0.parquet")
    pl.DataFrame({"HHID": [h[0] for h in hogares], "SHREGION": [1.0, 2.0, 3.0, 4.0], "HV270": [1.0, 2.0, 3.0, 5.0]}).write_parquet(d / "RECH23.parquet")
    personas = [("h1", 1, 1, 2), ("h1", 2, 1, 1), ("h2", 1, 1, 2), ("h3", 1, 1, 2), ("h4", 1, 0, 2), ("h4", 2, 1, 1)]
    pl.DataFrame({"HHID": [p[0] for p in personas], "HVIDX": [float(p[1]) for p in personas], "HV103": [float(p[2]) for p in personas],
                  "HV104": [float(p[3]) for p in personas]}).write_parquet(d / "RECH1.parquet")
    pl.DataFrame({"HHID": [p[0] for p in personas], "IDXH4": [float(p[1]) for p in personas],
                  "SH11Z": [float(i % 2) for i in range(len(personas))]}).write_parquet(d / "RECH4.parquet")
    ninos = [("h1", 1, 10, 0, 1, 1, -250), ("h1", 2, 20, 0, 4, 4, -100), ("h2", 1, 30, 0, 3, 2, -300), ("h3", 1, 7, 0, 2, 3, 9996),
             ("h4", 1, 12, 0, 4, 4, -50), ("h4", 2, 50, 1, 9, 9, -400)]
    pl.DataFrame({"HHID": [n[0] for n in ninos], "HC0": [float(n[1]) for n in ninos], "HC1": [float(n[2]) for n in ninos], "HC27": [1.0, 2.0, 1.0, 2.0, 1.0, 2.0],
                  "HC55": [float(n[3]) for n in ninos], "HC57": [float(n[4]) for n in ninos], "HC57A": [float(n[5]) for n in ninos],
                  "HC70": [float(n[6]) for n in ninos]}).write_parquet(d / "RECH6.parquet")
    # (caso, hogar, edad, V025, V005, V190)
    mujeres = [("c1", "h1", 30, 2, 1_100_000.0, 1), ("c2", "h1", 25, 2, 900_000.0, 1), ("c3", "h2", 14, 1, 2_000_000.0, 2),
               ("c4", "h3", 40, 1, 1_500_000.0, 3), ("c5", "h4", 20, 2, 500_000.0, 5)]
    pl.DataFrame({"CASEID": [m[0] for m in mujeres], "HHID": [m[1] for m in mujeres], "V003": [1.0] * 5, "V005": [m[4] for m in mujeres],
                  "V012": [float(m[2]) for m in mujeres], "V015": [1.0] * 5, "V021": [1, 1, 1, 2, 3], "V022": [1, 1, 1, 2, 3], "V024": [15, 15, 15, 7, 8],
                  "V025": [float(m[3]) for m in mujeres], "V190": [float(m[5]) for m in mujeres]}).write_parquet(d / "REC0111.parquet")
    # (caso, hogar, índice del nacimiento, sexo, vivo, línea del niño en el hogar)
    hijos = [("c1", "h1", 1, 1, 1, 1.0), ("c1", "h1", 2, 2, 1, 2.0), ("c2", "h1", 1, 2, 1, 0.0), ("c3", "h2", 1, 1, 0, None),
             ("c4", "h3", 1, 2, 1, 1.0), ("c5", "h4", 1, 1, 1, 1.0), ("c5", "h4", 2, 2, 0, None)]
    pl.DataFrame({"CASEID": [h[0] for h in hijos], "HHID": [h[1] for h in hijos], "BIDX": [float(h[2]) for h in hijos],
                  "B4": [float(h[3]) for h in hijos], "B5": [float(h[4]) for h in hijos], "B16": [h[5] for h in hijos]},
                 schema_overrides={"B16": pl.Float64}).write_parquet(d / "REC21.parquet")
    ultimos = [("c1", 1, 1, 21, 95), ("c2", 1, 0, 11, 93), ("c3", 1, 1, 21, 94), ("c4", 1, 0, 31, 95), ("c5", 1, 1, 21, 93)]
    pl.DataFrame({"CASEID": [u[0] for u in ultimos], "HHID": ["h1", "h1", "h2", "h3", "h4"], "MIDX": [float(u[1]) for u in ultimos],
                  "M4": [float(u[4]) for u in ultimos], "M15": [float(u[3]) for u in ultimos],
                  "M17": [float(u[2]) for u in ultimos], "M35": [float(u[2]) for u in ultimos]}).write_parquet(d / "REC41.parquet")
    # (caso, hogar, índice, diarrea): los seis nacimientos de los últimos cinco años, con los dos fallecidos (c3 y el segundo de c5)
    diarrea = [("c1", "h1", 1, 1), ("c2", "h1", 1, 0), ("c3", "h2", 1, 0), ("c4", "h3", 1, 1), ("c5", "h4", 1, 0), ("c5", "h4", 2, 1)]
    pl.DataFrame({"CASEID": [x[0] for x in diarrea], "HHID": [x[1] for x in diarrea], "HIDX": [float(x[2]) for x in diarrea],
                  "H11": [float(x[3]) for x in diarrea]}).write_parquet(d / "REC43.parquet")
    # (hogar, línea, edad, resultado de medir, nivel de anemia): h3 no se midió y h2 tiene 14 años; h4 no durmió en el hogar (RECH1)
    rech5 = [("h1", 1, 30, 0, 3), ("h2", 1, 14, 0, 4), ("h3", 1, 40, 4, 9), ("h4", 1, 20, 0, 1)]
    pl.DataFrame({"HHID": [x[0] for x in rech5], "HA0": [float(x[1]) for x in rech5], "HA1": [float(x[2]) for x in rech5],
                  "HA55": [float(x[3]) for x in rech5], "HA57A": [float(x[4]) for x in rech5]}).write_parquet(d / "RECH5.parquet")
    medidos = [("c1", 1, 10, 0, 1, -250), ("c2", 1, 20, 0, 4, -100), ("c4", 1, 30, 0, 3, -300), ("c5", 1, 12, 0, 4, -50)]
    pl.DataFrame({"CASEID": [m[0] for m in medidos], "HHID": ["h1", "h1", "h3", "h4"], "HWIDX": [float(m[1]) for m in medidos],
                  "HW1": [float(m[2]) for m in medidos], "HW55": [float(m[3]) for m in medidos], "HW57": [float(m[4]) for m in medidos],
                  "HW70": [float(m[5]) for m in medidos]}).write_parquet(d / "REC44.parquet")
    con_filas = [("c1", "h1"), ("c2", "h1"), ("c4", "h3"), ("c5", "h4")]                 # la de 14 años (c3) no tiene fila
    pl.DataFrame({"CASEID": [c[0] for c in con_filas], "HHID": [c[1] for c in con_filas],
                  "V502": [1.0, 1.0, 2.0, 0.0]}).write_parquet(d / "RE516171.parquet")
    pl.DataFrame({"CASEID": [c[0] for c in con_filas], "HHID": [c[1] for c in con_filas],
                  "V313": [3.0, 0.0, 3.0, 1.0]}).write_parquet(d / "RE223132.parquet")
    return carpeta


def contexto(carpeta: Path, estado: str = "revisado", **cambios) -> tuple[Contexto, Path]:
    """Contexto con las tablas curadas reales y las relaciones reales de `archivos_endes_2024.yaml`."""
    micro = escribir_parquets(carpeta / "microdatos")
    v, c, a = variables(estado)
    archivos = yaml.safe_load((RAIZ_REAL / "curados" / "inferencia" / "archivos_endes_2024.yaml").read_text(encoding="utf-8"))
    ctx = Contexto(Esquema.desde_frames(v, c, a), tc.leer_universos(RAIZ_REAL), tc.leer_diseno_muestral(RAIZ_REAL),
                   tc.leer_territorios(RAIZ_REAL), tc.leer_cortes(RAIZ_REAL), tc.leer_perfil_anual(RAIZ_REAL),
                   {("ENDES", 2024): relaciones_desde_yaml(archivos)}, {("INEI-ENDES", 2024, "*"): VERIFICADA_2024}, RANK,
                   ParametrosVerificador.desde_yaml(), micro, tc.leer_mediciones(RAIZ_REAL), tc.leer_unidades(RAIZ_REAL))
    return replace(ctx, **cambios), micro
