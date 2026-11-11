"""Compuertas de proporciones (M0-09; diseño §15.1 y §15.2). **No hay lógica nueva**: el árbol aplica R-ENC-02, R-ENC-03 y R-ENC-04
con las funciones de `pap.motor.validador.reglas_etapa4` (las mismas que usa el validador del cubo) y los parámetros de
`reglas/reglas.json`; este módulo solo las ordena, las combina y le pone la confianza.

Árbol (§15.1), en el orden de la tabla:
1. R-ENC-02, n < 25 → suprimir (corta);
2. R-ENC-02, 25 ≤ n ≤ 49 → referencial (sigue);
3. R-ENC-04 si p < 10 % o p > 90 %: n efectivo < 30, ancho ≥ 30 pp o ancho relativo > 130 % con ancho > 5 pp → suprimir (corta);
4. R-ENC-04: ancho relativo > 59 % con ancho > 5 pp, n efectivo < 50, gl < 8 o CV ref > 15 % → referencial;
5. R-ENC-04: numerador 0 o igual a n → rótulo «menos de {límite superior}» / «más de {límite inferior}»;
6. R-ENC-03 si 10 % ≤ p ≤ 90 %: CV > 30 % → suprimir (corta);
7. R-ENC-03: 15 % < CV ≤ 30 % o gl < 8 → referencial;
8. no respuesta del ítem: **no se aplica** (K-07 sin aprobar; la tasa solo se informa, sin efecto).
Las que suprimen cortan, las referenciales se acumulan y gana la más severa; se guardan todos los motivos. Un dominio sin casos
(n = 0) es «sin datos». Un dato que la regla necesita y falta (por ejemplo un ee nulo) suprime con `metadato_faltante` (R-MOTOR-02).

Unidades: `Estimacion` va en 0–1; las reglas leen el cubo en % (`valor`, `ee`, `ic_*`), así que aquí se convierte al armar la `Cifra`.
"""
from __future__ import annotations

import functools
import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..motor.validador import cargar
from ..motor.validador.nucleo import Cifra, Contexto, Resultado, accion_final, estado_cifra
from ..motor.validador.validador import correr_regla
from ..zip_seguro import RUTA_PARAMETROS
from .estimacion import Estimacion

RAIZ_REPO = Path(__file__).resolve().parents[3]
REGLAS_PROPORCION = ("R-ENC-02", "R-ENC-03", "R-ENC-04")      # en el orden de la tabla del §15.1

# Lo que `aplica_a` de R-ENC-02 a 04 exige de la cifra; las proporciones de encuesta del piloto lo cumplen por construcción.
META_ENCUESTA = {"tipo_estimacion": "proporcion", "naturaleza_dato": "encuesta_muestral", "tipo_medida": "prevalencia",
                 "base_geografica_usada": "muestra", "fuente_principal": "INEI-ENDES"}

CONFIANZA_ALTA, CONFIANZA_MEDIA, CONFIANZA_BAJA = "alta", "media", "baja"
MOTIVO_CONFIANZA = {
    CONFIANZA_ALTA: "La receta está verificada y su cifra coincide con la cifra oficial.",
    CONFIANZA_MEDIA: "La receta está verificada, pero no hay cifra oficial con qué compararla.",
    CONFIANZA_BAJA: "La cifra es aproximada: la encuesta la mide con poca precisión.",
}


@dataclass(frozen=True)
class Motivo:
    regla: str
    accion: str                  # suprimir | publicar_referencial | rotular (vocabulario de R-MOTOR-02)
    codigo: str                  # pocos_casos | precision | metadato_faltante | sin_datos
    clausula: str | None = None
    rotulo: str | None = None


@dataclass(frozen=True)
class Compuerta:
    estado: str                                  # publicable | referencial | suprimida | sin_datos
    motivos: tuple[Motivo, ...] = ()
    confianza: str | None = None                 # alta | media | baja; None si la cifra no se publica
    motivo_confianza: str | None = None
    rotulo: str | None = None                    # «menos de X %» / «más de X %» cuando p = 0 o p = 1
    tasa_no_respuesta: float | None = None       # solo informativa (paso 8 sin aprobar, K-07)
    resultados: tuple[Resultado, ...] = field(default=(), repr=False)

    @property
    def publicable(self) -> bool:
        return self.estado in ("publicable", "referencial")


def contexto_compuertas(raiz: Path = RAIZ_REPO) -> Contexto:
    """Contexto mínimo: solo `reglas/reglas.json` (reglas, parámetros globales, etapas). No lee el cubo ni la biblioteca."""
    cargar()
    rj = json.loads((Path(raiz) / "reglas" / "reglas.json").read_text(encoding="utf-8"))
    ctx = Contexto(reglas={r["id"]: r for r in rj["reglas"]}, pg=rj["parametros_globales"], catalogo={}, inferencia=[], dominios=[],
                   ubigeos=None, manifiestos={}, doradas=[], cruces=[], indicadores={}, lenguaje=rj.get("lenguaje"), ficha=rj.get("ficha_limites"))
    ctx.etapas = rj["etapas"]
    return ctx


