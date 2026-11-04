"""Verificar: recetas contra su esquema, capturas contra Frictionless y el contrato, y crudos contra su huella.

Los crudos guardados como `<huella>.zst` se verifican descomprimiendo en flujo (huella y tamaño del original); con
--rapido, contra el tamaño original anotado en la cabecera zstd."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import almacen, bitacora, capturas, recetas
from .config import Rutas


@dataclass
class Informe:
    problemas: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    recetas: int = 0
    paquetes: int = 0
    recursos: int = 0

    @property
    def ok(self) -> bool:
        return not self.problemas


def verificar(rutas: Rutas, source_id: str | None = None, completo: bool = True, anotar: bool = True) -> Informe:
    inf = Informe()

    for ruta in recetas.listar(rutas):
        if source_id and ruta.stem != source_id:
            continue
        inf.recetas += 1
        try:
            errs = recetas.errores(recetas.leer(ruta), ruta)
        except Exception as e:  # noqa: BLE001  (YAML ilegible)
            errs = [f"no se pudo leer: {e}"]
        inf.problemas += [f"receta {ruta.stem}: {e}" for e in errs]

    referenciados: set[str] = set()
    for ruta, paq in capturas.iterar(rutas):
        recs = paq.get("resources", [])
        for rec in recs:
            for ev in rec.get("manual_evidence") or []:
                referenciados.add(ev["hash"].removeprefix("sha256:"))
            referenciados.add(str(rec.get("hash", "")).removeprefix("sha256:"))
        if source_id and not any(r.get("source_id") == source_id for r in recs):
            continue
        inf.paquetes += 1
        donde = rutas.relativa(ruta)
        inf.problemas += [f"{donde}: {e}" for e in capturas.errores_paquete(paq)]
        for rec in recs:
            inf.recursos += 1
            h = str(rec.get("hash", "")).removeprefix("sha256:")
            probs = almacen.comprobar(rutas, h, rec.get("bytes"), completo=completo)
            for ev in rec.get("manual_evidence") or []:
                probs += [f"evidencia {ev['original_filename']}: {p}" for p in
                          almacen.comprobar(rutas, ev["hash"].removeprefix("sha256:"), None, completo=completo)]
            inf.problemas += [f"{donde} [{rec.get('name')}]: {p}" for p in probs]
            if anotar:
                bitacora.anotar(rutas, rec.get("source_id"), "verificar", "fallo" if probs else "ok",
                                hash=rec.get("hash"), captura=rutas.relativa(ruta.parent),
                                detalle="; ".join(probs) or ("huella verificada" if completo else "tamaño verificado"))

    if not source_id:
        huerfanos = [h for h in almacen.objetos(rutas) if h not in referenciados]
        inf.avisos += [f"objeto sin captura en el almacén: {h[:12]}…" for h in huerfanos]
        inf.avisos += [f"objeto con original y .zst a la vez (compresión interrumpida; termina con "
                       f"`pap almacen comprimir`): {h[:12]}…" for h in almacen.duplicados(rutas)]
        inf.avisos += [f"temporal de una operación interrumpida: {rutas.relativa(t)}" for t in almacen.temporales(rutas)]
    return inf
