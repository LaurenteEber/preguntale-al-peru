"""Pieza D de las decisiones del gasto (rondas 1-2; decisión 12 del dueño, 7/10/2026): foto mensual del PIM.
DESACTIVADA el 8/10/2026 (docs/decisiones.md): la receta real se niega a registrar (test_receta_real_desactivada_*);
el resto de las pruebas usa una copia sin el bloque `desactivada` para que el código siga probado si se reactiva.
Solo datos SINTÉTICOS (aún no hay capturas mensuales de 2026): montos y códigos inventados, con la cabecera real de
Gastos_Diccionario.csv. Evidencia: 03_auditoria/ola0/decisiones_gasto/implementacion/pieza_d/."""
import csv
import shutil
from datetime import date
from decimal import Decimal

import duckdb
import pytest

from pap import capturas
from pap.capa0 import foto_pim as F
from pap.errores import PapError

from conftest import RAIZ_REAL

CABECERA = ("ANO_EJE,MES_EJE,NIVEL_GOBIERNO,NIVEL_GOBIERNO_NOMBRE,SECTOR,SECTOR_NOMBRE,PLIEGO,PLIEGO_NOMBRE,SEC_EJEC,"
            "EJECUTORA,EJECUTORA_NOMBRE,DEPARTAMENTO_EJECUTORA,DEPARTAMENTO_EJECUTORA_NOMBRE,PROVINCIA_EJECUTORA,"
            "PROVINCIA_EJECUTORA_NOMBRE,DISTRITO_EJECUTORA,DISTRITO_EJECUTORA_NOMBRE,SEC_FUNC,PROGRAMA_PPTO,"
            "PROGRAMA_PPTO_NOMBRE,TIPO_ACT_PROY,TIPO_ACT_PROY_NOMBRE,PRODUCTO_PROYECTO,PRODUCTO_PROYECTO_NOMBRE,"
            "ACTIVIDAD_ACCION_OBRA,ACTIVIDAD_ACCION_OBRA_NOMBRE,FUNCION,FUNCION_NOMBRE,DIVISION_FUNCIONAL,"
            "DIVISION_FUNCIONAL_NOMBRE,GRUPO_FUNCIONAL,GRUPO_FUNCIONAL_NOMBRE,META,FINALIDAD,META_NOMBRE,"
            "DEPARTAMENTO_META,DEPARTAMENTO_META_NOMBRE,FUENTE_FINANCIAMIENTO,FUENTE_FINANCIAMIENTO_NOMBRE,RUBRO,"
            "RUBRO_NOMBRE,TIPO_RECURSO,TIPO_RECURSO_NOMBRE,CATEGORIA_GASTO,CATEGORIA_GASTO_NOMBRE,TIPO_TRANSACCION,"
            "GENERICA,GENERICA_NOMBRE,SUBGENERICA,SUBGENERICA_NOMBRE,SUBGENERICA_DET,SUBGENERICA_DET_NOMBRE,"
            "ESPECIFICA,ESPECIFICA_NOMBRE,ESPECIFICA_DET,ESPECIFICA_DET_NOMBRE,MONTO_PIA,MONTO_PIM,MONTO_CERTIFICADO,"
            "MONTO_COMPROMETIDO_ANUAL,MONTO_COMPROMETIDO,MONTO_DEVENGADO,MONTO_GIRADO").split(",")


def fila(anio, mes, sec, meta, gen, pia, pim, dev, prog="1001", sec_func="1", esp="1", sub_det="1", rubro="00"):
    """Una fila sintética: ejecutora `sec`, departamento meta `meta`, genérica `gen`."""
    d = {c: "X" for c in CABECERA}
    d.update(ANO_EJE=str(anio), MES_EJE=str(mes), NIVEL_GOBIERNO="R", PLIEGO="999", SEC_EJEC=sec, SEC_FUNC=sec_func,
             PROGRAMA_PPTO=prog, TIPO_ACT_PROY="3", TIPO_ACT_PROY_NOMBRE="ACTIVIDAD", PRODUCTO_PROYECTO="3000001",
             ACTIVIDAD_ACCION_OBRA="5000001", FUNCION="20", FUNCION_NOMBRE="SALUD", DIVISION_FUNCIONAL="044",
             DIVISION_FUNCIONAL_NOMBRE="SALUD INDIVIDUAL", GRUPO_FUNCIONAL="0096",
             GRUPO_FUNCIONAL_NOMBRE="ATENCION MEDICA BASICA", DEPARTAMENTO_META=meta, FUENTE_FINANCIAMIENTO="1",
             RUBRO=rubro, CATEGORIA_GASTO="5", TIPO_TRANSACCION="2", GENERICA=gen, SUBGENERICA="1",
             SUBGENERICA_DET=sub_det, ESPECIFICA="1", ESPECIFICA_DET=esp, MONTO_PIA=pia, MONTO_PIM=pim,
             MONTO_DEVENGADO=dev, MONTO_CERTIFICADO="0", MONTO_COMPROMETIDO_ANUAL="0", MONTO_COMPROMETIDO="0",
             MONTO_GIRADO="0")
    return d


