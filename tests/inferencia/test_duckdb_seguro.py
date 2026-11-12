"""M0-07: la conexión DuckDB endurecida (diseño §22). Parquet sintéticos en carpetas temporales."""
import duckdb
import polars as pl
import pyarrow as pa
import pytest

from pap.inferencia.duckdb_seguro import ErrorSqlNoPermitido, ParametrosDuckdb, conexion_segura, ejecutar_select


@pytest.fixture
def carpetas(tmp_path):
    permitida, fuera = tmp_path / "permitida", tmp_path / "fuera"
    permitida.mkdir()
    fuera.mkdir()
    pl.DataFrame({"a": [1, 2, 3]}).write_parquet(permitida / "ok.parquet")
    pl.DataFrame({"a": [9]}).write_parquet(fuera / "no.parquet")
    (fuera / "secreto.txt").write_text("secreto")
    return permitida, fuera


def test_lee_los_parquet_de_las_carpetas_permitidas(carpetas):
    permitida, _ = carpetas
    con = conexion_segura(carpetas=[permitida])
    assert con.execute("SELECT sum(a) FROM read_parquet(?)", [str(permitida / "ok.parquet")]).fetchone() == (6,)
    assert con.execute(f"SELECT count(*) FROM '{permitida / 'ok.parquet'}'").fetchone() == (3,)


@pytest.mark.parametrize("consulta", [
    "SELECT * FROM read_text('/etc/hosts')",
    "SELECT * FROM read_csv('/etc/hosts')",
    "SELECT * FROM read_blob('/etc/hosts')",
    "SELECT * FROM glob('/etc/*')",
    "COPY (SELECT 1) TO '{fuera}/salida.csv'",
    "SELECT * FROM read_parquet('{fuera}/no.parquet')",
    "SELECT * FROM read_text('{fuera}/secreto.txt')",
    "ATTACH '{fuera}/otra.duckdb'",
    "INSTALL httpfs",
    "LOAD httpfs",
    "EXPORT DATABASE '{fuera}/export'",
])
def test_lo_que_sale_de_las_carpetas_permitidas_falla(carpetas, consulta):
    permitida, fuera = carpetas
    con = conexion_segura(carpetas=[permitida])
    with pytest.raises(duckdb.Error):
        con.execute(consulta.format(permitida=permitida, fuera=fuera))
    assert not (fuera / "salida.csv").exists()


@pytest.mark.parametrize("ajuste", ["SET enable_external_access=true", "SET allowed_directories=['/']", "SET threads=64",
                                    "SET memory_limit='64GB'", "SET autoload_known_extensions=true", "SET lock_configuration=false"])
def test_la_configuracion_queda_bloqueada(carpetas, ajuste):
    permitida, _ = carpetas
    con = conexion_segura(carpetas=[permitida])
    with pytest.raises(duckdb.Error):
        con.execute(ajuste)
    with pytest.raises(duckdb.Error):
        con.execute("SELECT * FROM read_text('/etc/hosts')")


def test_la_configuracion_sale_de_parametros_yaml(carpetas):
    permitida, _ = carpetas
    p = ParametrosDuckdb.desde_yaml()
    con = conexion_segura(carpetas=[permitida])
    val = lambda k: con.execute(f"SELECT current_setting('{k}')").fetchone()[0]
    assert (p.memoria_mb, p.threads) == (1536, 2) and p.carpetas == ("biblioteca/microdatos", "biblioteca/variables")
    assert val("threads") == p.threads and val("enable_external_access") is False
    assert val("autoinstall_known_extensions") is False and val("autoload_known_extensions") is False
    assert val("lock_configuration") is True and val("memory_limit").startswith("1.4 GiB")      # 1 536 MB


def test_por_defecto_solo_se_leen_los_dos_directorios_del_yaml(tmp_path):
    (tmp_path / "biblioteca" / "microdatos").mkdir(parents=True)
    (tmp_path / "biblioteca" / "variables").mkdir(parents=True)
    (tmp_path / "biblioteca" / "otra").mkdir(parents=True)
    for d in ("microdatos", "variables", "otra"):
        pl.DataFrame({"a": [1]}).write_parquet(tmp_path / "biblioteca" / d / "x.parquet")
    con = conexion_segura(tmp_path)
    for d in ("microdatos", "variables"):
        assert con.execute("SELECT count(*) FROM read_parquet(?)", [str(tmp_path / "biblioteca" / d / "x.parquet")]).fetchone() == (1,)
    with pytest.raises(duckdb.Error):
        con.execute("SELECT count(*) FROM read_parquet(?)", [str(tmp_path / "biblioteca" / "otra" / "x.parquet")])


def test_el_orden_importa_allowed_directories_va_antes_de_apagar_el_acceso(carpetas):
    """Al revés DuckDB da error: con el acceso externo apagado ya no deja fijar los directorios permitidos."""
    permitida, _ = carpetas
    con = duckdb.connect(":memory:")
    con.execute("SET enable_external_access=false")
    with pytest.raises(duckdb.Error):
        con.execute(f"SET allowed_directories=['{permitida}']")
    assert conexion_segura(carpetas=[permitida]) is not None


def test_arrow_devuelve_un_record_batch_reader_que_polars_acepta(carpetas):
    permitida, _ = carpetas
    con = conexion_segura(carpetas=[permitida])
    lector = con.execute("SELECT a FROM read_parquet(?) ORDER BY a", [str(permitida / "ok.parquet")]).arrow()
    assert isinstance(lector, pa.RecordBatchReader)
    df = pl.from_arrow(lector)
    assert df.to_dict(as_series=False) == {"a": [1, 2, 3]}


# ------------------------------------------------------------------ ejecutar_select (H07-1)

def test_ejecutar_select_corre_un_select_con_parametros(carpetas):
    permitida, _ = carpetas
    con = conexion_segura(carpetas=[permitida])
    assert ejecutar_select(con, "SELECT sum(a) FROM read_parquet(?)", [str(permitida / "ok.parquet")]).fetchone() == (6,)


def test_ejecutar_select_rechaza_copy_a_una_carpeta_permitida_y_no_toca_el_archivo(carpetas):
    permitida, _ = carpetas
    con = conexion_segura(carpetas=[permitida])
    destino = permitida / "ok.parquet"
    antes = destino.read_bytes()
    with pytest.raises(ErrorSqlNoPermitido):
        ejecutar_select(con, f"COPY (SELECT 1 AS a) TO '{destino}' (FORMAT parquet)", [])
    assert destino.read_bytes() == antes


def test_ejecutar_select_rechaza_varias_sentencias(carpetas):
    permitida, _ = carpetas
    con = conexion_segura(carpetas=[permitida])
    destino = permitida / "nuevo.csv"
    with pytest.raises(ErrorSqlNoPermitido):
        ejecutar_select(con, f"SELECT 1; COPY (SELECT 2) TO '{destino}'", [])
    assert not destino.exists()


@pytest.mark.parametrize("sql", ["", "CREATE TABLE t AS SELECT 1", "SET threads=1", "INSERT INTO t VALUES (1)"])
def test_ejecutar_select_rechaza_lo_que_no_es_un_select(carpetas, sql):
    permitida, _ = carpetas
    with pytest.raises(ErrorSqlNoPermitido):
        ejecutar_select(conexion_segura(carpetas=[permitida]), sql, [])
