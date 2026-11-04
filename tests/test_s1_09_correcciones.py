"""S1-09, tarea 3 — Regresión de los hallazgos altos y bloqueantes de la auditoría estadística (A-H…) y de la revisión de usuario (H…).
Cada prueba reproduce el comando o el caso del informe (backlog/slice-1/evidencia/correcciones_s1-09.md lista hallazgo → prueba).
Si falta el cubo, las pruebas FALLAN (agents.md §8)."""
import re

import pytest
import yaml

from pap import cli
from pap.config import Rutas
from pap.motor import plantillas as PLT
from pap.motor import preguntar as PRE
from pap.motor.planificador import _comparable, anio_anterior, anio_primero
from pap.motor.respuesta import Motor
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL
from matriz.comprobar import visible

DCI = "endes_dci_menores_5"


@pytest.fixture(autouse=True)
def raiz_del_proyecto(monkeypatch):
    monkeypatch.setenv("PAP_RAIZ", str(Rutas(RAIZ_REAL).raiz))


@pytest.fixture(scope="module")
def raiz():
    r = Rutas(RAIZ_REAL).raiz
    assert (r / "biblioteca" / "indicadores" / "fact_indicador.parquet").exists(), "falta el cubo: `pap calcular`"
    return r


@pytest.fixture(scope="module")
def motor(raiz):
    return Motor(cargar_contexto(raiz))


def T(texto):
    return {"texto": texto}


def preg(motor, intencion, tema, lugar, elegir=None, periodo=None, comparar_con=None, **extra):
    c = {"intencion": intencion, "tema": tema, "territorio": T(lugar), **extra}
    if periodo:
        c["periodo"] = periodo
    if comparar_con:
        c["comparar_con"] = T(comparar_con)
    return PRE.preguntar_minima(motor, c, elegir=elegir)


def capa1(r):
    k = r["capas"]["capa1"]
    cl = k["cifra_clave"] or {}
    return " ".join([k["respuesta_corta"], cl.get("valor", ""), cl.get("texto", ""), *k["ojo_al_leer"]])


def todo(r):
    return " ".join(visible(r))


# ======================================================================= User H1 (bloqueante): comparación entre territorios

def test_h1_comparacion_con_diferencia_clara_dice_cual_es_mayor(motor):
    """Cusco 18,8 % y Puno 37,5 % (pobreza): p < 0,05 → declara la dirección, las dos cifras en la capa 1, sin «no se compara»."""
    r = preg(motor, "comparacion", "pobreza_monetaria", "departamento de Cusco", comparar_con="departamento de Puno")
    k = r["capas"]["capa1"]
    assert "mayor en Puno que en Cusco" in k["respuesta_corta"] and "estadísticamente clara" in k["respuesta_corta"]
    assert len(k["cifra_clave"]["ids"]) == 2
    cifras = k["cifra_clave"]["valor"] + " " + k["cifra_clave"]["texto"]
    assert "18,8" in cifras and "37,5" in cifras
    t = todo(r)
    assert "no se compara" not in t.lower() and "puede deberse al azar de la encuesta" not in t
    assert not any("azar" in x for x in k["ojo_al_leer"])                # el «Ojo» depende de la prueba: aquí la diferencia es clara
    assert r["capas"]["capa1"]["palabras"] <= 125


def test_h1_comparacion_sin_diferencia_clara(motor):
    """Cusco 42,8 % y Ayacucho 44,1 % (anemia, p = 0,76): «sin diferencia estadísticamente clara», sin dirección, «Ojo» sobre el azar."""
    r = preg(motor, "comparacion", "anemia", "departamento de Cusco", comparar_con="departamento de Ayacucho")
    k = r["capas"]["capa1"]
    assert "sin diferencia estadísticamente clara" in k["respuesta_corta"]
    assert not re.search(r"\b(mayor|menor|más alta|más baja)\b", todo(r))
    assert any("azar" in x for x in k["ojo_al_leer"])
    assert len(k["cifra_clave"]["ids"]) == 2 and "no se compara" not in todo(r).lower()


