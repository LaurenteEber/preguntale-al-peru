"""Contrato de respuesta (12/10/2026, decisión del dueño tras la revisión de usuario): la respuesta se entrega por capas.

Capa 1, siempre visible (R-04: objetivo 100 palabras, máximo 125; `respuesta.capa1_palabras_*` en parametros_motor.yaml): respuesta corta, cifra clave, «Ojo al leer» y confianza en los datos.
Capa 2, «Más contexto»: cifras secundarias en tarjetas con su etiqueta «no se compara», avisos de las reglas y límites.
Capa 3, «Para citar y verificar»: una línea de cita por cifra, glosario y «¿Qué puedo hacer?» (texto fijo oficial).
El detalle técnico (tabla, ficha larga, reglas, reproducibilidad) queda aparte.

Especificación: docs/especificaciones/contrato_respuesta.md. Nada aquí calcula cifras ni decide reglas: solo ordena y
redacta lo que ya validaron el validador y las plantillas.

Intervalo visible (X-04, `pendientes_dueno.intervalo_visible`): `ambos` = capa 1 con el intervalo propio y cita con el del INEI
si existe; `uno` = capa 1 (`plantillas.valor_cifra`) y cita con el del INEI si existe, si no el propio. La cita ya usa el del
INEI cuando existe en los dos modos; la ficha larga muestra siempre los dos.
"""
from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

import yaml

from . import formato as fmt
from . import plantillas

NIVEL_CONFIANZA = {"verde": "alta", "ambar": "media", "rojo": "baja"}
SIGLA = {"INEI-ENDES": ("ENDES", "INEI"), "INEI-ENAHO": ("ENAHO", "INEI"), "INS-CENAN-SIEN": ("SIEN", "INS"),
         "MEF-DA-PRESUPUESTO-EJECUCION-GASTO": ("gasto registrado en el MEF", "MEF"),
         "INEI-MAPA-POBREZA": ("Mapa de Pobreza", "INEI")}


