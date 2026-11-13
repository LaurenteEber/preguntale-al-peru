"""M1-04 — Texto de los cuestionarios y diccionarios de la ENDES 2024 y su vínculo con las variables del índice.

Qué hace este módulo (sin LLM; el LLM está en `cuestionarios_lote.py`):
- `leer_pdf`: lee un PDF con pdfplumber **en el subproceso aislado** (`lector_aislado`, modo `pdf`; mismos topes de tiempo y
  memoria que los SAV/DTA) y devuelve, por página, las palabras con su posición y, si se pide, las tablas.
- `preguntas_de_paginas`: arma las preguntas de un cuestionario (número, texto, opciones, saltos, sección y página) a partir de
  la posición de cada palabra: el número va en la columna izquierda, el texto en la segunda y las categorías en la tercera.
- `diccionario_de_paginas`: arma las variables de un «Diccionario - <tabla>.pdf» (variable, etiqueta, categorías, rango).
- `vincular_por_regla`: el vínculo que no necesita LLM (número de pregunta en el código o en la etiqueta de la variable).
Nada de esto calcula cifras: son textos de apoyo para el índice y quedan en `propuesto` (M1-04, tarea 6).
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from ..errores import PapError
from ..zip_seguro import RUTA_PARAMETROS
from .almacen import Parametros, ejecutar_aislado


# ------------------------------------------------------------------ lector aislado

def leer_pdf(entrada: Path | str, p: Parametros, *, tablas: bool = False, max_paginas: int | None = None) -> list[dict]:
    """Páginas del PDF: `{"n", "ancho", "alto", "palabras": [[texto, x0, arriba], …], "tablas": […]}`. Corre en el subproceso
    aislado con los topes de `conversion.*`; si los pasa, lanza `LectorAbortado`."""
    entrada = Path(entrada).resolve()      # el subproceso corre en otra carpeta
    with tempfile.TemporaryDirectory(prefix="pap-pdf-") as d:
        d = Path(d)
        spec = {"modo": "pdf", "entrada": str(entrada), "tablas": bool(tablas), "max_paginas": max_paginas or 0,
                "resultado": str(d / "resultado.json")}
        (d / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
        ej = ejecutar_aislado([sys.executable, "-I", "-m", "pap.inferencia.lector_aislado", str(d / "spec.json")], p, cwd=d)
        ruta = d / "resultado.json"
        res = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
        if ej.returncode != 0 or "error" in res:
            raise PapError(f"{entrada.name}: " + (res.get("error") or
                           f"el lector terminó con código {ej.returncode}: {ej.stderr.strip()[-600:]}"))
    return res["paginas"]


# ------------------------------------------------------------------ parámetros

@dataclass(frozen=True)
class ParametrosCuestionarios:
    """`cuestionarios.*` de curados/inferencia/parametros.yaml (ningún valor fijo en el código)."""
    numero: re.Pattern
    numero_x_max: float
    numero_tolerancia: float
    texto_margen: float
    linea_tolerancia_y: float
    categorias_x_defecto_prop: float
    categorias_margen: float
    salto_x_defecto_prop: float
    texto_max_caracteres: int
    opciones_max: int
    seccion: re.Pattern
    paginas_especiales: tuple = ()   # rangos de páginas con sección fija: anexos sin encabezado «SECCIÓN» y el calendario

    @classmethod
    def desde_yaml(cls, ruta: Path = RUTA_PARAMETROS) -> "ParametrosCuestionarios":
        c = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))["cuestionarios"]
        v = lambda k: c[k]["valor"]
        return cls(numero=re.compile(v("numero_patron")), numero_x_max=float(v("numero_x_max")),
                   numero_tolerancia=float(v("numero_tolerancia")), texto_margen=float(v("texto_margen")),
                   linea_tolerancia_y=float(v("linea_tolerancia_y")),
                   categorias_x_defecto_prop=float(v("categorias_x_defecto_prop")), categorias_margen=float(v("categorias_margen")),
                   salto_x_defecto_prop=float(v("salto_x_defecto_prop")), texto_max_caracteres=int(v("texto_max_caracteres")),
                   opciones_max=int(v("opciones_max")), seccion=re.compile(v("seccion_patron")),
                   paginas_especiales=tuple(c.get("paginas_especiales", {}).get("valor") or ()))


# ------------------------------------------------------------------ preguntas

@dataclass
class Pregunta:
    cuestionario: str          # hogar | individual | salud
    numero: str                # «325B»
    texto: str
    seccion: str
    pagina: int
    opciones: list[str] = field(default_factory=list)      # «03 PÍLDORA»
    saltos: list[str] = field(default_factory=list)        # números de pregunta a los que pasa
    cortada: bool = False                                  # el texto pasó de `texto_max_caracteres` y se cortó
    tipo: str = "pregunta"                                 # «matriz»: página de columnas (1) (2)… del listado; el texto es el encabezado de toda la página;
                                                           # «calendario»: una página del calendario de la mujer, con su texto

    @property
    def id(self) -> str:
        return f"{self.cuestionario}:{self.numero}"


_HOYOS = re.compile(r"[.…_]{3,}|(?:\.\s?){3,}")                  # guías de puntos o rayas hasta el código
_PASE = re.compile(r"PASE\s+A\s+(?:LA\s+PREGUNTA\s+)?(\d{1,3}[A-Z]?\d?)", re.I)
_CODIGO_FINAL = re.compile(r"^(.*?)[\s.…_]*?(\d(?:\s?\.*\s?\d)?|[A-Z])\s*$")


def _limpiar_guias(t: str) -> str:
    return " ".join(_HOYOS.sub(" ", t).split())


def _lineas(palabras: list[list], tol: float) -> list[list[tuple[float, str]]]:
    """Agrupa palabras [texto, x0, arriba] en líneas por altura y las ordena de izquierda a derecha."""
    grupos: list[tuple[float, list]] = []
    for t, x, y in sorted(palabras, key=lambda w: (w[2], w[1])):
        if grupos and abs(grupos[-1][0] - y) <= tol:
            grupos[-1][1].append((x, t))
        else:
            grupos.append((y, [(x, t)]))
    return [sorted(g) for _, g in grupos]


_LIDER = re.compile(r"[.…]{4,}")


def _x_categorias(lineas, ancho: float, pc: ParametrosCuestionarios) -> float:
    """Dónde empiezan las categorías en la página: la columna donde más palabras traen guías de puntos hacia el código (en la mitad
    derecha de la página; las categorías de una página arrancan casi todas en la misma columna), menos un margen. Sin guías, una
    fracción del ancho."""
    cuenta: dict[int, list[float]] = {}
    for l in lineas:
        for x, t in l:
            if _LIDER.search(t) and x > ancho * 0.25:
                cuenta.setdefault(round(x / 4), []).append(x)
    if not cuenta:
        return ancho * pc.categorias_x_defecto_prop
    mejor = max(cuenta, key=lambda k: (len(cuenta[k]), -k))
    return min(cuenta[mejor]) - pc.categorias_margen


def _opcion(linea_texto: str) -> str | None:
    """«PÍLDORA........ 03» → «03 PÍLDORA». Sin código, solo la etiqueta; sin etiqueta, None."""
    crudo = " ".join(linea_texto.split())
    if not crudo or not re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]", crudo):
        return None
    m = _CODIGO_FINAL.match(crudo)
    codigo = None
    if m and (_HOYOS.search(crudo) or re.search(r"\s\d{1,2}$", crudo)):
        codigo = re.sub(r"[\s.…]", "", m.group(2))
    etiqueta = _limpiar_guias(m.group(1) if codigo else crudo)
    etiqueta = re.sub(r"[\s_]+$", "", etiqueta)
    if not etiqueta:
        return None
    return f"{codigo} {etiqueta}" if codigo else etiqueta


def preguntas_de_paginas(paginas: list[dict], cuestionario: str, pc: ParametrosCuestionarios | None = None) -> list[Pregunta]:
    """Preguntas de un cuestionario a partir de la salida de `leer_pdf`. Una pregunta empieza donde hay un número de pregunta en la
    columna izquierda de la página; su texto es lo que sigue en la segunda columna, las opciones lo de la tercera (hasta la columna
    «PASE A») y los saltos lo de la última o un «PASE A <n>» del texto. La sección vigente es la última línea «SECCIÓN …» vista. Las
    páginas sin números en columna (las matrices del listado del hogar) no dan preguntas. Las páginas de `paginas_especiales` llevan la
    sección de su rango (un anexo sin encabezado no hereda la sección anterior, y la página siguiente vuelve a la vigente); las de tipo
    «calendario» dan una sola entrada por página con su texto (número `C<página>`)."""
    pc = pc or ParametrosCuestionarios.desde_yaml()
    preguntas: list[Pregunta] = []
    especiales = {n: e for e in pc.paginas_especiales if e["cuestionario"] == cuestionario
                  for n in range(int(e["desde"]), int(e["hasta"]) + 1)}
    vigente = ""
    for pag in paginas:
        lineas = _lineas(pag["palabras"], pc.linea_tolerancia_y)
        for l in lineas:
            txt = " ".join(t for _, t in l)
            if pc.seccion.match(txt):
                vigente = " ".join(txt.split())
        especial = especiales.get(pag["n"])
        seccion = especial["seccion"] if especial else vigente
        if especial and especial["tipo"] == "calendario":
            texto = " ".join(" ".join(t for _, t in l) for l in lineas)
            texto = " ".join(texto.split())
            preguntas.append(Pregunta(cuestionario, f"C{pag['n']}", texto[:pc.texto_max_caracteres], seccion, pag["n"], [], [],
                                      len(texto) > pc.texto_max_caracteres, "calendario"))
            continue
        # columna de los números: los candidatos (primera palabra de línea, a la izquierda, con texto de más de 2 letras a su derecha)
        cand = []
        for i, l in enumerate(lineas):
            x, t = l[0]
            resto = " ".join(w for _, w in l[1:])
            if x <= pc.numero_x_max and pc.numero.match(t) and re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ¿]{3,}", resto) \
                    and (len(l) > 1 and l[1][0] - x >= pc.texto_margen or len(l) == 1):
                cand.append((i, x))
            elif x <= pc.numero_x_max and pc.numero.match(t) and len(l) == 1:
                cand.append((i, x))
        cabecera = {t for l in lineas for _, t in l} >= {"PREGUNTAS", "FILTROS"}
        if not seccion and not cabecera:
            continue                                      # la carátula: sus recuadros numerados no son preguntas
        matriz = _matriz(pag, lineas, seccion, pc)
        if matriz:
            matriz.cuestionario = cuestionario
            preguntas.append(matriz)
        if not cand:
            continue
        # la columna es la más repetida (en pasos de 6 puntos); lo que se aleja de ella es un código dentro del texto
        columnas: dict[int, int] = {}
        for _, x in cand:
            columnas[round(x / 6)] = columnas.get(round(x / 6), 0) + 1
        x_col = max(columnas, key=columnas.get) * 6
        inicios = [i for i, x in cand if abs(x - x_col) <= pc.numero_tolerancia]
        if not inicios:
            continue
        x_cat = _x_categorias(lineas, pag["ancho"], pc)
        pase = [x for l in lineas for x, t in l if t == "PASE"]
        x_salto = (min(pase) - 5) if pase else pag["ancho"] * pc.salto_x_defecto_prop
        for k, i in enumerate(inicios):
            fin = inicios[k + 1] if k + 1 < len(inicios) else len(lineas)
            numero = lineas[i][0][1]
            stem, ops, saltos, todo = [], [], [], []
            for j in range(i, fin):
                l = lineas[j][1:] if j == i else lineas[j]
                izq = [(x, t) for x, t in l if x_col + pc.texto_margen < x < x_cat and not _HOYOS.fullmatch(t)]
                med = [(x, t) for x, t in l if x_cat <= x < x_salto]
                der = [(x, t) for x, t in l if x >= x_salto]
                if izq:
                    stem.append(_limpiar_guias(" ".join(t for _, t in izq)))
                if med:
                    o = _opcion(" ".join(t for _, t in med))
                    if o:
                        ops.append(o)
                saltos += [t for _, t in der if pc.numero.match(t)]
                todo.append(" ".join(t for _, t in l))
            saltos += _PASE.findall(" ".join(todo))
            texto = " ".join(s for s in stem if s)
            cortada = len(texto) > pc.texto_max_caracteres
            preguntas.append(Pregunta(cuestionario, numero, texto[:pc.texto_max_caracteres].rstrip(), seccion, pag["n"],
                                      ops[:pc.opciones_max], list(dict.fromkeys(saltos)), cortada))
    return _depurar(preguntas)


_COLUMNA = re.compile(r"^\(\d{1,2}[A-Z]?\)$")


def _matriz(pag: dict, lineas, seccion: str, pc: ParametrosCuestionarios) -> Pregunta | None:
    """Una página con una fila de números de columna «(1) (2) (3) …» es una matriz (el listado del hogar): sus preguntas son las
    columnas y no se pueden separar con fiabilidad. Se guarda el encabezado de la página como una sola pregunta de tipo «matriz»
    (número `M<página>`), para que el vínculo de sus variables sea al menos a nivel de página."""
    for i, l in enumerate(lineas):
        if sum(1 for _, t in l if _COLUMNA.match(t)) >= 3:
            arriba = " ".join(" ".join(t for _, t in lin) for lin in lineas[:i])
            texto = " ".join(arriba.split())
            return Pregunta("", f"M{pag['n']}", texto[:pc.texto_max_caracteres], seccion, pag["n"], [], [],
                            len(texto) > pc.texto_max_caracteres, "matriz")
    return None


def _depurar(preguntas: list[Pregunta]) -> list[Pregunta]:
    """(1) (La carátula ya se descartó página por página.) (2) Una pregunta que se repite en
    varias páginas (la misma tabla para la 1.ª, 2.ª y 3.ª persona) queda una sola vez: la de texto más largo. (3) Un salto solo vale
    si nombra una pregunta del mismo cuestionario, y distinta de la que salta."""
    con_seccion = list(preguntas)
    por_numero: dict[str, Pregunta] = {}
    for q in con_seccion:
        if q.numero not in por_numero or len(q.texto) > len(por_numero[q.numero].texto):
            por_numero[q.numero] = q
    for q in por_numero.values():
        q.saltos = [t for t in q.saltos if t in por_numero and t != q.numero]
    orden = {id(q): i for i, q in enumerate(con_seccion)}
    return sorted(por_numero.values(), key=lambda q: orden[id(q)])


# ------------------------------------------------------------------ manual de la entrevistadora

def fragmentos_del_manual(paginas: list[dict], numeros: list[str], ancho: int = 300, max_por_numero: int = 3) -> dict[str, list[dict]]:
    """Apoyo para los saltos cuando el cuestionario no basta (M1-04, tarea 5): de las páginas del Manual de la Entrevistadora
    (`leer_pdf`), solo los fragmentos que nombran «pregunta <n>» para los números pedidos, con la página. El manual **no** se guarda
    ni se indexa entero: quien llama pide unos pocos números y recibe unos pocos fragmentos."""
    out: dict[str, list[dict]] = {n: [] for n in numeros}
    for pag in paginas:
        texto = " ".join(" ".join(t for _, t in l) for l in _lineas(pag["palabras"], 2.5))
        for n in numeros:
            if len(out[n]) >= max_por_numero:
                continue
            m = re.search(rf"\bpreguntas?\s+(?:[\w\d,y ]{{0,20}}?\b)?{re.escape(n)}\b", texto, re.I)
            if m:
                a, b = max(m.start() - ancho // 2, 0), min(m.end() + ancho // 2, len(texto))
                out[n].append({"pagina": pag["n"], "texto": texto[a:b].strip()})
    return out


# ------------------------------------------------------------------ diccionarios

@dataclass
class VariableDic:
    tabla: str
    codigo: str
    etiqueta: str
    rango: str = ""
    obs: str = ""
    categorias: list[tuple[str, str]] = field(default_factory=list)
    orden: int = 0


def _celda(x) -> str:
    return " ".join(str(x or "").split())


def diccionario_de_paginas(paginas: list[dict], tabla: str) -> list[VariableDic]:
    """Variables de un «Diccionario - <tabla>.pdf» (leído con `tablas=True`): una fila por variable, y filas de continuación (sin
    variable) con los valores y descripciones de las categorías. Las filas de continuación al inicio de una página siguen a la
    última variable de la página anterior."""
    vs: list[VariableDic] = []
    for pag in paginas:
        for tb in pag.get("tablas") or []:
            for fila in tb:
                f = [_celda(c) for c in fila] + [""] * (9 - len(fila))
                if f[0].upper().startswith("N") and f[1].upper() == "VARIABLE":
                    continue                                    # encabezado repetido en cada página
                if f[1]:
                    vs.append(VariableDic(tabla, f[1].upper(), f[2], f[5], f[8], [], int(f[0]) if f[0].isdigit() else len(vs) + 1))
                elif not vs:
                    continue
                if f[6] or f[7]:
                    if f[6] or vs[-1].categorias:
                        vs[-1].categorias.append((f[6], f[7]))
    return vs


# ------------------------------------------------------------------ vínculo sin LLM

@dataclass
class Vinculo:
    tabla: str
    codigo: str
    pregunta_id: str | None            # «salud:25C»; None si no hay
    metodo: str                        # diccionario | regla | llm | manual | sin_pregunta
    estado: str = "propuesto"          # nunca más que `propuesto` aquí (AGENTS.md §5.2; `revisado` lo decide M1-07)
    motivo: str = ""                   # sin_pregunta: administrativa | construida | no_encontrada; regla: de dónde sale el número
    evidencia: str = ""


@lru_cache(maxsize=4)
def _config_de(ruta: str) -> dict:
    return yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))["cuestionarios"]


def _config(ruta: Path = RUTA_PARAMETROS) -> dict:
    """`cuestionarios.*` de parametros.yaml, leído una vez por archivo (no se modifica)."""
    return _config_de(str(ruta))


def _numero_mas_largo(base: str, existentes: set[str]) -> str | None:
    """De «25C1» prueba 25C1, 25C y 25: el más largo que sea una pregunta del cuestionario. Solo se recorta la cola que sigue a los
    dígitos iniciales: «1040A» nunca se vuelve «104» (sería otra pregunta)."""
    m = re.match(r"(\d+)(.*)$", base)
    if not m:
        return None
    cabeza, cola = m.groups()
    for k in range(len(cola), -1, -1):
        if cabeza + cola[:k] in existentes:
            return cabeza + cola[:k]
    return None


def vincular_por_regla(variables: list[VariableDic], preguntas: list[Pregunta],
                       cuestionarios_de_tabla: dict[str, list[str]] | None = None, cfg: dict | None = None) -> dict[tuple[str, str], Vinculo]:
    """Los vínculos que no necesitan LLM: (1) el diccionario trae el número de pregunta en la etiqueta («pregunta 105») y (2) el
    código de la variable lleva el número (QS25C1 → pregunta 25C del cuestionario de salud). Solo vale un número que exista en el
    cuestionario; si no existe, la variable no se vincula (nunca se inventa). Devuelve {(tabla, código): Vinculo} en `propuesto`."""
    cfg = cfg or _config()
    existentes: dict[str, set[str]] = {}
    for q in preguntas:
        existentes.setdefault(q.cuestionario, set()).add(q.numero)
    reglas = [(r, re.compile(r["regex"])) for r in cfg["reglas_codigo"]["valor"]]
    en_etiqueta = re.compile(cfg["etiqueta_pregunta_patron"]["valor"], re.I)
    out: dict[tuple[str, str], Vinculo] = {}
    for v in variables:
        clave = (v.tabla, v.codigo)
        cuest = (cuestionarios_de_tabla or {}).get(v.tabla) or sorted(existentes)
        m = en_etiqueta.search(v.etiqueta)
        if m:
            for c in cuest:
                n = _numero_mas_largo(m.group(1).upper(), existentes.get(c, set()))
                if n:
                    out[clave] = Vinculo(v.tabla, v.codigo, f"{c}:{n}", "diccionario", evidencia=f"etiqueta: «{m.group(0)}»")
                    break
        if clave in out:
            continue
        for r, rx in reglas:
            if r["tablas"] != ["*"] and v.tabla not in r["tablas"]:
                continue
            m = rx.match(v.codigo)
            n = _numero_mas_largo(m.group(1), existentes.get(r["cuestionario"], set())) if m else None
            if n:
                out[clave] = Vinculo(v.tabla, v.codigo, f"{r['cuestionario']}:{n}", "regla", motivo=r["id"],
                                     evidencia=f"código {v.codigo} → pregunta {n}")
                break
    return out


RUTA_VINCULOS_MANUALES = Path("curados/inferencia/vinculos_manuales.yaml")      # relativa a la raíz del repo
_PREGUNTA_ID = re.compile(r"^(hogar|individual|salud):[0-9][0-9A-Z]*$")


def leer_vinculos_manuales(ruta: Path) -> list[Vinculo]:
    """Los vínculos que el dueño fijó a mano (`curados/inferencia/vinculos_manuales.yaml`): una entrada por variable con tabla, código,
    pregunta («cuestionario:número»), motivo, quien y fecha. Mandan sobre la regla y el LLM (`pap cuestionarios aplicar`) y el lote
    no las manda al modelo. Método `manual`; siguen en `propuesto` (el visto de `revisado` es de M1-07). Sin archivo, no hay vínculos
    manuales; una entrada incompleta o repetida es un error (no se adivina)."""
    ruta = Path(ruta)
    if not ruta.exists():
        return []
    entradas = (yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}).get("vinculos") or []
    out: list[Vinculo] = []
    vistos: set[tuple[str, str]] = set()
    for i, e in enumerate(entradas, 1):
        faltan = [k for k in ("tabla", "codigo", "pregunta", "motivo", "quien", "fecha") if not str(e.get(k) or "").strip()]
        if faltan:
            raise PapError(f"{ruta.name}, entrada {i}: falta {', '.join(faltan)}")
        if not _PREGUNTA_ID.match(str(e["pregunta"])):
            raise PapError(f"{ruta.name}, entrada {i}: la pregunta debe ser «cuestionario:número» (p. ej. individual:474C), no «{e['pregunta']}»")
        clave = (str(e["tabla"]), str(e["codigo"]).upper())
        if clave in vistos:
            raise PapError(f"{ruta.name}: {clave[0]}.{clave[1]} aparece dos veces")
        vistos.add(clave)
        out.append(Vinculo(clave[0], clave[1], str(e["pregunta"]), "manual", motivo="manual",
                           evidencia=f"manual ({e['quien']}, {e['fecha']}): {str(e['motivo']).strip()}"))
    return out


def motivo_sin_pregunta(v: VariableDic, cfg: dict | None = None) -> str | None:
    """«administrativa» (identificador, peso, diseño de la muestra) o «construida» (la calcula el INEI) si el código o la etiqueta
    lo dicen; None si no se sabe (esa variable va al LLM; no se adivina)."""
    cfg = cfg or _config()
    for motivo, reglas in cfg["sin_pregunta"]["valor"].items():
        if any(re.search(r, v.codigo) for r in reglas.get("codigos", [])) or \
                any(re.search(r, v.etiqueta, re.I) for r in reglas.get("etiquetas", [])):
            return motivo
    return None


# ------------------------------------------------------------------ candidatos para el LLM

def _palabras(texto: str, stop: set[str], prefijo: int) -> list[str]:
    import unicodedata

    t = unicodedata.normalize("NFD", texto.casefold())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return [w[:prefijo] for w in re.findall(r"[a-z0-9ñ]+", t) if w not in stop and len(w) > 1]


class Candidatos:
    """Las preguntas más parecidas a una variable por palabras en común (peso por rareza, como un BM25 simple), para dárselas al
    LLM como lista corta. No decide nada: solo ordena. Sin parecido, devuelve las primeras del cuestionario en su orden."""

    def __init__(self, preguntas: list[Pregunta], cfg: dict | None = None):
        import math
        from collections import Counter

        cfg = cfg or _config()
        self.stop, self.pref = set(cfg["candidatos_stopwords"]["valor"]), int(cfg["candidatos_prefijo"]["valor"])
        self.preguntas = list(preguntas)
        self._bolsas = [Counter(_palabras(q.texto + " " + " ".join(q.opciones), self.stop, self.pref)) for q in self.preguntas]
        df: Counter = Counter()
        for b in self._bolsas:
            df.update(b.keys())
        n = max(len(self.preguntas), 1)
        self._idf = {w: math.log(1 + n / c) for w, c in df.items()}
        # Sinónimos (dueño, 13/11/2026; `cuestionarios.sinonimos`): si la etiqueta de la variable dice «edad», también se buscan «años» y
        # «cumplidos». Solo amplían la consulta; las preguntas no cambian y el número de candidatas tampoco.
        self._sinonimos: dict[str, set[str]] = {}
        for clave, otros in ((cfg.get("sinonimos") or {}).get("valor") or {}).items():
            for k in _palabras(clave, self.stop, self.pref):
                self._sinonimos.setdefault(k, set()).update(w for o in otros for w in _palabras(o, self.stop, self.pref))

    def _consulta(self, v: VariableDic) -> set[str]:
        base = set(_palabras(v.etiqueta + " " + " ".join(d for _, d in v.categorias), self.stop, self.pref))
        for w in list(base):
            base |= self._sinonimos.get(w, set())
        return base

    def puntaje(self, v: VariableDic, i: int, consulta: set[str] | None = None) -> float:
        import math

        consulta = self._consulta(v) if consulta is None else consulta
        b = self._bolsas[i]
        return sum(self._idf.get(w, 0.0) for w in consulta if w in b) / math.sqrt(1 + sum(b.values()))

    def de(self, v: VariableDic, cuestionarios: list[str], k: int) -> list[Pregunta]:
        consulta = self._consulta(v)
        ids = [i for i, q in enumerate(self.preguntas) if not cuestionarios or q.cuestionario in cuestionarios]
        orden = sorted(ids, key=lambda i: (-self.puntaje(v, i, consulta), i))
        return [self.preguntas[i] for i in orden[:k]]


# ------------------------------------------------------------------ del almacén a los Parquet

ENCUESTA = "ENDES"
CUESTIONARIOS = ("hogar", "individual", "salud")
SEP_ID = "·"


def carpeta_cuestionarios(rutas, encuesta: str = ENCUESTA, anio: int = 2024) -> Path:
    return rutas.raiz / "biblioteca" / "variables" / "cuestionarios" / encuesta / str(anio)


def var_id(tabla: str, codigo: str, encuesta: str = ENCUESTA, anio: int = 2024) -> str:
    """La misma llave del índice de variables (`encuesta·año·archivo·código`, M0-05)."""
    return SEP_ID.join((encuesta, str(anio), tabla, codigo))


def _cuestionario_de_miembro(miembro: str) -> str | None:
    n = miembro.upper()
    if not n.endswith(".PDF") or "CUESTIONARIO" not in n:
        return None
    return "hogar" if "HOGAR" in n else "individual" if "INDIVIDUAL" in n else "salud" if "SALUD" in n else None


def _tabla_de_diccionario(miembro: str, anio: int) -> str | None:
    base = Path(miembro.replace("\\", "/")).stem
    if not base.lower().startswith("diccionario"):
        return None
    from .almacen import nombre_parquet

    return nombre_parquet(re.sub(r"^diccionario\s*-\s*", "", base, flags=re.I) + ".pdf", anio)


def extraer_cuestionarios(rutas, anio: int = 2024, p: Parametros | None = None, pc: ParametrosCuestionarios | None = None,
                          log=print) -> dict[str, list[Pregunta]]:
    """Las preguntas de los tres cuestionarios registrados (`endes-<año>-cuestionario-<hogar|individual|salud>`), leídas en el
    subproceso aislado. Comprueba la huella del PDF contra la registrada antes de leerlo."""
    from ..util import sha256
    from .almacen import _insumo

    p, pc = p or Parametros.desde_yaml(), pc or ParametrosCuestionarios.desde_yaml()
    out = {}
    for c in CUESTIONARIOS:
        ins = _insumo(rutas, "INEI-ENDES", f"endes-{anio}-cuestionario-{c}")
        if sha256(ins.ruta) != ins.hash.removeprefix("sha256:"):
            raise PapError(f"cuestionario {c}: la huella del PDF no coincide con la registrada; corre `pap verificar`")
        qs = preguntas_de_paginas(leer_pdf(ins.ruta, p), c, pc)
        out[c] = qs
        log(f"✔ cuestionario {c}: {len(qs)} preguntas")
    return out


def extraer_diccionarios(rutas, anio: int = 2024, p: Parametros | None = None, log=print) -> tuple[list[VariableDic], dict[str, list[str]]]:
    """Las variables de todos los «Diccionario - <tabla>.pdf» de los ZIP registrados de la ENDES y, por tabla, los cuestionarios que
    vienen en su mismo ZIP (de dónde puede salir su pregunta). Los ZIP se abren con `abrir_zip_seguro`."""
    from ..util import sha256
    from ..zip_seguro import abrir_zip_seguro
    from .almacen import _insumo

    p = p or Parametros.desde_yaml()
    lista = rutas.raiz / "curados" / "inferencia" / "descargas" / f"endes_{anio}.yaml"
    cfg = yaml.safe_load(lista.read_text(encoding="utf-8"))
    variables: list[VariableDic] = []
    cuests: dict[str, list[str]] = {}
    for mod in cfg["modulos"]:
        ins = _insumo(rutas, cfg["fuente"], mod["recurso"])
        if sha256(ins.ruta) != ins.hash.removeprefix("sha256:"):
            raise PapError(f"{mod['recurso']}: la huella del ZIP no coincide con la registrada; corre `pap verificar`")
        with abrir_zip_seguro(ins.ruta) as z, tempfile.TemporaryDirectory(prefix="pap-dic-") as d:
            presentes = sorted({c for m in z.miembros() if (c := _cuestionario_de_miembro(m))})
            for m in sorted(z.miembros()):
                tabla = _tabla_de_diccionario(m, anio) if m.lower().endswith(".pdf") else None
                if not tabla:
                    continue
                local = Path(d) / Path(m).name
                local.write_bytes(z.leer(m))
                vs = diccionario_de_paginas(leer_pdf(local, p, tablas=True), tabla)
                local.unlink()
                variables += vs
                cuests[tabla] = presentes
                log(f"✔ diccionario {tabla}: {len(vs)} variables")
    return variables, cuests


def _escribir_parquet(df, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_name(f".{ruta.name}.tmp")
    df.write_parquet(tmp, compression="zstd", compression_level=3)
    tmp.replace(ruta)


def guardar_cuestionarios(preguntas: dict[str, list[Pregunta]], destino: Path) -> dict[str, Path]:
    """Un Parquet por cuestionario (`hogar.parquet`, `individual.parquet`, `salud.parquet`). Fuera de git (biblioteca/)."""
    import polars as pl

    esquema = {"cuestionario": pl.String, "numero": pl.String, "texto": pl.String, "seccion": pl.String, "pagina": pl.Int32,
               "opciones": pl.List(pl.String), "saltos": pl.List(pl.String), "cortada": pl.Boolean, "tipo": pl.String, "estado": pl.String}
    salida = {}
    for c, qs in preguntas.items():
        filas = [{"cuestionario": q.cuestionario, "numero": q.numero, "texto": q.texto, "seccion": q.seccion, "pagina": q.pagina,
                  "opciones": q.opciones, "saltos": q.saltos, "cortada": q.cortada, "tipo": q.tipo, "estado": "propuesto"} for q in qs]
        salida[c] = destino / f"{c}.parquet"
        _escribir_parquet(pl.DataFrame(filas, schema=esquema), salida[c])
    return salida


def leer_cuestionarios(destino: Path) -> list[Pregunta]:
    import polars as pl

    out = []
    for c in CUESTIONARIOS:
        ruta = Path(destino) / f"{c}.parquet"
        if not ruta.exists():
            raise PapError(f"Falta {ruta.name}: corre antes `pap cuestionarios extraer`")
        for f in pl.read_parquet(ruta).iter_rows(named=True):
            out.append(Pregunta(f["cuestionario"], f["numero"], f["texto"], f["seccion"], f["pagina"], f["opciones"], f["saltos"], f["cortada"], f["tipo"]))
    return out


def guardar_diccionarios(variables: list[VariableDic], cuests: dict[str, list[str]], destino: Path) -> Path:
    import polars as pl

    filas = [{"tabla": v.tabla, "codigo": v.codigo, "etiqueta": v.etiqueta, "rango": v.rango, "obs": v.obs, "orden": v.orden,
              "categorias": json.dumps(v.categorias, ensure_ascii=False), "cuestionarios": cuests.get(v.tabla, [])} for v in variables]
    esquema = {"tabla": pl.String, "codigo": pl.String, "etiqueta": pl.String, "rango": pl.String, "obs": pl.String,
               "orden": pl.Int32, "categorias": pl.String, "cuestionarios": pl.List(pl.String)}
    ruta = Path(destino) / "diccionarios.parquet"
    _escribir_parquet(pl.DataFrame(filas, schema=esquema), ruta)
    return ruta


def leer_diccionarios(destino: Path) -> tuple[list[VariableDic], dict[str, list[str]]]:
    import polars as pl

    ruta = Path(destino) / "diccionarios.parquet"
    if not ruta.exists():
        raise PapError(f"Falta {ruta.name}: corre antes `pap cuestionarios extraer`")
    vs, cuests = [], {}
    for f in pl.read_parquet(ruta).iter_rows(named=True):
        vs.append(VariableDic(f["tabla"], f["codigo"], f["etiqueta"], f["rango"], f["obs"],
                              [tuple(x) for x in json.loads(f["categorias"])], f["orden"]))
        cuests[f["tabla"]] = f["cuestionarios"]
    return vs, cuests


# ------------------------------------------------------------------ tabla de vínculos

def tabla_de_vinculos(vinculos: list[Vinculo], preguntas: list[Pregunta]):
    """Los vínculos como tabla (una fila por variable), con la pregunta, su referencia y su texto, lista para `indice.aplicar_vinculos`.
    Columnas: var_id, tabla, codigo, pregunta_id, metodo, estado, motivo, evidencia, cuestionario, seccion, numero, pagina, texto_pregunta."""
    import polars as pl

    por_id = {q.id: q for q in preguntas}
    filas = []
    for v in vinculos:
        q = por_id.get(v.pregunta_id) if v.pregunta_id else None
        if v.pregunta_id and q is None:
            raise PapError(f"{v.tabla}.{v.codigo}: la pregunta {v.pregunta_id} no está entre las extraídas")
        filas.append({"var_id": var_id(v.tabla, v.codigo), "tabla": v.tabla, "codigo": v.codigo, "pregunta_id": v.pregunta_id,
                      "metodo": v.metodo, "estado": v.estado, "motivo": v.motivo, "evidencia": v.evidencia,
                      "cuestionario": q.cuestionario if q else None, "seccion": q.seccion if q else None, "numero": q.numero if q else None,
                      "pagina": q.pagina if q else None, "texto_pregunta": q.texto if q else None})
    S = pl.String
    return pl.DataFrame(filas, schema={"var_id": S, "tabla": S, "codigo": S, "pregunta_id": S, "metodo": S, "estado": S, "motivo": S,
                                       "evidencia": S, "cuestionario": S, "seccion": S, "numero": S, "pagina": pl.Int32, "texto_pregunta": S})


def vincular_sin_llm(variables: list[VariableDic], preguntas: list[Pregunta], cuests: dict[str, list[str]]) -> list[Vinculo]:
    """Todo lo que se puede decir sin LLM: el vínculo por diccionario o por regla, y el motivo de las que no tienen pregunta por ser
    administrativas o construidas. El resto no aparece: espera al lote (`sin_pregunta = pendiente` en el índice)."""
    por_regla = vincular_por_regla(variables, preguntas, cuests)
    out = []
    for v in variables:
        x = por_regla.get((v.tabla, v.codigo))
        if x:
            out.append(x)
        elif (m := motivo_sin_pregunta(v)):
            out.append(Vinculo(v.tabla, v.codigo, None, "sin_pregunta", motivo=m, evidencia="por el código o la etiqueta"))
    return out
