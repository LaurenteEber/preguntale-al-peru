"""Las recetas versionadas del repositorio: todas pasan su esquema y cubren la Ola 0 del catálogo."""
import json

from pap import recetas
from pap.config import Rutas

from conftest import RAIZ_REAL

RUTAS = Rutas(RAIZ_REAL)


def test_todas_las_recetas_pasan_su_esquema():
    archivos = recetas.listar(RUTAS)
    assert archivos
    fallas = {p.stem: recetas.errores(recetas.leer(p), p) for p in archivos}
    assert {k: v for k, v in fallas.items() if v} == {}


def test_cubren_la_ola_0():
    catalogo = json.loads(RUTAS.catalogo.read_text(encoding="utf-8"))
    ola0 = {f["id"] for f in catalogo if f.get("ola") == "0_base"}
    assert len(ola0) == 19   # 16 + BCRP-IPC-LIMA, INEI-PROYECCIONES-DISTRITAL-2018-2022, PROPIO-... (8/10/2026)
    presentes = {p.stem for p in recetas.listar(RUTAS)}
    assert ola0 <= presentes
    assert "PROPIO-ESTADISTICAS-SOCIALES-2020" in presentes


def test_bloque_catalogo_coincide_con_catalogo_y_reglas():
    """Una sola fuente de verdad: el bloque `catalogo:` de cada receta es copia del catálogo (ola, estrategia,
    compuerta) y de R-DEP-01 (bloquea_mvp). Si falla: `pap recetas sincronizar`."""
    assert recetas.incoherencias_catalogo(RUTAS) == []


def test_bloqueantes_se_leen_de_reglas():
    reglas = json.loads((RAIZ_REAL / "reglas" / "reglas.json").read_text(encoding="utf-8"))
    dep = next(r for r in reglas["reglas"] if r["id"] == "R-DEP-01")
    assert recetas.bloqueantes_mvp(RUTAS) == set(dep["parametros"]["insumos_bloqueantes_mvp"])
    assert not hasattr(recetas, "BLOQUEAN_MVP")   # sin copia en el código


def test_compuerta_aprobada_por_captura_verificada():
    """Decisión del 8/10/2026: CPV2017, Directorio y proyección 2018–2026 quedan aprobadas por captura verificada."""
    cat = {f["id"]: f for f in json.loads(RUTAS.catalogo.read_text(encoding="utf-8"))}
    for sid in ("INEI-CPV2017", "INEI-DIRECTORIO-MUNICIPALIDADES", "INEI-PROYECCIONES-POBLACION-DISTRITAL",
                "BCRP-IPC-LIMA", "INEI-PROYECCIONES-DISTRITAL-2018-2022", "PROPIO-ESTADISTICAS-SOCIALES-2020"):
        f = cat[sid]
        assert (f["compuerta_ingesta"], f["estado_ingesta"], f["base_aprobacion"]) == (
            "aprobada", "capturada_verificada_capa0", "captura_verificada"), sid
        assert f["evidencia_ingesta"]["huellas"] and f["evidencia_ingesta"]["capturas"], sid
    assert "MEF-FOTO-PIM-MENSUAL" not in cat


def test_generador_reproduce_las_recetas(tmp_path):
    """Regenerar desde el catálogo da las mismas recetas (salvo las editadas a mano)."""
    import shutil
    (tmp_path / "catalogo").mkdir()
    shutil.copy(RUTAS.catalogo, tmp_path / "catalogo" / "catalogo_fuentes.json")
    (tmp_path / "reglas").mkdir()
    shutil.copy(RAIZ_REAL / "reglas" / "reglas.json", tmp_path / "reglas" / "reglas.json")
    escritas, _ = recetas.generar_desde_catalogo(Rutas(tmp_path))
    for p in escritas:
        real = RUTAS.recetas / p.name
        if "con `pap recetas generar`" in real.read_text(encoding="utf-8").splitlines()[0]:
            assert recetas.leer(p) == recetas.leer(real), p.name
