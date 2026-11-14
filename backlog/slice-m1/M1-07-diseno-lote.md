# M1-07 — Diseño muestral y universos de niño, mujer y hogar; lote a `revisado`

**Se deriva de** el diseño §7.4, §12.1 y §26.4.

## Contexto

Hoy `diseno_muestral.csv` tiene 7 filas, de 6 tablas. Sin esa fila, el verificador no puede estimar nada de una tabla. Para que el planificador responda sobre niño, mujer y hogar hacen falta el diseño y los universos de esas tablas.

## Tareas

1. **Lote de tablas de M1:** el del README («Lote de tablas»). Quedan fuera: REC82 (calendario), REC83 (hermanos), REC84DV y REC93DVdisciplina (violencia y disciplina: submuestras y reglas propias), RECHM, CSALUD y programas sociales. Se anota por qué en la ficha de cada una.
2. **Unidad, tabla base y peso.** Las unidades del índice (`persona_del_hogar`, `hijo_de_mujer`, `mujer`, `hogar`) no son las del plan (`nino`, `mujer`, `hogar`, `persona`). Escribir la tabla curada `curados/inferencia/unidades.yaml`: por cada tabla del lote, la unidad del plan, su tabla base y de dónde sale su peso. El verificador elige el universo y el diseño **por la tabla que interviene,** no por el primer archivo de la unidad (hoy `_universo_analitico` toma `aplica_a.archivos[0]`).
   - **`diseno_muestral.csv`:** una fila por tabla y medición del lote, con peso, estrato, UPM, `nivel_submuestra`, uniones para el diseño y **cita a la ficha técnica** (página). Las tablas del cuestionario individual usan el peso de la mujer (V005) vía REC0111.
   - **RECH5** (peso, talla y hemoglobina de mujeres) es del cuestionario del hogar: qué peso le corresponde se resuelve con la ficha técnica; si la ficha no lo dice, es consulta (tipo C) y RECH5 sale del lote.
3. **`universos_analiticos.yaml`:** las convenciones del INEI que falten, con su fuente (ficha técnica, informe del INEI o DHS-Indicators-R como referencia de método):
   - `mujer_15_49_entrevistada` y `mujer_12_49_entrevistada` (la ficha 2024 habla de 12 a 49);
   - `nino_hijo_de_entrevistada` (nacidos en los últimos 5 años, vivos, según el indicador);
   - `persona_de_hecho` y `hogar`.
4. **Uniones entre unidades** en `archivos_endes_2024.yaml`: hijo de mujer → mujer → hogar ya están; declarar las que falten para llevar cortes del hogar (área, región, quintil) y de la madre (educación, lengua) a las tablas del niño. En particular, REC41, REC43, REC44, REC94 y REC95 con REC21 por CASEID y el índice del nacimiento (= BIDX), para el sexo y la edad del niño; cada una se comprueba sin pérdidas.
5. **`mediciones.yaml`** (M1-03) completa para el lote.
6. **Tres controles de prueba,** para comprobar el diseño de la mujer y del hijo de la entrevistada contra cifras oficiales de 2024. Son recetas que viven en `tests/inferencia/recetas_control/`: **no entran a `dim_indicador`, no responden preguntas y no se marcan `verificado`.** Convertir alguna en indicador es una consulta al dueño. Las elige el agente entre indicadores del informe de programas presupuestales que quepan en la gramática actual (hasta 3 condiciones, sin transformaciones), al menos uno por diseño: mujer e hijo de la entrevistada. Parto institucional (REC41) **no cabe** (necesita una condición dentro de otra; resolución del dueño del 13/11/2026: va al backlog de M2); lactancia exclusiva y vacunas completas no caben y quedan fuera. Como no están en `dim_indicador`, se cargan por un camino de prueba que no pasa por `validar-recetas`; cada una con su cifra oficial nacional y por área, y la cita del cuadro. Deben reproducirla (±0,1 pp).
7. **Revisión del auditor-agente,** fila por fila, de las tablas curadas nuevas (`evidencia/m1-07_revision.md`).
8. **Lote a `revisado`:** con la revisión en verde, el agente arma el lote (variables del índice, fichas y bloques de estas tablas) para el visto del dueño. Sin el visto, todo sigue en `propuesto` y las historias de la etapa C se prueban con ese estado detrás del parámetro `inferencia.admitir_propuesto_en_sombra` de `curados/inferencia/parametros.yaml` (solo válido con `motor.version` distinto de `nuevo`; el código lo rechaza en otro caso).

## Criterios de aceptación

- [x] `pap inferencia validar-tablas` sale con 0; cada fila nueva con su cita y su página.
- [x] Un plan de prueba por cada tabla del lote pasa el verificador y calcula.
- [x] Los 3 controles reproducen su cifra oficial; si alguno no reproduce, es consulta.
- [x] El peso al unir tablas sigue la regla de la submuestra más restrictiva (prueba con niño × madre × hogar).
- [ ] Lote entregado al dueño con un resumen en sencillo: cuántas variables, qué controles saltaron y qué dudas quedan. — pendiente: el resumen está en `evidencia/m1-07_lote.txt`, pero falta el visto del dueño al lote (y C-M1-07-1)

## Fuera

Violencia, disciplina infantil, salud de adultos y programas sociales.
