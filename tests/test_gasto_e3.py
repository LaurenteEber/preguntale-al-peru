"""E3 – gasto (decisiones del dueño del 8/10/2026, docs/decisiones.md): ejecutoras_alcance.yaml v3, obras de sede
o función nacional (obras_sede_nacional.yaml), temas ps_ (Llamkasun con su línea aparte, Jóvenes Productivos, aumento
del PCA en 2025, visto del dueño) y el nombre de 2023. Pruebas sobre los curados y sobre las tablas publicadas (no
reconstruye: el constructor lo prueba test_gasto.py, G-27, G-37 y G-38). Evidencia:
curados/generadores/e3_gasto/."""
import json
import subprocess
import sys

import duckdb
import pytest
import yaml

from pap.capa0 import gasto as G
from pap.capa0 import guardia_gasto as gu
from pap.capa0 import trazabilidad as T
from pap.config import Rutas
from pap.errores import PapError

from conftest import RAIZ_REAL

DATOS = RAIZ_REAL / "curados" / "capa0"
DIM = RAIZ_REAL / "biblioteca" / "dimensiones"
E3 = RAIZ_REAL / "curados" / "generadores" / "e3_gasto"
YAML = yaml.safe_load((DATOS / "ejecutoras_alcance.yaml").read_text(encoding="utf-8"))
POR_SEC = {e["sec_ejec"]: e for e in YAML}
SEDE = yaml.safe_load((DATOS / "obras_sede_nacional.yaml").read_text(encoding="utf-8"))


# ---------------- ejecutoras_alcance.yaml v3
def test_yaml_v3_decisiones_del_8_10():
    # P3 (9/10/2026) agrega 3 ejecutoras sin meta 15 con su bloque alcance_callao (test_gasto_lima.py)
    dec = [e for e in YAML if e["base_alcance"]["paso"] not in ("agregada_e3_sin_meta_lima", "agregada_p3_sin_meta_lima")]
    assert len(dec) == 231 and all(e["revisado_dueno"] and e["base_alcance"]["decision"] for e in dec)
    # auditoría de E3, H6: se conserva el veredicto de la ronda 1 de las 171 entradas que no tenían decisión individual
    assert sum("veredicto_ronda1" in e["base_alcance"] for e in YAML) == 171
    assert POR_SEC["1418"]["base_alcance"]["confianza"] == POR_SEC["162"]["base_alcance"]["confianza"] == "media"
    pasos = [e["base_alcance"]["paso"] for e in YAML]
    assert pasos.count("confirmado_en_bloque_8_10") == 166 and "no_evaluado_criterio_unico" not in pasos
    for s in ("17", "117", "1312"):            # INPE Sede Central, MINSA central, DIREICAJ
        e = POR_SEC[s]
        assert e["alcance"] == "nacional" and e["mixta"] and e["base_alcance"]["paso"] == "mixta", s
    for s in ("1418", "162"):                  # COAR Lima, CENFOTUR
        e = POR_SEC[s]
        assert e["alcance"] == "lima_metropolitana" and e["verificar_procedencia"] and not e["mixta"], s
        assert e["base_alcance"]["alcance_anterior"] == "nacional", s
    assert POR_SEC["18"]["alcance"] == "lima_departamento"
    assert sum(e["mixta"] for e in YAML) == 25 and len(YAML) == 254   # P3: + 3 sin meta 15 (CSJ Callao, RENIEC, ONPE)


def test_yaml_v3_ejecutoras_fuera_del_yaml():
    """Auditoría de E3, H3: las 20 ejecutoras con obras en Lima y sin meta 15 tienen alcance declarado (sin decisión)."""
    nuevas = [e for e in YAML if e["base_alcance"]["paso"] == "agregada_e3_sin_meta_lima"]
    assert len(nuevas) == 20 and not any(e["revisado_dueno"] or e["base_alcance"]["decision"] for e in nuevas)
    assert {e["sec_ejec"] for e in nuevas if e["alcance"] != "nacional"} == {"1269"}   # SUNARP Zona IX: lima_callao
    assert all(e["devengado_meta15_2023_2025_millones"] == 0 for e in nuevas)
    assert {x["sec_ejec"] for x in SEDE["obras"] if x["origen"] == "fuera_del_yaml"} <= {e["sec_ejec"] for e in nuevas}


