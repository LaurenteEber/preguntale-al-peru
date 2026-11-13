"""M1-04, hallazgo 10: ¿las variables hermanas de una tabla apuntan a la misma pregunta? Sin LLM, sin red.
Uso: `uv run python backlog/slice-m1/evidencia/m1-04_coherencia.py [TABLA] > m1-04_coherencia.md`  (por defecto REC43).

Una «familia» es el conjunto de variables de la tabla con el mismo prefijo: la letra o letras + el número del código (H12A, H12B… → H12;
H32T → H32; H44A → H44). Para cada familia de 3 o más variables se muestra a qué pregunta apunta cada miembro hoy (`vinculos.parquet`
y `vinculos_llm.parquet`, con `vinculos_manuales.yaml` por encima). Se marca:
- «mezcla»: los miembros vinculados apuntan a preguntas distintas (puede estar bien: una familia puede abarcar varias preguntas, p. ej. días
  y lugares; pero hay que mirarlo);
- «incompleta»: algunos miembros tienen pregunta y otros no.
No decide nada: solo ordena el trabajo de revisión del dueño."""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import polars as pl

from pap.config import Rutas
from pap.inferencia import cuestionarios as c

MINIMO = 3


def familia(codigo: str) -> str:
    m = re.match(r"^([A-Z]+\d+)", codigo)
    return m.group(1) if m else codigo


def cargar(raiz: Path, tabla: str):
    R = Rutas(raiz)
    d = c.carpeta_cuestionarios(R)
    vs, _ = c.leer_diccionarios(d)
    vs = [v for v in vs if v.tabla == tabla]
    filas = {}
    for nombre in ("vinculos.parquet", "vinculos_llm.parquet"):
        ruta = d / nombre
        if ruta.exists():
            for f in pl.read_parquet(ruta).filter(pl.col("tabla") == tabla).iter_rows(named=True):
                filas[f["codigo"]] = f
    for e in c.leer_vinculos_manuales(raiz / c.RUTA_VINCULOS_MANUALES):
        if e.tabla == tabla:
            filas[e.codigo] = {"pregunta_id": e.pregunta_id, "metodo": "manual", "motivo": "manual"}
    return vs, filas


def analizar(vs, filas):
    fams: dict[str, list] = defaultdict(list)
    for v in vs:
        fams[familia(v.codigo)].append(v)
    out = []
    for f, miembros in fams.items():
        if len(miembros) < MINIMO:
            continue
        pregs = {v.codigo: (filas.get(v.codigo) or {}).get("pregunta_id") for v in miembros}
        con = {k: p for k, p in pregs.items() if p}
        distintas = set(con.values())
        estado = []
        if len(distintas) > 1:
            estado.append("mezcla")
        if con and len(con) < len(miembros):
            estado.append("incompleta")
        out.append((f, miembros, pregs, estado))
    return sorted(out, key=lambda x: (int(re.search(r"\d+", x[0]).group()), x[0]))


def informe(tabla: str, raiz: Path) -> str:
    vs, filas = cargar(raiz, tabla)
    fams = analizar(vs, filas)
    marcadas = [x for x in fams if x[3]]
    L = [f"# M1-04 — Coherencia entre variables hermanas de {tabla} (sin LLM)\n",
         f"Generado por `m1-04_coherencia.py` con `vinculos.parquet`, `vinculos_llm.parquet` y `curados/inferencia/vinculos_manuales.yaml`. "
         f"Familia = variables con el mismo prefijo (letras + número: H12A, H12B… → H12); solo las de {MINIMO} o más. "
         f"**{len(fams)} familias; {len(marcadas)} marcadas** ({sum('mezcla' in x[3] for x in fams)} con preguntas distintas, "
         f"{sum('incompleta' in x[3] for x in fams)} con miembros vinculados y otros no). Una marca no es un error: es lo que hay que mirar.\n",
         "| Familia | Miembros | Vinculados | Preguntas a las que apuntan | Marca |", "|---|---|---|---|---|"]
    for f, miembros, pregs, estado in fams:
        cnt = Counter(p for p in pregs.values() if p)
        preg = ", ".join(f"{p} ×{n}" for p, n in sorted(cnt.items())) or "—"
        L.append(f"| {f} | {len(miembros)} | {sum(1 for p in pregs.values() if p)} | {preg} | {', '.join(estado) or 'coherente'} |")
    L.append("\n**Cómo leerlo.** *Incompleta* es la marca que más importa: en una familia de opción múltiple (H12, H32, H37…) todos los miembros "
             "deberían apuntar a la misma pregunta, así que los que quedaron «rechazada_por_verificacion» o «no_encontrada» son candidatos a revisar "
             "a mano. *Mezcla* es normal cuando la familia es una secuencia de preguntas distintas (H31: tos, respiración, bebidas…; H44: lugar, días, "
             "sigue enfermo): ahí lo que se mira es que cada miembro caiga en la pregunta que le toca.\n")
    L.append("\n## Detalle de las familias marcadas\n")
    por_codigo = {v.codigo: v for v in vs}
    for f, miembros, pregs, estado in marcadas:
        L.append(f"### {f} — {', '.join(estado)}\n")
        L.append("| Variable | Etiqueta | Pregunta | Cómo |")
        L.append("|---|---|---|---|")
        for v in miembros:
            x = filas.get(v.codigo) or {}
            cómo = x.get("metodo") or "sin mirar"
            if x.get("motivo") and not x.get("pregunta_id"):
                cómo += f" ({x['motivo']})"
            L.append(f"| {v.codigo} | {por_codigo[v.codigo].etiqueta[:70]} | {pregs[v.codigo] or '—'} | {cómo} |")
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    print(informe(sys.argv[1] if len(sys.argv) > 1 else "REC43", Path(__file__).resolve().parents[3]))
