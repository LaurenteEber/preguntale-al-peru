# Esquema de registro v2 — Catálogo de fuentes "Pregúntale al Perú"

Cambios frente a v1 (respuesta a la auditoría del 5/10/2026): campos de años tipados, licencia normalizada,
estado de verificación separado en portal y datos, URL literal separada de la plantilla, base geográfica y tipo de medida,
trazabilidad de fusiones y rutas alternas, quiebres metodológicos.

Una "fuente" = un conjunto de datos o sistema concreto. Usa null si no se sabe; NO inventes.

## Campos

| Campo | Tipo | Regla |
|---|---|---|
| id | str | `ENTIDAD-FUENTE`, mayúsculas y guiones, único |
| nombre, sigla, descripcion | str | |
| tematica_principal | enum VOCAB_TEMATICA | |
| tematicas_secundarias | list[VOCAB_TEMATICA] | sin repetir la principal |
| subtemas | list[str] | palabras clave |
| entidad, sector, unidad_organica | str | entidad obligatoria en Ola 0/1 |
| naturaleza_dato | enum VOCAB_NATURALEZA | |
| tipo_acceso | list[VOCAB_ACCESO] | |
| unidad_observacion | str | |
| cobertura_geografica | str | |
| nivel_territorial_disponible | enum VOCAB_TERRITORIO | nivel más fino publicado |
| nivel_territorial_inferencia | enum VOCAB_TERRITORIO o null | **solo encuestas y estimaciones modeladas**; null en registros, censos y presupuesto |
| base_geografica | enum VOCAB_BASE_GEO | a qué lugar se refiere el ubigeo |
| tipo_medida | enum VOCAB_MEDIDA | qué mide el dato |
| desagregaciones | list[str] | |
| llaves_cruce | list[VOCAB_LLAVES] | solo llaves que existan como columna en los datos |
| periodicidad | str | |
| cobertura_temporal | str | texto libre descriptivo (se conserva) |
| anio_inicio, anio_fin | int o null | anio_fin = último año con datos publicados; ≤ 2026 salvo es_proyeccion |
| fecha_ultimo_dato | str ISO (AAAA-MM o AAAA-MM-DD) o null | |
| es_proyeccion | bool | |
| serie_activa | bool o null | true si sigue publicándose |
| anios_con_quiebre | str o null | años y motivo de quiebres metodológicos |
| rezago_publicacion | str o null | |
| formatos | list[str] | |
| url_portal | URL http(s) o null | página estable de la fuente |
| url_datos | URL http(s) literal o null | archivo, endpoint o ficha de dataset; sin espacios ni texto |
| url_patron | str o null | plantilla con {anio}, {mes}, {semestre}; ej. `https://.../{anio}-Gasto.csv` |
| url_documentacion | URL o null | |
| estrategia_descarga | enum VOCAB_ESTRATEGIA | si es descarga_directa_url/api_*/geoservicio, url_datos o url_patron obligatorio |
| detalle_descarga | str | |
| requiere_registro | bool | |
| licencia | enum VOCAB_LICENCIA | |
| licencia_texto | str o null | texto original |
| permite_redistribucion | bool o null | |
| limitaciones | str | |
| prioridad_mvp | alta/media/baja | heredado; informativo |
| estado_portal | confirmado_busqueda / confirmado_navegador / no_responde | |
| estado_datos | sin_probar / descarga_ok / enlace_confirmado / descarga_falla / sin_descarga_publica | resultado de la prueba de humo: descarga_ok = se leyó una muestra real del archivo; enlace_confirmado = el enlace al archivo o tablero existe en la página oficial pero no se descargó |
| compuerta_ingesta | aprobada / enlace_confirmado / pendiente_prueba / bloqueada / manual_o_transparencia | solo Olas 0 y 1; la calcula prioriza_v2.py. «aprobada» = (a) la prueba de humo bajó una muestra o (b) hay captura completa verificada (ver estado_ingesta; decisión del 8/10/2026). R-DEP-01 lee solo este campo |
| fecha_verificacion | str ISO o null | fecha de la prueba de humo o, si hay captura verificada, de su última verificación |
| base_aprobacion | humo / captura_verificada / null | solo si compuerta_ingesta = aprobada. «humo»: solo la muestra de la prueba de humo (criterio a, sigue valiendo: la decisión del 8/10/2026 dice que la captura *también* cuenta). «captura_verificada»: criterio b, archivo completo en el almacén con huella verificada. Lo calcula prioriza_v2.py; el validador y el dueño pueden exigir captura_verificada para los insumos bloqueantes |
| estado_ingesta | capturada_verificada_capa0 / capturada_verificada_piloto / null | lo escribe run.py desde ingesta_verificada.json (catalogo/scripts/ingesta_src.py): captura registrada con la última verificación por huella «ok»; _capa0 = además todas sus huellas de curados/insumos.lock.yaml están en esas capturas |
| evidencia_ingesta | objeto (solo JSON) | fecha_verificacion, tipo_verificacion (huella / tamano / mixta), capturas, huellas, huellas_en_lock. Exige al menos una verificación de huella completa sin fallas posteriores (una de solo tamaño no basta) |
| ids_fusionados | list[str] | IDs absorbidos por este registro |
| id_ruta_principal | str o null | para rutas alternas: ID del registro preferido |
| origen, capa, ola, puntaje_prioridad, motivo_ola | | los calcula prioriza.py |
| notas | str o null | |

