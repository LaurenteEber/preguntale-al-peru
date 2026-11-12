"""`Estimacion` (M0-08; diseño §14, «Salida»): lo que el ejecutor entrega por dominio. Solo biblioteca estándar: el trabajador
del pool lo importa antes de fijar las variables de hilos, y el padre lo usa sin cargar `svy` ni `polars`.

Las proporciones van en 0–1 (no en porcentaje: el cubo multiplica por 100 al escribir su fila)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Estimacion:
    dominio: tuple[str, ...]                    # valores de las columnas `por`, en ese orden (sin el año)
    anio: int | None                            # el año del dominio; None si la llamada no lo declaró
    n: int                                      # casos del dominio dentro de u; 0 = «sin datos» (dominio pedido y vacío)
    valor: float | None = None                  # proporción (0–1)
    ee: float | None = None
    gl: int | None = None
    n_efectivo: float | None = None             # mín(n, p(1−p)/ee²); n si ee = 0 (no lo topa el cubo, que lo deja sin tope)
    deff: float | None = None
    ic_inf: float | None = None                 # Korn-Graubard, variante NCHS (E-04)
    ic_sup: float | None = None
    eventos: int = 0                            # casos con y = 1 dentro del dominio
    tasa_no_respuesta: float | None = None      # del ítem, sin ponderar; None = no se midió (M0 no resuelve `rol_faltante`)
    tasa_no_respuesta_ponderada: float | None = None

    @property
    def sin_datos(self) -> bool:
        return self.n == 0