def escribir(ruta, filas):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, CABECERA, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(filas)
    return ruta


# Como el archivo real (auditoría H6): PIA y PIM solo en MES_EJE = 0; devengado por mes.
# Foto descargada a inicios de marzo: devengado de enero y febrero (y unos días de marzo, en cero aquí).
# Línea A con PIA; línea B nació durante el año (sin PIA); línea T es una transferencia 2.4.1.3.1.1 (R-GASTO-05).
MARZO = [fila(2026, 0, "700", "01", "3", "100.00", "120.50", "0"),
         fila(2026, 1, "700", "01", "3", "0", "0", "10.25"),
         fila(2026, 2, "700", "01", "3", "0", "0", "20.00", esp="2"),      # misma línea, otra específica detalle
         fila(2026, 0, "700", "15", "6", "0", "300.00", "0", prog="9002"),
         fila(2026, 2, "700", "15", "6", "0", "0", "5.00", prog="9002"),
         fila(2026, 0, "1235", "15", "3", "50.00", "40.00", "0"),
         fila(2026, 1, "1235", "15", "3", "0", "0", "1.00"),
         fila(2026, 0, "700", "01", "4", "0", "80.00", "0", sub_det="3"),
         fila(2026, 2, "700", "01", "4", "0", "0", "80.00", sub_det="3")]
# Foto de inicios de abril: el PIM de la línea B subió y hay devengado de marzo
ABRIL = [x for x in MARZO if not (x["PROGRAMA_PPTO"] == "9002" and x["MES_EJE"] == "0")] + [
    fila(2026, 0, "700", "15", "6", "0", "450.00", "0", prog="9002"),
    fila(2026, 3, "700", "15", "6", "0", "0", "70.00", prog="9002")]


RECETA_REAL = RAIZ_REAL / "curados" / "recetas" / "MEF-FOTO-PIM-MENSUAL.yaml"


def _sin_bloque_desactivada(texto: str) -> str:
    """La receta real está desactivada (decisión del 8/10/2026); estas pruebas comprueban que el código sigue
    funcionando si se reactiva, así que usan una copia sin el bloque `desactivada`."""
    import yaml
    d = yaml.safe_load(texto)
    d.pop("desactivada")
    return yaml.safe_dump(d, allow_unicode=True, sort_keys=False)


@pytest.fixture
def proyecto_foto(proyecto):
    (proyecto.recetas / RECETA_REAL.name).write_text(_sin_bloque_desactivada(RECETA_REAL.read_text(encoding="utf-8")),
                                                     encoding="utf-8")
    return proyecto


@pytest.fixture
def proyecto_foto_desactivada(proyecto):
    shutil.copy(RECETA_REAL, proyecto.recetas)
    return proyecto


def test_receta_real_desactivada_no_registra(proyecto_foto_desactivada, tmp_path):
    """Decisión del 8/10/2026: no se puede registrar una foto por error, ni por `pap foto-pim` ni por `pap registrar`."""
    from pap import recetas
    from pap.cli import main
    from pap.registrar import registrar
    r = proyecto_foto_desactivada
    m = escribir(tmp_path / "mar" / "2026-Gasto-Mensual.csv", MARZO)
    with pytest.raises(PapError, match="DESACTIVADA"):
        F.registrar_foto(r, m, corte="2026-03-02")
    with pytest.raises(PapError, match="DESACTIVADA"):
        registrar(r, F.SOURCE_ID, [m])
    with pytest.raises(PapError, match="DESACTIVADA"):
        recetas.cargar(r, F.SOURCE_ID)
    assert recetas.cargar(r, F.SOURCE_ID, permitir_desactivada=True)["desactivada"]["fecha"] == "2026-10-08"
    assert main(["foto-pim", "registrar", str(m), "--corte", "2026-03-02"]) == 1
    assert main(["foto-pim", "extraer"]) == 1
    assert main(["foto-pim", "listar"]) == 0
    assert m.exists() and not (r.capturas / F.SOURCE_ID).exists()
    assert not list(r.almacen.glob("sha256/*/*/*")) if r.almacen.exists() else True


