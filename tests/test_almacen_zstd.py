"""E4 (8/10/2026): crudos guardados como <huella>.zst con la huella SHA-256 del ORIGINAL."""
import errno
import json
import os

import duckdb
import pandas as pd
import pytest
import zstandard

from pap import almacen, capturas, cli
from pap.capa0 import insumos
from pap.registrar import Opciones, registrar
from pap.util import sha256
from pap.verificar import verificar

LECTOR_GASTO = "read_csv(?, header=true, all_varchar=true, quote='\"', escape='\"', delim=',', strict_mode=true)"


@pytest.fixture
def csv_grande(tmp_path):
    """CSV sintético con coma, comillas y UTF-8 (como los del MEF), de ~60 KB."""
    p = tmp_path / "entrada" / "2099-Gasto.csv"
    p.parent.mkdir(exist_ok=True)
    filas = ['ubigeo,distrito,poblacion']
    filas += [f'{150101 + i:06d},"Distrito ñ, {i}",{1000 + i}' for i in range(3000)]
    p.write_text("\n".join(filas) + "\n", encoding="utf-8")
    return p


def _registrar(proyecto, archivo, **kw):
    r = registrar(proyecto, "PRUEBA-CSV", [archivo], Opciones(**kw))
    return r.nuevos[0], r.nuevos[0]["hash"][7:]


def _receta_coma(proyecto):
    ruta = proyecto.recetas / "PRUEBA-CSV.yaml"
    ruta.write_text(ruta.read_text(encoding="utf-8").replace("bytes: [10, 1000000]", "bytes: [10, 10000000]"),
                    encoding="utf-8")


def test_registrar_grande_guarda_zst_con_huella_del_original(proyecto, csv_grande, monkeypatch):
    _receta_coma(proyecto)
    monkeypatch.setenv("PAP_COMPRIMIR_MIN_MB", "0.01")
    original = csv_grande.read_bytes()
    rec, h = _registrar(proyecto, csv_grande)
    assert h == sha256(csv_grande) and csv_grande.exists()             # sin --mover el original del usuario queda
    obj = almacen.ruta_objeto(proyecto, h)
    assert obj.name == f"{h}.zst" and not (proyecto.cruda / rec["path"]).exists()
    assert zstandard.ZstdDecompressor().decompress(obj.read_bytes()) == original
    # el datapackage describe el ORIGINAL; la forma de guardado va en pap_storage
    assert rec["path"] == almacen.ruta_relativa(h) and rec["bytes"] == len(original)
    assert rec["pap_storage"] == {"compression": "zstd", "path": rec["path"] + ".zst", "bytes": obj.stat().st_size}
    paq = capturas.leer_json(next(proyecto.capturas.glob("*/*/datapackage.json")))
    assert capturas.errores_paquete(paq) == []
    for completo in (True, False):
        inf = verificar(proyecto, completo=completo, anotar=False)
        assert inf.ok and not inf.avisos, (inf.problemas, inf.avisos)
    assert almacen.objetos(proyecto) == [h]
    # registrar otra vez no duplica
    r2 = registrar(proyecto, "PRUEBA-CSV", [csv_grande])
    assert r2.sin_cambio and almacen.objetos(proyecto) == [h]


def test_pequeno_o_desactivado_no_se_comprime(proyecto, csv_grande, monkeypatch):
    _receta_coma(proyecto)
    monkeypatch.setenv("PAP_COMPRIMIR_MIN_MB", "no")
    rec, h = _registrar(proyecto, csv_grande)
    assert not almacen.comprimido(proyecto, h) and "pap_storage" not in rec
    assert almacen.debe_comprimirse("csv", 11_000_000, 10_000_000)
    assert not almacen.debe_comprimirse("zip", 11_000_000, 10_000_000)      # ya comprimidos: no
    assert not almacen.debe_comprimirse("csv", 9_000_000, 10_000_000)


