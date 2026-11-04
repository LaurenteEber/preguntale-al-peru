"""S1-08 — Matriz de cobertura: versión reducida (`matriz_cobertura.casos_pytest` casos fijos) y pruebas del propio generador y de
las comprobaciones. La matriz completa (≈5 000 casos, ~5 min) se corre a mano con `tests/matriz/correr.py`
y su reporte queda en backlog/slice-1/evidencia/matriz.md.

Si falta el cubo, las pruebas FALLAN (agents.md §8): no se salta."""
import copy
import json

import pytest
import yaml

from pap.config import Rutas
from pap.motor import capas as K
from pap.motor.consulta import cargar
from pap.motor.formato import FINO

from conftest import RAIZ_REAL
from matriz import comprobar as C
from matriz import correr as R
from matriz import generar as G

RAIZ = Rutas(RAIZ_REAL).raiz


@pytest.fixture(scope="module")
def mundo():
    assert (RAIZ / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    motor, p, nombre = R.cargar(RAIZ)
    par = G.parametros(RAIZ)
    todos = G.casos(RAIZ, motor.ctx)
    return {"motor": motor, "p": p, "nombre": nombre, "par": par, "todos": todos,
            "reducida": G.reducida(todos, par["casos_pytest"], par["semilla"])}


# ------------------------------------------------------------------------------------------------- el generador

def test_generador_es_determinista(mundo):
    otra = G.casos(RAIZ, mundo["motor"].ctx)
    assert json.dumps(otra, sort_keys=True) == json.dumps(mundo["todos"], sort_keys=True)
    par = mundo["par"]
    assert G.reducida(otra, par["casos_pytest"], par["semilla"]) == mundo["reducida"]
    assert len(mundo["reducida"]) == par["casos_pytest"] == 60
    assert G.reducida(otra, par["casos_pytest"], par["semilla"] + 1) != mundo["reducida"]     # la semilla importa


def test_casos_son_consultas_minimas_validas(mundo):
    for c in mundo["todos"]:
        cargar(copy.deepcopy(c["consulta"]), RAIZ)                  # no lanza


def test_territorios_pedidos(mundo):
    T = G.territorios(RAIZ, mundo["motor"].ctx)["lista"]
    par = mundo["par"]
    por = lambda g: [t for t in T if t["grupo"] == g]               # noqa: E731
    assert len(por("nacional")) == 1 and len(por("departamento")) == 23                 # los 23 departamentos sin Lima
    assert {t["lugar"]["ambito"] for t in por("ambito")} == {"LIMA_METROPOLITANA", "LIMA_REGION", "CALLAO"}
    assert not {"07", "15"} & {t["lugar"]["ubigeo"] for t in por("departamento")}
    provs = por("provincia")
    assert len(provs) == 23 * par["provincias_por_departamento"] and len({t["ubigeo"][:2] for t in provs}) == 23
    ubigeos = {t["ubigeo"] for t in por("distrito")}
    nm = {x["ubigeo"] for x in yaml.safe_load((RAIZ / "curados/capa0/nombres_mostrados.yaml").read_text(encoding="utf-8"))["correcciones"]}
    assert len(nm) == 15 and nm <= ubigeos
    assert {G.Q2, G.Q3, G.ALTO_TRUJILLO, G.SANGANI} <= ubigeos
    sin_sien = [u for u, _ in G.datos_s1_00(RAIZ)["sin_sien"]][: par["distritos_sin_sien"]]
    assert sin_sien == ["050413", "080915", "150121"] and set(sin_sien) <= ubigeos
    hom = [t for t in por("distrito") if t.get("nota") == "homónimo"]
    assert [t["lugar"]["texto"] for t in hom] == ["San Juan", "Independencia", "Ayaviri"] and all(t["elegir"] for t in hom)
    # la muestra estratificada: `distritos_muestra` distritos al azar, de las cuatro regiones naturales
    ub = mundo["motor"].ctx.ubigeos
    region = {str(r.ubigeo_inei): str(r.region_natural_ref) for r in ub[ub.nivel == "distrito"].itertuples()}
    obligatorios = set(nm) | {G.Q2, G.Q3, G.ALTO_TRUJILLO, G.SANGANI} | set(sin_sien)
    muestra = [u for u in ubigeos - obligatorios if u not in {t["ubigeo"] for t in hom}]
    assert len(muestra) == par["distritos_muestra"]
    assert {region[u] for u in muestra} >= {"COSTA", "SIERRA", "SELVA ALTA", "SELVA BAJA"}


def test_periodos_por_tema(mundo):
    ctx = mundo["motor"].ctx
    for tema in ("anemia", "gasto_publico", "pobreza_monetaria", "desnutricion_cronica"):
        anios = G.anios_del_tema(ctx, tema)
        assert G.periodo(ctx, tema, "ultimo") == {"tipo": "ultimo"} and G.periodo(ctx, tema, "serie") == {"tipo": "serie"}
        assert G.periodo(ctx, tema, "intermedio")["anio"] in anios[:-1] + anios[-1:]
        assert G.periodo(ctx, tema, "sin_datos")["anio"] == anios[-1] + 1
    assert {c["periodo"] for c in mundo["todos"]} == set(G.PERIODOS)


def test_temas_e_intenciones_salen_de_intenciones_yaml(mundo):
    temas, intenciones = G.temas_e_intenciones(RAIZ)
    assert {(c["tema"], c["intencion"]) for c in mundo["todos"]} == {(t, i) for t in temas for i in intenciones}


# ------------------------------------------------------------------------------------------------- la versión reducida

def test_reducida_sin_fallos_ni_errores(mundo):
    """Los 60 casos fijos: 0 errores y 0 fallos de las comprobaciones; toda combinación sin datos sale como `no_se_puede` con un
    motivo de S1-05; la reducida cubre las cuatro clases de periodo y los dos tipos de respuesta."""
    resultados = [R.correr_caso(mundo["motor"], mundo["p"], mundo["nombre"], c)[0] for c in mundo["reducida"]]
    fallos = {r["id"]: r["fallos"] for r in resultados if r["fallos"]}
    assert not fallos, json.dumps(fallos, ensure_ascii=False, indent=1)[:3000]
    assert not [r for r in resultados if r["clase"] == "error"]
    clases = {r["clase"] for r in resultados}
    assert {"respondida", "no_se_puede"} <= clases
    sin_datos = [r for r in resultados if r["periodo"] == "sin_datos"]
    assert sin_datos
    for r, c in zip(resultados, mundo["reducida"]):
        if c["espera"] == "no_se_puede":
            assert r["clase"] == "no_se_puede" and r["motivo"], r["id"]
    assert {r["periodo"] for r in resultados} == set(G.PERIODOS)


def test_distritos_sin_establecimientos_del_sien_no_se_puede(mundo):
    """Los 3 distritos sin ninguna fila en el SIEN (S1-00): la anemia «actual» sale `no_se_puede` con motivo `sin_registros`."""
    casos = [c for c in mundo["todos"] if c["ubigeo"] in ("050413", "080915", "150121") and c["tema"] == "anemia"
             and c["intencion"] == "nivel_actual" and c["periodo"] == "ultimo"]
    assert len(casos) == 3 and all(c["espera"] == "no_se_puede" for c in casos)
    for c in casos:
        r, _ = R.correr_caso(mundo["motor"], mundo["p"], mundo["nombre"], c)
        assert (r["clase"], r["motivo"], r["fallos"]) == ("no_se_puede", "sin_registros", []), c["id"]


# ------------------------------------------------------------------------------------------------- las comprobaciones detectan

def respuesta_falsa(**cambios):
    r = {"tipo": "respuesta", "resultados_respuesta": [], "cifras": {"c1": {"territorio_nombre": "Anguía", "anio": 2025, "resultados": []}},
         "capas": {"capa1": {"respuesta_corta": "La anemia en Anguía.", "confianza": {"texto": "Confianza en los datos: alta."},
                             "ojo_al_leer": [], "cifra_clave": None, "palabras": 10},
                   "capa2": {"mas_contexto": [], "avisos": [], "limites": []},
                   "capa3": {"para_citar": ["25,0 %: anemia, Anguía, 2025. Fuente: INEI."], "glosario": []}}}
    for k, v in cambios.items():
        r["capas"]["capa1" if k == "corta" else "capa3" if k == "citar" else "capa2"].update(
            {"corta": {"respuesta_corta": v}, "citar": {"para_citar": v}, "avisos": {"avisos": v}}[k])
    return r


def test_comprobaciones_pasan_una_respuesta_buena(mundo):
    assert C.revisar(respuesta_falsa(), mundo["p"], ["Anguía"]) == []


@pytest.mark.parametrize("mal", ["Anguia", "ANGUIA", "Acari"])
def test_detecta_nombres_sin_tilde(mal):
    nombre = "Acarí" if mal == "Acari" else "Anguía"
    f = C.nombres(respuesta_falsa(corta=f"La anemia en {mal}."), [nombre])
    assert [x["codigo"] for x in f] == ["nombre_mal_escrito"]
    assert C.nombres(respuesta_falsa(corta=f"La anemia en {nombre.upper()} y {nombre}."), [nombre]) == []
    assert [x["codigo"] for x in C.nombres(respuesta_falsa(corta="Zuniga y Zúñiga"), ["Zúñiga"])] == ["nombre_mal_escrito"]


@pytest.mark.parametrize("texto", ["queda {{valor}} sin rellenar", "según R-LENGUAJE-03", "indicador endes_anemia_6_35m_oms2024",
                                   "código NC-ACTUAL", "cruce CR-01", "columna territorio_id", "LIMA_METROPOLITANA"])
def test_detecta_marcadores_y_codigos(texto):
    assert C.marcadores(respuesta_falsa(avisos=[texto]))


def test_detecta_capa1_larga_citas_y_corrector(mundo):
    r = respuesta_falsa()
    r["capas"]["capa1"]["palabras"] = 126
    assert [x["codigo"] for x in C.capa1_maximo(r, mundo["p"])] == ["capa1_sobre_el_maximo"]
    r["capas"]["capa1"]["palabras"] = 125
    assert C.capa1_maximo(r, mundo["p"]) == []
    assert [x["codigo"] for x in C.citas(respuesta_falsa(citar=[]))] == ["cifra_sin_cita"] * 3
    ns = {"tipo": "no_se_puede", "cifras": {}, "capas": respuesta_falsa(corta="Hay 25 % de niños", citar=[])["capas"]}
    assert [x["codigo"] for x in C.citas(ns)] == ["cifra_sin_cita"]
    r = respuesta_falsa()
    r["resultados_respuesta"] = [{"regla": "R-LENGUAJE-03", "accion": "bloquear"}, {"regla": "R-LENGUAJE-06", "accion": "rotular"},
                                 {"regla": "R-LENGUAJE-02", "accion": "suprimir"}]
    assert {x["detalle"]["regla"] for x in C.corrector(r, mundo["p"])} == {"R-LENGUAJE-03", "R-LENGUAJE-02"}
    r["resultados_respuesta"] = [{"regla": "R-X", "accion": "suprimir", "motivo": "metadato_faltante"}]
    assert [x["codigo"] for x in C.validador(r)] == ["validador_error_de_ejecucion"]


# ------------------------------------------------------------------------------------------------- defecto hallado: capa 1 larga

def test_capa1_larga_pasa_el_ojo_sobrante_a_la_capa_2(mundo):
    """S1-08: San Juan de Lurigancho (anemia, SIEN) tenía la capa 1 en 140 palabras (máximo 125). Ahora los «Ojo al leer» que
    no caben pasan a «Avisos» (nada se pierde); la cifra clave, su texto y la confianza no cambian."""
    from pap.motor import preguntar as P
    res = P.preguntar_minima(mundo["motor"], {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"ubigeo": G.Q3}})
    c1, c2 = res["capas"]["capa1"], res["capas"]["capa2"]
    tope = mundo["p"]["respuesta"]["capa1_palabras_max"]["valor"]
    assert c1["palabras"] <= tope
    assert len(c1["ojo_al_leer"]) >= mundo["p"]["respuesta"]["ojo_al_leer"]["min"]
    assert c1["cifra_clave"]["valor"] == f"alrededor de 8{FINO}% (entre 7,8{FINO}% y 8,6{FINO}%)"
    assert c1["confianza"]["nivel"] == "baja" and res["semaforo_respuesta"] == "rojo"
    movidos = {"No la compares con la cifra de todo Lima Metropolitana: miden cosas distintas."}
    assert movidos <= set(c2["avisos"]) and not movidos & set(c1["ojo_al_leer"])
    assert c1["ojo_al_leer"][0] == "No es la cifra de todos los niños de San Juan de Lurigancho: solo de los que fueron a un establecimiento."


def test_ajuste_de_capa1_no_toca_lo_que_cabe():
    ojo = ["uno dos tres", "cuatro cinco"]
    assert K._ajustar_capa1(RAIZ, ojo, ["texto corto", *ojo]) == (ojo, [])
    largo = ["palabra " * 130, "otra cosa", "y otra"]
    quedan, pasan = K._ajustar_capa1(RAIZ, largo, ["x", *largo])
    assert quedan == largo[:1] and pasan == largo[1:]                # nunca baja de ojo_al_leer.min (1)
