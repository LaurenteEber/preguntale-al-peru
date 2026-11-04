"""S1-07, fase 2 (desde S1-04): `test_respuestas` compara la respuesta completa por el camino nuevo (consulta mínima →
resolver → planificador → Motor.responder → plantilla genérica) con la referencia de `tests/referencias/q*.json`
(tomada al cerrar S1-00): cifras usadas por clave, valores, intervalos, estados, semáforo, confianza, parcialidad,
comparaciones bloqueadas y reglas de bloqueo iguales; capa 1 dentro del máximo de R-04; sin infracciones del corrector;
sin marcadores ni códigos internos; y todo cambio de texto en las capas 1–3 (o de reglas que solo rotulan) aprobado en
`backlog/slice-1/evidencia/regresion/<Q>.yaml` (agents.md §5.1).

S1-07, fase 1 (desde S1-03): el plan generado desde la consulta mínima (consulta → resolver → planificador) es
igual a las cifras de los q1–q4.yaml hechos a mano, comparadas por clave (no por id) y con la misma comparación.

Diferencia por la decisión del dueño (C-01, E-06, 3/11/2026): Q1 ya no lleva la cifra de 2022
(`anemia_hvca_2022_ant`): una prueba aparte comprueba que no se planifica y el resto debe coincidir exactamente. Si falta el cubo, las pruebas FALLAN (agents.md §8)."""
import json
import re

import pytest
import yaml

from pap.config import Rutas
from pap.motor.consulta import cargar
from pap.motor.planificador import planificar
from pap.motor.respuesta import Motor
from pap.motor.territorio import resolver
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL

QS = ["q1", "q2", "q3", "q4"]
CLAVE_2022_Q1 = ("endes_anemia_6_35m", 2022, "departamento", "09", "proporcion", "contexto")   # anemia_hvca_2022_ant


@pytest.fixture(scope="module")
def raiz():
    r = Rutas(RAIZ_REAL).raiz
    cubo = r / "biblioteca" / "indicadores" / "fact_indicador.parquet"
    assert cubo.exists(), f"falta el cubo {cubo}: `pap calcular` (no se salta: agents.md §8)"
    return r


@pytest.fixture(scope="module")
def motor(raiz):
    return Motor(cargar_contexto(raiz))


def manual(raiz, q):
    return yaml.safe_load((raiz / "tests" / "fixtures" / "consultas_piloto" / f"{q}.yaml").read_text(encoding="utf-8"))


def generado(raiz, motor, q):
    cm = cargar(raiz / "curados" / "motor" / "consultas_minimas" / f"{q}.json", raiz)
    t = cm["territorio"]
    res = resolver(t.get("dentro_de"), motor.ctx) if "nivel" in t and "dentro_de" in t else (
        None if "nivel" in t else resolver(t, motor.ctx))
    return planificar(cm, res, motor)


def por_clave(motor, cifras):
    """{(indicador, anio resuelto, nivel, territorio, medida, rol): año con el que se compara (o None)}."""
    out = {}
    for c in cifras:
        ind = c["indicador"]
        k = (ind, motor.anio(ind, c.get("anio")), c["nivel"], str(c["territorio"]), motor.medida(ind, c.get("medida")), c["rol"])
        assert k not in out, f"clave repetida {k}"
        out[k] = None if c.get("comparar_con") is None else motor.anio(ind, c["comparar_con"])
    return out


@pytest.mark.parametrize("q", QS)
def test_planes(raiz, motor, q):
    esperado = por_clave(motor, manual(raiz, q)["cifras"])
    if q == "q1":
        assert esperado.pop(CLAVE_2022_Q1, "falta") is None      # la diferencia aprobada (C-01) se retira solo de q1.yaml
    plan = generado(raiz, motor, q)
    assert por_clave(motor, plan["cifras"]) == esperado
    assert (plan.get("grupos") or []) == (manual(raiz, q).get("grupos") or [])
    assert plan["intencion"] == manual(raiz, q)["intencion"]
    assert plan["periodo"] == manual(raiz, q)["periodo"]
    assert plan["territorio"]["nivel"] == manual(raiz, q)["territorio"]["nivel"]
    assert plan["territorio"]["id"] == manual(raiz, q)["territorio"]["id"]


def test_q1_cifra_2022(raiz, motor):
    """C-01 cerrada (dueño, 3/11/2026; E-06): la serie se cuenta con su primer y último año; 2022 no se planifica."""
    assert CLAVE_2022_Q1 not in por_clave(motor, generado(raiz, motor, "q1")["cifras"])


