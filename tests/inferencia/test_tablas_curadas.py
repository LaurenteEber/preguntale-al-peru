"""M0-06: las 6 tablas curadas de curados/inferencia/ contra su esquema, sus citas y sus cruces (sin microdatos).

Las pruebas con los Parquet de 2024 (9 959 / 19 511 / 20 290, 30 unidades, HV001 = HV021) están en
test_tablas_curadas_microdatos.py."""
import shutil
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from pap.config import Rutas
from pap.inferencia import tablas_curadas as tc

from conftest import RAIZ_REAL

CITA = "Ficha técnica ENDES 2024, §VI p. 11"
ESQUEMAS = {"diseno_muestral": tc.DisenoMuestral, "perfil_anual": tc.PerfilAnual, "relacion_entre_anios": tc.RelacionEntreAnios}


@pytest.fixture
def copia(tmp_path):
    """Copia de las tablas y de lo que cruzan, para romperlas sin tocar el repo."""
    for rel in ("curados/inferencia", "curados/capa0/dim_indicador.yaml"):
        origen, destino = RAIZ_REAL / rel, tmp_path / rel
        destino.parent.mkdir(parents=True, exist_ok=True)
        if origen.is_dir():
            shutil.copytree(origen, destino, ignore=shutil.ignore_patterns("descargas"))
        else:
            shutil.copy(origen, destino)
    return tmp_path


def _sin_lineas(errores):
    """La copia no trae los archivos de código y curados que las citas nombran: esos errores no son de lo que se prueba."""
    return [e for e in errores if not e.startswith("cita con archivo:línea")]


# ------------------------------------------------------------------ las tablas reales

def test_las_seis_tablas_validan_y_cada_fila_tiene_su_cita():
    res = tc.validar(Rutas(RAIZ_REAL))
    assert set(res) == set(tc.ARCHIVOS_TABLAS)
    for nombre, (filas, errores) in res.items():
        assert errores == [], nombre
        assert filas > 0, nombre
    for nombre, lector in tc.LECTORES.items():
        for cita in tc._citas(nombre, lector(RAIZ_REAL)):
            assert cita.strip() and tc._DONDE.search(cita), f"{nombre}: {cita[:60]}"


def test_filas_esperadas_de_2024():
    d = tc.leer_diseno_muestral(RAIZ_REAL)
    assert {(f.archivo, f.medicion) for f in d} == {
        ("RECH0", "hogar"), ("RECH23", "hogar"), ("RECH6", "hemoglobina"), ("RECH6", "talla"),
        ("REC0111", "individual_mujer"), ("CSALUD01", "salud_15_mas"), ("CSALUD08", "salud_menores_12")}
    assert all(f.encuesta == "ENDES" and f.anio == 2024 and f.peso_normalizado == "sí" for f in d)
    por = {(f.archivo, f.medicion): f for f in d}
    assert por[("RECH0", "hogar")].peso_expr == "HV005/1e6" and por[("RECH6", "hemoglobina")].peso_expr == "HV005/1e6"
    assert por[("REC0111", "individual_mujer")].peso_expr == "V005/1e6"
    assert all(f.estrato_expr == "printf('%02d-%d', HV024, HV022)" for f in d if f.archivo != "REC0111")
    assert all(f.psu_expr == "HV021" for f in d if f.archivo in ("RECH0", "RECH23", "RECH6"))
    assert {f.nivel_submuestra for f in d} == {"hogar", "individual", "medicion"}

    u = {x.id: x for x in tc.leer_universos(RAIZ_REAL)}
    assert tc.sql_predicados(u["nino_anemia_6_35m_rm363"].predicados) == \
        "HV103 IN (1) AND HC1 BETWEEN 6 AND 35 AND HC55 IN (0) AND HC57 IN (1, 2, 3, 4)"
    assert tc.sql_predicados(u["nino_dci_0_59m"].predicados) == "HV103 IN (1) AND HC1 BETWEEN 0 AND 59 AND HC70 BETWEEN -9989 AND 9989"

    t = {x.nivel: x for x in tc.leer_territorios(RAIZ_REAL)}
    assert list(t) == ["nacional", "dominio_subnacional", "departamento", "CALLAO", "LIMA_METROPOLITANA", "LIMA_REGION"]
    assert {x.como for x in t.values()} == {"dominio"}
    assert t["CALLAO"].expr == "HV024 = 7" and t["LIMA_REGION"].expr == "HV024 = 15 AND substr(UBIGEO, 1, 4) <> '1501'"

    p = tc.leer_perfil_anual(RAIZ_REAL)
    assert [(x.encuesta, x.anio, x.n_upm, x.ubigeo_minimo) for x in p] == [("ENDES", 2024, 3254, "distrito")]

    c = {x.id for x in tc.leer_cortes(RAIZ_REAL)}
    assert c == {"area", "sexo", "grupo_edad", "region_natural", "quintil_riqueza"}


