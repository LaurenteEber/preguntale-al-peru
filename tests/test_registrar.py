import json

import duckdb
import pytest

from pap import almacen, bitacora, capturas
from pap.errores import PapError
from pap.registrar import Opciones, registrar
from pap.verificar import verificar


def test_registrar_dos_veces_no_duplica(proyecto, csv_valido):
    r1 = registrar(proyecto, "PRUEBA-CSV", [csv_valido])
    assert len(r1.nuevos) == 1 and r1.nuevos[0]["change"] == "nuevo"
    r2 = registrar(proyecto, "PRUEBA-CSV", [csv_valido])
    assert r2.nuevos == [] and r2.sin_cambio == [r1.nuevos[0]["hash"]] and r2.captura is None
    assert len(list(capturas.iterar(proyecto))) == 1
    assert len(almacen.objetos(proyecto)) == 1
    assert [v["resultado"] for v in bitacora.leer(proyecto)] == ["nuevo", "sin_cambio"]


def test_misma_fuente_misma_fecha_contenido_nuevo(proyecto, csv_valido, tmp_path):
    r1 = registrar(proyecto, "PRUEBA-CSV", [csv_valido], Opciones(consultado="2026-10-06T10:00:00-05:00"))
    v2 = tmp_path / "v2.csv"
    v2.write_text(csv_valido.read_text() + "150102;Ancón;70000\n", encoding="utf-8")
    r2 = registrar(proyecto, "PRUEBA-CSV", [v2], Opciones(consultado="2026-10-06T11:00:00-05:00"))
    rec = r2.nuevos[0]
    assert rec["change"] == "contenido" and rec["previous"] == r1.nuevos[0]["hash"]
    assert r2.captura.parent.name == "2026-10-06-2"


def test_metadatos_y_frictionless(proyecto, csv_valido):
    r = registrar(proyecto, "PRUEBA-CSV", [csv_valido], Opciones(issued="2026-01-15", version="Edición 2026"))
    paq = json.loads(r.captura.read_text(encoding="utf-8"))
    assert capturas.errores_paquete(paq) == []
    rec = paq["resources"][0]
    assert rec["hash"] == "sha256:" + __import__("hashlib").sha256(csv_valido.read_bytes()).hexdigest()
    assert rec["path"] == almacen.ruta_relativa(rec["hash"][7:])
    assert rec["encoding"] == "utf-8" and rec["mediatype"] == "text/csv"
    assert rec["source_version_basis"] == "declarada" and rec["temporal"] == "2020–2024"
    assert rec["method"] == "manual_navegador" and rec["attributed_to"] == "Prueba (manual)"
    assert rec["recipe"] == "PRUEBA-CSV@sin-git"
    assert rec["previous"] is None and "access_url" in rec


def test_contrato_detecta_faltas(proyecto, csv_valido):
    r = registrar(proyecto, "PRUEBA-CSV", [csv_valido])
    paq = json.loads(r.captura.read_text(encoding="utf-8"))
    del paq["resources"][0]["license_basis"]
    paq["resources"][0]["name"] = "Nombre Inválido"
    errs = capturas.errores_paquete(paq)
    assert any("license_basis" in e for e in errs)
    assert any(e.startswith("frictionless") for e in errs)


def test_espera_rechaza_columnas_y_forzar(proyecto, tmp_path):
    malo = tmp_path / "malo.csv"
    malo.write_text("codigo,nombre\n1,a\n", encoding="utf-8")
    with pytest.raises(PapError, match="faltan columnas"):
        registrar(proyecto, "PRUEBA-CSV", [malo])
    assert almacen.objetos(proyecto) == []
    r = registrar(proyecto, "PRUEBA-CSV", [malo], Opciones(forzar=True))
    assert r.nuevos[0]["validation"]["estado"] == "valido_con_avisos"


def test_formato_falso_rechazado(proyecto, tmp_path):
    falso = tmp_path / "x.xlsx"
    falso.write_text("no soy un excel")
    with pytest.raises(PapError, match="formato"):
        registrar(proyecto, "PRUEBA-CSV", [falso])


def test_bandeja_y_evidencia(proyecto, csv_valido, tmp_path):
    bandeja = proyecto.bandeja / "PRUEBA-CSV"
    bandeja.mkdir(parents=True)
    (bandeja / csv_valido.name).write_bytes(csv_valido.read_bytes())
    (bandeja / "a-medias.csv.crdownload").write_text("x")
    ev = tmp_path / "pagina.png"
    ev.write_bytes(b"\x89PNG....")
    r = registrar(proyecto, "PRUEBA-CSV", None, Opciones(evidencias=[ev]))
    assert len(r.nuevos) == 1
    assert r.nuevos[0]["manual_evidence"][0]["original_filename"] == "pagina.png"
    assert verificar(proyecto).ok


