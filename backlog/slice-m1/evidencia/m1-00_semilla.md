# M1-00, tarea 11 — Conjunto semilla de evaluación

**Archivo:** `tests/inferencia/evaluacion.yaml` (38 preguntas, `autor: agente`, `estado: propuesto`, formato de M1-19). **Prueba:** `tests/inferencia/test_evaluacion_semilla.py`.

## Qué es

Preguntas en lenguaje cotidiano sobre las tablas de niño, mujer y hogar de la ENDES 2024 del lote de M1. Cada una trae la variable (o variables) que debería elegir el sistema, la tabla, el territorio y el periodo si los hay, y la cifra oficial cuando el proyecto la tiene. Lo usan M1-05 (enriquecimiento) y M1-09 / M1-09b (recuperador); M1-19 lo completa. `plan_esperado` queda en `null`: lo completan M1-19 y los dos revisores del universo.

## Conteos

| Estrato | Preguntas | De ellas, no vistas |
|---|---|---|
| pares casi iguales | 8 | 3 |
| directa (supuesto M1-00-s7, ver abajo) | 7 | 1 |
| vocabulario popular | 7 | 4 |
| respuesta múltiple | 5 | 1 |
| universo con convención | 3 | 0 |
| parecen no tener insumos | 3 | 1 |
| sin insumos | 2 | 0 |
| ambiguas | 2 | 1 |
| temas nuevos | 1 | 0 |
| **Total** | **38** | **11 (29 %)** |

Partición: 27 `desarrollo` y 11 `no_vista` (la prueba exige entre 25 % y 35 %). Las `no_vista` **no se usan** para ajustar prompts, sinónimos ni umbrales; se corren una sola vez al final (M1-19).
Salidas esperadas: 31 respuesta, 5 aclaración, 2 «no se puede». Con cifra oficial: 13. Sin cifra oficial: 25.

## Cómo se obtuvieron las cifras

Solo hay cifra oficial en el proyecto para tres indicadores de la ENDES 2024: anemia (criterio RM 363-2022), anemia (criterio OMS 2024) y desnutrición crónica. Las 13 cifras salen **tal cual** de `curados/capa0/cifras_doradas.csv` (las mismas que citan las recetas de M0-10): `id_cifra`, valor, documento, cuadro y página, URL. Nada se calculó ni se redondeó. La prueba `test_cifras_oficiales_son_las_de_las_doradas` compara cada una con el CSV (valor y cita idénticos). Las demás preguntas llevan `cifra_oficial: null`: no se inventó ninguna.
Las variables esperadas se verificaron contra `biblioteca/variables/variables.parquet` (año 2024, solo lectura); la prueba las vuelve a verificar. Todas existen (el índice está en estado `propuesto`, el que mide M1-19 a menos que haya lote `revisado`).
El archivo se generó con un script temporal (fuera del repositorio) que copia las citas del CSV; el YAML es la fuente, editable a mano.

## Prueba

- RED: con el archivo ausente, las 4 pruebas fallaron («falta tests/inferencia/evaluacion.yaml»).
- GREEN: `uv run pytest -v tests/inferencia/test_evaluacion_semilla.py` → 4 passed (estructura, cobertura/partición, variables en el índice 2024, cifras = doradas).
- Lleva las marcas `regresion_microdatos` y `solo_mac` como `test_indice_regresion.py` (el índice solo está en el Mac): en la nube se deja fuera, y si falta el índice **falla**, no se salta.

## Supuestos (vacíos tipo B, para registrar en `consultas_al_dueno.md`)

- **M1-00-s7 — estrato «directa».** M1-19 no tiene un estrato para las preguntas sin dificultad especial (p. ej. «¿qué porcentaje de niños tiene desnutrición crónica?»). Se agregó `directa` a los estratos permitidos de la semilla, para no forzarlas en uno de los siete. Reversible: se renombran o reclasifican editando el YAML y la lista de la prueba.
- **M1-00-s8 — tamaño y partición.** Se hicieron 38 preguntas (la historia pide «unas 30») para tener los estratos pedidos; la partición no vista se fijó a mano en 11 de 38 (29 %), repartida entre estratos, sin sorteo.

## Dudas abiertas

- **D1 — anemia sin decir la norma (EV-001).** Hay dos criterios publicados (RM 363-2022 y OMS 2024). La semilla espera `respuesta` con HC57 (la receta `endes_anemia_6_35m`). Si el dueño prefiere que una pregunta sin norma pida aclaración, es cambio de comportamiento visible; el agente no lo decide.
- **D2 — «chiquitos para su edad» (EV-011).** Se esperó respuesta con HC70 (talla para la edad); una aclaración también sería defendible.
- **D3 — diarrea «en la última semana» (EV-016).** La ENDES pregunta por 14 días. Se esperó aclaración que diga la ventana real; podría ser también «no se puede».
- **D4 — discapacidad infantil (EV-034).** `QD333_1` es solo una de las seis dificultades de la historia de nacimientos; falta decidir cuál(es) corresponde(n).
- **D5.** Las 25 preguntas sin cifra oficial no se pueden aprobar «reproduciendo la cifra publicada» (M1-19 tarea 2): quedan `propuesto` hasta que el plan se anote con los revisores del universo. Las de estratos «sin insumos», «ambiguas» y «parecen no tener insumos» son solo ejemplos: M1-19 las asigna al dueño (40 a 60 preguntas).
