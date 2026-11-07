"""S3-03 — Servicio FastAPI sobre el mismo motor. Un solo proceso; un candado envuelve toda llamada a `interpretar()` o
`preguntar_minima()` (el LLM queda dentro del candado: en local basta, el slice 4 lo revisa). Los textos salen de
curados/web/textos.yaml y los parámetros de curados/web/parametros.yaml; nunca se muestra un texto pensado para la terminal.
Imports de `pap` permitidos: ver backlog/slice-3/S3-03-servicio.md, punto 7."""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

import yaml
from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response

from pap.interprete.interpretar import crear_cliente, interpretar
from pap.motor.consulta import ConsultaInvalida
from pap.motor.preguntar import EleccionInvalida, preguntar_minima
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto
from pap.web import limites, paginas, registro

log = logging.getLogger("pap.web")
_DEFECTO = object()                          # `registro_uso` sin dar: `interpretar()` decide (salidas/interprete/uso.jsonl, salvo en pytest)


def _yaml(raiz: Path, ruta: str) -> dict:
    return yaml.safe_load((raiz / ruta).read_text(encoding="utf-8")) or {}


def _json(dato, estado: int = 200) -> Response:
    return Response(json.dumps(dato, ensure_ascii=False, default=str), status_code=estado, media_type="application/json")


