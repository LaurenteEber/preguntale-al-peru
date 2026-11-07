"""S3-01b punto 3 (u13), aprobado por el dueño el 6/11/2026: toda respuesta de gasto (nivel actual) abre con lo que cubre la cifra y
lo que no, y la cifra va después; el «Ojo al leer» que repetía lo mismo se quita. Cifras, semáforo y confianza no cambian.
Si falta el cubo, las pruebas FALLAN (AGENTS.md §8)."""
import pytest

from pap.config import Rutas
from pap.motor import preguntar as PRE
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL
from matriz import comprobar as C

APERTURA = "Esta cifra no es solo de anemia: es de todos los servicios de salud y nutrición infantil"
# lugar → (cierre de la apertura, id de la cifra, devengado y semáforo de la respuesta ANTES del cambio, «Ojo al leer» repetido que se quita)
CASOS = {
    "Lima Metropolitana": (", y no incluye lo que gastan las entidades nacionales con sede en Lima.",
                           "gasto_ex_pan__devengado__LIMA_METROPOLITANA__LIMA_METROPOLITANA__2025__principal", 260593096.7, "verde",
                           "No incluye a las entidades nacionales con sede en Lima, que atienden a todo el país."),
    "Ayacucho": (", y solo cuenta lo que registran las entidades con sede en Ayacucho.",
                 "gasto_ex_pan__devengado__departamento__05__2025__principal", 93375145.82, "verde",
                 "No leas esta cifra como todo el gasto en Ayacucho: solo cuenta lo que registran las entidades con sede allí."),
    "San Juan de Lurigancho": (", y solo cuenta a la municipalidad y las obras ubicadas en San Juan de Lurigancho.",
                               "gasto_ex_pan__devengado__distrito__150132__2025__principal", 3960205.2, "ambar",
                               "No es todo el gasto en el distrito: no incluye lo que gastan el Ministerio de Salud ni otras entidades."),
    "Perú": (" de todas las entidades públicas del país.",
             "gasto_ex_pan__devengado__nacional__PE__2025__principal", 2455856886.1, "verde",
             "No es el gasto de cada lugar: es la suma de lo que registran las entidades públicas."),
}


@pytest.fixture(scope="module")
def motor():
    r = Rutas(RAIZ_REAL).raiz
    assert (r / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    return Motor(cargar_contexto(r))


def _resp(motor, lugar):
    return PRE.preguntar_minima(motor, {"intencion": "nivel_actual", "tema": "gasto_publico", "territorio": {"texto": lugar},
                                        "pregunta_original": "prueba"})


@pytest.mark.parametrize("lugar", list(CASOS))
def test_la_apertura_va_primero_y_la_cifra_despues(motor, lugar):
    cierre, _, _, _, _ = CASOS[lugar]
    c1 = _resp(motor, lugar)["capas"]["capa1"]
    corta = c1["respuesta_corta"]
    assert corta.startswith(APERTURA + cierre)
    resto = corta[len(APERTURA + cierre):].strip()
    assert resto.startswith("En 2025, en ") and resto.endswith("fue:")
    assert c1["cifra_clave"]["valor"].startswith("S/")


@pytest.mark.parametrize("lugar", list(CASOS))
def test_el_ojo_repetido_se_quita_y_cifras_y_semaforo_no_cambian(motor, lugar):
    _, id_, devengado, semaforo, ojo = CASOS[lugar]
    r = _resp(motor, lugar)
    assert ojo not in r["capas"]["capa1"]["ojo_al_leer"]
    assert list(r["cifras"]) == [id_] and r["cifras"][id_]["valor"] == devengado
    assert r["semaforo_respuesta"] == semaforo
    assert r["capas"]["capa1"]["confianza"]["nivel"] == "alta" or lugar == "San Juan de Lurigancho"


@pytest.mark.parametrize("lugar", list(CASOS))
def test_capa1_dentro_del_limite_y_sin_infracciones(motor, lugar):
    r = _resp(motor, lugar)
    p = C.parametros(RAIZ_REAL)
    assert C.capa1_maximo(r, p) == []
    assert C.corrector(r, p) == []
    assert C.comparaciones(r) == []
    assert C.revisar(r, p, [lugar]) == []                       # todas las comprobaciones de la matriz, incluida R-LENGUAJE-02 y las comparaciones escritas
