# Instrucciones para el agente implementador

Para el agente (Claude Code u otro) que implementa el backlog de `backlog/`. `CLAUDE.md` carga este archivo; no hay otra copia de estas reglas.

## 1. Qué es el proyecto, en una línea

Pregúntale al Perú responde preguntas sobre problemas del país con cifras de fuentes públicas oficiales, por territorio y con los límites de cada cifra. Un error en una cifra o una respuesta mal leída es peor que no responder.

## 2. Qué leer y en qué orden

| Orden | Documento | Para qué | Cuándo |
|---|---|---|---|
| 1 | `docs/decisiones.md` | Lo decidido: una fila por tema, con su ID (P-01, T-02, S-01…) y las pendientes del dueño (X-01…) | Siempre, antes de cada historia |
| 2 | `backlog/README.md` y `backlog/slice-N/README.md` | Objetivo del slice, orden de las historias, definición de hecho | Al empezar el slice |
| 3 | `backlog/slice-N/S<N>-<nn>-*.md` | La historia: contexto, tareas, criterios de aceptación | Antes de cada historia |
| 4 | `curados/motor/parametros_motor.yaml` | Valores por defecto del motor (pendientes del dueño y supuestos) | Antes de fijar cualquier número o comportamiento visible |
| 5 | `docs/especificaciones/contrato_respuesta.md` | Cómo debe verse toda respuesta (capas, redacción) | Al tocar texto o capas |
| 6 | `reglas/reglas.md` (y `reglas.json`) | Las 96 reglas que aplica el validador | Cuando una historia cita una regla |
| 7 | `docs/arquitectura.md` | Cómo está hecho el código hoy | Al empezar el slice |
| 8 | `curados/capa0/` (`dim_indicador.yaml`, `cruces_permitidos.yaml`, `nombres_mostrados.yaml`…) | Tablas curadas: la fuente de verdad de indicadores, cruces y nombres | Al planificar cifras |
| 9 | `docs/estado.md` | Foto del proyecto y deuda conocida | Para contexto |

Las citas a documentos de trabajo anteriores al repositorio (`03_auditoria/`, `00_proyecto/`…) no están aquí ni hacen falta: ver `docs/historia.md`. La evidencia de cada slice (`backlog/slice-N/evidencia/`) es registro, no instrucción.

## 3. Precedencia cuando dos fuentes no coinciden

1. `docs/decisiones.md`
2. `reglas/reglas.json` (lo genera el consolidador; es la implementación de las reglas)
3. Tablas curadas de `curados/capa0/` y las entradas de `curados/motor/parametros_motor.yaml` marcadas `decision:` o `pendiente:`
4. `contrato_respuesta.md` y las especificaciones de `docs/especificaciones/` y `reglas/`
5. El backlog
6. Las entradas de `parametros_motor.yaml` marcadas `supuesto:` (defaults de diseño)
7. La documentación descriptiva y el estado
8. El código existente (describe lo que hay, no lo que debe haber)

Si la que está más arriba contradice a la de más abajo, se sigue la de arriba y la discrepancia se anota como supuesto (sección 5). Si el código hace algo distinto de una decisión, se trata como vacío tipo C.

## 4. Cómo trabajar una historia

**Antes de la primera historia:** correr `uv run pytest -q` y guardar la salida en `backlog/slice-N/evidencia/pytest_base.txt`. Los fallos que ya estaban se anotan en `consultas_al_dueno.md` y no se arreglan salvo que la historia lo pida; «en verde» significa «sin fallos nuevos respecto de esa base».

1. Leer la historia, las decisiones que cita y el código que nombra. Buscar si lo que se va a crear ya existe (p. ej. `dim_indicador.niveles_validos`, `anios_disponibles`, `Motor.anio` para R-MOTOR-03, `map_intencion_tema` de R-GASTO-08b en `reglas.json`, `cruces_permitidos.yaml`): **se reutiliza, no se duplica**.
2. Marcar la historia «en curso» en el `README.md` del slice.
3. Implementar con pruebas. Correr `uv run pytest -q` completo antes de cada commit; desde S1-07, también la regresión Q1–Q4.
4. Commit con el ID: `S1-03: planificador de cifras`. Una rama por slice (`slice-1`); nunca forzar, reescribir historia ni borrar ramas ajenas.
5. Dejar la evidencia que piden los criterios en `backlog/slice-N/evidencia/` y marcar la historia «hecha» con un enlace a esa evidencia.
6. Si un criterio no se puede cumplir, la historia queda «bloqueada» con el motivo, y se sigue con la siguiente que no dependa de ella.

**Cuándo se detiene todo el slice** (y se avisa al dueño con un resumen en `consultas_al_dueno.md`):
- cambia una cifra, un semáforo o un nivel de confianza que no debía cambiar;
- no se puede correr el entorno (sección 8);
- una consulta tipo C bloquea una historia de la que dependen todas las siguientes.

## 5. Qué hacer con un vacío del diseño

Un vacío es algo que el backlog, las decisiones y las reglas no dicen. Se clasifica antes de actuar:

