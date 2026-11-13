"""M1-06 tarea 5: compara el documento n.º 11 del INEI «Identificadores de las bases de datos» con las llaves y uniones de
curados/inferencia/archivos_endes_2024.yaml y con los datos. Uso (desde la raíz del repo): uv run python backlog/slice-m1/evidencia/m1-06_identificadores.py
El PDF se lee con `pdftotext` (herramienta externa, sin ejecutar nada del documento) en una carpeta temporal nueva."""
import json, re, subprocess, tempfile
from pathlib import Path
import duckdb, yaml

RAIZ = Path(__file__).resolve().parents[3]
cap = json.loads((RAIZ / "biblioteca/cruda/capturas/INEI-ENDES/2026-11-12-3/datapackage.json").read_text(encoding="utf-8"))
rec = next(r for r in cap["resources"] if r["name"] == "endes-2024-identificadores-bd")
pdf = RAIZ / "biblioteca/cruda" / rec["path"]
with tempfile.TemporaryDirectory(prefix="pap-doc11-") as d:
    txt = Path(d) / "doc11.txt"
    subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=True)
    texto = txt.read_text(encoding="utf-8")

# Filas de la tabla: «N°  NOMBRE  IDENTIFICADOR PRINCIPAL  [IDENTIFICADOR 2  [IDENTIFICADOR 3]]»
filas = {}
for linea in texto.splitlines():
    m = re.match(r"^\s*(\d{1,2})\s{2,}(\S.*?)\s{2,}(\S.*)$", linea)
    if m and 1 <= int(m.group(1)) <= 34:
        ids = [x.strip() for x in re.split(r"\s{2,}", m.group(3).strip())]
        filas[int(m.group(1))] = (m.group(2).strip(), ids)
y = yaml.safe_load((RAIZ / "curados/inferencia/archivos_endes_2024.yaml").read_text(encoding="utf-8"))
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
doc_por_tabla = {norm(n): (f, ids) for f, (n, ids) in filas.items()}
P = RAIZ / "biblioteca/microdatos/ENDES/2024"
con = duckdb.connect()
def unica(tabla, cols):
    c = ", ".join(f'"{x}"' for x in cols)
    n, d = con.execute(f"select count(*), count(distinct ({c})) from read_parquet('{P / (tabla + '.parquet')}') where {' and '.join(f'\"{x}\" is not null' for x in cols)}").fetchone()
    nt = con.execute(f"select count(*) from read_parquet('{P / (tabla + '.parquet')}')").fetchone()[0]
    return nt, n, d
L = ["# M1-06 tarea 5 — Documento n.º 11 «Identificadores de las bases de datos» frente a las llaves declaradas", "",
     f"Generado por `{Path(__file__).name}`. Documento: recurso `endes-2024-identificadores-bd` (`{rec['original_filename']}`, sha256 `{rec['hash'][7:23]}…`), leído con `pdftotext`. "
     "Tiene 2 páginas: la tabla de 34 filas (identificador principal y hasta dos alternos) y las «Precisiones».", "",
     "## Llaves", "", "| Fila | Tabla | Identificador principal (documento) | Llave declarada | ¿Coincide? | Filas | Filas con la llave completa | Llaves distintas | Alternos del documento |",
     "|---|---|---|---|---|---|---|---|---|"]
problemas = []
for t, e in y["archivos"].items():
    k = norm(t.replace("_", " "))
    fila, ids = doc_por_tabla.get(k) or next(v for kk, v in doc_por_tabla.items() if k.startswith(kk))      # el nombre de la fila 8 sigue en la línea de abajo
    declarada = " + ".join(e["llave"])
    # CASEID se declara tal cual; el HHID de los módulos de la mujer es el derivado de CASEID
    coincide = norm(ids[0]) == norm(declarada)
    nt, n, d = unica(t, e["llave"])
    unica_ok = (n == d == nt)
    if not coincide: problemas.append((t, ids[0], declarada))
    L.append(f"| {fila} | {t} | {ids[0]} | {declarada} | {'sí' if coincide else '**NO**'} | {nt:,} | {n:,} | {d:,}{'' if unica_ok else ' (**repite**)'} | {'; '.join(ids[1:]) or '—'} |")
L += ["", "## Llaves alternas del documento comprobadas en los datos", "", "| Tabla | Alterna | Filas | Llaves distintas |", "|---|---|---|---|"]
for t, cols in (("REC21", ["CASEID", "BORD"]), ("REC21", ["CASEID", "B16"]), ("DIT", ["CASEID", "BORD"]), ("REC95", ["CASEID", "Q452"]),
                ("REC93DVdisciplina", ["CASEID", "Q1035NO"]), ("CSALUD01", ["HHID", "QSNUMERO"])):
    nt, n, d = unica(t, cols)
    c = ", ".join(f'"{x}"' for x in cols)
    nulos = con.execute(f"select count(*) from read_parquet('{P / (t + '.parquet')}') where {' or '.join(f'\"{x}\" is null' for x in cols)}").fetchone()[0]
    L.append(f"| {t} | {' + '.join(cols)} | {nt:,} | {d:,} distintas en {n:,} con llave completa ({nulos:,} filas con algún nulo) |")
L += ["", "## Uniones declaradas y lo que el documento dice", "", "| Unión (hijo → padre) | Por | Cardinalidad | Respaldo |", "|---|---|---|---|"]
for r in y["relaciones"]:
    L.append(f"| {r['hijo']} → {r['padre']} | {', '.join(a + ' = ' + b for a, b in r['por'])} | {r['cardinalidad']} | {r['cita']} |")
L += ["", "## Equivalencias de las «Precisiones»", "",
      "- HVIDX = IDXH4 = B16 = HA0 = HC0 = QSNUMERO = QS801 (número de línea de la persona en el hogar). Respalda RECH6 → RECH1 (HC0 = HVIDX), CSALUD08 → RECH1 (QS801 = HVIDX) y los PS_* → RECH1 (HVIDX = HVIDX).",
      "- BIDX = MIDX = HIDX = HWIDX = IDX94 = IDX95 = QCOL93 (índice del hijo nacido vivo, empezando por el último); BORD = Q1035NO = Q452 (orden del nacimiento).",
      "- «Si B16 = 0, es porque no fue listado en el hogar»: por eso B16 no puede ser llave (se repite el 0).", "",
      "## Resultado", ""]
L.append(f"- {34 - len(problemas)} de 34 tablas con la llave igual a la del documento." if True else "")
for t, d_, a in problemas:
    L.append(f"- **{t}**: el documento da `{d_}` y se declara `{a}`.")
print("\n".join(L))
