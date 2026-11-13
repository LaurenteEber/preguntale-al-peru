"""M0-10: las recetas de indicador (esquema, cruces con las tablas curadas, plan que arman, comparación con el cubo y doradas).

Sin microdatos: las pruebas que calculan sobre los Parquet de 2024 están en test_recetas_microdatos.py."""
import shutil

import pytest
import yaml
from pydantic import ValidationError

from pap.cli import construir_parser, main
from pap.config import Rutas
from pap.errores import PapError
from pap.inferencia import recetas as rc
from pap.inferencia.estimacion import Estimacion

from conftest import RAIZ_REAL

IDS = ("endes_anemia_6_35m", "endes_anemia_6_35m_oms2024", "endes_dci_menores_5")


def _datos(id_: str) -> dict:
    return yaml.safe_load((RAIZ_REAL / rc.CARPETA / f"{id_}.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def recetas():
    return {r.id: r for r in rc.leer_recetas(RAIZ_REAL)}


# ------------------------------------------------------------------ las tres recetas

def test_estan_las_tres_recetas_verificadas_con_el_visto_del_dueno(recetas):
    assert tuple(sorted(recetas)) == tuple(sorted(IDS))
    for r in recetas.values():
        assert (r.estado, r.pendiente) == ("verificado", None)             # K-03: visto del dueño el 12/11/2026
        assert r.transformaciones == () and r.tolerancia_pp == 0.1 and r.anios == (2024, 2024) and r.indicador_id == r.id


def test_los_cinco_cortes_estan_permitidos_desde_m1_03(recetas):
    """M1-03 pasa grupo_edad, región natural y quintil de bienestar (con los tramos y rótulos de M1-01) de «no permitidos» a «permitidos»."""
    for r in recetas.values():
        assert r.cortes_permitidos == ("area", "sexo", "grupo_edad", "region_natural", "quintil_riqueza")
        assert r.cortes_no_permitidos == ()


def test_los_universos_y_las_doradas_de_cada_receta(recetas):
    assert recetas["endes_anemia_6_35m"].universo_analitico == recetas["endes_anemia_6_35m_oms2024"].universo_analitico == "nino_hecho_hb_medida"
    assert recetas["endes_dci_menores_5"].universo_analitico == "nino_hecho"
    assert {k: len(r.doradas) for k, r in recetas.items()} == {"endes_anemia_6_35m": 9, "endes_anemia_6_35m_oms2024": 9, "endes_dci_menores_5": 3}
    assert all(d.cita and d.valor_publicado for r in recetas.values() for d in r.doradas)


def test_los_planes_de_las_recetas(recetas):
    def condiciones(id_):
        p = recetas[id_].a_plan(2024)
        return [(c.var, c.op, c.valores) for c in (*p.indicador.condiciones, *p.universo.restricciones)]

    assert condiciones("endes_anemia_6_35m") == [("ENDES·2024·RECH6·HC57", "en", (1, 2, 3)), ("ENDES·2024·RECH6·HC1", "entre", (6, 35)),
                                                 ("ENDES·2024·RECH6·HC57", "en", (1, 2, 3, 4))]
    assert condiciones("endes_anemia_6_35m_oms2024") == [("ENDES·2024·RECH6·HC57A", "en", (1, 2, 3)), ("ENDES·2024·RECH6·HC1", "entre", (6, 35)),
                                                         ("ENDES·2024·RECH6·HC57A", "en", (1, 2, 3, 4))]
    assert condiciones("endes_dci_menores_5") == [("ENDES·2024·RECH6·HC70", "<", (-200,)), ("ENDES·2024·RECH6·HC1", "entre", (0, 59)),
                                                  ("ENDES·2024·RECH6·HC70", "entre", (-9989, 9989))]
    p = recetas["endes_dci_menores_5"].a_plan(2024, "departamento", "15", ("area", "sexo"))
    assert (p.origen, p.receta_id, p.territorio.nivel, p.territorio.id, p.cortes) == ("receta", "endes_dci_menores_5", "departamento", "15", ("area", "sexo"))


def test_una_receta_no_arma_planes_de_otro_anio_ni_con_cortes_no_permitidos(recetas):
    r = recetas["endes_anemia_6_35m"]
    with pytest.raises(PapError, match="2024–2024, no para 2023"):
        r.a_plan(2023)
    for corte in ("lengua_materna", "no_existe"):
        with pytest.raises(PapError, match="no permite los cortes"):
            r.a_plan(2024, cortes=(corte,))


def test_leer_una_receta_que_no_existe_dice_cuales_hay():
    with pytest.raises(PapError, match="No hay receta «nada».*endes_anemia_6_35m"):
        rc.leer_receta(RAIZ_REAL, "nada")
    with pytest.raises(PapError, match="No hay receta"):
        rc.leer_receta(RAIZ_REAL, "../recetas/endes_dci_menores_5")


# ------------------------------------------------------------------ el esquema rechaza

def test_transformaciones_no_vacias_son_tipo_c():
    d = _datos("endes_dci_menores_5") | {"transformaciones": [{"tipo": "inventada"}]}
    with pytest.raises(ValidationError, match="tipo C"):
        rc.Receta.model_validate(d)


@pytest.mark.parametrize("cambio,mensaje", [
    ({"estado": "revisado", "pendiente": None}, "visto_dueno"),    # revisado sin el visto pendiente
    ({"pendiente": "visto_dueno"}, "«verificado» no lleva pendiente"),
    ({"campo_nuevo": 1}, "Extra inputs"),
    ({"anios": [2025, 2024]}, "primero no puede pasar"),
    ({"cortes_no_permitidos": [{"id": "area", "motivo": "x"}]}, "permitidos y no permitidos"),
    ({"fuente": "sin dónde"}, "no dice dónde"),
    ({"tolerancia_pp": 0}, "greater than 0"),
])
def test_el_esquema_rechaza(cambio, mensaje):
    with pytest.raises(ValidationError, match=mensaje):
        rc.Receta.model_validate(_datos("endes_dci_menores_5") | cambio)


def test_una_receta_verificada_no_lleva_pendiente():
    r = rc.Receta.model_validate(_datos("endes_dci_menores_5") | {"estado": "verificado", "pendiente": None})
    assert r.estado == "verificado"


def test_el_estado_revisado_sigue_existiendo_con_su_visto_pendiente():
    """Las tres recetas están verificadas (K-03), pero el esquema conserva la escalera propuesto < revisado < verificado."""
    r = rc.Receta.model_validate(_datos("endes_dci_menores_5") | {"estado": "revisado", "pendiente": "visto_dueno"})
    assert (r.estado, r.pendiente) == ("revisado", "visto_dueno")


# ------------------------------------------------------------------ validar (cruces con las tablas curadas)

def test_validar_recetas_del_repo_sin_errores():
    res = rc.validar(Rutas(RAIZ_REAL))
    assert sorted(res) == sorted(IDS)
    assert all(ok == 1 and not errores for ok, errores in res.values()), res


@pytest.fixture
def copia(tmp_path):
    for rel in ("curados/inferencia", "curados/capa0/dim_indicador.yaml", "curados/capa0/cifras_doradas.csv"):
        origen, destino = RAIZ_REAL / rel, tmp_path / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(origen, destino, ignore=shutil.ignore_patterns("descargas")) if origen.is_dir() else shutil.copy(origen, destino)
    return tmp_path


def _sin_lineas(errores):
    """La copia no trae los archivos que las citas nombran: esos errores no son de lo que se prueba."""
    return [e for e in errores if not e.startswith("cita con archivo:línea")]


def test_validar_detecta_una_dorada_que_no_es_la_de_la_tabla(copia):
    ruta = copia / rc.CARPETA / "endes_anemia_6_35m.yaml"
    ruta.write_text(ruta.read_text(encoding="utf-8").replace("valor_publicado: 43.7", "valor_publicado: 43.8"), encoding="utf-8")
    errores = _sin_lineas(rc.validar(Rutas(copia))["endes_anemia_6_35m"][1])
    assert len(errores) == 1 and errores[0].startswith("dorada DOR-ANE-2024-PE: no coincide con cifras_doradas.csv")


def test_validar_detecta_una_dorada_inexistente_y_un_universo_inexistente(copia):
    ruta = copia / rc.CARPETA / "endes_dci_menores_5.yaml"
    ruta.write_text(ruta.read_text(encoding="utf-8").replace("DOR-DCI-2024-RURAL", "DOR-NO-EXISTE").replace(
        "universo_analitico: nino_hecho", "universo_analitico: nino_inventado"), encoding="utf-8")
    errores = _sin_lineas(rc.validar(Rutas(copia))["endes_dci_menores_5"][1])
    assert errores == ["universo_analitico «nino_inventado» no está en universos_analiticos.yaml",
                       "dorada DOR-DCI-2024-RURAL: falta en la receta (está en cifras_doradas.csv para endes_dci_menores_5)",   # H10-1
                       "dorada DOR-NO-EXISTE: no está en cifras_doradas.csv"]


def test_validar_detecta_una_dorada_de_la_tabla_que_la_receta_no_lleva(copia):
    """H10-1: las doradas de la receta son exactamente las de su indicador y año en cifras_doradas.csv."""
    ruta = copia / rc.CARPETA / "endes_dci_menores_5.yaml"
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    assert any(d["id_cifra"] == "DOR-DCI-2024-RURAL" for d in datos["doradas"])
    datos["doradas"] = [d for d in datos["doradas"] if d["id_cifra"] != "DOR-DCI-2024-RURAL"]
    ruta.write_text(yaml.safe_dump(datos, allow_unicode=True, sort_keys=False), encoding="utf-8")
    errores = _sin_lineas(rc.validar(Rutas(copia))["endes_dci_menores_5"][1])
    assert len(errores) == 1 and "DOR-DCI-2024-RURAL" in errores[0] and "falta" in errores[0]


def test_validar_exige_el_campo_receta_en_dim_indicador(copia):
    ruta = copia / "curados/capa0/dim_indicador.yaml"
    ruta.write_text(ruta.read_text(encoding="utf-8").replace("  receta: endes_dci_menores_5\n", ""), encoding="utf-8")
    errores = _sin_lineas(rc.validar(Rutas(copia))["endes_dci_menores_5"][1])
    assert errores == ["dim_indicador.yaml: el indicador endes_dci_menores_5 debe llevar `receta: endes_dci_menores_5` (lleva None)"]


def test_validar_dice_si_una_receta_no_cumple_el_esquema(copia):
    ruta = copia / rc.CARPETA / "endes_dci_menores_5.yaml"
    ruta.write_text(ruta.read_text(encoding="utf-8").replace("transformaciones: []", "transformaciones: [x]"), encoding="utf-8")
    ok, errores = rc.validar(Rutas(copia))["endes_dci_menores_5"]
    assert ok == 0 and "tipo C" in errores[0]


def test_dim_indicador_lleva_el_campo_receta_en_los_tres_indicadores():
    inds = {i["id"]: i for i in yaml.safe_load((RAIZ_REAL / rc.DIM_INDICADOR).read_text(encoding="utf-8"))["indicadores"]}
    assert {k: inds[k].get("receta") for k in IDS} == {k: k for k in IDS}
    assert [k for k, i in inds.items() if "receta" in i and k not in IDS] == []


# ------------------------------------------------------------------ comparar_fila y reproducir_doradas (con estimaciones armadas a mano)

def _est(**kw) -> Estimacion:
    base = dict(dominio=("PE",), anio=2024, n=400, valor=0.35, ee=0.02, gl=100, n_efectivo=300.0, deff=1.2, ic_inf=0.31, ic_sup=0.39, eventos=140)
    return Estimacion(**{**base, **kw})


def _cubo(e: Estimacion, **cambios) -> dict[str, str]:
    p = rc.ParametrosRecetas.desde_yaml()
    fila = {k: ("" if v is None else repr(round(float(v), p.cubo_decimales))) for k, v in rc.en_unidades_del_cubo(e).items()}
    return {**fila, **{k: str(v) for k, v in cambios.items()}}


def test_los_parametros_de_las_recetas_son_los_de_la_definicion_de_hecho():
    p = rc.ParametrosRecetas.desde_yaml()
    assert (p.cubo_decimales, p.cubo_tolerancia_unidades, p.oraculo_tolerancia) == (8, 1, 1e-12)


def test_una_fila_igual_a_la_del_cubo_pasa_todas_las_columnas():
    e = _est()
    p = rc.ParametrosRecetas.desde_yaml()
    d = rc.comparar_fila(e, _cubo(e), p)
    assert [x.columna for x in d] == list(rc.COLUMNAS) and all(x.ok for x in d)


def test_la_tolerancia_es_una_unidad_del_octavo_decimal():
    e = _est()
    p = rc.ParametrosRecetas.desde_yaml()
    mas_una = float(_cubo(e)["valor"]) + 1e-8
    assert next(x for x in rc.comparar_fila(e, _cubo(e, valor=mas_una), p) if x.columna == "valor").ok
    mas_dos = float(_cubo(e)["valor"]) + 2e-8
    assert not next(x for x in rc.comparar_fila(e, _cubo(e, valor=mas_dos), p) if x.columna == "valor").ok


@pytest.mark.parametrize("columna,valor", [("gl", 101), ("n_muestra", 401), ("ee", 2.1), ("deff", 1.3), ("ic_sup", 40.0), ("cv", 5.8)])
def test_una_columna_distinta_no_pasa(columna, valor):
    e = _est()
    d = {x.columna: x.ok for x in rc.comparar_fila(e, _cubo(e, **{columna: valor}), rc.ParametrosRecetas.desde_yaml())}
    assert d.pop(columna) is False and all(d.values())


def test_el_n_efectivo_se_compara_con_el_minimo_de_n_y_el_del_cubo():
    p = rc.ParametrosRecetas.desde_yaml()
    e = _est(n=400, n_efectivo=400.0)                                                   # el ejecutor lo topa en n
    d = {x.columna: x for x in rc.comparar_fila(e, _cubo(e, n_efectivo=451.5), p)}      # el cubo no lo topa
    assert d["n_efectivo"].ok and d["n_efectivo"].cubo == 400.0
    assert not {x.columna: x for x in rc.comparar_fila(e, _cubo(e, n_efectivo=399.0), p)}["n_efectivo"].ok
    vacio = {x.columna: x for x in rc.comparar_fila(e, _cubo(e, n_efectivo=""), p)}     # el cubo lo deja vacío si ee = 0: se compara con n
    assert vacio["n_efectivo"].ok


def test_el_cv_vacio_del_cubo_solo_coincide_con_un_cv_nulo():
    p = rc.ParametrosRecetas.desde_yaml()
    e = _est(valor=0.0, ee=0.0, ic_inf=0.0, ic_sup=0.05)
    d = {x.columna: x for x in rc.comparar_fila(e, _cubo(e), p)}
    assert d["cv"].cubo is None and d["cv"].nuevo is None and d["cv"].ok
    assert not {x.columna: x for x in rc.comparar_fila(_est(), _cubo(e), p)}["cv"].ok


def _con_doradas(r: rc.Receta, *doradas: rc.Dorada) -> rc.Receta:
    return r.model_copy(update={"doradas": doradas})


def _dorada(**kw) -> rc.Dorada:
    base = dict(id_cifra="X", nivel="nacional", territorio="PE", valor_publicado=35.0, decimales=1, bloqueante=True, cita="Cuadro p. 1")
    return rc.Dorada(**{**base, **kw})


def test_reproducir_doradas_pasa_dentro_de_la_tolerancia_de_e_05(recetas):
    r = recetas["endes_dci_menores_5"]
    e = _est(valor=0.35049)                                                              # 35,0 al redondear a 1 decimal
    assert rc.reproducir_doradas(_con_doradas(r, _dorada()), [("nacional", e)])[0]["pasa"]
    assert rc.reproducir_doradas(_con_doradas(r, _dorada(valor_publicado=35.1)), [("nacional", e)])[0]["pasa"]          # 0,1 pp
    assert not rc.reproducir_doradas(_con_doradas(r, _dorada(valor_publicado=35.2)), [("nacional", e)])[0]["pasa"]      # 0,2 pp


def test_reproducir_doradas_exige_casos_exactos_y_cv_dentro_de_la_tolerancia(recetas):
    r = recetas["endes_dci_menores_5"]
    e = _est(valor=0.35, ee=0.0099)                                                      # cv = 2,83
    d = lambda **kw: rc.reproducir_doradas(_con_doradas(r, _dorada(**kw)), [("nacional", e)])[0]["pasa"]  # noqa: E731
    assert d(casos_publicados=400, cv_publicado=2.8)
    assert not d(casos_publicados=399)
    assert not d(cv_publicado=2.6)


def test_una_dorada_sin_dominio_o_sin_datos_no_pasa(recetas):
    r = recetas["endes_dci_menores_5"]
    assert not rc.reproducir_doradas(_con_doradas(r, _dorada()), [])[0]["pasa"]
    assert not rc.reproducir_doradas(_con_doradas(r, _dorada()), [("nacional", Estimacion(("PE",), 2024, 0))])[0]["pasa"]


# ------------------------------------------------------------------ comando

def test_cli_registra_pap_inferencia_receta():
    a = construir_parser().parse_args(["inferencia", "receta", "endes_dci_menores_5", "--anio", "2024", "--comparar-cubo"])
    assert (a.accion, a.id, a.anio, a.comparar_cubo) == ("receta", "endes_dci_menores_5", 2024, True)
    assert a.fn.__name__ == "cmd_inferencia"
    a = construir_parser().parse_args(["inferencia", "validar-recetas"])
    assert a.accion == "validar-recetas" and a.id is None and not a.comparar_cubo


def test_cli_validar_recetas_sale_con_0_y_lista_las_tres(capsys):
    assert main(["inferencia", "validar-recetas"]) == 0
    salida = capsys.readouterr().out
    assert salida.count("✔ ") == 3 and "estado verificado" in salida and "pendiente" not in salida and "✘" not in salida


def test_cli_receta_sin_id_o_sin_anio_o_inexistente_falla_con_mensaje(capsys):
    for argv in (["inferencia", "receta"], ["inferencia", "receta", "endes_dci_menores_5"], ["inferencia", "receta", "nada", "--anio", "2024"]):
        assert main(argv) != 0
    assert "Uso: pap inferencia receta" in capsys.readouterr().err
