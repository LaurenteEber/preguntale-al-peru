"""M1-04, tarea 3 — medir cuántas variables se vinculan sin LLM (diccionario y expresiones regulares), por tabla, y qué variables usan
las recetas. Es la hipótesis de tecnologias.md §6: «los códigos de la ENDES no siguen el número de pregunta». Solo lee y cuenta."""
from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .cuestionarios import Candidatos, VariableDic, Vinculo, _config, motivo_sin_pregunta

TABLAS_DE_LA_MEDICION = ("RECH6", "REC43", "REC0111")


def k_candidatos() -> int:
    return int(_config()["candidatos_k"]["valor"])


def variables_de_recetas(raiz: Path, variables: list[VariableDic]) -> set[tuple[str, str]]:
    """(tabla, variable) que usan las recetas de `curados/inferencia/recetas/`: las del indicador, las del universo, los predicados del
    universo analítico, las del diseño muestral de los archivos de la receta y las de los cortes que permite. Se leen los YAML tal
    cual (sin el esquema de recetas.py, que es de otra historia)."""
    raiz = Path(raiz)
    por_codigo: dict[str, set[str]] = {}
    for v in variables:
        por_codigo.setdefault(v.codigo, set()).add(v.tabla)
    universos = {u["id"]: u for u in yaml.safe_load((raiz / "curados/inferencia/universos_analiticos.yaml").read_text(encoding="utf-8"))["universos"]}
    cortes = {c["id"]: c for c in yaml.safe_load((raiz / "curados/inferencia/cortes_estandar.yaml").read_text(encoding="utf-8"))["cortes"]}
    diseno = list(csv.DictReader((raiz / "curados/inferencia/diseno_muestral.csv").open(encoding="utf-8")))
    out: set[tuple[str, str]] = set()
    for f in sorted((raiz / "curados/inferencia/recetas").glob("*.yaml")):
        r = yaml.safe_load(f.read_text(encoding="utf-8"))
        tablas_receta: set[str] = set()
        for c in (r.get("indicador") or {}).get("condiciones", []) + (r.get("universo") or {}).get("restricciones", []):
            out.add((c["archivo"], c["variable"]))
            tablas_receta.add(c["archivo"])
        u = universos.get(r.get("universo_analitico"))
        if u:
            for pr in u.get("predicados", []):
                for t in u["aplica_a"]["archivos"]:                      # el archivo que declara esa variable
                    if t in por_codigo.get(pr["var"], ()):
                        out.add((t, pr["var"]))
            tablas_receta |= set(u["aplica_a"]["archivos"])
        for corte in r.get("cortes_permitidos", []):
            for e in (cortes.get(corte, {}).get("por_encuesta") or {}).get(r.get("encuesta"), []):
                if e.get("unidad") in (r.get("unidad"), "hogar"):
                    out.add((e["archivo"], e["variable"]))
        for d in diseno:
            if d["archivo"] in tablas_receta or d["archivo"] == "RECH0":
                if d["archivo"] in tablas_receta or d["archivo"] == "RECH0":
                    for expr in (d["peso_expr"], d["estrato_expr"], d["psu_expr"]):
                        for cod in por_codigo:
                            if cod in expr and d["archivo"] in por_codigo[cod]:
                                out.add((d["archivo"], cod))
    return {(t, c) for t, c in out if t in por_codigo.get(c, ())}


@dataclass
class FilaMedicion:
    tabla: str
    total: int
    por_diccionario: int = 0
    por_regla: int = 0
    sin_pregunta_administrativa: int = 0
    sin_pregunta_construida: int = 0
    pendientes: int = 0                                 # los que necesitan al LLM
    por_llm: int | None = None                          # None = el LLM no se corrió

    @property
    def pct_sin_llm(self) -> float:
        return round(100 * (self.por_diccionario + self.por_regla) / self.total, 1) if self.total else 0.0


