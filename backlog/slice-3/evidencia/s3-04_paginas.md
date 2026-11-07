# S3-04 — Páginas: pregunta, respuesta y aclaración: evidencia

Código en `src/pap/web/paginas.py` (rutas), `src/pap/web/plantillas/`, `src/pap/web/estatico/` (`estilo.css`, `app.js`); textos en `curados/web/textos.yaml` (`paginas`, `mensajes`) y rótulos de `curados/motor/textos/capas.yaml`; parámetros en `curados/web/parametros.yaml` (`paginas`); especificación en `docs/especificaciones/api.md`; pruebas en `tests/web/test_paginas.py` (con `tests/web/_html.py`, un lector de HTML sin dependencias nuevas).

## Qué ve una persona

- **Inicio** (`/`): una caja para escribir, tres ejemplos que se tocan, los temas de hoy con las fuentes de los datos y un enlace al formulario guiado (`/guiado`; lo construye S3-05, hoy da «no encontramos esa dirección»).
- **Respuesta**: Entendimos, respuesta corta, cifra clave con su fuente, lo más cercano que sí tenemos, ojo al leer, la confianza (solo la frase «Confianza en los datos: …»), qué puedo hacer, y dos desplegables cerrados: Más contexto y Para citar y verificar (con enlace al documento oficial, glosario y versión de la biblioteca). En «no se puede», lo que no se puede va primero.
- **Aclaración**: la pregunta, lo que la persona escribió (marcado) y un botón por opción. Cada botón reenvía la misma entrada con la elección acumulada en un campo oculto («1» pasa a «1,2»).
- **Avisos**: textos fijos de la web (sin la frase que manda a la terminal). Si el LLM no está disponible o se llegó al tope, llevan el enlace al formulario guiado. Los errores (422) tienen su texto y la caja para escribir de nuevo.
- Al enviar, el botón dice «Buscando…» (único JavaScript, `/estatico/app.js`); sin él todo funciona igual.

## Criterios de aceptación

- [x] **Prueba de números en verde para Q1–Q4, la matriz reducida y el conjunto con grabaciones.** `test_ningun_numero_fuera_del_json_q1_q4`, `…_matriz_reducida`, `…_conjunto_con_grabaciones` (`-s` imprime los conteos):

  | Grupo | Páginas | Números revisados | Ecos de la aclaración |
  |---|---|---|---|
  | Q1–Q4 | 4 | 371 | 0 |
  | Matriz reducida (`q1_abancay_elegir_1` + 60 de la matriz) | 61 | 1 262 | 0 |
  | Conjunto de evaluación (158, caché nueva por caso) | 158 | 4 250 | 36 |

  Texto de todos los nodos del `<body>` (con los `<details>` cerrados; sin `script`, `style` ni atributos), números con `\d[\d   .,]*`; cada uno aparece en una cadena ya escrita de `entendimos`, `capas` (sin `ids`, `id_cifra`, `url`, `ficha`, `nivel`), `alternativas`/`temas_disponibles`/`aclaracion`, el rótulo de versión o los YAML de textos. No valen `valor`, `ic_inf`… ni la huella. Lo que repite la pregunta se comprueba aparte: solo la aclaración por texto lo repite, en un único `<q data-eco>` igual a lo escrito (36 de 36). `test_el_detector_de_numeros_atrapa_un_numero_inventado` prueba el detector; además se comprobó a mano que un «41,7 %» metido en la plantilla hace fallar la prueba (y se revirtió).
- [x] **Ningún texto visible escrito en HTML ni en Python.** `test_los_textos_visibles_no_estan_en_el_js_ni_en_las_plantillas` (las plantillas, sin etiquetas ni Jinja, no tienen palabras; el JS no tiene cadenas con espacios ni «Buscando»); los textos de `paginas.py` y `app.py` salen de `tx`.

## Tarea 9 y seguridad

