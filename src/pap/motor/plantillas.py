"""Plantillas por intención (S1-04; sin LLM, decisión del 10/10/2026).

Cinco plantillas genéricas (`nivel_actual`, `evolucion`, `comparacion`, `identificar_extremo`, `cruce_efecto`) que reciben
el plan de S1-03 y devuelven el borrador de la respuesta (`corta`, `clave`, `ojo`, `contexto`, `cifras_usadas`…). Eligen
las cifras por indicador, rol y territorio (nunca por id ni por nombre de lugar) y deciden qué oraciones van según la salida
del validador (estado, semáforo, comparaciones bloqueadas). Ninguna decide una regla.

Todo texto que producen sale de `curados/motor/textos/`: `plantillas/<intención>.yaml` (lo propio de la intención),
`plantillas/comunes.yaml` y `bloques.yaml` (piezas de un tema, activadas por lo que trae el plan). El código solo une
esos textos y rellena variables ({lugar}, {anio}…). Los números van siempre por marcadores: {{c:id}} cifra, {{v:id}} verbo de
cambio según la prueba, {{u:id}} universo, {{e:id}} entidad o lista, {{p:id}} texto fijo protegido (frases estándar y
avisos). R-LENGUAJE-02/03/06 validan el texto con marcadores; `rellenar` pone los valores al final.

Los nombres de las plantillas de las preguntas piloto (q1_evolucion…) se traducen a su plantilla genérica con la tabla
`plantillas.nombres_antiguos` de parametros_motor.yaml (para que los q*.yaml archivados en tests/fixtures/consultas_piloto/ sigan funcionando).
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from . import formato as fmt

RUTA_TEXTOS = Path("curados/motor/textos")
RUTA_PARAMETROS = Path("curados/motor/parametros_motor.yaml")
NIVELES_LOCALES = ("distrito", "provincia")      # por debajo del departamento (o del ámbito de Lima)
NIVELES_FINOS = ("distrito", "provincia", "establecimiento")


# ======================================================================= tablas

@lru_cache(maxsize=None)
def _yaml(raiz: str, ruta: str) -> dict:
    return yaml.safe_load((Path(raiz) / ruta).read_text(encoding="utf-8")) or {}


def textos(raiz, nombre: str) -> dict:
    return _yaml(str(raiz), str(RUTA_TEXTOS / nombre))


def parametros(raiz) -> dict:
    return _yaml(str(raiz), str(RUTA_PARAMETROS))


# S1-15 (N-3): clase de nivel para unir los lugares de una comparación en un solo «No permite concluir»: los niveles del
# ubigeo son cada uno su clase; los ámbitos (cualquier otro nivel, p. ej. los de Lima, T-03) son una sola
_NIVELES_UBIGEO = ("nacional", "departamento", "provincia", "distrito")


def _clase_nivel(nivel: str) -> str:
    return nivel if nivel in _NIVELES_UBIGEO else "ambito"

# ======================================================================= estado de las cifras (salida del validador)

def _publicable(c) -> bool:
    return c is not None and c.estado_cifra not in ("suprimida", "sin_datos")


REGLAS_COMPARACION = {"R-ENC-11", "R-ENC-13", "R-ENC-14", "R-CRUCES-04", "R-REG-10", "R-GASTO-09", "R-GASTO-12"}


def _bloqueada(c) -> bool:
    """La comparación de la cifra quedó bloqueada: por las reglas de series de la propia cifra (etapa 5) o por R-ENC-11
    en la respuesta (el motor marca `comparacion_bloqueada` en la segunda pasada)."""
    ev = c.evaluacion
    if ev is None or c.comparacion_bloqueada:
        return True
    return any(r.regla in REGLAS_COMPARACION for r in ev.bloqueos_cruce)


def verbo(c) -> str | None:
    """Verbo de cambio (R-ENC-11): solo si hay comparación no bloqueada y prueba del motor."""
    comp = c.comparacion
    if not comp or not comp.get("prueba_cambio") or _bloqueada(c):
        return None
    pc = comp["prueba_cambio"]
    if not pc["significativa"]:
        return "se mantuvo sin cambio estadísticamente claro"
    return "bajó de forma estadísticamente clara" if pc["diferencia"] < 0 else "subió de forma estadísticamente clara"


def _sin_cambio(c) -> bool:
    return _publicable(c) and bool(verbo(c)) and not c.comparacion["prueba_cambio"]["significativa"]


def _anios_comp(c) -> tuple[int, int]:
    return int(c.comparacion["anio"]), int(c.anio)


def expandir_grupo(motor, g: dict, consulta: dict) -> list[dict]:
    """Cifras en lote: distritos de un grupo robusto del Mapa o unidades del ranking departamental (L8). El indicador del
    Mapa es el único del cubo con grupo robusto por distrito y su año es el último disponible (R-MOTOR-03)."""
    cubo = motor.ctx.cubo
    if g["tipo"] == "mapa_grupo_robusto":
        con_grupo = cubo[(cubo.nivel == "distrito") & cubo.grupo_robusto_nacional.notna()]
        ind = g.get("indicador") or str(con_grupo.indicador_id.iloc[0])
        anio = motor.anio(ind, g.get("anio"))
        x = cubo[(cubo.indicador_id == ind) & (cubo.nivel == "distrito") & (cubo.anio == anio)
                 & (cubo.grupo_robusto_nacional == int(g["grupo"]))].sort_values("territorio_id")
        return [{"id": f"{g.get('prefijo', 'mapa')}_{t}", "indicador": ind, "anio": anio, "nivel": "distrito",
                 "territorio": t, "rol": g.get("rol", "principal")} for t in x.territorio_id]
    if g["tipo"] == "ranking_departamental":
        u = motor.ctx.param("R-ENC-12", "unidades_ranking_departamental") or {}
        out = []
        for un in u.get("unidades") or []:      # un departamento (2 dígitos) o un ámbito de Lima (T-03: su id es su nivel)
            depto = str(un).isdigit()
            nivel, terr = ("departamento", str(un)[:2]) if depto else (str(un), str(un))
            out.append({"id": f"{g['prefijo']}_{terr}", "indicador": g["indicador"], "anio": g.get("anio"),
                        "nivel": nivel, "territorio": terr, "rol": g.get("rol", "contexto"), "nivel_pedido": nivel})
        return out
    raise ValueError(g["tipo"])


# ======================================================================= armado del borrador

_VAR = re.compile(r"(?<!\{)\{([a-z_0-9]+)\}(?!\})")
_MARCADOR = re.compile(r"\{\{([up]):([^}]+)\}\}")


def _sub(texto, v: dict):
    """Rellena {variables}; deja los marcadores {{…}} tal cual. Una cadena que es solo `{x}` devuelve el valor tal cual."""
    if not isinstance(texto, str):
        return texto
    m = re.fullmatch(r"\{([a-z_0-9]+)\}", texto)
    if m:
        return v[m.group(1)]
    return _VAR.sub(lambda m: str(v[m.group(1)]), texto)


def _lugar(c) -> str:
    """Nombre mostrado (T-02) sin el rótulo entre paréntesis («Lima Metropolitana (provincia de Lima)» → «Lima Metropolitana»)."""
    return re.sub(r"\s*\([^)]*\)", "", str(c.territorio_nombre)).strip()


class _Plantilla:
    """Estado de una respuesta en armado: lee los textos, activa los bloques del plan y acumula el borrador."""

    def __init__(self, motor, consulta: dict, cifras: dict, nombre: str):
        self.m, self.q, self.cf, self.nombre = motor, consulta, cifras, nombre
        raiz = motor.ctx.raiz
        self.c = textos(raiz, "plantillas/comunes.yaml")
        self.i = textos(raiz, f"plantillas/{nombre}.yaml")
        self.na = textos(raiz, "plantillas/nivel_actual.yaml")
        self.bl = textos(raiz, "bloques.yaml")
        self.par = parametros(raiz)
        self.sec_nombre = "cruce_efecto" if nombre == "cruce_efecto" else nombre
        self.activos_d = {n: b for n, b in self.bl["bloques"].items() if self._cuando(b["cuando"])}
        self.activos = list(self.activos_d.values())
        self.corta, self.ojo, self.ctxs, self.usadas = [], [], [], []
        self.v, self.u, self.p, self.e = {}, {}, {}, {}
        self.nc, self.expl = [], {}
        self.umbral = motor.ctx.param("R-REG-07", "sien_umbral_tamizaje_pct")
        self.prot = dict(self.c.get("protegidos") or {})
        self.prot.update(self.i.get("protegidos") or {})
        if consulta.get("intencion") in self.i and isinstance(self.i[consulta["intencion"]], dict):
            self.prot.update(self.i[consulta["intencion"]].get("protegidos") or {})
        for b in self.activos:
            self.prot.update(b.get("protegidos") or {})
            self.prot.update((b.get(self.sec_nombre) or {}).get("protegidos") or {})

    # ------------------------------------------------------------------ plan y cifras
    def _cuando(self, q: dict) -> bool:
        plan, cf = self.q, self.cf.values()
        if "plan_bloques" in q and not set(q["plan_bloques"]) & set(plan.get("bloques") or []):
            return False
        if "grupos_estadisticos" in q and plan.get("grupos_estadisticos") not in q["grupos_estadisticos"]:
            return False
        if "cruce" in q and plan.get("cruce") not in q["cruce"]:
            return False
        if "indicador" in q and not any(c.indicador_id in q["indicador"] and ("rol" not in q or c.rol == q["rol"]) for c in cf):
            return False
        if "nivel" in q and not any(c.nivel in q["nivel"] for c in cf):
            return False
        return True

    def por(self, indicador=None, rol=None, medida=None, no_indicador=()) -> list[tuple[str, object]]:
        return [(i, c) for i, c in self.cf.items()
                if (indicador is None or c.indicador_id == indicador) and (rol is None or c.rol == rol)
                and (medida is None or c.medida == medida) and c.indicador_id not in no_indicador]

    def sec(self, clave: str):
        """La clave de la sección de la intención en el primer bloque activo que la trae."""
        for b in self.activos:
            s = (b.get(self.sec_nombre) or {})
            if clave in s:
                return s[clave]
        return None

    def secs(self, clave: str) -> list:
        """La clave de la sección de la intención en todos los bloques activos que la traen, en orden."""
        return [b[self.sec_nombre][clave] for b in self.activos if clave in (b.get(self.sec_nombre) or {})]

    def lugar_ficha(self, c) -> str:
        """El lugar como se dice en la línea «Territorio» de la ficha: «departamento de Cusco», «Lima Metropolitana», «todo el país»."""
        t = self.c["lugar_ficha"]
        return _sub(t.get(c.nivel, t["defecto"]), {"lugar": _lugar(c)})

    def bloque(self, nombre: str):
        """El bloque `nombre` de bloques.yaml si el plan lo activa."""
        return self.activos_d.get(nombre)

    def indic(self, c) -> dict:
        return self.bl["indicadores"].get(c.indicador_id) or {}

    # ------------------------------------------------------------------ variables de una cifra
    def vars_cifra(self, c, prefijo: str = "", i: str | None = None) -> dict:
        com = self.c
        nivel = c.nivel if c.nivel in com["nivel_del"] else None
        nom = str(self.indic(c).get("ciudadano") or c.nombre_ciudadano or "")
        lugar = (self.q.get("desambiguados") or {}).get(f"{c.nivel}:{c.territorio_id}") or _lugar(c)    # S1-09 (H4): homónimo aclarado
        largo = self.m.nombre_completo(c.territorio_id) if c.nivel == "distrito" else str(c.territorio_nombre)
        fuente = com["fuentes"].get(c.fuente_principal, com["fuentes"]["defecto"])
        d = {"lugar": lugar, "lugar_completo": str(c.territorio_nombre), "lugar_largo": largo, "anio": int(c.anio),
             "ciudadano": nom[:1].lower() + nom[1:], "ciudadano_cap": nom[:1].upper() + nom[1:],
             "sujeto": self.indic(c).get("sujeto") or (nom[:1].lower() + nom[1:]),
             "sujeto_corto": self.indic(c).get("sujeto_corto") or (nom[:1].lower() + nom[1:]),
             "nivel_del": com["nivel_del"].get(nivel, ""), "nivel_en": com["nivel_en"].get(nivel, ""),
             "nivel_palabra": com["nivel_palabra"].get(nivel, str(c.nivel)),
             "nivel_plural": com["nivel_plural"].get(nivel, com["nivel_plural"]["defecto"]),
             "fuente": _sub(fuente, {"anio": int(c.anio), "fuente_principal": c.fuente_principal})}
        if i is not None and c.get("denominador") is not None:      # conteo de un registro («52 de 547»); un marcador por cifra
            d["n"] = self.ent(f"n_{i}", fmt._num(float(c.get("denominador")), 0))
            if c.get("numerador") is not None:
                d["n_con"] = self.ent(f"n_con_{i}", fmt._num(float(c.get("numerador")), 0))
        return {prefijo + k: v for k, v in d.items()}

    def vars_region(self, r) -> dict:
        """Cómo se nombra el territorio de una cifra de contexto más amplio (departamento o ámbito de Lima)."""
        k = "departamento" if r.nivel == "departamento" else "otro"
        lugar = _lugar(r)
        return {"lugar_region": lugar, "region_art": self.c["region_art"][k].format(lugar=lugar),
                "region_de": self.c["region_de"][k].format(lugar=lugar), "region_gen": self.c["region_gen"][k].format(lugar=lugar),
                "nivel_regional": r.nivel}

    # ------------------------------------------------------------------ marcadores
    def cm(self, i: str) -> str:
        return "{{c:%s}}" % i

    def ent(self, nombre: str, valor) -> str:
        self.e[nombre] = valor
        return "{{e:%s}}" % nombre

    def vb(self, i: str) -> str:
        self.v[i] = verbo(self.cf[i])
        return "{{v:%s}}" % i

    def _proteg(self, nombre: str, v: dict) -> str:
        spec = self.prot[nombre]
        if spec.startswith("@frase:"):
            f = self.m.ctx.lenguaje["frases_estandar"][spec[len("@frase:"):]]
            return f.replace("{año}", str(v.get("anio", "")))
        return _sub(spec, v)

    def t(self, texto: str, **v) -> str:
        """Rellena las variables y registra los universos {{u:…}} y textos protegidos {{p:…}} que el texto usa."""
        out = _sub(texto, v)
        for tipo, nombre in _MARCADOR.findall(out):
            if tipo == "u" and nombre not in self.u:
                self.u[nombre] = _sub(self.c["universos"][nombre], v)
            if tipo == "p" and nombre not in self.p:
                self.p[nombre] = self._proteg(nombre, v)
        return out

    def valores(self, base: dict, *extra: dict, **v) -> dict:
        out = dict(base)
        for x in extra:
            out.update(x)
        out.update(v)
        return out

    # ------------------------------------------------------------------ piezas comunes
    def lista(self, xs: list[str]) -> str:
        y = self.c["conjuncion"]
        return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + f" {y} " + xs[-1]

    def numero(self, n: int) -> str:
        return self.c["numeros"].get(n, self.c["varios"])

    def umbral_txt(self) -> str:
        pal = self.c["umbral_en_palabras"]
        return pal.get(int(self.umbral), _sub(pal["defecto"], {"umbral": int(self.umbral)})) if self.umbral is not None else ""

    def aviso_cobertura(self, c, **v) -> str:
        """R-REG-07 y rótulos de sien_cobertura_tamizaje_6_35m (P4-03): qué se puede decir frente al umbral de tamizaje."""
        av = self.bloque("cobertura_sien")["avisos"]
        v = {**v, "umbral_txt": self.umbral_txt()}
        if c.cota_sup < self.umbral:
            return _sub(av["menos_del_umbral"], v)
        if c.cota_inf < self.umbral:
            return _sub(av["incierto"], v)
        if c.cota_inf - self.umbral < 1:
            return _sub(av["apenas"], v)
        return _sub(av["mas_del_umbral"], v)

    def tarjeta_generica(self, c, i: str, etiqueta: str | None = None, **v) -> dict:
        """Una cifra de contexto sin pieza propia del tema: nombre del indicador, lugar, año y cifra."""
        tp = self.na
        vv = self.valores(self.vars_cifra(c), v, c=self.cm(i))
        forma = tp["tarjeta"]["proporcion" if c.medida == "proporcion" else "defecto"]
        self.usadas.append(i)
        return {"titulo": _sub(tp["tarjeta"]["titulo"], vv), "texto": self.t(forma, **vv),
                "etiqueta": etiqueta if etiqueta is not None else self.c["no_se_compara"]}

    def clave_generica(self, i: str, c, plantilla: dict) -> dict:
        vv = self.vars_cifra(c)
        self.usadas.append(i)
        forma = plantilla["clave"]["proporcion" if c.medida == "proporcion" else "defecto"]
        return {"ids": [i], "valor": self.cm(i), "texto": self.t(forma, **vv)}

    def ojo_generico(self, c) -> str:
        og = self.c["ojo_generico"]
        return og.get(c.naturaleza_dato, og["otro"])

    def nc_asignados(self) -> list[tuple[str, dict]]:
        """Los códigos «no permite concluir» (R-LENGUAJE-01, sección 7 de la ficha) que se desprenden de las cifras usadas,
        según `plantillas.nc_asignacion` de parametros_motor.yaml (la regla de asignación es la de reglas.json: la plantilla
        solo la aplica a lo que ya dijo el validador, no decide nada)."""
        usadas = [self.cf[i] for i in dict.fromkeys(self.usadas)]
        out = []
        for cod, cond in self.par["plantillas"]["nc_asignacion"]["valor"].items():
            if "intencion" in cond and self.q.get("intencion") not in cond["intencion"]:
                continue
            base = [c for c in usadas if c.rol == "principal"]
            if "fuente" in cond:
                if any(c.fuente_principal in cond["fuente"] for c in base):
                    out.append((cod, {}))
            elif "naturaleza" in cond:
                if any(c.naturaleza_dato in cond["naturaleza"] for c in usadas):
                    out.append((cod, {}))
            elif "vigencia_min" in cond:
                viejas = [c for c in base if any(m.get("criterio") == "vigencia" and m.get("puntaje", 0) >= cond["vigencia_min"]
                                                 for m in c.get("motivos_semaforo") or [])]
                if viejas:
                    anio = int(viejas[0].anio)
                    choque = any(anio < a <= self.m.ctx.anio_actual for a in self.m.ctx.param("R-LENGUAJE-04", "anios_choque") or [])
                    out.append((cod, {"anio_dato": anio, "choque": choque}))
            elif "cifras_min" in cond:
                if len(base) >= cond["cifras_min"]:
                    out.append((cod, {}))
        return out

    def nc_respaldo(self) -> list[list]:
        """`plantillas.nc_respaldo` de parametros_motor.yaml (R-LENGUAJE-01, C-04): si ninguna cifra dio un código, una
        cifra principal de la naturaleza y el nivel indicados lleva ese código, con el nivel en palabras."""
        cond = self.par["plantillas"]["nc_respaldo"]["valor"]
        lugares = []                       # (clase de nivel, nivel en palabras) de cada cifra principal que lleva el código
        for i in dict.fromkeys(self.usadas):
            c = self.cf[i]
            if c.rol == "principal" and c.naturaleza_dato in cond["naturaleza"] and c.nivel in cond["niveles"]:
                lugar = (_clase_nivel(c.nivel), cond["niveles"][c.nivel])
                if lugar not in lugares:
                    lugares.append(lugar)
            if lugares and self.q.get("intencion") != "comparacion":
                break                          # fuera de una comparación, como antes: la primera cifra principal
        if not lugares:
            return []
        # S1-15 (N-3): en una comparación, los dos lugares; del mismo nivel, unidos con « y »; de niveles distintos, uno por lugar
        if len({k for k, _ in lugares}) == 1:
            return [[cond["codigo"], {"nivel_publicado": " y ".join(t for _, t in lugares)}]]
        return [[cond["codigo"], {"nivel_publicado": t, "_por_lugar": True}] for _, t in lugares]

    def cierre(self, *, clave: dict, tema, nivel_respuesta=None, territorio_nombre="", territorio_ficha=None,
               motivo_confianza=None, alcance=None, cruces=None, glosario_extra=()) -> dict:
        lim = self.par["respuesta"]["ojo_al_leer"]
        ojo = self.ojo[: lim["max"]]
        glos = []
        for b in self.activos:
            glos += b.get("glosario") or []
        for i in dict.fromkeys(self.usadas):
            glos += self.indic(self.cf[i]).get("glosario") or []
        glos += list(glosario_extra)
        if any(self.v.values()):
            glos.append("cambio_claro")
        nc = []
        for cod, prm in self.nc_asignados():
            nc.append([cod, prm])
        for b in self.activos:
            nc += [[n, {k: _sub(x, self._nc_vars) for k, x in prm.items()}]
                   for n, prm in (b.get("nc") or []) + ((b.get(self.sec_nombre) or {}).get("nc") or [])]
        nc += [[n, {k: _sub(x, self._nc_vars) for k, x in prm.items()}] for n, prm in self.nc]
        if not nc:  # C-04 (dueño, 3/11/2026): código de respaldo solo cuando ningún otro aplica
            nc += self.nc_respaldo()
        pend = self.par["pendientes_dueno"]
        d = {"corta": self.corta, "clave": clave, "ojo": ojo, "contexto": self.ctxs,
             "cifras_usadas": list(dict.fromkeys(self.usadas)), "verbos": {k: x for k, x in self.v.items() if x},
             "universos": self.u, "protegidos": self.p, "entidades": self.e, "glosario": list(dict.fromkeys(glos)),
             "tema": tema, "nc": list({(n, prm["nivel_publicado"]) if prm.get("_por_lugar") else n: (n, prm)   # N-3: uno por lugar
                                       for n, prm in reversed(nc)}.values())[::-1], "nivel_respuesta": nivel_respuesta,
             "territorio_nombre": territorio_nombre, "respuesta_parcial": bool(self.q.get("respuesta_parcial")),
             "opciones": {"intervalo_visible": pend["intervalo_visible"]["valor"], "umbral_tamizaje": self.umbral}}
        if territorio_ficha:
            d["territorio_ficha"] = territorio_ficha
        if motivo_confianza:
            d["motivo_confianza"] = motivo_confianza
        if alcance:
            d["alcance"] = alcance
        if cruces:
            d["cruces"] = cruces
        if self.expl:
            d["explicaciones"] = self.expl
        return _armar(d)

    _nc_vars: dict = {}


def _armar(d: dict) -> dict:
    cl = d["clave"]
    partes = list(d["corta"]) + [" ".join(x for x in (cl.get("valor"), cl.get("texto")) if x)] + list(d["ojo"]) \
        + [t["texto"] for t in d["contexto"]]
    d["texto"] = " ".join(p for p in partes if p)
    return d


def _principal_publicable(P: _Plantilla):
    """(id, cifra) principal que da el nivel y el territorio de la respuesta: la primera publicable; si no hay, la primera cifra."""
    cand = P.por(rol="principal") or list(P.cf.items())
    return next(((i, c) for i, c in cand if _publicable(c)), cand[0] if cand else (None, None))


def _nivel_respuesta(P: _Plantilla, c0):
    if c0 is not None and _publicable(c0):
        return c0.nivel
    return next((c.nivel for c in P.cf.values() if _publicable(c)), c0.nivel if c0 is not None else None)


# ======================================================================= nivel_actual

def nivel_actual(P: _Plantilla) -> dict:
    """«¿Cuánto hay?»: la cifra principal del lugar como cifra clave y, en tarjetas, las cifras de contexto. Si el plan activa
    el bloque del SIEN (registro de niños medidos, S-01), usa su redacción: lo que no se puede saber va primero (R-04)."""
    tp = P.na
    prin = P.por(rol="principal")
    ctx = [(i, c) for i, c in P.cf.items() if c.rol != "principal"]
    s_id, s = _principal_publicable(P)
    pub = _publicable(s)
    clave = {"ids": [], "valor": "", "texto": ""}
    vs = P.vars_cifra(s, i=s_id) if s is not None else {}
    bloque = P.sec("corta") is not None
    regionales = [(i, c) for i, c in ctx if c.medida != "cobertura" and c.nivel not in NIVELES_FINOS]
    cobs = [(i, c) for i, c in ctx if c.medida == "cobertura"]
    reg_c = (regionales or cobs or [(None, None)])[0][1]
    vr = P.vars_region(reg_c) if reg_c is not None else {}
    vs = {**vs, **vr}
    gastadas: set = set()
    if bloque:
        if pub:
            P.usadas.append(s_id)
            P.corta += [P.t(x, **vs) for x in P.sec("corta")]
            clave = {"ids": [s_id], "valor": P.cm(s_id), "texto": P.t(P.sec("clave"), **vs)}
            P.ojo += [P.t(x, **vs) for x in P.sec("ojo")]
        else:
            P.corta += [P.t(x, **vs) for x in P.sec("corta_sin_cifra")]
            P.nc += [[n, prm] for n, prm in P.sec("sin_cifra_nc") or []]
        P._nc_vars = vs
        if pub and P.par["pendientes_dueno"]["mostrar_conteo_sien"]["valor"] and s.get("numerador") is not None:
            tc = P.sec("tarjeta_conteo")                     # X-02: el conteo («52 de 547») como tarjeta de la capa 2
            P.ctxs.append({"titulo": tc["titulo"], "texto": P.t(tc["texto"], **vs), "etiqueta": None})
        for i, c in regionales:
            if not _publicable(c):
                continue
            vc = P.valores(P.vars_cifra(c), vr, c=P.cm(i), lugar_largo=vs["lugar_largo"])
            P.usadas.append(i)
            P.ojo.append(P.t(P.sec("ojo_region"), **vc))
            tr = P.sec("tarjeta_region")
            P.ctxs.append({"titulo": _sub(tr["titulo"], vc), "texto": P.t(tr["texto"], **vc), "etiqueta": P.c["no_se_compara"]})
            gastadas.add(i)
        for i, c in cobs:
            if not _publicable(c):
                continue
            vc = P.valores(P.vars_cifra(c), vr, c=P.cm(i))
            P.usadas.append(i)
            P.p["cobertura"] = P.aviso_cobertura(c, lugar=vc["lugar"])
            tc = P.sec("tarjeta_cobertura")
            P.ctxs.append({"titulo": tc["titulo"], "texto": P.t(tc["texto"], **vc), "etiqueta": None})
            gastadas.add(i)
        if pub:
            tq = P.sec("tarjeta_porque")
            P.ctxs.append({"titulo": tq["titulo"], "texto": P.t(tq["texto"], **vs), "etiqueta": None})
        ex = P.sec("explicaciones")
        if ex:
            P.expl = {k: _sub(x, vs) for k, x in ex.items()}
    elif s is not None and P.sec("gasto") is not None:        # S1-09 (H5): el gasto sin jerga y con su alcance
        clave = _gasto_nivel_actual(P, s_id, s, vs) or clave
    else:
        if s is not None:
            P.corta.append(P.t(tp["corta"], **vs))
            if pub:
                clave = P.clave_generica(s_id, s, tp)
                P.ojo.append(P.ojo_generico(s))
    for i, c in ctx + prin[1:]:
        if i not in gastadas and i != s_id and _publicable(c):
            P.ctxs.append(P.tarjeta_generica(c, i))
    nivel = _nivel_respuesta(P, s)
    return P.cierre(clave=clave, tema=P.q.get("tema"), nivel_respuesta=nivel,
                    territorio_nombre=_lugar(s) if s is not None else "")


def _gasto_nivel_actual(P: _Plantilla, i: str, c, vs: dict):
    """S1-09 (H5): el gasto de un lugar con su alcance en la capa 1 (lo que registran las entidades con sede allí; en Lima, sin las
    entidades nacionales) y sin «PAN» ni «devengado», que quedan en el glosario. Reutiliza los bloques `gasto` y `sesgo_sede_lima`."""
    g, lima = P.sec("gasto"), P.sec("gasto_lima")
    alcance = "nacional" if c.nivel == "nacional" else "local" if c.nivel in NIVELES_LOCALES else "regional"
    if _publicable(c):                      # S3-01b (u13): qué cubre la cifra y qué no, antes de la cifra (si no hay cifra, «no se puede» va primero)
        P.corta.append(P.t(lima["apertura"] if lima and alcance == "regional" else g["apertura"][alcance], **vs))
    P.corta.append(P.t(P.na["corta"], **vs))
    if not _publicable(c):
        return None
    P.usadas.append(i)
    P.ojo.append(P.ojo_generico(c))
    ref_nac = [x["devengado"] for x in (c.lineas_aparte or []) if x["linea"] == "referencia_nacional"]
    if lima and ref_nac:
        tj = lima["tarjeta"]
        P.ctxs.append({"titulo": tj["titulo"], "texto": P.t(tj["texto"], **P.valores(vs, linea_ref=P.ent("linea_ref", fmt.monto(sum(ref_nac))))),
                       "etiqueta": None})
    return {"ids": [i], "valor": P.cm(i), "texto": P.t(g["clave"][alcance], **vs)}


# ======================================================================= evolucion

def _inicial(P: _Plantilla, c):
    """La cifra del primer año de la serie (el año con el que se compara `c`), si el plan la trae."""
    if not c.comparacion:
        return None, None
    a = int(c.comparacion["anio"])
    return next(((i, x) for i, x in P.cf.items() if x.indicador_id == c.indicador_id and x.nivel == c.nivel
                 and str(x.territorio_id) == str(c.territorio_id) and int(x.anio) == a and x is not c), (None, None))


def evolucion(P: _Plantilla) -> dict:
    """«¿Cómo ha cambiado?»: último año contra el primer año comparable; el verbo lo da la prueba del motor (R-ENC-11)."""
    series = [(i, c) for i, c in P.por(rol="principal") if c.comparacion] or P.por(rol="principal")
    bloque = P.sec("corta_sin_cambio") is not None and len(series) >= 2
    if bloque:
        return _evolucion_dos_formas(P, series)
    tp = P.i
    i0, c0 = series[0] if series else _principal_publicable(P)
    pub = _publicable(c0)
    clave = {"ids": [], "valor": "", "texto": ""}
    vs = P.vars_cifra(c0)
    ini_id, ini = _inicial(P, c0)
    constantes = pub and c0.get("precios") == "constantes"
    if pub:
        clave = P.clave_generica(i0, c0, tp)
        if constantes:                     # S1-16 (M-1): la cifra clave dice que está en soles del año base
            clave["texto"] = P.t(tp["clave"]["constantes"], **P.valores(vs, anio_base=c0.anio_base_deflactor))
    sin_par = c0.get("comparacion_no_publicable") if c0 is not None else None
    if pub and sin_par is None and c0.comparacion and ini is not None and not _publicable(ini) and not verbo(c0):
        sin_par = int(ini.anio)
    if pub and sin_par is not None:        # S1-16 (B-1): el año con el que se compara no se puede publicar; va primero
        P.corta.append(P.t(tp["corta_no_comparable"], **P.valores(vs, a=sin_par)))
    if pub and c0.comparacion:
        a, b = _anios_comp(c0)
        v = verbo(c0)
        if v:
            P.corta.append(P.t(tp["corta_con_verbo"], **P.valores(vs, a=a, b=b, verbo=P.vb(i0))))
        elif constantes and _publicable(ini) and not _bloqueada(c0):          # S1-12: gasto en soles constantes
            P.v[f"{i0}__pasa"] = tp["verbo_pasa"]
            P.v[f"{i0}__sentido"] = tp["sentido_monto"]["sube" if c0.valor > ini.valor else "baja" if c0.valor < ini.valor else "igual"]
            P.corta.append(P.t(tp["corta_soles_constantes"], **P.valores(
                vs, a=a, b=b, c_ini=P.cm(ini_id), c_fin=P.cm(i0), anio_base=c0.anio_base_deflactor,
                pasa="{{v:%s__pasa}}" % i0, sentido="{{v:%s__sentido}}" % i0)))
        elif _publicable(ini) and not _bloqueada(c0):          # S1-09 (A-H1): con la comparación bloqueada nunca «pasó de X a Y»
            P.corta.append(P.t(tp["corta_sin_prueba"], **P.valores(vs, a=a, b=b, c_ini=P.cm(ini_id), c_fin=P.cm(i0))))
        else:
            P.corta.append(P.t(tp["corta_sin_comparacion"], **vs))
    else:
        P.corta.append(P.t(tp["corta_sin_comparacion"], **vs))
    if pub:
        P.ojo.append(P.ojo_generico(c0))
        if _sin_cambio(c0):
            P.ojo.append(P.c["ojo_sin_cambio"])
        sola = P.bloque("forma_anterior_sola")
        if sola and P.sec("ojo_vigente"):  # S1-13 (A-H6): la serie es de la forma anterior; se nombra la vigente
            anios_v = sorted(int(a) for a in P.m.ctx.indicadores[sola["vigente"]]["anios_disponibles"])
            P.ojo.append(P.t(P.sec("ojo_vigente"), **P.valores(vs, anio_vigente=anios_v[0])))
        if constantes:                     # S1-12: el mensaje de R-GASTO-12 prevalece sobre la plantilla (agents.md §3)
            m = next((r.mensaje for r in (c0.evaluacion.resultados if c0.evaluacion else [])
                      if r.regla == "R-GASTO-12" and r.motivo == "soles_constantes" and r.mensaje), None)
            if m:
                P.ojo.append(m)
    gastadas = {i0}
    if pub and _publicable(ini):
        ti = tp["tarjeta_inicial"]
        vi = P.valores(vs, a=int(ini.anio), c_ini=P.cm(ini_id), fuente=P.vars_cifra(ini)["fuente"])
        P.usadas.append(ini_id)
        comparada = bool(c0.comparacion) and int(ini.anio) == int(c0.comparacion["anio"]) and not _bloqueada(c0)
        etiqueta = (_sub(ti["etiqueta_constantes"], {"anio_base": c0.anio_base_deflactor})
                    if constantes and comparada else ti["etiqueta"])
        texto = (P.t(ti["texto_comparada"], **P.valores(vi, b=int(c0.anio), c_fin=P.cm(i0))) if comparada   # AD-1
                 else P.t(ti["texto"], **vi))
        P.ctxs.append({"titulo": _sub(ti["titulo"], vi), "texto": texto, "etiqueta": None if comparada and not constantes else etiqueta})
        gastadas.add(ini_id)
    sola = P.bloque("forma_anterior_sola")
    for i, c in P.cf.items():
        if i not in gastadas and _publicable(c):
            otra_forma = sola and c.indicador_id == sola["vigente"]
            P.ctxs.append(P.tarjeta_generica(c, i, P.sec("etiqueta_vigente") if otra_forma else None))
    return P.cierre(clave=clave, tema=P.q.get("tema"), nivel_respuesta=_nivel_respuesta(P, c0), territorio_nombre=_lugar(c0),
                    glosario_extra=("soles_constantes",) if constantes else ())


def _evolucion_dos_formas(P: _Plantilla, series: list) -> dict:
    """Decisión del dueño (11/10/2026, P4; E-06): las dos formas de medir en paralelo, cada una con su alcance. La serie
    vigente va primero (cifra clave); la anterior, desde su primer año comparable, en el contexto. Sin picos de años
    intermedios (C-01)."""
    (i1, c1), (i2, c2) = series[0], series[1]
    s = P.sec
    ini_id, ini = _inicial(P, c2)
    a1, b1 = _anios_comp(c1)
    a2, b2 = _anios_comp(c2)
    anios = sorted(int(a) for a in P.m.ctx.indicadores[c1.indicador_id]["anios_disponibles"])
    quiebre = next((int(q["anio"]) for q in P.m.ctx.indicadores[c2.indicador_id].get("quiebres") or [] if q["tipo"] == "modo"), None)
    vs = P.valores(P.vars_cifra(c1), a1=a1, b1=b1, a2=a2, b2=b2, anio_vigente=anios[0], anios_vigente=P.lista([str(a) for a in anios]),
                   anio_quiebre=quiebre if quiebre is not None else "")
    P._nc_vars = vs
    v1, v2 = (verbo(c1) if _publicable(c1) else None), (verbo(c2) if _publicable(c2) else None)
    sin_cambio = [x for x in (c1, c2) if _sin_cambio(x)]
    clave = {"ids": [], "valor": "", "texto": ""}
    if _publicable(c1) and _publicable(c2) and len(sin_cambio) == 2:
        P.corta.append(P.t(s("corta_sin_cambio"), **vs))
    else:
        P.corta.append(P.t(s("corta_general"), **vs))
    if _publicable(c1):
        P.usadas.append(i1)
        clave = {"ids": [i1], "valor": P.cm(i1), "texto": P.t(s("clave"), **vs)}
        if v1 and len(sin_cambio) < 2:                     # si las dos series no cambian, la primera oración ya lo dice
            P.corta.append(P.t(s("corta_verbo"), **P.valores(vs, verbo1=P.vb(i1))))
    P.ojo += [P.t(x, **vs) for x in s("ojo")]
    if _publicable(c2):
        ta = s("tarjeta_anterior")
        P.usadas.append(i2)
        vv = P.valores(vs, c_fin=P.cm(i2))
        if _publicable(ini):
            P.usadas.append(ini_id)
            t = P.t(ta["con_inicio"], **P.valores(vv, c_ini=P.cm(ini_id)))
        else:
            t = P.t(ta["sin_inicio"], **vv)
        t += P.t(ta["con_cambio"], **P.valores(vv, verbo2=P.vb(i2))) if v2 else ta["sin_cambio"]
        P.ctxs.append({"titulo": _sub(ta["titulo"], vs), "texto": t, "etiqueta": ta["etiqueta"]})
    tf = s("tarjeta_formas")
    P.ctxs.append({"titulo": tf["titulo"], "texto": P.t(tf["texto"] if quiebre is not None else tf["texto_sin_quiebre"], **vs),
                   "etiqueta": None})
    ini1_id, ini1 = _inicial(P, c1)
    if _publicable(c1) and _publicable(ini1) and s("tarjeta_vigente"):     # AD-1: el año con el que se compara, con su cita
        tv = s("tarjeta_vigente")                                          # (al final: las tarjetas anteriores no cambian)
        P.usadas.append(ini1_id)
        P.ctxs.append({"titulo": _sub(tv["titulo"], vs), "etiqueta": None,
                       "texto": P.t(tv["texto"], **P.valores(vs, c_ini=P.cm(ini1_id), c_fin=P.cm(i1)))})
    return P.cierre(clave=clave, tema=P.q.get("tema"), nivel_respuesta=_nivel_respuesta(P, c1), territorio_nombre=_lugar(c1))


# ======================================================================= comparacion

def _prueba_entre_lugares(P: _Plantilla, a, b) -> dict | None:
    """R-ENC-11 entre dos lugares: la misma prueba que entre años (`Motor.prueba_cambio`, cov = 0). Solo si las dos cifras son de
    una encuesta, del mismo indicador, año y medida, con error estándar, y ninguno de los lugares contiene al otro (con cov ≠ 0
    el motor no estima la covarianza: no hay prueba)."""
    if not (_publicable(a) and _publicable(b)):
        return None                                         # cualquiera suprimida → no comparar
    if (a.indicador_id, int(a.anio), a.medida) != (b.indicador_id, int(b.anio), b.medida) or a.medida != "proporcion":
        return None
    if a.naturaleza_dato != "encuesta_muestral" or a.ee is None or b.ee is None:
        return None
    from .validador.reglas_etapa8_10 import _contiene   # (el mismo criterio de contención que usa el validador)
    if str(a.territorio_id) != str(b.territorio_id) and (_contiene(P.m.ctx, a.territorio_id, b.territorio_id)
                                                          or _contiene(P.m.ctx, b.territorio_id, a.territorio_id)):
        return None
    return P.m.prueba_cambio({"valor": b.valor, "ee": b.ee, "anio": b.anio}, {"valor": a.valor, "ee": a.ee, "anio": a.anio})


def comparacion(P: _Plantilla) -> dict:
    """Dos lugares lado a lado: las dos cifras son las cifras clave. Dice cuál es mayor solo si la prueba de diferencia lo permite
    (R-ENC-11): p < alfa → dirección; p >= alfa → «sin diferencia estadísticamente clara»; sin prueba posible, solo las cifras."""
    tp = P.i
    prin = P.por(rol="principal")
    i0, c0 = _principal_publicable(P)
    otros = [(i, c) for i, c in prin if i != i0]
    ib, cb = otros[0] if otros else (None, None)
    vs = P.vars_cifra(c0)
    vb_ = P.vars_cifra(cb) if cb is not None else {}
    ambas = cb is not None and _publicable(c0) and _publicable(cb)
    pc = _prueba_entre_lugares(P, c0, cb) if ambas else None
    v = P.valores(vs, lugar_b=vb_.get("lugar", ""))
    clave = {"ids": [], "valor": "", "texto": ""}
    glosario_extra = []
    en_clave = {i0}
    if pc is not None and pc["significativa"]:
        mayor, menor = (vs["lugar"], vb_["lugar"]) if pc["diferencia"] > 0 else (vb_["lugar"], vs["lugar"])   # diferencia = primero − segundo
        P.corta.append(P.t(tp["corta_clara"], **P.valores(v, lugar_mayor=mayor, lugar_menor=menor)))
    elif pc is not None:
        P.corta.append(P.t(tp["corta_sin_diferencia"], **v))
    else:
        P.corta.append(P.t(tp["corta"], **v))
    if _publicable(c0):
        if ambas:                                           # las dos cifras en la capa 1
            P.usadas += [i0, ib]
            en_clave.add(ib)
            forma = tp["clave_dos"]["proporcion" if c0.medida == "proporcion" else "defecto"]
            clave = {"ids": [i0, ib], "valor": P.cm(i0), "texto": P.t(forma, **P.valores(v, c_b=P.cm(ib)))}
        else:
            clave = P.clave_generica(i0, c0, tp)
        P.ojo.append(P.ojo_generico(c0))
        if pc is not None and pc["significativa"]:
            P.ojo.append(tp["ojo_clara"])
        elif pc is not None:
            P.ojo.append(tp["ojo_sin_diferencia"])
        elif c0.naturaleza_dato == "encuesta_muestral":
            P.ojo.append(tp["ojo"])
        if pc is not None:
            glosario_extra.append("diferencia_clara")
    if pc is not None:
        P.ctxs.append({"titulo": tp["tarjeta_prueba"]["titulo"], "texto": tp["tarjeta_prueba"]["texto"], "etiqueta": None})
    for i, c in otros + [(i, c) for i, c in P.cf.items() if c.rol != "principal"]:
        if _publicable(c) and i not in en_clave:
            vc = P.valores(P.vars_cifra(c), c=P.cm(i))
            P.usadas.append(i)
            forma = tp["tarjeta"]["proporcion" if c.medida == "proporcion" else "defecto"]
            P.ctxs.append({"titulo": _sub(tp["tarjeta"]["titulo"], vc), "texto": P.t(forma, **vc), "etiqueta": tp["tarjeta"]["etiqueta"]})
    ficha = None
    if cb is not None:
        ficha = _sub(P.c["territorio_dos_lugares"], {"a": P.lugar_ficha(c0), "b": P.lugar_ficha(cb)})   # A-H4: la ficha nombra los dos lugares
    return P.cierre(clave=clave, tema=P.q.get("tema"), nivel_respuesta=_nivel_respuesta(P, c0), territorio_nombre=_lugar(c0),
                    territorio_ficha=ficha, glosario_extra=glosario_extra)


# ======================================================================= identificar_extremo

def _grupo_departamental(P: _Plantilla, dep: list) -> tuple[list[str], dict]:
    """(ids de las cifras del grupo con el valor más alto, datos para el texto): el grupo oficial del INEI si existe
    (R-ENC-12, decisión del dueño 11/10/2026); si no, la prueba contra la más alta (alfa de parametros_globales)."""
    en = dict(dep)
    c0 = next(iter(en.values()))
    oficial = P.m.grupos_oficiales(c0.indicador_id, c0.anio)
    if oficial:
        g1 = [r for r in oficial if int(r["grupo"]) == 1]
        claves = {c.territorio_id: k for k, c in en.items()}
        grupo = [claves[r["territorio"]] for r in g1 if r["territorio"] in claves]
        grupo.sort(key=lambda k: en[k].territorio_nombre)
        rango = fmt.intervalo(float(g1[0]["ic_inf_grupo"]), float(g1[0]["ic_sup_grupo"]), 1)
        return grupo, {"oficial": True, "rango_grupo": P.ent("rango_grupo", rango)}
    top = max(en.values(), key=lambda c: c.valor)
    grupo = []
    for k, c in sorted(en.items(), key=lambda kv: kv[1].territorio_nombre):
        pc = P.m.prueba_cambio({"valor": c.valor, "ee": c.ee, "anio": c.anio}, {"valor": top.valor, "ee": top.ee, "anio": top.anio})
        if c is top or (pc and not pc["significativa"]):
            grupo.append(k)
    return grupo, {"oficial": False}


def identificar_extremo(P: _Plantilla) -> dict:
    """«¿Cuál es el más alto?»: nunca un ranking uno por uno. Un grupo de territorios sin diferencias claras, en orden
    alfabético (R-04, R-ENC-12). Si el plan activa el bloque del Mapa de Pobreza (E-08), dice primero que no se puede
    nombrar un solo distrito y lista el grupo robusto sin cifra puntual."""
    tp = P.i
    pub = {i: c for i, c in P.cf.items() if _publicable(c)}
    mapa = [i for i, c in pub.items() if c.naturaleza_dato == "estimacion_modelada"]
    dep = [(i, c) for i, c in pub.items() if c.naturaleza_dato != "estimacion_modelada" and c.nivel not in NIVELES_FINOS]
    clave = {"ids": [], "valor": "", "texto": ""}
    bloque = P.sec("corta") is not None
    tema = P.q.get("tema")
    nivel = P.q["territorio"]["nivel"]
    nac = _nacional(P)
    ficha = None
    vm = {}
    if bloque:
        vm = {"anio": int(pub[mapa[0]].anio) if mapa else "", "anio_enaho": int(dep[0][1].anio) if dep else ""}
        P._nc_vars = vm
        P.corta.append(P.t(P.sec("corta")[0], **vm))
        if mapa:
            for k in mapa:                                 # P4-09: distrito con su provincia y departamento (tildes)
                P.e[f"lugar_{k}"] = P.m.nombre_completo(pub[k].territorio_id)
            mapa.sort(key=lambda k: P.e[f"lugar_{k}"])      # orden alfabético: no insinúa un ranking
            P.corta.append(P.t(P.sec("corta")[1], **P.valores(vm, n=P.numero(len(mapa)))))
            item = P.sec("clave_item")
            clave = {"ids": mapa, "valor": "", "texto": " ".join(
                P.t(item, **P.valores(vm, lugar_m="{{e:lugar_%s}}" % k, c=P.cm(k), anio=int(pub[k].anio))) for k in mapa)}
            P.usadas += mapa
        P.ojo += [P.t(x, **vm) for x in P.sec("ojo")]
        if dep:
            P.ojo.append(P.t(P.sec("ojo_enaho"), **vm))
        ficha = _sub(P.sec("territorio_ficha"), vm)
        P.expl = {k: _sub(x, vm) for k, x in (P.sec("explicaciones") or {}).items()}
    if dep:
        grupo, dat = _grupo_departamental(P, dep)
        c0 = pub[grupo[0]] if grupo else dep[0][1]
        vd = P.valores(P.vars_cifra(c0), vm and {"anio": int(c0.anio)} or {}, unidades=P.c["nivel_plural"].get(c0.nivel, P.c["nivel_plural"]["defecto"]),
                       n=P.numero(len(grupo)), sujeto_grupo=P.vars_cifra(c0)["sujeto_corto"])
        nombres = {k: _lugar(pub[k]) for k in grupo}
        vd["items"] = P.lista([f"{nombres[k]} ({P.cm(k)})" for k in grupo])
        if dat["oficial"]:
            vd["rango_grupo"] = dat["rango_grupo"]
            texto = P.t(tp["tarjeta_oficial"]["texto"], **vd)
        else:
            texto = P.t(tp["tarjeta_propia"]["texto"], **vd)
        principal = c0.rol == "principal"
        uno = principal and not bloque and len(grupo) == 1
        if uno:                                            # S1-09 (H2, A-H5): un solo miembro: se nombra y su cifra va en la capa 1
            tu = tp["uno"]
            vu = P.valores(vd, nivel_el=tu["nivel_el"].get(c0.nivel, tu["nivel_el"]["defecto"]))
            P.corta.append(P.t(tu["corta"], **vu))
            clave = P.clave_generica(grupo[0], c0, {"clave": tu["clave"]})
            P.ojo.append(P.ojo_generico(c0))
            P.ctxs.append({"titulo": tu["tarjeta"]["titulo"], "texto": P.t(tu["tarjeta"]["oficial" if dat["oficial"] else "propia"], **vu),
                           "etiqueta": None})
        else:
            if principal and not bloque:
                P.corta.append(P.t(tp["corta_grupo"], **vd))
                P.ojo.append(tp["ojo"])
            titulo = tp["tarjeta_oficial"]["titulo_principal" if principal else "titulo"]
            P.ctxs.append({"titulo": _sub(titulo, vd), "texto": texto, "etiqueta": P.c["no_se_compara"] if principal else tp["etiqueta"]})
        P.usadas += grupo
        if principal and not bloque:
            nivel = c0.nivel
            ficha = _sub(tp["territorio_ficha"], vd)       # A-H7: «todos los departamentos del país», no «departamento de Perú»
    elif not bloque:
        P.corta.append(P.t(tp["sin_ranking"], unidades=P.c["nivel_plural"].get(nivel, P.c["nivel_plural"]["defecto"])))
    nr = pub[mapa[0]].nivel if mapa else (dep[0][1].nivel if dep else nivel)
    return P.cierre(clave=clave, tema=None if bloque else tema, nivel_respuesta=nr, territorio_nombre=nac,
                    territorio_ficha=ficha)


def _nacional(P: _Plantilla) -> str:
    from .territorio import resolver          # (import tardío: territorio importa respuesta, que importa este módulo)
    return resolver({"nacional": True}, P.m.ctx).nombre_mostrado


# ======================================================================= cruce_efecto

def cruce_efecto(P: _Plantilla) -> dict:
    """CR-01 (gasto × anemia ENDES): las dos cifras lado a lado y, si se pregunta «¿sirvió?», la estructura de efecto en 5
    partes (R-CRUCES-07, R-03). Qué se gastó (cifra clave), qué cambió, y por qué no se puede decir que uno causó lo otro."""
    cr = next(x for x in P.m.ctx.cruces if x["id_cruce"] == P.q["cruce"])
    ti = P.i[P.q["intencion"]]
    dc = P.bl["cruces"][cr["id_cruce"]]
    A, B = P.por(indicador=cr["indicador_a"]), P.por(indicador=cr["indicador_b"])
    a_id, a = next(((i, c) for i, c in A if c.rol == "principal"), A[0] if A else (None, None))
    a_ctx = [(i, c) for i, c in A if (i, c) != (a_id, a) and c.rol != "principal"]
    b_id, b = (B[0] if B else (None, None))
    locales = P.por(rol="principal", no_indicador=(cr["indicador_a"], cr["indicador_b"]))
    cobs = [(i, c) for i, c in P.cf.items() if c.medida == "cobertura"]
    ref = a if a is not None else b
    vs = P.valores(P.vars_cifra(ref), gasto_contra=dc["gasto_contra"], sujeto_a=dc["sujeto_a"], sujeto_b=dc["sujeto_b"])
    P._nc_vars = vs
    P.nc += [[n, prm] for n, prm in dc["nc"] + ti["nc"]]
    clave = {"ids": [], "valor": "", "texto": ""}
    alcance = {}
    P.corta += [P.t(x, **vs) for x in ti["corta"]]
    if a is not None and _publicable(a):
        va = P.valores(vs, P.vars_cifra(a))
        P.usadas.append(a_id)
        P.corta.append(P.t(ti["corta_cifra"], **va))
        local = a.nivel in NIVELES_LOCALES
        clave = {"ids": [a_id], "valor": P.cm(a_id), "texto": P.t(P.sec("clave_local" if local else "clave_regional"), **va)}
        if local:
            alcance[a_id] = P.t(P.sec("alcance_local"), **va)
    P.ojo += [P.t(x, **vs) for x in ti["ojo"]]
    usados_a = {a_id}
    a_ctx = [(i, c) for i, c in a_ctx if a is None or int(c.anio) == int(a.anio)][:1]   # el del mismo año; los demás son de X-03
    for i, c in a_ctx:                                    # el gasto del territorio más amplio, con el sesgo de sede si lo hay
        if _publicable(c) and P.sec("tarjeta_regional"):
            vc = P.valores(vs, P.vars_cifra(c), c=P.cm(i))
            P.usadas.append(i)
            tr = P.sec("tarjeta_regional")
            t = P.t(tr["texto"], **vc)
            sesgo = P.bloque("sesgo_sede_lima")
            if sesgo:
                ss = sesgo["cruce_efecto"]
                if c.pct_gasto_atribuible is not None:
                    t += P.t(ss["atribuible"], **P.valores(vc, pct_atribuible=P.ent("pct_atribuible", fmt.pct(100 * c.pct_gasto_atribuible, 0))))
                ref_nac = [x["devengado"] for x in (c.lineas_aparte or []) if x["linea"] == "referencia_nacional"]
                if ref_nac:
                    t += P.t(ss["referencia"], **P.valores(vc, linea_ref=P.ent("linea_ref", fmt.monto(sum(ref_nac)))))
            P.ctxs.append({"titulo": _sub(tr["titulo"], vc), "texto": t, "etiqueta": P.i["etiqueta_otro_territorio"]})
            usados_a.add(i)
    motivo = None
    for i, c in locales:                                  # el registro local (SIEN): lo más cercano que llega al lugar
        if not _publicable(c) or P.sec("tarjeta") is None:
            continue
        vl = P.valores(vs, P.vars_cifra(c), P.vars_region(b) if b is not None else {}, c=P.cm(i))
        P.usadas.append(i)
        tj = P.sec("tarjeta")
        t = P.t(tj["texto"], **vl)
        cob = next(((j, x) for j, x in cobs if _publicable(x)), None)
        if cob:                                           # P4-02: la cobertura que pone la confianza en baja, a la vista
            j, x = cob
            vx = P.valores(vl, c_cob=P.cm(j), lugar_cob=_lugar(x), fuente_cob=P.vars_cifra(x)["fuente"])
            P.usadas.append(j)
            P.p["cobertura"] = P.aviso_cobertura(x, lugar=_lugar(x))
            t += P.t(tj["cobertura"], **vx)
        serie_unica = len(P.m.ctx.indicadores[c.indicador_id]["anios_disponibles"]) == 1
        t += P.t(tj["cierre_serie_unica" if serie_unica else "cierre"], **vl)
        P.ctxs.append({"titulo": _sub(tj["titulo"], vl), "texto": t, "etiqueta": P.c["no_se_compara"]})
        if clave["ids"] and clave["ids"][0] != i and P.indic(c).get("motivo_confianza"):
            motivo = _sub(P.indic(c)["motivo_confianza"], vl)   # la confianza la fija esta cifra, que no está en la capa 1
        ex = P.sec("explicaciones")
        if ex:
            P.expl = {k: _sub(x, vl) for k, x in ex.items()}
    if not locales:
        for i, c in cobs:
            if _publicable(c):
                P.ctxs.append(P.tarjeta_generica(c, i))
    if b is not None and _publicable(b):
        tt = P.i["tarjetas"]["endes"]
        vb_ = P.valores(vs, P.vars_cifra(b), c=P.cm(b_id), nivel_palabra=vs["nivel_palabra"])
        P.usadas.append(b_id)
        t = P.t(tt["texto"], **vb_)
        if verbo(b):                                      # R-CRUCES-07 paso 2 y nota de CR-01: la misma ENDES en dos años
            a1, a2 = _anios_comp(b)
            t += P.t(tt["cambio"], **P.valores(vb_, a=a1, b=a2, verbo=P.vb(b_id)))
        if clave["ids"] and P.cf[clave["ids"][0]].nivel in NIVELES_LOCALES:
            t += P.t(tt["sin_nivel_fino"], **vb_)
        P.ctxs.append({"titulo": _sub(tt["titulo"], vb_), "texto": t, "etiqueta": ti.get("etiqueta_otra_cifra") or P.c["no_se_compara"]})
    if P.par["pendientes_dueno"]["cr01_mismo_anio"]["valor"]:     # X-03: el gasto del mismo año que la anemia comparada
        for i, c in A:
            if i not in usados_a and _publicable(c):
                tm = P.i["tarjetas"]["mismo_anio"]
                vc = P.valores(vs, P.vars_cifra(c), c=P.cm(i))
                P.usadas.append(i)
                P.ctxs.append({"titulo": _sub(tm["titulo"], vc), "texto": P.t(tm["texto"], **vc), "etiqueta": tm["etiqueta"]})
    if ti.get("tarjeta_final"):
        tf = ti["tarjeta_final"]
        P.ctxs.append({"titulo": tf["titulo"], "texto": P.t(tf["texto"], **P.valores(vs, lugar_largo=P.vars_cifra(ref)["lugar_largo"])),
                       "etiqueta": None})
    cruces = []
    a_t = next(((i, c) for i, c in A if b is not None and (c.nivel, str(c.territorio_id), int(c.anio)) ==
                (b.nivel, str(b.territorio_id), int(b.anio))), (None, None))
    if a_t[1] is not None and _publicable(a_t[1]) and b is not None and _publicable(b):
        cruces.append({"id_cruce": cr["id_cruce"], "a": a_t[0], "b": b_id, "presentacion": cr["presentacion"],
                       "operacion": cr["presentacion"], "nivel": a_t[1].nivel, "anios": [int(a_t[1].anio)]})
    tema = P.m.ctx.indicadores[cr["indicador_b"]]["tema"]
    return P.cierre(clave=clave, tema=tema, nivel_respuesta=_nivel_respuesta(P, a if a is not None else b),
                    territorio_nombre=_lugar(ref), motivo_confianza=motivo, alcance=alcance, cruces=cruces)


# ======================================================================= punto de entrada

PLANTILLAS = {"nivel_actual": nivel_actual, "evolucion": evolucion, "comparacion": comparacion,
              "identificar_extremo": identificar_extremo, "cruce_efecto": cruce_efecto}


def generar(nombre: str, motor, consulta: dict, cifras: dict) -> dict:
    """Borrador de la respuesta con la plantilla genérica `nombre` (o un nombre antiguo, que se traduce con
    `plantillas.nombres_antiguos`: la consulta completa lo que le falta al q*.yaml con el valor de esa tabla)."""
    antiguos = parametros(motor.ctx.raiz)["plantillas"]["nombres_antiguos"]["valor"]
    if nombre in antiguos:
        regla = antiguos[nombre]
        nombre = regla["plantilla"]
        consulta = {**regla["plan"], **{k: v for k, v in consulta.items() if v is not None}}
    if nombre == "cruce_efecto" and not consulta.get("cruce"):
        nombre = "nivel_actual"                  # sin cruce permitido (R-CRUCES-11): dos cifras separadas
    return PLANTILLAS[nombre](_Plantilla(motor, consulta, cifras, nombre))


# ======================================================================= relleno

def valor_cifra(c, opciones: dict | None = None) -> str:
    opciones = opciones or {}
    if c.medida == "intervalo":
        return fmt.intervalo(c.ic_inf, c.ic_sup)
    if c.medida == "cobertura":  # P4-03: con 1 decimal si las cotas están cerca del umbral (el redondeo lo escondería)
        u = opciones.get("umbral_tamizaje")
        cerca = u is not None and any(abs(x - u) < 1 for x in (c.cota_inf, c.cota_sup))
        return fmt.intervalo(c.cota_inf, c.cota_sup, 1 if cerca else 0)
    if c.medida in fmt.MEDIDAS_MONTO:
        return fmt.monto(c.valor)
    lo, hi = c.ic_inf, c.ic_sup
    ii = c.get("ic_inei")
    if opciones.get("intervalo_visible") == "uno" and ii:   # X-04 «uno»: el del INEI si existe, si no el propio
        lo, hi = ii["ic_inf"], ii["ic_sup"]
    return fmt.pct_cifra(c.valor, lo, hi, c.semaforo_cifra, c.estado_cifra)


def rellenar(b: dict, cifras: dict) -> str:
    t = b["texto"]
    t = re.sub(r"\{\{c:([^}]+)\}\}", lambda m: valor_cifra(cifras[m.group(1)], b.get("opciones")), t)
    for tipo, dic in (("v", "verbos"), ("u", "universos"), ("e", "entidades"), ("p", "protegidos")):
        t = re.sub(r"\{\{" + tipo + r":([^}]+)\}\}", lambda m, d=b.get(dic, {}): d[m.group(1)], t)
    return t
