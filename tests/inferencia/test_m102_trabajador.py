"""M1-02, tarea 10 (H08-3, H08-4, H04-5): la alarma suave no se escapa del trabajador, una alarma suave descarta la conexión DuckDB
y un SIGKILL ajeno al límite de CPU no se atribuye a la CPU."""
import os
import signal
import sys
from dataclasses import replace

import pytest

import pap.inferencia.ejecutor as ej
from pap.inferencia import almacen
from pap.inferencia.almacen import LectorAbortado, Parametros, ejecutar_aislado


def test_una_alarma_que_llega_tarde_no_se_escapa_de_correr_H08_3(monkeypatch):
    """Simula la carrera: SIGALRM llega justo cuando `_correr` desarma la alarma, después de que la tarea terminó."""
    real = signal.alarm

    def alarma(n):
        if n == 0:
            os.kill(os.getpid(), signal.SIGALRM)          # la señal se entrega antes de desarmar
        return real(n)

    monkeypatch.setattr(ej.signal, "alarm", alarma)
    try:
        assert ej._correr(lambda: 5, 10) == ("ok", 5)
    finally:
        real(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)


def test_tras_una_alarma_suave_el_trabajador_descarta_su_conexion_duckdb_H08_4(monkeypatch):
    estado = {"con": object(), "clave": ("x", None), "p": "parametros"}
    monkeypatch.setattr(ej, "_ESTADO", estado)

    def trabajo():
        raise ej._AlarmaSuave()

    try:
        assert ej._correr(trabajo, 10) == ("tiempo", None)
    finally:
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
    assert estado["con"] is None and estado["clave"] is None and estado["p"] == "parametros"     # la siguiente tarea abre una nueva


def test_un_error_normal_no_descarta_la_conexion(monkeypatch):
    estado = {"con": object(), "clave": ("x", None), "p": None}
    monkeypatch.setattr(ej, "_ESTADO", estado)
    try:
        assert ej._correr(lambda: 1 / 0, 10)[0] == "interno"
    finally:
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
    assert estado["con"] is not None


def test_un_sigkill_ajeno_no_se_atribuye_al_limite_de_cpu_H04_5(tmp_path):
    p = replace(Parametros.desde_yaml(), tiempo_s=60)
    cmd = [sys.executable, "-I", "-c", "import os, signal; os.kill(os.getpid(), signal.SIGKILL)"]
    with pytest.raises(LectorAbortado) as e:
        ejecutar_aislado(cmd, p, cwd=tmp_path)
    assert "SIGKILL" in str(e.value) and "no por el tope de procesador" in str(e.value)


def test_un_sigkill_por_el_limite_de_cpu_si_se_atribuye_a_la_cpu_H04_5(tmp_path):
    p = replace(Parametros.desde_yaml(), cpu_s=1, tiempo_s=60)
    cmd = [sys.executable, "-I", "-c", "while True: pass"]
    with pytest.raises(LectorAbortado, match="procesador"):
        ejecutar_aislado(cmd, p, cwd=tmp_path)
