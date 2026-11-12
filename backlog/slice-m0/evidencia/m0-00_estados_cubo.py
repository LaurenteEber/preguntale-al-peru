"""M0-00 tarea 5: estado de R-ENC-02..04 sobre las 90 filas de 2024 del cubo, con las funciones de reglas_etapa4.py.
Uso: uv run python backlog/slice-m0/evidencia/m0-00_estados_cubo.py backlog/slice-m0/evidencia/m0-00_estados_cubo.csv
"""
import csv, sys
from pathlib import Path
from pap.motor.validador import cargar
from pap.motor.validador.contexto import cargar_contexto
from pap.motor.validador.nucleo import Cifra, accion_final, estado_cifra
from pap.motor.validador.validador import correr_regla
cargar()
ctx = cargar_contexto(Path("."))
IDS = ["endes_anemia_6_35m", "endes_anemia_6_35m_oms2024", "endes_dci_menores_5"]
ENC = ["R-ENC-02", "R-ENC-03", "R-ENC-04"]
cubo = ctx.cubo[ctx.cubo.indicador_id.isin(IDS) & (ctx.cubo.anio == 2024)]
print(len(cubo), sorted(cubo.linea.unique()), file=sys.stderr)
w = csv.writer(open(sys.argv[1], "w", newline=""))
w.writerow(["indicador_id", "nivel", "territorio_id", "accion_final", "estado", "reglas"])
for f in cubo.sort_values(["indicador_id", "nivel", "territorio_id"]).itertuples():
    fila = ctx.fila_cubo(f.indicador_id, 2024, f.nivel, f.territorio_id, f.medida, f.linea)
    c = Cifra.desde(fila, ctx.indicadores[f.indicador_id])
    res = [r for rid in ENC for r in correr_regla(rid, c, ctx)]
    fin = accion_final(res, ctx)
    w.writerow([f.indicador_id, f.nivel, f.territorio_id, fin, estado_cifra(fin, res),
                ";".join(f"{r.regla}:{r.accion}:{r.motivo}" for r in res)])
