"""S1-08 — Generador de la matriz de cobertura: arma consultas mínimas (el mismo objeto que valida `pap.motor.consulta`) para
temas × intenciones × territorios × periodos. Determinista: orden fijo y una sola semilla (`matriz_cobertura.semilla`).

Todo número (semilla, tamaño de la muestra, cuántos homónimos…) sale de `matriz_cobertura` de curados/motor/parametros_motor.yaml;
los temas y las intenciones, de curados/motor/intenciones.yaml; los datos de territorio, de dim_ubigeo_historico y de
backlog/slice-1/evidencia/s1-00_datos_territorio.txt (homónimos y distritos sin establecimientos en el SIEN).
No calcula ninguna cifra: solo pregunta."""
from __future__ import annotations

import random
import re
from pathlib import Path

import yaml

AMBITOS_LIMA = ["LIMA_METROPOLITANA", "LIMA_REGION", "CALLAO"]
PERIODOS = ["ultimo", "intermedio", "sin_datos", "serie"]
NIVELES_EXTREMO = ["departamento", "provincia", "distrito"]
Q2, Q3 = "210801", "150132"
ALTO_TRUJILLO, SANGANI = "130112", "120307"


def _yaml(raiz: Path, ruta: str):
    return yaml.safe_load((Path(raiz) / ruta).read_text(encoding="utf-8"))


def parametros(raiz) -> dict:
    """{nombre: valor} de `matriz_cobertura` en parametros_motor.yaml."""
    return {k: v["valor"] for k, v in _yaml(raiz, "curados/motor/parametros_motor.yaml")["matriz_cobertura"].items()}


def temas_e_intenciones(raiz) -> tuple[list[str], list[str]]:
    cat = _yaml(raiz, "curados/motor/intenciones.yaml")
    return list(cat["temas"]), list(cat["intenciones"])


# ----------------------------------------------------------------------------------------------------- territorios

def _vigentes(ctx):
    ub = ctx.ubigeos
    return ub[ub.vigente_hasta.isna()] if "vigente_hasta" in ub else ub


def datos_s1_00(raiz) -> dict:
    """Del archivo de evidencia de S1-00: los homónimos («NOMBRE»: ubigeo nivel, …) y los distritos vigentes sin filas en el SIEN."""
    txt = (Path(raiz) / "backlog/slice-1/evidencia/s1-00_datos_territorio.txt").read_text(encoding="utf-8")
    homonimos = []
    for m in re.finditer(r"^«([^»]+)»: (.+)$", txt, re.M):
        opciones = re.findall(r"(\d{6}) (departamento|provincia|distrito)", m.group(2))
        homonimos.append({"texto": m.group(1).title(), "opciones": opciones})
    sec = txt.split("sin ninguna fila en fact_sien_hb_ubigeo", 1)[1]
    sin_sien = [(u, n) for u, n, e in re.findall(r"\('(\d{6})', '([^']+)', '(\w+)'\)", sec) if e == "vigente"]
    return {"homonimos": homonimos, "sin_sien": sin_sien}


def _estratificar(pool: list[tuple[str, str]], n: int, rng: random.Random) -> list[str]:
    """`pool`: [(ubigeo, estrato)]. n ubigeos repartidos entre los estratos en proporción a su tamaño (resto mayor), con la
    semilla fija. El orden de entrada se fija antes (ordenado) para que no dependa del orden del parquet."""
    por: dict[str, list[str]] = {}
    for u, e in sorted(pool):
        por.setdefault(e, []).append(u)
    total = sum(len(v) for v in por.values())
    cuota = {e: n * len(v) / total for e, v in por.items()}
    base = {e: int(c) for e, c in cuota.items()}
    for e in sorted(por, key=lambda e: (-(cuota[e] - base[e]), e))[: n - sum(base.values())]:
        base[e] += 1
    out: list[str] = []
    for e in sorted(por):
        out += rng.sample(por[e], min(base[e], len(por[e])))
    return sorted(out)


