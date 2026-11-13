"""Un mundo mínimo para probar `pap fichas` sin el almacén: dos tablas (RECH0 y RECH6), sus tablas curadas, el índice y los microdatos."""
import csv
import json
from pathlib import Path

import polars as pl
import yaml

from pap.inferencia.indice import _esquemas


def _v(archivo, n, pos, variable, clase, tipo="categorica", grupo=None, etiqueta="etq"):
    return {"var_id": f"ENDES·2024·{archivo}·{variable}", "encuesta": "ENDES", "anio": 2024, "archivo": archivo, "variable": variable,
            "posicion": pos, "clase": clase, "tipo_valor": tipo, "formato_origen": "x", "rango_valido": None,
            "codigos_especiales": json.dumps([{"codigo": "99", "etiqueta": "No sabe"}] if variable == "HC1" else []), "rol_faltante": None,
            "etiqueta_original": etiqueta, "etiqueta_curada": etiqueta, "texto_pregunta": None, "universo_cuestionario": None,
            "ventana_referencia": None, "sujeto": None, "informante": None, "modo": None, "grupo": grupo, "tipo_origen": None,
            "universo_corto": None, "concepto_id": None, "estado": "propuesto", "derivada_de": None, "n_categorias": 0, "controles": []}


VARS = [("RECH0", [("ID1", "diseno"), ("HHID", "llave"), ("HV009", "medida"), ("HV015", "categoria"), ("HV005", "peso")]),
        ("RECH6", [("HHID", "llave"), ("HC0", "llave"), ("HC1", "medida"), ("HC27", "categoria"), ("HC53", "medida"), ("HC55", "categoria")])]

TEMAS = {"version": "0.1.0", "estado": "provisional", "temas": [
    {"id": "hogar_vivienda", "nombre": "Hogar", "estado": "provisional", "subtemas": [{"id": "composicion_hogar", "nombre": "Composición"}]},
    {"id": "salud_infantil", "nombre": "Salud infantil", "estado": "provisional",
     "subtemas": [{"id": "anemia_desnutricion", "nombre": "Anemia"}, {"id": "otros", "nombre": "Otros"}]}]}


def ficha_rech6():
    return {"anios": [2024, 2024], "nombre_corto": "Peso, talla y hemoglobina", "descripcion": "Mediciones de los menores de 6 años.",
            "cuestionario": "hogar", "secciones": ["Antropometría"], "tipo_tabla": "medicion",
            "poblacion": {"texto": "niñas y niños menores de 6 años", "sujeto": "nino", "edad_min": 0, "edad_max": 71, "edad_unidad": "meses",
                          "sexo": "ambos", "condicion": "listados en el hogar", "variable_edad": "HC1"},
            "quien_tiene_fila": "todos los menores de 6 años listados", "informante": "personal de campo", "modo": "medido",
            "avisos": ["aviso de prueba"], "documentos": [{"recurso": "endes-2024-anemia", "miembro": "Diccionario - RECH6.pdf"}],
            "estado": "propuesto"}


def ficha_rech0():
    return {"anios": [2024, 2024], "nombre_corto": "Hogares", "descripcion": "Un hogar por fila.", "cuestionario": "hogar",
            "secciones": [], "tipo_tabla": "base", "poblacion": {"texto": "hogares particulares", "sujeto": "hogar"},
            "quien_tiene_fila": "cada hogar", "informante": None, "modo": "declarado", "avisos": [],
            "documentos": [{"recurso": "endes-2024-hogar"}], "estado": "propuesto"}


def bloques():
    return [{"id": "endes_rech0_hogar", "tabla": "RECH0", "anios": [2024, 2024], "nombre": "El hogar", "descripcion": "Datos del hogar.",
             "variables": {"rango": ["HV009", "HV015"]}, "tema": "hogar_vivienda", "subtema": "composicion_hogar", "tema_estado": "provisional",
             "papel": "contexto", "poblacion": {}, "estado": "propuesto"},
            {"id": "endes_rech6_medidas", "tabla": "RECH6", "anios": [2024, 2024], "nombre": "Medidas", "descripcion": "Edad y sexo.",
             "variables": {"prefijos": ["HC1", "HC27"]}, "tema": "salud_infantil", "subtema": "anemia_desnutricion", "tema_estado": "provisional",
             "papel": "resultado", "poblacion": {"edad_min": 0, "edad_max": 71, "edad_unidad": "meses"}, "estado": "propuesto"},
            {"id": "endes_rech6_hemoglobina", "tabla": "RECH6", "anios": [2024, 2024], "nombre": "Hemoglobina", "descripcion": "Nivel de hemoglobina.",
             "variables": {"lista": ["HC53", "HC55"]}, "tema": "salud_infantil", "subtema": "anemia_desnutricion", "tema_estado": "provisional",
             "papel": "resultado", "poblacion": {}, "estado": "propuesto"}]


