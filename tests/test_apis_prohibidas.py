"""Control C6 (M0-00b): el código de `src/` no usa las llamadas que ejecutan código ajeno o bajan modelos sin auditar:
`svy_io.read_*`, `from_pretrained`, `trust_remote_code`, `allow_pickle=True`, `pickle.load` y `bm25s.hf`. Sin red.

Los patrones se arman por partes para que este archivo no se encuentre a sí mismo; se busca en el árbol de sintaxis
(llamadas y atributos), así que un comentario o una cadena que nombre la API no cuenta."""
import ast

from conftest import RAIZ_REAL


def _usos(fuente: str) -> list[str]:
    arbol = ast.parse(fuente)
    hallados = []
    for n in ast.walk(arbol):
        if isinstance(n, ast.Attribute):
            nombre = ast.unparse(n)
            if n.attr == "from_" + "pretrained" or nombre.startswith("svy_io.read_") or nombre in ("pickle." + "load", "bm25s." + "hf"):
                hallados.append(nombre)
        elif isinstance(n, ast.Name) and n.id in ("from_" + "pretrained", "trust_remote_" + "code"):
            hallados.append(n.id)
        elif isinstance(n, ast.keyword):
            if n.arg == "trust_remote_" + "code":
                hallados.append(n.arg)
            if n.arg == "allow_" + "pickle" and isinstance(n.value, ast.Constant) and n.value.value is True:
                hallados.append("allow_" + "pickle=True")
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            modulo = n.module if isinstance(n, ast.ImportFrom) else None
            nombres = [a.name for a in n.names]
            if modulo == "bm25s." + "hf" or "bm25s." + "hf" in nombres or modulo == "svy_io" and any(x.startswith("read_") for x in nombres):
                hallados.append(f"import {modulo or nombres}")
            if modulo == "pickle" and "load" in nombres:
                hallados.append("from pickle import load")
    return hallados


def test_src_no_usa_apis_prohibidas():
    archivos = sorted((RAIZ_REAL / "src").rglob("*.py"))
    assert len(archivos) > 30
    usos = {str(p.relative_to(RAIZ_REAL)): u for p in archivos if (u := _usos(p.read_text(encoding="utf-8")))}
    assert not usos, usos


def test_el_detector_encuentra_cada_api():
    casos = ["svy_io.read_sav('x')", "AutoModel.from_" + "pretrained('m')", "f(trust_remote_" + "code=True)",
             "np.load('x', allow_" + "pickle=True)", "pickle." + "load(f)", "import bm25s." + "hf", "from svy_io import read_dta"]
    for c in casos:
        assert _usos(c), c
    assert not _usos("np.load('x', allow_" + "pickle=False)\n# svy_io.read_sav\nx = 'pickle." + "load'")
