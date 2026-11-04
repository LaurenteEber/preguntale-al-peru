# Encargo S1-09 — Auditor estadístico

Quién: un subagente nuevo, sin la conversación del implementador ni los informes de los otros revisores (P-06).
Rama `slice-1`. No se edita código ni datos: el auditor solo lee, corre comandos y entrega su informe.

## Qué revisar

1. `codigo/motor/intenciones.yaml` y `codigo/ingesta/pap/motor/planificador.py` contra las decisiones E-03, E-04, E-05, E-06, E-07, E-08, S-01, T-03, G-07 y R-03 de `00_proyecto/decisiones.md` (y las tablas que citan: `codigo/capa0/datos/dim_indicador.yaml`, `cruces_permitidos.yaml`, `map_intencion_tema` de R-GASTO-08b en `04_reglas/reglas.json`). En particular:
   - ¿alguna combinación pide una cifra prohibida (cobertura del SIEN por provincia o distrito, cruce fuera de CR-01, tendencia entre los dos criterios de anemia, coeficientes)?
   - ¿se excluye solo 2020 en la ENDES (E-07) y se cortan los demás quiebres?
   - ¿la evolución de anemia ENDES usa las dos formas solo en evolución, con primer y último año, sin años intermedios (E-06)?
   - ¿Lima usa sus ámbitos y no el departamento 15 (T-03)? ¿«más pobre» usa el grupo robusto del Mapa 2018 por distrito y los grupos del INEI por departamento (E-08)?
   - ¿el planificador anticipa alguna supresión que debería decidir el validador (E-02, E-03, P-04)?
2. Elegir **15 respuestas** variadas (temas, intenciones, niveles, con y sin «no se puede»), generarlas con la CLI y, para **al menos una cifra de cada fuente** (ENDES, ENAHO, SIEN, gasto MEF, Mapa de Pobreza), verificar que coincide con la dorada oficial (`codigo/capa0/datos/cifras_doradas.csv`) o con el cubo (`05_biblioteca/indicadores/fact_indicador.parquet`, con DuckDB), incluidos intervalo, año, nivel y territorio. Comprobar también que el verbo de cambio («subió/bajó de forma estadísticamente clara», «sin cambio claro») corresponde a la prueba guardada en la cifra.
   - Generar respuestas: `uv run pap preguntar --intencion <i> --tema <t> --territorio "<lugar>" [--anio N] --salida salidas/s1-09_auditor` (opciones con `uv run pap preguntar --help`); las consultas de la matriz están en `codigo/ingesta/tests/matriz/generar.py` y su reporte en `backlog/slice-1/evidencia/matriz.md`.

## Criterios

- Bloqueante: se publicaría una cifra errada o prohibida por una decisión, o se afirma un cambio que la prueba no respalda.
- Alto: una decisión se aplica mal en una clase de preguntas, aunque la cifra sea correcta.
- Medio: el texto o la ficha pueden inducir una lectura estadística incorrecta.
- Bajo: mejora de claridad o documentación.
- Lo que contradice una decisión vigente se reporta, no se propone cambiar la decisión.

## Qué entregar

El texto completo de `backlog/slice-1/evidencia/auditoria_estadistica.md`, en español: veredicto («apto», «apto con observaciones» o «no apto»); las 15 respuestas revisadas (comando y resultado); la tabla de cifras verificadas (fuente, indicador, año, nivel, territorio, valor de la respuesta, valor de la dorada o del cubo, ¿coincide?); los hallazgos numerados con su clasificación, la evidencia (`archivo:línea` o comando) y la corrección propuesta.
