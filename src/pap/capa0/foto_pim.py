"""Foto mensual del PIM (pieza D de las decisiones del gasto, rondas 1-2; decisión 12 del dueño, 7/10/2026).

El MEF no publica el PIM mes a mes: cada descarga de {anio}-Gasto-Mensual.csv trae el PIA y el PIM vigentes a su
fecha de corte (en MES_EJE = 0) y el devengado por mes. Desde 2026 se registra una descarga por mes en la receta
MEF-FOTO-PIM-MENSUAL y de cada captura se extrae una tabla compacta `foto_pim` (R-GASTO-05, 07, 18, 19 y 21).

Llave de la foto (v1.1, auditoría de la pieza D, H2): (anio, mes_ref).
  * fecha_ref = la fecha «actualizado» declarada por la página del recurso (--corte, base `declarada`) o, sin ella,
    la fecha de consulta de la captura (`retrieved_at`, base `fecha_consulta`).
  * mes_ref = el último mes de `anio` que terminó ANTES de fecha_ref (el último mes cerrado que cubre la foto).
    Una descarga del 2/10/2026 → mes_ref 9; la del 5/1/2027 del archivo 2026 → 12; la del 3/12/2026 → 11. Así no
    chocan diciembre y enero y la foto (anio, m) se empareja con Σ devengado(MES_EJE ≤ m), como pide R-GASTO-07.
    mes_ref = 0 si fecha_ref cae en enero del mismo año (ningún mes cerrado).
  * Controles: el archivo debe traer devengado del mes_ref (si no, está desactualizado: pasa --corte) y no más allá de
    mes_ref + 1 (si no, la fecha de corte es incoherente). Con o sin --corte, una descarga de los primeros días del mes
    da el mismo mes_ref.
  * Se guardan también fecha_corte (data_cutoff de la captura), mes_descarga (AAAA-MM de la consulta) y
    mes_max_devengado.

Columnas de línea, con los mismos nombres y valores que la base de capa0/gasto.py (para unir con la fact, con
dim_tema_gasto y con transferencias.registrar): nivel_gobierno, pliego, sec_ejec, programa_ppto, tipo_act_proy,
producto_proyecto, actividad_accion_obra, funcion, division_funcional, grupo_funcional (nombres, como la base),
departamento_meta, fuente_financiamiento, rubro, categoria_gasto, generica y clasificador_transferencia (código completo
solo en la genérica 2.4: R-GASTO-05). La llave de línea de R-GASTO-19 está incluida. Montos DECIMAL(18,2) (mismo
redondeo que gasto.py): pia, pim (vigente a la fecha de corte), devengado_acum (al corte), filas.

El CSV se guarda una sola vez (almacén por huella). La tabla se escribe en
biblioteca/estandarizada/gasto/foto_pim/foto_pim_<anio>_<mes_ref>_<huella12>.parquet, con un .json de resumen al
lado; es derivada y se rehace desde el almacén con `pap foto-pim extraer --rehacer`.
"""
from __future__ import annotations

import re
import shutil
import tempfile
from datetime import date, datetime
from pathlib import Path

import duckdb

from .. import almacen, capturas
from ..config import Rutas
from ..errores import PapError
from ..util import ahora, escribir_json, leer_json, sha256

SOURCE_ID = "MEF-FOTO-PIM-MENSUAL"
VERSION_TABLA = "1.1.0"  # H1: rubro, categoría de gasto, clasificador de transferencias, cadena funcional por nombre; H2: mes_ref
NOMBRE_ARCHIVO = re.compile(r"^(\d{4})-Gasto-Mensual\.csv$")
LLAVE = ["nivel_gobierno", "pliego", "sec_ejec", "programa_ppto", "tipo_act_proy", "producto_proyecto",
         "actividad_accion_obra", "funcion", "division_funcional", "grupo_funcional", "departamento_meta",
         "fuente_financiamiento", "rubro", "categoria_gasto", "generica", "clasificador_transferencia"]
COLUMNAS = ["anio", "mes_ref", "fecha_ref", "fecha_ref_base", "fecha_corte", "fecha_corte_base", "mes_descarga",
            "mes_max_devengado", "huella_captura", *LLAVE, "pia", "pim", "devengado_acum", "filas"]
