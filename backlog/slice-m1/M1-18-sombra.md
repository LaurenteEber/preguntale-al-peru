# M1-18 — Modo sombra

**Se deriva de** el diseño §24.

## Tareas

1. **`motor.version` por tema** (`actual`, `sombra`, `nuevo`) en `curados/motor/parametros_motor.yaml`. En M1 ningún tema pasa a `nuevo`.
2. **Con `sombra`:** la web y la CLI responden con el motor actual; el motor nuevo calcula aparte y registra las diferencias (valor, estado, salida), sin el texto de la pregunta. Un error del motor nuevo nunca afecta la respuesta.
3. **`pap preguntar --motor nuevo`** (solo CLI) para ver la respuesta del motor nuevo en contrato v2.
4. **Informe de diferencias** (`pap inferencia sombra-informe`): por tema, cuántas respuestas coinciden y cuáles difieren, con su motivo.

## Criterios de aceptación

- [ ] El modo sombra corre sobre Q1–Q4, la matriz de cobertura y el conjunto de evaluación sin errores.
- [ ] En anemia y desnutrición crónica de 2024, las cifras del motor nuevo coinciden con las del actual; toda diferencia está explicada.
- [ ] Con el motor nuevo apagado o fallando, la web responde igual que hoy (prueba).
