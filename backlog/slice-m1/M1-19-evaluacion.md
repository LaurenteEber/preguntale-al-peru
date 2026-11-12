# M1-19 — Conjunto de evaluación y medición

**Se deriva de** el diseño §23.

## Tareas

1. **`tests/inferencia/evaluacion.yaml`,** con unas 100 preguntas. Cada una: `id`, `pregunta`, `salida_esperada`, `plan_esperado` (o su `huella_uy`), `cifra_oficial` si existe, `estrato`, `autor` y `particion`.
2. **Quién escribe qué:**
   - el agente genera las que tienen cifra oficial; se aprueban solo si su plan reproduce la cifra publicada;
   - **el dueño escribe de 40 a 60** (sin cifra oficial, ambiguas y de las que «parece que no hay»). El agente le deja una plantilla y ejemplos de cada estrato; no las escribe por él;
   - el universo de cada plan esperado lo anotan dos revisores: el dueño y el auditor-agente.
3. **Estratos** del §23.2: pares casi iguales, universo con convención, respuesta múltiple, temas nuevos, sin insumos, que parecen no tener insumos y ambiguas.
4. **Partición:** 30 % queda como prueba no vista; no se usa para ajustar prompts ni sinónimos.
5. **Medición** (`pap inferencia evaluar`): recall@20, acierto del plan, acierto de la cifra, matriz de salidas, aclaraciones útiles, «no puedo» con alternativa, error con consenso, p95 por etapa y costo por pregunta. Cada proporción con su intervalo de Wilson.
6. **Parámetros que se fijan con lo medido** (anexo B: «se mide en la fase 1»): 3 muestras frente a 2 más desempate, y el esfuerzo del planificador. El agente los fija como tipo B, con la evidencia, y lo informa al dueño. `recuperador.dos_pasos` se activa solo si mejora el recall@20 (`fichas.md` §7).
7. **Estado del índice:** el informe dice con qué estado se midió (`propuesto` admitido o lote ya en `revisado`).
8. **Grabaciones** del LLM para que la evaluación corra sin red en la suite.

## Criterios de aceptación

- [ ] Informe de métricas en `evidencia/m1-19_metricas.md`, en total y por estrato, en sencillo.
- [ ] 0 cifras publicadas con una variable equivocada en la partición de desarrollo; si hay alguna, se analiza una por una.
- [ ] La partición no vista se corrió una sola vez, al final.
- [ ] Muestras y esfuerzo fijados con su evidencia.

## Nota

Los umbrales del §23.3 son **indicativos** en M1 y exigibles desde M2. Si el dueño aún no entregó sus preguntas, la historia se cierra con las del agente y queda una consulta abierta; M2 no empieza sin ellas.