def test_h1_borde_tacna_moquegua_dice_mayor_en_moquegua(motor):
    """Anemia 26,0 % (Tacna) y 35,4 % (Moquegua): z = −2,10, p = 0,036 < 0,05 → «mayor en Moquegua que en Tacna»."""
    r = preg(motor, "comparacion", "anemia", "departamento de Tacna", comparar_con="departamento de Moquegua")
    k = r["capas"]["capa1"]
    assert "mayor en Moquegua que en Tacna" in k["respuesta_corta"] and "estadísticamente clara" in k["respuesta_corta"]
    assert "26,0" in k["cifra_clave"]["valor"] + k["cifra_clave"]["texto"] and "35,4" in k["cifra_clave"]["valor"] + k["cifra_clave"]["texto"]


def test_h1_sin_prueba_no_dice_mayor_ni_menor_sien_ni_gasto(motor):
    """SIEN (registro) y gasto no tienen prueba de diferencia (R-ENC-11): sin «mayor/menor» ni «estadísticamente clara»."""
    for tema, a, b in (("anemia", "Ayaviri, Melgar", "San Juan de Lurigancho"), ("gasto_publico", "Callao", "Lima Metropolitana")):
        r = preg(motor, "comparacion", tema, a, comparar_con=b)
        assert r["tipo"] == "respuesta"
        assert not re.search(r"\b(mayor|menor|más alta|más baja)\b", todo(r)), tema
        assert "estadísticamente clara" not in r["capas"]["capa1"]["respuesta_corta"]


def test_h1_comparacion_de_un_lugar_con_el_que_lo_contiene_no_declara_direccion(motor):
    """Perú contiene a Puno: la covarianza no está estimada, así que no hay prueba ni dirección (R-ENC-11)."""
    r = preg(motor, "comparacion", "anemia", "Perú", comparar_con="departamento de Puno")
    assert not re.search(r"\b(mayor|menor|más alta|más baja)\b", todo(r))
    assert "estadísticamente clara" not in r["capas"]["capa1"]["respuesta_corta"]


def test_h1_comparacion_con_una_cifra_suprimida_no_compara(motor, monkeypatch):
    """R-ENC-11: cualquiera suprimida → no comparar (la otra se muestra sola, sin dirección)."""
    evaluar = motor.evaluar

    def evaluar_falso(c):
        c = evaluar(c)
        if str(c.territorio_id) == "21":                      # Puno
            c.estado_cifra, c.semaforo_cifra = "suprimida", "no_publicable"
        return c
    monkeypatch.setattr(motor, "evaluar", evaluar_falso)
    r = preg(motor, "comparacion", "pobreza_monetaria", "departamento de Cusco", comparar_con="departamento de Puno")
    assert not re.search(r"\b(mayor|menor|más alta|más baja)\b", todo(r))
    assert "estadísticamente clara" not in r["capas"]["capa1"]["respuesta_corta"]


def test_a_h4_comparacion_la_ficha_nombra_los_dos_lugares(motor):
    r = preg(motor, "comparacion", "pobreza_monetaria", "departamento de Cusco", comparar_con="departamento de Puno")
    linea = next(x for x in r["ficha"]["corta"].splitlines() if x.startswith("Territorio:"))
    assert "Cusco" in linea and "Puno" in linea


def test_h1_preserva_comparacion_de_dos_ambitos_de_lima(motor):
    """PRESERVE: una comparación entre Lima Región y Callao (el caso de A-H4) sigue respondiendo con las dos cifras."""
    r = preg(motor, "comparacion", "anemia", "Lima Región", comparar_con="Callao")
    assert r["tipo"] == "respuesta" and len(r["cifras"]) >= 2
    linea = next(x for x in r["ficha"]["corta"].splitlines() if x.startswith("Territorio:"))
    assert "Lima Región" in linea and "Callao" in linea


# ======================================================================= User H2 + A-H5: lugar más alto con un solo departamento

def test_h2_extremo_con_un_solo_departamento_nombra_el_lugar(motor):
    r = preg(motor, "identificar_extremo", "anemia", None, territorio={"nivel": "departamento"})
    k = r["capas"]["capa1"]
    assert k["respuesta_corta"].startswith("En 2025, Puno es el departamento con la anemia")
    assert "con diferencia estadísticamente clara frente a los demás" in k["respuesta_corta"]
    assert "un departamentos" not in todo(r) and "No los ordenes" not in todo(r)
    assert k["cifra_clave"]["ids"] and "56,1" in k["cifra_clave"]["valor"]
    linea = next(x for x in r["ficha"]["corta"].splitlines() if x.startswith("Territorio:"))
    assert "departamento de Perú" not in linea and "departamentos" in linea


