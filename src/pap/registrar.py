"""Registrar: archivo → huella → validación de forma → almacén → datapackage.json → verificaciones → índice.

Toda obtención (automática o manual) termina aquí. Es idempotente: un archivo cuya huella ya está
registrada para la fuente no crea nada nuevo; solo anota «sin_cambio».
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from . import __version__, almacen, bitacora, capturas, indice, recetas, validacion
from .config import Rutas
from .errores import PapError
from .util import ahora, fecha_de, git, mediatype_de, sha256, slug


@dataclass
class Opciones:
    issued: str | None = None
    version: str | None = None
    corte: str | None = None
    corte_base: str | None = None
    consultado: str | None = None
    atribuido: str | None = None
    evidencias: list[Path] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)
    forzar: bool = False
    url_descarga: str | None = None
    mover: bool = False  # mover al almacén en lugar de copiar (archivos grandes)
    recurso: str | None = None  # nombre del recurso (p. ej. uno por año cuando se registra archivo por archivo)  # URL exacta del archivo, si se conoce (también en descargas manuales)
    http: dict | None = None  # {download_url, etag, last_modified, modified}


@dataclass
class Resultado:
    source_id: str
    nuevos: list[dict] = field(default_factory=list)
    sin_cambio: list[str] = field(default_factory=list)
    captura: Path | None = None
    avisos: list[str] = field(default_factory=list)


def archivos_en_bandeja(rutas: Rutas, source_id: str) -> list[Path]:
    carpeta = rutas.bandeja / source_id
    if not carpeta.exists():
        return []
    return sorted(
        p for p in carpeta.iterdir()
        if p.is_file() and not p.name.startswith(".") and not p.name.endswith((".part", ".tmp", ".crdownload"))
    )


def _responsable(rutas: Rutas, receta: dict, op: Opciones) -> str:
    if op.atribuido:
        return op.atribuido
    if receta.get("attributed_to"):
        return receta["attributed_to"]
    if op.http:
        return f"pap {__version__}"
    quien = os.environ.get("PAP_RESPONSABLE") or git(rutas.raiz, "config", "user.name") or "desconocido"
    return f"{quien} (manual)"


def _temporal(t: dict) -> str:
    ini, fin = t.get("inicio"), t.get("fin")
    if ini is None and fin is None:
        return "desconocido"
    if ini is None or fin is None or ini == fin:
        return str(ini if ini is not None else fin)
    return f"{ini}–{fin}"


def _nombre_recurso(receta: dict, archivo: Path, varios: bool) -> str:
    base = receta.get("resource_name") or slug(receta["id"])
    return f"{base}-{slug(archivo.stem)}" if varios else base


def _evidencias(rutas: Rutas, archivos: list[Path]) -> list[dict]:
    out = []
    for a in archivos:
        if not a.is_file():
            raise PapError(f"No existe la evidencia {a}")
        h = sha256(a)
        almacen.guardar(rutas, a, h)
        out.append({"original_filename": a.name, "hash": f"sha256:{h}", "path": almacen.ruta_relativa(h)})
    return out


def construir_recurso(rutas: Rutas, receta: dict, archivo: Path, huella: str, nombre: str,
                      validez: dict, anterior: dict | None, op: Opciones, consultado: str,
                      evidencias: list[dict]) -> dict:
    sv = receta.get("source_version") or {}
    dc = receta.get("data_cutoff") or {}
    fmt = validez["formato"]
    rec: dict = {
        "name": nombre,
        "title": receta["dataset_title"],
        "original_filename": archivo.name,
        "path": almacen.ruta_relativa(huella),
        "hash": f"sha256:{huella}",
        "bytes": archivo.stat().st_size,
        "format": fmt,
        "mediatype": mediatype_de(fmt),
    }
    if validez.get("encoding"):
        rec["encoding"] = validez["encoding"]
    rec.update({
        "source_id": receta["id"],
        "publisher": receta["publisher"],
        "dataset_title": receta["dataset_title"],
        "access_url": receta.get("access_url"),
    })
    metodo = receta["method"]
    if op.http is not None or metodo in capturas.METODOS_HTTP or op.url_descarga:
        url = (op.http or {}).get("download_url") or op.url_descarga
        if url and url.endswith("/"):  # carpeta: se completa con el nombre del archivo
            url = url + archivo.name
        rec["download_url"] = url
    version = op.version or sv.get("valor")
    if version:
        rec["source_version"] = version
    rec["source_version_basis"] = "declarada" if op.version else (sv.get("basis") or "ninguna")
    rec["temporal"] = _temporal(receta["temporal"])
    corte = op.corte or dc.get("valor")
    if corte:
        rec["data_cutoff"] = corte
    rec["data_cutoff_basis"] = op.corte_base or ("declarada" if op.corte else (dc.get("basis") or "desconocida"))
    if op.issued or receta.get("issued"):
        rec["issued"] = op.issued or receta.get("issued")
    if op.http and op.http.get("modified"):
        rec["modified"] = op.http["modified"]
    rec["retrieved_at"] = consultado
    if op.http:
        for k_src, k_dst in (("etag", "http_etag"), ("last_modified", "http_last_modified")):
            if op.http.get(k_src):
                rec[k_dst] = op.http[k_src]
    rec.update({
        "method": metodo,
        "recipe": recetas.version(rutas, receta["id"]),
        "attributed_to": _responsable(rutas, receta, op),
        "tool": f"pap {__version__}",
    })
    if evidencias:
        rec["manual_evidence"] = evidencias
    rec["licenses"] = receta["licenses"]
    rec["license_basis"] = receta["license_basis"]
    if receta.get("terms_note"):
        rec["terms_note"] = receta["terms_note"]
    if receta.get("sources"):
        rec["sources"] = receta["sources"]
    rec["previous"] = anterior["hash"] if anterior else None
    rec["change"] = "contenido" if anterior else "nuevo"
    if anterior:
        rec["change_summary"] = f"bytes {anterior.get('bytes')} → {rec['bytes']}"
    rec["spatial"] = receta["spatial"]
    problemas = list(receta.get("known_issues") or []) + list(op.notas)
    if problemas:
        rec["known_issues"] = problemas
    v = {"estado": validez["estado"]}
    if validez["avisos"]:
        v["avisos"] = validez["avisos"]
    rec["validation"] = v
    return rec


def registrar(rutas: Rutas, source_id: str, archivos: list[Path] | None = None,
              op: Opciones | None = None) -> Resultado:
    op = op or Opciones()
    receta = recetas.cargar(rutas, source_id)
    archivos = [Path(a) for a in archivos] if archivos else archivos_en_bandeja(rutas, source_id)
    if not archivos:
        pasos = "\n  ".join((receta.get("manual") or {}).get("pasos", []))
        raise PapError(
            f"No hay archivos para {source_id} en {rutas.relativa(rutas.bandeja / source_id)}."
            + (f"\nPasos de la receta:\n  {pasos}" if pasos else "")
        )
    for a in archivos:
        if not a.is_file():
            raise PapError(f"No existe el archivo {a}")

    res = Resultado(source_id)
    consultado = op.consultado or receta.get("retrieved_at") or ahora()
    varios = len(archivos) > 1
    vistos: set[str] = set()
    pendientes: list[tuple[Path, str, str, dict]] = []

    for a in archivos:
        h = sha256(a)
        if h in vistos:
            continue
        vistos.add(h)
        previo = capturas.buscar_por_huella(rutas, h, source_id)
        if previo:
            res.sin_cambio.append(f"sha256:{h}")
            bitacora.anotar(rutas, source_id, "registrar", "sin_cambio", hash=f"sha256:{h}",
                            captura=rutas.relativa(previo[0].parent), detalle=f"{a.name} ya estaba registrado")
            continue
        validez = validacion.comprobar(a, receta.get("espera"))
        if validez["estado"] == "invalido":
            if not op.forzar:
                bitacora.anotar(rutas, source_id, "registrar", "error", hash=f"sha256:{h}",
                                detalle="; ".join(validez["errores"]))
                raise PapError(
                    f"{a.name} no cumple lo que espera la receta {source_id}:\n  - "
                    + "\n  - ".join(validez["errores"])
                    + "\nRevisa el archivo o, si la receta está desactualizada, corrígela. "
                      "Para registrarlo igual: --forzar"
                )
            validez["avisos"] = validez["errores"] + ["registrado con --forzar"] + validez["avisos"]
            validez["estado"] = "valido_con_avisos"
        pendientes.append((a, h, op.recurso or _nombre_recurso(receta, a, varios), validez))

    if not pendientes:
        indice.reconstruir(rutas)
        return res

    evidencias = _evidencias(rutas, op.evidencias)
    nuevos = []
    movidos: list[tuple[str, Path]] = []  # para deshacer si el registro falla después de mover (RP-06)
    try:
        return _registrar_pendientes(rutas, source_id, receta, pendientes, op, consultado, evidencias, nuevos,
                                     movidos, res)
    except Exception:
        for h, origen in movidos:
            almacen.devolver(rutas, h, origen)
        raise


def _registrar_pendientes(rutas, source_id, receta, pendientes, op, consultado, evidencias, nuevos, movidos, res):
    for a, h, nombre, validez in pendientes:
        tam_original = a.stat().st_size
        nombre_original = a.name
        # Texto grande → <huella>.zst verificado (decisión del dueño del 8/10/2026; umbral en PAP_COMPRIMIR_MIN_MB)
        comprimir = almacen.debe_comprimirse(validez["formato"], tam_original)
        if op.mover:
            _, nuevo = almacen.mover(rutas, a, h, comprimir=comprimir)
            if nuevo:
                movidos.append((h, a))
            a = almacen.ruta_objeto(rutas, h)
        else:
            almacen.guardar(rutas, a, h, comprimir=comprimir)
        ant = capturas.ultimo(rutas, source_id, nombre)
        rec = construir_recurso(rutas, receta, a, h, nombre, validez, ant[1] if ant else None, op, consultado, evidencias)
        if rec.get("download_url") and rec["download_url"].endswith("/" + a.name):
            rec["download_url"] = rec["download_url"][: -len(a.name)] + nombre_original
        rec["original_filename"] = nombre_original
        rec["bytes"] = tam_original
        obj = almacen.ruta_objeto(rutas, h)
        if almacen.comprimido(rutas, h):
            rec["pap_storage"] = {"compression": "zstd", "path": rec["path"] + almacen.SUFIJO_ZST,
                                  "bytes": obj.stat().st_size}
        nuevos.append(rec)
        res.avisos += [f"{nombre_original}: {x}" for x in validez["avisos"]]

    ruta_paq = capturas.escribir(rutas, source_id, fecha_de(consultado), nuevos,
                                 receta["dataset_title"], ahora())
    res.captura = ruta_paq
    res.nuevos = nuevos
    for rec in nuevos:
        bitacora.anotar(rutas, source_id, "registrar", rec["change"], hash=rec["hash"],
                        captura=rutas.relativa(ruta_paq.parent), detalle=rec["original_filename"])
        if rec.get("pap_storage"):  # guardado como .zst: queda anotado (almacen_zst.json + verificaciones.jsonl)
            info = almacen.anotar_zst(rutas, rec["hash"][7:], rec["bytes"], rec["original_filename"])
            bitacora.anotar(rutas, source_id, "comprimir", "ok", hash=rec["hash"],
                            captura=rutas.relativa(ruta_paq.parent),
                            detalle=f"registrado como .zst: {rec['bytes']} → {info['bytes_zst']} bytes; "
                                    f"sha256_zst {info['sha256_zst'][:12]}…; ida y vuelta verificada")
    indice.reconstruir(rutas)
    return res
