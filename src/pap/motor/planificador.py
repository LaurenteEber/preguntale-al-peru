"""S1-03 — Planificador de cifras: consulta mínima + territorio resuelto → plan con la misma estructura que los
q*.yaml (`id`, `pregunta`, `intencion`, `territorio`, `periodo`, `plantilla`, `cifras`, `grupos`) más metadatos
del plan (`tema`, `respuesta_parcial`, `estructura_efecto`, `lado_a_lado`, `cruce`, `bloques`, `no_se_puede`…).

Python genérico: ninguna regla de un tema vive aquí. Qué cifras pide cada tema × intención está en
curados/motor/intenciones.yaml (cada fila cita su decisión). Los metadatos fijos salen de dim_indicador
(`niveles_validos`, `anios_disponibles`, `quiebres`, `tema_id`), de cruces_permitidos (`Contexto.cruces`) y de
map_intencion_tema (R-GASTO-08b). Los años se resuelven con `Motor.anio` (R-MOTOR-03).

No anticipa la supresión por precisión, privacidad ni falta de inferencia (E-02, E-03, P-04): eso es del validador
(`Motor.evaluar`); S1-05 lee su resultado. Solo registra en `no_se_puede` lo que los metadatos fijos ya dicen.
"""
from __future__ import annotations

import copy
from functools import lru_cache
from pathlib import Path

import yaml

from .territorio import Resuelto

RUTA_INTENCIONES = Path("curados/motor/intenciones.yaml")
RUTA_PARAMETROS = Path("curados/motor/parametros_motor.yaml")


# ----------------------------------------------------------------------------- tablas

@lru_cache(maxsize=None)
def _leer(raiz: str, ruta: str) -> dict:
    return yaml.safe_load((Path(raiz) / ruta).read_text(encoding="utf-8"))


def cargar_parametros(raiz) -> dict:
    """parametros_motor.yaml (en memoria; quien lo modifique debe copiarlo antes: `copy.deepcopy`)."""
    return _leer(str(raiz), str(RUTA_PARAMETROS))


def cargar_intenciones(raiz) -> dict:
    return _leer(str(raiz), str(RUTA_INTENCIONES))


def formato_id_cifra(*, indicador, medida, nivel, territorio, anio, rol, raiz=None, formato: str | None = None) -> str:
    """Id estable de cifra con el formato de parametros_motor.yaml (`planificador.formato_id_cifra`)."""
    if formato is None:
        formato = cargar_parametros(raiz)["planificador"]["formato_id_cifra"]["valor"]
    return formato.format(indicador=indicador, medida=medida, nivel=nivel, territorio=territorio, anio=anio, rol=rol)


# ----------------------------------------------------------------------------- años (R-MOTOR-03, E-07)

def _anios(motor, ind: str) -> list[int]:
    return sorted(int(a) for a in motor.ctx.indicadores[ind]["anios_disponibles"])


def _solo_punto(motor) -> set:
    return set(cargar_intenciones(motor.ctx.raiz)["quiebres"]["solo_el_punto"])


def _punto_excluido(motor, ind: str, y: int) -> bool:
    """Un quiebre de modo excluye solo ese punto (E-07), salvo que el indicador lo declare comparable consigo mismo."""
    solo = _solo_punto(motor)
    return any(int(q["anio"]) == y and q["tipo"] in solo and y not in [int(c) for c in q.get("comparable_con") or []]
               for q in motor.ctx.indicadores[ind].get("quiebres") or [])


def _comparable(motor, ind: str, a: int, b: int) -> bool:
    """a < b se pueden comparar: ni a ni b son un punto excluido (E-07: el año excluido tampoco se compara como año final) y ningún
    otro quiebre cae en (a, b] sin declarar a comparable."""
    if _punto_excluido(motor, ind, a) or _punto_excluido(motor, ind, b):
        return False
    solo = _solo_punto(motor)
    for q in motor.ctx.indicadores[ind].get("quiebres") or []:
        if q["tipo"] not in solo and a < int(q["anio"]) <= b and a not in [int(c) for c in q.get("comparable_con") or []]:
            return False
    return True


