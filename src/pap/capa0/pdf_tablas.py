"""Lectura de cuadros numéricos de PDF del INEI (columnas de años alineadas a la derecha, miles con espacio)."""
from __future__ import annotations

import re
from collections import defaultdict

RE_ANIO = re.compile(r"^(19|20)\d\d$")


def lineas(page, tol: float = 2.5) -> list[list[dict]]:
    words = page.extract_words(keep_blank_chars=False, use_text_flow=False, x_tolerance=1.5)
    filas: dict[float, list[dict]] = defaultdict(list)
    claves: list[float] = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        k = next((c for c in claves if abs(c - w["top"]) <= tol), None)
        if k is None:
            k = w["top"]
            claves.append(k)
        filas[k].append(w)
    return [sorted(filas[k], key=lambda w: w["x0"]) for k in sorted(filas)]


def cuadro(page) -> tuple[list[int], list[tuple[str, list[int | None]]], str]:
    """(años, [(etiqueta, valores por año)], texto del encabezado) de una página con columnas de años."""
    ls = lineas(page)
    cab_i = next((i for i, l in enumerate(ls) if sum(bool(RE_ANIO.match(w["text"])) for w in l) >= 3), None)
    if cab_i is None:
        return [], [], ""
    cols = [w for w in ls[cab_i] if RE_ANIO.match(w["text"])]
    anios = [int(w["text"]) for w in cols]
    centros = [(w["x0"] + w["x1"]) / 2 for w in cols]
    sep_miles = 3.5
    x_inicio = cols[0]["x0"] - (cols[1]["x0"] - cols[0]["x0"]) * 0.9
    titulo = " ".join(w["text"] for l in ls[:cab_i] for w in l)
    filas = []
    for l in ls[cab_i + 1:]:
        etiqueta = " ".join(w["text"] for w in l if w["x1"] < x_inicio)
        # 1) unir los grupos de miles: palabra de 3 dígitos muy cerca de la anterior
        nums: list[dict] = []
        for w in l:
            if w["x1"] < x_inicio or not re.fullmatch(r"\d+", w["text"]):
                continue
            if (nums and len(w["text"]) == 3 and w["x0"] - nums[-1]["x1"] < sep_miles
                    and len(nums[-1]["text"].split(" ")[-1]) <= 3):
                nums[-1] = {"text": nums[-1]["text"] + " " + w["text"], "x0": nums[-1]["x0"], "x1": w["x1"]}
            else:
                nums.append(dict(w))
        if not nums:
            if etiqueta:
                filas.append((etiqueta, []))
            continue
        # 2) asignar cada número a la columna cuyo centro está más cerca
        valores: list[int | None] = [None] * len(anios)
        for n in nums:
            c = (n["x0"] + n["x1"]) / 2
            j = min(range(len(centros)), key=lambda i: abs(centros[i] - c))
            valores[j] = int(n["text"].replace(" ", ""))
        filas.append((etiqueta, valores))
    return anios, filas, titulo
