"""S1-12 — Gasto en soles constantes y su evolución (G-01, R-GASTO-12).

El cubo trae, para el devengado del gasto, filas `devengado_constante` en soles del último año cerrado (IPC de Lima,
promedio anual de dim_ipc). Una evolución del gasto compara dos años en esos soles; una cifra de un solo año sigue en
soles corrientes. Si falta el cubo, las pruebas FALLAN (agents.md §8)."""
import math

import pandas as pd
import pytest

from pap.config import Rutas
from pap.motor import calculo
from pap.motor import preguntar as P
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL

FACTOR_2023 = 1.0388706        # backlog S1-12: 115,365655 / 111,049113 (dim_ipc)
CONTROLES_NOMINALES = {2023: 2179, 2024: 2429, 2025: 2456}   # G-07, millones, devengado nacional ex-PAN


@pytest.fixture(scope="module")
def raiz():
    r = Rutas(RAIZ_REAL).raiz
    assert (r / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    return r


@pytest.fixture(scope="module")
def ipc(raiz):
    return pd.read_parquet(raiz / "biblioteca" / "dimensiones" / "dim_ipc.parquet")


@pytest.fixture(scope="module")
def cubo(raiz):
    return pd.read_parquet(raiz / "biblioteca" / "indicadores" / "fact_indicador.parquet")


@pytest.fixture(scope="module")
def motor(raiz):
    return Motor(cargar_contexto(raiz))


def _gasto(cubo, medida, iid="gasto_ex_pan"):
    x = cubo[(cubo.indicador_id == iid) & (cubo.nivel == "nacional") & (cubo.linea == "cifra") & (cubo.medida == medida)]
    return {int(r.anio): r for r in x.itertuples()}


def test_factor_2023_2025_reproduce_dim_ipc(ipc):
    base, f = calculo.factores_deflactor(ipc, [2023, 2024, 2025])
    prom = ipc.groupby("anio").ipc_prom_anual.first()
    assert base == 2025
    assert round(f[2023], 7) == FACTOR_2023
    assert math.isclose(f[2023], prom[2025] / prom[2023], rel_tol=1e-12)
    assert f[2025] == 1.0


def test_anio_base_coincide_con_el_validador(raiz, ipc, cubo):
    ctx = cargar_contexto(raiz)
    anios = cubo[cubo.medida == "devengado"].anio.unique()
    assert calculo.anio_base_deflactor(ipc, anios) == ctx.anio_actual - 1   # R-GASTO-12: base = último año cerrado
    assert set(cubo[cubo.medida == "devengado_constante"].anio_base_deflactor.dropna().astype(int)) == {ctx.anio_actual - 1}


def test_ipc_incompleto_detiene_el_calculo(ipc):
    roto = ipc[~((ipc.anio == 2024) & (ipc.mes == 7))].copy()       # falta julio de 2024
    roto.loc[roto.anio == 2024, ["anio_completo", "ipc_prom_anual"]] = [False, float("nan")]
    roto.loc[roto.anio == 2024, "meses_con_dato"] = 11
    with pytest.raises(ValueError, match="falta el IPC completo de 2024"):
        calculo.factores_deflactor(roto, [2023, 2024, 2025])


def test_filas_constantes_solo_del_devengado_del_gasto(cubo):
    cst = cubo[cubo.medida == "devengado_constante"]
    assert set(cst.indicador_id) == {"gasto_ex_pan", "gasto_ex_pan_opcion_c"}
    k = ["indicador_id", "anio", "nivel", "territorio_id", "linea"]
    dev = cubo[(cubo.medida == "devengado") & cubo.indicador_id.isin(set(cst.indicador_id))]
    par = dev.merge(cst, on=k, suffixes=("_d", "_c"), how="outer", indicator=True)
    assert (par._merge == "both").all()                          # todos los niveles y líneas con devengado
    assert ((par.valor_c - par.valor_d * par.factor_deflactor_c).abs() < 1e-6).all()
    otras = cubo[cubo.medida != "devengado_constante"]
    assert otras.anio_base_deflactor.isna().all() and otras.factor_deflactor.isna().all()
    assert set(cubo.version_tabla) == {calculo.VERSION_TABLA} == {"1.2.0"}


def test_montos_nominales_de_control_no_cambian(cubo):
    nom = _gasto(cubo, "devengado")
    assert {a: round(r.valor / 1e6) for a, r in nom.items()} == CONTROLES_NOMINALES
    cst = _gasto(cubo, "devengado_constante")
    assert round(cst[2023].valor / 1e5) / 10 == 2263.9            # S/ 2 263,9 millones en soles de 2025


def test_evolucion_del_gasto_compara_2023_con_2025_en_soles_de_2025(motor):
    r = P.preguntar_minima(motor, {"intencion": "evolucion", "tema": "gasto_publico", "territorio": {"texto": "Perú"}})
    assert r["comparaciones_bloqueadas"] == []
    cifras = r["cifras"].values()
    assert all(not any(b["regla"] == "R-GASTO-12" for b in c["bloqueos_cruce"]) for c in cifras)
    assert {c["anio"] for c in cifras} == {2023, 2025}
    assert all(c["precios"] == "constantes" and c["anio_base_deflactor"] == 2025 for c in cifras)
    c1 = r["capas"]["capa1"]
    assert c1["respuesta_corta"] == ("En Perú, el gasto en servicios de salud y nutrición infantil pasó de S/ 2 263,9 "
                                     "millones en 2023 a S/ 2 455,9 millones en 2025, en soles de 2025: aumentó.")
    assert "%" not in c1["respuesta_corta"]
    assert "Montos en soles de 2025 (ajustados por inflación), para que se puedan comparar entre años." in c1["ojo_al_leer"]
    ctx = r["capas"]["capa2"]["mas_contexto"]
    assert all(t["etiqueta"] != "Otro año: no se compara con la cifra clave." for t in ctx)
    citas = " ".join(r["capas"]["capa3"]["para_citar"])
    assert "monto registrado en 2023: S/ 2 179,2 millones; factor de inflación: 1,0388706" in citas
    assert "soles constantes (ajustados por inflación)" in [g["termino"] for g in r["capas"]["capa3"]["glosario"]]
    infr = [x for x in r["corrector"] if x["detalle"].get("infracciones")]
    assert not infr, infr


def test_cifra_de_un_solo_anio_sigue_en_soles_corrientes(motor):
    r = P.preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "gasto_publico", "territorio": {"texto": "Perú"}})
    (c,) = r["cifras"].values()
    assert c["medida"] == "devengado" and "precios" not in c and "anio_base_deflactor" not in c
    assert round(c["valor"] / 1e6) == CONTROLES_NOMINALES[2025]
    assert not any(x["regla"] == "R-GASTO-12" and x["motivo"] != "soles_corrientes" for x in c["resultados"])


