"""M1-02, tarea 5 (H06-3, H10-2): `validar-tablas` y `validar-recetas` fallan si falta el índice de variables; no se saltan la comprobación."""
import shutil

import pytest

from conftest import RAIZ_REAL
from pap.cli import cmd_inferencia, construir_parser
from pap.config import Rutas
from pap.inferencia import recetas, tablas_curadas as tc


@pytest.fixture
def sin_indice(tmp_path):
    for rel in ("curados/inferencia", "curados/capa0/dim_indicador.yaml", "curados/capa0/cifras_doradas.csv"):
        origen, destino = RAIZ_REAL / rel, tmp_path / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(origen, destino, ignore=shutil.ignore_patterns("descargas")) if origen.is_dir() else shutil.copy(origen, destino)
    assert not (tmp_path / "biblioteca" / "variables" / "variables.parquet").exists()
    return tmp_path


def _con_indice_falta(errores):
    return [e for e in errores if "índice de variables" in e and "falta" in e]


def test_validar_tablas_estricto_marca_error_si_falta_el_indice(sin_indice):
    res = tc.validar(Rutas(sin_indice), exigir_indice=True)
    con_error = {t for t, (_, e) in res.items() if _con_indice_falta(e)}
    assert {"universos_analiticos", "territorios", "cortes_estandar"} <= con_error


def test_validar_recetas_estricto_marca_error_en_cada_receta_si_falta_el_indice(sin_indice):
    res = recetas.validar(Rutas(sin_indice), exigir_indice=True)
    assert res and all(_con_indice_falta(e) for _, e in res.values())


@pytest.mark.parametrize("accion", ["validar-tablas", "validar-recetas"])
def test_el_comando_sale_con_error_y_lo_dice_si_falta_el_indice(sin_indice, accion, capsys):
    a = construir_parser().parse_args(["inferencia", accion])
    assert cmd_inferencia(a, Rutas(sin_indice)) == 1
    assert "índice de variables" in capsys.readouterr().out


def test_sin_exigir_el_indice_la_validacion_de_biblioteca_sigue_como_antes(sin_indice):
    """PRESERVE: quien llama a `validar` sin `exigir_indice` (las pruebas con copias) no recibe el error nuevo."""
    assert not any(_con_indice_falta(e) for _, e in tc.validar(Rutas(sin_indice)).values())
    assert not any(_con_indice_falta(e) for _, e in recetas.validar(Rutas(sin_indice)).values())
