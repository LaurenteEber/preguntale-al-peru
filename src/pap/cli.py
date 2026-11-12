"""CLI `pap`: revisar | descargar | registrar | verificar | citar | indice | recetas | construir | calcular | foto-pim | almacen | microdatos | variables | servir."""
from __future__ import annotations

import json

import argparse
import sys
from datetime import date
from pathlib import Path

from . import __version__, almacen, bitacora, capturas, citar, indice, recetas
from .config import rutas as obtener_rutas
from .descargar import descargar
from .errores import NoImplementado, PapError
from .registrar import Opciones, Resultado, registrar
from .verificar import verificar


def _tabla(filas: list[list[str]], cabecera: list[str]) -> str:
    anchos = [max(len(str(x)) for x in col) for col in zip(cabecera, *filas)]
    linea = lambda f: "  ".join(str(x).ljust(a) for x, a in zip(f, anchos))  # noqa: E731
    return "\n".join([linea(cabecera), linea(["-" * a for a in anchos])] + [linea(f) for f in filas])


def _mostrar_resultado(r: Resultado, rutas) -> None:
    for rec in r.nuevos:
        print(f"✔ {rec['change']}: {rec['original_filename']} → {rec['hash'][:19]}…  ({rec['bytes']:,} bytes)")
    for h in r.sin_cambio:
        print(f"= sin cambio: {h[:19]}… ya estaba registrado; no se creó nada nuevo")
    for a in r.avisos:
        print(f"⚠ {a}")
    if r.captura:
        print(f"Captura: {rutas.relativa(r.captura)}")


def cmd_revisar(a, rutas) -> int:
    ultimos: dict[str, str] = {}
    for v in bitacora.leer(rutas):
        if v.get("source_id"):
            ultimos[v["source_id"]] = max(ultimos.get(v["source_id"], ""), v["fecha"])
    filas, malas = [], 0
    for ruta in recetas.listar(rutas):
        if a.source_id and ruta.stem != a.source_id:
            continue
        r = recetas.leer(ruta)
        errs = recetas.errores(r, ruta)
        malas += bool(errs)
        recs = capturas.recursos(rutas, ruta.stem)
        ult = ultimos.get(ruta.stem)
        dias = (date.today() - date.fromisoformat(ult[:10])).days if ult else None
        cat = r.get("catalogo") or {}
        filas.append([
            ruta.stem, r.get("strategy", "?"), "DESACTIVADA" if r.get("desactivada") else cat.get("compuerta_ingesta", "—"),
            "sí" if cat.get("bloquea_mvp") else "", str(len(recs)),
            recs[-1][1]["retrieved_at"][:10] if recs else "—",
            "—" if dias is None else str(dias), "INVÁLIDA" if errs else "ok",
        ])
    print(_tabla(filas, ["fuente", "estrategia", "compuerta", "MVP", "capturas", "última", "días sin revisar", "receta"]))
    if a.source_id and filas:
        r = recetas.cargar(rutas, a.source_id, permitir_desactivada=True)
        if r.get("desactivada"):
            print("⛔ " + recetas.mensaje_desactivada(r))
            return 1 if malas else 0
        for p in r.get("pendientes") or []:
            print(f"• pendiente: {p}")
        if r["strategy"] == "manual":
            print("Pasos:\n" + "\n".join(f"  {i}. {p}" for i, p in enumerate(r["manual"]["pasos"], 1)))
    return 1 if malas else 0


def _opciones(a) -> Opciones:
    return Opciones(issued=a.issued, version=a.edicion, corte=a.corte, corte_base=a.corte_base,
                    consultado=a.consultado, atribuido=a.atribuido,
                    evidencias=[Path(e) for e in (a.evidencia or [])], notas=a.nota or [], forzar=a.forzar,
                    url_descarga=getattr(a, "url_descarga", None), mover=getattr(a, "mover", False),
                    recurso=getattr(a, "recurso", None))


def cmd_registrar(a, rutas) -> int:
    r = registrar(rutas, a.source_id, [Path(x) for x in a.archivos] or None, _opciones(a))
    _mostrar_resultado(r, rutas)
    if r.nuevos and not a.archivos:
        print("Los archivos de la bandeja ya están en el almacén; puedes borrarlos de la bandeja cuando quieras.")
    return 0


def cmd_descargar(a, rutas) -> int:
    params = dict(p.split("=", 1) for p in (a.param or []))
    r = descargar(rutas, a.source_id, url=a.url, parametros=params, op=_opciones(a))
    if isinstance(r, str):
        print(f"{a.source_id} se obtiene a mano:\n{r}")
        return 0
    _mostrar_resultado(r, rutas)
    return 0


def cmd_verificar(a, rutas) -> int:
    inf = verificar(rutas, a.source_id, completo=not a.rapido)
    print(f"Recetas: {inf.recetas} · capturas: {inf.paquetes} · archivos: {inf.recursos}")
    for p in inf.problemas:
        print(f"✘ {p}")
    for w in inf.avisos:
        print(f"⚠ {w}")
    print("Todo en orden." if inf.ok else f"{len(inf.problemas)} problema(s).")
    if inf.recursos:
        indice.reconstruir(rutas)
    return 0 if inf.ok else 1


def _gb(n: int | None) -> str:
    return "—" if n is None else f"{n / 1e9:,.3f} GB"


def cmd_almacen(a, rutas) -> int:
    """pap almacen comprimir | restaurar | liberar."""
    if a.accion in ("restaurar", "liberar"):
        from . import bloques

        if not a.bloque:
            raise PapError(f"pap almacen {a.accion} necesita --bloque <encuesta>-<anio> (p. ej. endes-2024)")
        if a.accion == "restaurar":
            bloques.restaurar(rutas, a.bloque, repo_pedido=a.repo)
        else:
            bloques.liberar(rutas, a.bloque, ejecutar=a.ejecutar,
                            confirmar=(lambda: True) if a.si else (lambda: bloques.confirmar_por_terminal(a.bloque)))
        return 0
    return _comprimir(a, rutas)