# ======================================================================================= fase 2 (S1-04)

REFERENCIAS = RAIZ_REAL / "tests" / "referencias"
ACCIONES_FIRMES = {"bloquear", "suprimir", "agregar_nivel", "publicar_referencial", "bloquear_cruce"}
CAMPOS_CIFRA = ("valor", "ee", "ic_inf", "ic_sup", "cota_inf", "cota_sup", "n_muestra", "numerador", "denominador",
                "estado_cifra", "semaforo_cifra", "ic_inei", "pim", "devengado", "lineas_aparte", "pct_gasto_atribuible",
                "grupo_robusto_nacional", "comparacion", "metodo_ic")
CODIGOS_INTERNOS = [r"\{\{", r"\}\}", r"\{[a-z_0-9]+\}", r"\bR-[A-Z]+-\d+", r"\bNC-[A-Z]", r"\bCR-\d", r"\b[a-z]+_[a-z0-9]+_[a-z0-9_]+\b"]


def clave_dict(c):
    return (c["indicador_id"], int(c["anio"]), c["nivel"], str(c["territorio_id"]), c["medida"], c["rol"])


def texto_clave(k):
    return "/".join(str(x) for x in k)


@pytest.fixture(scope="module")
def nuevas(raiz, motor):
    return {q: motor.responder(generado(raiz, motor, q)) for q in QS}


def referencia(q):
    return json.loads((REFERENCIAS / f"{q}.json").read_text(encoding="utf-8"))


def sin_version(v):
    """S1-12: el cubo pasó a la versión 1.2.0 (soles constantes) sin cambiar ninguna fila anterior; la versión de la tabla
    que arrastra la fila de comparación no es una diferencia de la respuesta."""
    return {k: x for k, x in v.items() if k != "version_tabla"} if isinstance(v, dict) else v


def cifras_por_clave(r):
    out = {}
    for i, c in r["cifras"].items():
        k = clave_dict(c)
        assert k not in out, f"clave repetida {k}"
        out[k] = (i, c)
    return out


def reglas_por_clave(r, ids):
    """{(clave de cifra | respuesta | cruce, regla, acción)} de las cifras y de la respuesta; `ids`: id → clave."""
    out = set()
    for i, c in r["cifras"].items():
        for x in c["resultados"] + c["bloqueos_cruce"]:
            out.add((texto_clave(ids[i]), x["regla"], x["accion"]))
        out.add((texto_clave(ids[i]), "accion_final", c["accion_final"]))
    for x in r["resultados_respuesta"]:
        out.add((texto_clave(ids[x["objetivo"]]) if x["objetivo"] in ids else x["objetivo"], x["regla"], x["accion"]))
    return out


def textos_capas(r):
    c = r["capas"]
    out = {"capa1.respuesta_corta": c["capa1"]["respuesta_corta"], "capa1.confianza.texto": c["capa1"]["confianza"]["texto"],
           "capa1.confianza.ficha": c["capa1"]["confianza"]["ficha"]}
    k = c["capa1"]["cifra_clave"]
    if k:
        out.update({"capa1.cifra_clave.valor": k["valor"], "capa1.cifra_clave.texto": k["texto"],
                    "capa1.cifra_clave.fuente": k["fuente"]})
    for i, t in enumerate(c["capa1"]["ojo_al_leer"]):
        out[f"capa1.ojo_al_leer[{i}]"] = t
    q = c["capa1"]["que_hacer"]
    out["capa1.que_hacer.texto"] = q["texto"] if q else ""
    for i, t in enumerate(c["capa2"]["mas_contexto"]):
        out.update({f"capa2.mas_contexto[{i}].titulo": t["titulo"], f"capa2.mas_contexto[{i}].texto": t["texto"],
                    f"capa2.mas_contexto[{i}].etiqueta": t["etiqueta"] or ""})
    for i, t in enumerate(c["capa2"]["avisos"]):
        out[f"capa2.avisos[{i}]"] = t
    for i, t in enumerate(c["capa2"]["limites"]):
        out[f"capa2.limites[{i}]"] = t
    for i, t in enumerate(c["capa3"]["para_citar"]):
        out[f"capa3.para_citar[{i}]"] = t
    for i, t in enumerate(c["capa3"]["glosario"]):
        out[f"capa3.glosario[{i}].termino"] = t["termino"]
        out[f"capa3.glosario[{i}].definicion"] = t["definicion"]
    return out


