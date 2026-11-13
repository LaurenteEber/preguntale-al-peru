"""M1-04, hallazgo 7: ¿está la pregunta correcta entre las 20 candidatas? Sin LLM, sin red. Uso: `uv run python backlog/slice-m1/evidencia/m1-04_recall.py`.

Muestra: variables de REC0111 (V1xx y V009, V010, V012) cuya pregunta del cuestionario individual se conoce porque la etiqueta del
diccionario y el texto de la pregunta dicen lo mismo (se compararon a mano; no se inventó ninguna). Se omiten las variables del hogar
(V113 a V129…), las construidas (V011 CMC, V013, V133, V149) y V130 (religión, sin pregunta en el cuestionario individual extraído)."""
from pathlib import Path

from pap.config import Rutas
from pap.inferencia import cuestionarios as c
from pap.inferencia import cuestionarios_medicion as m

MUESTRA = {("REC0111", "V009"): "individual:105", ("REC0111", "V010"): "individual:105", ("REC0111", "V012"): "individual:106",
           ("REC0111", "V103"): "individual:102", ("REC0111", "V104"): "individual:103", ("REC0111", "V105"): "individual:104",
           ("REC0111", "V106"): "individual:108", ("REC0111", "V107"): "individual:108", ("REC0111", "V131"): "individual:119D",
           ("REC0111", "V155"): "individual:114", ("REC0111", "V156"): "individual:114A", ("REC0111", "V157"): "individual:115",
           ("REC0111", "V158"): "individual:116", ("REC0111", "V159"): "individual:117"}

if __name__ == "__main__":
    R = Rutas(Path(__file__).resolve().parents[3])
    d = c.carpeta_cuestionarios(R)
    qs = c.leer_cuestionarios(d)
    vs, cu = c.leer_diccionarios(d)
    vin = {(v.tabla, v.codigo): v for v in c.vincular_sin_llm(vs, qs, cu)}
    cand = c.Candidatos(qs)
    k = m.k_candidatos()
    for kk in (k, 30, 40):
        print("regla", m.recall_de_candidatos(vs, vin, cand, cu, kk))
    r = m.recall_de_muestra(vs, MUESTRA, cand, cu, k)
    print({x: r[x] for x in ("k", "total", "entre_los_candidatos", "porcentaje")})
    for f in r["filas"]:
        print(f"| {f['variable']} | {f['etiqueta'][:50]} | {f['pregunta']} | {f['puesto']} | {'sí' if f['entre_los_candidatos'] else 'no'} |")
