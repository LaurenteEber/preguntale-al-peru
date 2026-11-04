"""GA-05 (R-GASTO-05 v4): lista curada de la genérica 2.4 y su aplicación en DuckDB.

La usan gasto.py (construcción) y las pruebas (test_transferencias.py). Lista: curados/capa0/lista_transferencias.yaml.
Nada aquí depende de texto: la categoría sale del código exacto del clasificador y, en las excepciones, del código de
actividad (y del pliego, si se indica). Los nombres de actividad solo alimentan una alarma de revisión (G-18b).
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import yaml

CATEGORIAS = ("intergubernamental", "publico_fuera_de_base", "fondo_por_identificar", "gasto_final_externo")
# Transiciones que una excepción puede hacer sobre la categoría de su clasificador
TRANSICIONES = {("intergubernamental", "publico_fuera_de_base"),
                ("publico_fuera_de_base", "fondo_por_identificar")}
ESTADOS_EXCEPCION = {"aplicada", "pendiente_decision_dueno"}
# R-GASTO-05: fuera de toda cifra temática (igual que la marca 2.4.x.3 anterior)
EXCLUIDAS_TEMATICA = ("intergubernamental", "publico_fuera_de_base", "fondo_por_identificar")
BLOQUE = {"intergubernamental": "excluir_intergubernamental",
          "publico_fuera_de_base": "entregado_fuera_del_presupuesto",
          "fondo_por_identificar": "posible_doble_conteo_fondo",
          "gasto_final_externo": "gasto_final",
          "por_revisar": "por_revisar"}


class ListaInvalida(ValueError):
    pass


def cargar_lista(ruta: Path) -> dict:
    """Lee y valida el YAML. Devuelve {'clasificadores', 'excepciones' (todas, con estado), 'alarmas', 'version'}."""
    doc = yaml.safe_load(Path(ruta).read_text(encoding="utf-8")) or {}
    cl = pd.DataFrame(doc.get("clasificadores") or [])
    if cl.empty or not {"codigo", "nombre", "categoria", "motivo", "evidencia"} <= set(cl.columns):
        raise ListaInvalida("faltan clasificadores o columnas (codigo, nombre, categoria, motivo, evidencia)")
    if cl.codigo.duplicated().any():
        raise ListaInvalida(f"código repetido: {cl.codigo[cl.codigo.duplicated()].tolist()}")
    if not cl.codigo.astype(str).str.fullmatch(r"2\.4\.[12]\.\d\.\d+\.\d+").all():
        raise ListaInvalida("código fuera de la genérica 2.4 o mal formado")
    if not cl.categoria.isin([c for c in CATEGORIAS if c != "fondo_por_identificar"]).all():
        raise ListaInvalida("categoría desconocida (fondo_por_identificar solo vía excepción)")
    if not any(k.startswith("clasificador_") and "http" in str(v) for k, v in (doc.get("fuentes") or {}).items()):
        raise ListaInvalida("falta la URL del clasificador de gastos")
    base_cat = dict(zip(cl.codigo, cl.categoria))
    filas = []
    for e in doc.get("excepciones") or []:
        if e.get("estado") not in ESTADOS_EXCEPCION:
            raise ListaInvalida(f"{e.get('id')}: estado inválido")
        for comb in e["combinaciones"]:
            k = comb["clasificador"]
            if (base_cat.get(k), e["categoria"]) not in TRANSICIONES:
                raise ListaInvalida(f"{e['id']}: transición no permitida {base_cat.get(k)} → {e['categoria']} en {k}")
            if not re.fullmatch(r"\d{7}", str(comb["actividad_accion_obra"])):
                raise ListaInvalida(f"{e['id']}: la excepción usa el CÓDIGO de actividad, no texto")
            filas.append({"id": e["id"], "estado": e["estado"], "clasificador": k,
                          "nivel_gobierno": comb["nivel_gobierno"], "actividad_accion_obra": str(comb["actividad_accion_obra"]),
                          "pliego": comb.get("pliego"), "categoria": e["categoria"]})
    ex = pd.DataFrame(filas, columns=["id", "estado", "clasificador", "nivel_gobierno", "actividad_accion_obra",
                                      "pliego", "categoria"])
    if ex.duplicated(["clasificador", "nivel_gobierno", "actividad_accion_obra"]).any():
        raise ListaInvalida("dos excepciones sobre la misma combinación (duplicarían filas)")
    alarmas = [str(p).upper() for p in (doc.get("alarmas_revision") or {}).get("patrones_nombre", [])]
    return {"clasificadores": cl[["codigo", "categoria"]].astype(str), "excepciones": ex, "alarmas": alarmas,
            "version": str(doc.get("version"))}


def registrar(con, lista: dict, base_cruda: str = "base_cruda", destino: str = "base") -> None:
    """Crea tr_lista, tr_excep y la vista `destino` sobre `base_cruda` con las columnas de transferencia.
    Solo se aplican las excepciones con estado 'aplicada'; las pendientes quedan registradas para G-17b y G-18b."""
    con.register("tr_lista_df", lista["clasificadores"])
    con.register("tr_excep_df", lista["excepciones"])
    con.execute("CREATE OR REPLACE TABLE tr_lista AS SELECT * FROM tr_lista_df")
    con.execute("CREATE OR REPLACE TABLE tr_excep AS SELECT * FROM tr_excep_df")
    casos = " ".join(f"WHEN '{k}' THEN '{v}'" for k, v in BLOQUE.items())
    excl = ", ".join(f"'{c}'" for c in EXCLUIDAS_TEMATICA)
    con.execute(f"""
        CREATE OR REPLACE VIEW {destino} AS
        WITH c AS (
          SELECT b.* EXCLUDE (es_transferencia),
                 CASE WHEN b.generica = '4' THEN coalesce(e.categoria, l.categoria, 'por_revisar') END
                   AS categoria_transferencia,
                 e.id AS excepcion_transferencia
          FROM {base_cruda} b
          LEFT JOIN tr_lista l ON l.codigo = b.clasificador_transferencia
          LEFT JOIN tr_excep e ON e.estado = 'aplicada' AND e.clasificador = b.clasificador_transferencia
                              AND e.nivel_gobierno = b.nivel_gobierno AND e.actividad_accion_obra = b.actividad_accion_obra
                              AND (e.pliego IS NULL OR e.pliego = b.pliego)
        )
        SELECT *,
               coalesce(categoria_transferencia IN ({excl}), false) AS es_transferencia,
               coalesce(categoria_transferencia = 'intergubernamental', false) AS es_transferencia_intergub,
               CASE coalesce(categoria_transferencia, 'gasto_final_externo') {casos} END AS bloque_consolidado
        FROM c
    """)


def pruebas(con, lista: dict, prueba) -> None:
    """G-15, G-15b, G-17, G-17b, G-18 y G-18b sobre las vistas `base_cruda` y `base`. `prueba(id, desc, ok, det, bloq)`."""
    v = lista["version"]
    nuevas = con.execute("""SELECT anio, clasificador_transferencia, any_value(clasificador_transferencia_nombre),
                                   sum(pim)::DOUBLE, sum(devengado)::DOUBLE
                            FROM base WHERE categoria_transferencia = 'por_revisar' GROUP BY 1, 2
                            HAVING abs(sum(pim)) + abs(sum(devengado)) > 0""").fetchall()
    prueba("G-15", f"Toda específica de la genérica 2.4 está en lista_transferencias.yaml v{v}", not nuevas,
           [{"anio": a, "clasificador": k, "nombre": n, "pim": p, "devengado": d} for a, k, n, p, d in nuevas], True)
    fuera = con.execute("""SELECT count(*) FROM base WHERE generica <> '4'
                           AND (categoria_transferencia IS NOT NULL OR es_transferencia)""").fetchone()[0]
    prueba("G-15b", "Ninguna fila fuera de la genérica 2.4 lleva categoría de transferencia", fuera == 0, {"filas": fuera}, True)
    cons = con.execute("""
        SELECT c.anio, c.n = b.n AND c.dev = b.dev AND b.dev = b.dev_bloques, b.n, b.dev FROM
          (SELECT anio, count(*) n, sum(devengado) dev FROM base_cruda GROUP BY anio) c JOIN
          (SELECT anio, count(*) n, sum(devengado) dev,
                  sum(devengado) FILTER (WHERE bloque_consolidado IS NOT NULL) dev_bloques
           FROM base GROUP BY anio) b USING (anio) ORDER BY 1""").fetchall()
    prueba("G-17", "Conservación: la lista no duplica ni pierde filas ni soles; cada fila tiene un bloque (tolerancia 0)",
           all(ok for _, ok, _, _ in cons), {str(a): {"filas": int(n), "devengado": str(d)} for a, _, n, d in cons}, True)
    sin_uso = con.execute("""SELECT e.id, e.clasificador, e.nivel_gobierno, e.actividad_accion_obra, e.pliego FROM tr_excep e
                             WHERE NOT EXISTS (SELECT 1 FROM base_cruda b WHERE b.clasificador_transferencia = e.clasificador
                               AND b.nivel_gobierno = e.nivel_gobierno AND b.actividad_accion_obra = e.actividad_accion_obra
                               AND (e.pliego IS NULL OR e.pliego = b.pliego))""").df()
    prueba("G-17b", "Revisión: toda combinación de excepción tiene filas en la base (si no, cambió el código de actividad)",
           sin_uso.empty, sin_uso.to_dict("records"), False)
    coh = con.execute("""
        WITH o AS (SELECT anio, CASE right(clasificador_transferencia, 1) WHEN '1' THEN 'E' WHEN '2' THEN 'R'
                                     WHEN '3' THEN 'M' END AS destino, sum(devengado) AS otorgado
                   FROM base WHERE categoria_transferencia = 'intergubernamental' GROUP BY 1, 2),
             r AS (SELECT anio, nivel_gobierno AS destino, sum(pim) AS pim_f4 FROM base_cruda
                   WHERE fuente_financiamiento = '4' GROUP BY 1, 2)
        SELECT o.anio, o.destino, o.otorgado::DOUBLE, r.pim_f4::DOUBLE FROM o LEFT JOIN r USING (anio, destino)
        ORDER BY 1, 2""").fetchall()
    prueba("G-18", "Revisión: transferencias intergubernamentales ≤ PIM fuente 4 del nivel receptor",
           all(p is not None and o <= p for _, _, o, p in coh),
           [{"anio": a, "destino": d, "otorgado": round(o / 1e6, 1), "pim_f4": round((p or 0) / 1e6, 1)}
            for a, d, o, p in coh], False)
    if lista["alarmas"]:
        cond = " OR ".join(f"upper(actividad_accion_obra_nombre) LIKE '%{p}%'" for p in lista["alarmas"])
        alarma = con.execute(f"""SELECT anio, clasificador_transferencia, nivel_gobierno, actividad_accion_obra,
                                        any_value(actividad_accion_obra_nombre) AS actividad, count(DISTINCT sec_ejec) AS ejecutoras,
                                        round(sum(devengado)/1e6, 2) AS devengado_millones
                                 FROM base WHERE categoria_transferencia = 'intergubernamental' AND ({cond})
                                 GROUP BY 1, 2, 3, 4 HAVING sum(devengado) <> 0 ORDER BY 1, 7 DESC""").df()
        prueba("G-18b", "Revisión: filas intergubernamentales cuyo nombre de actividad sugiere un receptor fuera de la base "
               "(centros poblados, caminos vecinales, IVP, beneficencias). Solo avisa; no clasifica",
               alarma.empty, alarma.to_dict("records"), False)
