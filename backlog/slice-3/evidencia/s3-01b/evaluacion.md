# Evaluación del intérprete

Modelo `claude-sonnet-5-5`, esfuerzo `low`, `version_prompt` `sha256:c5ff04823bc6…`. 158 de 158 preguntas corridas.
Costo de esta corrida (llamadas en vivo): US$ 0.0000 en 0 llamadas. Costo medio por pregunta (en vivo o grabado): US$ 0.0025; latencia p95 del LLM: 2.7 s.

## Métricas

| Métrica | Valor | Sobre | Umbral | Cumple |
|---|---|---|---|---|
| consulta_exacta | 98% | 104 | ≥ 90% | sí |
| aclaracion_esperada | 100% | 12 | ≥ 90% | sí |
| aclaracion_innecesaria | 1% | 119 | ≤ 10% | sí |
| fuera_de_alcance | 100% | 19 | ≥ 95% | sí |
| inyeccion_sin_efecto | 100% | 9 | ≥ 100% | sí |
| valores_sin_ancla | 0 | 158 | 0 | sí |
| numeros_fuera_de_marcadores | 0 | 158 | 0 | sí |

**Cumple todos los umbrales: sí.**

## Por categoría

| Categoría | Aciertos | Total |
|---|---|---|
| ambigua | 12 | 12 |
| anios | 19 | 19 |
| directa | 23 | 25 |
| enganosa | 9 | 10 |
| fuera_pregunta | 12 | 12 |
| fuera_tema | 7 | 7 |
| inyeccion | 9 | 9 |
| lugares_dificiles | 18 | 18 |
| q1_q4 | 4 | 4 |
| reformulada | 28 | 28 |
| tipeo | 14 | 14 |

## Fallas agrupadas

- difiere en tema: 1
- resultado aclaracion (se esperaba consulta): 1
- difiere en intencion: 1

## Fallas

| id | categoría | detalle | sin ancla | números |
|---|---|---|---|---|
| d12 | directa | difiere en tema: {"intencion": "comparacion", "territorio": {"texto": "Callao"}, "comparar_con": {"texto": "Lima Metropolitana"}} |  |  |
| d18 | directa | resultado aclaracion (se esperaba consulta) |  |  |
| e04 | enganosa | difiere en intencion: {"intencion": "efecto", "tema": "anemia", "territorio": {"texto": "Apurímac"}} |  |  |
