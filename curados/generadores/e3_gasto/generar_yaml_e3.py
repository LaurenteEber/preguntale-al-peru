"""E3 – gasto (decisiones del dueño del 8/10/2026, docs/decisiones.md): genera
curados/capa0/ejecutoras_alcance.yaml v3 a partir de la v2 (salida de la pieza A, copiada sin cambios en
ejecutoras_alcance_v2_antes.yaml de esta carpeta). Reproducible e idempotente: siempre parte de esa copia.

Uso (desde la raíz del repositorio): uv run --frozen python <esta carpeta>/generar_yaml_e3.py <raiz> [--salida ruta]

Cambios:
  1. Las 166 ejecutoras sin decisión individual (paso no_evaluado_criterio_unico) se confirman en bloque:
     revisado_dueno: true y base_alcance.decision con la decisión del 8/10.
  2. INPE Sede Central (17), Administración Central del MINSA (117) y DIREICAJ PNP (1312): siguen nacionales y se
     marcan mixta: true (paso mixta).
  3. COAR Lima (1418) y CENFOTUR (162): lima_metropolitana + verificar_procedencia: true.
  4. INPE Oficina Regional Lima (18): lima_departamento (alcance nuevo de gasto.py: cuenta en Lima, sin ámbito; su
     gasto con meta 15 se atribuye al ubigeo 150000, la línea «Lima sin separar»).
  5. (auditoría de E3, H3) Las 20 ejecutoras del GN con obras en Lima y sin gasto con meta 15 (ejecutoras_fuera_del_yaml.csv)
     se agregan con alcance declarado por el implementador (revisado_dueno: false): nacional, salvo SUNARP Zona IX (1269),
     lima_callao. No cambia ninguna cifra (sin meta 15 no hay fila de la fact con alcance); declara a qué ejecutora siguen
     sus obras de obras_sede_nacional.yaml.
  (H6) Se conserva base_alcance.veredicto_ronda1; COAR Lima y CENFOTUR pasan a confianza media (sin dato de procedencia).
"""
import csv
import sys
from pathlib import Path

import yaml

RAIZ = Path(sys.argv[1])
AQUI = Path(__file__).resolve().parent
SALIDA = Path(sys.argv[sys.argv.index("--salida") + 1]) if "--salida" in sys.argv else \
    RAIZ / "curados/capa0/ejecutoras_alcance.yaml"
V2 = AQUI / "ejecutoras_alcance_v2_antes.yaml"
FUENTE = "00_proyecto/analisis_2026-10-08/gasto/informe.md"
D_BLOQUE = ("Dueño, 8/10/2026: se confirma en bloque el alcance de GA-01 (decisiones.md; análisis " + FUENTE + " §1)")
MIXTAS_NUEVAS = {
    "17": "Paga la planilla de todos los penales del país (95 % de su gasto es personal; las 8 oficinas regionales casi "
          "no pagan personal), incluidos los de Lima Metropolitana: nacional con advertencia, como la planilla PNP",
    "117": "2 896,6 M (2023-2025) de personal en «Preparación y perfeccionamiento de recursos humanos» (RO); la hipótesis "
           "de residentes o SERUMS en hospitales de Lima no es comprobable con la fact (auditoría del 8/10, H6): "
           "nacional con advertencia; pedir al MINSA la distribución por sede",
    "1312": "Investigación criminal (DIRINCRI), laboratorio y operativos con el 98 % de su meta en Lima: nacional con "
            "advertencia, como la PNP",
}
A_LIMA_VERIFICAR = {
    "1418": "COAR Lima (sede en Chosica): recibe postulantes de Lima y de regiones vecinas; mismo criterio que las "
            "escuelas de arte (lima_metropolitana con verificar_procedencia)",
    "162": "CENFOTUR: escuela de turismo con el 78,5 % de su gasto en Lima; mismo criterio que las escuelas de arte",
}
INPE_ORL = "18"
D_IND = "Dueño, 8/10/2026: decisión individual (decisiones.md; análisis " + FUENTE + " §1 y §5)"

