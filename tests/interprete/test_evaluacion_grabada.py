"""S2-05 — Evaluación con grabaciones: corre el conjunto de evaluación (tests/interprete/evaluacion.yaml, S2-02) por
`interpretar()` con el cliente en modo «reproducir» y exige en 0 las dos métricas absolutas del slice (README, definición de
hecho 2). Las demás métricas se informan, sin umbral hasta S2-09.

1. **Valores sin ancla aceptados:** cada valor de la consulta producida necesita un ancla que esté en la pregunta y lo
   justifique. Se comprueba con una implementación propia de esta prueba, no con la del intérprete.
2. **Números que no salen de un marcador del cubo:** en el texto de la respuesta (`texto_con_marcadores` sin marcadores, la
   misma comprobación de R-LENGUAJE-03 que tests/test_respuesta_p3.py), en la pregunta y las etiquetas de una aclaración, en un
   mensaje fijo y en `entendimos`, sin contar los años ni el eco literal de pregunta_original.

Si falta el conjunto, el cubo o una grabación, la prueba FALLA y dice cómo grabarla (agents.md §8; README del slice)."""
import json
import re
import unicodedata
from collections import Counter

import pytest
import yaml

from pap.config import Rutas
from pap.interprete import llm as L
from pap.interprete.interpretar import interpretar
from pap.motor.preguntar import EleccionInvalida
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL

RAIZ = Rutas(RAIZ_REAL).raiz
EVALUACION = RAIZ / "tests" / "interprete" / "evaluacion.yaml"
PAR = yaml.safe_load((RAIZ / "curados/motor/parametros_motor.yaml").read_text(encoding="utf-8"))


def norm(s) -> list[str]:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    out = []
    for w in re.sub(r"[^a-z0-9]+", " ", s).split():
        out += {"del": ["de", "el"], "al": ["a", "el"]}.get(w, [w])
    return out


def contiene(hay: list, aguja: list) -> bool:
    return bool(aguja) and any(hay[i:i + len(aguja)] == aguja for i in range(len(hay) - len(aguja) + 1))


def sin_ancla(pregunta: str, c: dict, anclas: dict) -> list[str]:
    """Los valores de la consulta producida que no tienen un ancla válida (métrica 1)."""
    q, malos = norm(pregunta), []
    nacional = [norm(t) for t in PAR["territorio"]["textos_nacional"]["valor"]]
    niveles = PAR["territorio"]["palabras_que_fijan_nivel"]["valor"]

    def en_q(k):
        return isinstance(anclas.get(k), str) and contiene(q, norm(anclas[k]))

    def lugar(x, k):
        if not en_q(k):
            return False
        if x.get("nacional") is True:
            return any(contiene(norm(anclas[k]), n) for n in nacional)
        return norm(x.get("texto")) == norm(anclas[k])
    defecto = PAR["interprete"]["sin_intencion"]["valor"]
    if "intencion" in c and not en_q("intencion") and not (c["intencion"] == defecto and "intencion" not in anclas):
        malos.append("intencion")
    if "tema" in c and not en_q("tema"):
        malos.append("tema")
    t = c.get("territorio") or {}
    if "nivel" in t:
        ps = {w for p in niveles[t["nivel"]] for w in norm(p)}
        if not (en_q("nivel") and any(w in ps or w.rstrip("s") in ps or w[:-2] in ps for w in norm(anclas["nivel"]))):
            malos.append("nivel")
        if "dentro_de" in t and not lugar(t["dentro_de"], "dentro_de"):
            malos.append("dentro_de")
    elif t and not lugar(t, "territorio"):
        malos.append("territorio")
    if "comparar_con" in c and not lugar(c["comparar_con"], "comparar_con"):
        malos.append("comparar_con")
    for k in ("anio", "desde", "hasta"):
        v = (c.get("periodo") or {}).get(k)
        if v is not None and not (en_q(k) and str(v) in norm(anclas[k])):
            malos.append(k)
    return malos


def numeros_sueltos(r: dict, pregunta: str) -> list[str]:
    """Números visibles que no salen de un marcador del cubo ni son años (métrica 2)."""
    if r["tipo"] == "aclaracion":
        a = r["aclaracion"]
        t = " ".join([a["pregunta"]] + [o["etiqueta"] for o in a["opciones"]])
    elif r["tipo"] == "mensaje":
        t = r["texto"]
    else:
        t = re.sub(r"\{\{[a-z]:[^}]+\}\}", "", r["texto_con_marcadores"])
    t = (t + " " + (r.get("entendimos") or "")).replace(pregunta, " ")
    return [d for d in re.findall(r"\d+", t) if not re.fullmatch(r"(19|20)\d\d", d)]


def test_evaluacion_con_grabaciones(tmp_path):
    assert EVALUACION.exists(), f"falta {EVALUACION} (S2-02); no se salta"
    assert (RAIZ / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    entradas = yaml.safe_load(EVALUACION.read_text(encoding="utf-8"))["entradas"]
    motor = Motor(cargar_contexto(RAIZ))
    cliente = L.Cliente(RAIZ, modo="reproducir")
    faltan, sin_ancla_aceptados, numeros, aciertos, por_resultado = [], [], [], 0, Counter()
    for e in entradas:
        try:
            r = interpretar(e["pregunta"], motor, llm=cliente, cache_dir=tmp_path / "cache", registro=None)
        except L.FaltaGrabacion as x:
            faltan.append((e["id"], str(x)))
            continue
        except EleccionInvalida as x:                       # no se pasa --elegir: no debería pasar
            pytest.fail(f"{e['id']}: {x}")
        i = r["interpretacion"]
        por_resultado[i["resultado"]] += 1
        aciertos += i["resultado"] == e["esperado"]["resultado"]
        if i.get("consulta"):
            malos = sin_ancla(e["pregunta"], i["consulta"], i.get("anclas") or {})
            if malos:
                sin_ancla_aceptados.append((e["id"], malos))
        n = numeros_sueltos(r, (r.get("plan") or {}).get("pregunta") or e["pregunta"])
        if n:
            numeros.append((e["id"], n))
    corridas = len(entradas) - len(faltan)
    print(f"\nevaluación con grabaciones: {corridas}/{len(entradas)} corridas; resultado correcto {aciertos}/{corridas}; "
          f"por resultado {dict(por_resultado)}")
    if faltan:
        pytest.fail(f"falta la grabación de {len(faltan)} de {len(entradas)} preguntas del conjunto "
                    f"({', '.join(i for i, _ in faltan[:10])}{'…' if len(faltan) > 10 else ''}). La primera: {faltan[0][1]}",
                    pytrace=False)
    assert not sin_ancla_aceptados, f"valores sin ancla aceptados: {sin_ancla_aceptados}"
    assert not numeros, f"números que no salen de un marcador del cubo: {numeros}"