def escribir_mundo(raiz: Path, *, edades=(0, 12, 71, 99)) -> Path:
    cur = raiz / "curados" / "inferencia"
    for d in ("fichas", "bloques", "descargas", "recetas"):
        (cur / d).mkdir(parents=True, exist_ok=True)
    (raiz / "catalogo").mkdir(exist_ok=True)
    (cur / "temas.yaml").write_text(yaml.safe_dump(TEMAS, allow_unicode=True), encoding="utf-8")
    (cur / "fichas" / "ENDES.yaml").write_text(yaml.safe_dump({
        "version": "0.1.0", "encuesta": "ENDES", "tipo_fuente": "muestra",
        "vocabularios": {"cuestionario": ["hogar", "individual", "salud"], "sujeto": ["nino", "madre", "hogar", "persona"]},
        "tablas": {"RECH0": ficha_rech0(), "RECH6": ficha_rech6()}}, allow_unicode=True), encoding="utf-8")
    (cur / "bloques" / "ENDES.yaml").write_text(yaml.safe_dump({"version": "0.1.0", "encuesta": "ENDES", "bloques": bloques()}, allow_unicode=True), encoding="utf-8")
    (cur / "descargas" / "endes_2024.yaml").write_text(yaml.safe_dump({
        "fuente": "INEI-ENDES", "encuesta": {"anio": 2024, "codigo": 968, "periodo_codigo": 5, "periodo_nombre": "Unico"},
        "modulos": [{"codigo": 1629, "nombre": "Hogar", "formato": "STATA", "recurso": "endes-2024-hogar", "tablas": ["RECH0"]},
                    {"codigo": 1638, "nombre": "Anemia", "formato": "STATA", "recurso": "endes-2024-anemia", "tablas": ["RECH6"]}]}, allow_unicode=True), encoding="utf-8")
    (cur / "archivos_endes_2024.yaml").write_text(yaml.safe_dump({
        "archivos": {"RECH0": {"unidad": "hogar", "llave": ["HHID"]}, "RECH6": {"unidad": "persona_del_hogar", "llave": ["HHID", "HC0"]}},
        "relaciones": [{"hijo": "RECH6", "padre": "RECH0", "por": [["HHID", "HHID"]], "cardinalidad": "n:1"}]}), encoding="utf-8")
    with (cur / "diseno_muestral.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["encuesta", "anio", "archivo", "medicion", "poblacion", "peso_expr", "estrato_expr", "psu_expr", "upm_estable_expr", "peso_normalizado", "nivel_submuestra", "uniones_para_diseno", "cita"])
        w.writerow(["ENDES", 2024, "RECH0", "hogar", "hogares", "HV005/1e6", "est", "HV021", "HV001", "sí", "hogar", "", "c"])
    (cur / "territorios.yaml").write_text(yaml.safe_dump({"territorios": []}), encoding="utf-8")
    with (raiz / "catalogo" / "inferencia_verificada.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["fuente", "anio", "modulo", "inferencia_verificada", "nivel_maximo", "dominios_anuales"])
        w.writerow(["INEI-ENDES", 2024, "*", "true", "departamento", "nacional; 24 departamentos"])
    ind = raiz / "biblioteca" / "variables"
    ind.mkdir(parents=True, exist_ok=True)
    esq_a, esq_v, _ = _esquemas()
    filas_v = [_v(a, len(vs), i, n, c) for a, vs in VARS for i, (n, c) in enumerate(vs, start=1)]
    pl.DataFrame(filas_v, schema=esq_v).sort("var_id").write_parquet(ind / "variables.parquet")
    pl.DataFrame([{"encuesta": "ENDES", "anio": 2024, "archivo": a, "unidad": "x", "llave": ["HHID"], "n_filas": 4, "formato": "dta",
                   "huella_datos": "h" * 64, "zip": z, "miembro": f"{a}_2024.dta", "n_variables": len(vs),
                   "relaciones": json.dumps([{"con": "RECH0", "por": [["HHID", "HHID"]], "cardinalidad": "n:1"}] if a == "RECH6" else [])}
                  for (a, vs), z in zip(VARS, ("968-Modulo1629.zip", "968-Modulo1638.zip"))], schema=esq_a).write_parquet(ind / "archivos.parquet")
    micro = raiz / "biblioteca" / "microdatos" / "ENDES" / "2024"
    micro.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"HHID": ["1"] * len(edades), "HC0": list(range(len(edades))), "HC1": [float(e) for e in edades]}).write_parquet(micro / "RECH6.parquet")
    return raiz


RECURSOS = {"endes-2024-hogar": ["968-Modulo1629/Diccionario - RECH0.pdf"], "endes-2024-anemia": ["968-Modulo1638/Diccionario - RECH6.pdf", "968-Modulo1638/CUESTIONARIO DEL HOGAR ENDES 2024.pdf"]}


def buscar(recurso):
    return (recurso in RECURSOS, RECURSOS.get(recurso))