def test_lectores_leen_el_zst_igual_que_el_original(proyecto, csv_grande, monkeypatch, tmp_path):
    _receta_coma(proyecto)
    monkeypatch.setenv("PAP_COMPRIMIR_MIN_MB", "0.01")
    rec, h = _registrar(proyecto, csv_grande)
    ruta = almacen.resolver(proyecto, rec["path"])
    assert ruta.suffix == ".zst"
    ins = insumos.ultimo(proyecto, "PRUEBA-CSV")
    assert ins.ruta == ruta and ins.hash == rec["hash"]
    con = duckdb.connect()
    sql = f"SELECT * FROM {LECTOR_GASTO} ORDER BY ubigeo"
    assert con.execute(sql, [str(ruta)]).fetchall() == con.execute(sql, [str(csv_grande)]).fetchall()
    pd.testing.assert_frame_equal(pd.read_csv(ruta, dtype=str), pd.read_csv(csv_grande, dtype=str))


def test_comprimir_objeto_existente_y_es_idempotente(proyecto, csv_grande):
    _receta_coma(proyecto)
    rec, h = _registrar(proyecto, csv_grande)                       # umbral por defecto (10 MB): sin comprimir
    plano = proyecto.cruda / rec["path"]
    assert plano.exists()
    p = almacen.comprimir_objeto(proyecto, h, rec["bytes"], ensayo=True)
    assert p.accion == "ensayo" and plano.exists() and not almacen.comprimido(proyecto, h)
    p = almacen.comprimir_objeto(proyecto, h, rec["bytes"])
    assert p.accion == "comprimido" and not plano.exists() and almacen.comprimido(proyecto, h)
    assert almacen.huella_y_tamano(almacen.ruta_objeto(proyecto, h)) == (h, rec["bytes"])
    assert almacen.comprimir_objeto(proyecto, h, rec["bytes"]).accion == "ya_comprimido"
    assert verificar(proyecto, anotar=False).ok
    assert not almacen.temporales(proyecto)


def test_falla_de_verificacion_deja_el_original_intacto(proyecto, csv_grande, monkeypatch):
    _receta_coma(proyecto)
    rec, h = _registrar(proyecto, csv_grande)
    plano = proyecto.cruda / rec["path"]
    antes = plano.read_bytes()

    def comprimir_mal(origen, destino, nivel=9, hilos=4):          # escribe un .zst válido pero de otro contenido
        destino.write_bytes(zstandard.ZstdCompressor().compress(antes[:-5] + b"XXXXX"))
        return destino.stat().st_size

    monkeypatch.setattr(almacen, "comprimir_archivo", comprimir_mal)
    p = almacen.comprimir_objeto(proyecto, h, rec["bytes"])
    assert p.accion == "error" and "original quedó intacto" in p.detalle
    assert plano.read_bytes() == antes and not almacen.comprimido(proyecto, h)
    assert not almacen.temporales(proyecto) and not almacen._zst(proyecto, h).exists()
    # por la CLI: código de salida 1 y el original sigue ahí
    assert cli.main(["almacen", "comprimir", "--min-mb", "0"]) == 1
    assert plano.read_bytes() == antes


def test_original_alterado_no_se_comprime(proyecto, csv_grande):
    _receta_coma(proyecto)
    rec, h = _registrar(proyecto, csv_grande)
    plano = proyecto.cruda / rec["path"]
    os.chmod(plano, 0o644)
    datos = bytearray(plano.read_bytes())
    datos[100] ^= 1
    plano.write_bytes(bytes(datos))
    p = almacen.comprimir_objeto(proyecto, h, rec["bytes"])
    assert p.accion == "error" and plano.read_bytes() == bytes(datos) and not almacen._zst(proyecto, h).exists()