def _comprimir(a, rutas) -> int:
    """pap almacen comprimir: CSV/TXT grandes del almacén → <huella>.zst verificado, uno por uno (reanudable)."""
    import time

    lista = almacen.candidatos(rutas, int(a.min_mb * 1_000_000))
    if a.solo:
        lista = [c for c in lista if any(c[0].startswith(p.removeprefix("sha256:").lower()) for p in a.solo)]
    for t in almacen.temporales(rutas):
        print(f"⚠ temporal de un corte anterior: {rutas.relativa(t)} (se rehace al procesar su objeto)")
    if not lista:
        print(f"No hay objetos de texto de más de {a.min_mb:g} MB.")
        return 0
    filas, errores, antes, despues = [], 0, 0, 0
    inicio = time.monotonic()
    for h, tam, fmt, nombre in lista:
        if a.max_segundos and not a.dry_run and time.monotonic() - inicio > a.max_segundos:
            print(f"⏸ tiempo agotado (--max-segundos {a.max_segundos}); vuelve a correr el comando para seguir")
            break
        paso = almacen.comprimir_objeto(rutas, h, tam, ensayo=a.dry_run, nivel=a.nivel, nombre=nombre)
        if paso.accion == "error":
            errores += 1
        if not a.dry_run and paso.accion != "ya_comprimido":  # registro trazable de cada cambio (H5)
            enc = capturas.buscar_por_huella(rutas, h)
            info = almacen.leer_registro(rutas).get(h) or {}
            bitacora.anotar(rutas, enc[1].get("source_id") if enc else None, "comprimir",
                            "error" if paso.accion == "error" else "ok", hash=f"sha256:{h}",
                            captura=rutas.relativa(enc[0].parent) if enc else None,
                            detalle=f"{paso.accion}: {nombre}; {tam} → {paso.bytes_zst} bytes"
                                    + (f"; sha256_zst {info['sha256_zst'][:12]}…" if info.get("sha256_zst") else "")
                                    + (f"; {paso.detalle}" if paso.detalle else "")
                                    + ("; ida y vuelta verificada, original retirado" if paso.accion == "comprimido" else ""))
        actual = paso.bytes_zst if paso.bytes_zst is not None and paso.accion != "error" else tam
        antes += tam
        despues += actual
        filas.append([h[:12], nombre[:40], fmt, _gb(tam), _gb(paso.bytes_zst), paso.accion,
                      f"{paso.segundos:.0f} s" if paso.segundos else "", paso.detalle[:70]])
        print(f"{'✘' if paso.accion == 'error' else '✔'} {h[:12]} {nombre}: {paso.accion}"
              + (f" ({_gb(tam)} → {_gb(paso.bytes_zst)}, {paso.segundos:.0f} s)" if paso.accion == "comprimido" else "")
              + (f" — {paso.detalle}" if paso.detalle else ""), flush=True)
    print()
    print(_tabla(filas, ["huella", "archivo", "fmt", "original", ".zst", "acción", "tiempo", "detalle"]))
    if a.dry_run:
        print(f"\nEnsayo: {len([f for f in filas if f[5] == 'ensayo'])} objeto(s) por comprimir, "
              f"{_gb(sum(c[1] for c, f in zip(lista, filas) if f[5] == 'ensayo'))} hoy sin comprimir. No se cambió nada.")
    if errores:
        print(f"✘ {errores} objeto(s) con error: sus originales quedaron intactos.")
    return 1 if errores else 0


def cmd_microdatos(a, rutas) -> int:
    """pap microdatos convertir: ZIP registrados de una encuesta y año → Parquet + manifiesto (M0-04)."""
    from .inferencia import almacen as microdatos     # importación diferida: trae polars, duckdb y pyreadstat

    m = microdatos.convertir(rutas, a.encuesta, a.anio)
    n = len(m["archivos"])
    print(f"\n{n} archivo(s) de {a.encuesta} {a.anio} en {rutas.relativa(microdatos.carpeta_salida(rutas, a.encuesta, a.anio))}"
          f" (manifiesto.json); huellas de los ZIP agregadas a curados/insumos.lock.yaml.")
    return 0


def cmd_variables(a, rutas) -> int:
    """pap variables indexar: ZIP registrados de una encuesta y año → biblioteca/variables/*.parquet (M0-05)."""
    from .inferencia import indice as indice_variables     # importación diferida: trae polars, duckdb y pyreadstat

    ind, rutas_salida = indice_variables.indexar(rutas, a.encuesta, a.anio)
    c = indice_variables.conteos(ind)
    print(f"\n{c['filas']['archivos']} archivo(s), {c['filas']['variables']:,} variable(s) y {c['filas']['categorias']:,} categoría(s) "
          f"de {a.encuesta} {a.anio} en {rutas.relativa(indice_variables.carpeta_indice(rutas))} "
          f"({', '.join(p.name for p in rutas_salida.values())}); todas en estado propuesto.")
    print(f"{c['especiales_propuestos']} código(s) especial(es) propuesto(s); {c['textos_distintos']:,} textos de etiqueta distintos; "
          "controles que saltaron: " + (", ".join(f"{k} {n}" for k, n in c["controles"].items() if n) or "ninguno") + ".")
    return 0


def cmd_inferencia(a, rutas) -> int:
    """pap inferencia validar-tablas | validar-recetas | receta <id> --anio AAAA [--comparar-cubo] (M0-06, M0-10)."""
    if a.accion == "validar-recetas":
        return _inferencia_validar_recetas(rutas)
    if a.accion == "receta":
        return _inferencia_receta(a, rutas)
    from .inferencia import tablas_curadas

    res = tablas_curadas.validar(rutas, exigir_indice=True)
    for nombre, (filas, errores) in res.items():
        print(("✘ " if errores else "✔ ") + f"{tablas_curadas.ARCHIVOS_TABLAS[nombre]}: {filas} fila(s)"
              + ("" if errores else ", todas con cita") + "".join(f"\n    - {e}" for e in errores))
    return 1 if any(e for _, e in res.values()) else 0


def _inferencia_validar_recetas(rutas) -> int:
    """pap inferencia validar-recetas: las recetas de curados/inferencia/recetas/ contra su esquema, las tablas curadas, las doradas y dim_indicador."""
    from .inferencia import recetas

    res = recetas.validar(rutas, exigir_indice=True)
    for id_, (ok, errores) in res.items():
        r = recetas.leer_receta(rutas.raiz, id_) if ok and not errores else None
        print(("✘ " if errores or not ok else "✔ ") + f"{id_}" + (f": estado {r.estado}{f', pendiente {r.pendiente}' if r.pendiente else ''}, {len(r.doradas)} dorada(s)" if r else "")
              + "".join(f"\n    - {e}" for e in errores))
    return 1 if any(e or not ok for ok, e in res.values()) else 0


