"""S3-05 — Formulario guiado en dos pasos, sin LLM: arma la consulta mínima con lo que la persona elige y la manda por el mismo camino
de respuesta y de aclaración que las páginas de S3-04 (`atender`). Sin lógica de respuesta: qué campos pide cada intención sale de
curados/web/parametros.yaml (`guiado`), los textos de curados/web/textos.yaml (`guiado`) y las opciones de `GET /api/opciones`.
No importa nada de `pap`."""
from __future__ import annotations

import json
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool


def _yaml(raiz: Path, ruta: str) -> dict:
    return yaml.safe_load((raiz / ruta).read_text(encoding="utf-8")) or {}


def _texto(v) -> str | None:
    return v.strip() if isinstance(v, str) else None


def _anio(v: str, digitos: int) -> int | None:
    return int(v) if v.isascii() and v.isdigit() and len(v) == digitos else None


def armar(g: dict, pg: dict, intencion: str, tema: str, campos: dict, nombres: dict, niveles: list[str],
          extremo_nacional: bool) -> tuple[dict | None, str | None]:
    """(consulta mínima, None) o (None, clave del error de `textos.yaml → guiado.errores`). `campos`: lo que mandó el formulario;
    `nombres`: {tema, tema_art} con los nombres de `no_se_puede.yaml`."""
    regla = pg["intenciones"]["valor"][intencion]
    lugares, valores = {}, {}
    for c in regla["campos"]:
        if c in pg["lugares_con_todo_el_peru"]["valor"]:
            escrito, nacional = _texto(campos.get(c)) or "", campos.get(f"{c}_nacional") is not None
            if escrito and nacional:
                return None, "lugar_doble"
            if not escrito and not nacional:
                return None, "falta_lugar"
            if len(escrito) > pg["lugar_max_caracteres"]["valor"]:
                return None, "lugar_muy_largo"
            lugares[c] = {"nacional": True} if nacional else {"texto": escrito}
            valores[c] = g["lugar_nacional_frase"] if nacional else escrito
        elif c in ("anio", "desde", "hasta"):
            v = _texto(campos.get(c)) or ""
            if v and _anio(v, pg["anio_digitos"]["valor"]) is None:
                return None, "anio_invalido"
            valores[c] = v
        elif c == "nivel":
            v = _texto(campos.get(c))
            if v not in niveles:
                return None, "nivel_invalido"
            valores[c] = v
    if regla["periodo"] == "serie":
        periodo = {"tipo": "serie", **{k: int(valores[k]) for k in ("desde", "hasta") if valores.get(k)}}
    elif valores.get("anio"):
        periodo = {"tipo": "anio", "anio": int(valores["anio"])}
    else:
        periodo = {"tipo": "ultimo"}
    consulta: dict = {"intencion": intencion, "tema": tema, "periodo": periodo}
    if intencion == "identificar_extremo":
        consulta["territorio"] = {"nivel": valores["nivel"], **({"dentro_de": {"nacional": True}} if extremo_nacional else {})}
    else:
        consulta["territorio"] = lugares["lugar"]
        if "lugar2" in lugares:
            consulta["comparar_con"] = lugares["lugar2"]
    consulta["pregunta_original"] = g["pregunta"][intencion].format(
        tema=nombres["tema"], tema_art=nombres["tema_art"], lugar=valores.get("lugar", ""), lugar2=valores.get("lugar2", ""),
        nivel=g["niveles_frase"].get(valores.get("nivel"), ""))
    consulta["idioma"] = "es"
    return consulta, None


def montar(app: FastAPI, raiz, tx: dict, par: dict, opciones, pagina, atender) -> None:
    """`opciones`: lo que devuelve `GET /api/opciones`, como dict; `pagina` y `atender`: los de paginas.py."""
    raiz = Path(raiz)
    g, pg = tx["guiado"], par["guiado"]
    descripcion = _yaml(raiz, "curados/interprete/intenciones_descripcion.yaml").get("intenciones", {})
    nst = _yaml(raiz, "curados/motor/textos/no_se_puede.yaml")
    dentro_nacional = _yaml(raiz, "curados/motor/parametros_motor.yaml")["planificador"]["extremo_dentro_de"]["valor"] == "solo_nacional"

    def paso1(estado: int = 200, error: str | None = None) -> Response:
        op = opciones()
        intenciones = [{**i, "descripcion": descripcion.get(i["id"], "")} for i in op["intenciones"]]
        return pagina("guiado_paso1.html", estado, g=g, temas=op["temas"], intenciones=intenciones,
                      error=g["errores"][error] if error else None)

    def paso2(tema: str, intencion: str, valores: dict, estado: int = 200, error: str | None = None) -> Response:
        op = opciones()
        rot = lambda lista, k: next(x["rotulo"] for x in lista if x["id"] == k)      # noqa: E731
        pedidos = pg["intenciones"]["valor"][intencion]["campos"]
        casillas = [x for c in pedidos for x in ([c, f"{c}_nacional"] if c in pg["lugares_con_todo_el_peru"]["valor"] else [c])]
        return pagina("guiado_paso2.html", estado, g=g, tema=tema, intencion=intencion, v=valores,
                      campos=[{"nombre": c, **g["campos"][c]} for c in casillas if c != "dentro_de"],
                      niveles=[n for n in op["niveles"] if n["id"] != "nacional"], lugares=pg["lugares_con_todo_el_peru"]["valor"],
                      maxlugar=pg["lugar_max_caracteres"]["valor"], dentro_de="dentro_de" in pedidos and dentro_nacional,
                      tema_rotulo=rot(op["temas"], tema), intencion_rotulo=rot(op["intenciones"], intencion),
                      error=g["errores"][error] if error else None)

    def enviar(datos: dict) -> Response:
        op = opciones()
        tema, intencion = _texto(datos.get("tema")), _texto(datos.get("intencion"))
        if tema not in {t["id"] for t in op["temas"]} or intencion not in {i["id"] for i in op["intenciones"]}:
            return paso1(422, "falta_eleccion")
        if datos.get("paso") != "2":
            return paso2(tema, intencion, {})
        niveles = [n["id"] for n in op["niveles"] if n["id"] != "nacional"]
        nombres = {"tema": nst["temas"][tema], "tema_art": nst["temas_art"][tema]}
        consulta, error = armar(g, pg, intencion, tema, datos, nombres, niveles, dentro_nacional)
        if error:
            return paso2(tema, intencion, {k: v for k, v in datos.items() if isinstance(v, str)}, 422, error)
        return atender({"consulta": json.dumps(consulta, ensure_ascii=False)})

    @app.get("/guiado")
    def guiado_paso1() -> Response:
        return paso1()

    @app.post("/guiado")
    async def guiado_enviar(request: Request) -> Response:
        try:
            form = await request.form()
            datos = {k: v for k, v in form.items()}               # un campo repetido queda con su primer valor
        except Exception:  # noqa: BLE001 — cuerpo que no es un formulario
            return paso1(422, "falta_eleccion")
        return await run_in_threadpool(enviar, datos)
