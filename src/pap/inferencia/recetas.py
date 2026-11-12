"""Recetas de indicador del motor de inferencia (M0-10; diseño §8.1): la definición oficial de un indicador como dato.

Una receta (`curados/inferencia/recetas/<id>.yaml`) dice qué se cuenta (`indicador`), entre quiénes (`universo` y el universo
analítico), con qué cortes y con qué cifras oficiales se comprueba. `Receta.a_plan` la vuelve un `Plan` (el mismo que arma el
planificador); desde ahí corre el camino de siempre: verificador → ejecutor → compuertas. Aquí **no hay lógica estadística**:
solo se lee la receta, se pasa por ese camino y se compara con el cubo y con las doradas.

- `transformaciones` va vacío: las recetas de M0 usan las variables que el INEI ya entrega ajustadas. Una transformación que no
  esté en el código actual es tipo C (no se inventa aquí).
- `estado`: propuesto < revisado < verificado. `verificado` lo da el visto del dueño (K-03) tras comprobar que la receta iguala al
  cubo y reproduce sus doradas; mientras falte, `revisado` lleva `pendiente: visto_dueno`.
- Las doradas se copian de `curados/capa0/cifras_doradas.csv` con su cita; `validar` exige que coincidan con esa tabla, que es la
  fuente de verdad (valor, indicador, año, nivel, territorio, casos, CV y tolerancias).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..config import Rutas
from ..errores import PapError
from ..zip_seguro import RUTA_PARAMETROS
from . import tablas_curadas as tc
from .compuertas import Compuerta, contexto_compuertas, evaluar
from .estimacion import Estimacion
from .plan import Plan

CARPETA = tc.CARPETA / "recetas"
EVIDENCIA_M0 = Path("backlog") / "slice-m0" / "evidencia"
FILAS_CUBO_2024 = EVIDENCIA_M0 / "m0-00_filas_cubo_2024.csv"
ESTADOS_CUBO_2024 = EVIDENCIA_M0 / "m0-00_estados_cubo.csv"
DORADAS = Path("curados") / "capa0" / "cifras_doradas.csv"
DIM_INDICADOR = Path("curados") / "capa0" / "dim_indicador.yaml"

# Columnas del cubo que se comparan, en las unidades del cubo (valor, ee, cv e IC en porcentaje).
COLUMNAS = ("valor", "ee", "cv", "ic_inf", "ic_sup", "gl", "n_muestra", "n_efectivo", "deff")
EXACTAS = ("gl", "n_muestra")                           # idénticas, sin redondeo


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# ------------------------------------------------------------------ esquema de la receta

class CondicionReceta(_M):
    """Un predicado sobre una variable de un archivo. El año lo pone `Receta.a_plan`, así que la receta no lo repite."""
    archivo: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
    variable: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
    op: Literal["en", "entre", "<", "≥", "es_nulo", "no_es_nulo"]
    valores: tuple[int | float, ...] = ()


class IndicadorReceta(_M):
    combinar: Literal["una", "alguna_de", "todas_de"]
    condiciones: tuple[CondicionReceta, ...] = Field(min_length=1)


class UniversoReceta(_M):
    restricciones: tuple[CondicionReceta, ...] = ()


class CorteNoPermitido(_M):
    id: str
    motivo: str = Field(min_length=1)


class Dorada(_M):
    id_cifra: str
    nivel: str
    territorio: str
    valor_publicado: float
    decimales: int
    bloqueante: bool
    casos_publicados: int | None = None
    cv_publicado: float | None = None
    cita: str

    _v_cita = field_validator("cita")(tc._cita)


class Receta(_M):
    id: str
    version: str
    fecha: str
    descripcion: str
    indicador_id: str
    encuesta: Literal["ENDES", "ENAHO"]
    unidad: str
    medida: str
    anios: tuple[int, int]
    universo_analitico: str
    indicador: IndicadorReceta
    universo: UniversoReceta = UniversoReceta()
    transformaciones: tuple[()] = ()
    cortes_permitidos: tuple[str, ...] = ()
    cortes_no_permitidos: tuple[CorteNoPermitido, ...] = ()
    tolerancia_pp: float = Field(gt=0)
    tolerancia_cv: float | None = None
    fuente: str
    doradas: tuple[Dorada, ...] = ()
    estado: Literal["propuesto", "revisado", "verificado"]
    pendiente: str | None = None

    _v_fuente = field_validator("fuente")(tc._cita)

    @field_validator("transformaciones", mode="before")
    @classmethod
    def _sin_transformaciones(cls, v):
        if v:
            raise ValueError("transformaciones debe ir vacío: una transformación que no está en el código actual es tipo C")
        return ()

    @model_validator(mode="after")
    def _coherente(self):
        if self.anios[0] > self.anios[1]:
            raise ValueError("anios: el primero no puede pasar del segundo")
        if self.estado == "revisado" and self.pendiente != "visto_dueno":
            raise ValueError("«revisado» lleva `pendiente: visto_dueno` (el visto del dueño, K-03)")
        if self.estado == "verificado" and self.pendiente is not None:
            raise ValueError("«verificado» no lleva pendiente")
        repetidos = set(self.cortes_permitidos) & {c.id for c in self.cortes_no_permitidos}
        if repetidos:
            raise ValueError(f"cortes a la vez permitidos y no permitidos: {sorted(repetidos)}")
        ids = [d.id_cifra for d in self.doradas]
        if len(set(ids)) != len(ids):
            raise ValueError("id_cifra repetido en doradas")
        return self

    def revisar_anio(self, anio: int) -> None:
        if not self.anios[0] <= anio <= self.anios[1]:
            raise PapError(f"La receta {self.id} vale para {self.anios[0]}–{self.anios[1]}, no para {anio}.")

    def a_plan(self, anio: int, nivel: str = "nacional", id_: str | None = None, cortes: tuple[str, ...] = ()) -> Plan:
        """El plan de esta receta para un año, un nivel territorial (todas sus unidades si `id_` es None) y unos cortes."""
        self.revisar_anio(anio)
        fuera = [c for c in cortes if c not in self.cortes_permitidos]
        if fuera:
            raise PapError(f"La receta {self.id} no permite los cortes {fuera} (permitidos: {list(self.cortes_permitidos)}).")

        def condicion(c: CondicionReceta) -> dict:
            return {"var": f"{self.encuesta}·{anio}·{c.archivo}·{c.variable}", "op": c.op, "valores": list(c.valores)}

        return Plan.model_validate({
            "origen": "receta", "receta_id": self.id, "encuesta": self.encuesta, "anios": [anio], "unidad": self.unidad,
            "medida": self.medida,
            "indicador": {"combinar": self.indicador.combinar, "condiciones": [condicion(c) for c in self.indicador.condiciones]},
            "universo": {"restricciones": [condicion(c) for c in self.universo.restricciones]},
            "cortes": list(cortes), "territorio": {"nivel": nivel, "id": id_}})


# ------------------------------------------------------------------ lectura y validación

def ids_de_recetas(raiz: Path) -> list[str]:
    return [p.stem for p in sorted((Path(raiz) / CARPETA).glob("*.yaml"))]


def leer_receta(raiz: Path, id_: str) -> Receta:
    ruta = Path(raiz) / CARPETA / f"{id_}.yaml"
    if id_ not in ids_de_recetas(raiz):
        raise PapError(f"No hay receta «{id_}» en {CARPETA} (hay: {', '.join(ids_de_recetas(raiz)) or 'ninguna'}).")
    return Receta.model_validate(yaml.safe_load(ruta.read_text(encoding="utf-8")))


def leer_recetas(raiz: Path) -> list[Receta]:
    return [leer_receta(raiz, i) for i in ids_de_recetas(raiz)]


def _doradas_csv(raiz: Path) -> dict[str, dict]:
    with open(Path(raiz) / DORADAS, encoding="utf-8", newline="") as f:
        return {r["id_cifra"]: r for r in csv.DictReader(f)}


def _errores_de_doradas(r: Receta, doradas: dict[str, dict]) -> list[str]:
    errores = []
    # H10-1: las doradas de la receta son exactamente las de su indicador y años en cifras_doradas.csv (ninguna falta)
    tengo = {d.id_cifra for d in r.doradas}
    errores += [f"dorada {i}: falta en la receta (está en cifras_doradas.csv para {r.indicador_id})" for i, f in sorted(doradas.items())
                if f["indicador_id"] == r.indicador_id and r.anios[0] <= int(f["anio"]) <= r.anios[1] and i not in tengo]
    for d in r.doradas:
        f = doradas.get(d.id_cifra)
        if f is None:
            errores.append(f"dorada {d.id_cifra}: no está en cifras_doradas.csv")
            continue
        esperado = (r.indicador_id, f["nivel"], f["territorio"], float(f["valor_publicado"]), int(f["decimales"]))
        tengo = (f["indicador_id"], d.nivel, d.territorio, d.valor_publicado, d.decimales)
        if esperado != tengo or not r.anios[0] <= int(f["anio"]) <= r.anios[1]:
            errores.append(f"dorada {d.id_cifra}: no coincide con cifras_doradas.csv ({esperado} frente a {tengo})")
        for campo, tipo in (("casos_publicados", int), ("cv_publicado", float)):
            csv_v, mia = f[campo], getattr(d, campo)
            if (csv_v == "") != (mia is None) or (csv_v != "" and tipo(csv_v) != mia):
                errores.append(f"dorada {d.id_cifra}: {campo} no coincide con cifras_doradas.csv")
        if float(f["tolerancia_pp"]) != r.tolerancia_pp:
            errores.append(f"dorada {d.id_cifra}: tolerancia_pp {f['tolerancia_pp']} de cifras_doradas.csv ≠ {r.tolerancia_pp} de la receta")
        if f["tolerancia_cv"] and (r.tolerancia_cv is None or float(f["tolerancia_cv"]) != r.tolerancia_cv):
            errores.append(f"dorada {d.id_cifra}: tolerancia_cv {f['tolerancia_cv']} de cifras_doradas.csv ≠ {r.tolerancia_cv} de la receta")
        if d.bloqueante != (f["bloqueante"] == "True"):
            errores.append(f"dorada {d.id_cifra}: bloqueante no coincide con cifras_doradas.csv")
    return errores


def validar(rutas: Rutas, *, exigir_indice: bool = False) -> dict[str, tuple[int, list[str]]]:
    """Valida cada receta: esquema, cruces con las tablas curadas, doradas, `dim_indicador` y citas. {id: (1 o 0, errores)}.
    Con `exigir_indice` (lo pasa `pap inferencia validar-recetas`), la falta del índice de variables es un error de cada receta (H10-2)."""
    raiz = rutas.raiz
    res: dict[str, tuple[int, list[str]]] = {}
    recetas: list[Receta] = []
    for ruta in sorted((raiz / CARPETA).glob("*.yaml")):
        try:
            r = Receta.model_validate(yaml.safe_load(ruta.read_text(encoding="utf-8")))
            recetas.append(r)
            res[r.id] = (1, [] if r.id == ruta.stem else [f"{ruta.name}: el id «{r.id}» no coincide con el nombre del archivo"])
        except Exception as e:                                   # pydantic o yaml: el mensaje se lleva tal cual
            res[ruta.stem] = (0, [f"{ruta.name}: {e}"])
    if not res:
        return {"recetas": (0, [f"no hay recetas en {CARPETA}"])}

    universos = {u.id for u in tc.leer_universos(raiz)}
    cortes = {c.id for c in tc.leer_cortes(raiz)}
    doradas = _doradas_csv(raiz)
    dim = {i["id"]: i for i in yaml.safe_load((raiz / DIM_INDICADOR).read_text(encoding="utf-8"))["indicadores"]}
    en_indice = tc._variables_indice(raiz)
    for r in recetas:
        errores = res[r.id][1]
        if r.universo_analitico not in universos:
            errores.append(f"universo_analitico «{r.universo_analitico}» no está en universos_analiticos.yaml")
        errores += [f"corte «{c}» no está en cortes_estandar.yaml" for c in (*r.cortes_permitidos, *(x.id for x in r.cortes_no_permitidos))
                    if c not in cortes]
        if en_indice is None and exigir_indice:
            errores.append(tc.ERROR_SIN_INDICE)
        if en_indice is not None:
            errores += [f"la variable {c.variable} no está en {c.archivo} del índice"
                        for c in (*r.indicador.condiciones, *r.universo.restricciones) if (c.archivo, c.variable) not in en_indice]
        errores += _errores_de_doradas(r, doradas)
        errores += [f"cita con archivo:línea inválido: {c}" for c in tc.citas_sin_linea(raiz, [r.fuente])]
        ind = dim.get(r.indicador_id)
        if ind is None:
            errores.append(f"indicador_id «{r.indicador_id}» no está en dim_indicador.yaml")
        elif ind.get("receta") != r.id:
            errores.append(f"dim_indicador.yaml: el indicador {r.indicador_id} debe llevar `receta: {r.id}` (lleva {ind.get('receta')!r})")
    return res


# ------------------------------------------------------------------ parámetros

@dataclass(frozen=True)
class ParametrosRecetas:
    """`recetas.*` de curados/inferencia/parametros.yaml (criterios de la definición de hecho del slice M0, punto 1)."""
    cubo_decimales: int
    cubo_tolerancia_unidades: int
    oraculo_tolerancia: float

    @classmethod
    def desde_yaml(cls, ruta: Path = RUTA_PARAMETROS) -> "ParametrosRecetas":
        c = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))["recetas"]
        return cls(int(c["cubo_decimales"]["valor"]), int(c["cubo_tolerancia_unidades"]["valor"]), float(c["oraculo_tolerancia"]["valor"]))


# ------------------------------------------------------------------ cálculo por el camino nuevo y comparaciones

@dataclass(frozen=True)
class FilaReceta:
    indicador_id: str
    nivel: str
    territorio_id: str
    estimacion: Estimacion
    compuerta: Compuerta


def niveles_del_anio(raiz: Path, receta: Receta, anio: int) -> list[str]:
    return [t.nivel for t in tc.leer_territorios(raiz) if t.encuesta == receta.encuesta and t.anios[0] <= anio <= t.anios[1]]


def en_unidades_del_cubo(e: Estimacion) -> dict[str, float | int | None]:
    """Una estimación (0–1) en las unidades del cubo: valor, ee, cv e IC en porcentaje; cv como `calculo._svy_niveles` (100·ee/p)."""
    p = e.valor
    return {"valor": 100 * p, "ee": 100 * e.ee, "cv": 100 * e.ee / p if p else None, "ic_inf": 100 * e.ic_inf, "ic_sup": 100 * e.ic_sup,
            "gl": e.gl, "n_muestra": e.n, "n_efectivo": e.n_efectivo, "deff": e.deff}


def calcular(receta: Receta, anio: int, raiz: Path, *, ctx=None, ejecutor=None, con=None) -> list[tuple[str, Estimacion]]:
    """Plan → verificador → ejecutor para todos los niveles del año: [(nivel, estimación)], 30 unidades en la ENDES 2024.
    Una `Falla` del verificador se vuelve error: una receta que el verificador no deja pasar no se ejecuta."""
    from .duckdb_seguro import conexion_segura
    from .ejecutor import Ejecutor
    from .verificador import Contexto, Falla, verificar

    receta.revisar_anio(anio)
    raiz = Path(raiz)
    ctx = ctx or Contexto.cargar(raiz)
    ejecutor = ejecutor or Ejecutor(raiz=raiz)
    con = con or conexion_segura(raiz)
    salida: list[tuple[str, Estimacion]] = []
    for nivel in niveles_del_anio(raiz, receta, anio):
        pc = verificar(receta.a_plan(anio, nivel), ctx, con)
        if isinstance(pc, Falla):
            raise PapError(f"El verificador no deja pasar la receta {receta.id} en {nivel}: {pc.dimension}: {pc.motivo}")
        salida += [(nivel, e) for e in ejecutor.ejecutar({anio: pc}, ctx)]
    return salida


@dataclass(frozen=True)
class Diferencia:
    """Una columna de una fila: lo del cubo, lo nuevo (redondeado a los decimales del cubo) y su diferencia."""
    columna: str
    cubo: float | None
    nuevo: float | None
    dif: float | None
    ok: bool


def comparar_fila(e: Estimacion, fila_cubo: dict[str, str], p: ParametrosRecetas) -> list[Diferencia]:
    """Los criterios del punto 1 de la definición de hecho: las columnas del cubo se comparan redondeadas a `cubo_decimales` con
    |dif| ≤ `cubo_tolerancia_unidades` unidades del último decimal (1e-8, contado en enteros para que el error de coma flotante
    no decida); n y gl idénticos; el n efectivo, contra mín(n, n efectivo del cubo) (el ejecutor lo topa en n y el cubo no).
    Un nulo en ambos lados coincide."""
    nuevo = en_unidades_del_cubo(e)
    unidad = 10.0 ** -p.cubo_decimales
    salida = []
    for col in COLUMNAS:
        c = None if fila_cubo[col] == "" else float(fila_cubo[col])
        n = nuevo[col]
        if col == "n_efectivo":
            c = float(fila_cubo["n_muestra"]) if c is None else min(float(fila_cubo["n_muestra"]), c)
            n = None if n is None else min(float(e.n), n)
        if col in EXACTAS:
            salida.append(Diferencia(col, c, n, None if c is None or n is None else n - c, c is not None and n is not None and n == c))
            continue
        r = None if n is None else round(float(n), p.cubo_decimales)
        if c is None or r is None:
            salida.append(Diferencia(col, c, r, None, c is None and r is None))
        else:
            salida.append(Diferencia(col, c, r, r - c, round(abs(r - c) / unidad) <= p.cubo_tolerancia_unidades))
    return salida


def leer_csv(ruta: Path, llave: tuple[str, ...]) -> dict[tuple, dict[str, str]]:
    with open(ruta, encoding="utf-8", newline="") as f:
        return {tuple(r[k] for k in llave): r for r in csv.DictReader(f)}


def reproducir_doradas(receta: Receta, estimaciones: list[tuple[str, Estimacion]]) -> list[dict]:
    """E-05 (R-ENC-18): cada dorada de la receta frente a la estimación de su dominio. Pasa si el valor redondeado a sus decimales
    difiere del publicado en ≤ `tolerancia_pp` (+1e-9) y, donde el INEI publica casos o CV, los casos son exactos y el CV (a los
    mismos decimales) difiere en ≤ `tolerancia_cv`. Mismo criterio que `capa0.indicadores._reproducir`, sobre la cifra nueva."""
    por_dominio = {(nivel, e.dominio[0]): e for nivel, e in estimaciones}
    filas = []
    for d in receta.doradas:
        e = por_dominio.get((d.nivel, d.territorio))
        fila = {"id_cifra": d.id_cifra, "nivel": d.nivel, "territorio": d.territorio, "publicado": d.valor_publicado, "nuestro": None,
                "dif_pp": None, "n": None, "casos_publicados": d.casos_publicados, "cv_publicado": d.cv_publicado, "cv_nuestro": None,
                "bloqueante": d.bloqueante, "pasa": False}
        if e is not None and not e.sin_datos:
            nuestro = round(100 * e.valor, d.decimales)
            dif = round(nuestro - d.valor_publicado, 6)
            cv = round(100 * e.ee / e.valor, d.decimales) if e.valor else None
            pasa = abs(dif) <= receta.tolerancia_pp + 1e-9 and (d.casos_publicados is None or d.casos_publicados == e.n)
            if d.cv_publicado is not None:
                pasa = pasa and cv is not None and abs(cv - d.cv_publicado) <= (receta.tolerancia_cv or 0.0) + 1e-9
            fila.update(nuestro=nuestro, dif_pp=dif, n=e.n, cv_nuestro=cv, pasa=bool(pasa))
        filas.append(fila)
    return filas


def compuertas_de(receta: Receta, estimaciones: list[tuple[str, Estimacion]], doradas: list[dict], raiz: Path) -> list[FilaReceta]:
    """Las compuertas (R-ENC-02 a 04) sobre cada estimación. `coincide_oficial` = la dorada de ese dominio pasa; la receta cuenta
    como verificada solo si su estado lo es."""
    ctx = contexto_compuertas(raiz)
    coinciden = {(d["nivel"], d["territorio"]) for d in doradas if d["pasa"]}
    return [FilaReceta(receta.indicador_id, nivel, e.dominio[0], e,
                       evaluar(e, ctx, verificada=receta.estado == "verificado", coincide_oficial=(nivel, e.dominio[0]) in coinciden))
            for nivel, e in estimaciones]


def firma_reglas(c: Compuerta) -> str:
    """Las reglas disparadas como en `m0-00_estados_cubo.csv`: «regla:acción:motivo;…»."""
    return ";".join(f"{x.regla}:{x.accion}:{x.motivo}" for x in c.resultados)
