"""Prueba permanente (dueño, 5/11/2026): ningún archivo versionado, ni las grabaciones del intérprete, ni la evidencia de los
slices contiene el prefijo de las claves de Anthropic, los de los tokens de GitHub, el nombre de la cabecera de la clave ni la clave de prueba. Sin red.

Los textos que se buscan se arman por partes para que este archivo no se encuentre a sí mismo (y para que
`git diff --cached | grep` sobre el prefijo y la cabecera salga vacío antes de cada commit)."""
import re
import re
import subprocess

from pap.interprete.llm import CABECERA_CLAVE

from conftest import RAIZ_REAL
from interprete.test_llm import CLAVE

PROHIBIDOS = ("sk-" + "ant-", "x-" + "api-key", CLAVE)
# A9 (M0-00b): también los tokens de GitHub (personal clásico, de grano fino y OAuth). Se busca el prefijo seguido del cuerpo
# del token (≥ 20 caracteres), para que la documentación que nombra los prefijos no cuente como fuga.
TOKENS_GITHUB = re.compile(rb"(?:gh" + b"p_|github_" + b"pat_|gh" + b"o_)[A-Za-z0-9_]{20,}")


def _archivos():
    versionados = subprocess.run(["git", "ls-files", "-z"], cwd=RAIZ_REAL, capture_output=True, check=True).stdout.split(b"\0")
    rutas = {RAIZ_REAL / p.decode() for p in versionados if p}
    rutas |= set((RAIZ_REAL / "tests/interprete/grabaciones").rglob("*"))
    rutas |= set((RAIZ_REAL / "backlog").glob("slice-*/evidencia/**/*"))
    return sorted(p for p in rutas if p.is_file())


def test_ningun_archivo_contiene_claves_ni_su_cabecera():
    assert CABECERA_CLAVE == PROHIBIDOS[1]                          # la cabecera que manda el cliente es la que se busca
    archivos = _archivos()
    assert len(archivos) > 100
    fugas = [(str(p.relative_to(RAIZ_REAL)), x) for p in archivos for x in PROHIBIDOS
             if x.encode() in p.read_bytes()]
    assert not fugas, fugas
    tokens = [str(p.relative_to(RAIZ_REAL)) for p in archivos if TOKENS_GITHUB.search(p.read_bytes())]
    assert not tokens, tokens


def test_el_detector_de_tokens_de_github_los_encuentra_y_no_confunde_la_documentacion():
    cuerpo = b"A1b2" * 6
    for prefijo in (b"gh" + b"p_", b"github_" + b"pat_", b"gh" + b"o_"):
        assert TOKENS_GITHUB.search(b"token=" + prefijo + cuerpo)
        assert not TOKENS_GITHUB.search(b"los prefijos " + prefijo + b", etc.")