URL_PATRON = "https://fs.datosabiertos.mef.gob.pe/datastorefiles/{anio}-Gasto-Mensual.csv"


def _q(ruta) -> str:
    """Literal SQL de una ruta (H12: una comilla en la ruta no rompe la consulta)."""
    return "'" + str(ruta).replace("'", "''") + "'"


def _monto(col: str) -> str:
    return f"SUM(TRY_CAST(NULLIF(trim({col}), '') AS DECIMAL(18,2)))"


def _no_cero(col: str) -> str:
    return f"coalesce(TRY_CAST(NULLIF(trim({col}), '') AS DECIMAL(18,2)), 0) <> 0"


def _invalido(col: str) -> str:
    return (f"COUNT(*) FILTER (WHERE NULLIF(trim({col}), '') IS NOT NULL "
            f"AND TRY_CAST(trim({col}) AS DECIMAL(18,2)) IS NULL)")


# Mismas opciones de lectura que capa0/gasto.py (escape explícito y modo estricto: auditoría del 6/10/2026)
LECTOR = "read_csv(?, header=true, all_varchar=true, quote='\"', escape='\"', delim=',', strict_mode=true)"

# Mismas expresiones que SQL_BASE de gasto.py para las columnas compartidas
SQL_AGREGADO = f"""
CREATE TEMP TABLE agg AS
SELECT CAST(ANO_EJE AS INTEGER) AS anio,
       NIVEL_GOBIERNO AS nivel_gobierno, PLIEGO AS pliego, SEC_EJEC AS sec_ejec,
       lpad(PROGRAMA_PPTO, 4, '0') AS programa_ppto, TIPO_ACT_PROY_NOMBRE AS tipo_act_proy,
       PRODUCTO_PROYECTO AS producto_proyecto, ACTIVIDAD_ACCION_OBRA AS actividad_accion_obra,
       FUNCION_NOMBRE AS funcion, DIVISION_FUNCIONAL_NOMBRE AS division_funcional,
       GRUPO_FUNCIONAL_NOMBRE AS grupo_funcional, DEPARTAMENTO_META AS departamento_meta,
       FUENTE_FINANCIAMIENTO AS fuente_financiamiento, RUBRO AS rubro, CATEGORIA_GASTO AS categoria_gasto,
       GENERICA AS generica,
       CASE WHEN GENERICA = '4' THEN TIPO_TRANSACCION || '.' || GENERICA || '.' || SUBGENERICA || '.' ||
            SUBGENERICA_DET || '.' || ESPECIFICA || '.' || ESPECIFICA_DET END AS clasificador_transferencia,
       {_monto('MONTO_PIA')} AS pia, {_monto('MONTO_PIM')} AS pim, {_monto('MONTO_DEVENGADO')} AS devengado_acum,
       COUNT(*) AS filas,
       max(TRY_CAST(MES_EJE AS INTEGER)) FILTER (WHERE {_no_cero('MONTO_DEVENGADO')}) AS mes_max_dev,
       COUNT(*) FILTER (WHERE TRY_CAST(MES_EJE AS INTEGER) IS NULL
                        OR TRY_CAST(MES_EJE AS INTEGER) NOT BETWEEN 0 AND 12) AS meses_invalidos,
       COUNT(*) FILTER (WHERE TRY_CAST(MES_EJE AS INTEGER) <> 0
                        AND ({_no_cero('MONTO_PIA')} OR {_no_cero('MONTO_PIM')})) AS pim_fuera_mes0,
       {_invalido('MONTO_PIA')} + {_invalido('MONTO_PIM')} + {_invalido('MONTO_DEVENGADO')} AS montos_invalidos
FROM {LECTOR}
GROUP BY ALL
"""


def carpeta(rutas: Rutas) -> Path:
    return rutas.raiz / "biblioteca" / "estandarizada" / "gasto" / "foto_pim"


def anio_de_nombre(nombre: str) -> int:
    m = NOMBRE_ARCHIVO.match(nombre)
    if not m:
        raise PapError(f"«{nombre}» no es un archivo {{anio}}-Gasto-Mensual.csv (R-GASTO-04: nunca el -Diario ni el "
                       "anual). Renómbralo solo si es ese archivo.")
    return int(m.group(1))


def _fecha(txt: str) -> date:
    return datetime.fromisoformat(str(txt)).date() if "T" in str(txt) else date.fromisoformat(str(txt)[:10])


