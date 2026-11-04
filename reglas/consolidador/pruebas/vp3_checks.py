"""Verificación independiente de PARCHES_V3 y de los cambios de la ronda 3 (ajustes_dueno.py).
Uso: python3 -I reglas/consolidador/pruebas/vp3_checks.py <raiz>   (raíz con catalogo/ y reglas/; no modifica nada)
Imprime un JSON con: aplicación de cada parche V3, chequeos de referencias y chequeos de la ronda 3."""
import json, os, re, sys, unicodedata, importlib.util
RAIZ = sys.argv[1]
H = os.path.join(RAIZ, 'reglas')
D = json.load(open(os.path.join(H, 'reglas.json')))
MD = open(os.path.join(H, 'reglas.md')).read()
R = {r['id']: r for r in D['reglas']}
cat = json.load(open(os.path.join(RAIZ, 'catalogo', 'catalogo_fuentes.json')))
CAT = {f['id']: f for f in (cat['fuentes'] if isinstance(cat, dict) else cat)}

sys.path.insert(0, os.path.join(H, 'consolidador'))
def carga(nombre):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(H, 'consolidador', nombre + '.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
CA = carga('correcciones_auditoria'); AD = carga('ajustes_dueno')

def get(d, ruta):
    for k in ruta.split('.'):
        if not isinstance(d, dict) or k not in d: return '__AUSENTE__'
        d = d[k]
    return d

out = {'parches_v3': [], 'chequeos': {}, 'ronda3': {}}
# 1. ¿cada parche V3 quedó en reglas.json? (los 'set' sin assert en el consolidador)
for n, t in enumerate(CA.PARCHES_V3, 1):
    rid, op, pr = t[0], t[1], t[-1]; r = R[rid]; est = None
    if op == 'set':
        v = get(r, t[2]); est = 'aplicado' if v == t[3] else ('sobrescrito' if v != '__AUSENTE__' else 'ausente')
    elif op == 'replace':
        s = r.get(t[2]) or ''; est = 'aplicado' if (t[4] in s and t[3] not in s.replace(t[4], '')) else 'ausente'
    elif op == 'append':
        est = 'aplicado' if t[3] in (r.get(t[2]) or []) else 'ausente'
    traza = pr in (r.get('hallazgos_auditoria_v11') or [])
    out['parches_v3'].append(dict(n=n, regla=rid, op=op, campo=t[2], hallazgo=pr, estado=est, hallazgo_en_traza=traza))

# 2. referencias de los parches V3: IDs de reglas, fuentes del catálogo, campos
p12 = R['R-REG-12']['parametros']
ids_listas = p12['fuentes_sensibles_por_tema'] + p12.get('fuentes_con_personas_celda_a_celda', []) + p12['temas_sensibles'].get('fuentes_completas', []) + [x['fuente'] for x in p12.get('sin_personas', [])]
out['chequeos']['ids_fuera_catalogo_REG12'] = sorted({i for i in ids_listas if i not in CAT})
out['chequeos']['naturaleza_por_tema'] = {i: CAT.get(i, {}).get('naturaleza_dato') for i in p12['fuentes_sensibles_por_tema']}
out['chequeos']['por_tema_fuera_de_aplica_a'] = [i for i in p12['fuentes_sensibles_por_tema'] if CAT.get(i, {}).get('naturaleza_dato') not in R['R-REG-12']['aplica_a']['naturaleza_dato']]
out['chequeos']['temas_fuentes_completas_vs_por_tema'] = {'solo_en_por_tema': sorted(set(p12['fuentes_sensibles_por_tema']) - set(p12['temas_sensibles'].get('fuentes_completas', []))), 'solo_en_fuentes_completas': sorted(set(p12['temas_sensibles'].get('fuentes_completas', [])) - set(p12['fuentes_sensibles_por_tema']))}
cond12 = R['R-REG-12']['condicion']
out['chequeos']['parametros_REG12_no_citados_en_condicion'] = [k for k in p12 if k not in cond12 and k not in (R['R-REG-12'].get('implementacion') or '')]
out['chequeos']['REG12_usa_termino_fuentes_sensibles_sin_definir'] = {k: len(re.findall(r'fuentes? sensibles?\b', R['R-REG-12'].get(k) or '')) for k in ('condicion', 'enunciado', 'casos_borde')}
out['chequeos']['REG12_param_residual_null'] = [k for k, v in p12.items() if v is None]
out['chequeos']['catalogo_sensibilidad_divulgacion'] = dict(__import__('collections').Counter(str(f.get('sensibilidad_divulgacion')) for f in CAT.values()))
m1 = R['R-MOTOR-01']['parametros']
out['chequeos']['MOTOR01'] = {'fuente_sensible': m1['secuencia_degradacion']['fuente_sensible'], 'divulgacion_no_degradable': 'divulgacion' in m1['no_degradables'],
    'condicion_cita_prioridad_secuencia': 'prioridad_secuencia' in R['R-MOTOR-01']['condicion'],
    'etapas_del_bucle': re.findall(r'etapas \d–\d', R['R-MOTOR-01']['condicion'] + R['R-MOTOR-01']['implementacion']), 'etapa_REG12': R['R-REG-12']['etapa']}
out['chequeos']['ventanas'] = {'cubo_protegido_mvp': p12['cubo_protegido']['mvp'], 'TERRITORIO04_fuentes_sensibles': R['R-TERRITORIO-04']['parametros'].get('fuentes_sensibles')}
out['chequeos']['ENC13_referencias'] = [(x['titulo'][:60], x.get('url')) for x in R['R-ENC-13']['referencias']]
out['chequeos']['CRUCES03_cita_declaracion_2020'] = any('Comisión Consultiva' in x['titulo'] for x in R['R-CRUCES-03']['referencias'])
out['chequeos']['diccionario_filas_anio_referencia'] = [c['campo'] for c in D['campos'] if re.search(r'anio_referencia|edad_dato', c['campo'])]
out['chequeos']['residuo_fin_periodo'] = sorted({r['id'] for r in D['reglas'] if 'fin del periodo de referencia' in json.dumps(r, ensure_ascii=False)})
# mensajes y corrector
LEX = json.load(open(os.path.join(H, 'consolidador', 'lenguaje_prohibidas_v11.json')))
def _n(t): return ''.join(ch for ch in unicodedata.normalize('NFD', t.lower()) if unicodedata.category(ch) != 'Mn')
RX = [(x['categoria'], re.compile(_n(x['patron']) if x.get('normalizar', True) else x['patron'], re.I), x.get('normalizar', True)) for x in LEX['prohibidas']]
def bloquea(t):
    t = re.sub(r'\{\{[^}]*\}\}', 'X', t); return sorted({c for c, rx, n in RX if rx.search(_n(t) if n else t.lower())})
out['chequeos']['mensajes'] = {i: dict(largo=len(R[i]['mensaje_usuario'] or ''), corrector=bloquea(R[i]['mensaje_usuario'] or ''),
    v3_vigente=any(t[0] == i and t[2] == 'mensaje_usuario' and (t[3] if t[1] == 'set' else t[4]) in (R[i]['mensaje_usuario'] or '') for t in CA.PARCHES_V3))
    for i in ('R-GASTO-05', 'R-CRUCES-06', 'R-DENOMINADORES-03', 'R-REG-12')}
out['chequeos']['mensajes_por_revisar'] = D['mensajes_por_revisar_jerga_longitud']
out['chequeos']['CRUCES06_niveles_condicion'] = re.findall(r'provincias o distritos dentro de un departamento|25 departamentos', R['R-CRUCES-06']['condicion'])
out['chequeos']['CRUCES06_enunciado_vs_param'] = (re.findall(r'al menos (\d+) territorios', R['R-CRUCES-06']['enunciado']), R['R-CRUCES-06']['parametros'].get('n_min_coeficiente'))
out['chequeos']['personas_censadas_definido_fuera_de_LENGUAJE02'] = sorted({r['id'] for r in D['reglas'] if 'personas_censadas' in json.dumps(r, ensure_ascii=False)} - {'R-LENGUAJE-02'}) or [x['campo'] for x in D['campos'] if 'personas_censadas' in json.dumps(x, ensure_ascii=False)]
out['chequeos']['lexico_tiene_patron_poblacion'] = [x['patron'] for x in LEX['prohibidas'] if 'poblaci' in x['patron']]
cr = json.load(open(os.path.join(H, 'consolidador', 'pruebas', 'corpus_reserva.json'))); ca = json.load(open(os.path.join(H, 'consolidador', 'pruebas', 'corpus_auditor.json')))['oraciones']
nres = len(cr['pasan']) + len(cr['bloquean'])
# COM-07 (decisión del orquestador, 7/10/2026): también cuenta corpus_ronda4.json; total = oraciones únicas de los 3 archivos
_p4 = os.path.join(H, 'consolidador', 'pruebas', 'corpus_ronda4.json')
c4 = json.load(open(_p4))['oraciones'] if os.path.exists(_p4) else []
_k = lambda t: re.sub(r'\s+', ' ', ''.join(ch for ch in unicodedata.normalize('NFD', re.sub(r'\{\{[^{}]*\}\}|\{\w+\}', 'X', t).lower()) if unicodedata.category(ch) != 'Mn')).strip()  # como el auditor final r4
_unicas = {_k(t) for t in cr['pasan'] + cr['bloquean']} | {_k(o['texto']) for o in ca} | {_k(o['texto']) for o in c4}
out['chequeos']['corpus'] = dict(reserva=nres, auditor=len(ca), ronda4=len(c4), suma=nres + len(ca) + len(c4),
                                 total=len(_unicas), duplicados=nres + len(ca) + len(c4) - len(_unicas),
                                 pct_reserva=round(nres / len(_unicas), 3), meta=200)
cons = open(os.path.join(H, 'consolidador', 'consolida_reglas.py')).read()
out['chequeos']['puerta_ci_assert'] = "assert not [p for p in PRUEBAS if p[0] != 'insumo_inexistente']" in cons and 'lexico_falso_positivo' in cons
out['chequeos']['consolidador_assert_en_set_v2v3'] = bool(re.search(r"for t in CA.PARCHES_V2 \+ CA.PARCHES_V3:(?:(?!\n\S).)*obj\[ks\[-1\]\] = val; assert", cons, re.S))
out['chequeos']['pruebas_consistencia'] = D['pruebas_consistencia']

# 3. ronda 3 (ajustes_dueno.py): presencia en reglas.json y reglas.md
r3 = {}
# CAMPOS_REGLAS puede traer varias entradas para el mismo (regla, ruta): rige la última, que debe coincidir exactamente con
# reglas.json. Una entrada anterior no es un fallo: se informa si la última la conserva (texto o lista como prefijo,
# dict como subconjunto) o si la sustituye (pieza B, decisiones del gasto r2, 8/10/2026).
_ult = {(rid, ruta): n for n, (rid, ruta, _) in enumerate(AD.CAMPOS_REGLAS)}
def _conserva(viejo, nuevo):
    if isinstance(viejo, str) and isinstance(nuevo, str): return viejo in nuevo
    if isinstance(viejo, list) and isinstance(nuevo, list): return nuevo[:len(viejo)] == viejo
    if isinstance(viejo, dict) and isinstance(nuevo, dict): return all(k in nuevo and nuevo[k] == v for k, v in viejo.items())
    return False
for n, (rid, ruta, val) in enumerate(AD.CAMPOS_REGLAS):
    _sub = [r2 for (q, r2), m in _ult.items() if q == rid and r2.startswith(ruta + '.') and m > n]  # subcampos fijados después
    if _ult[(rid, ruta)] == n and _sub:
        r3.setdefault(rid, []).append(('campo ' + ruta + ' (más ' + ', '.join(_sub) + ')', isinstance(val, dict) and _conserva(val, get(R[rid], ruta))
                                       and set(get(R[rid], ruta)) == set(val) | {x.split('.')[1] for x in _sub}))
    elif _ult[(rid, ruta)] == n:
        r3.setdefault(rid, []).append(('campo ' + ruta, get(R[rid], ruta) == val))
    else:
        r3.setdefault(rid, []).append(('campo ' + ruta + ' (entrada anterior)', 'conservada por la última' if _conserva(val, get(R[rid], ruta)) else 'sustituida por la última'))
for rid, campo, txt in AD.AGREGADOS_REGLAS_R3:
    r3.setdefault(rid, []).append(('agregado ' + campo, txt.strip() in (R[rid].get(campo) or '')))
for rid, old, new in AD.PARCHES_REGLAS_R3:
    s = json.dumps(R[rid], ensure_ascii=False)
    r3.setdefault(rid, []).append(('reemplazo', json.dumps(new, ensure_ascii=False)[1:-1] in s and json.dumps(old, ensure_ascii=False)[1:-1] not in s))
fila = {i: next((l for l in MD.splitlines() if l.startswith(f'| `{i}`')), '') for i in r3}
md = {'R-GASTO-05': '(v4)' in fila['R-GASTO-05'], 'R-GASTO-02': 'GA-09' in fila['R-GASTO-02'], 'R-TERRITORIO-08': 'dos cotas' in fila['R-TERRITORIO-08'],
      'R-REG-07': ('procedencia' in fila['R-REG-07'] or 'cotas' in fila['R-REG-07'])}
out['ronda3'] = {'json': r3, 'md_visible': md, 'especificaciones_nuevas': [k for k in AD.ESPECIFICACIONES_R3 if k in D['especificaciones']],
    'GASTO02_condicion_conserva_texto_original': ['Si UBIGEO nulo o solo departamento -> departamento_inversion' in R['R-GASTO-02']['condicion'], 'nacional_no_territorializable' in R['R-GASTO-02']['condicion']],
    'TERR08_condicion_menciona_SIEN': 'SIEN' in R['R-TERRITORIO-08']['condicion'],
    'REG07_condicion_menciona_cotas': 'cota' in R['R-REG-07']['condicion'],
    'campos_nuevos_GASTO05_en_diccionario': {c: any(re.search(r'\b' + c + r'\b', x['campo']) for x in D['campos']) for c in ('categoria_transferencia', 'bloque_consolidado', 'es_transferencia_intergub', 'es_transferencia_intergubernamental')},
    'GASTO05_hallazgos': R['R-GASTO-05'].get('hallazgos_auditoria_v11'), 'fecha_version': (D['fecha'], D['version']),
    'reglas_gasto_ronda2_pendientes': [i for i in ('R-GASTO-08b', 'R-GASTO-18', 'R-GASTO-19', 'R-GASTO-20', 'R-GASTO-21') if i not in R]}

# 4. Cierres (ronda 4): un chequeo por hallazgo o contradicción; True = cerrado. D-R4-1 queda abierto mientras CA.D_R4_1 sea None.
def _md_fila(i): return next((l for l in MD.splitlines() if l.startswith(f'| `{i}`')), '')
def _textos(m): return re.findall(r'«([^»]*)»', m) or [m]
dic = {x['campo']: x for x in D['campos']}
g05 = R['R-GASTO-05']['mensaje_usuario'] or ''
sec = m1['secuencia_degradacion']['fuente_sensible']
cubo, t04 = p12['cubo_protegido']['mvp'], R['R-TERRITORIO-04']['parametros'].get('fuentes_sensibles', '')
ventana = any('ventana' in x for x in sec)
# M4: residuos de D-R4-1 (cada opción debe dejar coherentes la secuencia, el cubo, R-TERRITORIO-04 y R-REG-04 con RMM, TMI y TMN)
r04 = R['R-REG-04']; p04 = r04['parametros']; prio = m1['prioridad_secuencia']
txt_v = json.dumps([R[i] for i in ('R-MOTOR-01', 'R-REG-04', 'R-REG-12', 'R-TERRITORIO-04')], ensure_ascii=False)
RESIDUOS_D_R4_1 = []
def _res(cond, msg):
    if not cond: RESIDUOS_D_R4_1.append(msg)
_res('pendiente' not in prio, 'prioridad_secuencia: D-R4-1 sin decidir')
_res('2020–2024' not in txt_v, 'quedan ventanas 2020–2024 (no son ventanas fijas de la decisión)')
_res('Celdas sensibles (RMM, TMI, TMN' in r04['enunciado'] and 'Celdas sensibles (RMM, TMI, TMN)' in r04['implementacion'], 'R-REG-04: enunciado o implementación sin el trato de las celdas sensibles (RMM, TMI, TMN)')
_res('celdas sensibles' in str(p04.get('nivel_minimo_agrupado')) and 'celdas sensibles' in str(p04.get('max_anios_agrupados')), 'R-REG-04: nivel_minimo_agrupado o max_anios_agrupados sin el caso de las celdas sensibles')
_res('2020–2024' not in (r04.get('ejemplo') or ''), 'R-REG-04: ejemplo con 2020–2024')
if ventana:
    n_ = re.search(r'ventana_fija_(\d+)_anios', ' '.join(sec)).group(1)
    _res('ventanas fijas' in cubo and f'{n_} años' in cubo, 'cubo_protegido.mvp no admite la ventana de la secuencia')
    _res('ventanas fijas' in t04 and f'{n_} años' in t04, 'R-TERRITORIO-04 no admite la ventana de la secuencia')
    _res(f'{n_} años' in prio, 'prioridad_secuencia con otra ventana')
    _res(f'{n_} años' in str(p04.get('rmm_nivel_minimo')), 'R-REG-04.rmm_nivel_minimo con otra ventana')
    _res('entre territorios' in p12.get('prueba_restas', ''), 'prueba_restas sin supresión complementaria entre territorios')
    _res('ventana_con_choque' in p04, 'R-REG-04 sin aviso de años de choque en la ventana')
    _res('RMM, TMI o TMN' in cond12, 'R-REG-12 (1): RMM, TMI o TMN con 5-9 casos no llegan a la ventana')
else:
    _res('sueltos' in cubo, 'cubo_protegido.mvp no dice años sueltos')
    _res('sin agrupar' in prio, 'prioridad_secuencia no dice que no se agrupan años')
    _res('5 años)' not in str(p04.get('rmm_nivel_minimo')) or 'posterior' in str(p04.get('rmm_nivel_minimo')), 'R-REG-04.rmm_nivel_minimo exige 5 años sin ventana en la secuencia')
out['residuos_D_R4_1'] = RESIDUOS_D_R4_1
_PERS = re.compile(r'matr[íi]cula|usuarios|hogares|beneficiari|docentes|poblaci[óo]n|autoridades', re.I)
sp = p12.get('sin_personas', [])
_m2 = [x['fuente'] for x in sp if _PERS.search(CAT.get(x['fuente'], {}).get('descripcion', '')) and (str(x.get('ninguna', x.get('variables', ''))).startswith('todas') or not _PERS.search(str(x.get('normal', ''))))]
out['M2_sin_personas_con_personas'] = _m2
sys.path.insert(0, os.path.join(H, 'consolidador'))
try:
    import corrector_estructural as CE
    _ce = json.load(open(os.path.join(H, 'consolidador', 'pruebas', 'casos_personas_censadas.json')))
    _hec01 = all(bool(CE.personas_censadas(c['texto'], _ce['cifras'])) == (c['debe'] == 'regenerar') for c in _ce['casos'])
except Exception:
    _hec01 = False
r01, r02 = R['R-GASTO-01'], R['R-GASTO-02']
_DEC = os.path.join(RAIZ, 'docs', 'decisiones.md')  # H7 (auditoría de E1): tope de la fecha de reglas.json
def _fechas_decisiones(txt):  # registro consolidado (2/11/2026): fecha dd/mm/aaaa en su columna; antes, filas «| aaaa-mm-dd |»
    iso = re.findall(r'(?m)^\| (\d{4}-\d{2}-\d{2}) \|', txt)
    dmy = ['%s-%s-%s' % (a, m.zfill(2), d.zfill(2)) for d, m, a in re.findall(r'\| (\d{1,2})/(\d{1,2})/(\d{4}) \|', txt)]
    return iso + dmy
_ULTIMA_DECISION = max(_fechas_decisiones(open(_DEC, encoding='utf-8').read()) or [D['fecha']]) if os.path.exists(_DEC) else D['fecha']
K = {
 'C-V3-3/N2 listas únicas (sin fuentes_completas, ola1 ni con_personas)': 'fuentes_completas' not in p12['temas_sensibles'] and 'fuentes_sensibles_ola1' not in p12 and 'fuentes_con_personas_celda_a_celda' not in p12,
 'C-V3-3 IDs de R-REG-12 en el catálogo': not out['chequeos']['ids_fuera_catalogo_REG12'],
 'C-V3-3/N2 mecanismo para ninguna (sin_personas citado y con MINEDU-CENSO-EDUCATIVO)': 'sin_personas' in cond12 and any(x['fuente'] == 'MINEDU-CENSO-EDUCATIVO' for x in p12.get('sin_personas', [])),
 'C-V3-3 sin el término «fuentes sensibles»': not any(out['chequeos']['REG12_usa_termino_fuentes_sensibles_sin_definir'].values()),
 'C-V3-2 la supresión por nivel pide degradación y el motor la atiende': 'solicitar_degradacion(divulgacion_nivel' in cond12 and 'divulgacion_nivel' in m1['motivos_degradables'] and 'R-REG-12' in R['R-MOTOR-01']['condicion'] and 'etapas 2–6' in R['R-MOTOR-01']['implementacion'],
 'C-V3-2 {alternativa} definida': 'alternativa' in p12,
 'P9 condición de R-MOTOR-01 cita prioridad_secuencia': 'prioridad_secuencia' in R['R-MOTOR-01']['condicion'],
 'N3 encuestas con su propia secuencia': 'encuestas siguen su propia secuencia' in m1['prioridad_secuencia'],
 'C-V3-1/M4 (D-R4-1) ventanas coherentes en R-MOTOR-01, R-REG-12, R-TERRITORIO-04 y R-REG-04 (RMM, TMI, TMN)': not RESIDUOS_D_R4_1,
 'HEC-12 todas las referencias de R-ENC-13 con URL': all(x.get('url') for x in R['R-ENC-13']['referencias']),
 'C-V3-4 mensaje de R-CRUCES-06 válido para cualquier nivel': 'en vez de departamentos' not in R['R-CRUCES-06']['mensaje_usuario'],
 'C-V3-4 enunciado de R-CRUCES-06 = parámetro': out['chequeos']['CRUCES06_enunciado_vs_param'][0] == [str(out['chequeos']['CRUCES06_enunciado_vs_param'][1])],
 'C-V3-5/HEC-01 personas_censadas en la condición y en el diccionario': 'personas_censadas' in R['R-LENGUAJE-02']['condicion'] and 'personas_censadas' in dic['poblacion_objetivo']['para_que'],
 'COM-07 prueba_corrector apunta a los corpus del consolidador': 'consolidador/pruebas' in json.dumps(R['R-LENGUAJE-02']['parametros'].get('prueba_corrector'), ensure_ascii=False),
 'COM-07 corpus ≥ 200 oraciones únicas (reserva + auditor + ronda 4)': out['chequeos']['corpus']['total'] >= 200,
 'C-R3-4/COM-13 R-GASTO-05: cada texto ≤ 300 y sin bloqueo del corrector (lo reescribe l_mensajes)': all(len(t) <= 300 for t in _textos(g05)) and not bloquea(g05),
 'C-R3-1 R-GASTO-02 sin cláusulas viejas y con GA-09': not any(out['ronda3']['GASTO02_condicion_conserva_texto_original']) and 'multidepartamental_mef' in R['R-GASTO-02']['condicion'] and 'nacional' not in re.sub(r'nacional_multidepartamental|Gobierno Nacional', '', R['R-GASTO-02']['enunciado']),
 'C-R3-2 condición de R-TERRITORIO-08 con la excepción SIEN': 'SIEN' in R['R-TERRITORIO-08']['condicion'] and 'dos cotas' in R['R-TERRITORIO-08']['condicion'] and 'ubigeo_procedencia' in R['R-TERRITORIO-08']['condicion'],
 'C-R3-3 condición de R-REG-07 con cotas, aviso del 50 % y bandas fuera del SIEN': all(x in R['R-REG-07']['condicion'] for x in ('cota_sup', 'cota_inf', 'salvo el SIEN', 'no podemos decir')) and 'cota superior' in R['R-CRUCES-09']['parametros']['criterios']['cobertura_registro'],
 'C-R3-5 diccionario con los campos de R-GASTO-05 y sin el nombre viejo': all(out['ronda3']['campos_nuevos_GASTO05_en_diccionario'][c] for c in ('categoria_transferencia', 'bloque_consolidado', 'es_transferencia_intergub')) and not out['ronda3']['campos_nuevos_GASTO05_en_diccionario']['es_transferencia_intergubernamental'],
 'C-R3-6 reglas.md muestra el cambio de R-REG-07': 'dos cotas' in _md_fila('R-REG-07'),
 # E1 (8/10/2026): la fecha puede ser posterior a la ronda 3 (cada actualización la avanza), con formato AAAA-MM-DD y no
 # posterior a la última fila de 00_proyecto/decisiones.md (auditoría de E1, H7); antes exigía == '2026-10-07'
 'C-R3-6 traza, fecha y decisiones de la ronda 3': bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', D['fecha'])) and '2026-10-07' <= D['fecha'] <= _ULTIMA_DECISION and all(R[i].get('hallazgos_ronda3') for i in ('R-GASTO-05', 'R-GASTO-02', 'R-TERRITORIO-08', 'R-REG-07')) and '| D14 |' in MD,
 'IMP-19 (parte) assert en los set de PARCHES_V2/V3/V4': 'obj[ks[-1]] = val; assert _get(r, ruta) == val, (rid, ruta)' in cons,
 'pruebas_consistencia vacías': D['pruebas_consistencia'] == [],
 'M1 «-MUL.DEP-» exceptuado en R-GASTO-01 (b) y en R-GASTO-02 (4)': '«-MUL.DEP-» (99xxxx, ubicaciones desconocidas) sigue R-GASTO-02 (4)' in r01['condicion'] and 'no entran en esa regla' in r02['condicion'],
 'M2 sin_personas no exime variables que cuentan personas u hogares': bool(sp) and not _m2,
 'M3 guardia por comparación con la propuesta original (todas las capas)': '_ORIG = copy.deepcopy(by)' in cons and 'def _pisa(rid, ruta)' in cons and os.path.exists(os.path.join(H, 'consolidador', 'pruebas', 'prueba_guardia.py')),
 'HEC-01 regla de personas_censadas ejecutable y con casos': _hec01 and 'poblacion_censada_verificacion' in R['R-LENGUAJE-02']['parametros'] and 'casos_personas_censadas' in cons,
 'B1 enunciado de R-MOTOR-01 y secuencia sensible para censos': 'R-REG-12' in R['R-MOTOR-01']['enunciado'] and 'censos' in m1['prioridad_secuencia'],
 'B2 R-GASTO-02 nombra *_inversion, ejemplo posible y nivel nacional_multidepartamental publicable': all(x in r02['condicion'] for x in ('distrito_inversion', 'provincia_inversion', 'departamento_inversion')) and 'tres distritos' not in (r02.get('ejemplo') or '') and 'nacional_multidepartamental' in r01['parametros'].get('nivel_maximo_publicable', {}),
 'B4 es_transferencia no figura como reemplazado y vigente a la vez': not any('es_transferencia (' in x['reemplaza'] for x in D['campos']),
}
# Auditoría final r4 (F1-F7), 7/10/2026
_dp = D.get('decisiones_pendientes')
_fila = next((x['decision'] for x in D['decisiones'] if x['id'] == 'D-R4-1'), '')
_opc = getattr(CA, 'D_R4_1', None)
_per = p04.get('periodos_permitidos', [])
_anios = [int(a) for v in _per if v != 'año suelto' for a in re.findall(r'\d{4}', v)]
_vs_BC = [t[3] for o in ('B', 'C') for t in CA.OPCIONES_D_R4_1[o] if t[2] == 'parametros.ventanas_fijas']
_restas_A = next((t[3] for t in CA.OPCIONES_D_R4_1['A'] if t[2] == 'parametros.prueba_restas'), '')
_r04txt = json.dumps({k: r04.get(k) for k in ('enunciado', 'condicion', 'implementacion', 'parametros', 'ejemplo')}, ensure_ascii=False)
K.update({
 'F1 decisiones_pendientes legible y estado pendiente sin ventanas multianuales de RMM, TMI ni TMN': isinstance(_dp, list) and (
     (_opc is None and any(x['id'] == 'D-R4-1' and 'R-REG-04' in x['reglas_afectadas'] for x in _dp) and not ventana
      and _per == ['año suelto'] and 'sueltos' in cubo)
     or (_opc in ('A', 'B', 'C') and _dp == [] and _fila.startswith(f'Opción {_opc} aplicada'))),
 'F2 la opción A incluye la supresión complementaria entre territorios': 'entre territorios' in _restas_A,
 'F3 ventanas de B y C desde 2017 (SINADEF), sin superponerse ni partir años': all(int(re.findall(r'\d{4}', v[0])[0]) == 2017 for v in _vs_BC) and all(min(int(a) for x in v for a in re.findall(r'\d{4}', x)) >= 2017 for v in _vs_BC) and (not _anios or min(_anios) >= 2017),
 'F4 R-REG-04 sin «hasta 5 años» ni rama de celdas no sensibles': 'hasta 5 años' not in _r04txt and 'no sensibles' not in _r04txt,
 'F5 R-GASTO-03 y R-DENOMINADORES-04 sin las frases ambiguas': 'de este gasto' not in (R['R-GASTO-03']['mensaje_usuario'] or '') and 'quienes no llegó' not in (R['R-DENOMINADORES-04']['mensaje_usuario'] or ''),
 'F6 D_R4_1 válido y la tabla dice la opción aplicada': _opc in (None, 'A', 'B', 'C') and (_fila.startswith('PENDIENTE') if _opc is None else _fila.startswith(f'Opción {_opc} aplicada')),
 'F7/M4 comillas unificadas y MINSA citado para la RMM': not any("'" in (r.get('mensaje_usuario') or '') for r in D['reglas'] if r['estado'] == 'vigente') and 'MINSA hace seguimiento de cada muerte materna' in (r04.get('mensaje_usuario') or '') and any('muerte-materna' in x.get('url', '') for x in r04.get('referencias', [])),
})
out['cierres'] = K
out['cierres_abiertos'] = [k for k, v in K.items() if not v]
print(json.dumps(out, ensure_ascii=False, indent=1))
