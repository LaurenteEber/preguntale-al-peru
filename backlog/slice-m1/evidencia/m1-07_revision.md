# M1-07 — Revisión del auditor-agente (tarea 7)

Revisado el 13/11/2026 por el auditor-agente, sobre los cambios sin confirmar de la rama `slice-m1` (implementación de M1-07). Solo lectura: no se tocó ninguna tabla, dato ni prueba; este archivo es lo único que se escribió.

**Veredicto: «aprobado con observaciones».** Las cifras, los pesos de las tablas de la mujer y del hijo, las uniones nuevas y el cambio del verificador están bien, y las tres recetas siguen iguales al cubo. Hay una página mal citada (Cuadro N.º 24), dos afirmaciones sobre universos que los datos desmienten y dos supuestos que en realidad deciden un peso o un universo, así que le tocan al dueño. **Hay que corregir los hallazgos 1 a 4 (o pasarlos a consulta) antes de que el lote suba a `revisado`.**

## Qué se hizo para revisar

- Se leyeron la historia, la evidencia (`m1-07.md` y los `m1-07_*`), los supuestos M1-07-s1 a s10, la consulta C-M1-07-1, el `git diff` y los archivos nuevos (`unidades.yaml`, `diseno_muestral.csv`, `universos_analiticos.yaml`, `archivos_endes_2024.yaml`, `mediciones.yaml`, `fichas/ENDES.yaml`, `verificador.py`, `tablas_curadas.py`, las pruebas `test_m107_*` y `recetas_control/`).
- Se leyeron con `pdftotext -layout` los PDF registrados: la ficha técnica 2024 (`endes-2024-ficha-tecnica`, huella `ad40972d…`, pp. 2, 8, 9, 11 y 20) y el informe de programas presupuestales 2024 (`endes-2024-informe-ppr`, huella `c40ffb3f…`; el número impreso de página es el del PDF menos 2).
- Consultas propias en duckdb sobre los Parquet de 2024, escritas desde cero (sin usar los scripts del implementador): los tres controles, las uniones nuevas, las cardinalidades, los niños fallecidos y la desnutrición de REC44 con los dos pesos.
- `uv run pap inferencia validar-tablas` → salida 0, las 8 tablas con cita (22 filas de diseño, 14 universos, 18 unidades).
- `uv run pap inferencia receta <id> --anio 2024 --comparar-cubo` para `endes_anemia_6_35m`, `endes_anemia_6_35m_oms2024` y `endes_dci_menores_5` → salida 0 en las tres: 30 de 30 filas con diferencia 0, 0 estados distintos y doradas 9/9, 9/9 y 3/3.
- `uv run pytest -q` de `test_m107_verificador.py`, `test_m107_tablas.py`, `test_m107_controles.py`, `test_m107_microdatos.py`, `test_verificador.py` y `test_tablas_curadas.py` → **140 passed**.
- Cuatro planes de prueba propios con el verificador (ver los hallazgos 3 y 5).

## Revisión fila por fila

### Citas contra los PDF

| Cita | ¿Dice eso? |
|---|---|
| Ficha p. 2 «Los hogares particulares y sus miembros…», «Todas las mujeres de 12 a 49 años de edad y niños menores de 5 años» | Sí |
| Ficha §5.2 p. 8 «a todas las mujeres elegibles, es decir, de 12 a 49 años» | Sí |
| Ficha p. 9: cuestionario del hogar (miembros; antropometría y hemoglobina de niños **y de mujeres de 12 a 49 años**), cuestionario individual (incluido DIT de 9 a 71 meses) | Sí |
| Ficha §VI p. 11: factor hogar HV005 («relacionados al hogar, desnutrición y anemia en menores de 5 años», RECH0); factor mujer V005 («planificación familiar…, parto institucional…, control prenatal, entre otros», REC0111) | Sí, literal |
| Ficha p. 20, #21: planificación familiar de mujeres de 15 a 49 años | Sí |
| Informe, Cuadro N.º 1 p. 41 y N.º 2 p. 43: 34 018 hogares (urbana 22 099, rural 11 919) | Sí (PDF 43 y 45) |
| Informe, Cuadro N.º 04 p. 49: desnutrición crónica 12,1 % | Sí (PDF 51; 19 511 casos) |
| Informe, Cuadro N.º 23 p. 91: 77,5 / 77,0 / 79,5; 19 764 / 13 115 / 6 649 | Sí (PDF 93) |
| **Informe, Cuadro N.º 24 «p. 93 (PDF 95)»** | **No: la p. 93 es el Cuadro N.º 23.1. El N.º 24 está en la p. 95 (PDF 97)**; las cifras 58,1 / 59,1 / 54,7 y los casos sí coinciden (hallazgo 1) |
| Informe, Cuadro N.º 27 p. 101: 93,5 / 97,8 / 81,1; 17 594 | Sí (PDF 103) |
| Informe, Cuadro N.º 29 p. 105: 38,2 / 44,4 / 21,0; 19 737 / 13 845 / 5 892 | Sí (PDF 107) |