def mes_ref_de(fecha_ref: date, anio: int) -> int:
    """Último mes de `anio` que terminó antes de `fecha_ref` (0 = ninguno)."""
    if fecha_ref.year < anio:
        raise PapError(f"La fecha de referencia {fecha_ref} es anterior al año del archivo ({anio}).")
    if fecha_ref.year > anio:
        return 12
    return fecha_ref.month - 1


def _referencia(corte: str | None, consultado: str, anio: int, mes_max: int | None) -> dict:
    try:
        d_cons = _fecha(consultado)
    except ValueError as e:
        raise PapError(f"Fecha de consulta ilegible: {consultado}") from e
    if corte:
        try:
            d = date.fromisoformat(corte)
        except ValueError as e:
            raise PapError(f"--corte debe ser AAAA-MM-DD (fecha «actualizado» de la página del recurso): {corte}") from e
        if d > d_cons:
            raise PapError(f"La fecha de corte {corte} es posterior a la fecha de consulta ({d_cons}).")
        ref, base_ref, fcorte, base_corte = d, "declarada", corte, "declarada"
    else:
        if mes_max is None:
            raise PapError("El archivo no tiene devengado: no se puede inferir la fecha de corte; pásala con --corte.")
        ref, base_ref = d_cons, "fecha_consulta"
        fcorte, base_corte = f"{anio}-{mes_max:02d}", "max_fecha_en_datos"
    mes_ref = mes_ref_de(ref, anio)
    if mes_ref > 0 and (mes_max is None or mes_max < mes_ref):
        raise PapError(f"El archivo no trae devengado de {anio}-{mes_ref:02d} (último mes con devengado: {mes_max}): "
                       "parece desactualizado. Revisa la fecha «actualizado» y pásala con --corte.")
    if mes_max is not None and ref.year == anio and mes_max > mes_ref + 1:
        raise PapError(f"El archivo trae devengado de {anio}-{mes_max:02d}, posterior a la fecha de referencia {ref}: "
                       "revisa --corte.")
    return {"fecha_ref": ref.isoformat(), "fecha_ref_base": base_ref, "mes_ref": mes_ref, "fecha_corte": fcorte,
            "fecha_corte_base": base_corte, "mes_descarga": d_cons.strftime("%Y-%m")}