| Tipo | Qué es | Ejemplos | Qué hace el agente |
|---|---|---|---|
| **A. Implementación** | Cómo construirlo, sin cambiar lo que ve el usuario ni las cifras | Nombre de un módulo, estructura interna, librería ya presente en `uv.lock` | Decide siguiendo los patrones del código existente. Basta un comentario o el mensaje del commit |
| **B. Comportamiento visible o parámetro** | Algo que el usuario ve o un umbral de experiencia sin decisión: texto, orden, límite, formato | Cuántas opciones ofrecer en una aclaración, cómo nombrar un tema en la CLI, umbral de similitud de nombres | Usa el valor de `parametros_motor.yaml`. Si no existe, elige según los criterios de la sección 6, lo agrega al YAML con `supuesto: S1-xx` y lo registra en «Supuestos» de `consultas_al_dueno.md`. **No se detiene** |
| **C. Cifras, reglas, decisiones, fuentes o privacidad** | Cualquier cosa que cambie un número, el nivel o año de una cifra, una regla, una decisión, una cita o lo que se publica | Una regla que impide responder algo que la historia pide; un dato que no coincide con su dorada; un indicador sin el nivel que la historia supone; una decisión que el código no cumple | **No lo resuelve.** Lo escribe en «Consultas que bloquean» de `consultas_al_dueno.md` (qué pasa, en lenguaje sencillo, por qué importa y qué propone), deja esa parte sin hacer y sigue con lo demás. Nunca lo baja a supuesto para avanzar |
| **D. Contradicción entre documentos** | Dos fuentes dicen cosas distintas | El backlog pide algo que una decisión prohíbe | Aplica la precedencia de la sección 3 y lo anota. Si la contradicción es tipo C, es una consulta que bloquea |

Ante la duda entre B y C, es C.

### 5.1 Cuándo el agente puede aprobar una diferencia de texto

En la regresión (S1-07), el agente puede aprobar por sí mismo un cambio de texto en Q1–Q4 solo si se cumplen **todas** estas condiciones:
1. no cambian cifras, semáforos, nivel de confianza ni reglas con acción de bloqueo, supresión, subida de nivel o referencial;
2. el texto nuevo no agrega ninguna afirmación que el anterior no hiciera (solo cambia la forma de decir lo mismo, o quita algo que la plantilla genérica no puede producir);
3. pasa el corrector sin infracciones (`respuesta.infracciones_corrector`) y la capa 1 queda dentro de `respuesta.capa1_palabras_max`;
4. si la respuesta es «no se puede», eso sigue yendo primero.

Lo registra en `evidencia/regresion/<Q>.yaml` con `aprobado_por: agente`. Si falla cualquier condición, es una consulta tipo C.

## 6. Criterios para elegir un default (vacíos tipo B)

En este orden:

1. **Calidad de los datos primero:** ante la duda, no publicar la cifra, subir de nivel o preguntar; nunca adivinar un territorio, un año ni un indicador.
2. **Interfaz intuitiva:** menos texto, una sola cifra clave, decir primero lo que no se puede, palabras de todos los días y orden neutro (alfabético) cuando no hay un orden natural.
3. **Consistencia:** el mismo caso se resuelve igual en todo el motor; se prefiere el patrón que ya usan Q1–Q4.
4. **Reversible:** todo default vive en un archivo de datos (`parametros_motor.yaml` o los textos de `curados/motor/textos/`), nunca fijo en el código, para que el dueño lo cambie editando una línea.

## 7. Lo que nunca se hace

- Calcular o redondear una cifra fuera del cubo o de la biblioteca, o meterla al texto sin marcador (P-01, R-04).
- Citar algo que no sea un documento oficial (P-02); guardar datos personales (P-03).
- Descargar datos o agregar fuentes (F-04). Usar un LLM dentro del motor (está fuera del slice 1).
- Editar `reglas/reglas.json` a mano: las reglas se cambian solo con `python3 reglas/consolidador/consolida_reglas.py`, y solo si una decisión lo pide.
- Corregir un dato, una tabla curada o una dorada para que una prueba pase.
- Editar `docs/decisiones.md`, salvo para registrar lo que el dueño decidió (editando la fila, nunca agregando una que aclare otra).
- Borrar archivos del dueño o crudos del almacén; operaciones de git destructivas.

## 8. Entorno y comandos

- Mac del dueño, uv + Python 3.12: `uv sync`; ayuda: `uv run pap --help`.
- **Si no puedes correr `uv run pytest -q` ni `uv run pap`** (otro equipo, sin Python 3.12, sin la biblioteca de Parquet): no implementes historias que toquen cifras o respuestas. Escribe la consulta en `consultas_al_dueno.md` y detente; solo puedes avanzar en lo que no necesita el cubo (esquemas, textos, documentación).
- Las pruebas nuevas que dependen del cubo o de la biblioteca **fallan** si faltan, no se saltan (no copiar el `pytest.skip` de `test_respuesta_p3.py`): un salto daría un falso verde.
- Pruebas: `uv run pytest -q`.
- Respuestas del piloto: `uv run pap preguntar curados/motor/consultas_minimas/` (consultas mínimas de Q1–Q4; los `q*.yaml` originales están archivados en `tests/fixtures/consultas_piloto/`).
- Reglas: `python3 reglas/consolidador/consolida_reglas.py`; verificación: `python3 -I reglas/consolidador/pruebas/vp3_checks.py .` y `python3 reglas/consolidador/pruebas/prueba_guardia.py`.
- Nombres de lugares siempre con tildes y ñ (T-02); para emparejar fuentes se usa `nombre_normalizado`.

## 9. Cómo informar

- Durante el trabajo: el estado de cada historia en el `README.md` del slice; las dudas, en `consultas_al_dueno.md`.
- Al cerrar el slice: `backlog/slice-N/evidencia/cierre.md`, una página en lenguaje sencillo con:
  - qué puede hacer ahora el usuario;
  - qué quedó fuera;
  - los supuestos aplicados que el dueño debe revisar;
  - las consultas abiertas;
  - qué se aprendió para detallar el slice siguiente.
- Las respuestas al dueño, en español, sin jerga técnica innecesaria y con una propuesta concreta cuando hay que decidir algo.
