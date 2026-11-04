"""Corrector estructural de R-LENGUAJE-02: reglas que la lista léxica no puede ver porque dependen de los metadatos de cada
cifra marcada {{c:id}} (fuente, nivel). Lo usan el validador y consolida_reglas.py (casos en pruebas/casos_personas_censadas.json)."""
import re
CIFRA = re.compile(r'\{\{c:([^}]+)\}\}')
PERSONAS_CENSADAS = '{{u:personas_censadas}}'
def oraciones(texto):
    return [o for o in re.split(r'(?<=[.!?;])\s+', texto) if o.strip()]
def personas_censadas(texto, cifras):
    """HEC-01: toda cifra del INEI-CPV2025 por provincia o distrito va en una oración con {{u:personas_censadas}}.
    cifras = {id: {'fuente': ..., 'nivel': ...}}. Devuelve las oraciones que obligan a regenerar (lista vacía = pasa)."""
    malas = []
    for o in oraciones(texto):
        for cid in CIFRA.findall(o):
            c = cifras.get(cid, {})
            if c.get('fuente') == 'INEI-CPV2025' and c.get('nivel') in ('provincia', 'distrito') and PERSONAS_CENSADAS not in o:
                malas.append(o); break
    return malas
