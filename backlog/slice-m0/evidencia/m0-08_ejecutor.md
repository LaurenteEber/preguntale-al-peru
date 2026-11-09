# M0-08 — Ejecutor: pool y adaptador de `svy`: evidencia

Código: `src/pap/inferencia/{estimacion,svy_adaptador,ejecutor}.py`. Parámetros: `curados/inferencia/parametros.yaml` (`ejecutor.*`). Pruebas: `tests/inferencia/test_{svy_adaptador,ejecutor,pool_ejecutor,ejecutor_microdatos}.py` (49 nuevas). Tiempos: `m0-08_tiempos.md` (se regenera con `uv run python tests/inferencia/medir_tiempos_m08.py 30`).

## Equivalencia con `calculo._svy_niveles` (anemia 2024, `endes_nino.parquet` en solo lectura)

Nacional (1), por área (2) y por departamento (24): 27 filas, por el ejecutor en el proceso y por el pool. **Máxima |dif| = 0** en valor, ee, IC (inf y sup), gl, n y deff (la tolerancia era 1e-12: sale idéntico bit a bit, porque el adaptador hace la misma llamada a `svy`). N efectivo = mín(n, el de `calculo.py`) con |dif| = 0 (cuando `calculo` lo deja vacío por ee = 0, el ejecutor da n). `test_ejecutor_microdatos.py::test_anemia_2024_*`.

## Primera lectura contra las 90 filas del cubo (M0-10 es la comparación formal)

Las 3 recetas × 30 territorios, desde los Parquet de microdatos 2024 (verificador → gramática → DuckDB endurecido → ejecutor), contra `m0-00_filas_cubo_2024.csv` (el cubo guarda 8 decimales):

| Campo | Máx. \|dif\| (valor y ee en %) |
|---|---|
| valor | 4,95e-09 |
| ee | 4,94e-09 |
| IC inf / sup | 4,94e-09 / 4,99e-09 |
| deff | 4,96e-09 |
| n efectivo (contra mín(n, cubo)) | 4,90e-09 |
| gl, n | 0 |

Todo está dentro del redondeo a 8 decimales del cubo (≤ 5e-9 < 1e-8). Ninguna fila difiere más: no hay consulta tipo C. `test_las_recetas_de_2024_sobre_los_microdatos_igualan_las_30_filas_del_cubo` (3 pruebas) y `test_el_cubo_no_topa_el_n_efectivo_y_el_ejecutor_si` (las 12 filas con n efectivo > n).

## Pool (tarea 4), Mac (arm64, Python 3.12.16), tiempo suave 1 s + gracia 1 s

Tiempo desde `pool.ejecutar` hasta el `ErrorTemporal` (pool ya precalentado); el tope de la historia es timeout + 3 s = 4 s.

| Caso | Causa | Tiempo | La tarea siguiente |
|---|---|---|---|
| Ciclo de Python que no termina | `tiempo` (alarma suave) | 1,0 s | funciona; **mismo proceso** (no se mató) |
| Llamada nativa de `svy`: 220 000 filas × 275 dominios (≈ 3,4 s) | `tiempo` (tiempo duro, trabajador muerto) | 2,05 s | funciona en un trabajador nuevo (1,3 s por el arranque) |
| 2 000 MB pedidos con tope de 1 100 MB | `memoria` (vigía, salida 137) | 0,55 s | funciona |
| `os.abort()` | `caida` (código −6) | < 0,1 s | funciona |

También probado: error de la tarea (nulo de `y` en `u`) llega como `ErrorInterno` sin matar al trabajador; hilos en el trabajador (`POLARS_MAX_THREADS=RAYON_NUM_THREADS=1`, `pl.thread_pool_size()==1`, DuckDB `threads=1`, `memory_limit=488.2 MiB` = 512 MB); `max_tasks_per_child` reemplaza al trabajador; el resultado por el pool es igual al del proceso. Tres corridas seguidas de `test_pool_ejecutor.py`: 10 de 10 cada vez (≈ 22 s).

## p95 en el Mac

Ver `m0-08_tiempos.md` (30 repeticiones por caso, pool precalentado): 27 dominios 0,07 s, 99 dominios 0,15 s, 2 años apilados (96 dominios) 0,37 s, 4 años apilados (192 dominios) 0,87 s, sintético de 275 dominios en una llamada 3,5 s. Todos menos el último caben en el 1 s del ejecutor (§21); el de 275 confirma el límite de `dominios_max_llamada`. **Memoria:** 4 años apilados 0,9–1,2 GB y los 275 dominios 1,4–1,9 GB frente a un tope de 1,5 GB: ver supuesto en `consultas_al_dueno.md`.

## Criterios

- [x] Pruebas del pool pasan **en el Mac**. **Linux: pendiente** — no se pudo correr aquí. Las pruebas no dependen de la plataforma (alarma `SIGALRM`, `os._exit`, `os.abort`, `ru_maxrss` normalizado a bytes con `lector_aislado._rss_max_bytes`, que ya distingue macOS y Linux); falta correrlas en la nube y anotar el resultado (el tope de 1 100 MB de la prueba de memoria y los 220 000 filas del caso nativo podrían necesitar ajuste allí).
- [x] Equivalencia con `calculo._svy_niveles` (|dif| = 0 ≤ 1e-12).
- [x] p95 en el Mac → `m0-08_tiempos.md`.
- [x] Solo `svy_adaptador.py` importa `svy` en `src/pap/inferencia` (prueba `test_solo_el_adaptador_importa_svy`: el único otro archivo con `svy` en `src/` es `motor/calculo.py`, que se queda como está).

## Pruebas

- `uv run pytest -q -p no:cacheprovider -m regresion_microdatos`: 56 passed, 1614 deselected.
- Suite completa (`uv run pytest -q -p no:cacheprovider -rf`): 1669 passed, 1 skipped (base: 1620 passed, 1 skipped).
- Hash del cubo: `010ea965…` (sin cambios; no se tocaron `biblioteca/estandarizada/` ni el cubo).