def _textos(raiz: Path, nombre: str) -> dict:
    ruta = raiz / "curados" / "motor" / "textos" / nombre
    return yaml.safe_load(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def _parte(t: str, b: dict, cifras: dict) -> str:
    return plantillas.rellenar({**b, "texto": t}, cifras) if t else ""


def palabras(*textos: str) -> int:
    return sum(len(re.findall(r"[\wÁÉÍÓÚÑáéíóúñü%]+", t or "")) for t in textos)


def _coincide(c, o: dict | None) -> bool:
    """La cifra oficial es la misma que la nuestra: el valor redondeado a 1 decimal coincide (S1-09, A-H3). Si el documento solo
    publica un rango (sin valor), no hay valor que comparar y se atribuye al documento."""
    return bool(o) and (o.get("valor") is None or round(float(c.valor), 1) == round(float(o["valor"]), 1))


def _fuente(c) -> str:
    sig, ent = SIGLA.get(c.fuente_principal, (c.fuente_principal, ""))
    t = f"{sig} {c.anio} ({ent})" if ent and ent not in sig else f"{sig} {c.anio}"
    o = c.get("contraste_oficial")
    if o and o.get("valor") is not None and _coincide(c, o):
        t += f"; el {o.get('entidad', 'INEI')} publica la misma cifra ({fmt.pct(o['valor'])})"
    elif o and c.medida == "intervalo":
        t += f"; rango publicado por el {o.get('entidad', 'INEI')}"
    return t


def _valor_cita(c) -> str:
    if c.medida == "intervalo":
        return f"{fmt.intervalo(c.ic_inf, c.ic_sup, 1)} (rango probable)"
    if c.medida == "cobertura":
        return f"{fmt.intervalo(c.cota_inf, c.cota_sup, 1)}"
    if c.medida in fmt.MEDIDAS_MONTO:
        return fmt.monto(c.valor)
    ii = c.get("ic_inei")
    lo, hi, quien = (ii["ic_inf"], ii["ic_sup"], "intervalo del INEI") if ii else (c.ic_inf, c.ic_sup, "intervalo")
    base = fmt.pct(c.valor, 1)
    return f"{base} ({quien}: {fmt.pct(lo, 1)} a {fmt.pct(hi, 1)})" if lo is not None else base


def _cita(c, alcance: str | None = None, nombre: str | None = None, tx: dict | None = None) -> str:
    o = c.get("contraste_oficial")
    publicado = ""
    if o and _coincide(c, o):
        src = f"{o['documento']}, {o['cuadro_pagina']}"
    else:
        if o and tx:                                  # S1-09 (A-H3): el documento oficial publica otro valor; no se le atribuye el nuestro
            publicado = tx["publicado_oficial"].format(entidad=o.get("entidad", "INEI"), valor=fmt.pct(o["valor"]))
        sig, ent = SIGLA.get(c.fuente_principal, (c.fuente_principal, ""))
        src = f"Pregúntale al Perú, cálculo propio con {sig} {c.anio}" + (f" ({ent})" if ent and ent not in sig else "")
        if c.get("fecha_descarga"):
            src += f", datos descargados el {c.fecha_descarga}"
    nom = c.nombre_ciudadano[0].lower() + c.nombre_ciudadano[1:] if c.nombre_ciudadano else c.indicador_id
    al = f" ({alcance})" if alcance else ""
    valor = _valor_cita(c)
    if c.get("precios") == "constantes" and tx:            # S1-12: se cita el monto nominal del año y el factor del IPC
        factor = (c.get("factores_deflactor") or {}).get(int(c.anio))
        valor = tx["cita_constantes"].format(valor=valor, anio_base=c.anio_base_deflactor, anio=c.anio,
                                             nominal=fmt.monto(c.devengado), factor=fmt._num(factor, 7))
    return f"{valor}: {nom}{al}, {nombre or c.territorio_nombre}, {c.anio}. Fuente: {src}{publicado}."


@lru_cache(maxsize=None)
def _catalogo_urls(raiz: str) -> dict:
    """{id de fuente: enlace oficial} del catálogo de fuentes (`url_portal`, si no `url_datos`). Vacío si no hay."""
    ruta = Path(raiz) / "catalogo" / "catalogo_fuentes.csv"
    if not ruta.exists():
        return {}
    with open(ruta, encoding="utf-8", newline="") as f:
        return {r["id"]: (r.get("url_portal") or r.get("url_datos") or "").strip() for r in csv.DictReader(f)}


def _url(motor, c) -> str:
    """S3-01 (plan_slices.md, slice 3; P-02): enlace al documento oficial de la cita. Con cifra dorada, la `url` de
    cifras_doradas.csv; si no, el portal de la fuente en el catálogo. Sin enlace oficial, vacío: nunca se inventa uno."""
    o = c.get("contraste_oficial")
    if o:
        d = next((d for d in motor.ctx.doradas if d["id_cifra"] == o.get("id_cifra")), None)
        if d and (d.get("url") or "").strip():
            return d["url"].strip()
    return _catalogo_urls(str(motor.ctx.raiz)).get(c.fuente_principal, "")


def _sin_parentesis(t: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", t).strip()


def _aviso_ciudadano(regla: str, texto: str, detalle: dict | None = None) -> str:
    """Los avisos de las reglas se muestran como lo que el lector NO debe concluir (revisión de usuario, 12/10/2026).
    Las reglas no cambian: solo cambia cómo se dice al lector."""
    m = re.match(r"Este párrafo combina datos de distinto tipo: (.+?)\. Se presentan juntos", texto)
    if regla == "R-LENGUAJE-06" and m:
        return (f"Estas cifras vienen de fuentes de distinto tipo ({m.group(1)}): se muestran juntas para dar contexto "
                "y cada una mide algo distinto.")
    pob = next((x for x in (detalle or {}).get("motivos") or [] if isinstance(x, dict) and "poblacion" in x), None)
    if regla == "R-CRUCES-05" and pob:
        return (f"Las cifras del cruce no cubren exactamente al mismo grupo: una se refiere a {_sin_parentesis(pob['a'])}; "
                f"la otra, a {_sin_parentesis(pob['b'])}.")
    return texto


def _ajustar_capa1(raiz: Path, ojo: list[str], visible: list[str]) -> tuple[list[str], list[str]]:
    """Capa 1 por encima del máximo (R-04, `respuesta.capa1_palabras_max`): los últimos «Ojo al leer» pasan a «Avisos» de la
    capa 2 —no se pierde ninguno— hasta caber, sin bajar de `respuesta.ojo_al_leer.min`. Los textos y las cifras no cambian
    (S1-08, `respuesta.capa1_exceso`). Devuelve (ojo que se quedan en la capa 1, ojo que pasan a la capa 2)."""
    par = plantillas.parametros(raiz)["respuesta"]
    if par["capa1_exceso"]["valor"] != "pasar_ojo_a_capa2":
        return ojo, []
    tope, minimo = par["capa1_palabras_max"]["valor"], par["ojo_al_leer"]["min"]
    ojo, pasan, resto = list(ojo), [], list(visible)
    while len(ojo) > minimo and palabras(*resto) > tope:
        quitado = ojo.pop()
        resto.remove(quitado)
        pasan.insert(0, quitado)
    return ojo, pasan


def construir(motor, consulta: dict, borrador: dict, cifras: dict, ficha: dict, sem: str | None, avisos: list[dict]) -> dict:
    raiz = motor.ctx.raiz
    b = borrador
    corta = _parte(" ".join(b.get("corta") or []), b, cifras)
    cl = b.get("clave") or {}
    clave_ids = [i for i in cl.get("ids") or [] if i in cifras]
    clave = None
    if clave_ids:
        fuentes = list(dict.fromkeys(_fuente(cifras[i]) for i in clave_ids))
        clave = {"ids": clave_ids, "valor": _parte(cl.get("valor", ""), b, cifras),
                 "texto": _parte(cl.get("texto", ""), b, cifras), "fuente": " · ".join(fuentes)}
    ojo = [_parte(t, b, cifras) for t in b.get("ojo") or []]
    lineas = ficha["corta"].splitlines()
    nivel = NIVEL_CONFIANZA.get(sem, "sin cifra")
    m = re.match(r"Confianza en los datos: \w+ \([^)]*\): (.+)$", lineas[0]) if lineas else None
    motivo = (m.group(1)[0].upper() + m.group(1)[1:]) if m else ""
    motivo = b.get("motivo_confianza") or motivo
    confianza = {"nivel": nivel, "texto": f"Confianza en los datos: {nivel}." + (f" {motivo}" if motivo else ""),
                 "ficha": lineas[0] if lineas else ""}
    contexto = [{"titulo": t["titulo"], "texto": _parte(t["texto"], b, cifras), "etiqueta": t.get("etiqueta")}
                for t in b.get("contexto") or []]
    av = list(dict.fromkeys(_aviso_ciudadano(a["regla"], a["texto"], a.get("detalle")) for a in avisos))
    visible = [corta, clave["valor"] if clave else "", clave["texto"] if clave else "", *ojo, confianza["texto"]]
    ojo, pasan = _ajustar_capa1(raiz, ojo, visible)
    av = list(dict.fromkeys(pasan + av))
    usados = list(dict.fromkeys(clave_ids + [i for i in b.get("cifras_usadas") or [] if i in cifras]))
    tx = _textos(raiz, "capas.yaml")
    largos = consulta.get("desambiguados") or {}          # S1-09 (H4): el homónimo aclarado se cita con provincia y departamento
    citar = [_cita(cifras[i], (b.get("alcance") or {}).get(i), largos.get(f"{cifras[i].nivel}:{cifras[i].territorio_id}"), tx) for i in usados]
    citas = [{"texto": t, "url": _url(motor, cifras[i]), "id_cifra": i} for t, i in zip(citar, usados)]    # S3-01: cada cita con su enlace
    glos = (_textos(raiz, "glosario.yaml").get("terminos") or {})
    glosario = [glos[k] for k in b.get("glosario") or [] if k in glos]
    qh = None
    tema = b.get("tema")
    if tema:
        t = (_textos(raiz, "que_hacer.yaml").get("temas") or {}).get(tema)
        if t:
            qh = {"texto": " ".join(str(t["texto"]).split()), "fuente": t["fuente"], "url": t["url"],
                  "revisado_dueno": bool(t.get("revisado_dueno"))}
    visible = [corta, clave["valor"] if clave else "", clave["texto"] if clave else "", *ojo, confianza["texto"]]
    return {"capa1": {"respuesta_corta": corta, "cifra_clave": clave, "ojo_al_leer": ojo, "confianza": confianza,
                      "que_hacer": qh, "palabras": palabras(*visible)},
            "capa2": {"mas_contexto": contexto, "avisos": av,
                      "limites": [x.replace("se tamizaron", "se les midió la hemoglobina") for x in lineas[1:]]},
            "capa3": {"para_citar": citar, "citas": citas, "glosario": glosario}}
