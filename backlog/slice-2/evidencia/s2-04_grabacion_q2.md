# S2-04 — Primera grabación en vivo (Q2)

5/11/2026. `uv run python tests/interprete/evaluar.py --grabar --solo q2`, con la clave en `PAP_ANTHROPIC_API_KEY` (decisión del dueño).

| Campo | Valor |
|---|---|
| Modelo | `claude-sonnet-5-5`, esfuerzo `low` (P-07) |
| Grabación | `tests/interprete/grabaciones/373fc9b43924ef7cb7126394.json` |
| Tokens | 8 434 de entrada + 124 de salida |
| Costo | US$ 0,0181 |
| Latencia | 1,8 s |
| Interpretación | `consulta`: `nivel_actual`, `anemia`, territorio «Ayaviri (Melgar, Puno)», con sus anclas |
| `pap preguntar --texto` | `tests/interprete/test_cli_texto.py::test_q1_q4_por_texto_con_grabaciones[q2]` pasa (criterios de la regresión Q1–Q4) |

Antes de esa llamada, el proveedor rechazó con 400, sin cobro, cuatro peticiones: tres por el esquema de la salida estructurada y una de prueba del mismo error. Los límites que dio son de hasta 24 parámetros opcionales y 16 con unión de tipos; el contrato de S2-01 tiene 34. Por eso no se manda `output_config.format` (supuesto S2-04-d, E-03): el prompt ya lleva el esquema y el código valida con el de S2-01.

Después de esta grabación se activó el caché del proveedor para las instrucciones (`cache_control` en `system`), que no cambia la interpretación ni la grabación.