def quiebre_que_corta(motor, ind: str, a: int, b: int) -> dict | None:
    """El quiebre que impide comparar a < b (el punto excluido a o b, o el quiebre que cae en (a, b]); None si se pueden comparar."""
    solo = _solo_punto(motor)
    quiebres = motor.ctx.indicadores[ind].get("quiebres") or []
    for q in quiebres:
        y = int(q["anio"])
        if q["tipo"] in solo and y in (a, b) and y not in [int(c) for c in q.get("comparable_con") or []]:
            return q
    for q in quiebres:
        if q["tipo"] not in solo and a < int(q["anio"]) <= b and a not in [int(c) for c in q.get("comparable_con") or []]:
            return q
    return None


def anio_anterior(motor, ind: str, anio: int) -> int | None:
    """El año anterior disponible con el que `anio` es comparable (a través de un quiebre de modo, no de los demás)."""
    c = [y for y in _anios(motor, ind) if y < anio and _comparable(motor, ind, y, anio)]
    return max(c) if c else None


def anio_primero(motor, ind: str, anio: int, desde: int | None = None) -> int | None:
    """Primer año de la serie (desde `desde`) comparable con `anio`; None si la serie tiene un solo año."""
    c = [y for y in _anios(motor, ind) if y < anio and (desde is None or y >= desde) and _comparable(motor, ind, y, anio)]
    return min(c) if c else None


# ----------------------------------------------------------------------------- territorio

class _Escalera:
    def __init__(self, t: dict):
        e = t["escalera_niveles"]
        self.pasos: list[str] = e["valor"]
        self.nacional = e["nacional"]
        self.ambito_en = e["ambito_en"]
        self.id_cubo = e["id_cubo"]

    def idx(self, peldano: str) -> int:
        return self.pasos.index(peldano)

    def peldano(self, res: Resuelto) -> str:
        return res.nivel if res.nivel in self.pasos else self.ambito_en     # un ámbito ocupa el peldaño de departamento

    def en(self, res: Resuelto, peldano: str):
        """(nivel, id) del lugar en ese peldaño, en la codificación del cubo; None si no se puede derivar."""
        if peldano == self.pasos[-1]:
            return self.nacional["nivel"], self.nacional["id"]
        propio = self.peldano(res)
        if peldano == propio:
            return res.nivel, res.id
        if self.idx(peldano) < self.idx(propio):
            return None
        if peldano == self.ambito_en and res.ambito_lima:                    # T-03: el ámbito, no el departamento 15
            return res.ambito_lima, res.ambito_lima
        if res.ubigeo and peldano in self.id_cubo:
            u = res.ubigeo
            return peldano, self.id_cubo[peldano].format(u2=u[:2], u4=u[:4], u6=u[:6])
        return None


def _validos(motor, ind: str) -> set:
    return {x["nivel"] for x in motor.ctx.indicadores[ind].get("niveles_validos") or []}


def _lista(resuelto) -> list:
    if resuelto is None:
        return []
    xs = list(resuelto) if isinstance(resuelto, (list, tuple)) else [resuelto]
    for x in xs:
        if not isinstance(x, Resuelto):
            raise TypeError("planificar necesita territorios resueltos (Resuelto); resuelve antes la aclaración")
    return xs


def _anio_datos_desde(motor, res: Resuelto):
    """Primer año con dato propio del distrito entre todas sus versiones (T-01: `anio_datos_desde`); una versión histórica con
    límites anteriores cuenta. Sin la tabla, el de la versión vigente (`Resuelto.anio_datos_desde`)."""
    anios = [res.anio_datos_desde] if res.anio_datos_desde is not None else []
    u = motor.ctx.ubigeos
    if u is not None and res.ubigeo:
        anios += [int(a) for a in u[u.ubigeo_inei.astype(str) == res.ubigeo].anio_datos_desde.dropna()]
    return min(anios) if anios else None


# ----------------------------------------------------------------------------- referencias y filas

def _ruta(d: dict, ruta: str):
    for k in ruta.split("."):
        d = d[k]
    return d


def _referencia(nombre: str, motor, tabla: dict, par: dict):
    """`$nombre` de una tabla de referencia (p. ej. el indicador cuyo tema_id es el defecto de map_intencion_tema)."""
    r = tabla["referencias"][nombre]
    mapa = motor.ctx.param(r["regla"], r["tabla"]) or {}
    clave = _ruta(par, r["clave_en"])["valor"]
    valor = (mapa.get(clave) or {}).get(r["campo"])
    for i, d in motor.ctx.indicadores.items():
        if valor is not None and d.get(r["indicador_con"]) == valor:
            return i
    return None


