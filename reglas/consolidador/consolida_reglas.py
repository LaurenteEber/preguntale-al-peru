"""Consolida las propuestas de reglas de la fase 2 en un único conjunto ordenado por etapa de evaluación."""
import json, glob, os, collections
C = os.path.dirname(os.path.abspath(__file__)); H = os.path.dirname(C); OUT = H  # reglas/
CATALOGO = os.path.join(os.path.dirname(H), 'catalogo', 'catalogo_fuentes.json')
P = {os.path.basename(f)[:-5]: json.load(open(f)) for f in sorted(glob.glob(os.path.join(H, 'propuestas', '*.json')))}
R = [dict(r, _origen=k) for k, p in P.items() for r in p['reglas']]
by = {r['id']: r for r in R}
import re, sys; sys.path.insert(0, C); import correcciones_prueba as CP
for r in CP.NUEVAS: by[r['id']] = dict(r, _origen='prueba')
import copy; _ORIG = copy.deepcopy(by)  # guardia de CAMPOS_REGLAS: estado de cada regla antes de cualquier corrección
def _set_param(par, ruta, val):
    ks = ruta.split('.')
    for k in ks[:-1]: par = par.setdefault(k, {})
    par[ks[-1]] = val
for rid, op, val, pr in CP.PARCHES:
    r = by[rid]; r.setdefault('hallazgos_prueba', [])
    for p in pr.split(', '):
        if p not in r['hallazgos_prueba']: r['hallazgos_prueba'].append(p)
    if op == 'borde': r['casos_borde'] = (r.get('casos_borde') or '').rstrip() + f' [{pr}] ' + val
    elif op == 'param':
        if not isinstance(r.get('parametros'), dict): r['parametros'] = {}
        _set_param(r['parametros'], *val)
    elif op == 'set': r[val[0]] = val[1]
    elif op == 'replace':
        s = json.dumps(r, ensure_ascii=False); old = json.dumps(val[0], ensure_ascii=False)[1:-1]
        assert old in s, (rid, val[0]); by[rid] = json.loads(s.replace(old, json.dumps(val[1], ensure_ascii=False)[1:-1]))
for x in P['cruces_lenguaje']['lenguaje']['prohibidas']:
    if x['patron'] in CP.LENGUAJE:
        x['patron'], exc = CP.LENGUAJE[x['patron']]; x['excepcion'] = exc
assert sum(x['patron'] in [v[0] for v in CP.LENGUAJE.values()] for x in P['cruces_lenguaje']['lenguaje']['prohibidas']) == len(CP.LENGUAJE)

# ================= capa v1.1: auditoría independiente (correcciones_auditoria.py) =================
import correcciones_auditoria as CA
for r in CA.NUEVAS: by[r['id']] = dict(r, _origen='auditoria')
_ORIG.update({r['id']: copy.deepcopy(by[r['id']]) for r in CA.NUEVAS if r['id'] not in _ORIG})
def _get(d, ruta):
    for k in ruta.split('.'): d = d[k]
    return d
APLICADOS = []
for t in CA.PARCHES:
    rid, op, pr = t[0], t[1], t[-1]
    r = by[rid]; r.setdefault('hallazgos_auditoria_v11', [])
    for p_ in pr.split(', '):
        if p_ not in r['hallazgos_auditoria_v11']: r['hallazgos_auditoria_v11'].append(p_)
    if op == 'set':
        ruta, val = t[2], t[3]; obj = r; ks = ruta.split('.')
        for k in ks[:-1]:
            if not isinstance(obj.get(k), dict): obj[k] = {}
            obj = obj[k]
        obj[ks[-1]] = val; assert _get(r, ruta) == val
    elif op == 'replace':
        campo, viejo, nuevo = t[2], t[3], t[4]
        assert viejo and viejo in r[campo], (rid, campo, viejo); r[campo] = r[campo].replace(viejo, nuevo)
    elif op == 'borde': r['casos_borde'] = (r.get('casos_borde') or '').rstrip() + f' [{pr}] ' + t[2]
    elif op == 'mover_fuentes_a_insumos':
        r['insumos_regla'] = sorted(set(r.get('insumos_regla', []) + r['aplica_a']['fuentes'])); r['aplica_a']['fuentes'] = []
    else: raise ValueError(op)
    APLICADOS.append((rid, op, pr))
RENOMBRADOS = collections.Counter()
for rid, r in by.items():
    for campo in ('condicion', 'implementacion', 'casos_borde'):
        if isinstance(r.get(campo), str):
            for pat, nuevo in CA.RENOMBRES.items():
                r[campo], n = re.subn(pat, nuevo, r[campo]); RENOMBRADOS[pat] += n
    if isinstance(r.get('parametros'), dict):
        s_ = json.dumps(r['parametros'], ensure_ascii=False)
        for pat, nuevo in CA.RENOMBRES.items():
            s_, n = re.subn(pat, nuevo.replace("'", "\\'") if False else nuevo, s_); RENOMBRADOS[pat] += n
        r['parametros'] = json.loads(s_)
for rid, campo, viejo, nuevo in CA.POST_RENOMBRE:
    assert viejo in by[rid][campo], (rid, campo); by[rid][campo] = by[rid][campo].replace(viejo, nuevo)
# D-R4-1 (F1, F6): solo None, 'A', 'B' o 'C'. None aplica el estado seguro (sin ventanas multianuales de RMM, TMI ni TMN
# por debajo del nivel nacional) y queda en reglas.json → decisiones_pendientes.
_D_R4_1_OPC = getattr(CA, 'D_R4_1', None)
CA_INICIO_SINADEF = 2017  # catálogo: MINSA-SINADEF cobertura_temporal 2017–2026 (F3)
if _D_R4_1_OPC is not None and _D_R4_1_OPC not in CA.OPCIONES_D_R4_1:
    raise SystemExit(f"D_R4_1 no válido: {_D_R4_1_OPC!r}. Use None (pendiente), 'A', 'B' o 'C' en reglas/consolidador/correcciones_auditoria.py")
_D_R4_1 = CA.OPCIONES_D_R4_1[_D_R4_1_OPC] if _D_R4_1_OPC is not None else CA.PENDIENTE_D_R4_1
for t in CA.PARCHES_V2 + CA.PARCHES_V3 + getattr(CA, 'PARCHES_V4', []) + _D_R4_1:
    rid, op, pr = t[0], t[1], t[-1]; r = by[rid]
    for p_ in pr.split(', '):
        if p_ not in r.setdefault('hallazgos_auditoria_v11', []): r['hallazgos_auditoria_v11'].append(p_)
    if op == 'set':
        ruta, val = t[2], t[3]; obj = r; ks = ruta.split('.')
        for k in ks[:-1]:
            if not isinstance(obj.get(k), dict): obj[k] = {}
            obj = obj[k]
        obj[ks[-1]] = val; assert _get(r, ruta) == val, (rid, ruta)
    elif op == 'replace':
        campo, viejo, nuevo = t[2], t[3], t[4]
        assert viejo and viejo in (r.get(campo) or ''), (rid, campo, viejo); r[campo] = r[campo].replace(viejo, nuevo)
    elif op == 'append':
        r.setdefault(t[2], []); r[t[2]].append(t[3])
    elif op == 'borrar':
        ks = t[2].split('.'); obj = _get(r, '.'.join(ks[:-1])) if len(ks) > 1 else r
        assert ks[-1] in obj, (rid, t[2]); del obj[ks[-1]]
    else: raise ValueError(op)
    APLICADOS.append((rid, op, pr))
LEX = json.load(open(os.path.join(C, 'lenguaje_prohibidas_v11.json')))
P['cruces_lenguaje']['lenguaje']['prohibidas'] = LEX['prohibidas']
P['cruces_lenguaje']['lenguaje']['notas_corrector'] = LEX.get('nota_estructurales')
Fl = P['cruces_lenguaje']['ficha_limites']
for x in Fl['corta']['campos']:
    if x['campo'] == 'semaforo_respuesta': x['texto'] = CA.FICHA['corta_confianza']
    if x['campo'] == 'no_concluir_principal': x['texto'] = CA.FICHA['corta_no_concluir']
for s_ in Fl['larga']['secciones']:
    if s_['seccion'].startswith('4.'): s_['texto_plantilla'] = CA.FICHA['larga_precision']
Fl['corta']['ejemplo'] = Fl['corta']['ejemplo'].replace('Usar con cautela', 'Dato con limitaciones')
P['territorio_denominadores']['especificaciones']['tablas_curadas_mvp'] = CA.TABLAS_MVP
import ajustes_dueno as AD
# AD-2 (dueño, 4/11/2026; S1-14): frases estándar que cambia el dueño, junto a las sobrescrituras de prohibidas y notas_corrector
for _k, _v in getattr(AD, 'FRASES_ESTANDAR', {}).items():
    assert _k in P['cruces_lenguaje']['lenguaje']['frases_estandar'], _k
    P['cruces_lenguaje']['lenguaje']['frases_estandar'][_k] = _v
# Auditoría de E1 (H1): niveles nuevos del vocabulario (region_umc de la ENLA), antes de la nota
if getattr(AD, 'NIVEL_RANK_D8', None):
    _nota_nr = CA.NIVEL_RANK.pop('nota', ''); CA.NIVEL_RANK.update(AD.NIVEL_RANK_D8)
    _nota_nr = getattr(AD, 'NOTA_NIVEL_RANK_BASE', _nota_nr)  # Lima en tres ámbitos (9/10/2026): nota base reescrita
    CA.NIVEL_RANK['nota'] = _nota_nr + AD.NOTA_NIVEL_RANK_D8
# Decisiones del gasto, rondas 1–2 (7/10/2026): patrones nuevos del corrector (R-GASTO-15 y regla de nombres del PAN).
for _x in getattr(AD, 'PROHIBIDAS_GASTO_R2', []):
    assert _x['patron'] not in [y['patron'] for y in LEX['prohibidas']], _x['categoria']; LEX['prohibidas'].append(dict(_x))
_E = P['territorio_denominadores']['especificaciones']
_cols = _E['dim_ubigeo_historico'].setdefault('columnas', [])
for _c in AD.COLUMNAS_DIM_UBIGEO:
    if _c['columna'] not in [x.get('columna') for x in _cols]: _cols.append(_c)
_E['dim_ambito'] = AD.DIM_AMBITO
for _k, _v in getattr(AD, 'TABLAS_MVP_RESPALDO_L', {}).items():  # Lima en tres ámbitos (9/10/2026)
    assert _k in _E['tablas_curadas_mvp']['con_respaldo_vacias'], _k; _E['tablas_curadas_mvp']['con_respaldo_vacias'][_k] = _v
for _c in _cols:
    for _n in AD.COLUMNAS_DIM_UBIGEO:
        if _c.get('columna') == _n['columna']: _c['regla'] = _n['regla']
for _rid, _old, _new in getattr(AD, 'PARCHES_REGLAS', []):
    _s = json.dumps(by[_rid], ensure_ascii=False); _o = json.dumps(_old, ensure_ascii=False)[1:-1]
    assert _o in _s, (_rid, _old[:40]); by[_rid] = json.loads(_s.replace(_o, json.dumps(_new, ensure_ascii=False)[1:-1]))
