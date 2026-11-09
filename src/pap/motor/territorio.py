"""S1-02 — Resolver territorial determinista (sin red, sin LLM).

Convierte lo que escribió la persona ({texto} | {ubigeo} | {ambito} | {nacional}) en un territorio vigente
(`Resuelto`) o en una pregunta de aclaración (`Aclaracion`). Lee solo dim_ubigeo_historico, dim_ambito,
`parametros_motor.yaml` (bloque `territorio`) y `curados/motor/textos/territorio.yaml`.

La normalización y los índices de nombres son los del validador (R-TERRITORIO-09): se importan, no se copian.
Decisiones: T-01 (anio_datos_desde), T-02 (nombres con tildes), T-03 (Lima), R-TERRITORIO-09, R-LENGUAJE-05.
"""
from __future__ import annotations

import difflib
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from .respuesta import nombre_completo_ubigeo
from .validador.reglas_etapa1_3 import NIVEL_PISTA, _ancestros, _candidatos, _indice_nombres, normalizar_texto  # noqa: F401

LM, LR, CALLAO, AMLC = "LIMA_METROPOLITANA", "LIMA_REGION", "CALLAO", "AREA_METROPOLITANA_LIMA_CALLAO"
ORDEN_NIVEL = {"departamento": 0, "provincia": 1, "distrito": 2}


@dataclass(frozen=True)
class Resuelto:
    nivel: str                       # nacional | departamento | provincia | distrito | ámbito de dim_ambito
    id: str                          # id de territorio del cubo: «PE», «09», «210801», «CALLAO»…
    ubigeo: str | None               # ubigeo INEI de 6 dígitos (None en nacional y ámbitos)
    nombre_mostrado: str
    nombre_completo: str
    departamento: str | None
    provincia: str | None
    ambito_lima: str | None          # LIMA_METROPOLITANA | LIMA_REGION | CALLAO | None
    anio_datos_desde: int | None
    provisional: bool = False        # estado_ubigeo = pendiente (R-LENGUAJE-05)

    def a_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Aclaracion:
    motivo: str                      # lima_a_secas | homonimo_niveles | homonimo_mismo_nivel | coincidencia_parcial
    pregunta: str                    #   | sin_coincidencia | demasiadas_opciones
    opciones: list = field(default_factory=list)   # [{etiqueta, territorio: Resuelto}]
    por_defecto: Resuelto | None = None

    def a_dict(self) -> dict:
        return {"motivo": self.motivo, "pregunta": self.pregunta,
                "opciones": [{"etiqueta": o["etiqueta"], "territorio": o["territorio"].a_dict()} for o in self.opciones],
                "por_defecto": self.por_defecto.a_dict() if self.por_defecto else None}


# ----------------------------------------------------------------------------- datos

@lru_cache(maxsize=None)
def _config(raiz: str) -> dict:
    r = Path(raiz)
    par = yaml.safe_load((r / "curados" / "motor" / "parametros_motor.yaml").read_text(encoding="utf-8"))["territorio"]
    txt = yaml.safe_load((r / "curados" / "motor" / "textos" / "territorio.yaml").read_text(encoding="utf-8"))
    palabras = {normalizar_texto(w): nivel for nivel, ws in par["palabras_que_fijan_nivel"]["valor"].items() for w in ws}
    return {
        "max": int(par["aclaracion_max_opciones"]["valor"]),
        "sugerencias": int(par["sin_coincidencia_sugerencias_max"]["valor"]),
        "similitud": float(par["similitud_min_para_sugerir"]["valor"]),
        "palabras_nivel": palabras,
        "nacional": {normalizar_texto(t) for t in par["textos_nacional"]["valor"]},
        "depto_a_secas": bool(par.get("departamento_a_secas", {}).get("activo", False)),   # T-03
        "lima_opciones": par["lima_a_secas"]["opciones"],
        "lima_defecto": par["lima_a_secas"]["por_defecto_sin_respuesta"],
        "txt": txt,
        "alias_ambito": {normalizar_texto(k): v for k, v in txt["alias_ambito"].items()},
        "alias_distrito": {normalizar_texto(k): v for k, v in txt["alias_distrito"].items()},
    }


def _filas(ctx) -> dict:
    """ubigeo → fila vigente (dict). Se guarda en el contexto: las dimensiones no cambian durante la corrida."""
    if getattr(ctx, "_territorio_filas", None) is None:
        ub = ctx.ubigeos
        assert ub is not None, "falta dim_ubigeo_historico"
        vig = ub[ub.vigente_hasta.isna()] if "vigente_hasta" in ub else ub
        ctx._territorio_filas = {str(r["ubigeo_inei"]): r for r in vig.to_dict("records")}
    return ctx._territorio_filas


