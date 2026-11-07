"""S1-08 — Comprobaciones automáticas sobre cada respuesta de la matriz (tarea 3 de la historia).

Aquí viven los patrones de «código interno» y la lista de textos visibles; `test_plantillas_intencion.py` los importa en vez de
copiarlos. Cada comprobación devuelve una lista de fallos `{"codigo", "detalle"}` (vacía si todo está bien); no lanza.

  validador        sin errores de ejecución del validador (resultado `metadato_faltante`: una regla no pudo correr)
  capa1_maximo     capa 1 ≤ respuesta.capa1_palabras_max (R-04)
  corrector        sin infracciones de respuesta.infracciones_corrector (acción distinta de «rotular»)
  marcadores       sin `{{…}}`, IDs de regla, de indicador, de cruce, códigos NC-… ni nombres de columnas en el texto visible
  nombres          cada nombre de lugar resuelto escrito como su nombre_mostrado (T-02)
  citas            cada cifra usada tiene su línea en `capa3.para_citar` (P-02); sin cifras, sin porcentajes ni montos visibles
  evolucion        S1-13 (AD-1, H11): una evolución muestra las dos cifras que compara, cada una con su marcador
  cruce            S1-14 (H9): la capa 1 de un cruce no dice «lado a lado» (trae una sola cifra clave, R-04)
  comparaciones    S3-01b (punto 9): toda comparación escrita («más alta», «más baja», «mayor», «menor») coincide con las
                   cifras de la misma respuesta; una comparación que no se sabe comprobar también falla
"""
from __future__ import annotations

import re
import unicodedata

import yaml

CODIGOS = [r"\{\{", r"\}\}", r"\{[a-z_0-9]+\}", r"\bR-[A-Z]+-\d+", r"\bNC-[A-Z]", r"\bCR-\d", r"\b[a-z]+_[a-z0-9]+_[a-z0-9_]+\b",
           r"\b[A-Z]{3,}_[A-Z_]+\b"]
COLUMNAS = ["indicador_id", "territorio_id", "estado_cifra", "semaforo_cifra", "nombre_ciudadano", "ubigeo_inei", "nombre_mostrado",
            "nombre_normalizado", "id_cifra", "fuente_principal", "ic_inf", "ic_sup", "cota_inf", "cota_sup", "n_muestra"]
CLASES = ["respondida", "no_se_puede", "aclaracion", "error"]


def parametros(raiz) -> dict:
    return yaml.safe_load((raiz / "curados" / "motor" / "parametros_motor.yaml").read_text(encoding="utf-8"))


def clase(res: dict) -> str:
    return {"respuesta": "respondida", "no_se_puede": "no_se_puede", "aclaracion": "aclaracion"}[res["tipo"]]


def visible(r: dict) -> list[str]:
    """Todo el texto que ve la persona en una respuesta (capas 1, 2 y 3, «Lo más cercano» y «¿Qué puedo hacer?»)."""
    c = r["capas"]
    out = [c["capa1"]["respuesta_corta"], c["capa1"]["confianza"]["texto"], *c["capa1"]["ojo_al_leer"]]
    k = c["capa1"]["cifra_clave"]
    if k:
        out += [k["valor"], k["texto"], k["fuente"]]
    cerca = c["capa1"].get("lo_mas_cercano")
    if cerca:
        out += [cerca["titulo"], cerca["texto"]]
    q = c["capa1"].get("que_hacer")
    if q:
        out += [q["texto"], q["fuente"]]
    for t in c["capa2"]["mas_contexto"]:
        out += [t["titulo"], t["texto"], t["etiqueta"] or ""]
    out += c["capa2"]["avisos"] + c["capa2"]["limites"] + c["capa3"]["para_citar"]
    for g in c["capa3"]["glosario"]:
        out += [g["termino"], g["definicion"]]
    return out


def sin_tildes(t: str) -> str:
    """Minúsculas y sin tildes ni ñ: para encontrar un lugar escrito de cualquier forma."""
    return "".join(ch for ch in unicodedata.normalize("NFD", t) if not unicodedata.combining(ch)).casefold()


def _fallo(codigo: str, detalle) -> dict:
    return {"codigo": codigo, "detalle": detalle}


