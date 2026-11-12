"""M0-08: el ejecutor en el mismo proceso (sin pool): años según `relacion_entre_anios.csv`, llamada partida, nulo de `y`, plan real
sintético. El pool tiene sus pruebas en `test_pool_ejecutor.py`; las de datos reales, en `test_ejecutor_microdatos.py`."""
import logging
from dataclasses import replace

import polars as pl
import pytest

from conftest import RAIZ_REAL
from pap.inferencia.duckdb_seguro import conexion_segura
from pap.inferencia.ejecutor import Ejecutor, ErrorInterno, ErrorTemporal, FuenteMemoria, Tarea, grupos_de_anios
from pap.inferencia.svy_adaptador import estimar_proporciones
from pap.inferencia.tablas_curadas import leer_relacion_entre_anios
from pap.inferencia.verificador import Falla, verificar

from .recetas_m0 import plan_anemia
from .sintetico_ejecutor import marco_sintetico
from .sintetico_m0 import contexto_sintetico

RELACIONES = leer_relacion_entre_anios(RAIZ_REAL)
CAMPOS = ("valor", "ee", "ic_inf", "ic_sup", "deff", "n_efectivo")


def _marco(semilla: int) -> pl.DataFrame:
    return marco_sintetico(n_filas=4000, n_dominios=5, semilla=semilla, n_estratos=6, upm_por_estrato=12)


def _igual(a, b, tol=1e-12):
    assert (a.dominio, a.anio, a.n, a.gl, a.eventos) == (b.dominio, b.anio, b.n, b.gl, b.eventos)
    for c in CAMPOS:
        assert getattr(a, c) == pytest.approx(getattr(b, c), abs=tol)


# ------------------------------------------------------------------ años

def test_los_anios_se_agrupan_segun_relacion_entre_anios():
    assert grupos_de_anios("ENDES", [2024], RELACIONES) == [(2024,)]
    assert grupos_de_anios("ENDES", [2023, 2024], RELACIONES) == [(2023, 2024)]                  # conglomerados_repetidos
    assert grupos_de_anios("ENDES", [2024, 2025], RELACIONES) == [(2024,), (2025,)]               # independiente
    assert grupos_de_anios("ENDES", [2025, 2023, 2024], RELACIONES) == [(2023, 2024), (2025,)]
    assert grupos_de_anios("ENDES", [2021, 2022, 2023], RELACIONES) == [(2021,), (2022,), (2023,)]     # sin fila: independiente (§7.4)
    assert grupos_de_anios("ENAHO", [2023, 2024], RELACIONES) == [(2023,), (2024,)]


def test_anios_independientes_dan_lo_mismo_que_cada_anio_por_separado():
    marcos = {2024: _marco(1), 2025: _marco(2)}
    ex = Ejecutor(relaciones=RELACIONES)
    juntos = ex.estimar(FuenteMemoria(marcos), "ENDES", [2024, 2025])
    por_separado = [e for a in (2024, 2025) for e in estimar_proporciones(marcos[a], ["territorio"], [(f"d{i:03d}",) for i in range(5)], anio=a)]
    assert len(juntos) == len(por_separado) == 10 and {e.anio for e in juntos} == {2024, 2025}
    for a, b in zip(juntos, por_separado):
        _igual(a, b, 0)


def test_conglomerados_repetidos_apila_un_solo_sample_con_la_upm_estable():
    # La UPM del año (`upm`) es distinta en cada año; la estable (`upm_estable`) es la misma: el apilado debe usar la estable.
    base = {a: _marco(a) for a in (2023, 2024)}
    marcos = {a: m.with_columns(upm_estable=pl.col("upm"), upm=pl.col("upm") + f"-{a}") for a, m in base.items()}
    res = Ejecutor(relaciones=RELACIONES).estimar(FuenteMemoria(marcos), "ENDES", [2023, 2024])
    apilado = pl.concat([m.drop("upm").rename({"upm_estable": "upm"}).with_columns(anio=pl.lit(str(a))) for a, m in marcos.items()])
    pedidos = [(str(a), f"d{i:03d}") for a in (2023, 2024) for i in range(5)]
    esperado = estimar_proporciones(apilado, ["anio", "territorio"], pedidos)
    assert [(e.anio, e.dominio) for e in res] == [(int(d[0]), d[1:]) for d in pedidos]
    for a, b in zip(res, esperado):
        assert (a.n, a.gl, a.valor, a.ee, a.ic_inf) == (b.n, b.gl, b.valor, b.ee, b.ic_inf)
    # La estimación por dominio no cambia al apilar (la covarianza entre años solo entra en las comparaciones, M1/M2); lo que
    # importa es que el ejecutor pida la UPM estable cuando apila y la del año cuando calcula año por año.