def medir(variables: list[VariableDic], vinculos: dict[tuple[str, str], Vinculo], tablas: list[str] | None = None,
          solo: set[tuple[str, str]] | None = None) -> list[FilaMedicion]:
    """Cuenta por tabla (o solo las variables de `solo`): cuántas quedan vinculadas por el diccionario, por la regla del código,
    cuántas no tienen pregunta por ser administrativas o construidas y cuántas quedan para el LLM."""
    filas: dict[str, FilaMedicion] = {}
    for v in variables:
        if (tablas and v.tabla not in tablas) or (solo is not None and (v.tabla, v.codigo) not in solo):
            continue
        f = filas.setdefault(v.tabla, FilaMedicion(v.tabla, 0))
        f.total += 1
        vin = vinculos.get((v.tabla, v.codigo))
        if vin and vin.metodo == "diccionario":
            f.por_diccionario += 1
        elif vin and vin.metodo == "regla":
            f.por_regla += 1
        elif (m := motivo_sin_pregunta(v)) == "administrativa":
            f.sin_pregunta_administrativa += 1
        elif m == "construida":
            f.sin_pregunta_construida += 1
        else:
            f.pendientes += 1
    return [filas[t] for t in sorted(filas)]


def recall_de_candidatos(variables: list[VariableDic], vinculos: dict[tuple[str, str], Vinculo], candidatos: Candidatos,
                         cuests: dict[str, list[str]], k: int) -> dict:
    """¿Entre las k preguntas candidatas que verá el LLM está la verdadera? Se mide con las variables que ya se vincularon por la regla
    del código (su pregunta se conoce): es el único conjunto con respuesta conocida. Informa aciertos y total (no es una cifra de
    precisión del LLM, solo del recorte de candidatos)."""
    aciertos = total = 0
    for v in variables:
        vin = vinculos.get((v.tabla, v.codigo))
        if not vin or vin.metodo != "regla":
            continue
        total += 1
        top = candidatos.de(v, cuests.get(v.tabla, []), k)
        aciertos += any(q.id == vin.pregunta_id for q in top)
    return {"k": k, "variables_con_respuesta_conocida": total, "con_la_pregunta_entre_los_candidatos": aciertos,
            "porcentaje": round(100 * aciertos / total, 1) if total else None}


def recall_de_muestra(variables: list[VariableDic], conocidas: dict[tuple[str, str], str], candidatos: Candidatos,
                      cuests: dict[str, list[str]], k: int) -> dict:
    """Como `recall_de_candidatos`, pero con una muestra de variables cuya pregunta se conoce por otra vía (`conocidas`: (tabla, código) →
    id de pregunta), y con el puesto de la pregunta correcta en el orden completo de candidatas (1 = la más parecida; None si no es del
    cuestionario de esa tabla). Solo mide el recorte; no decide ningún vínculo."""
    filas = []
    por_clave = {(v.tabla, v.codigo): v for v in variables}
    for clave, pid in sorted(conocidas.items()):
        v = por_clave.get(clave)
        if v is None:
            continue
        orden = [q.id for q in candidatos.de(v, cuests.get(v.tabla, []), len(candidatos.preguntas))]
        puesto = orden.index(pid) + 1 if pid in orden else None
        filas.append({"variable": f"{clave[0]}.{clave[1]}", "etiqueta": v.etiqueta, "pregunta": pid, "puesto": puesto,
                      "entre_los_candidatos": puesto is not None and puesto <= k})
    n = sum(f["entre_los_candidatos"] for f in filas)
    return {"k": k, "total": len(filas), "entre_los_candidatos": n, "porcentaje": round(100 * n / len(filas), 1) if filas else None, "filas": filas}


# ------------------------------------------------------------------ informes en Markdown (evidencia)

def _tabla_md(cab: list[str], filas: list[list]) -> str:
    return "\n".join(["| " + " | ".join(cab) + " |", "|" + "|".join("---" for _ in cab) + "|"] + ["| " + " | ".join(str(x) for x in f) + " |" for f in filas])


