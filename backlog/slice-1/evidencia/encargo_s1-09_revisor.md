# Encargo S1-09 — Revisor de usuario

Quién: un subagente nuevo, sin la conversación del implementador ni los informes de los otros revisores (P-06).
Rama `slice-1`. No se edita código ni datos: el revisor solo lee, corre la CLI y entrega su informe.

## Qué revisar

Con las **4 personas** de `03_auditoria/revision_usuario/informe_revision_usuario_q1_q4.md` (léelo primero, junto con `00_proyecto/piloto/contrato_respuesta.md`), leer **20 respuestas** del motor nuevo, elegidas para cubrir temas, intenciones y niveles, incluidas **al menos 4 de «no se puede»** y **2 aclaraciones** (por ejemplo «Lima» y «Huancavelica» sin nivel, o un homónimo como «San Juan»). Leer cada respuesta como la vería la persona: capa 1 (respuesta corta, cifra clave, «Ojo al leer», confianza), capa 2 («Más contexto», avisos, límites) y capa 3 (citas, glosario).

- Generar respuestas: `uv run pap preguntar --intencion <i> --tema <t> --territorio "<lugar>" [--anio N] [--elegir N] --salida salidas/s1-09_revisor` (opciones con `uv run pap preguntar --help`); leer el `.md` que escribe. Ideas de casos: `backlog/slice-1/evidencia/matriz.md` y `codigo/ingesta/tests/matriz/generar.py`.

## Criterios

Anotar, por respuesta y por persona, las **malas lecturas probables**: qué entendería mal, por qué y en qué frase. Prestar atención a: si la respuesta corta contesta la pregunta literal y, cuando no se puede, lo dice primero; si hay una sola cifra clave; si el «Ojo al leer» se entiende; si la confianza explica su motivo sin jerga; si un «no se puede» deja claro qué sí hay; si una aclaración se entiende y sus opciones se distinguen; nombres de lugares con tildes; jerga, siglas sin explicar, frases repetidas o contradictorias entre capas.

Clasificación: bloqueante (la lectura natural es falsa), alto (una persona probable lo entiende mal), medio (confunde pero el texto lo aclara), bajo (estilo).

## Qué entregar

El texto completo de `backlog/slice-1/evidencia/revision_usuario.md`, en español: veredicto («apto», «apto con observaciones» o «no apto»); la lista de las 20 respuestas (comando y tipo); por cada una, las malas lecturas por persona; los hallazgos numerados con su clasificación, la frase exacta y una redacción propuesta.