def test_h2_preserva_extremo_con_varios_departamentos(motor):
    """PRESERVE: con un grupo de varios departamentos (desnutrición) el texto de grupo sigue igual."""
    r = preg(motor, "identificar_extremo", "desnutricion_cronica", None, territorio={"nivel": "departamento"})
    assert "ocho departamentos" in r["capas"]["capa1"]["respuesta_corta"] or "departamentos, sin diferencias" in r["capas"]["capa1"]["respuesta_corta"]
    assert any("No los ordenes" in x for x in r["capas"]["capa1"]["ojo_al_leer"])


# ======================================================================= A-H1 (bloqueante): E-07 también como año final

def test_a_h1_un_punto_excluido_no_es_comparable_como_ano_final(motor):
    assert _comparable(motor, DCI, 2015, 2020) is False
    assert anio_anterior(motor, DCI, 2020) is None and anio_primero(motor, DCI, 2020) is None


def test_a_h1_preserva_comparar_a_traves_de_2020(motor):
    """PRESERVE (E-07): 2020 solo se excluye a sí mismo; 2021 se compara con 2019 y 2015 con 2025."""
    assert _comparable(motor, DCI, 2015, 2025) and _comparable(motor, DCI, 2019, 2021)
    assert anio_anterior(motor, DCI, 2021) == 2019 and anio_primero(motor, DCI, 2025) == 2015


@pytest.mark.parametrize("lugar,elegir,periodo", [
    ("Huancavelica", 1, {"tipo": "anio", "anio": 2020}),
    ("Perú", None, {"tipo": "anio", "anio": 2020}),
    ("Huancavelica", 1, {"tipo": "serie", "hasta": 2020}),
    ("Perú", None, {"tipo": "serie", "hasta": 2020}),
])
def test_a_h1_desnutricion_hasta_2020_no_compara_con_2020(motor, lugar, elegir, periodo):
    r = preg(motor, "evolucion", "desnutricion_cronica", lugar, elegir=elegir, periodo=periodo)
    assert r["tipo"] == "respuesta"
    t = todo(r)
    assert "pasó de" not in t and "bajó de forma" not in t and "subió de forma" not in t
    assert all("comparar_con" not in c for c in r["consulta"]["cifras"])
    assert "2020" in r["capas"]["capa1"]["respuesta_corta"] and "no se compara" in r["capas"]["capa1"]["respuesta_corta"]
    assert any("teléfono" in a for a in r["capas"]["capa2"]["avisos"])       # el aviso de R-ENC-13 llega


def test_a_h1_comparacion_bloqueada_usa_la_redaccion_sin_comparacion(motor, monkeypatch):
    """Con la comparación bloqueada por el validador, la plantilla nunca dice «pasó de X a Y»."""
    monkeypatch.setattr(PLT, "_bloqueada", lambda c: True)
    r = preg(motor, "evolucion", "desnutricion_cronica", "Huancavelica", elegir=1)
    assert "pasó de" not in todo(r)
    assert r["capas"]["capa1"]["respuesta_corta"].startswith("Esto es lo que dicen los datos oficiales sobre")


# ======================================================================= A-H2 (alto): un --desde que no se puede respetar se dice

def test_a_h2_c05_la_evolucion_del_gasto_del_peru_empieza_en_2023(motor):
    """C-05 (decisión del dueño, 3/11/2026): `comparable_con: [2023, 2024]` en el quiebre L11 de gasto_ex_pan. La serie del gasto
    del Perú ya empieza en 2023 (G-07), sin aviso de que se descartó el año; el validador decide el verbo (R-GASTO-12): no se fuerza."""
    for periodo in ({"tipo": "serie", "desde": 2023}, {"tipo": "serie"}):
        r = preg(motor, "evolucion", "gasto_publico", "Perú", periodo=periodo)
        corta = r["capas"]["capa1"]["respuesta_corta"]
        assert "Pediste" not in corta and "Empezamos en" not in corta and "no se compara con" not in corta
        t = re.sub(r"\s", " ", todo(r))                                        # los miles se separan con un espacio fino
        assert "2 179,2" in t and "2023" in t                                  # la cifra de 2023 (cubo) llega a la respuesta
        assert any(c["indicador_id"] == "gasto_ex_pan" and int(c["anio"]) == 2023 for c in r["cifras"].values())
        assert r["capas"]["capa1"]["palabras"] <= 125


