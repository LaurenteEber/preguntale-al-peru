"""Pipeline del catálogo v2: base v0.3 → migración → correcciones de auditoría → fuentes nuevas → prueba de humo → ingesta verificada → priorización."""
import json, re, os, sys
from migrar_v2 import migrar
from prioriza_v2 import priorizar
HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)

def aplicar(r, cambios, traza):
    for k, v in cambios.items():
        if k.startswith('_append_'):
            c = k[8:]; r[c] = ((r.get(c) or '') + v).strip()
        elif k.startswith('_sub_'):
            c = k[5:]; nuevo = re.sub(v[0], v[1], r.get(c) or '')
            r[c] = nuevo if nuevo != (r.get(c) or '') else ((r.get(c) or '') + ' ' + v[1]).strip()
        else:
            r[k] = v
    r.setdefault('correcciones', []).append(traza)

def main():
    d = migrar(json.load(open(P('catalogo_v03_base.json'))))
    by = {r['id']: r for r in d}
    log = []
    nf = json.load(open(P('nuevas_fuentes.json')))
    for c in nf['correcciones']:
        ch = dict(c['cambios'])
        if 'notas' in ch: ch['_append_notas'] = ' ' + ch.pop('notas')
        aplicar(by[c['id']], ch, {'hallazgos': ['vacío ' + c['vacio']], 'validacion': 'investigacion', 'evidencia': c['evidencia']})
    for r in nf['nuevos']:
        r = dict(r); r.pop('ola_sugerida', None); vac = r.pop('vacio', None)
        r.setdefault('ids_fusionados', []); r.setdefault('id_ruta_principal', None)
        r['correcciones'] = [{'hallazgos': ['vacío ' + str(vac)], 'validacion': 'investigacion', 'evidencia': r.get('url_portal') or r.get('url_datos')}]
        d.append(r); by[r['id']] = r
    # correcciones trazables: después de agregar las fuentes nuevas, para que también las alcancen
    for c in json.load(open(P('correcciones_auditoria.json'))):
        aplicar(by[c['id']], c['cambios'], {'hallazgos': c['hallazgos'], 'validacion': c['validacion'], 'evidencia': c['evidencia']})
        log.append(c['id'])
    # prueba de humo (si existe)
    if os.path.exists(P('prueba_humo.json')):
        for t in json.load(open(P('prueba_humo.json'))):
            r = by.get(t['id'])
            if r:
                r['estado_datos'] = t['estado_datos']; r['fecha_verificacion'] = t['fecha']
                if t.get('nota'): r['notas'] = ((r.get('notas') or '') + ' [Prueba de humo ' + t['fecha'] + '] ' + t['nota']).strip()
                if t.get('cambios'): r.update(t['cambios'])
    # ingesta verificada (decisión del dueño, 8/10/2026): captura registrada cuya última verificación por huella es «ok»
    # y, si la capa 0 la usa, con todas sus huellas de insumos.lock.yaml en esas capturas (lo genera ingesta_src.py).
    # Va después de la prueba de humo: es evidencia posterior y más fuerte (el archivo completo está en el almacén).
    for r in d:
        r.setdefault('estado_ingesta', None)
    if not os.path.exists(P('ingesta_verificada.json')):   # H2 (auditoría E2): no se salta en silencio
        sys.exit('Falta ingesta_verificada.json: correr primero `python3 ingesta_src.py` (o `just catalogo`).')
    iv = json.load(open(P('ingesta_verificada.json')))
    for t in iv['aprobadas']:
        r = by.get(t['id'])
        if r is None:
            sys.exit(f"ingesta_verificada.json: {t['id']} tiene captura verificada pero no está en el catálogo")
        r['estado_datos'] = 'descarga_ok'; r['fecha_verificacion'] = t['fecha_verificacion']
        r['estado_ingesta'] = 'capturada_verificada_' + t['uso']
        r['evidencia_ingesta'] = {k: t[k] for k in ('fecha_verificacion', 'tipo_verificacion', 'capturas', 'huellas', 'huellas_en_lock')}
        r.setdefault('correcciones', []).append({'hallazgos': ['R-DEP-01 (compuerta por captura verificada, 8/10/2026)'],
            'validacion': 'captura', 'evidencia': '; '.join(t['capturas']) + ' · ' + str(len(t['huellas'])) + ' huella(s) verificada(s) el ' + t['fecha_verificacion']})
    priorizar(d)
    json.dump(d, open(P('catalogo_fuentes_v2.json'), 'w'), ensure_ascii=False, indent=1)
    return d

if __name__ == '__main__':
    import collections
    d = main()
    print(len(d), collections.Counter(r['ola'] for r in d))
    print(collections.Counter(r.get('compuerta_ingesta') for r in d if r['ola'] in ('0_base', '1_nucleo')))
