# Slice 3 — API y web mínima

Rama `slice-3`, desde `main` en `slice-2-cerrado` (o desde la punta de `slice-2` si su PR sigue abierto, como en S2-00). Fase 5c. Plan general: `../plan_slices.md`.

4/11/2026. Lo revisó un subagente que emuló al implementador contra el repo y el backlog del slice 2; se corrigieron sus 25 hallazgos. S3-00 lo ajusta con el cierre del slice 2.

## Objetivo

Que una persona use el servicio **desde el celular**, en una página web:
- escribe su pregunta, o la arma con un formulario guiado;
- ve primero «Entendimos…» y la respuesta corta;
- abre «Más contexto» y «Para citar y verificar» como desplegables.

Todo es la **misma respuesta del motor**: la web no calcula, no redacta y no cambia cifras. Solo presenta el `respuesta.json`.

```
navegador (HTML servido, casi sin JavaScript)
  → FastAPI (src/pap/web/): POST /preguntar · POST /api/preguntar · GET /guiado · GET /api/version · GET /salud
      → interpretar() del slice 2 (texto libre) o preguntar_minima() (formulario guiado)
      → un Motor cargado una vez y precalentado en segundo plano; una respuesta a la vez (candado)
  → plantillas HTML que solo ordenan campos de respuesta.json y rótulos de YAML
```

**Datos del ensayo del supervisor (4/11/2026), con el motor ya cargado:**
- Una respuesta tarda de 0,01 s a 0,7 s (p50 0,1 s).
- Cargar el contexto y el motor tarda 1,1 s.
- La primera consulta de ranking (Q4) en frío tarda 5,8 s.
- Con texto libre domina el LLM; se mide en S2-09.
- El `Motor` se puede reutilizar entre consultas: la matriz ya lo hace. No tiene conexión DuckDB propia: el cubo es un DataFrame en memoria. El riesgo con hilos son sus cachés perezosas (`ctx._rel_origen`, `ctx._territorio_filas`, `Motor._grupos`, `_TEMAS_CACHE`, los `lru_cache`). Por eso se usa un candado.

## Lo aprendido en el slice 2 (S3-00, 5/11/2026)

Del cierre (`../slice-2/evidencia/cierre.md`):
- **Latencia del LLM** (Claude Sonnet 5.5, esfuerzo bajo; 204 grabaciones del prompt final): p50 1,6 s y p95 2,5 s, con máximo de 3,8 s. En la evaluación, el p95 por pregunta fue de 2,7 s. Con texto libre no se llega a los 2 s: S3-08 fija su objetivo (`supuesto: S3-08`).
- **Costo:** US$ 0,0024 por pregunta con el caché del proveedor caliente, y US$ 0,018 sin caché (5 minutos). El tope diario de llamadas de S3-07 se calcula con eso.
- **Riesgos de P-03 que quedaron:** los nombres de personas no se detectan; la caché de 24 h no se borra, solo deja de usarse; la pregunta se repite como título del `.md` (E-07 del slice 2).
- **Para el dueño, antes de abrir el servicio:** dos lecturas falsas del motor del slice 1 (E-09 del slice 2).
- **Interfaces:** `evidencia/s3-00_interfaces.md`. El tipo `mensaje` ya trae su código en `motivo`.

## Antes de empezar

1. El slice 2 está cerrado; S3-00 lee su `cierre.md`.
2. Lo único que espera al dueño es X-01 y los textos de H17 y H18 (abajo). Nada bloquea el slice: sin respuesta, se sigue con lo de hoy.
3. **Esto no es la beta:** la web corre solo en local y en la red de la casa (P-05). X-05 (revisar lo provisional) y X-07 (visto a las listas de gasto) siguen siendo requisito del slice 4, antes de que la vea gente de fuera.

## Historias (en orden)