def test_yaml_v3_reproducible(tmp_path):
    """El generador parte de la copia de la v2 y reproduce el YAML vigente byte a byte. Desde P3 (9/10/2026) los YAML
    vigentes son la salida de E3 más las adiciones del Callao: generar_p3.py corre los generadores de E3 sin cambios."""
    out = tmp_path / "y.yaml"
    subprocess.run([sys.executable, str(E3 / "generar_yaml_e3.py"), str(RAIZ_REAL), "--salida", str(out)], check=True,
                   capture_output=True)
    out2 = tmp_path / "o.yaml"
    subprocess.run([sys.executable, str(E3 / "generar_obras_sede.py"), str(RAIZ_REAL), "--salida", str(out2)],
                   check=True, capture_output=True)
    # E3 sin P3: lo mismo que el vigente quitando los bloques y entradas de P3
    vig = yaml.safe_load((DATOS / "ejecutoras_alcance.yaml").read_text(encoding="utf-8"))
    sin_p3 = [{k: v for k, v in e.items() if k != "alcance_callao"} for e in vig
              if e["base_alcance"]["paso"] != "agregada_p3_sin_meta_lima"]
    assert yaml.safe_load(out.read_text(encoding="utf-8")) == sin_p3
    o_vig = yaml.safe_load((DATOS / "obras_sede_nacional.yaml").read_text(encoding="utf-8"))
    o_e3 = yaml.safe_load(out2.read_text(encoding="utf-8"))
    assert o_e3["obras"] == [x for x in o_vig["obras"] if x["origen"] != "callao_p3"]
    p3 = RAIZ_REAL / "curados" / "generadores" / "p3_gasto" / "generar_p3.py"
    a, o = tmp_path / "a.yaml", tmp_path / "o2.yaml"
    subprocess.run([sys.executable, str(p3), str(RAIZ_REAL), "--salida-alcance", str(a), "--salida-obras", str(o)],
                   check=True, capture_output=True)
    assert a.read_bytes() == (DATOS / "ejecutoras_alcance.yaml").read_bytes()
    assert o.read_bytes() == (DATOS / "obras_sede_nacional.yaml").read_bytes()


def test_lector_acepta_lima_departamento_y_rechaza_alcance_desconocido(tmp_path):
    ok = G._alcance_ejecutoras(Rutas(RAIZ_REAL))
    assert ok.loc[ok.sec_ejec == "18", "alcance"].item() == "lima_departamento"
    malo = [dict(e) for e in YAML]
    malo[0]["alcance"] = "lima_sur"
    (tmp_path / "curados" / "capa0").mkdir(parents=True)
    (tmp_path / "curados" / "capa0" / "ejecutoras_alcance.yaml").write_text(
        yaml.safe_dump(malo, allow_unicode=True), encoding="utf-8")
    with pytest.raises(PapError, match="alcance desconocido"):
        G._alcance_ejecutoras(Rutas(tmp_path))


# ---------------- obras_sede_nacional.yaml
def test_lista_curada_de_obras_valida():
    df = G._obras_sede_nacional(DATOS / "obras_sede_nacional.yaml")
    # P3 (9/10/2026): + 12 obras del Callao (origen callao_p3; test_gasto_lima.py); aquí, las 210 del dpto 15
    assert len(df) == len(SEDE["obras"]) == 222 and SEDE["revisado_dueno"] is False
    assert SEDE["estado"].startswith("aplicada por criterio aprobado el 8/10/2026; lista revisable por el dueño")
    assert (E3 / "revision_dueno_obras_sede.csv").exists()
    o = [x for x in SEDE["obras"] if x["origen"] != "callao_p3"]
    assert len(o) == 210
    assert all(x["motivo"] and x["criterio"] in G.CRITERIOS_OBRA_SEDE for x in o)
    assert round(sum(x["devengado_2023_2025_millones"] for x in o), 1) == 1665.4
    assert {x["origen"] for x in o} == {"alcance_nacional_clase_b", "alcance_nacional_agregada", "fuera_del_yaml"}
    # no saca colegios ni hospitales que atienden a residentes (decisión del 8/10; auditoría de E3, H1): el Hospital
    # Nacional PNP se queda; las obras de los institutos especializados siguen a su ejecutora (motivo por CUI)
    import re
    for x in o:
        n = x["nombre_inversion"].upper()
        assert not re.search(r"I\.E\.|II\.EE|INSTITUCI[OÓ]N EDUCATIVA|COLEGIO|CENTRO DE ACOGIDA|CORTE SUPERIOR", n), x["cui"]
        assert "HOSPITAL" not in n, x["cui"]
        if x["sec_ejec"] in {"121", "123", "124", "126"}:
            assert x["revision"] == "revision_manual" and "sigue el alcance de su ejecutora" in x["motivo"], x["cui"]
    assert "2256359" not in {x["cui"] for x in o}


