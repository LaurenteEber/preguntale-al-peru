"""Acciones de `pap cuestionarios` (M1-04): extraer | vincular | medir | informe | lote | aplicar. La lógica está en `cuestionarios.py`,
`cuestionarios_medicion.py` y `cuestionarios_lote.py`; aquí solo se juntan las piezas. Sin red salvo `lote`."""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from ..errores import PapError
from . import cuestionarios as c
from . import cuestionarios_medicion as m


def _cargar(rutas):
    d = c.carpeta_cuestionarios(rutas)
    qs = c.leer_cuestionarios(d)
    vs, cuests = c.leer_diccionarios(d)
    return d, qs, vs, cuests


def _indice_variables(rutas) -> dict[str, set[str]]:
    import polars as pl

    ruta = rutas.raiz / "biblioteca" / "variables" / "variables.parquet"
    if not ruta.exists():
        raise PapError("Falta biblioteca/variables/variables.parquet: corre antes `pap variables indexar --encuesta ENDES --anio 2024`")
    out: dict[str, set[str]] = {}
    for a, v in pl.read_parquet(ruta, columns=["archivo", "variable"]).iter_rows():
        out.setdefault(a, set()).add(v)
    return out


def _vinculos_previos(d: Path, nombre: str):
    import polars as pl

    ruta = d / nombre
    return pl.read_parquet(ruta) if ruta.exists() else None


def _a_vinculos(df) -> list[c.Vinculo]:
    return [c.Vinculo(f["tabla"], f["codigo"], f["pregunta_id"], f["metodo"], f["estado"], f["motivo"], f["evidencia"])
            for f in df.iter_rows(named=True)]


def _manuales(rutas, vs) -> list[c.Vinculo]:
    """Vínculos fijados a mano por el dueño; la variable debe existir en los diccionarios."""
    out = c.leer_vinculos_manuales(rutas.raiz / c.RUTA_VINCULOS_MANUALES)
    existen = {(v.tabla, v.codigo) for v in vs}
    for v in out:
        if (v.tabla, v.codigo) not in existen:
            raise PapError(f"vinculos_manuales.yaml: {v.tabla}.{v.codigo} no está en los diccionarios")
    return out


def _manual(a, rutas) -> int:
    from .almacen import _insumo

    numeros = [n.strip().upper() for n in (a.preguntas or "").split(",") if n.strip()]
    if not numeros:
        raise PapError("manual: indica los números de pregunta con --preguntas 412,454")
    ins = _insumo(rutas, "INEI-ENDES", "endes-2024-manual-entrevistadora")
    for n, frs in c.fragmentos_del_manual(c.leer_pdf(ins.ruta, c.Parametros.desde_yaml()), numeros).items():
        print(f"pregunta {n}: " + ("sin fragmentos" if not frs else ""))
        for f in frs:
            print(f"  p. {f['pagina']}: …{f['texto']}…")
    return 0