| ID | Historia | Estado |
|---|---|---|
| S3-00 | [Preparación](S3-00-preparacion.md) | hecha ([interfaces](evidencia/s3-00_interfaces.md), [base](evidencia/pytest_base.txt): 944 pasan) |
| S3-01 | [Cambios del motor decididos (X-01 a X-04, enlaces de las citas, rótulos)](S3-01-decisiones-motor.md) | hecha ([evidencia](evidencia/s3-01_regresion.md)); X-01 sin aplicar: el dueño no la aprobó |
| S3-02 | [Observaciones bajas aprobadas y base de la web](S3-02-observaciones-y-base.md) | hecha ([evidencia](evidencia/s3-02_observaciones.md)); H14 y H15 aplicadas, H21 pasó a la consulta W-02, H17 y H18 sin marca del dueño (W-03) |
| S3-03 | [Servicio: FastAPI sobre el mismo motor](S3-03-servicio.md) | hecha ([evidencia](evidencia/s3-03_servicio.md)) |
| S3-01b | [Correcciones del motor antes de la web](S3-01b-correcciones-motor.md) | hecha ([evidencia](evidencia/s3-01b/correcciones.md)); H-G pendiente del dueño (W-04) |
| S3-04 | [Páginas: pregunta, respuesta y aclaración](S3-04-paginas.md) | hecha ([evidencia](evidencia/s3-04_paginas.md)); supuestos S3-04-a a h |
| S3-05 | [Formulario guiado, sin LLM](S3-05-formulario-guiado.md) | hecha ([evidencia](evidencia/s3-05_guiado.md), [diferencias](evidencia/s3-05_diferencias.md)); Q1 sin elegir por X-22 |
| S3-06 | [Accesibilidad y celular](S3-06-accesibilidad.md) | hecha ([evidencia](evidencia/s3-06_accesibilidad.md)); axe 0 fallas en 36 corridas; Chromium local |
| S3-07 | [Privacidad, abuso y costo](S3-07-privacidad-abuso.md) | hecha ([evidencia](evidencia/s3-07_privacidad.md)); supuestos S3-07-a a d |
| S3-08 | [Rendimiento](S3-08-rendimiento.md) | hecha ([evidencia](evidencia/s3-08_rendimiento.md)); sin LLM p95 0,27 s; texto en vivo p95 3,1 s |
| S3-09 | [Empaquetado: imagen y `pap servir`](S3-09-empaquetado.md) | hecha ([evidencia](evidencia/s3-09_imagen.md)); imagen probada con Docker (colima) |
| S3-10 | [Revisión independiente en el celular](S3-10-revision-independiente.md) | hecha ([revisión de usuario](evidencia/revision_usuario_s3.md), [revisión por partes](evidencia/revision_por_partes.md)): «apto con observaciones», correcciones aplicadas; prueba del dueño en su celular el 7/11/2026 |
| S3-11 | [Documentación y cierre](S3-11-documentacion-cierre.md) | hecha ([cierre](evidencia/cierre.md)); falta la fusión y la etiqueta `slice-3-cerrado`, cuando el dueño escriba «fusiona» |

Desde S3-03, en cada historia:
- `uv run pytest -q`, en la nube con `-m "not solo_mac and not navegador"` si no hay Chromium;
- la regresión Q1–Q4;
- la matriz reducida;
- la evaluación con grabaciones del slice 2;
- **la equivalencia web** (S3-03).

## Definición de hecho del slice

1. **Desde un celular** (360 px) se puede:
   - escribir una pregunta o armarla con el formulario;
   - resolver una aclaración tocando una opción;
   - leer la respuesta por capas, con su cita, la versión de la biblioteca y **enlaces a las fuentes oficiales**.
2. **Equivalencia:** la API devuelve exactamente el `respuesta.json` de `preguntar_minima()` o de `interpretar()`, sin exclusiones, para:
   - Q1–Q4;
   - la matriz reducida;
   - el conjunto de evaluación con grabaciones.

   Y **todo número visible en la página está escrito en un texto del JSON o de un YAML** (regla exacta en S3-04).
3. **Tiempo**, con el motor precalentado:
   - sin LLM: p95 < 2 s (`plan_slices.md`);
   - con texto libre: el objetivo medido de S3-08;
   - «Buscando…» visible mientras espera.
4. **Accesibilidad:** WCAG 2.1 AA en todas las páginas: axe con 0 fallas graves o críticas, uso con teclado y zoom al 200 %. La confianza va sin color (R-05).
5. **Privacidad (P-03):**
   - ningún registro, archivo ni traza de error guarda el texto de la pregunta, salvo la caché de interpretaciones de 24 h que permite P-03;
   - la página no carga nada de terceros y no usa cookies.
