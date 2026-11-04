"""Formato de cifras para el texto y la ficha (reglas.json → lenguaje.redondeo y R-LENGUAJE-03: coma decimal,
espacio fino no separable U+202F como separador de miles y antes de «%», rangos en palabras)."""
from __future__ import annotations

FINO = " "


def _num(x: float, dec: int) -> str:
    s = f"{x:,.{dec}f}"  # 1,234.5
    return s.replace(",", "§").replace(".", ",").replace("§", FINO)


def pct(x: float, dec: int = 1) -> str:
    if x is None:
        return "—"
    if 0 <= x < 0.5:
        return f"menos de 1{FINO}%"
    return f"{_num(x, dec)}{FINO}%"


def pct_cifra(valor: float, ic_inf: float | None, ic_sup: float | None, semaforo: str | None,
              estado: str | None = None) -> str:
    """Porcentaje de encuesta o registro: verde → 1 decimal; ámbar, rojo o referencial → «alrededor de N % (entre A % y
    B %)» en enteros (lenguaje.redondeo)."""
    if semaforo == "verde" and estado not in ("referencial",):
        return pct(valor, 1)
    base = f"alrededor de {pct(valor, 0)}"
    if ic_inf is not None and ic_sup is not None:
        # revisión de usuario (12/10/2026): si en enteros el intervalo casi no se distingue de la cifra («alrededor de
        # 8 % (entre 8 % y 9 %)»), el intervalo va con 1 decimal
        d = 1 if round(ic_sup) - round(ic_inf) <= 1 else 0
        base += f" (entre {pct(ic_inf, d)} y {pct(ic_sup, d)})"
    return base


def intervalo(ic_inf: float, ic_sup: float, d: int = 0) -> str:
    """Solo el intervalo, en enteros salvo que se pidan decimales (p. ej. si cruza un umbral, P4-03)."""
    return f"entre {pct(ic_inf, d)} y {pct(ic_sup, d)}"


MEDIDAS_MONTO = ("devengado", "devengado_constante", "pim", "pia")  # montos en soles (S1-12: también los constantes)


def monto(soles: float) -> str:
    """>= S/ 1 millón: millones con 1 decimal; < 1 millón: miles enteros (soles corrientes)."""
    if soles is None:
        return "—"
    if abs(soles) >= 1e6:
        return f"S/{FINO}{_num(soles / 1e6, 1)} millones"
    return f"S/{FINO}{_num(soles / 1e3, 0)} mil"


def poblacion(n: float) -> str:
    if n >= 1e6:
        return f"{_num(n / 1e6, 2)} millones"
    return f"{_num(n / 1e3, 1)} mil"


HUMANO = {"LIMA_METROPOLITANA": "Lima Metropolitana", "LIMA_REGION": "Lima Región", "CALLAO": "Callao",
          "AREA_METROPOLITANA_LIMA_CALLAO": "Lima Metropolitana y Callao",
          "MEF-DA-PRESUPUESTO-EJECUCION-GASTO": "el registro de gasto del MEF", "INEI-ENDES": "la ENDES",
          "INEI-ENAHO": "la ENAHO", "INS-CENAN-SIEN": "el SIEN", "INEI-MAPA-POBREZA": "el Mapa de Pobreza",
          "encuesta_muestral": "encuesta a hogares", "registro_administrativo": "registro de atenciones",
          "presupuestal_financiero": "gasto registrado", "estimacion_modelada": "estimación con modelo",
          "anemia_6_35m": "anemia en niñas y niños de 6 a 35 meses", "pobreza_monetaria": "pobreza monetaria",
          "INEI-PROYECCIONES-DEPARTAMENTAL-EDAD": "la proyección de población del INEI",
          "INEI-PROYECCIONES-POBLACION-DISTRITAL": "la proyección de población del INEI",
          "LM": "Lima Metropolitana", "LR": "Lima Región"}


def humanizar(texto: str | None, extra: dict | None = None) -> str | None:
    """Mensajes del validador → lenguaje ciudadano: códigos internos por nombres y marcadores {x} rellenados con
    `extra`. Devuelve None si queda algún marcador sin rellenar (el mensaje no se muestra; queda en el registro)."""
    import re
    if not texto:
        return None
    for k, v in (extra or {}).items():
        texto = texto.replace("{" + k + "}", str(v))
    for k in sorted(HUMANO, key=len, reverse=True):
        texto = re.sub(rf"(?<![\w-]){re.escape(k)}(?![\w-])", HUMANO[k], texto)
    if re.search(r"\{[a-z_]+\}", texto):
        return None
    return texto