v2 = yaml.safe_load(V2.read_text(encoding="utf-8"))
salida, n_bloque = [], 0
for e in v2:
    e = {**e, "base_alcance": dict(e["base_alcance"])}
    s, b = e["sec_ejec"], e["base_alcance"]
    if s in MIXTAS_NUEVAS:
        assert e["alcance"] == "nacional" and not e["mixta"] and b["paso"] == "no_evaluado_criterio_unico", s
        e["mixta"] = True
        e["criterio"] = f"Ejecutora mixta (sede nacional y servicio en Lima): {MIXTAS_NUEVAS[s]}"
        b.update(paso="mixta", decision=D_IND + ": nacional y mixta; se separa por producto después del piloto y las "
                                                "cifras de Lima llevan advertencia")
        e["revisado_dueno"] = True
    elif s in A_LIMA_VERIFICAR:
        assert e["alcance"] == "nacional" and b["paso"] == "no_evaluado_criterio_unico", s
        e.update(alcance="lima_metropolitana", verificar_procedencia=True,
                 criterio=f"Lima Metropolitana sin dato de procedencia: {A_LIMA_VERIFICAR[s]}")
        b.update(paso="decision_dueno_8_10", alcance_anterior="nacional", confianza="media",
                 decision=D_IND + ": lima_metropolitana con verificar_procedencia")
        e["revisado_dueno"] = True
    elif s == INPE_ORL:
        assert e["alcance"] == "lima_metropolitana" and e["revisado_dueno"], s
        e.update(alcance="lima_departamento",
                 criterio="16 penales: 8 de Lima Metropolitana, 3 de Lima Provincias (Cañete, Huacho, Huaral), 1 del "
                          "Callao, 2 de Ica y 2 de Áncash (Directorio de Establecimientos Penitenciarios del INPE). El "
                          "gasto con meta 15 cuenta en Lima en la línea «Lima sin separar» (ubigeo 150000, sin ámbito); "
                          "el de Ica, Áncash y Callao ya va a esos departamentos. Prorrateo por internos: pendiente")
        b.update(paso="decision_dueno_8_10", alcance_anterior="lima_metropolitana",
                 decision=D_IND + ": lima_departamento (opción B)",
                 L_fuente="https://cdn.www.gob.pe/uploads/document/file/965548/Directorio_de_Establecimientos_Penitenciarios_a_Nivel_Nacional.pdf")
    elif b["paso"] == "no_evaluado_criterio_unico":
        assert not e["revisado_dueno"] and b["decision"] is None, s
        b.update(paso="confirmado_en_bloque_8_10", decision=D_BLOQUE)
        e["revisado_dueno"] = True
        n_bloque += 1
    salida.append(e)

assert n_bloque == 166, n_bloque
assert all(e["revisado_dueno"] for e in salida)
# 5. ejecutoras fuera del YAML (sin meta 15): alcance declarado, sin decisión del dueño
ZONA_IX = {"1269": ("lima_callao", "SUNARP Zona Registral IX (sede Lima): Lima Metropolitana, Lima Provincias y Callao",
                    "media")}
ya = {e["sec_ejec"] for e in salida}
with open(AQUI / "ejecutoras_fuera_del_yaml.csv", encoding="utf-8") as f:
    fuera = sorted(csv.DictReader(f), key=lambda r: int(r["sec_ejec"]))
assert len(fuera) == 20 and not ya & {r["sec_ejec"] for r in fuera}
for r in fuera:
    alc, crit, conf = ZONA_IX.get(r["sec_ejec"], ("nacional", "Sede central, programa u organismo de alcance nacional "
                                                  "sin gasto con meta en Lima; solo sus obras por CUI caen en Lima", "alta"))
    salida.append({"sec_ejec": r["sec_ejec"], "nombre": r["nombre"], "pliego": r["pliego"], "alcance": alc,
                   "referencia_nacional": False, "verificar_procedencia": False, "mixta": False, "criterio": crit,
                   "base_alcance": {"paso": "agregada_e3_sin_meta_lima", "L_pct": None, "L_metrica": None,
                                    "L_fuente": None, "pct_atencion_directa": None, "confianza": conf,
                                    "decision": None},
                   "devengado_meta15_2023_2025_millones": float(r["devengado_meta15_2023_2025_millones"]),
                   "revisado_dueno": False})
