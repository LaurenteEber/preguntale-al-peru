# S2-05 — Interpretar: validar, anclar, aclarar y «Entendimos»

## Por qué

Todo lo que rodea al LLM es determinista y se prueba. El LLM propone y el código decide si acepta, si pregunta o si dice que no.

## Tareas

### 1. `interpretar(texto, motor, *, elegir=None) -> dict` (`src/pap/interprete/interpretar.py`)

En este orden:

1. **Limpiar** (S2-04).
2. **Caché.** Si hay una interpretación vigente para esa huella (`interprete.cache_horas`), se usa. Si no, se llama al LLM.
   - **Con `elegir` y sin caché vigente:** error de uso («la pregunta venció; escríbela de nuevo»). **Nunca se reinterpreta** para elegir.
   - En pytest, la caché va a una carpeta temporal.
3. **Validar** con el esquema de S2-01. Si falla, un reintento con el mensaje del error. Si vuelve a fallar → `no_entendida`.
4. **Anclas.** Se normaliza la pregunta y cada ancla: minúsculas, sin tildes, signos → espacio, espacios colapsados.
   - Cada ancla tiene que aparecer en la pregunta normalizada.
   - `territorio.texto`, `comparar_con.texto` y `dentro_de.texto` deben ser **iguales a su ancla** una vez normalizados. El LLM no puede agregar palabras.
   - `nacional: true` necesita un ancla que esté en la lista de textos que el resolver acepta como todo el país.
   - `nivel` necesita un ancla con una de las palabras que fijan el nivel (S2-03).
   - `anio`, `desde` y `hasta` deben ser iguales a un número de 4 cifras de su ancla.
   - Un valor sin ancla válida **se descarta** y sigue al paso 5.
5. **Lo que falta** (parámetros de `interprete`):
   - **Sin intención:** `nivel_actual` o aclaración.
   - **Sin lugar:** aclaración armada por el código con las opciones de `interprete.yaml` («Todo el Perú», «Escribe el lugar»).
   - **Año relativo descartado:** opciones «el último año con datos» o «Escribe el año».
   - Estas opciones las arma el código, así que no llevan anclas.
   - «Escribe…» no es una consulta: termina con el mensaje de volver a preguntar.
6. **Lugares escritos con paréntesis** («Ayaviri (Melgar, Puno)»): antes del resolver, el texto pasa a la forma con comas («Ayaviri, Melgar, Puno»). Es una transformación fija y probada, y el resolver no cambia.
7. **Despachar:**

   | Resultado | Qué se hace |
   |---|---|
   | `consulta` | Se agrega `pregunta_original` (la pregunta limpia) e `idioma: es`, y se llama a `preguntar_minima(motor, consulta, elegir=…)` |
   | `aclaracion` | Respuesta con **la misma forma que `respuesta_aclaracion()`**: `{tipo: "aclaracion", texto, aclaracion: {motivo: "interprete_<motivo>", pregunta, opciones: [{n, etiqueta, …}]}}`. La etiqueta de cada opción es su «Entendimos…» (punto 3), en orden alfabético por etiqueta (`agents.md` §6.2) |
   | `fuera_de_alcance`, `tipo: tema` | `respuesta_no_se_puede` con un plan aparte, como hace `preguntar_minima` con `tema_fuera_del_piloto`, sin pasar por `cargar()`. `tema_pedido` = el ancla `pedido` |
   | `fuera_de_alcance`, `tipo: pregunta` | Plan aparte con un motivo nuevo, `interprete_fuera_de_alcance` (en `no_se_puede.yaml` con `regla: null`). Dice qué tipos de pregunta sí respondemos. No se dice «no tenemos datos de ese tema» |
   | `no_es_pregunta`, `otro_idioma`, `no_entendida`, `no_disponible` | Mensaje fijo (tabla de S2-06) |

### 2. `--elegir` con el intérprete

- Si la respuesta es una aclaración del intérprete, consume el primer número y pasa el resto a `preguntar_minima` (aclaración de territorio), como hace `falta_tema`.
- **El intérprete valida los números de más** antes de llamar al motor, con la cuenta total escrita por la persona y los textos `elegir_de_mas*` de `cli.yaml`.
- Si no hay nada por elegir, lo dice como hoy.

### 3. «Entendimos» (`entendimos`)

- Una frase armada **desde la consulta** con plantillas de `interprete.yaml` por intención. Ejemplo: «Entendimos: cómo cambió la anemia en el departamento de Puno».
- Si el lugar ya está resuelto, usa el nombre del resolver. Si no (homónimo pendiente), usa el texto literal entre comillas: «en «Huancavelica»».
- Lleva años, pero nunca otros números.

### 4. Pruebas (`tests/interprete/test_interpretar.py`, con grabaciones o con un LLM falso inyectado)

- Una por fila de la tabla del paso 7 y por cada regla del paso 4.
- **LLM falso adversario:** devuelve «departamento de Huancavelica» con ancla «Huancavelica», un año que no está en la pregunta, un ubigeo, una cifra en el texto del lugar y un `nivel` sin ancla. **Ninguno** llega a la consulta ni a la respuesta.
- `--elegir 2,1`: aclaración del intérprete y luego de territorio. Números de más con la cuenta correcta. `--elegir` sin caché → error, sin llamar al LLM.
- **Equivalencia** (README, segunda comparación): para cada entrada `consulta` del conjunto con grabación, el `respuesta.json` por texto es igual al de `preguntar_minima(consulta producida + misma pregunta_original)`, salvo `interpretacion`, `entendimos` y rutas.
- **Evaluación con grabaciones:** `tests/interprete/test_evaluacion_grabada.py` corre el conjunto y exige las dos métricas absolutas en 0. Las demás métricas se informan, sin umbral hasta S2-09.

## Criterios de aceptación

- [ ] Las pruebas del LLM falso adversario y de equivalencia están en verde.
- [ ] Regresión Q1–Q4 por la vía estructurada sin cambios.
- [ ] Ningún texto visible nuevo está en Python.
