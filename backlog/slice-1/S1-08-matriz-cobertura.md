# S1-08 — Matriz de cobertura automática

## Por qué

Cuatro preguntas no prueban un motor general. La matriz recorre sistemáticamente lo que una persona podría preguntar con los datos del piloto y encuentra los casos rotos antes que el usuario.

## Tareas

1. Generador `tests/matriz/generar.py` que arma consultas mínimas para:
   - **temas × intenciones válidas** según `intenciones.yaml`;
   - **territorios:** nacional; los 23 departamentos sin Lima, más Lima Metropolitana, Lima Región y el Callao; provincias y distritos según `matriz_cobertura` de `parametros_motor.yaml` (semilla fija), estratificados por región natural, incluyendo: los 15 de `nombres_mostrados.yaml`, Q2 y Q3, Alto Trujillo, Sangani, 3 distritos sin establecimientos en el SIEN y 3 homónimos (resueltos con `--elegir`), tomados de `evidencia/s1-00_datos_territorio.txt`;
   - **periodos:** último, un año intermedio, un año sin datos y una serie.
2. Corredor que responde todo y clasifica cada caso: `respondida`, `no_se_puede` (con motivo), `aclaracion`, `error`.
3. Comprobaciones automáticas en cada respuesta: validador sin errores de ejecución; capa 1 dentro de `respuesta.capa1_palabras_max` (R-04); sin infracciones del corrector (`respuesta.infracciones_corrector`); sin marcadores `{{…}}`, sin IDs de regla ni de indicador, sin nombres de columnas; nombres de lugar con su ortografía de T-02; cada cifra visible con su cita (P-02).
4. Reporte `backlog/slice-1/evidencia/matriz.md`: totales por clase y por tema, los 20 casos más largos y todos los fallos con su consulta.
5. Una versión reducida (`matriz_cobertura.casos_pytest` casos fijos) entra a `pytest` y **falla** (no se salta) si falta el cubo; la completa se corre a mano, con `--salida` fuera de git, y su reporte se guarda.

## Criterios de aceptación

- [ ] 0 casos `error`.
- [ ] 0 respuestas con marcadores, códigos internos o con la capa 1 por encima de `respuesta.capa1_palabras_max`.
- [ ] Toda combinación sin datos sale como `no_se_puede` con un motivo de S1-05.
- [ ] El reporte está en `evidencia/` y la versión reducida en `pytest`.
