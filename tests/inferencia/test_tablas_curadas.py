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


def test_la_relacion_2024_2025_es_conglomerados_repetidos_por_la_ficha_2025():
    """C-M0-06-1 (dueño, 12/11/2026): la ficha técnica de la ENDES 2025 (§3.1 y §IV) declara paneles los conglomerados con el mismo HV001."""
    r = {(x.anio_a, x.anio_b): x for x in tc.leer_relacion_entre_anios(RAIZ_REAL)}
    assert r[(2023, 2024)].relacion == "conglomerados_repetidos" and r[(2023, 2024)].upm_estable_expr == "HV001"
    x = r[(2024, 2025)]
    assert x.relacion == "conglomerados_repetidos" and x.upm_estable_expr == "HV001"
    for parte in ("endes-2025-ficha-tecnica", "§3.1", "§IV", "p. 4", "p. 8", "misma numeración en la variable HV001"):
        assert parte in x.cita, parte


# ------------------------------------------------------------------ valores decididos el 12/11/2026 (M1-01)

def _corte(id_):
    return {c.id: c for c in tc.leer_cortes(RAIZ_REAL)}[id_]


def test_grupo_edad_del_nino_lleva_los_tramos_del_inei_en_dos_juegos_por_receta():
    """C-M0-06-2: anemia 6–8, 9–11, 12–17, 18–23 y 24–35 meses; desnutrición crónica menores de 36 y 36–59 (Cuadros 06B, 6.1B y 04)."""
    v = {(x.archivo, x.variable): x for x in _corte("grupo_edad").por_encuesta["ENDES"]}[("RECH6", "HC1")]
    juegos = {j.id: j for j in v.juegos_de_tramos}
    assert set(juegos) == {"anemia", "desnutricion_cronica"}
    assert [(t.desde, t.hasta) for t in juegos["anemia"].tramos] == [(6, 8), (9, 11), (12, 17), (18, 23), (24, 35)]
    assert [t.rotulo for t in juegos["anemia"].tramos] == ["6 a 8 meses", "9 a 11 meses", "12 a 17 meses", "18 a 23 meses", "24 a 35 meses"]
    assert [(t.desde, t.hasta) for t in juegos["desnutricion_cronica"].tramos] == [(0, 35), (36, 59)]
    assert [t.rotulo for t in juegos["desnutricion_cronica"].tramos] == ["Menores de 36 meses", "De 36 a 59 meses"]
    assert juegos["anemia"].aplica_a_recetas == ["endes_anemia_6_35m", "endes_anemia_6_35m_oms2024"]
    assert juegos["desnutricion_cronica"].aplica_a_recetas == ["endes_dci_menores_5"]
    for parte in ("endes-2024-informe-ppr", "N.º 06B p. 55", "N.º 6.1B p. 58"):
        assert parte in juegos["anemia"].cita, parte
    for parte in ("endes-2024-informe-ppr", "N.º 04 p. 49"):
        assert parte in juegos["desnutricion_cronica"].cita, parte


def test_los_tramos_del_nino_siguen_sin_compilarse_hasta_m1_03():
    """Los valores están decididos, pero el verificador no los compila todavía (M1-03, tarea 1b): el corte sigue marcado como pendiente
    de esa historia y las recetas siguen sin permitirlo."""
    v = {(x.archivo, x.variable): x for x in _corte("grupo_edad").por_encuesta["ENDES"]}
    assert v[("RECH6", "HC1")].pendiente == "M1-03"
    assert v[("RECH1", "HV105")].pendiente == "C-M0-06-2"          # la decisión del dueño solo cubre a los niños


def test_region_natural_agrupa_costa_y_rotula_las_dos_categorias_por_separado():
    """C-M0-06-3: Costa = SHREGION 1 y 2 (verificado contra las cifras publicadas); por separado, «Lima Metropolitana y Callao» y «resto de la Costa»."""
    c = _corte("region_natural")
    assert c.categorias == {1: "Lima Metropolitana y Callao", 2: "resto de la Costa", 3: "Sierra", 4: "Selva"}
    assert c.agrupa == {"Costa": [1, 2]}
    assert "verificado contra las cifras publicadas" in c.nota and "Cuadro N.º 04 p. 49" in c.nota


def test_quintil_se_rotula_quintil_de_bienestar_y_guarda_la_duda_de_version_como_nota():
    c = _corte("quintil_riqueza")
    assert c.id == "quintil_riqueza" and c.nombre == "quintil de bienestar"
    assert "dos versiones" in c.nota and "HV270" in c.nota and "V190" in c.nota


def test_el_universo_de_disciplina_infantil_exige_a_la_mujer_en_rec0111():
    """C-M0-05-2: las 341 filas de REC93DVdisciplina sin la mujer en REC0111 quedan fuera de todo cálculo de disciplina infantil."""
    u = {x.id: x for x in tc.leer_universos(RAIZ_REAL)}["hijo_disciplina_con_madre"]
    assert (u.encuesta, u.unidad, u.anios) == ("ENDES", "hijo_de_mujer", (2024, 2024))
    assert [(e.archivo, e.por) for e in u.exige_pareja] == [("REC0111", [("CASEID", "CASEID")])]
    assert "341" in u.fuente and "C-M0-05-2" in u.fuente


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


