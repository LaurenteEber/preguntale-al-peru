# Slice 2 — Intérprete de preguntas

Rama `slice-2` desde `main`, **después de la etiqueta `slice-1-adenda-cerrada`**. Fase 5b. Plan general: `../plan_slices.md`.

4/11/2026. Revisado por un subagente que emuló al implementador (31 hallazgos corregidos) y por el supervisor.

## Objetivo

Que la persona escriba su pregunta con sus palabras («¿Cuánta anemia hay en Puno?») y reciba la respuesta por capas del motor del slice 1.

Un LLM traduce la frase a una **interpretación**: una consulta, una aclaración o un «fuera de alcance». Cada valor de la consulta va con su **ancla**, el fragmento literal de la pregunta que lo justifica. El LLM:
- no ve cifras ni datos de la biblioteca;
- no redacta la respuesta;
- no elige el lugar exacto: copia lo que escribió la persona, y el resolver determinista decide o pregunta. Por ejemplo, «Huancavelica» sigue dando la aclaración departamento / provincia / distrito (T-03, R-TERRITORIO-09).

```
pregunta en texto libre
  → limpieza determinista (longitud, control, datos personales)             S2-04
  → LLM: interpretación con esquema propio y anclas literales                 S2-01, S2-03, S2-04
  → validación determinista: esquema + anclas + vocabulario                   S2-05
      ├─ no valida → 1 reintento con el error → si no, mensaje fijo con las opciones estructuradas
      ├─ falta lugar, intención o año → default o aclaración armada por el código (no por el LLM)
      ├─ aclaración del LLM → opciones (consultas completas) con su «Entendimos…»
      ├─ fuera de alcance / no es pregunta / otro idioma → «no se puede» o mensaje fijo
      └─ consulta → preguntar_minima(consulta + pregunta_original) del slice 1, SIN CAMBIOS
  → «Entendimos tu pregunta así: …» (texto fijo armado desde la consulta resuelta)    S2-05, S2-06
```

## Qué significa «la misma respuesta»

Hay tres comparaciones y cada una tiene su criterio:

| Comparación | Criterio | Dónde |
|---|---|---|
| Texto libre frente a la referencia Q1–Q4 | Los de `tests/test_regresion_q1_q4.py`: cifras por clave, semáforos, confianza y reglas firmes. No se comparan bytes | S2-06 |
| Texto libre frente a la vía estructurada | `respuesta.json` igual a `preguntar_minima(consulta producida, con la misma pregunta_original)`, excluyendo `interpretacion`, `entendimos` y las rutas o nombres de archivo | S2-05 |
| Vía estructurada antes y después del slice | `respuesta.json` igual a la base guardada en S2-00, excluyendo las mismas rutas | S2-06 |

**Ojo:** `pregunta_original` cambia lo que se aplica. R-CRUCES-07 busca «disparadores de efecto» en ese texto (`reglas_etapa8_10.py`). Por eso, en la segunda comparación la vía estructurada recibe la misma `pregunta_original`.

## Lo que cambió con la adenda (S2-00, 4/11/2026)

Según `../slice-1/evidencia/cierre.md` §Adenda: el gasto entre años sale en soles de 2025 (cubo `68f2a609…`, versión 1.2.0); toda evolución muestra los dos años; la evolución de anemia hasta 2018 o 2024 responde con la forma anterior; «Lima» ofrece Lima Metropolitana, Lima Región y Callao; un año de anemia que solo existe con la forma anterior ofrece la evolución. Nada de esto cambia el contrato de la consulta mínima. La rama `slice-2` nace de la punta de `slice-1-adenda` (sin fusionar en `main`: E-01 en `consultas_al_dueno.md`).

## Antes de empezar

1. La adenda está cerrada (etiqueta `slice-1-adenda-cerrada`); S2-00 lee su `cierre.md` §Adenda y anota en este README lo que cambie.
2. Las decisiones del dueño ya están en `docs/decisiones.md` (F-05, P-03 y P-07; tabla de abajo). La clave de la API debe estar en el entorno antes de S2-04.

## Historias (en orden)

| ID | Historia | LLM real | Estado |
|---|---|---|---|
| S2-00 | [Preparación](S2-00-preparacion.md) | no | hecha ([base](evidencia/s2-00_base.txt)) |
| S2-01 | [Contrato de la interpretación](S2-01-contrato-interpretacion.md) | no | hecha (`tests/interprete/test_contrato.py`) |
| S2-02 | [Conjunto de evaluación (independiente)](S2-02-conjunto-evaluacion.md) | no | hecha, pendiente de revisión (137 entradas; dudas en E-04) |
| S2-03 | [Vocabulario e instrucciones desde datos curados](S2-03-vocabulario-prompt.md) | no | hecha ([cambios del prompt](evidencia/cambios_prompt.md)) |
| S2-04 | [Limpieza, cliente del LLM, grabaciones y presupuesto](S2-04-cliente-llm.md) | sí, para grabar | bloqueada en parte: código y pruebas sin red hechos; falta la grabación en vivo de Q2 (E-02) |
| S2-05 | [Interpretar: validar, anclar, aclarar y «Entendimos»](S2-05-interpretar.md) | no (grabaciones) | pendiente |
| S2-06 | [CLI `--texto`](S2-06-cli.md) | no | pendiente |
| S2-07 | [Revisión independiente temprana](S2-07-revision-independiente.md) | sí | pendiente |
| S2-08 | [Pruebas de robustez y privacidad](S2-08-robustez-privacidad.md) | sí, para grabar | pendiente |
| S2-09 | [Evaluación en vivo y elección del modelo](S2-09-evaluacion-en-vivo.md) | sí | pendiente |
| S2-10 | [Documentación y cierre](S2-10-documentacion-cierre.md) | sí, una corrida | pendiente |