# ----------------------------------------------------------------------------------------------------- comprobaciones

def validador(r: dict) -> list[dict]:
    malos = [x for x in r.get("resultados_respuesta") or [] if x.get("motivo") == "metadato_faltante"]
    for c in (r.get("cifras") or {}).values():
        malos += [x for x in c.get("resultados") or [] if isinstance(x, dict) and x.get("motivo") == "metadato_faltante"]
    return [_fallo("validador_error_de_ejecucion", {"regla": x["regla"], "detalle": x.get("detalle")}) for x in malos]


def capa1_maximo(r: dict, p: dict) -> list[dict]:
    n, tope = r["capas"]["capa1"]["palabras"], p["respuesta"]["capa1_palabras_max"]["valor"]
    return [_fallo("capa1_sobre_el_maximo", f"{n} palabras (máximo {tope})")] if n > tope else []


def corrector(r: dict, p: dict) -> list[dict]:
    cuentan = p["respuesta"]["infracciones_corrector"]["valor"]
    return [_fallo("infraccion_del_corrector", {"regla": x["regla"], "accion": x["accion"], "mensaje": x.get("mensaje")})
            for x in r["resultados_respuesta"] if x["regla"] in cuentan and x["accion"] != "rotular"]


def marcadores(r: dict) -> list[dict]:
    out = []
    for t in visible(r):
        for cod in CODIGOS:
            m = re.search(cod, t)
            if m:
                out.append(_fallo("marcador_o_codigo_interno", {"patron": cod, "encontrado": m.group(0), "texto": t[:200]}))
        for col in COLUMNAS:
            if re.search(rf"\b{col}\b", t):
                out.append(_fallo("nombre_de_columna", {"columna": col, "texto": t[:200]}))
    return out


def nombres(r: dict, lugares: list[str]) -> list[dict]:
    """Cada aparición (sin importar tildes ni mayúsculas) de un lugar de `lugares` —sus nombres_mostrados— debe escribirse
    igual que el nombre mostrado (tildes y ñ de T-02)."""
    out = []
    textos = visible(r)
    for nombre in {n for n in lugares if n}:
        patron = re.compile(r"(?<!\w)" + re.escape(sin_tildes(nombre)) + r"(?!\w)")
        for t in textos:
            for m in patron.finditer(sin_tildes(t)):
                escrito = t[m.start():m.end()]
                if escrito.casefold() != nombre.casefold():
                    out.append(_fallo("nombre_mal_escrito", {"esperado": nombre, "escrito": escrito, "texto": t[:200]}))
    return out


MONTO = re.compile(r"(\d[\d\s\u00a0\u202f.,]*\s?%)|(S/)")


def citas(r: dict) -> list[dict]:
    """P-02: cada cifra usada tiene su línea de cita (con su lugar y año) y no hay más líneas que cifras; una respuesta sin
    cifras (no se puede, aclaración) no muestra ningún porcentaje ni monto."""
    cifras = r.get("cifras") or {}
    lineas = r["capas"]["capa3"]["para_citar"]
    out = []
    if r["tipo"] != "respuesta":
        for t in visible(r):
            if MONTO.search(t):
                out.append(_fallo("cifra_sin_cita", {"texto": t[:200], "motivo": "una respuesta sin cifras muestra un porcentaje o un monto"}))
        return out
    if len(lineas) != len(cifras):
        out.append(_fallo("cifra_sin_cita", {"cifras": len(cifras), "citas": len(lineas)}))
    for k, c in cifras.items():
        # el lugar de un homónimo aclarado se cita con su provincia y departamento entre paréntesis (S1-09, H4)
        marca = re.compile(re.escape(f", {c['territorio_nombre']}") + r"( \([^)]*\))?" + re.escape(f", {c['anio']}."))
        if not any(marca.search(x) for x in lineas):
            out.append(_fallo("cifra_sin_cita", {"cifra": k, "buscado": f", {c['territorio_nombre']}, {c['anio']}."}))
    if cifras and not lineas:
        out.append(_fallo("cifra_sin_cita", "hay cifras y ninguna cita"))
    return out


