"""Recetas YAML: carga, validación contra su esquema, versión (commit) y generación desde el catálogo."""
from __future__ import annotations

import json
import re
from importlib import resources
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from .config import Rutas
from .errores import PapError
from .util import a_texto_fechas, git, leer_json

ESTRATEGIA_A_METODO = {
    "http_file": "http_directo",
    "http_pattern": "http_patron",
    "http_archive": "microdatos_encuesta",
    "geoservice": "geoservicio",
    "manual": "manual_navegador",
    "dashboard": "scraping_navegador",
    "owner_file": "archivo_propio",
}

# R-DEP-01: los insumos que bloquean el MVP se leen de reglas/reglas.json (una sola fuente de verdad; antes había
# una copia aquí que se desfasó: MEF-PPR seguía como bloqueante). Ver bloqueantes_mvp().
REGLAS_JSON = Path("reglas") / "reglas.json"
CAMPOS_CATALOGO = ("ola", "estrategia_descarga", "compuerta_ingesta")

EXT_ARCHIVO = re.compile(r"\.(csv|xlsx?|zip|rar|pdf|json|geojson|gpkg|dbf|txt|parquet)(\?.*)?$", re.I)
FORMATOS_ARCHIVO = {"csv", "xlsx", "xls", "zip", "rar", "pdf", "json", "geojson", "gpkg", "dbf", "txt", "shp", "rds", "sav", "dta"}


def _validador() -> Draft202012Validator:
    texto = resources.files("pap.esquemas").joinpath("receta.schema.json").read_text(encoding="utf-8")
    return Draft202012Validator(json.loads(texto))


def listar(rutas: Rutas) -> list[Path]:
    if not rutas.recetas.exists():
        return []
    return sorted(p for p in rutas.recetas.glob("*.yaml") if not p.name.startswith("_"))


def leer(ruta: Path) -> dict:
    with open(ruta, encoding="utf-8") as f:
        datos = yaml.safe_load(f)
    return a_texto_fechas(datos or {})


def errores(receta: dict, ruta: Path | None = None) -> list[str]:
    errs = []
    for e in sorted(_validador().iter_errors(receta), key=lambda e: list(e.absolute_path)):
        lugar = "/".join(str(p) for p in e.absolute_path) or "(raíz)"
        errs.append(f"{lugar}: {e.message}")
    if ruta is not None and receta.get("id") != ruta.stem:
        errs.append(f"id '{receta.get('id')}' no coincide con el nombre del archivo '{ruta.stem}'")
    return errs


def mensaje_desactivada(receta: dict) -> str:
    d = receta.get("desactivada") or {}
    return (f"La receta {receta.get('id')} está DESACTIVADA desde {d.get('fecha', '?')}: {d.get('motivo', '')} "
            f"(decisión: {d.get('decision', '?')}). No se registra ni se descarga nada con ella. "
            f"Para reactivarla: {d.get('reactivar', 'quitar el bloque `desactivada` de la receta, con una decisión nueva del dueño')}.")


def cargar(rutas: Rutas, source_id: str, permitir_desactivada: bool = False) -> dict:
    ruta = rutas.recetas / f"{source_id}.yaml"
    if not ruta.exists():
        raise PapError(f"No hay receta para {source_id} ({rutas.relativa(ruta)}).")
    receta = leer(ruta)
    errs = errores(receta, ruta)
    if errs:
        raise PapError(f"La receta {source_id} no pasa su esquema:\n  - " + "\n  - ".join(errs))
    if receta.get("desactivada") and not permitir_desactivada:
        raise PapError(mensaje_desactivada(receta))
    receta.setdefault("method", ESTRATEGIA_A_METODO[receta["strategy"]])
    return receta


def version(rutas: Rutas, source_id: str) -> str:
    """`<id>@<commit>` del último commit que tocó la receta; marca si hay cambios sin guardar."""
    rel = f"curados/recetas/{source_id}.yaml"
    commit = git(rutas.raiz, "log", "-1", "--format=%h", "--", rel)
    if commit is None:
        return f"{source_id}@sin-git"
    if not commit:
        return f"{source_id}@sin-commit"
    sucio = git(rutas.raiz, "status", "--porcelain", "--", rel)
    return f"{source_id}@{commit}" + ("-modificada" if sucio else "")


