"""Validaciones del catálogo v2 (A-10 / INT-14). Uso: python3 test_catalogo.py  (o pytest test_catalogo.py).
Errores = bloquean la publicación; advertencias = se reportan."""
import json, re, os, collections, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
V = {
 'tematica_principal': set('presupuesto_finanzas_publicas inversion_publica contrataciones_publicas pobreza_condiciones_vida salud nutricion_anemia educacion empleo_ingresos programas_sociales poblacion_demografia vivienda_servicios_basicos agricultura_desarrollo_rural ambiente_recursos_naturales riesgo_desastres_clima seguridad_ciudadana_justicia genero_violencia gobernanza_transparencia_corrupcion elecciones_participacion conflictos_sociales pueblos_indigenas_cultura economia_empresas_produccion mineria_energia_hidrocarburos transporte_infraestructura territorio_cartografia inclusion_financiera ciencia_tecnologia_digital turismo identidad_migracion multitematica'.split()),
 'naturaleza_dato': set('encuesta_muestral censo registro_administrativo presupuestal_financiero geoespacial indicadores_derivados estimacion_modelada catalogo_portal'.split()),
 'territorio': set('nacional departamento provincia distrito centro_poblado manzana_conglomerado establecimiento punto_coordenadas dominio'.split()),
 'estrategia_descarga': set('api_rest api_ckan descarga_directa_url descarga_manual scraping_html scraping_dinamico geoservicio solicitud_acceso_informacion convenio'.split()),
 'llaves': set(['ubigeo_inei', 'ubigeo_reniec', 'codigo_centro_poblado', 'conglomerado_vivienda', 'codigo_modular_ie', 'codigo_local_escolar', 'codigo_renipress_ipress', 'cui_inversion', 'codigo_snip', 'pliego_unidad_ejecutora (sec_ejec)', 'clasificador_presupuestal (función/programa/genérica)', 'ruc', 'dni (restringido)', 'codigo_cuenca', 'coordenadas', 'otro']),
 'base_geografica': set('residencia establecimiento ejecutora meta_departamento inversion_ubicacion domicilio_fiscal ocurrencia muestra territorio no_aplica'.split()),
 'tipo_medida': set('prevalencia cobertura_programa atenciones_produccion notificacion_vigilancia registro_eventos stock_infraestructura presupuesto_gasto estimacion_modelada padron_referencia otro'.split()),
 'licencia': set('ODC-By-1.0 ODbL-1.0 CC-BY-4.0 CC-BY-3.0 CC-BY-3.0-IGO CC-BY-NC-4.0 CC-BY-NC-3.0-IGO CC-BY-NC-SA-4.0 CC0-1.0 PDDL-1.0 MIT Apache-2.0 otra-abierta uso-libre-con-cita restringido no-especificada'.split()),
 'estado_portal': {'confirmado_busqueda', 'confirmado_navegador', 'no_responde'},
 'estado_datos': {'sin_probar', 'descarga_ok', 'enlace_confirmado', 'descarga_falla', 'sin_descarga_publica'},
 'ola': {'0_base', '1_nucleo', '2_expansion', '3_complementaria', 'referencia', 'ruta_alterna', 'infraestructura_acceso', 'fuera_de_alcance'},
}
CAMPOS = ['id', 'nombre', 'sigla', 'descripcion', 'tematica_principal', 'tematicas_secundarias', 'subtemas', 'entidad', 'sector', 'unidad_organica',
 'naturaleza_dato', 'tipo_acceso', 'unidad_observacion', 'cobertura_geografica', 'nivel_territorial_disponible', 'nivel_territorial_inferencia',
 'base_geografica', 'tipo_medida', 'desagregaciones', 'llaves_cruce', 'periodicidad', 'cobertura_temporal', 'anio_inicio', 'anio_fin',
 'fecha_ultimo_dato', 'es_proyeccion', 'serie_activa', 'anios_con_quiebre', 'rezago_publicacion', 'formatos', 'url_portal', 'url_datos', 'url_patron',
 'url_documentacion', 'estrategia_descarga', 'detalle_descarga', 'requiere_registro', 'licencia', 'licencia_texto', 'permite_redistribucion',
 'limitaciones', 'prioridad_mvp', 'estado_portal', 'estado_datos', 'fecha_verificacion', 'ids_fusionados', 'id_ruta_principal',
 'origen', 'capa', 'ola', 'puntaje_prioridad', 'motivo_ola', 'compuerta_ingesta', 'base_aprobacion', 'estado_ingesta', 'notas']