for _rid, _campo, _texto in getattr(AD, 'AGREGADOS_REGLAS', []):
    assert isinstance(by[_rid].get(_campo), str), (_rid, _campo)
    by[_rid][_campo] = by[_rid][_campo].rstrip() + _texto
# Ronda 3 (pendientes menores, 7/10/2026): agregados, reemplazos de texto, campos completos y especificaciones nuevas
for _rid, _campo, _texto in getattr(AD, 'AGREGADOS_REGLAS_R3', []):
    assert isinstance(by[_rid].get(_campo), str), (_rid, _campo)
    by[_rid][_campo] = by[_rid][_campo].rstrip() + _texto
for _rid, _old, _new in getattr(AD, 'PARCHES_REGLAS_R3', []):
    _s = json.dumps(by[_rid], ensure_ascii=False); _o = json.dumps(_old, ensure_ascii=False)[1:-1]
    assert _s.count(_o) == 1, (_rid, _old[:40]); by[_rid] = json.loads(_s.replace(_o, json.dumps(_new, ensure_ascii=False)[1:-1]))
_SIN = object()
def _valor(d, ruta):
    for k in ruta.split('.'):
        if not isinstance(d, dict) or k not in d: return _SIN
        d = d[k]
    return d
def _renombra(v):  # los renombres de CA.RENOMBRES son mecánicos: no cuentan como corrección
    if isinstance(v, str):
        for pat, nuevo in CA.RENOMBRES.items(): v = re.sub(pat, nuevo, v)
        return v
    s_ = json.dumps(v, ensure_ascii=False)
    for pat, nuevo in CA.RENOMBRES.items(): s_ = re.sub(pat, nuevo, s_)
    return json.loads(s_)
def _pisa(rid, ruta):  # True si el campo ya no es el de la propuesta original (lo tocó cualquier capa anterior)
    a, o = _valor(by[rid], ruta), _valor(_ORIG.get(rid, {}), ruta)
    if a is _SIN: return False
    if o is _SIN: return True
    if ruta.split('.')[0] in ('condicion', 'implementacion', 'casos_borde', 'parametros'): o = _renombra(o)
    return o != a
for _r in getattr(AD, 'NUEVAS_GASTO_R2', []):  # decisiones del gasto, rondas 1–2: reglas nuevas
    assert _r['id'] not in by, _r['id']; by[_r['id']] = dict(copy.deepcopy(_r), _origen='decisiones_gasto_r2'); _ORIG[_r['id']] = copy.deepcopy(by[_r['id']])
for _r in (AD.nuevas_m1(by) if hasattr(AD, 'nuevas_m1') else []):  # slice M1, M1-01 (12/11/2026): reglas nuevas
    assert _r['id'] not in by, _r['id']; by[_r['id']] = dict(copy.deepcopy(_r), _origen='decisiones_m1'); _ORIG[_r['id']] = copy.deepcopy(by[_r['id']])
for _rid, _ruta, _val in getattr(AD, 'CAMPOS_REGLAS', []):  # guardia: no pisar sin querer un campo ya corregido
    assert not _pisa(_rid, _ruta) or (_rid, _ruta) in getattr(AD, 'SOBRESCRITURAS_CONSCIENTES', set()), ('CAMPOS_REGLAS pisa un campo corregido', _rid, _ruta)
for _rid, _ruta, _val in getattr(AD, 'CAMPOS_REGLAS', []):
    _d = by[_rid]; _ks = _ruta.split('.')
    for _k in _ks[:-1]:
        assert isinstance(_d.get(_k), dict), (_rid, _ruta); _d = _d[_k]
    _d[_ks[-1]] = _val
for _f in getattr(AD, 'TRANSFORMACIONES_P0', []): _f(by)  # piloto P0, 10/10/2026: cambios que no son rutas simples
for _rid, _hs in getattr(AD, 'HALLAZGOS_R3', {}).items(): by[_rid]['hallazgos_ronda3'] = list(_hs)
for _rid, _hs in getattr(AD, 'HALLAZGOS_GASTO_R2', {}).items(): by[_rid]['decisiones_gasto_r2'] = list(_hs)
for _rid, _hs in getattr(AD, 'HALLAZGOS_D8', {}).items(): by[_rid]['decisiones_dueno_2026_10_08'] = list(_hs)  # decisiones del 8/10/2026
for _rid, _hs in getattr(AD, 'HALLAZGOS_L', {}).items(): by[_rid]['decisiones_dueno_2026_10_09'] = list(_hs)  # Lima en tres ámbitos, 9/10/2026
for _rid, _hs in getattr(AD, 'HALLAZGOS_P0', {}).items(): by[_rid]['decisiones_dueno_2026_10_10'] = list(_hs)  # piloto P0, 10/10/2026
for _rid, _hs in getattr(AD, 'HALLAZGOS_M1', {}).items(): by[_rid]['decisiones_dueno_2026_11_12'] = list(_hs)  # slice M1, M1-01, 12/11/2026
for _n, _spec in getattr(AD, 'ESPECIFICACIONES_R3', {}).items():
    assert _n not in _E, _n; _E[_n] = _spec
_fs = json.dumps(P['cruces_lenguaje']['ficha_limites'], ensure_ascii=False)
for v_, n_ in [('Usar con cautela', 'Dato con limitaciones'), ('Solo como referencia', 'Dato muy aproximado'), ('Confiable', 'Dato sólido'), ('{nivel_valido}', '{nivel_publicado}'), ('solo es confiable para', 'solo da cifras con suficiente precisión para')]:
    _fs = _fs.replace(v_, n_)
P['cruces_lenguaje']['ficha_limites'] = json.loads(_fs); Fl = P['cruces_lenguaje']['ficha_limites']
Fl['ayuda_confianza'] = 'La confianza indica si hay suficientes datos y si son recientes. No indica qué causó el problema.'
# C-04 del slice 1 (decisión del dueño, 3/11/2026): NC-NIVEL también para toda cifra principal de encuesta muestral
# publicada por departamento, ámbito de Lima o nacional (sin esto, una cifra simple de encuesta no tenía ningún código y
# R-LENGUAJE-01 suprimía la respuesta).
_asig = [s for s in Fl['larga']['secciones'] if isinstance(s, dict) and 'reglas_asignacion' in s]
assert len(_asig) == 1, 'reglas_asignacion de la ficha larga'
_asig[0]['reglas_asignacion']['NC-NIVEL'] = ('nivel_respuesta > nivel_pedido, o cifra principal de encuesta muestral '
                                            'publicada por departamento, ámbito de Lima o nacional cuando ningún otro código aplica (C-04, 3/11/2026)')

ETAPAS = collections.OrderedDict([
 ('0_prerrequisitos', ('Insumos y secuencia del motor', 'Que la cifra se pueda calcular y que el motor sepa cómo degradarla',
   ['R-MOTOR-03', 'R-DEP-01', 'R-MOTOR-01', 'R-MOTOR-02'])),
 ('1_territorio', ('Llave territorial', 'Que cada dato esté bien ubicado antes de cualquier cálculo',
   ['R-TERRITORIO-09', 'R-TERRITORIO-01', 'R-TERRITORIO-02', 'R-TERRITORIO-03', 'R-TERRITORIO-08', 'R-TERRITORIO-06', 'R-TERRITORIO-07'])),
 ('2_nivel', ('Nivel válido de publicación', 'A qué territorio se puede referir cada cifra según cómo se produjo',
   ['R-ENC-06', 'R-ENC-07', 'R-ENC-08', 'R-ENC-09', 'R-ENC-15', 'R-REG-02', 'R-GASTO-01', 'R-GASTO-02', 'R-GASTO-03', 'R-TERRITORIO-04', 'R-TERRITORIO-05', 'R-EST-05'])),
 ('3_denominador', ('Denominadores', 'Qué población se usa para tasas, coberturas y gasto por habitante',
   ['R-DENOMINADORES-01', 'R-DENOMINADORES-02', 'R-DENOMINADORES-03', 'R-DENOMINADORES-04', 'R-DENOMINADORES-05', 'R-DENOMINADORES-07', 'R-EST-04', 'R-GASTO-11', 'R-GASTO-12'])),
 ('4_precision', ('Precisión y calidad de la cifra', 'Si la cifra es publicable, referencial o se suprime',
   ['R-ENC-01', 'R-ENC-02', 'R-ENC-03', 'R-ENC-04', 'R-ENC-05', 'R-ENC-10', 'R-ENC-17', 'R-ENC-18', 'R-ENC-16',
    'R-REG-01', 'R-REG-03', 'R-REG-04', 'R-REG-05', 'R-REG-06', 'R-REG-07', 'R-REG-08', 'R-REG-09', 'R-EST-01', 'R-EST-03',
    'R-GASTO-04', 'R-GASTO-05', 'R-GASTO-06', 'R-GASTO-07', 'R-GASTO-10', 'R-GASTO-13', 'R-GASTO-14', 'R-GASTO-17'])),
 ('5_series', ('Vigencia, series y quiebres', 'Cuándo se puede hablar de cambios en el tiempo',
   ['R-ENC-13', 'R-ENC-14', 'R-REG-10', 'R-REG-14', 'R-GASTO-08', 'R-GASTO-09', 'R-CRUCES-04', 'R-LENGUAJE-04'])),
 ('6_divulgacion', ('Protección de datos personales', 'Que ninguna cifra permita identificar a una persona', ['R-REG-12'])),
 ('7_semaforo_cifra', ('Semáforo de cada cifra', 'Confianza de cada cifra antes de combinarla', ['R-CRUCES-09'])),
 ('8_cruces', ('Cruces y comparaciones', 'Cómo se combinan fuentes, territorios y años',
   ['R-CRUCES-11', 'R-CRUCES-01', 'R-CRUCES-02', 'R-CRUCES-03', 'R-CRUCES-05', 'R-CRUCES-08', 'R-CRUCES-06', 'R-CRUCES-07',
    'R-ENC-11', 'R-ENC-12', 'R-REG-15', 'R-EST-02', 'R-GASTO-15', 'R-GASTO-16'])),
 ('9_semaforo_respuesta', ('Semáforo de la respuesta', 'Resumen de la confianza de la respuesta completa', ['R-CRUCES-10'])),
 ('10_comunicacion', ('Ficha de límites y lenguaje', 'Cómo se redacta y qué acompaña a cada respuesta',
   ['R-LENGUAJE-01', 'R-LENGUAJE-03', 'R-LENGUAJE-06', 'R-LENGUAJE-02', 'R-LENGUAJE-05', 'R-LENGUAJE-07', 'R-LENGUAJE-08'])),
])
for _rid, _et, _tras in getattr(AD, 'ETAPAS_GASTO_R2', []):  # decisiones del gasto, rondas 1–2
    _ids = ETAPAS[_et][2]; assert _rid not in _ids and _tras in _ids, (_rid, _tras); _ids.insert(_ids.index(_tras) + 1, _rid)
