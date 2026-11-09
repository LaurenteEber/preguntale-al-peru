"""Lanzador del verificador en R (M0-09; `tecnologias.md` §3 y control C11).

R **no corre dentro de pytest**: este módulo se usa a mano en el Mac (`just esperados-r`) para generar una vez
`tests/esperados/r_survey_sintetico.csv`, y pytest solo compara. La llamada es siempre:
- `Rscript --vanilla verificar.R <parametros.json>` como subproceso, con lista de argumentos (sin shell);
- parámetros en un JSON;
- entorno mínimo: solo lo de la lista blanca de abajo, nunca `PAP_ANTHROPIC_API_KEY`, `GH_TOKEN` ni nada parecido.

Uso: uv run python -m pap.inferencia.verificador_r esperados [--salida RUTA]
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[3]
CARPETA_R = RAIZ_REPO / "verificador_r"
SALIDA_ESPERADOS = RAIZ_REPO / "tests" / "esperados" / "r_survey_sintetico.csv"
# Lista blanca (C11): lo que Rscript y renv necesitan para encontrar R, la caché de renv y un directorio temporal.
ENTORNO_PERMITIDO = ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "R_HOME")
ENTORNO_FIJO = {"LANG": "en_US.UTF-8", "RENV_CONFIG_AUTOLOADER_ENABLED": "TRUE"}
TIEMPO_MAX_S = 900


def entorno_minimo(origen: dict[str, str] | None = None) -> dict[str, str]:
    """Del entorno de origen, solo las variables de la lista blanca (más las fijas). Ninguna clave ni token pasa."""
    origen = os.environ if origen is None else origen
    env = {k: origen[k] for k in ENTORNO_PERMITIDO if k in origen}
    env.update(ENTORNO_FIJO)
    return env


def argumentos(parametros: Path, rscript: str | None = None) -> list[str]:
    """La lista de argumentos (sin shell) con que se invoca al verificador."""
    exe = rscript or shutil.which("Rscript") or "Rscript"
    return [exe, "--vanilla", str(CARPETA_R / "verificar.R"), str(Path(parametros).resolve())]


def correr(parametros: dict, *, env: dict[str, str] | None = None, tiempo_max_s: int = TIEMPO_MAX_S) -> subprocess.CompletedProcess:
    """Escribe el JSON en un directorio temporal, llama a `verificar.R` y devuelve el proceso (salida de texto)."""
    with tempfile.TemporaryDirectory(prefix="pap_verificador_r_") as tmp:
        ruta = Path(tmp) / "parametros.json"
        ruta.write_text(json.dumps(parametros, ensure_ascii=False, indent=2), encoding="utf-8")
        return subprocess.run(argumentos(ruta), cwd=CARPETA_R, env=entorno_minimo() if env is None else env, shell=False,
                              capture_output=True, text=True, timeout=tiempo_max_s, check=False)


def generar_esperados(salida: Path = SALIDA_ESPERADOS) -> Path:
    sys.path.insert(0, str(RAIZ_REPO / "tests"))
    from inferencia.sintetico_r import parametros_r  # noqa: E402  (solo en este uso manual: los casos viven con las pruebas)

    salida.parent.mkdir(parents=True, exist_ok=True)
    p = correr(parametros_r(salida.resolve()))
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    if p.returncode != 0:
        raise SystemExit(f"verificar.R terminó con código {p.returncode}")
    return salida


def main(argv: list[str] | None = None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] != "esperados":
        print(__doc__)
        return 2
    salida = Path(a[a.index("--salida") + 1]) if "--salida" in a else SALIDA_ESPERADOS
    generar_esperados(salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