def test_el_ejecutor_pide_la_upm_estable_solo_al_apilar():
    class Espia(FuenteMemoria):
        pedidos: list = []

        def cargar(self, anio, *, upm_estable=False):
            Espia.pedidos.append((anio, upm_estable))
            return super().cargar(anio, upm_estable=upm_estable)

    marcos = {a: _marco(a) for a in (2023, 2024, 2025)}
    Ejecutor(relaciones=RELACIONES).estimar(Espia(marcos), "ENDES", [2023, 2024])
    assert Espia.pedidos == [(2023, True), (2024, True)]
    Espia.pedidos = []
    Ejecutor(relaciones=RELACIONES).estimar(Espia(marcos), "ENDES", [2024, 2025])
    assert Espia.pedidos == [(2024, False), (2025, False)]


def test_dominios_pedidos_de_un_anio_que_no_los_tiene_salen_sin_datos_en_el_apilado():
    marcos = {2023: _marco(1), 2024: _marco(2).filter(pl.col("territorio") != "d004")}
    res = Ejecutor(relaciones=RELACIONES).estimar(FuenteMemoria(marcos), "ENDES", [2023, 2024])
    vacio = [e for e in res if e.anio == 2024 and e.dominio == ("d004",)]
    assert len(res) == 10 and len(vacio) == 1 and vacio[0].sin_datos


# ------------------------------------------------------------------ llamada partida

class PoolFalso:
    """Falla las llamadas completas con la causa dada y deja pasar los bloques (o falla también los bloques)."""

    def __init__(self, causa="tiempo", falla_bloques=False):
        self.causa, self.falla_bloques, self.llamadas = causa, falla_bloques, []

    def ejecutar(self, trabajo):
        self.llamadas.append(trabajo.bloque)
        if trabajo.bloque is None or self.falla_bloques:
            raise ErrorTemporal(self.causa, "simulado")
        return trabajo()


@pytest.mark.parametrize("causa", ["tiempo", "memoria"])
def test_si_se_excede_la_llamada_se_parte_en_dos_bloques_y_da_lo_mismo(causa):
    fuente = FuenteMemoria({2024: _marco(5)})
    pool = PoolFalso(causa)
    res = Ejecutor(pool, relaciones=RELACIONES).estimar(fuente, "ENDES", [2024])
    assert pool.llamadas == [None, (0, 2), (1, 2)]
    completo = Ejecutor(relaciones=RELACIONES).estimar(fuente, "ENDES", [2024])
    assert len(res) == 5
    for a, b in zip(res, completo):
        _igual(a, b)


def test_la_llamada_partida_se_reintenta_una_sola_vez():
    pool = PoolFalso("tiempo", falla_bloques=True)
    with pytest.raises(ErrorTemporal) as e:
        Ejecutor(pool, relaciones=RELACIONES).estimar(FuenteMemoria({2024: _marco(5)}), "ENDES", [2024])
    assert e.value.causa == "tiempo" and pool.llamadas == [None, (0, 2)]            # el primer bloque que falla corta; no hay segundo nivel


def test_una_caida_del_trabajador_no_se_parte_ni_se_reintenta():
    pool = PoolFalso("caida")
    with pytest.raises(ErrorTemporal) as e:
        Ejecutor(pool, relaciones=RELACIONES).estimar(FuenteMemoria({2024: _marco(5)}), "ENDES", [2024])
    assert e.value.causa == "caida" and pool.llamadas == [None]


