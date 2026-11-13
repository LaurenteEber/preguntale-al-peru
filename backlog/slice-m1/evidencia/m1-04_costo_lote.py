"""M1-04, §0.4: costo máximo del lote completo, SIN llamar a la API ni leer ninguna clave. Reutiliza `peticiones_vincular`,
`peticiones_verificar` y `costo_maximo_usd` de `cuestionarios_lote.py`. Uso: `uv run python backlog/slice-m1/evidencia/m1-04_costo_lote.py`.

Pendientes = variables de los diccionarios sin vínculo en `vinculos.parquet` (regla, diccionario o sin pregunta administrativa/construida)
y sin vínculo manual (`vinculos_manuales.yaml`). Pasada 2 en el peor caso: a cada variable se le verifica la candidata de texto más largo."""
from pathlib import Path

import polars as pl

from pap.config import Rutas
from pap.inferencia import cuestionarios as c
from pap.inferencia import cuestionarios_lote as lote

if __name__ == "__main__":
    raiz = Path(__file__).resolve().parents[3]
    R = Rutas(raiz)
    d = c.carpeta_cuestionarios(R)
    qs = c.leer_cuestionarios(d)
    vs, cu = c.leer_diccionarios(d)
    pl_ = lote.ParametrosLote.desde_yaml()
    hechos = {(f["tabla"], f["codigo"]) for f in pl.read_parquet(d / "vinculos.parquet").iter_rows(named=True)}
    manuales = {(v.tabla, v.codigo) for v in c.leer_vinculos_manuales(raiz / c.RUTA_VINCULOS_MANUALES)}
    ya_llm = {(f["tabla"], f["codigo"]) for f in pl.read_parquet(d / "vinculos_llm.parquet").iter_rows(named=True)}
    pend = [v for v in vs if (v.tabla, v.codigo) not in hechos and (v.tabla, v.codigo) not in manuales]
    print(f"pendientes (sin regla/diccionario/administrativa/construida ni manual): {len(pend)}; manuales excluidas: "
          f"{len(manuales & {(v.tabla, v.codigo) for v in vs} - hechos)}; ya pasaron por el LLM (RECH6, REC43, REC0111): "
          f"{len([v for v in pend if (v.tabla, v.codigo) in ya_llm])}")
    cand = c.Candidatos(qs)
    por_id = {q.id: q for q in qs}
    for titulo, vars_ in (("todas las pendientes", pend), ("sin las que ya pasaron por el LLM", [v for v in pend if (v.tabla, v.codigo) not in ya_llm])):
        pet1, mapa = lote.peticiones_vincular(vars_, cand, cu, pl_)
        propuestas = {}
        for m in mapa.values():
            ids = list(m["candidatas"].values())
            propuestas[(m["tabla"], m["codigo"])] = max(ids, key=lambda i: len(por_id[i].texto) + sum(len(o) for o in por_id[i].opciones))
        pet2, _ = lote.peticiones_verificar(propuestas, {(v.tabla, v.codigo): v for v in vars_}, por_id, pl_)
        m1, m2 = lote.costo_maximo_usd(pet1, pl_), lote.costo_maximo_usd(pet2, pl_)
        print(f"\n{titulo}: {len(vars_)} variables; pasada 1: {len(pet1)} peticiones, máx US$ {m1:.2f}; pasada 2 (peor caso): {len(pet2)} peticiones, "
              f"máx US$ {m2:.2f}; total máx US$ {m1 + m2:.2f}; tope por lote US$ {pl_.tope_lote_usd:g} "
              f"({'ambos lotes bajo el tope' if max(m1, m2) <= pl_.tope_lote_usd else 'UN LOTE PASA EL TOPE'})")
