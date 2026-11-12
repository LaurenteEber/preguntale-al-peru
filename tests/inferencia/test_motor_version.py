"""M1-00 tarea 10: bandera `motor.version` por tema (diseño §24). En M1 todos los temas siguen en `actual`."""
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]


def _parametros() -> dict:
    return yaml.safe_load((RAIZ / "curados/motor/parametros_motor.yaml").read_text(encoding="utf-8"))


def test_motor_version_cubre_cada_tema_del_vocabulario_y_todos_siguen_en_actual():
    p = _parametros()
    temas = set(p["temas"]["vocabulario"]["valor"])
    version = p["motor"]["version"]
    assert set(version["valor"]) == temas
    assert set(version["valor"].values()) == {"actual"}
    assert set(version["valores_posibles"]) == {"actual", "sombra", "nuevo"}


def test_modo_del_interprete_sigue_en_actual_y_los_parametros_nuevos_de_m1_estan_en_datos():
    assert _parametros()["inferencia"]["modo_interprete"]["valor"] == "actual"
    q = yaml.safe_load((RAIZ / "curados/inferencia/parametros.yaml").read_text(encoding="utf-8"))
    assert q["recuperador"]["candidatos_max"]["valor"] == 20
    assert q["planificador"]["muestras"]["valor"] == 3 and q["planificador"]["modelo"]["valor"] == "claude-sonnet-5-5"
    assert q["batch"]["tope_lote_usd"]["valor"] == 20          # K-05
