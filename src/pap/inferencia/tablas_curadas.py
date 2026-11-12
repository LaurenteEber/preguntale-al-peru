"""Tablas curadas del motor de inferencia (M0-06; diseño §7.4 y anexo A): esquemas y validación.

Las seis tablas viven en `curados/inferencia/` y cada fila lleva su cita (documento + página, o archivo:línea):

| Tabla | Archivo | Una fila es |
|---|---|---|
| `diseno_muestral` | `diseno_muestral.csv` | encuesta × año × archivo × medición (llave) |
| `universos_analiticos` | `universos_analiticos.yaml` | un universo con sus predicados |
| `territorios` | `territorios.yaml` | un nivel territorial de una encuesta |
| `perfil_anual` | `perfil_anual.csv` | encuesta × año |
| `relacion_entre_anios` | `relacion_entre_anios.csv` | encuesta × par de años |
| `cortes_estandar` | `cortes_estandar.yaml` | un corte, con su variable por archivo |

Una fila sin cita, o con una cita que no dice dónde (página o línea), no valida: es tipo C (AGENTS.md §5). Las expresiones SQL
(`peso_expr`, `estrato_expr`, `expr`…) solo admiten un alfabeto corto de identificadores, números, comillas simples y operadores;
las verifica además la gramática de M0-07. `validar` también cruza las tablas con `archivos_endes_2024.yaml` (archivos y uniones
declaradas), con `dim_indicador.yaml` (niveles) y, si existe, con el índice de variables (cada variable citada existe en su archivo).

El comando es `pap inferencia validar-tablas`; las pruebas con datos reales están en `tests/inferencia/test_tablas_curadas.py`.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from ..config import Rutas

CARPETA = Path("curados") / "inferencia"
ARCHIVOS_TABLAS = {
    "diseno_muestral": "diseno_muestral.csv",
    "universos_analiticos": "universos_analiticos.yaml",
    "territorios": "territorios.yaml",
    "perfil_anual": "perfil_anual.csv",
    "relacion_entre_anios": "relacion_entre_anios.csv",
    "cortes_estandar": "cortes_estandar.yaml",
}

# Una cita dice dónde: página de un documento («p. 11», «pp. 10-11»), archivo:línea o la etiqueta de un archivo de datos.
_DONDE = re.compile(r"\bpp?\. ?\d|\.(?:py|ya?ml|md|csv|json|parquet):\d|[Ee]tiqueta del archivo [A-Za-z0-9_]+ \d{4}")
_ARCHIVO_LINEA = re.compile(r"\b((?:src|curados|docs|tests|backlog)/[\w./-]+\.(?:py|ya?ml|md|csv|json)):(\d+)(?:-(\d+))?")
_EXPR_SEGURA = re.compile(r"^[\w\s.,()'<>=+*/%-]+$")
_PROHIBIDO = re.compile(r"--|/\*|;|\b(?:SELECT|FROM)\b", re.IGNORECASE)
_VAR = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _cita(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("falta la cita")
    if not _DONDE.search(v):
        raise ValueError("la cita no dice dónde (página «p. N», archivo:línea o «Etiqueta del archivo X AAAA»)")
    return v


def _expr(v: str) -> str:
    if not _EXPR_SEGURA.match(v) or _PROHIBIDO.search(v):
        raise ValueError(f"expresión con caracteres no permitidos: {v!r}")
    return v


def _uniones(texto: str) -> list[tuple[str, str, str, str]]:
    out = []
    for u in filter(None, (x.strip() for x in texto.split(";"))):
        izq, _, der = u.partition("=")
        (h, _, ch), (p, _, cp) = izq.partition("."), der.partition(".")
        if not (h and ch and p and cp):
            raise ValueError(f"unión mal escrita: {u!r} (se espera HIJO.COL=PADRE.COL)")
        out.append((h, ch, p, cp))
    return out


class _Fila(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ------------------------------------------------------------------ diseño muestral

class DisenoMuestral(_Fila):
    """Anexo A: llave `encuesta, anio, archivo, medicion`."""
    encuesta: Literal["ENDES", "ENAHO"]
    anio: int
    archivo: str
    medicion: str
    poblacion: str
    peso_expr: str
    estrato_expr: str
    psu_expr: str
    upm_estable_expr: str
    peso_normalizado: Literal["sí", "no"]
    nivel_submuestra: Literal["hogar", "individual", "medicion"]
    uniones_para_diseno: str = ""        # «HIJO.COL=PADRE.COL;…», cada una declarada en archivos_<encuesta>_<año>.yaml
    cita: str

    _v_cita = field_validator("cita")(_cita)
    _v_expr = field_validator("peso_expr", "estrato_expr", "psu_expr", "upm_estable_expr")(_expr)

    @property
    def llave(self) -> tuple:
        return (self.encuesta, self.anio, self.archivo, self.medicion)

    @property
    def uniones(self) -> list[tuple[str, str, str, str]]:
        """[(hijo, columna del hijo, padre, columna del padre)]"""
        return _uniones(self.uniones_para_diseno)

    @field_validator("uniones_para_diseno")
    @classmethod
    def _uniones_bien_escritas(cls, v: str) -> str:
        _uniones(v)
        return v


# ------------------------------------------------------------------ universos analíticos

class Predicado(_Fila):
    var: str
    op: Literal["en", "entre"]
    valores: list[float]

    @model_validator(mode="after")
    def _forma(self):
        if not _VAR.match(self.var):
            raise ValueError(f"nombre de variable no permitido: {self.var!r}")
        if not self.valores:
            raise ValueError("predicado sin valores")
        if self.op == "entre" and (len(self.valores) != 2 or self.valores[0] > self.valores[1]):
            raise ValueError("«entre» lleva dos valores, el primero no mayor que el segundo")
        return self


class AplicaA(_Fila):
    archivos: list[str]
    mediciones: list[str]


class ExigePareja(_Fila):
    """El registro de la unidad debe tener su pareja en `archivo` (por las columnas de `por`: (columna de la unidad, columna de `archivo`)).
    Los que no la tienen quedan fuera del universo. C-M0-05-2: disciplina infantil exige a la mujer en REC0111."""
    archivo: str
    por: list[tuple[str, str]]

    @field_validator("por")
    @classmethod
    def _por(cls, v):
        if not v:
            raise ValueError("`por` necesita al menos un par de columnas")
        for a, b in v:
            if not (_VAR.match(a) and _VAR.match(b)):
                raise ValueError(f"nombre de columna no permitido: {a!r}, {b!r}")
        return v


class UniversoAnalitico(_Fila):
    id: str
    encuesta: Literal["ENDES", "ENAHO"]
    unidad: str
    aplica_a: AplicaA
    predicados: list[Predicado]
    anios: tuple[int, int]
    fuente: str
    exige_pareja: list[ExigePareja] = []      # M1-01: registros que deben tener su pareja en otro archivo (no es un predicado de valor)

    _v_cita = field_validator("fuente")(_cita)

    @model_validator(mode="after")
    def _hay(self):
        if not self.predicados and not self.exige_pareja:
            raise ValueError("un universo necesita al menos un predicado (o exigir su pareja en otro archivo)")
        return self

    @field_validator("anios")
    @classmethod
    def _orden(cls, v):
        if v[0] > v[1]:
            raise ValueError("anios: el primero no puede pasar del segundo")
        return v


class TablaUniversos(_Fila):
    version: str
    fecha: str
    universos: list[UniversoAnalitico]


# ------------------------------------------------------------------ territorios

class Territorio(_Fila):
    nivel: str
    encuesta: Literal["ENDES", "ENAHO"]
    anios: tuple[int, int]
    expr: str
    unidad_expr: str
    columnas: list[str]
    como: Literal["dominio"]
    cita: str

    _v_cita = field_validator("cita")(_cita)
    _v_expr = field_validator("expr", "unidad_expr")(_expr)

    @field_validator("anios")
    @classmethod
    def _orden(cls, v):
        if v[0] > v[1]:
            raise ValueError("anios: el primero no puede pasar del segundo")
        return v


class TablaTerritorios(_Fila):
    version: str
    fecha: str
    territorios: list[Territorio]


# ------------------------------------------------------------------ perfil anual y relación entre años

class PerfilAnual(_Fila):
    """Anexo A: llave `encuesta, anio`. `clase_cambio` vacía = sin decidir (la decide el dueño, E-07)."""
    encuesta: Literal["ENDES", "ENAHO"]
    anio: int
    marco: str
    muestra_maestra: str
    n_estratos: int
    n_upm: int
    modo_entrevista: str
    meses_campo: str
    ubigeo_minimo: Literal["departamento", "provincia", "distrito"]
    pesos_especiales: str = ""
    clase_cambio: Literal["", "corte", "aviso"] = ""
    cita: str

    _v_cita = field_validator("cita")(_cita)

    @field_validator("n_estratos", "n_upm")
    @classmethod
    def _positivo(cls, v):
        if v <= 0:
            raise ValueError("debe ser positivo")
        return v


class RelacionEntreAnios(_Fila):
    """Anexo A: llave `encuesta, anio_a, anio_b`. Sin llave de UPM estable solo cabe `independiente`."""
    encuesta: Literal["ENDES", "ENAHO"]
    anio_a: int
    anio_b: int
    relacion: Literal["independiente", "conglomerados_repetidos", "panel_parcial"]
    upm_estable_expr: str = ""
    cita: str

    _v_cita = field_validator("cita")(_cita)

    @model_validator(mode="after")
    def _coherente(self):
        if self.anio_b <= self.anio_a:
            raise ValueError("anio_b debe ser posterior a anio_a")
        if self.relacion != "independiente" and not self.upm_estable_expr:
            raise ValueError(f"«{self.relacion}» necesita la llave de la UPM estable")
        if self.upm_estable_expr:
            _expr(self.upm_estable_expr)
        return self


# ------------------------------------------------------------------ cortes estándar

class Tramo(_Fila):
    """Un rango de una variable numérica, con los límites incluidos (HC1 en meses: 6 a 8 = desde 6, hasta 8)."""
    rotulo: str
    desde: int
    hasta: int

    @field_validator("rotulo")
    @classmethod
    def _rotulo(cls, v):
        if not v.strip():
            raise ValueError("el tramo necesita su rótulo")
        return v

    @model_validator(mode="after")
    def _orden(self):
        if self.desde > self.hasta:
            raise ValueError("desde no puede pasar de hasta")
        return self


class JuegoTramos(_Fila):
    """Un juego de tramos para ciertas recetas (los de la anemia no son los de la desnutrición crónica). M1-01 solo los escribe; los
    compila M1-03 (tarea 1b)."""
    id: str
    aplica_a_recetas: list[str]
    tramos: list[Tramo]
    cita: str

    _v_cita = field_validator("cita")(_cita)

    @model_validator(mode="after")
    def _forma(self):
        if not self.aplica_a_recetas:
            raise ValueError(f"{self.id}: el juego necesita al menos una receta")
        if not self.tramos:
            raise ValueError(f"{self.id}: el juego necesita al menos un tramo")
        for a, b in zip(self.tramos, self.tramos[1:]):
            if b.desde <= a.hasta and b.desde > a.desde:
                raise ValueError(f"{self.id}: los tramos «{a.rotulo}» y «{b.rotulo}» se traslapan")
            if b.desde <= a.desde:
                raise ValueError(f"{self.id}: los tramos van en orden creciente («{b.rotulo}» no sigue a «{a.rotulo}»)")
        return self


class VariableCorte(_Fila):
    archivo: str
    variable: str
    unidad: str
    categorias: dict[int, str] | None = None
    juegos_de_tramos: list[JuegoTramos] | None = None     # variable numérica agrupada en tramos, un juego por grupo de recetas
    pendiente: str | None = None         # ID de la consulta (tipo C) o de la historia que falta para poder usar el corte
    cita: str

    _v_cita = field_validator("cita")(_cita)

    @model_validator(mode="after")
    def _juegos(self):
        vistos: dict[str, str] = {}
        ids = [j.id for j in self.juegos_de_tramos or []]
        for i in {i for i in ids if ids.count(i) > 1}:
            raise ValueError(f"el juego «{i}» se repite")
        for j in self.juegos_de_tramos or []:
            for r in j.aplica_a_recetas:
                if r in vistos:
                    raise ValueError(f"la receta {r} está en más de un juego de tramos («{vistos[r]}» y «{j.id}»)")
                vistos[r] = j.id
        return self


class CorteEstandar(_Fila):
    id: str
    nombre: str
    por_encuesta: dict[str, list[VariableCorte]]
    categorias: dict[int, str] | None = None
    agrupa: dict[str, list[int]] | None = None       # categoría formada por varios códigos de `categorias` (Costa = 1 y 2); la compila M1-03
    nota: str | None = None
    cita: str

    _v_cita = field_validator("cita")(_cita)

    @model_validator(mode="after")
    def _categorias(self):
        for enc, variables in self.por_encuesta.items():
            if not variables:
                raise ValueError(f"{enc}: sin variables")
            for v in variables:
                if not (v.categorias or self.categorias or v.juegos_de_tramos or v.pendiente):
                    raise ValueError(f"{enc} {v.archivo}.{v.variable}: sin categorías ni consulta pendiente")
        usados: dict[int, str] = {}
        for grupo, codigos in (self.agrupa or {}).items():
            if len(codigos) < 2:
                raise ValueError(f"el grupo «{grupo}» necesita al menos dos códigos")
            for k in codigos:
                if k not in (self.categorias or {}):
                    raise ValueError(f"el grupo «{grupo}» nombra el código {k}, que no está en las categorías del corte")
                if k in usados:
                    raise ValueError(f"el código {k} está en más de un grupo («{usados[k]}» y «{grupo}»)")
                usados[k] = grupo
        return self


class TablaCortes(_Fila):
    version: str
    fecha: str
    cortes: list[CorteEstandar]


# ------------------------------------------------------------------ lectura

def _leer_csv(ruta: Path, modelo: type[BaseModel]) -> list:
    with open(ruta, encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        faltan = set(modelo.model_fields) - set(lector.fieldnames or []) - {n for n, c in modelo.model_fields.items() if not c.is_required()}
        sobran = set(lector.fieldnames or []) - set(modelo.model_fields)
        if faltan or sobran:
            raise ValueError(f"{ruta.name}: columnas que faltan {sorted(faltan)}, columnas que sobran {sorted(sobran)}")
        return [modelo.model_validate(fila) for fila in lector]


def leer_diseno_muestral(raiz: Path) -> list[DisenoMuestral]:
    return _leer_csv(raiz / CARPETA / ARCHIVOS_TABLAS["diseno_muestral"], DisenoMuestral)


def leer_perfil_anual(raiz: Path) -> list[PerfilAnual]:
    return _leer_csv(raiz / CARPETA / ARCHIVOS_TABLAS["perfil_anual"], PerfilAnual)


def leer_relacion_entre_anios(raiz: Path) -> list[RelacionEntreAnios]:
    return _leer_csv(raiz / CARPETA / ARCHIVOS_TABLAS["relacion_entre_anios"], RelacionEntreAnios)


def _leer_yaml(raiz: Path, nombre: str, modelo: type[BaseModel]):
    return modelo.model_validate(yaml.safe_load((raiz / CARPETA / ARCHIVOS_TABLAS[nombre]).read_text(encoding="utf-8")))


def leer_universos(raiz: Path) -> list[UniversoAnalitico]:
    return _leer_yaml(raiz, "universos_analiticos", TablaUniversos).universos


def leer_territorios(raiz: Path) -> list[Territorio]:
    return _leer_yaml(raiz, "territorios", TablaTerritorios).territorios


def leer_cortes(raiz: Path) -> list[CorteEstandar]:
    return _leer_yaml(raiz, "cortes_estandar", TablaCortes).cortes


LECTORES = {"diseno_muestral": leer_diseno_muestral, "universos_analiticos": leer_universos, "territorios": leer_territorios,
            "perfil_anual": leer_perfil_anual, "relacion_entre_anios": leer_relacion_entre_anios, "cortes_estandar": leer_cortes}


# ------------------------------------------------------------------ ayudas para aplicar las tablas

def sql_predicados(predicados: list[Predicado]) -> str:
    """Condición SQL (DuckDB) con todos los predicados a la vez. Un nulo no cumple ninguno."""
    def uno(p: Predicado) -> str:
        v = [int(x) if float(x).is_integer() else x for x in p.valores]
        return f"{p.var} BETWEEN {v[0]} AND {v[1]}" if p.op == "entre" else f"{p.var} IN ({', '.join(map(str, v))})"
    return " AND ".join(uno(p) for p in predicados)


def fraccion_upm_repetidas(upm_a, upm_b) -> float:
    """Parte de las UPM del año B que ya estaban en el año A (relación `conglomerados_repetidos`). 0 si B está vacío."""
    b = set(upm_b)
    return len(b & set(upm_a)) / len(b) if b else 0.0


# ------------------------------------------------------------------ validación cruzada

def _dim_indicador_niveles(raiz: Path) -> set[str]:
    dim = yaml.safe_load((raiz / "curados" / "capa0" / "dim_indicador.yaml").read_text(encoding="utf-8"))
    lista = dim if isinstance(dim, list) else dim["indicadores"]
    return {n["nivel"] for i in lista if i["id"].startswith("endes") for n in i["niveles_validos"]}


def citas_sin_linea(raiz: Path, textos: list[str]) -> list[str]:
    """Citas `archivo:línea` cuyo archivo no existe o no llega a esa línea."""
    malas = []
    for t in textos:
        for ruta, desde, hasta in _ARCHIVO_LINEA.findall(t):
            p = raiz / ruta
            if not p.exists():
                malas.append(f"{ruta}: no existe")
                continue
            n = sum(1 for _ in open(p, encoding="utf-8", errors="replace"))
            if int(hasta or desde) > n or int(desde) < 1:
                malas.append(f"{ruta}:{desde}{'-' + hasta if hasta else ''}: el archivo tiene {n} líneas")
    return malas


def _citas(nombre: str, filas: list) -> list[str]:
    if nombre == "universos_analiticos":
        return [f.fuente for f in filas]
    if nombre == "cortes_estandar":
        return ([c.cita for c in filas] + [v.cita for c in filas for vs in c.por_encuesta.values() for v in vs]
                + [j.cita for c in filas for vs in c.por_encuesta.values() for v in vs for j in v.juegos_de_tramos or []])
    return [f.cita for f in filas]


def _variables_indice(raiz: Path) -> set[tuple[str, str]] | None:
    ruta = raiz / "biblioteca" / "variables" / "variables.parquet"
    if not ruta.exists():
        return None
    import duckdb
    return set(duckdb.sql(f"SELECT archivo, variable FROM read_parquet('{ruta}') WHERE encuesta = 'ENDES' AND anio = 2024").fetchall())


RUTA_INDICE = "biblioteca/variables/variables.parquet"
ERROR_SIN_INDICE = (f"falta el índice de variables ({RUTA_INDICE}): no se pudo comprobar que las variables citadas existan "
                    "(`pap indice` lo genera)")


def validar(rutas: Rutas, *, exigir_indice: bool = False) -> dict[str, tuple[int, list[str]]]:
    """Valida las seis tablas: {tabla: (filas, errores)}. Sin errores = la tabla cumple su esquema y todas sus filas llevan cita.
    Con `exigir_indice` (lo pasa `pap inferencia validar-tablas`), la falta del índice de variables es un error de las tablas que
    citan variables y no una comprobación que se salta en silencio (M1-02, H06-3)."""
    raiz = rutas.raiz
    res: dict[str, tuple[int, list[str]]] = {}
    datos: dict[str, list] = {}
    for nombre, lector in LECTORES.items():
        try:
            datos[nombre] = lector(raiz)
            res[nombre] = (len(datos[nombre]), [])
        except Exception as e:                              # pydantic, yaml o csv: el mensaje se lleva tal cual
            res[nombre] = (0, [f"{ARCHIVOS_TABLAS[nombre]}: {e}"])
    err = lambda nombre, msg: res[nombre][1].append(msg)

    archivos_yaml = yaml.safe_load((raiz / CARPETA / "archivos_endes_2024.yaml").read_text(encoding="utf-8"))
    archivos = set(archivos_yaml["archivos"])
    relaciones = {(r["hijo"], c[0], r["padre"], c[1]) for r in archivos_yaml["relaciones"] for c in r["por"]}
    en_indice = _variables_indice(raiz)
    if exigir_indice and en_indice is None:
        for nombre in ("universos_analiticos", "territorios", "cortes_estandar"):
            err(nombre, ERROR_SIN_INDICE)

    for nombre, filas in datos.items():
        for c in citas_sin_linea(raiz, _citas(nombre, filas)):
            err(nombre, f"cita con archivo:línea inválido: {c}")

    if "diseno_muestral" in datos:
        llaves = [f.llave for f in datos["diseno_muestral"]]
        for k in {k for k in llaves if llaves.count(k) > 1}:
            err("diseno_muestral", f"llave repetida {k}")
        for f in datos["diseno_muestral"]:
            if f.archivo not in archivos:
                err("diseno_muestral", f"{f.llave}: el archivo {f.archivo} no está en archivos_endes_2024.yaml")
            for u in f.uniones:
                if u not in relaciones:
                    err("diseno_muestral", f"{f.llave}: la unión {u} no está declarada en archivos_endes_2024.yaml")
    if "universos_analiticos" in datos:
        ids = [u.id for u in datos["universos_analiticos"]]
        for i in {i for i in ids if ids.count(i) > 1}:
            err("universos_analiticos", f"id repetido {i}")
        for u in datos["universos_analiticos"]:
            for a in u.aplica_a.archivos:
                if a not in archivos:
                    err("universos_analiticos", f"{u.id}: el archivo {a} no está en archivos_endes_2024.yaml")
            if en_indice is not None:
                for p in u.predicados:
                    if not any((a, p.var) in en_indice for a in u.aplica_a.archivos):
                        err("universos_analiticos", f"{u.id}: la variable {p.var} no está en {u.aplica_a.archivos} del índice")
            for e in u.exige_pareja:
                if e.archivo not in archivos:
                    err("universos_analiticos", f"{u.id}: la pareja se exige en {e.archivo}, que no está en archivos_endes_2024.yaml")
    if "territorios" in datos:
        niveles = [t.nivel for t in datos["territorios"]]
        for n in {n for n in niveles if niveles.count(n) > 1}:
            err("territorios", f"nivel repetido {n}")
        for n in set(niveles) - _dim_indicador_niveles(raiz):
            err("territorios", f"el nivel {n} no está en niveles_validos de dim_indicador.yaml")
        if en_indice is not None:
            for t in datos["territorios"]:
                for c in t.columnas:
                    if ("RECH0", c) not in en_indice:
                        err("territorios", f"{t.nivel}: la columna {c} no está en RECH0 del índice")
    for nombre, clave in (("perfil_anual", lambda f: (f.encuesta, f.anio)),
                          ("relacion_entre_anios", lambda f: (f.encuesta, f.anio_a, f.anio_b))):
        if nombre in datos:
            llaves = [clave(f) for f in datos[nombre]]
            for k in {k for k in llaves if llaves.count(k) > 1}:
                err(nombre, f"llave repetida {k}")
    if "cortes_estandar" in datos:
        ids = [c.id for c in datos["cortes_estandar"]]
        for i in {i for i in ids if ids.count(i) > 1}:
            err("cortes_estandar", f"id repetido {i}")
        for c in datos["cortes_estandar"]:
            for enc, variables in c.por_encuesta.items():
                for v in variables:
                    if v.archivo not in archivos:
                        err("cortes_estandar", f"{c.id}: el archivo {v.archivo} no está en archivos_endes_2024.yaml")
                    elif en_indice is not None and (v.archivo, v.variable) not in en_indice:
                        err("cortes_estandar", f"{c.id}: la variable {v.variable} no está en {v.archivo} del índice")
    return res
