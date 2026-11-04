"""Guardia del motor para el gasto (R-GASTO-05 v4, GA-05; ronda 3, 7/10/2026). Pendiente: conectarla al ejecutor
SQL del motor. Toda consulta de gasto pasa por `verificar_consulta(sql)` antes de ejecutarse.

Reglas (las tres rechazan con GuardiaGasto):
  G1. Leer fact_gasto_territorial o gasto_base_* directamente solo se permite para UNA entidad: cada SELECT que los lea
      debe tener, como conjunción de primer nivel del WHERE, `sec_ejec = <constante>` o `pliego = <constante>`.
      Todo lo demás (temas, territorios, consolidados) va por v_gasto_tematico o v_gasto_consolidado.
  G2. Ninguna consulta puede leer a la vez columnas del gasto final y de lo entregado fuera del presupuesto, en
      ningún nivel (expresión, alias, subconsulta, CTE, UNION, UNPIVOT o SELECT * sobre v_gasto_consolidado). El
      motor pide cada línea del consolidado en una consulta aparte (auditoría final de la ronda 3, hallazgo 1).
  G3. v_gasto_fondos_por_identificar no se agrega junto con otra vista de gasto en la misma consulta.
  G4. (pieza C, R-GASTO-08b: los alcances no se suman entre sí; rediseño tras la auditoría, H1) El gasto por tema solo
      se lee con la macro gasto_tema('<tema_id>'): como mucho UNA llamada por consulta, con un argumento constante o
      parámetro (una llamada = un tema; no hay autojoin ni producto que junte dos temas). v_gasto_tema_interna (todos
      los temas) no se lee nunca. gasto_tema() y v_gasto_concepto no se combinan con otra vista de gasto ni entre sí, y
      ninguna consulta que lea gasto puede leer las tablas que definen los temas (dim_tema_gasto, rel_concepto_grupo,
      rel_concepto_nodo, rel_programa_social_ejecutora): con ellas se podría rearmar la unión de alcances. Es una
      regla de nombres sobre el árbol del parser, no de filtros: no depende de alias ni de dónde está el WHERE.
  G5. (verificación de la pieza C, H1b) Solo se admiten las funciones de tabla de FUNCIONES_TABLA (gasto_tema y las
      generadoras sin acceso a datos) y read_parquet/read_csv/parquet_scan sobre el fact o la base (regidas por G1).
      Se rechazan query(), query_table(), glob(), read_* de cualquier otro archivo y toda tabla nombrada por una ruta
      ('…/x.parquet') que no sea el fact o la base: con ellas se leería por texto la vista interna o las tablas que
      definen los temas, saltando G4.
  G6. (E3, 8/10/2026) v_programa_social_linea_aparte (p. ej. lo transferido a municipalidades por Llamkasun) se muestra
      siempre aparte: no se lee junto con otra vista de gasto, con gasto_tema() ni con el fact en la misma consulta.
  G7. (auditoría de P3, H-P3-2) Una consulta sobre las vistas de gasto o gasto_tema() que filtra el departamento 15 o 07
      (departamento_atribucion, departamento_meta o ubigeo_atribucion con un texto que empieza por '15' o '07', o con
      'A-' de un ámbito de Lima) debe usar ambito_gasto o cuenta_en_ambito (o cuenta_en_lima en el 15): sin ellos
      sumaría la sede nacional (Marina, ministerios) a Lima o al Callao (H-A4).
Usa el parser de DuckDB (json_serialize_sql), no expresiones regulares sobre el texto.
Límite conocido: no inspecciona SQL dinámico ni macros; el motor no debe usarlos para el gasto.
"""
from __future__ import annotations

import json

import duckdb

