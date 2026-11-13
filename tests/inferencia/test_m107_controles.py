"""M1-07, tarea 6, en el Mac: tres controles de prueba que reproducen cifras oficiales de 2024 (±0,1 pp y casos exactos) con el diseño de la mujer y
del hijo de la entrevistada. Son recetas de `tests/inferencia/recetas_control/`: NO están en `dim_indicador`, no responden preguntas, no se marcan
`verificado` y no pasan por `pap inferencia validar-recetas`; se cargan aquí con el esquema de `recetas.Receta`.

Necesitan `biblioteca/microdatos/ENDES/2024/` y `biblioteca/variables/`: si faltan, FALLAN (no se saltan)."""
from pathlib import Path

import pytest
import yaml

from pap.inferencia import recetas
from pap.inferencia.duckdb_seguro import conexion_segura
from pap.inferencia.ejecutor import Ejecutor
from pap.inferencia.verificador import Contexto, Falla, verificar

from conftest import RAIZ_REAL

pytestmark = [pytest.mark.regresion_microdatos, pytest.mark.solo_mac]

CARPETA = Path(__file__).parent / "recetas_control"
CONTROLES = ["control_pf_unidas", "control_pf_moderno", "control_cesarea", "control_anemia_mujeres"]
CUADRO = {"control_pf_unidas": "Cuadro N.º 23 p. 91", "control_pf_moderno": "Cuadro N.º 24 p. 95", "control_cesarea": "Cuadro N.º 29 p. 105",
          "control_anemia_mujeres": "Principales indicadores 2009–2024», p. 33"}
DOCUMENTO = {"control_anemia_mujeres": "endes-2024-informe-principal"}           # los demás, del informe de programas presupuestales
UNIDAD = {"control_pf_unidas": "mujer", "control_pf_moderno": "mujer", "control_cesarea": "nino", "control_anemia_mujeres": "mujer"}
# (tabla base, submuestra, peso, conglomerado) que el control declara para su diseño
DISENO = {"mujer": ("RE223132", "individual", "V005/1e6", "V021"), "nino": ("REC41", "individual", "V005/1e6", "V021"),
          "anemia": ("RECH5", "medicion", "HV005/1e6", "HV021")}
CASOS_MEDIDOS = {"control_anemia_mujeres": 30290}              # sin casos publicados: los midió el supervisor (13/11/2026), no son una cifra del INEI


def cargar(id_: str):
    """La receta de control y sus cifras por área, sin pasar por `recetas.leer_receta` (que solo lee curados/inferencia/recetas/)."""
    d = yaml.safe_load((CARPETA / f"{id_}.yaml").read_text(encoding="utf-8"))
    por_area = [recetas.DoradaCorte.model_validate(x) for x in d.pop("doradas_area")]
    return recetas.Receta.model_validate(d), por_area


@pytest.fixture(scope="module")
def mundo():
    for carpeta in ("biblioteca/variables", "biblioteca/microdatos/ENDES/2024"):
        assert (RAIZ_REAL / carpeta).is_dir(), f"falta {carpeta}"
    ctx = Contexto.cargar(RAIZ_REAL)
    variables = {k: {**v, "estado": "revisado"} for k, v in ctx.esquema.variables.items()}      # como quedará el lote con el visto del dueño
    from dataclasses import replace
    return replace(ctx, esquema=replace(ctx.esquema, variables=variables)), conexion_segura(RAIZ_REAL), Ejecutor(raiz=RAIZ_REAL)


def test_los_controles_no_estan_en_dim_indicador_ni_en_las_recetas_del_repo():
    dim = yaml.safe_load((RAIZ_REAL / "curados/capa0/dim_indicador.yaml").read_text(encoding="utf-8"))
    ids = {i["id"] for i in (dim if isinstance(dim, list) else dim["indicadores"])}
    for c in CONTROLES:
        assert c not in ids and c not in recetas.ids_de_recetas(RAIZ_REAL)
        receta, _ = cargar(c)
        assert receta.estado == "propuesto" and receta.pendiente is None and receta.tolerancia_pp == 0.1


@pytest.mark.parametrize("id_", CONTROLES)
def test_el_control_reproduce_la_cifra_oficial_nacional_y_por_area(mundo, id_):
    ctx, con, ejecutor = mundo
    receta, por_area = cargar(id_)
    # 1. nacional: plan → verificador → ejecutor (un solo territorio) y la dorada con la tolerancia y los casos de la receta
    pc = verificar(receta.a_plan(2024, "nacional"), ctx, con)
    assert not isinstance(pc, Falla), pc
    assert pc.universo_analitico.id == receta.universo_analitico and pc.controles["perdida_u"] == 0
    est = [("nacional", e) for e in ejecutor.ejecutar({2024: pc}, ctx)]
    filas = recetas.reproducir_doradas(receta, est)
    assert len(filas) == 1
    for f in filas:
        assert f["pasa"], f"{id_} {f['id_cifra']}: publicado {f['publicado']}, nuestro {f['nuestro']} (dif {f['dif_pp']} pp), casos {f['casos_publicados']} vs {f['n']}"
        assert abs(f["dif_pp"]) <= 0.1 and (f["casos_publicados"] is None or f["casos_publicados"] == f["n"])
        assert (f["n"] == CASOS_MEDIDOS[id_]) if id_ in CASOS_MEDIDOS else f["casos_publicados"] == f["n"]
    # 2. por área (urbana y rural)
    estimaciones, valores = recetas.calcular_cortes(receta, por_area, RAIZ_REAL, ctx=ctx, ejecutor=ejecutor, con=con)
    filas = recetas.reproducir_doradas_cortes(receta, por_area, estimaciones, valores)
    assert {f["categoria"] for f in filas} == {"urbano", "rural"}
    for f in filas:
        assert f["pasa"], f"{id_} {f['id_cifra']}: publicado {f['publicado']}, nuestro {f['nuestro']} (dif {f['dif_pp']} pp), casos {f['casos_publicados']} vs {f['n']}"
        assert abs(f["dif_pp"]) <= 0.1 and (f["casos_publicados"] is None or f["casos_publicados"] == f["n"])
    for d in [*receta.doradas, *por_area]:
        assert CUADRO[id_] in d.cita and DOCUMENTO.get(id_, "endes-2024-informe-ppr") in d.cita


@pytest.mark.parametrize("id_", CONTROLES)
def test_el_control_usa_el_diseno_de_su_unidad(mundo, id_):
    ctx, con, _ = mundo
    receta, _ = cargar(id_)
    pc = verificar(receta.a_plan(2024, "nacional", None, ("area",)), ctx, con)
    assert not isinstance(pc, Falla), pc
    tabla, nivel, peso, psu = DISENO["anemia" if id_ == "control_anemia_mujeres" else receta.unidad]
    assert (pc.diseno.nivel_submuestra, pc.diseno.peso_expr, pc.diseno.psu_expr) == (nivel, peso, psu)
    assert receta.unidad == UNIDAD[id_] and pc.archivo_unidad == tabla
