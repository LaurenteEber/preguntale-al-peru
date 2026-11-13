# M1-06 — Fichas de tabla, bloques y temas

**Se deriva de** `docs/diseno/fichas.md` (completo).

## Tareas

1. **`curados/inferencia/temas.yaml`** con los temas y subtemas provisionales de `fichas.md` §8 (`estado: provisional`).
2. **`curados/inferencia/fichas/ENDES.yaml`:** los 10 campos a mano de las **34 tablas** (`fichas.md` §5.1), leyendo el diccionario de cada tabla, el cuestionario y el documento «Identificadores de las bases de datos».
   - Confirmar o corregir los temas marcados «por confirmar» (RE758081, REC91, RECH4).
   - `poblacion` estructurada: edades y sexo se comprueban contra los datos cuando la tabla trae la variable.
   - Avisos conocidos: REC93DVdisciplina (341 filas, C-M0-05-2).
3. **`curados/inferencia/bloques/ENDES.yaml`:** bloques temáticos del lote de tablas del README. Punto de partida: baterías del índice (`grupo`) y secciones del cuestionario (M1-04). Cada variable `categoria` o `medida` en un solo bloque. Cada bloque con tema, subtema, `papel` y, si aplica, ventana y población más estrecha.
4. **`src/pap/inferencia/fichas.py`** y los comandos `pap fichas generar`, `validar` y `ver` (`fichas.md` §3 y §9):
   - arma `fichas_tabla.parquet` y `bloques.parquet`, y escribe `bloque_id` en `variables.parquet`;
   - aplica las 8 reglas de validación;
   - es reproducible (dos corridas dan los mismos archivos).
5. **Cardinalidad de las uniones** con cita: usar el documento n.º 11 para citar las llaves y uniones de `archivos_endes_2024.yaml` que hoy solo están comprobadas contra los datos. Si el documento contradice una unión declarada, es consulta.
6. **Revisión del auditor-agente** de fichas y bloques contra los diccionarios (`evidencia/m1-06_revision.md`), y lote para el visto del dueño.

## Criterios de aceptación

- [x] 34 fichas; `pap fichas validar` sale con 0.
- [x] Cobertura de bloques: 100 % de las variables `categoria` y `medida` de las tablas del lote; el número de bloques por tabla informado.
- [x] `pap fichas ver RECH6` muestra la ficha completa en texto legible.
- [x] La columna `bloque_id` no cambia ninguna otra columna del índice (comparación antes y después).
- [x] Revisión del auditor-agente sin hallazgos abiertos, o con sus consultas anotadas.

## Fuera

La ficha común y el enlace entre fuentes (anexo de varias fuentes). Bloques de CSALUD y programas sociales, salvo que sobre tiempo.
