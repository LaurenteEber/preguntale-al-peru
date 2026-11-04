"""E3 – gasto (decisión del dueño del 8/10/2026: «obras de ejecutoras nacionales con meta en Lima: salen de la cifra de
Lima solo las de sede o de función nacional (lista curada de CUI), no colegios ni hospitales; se revisan también las
obras de ejecutoras fuera de ejecutoras_alcance.yaml»). Genera curados/capa0/obras_sede_nacional.yaml.

Insumos fijos (reproducible):
  obras_gn_lima_clasificadas.csv  obras en Lima de ejecutoras con alcance nacional, clasificadas por palabras
                                              clave (análisis del 8/10, punto 4; clase b = sede o función nacional)
  obras_fuera_del_yaml.csv                    obras en Lima de las 20 ejecutoras del GN sin entrada en el YAML (H6)
Curaduría (revisión a mano por nombre del proyecto, de mayor a menor monto):
  EXCLUIR_B   CUI de la clase b que en realidad sirven a residentes (colegios, cortes y defensa pública de Lima, CAR,
              biblioteca pública, riego) → se quedan en Lima
  INCLUIR_A   CUI de la clase a que son sede o función nacional y la palabra clave no detectó
  FUERA_YAML_QUEDA  CUI de las ejecutoras fuera del YAML que sirven a residentes de Lima → se quedan
Uso (desde codigo/ingesta): uv run --frozen python <esta carpeta>/generar_obras_sede.py <raiz> [--salida ruta]"""
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

RAIZ = Path(sys.argv[1])
AQUI = Path(__file__).resolve().parent
SALIDA = Path(sys.argv[sys.argv.index("--salida") + 1]) if "--salida" in sys.argv else \
    RAIZ / "curados/capa0/obras_sede_nacional.yaml"
cla = pd.read_csv(AQUI / "obras_gn_lima_clasificadas.csv", dtype={"sec_ejec": str, "cui": str})
fy = pd.read_csv(AQUI / "obras_fuera_del_yaml.csv", dtype={"sec_ejec": str, "cui": str})

