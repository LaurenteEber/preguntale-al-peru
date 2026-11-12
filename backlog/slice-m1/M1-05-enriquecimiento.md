# M1-05 — Enriquecimiento del índice

**Se deriva de** el diseño §7.2, §7.3 y §7.4.

## Tareas

0. **Clase de cada variable (va primero; M1-06 y M1-09 dependen de esto).** Hoy `clase` está vacía en 2 770 de las 2 856 variables: ninguna es `categoria` ni `medida`. Clasificarlas **solo en el índice** (regla por tipo de valor y número de categorías, más una lista curada de excepciones), sin tocar `clases_columnas.yaml` ni reconvertir: las huellas de los 34 Parquet no cambian. Informar el conteo por clase y por tabla.
1. **Campos por variable** (diseño §7.2), propuestos fuera de línea por el LLM con la Batch API y dos pasadas (redactar y verificar), sobre el texto de M1-04:
   - `universo_cuestionario` como predicados de la gramática (§11.3), a partir de los saltos;
   - `ventana_referencia`, `sujeto`, `informante`, `modo`, `universo_corto` (≤ 12 palabras) y `tipo_origen`;
   - `rol_faltante` por código especial (`faltante_excluye` o `faltante_cuenta_no`) y confirmación de los 1 082 códigos especiales propuestos en M0-05;
   - `rango_valido` de las numéricas;
   - `etiqueta_curada` para las erratas marcadas en M0-05.
   - El LLM propone; el código valida que cada predicado use variables y códigos que existen en la tabla.
2. **Control del universo contra los datos** (§7.3): el `universo_cuestionario` debe coincidir con el patrón real de valores no vacíos en ≥ 99,5 % de las filas. Lo que no llegue queda marcado para revisión, con el porcentaje.
3. **Gramática y ejecutor con faltantes:** compilar la columna `faltante` y aplicar `rol_faltante` (M0 lo dejó pendiente: supuestos M0-07 y M0-08). Con eso el ejecutor informa la tasa de no respuesta del ítem, ponderada y sin ponderar, y las compuertas aplican R-ENC-19.
4. **`cortes_estandar.yaml`:** agregar educación de la madre y lengua materna (M0 los dejó fuera), con su variable por unidad y su cita.
5. **`sinonimos.yaml`** inicial: vocabulario peruano y de programas (chispitas, posta, SIS, Qali Warma, sulfato ferroso, CRED…), con al menos los términos del conjunto de evaluación del slice 2.
6. **`no_cubre.yaml`** inicial: temas que se sabe que la ENDES no mide, cada uno con su motivo en palabras sencillas. Lo aprueba el dueño (es lo único que permite un «no puedo» por tema).
7. **`concepto_id`:** solo para las variables de las 3 recetas; las del conjunto de evaluación se completan en M1-19. Con un año basta el identificador. La armonización entre años es de M2.

## Criterios de aceptación

- [ ] Ninguna variable del índice queda sin clase; huellas de contenido de los Parquet sin cambios.
- [ ] Los campos del §7.2 llenos en `propuesto` para el lote de tablas del README.
- [ ] Informe del control del universo: cuántas variables pasan el 99,5 % y cuáles no (`evidencia/m1-05_universos.md`).
- [ ] Una receta de prueba con `rol_faltante` da la misma cifra con y sin la columna `faltante` cuando no hay faltantes, y la tasa de no respuesta sale informada.
- [ ] Las 90 filas siguen iguales.
- [ ] Costo del lote informado y dentro del tope.

## Fuera

Tablas de salud (CSALUD) y programas sociales: quedan en `propuesto` con lo que traiga el índice de M0, salvo que sobren tiempo y tope.
