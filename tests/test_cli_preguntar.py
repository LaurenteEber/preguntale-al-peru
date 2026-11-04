"""S1-06 — `pap preguntar` con consulta mínima: archivo JSON (uno, varios o una carpeta), opciones directas, aclaración con
opciones numeradas y `--elegir`, `--plan`, salida por defecto fuera de git, mensajes de una consulta inválida y `--help` en español.
S2-06: la vía estructurada da los mismos `respuesta.json` que la base de S2-00; `--texto` se prueba en tests/interprete/test_cli_texto.py.

Las pruebas llaman a `cli.main` (y una, al proceso real) con la raíz del proyecto; los resultados van a carpetas temporales.
Los códigos de salida salen de `cli.codigo_salida` de parametros_motor.yaml. Si falta el cubo, las pruebas FALLAN (agents.md §8)."""
import hashlib
import json
import subprocess
import sys

import pytest
import yaml

from pap import cli
from pap.config import Rutas

from conftest import RAIZ_REAL

RAIZ = Rutas(RAIZ_REAL).raiz
REFERENCIAS = RAIZ / "tests" / "referencias"
PARAMETROS = yaml.safe_load((RAIZ / "curados" / "motor" / "parametros_motor.yaml").read_text(encoding="utf-8"))
COD = PARAMETROS["cli"]["codigo_salida"]["valor"]
HUANCAVELICA = ["preguntar", "--intencion", "evolucion", "--tema", "anemia", "--territorio", "Huancavelica"]


