"""Fichas de tabla y bloques temáticos (M1-06; docs/diseno/fichas.md).

`pap fichas generar | validar | ver` arma, desde tablas curadas y el índice de variables:

- `biblioteca/variables/fichas_tabla.parquet`: una ficha por encuesta × año × tabla (fichas.md §5): los campos escritos a mano
  (`curados/inferencia/fichas/<encuesta>.yaml`) más los derivados (descargas, índice, uniones, diseño muestral, recetas, bloques);
- `biblioteca/variables/bloques.parquet`: los bloques de `curados/inferencia/bloques/<encuesta>.yaml` con sus variables resueltas;
- la columna `bloque_id` de `biblioteca/variables/variables.parquet` (ninguna otra columna cambia).

Nada de esto calcula ni cambia una cifra. Las variables de un bloque se declaran por prefijo, por rango de posición entre dos códigos
o por lista (`rango` es un par; `rangos`, varios pares: la unión); solo cuentan las de clase `categoria` o `medida` (las llaves, pesos, diseño y geografía no llevan bloque). Los archivos
salen ordenados y con la misma compresión que el resto del índice: dos corridas dan los mismos bytes (regla 8 de `validar`).

`validar` aplica las 8 reglas de fichas.md §9. Las que necesitan el almacén de crudos (7: documentos y miembros de ZIP) o los
microdatos (6: edad observada) fallan si faltan, no se saltan; `--sin-microdatos` deja la comprobación de la edad sin hacer y lo dice.
"""
from __future__ import annotations

import json
import re
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import yaml

from ..config import Rutas
from ..errores import PapError

RAIZ_REPO = Path(__file__).resolve().parents[3]
TIPOS_TABLA = ("base", "detalle", "medicion", "lista", "calendario", "construida")
MODOS = ("declarado", "medido", "mixto")
PAPELES = ("resultado", "servicio", "recurso", "contexto")
EDAD_UNIDADES = ("meses", "anios")
SEXOS = ("ambos", "mujer", "hombre")
TIPOS_FUENTE = ("muestra", "registro", "censo", "presupuesto")
ESTADOS = ("propuesto", "revisado")
TEMA_ESTADOS = ("provisional", "aprobado")
CLASES_CON_BLOQUE = ("categoria", "medida")
CAMPOS_FICHA = ("nombre_corto", "descripcion", "cuestionario", "secciones", "tipo_tabla", "poblacion", "quien_tiene_fila",
                "informante", "modo", "avisos", "documentos", "estado")
CAMPOS_POBLACION = ("texto", "sujeto", "edad_min", "edad_max", "edad_unidad", "sexo", "condicion", "variable_edad")


@dataclass(frozen=True)
class Problema:
    regla: int
    objeto: str
    mensaje: str

    def __str__(self) -> str:
        return f"regla {self.regla} · {self.objeto}: {self.mensaje}"


# ------------------------------------------------------------------ lectura de las tablas curadas

def _yaml(ruta: Path) -> dict:
    if not ruta.exists():
        raise PapError(f"Falta {ruta}")
    return yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}


@dataclass
class Fuentes:
    """Todo lo que lee `generar` y `validar`, ya cargado: las tablas curadas y el índice."""
    raiz: Path
    encuesta: str
    anio: int
    temas: dict
    fichas: dict
    bloques: dict
    descargas: dict
    archivos_yaml: dict
    archivos: "pl.DataFrame"
    variables: "pl.DataFrame"
    diseno: list[dict]
    territorios: list[dict]
    inferencia_verificada: list[dict]
    recetas: list[dict]

    @property
    def carpeta_indice(self) -> Path:
        return self.raiz / "biblioteca" / "variables"


def cargar(raiz: Path, encuesta: str, anio: int) -> Fuentes:
    import csv

    import polars as pl

    raiz = Path(raiz)
    cur = raiz / "curados" / "inferencia"
    ind = raiz / "biblioteca" / "variables"
    for f in ("archivos.parquet", "variables.parquet"):
        if not (ind / f).exists():
            raise PapError(f"Falta {ind / f}: corre antes `pap variables indexar --encuesta {encuesta} --anio {anio}`")
    leer_csv = lambda p: list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []
    recetas = [yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted((cur / "recetas").glob("*.yaml"))] if (cur / "recetas").exists() else []
    return Fuentes(
        raiz=raiz, encuesta=encuesta, anio=anio, temas=_yaml(cur / "temas.yaml"), fichas=_yaml(cur / "fichas" / f"{encuesta}.yaml"),
        bloques=_yaml(cur / "bloques" / f"{encuesta}.yaml"), descargas=_yaml(cur / "descargas" / f"{encuesta.lower()}_{anio}.yaml"),
        archivos_yaml=_yaml(cur / f"archivos_{encuesta.lower()}_{anio}.yaml"),
        archivos=pl.read_parquet(ind / "archivos.parquet").filter(pl.col("anio") == anio),
        variables=pl.read_parquet(ind / "variables.parquet").filter(pl.col("anio") == anio).sort("archivo", "posicion"),
        diseno=[r for r in leer_csv(cur / "diseno_muestral.csv") if r["encuesta"] == encuesta and int(r["anio"]) == anio],
        territorios=(_yaml(cur / "territorios.yaml").get("territorios") or []),
        inferencia_verificada=leer_csv(raiz / "catalogo" / "inferencia_verificada.csv"), recetas=recetas)