def test_a_h2_c05_la_tabla_curada_declara_2023_comparable_con_2025():
    """El motor lee dim_indicador.yaml (cargar_contexto), no la copia en Parquet: 2023→2025 y 2024→2025 se comparan en gasto_ex_pan;
    el quiebre de 2023 (sin año anterior con montos) y el de 2025 de la opción C no cambian."""
    ind = yaml.safe_load((Rutas(RAIZ_REAL).raiz / "curados" / "capa0" / "dim_indicador.yaml").read_text(encoding="utf-8"))["indicadores"]
    q = {x["id"]: {int(y["anio"]): [int(c) for c in y["comparable_con"]] for y in x.get("quiebres") or []} for x in ind}
    assert q["gasto_ex_pan"][2025] == [2023, 2024] and q["gasto_ex_pan"][2023] == []
    assert q["gasto_ex_pan_opcion_c"][2025] == []


def test_a_h2_c05_comparable_en_el_planificador(motor):
    assert _comparable(motor, "gasto_ex_pan", 2023, 2025) and _comparable(motor, "gasto_ex_pan", 2024, 2025)
    assert anio_primero(motor, "gasto_ex_pan", 2025) == 2023
    assert not _comparable(motor, "gasto_ex_pan_opcion_c", 2024, 2025)         # PRESERVE: la opción C sigue sin compararse


def test_a_h2_desde_2020_de_desnutricion_dice_que_empieza_en_2021(motor):
    """El aviso de un año pedido que no se puede respetar sigue funcionando (ahora con otro caso que el gasto, por C-05)."""
    r = preg(motor, "evolucion", "desnutricion_cronica", "Perú", periodo={"tipo": "serie", "desde": 2020})
    corta = r["capas"]["capa1"]["respuesta_corta"]
    assert "2020" in corta and "Empezamos en 2021" in corta and "Pediste" in corta


def test_a_h2_preserva_serie_sin_desde_que_se_puede_respetar(motor):
    """PRESERVE: una serie con un --desde comparable (2016) no lleva el aviso y compara 2016 con 2025."""
    r = preg(motor, "evolucion", "desnutricion_cronica", "Perú", periodo={"tipo": "serie", "desde": 2016})
    assert "Pediste" not in r["capas"]["capa1"]["respuesta_corta"] and "2016" in r["capas"]["capa1"]["respuesta_corta"]


# ======================================================================= A-H3 (alto): capa 3 solo atribuye al documento si el valor coincide

def _linea(r, marca):
    return next(x for x in r["capas"]["capa3"]["para_citar"] if marca in x)


def test_a_h3_la_cita_no_atribuye_al_inei_un_valor_que_no_publica(motor):
    r = preg(motor, "evolucion", "anemia", "Perú")
    x = _linea(r, "anterior a 2024), Perú, 2015.")
    assert "Nota de prensa" not in x and "cálculo propio con ENDES 2015" in x
    assert "43,5" in x and "publicó" in x                                  # el valor que sí publicó el INEI (DOR-ANE-2015-PE)


def test_a_h3_desnutricion_2015_tampoco(motor):
    """14,3 % (nuestro valor redondeado) frente a 14,4 % del INEI: no coinciden, aunque la diferencia sea de una décima."""
    r = preg(motor, "evolucion", "desnutricion_cronica", "Perú")
    x = _linea(r, ", Perú, 2015.")
    assert "Nota de prensa" not in x and "cálculo propio" in x and "14,4" in x


def test_a_h3_preserva_la_cita_oficial_cuando_el_valor_coincide(motor):
    """PRESERVE: 43,4 % de 2025 coincide con la cifra oficial (DOR-ANE-2025-PE): se cita el documento del INEI."""
    r = preg(motor, "evolucion", "anemia", "Perú")
    x = _linea(r, "anterior a 2024), Perú, 2025.")
    assert "Fuente: INEI, Informe Preliminar" in x and "cálculo propio" not in x