def _plano(xs) -> list:
    out = []
    for x in xs or []:
        out.extend(_plano(x) if isinstance(x, list) else [x])
    return out


def _entrada(tabla: dict, tema: str, intencion: str) -> dict:
    base = tabla["intenciones"][intencion]
    t = tabla["temas"][tema]
    entrada = {**base, **(t.get(intencion) or {})}
    entrada.setdefault("principal", t["principal"])
    return entrada


def _cumple(cuando: dict, principal, peldano) -> bool:
    if "principal" in cuando and principal not in cuando["principal"]:
        return False
    return not ("nivel" in cuando and peldano not in cuando["nivel"])


def _cruce_activo(motor, tema: str, tabla: dict):
    estado = tabla["cruces"]["estado_activo"]
    for c in motor.ctx.cruces:
        if c.get("estado_propuesta") == estado and tema in {motor.ctx.indicadores[c["indicador_a"]]["tema"],
                                                            motor.ctx.indicadores[c["indicador_b"]]["tema"]}:
            return c
    return None


# ----------------------------------------------------------------------------- periodo

def _periodo_pedido(cm: dict, par: dict) -> dict:
    p = cm.get("periodo")
    if p:
        return dict(p)
    tipo = par["periodo"]["por_intencion"]["valor"].get(cm["intencion"], par["periodo"]["por_defecto"]["valor"])
    return {"tipo": tipo}


def _fin(periodo: dict):
    if periodo["tipo"] == "anio":
        return periodo["anio"]
    if periodo["tipo"] == "serie" and periodo.get("hasta") not in (None, "ultimo"):
        return periodo["hasta"]
    return None


# ----------------------------------------------------------------------------- planificar

