"""Ejecución del validador: etapas 0–7 por cifra (con precedencia R-MOTOR-02) y 8–10 por respuesta.

La degradación (R-MOTOR-01) la conduce `evaluar_con_degradacion`: si la cifra queda suprimida o pide agregar nivel o
agrupar años por un motivo degradable, se pide a la implementación de R-MOTOR-01 el siguiente paso de la secuencia,
se lee esa fila del cubo y se vuelve a evaluar desde la etapa 1. Cada paso queda en `motivo_nivel`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .nucleo import (ACUMULABLES, REGISTRO, CampoFaltante, Cifra, Contexto, Respuesta, Resultado, accion_final,
                     aplica, estado_cifra, normalizar)

ETAPAS_CIFRA = ("0_prerrequisitos", "1_territorio", "2_nivel", "3_denominador", "4_precision", "5_series",
                "6_divulgacion", "7_semaforo_cifra")
ETAPAS_RESPUESTA = ETAPAS_CIFRA + ("8_cruces", "9_semaforo_respuesta", "10_comunicacion")  # solo corre las reglas de ámbito «respuesta»


@dataclass
class Evaluacion:
    resultados: list[Resultado] = field(default_factory=list)
    accion_final: str = "publicar"
    estado_cifra: str = "publicable"
    errores: list[str] = field(default_factory=list)

    @property
    def bloqueos_cruce(self) -> list[Resultado]:
        """Comparaciones, series o cruces de esta cifra que no se pueden hacer (no cambian su estado)."""
        return [r for r in self.resultados if r.accion == "bloquear_cruce"]

    @property
    def acumulables(self) -> list[Resultado]:
        return [r for r in self.resultados if r.accion in ACUMULABLES]

    def motivos(self) -> list[str]:
        return [r.motivo for r in self.resultados if r.accion == self.accion_final and not r.modificador] or \
            [r.motivo for r in self.resultados if r.accion == self.accion_final]


def _como_lista(x) -> list[Resultado]:
    if x is None:
        return []
    return list(x) if isinstance(x, (list, tuple)) else [x]


def correr_regla(rid: str, objeto, ctx: Contexto, ambito: str | None = None) -> list[Resultado]:
    """Corre una regla registrada sobre una cifra o una respuesta: aplica_a, CampoFaltante → suprimir
    (metadato_faltante, R-MOTOR-02) y normalización de las acciones."""
    impl = REGISTRO[rid]
    ambito = ambito or impl.ambito
    if ambito == "cifra" and not aplica(ctx.regla(rid), objeto):
        return []
    try:
        res = _como_lista(impl.fn(objeto, ctx))
    except CampoFaltante as e:
        if ambito == "cifra":
            res = [Resultado(rid, "suprimir", "metadato_faltante", detalle={"campo": e.campo})]
        else:  # en una regla de respuesta no se suprime toda la respuesta: revisión humana sobre la respuesta
            res = [Resultado(rid, "revision_humana", "metadato_faltante", detalle={"campo": e.campo}, objetivo="respuesta")]
    for r in res:
        r.accion, modo = normalizar(r.accion, ctx, ambito)
        r.modo = r.modo or modo
        r.regla = r.regla or rid
    return res


def reglas_de(etapa: str, ctx: Contexto) -> list[str]:
    return [rid for rid in ctx.etapas[etapa]["reglas"] if rid in REGISTRO]


def evaluar_cifra(c: Cifra, ctx: Contexto, etapas=ETAPAS_CIFRA) -> Evaluacion:
    ev = Evaluacion()
    for et in etapas:
        for rid in reglas_de(et, ctx):
            if REGISTRO[rid].ambito != "cifra":
                continue
            c.resultados_previos = ev.resultados  # algunas reglas (semáforo) leen lo anterior
            c.accion_previa = accion_final(ev.resultados, ctx)
            ev.resultados += correr_regla(rid, c, ctx)
    ev.accion_final = accion_final(ev.resultados, ctx)
    ev.estado_cifra = estado_cifra(ev.accion_final, ev.resultados)
    c.estado_cifra, c.accion_final = ev.estado_cifra, ev.accion_final
    c.evaluacion = ev
    return ev


def evaluar_con_degradacion(c: Cifra, ctx: Contexto, construir, max_pasos: int = 8) -> tuple[Cifra, list[dict]]:
    """Evalúa y, si hace falta, degrada (R-MOTOR-01). `construir(paso)` devuelve la Cifra del paso pedido
    (otro nivel/territorio o periodo agrupado) o None si el cubo no la tiene. Devuelve la cifra final y la traza."""
    from .reglas_etapa0 import siguiente_paso  # implementación de R-MOTOR-01
    traza = []
    actual = c
    for _ in range(max_pasos):
        ev = evaluar_cifra(actual, ctx)
        traza.append({"nivel": actual.nivel, "territorio_id": actual.territorio_id, "anio": actual.anio,
                      "periodo_agrupado": actual.periodo_agrupado, "accion": ev.accion_final, "estado": ev.estado_cifra,
                      "motivos": ev.motivos()})
        paso = siguiente_paso(actual, ev, ctx)
        if paso is None:
            break
        nueva = construir(paso)
        if nueva is None:
            traza.append({"paso": paso, "resultado": "sin_fila_en_el_cubo"})
            break
        nueva.motivo_nivel = list(actual.motivo_nivel or []) + [{"paso": paso, "motivos": ev.motivos()}]
        nueva.cifra_original = actual.cifra_original or actual
        actual = nueva
    return actual, traza


def evaluar_respuesta(r: Respuesta, ctx: Contexto, etapas=ETAPAS_RESPUESTA) -> list[Resultado]:
    res = []
    for et in etapas:
        for rid in reglas_de(et, ctx):
            if REGISTRO[rid].ambito != "respuesta":
                continue
            r.resultados_previos = res
            res += correr_regla(rid, r, ctx, "respuesta")
    return res
