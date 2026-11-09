"""Apertura segura de los ZIP de las fuentes (M0-00b, control C7; diseño §22).

Antes de leer nada se revisa el ZIP completo: se rechazan las rutas absolutas o con `..`, los enlaces simbólicos, los
miembros cifrados, los tamaños por encima de los límites y las proporciones de compresión de una bomba. Los miembros se
leen en flujo, por bloques, contando los bytes reales (el tamaño declarado en la cabecera puede mentir): nunca hay un
`z.read()` completo. Los límites viven en `curados/inferencia/parametros.yaml` (`almacen.zip_*`).
"""
from __future__ import annotations

import stat
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterator

import yaml

from .errores import PapError

RUTA_PARAMETROS = Path(__file__).resolve().parents[2] / "curados" / "inferencia" / "parametros.yaml"
MB = 1 << 20


class ZipInseguro(PapError):
    """El ZIP o uno de sus miembros no pasa los controles de seguridad."""


@dataclass(frozen=True)
class Limites:
    max_miembro: int
    max_total: int
    proporcion_max: float
    proporcion_desde: int
    bloque: int

    @classmethod
    def desde_yaml(cls, ruta: Path = RUTA_PARAMETROS) -> "Limites":
        a = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))["almacen"]
        return cls(max_miembro=int(a["zip_max_miembro_mb"]["valor"] * MB),
                   max_total=int(a["zip_max_total_mb"]["valor"] * MB),
                   proporcion_max=float(a["zip_proporcion_max"]["valor"]),
                   proporcion_desde=int(a["zip_proporcion_desde_mb"]["valor"] * MB),
                   bloque=int(a["zip_bloque_kb"]["valor"] * 1024))


def _revisar_miembro(info: zipfile.ZipInfo, lim: Limites, origen: str) -> None:
    nombre = info.filename
    ruta = PurePosixPath(nombre.replace("\\", "/"))
    if ruta.is_absolute() or nombre.startswith(("/", "\\")) or (len(nombre) > 1 and nombre[1] == ":") \
            or ".." in ruta.parts:
        raise ZipInseguro(f"{origen}: ruta no permitida en el ZIP: {nombre!r}")
    if stat.S_ISLNK(info.external_attr >> 16):
        raise ZipInseguro(f"{origen}: enlace simbólico en el ZIP: {nombre!r}")
    if info.flag_bits & 0x1:
        raise ZipInseguro(f"{origen}: miembro cifrado en el ZIP: {nombre!r}")
    if info.file_size > lim.max_miembro:
        raise ZipInseguro(f"{origen}: {nombre!r} ocupa {info.file_size / MB:.0f} MB descomprimido "
                          f"(máximo {lim.max_miembro / MB:.0f} MB)")
    if info.file_size >= lim.proporcion_desde and info.file_size > lim.proporcion_max * max(info.compress_size, 1):
        raise ZipInseguro(f"{origen}: {nombre!r} tiene una proporción de compresión de "
                          f"{info.file_size / max(info.compress_size, 1):.0f} (máximo {lim.proporcion_max:.0f})")


class ZipSeguro:
    """ZIP ya revisado. `miembros()` da los nombres (sin directorios); `copiar` y `leer` leen en flujo con tope."""

    def __init__(self, z: zipfile.ZipFile, lim: Limites, origen: str):
        self._z, self._lim, self._origen = z, lim, origen

    def miembros(self) -> list[str]:
        return [i.filename for i in self._z.infolist() if not i.is_dir()]

    def copiar(self, nombre: str, destino: BinaryIO) -> int:
        """Copia el miembro a `destino` por bloques; corta si los bytes reales pasan del tope."""
        info = self._z.getinfo(nombre)
        tope = min(info.file_size, self._lim.max_miembro)
        total = 0
        with self._z.open(info) as f:
            while bloque := f.read(self._lim.bloque):
                total += len(bloque)
                if total > tope:
                    raise ZipInseguro(f"{self._origen}: {nombre!r} da más bytes de los que declara su cabecera")
                destino.write(bloque)
        return total

    def leer(self, nombre: str) -> bytes:
        """Los bytes del miembro, leídos por bloques con tope (para los lectores que necesitan memoria)."""
        import io

        b = io.BytesIO()
        self.copiar(nombre, b)
        return b.getvalue()


@contextmanager
def abrir_zip_seguro(ruta: Path | str, limites: Limites | None = None) -> Iterator[ZipSeguro]:
    """Abre `ruta` y revisa todos sus miembros antes de devolverlo. Lanza `ZipInseguro` si algo no pasa."""
    lim = limites or Limites.desde_yaml()
    origen = Path(ruta).name
    try:
        z = zipfile.ZipFile(ruta)
    except zipfile.BadZipFile as e:
        raise ZipInseguro(f"{origen}: no es un ZIP válido ({e})") from e
    with z:
        total = 0
        for info in z.infolist():
            _revisar_miembro(info, lim, origen)
            total += info.file_size
            if total > lim.max_total:
                raise ZipInseguro(f"{origen}: el ZIP pasa de {lim.max_total / MB:.0f} MB descomprimido")
        yield ZipSeguro(z, lim, origen)
