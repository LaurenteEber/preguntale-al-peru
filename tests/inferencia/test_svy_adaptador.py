"""M0-08: el adaptador de `svy` (único módulo que lo importa) y la fórmula del n efectivo. Sin datos reales."""
import ast
import math

import polars as pl
import pytest

from conftest import RAIZ_REAL
from pap.inferencia.estimacion import Estimacion
from pap.inferencia.svy_adaptador import estimar_proporciones, n_efectivo

from .sintetico_ejecutor import marco_sintetico

PERMITIDOS = {"src/pap/inferencia/svy_adaptador.py", "src/pap/motor/calculo.py"}       # calculo.py es el oráculo y se queda como está


def _importa_svy(fuente: str) -> bool:
    for n in ast.walk(ast.parse(fuente)):
        if isinstance(n, ast.Import) and any(a.name.split(".")[0] == "svy" for a in n.names):
            return True
        if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "svy":
            return True
        if isinstance(n, ast.Call) and ast.unparse(n.func) in ("importlib.import_module", "__import__") and n.args \
                and isinstance(n.args[0], ast.Constant) and str(n.args[0].value).split(".")[0] == "svy":
            return True
    return False


def test_solo_el_adaptador_importa_svy():
    archivos = sorted((RAIZ_REAL / "src").rglob("*.py"))
    assert len(archivos) > 30
    importan = {str(p.relative_to(RAIZ_REAL)) for p in archivos if _importa_svy(p.read_text(encoding="utf-8"))}
    assert importan == PERMITIDOS, importan


def test_el_detector_de_importaciones_de_svy_encuentra_cada_forma():
    for caso in ("import svy", "import svy.estimation", "from svy import Sample", "from svy.core import x", "importlib.import_module('svy')",
                 "def f():\n    import svy"):
        assert _importa_svy(caso), caso
    assert not _importa_svy("import svy_io\nx = 'import svy'\n# import svy")


def test_n_efectivo_es_el_minimo_entre_n_y_la_formula_y_n_si_ee_es_cero():
    assert n_efectivo(0.5, 0.1, 1000) == pytest.approx(25.0)                  # p(1−p)/ee² = 25 < n
    assert n_efectivo(0.5, 0.01, 100) == 100.0                                # 2500 > n: se topa en n
    assert n_efectivo(0.3, 0.0, 77) == 77.0                                   # ee = 0
    assert n_efectivo(None, 0.1, 10) is None and n_efectivo(0.5, math.nan, 10) is None


def _marco_chico() -> pl.DataFrame:
    return marco_sintetico(n_filas=6000, n_dominios=6, semilla=3, n_estratos=8, upm_por_estrato=10)


def test_un_dominio_pedido_y_vacio_sale_con_n_cero_y_sin_datos():
    m = _marco_chico()
    pedidos = [(f"d{i:03d}",) for i in range(6)] + [("d999",)]
    res = estimar_proporciones(m, ["territorio"], pedidos, anio=2024)
    assert [e.dominio for e in res] == pedidos
    vacio = res[-1]
    assert vacio == Estimacion(dominio=("d999",), anio=2024, n=0) and vacio.sin_datos
    assert all(not e.sin_datos and 0 < e.valor < 1 and e.gl > 0 and e.ic_inf < e.valor < e.ic_sup for e in res[:-1])


def test_un_dominio_con_filas_pero_ninguna_en_u_tambien_es_sin_datos():
    m = _marco_chico().with_columns(u=pl.when(pl.col("territorio") == "d002").then(False).otherwise(pl.col("u")),
                                    y=pl.when(pl.col("territorio") == "d002").then(None).otherwise(pl.col("y")))
    res = {e.dominio[0]: e for e in estimar_proporciones(m, ["territorio"], [("d001",), ("d002",)])}
    assert res["d002"].sin_datos and res["d002"].eventos == 0 and not res["d001"].sin_datos


