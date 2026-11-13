"""Plan de inferencia (M0-07; diseño §11.2 y anexo A): lo que sale del planificador o de una receta, ya normalizado.

El plan **no contiene SQL ni texto libre**: solo identificadores del índice (`var_id`), operadores de la gramática (§11.3),
números e identificadores de las tablas curadas. Todos los modelos son `extra="forbid"`: un campo que no existe no pasa.
El diseño muestral **no va en el plan**: lo agrega el verificador (`PlanCompleto`). El universo analítico tampoco, salvo en una receta,
que lo nombra (`universo_analitico`, M1-03): ahí el verificador aplica ese universo completo; en un plan compuesto lo elige el verificador por
la medición de las variables que intervienen.

`id_plan` = sha256 del JSON canónico (claves ordenadas, sin espacios): el mismo plan da siempre el mismo id.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, field_validator, model_validator

from .tablas_curadas import CategoriaCorte, DisenoMuestral, Territorio as TerritorioCurado, UniversoAnalitico, leer_territorios

RAIZ_REPO = Path(__file__).resolve().parents[3]
OPERADORES = ("en", "entre", "<", "≥", "es_nulo", "no_es_nulo")
COMBINACIONES = ("una", "alguna_de", "todas_de")
MAX_CONDICIONES = 3                                   # §11.3: «con un máximo de 3 condiciones»

# Solo letras, dígitos y «_» (sin comillas, espacios, «;» ni «-»): el alfabeto de lo que sí puede llegar a una consulta.
_ID = r"^[A-Za-z][A-Za-z0-9_]{0,63}$"
_VAR_ID = r"^[A-Z][A-Z0-9_]{1,15}·\d{4}·[A-Za-z][A-Za-z0-9_]{0,63}·[A-Za-z][A-Za-z0-9_]{0,63}$"
_ID_TERRITORIO = r"^[A-Za-z0-9_]{1,32}$"

Numero = Annotated[StrictInt | StrictFloat, Field(allow_inf_nan=False)]


class _Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


@lru_cache(maxsize=1)
def niveles_territorio() -> tuple[str, ...]:
    """Niveles de `curados/inferencia/territorios.yaml` (la fuente de verdad de `Territorio.nivel`)."""
    return tuple(t.nivel for t in leer_territorios(RAIZ_REPO))


class Condicion(_Modelo):
    """Un predicado sobre una variable del índice (§11.3). `valores` solo lleva números: nunca texto."""
    var: str = Field(pattern=_VAR_ID)
    op: Literal["en", "entre", "<", "≥", "es_nulo", "no_es_nulo"]
    valores: tuple[Numero, ...] = ()

    @field_validator("valores")
    @classmethod
    def _enteros_como_enteros(cls, v):
        return tuple(int(x) if isinstance(x, float) and x.is_integer() else x for x in v)       # 6 y 6.0 dan el mismo id_plan

    @model_validator(mode="after")
    def _forma(self):
        n = len(self.valores)
        if self.op == "en" and n < 1:
            raise ValueError("«en» lleva al menos un valor")
        if self.op == "entre" and (n != 2 or self.valores[0] > self.valores[1]):
            raise ValueError("«entre» lleva dos valores, el primero no mayor que el segundo")
        if self.op in ("<", "≥") and n != 1:
            raise ValueError(f"«{self.op}» lleva un valor")
        if self.op in ("es_nulo", "no_es_nulo") and n:
            raise ValueError(f"«{self.op}» no lleva valores")
        if n > 50:
            raise ValueError("demasiados valores")
        return self


class Indicador(_Modelo):
    combinar: Literal["una", "alguna_de", "todas_de"]
    condiciones: tuple[Condicion, ...] = Field(min_length=1, max_length=MAX_CONDICIONES)

    @model_validator(mode="after")
    def _una(self):
        if self.combinar == "una" and len(self.condiciones) != 1:
            raise ValueError("«una» lleva exactamente una condición")
        return self


class Universo(_Modelo):
    """Restricciones del universo del plan; se cumplen todas a la vez (y con el universo analítico que agrega el verificador)."""
    restricciones: tuple[Condicion, ...] = Field(default=(), max_length=MAX_CONDICIONES)


class Territorio(_Modelo):
    """`nivel` es uno de `territorios.yaml`; `id` vacío = todas las unidades del nivel."""
    nivel: str
    id: str | None = Field(default=None, pattern=_ID_TERRITORIO)

    @field_validator("nivel")
    @classmethod
    def _nivel_curado(cls, v):
        if v not in niveles_territorio():
            raise ValueError(f"nivel {v!r} fuera de territorios.yaml {list(niveles_territorio())}")
        return v


class Plan(_Modelo):
    version_plan: Literal[1] = 1
    origen: Literal["compuesto", "receta"]
    receta_id: str | None = Field(default=None, pattern=_ID)
    encuesta: Literal["ENDES", "ENAHO"]
    anios: tuple[int, ...] = Field(min_length=1, max_length=32)
    unidad: str = Field(pattern=_ID)
    medida: str = Field(pattern=_ID)
    universo_analitico: str | None = Field(default=None, pattern=_ID)       # solo una receta lo nombra (M1-03, tarea 2)
    indicador: Indicador
    universo: Universo = Universo()
    cortes: tuple[Annotated[str, Field(pattern=_ID)], ...] = Field(default=(), max_length=8)
    territorio: Territorio

    @field_validator("anios")
    @classmethod
    def _anios(cls, v):
        if any(not 1900 <= a <= 2100 for a in v) or len(set(v)) != len(v):
            raise ValueError("años repetidos o fuera de rango")
        return tuple(sorted(v))

    @model_validator(mode="after")
    def _receta(self):
        if (self.origen == "receta") != (self.receta_id is not None):
            raise ValueError("receta_id va si y solo si el origen es «receta»")
        if self.universo_analitico is not None and self.origen != "receta":
            raise ValueError("universo_analitico lo nombra solo una receta: en un plan compuesto lo elige el verificador por la medición")
        return self

    def canonico(self) -> str:
        d = self.model_dump(mode="json")
        if d["universo_analitico"] is None:                 # los planes que no lo nombran conservan el id_plan que tenían antes de M1-03
            del d["universo_analitico"]
        return json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @property
    def id_plan(self) -> str:
        return hashlib.sha256(self.canonico().encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ plan completado por el verificador

@dataclass(frozen=True)
class UnionPlan:
    """Una unión izquierda de una relación de archivos_<encuesta>_<año>.yaml. `hacia="padre"` (la de siempre): se trae el padre y cuelga
    del hijo, que ya está en la consulta. `hacia="hijo"` (M1-03): se trae el hijo —que es 1:1 o 1:0..1 con su padre— y cuelga del padre,
    que ya está en la consulta; así se llega de un hijo a su hermano por el padre común."""
    hijo: str
    padre: str
    pares: tuple[tuple[str, str], ...]          # (columna del hijo, columna del padre)
    cardinalidad: str = "n:1"
    hacia: str = "padre"

    @property
    def unido(self) -> str:
        """El archivo que esta unión agrega a la consulta."""
        return self.padre if self.hacia == "padre" else self.hijo

    @property
    def ancla(self) -> str:
        """El archivo que ya debe estar en la consulta."""
        return self.hijo if self.hacia == "padre" else self.padre

    @property
    def texto(self) -> str:
        return f"{self.ancla}→{self.unido}"


@dataclass(frozen=True)
class CorteResuelto:
    """Un corte ya ubicado en un archivo. `categorias`: lo que devuelve la columna del dominio → su rótulo (el código si la columna se usa
    tal cual; el propio rótulo si hay `reglas`). `reglas` (M1-03): categorías por tramos o agrupadas; el SQL arma un `CASE` con los
    rótulos como parámetros."""
    id: str
    archivo: str
    variable: str
    categorias: dict[int | str, str]
    reglas: tuple[CategoriaCorte, ...] = ()


@dataclass(frozen=True)
class PlanCompleto:
    """Lo que devuelve el verificador: el plan más lo que él agrega desde las tablas curadas (§11.2)."""
    plan: Plan
    universo_analitico: UniversoAnalitico
    diseno: DisenoMuestral
    territorio: TerritorioCurado
    archivo_unidad: str
    uniones: tuple[UnionPlan, ...]               # todas las uniones, en el orden en que se hacen
    uniones_u_y: tuple[UnionPlan, ...]           # solo las que necesitan u e y (para el control «antes»)
    cortes: tuple[CorteResuelto, ...] = ()
    ajustes: tuple[str, ...] = ()                # p. ej. «el nivel LIMA_REGION subió a departamento (R-ENC-06)»
    controles: dict | None = field(default=None, compare=False)

    @property
    def id_plan(self) -> str:
        return self.plan.id_plan