for _rid, _et, _tras in getattr(AD, 'ETAPAS_M1', []):  # slice M1, M1-01 (12/11/2026)
    _ids = ETAPAS[_et][2]; assert _rid not in _ids and _tras in _ids, (_rid, _tras); _ids.insert(_ids.index(_tras) + 1, _rid)
ABSORBIDAS = {  # regla duplicada -> regla canónica (conflictos K1, K2, K5)
 'R-REG-11': ('R-ENC-14', 'Mismo contenido (criterio de anemia). La canónica aplica también a SIEN y REUNIS.'),
 'R-DENOMINADORES-06': ('R-REG-08', 'Coberturas >100 %: se adopta el umbral de 110 % de R-REG-08 (sin truncar) y su escalamiento a provincia; se conserva de DENOMINADORES-06 el rótulo cuando el numerador es por establecimiento.'),
 'R-REG-13': ('R-CRUCES-08', 'Jerarquía registro vs encuesta: se integra en la jerarquía de fuentes que miden lo mismo.'),
}
AJUSTES = {  # resolución de conflictos sobre las reglas canónicas
 'R-ENC-14': 'Aplica también a INS-CENAN-SIEN y MINSA-REUNIS (absorbe R-REG-11). Corte 6–23 meses OMS 2024: 10,5 g/dL.',
 'R-REG-08': 'Absorbe R-DENOMINADORES-06: si el numerador es por establecimiento, rotular "atenciones en establecimientos ubicados en…" antes de escalar.',
 'R-CRUCES-08': 'Absorbe R-REG-13: la encuesta representativa es la cifra principal a su nivel; bajo ese nivel, la estimación modelada oficial; el registro va en bloque aparte y nunca se resta ni promedia.',
 'R-ENC-05': 'El formato numérico (coma decimal, redondeo) lo fija R-LENGUAJE-03; esta regla conserva qué estadísticos acompañan la cifra.',
 'R-CRUCES-03': 'Excepción alineada con R-ENC-13: la pobreza monetaria ENAHO 2020–2021 es comparable según la Comisión Consultiva del INEI.',
 'R-ENC-08': 'Requiere el campo inferencia_verificada; ya verificadas en ficha técnica: ENAHO 2024, ENDES 2024, ENAPRES (por confirmar).',
}
AJUSTES.update(getattr(AD, 'AJUSTES_CONSOLIDACION_D8', {}))  # decisiones del dueño del 8/10/2026
for k in ABSORBIDAS: assert k in by and ABSORBIDAS[k][0] in by
asignadas = {i for _, (_, _, ids) in ETAPAS.items() for i in ids}
faltan = set(by) - asignadas - set(ABSORBIDAS); assert not faltan, faltan

CONFLICTOS = [
 ('K1', 'Anemia definida dos veces (encuestas y registros)', 'R-ENC-14 canónica; R-REG-11 absorbida.'),
 ('K2', 'Coberturas >100 %: R-REG-08 (referencial hasta 110 %) vs R-DENOMINADORES-06 (escalar desde 100 %)', 'Se adopta R-REG-08: no truncar; 100–110 % referencial; >110 % se muestran numerador y denominador y se escala a provincia.'),
 ('K3', 'Formato numérico en R-ENC-05 y R-LENGUAJE-03', 'R-LENGUAJE-03 fija el formato para todas las fuentes (estilo INEI).'),
 ('K4', 'Años 2020–2021: series (R-ENC-13), cruces (R-CRUCES-03) y redacción (R-LENGUAJE-04)', 'Un solo parámetro global anios_choque = [2020, 2021] con la misma excepción (pobreza monetaria ENAHO).'),
 ('K5', 'Registro vs encuesta: R-REG-13 y R-CRUCES-08', 'R-CRUCES-08 canónica con la jerarquía de R-REG-13.'),
 ('K6', 'Campos con el mismo significado y distinto nombre (criterio_anemia / criterio_medicion; quiebres / quiebres_tipados / anios_choque; denominador_* en tres ámbitos; estado_precision / estado_estabilidad; origen)', 'Diccionario único de campos (sección 4). "origen" de registros se renombra a origen_cifra para no chocar con el campo origen del catálogo.'),
 ('K7', 'Agrupación de años: 3 (encuestas, registros) vs 5 (mortalidad infantil)', 'Se mantiene: 3 por defecto; 5 solo en R-REG-04 (mortalidad infantil y neonatal).'),
]
CAMPOS = [  # diccionario unificado (canónico, nivel, reemplaza a, para qué)
 ('dominios_inferencia', 'catálogo', 'dominios_inferencia (encuestas y territorio)', 'Dominios oficiales de la encuesta (Lima Metropolitana, regiones naturales…).'),
 ('inferencia_verificada', 'catálogo', 'inferencia_verificada, cita_ficha_inferencia', 'Si el nivel de inferencia está confirmado en la ficha técnica (R-ENC-08).'),
 ('variables_diseno', 'catálogo', 'variables_diseno', 'Nombres de estrato, conglomerado y factor por encuesta y año.'),
 ('quiebres', 'catálogo', 'anios_con_quiebre (texto), quiebres, quiebres_tipados, anios_choque', 'Lista tipada: {anio, tipo (modo, criterio, cobertura, sistema, programa), descripcion, comparable_con}.'),
 ('sistema_ubigeo', 'catálogo', 'sistema_ubigeo, columna_ubigeo', 'INEI o RENIEC, detectado en la carga (R-TERRITORIO-02), y columna que lo contiene.'),
 ('rol_gasto', 'catálogo', 'rol_gasto, base_territorial_gasto', 'Fuente canónica de gasto vs ruta alterna (R-GASTO-04).'),
 ('velocidad_cambio', 'indicador', 'velocidad_cambio', 'rápida o lenta: ventana de años en cruces (R-CRUCES-03).'),
 ('criterio_medicion', 'indicador', 'criterio_anemia, criterio_medicion', 'Criterio con el que se midió (p. ej., anemia RM 363-2022 o RM 251-2024).'),
 ('poblacion_objetivo', 'indicador', 'poblacion_objetivo, poblacion_objetivo_dominio, universo', 'Grupo al que se refiere la cifra y universo (p. ej., niños 6–35 meses; solo atendidos).'),
 ('concepto_medido', 'indicador', 'concepto_medido, rank_concepto', 'Concepto común para detectar fuentes que miden lo mismo (R-CRUCES-08).'),
 ('denominador_principal / denominadores_contraste', 'indicador', 'denominador_tipo, tipo_denominador, denominador_principal, denominadores_contraste', 'Matriz de R-DENOMINADORES-01.'),
 ('tipo_estimacion', 'cifra', 'tipo_estimacion, origen (registros)', 'proporción, total, media, tasa, modelada, propia.'),
 ('n_sin_ponderar, n_efectivo, ee, cv, ic_inf, ic_sup, metodo_ic, gl, deff', 'cifra', 'idem + ic_metodo', 'Estadísticos de precisión (R-ENC-01).'),
 ('estado_cifra', 'cifra', 'estado_precision, estado_estabilidad, incertidumbre_publicada', 'publicable | referencial | suprimida | agregada | agrupada, con motivos[].'),
 ('nivel_publicado / motivo_nivel', 'cifra', 'nivel_valido, motivo_nivel, motivo_agregacion, nivel_atribucion_gasto, base_geografica_usada', 'Nivel al que finalmente se publica y por qué.'),
 ('periodo_agrupado', 'cifra', 'periodo_agrupado, anios_agrupados', 'Años combinados cuando se agrupa (R-ENC-10, R-REG-03).'),
 ('fecha_corte / es_preliminar', 'cifra', 'fecha_corte, es_preliminar, fecha_corte_datos, es_anio_cerrado, fecha_cierre_fuente', 'Corte de los datos y si el periodo está cerrado.'),
 ('vintage_denominador / metodo_denominador / sensibilidad_denominador', 'cifra', 'vintage_denominador, vintage_poblacion, denominador_fuente, denominador_anio, denominador_concepto, metodo_denominador, sensibilidad_denominador', 'Trazabilidad del denominador (R-DENOMINADORES-02, 05).'),
 ('geografia_base / grupo_comparable / version_dim_ubigeo', 'cifra', 'idem', 'Geografía (vigente o GEO2017) y versión de la tabla de ubigeo.'),
 ('pct_numerador_ubicado', 'cifra', 'idem', 'Cobertura territorial de la carga (R-TERRITORIO-08).'),
 ('ubigeo_atribucion / pct_gasto_atribuible / fase_gasto / precios', 'cifra', 'idem + anio_base_deflactor', 'Atribución y forma del gasto (R-GASTO-01, 03, 06, 12).'),
 ('es_transferencia_intergubernamental', 'cifra', 'idem', 'Evita el doble conteo (R-GASTO-05).'),
 ('rotulo_medida', 'cifra', 'rotulo_medida', 'Rótulo obligatorio según tipo_medida (R-REG-01).'),
 ('grupo_ranking', 'cifra', 'grupo_ranking, grupo_robusto', 'Grupo estadísticamente semejante en lugar de puesto (R-ENC-12, R-EST-01).'),
 ('test_cambio / p_valor_diferencia', 'cifra', 'test_cambio, p_valor_diferencia, diferencia_significativa, comparable_en_quiebre, comparable_con', 'Resultado de la prueba de diferencia (R-ENC-11).'),
 ('sensibilidad_divulgacion', 'cifra', 'idem', 'Si la celda requiere umbral sensible (R-REG-12).'),
 ('semaforo_cifra / motivos_semaforo / es_principal', 'cifra', 'idem', 'Salida de R-CRUCES-09.'),
 ('intencion_pregunta / id_cifra / cifras_permitidas', 'respuesta', 'idem', 'Control de la redacción (R-LENGUAJE-03, R-CRUCES-07).'),
 ('Tablas curadas', 'tabla', '—', 'dim_ubigeo_historico, puente_ubigeo, dim_dominio, fact_poblacion, dim_unidad_ejecutora, dim_inversion, dim_tema_gasto, cruces_permitidos, evaluaciones_relacionadas, explicaciones_divergencia, cobertura_registro_estimada.'),
]
CAMPOS += CP.CAMPOS_NUEVOS + CA.CAMPOS_CORREGIDOS + CA.CAMPOS_V2 + getattr(CA, 'CAMPOS_V4', []) + getattr(AD, 'CAMPOS_R3', []) + getattr(AD, 'CAMPOS_GASTO_R2', []) + getattr(AD, 'CAMPOS_D8', [])
CAMPOS = [x for x in CAMPOS if x[0] not in getattr(AD, 'CAMPOS_R3_RETIRADOS', [])]
_vistos = {}
for x in CAMPOS: _vistos[x[0]] = x
CAMPOS = [x for x in CAMPOS if _vistos[x[0]] is x and not x[0].startswith('estado_cifra')] 
CAMPOS = [x for x in CAMPOS if not ('sensibilidad_divulgacion' == x[0] and x is not _vistos['sensibilidad_divulgacion'])]
CAMPOS.insert(0, [x for x in CA.CAMPOS_V2 if x[0] == 'estado_cifra'][0])
CAMPOS = [x for x in CAMPOS if not (x[0] == 'Tablas curadas')] + [('Tablas curadas', 'tabla', '—', 'MVP: ' + ', '.join(CA.TABLAS_MVP['imprescindibles']) + '. Pueden empezar vacías: ' + ', '.join(CA.TABLAS_MVP['con_respaldo_vacias']) + '.')]
DECISIONES = [
 ('D1', 'Serie de anemia', 'Recalcular la serie ENDES desde microdatos con el criterio RM 251-2024 (hemoglobina y altitud), o mostrar en el MVP solo el criterio vigente sin tendencia cruzada.', 'MVP: solo criterio vigente y series separadas; recalcular en la fase 4 (los microdatos lo permiten).', 'R-ENC-14'),
 ('D2', 'CV mayor a 30 %', 'Suprimir o mostrar como referencial sin techo (como hacen los cuadros del INEI).', 'Suprimir: el público no especialista no distingue una cifra referencial muy imprecisa.', 'R-ENC-03'),
 ('D3', 'Números pequeños en registros', 'Mínimo 5 y estable con 20 eventos (más supresión rural) o 3 y 10 (más cifras, más ruido).', 'Mantener 5 / 20 (práctica NCHS y NY DOH).', 'R-REG-03'),
 ('D4', 'Datos con base establecimiento por distrito (SIEN, vacunas, REUNIS)', 'Mostrar por distrito con el rótulo "en establecimientos ubicados en", o solo desde provincia.', 'Conteos por distrito con rótulo; tasas y coberturas desde provincia.', 'R-REG-02'),
 ('D5', 'Mapa de Pobreza 2018 y Mapa DCI 2019', 'Cifra principal con aviso de antigüedad, o solo contexto.', 'Contexto con aviso; la cifra principal es la más reciente disponible a nivel departamental.', 'R-EST-01, R-CRUCES-02'),
 ('D6', 'Gasto: atribución y deflactor', 'Umbral de gasto atribuible (50 %); IPC Lima vs nacional; repartir inversiones multidistritales.', '50 %; IPC Lima base último año cerrado; no repartir en el MVP.', 'R-GASTO-02, 03, 12'),
 ('D7', 'Geografía para series', 'Congelar en 2017 o usar la vigente; cuándo pasar a base 2025.', 'GEO2017 para series hasta que el INEI publique proyecciones base 2025; luego migrar de una vez.', 'R-TERRITORIO-04'),
 ('D8', 'Denominador de coberturas de salud', 'Población MINSA (coincide con cifras oficiales, solo en tablero) o estimación propia sobre INEI (reproducible).', 'Estimación propia como principal reproducible y MINSA como contraste cuando se capture; mostrar rango si difieren >10 %.', 'R-DENOMINADORES-01, 03, 05'),
 ('D9', 'Coeficientes de asociación en el MVP', 'Mostrar correlaciones entre territorios o solo valores lado a lado y mapas.', 'MVP: lado a lado y mapas; coeficientes solo por departamento con ≥20 territorios y siempre en ámbar.', 'R-CRUCES-06'),
 ('D10', 'Significancia', 'p < 0,05 o p < 0,10 (el INEI usa ambos según el informe).', 'p < 0,05 para afirmar cambios ante público general.', 'R-ENC-11'),
 ('D11', 'Tablas curadas', 'Quién mantiene cruces_permitidos, dim_tema_gasto, evaluaciones_relacionadas y explicaciones_divergencia, y con qué frecuencia.', 'Tú como dueño; revisión anual al publicarse el presupuesto y cada nueva fuente.', 'R-CRUCES-07, 08, 11; R-GASTO-08'),
]