# ======================================================================= User H3 (alto): comparar con un segundo lugar ambiguo

COD_ERROR = yaml.safe_load((Rutas(RAIZ_REAL).raiz / "curados" / "motor" / "parametros_motor.yaml").read_text(encoding="utf-8"))["cli"]["codigo_salida"]["valor"]["error"]


def _cli(capsys, tmp_path, *args):
    codigo = cli.main(["preguntar", "--salida", str(tmp_path), *args])
    cap = capsys.readouterr()
    return codigo, cap.out, cap.err


def test_h3_elegir_acepta_dos_numeros_para_una_comparacion(capsys, tmp_path):
    codigo, out, _ = _cli(capsys, tmp_path, "--intencion", "comparacion", "--tema", "pobreza", "--territorio", "Cusco",
                          "--comparar-con", "Puno", "--elegir", "1,1")
    assert codigo == 0 and "mayor en Puno que en Cusco" in out
    assert list(tmp_path.glob("*.md"))


def test_h3_la_instruccion_dice_como_elegir_los_dos(capsys, tmp_path):
    codigo, out, _ = _cli(capsys, tmp_path, "--intencion", "comparacion", "--tema", "pobreza", "--territorio", "Cusco",
                          "--comparar-con", "Puno", "--elegir", "1")
    assert codigo == 2 and "--elegir 1,1" in out                              # el primero ya se eligió; falta el segundo
    assert not list(tmp_path.glob("*.md"))


def test_h3_sin_coincidencia_no_manda_a_usar_elegir(capsys, tmp_path):
    codigo, out, _ = _cli(capsys, tmp_path, "--intencion", "nivel_actual", "--tema", "anemia", "--territorio", "Zzzzxq")
    assert codigo == 2 and "No encontramos ese lugar" in out and "--elegir" not in out


def test_n1_elegir_con_numeros_de_mas_en_una_comparacion_es_un_error(capsys, tmp_path):
    """N-1: `--elegir 1,1,1` con dos aclaraciones → error en español, código `cli.codigo_salida.error`, nada escrito."""
    codigo, out, err = _cli(capsys, tmp_path, "--intencion", "comparacion", "--tema", "pobreza", "--territorio", "Cusco",
                            "--comparar-con", "Puno", "--elegir", "1,1,1")
    assert codigo == COD_ERROR and out == ""
    assert err == "✘ Escribiste 3 números en --elegir, pero solo había 2 preguntas por responder. Escribe un número por cada una.\n"
    assert not list(tmp_path.iterdir())


def test_n1_elegir_con_dos_numeros_y_una_sola_aclaracion_es_un_error(capsys, tmp_path):
    codigo, out, err = _cli(capsys, tmp_path, "--intencion", "nivel_actual", "--tema", "pobreza", "--territorio", "Cusco", "--elegir", "1,2")
    assert codigo == COD_ERROR and out == ""
    assert err == "✘ Escribiste 2 números en --elegir, pero solo había 1 pregunta por responder. Escribe un solo número.\n"
    assert not list(tmp_path.iterdir())


def test_n1_elegir_sin_nada_que_elegir_es_un_error(capsys, tmp_path):
    codigo, out, err = _cli(capsys, tmp_path, "--intencion", "nivel_actual", "--tema", "pobreza", "--territorio", "Perú", "--elegir", "1")
    assert codigo == COD_ERROR and out == ""
    assert err == "✘ Esta pregunta no tiene nada por elegir: repite el comando sin --elegir.\n"
    assert not list(tmp_path.iterdir())


def test_n1_el_texto_sale_de_cli_yaml(raiz):
    m = yaml.safe_load((raiz / "curados" / "motor" / "textos" / "cli.yaml").read_text(encoding="utf-8"))["mensajes"]
    assert {"elegir_de_mas", "elegir_de_mas_una", "elegir_de_mas_ninguna"} <= set(m)


def test_n1_preserva_elegir_con_tantos_numeros_como_aclaraciones(capsys, tmp_path):
    """PRESERVE: `--elegir 1,1` con dos aclaraciones y `--elegir N` con una siguen respondiendo (código 0, archivos escritos)."""
    codigo, out, err = _cli(capsys, tmp_path, "--intencion", "comparacion", "--tema", "pobreza", "--territorio", "Cusco",
                            "--comparar-con", "Puno", "--elegir", "1,1")
    assert codigo == 0 and err == "" and list(tmp_path.glob("*.md"))


