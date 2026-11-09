"""M0-08: trabajos de prueba del pool. Son clases de módulo (no funciones locales) para que el trabajador `spawn` las pueda importar."""
import os
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Responder:
    valor: int = 1

    def __call__(self):
        return (self.valor, os.getpid())


@dataclass(frozen=True)
class DormirPython:
    """Un ciclo de Python que no termina por sí solo: el tiempo suave (`signal.alarm`) lo corta."""
    segundos: float = 30

    def __call__(self):
        fin = time.monotonic() + self.segundos
        while time.monotonic() < fin:
            sum(range(1000))
        return "terminó"


@dataclass(frozen=True)
class ConsumirMemoria:
    """Pide `mb` megas y los toca (para que cuenten en la memoria residente) de a 25 MB."""
    mb: int = 2000

    def __call__(self):
        trozos = []
        for _ in range(self.mb // 25):
            trozos.append(bytearray(b"\x01") * (25 * 1024 * 1024))
            time.sleep(0.01)
        return len(trozos)


@dataclass(frozen=True)
class Caer:
    def __call__(self):
        os.abort()


@dataclass(frozen=True)
class VerEntorno:
    def __call__(self):
        import polars as pl

        return ({k: os.environ.get(k) for k in ("POLARS_MAX_THREADS", "RAYON_NUM_THREADS")}, pl.thread_pool_size())


@dataclass(frozen=True)
class VerDuckdb:
    """Los topes de la conexión DuckDB del trabajador."""
    raiz: str

    def __call__(self):
        from pathlib import Path

        from pap.inferencia.ejecutor import _conexion

        con = _conexion(Path(self.raiz))
        return tuple(con.execute("SELECT current_setting('threads'), current_setting('memory_limit')").fetchone())


@dataclass(frozen=True)
class ConPico:
    """Corre `trabajo` y devuelve (resultado, segundos dentro del trabajador, pico de memoria residente en bytes)."""
    trabajo: object

    def __call__(self):
        from pap.inferencia.lector_aislado import _rss_max_bytes

        t0 = time.monotonic()
        r = self.trabajo()
        return r, time.monotonic() - t0, _rss_max_bytes()