### `diseno_muestral.csv` (15 filas nuevas) y `unidades.yaml` (18 filas)

- **Tablas de la mujer** (REC0111, REC91, RE223132, REC42, RE516171, RE758081) y **del hijo de la entrevistada** (REC21, REC41, REC43, REC94, REC95, DIT): peso V005/1e6 tomado de REC0111 por CASEID, estrato V024 × V022 y conglomerado V021, igual que la fila de REC0111 que ya existía. La ficha p. 11 lo sustenta, y además nombra el parto institucional y el control prenatal, que son indicadores de los nacimientos: el hijo usa el peso de su madre. **Correcto.**
- **RECH0 y RECH23**: HV005, como ya estaba. **RECH1 y RECH4** (M1-07-s1): HV005. La ficha no nombra a los miembros del hogar, pero es la convención de la DHS para las personas del hogar. **Razonable** (hallazgo 4, baja).
- **RECH6**: sin cambios. **REC44** (M1-07-s2): HV005 con submuestra de medición (hallazgo 4).
- `validar-tablas` comprueba que el peso de `unidades.yaml` coincida con el de `diseno_muestral.csv` y con la unidad del índice. Los 18 pesos coinciden.

### `universos_analiticos.yaml` (8 universos nuevos)

- `hogar` (HV015 = 1): da exactamente los 34 018 hogares del informe (lo medí). **Correcto.**
- `persona_de_hecho` (HV103 = 1): es el criterio de la población de hecho de la ficha y de la DHS. **Correcto.**
- `mujer_12_49_entrevistada` / `mujer_15_49_entrevistada` (V015 = 1): 34 252 mujeres. El de 15 a 49 reproduce los 19 764 casos del Cuadro N.º 23. **Correcto.** Que el universo por defecto sea el de 12 a 49 es una decisión (hallazgo 4).
- `nino_hijo_de_entrevistada` y `_15_49`: los 60 693 nacimientos de REC21 son de madres con V015 = 1 (lo medí), y el de 15 a 49 da los 19 737 del Cuadro N.º 29. **Correcto para la cesárea**, pero la nota dice que esos nacimientos son «vivos», y no lo son todos (hallazgo 2); además, REC21 no es una tabla de niños (hallazgo 3).
- `…_hb_medida` y `…_talla` (REC44): repiten el criterio de RECH6 (HW55 = 0; HW1 de 0 a 59 meses y HW70 válida). **Correcto**, salvo lo que cubren (hallazgo 5).

### `archivos_endes_2024.yaml` (uniones nuevas)

- REC41, REC43, REC44, REC94 y REC95 → REC21 por CASEID y MIDX / HIDX / HWIDX / IDX94 / IDX95 = BIDX: cada una tiene 19 751 de 19 751 filas con pareja. DIT, 19 245. REC21 no repite (CASEID, BIDX): 60 693 filas, 60 693 distintas. La cardinalidad `1:0..1` es correcta.
- RECH4 → RECH1 (HHID, IDXH4 = HVIDX): 135 045 filas con pareja y sin repetir, `1:1`. REC91 → REC0111: 37 117 filas con 37 117 CASEID distintos, `1:1`. **Correcto.** Las uniones no pierden filas, y `comprobar_cardinalidades` sale vacío en la prueba.

### `mediciones.yaml` (2 filas nuevas)

Hemoglobina y talla de REC44, con las mismas baterías y exclusiones que RECH6. **Correcto.**

### Verificador

- El universo y la tabla base se eligen ahora **por la tabla del plan** que es de la unidad (`_tablas_de_la_unidad`, `_tabla_base`), y el plan falla si ninguna tabla es de la unidad. Si el plan no usa ninguna tabla del lote, se conserva el comportamiento anterior.
- El peso sale de la submuestra más restrictiva (medición > individual > hogar), y dos tablas individuales con pesos distintos hacen fallar el plan. Lo prueban `test_m107_verificador.py` (niño × madre × hogar) y los controles: el diseño queda «individual, V005, V021».
- Un corte se ofrece solo si describe a la unidad del plan o al hogar (`corte_aplica`).
- **Las tres recetas no cambian** (`--comparar-cubo` en 0, ver arriba). **Correcto.**

### Los tres controles

Los reproduje con una consulta propia (peso V005, V015 = 1, V012 de 15 a 49 y V502 = 1 donde corresponde):

