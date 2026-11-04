# Cierre del slice 1 — Motor por intenciones

3/11/2026 · rama `slice-1` → `main`, etiqueta `slice-1-cerrado` · huella del cubo `ba1fbc55…` (sin cambios en el slice desde S1-00).

## Qué puede hacer ahora el usuario

- Preguntar por cualquier lugar y año con datos, sin escribir una consulta ni una plantilla a mano: `uv run pap preguntar --intencion evolucion --tema anemia --territorio Huancavelica`. Sirve para los 9 indicadores del piloto y para seis tipos de pregunta: cuánto hay, cómo cambió, comparar dos lugares, el lugar más alto, cruce y efecto.
- Si el lugar es ambiguo, la respuesta pregunta antes de calcular: «Hay varios lugares llamados «Huancavelica». ¿Cuál quieres?». También pregunta con «Lima» a secas, que tiene tres ámbitos (T-03), con homónimos como «San Juan» y cuando hay errores de tipeo. Se responde con `--elegir N` (`N,N` en una comparación).
- Cuando los datos no alcanzan, la respuesta dice primero qué no se puede, da el motivo y ofrece lo más cercano, sin mostrar ninguna cifra suprimida. Por ejemplo: «No podemos mostrar cuánto hay de desnutrición crónica en Ayaviri por distrito. Sí tenemos la cifra para el departamento de Puno».
- Las comparaciones entre lugares dicen cuál es mayor solo si la prueba estadística lo respalda (R-ENC-11).
- Q1–Q4 salen por este camino nuevo con las mismas cifras, semáforos y niveles de confianza que la referencia.

## Definición de hecho, punto por punto

| Punto | Estado | Evidencia |
|---|---|---|
| 1. Q1–Q4 con las mismas cifras, semáforos y confianza; cambios de texto aprobados | cumplido | `codigo/ingesta/tests/test_regresion_q1_q4.py` (fases 1 y 2); `evidencia/regresion/Q1–Q4.yaml`. La diferencia de Q1, sin el pico de 2022, la aprobó el dueño en C-01 |
| 2. Matriz sin caídas, marcadores, códigos internos ni capa 1 por encima de 125 palabras; toda combinación sin datos da «no se puede» con motivo | cumplido | [matriz.md](matriz.md): 5 086 casos, 0 errores, 0 fallos; versión reducida en `test_matriz_cobertura.py` |
| 3. Aclaraciones de territorio según T-03 y R-TERRITORIO-09 | cumplido | `test_resolver_territorio.py` (133 casos); D-01 registrada |
| 4. `pytest` entero en verde; el cubo no cambia de huella en el slice | cumplido | [s1-09_pytest_cierre.txt](s1-09_pytest_cierre.txt) y, en `main` tras la fusión, [s1-10_pytest_main.txt](s1-10_pytest_main.txt): 748 pasan; la huella es `ba1fbc55` desde S1-00 (se reconstruyó tras C-05 y salió igual) |
| 5. Revisión independiente de usuario y estadística «apto» o «apto con observaciones» | cumplido | [auditoria_estadistica.md](auditoria_estadistica.md) y [revision_usuario.md](revision_usuario.md): «no apto» en la primera revisión y «apto con observaciones» en la segunda; [verificacion_correcciones.md](verificacion_correcciones.md) |
| 6. Documentación al día y etiqueta `slice-1-cerrado` | cumplido | S1-10 (este cierre) |

## Qué quedó fuera

- El LLM que traduce el texto libre a una consulta mínima (slice 2), la API y la web.
- Datos o indicadores nuevos y cambios de reglas, salvo los que decidió el dueño (C-04, C-05).
- Observaciones medias y bajas de la revisión, sin conclusiones falsas en la capa 1. La lista completa está en [correcciones_s1-09.md](correcciones_s1-09.md); conviene resolverlas al empezar el slice 2:
  - el cruce «lado a lado» muestra en la capa 1 solo el gasto;
  - la evolución no muestra el año con el que compara;
  - la respuesta de efecto tiene una frase de regla que se contradice;
  - la evolución del gasto no dice por qué no compara 2023 con 2025 (R-GASTO-12: montos sin deflactar);
  - detalles de redacción.