def test_bandeja_vacia_muestra_pasos(proyecto):
    with pytest.raises(PapError, match="Descargar de la ficha"):
        registrar(proyecto, "PRUEBA-CSV")


def test_huella_se_verifica_y_detecta_alteracion(proyecto, csv_valido):
    r = registrar(proyecto, "PRUEBA-CSV", [csv_valido])
    inf = verificar(proyecto)
    assert inf.ok and inf.recursos == 1
    obj = almacen.ruta_objeto(proyecto, r.nuevos[0]["hash"][7:])
    obj.chmod(0o644)
    datos = bytearray(obj.read_bytes())
    datos[0] ^= 1  # mismo tamaño, contenido distinto
    obj.write_bytes(bytes(datos))
    inf = verificar(proyecto)
    assert not inf.ok and any("huella" in p for p in inf.problemas)
    assert bitacora.leer(proyecto)[-1]["resultado"] == "fallo"


def test_indice_duckdb(proyecto, csv_valido):
    registrar(proyecto, "PRUEBA-CSV", [csv_valido])
    registrar(proyecto, "PRUEBA-CSV", [csv_valido])
    with duckdb.connect(str(proyecto.indice), read_only=True) as con:
        assert con.execute("select count(*) from recursos").fetchone()[0] == 1
        assert con.execute("select count(*) from verificaciones").fetchone()[0] == 2
        fila = con.execute("select source_id, recursos from fuentes_estado").fetchone()
        assert fila == ("PRUEBA-CSV", 1)


def test_xlsx_columnas_en_hoja(proyecto, tmp_path):
    import openpyxl
    from pap import validacion

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "1. Info_General"
    ws.append(["Volver al índice"])
    ws.append([])
    ws.append(["UBIGEO", "Departamento /\nProvincia", "Capital legal 1/", "Tipología de distrito \n5/"])
    p = tmp_path / "libro.xlsx"
    wb.save(p)
    ok = validacion.comprobar(p, {"formato": ["xlsx"], "hoja": "1. Info_General",
                                  "columnas": ["UBIGEO", "Capital legal", "Tipologia de distrito"]})
    assert ok["estado"] == "valido", ok
    mal = validacion.comprobar(p, {"hoja": "Otra", "columnas": ["UBIGEO"]})
    assert mal["estado"] == "invalido"


def test_mover_no_duplica_y_conserva_nombre(proyecto, csv_valido):
    contenido = csv_valido.read_bytes()
    r = registrar(proyecto, "PRUEBA-CSV", [csv_valido], Opciones(mover=True))
    rec = r.nuevos[0]
    assert not csv_valido.exists()
    obj = almacen.ruta_objeto(proyecto, rec["hash"][7:])
    assert obj.read_bytes() == contenido
    assert rec["original_filename"] == "poblacion_distrital.csv" and rec["bytes"] == len(contenido)
    assert verificar(proyecto).ok


def test_mover_se_deshace_si_falla_el_registro(proyecto, csv_valido, monkeypatch):
    """RP-06: si el registro falla después de mover, el crudo vuelve a su lugar (no queda sin captura)."""
    contenido = csv_valido.read_bytes()

    def falla(*a, **k):
        raise PapError("fallo simulado al escribir la captura")
    monkeypatch.setattr(capturas, "escribir", falla)
    with pytest.raises(PapError):
        registrar(proyecto, "PRUEBA-CSV", [csv_valido], Opciones(mover=True))
    assert csv_valido.exists() and csv_valido.read_bytes() == contenido
    assert almacen.objetos(proyecto) == []


def test_ultima_captura_orden_numerico(tmp_path):
    """RP-05: a igual fecha, la carpeta -10 es posterior a la -2."""
    from pathlib import Path
    a = capturas._orden(Path("x/2026-10-06-2/datapackage.json"), {"retrieved_at": "2026-10-06"})
    b = capturas._orden(Path("x/2026-10-06-10/datapackage.json"), {"retrieved_at": "2026-10-06"})
    c = capturas._orden(Path("x/2026-10-06/datapackage.json"), {"retrieved_at": "2026-10-06T10:00:00-05:00"})
    assert a < b and c > b