URL = re.compile(r'^https?://\S+$')
AUTO = {'descarga_directa_url', 'api_rest', 'api_ckan', 'geoservicio'}

def revisar(d):
    E, W = [], []
    ids = collections.Counter(r['id'] for r in d)
    E += [f'id duplicado: {i}' for i, n in ids.items() if n > 1]
    idset = set(ids)
    for r in d:
        i = r['id']; core = r.get('ola') in ('0_base', '1_nucleo')
        if not re.match(r'^[A-Z0-9]+(-[A-Z0-9]+)+$', i): E.append(f'{i}: id fuera de convención')
        falt = [c for c in CAMPOS if c not in r]
        if falt: E.append(f'{i}: faltan campos {falt}')
        for c, voc in (('tematica_principal', 'tematica_principal'), ('naturaleza_dato', 'naturaleza_dato'), ('estrategia_descarga', 'estrategia_descarga'),
                       ('licencia', 'licencia'), ('estado_portal', 'estado_portal'), ('estado_datos', 'estado_datos'), ('ola', 'ola')):
            if r.get(c) not in V[voc]: E.append(f'{i}: {c}={r.get(c)!r} fuera de vocabulario')
        for c in ('nivel_territorial_disponible', 'nivel_territorial_inferencia'):
            if r.get(c) is not None and r[c] not in V['territorio']: E.append(f'{i}: {c}={r[c]!r} fuera de vocabulario')
        for c, voc in (('base_geografica', 'base_geografica'), ('tipo_medida', 'tipo_medida')):
            if r.get(c) is not None and r[c] not in V[voc]: E.append(f'{i}: {c}={r[c]!r} fuera de vocabulario')
            if r.get(c) is None and core: E.append(f'{i}: {c} vacío en ola {r["ola"]}')
        mal = [k for k in r.get('llaves_cruce') or [] if k not in V['llaves']]
        if mal: E.append(f'{i}: llaves fuera de vocabulario {mal}')
        for c in ('url_portal', 'url_datos', 'url_documentacion'):
            if r.get(c) and not URL.match(r[c]): E.append(f'{i}: {c} no es URL: {r[c][:60]}')
            if r.get(c) and re.match(r'^https?://datosabiertos\.gob\.pe', r[c]): E.append(f'{i}: {c} usa el host PNDA sin www')
        if r.get('estrategia_descarga') in AUTO and not (r.get('url_datos') or r.get('url_patron')):
            (E if core else W).append(f'{i}: estrategia automatizable sin url_datos ni url_patron')
        a0, a1 = r.get('anio_inicio'), r.get('anio_fin')
        if a0 and a1 and a0 > a1: E.append(f'{i}: anio_inicio > anio_fin')
        if a1 and a1 > 2026 and not r.get('es_proyeccion'): E.append(f'{i}: anio_fin {a1} futuro sin es_proyeccion')
        if r.get('nivel_territorial_inferencia') and r.get('naturaleza_dato') not in ('encuesta_muestral', 'estimacion_modelada'):
            E.append(f'{i}: nivel de inferencia en un registro/censo/presupuesto')
        if r.get('id_ruta_principal') and r['id_ruta_principal'] not in idset: E.append(f'{i}: id_ruta_principal inexistente')
        if r.get('tematica_principal') in (r.get('tematicas_secundarias') or []): W.append(f'{i}: temática principal repetida en secundarias')
        if core:
            if not r.get('entidad'): E.append(f'{i}: sin entidad en ola {r["ola"]}')
            if r.get('licencia') == 'no-especificada': W.append(f'{i}: licencia no especificada en ola {r["ola"]}')
            if r.get('compuerta_ingesta') in ('pendiente_prueba', 'bloqueada'): W.append(f'{i}: compuerta {r["compuerta_ingesta"]}')
            if not r.get('anio_fin'): W.append(f'{i}: sin anio_fin en ola {r["ola"]}')
    urls = collections.defaultdict(list)
    for r in d:
        if r.get('url_datos') and not r.get('id_ruta_principal'): urls[r['url_datos']].append(r['id'])
    W += [f'mismo url_datos en {v}' for v in urls.values() if len(v) > 1]
    return E, W