def crear_app(raiz, *, llm=None, dir_cache=None, precalentar: bool = True, reloj=None, registro_uso=_DEFECTO) -> FastAPI:
    """`reloj`: devuelve la hora con zona (las pruebas cambian de día); `registro_uso`: ruta del registro de uso del intérprete (P-03)."""
    raiz = Path(raiz)
    par = _yaml(raiz, "curados/web/parametros.yaml")
    tx = _yaml(raiz, "curados/web/textos.yaml")
    motor = Motor(cargar_contexto(raiz))
    candado = threading.Lock()
    listo = threading.Event()
    app = FastAPI(title="Pregúntale al Perú", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.motor, app.state.listo, app.state.candado = motor, listo, candado
    app.state.llm, app.state.dir_cache = llm, dir_cache          # las pruebas cambian la caché entre comparaciones
    app.state.error_precalentamiento = None
    lim = app.state.limites = limites.Limites(par, reloj)               # S3-07: contadores en memoria (P-05)
    contado = limites.LlmContado(lim, llm, crear=lambda: crear_cliente(raiz))
    extra_uso = {} if registro_uso is _DEFECTO else {"registro": registro_uso}
    registro.instalar()
    app.add_middleware(registro.Guardia, limites=lim, tx=tx, cabeceras=paginas.cabeceras_de(par))

    def fallo(clave: str, estado: int, texto: str | None = None) -> tuple[int, dict]:
        return estado, {"tipo": "error", "motivo": clave, "texto": texto or tx["errores"][clave]}

    def error(clave: str, estado: int, texto: str | None = None) -> Response:
        return _json(fallo(clave, estado, texto)[1], estado)

    # ---- precalentamiento: en un hilo aparte; /salud y las preguntas responden 503 mientras corre
    def calentar() -> None:
        try:
            p = _yaml(raiz, "curados/web/precalentar.yaml")
            consultas = [json.loads((raiz / "curados/motor/consultas_minimas" / f"{n}.json").read_text(encoding="utf-8"))
                         for n in p.get("consultas_minimas", [])] + list(p.get("por_intencion", []))
            for c in consultas:
                with candado:
                    preguntar_minima(motor, c)
        except Exception as e:  # noqa: BLE001 — un fallo al calentar no deja el servicio caído; se registra sin la pregunta
            app.state.error_precalentamiento = type(e).__name__
            log.error("precalentamiento: %s", type(e).__name__)
        finally:
            listo.set()

    if precalentar:
        threading.Thread(target=calentar, name="pap-precalentar", daemon=True).start()
    else:
        listo.set()

    # ---- errores de forma: nunca se devuelve lo que mandó la persona
    @app.exception_handler(RequestValidationError)
    def _forma(_req: Request, _exc: RequestValidationError) -> Response:
        return error("solicitud_invalida", 422)

    @app.exception_handler(405)
    def _metodo(_req: Request, _exc) -> Response:
        return error("metodo_no_permitido", 405)

    @app.exception_handler(404)
    def _no_hay(_req: Request, _exc) -> Response:
        return error("no_encontrado", 404)

    def mensaje_fijo(motivo: str) -> tuple[int, dict]:
        tabla = par["http"]["estado_por_motivo"]
        return tabla["valor"].get(motivo) or tabla["por_defecto"], {"tipo": "mensaje", "motivo": motivo,
                                                                    "texto": tx["mensajes"][motivo], "cifras": {}}

    # ---- rutas
    def resolver(cuerpo: dict) -> tuple[int, dict]:
        """Lo que responde `/api/preguntar`, como (estado HTTP, JSON); las páginas HTML (S3-04) llaman a esta misma función."""
        if not listo.is_set():
            return 503, {"tipo": "mensaje", "motivo": "preparando", "texto": tx["preparando"], "cifras": {}}
        p = par["pregunta"]
        texto, consulta, elegir = cuerpo.get("texto"), cuerpo.get("consulta"), cuerpo.get("elegir")
        if (texto is None) == (consulta is None) or set(cuerpo) - {"texto", "consulta", "elegir"}:
            return fallo("solicitud_invalida", 422)
        if (texto is not None and not isinstance(texto, str)) or (consulta is not None and not isinstance(consulta, dict)):
            return fallo("solicitud_invalida", 422)
        if isinstance(texto, str) and len(texto) > p["texto_max_caracteres"]["valor"]:
            return fallo("texto_muy_largo", 422)
        lista = elegir if isinstance(elegir, list) else [] if elegir is None else [elegir]
        if (len(lista) > p["elegir_max_numeros"]["valor"]
                or not all(type(n) is int and 1 <= n <= p["elegir_max_valor"]["valor"] for n in lista)):
            return fallo("solicitud_invalida", 422)
        if not lim.ip_permitida(limites.IP_ACTUAL.get()):
            return mensaje_fijo("espera_un_momento")
        try:
            with candado:
                if texto is not None:
                    contado.base, contado.tope_visto = app.state.llm, False           # las pruebas cambian `app.state.llm`
                    res = interpretar(texto, motor, elegir=elegir, llm=contado, cache_dir=app.state.dir_cache, **extra_uso)
                    if res.get("tipo") == "mensaje" and res.get("motivo") == "no_disponible" and contado.tope_visto:
                        return mensaje_fijo("tope_diario")              # el tope diario, no una caída del proveedor
                else:
                    res = preguntar_minima(motor, consulta, elegir=elegir)
        except ConsultaInvalida as e:
            log.info("consulta inválida: %s", ",".join(e.codigos))      # el detalle va al registro, sin la pregunta (S3-07)
            propios = tx.get("codigos_consulta") or {}
            clave = next((c for c in e.codigos if c in propios), None)
            return fallo("consulta_invalida", 422, propios[clave] if clave else None)
        except EleccionInvalida:
            log.info("elección inválida")
            return fallo("eleccion_invalida", 422)
        except Exception as e:  # noqa: BLE001
            log.error("error interno: %s", type(e).__name__)
            return fallo("error_interno", 500)
        tabla = par["http"]["estado_por_motivo"]
        estado = tabla["valor"].get(res.get("motivo")) if res.get("tipo") == "mensaje" else None
        return estado or tabla["por_defecto"], res

    @app.post("/api/preguntar")
    def preguntar(cuerpo: dict = Body(...)) -> Response:
        estado, res = resolver(cuerpo)
        return _json(res, estado)

    def datos_opciones() -> dict:
        """Lo que responde `/api/opciones`; el formulario guiado (S3-05) lee lo mismo en el servidor."""
        i = _yaml(raiz, "curados/motor/intenciones.yaml")

        def rot(clave: str, ids) -> list[dict]:
            return [{"id": k, "rotulo": tx[clave].get(k, k)} for k in ids]

        return {"temas": rot("rotulos_temas", i["temas"]), "intenciones": rot("rotulos_intenciones", i["intenciones"]),
                "niveles": rot("rotulos_niveles", i["escalera_niveles"]["valor"]), "ejemplos": tx["ejemplos"]}

    @app.get("/api/opciones")
    def opciones() -> Response:
        return _json(datos_opciones())

    def version_web() -> dict:
        v = motor.version()
        man = motor.ctx.manifiestos.get("p1_indicadores", {})
        huella = (v.get("cubo") or "").removeprefix("sha256:")[:12]
        fecha = str(man.get("construido", ""))[:10]
        return {**v, "rotulo": tx["version_rotulo"].format(huella=huella, fecha=fecha)}

    @app.get("/api/version")
    def version() -> Response:
        return _json(version_web())

    @app.get("/salud")
    def salud() -> Response:
        if listo.is_set() and app.state.error_precalentamiento:      # S3-11: un precalentamiento fallido no se informa como «ok»
            return _json({"estado": "error_precalentamiento"}, 503)
        if listo.is_set():
            return _json({"estado": "ok"})
        return _json({"estado": "preparando"}, 503)

    paginas.montar(app, raiz, tx, par, resolver, lambda: version_web()["rotulo"], datos_opciones)      # S3-04 y S3-05: las páginas HTML
    return app
