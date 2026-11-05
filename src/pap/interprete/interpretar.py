"""S2-05 — De la pregunta en texto libre a la respuesta del motor del slice 1. El LLM propone; el código decide.

Orden (backlog/slice-2/S2-05-interpretar.md):
1. limpiar (S2-04);
2. caché por huella (`interprete.cache_horas`); con `elegir` y sin caché vigente es un error de uso: nunca se reinterpreta;
3. LLM y validación con el esquema de S2-01, con `interprete.reintentos_si_no_valida` reintentos que llevan el error;
4. anclas: cada valor necesita un fragmento literal de la pregunta que lo justifique; el que no lo tiene se descarta;
5. lo que falta: default o aclaración armada por el código (opciones de curados/motor/textos/interprete.yaml);
6. lugares con paréntesis («Ayaviri (Melgar, Puno)») a la forma con comas, antes del resolver;
7. despacho: `preguntar_minima` sin cambios, aclaración, «no se puede» o mensaje fijo.

No hay textos visibles aquí: salen de interprete.yaml, no_se_puede.yaml, errores_consulta.yaml y cli.yaml; los defaults, de
parametros_motor.yaml → interprete."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
import time
import unicodedata
from pathlib import Path

import yaml

from ..motor import plantillas
from ..motor import preguntar as P
from ..motor.interpretacion import InterpretacionInvalida, validar
from ..motor.preguntar import EleccionInvalida
from ..motor.territorio import Aclaracion, resolver
from . import llm as L
from .limpiar import limpiar
from .prompt import armar

DEFECTO = object()
_CACHE_PYTEST: Path | None = None
LUGARES = ("territorio", "comparar_con", "dentro_de")


# ======================================================================= datos

def _yaml(raiz, ruta: str) -> dict:
    return yaml.safe_load((Path(raiz) / ruta).read_text(encoding="utf-8"))


def _par(raiz) -> dict:
    return _yaml(raiz, "curados/motor/parametros_motor.yaml")


def _tx(raiz) -> dict:
    return _yaml(raiz, "curados/motor/textos/interprete.yaml")


# ======================================================================= normalización y anclas (paso 4)

def normalizar(s) -> str:
    """Minúsculas, sin tildes, signos → espacio, espacios colapsados."""
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


class Anclas:
    """Las comprobaciones del paso 4 sobre una pregunta ya limpia."""

    def __init__(self, raiz, pregunta: str):
        par = _par(raiz)
        a = par["interprete"]["anclas"]
        self.contr = {normalizar(k): normalizar(v).split() for k, v in a["contracciones"]["valor"].items()}
        self.plurales = list(a["plurales_nivel"]["valor"])
        t = par["territorio"]
        self.nacional = [self.palabras(x) for x in t["textos_nacional"]["valor"]]
        self.niveles = {n: {normalizar(w) for w in ws} for n, ws in t["palabras_que_fijan_nivel"]["valor"].items()}
        self.pregunta = self.palabras(pregunta)

    def palabras(self, s) -> list[str]:
        return [w for x in normalizar(s).split() for w in self.contr.get(x, [x])]

    @staticmethod
    def _seguidas(hay: list, aguja: list) -> bool:
        n = len(aguja)
        return n > 0 and any(hay[i:i + n] == aguja for i in range(len(hay) - n + 1))

    def en_pregunta(self, ancla) -> bool:
        return isinstance(ancla, str) and self._seguidas(self.pregunta, self.palabras(ancla))

    def lugar(self, lugar: dict, ancla) -> bool:
        if not self.en_pregunta(ancla):
            return False
        if lugar.get("nacional") is True:
            return any(self._seguidas(self.palabras(ancla), x) for x in self.nacional)
        return normalizar(lugar.get("texto")) == normalizar(ancla)

    def nivel(self, nivel: str, ancla) -> bool:
        ws = self.niveles.get(nivel, set())
        return self.en_pregunta(ancla) and any(w in ws or any(w == p + s for p in ws for s in self.plurales)
                                                for w in normalizar(ancla).split())

    def anio(self, valor, ancla) -> bool:
        return self.en_pregunta(ancla) and str(valor) in re.findall(r"(?<!\d)\d{4}(?!\d)", normalizar(ancla))


def anclar(consulta: dict, anclas: dict, chk: Anclas) -> tuple[dict, list[str]]:
    """La consulta sin los valores que no tienen un ancla válida, y la lista de lo descartado (paso 4)."""
    c, fuera = copy.deepcopy(consulta), []
    for k in ("intencion", "tema"):
        if k in c and not chk.en_pregunta(anclas.get(k)):
            c.pop(k)
            fuera.append(k)
    t = c.get("territorio")
    if isinstance(t, dict) and "nivel" in t:
        if "dentro_de" in t and not chk.lugar(t["dentro_de"], anclas.get("dentro_de")):
            t.pop("dentro_de")
            fuera.append("dentro_de")
        if not chk.nivel(t["nivel"], anclas.get("nivel")):
            c.pop("territorio")
            fuera.append("nivel")
    elif isinstance(t, dict) and not chk.lugar(t, anclas.get("territorio")):
        c.pop("territorio")
        fuera.append("territorio")
    if "comparar_con" in c and not chk.lugar(c["comparar_con"], anclas.get("comparar_con")):
        c.pop("comparar_con")
        fuera.append("comparar_con")
    p = c.get("periodo")
    for k in ("anio", "desde", "hasta"):
        if isinstance(p, dict) and k in p and not chk.anio(p[k], anclas.get(k)):
            p.pop(k)
            fuera.append(k)
    return c, fuera


# ======================================================================= paréntesis (paso 6)

def forma_con_comas(texto: str) -> str:
    """«Ayaviri (Melgar, Puno)» → «Ayaviri, Melgar, Puno». Sin paréntesis, el texto no cambia."""
    if "(" not in texto:
        return texto
    t = re.sub(r"\s*\(\s*([^()]*?)\s*\)", r", \1", texto)
    t = re.sub(r"\s*,[\s,]*", ", ", t)
    return " ".join(t.split()).strip(" ,")


def _con_comas(c: dict) -> dict:
    c = copy.deepcopy(c)
    for lugar in (c.get("territorio"), c.get("comparar_con"), (c.get("territorio") or {}).get("dentro_de")):
        if isinstance(lugar, dict) and isinstance(lugar.get("texto"), str):
            lugar["texto"] = forma_con_comas(lugar["texto"])
    return c


# ======================================================================= «Entendimos» (punto 3)

def _piezas(c: dict) -> list[tuple[str, dict | None]]:
    """Los lugares de la consulta en el orden en que el motor pide aclararlos (preguntar._resolver)."""
    t = c.get("territorio") or {}
    if c.get("intencion") == "identificar_extremo":
        return [("dentro_de", t.get("dentro_de"))]
    return [("territorio", c.get("territorio")), ("comparar_con", c.get("comparar_con"))]


def _nombre_lugar(motor, lugar: dict, numeros: list[int], tx: dict) -> str:
    r = resolver(lugar, motor.ctx)
    if isinstance(r, Aclaracion):
        if numeros and 1 <= numeros[0] <= len(r.opciones):
            r = r.opciones[numeros.pop(0) - 1]["territorio"]
        else:
            return tx["lugar_literal"].format(texto=lugar.get("texto", ""))
    nombre = r.nombre_completo if r.nivel in ("provincia", "distrito") else r.nombre_mostrado
    return tx["lugar_resuelto"].get(r.nivel, tx["lugar_resuelto"]["defecto"]).format(nombre=nombre)


def frase(motor, c: dict, numeros=()) -> str:
    """La frase de «Entendimos» armada desde la consulta. `numeros`: los de --elegir que el motor usa para los lugares."""
    tx = _tx(motor.ctx.raiz)["entendimos"]
    nsp = P._tx(motor)
    nums = [int(n) for n in numeros]
    tema = c.get("tema")
    v = {"tema": nsp["temas"].get(tema, tx["tema_sin_elegir"]), "tema_art": nsp["temas_art"].get(tema, tx["tema_sin_elegir"]),
         "en_lugar": "", "con_lugar": "", "dentro_de": "", "periodo": "", "nivel": ""}
    for clave, lugar in _piezas(c):
        nombre = _nombre_lugar(motor, lugar, nums, tx) if lugar else None
        if clave == "territorio" and nombre:
            v["en_lugar"] = tx["en_lugar"].format(lugar=nombre)
        elif clave == "comparar_con" and nombre:
            v["con_lugar"] = tx["con_lugar"].format(lugar=nombre)
        elif clave == "dentro_de":
            v["dentro_de"] = tx["dentro_de"].format(lugar=nombre or tx["lugar_resuelto"]["nacional"])
    if c.get("intencion") == "identificar_extremo":
        v["nivel"] = tx["niveles"].get((c.get("territorio") or {}).get("nivel"), "")
    p = c.get("periodo") or {}
    tp = tx["periodo"]
    if "anio" in p:
        v["periodo"] = tp["anio"].format(anio=p["anio"])
    elif "desde" in p and "hasta" in p:
        v["periodo"] = tp["desde_hasta"].format(desde=p["desde"], hasta=p["hasta"])
    elif "desde" in p:
        v["periodo"] = tp["desde"].format(desde=p["desde"])
    elif "hasta" in p:
        v["periodo"] = tp["hasta"].format(hasta=p["hasta"])
    pl = tx["intenciones"].get(c.get("intencion"), tx["intenciones"]["nivel_actual"])
    if isinstance(pl, dict):
        pl = pl.get(tema, pl["defecto"])
    return " ".join(pl.format_map(v).split())


def entendimos(motor, c: dict, numeros=()) -> str:
    return _tx(motor.ctx.raiz)["entendimos"]["prefijo"].format(frase=frase(motor, c, numeros))


def _etiqueta(motor, c: dict) -> str:
    f = _tx(motor.ctx.raiz)["entendimos"]["opcion"].format(frase=frase(motor, c))
    return f[:1].upper() + f[1:]


# ======================================================================= caché (paso 2)

def _carpeta_cache(raiz, cache_dir) -> Path:
    global _CACHE_PYTEST
    if cache_dir is not None:
        return Path(cache_dir)
    if os.environ.get("PYTEST_CURRENT_TEST"):              # en pytest la caché nunca tapa una grabación que falta
        if _CACHE_PYTEST is None:
            _CACHE_PYTEST = Path(tempfile.mkdtemp(prefix="pap-interprete-cache-"))
        return _CACHE_PYTEST
    return Path(raiz) / _par(raiz)["interprete"]["cache_carpeta"]["valor"]


def _huella(limpia: str, modelo: str, version_prompt: str) -> str:
    return hashlib.sha256(json.dumps([limpia, modelo, version_prompt], ensure_ascii=False).encode("utf-8")).hexdigest()


def _leer_cache(ruta: Path, horas: float) -> dict | None:
    try:
        g = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return g if time.time() - float(g.get("creada", 0)) <= horas * 3600 else None


# ======================================================================= respuestas que no calculan cifras

def _mensaje(motor, motivo: str) -> dict:
    raiz = motor.ctx.raiz
    tx = _tx(raiz)
    via = tx["via_estructurada"]
    texto = {"no_es_pregunta": f"{tx['no_es_pregunta']} {via}",
             "otro_idioma": f"{_yaml(raiz, 'curados/motor/textos/errores_consulta.yaml')['mensajes']['idioma_invalido']} {via}",
             "no_entendida": f"{tx['no_entendida']} {via}",
             "no_disponible": tx["no_disponible"],
             "volver_a_preguntar": tx["volver_a_preguntar"]}[motivo]
    return {"tipo": "mensaje", "motivo": motivo, "texto": texto, "cifras": {}}


def _dato(limpia: str) -> dict:
    return {"pregunta_original": limpia, "idioma": "es"}


def _no_se_puede(motor, limpia: str, motivo: str, **detalle) -> dict:
    d = _dato(limpia)
    m = {"motivo": motivo, **detalle}
    plan = P._plan_aparte(None, d, id=f"no_se_puede__{motivo}", no_se_puede=m, motivos_no_se_puede=[dict(m)])
    return {**motor.responder(plan), "consulta_minima": d, "plan": plan}


def _aclaracion(motor, limpia: str, motivo: str, pregunta: str, opciones: list[dict]) -> dict:
    a = {"motivo": f"interprete_{motivo}", "pregunta": pregunta,
         "opciones": [{"n": i, **o} for i, o in enumerate(opciones, 1)], "por_defecto": None}
    plan = P._plan_aparte(None, _dato(limpia), id=f"aclaracion__{a['motivo']}", aclaracion=a)
    return {**motor.responder(plan), "consulta_minima": None, "plan": plan}


def _de_mas(raiz, escritos: int, hay: int) -> EleccionInvalida:
    msgs = plantillas.textos(raiz, "cli.yaml")["mensajes"]
    clave = "elegir_de_mas_ninguna" if hay == 0 else "elegir_de_mas_una" if hay == 1 else "elegir_de_mas"
    return EleccionInvalida(msgs[clave].format(escritos=escritos, hay=hay))


# ======================================================================= lo que falta (paso 5)

def _pendiente(motor, c: dict, fuera: list[str]) -> dict | str | None:
    """La siguiente aclaración armada por el código ({clave, motivo, pregunta, opciones}), «no_entendida» o None. Aplica los
    defaults que no preguntan (sin intención → interprete.sin_intencion)."""
    raiz = motor.ctx.raiz
    par = _par(raiz)["interprete"]
    tx = _tx(raiz)["aclaraciones"]
    if "intencion" not in c:
        if par["sin_intencion"]["valor"] != "aclarar":
            c["intencion"] = par["sin_intencion"]["valor"]
        else:
            ops = [{"etiqueta": _etiqueta(motor, {**c, "intencion": i}), "intencion": i}
                   for i in par["sin_intencion_opciones"]["valor"]]
            return {"clave": "intencion", "motivo": "sin_intencion", "pregunta": tx["sin_intencion"],
                    "opciones": sorted(ops, key=lambda o: normalizar(o["etiqueta"]))}
    t = c.get("territorio")
    extremo = c["intencion"] == "identificar_extremo"
    if isinstance(t, dict) and ("nivel" in t) != extremo:          # la forma del lugar no es la de la intención
        c.pop("territorio")
        t = None
        if not extremo:
            fuera.append("territorio")
    if c["intencion"] != "comparacion" and "comparar_con" in c:
        c.pop("comparar_con")
        fuera.append("comparar_con")
    if extremo and t is None:
        return par["extremo_sin_nivel"]["valor"]
    lugar = [{"etiqueta": tx["opciones_sin_lugar"][k], "opcion": k} for k in par["sin_lugar"]["opciones"]]
    if not extremo and t is None:
        if par["sin_lugar"]["valor"] == "nacional":
            c["territorio"] = {"nacional": True}
        else:
            return {"clave": "territorio", "motivo": "sin_lugar", "pregunta": tx["sin_lugar"]["territorio"], "opciones": lugar}
    if c["intencion"] == "comparacion" and "comparar_con" in fuera and "comparar_con" not in c:
        return {"clave": "comparar_con", "motivo": "sin_lugar", "pregunta": tx["sin_lugar"]["comparar_con"], "opciones": lugar}
    if extremo and "dentro_de" in fuera and "dentro_de" not in c["territorio"]:
        return {"clave": "dentro_de", "motivo": "sin_lugar", "pregunta": tx["sin_lugar"]["dentro_de"], "opciones": lugar}
    if any(k in fuera for k in ("anio", "desde", "hasta")):
        ops = [{"etiqueta": tx["opciones_anio"][k], "opcion": k} for k in par["anios_relativos"]["opciones"]]
        return {"clave": "periodo", "motivo": "anio_relativo", "pregunta": tx["anio_relativo"], "opciones": ops}
    return None


def _aplicar(c: dict, fuera: list[str], pend: dict, op: dict) -> bool:
    """Aplica la opción elegida de una aclaración del código. False si la opción es «Escribe…» (no es una consulta)."""
    if op.get("opcion") == "escribir":
        return False
    k = pend["clave"]
    if k == "intencion":
        c["intencion"] = op["intencion"]
    elif k == "territorio":
        c["territorio"] = {"nacional": True}
    elif k == "comparar_con":
        c["comparar_con"] = {"nacional": True}
    elif k == "dentro_de":
        c["territorio"]["dentro_de"] = {"nacional": True}
    elif k == "periodo":
        p = c.get("periodo") or {}
        c["periodo"] = {"tipo": "serie", **{x: p[x] for x in ("desde", "hasta") if x in p}} if p.get("tipo") == "serie" \
            else {"tipo": "ultimo"}
        fuera[:] = [x for x in fuera if x not in ("anio", "desde", "hasta")] + ["anio_aclarado"]
    return True


# ======================================================================= LLM y validación (paso 3)

def _llamar(raiz, limpia: str, llm, registro) -> tuple[dict | None, dict, str | None]:
    """(interpretación válida o None, metadatos, motivo de falla: no_disponible | no_entendida | None)."""
    prompt, version = armar(raiz)
    reintentos = int(_par(raiz)["interprete"]["reintentos_si_no_valida"]["valor"])
    meta = {"modelo": None, "version_prompt": version, "reintentos": 0, "cache": False}
    error = None
    for i in range(1 + reintentos):
        try:
            r = llm.interpretar_crudo(prompt, limpia, version, error_previo=error) if error else \
                llm.interpretar_crudo(prompt, limpia, version)
        except L.NoDisponible:
            _uso(raiz, limpia, None, "no_disponible", None, registro)
            return None, meta, "no_disponible"
        meta.update(modelo=r.modelo, reintentos=i)
        try:
            dato = validar(r.json, raiz)
        except InterpretacionInvalida as e:
            _uso(raiz, limpia, None, "invalida", r, registro)
            error = f"{', '.join(e.codigos)}: {' '.join(e.mensajes)}"
            continue
        _uso(raiz, limpia, dato.get("consulta"), dato["resultado"], r, registro)
        return dato, meta, None
    return None, meta, "no_entendida"


def _uso(raiz, limpia, consulta, resultado, r, registro) -> None:
    if registro is not None:
        L.registrar_uso(raiz, limpia, consulta, resultado, r, ruta=registro)


# ======================================================================= interpretar

def interpretar(texto: str, motor, *, elegir=None, llm=None, cache_dir=None, registro=DEFECTO) -> dict:
    """Responde una pregunta en texto libre. Devuelve la respuesta del motor (`tipo`: respuesta | no_se_puede | aclaracion)
    o un mensaje fijo (`tipo`: mensaje), con `interpretacion` y `entendimos`. `elegir`: un número o varios (las aclaraciones
    del intérprete primero, luego las del territorio). `llm`: un objeto con `interpretar_crudo` (por defecto el cliente en
    vivo). `registro`: ruta del registro de uso (P-03), None para no registrar; por defecto salidas/interprete/uso.jsonl,
    salvo en pytest. Lanza EleccionInvalida (error de uso, mensaje para la persona)."""
    raiz = Path(motor.ctx.raiz)
    par = _par(raiz)["interprete"]
    if registro is DEFECTO:
        registro = None if os.environ.get("PYTEST_CURRENT_TEST") else raiz / "salidas/interprete/uso.jsonl"
    limpia = limpiar(texto, raiz)
    numeros = P._numeros(elegir)
    escritos = len(numeros)
    _, version = armar(raiz)
    ruta = _carpeta_cache(raiz, cache_dir) / f"{_huella(limpia.texto, par['modelo']['valor'], version)}.json"
    g = _leer_cache(ruta, float(par["cache_horas"]["valor"]))
    if g is not None:
        dato, meta, falla = g["interpretacion"], {**g["meta"], "cache": True}, None
    elif numeros:
        raise EleccionInvalida(_tx(raiz)["elegir_vencida"])          # nunca se reinterpreta para elegir
    else:
        dato, meta, falla = _llamar(raiz, limpia.texto, llm if llm is not None else L.Cliente(raiz, modo="vivo"), registro)
        if dato is not None:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(json.dumps({"creada": time.time(), "interpretacion": dato, "meta": meta}, ensure_ascii=False),
                            encoding="utf-8")
    info = {"resultado": dato["resultado"] if dato else falla, **meta, "consulta": None, "anclas": None, "descartados": [],
            "avisos": list(limpia.avisos), "datos_personales_quitados": limpia.reemplazos}
    usados = 0

    def fin(res: dict, ent: str | None = None) -> dict:
        if numeros:                                                     # números que nadie usó: no se descartan en silencio
            raise _de_mas(raiz, escritos, usados)
        return {**res, "interpretacion": info, "entendimos": ent}

    if dato is None:
        return fin(_mensaje(motor, falla))
    res = dato["resultado"]
    if res in ("no_es_pregunta", "otro_idioma"):
        return fin(_mensaje(motor, res))
    chk = Anclas(raiz, limpia.texto)
    if res == "fuera_de_alcance":
        ok = chk.en_pregunta(dato["pedido"])
        info["descartados"] = [] if ok else ["pedido"]
        pedido = dato["pedido"] if ok else None
        if dato["tipo"] == "tema":
            return fin(_no_se_puede(motor, limpia.texto, "tema_fuera_del_piloto", tema_pedido=pedido))
        return fin(_no_se_puede(motor, limpia.texto, "interprete_fuera_de_alcance", pedido=pedido))

    if res == "aclaracion":
        vistas, opciones = set(), []
        for o in dato["opciones"]:
            c, fuera = anclar(o["consulta"], o["anclas"], chk)
            if "intencion" not in c and par["sin_intencion"]["valor"] != "aclarar":     # el default, antes de comparar opciones
                c["intencion"] = par["sin_intencion"]["valor"]
            clave = json.dumps(c, sort_keys=True, ensure_ascii=False)
            if clave not in vistas:
                vistas.add(clave)
                opciones.append({"consulta": c, "anclas": o["anclas"], "descartados": fuera})
        for o in opciones:
            o["etiqueta"] = _etiqueta(motor, o["consulta"])
        opciones.sort(key=lambda o: normalizar(o["etiqueta"]))           # orden neutro: alfabético (agents.md §6.2)
        if len(opciones) > 1:
            if not numeros:
                info["descartados"] = sorted({d for o in opciones for d in o["descartados"]})
                return fin(_aclaracion(motor, limpia.texto, dato["motivo"], _tx(raiz)["aclaraciones"][dato["motivo"]],
                                       [{"etiqueta": o["etiqueta"], "consulta": o["consulta"]} for o in opciones]))
            elegida = P._elegir(motor, {"opciones": opciones}, numeros.pop(0))
            usados += 1
        else:
            elegida = opciones[0]
        c, fuera, anclas = elegida["consulta"], list(elegida["descartados"]), elegida["anclas"]
    else:
        c, fuera = anclar(dato["consulta"], dato["anclas"], chk)
        anclas = dato["anclas"]

    while True:                                                         # paso 5: cada aclaración del código usa un número
        pend = _pendiente(motor, c, fuera)
        info.update(consulta=copy.deepcopy(c), descartados=list(fuera),
                    anclas={k: v for k, v in (anclas or {}).items() if k not in fuera})    # solo las anclas de lo aceptado
        if pend is None:
            break
        if isinstance(pend, str):
            return fin(_mensaje(motor, pend))
        if not numeros:
            return fin(_aclaracion(motor, limpia.texto, pend["motivo"], pend["pregunta"], pend["opciones"]),
                       entendimos(motor, info["consulta"]))
        op = P._elegir(motor, {"opciones": pend["opciones"]}, numeros.pop(0))
        usados += 1
        if not _aplicar(c, fuera, pend, op):
            return fin(_mensaje(motor, "volver_a_preguntar"))

    consulta = {**_con_comas(info["consulta"]), **_dato(limpia.texto)}     # paso 6 y paso 7
    resto, numeros[:] = list(numeros), []
    try:
        r = P.preguntar_minima(motor, consulta, elegir=resto or None)
    except EleccionInvalida as e:
        for hay in range(len(resto)):                                   # el motor no usó todos: se dice con la cuenta total
            if str(e) == str(_de_mas(raiz, len(resto), hay)):
                raise _de_mas(raiz, escritos, usados + hay) from None
        raise
    tema = (r.get("consulta_minima") or {}).get("tema")
    if "tema" not in consulta and tema:                                 # el motor preguntó el tema y usó el primer número
        consulta, resto = {**consulta, "tema": tema}, resto[1:]
    return {**r, "interpretacion": info, "entendimos": entendimos(motor, consulta, resto)}
