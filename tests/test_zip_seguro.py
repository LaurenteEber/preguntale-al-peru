"""M0-00b (A3, control C7): `abrir_zip_seguro` rechaza los ZIP peligrosos y lee igual los ZIP registrados."""
import hashlib
import io
import random
import stat
import zipfile

import pytest

from pap.zip_seguro import Limites, ZipInseguro, abrir_zip_seguro

from conftest import RAIZ_REAL


def _zip(ruta, miembros, comprimir=zipfile.ZIP_DEFLATED):
    with zipfile.ZipFile(ruta, "w", comprimir) as z:
        for info, datos in miembros:
            info.compress_type = comprimir
            z.writestr(info, datos)
    return ruta


def _info(nombre, attr=None):
    i = zipfile.ZipInfo(nombre)
    if attr is not None:
        i.external_attr = attr << 16
    return i


def test_lee_un_zip_normal_por_bloques(tmp_path):
    datos = random.Random(0).randbytes(3 << 20)                 # 3 MB, más que un bloque y sin proporción alta
    ruta = _zip(tmp_path / "ok.zip", [(_info("carpeta/RECH0.dta"), datos), (_info("carpeta/"), b"")])
    with abrir_zip_seguro(ruta) as z:
        assert z.miembros() == ["carpeta/RECH0.dta"]
        assert z.leer("carpeta/RECH0.dta") == datos
        b = io.BytesIO()
        assert z.copiar("carpeta/RECH0.dta", b) == len(datos)
        assert b.getvalue() == datos


@pytest.mark.parametrize("nombre", ["../fuera.dta", "a/../../fuera.dta", "/etc/passwd", "C:/x.dta"])
def test_rechaza_rutas_absolutas_o_con_puntos(tmp_path, nombre):
    ruta = _zip(tmp_path / "malo.zip", [(_info(nombre), b"x")])
    with pytest.raises(ZipInseguro, match="ruta no permitida"):
        with abrir_zip_seguro(ruta):
            pass


def test_rechaza_enlaces_simbolicos(tmp_path):
    ruta = _zip(tmp_path / "enlace.zip", [(_info("enlace", stat.S_IFLNK | 0o777), b"/etc/passwd")])
    with pytest.raises(ZipInseguro, match="enlace simbólico"):
        with abrir_zip_seguro(ruta):
            pass


def test_rechaza_miembros_cifrados(tmp_path):
    ruta = _zip(tmp_path / "cifrado.zip", [(_info("RECH0.dta"), b"datos")])
    crudo = bytearray(ruta.read_bytes())
    for firma, desplazamiento in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):   # bit 0 de las banderas = cifrado
        i = crudo.find(firma)
        crudo[i + desplazamiento] |= 0x1
    ruta.write_bytes(bytes(crudo))
    with pytest.raises(ZipInseguro, match="cifrado"):
        with abrir_zip_seguro(ruta):
            pass


def test_rechaza_una_bomba_de_compresion(tmp_path):
    ruta = _zip(tmp_path / "bomba.zip", [(_info("ceros.dta"), b"\0" * (50 << 20))])
    with pytest.raises(ZipInseguro, match="proporción de compresión"):
        with abrir_zip_seguro(ruta):
            pass


def test_rechaza_miembros_y_totales_por_encima_del_tope(tmp_path):
    lim = Limites(max_miembro=1000, max_total=1500, proporcion_max=100, proporcion_desde=1 << 20, bloque=64)
    grande = _zip(tmp_path / "grande.zip", [(_info("a.dta"), b"x" * 1001)], zipfile.ZIP_STORED)
    with pytest.raises(ZipInseguro, match="descomprimido"):
        with abrir_zip_seguro(grande, lim):
            pass
    varios = _zip(tmp_path / "varios.zip", [(_info("a.dta"), b"x" * 800), (_info("b.dta"), b"x" * 800)],
                  zipfile.ZIP_STORED)
    with pytest.raises(ZipInseguro, match="pasa de"):
        with abrir_zip_seguro(varios, lim):
            pass


def test_rechaza_lo_que_no_es_zip(tmp_path):
    (tmp_path / "x.zip").write_bytes(b"no soy un zip")
    with pytest.raises(ZipInseguro, match="no es un ZIP"):
        with abrir_zip_seguro(tmp_path / "x.zip"):
            pass


def test_los_limites_vienen_del_yaml():
    lim = Limites.desde_yaml()
    assert lim.max_miembro >= 54 << 20 and lim.max_total >= 732 << 20 and lim.proporcion_max > 28.3


@pytest.mark.solo_mac
def test_los_zip_registrados_de_la_endes_se_leen_igual():
    """Los miembros de los ZIP de la ENDES 2024 (hogar y anemia) dan los mismos bytes que con `z.read()`."""
    from pap.capa0 import insumos
    from pap.config import Rutas

    rutas = Rutas(RAIZ_REAL)
    for recurso in ("endes-2024-hogar", "endes-2024-anemia"):
        ins = insumos.ultimo(rutas, "INEI-ENDES", recurso=recurso)
        with zipfile.ZipFile(ins.ruta) as z:
            esperado = {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith("/")}
        with abrir_zip_seguro(ins.ruta) as z:
            assert {n: hashlib.sha256(z.leer(n)).hexdigest() for n in z.miembros()} == esperado