def test_lector_de_obras_rechaza_repetidos_y_criterio(tmp_path):
    base = {"version": "1.0.0", "revisado_dueno": False, "estado": "aplicada; lista revisable por el dueño"}
    p = tmp_path / "o.yaml"
    p.write_text(yaml.safe_dump({**base, "obras": [{"cui": "2412703", "sec_ejec": "1698", "criterio": "otro",
                                                    "motivo": "x"}]}), encoding="utf-8")
    with pytest.raises(PapError, match="criterio desconocido"):
        G._obras_sede_nacional(p)
    o = {"cui": "2412703", "sec_ejec": "1698", "criterio": "funcion_nacional", "motivo": "x"}
    p.write_text(yaml.safe_dump({**base, "obras": [o, o]}), encoding="utf-8")
    with pytest.raises(PapError, match="repetido"):
        G._obras_sede_nacional(p)
    p.write_text(yaml.safe_dump({"version": "1.0.0", "revisado_dueno": False, "obras": [o]}), encoding="utf-8")
    with pytest.raises(PapError, match="revisable"):
        G._obras_sede_nacional(p)


# ---------------- programas sociales (curados)
def test_programas_sociales_e3():
    d, _ = T.cargar(Rutas(RAIZ_REAL))
    ps = {p["id"]: p for p in d["ps"]["programas"]}
    assert len(ps) == 14 and d["ps"]["revisado_por"].startswith("Dueño, 8/10/2026")
    assert ps["jovenes_productivos"]["identificacion"] == {"nivel_gobierno": "E", "sec_ejec": ["993"]}
    la = ps["empleo_temporal"]["linea_aparte"]
    assert la["obligatoria"] and la["id"] == "transferido_a_municipalidades"
    assert T.etiqueta_programa_social(ps["empleo_temporal"]["nombres"], 2023, None)["etiqueta"] == \
        "Lurawi Perú (Llamkasun Perú desde agosto de 2023)"
    # la precisión por día se mantiene donde no se decidió otra cosa
    assert T.etiqueta_programa_social(ps["warmi_nan"]["nombres"], 2025, None)["etiqueta"] == "Warmi Ñan (AURORA hasta el 2/5/2025)"


def test_validar_rechaza_revisado_por_sin_visto_explicito():
    d, _ = T.cargar(Rutas(RAIZ_REAL))
    d["ps"] = {**d["ps"], "revisado_por": "revisado"}
    with pytest.raises(PapError, match="revisado_por"):
        T.validar(d)


def test_guardia_linea_aparte_sola():
    gu.verificar_consulta("SELECT anio, sum(devengado) FROM v_programa_social_linea_aparte "
                          "WHERE tema_id = 'ps_empleo_temporal' GROUP BY 1")
    for q in ("SELECT * FROM v_programa_social_linea_aparte UNION ALL SELECT * FROM gasto_tema('ps_empleo_temporal')",
              "SELECT * FROM v_programa_social_linea_aparte a, v_gasto_tematico b",
              "SELECT * FROM v_programa_social_linea_aparte a JOIN rel_programa_social_linea_aparte r USING (tema_id)"):
        with pytest.raises(gu.GuardiaGasto):
            gu.verificar_consulta(q)