def _inferencia_receta(a, rutas) -> int:
    """pap inferencia receta <id> --anio AAAA [--comparar-cubo]: plan → verificador → ejecutor → compuertas para todos los territorios del año."""
    from .inferencia import recetas
    from .inferencia.ejecutor import Ejecutor, PoolEjecutor

    if not a.id or a.anio is None:
        raise PapError("Uso: pap inferencia receta <id> --anio AAAA [--comparar-cubo]")
    receta = recetas.leer_receta(rutas.raiz, a.id)
    with PoolEjecutor(raiz=rutas.raiz) as pool:
        estimaciones = recetas.calcular(receta, a.anio, rutas.raiz, ejecutor=Ejecutor(pool, raiz=rutas.raiz))
    doradas = recetas.reproducir_doradas(receta, estimaciones)
    filas = recetas.compuertas_de(receta, estimaciones, doradas, rutas.raiz)
    print(f"Receta {receta.id} ({receta.estado}, pendiente {receta.pendiente}) · {receta.encuesta} {a.anio} · {len(estimaciones)} territorio(s)")
    if not a.comparar_cubo:
        for f in filas:
            e = f.estimacion
            print(f"  {f.nivel:<20} {f.territorio_id:<20} {100 * e.valor:6.2f} % (IC {100 * e.ic_inf:.2f}–{100 * e.ic_sup:.2f})  n={e.n}  {f.compuerta.estado}")
        _imprimir_doradas(doradas)
        return 1 if any(not d["pasa"] for d in doradas) else 0

    p = recetas.ParametrosRecetas.desde_yaml()
    cubo = recetas.leer_csv(rutas.raiz / recetas.FILAS_CUBO_2024, ("indicador_id", "nivel", "territorio_id"))
    estados = recetas.leer_csv(rutas.raiz / recetas.ESTADOS_CUBO_2024, ("indicador_id", "nivel", "territorio_id"))
    if a.anio != 2024:
        raise PapError("--comparar-cubo solo tiene las filas de 2024 (backlog/slice-m0/evidencia/m0-00_filas_cubo_2024.csv).")
    maximos, fallan, sin_fila = dict.fromkeys(recetas.COLUMNAS, 0.0), [], []
    for f in filas:
        llave = (receta.indicador_id, f.nivel, f.territorio_id)
        if llave not in cubo:
            sin_fila.append(llave)
            continue
        for d in recetas.comparar_fila(f.estimacion, cubo[llave], p):
            if d.dif is not None:
                maximos[d.columna] = max(maximos[d.columna], abs(d.dif))
            if not d.ok:
                fallan.append(f"{'/'.join(llave)}: {d.columna} cubo {d.cubo} nuevo {d.nuevo}")
    print(f"  Contra el cubo ({len(filas) - len(sin_fila)} de {len(cubo and [k for k in cubo if k[0] == receta.indicador_id])} filas), "
          f"máxima |dif| redondeada a {p.cubo_decimales} decimales:")
    print("    " + "  ".join(f"{c}={m:.2e}" for c, m in maximos.items()))
    distintos = [f"{f.nivel}/{f.territorio_id}: cubo {estados[(receta.indicador_id, f.nivel, f.territorio_id)]['estado']} · nuevo {f.compuerta.estado}"
                 for f in filas if (receta.indicador_id, f.nivel, f.territorio_id) in estados
                 and (estados[(receta.indicador_id, f.nivel, f.territorio_id)]["estado"] != f.compuerta.estado
                      or estados[(receta.indicador_id, f.nivel, f.territorio_id)]["reglas"] != recetas.firma_reglas(f.compuerta))]
    print(f"  Compuertas: {len(distintos)} fila(s) con estado o reglas distintos de m0-00_estados_cubo.csv")
    _imprimir_doradas(doradas)
    for linea in [*(f"sin fila en el cubo: {'/'.join(k)}" for k in sin_fila), *fallan, *distintos]:
        print(f"    ✘ {linea}")
    return 1 if (sin_fila or fallan or distintos or any(not d["pasa"] for d in doradas)) else 0


def _imprimir_doradas(doradas: list[dict]) -> None:
    pasan = sum(d["pasa"] for d in doradas)
    print(f"  Doradas (E-05): {pasan} de {len(doradas)} se reproducen")
    for d in doradas:
        if not d["pasa"]:
            print(f"    ✘ {d['id_cifra']}: publicado {d['publicado']} · nuestro {d['nuestro']} (dif {d['dif_pp']} pp)")


def cmd_citar(a, rutas) -> int:
    clave = a.clave
    if clave.startswith("sha256:") or all(c in "0123456789abcdef" for c in clave.lower()) and len(clave) >= 6:
        encontrados = capturas.buscar_por_prefijo(rutas, clave)
        if len(encontrados) > 1 and len({e[1]["hash"] for e in encontrados}) > 1:
            raise PapError(f"El prefijo {clave} es ambiguo; usa más caracteres.")
    else:
        u = capturas.ultimo(rutas, clave)
        encontrados = [u] if u else []
    if not encontrados:
        raise PapError(f"No hay ningún archivo registrado para «{clave}».")
    rec = encontrados[-1][1]
    print(citar.ficha_corta(rec) if a.corta else citar.cita(rec))
    return 0


def cmd_indice(a, rutas) -> int:
    print(f"Índice reconstruido: {rutas.relativa(indice.reconstruir(rutas))}")
    return 0


def cmd_recetas(a, rutas) -> int:
    if a.accion == "sincronizar":
        for p in recetas.sincronizar_catalogo(rutas):
            print(f"✔ bloque catalogo actualizado: {rutas.relativa(p)}")
        a.accion = "validar"
    if a.accion == "generar":
        escritas, omitidas = recetas.generar_desde_catalogo(rutas, a.ola, a.sobrescribir)
        for p in escritas:
            print(f"✔ {rutas.relativa(p)}")
        if omitidas:
            print(f"= {len(omitidas)} receta(s) ya existían y no se tocaron (usa --sobrescribir)")
        return 0
    malas = 0
    for ruta in recetas.listar(rutas):
        errs = recetas.errores(recetas.leer(ruta), ruta)
        malas += bool(errs)
        print(("✘ " if errs else "✔ ") + ruta.stem + "".join(f"\n    - {e}" for e in errs))
    incoh = recetas.incoherencias_catalogo(rutas)
    print(f"Coherencia con el catálogo y R-DEP-01: {'ok' if not incoh else str(len(incoh)) + ' diferencia(s)'}")
    for e in incoh:
        print(f"  ✘ {e}")
    return 1 if malas or incoh else 0