def informe_cuestionarios(preguntas: list, variables: list[VariableDic], vars_indice: dict[str, set[str]], fecha: str) -> str:
    """Conteo de preguntas por cuestionario y sección, y de variables del diccionario frente al índice (criterio 1 de M1-04)."""
    por_c: dict[str, Counter] = {}
    matrices: Counter = Counter()
    calendario: Counter = Counter()
    for q in preguntas:
        if q.tipo == "matriz":
            matrices[q.cuestionario] += 1
        elif q.tipo == "calendario":
            calendario[q.cuestionario] += 1
        else:
            por_c.setdefault(q.cuestionario, Counter())[q.seccion] += 1
    out = [f"# M1-04 — Cuestionarios y diccionarios de la ENDES 2024 (extracción)\n\nGenerado el {fecha} por `pap cuestionarios informe`. "
           "Los textos salen de los PDF oficiales registrados (`endes-2024-cuestionario-*` y los «Diccionario - <tabla>.pdf» dentro de "
           "cada ZIP), leídos con `pdfplumber` en el lector aislado (tiempo y memoria acotados). Todo queda en `propuesto`.\n"]
    for c in ("hogar", "individual", "salud"):
        n = sum(por_c.get(c, {}).values())
        out.append(f"## Cuestionario {c}: {n} preguntas" + (f" y {matrices[c]} páginas de matriz (columnas del listado, no separables)" if matrices[c] else "")
                   + (f" y {calendario[c]} páginas del calendario" if calendario[c] else "") + "\n")
        out.append(_tabla_md(["Sección", "Preguntas"], [[s or "(sin sección)", k] for s, k in por_c.get(c, Counter()).items()]) + "\n")
    out.append("## Diccionarios por tabla frente al índice de variables\n")
    por_t: Counter = Counter(v.tabla for v in variables)
    filas, faltan_tot = [], 0
    for t in sorted(vars_indice):
        en_dic = {v.codigo for v in variables if v.tabla == t}
        falta = sorted(vars_indice[t] - en_dic)
        faltan_tot += len(falta)
        filas.append([t, len(vars_indice[t]), por_t.get(t, 0), len(falta), ", ".join(falta[:6]) + ("…" if len(falta) > 6 else "")])
    out.append(_tabla_md(["Tabla", "Variables en el índice", "En el diccionario", "Sin diccionario", "Cuáles"], filas))
    out.append(f"\nTotal: {sum(len(v) for v in vars_indice.values())} variables en el índice, {len(variables)} en los diccionarios, "
               f"{faltan_tot} del índice sin entrada de diccionario (columnas derivadas por el almacén, como `HHID`, y algunas que el INEI no documenta).\n")
    out.append("## Límites de esta extracción (para quien revise)\n\n"
               "- El diseño de los PDF cambia entre cuestionarios y páginas; el lector se guía por la posición de las palabras (valores en "
               "`cuestionarios.*` de `curados/inferencia/parametros.yaml`). Las **opciones** de respuesta pueden traer ruido (por ejemplo un «(PASE A 413)» "
               "como si fuera una opción) y los **saltos** solo valen si nombran una pregunta que existe en el mismo cuestionario.\n"
               "- Las **matrices** (las columnas «(1) (2) …» del listado del hogar y tablas parecidas) no se separan en preguntas: cada página es una "
               "sola entrada de tipo `matriz` con su encabezado. Los vínculos de esas variables serán a nivel de página.\n"
               "- Las páginas sin encabezado «SECCIÓN» que no son de la sección anterior se fijan en `cuestionarios.paginas_especiales`: el anexo "
               "del carné (pp. 82–84 del individual, preguntas 456 a 466E) y el **calendario** (pp. 89–90), que no tiene preguntas numeradas: cada "
               "página es una entrada de tipo `calendario` con su texto, y el vínculo de sus variables (REC82) será a nivel de página.\n"
               "- Si una pregunta aparece en varias páginas (la misma tabla para la 1.ª, 2.ª y 3.ª persona) queda una vez, con el texto más largo.\n"
               "- En el hogar, la sección 4 (peso y talla) y casi toda la 5 (hemoglobina) son formularios de tabla, sin el encabezado de preguntas: "
               "dan pocas o ninguna pregunta. Ahí están las mediciones de los niños (HC53 a HC57A, HC70…) que usan las recetas; su vínculo, si lo "
               "hay, será a las pocas preguntas extraídas o `sin_pregunta` con su motivo. No se corrigió a mano (AGENTS.md §7).\n"
               "- Todo queda en `propuesto`; el visto es de M1-07.\n")
    return "\n".join(out)