def ejecutar(a, rutas) -> int:
    d = c.carpeta_cuestionarios(rutas)
    if a.accion == "manual":
        return _manual(a, rutas)
    if a.accion == "extraer":
        qs = c.extraer_cuestionarios(rutas)
        vs, cuests = c.extraer_diccionarios(rutas)
        c.guardar_cuestionarios(qs, d)
        c.guardar_diccionarios(vs, cuests, d)
        print(f"\n{sum(len(x) for x in qs.values())} preguntas y {len(vs)} variables de diccionario en {rutas.relativa(d)} (propuesto).")
        return 0
    _, qs, vs, cuests = _cargar(rutas)
    if a.accion == "vincular":
        vin = c.vincular_sin_llm(vs, qs, cuests)
        c._escribir_parquet(c.tabla_de_vinculos(vin, qs), d / "vinculos.parquet")
        n = {k: sum(1 for v in vin if v.metodo == k) for k in ("regla", "diccionario", "sin_pregunta")}
        print(f"{len(vin)} variables resueltas sin LLM (regla {n['regla']}, diccionario {n['diccionario']}, sin pregunta {n['sin_pregunta']}) "
              f"de {len(vs)}; {len(vs) - len(vin)} esperan al lote.")
        return 0
    if a.accion in ("medir", "informe"):
        vin = {(v.tabla, v.codigo): v for v in c.vincular_sin_llm(vs, qs, cuests)}
        solo = m.variables_de_recetas(rutas.raiz, vs)
        f3, fr, ft = m.medir(vs, vin, list(m.TABLAS_DE_LA_MEDICION)), m.medir(vs, vin, solo=solo), m.medir(vs, vin)
        recall = m.recall_de_candidatos(vs, vin, c.Candidatos(qs), cuests, m.k_candidatos())
        if a.accion == "medir":
            for f in f3:
                print(f"{f.tabla}: {f.total} variables; diccionario {f.por_diccionario}, regla {f.por_regla} ({f.pct_sin_llm} %), "
                      f"sin pregunta {f.sin_pregunta_administrativa + f.sin_pregunta_construida}, para el LLM {f.pendientes}")
            return 0
        hoy = date.today().isoformat()
        ev = rutas.raiz / "backlog" / "slice-m1" / "evidencia"
        (ev / "m1-04_cuestionarios.md").write_text(m.informe_cuestionarios(qs, vs, _indice_variables(rutas), hoy), encoding="utf-8")
        (ev / "m1-04_vinculos.md").write_text(m.informe_vinculos(f3, fr, ft, recall, solo, hoy), encoding="utf-8")
        print(f"Escribí {rutas.relativa(ev / 'm1-04_cuestionarios.md')} y {rutas.relativa(ev / 'm1-04_vinculos.md')}.")
        return 0
    if a.accion == "lote":
        from ..interprete.llm import ClienteLote
        from .cuestionarios_lote import ParametrosLote, vincular_con_llm

        pl = ParametrosLote.desde_yaml()
        if not os.environ.get(pl.variable_clave):          # solo se comprueba que exista; el valor no se lee ni se muestra
            raise PapError(f"No hay clave para la Batch API: falta la variable de entorno {pl.variable_clave} (clave y Workspace aparte, "
                           "condición 1 de backlog/slice-m1/evidencia/auditoria_batch_api.md). No se llamó a nada.")
        previos = _vinculos_previos(d, "vinculos.parquet")
        hechos = {(v.tabla, v.codigo) for v in _a_vinculos(previos)} if previos is not None else set()
        hechos |= {(v.tabla, v.codigo) for v in _manuales(rutas, vs)}          # los fijados a mano no van al modelo
        tablas = set(a.tablas.split(",")) if a.tablas else None
        pendientes = [v for v in vs if (v.tabla, v.codigo) not in hechos and (tablas is None or v.tabla in tablas)]
        if a.max_variables:
            pendientes = pendientes[:a.max_variables]
        print(f"{len(pendientes)} variables al lote (tope US$ {pl.tope_lote_usd:g}).")
        vin = vincular_con_llm(pendientes, qs, cuests, ClienteLote(rutas.raiz), d / "lote", pl)
        c._escribir_parquet(c.tabla_de_vinculos(vin, qs), d / "vinculos_llm.parquet")
        print(f"{sum(1 for v in vin if v.metodo == 'llm')} vinculadas por el LLM de {len(vin)}; lotes borrados en el servicio.")
        return 0
    if a.accion == "aplicar":
        import polars as pl

        from . import indice

        sin_llm = _vinculos_previos(d, "vinculos.parquet")
        if sin_llm is None:
            raise PapError("Falta vinculos.parquet: corre antes `pap cuestionarios vincular`")
        llm = _vinculos_previos(d, "vinculos_llm.parquet")
        todos = pl.concat([sin_llm] + ([llm] if llm is not None else []))
        manuales = _manuales(rutas, vs)
        if manuales:                                                           # mandan sobre la regla y el LLM (método `manual`)
            quita = [c.var_id(v.tabla, v.codigo) for v in manuales]
            todos = pl.concat([todos.filter(~pl.col("var_id").is_in(quita)), c.tabla_de_vinculos(manuales, qs)])
        ruta_ind = rutas.raiz / "biblioteca" / "variables" / "variables.parquet"
        df = indice.aplicar_vinculos(pl.read_parquet(ruta_ind), todos)
        destino = ruta_ind if a.sobre_indice else d / "variables_con_pregunta.parquet"
        c._escribir_parquet(df, destino)
        print(f"{df['texto_pregunta'].is_not_null().sum()} variables con texto de pregunta (propuesto) en {rutas.relativa(destino)}.")
        return 0
    raise PapError(f"acción desconocida: {a.accion}")
