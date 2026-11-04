"""S1-05 — Respuestas de «no se puede» y aclaraciones.

Un caso por motivo: la respuesta corta dice primero lo que no se puede (empieza con «No …» o «Todavía no …») en no más de
`no_se_puede.respuesta_corta_max_oraciones` oraciones, ofrece «Lo más cercano que sí tenemos» (solo lo que el validador deja
publicar), deja el motivo en «Más contexto» y no muestra ninguna cifra: ni la suprimida ni una inventada (todo número visible es un
año). Pasa el corrector (`respuesta.infracciones_corrector`), no trae códigos internos y la capa 1 queda dentro del máximo de R-04.
Los motivos que R-LENGUAJE-05 ya trae (`motivos_codificados`) se reutilizan; solo se agregan los que no trae.
Si falta el cubo, las pruebas FALLAN (agents.md §8). Los dos casos que el cubo no da (cifra suprimida por precisión y por falta de
inferencia: ninguna cifra del cubo está en ese estado hoy) se prueban con el estado que el validador dejaría, sin tocar datos."""
import json
import re

import pytest
import yaml

from pap.config import Rutas
from pap.motor import preguntar as P
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto
from pap.motor.validador.nucleo import Resultado
from pap.motor.validador.validador import Evaluacion

from conftest import RAIZ_REAL

CODIGOS = [r"\{\{", r"\}\}", r"\{[a-z_0-9]+\}", r"\bR-[A-Z]+-\d+", r"\bNC-[A-Z]", r"\bCR-\d", r"\b[a-z]+_[a-z0-9]+_[a-z0-9_]+\b",
           r"\b[A-Z]{3,}_[A-Z_]+\b", r"\bNone\b", r"\bnan\b"]
INICIOS = ("No ", "Todavía no ")


