# Cierre del slice 3: API y web mínima (7/11/2026)

## Qué puede hacer ahora el usuario

Usar Pregúntale al Perú **desde el celular**, en una página web que corre en el Mac del dueño (local o en la red de la casa, con `uv run pap servir --red-local`):

- **Escribir la pregunta** o **armarla con un formulario de dos pasos** (tema y qué quiere saber; después el lugar y el año), sin depender del LLM.
- **Resolver una aclaración tocando una opción** (por ejemplo, cuál «Ayaviri» o qué nivel de «Huancavelica»).
- **Leer la respuesta por capas:**
  - primero «Entendimos…» y la respuesta corta, con su cifra clave y «Ojo al leer»;
  - después «Más contexto» y «Para citar y verificar» como desplegables, con la cita, la versión de la biblioteca y el **enlace al documento oficial** de cada cifra.

Todo es la misma respuesta del motor: la web no calcula, no redacta y no cambia cifras.

## Definición de hecho, punto por punto

| # | Punto | Cumple | Evidencia |
|---|---|---|---|
| 1 | Desde un celular (360 px): escribir o usar el formulario, resolver una aclaración tocando una opción, leer por capas con cita, versión y enlaces oficiales | sí | revisión con Playwright a 360 px ([revision_usuario_s3.md](revision_usuario_s3.md)); prueba del dueño en su celular (7/11/2026, sin observaciones) |
| 2 | Equivalencia: la API devuelve exactamente el `respuesta.json` del motor para Q1–Q4, la matriz reducida y la evaluación con grabaciones (162 preguntas), sin exclusiones; ningún número visible fuera del JSON o de un YAML | sí | `tests/web/test_servicio.py` y `test_paginas.py` en la suite completa ([s3-11/pytest_completo.txt](s3-11/pytest_completo.txt)) |
| 3 | Tiempo con el motor precalentado: sin LLM p95 < 2 s; con texto libre, el objetivo de S3-08; «Buscando…» visible | sí | sin LLM: p95 0,26 s (página) y 0,26 s (API) en 200 respuestas; por texto con grabaciones: p95 0,79 s ([s3-11/medicion_s3-08.txt](s3-11/medicion_s3-08.txt)); en vivo con el LLM: p95 3,1 s con un objetivo de ≤ 3,5 s ([s3-08_rendimiento.md](s3-08_rendimiento.md)) |
| 4 | Accesibilidad WCAG 2.1 AA: axe sin fallas graves ni críticas, teclado, zoom al 200 %, confianza sin color | sí | axe: 0 fallas en 36 corridas ([s3-06_accesibilidad.md](s3-06_accesibilidad.md)); desde S3-11 la prueba también falla si axe no revisó nada |
| 5 | Privacidad (P-03): la pregunta no queda en registros, archivos ni trazas (salvo la caché de 24 h); nada de terceros, sin cookies | sí | `tests/web/test_privacidad.py` ([s3-07_privacidad.md](s3-07_privacidad.md)) |
| 6 | Límite por IP y tope diario del LLM; al llegar al tope, se ofrece el formulario | sí | `tests/web/test_limites.py` ([s3-07_privacidad.md](s3-07_privacidad.md)) |
| 7 | `pap servir` en local; la imagen Docker baja la biblioteca, comprueba su huella y responde `/salud`; sin despliegue público | sí | [s3-09_imagen.md](s3-09_imagen.md) |
| 8 | Revisión independiente en celular «apto», documentación al día, etiqueta `slice-3-cerrado` | sí | revisión: «apto con observaciones», con las correcciones aplicadas; revisión del código por partes: 13 de 13 aprobadas ([revision_por_partes.md](revision_por_partes.md)); documentación al día (S3-11). Etiqueta `slice-3-cerrado` creada tras la fusión |

## Comprobaciones finales (7/11/2026)

| Comprobación | Resultado | Archivo |
|---|---|---|
| Suite completa (`uv run pytest -q`) | 1258 pasan, 1 se salta (la que genera capturas, solo con `PAP_CAPTURAS=1`) | [s3-11/pytest_completo.txt](s3-11/pytest_completo.txt) |
| Regresión Q1–Q4 | dentro de la suite; las diferencias de texto de Q1 (H-07) y Q3 (H-05) las aprobó el dueño | `backlog/slice-1/evidencia/regresion/` |
| Matriz completa | 5086 casos, 0 con fallos (respondida 2087, «no se puede» 2997, aclaración 2, error 0) | [s3-11/matriz_completa.md](s3-11/matriz_completa.md) |
| Evaluación con grabaciones (162 preguntas) | cumple todos los umbrales (consulta exacta 98 %, aclaraciones 100 %, inyección sin efecto 100 %) | [s3-11/evaluacion.md](s3-11/evaluacion.md) |
| Enlaces de las citas | 34 enlaces, 1 con falla: RENIEC, con el certificado vencido (W-06, ya conocida) | [s3-11/enlaces.txt](s3-11/enlaces.txt) |
| Medición de S3-08, sin LLM | p95 0,26 s; arranque hasta `/salud` 200 en 4,2 a 4,6 s | [s3-11/medicion_s3-08.txt](s3-11/medicion_s3-08.txt) |