def _tabla(ruta):
    return duckdb.sql(f"SELECT * FROM read_parquet('{ruta}') ORDER BY ALL").fetchall()


def test_extraer_agrega_y_conserva(tmp_path):
    csv_ = escribir(tmp_path / "a" / "2026-Gasto-Mensual.csv", MARZO)
    res = F.extraer(csv_, tmp_path / "out" / "f.parquet", "ab" * 32, consultado="2026-03-04T09:00:00-05:00")
    assert res["anio"] == 2026 and res["mes_max_devengado"] == 2
    assert (res["fecha_ref"], res["fecha_ref_base"], res["mes_ref"]) == ("2026-03-04", "fecha_consulta", 2)
    assert (res["fecha_corte"], res["fecha_corte_base"], res["mes_descarga"]) == ("2026-02", "max_fecha_en_datos", "2026-03")
    assert res["filas"] == 4 and res["filas_csv"] == 9
    assert Decimal(res["totales"]["pim"]) == Decimal("540.50")
    assert Decimal(res["totales"]["devengado_acum"]) == Decimal("116.25")
    p = tmp_path / "out" / "f.parquet"
    cols = duckdb.sql(f"DESCRIBE SELECT * FROM read_parquet('{p}')").fetchall()
    assert [c[0] for c in cols] == F.COLUMNAS
    a = duckdb.sql(f"SELECT pia, pim, devengado_acum, filas, clasificador_transferencia, funcion FROM read_parquet('{p}') "
                   "WHERE sec_ejec='700' AND departamento_meta='01' AND generica='3'").fetchall()
    assert a == [(Decimal("100.00"), Decimal("120.50"), Decimal("30.25"), 3, None, "SALUD")]
    t = duckdb.sql(f"SELECT clasificador_transferencia, pim FROM read_parquet('{p}') WHERE generica='4'").fetchall()
    assert t == [("2.4.1.3.1.1", Decimal("80.00"))]
    assert (tmp_path / "out" / "f.json").exists()


def test_mes_ref_igual_con_o_sin_corte(tmp_path):
    """H2: una descarga de los primeros días del mes da el mismo mes_ref con o sin --corte."""
    csv_ = escribir(tmp_path / "a" / "2026-Gasto-Mensual.csv", MARZO)
    d = F.extraer(csv_, tmp_path / "o1.parquet", "cd" * 32, corte="2026-03-02", consultado="2026-03-04T10:00:00-05:00")
    i = F.extraer(csv_, tmp_path / "o2.parquet", "cd" * 32, consultado="2026-03-04T10:00:00-05:00")
    assert d["mes_ref"] == i["mes_ref"] == 2
    assert (d["fecha_corte"], d["fecha_corte_base"], d["fecha_ref_base"]) == ("2026-03-02", "declarada", "declarada")
    assert duckdb.sql(f"SELECT * EXCLUDE (fecha_ref, fecha_ref_base, fecha_corte, fecha_corte_base) "
                      f"FROM read_parquet('{tmp_path}/o1.parquet') ORDER BY ALL").fetchall() == \
        duckdb.sql(f"SELECT * EXCLUDE (fecha_ref, fecha_ref_base, fecha_corte, fecha_corte_base) "
                   f"FROM read_parquet('{tmp_path}/o2.parquet') ORDER BY ALL").fetchall()


def test_mes_ref_diciembre_y_enero_no_chocan():
    assert F.mes_ref_de(date(2026, 12, 3), 2026) == 11
    assert F.mes_ref_de(date(2027, 1, 5), 2026) == 12
    assert F.mes_ref_de(date(2026, 1, 6), 2026) == 0
    assert F.mes_ref_de(date(2026, 10, 1), 2026) == 9
    with pytest.raises(PapError):
        F.mes_ref_de(date(2025, 12, 31), 2026)