def informe_vinculos(filas: list[FilaMedicion], filas_recetas: list[FilaMedicion], filas_todas: list[FilaMedicion], recall: dict | None,
                     recetas: set[tuple[str, str]], fecha: str) -> str:
    def fila(f: FilaMedicion):
        llm = "no corrido" if f.por_llm is None else f.por_llm
        return [f.tabla, f.total, f"{f.por_diccionario} ({100*f.por_diccionario/f.total:.1f} %)", f"{f.por_regla} ({100*f.por_regla/f.total:.1f} %)",
                f"{f.sin_pregunta_administrativa + f.sin_pregunta_construida}", f.pendientes, llm]
    cab = ["Tabla", "Variables", "Por diccionario", "Por regla del código", "Sin pregunta (administrativa o construida)", "Quedan para el LLM", "Por LLM"]
    tot = lambda fs, a: sum(getattr(f, a) for f in fs)
    out = [f"# M1-04 — Cuántas variables se vinculan sin LLM (tarea 3)\n\nGenerado el {fecha} por `pap cuestionarios informe`. "
           "**Hipótesis de `tecnologias.md` §6:** en la ENDES los códigos no siguen el número de pregunta, así que el diccionario y las expresiones regulares "
           "vinculan poco y el resto lo propone Sonnet fuera de línea. Se midió antes de usar el LLM.\n",
           "## Las tres tablas pedidas\n", _tabla_md(cab, [fila(f) for f in filas]) + "\n",
           "## Las variables de las 3 recetas\n",
           "Variables que usan las recetas (indicador, universo, universo analítico, diseño muestral y cortes permitidos): "
           + ", ".join(f"`{t}.{c}`" for t, c in sorted(recetas)) + ".\n",
           _tabla_md(cab, [fila(f) for f in filas_recetas]) + "\n",
           f"En conjunto: {tot(filas_recetas,'total')} variables; {tot(filas_recetas,'por_diccionario')+tot(filas_recetas,'por_regla')} vinculadas sin LLM; "
           f"{tot(filas_recetas,'sin_pregunta_administrativa')+tot(filas_recetas,'sin_pregunta_construida')} sin pregunta por ser administrativas o construidas; "
           f"{tot(filas_recetas,'pendientes')} esperan al LLM. **Meta (≥ 95 % con su texto vinculado): no se puede decir que se cumple** hasta correr el lote.\n",
           "## Las 34 tablas\n", _tabla_md(cab, [fila(f) for f in filas_todas]) + "\n",
           f"Total: {tot(filas_todas,'total')} variables; por diccionario {tot(filas_todas,'por_diccionario')}; por regla {tot(filas_todas,'por_regla')} "
           f"({100*(tot(filas_todas,'por_diccionario')+tot(filas_todas,'por_regla'))/max(tot(filas_todas,'total'),1):.1f} %); sin pregunta "
           f"{tot(filas_todas,'sin_pregunta_administrativa')+tot(filas_todas,'sin_pregunta_construida')}; para el LLM {tot(filas_todas,'pendientes')}.\n"]
    if recall:
        out.append("## ¿Están las preguntas correctas entre las candidatas que verá el LLM?\n")
        out.append(f"Con las {recall['variables_con_respuesta_conocida']} variables vinculadas por regla (su pregunta se conoce) se probó el recorte a "
                   f"{recall['k']} candidatas por palabras en común: la pregunta correcta está entre ellas en {recall['con_la_pregunta_entre_los_candidatos']} "
                   f"({recall['porcentaje']} %). Es un piso para el LLM: nunca podrá acertar una pregunta que no le llegue. No es una cifra de acierto del LLM.\n")
    return "\n".join(out)