DECISIONES = [(a, b, cc, CA.AJUSTES_DECISIONES.get(a, CP.AJUSTES_DECISIONES.get(a, d)), e) for a, b, cc, d, e in DECISIONES]
DECISION_DUENO = {  # columna 'Decisión Eber' (5/10/2026)
 'D1': 'Adoptada. Después del MVP se recalcula la serie histórica con el criterio vigente para tener una serie suficiente para análisis.',
 'D7': 'Adoptada. Antes, confirmar qué ha publicado el INEI del Censo 2025.'}
DECISIONES = [(a, b, cc, d, e, DECISION_DUENO.get(a, 'Adoptada (recomendación).')) for a, b, cc, d, e in DECISIONES]
DECISIONES += list(getattr(AD, 'DECISIONES_R3', [])) + list(getattr(AD, 'DECISIONES_GASTO_R2', [])) + list(getattr(AD, 'DECISIONES_D8', []))
# D-R4-1 (ronda 4): fila visible en la tabla de decisiones; mientras el interruptor siga en None queda «PENDIENTE»
_D_R4_1_TXT = ('PENDIENTE: sin decidir (interruptor D_R4_1 = None en reglas/consolidador/correcciones_auditoria.py). Mientras tanto se '
               'aplica el estado seguro: RMM, TMI y TMN sin ventanas de varios años por debajo del nivel nacional (solo años '
               'sueltos). Explicación: auditoria/ronda4/explicacion_D-R4-1.md.') if _D_R4_1_OPC is None else CA.D_R4_1_TEXTO[_D_R4_1_OPC]
DECISIONES_PENDIENTES = [] if _D_R4_1_OPC is not None else [dict(
    id='D-R4-1', tema='Años de las celdas sensibles de mortalidad (RMM, TMI, TMN)', reglas_afectadas=list(CA.D_R4_1_REGLAS),
    estado_aplicado='seguro: sin ventanas multianuales de RMM, TMI ni TMN por debajo del nivel nacional',
    validador='no publicar ventanas de varios años de RMM, TMI ni TMN por debajo del nivel nacional')]
DECISIONES.append(('D-R4-1', 'Años de las celdas sensibles de mortalidad (RMM, TMI, TMN) en el MVP',
                   'A: no sumar años; B: periodos fijos de 5 años; C: periodos fijos de 3 años',
                   'C (analista de la ronda 4)', ', '.join(CA.D_R4_1_REGLAS), _D_R4_1_TXT))
_FECHA, _FECHA_TXT = getattr(AD, 'FECHA_ACTUALIZACION', ('2026-10-05', '5 de octubre de 2026'))
# ---------- pruebas de consistencia ----------
CAT = {f['id'] for f in json.load(open(CATALOGO))['fuentes']} if isinstance(json.load(open(CATALOGO)), dict) else {f['id'] for f in json.load(open(CATALOGO))}
vig_ids = {i for _, (_, _, ids) in ETAPAS.items() for i in ids}
PRUEBAS = []
for i in vig_ids:
    r = by[i]; txt = json.dumps({k: v for k, v in r.items() if k not in ('id', 'absorbe', 'hallazgos_prueba')}, ensure_ascii=False)
    for m in set(re.findall(r'R-[A-Z]+-\d\d', txt)):
        if m not in vig_ids: PRUEBAS.append(('ref_no_vigente', i, m))
    for f in (r.get('aplica_a') or {}).get('fuentes', []):
        if f not in CAT: PRUEBAS.append(('fuente_inexistente', i, f))
rx = [re.compile(x['patron'], re.I) for x in P['cruces_lenguaje']['lenguaje']['prohibidas']]
import unicodedata
def _norm(t): return ''.join(ch for ch in unicodedata.normalize('NFD', t.lower()) if unicodedata.category(ch) != 'Mn')
# texto_original (decisiones del gasto r2, patrón del PAN): el patrón se aplica al texto tal cual, sin minúsculas ni tildes quitadas
RX = [(x['categoria'], re.compile(_norm(x['patron']) if x.get('normalizar', True) else x['patron'], re.I),
       'original' if x.get('texto_original') else x.get('normalizar', True)) for x in LEX['prohibidas']]
_NUEVOS_R2 = [i_ for i_, x in enumerate(LEX['prohibidas']) if str(x.get('origen', '')).startswith('decisiones del gasto r2')]
def _bloquea(t, solo=None):
    t = re.sub(r'\{\{[^}]*\}\}', 'X', t)
    return [c_ for i_, (c_, rx_, n_) in enumerate(RX) if (solo is None or i_ in solo)
            and rx_.search(t if n_ == 'original' else (_norm(t) if n_ else t.lower()))]
cr = json.load(open(os.path.join(C, 'pruebas', 'corpus_reserva.json'))); ca = json.load(open(os.path.join(C, 'pruebas', 'corpus_auditor.json')))['oraciones']
ESTRUCTURALES = {'La pobreza en el distrito es de 45 % (Mapa de Pobreza 2018).', 'Actualmente la pobreza distrital alcanza alrededor de 45 %.', 'La anemia en el distrito fue de 30 % según el SIEN.'}
for t in cr['pasan'] + [o['texto'] for o in ca if o['debe'] == 'pasar']:
    if t not in cr['protegidas'] and _bloquea(t): PRUEBAS.append(('lexico_falso_positivo', '-', t))
for t in cr['bloquean'] + [o['texto'] for o in ca if o['debe'] == 'bloquear']:
    if t not in ESTRUCTURALES and not _bloquea(t): PRUEBAS.append(('lexico_no_detectada', '-', t))
import corrector_estructural as CE  # HEC-01: regla estructural ejecutable de R-LENGUAJE-02
_CE = json.load(open(os.path.join(C, 'pruebas', 'casos_personas_censadas.json')))
for _c in _CE['casos']:
    if bool(CE.personas_censadas(_c['texto'], _CE['cifras'])) != (_c['debe'] == 'regenerar'): PRUEBAS.append(('estructural_personas_censadas', 'R-LENGUAJE-02', _c['texto'][:60]))
ACC = {'publicar', 'publicar_referencial', 'suprimir', 'agregar_nivel', 'agrupar_anios', 'bloquear_cruce', 'rotular', 'advertir', 'revision_humana'}
VOC_NAT = {f.get('naturaleza_dato') for f in (json.load(open(CATALOGO))['fuentes'] if isinstance(json.load(open(CATALOGO)), dict) else json.load(open(CATALOGO)))}
for i in vig_ids:
    r = by[i]
    if r['accion'] not in ACC: PRUEBAS.append(('accion_fuera_vocabulario', i, r['accion']))
    for v in (r.get('aplica_a') or {}).get('naturaleza_dato', []):
        if v not in VOC_NAT: PRUEBAS.append(('naturaleza_fuera_vocabulario', i, v))
    for f in r.get('insumos_regla', []):
        if f.split(' ')[0] not in CAT: PRUEBAS.append(('insumo_inexistente', i, f))
    for pat in CA.RENOMBRES:
        for campo_ in ('condicion', 'implementacion'):
            if pat.startswith('\\b') and re.search(pat, r.get(campo_) or ''): PRUEBAS.append(('nombre_obsoleto', i, pat))
    if re.search(r"estado_cifra[^.;]{0,40}(\b(inestable|estable)\b|'suprimido'|\bsuprimido\b)", (r.get('condicion') or '') + (r.get('implementacion') or '')): PRUEBAS.append(('valor_estado_obsoleto', i, 'estado_cifra'))
    for m_ in re.finditer(r"tipo_estimacion\s*(?:==?\s*'(\w+)'|IN\s*\(([^)]*)\))", r.get('condicion') or ''):
        for v_ in ([m_.group(1)] if m_.group(1) else re.findall(r"'(\w+)'", m_.group(2))):
            if v_ not in ('proporcion', 'total', 'media', 'razon', 'tasa', 'modelada', 'propia'): PRUEBAS.append(('tipo_estimacion_fuera_vocabulario', i, v_))
    for t_ in [r.get('mensaje_usuario') or '', r.get('ejemplo') or '']:
        if re.search(r'Confiable|Usar con cautela|Solo como referencia|Cifra referencial|cifra confiable', t_): PRUEBAS.append(('rotulo_viejo', i, t_[:60]))
