"""S2-04 — Cliente del LLM (P-07) detrás de una interfaz pequeña: `interpretar_crudo(prompt, pregunta_limpia) -> RespuestaLLM`.

- HTTP con httpx (ya en uv.lock), salida estructurada (`output_config.format`) y temperatura de `interprete.temperatura`; la
  pregunta va como dato delimitado en el mensaje del usuario, fuera de las instrucciones (que van en `system`).
- La API de salida estructurada no acepta `oneOf`, `if/then`, `$ref` externos ni límites de longitud o número
  (https://platform.claude.com/docs/en/build-with-claude/structured-outputs): se le manda una versión simplificada del
  esquema (`esquema_para_api`). La validación completa la hace el código con el esquema de S2-01.
- La clave se lee de la variable `interprete.variable_clave`; nunca se escribe en archivos, registros ni errores.
- Grabaciones (tests/interprete/grabaciones/): una por (pregunta limpia, modelo, version_prompt) y, en el reintento de S2-05,
  también por el error que se le devuelve al LLM (`error_previo`). En pytest solo se reproducen; se graban con
  `tests/interprete/evaluar.py --grabar`.
- Uso: `salidas/interprete/uso.jsonl` (fuera de git) con los campos de P-03; `interprete.tope_por_corrida` corta una corrida."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import httpx
import yaml

DELIM_INICIO, DELIM_FIN = "<pregunta>", "</pregunta>"


class NoDisponible(Exception):
    """El LLM no está disponible (sin clave, tiempo agotado, límite agotado, caída o tope de la corrida). `motivo` es un
    código corto; el mensaje nunca trae la clave."""

    def __init__(self, motivo: str):
        self.motivo = motivo
        super().__init__(motivo)


class FaltaGrabacion(AssertionError):
    pass


@dataclass
class RespuestaLLM:
    json: dict | None
    texto: str
    modelo: str
    tokens_entrada: int = 0
    tokens_salida: int = 0
    latencia_s: float = 0.0
    costo_usd: float = 0.0
    version_prompt: str = ""
    grabacion: str | None = None
    extra: dict = field(default_factory=dict)


def parametros(raiz) -> dict:
    return yaml.safe_load((Path(raiz) / "curados/motor/parametros_motor.yaml").read_text(encoding="utf-8"))["interprete"]


# ---------------------------------------------------------------------------------------------- esquema para la API

_QUITAR = {"minLength", "maxLength", "minimum", "maximum", "x-error", "$id", "$schema", "default"}


def esquema_para_api(esquema: dict, externos: dict) -> dict:
    """Versión del esquema que acepta la salida estructurada: `$ref` resueltos en línea, `oneOf` → `anyOf`, sin `if/then`,
    `allOf` de comprobaciones, límites de longitud y número ni `minItems` > 1, y `additionalProperties: false` en todo objeto."""
    raiz = esquema

    def resolver(ref: str):
        doc, _, frag = ref.partition("#")
        nodo = externos[doc] if doc else raiz
        for k in [x for x in frag.split("/") if x]:
            nodo = nodo[k]
        return nodo, (externos[doc] if doc else None)

    def conv(n, base=None):
        if isinstance(n, list):
            return [conv(x, base) for x in n]
        if not isinstance(n, dict):
            return n
        if "$ref" in n:
            destino, doc = resolver(n["$ref"]) if not n["$ref"].startswith("#") or base is None else _local(base, n["$ref"])
            fuera = {k: v for k, v in n.items() if k != "$ref"}
            return conv({**copy.deepcopy(destino), **fuera}, doc if doc is not None else base)
        out = {}
        for k, v in n.items():
            if k in _QUITAR or k in ("if", "then", "else", "allOf", "not", "description", "$defs", "title"):
                continue
            if k == "minItems":
                v = min(int(v), 1)
            out["anyOf" if k == "oneOf" else k] = conv(v, base)
        if out.get("type") == "object" or "properties" in out:
            out["additionalProperties"] = False
        return out

    def _local(base, ref):
        nodo = base
        for k in [x for x in ref.partition("#")[2].split("/") if x]:
            nodo = nodo[k]
        return nodo, base

    return conv(esquema)


# ---------------------------------------------------------------------------------------------- grabaciones

def huella_grabacion(pregunta_limpia: str, modelo: str, version_prompt: str, error_previo: str | None = None) -> str:
    clave = [pregunta_limpia, modelo, version_prompt] + ([error_previo] if error_previo else [])
    return hashlib.sha256(json.dumps(clave, ensure_ascii=False).encode("utf-8")).hexdigest()[:24]


def ruta_grabacion(raiz, pregunta_limpia: str, modelo: str, version_prompt: str, error_previo: str | None = None) -> Path:
    return Path(raiz) / "tests/interprete/grabaciones" / f"{huella_grabacion(pregunta_limpia, modelo, version_prompt, error_previo)}.json"


def _de_cuerpo(cuerpo: dict, modelo: str, version_prompt: str, latencia: float, par: dict) -> RespuestaLLM:
    texto = "".join(b.get("text", "") for b in cuerpo.get("content") or [] if b.get("type") == "text")
    try:
        dato = json.loads(texto)
    except (ValueError, TypeError):
        dato = None
    u = cuerpo.get("usage") or {}
    te, ts = int(u.get("input_tokens") or 0), int(u.get("output_tokens") or 0)
    pr = par["precios_usd_por_millon"]
    costo = round(te * float(pr["entrada"]) / 1e6 + ts * float(pr["salida"]) / 1e6, 6)
    return RespuestaLLM(dato, texto, cuerpo.get("model") or modelo, te, ts, round(latencia, 3), costo, version_prompt)


# ---------------------------------------------------------------------------------------------- cliente

class Cliente:
    """modo: «reproducir» (pytest: solo grabaciones), «grabar» (llama a la API y guarda) o «vivo» (llama sin guardar).
    `transporte`: un httpx.BaseTransport para las pruebas (sin red)."""

    def __init__(self, raiz, modo: str = "reproducir", transporte=None, tope_usd: float | None = None):
        self.raiz, self.modo, self.transporte = Path(raiz), modo, transporte
        self.par = parametros(raiz)
        self.tope = float(self.par["tope_por_corrida"]["valor_usd"] if tope_usd is None else tope_usd)
        self.gastado = 0.0

    def _cuerpo(self, prompt: str, pregunta_limpia: str, error_previo: str | None = None) -> dict:
        from ..motor.interpretacion import RUTA_CONSULTA, RUTA_ESQUEMA
        esq = json.loads((self.raiz / RUTA_ESQUEMA).read_text(encoding="utf-8"))
        cm = json.loads((self.raiz / RUTA_CONSULTA).read_text(encoding="utf-8"))
        return {"model": self.par["modelo"]["valor"], "max_tokens": int(self.par["max_tokens"]["valor"]),
                "temperature": self.par["temperatura"]["valor"], "system": prompt,
                "messages": [{"role": "user", "content": self._turno(pregunta_limpia, error_previo)}],
                "output_config": {"format": {"type": "json_schema",
                                             "schema": esquema_para_api(esq, {"consulta_minima.schema.json": cm})}}}

    def _turno(self, pregunta_limpia: str, error_previo: str | None) -> str:
        """La pregunta como dato delimitado y, en el reintento (S2-05), el error de la respuesta anterior."""
        t = f"{DELIM_INICIO}\n{pregunta_limpia}\n{DELIM_FIN}"
        return t + "\n\n" + self.par["reintento_mensaje"]["valor"].format(error=error_previo) if error_previo else t

    def interpretar_crudo(self, prompt: str, pregunta_limpia: str, version_prompt: str,
                          error_previo: str | None = None) -> RespuestaLLM:
        modelo = self.par["modelo"]["valor"]
        ruta = ruta_grabacion(self.raiz, pregunta_limpia, modelo, version_prompt, error_previo)
        if self.modo == "reproducir":
            if not ruta.exists():
                raise FaltaGrabacion(f"falta la grabación {ruta.name} de «{pregunta_limpia}»; corre "
                                     "`uv run python tests/interprete/evaluar.py --grabar --solo <id>`")
            g = json.loads(ruta.read_text(encoding="utf-8"))
            r = _de_cuerpo(g["respuesta"], modelo, version_prompt, g.get("latencia_s", 0.0), self.par)
            r.grabacion = ruta.name
            return r
        if self.gastado >= self.tope:
            raise NoDisponible("tope_por_corrida")
        clave = os.environ.get(self.par["variable_clave"]["valor"])
        if not clave:
            raise NoDisponible("sin_clave")
        cab = {"x-api-key": clave, "anthropic-version": self.par["api"]["version"], "content-type": "application/json"}
        t0 = time.monotonic()
        try:
            with httpx.Client(transport=self.transporte, timeout=float(self.par["tiempo_max_segundos"]["valor"])) as h:
                resp = h.post(self.par["api"]["url"], headers=cab, json=self._cuerpo(prompt, pregunta_limpia, error_previo))
        except httpx.TimeoutException:
            raise NoDisponible("tiempo_agotado") from None
        except httpx.HTTPError:
            raise NoDisponible("caida") from None
        if resp.status_code == 429:
            raise NoDisponible("limite_agotado")
        if resp.status_code in (401, 403):
            raise NoDisponible("clave_rechazada")
        if resp.status_code >= 400:
            raise NoDisponible("caida")
        cuerpo = resp.json()
        r = _de_cuerpo(cuerpo, modelo, version_prompt, time.monotonic() - t0, self.par)
        self.gastado += r.costo_usd
        if self.modo == "grabar":
            ruta.parent.mkdir(parents=True, exist_ok=True)
            g = {"pregunta_limpia": pregunta_limpia, "modelo": modelo, "version_prompt": version_prompt}
            if error_previo:
                g["error_previo"] = error_previo
            ruta.write_text(json.dumps({**g, "latencia_s": r.latencia_s, "respuesta": cuerpo}, ensure_ascii=False, indent=1) + "\n",
                            encoding="utf-8")
            r.grabacion = ruta.name
        return r


def registrar_uso(raiz, pregunta_limpia: str, consulta: dict | None, resultado: str, r: RespuestaLLM | None,
                  ruta: Path | None = None) -> dict:
    """P-03: huella de la pregunta, la consulta sin textos de lugar, el resultado, el modelo, los tokens y el costo."""
    def sin_lugar(x):
        if isinstance(x, dict):
            return {k: ("…" if k == "texto" else sin_lugar(v)) for k, v in x.items()}
        return x
    fila = {"fecha": time.strftime("%Y-%m-%dT%H:%M:%S"), "pregunta_sha256": hashlib.sha256(pregunta_limpia.encode("utf-8")).hexdigest(),
            "consulta": sin_lugar(consulta) if consulta else None, "resultado": resultado,
            "modelo": r.modelo if r else None, "tokens_entrada": r.tokens_entrada if r else 0,
            "tokens_salida": r.tokens_salida if r else 0, "costo_usd": r.costo_usd if r else 0.0}
    ruta = ruta or Path(raiz) / "salidas/interprete/uso.jsonl"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a", encoding="utf-8") as f:
        f.write(json.dumps(fila, ensure_ascii=False) + "\n")
    return fila