AVISOS = {'', 'entrevista_telefonica'}
INF_CAMPOS = ['fuente', 'anio', 'modulo', 'inferencia_verificada', 'nivel_maximo', 'dominios_anuales', 'excepciones',
              'excluye_departamentos', 'aviso', 'cita_url',
              'cita_documento', 'cita_ubicacion', 'evidencia_local', 'metodo_lectura', 'verificado_el', 'verificado_por', 'nota',
              'ambitos_publicados', 'ambitos_metodo', 'ambitos_cita_url', 'ambitos_cita_documento', 'ambitos_cita_ubicacion']
# Lima en tres ámbitos (L1, L2; 9/10/2026): ámbitos que el INEI publica (uniones de estratos completos) sin ser dominio
# de la ficha. R-ENC-08 los consulta antes que excluye_departamentos y los publica con el aviso ambito_no_dominio.
AMBITOS_PUBLICADOS = {'LIMA_METROPOLITANA', 'LIMA_REGION', 'CALLAO'}
AMBITOS_METODO = {'ubigeo', 'estrato_hv022'}


def revisar_inferencia(d, filas):
    """inferencia_verificada.csv (tabla curada que lee R-ENC-08): una fila por fuente × año × módulo ('*' = todos).
    true exige nivel, URL y ubicación (sección/página) de la cita; sin verificar exige la nota «pendiente: verificar ficha técnica AAAA»."""
    E = []
    by = {r['id']: r for r in d}
    vistos = collections.Counter((f['fuente'], f['anio'], f['modulo']) for f in filas)
    E += [f'inferencia: fila repetida {k}' for k, n in vistos.items() if n > 1]
    for f in filas:
        k = f"inferencia {f['fuente']} {f['anio']} {f['modulo']}"
        if list(f) != INF_CAMPOS: E.append(f'{k}: columnas distintas de {INF_CAMPOS}'); break
        r = by.get(f['fuente'])
        if r is None: E.append(f'{k}: fuente fuera del catálogo'); continue
        if r.get('naturaleza_dato') != 'encuesta_muestral': E.append(f'{k}: la fuente no es encuesta_muestral')
        if not re.match(r'^(19|20)\d\d$', f['anio']): E.append(f'{k}: año inválido')
        elif r.get('anio_inicio') and r.get('anio_fin') and not r['anio_inicio'] <= int(f['anio']) <= r['anio_fin']:
            E.append(f'{k}: año fuera de la cobertura del catálogo')
        if not f['modulo']: E.append(f'{k}: módulo vacío (usar * para todos)')
        if f['excluye_departamentos'] and not re.match(r'^\d\d(;\d\d)*$', f['excluye_departamentos']):
            E.append(f'{k}: excluye_departamentos debe ser códigos de 2 dígitos separados por «;»')
        if f['aviso'] not in AVISOS: E.append(f'{k}: aviso fuera de vocabulario {sorted(AVISOS)}')
        v = f['inferencia_verificada']
        if v not in ('true', 'false', ''): E.append(f'{k}: inferencia_verificada debe ser true, false o vacío')
        if v == 'true':
            if f['nivel_maximo'] not in V['territorio']: E.append(f'{k}: nivel_maximo fuera de vocabulario')
            if not URL.match(f['cita_url'] or ''): E.append(f'{k}: verificada sin URL de la cita')
            if not re.search(r'(p\.|pp\.|§)', f['cita_ubicacion'] or ''): E.append(f'{k}: verificada sin sección/página')
            if not f['verificado_el'] or not f['verificado_por']: E.append(f'{k}: verificada sin fecha o responsable')
        elif not (f['nota'] or '').startswith('pendiente: verificar ficha técnica ' + f['anio']):
            E.append(f'{k}: sin verificar y sin la nota «pendiente: verificar ficha técnica {f["anio"]}»')
        if f['ambitos_publicados']:
            amb = f['ambitos_publicados'].split(';')
            if not set(amb) <= AMBITOS_PUBLICADOS or len(set(amb)) != len(amb):
                E.append(f'{k}: ambitos_publicados fuera de {sorted(AMBITOS_PUBLICADOS)} o repetidos')
            if v != 'true': E.append(f'{k}: ambitos_publicados sin inferencia_verificada = true')
            if f['ambitos_metodo'] not in AMBITOS_METODO: E.append(f'{k}: ambitos_metodo fuera de {sorted(AMBITOS_METODO)}')
            if not URL.match(f['ambitos_cita_url'] or ''): E.append(f'{k}: ambitos_publicados sin URL de la cita')
            if not f['ambitos_cita_documento']: E.append(f'{k}: ambitos_publicados sin documento de la cita')
            if not re.search(r'(p\.|pp\.|§)', f['ambitos_cita_ubicacion'] or ''): E.append(f'{k}: ambitos_publicados sin sección/página')
            exc = set(filter(None, f['excluye_departamentos'].split(';')))
            if 'CALLAO' in amb and '07' in exc: E.append(f'{k}: el Callao es ámbito publicado y a la vez departamento excluido')
        elif any(f[c] for c in ('ambitos_metodo', 'ambitos_cita_url', 'ambitos_cita_documento', 'ambitos_cita_ubicacion')):
            E.append(f'{k}: cita de ámbitos sin ambitos_publicados')
    return E