def extraer(csv: Path, destino: Path, huella: str, corte: str | None = None, anio_esperado: int | None = None,
            consultado: str | None = None) -> dict:
    """Agrega el CSV del MEF a la tabla foto_pim (parquet en `destino`). Devuelve el resumen (también en .json)."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    consultado = consultado or ahora()
    tmpdir = tempfile.mkdtemp(prefix="pap_foto_pim_")
    con = duckdb.connect()
    tmp = destino.with_name(destino.name + ".tmp")
    try:
        con.execute(f"SET memory_limit='2GB'; SET threads=2; SET temp_directory={_q(tmpdir)}; "
                    "SET preserve_insertion_order=false; SET enable_progress_bar=false")
        con.execute(SQL_AGREGADO, [str(csv)])
        anios = [r[0] for r in con.execute("SELECT DISTINCT anio FROM agg ORDER BY 1").fetchall()]
        if len(anios) != 1:
            raise PapError(f"El archivo debe traer un solo año (ANO_EJE); trae {anios}")
        anio = anios[0]
        if anio_esperado is not None and anio != anio_esperado:
            raise PapError(f"El nombre dice {anio_esperado} pero ANO_EJE = {anio}")
        invalidos, mes_max, meses_mal, fuera0 = con.execute(
            "SELECT sum(montos_invalidos), max(mes_max_dev), sum(meses_invalidos), sum(pim_fuera_mes0) FROM agg"
        ).fetchone()
        if invalidos:
            raise PapError(f"{invalidos} monto(s) ilegibles en el CSV: no se escribe la foto")
        if meses_mal:
            raise PapError(f"{meses_mal} fila(s) con MES_EJE fuera de 0–12: no se escribe la foto")
        if fuera0:
            raise PapError(f"{fuera0} fila(s) con PIA o PIM ≠ 0 en un MES_EJE ≠ 0: el formato del archivo cambió "
                           "(R-GASTO-21 lee el PIM del mes 0); revisar antes de sumar")
        ref = _referencia(corte, consultado, anio, mes_max)
        llave = ", ".join(LLAVE)
        con.execute(f"""
            COPY (SELECT anio, {ref['mes_ref']}::INTEGER AS mes_ref, ? AS fecha_ref, ? AS fecha_ref_base,
                         ? AS fecha_corte, ? AS fecha_corte_base, ? AS mes_descarga,
                         {mes_max if mes_max is not None else 'NULL'}::INTEGER AS mes_max_devengado,
                         ? AS huella_captura, {llave},
                         sum(pia) AS pia, sum(pim) AS pim, sum(devengado_acum) AS devengado_acum,
                         sum(filas)::BIGINT AS filas
                  FROM agg GROUP BY ALL ORDER BY ALL)
            TO {_q(tmp)} (FORMAT parquet, COMPRESSION zstd)""",
                    [ref["fecha_ref"], ref["fecha_ref_base"], ref["fecha_corte"], ref["fecha_corte_base"],
                     ref["mes_descarga"], f"sha256:{huella}"])
        filas, pia, pim, dev, filas_csv = con.execute(
            f"SELECT count(*), sum(pia)::VARCHAR, sum(pim)::VARCHAR, sum(devengado_acum)::VARCHAR, sum(filas) "
            f"FROM read_parquet({_q(tmp)})").fetchone()
        # conservación: la tabla suma lo mismo que una segunda lectura del CSV (tolerancia 0)
        tot = con.execute(f"SELECT {_monto('MONTO_PIA')}::VARCHAR, {_monto('MONTO_PIM')}::VARCHAR, "
                          f"{_monto('MONTO_DEVENGADO')}::VARCHAR, count(*) FROM {LECTOR}", [str(csv)]).fetchone()
        if (pia, pim, dev, filas_csv) != tot:
            raise PapError(f"La foto no conserva los totales del CSV: {(pia, pim, dev, filas_csv)} ≠ {tot}")
        tmp.replace(destino)
    finally:
        con.close()
        tmp.unlink(missing_ok=True)
        shutil.rmtree(tmpdir, ignore_errors=True)  # H7
    resumen = {"tabla": "foto_pim", "version_tabla": VERSION_TABLA, "anio": anio, **ref,
               "mes_max_devengado": mes_max, "huella_captura": f"sha256:{huella}", "filas": filas,
               "filas_csv": filas_csv, "totales": {"pia": pia, "pim": pim, "devengado_acum": dev},
               "parquet": destino.name, "huella_parquet": f"sha256:{sha256(destino)}"}
    escribir_json(destino.with_suffix(".json"), resumen)
    return resumen


def ruta_foto(rutas: Rutas, anio: int, mes_ref: int, huella: str) -> Path:
    h = huella.removeprefix("sha256:")[:12]
    return carpeta(rutas) / f"foto_pim_{anio}_{mes_ref:02d}_{h}.parquet"


def capturas_foto(rutas: Rutas) -> list[tuple[Path, dict]]:
    return capturas.recursos(rutas, SOURCE_ID)


def resumenes(rutas: Rutas) -> list[dict]:
    return [leer_json(p) for p in sorted(carpeta(rutas).glob("foto_pim_*.json"))]


def _publicar(rutas: Rutas, tmp: Path, res: dict) -> dict:
    final = ruta_foto(rutas, res["anio"], res["mes_ref"], res["huella_captura"])
    tmp.replace(final)
    tmp.with_suffix(".json").unlink(missing_ok=True)
    res["parquet"] = final.name
    escribir_json(final.with_suffix(".json"), res)
    return res


def extraer_pendientes(rutas: Rutas, rehacer: bool = False) -> list[dict]:
    """Escribe la foto de cada captura de MEF-FOTO-PIM-MENSUAL que aún no la tiene (desde el almacén). Usa solo los
    metadatos de la captura (corte declarado y retrieved_at), así el resultado es el mismo que al registrarla."""
    hechas = {r["huella_captura"]: r for r in resumenes(rutas)}
    out = []
    for _, rec in capturas_foto(rutas):
        if rec["hash"] in hechas and not rehacer:
            continue
        anio = anio_de_nombre(rec["original_filename"])
        corte = rec.get("data_cutoff") if rec.get("data_cutoff_basis") == "declarada" else None
        crudo = almacen.resolver(rutas, rec["path"])  # <huella> o <huella>.zst
        if not crudo.exists():
            raise PapError(f"No está el crudo {rec['path']} de {rec['hash'][:19]}… en el almacén")
        if rec["hash"] in hechas:  # rehacer: quitar la versión anterior (su nombre puede cambiar)
            vieja = carpeta(rutas) / hechas[rec["hash"]]["parquet"]
            vieja.unlink(missing_ok=True)
            vieja.with_suffix(".json").unlink(missing_ok=True)
        tmp = carpeta(rutas) / f"_tmp_{rec['hash'][7:19]}.parquet"
        res = extraer(crudo, tmp, rec["hash"][7:], corte, anio, rec["retrieved_at"])
        out.append(_publicar(rutas, tmp, res))
    return out


def meses_faltantes(rutas: Rutas, anio: int, hasta_mes: int) -> list[int]:
    """Meses sin foto entre la primera foto del año y `hasta_mes` (la serie empieza cuando empezó a guardarse)."""
    tiene = {r["mes_ref"] for r in resumenes(rutas) if r["anio"] == anio}
    if not tiene:
        return []
    return [m for m in range(min(tiene), hasta_mes + 1) if m not in tiene]


def sql_vistas(rutas: Rutas) -> str:
    """Vistas DuckDB: foto_pim (todas las fotos) y foto_pim_mensual (por año × mes_ref, la de fecha_ref más reciente;
    p. ej. una descarga de marzo del año siguiente reemplaza en la vista a la de enero como foto del mes 12)."""
    patron = _q(carpeta(rutas) / "foto_pim_*.parquet")
    return (f"CREATE OR REPLACE VIEW foto_pim AS SELECT * FROM read_parquet({patron});\n"
            "CREATE OR REPLACE VIEW foto_pim_mensual AS SELECT f.* FROM foto_pim f JOIN ("
            "SELECT anio, mes_ref, arg_max(huella_captura, fecha_ref || huella_captura) AS huella_captura "
            "FROM (SELECT DISTINCT anio, mes_ref, fecha_ref, huella_captura FROM foto_pim) GROUP BY anio, mes_ref) u "
            "USING (anio, mes_ref, huella_captura);")


def registrar_foto(rutas: Rutas, archivo: Path, corte: str | None = None, mover: bool = False,
                   notas: list[str] | None = None, atribuido: str | None = None,
                   consultado: str | None = None) -> tuple[object | None, dict]:
    """Extrae la foto y registra el CSV como captura fechada de MEF-FOTO-PIM-MENSUAL (nunca pisa una anterior: cada
    registro crea capturas/MEF-FOTO-PIM-MENSUAL/<fecha>[-n]/). Si la huella ya estaba registrada, solo asegura la
    foto. Devuelve (Resultado de registrar o None, resumen de la foto)."""
    from ..registrar import Opciones, registrar

    archivo = Path(archivo)
    if not archivo.is_file():
        raise PapError(f"No existe el archivo {archivo}")
    anio = anio_de_nombre(archivo.name)
    huella = sha256(archivo)
    if capturas.buscar_por_huella(rutas, huella, SOURCE_ID):
        hechas = {r["huella_captura"]: r for r in resumenes(rutas)}
        if f"sha256:{huella}" in hechas:
            return None, hechas[f"sha256:{huella}"]
        return None, next(x for x in extraer_pendientes(rutas) if x["huella_captura"] == f"sha256:{huella}")
    consultado = consultado or ahora()
    tmp = carpeta(rutas) / f"_tmp_{huella[:12]}.parquet"
    res = extraer(archivo, tmp, huella, corte, anio, consultado)
    op = Opciones(corte=res["fecha_corte"], corte_base=res["fecha_corte_base"], recurso=f"foto-pim-{anio}",
                  mover=mover, notas=list(notas or []), atribuido=atribuido, consultado=consultado,
                  url_descarga=URL_PATRON.format(anio=anio))
    try:
        r = registrar(rutas, SOURCE_ID, [archivo], op)
    except Exception:
        tmp.unlink(missing_ok=True)
        tmp.with_suffix(".json").unlink(missing_ok=True)
        raise
    return r, _publicar(rutas, tmp, res)