def cmd_construir(a, rutas) -> int:
    from .capa0 import gasto, poblacion, puentes, salida, territorio

    from .util import git
    if not a.permitir_sucio and git(rutas.raiz, "status", "--porcelain", "--", "src", "curados", "tests", "catalogo/scripts", ":!curados/insumos.lock.yaml"):
        print("El código tiene cambios sin commit: el manifiesto no podría citar el código que produjo las tablas "
              "(RP-03). Haz commit primero o usa --permitir-sucio (solo para pruebas).")
        return 1
    from .capa0 import encuestas, indicadores, mapa_pobreza
    from .motor import calculo
    constructor, sprint = {"territorio": (territorio.construir, "s1_territorio"),
                           "poblacion": (poblacion.construir, "s2_poblacion"),
                           "puentes": (puentes.construir, "s3_puentes"), "gasto": (gasto.construir, "s3_gasto"),
                           # S4 (9/10/2026): insumos del piloto, a biblioteca/estandarizada/
                           "endes": (encuestas.construir_endes, "s4_endes"),
                           "enaho": (encuestas.construir_enaho, "s4_enaho"),
                           "mapa_pobreza": (mapa_pobreza.construir, "s4_mapa_pobreza"),
                           # Piloto (9/10/2026): dim_indicador, cruces_permitidos y cifras_doradas
                           "indicadores": (indicadores.construir, "piloto_indicadores"),
                           # Piloto P1 (10/10/2026): cubo de indicadores (`pap calcular`)
                           "calculo": (calculo.construir, "p1_indicadores")}[a.que]
    from .capa0 import insumos as ins_mod
    ins_mod.ACTUALIZAR_LOCK = bool(a.actualizar_insumos)
    res = constructor(rutas)
    for p in res.pruebas:
        marca = "✔" if p["ok"] else ("✘" if p["bloqueante"] else "⚠")
        print(f"{marca} {p['id']} {p['descripcion']}" + ("" if p["ok"] else f"  → {p['detalle']}"))
    if not res.ok and not a.forzar:
        print("No se escriben las tablas: hay pruebas bloqueantes fallidas (usa --forzar solo para inspeccionar).")
        for t in res.tablas.values():  # temporal del constructor de gasto
            if isinstance(t, Path):
                t.unlink(missing_ok=True)
        return 1
    man = salida.guardar(rutas, sprint, res.tablas, res.pruebas, res.revision, res.insumos)
    ins_mod.escribir_lock(rutas, res.insumos)
    for n, t in res.tablas.items():
        print(f"  {n}: {json.load(open(man))['tablas'][n]['filas']:,} filas")
    print(f"Manifiesto: {rutas.relativa(man)}")
    return 0 if res.ok else 1


def cmd_validar_reglas(a, rutas) -> int:
    """Piloto P2: corre los casos de prueba del validador (contrato §6) y la cobertura del alcance."""
    import csv
    from .motor.validador import casos
    from .motor.validador.contexto import cargar_contexto
    ctx = cargar_contexto(rutas.raiz)
    res = casos.correr(ctx, rutas.raiz / "tests" / "casos_validador" / a.carpeta)
    mal = [r for r in res if not r["ok"]]
    print(f"casos: {len(res)}  ok: {len(res) - len(mal)}  fallan: {len(mal)}")
    for r in mal[:30]:
        print(f"  ✘ {r['id']} ({r['regla']}): {str(r.get('obtenido'))[:160]}")
    p = rutas.raiz / "reglas" / "alcance_piloto.csv"
    alcance = [x["id"] for x in csv.DictReader(open(p, encoding="utf-8")) if x["necesaria_piloto"] in ("si", "solo_infraestructura")]
    cob = casos.cobertura(res, alcance)
    print(f"reglas del alcance: {len(alcance)}; implementadas: {sum(v['implementada'] for v in cob.values())}")
    return 0 if not mal else 1


class _ErrorCli(Exception):
    """Un error de uso de `pap preguntar` (el mensaje es para la persona)."""


def _tema_cli(tema: str, alias: dict) -> str:
    """`--tema` acepta los alias de `temas.alias_cli` (parametros_motor.yaml); lo que no es alias se pasa tal cual."""
    t = tema.strip().lower()
    return alias.get(t, t)


def _consulta_directa(a, alias: dict, msgs: dict) -> dict:
    """La consulta mínima que describen las opciones directas (sin validarla: eso lo hace `consulta.cargar`, S1-01)."""
    if a.anio is not None and (a.desde is not None or a.hasta is not None):
        raise _ErrorCli(msgs["anio_y_serie"])
    c: dict = {}
    if a.intencion:
        c["intencion"] = a.intencion
    if a.tema:
        c["tema"] = _tema_cli(a.tema, alias)
    if a.indicador:
        c["indicador"] = a.indicador
    if a.intencion == "identificar_extremo" and (a.nivel or a.dentro_de):
        t = {"nivel": a.nivel} if a.nivel else {}
        if a.dentro_de:
            t["dentro_de"] = {"texto": a.dentro_de}
        c["territorio"] = t
    elif a.territorio:
        c["territorio"] = {"texto": a.territorio}
    if a.comparar_con:
        c["comparar_con"] = {"texto": a.comparar_con}
    if a.anio is not None:
        c["periodo"] = {"tipo": "anio", "anio": a.anio}
    elif a.desde is not None or a.hasta is not None:
        c["periodo"] = {"tipo": "serie", **({"desde": a.desde} if a.desde is not None else {}),
                        **({"hasta": a.hasta} if a.hasta is not None else {})}
    return c


