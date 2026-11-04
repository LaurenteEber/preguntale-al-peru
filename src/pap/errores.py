class PapError(Exception):
    """Error esperado: se muestra al usuario sin traza."""


class NoImplementado(PapError):
    """Estrategia prevista en la especificación pero aún no construida."""
