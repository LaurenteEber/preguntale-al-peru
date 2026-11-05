# S2-09 — Evaluación en vivo y elección del modelo

5/11/2026. Modelo **`claude-sonnet-5-5` con esfuerzo `low`** (decisión del dueño del 5/11/2026, P-07; antes Opus). Corredor: `uv run python tests/interprete/evaluar.py --evaluar --reporte <md>`, por `interpretar()`, con el cliente en modo «completar». Comparación según S2-02 §4; umbrales en `interprete.evaluacion` (`supuesto: S2-09`, los confirma el dueño).

## Rondas

| Ronda | Prompt | Consulta exacta | Aclaración esperada | Aclaración innecesaria | Fuera de alcance | Inyección | Sin ancla | Números | Costo |
|---|---|---|---|---|---|---|---|---|---|
| 1 ([reporte](s2-09_evaluacion_r1.md)) | v3 | 89 % | 83 % | 4 % | 100 % | 50 % | 0 | 1 | US$ 0,31 |
| 2 ([reporte](s2-09_evaluacion_r2.md)) | v4 | 98 % | 83 % | 0 % | 100 % | 88 % | 0 | 0 | US$ 0,33 |
| **3** ([reporte](s2-09_evaluacion_r3.md)) | **v5** | **98 %** | **100 %** | **1 %** | **100 %** | **100 %** | **0** | **0** | US$ 0,33 |

Cada cambio del prompt, por categoría y sin copiar preguntas del conjunto, está en [`cambios_prompt.md`](cambios_prompt.md) (versiones 4 y 5). Entre la ronda 1 y la 2 cambiaron también dos cosas de la medición: `efecto` y `cruce` con tema `anemia` o `gasto_publico` cuentan como la misma consulta, porque el motor da la misma respuesta (supuesto S2-09-a, prueba `test_efecto_con_anemia_o_gasto_es_la_misma_consulta`); y la comparación diferencial de E-08 se aplica también a las aclaraciones del resolver (el número de l10 era el «más de 10 lugares» fijo del resolver).

## Ronda final (v5)

- 139 preguntas: el conjunto de S2-02 (137) más las dos de S2-07 (`s07a`, `s07b`). **Cumple todos los umbrales**, con las dos métricas absolutas en 0.
- **Costo:** US$ 0,0024 de media por pregunta (con el caché del proveedor en las instrucciones) y latencia p95 del LLM de 2,7 s.
- **Fallas que quedan (3):** d12 (el LLM no puso el tema en una comparación), d18 (una aclaración de más) y e04 (efecto en vez de evolución ante una premisa). Ninguna da una cifra equivocada: terminan en una aclaración o en una respuesta del motor a lo que se interpretó, con su «Entendimos».

## Grabaciones

- Con el prompt v5 se volvió a grabar todo por `interpretar()`, también los reintentos (E-05): el conjunto (ronda 3), las pruebas de S2-08 y las 35 preguntas de S2-07 (`evaluar.py --completar`: US$ 0,09 en 43 llamadas).
- Se borraron **285 grabaciones huérfanas** de las versiones 2 a 4 del prompt (`evaluar.py --huerfanas --borrar`). Solo una estaba en git: la de Q2 con la versión 2 (`373fc9b43924ef7cb7126394.json`); las demás eran de las rondas 1 y 2 y de S2-07 y nunca se subieron. La lista con nombres no se guardó antes de borrar; se reconstruye corriendo las rondas 1 y 2 con sus versiones.

## Gasto total en vivo del slice

Según `salidas/interprete/uso.jsonl` (fuera de git), hasta el cierre de S2-09 y con la revisión adversaria repetida incluida: ver la tabla de costos de `cierre.md` (S2-10), que suma cada corrida.