EXCLUIR_B = {
    "2661443": "mobiliario de 4 instituciones educativas (colegios PNP): colegio, se queda",
    "2645738": "Corte Superior de Puente Piedra-Ventanilla, unidad de flagrancia: servicio local",
    "2708358": "hardware de órganos jurisdiccionales no penales del Cercado de Lima: cortes de Lima",
    "2708375": "hardware de órganos jurisdiccionales penales del Cercado de Lima: cortes de Lima",
    "2388844": "nueva sede judicial de la Corte Superior de Justicia de Lima: servicio local",
    "2668735": "salas y juzgados de extinción de dominio en Lima: competencia no verificada, se queda (conservador)",
    "2623092": "defensa pública de Lima Este (flagrancia): servicio local",
    "2623016": "defensa pública de Lima Norte (flagrancia): servicio local",
    "2700763": "defensa pública de Lima Centro (flagrancia): servicio local",
    "2700774": "defensa pública de Lima Sur (flagrancia): servicio local",
    "2673350": "módulo defensorial de Lima Norte: servicio local",
    "2672578": "oficina defensorial de Lima: servicio local",
    "2687730": "módulo defensorial de Los Olivos: servicio local",
    "2660702": "centro de acogida residencial (CONADIS) en Ancón: atiende a residentes",
    "2660713": "centro de acogida residencial (CONADIS) en San Miguel: atiende a residentes",
    "2660715": "centro de acogida residencial (CONADIS) en San Miguel: atiende a residentes",
    "2660688": "centro de acogida residencial (CONADIS) en Lima: atiende a residentes",
    "2660654": "centro de acogida residencial (CONADIS) en San Miguel: atiende a residentes",
    "2667819": "centro de acogida residencial (INABIF) en San Miguel: atiende a residentes",
    "2667726": "centro de acogida residencial (INABIF) en San Miguel: atiende a residentes",
    "2667795": "centro de acogida residencial (INABIF) en San Miguel: atiende a residentes",
    "2512530": "equipos para instituciones educativas (COVID-19): colegios, se quedan",
    "2488226": "equipos para instituciones educativas (COVID-19): colegios, se quedan",
    "2505984": "Gran Biblioteca Pública de Lima (Av. Abancay): servicio a residentes",
    "2702791": "Dirección Regional de Trabajo de Lima Metropolitana: servicio local",
    "2700070": "Centro MAC de Ciudad de Dios (San Juan de Miraflores): atención a residentes",
    "2577388": "protección de quebradas en Santiago de Surco: obra para residentes",
    "2618885": "agua para riego en Laraos (Yauyos): obra para residentes",
    "2582398": "agua para riego en Colonia (Yauyos): obra para residentes",
    # auditoría de E3, H1: la decisión dice «no colegios ni hospitales»; el Hospital PNP atiende sobre todo a policías y
    # familiares que viven en Lima: se queda en Lima
    "2256359": "Hospital Nacional PNP Luis N. Sáenz (servicios críticos y consulta externa): hospital que atiende a "
               "residentes de Lima; se queda (decisión «no hospitales», auditoría de E3, H1)",
}
INCLUIR_A = {
    "2410495": ("sede_institucional", "Sistema integrado de fiscalización ambiental del OEFA (sede de Jesús María)"),
    "2647972": ("funcion_nacional", "drones y equipos de fiscalización ambiental del OEFA (organismo nacional)"),
    "2646534": ("funcion_nacional", "equipos de fiscalización ambiental del OEFA (organismo nacional)"),
    "2593676": ("sede_institucional", "equipos de las direcciones generales del Ministerio de Cultura (sede San Borja)"),
    "2599670": ("funcion_nacional", "equipos de medición de la calidad de servicios móviles (OSIPTEL, fiscalización nacional)"),
    "2300172": ("tecnologia_institucional", "TIC de la SUCAMEC (sede de Magdalena)"),
    "2486616": ("sede_institucional", "equipos de la Intendencia Nacional de Bomberos (sede de San Isidro)"),
    "2700106": ("sede_institucional", "equipos de oficina del PRONATEL (sede de La Victoria)"),
    "2614715": ("instituto_nacional", "órganos de línea del INGEMMET (servicio geológico nacional)"),
    "2131851": ("instituto_nacional", "infraestructura y equipos del INGEMMET (servicio geológico nacional)"),
    "2662789": ("instituto_nacional", "radiómetro de teledetección del laboratorio del INGEMMET"),
    "2599682": ("instituto_nacional", "plataforma del SENAMHI (servicio meteorológico nacional)"),
    "2518933": ("funcion_nacional", "telecomunicaciones de la DIRTIC PNP (red policial nacional)"),
    "2611575": ("funcion_nacional", "vehículos de la Dirección de Inteligencia de la PNP (dirección nacional)"),
    "2627484": ("patrimonio_cultural_nacional", "Gran Teatro Nacional"),
    "2571990": ("formacion_nacional", "Escuela Nacional de Archivística del Archivo General de la Nación"),
    "2685460": ("formacion_nacional", "Dirección de Educación y Doctrina de la PNP (formación policial nacional)"),
    "2616500": ("sede_institucional", "Sala Penal Permanente de la Corte Suprema (competencia nacional)"),
    "2186722": ("funcion_nacional", "Centro de Convenciones de Lima (activo nacional del MVCS)"),
    "2454518": ("sede_institucional", "ascensores del Palacio Nacional de Justicia (Corte Suprema y dirección del PJ)"),
    "2529904": ("funcion_nacional", "Fiscalía Superior Coordinadora Nacional de extinción de dominio"),
    "2480974": ("funcion_nacional", "análisis de la información nacional de las fiscalías de violencia contra la mujer"),
    "2601335": ("sede_institucional", "oficinas de la Comandancia General de la PNP y de la OGTIC del MININTER"),
    "2532717": ("funcion_nacional", "almacén central de la División de Logística de la PNP"),
    "2559254": ("tecnologia_institucional", "equipos de comunicación de la DIRTIC PNP"),
    "2652695": ("tecnologia_institucional", "TI de la SUNASS (sede)"),
    "2700826": ("instituto_nacional", "laboratorio de geomática del INGEMMET"),
    "2688905": ("sede_institucional", "ambiente administrativo de la Dirección de Investigación Criminal (edificio COIP)"),
    "2561416": ("instituto_nacional", "servicios de metrología del INACAL (laboratorio nacional)"),
    "2652583": ("sede_institucional", "ascensor y seguridad de la sede central del Programa Nacional de Saneamiento Rural"),
    "2549886": ("tecnologia_institucional", "sistemas de información de la sede central de FONDEPES"),
    "2233917": ("patrimonio_cultural_nacional", "patrimonio archivístico de la Nación (Archivo General de la Nación)"),
    "2161813": ("funcion_nacional", "Villa Deportiva Nacional (VIDENA), del IPD"),
}
FUERA_YAML_QUEDA = {
    "2510864": "centro de servicios al contribuyente Oeste 1-B Surquillo y cobranza de campo (atención a contribuyentes "
               "de Lima; la parte de sede nacional de insumos químicos no se separa): se queda (conservador)",
    "2151569": "centro de servicio al contribuyente de Lima Este 2: atención a residentes",
    "2133067": "centro de servicios al contribuyente de Lima Sur: atención a residentes",
    "2159420": "centro de servicio al contribuyente de Lima Oeste 1 (Miraflores): atención a residentes",
    "2652545": "intendencia de tributos internos de Huacho: servicio local",
    "2524178": "SUNARP Zona Registral IX (Lima, Huaura, Cañete, Huaral, Barranca y Callao): servicio a residentes",
    "2115270": "SUNARP Zona Registral IX, edificio de bienes muebles (sede Lima): servicio a residentes",
}
# Motivos revisados a mano (los de mayor monto y los dudosos); los demás reciben el motivo de su criterio
MANUAL = {
    "2412703": ("funcion_nacional", "Contraloría: servicios de control gubernamental de todo el país (proyecto BID)"),
    "2300104": ("tecnologia_institucional", "SUNAT: soluciones de TI para la atención de usuarios de todo el país"),
    "2325802": ("funcion_nacional", "Ventanilla Única de Comercio Exterior (VUCE), plataforma nacional"),
    "2300859": ("funcion_nacional", "SUNAT: custodia y disposición de bienes y mercancías (aduanas, función nacional)"),
    "2359961": ("funcion_nacional", "MEF: gestión de la inversión pública (sistema nacional Invierte.pe)"),
    "2394412": ("funcion_nacional", "OSCE: gestión de la contratación pública nacional"),
    "2194717": ("funcion_nacional", "MEF: política de ingresos públicos y recaudación municipal de todo el país"),
    "2577341": ("tecnologia_institucional", "INEI: servidores y almacenamiento de la sede (estadística nacional)"),
    "2363565": ("tecnologia_institucional", "Perú Compras: plataforma tecnológica de compras públicas nacionales"),
    "2565162": ("funcion_nacional", "MEF: abastecimiento público (sistema nacional)"),
    "2293177": ("sede_institucional", "SMV: servicios de regulación del mercado de valores (sede)"),
    "2566964": ("funcion_nacional", "PCM: transformación digital del Estado (Secretaría de Gobierno Digital)"),
    "2545687": ("tecnologia_institucional", "SERVIR: transformación digital (sede)"),
    "2235055": ("formacion_nacional", "Escuela de Oficiales de la PNP (Chorrillos): forma oficiales para todo el país"),
    "2540919": ("funcion_nacional", "fusiles de asalto de la PNP (compra central para todo el país)"),
    "2424326": ("sede_institucional", "reforzamiento estructural del edificio del MEF"),
    "2386675": ("tecnologia_institucional", "Expediente Judicial Electrónico, procesos no penales a nivel nacional"),
    "2380780": ("funcion_nacional", "protección respiratoria de los bomberos del país (compra central)"),
    "2651949": ("tecnologia_institucional", "SUNAT: hardware y servidores de los servicios tributarios y aduaneros"),
    "2251549": ("patrimonio_cultural_nacional", "Museo Nacional del Perú (Lurín)"),
    "2355382": ("sede_institucional", "sede central del Ministerio de Relaciones Exteriores"),
    "2455051": ("tecnologia_institucional", "data center del MEF"),
    "2235054": ("formacion_nacional", "Escuela Técnico Superior de Mujeres PNP (San Bartolo): formación policial nacional"),
    "2598813": ("sede_institucional", "habitabilidad de las unidades orgánicas del MTC"),
    "2519200": ("funcion_nacional", "equipos para las 243 compañías de bomberos del país (compra central)"),
    "2264711": ("sede_institucional", "nueva sede del Ministerio de Agricultura y Riego"),
    "2234253": ("instituto_nacional", "Laboratorio Nacional de Instrumentación Geofísica del IGP"),
    "2518751": ("funcion_nacional", "vehículos de la Dirección Nacional de Investigación Criminal (DIREICAJ, mixta)"),
    "2635727": ("funcion_nacional", "telefonía forense de la DIVINDAT (análisis a nivel nacional)"),
    "2420630": ("sede_institucional", "servicios a usuarios del MVCS (sede de San Isidro)"),
}
REGEX = [
    ("sede_institucional", r"SEDE CENTRAL|SEDE INSTITUCIONAL|SEDE ADMINISTRATIVA|NUEVA SEDE|HABITABILIDAD|EDIFICIO P[UÚ]BLICO|"
                           r"ASCENSOR|EMBAJADA|OFICINA CONSULAR|ALMAC[EÉ]N CENTRAL|ARCHIVO CENTRAL"),
    ("tecnologia_institucional", r"SERVIDOR|STORAGE|HARDWARE|SOFTWARE|DATA CENTER|CENTRO DE DATOS|SISTEMA DE INFORMACI|"
                                 r"INTEROPERABILIDAD|TECNOLOG[IÍ]AS? DE (LA )?INFORMACI|PLATAFORMA TECNOL|VIDEOCONFERENCIA"),
    ("formacion_nacional", r"ESCUELA"),
    ("patrimonio_cultural_nacional", r"MUSEO NACIONAL|BIBLIOTECA NACIONAL|TEATRO NACIONAL"),
]
INSTITUTOS = {"151", "121", "123", "124", "126", "188", "84", "160", "189", "474", "1632"}
MOTIVO_CRIT = {
    "sede_institucional": "obra o equipamiento de la sede de una entidad de alcance nacional",
    "tecnologia_institucional": "tecnología de la sede de una entidad de alcance nacional (sirve a todo el país)",
    "formacion_nacional": "escuela o centro de formación de alcance nacional",
    "patrimonio_cultural_nacional": "museo, biblioteca o teatro nacional",
    "instituto_nacional": "instituto nacional (salud, ciencia o servicio técnico) de alcance nacional: la obra sigue a su ejecutora",
    "funcion_nacional": "activo de una función nacional (no atiende a residentes de un lugar)",
}