TABLAS_CRUDAS = ("fact_gasto_territorial", "gasto_base_")
COLS_GASTO_FINAL = {"gasto_final_devengado", "gasto_final_pim"}
COLS_ENTREGADO = {"entregado_fuera_del_presupuesto_devengado", "entregado_fuera_del_presupuesto_pim"}
FILTROS_UNA_ENTIDAD = {"sec_ejec", "pliego"}
MACRO_TEMA = "gasto_tema"
VISTAS_PROHIBIDAS = {"v_gasto_tema_interna", "v_gasto_tema"}   # la segunda: nombre anterior a la corrección H1
VISTAS_ALCANCE = {"v_gasto_concepto"}
# P3 (9/10/2026): v_gasto_por_ambito (LM, LR, Callao y líneas aparte) es una vista de gasto más: G3, G4 y G6 la cubren.
# La guardia no supone Lima = 15: las cifras por ámbito se leen por ambito_gasto / cuenta_en_ambito (15 y 07).
VISTAS_GASTO = {"v_gasto_tematico", "v_gasto_consolidado", "v_gasto_fondos_por_identificar",
                "v_gasto_por_ambito"} | VISTAS_ALCANCE
FUNCIONES_TABLA = {"gasto_tema", "range", "generate_series", "unnest"}
LECTORES_ARCHIVO = {"read_parquet", "parquet_scan", "read_csv", "read_csv_auto"}
TABLAS_DEFINICION_TEMAS = {"dim_tema_gasto", "rel_concepto_grupo", "rel_concepto_nodo", "rel_programa_social_ejecutora",
                           "rel_programa_social_linea_aparte"}
VISTAS_LINEA_APARTE = {"v_programa_social_linea_aparte"}   # G6 (E3)
COLS_TERRITORIO = {"departamento_atribucion", "departamento_meta", "ubigeo_atribucion"}   # G7 (P3)
COLS_FILTRO_AMBITO = {"ambito_gasto", "cuenta_en_ambito", "cuenta_en_lima"}


class GuardiaGasto(ValueError):
    """Consulta rechazada por R-GASTO-05."""


def _ast(sql: str) -> dict:
    out = json.loads(duckdb.execute("SELECT json_serialize_sql(?)", [sql]).fetchone()[0])
    if out.get("error"):
        raise GuardiaGasto(f"SQL no analizable: {out.get('error_message')}")
    return out