@pytest.fixture(scope="module")
def raiz():
    r = Rutas(RAIZ_REAL).raiz
    assert (r / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    return r


@pytest.fixture(scope="module")
def motor(raiz):
    return Motor(cargar_contexto(raiz))


@pytest.fixture(scope="module")
def parametros(raiz):
    return yaml.safe_load((raiz / "curados" / "motor" / "parametros_motor.yaml").read_text(encoding="utf-8"))


def consulta(intencion="nivel_actual", tema="anemia", lugar="departamento de Puno", **extra):
    c = {"intencion": intencion, "pregunta_original": "pregunta de prueba", "territorio": {"texto": lugar}}
    if tema:
        c["tema"] = tema
    c.update(extra)
    return c


def visibles(r):
    c = r["capas"]
    out = [c["capa1"]["respuesta_corta"], c["capa1"]["confianza"]["texto"], *c["capa1"]["ojo_al_leer"]]
    if c["capa1"].get("lo_mas_cercano"):
        out += [c["capa1"]["lo_mas_cercano"]["titulo"], c["capa1"]["lo_mas_cercano"]["texto"]]
    for t in c["capa2"]["mas_contexto"]:
        out += [t["titulo"], t["texto"], t["etiqueta"] or ""]
    out += c["capa2"]["avisos"] + c["capa2"]["limites"] + c["capa3"]["para_citar"] + [r["texto"], r["ficha"]["corta"]]
    return out


def revisar(raiz, parametros, r, *, motivo):
    """Lo que toda respuesta de «no se puede» cumple (criterios de S1-05)."""
    assert r["tipo"] == "no_se_puede" and r["motivo"]["codigo"] == motivo, (r["tipo"], r["motivo"])
    capa1 = r["capas"]["capa1"]
    corta = capa1["respuesta_corta"]
    assert corta.startswith(INICIOS), corta                                   # primero, lo que no se puede
    oraciones = [x for x in re.split(r"(?<=[.!?])\s+", corta.strip()) if x]
    assert 1 <= len(oraciones) <= parametros["no_se_puede"]["respuesta_corta_max_oraciones"]["valor"], oraciones
    assert capa1["lo_mas_cercano"]["titulo"] == "Lo más cercano que sí tenemos" and capa1["lo_mas_cercano"]["texto"]
    assert capa1["cifra_clave"] is None and capa1["confianza"]["nivel"] == "sin cifra"
    assert capa1["palabras"] <= parametros["respuesta"]["capa1_palabras_max"]["valor"]
    assert [t for t in r["capas"]["capa2"]["mas_contexto"] if t["titulo"] == "Por qué no se puede" and t["texto"]]   # el motivo
    assert r["capas"]["capa3"]["para_citar"] == ["Esta respuesta no publica cifras."]       # ninguna cifra que citar (P-02); S1-09, H16
    assert r["cifras"] == {} and r["cruces"] == []
    for t in visibles(r):
        for cod in CODIGOS:
            assert not re.search(cod, t), (cod, t)
        assert not [d for d in re.findall(r"\d+", t) if not re.fullmatch(r"(19|20)\d\d", d)], t   # solo años: ninguna cifra
    infr = [x for x in r["resultados_respuesta"] if x["regla"] in parametros["respuesta"]["infracciones_corrector"]["valor"]
            and x["accion"] != "rotular"]
    assert not infr, infr
    assert not any(x["accion"] in ("suprimir", "bloquear") and x["regla"].startswith("R-LENGUAJE") for x in r["resultados_respuesta"])
    ficha = r["ficha"]["corta"].splitlines()
    assert len(ficha) <= 4 and ficha[-1].startswith("No permite concluir: ") and len(ficha[-1]) > len("No permite concluir: ")
    assert len(r["alternativas"]) <= 2                                           # max_alternativas de R-LENGUAJE-05
    assert not any(re.search(r"\bvalor\b", k) for a in r["cifras_no_publicadas"] for k in a)   # nunca el valor suprimido
    texto = r["capas"]["capa1"]["lo_mas_cercano"]["texto"]
    return corta, texto


def sin_valor(r, *valores):
    """Ningún valor suprimido (ni redondeado) aparece en el JSON ni en el markdown de la respuesta."""
    from pap.motor import ficha as F
    todo = json.dumps(r, ensure_ascii=False, default=str) + F.markdown(r)
    for v in valores:
        for s in {str(v), f"{v:.1f}", f"{v:.2f}", f"{v:.1f}".replace(".", ","), f"{v:.2f}".replace(".", ",")}:
            assert not re.search(rf"(?<![\d.,]){re.escape(s)}(?![\d])", todo), s


# ------------------------------------------------------------------------- un caso por motivo

def test_tema_fuera_del_piloto(raiz, motor, parametros):
    """«Todavía no tenemos datos de ese tema», con la lista de temas disponibles; sale por la misma ruta que las demás."""
    r = P.preguntar_minima(motor, consulta(tema="pobreza_extrema", lugar="Puno"))
    corta, cercano = revisar(raiz, parametros, r, motivo="tema_fuera_del_piloto")
    assert corta == "Todavía no tenemos datos de ese tema."
    for tema in ("anemia", "desnutrición crónica", "pobreza", "gasto público en salud y nutrición infantil"):
        assert tema in cercano
    assert r["motivo"]["regla_lenguaje_05"] == "sin_fuente_en_catalogo"
    assert r["cifras_no_publicadas"] == []


def test_anio_sin_datos_ofrece_el_mas_cercano(raiz, motor, parametros):
    """`no_se_puede.anio_mas_cercano` = anterior_primero: el año anterior más reciente; si no hay, el último disponible (S1-09, H7)."""
    assert parametros["no_se_puede"]["anio_mas_cercano"]["valor"] == "anterior_primero"
    r = P.preguntar_minima(motor, consulta(periodo={"tipo": "anio", "anio": 2030}))
    corta, cercano = revisar(raiz, parametros, r, motivo="anio_sin_datos")
    assert "2030" in corta and "2025" in cercano and r["alternativas"][0]["anio"] == 2025          # el anterior más reciente
    assert r["motivo"]["regla_lenguaje_05"] == "anio_no_disponible"
    r = P.preguntar_minima(motor, consulta(periodo={"tipo": "anio", "anio": 2019}))                # no hay anterior: el último disponible
    corta, cercano = revisar(raiz, parametros, r, motivo="anio_sin_datos")
    assert "2019" in corta and "2025" in cercano and r["alternativas"][0]["anio"] == 2025
    assert r["alternativas"][0]["lugar"] == {"ubigeo": "21"}                                         # y lo que se podría preguntar


def test_nivel_no_valido_ofrece_el_nivel_superior(raiz, motor, parametros):
    """`no_se_puede.nivel_alternativo` = superior_inmediato (R-REG-02): la desnutrición no tiene cifra por distrito."""
    r = P.preguntar_minima(motor, consulta(tema="desnutricion_cronica", lugar="Ayaviri, Melgar"))
    corta, cercano = revisar(raiz, parametros, r, motivo="nivel_no_valido")
    assert "distrito" in corta and "Puno" in cercano and "departamento" in cercano
    assert r["alternativas"][0]["nivel"] == "departamento" and r["alternativas"][0]["territorio_id"] == "21"
    assert r["motivo"]["regla_lenguaje_05"] == "nivel_no_representativo"


def test_cifra_suprimida_por_privacidad(raiz, motor, parametros):
    """El SIEN de un distrito pequeño: el validador la suprime (divulgación, P-04). Se detecta en su estado y su traza; el valor no se muestra."""
    spec = {"id": "x", "indicador": "sien_anemia_tamizados_6_35m", "anio": 2025, "nivel": "distrito", "territorio": "030218", "rol": "principal"}
    cons = {"territorio": {"nivel": "distrito", "nombre_pedido": "Turpo"}, "intencion": "nivel_actual", "periodo": {"tipo": "ultimo"}}
    c = motor.evaluar(motor.cifra(spec, cons))
    assert c.estado_cifra == "suprimida" and "divulgacion" in c.evaluacion.motivos()
    valor = float(motor.fila(spec["indicador"], 2025, "distrito", "030218")["valor"])
    r = P.preguntar_minima(motor, consulta(lugar="Turpo, Andahuaylas"))
    corta, cercano = revisar(raiz, parametros, r, motivo="privacidad")
    assert "Turpo" in corta and "reconocerse" in corta and "provincia" in cercano
    assert r["alternativas"][0]["nivel"] == "provincia" and r["cifras_no_publicadas"][0]["estado"] == "suprimida"
    assert r["cifras_no_publicadas"][0]["motivo"] == "privacidad" and r["motivo"]["regla_lenguaje_05"] is None   # lo agrega S1-05
    sin_valor(r, valor)


def _forzar(monkeypatch, motor, motivo, regla="R-ENC-05"):
    """El estado que el validador dejaría para una cifra suprimida por ese motivo (ninguna del cubo lo está hoy)."""
    original = motor.evaluar

    def evaluar(c):
        c = original(c)
        if c.rol == "principal" and c.nivel in ("departamento",) and not c.get("sin_fila"):
            c.estado_cifra, c.accion_final = "suprimida", "suprimir"
            c.evaluacion = Evaluacion(resultados=[Resultado(regla, "suprimir", motivo)], accion_final="suprimir", estado_cifra="suprimida")
            c.traza = [{"nivel": c.nivel, "estado": "suprimida", "motivos": [motivo]}]
        return c
    monkeypatch.setattr(motor, "evaluar", evaluar)


@pytest.mark.parametrize("motivo_validador,esperado,regla", [("precision", "precision", "pocos_casos"),
                                                               ("pocos_casos", "precision", "pocos_casos"),
                                                               ("fuera_de_cobertura", "nivel_sin_inferencia", "nivel_no_representativo")])
def test_cifra_suprimida_por_precision_o_inferencia(raiz, motor, parametros, monkeypatch, motivo_validador, esperado, regla):
    valor = float(motor.fila("endes_anemia_6_35m_oms2024", 2025, "departamento", "21")["valor"])
    _forzar(monkeypatch, motor, motivo_validador)
    r = P.preguntar_minima(motor, consulta(lugar="departamento de Puno"))
    revisar(raiz, parametros, r, motivo=esperado)
    assert r["motivo"]["regla_lenguaje_05"] == regla
    assert r["cifras_no_publicadas"] and all(a["estado"] == "suprimida" for a in r["cifras_no_publicadas"])
    sin_valor(r, valor)
    assert not r["alternativas"] or r["alternativas"][0]["nivel"] == "nacional"   # el departamento no se ofrece: está suprimido


def test_distrito_creado_despues_del_ultimo_dato(raiz, motor, parametros):
    """Sangani (código provisional, T-01): sin datos propios; ofrece su distrito de origen y su provincia (T-04)."""
    r = P.preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"ubigeo": "120307"}})
    corta, cercano = revisar(raiz, parametros, r, motivo="distrito_creado_despues")
    assert "Sangani" in corta and "distrito nuevo" in corta
    assert [a["tipo"] for a in r["alternativas"]] == ["origen", "provincia"]
    assert "Perené" in cercano and "Chanchamayo" in cercano
    assert r["motivo"]["detalle"]["anio_datos_desde"] > r["motivo"]["detalle"]["anio_ultimo_dato"]