def test_h3_preserva_elegir_con_un_numero(capsys, tmp_path):
    codigo, out, _ = _cli(capsys, tmp_path, "--intencion", "nivel_actual", "--tema", "anemia", "--territorio", "Huancavelica", "--elegir", "1")
    assert codigo == 0 and "Huancavelica" in out


def test_h3_elegir_fuera_de_rango_sigue_siendo_un_error(capsys, tmp_path):
    codigo, _, err = _cli(capsys, tmp_path, "--intencion", "nivel_actual", "--tema", "anemia", "--territorio", "Huancavelica", "--elegir", "9")
    assert codigo == 1 and "La opción 9 no existe" in err


def test_h3_ayuda_y_guia_dicen_los_dos_numeros(capsys, raiz):
    with pytest.raises(SystemExit):
        cli.main(["preguntar", "--help"])
    ayuda = " ".join(capsys.readouterr().out.split())
    assert "N,N" in ayuda or "1,1" in ayuda
    assert "--elegir 1,1" in (raiz / "docs" / "guia_de_operacion.md").read_text(encoding="utf-8")


# ======================================================================= User H4 (alto): el homónimo aclarado conserva su nombre completo

def test_h4_homonimo_aclarado_se_nombra_con_provincia_y_departamento(motor):
    a = preg(motor, "nivel_actual", "anemia", "San Juan")
    n = next(o["n"] for o in a["aclaracion"]["opciones"] if o["territorio"]["departamento"] == "Cajamarca")
    r = preg(motor, "nivel_actual", "anemia", "San Juan", elegir=n)
    k = r["capas"]["capa1"]
    completo = "San Juan (Cajamarca, Cajamarca)"
    assert completo in k["respuesta_corta"] and completo in (k["cifra_clave"]["texto"] or "")
    assert any(completo in x for x in r["capas"]["capa3"]["para_citar"])
    assert k["palabras"] <= 125


def test_h4_la_ficha_nombra_el_homonimo_aclarado(motor):
    a = preg(motor, "nivel_actual", "anemia", "San Juan")
    n = next(o["n"] for o in a["aclaracion"]["opciones"] if o["territorio"]["departamento"] == "Cajamarca")
    r = preg(motor, "nivel_actual", "anemia", "San Juan", elegir=n)
    linea = next(x for x in r["ficha"]["corta"].splitlines() if x.startswith("Territorio:"))
    assert linea.startswith("Territorio: distrito de San Juan (Cajamarca, Cajamarca)")


def test_h4_preserva_el_lugar_sin_homonimo(motor):
    """PRESERVE: un lugar sin aclaración se nombra como siempre («Ayaviri», con su provincia solo en la capa 2)."""
    r = preg(motor, "nivel_actual", "anemia", "Ayaviri, Melgar")
    assert "Ayaviri (" not in r["capas"]["capa1"]["respuesta_corta"] and any(", Ayaviri, 2025." in x for x in r["capas"]["capa3"]["para_citar"])


# ======================================================================= User H5 (alto): gasto «nivel_actual» sin jerga y con su alcance

@pytest.mark.parametrize("lugar,elegir", [("Lima Metropolitana", None), ("Puno", 1), ("Perú", None)])
def test_h5_gasto_sin_jerga_en_la_capa_1(motor, lugar, elegir):
    r = preg(motor, "nivel_actual", "gasto_publico", lugar, elegir=elegir)
    k = capa1(r)
    assert not re.search(r"\bPAN\b|devengad", k)
    assert re.search(r"entidades", k)


def test_h5_gasto_de_lima_dice_que_no_incluye_a_las_entidades_nacionales(motor):
    r = preg(motor, "nivel_actual", "gasto_publico", "Lima Metropolitana")
    k = capa1(r)
    assert "con sede en Lima Metropolitana" in k and "no incluye a las entidades nacionales" in k.lower()
    assert r["capas"]["capa1"]["palabras"] <= 125
    assert any("devengado" in g["termino"] for g in r["capas"]["capa3"]["glosario"])      # la jerga queda en el glosario