def revisar_ingesta(d, iv):
    """La compuerta y la evidencia de captura del catálogo coinciden con ingesta_verificada.json (una sola fuente de verdad)."""
    E = []
    by = {r['id']: r for r in d}
    ok = {t['id']: t for t in iv['aprobadas']}
    for i, t in ok.items():
        r = by.get(i)
        if r is None: E.append(f'ingesta: {i} capturada y verificada pero fuera del catálogo'); continue
        if r.get('ola') in ('0_base', '1_nucleo') and r.get('compuerta_ingesta') != 'aprobada':
            E.append(f'ingesta: {i} tiene captura verificada pero compuerta {r.get("compuerta_ingesta")}')
        ev = r.get('evidencia_ingesta') or {}
        if not ev.get('huellas') or ev.get('huellas') != t['huellas'] or not ev.get('capturas'):
            E.append(f'ingesta: {i} sin evidencia (capturas y huellas) o distinta de ingesta_verificada.json')
    for r in d:
        if r.get('estado_ingesta') and r['id'] not in ok: E.append(f"ingesta: {r['id']} con estado_ingesta sin captura verificada")
        # H1 (auditoría E2): la base de la aprobación queda explícita
        esperada = None if r.get('compuerta_ingesta') != 'aprobada' else ('captura_verificada' if r.get('estado_ingesta') else 'humo')
        if r.get('base_aprobacion') != esperada:
            E.append(f"ingesta: {r['id']} base_aprobacion = {r.get('base_aprobacion')!r}, se esperaba {esperada!r}")
    return E


def revisar_ingesta_al_dia(iv):
    """H2 (auditoría E2): ingesta_verificada.json debe ser lo que hoy calcula ingesta_src.evaluar() a partir de
    capturas, verificaciones.jsonl, insumos.lock.yaml y recetas. Si falla: `just catalogo`."""
    import ingesta_src
    ok, rech = ingesta_src.evaluar()
    if ok != iv['aprobadas'] or rech != iv['rechazadas']:
        a = {t['id']: t for t in iv['aprobadas']}; b = {t['id']: t for t in ok}
        dif = sorted(i for i in set(a) | set(b) if a.get(i) != b.get(i)) or ['rechazadas']
        return [f'ingesta_verificada.json desactualizado respecto de capturas/verificaciones (correr `just catalogo`): {dif}']
    return []


