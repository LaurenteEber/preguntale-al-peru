"""P3 – Lima en tres ámbitos (L6, decisiones del dueño del 9/10/2026): extiende GA-01 y E3 al Callao (07) con UN solo
mecanismo. Genera curados/capa0/ejecutoras_alcance.yaml (v4) y obras_sede_nacional.yaml (v1.2.0) a partir de la
salida de los generadores de E3 (que se corren aquí, sin cambios) y de las instantáneas de esta carpeta
(ejecutoras_meta07.csv y obras_gn_callao.csv, de 01_inventario_callao.py). Reproducible e idempotente.

Uso (desde la raíz del repo): .venv/bin/python <esta carpeta>/generar_p3.py <raiz> [--salida-alcance r] [--salida-obras r]

Cambios:
  1. Cada ejecutora del GN con gasto por meta 07 (67) recibe el bloque `alcance_callao` (alcance nacional | callao,
     mixta, verificar_procedencia, criterio, paso, decision, revisado_dueno). Pasos:
       decision_L6_HA3       decisión L6 del dueño con la corrección H-A3 del auditor (revisado_dueno: true);
       p3_implementador      caso revisado una por una por el implementador (revisado_dueno: false);
       p3_auditor            corrección de la auditoría de P3 (H-P3-3, H-P3-4; revisado_dueno: false);
       regla_sede_fuera_del_07  sede fuera del Callao: la meta 07 es servicio prestado en el Callao → callao.
  2. Se agregan 3 ejecutoras sin gasto con meta 15 (CSJ Callao, RENIEC, ONPE; paso agregada_p3_sin_meta_lima) para
     llevar su bloque: su `alcance` (meta 15) no se aplica.
  3. obras_sede_nacional.yaml: 12 obras del GN en el Callao de sede o de función nacional (origen callao_p3,
     departamento 07). Las dudosas quedan FUERA de la lista y se listan en obras_callao_revision.csv como `revisar`.
"""
import csv
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