# auditoría de E3, H1: obras de los 4 institutos especializados con alcance nacional y verificar_procedencia
# (decisión 8 de la ronda 2). No se tratan como «hospital de residentes»: siguen el alcance de su ejecutora, igual que su
# gasto corriente; si el dueño fija su procedencia (Ley 27806), la obra cambia con la ejecutora. Las obras del INEN y del
# INSN San Borja no están en esta lista: salen de Lima por referencia_nacional (línea aparte).
INSTITUTOS_SALUD = {"126": "INSN Breña", "124": "Instituto Nacional de Oftalmología",
                    "121": "Instituto Nacional de Salud Mental", "123": "Instituto Nacional de Ciencias Neurológicas"}


def criterio(r):
    if r.sec_ejec in INSTITUTOS_SALUD:
        return ("instituto_nacional", f"{INSTITUTOS_SALUD[r.sec_ejec]}: instituto especializado de alcance nacional con "
                "verificar_procedencia (decisión 8 de la ronda 2); la obra sigue el alcance de su ejecutora, como su "
                "gasto corriente, y cambia con ella si el dueño fija su procedencia", "revision_manual")
    if r.cui in MANUAL:
        return MANUAL[r.cui][0], MANUAL[r.cui][1], "revision_manual"
    if r.cui in INCLUIR_A:
        return INCLUIR_A[r.cui][0], INCLUIR_A[r.cui][1], "revision_manual_agregada"
    n = str(r.nombre_inversion).upper()
    if r.sec_ejec in INSTITUTOS:
        return "instituto_nacional", MOTIVO_CRIT["instituto_nacional"], "palabra_clave_y_ejecutora"
    for c, rx in REGEX:
        if re.search(rx, n):
            return c, MOTIVO_CRIT[c], "palabra_clave_y_ejecutora"
    return "funcion_nacional", MOTIVO_CRIT["funcion_nacional"], "palabra_clave_y_ejecutora"


