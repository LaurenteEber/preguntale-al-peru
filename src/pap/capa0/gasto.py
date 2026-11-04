"""Sprint S3 — Gasto: base agregada del MEF, dim_unidad_ejecutora, dim_inversion_ubicacion, dim_tema_gasto y
atribución territorial (R-GASTO-01/02/03/04/05/08). Todo en DuckDB: los CSV anuales pesan ~10 GB.

Paso 1 (lento, una vez por archivo y versión del SQL): `construir_base` agrega cada CSV a
gasto_base_<año>_<huella CSV>_<huella SQL>.parquet (montos DECIMAL). Si cambia el SQL, cambia el nombre y se rehace.
Paso 2 (rápido): dimensiones, atribución y pruebas sobre la base. fact_gasto_territorial se escribe directo desde
DuckDB (montos DECIMAL exactos, GA-12).

Correcciones de la auditoría de la Ola 0 (6/10/2026): GA-01 (alcance de ejecutoras nacionales con sede en Lima,
decisión del dueño: marcar), GA-02 (ubicación principal del CUI y consistencia con la meta), GA-04/GA-05 (base con
producto, actividad, fuente y clasificador de transferencias), RP-02 (insumos exactos y huella de la base),
RP-08 (pruebas bloqueantes y montos ilegibles), SP-06/TE-10 (ámbitos de Lima con código propio), TE-03 (CUI en
distritos que aún no existían), GA-09 (ningún CUI del detalle se pierde: LEFT JOIN con método y motivo de
ubicación; «-MUL.DEP-» del GN/GORE con meta en Lima → nacional_multidepartamental; alias 160114 y 030715;
160109 escindido → curado por CUI o provincia 160800; UBIGEO nulo por nombre solo en GL, decisión del dueño).

GA-05 (ronda 3, 7/10/2026, v2 tras la auditoría aud_ga05): la categoría de cada fila de la genérica 2.4 sale de la lista
curada curados/capa0/lista_transferencias.yaml (módulo transferencias.py), no de un patrón. La base agregada no
cambia (misma HUELLA_SQL): la vista `base` reemplaza su `es_transferencia`. Las vistas del motor (vistas_gasto.sql) se
crean y se prueban aquí (G-17c); el motor consulta solo a través de guardia_gasto.verificar_consulta().
Pruebas de GA-05: G-15, G-15b, G-17, G-17b, G-17c, G-18, G-18b. Pruebas de GA-09: G-10 (redefinida), G-20 a G-24.

Pieza C (rondas 1-2, 8/10/2026): capa de trazabilidad (módulo trazabilidad.py), dim_tema_gasto v1.2 y glosario v2. Las
vistas temáticas (v_gasto_concepto, macro gasto_tema y v_gasto_tema_interna, esta solo para pruebas) están en vistas_gasto_temas.sql. Pruebas: G-03 (v1.2, todos los
alcances), G-28 a G-36.

E3 – gasto (decisiones del dueño del 8/10/2026; fact v1.4.0): alcance lima_departamento (cuenta en Lima sin ámbito, ubigeo
150000), obras de sede o función nacional (lista curada obras_sede_nacional.yaml: columna obra_sede_nacional; salen de
cuenta_en_lima) y línea aparte de los programas sociales (rel_programa_social_linea_aparte). Pruebas: G-27 (redefinida),
G-37, G-38.

P3 – Lima en tres ámbitos (decisiones L1-L9 del dueño del 9/10/2026; fact v1.5.0): un solo mecanismo de sesgo de sede
para los dpto 15 y 07 (cuenta_en_ambito; cuenta_en_lima queda como alias en el 15), alcance por (ejecutora, meta) con el
bloque alcance_callao de ejecutoras_alcance.yaml, obras de sede o función nacional también en el 07, y pliegos
regionales con ámbito por ley (GR Lima → Lima Región, Ley 31140; GR Callao → 07). Vista v_gasto_por_ambito. Pruebas:
G-27, G-37 y G-12 generalizadas (pruebas_ambito), G-39, G-40, G-41 y G-42 (no bloqueante). Informe:
curados/generadores/p3_gasto/implementacion.md.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
import pandas as pd
import yaml

from .. import almacen, capturas
from ..config import Rutas
from ..errores import PapError
from . import insumos
from . import transferencias as tr
from . import trazabilidad as traza

VERSION_TABLA = "1.5.0"  # P3 (9/10/2026): cuenta_en_ambito (15 y 07), alcance_callao, pliegos regionales por ley
# (v1.4.0: E3, obra_sede_nacional y lima_departamento; v1.3.0: pieza A, rondas 1-2)
# Versión propia de las tablas cuyo contenido no cambió en la pieza A (auditoría de la pieza A, H7): su huella no
# debe moverse solo por la etiqueta. Aplica a fact_gasto_territorial y dim_unidad_ejecutora la VERSION_TABLA.
VERSION_INVERSION = "1.2.0"   # dim_inversion_ubicacion (GA-09)
VERSION_TEMA = traza.VERSION_TEMA  # dim_tema_gasto v1.2 de contenido (pieza C): prefijos de cadena, conceptos, sin transf.
MEMORIA = "2GB"
# PIA nacional por Ley de Presupuesto (millones de soles), control de que el PIA no se repite por mes
PIA_LEY_MILLONES = {2023: 214_790, 2024: 240_806, 2025: 251_808}
TOL_CONCILIACION_ESTRICTA = 0.0005  # GA-06: aviso si un año × nivel difiere más de 0,05 %
COBERTURA_CUI_MIN = 0.60           # G-04: devengado en proyectos ubicado por CUI
SALTO_COBERTURA_PP = 0.05          # GA-03: años no comparables si la cobertura por CUI difiere más de 5 pp

# Cifras aprobadas por el dueño el 7/10/2026 (millones de soles, devengado, sin transferencias; ronda2/README.md §1.4):
# G-30 y G-32 las exigen exactas, desde la capa de trazabilidad y desde las vistas del motor
CONTROLES_R2 = {"grupo_expan": {2023: 2179, 2024: 2429, 2025: 2456},
                "grupo_opcion_c": {2023: 2056, 2024: 2327, 2025: 2366},
                "grupo_anemia_estricta": {2023: 138, 2024: 184, 2025: 208},
                "pp_1001_dit": {2023: 2750, 2024: 3607, 2025: 3867}}
AMBITO_UBIGEO = {"LIMA_REGION": "A-LIMA_REGION", "LIMA_METROPOLITANA": "A-LIMA_METROPOLITANA",
                 "AREA_METROPOLITANA_LIMA_CALLAO": "A-AREA_METROPOLITANA_LIMA_CALLAO"}
# lima_departamento (E3, 8/10/2026; INPE Oficina Regional Lima): cuenta en Lima, sin ámbito (ubigeo 150000)
ALCANCES = {"nacional", "lima_metropolitana", "lima_region", "lima_callao", "lima_departamento"}
CRITERIOS_OBRA_SEDE = {"sede_institucional", "tecnologia_institucional", "formacion_nacional",
                       "patrimonio_cultural_nacional", "instituto_nacional", "funcion_nacional"}
# GA-09: códigos del detalle MEF que no existen en dim_ubigeo_historico y que equivalen a UN solo distrito (alias).
# 160114 Teniente Manuel Clavero pasó entero de Maynas a Putumayo (Ley 30186, 2014) → 160803. 030715 es el código del
# MEF para «Mariscal Gamarra» (Grau, Apurímac) → 030703; los 3 nombres dicen «distrito de Mariscal Gamarra - Grau»
# (confianza media hasta citar la norma de denominación). Mover a la tabla alias_ubigeo cuando exista (TE-11).
ALIAS_UBIGEO_INVERSION = {"160114": "160803", "030715": "030703"}
CONFIANZA_ALIAS = {"160114": "alta", "030715": "media"}
# GA-09: códigos ESCINDIDOS (un código antiguo → varios distritos). 160109 Putumayo se dividió (Ley 30186) en 160801,
# 160802 y 160804: no hay alias. Se ubica por CUI con inversiones_ubicacion_curada.yaml y, si el CUI no está curado,
# en la provincia que contiene a todos los sucesores.
ESCINDIDOS_UBIGEO = {"160109": "160800"}
# GA-09: proyectos «-MUL.DEP-» (UBIGEO 99xxxx) del GN o de un GORE. True (opción B, recomendada): solo los de meta en
# Lima van a nacional_multidepartamental; fuera de Lima se respeta la meta y se rotula. False (opción A): todos a
# nacional_multidepartamental.
MULTIDEP_SOLO_META_LIMA = True
FILTRO_MULTIDEP = "AND b.departamento_meta = '15'" if MULTIDEP_SOLO_META_LIMA else ""  # el mismo texto va a G-16
# GA-09: el UBIGEO nulo se ubica por nombre solo en gobiernos locales (decisión del dueño, 7/10/2026; auditoría final,
# hallazgo 2). En el GN el texto suele ser la sede; en un GORE no está autorizado (hoy no hay casos).
NIVELES_UBICACION_POR_NOMBRE = ("GL",)
MOTIVOS_SIN_UBICACION = {"ubigeo_nulo_texto_gn_no_fiable", "ubigeo_nulo_texto_gr_no_usado", "ubigeo_nulo_sin_texto",
                         "ubigeo_nulo_nombre_ambiguo", "ubigeo_nulo_nombre_no_resuelto", "ubigeo_inexistente"}
# Pieza A (rondas 1-2, 8/10/2026): la clave suma la actividad (eslabón de la trazabilidad, decisión 4 de la ronda 2),
# el grupo funcional, la categoría de gasto, el clasificador de gasto y la fuente/rubro (R-GASTO-05, 18 a 21;
# PRE-DATOS-01 de reglas_propuestas_v2.csv). El clasificador de gasto es la genérica (2.x) en general y el código
# completo hasta la específica de detalle en la genérica 2.4 (es el único nivel que piden las reglas; la base no
# agrega por subgenérica fuera de 2.4).
CLAVE_FACT = ["anio", "mes", "nivel_atribucion", "ubigeo_atribucion", "ambito_id", "sec_ejec", "departamento_meta",
              "programa_ppto", "producto_proyecto", "actividad_accion_obra", "funcion", "division_funcional",
              "grupo_funcional", "categoria_gasto", "generica", "clasificador_gasto", "fuente_financiamiento", "rubro",
              "tipo_act_proy", "categoria_transferencia"]
# (tabla, código, nombre) que se agregan a la fact al escribirla
NOMBRES_FACT = [("nom_actividad", "actividad_accion_obra", "actividad_accion_obra_nombre"),
                ("nom_generica", "generica", "generica_nombre"),
                ("nom_clasificador", "clasificador_transferencia", "clasificador_transferencia_nombre"),
                ("nom_fuente", "fuente_financiamiento", "fuente_financiamiento_nombre"),
                ("nom_rubro", "rubro", "rubro_nombre")]
# Campos de ejecutoras_alcance.yaml v2 (criterio único, ronda 2 §3)
MARCAS_ALCANCE = ["referencia_nacional", "verificar_procedencia", "mixta"]

# ---------------- P3 (Lima en tres ámbitos, L6; 9/10/2026): un solo mecanismo de sesgo de sede para los dpto 15 y 07
# El alcance de una ejecutora del GN se decide por (ejecutora, departamento de la meta): `alcance` de
# ejecutoras_alcance.yaml para la meta 15 (GA-01) y el bloque `alcance_callao` para la meta 07. Una fila cuenta en las
# cifras de su ámbito (LM, LR o Callao) si está atribuida al 15 o al 07 y no es de alcance nacional, ni de un centro de
# referencia nacional, ni una obra de sede o función nacional (cuenta_en_ambito). cuenta_en_lima = cuenta_en_ambito ∧
# dpto 15 (alias, se conserva). Las funciones sql_* son la única definición: gasto.py y la simulación de P3 las usan.
DPTOS_SEDE = ("15", "07")
ALCANCES_CALLAO = {"nacional", "callao", "lima_callao"}  # lima_callao: ATU (H-P3-3)
# Pliegos regionales con ámbito por ley (Ley 31140 y Ley 27783): todo su gasto territorializado va a ese ámbito
AMBITO_PLIEGO_REGIONAL_SQL = """CASE WHEN {ng} = 'R' AND {p} LIKE 'GOBIERNO REGIONAL%LIMA%' AND {p} NOT LIKE '%METROPOLITANA%'
                                       THEN 'LIMA_REGION'
                                     WHEN {ng} = 'R' AND {p} LIKE 'MUNICIPALIDAD METROPOLITANA DE LIMA%' THEN 'LIMA_METROPOLITANA'
                                     WHEN {ng} = 'R' AND {p} LIKE 'GOBIERNO REGIONAL%CALLAO%' THEN 'CALLAO' END"""


def sql_ambito_pliego_regional(nivel_gobierno: str = "nivel_gobierno", pliego_nombre: str = "pliego_nombre") -> str:
    """Ámbito por ley del pliego regional: GR Lima → LIMA_REGION (Ley 31140), pliego regional de la MML →
    LIMA_METROPOLITANA, GR Callao → CALLAO; NULL en el resto."""
    return AMBITO_PLIEGO_REGIONAL_SQL.format(ng=nivel_gobierno, p=pliego_nombre)


def sql_fuera_de_su_ambito(ubigeo: str = "ubigeo_base", ambito_pliego: str = "ambito_pliego") -> str:
    """¿La fila de un pliego regional con ámbito por ley cae en el dpto 15 fuera de ese ámbito? (H-A2, H-08). La Ley 31140
    reparte el dpto 15: el gasto con meta o CUI en otro departamento (GR Lima con meta 12) se queda donde está
    (auditoría de P3, H-P3-6); 000000 (deuda, multidepartamental) es nacional, como en todo GORE."""
    u, a = ubigeo, ambito_pliego
    return f"""({a} IS NOT NULL AND substr({u}, 1, 2) = '15' AND CASE {a}
                  WHEN 'LIMA_REGION' THEN substr({u}, 1, 4) = '1501' OR {u} = '150000'
                  WHEN 'LIMA_METROPOLITANA' THEN substr({u}, 1, 4) <> '1501'
                  WHEN 'CALLAO' THEN true END)"""


def sql_ubigeo_base_regional(ubigeo: str = "ubigeo_base", ambito_pliego: str = "ambito_pliego") -> str:
    """ubigeo_base corregido: GR Callao en el 15 → 070000; GR Lima / MML fuera de su ámbito en el 15 → 150000 (con ámbito)."""
    return (f"CASE WHEN {sql_fuera_de_su_ambito(ubigeo, ambito_pliego)} THEN "
            f"CASE WHEN {ambito_pliego} = 'CALLAO' THEN '070000' ELSE '150000' END ELSE {ubigeo} END")


def sql_ambito_id(nivel_atribucion: str = "nivel_atribucion", ubigeo: str = "ubigeo_base",
                  ambito_ue: str = "ambito_ue", ambito_pliego: str = "ambito_pliego",
                  alcance_fila: str = "alcance_fila") -> str:
    """ámbito de Lima con código propio (SP-06): el del pliego regional si su fila cae fuera de su ámbito (H-A2); el de la
    ejecutora para el gasto por meta atribuido a 150000 (nunca el del GR Callao, H-P3-8); y Lima y Callao sin separar
    para el gasto por meta 07 con alcance_callao lima_callao (ATU, H-P3-3: el mismo trato que con meta 15). `ubigeo` es el
    ubigeo_base SIN corregir."""
    return (f"CASE WHEN {sql_fuera_de_su_ambito(ubigeo, ambito_pliego)} AND {ambito_pliego} <> 'CALLAO' "
            f"THEN {ambito_pliego} WHEN {nivel_atribucion} = 'departamento_meta' AND {ubigeo} = '150000' "
            f"AND coalesce({ambito_pliego}, '') <> 'CALLAO' THEN {ambito_ue} "
            f"WHEN {nivel_atribucion} = 'departamento_meta' AND {ubigeo} = '070000' AND {alcance_fila} = 'lima_callao' "
            f"THEN 'AREA_METROPOLITANA_LIMA_CALLAO' END")


def sql_alcance_fila(nivel_atribucion: str = "nivel_atribucion", departamento_meta: str = "departamento_meta",
                     nivel_gobierno: str = "nivel_gobierno", alcance_15: str = "alcance_ejecutora",
                     alcance_07: str = "alcance_ejecutora_callao", actividad: str = "actividad_accion_obra",
                     actividades_nacionales_07: str = "actividades_nacionales_callao") -> str:
    """Alcance de la fila: solo el gasto del GN por meta en el 15 (GA-01) o en el 07 (L6); en el resto, no_aplica. Con meta
    07, las actividades listadas en alcance_callao.actividades_nacionales son nacionales aunque la ejecutora cuente
    (separación por producto de una mixta: aviación policial de DIREFIN, auditoría de P3)."""
    return (f"CASE WHEN {nivel_atribucion} = 'departamento_meta' AND {nivel_gobierno} = 'E' AND {departamento_meta} = '15' "
            f"THEN coalesce({alcance_15}, 'sin_clasificar') "
            f"WHEN {nivel_atribucion} = 'departamento_meta' AND {nivel_gobierno} = 'E' AND {departamento_meta} = '07' "
            f"THEN CASE WHEN list_contains(string_split(coalesce({actividades_nacionales_07}, ''), ','), {actividad}) "
            f"THEN 'nacional' ELSE coalesce({alcance_07}, 'sin_clasificar') END ELSE 'no_aplica' END")


def sql_cuenta_en_ambito(departamento: str = "departamento_atribucion", alcance_fila: str = "alcance_ejecutora",
                         referencia_nacional: str = "referencia_nacional",
                         obra_sede_nacional: str = "obra_sede_nacional") -> str:
    """La fila entra en las cifras de su ámbito (LM, LR o Callao): dpto 15 o 07, sin alcance nacional (GA-01 / L6), sin
    referencia nacional (con sus obras) y sin obra de sede o de función nacional."""
    return (f"({departamento} IN {DPTOS_SEDE} AND coalesce({alcance_fila}, '') <> 'nacional' "
            f"AND NOT {referencia_nacional} AND NOT {obra_sede_nacional})")


def cuenta_en_ambito(departamento: str, alcance_fila: str | None, referencia_nacional: bool,
                     obra_sede_nacional: bool) -> bool:
    """Versión Python de sql_cuenta_en_ambito (pruebas unitarias y documentación)."""
    return (departamento in DPTOS_SEDE and (alcance_fila or "") != "nacional" and not referencia_nacional
            and not obra_sede_nacional)


@dataclass
class Resultado:
    tablas: dict = field(default_factory=dict)
    pruebas: list[dict] = field(default_factory=list)
    revision: dict[str, pd.DataFrame] = field(default_factory=dict)
    insumos: list = field(default_factory=list)

    def prueba(self, id_, descripcion, ok, detalle=None, bloqueante=True):
        self.pruebas.append({"id": id_, "descripcion": descripcion, "ok": bool(ok), "bloqueante": bloqueante,
                             "detalle": detalle})

    @property
    def ok(self):
        return all(p["ok"] for p in self.pruebas if p["bloqueante"])


def _con(rutas: Rutas) -> duckdb.DuckDBPyConnection:
    tmp = Path.home() / ".pap_duckdb_tmp"
    tmp.mkdir(exist_ok=True)
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{MEMORIA}'; SET threads=2; SET temp_directory='{tmp}'; "
                "SET preserve_insertion_order=false; SET enable_progress_bar=false")
    return con


def carpeta_base(rutas: Rutas) -> Path:
    return rutas.raiz / "biblioteca" / "estandarizada" / "gasto"


def archivos_gasto(rutas: Rutas) -> dict[int, dict]:
    """Último archivo canónico por año (R-GASTO-04: -Gasto.csv hasta 2024; -Gasto-Mensual.csv desde 2025)."""
    out = {}
    recs = insumos.filtrar_por_lock(rutas, "MEF-DA-PRESUPUESTO-EJECUCION-GASTO",
                                    [r for _, r in capturas.recursos(rutas, "MEF-DA-PRESUPUESTO-EJECUCION-GASTO")])
    for rec in recs:
        n = rec["original_filename"]
        for anio in range(2012, 2031):
            esperado = f"{anio}-Gasto.csv" if anio <= 2024 else f"{anio}-Gasto-Mensual.csv"
            if n == esperado:
                out[anio] = rec
    return out


def _monto(col: str) -> str:
    return f"SUM(TRY_CAST(NULLIF(trim({col}), '') AS DECIMAL(18,2)))"


def _invalido(col: str) -> str:
    return (f"COUNT(*) FILTER (WHERE NULLIF(trim({col}), '') IS NOT NULL "
            f"AND TRY_CAST(trim({col}) AS DECIMAL(18,2)) IS NULL)")


SQL_BASE = f"""
COPY (
  SELECT CAST(ANO_EJE AS INTEGER) AS anio, CAST(MES_EJE AS INTEGER) AS mes,
         NIVEL_GOBIERNO AS nivel_gobierno, SECTOR AS sector, SECTOR_NOMBRE AS sector_nombre,
         PLIEGO AS pliego, PLIEGO_NOMBRE AS pliego_nombre,
         SEC_EJEC AS sec_ejec, EJECUTORA_NOMBRE AS ejecutora_nombre,
         DEPARTAMENTO_EJECUTORA || PROVINCIA_EJECUTORA || DISTRITO_EJECUTORA AS ubigeo_sede,
         lpad(PROGRAMA_PPTO, 4, '0') AS programa_ppto, PROGRAMA_PPTO_NOMBRE AS programa_ppto_nombre,
         TIPO_ACT_PROY_NOMBRE AS tipo_act_proy, PRODUCTO_PROYECTO AS producto_proyecto,
         PRODUCTO_PROYECTO_NOMBRE AS producto_proyecto_nombre,
         ACTIVIDAD_ACCION_OBRA AS actividad_accion_obra, ACTIVIDAD_ACCION_OBRA_NOMBRE AS actividad_accion_obra_nombre,
         FUNCION_NOMBRE AS funcion, DIVISION_FUNCIONAL_NOMBRE AS division_funcional,
         GRUPO_FUNCIONAL_NOMBRE AS grupo_funcional,
         DEPARTAMENTO_META AS departamento_meta,
         FUENTE_FINANCIAMIENTO AS fuente_financiamiento, FUENTE_FINANCIAMIENTO_NOMBRE AS fuente_financiamiento_nombre,
         -- Pieza A (rondas 1-2, 8/10/2026): rubro y tipo de transacción para las reglas de ejecución (R-GASTO-18 a 21)
         RUBRO AS rubro, RUBRO_NOMBRE AS rubro_nombre,
         CATEGORIA_GASTO AS categoria_gasto, TIPO_TRANSACCION AS tipo_transaccion,
         GENERICA AS generica, GENERICA_NOMBRE AS generica_nombre,
         -- Clasificador completo solo para donaciones y transferencias (GA-05: la marca debe ser auditable)
         CASE WHEN GENERICA = '4' THEN TIPO_TRANSACCION || '.' || GENERICA || '.' || SUBGENERICA || '.' ||
              SUBGENERICA_DET || '.' || ESPECIFICA || '.' || ESPECIFICA_DET END AS clasificador_transferencia,
         CASE WHEN GENERICA = '4' THEN ESPECIFICA_DET_NOMBRE END AS clasificador_transferencia_nombre,
         -- Transferencia intergubernamental = 2.4.x.3 «A otras unidades del gobierno» (R-GASTO-05)
         (GENERICA = '4' AND SUBGENERICA_DET = '3') AS es_transferencia,
         {_monto('MONTO_PIA')} AS pia,
         {_monto('MONTO_PIM')} AS pim,
         {_monto('MONTO_DEVENGADO')} AS devengado,
         COUNT(*) AS filas,
         {_invalido('MONTO_PIA')} + {_invalido('MONTO_PIM')} + {_invalido('MONTO_DEVENGADO')} AS montos_invalidos
  -- escape explícito y modo estricto: con el escape adivinado, DuckDB unía filas y corría columnas (auditoría,
  -- 6/10/2026: 3 de cada 50 000 filas en 2023); en modo estricto una línea mal formada detiene la construcción
  FROM read_csv(?, header=true, all_varchar=true, quote='"', escape='"', delim=',', strict_mode=true)
  GROUP BY ALL
  ORDER BY ALL
) TO '{{destino}}' (FORMAT parquet, COMPRESSION zstd)
"""
HUELLA_SQL = hashlib.sha256(SQL_BASE.encode()).hexdigest()[:8]


def ruta_base(rutas: Rutas, anio: int, rec: dict) -> Path:
    return carpeta_base(rutas) / f"gasto_base_{anio}_{rec['hash'][7:19]}_{HUELLA_SQL}.parquet"


def filtrar_bases(rutas_bases, huella_sql: str = HUELLA_SQL, huellas_csv: dict | None = None) -> list[Path]:
    """De una lista de gasto_base_<año>_<huella CSV>_<huella SQL>.parquet deja solo las de la huella SQL vigente (y,
    si se da, la huella del CSV fijada por año). Falla si queda más de una por año: así una base vieja que siga en la
    carpeta nunca se suma dos veces (auditoría de la pieza A, H3)."""
    por_anio: dict[int, list[Path]] = {}
    for r in map(Path, rutas_bases):
        partes = r.stem.split("_")  # gasto, base, <año>, <huella CSV>, <huella SQL>
        if len(partes) != 5 or partes[:2] != ["gasto", "base"] or partes[4] != huella_sql:
            continue
        anio = int(partes[2])
        if huellas_csv is not None and huellas_csv.get(anio) != partes[3]:
            continue
        por_anio.setdefault(anio, []).append(r)
    repetidos = {a: [x.name for x in v] for a, v in por_anio.items() if len(v) > 1}
    if repetidos:
        raise PapError(f"Más de una base de gasto vigente por año: {repetidos}")
    return [v[0] for _, v in sorted(por_anio.items())]


def bases_vigentes(rutas: Rutas) -> list[Path]:
    """Las bases que corresponden a los CSV fijados en insumos.lock.yaml y a la HUELLA_SQL de este código. Todo lector
    de la base (constructor, pruebas, análisis) debe usar esta función y no un glob gasto_base_*.parquet."""
    huellas = {a: rec["hash"][7:19] for a, rec in archivos_gasto(rutas).items()}
    vig = filtrar_bases(sorted(carpeta_base(rutas).glob("gasto_base_*.parquet")), HUELLA_SQL, huellas)
    falta = sorted(set(huellas) - {int(p.stem.split("_")[2]) for p in vig})
    if falta:
        raise PapError(f"Falta la base de gasto vigente de {falta}: corre `pap construir gasto`")
    return vig


def construir_base(rutas: Rutas, anios: list[int] | None = None, rehacer: bool = False) -> list[Path]:
    arch = archivos_gasto(rutas)
    if not arch:
        raise PapError("No hay archivos de gasto registrados (MEF-DA-PRESUPUESTO-EJECUCION-GASTO)")
    carpeta_base(rutas).mkdir(parents=True, exist_ok=True)
    hechos = []
    for anio, rec in sorted(arch.items()):
        if anios and anio not in anios:
            continue
        destino = ruta_base(rutas, anio, rec)
        if destino.exists() and not rehacer:
            hechos.append(destino)
            continue
        tmp = destino.with_name(destino.name + ".tmp")
        con = _con(rutas)
        try:
            con.execute(SQL_BASE.replace("{destino}", str(tmp)), [str(almacen.resolver(rutas, rec["path"]))])  # .zst: DuckDB lo detecta por la extensión
        finally:
            con.close()
        tmp.replace(destino)
        hechos.append(destino)
    return hechos


def _alcance_ejecutoras(rutas: Rutas) -> pd.DataFrame:
    ruta = rutas.raiz / "curados" / "capa0" / "ejecutoras_alcance.yaml"
    filas = yaml.safe_load(ruta.read_text(encoding="utf-8")) or []
    faltan = [m for m in MARCAS_ALCANCE + ["base_alcance"] if any(m not in f for f in filas)]
    if faltan:
        raise PapError(f"ejecutoras_alcance.yaml: faltan campos en alguna entrada: {faltan}")
    df = pd.DataFrame(filas)
    df["confianza_alcance"] = [f["base_alcance"].get("confianza") for f in filas]
    df["paso_criterio"] = [f["base_alcance"].get("paso") for f in filas]
    df = df[["sec_ejec", "alcance", "criterio", "revisado_dueno", *MARCAS_ALCANCE, "confianza_alcance", "paso_criterio"]]
    if df.sec_ejec.duplicated().any():
        raise PapError("ejecutoras_alcance.yaml: sec_ejec repetido")
    if not df.alcance.isin(sorted(ALCANCES)).all():
        raise PapError("ejecutoras_alcance.yaml: alcance desconocido")
    for m in MARCAS_ALCANCE + ["revisado_dueno"]:
        if not df[m].map(lambda x: isinstance(x, bool)).all():
            raise PapError(f"ejecutoras_alcance.yaml: {m} debe ser true o false en todas las entradas")
    if (df.referencia_nacional & (df.alcance != "nacional")).any():
        raise PapError("ejecutoras_alcance.yaml: referencia_nacional exige alcance nacional")
    # P3 (L6): bloque opcional alcance_callao = alcance con meta 07 (mismo mecanismo que GA-01, otra meta)
    cal = [f.get("alcance_callao") for f in filas]
    for f, c in zip(filas, cal):
        if c is None:
            continue
        if not isinstance(c, dict) or c.get("alcance") not in ALCANCES_CALLAO:
            raise PapError(f"ejecutoras_alcance.yaml: alcance_callao desconocido en {f.get('sec_ejec')}")
        for m in ("mixta", "verificar_procedencia", "revisado_dueno"):
            if not isinstance(c.get(m), bool):
                raise PapError(f"ejecutoras_alcance.yaml: alcance_callao.{m} debe ser true o false ({f.get('sec_ejec')})")
        if not str(c.get("criterio") or "").strip():
            raise PapError(f"ejecutoras_alcance.yaml: alcance_callao sin criterio ({f.get('sec_ejec')})")
        act = c.get("actividades_nacionales", [])
        if not isinstance(act, list) or not all(isinstance(x, str) and x.isdigit() for x in act):
            raise PapError(f"ejecutoras_alcance.yaml: alcance_callao.actividades_nacionales mal formado ({f.get('sec_ejec')})")
        if act and c["alcance"] == "nacional":
            raise PapError(f"ejecutoras_alcance.yaml: actividades_nacionales sobra si el alcance ya es nacional ({f.get('sec_ejec')})")
    df["alcance_callao"] = pd.array([c["alcance"] if c else None for c in cal], dtype="string")
    df["mixta_callao"] = pd.array([c["mixta"] if c else None for c in cal], dtype="boolean")
    df["verificar_procedencia_callao"] = pd.array([c["verificar_procedencia"] if c else None for c in cal], dtype="boolean")
    df["criterio_callao"] = [c["criterio"] if c else None for c in cal]
    df["actividades_nacionales_callao"] = pd.array(
        [",".join(c.get("actividades_nacionales", [])) or None if c else None for c in cal], dtype="string")
    df["revisado_dueno_callao"] = pd.array([c["revisado_dueno"] if c else None for c in cal], dtype="boolean")
    return df.astype({"sec_ejec": str})


def _obras_sede_nacional(ruta: Path) -> pd.DataFrame:
    """Lista curada (E3, decisión del dueño del 8/10/2026) de obras de sede o de función nacional: (cui, sec_ejec)."""
    doc = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
    obras = doc.get("obras") or []
    df = pd.DataFrame(obras, columns=["cui", "sec_ejec", "criterio", "motivo"]).astype({"cui": str, "sec_ejec": str})
    if not isinstance(doc.get("revisado_dueno"), bool) or not doc.get("version"):
        raise PapError("obras_sede_nacional.yaml: faltan version o revisado_dueno")
    if not doc["revisado_dueno"] and "revisable por el dueño" not in str(doc.get("estado", "")):
        raise PapError("obras_sede_nacional.yaml: sin visto del dueño, estado debe declarar la lista revisable (E3, H2)")
    if df.duplicated(["cui", "sec_ejec"]).any():
        raise PapError("obras_sede_nacional.yaml: (cui, sec_ejec) repetido")
    if not df.cui.str.fullmatch(r"\d{7}").all() or not df.sec_ejec.str.fullmatch(r"\d+").all():
        raise PapError("obras_sede_nacional.yaml: cui (7 dígitos) o sec_ejec mal formado")
    if not df.criterio.isin(sorted(CRITERIOS_OBRA_SEDE)).all() or df.motivo.fillna("").str.strip().eq("").any():
        raise PapError("obras_sede_nacional.yaml: criterio desconocido o motivo vacío")
    return df[["cui", "sec_ejec", "criterio"]]


# Atribución final (fact_gasto_territorial) desde la tabla `atribuida`, `obras_sede` y `corte` (P3: función aparte para
# probarla con datos sintéticos (test_gasto_lima.py::test_sql_fact_sintetica) y con la fact publicada
# (p3_gasto/simular_efecto.py §4)
FACT_SQL = """
        CREATE TABLE fact AS
        WITH t00 AS (
          SELECT a.*,
                 CASE a.nivel_atribucion
                   WHEN 'distrito_inversion' THEN a.inv_ubigeo WHEN 'provincia_inversion' THEN a.inv_ubigeo
                   WHEN 'departamento_inversion' THEN a.inv_ubigeo
                   WHEN 'distrito_municipal' THEN a.ubigeo_sede
                   WHEN 'provincia_municipal' THEN substr(a.ubigeo_sede, 1, 4) || '00'
                   WHEN 'departamento_meta' THEN a.departamento_meta || '0000'
                   ELSE '000000' END AS ubigeo_base0
          FROM atribuida a
        ), t0 AS (
          -- P3 (H-A2, H-08): el pliego regional con ámbito por ley no sale de él (GR Lima → LR, MML → LM, GR Callao
          -- → 07). Los ámbitos de Lima tienen código propio (SP-06): el del pliego o el de la ejecutora en 150000.
          SELECT t00.*, {ubigeo_base} AS ubigeo_base, {ambito_id} AS ambito_id,
                 -- P3 (L6): alcance por (ejecutora, departamento de la meta): 15 → GA-01; 07 → alcance_callao
                 {alcance_fila} AS alcance_fila
          FROM t00
        ), t AS (
          -- E3: obra de sede o de función nacional (lista curada por CUI y ejecutora; solo nivel E, por CUI; dpto 15
          -- y, desde P3, 07)
          SELECT t0.*, (t0.nivel_gobierno = 'E' AND t0.nivel_atribucion IN ('distrito_inversion', 'provincia_inversion',
                        'departamento_inversion') AND substr(t0.ubigeo_base, 1, 2) IN {dptos}
                        AND os.cui IS NOT NULL) AS obra_sede_nacional,
                 -- P3: con meta 07 y bloque alcance_callao, las marcas mixta y verificar_procedencia salen del bloque
                 CASE WHEN t0.departamento_meta = '07' AND t0.alcance_fila NOT IN ('no_aplica', 'sin_clasificar')
                      THEN t0.ejecutora_mixta_callao ELSE t0.ejecutora_mixta END AS mixta_fila,
                 CASE WHEN t0.departamento_meta = '07' AND t0.alcance_fila NOT IN ('no_aplica', 'sin_clasificar')
                      THEN t0.verificar_procedencia_callao ELSE t0.verificar_procedencia END AS verificar_fila
          FROM t0 LEFT JOIN obras_sede os ON t0.tipo_act_proy ILIKE 'PROYECTO%'
               AND os.cui = lpad(t0.producto_proyecto, 7, '0') AND os.sec_ejec = t0.sec_ejec
        )
        SELECT anio, mes, nivel_atribucion,
               -- Los ámbitos de Lima tienen código propio para no compartir el 150000 (SP-06, TE-10)
               CASE WHEN ambito_id IS NOT NULL THEN 'A-' || ambito_id ELSE ubigeo_base END AS ubigeo_atribucion,
               substr(ubigeo_base, 1, 2) AS departamento_atribucion,
               ambito_id, sec_ejec, nivel_gobierno,
               -- alcance solo en el gasto del GN por meta en el 15 (GA-01) o en el 07 (P3); en el resto, no_aplica
               alcance_fila AS alcance_ejecutora, departamento_meta,
               programa_ppto, producto_proyecto,
               -- Pieza A: actividad, clasificador y fuente/rubro (sus nombres se agregan al escribir el Parquet)
               actividad_accion_obra, funcion, division_funcional, grupo_funcional, categoria_gasto,
               generica, clasificador_gasto, nivel_clasificador, fuente_financiamiento, rubro, tipo_act_proy,
               categoria_transferencia, es_transferencia, es_transferencia_intergub, bloque_consolidado,
               -- Pieza A (ronda 2 §3): marcas de la ejecutora. Un centro de referencia nacional (INEN, INSN San Borja)
               -- sale de la cifra de Lima con todo su gasto, incluidas sus obras ubicadas por CUI (alcance no_aplica).
               -- P3: con meta 07, mixta y verificar_procedencia salen del bloque alcance_callao
               referencia_nacional, verificar_fila AS verificar_procedencia, mixta_fila AS ejecutora_mixta,
               -- E3: obra de sede o de función nacional (obras_sede_nacional.yaml); sale de la cifra de su ámbito
               obra_sede_nacional,
               -- cuenta_en_lima: alias desde P3 = cuenta_en_ambito en el dpto 15 (se conserva para vistas y pruebas)
               bool_and({cuenta} AND substr(ubigeo_base, 1, 2) = '15') AS cuenta_en_lima,
               -- P3 (L6): cuenta_en_ambito: la fila entra en las cifras de su ámbito (LM, LR o Callao): dpto 15 o 07,
               -- sin alcance nacional, sin referencia nacional (con sus obras) y sin obras de sede o función nacional
               -- (la expresión es constante dentro de cada grupo de la clave)
               bool_and({cuenta}) AS cuenta_en_ambito,
               any_value(consistencia_meta) AS consistencia_meta,
               any_value(metodo_ubicacion) AS metodo_ubicacion_cui,  -- GA-09
               bool_or(inv_redirigido_origen) AS cui_redirigido_origen,
               sum(pia) AS pia, sum(pim) AS pim, sum(devengado) AS devengado,
               any_value(c.anio::VARCHAR || '-' || lpad(c.mes_max::VARCHAR, 2, '0')) AS fecha_corte_datos,
               any_value(c.es_anio_cerrado) AS es_anio_cerrado
        FROM t JOIN corte c USING (anio)
        GROUP BY anio, mes, nivel_atribucion, ubigeo_atribucion, departamento_atribucion, ambito_id, sec_ejec,
                 nivel_gobierno, alcance_fila, departamento_meta, programa_ppto, producto_proyecto,
                 actividad_accion_obra, funcion, division_funcional, grupo_funcional, categoria_gasto, generica,
                 clasificador_gasto, nivel_clasificador, fuente_financiamiento, rubro, tipo_act_proy,
                 categoria_transferencia, es_transferencia, es_transferencia_intergub, bloque_consolidado,
                 referencia_nacional, verificar_fila, mixta_fila, obra_sede_nacional