def test_errores_de_forma_y_corte(tmp_path):
    csv_ = escribir(tmp_path / "a" / "2026-Gasto-Mensual.csv", MARZO)
    c = "2026-03-04T10:00:00-05:00"
    with pytest.raises(PapError, match="desactualizado"):        # corte de abril: falta devengado de marzo
        F.extraer(csv_, tmp_path / "o2.parquet", "cd" * 32, corte="2026-04-02", consultado="2026-04-03T10:00:00-05:00")
    with pytest.raises(PapError, match="posterior a la fecha de referencia"):
        F.extraer(csv_, tmp_path / "o2.parquet", "cd" * 32, corte="2026-01-31", consultado=c)
    with pytest.raises(PapError, match="posterior a la fecha de consulta"):
        F.extraer(csv_, tmp_path / "o2.parquet", "cd" * 32, corte="2026-03-09", consultado=c)
    with pytest.raises(PapError, match="AAAA-MM-DD"):
        F.extraer(csv_, tmp_path / "o3.parquet", "cd" * 32, corte="02/03/2026", consultado=c)
    with pytest.raises(PapError, match="R-GASTO-04"):
        F.anio_de_nombre("2026-Gasto-Diario.csv")
    casos = [("un solo año", [fila(2025, 1, "700", "01", "3", "0", "0", "1")]),
             ("ilegibles", [fila(2026, 1, "700", "01", "3", "0", "0", "1,5")]),
             ("fuera de 0–12", [fila(2026, 13, "700", "01", "3", "0", "0", "1")]),
             ("MES_EJE ≠ 0", [fila(2026, 2, "700", "01", "3", "0", "999", "0")])]
    for n, (msg, extra) in enumerate(casos):
        malo = escribir(tmp_path / f"m{n}" / "2026-Gasto-Mensual.csv", MARZO + extra)
        with pytest.raises(PapError, match=msg):
            F.extraer(malo, tmp_path / f"x{n}.parquet", "cd" * 32, consultado=c)
    assert not list(tmp_path.glob("x*.parquet*")) and not list(tmp_path.glob("o*.parquet*"))


def test_no_quedan_temporales(tmp_path):
    import glob
    import tempfile
    antes = set(glob.glob(tempfile.gettempdir() + "/pap_foto_pim_*"))
    csv_ = escribir(tmp_path / "a" / "2026-Gasto-Mensual.csv", MARZO)
    F.extraer(csv_, tmp_path / "o.parquet", "ef" * 32, consultado="2026-03-04T10:00:00-05:00")
    with pytest.raises(PapError):
        F.extraer(csv_, tmp_path / "p.parquet", "ef" * 32, corte="2026-01-31", consultado="2026-03-04T10:00:00-05:00")
    assert set(glob.glob(tempfile.gettempdir() + "/pap_foto_pim_*")) == antes