def _inferencia():
    import csv
    return list(csv.DictReader(open(os.path.join(HERE, 'inferencia_verificada.csv'), encoding='utf-8')))


def test_inferencia_verificada():
    E = revisar_inferencia(json.load(open(os.path.join(HERE, 'catalogo_fuentes_v2.json'))), _inferencia())
    assert not E, '\n'.join(E)


def test_ingesta_verificada():
    E = revisar_ingesta(json.load(open(os.path.join(HERE, 'catalogo_fuentes_v2.json'))),
                        json.load(open(os.path.join(HERE, 'ingesta_verificada.json'))))
    assert not E, '\n'.join(E)


def test_ingesta_verificada_al_dia():
    E = revisar_ingesta_al_dia(json.load(open(os.path.join(HERE, 'ingesta_verificada.json'))))
    assert not E, '\n'.join(E)


def test_ingesta_src_exige_huella_y_detecta_desfase(tmp_path, monkeypatch):
    """H7: solo tamaño no aprueba; una falla posterior desaprueba. H2: un JSON viejo se detecta."""
    import ingesta_src
    cruda = tmp_path / 'cruda'; cap = cruda / 'capturas' / 'X-Y' / '2026-01-01'; cap.mkdir(parents=True)
    h = 'sha256:' + 'a' * 64
    (cap / 'datapackage.json').write_text(json.dumps({'resources': [{'hash': h}]}))
    (tmp_path / 'lock.yaml').write_text('X-Y:\n- ' + h + '\n'); (tmp_path / 'recetas').mkdir()
    for k, v in (('RAIZ', str(tmp_path)), ('CRUDA', str(cruda)), ('LOCK', str(tmp_path / 'lock.yaml')), ('RECETAS', str(tmp_path / 'recetas'))):
        monkeypatch.setattr(ingesta_src, k, v)
    ver = cruda / 'verificaciones.jsonl'
    def anotar(fecha, res, det):
        with open(ver, 'a') as f:
            f.write(json.dumps({'accion': 'verificar', 'source_id': 'X-Y', 'hash': h, 'fecha': fecha, 'resultado': res, 'detalle': det}) + '\n')
    anotar('2026-01-01T10:00', 'ok', 'tamaño verificado')
    ok, rech = ingesta_src.evaluar()
    assert ok == [] and 'solo verificación de tamaño' in rech[0]['motivo']
    anotar('2026-01-02T10:00', 'ok', 'huella verificada')
    ok, rech = ingesta_src.evaluar()
    assert [t['id'] for t in ok] == ['X-Y'] and ok[0]['huellas'] == [h] and ok[0]['uso'] == 'capa0'
    viejo = {'aprobadas': ok, 'rechazadas': rech}
    anotar('2026-01-03T10:00', 'falla', 'huella distinta')
    anotar('2026-01-04T10:00', 'ok', 'tamaño verificado')
    ok, rech = ingesta_src.evaluar()
    assert ok == [] and 'falla posterior' in rech[0]['motivo']
    assert revisar_ingesta_al_dia(viejo)          # el JSON de antes de la falla ya no está al día


def test_catalogo():
    E, W = revisar(json.load(open(os.path.join(HERE, 'catalogo_fuentes_v2.json'))))
    assert not E, '\n'.join(E)

if __name__ == '__main__':
    _d = json.load(open(os.path.join(HERE, 'catalogo_fuentes_v2.json')))
    E, W = revisar(_d)
    E += revisar_inferencia(_d, _inferencia())
    _iv = json.load(open(os.path.join(HERE, 'ingesta_verificada.json')))
    E += revisar_ingesta(_d, _iv) + revisar_ingesta_al_dia(_iv)
    print(f'ERRORES ({len(E)}):'); print('\n'.join(E[:80]))
    print(f'\nADVERTENCIAS ({len(W)}):'); print('\n'.join(W[:40]))
    raise SystemExit(1 if E else 0)