CAB = """# Alcance de las unidades ejecutoras del Gobierno Nacional con meta en el departamento de Lima (15) — GA-01, v3.
# GA-01 (dueño, 6/10/2026): se MARCA el alcance; la atribución (departamento_meta) no cambia.
# Cifras de Lima (departamento, Lima Metropolitana, Lima Región): SOLO las filas de fact_gasto_territorial con
# cuenta_en_lima = true (dpto 15, sin alcance nacional, sin referencia_nacional —incluidas sus obras— y sin las obras de
# sede o función nacional de curados/capa0/obras_sede_nacional.yaml).
# Línea aparte: referencia_nacional AND departamento_atribucion = '15'.
# alcance: nacional | lima_metropolitana | lima_region | lima_callao | lima_departamento. Las UE lima_* pasan a su ámbito
# (A-LIMA_METROPOLITANA / A-LIMA_REGION / A-AREA_METROPOLITANA_LIMA_CALLAO); lima_departamento no tiene ámbito: su gasto
# con meta 15 se atribuye al departamento (150000, línea «Lima sin separar») y cuenta en Lima. Solo se graba con
# departamento_meta = 15.
#
# v2 (pieza A de las rondas 1-2; decisiones del dueño del 7/10/2026): criterio único (ronda 2 §3.3): sin servicio
# directo → nacional; L = % de pacientes nuevos o atendidos que residen en el departamento de Lima: L ≥ 60 % → Lima;
# L ≤ 40 % → nacional; 40-60 % → nacional solo si es rector/red nacional o solo recibe referidos; sin dato →
# verificar_procedencia: true. Campos (los lee gasto.py y los propaga a dim_unidad_ejecutora y a la fact):
#   referencia_nacional: centro nacional de referencia ubicado en Lima (INEN, INSN San Borja). Su gasto, incluidas sus
#       obras, sale de la cifra de Lima y se muestra como línea aparte. Exige alcance: nacional.
#   verificar_procedencia: el alcance se decidió sin dato (o con dato débil) de procedencia; pedirlo.
#   mixta: sede nacional y servicio en Lima a la vez; se separan por producto después del piloto; mientras tanto las
#       cifras de Lima llevan advertencia (obligatoria en seguridad, protección social, justicia, transporte y salud).
#   base_alcance: paso del criterio, L (%), métrica, fuente (URL), % de atención directa, confianza y decisión.
#   revisado_dueno: true si el dueño decidió la entrada.
# v3 (E3 – gasto; decisiones del dueño del 8/10/2026): las 166 entradas sin decisión individual se confirman en bloque
# (paso confirmado_en_bloque_8_10); INPE Sede Central, Administración Central del MINSA y DIREICAJ PNP → mixta (25 en
# total); COAR Lima y CENFOTUR → lima_metropolitana con verificar_procedencia; INPE Oficina Regional Lima →
# lima_departamento. Las 231 quedan con revisado_dueno: true (las mixtas, con alcance provisional). Se agregan 20
# ejecutoras sin gasto con meta 15 cuyas obras están en Lima (auditoría de E3, H3; paso agregada_e3_sin_meta_lima,
# revisado_dueno: false): declaran a qué alcance siguen sus obras en obras_sede_nacional.yaml.
# Generado por curados/generadores/e3_gasto/generar_yaml_e3.py a partir de la v2
# (03_auditoria/ola0/decisiones_gasto/implementacion/pieza_a/generar_yaml.py). No editar a mano sin actualizar esos
# scripts; el de la pieza A no debe volver a correrse sobre la v3.
"""
SALIDA.write_text(CAB + yaml.safe_dump(salida, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
print(len(salida), "entradas;", sum(e["revisado_dueno"] for e in salida), "revisadas;", n_bloque, "confirmadas en bloque;", sum(e["mixta"] for e in salida), "mixtas;",
      sum(e["verificar_procedencia"] for e in salida), "con verificar_procedencia")
