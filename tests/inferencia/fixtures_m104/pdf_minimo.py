"""PDF mínimo hecho a mano para las pruebas de M1-04: texto en posiciones fijas y líneas (para que pdfplumber vea tablas).
No usa ninguna librería de PDF; el texto va en cp1252 con la fuente Helvetica estándar."""
from __future__ import annotations


def _esc(t: str) -> bytes:
    return t.encode("cp1252").replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def construir_pdf(paginas: list[dict], ancho: int = 595, alto: int = 842) -> bytes:
    """`paginas`: lista de {"texto": [(x, y_desde_arriba, texto), ...], "lineas": [(x1, y1, x2, y2), ...]}."""
    objetos: list[bytes] = []
    n_pag = len(paginas)
    # 1 catálogo, 2 páginas, 3 fuente, luego (página, contenido) por cada página
    ids_pag = [4 + 2 * i for i in range(n_pag)]
    objetos.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objetos.append(("<< /Type /Pages /Kids [" + " ".join(f"{i} 0 R" for i in ids_pag) + f"] /Count {n_pag} >>").encode())
    objetos.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    for i, pag in enumerate(paginas):
        partes = []
        for x1, y1, x2, y2 in pag.get("lineas", []):
            partes.append(f"0.5 w {x1} {alto - y1} m {x2} {alto - y2} l S".encode())
        for x, y, t in pag.get("texto", []):
            partes.append(b"BT /F1 9 Tf " + f"{x} {alto - y} Td (".encode() + _esc(t) + b") Tj ET")
        flujo = b"\n".join(partes)
        objetos.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {ancho} {alto}] /Resources << /Font << /F1 3 0 R >> >> "
                       f"/Contents {5 + 2 * i} 0 R >>".encode())
        objetos.append(b"<< /Length " + str(len(flujo)).encode() + b" >>\nstream\n" + flujo + b"\nendstream")
    salida = bytearray(b"%PDF-1.4\n")
    pos = []
    for n, cuerpo in enumerate(objetos, start=1):
        pos.append(len(salida))
        salida += f"{n} 0 obj\n".encode() + cuerpo + b"\nendobj\n"
    inicio = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    for p in pos:
        salida += f"{p:010d} 00000 n \n".encode()
    salida += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio}\n%%EOF\n".encode()
    return bytes(salida)


def pagina_de_preguntas(seccion: str | None, preguntas: list[tuple[str, str, list[str], str]]) -> dict:
    """Una página con el diseño del cuestionario individual: encabezado «PREG. PREGUNTAS Y FILTROS CATEGORÍAS Y CÓDIGOS PASE A»,
    número en x≈39, texto de la pregunta desde x≈71, categorías desde x≈309 y salto en x≈540.
    `preguntas`: (número, texto, categorías, salto)."""
    texto = [(37, 30, "PREG."), (142, 30, "PREGUNTAS Y FILTROS"), (378, 30, "CATEGORÍAS Y CÓDIGOS"), (540, 30, "PASE A")]
    y = 50
    if seccion:
        texto.insert(0, (37, 15, seccion))
    for num, t, cats, salto in preguntas:
        texto.append((39, y, num))
        texto.append((71, y, t))
        for k, c in enumerate(cats):
            texto.append((309, y + 11 * k, c))
        if salto:
            texto.append((540, y, salto))
        y += max(11 * max(len(cats), 1), 11) + 8
    return {"texto": texto}


def pagina_de_diccionario(filas: list[tuple[str, str, str, str, str, str, str, str, str]]) -> dict:
    """Una página con la tabla del diccionario del INEI (9 columnas, con rejilla). Las filas de continuación llevan '' en las
    seis primeras columnas y el valor y su descripción en la 7.ª y la 8.ª."""
    xs = [30, 55, 110, 300, 345, 395, 470, 510, 570]
    cab = ("Nº", "VARIABLE", "DESCRIPCIÓN DE LAS VARIABLES", "TIPO", "LONG.", "RANGO", "VALORES", "DESCRIPCIÓN", "OBS")
    todas = [cab] + list(filas)
    texto, lineas = [], []
    y, alto_fila = 40, 14
    for fila in todas:
        for x, t in zip(xs, fila):
            if t:
                texto.append((x + 2, y + 10, t))
        lineas.append((xs[0], y, xs[-1] + 40, y))
        y += alto_fila
    lineas.append((xs[0], y, xs[-1] + 40, y))
    for x in xs + [xs[-1] + 40]:
        lineas.append((x, 40, x, y))
    return {"texto": texto, "lineas": lineas}