# ---------------------------------------------------------------- generación desde el catálogo

def _licencia(fuente: dict) -> tuple[list[dict], str, str | None]:
    lic = (fuente.get("licencia") or "").strip()
    if lic in ("", "no-especificada", "no-declarada"):
        return [{"name": "no-declarada"}], "no_declarada", None
    if lic == "uso-libre-con-cita":
        return ([{"name": "uso-libre-con-cita", "title": fuente.get("licencia_texto") or "Uso libre citando la fuente"}],
                "norma_general", "Información pública (TUO Ley 27806); citar a la entidad")
    item = {"name": lic}
    if fuente.get("licencia_texto"):
        item["title"] = fuente["licencia_texto"]
    return [item], "declarada_en_pagina", None


def _entidad_corta(entidad: str | None) -> str:
    """'Instituto Nacional de Estadística e Informática (INEI)' -> 'INEI'."""
    if not entidad:
        return "desconocido"
    m = re.search(r"\(([^()]+)\)\s*$", entidad)
    return m.group(1).strip() if m else entidad.strip()


def _formatos(fuente: dict) -> list[str]:
    out = []
    for f in fuente.get("formatos") or []:
        tok = str(f).split()[0].lower()
        if tok in FORMATOS_ARCHIVO and tok not in out:
            out.append(tok)
    return out


def bloqueantes_mvp(rutas: Rutas) -> set[str]:
    """`parametros.insumos_bloqueantes_mvp` de R-DEP-01 en reglas/reglas.json."""
    ruta = rutas.raiz / REGLAS_JSON
    if not ruta.exists():
        raise PapError(f"No encuentro {REGLAS_JSON}: de ahí se leen los insumos bloqueantes de R-DEP-01.")
    datos = leer_json(ruta)
    reglas = datos.get("reglas", []) if isinstance(datos, dict) else datos
    for r in reglas:
        if r.get("id") == "R-DEP-01":
            return set((r.get("parametros") or {}).get("insumos_bloqueantes_mvp") or [])
    raise PapError(f"{REGLAS_JSON} no tiene la regla R-DEP-01.")


def incoherencias_catalogo(rutas: Rutas) -> list[str]:
    """El bloque `catalogo:` de cada receta es una copia: debe coincidir con catalogo/catalogo_fuentes.json
    (ola, estrategia, compuerta) y `bloquea_mvp` con R-DEP-01 de reglas.json. Las recetas desactivadas deben decirlo
    también en su bloque `catalogo` y no bloquear nada."""
    if not rutas.catalogo.exists():
        return [f"no encuentro el catálogo en {rutas.relativa(rutas.catalogo)}"]
    cat = {f["id"]: f for f in leer_json(rutas.catalogo)}
    bloq = bloqueantes_mvp(rutas)
    out = [f"R-DEP-01: el insumo bloqueante {i} no está en el catálogo" for i in sorted(bloq)
           if re.match(r"^[A-Z0-9]+(-[A-Z0-9]+)+$", i) and i not in cat]
    for ruta in listar(rutas):
        r = leer(ruta)
        sid, bloque = r.get("id", ruta.stem), r.get("catalogo")
        if r.get("desactivada"):
            if not bloque or bloque.get("compuerta_ingesta") != "desactivada" or bloque.get("bloquea_mvp"):
                out.append(f"{sid}: desactivada, pero su bloque catalogo no dice compuerta_ingesta: desactivada y bloquea_mvp: false")
            if sid in bloq:
                out.append(f"{sid}: desactivada, pero R-DEP-01 la tiene como bloqueante")
            continue
        f = cat.get(sid)
        if f is None:
            if bloque:
                out.append(f"{sid}: tiene bloque catalogo pero no está en el catálogo")
            continue
        if not bloque:
            out.append(f"{sid}: está en el catálogo y le falta el bloque catalogo")
            continue
        for k in CAMPOS_CATALOGO:
            if bloque.get(k) != f.get(k):
                out.append(f"{sid}: catalogo.{k} = {bloque.get(k)!r} en la receta y {f.get(k)!r} en el catálogo")
        if bool(bloque.get("bloquea_mvp")) != (sid in bloq):
            out.append(f"{sid}: catalogo.bloquea_mvp = {bloque.get('bloquea_mvp')!r} en la receta y {sid in bloq} en R-DEP-01 (reglas.json)")
    return out


