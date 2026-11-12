# M0-07 — Gramática, verificador base y DuckDB endurecido

**Se deriva de** el diseño §11.2, §11.3, §12.1 y §22, y del anexo A.

## Tareas

1. **Modelos del plan** en `src/pap/inferencia/plan.py`, con pydantic y `extra="forbid"`:
   - `Plan`, `Condicion`, `Universo` y `Territorio`;
   - `Territorio.nivel` toma los niveles de `territorios.yaml`;
   - `id_plan` = sha256 del JSON canónico (claves ordenadas, sin espacios).
2. **Gramática** en `src/pap/inferencia/gramatica.py`: compila a SQL de DuckDB **con parámetros**.
   - Nombres de columna desde el índice, entre comillas dobles; valores como `?`.
   - Operadores: `en`, `entre`, `<`, `≥`, `es_nulo` y `no_es_nulo`.
   - Combinación: `una`, `alguna_de` o `todas_de`, con un máximo de 3 condiciones.
   - Arma `u`, `y`, los cortes, el territorio, el peso, el estrato y la UPM.
   - **Si `rol_faltante` está vacío (M0),** `y` es nulo solo fuera del indicador. El universo de la receta debe excluir los códigos no válidos, como hoy (HC57 en 1–4).
3. **Verificador base** en `src/pap/inferencia/verificador.py`, con lo necesario para las recetas; el resto del §12.1 va en M1:
   - las variables y categorías existen en el año. **Dentro de una receta se aceptan variables `propuesto`** (diseño §12.1);
   - agrega el universo analítico, el diseño y el territorio desde las tablas curadas;
   - regla del peso de la submuestra más restrictiva;
   - *left join* hacia la unidad, con sus controles (filas de `u` antes y después, suma de pesos, conglomerados y estratos);
   - un nivel fuera de `inferencia_verificada` sube al que lo contiene (R-ENC-06);
   - `dominios_max_llamada` y `anios_apilados_max_llamada`.

   Devuelve el plan completo o una `Falla(tipo, dimension, motivo)`.
4. **DuckDB endurecido** en `src/pap/inferencia/duckdb_seguro.py`, en el orden del §22: `allowed_directories` **antes** de `enable_external_access=false`, porque al revés DuckDB da error.
5. **`curados/inferencia/parametros.yaml`** con los valores del anexo B que use M0.
6. **Pruebas:**
   - planes válidos e inválidos;
   - **cadenas maliciosas** en cada campo (`UNION SELECT`, `read_text`, `COPY`, `;`, comillas), que deben ser rechazadas o quedar como valor inerte;
   - con la conexión endurecida, `read_text('/etc/hosts')`, `COPY … TO` y la lectura fuera de los directorios permitidos fallan, y la lectura de los Parquet funciona;
   - `.arrow()` devuelve un `RecordBatchReader` que `pl.from_arrow` acepta.

## Criterios de aceptación

- [ ] Pruebas de gramática y de seguridad en verde.
- [ ] El verificador completa el plan de las 3 recetas con el diseño, el universo y los territorios de M0-06.
- [ ] Ningún SQL se arma con texto que no venga del índice.

## Fuera

Planificador, huellas `u,y` y decisión 1 (M1).
