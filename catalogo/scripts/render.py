"""Genera catalogo_fuentes.{json,csv,md}, priorizacion.md y auditoria_estado.csv a partir de catalogo_fuentes_v2.json."""
import json, csv, collections, os, re, shutil
import prioriza_v2 as PZ
from test_catalogo import CAMPOS
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, 'catalogo'); OUT_PRI = os.path.join(ROOT, 'catalogo', 'salidas'); OUT_AUD = os.path.join(ROOT, 'catalogo', 'salidas', 'auditoria')
d = json.load(open(os.path.join(HERE, 'catalogo_fuentes_v2.json')))
nf = json.load(open(os.path.join(HERE, 'nuevas_fuentes.json')))
FECHA = '8 de octubre de 2026'

TEMA = collections.OrderedDict([
 ('presupuesto_finanzas_publicas', 'Presupuesto y finanzas públicas'), ('inversion_publica', 'Inversión pública'), ('contrataciones_publicas', 'Contrataciones públicas'),
 ('pobreza_condiciones_vida', 'Pobreza y condiciones de vida'), ('salud', 'Salud'), ('nutricion_anemia', 'Nutrición y anemia'), ('educacion', 'Educación'),
 ('empleo_ingresos', 'Empleo e ingresos'), ('programas_sociales', 'Programas sociales'), ('poblacion_demografia', 'Población y demografía'),
 ('vivienda_servicios_basicos', 'Vivienda y servicios básicos'), ('agricultura_desarrollo_rural', 'Agricultura y desarrollo rural'),
 ('ambiente_recursos_naturales', 'Ambiente y recursos naturales'), ('riesgo_desastres_clima', 'Riesgo de desastres y clima'),
 ('seguridad_ciudadana_justicia', 'Seguridad ciudadana y justicia'), ('genero_violencia', 'Género y violencia'),
 ('gobernanza_transparencia_corrupcion', 'Gobernanza, transparencia y corrupción'), ('elecciones_participacion', 'Elecciones y participación'),
 ('conflictos_sociales', 'Conflictos sociales'), ('pueblos_indigenas_cultura', 'Pueblos indígenas y cultura'), ('economia_empresas_produccion', 'Economía, empresas y producción'),
 ('mineria_energia_hidrocarburos', 'Minería, energía e hidrocarburos'), ('transporte_infraestructura', 'Transporte e infraestructura'),
 ('territorio_cartografia', 'Territorio y cartografía'), ('inclusion_financiera', 'Inclusión financiera'), ('ciencia_tecnologia_digital', 'Ciencia, tecnología y digital'),
 ('turismo', 'Turismo'), ('identidad_migracion', 'Identidad y migración'), ('multitematica', 'Multitemática y catálogos')])
OLA = collections.OrderedDict([('0_base', '0 · Base'), ('1_nucleo', '1 · Núcleo'), ('2_expansion', '2 · Expansión'), ('3_complementaria', '3 · Complementaria'),
 ('referencia', 'Referencia'), ('ruta_alterna', 'Ruta alterna'), ('infraestructura_acceso', 'Infraestructura de acceso'), ('fuera_de_alcance', 'Fuera de alcance')])
DATOS = {'descarga_ok': '✅', 'enlace_confirmado': '🔗', 'descarga_falla': '❌', 'sin_descarga_publica': '🔒', 'sin_probar': '·'}

def c(v):
    if v in (None, '', []): return '—'
    if isinstance(v, bool): v = 'sí' if v else 'no'
    if isinstance(v, list): v = ', '.join(map(str, v))
    return str(v).replace('|', '\\|').replace('\n', ' ')
def lk(r):
    u = r.get('url_portal') or r.get('url_datos')
    return f"[{c(r['nombre'])}]({u})" if u else c(r['nombre'])
def terr(r):
    t = c(r.get('nivel_territorial_disponible'))
    if r.get('nivel_territorial_inferencia') and r['nivel_territorial_inferencia'] != r.get('nivel_territorial_disponible'): t += f" / **{r['nivel_territorial_inferencia']}**"
    return t