def territorios(raiz, ctx) -> dict:
    """Los territorios de la matriz, cada uno {etiqueta, lugar (el objeto «lugar» de la consulta), ubigeo, grupo, nucleo, elegir}.
    `grupo`: nacional | departamento | ambito | provincia | distrito. `nucleo`: va con los cuatro periodos."""
    par = parametros(raiz)
    rng = random.Random(par["semilla"])
    v = _vigentes(ctx)
    nombre = {str(r.ubigeo_inei): str(r.nombre_mostrado) for r in v.itertuples()}
    out: list[dict] = [{"etiqueta": "Perú", "lugar": {"nacional": True}, "ubigeo": None, "grupo": "nacional", "nucleo": True}]
    deptos = sorted(u for u in nombre if u.endswith("0000") and u not in ("000000", "070000", "150000"))
    out += [{"etiqueta": nombre[u], "lugar": {"ubigeo": u[:2]}, "ubigeo": u, "grupo": "departamento", "nucleo": i % 4 == 0}
            for i, u in enumerate(deptos)]
    out += [{"etiqueta": a, "lugar": {"ambito": a}, "ubigeo": None, "grupo": "ambito", "nucleo": True} for a in AMBITOS_LIMA]
    dist = v[v.nivel == "distrito"]
    # provincias: `provincias_por_departamento` por departamento (sin Lima: sus ámbitos ya están), al azar con la semilla
    provs = sorted(u for u in nombre if u.endswith("00") and not u.endswith("0000") and u[:2] not in ("07", "15"))
    for d in deptos:
        cand = [u for u in provs if u[:2] == d[:2]]
        for u in sorted(rng.sample(cand, min(par["provincias_por_departamento"], len(cand)))):
            out.append({"etiqueta": f"{nombre[u]} (provincia, {nombre[d]})", "lugar": {"ubigeo": u[:4]}, "ubigeo": u,
                        "grupo": "provincia", "nucleo": False})
    # distritos: muestra estratificada por región natural + los obligatorios
    datos = datos_s1_00(raiz)
    nm = [x["ubigeo"] for x in _yaml(raiz, "curados/capa0/nombres_mostrados.yaml")["correcciones"]]
    sin_sien = [u for u, _ in datos["sin_sien"]][: par["distritos_sin_sien"]]
    obligatorios = list(dict.fromkeys(nm + [Q2, Q3, ALTO_TRUJILLO, SANGANI] + sin_sien))
    pool = [(str(r.ubigeo_inei), str(r.region_natural_ref)) for r in dist.itertuples() if str(r.ubigeo_inei) not in obligatorios]
    muestra = _estratificar(pool, par["distritos_muestra"], rng)
    notas = {Q2: "Q2", Q3: "Q3", ALTO_TRUJILLO: "Alto Trujillo", SANGANI: "Sangani (pendiente)"}
    for u in obligatorios + muestra:
        if u not in nombre:
            continue
        etiqueta = f"{nombre[u]} (distrito, {nombre.get(u[:4] + '00', '?')})"
        extra = notas.get(u) or ("nombre corregido (T-02)" if u in nm else "sin establecimientos SIEN" if u in sin_sien else None)
        out.append({"etiqueta": etiqueta, "lugar": {"ubigeo": u}, "ubigeo": u, "grupo": "distrito", "nucleo": u in obligatorios,
                    "nota": extra})
    # homónimos: se escriben como texto y se resuelven con --elegir (la opción cambia de un homónimo a otro)
    for i, h in enumerate(datos["homonimos"][: par["homonimos"]]):
        n = len(h["opciones"])
        out.append({"etiqueta": f"{h['texto']} (homónimo, opción {(i % n) + 1} de {n})", "lugar": {"texto": h["texto"]},
                    "ubigeo": h["opciones"][i % n][0], "grupo": "distrito", "nucleo": True, "elegir": (i % n) + 1, "nota": "homónimo"})
    return {"lista": out, "nombre": nombre}


# ----------------------------------------------------------------------------------------------------- periodos

def anios_del_tema(ctx, tema: str) -> list[int]:
    return sorted({int(a) for i in ctx.indicadores.values() if i.get("tema") == tema for a in i["anios_disponibles"]})


