# M1-05 t0 y M1-06 — `variables.parquet` antes y después, columna por columna

Generado con `m1-06_comparar_indice.py` (antes = copia guardada del archivo, sha256 `e523850f…`; después = `cc36ee41…`). Solo `clase` cambia (la llena M1-05 t0) y `bloque_id` es nueva (la escribe M1-06); las otras 26 columnas son idénticas fila por fila.

Filas: antes 2856, después 2856; mismos var_id y mismo orden: True

| Columna | Estado | Filas distintas |
|---|---|---|
| `var_id` | igual | 0 |
| `encuesta` | igual | 0 |
| `anio` | igual | 0 |
| `archivo` | igual | 0 |
| `variable` | igual | 0 |
| `posicion` | igual | 0 |
| `clase` | **cambia** | 2770 |
| `tipo_valor` | igual | 0 |
| `formato_origen` | igual | 0 |
| `rango_valido` | igual | 0 |
| `codigos_especiales` | igual | 0 |
| `rol_faltante` | igual | 0 |
| `etiqueta_original` | igual | 0 |
| `etiqueta_curada` | igual | 0 |
| `texto_pregunta` | igual | 0 |
| `universo_cuestionario` | igual | 0 |
| `ventana_referencia` | igual | 0 |
| `sujeto` | igual | 0 |
| `informante` | igual | 0 |
| `modo` | igual | 0 |
| `grupo` | igual | 0 |
| `tipo_origen` | igual | 0 |
| `universo_corto` | igual | 0 |
| `concepto_id` | igual | 0 |
| `estado` | igual | 0 |
| `derivada_de` | igual | 0 |
| `n_categorias` | igual | 0 |
| `controles` | igual | 0 |
| `bloque_id` | **nueva** | 2075 con valor |

Columnas que estaban y ya no están: ninguna

`clase` vacía antes: 2770; después: 0


---

## Segunda comparación (ronda de corrección del auditor)

Antes = el `variables.parquet` con que terminó la primera ronda (sha256 `cc36ee41…`); después = el de esta ronda. Solo cambian `clase` (regla de valores sin etiqueta y excepciones nuevas) y `bloque_id` (bloques corregidos y variables que dejaron de llevar bloque); las otras 26 columnas son idénticas. `archivos.parquet`, `categorias.parquet`, los 34 Parquet de microdatos, el manifiesto y el cubo `010ea965…`: mismo sha256 antes y después.

Filas: antes 2856, después 2856; mismos var_id y mismo orden: True

| Columna | Estado | Filas distintas |
|---|---|---|
| `var_id` | igual | 0 |
| `encuesta` | igual | 0 |
| `anio` | igual | 0 |
| `archivo` | igual | 0 |
| `variable` | igual | 0 |
| `posicion` | igual | 0 |
| `clase` | **cambia** | 140 |
| `tipo_valor` | igual | 0 |
| `formato_origen` | igual | 0 |
| `rango_valido` | igual | 0 |
| `codigos_especiales` | igual | 0 |
| `rol_faltante` | igual | 0 |
| `etiqueta_original` | igual | 0 |
| `etiqueta_curada` | igual | 0 |
| `texto_pregunta` | igual | 0 |
| `universo_cuestionario` | igual | 0 |
| `ventana_referencia` | igual | 0 |
| `sujeto` | igual | 0 |
| `informante` | igual | 0 |
| `modo` | igual | 0 |
| `grupo` | igual | 0 |
| `tipo_origen` | igual | 0 |
| `universo_corto` | igual | 0 |
| `concepto_id` | igual | 0 |
| `estado` | igual | 0 |
| `derivada_de` | igual | 0 |
| `n_categorias` | igual | 0 |
| `controles` | igual | 0 |
| `bloque_id` | **cambia** | 54 |

Columnas que estaban y ya no están: ninguna

`clase` vacía antes: 0; después: 0