def test_las_citas_con_archivo_y_linea_apuntan_a_lineas_que_existen():
    for nombre, lector in tc.LECTORES.items():
        assert tc.citas_sin_linea(RAIZ_REAL, tc._citas(nombre, lector(RAIZ_REAL))) == [], nombre


def test_cita_con_linea_inexistente_se_detecta():
    mal = tc.citas_sin_linea(RAIZ_REAL, ["curados/capa0/definiciones_endes.yaml:3000", "src/pap/no_existe.py:1"])
    assert len(mal) == 2 and "no existe" in mal[1] and "líneas" in mal[0]


def test_la_relacion_2024_2025_no_inventa_el_panel():
    """La ficha 2024 no declara qué conglomerados repite 2025 (consulta C-M0-06-1): la fila es `independiente`."""
    r = {(x.anio_a, x.anio_b): x for x in tc.leer_relacion_entre_anios(RAIZ_REAL)}
    assert r[(2023, 2024)].relacion == "conglomerados_repetidos" and r[(2023, 2024)].upm_estable_expr == "HV001"
    assert r[(2024, 2025)].relacion == "independiente" and r[(2024, 2025)].upm_estable_expr == ""


# ------------------------------------------------------------------ el esquema rechaza lo que debe

def _fila_diseno(**cambios):
    base = dict(encuesta="ENDES", anio=2024, archivo="RECH0", medicion="hogar", poblacion="hogares", peso_expr="HV005/1e6",
                estrato_expr="printf('%02d-%d', HV024, HV022)", psu_expr="HV021", upm_estable_expr="HV001", peso_normalizado="sí",
                nivel_submuestra="hogar", uniones_para_diseno="", cita=CITA)
    return {**base, **cambios}


def test_el_esquema_acepta_una_fila_bien_hecha_y_rechaza_cita_vacia_o_sin_lugar():
    assert tc.DisenoMuestral(**_fila_diseno()).llave == ("ENDES", 2024, "RECH0", "hogar")
    for mala in ("", "   ", "según la ficha técnica", "Ficha técnica ENDES 2024"):
        with pytest.raises(ValidationError, match="cita"):
            tc.DisenoMuestral(**_fila_diseno(cita=mala))
    for buena in ("Ficha técnica, p. 11", "pp. 10-11", "src/pap/capa0/encuestas.py:140", "Etiqueta del archivo RECH6 2024: «Sexo»"):
        assert tc.DisenoMuestral(**_fila_diseno(cita=buena)).cita == buena


def test_el_esquema_rechaza_expresiones_con_caracteres_peligrosos():
    for mala in ("HV005/1e6; DROP TABLE x", "HV005 -- nada", "HV005 /* x */", "read_csv('/etc/passwd')\n;"):
        with pytest.raises(ValidationError, match="expresión"):
            tc.DisenoMuestral(**_fila_diseno(peso_expr=mala))


