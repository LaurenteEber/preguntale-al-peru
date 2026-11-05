"""S3-01 — Decisiones del dueño aplicadas al motor (X-02, X-03, X-04), enlaces de las citas (P-02) y rótulos en YAML.

Cada prueba cubre una regla de `backlog/slice-3/S3-01-decisiones-motor.md`. Si falta el cubo, las pruebas FALLAN (agents.md §8)."""
import copy
import csv
import re

import pytest
import yaml

from pap.config import Rutas
from pap.motor import ficha as F
from pap.motor import plantillas as PLT
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL
from test_plantillas_intencion import plan_de
from test_regresion_q1_q4 import generado

# Los rótulos que antes estaban fijos en ficha.py (el .md de Q1–Q4 debe quedar idéntico byte a byte)
ROTULOS_LEGADO = {"ojo_al_leer": "Ojo al leer", "avisos": "Avisos", "limites": "Límites de esta respuesta",
                  "para_citar": "Para citar y verificar", "glosario": "Glosario", "que_hacer": "¿Qué puedo hacer?",
                  "texto_pendiente": "(texto pendiente de revisión)", "mas_contexto": "Más contexto", "como_citar": "Cómo citar",
                  "enlace_oficial": "Documento oficial"}   # el último es nuevo (P-02): el texto del enlace de cada cita


@pytest.fixture(scope="module")
def raiz():
    r = Rutas(RAIZ_REAL).raiz
    assert (r / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    return r


@pytest.fixture(scope="module")
def motor(raiz):
    return Motor(cargar_contexto(raiz))


def parametros(raiz):
    return yaml.safe_load((raiz / "curados" / "motor" / "parametros_motor.yaml").read_text(encoding="utf-8"))["pendientes_dueno"]


def con_parametros(monkeypatch, raiz, **pendientes):
    p = copy.deepcopy(PLT.parametros(raiz))
    for k, v in pendientes.items():
        p["pendientes_dueno"][k]["valor"] = v
    monkeypatch.setattr(PLT, "parametros", lambda r: p)
    return p


# ------------------------------------------------------------------------- tarea 1: decisiones

def test_x02_x03_x04_son_decision_en_los_parametros(raiz):
    p = parametros(raiz)
    for k, valor, fila in (("mostrar_conteo_sien", True, "X-02"), ("cr01_mismo_anio", True, "X-03"), ("intervalo_visible", "uno", "X-04")):
        assert p[k]["valor"] == valor and fila in str(p[k].get("decision")) and "pendiente" not in p[k], k


def test_x02_q2_trae_el_conteo_sien(raiz, motor):
    r = motor.responder(generado(raiz, motor, "q2"))
    t = next(t for t in r["capas"]["capa2"]["mas_contexto"] if t["titulo"] == "Cuántos niños se midieron")
    assert "547" in t["texto"] and "52" in t["texto"]


def test_x03_q3_trae_el_gasto_del_mismo_anio(raiz, motor):
    r = motor.responder(generado(raiz, motor, "q3"))
    claves = {(c["indicador_id"], int(c["anio"]), c["nivel"], str(c["territorio_id"]), c["rol"]) for c in r["cifras"].values()}
    nuevas = [k for k in claves if k[0] == "gasto_ex_pan" and k[1] == 2024 and k[4] == "contexto"]
    assert len(nuevas) == 1 and nuevas[0][2:4] == ("LIMA_METROPOLITANA", "LIMA_METROPOLITANA"), claves


def test_x04_un_solo_intervalo_con_ic_inei_distinto_del_propio(raiz, motor, monkeypatch):
    """Moquegua, pobreza monetaria 2025 (ámbar, la capa 1 muestra el intervalo): el propio redondea a 5–11 y el del INEI a 5–10."""
    f = lambda t: t.replace(" %", "\u202f%")   # noqa: E731
    pedir = lambda: motor.responder(plan_de(raiz, motor, "nivel_actual", "pobreza_monetaria", "departamento de Moquegua"))   # noqa: E731
    uno = pedir()
    c = next(c for c in uno["cifras"].values() if c["rol"] == "principal")
    assert c["ic_inei"] and (round(c["ic_inf"]), round(c["ic_sup"])) != (round(c["ic_inei"]["ic_inf"]), round(c["ic_inei"]["ic_sup"]))
    assert uno["capas"]["capa1"]["cifra_clave"]["valor"] == f("alrededor de 8 % (entre 5 % y 10 %)")     # el del INEI (5,3 a 10,4)
    assert f("entre 5,3 % y 10,4 %") in uno["ficha"]["larga"]["cifras"][uno["capas"]["capa1"]["cifra_clave"]["ids"][0]]["4_precision"] \
        or "5,3" in uno["ficha"]["larga"]["cifras"][uno["capas"]["capa1"]["cifra_clave"]["ids"][0]]["4_precision"]   # la ficha larga trae los dos
    con_parametros(monkeypatch, raiz, intervalo_visible="ambos")
    ambos = pedir()
    assert ambos["capas"]["capa1"]["cifra_clave"]["valor"] == f("alrededor de 8 % (entre 5 % y 11 %)")   # el propio (5,5 a 10,7)
    assert ambos["cifras"] == uno["cifras"]                                               # la cifra no cambia: solo cómo se muestra


# ------------------------------------------------------------------------- tarea 2: enlaces de las citas (P-02)

def _oficial(url: str) -> bool:
    return bool(re.match(r"https://[\w.-]+\.(gob\.pe|gov\.pe)/", url + "/")) or "inei.gob.pe" in url or "ins.gob.pe" in url


@pytest.mark.parametrize("q", ["q1", "q2", "q3", "q4"])
def test_cada_cita_lleva_su_url_oficial(raiz, motor, q):
    r = motor.responder(generado(raiz, motor, q))
    c3 = r["capas"]["capa3"]
    assert [x["texto"] for x in c3["citas"]] == c3["para_citar"]                       # mismas líneas, ahora con su campo `url`
    doradas = {d["id_cifra"]: d["url"] for d in csv.DictReader(open(raiz / "curados" / "capa0" / "cifras_doradas.csv", encoding="utf-8"))}
    assert c3["citas"]
    for x in c3["citas"]:
        assert set(x) >= {"texto", "url", "id_cifra"}
        assert x["url"] == "" or _oficial(x["url"]), x
        o = r["cifras"][x["id_cifra"]].get("contraste_oficial")
        if o:                                                                          # con dorada: la `url` de cifras_doradas.csv
            assert x["url"] == doradas[o["id_cifra"]] and x["url"], x
        else:
            assert x["url"] == "" or x["url"].startswith("https://"), x
    md = F.markdown(r)
    for x in c3["citas"]:
        if x["url"]:
            assert x["url"] in md


def test_sin_cifras_la_cita_no_lleva_enlace(raiz, motor):
    """«No se puede» (la desnutrición no tiene cifra por distrito): no hay qué citar y por tanto no hay enlace."""
    from pap.motor import preguntar as PRE
    r = PRE.preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "desnutricion_cronica", "pregunta_original": "prueba",
                                     "territorio": {"texto": "Ayaviri, Melgar"}})
    c3 = r["capas"]["capa3"]
    assert r["cifras"] == {} and c3["para_citar"] == ["Esta respuesta no publica cifras."]
    assert c3["citas"] == [{"texto": "Esta respuesta no publica cifras.", "url": "", "id_cifra": None}]


