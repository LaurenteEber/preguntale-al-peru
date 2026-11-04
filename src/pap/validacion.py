"""Validación de forma de un archivo contra lo que su receta espera (formato, tamaño, columnas)."""
from __future__ import annotations

import csv
import io
from pathlib import Path

from .util import firma_valida, formato_de, normalizar_texto

FILAS_BUSQUEDA = 40


def _leer_texto(ruta: Path, n: int = 256 * 1024) -> tuple[str, str]:
    with open(ruta, "rb") as f:
        crudo = f.read(n)
    for enc in ("utf-8-sig", "utf-8"):
        try:
            return crudo.decode(enc), ("utf-8" if enc == "utf-8-sig" else enc)
        except UnicodeDecodeError as e:
            if e.start > len(crudo) - 4:  # corte a mitad de un carácter multibyte
                return crudo[: e.start].decode(enc), "utf-8"
    return crudo.decode("latin-1"), "latin-1"


def filas_csv(ruta: Path) -> tuple[list[list[str]], str]:
    texto, enc = _leer_texto(ruta)
    lineas = texto.splitlines()[:FILAS_BUSQUEDA]
    muestra = "\n".join(lineas)
    try:
        dialecto = csv.Sniffer().sniff(muestra, delimiters=",;|\t")
        delim = dialecto.delimiter
    except csv.Error:
        delim = ","
    return list(csv.reader(io.StringIO(muestra), delimiter=delim)), enc


def filas_xlsx(ruta: Path, hoja: str | None) -> list[list]:
    import openpyxl

    wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
    try:
        if hoja is not None and hoja not in wb.sheetnames:
            raise KeyError(f"no existe la hoja «{hoja}» (hojas: {', '.join(wb.sheetnames)})")
        ws = wb[hoja] if hoja else wb.worksheets[0]
        return [list(r) for r in ws.iter_rows(max_row=FILAS_BUSQUEDA, values_only=True)]
    finally:
        wb.close()


def faltantes(filas: list[list], columnas: list[str]) -> list[str]:
    """Columnas esperadas que no aparecen en ninguna fila de cabecera candidata.

    Una celda cumple si, normalizada (minúsculas, sin tildes ni saltos), empieza con la columna esperada:
    'Capital legal 1/' cumple 'Capital legal'. Se acepta la fila que contenga más columnas.
    """
    esperadas = [normalizar_texto(c) for c in columnas]
    mejor = list(columnas)
    for fila in filas:
        celdas = [normalizar_texto(c) for c in fila if c is not None]
        falta = [orig for orig, e in zip(columnas, esperadas) if not any(c.startswith(e) for c in celdas)]
        if len(falta) < len(mejor):
            mejor = falta
        if not mejor:
            break
    return mejor


def comprobar(ruta: Path, espera: dict | None) -> dict:
    """Devuelve {estado, avisos, errores, formato, encoding}. estado ∈ valido | valido_con_avisos | invalido."""
    espera = espera or {}
    avisos: list[str] = []
    errores: list[str] = []
    fmt = formato_de(ruta)
    encoding = None
    tam = Path(ruta).stat().st_size

    if tam == 0:
        errores.append("el archivo está vacío")
    formatos = espera.get("formato")
    if formatos and fmt not in formatos:
        errores.append(f"formato «{fmt}» no es uno de los esperados {formatos}")
    firma = firma_valida(ruta, fmt)
    if firma is False:
        errores.append(f"el contenido no corresponde a un archivo {fmt} (firma inicial distinta)")
    rango = espera.get("bytes")
    if rango and not (rango[0] <= tam <= rango[1]):
        errores.append(f"tamaño {tam:,} bytes fuera del rango esperado {rango[0]:,}–{rango[1]:,}")

    if fmt in ("csv", "txt"):
        try:
            filas, encoding = filas_csv(ruta)
        except Exception as e:  # noqa: BLE001
            filas = []
            errores.append(f"no se pudo leer como texto: {e}")
    elif fmt == "xlsx" and espera.get("columnas") and not errores:
        try:
            filas = filas_xlsx(ruta, espera.get("hoja"))
        except Exception as e:  # noqa: BLE001
            filas = []
            errores.append(f"no se pudo leer el Excel: {e}")
    else:
        filas = []
        if espera.get("columnas") and fmt not in ("csv", "txt", "xlsx"):
            avisos.append(f"no se comprueban columnas en archivos {fmt}")

    if espera.get("columnas") and filas:
        falta = faltantes(filas, espera["columnas"])
        if falta:
            errores.append(f"faltan columnas esperadas: {falta}")

    estado = "invalido" if errores else ("valido_con_avisos" if avisos else "valido")
    return {"estado": estado, "avisos": avisos, "errores": errores, "formato": fmt, "encoding": encoding}
