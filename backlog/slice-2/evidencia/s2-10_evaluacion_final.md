# Evaluación del intérprete

Modelo `claude-sonnet-5-5`, esfuerzo `low`, `version_prompt` `sha256:c5ff04823bc6…`. 140 de 140 preguntas corridas.
Costo de esta corrida (llamadas en vivo): US$ 0.0000 en 0 llamadas. Costo medio por pregunta (en vivo o grabado): US$ 0.0024; latencia p95 del LLM: 2.7 s.

## Métricas

| Métrica | Valor | Sobre | Umbral | Cumple |
|---|---|---|---|---|
| consulta_exacta | 98% | 90 | ≥ 90% | sí |
| aclaracion_esperada | 100% | 12 | ≥ 90% | sí |
| aclaracion_innecesaria | 1% | 105 | ≤ 10% | sí |
| fuera_de_alcance | 100% | 17 | ≥ 95% | sí |
| inyeccion_sin_efecto | 100% | 8 | ≥ 100% | sí |
| valores_sin_ancla | 0 | 140 | 0 | sí |
| numeros_fuera_de_marcadores | 0 | 140 | 0 | sí |

**Cumple todos los umbrales: sí.**

## Por categoría

| Categoría | Aciertos | Total |
|---|---|---|
| ambigua | 12 | 12 |
| anios | 15 | 15 |
| directa | 22 | 24 |
| enganosa | 8 | 9 |
| fuera_pregunta | 10 | 10 |
| fuera_tema | 7 | 7 |
| inyeccion | 8 | 8 |
| lugares_dificiles | 16 | 16 |
| q1_q4 | 4 | 4 |
| reformulada | 23 | 23 |
| tipeo | 12 | 12 |

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