REGLAS_COMPARACION = {"R-ENC-11", "R-ENC-13", "R-ENC-14", "R-CRUCES-04", "R-REG-10", "R-GASTO-09", "R-GASTO-12"}


def evolucion(r: dict) -> list[dict]:
    """S1-13 (AD-1, H11): en una evolución respondida, cada cifra principal cuya comparación no quedó bloqueada se muestra junto
    con la cifra del año con el que se compara; las dos están en las cifras usadas y su marcador va en el texto."""
    if r["tipo"] != "respuesta" or (r.get("consulta") or {}).get("intencion") != "evolucion":
        return []
    cifras, texto, out = r.get("cifras") or {}, r.get("texto_con_marcadores") or "", []
    for i, c in cifras.items():
        comp = c.get("comparacion")
        if c.get("rol") != "principal" or not comp or i in (r.get("comparaciones_bloqueadas") or []) or \
                any(b.get("regla") in REGLAS_COMPARACION for b in c.get("bloqueos_cruce") or []):
            continue
        par = [k for k, x in cifras.items() if k != i and (x["indicador_id"], x["nivel"], str(x["territorio_id"]), int(x["anio"])) ==
               (c["indicador_id"], c["nivel"], str(c["territorio_id"]), int(comp["anio"]))]
        if not par or "{{c:%s}}" % par[0] not in texto or "{{c:%s}}" % i not in texto:
            out.append(_fallo("evolucion_sin_las_dos_cifras", {"cifra": i, "anio_comparado": int(comp["anio"])}))
    return out


def cruce(r: dict) -> list[dict]:
    """S1-14 (H9): la capa 1 de una respuesta de cruce no promete cifras «lado a lado»: la otra cifra está en «Más contexto»."""
    if r["tipo"] != "respuesta" or (r.get("consulta") or {}).get("intencion") != "cruce":
        return []
    c1 = r["capas"]["capa1"]
    textos = [c1["respuesta_corta"], *(c1["ojo_al_leer"] or []), *((c1.get("cifra_clave") or {}).get(k, "") for k in ("valor", "texto"))]
    return [_fallo("cruce_lado_a_lado_en_capa1", t[:200]) for t in textos if "lado a lado" in t.lower()]


# S3-01b (punto 9): comparaciones escritas. Cada frase visible con una palabra de COMPARATIVO debe ser una comparación que se
# sabe comprobar (abajo) o una frase sin comparación entre cifras (NO_COMPARA); si no, falla, para que una comparación nueva
# en un texto no pase sin revisar.
COMPARATIVO = re.compile(r"\bmás\s+(alt|baj)[oa]s?\b|\bmayor(es)?\b|\bmenor(es)?\b", re.IGNORECASE)
NO_COMPARA = [
    re.compile(r"\bmenores de \d"),                                   # «niñas y niños menores de 5 años»
    re.compile(r"dónde es más alto( o más bajo)?"),                     # menú de lo que se puede preguntar
    re.compile(r"valor más alto de"),                                   # ofrecimiento de «no se puede»
    re.compile(r"[Pp]or qué es mayor en un lugar que en el otro"),      # ojo de la comparación: no afirma cuál es mayor
    # ranking: el grupo lo fija la prueba estadística (del INEI o la propia), no una comparación entre dos cifras escritas
    re.compile(r"grupo con .+ más alta"),
    re.compile(r"[Ll]os \w+ con .+ más alta \(\d{4}\)"),
    re.compile(r"se estima que .+ era más alta, sin diferencias"),
    re.compile(r"con el más alto con una prueba estadística"),
]
ANEMIA_ANTERIOR, ANEMIA_VIGENTE = "endes_anemia_6_35m", "endes_anemia_6_35m_oms2024"
FORMA_ANTERIOR_MAS_ALTA = re.compile(r"(anterior|otra forma)[^.]*cifras más altas")
SIEN_MAS_BAJA = re.compile(r"más baja que la de la encuesta")
MAYOR_EN = re.compile(r"fue mayor en (?P<a>.+?) que en (?P<b>.+?),")
EXTREMO_UNO = re.compile(r"En (?P<anio>\d{4}), (?P<lugar>.+?) es (el|la) \w+ con .+? más alta, con diferencia")