def _temas(f: Fuentes) -> dict[str, set[str]]:
    return {t["id"]: {s["id"] for s in t.get("subtemas") or []} for t in f.temas.get("temas") or []}


def _tablas_en_anio(f: Fuentes) -> dict[str, dict]:
    """Fichas escritas a mano que valen para el año."""
    return {t: d for t, d in (f.fichas.get("tablas") or {}).items() if d["anios"][0] <= f.anio <= d["anios"][1]}


# ------------------------------------------------------------------ bloques: variables resueltas

def resolver_variables(spec: dict, vars_tabla: list[dict], objeto: str, problemas: list[Problema]) -> list[str]:
    """Las variables de un bloque, en el orden de la tabla. `vars_tabla` = filas del índice de esa tabla ordenadas por `posicion`.
    Prefijos y rangos saltan las variables que no son `categoria` o `medida`; una variable puesta en `lista` que no lo es es un error."""
    spec = spec or {}
    nombres = [v["variable"] for v in vars_tabla]
    clase = {v["variable"]: v["clase"] for v in vars_tabla}
    pos = {n: i for i, n in enumerate(nombres)}
    elegidas: set[str] = set()
    vacio = True
    for p in spec.get("prefijos") or []:
        vacio = False
        hit = [n for n in nombres if n.startswith(p)]
        if not hit:
            problemas.append(Problema(4, objeto, f"el prefijo {p!r} no coincide con ninguna variable de la tabla"))
        elegidas.update(n for n in hit if clase[n] in CLASES_CON_BLOQUE)
    for n in spec.get("lista") or []:
        vacio = False
        if n not in pos:
            problemas.append(Problema(4, objeto, f"la variable {n} de la lista no existe en la tabla"))
        elif clase[n] not in CLASES_CON_BLOQUE:
            problemas.append(Problema(4, objeto, f"la variable {n} es de clase {clase[n]} y no lleva bloque"))
        else:
            elegidas.add(n)
    rangos = ([spec["rango"]] if spec.get("rango") else []) + list(spec.get("rangos") or [])
    for rango in rangos:
        vacio = False
        if len(rango) != 2 or any(r not in pos for r in rango):
            problemas.append(Problema(4, objeto, f"el rango {rango} no son dos variables de la tabla"))
        elif pos[rango[0]] > pos[rango[1]]:
            problemas.append(Problema(4, objeto, f"el rango {rango} está al revés (la primera va después de la última)"))
        else:
            elegidas.update(n for n in nombres[pos[rango[0]]:pos[rango[1]] + 1] if clase[n] in CLASES_CON_BLOQUE)
    if vacio:
        problemas.append(Problema(4, objeto, "el bloque no declara variables (ni prefijos, ni lista, ni rango)"))
    return [n for n in nombres if n in elegidas]


def asignar_bloques(f: Fuentes, problemas: list[Problema]) -> tuple[list[dict], dict[str, str]]:
    """Bloques resueltos (con `variables`) y `var_id → bloque_id`. Una variable en dos bloques es un error (regla 4)."""
    por_tabla: dict[str, list[dict]] = {}
    for r in f.variables.iter_rows(named=True):
        por_tabla.setdefault(r["archivo"], []).append(r)
    asignacion: dict[str, str] = {}
    duenio: dict[str, str] = {}
    salida, ids = [], Counter(b["id"] for b in f.bloques.get("bloques") or [])
    for b in f.bloques.get("bloques") or []:
        if ids[b["id"]] > 1:
            problemas.append(Problema(3, b["id"], "el id del bloque está repetido"))
            ids[b["id"]] = 0
        if not (b["anios"][0] <= f.anio <= b["anios"][1]):
            continue
        tabla = b["tabla"]
        if tabla not in por_tabla:
            problemas.append(Problema(1, b["id"], f"la tabla {tabla} no existe en el índice de {f.encuesta} {f.anio}"))
            continue
        vs = resolver_variables(b.get("variables"), por_tabla[tabla], b["id"], problemas)
        vid = {r["variable"]: r["var_id"] for r in por_tabla[tabla]}
        for n in vs:
            if vid[n] in duenio:
                problemas.append(Problema(4, f"{tabla}.{n}", f"está en dos bloques: {duenio[vid[n]]} y {b['id']}"))
            else:
                duenio[vid[n]] = b["id"]
                asignacion[vid[n]] = b["id"]
        salida.append({**b, "variables_resueltas": vs})
    return salida, asignacion


def cobertura(f: Fuentes, asignacion: dict[str, str]) -> dict[str, dict]:
    """Por tabla: variables `categoria` o `medida`, cuántas tienen bloque, porcentaje y número de bloques."""
    cob: dict[str, dict] = {}
    for r in f.variables.iter_rows(named=True):
        c = cob.setdefault(r["archivo"], {"variables": 0, "con_bloque": 0, "sin_bloque": [], "bloques": set()})
        if r["clase"] in CLASES_CON_BLOQUE:
            c["variables"] += 1
            if r["var_id"] in asignacion:
                c["con_bloque"] += 1
                c["bloques"].add(asignacion[r["var_id"]])
            else:
                c["sin_bloque"].append(r["variable"])
    for c in cob.values():
        c["bloques"] = len(c["bloques"])
        c["porcentaje"] = (100.0 * c["con_bloque"] / c["variables"]) if c["variables"] else 100.0
    return cob


