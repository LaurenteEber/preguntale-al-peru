"""M0-02 (tarea 1): la lista de descargas de la ENDES 2024 cumple lo aprobado en K-01."""
import re
from pathlib import Path, PurePosixPath

import pytest
import yaml

from conftest import RAIZ_REAL
from pap import almacen, capturas
from pap.config import Rutas
from pap.zip_seguro import abrir_zip_seguro

LISTA = Path(RAIZ_REAL) / "curados/inferencia/descargas/endes_2024.yaml"
PREFIJO = "https://proyectos.inei.gob.pe/"


def _lista():
    return yaml.safe_load(LISTA.read_text(encoding="utf-8"))


def test_trece_modulos_1629_a_1641():
    mods = _lista()["modulos"]
    assert [m["codigo"] for m in mods] == list(range(1629, 1642))
    assert all(m["formato"] == "STATA" for m in mods)
    for m in mods:
        assert m["url"].endswith(f"/descarga/STATA/968-Modulo{m['codigo']}.zip")


def test_solo_hogar_y_anemia_ya_registrados():
    ya = {m["codigo"]: m["recurso"] for m in _lista()["modulos"] if m.get("ya_registrado")}
    assert ya == {1629: "endes-2024-hogar", 1638: "endes-2024-anemia"}


def test_todas_las_url_son_del_inei_https():
    lista = _lista()
    urls = [m["url"] for m in lista["modulos"]] + [d["url"] for d in lista["documentos"]]
    assert len(urls) == 13 + len(lista["documentos"]) == 23
    assert all(u.startswith(PREFIJO) for u in urls)


def test_documentos_pdf_y_recursos_unicos():
    lista = _lista()
    docs = lista["documentos"]
    assert len(docs) == 10 and all(d["url"].endswith(".pdf") and d["formato"] == "PDF" for d in docs)
    recursos = [x["recurso"] for x in lista["modulos"] + docs]
    assert len(recursos) == len(set(recursos))
    assert all(re.fullmatch(r"endes-2024-[a-z0-9-]+", r) for r in recursos)
    assert {d["recurso"] for d in docs} >= {
        "endes-2024-manual-entrevistadora", "endes-2024-manual-antropometrista", "endes-2024-identificadores-bd"}
    assert lista["pendientes"] == []


# ------------------------------------------------------------------ M1-00 (tareas 4 a 6)

def test_encuesta_con_codigo_y_nombre_del_periodo():
    enc = _lista()["encuesta"]
    assert enc == {"anio": 2024, "codigo": 968, "periodo_codigo": 5, "periodo_nombre": "Unico"}
    assert "periodo" not in enc


def test_codigo_documento_unico_de_1_a_11_sin_el_10():
    codigos = [d["codigo_documento"] for d in _lista()["documentos"]]
    assert sorted(codigos) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 11]
    por_codigo = {d["codigo_documento"]: d["recurso"] for d in _lista()["documentos"]}
    assert por_codigo[7] == "endes-2024-ficha-tecnica" and por_codigo[1] == "endes-2024-cuestionario-hogar"
    assert por_codigo[11] == "endes-2024-identificadores-bd"


def test_documentos_adicionales_fuera_del_listado_2024():
    extra = {d["recurso"]: d for d in _lista()["documentos_adicionales"]}
    assert set(extra) == {"endes-2025-ficha-tecnica", "endes-2024-informe-ppr"}
    ficha = extra["endes-2025-ficha-tecnica"]
    assert ficha["url"] == "https://proyectos.inei.gob.pe/iinei/srienaho/Descarga/FichaTecnica/1038-Ficha.pdf"
    assert ficha["encuesta_codigo"] == 1038 and ficha["formato"] == "PDF"
    informe = extra["endes-2024-informe-ppr"]
    assert informe["formato"] == "PDF" and "codigo_documento" not in informe
    assert informe.get("url") is None  # sin URL oficial conocida (supuesto en consultas_al_dueno.md)
    assert "codigo_documento" not in ficha


def test_tablas_34_y_unicas():
    mods = _lista()["modulos"]
    assert all(m["tablas"] for m in mods)
    todas = [t for m in mods for t in m["tablas"]]
    assert len(todas) == 34 and len(set(todas)) == 34
    assert not any(t.lower().endswith(".dta") or t.endswith("_2024") for t in todas)


@pytest.mark.solo_mac
def test_tablas_iguales_a_los_dta_de_cada_zip_registrado():
    """Necesita los ZIP en el almacén: si faltan, FALLA (no se salta)."""
    rutas = Rutas(RAIZ_REAL)
    recs = {}
    for _, rec in capturas.recursos(rutas, "INEI-ENDES"):
        recs[rec["name"]] = rec  # la última captura de cada recurso
    for m in _lista()["modulos"]:
        assert m["recurso"] in recs, f"falta el ZIP {m['recurso']} en el almacén"
        ruta = almacen.resolver(rutas, recs[m["recurso"]]["path"])
        assert ruta.exists(), f"falta el crudo de {m['recurso']}"
        with abrir_zip_seguro(ruta) as z:
            dta = sorted(
                re.sub(r"_2024$", "", PurePosixPath(n).stem) for n in z.miembros() if n.lower().endswith(".dta"))
        assert dta == sorted(m["tablas"]), m["recurso"]
