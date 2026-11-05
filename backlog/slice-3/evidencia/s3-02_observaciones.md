# S3-02 — Evidencia

Historia: [S3-02](../S3-02-observaciones-y-base.md). Pruebas: `tests/test_s3_02_observaciones.py` (3 pruebas, vistas fallar antes del cambio).

## Observaciones

| ID | Resultado | Qué cambió | Dónde |
|---|---|---|---|
| H14 | **hecha** (agente, §5.1) | La corta de «¿cuánto hay?» pasa de «Esto es lo que dicen los datos oficiales sobre {sujeto} en {lugar}:» a «En {anio}, en {lugar}, {sujeto} fue:» (p. ej. «En 2025, en Huancavelica, la anemia en niñas y niños de 6 a 35 meses fue:»). Q1–Q4 no la usan (Q1 es evolución; Q2–Q4 tienen bloque propio): su `.md` no cambia por H14. No se tocaron la corta de evolución sin comparación ni la de comparación: `test_s1_09_correcciones.py` depende de la primera y H14 no dice nada de la forma de comparar dos lugares | `curados/motor/textos/plantillas/nivel_actual.yaml` |
| H15 | **hecha** (agente, §5.1) | «forma de medir la anemia» (`glosario.yaml`, ya existía) se agrega al glosario de los dos indicadores de anemia de ENDES. Q1 ya lo tenía (sin cambio); Q2 y Q3 lo ganan (sus citas dicen «forma de medir vigente desde 2024»); Q4 no lo usa. En Q3 «cambio estadísticamente claro» baja un puesto | `curados/motor/textos/bloques.yaml` (`glosario` de `endes_anemia_6_35m_oms2024` y `endes_anemia_6_35m`) |
| H21 | **no hecha: consulta W-02** | Quitar los porcentajes de «Más contexto» de Q4 hace desaparecer el aviso «Estas cifras vienen de fuentes de distinto tipo…» y la regla R-LENGUAJE-06 (rotular). Quitar un aviso falla la condición 2 de §5.1 | [`../consultas_al_dueno.md`](../consultas_al_dueno.md) |
| H17, H18 | **no hechas** (caso B) | El dueño no los marcó. No se tocó `reglas/` | W-03 |

## §5.1 en las diferencias aprobadas (H15, `regresion/Q2.yaml` y `Q3.yaml`, `aprobado_por: agente`)

1. Cifras, semáforos, confianza y reglas de bloqueo: sin cambio (`test_respuestas` compara todos sus campos con la referencia; solo cambia `capa3.glosario`).
2. Sin afirmaciones nuevas: el término ya está en el texto de la respuesta («forma de medir vigente desde 2024» en las citas) y la definición es el texto fijo del glosario, el mismo que ya lleva Q1. Es lo que pide la historia.
3. Corrector sin infracciones y capa 1 dentro de `capa1_palabras_max`: la capa 1 de Q1–Q4 no cambia; la prueba de S3-02 lo comprueba para las cuatro y para las respuestas de H14.
4. Ningún «no se puede» cambia. `tests/referencias/` sin tocar.

## Base de la web

`base_api/` (`MANIFIESTO.txt` dice el commit, el estado del árbol y el conteo) la genera [`s3-02_generar_base.py`](s3-02_generar_base.py): Q1–Q4 con `preguntar_minima` (más Q1 con «Huancavelica» + `elegir=[1]`), los 60 casos de la matriz reducida con `correr_caso` (aclaraciones incluidas) y los 140 del conjunto de evaluación con `interpretar()` en modo «reproducir». Cada carpeta tiene `respuesta.json` y `entrada.json`. Correrlo dos veces seguidas no cambia ningún archivo. Se genera con el árbol de trabajo (los cambios de S3-02 aún sin commit): el parent debe volver a correrlo tras el commit si quiere que el manifiesto diga el commit final.
