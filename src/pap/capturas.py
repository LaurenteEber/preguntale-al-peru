"""Capturas: capturas/<source_id>/<fecha>/datapackage.json (Frictionless Data Package v2 + DCAT/PROV)."""
from __future__ import annotations

from pathlib import Path

from frictionless import Package

from . import __version__
from .config import Rutas
from .errores import PapError
from .util import escribir_json, leer_json, slug

PERFIL_V2 = "https://datapackage.org/profiles/2.0/datapackage.json"
NOTA_RUTAS = "Las rutas `path` de los recursos son relativas a biblioteca/cruda/."

# Contrato de metadatos (especificacion_cruda.md §3): campos obligatorios por recurso.
OBLIGATORIOS = [
    "name", "original_filename", "path", "hash", "bytes", "mediatype",
    "source_id", "publisher", "dataset_title", "source_version_basis", "temporal",
    "data_cutoff_basis", "retrieved_at", "method", "recipe", "attributed_to",
    "licenses", "license_basis", "change", "spatial", "validation",
]
# Obligatorios que pueden valer null, pero la clave debe estar.
CLAVE_PRESENTE = ["access_url", "previous"]
BASES = {
    "source_version_basis": {"declarada", "inferida", "ninguna"},
    "data_cutoff_basis": {"declarada", "max_fecha_en_datos", "desconocida"},
    "license_basis": {"declarada_en_pagina", "norma_general", "no_declarada"},
    "change": {"contenido", "esquema", "url", "sin_cambio", "nuevo"},
}
METODOS_HTTP = {"http_directo", "http_patron", "microdatos_encuesta", "geoservicio"}


def iterar(rutas: Rutas):
    """(ruta_json, paquete) de todas las capturas, en orden de carpeta."""
    if not rutas.capturas.exists():
        return
    for ruta in sorted(rutas.capturas.glob("*/*/datapackage.json")):
        yield ruta, leer_json(ruta)


def recursos(rutas: Rutas, source_id: str | None = None) -> list[tuple[Path, dict]]:
    out = []
    for ruta, paq in iterar(rutas):
        for rec in paq.get("resources", []):
            if source_id is None or rec.get("source_id") == source_id:
                out.append((ruta, rec))
    out.sort(key=lambda x: _orden(x[0], x[1]))
    return out


def _orden(ruta: Path, rec: dict):
    """Orden cronológico robusto (RP-05): fecha de consulta normalizada a America/Lima (una fecha sin hora vale
    00:00 de Lima) y, a igual fecha, el sufijo numérico de la carpeta de captura (2026-10-06-10 después de -2)."""
    import re
    from datetime import datetime
    from zoneinfo import ZoneInfo
    txt = rec.get("retrieved_at") or "1900-01-01"
    try:
        d = datetime.fromisoformat(txt)
    except ValueError:
        d = datetime(1900, 1, 1)
    if d.tzinfo is None:
        d = d.replace(tzinfo=ZoneInfo("America/Lima"))
    carpeta = ruta.parent.name
    m = re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:-(\d+))?", carpeta)
    sufijo = int(m.group(1) or 1) if m else 0
    return (d.timestamp(), carpeta[:10], sufijo, str(ruta))


def buscar_por_huella(rutas: Rutas, huella: str, source_id: str | None = None) -> tuple[Path, dict] | None:
    huella = huella if huella.startswith("sha256:") else f"sha256:{huella}"
    for ruta, rec in recursos(rutas, source_id):
        if rec.get("hash") == huella:
            return ruta, rec
    return None


def buscar_por_prefijo(rutas: Rutas, prefijo: str) -> list[tuple[Path, dict]]:
    prefijo = prefijo.removeprefix("sha256:").lower()
    return [(r, rec) for r, rec in recursos(rutas) if rec.get("hash", "").removeprefix("sha256:").startswith(prefijo)]


def ultimo(rutas: Rutas, source_id: str, nombre: str | None = None) -> tuple[Path, dict] | None:
    candidatos = [x for x in recursos(rutas, source_id) if nombre is None or x[1].get("name") == nombre]
    return candidatos[-1] if candidatos else None


