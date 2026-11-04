"""Embudo de priorización v2 (corrige A-01, A-02, A-03, A-04, C-01 y EMB-* de la auditoría del 5/10/2026).
Orden: ruta alterna → capa 0 → infraestructura de acceso → excepciones → reglas del embudo."""
import re

ANIO_REF = 2026
VIGENCIA_MIN = ANIO_REF - 5          # A-02: último dato ≥ 2021 para entrar a la Ola 1
NUCLEO_CORE = {'pobreza_condiciones_vida', 'salud', 'nutricion_anemia', 'educacion', 'programas_sociales'}
NUCLEO_AMPL = {'poblacion_demografia', 'vivienda_servicios_basicos', 'empleo_ingresos', 'genero_violencia', 'pueblos_indigenas_cultura'}
NUCLEO = NUCLEO_CORE | NUCLEO_AMPL
OFICIAL_NO = {'Académico', 'Internacional', 'Privado', 'Sociedad civil', 'Académico / privado (no oficial)'}
PRIM_NAT = {'encuesta_muestral', 'censo', 'registro_administrativo', 'presupuestal_financiero'}

BASE = {  # capa 0: tablas de referencia, denominadores y puentes
 'BCRP-IPC-LIMA': 'Deflactor del gasto a soles constantes (IPC Lima Metropolitana, BCRP PN38705PM).',
 'INEI-PROYECCIONES-DISTRITAL-2018-2022': 'Boletín 27: altas de distritos 2018–2022 para el ubigeo histórico.',
 'PROPIO-ESTADISTICAS-SOCIALES-2020': 'Archivo propio: semilla GEO2017 del ubigeo histórico (no redistribuible).',
 'INEI-PNDA-UBIGEOS': 'Lista oficial de ubigeos INEI (corte 2022; completar con 1 892 distritos).',
 'GITHUB-UBIGEO-PERU-AUMENTADO': 'Puente INEI↔RENIEC y centro poblado con coordenadas (secundaria, corte 2021; solo como herramienta validada).',
 'INEI-DIRECTORIO-MUNICIPALIDADES': 'Ley y fecha de creación de cada distrito: base del ubigeo histórico.',
 'INEI-IDE-LIMITES': 'Límites censales (distritos, centros poblados, manzanas) para mapas.',
 'INEI-DIRECTORIO-CCPP': 'Centros poblados con ubigeo de 10 dígitos.',
 'INEI-CPV2017': 'Línea de base de población y vivienda; distrito × sexo × edad simple.',
 'INEI-CPV2025': 'Nuevo denominador censal: resultados por distrito desde jul-2026 (consulta en línea; aún sin bases).',
 'INEI-PROYECCIONES-POBLACION-DISTRITAL': 'Población total proyectada por distrito y año 2018–2026.',
 'INEI-PROYECCIONES-DEPARTAMENTAL-EDAD': 'Población por edad simple y sexo, departamental, 1995–2030.',
 'MINSA-POBLACION-ESTIMADA': 'Denominador oficial del MINSA por distrito y edad (coberturas de salud).',
 'RENIEC-POBLACION-IDENTIFICADA': 'Población identificada con DNI por distrito, edad y sexo (contraste; no es población residente).',
 'SUSALUD-RENIPRESS': 'Puente establecimiento de salud → ubigeo (mensual).',
 'MINEDU-ESCALE-PADRON': 'Puente institución educativa (código modular) → ubigeo y coordenadas.',
 'MEF-DETALLE-INVERSIONES': 'Maestro de inversiones: CUI → ubigeo, función y sector.',
 'MEF-MAESTRO-EJECUTORAS-DERIVADO': 'Maestro de unidades ejecutoras con ubigeo y nivel de gobierno (derivado del gasto MEF).',
 'MEF-PPR-PROGRAMAS-PRESUPUESTALES': 'Estructura programática versionada por año (PP → producto → actividad), con el cambio 0001/0002 → 1001.',
}
GASTO = {'MEF-DA-PRESUPUESTO-EJECUCION-GASTO', 'MEF-DA-GASTO-DEVENGADO-MENSUAL', 'MEF-DA-GASTO-PPR', 'MEF-DA-TRANSFERENCIAS',
         'MEF-DA-GASTO-DEVENGADO-SECTORES', 'MEF-PPR-SEGUIMIENTO-INDICADORES', 'MEF-PPR-EVALUACIONES-INDEPENDIENTES',
         'MEF-PI-INCENTIVOS-MUNICIPALES', 'MEF-MIDIS-FED', 'MEF-DA-GASTO-GPNNA', 'MEF-SEGUIMIENTO-PI', 'MEF-FORMATO-12B',
         'MEF-INVERSIONES-BRECHAS', 'MEF-BRECHAS-VALORES', 'MEF-CIERRE-INVERSIONES', 'MEF-GEOINVIERTE', 'MEF-OXI-BASE', 'CGR-INFOBRAS',
         'MEF-CONSULTA-AMIGABLE-GASTO-DIARIA', 'MEF-CONSULTA-AMIGABLE-GASTO-MENSUAL', 'MEF-SSI', 'MEF-CONSULTA-INVERSIONES',
         'MEF-CONSULTA-AMIGABLE-SEGUIMIENTO-PI', 'MEF-CONSULTA-TRANSFERENCIAS', 'MEF-PMI-CARTERA'}
