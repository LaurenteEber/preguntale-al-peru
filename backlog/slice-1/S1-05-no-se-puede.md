# S1-05 — Respuestas de «no se puede» y aclaraciones

## Por qué

Con preguntas abiertas aparecen muchas que los datos no pueden responder. La regla de redacción 1 del contrato manda decirlo primero y luego ofrecer lo más cercano. Una respuesta vacía, un error técnico o una cifra forzada son los peores resultados posibles.

## Tareas

1. Un tipo de respuesta `no_se_puede` con su motivo, que sale por las mismas capas (respuesta corta + «Lo más cercano que sí tenemos» + motivo en «Más contexto»). Motivos mínimos:
   - tema fuera del piloto («Todavía no tenemos datos de ese tema»), con la lista de temas disponibles;
   - año sin datos (ofrece el más cercano disponible);
   - nivel no válido o sin inferencia verificada (ofrece el nivel superior, E-02, R-REG-02);
   - cifra suprimida por precisión (E-03), por privacidad (P-04) o por falta de inferencia verificada (E-02): la decide el validador; S1-05 la detecta en el `estado_cifra` y su traza y nunca muestra el valor;
   - distrito creado después del último dato (ofrece su distrito de origen o la provincia, T-01, T-04);
   - intención no soportada para el tema (p. ej. evolución del SIEN, que solo tiene 2025, como Q3);
   - sin registros en el lugar (distrito sin filas del SIEN: la cifra viene `sin_fila`).
   Se reutilizan los `motivos_codificados`, el `mensaje_usuario` y `max_alternativas` de R-LENGUAJE-05 en `reglas.json`; solo se agregan los motivos que esa regla no trae.
2. Un tipo `aclaracion` (de S1-02 y de consultas incompletas) con la pregunta y sus opciones, sin calcular nada. `Motor.responder` desvía antes de calcular cuando el plan trae `no_se_puede` o `aclaracion`; comprobar que `ficha.generar` y `capas.construir` funcionan con cero cifras.
3. Textos en `curados/motor/textos/no_se_puede.yaml`; pasan el corrector.
4. Pruebas: un caso por motivo.

## Criterios de aceptación

- [ ] Cada motivo tiene prueba y texto revisable.
- [ ] Ninguna respuesta `no_se_puede` contiene una cifra suprimida o inventada.
- [ ] La respuesta corta dice primero lo que no se puede, en no más de `no_se_puede.respuesta_corta_max_oraciones` oraciones; el año y el nivel alternativos siguen `no_se_puede` de `parametros_motor.yaml`.
