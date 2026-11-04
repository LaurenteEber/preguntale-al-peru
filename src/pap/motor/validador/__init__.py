"""Validador de reglas del piloto (P2). Importar `cargar` registra todas las reglas implementadas."""
from .nucleo import REGISTRO  # noqa: F401


def cargar():
    """Importa los módulos de reglas (cada uno registra sus funciones con @regla)."""
    import importlib
    for m in ("reglas_etapa0", "reglas_etapa1_3", "reglas_etapa4", "reglas_etapa6_7", "reglas_etapa5", "reglas_etapa8_10"):
        try:
            importlib.import_module(f"{__name__}.{m}")
        except ModuleNotFoundError as e:
            if e.name != f"{__name__}.{m}":
                raise
    return REGISTRO
