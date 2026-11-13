"""M1-04, tarea 1 y 2: lector aislado de PDF (pdfplumber en un subproceso con topes) y análisis de cuestionarios y diccionarios."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from pap.inferencia.almacen import LectorAbortado, Parametros

from .fixtures_m104.pdf_minimo import construir_pdf, pagina_de_diccionario, pagina_de_preguntas


@pytest.fixture
def pdf_preguntas(tmp_path):
    pag1 = pagina_de_preguntas("SECCIÓN 4B. INMUNIZACIÓN Y SALUD", [
        ("325B", "¿Qué método quería usar usted?", ["PÍLDORA........ 03", "DIU........ 04"], ""),
        ("326", "VERIFIQUE 320: esterilización", ["SI........ 1", "NO........ 2"], "330"),
    ])
    pag2 = pagina_de_preguntas(None, [
        ("327", "¿Dónde obtuvo usted el método?", ["HOSPITAL MINSA........ 10"], "999"),
        ("330", "¿Cuándo dejó de usarlo?", [], ""),
    ])
    # la carátula trae recuadros numerados antes de la primera sección: no son preguntas
    caratula = {"texto": [(39, 50, "6"), (71, 50, "DISCAPACITADA Ver 7 OTRA")]}              # sin el encabezado de preguntas
    ruta = tmp_path / "cuestionario.pdf"
    ruta.write_bytes(construir_pdf([caratula, pag1, pag2]))
    return ruta


def test_el_lector_aislado_devuelve_las_palabras_con_su_posicion(pdf_preguntas):
    from pap.inferencia.cuestionarios import leer_pdf

    paginas = leer_pdf(pdf_preguntas, Parametros.desde_yaml())
    assert [p["n"] for p in paginas] == [1, 2, 3]
    palabras = {w[0]: w for w in paginas[1]["palabras"]}
    assert "325B" in palabras and 38 <= palabras["325B"][1] <= 41      # x0 del número de pregunta
    assert paginas[1]["tablas"] == []                                   # sin pedir tablas, no se buscan


def test_el_lector_aislado_respeta_los_topes_de_tiempo(pdf_preguntas):
    from pap.inferencia.cuestionarios import leer_pdf

    p = replace(Parametros.desde_yaml(), tiempo_s=0.001)
    with pytest.raises(LectorAbortado, match="tiempo"):
        leer_pdf(pdf_preguntas, p)


def test_un_pdf_dañado_da_un_error_claro_y_no_un_volcado(tmp_path):
    from pap.errores import PapError
    from pap.inferencia.cuestionarios import leer_pdf

    malo = tmp_path / "malo.pdf"
    malo.write_bytes(b"%PDF-1.4\nesto no es un pdf")
    with pytest.raises(PapError, match="malo.pdf"):
        leer_pdf(malo, Parametros.desde_yaml())


def test_las_preguntas_salen_con_numero_texto_opciones_salto_seccion_y_pagina(pdf_preguntas):
    from pap.inferencia.cuestionarios import leer_pdf, preguntas_de_paginas

    paginas = leer_pdf(pdf_preguntas, Parametros.desde_yaml())
    qs = preguntas_de_paginas(paginas, cuestionario="individual")
    assert [q.numero for q in qs] == ["325B", "326", "327", "330"]       # sin el recuadro «6» de la carátula
    q = qs[0]
    assert q.texto == "¿Qué método quería usar usted?"
    assert q.seccion == "SECCIÓN 4B. INMUNIZACIÓN Y SALUD" and q.pagina == 2 and q.cuestionario == "individual"
    assert q.opciones == ["03 PÍLDORA", "04 DIU"]
    assert qs[1].saltos == ["330"]
    assert qs[2].saltos == []                       # «999» no es una pregunta del cuestionario: el salto no vale
    # la sección sigue vigente en la página siguiente, que no la repite
    assert qs[2].seccion == "SECCIÓN 4B. INMUNIZACIÓN Y SALUD" and qs[2].pagina == 3


def test_una_pregunta_repetida_en_dos_paginas_queda_una_vez_con_el_texto_mas_largo(tmp_path):
    from pap.inferencia.cuestionarios import leer_pdf, preguntas_de_paginas

    a = pagina_de_preguntas("SECCIÓN 8. SALUD BUCAL", [("806", "En los últimos 12 meses", [], "")])
    b = pagina_de_preguntas(None, [("806", "En los últimos 12 meses ¿recibió dental?", ["SI.... 1", "NO.... 2"], "")])
    ruta = tmp_path / "rep.pdf"
    ruta.write_bytes(construir_pdf([a, b]))
    qs = preguntas_de_paginas(leer_pdf(ruta, Parametros.desde_yaml()), "salud")
    assert [q.numero for q in qs] == ["806"] and "dental" in qs[0].texto and qs[0].pagina == 2


def test_el_diccionario_da_variable_etiqueta_categorias_y_rango(tmp_path):
    from pap.inferencia.cuestionarios import diccionario_de_paginas, leer_pdf

    filas = [
        ("1", "ID1", "Año", "N", "4", "", "", "", ""),
        ("2", "HC57", "Nivel de anemia", "N", "1", "1:4", "1", "Grave", ""),
        ("", "", "", "", "", "", "2", "Moderar", ""),
        ("", "", "", "", "", "", "4", "Sin anemia", ""),
        ("3", "HC1", "Edad en meses", "N", "2", "0:59", "", "", ""),
    ]
    ruta = tmp_path / "dic.pdf"
    ruta.write_bytes(construir_pdf([pagina_de_diccionario(filas)]))
    paginas = leer_pdf(ruta, Parametros.desde_yaml(), tablas=True)
    vs = diccionario_de_paginas(paginas, tabla="RECH6")
    assert [v.codigo for v in vs] == ["ID1", "HC57", "HC1"]
    hc57 = vs[1]
    assert hc57.etiqueta == "Nivel de anemia" and hc57.rango == "1:4" and hc57.tabla == "RECH6"
    assert hc57.categorias == [("1", "Grave"), ("2", "Moderar"), ("4", "Sin anemia")]
    assert vs[2].categorias == []


def test_una_pagina_de_columnas_del_listado_da_una_pregunta_de_tipo_matriz(tmp_path):
    from pap.inferencia.cuestionarios import leer_pdf, preguntas_de_paginas

    texto = [(37, 15, "SECCIÓN 1. CARACTERÍSTICAS DE LOS MIEMBROS DEL HOGAR"), (60, 60, "¿Durmió anoche aquí?"),
             (200, 60, "¿Es hombre o mujer?")]
    texto += [(21, 100, "(1)"), (83, 100, "(2)"), (180, 100, "(3)"), (240, 100, "(4)")]
    texto += [(25, 120, "01 1 2 1 2")]                   # una fila de datos: no es una pregunta
    ruta = tmp_path / "matriz.pdf"
    ruta.write_bytes(construir_pdf([{"texto": texto}]))
    qs = preguntas_de_paginas(leer_pdf(ruta, Parametros.desde_yaml()), "hogar")
    assert [(q.numero, q.tipo, q.pagina) for q in qs] == [("M1", "matriz", 1)]
    assert "Durmió anoche" in qs[0].texto and "hombre o mujer" in qs[0].texto and qs[0].cuestionario == "hogar"


def test_las_preguntas_de_antes_de_la_seccion_1_se_conservan_si_la_pagina_tiene_el_encabezado_de_preguntas(tmp_path):
    from pap.inferencia.cuestionarios import leer_pdf, preguntas_de_paginas

    ruta = tmp_path / "salud.pdf"
    ruta.write_bytes(construir_pdf([pagina_de_preguntas(None, [("25B", "¿Usted se considera quechua?", ["QUECHUA.... 1"], "")]),
                                    pagina_de_preguntas("SECCIÓN 1. HIPERTENSIÓN", [("100", "¿Le midieron la presión?", [], "")])]))
    qs = preguntas_de_paginas(leer_pdf(ruta, Parametros.desde_yaml()), "salud")
    assert [(q.numero, q.seccion) for q in qs] == [("25B", ""), ("100", "SECCIÓN 1. HIPERTENSIÓN")]


def test_el_manual_solo_da_fragmentos_de_las_preguntas_pedidas_y_no_se_guarda_entero(tmp_path):
    from pap.inferencia.cuestionarios import fragmentos_del_manual, leer_pdf

    pag1 = {"texto": [(40, 50, "Cuando la respuesta a la pregunta 412 es NO, pase a la pregunta 413."), (40, 70, "Otro asunto sin relación.")]}
    pag2 = {"texto": [(40, 50, "La pregunta 999 no se menciona en ningún otro lado.")]}
    ruta = tmp_path / "manual.pdf"
    ruta.write_bytes(construir_pdf([pag1, pag2]))
    r = fragmentos_del_manual(leer_pdf(ruta, Parametros.desde_yaml()), ["412", "700"], ancho=60)
    assert set(r) == {"412", "700"} and r["700"] == []
    [f] = r["412"]
    assert f["pagina"] == 1 and "pase a la pregunta 413" in f["texto"] and len(f["texto"]) <= 130
    assert "Otro asunto" not in f["texto"]