def test_reanuda_tras_un_corte(proyecto, csv_grande):
    _receta_coma(proyecto)
    rec, h = _registrar(proyecto, csv_grande)
    plano, z = proyecto.cruda / rec["path"], almacen._zst(proyecto, h)
    # corte 1: quedó un .tmp a medias → se descarta y se rehace
    tmp = z.with_name(z.name + ".tmp")
    tmp.write_bytes(b"basura a medias")
    assert verificar(proyecto, anotar=False).avisos                   # verificar avisa del temporal
    # corte 2: el .zst ya se renombró pero el original no se retiró → se verifica y se retira
    almacen.comprimir_archivo(plano, z)
    assert almacen.duplicados(proyecto) == [h]
    inf = verificar(proyecto, anotar=False)
    assert inf.ok and any("original y .zst" in a for a in inf.avisos)
    p = almacen.comprimir_objeto(proyecto, h, rec["bytes"])
    assert p.accion == "comprimido" and not plano.exists() and not tmp.exists()
    assert verificar(proyecto, anotar=False).ok


def test_zst_a_medias_corrupto_no_retira_el_original(proyecto, csv_grande):
    _receta_coma(proyecto)
    rec, h = _registrar(proyecto, csv_grande)
    plano, z = proyecto.cruda / rec["path"], almacen._zst(proyecto, h)
    z.write_bytes(zstandard.ZstdCompressor().compress(b"otro contenido"))
    p = almacen.comprimir_objeto(proyecto, h, rec["bytes"])
    assert p.accion == "error" and plano.exists() and z.exists()


def test_verificar_detecta_zst_alterado(proyecto, csv_grande, monkeypatch):
    _receta_coma(proyecto)
    monkeypatch.setenv("PAP_COMPRIMIR_MIN_MB", "0.01")
    rec, h = _registrar(proyecto, csv_grande)
    z = almacen.ruta_objeto(proyecto, h)
    os.chmod(z, 0o644)
    otro = zstandard.ZstdCompressor(write_content_size=True).compress(csv_grande.read_bytes().replace(b"1000", b"1001", 1))
    z.write_bytes(otro)
    inf = verificar(proyecto, anotar=False)
    assert not inf.ok and any("huella" in p for p in inf.problemas)
    # --rapido: el .zst nuevo mide distinto de lo anotado en almacen_zst.json → lo ve
    assert any("anotado" in p for p in verificar(proyecto, completo=False, anotar=False).problemas)
    z.write_bytes(zstandard.ZstdCompressor(write_content_size=True).compress(b"corto"))
    assert not verificar(proyecto, completo=False, anotar=False).ok  # --rapido sí ve el tamaño original distinto


def test_mover_comprimiendo_y_deshacer(proyecto, csv_grande, monkeypatch):
    _receta_coma(proyecto)
    h = sha256(csv_grande)
    original = csv_grande.read_bytes()
    destino, nuevo = almacen.mover(proyecto, csv_grande, h, comprimir=True)
    assert nuevo and destino.name.endswith(".zst") and not csv_grande.exists()
    almacen.devolver(proyecto, h, csv_grande)
    assert csv_grande.read_bytes() == original and not almacen.existe(proyecto, h)
    # registrar --mover que falla después de mover devuelve el archivo (RP-06), también comprimido
    monkeypatch.setenv("PAP_COMPRIMIR_MIN_MB", "0.01")

    def falla(*a, **k):
        raise RuntimeError("falla simulada")
    monkeypatch.setattr(capturas, "escribir", falla)
    with pytest.raises(RuntimeError):
        registrar(proyecto, "PRUEBA-CSV", [csv_grande], Opciones(mover=True))
    assert csv_grande.read_bytes() == original and almacen.objetos(proyecto) == []


def test_contrato_pap_storage(proyecto, csv_grande, monkeypatch):
    _receta_coma(proyecto)
    monkeypatch.setenv("PAP_COMPRIMIR_MIN_MB", "0.01")
    registrar(proyecto, "PRUEBA-CSV", [csv_grande])
    ruta = next(proyecto.capturas.glob("*/*/datapackage.json"))
    from pap.util import leer_json
    paq = leer_json(ruta)
    assert capturas.errores_paquete(paq) == []
    paq["resources"][0]["pap_storage"]["path"] = paq["resources"][0]["path"]
    assert any("pap_storage.path" in e for e in capturas.errores_paquete(paq))


