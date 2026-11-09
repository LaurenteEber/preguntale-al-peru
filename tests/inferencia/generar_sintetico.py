"""M0-09: microdato sintético de diseño conocido para comparar `svy` con R `survey` y probar las compuertas (sin datos reales).

Uso: uv run python tests/inferencia/generar_sintetico.py   (reescribe tests/inferencia/datos/sintetico.parquet; semilla fija)

Cubre, con un solo archivo:
- 6 estratos (E1…E6) con 1, 2, 3, 4, 6 y 8 UPM; E1 tiene una sola UPM; los ids de UPM («1»…«8») se repiten entre estratos;
- pesos variables y 2 años (2023 y 2024) con las mismas UPM;
- `terr`, el dominio territorial: T1 grande; T2 con p = 0 (con gl > 0); T3 vacío (existe pero ninguna fila entra a `u`); T4 con una UPM por estrato
  dentro del dominio; T5 con n < 25; T6 con CV > 30 %; T7 con p = 1 (con gl > 0); TN con un `y` nulo dentro de `u` (solo 2024);
- `grupo`, un corte de 5 grupos (g1…g5), y `nac`, un dominio único (todo el país).
"""
from pathlib import Path

import numpy as np
import polars as pl

SEMILLA = 20261109
RUTA = Path(__file__).resolve().parent / "datos" / "sintetico.parquet"
UPM_POR_ESTRATO = {"E1": 1, "E2": 2, "E3": 3, "E4": 4, "E5": 6, "E6": 8}
FILAS_POR_UPM = 40
ANIOS = (2023, 2024)


def _asigna(estrato: str, upm: int, i: int) -> str:
    """Dominio territorial de la fila `i` (0–39) de la UPM `upm` del `estrato`."""
    if i < 10 and upm == 2 and estrato != "E1":
        return "T4"                                          # una UPM (la 2) en cada estrato E2…E6: n = 50
    if (estrato, upm) in (("E5", 1), ("E5", 2), ("E6", 2)):
        return "T2"                                          # p = 0: 3 UPM en 2 estratos (gl = 1)
    if estrato == "E2" and upm == 2 and 10 <= i < 15:
        return "T3"                                          # dominio vacío: las cinco filas quedan fuera de u
    if estrato == "E5" and upm == 3 and i >= 20:
        return "T5"                                          # n < 25 (20 filas, menos las que no entran a u: se fuerzan a u)
    if estrato == "E6" and upm in (7, 8) and i >= 10:
        return "T6"                                          # 60 casos en dos UPM con p muy distinta: CV > 30 %
    if (estrato, upm) in (("E5", 5), ("E5", 6), ("E6", 1)) and i < 20:
        return "T7"                                          # p = 1: 60 casos en 3 UPM de 2 estratos (gl = 1)
    return "T1"


def generar() -> pl.DataFrame:
    rng = np.random.default_rng(SEMILLA)
    filas: list[dict] = []
    p_upm = {(h, c): float(rng.beta(3, 7)) for h, k in UPM_POR_ESTRATO.items() for c in range(1, k + 1)}
    for anio in ANIOS:
        for h, k in UPM_POR_ESTRATO.items():
            for c in range(1, k + 1):
                for i in range(FILAS_POR_UPM):
                    terr = _asigna(h, c, i)
                    u = bool(rng.random() < 0.85)
                    if terr == "T3":
                        u = False
                    elif terr in ("T2", "T4", "T5", "T6", "T7"):
                        u = True
                    p = {"T2": 0.0, "T7": 1.0}.get(terr, p_upm[(h, c)])
                    if terr == "T6":
                        p = 0.65 if c == 7 else 0.05
                    y = int(rng.random() < p) if u else None
                    filas.append({"anio": anio, "estrato": h, "upm": str(c), "peso": float(np.round(rng.lognormal(0.0, 0.5) * 1000, 4)),
                                  "u": u, "y": y, "terr": terr, "grupo": f"g{int(rng.choice(5, p=[0.4, 0.25, 0.2, 0.1, 0.05])) + 1}",
                                  "nac": "PE"})
    marco = pl.DataFrame(filas, schema={"anio": pl.Int32, "estrato": pl.String, "upm": pl.String, "peso": pl.Float64, "u": pl.Boolean,
                                        "y": pl.Int8, "terr": pl.String, "grupo": pl.String, "nac": pl.String})
    # TN: tres filas de la única UPM de E1, solo en 2024, dentro de u y con y nulo (un error del llamador: el adaptador debe negarse)
    indice = marco.with_row_index("_i").filter((pl.col("anio") == 2024) & (pl.col("estrato") == "E1") & (pl.col("terr") == "T1"))["_i"][:3].to_list()
    marco = marco.with_row_index("_i").with_columns(
        pl.when(pl.col("_i").is_in(indice)).then(pl.lit("TN")).otherwise(pl.col("terr")).alias("terr"),
        pl.when(pl.col("_i").is_in(indice)).then(True).otherwise(pl.col("u")).alias("u"),
        pl.when(pl.col("_i").is_in(indice)).then(None).otherwise(pl.col("y")).cast(pl.Int8).alias("y")).drop("_i")
    return marco


if __name__ == "__main__":
    RUTA.parent.mkdir(parents=True, exist_ok=True)
    generar().write_parquet(RUTA, compression="snappy", statistics=False)
    print(f"{RUTA} ({RUTA.stat().st_size} bytes)")