# ------------------------------------------------------------------------- tarea 3: rótulos a YAML

def test_rotulos_en_yaml_igual_a_los_de_antes(raiz):
    tx = yaml.safe_load((raiz / "curados" / "motor" / "textos" / "capas.yaml").read_text(encoding="utf-8"))
    assert tx["rotulos"] == ROTULOS_LEGADO
    assert F.rotulos(raiz) == ROTULOS_LEGADO


def test_ficha_no_fija_rotulos_en_el_codigo():
    fuente = (RAIZ_REAL / "src" / "pap" / "motor" / "ficha.py").read_text(encoding="utf-8")
    cuerpo = fuente[fuente.index("def markdown"):fuente.index("## Detalle técnico")]
    for t in ROTULOS_LEGADO.values():
        assert f'"{t}"' not in cuerpo and f"{t}**" not in cuerpo and f"▸ {t}" not in cuerpo, t


@pytest.mark.parametrize("q", ["q1", "q2", "q3", "q4"])
def test_md_usa_los_rotulos_del_yaml(raiz, motor, q, monkeypatch):
    r = motor.responder(generado(raiz, motor, q))
    md = F.markdown(r)
    R = ROTULOS_LEGADO
    for esperado in (f"## ▸ {R['mas_contexto']}", f"**{R['limites']}**", f"## ▸ {R['para_citar']}", f"**{R['como_citar']}**"):
        assert esperado in md
    cambiados = {k: "XX " + v for k, v in R.items()}
    md2 = F.markdown(r, cambiados)
    assert f"## ▸ XX {R['mas_contexto']}" in md2 and f"**XX {R['limites']}**" in md2 and md != md2
    # con los rótulos de siempre (pasados a mano) el .md es idéntico byte a byte
    assert F.markdown(r, R).encode("utf-8") == md.encode("utf-8")


# ------------------------------------------------------------------------- regla de regresión: tarjetas por título

def test_tarjetas_nuevas_no_corren_los_indices_de_las_demas():
    from test_regresion_q1_q4 import indices_por_titulo, textos_capas
    ref = ["A", "B", "C"]
    assert indices_por_titulo(ref, ["A", "B", "C"]) == [0, 1, 2]
    assert indices_por_titulo(ref, ["Nueva", "A", "B", "C"]) == [3, 0, 1, 2]       # una tarjeta nueva al principio no corre las otras
    assert indices_por_titulo(ref, ["A", "Nueva", "B", "C", "Otra"]) == [0, 3, 1, 2, 4]
    assert indices_por_titulo(ref, ["A", "A"]) == [0, 3]                            # un título repetido no se empareja dos veces

    def resp(*titulos):
        return {"capas": {"capa1": {"respuesta_corta": "", "confianza": {"texto": "", "ficha": ""}, "cifra_clave": None,
                                    "ojo_al_leer": [], "que_hacer": None},
                          "capa2": {"mas_contexto": [{"titulo": t, "texto": "texto " + t, "etiqueta": None} for t in titulos],
                                    "avisos": [], "limites": []},
                          "capa3": {"para_citar": [], "glosario": []}}}
    antes, despues = textos_capas(resp(*ref), ref), textos_capas(resp("Nueva", *ref), ref)
    assert {k: v for k, v in despues.items() if "[3]" not in k} == antes                 # las tres de siempre, sin diferencias
    assert despues["capa2.mas_contexto[3].titulo"] == "Nueva"
