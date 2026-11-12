"""Conexión DuckDB endurecida (M0-07; diseño §22).

Orden obligatorio (si se invierte, DuckDB da error: con el acceso externo apagado ya no deja cambiar los directorios):
1. `SET allowed_directories=[biblioteca/microdatos, biblioteca/variables]`;
2. `SET enable_external_access=false`;
3. `autoinstall_known_extensions=false` y `autoload_known_extensions=false`;
4. `memory_limit` y `threads` (de `curados/inferencia/parametros.yaml`, sección `duckdb`);
5. `SET lock_configuration=true`: desde aquí nada de lo anterior se puede volver a cambiar.

Con esto `read_text('/etc/hosts')`, `COPY … TO` y la lectura fuera de las carpetas permitidas fallan; la lectura de los Parquet
de esas carpetas sí funciona. `.arrow()` devuelve un `pyarrow.RecordBatchReader` (DuckDB 1.5), que `polars.from_arrow` acepta.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ..errores import PapError
from ..zip_seguro import RUTA_PARAMETROS

RAIZ_REPO = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ParametrosDuckdb:
    """`duckdb.*` de curados/inferencia/parametros.yaml (ningún valor fijo en el código)."""
    memoria_mb: int
    threads: int
    carpetas: tuple[str, ...]

    @classmethod
    def desde_yaml(cls, ruta: Path = RUTA_PARAMETROS) -> "ParametrosDuckdb":
        c = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))["duckdb"]
        return cls(memoria_mb=int(c["memoria_mb"]["valor"]), threads=int(c["threads"]["valor"]),
                   carpetas=tuple(c["carpetas_permitidas"]["valor"]))


def _literal(texto: str) -> str:
    return "'" + texto.replace("'", "''") + "'"


def conexion_segura(raiz: Path = RAIZ_REPO, *, p: ParametrosDuckdb | None = None, carpetas: list[Path] | None = None):
    """Conexión en memoria que solo lee `carpetas` (por defecto, las del YAML bajo `raiz`) y queda con la configuración bloqueada."""
    import duckdb

    p = p or ParametrosDuckdb.desde_yaml()
    permitidas = [Path(c).resolve() for c in (carpetas if carpetas is not None else [Path(raiz) / c for c in p.carpetas])]
    con = duckdb.connect(":memory:")
    con.execute("SET allowed_directories=[" + ", ".join(_literal(str(c)) for c in permitidas) + "]")      # 1. antes que 2
    con.execute("SET enable_external_access=false")                                                         # 2
    con.execute("SET autoinstall_known_extensions=false")                                                   # 3
    con.execute("SET autoload_known_extensions=false")
    con.execute(f"SET memory_limit={_literal(f'{p.memoria_mb}MB')}")                                        # 4
    con.execute(f"SET threads={int(p.threads)}")
    con.execute("SET lock_configuration=true")                                                              # 5
    return con


class ErrorSqlNoPermitido(PapError):
    """El SQL que se iba a ejecutar no es exactamente una sentencia SELECT."""


def ejecutar_select(con, sql: str, params=None):
    """Ejecuta `sql` solo si es **una** sentencia de tipo SELECT (H07-1). `allowed_directories` deja escribir en las carpetas
    permitidas (`COPY … TO` a un Parquet existente lo sobrescribiría): todo SQL armado a partir de un plan pasa por aquí.
    El SQL fijo de `conexion_segura` (SET) no pasa por aquí."""
    import duckdb

    sentencias = con.extract_statements(sql)
    if len(sentencias) != 1 or sentencias[0].type != duckdb.StatementType.SELECT:
        tipos = [str(x.type) for x in sentencias]
        raise ErrorSqlNoPermitido(f"solo se ejecuta una sentencia SELECT (llegó: {tipos or 'ninguna'})")
    return con.execute(sql, params if params is not None else [])
