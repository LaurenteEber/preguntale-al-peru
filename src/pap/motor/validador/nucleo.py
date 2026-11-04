"""Núcleo del validador (P2): campos de una cifra, contexto de la biblioteca, registro de reglas, aplica_a,
normalización y precedencia de acciones (R-MOTOR-02).

Contrato: docs/especificaciones/contrato_validador.md. Cada regla del alcance del piloto es una función pura registrada con
@regla("R-…"): recibe la cifra (o la respuesta) y el contexto y devuelve None (no dispara), un Resultado o una lista.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

# ======================================================================= errores y resultados


class CampoFaltante(Exception):
    """Un campo que la regla necesita está vacío y la regla no define el caso: R-MOTOR-02 → suprimir (metadato_faltante)."""

    def __init__(self, campo: str):
        super().__init__(campo)
        self.campo = campo


@dataclass
class Resultado:
    regla: str
    accion: str                      # vocabulario de R-MOTOR-02 (se normaliza con normalizacion_salidas)
    motivo: str                      # código corto: precision, pocos_casos, nivel_no_representativo, sin_datos, …
    clausula: str | None = None      # cláusula de la condición que se cumplió (texto corto)
    detalle: dict = field(default_factory=dict)   # valores y parámetros usados
    mensaje: str | None = None       # texto al usuario (mensaje_usuario de la regla, rellenado)
    rotulo: str | None = None        # rótulo que debe acompañar a la cifra
    aviso: str | None = None         # código de aviso (p. ej. ambito_no_dominio)
    nivel_minimo: str | None = None  # para agregar_nivel / solicitar_degradacion (R-MOTOR-01)
    modo: str | None = None          # rango | suavizada | lista (normalizacion_salidas)
    objetivo: str | None = None      # en reglas de respuesta: id_cifra afectada, «cruce:<id>» o «respuesta»
    modificador: bool = False        # cláusula «Modificador»/«Además»: actúa sobre la acción resultante

    def a_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v not in (None, {}, False)}


# ======================================================================= cifra y respuesta

class Campos:
    """Bolsa de campos con acceso por atributo. `c.x` devuelve None si falta; `c.req("x")` lanza CampoFaltante."""

    def __init__(self, datos: dict | None = None):
        object.__setattr__(self, "_d", dict(datos or {}))

    def __getattr__(self, k):
        if k.startswith("__"):
            raise AttributeError(k)
        return self._d.get(k)

    def __setattr__(self, k, v):
        self._d[k] = v

    def __contains__(self, k):
        return self._d.get(k) is not None

    def get(self, k, defecto=None):
        v = self._d.get(k)
        return defecto if v is None else v

    def req(self, *ks):
        vals = []
        for k in ks:
            v = self._d.get(k)
            if v is None or (isinstance(v, float) and v != v):
                raise CampoFaltante(k)
            vals.append(v)
        return vals[0] if len(vals) == 1 else tuple(vals)

    def datos(self) -> dict:
        return dict(self._d)


class Cifra(Campos):
    """Una cifra en evaluación: fila del cubo + metadatos de dim_indicador (al primer nivel) + consulta + estado.
    Alias de nombres que usan las reglas: n_sin_ponderar = n_muestra; base_geografica = base_geografica_usada;
    fuente = fuente_principal; p y estimacion en proporción (0–1) para proporciones."""

    @classmethod
    def desde(cls, fila: dict, indicador: dict | None = None, consulta: dict | None = None) -> "Cifra":
        d = dict(indicador or {})
        d["indicador_id"] = d.pop("id", d.get("indicador_id"))
        d.update({k: v for k, v in (fila or {}).items()})
        d.update(consulta or {})
        if isinstance(d.get("avisos"), str):
            d["avisos"] = json.loads(d["avisos"])
        d.setdefault("avisos", [])
        d.setdefault("n_sin_ponderar", d.get("n_muestra"))
        d.setdefault("base_geografica", d.get("base_geografica_usada"))
        d.setdefault("fuente", d.get("fuente_principal"))
        if d.get("tipo_estimacion") == "proporcion" and d.get("valor") is not None and d.get("medida") != "cobertura":
            d.setdefault("p", float(d["valor"]) / 100)
            d.setdefault("estimacion", float(d["valor"]) / 100)
            if d.get("ee") is not None:
                d.setdefault("ee_prop", float(d["ee"]) / 100)
        else:
            d.setdefault("estimacion", d.get("valor"))
        d.setdefault("motivo_nivel", [])
        d.setdefault("nivel_publicado", d.get("nivel"))
        d.setdefault("sensibilidad_divulgacion", d.get("sensibilidad_divulgacion") or "normal")
        return cls(d)


class Respuesta(Campos):
    """Respuesta en evaluación (etapas 8–10): consulta, cifras evaluadas (lista de Cifra con su evaluación), cruces
    pedidos, texto redactado y ficha. Campos: intencion_pregunta, nivel_pedido, cifras, cruces, texto, ficha,
    cifras_permitidas, respuesta_parcial."""


# ======================================================================= contexto

class Contexto:
    """Lo que las reglas consultan de la biblioteca. Se arma una vez por corrida (cargar_contexto) y en los casos de
    prueba se puede sobrescribir cualquier parte (con_sobrescrituras)."""

    def __init__(self, reglas: dict, pg: dict, catalogo: dict, inferencia: list[dict], dominios: list[dict],
                 ubigeos: Any, manifiestos: dict, doradas: list[dict], cruces: list[dict], indicadores: dict,
                 cubo: Any = None, anio_actual: int = 2026, fecha_referencia: str = "2026-10-10", lenguaje: dict | None = None,
                 ficha: dict | None = None):
        self.reglas, self.pg, self.catalogo, self.inferencia = reglas, pg, catalogo, inferencia
        self.dominios, self.ubigeos, self.manifiestos, self.doradas = dominios, ubigeos, manifiestos, doradas
        self.cruces, self.indicadores, self.cubo = cruces, indicadores, cubo
        self.anio_actual, self.fecha_referencia = anio_actual, fecha_referencia
        self.lenguaje, self.ficha = lenguaje or {}, ficha or {}

    def regla(self, rid: str) -> dict:
        return self.reglas[rid]

    def param(self, rid: str, clave: str, defecto=None):
        return (self.reglas[rid].get("parametros") or {}).get(clave, defecto)

    def nivel_rank(self, nivel: str) -> float | None:
        r = self.pg["NIVEL_RANK"].get(nivel)
        return r if isinstance(r, (int, float)) else None

    def fila_cubo(self, indicador_id: str, anio: int, nivel: str, territorio_id: str, medida: str | None = None,
                  linea: str = "cifra") -> dict | None:
        if self.cubo is None:
            return None
        c = self.cubo
        m = (c.indicador_id == indicador_id) & (c.anio == int(anio)) & (c.nivel == nivel) & \
            (c.territorio_id == str(territorio_id)) & (c.linea == linea)
        if medida:
            m &= c.medida == medida
        x = c[m]
        return None if x.empty else {k: (None if _nulo(v) else v) for k, v in x.iloc[0].to_dict().items()}

    def con_sobrescrituras(self, sob: dict | None) -> "Contexto":
        if not sob:
            return self
        import copy
        nuevo = copy.copy(self)
        for k, v in sob.items():
            actual = getattr(nuevo, k, None)
            if isinstance(actual, dict) and isinstance(v, dict):
                m = copy.deepcopy(actual)
                for kk, vv in v.items():
                    if isinstance(m.get(kk), dict) and isinstance(vv, dict):
                        m[kk] = {**m[kk], **vv}
                    else:
                        m[kk] = vv
                setattr(nuevo, k, m)
            else:
                setattr(nuevo, k, v)
        return nuevo


def _nulo(v) -> bool:
    try:
        return v is None or (isinstance(v, float) and v != v) or (hasattr(v, "__class__") and str(v) in ("<NA>", "nan"))
    except Exception:
        return False


# ======================================================================= registro

@dataclass
class ReglaImpl:
    id: str
    ambito: str          # «cifra» (etapas 0–7) o «respuesta» (etapas 8–10)
    fn: Callable
    nota: str = ""


REGISTRO: dict[str, ReglaImpl] = {}


def regla(rid: str, ambito: str = "cifra", nota: str = ""):
    """Decorador: registra la implementación de una regla de reglas.json."""
    def deco(fn):
        if rid in REGISTRO:
            raise ValueError(f"regla registrada dos veces: {rid}")
        REGISTRO[rid] = ReglaImpl(rid, ambito, fn, nota)
        return fn
    return deco


def aplica(regla_json: dict, c: Campos) -> bool:
    """semantica_aplica_a de reglas.json: «fuentes» no vacía = lista cerrada; si está vacía, se exigen a la vez todas
    las listas no vacías (naturaleza_dato, tipo_medida, base_geografica, esta sobre base_geografica_usada)."""
    a = regla_json.get("aplica_a") or {}
    fuentes = a.get("fuentes") or []
    if fuentes:
        return c.get("fuente_principal") in fuentes
    for campo, valor in (("naturaleza_dato", c.get("naturaleza_dato")), ("tipo_medida", c.get("tipo_medida")),
                         ("base_geografica", c.get("base_geografica_usada") or c.get("base_geografica"))):
        lista = a.get(campo) or []
        if lista and valor not in lista:
            return False
    return True


# ======================================================================= normalización y precedencia (R-MOTOR-02)

ACUMULABLES = ("rotular", "advertir", "revision_humana")


def normalizar(accion: str, ctx: Contexto, ambito: str = "cifra") -> tuple[str, str | None]:
    """Acción de una regla → acción del vocabulario (y modo). normalizacion_salidas de R-MOTOR-02."""
    tabla = ctx.param("R-MOTOR-02", "normalizacion_salidas", {})
    orden = ctx.param("R-MOTOR-02", "orden_restriccion", [])
    if accion in orden or accion in ACUMULABLES:
        return accion, None
    if accion == "bloquear":
        return ("suprimir" if ambito == "cifra" else "bloquear_cruce"), None
    destino = tabla.get(accion)
    if destino is None:
        raise ValueError(f"acción fuera del vocabulario de R-MOTOR-02: {accion}")
    base = destino.split(" ")[0]
    modo = None
    if "modo=" in destino:
        modo = destino.split("modo=")[1].split(";")[0].split(")")[0]
    elif "(corrector)" in destino:
        modo = "corrector"  # «regenerar»: el texto se vuelve a generar
    return base, modo


def accion_final(resultados: list[Resultado], ctx: Contexto, ambito: str = "cifra") -> str:
    """La acción más restrictiva entre las no acumulables (por omisión, publicar). En una cifra, `bloquear_cruce` no
    compite (auditoría P2, H-1): es una marca sobre sus comparaciones o cruces y no puede volver publicable una cifra
    suprimida o referencial; se informa aparte (Evaluacion.bloqueos_cruce)."""
    orden = ctx.param("R-MOTOR-02", "orden_restriccion")
    acciones = [r.accion for r in resultados if r.accion in orden and not (ambito == "cifra" and r.accion == "bloquear_cruce")]
    if not acciones:
        return "publicar"
    return min(acciones, key=orden.index)


ESTADO = {"publicar": "publicable", "publicar_referencial": "referencial", "suprimir": "suprimida",
          "agregar_nivel": "agregada", "agrupar_anios": "agrupada", "bloquear_cruce": "publicable"}
MOTIVOS_SIN_DATOS = {"sin_datos", "insumo_en_ingesta", "tabla_curada_sin_respaldo", "sin_fila", "fuera_de_cobertura"}


def estado_cifra(final: str, resultados: list[Resultado]) -> str:
    if final == "suprimir" and any(r.accion == "suprimir" and r.motivo in MOTIVOS_SIN_DATOS for r in resultados):
        return "sin_datos"
    return ESTADO[final]