def _bloque_catalogo_texto(bloque: dict) -> list[str]:
    def v(x):
        return "null" if x is None else ("true" if x is True else "false" if x is False else str(x))
    return ["catalogo:"] + [f"  {k}: {v(bloque.get(k))}" for k in (*CAMPOS_CATALOGO, "bloquea_mvp")]


def sincronizar_catalogo(rutas: Rutas) -> list[Path]:
    """Reescribe SOLO el bloque `catalogo:` de cada receta (no desactivada) que está en el catálogo, copiándolo de
    catalogo/catalogo_fuentes.json y de R-DEP-01 (reglas.json). Conserva comentarios y el resto del texto.
    Devuelve las recetas que cambiaron. Después, `pap recetas validar` debe dar 0 diferencias."""
    cat = {f["id"]: f for f in leer_json(rutas.catalogo)}
    bloq = bloqueantes_mvp(rutas)
    cambiadas = []
    for ruta in listar(rutas):
        receta = leer(ruta)
        sid = receta.get("id", ruta.stem)
        if receta.get("desactivada") or sid not in cat:
            continue
        nuevo = {k: cat[sid].get(k) for k in CAMPOS_CATALOGO} | {"bloquea_mvp": sid in bloq}
        if receta.get("catalogo") == nuevo:
            continue
        lineas = ruta.read_text(encoding="utf-8").split("\n")
        ini = next((i for i, l in enumerate(lineas) if l.startswith("catalogo:")), None)
        if ini is None:
            ini = next((i for i, l in enumerate(lineas) if l.startswith(("pendientes:", "notas:"))), len(lineas))
            fin = ini
        else:
            fin = ini + 1
            if "{" not in lineas[ini]:
                while fin < len(lineas) and (lineas[fin].startswith((" ", "\t")) or not lineas[fin].strip()) and fin < len(lineas) - 1:
                    fin += 1
        lineas[ini:fin] = _bloque_catalogo_texto(nuevo)
        texto = "\n".join(lineas)
        antes = {k: v for k, v in receta.items() if k != "catalogo"}
        despues = a_texto_fechas(yaml.safe_load(texto) or {})
        if {k: v for k, v in despues.items() if k != "catalogo"} != antes or despues.get("catalogo") != nuevo:
            raise PapError(f"No pude reescribir solo el bloque catalogo de {ruta.name}; corrígelo a mano.")
        ruta.write_text(texto, encoding="utf-8")
        cambiadas.append(ruta)
    return cambiadas