b = cla[cla.clase == "b_institucional_nacional"]
assert set(EXCLUIR_B) <= set(b.cui), set(EXCLUIR_B) - set(b.cui)
a = cla[cla.clase == "a_servicio_residentes"]
assert set(INCLUIR_A) <= set(a.cui), set(INCLUIR_A) - set(a.cui)
assert set(FUERA_YAML_QUEDA) <= set(fy.cui)
lista = pd.concat([b[~b.cui.isin(EXCLUIR_B)].assign(origen="alcance_nacional_clase_b"),
                   a[a.cui.isin(INCLUIR_A)].assign(origen="alcance_nacional_agregada"),
                   fy[~fy.cui.isin(FUERA_YAML_QUEDA)].assign(origen="fuera_del_yaml")], ignore_index=True)
assert not lista.duplicated(["cui", "sec_ejec"]).any()
filas = []
for r in lista.sort_values(["d2023_2025", "cui", "sec_ejec"], ascending=[False, True, True]).itertuples():
    c, m, rev = criterio(r)
    filas.append({"cui": r.cui.zfill(7), "sec_ejec": r.sec_ejec, "ejecutora": str(r.ejecutora).strip(),
                  "nombre_inversion": re.sub(r"\s+", " ", str(r.nombre_inversion)).strip(), "criterio": c,
                  "motivo": m, "revision": rev, "origen": r.origen,
                  "devengado_2023_2025_millones": round(float(r.d2023_2025), 2)})
