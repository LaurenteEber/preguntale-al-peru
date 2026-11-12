"""Utilidades: huellas, fechas, JSON determinista, tipos de archivo, git."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import unicodedata
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import ZONA_HORARIA

BLOQUE = 1024 * 1024

MEDIATYPES = {
    "csv": "text/csv",
    "txt": "text/plain",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xls": "application/vnd.ms-excel",
    "zip": "application/zip",
    "rar": "application/vnd.rar",
    "pdf": "application/pdf",
    "json": "application/json",
    "geojson": "application/geo+json",
    "gpkg": "application/geopackage+sqlite3",
    "dbf": "application/x-dbf",
    "html": "text/html",
    "png": "image/png",
    "jpg": "image/jpeg",
    "parquet": "application/vnd.apache.parquet",
    "sav": "application/x-spss-sav",
    "dta": "application/x-stata-dta",
    "onnx": "application/octet-stream",   # modelos ONNX (protobuf, sin firma fija): sin tipo registrado en IANA
}

# Firmas de los primeros bytes para confirmar que la extensión no miente.
FIRMAS = {
    "xlsx": [b"PK\x03\x04"],
    "zip": [b"PK\x03\x04", b"PK\x05\x06"],
    "pdf": [b"%PDF"],
    "xls": [b"\xd0\xcf\x11\xe0"],
    "rar": [b"Rar!"],
    "png": [b"\x89PNG"],
    "gpkg": [b"SQLite format 3"],
}


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(BLOQUE), b""):
            h.update(bloque)
    return h.hexdigest()


def hoy() -> str:
    """Fecha de hoy en la zona horaria del proyecto (America/Lima), no la del sistema (RP-10)."""
    return datetime.now(ZoneInfo(ZONA_HORARIA)).date().isoformat()


def ahora() -> str:
    return datetime.now(ZoneInfo(ZONA_HORARIA)).isoformat(timespec="seconds")


def fecha_de(marca: str) -> str:
    """YYYY-MM-DD de una marca ISO (fecha u hora)."""
    return str(marca)[:10]


def formato_de(ruta: Path) -> str:
    ext = Path(ruta).suffix.lower().lstrip(".")
    return {"jpeg": "jpg", "htm": "html"}.get(ext, ext) or "desconocido"


def mediatype_de(formato: str) -> str:
    return MEDIATYPES.get(formato, "application/octet-stream")


def firma_valida(ruta: Path, formato: str) -> bool | None:
    firmas = FIRMAS.get(formato)
    if not firmas:
        return None
    with open(ruta, "rb") as f:
        cabeza = f.read(16)
    return any(cabeza.startswith(s) for s in firmas)


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-z0-9._-]+", "-", t.lower()).strip("-._")
    return re.sub(r"-{2,}", "-", t) or "recurso"


def normalizar_texto(texto) -> str:
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t).strip().lower()


def a_texto_fechas(obj):
    """PyYAML convierte 2020-08-24 en date; lo devolvemos a texto ISO."""
    if isinstance(obj, dict):
        return {k: a_texto_fechas(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [a_texto_fechas(v) for v in obj]
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj


def escribir_json(ruta: Path, obj) -> None:
    """Escritura atómica, UTF-8, orden de claves estable (el de construcción)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_name(ruta.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, ruta)


def leer_json(ruta: Path):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def anexar_jsonl(ruta: Path, obj) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")


def git(raiz: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(
            ["git", "-C", str(raiz), *args], capture_output=True, text=True, timeout=20
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() if r.returncode == 0 else None