def test_el_esquema_rechaza_campos_de_mas_y_valores_fuera_de_vocabulario():
    with pytest.raises(ValidationError):
        tc.DisenoMuestral(**_fila_diseno(otro="x"))
    with pytest.raises(ValidationError):
        tc.DisenoMuestral(**_fila_diseno(nivel_submuestra="persona"))
    with pytest.raises(ValidationError):
        tc.DisenoMuestral(**_fila_diseno(peso_normalizado="tal vez"))
    with pytest.raises(ValidationError, match="unión mal escrita"):
        tc.DisenoMuestral(**_fila_diseno(uniones_para_diseno="RECH6.HHID"))
    assert tc.DisenoMuestral(**_fila_diseno(uniones_para_diseno="RECH6.HHID=RECH0.HHID")).uniones == [("RECH6", "HHID", "RECH0", "HHID")]


def test_relacion_entre_anios_pide_la_llave_de_la_upm_estable_salvo_si_es_independiente():
    base = dict(encuesta="ENDES", anio_a=2023, anio_b=2024, cita=CITA)
    tc.RelacionEntreAnios(**base, relacion="independiente")
    with pytest.raises(ValidationError, match="UPM estable"):
        tc.RelacionEntreAnios(**base, relacion="conglomerados_repetidos")
    with pytest.raises(ValidationError, match="posterior"):
        tc.RelacionEntreAnios(**{**base, "anio_b": 2023}, relacion="independiente")
    with pytest.raises(ValidationError):
        tc.RelacionEntreAnios(**base, relacion="parecida", upm_estable_expr="HV001")


def test_universo_y_predicados_validan_su_forma():
    with pytest.raises(ValidationError, match="entre"):
        tc.Predicado(var="HC1", op="entre", valores=[35, 6])
    with pytest.raises(ValidationError, match="entre"):
        tc.Predicado(var="HC1", op="entre", valores=[1, 2, 3])
    with pytest.raises(ValidationError):
        tc.Predicado(var="HC1", op="mayor", valores=[1])
    with pytest.raises(ValidationError, match="sin valores"):
        tc.Predicado(var="HC1", op="en", valores=[])
    with pytest.raises(ValidationError, match="al menos un predicado"):
        tc.UniversoAnalitico(id="x", encuesta="ENDES", unidad="nino", aplica_a={"archivos": ["RECH6"], "mediciones": []},
                             predicados=[], anios=(2024, 2024), fuente=CITA)


def test_territorio_solo_admite_dominio():
    base = dict(nivel="CALLAO", encuesta="ENDES", anios=(2024, 2024), expr="HV024 = 7", unidad_expr="'CALLAO'", columnas=["HV024"],
                cita=CITA)
    assert tc.Territorio(**base, como="dominio").nivel == "CALLAO"
    with pytest.raises(ValidationError):
        tc.Territorio(**base, como="subpoblacion")


def test_corte_sin_categorias_ni_consulta_pendiente_no_valida():
    v = dict(archivo="RECH6", variable="HC1", unidad="nino", cita=CITA)
    with pytest.raises(ValidationError, match="sin categorías"):
        tc.CorteEstandar(id="grupo_edad", nombre="grupo de edad", por_encuesta={"ENDES": [v]}, cita=CITA)
    assert tc.CorteEstandar(id="g", nombre="g", por_encuesta={"ENDES": [{**v, "pendiente": "C-M0-06-2"}]}, cita=CITA)
    assert tc.CorteEstandar(id="g", nombre="g", por_encuesta={"ENDES": [v]}, categorias={1: "a"}, cita=CITA)


# ------------------------------------------------------------------ la validación cruzada

def test_validar_detecta_una_fila_sin_cita_en_cada_tabla_csv_y_yaml(copia):
    d = copia / "curados" / "inferencia"
    csv_p = d / "perfil_anual.csv"
    lineas = csv_p.read_text(encoding="utf-8").splitlines()
    csv_p.write_text("\n".join([lineas[0], lineas[1].rsplit(',"Ficha', 1)[0] + ','] ) + "\n", encoding="utf-8")
    y = d / "universos_analiticos.yaml"
    contenido = yaml.safe_load(y.read_text(encoding="utf-8"))
    contenido["universos"][0]["fuente"] = ""
    y.write_text(yaml.safe_dump(contenido, allow_unicode=True), encoding="utf-8")
    res = tc.validar(Rutas(copia))
    assert _sin_lineas(res["perfil_anual"][1]) and "cita" in res["perfil_anual"][1][0]
    assert _sin_lineas(res["universos_analiticos"][1]) and "cita" in res["universos_analiticos"][1][0]
    assert _sin_lineas(res["diseno_muestral"][1]) == [] and _sin_lineas(res["territorios"][1]) == []