def test_distrito_antiguo_con_limites_nuevos_sigue_respondiendo(raiz, motor):
    """Perené cambió de límites en 2026 pero tiene una versión histórica con datos: el validador la publica y S1-05 no la tapa."""
    r = P.preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "anemia", "territorio": {"ubigeo": "120302"}})
    assert r["tipo"] == "respuesta"


def test_intencion_no_soportada_para_el_tema(raiz, motor, parametros):
    """El orden del gasto de 26 unidades no está construido (R-GASTO-13)."""
    r = P.preguntar_minima(motor, {"intencion": "identificar_extremo", "tema": "gasto_publico", "territorio": {"nivel": "departamento"}})
    corta, cercano = revisar(raiz, parametros, r, motivo="intencion_no_soportada")
    assert "gasto público" in corta + cercano and "lugar concreto" in cercano


def test_evolucion_de_un_registro_de_un_solo_anio(raiz, motor, parametros):
    """Como Q3: la evolución de la anemia por distrito sale del SIEN, que solo tiene 2025."""
    r = P.preguntar_minima(motor, consulta(intencion="evolucion", lugar="Ayaviri, Melgar"))
    corta, cercano = revisar(raiz, parametros, r, motivo="serie_un_solo_anio")
    assert "Ayaviri" in cercano and "2025" in cercano and "no tenemos dos años" in corta
    assert r["alternativas"][0]["anio"] == 2025 and r["motivo"]["regla_lenguaje_05"] == "anio_no_disponible"