def anios(r):
    a0, a1 = r.get('anio_inicio'), r.get('anio_fin')
    return f'{a0}–{a1}' if a0 and a1 and a0 != a1 else str(a1 or a0 or '—')

orden_t = list(TEMA); orden_o = list(OLA)
d.sort(key=lambda r: (orden_t.index(r['tematica_principal']) if r['tematica_principal'] in orden_t else 99, orden_o.index(r['ola']), -r['puntaje_prioridad'], r['id']))

# ---------------- JSON / CSV ----------------
json.dump(d, open(os.path.join(OUT, 'catalogo_fuentes.json'), 'w'), ensure_ascii=False, indent=1)
with open(os.path.join(OUT, 'catalogo_fuentes.csv'), 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=CAMPOS + ['correcciones']); w.writeheader()
    for r in d:
        row = {k: ('; '.join(map(str, r[k])) if isinstance(r.get(k), list) else r.get(k)) for k in CAMPOS}
        row['correcciones'] = ' / '.join(f"{','.join(x['hallazgos'])} ({x['validacion']})" for x in r.get('correcciones', []))
        w.writerow(row)

# tabla curada de inferencia (fuente: catalogo/scripts/inferencia_verificada.csv; la valida test_catalogo.py)
shutil.copyfile(os.path.join(HERE, 'inferencia_verificada.csv'), os.path.join(OUT, 'inferencia_verificada.csv'))

# ---------------- catálogo MD ----------------
N = len(d); cnt = lambda k: collections.Counter(r.get(k) for r in d)
L = []; A = L.append
A('# Catálogo de fuentes de datos — Pregunta al Perú\n')
ep, ed = cnt('estado_portal'), cnt('estado_datos')
A(f'Versión 2.0 · {FECHA} · **{N} fuentes** · esquema v2 (`esquema_registro.md`) · corregido tras la auditoría (`03_auditoria/auditoria.md`, `03_auditoria/auditoria_estado.csv`).\n')
A(f'**Verificación de enlaces:** {ep["confirmado_navegador"]} abiertos en navegador, {ep["confirmado_busqueda"]} confirmados por búsqueda, {ep["no_responde"]} no responden. '
  f'**Prueba de humo de datos:** {ed["descarga_ok"]} con muestra descargada ✅, {ed["enlace_confirmado"]} con enlace confirmado 🔗, {ed["descarga_falla"]} fallidos ❌, {ed["sin_descarga_publica"]} sin descarga pública 🔒, {ed["sin_probar"]} sin probar.\n')
A('Los mismos registros están en `catalogo_fuentes.csv` y `catalogo_fuentes.json` (fuente de verdad). Cada registro guarda en `correcciones` el hallazgo de auditoría que lo modificó y cómo se validó. `estado_ingesta` y `evidencia_ingesta` (solo JSON: capturas, huellas y fecha) dicen si la fuente tiene captura completa verificada. La representatividad verificada de las encuestas por año y módulo (R-ENC-08) está en `inferencia_verificada.csv`, con la cita de la ficha técnica.\n')
A('## Resumen\n')
A('| Temática | Fuentes | Ola 0 | Ola 1 | Ola 2 |'); A('|---|---:|---:|---:|---:|')
by = collections.OrderedDict()
for r in d: by.setdefault(r['tematica_principal'], []).append(r)
for k, rs in by.items():
    cc = collections.Counter(r['ola'] for r in rs)
    A(f"| [{TEMA.get(k, k)}](#{re.sub(r'[^a-z0-9áéíóúñ -]', '', TEMA.get(k, k).lower()).replace(' ', '-')}) | {len(rs)} | {cc['0_base']} | {cc['1_nucleo']} | {cc['2_expansion']} |")
