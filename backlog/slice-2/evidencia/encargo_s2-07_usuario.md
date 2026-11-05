# Encargo S2-07 — Revisor de usuario

Quién: un subagente nuevo, sin la conversación del implementador ni el informe del otro revisor. No se edita código, datos ni pruebas: el revisor escribe sus preguntas, corre la CLI, lee las respuestas y entrega su informe.

**No leer:** `curados/interprete/` (instrucciones del intérprete), `src/pap/interprete/` (código del intérprete), `tests/interprete/` (conjunto de evaluación y pruebas), `backlog/slice-2/evidencia/cambios_prompt.md` ni el informe del otro revisor.

## Qué hacer

1. Lee `docs/manual_de_uso.md` y `docs/especificaciones/contrato_respuesta.md`. Las 4 personas son las de la revisión del slice 1 (`backlog/slice-1/evidencia/revision_usuario.md`, línea 4): madre de Huancavelica o Puno, periodista, regidor o funcionario, estudiante o docente.
2. Escribe **20 preguntas propias**, como las escribiría cada persona (5 por persona), sobre anemia, desnutrición crónica, pobreza y gasto público en lugares del Perú, con tus palabras: cuánto hay, cómo cambió, comparar dos lugares, dónde es más alto, si el gasto tuvo efecto, alguna ambigua, alguna con un lugar homónimo o mal escrito. Inventadas: ningún dato personal real. Guárdalas, antes de correr nada, en `backlog/slice-2/evidencia/preguntas_s2-07_usuario.yaml` con la forma `entradas: [{id: u01, persona: …, pregunta: "…"}]`.
3. Corre cada una así (una vez; si la respuesta es una aclaración, repite con `--elegir N` la opción que elegiría la persona):

   `PAP_INTERPRETE_MODO=completar uv run pap preguntar --texto "<pregunta>" --salida salidas/s2-07_usuario`

   Lee lo que imprime y el `.md` que escribe en `salidas/s2-07_usuario/`. Como mucho 40 corridas en total.
4. **Nunca** muestres, imprimas ni busques variables de entorno (nada de `env`, `printenv`, `echo $…`, `set -x`).

## Criterios

Por pregunta: ¿«Entendimos…» dice lo que la persona preguntó? ¿La respuesta contesta esa pregunta y no otra? ¿Se entienden las aclaraciones y sus opciones se distinguen? ¿Algún mensaje fijo o «no se puede» confunde o deja sin salida? Clasificación: bloqueante (la lectura natural es falsa), alto (una persona probable lo entiende mal), medio (confunde pero el texto lo aclara), bajo (estilo).

## Qué entregar

El texto completo de `backlog/slice-2/evidencia/revision_usuario_s2.md`, en español: veredicto («apto», «apto con observaciones» o «no apto»); la tabla de las 20 preguntas (id, persona, resultado: respuesta, aclaración, no se puede o mensaje); hallazgos numerados con su clasificación, la pregunta (por id), la frase exacta y una propuesta. Escribe el archivo tú mismo y devuelve un resumen corto.
