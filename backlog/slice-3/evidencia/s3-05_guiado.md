# S3-05 — Formulario guiado: evidencia

Código: `src/pap/web/guiado.py` (rutas y armado de la consulta), plantillas `guiado_paso1.html` y `guiado_paso2.html`, estilos en `estatico/estilo.css`; textos en `curados/web/textos.yaml` (`guiado`); campos por intención en `curados/web/parametros.yaml` (`guiado`); especificación en `docs/especificaciones/api.md`; pruebas en `tests/web/test_guiado.py`. `app.py` solo separa `datos_opciones()` (lo mismo que `/api/opciones`) para que el servidor lo lea sin una llamada HTTP.

## Qué ve una persona

- **Paso 1** (`/guiado`): elige tema y qué quiere saber (cada intención con su descripción). Enlazado desde el inicio.
- **Paso 2**: solo los campos de esa intención (lugar o «Todo el Perú»; segundo lugar en comparar; año, o desde y hasta en evolución; nivel en «dónde es más alto o más bajo», con «Dentro de: Todo el Perú» fijo).
- Al enviar, la misma página de respuesta, de aclaración o de aviso de S3-04. Si falta el lugar o el año no es válido, vuelve al paso 2 con su aviso, sin llamar al motor.
- Funciona sin JavaScript y sin la clave del LLM (el servicio de las pruebas se crea con `llm=None` y sin ninguna variable de entorno de claves).

## Criterios de aceptación

- [x] **Q1–Q4 por el formulario cumplen los criterios de la regresión** (`test_q1_q4_por_el_formulario_cumplen_los_criterios_de_la_regresion`: llama a `test_respuestas` de `tests/test_regresion_q1_q4.py` con la respuesta que dio el formulario). Con la salvedad del aviso de Q1 de abajo.
- [x] **Diferencias con `base_api`** listadas en [`s3-05_diferencias.md`](s3-05_diferencias.md). Solo difieren `pregunta_original` (y sus copias `pregunta`), y el `territorio.texto` de Q1; **más un hallazgo**: Q1 con «Huancavelica» a secas trae el aviso de X-22 en `capa2.avisos`.
- **Contradicción resuelta por precedencia (D):** la historia pide Q1 con «Huancavelica» y elegir 1; desde X-22 (6/11/2026) «Huancavelica» se responde como departamento sin aclaración. Q1 va **sin** elegir; el caso con aclaración es «Abancay» + elegir 1 (`test_q1_con_aclaracion_abancay_elegir_1_por_el_formulario`, igual a `base_api/q/q1_abancay_elegir_1` en capas, cifras y semáforo).
- Una prueba por intención (`test_cada_intencion_arma_su_consulta_y_el_motor_responde`, 10 casos: las seis intenciones, con y sin año, serie con y sin límites, segundo lugar nacional); «Todo el Perú» da `{nacional: true}` (`test_todo_el_peru_da_nacional_true`, y en el segundo lugar y en «dentro de»); sin clave funciona (`test_sin_la_clave_del_llm_el_formulario_funciona`); combinaciones sin fila (gasto × extremo, anemia × extremo por distrito, pobreza × extremo por provincia) dan el «no se puede» del motor (`test_combinacion_sin_fila_…`).
- Paso 2 solo con los campos de la intención (6 pruebas); errores de llenado (4 + nivel inválido + cuerpo mal formado); prueba de números ampliada a las páginas del formulario (`test_ningun_numero_nuevo_en_las_paginas_del_formulario`); texto en YAML (la prueba de S3-04 que revisa las plantillas sigue en verde).

## RED y GREEN

- RED: con las pruebas escritas y sin código, `GET /guiado` daba 404 (`test_paso1_…` falló con `404 == 200`).
- GREEN: ver comandos abajo.

## Supuestos (tipo B)

- **S3-05-a:** los rótulos de tema e intención del paso 1 son los de `/api/opciones` (`rotulos_temas`, «Anemia infantil»…), no los nombres de `no_se_puede.yaml`; esos se usan solo dentro de la pregunta armada (`{tema}`, `{tema_art}`). Así el formulario muestra lo mismo que la API.
- **S3-05-b:** qué campos pide cada intención y cómo arma el periodo (`parametros.yaml` → `guiado.intenciones`); `cruce` y `efecto` piden lo mismo que `nivel_actual`.
- **S3-05-c:** el segundo lugar de «comparar» también admite «Todo el Perú» (casilla `lugar2_nacional`).
- **S3-05-d:** el lugar admite hasta 200 caracteres (el tope del esquema); si lo excede, aviso `lugar_muy_largo`.
- **S3-05-e:** el año se escribe con cuatro cifras; el rango (1990–2100) lo valida el motor. Si la persona escribe un lugar y marca «Todo el Perú» a la vez, no se adivina: se pide dejar uno (`lugar_doble`).
- **S3-05-f:** textos del formulario (rótulos de campos, ayudas, plantillas de `pregunta_original`, avisos) escritos por el agente en `textos.yaml` → `guiado`; el dueño debe revisarlos. Las plantillas de `pregunta_original` no repiten la frase de la base («¿Cómo ha evolucionado la anemia en niñas y niños pequeños…?»).
- **S3-05-g:** orden de los niveles en «Qué quieres ordenar»: el de `/api/opciones` (distrito, provincia, departamento), sin «Todo el Perú».

## Vacíos tipo C

- Aviso de X-22 en Q1 por el formulario (ver `s3-05_diferencias.md`): por decidir con el dueño si se aprueba en `evidencia/regresion/Q1.yaml`. No se detuvo nada.

## Comandos

Ver el resultado de `uv run pytest -q tests/web tests/test_sin_secretos.py` al final de este archivo.

- `uv run pytest -q tests/web tests/test_sin_secretos.py` (≈165 s): 88 pasan y 1 falla: `tests/web/test_servicio.py::test_no_hay_get_que_lleve_la_pregunta`, cuya lista cerrada de rutas `GET` no incluye `/guiado` (la historia lo exige). Hace falta agregar `"/guiado"` en la línea 147 de ese archivo, que está fuera de las superficies de esta historia. (`test_imports_permitidos_en_pap_web` falló al principio por `from pap.web import guiado`; se resolvió con `import pap.web.guiado as guiado`.) Tras ese cambio, `test_servicio.py` + `test_guiado.py` + `test_sin_secretos.py`: 54 pasan y esa 1 falla.
- `tests/web/test_guiado.py`: 41 pasan (RED previo: 404 en `/guiado`).

## Nota del orquestador: el aviso de X-22 en Q1 por el formulario

Por el formulario, Q1 se escribe «Huancavelica» a secas. Desde X-22 esa respuesta trae en «Avisos» la frase que ofrece la provincia o el distrito. Esa frase es justo lo que decidió el dueño en X-22 (6/11/2026), así que no es una afirmación nueva ni una consulta tipo C. La regresión de Q1 sigue con «departamento de Huancavelica», que no lleva el aviso, y no cambia. La prueba del formulario comprueba que ese aviso es la única diferencia y después aplica los criterios de la regresión.

Suite completa en el Mac (6/11/2026, antes del commit): 1130 pasan, 0 fallan.
