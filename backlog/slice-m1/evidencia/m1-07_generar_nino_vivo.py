"""M1-07 (C-M1-07-2): saca de los bloques de M1-06 (curados/inferencia/bloques/ENDES.yaml) y del índice las variables de la batería `nino_vivo` de
mediciones.yaml: todas las de REC43, REC95 y DIT (vacunas, diarrea, fiebre y tos, suplementos, desarrollo infantil temprano) y las de lactancia
de REC41 y REC94. Imprime el YAML de las cinco filas. Uso: `uv run python backlog/slice-m1/evidencia/m1-07_generar_nino_vivo.py`."""
from pathlib import Path

from pap.inferencia import fichas

RAIZ = Path(__file__).resolve().parents[3]
f = fichas.cargar(RAIZ, "ENDES", 2024)
problemas: list = []
bloques, _ = fichas.asignar_bloques(f, problemas)
assert not problemas, problemas
por_id = {b["id"]: b for b in bloques}
TABLAS = {
    "REC43": ("Vacunas, diarrea, fiebre y tos, vitamina A, hierro y desparasitación del nacimiento (repetida de REC43)", None),
    "REC95": ("Vacunas con fechas, controles de crecimiento, anemia y suplementos del niño", None),
    "DIT": ("Desarrollo infantil temprano de niñas y niños de 9 a 71 meses", None),
    "REC41": ("Lactancia del último nacimiento: duración, inicio, tomas y biberón", ["endes_rec41_lactancia_duracion", "endes_rec41_lactancia_inicio_tomas"]),
    "REC94": ("Lactancia y alimentación del niño: biberón, contacto piel a piel, motivos, capacitación y preparación de alimentos",
              ["endes_rec94_lactancia", "endes_rec94_preparacion_alimentos"]),
}
for tabla, (bateria, ids) in TABLAS.items():
    vs: list[str] = []
    for b in bloques:
        if b["tabla"] == tabla and (ids is None or b["id"] in ids):
            vs += b["variables_resueltas"]
    orden = {v: i for i, v in enumerate(r["variable"] for r in f.variables.iter_rows(named=True) if r["archivo"] == tabla)}
    vs = sorted(set(vs), key=orden.get)
    print(f"# {tabla}: {len(vs)} variables")
    print(f"  - id: nino_vivo\n    encuesta: ENDES\n    anios: [2024, 2024]\n    archivo: {tabla}\n    bateria: \"{bateria}\"")
    cuerpo = ", ".join(vs)
    print("    variables: [" + cuerpo + "]")