CAB = f"""# Obras (proyectos ubicados por CUI) de ejecutoras del Gobierno Nacional en el departamento de Lima que son SEDE o
# ACTIVO DE UNA FUNCIÓN NACIONAL: salen de la cifra de Lima (cuenta_en_lima = false; obra_sede_nacional = true en
# fact_gasto_territorial) y se cuentan como gasto nacional con sede en Lima, como el resto del gasto de su ejecutora.
# Decisión del dueño (8/10/2026, docs/decisiones.md): «salen de la cifra de Lima solo las de sede o de función
# nacional (lista curada de CUI), no colegios ni hospitales; se revisan también las obras de ejecutoras fuera de
# ejecutoras_alcance.yaml». Análisis: 00_proyecto/analisis_2026-10-08/gasto/informe.md §4 (opción B).
# Clave: (cui, sec_ejec); solo se aplica a filas del nivel E atribuidas por CUI al departamento 15.
# criterio: sede_institucional | tecnologia_institucional | formacion_nacional | patrimonio_cultural_nacional |
#           instituto_nacional | funcion_nacional.  revision: revision_manual (por nombre del proyecto),
#           revision_manual_agregada (no la detectó la palabra clave) o palabra_clave_y_ejecutora (aproximada).
# origen: alcance_nacional_clase_b | alcance_nacional_agregada | fuera_del_yaml (20 ejecutoras sin entrada, H6).
# devengado_2023_2025_millones: informativo (gasto final, fact v1.3.0); la construcción no lo usa.
# Estado: APLICADA por el criterio aprobado por el dueño el 8/10/2026; la lista (CUI por CUI) es revisable por el dueño
# (revisado_dueno: false hasta su visto; resumen para la revisión: e3_gasto/revision_dueno_obras_sede.csv). Mientras
# tanto la cifra de Lima que la usa es provisional. No se incluyen hospitales que atienden a residentes (el Hospital
# Nacional PNP se queda en Lima); las obras del INS y de los 4 institutos especializados con verificar_procedencia siguen
# el alcance nacional de su ejecutora (motivo por CUI); las del INEN e INSN San Borja salen por referencia_nacional.
# Las 20 ejecutoras de origen fuera_del_yaml tienen desde la v3 entrada propia en ejecutoras_alcance.yaml
# (paso agregada_e3_sin_meta_lima): sus obras siguen ese alcance declarado.
# Generado por curados/generadores/e3_gasto/generar_obras_sede.py ({len(filas)} CUI).
"""
doc = {"version": "1.1.0", "revisado_dueno": False,
       "estado": "aplicada por criterio aprobado el 8/10/2026; lista revisable por el dueño (revision_dueno_obras_sede.csv)",
       "obras": filas}
