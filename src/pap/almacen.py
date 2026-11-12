"""Almacén de crudos direccionado por contenido: almacen/sha256/aa/bb/<huella>[.zst].

La huella es SIEMPRE el SHA-256 del archivo ORIGINAL (sin comprimir). Un objeto puede estar guardado de dos formas:

- tal cual: `almacen/sha256/aa/bb/<huella>`
- comprimido con zstd: `almacen/sha256/aa/bb/<huella>.zst` (decisión del dueño del 8/10/2026). Descomprimido da byte a
  byte el original: la huella se verifica descomprimiendo en flujo, sin escribir nada en disco.

El `path` de los datapackage.json es siempre la ruta lógica (sin `.zst`); la forma real se resuelve aquí
(`ruta_objeto`, `resolver`). Así los datapackage.json existentes no cambian al comprimir.
"""
from __future__ import annotations

import errno
import hashlib
import os
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path

import zstandard

from .config import Rutas
from .errores import PapError
from .util import BLOQUE, ahora, escribir_json, leer_json, sha256

SUFIJO_ZST = ".zst"
# Registrar: los archivos de texto que pesen más que esto se guardan comprimidos. Se cambia con la variable de entorno
# PAP_COMPRIMIR_MIN_MB (p. ej. 50) y se desactiva con PAP_COMPRIMIR_MIN_MB=no.
COMPRIMIR_MIN_MB = 10
# Solo texto: Excel, ZIP, PDF, Parquet ya vienen comprimidos (88–100 % medido) y sus lectores no aceptan .zst.
FORMATOS_COMPRIMIBLES = {"csv", "txt"}
NIVEL_ZSTD = 9      # medido 8/10/2026: 10 GB → 0,25 GB; sin --long (los lectores, DuckDB incluido, lo leen sin opciones)
HILOS_ZSTD = 4
# Registro versionado (git) de los objetos guardados como .zst: tamaño y SHA-256 del propio .zst. Permite que
# `pap verificar --rapido` detecte un .zst truncado (la cabecera zstd conserva el tamaño original aunque se corte).
REGISTRO_ZST = "almacen_zst.json"


# ------------------------------------------------------------------ rutas

def ruta_relativa(huella_hex: str) -> str:
    """Ruta LÓGICA relativa a biblioteca/cruda/ (la que va en `path` del datapackage; nunca lleva `.zst`)."""
    return f"almacen/sha256/{huella_hex[:2]}/{huella_hex[2:4]}/{huella_hex}"


def _plano(rutas: Rutas, huella_hex: str) -> Path:
    return rutas.cruda / ruta_relativa(huella_hex)


def _zst(rutas: Rutas, huella_hex: str) -> Path:
    return rutas.cruda / (ruta_relativa(huella_hex) + SUFIJO_ZST)


def ruta_objeto(rutas: Rutas, huella_hex: str) -> Path:
    """Ruta real del objeto: la del original si está; si no, la del `.zst` si está; si no hay ninguno, la lógica."""
    plano = _plano(rutas, huella_hex)
    if plano.exists():
        return plano
    z = _zst(rutas, huella_hex)
    return z if z.exists() else plano


def resolver(rutas: Rutas, path_relativo: str) -> Path:
    """`rutas.cruda / rec["path"]` con la forma real de almacenamiento. Todo lector de crudos debe usar esto.

    DuckDB (read_csv) y pandas (read_csv) reconocen el `.zst` por la extensión y lo leen sin descomprimir a disco."""
    p = rutas.cruda / path_relativo
    if p.exists():
        return p
    z = p.with_name(p.name + SUFIJO_ZST)
    return z if z.exists() else p


def existe(rutas: Rutas, huella_hex: str) -> bool:
    return _plano(rutas, huella_hex).exists() or _zst(rutas, huella_hex).exists()


def comprimido(rutas: Rutas, huella_hex: str) -> bool:
    return ruta_objeto(rutas, huella_hex).name.endswith(SUFIJO_ZST)


# ------------------------------------------------------------------ zstd

def huella_y_tamano(ruta: Path, zst: bool | None = None) -> tuple[str, int]:
    """SHA-256 y tamaño del contenido ORIGINAL: descomprime en flujo si `zst` (por defecto: si termina en `.zst`)."""
    zst = ruta.name.endswith(SUFIJO_ZST) if zst is None else zst
    h = hashlib.sha256()
    n = 0
    with open(ruta, "rb") as f:
        if zst:
            with zstandard.ZstdDecompressor().stream_reader(f) as lector:
                for bloque in iter(lambda: lector.read(BLOQUE), b""):
                    h.update(bloque)
                    n += len(bloque)
        else:
            for bloque in iter(lambda: f.read(BLOQUE), b""):
                h.update(bloque)
                n += len(bloque)
    return h.hexdigest(), n