def _entradas(a, alias: dict, msgs: dict) -> list[tuple[str, str, object]]:
    """[(nombre, tipo, valor)]: `yaml` (consulta del piloto, qN.yaml), `json` (consulta mínima en archivo), `directa` o `texto`
    (pregunta en texto libre, S2-06: excluyente con los archivos, las opciones directas y --plan)."""
    directas = [a.intencion, a.tema, a.indicador, a.territorio, a.anio, a.desde, a.hasta, a.comparar_con, a.nivel, a.dentro_de]
    hay_directas = any(x is not None for x in directas)
    if a.texto is not None:
        if a.consultas or hay_directas or a.plan:
            raise _ErrorCli(msgs["texto_y_opciones"])
        return [("texto", "texto", a.texto)]
    if a.consultas and hay_directas:
        raise _ErrorCli(msgs["archivos_y_opciones"])
    if not a.consultas and not hay_directas:
        raise _ErrorCli(msgs["sin_consulta"])
    if hay_directas:
        return [("directa", "directa", _consulta_directa(a, alias, msgs))]
    out = []
    for q in a.consultas:
        ruta = Path(q)
        if not ruta.exists():
            raise _ErrorCli(msgs["no_existe"].format(ruta=q))
        archivos = sorted(x for x in ruta.iterdir() if x.suffix in (".json", ".yaml", ".yml")) if ruta.is_dir() else [ruta]
        if not archivos:
            raise _ErrorCli(msgs["carpeta_vacia"].format(ruta=q))
        for f in archivos:
            if f.suffix not in (".json", ".yaml", ".yml"):
                raise _ErrorCli(msgs["formato_no_soportado"].format(ruta=f))
            out.append((f.stem, "json" if f.suffix == ".json" else "yaml", f))
    return out