def nueva_carpeta(rutas: Rutas, source_id: str, fecha: str) -> Path:
    base = rutas.capturas / source_id
    carpeta = base / fecha
    n = 2
    while carpeta.exists():
        carpeta = base / f"{fecha}-{n}"
        n += 1
    return carpeta


def errores_paquete(paquete: dict) -> list[str]:
    """Frictionless (descriptor v2) + contrato propio de metadatos."""
    errs = []
    reporte = Package.validate_descriptor(paquete)
    if not reporte.valid:
        for e in reporte.errors:
            errs.append(f"frictionless: {e.message}")
    if paquete.get("$schema") != PERFIL_V2:
        errs.append("el paquete no declara el perfil Data Package v2")
    for i, rec in enumerate(paquete.get("resources", [])):
        quien = rec.get("name", f"recurso {i}")
        for campo in OBLIGATORIOS:
            if rec.get(campo) in (None, "", []):
                errs.append(f"{quien}: falta el campo obligatorio «{campo}»")
        for campo in CLAVE_PRESENTE:
            if campo not in rec:
                errs.append(f"{quien}: falta la clave «{campo}» (puede ser null)")
        for campo, valores in BASES.items():
            if rec.get(campo) is not None and rec[campo] not in valores:
                errs.append(f"{quien}: «{campo}» = {rec[campo]!r} no es uno de {sorted(valores)}")
        if rec.get("method") in METODOS_HTTP and "download_url" not in rec:
            errs.append(f"{quien}: método {rec['method']} exige la clave «download_url»")
        if rec.get("mediatype") == "text/csv" and not rec.get("encoding"):
            errs.append(f"{quien}: un CSV debe declarar «encoding»")
        h = str(rec.get("hash", ""))
        if not (h.startswith("sha256:") and len(h) == 71):
            errs.append(f"{quien}: «hash» debe ser sha256:<64 hex>")
        elif rec.get("path") != f"almacen/sha256/{h[7:9]}/{h[9:11]}/{h[7:]}":
            errs.append(f"{quien}: «path» no corresponde a su huella")
        # `path`, `hash` y `bytes` describen siempre el ORIGINAL; la forma de guardado va aparte (§3.1 de la
        # especificación). Sin `pap_storage` el recurso se registró sin comprimir (puede haberse comprimido después:
        # la forma vigente la resuelve el almacén).
        alm = rec.get("pap_storage")
        if alm is not None:
            if not isinstance(alm, dict) or alm.get("compression") != "zstd":
                errs.append(f"{quien}: «pap_storage.compression» debe ser 'zstd'")
            elif alm.get("path") != f"{rec.get('path')}.zst":
                errs.append(f"{quien}: «pap_storage.path» debe ser «path» + '.zst'")
            elif not isinstance(alm.get("bytes"), int) or alm["bytes"] <= 0:
                errs.append(f"{quien}: «pap_storage.bytes» debe ser el tamaño del .zst")
    return errs


def armar_paquete(source_id: str, carpeta: Path, recursos_: list[dict], titulo: str, creado: str) -> dict:
    return {
        "$schema": PERFIL_V2,
        "name": slug(f"{source_id}-{carpeta.name}"),
        "title": titulo,
        "created": creado,
        "keywords": [source_id],
        "pap": {"version": __version__, "nota": NOTA_RUTAS},
        "resources": recursos_,
    }


def escribir(rutas: Rutas, source_id: str, fecha: str, recursos_: list[dict], titulo: str, creado: str) -> Path:
    carpeta = nueva_carpeta(rutas, source_id, fecha)
    paquete = armar_paquete(source_id, carpeta, recursos_, titulo, creado)
    errs = errores_paquete(paquete)
    if errs:
        raise PapError("El datapackage.json no pasa la validación:\n  - " + "\n  - ".join(errs))
    ruta = carpeta / "datapackage.json"
    escribir_json(ruta, paquete)
    return ruta