# ---------------- tablas publicadas
@pytest.fixture(scope="module")
def con():
    man_p = DIM / "manifiesto_s3_gasto.json"
    if not man_p.exists():
        pytest.skip("gasto no construido")
    man = json.loads(man_p.read_text(encoding="utf-8"))
    if "obra_sede_nacional" not in man["tablas"]["fact_gasto_territorial"]["columnas"]:
        pytest.skip("la fact publicada es anterior a E3")
    c = duckdb.connect()
    c.execute("SET enable_progress_bar=false; SET memory_limit='2GB'; SET threads=2")
    c.execute(f"CREATE VIEW fact AS SELECT * FROM '{DIM / 'fact_gasto_territorial.parquet'}'")
    # P3: hasta reconstruir, la fact v1.4.0 no trae cuenta_en_ambito (las vistas la leen); en el 15 equivale a
    # cuenta_en_lima y el Callao no tenía marcas
    p3 = "cuenta_en_ambito" in man["tablas"]["fact_gasto_territorial"]["columnas"]
    c.execute("CREATE VIEW fact_gasto_territorial AS SELECT * " + ("" if p3 else ", cuenta_en_lima AS cuenta_en_ambito")
              + " FROM fact")
    for t in ("dim_tema_gasto", "rel_concepto_grupo", "rel_concepto_nodo", "rel_programa_social_ejecutora",
              "rel_programa_social_linea_aparte", "dim_programa_social"):
        c.execute(f"CREATE VIEW {t} AS SELECT * FROM '{DIM / (t + '.parquet')}'")
    c.execute((DATOS / "vistas_gasto.sql").read_text(encoding="utf-8"))
    c.execute((DATOS / "vistas_gasto_temas.sql").read_text(encoding="utf-8"))
    yield c
    c.close()


def test_pruebas_publicadas_e3(con):
    pr = {p["id"]: p for p in json.loads((DIM / "pruebas_s3_gasto.json").read_text(encoding="utf-8"))}
    for i in ("G-01", "G-26", "G-27", "G-30", "G-32", "G-37", "G-38"):
        assert pr[i]["ok"] and pr[i]["bloqueante"], i
    assert pr["G-37"]["detalle"]["gasto_final_millones"] == {"2023": 478.6, "2024": 511.3, "2025": 675.5}


def test_obras_de_sede_fuera_de_lima(con):
    r = con.execute("""SELECT round(sum(devengado) FILTER (WHERE obra_sede_nacional)/1e6, 1),
                              count(*) FILTER (WHERE obra_sede_nacional AND cuenta_en_lima),
                              count(DISTINCT (producto_proyecto, sec_ejec)) FILTER (WHERE obra_sede_nacional)
                       FROM fact WHERE departamento_atribucion = '15' AND NOT es_transferencia""").fetchone()
    assert r == (1665.4, 0, 210)
    # las obras de los centros de referencia nacional siguen en la línea aparte (no se marcan como obra de sede)
    assert con.execute("SELECT count(*) FROM fact WHERE obra_sede_nacional AND referencia_nacional").fetchone()[0] == 0


def test_cifra_de_lima_y_linea_aparte(con):
    """76 172,4 = 77 689,0 − 927,1 (obras de sede, ejecutoras del YAML; el Hospital PNP se queda, H1) − 738,3 (obras de
    sede, 20 ejecutoras fuera del YAML) + 148,8 (COAR Lima y CENFOTUR). La línea aparte no cambia (2 123,1)."""
    r = con.execute("""SELECT anio, round(sum(devengado) FILTER (WHERE cuenta_en_lima)/1e6, 1),
                              round(sum(devengado) FILTER (WHERE referencia_nacional)/1e6, 1)
                       FROM fact WHERE departamento_atribucion = '15' AND NOT es_transferencia GROUP BY 1 ORDER BY 1
                    """).fetchall()
    # P3 (fact v1.5.0): el GR Callao con meta 15 sale al 07 (−9,2 en 2025)
    p3 = "cuenta_en_ambito" in {x[0] for x in con.execute("DESCRIBE fact").fetchall()}
    assert r == ([(2023, 21741.4, 633.4), (2024, 26629.4, 711.9), (2025, 27792.3, 777.8)] if p3 else
                 [(2023, 21741.4, 633.4), (2024, 26629.4, 711.9), (2025, 27801.5, 777.8)])
    hosp = con.execute("""SELECT bool_and(cuenta_en_lima), bool_or(obra_sede_nacional) FROM fact
                          WHERE nivel_gobierno = 'E' AND sec_ejec = '1558' AND producto_proyecto = '2256359'""").fetchone()
    assert hosp == (True, False)   # Hospital Nacional PNP: se queda en Lima (H1)
    coar = con.execute("""SELECT round(sum(devengado)/1e6, 1), bool_and(cuenta_en_lima), list(DISTINCT ambito_id)
                          FROM fact WHERE nivel_gobierno = 'E' AND sec_ejec IN ('1418', '162')
                            AND nivel_atribucion = 'departamento_meta' AND departamento_meta = '15'
                            AND NOT es_transferencia""").fetchone()
    assert coar == (148.8, True, ["LIMA_METROPOLITANA"])


