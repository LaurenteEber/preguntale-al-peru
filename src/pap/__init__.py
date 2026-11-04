"""pap: obtener, registrar, verificar y citar archivos crudos de Pregunta al Perú."""

import pandas as _pd

__version__ = "0.1.0"

# P1 (10/10/2026): svy y polars traen pyarrow. Con pyarrow instalado, pandas 3 guarda las columnas «string» en Arrow y
# sus comparaciones devuelven bool[pyarrow], que no se multiplica por enteros (rompía puentes.py) y podría cambiar tipos
# en la capa 0. Se fija el almacenamiento «python», el mismo que había antes de pyarrow: la capa 0 se comporta igual.
_pd.set_option("mode.string_storage", "python")