def _cifras_de(r: dict, indicador=None, prefijo=None, rol=None) -> list[dict]:
    return [c for c in (r.get("cifras") or {}).values() if c.get("valor") is not None
            and (indicador is None or c["indicador_id"] == indicador)
            and (prefijo is None or c["indicador_id"].startswith(prefijo)) and (rol is None or c.get("rol") == rol)]


def _comprobar_frase(r: dict, t: str) -> list[dict] | None:
    """Los fallos de una frase con comparativo, o None si no es una comparación que se sepa comprobar."""
    if FORMA_ANTERIOR_MAS_ALTA.search(t):          # la forma anterior de medir la anemia da cifras más altas que la vigente
        vig = {(str(c["territorio_id"]), int(c["anio"])): c for c in _cifras_de(r, ANEMIA_VIGENTE)}
        return [_fallo("comparacion_contradice_cifras", {"texto": t[:200], "lugar": a["territorio_nombre"], "anio": int(a["anio"]),
                                                       "anterior": a["valor"], "vigente": v["valor"]})
                for a in _cifras_de(r, ANEMIA_ANTERIOR)
                if (v := vig.get((str(a["territorio_id"]), int(a["anio"])))) and not a["valor"] > v["valor"]]
    if SIEN_MAS_BAJA.search(t):                    # la cifra del SIEN es más baja que la de la ENDES de la misma respuesta
        return [_fallo("comparacion_contradice_cifras", {"texto": t[:200], "sien": s["valor"], "encuesta": e["valor"],
                                                       "lugar": s["territorio_nombre"]})
                for s in _cifras_de(r, prefijo="sien_anemia") for e in _cifras_de(r, prefijo="endes_anemia")
                if int(s["anio"]) == int(e["anio"]) and not s["valor"] < e["valor"]]
    if m := MAYOR_EN.search(t):                    # comparación entre dos lugares: «fue mayor en A que en B»
        val = {c["territorio_nombre"]: c["valor"] for c in _cifras_de(r, rol="principal")}
        a, b = val.get(m["a"]), val.get(m["b"])
        if a is None or b is None:
            return [_fallo("comparacion_sin_cifras", {"texto": t[:200], "lugares": [m["a"], m["b"]]})]
        return [] if a > b else [_fallo("comparacion_contradice_cifras", {"texto": t[:200], m["a"]: a, m["b"]: b})]
    if m := EXTREMO_UNO.search(t):                 # un solo lugar con la cifra más alta: ninguna otra del mismo año la supera
        anio = int(m["anio"])
        del_anio = [c for c in _cifras_de(r) if int(c["anio"]) == anio and c.get("medida") != "cobertura"]
        suya = [c for c in del_anio if c["territorio_nombre"] == m["lugar"]]
        if not suya:
            return [_fallo("comparacion_sin_cifras", {"texto": t[:200], "lugar": m["lugar"]})]
        mas = [c for c in del_anio if c["indicador_id"] == suya[0]["indicador_id"] and c["valor"] > suya[0]["valor"]]
        return [_fallo("comparacion_contradice_cifras", {"texto": t[:200], "lugar": m["lugar"], "mayor": c["territorio_nombre"]})
                for c in mas]
    return None


def comparaciones(r: dict) -> list[dict]:
    """S3-01b (punto 9): cada comparación escrita en el texto visible coincide con las cifras de la misma respuesta."""
    out = []
    for t in visible(r):
        for frase in re.split(r"(?<=[.:;])\s+", t or ""):
            if not COMPARATIVO.search(frase) or any(x.search(frase) for x in NO_COMPARA):
                continue
            fallos = _comprobar_frase(r, frase)
            out += fallos if fallos is not None else [_fallo("comparacion_sin_comprobar", frase[:200])]
    return out


def revisar(res: dict, p: dict, lugares: list[str]) -> list[dict]:
    """Todas las comprobaciones sobre una respuesta con capas (respondida o no_se_puede)."""
    return (validador(res) + capa1_maximo(res, p) + corrector(res, p) + marcadores(res) + nombres(res, lugares) + citas(res)
            + evolucion(res) + cruce(res) + comparaciones(res))