def test_inpe_orl_cuenta_en_lima_sin_separar(con):
    r = con.execute("""SELECT round(sum(devengado)/1e6, 1), list(DISTINCT ubigeo_atribucion), bool_and(cuenta_en_lima),
                              list(DISTINCT alcance_ejecutora)
                       FROM fact WHERE nivel_gobierno = 'E' AND sec_ejec = '18' AND departamento_meta = '15'
                         AND nivel_atribucion = 'departamento_meta' AND NOT es_transferencia""").fetchone()
    assert r == (379.4, ["150000"], True, ["lima_departamento"])


def test_llamkasun_linea_aparte_y_gasto_final(con):
    la = dict(con.execute("""SELECT anio, round(sum(devengado)/1e6, 1) FROM v_programa_social_linea_aparte
                             WHERE tema_id = 'ps_empleo_temporal' GROUP BY 1""").fetchall())
    gf = dict(con.execute("SELECT anio, round(sum(devengado)/1e6, 1) FROM gasto_tema('ps_empleo_temporal') GROUP BY 1"
                          ).fetchall())
    assert la == {2023: 605.6, 2024: 535.7, 2025: 409.0} and gf == {2023: 40.6, 2024: 34.5, 2025: 37.6}
    # el tema muestra el 6-8 % del programa (auditoría del 8/10, H6: 8,4 % en 2025)
    pct = con.execute("""
        SELECT anio, round(100 * sum(devengado) FILTER (WHERE bloque_consolidado = 'gasto_final') / sum(devengado), 1)
        FROM fact WHERE nivel_gobierno = 'E' AND sec_ejec = '1066' GROUP BY 1 ORDER BY 1""").fetchall()
    assert pct == [(2023, 6.3), (2024, 6.0), (2025, 8.4)]
    jp = dict(con.execute("SELECT anio, round(sum(devengado)/1e6, 1) FROM gasto_tema('ps_jovenes_productivos') GROUP BY 1"
                          ).fetchall())
    assert jp == {2023: 13.5, 2024: 18.0, 2025: 17.0}


def test_nombres_y_comparabilidad_ps(con):
    et = dict(con.execute("SELECT anio, etiqueta FROM dim_programa_social WHERE id_programa_social = 'empleo_temporal'"
                          ).fetchall())
    assert et[2023].startswith("Lurawi Perú (Llamkasun Perú desde agosto de 2023) (en el presupuesto del MEF")
    r = con.execute("""SELECT comparable_con_anio_anterior, motivo_quiebre FROM dim_tema_gasto
                       WHERE tema_id = 'ps_pca' AND anio = 2025""").fetchone()
    assert r[0] == "no" and "L24" in r[1] and "305,8" in r[1]
    n = con.execute("""SELECT count(DISTINCT tema_id) FROM dim_tema_gasto WHERE starts_with(tema_id, 'ps_')
                       AND starts_with(revisado_por, 'Dueño, 8/10/2026')""").fetchone()[0]
    assert n == 14
    assert con.execute("""SELECT linea_aparte_obligatoria FROM dim_programa_social
                          WHERE id_programa_social = 'empleo_temporal' AND anio = 2025""").fetchone()[0] is True
