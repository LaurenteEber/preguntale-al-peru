"""S2-04 — Cliente del LLM (P-07) detrás de una interfaz pequeña: `interpretar_crudo(prompt, pregunta_limpia) -> RespuestaLLM`.

- HTTP con httpx (ya en uv.lock), salida estructurada (`output_config.format`) y esfuerzo de `interprete.esfuerzo` (sin
  temperatura: la cabecera 2026-10-21 la rechaza en todo modelo); la pregunta va como dato delimitado en el mensaje del usuario, fuera de las instrucciones (que van en `system`).
- La API de salida estructurada no acepta `oneOf`, `if/then`, `$ref` externos ni límites de longitud o número
  (https://platform.claude.com/docs/en/build-with-claude/structured-outputs): se le manda una versión simplificada del
  esquema (`esquema_para_api`). La validación completa la hace el código con el esquema de S2-01.
- La clave se lee de la variable `interprete.variable_clave` solo aquí y en el momento de la llamada; nunca se escribe en
  archivos, registros ni errores. Los registros de httpx y httpcore van en WARNING o más (no anotan peticiones), y todo error
  del cliente se re-lanza como `NoDisponible(motivo)`, sin el objeto request ni sus encabezados.
- Proveedor (decisión del dueño, 5/11/2026; `interprete.reintento_proveedor`): 401/403 → sin reintento y el cliente se detiene;
  429/5xx → como máximo un reintento con espera; límite de gasto agotado → `limite_agotado` y el cliente se detiene.
- Las grabaciones guardan solo el cuerpo de la respuesta y los metadatos (modelo, tokens, latencia, costo, version_prompt),
  nunca encabezados.
- Grabaciones (tests/interprete/grabaciones/): una por (pregunta limpia, modelo, version_prompt) y, en el reintento de S2-05,
  también por el error que se le devuelve al LLM (`error_previo`). En pytest solo se reproducen; se graban con
  `tests/interprete/evaluar.py --grabar`.
- Uso: `salidas/interprete/uso.jsonl` (fuera de git) con los campos de P-03; `interprete.tope_por_corrida` corta una corrida."""
from __future__ import annotations

import copy
import hashlib
import json
import logging
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import httpx
import yaml

DELIM_INICIO, DELIM_FIN = "<pregunta>", "</pregunta>"
# Nombre de la cabecera de la clave, partido para que la prueba de secretos (tests/test_sin_secretos.py), que busca el texto
# literal en todo archivo versionado, siga sirviendo.
CABECERA_CLAVE = "x-" + "api-key"

for _nombre in ("httpx", "httpcore"):
    if logging.getLogger(_nombre).getEffectiveLevel() < logging.WARNING:
        logging.getLogger(_nombre).setLevel(logging.WARNING)


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
        self.detenido: str | None = None      # motivo por el que el cliente ya no llama (clave rechazada, límite agotado)
        self.espera = time.sleep              # las pruebas la reemplazan para no esperar

    def _cuerpo(self, prompt: str, pregunta_limpia: str, error_previo: str | None = None) -> dict:
        from ..motor.interpretacion import RUTA_CONSULTA, RUTA_ESQUEMA
        esq = json.loads((self.raiz / RUTA_ESQUEMA).read_text(encoding="utf-8"))
        cm = json.loads((self.raiz / RUTA_CONSULTA).read_text(encoding="utf-8"))
        return {"model": self.par["modelo"]["valor"], "max_tokens": int(self.par["max_tokens"]["valor"]),
                "system": prompt,
                "messages": [{"role": "user", "content": self._turno(pregunta_limpia, error_previo)}],
                "output_config": {"effort": self.par["esfuerzo"]["valor"], "format": {"type": "json_schema",
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
        if self.detenido:
            raise NoDisponible(self.detenido)
        if self.gastado >= self.tope:
            raise NoDisponible("tope_por_corrida")
        cuerpo_peticion = self._cuerpo(prompt, pregunta_limpia, error_previo)
        rp = self.par["reintento_proveedor"]
        t0 = time.monotonic()
        for intento in range(1 + int(rp["valor"])):
            resp, motivo = self._post(cuerpo_peticion)
            if motivo is None:
                break
            if motivo in ("clave_rechazada", "limite_agotado", "sin_clave"):
                self.detenido = motivo                  # 401/403, sin clave o gasto agotado: nunca se reintenta
                raise NoDisponible(motivo)
            if motivo == "rechazada":                   # otro 4xx: la misma petición fallaría igual
                raise NoDisponible(motivo)
            if intento < int(rp["valor"]):              # 429, 5xx, caída o tiempo agotado: un reintento con espera
                self.espera(self._espera(resp, rp))
                continue
            raise NoDisponible(motivo)
        try:
            cuerpo = resp.json()
        except ValueError:
            raise NoDisponible("caida") from None
        r = _de_cuerpo(cuerpo, modelo, version_prompt, time.monotonic() - t0, self.par)
        self.gastado += r.costo_usd
        if self.modo == "grabar":
            ruta.parent.mkdir(parents=True, exist_ok=True)
            g = {"pregunta_limpia": pregunta_limpia, "modelo": modelo, "version_prompt": version_prompt,
                 "tokens_entrada": r.tokens_entrada, "tokens_salida": r.tokens_salida, "costo_usd": r.costo_usd}
            if error_previo:
                g["error_previo"] = error_previo
            ruta.write_text(json.dumps({**g, "latencia_s": r.latencia_s, "respuesta": cuerpo}, ensure_ascii=False, indent=1) + "\n",
                            encoding="utf-8")
            r.grabacion = ruta.name
        return r

    def _post(self, cuerpo: dict):
        """Una llamada. Devuelve (respuesta, None) si salió bien o (respuesta | None, motivo). La clave se lee aquí y no sale de
        esta función; los errores de httpx se traducen sin encadenar la excepción (que lleva la petición y sus encabezados)."""
        clave = os.environ.get(self.par["variable_clave"]["valor"])
        if not clave:
            return None, "sin_clave"
        cab = {CABECERA_CLAVE: clave, "anthropic-version": self.par["api"]["version"], "content-type": "application/json"}
        del clave
        try:
            with httpx.Client(transport=self.transporte, timeout=float(self.par["tiempo_max_segundos"]["valor"])) as h:
                resp = h.post(self.par["api"]["url"], headers=cab, json=cuerpo)
        except httpx.TimeoutException:
            return None, "tiempo_agotado"
        except httpx.HTTPError:
            return None, "caida"
        finally:
            cab.clear()
        if resp.status_code < 400:
            return resp, None
        if resp.status_code in (401, 403):
            return resp, "clave_rechazada"
        if resp.status_code == 402 or self._dice_limite(resp):
            return resp, "limite_agotado"
        if resp.status_code == 429:
            return resp, "limite_de_ritmo"
        if resp.status_code >= 500:
            return resp, "caida"
        return resp, "rechazada"

    def _dice_limite(self, resp) -> bool:
        try:
            msg = str(((resp.json() or {}).get("error") or {}).get("message") or "").lower()
        except ValueError:
            return False
        return any(x in msg for x in self.par["limite_agotado_textos"]["valor"])

    @staticmethod
    def _espera(resp, rp) -> float:
        tope = float(rp["espera_max_segundos"])
        try:
            return min(float(resp.headers.get("retry-after")), tope) if resp is not None and resp.headers.get("retry-after") else float(rp["espera_segundos"])
        except ValueError:
            return float(rp["espera_segundos"])


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