def test_con_anios_independientes_la_llamada_partida_es_la_de_un_anio():
    class PoolAnio2025(PoolFalso):
        def ejecutar(self, trabajo):
            self.llamadas.append((trabajo.anios, trabajo.bloque))
            if trabajo.anios == (2025,) and trabajo.bloque is None:
                raise ErrorTemporal("tiempo", "simulado")
            return trabajo()

    pool = PoolAnio2025()
    marcos = {2024: _marco(1), 2025: _marco(2)}
    res = Ejecutor(pool, relaciones=RELACIONES).estimar(FuenteMemoria(marcos), "ENDES", [2024, 2025])
    assert pool.llamadas == [((2024,), None), ((2025,), None), ((2025,), (0, 2)), ((2025,), (1, 2))] and len(res) == 10


def test_los_bloques_cubren_cada_dominio_exactamente_una_vez():
    t = Tarea(FuenteMemoria({2024: _marco(5)}), (2024,))
    a, b = t.partir()
    c, d = b.partir()
    vistos = [e.dominio for x in (a, c, d) for e in x()]
    assert sorted(vistos) == sorted(e.dominio for e in t()) and len(vistos) == len(set(vistos)) == 5


# ------------------------------------------------------------------ nulo de y dentro de u

def test_un_nulo_de_y_dentro_de_u_es_error_interno_y_queda_registrado(caplog):
    m = _marco(1).with_columns(y=pl.when(pl.int_range(pl.len()) == 3).then(None).otherwise(pl.col("y")),
                               u=pl.when(pl.int_range(pl.len()) == 3).then(True).otherwise(pl.col("u")))
    with caplog.at_level(logging.ERROR, logger="pap.inferencia.ejecutor"), pytest.raises(ErrorInterno, match="y nulo"):
        Ejecutor(relaciones=RELACIONES).estimar(FuenteMemoria({2024: m}), "ENDES", [2024])
    assert any("y nulo" in r.getMessage() and r.levelno == logging.ERROR for r in caplog.records)


def test_un_nulo_de_y_fuera_de_u_no_es_error():
    m = _marco(1)
    assert m.filter(~pl.col("u"))["y"].null_count() > 0
    assert len(Ejecutor(relaciones=RELACIONES).estimar(FuenteMemoria({2024: m}), "ENDES", [2024])) == 5


# ------------------------------------------------------------------ un plan real (sintético) por DuckDB endurecido

def test_ejecutar_un_plan_compilado_lee_por_duckdb_endurecido_y_reindexa_los_dominios(tmp_path):
    ctx, micro = contexto_sintetico(tmp_path)
    con = conexion_segura(RAIZ_REAL, carpetas=[micro])
    pc = verificar(plan_anemia("departamento"), ctx, con)
    assert not isinstance(pc, Falla), pc
    res = Ejecutor(relaciones=RELACIONES).ejecutar({2024: pc}, ctx, carpetas=[micro])
    por = {e.dominio: e for e in res}
    assert set(por) == {("08",), ("15",)}                                     # 08 (Cusco) tiene filas pero ninguna en u: «sin datos»
    assert por[("08",)].sin_datos and por[("08",)].anio == 2024
    lima = por[("15",)]
    assert lima.n == 3 and lima.eventos == 2 and lima.valor == pytest.approx(0.75)


def test_con_un_territorio_pedido_solo_sale_ese_dominio(tmp_path):
    ctx, micro = contexto_sintetico(tmp_path)
    pc = verificar(plan_anemia("departamento", "15"), ctx)
    res = Ejecutor(relaciones=RELACIONES).ejecutar({2024: pc}, ctx, carpetas=[micro])
    assert [e.dominio for e in res] == [("15",)]


def test_con_un_corte_los_dominios_son_territorio_por_categoria_mas_sin_dato(tmp_path):
    ctx, micro = contexto_sintetico(tmp_path)
    pc = verificar(plan_anemia("departamento", "15", cortes=("area",)), ctx)
    assert not isinstance(pc, Falla), pc
    res = Ejecutor(relaciones=RELACIONES).ejecutar({2024: pc}, ctx, carpetas=[micro])
    assert len(res) == len(pc.cortes[0].categorias) + 1 and {e.dominio[0] for e in res} == {"15"}
    assert sum(e.n for e in res) == 3 and any(e.sin_datos for e in res)