**Peso de las páginas:** la respuesta de Q1 pesa 6,3 KB sin comprimir (el límite es 100 KB), sin imágenes ([s3-06_accesibilidad.md](s3-06_accesibilidad.md)).

**Costo del LLM en vivo en el slice:** S3-07 y S3-08 ≈ US$ 0,12; S3-10: US$ 0,07 de US$ 0,50.

**Arreglos de S3-11** (de la revisión por partes, pedidos por el dueño):
- `/salud` responde 503 «error_precalentamiento» si el precalentamiento falló, en vez de «ok».
- Al volver atrás en el navegador, los botones ya no quedan desactivados ni en «Buscando…».
- La prueba de axe falla si axe no revisó ninguna regla.
- El chequeo de comparaciones de la matriz ya no da un falso aviso con «Lima Región» y «Lima Metropolitana»: comparaba el nombre escrito con el nombre que lleva el rótulo entre paréntesis. La respuesta estaba bien (32,2 % frente a 25,3 %).

## Fusión y cierre (7/11/2026)

- El dueño escribió «fusiona».
- El PR #3 se fusionó en `main` con un commit de merge (`3103961`).
- La etiqueta `slice-3-cerrado` se creó sobre ese commit y se subió a GitHub.
- La suite completa en `main` después de la fusión: 1258 pasan y 1 se salta (la de capturas).
- El código de S3-11 también pasó la revisión independiente, con 7 observaciones que no bloquean. Con eso están revisadas todas las historias con código; S3-00 es una sola línea de documentación y no se revisa.
- Las ramas `slice-3` y `claude/determined-einstein-lwwemc` se conservan.

## Qué quedó fuera

- Despliegue público, dominio y HTTPS (slice 4, P-05).
- Cuentas, historial, mapas, gráficos y descargas.
- «¿Qué puedo hacer?» no se muestra en la web hasta que el dueño apruebe X-01 (el JSON y la CLI no cambian).
- En provincias y distritos, el «¿sirvió?» y el cruce del gasto no abren con el aviso de u13: no entraba en las 125 palabras y la frase de la cifra ya dice qué cubre (decisión del dueño, W-10).

## Supuestos aplicados que el dueño debe revisar

Están todos en [consultas_al_dueno.md](../consultas_al_dueno.md), «Supuestos aplicados»: S3-01-a a d, S3-03-a a d, S3-01b-a a e, S3-04-a a h, S3-05-a a g, S3-07-a a d, S3-08-a a c, S3-09-a a d y S3-10-a a e. Los que piden una lectura en particular:

- **S3-04-e:** el rótulo «Preguntar esto».
- **S3-04-g:** la línea de fuentes del inicio.
- **S3-05-f:** los textos del formulario.
- **S3-10-b:** la tarjeta «Cuántos se midieron la hemoglobina».
- **S3-10-c:** ENDES en desnutrición, «… y mide la talla de los niños».

## Consultas abiertas

Ninguna bloquea:
- **W-01:** subir la etiqueta `slice-2-cerrado` (la sube el dueño).
- **W-03:** H17 y H18.
- **W-04:** H-G, la altitud de los distritos (el dueño agregará los datos).
- **W-06:** el enlace de RENIEC con el certificado vencido.
- **W-09:** la IP detrás de un proxy (slice 4).
- **H-07 de W-11:** ¿qué texto llevan las citas propias de gasto y del SIEN?
- **X-01:** «¿Qué puedo hacer?».
- **X-05 y X-07:** son requisito antes de que entre gente de fuera.

## Qué se aprendió para el slice 4

- **El tope de 125 palabras de la capa 1 (R-04) es la restricción que más pesa** al sumar avisos: el aviso de u13 y la oferta de X-22 no entran juntos en efecto, cruce, comparación ni evolución. Antes de agregar texto a la capa 1, medir el peor caso con un barrido (como en S3-10).
- **La revisión con personas encuentra lo que las pruebas no ven.** Ninguna cifra estaba mal, pero el nivel del lugar y el alcance del gasto se podían leer mal. Conviene repetir la revisión con usuarios en el slice 4, con gente de fuera.
- **Revisar por historias.** Un slice entero no entra en una sola revisión independiente; hay que revisar el código de cada historia por separado y dejar la evidencia generada (JSON de la base, capturas) en commits aparte.
- **Correr la matriz completa en cada cierre, no solo la reducida:** fue la que encontró el falso aviso del chequeo de comparaciones.
- **Para varios usuarios (slice 4):**
  - contadores de límites fuera de memoria;
  - medir el candado del motor con varios usuarios a la vez;
  - registrar la traza de un error interno sin la pregunta;
  - escapar los saltos de línea del registro de accesos;
  - que `pap servir` avise que está listo después de abrir el puerto;
  - revisar la imagen escuchando en todas las interfaces.

  Detalle en [revision_por_partes.md](revision_por_partes.md) y en `backlog/plan_slices.md`.