def _cfg(ctx) -> dict:
    return _config(str(ctx.raiz))


def _t(ctx, clave: str, **kw) -> str:
    return _cfg(ctx)["txt"]["preguntas"][clave].format(**kw)


# ----------------------------------------------------------------------------- construcción de Resuelto

def _ambito_lima(u: str) -> str | None:
    if u.startswith("1501"):
        return LM
    if u.startswith("15") and u[:4] != "1500" and u[2:4] != "00":
        return LR
    if u.startswith("07"):
        return CALLAO
    return None


def _nombre(ctx, u: str) -> str | None:
    f = _filas(ctx).get(u)
    return str(f["nombre_mostrado"]) if f else None


def _resuelto(ctx, fila: dict) -> Resuelto:
    u = str(fila["ubigeo_inei"])
    nivel = fila["nivel"]
    if nivel == "nacional":
        return Resuelto("nacional", "PE", None, "Perú", "Perú", None, None, None, int(fila["anio_datos_desde"]))
    nombre = str(fila["nombre_mostrado"])
    if nivel == "departamento":
        completo, prov = nombre, None
    elif nivel == "provincia":
        completo, prov = f"{nombre} ({_nombre(ctx, u[:2] + '0000')})", nombre
    else:
        completo, prov = nombre_completo_ubigeo(ctx, u), _nombre(ctx, u[:4] + "00")
    desde = fila.get("anio_datos_desde")
    return Resuelto(
        nivel=nivel, id=u[:2] if nivel == "departamento" else u, ubigeo=u, nombre_mostrado=nombre,
        nombre_completo=completo, departamento=_nombre(ctx, u[:2] + "0000"), provincia=prov,
        ambito_lima=None if nivel == "departamento" and u[:2] == "15" else _ambito_lima(u),
        anio_datos_desde=int(desde) if desde == desde and desde is not None else None,
        provisional=fila.get("estado_ubigeo") == "pendiente")


def _ambito(ctx, ambito_id: str) -> Resuelto | None:
    a = ctx.ambitos
    if a is None:
        return None
    f = a[a.ambito_id == ambito_id]
    if f.empty:
        return None
    nombre = str(f.iloc[0].nombre_mostrado)
    dep = {LM: "150000", LR: "150000", CALLAO: "070000"}.get(ambito_id)
    return Resuelto(nivel=ambito_id, id=ambito_id, ubigeo=None, nombre_mostrado=nombre, nombre_completo=nombre,
                    departamento=_nombre(ctx, dep) if dep else None, provincia="Lima" if ambito_id == LM else None,
                    ambito_lima=None if ambito_id == AMLC else ambito_id, anio_datos_desde=None)


def _etiqueta(ctx, fila: dict) -> str:
    t = _cfg(ctx)["txt"]
    u = str(fila["ubigeo_inei"])
    nivel = fila["nivel"]
    prov = t["fragmentos"]["provincia"].format(provincia=_nombre(ctx, u[:4] + "00")) if nivel == "distrito" else ""
    dep = t["fragmentos"]["departamento"].format(departamento=_nombre(ctx, u[:2] + "0000")) if nivel != "departamento" else ""
    return t["fragmentos"]["opcion"].format(nombre=fila["nombre_mostrado"], nivel=t["niveles"][nivel],
                                              provincia=prov, departamento=dep)


def _clave_orden(ctx, fila: dict):
    u = str(fila["ubigeo_inei"])
    n = lambda c: normalizar_texto(_nombre(ctx, c) or "")  # noqa: E731
    return (ORDEN_NIVEL[fila["nivel"]], n(u[:2] + "0000"), n(u[:4] + "00") if fila["nivel"] != "departamento" else "",
            normalizar_texto(fila["nombre_mostrado"]), u)


def _opciones(ctx, filas: list[dict]) -> list[dict]:
    return [{"etiqueta": _etiqueta(ctx, f), "territorio": _resuelto(ctx, f)}
            for f in sorted(filas, key=lambda f: _clave_orden(ctx, f))]


def _sin_coincidencia(ctx) -> Aclaracion:
    return Aclaracion("sin_coincidencia", _t(ctx, "sin_coincidencia"))


