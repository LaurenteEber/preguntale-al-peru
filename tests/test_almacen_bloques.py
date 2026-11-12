"""M0-11 (tareas 1–2): `pap almacen restaurar` y `pap almacen liberar` con un bloque sintético.

`gh` se reemplaza por un programa falso en PATH que «baja» el release desde una carpeta local: no hay red ni token
real. El bloque `endes-2024` tiene un ZIP que lee `pap calcular` (hogar), un ZIP liberable (mujer, con un DTA real
convertido con el conversor de M0-04) y un PDF; fuera del bloque hay una sumaria de la ENAHO y un crudo del MEF."""
import hashlib
import io
import json
import os
import shutil
import zipfile
from pathlib import Path

import pandas as pd
import pyreadstat
import pytest

from pap import almacen, bloques, cli
from pap.inferencia.almacen import Parametros, convertir_archivo, huella_contenido_v1

SECRETO = "gh" + "p_" + "SECRETO_DE_PRUEBA_456"
URL = "https://github.com/LaurenteEber/preguntale-al-peru-crudos/releases/tag/crudos-endes-2024"


def _zip(miembros: dict[str, bytes]) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
        for n, c in miembros.items():
            z.writestr(n, c)
    return b.getvalue()


def _guardar(rutas, contenido: bytes) -> str:
    h = hashlib.sha256(contenido).hexdigest()
    p = rutas.cruda / almacen.ruta_relativa(h)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(contenido)
    return h


def _rec(fuente, nombre, archivo, h, n, formato):
    return {"name": nombre, "original_filename": archivo, "path": almacen.ruta_relativa(h), "hash": f"sha256:{h}",
            "bytes": n, "format": formato, "source_id": fuente, "retrieved_at": "2026-11-09T10:00:00-05:00"}


def _datapackage(rutas, fuente, recs):
    p = rutas.capturas / fuente / "2026-11-09" / "datapackage.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"name": fuente, "resources": recs}), encoding="utf-8")
    return p


