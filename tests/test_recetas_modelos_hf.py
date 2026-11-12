"""Recetas de los tres modelos de embeddings (M1-00 t9, M1-09b t2): fuentes del catálogo con descarga manual,
commit fijado y huellas SHA-256 de la auditoría. Ningún modelo se descarga aquí: se usan archivos de mentira."""
import json
import re
import shutil

import pytest

from pap import recetas, almacen
from pap.config import Rutas
from pap.errores import PapError
from pap.registrar import Opciones, registrar
from pap.util import formato_de, mediatype_de
from pap.validacion import comprobar

from conftest import RAIZ_REAL

RUTAS = Rutas(RAIZ_REAL)
AUDITORIA = RAIZ_REAL / "backlog/slice-m1/evidencia/auditoria_modelos_lista_dueno.md"

MODELOS = {
    "HF-MULTILINGUAL-E5-SMALL": ("intfloat/multilingual-e5-small", "614241f622f53c4eeff9890bdc4f31cfecc418b3", "MIT",
                                 "hf-multilingual-e5-small"),
    "HF-GRANITE-EMBEDDING-97M-MULTILINGUAL-R2": ("ibm-granite/granite-embedding-97m-multilingual-r2",
                                                 "835ad14087e140460703cf0fae09f97d469d65c2", "Apache-2.0",
                                                 "hf-granite-embedding-97m-multilingual-r2"),
    "HF-GRANITE-EMBEDDING-311M-MULTILINGUAL-R2": ("ibm-granite/granite-embedding-311m-multilingual-r2",
                                                  "44399559930365213510b1ee2eb15ded83374f0e", "Apache-2.0",
                                                  "hf-granite-embedding-311m-multilingual-r2"),
}
IDS = list(MODELOS)
SHA = re.compile(r"\b([0-9a-f]{64})\b")


def _sumas_auditoria() -> dict[str, dict[str, str]]:
    """{repo: {ruta: sha256}} desde los bloques SHA256SUMS de la lista del dueño."""
    out: dict[str, dict[str, str]] = {}
    repo = None
    dentro = False   # dentro de un bloque ``` cualquiera
    en_bloque = False   # dentro de un bloque ``` que es un SHA256SUMS
    prev = ""
    for linea in AUDITORIA.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## \d\. `([^`]+)`", linea)
        if m:
            repo = m.group(1)
            out[repo] = {}
        if linea.startswith("```"):
            dentro = not dentro
            en_bloque = dentro and "SHA256SUMS" in prev
        elif en_bloque and repo:
            h, ruta = linea.split("  ", 1)
            out[repo][ruta.strip()] = h
        prev = linea
    return out


def _archivos_receta(receta: dict) -> dict[str, tuple[str, str]]:
    """{ruta: (sha256, url)} desde los pasos de la receta (una línea por archivo)."""
    out = {}
    for paso in receta["manual"]["pasos"]:
        h = SHA.search(paso)
        u = re.search(r"https://huggingface\.co/\S+/resolve/\S+", paso)
        if h and u:
            ruta = u.group(0).split("/resolve/", 1)[1].split("/", 1)[1]
            out[ruta] = (h.group(1), u.group(0))
    return out


@pytest.mark.parametrize("sid", IDS)
def test_receta_valida_y_fija_el_commit(sid):
    repo, commit, licencia, _ = MODELOS[sid]
    ruta = RUTAS.recetas / f"{sid}.yaml"
    r = recetas.leer(ruta)
    assert recetas.errores(r, ruta) == []
    assert r["id"] == sid and r["strategy"] == "owner_file"
    assert r["access_url"] == f"https://huggingface.co/{repo}/tree/{commit}"
    assert r["licenses"][0]["name"] == licencia and r["license_basis"] == "declarada_en_pagina"
    assert r["publisher"] and r["dataset_title"] and r["attributed_to"] and r["retrieved_at"]
    assert {"onnx", "json"} <= set(r["espera"]["formato"])


@pytest.mark.parametrize("sid", IDS)
def test_huellas_coinciden_con_la_auditoria(sid):
    repo, commit, _, _ = MODELOS[sid]
    esperadas = _sumas_auditoria()[repo]
    assert len(esperadas) >= 8
    r = recetas.leer(RUTAS.recetas / f"{sid}.yaml")
    en_receta = _archivos_receta(r)
    assert {k: v[0] for k, v in en_receta.items()} == esperadas
    for ruta, (_, url) in en_receta.items():
        assert url == f"https://huggingface.co/{repo}/resolve/{commit}/{ruta}"


@pytest.mark.parametrize("sid", IDS)
def test_entrada_en_el_catalogo_coherente_con_la_receta(sid):
    cat = {f["id"]: f for f in json.loads(RUTAS.catalogo.read_text(encoding="utf-8"))}
    repo, commit, licencia, _ = MODELOS[sid]
    f = cat[sid]
    assert f["licencia"] == licencia and f["estrategia_descarga"] == "descarga_manual"
    assert f["url_portal"] == f"https://huggingface.co/{repo}/tree/{commit}"
    assert f["ola"] == "fuera_de_alcance" and f["compuerta_ingesta"] is None
    assert [m for m in recetas.incoherencias_catalogo(RUTAS) if m.startswith(sid)] == []


def test_onnx_tiene_mediatype_y_se_comprueba(tmp_path):
    assert formato_de(tmp_path / "model.onnx") == "onnx"
    assert mediatype_de("onnx") == "application/octet-stream"
    espera = recetas.leer(RUTAS.recetas / "HF-MULTILINGUAL-E5-SMALL.yaml")["espera"]
    onnx = tmp_path / "model.onnx"
    onnx.write_bytes(b"\x08\x07onnx de mentira")
    cfg = tmp_path / "config.json"
    cfg.write_text("{}", encoding="utf-8")
    assert comprobar(onnx, espera)["estado"] == "valido"
    assert comprobar(cfg, espera)["estado"] == "valido"
    malo = tmp_path / "model.safetensors"
    malo.write_bytes(b"x")
    assert comprobar(malo, espera)["estado"] == "invalido"


def test_registrar_un_onnx_en_una_biblioteca_aislada(proyecto, tmp_path):
    sid = "HF-MULTILINGUAL-E5-SMALL"
    shutil.copy(RUTAS.recetas / f"{sid}.yaml", proyecto.recetas / f"{sid}.yaml")
    onnx = tmp_path / "model.onnx"
    onnx.write_bytes(b"\x08\x07onnx de mentira")
    url = f"https://huggingface.co/{MODELOS[sid][0]}/resolve/{MODELOS[sid][1]}/onnx/model.onnx"
    r = registrar(proyecto, sid, [onnx], Opciones(recurso="e5-small-onnx-model", url_descarga=url))
    rec = json.loads(r.captura.read_text(encoding="utf-8"))["resources"][0]
    assert rec["mediatype"] == "application/octet-stream" and rec["name"] == "e5-small-onnx-model"
    assert rec["licenses"][0]["name"] == "MIT"
    assert len(almacen.objetos(proyecto)) == 1
    safe = tmp_path / "model.safetensors"
    safe.write_bytes(b"x")
    with pytest.raises(PapError, match="formato"):
        registrar(proyecto, sid, [safe])
