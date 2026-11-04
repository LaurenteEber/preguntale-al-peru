"""Citas: formato adaptado de DataCite y APA 7 (especificacion_cruda.md §6)."""
from __future__ import annotations

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
METODO_TEXTO = {
    "http_directo": "descarga automática",
    "http_patron": "descarga automática",
    "microdatos_encuesta": "microdatos",
    "geoservicio": "geoservicio",
    "manual_navegador": "descarga manual",
    "scraping_navegador": "extracción desde el navegador",
    "solicitud_acceso": "solicitud Ley 27806",
    "redatam_export": "exportación REDATAM",
    "archivo_propio": "archivo propio",
}


def fecha_corta(iso: str | None) -> str | None:
    if not iso or len(iso) < 10:
        return iso
    a, m, d = iso[:4], int(iso[5:7]), iso[8:10]
    return f"{d}-{MESES[m - 1]}-{a}"


def cita(rec: dict) -> str:
    anio = (rec.get("issued") or "")[:4] or "s. f."
    partes = [f"{rec['publisher']} ({anio}). {rec['dataset_title']} [{rec['original_filename']}]"]
    if rec.get("source_version"):
        partes[-1] += f", {rec['source_version']}"
    partes[-1] += "."
    partes.append("(Conjunto de datos).")
    if rec.get("data_cutoff") and rec.get("data_cutoff_basis") != "desconocida":
        nota = " (fecha máxima en los datos)" if rec.get("data_cutoff_basis") == "max_fecha_en_datos" else ""
        partes.append(f"Datos al {fecha_corta(rec['data_cutoff'])}{nota}.")
    if rec.get("access_url"):
        partes.append(f"{rec['access_url']}.")
    partes.append(f"Consultado el {fecha_corta(rec['retrieved_at'])}.")
    partes.append(f"SHA-256: {rec['hash'].removeprefix('sha256:')[:12]}.")
    return " ".join(partes)


def ficha_corta(rec: dict) -> str:
    ed = f", {rec['source_version']}" if rec.get("source_version") else ""
    metodo = METODO_TEXTO.get(rec.get("method"), rec.get("method"))
    return (f"{rec['publisher']}, {rec['dataset_title']}{ed} ({metodo}). Datos de {rec['temporal']}. "
            f"Consultado el {fecha_corta(rec['retrieved_at'])}.")