@pytest.fixture
def bloque(proyecto, tmp_path, monkeypatch):
    rutas = proyecto
    trabajo = tmp_path / "fabrica"
    trabajo.mkdir()
    dta = trabajo / "REC0111_2024.dta"
    pyreadstat.write_dta(pd.DataFrame({"NUMERO": [1, 2], "EDAD": [30, 41]}), str(dta))
    zips = {
        "endes-2024-hogar": ("968-Modulo1629.zip", _zip({"968-Modulo1629/RECH0_2024.dta": b"hogar"})),
        "endes-2024-mujer": ("968-Modulo1631.zip", _zip({"968-Modulo1631/REC0111_2024.dta": dta.read_bytes()})),
    }
    recs, contenidos = [], {}
    for nombre, (archivo, c) in zips.items():
        recs.append(_rec("INEI-ENDES", nombre, archivo, _guardar(rutas, c), len(c), "zip"))
        contenidos[archivo] = c
    pdf = b"%PDF-1.4 ficha"
    recs.append(_rec("INEI-ENDES", "endes-2024-ficha", "Ficha.pdf", _guardar(rutas, pdf), len(pdf), "pdf"))
    contenidos["Ficha.pdf"] = pdf
    dp_endes = _datapackage(rutas, "INEI-ENDES", recs)
    sumaria = _zip({"966-Modulo34/sumaria-2024.dta": b"sumaria"})
    dp_enaho = _datapackage(rutas, "INEI-ENAHO", [_rec("INEI-ENAHO", "enaho-2024-sumaria", "966-Modulo34.zip",
                                                       _guardar(rutas, sumaria), len(sumaria), "zip")])
    mef = b"a;b\n1;2\n"
    _datapackage(rutas, "MEF-PIM", [_rec("MEF-PIM", "pim", "pim.csv", _guardar(rutas, mef), len(mef), "csv")])
    # Microdatos convertidos y su manifiesto (como deja `pap microdatos convertir`).
    micro = rutas.raiz / "biblioteca" / "microdatos" / "ENDES" / "2024"
    parquet = micro / "REC0111.parquet"
    convertir_archivo(dta, parquet, anio=2024, formato="dta", p=Parametros.desde_yaml())
    h_mujer = recs[1]["hash"].split(":")[1]
    (micro / "manifiesto.json").write_text(json.dumps({"encuesta": "ENDES", "anio": 2024, "archivos": {"REC0111": {
        "origen": {"zip": "968-Modulo1631.zip", "zip_sha256": h_mujer, "recurso": "endes-2024-mujer",
                   "miembro": "968-Modulo1631/REC0111_2024.dta"},
        "huella_contenido_v1": huella_contenido_v1(parquet), "filas": 2, "parquet": "REC0111.parquet"}}}),
        encoding="utf-8")
    (rutas.raiz / "insumos.lock.yaml").write_text("INEI-ENDES: []\n", encoding="utf-8")
    rutas.indice.write_bytes(b"duckdb")
    # Release falso: los mismos archivos con su SHA256SUMS y LEEME.
    release = tmp_path / "release"
    release.mkdir()
    for archivo, c in contenidos.items():
        (release / archivo).write_bytes(c)
    (release / "SHA256SUMS").write_text("".join(f"{hashlib.sha256(c).hexdigest()}  {a}\n"
                                                for a, c in sorted(contenidos.items())), encoding="utf-8")
    (release / "LEEME.txt").write_text("Crudos ENDES 2024", encoding="utf-8")
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    gh = bin_ / "gh"
    gh.write_text(
        '#!/usr/bin/env bash\necho "$*" >> "$GH_REGISTRO"\n'
        'if [ "$1 $2" = "repo view" ]; then echo "$GH_VISIBILIDAD"; exit 0; fi\n'
        'if [ "$1 $2" = "release download" ]; then cp "$GH_RELEASE"/* "${@: -1}"/; exit 0; fi\n'
        f'if [ "$1 $2" = "release view" ]; then echo "{URL}"; exit 0; fi\n'
        'exit 1\n')
    gh.chmod(0o755)
    registro = tmp_path / "llamadas.txt"
    monkeypatch.setenv("PATH", f"{bin_}:{os.environ['PATH']}")
    monkeypatch.setenv("GH_REGISTRO", str(registro))
    monkeypatch.setenv("GH_RELEASE", str(release))
    monkeypatch.setenv("GH_VISIBILIDAD", "PRIVATE")
    monkeypatch.setenv("GH_TOKEN", SECRETO)
    monkeypatch.setattr(bloques, "espacio_libre_gb", lambda rutas: 500.0)
    rutas_zip = {n: rutas.cruda / r["path"] for n, r in zip(["hogar", "mujer", "ficha"], recs)}
    protegidos = [rutas_zip["hogar"], rutas_zip["ficha"], parquet, micro / "manifiesto.json", dp_endes, dp_enaho,
                  rutas.raiz / "insumos.lock.yaml", rutas.indice,
                  rutas.cruda / almacen.ruta_relativa(hashlib.sha256(sumaria).hexdigest()),
                  rutas.cruda / almacen.ruta_relativa(hashlib.sha256(mef).hexdigest())]
    return {"rutas": rutas, "release": release, "registro": registro, "mujer": rutas_zip["mujer"],
            "protegidos": protegidos, "h_mujer": h_mujer}