ALTERNA = {  # además de los id_ruta_principal que traen los registros
 'MEF-CONSULTA-AMIGABLE-GASTO-DIARIA': 'MEF-DA-PRESUPUESTO-EJECUCION-GASTO', 'MEF-CONSULTA-AMIGABLE-GASTO-MENSUAL': 'MEF-DA-PRESUPUESTO-EJECUCION-GASTO',
 'MEF-CONSULTA-AMIGABLE-SEGUIMIENTO-PI': 'MEF-SEGUIMIENTO-PI', 'MEF-SSI': 'MEF-SEGUIMIENTO-PI', 'MEF-CONSULTA-INVERSIONES': 'MEF-DETALLE-INVERSIONES',
 'MEF-CONSULTA-TRANSFERENCIAS': 'MEF-DA-TRANSFERENCIAS', 'MINSA-CNV': 'MINSA-CNV-NACIDOS-VIVOS',
 'RENIEC-POBLACION-IDENTIFICADA-DNI': 'RENIEC-POBLACION-IDENTIFICADA',   # EMB-14: la de API CKAN es más estable
 'INEI-UBIGEO-CODIGOS': 'INEI-PNDA-UBIGEOS', 'INEI-CPV2017-MANZANA': 'INEI-CPV2017',
 'SIS-ATENCIONES-PNDA': 'SIS-ATENCIONES', 'SIS-AFILIADOS-PNDA': 'SIS-AFILIADOS', 'ESSALUD-EMERGENCIAS-PNDA': 'ESSALUD-DATOS-ABIERTOS',
 'CENEPRED-SIGRID-IIEE': 'MINEDU-ESCALE-PADRON', 'MINEDU-SIGMED-DESCARGAS': 'MINEDU-ESCALE-PADRON'}
ESENCIAL = {  # entran a la Ola 1 aunque su descarga no sea automatizable: no tienen sustituto
 'MINEDU-CENSO-EDUCATIVO': 'Única fuente de matrícula, docentes y servicios por IE; ESCALE exige navegador automatizado.',
 'INEI-MAPA-POBREZA': 'Única pobreza oficial por distrito (2018, estimación con IC); publicar con las reglas de C-03.',
 'INEI-MAPA-DCI-PROVINCIAL-2019': 'Única desnutrición crónica oficial bajo el departamento (196 provincias, 2019, con IC).',
 'MINSA-REUNIS': 'Concentra indicadores por EESS (HIS, CRED, anemia) sin otra vía pública; requiere extraer de tableros.',
 'MINSA-INMUNIZACIONES': 'Vacunación por distrito/EESS: sin dataset abierto, solo tablero REUNIS o transparencia.',
 'MINEDU-UMC-ENLA': 'Única medición vigente de aprendizajes (2022–2025), representativa por departamento; descarga manual.'}
LINEA_BASE = {'INEI-CPV2017', 'INEI-MAPA-POBREZA', 'INEI-MAPA-DCI-PROVINCIAL-2019'}
SEGUNDA = {
 'MINSA-COVID-DATOS-ABIERTOS': 'Serie cerrada de la pandemia.', 'MINSA-FALLECIDOS-COVID19': 'Serie cerrada de la pandemia.',
 'MEF-DA-GASTO-COVID19': 'Serie cerrada de la pandemia.', 'DEVIDA-OPD': 'Reportes de estudios, no base estructurada por ubigeo.',
 'CONADIS-RNPCD': 'Registro voluntario con subregistro alto; usar Censo como cifra principal.', 'DIRESA-CALLAO-OPENDATA': 'Cobertura solo Callao.',
 'SUSALUD-PNDA-COBERTURA-PRIVADA': 'Solo sector privado.', 'PRONABEC-DATOS-ABIERTOS': 'Educación superior: segunda prioridad.',
 'SUNEDU-LICENCIAMIENTO': 'Educación superior: segunda prioridad.', 'SUNEDU-PROGRAMAS': 'Educación superior: segunda prioridad.',
 'MEF-OXI-BASE': 'Valor marginal bajo para el MVP: ya cubierto por Detalle y Seguimiento de inversiones (EMB-15).',
 'MEF-CIERRE-INVERSIONES': 'Valor marginal bajo para el MVP (EMB-15).', 'MEF-FORMATO-12B': 'Valor marginal bajo para el MVP (EMB-15).'}