Desde S2-05, en cada historia se corren:
- `uv run pytest -q`;
- la regresión Q1–Q4;
- la matriz reducida;
- la evaluación con grabaciones (`tests/interprete/`).

El modelo es Opus desde S2-04 (`interprete.modelo`, `decision: P-07`). Si en S2-09 cambia la versión del modelo o el prompt, se vuelve a grabar todo.

## Definición de hecho del slice

1. **Q1–Q4 escritas como en su `pregunta_original`:**
   - dan su consulta o la aclaración que corresponde al lugar (Q1, «Huancavelica»: departamento, provincia o distrito);
   - con `--elegir` en la opción de la referencia, cumplen los criterios de `test_regresion_q1_q4.py`.
2. **Conjunto de evaluación** de ≥ 100 preguntas (S2-02), con los umbrales de `interprete.evaluacion` cumplidos en vivo con el modelo elegido (S2-09). Además, dos métricas deben quedar siempre en **0**:
   - **valores sin ancla aceptados;**
   - **números de las capas 1 a 3 y de `entendimos` que no salgan de un marcador del cubo,** sin contar los años ni el eco literal de `pregunta_original` en el encabezado y en las aclaraciones.
3. **Toda falla del LLM termina en un mensaje fijo que ofrece la vía estructurada,** nunca en una respuesta adivinada. Fallas cubiertas: caída, tiempo agotado, tope de costo, sin clave y salida inválida dos veces.
4. **`uv run pytest -q` en verde sin red y sin clave.**
5. **Lo que se guarda de la pregunta es lo que dice P-03.** Los números con forma de dato personal se quitan antes de enviar y de guardar (P-03).
6. **Revisión independiente «apto»** (S2-07, repetida en S2-10 si cambió el modelo). Documentación al día y etiqueta `slice-2-cerrado`.

## Decisiones del dueño

Leer antes: P-01, P-02, **P-03**, P-05, **P-07**, R-04, T-03, E-06 y **F-05**, en `docs/decisiones.md`.

Decididas el 4/11/2026 (eran las propuestas X-11 a X-14 de este backlog):

| Tema | Fila | Qué rige |
|---|---|---|
| Entorno en la nube | F-05 | Los Parquet se bajan del release de GitHub (`scripts/bajar_biblioteca.sh`); `pap construir` y las pruebas `solo_mac`, solo en el Mac |
| Proveedor, modelo y gasto del LLM | P-07 | Anthropic, modelo Opus; las llamadas se pagan con una clave de API; el tope mensual está en la consola del proveedor y la evaluación lleva tope por corrida |
| Qué se guarda de las preguntas | P-03 | Pregunta limpia solo en `respuesta.json` (en `salidas/`, fuera de git); registro de uso sin texto; caché de 24 h; preguntas reales nunca en git ni en grabaciones; los nombres propios se revisan en el slice 3 |

**Lo que necesita el entorno desde S2-04:** la clave de la API como variable secreta del entorno en la nube (su nombre va en `interprete.variable_clave`) y salida de red a la API del proveedor. Si faltan, S2-04 a S2-10 quedan bloqueadas en lo que necesita LLM real (grabar y evaluar) y se sigue con lo demás.

**Defaults que fija el backlog.** Son vacíos B; el dueño los cambia editando una línea de `parametros_motor.yaml` → `interprete`, que se crea en S2-01.

| Parámetro | Default | Alternativa |
|---|---|---|
| `sin_lugar` | `aclarar`, con opciones armadas por el código: «Todo el Perú» o «Escribe el lugar» | `nacional` |
| `sin_intencion` («anemia en Puno») | `nivel_actual` | `aclarar` |
| `anios_relativos` («el año pasado») | `aclarar`: «el último año con datos» o «Escribe el año» | — |
| `reintentos_si_no_valida` | 1 | 0 |
| `cache_horas` | 24 | — |
| `aclaracion_max_opciones` | 4 | — |

## Fuera del slice

- API, web, cuentas y conversación de varios turnos (más allá de `--elegir`).
- Temas o datos nuevos.
- Cambios del motor, las plantillas de respuesta, el resolver o las reglas.

Si una pregunta real pide algo que el motor no hace, va al conjunto de evaluación como «fuera de alcance» y a `consultas_al_dueno.md` como dato para la Ola 1.

## Reglas propias de este slice

- **Ninguna prueba de pytest llama al LLM.** Si falta una grabación, la prueba falla y dice cómo grabarla, sin saltarse. En pytest la caché va a una carpeta temporal, para que no tape una grabación que falta.
- **El conjunto de evaluación no se usa para ajustar las instrucciones.** Los ejemplos del prompt están en `curados/interprete/ejemplos.yaml`, y una prueba comprueba que no se cruzan con el conjunto. Cada cambio del prompt queda en `evidencia/cambios_prompt.md`, con la categoría que lo motivó.
- **Una puerta humana no detiene el slice.** Si una historia espera una revisión del supervisor o del dueño, queda «hecha, pendiente de revisión» y se sigue.

Según `agents.md`. Consultas y supuestos: `consultas_al_dueno.md` (se crea en S2-00). Evidencia: `evidencia/`.