def tamano_declarado_zst(ruta: Path) -> int | None:
    """Tamaño del original anotado en la cabecera del cuadro zstd (lo escribe `comprimir_archivo`); None si no está."""
    with open(ruta, "rb") as f:
        cabeza = f.read(18)
    try:
        n = zstandard.get_frame_parameters(cabeza).content_size
    except zstandard.ZstdError:
        return None
    return None if n in (zstandard.CONTENTSIZE_UNKNOWN, zstandard.CONTENTSIZE_ERROR) else n


def comprimir_archivo(origen: Path, destino: Path, nivel: int = NIVEL_ZSTD, hilos: int = HILOS_ZSTD) -> int:
    """Comprime `origen` en `destino` (un solo cuadro zstd con el tamaño original en la cabecera). Devuelve bytes escritos."""
    cctx = zstandard.ZstdCompressor(level=nivel, threads=hilos, write_content_size=True, write_checksum=True)
    with open(origen, "rb") as fi, open(destino, "wb") as fo:
        _, escritos = cctx.copy_stream(fi, fo, size=os.fstat(fi.fileno()).st_size)
        fo.flush()
        os.fsync(fo.fileno())
    return escritos


def _solo_lectura(p: Path) -> None:
    try:  # en algunos sistemas de archivos montados no tiene efecto
        os.chmod(p, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    except OSError:
        pass


def _escribible(p: Path) -> None:
    try:
        os.chmod(p, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    except OSError:
        pass


def _verificar_zst(z: Path, huella_hex: str, bytes_esperados: int | None) -> list[str]:
    try:
        h, n = huella_y_tamano(z, zst=True)  # también para el temporal <huella>.zst.tmp
    except zstandard.ZstdError as e:
        return [f"el .zst no se puede descomprimir: {e}"]
    probs = []
    if h != huella_hex:
        probs.append("la huella del .zst descomprimido no coincide con la del original")
    if bytes_esperados is not None and n != bytes_esperados:
        probs.append(f"el .zst descomprimido mide {n} ≠ {bytes_esperados}")
    return probs


def _comprimir_verificado(origen: Path, z: Path, huella_hex: str, bytes_esperados: int,
                          nivel: int = NIVEL_ZSTD, hilos: int = HILOS_ZSTD) -> int:
    """Escribe `<z>.tmp`, comprueba la ida y vuelta (huella y tamaño) y solo entonces lo renombra a `z`.
    Si algo falla, borra solo el temporal y lanza PapError; `origen` nunca se toca."""
    z.parent.mkdir(parents=True, exist_ok=True)
    tmp = z.with_name(z.name + ".tmp")
    try:
        comprimir_archivo(origen, tmp, nivel, hilos)
        probs = _verificar_zst(tmp, huella_hex, bytes_esperados)
    except (OSError, zstandard.ZstdError) as e:  # p. ej. disco lleno: error claro, sin traceback
        tmp.unlink(missing_ok=True)
        raise PapError(f"{huella_hex[:12]}…: {_motivo(e)}; el original quedó intacto") from e
    except BaseException:  # Ctrl-C: se limpia el temporal y se deja pasar
        tmp.unlink(missing_ok=True)
        raise
    if probs:
        tmp.unlink(missing_ok=True)
        raise PapError(f"{huella_hex[:12]}…: la verificación de la compresión falló ({'; '.join(probs)}); "
                       "el original quedó intacto")
    _solo_lectura(tmp)
    os.replace(tmp, z)
    _fsync_dir(z.parent)  # que el renombrado llegue al disco antes de retirar el original
    return z.stat().st_size


def _motivo(e: BaseException) -> str:
    if isinstance(e, OSError) and e.errno == errno.ENOSPC:
        return "disco lleno (libera espacio y vuelve a correr el comando)"
    return f"{type(e).__name__}: {e}"


def _fsync_dir(d: Path) -> None:
    try:
        fd = os.open(d, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:  # algunos sistemas de archivos montados no lo admiten en carpetas
        pass
    finally:
        os.close(fd)


# ------------------------------------------------------------------ registro de .zst

def ruta_registro(rutas: Rutas) -> Path:
    return rutas.cruda / REGISTRO_ZST


def leer_registro(rutas: Rutas) -> dict:
    p = ruta_registro(rutas)
    return (leer_json(p).get("objetos") or {}) if p.exists() else {}


def anotar_zst(rutas: Rutas, huella_hex: str, bytes_original: int, nombre: str | None = None) -> dict:
    """Anota (o actualiza) en almacen_zst.json el tamaño y el SHA-256 del .zst ya verificado."""
    z = _zst(rutas, huella_hex)
    h_zst, n_zst = huella_y_tamano(z, zst=False)
    reg = leer_registro(rutas)
    reg[huella_hex] = {"original_filename": nombre, "bytes": bytes_original, "bytes_zst": n_zst,
                       "sha256_zst": h_zst, "compression": "zstd", "verificado": ahora()}
    p = ruta_registro(rutas)
    otras = {k: v for k, v in (leer_json(p) if p.exists() else {}).items() if k not in ("nota", "objetos")}
    escribir_json(p, {
        "nota": "Objetos del almacén guardados como <huella>.zst. La huella es la del original sin comprimir; "
                "bytes_zst y sha256_zst son los del .zst (para `pap verificar --rapido` y para revisar respaldos). "
                "Lo escribe `pap almacen comprimir` / `pap registrar`; no editar a mano.",
        "objetos": dict(sorted(reg.items())),
        **otras,   # p. ej. `bloques` (pap almacen restaurar/liberar, M0-11)
    })
    return reg[huella_hex]


# ------------------------------------------------------------------ registrar

def umbral_compresion() -> int | None:
    """Bytes a partir de los cuales registrar comprime (None = no comprimir)."""
    v = os.environ.get("PAP_COMPRIMIR_MIN_MB", str(COMPRIMIR_MIN_MB)).strip().lower()
    if v in ("no", "off", "0", "false", ""):
        return None
    try:
        return int(float(v) * 1_000_000)
    except ValueError:
        raise PapError(f"PAP_COMPRIMIR_MIN_MB={v!r}: debe ser un número de MB o «no»") from None


def debe_comprimirse(formato: str, tam: int, umbral: int | None = -1) -> bool:
    umbral = umbral_compresion() if umbral == -1 else umbral
    return umbral is not None and formato in FORMATOS_COMPRIMIBLES and tam > umbral


def guardar(rutas: Rutas, origen: Path, huella_hex: str, comprimir: bool = False) -> tuple[Path, bool]:
    """Copia (o comprime, si `comprimir`) el archivo al almacén si no está. Devuelve (ruta, nuevo).

    El original nunca se mueve ni se borra. Si el objeto ya existe (en cualquier forma) no se toca."""
    if existe(rutas, huella_hex):
        return ruta_objeto(rutas, huella_hex), False
    if comprimir:
        _comprimir_verificado(origen, _zst(rutas, huella_hex), huella_hex, origen.stat().st_size)
        return _zst(rutas, huella_hex), True
    destino = _plano(rutas, huella_hex)
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_name(destino.name + ".tmp")
    shutil.copyfile(origen, tmp)
    copiada = sha256(tmp)
    if copiada != huella_hex:
        tmp.unlink(missing_ok=True)
        raise PapError(f"La copia de {origen} no coincide con su huella (¿cambió durante la copia?)")
    _solo_lectura(tmp)
    os.replace(tmp, destino)
    return destino, True


def mover(rutas: Rutas, origen: Path, huella_hex: str, comprimir: bool = False) -> tuple[Path, bool]:
    """Como guardar(), pero mueve el archivo (mismo disco): para crudos grandes, evita duplicar espacio.

    Con `comprimir`, escribe el `.zst` verificado y solo después borra el origen.
    Si el objeto ya existe, el origen no se toca (el contenido es idéntico por definición de la huella)."""
    if existe(rutas, huella_hex):
        return ruta_objeto(rutas, huella_hex), False
    if comprimir:
        destino, _ = guardar(rutas, origen, huella_hex, comprimir=True)
        origen.unlink()
        return destino, True
    destino = _plano(rutas, huella_hex)
    destino.parent.mkdir(parents=True, exist_ok=True)
    tam = origen.stat().st_size
    try:
        os.replace(origen, destino)
    except OSError:
        # otro disco (EXDEV): copiar y verificar la huella; el origen se borra solo después de verificar (RP-06)
        destino, _ = guardar(rutas, origen, huella_hex)
        origen.unlink()
        return destino, True
    if destino.stat().st_size != tam:  # el renombrado no cambia el contenido; control barato de tamaño
        os.replace(destino, origen)
        raise PapError(f"{origen.name}: el tamaño cambió al moverlo al almacén; se devolvió a su lugar")
    _solo_lectura(destino)
    return destino, True


def devolver(rutas: Rutas, huella_hex: str, origen: Path) -> None:
    """Deshace mover(): devuelve el objeto a su ubicación original (registro fallido después de mover)."""
    if origen.exists():
        return
    plano, z = _plano(rutas, huella_hex), _zst(rutas, huella_hex)
    if plano.exists():
        _escribible(plano)
        os.replace(plano, origen)
    elif z.exists():  # se movió comprimiendo: descomprimir, verificar y solo entonces retirar el .zst
        tmp = origen.with_name(origen.name + ".tmp")
        with open(z, "rb") as fi, open(tmp, "wb") as fo:
            zstandard.ZstdDecompressor().copy_stream(fi, fo)
        if sha256(tmp) != huella_hex:
            tmp.unlink(missing_ok=True)
            raise PapError(f"No se pudo devolver {origen.name}: el .zst no reproduce la huella")
        os.replace(tmp, origen)
        _escribible(z)
        z.unlink()


# ------------------------------------------------------------------ verificar

def comprobar(rutas: Rutas, huella_hex: str, bytes_esperados: int | None, completo: bool = True) -> list[str]:
    """Problemas del objeto (vacío = íntegro). `bytes_esperados` es el tamaño del ORIGINAL.

    Original sin comprimir: tamaño y, si `completo`, huella. Objeto `.zst`: el tamaño del original anotado en la
    cabecera zstd (rápido) y, si `completo`, la huella y el tamaño recalculados descomprimiendo en flujo."""
    plano, z = _plano(rutas, huella_hex), _zst(rutas, huella_hex)
    if not plano.exists() and not z.exists():
        return [f"falta el objeto {ruta_relativa(huella_hex)}"]
    problemas = []
    if plano.exists():
        tam = plano.stat().st_size
        if bytes_esperados is not None and tam != bytes_esperados:
            problemas.append(f"tamaño {tam} ≠ {bytes_esperados} declarado")
        if completo and sha256(plano) != huella_hex:
            problemas.append("la huella SHA-256 no coincide: el archivo fue alterado")
    if z.exists() and (not plano.exists() or completo):
        if completo:
            problemas += [f"{SUFIJO_ZST}: {p}" for p in _verificar_zst(z, huella_hex, bytes_esperados)]
        else:
            n = tamano_declarado_zst(z)
            if n is None:
                problemas.append(".zst sin tamaño original en la cabecera (corre la verificación completa)")
            elif bytes_esperados is not None and n != bytes_esperados:
                problemas.append(f".zst: tamaño original {n} ≠ {bytes_esperados} declarado")
        # tamaño del propio .zst contra el registro (detecta un .zst truncado, también con --rapido)
        reg = leer_registro(rutas).get(huella_hex)
        tam_zst = z.stat().st_size
        if reg is None:
            if not completo:
                problemas.append(f".zst sin anotar en {REGISTRO_ZST} (corre `pap almacen comprimir` o la "
                                 "verificación completa)")
        elif tam_zst != reg.get("bytes_zst"):
            problemas.append(f".zst: mide {tam_zst} ≠ {reg.get('bytes_zst')} anotado en {REGISTRO_ZST} "
                             "(¿truncado o reemplazado?)")
    return problemas


def objetos(rutas: Rutas) -> list[str]:
    """Huellas presentes en el almacén (en cualquier forma)."""
    base = rutas.almacen / "sha256"
    if not base.exists():
        return []
    return sorted({p.name.removesuffix(SUFIJO_ZST) for p in base.glob("*/*/*")
                   if p.is_file() and not p.name.endswith(".tmp")})


def duplicados(rutas: Rutas) -> list[str]:
    """Huellas con original y `.zst` a la vez (compresión interrumpida antes de retirar el original)."""
    return [h for h in objetos(rutas) if _plano(rutas, h).exists() and _zst(rutas, h).exists()]


def temporales(rutas: Rutas) -> list[Path]:
    base = rutas.almacen / "sha256"
    return sorted(base.glob("*/*/*.tmp")) if base.exists() else []


# ------------------------------------------------------------------ pap almacen comprimir

@dataclass
class Paso:
    huella: str
    accion: str          # comprimido | ya_comprimido | retirado_original | ensayo | error | omitido
    bytes_original: int
    bytes_zst: int | None = None
    segundos: float = 0.0
    detalle: str = ""


def candidatos(rutas: Rutas, min_bytes: int) -> list[tuple[str, int, str, str]]:
    """(huella, bytes del original, formato, nombre original) de los objetos de texto referenciados por alguna captura
    con más de `min_bytes`, en cualquier forma (para que el comando sea idempotente)."""
    from . import capturas  # evitar import circular

    vistos: dict[str, tuple[str, int, str, str]] = {}
    for _, rec in capturas.recursos(rutas):
        h = str(rec.get("hash", "")).removeprefix("sha256:")
        fmt = rec.get("format") or ""
        if len(h) != 64 or h in vistos or fmt not in FORMATOS_COMPRIMIBLES:
            continue
        if not existe(rutas, h) and not _zst(rutas, h).with_name(f"{h}{SUFIJO_ZST}.tmp").exists():
            continue
        tam = int(rec.get("bytes") or 0)
        if tam > min_bytes:
            vistos[h] = (h, tam, fmt, rec.get("original_filename", ""))
    return sorted(vistos.values(), key=lambda x: x[1])


def comprimir_objeto(rutas: Rutas, huella_hex: str, bytes_original: int, ensayo: bool = False,
                     nivel: int = NIVEL_ZSTD, hilos: int = HILOS_ZSTD, borrar=None, nombre: str | None = None) -> Paso:
    """Comprime un objeto del almacén. Idempotente y reanudable:

    - solo `.zst` → nada que hacer (si falta en almacen_zst.json, se verifica completo y se anota);
    - original y `.zst` (corte anterior entre renombrar y retirar) → se verifica el `.zst` completo y, si pasa,
      se retira el original;
    - solo `.zst.tmp` (corte de energía tras renombrar sin llegar al disco) → se verifica completo y se renombra;
    - solo original → `.zst.tmp`, ida y vuelta (huella y tamaño), renombrar, fsync, retirar el original.
    Si cualquier verificación falla (o el disco se llena), el original queda intacto y se devuelve accion='error'."""
    import time

    borrar = borrar or (lambda p: (_escribible(p), p.unlink()))
    t0 = time.monotonic()
    plano, z = _plano(rutas, huella_hex), _zst(rutas, huella_hex)
    tmp = z.with_name(z.name + ".tmp")
    paso = Paso(huella_hex, "", bytes_original)

    def fin(accion, detalle=""):
        paso.accion, paso.detalle, paso.segundos = accion, detalle, time.monotonic() - t0
        if z.exists():
            paso.bytes_zst = z.stat().st_size
        return paso

    if ensayo:
        if not plano.exists():
            return fin("ya_comprimido" if z.exists() else ("ensayo" if tmp.exists() else "error"),
                       "" if z.exists() else ("solo queda el .zst.tmp: se verificaría y se renombraría"
                                               if tmp.exists() else "falta el objeto"))
        return fin("ensayo", "hay .zst a medias: se verificaría y se retiraría el original" if z.exists() else "")
    try:
        if not plano.exists():
            if z.exists():
                if huella_hex in leer_registro(rutas):
                    return fin("ya_comprimido")
                probs = _verificar_zst(z, huella_hex, bytes_original)
                if probs:
                    return fin("error", "el .zst no pasa la verificación: " + "; ".join(probs))
                anotar_zst(rutas, huella_hex, bytes_original, nombre)
                return fin("anotado", "ya estaba comprimido: verificado y anotado en " + REGISTRO_ZST)
            if tmp.exists():  # el único resto: verificar completo antes de darlo por bueno
                probs = _verificar_zst(tmp, huella_hex, bytes_original)
                if probs:
                    return fin("error", "solo queda el .zst.tmp y no pasa la verificación (no se toca): "
                               + "; ".join(probs))
                os.replace(tmp, z)
                _fsync_dir(z.parent)
                anotar_zst(rutas, huella_hex, bytes_original, nombre)
                return fin("recuperado", "el .zst.tmp verificado se renombró a .zst")
            return fin("error", "falta el objeto")
        # hay original: los restos .tmp de un corte anterior son nuestros y nunca son la única copia
        tmp.unlink(missing_ok=True)
        if z.exists():
            probs = _verificar_zst(z, huella_hex, bytes_original)
            if probs:
                return fin("error", "el .zst existente no pasa la verificación: " + "; ".join(probs))
        else:
            _comprimir_verificado(plano, z, huella_hex, bytes_original, nivel, hilos)
        anotar_zst(rutas, huella_hex, bytes_original, nombre)
    except PapError as e:
        return fin("error", str(e))
    except (OSError, zstandard.ZstdError) as e:
        return fin("error", f"{_motivo(e)}; el original quedó intacto")
    # Aquí el .zst existe, su ida y vuelta reproduce la huella y el tamaño, y está anotado: recién ahora se retira.
    try:
        borrar(plano)
    except OSError as e:
        return fin("error", f"el .zst está verificado pero no se pudo retirar el original ({_motivo(e)}); "
                            "vuelve a correr el comando")
    return fin("comprimido")