def _preguntar(ctx, motivo: str, filas: list[dict], texto: str) -> Aclaracion:
    if len(filas) > _cfg(ctx)["max"]:  # aclaracion_exceso: no se listan; se pide provincia o departamento
        return Aclaracion("demasiadas_opciones", _t(ctx, "demasiadas_opciones", n=len(filas), texto=texto))
    return Aclaracion(motivo, _t(ctx, "homonimo_niveles" if motivo == "homonimo_niveles" else
                                 "homonimo_mismo_nivel" if motivo == "homonimo_mismo_nivel" else motivo, texto=texto),
                      _opciones(ctx, filas))


# ----------------------------------------------------------------------------- texto

def _limpiar(ctx, parte: str) -> tuple[str, str | None]:
    """Quita la palabra de nivel inicial («departamento de», «provincia», «dist.») y devuelve (nombre, nivel)."""
    palabras = parte.split()
    nivel = None
    if len(palabras) > 1 and palabras[0] in _cfg(ctx)["palabras_nivel"]:
        nivel = _cfg(ctx)["palabras_nivel"][palabras[0]]
        palabras = palabras[1:]
        if len(palabras) > 1 and palabras[0] in ("DE", "DEL"):
            palabras = palabras[1:]
    return " ".join(palabras), nivel


def _vigente_en(fila: dict, fecha: str | None) -> bool:
    return fecha is None or str(fila.get("vigente_desde") or "") <= fecha


def _variantes(partes: list[tuple[str, str | None]]):
    """Cada parte puede ser el lugar y las demás su jerarquía, en cualquier orden."""
    for i, (nombre, nivel) in enumerate(partes):
        yield nombre, nivel, [p for j, (p, _) in enumerate(partes) if j != i]


def _dedup(filas: list[dict]) -> list[dict]:
    return list({str(f["ubigeo_inei"]): f for f in filas}.values())


def _por_padres(ctx, filas: list[dict], padres: list[str]) -> list[dict]:
    for p in padres:
        filas = [f for f in filas if p in _ancestros(ctx, str(f["ubigeo_inei"]))]
    return filas


def _buscar(ctx, partes, fecha, tipo: str) -> list[dict]:
    """tipo: exacta | parcial. Devuelve filas vigentes (no el país) sin repetir."""
    idx = _indice_nombres(ctx.ubigeos)
    res: list[dict] = []
    for nombre, nivel, padres in _variantes(partes):
        if tipo == "exacta":
            cand = _candidatos(ctx, nombre, padres)
        else:
            palabras = set(nombre.split())
            cand = [f for k, filas in idx.items() if palabras <= set(k.split()) for f in filas.values()]
            cand = _por_padres(ctx, cand, padres)
        res += [f for f in cand if f["nivel"] != "nacional" and (nivel is None or f["nivel"] == nivel)
                and _vigente_en(f, fecha)]
    return _dedup(res)


def _parecidos(ctx, partes, fecha) -> list[dict]:
    idx = _indice_nombres(ctx.ubigeos)
    minimo = _cfg(ctx)["similitud"]
    mejor: dict[str, tuple[float, dict]] = {}
    for nombre, nivel, padres in _variantes(partes):
        sm = difflib.SequenceMatcher(autojunk=False)
        sm.set_seq2(nombre)
        for k, filas in idx.items():
            sm.set_seq1(k)
            if sm.real_quick_ratio() < minimo or sm.quick_ratio() < minimo:
                continue
            r = sm.ratio()
            if r < minimo:
                continue
            for f in _por_padres(ctx, list(filas.values()), padres):
                if f["nivel"] == "nacional" or (nivel and f["nivel"] != nivel) or not _vigente_en(f, fecha):
                    continue
                u = str(f["ubigeo_inei"])
                if u not in mejor or mejor[u][0] < r:
                    mejor[u] = (r, f)
    orden = sorted(mejor.values(), key=lambda x: (-x[0], _clave_orden(ctx, x[1])))
    return [f for _, f in orden[:_cfg(ctx)["sugerencias"]]]


def _lima_a_secas(ctx) -> Aclaracion:
    c = _cfg(ctx)
    rot = c["txt"]["lima_opciones"]
    ops = [{"etiqueta": rot[a], "territorio": _ambito(ctx, a)} for a in c["lima_opciones"]]
    return Aclaracion("lima_a_secas", _t(ctx, "lima_a_secas"), ops, _ambito(ctx, c["lima_defecto"]))


