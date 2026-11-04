"""Genera ingesta_verificada.json: evidencia de captura verificada por fuente (decisión del dueño, 8/10/2026).

Criterio (b) de la compuerta («aprobada» por captura verificada), además de la prueba de humo (a):
  1. la fuente tiene capturas registradas en biblioteca/cruda/capturas/<id>/*/datapackage.json;
  2. la ÚLTIMA verificación de cada huella relevante en verificaciones.jsonl es «ok» y hubo al menos una verificación
     de huella completa («huella verificada»), sin fallas desde entonces: una verificación solo de tamaño (`--rapido`)
     no basta (H7 de la auditoría del E2);
  3. si la capa 0 la usa (curados/insumos.lock.yaml), TODAS sus huellas del lock están en sus capturas.
     Huellas relevantes = las del lock (uso capa0) o todas las de sus capturas (uso piloto).
  Las recetas con bloque `desactivada` no se aprueban (p. ej. MEF-FOTO-PIM-MENSUAL).
Las fuentes que tienen capturas pero no cumplen quedan en `rechazadas` con el motivo (no cambian el catálogo).
Uso (desde catalogo/scripts/): python3 ingesta_src.py   (requiere PyYAML; volver a correrlo tras cada `pap registrar`
o `pap verificar`, y luego run.py)."""
import json, os, glob, collections
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.environ.get('PAP_RAIZ') or os.path.abspath(os.path.join(HERE, '..', '..'))
CRUDA = os.path.join(RAIZ, 'biblioteca', 'cruda')
RECETAS = os.path.join(RAIZ, 'curados', 'recetas')
LOCK = os.path.join(RAIZ, 'curados', 'insumos.lock.yaml')
SALIDA = os.path.join(HERE, 'ingesta_verificada.json')


def desactivadas():
    out = set()
    for p in glob.glob(os.path.join(RECETAS, '*.yaml')):
        r = yaml.safe_load(open(p, encoding='utf-8')) or {}
        if r.get('desactivada'): out.add(r.get('id'))
    return out


def evaluar():
    lock = yaml.safe_load(open(LOCK, encoding='utf-8')) or {}
    ver = collections.defaultdict(list)          # huella -> verificaciones (orden de archivo = orden temporal)
    for l in open(os.path.join(CRUDA, 'verificaciones.jsonl'), encoding='utf-8'):
        if l.strip():
            v = json.loads(l)
            if v.get('accion') == 'verificar' and v.get('hash'): ver[(v['source_id'], v['hash'])].append(v)
    fuera = desactivadas()
    ok, rech = [], []
    for d in sorted(glob.glob(os.path.join(CRUDA, 'capturas', '*'))):
        sid = os.path.basename(d)
        caps = sorted(glob.glob(os.path.join(d, '*', 'datapackage.json')))
        if not caps: continue
        if sid in fuera:
            rech.append({'id': sid, 'motivo': 'receta desactivada'}); continue
        por_huella = {}
        for c in caps:
            for r in json.load(open(c, encoding='utf-8')).get('resources', []):
                por_huella.setdefault(r['hash'], os.path.relpath(os.path.dirname(c), RAIZ))
        en_lock = list(lock.get(sid) or [])
        faltan = [h for h in en_lock if h not in por_huella]
        if faltan:
            rech.append({'id': sid, 'motivo': 'huellas del lock sin captura: ' + ', '.join(h[:19] for h in faltan)}); continue
        relevantes = en_lock or sorted(por_huella)
        malas, tipos, fechas = [], set(), []
        for h in relevantes:
            vs = sorted(ver.get((sid, h), []), key=lambda v: v['fecha'])
            if not vs or vs[-1]['resultado'] != 'ok':
                malas.append(h[:19] + ('… sin verificación' if not vs else f"… última verificación {vs[-1]['resultado']}")); continue
            ult_completa = next((v for v in reversed(vs) if v.get('detalle') == 'huella verificada'), None)
            if ult_completa is None:   # H7 (auditoría E2): una verificación solo de tamaño no basta
                malas.append(h[:19] + '… solo verificación de tamaño (falta `pap verificar` sin --rapido)'); continue
            if any(v['resultado'] != 'ok' for v in vs if v['fecha'] >= ult_completa['fecha']):
                malas.append(h[:19] + '… falla posterior a la última verificación de huella'); continue
            tipos.add('huella'); fechas.append(vs[-1]['fecha'])
        if malas:
            rech.append({'id': sid, 'motivo': '; '.join(malas)}); continue
        ok.append({
            'id': sid,
            'uso': 'capa0' if en_lock else 'piloto',
            'fecha_verificacion': max(fechas)[:10],
            'tipo_verificacion': 'huella',
            'capturas': sorted({por_huella[h] for h in relevantes}),
            'huellas': relevantes,
            'huellas_en_lock': bool(en_lock),
        })
    return ok, rech


def main():
    ok, rech = evaluar()
    json.dump({'criterio': 'captura con última verificación ok por huella; si está en insumos.lock.yaml, todas sus huellas '
                           'del lock en sus capturas (decisión del dueño 8/10/2026; catalogo/scripts/ingesta_src.py)',
               'aprobadas': ok, 'rechazadas': rech},
              open(SALIDA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return ok, rech


if __name__ == '__main__':
    ok, rech = main()
    for r in ok: print('ok ', r['id'], r['uso'], r['fecha_verificacion'], r['tipo_verificacion'], len(r['huellas']))
    for r in rech: print('NO ', r['id'], r['motivo'])
