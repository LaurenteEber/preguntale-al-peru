"""S1-04 — Plantillas por intención: generalizan Q1–Q4 a cualquier lugar y tema, con los textos en curados/motor/textos/.

La regresión de Q1–Q4 contra la referencia está en test_regresion_q1_q4.py (fase 2). Aquí: (1) nada fijo en el código
(lugares, años, ids de cifra o de indicador), (2) otras combinaciones tema × intención × lugar salen sin marcadores,
códigos internos ni infracciones del corrector y con la capa 1 dentro del máximo de R-04, (3) los parámetros
`pendientes_dueno` y el umbral de R-REG-07 se leen de sus archivos, (4) los nombres antiguos (q1_evolucion…) se traducen y
los q*.yaml dan las mismas capas que el camino nuevo. Si falta el cubo, las pruebas FALLAN (agents.md §8)."""
import ast
import copy
import re
from types import SimpleNamespace

import pytest
import yaml

from pap.config import Rutas
from pap.motor import formato as fmt
from pap.motor import plantillas as PLT
from pap.motor import preguntar as PRE
from pap.motor.consulta import cargar
from pap.motor.planificador import planificar
from pap.motor.respuesta import Motor
from pap.motor.territorio import Resuelto, resolver
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL

# los patrones de «código interno» y la lista de textos visibles son los de la matriz de cobertura (S1-08): una sola copia
from matriz.comprobar import CODIGOS, visible  # noqa: E402


