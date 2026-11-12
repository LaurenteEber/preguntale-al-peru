"""M0-02 (tarea 1): la lista de descargas de la ENDES 2024 cumple lo aprobado en K-01."""
import re
from pathlib import Path

import yaml

from conftest import RAIZ_REAL

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
    assert len(urls) == 13 + len(lista["documentos"])
    assert all(u.startswith(PREFIJO) for u in urls)


def test_documentos_pdf_y_recursos_unicos():
    lista = _lista()
    docs = lista["documentos"]
    assert len(docs) == 7 and all(d["url"].endswith(".pdf") and d["formato"] == "PDF" for d in docs)
    recursos = [x["recurso"] for x in lista["modulos"] + docs]
    assert len(recursos) == len(set(recursos))
    assert all(re.fullmatch(r"endes-2024-[a-z0-9-]+", r) for r in recursos)
    assert lista["pendientes"] == []
