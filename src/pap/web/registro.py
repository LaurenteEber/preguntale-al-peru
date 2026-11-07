"""S3-07 — Registros sin la pregunta (P-03). El acceso guarda solo método, ruta (sin la consulta de la URL), código y tiempo. Un error guarda
el tipo de la excepción, nunca su mensaje ni la traza (los mensajes de consulta repiten el lugar escrito). La guardia es el manejador global:
atrapa lo que ningún `except` atrapó antes de que llegue a uvicorn, que registraría la traza completa. También acota el tamaño del cuerpo
y fija la IP de la petición para el límite por IP (limites.py). La web no escribe `respuesta.json` ni ningún otro archivo."""
from __future__ import annotations

import json
import logging
import sys
import time

from starlette.responses import Response

from pap.web import limites as L

log = logging.getLogger("pap.web")
acceso = logging.getLogger("pap.web.acceso")


class _Stderr(logging.StreamHandler):
    """Escribe en el `sys.stderr` de cada momento (no en el que había al crearlo)."""

    def __init__(self):
        logging.Handler.__init__(self)

    @property
    def stream(self):
        return sys.stderr


class FiltroPrivado(logging.Filter):
    """Quita la traza y el mensaje de la excepción de cada registro (queda el tipo); con `descartar`, tira el registro."""

    def __init__(self, descartar: bool = False):
        super().__init__()
        self.descartar = descartar

    def filter(self, record: logging.LogRecord) -> bool:
        if self.descartar:
            return False
        if record.exc_info and record.exc_info[0] is not None:
            record.msg, record.args = f"{record.getMessage().strip()} [{record.exc_info[0].__name__}]", None
        record.exc_info = record.exc_text = record.stack_info = None
        return True


def instalar() -> None:
    """Una sola vez por proceso: el acceso propio reemplaza al de uvicorn (que pone la URL con su consulta) y los registros de error
    de uvicorn y de la web pierden la traza."""
    uv = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, FiltroPrivado) for f in uv.filters):
        uv.addFilter(FiltroPrivado(descartar=True))
    for nombre in ("uvicorn", "uvicorn.error", "pap.web"):
        lg = logging.getLogger(nombre)
        if not any(isinstance(f, FiltroPrivado) for f in lg.filters):
            lg.addFilter(FiltroPrivado())
    if not any(isinstance(h, _Stderr) for h in log.handlers):
        h = _Stderr()
        h.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
        log.addHandler(h)
    if log.level == logging.NOTSET:
        log.setLevel(logging.INFO)


class Guardia:
    """Middleware ASGI puro (no toca el cuerpo salvo para medirlo)."""

    def __init__(self, app, limites: L.Limites, tx: dict, cabeceras: dict):
        self.app, self.limites, self.tx, self.cabeceras = app, limites, tx, cabeceras

    def _respuesta(self, scope, estado: int, motivo: str) -> Response:
        texto = self.tx["errores"][motivo]
        if scope["path"].startswith("/api/"):
            cuerpo = json.dumps({"tipo": "error", "motivo": motivo, "texto": texto}, ensure_ascii=False)
            return Response(cuerpo, status_code=estado, media_type="application/json", headers=self.cabeceras)
        return Response(texto, status_code=estado, media_type="text/plain", headers=self.cabeceras)

    async def _acotar(self, scope, receive):
        """(función `receive` que repite el cuerpo, None) o (None, True) si el cuerpo pasa del máximo."""
        maximo = self.limites.cuerpo_max
        largo = dict(scope["headers"]).get(b"content-length", b"")
        if largo.isdigit() and int(largo) > maximo:
            return None, True
        mensajes, total = [], 0
        while True:
            m = await receive()
            mensajes.append(m)
            total += len(m.get("body") or b"")
            if total > maximo:
                return None, True
            if m["type"] != "http.request" or not m.get("more_body"):
                break

        async def repetir():
            return mensajes.pop(0) if mensajes else await receive()
        return repetir, False

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        t0, estado = time.monotonic(), [None]

        async def enviar(m):
            if m["type"] == "http.response.start":
                estado[0] = m["status"]
            await send(m)

        token = L.IP_ACTUAL.set((scope.get("client") or ("desconocida", 0))[0])
        try:
            repetir, grande = await self._acotar(scope, receive)
            if grande:
                await self._respuesta(scope, 413, "cuerpo_muy_grande")(scope, receive, enviar)
            else:
                await self.app(scope, repetir, enviar)
        except Exception as e:  # noqa: BLE001 — el mensaje y la traza pueden traer lo que escribió la persona: solo el tipo
            log.error("error no capturado: %s", type(e).__name__)
            if estado[0] is None:
                await self._respuesta(scope, 500, "error_interno")(scope, receive, enviar)
        finally:
            L.IP_ACTUAL.reset(token)
            acceso.info("%s %s %s %.0f ms", scope["method"], scope["path"], estado[0], (time.monotonic() - t0) * 1000)
