"""M0-08: marcos sintéticos para las pruebas del ejecutor y del pool (sin datos reales; semilla fija)."""
from dataclasses import dataclass

import numpy as np
import polars as pl


def marco_sintetico(n_filas: int = 220_000, n_dominios: int = 275, semilla: int = 7, n_estratos: int = 60, upm_por_estrato: int = 40) -> pl.DataFrame:
    """Una llamada de `n_dominios` territorios sobre `n_filas` filas: la serie de 11 años × 25 departamentos del diseño §14
    (275 dominios en una sola llamada). `y` es 0/1 dentro de `u` y nulo fuera; el diseño es estratificado por conglomerados."""
    rng = np.random.default_rng(semilla)
    estrato = rng.integers(0, n_estratos, n_filas)
    upm = estrato * upm_por_estrato + rng.integers(0, upm_por_estrato, n_filas)
    u = rng.random(n_filas) < 0.8
    y = (rng.random(n_filas) < 0.3).astype(np.int64)
    return pl.DataFrame({"u": u, "y": pl.Series("y", np.where(u, y, -1)).replace(-1, None).cast(pl.Int64),
                         "peso": rng.random(n_filas) + 0.5, "estrato": [f"e{i:03d}" for i in estrato], "upm": [f"c{i:05d}" for i in upm],
                         "territorio": [f"d{i:03d}" for i in rng.integers(0, n_dominios, n_filas)]})


@dataclass(frozen=True)
class FuenteSintetica:
    """Fuente picklable: el trabajador genera el marco (no viaja por la tubería del pool)."""
    n_filas: int = 220_000
    n_dominios: int = 275
    semilla: int = 7

    def cargar(self, anio: int, *, upm_estable: bool = False) -> pl.DataFrame:
        return marco_sintetico(self.n_filas, self.n_dominios, self.semilla)