A('')
A('**Por ola:** ' + ' · '.join(f'{OLA[k]} {v}' for k, v in sorted(cnt('ola').items(), key=lambda x: orden_o.index(x[0]))) + '\n')
A('## Índice por temática\n')
A('Territorio: nivel más fino publicado / **nivel con representatividad** (solo encuestas y estimaciones). Base: a qué lugar se refiere el ubigeo. Datos: ✅ muestra descargada · 🔗 enlace confirmado · ❌ falla · 🔒 sin descarga pública · · sin probar.\n')
for k, rs in by.items():
    A(f'### {TEMA.get(k, k)}\n')
    A('| ID | Fuente | Entidad | Naturaleza | Territorio | Base | Años | Descarga | Ola | Datos |'); A('|---|---|---|---|---|---|---|---|---|---|')
    for r in rs:
        A(f"| [`{r['id']}`](#{r['id'].lower()}) | {lk(r)} | {c(r.get('entidad'))} | {c(r['naturaleza_dato'])} | {terr(r)} | {c(r.get('base_geografica'))} | {anios(r)} | {c(r['estrategia_descarga'])} | {OLA[r['ola']]} | {DATOS.get(r['estado_datos'], '·')} |")
    A('')
A('## Fichas\n')
for k, rs in by.items():
    A(f'### {TEMA.get(k, k)} — fichas\n')
    for r in rs:
        A(f'<a id="{r["id"].lower()}"></a>'); A(f"#### {r['id']} — {r['nombre']}\n"); A(f"{c(r.get('descripcion'))}\n")
        A('| Campo | Valor |'); A('|---|---|')
        rows = [('Temáticas', c([r['tematica_principal']] + (r.get('tematicas_secundarias') or []))), ('Subtemas', c(r.get('subtemas'))),
                ('Entidad / unidad orgánica', f"{c(r.get('entidad'))} — {c(r.get('unidad_organica'))} ({c(r.get('sector'))})"),
                ('Naturaleza · acceso', f"{c(r['naturaleza_dato'])} · {c(r.get('tipo_acceso'))}"), ('Unidad de observación', c(r.get('unidad_observacion'))),
                ('Territorio', f"disponible: {c(r.get('nivel_territorial_disponible'))} · inferencia: {c(r.get('nivel_territorial_inferencia'))} · base geográfica: {c(r.get('base_geografica'))}"),
                ('Qué mide', c(r.get('tipo_medida'))), ('Desagregaciones', c(r.get('desagregaciones'))), ('Llaves de cruce', c(r.get('llaves_cruce'))),
                ('Periodo', f"{c(r.get('cobertura_temporal'))} · años {anios(r)} · último dato {c(r.get('fecha_ultimo_dato'))} · {c(r.get('periodicidad'))} · serie activa: {c(r.get('serie_activa'))}" + (' · proyección' if r.get('es_proyeccion') else '')),
                ('Quiebres', c(r.get('anios_con_quiebre'))), ('Formatos', c(r.get('formatos'))),
                ('Enlaces', ' · '.join(x for x in [f"[portal]({r['url_portal']})" if r.get('url_portal') else '', f"[datos]({r['url_datos']})" if r.get('url_datos') else '', f"patrón `{r['url_patron']}`" if r.get('url_patron') else '', f"[documentación]({r['url_documentacion']})" if r.get('url_documentacion') else ''] if x) or '—'),
                ('Descarga', f"**{c(r['estrategia_descarga'])}** — {c(r.get('detalle_descarga'))}"),
                ('Licencia', f"{c(r.get('licencia'))} ({c(r.get('licencia_texto'))}) · redistribución: {c(r.get('permite_redistribucion'))} · registro: {c(r.get('requiere_registro'))}"),
                ('Limitaciones', c(r.get('limitaciones'))),
                ('Verificación', f"portal: {c(r.get('estado_portal'))} · datos: {DATOS.get(r['estado_datos'], '')} {c(r.get('estado_datos'))} · fecha: {c(r.get('fecha_verificacion'))}"),
                ('Priorización', f"**{OLA[r['ola']]}** · origen {c(r['origen'])} · capa {c(r['capa'])} · puntaje {r['puntaje_prioridad']}" + (f" · compuerta {r['compuerta_ingesta']}" if r.get('compuerta_ingesta') else '') + (f" por {r['base_aprobacion']}" if r.get('base_aprobacion') else '') + (f" ({r['estado_ingesta']}, {r['fecha_verificacion']})" if r.get('estado_ingesta') else '') + f" — {c(r['motivo_ola'])}"),
                ('Trazabilidad', ' / '.join(f"{','.join(x['hallazgos'])} ({x['validacion']})" for x in r.get('correcciones', [])) or '—'),
                ('Notas', c(r.get('notas')))]
        if r.get('id_ruta_principal'): rows.insert(-1, ('Ruta principal', f"`{r['id_ruta_principal']}`"))
        if r.get('ids_fusionados'): rows.insert(-1, ('Registros fusionados', c(r['ids_fusionados'])))
        for a, b in rows: A(f'| {a} | {b} |')
        A('')