def test_extremo_dentro_de_un_lugar(raiz, motor, parametros):
    r = P.preguntar_minima(motor, {"intencion": "identificar_extremo", "tema": "anemia",
                                   "territorio": {"nivel": "departamento", "dentro_de": {"texto": "departamento de Puno"}}})
    corta, cercano = revisar(raiz, parametros, r, motivo="extremo_dentro_de_no_soportado")
    assert "dentro de Puno" in corta and "todo el país" in cercano
    assert r["alternativas"][0]["consulta_minima"]["territorio"] == {"nivel": "departamento"}


def test_sin_registros_en_el_lugar(raiz, motor, parametros):
    """Cajamarquilla (Ocros) no tiene filas del SIEN: la cifra viene `sin_fila`. Ofrece el nivel superior verificado."""
    spec = {"id": "x", "indicador": "sien_anemia_tamizados_6_35m", "anio": 2025, "nivel": "distrito", "territorio": "021403", "rol": "principal"}
    cons = {"territorio": {"nivel": "distrito", "nombre_pedido": "Cajamarquilla"}, "intencion": "nivel_actual", "periodo": {"tipo": "ultimo"}}
    assert motor.cifra(spec, cons).sin_fila
    r = P.preguntar_minima(motor, consulta(lugar="Cajamarquilla, Ocros"))
    corta, cercano = revisar(raiz, parametros, r, motivo="sin_registros")
    assert "No tenemos registros" in corta and "Cajamarquilla" in corta and "provincia de Ocros" in cercano
    assert r["cifras_no_publicadas"][0]["motivo"] == "sin_registros" and r["alternativas"][0]["nivel"] == "provincia"


# ------------------------------------------------------------------------- parcial, aclaración y límites

def test_cruce_fuera_de_la_lista_blanca_es_parcial(raiz, motor, parametros):
    """R-LENGUAJE-05 parcial: se responde con las cifras separadas y se dice primero lo que falta (no un «no se puede» total)."""
    r = P.preguntar_minima(motor, consulta(intencion="efecto", tema="desnutricion_cronica"))
    assert r["tipo"] == "respuesta" and r["respuesta_parcial"] and r["cifras"]
    assert r["capas"]["capa1"]["respuesta_corta"].startswith("No podemos decir si una cifra explica la otra")
    assert [t for t in r["capas"]["capa2"]["mas_contexto"] if t["titulo"] == "Lo que no pudimos mostrar"]
    assert not [x for x in r["resultados_respuesta"] if x["regla"] in parametros["respuesta"]["infracciones_corrector"]["valor"]
                and x["accion"] != "rotular"]


def test_principal_suprimida_con_otra_publicable_es_parcial(raiz, motor, parametros, monkeypatch):
    """Dos formas de medir la anemia: si una principal no se publica y la otra sí, se sigue respondiendo y se dice lo que falta."""
    original = motor.evaluar

    def evaluar(c):
        c = original(c)
        if c.indicador_id == "endes_anemia_6_35m" and c.rol == "principal":
            c.estado_cifra, c.accion_final = "suprimida", "suprimir"
            c.evaluacion = Evaluacion(resultados=[Resultado("R-ENC-05", "suprimir", "precision")], accion_final="suprimir", estado_cifra="suprimida")
        return c
    monkeypatch.setattr(motor, "evaluar", evaluar)
    r = P.preguntar_minima(motor, consulta(intencion="evolucion", lugar="departamento de Huancavelica"))
    assert r["tipo"] == "respuesta" and r["respuesta_parcial"] and r["cifras"]
    assert r["capas"]["capa1"]["respuesta_corta"].startswith("No podemos mostrar la anemia en Huancavelica en 2025")
    assert not [x for x in r["resultados_respuesta"] if x["regla"] in parametros["respuesta"]["infracciones_corrector"]["valor"]
                and x["accion"] != "rotular"]