@pytest.fixture(autouse=True)
def raiz_del_proyecto(monkeypatch):
    assert (RAIZ / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    monkeypatch.setenv("PAP_RAIZ", str(RAIZ))


def correr(capsys, *argv):
    codigo = cli.main(list(argv))
    c = capsys.readouterr()
    return codigo, c.out, c.err


def clave(c):
    return (c["indicador_id"], int(c["anio"]), c["nivel"], str(c["territorio_id"]), c["medida"], c["rol"])


# ------------------------------------------------------------------------- criterios de aceptación

def test_huancavelica_pide_aclarar_y_no_escribe(capsys, tmp_path):
    """Homónimo de departamento, provincia y distrito: imprime las opciones numeradas (el departamento primero, `aclaracion_orden`),
    no escribe ninguna respuesta y sale con el código de aclaración."""
    codigo, out, err = correr(capsys, *HUANCAVELICA, "--salida", str(tmp_path / "s"))
    lineas = out.splitlines()
    assert codigo == COD["aclaracion"] == 2 and err == ""
    assert lineas[0] == "Hay varios lugares llamados «Huancavelica». ¿Cuál quieres?"
    assert lineas[1] == "1) Huancavelica (departamento)"
    assert lineas[2].startswith("2) Huancavelica (provincia") and lineas[3].startswith("3) Huancavelica (distrito")
    assert lineas[4] == "Para responder, repite el comando con --elegir <número>."
    assert not (tmp_path / "s").exists()


def test_elegir_1_responde_como_q1(capsys, tmp_path):
    """Con `--elegir 1` responde como Q1: mismas cifras y semáforos que la referencia (sin la de 2022, C-01); el JSON lleva la
    consulta mínima, el plan generado y la versión de la biblioteca; el markdown va por capas."""
    codigo, out, err = correr(capsys, *HUANCAVELICA, "--elegir", "1", "--salida", str(tmp_path))
    assert codigo == COD["respondida"] == 0 and err == ""
    assert out.startswith("===== evolucion__anemia__09 · semáforo: verde")
    r = json.loads((tmp_path / "evolucion__anemia__09.json").read_text(encoding="utf-8"))
    ref = json.loads((REFERENCIAS / "q1.json").read_text(encoding="utf-8"))
    ad1 = ("endes_anemia_6_35m_oms2024", 2024, "departamento", "09", "proporcion", "contexto")   # AD-1 (S1-13): cifra nueva de Q1
    nuevas = {clave(c): c for c in r["cifras"].values() if clave(c) != ad1}
    assert len(r["cifras"]) == len(nuevas) + 1
    esperadas = {clave(c): c for c in ref["cifras"].values() if clave(c) != ("endes_anemia_6_35m", 2022, "departamento", "09", "proporcion", "contexto")}
    assert set(nuevas) == set(esperadas)
    for k, c in nuevas.items():
        for campo in ("valor", "ic_inf", "ic_sup", "estado_cifra", "semaforo_cifra"):
            assert c[campo] == esperadas[k][campo], (k, campo)
    assert r["semaforo_respuesta"] == ref["semaforo_respuesta"] == "verde"
    assert r["capas"]["capa1"]["confianza"]["nivel"] == ref["capas"]["capa1"]["confianza"]["nivel"]
    assert r["consulta_minima"] == {"intencion": "evolucion", "tema": "anemia", "territorio": {"texto": "Huancavelica"}, "idioma": "es"}
    assert r["plan"]["intencion"] == "evolucion" and r["plan"]["periodo"]["tipo"] == "serie" and r["plan"]["cifras"]
    assert set(r["version_biblioteca"]) == {"cubo", "commit_cubo", "reglas"} and r["version_biblioteca"]["cubo"]
    md = (tmp_path / "evolucion__anemia__09.md").read_text(encoding="utf-8")
    assert "## ▸ Más contexto" in md and "## ▸ Para citar y verificar" in md


def test_carpeta_de_consultas_minimas_responde_q1_a_q4(capsys, tmp_path):
    codigo, out, err = correr(capsys, "preguntar", str(RAIZ / "curados" / "motor" / "consultas_minimas"), "--salida", str(tmp_path))
    assert codigo == 0 and err == ""
    esperado = {"q1": "verde", "q2": "ambar", "q3": "rojo", "q4": "rojo"}                 # semáforos de P3, como Q1–Q4 de hoy
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(f"{q}.{x}" for q in esperado for x in ("json", "md"))
    for q, sem in esperado.items():
        r = json.loads((tmp_path / f"{q}.json").read_text(encoding="utf-8"))
        assert r["tipo"] == "respuesta" and r["semaforo_respuesta"] == sem, q
        assert r["consulta_minima"] and r["plan"] and r["version_biblioteca"]
        assert f"===== {r['consulta']['id']} · semáforo: {sem}" in out


def test_varios_archivos_json(capsys, tmp_path):
    base = RAIZ / "curados" / "motor" / "consultas_minimas"
    codigo, out, _ = correr(capsys, "preguntar", str(base / "q2.json"), str(base / "q3.json"), "--salida", str(tmp_path))
    assert codigo == 0 and sorted(p.name for p in tmp_path.iterdir()) == ["q2.json", "q2.md", "q3.json", "q3.md"]


def test_q_yaml_antiguos_siguen_funcionando(capsys, tmp_path):
    """Los q*.yaml del piloto siguen respondiendo igual (archivadas en consultas/piloto) y escriben `qN.json` y `.md` en --salida."""
    codigo, out, err = correr(capsys, "preguntar", str(RAIZ / "tests" / "fixtures" / "consultas_piloto" / "q2.yaml"), "--salida", str(tmp_path))
    assert codigo == 0 and err == "" and out.startswith("===== Q2 · semáforo: ambar")
    r = json.loads((tmp_path / "q2.json").read_text(encoding="utf-8"))
    assert r["semaforo_respuesta"] == "ambar" and (tmp_path / "q2.md").exists() and r["tipo"] == "respuesta"


def test_salida_por_defecto_no_es_la_del_piloto(capsys, tmp_path, monkeypatch):
    """Sin --salida escribe en `cli.salida_por_defecto` (fuera de git) y no toca las respuestas de referencia del repositorio.
    La prueba redirige esa carpeta por defecto a una carpeta temporal: no escribe ni borra nada dentro del repositorio (S1-09)."""
    import copy
    from pap.motor import plantillas
    piloto = RAIZ / "tests" / "referencias"
    huellas = lambda: {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in piloto.iterdir()}   # noqa: E731
    antes = huellas()
    original = plantillas.parametros
    destino = tmp_path / "salidas" / "preguntar"

    def parametros_con_destino_temporal(raiz):
        par = copy.deepcopy(original(raiz))
        par["cli"]["salida_por_defecto"]["valor"] = str(destino)
        return par
    monkeypatch.setattr(plantillas, "parametros", parametros_con_destino_temporal)
    codigo, out, _ = correr(capsys, "preguntar", str(RAIZ / "tests" / "fixtures" / "consultas_piloto" / "q1.yaml"))
    assert codigo == 0 and (destino / "q1.json").exists() and (destino / "q1.md").exists()
    assert out.splitlines()[-1] == f"Respuestas en {destino}"
    assert huellas() == antes
    valor = PARAMETROS["cli"]["salida_por_defecto"]["valor"]
    assert not valor.startswith(("tests", "curados", "docs"))                         # la carpeta por defecto no es del repositorio
    ignorado = subprocess.run(["git", "check-ignore", "-q", valor + "/q1.json"], cwd=RAIZ)
    assert ignorado.returncode == 0                                                    # .gitignore la cubre


# ------------------------------------------------------------------------- opciones directas

def test_plan_solo_imprime_el_plan(capsys, tmp_path, monkeypatch):
    """`--plan` imprime el plan (JSON) sin calcular ninguna cifra ni escribir nada; el periodo por defecto de `evolucion` es una serie."""
    from pap.motor.respuesta import Motor

    def prohibido(*a, **k):
        raise AssertionError("--plan no calcula")
    monkeypatch.setattr(Motor, "cifra", prohibido)
    codigo, out, err = correr(capsys, "preguntar", "--plan", "--intencion", "evolucion", "--tema", "anemia", "--territorio",
                              "departamento de Huancavelica", "--salida", str(tmp_path / "s"))
    plan = json.loads(out)
    assert codigo == 0 and err == "" and not (tmp_path / "s").exists()
    assert plan["periodo"] == {"tipo": "serie", "desde": 2015, "hasta": "ultimo"} and plan["territorio"]["id"] == "09"
    assert {c["rol"] for c in plan["cifras"]} == {"principal", "contexto"}


@pytest.mark.parametrize("opciones,periodo", [
    ([], {"tipo": "ultimo"}),
    (["--anio", "2024"], {"tipo": "anio", "anio": 2024}),
    (["--desde", "2018", "--hasta", "2024"], None),
])
def test_periodo_de_las_opciones(capsys, opciones, periodo):
    intencion = "evolucion" if "--desde" in opciones else "nivel_actual"
    codigo, out, _ = correr(capsys, "preguntar", "--plan", "--intencion", intencion, "--tema", "desnutricion_cronica",
                            "--territorio", "departamento de Puno", *opciones)
    plan = json.loads(out)
    assert codigo == 0
    assert plan["periodo"] == (periodo or {"tipo": "serie", "desde": 2018, "hasta": 2024})


def test_alias_de_tema_indicador_y_comparar_con(capsys):
    codigo, out, _ = correr(capsys, "preguntar", "--plan", "--intencion", "comparacion", "--tema", "desnutrición",
                            "--territorio", "departamento de Puno", "--comparar-con", "departamento de Cusco")
    plan = json.loads(out)
    assert codigo == 0 and plan["tema"] == "desnutricion_cronica" and plan["territorio_comparado"]["id"] == "08"
    assert plan["consulta_minima"]["tema"] == "desnutricion_cronica" and plan["consulta_minima"]["comparar_con"] == {"texto": "departamento de Cusco"}
    codigo, out, _ = correr(capsys, "preguntar", "--plan", "--intencion", "nivel_actual", "--indicador", "endes_dci_menores_5",
                            "--territorio", "departamento de Puno")
    assert codigo == 0 and json.loads(out)["cifras"][0]["indicador"] == "endes_dci_menores_5"


def test_identificar_extremo_con_nivel(capsys):
    codigo, out, _ = correr(capsys, "preguntar", "--plan", "--intencion", "identificar_extremo", "--tema", "anemia", "--nivel", "departamento")
    plan = json.loads(out)
    assert codigo == 0 and plan["territorio"]["nivel"] == "departamento" and plan["grupos"]


def test_no_se_puede_escribe_su_respuesta_y_sale_con_su_codigo(capsys, tmp_path):
    codigo, out, err = correr(capsys, "preguntar", "--intencion", "nivel_actual", "--tema", "desnutricion_cronica", "--territorio",
                              "Ayaviri, Melgar", "--salida", str(tmp_path))
    assert codigo == COD["no_se_puede"] and err == ""
    assert out.startswith("===== nivel_actual__desnutricion_cronica__210801 · no se puede")
    r = json.loads((tmp_path / "nivel_actual__desnutricion_cronica__210801.json").read_text(encoding="utf-8"))
    assert r["tipo"] == "no_se_puede" and r["motivo"]["codigo"] == "nivel_no_valido" and r["consulta_minima"] and r["plan"]
    md = (tmp_path / "nivel_actual__desnutricion_cronica__210801.md").read_text(encoding="utf-8")
    assert "**Lo más cercano que sí tenemos**" in md and "Por qué no se puede" in md


def test_tema_fuera_del_piloto_se_responde_con_la_lista_de_temas(capsys, tmp_path):
    codigo, out, _ = correr(capsys, "preguntar", "--intencion", "nivel_actual", "--tema", "educacion", "--territorio", "Puno",
                            "--salida", str(tmp_path))
    assert codigo == COD["no_se_puede"] and "Todavía no tenemos datos de ese tema." in out and "anemia" in out


# ------------------------------------------------------------------------- consulta inválida y errores de uso

@pytest.mark.parametrize("argv,mensajes", [
    (["--tema", "anemia", "--territorio", "Puno"], ["No sabemos qué quieres saber"]),
    (["--intencion", "nivel_actual", "--tema", "anemia"], ["Falta el lugar"]),
])
def test_consulta_invalida_mensajes_sencillos(capsys, tmp_path, argv, mensajes):
    codigo, out, err = correr(capsys, "preguntar", *argv, "--salida", str(tmp_path / "s"))
    assert codigo == COD["error"] == 1 and out == ""
    for m in mensajes:
        assert m in err
    assert err.startswith("✘ ") and "Traceback" not in err and not (tmp_path / "s").exists()


def test_consulta_invalida_en_archivo(capsys, tmp_path):
    f = tmp_path / "mala.json"
    f.write_text(json.dumps({"intencion": "adivinar", "tema": "anemia", "territorio": {"texto": "Puno"}}), encoding="utf-8")
    mensajes = yaml.safe_load((RAIZ / "curados" / "motor" / "textos" / "errores_consulta.yaml").read_text(encoding="utf-8"))["mensajes"]
    codigo, out, err = correr(capsys, "preguntar", str(f), "--salida", str(tmp_path / "s"))
    assert codigo == COD["error"] and out == "" and mensajes["intencion_invalida"] in err and "En «mala»:" in err
    assert not (tmp_path / "s").exists()


def test_elegir_invalido_y_sin_nada_que_preguntar(capsys, tmp_path):
    codigo, out, err = correr(capsys, *HUANCAVELICA, "--elegir", "9", "--salida", str(tmp_path / "s"))
    assert codigo == COD["error"] and err == "✘ La opción 9 no existe. Elige un número entre 1 y 3.\n" and not (tmp_path / "s").exists()
    codigo, out, err = correr(capsys, "preguntar")
    assert codigo == COD["error"] and err.startswith("✘ No hay nada que preguntar.")
    codigo, out, err = correr(capsys, "preguntar", "no_existe.json")
    assert codigo == COD["error"] and err == "✘ No encontramos «no_existe.json».\n"
    codigo, out, err = correr(capsys, "preguntar", "--anio", "2024", "--desde", "2018", "--intencion", "nivel_actual")
    assert codigo == COD["error"] and "no los dos" in err
    codigo, out, err = correr(capsys, "preguntar", str(RAIZ / "curados" / "motor" / "consultas_minimas" / "q1.json"), "--intencion", "evolucion")
    assert codigo == COD["error"] and "no las dos cosas a la vez" in err


# ------------------------------------------------------------------------- vía estructurada igual que antes del slice 2 (S2-06)

BASE_ESTRUCTURADA = RAIZ / "backlog" / "slice-2" / "evidencia" / "base_estructurada"


def test_via_estructurada_igual_a_la_base_de_s2_00(tmp_path):
    """Los `respuesta.json` de la vía estructurada, generados con los comandos exactos de `generar.sh`, son iguales a los
    guardados en S2-00, salvo las rutas (la carpeta de salida se reemplaza antes de comparar)."""
    salida = tmp_path / "base"
    p = subprocess.run(["bash", str(BASE_ESTRUCTURADA / "generar.sh"), str(salida)], cwd=RAIZ, capture_output=True, text=True,
                       env={**__import__("os").environ, "PAP_RAIZ": str(RAIZ)})
    assert p.returncode == 0, p.stderr[-2000:]
    esperados = sorted(x.relative_to(BASE_ESTRUCTURADA) for x in BASE_ESTRUCTURADA.rglob("*.json"))
    assert esperados and sorted(x.relative_to(salida) for x in salida.rglob("*.json")) == esperados
    for rel in esperados:
        nuevo = json.loads((salida / rel).read_text(encoding="utf-8").replace(str(salida), "<salida>"))
        assert nuevo == json.loads((BASE_ESTRUCTURADA / rel).read_text(encoding="utf-8")), rel
        assert "entendimos" not in nuevo and "interpretacion" not in nuevo, rel


# ------------------------------------------------------------------------- ayuda y proceso real

def test_help_en_espanol_para_cada_opcion(capsys):
    sub = next(a for a in cli.construir_parser()._actions if getattr(a, "choices", None) and "preguntar" in a.choices).choices["preguntar"]
    opciones = [a for a in sub._actions]
    esperadas = {"--intencion", "--tema", "--indicador", "--territorio", "--anio", "--desde", "--hasta", "--comparar-con", "--elegir",
                 "--plan", "--salida", "--help", "--texto"}
    assert esperadas <= {o for a in opciones for o in a.option_strings}
    for a in opciones:
        assert a.help and len(a.help) > 15, a.option_strings
        assert not any(w in f" {a.help.lower()} " for w in (" the ", " show ", " and ", " exit ")), a.help   # sin inglés
    with pytest.raises(SystemExit) as e:
        cli.main(["preguntar", "--help"])
    assert e.value.code == 0
    ayuda = capsys.readouterr().out
    assert "Muestra esta ayuda y termina" in ayuda and "--elegir N" in ayuda and "show this help" not in ayuda


def test_proceso_real_aclaracion_y_elegir():
    """Como lo corre la persona (`pap preguntar …`): códigos de salida del proceso."""
    base = [sys.executable, "-m", "pap.cli", *HUANCAVELICA]
    p = subprocess.run(base, cwd=RAIZ, capture_output=True, text=True, env={**__import__("os").environ, "PAP_RAIZ": str(RAIZ)})
    assert p.returncode == 2 and p.stdout.splitlines()[1] == "1) Huancavelica (departamento)" and p.stderr == ""
