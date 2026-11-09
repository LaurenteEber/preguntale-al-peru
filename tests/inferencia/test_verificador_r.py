"""M0-09: `verificador_r/` sin correr R (R no corre dentro de pytest): `renv.lock` (versiones y repositorio), la llamada sin shell con
entorno mínimo (C11) y los archivos que el proyecto renv necesita."""
import json
import re
import subprocess
from datetime import date

import yaml

from conftest import RAIZ_REAL
from pap.inferencia import verificador_r as vr

CARPETA = RAIZ_REAL / "verificador_r"
PARAMETROS = yaml.safe_load((RAIZ_REAL / "curados" / "inferencia" / "parametros.yaml").read_text(encoding="utf-8"))
LOCK = json.loads((CARPETA / "renv.lock").read_text(encoding="utf-8"))


def test_renv_lock_fija_renv_1_3_1_y_nanoparquet_0_5_2():
    paquetes = LOCK["Packages"]
    assert paquetes["renv"]["Version"] == "1.3.1"            # la 1.2.4 no pasó la auditoría
    assert paquetes["nanoparquet"]["Version"] == "0.5.2"     # la 0.5.1 leía mal los perdidos con col_select
    assert paquetes["survey"]["Version"] == PARAMETROS["verificador_r"]["survey_version"]["valor"] == "4.5"
    assert {"survey", "jsonlite", "nanoparquet", "renv", "minqa"} <= set(paquetes)
    assert all(p["Source"] == "Repository" for p in paquetes.values())


def test_renv_lock_apunta_a_una_instantanea_con_fecha_de_al_menos_dos_semanas():
    repos = LOCK["R"]["Repositories"]
    assert len(repos) == 1 and repos[0]["Name"] == "CRAN"
    m = re.fullmatch(r"https://packagemanager\.posit\.co/cran/(\d{4}-\d{2}-\d{2})", repos[0]["URL"])
    assert m, repos[0]["URL"]
    instantanea = date.fromisoformat(m.group(1))
    assert m.group(1) == PARAMETROS["verificador_r"]["cran_instantanea"]["valor"]
    assert (date.today() - instantanea).days >= PARAMETROS["seguridad"]["lock_dias_min"]["valor"]
    assert LOCK["R"]["Version"].startswith("4.6.")


def paquetes_dudosos(lock: dict) -> list[str]:
    """Paquetes del lock con un `Title` que dice «stub» o con un `Repository` que no es CRAN ni RSPM (M0-09, dueño 9/11/2026:
    la biblioteca se restaura solo con binarios de la instantánea; un paquete de reemplazo no puede volver a colarse)."""
    return sorted(nombre for nombre, p in lock["Packages"].items()
                  if "stub" in p.get("Title", "").lower() or p.get("Repository") not in ("CRAN", "RSPM"))


def test_ningun_paquete_del_lock_es_un_stub_y_todos_vienen_de_cran_o_rspm():
    assert LOCK["Packages"] and paquetes_dudosos(LOCK) == []


def test_paquetes_dudosos_detecta_un_stub_y_un_repositorio_ajeno():
    lock = {"Packages": {"minqa": {"Title": "Stub provisional sin Fortran", "Repository": "CRAN"},
                         "otro": {"Title": "Un paquete", "Repository": "github"},
                         "bien": {"Title": "Un paquete", "Repository": "RSPM"}}}
    assert paquetes_dudosos(lock) == ["minqa", "otro"]


def test_el_proyecto_renv_esta_completo_y_la_biblioteca_local_no_se_versiona():
    assert 'source("renv/activate.R")' in (CARPETA / ".Rprofile").read_text(encoding="utf-8")
    assert 'version <- "1.3.1"' in (CARPETA / "renv" / "activate.R").read_text(encoding="utf-8")
    assert (CARPETA / "verificar.R").exists() and (CARPETA / "README.md").exists() and (CARPETA / "verificar_prototipo.R").exists()
    ignorados = subprocess.run(["git", "check-ignore", "-q", "verificador_r/renv/library/x"], cwd=RAIZ_REAL).returncode
    assert ignorados == 0


def test_el_entorno_minimo_no_deja_pasar_claves_ni_tokens():
    origen = {"PATH": "/usr/bin", "HOME": "/h", "TMPDIR": "/t", "PAP_ANTHROPIC_API_KEY": "sk-x", "GH_TOKEN": "ghp_x", "GITHUB_TOKEN": "t",
              "AWS_SECRET_ACCESS_KEY": "s", "R_LIBS_USER": "/otra", "LANG": "es_PE.UTF-8"}
    env = vr.entorno_minimo(origen)
    assert set(env) <= set(vr.ENTORNO_PERMITIDO) | set(vr.ENTORNO_FIJO)
    assert not {"PAP_ANTHROPIC_API_KEY", "GH_TOKEN", "GITHUB_TOKEN", "AWS_SECRET_ACCESS_KEY", "R_LIBS_USER"} & set(env)
    assert env["PATH"] == "/usr/bin" and env["HOME"] == "/h" and env["LANG"] == "en_US.UTF-8"


def test_la_llamada_es_rscript_vanilla_con_lista_de_argumentos_sin_shell(monkeypatch, tmp_path):
    visto = {}

    def falso(args, **kw):
        visto.update(args=args, **kw)
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(subprocess, "run", falso)
    monkeypatch.setenv("GH_TOKEN", "ghp_secreto")
    monkeypatch.setenv("PAP_ANTHROPIC_API_KEY", "sk-secreto")
    vr.correr({"contrato": "pap-verificador-r/1"})
    assert isinstance(visto["args"], list) and visto["args"][1:3] == ["--vanilla", str(CARPETA / "verificar.R")]
    assert visto["args"][0].endswith("Rscript") and visto["args"][3].endswith("parametros.json") and len(visto["args"]) == 4
    assert visto["shell"] is False and visto["cwd"] == CARPETA
    assert "GH_TOKEN" not in visto["env"] and "PAP_ANTHROPIC_API_KEY" not in visto["env"]


def test_verificar_r_recibe_un_json_y_no_llama_a_shell_ni_a_la_red():
    codigo = "\n".join(l for l in (CARPETA / "verificar.R").read_text(encoding="utf-8").splitlines() if not l.lstrip().startswith("#"))
    assert "fromJSON(ruta_params" in codigo and "read_parquet" in codigo and "--vanilla" in (CARPETA / "verificar.R").read_text(encoding="utf-8")
    for prohibido in ("system(", "system2(", "shell(", "download.file", "install.packages", "Sys.getenv", "url("):
        assert prohibido not in codigo, prohibido