@pytest.fixture(scope="module")
def raiz():
    r = Rutas(RAIZ_REAL).raiz
    assert (r / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    return r


@pytest.fixture(scope="module")
def motor(raiz):
    return Motor(cargar_contexto(raiz))


def plan_de(raiz, motor, intencion, tema=None, lugar=None, extremo=None, comparar_con=None, periodo=None, parametros=None):
    c = {"intencion": intencion, "pregunta_original": "pregunta de prueba"}
    if tema:
        c["tema"] = tema
    if periodo:
        c["periodo"] = periodo
    c["territorio"] = extremo if extremo else {"texto": lugar}
    if comparar_con:
        c["comparar_con"] = {"texto": comparar_con}
    cm = cargar(c, raiz)
    if extremo:
        res = resolver(extremo["dentro_de"], motor.ctx) if extremo.get("dentro_de") else None
    else:
        res = resolver(cm["territorio"], motor.ctx)
        if comparar_con:
            res = [res, resolver(cm["comparar_con"], motor.ctx)]
    return planificar(cm, res, motor, parametros=parametros)


def revisar(raiz, r):
    """Los límites de S1-04 sobre una respuesta: sin marcadores ni códigos internos, sin infracciones del corrector y capa 1 dentro del máximo."""
    p = yaml.safe_load((raiz / "curados" / "motor" / "parametros_motor.yaml").read_text(encoding="utf-8"))["respuesta"]
    for t in visible(r):
        for cod in CODIGOS:
            assert not re.search(cod, t), (cod, t)
    infr = [x for x in r["resultados_respuesta"] if x["regla"] in p["infracciones_corrector"]["valor"] and x["accion"] != "rotular"]
    assert not infr, infr
    assert r["capas"]["capa1"]["palabras"] <= p["capa1_palabras_max"]["valor"], r["capas"]["capa1"]["palabras"]
    assert p["ojo_al_leer"]["min"] <= len(r["capas"]["capa1"]["ojo_al_leer"]) <= p["ojo_al_leer"]["max"]
    # C-04 (dueño, 3/11/2026): toda respuesta lleva al menos un código «No permite concluir» (NC-NIVEL de respaldo)
    assert r["ficha"]["corta"].splitlines()[-1].strip() != "No permite concluir:"
    assert not any(x["accion"] in ("suprimir", "bloquear") and x["regla"].startswith("R-LENGUAJE") for x in r["resultados_respuesta"])


# ------------------------------------------------------------------------- 1. nada fijo en el código

def _cadenas_del_codigo(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    docs = set()
    for n in ast.walk(arbol):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body and isinstance(n.body[0], ast.Expr) \
                and isinstance(n.body[0].value, ast.Constant) and isinstance(n.body[0].value.value, str):
            docs.add(id(n.body[0].value))
    return [n.value for n in ast.walk(arbol) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs]


PERMITIDAS = {"mapa_grupo_robusto", "sien_umbral_tamizaje_pct"}   # tipo de grupo del plan (S1-03) y clave de parámetro de R-REG-07


def test_sin_lugares_anios_ni_ids_en_el_codigo(raiz):
    """Criterio de S1-04: ni nombres de lugares, ni años fijos, ni ids de cifra o de indicador en el código de las plantillas."""
    u = Motor(cargar_contexto(raiz, con_cubo=False)).ctx.ubigeos
    lugares = {str(x) for x in u.nombre_mostrado.unique() if len(str(x)) > 3}
    lugares |= {"LIMA_METROPOLITANA", "LIMA_REGION", "CALLAO", "Perú"}
    malos = []
    for s in _cadenas_del_codigo(raiz / "src" / "pap" / "motor" / "plantillas.py"):
        if s in PERMITIDAS:
            continue
        if re.search(r"\b(19|20)\d\d\b", s) or re.search(r"\b(endes|sien|enaho|gasto_ex|mapa_pobreza)_?[a-z0-9]", s) \
                or re.search(r"_(19|20)\d\d\b", s) or any(re.search(rf"\b{re.escape(l)}\b", s) for l in lugares):
            malos.append(s)
    assert not malos, malos


def test_textos_en_archivos(raiz):
    """Los textos de las plantillas viven en curados/motor/textos/: no quedan oraciones (varias palabras con tilde o signos) en el código."""
    frases = [s for s in _cadenas_del_codigo(raiz / "src" / "pap" / "motor" / "plantillas.py")
              if len(s.split()) >= 4 and not s.startswith(("{{", "{", "codigo/")) and not re.fullmatch(r"[\w\s{}:.%|\\()\[\]+*?^$-]+", s)]
    assert not frases, frases
    for nombre in ("comunes", "nivel_actual", "evolucion", "comparacion", "identificar_extremo", "cruce_efecto"):
        assert (raiz / "curados" / "motor" / "textos" / "plantillas" / f"{nombre}.yaml").exists(), nombre
    assert (raiz / "curados" / "motor" / "textos" / "bloques.yaml").exists()


# ------------------------------------------------------------------------- 2. otras combinaciones

COMBINACIONES = [
    ("nivel_actual", "anemia", "departamento de Puno", {}),
    ("nivel_actual", "anemia", "Ayaviri, Melgar", {}),
    ("nivel_actual", "anemia", "distrito de Pangoa", {}),
    ("nivel_actual", "desnutricion_cronica", "departamento de Cusco", {}),
    ("nivel_actual", "pobreza_monetaria", "departamento de Cajamarca", {}),
    ("nivel_actual", "pobreza_monetaria", "distrito de Anguía", {}),
    ("nivel_actual", "gasto_publico", "departamento de Ayacucho", {}),
    ("evolucion", "anemia", "departamento de Puno", {}),
    ("evolucion", "anemia", "Ayaviri, Melgar", {}),
    ("evolucion", "desnutricion_cronica", "departamento de Cusco", {}),
    ("evolucion", "pobreza_monetaria", "departamento de Cajamarca", {}),
    ("evolucion", "gasto_publico", "departamento de Ayacucho", {}),
    ("comparacion", "anemia", "departamento de Puno", {"comparar_con": "departamento de Cusco"}),
    ("comparacion", "desnutricion_cronica", "departamento de Puno", {"comparar_con": "departamento de Cusco"}),
    ("efecto", "gasto_publico", "departamento de Ayacucho", {}),
    ("efecto", "gasto_publico", "Lima Metropolitana", {}),
    ("cruce", "gasto_publico", "San Juan de Lurigancho", {}),
    ("cruce", "gasto_publico", "departamento de Puno", {}),
    ("identificar_extremo", "anemia", None, {"extremo": {"nivel": "departamento"}}),
    ("identificar_extremo", "desnutricion_cronica", None, {"extremo": {"nivel": "departamento"}}),
    ("identificar_extremo", "pobreza_monetaria", None, {"extremo": {"nivel": "departamento", "dentro_de": {"nacional": True}}}),
]


@pytest.mark.parametrize("intencion,tema,lugar,kw", COMBINACIONES, ids=lambda x: str(x)[:40])
def test_combinaciones(raiz, motor, intencion, tema, lugar, kw):
    plan = plan_de(raiz, motor, intencion, tema, lugar, **kw)
    r = motor.responder(plan)
    if plan["no_se_puede"] and PRE.motivo_total(motor, plan):     # S1-05: «no se puede» total, con su motivo y sin ninguna cifra
        assert r["tipo"] == "no_se_puede" and r["motivo"]["codigo"] == plan["no_se_puede"]["motivo"] and r["cifras"] == {}
        assert r["capas"]["capa1"]["respuesta_corta"].startswith(("No ", "Todavía no "))
        assert r["capas"]["capa1"]["lo_mas_cercano"]["texto"]
        return
    assert r["tipo"] == "respuesta"
    revisar(raiz, r)
    assert r["capas"]["capa1"]["respuesta_corta"]
    assert set(r["cifras"]) == set(plan_usadas(r))
    if lugar and not kw.get("comparar_con"):
        nombre = r["cifras"][next(iter(r["cifras"]))]["territorio_nombre"]
        assert re.sub(r"\s*\([^)]*\)", "", nombre) in " ".join(visible(r)) or intencion == "identificar_extremo"


def plan_usadas(r):
    return [i for i in r["cifras"]]


def test_texto_por_lugar_y_tema(raiz, motor):
    """El mismo texto sirve a otro lugar: el nombre y el año salen del plan y de la cifra."""
    r = motor.responder(plan_de(raiz, motor, "nivel_actual", "anemia", "Ayaviri, Melgar"))
    r2 = motor.responder(plan_de(raiz, motor, "nivel_actual", "anemia", "distrito de Pangoa"))
    assert "Ayaviri" in r["capas"]["capa1"]["respuesta_corta"] and "Pangoa" not in r["capas"]["capa1"]["respuesta_corta"]
    assert "Pangoa" in r2["capas"]["capa1"]["respuesta_corta"] and "Ayaviri" not in " ".join(visible(r2))
    d = motor.responder(plan_de(raiz, motor, "nivel_actual", "desnutricion_cronica", "departamento de Cusco"))
    assert "Cusco" in " ".join(visible(d)) and "anemia" not in d["capas"]["capa1"]["respuesta_corta"].lower()


def test_nombre_largo_solo_una_vez_en_capa_2(raiz, motor):
    r = motor.responder(plan_de(raiz, motor, "nivel_actual", "anemia", "Ayaviri, Melgar"))
    todo = " ".join(visible(r))
    assert todo.count("Ayaviri (Melgar, Puno)") == 1
    assert "Melgar" not in r["capas"]["capa1"]["respuesta_corta"] + " ".join(r["capas"]["capa1"]["ojo_al_leer"])


def test_comparacion_dice_cual_es_mayor_solo_con_prueba(raiz, motor):
    """S1-09 (H1, R-ENC-11): Puno (56,1 %) y Cusco (42,8 %) difieren con p < 0,05 → se dice cuál es mayor; sin prueba posible (el país
    contra un departamento, que lo contiene) no se dice. Las pruebas por caso están en test_s1_09_correcciones.py."""
    r = motor.responder(plan_de(raiz, motor, "comparacion", "anemia", "departamento de Puno", comparar_con="departamento de Cusco"))
    t = " ".join(visible(r))
    assert "Puno" in t and "Cusco" in t and "mayor en Puno que en Cusco" in r["capas"]["capa1"]["respuesta_corta"]
    r = motor.responder(plan_de(raiz, motor, "comparacion", "anemia", "Perú", comparar_con="departamento de Puno"))
    assert not re.search(r"\b(mayor|menor|más alta que|más baja que)\b", " ".join(visible(r)))


def test_extremo_departamental_es_un_grupo_sin_orden(raiz, motor):
    r = motor.responder(plan_de(raiz, motor, "identificar_extremo", "desnutricion_cronica", None, extremo={"nivel": "departamento"}))
    assert "no se puede ordenar" in r["capas"]["capa1"]["respuesta_corta"].lower() or "sin diferencias" in r["capas"]["capa1"]["respuesta_corta"]
    nombres = re.findall(r"([A-ZÁÉÍÓÚÑ][\w ñáéíóú]+) \(\d", r["capas"]["capa2"]["mas_contexto"][0]["texto"])
    assert nombres == sorted(nombres)                          # orden alfabético: no insinúa un ranking


# ------------------------------------------------------------------------- 3. parámetros del dueño y R-REG-07

def con_parametros(monkeypatch, raiz, **pendientes):
    p = copy.deepcopy(PLT.parametros(raiz))
    for k, v in pendientes.items():
        p["pendientes_dueno"][k]["valor"] = v
    monkeypatch.setattr(PLT, "parametros", lambda r: p)
    return p


def test_conteo_sien_x02(raiz, motor, monkeypatch):
    q2 = lambda: motor.responder(plan_de(raiz, motor, "nivel_actual", "anemia", "Ayaviri, Melgar"))   # noqa: E731
    base = q2()
    assert not any("Cuántos niños se midieron" == t["titulo"] for t in base["capas"]["capa2"]["mas_contexto"])
    con_parametros(monkeypatch, raiz, mostrar_conteo_sien=True)
    r = q2()
    t = next(t for t in r["capas"]["capa2"]["mas_contexto"] if t["titulo"] == "Cuántos niños se midieron")
    assert "547" in t["texto"] and "52" in t["texto"] and "Ayaviri" in t["texto"]
    revisar(raiz, r)
    assert r["capas"]["capa1"] == base["capas"]["capa1"]         # la capa 1 no cambia: solo una tarjeta en la capa 2


def test_cr01_mismo_anio_x03(raiz, motor, monkeypatch):
    base = motor.responder(plan_de(raiz, motor, "efecto", "gasto_publico", "San Juan de Lurigancho"))
    assert not any(t["titulo"].startswith("Gasto en Lima Metropolitana en") for t in base["capas"]["capa2"]["mas_contexto"])
    p = con_parametros(monkeypatch, raiz, cr01_mismo_anio=True)
    plan = plan_de(raiz, motor, "efecto", "gasto_publico", "San Juan de Lurigancho", parametros=p)
    r = motor.responder(plan)
    assert len(plan["cifras"]) == len(base["consulta"]["cifras"]) + 1
    assert any(t["titulo"].startswith("Gasto en Lima Metropolitana en 2024") for t in r["capas"]["capa2"]["mas_contexto"])
    revisar(raiz, r)


def _cifra(**kw):
    c = SimpleNamespace(medida="proporcion", valor=38.6, ic_inf=32.5, ic_sup=44.9, semaforo_cifra="ambar", estado_cifra="publicable", **kw)
    c.get = lambda k, d=None: getattr(c, k, d)
    return c


def test_intervalo_visible_x04():
    """`ambos` (como hoy): capa 1 con el intervalo propio. `uno`: con el del INEI si existe, si no el propio."""
    con = _cifra(ic_inei={"ic_inf": 32.0, "ic_sup": 45.1})
    sin = _cifra(ic_inei=None)
    ambos, uno = {"intervalo_visible": "ambos"}, {"intervalo_visible": "uno"}
    f = lambda t: t.replace(" %", fmt.FINO + "%")   # noqa: E731
    assert PLT.valor_cifra(con, ambos) == PLT.valor_cifra(con) == f("alrededor de 39 % (entre 32 % y 45 %)")
    assert PLT.valor_cifra(con, uno) == f("alrededor de 39 % (entre 32 % y 45 %)")
    con.ic_inf, con.ic_sup = 30.2, 47.9
    assert PLT.valor_cifra(con, ambos) == f("alrededor de 39 % (entre 30 % y 48 %)")
    assert PLT.valor_cifra(con, uno) == f("alrededor de 39 % (entre 32 % y 45 %)")
    assert PLT.valor_cifra(sin, uno) == PLT.valor_cifra(sin, ambos)


def test_umbral_de_tamizaje_sale_de_r_reg_07(raiz, motor):
    """El texto del aviso de cobertura usa el umbral de R-REG-07 (`sien_umbral_tamizaje_pct`), no una constante del código."""
    plan = plan_de(raiz, motor, "nivel_actual", "anemia", "Ayaviri, Melgar")
    params = motor.ctx.reglas["R-REG-07"]["parametros"]
    original = params["sien_umbral_tamizaje_pct"]
    try:
        base = " ".join(t["texto"] for t in motor.responder(plan)["capas"]["capa2"]["mas_contexto"])
        params["sien_umbral_tamizaje_pct"] = 70
        r = motor.responder(plan)
        cob = next(t["texto"] for t in r["capas"]["capa2"]["mas_contexto"] if t["titulo"].startswith("¿A cuántos"))
    finally:
        params["sien_umbral_tamizaje_pct"] = original
    assert "a más o a menos de la mitad" in base
    assert "En Puno, a menos de 70 % de los niños se les midió la hemoglobina" in cob


def test_intervalo_visible_y_conteo_estan_en_parametros(raiz):
    p = PLT.parametros(raiz)["pendientes_dueno"]
    assert p["mostrar_conteo_sien"]["valor"] is False and p["cr01_mismo_anio"]["valor"] is False
    assert p["intervalo_visible"]["valor"] == "ambos" and p["intervalo_visible"]["permitidos"] == ["ambos", "uno"]


# ------------------------------------------------------------------------- 4. nombres antiguos

@pytest.mark.parametrize("q", ["q1", "q2", "q3", "q4"])
def test_nombres_antiguos_dan_las_mismas_capas(raiz, motor, q):
    """q1_evolucion… se traducen a la plantilla de su intención: el q*.yaml da las mismas capas que el camino nuevo
    (salvo Q1, cuyo q1.yaml sigue trayendo la cifra de 2022 que el plan ya no trae: C-01, no se usa en el texto)."""
    antiguo = yaml.safe_load((raiz / "tests" / "fixtures" / "consultas_piloto" / f"{q}.yaml").read_text(encoding="utf-8"))
    assert antiguo["plantilla"] in PLT.parametros(raiz)["plantillas"]["nombres_antiguos"]["valor"]
    cm = cargar(raiz / "curados" / "motor" / "consultas_minimas" / f"{q}.json", raiz)
    t = cm["territorio"]
    res = resolver(t.get("dentro_de"), motor.ctx) if "nivel" in t and "dentro_de" in t else (None if "nivel" in t else resolver(t, motor.ctx))
    nuevo = motor.responder(planificar(cm, res, motor))
    viejo = motor.responder(antiguo)
    sin_ids = lambda c: {**c, "cifra_clave": c["cifra_clave"] and {k: v for k, v in c["cifra_clave"].items() if k != "ids"}}   # noqa: E731
    assert sin_ids(viejo["capas"]["capa1"]) == sin_ids(nuevo["capas"]["capa1"])      # los ids de los q*.yaml son otros
    if q == "q1":          # AD-1 (S1-13): el q1.yaml archivado no trae la cifra vigente de 2024 que el plan nuevo agrega al final
        mc = nuevo["capas"]["capa2"]["mas_contexto"]
        assert mc[-1]["titulo"] == "2024 y 2025, con la forma de medir actual"
        nuevo["capas"]["capa2"] = {**nuevo["capas"]["capa2"], "mas_contexto": mc[:-1]}
        citas = nuevo["capas"]["capa3"]["para_citar"]
        assert "(forma de medir vigente desde 2024), Huancavelica, 2024." in citas[-1]
        nuevo["capas"]["capa3"] = {**nuevo["capas"]["capa3"], "para_citar": citas[:-1]}
    assert viejo["capas"]["capa2"] == nuevo["capas"]["capa2"]
    assert viejo["capas"]["capa3"]["glosario"] == nuevo["capas"]["capa3"]["glosario"]
    assert viejo["capas"]["capa3"]["para_citar"] == nuevo["capas"]["capa3"]["para_citar"]
    assert viejo["semaforo_respuesta"] == nuevo["semaforo_respuesta"]
    assert not re.search(r"\{\{|\}\}", viejo["texto"])