for h_ in CA.VEREDICTOS: pass
assert len(CA.VEREDICTOS) == 59, len(CA.VEREDICTOS)
print('pruebas:', collections.Counter(p[0] for p in PRUEBAS)); [print('  ', p) for p in PRUEBAS]
# ---- ronda 4 · auditoría final (F7): un solo formato de comillas en mensaje_usuario. Los textos que ve el usuario van
#      entre «…» (así el detector mide cada uno); los términos citados dentro de un texto, entre “…”. Listas en ajustes_dueno.py.
for _rid, _ref in getattr(AD, 'REFERENCIAS_R4', []):
    if _ref not in by[_rid].setdefault('referencias', []): by[_rid]['referencias'].append(_ref)
_COM = getattr(AD, 'COMILLAS_R4', {})
for _rid in _COM.get('textos', []):
    _m = by[_rid]['mensaje_usuario']; assert "'" in _m, _rid
    by[_rid]['mensaje_usuario'] = re.sub(r"'([^']*)'", r'«\1»', _m)
for _rid in _COM.get('terminos', []):
    _m = by[_rid]['mensaje_usuario']; assert "'" in _m, _rid
    by[_rid]['mensaje_usuario'] = re.sub(r"'([^']*)'", r'“\1”', _m)
_SIMPLES = sorted(i for i in vig_ids if "'" in (by[i].get('mensaje_usuario') or ''))
if _SIMPLES: PRUEBAS.append(('mensaje_con_comillas_simples', ', '.join(_SIMPLES), ''))
# ---- ronda 4 · l_mensajes: detector de mensajes (parámetros en ajustes_dueno.py, bloque 4.4) ----
JERGA = re.compile(AD.JERGA_MENSAJES, re.I); _MAX = AD.MENSAJES_MAX_CARACTERES
def _textos_mensaje(m):  # cada «…» es un texto que ve el usuario; sin «», el mensaje entero
    return re.findall(r'«([^»]*)»', m) or [m]
def _sin_marcadores(t): return re.sub(r'\{\{[^{}]*\}\}|\{\w+\}', 'X', t)  # {x} y {{x}} no son texto visible
def _revisar_mensaje(m):
    return [t for t in _textos_mensaje(m) if len(t) > _MAX or JERGA.search(_sin_marcadores(t))]
MENSAJES_REVISAR = sorted(i for i in vig_ids if (by[i].get('mensaje_usuario') or '') and _revisar_mensaje(by[i]['mensaje_usuario']))
# ---- ronda 4 · l_mensajes: avisos del corrector (bloque 4.5; no bloquean) y corpus de la ronda 4 (informativo) ----
_AV = getattr(AD, 'AVISOS_CORRECTOR', None)
_RXA = {k_: re.compile(v_, re.I) for k_, v_ in (_AV or {}).get('patrones', {}).items()}
def _avisos(t):
    t = _norm(re.sub(r'\{\{[^}]*\}\}', 'X', t))
    return sorted(k_ for k_, r_ in _RXA.items() if r_.search(t))
if _AV:
    P['cruces_lenguaje']['lenguaje']['avisos_pendientes_validacion'] = [
        dict(categoria=k_, patron=v_, efecto=_AV['efecto'], estado=_AV['estado'], origen=_AV['origen']) for k_, v_ in _AV['patrones'].items()]
    _AVISOS_MENSAJES = sorted(i for i in vig_ids if _avisos(by[i].get('mensaje_usuario') or ''))
    print(f"avisos del corrector ({_AV['estado']}): {len(_RXA)} patrones · mensajes vigentes con aviso: {_AVISOS_MENSAJES}")
_CR4 = os.path.join(C, 'pruebas', 'corpus_ronda4.json')
if os.path.exists(_CR4):
    _r4 = {'evaluadas': 0, 'aciertos_bloqueo': 0, 'aciertos_con_avisos': 0, 'falsos_positivos': [], 'no_detectadas': [],
           'no_bloqueadas_pero_con_aviso': [], 'avisos_sobre_correctas': [], 'categoria_incompleta': []}
    for _o in json.load(open(_CR4))['oraciones']:
        if _o['debe'] not in ('pasar', 'bloquear'): continue
        _c = set(_bloquea(_o['texto'])) | ({'jerga'} if JERGA.search(_sin_marcadores(_o['texto'])) else set()); _a = _avisos(_o['texto'])
        _r4['evaluadas'] += 1
        if _o['debe'] == 'pasar':
            if _a: _r4['avisos_sobre_correctas'].append([_o['id'], _a])
            if _c: _r4['falsos_positivos'].append([_o['id'], sorted(_c)]); continue
        elif not _c:
            if _a: _r4['no_bloqueadas_pero_con_aviso'].append([_o['id'], _a]); _r4['aciertos_con_avisos'] += 1
            else: _r4['no_detectadas'].append([_o['id'], _o.get('cat_esperada')])
            continue
        else:
            _f = [x for x in _o.get('cat_esperada', []) if x not in _c and not (x == 'causal' and 'causal/evaluativa' in _c)]
            if _f: _r4['categoria_incompleta'].append([_o['id'], _f])
        _r4['aciertos_bloqueo'] += 1; _r4['aciertos_con_avisos'] += 1
    print(f"corpus ronda 4 (informativo): bloqueo {_r4['aciertos_bloqueo']}/{_r4['evaluadas']} · con avisos {_r4['aciertos_con_avisos']}/{_r4['evaluadas']} · FP {len(_r4['falsos_positivos'])} · no detectadas {len(_r4['no_detectadas'])}")
# ---- ronda 4 · COM-07 (decisión del orquestador, 7/10/2026): el corpus del corrector es la unión de los tres archivos
#      (reserva, auditor y ronda 4), contando solo oraciones únicas. Una misma oración no puede tener veredictos distintos,
#      y la puerta de falsos positivos (tolerancia 0) cubre también las oraciones correctas de la ronda 4. Las oraciones de
#      la ronda 4 que deben bloquearse siguen siendo informativas: los 3 patrones nuevos solo avisan.
def _clave_corpus(t):  # auditoría final r4: minúsculas, sin tildes ni marcadores {{…}}/{…}, espacios simples
    return re.sub(r'\s+', ' ', _norm(re.sub(r'\{\{[^{}]*\}\}|\{\w+\}', 'X', t)).strip())
_CORPUS = collections.defaultdict(set)
for t in cr['pasan']: _CORPUS[_clave_corpus(t)].add('pasar')
for t in cr['bloquean']: _CORPUS[_clave_corpus(t)].add('bloquear')
for o in ca: _CORPUS[_clave_corpus(o['texto'])].add(o['debe'])
_O4 = json.load(open(_CR4))['oraciones'] if os.path.exists(_CR4) else []
for o in _O4: _CORPUS[_clave_corpus(o['texto'])].add(o['debe'])
for t, d in _CORPUS.items():
    if len(d) > 1: PRUEBAS.append(('corpus_veredictos_distintos', '-', t[:80]))
for o in _O4:
    if o['debe'] == 'pasar' and (_bloquea(o['texto']) or JERGA.search(_sin_marcadores(o['texto']))):
        PRUEBAS.append(('lexico_falso_positivo', '-', o['texto']))
CORPUS_UNICO = len(_CORPUS)
print(f'corpus del corrector (COM-07): {CORPUS_UNICO} oraciones únicas (reserva + auditor + ronda 4; meta 200) · '
      f'pruebas de consistencia: {len(PRUEBAS)}')
print('mensajes con jerga o muy largos (informativo):', len(MENSAJES_REVISAR))
TEXTOS_FIJOS_COINCIDEN = sorted({i for i in vig_ids if _bloquea(by[i].get('mensaje_usuario') or '')})
print('textos fijos que el corrector bloquearía si no fueran {{p:id}}:', len(TEXTOS_FIJOS_COINCIDEN))
print('parches v1.1 aplicados:', len(APLICADOS), '· renombres:', sum(RENOMBRADOS.values()))
# F1 y F3 (auditoría final r4): el estado pendiente no admite ventanas; ninguna ventana empieza antes del SINADEF (2017)
_sec_s = by['R-MOTOR-01']['parametros']['secuencia_degradacion']['fuente_sensible']
_per04 = by['R-REG-04']['parametros'].get('periodos_permitidos', [])
if _D_R4_1_OPC is None and (any('ventana' in x or '_anios' in x for x in _sec_s) or _per04 != ['año suelto']
                            or not DECISIONES_PENDIENTES):
    PRUEBAS.append(('d_r4_1_pendiente_con_ventanas', 'R-MOTOR-01/R-REG-04', str(_sec_s)))
_anios_v = [int(a) for v_ in _per04 if v_ != 'año suelto' for a in re.findall(r'\d{4}', v_)]
if _anios_v and min(_anios_v) < CA_INICIO_SINADEF:
    PRUEBAS.append(('ventana_antes_de_los_datos', 'R-REG-04', str(_per04)))
_tramos = [tuple(int(a) for a in re.findall(r'\d{4}', v_)) for v_ in _per04 if v_ != 'año suelto']
if any(b_[0] <= a_[1] for a_, b_ in zip(_tramos, _tramos[1:])):
    PRUEBAS.append(('ventanas_superpuestas', 'R-REG-04', str(_per04)))
# Decisiones del gasto, rondas 1–2: los patrones nuevos detectan sus casos y no bloquean los correctos; los ids de temas
# siguen la gramática de R-GASTO-08b; las alternativas apuntan a temas existentes.
_CG = getattr(AD, 'CASOS_CORRECTOR_GASTO_R2', {})
for t in _CG.get('bloquear', []):
    if not _bloquea(t): PRUEBAS.append(('gasto_r2_no_detectada', 'R-GASTO-15/08', t))
for t in _CG.get('pasar', []):
    if _bloquea(t) or JERGA.search(_sin_marcadores(t)): PRUEBAS.append(('gasto_r2_falso_positivo', 'R-GASTO-15/08', t))
for t in _CG.get('pasar_solo_patrones_nuevos', []):
    if _bloquea(t, solo=_NUEVOS_R2): PRUEBAS.append(('gasto_r2_falso_positivo', 'R-GASTO-15/08', t))
