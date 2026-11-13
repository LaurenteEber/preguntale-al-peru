"""M1-04, tarea 6: el texto de la pregunta y su referencia entran al índice en `propuesto`; las variables sin pregunta llevan su motivo;
y ningún texto de pregunta llega a una respuesta pública mientras esté en `propuesto`."""
from __future__ import annotations

import re
from pathlib import Path

import polars as pl

RAIZ = Path(__file__).resolve().parents[2]


def _variables():
    S = pl.String
    return pl.DataFrame({"var_id": ["ENDES·2024·REC95·S412", "ENDES·2024·REC95·HHID", "ENDES·2024·REC95·S999", "ENDES·2024·REC95·S500"],
                         "texto_pregunta": [None, None, None, None], "estado": ["propuesto"] * 4}, schema_overrides={"texto_pregunta": S})


def _vinculos():
    return pl.DataFrame([
        {"var_id": "ENDES·2024·REC95·S412", "pregunta_id": "individual:412", "metodo": "llm", "estado": "propuesto", "motivo": "",
         "cuestionario": "individual", "seccion": "SECCIÓN 8", "numero": "412", "pagina": 3, "texto_pregunta": "¿Le hicieron la prueba?"},
        {"var_id": "ENDES·2024·REC95·HHID", "pregunta_id": None, "metodo": "sin_pregunta", "estado": "propuesto", "motivo": "administrativa",
         "cuestionario": None, "seccion": None, "numero": None, "pagina": None, "texto_pregunta": None},
        {"var_id": "ENDES·2024·REC95·S999", "pregunta_id": None, "metodo": "sin_pregunta", "estado": "propuesto", "motivo": "no_encontrada",
         "cuestionario": None, "seccion": None, "numero": None, "pagina": None, "texto_pregunta": None},
    ], schema_overrides={"pagina": pl.Int32, "cuestionario": pl.String, "seccion": pl.String, "numero": pl.String, "texto_pregunta": pl.String,
                         "pregunta_id": pl.String})


def test_el_indice_recibe_texto_referencia_metodo_y_motivo():
    from pap.inferencia.indice import aplicar_vinculos

    df = aplicar_vinculos(_variables(), _vinculos())
    f = {r["var_id"].rsplit("·", 1)[1]: r for r in df.iter_rows(named=True)}
    assert f["S412"]["texto_pregunta"] == "¿Le hicieron la prueba?" and f["S412"]["vinculo_metodo"] == "llm"
    assert f["S412"]["pregunta_ref"] == '{"cuestionario": "individual", "seccion": "SECCIÓN 8", "numero": "412", "pagina": 3}'
    assert f["S412"]["sin_pregunta"] is None and f["S412"]["estado"] == "propuesto"
    assert f["HHID"]["texto_pregunta"] is None and f["HHID"]["sin_pregunta"] == "administrativa"
    assert f["S999"]["sin_pregunta"] == "no_encontrada"
    assert f["S500"]["sin_pregunta"] == "pendiente" and f["S500"]["vinculo_metodo"] is None      # el LLM aún no la miró: no se afirma nada


def test_solo_un_texto_revisado_o_verificado_es_publicable():
    from pap.inferencia.indice import texto_publicable

    assert texto_publicable({"estado": "propuesto", "texto_pregunta": "¿algo?"}) is None
    assert texto_publicable({"estado": "revisado", "texto_pregunta": "¿algo?"}) == "¿algo?"
    assert texto_publicable({"estado": "verificado", "texto_pregunta": "¿algo?"}) == "¿algo?"
    assert texto_publicable({"estado": "revisado", "texto_pregunta": None}) is None


def test_ningun_modulo_de_las_respuestas_lee_el_texto_de_las_preguntas():
    """Hoy ninguna ruta de respuesta (motor, web, intérprete, respuesta) usa `texto_pregunta` ni la referencia de la pregunta: cuando
    alguna lo use (M1-06 en adelante), tiene que pasar por `texto_publicable`. Esta prueba vigila que no se cuele antes."""
    prohibidos = re.compile(r"texto_pregunta|pregunta_ref|vinculo_metodo|cuestionarios\b")
    for carpeta in ("motor", "web", "interprete"):
        for f in (RAIZ / "src/pap" / carpeta).rglob("*.py"):
            for n, linea in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                assert not prohibidos.search(linea) or "ClienteLote" in linea or f.name == "llm.py", f"{f.relative_to(RAIZ)}:{n}: {linea.strip()}"
