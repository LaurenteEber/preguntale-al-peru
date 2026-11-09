"""M0-09: los casos que se comparan entre `svy` (el adaptador) y R `survey` sobre `datos/sintetico.parquet`.
Los usan el lanzador de R (`pap.inferencia.verificador_r`, que arma el JSON de parámetros) y las pruebas del adaptador."""
from itertools import product
from pathlib import Path

import polars as pl

RUTA_SINTETICO = Path(__file__).resolve().parent / "datos" / "sintetico.parquet"
TERRITORIOS = ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]     # TN (y nulo dentro de u) queda fuera: el adaptador se niega a estimarlo
GRUPOS = [f"g{i}" for i in range(1, 6)]
EXCLUIR = {"terr": ["TN"]}


def _casos() -> list[dict]:
    cruce = [list(d) for d in product([t for t in TERRITORIOS if t != "T3"], GRUPOS)]
    return [
        {"caso": "terr_2023", "anio": 2023, "por": ["terr"], "dominios": [[t] for t in TERRITORIOS]},
        {"caso": "terr_2024", "anio": 2024, "por": ["terr"], "dominios": [[t] for t in TERRITORIOS]},
        {"caso": "grupo_2024", "anio": 2024, "por": ["grupo"], "dominios": [[g] for g in GRUPOS]},
        {"caso": "nac_2024", "anio": 2024, "por": ["nac"], "dominios": [["PE"]]},
        {"caso": "terr_grupo_2024", "anio": 2024, "por": ["terr", "grupo"], "dominios": cruce},
    ]


CASOS = _casos()


def marco(anio: int) -> pl.DataFrame:
    """Las filas del año sin las del dominio TN (la UPM y el estrato siguen declarados por las demás filas)."""
    return pl.read_parquet(RUTA_SINTETICO).filter((pl.col("anio") == anio) & ~pl.col("terr").is_in(EXCLUIR["terr"]))


def parametros_r(salida: Path, datos: Path = RUTA_SINTETICO) -> dict:
    """El JSON que lee `verificar.R`."""
    return {"contrato": "pap-verificador-r/1", "datos": str(datos), "salida": str(salida), "variable": "y", "universo": "u",
            "anio": "anio", "diseno": {"estrato": "estrato", "upm": "upm", "peso": "peso", "nest": True, "lonely_psu": "adjust"},
            "ic": {"metodo": "korn-graubard-nchs", "nivel": 0.95}, "excluir": EXCLUIR, "casos": CASOS}
