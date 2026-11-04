"""Descargadores genéricos. S0: http_file y http_pattern (petición condicional) y manual (instrucciones)."""
from __future__ import annotations

import re
import tempfile
import time
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx

from . import __version__, bitacora, capturas, indice, recetas
from .config import Rutas
from .errores import NoImplementado, PapError
from .registrar import Opciones, Resultado, registrar

AGENTE = f"pap/{__version__} (Pregunta al Peru; descarga de datos publicos)"
REINTENTOS = 3


def instrucciones(rutas: Rutas, receta: dict) -> str:
    pasos = (receta.get("manual") or {}).get("pasos") or [
        f"Abrir {receta.get('access_url')} y descargar el archivo.",
        f"Guardar en biblioteca/cruda/bandeja/{receta['id']}/",
        f"Ejecutar: pap registrar {receta['id']}",
    ]
    (rutas.bandeja / receta["id"]).mkdir(parents=True, exist_ok=True)
    return "\n".join(f"  {i}. {p}" for i, p in enumerate(pasos, 1))


def expandir_patron(patron: str, parametros: dict[str, str]) -> str:
    url = patron
    for k, v in parametros.items():
        url = url.replace("{" + k + "}", v)
    resto = re.findall(r"\{[^}]+\}", url)
    if resto:
        raise PapError(f"Faltan parámetros para el patrón: {', '.join(resto)} (usa --param nombre=valor)")
    return url


def _nombre_archivo(resp: httpx.Response, url: str) -> str:
    cd = resp.headers.get("content-disposition", "")
    m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(r'filename="?([^";]+)"?', cd)
    nombre = unquote(m.group(1)) if m else unquote(Path(urlparse(url).path).name)
    return Path(nombre).name or "descarga"


def _iso(http_fecha: str | None) -> str | None:
    if not http_fecha:
        return None
    try:
        return parsedate_to_datetime(http_fecha).isoformat()
    except (TypeError, ValueError):
        return None


def descargar(rutas: Rutas, source_id: str, url: str | None = None, parametros: dict[str, str] | None = None,
              cliente: httpx.Client | None = None, op: Opciones | None = None) -> Resultado | str:
    """Devuelve un Resultado (si descargó o no hubo cambio) o un texto con instrucciones (si es manual)."""
    receta = recetas.cargar(rutas, source_id)
    estrategia = receta["strategy"]
    if estrategia in ("manual", "owner_file"):
        return instrucciones(rutas, receta)
    if estrategia == "http_file":
        url = url or receta["download_url"]
    elif estrategia == "http_pattern":
        url = url or expandir_patron(receta["url_patron"], parametros or {})
    else:
        raise NoImplementado(
            f"La estrategia «{estrategia}» de {source_id} se construye en un sprint posterior. "
            f"Mientras tanto: descarga manual a biblioteca/cruda/bandeja/{source_id}/ y `pap registrar {source_id}`."
        )

    previo = None
    for _, rec in reversed(capturas.recursos(rutas, source_id)):
        if rec.get("download_url") == url:
            previo = rec
            break
    cabeceras = {"User-Agent": AGENTE}
    if previo and previo.get("http_etag"):
        cabeceras["If-None-Match"] = previo["http_etag"]
    if previo and previo.get("http_last_modified"):
        cabeceras["If-Modified-Since"] = previo["http_last_modified"]

    propio = cliente is None
    cliente = cliente or httpx.Client(follow_redirects=True, timeout=httpx.Timeout(60.0, read=600.0))
    try:
        with tempfile.TemporaryDirectory(prefix="pap-") as d:
            destino = None
            for intento in range(1, REINTENTOS + 1):
                try:
                    with cliente.stream("GET", url, headers=cabeceras) as resp:
                        if resp.status_code == 304:
                            bitacora.anotar(rutas, source_id, "descargar", "sin_cambio", hash=previo["hash"],
                                            detalle=f"304 Not Modified: {url}")
                            indice.reconstruir(rutas)
                            return Resultado(source_id, sin_cambio=[previo["hash"]])
                        if resp.status_code >= 500 and intento < REINTENTOS:
                            time.sleep(2 ** intento)
                            continue
                        if resp.status_code != 200:
                            bitacora.anotar(rutas, source_id, "descargar", "error", detalle=f"HTTP {resp.status_code}: {url}")
                            raise PapError(f"HTTP {resp.status_code} al descargar {url}")
                        destino = Path(d) / _nombre_archivo(resp, str(resp.url))
                        with open(destino, "wb") as f:
                            for bloque in resp.iter_bytes(1024 * 1024):
                                f.write(bloque)
                        http = {
                            "download_url": url,
                            "etag": resp.headers.get("etag"),
                            "last_modified": resp.headers.get("last-modified"),
                            "modified": _iso(resp.headers.get("last-modified")),
                        }
                    break
                except httpx.TransportError as e:
                    if intento == REINTENTOS:
                        bitacora.anotar(rutas, source_id, "descargar", "error", detalle=f"{type(e).__name__}: {url}")
                        raise PapError(f"No se pudo descargar {url}: {e}") from e
                    time.sleep(2 ** intento)
            op = op or Opciones()
            op.http = http
            return registrar(rutas, source_id, [destino], op)
    finally:
        if propio:
            cliente.close()