RAIZ = Path(sys.argv[1])
AQUI = Path(__file__).resolve().parent
E3 = RAIZ / "curados/generadores/e3_gasto"
DATOS = RAIZ / "curados/capa0"
arg = lambda k, d: Path(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d  # noqa: E731
SAL_ALC = arg("--salida-alcance", DATOS / "ejecutoras_alcance.yaml")
SAL_OBR = arg("--salida-obras", DATOS / "obras_sede_nacional.yaml")

D_L6 = ("Dueño, 9/10/2026: L6 (03_auditoria/lima_tres_ambitos/README.md) con la corrección H-A3 del auditor "
        "(auditor_maquinaria/auditoria.md)")
# sec_ejec: (alcance, mixta, verificar_procedencia, paso, criterio)
DECISIONES = {
    # --- L6 + H-A3 (nacional solo donde no hay servicio directo a residentes del Callao)
    "471": ("nacional", False, False, "decision_L6_HA3",
            "Marina de Guerra, sede en el Callao (070104): defensa nacional sin servicio directo a residentes (personal, "
            "operación e inversiones de la Marina de todo el país; 50/38/34 % del gasto del Callao en 2023-2025)"),
    "1205": ("nacional", False, False, "decision_L6_HA3",
             "Autoridad Portuaria Nacional, sede en el Callao: regula todos los puertos del país"),
    "193": ("nacional", False, False, "decision_L6_HA3",
            "IMARPE, sede en el Callao: investigación del mar y de la pesca de todo el país"),
    "1123": ("nacional", False, False, "decision_L6_HA3",
             "Escuela Nacional de Marina Mercante (Callao): forma oficiales de la marina mercante de todo el país"),
    "1273": ("nacional", False, False, "decision_L6_HA3",
             "SUNAT-Aduanas con meta 07: despacho aduanero y control del contrabando en el puerto y el aeropuerto del "
             "Callao, que sirven a todo el comercio exterior del país"),
    "200": ("callao", True, False, "decision_L6_HA3",
            "Fiscalías del Callao (meta 07; la ejecutora tiene sede en Lima): servicio en el Callao. Mixta (decisión del "
            "7/10 sobre fiscalías): cuenta en el Callao con advertencia"),
    "26": ("callao", True, False, "decision_L6_HA3",
           "Policía del Callao (patrullaje y operaciones con meta 07): servicio en el Callao. Mixta (PNP, decisión del "
           "7/10): cuenta en el Callao con advertencia. La aviación policial con base en el Callao (servicios del "
           "transporte aéreo 5001193 y soporte aéreo TID 5004067: 34,1 / 36,9 / 39,2 M) se separa como nacional "
           "(actividades_nacionales; auditoría de P3)"),
    "12": ("callao", True, True, "decision_L6_HA3",
           "Procesos judiciales de las cortes superiores con meta 07: mixta provisional con verificar_procedencia "
           "(H-A3); cuenta en el Callao con advertencia"),
    "107": ("callao", False, True, "decision_L6_HA3",
            "L6: la Universidad Nacional del Callao cuenta en el Callao; verificar_procedencia (auditoría de P3: sin dato "
            "de residencia de los alumnos, criterio del 7/10)"),
    "1467": ("callao", False, False, "decision_L6_HA3", "Corte Superior de Justicia del Callao (H-A3: alcance callao)"),
    # --- implementador (revisado_dueno: false)
    "1588": ("nacional", False, False, "p3_implementador",
             "SANIPES, sede en el Callao (070106): autoridad nacional de sanidad pesquera de todo el país; mismo "
             "criterio que IMARPE"),
    "194": ("nacional", False, False, "p3_implementador",
            "ITP: sede institucional en el Callao (Carretera a Ventanilla km 5,2); conduce la red nacional de CITE"),
    "1520": ("nacional", False, False, "p3_implementador",
             "Migraciones con meta 07: control migratorio del aeropuerto internacional Jorge Chávez y del puerto del "
             "Callao (frontera nacional), no un servicio a residentes del Callao"),
    "42": ("nacional", False, False, "p3_implementador",
           "Aviación Policial con meta 07: operación y mantenimiento de aeronaves en su base del Callao, que operan en "
           "todo el país (interdicción, emergencias)"),
    "1072": ("nacional", False, True, "p3_implementador",
             "MTC-Administración General con meta 07: supervisión de obras y concesiones aeroportuarias (aeropuerto "
             "Jorge Chávez), función nacional; el proyecto 2045273 no está en el detalle de inversiones: verificar"),
    "470": ("nacional", False, False, "p3_implementador",
            "Ejército con meta 07: defensa nacional sin servicio directo a residentes (efectivo militar, capacidad "
            "operativa, puestos de vigilancia); mismo criterio que la Marina"),
    "472": ("nacional", False, False, "p3_implementador",
            "Fuerza Aérea con meta 07: defensa nacional sin servicio directo a residentes; mismo criterio que la Marina"),
    "1343": ("nacional", False, True, "p3_implementador",
             "DIREJANDRO con meta 07: operaciones antidrogas en el puerto y el aeropuerto (función nacional); verificar"),
    "157": ("callao", True, False, "p3_implementador",
            "SENASA con meta 07: control de plagas y de enfermedades animales en el Callao (servicio local) junto con el "
            "control de importaciones en puerto y aeropuerto (función nacional): mixta, cuenta con advertencia"),
    "1345": ("callao", False, False, "p3_implementador",
             "CENARES: vacunas y bienes entregados al Callao (la meta 07 es el destino); se mantiene, rotulado (analista "
             "y auditor de Lima en tres ámbitos)"),
    "1078": ("callao", False, False, "p3_implementador",
             "Provías Nacional: mantenimiento de la red vial nacional en el Callao, infraestructura que usan sus residentes"),
    "1717": ("lima_callao", False, False, "p3_auditor",
             "ATU: con meta 07 es «gestión del programa» (incluye planilla), no un servicio exclusivo del Callao; el "
             "mismo trato que con meta 15: Lima y Callao sin separar (no asignable; auditoría de P3, H-P3-3)"),
    # --- auditoría de P3 (H-P3-4): sin servicio directo a la población → nacional (criterio del 7/10)
    "196": ("nacional", False, False, "p3_auditor",
            "Contraloría con meta 07: control de entidades públicas del Callao, sin servicio directo a la población "
            "(criterio del 7/10; con meta 15 ya es nacional)"),
    "1698": ("nacional", False, False, "p3_auditor",
             "Contraloría-Gestión de Proyectos con meta 07: sin servicio directo a la población (criterio del 7/10)"),
    "1745": ("nacional", False, False, "p3_auditor",
             "Autoridad Nacional de Control del Ministerio Público con meta 07: control interno, sin servicio directo"),
    "1267": ("nacional", False, False, "p3_auditor",
             "SUNASS con meta 07: regulación de servicios de saneamiento, sin servicio directo a la población"),
    "18": ("callao", False, False, "p3_implementador", "INPE Oficina Regional Lima con meta 07: penales del Callao"),
    "33": ("callao", False, False, "p3_implementador", "VII DIRTEPOL Lima con meta 07: comisarías y operaciones en el Callao"),
}
REGLA = ("callao", False, False, "regla_sede_fuera_del_07",
         "Sede de la ejecutora fuera del Callao y presta servicio directo a la población: la meta 07 es servicio "
         "prestado en el Callao (sin sesgo de sede)")
# Separación por actividad de una mixta (auditoría de P3): actividades con meta 07 que son nacionales aunque la ejecutora
# cuente en el Callao. DIREFIN: aviación policial con base en el Callao, la misma función que Aviación Policial (42)
ACTIVIDADES_NACIONALES = {"26": ["5001193", "5004067"]}   # servicios del transporte aéreo; soporte aéreo TID

# Obras del GN en el 07 de sede o de función nacional (cui: (sec_ejec, criterio, motivo)) — salen de la cifra del Callao
OBRAS = {
    "2627351": ("1520", "funcion_nacional", "Migraciones: control migratorio del aeropuerto internacional Jorge Chávez "
                                            "(frontera nacional)"),
    "2578287": ("42", "funcion_nacional", "Aviación Policial: reparación de aeronaves en la División de Mantenimiento "
                                          "Aéreo del Callao (flota que opera en todo el país)"),
    "2392678": ("1340", "sede_institucional", "SUNAT: sede institucional de Aduanas (Chucuito)"),
    "2468685": ("1340", "funcion_nacional", "SUNAT: Intendencia de Aduana Aérea y Postal (aeropuerto Jorge Chávez)"),
    "2474628": ("193", "sede_institucional", "IMARPE: sede central (ciencia y tecnología del mar de todo el país)"),
    "2525078": ("193", "instituto_nacional", "IMARPE: centro de investigación científica de su sede en el Callao"),
    "2266632": ("1588", "instituto_nacional", "SANIPES: laboratorios de referencia nacional"),
    "2194402": ("194", "instituto_nacional", "ITP: investigación en biotecnología en su sede del Callao"),
    "2607237": ("194", "sede_institucional", "ITP: sede del Callao (protección contra incendios y videovigilancia)"),
    "2700599": ("1205", "sede_institucional", "APN: Dirección Técnica de la Autoridad Portuaria Nacional"),
    "2665187": ("1558", "funcion_nacional", "PNP: División de Seguridad Aeroportuaria, Fluvial y Lacustre (unidad nacional)"),
    "2454827": ("192", "sede_institucional", "FONDEPES: archivo general de la entidad"),
}
# Se quedan en la cifra del Callao con rótulo (auditoría de P3; el rótulo va en el aviso de v_gasto_por_ambito)
ROTULO = {
    "2473375": "Vía Expresa Santa Rosa (ruta PE-20I): obra vial nacional, acceso al aeropuerto; cuenta donde está, como "
               "la red vial nacional en todo el país",
    "2407158": "SUAT PNP «en Lima Metropolitana y el Callao»: sirve a los dos ámbitos; el mecanismo de obras no tiene línea "
               "Lima y Callao sin separar",
}
# Dudosas: quedan en la cifra del Callao (fuera de la lista) hasta el visto del dueño
REVISAR = {
    "2145423": "SUNAT: centro de servicio al contribuyente (local) y de control y fiscalización (nacional) en el Callao",
}

# ---------------- 1) salida de E3 sin cambios
with tempfile.TemporaryDirectory() as td:
    ya, yo = Path(td) / "a.yaml", Path(td) / "o.yaml"
    subprocess.run([sys.executable, str(E3 / "generar_yaml_e3.py"), str(RAIZ), "--salida", str(ya)], check=True,
                   capture_output=True)
    subprocess.run([sys.executable, str(E3 / "generar_obras_sede.py"), str(RAIZ), "--salida", str(yo)], check=True,
                   capture_output=True)
    txt_a, txt_o = ya.read_text(encoding="utf-8"), yo.read_text(encoding="utf-8")


def cabecera(txt):
    lineas = txt.splitlines(keepends=True)
    n = next(i for i, x in enumerate(lineas) if not x.startswith("#"))
    return "".join(lineas[:n])


alc = yaml.safe_load(txt_a)
obr = yaml.safe_load(txt_o)
with open(AQUI / "ejecutoras_meta07.csv", encoding="utf-8") as f:
    m07 = list(csv.DictReader(f))
with open(AQUI / "obras_gn_callao.csv", encoding="utf-8") as f:
    obras_csv = {(r["cui"], r["sec_ejec"]): r for r in csv.DictReader(f)}
assert len(m07) == 67 and set(DECISIONES) <= {r["sec_ejec"] for r in m07}

# ---------------- 2) bloque alcance_callao
por_sec = {e["sec_ejec"]: e for e in alc}
for r in m07:
    s = r["sec_ejec"]
    a, mixta, verif, paso, crit = DECISIONES.get(s, REGLA)
    bloque = {"alcance": a, "mixta": mixta, "verificar_procedencia": verif, "criterio": crit, "paso": paso,
              "decision": D_L6 if paso == "decision_L6_HA3" else None, "revisado_dueno": paso == "decision_L6_HA3",
              "devengado_meta07_2023_2025_millones": float(r["d2023_2025"])}
    if s in ACTIVIDADES_NACIONALES:
        bloque["actividades_nacionales"] = ACTIVIDADES_NACIONALES[s]
    if s not in por_sec:
        e = {"sec_ejec": s, "nombre": r["ejecutora"], "pliego": r["pliego"], "alcance": "nacional",
             "referencia_nacional": False, "verificar_procedencia": False, "mixta": False,
             "criterio": "Sin gasto con meta 15 (P3): el alcance de la meta 15 no se aplica; ver alcance_callao",
             "base_alcance": {"paso": "agregada_p3_sin_meta_lima", "L_pct": None, "L_metrica": None, "L_fuente": None,
                              "pct_atencion_directa": None, "confianza": "alta", "decision": None},
             "devengado_meta15_2023_2025_millones": 0.0, "revisado_dueno": False}
        alc.append(e)
        por_sec[s] = e
    por_sec[s]["alcance_callao"] = bloque
nuevas = [e for e in alc if e["base_alcance"]["paso"] == "agregada_p3_sin_meta_lima"]
assert {e["sec_ejec"] for e in nuevas} == {"1467", "480", "479"}

CAB_A = cabecera(txt_a) + """# v4 (P3 – Lima en tres ámbitos; decisión L6 del dueño del 9/10/2026, 03_auditoria/lima_tres_ambitos/): UN solo
# mecanismo de sesgo de sede para los dpto 15 y 07. El alcance se decide por (ejecutora, departamento de la meta):
# `alcance` para la meta 15 (GA-01) y el bloque `alcance_callao` para la meta 07 (alcance: nacional | callao; mixta;
# verificar_procedencia; criterio; paso; decision; revisado_dueno). Con meta 07, `nacional` sale de la cifra del Callao;
# `callao` cuenta en ella (con advertencia si mixta). En la fact: cuenta_en_ambito (15 y 07); cuenta_en_lima es su alias
# en el 15. Pasos del bloque: decision_L6_HA3 (L6 + corrección H-A3 del auditor; revisado_dueno: true),
# p3_implementador, p3_auditor y regla_sede_fuera_del_07 (revisado_dueno: false). alcance_callao lima_callao (ATU): Lima y
# Callao sin separar; actividades_nacionales: actividades con meta 07 que son nacionales dentro de una mixta (DIREFIN). Se agregan 3 ejecutoras sin meta 15 (paso
# agregada_p3_sin_meta_lima). Generado por curados/generadores/p3_gasto/generar_p3.py.
"""
SAL_ALC.write_text(CAB_A + yaml.safe_dump(alc, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")

# ---------------- 3) obras de sede o función nacional en el Callao
ya_en = {(o["cui"], o["sec_ejec"]) for o in obr["obras"]}
for cui, (sec, crit, mot) in OBRAS.items():
    r = obras_csv[(cui, sec)]
    assert (cui, sec) not in ya_en and r["ubigeo"].startswith("07"), cui
    obr["obras"].append({"cui": cui, "sec_ejec": sec, "ejecutora": r["ejecutora"], "nombre_inversion": r["nombre_inversion"],
                         "criterio": crit, "motivo": mot, "revision": "revision_manual", "origen": "callao_p3",
                         "departamento": "07", "devengado_2023_2025_millones": float(r["d2023_2025"])})
assert not (set(REVISAR) | set(ROTULO)) & set(OBRAS)
obr["version"] = "1.2.0"
CAB_O = cabecera(txt_o) + """# v1.2.0 (P3 – Lima en tres ámbitos, L6 del 9/10/2026): la marca se aplica también a obras del nivel E atribuidas por
# CUI al departamento 07 (sale de la cifra del Callao: cuenta_en_ambito = false). Se agregan 12 obras del Callao
# (origen callao_p3, departamento '07'), revisables por el dueño; las dudosas quedan fuera y figuran como «revisar» en
# curados/generadores/p3_gasto/obras_callao_revision.csv. Generado por generar_p3.py (esa carpeta).
"""
SAL_OBR.write_text(CAB_O + yaml.safe_dump(obr, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")

# ---------------- 4) revisión: todas las obras del GN en el 07 con su decisión
with open(AQUI / "obras_callao_revision.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["cui", "sec_ejec", "ejecutora", "devengado_2023_2025_millones", "decision", "criterio", "motivo",
                "nombre_inversion"])
    for (cui, sec), r in obras_csv.items():
        if cui in OBRAS and OBRAS[cui][0] == sec:
            dec, crit, mot = "sale", OBRAS[cui][1], OBRAS[cui][2]
        elif cui in ROTULO:
            dec, crit, mot = "queda_con_rotulo", "", ROTULO[cui]
        elif cui in REVISAR:
            dec, crit, mot = "revisar", "", REVISAR[cui]
        else:
            dec, crit, mot = "queda", "", "servicio en el Callao (colegio, hospital, agua, vía, comisaría, universidad...)"
        w.writerow([cui, sec, r["ejecutora"], r["d2023_2025"], dec, crit, mot, r["nombre_inversion"][:160]])
print(len(alc), "entradas;", sum("alcance_callao" in e for e in alc), "con alcance_callao;",
      sum(e.get("alcance_callao", {}).get("alcance") == "nacional" for e in alc), "nacionales en el 07;",
      len(obr["obras"]), "obras")
