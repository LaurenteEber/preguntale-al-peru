# Slice 1 — Motor por intenciones

Rama: `slice-1`. Fase 5a. Plan general: `../plan_slices.md`.

## Objetivo

Que cualquier pregunta **estructurada** sobre los 9 indicadores del piloto (anemia con sus dos criterios, desnutrición crónica, anemia y cobertura del SIEN, gasto en servicios ex-PAN, pobreza monetaria y Mapa de Pobreza) salga por capas y validada, para cualquier territorio y año con datos, sin escribir una consulta ni una plantilla a mano.

Hoy: `tests/fixtures/consultas_piloto/q1–q4.yaml` listan cada cifra a mano y `pap/motor/plantillas.py` tiene una función por pregunta (`_q1…_q4`) con nombres de lugares dentro del código.

Al terminar:

```
consulta mínima (JSON, con esquema)        ← la producirá el LLM en el slice 2
  → resolver territorio (determinista)      → o una aclaración («¿Lima Metropolitana, Lima Región o el Callao?»)
  → planificador de cifras (intenciones.yaml + decisiones)
  → Motor.responder (sin cambios de fondo: cifras, validador de 68 reglas, ficha)
  → plantilla por intención (textos fijos en YAML; números solo por marcadores)
  → respuesta por capas (contrato_respuesta.md)
```

**Adenda (actualizada el 4/11/2026):** las historias S1-11 a S1-16 que concluyen la implementación están en [adenda/](adenda/README.md).

## Historias (en orden)

| ID | Historia | Estado |
|---|---|---|
| S1-00 | [Preparación: reconstruir con los nombres de T-02 y dejar la base lista](S1-00-preparacion.md) | hecha ([evidencia](evidencia/s1-00_comparacion_cubo.txt), [territorio](evidencia/s1-00_datos_territorio.txt), [pytest](evidencia/s1-00_pytest_post.txt)) |
| S1-01 | [Contrato de la consulta mínima](S1-01-consulta-minima.md) | hecha (`tests/test_consulta_minima.py`) |
| S1-02 | [Resolver territorial determinista](S1-02-resolver-territorio.md) | hecha (`tests/test_resolver_territorio.py`, 133 casos) |
| S1-03 | [Catálogo de intenciones y planificador de cifras](S1-03-planificador.md) | hecha (`test_planificador.py`; fase 1 de S1-07 en `test_regresion_q1_q4.py::test_planes`, sin 2022 en Q1 por C-01) |
| S1-04 | [Plantillas por intención](S1-04-plantillas-por-intencion.md) | hecha (fase 2 de S1-07 en `test_regresion_q1_q4.py::test_respuestas`; diferencias aprobadas en [evidencia/regresion](evidencia/regresion/)) |
| S1-05 | [Respuestas de «no se puede» y aclaraciones](S1-05-no-se-puede.md) | hecha (`test_no_se_puede.py`, un caso por motivo) |
| S1-06 | [CLI `pap preguntar` con consulta mínima](S1-06-cli.md) | hecha (`test_cli_preguntar.py`) |
| S1-07 | [Regresión Q1–Q4](S1-07-regresion-q1-q4.md) | hecha (fases 1 y 2 en `test_regresion_q1_q4.py`; diferencias aprobadas en [evidencia/regresion](evidencia/regresion/); en verde al cerrar cada historia) |
| S1-08 | [Matriz de cobertura automática](S1-08-matriz-cobertura.md) | hecha ([matriz.md](evidencia/matriz.md): 5 086 casos, 0 errores, 0 fallos; reducida en `test_matriz_cobertura.py`) |
| S1-09 | [Revisión independiente (usuario y estadística)](S1-09-revision-independiente.md) | hecha (auditoría y revisión de usuario «apto con observaciones» en su segunda revisión; [verificación](evidencia/verificacion_correcciones.md); [correcciones](evidencia/correcciones_s1-09.md)) |
| S1-10 | [Documentación y cierre](S1-10-documentacion-cierre.md) | hecha ([cierre.md](evidencia/cierre.md)) |

S1-07 se arma en dos fases: comparación de planes justo después de S1-03 y comparación de respuestas completas desde S1-04. Después se corre en cada historia siguiente.

**Bloqueos conocidos al empezar:** ninguno (C-01 y C-02 cerradas el 3/11/2026).

## Definición de hecho del slice

1. Q1–Q4 salen por el motor por intenciones con las **mismas cifras, semáforos de respuesta y niveles de confianza** que la referencia tomada al cerrar S1-00 (S1-07), con los parámetros de `pendientes_dueno` en su valor de hoy. Los cambios de texto están aprobados en `evidencia/regresion/`. Única excepción, decidida por el dueño (C-01): Q1 deja de mostrar el pico de 2022.
2. La matriz de cobertura (S1-08) no tiene caídas, marcadores sin rellenar, códigos internos ni capas 1 por encima del máximo de palabras (`parametros_motor.yaml`, R-04); toda combinación sin datos da una respuesta de «no se puede» con su motivo.
3. Las aclaraciones de territorio cumplen T-03 (Lima) y R-TERRITORIO-09 (homónimos).
4. `uv run pytest -q` pasa entero; el cubo no cambia de huella en este slice (solo cambia en S1-00).
5. Revisión independiente de usuario y estadística «apto» (o «apto con observaciones» ya corregidas) (S1-09).
6. Documentación al día y etiqueta `slice-1-cerrado` (S1-10; es de la carpeta de trabajo anterior y no existe en este repositorio, `docs/historia.md`).

## Decisiones que lo gobiernan

Leer antes de empezar (`docs/decisiones.md`): P-01, P-02, P-04, T-02, T-03, E-03 a E-08, S-01, G-05 a G-07, R-01 a R-07.

**Pendientes del dueño que tocan este slice.** Se implementan detrás de un parámetro de `curados/motor/parametros_motor.yaml` (bloque `pendientes_dueno`), para que cambiarlos sea editar una línea. Mientras el dueño no decida, rige **el comportamiento de hoy**, para que la regresión compare lo mismo; la recomendación queda anotada en el YAML:

| Pendiente | Historia | Por defecto |
|---|---|---|
| X-02: conteo en «¿cuántos?» del SIEN (52 de 547) | S1-04 | no se muestra (como hoy); recomendación: tarjeta en la capa 2 |
| X-03: CR-01 con el gasto del mismo año que la anemia comparada | S1-03 | no (como hoy, solo el último año); recomendación: sí |
| X-04: un solo intervalo visible | S1-04 | `ambos` (como hoy); recomendación: `uno` |

## Fuera del slice

LLM, API, web, datos o indicadores nuevos, cambios a las reglas de `reglas/` (si una regla estorba, va a `consultas_al_dueno.md`).

## Cómo se trabaja

Según `agents.md`. Valores por defecto: `curados/motor/parametros_motor.yaml`. Dudas y supuestos: `consultas_al_dueno.md`. Evidencia: `evidencia/`.
