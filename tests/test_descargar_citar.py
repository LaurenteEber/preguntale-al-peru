import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from pap import bitacora, citar
from pap.descargar import descargar, expandir_patron
from pap.errores import PapError
from pap.registrar import registrar

CONTENIDO = b"ubigeo,monto\n010101,100.50\n"


class Servidor(BaseHTTPRequestHandler):
    etag = '"v1"'

    def do_GET(self):  # noqa: N802
        if self.headers.get("If-None-Match") == self.etag:
            self.send_response(304)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("ETag", self.etag)
        self.send_header("Last-Modified", "Mon, 05 Oct 2026 12:00:00 GMT")
        self.send_header("Content-Disposition", 'attachment; filename="DETALLE.csv"')
        self.end_headers()
        self.wfile.write(CONTENIDO)

    def log_message(self, *a):
        pass


@pytest.fixture
def servidor():
    srv = HTTPServer(("127.0.0.1", 0), Servidor)
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{srv.server_port}/datos.csv"
    srv.shutdown()


def test_descarga_condicional(proyecto, servidor):
    r1 = descargar(proyecto, "PRUEBA-HTTP", url=servidor)
    rec = r1.nuevos[0]
    assert rec["original_filename"] == "DETALLE.csv"
    assert rec["http_etag"] == '"v1"' and rec["download_url"] == servidor
    assert rec["method"] == "http_directo" and rec["attributed_to"].startswith("pap ")
    assert rec["modified"].startswith("2026-10-05")
    r2 = descargar(proyecto, "PRUEBA-HTTP", url=servidor)
    assert r2.nuevos == [] and r2.sin_cambio == [rec["hash"]]
    assert bitacora.leer(proyecto)[-1]["detalle"].startswith("304")


def test_manual_devuelve_pasos(proyecto):
    texto = descargar(proyecto, "PRUEBA-CSV")
    assert "Descargar de la ficha" in texto


def test_patron():
    assert expandir_patron("https://x/{anio}/f.zip", {"anio": "2025"}) == "https://x/2025/f.zip"
    with pytest.raises(PapError):
        expandir_patron("https://x/{anio}/{mes}.zip", {"anio": "2025"})


def test_cita(proyecto, csv_valido):
    from pap.registrar import Opciones
    r = registrar(proyecto, "PRUEBA-CSV", [csv_valido],
                  Opciones(issued="2025-12-31", version="Boletín 2025", consultado="2026-10-06T08:15:00-05:00"))
    rec = r.nuevos[0]
    c = citar.cita(rec)
    assert c.startswith("INEI (2025). Tabla de prueba por distrito [poblacion_distrital.csv], Boletín 2025.")
    assert "Consultado el 06-oct-2026." in c and f"SHA-256: {rec['hash'][7:19]}." in c
    assert "Datos al" not in c  # corte desconocido: no se inventa
    assert "descarga manual" in citar.ficha_corta(rec)