def aprobadas(raiz, q):
    ruta = raiz / "backlog" / "slice-1" / "evidencia" / "regresion" / f"{q.upper()}.yaml"
    return (yaml.safe_load(ruta.read_text(encoding="utf-8")) or []) if ruta.exists() else []


def parametros(raiz):
    return yaml.safe_load((raiz / "curados" / "motor" / "parametros_motor.yaml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("q", QS)
def test_respuestas(raiz, motor, nuevas, q):
    ref, new = referencia(q), nuevas[q]
    if q == "q1":                                   # C-01 (dueño, 3/11/2026): sin la cifra de 2022
        ref["cifras"] = {i: c for i, c in ref["cifras"].items() if clave_dict(c) != CLAVE_2022_Q1}
        ref["resultados_respuesta"] = [x for x in ref["resultados_respuesta"] if x["objetivo"] != "anemia_hvca_2022_ant"]
    rc, nc = cifras_por_clave(ref), cifras_por_clave(new)
    # --- iguales exactos
    assert set(nc) == set(rc), (set(nc) ^ set(rc))
    for k, (_, c) in nc.items():
        for campo in CAMPOS_CIFRA:
            assert sin_version(c[campo]) == sin_version(rc[k][1][campo]), (k, campo)
    assert new["semaforo_respuesta"] == ref["semaforo_respuesta"]
    assert new["capas"]["capa1"]["confianza"]["nivel"] == ref["capas"]["capa1"]["confianza"]["nivel"]
    assert new["respuesta_parcial"] == ref["respuesta_parcial"]
    ids_ref = {i: k for k, (i, _) in rc.items()}
    ids_new = {i: k for k, (i, _) in nc.items()}
    assert sorted(texto_clave(ids_new[i]) for i in new["comparaciones_bloqueadas"]) == \
        sorted(texto_clave(ids_ref[i]) for i in ref["comparaciones_bloqueadas"])
    regs_ref, regs_new = reglas_por_clave(ref, ids_ref), reglas_por_clave(new, ids_new)
    firmes = lambda s: {x for x in s if x[2] in ACCIONES_FIRMES or x[1] == "accion_final"}   # noqa: E731
    assert firmes(regs_new) == firmes(regs_ref)
    # --- límites
    p = parametros(raiz)["respuesta"]
    assert new["capas"]["capa1"]["palabras"] <= p["capa1_palabras_max"]["valor"]
    infr = [x for x in new["resultados_respuesta"] if x["regla"] in p["infracciones_corrector"]["valor"] and x["accion"] != "rotular"]
    assert not infr, infr
    visible = textos_capas(new)
    for ruta, t in visible.items():
        for cod in CODIGOS_INTERNOS:
            assert not re.search(cod, t), (ruta, cod, t)
    assert not re.search(r"\{\{|\}\}", new["texto"])
    # --- diferencias aprobadas (texto de las capas 1–3 y reglas que solo rotulan, advierten o piden revisión)
    diferencias = [{"capa": r, "antes": textos_capas(ref).get(r, ""), "despues": visible.get(r, "")}
                   for r in sorted(set(visible) | set(textos_capas(ref)))
                   if visible.get(r, "") != textos_capas(ref).get(r, "")]
    f = lambda s: {x for x in s if x[2] not in ACCIONES_FIRMES and x[1] != "accion_final"}   # noqa: E731
    fmt = lambda x: f"{x[1]} · {x[2]} · {x[0]}"   # noqa: E731
    diferencias += [{"capa": "reglas", "antes": fmt(x), "despues": ""} for x in sorted(f(regs_ref) - f(regs_new))]
    diferencias += [{"capa": "reglas", "antes": "", "despues": fmt(x)} for x in sorted(f(regs_new) - f(regs_ref))]
    ok = aprobadas(raiz, q)
    for a in ok:
        assert a["aprobado_por"] in ("agente", "dueño") and str(a["motivo"]).strip(), a
    clave = lambda d: (d["capa"], d["antes"], d["despues"])   # noqa: E731
    sin_aprobar = [d for d in diferencias if clave(d) not in {clave(a) for a in ok}]
    caducadas = [a for a in ok if clave(a) not in {clave(d) for d in diferencias}]
    assert not sin_aprobar, "diferencias sin aprobar en evidencia/regresion/%s.yaml:\n%s" % (
        q.upper(), yaml.safe_dump(sin_aprobar, allow_unicode=True, width=10_000))
    assert not caducadas, caducadas