NIVEL = {'centro_poblado': 1.0, 'manzana_conglomerado': 1.0, 'punto_coordenadas': 1.0, 'establecimiento': 1.0,
         'distrito': 1.0, 'provincia': 0.7, 'dominio': 0.6, 'departamento': 0.55, 'nacional': 0.1}
LLAVE_OK = {'ubigeo_inei', 'ubigeo_reniec', 'codigo_centro_poblado', 'codigo_modular_ie', 'codigo_local_escolar', 'codigo_renipress_ipress',
            'cui_inversion', 'codigo_snip', 'pliego_unidad_ejecutora (sec_ejec)', 'coordenadas', 'conglomerado_vivienda'}
FACT = {'api_rest': 1.0, 'api_ckan': 1.0, 'descarga_directa_url': 1.0, 'geoservicio': 0.8, 'descarga_manual': 0.6,
        'scraping_html': 0.5, 'scraping_dinamico': 0.3, 'solicitud_acceso_informacion': 0.1, 'convenio': 0.1}
FAC_OLA1 = 0.8   # A-03: la Ola 1 exige API, URL estable o geoservicio; lo manual entra solo por ESENCIAL

def capa(r):
    if r['id'] in BASE: return 'base'
    if r['naturaleza_dato'] == 'catalogo_portal' and (r.get('sector') or '') not in OFICIAL_NO: return 'infraestructura_acceso'
    if r['id'] in GASTO: return 'gasto_publico'
    temas = {r['tematica_principal']} | set(r.get('tematicas_secundarias') or [])   # A-04: se miran siempre las secundarias
    if temas & NUCLEO: return 'nucleo_social'
    return 'complementaria'

def es_core(r):
    temas = {r['tematica_principal']} | set(r.get('tematicas_secundarias') or [])
    return r['tematica_principal'] in NUCLEO_CORE or (r['tematica_principal'] in ('multitematica', 'poblacion_demografia') and bool(temas & NUCLEO_CORE))

def origen(r):
    if (r.get('sector') or '') == 'Propio': return 'secundaria'   # H6 (auditoría E2): compilación propia, no oficial
    if r['naturaleza_dato'] == 'catalogo_portal' or (r.get('sector') or '') in OFICIAL_NO: return 'secundaria'
    if r['naturaleza_dato'] in PRIM_NAT: return 'primaria'
    if r['naturaleza_dato'] == 'geoespacial' and (r.get('tipo_medida') in ('padron_referencia', 'stock_infraestructura') or r.get('base_geografica') in ('inversion_ubicacion', 'establecimiento')):
        return 'primaria'   # EMB-17: capas que son registros (GeoInvierte, padrones georreferenciados)
    return 'derivada_oficial'

def cruz_fac(r):
    niv = NIVEL.get(r.get('nivel_territorial_inferencia') or r.get('nivel_territorial_disponible'), 0)
    if r.get('base_geografica') == 'ejecutora': niv = min(niv, 0.7)   # C-01: el gasto solo es distrital para municipalidades
    llaves = set(r.get('llaves_cruce') or [])
    cz = niv * (1.0 if llaves & LLAVE_OK else 0.5)
    fc = FACT.get(r.get('estrategia_descarga'), 0.3)
    if r.get('estado_portal') == 'no_responde' or r.get('estado_datos') in ('sin_descarga_publica', 'descarga_falla'): fc = min(fc, 0.1)
    return cz, fc

def vigente(r):
    return r['id'] in LINEA_BASE or (r.get('anio_fin') or 0) >= VIGENCIA_MIN

def puntaje(r, c):
    cz, fc = cruz_fac(r)
    temas = {r['tematica_principal']} | set(r.get('tematicas_secundarias') or [])
    rel = 1.0 if c == 'base' else 0.9 if c == 'gasto_publico' else 1.0 if temas & NUCLEO_CORE else 0.75 if temas & NUCLEO_AMPL else 0.3
    a1 = r.get('anio_fin'); a0 = r.get('anio_inicio')
    vig = 0.0 if not a1 else (0.6 if a1 >= 2024 else 0.35 if a1 >= VIGENCIA_MIN else 0.1) + (0.4 if a0 and a1 - a0 >= 5 else 0.15)
    return round(100 * (0.30 * rel + 0.30 * cz + 0.25 * fc + 0.15 * vig)), cz, fc   # EMB-18: más peso a relevancia

