"""M1-02, tarea 9: `COPY … TO` NO falla dentro de las carpetas permitidas; la barrera es `ejecutar_select`. La documentación lo dice."""
import duckdb
import pytest

from pap.inferencia import duckdb_seguro
from pap.inferencia.duckdb_seguro import ErrorSqlNoPermitido, conexion_segura, ejecutar_select


def test_copy_to_dentro_de_las_carpetas_permitidas_si_escribe_y_fuera_falla(tmp_path):
    dentro, fuera = tmp_path / "permitida", tmp_path / "otra"
    dentro.mkdir(), fuera.mkdir()
    con = conexion_segura(tmp_path, carpetas=[dentro])
    con.execute(f"COPY (SELECT 1 AS x) TO '{dentro / 'a.parquet'}' (FORMAT parquet)")          # el SQL crudo SÍ escribe
    assert (dentro / "a.parquet").exists()
    with pytest.raises(duckdb.Error):
        con.execute(f"COPY (SELECT 1 AS x) TO '{fuera / 'b.parquet'}' (FORMAT parquet)")
    assert not (fuera / "b.parquet").exists()


def test_ejecutar_select_es_la_barrera_contra_copy_to(tmp_path):
    permitida = tmp_path / "permitida"
    permitida.mkdir()
    con = conexion_segura(tmp_path, carpetas=[permitida])
    with pytest.raises(ErrorSqlNoPermitido):
        ejecutar_select(con, f"COPY (SELECT 1 AS x) TO '{permitida / 'c.parquet'}' (FORMAT parquet)")
    assert not (permitida / "c.parquet").exists()


def test_el_comentario_del_modulo_dice_la_verdad_y_deja_la_nota_para_m4():
    doc = " ".join(duckdb_seguro.__doc__.split())
    assert "`COPY … TO` y la lectura fuera de las carpetas permitidas fallan" not in doc
    assert "`COPY … TO` no falla dentro de las carpetas permitidas" in doc and "ejecutar_select" in doc
    assert "M4" in doc and "solo lectura" in doc