def _juego(**kw):
    base = dict(id="j", aplica_a_recetas=["r"], tramos=[dict(rotulo="a", desde=0, hasta=5), dict(rotulo="b", desde=6, hasta=9)], cita=CITA)
    return {**base, **kw}


def test_tramos_que_se_traslapan_o_estan_al_reves_no_validan():
    v = dict(archivo="RECH6", variable="HC1", unidad="nino", cita=CITA)
    assert tc.VariableCorte(**v, juegos_de_tramos=[_juego()]).juegos_de_tramos[0].tramos[1].desde == 6
    for tramos, msg in (([dict(rotulo="a", desde=0, hasta=6), dict(rotulo="b", desde=6, hasta=9)], "se traslapan"),
                        ([dict(rotulo="a", desde=5, hasta=2)], "desde no puede pasar de hasta"),
                        ([dict(rotulo="b", desde=6, hasta=9), dict(rotulo="a", desde=0, hasta=5)], "en orden"),
                        ([dict(rotulo="", desde=0, hasta=5)], "rótulo")):
        with pytest.raises(ValidationError, match=msg):
            tc.VariableCorte(**v, juegos_de_tramos=[_juego(tramos=tramos)])
    with pytest.raises(ValidationError, match="al menos una receta"):
        tc.VariableCorte(**v, juegos_de_tramos=[_juego(aplica_a_recetas=[])])
    with pytest.raises(ValidationError, match="se repite"):
        tc.VariableCorte(**v, juegos_de_tramos=[_juego(), _juego()])


def test_una_receta_no_puede_tener_dos_juegos_de_tramos():
    v = dict(archivo="RECH6", variable="HC1", unidad="nino", cita=CITA)
    with pytest.raises(ValidationError, match="más de un juego"):
        tc.VariableCorte(**v, juegos_de_tramos=[_juego(id="a"), _juego(id="b")])


def test_agrupa_solo_junta_codigos_que_existen_y_no_repite_ninguno():
    v = dict(archivo="RECH23", variable="SHREGION", unidad="hogar", cita=CITA)
    base = dict(id="r", nombre="r", por_encuesta={"ENDES": [v]}, categorias={1: "a", 2: "b", 3: "c"}, cita=CITA)
    assert tc.CorteEstandar(**base, agrupa={"X": [1, 2]}).agrupa == {"X": [1, 2]}
    with pytest.raises(ValidationError, match="código 9"):
        tc.CorteEstandar(**base, agrupa={"X": [1, 9]})
    with pytest.raises(ValidationError, match="más de un grupo"):
        tc.CorteEstandar(**base, agrupa={"X": [1, 2], "Y": [2, 3]})
    with pytest.raises(ValidationError, match="al menos dos códigos"):
        tc.CorteEstandar(**base, agrupa={"X": [1]})


def test_un_universo_sin_predicados_ni_pareja_exigida_no_valida_y_la_pareja_debe_existir(copia):
    base = dict(id="u", encuesta="ENDES", unidad="hijo_de_mujer", aplica_a=dict(archivos=["REC93DVdisciplina"], mediciones=["m"]),
                anios=(2024, 2024), fuente=CITA)
    with pytest.raises(ValidationError, match="al menos un predicado"):
        tc.UniversoAnalitico(**base, predicados=[])
    u = tc.UniversoAnalitico(**base, predicados=[], exige_pareja=[dict(archivo="REC0111", por=[("CASEID", "CASEID")])])
    assert u.exige_pareja[0].archivo == "REC0111"
    y = copia / "curados" / "inferencia" / "universos_analiticos.yaml"
    y.write_text(y.read_text(encoding="utf-8").replace("archivo: REC0111\n        por:", "archivo: REC9999\n        por:"), encoding="utf-8")
    assert any("REC9999" in e for e in tc.validar(Rutas(copia))["universos_analiticos"][1])


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


@pytest.mark.parametrize("var", ["hc1", "1HC", "HC 1", 'HC1"', "HC1;", "", "_HC1"])
def test_predicado_var_solo_acepta_nombres_de_variable(var):
    """H06-2: `Predicado.var` es un nombre en mayúsculas (^[A-Z][A-Z0-9_]*$), nunca texto libre."""
    with pytest.raises(ValidationError):
        tc.Predicado(var=var, op="en", valores=[1])


@pytest.mark.parametrize("expr", ["(SELECT 1)", "select HV024", "HV024 FROM x", "HV024 from RECH0", "HV024 Select"])
def test_expr_rechaza_select_y_from_como_palabras(expr):
    """H06-2: una expresión curada no abre subconsultas."""
    with pytest.raises(ValueError):
        tc._expr(expr)


def test_expr_admite_nombres_que_solo_contienen_esas_palabras():
    assert tc._expr("HV005/1e6") == "HV005/1e6"
    assert tc._expr("FROMAGE + SELECTOR") == "FROMAGE + SELECTOR"
