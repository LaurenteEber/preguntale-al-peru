"""Proveedor falso de la Batch API para las pruebas de M1-04: un «servidor» en memoria que comparten todas las instancias (como el
servicio real: sigue vivo aunque el proceso muera) y puntos de corte para probar la reanudación."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from pap.inferencia.cuestionarios_lote import Peticion, ResultadoPeticion


class Interrumpido(Exception):
    """Simula que el proceso murió justo ahí."""


@dataclass
class ServidorFalso:
    responder: object                                   # (Peticion) -> texto de la respuesta del modelo
    lotes: dict = field(default_factory=dict)           # batch_id -> lista de Peticion
    creados: int = 0
    borrados: list = field(default_factory=list)
    consultas_de_estado: int = 0
    en_proceso_antes_de_terminar: int = 0               # cuántas consultas devuelven «en_proceso» antes de «terminado»
    tokens_entrada: int = 1000
    tokens_salida: int = 20
    falla_borrado: bool = False

    @property
    def vivos(self) -> int:
        return len(self.lotes)


@dataclass
class ProveedorFalso:
    servidor: ServidorFalso
    corta_tras_crear: bool = False                      # el proceso muere justo después de crear el lote
    corta_en_estado: bool = False                       # muere en la primera consulta de estado
    corta_tras_n_resultados: int | None = None          # muere mientras baja los resultados

    def crear_lote(self, peticiones: list[Peticion]) -> str:
        s = self.servidor
        s.creados += 1
        bid = f"msgbatch_falso_{s.creados:03d}"
        s.lotes[bid] = list(peticiones)
        if self.corta_tras_crear:
            raise Interrumpido("murió tras crear el lote, antes de guardar el batch_id")
        return bid

    def estado(self, batch_id: str) -> str:
        s = self.servidor
        s.consultas_de_estado += 1
        if self.corta_en_estado:
            raise Interrumpido("murió al consultar el estado")
        if s.consultas_de_estado <= s.en_proceso_antes_de_terminar:
            return "en_proceso"
        return "terminado"

    def resultados(self, batch_id: str):
        for i, p in enumerate(self.servidor.lotes[batch_id]):
            if self.corta_tras_n_resultados is not None and i >= self.corta_tras_n_resultados:
                raise Interrumpido("murió bajando resultados")
            yield ResultadoPeticion(p.custom_id, self.servidor.responder(p), None, self.servidor.tokens_entrada, self.servidor.tokens_salida)

    def borrar(self, batch_id: str) -> None:
        if self.servidor.falla_borrado:
            raise OSError("no se pudo borrar")
        self.servidor.borrados.append(batch_id)
        self.servidor.lotes.pop(batch_id, None)


def responder_con(reglas: dict):
    """`reglas`: {fragmento_del_usuario: texto_de_respuesta}; la primera que aparezca en el texto de la petición."""
    def f(p: Peticion) -> str:
        for frag, texto in reglas.items():
            if frag in p.usuario:
                return texto if isinstance(texto, str) else json.dumps(texto)
        return json.dumps({"id": "ninguna"}) if p.custom_id.startswith("vin") else json.dumps({"coincide": False})
    return f
