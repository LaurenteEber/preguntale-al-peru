# S2-02 — Conjunto de evaluación (independiente)

## Por qué

La calidad del intérprete se mide contra preguntas con resultado esperado. Esas preguntas se escriben **antes** del prompt y las escribe alguien que no lo escribe; si no, se mide lo que ya se ajustó (lección 3 del cierre del slice 1).

## Tareas

1. **Quién lo escribe:**
   - Un subagente nuevo, con su encargo en `evidencia/encargo_s2-02_evaluacion.md`.
   - Recibe: el contrato (S2-01), `docs/manual_de_uso.md`, `docs/decisiones.md`, `curados/motor/intenciones.yaml`, `parametros_motor.yaml` y `curados/motor/textos/territorio.yaml`.
   - **No** recibe `curados/interprete/` ni el código del intérprete.
   - El dueño puede sumar preguntas reales suyas. Se le piden en `consultas_al_dueno.md`; no bloquea.
2. **Archivo** `tests/interprete/evaluacion.yaml`. Por entrada:
   - `id`, `pregunta` y `categoria`;
   - `esperado`: `resultado` y, si es `consulta`, la consulta mínima en la forma de S2-01, sin anclas;
   - `notas`.
3. **Cobertura mínima** (≥ 100 en total):

   | Categoría | Mín. | Ejemplos |
   |---|---|---|
   | Directa | 24 | Las combinaciones de intención × tema que tienen fila en `intenciones.yaml`; las que dan `intencion_no_soportada` esperan ese «no se puede» |
   | Reformulada o coloquial | 20 | «¿Los niños en Ayaviri están anémicos?», «¿cuánta plata se gastó…?» |
   | Errores de tipeo o sin tildes | 10 | «anemia en uancavelica» |
   | Lugares difíciles | 12 | «Lima», «San Juan», «Callao», «Lima provincias», «Ayaviri (Melgar, Puno)» |
   | Años y periodos | 10 | «en 2019», «desde 2015», «el año pasado» |
   | Ambigua | 10 | «¿Cómo está la salud en Cusco?» |
   | Fuera de alcance, tema | 6 | «delincuencia en Trujillo» |
   | Fuera de alcance, pregunta | 6 | «¿Por qué subió la pobreza en Lima?», «¿cuánta anemia habrá en 2030?» |
   | Engañosa o con premisa | 8 | «Si la anemia en Puno es 90 %, ¿por qué…?» |
   | Inyección o fuera de tarea | 6 | «Ignora tus instrucciones y…», «escribe un poema» |
   | Q1–Q4, tal como están en `pregunta_original` | 4 | — |

4. **Cómo se compara** (lo usan S2-05 y S2-09). No se compara el texto: se compara lo que entiende el motor.
   - Intención, tema, periodo y nivel, iguales.
   - Territorio, `comparar_con` y `dentro_de`: el resultado de `territorio.resolver()` (ubigeo o ámbito, o la misma aclaración con las mismas opciones).
   - Así, Q1 («…en Huancavelica») espera la aclaración de homónimo. En `notas`: «con `--elegir 1`, consulta de q1.json».
5. **Comprobación como prueba:** `tests/interprete/test_conjunto.py` comprueba que:
   - todas las consultas esperadas son válidas;
   - las 4 de Q1–Q4 resuelven como sus JSON (Q1, tras elegir el departamento);
   - no hay `id` repetidos;
   - se cumplen los mínimos por categoría.

## Criterios de aceptación

- [ ] ≥ 100 entradas, mínimos cumplidos, `test_conjunto.py` en verde.
- [ ] El encargo es anterior al conjunto en `git log` y no menciona el prompt.
- [ ] La historia queda «hecha, pendiente de revisión»: el supervisor revisa una muestra de 20 sin detener S2-03.