def test_validar_detecta_llave_repetida_union_no_declarada_y_nivel_desconocido(copia):
    d = copia / "curados" / "inferencia"
    csv_p = d / "diseno_muestral.csv"
    lineas = csv_p.read_text(encoding="utf-8").splitlines()
    lineas.append(lineas[1])                                                          # llave repetida
    lineas.append(lineas[2].replace("RECH23,hogar", "RECH23,otra").replace("RECH23.HHID=RECH0.HHID", "RECH23.HHID=RECH1.HHID"))
    csv_p.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    t = d / "territorios.yaml"
    t.write_text(t.read_text(encoding="utf-8").replace("nivel: CALLAO", "nivel: CALLAO_VIEJO"), encoding="utf-8")
    res = tc.validar(Rutas(copia))
    errs = " | ".join(res["diseno_muestral"][1])
    assert "llave repetida" in errs and "no está declarada" in errs
    assert any("CALLAO_VIEJO" in e for e in res["territorios"][1])


def test_validar_detecta_un_archivo_que_no_existe_en_los_archivos_de_la_encuesta(copia):
    d = copia / "curados" / "inferencia"
    c = d / "cortes_estandar.yaml"
    c.write_text(c.read_text(encoding="utf-8").replace("archivo: RECH6\n          variable: HC27", "archivo: RECH99\n          variable: HC27"),
                 encoding="utf-8")
    res = tc.validar(Rutas(copia))
    assert any("RECH99" in e for e in res["cortes_estandar"][1])


# ------------------------------------------------------------------ ayudas

def test_fraccion_upm_repetidas_con_datos_sinteticos():
    """`conglomerados_repetidos`: la ficha declara 66,7 % de conglomerados repetidos entre años consecutivos (rotación de un tercio).
    No hay microdatos de 2025 en M0: solo se prueba con conglomerados inventados."""
    año_a = set(range(1, 10))                       # 9 conglomerados
    año_b = set(range(4, 13))                       # 9 conglomerados: 6 repetidos (4..9) y 3 nuevos (10..12)
    assert tc.fraccion_upm_repetidas(año_a, año_b) == pytest.approx(2 / 3)
    assert tc.fraccion_upm_repetidas(año_a, set()) == 0.0
    assert tc.fraccion_upm_repetidas([1, 1, 2], [2, 2, 3]) == 0.5       # lo que cuenta son los conglomerados distintos
    assert tc.fraccion_upm_repetidas([], [1, 2]) == 0.0


def test_sql_predicados_deja_pasar_los_limites_y_no_acepta_nulos():
    p = [tc.Predicado(var="HC70", op="entre", valores=[-9989, 9989]), tc.Predicado(var="HV103", op="en", valores=[1])]
    assert tc.sql_predicados(p) == "HC70 BETWEEN -9989 AND 9989 AND HV103 IN (1)"


def test_cli_registra_pap_inferencia_validar_tablas(capsys):
    from pap.cli import construir_parser, main

    a = construir_parser().parse_args(["inferencia", "validar-tablas"])
    assert a.accion == "validar-tablas" and a.fn.__name__ == "cmd_inferencia"
    with pytest.raises(SystemExit):
        construir_parser().parse_args(["inferencia", "otra-cosa"])
    assert main(["inferencia", "validar-tablas"]) == 0
    salida = capsys.readouterr().out
    for archivo in tc.ARCHIVOS_TABLAS.values():
        assert f"✔ {archivo}" in salida
    assert "✘" not in salida
