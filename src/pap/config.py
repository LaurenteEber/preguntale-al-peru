"""Rutas del proyecto. La raíz se detecta subiendo desde el directorio actual o con PAP_RAIZ."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .errores import PapError

ZONA_HORARIA = "America/Lima"


@dataclass(frozen=True)
class Rutas:
    raiz: Path

    @property
    def cruda(self) -> Path:
        return self.raiz / "biblioteca" / "cruda"

    @property
    def almacen(self) -> Path:
        return self.cruda / "almacen"

    @property
    def capturas(self) -> Path:
        return self.cruda / "capturas"

    @property
    def bandeja(self) -> Path:
        return self.cruda / "bandeja"

    @property
    def verificaciones(self) -> Path:
        return self.cruda / "verificaciones.jsonl"

    @property
    def indice(self) -> Path:
        return self.cruda / "indice.duckdb"

    @property
    def recetas(self) -> Path:
        return self.raiz / "curados" / "recetas"

    @property
    def catalogo(self) -> Path:
        return self.raiz / "catalogo" / "catalogo_fuentes.json"

    def relativa(self, ruta: Path) -> str:
        """Ruta legible relativa a la raíz (para mensajes)."""
        try:
            return str(Path(ruta).resolve().relative_to(self.raiz))
        except ValueError:
            return str(ruta)


def encontrar_raiz(inicio: Path | None = None) -> Path:
    env = os.environ.get("PAP_RAIZ")
    if env:
        return Path(env).resolve()
    p = Path(inicio or Path.cwd()).resolve()
    for d in (p, *p.parents):
        if (d / "pyproject.toml").is_file() and (d / "biblioteca").is_dir():
            return d
    raise PapError(
        "No encuentro la raíz del proyecto (carpeta con pyproject.toml y biblioteca/). "
        "Ejecuta pap dentro de la carpeta pregunta-al-peru o define PAP_RAIZ."
    )


def rutas(inicio: Path | None = None) -> Rutas:
    return Rutas(encontrar_raiz(inicio))
