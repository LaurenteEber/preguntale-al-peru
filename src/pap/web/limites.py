"""S3-07 — Límites de abuso y costo (P-05, P-07). Los contadores viven en memoria y se reinician al reiniciar el proceso: en local basta
y el slice 4 los revisa. Los valores salen de curados/web/parametros.yaml → `limites`; el reloj es inyectable para las pruebas.

- Por IP: a lo más N preguntas por ventana (deslizante). Solo cuentan las preguntas que llegan a `resolver`, no el paso 1 del formulario guiado.
- Tope diario: llamadas reales al LLM (reintentos del proveedor incluidos; los aciertos de caché no llaman) por día de Lima."""
from __future__ import annotations

import threading
from collections import deque
from contextvars import ContextVar
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from pap.interprete.llm import NoDisponible

IP_ACTUAL: ContextVar[str] = ContextVar("pap_ip_actual", default="desconocida")        # lo fija la guardia (registro.py)


class Limites:
    def __init__(self, par: dict, reloj=None):
        p = par["limites"]
        self.por_minuto = int(p["preguntas_por_minuto_por_ip"]["valor"])
        self.ventana = float(p["ventana_segundos"]["valor"])
        self.llamadas_por_dia = int(p["llamadas_llm_por_dia"]["valor"])
        self.cuerpo_max = int(p["cuerpo_max_bytes"]["valor"])
        self.zona = ZoneInfo(p["zona_horaria"]["valor"])
        self.reloj = reloj or (lambda: datetime.now(timezone.utc))
        self.llamadas_hoy = 0
        self._dia = self._hoy()
        self._golpes: dict[str, deque] = {}
        self._candado = threading.Lock()

    def _hoy(self):
        return self.reloj().astimezone(self.zona).date()

    def _rodar_dia(self) -> None:
        if self._hoy() != self._dia:
            self._dia, self.llamadas_hoy = self._hoy(), 0

    def ip_permitida(self, ip: str) -> bool:
        """Registra la pregunta y dice si cabe en la ventana; una pregunta rechazada no cuenta."""
        with self._candado:
            ahora = self.reloj().timestamp()
            for k in [k for k, v in self._golpes.items() if not v or v[-1] <= ahora - self.ventana]:
                del self._golpes[k]                              # la memoria no crece con IPs que ya no preguntan
            golpes = self._golpes.setdefault(ip, deque())
            while golpes and golpes[0] <= ahora - self.ventana:
                golpes.popleft()
            if len(golpes) >= self.por_minuto:
                return False
            golpes.append(ahora)
            return True

    def tope_alcanzado(self) -> bool:
        with self._candado:
            self._rodar_dia()
            return self.llamadas_hoy >= self.llamadas_por_dia

    def contar(self, n: int) -> None:
        with self._candado:
            self._rodar_dia()
            self.llamadas_hoy += n


class LlmContado:
    """Envuelve al LLM que recibe `interpretar()`: cuenta las peticiones reales y, al tope, ya no llama (lanza `NoDisponible`).
    `base`: el cliente (o uno falso); sin él, `crear()` da uno por llamada, como hace el intérprete. Un cliente sin `intentos_http`
    cuenta una petición por llamada. Se usa dentro del candado de la app, así que `tope_visto` es de la pregunta en curso."""

    def __init__(self, limites: Limites, base=None, crear=None):
        self.limites, self.base, self.crear = limites, base, crear
        self.tope_visto = False

    def interpretar_crudo(self, prompt, pregunta_limpia, version_prompt, error_previo=None):
        if self.limites.tope_alcanzado():
            self.tope_visto = True
            raise NoDisponible("tope_diario")
        cliente = self.base if self.base is not None else self.crear()
        antes = getattr(cliente, "intentos_http", None)
        try:
            if error_previo:
                return cliente.interpretar_crudo(prompt, pregunta_limpia, version_prompt, error_previo=error_previo)
            return cliente.interpretar_crudo(prompt, pregunta_limpia, version_prompt)
        finally:
            self.limites.contar(1 if antes is None else cliente.intentos_http - antes)