# Auditoría de la pieza B (hallazgo 3): ningún id de tema viejo o sin prefijo válido en las reglas vigentes (la justificación
# puede citarlos como historia); las llaves de grupos_objetivo de R-GASTO-11 son temas v1.2 o fuentes declaradas.
if hasattr(AD, 'TEMAS_VIEJOS'):
    _gr2 = re.compile(AD.GRAMATICA_TEMAS); _tm2 = by['R-GASTO-08']['parametros'].get('temas_iniciales', {})
    for i in sorted(vig_ids):
        for k_, v_ in by[i].items():
            if k_.startswith('_') or k_ in ('justificacion', 'id'): continue
            s_ = json.dumps(v_, ensure_ascii=False)
            for o_ in AD.TEMAS_VIEJOS:
                if re.search(r'(?<![A-Za-z0-9_])' + o_ + r'(?![A-Za-z0-9_])', s_): PRUEBAS.append(('tema_id_viejo', i, o_))
            for m_ in (re.finditer(r"\btema\s*==?\s*['\"]?([a-z][a-z0-9_]*)", s_) if i.startswith('R-GASTO-') else []):  # temas de dim_tema_gasto
                if not _gr2.match(m_.group(1)): PRUEBAS.append(('tema_sin_prefijo_valido', i, m_.group(1)))
    for k_ in by['R-GASTO-11']['parametros'].get('grupos_objetivo', {}):
        if k_ not in AD.CLAVES_NO_TEMA and not (_gr2.match(k_) and k_ in _tm2): PRUEBAS.append(('tema_sin_prefijo_valido', 'R-GASTO-11', k_))
if hasattr(AD, 'GRAMATICA_TEMAS'):
    _gr = re.compile(AD.GRAMATICA_TEMAS); _tm = by['R-GASTO-08']['parametros'].get('temas_iniciales', {})
    _ids_tema = list(_tm) + [v_ for x_ in by['R-GASTO-08b']['parametros']['map_intencion_tema'].values() for v_ in [x_['defecto'], x_.get('desglose')] + x_['contexto'] if v_ and not v_.startswith('ps_*')]
    for t_ in _ids_tema:
        if not _gr.match(t_): PRUEBAS.append(('tema_fuera_de_gramatica', 'R-GASTO-08/08b', t_))
        elif t_ not in _tm: PRUEBAS.append(('tema_sin_definir', 'R-GASTO-08b', t_))
    for t_, v_ in _tm.items():
        if v_.get('alternativa_de') and v_['alternativa_de'] not in _tm: PRUEBAS.append(('alternativa_inexistente', 'R-GASTO-08', t_))
        if AD.GRAMATICA_TEMAS and by['R-GASTO-08b']['parametros']['prefijo_cadena'][t_.split('_')[0]] != v_['cadena']: PRUEBAS.append(('prefijo_no_coincide_con_cadena', 'R-GASTO-08', t_))
# Hallazgo H8 (auditoría de la pieza C): toda tabla o vista de gasto que nombre una regla R-GASTO-* está publicada
# (manifiesto_s3_gasto.json y vistas SQL) o declarada como no publicada, con su motivo, en ajustes_dueno.py. Las listas de
# ajustes_dueno.py se comparan con el manifiesto y las vistas cuando esos archivos existen (en una copia sin la biblioteca
# solo se usan las listas).
if hasattr(AD, 'TABLAS_GASTO_PUBLICADAS'):
    _RAIZ = os.path.dirname(H)
    _man = os.path.join(_RAIZ, 'biblioteca', 'dimensiones', 'manifiesto_s3_gasto.json')
    _enc = set(getattr(AD, 'TABLAS_GASTO_EN_CONSTRUCCION', {}))  # 8/10/2026: pueden estar o no en el manifiesto
    if os.path.exists(_man) and (set(json.load(open(_man))['tablas']) - _enc) != set(AD.TABLAS_GASTO_PUBLICADAS):
        PRUEBAS.append(('manifiesto_gasto_distinto', '-', str(sorted((set(json.load(open(_man))['tablas']) - _enc) ^ set(AD.TABLAS_GASTO_PUBLICADAS)))))
    _sql = [os.path.join(_RAIZ, 'curados', 'capa0', f_) for f_ in ('vistas_gasto.sql', 'vistas_gasto_temas.sql')]
    if all(os.path.exists(f_) for f_ in _sql):
        _vs = {m_.lower() for f_ in _sql for m_ in re.findall(r'(?i)create\s+(?:or\s+replace\s+)?(?:view|macro)\s+([a-z_][a-z0-9_]*)', open(f_).read())}
        if _vs != set(AD.VISTAS_GASTO_PUBLICADAS): PRUEBAS.append(('vistas_gasto_distintas', '-', str(sorted(_vs ^ set(AD.VISTAS_GASTO_PUBLICADAS)))))
    _ok = set(AD.TABLAS_GASTO_PUBLICADAS) | set(AD.VISTAS_GASTO_PUBLICADAS) | set(AD.TABLAS_GASTO_NO_PUBLICADAS) | _enc
    for i in sorted(x for x in vig_ids if x.startswith('R-GASTO-')):
        s_ = json.dumps({k_: v_ for k_, v_ in by[i].items() if not k_.startswith('_')}, ensure_ascii=False)
        for t_ in sorted(set(re.findall(r'(?<![A-Za-z0-9_./])((?:dim|rel|fact|map|cobertura)_[a-z0-9_]+|v_gasto_[a-z0-9_]+)(?![A-Za-z0-9_])(?!\.(?:csv|parquet|yaml|json|sql|py)\b)', s_))):
            if t_ not in _ok: PRUEBAS.append(('tabla_gasto_no_publicada', i, t_))