SALIDA.write_text(CAB + yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
t = pd.DataFrame(filas)
print(len(t), "CUI;", round(t.devengado_2023_2025_millones.sum(), 1), "M")
print(t.groupby("origen").devengado_2023_2025_millones.agg(["count", "sum"]).round(1))
print(t.groupby("criterio").devengado_2023_2025_millones.agg(["count", "sum"]).round(1))
print("excluidas de la clase b:", round(b[b.cui.isin(EXCLUIR_B)].d2023_2025.sum(), 2), "| quedan fuera del YAML:",
      round(fy[fy.cui.isin(FUERA_YAML_QUEDA)].d2023_2025.sum(), 2))
# H2: CSV corto para el visto del dueño: los 30 mayores de la lista + casos límite (salen o se quedan)
LIMITE = {
    "2300859": "instalación de aduanas ubicada en Lima, aunque la función es nacional (5.º mayor)",
    "2235054": "no verificado que la ETS de Mujeres PNP forme personal de todo el país",
    "2186722": "Centro de Convenciones de Lima: activo nacional, uso local posible",
    "2518751": "vehículos de DIRINCRI (DIREICAJ, mixta): operan sobre todo en Lima",
    "2635727": "DIVINDAT (DIREICAJ, mixta): análisis nacional, operación en Lima",
}
QUEDA = {"2256359": "hospital: se queda en Lima por la decisión (H1)",
         "2510864": "centro de servicios SUNAT Surquillo: atención a contribuyentes de Lima, se queda (mixto)",
         "2459243": "central 911 de Lima Metropolitana y Callao (PRONATEL): servicio a residentes, se queda"}
tl = pd.DataFrame(filas).assign(cui=lambda x: x.cui.str.lstrip("0").str.zfill(7))
top = set(tl.head(30).cui)
rev = []
for x in filas:
    lim = LIMITE.get(x["cui"]) or ("instituto especializado (hospital de alcance nacional): sigue a su ejecutora"
                                   if x["criterio"] == "instituto_nacional" and x["sec_ejec"] in INSTITUTOS_SALUD else None)
    if x["cui"] in top or lim:
        rev.append({"cui": x["cui"], "sec_ejec": x["sec_ejec"], "ejecutora": x["ejecutora"][:60],
                    "proyecto": x["nombre_inversion"][:120], "devengado_2023_2025_millones": x["devengado_2023_2025_millones"],
                    "aplicado": "sale de Lima", "criterio": x["criterio"], "origen": x["origen"],
                    "por_que_revisar": lim or ("ejecutora fuera del YAML hasta la v3" if x["origen"] == "fuera_del_yaml"
                                               else "entre los 30 mayores")})
todas = pd.concat([cla, fy], ignore_index=True)
for cui, porq in QUEDA.items():
    r = todas[todas.cui == cui].iloc[0]
    rev.append({"cui": cui, "sec_ejec": r.sec_ejec, "ejecutora": str(r.ejecutora).strip()[:60],
                "proyecto": re.sub(r"\s+", " ", str(r.nombre_inversion)).strip()[:120],
                "devengado_2023_2025_millones": round(float(r.d2023_2025), 2), "aplicado": "se queda en Lima",
                "criterio": "", "origen": "", "por_que_revisar": porq})
pd.DataFrame(rev).to_csv(AQUI / "revision_dueno_obras_sede.csv", index=False)
print("revision_dueno_obras_sede.csv:", len(rev), "filas")
# H9: las listas de curaduría usan el CUI como clave. Los CUI decididos que tienen dos ejecutoras son 4, y en los 4 la
# decisión vale para ambas (las dos salen de Lima): 2412703 Contraloría (1698 y 196), 2325802 VUCE (1661 y 1070),
# 2566964 transformación digital PCM (1763 y 3) y 2627484 Gran Teatro Nacional (1544 y 1363, ambas del MINCUL)
dobles = set(todas[todas.duplicated("cui", keep=False)].cui)
DOBLES_OK = {"2412703", "2325802", "2566964", "2627484"}
assert dobles & (set(EXCLUIR_B) | set(INCLUIR_A) | set(MANUAL) | set(FUERA_YAML_QUEDA)) == DOBLES_OK
assert all(set(lista[lista.cui == c].sec_ejec) == set(todas[todas.cui == c].sec_ejec) for c in DOBLES_OK)
if "--revisar" in sys.argv:   # clase a que mencionan sede/nacional/TI y no se agregaron (para la revisión manual)
    rx = r"SEDE|NACIONAL|OFICINA GENERAL|TECNOLOG|SERVIDOR|HARDWARE|SOFTWARE|INSTITUTO|DIRECCI[OÓ]N"
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 140); pd.set_option("display.max_rows", 300)
    x = a[~a.cui.isin(INCLUIR_A) & a.nombre_inversion.str.upper().str.contains(rx, regex=True, na=False)]
    print(x[["sec_ejec", "cui", "d2023_2025", "nombre_inversion"]].to_string())