def test_sin_cifra_publicable_del_anio_comparado_dice_primero_que_no_compara(motor):
    """Verificación S1-16 (B-1): la cifra de 2023 de Kumpirushiato se suprime (R-GASTO-07); la evolución no compara, lo dice
    primero y la cifra de 2025 va en soles corrientes, sin el aviso de soles constantes."""
    r = P.preguntar_minima(motor, {"intencion": "evolucion", "tema": "gasto_publico", "territorio": {"ubigeo": "080915"}})
    assert r["tipo"] == "respuesta"
    c1 = r["capas"]["capa1"]
    assert c1["respuesta_corta"].startswith("No podemos mostrar cómo cambió el gasto en servicios de salud y nutrición infantil "
                                            "en Kumpirushiato desde 2023: la cifra de 2023 no se puede publicar.")
    (c,) = r["cifras"].values()
    assert c["medida"] == "devengado" and "precios" not in c and c["comparacion"] is None
    assert not any("soles de 2025" in t for t in [c1["respuesta_corta"], *c1["ojo_al_leer"], c1["cifra_clave"]["texto"]])


def test_cifra_clave_de_un_anio_que_no_es_el_base_lleva_el_rotulo(motor):
    """Verificación S1-16 (M-1): con --hasta 2024 la cifra clave (2024) dice que está en soles de 2025."""
    r = P.preguntar_minima(motor, {"intencion": "evolucion", "tema": "gasto_publico", "territorio": {"texto": "Perú"},
                                   "periodo": {"tipo": "serie", "hasta": 2024}})
    assert r["capas"]["capa1"]["cifra_clave"]["texto"].endswith("en Perú en 2024, en soles de 2025.")