def cmd_preguntar(a, rutas) -> int:
    """Responde consultas: del piloto (tests/fixtures/consultas_piloto/qN.yaml), consultas mínimas en JSON (archivo, varios o carpeta) u
    opciones directas (S1-06). Escribe respuesta.json y .md por capas en --salida; una aclaración se imprime con sus opciones
    numeradas y no escribe nada. Códigos de salida: `cli.codigo_salida` de parametros_motor.yaml."""
    from .motor import ficha as F
    from .motor import plantillas
    from .motor import preguntar as P
    from .motor.consulta import ConsultaInvalida
    from .motor.respuesta import Motor, preguntar as preguntar_piloto
    from .motor.validador.contexto import cargar_contexto
    par = plantillas.parametros(rutas.raiz)
    cod = par["cli"]["codigo_salida"]["valor"]
    msgs = plantillas.textos(rutas.raiz, "cli.yaml")["mensajes"]
    try:
        entradas = _entradas(a, par["temas"]["alias_cli"]["valor"], msgs)
    except _ErrorCli as e:
        print(f"✘ {e}", file=sys.stderr)
        return cod["error"]
    salida = Path(a.salida) if a.salida else rutas.raiz / par["cli"]["salida_por_defecto"]["valor"]
    ctx = cargar_contexto(rutas.raiz)
    m = Motor(ctx)
    if entradas[0][1] == "texto":
        return _preguntar_texto(a, rutas, m, entradas[0][2], salida, cod, msgs)
    codigo, escribio = cod["respondida"], False
    gravedad = {cod["respondida"]: 0, cod["no_se_puede"]: 0, cod["aclaracion"]: 1, cod["error"]: 2}
    for nombre, tipo, valor in entradas:
        etiqueta = "" if tipo == "directa" else nombre
        try:
            if tipo == "yaml":
                if a.plan:
                    continue
                res = preguntar_piloto(ctx, valor, salida)
                escribio = True
                print(f"===== {res['consulta']['id']} · semáforo: {res['semaforo_respuesta']}")
                print(res["texto"])
                print("--- ficha")
                print(res["ficha"]["corta"])
                continue
            res = P.preguntar_minima(m, valor, elegir=a.elegir, solo_plan=a.plan)
        except (ConsultaInvalida, P.EleccionInvalida) as e:
            if etiqueta:
                print(f"✘ {msgs['consulta_de'].format(nombre=etiqueta)}", file=sys.stderr)
            for msg in (e.mensajes if isinstance(e, ConsultaInvalida) else [str(e)]):
                print(f"✘ {msg}", file=sys.stderr)
            nuevo = cod["error"]
        else:
            if res["tipo"] == "aclaracion":
                print(res["texto"])
                if res["aclaracion"]["opciones"]:                  # sin opciones no hay nada que elegir (S1-09, H3)
                    comparando = bool((res.get("consulta_minima") or {}).get("comparar_con"))
                    print(msgs["elegir_pista_comparar" if comparando else "elegir_pista"])
                nuevo = cod["aclaracion"]
            elif res["tipo"] == "plan":
                print(json.dumps(res["plan"], ensure_ascii=False, indent=1, default=str))
                nuevo = cod["respondida"]
            else:
                base = nombre if tipo == "json" else res["consulta"]["id"].lower()
                salida.mkdir(parents=True, exist_ok=True)
                (salida / f"{base}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
                (salida / f"{base}.md").write_text(F.markdown(res), encoding="utf-8")
                escribio = True
                sem = f" · semáforo: {res['semaforo_respuesta']}" if res["tipo"] == "respuesta" else " · no se puede"
                print(f"===== {res['consulta']['id']}{sem}")
                print(res["texto"])
                print("--- ficha")
                print(res["ficha"]["corta"])
                nuevo = cod["respondida"] if res["tipo"] == "respuesta" else cod["no_se_puede"]
        if gravedad.get(nuevo, 0) >= gravedad.get(codigo, 0):
            codigo = nuevo
    if escribio:
        print(f"Respuestas en {rutas.relativa(salida)}")
    return codigo


# Solo para las pruebas (tests/interprete/test_cli_texto.py lo reemplaza con monkeypatch por una función raiz → cliente: un
# LLM falso o el Cliente en modo «reproducir»). Ninguna opción ni variable de entorno lo cambia: en uso normal es None y
# `interpretar` usa el cliente en modo «vivo».
_LLM_DE_PRUEBA = None


def _preguntar_texto(a, rutas, m, texto: str, salida: Path, cod: dict, msgs: dict) -> int:
    """`pap preguntar --texto` (S2-06): la pregunta en texto libre pasa por el intérprete (S2-05). Imprime el aviso de recorte
    antes de todo; `entendimos` va primero en la respuesta, en el .md y fuera de las capas en el JSON. Solo una respuesta o un
    «no se puede» escriben archivos. Códigos de salida: `cli.codigo_salida` (un mensaje fijo, por su motivo o `mensaje`)."""
    from .interprete import interpretar as I
    from .motor import ficha as F
    from .motor.preguntar import EleccionInvalida
    try:
        res = I.interpretar(texto, m, elegir=a.elegir, llm=_LLM_DE_PRUEBA(rutas.raiz) if _LLM_DE_PRUEBA else None)
    except EleccionInvalida as e:
        print(f"✘ {e}", file=sys.stderr)
        return cod["error"]
    for aviso in res["interpretacion"]["avisos"]:
        print(aviso)
    if res["tipo"] == "mensaje":
        print(res["texto"])
        return cod.get(res["motivo"], cod["mensaje"])
    if res["tipo"] == "aclaracion":
        print(res["texto"])
        if res["aclaracion"]["opciones"]:
            comparando = bool((res.get("consulta_minima") or {}).get("comparar_con"))
            print(msgs["elegir_pista_comparar" if comparando else "elegir_pista"])
        return cod["aclaracion"]
    res = {"entendimos": res["entendimos"], **res}                  # fuera de las capas, primero
    base = res["consulta"]["id"].lower()
    salida.mkdir(parents=True, exist_ok=True)
    (salida / f"{base}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (salida / f"{base}.md").write_text(F.markdown(res), encoding="utf-8")
    if res["entendimos"]:
        print(res["entendimos"])
    sem = f" · semáforo: {res['semaforo_respuesta']}" if res["tipo"] == "respuesta" else " · no se puede"
    print(f"===== {res['consulta']['id']}{sem}")
    print(res["texto"])
    print("--- ficha")
    print(res["ficha"]["corta"])
    print(f"Respuestas en {rutas.relativa(salida)}")
    return cod["respondida"] if res["tipo"] == "respuesta" else cod["no_se_puede"]


def cmd_servir(a, rutas) -> int:
    """S3-09: levanta el servicio web en local (`--puerto`, `--red-local`); bloquea hasta Ctrl+C."""
    from .web import servir as S
    try:
        return S.servir(rutas.raiz, puerto=a.puerto, red_local=a.red_local)
    except KeyboardInterrupt:
        return 0


def cmd_foto_pim(a, rutas) -> int:
    """Pieza D (rondas 1-2): foto mensual del PIM (receta MEF-FOTO-PIM-MENSUAL, tabla foto_pim).
    DESACTIVADA por decisión del dueño del 8/10/2026: `registrar` y `extraer` se niegan; `listar` y `vistas` siguen."""
    from .capa0 import foto_pim as F
    if a.accion in ("registrar", "extraer"):
        receta = recetas.cargar(rutas, F.SOURCE_ID, permitir_desactivada=True)
        if receta.get("desactivada"):
            raise PapError(recetas.mensaje_desactivada(receta) + " Guía: biblioteca/cruda/GUIA_FOTO_PIM_MENSUAL.md")
    if a.accion == "registrar":
        if not a.archivo:
            raise PapError("Indica el archivo: pap foto-pim registrar RUTA/2026-Gasto-Mensual.csv --corte AAAA-MM-DD")
        r, res = F.registrar_foto(rutas, Path(a.archivo), a.corte, a.mover, a.nota, a.atribuido, a.consultado)
        if r is None:
            print(f"= sin cambio: ese archivo ya estaba registrado (foto {res['parquet']})")
        else:
            _mostrar_resultado(r, rutas)
        if res["fecha_corte_base"] != "declarada":
            print("⚠ sin --corte: mes_ref sale de la fecha de consulta y data_cutoff del último mes con devengado")
    elif a.accion == "extraer":
        for res in F.extraer_pendientes(rutas, rehacer=a.rehacer):
            print(f"✔ {res['parquet']}: {res['filas']:,} filas")
    elif a.accion == "vistas":
        print(F.sql_vistas(rutas))
        return 0
    filas = [[str(x["anio"]), f"{x['mes_ref']:02d}", x["fecha_ref"], x["fecha_ref_base"], x["mes_descarga"],
              str(x["mes_max_devengado"]), f"{x['filas']:,}", x["totales"]["pim"], x["parquet"]]
             for x in F.resumenes(rutas)]
    print(_tabla(filas, ["año", "mes_ref", "fecha_ref", "base", "descarga", "mes_dev", "filas", "PIM", "archivo"]) if filas
          else "No hay fotos del PIM todavía.")
    hoy = date.today()
    for anio in sorted({x["anio"] for x in F.resumenes(rutas)}):
        hasta = 12 if anio < hoy.year else hoy.month - 1  # último mes cerrado
        falta = F.meses_faltantes(rutas, anio, hasta)
        if falta:
            print(f"⚠ {anio}: faltan fotos de los meses {falta} (no se pueden reconstruir; ver la guía)")
    return 0


def _numeros_elegir(texto: str) -> list[int]:
    """`--elegir 2` o `--elegir 1,1`: los números de las opciones, uno por cada lugar ambiguo (S1-09, H3)."""
    try:
        numeros = [int(x) for x in texto.split(",")]
    except ValueError:
        raise argparse.ArgumentTypeError(f"«{texto}» no es un número de opción: escribe uno (2) o varios separados por coma (1,1)")
    return numeros


def _puerto(texto: str) -> int:
    try:
        n = int(texto)
    except ValueError:
        n = 0
    if not 1 <= n <= 65535:
        raise argparse.ArgumentTypeError(f"«{texto}» no es un puerto: escribe un número entre 1 y 65535")
    return n


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pap", description="Obtener, registrar, verificar y citar crudos de Pregúntale al Perú.")
    p.add_argument("--version", action="version", version=f"pap {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("revisar", help="Estado de las fuentes: recetas, capturas y días sin revisar")
    s.add_argument("source_id", nargs="?")
    s.set_defaults(fn=cmd_revisar)

    def opciones_registro(s):
        s.add_argument("--issued", help="Fecha de publicación según la fuente (AAAA-MM-DD)")
        s.add_argument("--edicion", help="Edición o versión declarada por la fuente")
        s.add_argument("--corte", help="Fecha de corte de los datos (AAAA-MM-DD)")
        s.add_argument("--corte-base", choices=["declarada", "max_fecha_en_datos", "desconocida"])
        s.add_argument("--consultado", help="Momento de obtención, si no es ahora (ISO 8601)")
        s.add_argument("--atribuido", help="Quién obtuvo el archivo y con qué (p. ej. 'Eber (manual, Firefox)')")
        s.add_argument("--evidencia", action="append", help="Captura de pantalla o PDF de la página (repetible)")
        s.add_argument("--nota", action="append", help="Problema conocido a anotar (repetible)")
        s.add_argument("--forzar", action="store_true", help="Registrar aunque no cumpla lo esperado (queda anotado)")

    s = sub.add_parser("registrar", help="Registrar archivos (de la bandeja o los indicados)")
    s.add_argument("source_id")
    s.add_argument("archivos", nargs="*")
    s.add_argument("--url-descarga", help="URL exacta del archivo (si se bajó a mano desde un enlace conocido)")
    s.add_argument("--mover", action="store_true", help="Mover el archivo al almacén en vez de copiarlo (crudos grandes)")
    s.add_argument("--recurso", help="Nombre del recurso (minúsculas, guiones), p. ej. gasto-2024")
    opciones_registro(s)
    s.set_defaults(fn=cmd_registrar)

    s = sub.add_parser("descargar", help="Descargar según la receta (o mostrar los pasos si es manual)")
    s.add_argument("source_id")
    s.add_argument("--url", help="URL concreta (sustituye la de la receta)")
    s.add_argument("--param", action="append", help="Valor para el patrón de URL: nombre=valor (repetible)")
    opciones_registro(s)
    s.set_defaults(fn=cmd_descargar)

    s = sub.add_parser("verificar", help="Verificar recetas, datapackage.json y huellas de los crudos")
    s.add_argument("source_id", nargs="?")
    s.add_argument("--rapido", action="store_true", help="Solo tamaños, sin recalcular huellas")
    s.set_defaults(fn=cmd_verificar)

    s = sub.add_parser("citar", help="Cita de un archivo (por prefijo de huella o por fuente: su última captura)")
    s.add_argument("clave")
    s.add_argument("--corta", action="store_true", help="Una línea para la ficha corta")
    s.set_defaults(fn=cmd_citar)

    s = sub.add_parser("construir", help="Construir tablas curadas (capa 0 e insumos estandarizados del piloto)")
    s.add_argument("que", choices=["territorio", "poblacion", "puentes", "gasto", "endes", "enaho", "mapa_pobreza",
                                          "indicadores"])
    s.add_argument("--forzar", action="store_true", help="Escribir aunque fallen pruebas bloqueantes")
    s.add_argument("--permitir-sucio", action="store_true", help="Construir con código sin commit (manifiesto 'sucio')")
    s.add_argument("--actualizar-insumos", action="store_true",
                   help="Usar las capturas más recientes y reescribir curados/insumos.lock.yaml")
    s.set_defaults(fn=cmd_construir)

    s = sub.add_parser("calcular", help="Piloto P1: cubo de indicadores (biblioteca/indicadores/fact_indicador.parquet)")
    s.add_argument("--forzar", action="store_true", help="Escribir aunque fallen pruebas bloqueantes")
    s.add_argument("--permitir-sucio", action="store_true", help="Construir con código sin commit (manifiesto 'sucio')")
    s.add_argument("--actualizar-insumos", action="store_true",
                   help="Usar las capturas más recientes y reescribir curados/insumos.lock.yaml")
    s.set_defaults(fn=cmd_construir, que="calculo")

    s = sub.add_parser("preguntar", help="Responder preguntas: consultas mínimas (JSON), consultas del piloto (YAML) u opciones directas",
                       description="Responde preguntas sobre los problemas del país con cifras de fuentes oficiales. La pregunta puede venir "
                                   "de archivos (consulta mínima .json o consulta del piloto tests/fixtures/consultas_piloto/qN.yaml), de una carpeta "
                                   "(curados/motor/consultas_minimas/), de las opciones directas o de una pregunta escrita con --texto. Si el lugar es ambiguo, imprime las opciones "
                                   "numeradas y sale con el código 2; repite con --elegir N para responderla.", add_help=False)
    s.add_argument("-h", "--help", action="help", help="Muestra esta ayuda y termina")
    s.add_argument("consultas", nargs="*", help="Archivos .json (consulta mínima) o .yaml (consulta del piloto), o carpetas con ellos")
    s.add_argument("--intencion", choices=["nivel_actual", "evolucion", "comparacion", "cruce", "identificar_extremo", "efecto"],
                   help="Qué se quiere saber: cuánto hay hoy, cómo cambió, comparar dos lugares, cruzar dos cifras, el lugar más alto o el efecto")
    s.add_argument("--tema", help="El problema: anemia, desnutricion_cronica, pobreza_monetaria o gasto_publico (también acepta alias "
                                  "como «desnutrición», «pobreza» o «gasto»)")
    s.add_argument("--indicador", help="Una cifra concreta (id de dim_indicador), en vez de --tema")
    s.add_argument("--territorio", help="El lugar, como se escribe: «Puno», «Ayaviri, Melgar», «Lima Metropolitana», «Perú»")
    s.add_argument("--anio", type=int, help="Un año concreto (por defecto, el último con datos)")
    s.add_argument("--desde", type=int, help="Primer año de una serie (con --intencion evolucion; por defecto, el primero con datos)")
    s.add_argument("--hasta", type=int, help="Último año de una serie (por defecto, el último con datos)")
    s.add_argument("--comparar-con", help="El segundo lugar de una comparación (con --intencion comparacion)")
    s.add_argument("--nivel", choices=["departamento", "provincia", "distrito"],
                   help="Con --intencion identificar_extremo: el nivel de los lugares que se ordenan")
    s.add_argument("--dentro-de", help="Con --intencion identificar_extremo: limitar a un lugar (hoy solo se responde para todo el país)")
    s.add_argument("--texto", metavar="PREGUNTA",
                   help="La pregunta escrita con tus palabras, entre comillas: «¿Cuánta anemia hay en Puno?». Se usa sola, sin "
                        "archivos ni opciones como --intencion o --tema (solo con --elegir y --salida)")
    s.add_argument("--elegir", type=_numeros_elegir, metavar="N[,N]",
                   help="Responde una aclaración sin preguntar: el número de la opción que imprimió el comando (empieza en 1). En una "
                        "comparación con dos lugares ambiguos, un número por lugar y en orden: --elegir 1,1")
    s.add_argument("--plan", action="store_true", help="Solo imprime el plan de cifras (JSON), sin calcular ni escribir respuestas; sirve para depurar")
    s.add_argument("--salida", help="Carpeta donde se escriben respuesta.json y .md por capas (por defecto salidas/preguntar, fuera de git)")
    s.set_defaults(fn=cmd_preguntar)

    s = sub.add_parser("servir", help="Levantar la web en este equipo (por defecto solo http://127.0.0.1:8000)",
                       description="Levanta la web de Pregúntale al Perú con el mismo motor. Por defecto solo se entra desde este equipo; "
                                   "con --red-local también desde otros equipos de la red de la casa. No es un despliegue público. "
                                   "Pulsa Ctrl+C para pararlo.")
    s.add_argument("--puerto", type=_puerto, help="Puerto donde escucha (por defecto, el de curados/web/parametros.yaml: 8000)")
    s.add_argument("--red-local", action="store_true",
                   help="Escuchar también en la red de la casa (0.0.0.0); sin esta opción, solo en 127.0.0.1")
    s.set_defaults(fn=cmd_servir)

    s = sub.add_parser("validar-reglas", help="Piloto P2: casos de prueba del validador de reglas")
    s.add_argument("--carpeta", default="casos", choices=["casos", "casos_implementador"])
    s.set_defaults(fn=cmd_validar_reglas)

    s = sub.add_parser("foto-pim", help="[DESACTIVADA 8/10/2026] Foto mensual del PIM: listar o ver vistas (registrar/extraer se niegan)")
    s.add_argument("accion", choices=["registrar", "extraer", "listar", "vistas"])
    s.add_argument("archivo", nargs="?", help="{anio}-Gasto-Mensual.csv (solo con registrar)")
    s.add_argument("--corte", help="Fecha «actualizado» del recurso en la página del MEF/PNDA (AAAA-MM-DD)")
    s.add_argument("--mover", action="store_true", help="Mover el CSV al almacén en vez de copiarlo")
    s.add_argument("--rehacer", action="store_true", help="extraer: rehacer también las fotos ya escritas")
    s.add_argument("--nota", action="append", help="Problema conocido a anotar (repetible)")
    s.add_argument("--atribuido", help="Quién obtuvo el archivo y con qué")
    s.add_argument("--consultado", help="Momento de obtención, si no es ahora (ISO 8601)")
    s.set_defaults(fn=cmd_foto_pim)

    s = sub.add_parser("almacen", help="Mantenimiento del almacén de crudos: comprimir con zstd, restaurar un bloque "
                                       "desde su respaldo y liberar sus ZIP")
    s.add_argument("accion", choices=["comprimir", "restaurar", "liberar"],
                   help="comprimir: CSV/TXT grandes → .zst; restaurar: prueba el respaldo del bloque y lo marca "
                        "«respaldado»; liberar: borra los ZIP de un bloque respaldado (simulación por defecto)")
    s.add_argument("--bloque", help="restaurar/liberar: <encuesta>-<anio>, p. ej. endes-2024")
    s.add_argument("--repo", help="restaurar: repo de respaldo; debe ser el configurado (almacen.repo_crudos)")
    s.add_argument("--simular", dest="ejecutar", action="store_false", default=False,
                   help="liberar: solo mostrar qué se borraría y cuánto (por defecto)")
    s.add_argument("--ejecutar", dest="ejecutar", action="store_true",
                   help="liberar: borrar de verdad, después de confirmar")
    s.add_argument("--si", action="store_true", help="liberar --ejecutar: no preguntar (confirmación dada)")
    s.add_argument("--min-mb", type=float, default=almacen.COMPRIMIR_MIN_MB,
                   help=f"Solo archivos de texto de más de N MB (por defecto {almacen.COMPRIMIR_MIN_MB})")
    s.add_argument("--dry-run", "--ensayo", dest="dry_run", action="store_true",
                   help="Solo listar qué se comprimiría y cuánto pesa; no cambia nada")
    s.add_argument("--solo", action="append", help="Prefijo de huella a procesar (repetible); por defecto, todos")
    s.add_argument("--nivel", type=int, default=almacen.NIVEL_ZSTD, help="Nivel de zstd (por defecto 9)")
    s.add_argument("--max-segundos", type=float, default=0,
                   help="No empezar un objeto nuevo pasado este tiempo (para correr por partes)")
    s.set_defaults(fn=cmd_almacen)

    s = sub.add_parser("microdatos", help="Microdatos de las encuestas: convertir los ZIP registrados a Parquet (SAV/DTA aislados)")
    s.add_argument("accion", choices=["convertir"])
    s.add_argument("--encuesta", required=True, choices=["ENDES"], help="Encuesta a convertir")
    s.add_argument("--anio", required=True, type=int, help="Año de la encuesta (p. ej. 2024)")
    s.set_defaults(fn=cmd_microdatos)

    s = sub.add_parser("variables", help="Índice de variables de las encuestas: indexar los ZIP registrados (metadatos de SAV/DTA)")
    s.add_argument("accion", choices=["indexar"])
    s.add_argument("--encuesta", required=True, choices=["ENDES"], help="Encuesta a indexar")
    s.add_argument("--anio", required=True, type=int, help="Año de la encuesta (p. ej. 2024)")
    s.set_defaults(fn=cmd_variables)

    s = sub.add_parser("inferencia", help="Motor de inferencia: validar las tablas curadas y las recetas de curados/inferencia/, o calcular una receta")
    s.add_argument("accion", choices=["validar-tablas", "validar-recetas", "receta"])
    s.add_argument("id", nargs="?", help="receta: id de la receta (curados/inferencia/recetas/<id>.yaml)")
    s.add_argument("--anio", type=int, help="receta: año de la encuesta (p. ej. 2024)")
    s.add_argument("--comparar-cubo", action="store_true", help="receta: compara las filas con las 90 de 2024 del cubo y las compuertas con m0-00_estados_cubo.csv")
    s.set_defaults(fn=cmd_inferencia)

    s = sub.add_parser("indice", help="Reconstruir el índice DuckDB")
    s.set_defaults(fn=cmd_indice)

    s = sub.add_parser("recetas", help="Generar recetas desde el catálogo o validarlas")
    s.add_argument("accion", choices=["generar", "validar", "sincronizar"],
                   help="sincronizar: copia ola, estrategia y compuerta del catálogo y bloquea_mvp de R-DEP-01 al bloque catalogo de cada receta")
    s.add_argument("--ola", default="0_base")
    s.add_argument("--sobrescribir", action="store_true")
    s.set_defaults(fn=cmd_recetas)
    return p


def main(argv: list[str] | None = None) -> int:
    a = construir_parser().parse_args(argv)
    try:
        return a.fn(a, obtener_rutas())
    except NoImplementado as e:
        print(f"⏳ {e}", file=sys.stderr)
        return 2
    except PapError as e:
        print(f"✘ {e}", file=sys.stderr)
        return 1
    except OSError as e:  # p. ej. disco lleno: mensaje claro, sin traceback
        import errno
        motivo = "disco lleno: libera espacio y vuelve a correr el comando" if e.errno == errno.ENOSPC else str(e)
        print(f"✘ Error del sistema de archivos: {motivo}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