def test_h5_la_frase_de_lo_que_no_incluye_no_se_repite(motor):
    r = preg(motor, "nivel_actual", "gasto_publico", "Lima Metropolitana")
    t = todo(r).lower()
    assert t.count("no incluye a las entidades nacionales con sede en lima") == 1
    assert "institutos nacionales de referencia" in t and "3,2" in t                 # la línea aparte sigue, con su cifra


# ======================================================================= User H6 (alto): sin registros no es «sin casos»

def test_h6_sin_registros_dice_que_no_es_sin_casos(motor):
    r = preg(motor, "nivel_actual", "anemia", "Putis")
    assert r["tipo"] == "no_se_puede" and r["motivo"]["codigo"] == "sin_registros"
    corta = r["capas"]["capa1"]["respuesta_corta"]
    assert "no quiere decir que no haya" in corta and corta.startswith("No tenemos registros")


# ======================================================================= User H7 + A-H7 (alto): año sin datos

def test_h7_anio_sin_datos_describe_los_anios_de_cada_forma_y_ofrece_2025(motor):
    r = preg(motor, "nivel_actual", "anemia", "Perú", periodo={"tipo": "anio", "anio": 2010})
    assert r["motivo"]["codigo"] == "anio_sin_datos"
    motivo = r["capas"]["capa2"]["mas_contexto"][0]["texto"]
    assert " de de " not in motivo
    assert "forma de medir actual" in motivo and "2024" in motivo and "2025" in motivo
    assert "2015" in motivo and "anterior" in motivo
    assert "2025" in r["capas"]["capa1"]["lo_mas_cercano"]["texto"] and r["alternativas"][0]["anio"] == 2025


def test_h7_anio_dentro_del_rango_de_la_forma_anterior_no_se_contradice(motor):
    """`--anio 2018`: la corta habla de la forma de medir actual; la anterior (2015–2025) se dice después sin contradecirla.
    E-06: «cuánto hay» no publica la cifra de 2018 de la forma anterior."""
    r = preg(motor, "nivel_actual", "anemia", "Perú", periodo={"tipo": "anio", "anio": 2018})
    assert r["tipo"] == "no_se_puede" and r["motivo"]["codigo"] == "anio_sin_datos"
    corta = r["capas"]["capa1"]["respuesta_corta"]
    # S1-15 (H7): dice que 2018 solo existe con la forma anterior y ofrece la evolución hasta 2018 (tests/test_menores_adenda.py)
    assert corta.startswith("No hay datos de anemia de 2018 con la forma de medir actual. La cifra de 2018 solo existe con la forma")
    assert not corta.startswith("No tenemos datos de anemia de 2018")
    assert "con la anterior, de 2015 a 2025" in r["capas"]["capa2"]["mas_contexto"][0]["texto"]
    assert r["cifras"] == {} and r["alternativas"][0]["tipo"] == "evolucion" and r["alternativas"][0]["anio"] == 2018


def test_h7_preserva_la_corta_de_un_tema_con_una_sola_forma_de_medir(motor):
    r = preg(motor, "nivel_actual", "pobreza_monetaria", "Perú", periodo={"tipo": "anio", "anio": 2010})
    assert r["capas"]["capa1"]["respuesta_corta"] == "No tenemos datos de pobreza de 2010."


def test_h7_sin_de_de_en_otros_temas(motor):
    r = preg(motor, "nivel_actual", "pobreza_monetaria", "Perú", periodo={"tipo": "anio", "anio": 2010})
    t = " ".join(visible(r))
    assert " de de " not in t and "2024" in t and "2025" in t
    assert r["alternativas"][0]["anio"] == 2025


def test_h7_preserva_el_anio_anterior_mas_cercano(motor):
    """PRESERVE: si el año pedido es posterior (2030), se ofrece el último disponible (2025)."""
    r = preg(motor, "nivel_actual", "pobreza_monetaria", "Perú", periodo={"tipo": "anio", "anio": 2030})
    assert r["alternativas"][0]["anio"] == 2025


# ======================================================================= medios y bajos baratos

