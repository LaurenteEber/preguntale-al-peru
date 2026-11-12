"""Acceso a los crudos registrados: siempre la última captura de cada fuente, con su huella para la trazabilidad."""
from __future__ import annotations

import io
import re
from dataclasses import dataclass
from pathlib import Path

from .. import almacen, capturas
from ..config import Rutas
from ..errores import PapError
from ..zip_seguro import abrir_zip_seguro


@dataclass(frozen=True)
class Insumo:
    source_id: str
    nombre: str
    hash: str
    ruta: Path  # ruta real en el almacén: puede terminar en .zst (almacen.resolver); la huella es la del original
    original_filename: str
    issued: str | None
    retrieved_at: str
    corte: str | None = None  # data_cutoff declarado en el datapackage


# ------------------------------------------------------------------ insumos fijados (RP-05)
ACTUALIZAR_LOCK = False  # lo activa `pap construir … --actualizar-insumos`
TIPOS_NO_CRUDOS = ("CAPA0:", "CURADO", "ESTANDARIZADA:")


def _ruta_lock(rutas: Rutas) -> Path:
    return rutas.raiz / "curados" / "insumos.lock.yaml"


def _lock(rutas: Rutas) -> dict:
    import yaml
    r = _ruta_lock(rutas)
    return (yaml.safe_load(r.read_text(encoding="utf-8")) or {}) if r.exists() else {}


def filtrar_por_lock(rutas: Rutas, source_id: str, recs: list[dict]) -> list[dict]:
    """Si el lock fija huellas para la fuente, solo valen esas (una captura nueva no cambia el siguiente build
    sin aviso). Con --actualizar-insumos se usan las más recientes y el lock se reescribe."""
    fijadas = set(_lock(rutas).get(source_id) or [])
    if ACTUALIZAR_LOCK or not fijadas:
        return recs
    elegidas = [r for r in recs if r["hash"] in fijadas]
    nuevas = [r for r in recs if r["hash"] not in fijadas]
    if nuevas and elegidas and recs.index(nuevas[-1]) > recs.index(elegidas[-1]):
        import sys
        print(f"Aviso: {source_id} tiene una captura más reciente que la fijada en insumos.lock.yaml "
              f"({nuevas[-1]['original_filename']}); se usa la fijada. Para cambiar: --actualizar-insumos",
              file=sys.stderr)
    return elegidas


def escribir_lock(rutas: Rutas, usados: list) -> None:
    import yaml
    lock = _lock(rutas)
    por_fuente: dict[str, set] = {}
    for i in usados:
        if not i.source_id.startswith(TIPOS_NO_CRUDOS):
            por_fuente.setdefault(i.source_id, set()).add(i.hash)
    cambio = False
    for f, hs in por_fuente.items():
        previo = set(lock.get(f) or [])
        nuevo = hs if ACTUALIZAR_LOCK else (previo | hs)
        if nuevo != previo:
            lock[f] = sorted(nuevo)
            cambio = True
    if cambio:
        cab = ("# Huellas de los crudos con que se construyó la capa 0 (RP-05). `pap construir` usa exactamente\n"
               "# estas; para tomar capturas nuevas: pap construir <sprint> --actualizar-insumos\n")
        _ruta_lock(rutas).write_text(cab + yaml.safe_dump(dict(sorted(lock.items())), allow_unicode=True),
                                     encoding="utf-8")


def ultimo(rutas: Rutas, source_id: str, patron_archivo: str | None = None, recurso: str | None = None) -> Insumo:
    """Última captura de la fuente (dentro de las fijadas en el lock); con patrón, el último recurso cuyo nombre
    original lo cumpla; con `recurso`, solo los recursos con ese nombre (p. ej. para no tomar la documentación de la
    fuente —diccionario, metadatos— como si fuera el archivo de datos, también con --actualizar-insumos)."""
    candidatos = filtrar_por_lock(rutas, source_id, [
        rec for _, rec in capturas.recursos(rutas, source_id)
        if (patron_archivo is None or re.search(patron_archivo, rec["original_filename"], re.I))
        and (recurso is None or rec.get("name") == recurso)
    ])
    if not candidatos:
        raise PapError(
            f"Falta el insumo {source_id}" + (f" ({patron_archivo})" if patron_archivo else "")
            + (f" (recurso {recurso})" if recurso else "")
            + f". Regístralo primero: pap revisar {source_id}"
        )
    rec = candidatos[-1]
    corte = rec.get("data_cutoff") if rec.get("data_cutoff_basis") != "desconocida" else None
    return Insumo(source_id, rec["name"], rec["hash"], almacen.resolver(rutas, rec["path"]), rec["original_filename"],
                  rec.get("issued"), rec["retrieved_at"], corte)


def miembro_zip(insumo: Insumo, patron: str) -> tuple[str, bytes]:
    with abrir_zip_seguro(insumo.ruta) as z:
        nombres = [n for n in z.miembros() if re.search(patron, n, re.I)]
        if len(nombres) != 1:
            raise PapError(f"{insumo.source_id}: se esperaba 1 miembro que cumpla {patron!r}, hay {len(nombres)}")
        return nombres[0], z.leer(nombres[0])


def miembros_zip(insumo: Insumo, patron: str) -> list[tuple[str, bytes]]:
    with abrir_zip_seguro(insumo.ruta) as z:
        return [(n, z.leer(n)) for n in sorted(z.miembros()) if re.search(patron, n, re.I)]


def como_archivo(datos: bytes) -> io.BytesIO:
    return io.BytesIO(datos)


# ------------------------------------------------------------------ insumos que no son crudos (RP-01)

def _sha256(ruta: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return "sha256:" + h.hexdigest()


def tabla(rutas: Rutas, nombre: str) -> Insumo:
    """Tabla de la capa 0 usada como insumo de otro sprint. Exige que el Parquet en disco sea exactamente el que
    registró el manifiesto del sprint que la produjo (si no, hay que reconstruir en orden)."""
    import json

    from .salida import carpetas_con_manifiesto

    candidatas = [c for c in carpetas_con_manifiesto(rutas) if (c / f"{nombre}.parquet").exists()]
    if not candidatas:
        raise PapError(f"Falta la tabla {nombre}: constrúyela primero (pap construir …)")
    carpeta = candidatas[0]
    ruta = carpeta / f"{nombre}.parquet"
    for man in sorted(carpeta.glob("manifiesto_*.json")):
        m = json.loads(man.read_text(encoding="utf-8"))
        reg = m.get("tablas", {}).get(nombre)
        if reg is None:
            continue
        actual = _sha256(ruta)
        if actual != reg["hash"]:
            raise PapError(f"{nombre}.parquet no coincide con {man.name} (huella {actual[:19]}… ≠ {reg['hash'][:19]}…). "
                           f"Reconstruye {m['sprint']} antes de seguir.")
        return Insumo(f"CAPA0:{m['sprint']}", nombre, actual, ruta, ruta.name, m.get("construido"), m.get("construido"))
    raise PapError(f"Ningún manifiesto registra la tabla {nombre}")


def curado(rutas: Rutas, nombre: str) -> Insumo:
    """Dato curado a mano y versionado en git (curados/capa0/), identificado por su huella."""
    ruta = rutas.raiz / "curados" / "capa0" / nombre
    if not ruta.exists():
        raise PapError(f"Falta el dato curado {ruta}")
    return Insumo("CURADO", nombre, _sha256(ruta), ruta, nombre, None, None)
