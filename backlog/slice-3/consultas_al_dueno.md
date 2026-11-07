# Slice 3 — Consultas al dueño

Mismas reglas que los slices anteriores (`agents.md` §5). Tipo C o D: «Consultas que bloquean». Tipo B: «Supuestos aplicados».

## Consultas que bloquean (vacíos tipo C o D)

### W-01 — La etiqueta `slice-2-cerrado` no se pudo subir desde la nube (S3-00) · abierta (no bloquea)
- **Qué pasa:** el slice 2 se fusionó en `main` ([PR #2](https://github.com/LaurenteEber/preguntale-al-peru/pull/2), `e1a0d0f`). La etiqueta se creó en local, pero el push de etiquetas desde este entorno se corta («the remote end hung up»), aunque el de ramas funciona.
- **Propuesta:** desde el Mac: `git fetch origin main && git tag -a slice-2-cerrado e1a0d0f -m "Slice 2 cerrado" && git push origin slice-2-cerrado`.

### W-02 — H21: quitar los porcentajes de «Más contexto» de Q4 también quita un aviso (S3-02) · cerrada sin aplicar (dueño, 6/11/2026, S3-01b punto 14)
- **Qué pasa:** la historia pide que «Más contexto» de Q4 muestre solo el rango del grupo (35,7 % a 39,8 %) y no los porcentajes de los siete departamentos. Lo probé: el texto cambia como se pidió, pero **también desaparece el aviso «Estas cifras vienen de fuentes de distinto tipo (encuesta a hogares, estimación con modelo)…»** y la regla R-LENGUAJE-06 (rotular) deja de dispararse, porque esa regla se activa cuando el texto mezcla cifras de distinta naturaleza. Quitar un aviso no es «decir lo mismo de otra forma» (`agents.md` §5.1, condición 2), y ante la duda es tipo C.
- **Por qué importa:** la respuesta sigue mostrando juntos el Mapa de Pobreza 2018 (modelo) y el grupo de ENAHO 2025 (encuesta); sin el aviso, esa diferencia queda solo en «Ojo al leer» y en «Límites».
- **No se hizo:** el texto de `identificar_extremo.yaml` queda como estaba; Q4 no cambia.
- **Propuesta:** (a) aprobar la pérdida del aviso (el cambio de texto ya está probado; se aplica en una línea de `curados/motor/textos/plantillas/identificar_extremo.yaml`: quitar «En orden alfabético: {items}.»), o (b) conservar el aviso: pide un cambio de código (que «Más contexto» nombre a los departamentos sin porcentaje), fuera de lo que S3-02 permite. Recomiendo (a).

### W-03 — H17 y H18: el dueño no los marcó (S3-02, caso B) · pendiente del dueño (no bloquea)
- **Qué pasa:** la tabla de S3-02 los deja en blanco (☐), así que no se hicieron y no se tocó `reglas/` ni `ajustes_dueno.py`. Siguen con el texto de hoy: H17 «solo sabemos de los que se les midió la hemoglobina»; H18 «nada sobre provincias o distritos concretos… para Lima Metropolitana».
- **Para aplicarlos:** el dueño marca la columna con la fecha en `S3-02-observaciones-y-base.md`; entonces se cambian solo por `reglas/consolidador/ajustes_dueno.py` y `consolida_reglas.py`.

### W-04 — H-G: cifras del SIEN muy altas en distritos con mucha diferencia de altura (S3-01b, punto 5) · pendiente del dueño (no bloquea)
- **Qué pasa:** San Antonio (Huarochirí, 150716) da 94,9 % de anemia (1 516 de 1 597 niños). El INS publica lo mismo (Cuadro 15), así que no es un error nuestro de cálculo. Pero la hemoglobina sin ajustar de esos niños tiene mediana 11,5 g/dL (normal), y el 95 % sale de ajustarla por 3 456 m, la altura de la capital del distrito, aunque la mayoría se atiende en anexos de Jicamarca, mucho más abajo. Lo mismo puede pasar en Santo Domingo de los Olleros; Incahuasi, Pullo y Unión Progreso sí están en altura. El informe gerencial del INS (p. 11) dice que ajusta por la altura de la residencia del niño, pero el dato usa la de la capital (choca también con S-01). Detalle: `evidencia/s3-01b/correcciones.md`.
- **Decisión del dueño (6/11/2026):** «lo dejamos pendiente, luego agrego datos de altura para cada distrito». No se cambió ningún dato ni regla.

### W-05 — u13: qué cubre la cifra de gasto (S3-01b, punto 3) · cerrada: aprobada por el dueño el 6/11/2026 y aplicada
- **Qué pasa:** «¿Cuánto gastó el gobierno en anemia en Lima?» responde «S/ 260,6 millones es lo que se gastó en 2025 en servicios de salud y nutrición infantil…»; lo que la cifra no cubre llega después.
- **Propuesta:** que toda respuesta de gasto (nivel actual) abra con lo que cubre y lo que no, y la cifra vaya después. Lima: «Esta cifra no es solo de anemia: es de todos los servicios de salud y nutrición infantil, y no incluye lo que gastan las entidades nacionales con sede en Lima.» Otras regiones: «…y solo cuenta lo que registran las entidades con sede en {lugar}.» Municipios: «…y solo cuenta a la municipalidad y las obras ubicadas en {lugar}.» El «Ojo al leer» que repite lo mismo se quita. Aplicada (nacional: «…de todas las entidades públicas del país.»).

### W-06 — Enlace oficial de RENIEC con certificado vencido (S3-01b, punto 8) · abierta (no bloquea)
- **Qué pasa:** `scripts/comprobar_enlaces.sh` da 33 de 34 enlaces bien; falla `portales.reniec.gob.pe/web/estadistica/identificada` («certificate has expired»). Es la página oficial; el problema es de RENIEC.
- **Propuesta:** dejarla como está y volver a probar al cierre del slice; si sigue fallando, buscar el mismo dato en gob.pe/reniec.

### W-07 — No hay release de la biblioteca del cubo actual (S3-01b, punto 10) · cerrada: release `biblioteca-010ea965` publicado el 6/11/2026 (autorizado por el dueño) y valor por defecto del script
- **Qué pasa:** el único release es `biblioteca-ba1fbc55`; el cubo actual es `010ea965`. En la nube, `bajar_biblioteca.sh` + `pap calcular` reconstruye el cubo, pero el release no coincide con la huella de hoy.
- **Propuesta:** publicar `biblioteca-010ea965` desde el Mac (empaquetar `biblioteca/` sin crudos, como el anterior) y cambiar el valor por defecto del script.

### W-08 — pd02: «¿en Huancavelica los niños siguen con anemia como antes?» (S3-01b, punto 12) · cerrada: el dueño acepta la aclaración (6/11/2026)
- **Qué pasa:** se esperaba una evolución de la anemia en Huancavelica; el intérprete pide aclarar entre «cómo cambió» y «cuánto hay hoy» (como en tu prueba). Es lo más prudente, pero cuenta como falla en la evaluación (los umbrales globales se cumplen).
- **Propuesta:** aceptar la aclaración como resultado esperado (`resultado: aclaracion`, `intencion_ambigua`).

### W-09 — Para el slice 4: la IP detrás de un proxy (S3-07) · abierta (no bloquea)
- **Qué pasa:** el límite por IP usa la IP que ve la aplicación. En la red de la casa es la del celular. Detrás de un proxy o un balanceador (slice 4) sería la del proxy, y el límite se aplicaría a todos juntos.
- **Propuesta:** con el despliegue, lanzar uvicorn con las cabeceras de proxy del servidor de confianza. Hoy no aplica (P-05).

### W-10 — H-02 (S3-10): el gasto en «¿sirvió?» y en cruces, sin el aviso de alcance de u13 · cerrada: aprobada por el dueño el 7/11/2026 y aplicada
- **Qué pasa:** u13 se aprobó para el gasto de «¿cuánto hay hoy?». En «efecto» y «cruce» (w17: «¿El gasto sirvió en Lima Metropolitana?») la cifra de S/ 260,6 millones sale sin decir antes que no es solo anemia ni que no incluye a las entidades nacionales con sede en Lima. El revisor lo clasificó alto. La frase rota «lo gastado :» ya se corrigió («lo gastado en Lima Metropolitana:»).
- **Propuesta:** extender la apertura de u13 a las respuestas de efecto y cruce con gasto, con los mismos textos. Cambia la capa 1 de Q3; se aprobaría como «dueño» en la regresión.
- **Respuesta del dueño (7/11/2026):** «Sí, mismos textos». Con los mismos textos, en provincia y distrito la capa 1 pasaba de 125 palabras (tope de R-04: hasta 141). El dueño eligió entonces: **sin apertura en provincia y distrito**, donde la frase de la cifra ya dice «solo de la municipalidad y de obras ubicadas…».
- **Aplicado:** la apertura va en efecto y cruce para departamento, ámbitos de Lima, Callao y Perú. Para entrar en el tope, en esos casos la frase de la cifra no repite «servicios de salud y nutrición infantil» (lo dice la apertura), el cruce dice «La cifra clave es el gasto.» y la oferta de X-22 va primero en «Avisos» (supuesto S3-10-a). Barrido de 72 respuestas de efecto y cruce: máximo 125 palabras. Q3 (distrito) no lleva la apertura.

### W-11 — Hallazgos medios de la revisión S3-10 · aplicados (dueño, 7/11/2026), salvo lo que se indica
Detalle y capturas en `evidencia/revision_usuario_s3.md`:
- H-03: «¿Qué puedo hacer?» pendiente de revisión se ve en público (X-01).
- H-04: la tarjeta de cobertura de hemoglobina no dice que no es anemia.
- H-05: «Gasto en 2024» no explica por qué ese año ni que está en soles de 2025.
- H-06: el glosario no se adapta al tema.
- H-07: las citas de cálculo propio enlazan a portales genéricos.
- H-08: el formulario con un lugar mal escrito no sugiere nada y reinicia.
- H-09: «Espera un momento.» pierde lo escrito.
- H-10: la aclaración repite «distrito Ayaviri».
- **Decisión del dueño (7/11/2026):** H-03 se oculta solo en la web mientras X-01 no esté aprobada (`curados/web/parametros.yaml` → `paginas.mostrar_que_hacer_sin_revisar`); se aplican H-04, H-05, H-06 y H-07; H-08, H-09, H-10 y H-14 son de tipo A/B y se arreglaron (ver `evidencia/revision_usuario_s3.md`).
- **Queda abierto (H-07):** el agregado «no hay tabla publicada con esta cifra; se calcula de microdatos» solo va en cifras de encuestas (ENDES). Las citas de gasto (MEF) y del SIEN siguen enlazando al portal de datos, sin ese agregado: decir «microdatos» de un registro o del gasto no sería exacto. Si quieres un texto para ellas, dímelo.

## Supuestos aplicados (vacíos tipo B)

| ID | Historia | Qué se supuso | Dónde vive |
|---|---|---|---|
| S3-01-a | S3-01 | El texto de la tarjeta «Gasto en Lima Metropolitana en 2024» (X-03) dice «registrado por unidades ejecutoras con sede en Lima Metropolitana», como la tarjeta del gasto de 2025. Sin esa frase, la regla R-LENGUAJE-02 (todo gasto nombra su base ejecutora) la marcaba. Es la misma información, sin afirmaciones nuevas | `curados/motor/textos/plantillas/cruce_efecto.yaml` → `tarjetas.mismo_anio.texto` |
| S3-01-b | S3-01 | El enlace de cada cita sale de `cifras_doradas.csv` (columna `url`) cuando la cifra tiene dorada y, si no, del portal de la fuente en `catalogo_fuentes.csv` (`url_portal`, si no `url_datos`). Si no hay enlace oficial, el campo va vacío. En el `.md` el enlace se muestra como «[Documento oficial](url)» al final de la cita. Las citas de ENDES sin dorada apuntan al portal de microdatos del INEI, no al informe del año | `src/pap/motor/capas.py` (`_url`); texto del enlace en `curados/motor/textos/capas.yaml` → `rotulos.enlace_oficial` |
| S3-01-c | S3-01 | `capa3` suma `citas` = lista de `{texto, url, id_cifra}`, con las mismas líneas que `para_citar` (que no cambia). La web lee `citas`. Se eligió una lista aparte para no cambiar la forma de `para_citar`, que usan la matriz y varias pruebas | `src/pap/motor/capas.py` |
| S3-01-d | S3-01 | Además de los 8 rótulos que pedía la historia, se movió a YAML «Cómo citar» (rótulo de la lista de citas) y se agregó «Documento oficial» (texto del enlace). El `.md` de Q1–Q4 solo cambia por los enlaces y por X-02/X-03 | `curados/motor/textos/capas.yaml` → `rotulos` |
| S3-03-a | S3-03 | Servidor local en 127.0.0.1:8000 (el de producción lo fija S3-09) | `curados/web/parametros.yaml` → `servicio` |
| S3-03-b | S3-03 | Topes de la entrada: `texto` hasta 2000 caracteres; `elegir` hasta 4 números, cada uno entre 1 y 50; se acepta un número o una lista | `curados/web/parametros.yaml` → `pregunta` |
| S3-03-c | S3-03 | Las pruebas esperan hasta 120 s a que termine el precalentamiento | `curados/web/parametros.yaml` → `precalentamiento` |
| S3-03-d | S3-03 | Estado HTTP: 200 para cualquier respuesta del motor (incluidos los mensajes fijos), 503 para `mensaje` con `motivo: no_disponible` y para «preparando», 422 para entradas inválidas. Tabla en `docs/especificaciones/api.md` | `curados/web/parametros.yaml` → `http`; `curados/web/textos.yaml` |
| S3-01b-a | S3-01b | X-22: la frase que ofrece la provincia o el distrito va ahora primero en «Ojo al leer» (capa 1), salvo en comparación y evolución, donde va primero en «Avisos» (capa 2) porque en comparación (dos departamentos a secas) y en evolución de anemia la capa 1 pasaría del máximo de 125 palabras; antes (S3-01b) iba en «Avisos». Cambiado tras la revisión S3-10 (H-01): quien lee «en Huancavelica» puede pensar en el distrito. Solo nombra los niveles que existen con ese nombre | `curados/motor/textos/territorio.yaml` → `oferta_otros_niveles` |
| S3-01b-b | S3-01b | Interruptor `territorio.departamento_a_secas.activo` (con `false` vuelve la aclaración de antes; lo usa la prueba de la base del slice 2) | `curados/motor/parametros_motor.yaml` |
| S3-01b-c | S3-01b | Alias «lurigancho chosica» y «lurigancho-chosica» → 150118 (H-J) | `curados/motor/textos/territorio.yaml` → `alias_distrito` |
| S3-01b-d | S3-01b | `comprobar_enlaces.sh` usa un agente de navegador (`-A 'Mozilla/5.0'`): datosabiertos.gob.pe responde 418 a curl sin él | `scripts/comprobar_enlaces.sh` |
| S3-01b-e | S3-01b | Evaluación: pd09 «la municipalidad» = gasto del lugar; pd17 (inyección) = no responder | `tests/interprete/evaluacion.yaml` (notas) |
| S3-04-a | S3-04 | La política de seguridad de las páginas suma `form-action 'self'`, `frame-ancestors 'none'`, `base-uri 'none'`, `Referrer-Policy: no-referrer` y `nosniff` | `curados/web/parametros.yaml` → `paginas.csp` |
| S3-04-b | S3-04 | Llevan enlace al formulario guiado los mensajes `no_disponible` y `tope_diario` | `curados/web/parametros.yaml` → `paginas.mensajes_con_enlace_guiado` |
| S3-04-c | S3-04 | Los avisos de la web son los textos del intérprete sin la frase de la terminal; `otro` cubre un motivo desconocido | `curados/web/textos.yaml` → `mensajes` |
| S3-04-d | S3-04 | En «no se puede», la respuesta corta va antes que «Entendimos» (R-04); en una aclaración se muestra lo que escribió la persona, no «Entendimos» | plantillas web |
| S3-04-e | S3-04 | De `alternativas` solo salen las que traen consulta, como botón «Preguntar esto» (**revisar el rótulo**) | `curados/web/textos.yaml` |
| S3-04-f | S3-04 | Si la caché venció o la elección no vale: el texto de elección inválida y la caja vacía (la web no distingue los dos casos) | `curados/web/textos.yaml` → `errores.eleccion_invalida` |
| S3-04-g | S3-04 | La línea de fuentes del inicio nombra INEI, Instituto Nacional de Salud y Ministerio de Economía y Finanzas (**revisar**) | `curados/web/textos.yaml` → `paginas` |
| S3-04-h | S3-04 | Texto vacío: aviso y 422, sin llamar al motor | `curados/web/textos.yaml` → `paginas.texto_vacio` |
| S3-05-a | S3-05 | Los rótulos del paso 1 son los de `/api/opciones`; los nombres de `no_se_puede.yaml` solo van dentro de la pregunta armada | `curados/web/textos.yaml` → `guiado` |
| S3-05-b | S3-05 | Campos por intención y armado del periodo | `curados/web/parametros.yaml` → `guiado` |
| S3-05-c | S3-05 | El segundo lugar de una comparación también admite «Todo el Perú» | `curados/web/parametros.yaml` → `guiado` |
| S3-05-d | S3-05 | El lugar admite hasta 200 caracteres | `curados/web/parametros.yaml` → `guiado` |
| S3-05-e | S3-05 | Año con cuatro cifras; si hay lugar y «Todo el Perú» a la vez, se pide dejar uno | `curados/web/textos.yaml` → `guiado` |
| S3-05-f | S3-05 | Rótulos, ayudas, plantillas de `pregunta_original` y avisos del formulario (**revisar**) | `curados/web/textos.yaml` → `guiado` |
| S3-05-g | S3-05 | Niveles en el orden de `/api/opciones`, sin «Todo el Perú» | `curados/web/parametros.yaml` → `guiado` |
| S3-07-a | S3-07 | Límite por IP: 10 preguntas por minuto (ventana de 60 s) → «Espera un momento.» (429) | `curados/web/parametros.yaml` → `limites` |
| S3-07-b | S3-07 | Tope diario: 300 llamadas reales al LLM (reintentos incluidos, la caché no cuenta), día de Lima; al llegar, la caja de texto se desactiva y lleva al formulario (503 en la API) | `curados/web/parametros.yaml` → `limites` |
| S3-07-c | S3-07 | Cuerpo máximo de 8 192 bytes (413) | `curados/web/parametros.yaml` → `limites` |
| S3-07-d | S3-07 | `tope_diario` es el motivo del tope (confirma S3-04-b) | `curados/web/parametros.yaml` → `paginas` |
| S3-09-a | S3-09 | La imagen escucha en la red (`--red-local`, 0.0.0.0) porque está dentro de un contenedor; el puerto sale de `PAP_PUERTO` (8000) | `Dockerfile`, `scripts/arranque_imagen.sh` |
| S3-09-b | S3-09 | El `HEALTHCHECK` lee `PAP_PUERTO` y espera 180 s al precalentamiento | `Dockerfile` |
| S3-09-c | S3-09 | Al arrancar, si el cubo no es el del manifiesto, se corre `pap calcular --permitir-sucio` (la imagen no lleva `.git`) | `scripts/arranque_imagen.sh` |
| S3-09-d | S3-09 | uv se instala con pip solo para construir la imagen (no es una dependencia del proyecto) | `Dockerfile` |
| S3-08-a | S3-08 | Texto libre: p95 ≤ 3,5 s (p95 de 2,5 s medido en S2-09, más 1 s) y máximo ≤ 10 s. Medido: p95 3,1 s y máximo 4,5 s en 20 preguntas en vivo | `curados/web/parametros.yaml` → `rendimiento` |
| S3-08-b | S3-08 | Arranque hasta `/salud` 200: ≤ 30 s (medido 4–5 s; 25 s en frío tras `uv sync`) | `curados/web/parametros.yaml` → `rendimiento` |
| S3-08-c | S3-08 | Medición: semilla 3008, 20 preguntas en vivo y 50 por uvicorn real | `tests/web/medir.py` |
| S3-10-a | S3-10 | Oferta de X-22 (provincia o distrito) primero en «Avisos» también en efecto y cruce: con la apertura del gasto (W-10), la capa 1 pasaba de 125 palabras | `src/pap/motor/preguntar.py` → `_OFERTA_EN_AVISOS` |
| S3-10-b | S3-10 | H-04: tarjeta «Cuántos se midieron la hemoglobina (Puno)» con el texto de la tarjeta de cobertura del SIEN (**revisar**) | `curados/motor/textos/plantillas/cruce_efecto.yaml` → `tarjetas.cobertura` |
| S3-10-c | S3-10 | H-06: ENDES se define según el tema. Anemia: igual que antes; desnutrición: «… y mide la talla de los niños»; sin tema: sin la última parte (**revisar**). «Cambio estadísticamente claro» solo con cifras de encuesta o de modelo | `curados/motor/textos/glosario.yaml` → `endes.por_tema`, `cambio_claro.solo_con_naturaleza` |
| S3-10-d | S3-10 | H-08: con dos lugares en el formulario (comparación) y uno no encontrado, se nombran los dos y se vacían los dos (el motor no dice cuál falló) | `src/pap/web/guiado.py`, `curados/web/textos.yaml` |
| S3-10-e | S3-10 | H-09: «Espera unos segundos y vuelve a intentar.» también en la API (es el mismo texto) | `curados/web/textos.yaml` → `mensajes.espera_un_momento` |

## Pendientes del dueño que siguen abiertos

- **X-01 — texto de «¿Qué puedo hacer?» (R-06):** el dueño todavía no lo aprobó, así que `curados/motor/textos/que_hacer.yaml` → `anemia.revisado_dueno` sigue en `false` y la respuesta conserva «(texto pendiente de revisión)». S3-01 no lo toca. Cuando lo apruebe: poner `true`, pasar R-06 a «vigente» y sacar X-01 de las pendientes.