- Orden de bloques: `test_orden_de_bloques_q1_q4` (4), `test_orden_de_bloques_en_toda_la_matriz_y_la_base_q` (61 páginas), `test_orden_de_bloques_con_entendimos_por_texto`, `test_no_se_puede_pone_primero_lo_que_no_se_puede`, `test_no_se_puede_por_texto_con_entendimos_y_temas_disponibles`, `test_cada_bloque_sale_de_su_campo_y_el_enlace_oficial_es_un_ancla`, `test_sin_bloque_de_ficha_tecnica`.
- Confianza: `test_confianza_solo_el_texto_sin_clase_por_nivel_ni_rotulo_de_ficha[q1–q4]`; el CSS no tiene clases por nivel (`test_estilo_movil_primero_letra_base_y_modo_oscuro`).
- Aclaración: `test_aclaracion_dos_lugares_elegir_acumulado_con_consulta` (Ayaviri, de nada a «1» y a «1,2»), `…_con_texto_y_entendimos` (`m11`: tema y luego «Lima», conserva `entendimos`), `test_aclaracion_sin_opciones_ofrece_la_caja_de_texto`.
- Sin JavaScript: las pruebas envían formularios como un navegador sin JS (`_html.formulario`); `test_un_solo_js_y_un_solo_css_propios` (sin manejadores ni estilos en línea).
- CSP, cookies, orígenes: `test_cabecera_csp_sin_cookies_y_sin_origenes_externos` (sin `Set-Cookie`; ningún `src`, `href` de recursos ni `action` externo; solo las anclas a documentos oficiales pueden ser `http`).
- Mensajes: `test_mensajes_fijos_de_la_web_sin_texto_de_terminal`, `test_sin_llm_el_mensaje_lleva_el_enlace_al_formulario_guiado`, `test_cache_vencida_muestra_el_mensaje_con_la_caja_de_texto`, `test_errores_de_forma_con_texto_de_la_web_y_estado_de_la_api`, `test_texto_vacio_vuelve_al_inicio_con_su_aviso`, `test_la_pagina_de_preparacion_usa_el_texto_de_la_web`.
- La API no cambia: `tests/web/test_servicio.py` sigue en verde (equivalencia con la base) y `test_la_api_no_cambia_por_las_paginas`.

## Comandos

- `uv run pytest -q tests/web tests/test_sin_secretos.py`: 49 pasan (35 nuevas en `test_paginas.py`, 13 de S3-03 y la de secretos); unos 150 s.
- Antes de las páginas, las 32 pruebas nuevas que ejercían rutas fallaban (RED: 404 en `/`, `/preguntar` y `/estatico/…`).

## Supuestos (tipo B)

- **S3-04-a:** la política de seguridad lleva además `form-action 'self'`, `frame-ancestors 'none'` y `base-uri 'none'`; y se mandan `Referrer-Policy: no-referrer` y `X-Content-Type-Options: nosniff` (`parametros.yaml` → `paginas.csp`).
- **S3-04-b:** motivos de `mensaje` que llevan el enlace al formulario guiado: `no_disponible` y `tope_diario` (S3-07 fija el nombre real del motivo del tope) (`parametros.yaml` → `paginas.mensajes_con_enlace_guiado`).
- **S3-04-c:** los avisos de la web (`textos.yaml` → `mensajes`) son los textos del intérprete sin la frase de la terminal; `no_disponible` y `tope_diario` ofrecen «elegir las opciones paso a paso» y `otro` es el texto para un motivo desconocido.
- **S3-04-d:** en «no se puede», la respuesta corta va antes que «Entendimos» (R-04). En una aclaración no se muestra «Entendimos»; sí lo que la persona escribió.
- **S3-04-e:** de `alternativas` solo se muestran las que traen `consulta_minima` (botón «Preguntar esto» que la envía como consulta); las demás ya están dichas en `lo_mas_cercano.texto`. `temas_disponibles` se muestra como lista de nombres.
- **S3-04-f:** si la caché venció (o la elección no vale) sale el texto web `errores.eleccion_invalida` con la caja de texto vacía; la web no distingue entre «venció» y «número inválido».
- **S3-04-g:** textos de inicio (`paginas`): la línea de fuentes nombra INEI, Instituto Nacional de Salud y Ministerio de Economía y Finanzas; los ejemplos son los de S3-03. El dueño debe revisarla.
- **S3-04-h:** texto vacío: aviso `paginas.texto_vacio` (422), sin llamar al motor.

## Vacíos tipo C

Ninguno detenido. Por revisar con el dueño: el rótulo del botón de las alternativas (S3-04-e) y la línea de fuentes (S3-04-g).

Suite completa en el Mac (6/11/2026, antes del commit): 1089 pasan, 0 fallan (incluye regresión Q1–Q4, matriz reducida y equivalencia web).