def _resolver_texto(ctx, texto: str, fecha: str | None) -> Resuelto | Aclaracion:
    c = _cfg(ctx)
    norm = normalizar_texto(texto)
    if not norm:
        return _sin_coincidencia(ctx)
    if norm in c["nacional"]:
        return _resuelto(ctx, _filas(ctx)["000000"])
    if norm in c["alias_ambito"]:
        return _ambito(ctx, c["alias_ambito"][norm])
    if norm in c["alias_distrito"]:
        return _resuelto(ctx, _filas(ctx)[c["alias_distrito"][norm]])
    partes = [_limpiar(ctx, p.strip()) for p in norm.split(",") if p.strip()]
    if not partes:
        return _sin_coincidencia(ctx)
    if len(partes) == 1:
        nombre, nivel = partes[0]
        if nombre == "LIMA" and nivel is None:
            return _lima_a_secas(ctx)                      # T-03
        if nombre == "CALLAO" and nivel in (None, "departamento"):
            return _ambito(ctx, CALLAO)                    # parametros territorio.callao
    cand = _buscar(ctx, partes, fecha, "exacta")
    if len(cand) == 1:
        return _resuelto(ctx, cand[0])
    if cand:
        niveles = {f["nivel"] for f in cand}
        dptos = [f for f in cand if f["nivel"] == "departamento"]
        if _cfg(ctx)["depto_a_secas"] and len(partes) == 1 and partes[0][1] is None and len(dptos) == 1:
            return _resuelto(ctx, dptos[0])                # T-03: el nombre a secas de un departamento se responde como departamento
        nombres = {f["nombre_mostrado"] for f in cand}      # S3-10 (H-10): «Ayaviri», no «distrito Ayaviri» (y con tildes, T-02)
        nombre = nombres.pop() if len(nombres) == 1 else texto.strip()
        return _preguntar(ctx, "homonimo_niveles" if len(niveles) > 1 else "homonimo_mismo_nivel", cand, nombre)
    parcial = _buscar(ctx, partes, fecha, "parcial")
    if parcial:
        return _preguntar(ctx, "coincidencia_parcial", parcial, texto.strip())
    sug = _parecidos(ctx, partes, fecha)
    if sug:
        return Aclaracion("sin_coincidencia", _t(ctx, "sugerencia", texto=texto.strip()), _opciones_ordenadas(ctx, sug))
    return _sin_coincidencia(ctx)


def oferta_otros_niveles(ctx, entrada: dict, resuelto, fecha: str | None = None) -> str | None:
    """T-03: si `entrada` (texto a secas) se resolvió como departamento y existe una provincia o un distrito con ese nombre,
    la frase que lo dice y enseña a pedirlos (textos en territorio.yaml, `oferta_otros_niveles`). Solo ofrece niveles que existen."""
    if not _cfg(ctx)["depto_a_secas"] or not isinstance(resuelto, Resuelto) or resuelto.nivel != "departamento" or not isinstance(entrada.get("texto"), str):
        return None
    partes = [_limpiar(ctx, p.strip()) for p in normalizar_texto(entrada["texto"]).split(",") if p.strip()]
    if len(partes) != 1 or partes[0][1] is not None:
        return None
    niveles = {f["nivel"] for f in _buscar(ctx, partes, fecha, "exacta")} - {"departamento"}
    clave = "ambos" if niveles == {"provincia", "distrito"} else next(iter(niveles), None)
    if clave is None:
        return None
    return _cfg(ctx)["txt"]["oferta_otros_niveles"][clave].format(nombre=resuelto.nombre_mostrado)


def _opciones_ordenadas(ctx, filas: list[dict]) -> list[dict]:
    """Las sugerencias por similitud conservan su orden (más parecida primero)."""
    return [{"etiqueta": _etiqueta(ctx, f), "territorio": _resuelto(ctx, f)} for f in filas]


# ----------------------------------------------------------------------------- API

def resolver(entrada: dict, ctx, fecha: str | None = None) -> Resuelto | Aclaracion:
    """`entrada` es el objeto de territorio de la consulta mínima: {texto} | {ubigeo} | {ambito} | {nacional: true}.
    `fecha` (AAAA-MM-DD) exige que el distrito ya exista ese día; sin fecha se usan los vigentes."""
    if entrada.get("nacional") is True:
        return _resuelto(ctx, _filas(ctx)["000000"])
    if "ambito" in entrada:
        r = _ambito(ctx, entrada["ambito"])
        return r if r else _sin_coincidencia(ctx)
    if "ubigeo" in entrada:
        u = str(entrada["ubigeo"])
        u6 = {2: u + "0000", 4: u + "00", 6: u}.get(len(u))
        f = _filas(ctx).get(u6) if u6 else None
        return _resuelto(ctx, f) if f and f["nivel"] != "nacional" else _sin_coincidencia(ctx)
    if isinstance(entrada.get("texto"), str):
        return _resolver_texto(ctx, entrada["texto"], fecha)
    return _sin_coincidencia(ctx)
