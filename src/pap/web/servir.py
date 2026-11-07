"""S3-09 — `pap servir`: levanta el servicio web (crear_app + uvicorn). Por defecto escucha solo en este equipo; con
`--red-local` escucha en todas las interfaces (la red de la casa). Host y puerto salen de curados/web/parametros.yaml
(`servicio`); los mensajes, de curados/motor/textos/cli.yaml. Sin despliegue público (P-05)."""
from __future__ import annotations

from pathlib import Path

import yaml

from pap.motor.plantillas import textos
from pap.web.app import crear_app

TODAS_LAS_INTERFACES = "0.0.0.0"


def parametros_servicio(raiz) -> dict:
    par = yaml.safe_load((Path(raiz) / "curados/web/parametros.yaml").read_text(encoding="utf-8"))["servicio"]
    return {"host": par["host"]["valor"], "puerto": par["puerto"]["valor"]}


def _correr(app, host: str, puerto: int) -> None:
    import uvicorn
    uvicorn.run(app, host=host, port=puerto, log_level="warning")


def servir(raiz, puerto: int | None = None, red_local: bool = False) -> int:
    msgs = textos(raiz, "cli.yaml")["mensajes"]
    par = parametros_servicio(raiz)
    puerto = par["puerto"] if puerto is None else puerto
    host = TODAS_LAS_INTERFACES if red_local else par["host"]
    direccion = f"http://{host}:{puerto}"
    print(msgs["servir_red_local" if red_local else "servir_local"].format(direccion=direccion, puerto=puerto), flush=True)
    _correr(crear_app(raiz), host, puerto)
    return 0
