# M0-07 — Gramática, verificador base y DuckDB endurecido: evidencia

Código: `src/pap/inferencia/{plan,gramatica,verificador,duckdb_seguro}.py`. Parámetros: `curados/inferencia/parametros.yaml` (`verificador.*`, `duckdb.*`). Pruebas: `tests/inferencia/test_{plan_gramatica,verificador,duckdb_seguro,verificador_microdatos}.py` (217 pruebas nuevas; los planes de las 3 recetas están en `tests/inferencia/recetas_m0.py`, los YAML de recetas son de M0-10).

## SQL compilado de las 3 recetas (nivel `departamento`)

Una sola consulta con `u`, `y`, `territorio`, `peso`, `estrato` y `upm` (más `corte_<id>` si el plan trae cortes). Los nombres vienen del índice, entre comillas dobles; todo valor, incluidos los textos de las expresiones curadas y la ruta de cada Parquet, va como `?`.

**Anemia (criterio anterior, HC57 en 1–3)** — `id_plan` `a16ef601…`
```sql
SELECT u, CASE WHEN u THEN CAST(ind AS INTEGER) END AS y, territorio, peso, estrato, upm
FROM (SELECT COALESCE(("RECH1"."HV103" IN (?)) AND ("RECH6"."HC1" BETWEEN ? AND ?) AND ("RECH6"."HC57" IN (?, ?, ?, ?)), FALSE) AS u,
  "RECH6"."HC57" IN (?, ?, ?) AS ind,
  CASE WHEN "RECH0"."HV024" <> 7 THEN printf(?, "RECH0"."HV024") END AS territorio,
  ("RECH0"."HV005"/1e6) AS peso,
  printf(?, "RECH0"."HV024", "RECH0"."HV022") AS estrato,
  "RECH0"."HV021" AS upm
FROM read_parquet(?) AS "RECH6"
LEFT JOIN read_parquet(?) AS "RECH0" ON "RECH6"."HHID" = "RECH0"."HHID"
LEFT JOIN read_parquet(?) AS "RECH1" ON "RECH6"."HHID" = "RECH1"."HHID" AND "RECH6"."HC0" = "RECH1"."HVIDX")
-- parámetros: [1, 6, 35, 1, 2, 3, 4, 1, 2, 3, '%02d', '%02d-%d', '…/RECH6.parquet', '…/RECH0.parquet', '…/RECH1.parquet']
```

**Anemia OMS 2024 (HC57A)** — `id_plan` `72eac51f…`: igual, con `"RECH6"."HC57A"` en lugar de `"RECH6"."HC57"` (mismos parámetros).

**DCI (HC70 < −200)** — `id_plan` `38e5b079…`
```sql
SELECT u, CASE WHEN u THEN CAST(ind AS INTEGER) END AS y, territorio, peso, estrato, upm
FROM (SELECT COALESCE(("RECH1"."HV103" IN (?)) AND ("RECH6"."HC1" BETWEEN ? AND ?) AND ("RECH6"."HC70" BETWEEN ? AND ?), FALSE) AS u,
  "RECH6"."HC70" < ? AS ind,
  CASE WHEN "RECH0"."HV024" <> 7 THEN printf(?, "RECH0"."HV024") END AS territorio,
  ("RECH0"."HV005"/1e6) AS peso,
  printf(?, "RECH0"."HV024", "RECH0"."HV022") AS estrato,
  "RECH0"."HV021" AS upm
FROM read_parquet(?) AS "RECH6" ... (mismas uniones)
-- parámetros: [1, 0, 59, -9989, 9989, -200, '%02d', '%02d-%d', '…/RECH6.parquet', '…/RECH0.parquet', '…/RECH1.parquet']
```

- `u` = universo analítico `nino_hecho` (HV103 = 1) + restricciones de la receta; un nulo no cumple (`COALESCE(…, FALSE)`).
- `y` = 0/1 dentro de `u`, nulo fuera. Con `rol_faltante` vacío (M0) no hay códigos que salgan del denominador: el universo de la receta excluye los inválidos (HC57 en 1–4; HC70 de −9 989 a 9 989) y un nulo dentro de `u` es falla (`y_nulos_en_u`).
- Universo, diseño (RECH6 medición: `HV005/1e6`, estrato `HV024`×`HV022`, UPM `HV021`) y territorio los agrega el verificador desde `universos_analiticos.yaml`, `diseno_muestral.csv` y `territorios.yaml`.

## Controles de las uniones que devuelve el verificador (ENDES 2024, real)

Uniones: `RECH6→RECH0` (HHID) y `RECH6→RECH1` (HHID, HC0=HVIDX). Mismos valores en los 6 niveles de territorio:

