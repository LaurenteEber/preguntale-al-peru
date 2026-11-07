"""S2-06 — `pap preguntar --texto`: una prueba por fila de la tabla de códigos de salida (backlog/slice-2/S2-06-cli.md), con un
LLM FALSO inyectado por `cli._LLM_DE_PRUEBA` (solo pruebas); combinar opciones es un error de uso; `entendimos` va primero
(en pantalla y en el .md) y fuera de las capas en `respuesta.json`; el aviso de recorte va antes de la respuesta; el corrector
no tiene infracciones en `entendimos` ni en los textos de interprete.yaml; y Q1–Q4 por `--texto` con el LLM GRABADO (modo
«reproducir»): si falta la grabación, la prueba FALLA y dice cómo grabarla (README del slice; agents.md §8).

Los códigos salen de `cli.codigo_salida` de parametros_motor.yaml. Si falta el cubo, las pruebas FALLAN (agents.md §8)."""
import json
import os
import subprocess
import sys

import pytest
import yaml

from pap import cli
from pap.config import Rutas
from pap.interprete import interpretar as I
from pap.interprete import llm as L
from pap.motor.preguntar import preguntar_minima
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto
from pap.motor.validador.reglas_etapa8_10 import corrector

import test_regresion_q1_q4 as R
from conftest import RAIZ_REAL

RAIZ = Rutas(RAIZ_REAL).raiz
PAR = yaml.safe_load((RAIZ / "curados/motor/parametros_motor.yaml").read_text(encoding="utf-8"))
COD = PAR["cli"]["codigo_salida"]["valor"]
TX = yaml.safe_load((RAIZ / "curados/motor/textos/interprete.yaml").read_text(encoding="utf-8"))
CLI = yaml.safe_load((RAIZ / "curados/motor/textos/cli.yaml").read_text(encoding="utf-8"))["mensajes"]
ERR = yaml.safe_load((RAIZ / "curados/motor/textos/errores_consulta.yaml").read_text(encoding="utf-8"))["mensajes"]


@pytest.fixture(scope="module")
def motor():
    assert (RAIZ / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    return Motor(cargar_contexto(RAIZ))


@pytest.fixture(autouse=True)
def entorno(monkeypatch, tmp_path):
    """La raíz del proyecto y una caché del intérprete propia de cada prueba (para que no se mezclen LLM falsos)."""
    monkeypatch.setenv("PAP_RAIZ", str(RAIZ))
    monkeypatch.setattr(I, "_CACHE_PYTEST", tmp_path / "cache")


class Falso:
    """LLM falso: devuelve en orden las interpretaciones dadas (la última se repite) o lanza la excepción dada."""

    def __init__(self, *respuestas):
        self.respuestas, self.llamadas = list(respuestas), 0

    def interpretar_crudo(self, prompt, pregunta_limpia, version_prompt, error_previo=None):
        self.llamadas += 1
        x = self.respuestas[min(self.llamadas, len(self.respuestas)) - 1]
        if isinstance(x, Exception):
            raise x
        return L.RespuestaLLM(x, json.dumps(x, ensure_ascii=False), "falso", version_prompt=version_prompt)


def con_llm(monkeypatch, llm):
    monkeypatch.setattr(cli, "_LLM_DE_PRUEBA", lambda raiz: llm)
    return llm


def correr(capsys, *argv):
    codigo = cli.main(["preguntar", *argv])
    c = capsys.readouterr()
    return codigo, c.out, c.err


def consulta(c, **anclas):
    return {"resultado": "consulta", "consulta": c, "anclas": anclas}


APURIMAC = "¿Cuánta anemia hay en Apurímac?"
NIVEL_APURIMAC = consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac"}},
                          intencion="Cuánta", tema="anemia", territorio="Apurímac")