def priorizar(d):
    ids = {r['id'] for r in d}
    for r in d:
        alt = r.get('id_ruta_principal') or ALTERNA.get(r['id'])
        if alt and alt in ids: r['id_ruta_principal'] = alt
        c = capa(r); o = origen(r); p, cz, fc = puntaje(r, c)
        r['capa'], r['origen'], r['puntaje_prioridad'] = c, o, p
        nr = r.get('estado_portal') == 'no_responde' or r.get('estado_datos') in ('sin_descarga_publica', 'descarga_falla')
        if r.get('id_ruta_principal'):
            ola, mot = 'ruta_alterna', f"Misma información que {r['id_ruta_principal']}, que es la ruta preferida; usar solo para validar o para el dato del día."
        elif c == 'base':
            ola, mot = '0_base', BASE[r['id']]
        elif c == 'infraestructura_acceso':
            ola, mot = 'infraestructura_acceso', 'Portal o catálogo por el que se descargan otras fuentes: se monitorea (fechas de actualización), no se ingiere como dato.'
        elif r['id'] in ESENCIAL:
            ola, mot = '1_nucleo', 'Indispensable por excepción: ' + ESENCIAL[r['id']]
        elif r['id'] in SEGUNDA:
            ola, mot = '2_expansion', SEGUNDA[r['id']]
        elif c in ('nucleo_social', 'gasto_publico') and o == 'primaria':
            if nr or r.get('estrategia_descarga') in ('solicitud_acceso_informacion', 'convenio'):
                ola, mot = '2_expansion', 'Primaria y relevante, pero hoy sin descarga pública (sitio caído, login, sin datasets o solo por transparencia).'
            elif not r.get('anio_fin') and r['id'] not in LINEA_BASE:
                ola, mot = '2_expansion', 'Primaria y relevante, pero sin año del último dato confirmado: confirmar vigencia antes de subirla a la Ola 1.'
            elif not vigente(r):
                ola, mot = 'referencia', f"Serie cerrada o antigua (último dato {r.get('anio_fin') or 'desconocido'}; la Ola 1 exige ≥ {VIGENCIA_MIN}): útil como contexto histórico."
            elif cz >= 0.5 and fc >= FAC_OLA1 and (c == 'gasto_publico' or es_core(r)):
                ola, mot = '1_nucleo', 'Primaria, vigente, del foco duro o su gasto, cruzable y descargable por API o URL estable.'
            elif cz >= 0.5 and fc >= FAC_OLA1:
                ola, mot = '2_expansion', 'Primaria, vigente, cruzable y descargable, de un tema social ampliado (agua y vivienda, empleo, género, población, pueblos indígenas).'
            elif cz >= 0.5:
                ola, mot = '2_expansion', 'Primaria y cruzable, pero su descarga es manual o exige automatizar tableros.'
            else:
                ola, mot = '2_expansion', 'Primaria y relevante, pero sin llave o nivel territorial útil para cruzar.'
        elif c in ('nucleo_social', 'gasto_publico') and o == 'derivada_oficial':
            if cz >= 0.9 and fc >= 0.3 and vigente(r):
                ola, mot = '2_expansion', 'Indicador oficial ya procesado con detalle fino que no se puede reconstruir desde microdatos.'
            else:
                ola, mot = 'referencia', 'Cifra oficial ya procesada: sirve para validar que nuestros cálculos coinciden con lo publicado.'
        elif c in ('nucleo_social', 'gasto_publico'):
            ola, mot = 'referencia', 'Fuente secundaria (académica, internacional o herramienta): útil para contrastar, no como dato base.'
        else:
            if o == 'primaria' and cz >= 0.5 and not nr:
                ola, mot = '3_complementaria', 'Primaria y cruzable, de un tema fuera del foco social inicial.'
            else:
                ola, mot = 'fuera_de_alcance', 'Tema fuera del foco y sin dato primario cruzable.'
        r['ola'], r['motivo_ola'] = ola, mot
        # compuerta de ingesta (C-06): «aprobada» si (a) la prueba de humo bajó una muestra o (b) hay captura verificada
        # (paso «ingesta verificada» de run.py, decisión del 8/10/2026); ambas dejan estado_datos = descarga_ok
        if ola in ('0_base', '1_nucleo'):
            r['compuerta_ingesta'] = {'descarga_ok': 'aprobada', 'enlace_confirmado': 'enlace_confirmado', 'descarga_falla': 'bloqueada', 'sin_descarga_publica': 'manual_o_transparencia'}.get(r.get('estado_datos'), 'pendiente_prueba')
        else:
            r['compuerta_ingesta'] = None
        # H1 (auditoría E2): base de la aprobación, visible para el validador y el dueño
        r['base_aprobacion'] = (('captura_verificada' if r.get('estado_ingesta') else 'humo')
                                if r['compuerta_ingesta'] == 'aprobada' else None)
    return d