def test_cli_dry_run_no_cambia_nada(proyecto, csv_grande, capsys):
    _receta_coma(proyecto)
    rec, h = _registrar(proyecto, csv_grande)
    assert cli.main(["almacen", "comprimir", "--min-mb", "0", "--dry-run"]) == 0
    assert "ensayo" in capsys.readouterr().out and not almacen.comprimido(proyecto, h)
    assert cli.main(["almacen", "comprimir", "--min-mb", "0"]) == 0 and almacen.comprimido(proyecto, h)
    assert cli.main(["almacen", "comprimir", "--min-mb", "0"]) == 0          # idempotente
    assert "ya_comprimido" in capsys.readouterr().out


# ------------------------------------------------------------------ correcciones tras la auditoría (H2, H4, H5, fsync)

def _objeto_plano(proyecto, csv_grande):
    _receta_coma(proyecto)
    rec, h = _registrar(proyecto, csv_grande)
    return rec, h, proyecto.cruda / rec["path"]


def test_rapido_detecta_zst_truncado(proyecto, csv_grande):
    rec, h, _ = _objeto_plano(proyecto, csv_grande)
    assert almacen.comprimir_objeto(proyecto, h, rec["bytes"]).accion == "comprimido"
    assert verificar(proyecto, completo=False, anotar=False).ok
    z = almacen.ruta_objeto(proyecto, h)
    os.chmod(z, 0o644)
    z.write_bytes(z.read_bytes()[: z.stat().st_size // 2])            # la cabecera (tamaño original) sobrevive
    rapido = verificar(proyecto, completo=False, anotar=False)
    assert not rapido.ok and any("truncado" in p for p in rapido.problemas)
    assert not verificar(proyecto, anotar=False).ok


def test_registro_trazable_de_la_compresion(proyecto, csv_grande):
    rec, h, _ = _objeto_plano(proyecto, csv_grande)
    assert cli.main(["almacen", "comprimir", "--min-mb", "0"]) == 0
    reg = json.loads(almacen.ruta_registro(proyecto).read_text(encoding="utf-8"))["objetos"][h]
    z = almacen.ruta_objeto(proyecto, h)
    assert reg["bytes"] == rec["bytes"] and reg["bytes_zst"] == z.stat().st_size and reg["sha256_zst"] == sha256(z)
    lineas = [json.loads(x) for x in proyecto.verificaciones.read_text(encoding="utf-8").splitlines()]
    comp = [x for x in lineas if x["accion"] == "comprimir"]
    assert len(comp) == 1 and comp[0]["resultado"] == "ok" and comp[0]["hash"] == f"sha256:{h}"
    assert comp[0]["source_id"] == "PRUEBA-CSV" and "original retirado" in comp[0]["detalle"]
    assert cli.main(["almacen", "comprimir", "--min-mb", "0"]) == 0          # idempotente: no agrega líneas
    assert len(proyecto.verificaciones.read_text(encoding="utf-8").splitlines()) == len(lineas)


def test_registrar_comprimido_anota(proyecto, csv_grande, monkeypatch):
    _receta_coma(proyecto)
    monkeypatch.setenv("PAP_COMPRIMIR_MIN_MB", "0.01")
    rec, h = _registrar(proyecto, csv_grande)
    assert almacen.leer_registro(proyecto)[h]["bytes_zst"] == rec["pap_storage"]["bytes"]
    assert any(json.loads(x)["accion"] == "comprimir" for x in proyecto.verificaciones.read_text().splitlines())
    assert verificar(proyecto, completo=False, anotar=False).ok


def test_zst_sin_anotar_se_verifica_y_anota(proyecto, csv_grande):
    rec, h, plano = _objeto_plano(proyecto, csv_grande)
    almacen.comprimir_archivo(plano, almacen._zst(proyecto, h))      # .zst hecho a mano, sin registro
    plano.unlink()
    assert any("sin anotar" in p for p in verificar(proyecto, completo=False, anotar=False).problemas)
    p = almacen.comprimir_objeto(proyecto, h, rec["bytes"])
    assert p.accion == "anotado" and verificar(proyecto, completo=False, anotar=False).ok


def test_disco_lleno_error_claro_sin_traceback(proyecto, csv_grande, monkeypatch, capsys):
    rec, h, plano = _objeto_plano(proyecto, csv_grande)
    antes = plano.read_bytes()

    def lleno(origen, destino, *a, **k):
        destino.write_bytes(b"\x28\xb5\x2f\xfd" + b"\0" * 50)
        raise OSError(errno.ENOSPC, "No space left on device")
    monkeypatch.setattr(almacen, "comprimir_archivo", lleno)
    assert cli.main(["almacen", "comprimir", "--min-mb", "0"]) == 1         # sin excepción
    salida = capsys.readouterr().out
    assert "disco lleno" in salida and "Traceback" not in salida
    assert plano.read_bytes() == antes and not almacen._zst(proyecto, h).exists() and not almacen.temporales(proyecto)
    linea = json.loads(proyecto.verificaciones.read_text(encoding="utf-8").splitlines()[-1])
    assert (linea["accion"], linea["resultado"]) == ("comprimir", "error")
    # registrar con el disco lleno: PapError (mensaje claro) y el archivo del usuario intacto
    with pytest.raises(Exception) as e:
        almacen.guardar(proyecto, csv_grande, "0" * 64, comprimir=True)
    assert "disco lleno" in str(e.value)


def test_falla_al_retirar_el_original(proyecto, csv_grande):
    rec, h, plano = _objeto_plano(proyecto, csv_grande)

    def no_puedo(p):
        raise PermissionError(errno.EPERM, "Operation not permitted")
    p = almacen.comprimir_objeto(proyecto, h, rec["bytes"], borrar=no_puedo)
    assert p.accion == "error" and "no se pudo retirar" in p.detalle and plano.exists()
    assert almacen.comprimir_objeto(proyecto, h, rec["bytes"]).accion == "comprimido"


def test_recupera_si_solo_queda_el_tmp(proyecto, csv_grande):
    """Corte de energía tras renombrar sin que el renombrado llegue al disco: solo queda <huella>.zst.tmp."""
    rec, h, plano = _objeto_plano(proyecto, csv_grande)
    z = almacen._zst(proyecto, h)
    tmp = z.with_name(z.name + ".tmp")
    almacen.comprimir_archivo(plano, tmp)
    plano.unlink()
    assert almacen.candidatos(proyecto, 0)[0][0] == h
    p = almacen.comprimir_objeto(proyecto, h, rec["bytes"])
    assert p.accion == "recuperado" and z.exists() and not tmp.exists()
    assert verificar(proyecto, anotar=False).ok and verificar(proyecto, completo=False, anotar=False).ok


def test_tmp_unico_corrupto_no_se_toca(proyecto, csv_grande):
    rec, h, plano = _objeto_plano(proyecto, csv_grande)
    z = almacen._zst(proyecto, h)
    tmp = z.with_name(z.name + ".tmp")
    tmp.write_bytes(zstandard.ZstdCompressor().compress(b"otra cosa"))
    plano.unlink()
    p = almacen.comprimir_objeto(proyecto, h, rec["bytes"])
    assert p.accion == "error" and tmp.exists() and not z.exists()


def test_fsync_de_la_carpeta_tras_renombrar(proyecto, csv_grande, monkeypatch):
    rec, h, _ = _objeto_plano(proyecto, csv_grande)
    llamadas = []
    monkeypatch.setattr(almacen, "_fsync_dir", lambda d: llamadas.append(d))
    almacen.comprimir_objeto(proyecto, h, rec["bytes"])
    assert llamadas == [almacen._zst(proyecto, h).parent]
