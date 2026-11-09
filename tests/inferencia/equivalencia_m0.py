"""M0-08: el marco de `endes_nino.parquet` (solo lectura) en la forma que pide el ejecutor, y el oráculo `calculo._svy_niveles`.

`endes_nino.parquet` está fuera de las carpetas que lee DuckDB (`biblioteca/microdatos`), así que estos marcos se arman en Python
(`FuenteMemoria`) con la misma definición de universo y de `y` que el cubo (`capa0.encuestas._en_universo`)."""
import pandas as pd
import polars as pl
import yaml

from conftest import RAIZ_REAL
from pap.capa0.encuestas import _en_universo
from pap.motor import calculo

ENDES_NINO = RAIZ_REAL / "biblioteca" / "estandarizada" / "encuestas" / "endes_nino.parquet"
DEFINICIONES = RAIZ_REAL / "curados" / "capa0" / "definiciones_endes.yaml"
NIVELES = ("nacional", "dominio_subnacional", "departamento")        # los de la historia: nacional, por área y por departamento


def leer_endes_nino() -> pd.DataFrame:
    return pl.read_parquet(ENDES_NINO).to_pandas()


def definicion(clave: str = "anemia_6_35m") -> dict:
    return yaml.safe_load(DEFINICIONES.read_text(encoding="utf-8"))["indicadores"][clave]


def etiquetas(d: pd.DataFrame) -> dict[str, pd.Series]:
    """Las mismas etiquetas de `calculo._calcular_endes` para los tres niveles de la historia."""
    return {"nacional": pd.Series("PE", index=d.index), "dominio_subnacional": d.area,
            "departamento": d.departamento.where(d.departamento != "07")}


def oraculo(d: pd.DataFrame, anio: int, clave: str = "anemia_6_35m") -> dict[tuple[str, str], dict]:
    """(nivel, territorio_id) → fila de `calculo._svy_niveles` (valor y ee en porcentaje, como el cubo)."""
    defi = definicion(clave)
    da = d[d.anio == anio].reset_index(drop=True)
    u = _en_universo(da, anio, defi)
    filas = calculo._svy_niveles(da, da[defi["variable"]], u, etiquetas(da), "id_estrato", "id_conglomerado", "peso")
    return {(f["nivel"], f["territorio_id"]): f for f in filas}


def marco(d: pd.DataFrame, anio: int, nivel: str, clave: str = "anemia_6_35m") -> pl.DataFrame:
    """Marco del ejecutor para un nivel: u, y (nulo fuera de u), peso, estrato, upm y `territorio`."""
    defi = definicion(clave)
    da = d[d.anio == anio].reset_index(drop=True)
    u = _en_universo(da, anio, defi)
    y = da[defi["variable"]].astype(float)
    t = etiquetas(da)[nivel].astype(object).where(etiquetas(da)[nivel].notna(), None)
    return pl.DataFrame({"u": u.to_numpy(), "y": pl.Series(y.where(u).to_numpy()).fill_nan(None).cast(pl.Int64),
                         "peso": da.peso.astype(float).to_numpy(), "estrato": da.id_estrato.astype(str).to_numpy(),
                         "upm": da.id_conglomerado.astype(str).to_numpy(), "territorio": pl.Series(t.to_list(), dtype=pl.String)})