def test_aclaracion_no_calcula(raiz, motor, monkeypatch):
    """Huancavelica es departamento, provincia y distrito: se pregunta, con el departamento primero, y no se calcula nada."""
    def prohibido(*a, **k):
        raise AssertionError("una aclaración no calcula cifras")
    monkeypatch.setattr(motor, "cifra", prohibido)
    r = P.preguntar_minima(motor, consulta(intencion="evolucion", lugar="Huancavelica"))
    assert r["tipo"] == "aclaracion" and r["cifras"] == {} and "capas" not in r
    ops = r["aclaracion"]["opciones"]
    assert [o["n"] for o in ops] == [1, 2, 3]
    assert ops[0]["territorio"]["nivel"] == "departamento" and ops[0]["etiqueta"] == "Huancavelica (departamento)"
    assert r["texto"].splitlines()[1] == "1) Huancavelica (departamento)"


def test_consulta_incompleta_pregunta_el_tema(raiz, motor):
    """Sin tema ni indicador se pregunta el tema (opciones en orden alfabético); con `elegir` se responde."""
    c = consulta(tema=None, lugar="departamento de Puno")
    r = P.preguntar_minima(motor, c)
    assert r["tipo"] == "aclaracion" and r["aclaracion"]["motivo"] == "falta_tema" and r["cifras"] == {}
    etiquetas = [o["etiqueta"] for o in r["aclaracion"]["opciones"]]
    assert etiquetas == sorted(etiquetas, key=str.lower) and "Anemia" in etiquetas
    r2 = P.preguntar_minima(motor, c, elegir=1 + etiquetas.index("Anemia"))
    assert r2["tipo"] == "respuesta" and r2["consulta_minima"]["tema"] == "anemia"


def test_elegir_fuera_de_rango(raiz, motor):
    with pytest.raises(P.EleccionInvalida) as e:
        P.preguntar_minima(motor, consulta(lugar="Huancavelica"), elegir=9)
    assert str(e.value) == "La opción 9 no existe. Elige un número entre 1 y 3."


def test_consulta_invalida_sigue_siendo_un_error(raiz, motor):
    """Lo que no es un tema ni un tema incompleto sigue siendo una consulta inválida (mensajes de S1-01)."""
    from pap.motor.consulta import ConsultaInvalida
    with pytest.raises(ConsultaInvalida):
        P.preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "anemia"})


def test_respuesta_con_cifras_conserva_su_forma(raiz, motor):
    """Lo que ya respondía no cambia: una respuesta normal es `tipo: respuesta` y no tiene «Lo más cercano»."""
    r = P.preguntar_minima(motor, consulta())
    assert r["tipo"] == "respuesta" and r["cifras"] and "lo_mas_cercano" not in r["capas"]["capa1"]


# ------------------------------------------------------------------------- textos y reglas reutilizadas

def test_textos_y_motivos_de_la_regla(raiz, motor, parametros):
    tx = yaml.safe_load((raiz / "curados" / "motor" / "textos" / "no_se_puede.yaml").read_text(encoding="utf-8"))
    codificados = set(motor.ctx.param("R-LENGUAJE-05", "motivos_codificados"))
    assert motor.ctx.param("R-LENGUAJE-05", "max_alternativas") == 2
    reglas = {m: s["regla"] for m, s in tx["motivos"].items()}
    assert {r for r in reglas.values() if r} <= codificados                       # lo que usa de la regla, lo reutiliza tal cual
    agregados = {m for m, r in reglas.items() if r is None}
    assert {"privacidad", "distrito_creado_despues", "intencion_no_soportada", "extremo_dentro_de_no_soportado", "sin_registros"} <= agregados
    intenciones = yaml.safe_load((raiz / "curados" / "motor" / "intenciones.yaml").read_text(encoding="utf-8"))
    assert set(intenciones["motivos_no_se_puede"]) <= set(tx["motivos"])           # todo motivo del planificador tiene texto
    assert set(tx["motivos_validador"].values()) <= set(tx["motivos"])
    assert {tx["motivos"][m]["alcance"] for m in tx["motivos"]} == {"total", "parcial"}
    for m, s in tx["motivos"].items():
        if s["alcance"] == "total":
            assert s["corta"].startswith(INICIOS), m
            assert all(c.endswith(".") for c in s["cercano"].values()), m