def periodo(ctx, tema: str, clase: str) -> dict:
    a = anios_del_tema(ctx, tema)
    if clase == "ultimo":
        return {"tipo": "ultimo"}
    if clase == "intermedio":
        return {"tipo": "anio", "anio": a[len(a) // 2]}
    if clase == "sin_datos":
        return {"tipo": "anio", "anio": a[-1] + 1}          # un año posterior a todo lo que el cubo tiene del tema
    return {"tipo": "serie"}


# ----------------------------------------------------------------------------------------------------- casos

def _caso(tema, intencion, terr, clase, cm, elegir=None, espera=None) -> dict:
    return {"id": f"{tema}|{intencion}|{terr['etiqueta']}|{clase}" + (f"|{cm['territorio'].get('nivel')}" if intencion == "identificar_extremo" else ""),
            "tema": tema, "intencion": intencion, "lugar": terr["etiqueta"], "grupo": terr["grupo"], "periodo": clase,
            "ubigeo": terr.get("ubigeo"), "elegir": elegir, "espera": espera, "consulta": cm}


def casos(raiz, ctx) -> list[dict]:
    """Todos los casos de la matriz completa, en orden fijo. Cada uno: id, tema, intencion, lugar, grupo, periodo (clase),
    consulta (mínima), elegir y `espera` (None | "no_se_puede" | "aclaracion")."""
    temas, intenciones = temas_e_intenciones(raiz)
    T = territorios(raiz, ctx)["lista"]
    out: list[dict] = []
    pregunta = "pregunta de la matriz de cobertura"
    por_grupo: dict[str, list[dict]] = {}
    for t in T:
        por_grupo.setdefault(t["grupo"], []).append(t)
    comparables = {g: [t for t in lista if "elegir" not in t] for g, lista in por_grupo.items()}

    def otro(t):
        """El territorio con el que se compara: el siguiente de su grupo (el primer departamento si es el país)."""
        g = comparables["departamento" if t["grupo"] == "nacional" else t["grupo"]]
        i = next((k for k, x in enumerate(g) if x["etiqueta"] == t["etiqueta"]), -1)
        return g[(i + 1) % len(g)]

    for tema in temas:
        for t in T:
            clases = PERIODOS if t["nucleo"] else ["ultimo"]
            for intencion in intenciones:
                for clase in clases:
                    cm = {"intencion": intencion, "tema": tema, "periodo": periodo(ctx, tema, clase), "pregunta_original": pregunta}
                    if intencion == "identificar_extremo":
                        if t["grupo"] in ("provincia", "distrito"):
                            continue                                         # «el más X dentro de un distrito» no es una pregunta
                        for nivel in NIVELES_EXTREMO:
                            c = {**cm, "territorio": {"nivel": nivel, "dentro_de": t["lugar"]}}
                            out.append(_caso(tema, intencion, t, clase, c))
                        continue
                    cm["territorio"] = t["lugar"]
                    if intencion == "comparacion":
                        cm["comparar_con"] = otro(t)["lugar"]
                    sin_datos = clase == "sin_datos" and intencion != "evolucion"            # el año pedido no está en el cubo
                    sin_sien = (t.get("nota") == "sin establecimientos SIEN" and tema == "anemia"      # el SIEN no tiene ni una fila
                                and intencion == "nivel_actual" and clase == "ultimo")
                    out.append(_caso(tema, intencion, t, clase, cm, elegir=t.get("elegir"),
                                     espera="no_se_puede" if sin_datos or sin_sien else None))
    # aclaraciones esperadas (T-03 y R-TERRITORIO-09)
    for texto in ("Lima", "Huancavelica"):
        t = {"etiqueta": texto + " (a secas)", "lugar": {"texto": texto}, "ubigeo": None, "grupo": "aclaracion"}
        out.append(_caso("anemia", "nivel_actual", t, "ultimo",
                         {"intencion": "nivel_actual", "tema": "anemia", "territorio": t["lugar"], "periodo": {"tipo": "ultimo"},
                          "pregunta_original": pregunta}, espera="aclaracion"))
    ids = [c["id"] for c in out]
    assert len(ids) == len(set(ids)), "ids de caso repetidos"
    return out


def reducida(todos: list[dict], n: int, semilla: int) -> list[dict]:
    """La versión de pytest: `n` casos fijos. Primero un caso por (tema, intención), por (periodo, grupo de territorio) y por clase de
    resultado esperado/homónimo —para que cada combinación esté probada— y el resto al azar con la semilla. Misma entrada y semilla → mismos casos."""
    rng = random.Random(semilla)
    ordenados = sorted(todos, key=lambda c: c["id"])
    claves = (lambda c: ("tema", c["tema"], c["intencion"]), lambda c: ("periodo", c["periodo"], c["grupo"]),
              lambda c: ("espera", c["espera"], c["elegir"] is not None))
    vistos, elegidos = set(), []
    for c in rng.sample(ordenados, len(ordenados)):
        nuevas = [k(c) for k in claves if k(c) not in vistos]
        if nuevas:
            vistos.update(nuevas)
            elegidos.append(c)
    en = {c["id"] for c in elegidos}
    for c in rng.sample(ordenados, len(ordenados)):
        if len(elegidos) >= n:
            break
        if c["id"] not in en:
            en.add(c["id"])
            elegidos.append(c)
    return sorted(elegidos[:n], key=lambda c: c["id"])
