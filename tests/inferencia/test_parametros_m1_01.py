"""M1-01 (dueño, 12/11/2026): los parámetros que fijan las decisiones del día, cada uno con su `decision`, y los umbrales nuevos que el
código lee de ellos. Ningún valor se fija en el código (AGENTS.md §6)."""
import yaml

from conftest import RAIZ_REAL
from pap.inferencia import compuertas as cp


def _yaml(ruta):
    return yaml.safe_load((RAIZ_REAL / ruta).read_text(encoding="utf-8"))


def test_parametros_de_inferencia_de_las_decisiones_del_12_de_noviembre():
    p = _yaml("curados/inferencia/parametros.yaml")
    esperado = {("batch", "tope_lote_usd"): 20, ("almacen", "tope_endes_mac_gb"): 2, ("almacen", "tope_endes_repo_privado_gb"): 1.5,
                ("inferencia", "admitir_propuesto_en_sombra"): True, ("compuertas", "paso_no_respuesta_activo"): True}
    for (seccion, clave), valor in esperado.items():
        fila = p[seccion][clave]
        assert fila["valor"] == valor and type(fila["valor"]) is type(valor), (seccion, clave)
        assert fila.get("decision"), f"{seccion}.{clave} necesita `decision` (K-05, C-M0-11-1, K-04 o K-07)"


def test_el_tope_diario_del_llm_en_dolares_esta_en_los_parametros_de_la_web_sin_reemplazar_al_vigente():
    limites = _yaml("curados/web/parametros.yaml")["limites"]
    assert limites["tope_llm_usd_dia"]["valor"] == 5 and limites["tope_llm_usd_dia"].get("decision")
    assert limites["llamadas_llm_por_dia"]["valor"] == 300          # sigue rigiendo hasta que M1-17 lo reemplace


def test_el_interruptor_de_no_respuesta_lo_lee_el_codigo():
    cp.paso_no_respuesta_activo.cache_clear()
    assert cp.paso_no_respuesta_activo() is True