# ---- decisiones del dueño del 8/10/2026 (E1: reglas). R-ENC-08 sin lista cerrada; R-DEP-01 contra insumos.lock.yaml y los
#      manifiestos de la capa 0; sin foto mensual del PIM; R-GASTO-03 (funciones del MEF, línea aparte y sesgo de sede);
#      Llamkasun con «transferido a municipalidades»; nombres por año iguales a programas_sociales.yaml. Los archivos de la
#      capa 0 se leen solo si existen (en la copia de prueba_guardia.py no están).
if hasattr(AD, 'BLOQUEANTES_MVP_D8'):
    import datetime as _dt
    _RAIZ8 = os.path.dirname(H)
    _e08 = by['R-ENC-08']['aplica_a']
    if _e08.get('fuentes') or _e08.get('tipo_medida') or _e08.get('base_geografica') or _e08.get('naturaleza_dato') != ['encuesta_muestral']:
        PRUEBAS.append(('enc08_lista_cerrada', 'R-ENC-08', json.dumps(_e08, ensure_ascii=False)))
    for i_ in ('R-ENC-06', 'R-ENC-07', 'R-ENC-15'):
        if by[i_]['aplica_a'].get('tipo_medida') or by[i_]['aplica_a'].get('base_geografica'): PRUEBAS.append(('enc_alcance_desigual', i_, 'tipo_medida/base_geografica'))
    if not all(x_ in by['R-ENC-08']['condicion'] for x_ in ('inferencia_verificada', 'modulo', 'cita_url', 'nivel_maximo', 'excluye_departamentos', 'aviso')):
        PRUEBAS.append(('enc08_sin_inferencia_verificada', 'R-ENC-08', 'condicion'))
    _CATF = {f_['id']: f_ for f_ in (json.load(open(CATALOGO))['fuentes'] if isinstance(json.load(open(CATALOGO)), dict) else json.load(open(CATALOGO)))}
    for f_ in by['R-ENC-08']['parametros']['verificar_antes_del_mvp']:
        if _CATF.get(f_, {}).get('naturaleza_dato') != 'encuesta_muestral': PRUEBAS.append(('enc08_fuente_no_muestral', 'R-ENC-08', f_))
    _bl = by['R-DEP-01']['parametros']['insumos_bloqueantes_mvp']; _ct = set(by['R-DEP-01']['parametros']['insumos_contraste_opcionales'])
    if len(_bl) != len(set(_bl)) or set(_bl) & _ct: PRUEBAS.append(('bloqueante_repetido_o_contraste', 'R-DEP-01', str(sorted(set(_bl) & _ct))))
    _lock = os.path.join(_RAIZ8, 'curados', 'insumos.lock.yaml')
    if os.path.exists(_lock):
        import yaml
        _LK = set(yaml.safe_load(open(_lock)))
        for f_ in _bl:
            if f_ not in _LK: PRUEBAS.append(('bloqueante_fuera_del_lock', 'R-DEP-01', f_))
        for t_, m_ in AD.TABLAS_CURADAS_BLOQUEANTES_D8.items():
            _mf = os.path.join(_RAIZ8, 'biblioteca', 'dimensiones', m_) if isinstance(m_, str) else None
            if _mf and not os.path.exists(_mf): continue
            _fs = set(m_) if not _mf else {x_['source_id'] for x_ in json.load(open(_mf))['insumos'] if x_['source_id'] in _LK}
            for f_ in sorted(_fs - _ct - set(_bl)): PRUEBAS.append(('insumo_capa0_no_bloqueante', 'R-DEP-01', f'{t_}: {f_}'))
    for f_ in _bl:
        if f_ not in CAT: PRUEBAS.append(('bloqueante_fuera_del_catalogo', 'R-DEP-01', f_))
    print('R-DEP-01: bloqueantes no aprobados hoy en el catálogo (informativo):', [f_ for f_ in _bl if _CATF.get(f_, {}).get('compuerta_ingesta') != 'aprobada'])
    _inf = os.path.join(os.path.dirname(CATALOGO), 'inferencia_verificada.csv')  # tabla del catálogo que lee R-ENC-08
    if os.path.exists(_inf):
        import csv
        _fi = list(csv.DictReader(open(_inf, encoding='utf-8')))
        _cu = by['R-ENC-08']['parametros']['registro_inferencia_verificada']['campos_que_usa_la_regla']
        for c_ in ['fuente', 'anio', 'modulo'] + _cu:
            if _fi and c_ not in _fi[0]: PRUEBAS.append(('inferencia_csv_sin_campo', 'R-ENC-08', c_))
        for x_ in _fi:
            if _CATF.get(x_['fuente'], {}).get('naturaleza_dato') != 'encuesta_muestral': PRUEBAS.append(('inferencia_fuente_no_muestral', 'R-ENC-08', x_['fuente']))
            if x_.get('inferencia_verificada') == 'true' and not all(x_.get(k_) for k_ in ('cita_url', 'cita_documento', 'cita_ubicacion')): PRUEBAS.append(('inferencia_true_sin_cita', 'R-ENC-08', f"{x_['fuente']} {x_['anio']} {x_['modulo']}"))
            if x_.get('inferencia_verificada') == 'true' and (x_.get('nivel_maximo') not in CA.NIVEL_RANK or x_.get('nivel_maximo') == 'nota'): PRUEBAS.append(('inferencia_nivel_fuera_de_vocabulario', 'R-ENC-08', f"{x_['fuente']} {x_['anio']}: {x_.get('nivel_maximo')}"))
            if x_.get('aviso') and x_['aviso'] not in by['R-ENC-08']['parametros'].get('avisos', {}): PRUEBAS.append(('inferencia_aviso_sin_texto', 'R-ENC-08', f"{x_['fuente']} {x_['anio']}: {x_['aviso']}"))
            for d_ in [t_.strip() for t_ in (x_.get('excluye_departamentos') or '').split(';') if t_.strip()]:
                if not re.fullmatch(r'(0[1-9]|1\d|2[0-5])', d_): PRUEBAS.append(('inferencia_departamento_invalido', 'R-ENC-08', f"{x_['fuente']} {x_['anio']}: {d_}"))
        print('R-ENC-08: filas sin verificar en inferencia_verificada.csv (informativo):', sorted({f"{x_['fuente']} {x_['anio']}" for x_ in _fi if x_.get('inferencia_verificada') != 'true'}))
    for i in sorted(x_ for x_ in vig_ids if x_.startswith('R-GASTO-')):
        s_ = json.dumps({k_: by[i].get(k_) for k_ in ('enunciado', 'condicion', 'parametros', 'implementacion', 'mensaje_usuario', 'ejemplo')}, ensure_ascii=False)
        for pat_ in (r'foto_pim\(', r'con_fotos', r'\(desde 2026\)', r'copia fechada', r'serie propia de fotos'):
            if re.search(pat_, s_): PRUEBAS.append(('foto_pim_en_regla', i, pat_))
    _l3 = by['R-GASTO-03']['parametros']['lima']
    if set(_l3.get('funciones_advertencia_obligatoria', {})) != {'05', '06', '15', '20', '23'}: PRUEBAS.append(('funciones_mixtas_distintas_a_la_decision', 'R-GASTO-03', str(_l3.get('funciones_advertencia_obligatoria'))))
    for k_, v_ in _l3.get('funciones_advertencia_obligatoria', {}).items():
        if AD.FUNCIONES_MEF.get(k_) != v_: PRUEBAS.append(('funcion_mef_inexistente', 'R-GASTO-03', f'{k_} {v_}'))
    if 'algunos programas nacionales' not in by['R-GASTO-03']['mensaje_usuario'] or not _l3.get('programas_mixtos_respaldo'):
        PRUEBAS.append(('mixtas_sin_respaldo', 'R-GASTO-03', 'texto sin lista'))
    for marca_ in ('{refnac}', '{pct_sede}', '{programas_mixtos}'):
        if marca_ not in by['R-GASTO-03']['mensaje_usuario']: PRUEBAS.append(('lima_sin_linea_obligatoria', 'R-GASTO-03', marca_))
    _c3 = json.dumps({k_: by['R-GASTO-03'].get(k_) for k_ in ('condicion', 'parametros', 'implementacion')}, ensure_ascii=False)
    _cl = next((x_ for x_ in CAMPOS if x_[0] == 'cuenta_en_lima'), ('', '', '', ''))[3]
    for t_ in ('obra_sede_nacional', 'lima_departamento'):  # definición de cuenta_en_lima (E3)
        if t_ not in _c3 or t_ not in _cl: PRUEBAS.append(('cuenta_en_lima_incompleta', 'R-GASTO-03', t_))
    _ps8 = by['R-GASTO-08']['parametros'].get('temas_ps', {}).get('ps_empleo_temporal', {})
    if _ps8.get('linea_obligatoria') != 'transferido a municipalidades' or 'transferido a municipalidades' not in by['R-GASTO-08']['mensaje_usuario'].lower():
        PRUEBAS.append(('llamkasun_sin_linea_transferido', 'R-GASTO-08', 'ps_empleo_temporal'))
    _ys = os.path.join(_RAIZ8, 'curados', 'capa0', 'trazabilidad', 'programas_sociales.yaml')
    if os.path.exists(_ys):
        import yaml
        _PS8 = {p_['id']: p_ for p_ in yaml.safe_load(open(_ys))['programas']}
        def _f8(s):
            p_ = [int(x_) for x_ in str(s).split('-')]
            return _dt.date(p_[0], 1, 1) if len(p_) == 1 else _dt.date(p_[0], p_[1], 1) if len(p_) == 2 else _dt.date(*p_)
        def _fr8(d_, mes_): return f'{AD.MESES[d_.month - 1]} de {d_.year}' if mes_ else f'el {d_.day}/{d_.month}/{d_.year}'
        def _etiqueta8(nombres, anio):  # misma regla que trazabilidad.etiqueta_programa_social (sin el nombre del MEF)
            ef_, prev_ = [], _dt.date(1900, 1, 1)
            for n_ in nombres: prev_ = _f8(n_['desde']) if n_.get('desde') else prev_; ef_.append(prev_)
            vig_ = []
            for j_, n_ in enumerate(nombres):
                fin_ = ef_[j_ + 1] - _dt.timedelta(days=1) if j_ + 1 < len(nombres) else _dt.date(9999, 12, 31)
                a_, b_ = max(ef_[j_], _dt.date(anio, 1, 1)), min(fin_, _dt.date(anio, 12, 31))
                if a_ <= b_: vig_.append((n_['nombre'], (b_ - a_).days + 1, n_, ef_[j_], fin_))
            pr_ = max(vig_, key=lambda x_: x_[1])
            otros_ = [f"{v_[0]} hasta {_fr8(v_[4], (vig_[k_ + 1][2] if k_ + 1 < len(vig_) else {}).get('rotulo_fecha') == 'mes')}" if v_[3] < pr_[3]
                      else f"{v_[0]} desde {_fr8(v_[3], v_[2].get('rotulo_fecha') == 'mes')}" for k_, v_ in enumerate(vig_) if v_[0] != pr_[0]]
            return pr_[0] + (f" ({'; '.join(otros_)})" if otros_ else '')
        for nm_, e_ in by['R-GASTO-08']['parametros']['nombres']['mef_vs_vigente'].items():
            p_ = _PS8.get(e_['programa_social'])
            if not p_: PRUEBAS.append(('programa_social_inexistente', 'R-GASTO-08', e_['programa_social'])); continue
            for a_, et_ in e_['por_anio'].items():
                if _etiqueta8(p_['nombres'], int(a_)) != et_: PRUEBAS.append(('nombre_vigente_no_coincide', 'R-GASTO-08', f"{e_['programa_social']} {a_}: {et_} ≠ {_etiqueta8(p_['nombres'], int(a_))}"))
if hasattr(AD, 'PRUEBAS_LIMA_L'): PRUEBAS += AD.PRUEBAS_LIMA_L(by, vig_ids, CA.NIVEL_RANK, CAMPOS, DECISIONES, _E, JERGA, _MAX, _textos_mensaje, _sin_marcadores, os.path.dirname(H))  # Lima en tres ámbitos, 9/10/2026
if hasattr(AD, 'PRUEBAS_P0'): PRUEBAS += AD.PRUEBAS_P0(by, os.path.dirname(H))  # piloto P0, 10/10/2026
[print('  fallida:', p) for p in PRUEBAS if p[0] != 'insumo_inexistente']
assert not [p for p in PRUEBAS if p[0] != 'insumo_inexistente'], 'pruebas de consistencia fallidas'
if os.path.exists(_CR4):
    json.dump(_r4, open(os.path.join(C, 'pruebas', 'resultado_corpus_ronda4.json'), 'w'), ensure_ascii=False, indent=1)
# ---------- JSON consolidado ----------
reglas = []
for et, (tit, _, ids) in ETAPAS.items():
    for i in ids:
        r = {k: v for k, v in by[i].items() if not k.startswith('_')}
        r['etapa'] = et; r['ambito_origen'] = by[i]['_origen']; r['estado'] = 'vigente'
        r['absorbe'] = [k for k, (v, _) in ABSORBIDAS.items() if v == i]
        if i in AJUSTES: r['ajuste_consolidacion'] = AJUSTES[i]
        r['origen_regla'] = by[i]['_origen'] if by[i]['_origen'] in ('prueba', 'auditoria', 'decisiones_gasto_r2', 'decisiones_m1') else 'propuesta'
        reglas.append(r)
for k, (v, mot) in ABSORBIDAS.items():
    r = {kk: vv for kk, vv in by[k].items() if not kk.startswith('_')}; r.update(estado='absorbida', absorbida_por=v, motivo_absorcion=mot, ambito_origen=by[k]['_origen'])
    reglas.append(r)
out = {'version': '1.1-borrador', 'mensajes_por_revisar_jerga_longitud': MENSAJES_REVISAR if 'MENSAJES_REVISAR' in dir() else [], 'textos_fijos_protegidos': TEXTOS_FIJOS_COINCIDEN if 'TEXTOS_FIJOS_COINCIDEN' in dir() else [], 'veredictos_auditoria': {k: dict(veredicto=v[0], nota=v[1]) for k, v in CA.VEREDICTOS.items()}, 'semantica_aplica_a': CP.SEMANTICA_APLICA_A, 'pruebas_consistencia': [dict(tipo=a, regla=b, valor=c) for a, b, c in PRUEBAS], 'fecha': _FECHA, 'parametros_globales': {'NIVEL_RANK': CA.NIVEL_RANK, 'anios_choque': [2020, 2021], 'nivel_confianza': 0.95, 'alfa': 0.05,
       'excepcion_choque': 'pobreza monetaria ENAHO (comparable según Comisión Consultiva INEI)', **getattr(AD, 'PARAMETROS_GLOBALES_P0', {})},
       'etapas': {k: {'titulo': v[0], 'proposito': v[1], 'reglas': v[2]} for k, v in ETAPAS.items()},
       'reglas': reglas, 'conflictos_resueltos': [dict(id=a, conflicto=b, resolucion=c) for a, b, c in CONFLICTOS],
       'campos': [dict(campo=a, nivel=b, reemplaza=c, para_que=e) for a, b, c, e in CAMPOS],
       'decisiones': [dict(id=a, tema=b, opciones=c, recomendacion=d, reglas=e, decision=f) for a, b, c, d, e, f in DECISIONES],
       'decisiones_pendientes': DECISIONES_PENDIENTES,
       'ficha_limites': P['cruces_lenguaje']['ficha_limites'], 'lenguaje': P['cruces_lenguaje']['lenguaje'],
       'especificaciones': P['territorio_denominadores']['especificaciones'],
       # Las preguntas abiertas de las propuestas de la fase 2 ya se respondieron (D1–D24); las decisiones vigentes y las
       # pendientes del dueño están en un solo registro (consolidado el 2/11/2026).
       'registro_decisiones': 'docs/decisiones.md'}
json.dump(out, open(os.path.join(OUT, 'reglas.json'), 'w'), ensure_ascii=False, indent=1)

# ---------- Markdown ----------
def c(v):
    if v in (None, '', []): return '—'
    if isinstance(v, (dict, list)): v = json.dumps(v, ensure_ascii=False)
    return str(v).replace('|', '\\|').replace('\n', ' ')
