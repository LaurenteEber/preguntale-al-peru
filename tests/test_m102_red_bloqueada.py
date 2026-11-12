"""M1-02, tarea 10 (H00b-3): las pruebas no salen a internet. Comprueba que `pytest-socket` está activo, no solo que está instalado.
Lo que NO cubre (anotado en la evidencia): las consultas DNS (`getaddrinfo`) y los subprocesos, que no pasan por `socket.connect` de Python."""
import socket

import pytest
from pytest_socket import SocketConnectBlockedError


def test_un_socket_a_un_host_externo_esta_bloqueado():
    with pytest.raises(SocketConnectBlockedError):
        socket.create_connection(("93.184.216.34", 80), timeout=1)


def test_un_socket_nuevo_de_red_esta_bloqueado_pero_el_bucle_local_y_unix_estan_permitidos():
    with pytest.raises(SocketConnectBlockedError):
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
    with socket.socket(socket.AF_UNIX) as s:                      # --allow-unix-socket
        assert s.fileno() >= 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:   # bucle local: permitido (no hay quien escuche, pero no es SocketConnectBlockedError)
        with pytest.raises(ConnectionRefusedError):
            s.connect(("127.0.0.1", 9))