def test_h10_la_aclaracion_de_lima_no_promete_un_defecto_que_la_cli_no_aplica(motor):
    a = preg(motor, "nivel_actual", "pobreza_monetaria", "Lima")
    assert a["tipo"] == "aclaracion" and "Si no eliges" not in a["texto"] and "usamos" not in a["texto"]


def test_h19_una_sola_frase_para_las_aclaraciones_de_homonimos(motor):
    textos = [preg(motor, "nivel_actual", "pobreza_monetaria", x)["texto"].splitlines()[0] for x in ("Lima", "Huancavelica", "San Juan", "Ayaviri")]
    assert all(re.fullmatch(r"Hay varios lugares llamados «[^»]+»\. ¿Cuál quieres\?", t) for t in textos), textos


def test_h8_serie_de_un_solo_anio_no_promete_una_cifra_de_ahora(motor):
    r = preg(motor, "evolucion", "pobreza_monetaria", "Uchuraccay")
    assert r["motivo"]["codigo"] == "serie_un_solo_anio"
    assert "cuánto hay ahora" not in r["capas"]["capa1"]["lo_mas_cercano"]["texto"]


def test_h13_extremo_dentro_de_un_lugar_nombra_el_lugar_en_la_ficha(motor):
    r = PRE.preguntar_minima(motor, {"intencion": "identificar_extremo", "tema": "pobreza_monetaria",
                                     "territorio": {"nivel": "distrito", "dentro_de": T("Puno")}}, elegir=1)
    assert r["tipo"] == "no_se_puede"
    assert "sin lugar identificado" not in r["ficha"]["corta"] and "Puno" in r["ficha"]["corta"]


def test_h16_los_no_se_puede_no_dejan_vacio_el_como_citar(motor):
    r = preg(motor, "nivel_actual", "anemia", "Putis")
    assert r["capas"]["capa3"]["para_citar"] == ["Esta respuesta no publica cifras."]


def test_a_h7_la_ficha_no_dice_pais_de_peru_ni_departamento_de_peru(motor):
    r = preg(motor, "evolucion", "pobreza_monetaria", "Perú")
    linea = next(x for x in r["ficha"]["corta"].splitlines() if x.startswith("Territorio:"))
    assert linea == "Territorio: todo el país"


def test_a_h7_mapa_no_repite_el_anio(motor):
    r = preg(motor, "nivel_actual", "pobreza_monetaria", "Ayaviri, Melgar")
    texto = r["capas"]["capa1"]["cifra_clave"]["texto"]
    assert len(re.findall(r"\b2018\b", texto)) == 1, texto


# ======================================================================= advertencia: comparar un lugar consigo mismo

def test_mismo_lugar_no_deja_un_hueco_en_la_comparacion(motor):
    r = preg(motor, "comparacion", "anemia", "departamento de Puno", comparar_con="departamento de Puno")
    assert r["tipo"] == "no_se_puede" and r["motivo"]["codigo"] == "mismo_lugar"
    t = todo(r)
    assert "No podemos comparar Puno con Puno: es el mismo lugar." == r["capas"]["capa1"]["respuesta_corta"]
    assert " en : " not in t and "y en :" not in t and "{" not in t
    assert r["cifras"] == {} and r["capas"]["capa3"]["para_citar"] == ["Esta respuesta no publica cifras."]
    assert "Territorio: Puno" in r["ficha"]["corta"] and r["capas"]["capa1"]["palabras"] <= 125


def test_mismo_lugar_por_la_cli_no_escribe_cifras_y_termina_como_un_no_se_puede(capsys, tmp_path):
    codigo, out, err = _cli(capsys, tmp_path, "--intencion", "comparacion", "--tema", "anemia", "--territorio", "departamento de Puno",
                            "--comparar-con", "departamento de Puno")
    assert err == "" and "es el mismo lugar" in out and " en : " not in out
    assert codigo == yaml.safe_load((Rutas(RAIZ_REAL).raiz / "curados" / "motor" / "parametros_motor.yaml").read_text(encoding="utf-8"))["cli"]["codigo_salida"]["valor"]["no_se_puede"]


def test_mismo_lugar_preserva_la_comparacion_de_dos_lugares_distintos(motor):
    r = preg(motor, "comparacion", "anemia", "departamento de Cusco", comparar_con="departamento de Ayacucho")
    assert r["tipo"] == "respuesta" and len(r["cifras"]) >= 2