## Vocabularios nuevos

VOCAB_BASE_GEO: residencia, establecimiento, ejecutora, meta_departamento, inversion_ubicacion, domicilio_fiscal, ocurrencia, muestra (encuesta), territorio (límites/población), no_aplica

VOCAB_MEDIDA: prevalencia (población, encuesta/censo), cobertura_programa, atenciones_produccion, notificacion_vigilancia, registro_eventos (nacimientos, defunciones, denuncias), stock_infraestructura, presupuesto_gasto, estimacion_modelada, padron_referencia, otro

VOCAB_LICENCIA: ODC-By-1.0, ODbL-1.0, CC-BY-4.0, CC-BY-3.0, CC-BY-3.0-IGO, CC-BY-NC-4.0, CC-BY-NC-3.0-IGO, CC-BY-NC-SA-4.0, CC0-1.0, PDDL-1.0, MIT, Apache-2.0, otra-abierta, uso-libre-con-cita, restringido, no-especificada

Vocabularios de v1 (sin cambios salvo los añadidos): ver esquema_registro_v1.md.
VOCAB_TERRITORIO añade: dominio (dominios de encuesta, p. ej. Lima Metropolitana).
VOCAB_ESTRATEGIA y VOCAB_NATURALEZA sin cambios.

## Tabla asociada: `inferencia_verificada.csv` (R-ENC-08)

Una fila por fuente × año × módulo (`*` = todos los módulos de esa encuesta y año). La fuente curada es `catalogo/scripts/inferencia_verificada.csv`; `render.py` la publica aquí y `test_catalogo.py` la valida contra el catálogo.

| Campo | Valores | Nota |
|---|---|---|
| fuente, anio, modulo | id del catálogo (encuesta_muestral), año, código de módulo o `*` | llave única |
| inferencia_verificada | true / false / vacío | true solo con cita; sin verificar → la cifra se publica solo a nivel nacional |
| nivel_maximo | vocabulario de territorio | nivel más fino con representatividad anual según la ficha |
| dominios_anuales, excepciones | texto | lo que declara la ficha y lo que no cubre (p. ej., el Callao en la ENAHO) |
| excluye_departamentos | códigos de departamento (2 dígitos) separados por «;» | ámbitos de nivel_maximo que la ficha NO declara como dominio (antes, ENAHO: `07`). R-ENC-08 no publica esos ámbitos. Desde el 9/10/2026 el Callao de la ENAHO (2015–2025) va por `ambitos_publicados` (L1) y la columna queda vacía |
| aviso | vacío / entrevista_telefonica | advertencia estructurada del año (pandemia: entrevista telefónica total o parcial). Se muestra junto a la cifra |
| cita_url, cita_documento, cita_ubicacion | URL, nombre, sección y página | obligatorias si true. Las páginas leídas por WebFetch se marcan «aprox.»: la sección (§) es la referencia estable |
| evidencia_local, metodo_lectura | texto | captura del repositorio y cómo se leyó (pdftotext, WebFetch) |
| verificado_el, verificado_por, nota | fecha, responsable, texto | sin verificar: la nota empieza con «pendiente: verificar ficha técnica AAAA» |
| ambitos_publicados | `LIMA_METROPOLITANA`, `LIMA_REGION`, `CALLAO` separados por «;» | ámbitos que el INEI publica (uniones de estratos completos) sin ser dominio de la ficha (L1, L2, auditoría Lima A1). R-ENC-08 los consulta antes que excluye_departamentos y los publica con el aviso `ambito_no_dominio`. ENAHO 2015–2025: los tres (informe técnico de pobreza; páginas impresas, y la del PDF aparte si difiere); ENDES: LM y LR (el Callao ya es dominio de la ficha) |
| ambitos_metodo | `ubigeo` / `estrato_hv022` | cómo se asigna cada unidad (ENDES 2015–2017: estrato de diseño, con aviso de método); la asignación la hace `src/pap/capa0/ambitos_lima.py` |
| ambitos_cita_url, ambitos_cita_documento, ambitos_cita_ubicacion | URL, nombre, sección y página | obligatorias si hay ambitos_publicados (ENDES: ficha §3.6, Cuadro N.º 1; ENAHO: informe técnico, Gráfico N.º 4.7 y Cuadro N.º III.1) |