L = []; A = L.append
vig = [r for r in reglas if r['estado'] == 'vigente']
A('# Reglas de publicación y atribución — Pregúntale al Perú\n')
if _D_R4_1_OPC is None:
    A('> **Decisión pendiente D-R4-1** (años de las celdas sensibles de mortalidad: RMM, TMI y TMN). El dueño aún no '
      'decide entre A (no sumar años), B (periodos fijos de 5 años) y C (periodos fijos de 3 años); el interruptor '
      '`D_R4_1` está en `None` y se aplica el estado seguro (solo años sueltos, sin ventanas de varios años por debajo '
      'del nivel nacional). Ver `decisiones_pendientes` en reglas.json, la tabla de decisiones y '
      '`auditoria/ronda4/explicacion_D-R4-1.md`.\n')
A(f'Versión 1.1 (corregida tras la prueba con 12 preguntas reales y la auditoría independiente) · {_FECHA_TXT} · **{len(vig)} reglas vigentes** ({sum(r["prioridad"] == "mvp" for r in vig)} para el MVP) · {len(ABSORBIDAS)} absorbidas por duplicado. '
  'Detalle completo de cada regla (condición, parámetros, implementación, casos borde, referencias) en `reglas.json`.\n')
A('## 1. Cómo se aplican\n')
A('El motor calcula las cifras; el **validador de reglas** las revisa en este orden antes de que el redactor (LLM) las vea. '
  'Cada etapa puede publicar, marcar como referencial, subir de nivel, agrupar años, suprimir o bloquear un cruce. '
  'El resultado alimenta el semáforo y la ficha de límites, y el redactor solo puede usar las cifras que sobreviven.\n')
A('```')
for k, (t, p, ids) in ETAPAS.items(): A(f'{k.split("_")[0]:>2}. {t:<34} {p}')
A('```\n')
A('**' + CP.SEMANTICA_APLICA_A + '**\n')
A('El semáforo de cada cifra (etapa 7) se calcula antes de los cruces; el de la respuesta (etapa 9), después. Si una cifra se suprime en las etapas 2–4, el motor la degrada con la secuencia única de R-MOTOR-01 y vuelve a evaluarla.\n')
A('**Parámetros globales:** confianza 95 %, α = 0,05, años de choque 2020–2021 (excepción: pobreza monetaria ENAHO, declarada comparable por el INEI).\n')
for k, (t, p, ids) in ETAPAS.items():
    A(f'## {k[0] if k[0].isdigit() else ""}{"" if not k[0].isdigit() else "."} {t}\n'.replace('## 1.', '## 2.' if False else '## 1.'))
    L[-1] = f'## Etapa {k.split("_")[0]} · {t}\n'
    A(f'{p}.\n')
    A('| ID | Regla | Acción | Umbrales | Mensaje al usuario |'); A('|---|---|---|---|---|')
    for i in ids:
        r = by[i]; ab = [x for x, (v, _) in ABSORBIDAS.items() if v == i]
        tit = f"**{c(r['titulo'])}**{' *(posterior)*' if r['prioridad'] != 'mvp' else ''}. {c(r['enunciado'])}"
        if ab: tit += f" *Absorbe {', '.join(ab)}.*"
        if i in AJUSTES: tit += f" *Ajuste: {c(AJUSTES[i])}*"
        if r.get('hallazgos_prueba'): tit += f" *{'Nueva' if r.get('_origen') == 'prueba' else 'Corregida'} tras la prueba: {', '.join(r['hallazgos_prueba'])}.*"
        if r.get('hallazgos_auditoria_v11') or r.get('_origen') == 'auditoria': tit += f" *{'Nueva' if r.get('_origen') == 'auditoria' else 'Corregida'} en la auditoría v1.1: {', '.join(r.get('hallazgos_auditoria_v11') or r.get('hallazgos_prueba') or [])}.*"
        if r.get('hallazgos_ronda3'): tit += f" *Corregida en la ronda 3 (Ola 0): {', '.join(r['hallazgos_ronda3'])}.*"
        if r.get('decisiones_dueno_2026_10_08'): tit += f" *Corregida por las decisiones del dueño del 8/10/2026: {'; '.join(r['decisiones_dueno_2026_10_08'])}.*"
        if r.get('decisiones_dueno_2026_10_09'): tit += f" *Corregida por las decisiones del dueño del 9/10/2026 (Lima en tres ámbitos): {'; '.join(r['decisiones_dueno_2026_10_09'])}.*"
        if r.get('decisiones_gasto_r2'): tit += f" *{'Nueva' if r.get('_origen') == 'decisiones_gasto_r2' else 'Corregida'} en las decisiones del gasto (rondas 1–2, 7/10/2026): {', '.join(r['decisiones_gasto_r2'])}.*"
        par = r.get('parametros') or {}
        par_txt = '; '.join(f'{k2}: {c(v2)[:90]}' for k2, v2 in list(par.items())[:4]) if isinstance(par, dict) else c(par)[:200]
        A(f"| `{i}` | {tit} | {c(r['accion'])} | {par_txt} | {c(r.get('mensaje_usuario'))[:220]} |")
    A('')
A('## Conflictos resueltos en la consolidación\n')
A('| # | Conflicto | Resolución |'); A('|---|---|---|')
for a, b, cc in CONFLICTOS: A(f'| {a} | {b} | {cc} |')
A('')
A('## Diccionario unificado de campos nuevos\n')
A('Los cinco ámbitos propusieron 82 campos; muchos eran el mismo con otro nombre. Este es el diccionario único que usará la biblioteca.\n')
A('| Campo | Nivel | Reemplaza a | Para qué |'); A('|---|---|---|---|')
for a, b, cc, e in CAMPOS: A(f'| `{a}` | {b} | {cc} | {e} |')
A('')
A('## Auditoría v1.1: veredictos\n')
A('Cuatro auditores independientes (estadística, implementación, hechos y fuentes, comunicación y privacidad) revisaron la v1.0: 59 hallazgos. '
  'Veredictos: A = aceptado; AA = aceptado con ajuste del orquestador; F = aceptado y toca una decisión del dueño. Detalle de cada hallazgo en `auditoria/hallazgos/`.\n')
A('| Hallazgo | Veredicto | Nota |'); A('|---|---|---|')
for k_, (v_, n_) in sorted(CA.VEREDICTOS.items()): A(f'| {k_} | {v_} | {c(n_)} |')
A('')
A('## Decisiones del dueño del proyecto\n')
A('| # | Tema | Opciones | Recomendación | Reglas | Decisión |'); A('|---|---|---|---|---|---|')
for a, b, cc, d, e, f in DECISIONES: A(f'| {a} | {b} | {cc} | {d} | {e} | {f} |')
A('')
open(os.path.join(OUT, 'reglas.md'), 'w').write('\n'.join(L))

# ---------- ficha de límites ----------
F = out['ficha_limites']; Lg = out['lenguaje']
L = []; A = L.append
A('# Ficha de límites y reglas de lenguaje\n')
A('Plantilla que acompaña cada respuesta (R-LENGUAJE-01). La genera el sistema desde el resultado del validador; el LLM no la redacta.\n')
A('## Principios\n'); [A(f'- {x}') for x in F.get('principios', [])]; A('')
A('## Versión corta (siempre visible)\n'); A('| Campo | Texto |'); A('|---|---|')
for x in F['corta']['campos']: A(f"| `{x['campo']}` | {c(x['texto'])} |")
A('\n**Ejemplo:**\n'); A('```'); A(F['corta'].get('ejemplo', '')); A('```\n')
A('## Versión larga (desplegable)\n')
for s in F['larga']['secciones']:
    A(f"### {s['seccion']}\n"); A(f"Plantilla: {c(s.get('texto_plantilla'))}\n")
    for k2, v2 in s.items():
        if k2 in ('seccion', 'texto_plantilla', 'campos'): continue
        if isinstance(v2, dict):
            A(f'**{k2}**\n'); A('| Caso | Texto |'); A('|---|---|'); [A(f'| `{a}` | {c(b)} |') for a, b in v2.items()]; A('')
        elif isinstance(v2, list):
            A(f'**{k2}**\n'); [A(f'- {c(x)}') for x in v2]; A('')
    if s.get('codigos'):
        A('| Código | Texto | Cuándo |'); A('|---|---|---|')
        for x in s['codigos']: A(f"| `{c(x.get('codigo'))}` | {c(x.get('texto'))} | {c(x.get('cuando') or x.get('condicion'))} |")
        A('')
for k2, v2 in F.items():
    if k2 not in ('principios', 'corta', 'larga'):
        A(f'### {k2}\n'); A('```json'); A(json.dumps(v2, ensure_ascii=False, indent=1)[:6000]); A('```\n')
A('## Lenguaje\n'); A('### Expresiones permitidas\n'); A('| Expresión | Uso |'); A('|---|---|')
for x in Lg.get('permitidas', []): A(f"| {c(x.get('expresion'))} | {c(x.get('uso'))} |")
A('\n### Patrones prohibidos (los revisa un corrector automático)\n'); A('| Categoría | Patrón | Reemplazo | Excepción |'); A('|---|---|---|---|')
for x in Lg.get('prohibidas', []): A(f"| {c(x.get('categoria'))} | `{c(x.get('patron'))}` | {c(x.get('reemplazo'))} | {c(x.get('excepcion'))} |")
A('')
for k2, v2 in Lg.items():
    if k2 not in ('permitidas', 'prohibidas'):
        A(f'### {k2}\n'); A('```json'); A(json.dumps(v2, ensure_ascii=False, indent=1)[:5000]); A('```\n')
open(os.path.join(OUT, 'ficha_limites_y_lenguaje.md'), 'w').write('\n'.join(L))

# ---------- especificaciones ----------
E = out['especificaciones']; L = []; A = L.append
A('# Especificaciones de tablas de la capa 0\n'); A('Propuestas por el ámbito territorio y denominadores (fase 2). La tabla de ubigeo histórico la construye el proyecto (decisión del 5/10/2026).\n')
for nombre, spec in E.items():
    A(f'## {nombre}\n')
    if isinstance(spec, dict):
        if spec.get('proposito'): A(spec['proposito'] + '\n')
        if spec.get('columnas'):
            A('| Columna | Tipo | Regla |'); A('|---|---|---|')
            for col in spec['columnas']: A(f"| `{c(col.get('columna'))}` | {c(col.get('tipo'))} | {c(col.get('regla'))} |")
            A('')
        for k2, v2 in spec.items():
            if k2 in ('proposito', 'columnas'): continue
            A(f'**{k2}**\n')
            if isinstance(v2, list): [A(f'- {c(x)}') for x in v2]; A('')
            else: A(c(v2) + '\n')
    else: A(c(spec) + '\n')
A('## Notas de verificación\n'); [A(f'- {x}') for x in P['territorio_denominadores'].get('notas_verificacion', [])]
if getattr(AD, 'ANEXO_ESPECIFICACIONES', None): A(AD.ANEXO_ESPECIFICACIONES.rstrip('\n'))  # secciones agregadas por capas posteriores (S4)
open(os.path.join(OUT, 'especificaciones_capa0.md'), 'w').write('\n'.join(L))
print('vigentes', len(vig), 'absorbidas', len(ABSORBIDAS), 'mvp', sum(r['prioridad'] == 'mvp' for r in vig))