def test_registrar_dos_meses_sin_pisar(proyecto_foto, tmp_path):
    r = proyecto_foto
    m = escribir(tmp_path / "mar" / "2026-Gasto-Mensual.csv", MARZO)
    a = escribir(tmp_path / "abr" / "2026-Gasto-Mensual.csv", ABRIL)
    reg1, f1 = F.registrar_foto(r, m, corte="2026-03-02", consultado="2026-03-03T09:00:00-05:00")
    reg2, f2 = F.registrar_foto(r, a, corte="2026-04-01", consultado="2026-04-02T09:00:00-05:00", mover=True)
    assert not a.exists()                                                   # --mover: no queda copia
    assert reg1.captura != reg2.captura and reg1.captura.exists() and reg2.captura.exists()
    assert (f1["mes_ref"], f2["mes_ref"]) == (2, 3)
    recs = [rec for _, rec in capturas.recursos(r, F.SOURCE_ID)]
    assert [x["data_cutoff"] for x in recs] == ["2026-03-02", "2026-04-01"]
    assert {x["data_cutoff_basis"] for x in recs} == {"declarada"} and {x["name"] for x in recs} == {"foto-pim-2026"}
    assert recs[1]["previous"] == recs[0]["hash"] and recs[0]["previous"] is None
    assert recs[0]["download_url"].endswith("/2026-Gasto-Mensual.csv")
    # la receta principal del gasto no recibe nada (capa0/gasto.py no ve las fotos)
    assert capturas.recursos(r, "MEF-DA-PRESUPUESTO-EJECUCION-GASTO") == []
    # el CSV está una sola vez en el almacén; registrar otra vez el mismo archivo no crea captura
    assert len(list((r.almacen / "sha256").glob("*/*/*"))) == 2
    reg3, f3 = F.registrar_foto(r, m, corte="2026-03-02")
    assert reg3 is None and f3["parquet"] == f1["parquet"]
    assert len(list((r.capturas / F.SOURCE_ID).iterdir())) == 2
    # vistas: el PIM de la línea B sube de 300 a 450 entre fotos; R-GASTO-07 empareja dev(≤ m) con la foto m
    con = duckdb.connect()
    con.execute(F.sql_vistas(r))
    b = con.execute("SELECT mes_ref, pim, devengado_acum FROM foto_pim WHERE programa_ppto='9002' ORDER BY 1").fetchall()
    assert b == [(2, Decimal("300.00"), Decimal("5.00")), (3, Decimal("450.00"), Decimal("75.00"))]
    assert con.execute("SELECT count(DISTINCT huella_captura) FROM foto_pim_mensual").fetchone()[0] == 2
    # la foto se puede pasar por la lista curada de transferencias (mismas columnas que la base del gasto)
    assert {"generica", "clasificador_transferencia", "nivel_gobierno", "actividad_accion_obra", "pliego"} <= set(F.LLAVE)
    assert F.meses_faltantes(r, 2026, 5) == [4, 5]


def test_extraer_desde_almacen_reproduce(proyecto_foto, tmp_path):
    r = proyecto_foto
    m = escribir(tmp_path / "mar" / "2026-Gasto-Mensual.csv", MARZO)
    _, f1 = F.registrar_foto(r, m, consultado="2026-03-04T09:00:00-05:00")   # sin --corte
    assert (f1["fecha_ref_base"], f1["mes_ref"]) == ("fecha_consulta", 2)
    rec = capturas.recursos(r, F.SOURCE_ID)[0][1]
    assert (rec["data_cutoff"], rec["data_cutoff_basis"]) == ("2026-02", "max_fecha_en_datos")
    antes = _tabla(F.carpeta(r) / f1["parquet"])
    rehechas = F.extraer_pendientes(r, rehacer=True)
    assert [x["parquet"] for x in rehechas] == [f1["parquet"]]
    assert _tabla(F.carpeta(r) / f1["parquet"]) == antes
    assert not list(F.carpeta(r).glob("_tmp_*"))
    assert len(list(F.carpeta(r).glob("foto_pim_*.parquet"))) == 1


def test_receta_valida():
    from pap import recetas
    ruta = RECETA_REAL
    receta = recetas.leer(ruta)
    assert recetas.errores(receta, ruta) == []
    assert receta["desactivada"]["fecha"] == "2026-10-08"                  # decisión del dueño del 8/10/2026
    assert receta["catalogo"]["compuerta_ingesta"] == "desactivada" and receta["catalogo"]["bloquea_mvp"] is False


def test_foto_pasa_por_la_lista_de_transferencias(tmp_path):
    """H1: la foto se clasifica con la misma lista curada que la base (R-GASTO-05) y permite quitar transferencias."""
    from pap.capa0 import transferencias as tr
    csv_ = escribir(tmp_path / "a" / "2026-Gasto-Mensual.csv", MARZO)
    p = tmp_path / "f.parquet"
    F.extraer(csv_, p, "ab" * 32, consultado="2026-03-04T09:00:00-05:00")
    con = duckdb.connect()
    con.execute(f"CREATE VIEW base_cruda AS SELECT *, false AS es_transferencia FROM read_parquet('{p}')")
    tr.registrar(con, tr.cargar_lista(RAIZ_REAL / "curados" / "capa0" / "lista_transferencias.yaml"))
    cat = con.execute("SELECT categoria_transferencia, sum(pim) FROM base WHERE generica = '4' GROUP BY 1").fetchall()
    assert cat == [("intergubernamental", Decimal("80.00"))]
    assert con.execute("SELECT sum(pim) FROM base WHERE NOT es_transferencia").fetchone()[0] == Decimal("460.50")
