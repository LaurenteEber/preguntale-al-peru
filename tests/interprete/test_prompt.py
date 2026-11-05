"""S2-03 — Vocabulario e instrucciones desde datos curados: los 4 temas y las 6 intenciones; sin números fuera del esquema y
de los ejemplos; un alias cambia el prompt y su versión; la huella es determinista; los ejemplos no se cruzan con el conjunto
de evaluación y cumplen el contrato."""
import re
import shutil
import unicodedata
from pathlib import Path

import pytest
import yaml

from pap.config import Rutas
from pap.interprete.prompt import armar, ejemplos
from pap.interprete.vocabulario import vocabulario
from pap.motor.interpretacion import validar

from conftest import RAIZ_REAL

RAIZ = Rutas(RAIZ_REAL).raiz
EVALUACION = RAIZ / "tests" / "interprete" / "evaluacion.yaml"


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^\w\s]", " ", t).split())


def test_el_prompt_trae_los_temas_y_las_intenciones():
    texto, _ = armar(RAIZ)
    par = yaml.safe_load((RAIZ / "curados/motor/parametros_motor.yaml").read_text(encoding="utf-8"))
    temas = par["temas"]["vocabulario"]["valor"]
    intenciones = list(yaml.safe_load((RAIZ / "curados/motor/intenciones.yaml").read_text(encoding="utf-8"))["intenciones"])
    assert len(temas) == 4 and len(intenciones) == 6
    for x in temas + intenciones:
        assert f"`{x}`" in texto, x


def test_sin_numeros_fuera_del_esquema_y_de_los_ejemplos():
    texto, _ = armar(RAIZ)
    antes = texto.split("## Ejemplos")[0]
    assert not re.search(r"\d", antes), re.findall(r".{20}\d.{20}", antes)
    assert not re.search(r"\d", (RAIZ / "curados/interprete/prompt.md").read_text(encoding="utf-8"))


def test_el_vocabulario_no_trae_datos_de_la_biblioteca():
    v = vocabulario(RAIZ)
    assert set(v) == {"temas", "intenciones", "lima", "niveles", "nacional"}
    assert not re.search(r"\d", repr(v))


def test_cambiar_un_alias_cambia_el_prompt_y_su_version(tmp_path):
    copia = tmp_path / "raiz"
    for d in ("curados/motor", "curados/interprete"):
        shutil.copytree(RAIZ / d, copia / d)
    t1, v1 = armar(copia)
    p = copia / "curados/motor/parametros_motor.yaml"
    s = p.read_text(encoding="utf-8")
    assert "      gasto: gasto_publico\n" in s
    p.write_text(s.replace("      gasto: gasto_publico\n", "      gasto: gasto_publico\n      plata: gasto_publico\n"), encoding="utf-8")
    t2, v2 = armar(copia)
    assert t1 != t2 and v1 != v2 and "plata" in t2


def test_la_misma_entrada_da_la_misma_huella():
    assert armar(RAIZ) == armar(RAIZ)
    assert armar(RAIZ)[1].startswith("sha256:") and len(armar(RAIZ)[1]) == 71


def test_ejemplos_cumplen_el_contrato_y_son_entre_diez_y_veinte():
    ej = ejemplos(RAIZ)
    assert 10 <= len(ej) <= 20
    for e in ej:
        validar(e["interpretacion"], RAIZ)
        for a in _anclas(e["interpretacion"]):
            assert a in e["pregunta"], (e["pregunta"], a)               # las anclas de los ejemplos son literales


def _anclas(i):
    if i["resultado"] == "consulta":
        return list(i["anclas"].values())
    if i["resultado"] == "aclaracion":
        return [a for o in i["opciones"] for a in o["anclas"].values()]
    if i["resultado"] == "fuera_de_alcance":
        return [i["pedido"]]
    return []


def test_los_ejemplos_no_se_cruzan_con_el_conjunto_de_evaluacion():
    assert EVALUACION.exists(), f"falta {EVALUACION} (S2-02); no se salta"
    ev = {norm(e["pregunta"]) for e in yaml.safe_load(EVALUACION.read_text(encoding="utf-8"))["entradas"]}
    cruce = [e["pregunta"] for e in ejemplos(RAIZ) if norm(e["pregunta"]) in ev]
    assert not cruce, cruce