def test_eventos_gl_y_n_cuentan_las_filas_de_u_del_dominio():
    m = _marco_chico()
    res = {e.dominio[0]: e for e in estimar_proporciones(m, ["territorio"], [(f"d{i:03d}",) for i in range(6)])}
    for t, e in res.items():
        d = m.filter((pl.col("territorio") == t) & pl.col("u"))
        assert e.n == d.height and e.eventos == int(d["y"].sum())
        assert e.n_efectivo is not None and e.n_efectivo <= e.n


def test_un_dominio_sin_ningun_si_usa_el_complemento_y_da_cero():
    m = _marco_chico().with_columns(y=pl.when(pl.col("territorio") == "d001").then(pl.when(pl.col("u")).then(0)).otherwise(pl.col("y")))
    e = {e.dominio[0]: e for e in estimar_proporciones(m, ["territorio"], [("d001",), ("d002",)])}["d001"]
    assert e.valor == 0 and e.eventos == 0 and e.ic_inf == pytest.approx(0, abs=1e-12) and e.ic_sup > 0
    assert e.ee == 0 and e.n_efectivo == e.n                                   # ee = 0 → n efectivo = n


def test_un_nulo_de_y_dentro_de_u_es_un_error_del_llamador():
    m = _marco_chico()
    mal = m.with_columns(y=pl.when(pl.int_range(pl.len()) == 0).then(None).otherwise(pl.col("y")), u=pl.when(pl.int_range(pl.len()) == 0).then(True).otherwise(pl.col("u")))
    with pytest.raises(ValueError, match="y nulo"):
        estimar_proporciones(mal, ["territorio"])


def test_la_tasa_de_no_respuesta_solo_se_mide_con_la_columna_faltante():
    m = _marco_chico()
    sin = estimar_proporciones(m, ["territorio"], [("d001",)])[0]
    assert sin.tasa_no_respuesta is None and sin.tasa_no_respuesta_ponderada is None
    # Filas fuera de u marcadas como «faltante»: 1 de cada 5 filas elegibles del dominio.
    con_faltante = m.with_columns(faltante=pl.col("territorio").eq("d001") & ~pl.col("u") & (pl.int_range(pl.len()) % 2 == 0))
    e = estimar_proporciones(con_faltante, ["territorio"], [("d001",)], faltante="faltante")[0]
    d = con_faltante.filter(pl.col("territorio") == "d001")
    nr, u_n = d["faltante"].sum(), d["u"].sum()
    assert e.tasa_no_respuesta == pytest.approx(nr / (nr + u_n))
    w = d.filter(pl.col("faltante") | pl.col("u"))
    assert e.tasa_no_respuesta_ponderada == pytest.approx(w.filter(pl.col("faltante"))["peso"].sum() / w["peso"].sum())
    assert (e.valor, e.ee, e.n) == (sin.valor, sin.ee, sin.n)                  # medir la no respuesta no cambia la cifra


def test_calcular_un_bloque_da_lo_mismo_que_la_llamada_completa():
    m = _marco_chico()
    pedidos = [(f"d{i:03d}",) for i in range(6)]
    todo = estimar_proporciones(m, ["territorio"], pedidos)
    partes = estimar_proporciones(m, ["territorio"], pedidos, solo=pedidos[:3]) + estimar_proporciones(m, ["territorio"], pedidos, solo=pedidos[3:])
    assert [e.dominio for e in partes] == [e.dominio for e in todo]
    for a, b in zip(todo, partes):
        assert (a.n, a.gl, a.eventos) == (b.n, b.gl, b.eventos)
        for campo in ("valor", "ee", "ic_inf", "ic_sup", "deff", "n_efectivo"):
            assert getattr(a, campo) == pytest.approx(getattr(b, campo), abs=1e-12)


def test_dos_columnas_de_dominio_dan_un_dominio_por_combinacion():
    m = _marco_chico().with_columns(corte=pl.when(pl.int_range(pl.len()) % 2 == 0).then(pl.lit("a")).otherwise(pl.lit("b")))
    pedidos = [("d001", "a"), ("d001", "b"), ("d001", "c")]
    res = estimar_proporciones(m, ["territorio", "corte"], pedidos)
    assert [e.dominio for e in res] == pedidos and [e.sin_datos for e in res] == [False, False, True]