"""


def sql_fact() -> str:
    alcance = sql_alcance_fila("t00.nivel_atribucion", "t00.departamento_meta", "t00.nivel_gobierno",
                               "t00.alcance_ejecutora", "t00.alcance_ejecutora_callao", "t00.actividad_accion_obra",
                               "t00.actividades_nacionales_callao")
    return (FACT_SQL.replace("{ubigeo_base}", sql_ubigeo_base_regional("t00.ubigeo_base0", "t00.ambito_pliego"))
            .replace("{ambito_id}", sql_ambito_id("t00.nivel_atribucion", "t00.ubigeo_base0", "t00.ambito_ue",
                                                  "t00.ambito_pliego", f"({alcance})"))
            .replace("{alcance_fila}", alcance)
            .replace("{dptos}", str(DPTOS_SEDE))
            .replace("{cuenta}", sql_cuenta_en_ambito("substr(ubigeo_base, 1, 2)", "alcance_fila",
                                                      "referencia_nacional", "obra_sede_nacional")))


def pruebas_ambito(con: duckdb.DuckDBPyConnection, res: Resultado, refnac_yaml: list[str], n_obras: int) -> None:
    """Pruebas G-27, G-37, G-12, G-39, G-40, G-41 y G-42 (E3 y P3) sobre la tabla `fact` y `dim_unidad_ejecutora` de `con`.
    Separadas de construir() para correrlas también sobre la fact publicada con la lógica de P3 simulada."""
    # G-27 (pieza A, E3; P3: dpto 15 y 07): cuenta_en_ambito + referencia nacional + nacional = total del dpto
    amb = con.execute("""
        SELECT anio, departamento_atribucion, sum(devengado) AS total,
               coalesce(sum(devengado) FILTER (WHERE cuenta_en_ambito), 0) AS ambito,
               coalesce(sum(devengado) FILTER (WHERE referencia_nacional), 0) AS refnac,
               coalesce(sum(devengado) FILTER (WHERE NOT cuenta_en_ambito AND NOT referencia_nacional), 0) AS nacional,
               count(*) FILTER (WHERE referencia_nacional AND cuenta_en_ambito) AS refnac_en_ambito,
               count(*) FILTER (WHERE cuenta_en_ambito AND alcance_ejecutora = 'nacional') AS nacional_en_ambito,
               list(DISTINCT sec_ejec ORDER BY sec_ejec) FILTER (WHERE referencia_nacional) AS ue_refnac
        FROM fact WHERE departamento_atribucion IN ('15', '07') GROUP BY 1, 2 ORDER BY 1, 2""").fetchall()
    # H5 de la auditoría: fila a fila, sin depender del bool_and de la agregación
    fuera = con.execute(f"""SELECT count(*) FROM fact
                            WHERE cuenta_en_ambito IS DISTINCT FROM {sql_cuenta_en_ambito()}
                               OR cuenta_en_lima IS DISTINCT FROM (cuenta_en_ambito AND departamento_atribucion = '15')
                            """).fetchone()[0]
    res.prueba("G-27", "Lima (dpto 15) y Callao (07): cuenta_en_ambito + referencia nacional (aparte, con sus obras) + "
               "alcance nacional = total atribuido al dpto (tolerancia 0); cuenta_en_ambito = dpto ∈ {15, 07} ∧ alcance ≠ "
               "nacional ∧ ¬referencia_nacional ∧ ¬obra_sede_nacional y cuenta_en_lima = cuenta_en_ambito ∧ dpto 15, fila "
               "a fila (E3, P3); ninguna fila de referencia nacional ni de alcance nacional cuenta en su ámbito; las UE de "
               "referencia nacional en el 15 son las del YAML",
               fuera == 0 and all(t == a_ + r + n and ra == 0 and na == 0
                                  and (d != "15" or sorted(u or []) == refnac_yaml)
                                  for _, d, t, a_, r, n, ra, na, u in amb),
               {f"{a}/{d}": {"ambito": str(a_), "referencia_nacional": str(r), "nacional": str(n)}
                for a, d, t, a_, r, n, ra, na, u in amb})
    # G-37 (E3, decisión del 8/10/2026; P3: también el 07): obras de sede o función nacional. Cada (cui, sec_ejec) de la
    # lista curada existe como obra del nivel E atribuida al dpto 15 o 07; ninguna cuenta en su ámbito; la marca solo
    # está en esas filas.
    sede = con.execute("""
        WITH f AS (SELECT lpad(producto_proyecto, 7, '0') AS cui, sec_ejec, bool_or(obra_sede_nacional) AS marcada,
                          bool_or(obra_sede_nacional AND cuenta_en_ambito) AS en_ambito
                   FROM fact WHERE nivel_gobierno = 'E' AND departamento_atribucion IN ('15', '07')
                     AND nivel_atribucion LIKE '%_inversion' GROUP BY 1, 2)
        SELECT count(*) FILTER (WHERE f.cui IS NULL), count(*) FILTER (WHERE NOT f.marcada),
               count(*) FILTER (WHERE f.en_ambito),
               (SELECT count(*) FROM fact WHERE obra_sede_nacional AND (nivel_gobierno <> 'E'
                    OR departamento_atribucion NOT IN ('15', '07') OR nivel_atribucion NOT LIKE '%_inversion'))
        FROM obras_sede o LEFT JOIN f USING (cui, sec_ejec)""").fetchone()
    monto_sede = con.execute("""SELECT anio, departamento_atribucion, sum(devengado) FROM fact WHERE obra_sede_nacional
                                AND bloque_consolidado = 'gasto_final' GROUP BY 1, 2 ORDER BY 1, 2""").fetchall()
    res.prueba("G-37", "Obras de sede o función nacional (obras_sede_nacional.yaml): cada (CUI, ejecutora) está en la fact "
               "como obra del GN en el dpto 15 o 07, ninguna cuenta en su ámbito y la marca no aparece en otras filas",
               not any(sede), {"no_encontradas": sede[0], "sin_marca": sede[1], "en_ambito": sede[2],
                               "marca_fuera_de_obras_gn_15_07": sede[3], "obras_lista": n_obras,
                               "gasto_final_millones": {str(a): round(float(m) / 1e6, 1)
                                                        for a, d, m in monto_sede if d == "15"},
                               "gasto_final_millones_callao": {str(a): round(float(m) / 1e6, 1)
                                                               for a, d, m in monto_sede if d == "07"}})
    res.revision["gasto_lima_obras_sede_nacional"] = con.execute("""
        SELECT anio, departamento_atribucion, sec_ejec, lpad(producto_proyecto, 7, '0') AS cui, nivel_atribucion,
               round(sum(devengado)/1e6, 2) AS devengado_millones
        FROM fact WHERE obra_sede_nacional AND bloque_consolidado = 'gasto_final'
        GROUP BY ALL ORDER BY anio, departamento_atribucion, devengado_millones DESC, sec_ejec, cui, nivel_atribucion""").df()
    res.revision["gasto_lima_referencia_nacional"] = con.execute("""
        SELECT anio, sec_ejec, nivel_atribucion, funcion, programa_ppto, round(sum(devengado)/1e6, 2) AS devengado_millones
        FROM fact WHERE referencia_nacional AND departamento_atribucion = '15' AND bloque_consolidado = 'gasto_final'
        GROUP BY ALL ORDER BY anio, sec_ejec, nivel_atribucion, funcion, programa_ppto""").df()

    # GA-01 / P3: gasto de ejecutoras nacionales con meta en Lima o en el Callao (se marca). Las cifras de cada ámbito
    # se calculan con cuenta_en_ambito (excluye el alcance nacional Y la referencia nacional, con sus obras)
    res.revision["gasto_lima_por_alcance"] = con.execute("""
        SELECT anio, departamento_meta, coalesce(alcance_ejecutora, 'no_E') AS alcance, coalesce(ambito_id, '-') AS ambito,
               round(sum(devengado)/1e6, 1) AS devengado_millones
        FROM fact WHERE nivel_atribucion = 'departamento_meta' AND departamento_meta IN ('15', '07')
        GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4""").df()
    sincl = con.execute("""SELECT anio, departamento_meta,
                                  sum(devengado) FILTER (WHERE alcance_ejecutora = 'sin_clasificar') / sum(devengado)
                           FROM fact WHERE nivel_atribucion = 'departamento_meta' AND departamento_meta IN ('15', '07')
                             AND nivel_gobierno = 'E' GROUP BY 1, 2 ORDER BY 1, 2""").fetchall()
    res.prueba("G-12", "Ejecutoras nacionales con meta en Lima clasificadas por alcance (sin clasificar ≤ 3 % del devengado)",
               all(float(p or 0) <= 0.03 for _, d, p in sincl if d == "15"),
               {str(a): round(float(p or 0), 4) for a, d, p in sincl if d == "15"})
    res.prueba("G-40", "P3 (L6): ejecutoras nacionales con meta en el Callao clasificadas por alcance_callao (sin "
               "clasificar ≤ 3 % del devengado); el alcance de la fila es no_aplica fuera del GN por meta 15 o 07",
               all(float(p or 0) <= 0.03 for _, d, p in sincl if d == "07") and con.execute(f"""
                   SELECT count(*) FROM fact WHERE (alcance_ejecutora = 'no_aplica') IS DISTINCT FROM
                     (NOT (nivel_atribucion = 'departamento_meta' AND nivel_gobierno = 'E'
                           AND departamento_meta IN {DPTOS_SEDE}))""").fetchone()[0] == 0,
               {str(a): round(float(p or 0), 4) for a, d, p in sincl if d == "07"})
    # G-39 (P3, H-A2, H-08; auditoría de P3, H-P3-6): pliegos regionales con ámbito por ley en el dpto 15. Toda fila del
    # GR Lima atribuida al 15 está en LR, la del pliego regional de la MML en LM y ninguna del GR Callao queda en el 15.
    # El gasto con meta o CUI en otro departamento se queda donde está (la Ley 31140 solo reparte el dpto 15).
    reg = con.execute(f"""
        SELECT u.ambito_pliego_regional AS pliego, f.anio,
               count(*) FILTER (WHERE f.departamento_atribucion = '15' AND NOT CASE u.ambito_pliego_regional
                   WHEN 'LIMA_REGION' THEN f.ubigeo_atribucion = 'A-LIMA_REGION' OR (f.ubigeo_atribucion LIKE '15%'
                        AND f.ubigeo_atribucion NOT LIKE '1501%' AND f.ubigeo_atribucion <> '150000')
                   WHEN 'LIMA_METROPOLITANA' THEN f.ubigeo_atribucion = 'A-LIMA_METROPOLITANA'
                        OR f.ubigeo_atribucion LIKE '1501%'
                   WHEN 'CALLAO' THEN false END) AS fuera,
               round(coalesce(sum(f.devengado) FILTER (WHERE f.departamento_atribucion NOT IN ('15', '07')), 0) / 1e6, 2)
                 AS fuera_del_15_07_millones
        FROM fact f JOIN dim_unidad_ejecutora u USING (anio, sec_ejec)
        WHERE f.nivel_gobierno = 'R' AND u.ambito_pliego_regional IS NOT NULL GROUP BY 1, 2 ORDER BY 1, 2""").fetchall()
    res.prueba("G-39", "P3 (Ley 31140; H-A2, H-08, H-P3-6): en el dpto 15, toda fila del GR Lima está en Lima Región, la "
               "del pliego regional de la MML en Lima Metropolitana y ninguna es del GR Callao (pasa al 07); el gasto "
               "con meta o CUI en otro departamento, la deuda y lo multidepartamental se quedan donde están",
               bool(reg) and all(fu == 0 for _, _, fu, _ in reg) and {p for p, *_ in reg} == {
                   "LIMA_REGION", "LIMA_METROPOLITANA", "CALLAO"},
               {f"{p}/{a}": {"fuera": fu, "fuera_del_15_07_millones": nt} for p, a, fu, nt in reg})
    # G-42 (auditoría de P3, H-P3-1; no bloqueante): canasta comparable del Callao con LM. Con meta 07 cuentan en el
    # Callao ejecutoras cuyo alcance con meta 15 es nacional (incluidas las mixtas), lima_callao o lima_departamento:
    # en LM no cuentan. El aviso obligatorio de v_gasto_por_ambito dice «≈ 15-17 %»: se revisa que siga en 12-22 %.
    cmp_ = con.execute("""
        SELECT f.anio, sum(f.devengado) AS callao,
               coalesce(sum(f.devengado) FILTER (WHERE f.nivel_atribucion = 'departamento_meta' AND f.nivel_gobierno = 'E'
                        AND u.alcance_ejecutora IN ('nacional', 'lima_callao', 'lima_departamento')), 0) AS no_comparable
        FROM fact f LEFT JOIN dim_unidad_ejecutora u USING (anio, sec_ejec)
        WHERE f.bloque_consolidado = 'gasto_final' AND f.cuenta_en_ambito AND f.departamento_atribucion = '07'
          AND f.ubigeo_atribucion <> 'A-AREA_METROPOLITANA_LIMA_CALLAO'
        GROUP BY 1 ORDER BY 1""").fetchall()
    res.revision["callao_canasta_comparable"] = pd.DataFrame(
        [(a, round(float(c_) / 1e6, 1), round(float(n) / 1e6, 1), round(float(c_ - n) / 1e6, 1),
          round(100 * float(n) / float(c_), 1)) for a, c_, n in cmp_],
        columns=["anio", "callao", "no_comparable_con_lm", "canasta_comparable", "pct_no_comparable"])
    res.prueba("G-42", "Auditoría de P3 (H-P3-1): el Callao incluye entidades que en LM se cuentan como nacionales o "
               "mixtas; su peso sigue en 12-22 % (el aviso de v_gasto_por_ambito dice ≈ 15-17 %)",
               bool(cmp_) and all(0.12 <= float(n) / float(c_) <= 0.22 for _, c_, n in cmp_),
               {str(a): {"callao": round(float(c_) / 1e6, 1), "canasta_comparable": round(float(c_ - n) / 1e6, 1),
                         "pct_no_comparable": round(100 * float(n) / float(c_), 1)} for a, c_, n in cmp_},
               bloqueante=False)
    # G-41 (P3, H-A4): v_gasto_por_ambito reparte el gasto final del 15 y el 07 sin solaparse ni perder nada, y la cifra
    # de cada ámbito es la de cuenta_en_ambito (LM y LR con su ubigeo o su código de ámbito; Callao = 07)
    va = con.execute("""
        WITH v AS (SELECT anio, sum(devengado) AS total,
                          sum(devengado) FILTER (WHERE ambito_gasto = 'LIMA_METROPOLITANA') AS lm,
                          sum(devengado) FILTER (WHERE ambito_gasto = 'LIMA_REGION') AS lr,
                          sum(devengado) FILTER (WHERE ambito_gasto = 'CALLAO') AS ca,
                          sum(devengado) FILTER (WHERE linea = 'revisar') AS rev
                   FROM v_gasto_por_ambito GROUP BY 1),
             f AS (SELECT anio, sum(devengado) AS total,
                          sum(devengado) FILTER (WHERE cuenta_en_ambito AND (ubigeo_atribucion = 'A-LIMA_METROPOLITANA'
                                                 OR ubigeo_atribucion LIKE '1501%')) AS lm,
                          sum(devengado) FILTER (WHERE cuenta_en_ambito AND (ubigeo_atribucion = 'A-LIMA_REGION'
                                                 OR (ubigeo_atribucion LIKE '15%' AND ubigeo_atribucion NOT LIKE '1501%'
                                                     AND ubigeo_atribucion <> '150000'))) AS lr,
                          sum(devengado) FILTER (WHERE cuenta_en_ambito AND departamento_atribucion = '07'
                                                 AND ubigeo_atribucion <> 'A-AREA_METROPOLITANA_LIMA_CALLAO') AS ca
                   FROM fact WHERE bloque_consolidado = 'gasto_final' AND departamento_atribucion IN ('15', '07')
                   GROUP BY 1)
        SELECT f.anio, f.total, v.total, f.lm, v.lm, f.lr, v.lr, f.ca, v.ca, v.rev
        FROM f LEFT JOIN v USING (anio) ORDER BY 1""").fetchall()
    res.prueba("G-41", "P3 (H-A4): v_gasto_por_ambito = gasto final del 15 y el 07 sin solapes (tolerancia 0); LM, LR y "
               "Callao = filas cuenta_en_ambito de su territorio; ninguna fila en «revisar»",
               bool(va) and all(ft == vt and fl == vl and fr == vr and fc == vc and not rv
                                for _, ft, vt, fl, vl, fr, vr, fc, vc, rv in va),
               {str(a): {"LM": round(float(vl or 0) / 1e6, 1), "LR": round(float(vr or 0) / 1e6, 1),
                         "CALLAO": round(float(vc or 0) / 1e6, 1)} for a, ft, vt, fl, vl, fr, vr, fc, vc, rv in va})
    res.revision["gasto_por_ambito"] = con.execute("""
        SELECT anio, linea, ambito_gasto, round(sum(devengado)/1e6, 1) AS devengado_millones
        FROM v_gasto_por_ambito GROUP BY ALL ORDER BY anio, linea, ambito_gasto""").df()


def construir(rutas: Rutas) -> Resultado:
    res = Resultado()
    arch = archivos_gasto(rutas)
    construir_base(rutas)
    bases = bases_vigentes(rutas)  # H3: solo la huella vigente, una por año
    # Insumos exactos: el archivo canónico de cada año (RP-02) y la base agregada que de verdad se leyó
    for anio, rec in sorted(arch.items()):
        res.insumos.append(insumos.Insumo("MEF-DA-PRESUPUESTO-EJECUCION-GASTO", rec["name"], rec["hash"],
                                          almacen.resolver(rutas, rec["path"]), rec["original_filename"], rec.get("issued"),
                                          rec["retrieved_at"]))
    for b in bases:
        res.insumos.append(insumos.Insumo("ESTANDARIZADA:gasto_base", b.name, insumos._sha256(b), b, b.name,
                                          None, None))
    i_inv = insumos.ultimo(rutas, "MEF-DETALLE-INVERSIONES")
    i_dim = insumos.tabla(rutas, "dim_ubigeo_historico")
    i_rel = insumos.tabla(rutas, "rel_ubigeo_origen")
    i_ctl = insumos.curado(rutas, "control_consulta_amigable.yaml")
    i_alc = insumos.curado(rutas, "ejecutoras_alcance.yaml")
    i_cur = insumos.curado(rutas, "inversiones_ubicacion_curada.yaml")  # GA-09
    i_tr = insumos.curado(rutas, "lista_transferencias.yaml")  # GA-05
    i_vis = insumos.curado(rutas, "vistas_gasto.sql")          # GA-05
    i_vtem = insumos.curado(rutas, "vistas_gasto_temas.sql")   # pieza C
    i_sede = insumos.curado(rutas, "obras_sede_nacional.yaml")  # E3
    res.insumos += [i_inv, i_dim, i_rel, i_ctl, i_alc, i_cur, i_tr, i_vis, i_vtem, i_sede]
    alcance = _alcance_ejecutoras(rutas)
    obras_sede = _obras_sede_nacional(i_sede.ruta)
    try:
        lista_tr = tr.cargar_lista(i_tr.ruta)
    except tr.ListaInvalida as e:
        raise PapError(f"lista_transferencias.yaml: {e}") from e

    con = _con(rutas)
    lista = ", ".join(f"'{b}'" for b in bases)
    con.execute(f"CREATE VIEW base_cruda AS SELECT * FROM read_parquet([{lista}])")
    tr.registrar(con, lista_tr, base_cruda="base_cruda", destino="base")  # GA-05: categoria_transferencia y bloque
    con.execute(f"CREATE VIEW dim_ubigeo AS SELECT * FROM '{i_dim.ruta}'")
    con.execute("CREATE TABLE ubigeos AS SELECT DISTINCT ubigeo_inei, nivel FROM dim_ubigeo")
    con.register("alcance_df", alcance)
    con.execute("CREATE TABLE alcance AS SELECT * FROM alcance_df")
    con.register("obras_sede_df", obras_sede)
    con.execute("CREATE TABLE obras_sede AS SELECT * FROM obras_sede_df")
    anios = [r[0] for r in con.execute("SELECT DISTINCT anio FROM base ORDER BY 1").fetchall()]

    # ---------------- montos ilegibles (RP-08): ningún monto con texto puede perderse en silencio
    inval = con.execute("SELECT anio, sum(montos_invalidos), sum(filas) FROM base GROUP BY 1 ORDER BY 1").fetchall()
    res.prueba("G-11", "Ningún monto ilegible en los CSV (PIA, PIM, devengado)", all(r[1] == 0 for r in inval),
               {str(a): {"montos_invalidos": int(i), "filas_csv": int(f)} for a, i, f in inval})

    # ---------------- distritos por año (TE-03): un CUI en un distrito que aún no existía va a su distrito de origen
    con.execute(f"""
        CREATE TABLE distrito_anio AS
        SELECT DISTINCT d.ubigeo_inei, a.anio
        FROM dim_ubigeo d, (SELECT unnest({anios}) AS anio) a
        WHERE d.nivel = 'distrito' AND d.anio_datos_desde <= a.anio
          AND (d.anio_datos_hasta IS NULL OR d.anio_datos_hasta >= a.anio)
    """)
    con.execute(f"""CREATE TABLE origen_principal AS SELECT ubigeo_hijo, ubigeo_origen FROM '{i_rel.ruta}'
                    WHERE es_origen_principal""")

    # ---------------- dim_inversion_ubicacion (R-GASTO-02)
    con.execute("""
        CREATE TABLE inv_raw AS
        SELECT lpad(trim(CODIGO_UNICO), 7, '0') AS cui, trim(CODIGO_UNICO) AS codigo_unico_fuente, NULLIF(trim(UBIGEO), '') AS ubigeo, DEPARTAMENTO AS departamento,
               PROVINCIA AS provincia, DISTRITO AS distrito,
               ESTADO AS estado, ANIO_PROCESO AS anio_proceso,
               -- GA-10: campos para listar obras (R-GASTO-14/17)
               NIVEL AS nivel_gobierno_inv, ENTIDAD AS entidad, SEC_EJEC AS sec_ejec_uep, NOMBRE_INVERSION AS nombre_inversion,
               SITUACION AS situacion, FUNCION AS funcion_inv, DES_TIPOLOGIA AS tipologia,
               TRY_CAST(COSTO_ACTUALIZADO AS DOUBLE) AS costo_actualizado,
               TRY_CAST(DEVEN_ACUMUL_ANIO_ANT AS DOUBLE) AS devengado_acumulado_anio_anterior,
               TRY_CAST(DEV_ANIO_ACTUAL AS DOUBLE) AS devengado_anio_actual,
               TRY_CAST(PIM_ANIO_ACTUAL AS DOUBLE) AS pim_anio_actual,
               TRY_CAST(AVANCE_FISICO AS DOUBLE) AS avance_fisico, TRY_CAST(AVANCE_EJECUCION AS DOUBLE) AS avance_ejecucion,
               ULT_FEC_DECLA_ESTIM AS ultima_declaracion_avance, FECHA_VIABILIDAD AS fecha_viabilidad,
               TRY_CAST(NUM_HABITANTES_BENEF AS DOUBLE) AS habitantes_beneficiarios,
               TRY_CAST(LATITUD AS DOUBLE) AS lat, TRY_CAST(LONGITUD AS DOUBLE) AS lon
        FROM read_csv(?, header=true, all_varchar=true, quote='"', escape='"', delim=',', strict_mode=true)
    """, [str(i_inv.ruta)])
    # GA-09: ningún CUI del detalle se pierde. Cada fila recibe un ubigeo efectivo y un método de ubicación:
    #   ubigeo_valido · codigo_antiguo_alias · curado_por_cui · codigo_escindido_contenedor ·
    #   nombre_texto (UBIGEO nulo de un GL, por nombre sin ambigüedad; 21 casos) ·
    #   multidepartamental_mef (99xxxx / «-MUL.DEP-») · sin_ubicacion (con motivo_sin_ubicacion).
    # En el GN, el texto de un UBIGEO nulo suele ser la sede de la entidad (MINEDU → SAN BORJA en 112 colegios de todo el
    # país; MVCS → MIRAFLORES; RREE → LIMA para embajadas): no se usa y el gasto queda en departamento_meta. Usarlo
    # llevaría 72–76 M al año de colegios de otros distritos a San Borja.
    con.execute("CREATE MACRO nrm(x) AS NULLIF(trim(regexp_replace(regexp_replace(upper(strip_accents(coalesce(x, ''))), "
                "'[^A-Z0-9 ]', ' ', 'g'), '\\s+', ' ', 'g')), '')")
    con.register("alias_df", pd.DataFrame({"codigo_fuente": list(ALIAS_UBIGEO_INVERSION),
                                           "ubigeo_inei": list(ALIAS_UBIGEO_INVERSION.values()),
                                           "confianza": [CONFIANZA_ALIAS[k] for k in ALIAS_UBIGEO_INVERSION]}))
    con.register("escindidos_df", pd.DataFrame({"codigo_fuente": list(ESCINDIDOS_UBIGEO),
                                                "ubigeo_contenedor": list(ESCINDIDOS_UBIGEO.values())}))
    curada = pd.DataFrame(yaml.safe_load(i_cur.ruta.read_text(encoding="utf-8")) or [],
                          columns=["cui", "codigo_fuente", "ubigeo_inei", "evidencia", "revisado_dueno"]).astype(
                          {"cui": str, "codigo_fuente": str, "ubigeo_inei": str})
    if curada.cui.duplicated().any():
        raise PapError("inversiones_ubicacion_curada.yaml: CUI repetido")
    con.register("curada_df", curada)
    con.execute("""
        CREATE TABLE nombres_ubigeo AS
        SELECT DISTINCT ubigeo_inei, nivel, nrm(n) AS n
        FROM (SELECT ubigeo_inei, nivel, unnest(list_append(coalesce(nombres_alternos, []), nombre_normalizado)) AS n
              FROM dim_ubigeo WHERE nivel IN ('departamento', 'provincia', 'distrito'))
        WHERE nrm(n) IS NOT NULL
    """)
    con.execute("""
        CREATE TABLE inv_ubic AS
        WITH r AS (
          SELECT r.*, nrm(r.departamento) AS dep_n, nrm(r.provincia) AS prov_n, nrm(r.distrito) AS dist_n,
                 (r.ubigeo LIKE '99%' OR r.departamento = '-MUL.DEP-') AS es_multidep,
                 a.ubigeo_inei AS ubigeo_alias, a.confianza AS confianza_alias,
                 cu.ubigeo_inei AS ubigeo_curado, e.ubigeo_contenedor,
                 u.ubigeo_inei IS NOT NULL AS ubigeo_existe
          FROM inv_raw r LEFT JOIN alias_df a ON a.codigo_fuente = r.ubigeo
          LEFT JOIN curada_df cu ON cu.cui = r.cui AND cu.codigo_fuente = r.ubigeo
          LEFT JOIN escindidos_df e ON e.codigo_fuente = r.ubigeo
          LEFT JOIN ubigeos u ON u.ubigeo_inei = r.ubigeo
          WHERE r.cui IS NOT NULL  -- 67 filas sin CODIGO_UNICO (solo SNIP): no pueden unirse al gasto
        ), dep AS (
          SELECT r.cui, r.ubigeo, list(DISTINCT substr(n.ubigeo_inei, 1, 2)) AS deps FROM r
          JOIN nombres_ubigeo n ON n.nivel = 'departamento' AND n.n = r.dep_n
          WHERE r.ubigeo IS NULL GROUP BY 1, 2
        ), prov AS (
          SELECT r.cui, list(DISTINCT n.ubigeo_inei) AS provs FROM r JOIN dep d USING (cui)
          JOIN nombres_ubigeo n ON n.nivel = 'provincia' AND n.n = r.prov_n AND len(d.deps) = 1
               AND substr(n.ubigeo_inei, 1, 2) = d.deps[1]
          WHERE r.ubigeo IS NULL GROUP BY 1
        ), dist AS (
          SELECT r.cui, list(DISTINCT n.ubigeo_inei) AS dists FROM r JOIN dep d USING (cui) LEFT JOIN prov p USING (cui)
          JOIN nombres_ubigeo n ON n.nivel = 'distrito' AND n.n = r.dist_n AND len(d.deps) = 1
               AND substr(n.ubigeo_inei, 1, 2) = d.deps[1]
               AND (p.provs IS NULL OR len(p.provs) <> 1 OR substr(n.ubigeo_inei, 1, 4) = substr(p.provs[1], 1, 4))
          WHERE r.ubigeo IS NULL GROUP BY 1
        ), x AS (
          SELECT r.*, d.deps, p.provs, t.dists,
            CASE
              WHEN r.ubigeo_existe THEN 'ubigeo_valido'
              WHEN r.ubigeo_alias IS NOT NULL THEN 'codigo_antiguo_alias'
              WHEN r.ubigeo_curado IS NOT NULL THEN 'curado_por_cui'
              WHEN r.ubigeo_contenedor IS NOT NULL THEN 'codigo_escindido_contenedor'
              WHEN r.es_multidep THEN 'multidepartamental_mef'
              WHEN r.ubigeo IS NULL AND r.nivel_gobierno_inv IN {niveles_nombre} AND len(d.deps) = 1
                   AND (len(t.dists) = 1 OR (r.dist_n IS NULL AND len(p.provs) = 1)
                        OR (r.dist_n IS NULL AND r.prov_n IS NULL)) THEN 'nombre_texto'
              ELSE 'sin_ubicacion' END AS metodo_ubicacion
          FROM r LEFT JOIN dep d USING (cui) LEFT JOIN prov p USING (cui) LEFT JOIN dist t USING (cui)
        )
        SELECT x.*,
          CASE metodo_ubicacion
            WHEN 'ubigeo_valido' THEN ubigeo WHEN 'codigo_antiguo_alias' THEN ubigeo_alias
            WHEN 'curado_por_cui' THEN ubigeo_curado WHEN 'codigo_escindido_contenedor' THEN ubigeo_contenedor
            WHEN 'nombre_texto' THEN CASE WHEN len(dists) = 1 THEN dists[1] WHEN len(provs) = 1 THEN provs[1]
                                          ELSE deps[1] || '0000' END
          END AS ubigeo_ef,
          CASE metodo_ubicacion WHEN 'ubigeo_valido' THEN 'alta' WHEN 'codigo_antiguo_alias' THEN confianza_alias
               WHEN 'curado_por_cui' THEN 'media' WHEN 'codigo_escindido_contenedor' THEN 'alta'
               WHEN 'multidepartamental_mef' THEN 'alta'
               WHEN 'nombre_texto' THEN CASE WHEN len(dists) = 1 OR len(provs) = 1 THEN 'media' ELSE 'baja' END
          END AS confianza_ubicacion,
          CASE WHEN metodo_ubicacion <> 'sin_ubicacion' THEN NULL
               WHEN ubigeo IS NOT NULL THEN 'ubigeo_inexistente'
               WHEN dep_n IS NULL THEN 'ubigeo_nulo_sin_texto'
               -- en el GN el texto suele ser la sede de la entidad (MINEDU → SAN BORJA en 112 colegios de todo el país);
               -- hay excepciones correctas (UNJBG Tacna, Estadio Nacional), pero no se distinguen sin revisión humana
               WHEN nivel_gobierno_inv = 'GN' THEN 'ubigeo_nulo_texto_gn_no_fiable'
               WHEN nivel_gobierno_inv = 'GR' THEN 'ubigeo_nulo_texto_gr_no_usado'
               WHEN len(dists) > 1 OR len(provs) > 1 OR len(deps) > 1 THEN 'ubigeo_nulo_nombre_ambiguo'
               ELSE 'ubigeo_nulo_nombre_no_resuelto' END AS motivo_sin_ubicacion
        FROM x
    """.replace("{niveles_nombre}", "(" + ", ".join(f"'{n}'" for n in NIVELES_UBICACION_POR_NOMBRE) + ")"))
    con.execute("""
        CREATE TABLE dim_inversion_ubicacion AS
        WITH v AS (
          SELECT r.*, u.nivel
          FROM inv_ubic r LEFT JOIN ubigeos u ON u.ubigeo_inei = r.ubigeo_ef
        ), g AS (
          SELECT cui, any_value(anio_proceso) AS anio_proceso,
                 list(DISTINCT ubigeo_ef ORDER BY ubigeo_ef) FILTER (WHERE ubigeo_ef IS NOT NULL) AS ubigeos,
                 count(DISTINCT ubigeo_ef) AS n_ubicaciones,
                 count(DISTINCT substr(ubigeo_ef, 1, 4)) AS n_prov, count(DISTINCT substr(ubigeo_ef, 1, 2)) AS n_dep,
                 bool_and(nivel = 'distrito') AS todos_distrito, min(ubigeo_ef) AS u_min,
                 bool_or(metodo_ubicacion = 'multidepartamental_mef') AS es_multidep,
                 -- prioridad si un CUI trae varias filas: el método de mayor confianza
                 CASE WHEN bool_or(metodo_ubicacion = 'ubigeo_valido') THEN 'ubigeo_valido'
                      WHEN bool_or(metodo_ubicacion = 'codigo_antiguo_alias') THEN 'codigo_antiguo_alias'
                      WHEN bool_or(metodo_ubicacion = 'curado_por_cui') THEN 'curado_por_cui'
                      WHEN bool_or(metodo_ubicacion = 'codigo_escindido_contenedor') THEN 'codigo_escindido_contenedor'
                      WHEN bool_or(metodo_ubicacion = 'nombre_texto') THEN 'nombre_texto'
                      WHEN bool_or(metodo_ubicacion = 'multidepartamental_mef') THEN 'multidepartamental_mef'
                      ELSE 'sin_ubicacion' END AS metodo_ubicacion,
                 any_value(confianza_ubicacion) AS confianza_ubicacion,
                 any_value(motivo_sin_ubicacion) AS motivo_sin_ubicacion,
                 any_value(ubigeo) AS ubigeo_fuente, any_value(departamento) AS departamento_txt,
                 any_value(provincia) AS provincia_txt, any_value(distrito) AS distrito_txt,
                 any_value(nombre_inversion) AS nombre_inversion, any_value(estado) AS estado,
                 any_value(situacion) AS situacion, any_value(nivel_gobierno_inv) AS nivel_gobierno_inv,
                 any_value(entidad) AS entidad, any_value(sec_ejec_uep) AS sec_ejec_uep,
                 any_value(funcion_inv) AS funcion_inv, any_value(tipologia) AS tipologia,
                 any_value(costo_actualizado) AS costo_actualizado,
                 any_value(devengado_acumulado_anio_anterior) AS devengado_acumulado_anio_anterior,
                 any_value(devengado_anio_actual) AS devengado_anio_actual, any_value(pim_anio_actual) AS pim_anio_actual,
                 any_value(avance_fisico) AS avance_fisico, any_value(avance_ejecucion) AS avance_ejecucion,
                 any_value(ultima_declaracion_avance) AS ultima_declaracion_avance,
                 any_value(fecha_viabilidad) AS fecha_viabilidad, any_value(habitantes_beneficiarios) AS habitantes_beneficiarios,
                 any_value(lat) AS lat, any_value(lon) AS lon
          FROM v GROUP BY cui
        )
        SELECT cui, ubigeos, n_ubicaciones,
               -- DETALLE_INVERSIONES trae una sola fila por CUI: es la ubicación principal, no todas (GA-02, PR-17)
               n_ubicaciones = 1 AS ubicacion_principal,
               CASE WHEN n_ubicaciones = 0 AND es_multidep THEN 'multidepartamental'
                    WHEN n_ubicaciones = 0 THEN NULL
                    WHEN n_ubicaciones = 1 AND todos_distrito THEN 'distrito'
                    WHEN n_prov = 1 AND (n_ubicaciones > 1 OR u_min LIKE '____00') AND u_min NOT LIKE '__0000' THEN 'provincia'
                    WHEN n_dep = 1 THEN 'departamento'
                    ELSE 'multidepartamental' END AS nivel_comun,
               CASE WHEN n_ubicaciones = 0 AND es_multidep THEN '000000'
                    WHEN n_ubicaciones = 0 THEN NULL
                    WHEN n_ubicaciones = 1 AND todos_distrito THEN u_min
                    WHEN n_prov = 1 AND (n_ubicaciones > 1 OR u_min LIKE '____00') AND u_min NOT LIKE '__0000' THEN substr(u_min, 1, 4) || '00'
                    WHEN n_dep = 1 THEN substr(u_min, 1, 2) || '0000'
                    ELSE '000000' END AS ubigeo_atribucion,
               metodo_ubicacion, confianza_ubicacion,
               CASE WHEN n_ubicaciones = 0 AND NOT es_multidep THEN motivo_sin_ubicacion END AS motivo_sin_ubicacion,
               ubigeo_fuente, departamento_txt, provincia_txt, distrito_txt,
               nombre_inversion, estado, situacion, nivel_gobierno_inv, entidad, sec_ejec_uep, funcion_inv, tipologia,
               costo_actualizado, devengado_acumulado_anio_anterior, devengado_anio_actual, pim_anio_actual,
               avance_fisico, avance_ejecucion, ultima_declaracion_avance, fecha_viabilidad, habitantes_beneficiarios,
               lat, lon, anio_proceso AS fecha_snapshot, ? AS version_tabla
        FROM g ORDER BY cui
    """, [VERSION_INVERSION])
    n_inv = con.execute("SELECT count(DISTINCT cui) FROM inv_raw").fetchone()[0]
    n_dim, n_ok, motivos = con.execute("""
        SELECT count(*), count(*) FILTER (WHERE (nivel_comun IS NULL) <> (motivo_sin_ubicacion IS NULL)),
               list(DISTINCT motivo_sin_ubicacion) FILTER (WHERE motivo_sin_ubicacion IS NOT NULL)
        FROM dim_inversion_ubicacion""").fetchone()
    # G-10 (GA-09, bloqueante, conteo exacto): todo CUI del detalle está en la dimensión con nivel o con motivo
    res.prueba("G-10", "Todo CUI del detalle MEF está en dim_inversion_ubicacion con nivel_comun o motivo_sin_ubicacion",
               n_dim == n_inv and n_ok == n_dim and set(motivos or []) <= MOTIVOS_SIN_UBICACION,
               {"inversiones": n_inv, "en_dimension": n_dim, "con_nivel_o_motivo": n_ok, "motivos": motivos,
                "filas_sin_codigo_unico": con.execute("SELECT count(*) FROM inv_raw WHERE cui IS NULL").fetchone()[0]})
    metodo = con.execute("""SELECT metodo_ubicacion, coalesce(motivo_sin_ubicacion, '-') AS motivo, count(*) AS cui,
                                   round(100.0 * count(*) / sum(count(*)) OVER (), 3) AS pct
                            FROM dim_inversion_ubicacion GROUP BY 1, 2 ORDER BY 3 DESC""").df()
    res.revision["inversiones_por_metodo_ubicacion"] = metodo
    res.prueba("G-20", "CUI con ubigeo válido, alias o curado (≥ 99 %; el resto, con método o motivo)",
               metodo.loc[metodo.metodo_ubicacion.isin(["ubigeo_valido", "codigo_antiguo_alias", "curado_por_cui"]),
                          "cui"].sum() / n_dim >= 0.99,
               dict(zip(metodo.metodo_ubicacion + "/" + metodo.motivo, metodo.cui.astype(int))))
    res.revision["inversiones_sin_ubicar"] = con.execute("""
        SELECT cui, ubigeo_fuente, departamento_txt, provincia_txt, distrito_txt, nivel_gobierno_inv, entidad,
               metodo_ubicacion, confianza_ubicacion, nivel_comun, ubigeo_atribucion, motivo_sin_ubicacion, estado
        FROM dim_inversion_ubicacion WHERE metodo_ubicacion <> 'ubigeo_valido' ORDER BY cui""").df()

    # ---------------- dim_unidad_ejecutora (con ámbito y alcance, GA-01, SP-06)
    con.execute("""
        CREATE TABLE ue AS
        SELECT anio, sec_ejec, any_value(nivel_gobierno) AS nivel_gobierno, any_value(sector_nombre) AS sector_nombre,
               any_value(pliego) AS pliego, any_value(pliego_nombre) AS pliego_nombre,
               any_value(ejecutora_nombre) AS ejecutora_nombre, any_value(ubigeo_sede) AS ubigeo_sede,
               count(DISTINCT ubigeo_sede) AS n_sedes
        FROM base GROUP BY anio, sec_ejec
    """)
    con.execute("""
        CREATE TABLE dim_unidad_ejecutora AS
        SELECT u.*,
               -- En gobiernos locales PLIEGO_NOMBRE viene vacío: el nombre de la municipalidad está en EJECUTORA_NOMBRE
               CASE WHEN u.nivel_gobierno = 'M' AND u.ejecutora_nombre LIKE 'MUNICIPALIDAD DISTRITAL%' THEN 'distrital'
                    WHEN u.nivel_gobierno = 'M' AND (u.ejecutora_nombre LIKE 'MUNICIPALIDAD PROVINCIAL%'
                         OR u.ejecutora_nombre LIKE 'MUNICIPALIDAD METROPOLITANA%') THEN 'provincial'
                    WHEN u.nivel_gobierno = 'M' THEN 'otra' END AS tipo_entidad_local,
               CASE WHEN u.nivel_gobierno = 'E' THEN coalesce(a.alcance, 'sin_clasificar') END AS alcance_ejecutora,
               a.criterio AS criterio_alcance,
               -- Pieza A: marcas del criterio único (false fuera de las UE del nivel E listadas)
               coalesce(a.referencia_nacional, false) AS referencia_nacional,
               coalesce(a.verificar_procedencia, false) AS verificar_procedencia,
               coalesce(a.mixta, false) AS ejecutora_mixta,
               a.confianza_alcance, a.paso_criterio AS paso_criterio_alcance,
               coalesce(a.revisado_dueno, false) AS alcance_revisado_dueno,
               -- P3 (L6): alcance con meta 07 (bloque alcance_callao) y sus marcas
               CASE WHEN u.nivel_gobierno = 'E' THEN coalesce(a.alcance_callao, 'sin_clasificar') END
                 AS alcance_ejecutora_callao,
               a.criterio_callao AS criterio_alcance_callao,
               coalesce(a.mixta_callao, false) AS ejecutora_mixta_callao,
               coalesce(a.verificar_procedencia_callao, false) AS verificar_procedencia_callao,
               coalesce(a.revisado_dueno_callao, false) AS alcance_callao_revisado_dueno,
               a.actividades_nacionales_callao,  -- auditoría de P3: actividades nacionales de una mixta con meta 07
               -- P3 (H-A2, H-08): ámbito por ley del pliego regional (todo su gasto territorializado va a ese ámbito)
               {ambito_pliego} AS ambito_pliego_regional,
               CASE
                 -- Gobierno Regional de Lima → Lima Región (decisión del dueño, 6/10/2026)
                 WHEN u.nivel_gobierno = 'R' AND u.pliego_nombre LIKE 'GOBIERNO REGIONAL%LIMA%'
                      AND u.pliego_nombre NOT LIKE '%METROPOLITANA%' THEN 'LIMA_REGION'
                 -- Pliego regional de la Municipalidad Metropolitana de Lima → Lima Metropolitana (decisión, SP-06)
                 WHEN u.nivel_gobierno = 'R' AND u.pliego_nombre LIKE 'MUNICIPALIDAD METROPOLITANA DE LIMA%'
                      THEN 'LIMA_METROPOLITANA'
                 WHEN a.alcance = 'lima_metropolitana' THEN 'LIMA_METROPOLITANA'
                 WHEN a.alcance = 'lima_region' THEN 'LIMA_REGION'
                 WHEN a.alcance = 'lima_callao' THEN 'AREA_METROPOLITANA_LIMA_CALLAO'
                 -- lima_departamento (E3): sin ámbito; con meta 15 va a 150000 y cuenta en Lima
               END AS ambito_id
        FROM ue u LEFT JOIN alcance a ON a.sec_ejec = u.sec_ejec
        ORDER BY u.anio, u.sec_ejec
    """.replace("{ambito_pliego}", sql_ambito_pliego_regional("u.nivel_gobierno", "u.pliego_nombre")))
    con.execute("ALTER TABLE dim_unidad_ejecutora ADD COLUMN sede_valida BOOLEAN")
    con.execute("UPDATE dim_unidad_ejecutora SET sede_valida = ubigeo_sede IN (SELECT ubigeo_inei FROM ubigeos WHERE nivel = 'distrito')")
    mun = con.execute("""SELECT count(*), sum(sede_valida::INT) FROM dim_unidad_ejecutora
                         WHERE tipo_entidad_local IN ('distrital','provincial')""").fetchone()
    res.prueba("G-05", "Municipalidades distritales y provinciales con sede en un distrito válido (≥ 99 %)",
               mun[0] > 0 and mun[1] / mun[0] >= 0.99, {"municipalidades_anio": mun[0], "validas": mun[1]})
    amb = con.execute("""SELECT ambito_id, list(DISTINCT pliego_nombre ORDER BY pliego_nombre) FROM dim_unidad_ejecutora
                         WHERE nivel_gobierno = 'R' AND ambito_id IS NOT NULL GROUP BY 1 ORDER BY 1""").fetchall()
    res.prueba("G-06", "GR Lima → Lima Región y pliego regional de la Municipalidad de Lima → Lima Metropolitana",
               {a for a, _ in amb} == {"LIMA_REGION", "LIMA_METROPOLITANA"}, {a: p for a, p in amb})

    # ---------------- atribución territorial (R-GASTO-01)
    con.execute("""
        CREATE TABLE atribuida AS
        -- Pieza A: sin las columnas de nombre (la fact las toma de tablas de nombres por año y código, más abajo):
        -- con la actividad y la fuente en la clave, llevarlas aquí agotaba la memoria y el disco temporal
        SELECT b.* EXCLUDE (cui_join, sector_nombre, pliego_nombre, ejecutora_nombre, programa_ppto_nombre,
                            producto_proyecto_nombre, actividad_accion_obra_nombre, generica_nombre,
                            fuente_financiamiento_nombre, rubro_nombre, clasificador_transferencia_nombre),
               i.nivel_comun AS inv_nivel,
               -- TE-03: si el distrito del CUI aún no existía ese año, se usa su distrito de origen principal
               CASE WHEN i.nivel_comun = 'distrito' AND da.ubigeo_inei IS NULL
                    THEN coalesce(op.ubigeo_origen, i.ubigeo_atribucion) ELSE i.ubigeo_atribucion END AS inv_ubigeo,
               i.nivel_comun = 'distrito' AND da.ubigeo_inei IS NULL AS inv_redirigido_origen,
               d.tipo_entidad_local, d.sede_valida, d.ambito_id AS ambito_ue, d.alcance_ejecutora,
               d.referencia_nacional, d.verificar_procedencia, d.ejecutora_mixta,
               d.alcance_ejecutora_callao, d.ejecutora_mixta_callao, d.verificar_procedencia_callao,  -- P3 (L6)
               d.actividades_nacionales_callao,
               d.ambito_pliego_regional AS ambito_pliego,                                              -- P3 (H-A2)
               -- clasificador de gasto: genérica (2.x) o, en 2.4, el código completo (GA-05)
               coalesce(b.clasificador_transferencia, b.tipo_transaccion || '.' || b.generica) AS clasificador_gasto,
               CASE WHEN b.clasificador_transferencia IS NOT NULL THEN 'especifica_detalle' ELSE 'generica' END
                 AS nivel_clasificador,
          CASE
            -- GA-02: DETALLE solo trae la ubicación principal del CUI. Si un proyecto del GN o de un GORE tiene su
            -- ubicación en otro departamento que su meta, es una obra que cruza departamentos (Línea 2 Lima-Callao,
            -- carreteras): no se carga a un distrito ni vuelve a la meta (repetiría el sesgo de sede, GA-01)
            WHEN b.tipo_act_proy ILIKE 'PROYECTO%' AND i.nivel_comun IN ('distrito', 'provincia', 'departamento')
                 AND b.nivel_gobierno IN ('E', 'R') AND b.departamento_meta BETWEEN '01' AND '25'
                 AND substr(i.ubigeo_atribucion, 1, 2) <> b.departamento_meta THEN 'nacional_multidepartamental'
            WHEN b.tipo_act_proy ILIKE 'PROYECTO%' AND i.nivel_comun = 'distrito' THEN 'distrito_inversion'
            WHEN b.tipo_act_proy ILIKE 'PROYECTO%' AND i.nivel_comun = 'provincia' THEN 'provincia_inversion'
            WHEN b.tipo_act_proy ILIKE 'PROYECTO%' AND i.nivel_comun = 'departamento' THEN 'departamento_inversion'
            WHEN d.tipo_entidad_local = 'distrital' AND d.sede_valida THEN 'distrito_municipal'
            WHEN d.tipo_entidad_local = 'provincial' AND d.sede_valida THEN 'provincia_municipal'
            WHEN b.funcion = 'DEUDA PUBLICA'
              OR (b.funcion = 'PREVISION SOCIAL' AND b.nivel_gobierno = 'E')
              OR (b.funcion = 'PLANEAMIENTO, GESTION Y RESERVA DE CONTINGENCIA' AND b.nivel_gobierno = 'E' AND b.departamento_meta = '15')
              THEN 'nacional_no_territorializable'
            -- GA-09: proyecto «-MUL.DEP-» (UBIGEO 99xxxx) del GN o de un GORE → multidepartamental, no a la meta
            -- (en 2025, 304 M iban a departamento_meta, 209 M de ellos a Lima). Las municipalidades que ejecutan un CUI
            -- multidepartamental (p. ej. 2340601, PATS) siguen en su sede: ya salieron por las ramas municipales.
            WHEN b.tipo_act_proy ILIKE 'PROYECTO%' AND i.nivel_comun = 'multidepartamental'
                 AND b.nivel_gobierno IN ('E', 'R') {filtro_multidep} THEN 'nacional_multidepartamental'
            WHEN b.departamento_meta BETWEEN '01' AND '25' THEN 'departamento_meta'
            ELSE 'nacional_no_territorializable'
          END AS nivel_atribucion,
          -- GA-02: el CUI se ubica por su ubicación principal; se marca si su departamento no coincide con la meta
          CASE WHEN b.tipo_act_proy ILIKE 'PROYECTO%' AND i.nivel_comun IN ('distrito', 'provincia', 'departamento') THEN
               CASE WHEN substr(i.ubigeo_atribucion, 1, 2) = b.departamento_meta THEN 'coincide' ELSE 'distinto_departamento' END
          END AS consistencia_meta,
          i.metodo_ubicacion, i.motivo_sin_ubicacion,
          b.cui_join IS NOT NULL AND i.cui IS NULL AS cui_fuera_del_detalle
        FROM (SELECT *, CASE WHEN tipo_act_proy ILIKE 'PROYECTO%' THEN lpad(producto_proyecto, 7, '0') END AS cui_join
              FROM base) b
        LEFT JOIN dim_inversion_ubicacion i ON i.cui = b.cui_join
        LEFT JOIN distrito_anio da ON da.ubigeo_inei = i.ubigeo_atribucion AND da.anio = b.anio
        LEFT JOIN origen_principal op ON op.ubigeo_hijo = i.ubigeo_atribucion
        LEFT JOIN dim_unidad_ejecutora d ON d.anio = b.anio AND d.sec_ejec = b.sec_ejec
    """.replace("{filtro_multidep}", FILTRO_MULTIDEP))
    # GA-07: fecha de corte de los datos (último mes con devengado) y si el año está cerrado
    # el año está cerrado si el archivo es el anual (-Gasto.csv) o si se descargó en un año posterior (no depende
    # de la fecha de construcción)
    cerrado = {a: (not r["original_filename"].endswith("-Mensual.csv")) or int(r["retrieved_at"][:4]) > a
               for a, r in arch.items()}
    con.register("cerrado_df", pd.DataFrame({"anio": list(cerrado), "es_anio_cerrado": list(cerrado.values())}))
    con.execute("""CREATE TABLE corte AS SELECT b.anio, max(b.mes) FILTER (WHERE b.devengado <> 0) AS mes_max,
                   any_value(c.es_anio_cerrado) AS es_anio_cerrado
                   FROM base b JOIN cerrado_df c USING (anio) GROUP BY b.anio""")
    # Pieza A: nombres por año y código (un código tiene un solo nombre por año; G-25b lo verifica)
    for tabla_n, cod, nom in NOMBRES_FACT:
        con.execute(f"""CREATE TABLE {tabla_n} AS SELECT anio, {cod}, min({nom}) AS {nom}, count(DISTINCT {nom}) AS n_nombres
                        FROM base WHERE {cod} IS NOT NULL GROUP BY ALL""")
    con.execute(sql_fact())
    con.execute("""
        CREATE VIEW fact_con_nombres AS
        SELECT f.* EXCLUDE (pia, pim, devengado, fecha_corte_datos, es_anio_cerrado),
               a.actividad_accion_obra_nombre, g.generica_nombre, c.clasificador_transferencia_nombre AS clasificador_gasto_nombre,
               fu.fuente_financiamiento_nombre, r.rubro_nombre,
               f.pia, f.pim, f.devengado, f.fecha_corte_datos, f.es_anio_cerrado
        FROM fact f
        LEFT JOIN nom_actividad a USING (anio, actividad_accion_obra)
        LEFT JOIN nom_generica g USING (anio, generica)
        LEFT JOIN nom_clasificador c ON c.anio = f.anio AND c.clasificador_transferencia = f.clasificador_gasto
        LEFT JOIN nom_fuente fu USING (anio, fuente_financiamiento)
        LEFT JOIN nom_rubro r USING (anio, rubro)""")
    # Clave única: primero por huella (barato en memoria); solo si hay choques se cuenta con la clave completa
    dup = con.execute(f"""SELECT count(*) FROM (SELECT hash({', '.join(CLAVE_FACT)}) h, count(*) n FROM fact
                          GROUP BY h HAVING n > 1)""").fetchone()[0]
    if dup:
        dup = con.execute(f"""SELECT count(*) FROM (SELECT {', '.join(CLAVE_FACT)}, count(*) n FROM fact
                              GROUP BY ALL HAVING n > 1)""").fetchone()[0]
    res.prueba("G-14", "fact_gasto_territorial: la clave es única (incluye ámbito y ejecutora)", dup == 0, dup)
    # G-17c (GA-05): el fact conserva cada bloque, y las vistas del motor reparten el total sin solaparse
    con.execute("CREATE VIEW fact_gasto_territorial AS SELECT * FROM fact_con_nombres")  # = Parquet publicado
    con.execute(i_vis.ruta.read_text(encoding="utf-8"))
    # Cada total se agrega por año por separado (sin subconsultas correlacionadas): mismo resultado, poca memoria
    blq = con.execute("""
        WITH b AS (SELECT anio, sum(devengado) AS base_total,
                          coalesce(sum(devengado) FILTER (WHERE bloque_consolidado = 'entregado_fuera_del_presupuesto'), 0)
                            AS base_b
                   FROM base GROUP BY anio),
             f AS (SELECT anio, sum(devengado) AS fact_total,
                          coalesce(sum(devengado) FILTER (WHERE bloque_consolidado = 'excluir_intergubernamental'), 0)
                            AS inter
                   FROM fact GROUP BY anio),
             t AS (SELECT anio, sum(devengado) AS tematico FROM v_gasto_tematico GROUP BY anio),
             c AS (SELECT anio, sum(gasto_final_devengado) AS cons_final,
                          sum(entregado_fuera_del_presupuesto_devengado) AS cons_b
                   FROM v_gasto_consolidado GROUP BY anio),
             o AS (SELECT anio, sum(devengado) AS fondos FROM v_gasto_fondos_por_identificar GROUP BY anio)
        SELECT f.anio, b.base_total, f.fact_total, coalesce(t.tematico, 0), coalesce(c.cons_final, 0),
               coalesce(c.cons_b, 0), coalesce(o.fondos, 0), f.inter, b.base_b
        FROM f LEFT JOIN b USING (anio) LEFT JOIN t USING (anio) LEFT JOIN c USING (anio) LEFT JOIN o USING (anio)
        ORDER BY f.anio""").fetchall()
    res.prueba("G-17c", "Vistas del motor: temático = gasto final consolidado; gasto final + (b) + fondos + (a) = total "
               "del fact = total de la base; (b) del fact = (b) de la base (tolerancia 0)",
               all(bt == ft == tm + cb + fo + it and tm == cf and cb == bb for _, bt, ft, tm, cf, cb, fo, it, bb in blq),
               {str(r[0]): {"tematico": str(r[3]), "entregado_fuera": str(r[5]), "fondos": str(r[6]),
                            "intergub": str(r[7])} for r in blq})
    cons = con.execute("""
        SELECT b.anio, b.dev, f.dev, b.pim, f.pim FROM
          (SELECT anio, sum(devengado) dev, sum(pim) pim FROM base GROUP BY anio) b
          JOIN (SELECT anio, sum(devengado) dev, sum(pim) pim FROM fact GROUP BY anio) f USING (anio)
        ORDER BY anio""").fetchall()
    for anio, bd, fd, bp, fp in cons:
        res.prueba("G-01", f"{anio}: Σ por niveles de atribución = total nacional del archivo (devengado y PIM, tolerancia 0)",
                   bd == fd and bp == fp, {"devengado": str(bd), "atribuido": str(fd)})
    res.revision["gasto_por_nivel_atribucion"] = con.execute("""
        SELECT anio, nivel_atribucion, round(sum(devengado)/1e6, 1) AS devengado_millones
        FROM fact GROUP BY 1, 2 ORDER BY 1, 3 DESC""").df()

    # ---------------- Pieza A (rondas 1-2): campos nuevos, conservación por actividad y fuente, y línea aparte de Lima
    nulos = con.execute("""
        SELECT count(*) FILTER (WHERE actividad_accion_obra IS NULL OR actividad_accion_obra_nombre IS NULL),
               count(*) FILTER (WHERE clasificador_gasto IS NULL OR generica_nombre IS NULL
                                OR (nivel_clasificador = 'especifica_detalle') <> (generica = '4')
                                OR (generica = '4' AND clasificador_gasto_nombre IS NULL)),
               count(*) FILTER (WHERE fuente_financiamiento IS NULL OR fuente_financiamiento_nombre IS NULL
                                OR rubro IS NULL OR rubro_nombre IS NULL),
               count(*) FILTER (WHERE grupo_funcional IS NULL OR categoria_gasto IS NULL),
               count(*) FILTER (WHERE referencia_nacional IS NULL OR verificar_procedencia IS NULL
                                OR ejecutora_mixta IS NULL OR cuenta_en_lima IS NULL OR obra_sede_nacional IS NULL
                                OR cuenta_en_ambito IS NULL)
        FROM fact_con_nombres""").fetchone()
    res.prueba("G-25", "Actividad, clasificador de gasto, fuente/rubro, grupo funcional y marcas de alcance presentes y "
               "no nulos en toda fila de fact_gasto_territorial",
               not any(nulos), dict(zip(["actividad", "clasificador", "fuente_rubro", "grupo_categoria", "marcas"], nulos)))
    varios = {t: con.execute(f"SELECT count(*) FROM {t} WHERE n_nombres > 1").fetchone()[0] for t, _, _ in NOMBRES_FACT}
    res.prueba("G-25b", "Un solo nombre por año y código (actividad, genérica, clasificador 2.4, fuente, rubro)",
               not any(varios.values()), varios, bloqueante=False)
    llave = "anio, sec_ejec, actividad_accion_obra, fuente_financiamiento, rubro, clasificador_gasto"
    dif_act = con.execute(f"""
        WITH b AS (SELECT anio, sec_ejec, actividad_accion_obra, fuente_financiamiento, rubro,
                          coalesce(clasificador_transferencia, tipo_transaccion || '.' || generica) AS clasificador_gasto,
                          sum(pim) AS pim, sum(devengado) AS dev FROM base GROUP BY ALL),
             f AS (SELECT {llave}, sum(pim) AS pim, sum(devengado) AS dev FROM fact GROUP BY ALL)
        SELECT count(*) FROM b FULL JOIN f USING ({llave})
        WHERE b.pim IS DISTINCT FROM f.pim OR b.dev IS DISTINCT FROM f.dev""").fetchone()[0]
    res.prueba("G-26", "Conservación exacta por año × ejecutora × actividad × fuente × rubro × clasificador (PIM y "
               "devengado, base = fact)", dif_act == 0, {"llaves_con_diferencia": dif_act})
    refnac_yaml = sorted(alcance.loc[alcance.referencia_nacional, "sec_ejec"])
    pruebas_ambito(con, res, refnac_yaml, len(obras_sede))

    # GA-02: proyectos cuyo CUI está en otro departamento que la meta
    res.revision["inversiones_meta_distinta"] = con.execute("""
        SELECT anio, nivel_gobierno, sec_ejec, producto_proyecto AS cui, departamento_meta, ubigeo_atribucion,
               round(sum(devengado)/1e6, 2) AS devengado_millones
        FROM fact WHERE consistencia_meta = 'distinto_departamento'
        GROUP BY ALL HAVING sum(devengado) > 0
        ORDER BY anio, devengado_millones DESC, sec_ejec, cui, departamento_meta, ubigeo_atribucion, nivel_gobierno""").df()
    conc = con.execute("""
        SELECT f.anio, f.ubigeo_atribucion, f.producto_proyecto, sum(f.devengado) AS d,
               sum(sum(f.devengado)) OVER (PARTITION BY f.anio, f.ubigeo_atribucion) AS total_distrito
        FROM fact f WHERE f.nivel_atribucion IN ('distrito_inversion', 'distrito_municipal')
        GROUP BY 1, 2, 3""").df()
    conc = conc[(conc.total_distrito > 0) & (conc.d / conc.total_distrito > 0.5)]
    gn = con.execute("""SELECT DISTINCT anio, producto_proyecto FROM fact
                        WHERE nivel_atribucion = 'distrito_inversion' AND nivel_gobierno = 'E'""").df()
    conc = conc.merge(gn, on=["anio", "producto_proyecto"])
    conc = conc[conc.d > 10_000_000]
    res.revision["distritos_dominados_por_un_cui_nacional"] = conc.assign(
        pct=(conc.d / conc.total_distrito).round(3)).sort_values(["anio", "d"], ascending=[True, False])
    res.prueba("G-13", "Revisión: distritos donde un solo CUI del Gobierno Nacional (> S/ 10 M) es más de la mitad de su gasto",
               True, {"casos": len(conc)}, bloqueante=False)
    multi = con.execute("""SELECT anio, round(sum(devengado)/1e6, 1),
                                  round(sum(devengado) FILTER (WHERE metodo_ubicacion_cui = 'multidepartamental_mef')/1e6, 1)
                           FROM fact WHERE nivel_atribucion = 'nacional_multidepartamental' GROUP BY 1 ORDER BY 1""").fetchall()
    res.prueba("G-16", "nacional_multidepartamental: proyectos del GN/GORE con CUI en otro departamento que la meta "
               "(GA-02) y «-MUL.DEP-» del GN/GORE (GA-09) con el filtro de meta [" + (FILTRO_MULTIDEP or "ninguno") +
               "] (millones: total y parte «-MUL.DEP-»; revisión en inversiones_meta_distinta.csv)", True,
               {str(a): {"total": float(m), "mul_dep": float(md or 0)} for a, m, md in multi}, bloqueante=False)

    # GA-09: ningún CUI del detalle se pierde al atribuir. Se compara como número (no con el lpad que arma la unión):
    # una fila de proyecto cuyo código, leído como entero, está en el detalle debe llegar con método de ubicación.
    perdidos = con.execute("""
        SELECT count(*), coalesce(sum(devengado), 0) FROM atribuida a
        WHERE a.tipo_act_proy ILIKE 'PROYECTO%' AND a.metodo_ubicacion IS NULL
          AND TRY_CAST(trim(a.producto_proyecto) AS BIGINT) IN
              (SELECT TRY_CAST(codigo_unico_fuente AS BIGINT) FROM inv_raw WHERE codigo_unico_fuente IS NOT NULL)
    """).fetchone()
    res.prueba("G-21", "Todo proyecto cuyo CUI (como número) está en el detalle MEF llega con método de ubicación",
               perdidos[0] == 0, {"filas_sin_unir": perdidos[0], "devengado": str(perdidos[1])})
    no_gl_texto = con.execute("""SELECT count(*) FILTER (WHERE nivel_gobierno_inv = 'GN'), count(*)
                                 FROM dim_inversion_ubicacion
                                 WHERE metodo_ubicacion = 'nombre_texto' AND nivel_gobierno_inv <> 'GL'""").fetchone()
    res.prueba("G-22", "Solo los CUI de gobiernos locales se ubican por el texto DEPARTAMENTO/PROVINCIA/DISTRITO "
               "(en el GN suele ser la sede; en el GORE no está autorizado)",
               no_gl_texto[1] == 0, {"cui_gn_por_texto": no_gl_texto[0], "cui_no_gl_por_texto": no_gl_texto[1]})
    malos_cur = con.execute("""
        SELECT list(c.cui) FROM curada_df c
        LEFT JOIN escindidos_df e ON e.codigo_fuente = c.codigo_fuente
        WHERE c.cui NOT IN (SELECT cui FROM inv_raw WHERE ubigeo = c.codigo_fuente)
           OR c.ubigeo_inei NOT IN (SELECT ubigeo_inei FROM ubigeos WHERE nivel = 'distrito')
           OR e.ubigeo_contenedor IS NULL OR substr(c.ubigeo_inei, 1, 4) <> substr(e.ubigeo_contenedor, 1, 4)
    """).fetchone()[0] or []
    res.prueba("G-24", "Ubicación curada por CUI: el CUI trae ese código escindido y el destino es un distrito de la "
               "provincia contenedora (para 160109, un distrito de 1608; no necesariamente uno de sus sucesores)",
               len(malos_cur) == 0, {"cui_mal_curados": malos_cur})
    met = con.execute("""
        SELECT anio, coalesce(metodo_ubicacion, 'cui_fuera_del_detalle') AS metodo,
               round(100 * sum(devengado) / sum(sum(devengado)) OVER (PARTITION BY anio), 2) AS pct_devengado_proyectos,
               round(sum(devengado) / 1e6, 1) AS devengado_millones
        FROM atribuida WHERE tipo_act_proy ILIKE 'PROYECTO%' GROUP BY 1, 2 ORDER BY 1, 3 DESC""").df()
    res.revision["gasto_proyectos_por_metodo_ubicacion"] = met
    res.prueba("G-23", "Revisión: % del devengado en proyectos por método de ubicación del CUI", True,
               {f"{a}/{m}": float(p) for a, m, p in met[["anio", "metodo", "pct_devengado_proyectos"]].itertuples(index=False)},
               bloqueante=False)

    # % del gasto en proyectos ubicado por CUI (G-04) y comparabilidad entre años (GA-03)
    cob = con.execute("""
        SELECT anio, sum(devengado) FILTER (WHERE nivel_atribucion LIKE '%_inversion') / nullif(sum(devengado), 0) AS cobertura
        FROM atribuida WHERE tipo_act_proy ILIKE 'PROYECTO%' GROUP BY anio ORDER BY anio""").df()
    cob["cobertura"] = cob.cobertura.astype(float).round(4)
    cob["comparable_con_anterior"] = cob.cobertura.diff().abs().le(SALTO_COBERTURA_PP) | cob.cobertura.diff().isna()
    res.revision["cobertura_cui"] = cob
    res.prueba("G-04", f"Devengado en proyectos ubicado por CUI ≥ {COBERTURA_CUI_MIN:.0%} cada año (las series de "
               "inversión distrital entre años con > 5 pp de diferencia se marcan no comparables)",
               (cob.cobertura >= COBERTURA_CUI_MIN).all(),
               {"cobertura": dict(zip(cob.anio.astype(str), cob.cobertura)),
                "no_comparables": cob.loc[~cob.comparable_con_anterior, "anio"].astype(int).tolist()},
               bloqueante=False)

    # PIA nacional: control contra la Ley de Presupuesto (detecta PIA repetido por mes) — bloqueante (RP-08)
    pia = dict(con.execute("SELECT anio, sum(pia)/1e6 FROM base GROUP BY anio").fetchall())
    difs = {a: round(float(pia[a]) / PIA_LEY_MILLONES[a] - 1, 4) for a in pia if a in PIA_LEY_MILLONES}
    res.prueba("G-07", "PIA nacional del archivo = PIA de la Ley de Presupuesto (± 0,5 %)",
               set(pia) <= set(PIA_LEY_MILLONES) and all(abs(d) <= 0.005 for d in difs.values()),
               {"diferencia_relativa": difs, "pia_archivo_millones": {a: round(float(v), 1) for a, v in pia.items()}})

    # Transferencias (R-GASTO-05 v4, GA-05): lista curada; pruebas G-15, G-15b, G-17, G-17b, G-18 y G-18b
    res.revision["transferencias"] = con.execute("""
        SELECT anio, clasificador_transferencia, any_value(clasificador_transferencia_nombre) AS nombre,
               categoria_transferencia, excepcion_transferencia, nivel_gobierno, count(DISTINCT sec_ejec) AS ejecutoras,
               round(sum(pim)/1e6, 2) AS pim_millones, round(sum(devengado)/1e6, 2) AS devengado_millones
        FROM base WHERE generica = '4' GROUP BY 1, 2, 4, 5, 6 ORDER BY 1, 2, 4, 5, 6""").df()
    tr.pruebas(con, lista_tr, res.prueba)

    # Conciliación con la Consulta Amigable (R-GASTO-04) — bloqueante, también si faltan las cifras de control
    concilia = con.execute("""SELECT anio, nivel_gobierno, sum(pim)::DOUBLE AS pim_archivo,
                                     sum(devengado)::DOUBLE AS devengado_archivo
                              FROM base GROUP BY 1, 2 ORDER BY 1, 2""").df()
    ctl = yaml.safe_load(i_ctl.ruta.read_text(encoding="utf-8"))
    tol = float(ctl["tolerancia_relativa"])
    c = pd.DataFrame(ctl["cifras"]).rename(columns={"pim": "pim_control", "devengado": "devengado_control"})
    concilia = concilia.merge(c, on=["anio", "nivel_gobierno"], how="outer")
    concilia["dif_rel_pim"] = (concilia.pim_archivo / concilia.pim_control - 1).round(6)
    concilia["dif_rel_devengado"] = (concilia.devengado_archivo / concilia.devengado_control - 1).round(6)
    maxdif = float(concilia[["dif_rel_pim", "dif_rel_devengado"]].abs().max().max())
    completo = bool(concilia[["pim_control", "pim_archivo"]].notna().all().all())
    res.prueba("G-08", f"Conciliación con la Consulta Amigable por año × nivel de gobierno (≤ {tol:.1%})",
               completo and maxdif <= tol, {"max_dif_relativa": round(maxdif, 6), "completo": completo,
                                            "fuente": ctl["fuente"]})
    estrictos = concilia[concilia.dif_rel_devengado.abs() > TOL_CONCILIACION_ESTRICTA]
    res.prueba("G-08b", "Conciliación estricta (≤ 0,05 %; GA-06): año × nivel con diferencia mayor, a explicar",
               estrictos.empty, estrictos[["anio", "nivel_gobierno", "dif_rel_devengado"]].to_dict("records"),
               bloqueante=False)
    res.revision["conciliacion_consulta_amigable"] = concilia

    # ---------------- pieza C: capa de trazabilidad, dim_tema_gasto v1.2 (R-GASTO-08, 08b, 09) y glosario v2
    traz = traza.construir(con, rutas, res, anios, CONTROLES_R2)
    for nombre in ("dim_tema_gasto", "rel_concepto_grupo", "rel_concepto_nodo", "rel_programa_social_ejecutora",
                   "rel_programa_social_linea_aparte"):
        con.register("t_df", traz[nombre])
        con.execute(f"CREATE OR REPLACE TABLE {nombre} AS SELECT * FROM t_df")
        con.unregister("t_df")
    con.execute(i_vtem.ruta.read_text(encoding="utf-8"))
    traza.pruebas_temas(con, res, traz["dim_tema_gasto"], anios, traz["dim_programa"], CONTROLES_R2)
    # revisión: monto por tema y año (millones, gasto final). Cadenas por función y programa en un solo recorrido;
    # conceptos y programas sociales desde la vista (alcances que NO se suman entre sí)
    agg = con.execute("""SELECT anio, funcion, division_funcional, programa_ppto, sum(devengado)::DOUBLE AS dev
                         FROM v_gasto_tematico GROUP BY ALL""").df()
    tem = traz["dim_tema_gasto"]
    filas = []
    for t in tem.itertuples():
        if t.cadena in ("concepto", "programa_social"):
            continue
        x = agg[agg.anio == t.anio]
        for c in ("funcion", "division_funcional", "programa_ppto"):
            if getattr(t, c) is not None and not pd.isna(getattr(t, c)):
                x = x[x[c] == getattr(t, c)]
        filas.append((t.anio, t.tema_id, t.cadena, float(x.dev.sum())))
    otros = con.execute("""SELECT anio, tema_id, cadena, sum(devengado)::DOUBLE FROM v_gasto_tema_interna
                           WHERE cadena IN ('concepto', 'programa_social') GROUP BY ALL""").fetchall()
    mt = pd.DataFrame(filas + otros, columns=["anio", "tema_id", "cadena", "dev"])
    mt = mt.groupby(["anio", "tema_id", "cadena"], as_index=False).dev.sum()
    mt["devengado_millones"] = (mt.dev / 1e6).round(1)
    res.revision["dim_tema_gasto_montos"] = mt.drop(columns="dev").merge(
        tem.drop_duplicates(["anio", "tema_id"])[["anio", "tema_id", "alternativa_de", "comparable_con_anio_anterior",
                                                    "motivo_quiebre"]], how="left").sort_values(["tema_id", "anio"])
    res.revision["concepto_serie"] = con.execute("""
        SELECT concepto_id, anio, round(sum(devengado)/1e6, 1) AS devengado_millones FROM v_gasto_concepto
        GROUP BY 1, 2 ORDER BY 1, 2""").df().merge(
        traz["cobertura_por_anio"][["concepto_id", "anio", "comparable_con_anio_anterior", "motivo_quiebre"]], how="left")
    # G-09: el PP cuenta como presente solo con devengado > 0 (GA-04: el PP 0001 de 2023 trae filas en 0)
    pan = con.execute("""SELECT anio, string_agg(DISTINCT programa_ppto, '+' ORDER BY programa_ppto) FROM base
                         WHERE programa_ppto IN ('0001', '1001') GROUP BY anio, programa_ppto HAVING sum(devengado) > 0
                         """).fetchall()
    pan = pd.DataFrame(pan, columns=["anio", "pp"]).groupby("anio").pp.agg(lambda s: "+".join(sorted(s))).to_dict()
    res.prueba("G-09", "Quiebre del PAN identificado (años con devengado en PP 0001 y/o 1001)", len(pan) > 0,
               pan, bloqueante=False)

    # ---------------- salida: fact directo desde DuckDB (DECIMAL exacto), el resto como DataFrame
    import os
    tmp = carpeta_base(rutas) / f"fact_gasto_territorial.{os.getpid()}.parquet"  # salida.guardar lo mueve
    con.execute("SET threads=1")
    # Pieza A: con la actividad y la fuente la fact crece ~65 %; ordenarla entera agotaba el disco temporal. Se libera
    # la tabla intermedia, se ordena cada año por separado (anio es la primera columna de la clave) y se concatenan
    # en orden: el resultado es el mismo orden total por CLAVE_FACT, con un solo hilo (Parquet determinista).
    for t_ in ("atribuida", "inv_raw", "inv_ubic", "nombres_ubigeo", "distrito_anio"):
        con.execute(f"DROP TABLE IF EXISTS {t_}")
    partes = []
    for anio in anios:
        parte = tmp.with_name(f"{tmp.stem}.{anio}.parquet")
        con.execute(f"""COPY (SELECT *, '{VERSION_TABLA}' AS version_tabla FROM fact_con_nombres WHERE anio = {int(anio)}
                              ORDER BY {', '.join(CLAVE_FACT)})
                        TO '{parte}' (FORMAT parquet, COMPRESSION zstd)""")
        partes.append(parte)
    con.execute("SET preserve_insertion_order=true")
    try:
        con.execute(f"""COPY (SELECT * FROM read_parquet([{', '.join(f"'{x}'" for x in partes)}]))
                        TO '{tmp}' (FORMAT parquet, COMPRESSION zstd)""")
    finally:
        for x in partes:
            x.unlink(missing_ok=True)
    res.tablas = {
        "dim_unidad_ejecutora": con.execute("SELECT *, ? AS version_tabla FROM dim_unidad_ejecutora", [VERSION_TABLA]).df(),
        "dim_inversion_ubicacion": con.execute("SELECT * FROM dim_inversion_ubicacion").df(),
        **traz,
        "fact_gasto_territorial": tmp,
    }
    con.close()
    return res