def planificar(consulta_minima: dict, resuelto, motor, *, parametros: dict | None = None) -> dict:
    """`resuelto`: un `Resuelto` (o dos, [lugar, comparar_con], en comparación). En `identificar_extremo`: el territorio
    de `dentro_de` ya resuelto, o None si no lo hay. Devuelve el plan (estructura de los q*.yaml)."""
    raiz = motor.ctx.raiz
    tabla = cargar_intenciones(raiz)
    par = parametros if parametros is not None else cargar_parametros(raiz)
    esc = _Escalera(tabla)
    fmt = par["planificador"]["formato_id_cifra"]["valor"]
    intencion = consulta_minima["intencion"]
    ubicaciones = _lista(resuelto)
    tema = consulta_minima.get("tema") or motor.ctx.indicadores[consulta_minima["indicador"]]["tema"]
    entrada = _entrada(tabla, tema, intencion)
    motivos: list[dict] = []
    omitidas: list[dict] = []
    decisiones: set = set()

    def cita(x):
        if isinstance(x, dict) and x.get("decision"):
            decisiones.add(str(x["decision"]))

    cita(entrada)
    plan = {"id": None, "pregunta": consulta_minima.get("pregunta_original"), "intencion": intencion, "tema": tema,
            "territorio": None, "periodo": None, "plantilla": entrada["plantilla"], "cifras": [], "grupos": []}
    flags = {k: bool(entrada.get(k)) for k in ("respuesta_parcial", "estructura_efecto", "lado_a_lado")}

    # --------------------------------------------------------- intenciones que ordenan unidades (sin territorio pedido)
    if entrada.get("ranking"):
        nivel = consulta_minima["territorio"]["nivel"]
        plan["territorio"] = {"nivel": nivel, "id": None, "nombre_pedido": None}
        plan["id"] = f"{intencion}__{tema}__{nivel}"
        plan["pregunta"] = plan["pregunta"] or f"{intencion} {tema} {nivel}"
        plan["periodo"] = _periodo_pedido(consulta_minima, par)
        plan["grupos_estadisticos"] = None
        nac = esc.nacional["nivel"]
        if (ubicaciones and ubicaciones[0].nivel != nac
                and par["planificador"]["extremo_dentro_de"]["valor"] == "solo_nacional"):
            motivos.append({"motivo": "extremo_dentro_de_no_soportado", "dentro_de": ubicaciones[0].nombre_mostrado})
        else:
            elegido = None
            for r in esc.pasos[esc.idx(nivel):]:
                elegido = next((c for c in entrada["casos"] if _cumple(c["cuando"], None, r)), None)
                if elegido:
                    break
            if elegido is None:
                motivos.append({"motivo": "intencion_no_soportada", "tema": tema, "intencion": intencion})
            else:
                cita(elegido)
                plan["grupos"] = [{k: v for k, v in g.items() if k != "decision"} for g in elegido["grupos"]]
                for g in elegido["grupos"]:
                    cita(g)
                plan["grupos_estadisticos"] = elegido.get("grupos_estadisticos")
                plan["bloques"] = list(elegido.get("bloques") or [])
                r = next(r for r in esc.pasos[esc.idx(nivel):] if _cumple(elegido["cuando"], None, r))
                if r != nivel:
                    motivos.append({"motivo": "nivel_no_valido", "nivel_pedido": nivel, "nivel_planificado": r})
        return _cerrar(plan, flags, motivos, omitidas, decisiones, entrada)

    if not ubicaciones:
        raise TypeError(f"la intención {intencion} necesita el territorio resuelto")

    # --------------------------------------------------------- cruce: solo la lista blanca
    cruce = None
    if entrada.get("requiere_cruce"):
        cruce = _cruce_activo(motor, tema, tabla)
        if cruce is None:
            motivos.append({"motivo": "cruce_fuera_de_lista_blanca", "tema": tema})
        else:
            esperado = _referencia(tabla["cruces"]["indicador_a_igual_a"][1:], motor, tabla, par)
            if cruce["indicador_a"] != esperado:
                motivos.append({"motivo": "cadena_gasto_distinta", "indicador": cruce["indicador_a"]})
                cruce = None
        if cruce is None:                       # dos cifras separadas: lo que el tema pediría sin cruce
            entrada = _entrada(tabla, tema, "nivel_actual")
            flags = dict.fromkeys(flags, False)
    plan["cruce"] = cruce["id_cruce"] if cruce else None

    def ref(s):
        if s == "$principal":
            return principal
        if s == "$cruce.a":
            return cruce["indicador_a"] if cruce else None
        if s == "$cruce.b":
            return cruce["indicador_b"] if cruce else None
        if isinstance(s, str) and s.startswith("$"):
            return _referencia(s[1:], motor, tabla, par)
        return s

    # --------------------------------------------------------- principal y nivel (R-REG-02: sube si no es válido)
    candidatos = [ref(c) for c in ([consulta_minima["indicador"]] if consulta_minima.get("indicador") else entrada["principal"])]
    candidatos = [c for c in candidatos if c]
    principal, planeados = None, []
    for k in range(len(esc.pasos)):
        ts = []
        for res in ubicaciones:
            j = min(esc.idx(esc.peldano(res)) + k, len(esc.pasos) - 1)
            lugar = esc.en(res, esc.pasos[j])
            ts.append(None if lugar is None else (esc.pasos[j], *lugar))
        if any(t is None for t in ts):
            continue
        for ind in candidatos:
            if all(t[1] in _validos(motor, ind) for t in ts):
                principal = ind
                planeados = [{"res": res, "peldano": t[0], "nivel": t[1], "id": t[2], "subio": k > 0}
                             for res, t in zip(ubicaciones, ts)]
                break
        if principal:
            break
    plan["territorio"] = {"nivel": ubicaciones[0].nivel, "id": ubicaciones[0].id, "nombre_pedido": ubicaciones[0].nombre_mostrado}
    if len(ubicaciones) > 1:
        plan["territorio_comparado"] = {"nivel": ubicaciones[1].nivel, "id": ubicaciones[1].id,
                                        "nombre_pedido": ubicaciones[1].nombre_mostrado}
    plan["id"] = "__".join([intencion, tema] + [u.id for u in ubicaciones])
    plan["pregunta"] = plan["pregunta"] or f"{intencion} {tema} " + " / ".join(u.nombre_mostrado for u in ubicaciones)
    periodo = _periodo_pedido(consulta_minima, par)
    if len(ubicaciones) > 1 and (ubicaciones[0].nivel, ubicaciones[0].id) == (ubicaciones[1].nivel, ubicaciones[1].id):
        motivos.append({"motivo": "mismo_lugar"})              # S1-09: el mismo lugar dos veces; no hay nada que comparar
        plan["periodo"] = periodo
        return _cerrar(plan, flags, motivos, omitidas, decisiones, entrada)
    if principal is None:
        motivos.append({"motivo": "nivel_no_valido", "nivel_pedido": ubicaciones[0].nivel, "nivel_planificado": None})
        plan["periodo"] = periodo
        return _cerrar(plan, flags, motivos, omitidas, decisiones, entrada)
    for p in planeados:
        if p["subio"]:
            motivos.append({"motivo": "nivel_no_valido", "nivel_pedido": p["res"].nivel, "nivel_planificado": p["nivel"],
                            "indicador": principal})
            break
    caso = next((c for c in entrada["casos"] if _cumple(c["cuando"], principal, planeados[0]["peldano"])), None)
    if caso is None:
        motivos.append({"motivo": "intencion_no_soportada", "tema": tema, "intencion": intencion})
        plan["periodo"] = periodo
        return _cerrar(plan, flags, motivos, omitidas, decisiones, entrada)
    cita(caso)
    plan["bloques"] = list(caso.get("bloques") or [])
    plan["tema_gasto"] = motor.ctx.indicadores[principal].get("tema_id")

    # --------------------------------------------------------- cifras
    desde, fin = periodo.get("desde") if periodo["tipo"] == "serie" else None, _fin(periodo)
    hechas: list[dict] = []
    avisos_periodo: list[dict] = []

    def lugares(plantilla):
        t = plantilla.get("territorio", "pedido")
        for p in planeados:
            if t == "pedido":
                yield p, (p["nivel"], p["id"])
            elif t == "regional":
                lugar = esc.en(p["res"], esc.ambito_en) if esc.idx(p["peldano"]) <= esc.idx(esc.ambito_en) else None
                if lugar:
                    yield p, lugar
            elif t == "nacional":
                yield p, (esc.nacional["nivel"], esc.nacional["id"])

    for t in _plano(caso["cifras"]):
        if t.get("si_parametro") and not _ruta(par, t["si_parametro"])["valor"]:
            continue
        cita(t)
        ind = ref(t["indicador"])
        if ind is None:
            continue
        for p, (nivel, tid) in lugares(t):
            if nivel not in _validos(motor, ind):
                omitidas.append({"indicador": ind, "nivel": nivel, "territorio": tid, "motivo": "nivel_no_valido"})
                continue
            fin_ind = motor.anio(ind, fin)
            a = t.get("anio", "periodo")
            if isinstance(a, dict):
                otro = ref(a["comparado_de"])
                a = next((h["comparar_con"] for h in hechas if h["indicador"] == otro and h["nivel"] == nivel
                          and h["territorio"] == tid and h.get("comparar_con") is not None), None)
            elif a == "periodo":
                a = fin_ind
            elif a == "ultimo":
                a = motor.anio(ind, None)
            elif a == "primero_serie":
                a = anio_primero(motor, ind, fin_ind, desde)
            if a is None:
                continue
            spec = {"indicador": ind, "anio": int(a), "nivel": nivel, "territorio": tid, "rol": t["rol"]}
            c = t.get("comparar_con")
            if c:
                y = anio_anterior(motor, ind, spec["anio"]) if c == "anterior_disponible" else anio_primero(motor, ind, spec["anio"], desde)
                if y is not None:
                    spec["comparar_con"] = y
                    if c == "primero_serie" and t["rol"] == "principal":      # S1-09 (A-H2): un inicio de serie que no se pudo respetar se dice
                        pedido = desde if desde is not None else _anios(motor, ind)[0]
                        q = quiebre_que_corta(motor, ind, pedido, spec["anio"]) if pedido < y and pedido in _anios(motor, ind) else None
                        if q is not None:
                            avisos_periodo.append({"aviso": "desde_no_comparable", "indicador": ind, "pedido": desde is not None,
                                                   "desde": pedido, "primero": y, "hasta": spec["anio"], "anio_quiebre": int(q["anio"]), "tipo_quiebre": q["tipo"]})
                elif t["rol"] == "principal" and intencion == "evolucion":
                    if _punto_excluido(motor, ind, spec["anio"]):             # S1-09 (A-H1, E-07): el último año es el punto excluido
                        avisos_periodo.append({"aviso": "anio_final_excluido", "indicador": ind, "anio": spec["anio"],
                                               "anio_quiebre": spec["anio"], "tipo_quiebre": "modo"})
                    else:
                        motivos.append({"motivo": "serie_un_solo_anio", "indicador": ind})
            if p["subio"] and (nivel, tid) == (p["nivel"], p["id"]):
                spec["nivel_pedido"] = p["res"].nivel
            igual = next((h for h in hechas if (h["indicador"], h["anio"], h["nivel"], h["territorio"]) ==
                          (ind, spec["anio"], nivel, tid)), None)
            if igual:                                   # misma cifra pedida dos veces: gana el rol principal
                if t["rol"] == "principal":
                    igual["rol"] = "principal"
                if "comparar_con" in spec:
                    igual.setdefault("comparar_con", spec["comparar_con"])
                continue
            hechas.append(spec)
    for h in hechas:
        h["id"] = formato_id_cifra(indicador=h["indicador"], medida=motor.medida(h["indicador"]), nivel=h["nivel"],
                                   territorio=h["territorio"], anio=h["anio"], rol=h["rol"], formato=fmt)
    plan["cifras"] = [{k: h[k] for k in ("id", "indicador", "anio", "nivel", "territorio", "rol", "comparar_con", "nivel_pedido")
                       if k in h} for h in hechas]
    # lo que los metadatos fijos ya dicen (no la precisión ni la privacidad: eso es del validador)
    vistos = set()
    for h in hechas:                  # T-01 / T-04: un distrito sin ninguna versión con datos hasta el año de la cifra no tiene cifra propia
        res = next((p["res"] for p in planeados if (p["nivel"], p["id"]) == (h["nivel"], h["territorio"])), None)
        if res is None or h["rol"] != "principal" or h["nivel"] != "distrito" or res.id in vistos:
            continue
        desde = _anio_datos_desde(motor, res)
        if desde is not None and h["anio"] < desde:
            vistos.add(res.id)
            motivos.append({"motivo": "distrito_creado_despues", "distrito": res.nombre_mostrado, "ubigeo": res.ubigeo,
                            "anio_datos_desde": desde, "anio_ultimo_dato": h["anio"], "indicador": h["indicador"]})
    if periodo["tipo"] == "anio":
        for ind in dict.fromkeys(h["indicador"] for h in hechas if h["rol"] == "principal"):
            if periodo["anio"] not in _anios(motor, ind):
                m = {"motivo": "anio_sin_datos", "indicador": ind, "anio_pedido": periodo["anio"], "anios_disponibles": _anios(motor, ind)}
                d = motor.ctx.indicadores[ind]
                hermanos = {i: _anios(motor, i) for i, x in motor.ctx.indicadores.items()      # S1-09 (H7): las formas de medir del mismo tema y fuente
                            if x.get("tema") == d.get("tema") and x.get("fuente_principal") == d.get("fuente_principal")}
                if len(hermanos) > 1:
                    m["anios_por_indicador"] = dict(sorted(hermanos.items(), key=lambda kv: -kv[1][0]))
                motivos.append(m)
    if periodo["tipo"] == "serie":
        periodo.setdefault("hasta", "ultimo")
        if periodo.get("desde") is None:
            principales = [h["indicador"] for h in hechas if h["rol"] == "principal"] or [principal]
            periodo["desde"] = min(_anios(motor, i)[0] for i in principales)
        periodo = {"tipo": "serie", "desde": periodo["desde"], "hasta": periodo["hasta"]}
    plan["periodo"] = periodo
    plan["avisos_periodo"] = avisos_periodo
    return _cerrar(plan, flags, motivos, omitidas, decisiones, entrada)


def _cerrar(plan, flags, motivos, omitidas, decisiones, entrada) -> dict:
    plan.update(flags)
    plan["no_se_puede"] = motivos[0] if motivos else None
    plan["motivos_no_se_puede"] = motivos
    plan["omitidas"] = omitidas
    plan["decisiones"] = sorted(decisiones)
    plan.setdefault("cruce", None)
    plan.setdefault("avisos_periodo", [])
    plan.setdefault("tema_gasto", None)
    plan.setdefault("grupos_estadisticos", None)
    plan.setdefault("bloques", [])
    return copy.deepcopy(plan)