open(os.path.join(OUT, 'catalogo_fuentes.md'), 'w').write('\n'.join(L))

# ---------------- priorización MD ----------------
ids = {r['id'] for r in d}
def nr(r): return r.get('estado_portal') == 'no_responde' or r.get('estado_datos') in ('sin_descarga_publica', 'descarga_falla')
resto = [r for r in d if r['ola'] not in ('ruta_alterna', '0_base', 'infraestructura_acceso')]
f1 = [r for r in resto if r['origen'] == 'primaria']
f2 = [r for r in f1 if r['capa'] in ('nucleo_social', 'gasto_publico')]
f3 = [r for r in f2 if not nr(r) and r.get('estrategia_descarga') not in ('solicitud_acceso_informacion', 'convenio')]
f4 = [r for r in f3 if r.get('anio_fin') and PZ.vigente(r)]
f5 = [r for r in f4 if PZ.cruz_fac(r)[0] >= 0.5]
f6 = [r for r in f5 if PZ.cruz_fac(r)[1] >= PZ.FAC_OLA1]
f7 = [r for r in f6 if r['capa'] == 'gasto_publico' or PZ.es_core(r)]
auto = {r['id'] for r in f7}; ola1 = {r['id'] for r in d if r['ola'] == '1_nucleo'}
bajadas = auto & set(PZ.SEGUNDA); excep = ola1 - auto
assert ola1 == (auto - bajadas) | excep, 'la aritmética del embudo no cierra'
O = collections.defaultdict(list)
for r in d: O[r['ola']].append(r)
for k in O: O[k].sort(key=lambda r: -r['puntaje_prioridad'])
L = []; A = L.append
A('# Priorización de fuentes v2: embudo para la biblioteca de datos curados\n')
A(f'Versión 2.0 · {FECHA} · {N} fuentes · corrige la v1 según la auditoría (temas A-01 a A-04, C-01, C-04 a C-06). Código: `prioriza_v2.py`; las cifras de este documento se calculan del JSON y se verifican al generarlo.\n')
A('## 1. Qué cambió frente a la v1\n')
A('''| Cambio | Hallazgo |
|---|---|
| La Ola 1 exige **API, URL estable o geoservicio**; lo manual entra solo como excepción indispensable | A-03 |
| La Ola 1 exige **vigencia**: último dato ≥ 2021 (salvo líneas de base); sin año confirmado va a la Ola 2 | A-02 |
| La regla de capa mira **siempre las temáticas secundarias**; los portales pasan a "infraestructura de acceso" | A-04 |
| El gasto MEF cuenta como cruzable solo hasta el nivel de su **base geográfica** (ejecutora → municipalidad o departamento) | C-01 |
| Duplicados MEF (devengado mensual, sectores) y HIS → **rutas alternas**; inversión de bajo valor marginal a la Ola 2 | A-01 |
| Fuentes que no existen como se describían salen de la Ola 1 (Padrón Nominal, HIS, CONTIGO, PpR, sectores) | C-04 |
| **Compuerta de ingesta**: cada fuente de las Olas 0 y 1 lleva el resultado de la prueba de humo | C-06 |
| Pesos del puntaje: relevancia 30 %, cruzabilidad 30 %, descarga 25 %, vigencia 15 % | EMB-18 |
''')
A('## 2. El embudo\n')
A('```')
for n, t in [(N, 'fuentes en el catálogo'), (len(O['ruta_alterna']), '→ rutas alternas (misma información por otra vía)'),
             (len(O['0_base']), '→ capa 0 · base de cruce (se construye primero)'), (len(O['infraestructura_acceso']), '→ infraestructura de acceso (portales y catálogos)'),
             (len(f1), '1. Origen primario oficial'), (len(f2), '2. Del foco social o del gasto asociado'), (len(f3), '3. Con descarga pública'),
             (len(f4), f'4. Vigentes (último dato ≥ {PZ.VIGENCIA_MIN})'), (len(f5), '5. Cruzables (llave territorial y nivel útil)'),
             (len(f6), '6. Descargables por API, URL estable o geoservicio'), (len(f7), '7. Del foco duro (salud, educación, pobreza, nutrición, programas sociales) o su gasto')]:
    A(f'{n:>4}  {t}')