| Plan | filas RECH6 | filas tras uniones | `u` antes | `u` después | pérdida | suma de pesos en `u` | conglomerados | estratos | `y` nulos en `u` | diseño nulo en `u` |
|---|---|---|---|---|---|---|---|---|---|---|
| anemia | 20 290 | 20 290 | 9 959 | 9 959 | 0 | 3 248,37 | 3 080 | 240 | 0 | 0 |
| anemia OMS 2024 | 20 290 | 20 290 | 9 959 | 9 959 | 0 | 3 248,37 | 3 080 | 240 | 0 | 0 |
| DCI | 20 290 | 20 290 | 19 511 | 19 511 | 0 | 6 384,31 | 3 226 | 240 | 0 | 0 |

`u` = 9 959 / 9 959 / 19 511: coincide con M0-06. Unidades de territorio por receta: nacional 1, dominio_subnacional 2, departamento 24, CALLAO 1, LIMA_METROPOLITANA 1, LIMA_REGION 1 = **30**. Los 6 niveles están verificados en `catalogo/inferencia_verificada.csv` (ENDES 2024: `nivel_maximo` departamento; ámbitos LIMA_METROPOLITANA y LIMA_REGION), así que ningún plan sube de nivel.

## Pruebas de seguridad

Resultado: todas en verde (217 pruebas nuevas en `tests/inferencia/`; 44 con `regresion_microdatos` + `solo_mac` en todo el repo).

- **Cadenas maliciosas en cada campo del plan** (`test_plan_gramatica.py`): 7 cadenas (`x' UNION SELECT 1 --`, `read_text('/etc/hosts')`, `COPY t TO '/tmp/x'`, `a; DROP TABLE t`, `a"b`, `a'b`, `1 OR 1=1`) × 16 campos (encuesta, años, unidad, medida, receta_id, origen, territorio.nivel, territorio.id, cortes, combinar, `var`/`op`/`valores` del indicador y de las restricciones): todas se rechazan al validar el plan.
- Un `var_id` con forma válida pero fuera del índice (`…UNION_SELECT`, `…read_text`, `…COPY_t`, `…OR_1_1`) queda inerte: falla `variable` y no se compila nada.
- **Expresiones curadas:** `read_text(…)`, `;`, `--`, `/* */`, subconsulta, `UNION`, `||`, función ajena, columna fuera del índice y comilla doble se rechazan; un texto entre comillas con SQL dentro (`'1; DROP TABLE x; --'`) pasa a ser solo un parámetro.
- **Ningún SQL con texto que no venga del índice:** para planes de las recetas (sintéticos y reales) los nombres entre comillas ⊂ archivos y columnas del índice, `identificadores` ⊂ `(archivo, variable)` del índice de 2024, no hay `'`, `;` ni `--`, `?` = número de parámetros, y los únicos números escritos son los de las expresiones curadas (nunca los del plan). Cada operador compila a su forma con el valor como `?`.
- **Conexión endurecida** (`test_duckdb_seguro.py`): fallan `read_text('/etc/hosts')`, `read_csv`, `read_blob`, `glob('/etc/*')`, `COPY … TO` fuera de las carpetas permitidas, `read_parquet`/`read_text` fuera de ellas, `ATTACH`, `INSTALL`, `LOAD`, `EXPORT DATABASE`; `SET enable_external_access=true`, `SET allowed_directories=['/']`, `threads`, `memory_limit`, `autoload…` y `lock_configuration=false` fallan (configuración bloqueada). La lectura de los Parquet de las carpetas permitidas funciona (sintéticos y los reales de ENDES 2024). Con la conexión por defecto solo se leen `biblioteca/microdatos` y `biblioteca/variables`. Al revés (apagar el acceso antes de fijar `allowed_directories`) DuckDB da error: probado.
- **`.arrow()`** devuelve `pyarrow.RecordBatchReader` en DuckDB 1.5 y `pl.from_arrow` lo acepta (no hizo falta `fetch_record_batch`, que en 1.5 está en desuso).
- **Límite conocido:** `allowed_directories` permite también escribir dentro de las carpetas permitidas; un `COPY … TO` hacia ellas no falla. No existe vía para pedirlo (el plan no lleva SQL); ver «Supuestos aplicados» (M0-07) en `consultas_al_dueno.md`.

## Criterios de aceptación

- [x] Pruebas de gramática y de seguridad en verde.
- [x] El verificador completa el plan de las 3 recetas con el diseño, el universo y los territorios de M0-06 (`test_el_verificador_completa_las_recetas_con_diseno_universo_y_los_30_territorios`).
- [x] Ningún SQL se arma con texto que no venga del índice.
