"""Piloto P1: cubo fact_indicador (`pap calcular`, 10/10/2026)."""
import json

import duckdb
import pandas as pd
import pytest

from pap.capa0 import guardia_gasto, salida
from pap.config import Rutas
from pap.errores import PapError
from pap.motor import biblioteca
from pap.motor import calculo as C

from conftest import RAIZ_REAL


@pytest.fixture(scope="module")
def rutas():
    return Rutas(RAIZ_REAL)


@pytest.fixture(scope="module")
def res(rutas):
    pytest.importorskip("svy")
    try:
        return C.construir(rutas)
    except (PapError, FileNotFoundError) as e:
        pytest.skip(f"faltan tablas de la capa 0: {e}")


@pytest.fixture(scope="module")
def cubo(res):
    return res.tablas["fact_indicador"]


def test_sin_bloqueantes_fallidas(res):
    assert {p["id"] for p in res.pruebas if p["bloqueante"] and not p["ok"]} == set()


def test_contrato_columnas_y_clave(cubo):
    assert list(cubo.columns) == C.COLUMNAS
    assert not cubo.duplicated(C.CLAVE).any()
    assert salida.CLAVES["fact_indicador"] == ", ".join(C.CLAVE)
    assert set(cubo.estado_calculo.dropna()) <= {"calculada", "sin_casos", "no_calculable"}
    assert set(cubo.linea) <= {"cifra", "referencia_nacional", "sede_nacional", "no_asignable_dpto_lima",
                               "no_asignable_lima_callao", "revisar", "sin_departamento"}


def test_doradas_bloqueantes_reproducidas(res):
    rep = res.revision["doradas_reproduccion_p1"]
    blo = rep[rep.bloqueante]
    # 60 desde el 11/10/2026 (validación ciega de las doradas): + DOR-ANE-2025-PE bloqueante y + 3 distritos del Mapa;
    # 89 desde el 12/10/2026: + 29 del SIEN contra el INS (control_registro)
    assert len(blo) == 89 and (blo.pasa == True).all()  # noqa: E712
    assert (blo.proposito == "control_registro").sum() == 29


def test_dci_2024_igual_al_inei(cubo):
    """Casos, CV e IC de la DCI 2024 nacional (Indicadores de Resultados ENDES 2024): el diseño es el del INEI."""
    r = cubo[(cubo.indicador_id == "endes_dci_menores_5") & (cubo.anio == 2024) & (cubo.nivel == "nacional")].iloc[0]
    assert round(r.valor, 1) == 12.1 and int(r.n_muestra) == 19511 and round(r.cv, 1) == 2.8
    assert (round(r.ic_inf, 1), round(r.ic_sup, 1)) == (11.5, 12.8)


def test_ambitos_lima_en_encuestas(cubo):
    e = cubo[cubo.indicador_id == "endes_anemia_6_35m"]
    for a in C.AMBITOS:
        assert set(e[e.nivel == a].anio) == set(range(2015, 2026))
    lm17 = e[(e.nivel == "LIMA_METROPOLITANA") & (e.anio == 2017)].iloc[0]
    assert "ambito_por_estrato" in json.loads(lm17.avisos)
    assert not (e.nivel == "departamento").any() or "07" not in set(e[e.nivel == "departamento"].territorio_id)


def test_gasto_controles_y_lineas(cubo):
    g = cubo[(cubo.indicador_id == "gasto_ex_pan") & (cubo.medida == "devengado")]
    nac = g[(g.nivel == "nacional") & (g.linea == "cifra")].set_index("anio").valor
    assert {a: round(v / 1e6) for a, v in nac.items()} == C.CONTROLES_R2["grupo_expan"]
    lm = g[(g.nivel == "LIMA_METROPOLITANA") & (g.linea == "cifra")]
    assert "sesgo_sede" in json.loads(lm.iloc[0].avisos)
    assert (g[(g.nivel == "LIMA_METROPOLITANA")].linea == "referencia_nacional").any()


def test_gasto_pasa_por_la_guardia(rutas):
    con, _ = biblioteca.conectar_gasto(rutas)
    with pytest.raises(guardia_gasto.GuardiaGasto):
        biblioteca.consultar_gasto(con, "SELECT sum(devengado) FROM gasto_tema('cpt_grupo_expan') "
                                        "WHERE departamento_atribucion = '15'")
    con.close()


def test_sien_dos_cotas(cubo):
    c = cubo[cubo.indicador_id == "sien_cobertura_tamizaje_6_35m"]
    assert set(c.nivel) == {"departamento", "LIMA_METROPOLITANA", "LIMA_REGION", "CALLAO"}
    assert (c.cota_inf <= c.cota_sup).all() and (c.valor == c.cota_sup).all()


def test_mapa_sin_cifra_puntual(cubo):
    m = cubo[cubo.indicador_id == "mapa_pobreza_2018"]
    assert m.valor.isna().all() and m.ic_inf.notna().all() and set(m.nivel) == {"distrito", "provincia"}


def test_parquet_publicado_reproducible(rutas, res):
    """El Parquet en disco es el del manifiesto y escribir el cubo recién calculado da la misma huella (bit a bit)."""
    man = rutas.raiz / "biblioteca" / "indicadores" / "manifiesto_p1_indicadores.json"
    if not man.exists():
        pytest.skip("cubo sin construir (pap calcular)")
    m = json.loads(man.read_text(encoding="utf-8"))
    import tempfile
    from pathlib import Path

    from pap.util import sha256
    with tempfile.TemporaryDirectory() as d:
        ruta = Path(d) / "fact_indicador.parquet"
        salida.escribir_parquet(res.tablas["fact_indicador"], ruta, salida.CLAVES["fact_indicador"])
        assert f"sha256:{sha256(ruta)}" == m["tablas"]["fact_indicador"]["hash"]


def test_doradas_sien_ins(res):
    """12/10/2026: el SIEN se valida contra la publicación oficial del INS (conteos exactos, cifra a 1 decimal)."""
    rep = res.revision["doradas_reproduccion_p1"]
    s = rep[rep.proposito == "control_registro"]
    assert len(s) >= 29 and (s.pasa == True).all()  # noqa: E712
    assert {"PE", "15", "21", "CALLAO", "LIMA_REGION", "210801", "150132"} <= set(s.territorio)
    assert {p["id"]: p for p in res.pruebas}["CAL-10"]["ok"]
    lm = rep[rep.id_cifra == "DOR-SIEN-2025-LM1501"]
    assert not lm.bloqueante.iloc[0] and bool(lm.pasa.iloc[0])