A(f'{len(ola1):>4}  Ola 1 = {len(f7)} − {len(bajadas)} bajadas a la Ola 2 por revisión + {len(excep)} indispensables por excepción')
A('```\n')
A('| Ola | Fuentes | Qué es |'); A('|---|---:|---|')
for k, desc in [('0_base', 'Tablas de referencia, denominadores y puentes'), ('1_nucleo', 'Primera ingesta: foco duro y gasto asociado'),
                ('2_expansion', 'Foco ampliado, descarga manual o por tableros, sin descarga pública o sin vigencia confirmada'),
                ('3_complementaria', 'Primarias y cruzables de otros temas'), ('referencia', 'Cifras procesadas, secundarias y series cerradas: para validar y contexto'),
                ('ruta_alterna', 'Misma información que otra fuente preferida'), ('infraestructura_acceso', 'Portales por los que se descargan otras fuentes: se monitorean'),
                ('fuera_de_alcance', 'Otros temas sin dato primario cruzable')]:
    A(f'| {OLA[k]} | {len(O[k])} | {desc} |')
A('')
comp = collections.Counter(r['compuerta_ingesta'] for r in d if r.get('compuerta_ingesta'))
base = collections.Counter(r.get('base_aprobacion') for r in d if r.get('compuerta_ingesta') == 'aprobada')
A(f"**Compuerta de ingesta (Olas 0 y 1):** {comp['aprobada']} aprobadas ({base['captura_verificada']} por captura completa verificada y {base['humo']} solo por la muestra de la prueba de humo; columna `base_aprobacion`), {comp['enlace_confirmado']} con enlace confirmado sin descargar, {comp['pendiente_prueba']} pendientes, {comp['bloqueada']} bloqueadas. "
  'Ninguna fuente entra a la biblioteca hasta estar "aprobada".\n')
def tabla(rs, cols):
    A('| ' + ' | '.join(h for h, _ in cols) + ' |'); A('|' + '---|' * len(cols))
    for r in rs: A('| ' + ' | '.join(f(r) for _, f in cols) + ' |')
    A('')
idc = lambda r: f"`{r['id']}`"
A('## 3. Ola 0 · Base de cruce\n')
tabla(O['0_base'], [('ID', idc), ('Fuente', lk), ('Para qué', lambda r: c(PZ.BASE.get(r['id']))), ('Territorio', terr), ('Años', anios), ('Compuerta', lambda r: f"{DATOS.get(r['estado_datos'])} {r['compuerta_ingesta']}")])
A('## 4. Ola 1 · Núcleo\n')
def bloque(r):
    if r['capa'] == 'gasto_publico': return 'Gasto e inversión pública'
    t = r['tematica_principal']
    if t == 'nutricion_anemia' or r['id'] in ('MINSA-CNV-NACIDOS-VIVOS',): return 'Nutrición y primera infancia'
    if t == 'salud': return 'Salud'
    if t == 'educacion': return 'Educación'
    if t == 'programas_sociales': return 'Programas sociales'
    return 'Pobreza y condiciones de vida'