COMO_VA = "¿Cómo va la anemia en Apurímac?"
AMBIGUA = {"resultado": "aclaracion", "motivo": "intencion_ambigua", "opciones": [
    {"consulta": {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac"}},
     "anclas": {"intencion": "Cómo va", "tema": "anemia", "territorio": "Apurímac"}},
    {"consulta": {"intencion": "evolucion", "tema": "anemia", "territorio": {"texto": "Apurímac"}},
     "anclas": {"intencion": "Cómo va", "tema": "anemia", "territorio": "Apurímac"}}]}


def sin_interprete(r):
    return {k: v for k, v in r.items() if k not in ("interpretacion", "entendimos")}


def igual(a, b):
    return json.dumps(sin_interprete(a), sort_keys=True, ensure_ascii=False, default=str) == \
        json.dumps(sin_interprete(b), sort_keys=True, ensure_ascii=False, default=str)


# ------------------------------------------------------------------ fila «respuesta / no se puede»: código 0 y escribe

def test_respuesta_entendimos_primero_y_fuera_de_las_capas(capsys, monkeypatch, tmp_path, motor):
    con_llm(monkeypatch, Falso(NIVEL_APURIMAC))
    codigo, out, err = correr(capsys, "--texto", APURIMAC, "--salida", str(tmp_path / "s"))
    assert codigo == COD["respondida"] == 0 and err == ""
    lineas = out.splitlines()
    assert lineas[0] == "Entendimos: cuánto hay de anemia en el departamento de Apurímac"
    assert lineas[1].startswith("===== nivel_actual__anemia__03 · semáforo: ")
    assert lineas[-1] == f"Respuestas en {tmp_path / 's'}"
    assert sorted(p.name for p in (tmp_path / "s").iterdir()) == ["nivel_actual__anemia__03.json", "nivel_actual__anemia__03.md"]
    r = json.loads((tmp_path / "s" / "nivel_actual__anemia__03.json").read_text(encoding="utf-8"))
    assert next(iter(r)) == "entendimos" and r["entendimos"] == lineas[0]
    assert "entendimos" not in json.dumps(r["capas"], ensure_ascii=False)                  # fuera de las capas
    base = preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac"},
                                    "pregunta_original": APURIMAC, "idioma": "es"})
    assert igual(r, json.loads(json.dumps(base, ensure_ascii=False, default=str)))       # capa 1 sin `entendimos`: mismas palabras
    i = r["interpretacion"]
    assert {"resultado", "consulta", "anclas", "modelo", "version_prompt", "reintentos", "cache"} <= set(i)
    assert i["resultado"] == "consulta" and i["modelo"] == "falso" and i["reintentos"] == 0 and i["cache"] is False
    assert i["consulta"] == {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Apurímac"}}
    assert i["anclas"] == {"intencion": "Cuánta", "tema": "anemia", "territorio": "Apurímac"} and i["version_prompt"]
    assert r["consulta_minima"]["pregunta_original"] == APURIMAC                         # la pregunta limpia (P-03)
    md = (tmp_path / "s" / "nivel_actual__anemia__03.md").read_text(encoding="utf-8").splitlines()
    assert md[0] == r["entendimos"] and md[1] == "" and md[2].startswith("# nivel_actual__anemia__03 — ")


def test_datos_personales_no_se_guardan(capsys, monkeypatch, tmp_path):
    """P-03: en `respuesta.json` solo va la pregunta limpia; el número con forma de DNI no aparece en ninguna parte."""
    con_llm(monkeypatch, Falso(NIVEL_APURIMAC))
    codigo, out, _ = correr(capsys, "--texto", "Mi DNI es 12345678. " + APURIMAC, "--salida", str(tmp_path))
    texto = (tmp_path / "nivel_actual__anemia__03.json").read_text(encoding="utf-8")
    assert codigo == 0 and "12345678" not in texto and "12345678" not in out
    r = json.loads(texto)
    assert r["consulta_minima"]["pregunta_original"] == "Mi DNI es [dato personal]. " + APURIMAC
    assert r["interpretacion"]["datos_personales_quitados"] == 1


def test_fuera_de_alcance_es_no_se_puede_con_codigo_0(capsys, monkeypatch, tmp_path):
    con_llm(monkeypatch, Falso({"resultado": "fuera_de_alcance", "tipo": "pregunta", "pedido": "Por qué hay tanta anemia"}))
    codigo, out, err = correr(capsys, "--texto", "¿Por qué hay tanta anemia en Puno?", "--salida", str(tmp_path))
    assert codigo == COD["no_se_puede"] == 0 and err == ""
    assert out.startswith("===== no_se_puede__interprete_fuera_de_alcance · no se puede")       # sin «Entendimos»: no hay consulta
    [f] = tmp_path.glob("*.json")
    r = json.loads(f.read_text(encoding="utf-8"))
    assert r["tipo"] == "no_se_puede" and r["motivo"]["codigo"] == "interprete_fuera_de_alcance" and r["entendimos"] is None
    assert (tmp_path / f"{f.stem}.md").read_text(encoding="utf-8").startswith("# ")


def test_aviso_de_recorte_va_antes_de_la_respuesta(capsys, monkeypatch, tmp_path):
    con_llm(monkeypatch, Falso(NIVEL_APURIMAC))
    tope = PAR["interprete"]["pregunta_max_caracteres"]["valor"]
    codigo, out, _ = correr(capsys, "--texto", APURIMAC + " " + "a" * (tope + 50), "--salida", str(tmp_path))
    lineas = out.splitlines()
    assert codigo == 0 and lineas[0] == TX["pregunta_recortada"].format(n=tope)
    assert lineas[1].startswith("Entendimos: ") and lineas[2].startswith("===== ")


# ------------------------------------------------------------------ fila «aclaración»: código 2 y no escribe

def test_aclaracion_del_interprete_y_luego_elegir(capsys, monkeypatch, tmp_path):
    con_llm(monkeypatch, Falso(AMBIGUA))
    codigo, out, err = correr(capsys, "--texto", COMO_VA, "--salida", str(tmp_path / "s"))
    lineas = out.splitlines()
    assert codigo == COD["aclaracion"] == 2 and err == "" and not (tmp_path / "s").exists()
    assert lineas[0] == TX["aclaraciones"]["intencion_ambigua"]
    assert lineas[1] == "1) Cómo cambió la anemia en el departamento de Apurímac"
    assert lineas[2] == "2) Cuánto hay de anemia en el departamento de Apurímac"
    assert lineas[3] == CLI["elegir_pista"]
    codigo, out, err = correr(capsys, "--texto", COMO_VA, "--elegir", "2", "--salida", str(tmp_path / "s"))
    assert codigo == 0 and out.startswith("Entendimos: cuánto hay de anemia en el departamento de Apurímac\n")
    assert (tmp_path / "s" / "nivel_actual__anemia__03.json").exists()


def test_aclaracion_de_territorio(capsys, monkeypatch, tmp_path):
    q = "¿Cuánta anemia hay en Abancay?"                                    # X-22: Huancavelica a secas ya no aclara; Abancay es provincia y distrito
    con_llm(monkeypatch, Falso(consulta({"intencion": "nivel_actual", "tema": "anemia", "territorio": {"texto": "Abancay"}},
                                        intencion="Cuánta", tema="anemia", territorio="Abancay")))
    codigo, out, err = correr(capsys, "--texto", q, "--salida", str(tmp_path / "s"))
    lineas = out.splitlines()
    assert codigo == COD["aclaracion"] and err == "" and not (tmp_path / "s").exists()
    assert lineas[0] == "Hay varios lugares llamados «Abancay». ¿Cuál quieres?" and lineas[1] == "1) Abancay (provincia, departamento de Apurímac)"
    assert lineas[-1] == CLI["elegir_pista"]
    codigo, out, _ = correr(capsys, "--texto", q, "--elegir", "1", "--salida", str(tmp_path / "s"))
    assert codigo == 0 and out.startswith("Entendimos: cuánto hay de anemia en la provincia de Abancay (Apurímac)\n")


# ------------------------------------------------------------------ fila «mensaje»: código 2, no escribe, ofrece la vía estructurada

@pytest.mark.parametrize("interp,texto", [
    ({"resultado": "no_es_pregunta"}, TX["no_es_pregunta"]),
    ({"resultado": "otro_idioma"}, ERR["idioma_invalido"]),
    (None, TX["no_entendida"]),                                   # no valida dos veces
], ids=["no_es_pregunta", "otro_idioma", "no_entendida"])
def test_mensajes_fijos_salen_con_2(capsys, monkeypatch, tmp_path, interp, texto):
    con_llm(monkeypatch, Falso(interp))
    codigo, out, err = correr(capsys, "--texto", "hola", "--salida", str(tmp_path / "s"))
    assert codigo == COD["mensaje"] == 2 and err == "" and not (tmp_path / "s").exists()
    assert out == f"{texto} {TX['via_estructurada']}\n"


# ------------------------------------------------------------------ fila «no disponible»: código 3, no escribe

@pytest.mark.parametrize("motivo", ["sin_clave", "caida", "tiempo_agotado", "limite_agotado"])
def test_no_disponible_sale_con_3(capsys, monkeypatch, tmp_path, motivo):
    con_llm(monkeypatch, Falso(L.NoDisponible(motivo)))
    codigo, out, err = correr(capsys, "--texto", APURIMAC, "--salida", str(tmp_path / "s"))
    assert codigo == COD["no_disponible"] == 3 and err == "" and out == TX["no_disponible"] + "\n"
    assert not (tmp_path / "s").exists()


def test_proceso_real_sin_clave_usa_el_cliente_en_vivo_y_sale_con_3(tmp_path):
    """Como lo corre la persona, sin la clave: el cliente en modo «vivo» no llama a la red y el mensaje fijo sale con 3."""
    env = {k: v for k, v in os.environ.items() if k != PAR["interprete"]["variable_clave"]["valor"]}
    p = subprocess.run([sys.executable, "-m", "pap.cli", "preguntar", "--texto", APURIMAC, "--salida", str(tmp_path / "s")],
                       cwd=RAIZ, capture_output=True, text=True, env={**env, "PAP_RAIZ": str(RAIZ)})
    assert p.returncode == 3 and p.stdout == TX["no_disponible"] + "\n" and p.stderr == ""
    assert not (tmp_path / "s").exists()


# ------------------------------------------------------------------ fila «error de uso»: código 1

@pytest.mark.parametrize("extra", [
    ["--tema", "anemia"],
    ["--intencion", "nivel_actual", "--territorio", "Puno"],
    ["--plan"],
    [str(RAIZ / "curados" / "motor" / "consultas_minimas" / "q1.json")],
], ids=["tema", "intencion_territorio", "plan", "archivo"])
def test_texto_con_otras_opciones_es_error_de_uso(capsys, monkeypatch, tmp_path, extra):
    falso = con_llm(monkeypatch, Falso(NIVEL_APURIMAC))
    codigo, out, err = correr(capsys, "--texto", APURIMAC, *extra, "--salida", str(tmp_path / "s"))
    assert codigo == COD["error"] == 1 and out == "" and err == f"✘ {CLI['texto_y_opciones']}\n"
    assert falso.llamadas == 0 and not (tmp_path / "s").exists()


def test_elegir_invalido_es_error_de_uso(capsys, monkeypatch, tmp_path):
    falso = con_llm(monkeypatch, Falso(NIVEL_APURIMAC))
    codigo, out, err = correr(capsys, "--texto", APURIMAC, "--elegir", "1")            # sin caché: nunca se reinterpreta
    assert codigo == COD["error"] and out == "" and err == f"✘ {TX['elegir_vencida']}\n" and falso.llamadas == 0
    assert correr(capsys, "--texto", APURIMAC, "--salida", str(tmp_path))[0] == 0
    codigo, out, err = correr(capsys, "--texto", APURIMAC, "--elegir", "1", "--salida", str(tmp_path / "s"))
    assert codigo == COD["error"] and out == "" and err == f"✘ {CLI['elegir_de_mas_ninguna']}\n"
    assert not (tmp_path / "s").exists()


# ------------------------------------------------------------------ corrector

def test_corrector_sin_infracciones_en_entendimos_y_en_interprete_yaml(capsys, monkeypatch, tmp_path, motor):
    def textos(x):
        if isinstance(x, dict):
            return [t for k, v in x.items() if k != "version" for t in textos(v)]
        if isinstance(x, list):
            return [t for v in x for t in textos(v)]
        return [x] if isinstance(x, str) else []
    todos = textos(TX)
    assert len(todos) > 30
    casos = [(APURIMAC, NIVEL_APURIMAC, []), (COMO_VA, AMBIGUA, ["--elegir", "1"]),
             ("¿Cuál es el distrito más pobre del Perú?",
              consulta({"intencion": "identificar_extremo", "tema": "pobreza_monetaria",
                        "territorio": {"nivel": "distrito", "dentro_de": {"nacional": True}}},
                       intencion="más pobre", tema="pobre", nivel="distrito", dentro_de="del Perú"), []),
             ("¿Hay más desnutrición en Abancay que en Ambo entre 2015 y 2022?",           # X-22: Loreto y Ucayali a secas ya no aclaran
              consulta({"intencion": "comparacion", "tema": "desnutricion_cronica", "territorio": {"texto": "Abancay"},
                        "comparar_con": {"texto": "Ambo"}, "periodo": {"tipo": "serie", "desde": 2015, "hasta": 2022}},
                       intencion="Hay más", tema="desnutrición", territorio="Abancay", comparar_con="Ambo",
                       desde="2015", hasta="2022"), ["--elegir", "1,1"]),
             ("¿Cuánto se gastó contra la anemia en San Juan de Lurigancho y sirvió?",       # efecto en un distrito (Q3)
              consulta({"intencion": "efecto", "tema": "gasto_publico", "territorio": {"texto": "San Juan de Lurigancho"}},
                       intencion="sirvió", tema="gastó", territorio="San Juan de Lurigancho"), []),
             ("¿Sirvió el gasto contra la anemia en San Juan de Lurigancho?",
              consulta({"intencion": "efecto", "tema": "anemia", "territorio": {"texto": "San Juan de Lurigancho"}},
                       intencion="Sirvió", tema="anemia", territorio="San Juan de Lurigancho"), []),
             ("¿Cómo se ven juntos la anemia y el gasto en San Juan de Lurigancho?",
              consulta({"intencion": "cruce", "tema": "anemia", "territorio": {"texto": "San Juan de Lurigancho"}},
                       intencion="se ven juntos", tema="anemia", territorio="San Juan de Lurigancho"), [])]
    for pregunta, interp, extra in casos:
        con_llm(monkeypatch, Falso(interp))
        if extra:
            assert correr(capsys, "--texto", pregunta)[0] == COD["aclaracion"]
        codigo, out, _ = correr(capsys, "--texto", pregunta, *extra, "--salida", str(tmp_path))
        assert codigo == 0 and out.startswith("Entendimos: "), pregunta
        todos.append(out.splitlines()[0])
    malos = [(t, corrector(t, motor.ctx)[0]) for t in todos if corrector(t, motor.ctx)[0]]
    assert not malos, malos


# ------------------------------------------------------------------ Q1–Q4 por --texto, con el LLM grabado

def cumple_regresion(new: dict, ref: dict):
    """Los criterios de tests/test_regresion_q1_q4.py: cifras por clave, semáforos, confianza, parcialidad, comparaciones
    bloqueadas, reglas firmes, capa 1 dentro del máximo y sin infracciones del corrector."""
    rc, nc = R.cifras_por_clave(ref), R.cifras_por_clave(new)
    assert set(nc) == set(rc), set(nc) ^ set(rc)
    for k, (_, c) in nc.items():
        for campo in R.CAMPOS_CIFRA:
            assert R.sin_version(c[campo]) == R.sin_version(rc[k][1][campo]), (k, campo)
    assert new["semaforo_respuesta"] == ref["semaforo_respuesta"]
    assert new["capas"]["capa1"]["confianza"]["nivel"] == ref["capas"]["capa1"]["confianza"]["nivel"]
    assert new["respuesta_parcial"] == ref["respuesta_parcial"]
    ids_ref, ids_new = {i: k for k, (i, _) in rc.items()}, {i: k for k, (i, _) in nc.items()}
    assert sorted(R.texto_clave(ids_new[i]) for i in new["comparaciones_bloqueadas"]) == \
        sorted(R.texto_clave(ids_ref[i]) for i in ref["comparaciones_bloqueadas"])
    firmes = lambda s: {x for x in s if x[2] in R.ACCIONES_FIRMES or x[1] == "accion_final"}   # noqa: E731
    assert firmes(R.reglas_por_clave(new, ids_new)) == firmes(R.reglas_por_clave(ref, ids_ref))
    p = PAR["respuesta"]
    assert new["capas"]["capa1"]["palabras"] <= p["capa1_palabras_max"]["valor"]
    assert not [x for x in new["resultados_respuesta"] if x["regla"] in p["infracciones_corrector"]["valor"] and x["accion"] != "rotular"]


@pytest.mark.parametrize("q", R.QS)
def test_q1_q4_por_texto_con_grabaciones(capsys, monkeypatch, tmp_path, motor, q):
    """La pregunta escrita como en su `pregunta_original`, con el cliente en modo «reproducir» (nunca la red). Q1
    («Huancavelica», X-22) se responde como departamento, sin aclaración. Sin la grabación, FALLA con «falta la grabación»."""
    con_llm(monkeypatch, L.Cliente(RAIZ, modo="reproducir"))
    pregunta = json.loads((RAIZ / "curados" / "motor" / "consultas_minimas" / f"{q}.json").read_text(encoding="utf-8"))["pregunta_original"]
    argv = ["--texto", pregunta, "--salida", str(tmp_path / "s")]
    codigo, out, err = correr(capsys, *argv)
    assert codigo == COD["respondida"] and err == "" and out.startswith("Entendimos: ")
    [f] = (tmp_path / "s").glob("*.json")
    new = json.loads(f.read_text(encoding="utf-8"))
    assert new["tipo"] == "respuesta" and new["consulta_minima"]["pregunta_original"] == pregunta
    ref = json.loads(json.dumps(motor.responder(R.generado(RAIZ, motor, q)), ensure_ascii=False, default=str))
    cumple_regresion(new, ref)