6. **Abuso y costo:** límite por IP y tope diario de llamadas al LLM. Al llegar al tope, se ofrece el formulario guiado.
7. **Empaquetado:**
   - `uv run pap servir` levanta todo en local;
   - la imagen Docker baja la biblioteca, comprueba su huella y responde `/salud`;
   - sin despliegue público (P-05; slice 4).
8. **Revisión** independiente en celular «apto», documentación al día y etiqueta `slice-3-cerrado`.

## Decisiones que lo gobiernan

Leer antes: P-02, P-03, P-05, P-07, F-05, R-04, R-05, R-06, `docs/especificaciones/stack.md` y la fila del slice 3 en `../plan_slices.md`. Todo lo del slice se deriva de ellas; **no hay decisiones nuevas**:

| Tema | Se deriva de | Qué rige |
|---|---|---|
| Dónde corre | P-05 (nada público antes de la prueba con usuarios), `plan_slices.md` (despliegue en el slice 4) y `stack.md` (imagen Docker desde `uv.lock`) | Local y red de la casa; imagen lista; sin servidor público |
| Tecnología | F-05 y `stack.md` («FastAPI + DuckDB en solo lectura») | FastAPI con `uvicorn`; `python-multipart` y `jinja2`, que FastAPI necesita para formularios y plantillas. Las herramientas de prueba (`playwright` y axe-core) no cambian nada visible (tipo A) |
| Tiempo | `plan_slices.md` y `stack.md` («respuesta en < 2 s») | Sin LLM: p95 < 2 s. Con texto libre, el LLM domina (P-07): se mide y su objetivo es un parámetro de experiencia (tipo B, `supuesto: S3-08`) |
| Formulario guiado | Definición de hecho del slice 2, punto 3 («toda falla del LLM… ofrece la vía estructurada») y P-07 (tope de gasto) | En la web, la vía estructurada es el formulario |
| Límites de uso | P-07 (el tope real de gasto está en la consola del proveedor) y `agents.md` §5 (umbrales de experiencia = tipo B) | El agente fija límite por IP y tope diario como `supuesto:` en `curados/web/parametros.yaml` |
| Enlaces a las fuentes | Fila del slice 3 en `plan_slices.md` («enlaces a las fuentes oficiales») y P-02 (solo documentos oficiales) | Cada cita lleva `url` del documento oficial (S3-01); si no hay, va vacía |
| Nombres de personas en la pregunta | P-03 («riesgo aceptado mientras no haya servidor») y P-05 | La red de la casa no es un servidor para terceros: el riesgo sigue aceptado y se revisa con el despliegue del slice 4 (ver nota) |
| Intervalo, conteo y gasto del mismo año | X-04 (E-04), X-02 (S-01) y X-03 (R-03), ya decididas | Se aplican en S3-01 |

**Solo dos cosas esperan al dueño, y ninguna es nueva:**
- **X-01** (pendiente desde R-06): aprobar el texto «¿Qué puedo hacer?». Mientras no se apruebe, se muestra con «pendiente de revisión».
- **Los textos de dos reglas (H17 y H18, S3-02):** `agents.md` §7 solo permite cambiar reglas si una decisión lo pide. Sin aprobación, no se hacen.

**Nota sobre P-03:** su fila se corrigió el 4/11/2026 a «se revisa con el despliegue del slice 4», en coherencia con P-05.

## Fuera del slice

- Despliegue público, dominio y HTTPS (slice 4).
- Cuentas, historial, mapas, gráficos, descargas y otros idiomas.
- La «ficha técnica» como bloque de la web: el contrato la reserva para auditoría (`contrato_respuesta.md`).
- Cambios del motor, de las cifras o de las reglas, salvo los de S3-01 y S3-02 aprobados por el dueño.
- Cambiar el backlog o el código del slice 2: la web usa sus interfaces tal como quedaron. Lo que haga falta adaptar se dice en S3-00 y S3-03.

## Cómo se trabaja

Según `agents.md`. Consultas y supuestos: `consultas_al_dueno.md` (se crea en S3-00). Evidencia: `evidencia/`.

**Una sola web, sin servidor público:** la red de la casa (`pap servir --red-local`) es solo para que el dueño pruebe en su celular (P-05).

**Regla propia del slice:** la web no tiene lógica de respuesta. Si una página necesita un texto o un número que no está en `respuesta.json` ni en un YAML de textos, es un vacío tipo C, no un arreglo en la plantilla.