B = collections.OrderedDict((k, []) for k in ['Pobreza y condiciones de vida', 'Salud', 'Nutrición y primera infancia', 'Educación', 'Programas sociales', 'Gasto e inversión pública'])
for r in O['1_nucleo']: B[bloque(r)].append(r)
for k, rs in B.items():
    A(f'### {k} ({len(rs)})\n')
    tabla(rs, [('ID', idc), ('Fuente', lk), ('Territorio', terr), ('Base', lambda r: c(r.get('base_geografica'))), ('Llaves', lambda r: c(r.get('llaves_cruce'))),
               ('Años', anios), ('Compuerta', lambda r: f"{DATOS.get(r['estado_datos'])} {r['compuerta_ingesta']}"), ('Nota', lambda r: c(PZ.ESENCIAL.get(r['id'], '')) if r['id'] in PZ.ESENCIAL else '')])
A('## 5. Ola 2 · Expansión\n')
tabla(O['2_expansion'], [('ID', idc), ('Fuente', lk), ('Tema', lambda r: c(r['tematica_principal'])), ('Por qué no está en la Ola 1', lambda r: c(r['motivo_ola'])), ('Puntaje', lambda r: str(r['puntaje_prioridad']))])
A('## 6. Referencia, rutas alternas e infraestructura de acceso\n')
A('**Rutas alternas** — no se ingieren:\n'); tabla(O['ruta_alterna'], [('ID', idc), ('Fuente', lk), ('Usar en su lugar', lambda r: f"`{r['id_ruta_principal']}`")])
A('**Infraestructura de acceso** — se monitorean sus fechas de actualización:\n'); tabla(O['infraestructura_acceso'], [('ID', idc), ('Fuente', lk)])
A(f'**Referencia** ({len(O["referencia"])}), **Ola 3** ({len(O["3_complementaria"])}) y **fuera de alcance** ({len(O["fuera_de_alcance"])}): filtrar por la columna `ola` en `catalogo_fuentes.csv`.\n')
A('## 7. Vacíos sin fuente pública\n')
A('Se buscaron y no existen como datos abiertos; quedan como solicitudes de acceso a la información o como tablas a construir:\n')
for x in nf['no_encontrado']: A(f"- **Vacío {x['vacio']}.** {c(x['detalle'])}")
A('')
A('## 8. Qué significa "curado" en cada ola\n')
A('''- **Ola 0:** tablas de dimensión versionadas: ubigeo con vigencia (construida desde el Directorio de Municipalidades, por no existir una tabla oficial legible por máquina), equivalencias INEI–RENIEC validadas, población por distrito y año (total) y por edad (departamento INEI, distrito MINSA), puentes IPRESS, IE, CUI y unidad ejecutora, estructura programática por año.
- **Ola 1:** cada fuente pasa por tres capas: **cruda** (archivo original con fecha de descarga), **estandarizada** (ubigeo INEI validado empíricamente, año, nombres comunes) e **indicadores** con ficha (fórmula, numerador, denominador, base geográfica, tipo de medida, nivel válido, quiebres).
- **Datos personales:** Pensión 65 publica DNI y nombres; Cuna Más, fechas de nacimiento. Se ingieren solo agregados por ubigeo; los datos personales no se almacenan.
- **Archivos grandes:** el gasto MEF y el GPNNA pesan 7–17 GB por año: ingesta por streaming y particionada por año.
- **Reglas de publicación** (precisión de encuestas, números pequeños, falacia ecológica, atribución territorial del gasto, Mapa de Pobreza 2018, criterio de anemia): se definen en la Fase 2 (auditoría C-01, C-02, C-03, A-05).
''')
open(os.path.join(OUT_PRI, 'priorizacion.md'), 'w').write('\n'.join(L))

