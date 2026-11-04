"""S1-11: comprueba que una reconstrucción de la biblioteca dio las mismas tablas que las registradas en git.

Compara, para cada manifiesto en git, las huellas de sus tablas y de sus insumos en HEAD contra el archivo del
disco. Ignora `commit`, fechas y orden. Sale con código 1 si alguna huella cambió o falta.
Uso, desde la raíz: uv run python backlog/slice-1/adenda/comparar_manifiestos.py
"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]


def huellas(m: dict) -> dict:
    h = {f"tabla:{t}": v.get("hash") for t, v in m.get("tablas", {}).items() if isinstance(v, dict)}
    h.update({f"insumo:{i.get('source_id')}/{i.get('recurso')}": i.get("hash") for i in m.get("insumos", [])})
    return h


rutas = subprocess.run(["git", "ls-files", "biblioteca/**/manifiesto_*.json"], cwd=RAIZ, capture_output=True,
                       text=True, check=True).stdout.split()
fallos = 0
for r in rutas:
    antes = huellas(json.loads(subprocess.run(["git", "show", f"HEAD:{r}"], cwd=RAIZ, capture_output=True,
                                              text=True, check=True).stdout))
    ahora = huellas(json.loads((RAIZ / r).read_text(encoding="utf-8")))
    distintas = sorted(k for k in antes.keys() | ahora.keys() if antes.get(k) != ahora.get(k))
    fallos += len(distintas)
    print(f"{'OK ' if not distintas else 'DIF'} {r}: {len(antes)} huellas" + "".join(
        f"\n    {k}: {antes.get(k)} → {ahora.get(k)}" for k in distintas))
cubo = json.loads((RAIZ / "biblioteca/indicadores/manifiesto_p1_indicadores.json").read_text(encoding="utf-8"))
print("fact_indicador:", cubo["tablas"]["fact_indicador"]["hash"])
sys.exit(1 if fallos or not rutas else 0)