def _huellas(paths):
    return {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def _bitacora(rutas):
    p = rutas.verificaciones
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


def _bloques(rutas):
    return bloques.leer_bloques(rutas)


# ------------------------------------------------------------------ restaurar

def test_restaurar_comprueba_huellas_reconvierte_y_marca_respaldado(bloque, capsys):
    rutas = bloque["rutas"]
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 0
    out, err = capsys.readouterr()
    assert "SHA256SUMS: OK (3 archivos)" in out
    for nombre in ("endes-2024-hogar", "endes-2024-mujer", "endes-2024-ficha"):
        assert f"OK         {nombre}" in out
    assert "Reconversión de REC0111 (968-Modulo1631/REC0111_2024.dta): huella_contenido_v1 igual" in out
    assert SECRETO not in out + err
    b = _bloques(rutas)["endes-2024"]
    assert b["estado"] == "respaldado" and b["release"] == URL and b["etiqueta"] == "crudos-endes-2024"
    assert bloque["h_mujer"] in b["huellas"] and len(b["huellas"]) == 3
    assert b["reconvertido"]["archivo"] == "REC0111"
    assert "Repuesto en el almacén" not in out             # nada faltaba: no toca el almacén
    ult = _bitacora(rutas)[-1]
    assert ult["accion"] == "restaurar" and ult["resultado"] == "ok" and URL in ult["detalle"]


def test_restaurar_falla_si_un_archivo_del_release_no_cuadra(bloque, capsys):
    rutas = bloque["rutas"]
    (bloque["release"] / "968-Modulo1631.zip").write_bytes(b"otro contenido")
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 1
    _, err = capsys.readouterr()
    assert "SHA256SUMS no cuadra: 968-Modulo1631.zip" in err
    assert "endes-2024" not in _bloques(rutas)
    assert _bitacora(rutas)[-1]["resultado"] == "fallo"


def test_restaurar_falla_si_falta_un_recurso_en_el_release(bloque, capsys):
    rutas = bloque["rutas"]
    (bloque["release"] / "968-Modulo1629.zip").unlink()
    sumas = bloque["release"] / "SHA256SUMS"
    sumas.write_text("".join(l + "\n" for l in sumas.read_text().splitlines() if "1629" not in l))
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 1
    out, err = capsys.readouterr()
    assert "FALTA      endes-2024-hogar" in out
    assert "endes-2024-hogar (falta en el release)" in err
    assert "endes-2024" not in _bloques(rutas)


def test_restaurar_falla_si_la_reconversion_no_da_la_misma_huella(bloque, capsys):
    rutas = bloque["rutas"]
    man = rutas.raiz / "biblioteca/microdatos/ENDES/2024/manifiesto.json"
    m = json.loads(man.read_text())
    m["archivos"]["REC0111"]["huella_contenido_v1"] = "0" * 64
    man.write_text(json.dumps(m))
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 1
    _, err = capsys.readouterr()
    assert "REC0111: la huella_contenido_v1 reconvertida no es la del manifiesto" in err
    assert "endes-2024" not in _bloques(rutas)


def test_restaurar_se_niega_ante_repo_publico(bloque, capsys, monkeypatch):
    monkeypatch.setenv("GH_VISIBILIDAD", "PUBLIC")
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 1
    out, err = capsys.readouterr()
    assert "no es privado (visibilidad: PUBLIC)" in err and SECRETO not in out + err
    assert not [x for x in bloque["registro"].read_text().splitlines() if "release" in x]


def test_restaurar_se_niega_ante_otro_repo(bloque, capsys):
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024", "--repo", "otro/repositorio"]) == 1
    assert "no es el configurado" in capsys.readouterr().err
    assert not bloque["registro"].exists()


def test_restaurar_se_niega_sin_token(bloque, capsys, monkeypatch):
    monkeypatch.delenv("GH_TOKEN")
    monkeypatch.setenv("PAP_LLAVERO_SERVICIO", "pap-servicio-que-no-existe")
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 1
    assert "Falta GH_TOKEN" in capsys.readouterr().err
    assert not bloque["registro"].exists()


def test_bloque_mal_escrito(proyecto, capsys):
    assert cli.main(["almacen", "liberar", "--bloque", "endes2024"]) == 1
    assert "debe ser <encuesta>-<anio>" in capsys.readouterr().err
    assert cli.main(["almacen", "restaurar"]) == 1
    assert "necesita --bloque" in capsys.readouterr().err


# ------------------------------------------------------------------ liberar

def test_liberar_no_libera_un_bloque_sin_restauracion_probada(bloque, capsys):
    rutas = bloque["rutas"]
    antes = _huellas(bloque["protegidos"] + [bloque["mujer"]])
    for args in ([], ["--ejecutar", "--si"]):
        assert cli.main(["almacen", "liberar", "--bloque", "endes-2024", *args]) == 1
        assert "no está respaldado con la restauración probada" in capsys.readouterr().err
    assert _huellas(bloque["protegidos"] + [bloque["mujer"]]) == antes
    assert _bitacora(rutas) == []


def test_liberar_simula_por_defecto(bloque, capsys):
    rutas = bloque["rutas"]
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 0
    capsys.readouterr()
    n_bitacora = len(_bitacora(rutas))
    antes = _huellas(bloque["protegidos"] + [bloque["mujer"]])
    assert cli.main(["almacen", "liberar", "--bloque", "endes-2024"]) == 0
    out = capsys.readouterr().out
    assert "liberaría  endes-2024-mujer" in out
    assert "se queda   endes-2024-hogar" in out and "(lo lee `pap calcular`)" in out
    assert "se queda   endes-2024-ficha" in out and "(no es un ZIP)" in out
    assert "Total: 1 ZIP" in out and "Simulación: no se borró nada" in out
    assert _huellas(bloque["protegidos"] + [bloque["mujer"]]) == antes
    assert len(_bitacora(rutas)) == n_bitacora


def test_liberar_borra_solo_el_zip_liberable_y_lo_registra(bloque, capsys):
    rutas = bloque["rutas"]
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 0
    antes = _huellas(bloque["protegidos"])
    n = bloque["mujer"].stat().st_size
    assert cli.main(["almacen", "liberar", "--bloque", "endes-2024", "--ejecutar", "--si"]) == 0
    out = capsys.readouterr().out
    assert "Liberados 1 ZIP" in out
    assert not bloque["mujer"].exists()
    assert _huellas(bloque["protegidos"]) == antes      # la lista protegida queda intacta, byte a byte
    ult = _bitacora(rutas)[-1]
    assert ult["accion"] == "liberar" and ult["resultado"] == "ok" and ult["hash"] == f"sha256:{bloque['h_mujer']}"
    assert URL in ult["detalle"]
    lib = _bloques(rutas)["endes-2024"]["liberado"]
    assert lib["archivos"] == 1 and lib["bytes"] == n
    # Una segunda vez no hay nada que liberar.
    assert cli.main(["almacen", "liberar", "--bloque", "endes-2024", "--ejecutar", "--si"]) == 0
    assert "Nada que liberar" in capsys.readouterr().out
    # Restaurar un bloque liberado vuelve a poner el ZIP en el almacén, idéntico, y conserva el registro de la liberación.
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 0
    assert "Repuesto en el almacén: endes-2024-mujer  968-Modulo1631.zip" in capsys.readouterr().out
    assert hashlib.sha256(bloque["mujer"].read_bytes()).hexdigest() == bloque["h_mujer"]
    assert _bloques(rutas)["endes-2024"]["liberado"]["archivos"] == 1
    assert _huellas(bloque["protegidos"]) == antes


def test_liberar_sin_confirmacion_no_borra(bloque, capsys, monkeypatch):
    rutas = bloque["rutas"]
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 0
    capsys.readouterr()
    monkeypatch.setattr("sys.stdin", io.StringIO(""))   # sin terminal: no se puede confirmar
    assert cli.main(["almacen", "liberar", "--bloque", "endes-2024", "--ejecutar"]) == 1
    assert "liberación no confirmada: no se borró nada" in capsys.readouterr().err
    assert bloque["mujer"].exists()
    assert _bitacora(rutas)[-1]["accion"] == "restaurar"


def test_liberar_no_toca_un_zip_cuya_huella_no_se_comprobo(bloque, capsys):
    rutas = bloque["rutas"]
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 0
    reg = json.loads(almacen.ruta_registro(rutas).read_text())
    reg["bloques"]["endes-2024"]["huellas"].remove(bloque["h_mujer"])
    almacen.ruta_registro(rutas).write_text(json.dumps(reg))
    capsys.readouterr()
    assert cli.main(["almacen", "liberar", "--bloque", "endes-2024", "--ejecutar", "--si"]) == 0
    assert "(su huella no se comprobó al restaurar)" in capsys.readouterr().out
    assert bloque["mujer"].exists()


def test_liberar_no_toca_un_zip_que_usa_otro_recurso(bloque, capsys):
    rutas = bloque["rutas"]
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 0
    c = bloque["mujer"].read_bytes()
    _datapackage(rutas, "INEI-ENDES-OTRO", [_rec("INEI-ENDES-OTRO", "copia", "x.zip", bloque["h_mujer"], len(c), "zip")])
    capsys.readouterr()
    assert cli.main(["almacen", "liberar", "--bloque", "endes-2024", "--ejecutar", "--si"]) == 0
    assert "(lo usa otro recurso)" in capsys.readouterr().out
    assert bloque["mujer"].exists()


def test_liberar_avisa_si_queda_poco_espacio(bloque, capsys, monkeypatch):
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 0
    monkeypatch.setattr(bloques, "espacio_libre_gb", lambda rutas: 12.3)
    capsys.readouterr()
    assert cli.main(["almacen", "liberar", "--bloque", "endes-2024"]) == 0
    assert ("Aviso: quedan 12.3 GB libres, menos que el mínimo de 50 GB (almacen.espacio_libre_min_gb)."
            in capsys.readouterr().out)


def test_comprimir_conserva_los_bloques_del_registro(bloque, tmp_path):
    """anotar_zst reescribe almacen_zst.json: no debe perder la clave `bloques` que escribe restaurar."""
    rutas = bloque["rutas"]
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 0
    csv = b"x;y\n" + b"1;2\n" * 1000
    h = _guardar(rutas, csv)
    _datapackage(rutas, "MEF-GRANDE", [_rec("MEF-GRANDE", "grande", "grande.csv", h, len(csv), "csv")])
    assert cli.main(["almacen", "comprimir", "--min-mb", "0", "--solo", h[:12]]) == 0
    reg = json.loads(almacen.ruta_registro(rutas).read_text())
    assert h in reg["objetos"] and reg["bloques"]["endes-2024"]["estado"] == "respaldado"


# ------------------------------------------------------------------ revisión por partes (M0-11): nombres y formatos del release

def _sin(bloque, archivo):
    (bloque["release"] / archivo).unlink()
    s = bloque["release"] / "SHA256SUMS"
    s.write_text("".join(l + "\n" for l in s.read_text().splitlines() if archivo not in l))


def test_restaurar_no_acepta_original_filename_con_ruta(bloque, capsys):
    """Un datapackage editado con una ruta no puede hacer pasar por respaldado un ZIP que no está en el release."""
    rutas = bloque["rutas"]
    dp = rutas.capturas / "INEI-ENDES" / "2026-11-09" / "datapackage.json"
    d = json.loads(dp.read_text())
    d["resources"][1]["original_filename"] = str(bloque["mujer"])
    dp.write_text(json.dumps(d))
    _sin(bloque, "968-Modulo1631.zip")
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 1
    assert "nombre de archivo no permitido" in capsys.readouterr().err
    assert "endes-2024" not in _bloques(rutas)
    assert cli.main(["almacen", "liberar", "--bloque", "endes-2024", "--ejecutar", "--si"]) == 1
    assert bloque["mujer"].exists()


def test_restaurar_rechaza_nombres_con_ruta_en_sha256sums(bloque, capsys, tmp_path):
    f = tmp_path / "fuera.txt"
    f.write_bytes(b"x")
    s = bloque["release"] / "SHA256SUMS"
    s.write_text(s.read_text() + f"{hashlib.sha256(b'x').hexdigest()}  {f}\n")
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 1
    assert "SHA256SUMS, línea 4: nombre de archivo no permitido" in capsys.readouterr().err
    assert "endes-2024" not in _bloques(bloque["rutas"])


def test_restaurar_sha256sums_mal_formado_falla_con_mensaje(bloque, capsys):
    s = bloque["release"] / "SHA256SUMS"
    s.write_text(s.read_text() + "solounhash\n")
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 1
    assert "SHA256SUMS, línea 4: no tiene la forma" in capsys.readouterr().err
    assert _bitacora(bloque["rutas"])[-1]["resultado"] == "fallo"


def test_restaurar_no_imprime_token_si_gh_falla(bloque, capsys, tmp_path):
    (tmp_path / "bin" / "gh").write_text('#!/usr/bin/env bash\nif [ "$1 $2" = "repo view" ]; then echo PRIVATE; exit 0; fi\n'
                                         'echo "fallo token=$GH_TOKEN" >&2; exit 1\n')
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 1
    out, err = capsys.readouterr()
    assert SECRETO not in out + err and SECRETO not in bloque["rutas"].verificaciones.read_text()


def test_liberar_no_borra_un_objeto_que_comparte_huella_con_un_protegido(bloque, capsys):
    """Si un ZIP liberable tuviera la huella del de hogar (protegido), el objeto es uno solo y no se borra."""
    rutas = bloque["rutas"]
    dp = rutas.capturas / "INEI-ENDES" / "2026-11-09" / "datapackage.json"
    d = json.loads(dp.read_text())
    hogar = d["resources"][0]
    d["resources"].append({**hogar, "name": "endes-2024-vivienda", "original_filename": "968-Modulo1630.zip"})
    dp.write_text(json.dumps(d))
    (bloque["release"] / "968-Modulo1630.zip").write_bytes((bloque["release"] / "968-Modulo1629.zip").read_bytes())
    s = bloque["release"] / "SHA256SUMS"
    s.write_text(s.read_text() + f"{hogar['hash'].split(':')[1]}  968-Modulo1630.zip\n")
    assert cli.main(["almacen", "restaurar", "--bloque", "endes-2024"]) == 0
    capsys.readouterr()
    assert cli.main(["almacen", "liberar", "--bloque", "endes-2024", "--ejecutar", "--si"]) == 0
    out = capsys.readouterr().out
    assert "se queda   endes-2024-vivienda" in out and "(lo usa otro recurso)" in out
    assert (rutas.cruda / hogar["path"]).exists()