def _nodos(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from _nodos(v)
    elif isinstance(x, list):
        for v in x:
            yield from _nodos(v)


def _columnas(x) -> set[str]:
    return {n["column_names"][-1].lower() for n in _nodos(x) if n.get("class") == "COLUMN_REF"}


def _lee_cruda(from_table) -> bool:
    """¿El FROM (incluidos joins y read_parquet('...')) lee el fact o la base, sin pasar por una subconsulta?"""
    if not isinstance(from_table, dict):
        return False
    t = from_table.get("type")
    if t == "BASE_TABLE":
        # nombre de tabla o ruta de archivo leída por reemplazo (FROM '…/gasto_base_2025.parquet')
        nombre = str(from_table.get("table_name", "")).lower().replace("\\", "/").rsplit("/", 1)[-1]
        return any(nombre.startswith(p) for p in TABLAS_CRUDAS)
    if t == "TABLE_FUNCTION":
        textos = [str(n.get("value", {}).get("value", "")) for n in _nodos(from_table.get("function"))
                  if n.get("class") == "CONSTANT" and isinstance(n.get("value"), dict)]
        return any(p in s for s in textos for p in TABLAS_CRUDAS)
    if t == "JOIN":
        return _lee_cruda(from_table.get("left")) or _lee_cruda(from_table.get("right"))
    return False  # SUBQUERY: su propio SELECT_NODE se revisa aparte


def _filtra_una_entidad(where) -> bool:
    if not where:
        return False
    conj = where["children"] if where.get("type") == "CONJUNCTION_AND" else [where]
    for c in conj:
        if c.get("type") == "COMPARE_EQUAL":
            lados = [c.get("left", {}), c.get("right", {})]
            cols = [l["column_names"][-1].lower() for l in lados if l.get("class") == "COLUMN_REF"]
            const = [l for l in lados if l.get("class") == "CONSTANT"]
            if cols and cols[0] in FILTROS_UNA_ENTIDAD and const:
                return True
    return False


def _rama_cols(node) -> list[set[str]]:
    """Columnas de cada posición del select_list de una rama de UNION."""
    if node.get("type") == "SELECT_NODE":
        return [_columnas(e) for e in node.get("select_list", [])]
    if node.get("type") == "SET_OPERATION_NODE":
        return _rama_cols(node["left"])
    return []


def verificar_consulta(sql: str) -> None:
    """Lanza GuardiaGasto si la consulta viola R-GASTO-05; si no, devuelve None."""
    arbol = _ast(sql)
    nodos = list(_nodos(arbol))
    # G1
    for n in nodos:
        if n.get("type") == "SELECT_NODE" and _lee_cruda(n.get("from_table")) and not _filtra_una_entidad(n.get("where_clause")):
            raise GuardiaGasto("R-GASTO-05: el fact o la base solo se leen para una entidad (WHERE sec_ejec = … o pliego = …). "
                               "Use v_gasto_tematico o v_gasto_consolidado.")
    # G2: misma columna de un UNION, o UNPIVOT que las junte (mensajes específicos; la regla general va después)
    for n in nodos:
        if n.get("type") == "SET_OPERATION_NODE":
            izq, der = _rama_cols(n["left"]), _rama_cols(n["right"])
            for a, b in zip(izq, der):
                u = a | b
                if u & COLS_GASTO_FINAL and u & COLS_ENTREGADO:
                    raise GuardiaGasto("R-GASTO-05: UNION que pone en la misma columna el gasto final y lo entregado "
                                       "fuera del presupuesto.")
        if n.get("type") == "PIVOT":
            # en UNPIVOT, las columnas van como textos en pivots[].entries[].values[]
            cols = _columnas(n) | {str(v.get("value", "")).lower() for p in n.get("pivots", [])
                                   for e in p.get("entries", []) for v in e.get("values", []) if isinstance(v, dict)}
            if cols & COLS_GASTO_FINAL and cols & COLS_ENTREGADO:
                raise GuardiaGasto("R-GASTO-05: UNPIVOT que junta el gasto final y lo entregado fuera del presupuesto.")
    # G2 (auditoría final de la ronda 3): una consulta no puede leer a la vez columnas de los dos grupos, en ningún
    # nivel (expresión, alias, subconsulta o CTE): seguir alias es frágil, así que se prohíbe la lectura conjunta. El
    # motor consulta cada línea del consolidado por separado. SELECT * sobre v_gasto_consolidado lee las dos.
    cols = _columnas(arbol)
    tablas_g2 = {str(n.get("table_name", "")).lower() for n in nodos if n.get("type") == "BASE_TABLE"}
    estrella = any(n.get("class") == "STAR" or n.get("type") == "STAR" for n in nodos)
    if (cols & COLS_GASTO_FINAL and cols & COLS_ENTREGADO) or (estrella and "v_gasto_consolidado" in tablas_g2):
        raise GuardiaGasto("R-GASTO-05: una consulta no lee a la vez el gasto final y lo entregado fuera del "
                           "presupuesto (ni con alias, subconsultas o *); se consultan y muestran en líneas separadas.")
    # G3
    tablas = {str(n.get("table_name", "")).lower() for n in nodos if n.get("type") == "BASE_TABLE"}
    if "v_gasto_fondos_por_identificar" in tablas and tablas & {"v_gasto_tematico", "v_gasto_consolidado",
                                                                  "v_gasto_por_ambito"}:
        raise GuardiaGasto("R-GASTO-05: los fondos por identificar no se combinan con el gasto en una misma consulta.")
    # G5 (H1b): funciones de tabla y rutas. Va antes de G4 porque esconden nombres en textos.
    for n in nodos:
        if n.get("type") == "TABLE_FUNCTION":
            fn = str((n.get("function") or {}).get("function_name", "")).lower()
            if fn in FUNCIONES_TABLA:
                continue
            textos = [str(x.get("value", {}).get("value", "")) for x in _nodos(n.get("function"))
                      if x.get("class") == "CONSTANT" and isinstance(x.get("value"), dict)
                      and isinstance(x["value"].get("value"), str)]
            rutas = [t.replace("\\", "/").rsplit("/", 1)[-1].lower() for t in textos if "/" in t or "." in t]
            if fn in LECTORES_ARCHIVO and rutas and all(r.startswith(TABLAS_CRUDAS) for r in rutas):
                continue  # solo el fact o la base por archivo: G1 ya exigió una sola entidad
            raise GuardiaGasto(f"R-GASTO-08b: función de tabla no permitida en consultas de gasto: {fn}() "
                               "(query, query_table, glob o archivos que no son el fact ni la base).")
        if n.get("type") == "BASE_TABLE":
            nombre = str(n.get("table_name", "")).lower()
            if any(x in nombre for x in ("/", "\\", ".parquet", ".csv", ".json")) and not _lee_cruda(n):
                raise GuardiaGasto("R-GASTO-08b: no se leen tablas por su ruta de archivo; use las vistas o gasto_tema().")
    # G4 (pieza C, H1): acceso por tema solo con gasto_tema('<tema>'), una vez; alcances y definiciones no se mezclan
    if tablas & VISTAS_PROHIBIDAS:
        raise GuardiaGasto("R-GASTO-08b: v_gasto_tema_interna es de uso interno; el gasto por tema se lee con "
                           "gasto_tema('<tema_id>').")
    llamadas = [n for n in nodos if n.get("type") == "TABLE_FUNCTION"
                and str((n.get("function") or {}).get("function_name", "")).lower() == MACRO_TEMA]
    if len(llamadas) > 1:
        raise GuardiaGasto("R-GASTO-08b: una sola llamada a gasto_tema() por consulta (un tema por consulta; los temas "
                           "y alcances no se suman entre sí).")
    for n in llamadas:
        args = n["function"].get("children", [])
        if len(args) != 1 or args[0].get("class") not in ("CONSTANT", "PARAMETER"):
            raise GuardiaGasto("R-GASTO-08b: gasto_tema() recibe un tema_id constante o como parámetro.")
    usa_alcance = bool(llamadas) or bool(tablas & VISTAS_ALCANCE)
    if usa_alcance and (len(tablas & VISTAS_GASTO) + bool(llamadas)) > 1:
        raise GuardiaGasto("R-GASTO-08b: gasto_tema() y v_gasto_concepto no se combinan con otra vista de gasto en la "
                           "misma consulta (cadenas distintas no se suman, restan ni comparan en una cuenta).")
    # G6 (E3): la línea aparte de los programas sociales nunca se combina con el gasto en una misma consulta
    if tablas & VISTAS_LINEA_APARTE and (llamadas or tablas & (VISTAS_GASTO | TABLAS_DEFINICION_TEMAS)
                                         or any(n.get("type") == "SELECT_NODE" and _lee_cruda(n.get("from_table"))
                                                for n in nodos)):
        raise GuardiaGasto("R-GASTO-05: la línea aparte de los programas sociales (v_programa_social_linea_aparte) se "
                           "consulta sola: no se suma ni se combina con el gasto final, gasto_tema() ni el fact.")
    if tablas & TABLAS_DEFINICION_TEMAS and (llamadas or tablas & VISTAS_GASTO):
        raise GuardiaGasto("R-GASTO-08b: las tablas que definen los temas no se leen junto con el gasto (se podría "
                           "rearmar la suma de alcances); use gasto_tema('<tema_id>') o v_gasto_concepto.")
    # G7 (auditoría de P3, H-P3-2): el 15 y el 07 solo con el filtro de ámbito
    if (llamadas or tablas & VISTAS_GASTO) and cols & COLS_TERRITORIO and not cols & COLS_FILTRO_AMBITO:
        textos = {str(n["value"].get("value", "")) for n in nodos if n.get("class") == "CONSTANT"
                  and isinstance(n.get("value"), dict) and isinstance(n["value"].get("value"), str)}
        if any(t.startswith(("15", "07", "A-LIMA", "A-AREA_METROPOLITANA")) for t in textos):
            raise GuardiaGasto("R-GASTO-03 (P3, H-A4): el gasto del departamento 15 o 07 se lee por ámbito, con "
                               "ambito_gasto o cuenta_en_ambito (v_gasto_por_ambito); sin ese filtro sumaría la sede "
                               "nacional a Lima o al Callao.")
