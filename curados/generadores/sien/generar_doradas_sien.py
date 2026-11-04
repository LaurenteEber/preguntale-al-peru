"""Genera las cifras doradas del SIEN (anemia 6–35 m, OMS 2024, 2025) desde la publicación oficial del INS.

Fuente: INS/CENAN, «Indicadores Niños – diciembre 2025 (Base de Datos HIS-Minsa)», periodo enero a diciembre 2025
(XLSX registrado en INS-CENAN-SIEN, recurso indicadores-ninos-2025-diciembre). Contraste: Tabla 8.18 del «Informe
Gerencial SIEN-HIS Niños 2025» (p. 36), mismos valores. Uso: python generar_doradas_sien.py <xlsx> <salida.csv>
"""
import sys
import unicodedata

import openpyxl
import pandas as pd

XLSX, SALIDA = sys.argv[1], sys.argv[2]
URL = ("https://cdn.www.gob.pe/uploads/document/file/9599740/"
       "7857855-indicadores-ninos-diciembre-2025-base-de-datos-hisminsa.xlsx")
DOC = "INS, Indicadores Niños – diciembre 2025 (Base de Datos HIS-Minsa), periodo enero a diciembre 2025"
PDF = "Informe Gerencial SIEN-HIS Niños 2025, Tabla 8.18, p. 36"
DEP = {"AMAZONAS": "01", "ANCASH": "02", "APURIMAC": "03", "AREQUIPA": "04", "AYACUCHO": "05", "CAJAMARCA": "06",
       "CUSCO": "08", "HUANCAVELICA": "09", "HUANUCO": "10", "ICA": "11", "JUNIN": "12", "LA LIBERTAD": "13",
       "LAMBAYEQUE": "14", "LIMA": "15", "LORETO": "16", "MADRE DE DIOS": "17", "MOQUEGUA": "18", "PASCO": "19",
       "PIURA": "20", "PUNO": "21", "SAN MARTIN": "22", "TACNA": "23", "TUMBES": "24", "UCAYALI": "25"}
DISTRITOS = {"210801": "Q2 (Ayaviri)", "150132": "Q3 (San Juan de Lurigancho)"}

wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)


def tabla(hoja, ncol):
    return [r[1:1 + ncol] for r in wb[hoja].iter_rows(min_row=6, values_only=True)
            if r[1] and isinstance(r[ncol - 2], (int, float))]


def norm(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper().strip()


filas = []


def fila(id_, nivel, terr, den, num, cuadro, bloq=True, proposito="control_registro", lima="no_aplica", nota=""):
    filas.append(dict(
        id_cifra=id_, indicador_id="sien_anemia_tamizados_6_35m", fuente_id="INS-CENAN-SIEN", anio=2025, nivel=nivel,
        territorio=terr, definicion_lima=lima, criterio="RM251-2024/OMS2024", valor_publicado=round(100 * num / den, 1),
        ic_inf_publicado="", ic_sup_publicado="", cv_publicado="", casos_publicados=int(den), decimales=1,
        comparacion="redondeada_1d", tolerancia_pp=0.0, tolerancia_cv="", bloqueante=bloq, proposito=proposito,
        documento=DOC, url=URL, cuadro_pagina=cuadro, fecha_publicacion="2026-03",
        tipo_cita="oficial_ins", verificado_por="generado del XLSX oficial y contrastado con el PDF (12/10/2026)",
        nota=(f"evaluados {int(den)}, casos {int(num)}. " + nota).strip()))


for d, den, num, _ in tabla("Anemia 6-35m x DEP", 4):
    k = norm(d)
    if k == "PERU":
        fila("DOR-SIEN-2025-PE", "nacional", "PE", den, num, "Cuadro N.º 11, fila PERÚ", nota=f"= {PDF}.")
    elif k == "CALLAO":
        fila("DOR-SIEN-2025-CALLAO", "CALLAO", "CALLAO", den, num, "Cuadro N.º 11, fila CALLAO",
             lima="departamento 07; INS «CALLAO»", nota=f"= {PDF}.")
    elif k == "LIMA":
        fila("DOR-SIEN-2025-15", "departamento", "15", den, num, "Cuadro N.º 11, fila LIMA",
             lima="departamento 15 completo (1501 + Lima Región); INS «LIMA»",
             nota="no está en la Tabla 8.18 (allí Lima va por DIRIS y Lima Provincias).")
    else:
        fila(f"DOR-SIEN-2025-{DEP[k]}", "departamento", DEP[k], den, num, f"Cuadro N.º 11, fila {d}",
             nota=f"= {PDF}.")

dr = {norm(r[0]): r for r in tabla("Anemia 6-35m x DIRESA", 4)}
r = dr["LIMA REGION"]
fila("DOR-SIEN-2025-LIMA_REGION", "LIMA_REGION", "LIMA_REGION", r[1], r[2], "Cuadro N.º 14, fila LIMA REGION",
     lima="departamento 15 sin la provincia 1501 (9 provincias); INS «LIMA REGION» («LIMA PROVINCIAS» en la Tabla 8.18)",
     nota=f"= {PDF}, fila LIMA PROVINCIAS.")
diris = [dr[k] for k in ("LIMA DIRIS CENTRO", "LIMA DIRIS ESTE", "LIMA DIRIS NORTE", "LIMA DIRIS SUR")]
fila("DOR-SIEN-2025-LM1501", "LIMA_METROPOLITANA", "LIMA_METROPOLITANA", sum(x[1] for x in diris),
     sum(x[2] for x in diris), "Cuadro N.º 14, suma de las filas LIMA DIRIS CENTRO, ESTE, NORTE y SUR", bloq=False,
     proposito="control", lima="provincia 1501 (43 distritos, Ley 31140), sin Callao; INS: suma de las 4 DIRIS",
     nota="cifra derivada (el INS no publica Lima Metropolitana como una sola fila): solo control, no bloquea.")
dis = {str(r[3]).zfill(6): r for r in tabla("Anemia 6-35m x DISTRITO", 7)}
for u, q in DISTRITOS.items():
    r = dis[u]
    fila(f"DOR-SIEN-2025-{u}", "distrito", u, r[4], r[5], f"Cuadro N.º 15, fila {r[0]} / {r[1]} / {r[2]} ({u})",
         nota=f"{q}. Distrito del establecimiento de salud.")
pd.DataFrame(filas).to_csv(SALIDA, index=False)
print(len(filas), "doradas →", SALIDA)
