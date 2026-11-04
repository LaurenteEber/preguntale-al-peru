"""P3 — Motor de respuesta del piloto: consulta estructurada → cifras del cubo → validador (etapas 0–7, con degradación
R-MOTOR-01) → semáforo de cifra → cruces → texto por plantilla → validador de la respuesta (etapas 8–10) → ficha de
límites → respuesta.json y respuesta.md.

Sin LLM (decisión del 10/10/2026): el texto sale de plantillas con marcadores {{c:}}, {{v:}}, {{u:}}, {{e:}} y {{p:}}
(R-LENGUAJE-03); los números se insertan al final desde el cubo. Especificación: 00_proyecto/piloto/
especificacion_validador_motor.md §4 y §6.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import yaml

from . import capas as K
from . import ficha as F
from . import formato as fmt  # noqa: F811
from . import plantillas
from .validador import cargar
from .validador.nucleo import Cifra, Contexto, Respuesta
from .validador.validador import evaluar_con_degradacion, evaluar_respuesta

MEDIDA_POR_DEFECTO = {"sien_cobertura_tamizaje_6_35m": "cobertura", "mapa_pobreza_2018": "intervalo",
                      "gasto_ex_pan": "devengado", "gasto_ex_pan_opcion_c": "devengado"}
VOCAB_INTENCION = ("nivel_actual", "evolucion", "comparacion", "cruce", "identificar_extremo", "efecto")


def nombre_completo_ubigeo(ctx, ubigeo: str) -> str:
    """«Distrito (provincia, departamento)» con el nombre mostrado de dim_ubigeo_historico vigente (P4-09).
    Lo usan Motor.nombre_completo y el resolver territorial (S1-02)."""
    u = ctx.ubigeos
    v = u[u.vigente_hasta.isna()] if "vigente_hasta" in u else u

    def nom(cod):
        x = v[v.ubigeo_inei.astype(str) == cod]
        return str(x.iloc[0].nombre_mostrado) if len(x) else cod
    u6 = str(ubigeo)
    return f"{nom(u6)} ({nom(u6[:4] + '00')}, {nom(u6[:2] + '0000')})"


def _limpio(d: dict | None) -> dict | None:
    if d is None:
        return None
    out = {}
    for k, v in d.items():
        try:
            if v is None or (isinstance(v, float) and math.isnan(v)) or str(v) in ("<NA>", "NaT"):
                v = None
        except Exception:
            pass
        out[k] = v
    return out


class Motor:
    def __init__(self, ctx: Contexto):
        cargar()
        self.ctx = ctx

    # ------------------------------------------------------------------ cubo
    def anio(self, ind_id: str, anio) -> int:
        disp = sorted(int(a) for a in self.ctx.indicadores[ind_id]["anios_disponibles"])
        return disp[-1] if anio in (None, "ultimo") else int(anio)

    def medida(self, ind_id: str, medida: str | None = None) -> str:
        return medida or MEDIDA_POR_DEFECTO.get(ind_id, "proporcion")

    def fila(self, ind_id, anio, nivel, terr, medida=None, linea="cifra") -> dict | None:
        return _limpio(self.ctx.fila_cubo(ind_id, int(anio), nivel, str(terr), self.medida(ind_id, medida), linea))

    def lineas_aparte(self, ind_id, anio, nivel, terr) -> list[dict]:
        c = self.ctx.cubo
        x = c[(c.indicador_id == ind_id) & (c.anio == int(anio)) & (c.nivel == nivel) & (c.territorio_id == str(terr))
              & (c.linea != "cifra") & (c.medida == "devengado")]
        return [{"linea": r.linea, "devengado": float(r.valor)} for r in x.itertuples()]

    # ------------------------------------------------------------------ cifras
    def cifra(self, spec: dict, consulta: dict) -> Cifra | None:
        ind_id = spec["indicador"]
        ind = self.ctx.indicadores[ind_id]
        anio = self.anio(ind_id, spec.get("anio"))
        f = self.fila(ind_id, anio, spec["nivel"], spec["territorio"], spec.get("medida"))
        q = {"nivel_pedido": consulta["territorio"]["nivel"], "territorio_pedido": consulta["territorio"].get("nombre_pedido"),
             "anio_pedido": None if consulta.get("periodo", {}).get("tipo") == "ultimo" else anio,
             "rol": spec.get("rol", "principal"), "es_principal": spec.get("rol", "principal") == "principal",
             "intencion_pregunta": consulta["intencion"], "id_cifra": spec["id"]}
        if spec.get("nivel_pedido"):
            q["nivel_pedido"] = spec["nivel_pedido"]
        if f is None:
            c = Cifra.desde({"indicador_id": ind_id, "anio": anio, "nivel": spec["nivel"],
                             "territorio_id": str(spec["territorio"]), "estado_calculo": "sin_fila"}, ind, q)
            c.sin_fila = True
            return c
        if ind["naturaleza_dato"] == "presupuestal_financiero":
            for med in ("pim", "pia", "devengado"):
                g = self.fila(ind_id, anio, spec["nivel"], spec["territorio"], med)
                f[med] = g["valor"] if g else None
            f["fase_gasto"], f["precios"] = "devengado", "corrientes"
            f["bloque_consolidado"] = "gasto_final"
            f["tema_id"] = ind.get("tema_id")
            f["cadena"] = "concepto" if str(ind.get("tema_id", "")).startswith("cpt_") else None
        c = Cifra.desde(f, ind, q)
        c.ic_inei = self.ic_inei(ind_id, anio, spec["nivel"], spec["territorio"], c.get("medida"))
        c.contraste_oficial = self.dorada(ind_id, anio, spec["nivel"], spec["territorio"])
        if ind["naturaleza_dato"] == "presupuestal_financiero":
            c.lineas_aparte = self.lineas_aparte(ind_id, anio, spec["nivel"], spec["territorio"])
        if spec.get("comparar_con") is not None:
            a2 = int(spec["comparar_con"])
            g = self.fila(ind_id, a2, spec["nivel"], spec["territorio"], spec.get("medida"))
            if g is not None:
                g = dict(g)
                g["prueba_cambio"] = self.prueba_cambio(g, f)
                c.comparacion = g
        if spec.get("serie"):
            c.serie = [x for x in (self.fila(ind_id, a, spec["nivel"], spec["territorio"], spec.get("medida"))
                                   for a in ind["anios_disponibles"]) if x]
        return c

    def nombre_completo(self, ubigeo: str) -> str:
        """«Distrito (provincia, departamento)» con el nombre mostrado de dim_ubigeo_historico vigente (P4-09)."""
        return nombre_completo_ubigeo(self.ctx, ubigeo)

    def grupos_oficiales(self, ind_id: str, anio) -> list[dict]:
        """Grupos de departamentos estadísticamente semejantes publicados por el INEI (R-ENC-12: prevalecen sobre los
        propios). Tabla curada con cita oficial: curados/capa0/grupos_oficiales_inei.csv."""
        if not hasattr(self, "_grupos"):
            import csv
            ruta = self.ctx.raiz / "curados" / "capa0" / "grupos_oficiales_inei.csv"
            self._grupos = list(csv.DictReader(open(ruta, encoding="utf-8"))) if ruta.exists() else []
        return [g for g in self._grupos if g["indicador_id"] == ind_id and g["anio"] == str(anio)]

    def dorada(self, ind_id, anio, nivel, terr) -> dict | None:
        """Cifra oficial (INEI o, para el SIEN, INS) con el mismo indicador (y por tanto el mismo criterio), año y territorio."""
        for d in self.ctx.doradas:
            if (d["indicador_id"], d["anio"], d["nivel"], d["territorio"]) == (ind_id, str(anio), nivel, str(terr)) \
                    and (d.get("valor_publicado") or d.get("ic_inf_publicado")):
                return {"valor": float(d["valor_publicado"]) if d.get("valor_publicado") else None,
                        "documento": d["documento"],
                        "cuadro_pagina": d["cuadro_pagina"], "criterio": d["criterio"], "id_cifra": d["id_cifra"],
                        "entidad": "INS" if d.get("tipo_cita") == "oficial_ins" else "INEI"}
        return None

    def ic_inei(self, ind_id, anio, nivel, terr, medida) -> dict | None:
        """Intervalo publicado por el INEI para la misma cifra, si existe (decisión del 11/10/2026: en el piloto se
        muestran el propio y el del INEI). Sale de cifras_doradas.csv, que solo tiene citas oficiales con su página."""
        if medida != "proporcion":
            return None
        for d in self.ctx.doradas:
            if (d["indicador_id"], d["anio"], d["nivel"], d["territorio"]) == (ind_id, str(anio), nivel, str(terr)) \
                    and d.get("ic_inf_publicado") and d.get("ic_sup_publicado"):
                return {"ic_inf": float(d["ic_inf_publicado"]), "ic_sup": float(d["ic_sup_publicado"]),
                        "documento": d["documento"], "cuadro_pagina": d["cuadro_pagina"], "id_cifra": d["id_cifra"]}
        return None

    def prueba_cambio(self, antes: dict, despues: dict) -> dict | None:
        """Diferencia de dos proporciones de años distintos (muestras independientes): z con los EE del diseño;
        p bilateral; significativa con alfa de parametros_globales."""
        if antes.get("ee") is None or despues.get("ee") is None:
            return None
        d = float(despues["valor"]) - float(antes["valor"])
        ee = math.sqrt(float(antes["ee"]) ** 2 + float(despues["ee"]) ** 2)
        z = d / ee if ee > 0 else 0.0
        p = math.erfc(abs(z) / math.sqrt(2))
        return {"diferencia": round(d, 4), "ee_diferencia": round(ee, 4), "z": round(z, 4), "p_valor": round(p, 6),
                "significativa": p < float(self.ctx.pg.get("alfa", 0.05)), "anios": [int(antes["anio"]), int(despues["anio"])]}

    def construir(self, base: Cifra):
        def _c(paso: dict) -> Cifra | None:
            if paso.get("tipo") != "nivel":
                return None  # el cubo no trae años agrupados ni respuestas parciales: se detiene con traza
            spec = {"id": base.id_cifra, "indicador": base.indicador_id, "anio": base.anio, "nivel": paso["nivel"],
                    "territorio": paso["territorio_id"], "medida": base.medida, "rol": base.rol,
                    "nivel_pedido": base.nivel_pedido}
            consulta = {"territorio": {"nivel": base.nivel_pedido, "nombre_pedido": base.territorio_pedido},
                        "intencion": base.intencion_pregunta, "periodo": {}}
            nueva = self.cifra(spec, consulta)
            return None if nueva is None or nueva.sin_fila else nueva
        return _c

    def evaluar(self, c: Cifra) -> Cifra:
        if c.sin_fila:
            c.estado_cifra, c.semaforo_cifra, c.traza = "sin_datos", "no_publicable", [{"resultado": "sin_fila_en_el_cubo"}]
            c.evaluacion = None
            return c
        final, traza = evaluar_con_degradacion(c, self.ctx, self.construir(c))
        final.traza = traza
        sem = next((r for r in final.evaluacion.resultados if r.regla == "R-CRUCES-09"), None)
        final.semaforo_cifra = (sem.detalle or {}).get("semaforo") if sem else None
        final.motivos_semaforo = (sem.detalle or {}).get("motivos") if sem else []
        final.semaforo_detalle = sem.detalle if sem else {}
        final.nivel_respuesta = final.nivel
        return final

    # ------------------------------------------------------------------ respuesta
    def responder(self, consulta: dict) -> dict:
        """Respuesta por capas. Antes de calcular, desvía las consultas que no se pueden responder (S1-05): una aclaración
        pendiente o un plan con un motivo de «no se puede» de alcance total. Si el validador deja sin publicar todas las
        cifras principales, también responde «no se puede» (con el motivo que dejó su traza, sin mostrar el valor)."""
        from . import preguntar as P
        ctx = self.ctx
        if consulta.get("aclaracion"):
            return P.respuesta_aclaracion(self, consulta)
        motivo = P.motivo_total(self, consulta)
        if motivo:
            return P.respuesta_no_se_puede(self, consulta, motivo)
        assert consulta["intencion"] in VOCAB_INTENCION, consulta["intencion"]
        cifras = {}
        for spec in consulta["cifras"]:
            c = self.cifra(spec, consulta)
            cifras[spec["id"]] = self.evaluar(c)
        for g in consulta.get("grupos") or []:  # cifras en lote (p. ej. distritos de un grupo robusto, departamentos)
            for spec in plantillas.expandir_grupo(self, g, consulta):
                cifras[spec["id"]] = self.evaluar(self.cifra(spec, consulta))
        base = P.ninguna_principal_publicable(cifras)
        if base is not None:                      # R-LENGUAJE-05: ninguna cifra principal es publicable
            return P.respuesta_no_se_puede(self, consulta, P.motivo_de_cifra(self, base), cifras=cifras, cifra_base=base)
        faltan = P.partes_faltantes(self, consulta, cifras)      # R-LENGUAJE-05 parcial: se responde y se dice lo que falta
        bloqueadas: set[str] = set()
        por_periodo = P.avisos_de_periodo(self, consulta)        # S1-09: las fechas pedidas que no se pudieron respetar
        for _ in range(3):  # R-ENC-11 (etapa 8) decide qué comparaciones se pueden hacer: borrador → validar → rehacer
            for k, c in cifras.items():
                c.comparacion_bloqueada = k in bloqueadas
            borrador = plantillas.generar(consulta["plantilla"], self, consulta, cifras)
            if faltan:
                borrador = P.con_partes_faltantes(self, borrador, faltan)
            if por_periodo:
                borrador = P.con_aviso_periodo(borrador, por_periodo)
            r, res = self._validar(consulta, borrador, cifras)
            nuevas = {x.objetivo for x in res if x.regla == "R-ENC-11" and x.accion == "bloquear_cruce"} & set(cifras)
            if nuevas <= bloqueadas:
                break
            bloqueadas |= nuevas
        sem_r = next(((x.detalle or {}) for x in res if x.regla == "R-CRUCES-10"), {})
        texto_final = plantillas.rellenar(borrador, cifras)
        avisos = self._avisos(res, borrador) + self._avisos_de_cifras(cifras, borrador)
        capas = K.construir(self, consulta, borrador, cifras, {"corta": r.ficha["corta_texto"]},
                            sem_r.get("semaforo_respuesta"), avisos)
        return {"capas": capas,"consulta": consulta, "version_biblioteca": self.version(),
                "cifras": {k: self._cifra_dict(v) for k, v in cifras.items() if k in borrador["cifras_usadas"]},
                "cruces": borrador.get("cruces") or [],
                "semaforo_respuesta": sem_r.get("semaforo_respuesta"), "motivos_semaforo_respuesta": sem_r.get("motivos"),
                "texto": texto_final, "texto_con_marcadores": borrador["texto"],
                "ficha": {"corta": r.ficha["corta_texto"], "larga": r.ficha["larga"]},
                "comparaciones_bloqueadas": sorted(bloqueadas),
                "avisos_al_usuario": [{k: v for k, v in a.items() if k != "detalle"} for a in avisos],
                "resultados_respuesta": [x.a_dict() for x in res],
                "corrector": [x.a_dict() for x in res if x.regla in ("R-LENGUAJE-02", "R-LENGUAJE-03", "R-LENGUAJE-06", "R-GASTO-15")],
                "respuesta_parcial": borrador.get("respuesta_parcial", False), "tipo": "respuesta"}

    def _validar(self, consulta, borrador, cifras):
        ctx = self.ctx
        lista = [cifras[i] for i in borrador["cifras_usadas"]]
        r = Respuesta({"pregunta": consulta["pregunta"], "intencion_pregunta": consulta["intencion"],
                       "nivel_pedido": consulta["territorio"]["nivel"], "territorio_pedido": consulta["territorio"].get("nombre_pedido"),
                       "cifras": lista, "cruces": borrador.get("cruces") or [], "texto": borrador["texto"],
                       "cifras_permitidas": borrador["cifras_usadas"], "respuesta_parcial": borrador.get("respuesta_parcial", False),
                       "nivel_respuesta": borrador.get("nivel_respuesta")})
        # 1.ª pasada: semáforo de la respuesta (R-CRUCES-10); 2.ª: con la ficha ya generada (R-LENGUAJE-01)
        r.ficha = {"corta": {}, "larga": {}}
        res1 = evaluar_respuesta(r, ctx)
        sem_r = next(((x.detalle or {}) for x in res1 if x.regla == "R-CRUCES-10"), {})
        r.ficha = F.generar(self, consulta, r, borrador, sem_r, res1)
        res = evaluar_respuesta(r, ctx)
        return r, res

    def _avisos(self, res, borrador) -> list[dict]:
        """Mensajes de las reglas de respuesta que acompañan al texto (rotular/advertir), en lenguaje ciudadano. El
        semáforo (R-CRUCES-10) ya va en la ficha y la estructura de efecto (R-CRUCES-07) en el texto."""
        out, vistos = [], set()
        for x in res:
            if x.accion not in ("rotular", "advertir") or x.regla in ("R-CRUCES-10", "R-CRUCES-07"):
                continue
            m = fmt.humanizar(x.mensaje, borrador.get("explicaciones"))
            if m and m not in vistos:
                vistos.add(m)
                out.append({"regla": x.regla, "objetivo": x.objetivo, "texto": m, "detalle": x.detalle})
        return out

    def _avisos_de_cifras(self, cifras, borrador) -> list[dict]:
        """R-ENC-13 (S1-09, A-H1): el aviso del año con quiebre de modo (ENDES 2020) llega a la capa 2 cuando la cifra mostrada es de
        ese año (la regla pide que siempre lleve una marca)."""
        out = []
        for i in borrador["cifras_usadas"]:
            c = cifras[i]
            for x in (c.evaluacion.resultados if c.evaluacion else []):
                anios = [int(a) for a in (x.detalle or {}).get("anios_quiebre") or []]
                if x.regla == "R-ENC-13" and x.accion == "advertir" and x.mensaje and int(c.anio) in anios:
                    m = fmt.humanizar(x.mensaje, borrador.get("explicaciones"))
                    if m:
                        out.append({"regla": x.regla, "objetivo": x.objetivo, "texto": m, "detalle": x.detalle})
        return out

    def _cifra_dict(self, c: Cifra) -> dict:
        ev = c.evaluacion
        campos = ("indicador_id", "anio", "nivel", "territorio_id", "territorio_nombre", "medida", "valor", "ee", "cv",
                  "ic_inf", "ic_sup", "n_muestra", "numerador", "denominador", "cota_inf", "cota_sup", "rol",
                  "nivel_pedido", "estado_cifra", "semaforo_cifra", "motivos_semaforo", "avisos", "validada_dorada",
                  "pct_gasto_atribuible", "pim", "devengado", "lineas_aparte", "grupo_robusto_nacional", "comparacion",
                  "traza", "metodo_ic", "ic_inei", "contraste_oficial")
        d = {k: (c.get(k) if not hasattr(c.get(k), "item") else c.get(k).item()) for k in campos}
        d["resultados"] = [r.a_dict() for r in ev.resultados] if ev else []
        d["accion_final"] = ev.accion_final if ev else "suprimir"
        d["bloqueos_cruce"] = [r.a_dict() for r in ev.bloqueos_cruce] if ev else []
        return json.loads(json.dumps(d, default=str))

    def version(self) -> dict:
        m = self.ctx.manifiestos.get("p1_indicadores", {})
        return {"cubo": m.get("tablas", {}).get("fact_indicador", {}).get("hash"), "commit_cubo": m.get("codigo", {}).get("commit"),
                "reglas": hashlib.sha256((self.ctx.raiz / "reglas" / "reglas.json").read_bytes()).hexdigest()[:12]}


def preguntar(ctx: Contexto, ruta_consulta: Path, salida: Path) -> dict:
    consulta = yaml.safe_load(Path(ruta_consulta).read_text(encoding="utf-8"))
    res = Motor(ctx).responder(consulta)
    salida.mkdir(parents=True, exist_ok=True)
    (salida / f"{consulta['id'].lower()}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str),
                                                           encoding="utf-8")
    (salida / f"{consulta['id'].lower()}.md").write_text(F.markdown(res), encoding="utf-8")
    return res