def receta_desde_catalogo(f: dict, bloqueantes: set[str] | frozenset[str] = frozenset()) -> dict:
    sid = f["id"]
    est_cat = f.get("estrategia_descarga")
    url_datos = f.get("url_datos")
    pendientes: list[str] = []
    metodo = None
    if sid == "INEI-CPV2017":
        estrategia, metodo = "manual", "redatam_export"
        pendientes.append("Exportar desde REDATAM la consulta por distrito y grupos de edad (sprint S2).")
    elif est_cat == "descarga_directa_url" and url_datos and EXT_ARCHIVO.search(url_datos):
        estrategia = "http_file"
    elif est_cat in ("descarga_directa_url", "url_patron") and f.get("url_patron"):
        estrategia = "http_pattern"
        pendientes.append("Definir cómo se eligen los valores del patrón (ver notas).")
    elif est_cat == "scraping_dinamico":
        estrategia = "dashboard"
    elif est_cat == "geoservicio":
        estrategia = "geoservice"
    else:
        estrategia = "manual"
        if est_cat == "descarga_directa_url":
            pendientes.append("La URL de datos del catálogo es una página, no un archivo: confirmar la URL directa.")
    if sid == "MEF-MAESTRO-EJECUTORAS-DERIVADO":
        pendientes.append("Fuente derivada: se construye en S3 desde MEF-DA-PRESUPUESTO-EJECUCION-GASTO; no se descarga.")

    licencias, base_lic, nota_terminos = _licencia(f)
    r: dict = {
        "id": sid,
        "strategy": estrategia,
    }
    if metodo:
        r["method"] = metodo
    r.update({
        "publisher": _entidad_corta(f.get("entidad")),
        "dataset_title": f.get("nombre") or sid,
        "access_url": f.get("url_portal"),
    })
    if estrategia == "http_file":
        r["download_url"] = url_datos
    if f.get("url_patron"):
        r["url_patron"] = f["url_patron"]
    if f.get("url_documentacion"):
        r["documentation_url"] = f["url_documentacion"]
    r["temporal"] = {"inicio": f.get("anio_inicio"), "fin": f.get("anio_fin")}
    r["spatial"] = {
        "ambito": "PE" if (f.get("cobertura_geografica") or "nacional") == "nacional" else str(f.get("cobertura_geografica")),
        "nivel_minimo": f.get("nivel_territorial_disponible") or "desconocido",
    }
    r["source_version"] = {"basis": "ninguna"}
    r["data_cutoff"] = {"basis": "desconocida"}
    r["licenses"] = licencias
    r["license_basis"] = base_lic
    if nota_terminos:
        r["terms_note"] = nota_terminos
    if f.get("limitaciones"):
        r["known_issues"] = [f["limitaciones"]]
    if estrategia == "manual":
        pasos = [f"Abrir {f.get('url_portal') or url_datos} y descargar el archivo."]
        if url_datos and url_datos != f.get("url_portal"):
            pasos.append(f"Enlace de datos conocido: {url_datos}")
        pasos += [
            "Anotar la fecha de publicación que muestra la página.",
            f"Guardar el archivo en biblioteca/cruda/bandeja/{sid}/",
            f"Ejecutar: pap registrar {sid} --issued <fecha>",
        ]
        r["manual"] = {"pasos": pasos}
    formatos = _formatos(f)
    if formatos:
        r["espera"] = {"formato": formatos}
    r["catalogo"] = {
        "ola": f.get("ola"),
        "estrategia_descarga": est_cat,
        "compuerta_ingesta": f.get("compuerta_ingesta"),
        "bloquea_mvp": sid in bloqueantes,
    }
    if pendientes:
        r["pendientes"] = pendientes
    if f.get("detalle_descarga"):
        r["notas"] = f["detalle_descarga"]
    return r


CABECERA = (
    "# Receta de obtención — generada desde catalogo/catalogo_fuentes.json con `pap recetas generar`.\n"
    "# Se puede editar a mano; `pap recetas generar` no la sobrescribe salvo con --sobrescribir.\n"
    "# Esquema: src/pap/esquemas/receta.schema.json\n"
)


def generar_desde_catalogo(rutas: Rutas, ola: str = "0_base", sobrescribir: bool = False) -> tuple[list[Path], list[Path]]:
    if not rutas.catalogo.exists():
        raise PapError(f"No encuentro el catálogo en {rutas.relativa(rutas.catalogo)}")
    fuentes = [f for f in leer_json(rutas.catalogo) if f.get("ola") == ola]
    if not fuentes:
        raise PapError(f"Ninguna fuente del catálogo tiene ola = {ola!r}")
    bloq = bloqueantes_mvp(rutas)
    rutas.recetas.mkdir(parents=True, exist_ok=True)
    escritas, omitidas = [], []
    for f in sorted(fuentes, key=lambda x: x["id"]):
        ruta = rutas.recetas / f"{f['id']}.yaml"
        if ruta.exists() and not sobrescribir:
            omitidas.append(ruta)
            continue
        receta = receta_desde_catalogo(f, bloq)
        errs = errores(receta, ruta)
        if errs:
            raise PapError(f"La receta generada para {f['id']} no pasa el esquema: {errs}")
        texto = yaml.safe_dump(receta, allow_unicode=True, sort_keys=False, width=110)
        ruta.write_text(CABECERA + texto, encoding="utf-8")
        escritas.append(ruta)
    return escritas, omitidas