# ---------------- estado de la auditoría ----------------
AUD = os.path.join(OUT_AUD, 'hallazgos_json')
import glob
H = []
for f in sorted(glob.glob(os.path.join(AUD, 'hallazgos_*.json'))): H += json.load(open(f))
asign = json.load(open(os.path.join(AUD, 'asignacion_temas.json')))
TEMA_EST = {
 'C-01': ('corregido_catalogo', 'base_geografica=ejecutora, llaves y limitaciones corregidas; cruzabilidad acotada en el embudo. La regla de cálculo se implementa en la Fase 2.'),
 'C-02': ('pendiente_fase2', 'Reglas de publicación: se escriben en la Fase 2.'),
 'C-03': ('corregido_catalogo', 'Limitación y regla de uso escritas en el registro; aplicación en la Fase 2.'),
 'C-04': ('corregido', 'Las cinco fuentes salieron de la Ola 1 con sus datos corregidos.'),
 'C-05': ('corregido_parcial', 'Agregados población por edad (INEI departamental, MINSA distrital en tablero), Directorio de Municipalidades, maestro de ejecutoras, estructura programática; RENIPRESS, padrón de IIEE y Censo 2025 corregidos. Pendiente: construir el ubigeo histórico y el cruce 0001/0002→1001 (no hay tabla oficial).'),
 'C-06': ('corregido', 'Prueba de humo en Chrome: 32 aprobadas, 11 con enlace confirmado; URL literales separadas de las plantillas; host PNDA normalizado.'),
 'A-01': ('corregido', 'Rutas alternas y regla -Mensual/-Diario.'), 'A-02': ('corregido', 'Regla de vigencia en el embudo.'),
 'A-03': ('corregido', 'Umbral de descarga, pesos y aritmética verificada al generar.'), 'A-04': ('corregido', 'Regla de capa, infraestructura de acceso y origen geoespacial.'),
 'A-05': ('corregido_catalogo', 'Campo anios_con_quiebre, omisión censal y ENDES 2025 corregidos; regla de uso en la Fase 2.'),
 'A-06': ('corregido_parcial', 'SIS-AFILIADOS confirmado como ubigeo INEI; SIS-ATENCIONES se valida empíricamente en la ingesta (Fase 2).'),
 'A-07': ('corregido', 'Inferencia vacía en registros; campos base_geografica y tipo_medida.'),
 'A-08': ('corregido_parcial', 'Agregados Mapa DCI, mortalidad neonatal, ETI, RRHH salud, Vaso de Leche, Evaluación Diagnóstica; vacunación en la Ola 1 por excepción. Sin fuente pública: RUBPVL, INFORHUS, vacunación abierta.'),
 'A-09': ('pendiente_fase3', 'Preguntas ancla y Ola 1a en la Fase 3 (la Ola 1 bajó de 43 a 29).'),
 'A-10': ('corregido', 'Esquema v2 tipado y test_catalogo.py (0 errores).'), 'A-11': ('corregido', 'Correcciones aplicadas con trazabilidad por registro.')}
aplicados = collections.defaultdict(list)
for r in d:
    for x in r.get('correcciones', []):
        for h in x['hallazgos']: aplicados[h].append(r['id'])
with open(os.path.join(OUT_AUD, 'auditoria_estado.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['id', 'tema', 'severidad', 'estado', 'registros_corregidos', 'detalle'])
    for h in H:
        g = asign.get(h['id']); est, det = TEMA_EST.get(g, ('pendiente', ''))
        regs = sorted(set(aplicados.get(h['id'], [])))
        if regs and est.startswith('pendiente'): est = 'corregido_parcial'
        w.writerow([h['id'], g, h['severidad'], est, '; '.join(regs), det])
print('ok', N, len(ola1))