| Control | Nacional | Urbana | Rural |
|---|---|---|---|
| Algún método | 77,54 (19 764) | 77,00 (13 115) | 79,46 (6 649) |
| Método moderno | 58,10 | 59,07 | 54,70 |
| Cesárea | 38,18 (19 737) | 44,36 (13 845) | 20,99 (5 892) |

Las nueve cifras quedan a menos de 0,1 pp de las publicadas y los casos coinciden exactos. Ningún control está en `dim_indicador` ni en `curados/inferencia/recetas/`; todos son `propuesto` y sin `verificado`. **Correcto**, salvo la página del Cuadro N.º 24 (hallazgo 1).

### Las 1 170 variables `categoria` que fallan por «nulo dentro del universo»

**No es un defecto de las tablas de M1-07; es lo esperado.** Hay dos causas:
- los saltos del cuestionario (la pregunta solo se hace a una parte del universo);
- en las tablas del hijo, los **169 niños fallecidos** de los 19 751 nacimientos, que no tienen respuesta en salud, vacunas ni desarrollo infantil. Por eso REC43 y REC95 pasan 0 de 129 y 0 de 99.

El control de nulos cumple su función: impide calcular sobre un denominador mal definido. **Sí conviene avisar al dueño** (hallazgo 6): la salida que propone la evidencia («agregar la restricción respondió») no es neutra.

### C-M1-07-1 (peso de RECH5)

**Bien planteada.** La ficha p. 9 pone la medición de las mujeres de 12 a 49 años dentro del cuestionario del hogar, y la p. 11 da el factor hogar solo a «desnutrición y anemia en menores de 5 años». Busqué en el informe de programas presupuestales y no hay ningún cuadro de anemia o antropometría de mujeres que sirva de control. Elegir el peso cambia la cifra, así que es tipo C. Sacar RECH5 del lote es la decisión prudente.

## Hallazgos

1. **Media — página mal citada del Cuadro N.º 24.**
   - Dónde: `tests/inferencia/recetas_control/control_pf_moderno.yaml:35,47,58`, `tests/inferencia/test_m107_controles.py:22` (la prueba fija la página errónea), `backlog/slice-m1/evidencia/m1-07.md:51` y el supuesto M1-07-s9 de `consultas_al_dueno.md`.
   - Qué pasa: se cita «Cuadro N.º 24 p. 93 (PDF 95)». La p. 93 es el Cuadro N.º 23.1 (métodos según la norma técnica, 68,1 %). El N.º 24 está en la **p. 95 (PDF 97)**. Las cifras y los casos sí son los del N.º 24.
   - Propuesta: corregir a «p. 95 (PDF 97)» en los cinco lugares.
2. **Media — los nacimientos de REC41, REC43, REC44, REC94 y REC95 no son todos «vivos».**
   - Dónde: `curados/inferencia/universos_analiticos.yaml:15-16` (cabecera) y la fuente de `nino_hijo_de_entrevistada`; el supuesto M1-07-s3.
   - Qué pasa: 169 de los 19 751 nacimientos tienen B5 = 0 en REC21 (fallecidos). Para la cesárea es lo correcto: el INEI cuenta los 19 737 nacimientos con los fallecidos. En cambio, los indicadores de niños vivos (vacunas, IRA/EDA, lactancia, DIT) necesitan B5 = 1, y el lote no lo dice.
   - Propuesta:
     - corregir el texto («últimos 5 años, vivos o fallecidos»);
     - agregar un universo `nino_vivo_hijo_de_entrevistada` (B5 = 1, por la unión con REC21), que la etapa C pueda elegir.
     - Es un universo, así que es tipo C: consultar al dueño.
3. **Media — REC21 entra como tabla «niño», pero tiene a todos los hijos nacidos de la mujer.**
   - Dónde: `curados/inferencia/unidades.yaml` (fila de REC21) y `universos_analiticos.yaml` (`nino_hijo_de_entrevistada`).
   - Qué pasa: de los 60 693 nacimientos de REC21, 39 557 tienen 5 años o más y 1 551 fallecieron. Un plan de prueba propio («proporción de niños varones», B4 de REC21) **pasa el verificador** con el universo `nino_hijo_de_entrevistada`, la tabla base REC21 y u = 60 693: respondería sobre todos los hijos que la mujer tuvo alguna vez como si fueran niños.
   - Propuesta: hay dos caminos.
     - Que REC21 sirva solo de puente (para llevar el sexo y la edad del niño a las demás tablas) y no pueda ser la tabla base de un plan de la unidad `nino`.
     - O darle a REC21 un universo propio de los nacidos en los últimos 5 años (B19 < 60).
   - Es tipo C: consultar al dueño.