## Supuestos aplicados que el dueño debe revisar

Están en `consultas_al_dueno.md` («Supuestos aplicados») y cada uno se cambia editando una línea de `parametros_motor.yaml` o de `codigo/motor/textos/`. Los que más pesan:

- **S1-08-a:** si la capa 1 pasa de 125 palabras, los últimos «Ojo al leer» bajan a «Avisos» de la capa 2, y siempre queda al menos uno visible.
- **S1-04-a:** el nombre largo de un distrito aparece una vez, en la capa 2. Tras una aclaración de homónimo, también va en la capa 1 y en la cita (S1-09).
- **S1-03-b y S1-03-c:** la evolución de desnutrición, pobreza, gasto y SIEN se cuenta con el primer y el último año comparables. «El más alto» de anemia y desnutrición usa el ranking departamental de 26 unidades.
- **S1-03-a y S1-03-d:** «el más pobre dentro de Puno» y los cruces fuera de CR-01 responden «no se puede» o dan cifras por separado.
- **S1-05-a a S1-05-g:** la redacción de cada «no se puede», cuáles son totales o parciales, y cómo se elige lo más cercano.
- **S1-02-a a S1-02-e, S1-06-a a S1-06-c:** textos de las aclaraciones, alias de Lima, opciones de la CLI y códigos de salida.

## Consultas al dueño

- **Cerradas en el slice:**
  - C-01: Q1 sin el pico de 2022.
  - C-02: dos formas de medir la anemia solo en evolución.
  - C-03: «La Unión» y «Páucar del Sara Sara».
  - C-04: NC-NIVEL de respaldo, solo cuando ningún otro código aplica.
  - C-05: la evolución del gasto incluye 2023.
- **D-01 (no bloquea):** alinear `ambiguos_conocidos` de R-TERRITORIO-09 con T-03 la próxima vez que se toque el consolidador.
- **Pendientes de `decisiones.md` que siguen con el comportamiento de hoy:**
  - X-02: conteo del SIEN.
  - X-03: CR-01 con el gasto del mismo año.
  - X-04: un solo intervalo.
  - X-01 y X-05 a X-08.
- **Nota tipo D:** T-02 dice que el nombre de las provincias sale del archivo propio, pero el código usa el Directorio 2025 para 194 de 196.
- **Posible consulta nueva (auditoría, N-1):** si la serie de gasto 2023–2025 debe mostrarse en soles constantes para poder compararla.
- **El respaldo de los Parquet** (`05_biblioteca/_respaldo_pre_s1-00/`, 355 MB) sigue en disco hasta que el dueño decida borrarlo.

## Qué aprendimos para detallar el slice 2

1. **El LLM solo tiene que producir la consulta mínima.** El esquema (`consulta_minima.schema.json`) y sus mensajes de error ya están, así que la frontera es estrecha y validable. Los alias de temas (`temas.alias_cli`) sirven tal cual.
2. **La matriz encuentra lo que cuatro preguntas no encuentran**: 91 capas 1 demasiado largas, y en la revisión, comparaciones sin prueba y grupos de un solo lugar. Conviene correrla en cada historia, no solo al final.
3. **Los revisores independientes encontraron lo que las pruebas no cubrían.** Todos los casos que reportaron tenían cifras correctas con una lectura equivocada. Vale la pena revisar más temprano, con menos respuestas y más seguido.
4. **Las tablas curadas y las reglas tienen huecos que solo aparecen al generalizar** (C-04, C-05). Vale reservar tiempo del dueño para responder rápido.
5. **El texto de las reglas que llega al usuario** (la estructura de efecto, por ejemplo) también necesita revisión de lenguaje. Cambia solo con el consolidador.
6. **La huella del cubo sirve de seguro**: comprobar que no cambió después de cada cambio de datos curados evitó dudas sobre las cifras.
