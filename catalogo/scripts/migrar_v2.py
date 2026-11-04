"""Migración automática del catálogo v0.3 al esquema v2 (responde a A-10, A-07, C-06 de la auditoría)."""
import re

ANIO_REF = 2026
FECHA_REF = '2026-10-05'

LIC = [  # (regex, código, permite_redistribucion)
    (r'odbl', 'ODbL-1.0', True), (r'odc[- ]?by', 'ODC-By-1.0', True),
    (r'by[- ]nc[- ]sa', 'CC-BY-NC-SA-4.0', False), (r'by[- ]nc.*igo', 'CC-BY-NC-3.0-IGO', False), (r'by[- ]nc', 'CC-BY-NC-4.0', False),
    (r'cc[- ]?by.*igo', 'CC-BY-3.0-IGO', True), (r'cc[- ]?by 3', 'CC-BY-3.0', True), (r'cc[- ]?by', 'CC-BY-4.0', True),
    (r'cc0', 'CC0-1.0', True), (r'public domain|dominio p', 'PDDL-1.0', True), (r'^mit', 'MIT', True), (r'apache', 'Apache-2.0', True),
    (r'restringid', 'restringido', False), (r'no especificad|not spec', 'no-especificada', None),
    (r'otr[oa] \(abiert|otra \(abierta|abierta', 'otra-abierta', True), (r'uso libre|cita', 'uso-libre-con-cita', True),
]
URL_OK = re.compile(r'^https?://\S+$')

def licencia(txt):
    if not txt: return 'no-especificada', None, None
    t = txt.lower()
    for rx, code, red in LIC:
        if re.search(rx, t): return code, txt, red
    return 'no-especificada', txt, None

def norm_url(u):
    if not u: return u
    u = u.strip()
    u = re.sub(r'^https?://datosabiertos\.gob\.pe', 'https://www.datosabiertos.gob.pe', u)
    u = re.sub(r'^http://www\.datosabiertos\.gob\.pe', 'https://www.datosabiertos.gob.pe', u)
    return u

def anios(txt):
    ys = [int(y) for y in re.findall(r'(?<!\d)(19[5-9]\d|20[0-4]\d)(?!\d)', txt or '')]
    if not ys: return None, None, False
    fut = [y for y in ys if y > ANIO_REF]
    pas = [y for y in ys if y <= ANIO_REF]
    es_proy = bool(fut) and bool(re.search(r'proyecc|horizonte|meta|plan', txt or '', re.I))
    if not pas: return min(ys), max(ys), True
    return min(pas), (max(ys) if es_proy else max(pas)), es_proy

def base_geo(r):
    nat = r['naturaleza_dato']; uo = (r.get('unidad_observacion') or '').lower(); niv = r.get('nivel_territorial_disponible')
    if nat == 'encuesta_muestral': return 'muestra'
    if nat == 'censo': return 'residencia'
    if nat == 'presupuestal_financiero': return 'ejecutora'
    if nat == 'estimacion_modelada': return 'residencia'
    if nat in ('catalogo_portal',): return 'no_aplica'
    if nat == 'geoespacial': return 'territorio'
    if nat == 'registro_administrativo':
        if re.search(r'ruc|empresa|contribuyente', uo): return 'domicilio_fiscal'
        if re.search(r'denuncia|emergencia|defunci|fallec|caso|delito|accidente', uo): return 'ocurrencia'
        if niv == 'establecimiento' or re.search(r'establecimiento|ipress|instituci[oó]n educativa|\bie\b|local escolar|atenci', uo): return 'establecimiento'
        if re.search(r'proyecto|inversi|obra', uo): return 'inversion_ubicacion'
    return None

def tipo_medida(r):
    nat = r['naturaleza_dato']; t = r['tematica_principal']
    if nat in ('encuesta_muestral', 'censo'): return 'prevalencia'
    if nat == 'presupuestal_financiero': return 'presupuesto_gasto'
    if nat == 'estimacion_modelada': return 'estimacion_modelada'
    if nat == 'registro_administrativo':
        if t == 'programas_sociales': return 'cobertura_programa'
        if t == 'salud': return 'atenciones_produccion'
        if t in ('inversion_publica', 'contrataciones_publicas'): return 'presupuesto_gasto'
    return None

def migrar(d):
    out = []
    for r in d:
        r = dict(r)
        # estado de verificación
        r['estado_portal'] = r.pop('estado_enlace', None) or ('confirmado_busqueda' if r.get('verificado') else 'confirmado_busqueda')
        r.pop('verificado', None)
        r['estado_datos'] = 'sin_probar'
        r['fecha_verificacion'] = FECHA_REF if r['estado_portal'] == 'confirmado_navegador' else None
        # URLs: separar literal de plantilla, normalizar host PNDA
        for k in ('url_portal', 'url_documentacion'):
            r[k] = norm_url(r.get(k))
            if r[k] and not URL_OK.match(r[k]):
                r['detalle_descarga'] = ((r.get('detalle_descarga') or '') + f' [{k} original: {r[k]}]').strip(); r[k] = None
        u = norm_url(r.get('url_datos')); r['url_patron'] = None
        if u and not URL_OK.match(u):
            m = re.search(r'(https?://|s3://)\S+', u)
            tok = m.group(0).rstrip('),;') if m else None
            if tok and re.search(r'<|\{', tok):
                r['url_patron'] = re.sub(r'<A[ÑN]O>|\{A[ÑN]O\}', '{anio}', tok); u = None
            elif tok and tok.startswith('http'):
                u = tok
            else:
                u = None
            r['detalle_descarga'] = ((r.get('detalle_descarga') or '') + f' [url_datos original: {r.get("url_datos")}]').strip()
        r['url_datos'] = u
        # años tipados
        a0, a1, proy = anios(r.get('cobertura_temporal'))
        r['anio_inicio'], r['anio_fin'], r['es_proyeccion'] = a0, a1, proy
        r['fecha_ultimo_dato'] = None
        per = (r.get('periodicidad') or '').lower()
        r['serie_activa'] = False if re.search(r'única|unica|discontinu|cerrad|histór', per) else (True if (a1 and a1 >= 2024) else None)
        r['anios_con_quiebre'] = None
        # licencia
        r['licencia'], r['licencia_texto'], r['permite_redistribucion'] = licencia(r.get('licencia'))
        # vocabulario de llaves
        r['llaves_cruce'] = [{'pliego_unidad_ejecutora': 'pliego_unidad_ejecutora (sec_ejec)', 'dni': 'dni (restringido)'}.get(k, k) for k in (r.get('llaves_cruce') or [])]
        # inferencia solo para encuestas y estimaciones
        if r['naturaleza_dato'] not in ('encuesta_muestral', 'estimacion_modelada'):
            r['nivel_territorial_inferencia'] = None
        r['base_geografica'] = base_geo(r); r['tipo_medida'] = tipo_medida(r)
        # trazabilidad de fusiones
        r['ids_fusionados'] = re.findall(r'\[Fusionado con registro ([A-Z0-9-]+)\]', r.get('notas') or '')
        r['id_ruta_principal'] = None
        r['tematicas_secundarias'] = [t for t in (r.get('tematicas_secundarias') or []) if t != r['tematica_principal']]
        for k in ('origen', 'capa', 'ola', 'puntaje_prioridad', 'motivo_ola'): r.pop(k, None)
        out.append(r)
    return out