# ------------------------------------------------------------------ campos derivados de la ficha

def _modulos(f: Fuentes) -> dict[str, dict]:
    """tabla (nombre del índice) → módulo de `descargas`."""
    salida = {}
    for m in f.descargas.get("modulos") or []:
        for t in m.get("tablas") or []:
            salida[t.replace(" ", "_")] = m
    return salida


def _recetas_de(f: Fuentes, tabla: str) -> list[str]:
    def archivos(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "archivo" and isinstance(v, str):
                    yield v
                else:
                    yield from archivos(v)
        elif isinstance(x, list):
            for v in x:
                yield from archivos(v)
    return sorted({r["id"] for r in f.recetas if r.get("id") and tabla in set(archivos({k: r[k] for k in ("indicador", "universo", "transformaciones") if k in r}))})


def _tabla_base(f: Fuentes, tabla: str) -> str | None:
    for r in f.archivos_yaml.get("relaciones") or []:
        if r["hijo"] == tabla:
            return r["padre"]
    return None


def _diseno(f: Fuentes, tabla: str) -> dict:
    filas = [r for r in f.diseno if r["archivo"] == tabla]
    if not filas:
        return {"tiene_diseno": False, "peso": None, "estrato": None, "upm": None, "nivel_submuestra": None, "permite_totales": None,
                "alcance_territorial": None}
    uniq = lambda k: " | ".join(dict.fromkeys(r[k] for r in filas if r[k]))
    cat = next((r for r in f.inferencia_verificada if r["fuente"] == f"INEI-{f.encuesta}" and int(r["anio"]) == f.anio
                and r["modulo"] in ("*", "")), None)
    alcance = f"hasta {cat['nivel_maximo']}: {cat['dominios_anuales']}" if cat else None
    return {"tiene_diseno": True, "peso": uniq("peso_expr"), "estrato": uniq("estrato_expr"), "upm": uniq("psu_expr"),
            "nivel_submuestra": uniq("nivel_submuestra"),
            "permite_totales": "no" if any(r["peso_normalizado"].strip().lower() in ("sí", "si") for r in filas) else "sí",
            "alcance_territorial": alcance}


def construir_fichas(f: Fuentes, bloques: list[dict]) -> list[dict]:
    """Una fila por tabla del índice que tenga ficha (fichas.md §5)."""
    mods, hand = _modulos(f), _tablas_en_anio(f)
    arch = {r["archivo"]: r for r in f.archivos.iter_rows(named=True)}
    cfg_arch = f.archivos_yaml.get("archivos") or {}
    por_tabla: dict[str, list[dict]] = {}
    for r in f.variables.iter_rows(named=True):
        por_tabla.setdefault(r["archivo"], []).append(r)
    enc = f.descargas.get("encuesta") or {}
    filas = []
    for t in sorted(hand):
        if t not in arch:
            continue
        h, vs, a = hand[t], por_tabla.get(t, []), arch[t]
        m = mods.get(t) or {}
        pob = h.get("poblacion") or {}
        mis_bloques = [b for b in bloques if b["tabla"] == t]
        por_tema = Counter()
        for b in mis_bloques:
            por_tema[b["tema"]] += len(b["variables_resueltas"])
        temas = [k for k, _ in sorted(por_tema.items(), key=lambda kv: (-kv[1], kv[0]))]
        clases = Counter(v["clase"] for v in vs)
        baterias = Counter(v["grupo"] for v in vs if v["grupo"])
        filas.append({
            "encuesta": f.encuesta, "anio": f.anio, "tabla": t,
            "nombre_corto": h["nombre_corto"], "descripcion": h["descripcion"], "tipo_fuente": f.fichas.get("tipo_fuente"),
            "cuestionario": h.get("cuestionario"), "secciones": list(h.get("secciones") or []), "tipo_tabla": h["tipo_tabla"],
            "poblacion_texto": pob.get("texto"), "poblacion_sujeto": pob.get("sujeto"), "poblacion_edad_min": pob.get("edad_min"),
            "poblacion_edad_max": pob.get("edad_max"), "poblacion_edad_unidad": pob.get("edad_unidad"), "poblacion_sexo": pob.get("sexo"),
            "poblacion_condicion": pob.get("condicion"), "poblacion_variable_edad": pob.get("variable_edad"),
            "quien_tiene_fila": h["quien_tiene_fila"], "informante": h.get("informante"), "modo": h.get("modo"),
            "avisos": list(h.get("avisos") or []), "documentos": json.dumps(h.get("documentos") or [], ensure_ascii=False),
            "estado": h["estado"],
            "modulo_codigo": m.get("codigo"), "modulo_nombre": m.get("nombre"), "codigo_encuesta": enc.get("codigo"),
            "periodo": enc.get("periodo_nombre"), "recurso": m.get("recurso"), "formato": a["formato"],
            "huella_datos": a["huella_datos"], "n_filas": a["n_filas"], "n_variables": a["n_variables"],
            "unidad": (cfg_arch.get(t) or {}).get("unidad"), "llave": list((cfg_arch.get(t) or {}).get("llave") or []),
            "uniones": a["relaciones"], "tabla_base": _tabla_base(f, t),
            "variables_por_clase": json.dumps(dict(sorted(clases.items())), ensure_ascii=False),
            "baterias": json.dumps([{"prefijo": k, "n": n} for k, n in sorted(baterias.items())], ensure_ascii=False),
            **_diseno(f, t),
            "anios_disponibles": [f.anio], "cambios_vs_anio_anterior": None,
            "n_propuesto": sum(1 for v in vs if v["estado"] == "propuesto"), "n_revisado": sum(1 for v in vs if v["estado"] == "revisado"),
            "controles": json.dumps(dict(sorted(Counter(c for v in vs for c in (v["controles"] or [])).items())), ensure_ascii=False),
            "temas": temas, "bloques": sorted(b["id"] for b in mis_bloques), "recetas": _recetas_de(f, t),
            "conceptos": sorted({v["concepto_id"] for v in vs if v.get("concepto_id")})})
    return filas


def filas_bloques(f: Fuentes, bloques: list[dict]) -> list[dict]:
    filas = []
    for b in sorted(bloques, key=lambda b: (b["tabla"], b["id"])):
        p = b.get("poblacion") or {}
        vs = b["variables_resueltas"]
        filas.append({"bloque_id": b["id"], "encuesta": f.encuesta, "anio": f.anio, "tabla": b["tabla"], "nombre": b["nombre"],
                      "descripcion": b["descripcion"], "tema": b["tema"], "subtema": b["subtema"], "tema_estado": b["tema_estado"],
                      "papel": b["papel"], "poblacion": json.dumps(p, ensure_ascii=False) if p else None,
                      "ventana_referencia": b.get("ventana_referencia"), "seccion_cuestionario": b.get("seccion_cuestionario"),
                      "estado": b["estado"], "n_variables": len(vs), "variables": vs,
                      "primera_variable": vs[0] if vs else None, "ultima_variable": vs[-1] if vs else None})
    return filas


# ------------------------------------------------------------------ escritura

def _esquema_fichas():
    import polars as pl

    S, L, I = pl.String, pl.List(pl.String), pl.Int64
    return {"encuesta": S, "anio": pl.Int32, "tabla": S, "nombre_corto": S, "descripcion": S, "tipo_fuente": S, "cuestionario": S,
            "secciones": L, "tipo_tabla": S, "poblacion_texto": S, "poblacion_sujeto": S, "poblacion_edad_min": I,
            "poblacion_edad_max": I, "poblacion_edad_unidad": S, "poblacion_sexo": S, "poblacion_condicion": S,
            "poblacion_variable_edad": S, "quien_tiene_fila": S, "informante": S, "modo": S, "avisos": L, "documentos": S, "estado": S,
            "modulo_codigo": I, "modulo_nombre": S, "codigo_encuesta": I, "periodo": S, "recurso": S, "formato": S, "huella_datos": S,
            "n_filas": I, "n_variables": pl.Int32, "unidad": S, "llave": L, "uniones": S, "tabla_base": S, "variables_por_clase": S,
            "baterias": S, "tiene_diseno": pl.Boolean, "peso": S, "estrato": S, "upm": S, "nivel_submuestra": S, "permite_totales": S,
            "alcance_territorial": S, "anios_disponibles": pl.List(pl.Int32), "cambios_vs_anio_anterior": S, "n_propuesto": I,
            "n_revisado": I, "controles": S, "temas": L, "bloques": L, "recetas": L, "conceptos": L}


def _esquema_bloques():
    import polars as pl

    S = pl.String
    return {"bloque_id": S, "encuesta": S, "anio": pl.Int32, "tabla": S, "nombre": S, "descripcion": S, "tema": S, "subtema": S,
            "tema_estado": S, "papel": S, "poblacion": S, "ventana_referencia": S, "seccion_cuestionario": S, "estado": S,
            "n_variables": pl.Int32, "variables": pl.List(S), "primera_variable": S, "ultima_variable": S}


def _escribir(df, ruta: Path) -> None:
    tmp = ruta.with_name(f".{ruta.name}.tmp")
    df.write_parquet(tmp, compression="zstd", compression_level=3)
    tmp.replace(ruta)


def armar(f: Fuentes, problemas: list[Problema] | None = None):
    """(fichas, bloques, variables con `bloque_id`, cobertura, problemas de estructura). No escribe nada."""
    import polars as pl

    probs = problemas if problemas is not None else []
    bloques, asignacion = asignar_bloques(f, probs)
    fichas = pl.DataFrame(construir_fichas(f, bloques), schema=_esquema_fichas()).sort("tabla")
    bl = pl.DataFrame(filas_bloques(f, bloques), schema=_esquema_bloques()).sort("tabla", "bloque_id")
    ruta_v = f.carpeta_indice / "variables.parquet"
    v = pl.read_parquet(ruta_v)
    if "bloque_id" in v.columns:
        v = v.drop("bloque_id")
    mapa = pl.DataFrame({"var_id": list(asignacion), "bloque_id": list(asignacion.values())}, schema={"var_id": pl.String, "bloque_id": pl.String})
    v = v.join(mapa, on="var_id", how="left").sort("var_id")
    return fichas, bl, v, cobertura(f, asignacion), probs


def generar(raiz: Path, encuesta: str, anio: int, destino: Path | None = None) -> dict:
    """`pap fichas generar`. Si la estructura tiene problemas (reglas 1 a 5), no escribe nada. `destino` (pruebas y regla 8) escribe
    en otra carpeta una copia del índice con `bloque_id`; sin él, se escribe en `biblioteca/variables/`."""
    f = cargar(raiz, encuesta, anio)
    fichas, bl, v, cob, probs = armar(f)
    probs += revisar_estructura(f, bl, cob)
    if probs:
        raise PapError("No se generó nada; la estructura de las fichas o los bloques tiene problemas:\n  " + "\n  ".join(str(p) for p in probs))
    out = Path(destino) if destino else f.carpeta_indice
    out.mkdir(parents=True, exist_ok=True)
    _escribir(fichas, out / "fichas_tabla.parquet")
    _escribir(bl, out / "bloques.parquet")
    _escribir(v, out / "variables.parquet")
    return {"fichas": fichas.height, "bloques": bl.height, "bloques_por_tabla": {r["tabla"]: r["n"] for r in bl.group_by("tabla").len().rename({"len": "n"}).sort("tabla").iter_rows(named=True)},
            "cobertura": cob, "carpeta": out}


# ------------------------------------------------------------------ validación (fichas.md §9)

def _en_vocabulario(valor, vocab, obj, campo, probs, regla=3, permitir_vacio=True):
    if valor is None:
        if not permitir_vacio:
            probs.append(Problema(regla, obj, f"{campo} está vacío"))
    elif valor not in vocab:
        probs.append(Problema(regla, obj, f"{campo} = {valor!r} no está en {list(vocab)}"))


def revisar_estructura(f: Fuentes, bloques_df, cob: dict) -> list[Problema]:
    """Reglas 1, 2, 3, 4 (cobertura), 5 y la parte de la 6 que no necesita microdatos (edad_min ≤ edad_max)."""
    probs: list[Problema] = []
    en_indice = set(f.archivos["archivo"].to_list())
    hand = _tablas_en_anio(f)
    voc = f.fichas.get("vocabularios") or {}
    # 1. cada tabla del índice tiene ficha y cada ficha corresponde a una tabla que existe
    for t in sorted(en_indice - set(hand)):
        probs.append(Problema(1, t, "la tabla del índice no tiene ficha"))
    for t in sorted(set(f.fichas.get("tablas") or {}) - en_indice):
        d = f.fichas["tablas"][t]
        if d["anios"][0] <= f.anio <= d["anios"][1]:
            probs.append(Problema(1, t, f"la ficha vale para {f.anio} y la tabla no existe en el índice de ese año"))
    # 2. las tablas de cada módulo son exactamente los miembros de datos de su ZIP (según el índice, que se leyó de los ZIP)
    cod = (f.descargas.get("encuesta") or {}).get("codigo")
    zips = {}
    for r in f.archivos.iter_rows(named=True):
        zips.setdefault(r["zip"], set()).add(r["archivo"])
    vistos: set[str] = set()
    for m in f.descargas.get("modulos") or []:
        declaradas = {t.replace(" ", "_") for t in m.get("tablas") or []}
        reales = zips.get(f"{cod}-Modulo{m['codigo']}.zip", set())
        if declaradas != reales:
            probs.append(Problema(2, f"módulo {m['codigo']}", f"`tablas` de descargas {sorted(declaradas)} no son los datos del ZIP {sorted(reales)}"))
        if vistos & declaradas:
            probs.append(Problema(2, f"módulo {m['codigo']}", f"tablas repetidas en dos módulos: {sorted(vistos & declaradas)}"))
        vistos |= declaradas
    for t in sorted(en_indice - vistos):
        probs.append(Problema(2, t, "la tabla no está en la lista `tablas` de ningún módulo de descargas"))
    # 3. vocabularios
    temas = _temas(f)
    if f.temas.get("estado") not in TEMA_ESTADOS:
        probs.append(Problema(3, "temas.yaml", f"estado {f.temas.get('estado')!r} fuera de {TEMA_ESTADOS}"))
    _en_vocabulario(f.fichas.get("tipo_fuente"), TIPOS_FUENTE, "fichas", "tipo_fuente", probs, permitir_vacio=False)
    for t, d in sorted(hand.items()):
        faltan = [c for c in CAMPOS_FICHA if c not in d]
        if faltan:
            probs.append(Problema(3, t, f"faltan campos de la ficha: {faltan}"))
            continue
        extra = [c for c in (d.get("poblacion") or {}) if c not in CAMPOS_POBLACION]
        if extra:
            probs.append(Problema(3, t, f"campos de población que no existen: {extra}"))
        p = d.get("poblacion") or {}
        _en_vocabulario(d["tipo_tabla"], TIPOS_TABLA, t, "tipo_tabla", probs, permitir_vacio=False)
        _en_vocabulario(d["modo"], MODOS, t, "modo", probs)
        _en_vocabulario(d["estado"], ESTADOS, t, "estado", probs, permitir_vacio=False)
        _en_vocabulario(d["cuestionario"], voc.get("cuestionario") or [], t, "cuestionario", probs)
        _en_vocabulario(p.get("sujeto"), voc.get("sujeto") or [], t, "población.sujeto", probs)
        _en_vocabulario(p.get("edad_unidad"), EDAD_UNIDADES, t, "población.edad_unidad", probs)
        _en_vocabulario(p.get("sexo"), SEXOS, t, "población.sexo", probs)
        if (p.get("edad_min") is not None or p.get("edad_max") is not None) and not p.get("edad_unidad"):
            probs.append(Problema(3, t, "la población trae edades sin `edad_unidad`"))
        # 6 (sin datos)
        if p.get("edad_min") is not None and p.get("edad_max") is not None and p["edad_min"] > p["edad_max"]:
            probs.append(Problema(6, t, f"edad_min {p['edad_min']} es mayor que edad_max {p['edad_max']}"))
    for b in f.bloques.get("bloques") or []:
        o = b.get("id", "?")
        faltan = [c for c in ("id", "tabla", "anios", "nombre", "descripcion", "variables", "tema", "subtema", "tema_estado", "papel", "estado") if c not in b]
        if faltan:
            probs.append(Problema(3, o, f"faltan campos del bloque: {faltan}"))
            continue
        _en_vocabulario(b["papel"], PAPELES, o, "papel", probs, permitir_vacio=False)
        _en_vocabulario(b["estado"], ESTADOS, o, "estado", probs, permitir_vacio=False)
        _en_vocabulario(b["tema_estado"], TEMA_ESTADOS, o, "tema_estado", probs, permitir_vacio=False)
        if b["tema"] not in temas:
            probs.append(Problema(3, o, f"el tema {b['tema']!r} no está en temas.yaml"))
        elif b["subtema"] not in temas[b["tema"]]:
            probs.append(Problema(3, o, f"el subtema {b['subtema']!r} no es de {b['tema']} en temas.yaml"))
        # 5. la población del bloque no es más amplia que la de su tabla
        if b["tabla"] in hand:
            probs += _poblacion_bloque(o, b.get("poblacion") or {}, hand[b["tabla"]].get("poblacion") or {})
    # 4. cobertura: 100 % en las tablas que tienen bloques o que están `revisado`
    con_bloques = set(bloques_df["tabla"].to_list()) if bloques_df.height else set()
    for t, c in sorted(cob.items()):
        exigida = t in con_bloques or (t in hand and hand[t].get("estado") == "revisado")
        if exigida and c["sin_bloque"]:
            probs.append(Problema(4, t, f"{len(c['sin_bloque'])} de {c['variables']} variables categoria o medida sin bloque "
                                        f"({c['porcentaje']:.1f} %): {', '.join(c['sin_bloque'][:12])}{'…' if len(c['sin_bloque']) > 12 else ''}"))
    return probs


def _poblacion_bloque(obj: str, b: dict, t: dict) -> list[Problema]:
    probs = []
    if not b:
        return probs
    for c in b:
        if c not in CAMPOS_POBLACION:
            probs.append(Problema(3, obj, f"campo de población del bloque que no existe: {c}"))
    if b.get("edad_min") is not None or b.get("edad_max") is not None:
        ub, ut = b.get("edad_unidad") or t.get("edad_unidad"), t.get("edad_unidad")
        if ub != ut:
            probs.append(Problema(5, obj, f"la edad del bloque va en {ub} y la de la tabla en {ut}: no se pueden comparar"))
        else:
            lo, hi = b.get("edad_min"), b.get("edad_max")
            if lo is not None and t.get("edad_min") is not None and lo < t["edad_min"]:
                probs.append(Problema(5, obj, f"edad_min {lo} es menor que la de la tabla ({t['edad_min']})"))
            if hi is not None and t.get("edad_max") is not None and hi > t["edad_max"]:
                probs.append(Problema(5, obj, f"edad_max {hi} es mayor que la de la tabla ({t['edad_max']})"))
            if lo is not None and hi is not None and lo > hi:
                probs.append(Problema(6, obj, f"edad_min {lo} es mayor que edad_max {hi}"))
    if b.get("sexo") is not None and t.get("sexo") in ("mujer", "hombre") and b["sexo"] != t["sexo"]:
        probs.append(Problema(5, obj, f"el bloque es de sexo {b['sexo']} y la tabla de {t['sexo']}"))
    return probs


def _edad_observada(f: Fuentes, tabla: str, variable: str) -> tuple[float, float, int] | None:
    """(mínimo, máximo, n) de la edad en el Parquet de la tabla, sin nulos ni códigos especiales del índice."""
    import duckdb
    import polars as pl

    ruta = f.raiz / "biblioteca" / "microdatos" / f.encuesta / str(f.anio) / f"{tabla}.parquet"
    if not ruta.exists():
        raise PapError(f"Falta {ruta}: la regla 6 necesita los microdatos (o pasa --sin-microdatos)")
    esp = f.variables.filter((pl.col("archivo") == tabla) & (pl.col("variable") == variable))
    if esp.is_empty():
        raise PapError(f"{tabla}: la variable de edad {variable} no está en el índice")
    codigos = [float(c["codigo"]) for c in json.loads(esp["codigos_especiales"][0] or "[]") if re.fullmatch(r"-?\d+(\.\d+)?", str(c.get("codigo", "")))]
    cond = f'AND "{variable}" NOT IN ({", ".join(repr(c) for c in codigos)})' if codigos else ""
    r = duckdb.connect().execute(f"SELECT min(\"{variable}\"), max(\"{variable}\"), count(\"{variable}\") FROM read_parquet('{str(ruta)}') "
                                 f'WHERE "{variable}" IS NOT NULL {cond}').fetchone()
    return None if r[2] == 0 else (r[0], r[1], r[2])


def _revisar_edades(f: Fuentes) -> tuple[list[Problema], list[str]]:
    probs, info = [], []
    for t, d in sorted(_tablas_en_anio(f).items()):
        p = d.get("poblacion") or {}
        if not p.get("variable_edad"):
            continue
        obs = _edad_observada(f, t, p["variable_edad"])
        if obs is None:
            probs.append(Problema(6, t, f"la variable de edad {p['variable_edad']} no tiene valores"))
            continue
        lo, hi, n = obs
        info.append(f"{t}: edad observada {lo:g}–{hi:g} {p.get('edad_unidad')} ({p['variable_edad']}, {n:,} valores); declarada {p.get('edad_min')}–{p.get('edad_max')}")
        if p.get("edad_min") is not None and lo < p["edad_min"]:
            probs.append(Problema(6, t, f"se observa edad {lo:g} y la ficha declara mínimo {p['edad_min']} (diferencia {p['edad_min'] - lo:g})"))
        if p.get("edad_max") is not None and hi > p["edad_max"]:
            probs.append(Problema(6, t, f"se observa edad {hi:g} y la ficha declara máximo {p['edad_max']} (diferencia {hi - p['edad_max']:g})"))
    return probs, info


def _miembros_zip_real(rutas: Rutas, fuente: str, recurso: str) -> tuple[bool, list[str] | None]:
    """(¿está registrado el recurso?, miembros si es un ZIP). Lee el almacén de crudos."""
    from .almacen import _insumo
    from ..zip_seguro import abrir_zip_seguro

    try:
        ins = _insumo(rutas, fuente, recurso)
    except PapError:
        return False, None
    if not str(ins.original_filename).lower().endswith(".zip"):
        return True, None
    with abrir_zip_seguro(ins.ruta) as z:
        return True, z.miembros()


def revisar_documentos(f: Fuentes, buscar: Callable[[str], tuple[bool, list[str] | None]]) -> list[Problema]:
    """Regla 7: cada documento citado existe como recurso registrado y, si nombra un miembro, ese miembro está en el ZIP."""
    probs = []
    for t, d in sorted(_tablas_en_anio(f).items()):
        for doc in d.get("documentos") or []:
            rec = doc.get("recurso")
            if not rec:
                probs.append(Problema(7, t, f"documento sin `recurso`: {doc}"))
                continue
            existe, miembros = buscar(rec)
            if not existe:
                probs.append(Problema(7, t, f"el recurso {rec} no está registrado"))
                continue
            mi = doc.get("miembro")
            if mi:
                if miembros is None:
                    probs.append(Problema(7, t, f"{rec} no es un ZIP y la ficha nombra el miembro {mi!r}"))
                elif not any(m == mi or m.rsplit("/", 1)[-1] == mi for m in miembros):
                    probs.append(Problema(7, t, f"el miembro {mi!r} no está en el ZIP de {rec}"))
    return probs


def _hash_archivos(carpeta: Path) -> dict[str, bytes]:
    return {n: (carpeta / n).read_bytes() for n in ("fichas_tabla.parquet", "bloques.parquet", "variables.parquet")}


def revisar_reproducible(raiz: Path, encuesta: str, anio: int) -> list[Problema]:
    """Regla 8: dos corridas dan los mismos archivos, y lo que está escrito en `biblioteca/variables/` es lo que da una corrida hoy."""
    probs = []
    with tempfile.TemporaryDirectory(prefix="pap-fichas-") as d:
        a, b = Path(d) / "a", Path(d) / "b"
        generar(raiz, encuesta, anio, a)
        generar(raiz, encuesta, anio, b)
        ha, hb = _hash_archivos(a), _hash_archivos(b)
        for n in ha:
            if ha[n] != hb[n]:
                probs.append(Problema(8, n, "dos corridas seguidas dan archivos distintos"))
        ind = Path(raiz) / "biblioteca" / "variables"
        for n in ("fichas_tabla.parquet", "bloques.parquet", "variables.parquet"):
            if not (ind / n).exists():
                probs.append(Problema(8, n, "no está generado: corre `pap fichas generar`"))
            elif (ind / n).read_bytes() != ha[n]:
                probs.append(Problema(8, n, "no es lo que da una corrida hoy: corre `pap fichas generar`"))
    return probs


def validar(raiz: Path, encuesta: str, anio: int, *, con_microdatos: bool = True,
            buscar_recurso: Callable[[str], tuple[bool, list[str] | None]] | None = None) -> tuple[list[Problema], dict]:
    """Las 8 reglas de fichas.md §9. Devuelve (problemas, informe) con la cobertura, las edades observadas y lo que no se comprobó."""
    raiz = Path(raiz)
    f = cargar(raiz, encuesta, anio)
    probs: list[Problema] = []
    fichas, bl, v, cob, _ = armar(f, probs)
    probs += revisar_estructura(f, bl, cob)
    no_comprobado = []
    info_edad: list[str] = []
    if con_microdatos:
        pe, info_edad = _revisar_edades(f)
        probs += pe
    else:
        no_comprobado.append("regla 6: la edad observada no se comparó con los datos (--sin-microdatos)")
    buscar = buscar_recurso or (lambda rec: _miembros_zip_real(Rutas(raiz), f.descargas["fuente"], rec))
    probs += revisar_documentos(f, buscar)
    if not [p for p in probs if p.regla in (1, 2, 3, 4, 5)]:
        probs += revisar_reproducible(raiz, encuesta, anio)
    else:
        no_comprobado.append("regla 8: no se probó la reproducibilidad porque la estructura tiene problemas")
    return probs, {"cobertura": cob, "fichas": fichas.height, "bloques": bl.height, "edades": info_edad, "no_comprobado": no_comprobado}


# ------------------------------------------------------------------ ver

def ver(raiz: Path, encuesta: str, anio: int, tabla: str) -> str:
    """La ficha de una tabla en texto para personas (fichas.md §3), armada desde las tablas curadas y el índice (no desde el Parquet)."""
    f = cargar(raiz, encuesta, anio)
    probs: list[Problema] = []
    fichas, bl, _, cob, _ = armar(f, probs)
    fila = next((r for r in fichas.iter_rows(named=True) if r["tabla"].lower() == tabla.lower()), None)
    if fila is None:
        raise PapError(f"No hay ficha de {tabla} en {encuesta} {anio}. Tablas: {', '.join(sorted(fichas['tabla'].to_list()))}")
    t = fila["tabla"]
    L = [f"{fila['encuesta']} {fila['anio']} · {t} · {fila['nombre_corto']}", "=" * 72, fila["descripcion"], ""]
    L.append("Qué es")
    L.append(f"  Tipo de fuente: {fila['tipo_fuente']} · Tipo de tabla: {fila['tipo_tabla']} · Estado de la ficha: {fila['estado']}")
    L.append(f"  Cuestionario: {fila['cuestionario'] or '—'} · Secciones: {'; '.join(fila['secciones']) or '—'}")
    L.append(f"  Quién tiene fila: {fila['quien_tiene_fila']}")
    L.append(f"  Informante: {fila['informante'] or '—'} · Modo: {fila['modo'] or '—'}")
    L += ["", "A quién describe"]
    L.append(f"  {fila['poblacion_texto'] or '—'}")
    edad = (f"{fila['poblacion_edad_min']}–{fila['poblacion_edad_max']} {fila['poblacion_edad_unidad']}"
            if fila["poblacion_edad_min"] is not None or fila["poblacion_edad_max"] is not None else "—")
    L.append(f"  Sujeto: {fila['poblacion_sujeto'] or '—'} · Edad: {edad} · Sexo: {fila['poblacion_sexo'] or '—'} · Condición: {fila['poblacion_condicion'] or '—'}")
    L += ["", "Dónde está"]
    L.append(f"  Módulo {fila['modulo_codigo']} «{fila['modulo_nombre']}» (encuesta {fila['codigo_encuesta']}, periodo {fila['periodo']}) · recurso {fila['recurso']} · {fila['formato']}")
    L.append(f"  {fila['n_filas']:,} filas · {fila['n_variables']} variables · huella {fila['huella_datos'][:16]}…")
    L.append(f"  Unidad: {fila['unidad']} · Llave: {', '.join(fila['llave'])} · Tabla de la que cuelga: {fila['tabla_base'] or '—'}")
    ups = json.loads(fila["uniones"] or "[]")
    for u in ups:
        L.append(f"  Unión → {u['con']} por {', '.join(f'{a} = {b}' for a, b in u['por'])} ({u['cardinalidad']})")
    L += ["", "Si se puede estimar"]
    if fila["tiene_diseno"]:
        L.append(f"  Diseño declarado: peso {fila['peso']} · estrato {fila['estrato']} · UPM {fila['upm']} · submuestra {fila['nivel_submuestra']}")
        L.append(f"  Permite totales: {fila['permite_totales']} · Alcance: {fila['alcance_territorial'] or '—'}")
    else:
        L.append("  Todavía no: la tabla no tiene diseño muestral declarado (el verificador rechaza los planes sobre ella).")
    L += ["", "Variables"]
    L.append(f"  Por clase: {', '.join(f'{k} {n}' for k, n in json.loads(fila['variables_por_clase']).items())}")
    bats = json.loads(fila["baterias"])
    L.append(f"  Baterías: {len(bats)}" + (" (" + ", ".join(f"{b['prefijo']} {b['n']}" for b in bats[:12]) + ("…" if len(bats) > 12 else "") + ")" if bats else ""))
    L.append(f"  Estado de las variables: {fila['n_propuesto']} propuesto, {fila['n_revisado']} revisado")
    c = cob.get(t)
    if c:
        L.append(f"  Cobertura de bloques: {c['con_bloque']} de {c['variables']} categoria o medida ({c['porcentaje']:.1f} %) en {c['bloques']} bloque(s)")
    L += ["", "De qué trata"]
    L.append(f"  Temas (el principal primero): {', '.join(fila['temas']) or '—'}")
    mis = [r for r in bl.iter_rows(named=True) if r["tabla"] == t]
    for b in mis:
        extra = f" · ventana: {b['ventana_referencia']}" if b["ventana_referencia"] else ""
        L.append(f"  • {b['bloque_id']} [{b['tema']}/{b['subtema']}, {b['papel']}, {b['n_variables']} variables{extra}]")
        L.append(f"      {b['nombre']}: {b['descripcion']}")
    if not mis:
        L.append("  (esta tabla todavía no tiene bloques)")
    L += ["", "Avisos"] + ([f"  • {a}" for a in fila["avisos"]] or ["  ninguno conocido"])
    L += ["", "Documentos"]
    for d in json.loads(fila["documentos"]):
        L.append("  • " + ", ".join(f"{k}: {v}" for k, v in d.items()))
    L += ["", "Recetas: " + (", ".join(fila["recetas"]) or "ninguna") + " · Conceptos: " + (", ".join(fila["conceptos"]) or "ninguno")]
    return "\n".join(L) + "\n"
