"""S3-04 — Páginas HTML sobre la misma función que atiende `/api/preguntar`. Sin lógica de respuesta: cada bloque sale de un campo
de `respuesta.json` o de un YAML de textos (curados/web/textos.yaml; rótulos en curados/motor/textos/capas.yaml). Sin cookies, sin
orígenes externos y con un solo JavaScript propio. No importa nada de `pap`: recibe `resolver` desde app.py."""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.concurrency import run_in_threadpool

AQUI = Path(__file__).parent
CABECERAS_FIJAS = {"Referrer-Policy": "no-referrer", "X-Content-Type-Options": "nosniff"}
MAX_DIGITOS_ELEGIR = 3                      # `elegir` lleva números chicos (parametros.yaml → pregunta.elegir_max_valor)


def montar(app: FastAPI, raiz, tx: dict, par: dict, resolver, rotulo_version) -> None:
    raiz = Path(raiz)
    rot = yaml.safe_load((raiz / "curados/motor/textos/capas.yaml").read_text(encoding="utf-8"))["rotulos"]
    pg = par["paginas"]
    cabeceras = {**CABECERAS_FIJAS, "Content-Security-Policy": pg["csp"]["valor"]}
    entorno = Environment(loader=FileSystemLoader(AQUI / "plantillas"), autoescape=select_autoescape(["html"]),
                          trim_blocks=True, lstrip_blocks=True)
    entorno.filters["como_json"] = lambda x: json.dumps(x, ensure_ascii=False)          # la consulta viaja en un campo oculto

    def pagina(plantilla: str, estado: int = 200, **ctx) -> Response:
        html = entorno.get_template(plantilla).render(tx=tx, p=tx["paginas"], rot=rot, par=par,
                                                      maxlen=par["pregunta"]["texto_max_caracteres"]["valor"], **ctx)
        return HTMLResponse(html, status_code=estado, headers=cabeceras)

    def aviso(bloque: str, texto: str, estado: int, guiado: bool = False, caja: bool = True) -> Response:
        return pagina("aviso.html", estado, bloque=bloque, texto=texto, guiado=guiado, caja=caja)

    def numeros(previo: str, n: str | None) -> list | None:
        """`elegir` acumulado: lo que ya había más el botón pulsado. None si algo no es un número chico."""
        trozos = [t.strip() for t in previo.split(",")] if previo.strip() else []
        if n is not None:
            trozos.append(n.strip())
        if not all(t.isascii() and t.isdigit() and len(t) <= MAX_DIGITOS_ELEGIR for t in trozos):
            return None
        return [int(t) for t in trozos]

    def atender(datos: dict) -> Response:
        texto, consulta, previo, n = datos.get("texto"), datos.get("consulta"), datos.get("elegir", ""), datos.get("n")
        invalido = [v for v in (texto, consulta, previo, n) if v is not None and not isinstance(v, str)]
        lista = None if invalido else numeros(previo, n)
        if invalido or lista is None:
            return aviso("error", tx["errores"]["solicitud_invalida"], 422)
        if texto is not None and consulta is None and not texto.strip():
            return aviso("error", tx["paginas"]["texto_vacio"], 422)
        cuerpo: dict = {}
        if texto is not None:
            cuerpo["texto"] = texto
        if consulta is not None:
            try:
                cuerpo["consulta"] = json.loads(consulta)
            except ValueError:
                cuerpo["consulta"] = None                    # `resolver` lo rechaza como solicitud inválida
        if lista:
            cuerpo["elegir"] = lista
        estado, res = resolver(cuerpo)
        tipo = res.get("tipo")
        if tipo in ("respuesta", "no_se_puede"):
            return pagina("respuesta.html", estado, res=res, rotulo_version=rotulo_version())
        if tipo == "aclaracion":
            return pagina("aclaracion.html", estado, a=res["aclaracion"], texto=texto, consulta=consulta,
                          elegir=",".join(map(str, lista)))
        if tipo == "mensaje":
            motivo = res.get("motivo")
            return aviso("mensaje", tx["mensajes"].get(motivo) or tx["mensajes"]["otro"], estado,
                         guiado=motivo in pg["mensajes_con_enlace_guiado"]["valor"])
        if tipo == "error":
            return aviso("error", res["texto"], estado)
        return aviso("error", tx["errores"]["error_interno"], 500)

    @app.get("/")
    def inicio() -> Response:
        return pagina("inicio.html")

    @app.post("/preguntar")
    async def preguntar_html(request: Request) -> Response:
        try:
            form = await request.form()
            datos = {k: v for k, v in form.items()}
        except Exception:  # noqa: BLE001 — cuerpo que no es un formulario
            return aviso("error", tx["errores"]["solicitud_invalida"], 422)
        return await run_in_threadpool(atender, datos)

    estaticos = {f.name for f in (AQUI / "estatico").iterdir() if f.is_file()}

    @app.get("/estatico/{nombre}")
    def estatico(nombre: str) -> Response:
        if nombre not in estaticos:                           # lista cerrada: nada de rutas armadas con lo que manda la persona
            return Response(status_code=404)
        return FileResponse(AQUI / "estatico" / nombre, headers=cabeceras)
