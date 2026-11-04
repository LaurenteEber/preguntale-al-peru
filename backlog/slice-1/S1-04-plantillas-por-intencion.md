# S1-04 — Plantillas por intención

## Por qué

Hoy hay una función por pregunta (`plantillas._q1…_q4`, ~300 líneas con «Huancavelica» o «San Juan de Lurigancho» dentro). Para responder cualquier territorio y año, la redacción debe salir de plantillas por intención, con los textos en archivos que el dueño pueda revisar sin leer Python.

## Contexto

- Contrato de respuesta por capas (R-04): `docs/especificaciones/contrato_respuesta.md`. Reglas de redacción 1 a 9: respuesta corta literal, una cifra clave, «Ojo al leer» de 1 a 3 viñetas en imperativo, confianza sin colores y con motivo (R-05), sin jerga en la capa 1, orden neutro, números solo por marcadores (`{{c:…}}`, `{{v:…}}`, `{{u:…}}`, `{{p:…}}`, `{{e:…}}`).
- `pap/motor/capas.py` arma las capas a partir del borrador; no cambia, salvo lo que exige el parámetro `intervalo_visible` (tarea 4).
- La salida de cada plantilla (`_armar`): `corta`, `clave`, `ojo`, `contexto`, `cifras_usadas`, `verbos`, `universos`, `protegidos`, `entidades`, `glosario`, `tema`, `nc`, `nivel_respuesta`, `territorio_nombre`, `territorio_ficha`, `motivo_confianza`, `alcance`, `respuesta_parcial`, `cruces` y `explicaciones` (estos tres últimos los usan `Motor._validar` y `ficha.py`).

## Tareas

1. Plantillas genéricas en `pap/motor/plantillas.py` (o un paquete `plantillas/`): `nivel_actual`, `evolucion`, `comparacion`, `identificar_extremo` y `cruce_efecto` (Q3 usa la estructura de efecto en 5 partes). Reciben el plan de S1-03 y devuelven el mismo borrador de hoy.
2. Textos fijos en `curados/motor/textos/plantillas/<intencion>.yaml`, con variables de lugar, universo y año (`{territorio}`, `{universo}`, `{anio_a}`…). El nombre del lugar sale de `nombre_mostrado` (T-02) con su provincia y departamento cuando es distrito.
3. Las piezas específicas de un tema (las dos formas de medir la anemia, la altitud del SIEN, el aviso de cobertura, el sesgo de sede del gasto en Lima, el Mapa sin cifra puntual, el `motivo_confianza` y el `alcance` de Q3) pasan a bloques reutilizables en `curados/motor/textos/bloques.yaml`, activados por el plan, no por el nombre de la pregunta. El umbral de tamizaje se lee de R-REG-07 (`sien_umbral_tamizaje_pct`), no de una constante.
4. Leer de `curados/motor/parametros_motor.yaml`: `pendientes_dueno.mostrar_conteo_sien` (X-02), `cr01_mismo_anio` (X-03) e `intervalo_visible` (X-04), y los límites de `respuesta`. Ninguno se fija en el código. `intervalo_visible`: `ambos` = el comportamiento actual (capa 1 con el intervalo propio; cita con el del INEI si existe; ficha con los dos); `uno` = capa 1 y cita con el del INEI si existe, si no el propio (cambio permitido en `capas.py`). El nombre largo de un distrito («X (provincia, departamento)») va una sola vez en la capa 1: Q2 y Q4 ya están en 124 de 125 palabras. Corregir de paso el docstring de `capas.py`, que dice «objetivo ≤ 90 palabras» (rige R-04: 100, máximo 125).
5. Retirar `_q1…_q4` cuando la fase 2 de la regresión (S1-07) pase con las plantillas genéricas. Al retirarlas, `plantillas.generar` traduce los nombres antiguos (`q1_evolucion`, `q2_tamizados`, `q3_gasto_anemia`, `q4_pobreza_distrital`) a la plantilla genérica de su intención, para que los `q*.yaml` sigan funcionando hasta S1-10.

## Criterios de aceptación

- [ ] `grep` de nombres de lugares, años fijos o IDs de cifra concretos en `plantillas` da 0 resultados (salvo pruebas).
- [ ] Toda cadena que producen las plantillas está en `curados/motor/textos/` y la matriz de S1-08 no tiene infracciones del corrector (`respuesta.infracciones_corrector`). Quedan fuera los textos de `capas.py`, `ficha.py` y los mensajes y frases estándar de `reglas.json`, que tienen su propio dueño.
- [ ] Capa 1 dentro de `respuesta.capa1_palabras_max` en todas las respuestas de la matriz.
- [ ] Ninguna cifra entra al texto si no es por marcador; ninguna plantilla decide una regla (las decide el validador).
- [ ] Regresión Q1–Q4 sin cambios de cifras, semáforos ni confianza.

## Fuera

Mejorar la redacción más allá de lo necesario para generalizar: los cambios de texto en Q1–Q4 se justifican uno por uno en `evidencia/regresion/`.