4. **Media — M1-07-s2 y la parte de M1-07-s3 sobre el universo por defecto deciden un peso o un universo: son tipo C, no supuestos.**
   - Dónde: `consultas_al_dueno.md` (supuestos M1-07-s2 y s3), `diseno_muestral.csv` (filas de REC44) y `universos_analiticos.yaml` (universos de la mujer).
   - Qué pasa con REC44: la ficha sí da HV005 a «desnutrición y anemia en menores de 5 años», así que la elección es razonable. Pero la prueba que la respalda es débil: se compara 12,12 % de REC44 (18 930 niños, sin pernocte) con el 12,1 % del informe, que sale de RECH6 (19 511 niños). Son poblaciones distintas; lo confirmé (12,12 % con HV005 y 11,67 % con V005). Además, es el mismo tipo de vacío que llevó RECH5 a consulta.
   - Qué pasa con la mujer: el universo por defecto (12 a 49 años) hace que cualquier plan sobre mujeres incluya a las niñas de 12 a 14 años. El INEI publica casi todo para mujeres de 15 a 49.
   - Propuesta: abrir C-M1-07-2 (peso de REC44: HV005, como se propone) y C-M1-07-3 (universo por defecto de la mujer: 15 a 49, propuesta del auditor), y que el dueño decida antes de dar el visto al lote.
   - M1-07-s1 (HV005 para RECH1 y RECH4) es la convención de la DHS: **baja**; basta con mencionarlo en el visto.
5. **Baja — los universos de medición de REC44 solo cubren REC44 y REC0111.**
   - Dónde: `universos_analiticos.yaml`, `aplica_a` de `nino_hijo_de_entrevistada_hb_medida` y de `_talla`.
   - Qué pasa: un plan propio (anemia de REC44 con una restricción de REC41) pierde el predicado HW55 = 0, cae al universo general y falla con «212 filas de u con y nulo». Hoy falla de forma segura, pero no puede calcularse.
   - Propuesta: agregar REC21, REC41, REC43, REC94, REC95 y DIT al `aplica_a` de esos dos universos.
6. **Media (para el dueño) — la restricción «respondió» cambia el denominador.**
   - Dónde: `backlog/slice-m1/evidencia/m1-07.md`, «Qué controles saltaron».
   - Qué pasa: la evidencia propone que el planificador agregue `no_es_nulo` para las 1 170 variables con saltos de cuestionario. Eso decide quién entra al denominador; el INEI a veces deja «no sabe» o «sin información» dentro. Aplicarlo en automático puede mover cifras.
   - Propuesta: anotarlo como consulta para la etapa C, para que la restricción salga de la ficha o del universo de la pregunta y no se agregue a ciegas.
7. **Baja — una prueba dice comprobar que no hay repetidos, pero no lo comprueba.**
   - Dónde: `tests/inferencia/test_m107_microdatos.py:116`.
   - Qué pasa: compara solo `count(*)` (`[0]`), no el conteo de llaves distintas. Lo medí aparte y no hay repetidos (60 693 = 60 693).
   - Propuesta: comparar `fetchone() == (60693, 60693)`.
8. **Baja — dice «no se une» donde debería decir «no se declara».**
   - Dónde: `universos_analiticos.yaml:187-188` y el supuesto M1-07-s2.
   - Qué pasa: se afirma que REC44 «no se une a la fila del niño en RECH1». Sí podría unirse por REC21.B16 = HVIDX, con la salvedad de B16 = 0 (M1-06-s8), y eso traería el pernocte.
   - Propuesta: reformular como «no se declara hoy» y dejar la posibilidad para M2.
9. **Baja — dos asuntos de proceso.**
   - Dónde: `archivos.parquet` del índice y `archivos_endes_2024.yaml`.
   - Qué pasa con el índice: la columna `relaciones` de `archivos.parquet` se editó en el sitio, fuera de `pap variables indexar`. Una prueba confirma que queda igual a lo que daría la reindexación, pero conviene reindexar (y volver a aplicar los vínculos de M1-04) apenas termine el lote en vivo, como dice la evidencia.
   - Qué pasa con las uniones: que «los caminos cortos no cambien» depende del orden de las líneas de `relaciones`. Es frágil; conviene que M2 elija el camino por una regla explícita y no por el orden.

## Lo que no se verificó

- La suite completa (`uv run pytest -q`). Se corrieron solo las 140 pruebas enfocadas; la evidencia del implementador dice 2153 pasadas.
- Si hay una cifra oficial de anemia de mujeres en otros informes del INEI (el informe principal de la ENDES no está entre los recursos registrados que revisé).