def parametros(ctx: Contexto | None = None) -> dict[str, dict]:
    """Los parámetros de R-ENC-02, 03 y 04 tal como están en `reglas.json` (para mostrarlos o probarlos)."""
    ctx = ctx or contexto_compuertas()
    return {rid: dict(ctx.regla(rid).get("parametros") or {}) for rid in REGLAS_PROPORCION}


def cifra_desde_estimacion(est: Estimacion, meta: dict | None = None) -> Cifra:
    """`Estimacion` (0–1) → `Cifra` (cubo en %). Numerador = casos con y = 1 y denominador = n, para el rótulo de p = 0 o p = 1."""
    pct = lambda x: None if x is None else x * 100  # noqa: E731
    fila = {**META_ENCUESTA, **(meta or {}), "n_muestra": est.n, "valor": pct(est.valor), "ee": pct(est.ee), "ic_inf": pct(est.ic_inf),
            "ic_sup": pct(est.ic_sup), "gl": est.gl, "n_efectivo": est.n_efectivo, "numerador": est.eventos if est.n else None,
            "denominador": est.n if est.n else None}
    return Cifra.desde({k: v for k, v in fila.items() if v is not None}, None)


@functools.lru_cache(maxsize=1)
def confianza_receta_no_verificada() -> str:
    """`compuertas.confianza_receta_no_verificada` de curados/inferencia/parametros.yaml (supuesto M0-09)."""
    c = yaml.safe_load(Path(RUTA_PARAMETROS).read_text(encoding="utf-8"))["compuertas"]
    return str(c["confianza_receta_no_verificada"]["valor"])


def _confianza(estado: str, verificada: bool, coincide_oficial: bool, compuesto: bool) -> tuple[str | None, str | None]:
    """§15.2: alta = verificada y coincide con su cifra oficial, publicada sin referencial; media = verificada sin cifra oficial
    para ese dominio, o plan compuesto, publicada sin referencial; baja = cualquier cifra referencial."""
    if estado == "referencial":
        return CONFIANZA_BAJA, MOTIVO_CONFIANZA[CONFIANZA_BAJA]
    if estado != "publicable":
        return None, None
    if not verificada:                                   # el §15.2 no lo prevé; ante la duda, la más baja (supuesto M0-09)
        return confianza_receta_no_verificada(), "La receta aún no está verificada."
    if coincide_oficial and not compuesto:
        return CONFIANZA_ALTA, MOTIVO_CONFIANZA[CONFIANZA_ALTA]
    return CONFIANZA_MEDIA, MOTIVO_CONFIANZA[CONFIANZA_MEDIA]


def evaluar_cifra(c: Cifra, ctx: Contexto | None = None, *, verificada: bool, coincide_oficial: bool = False,
                  compuesto: bool = False, tasa_no_respuesta: float | None = None) -> Compuerta:
    """El árbol del §15.1 sobre una `Cifra` ya armada (en % como el cubo)."""
    ctx = ctx or contexto_compuertas()
    if c.n_sin_ponderar is not None and int(c.n_sin_ponderar) == 0:
        m = Motivo("R-ENC-02", "suprimir", "sin_datos", "n_sin_ponderar == 0")
        return Compuerta("sin_datos", (m,), tasa_no_respuesta=tasa_no_respuesta)
    resultados: list[Resultado] = []
    for rid in REGLAS_PROPORCION:
        resultados += correr_regla(rid, c, ctx)
        if any(r.accion == "suprimir" for r in resultados):          # lo que suprime corta el árbol
            break
    final = accion_final(resultados, ctx)
    estado = estado_cifra(final, resultados)
    rotulo = next((r.rotulo for r in resultados if r.accion == "rotular"), None) if estado in ("publicable", "referencial") else None
    publicable = estado in ("publicable", "referencial")             # suprimida: ningún rótulo en los motivos (H09-4)
    motivos = tuple(Motivo(r.regla, r.accion, r.motivo, r.clausula, r.rotulo if r.accion == "rotular" and publicable else None)
                    for r in resultados)
    confianza, por_que = _confianza(estado, verificada, coincide_oficial, compuesto)
    return Compuerta(estado, motivos, confianza, por_que, rotulo, tasa_no_respuesta, tuple(resultados))


def evaluar(est: Estimacion, ctx: Contexto | None = None, *, meta: dict | None = None, verificada: bool,
            coincide_oficial: bool = False, compuesto: bool = False) -> Compuerta:
    """El árbol del §15.1 sobre la `Estimacion` de un dominio (0–1)."""
    return evaluar_cifra(cifra_desde_estimacion(est, meta), ctx, verificada=verificada, coincide_oficial=coincide_oficial,
                         compuesto=compuesto, tasa_no_respuesta=est.tasa_no_respuesta)
