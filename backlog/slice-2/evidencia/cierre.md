# Cierre del slice 2 — Intérprete de preguntas

5/11/2026. Rama `claude/determined-einstein-lwwemc` → `main`.

## Qué puede hacer ahora el usuario

Escribir la pregunta con sus palabras:

```
uv run pap preguntar --texto "¿Cuánta anemia hay en Puno?"
```

- Primero ve «Entendimos: …», cómo se leyó su pregunta; después, la misma respuesta por capas del motor del slice 1.
- Si falta el lugar, el año es relativo o no existe, la pregunta se lee de dos formas o el lugar tiene homónimos, recibe opciones y responde con `--elegir N`.
- Si pregunta algo que no tenemos, otra tarea u otro idioma, recibe un «no se puede» o un mensaje fijo que ofrece las opciones estructuradas. Nunca una respuesta adivinada.

El LLM, Claude Sonnet 5.5 con esfuerzo bajo, no ve cifras ni redacta: solo propone la consulta, con un ancla literal de la pregunta para cada valor, y el código valida todo.

## Definición de hecho, punto por punto

| Punto | Cumplido | Evidencia |
|---|---|---|
| 1. Q1–Q4 escritas como en su `pregunta_original` dan su consulta (Q1, la aclaración de Huancavelica) y con `--elegir` cumplen la regresión | sí | `tests/interprete/test_cli_texto.py::test_q1_q4_por_texto_con_grabaciones` en [`pytest_cierre.txt`](pytest_cierre.txt) |
| 2. Conjunto de ≥ 100 preguntas (140) con los umbrales de `interprete.evaluacion` en vivo con el modelo elegido; valores sin ancla y números fuera de marcadores, 0 | sí | [`s2-09_evaluacion.md`](s2-09_evaluacion.md) (3 rondas) y [`s2-10_evaluacion_final.md`](s2-10_evaluacion_final.md) |
| 3. Toda falla del LLM termina en un mensaje fijo con la vía estructurada (caída, tiempo agotado, tope, sin clave, salida inválida dos veces) | sí | `tests/interprete/test_llm.py`, `test_interpretar.py`, `test_robustez.py` |
| 4. `uv run pytest -q` en verde sin red y sin clave | sí, salvo los fallos que ya estaban en la base | [`pytest_cierre.txt`](pytest_cierre.txt) (la variable de la clave quitada y la red hacia el proveedor cortada) |
| 5. Lo que se guarda de la pregunta es lo que dice P-03 | sí | `tests/interprete/test_robustez.py`, `test_llm.py` (celular y DNI con separadores, E-06) y `tests/test_sin_secretos.py` |
| 6. Revisión independiente «apto», documentación al día y etiqueta `slice-2-cerrado` | «apto con observaciones», sin altos abiertos del intérprete; la etiqueta, al fusionar | [usuario](revision_usuario_s2.md), [adversario](revision_adversaria_s2.md), [adversario con el prompt final](revision_adversaria_s2_r2.md) |

## Costo medido

| Corrida | Llamadas | Costo |
|---|---|---|
| Grabación de Q2 (S2-04) | 1 | US$ 0,018 |
| Revisiones de S2-07 (usuario y adversario, por la CLI) | ~60 | incluido en el total |
| Evaluación, ronda 1 (prompt v3) | 141 | US$ 0,31 |
| Evaluación, ronda 2 (v4) | 143 | US$ 0,33 |
| Evaluación, ronda 3 (v5) | 143 | US$ 0,33 |
| Pruebas y revisiones con v5 (`--completar`) | 43 | US$ 0,09 |
| Revisión adversaria repetida (S2-09) | ~23 | incluido en el total |
| Evaluación final (S2-10) | 0 (todo grabado con la versión final) | US$ 0 |
| **Total del slice** (`salidas/interprete/uso.jsonl`) | **693** | **US$ 1,68** |

Las peticiones que el proveedor rechazó con un 400 al probar la salida estructurada no se cobran y no están en el registro.

- **Por pregunta:** US$ 0,0024 de media, con las instrucciones (unos 8 400 tokens) en el caché del proveedor. Sin caché, la primera pregunta cuesta unos US$ 0,018.
- **Proyección para 1 000 preguntas al mes:** entre US$ 2,4, con el caché caliente porque las preguntas llegan seguidas, y unos US$ 18 si cada pregunta llega sola y el caché de 5 minutos ya venció. Sin contar reintentos, que en la evaluación fueron menos del 3 %.
- **Latencia del LLM:** p95 de 2,7 s. Supera los 2 s del objetivo de respuesta del slice 3, que en el plan es sin LLM; S3-08 fija su propio objetivo con texto libre.

## Qué quedó fuera

- Los dos altos que encontraron las revisiones en el **motor del slice 1** (consulta E-09): la cifra de gasto que se lee como «gasto en anemia» y el mensaje de anemia de 2019. El slice 2 no puede cambiar el motor ni las plantillas.
- La salida estructurada del proveedor: no acepta el esquema de la interpretación (E-03, S2-04-d). El código valida igual.
- Los nombres de personas en la pregunta no se detectan (P-03, E-07): se revisa con el despliegue del slice 4.

## Supuestos que el dueño debe revisar

En `consultas_al_dueno.md` → «Supuestos aplicados». Los nuevos de este cierre:
- **S2-04-b:** sin `temperature`.
- **S2-04-c:** pytest sin clave ni red.
- **S2-04-d:** sin salida estructurada y con el caché del proveedor.
- **S2-07-a:** frases de año relativo.
- **S2-09-a:** `efecto` y `cruce` con anemia o gasto cuentan como iguales en la evaluación. Los umbrales de `interprete.evaluacion` también son supuesto de S2-09.

## Consultas abiertas

- **E-04:** preguntas reales del dueño para el conjunto. No bloquea.
- **E-07:** riesgos de privacidad para el slice 3.
- **E-09:** lo que las revisiones encontraron en el motor y las propuestas de avisos del intérprete.

Cerradas en este slice: E-01, E-02, E-05, E-06 y E-08. La E-03 queda registrada.

## Qué se aprendió para el slice 3

1. **Lo que manda el prompt tiene que coincidir con lo que espera el código.** El prompt pedía omitir los años relativos y el código solo aclaraba los años que el LLM ponía; al reintentar, el LLM quitaba el año inválido. En los dos casos se respondía el último año en silencio. La defensa quedó en el código, en forma determinista. En la web, todo lo que el intérprete descarte tiene que verse.
2. **La medición también se revisa.** Dos «fallas» eran del comparador (anemia y gasto en `efecto` dan la misma respuesta) y una de la métrica (el «10» de un texto fijo). Comparar con la vía estructurada evita falsos rojos.
3. **El caché del proveedor baja el costo unas 8 veces.** Conviene mantener las instrucciones idénticas entre preguntas y no ponerles nada variable.
4. **La latencia del LLM (p95 2,7 s) domina con texto libre.** El «Buscando…» de la web y el formulario guiado, que no usa LLM, son necesarios.
5. **Cada cambio del prompt invalida todas las grabaciones.** `evaluar.py --evaluar`, `--completar` y `--huerfanas --borrar` dejan regrabar por unos US$ 0,4.
