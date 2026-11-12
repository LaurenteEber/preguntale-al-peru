# M0-11 — Medición en el Mac (ENDES 2024)

Mac del dueño (Apple Silicon arm64, 16 GB de RAM, macOS), Python 3.12.16, `svy` 0.35.0. Medido entre el 9/11/2026 (M0-02 a M0-08) y el 10/11/2026 (este informe). Cada número cita de dónde sale. **Linux: pendiente** (el pool no se corrió allí).

## 1. Tamaño del bloque y proyección a 2015–2025

| Qué | Tamaño | Fuente |
|---|---:|---|
| 13 ZIP de Stata de 2024 | 88,0 MB | `m0-02_tamano_zip.md` |
| 7 PDF de 2024 (ficha, cuestionarios, diccionarios) | 16,8 MB | `m0-02_tamano_zip.md` |
| DTA descomprimidos (34 archivos; no se guardan) | 795,6 MB | `m0-04_tamano.md` |
| Parquet zstd de 2024 (34 archivos y su manifiesto) | 22,7 MB (22 MB con `du`) | `m0-04_tamano.md` |
| Índice de variables (`biblioteca/variables/`, 3 Parquet) | 184 KB | `du -sh`, 10/11/2026 |
| Release `crudos-endes-2024` del repo privado (22 archivos: 13 ZIP, 7 PDF, `SHA256SUMS`, `LEEME.txt`) | ≈ 104,8 MB | `m0-11_restauracion.txt` |

**Proyección a 2015–2025** (se escala el bloque de 2024 por el tamaño de los módulos de hogar y anemia de cada año, que ya están registrados; `m0-02_tamano_zip.md`):

- ZIP: ≈ 906 MB; con los PDF de cada año al nivel de 2024: ≈ 1,09 GB.
- Parquet: 22,7 MB × 11 años ≈ 0,25 GB.
- Índice: menos de 3 MB.
- **Total local con los ZIP: ≈ 1,35 GB. Después de liberar los ZIP de cada bloque: ≈ 0,5 GB** (Parquet, índice, PDF, y los ZIP de hogar y anemia, que lee `pap calcular`).

**Propuesta de tope para F-04 (ENDES 2015–2025):** **2 GB en el Mac** (ZIP, PDF, Parquet e índice) y **1,5 GB en el repo privado de crudos**. Deja ≈ 45 % de margen sobre la proyección, que es gruesa: los años en SPSS (2015–2020) pueden pesar distinto. Si un bloque nuevo hace pasar el tope, se para y se consulta. Es decisión del dueño: consulta C-M0-11-1 en `consultas_al_dueno.md`.

## 2. Espacio libre del Mac

| Momento | Libre (`df -k`, GB decimales) |
|---|---:|
| Al empezar el diseño del motor (`docs/diseno/motor_inferencia.md` §6) | 109 GB |
| 10/11/2026, antes de reindexar | 107,8 GB |
| 10/11/2026, después de reindexar | 107,8 GB |

El bloque de 2024 ocupa ≈ 0,13 GB (ZIP, PDF, Parquet e índice): **el espacio libre «antes del bloque» es el de ahora más esos 0,13 GB, calculado, no medido**. Los registramos sin medir el disco antes. La diferencia con los 109 GB del diseño viene de otras cosas del Mac, no del bloque. Siempre queda muy por encima de `almacen.espacio_libre_min_gb` (50 GB). Liberar los 11 ZIP liberables daría 73,0 MB (`m0-11_liberar_simulacion.txt`); no se liberó nada: es decisión del dueño.

## 3. Índice de variables

De `m0-05_conteos.md`, salvo el tiempo:

- Filas: 2 856 variables y 7 602 categorías (34 archivos).
- Textos de etiqueta distintos: 4 129.
- Tokens por texto, **aproximados por palabras**: p50 5, p95 14, máximo 20. El tokenizer real llega en M1.
- **Tiempo de `pap variables indexar --encuesta ENDES --anio 2024`, 10/11/2026:** 17,5 s de reloj y 0,40 GB de RSS máximo (`/usr/bin/time -l`). Los tres Parquet salieron **idénticos byte a byte** a los anteriores (SHA-256 iguales): el índice es reproducible.

## 4. Conversor

De `m0-04_tamano.md`:

- 21 s sumando los 34 archivos; 49 s de reloj el comando completo.
- RSS máximo por archivo: 778 MB (REC91). El criterio de M0-04 era menos de 1,5 GB.
- Huella de contenido: como mucho 0,68 s por archivo. El criterio era menos de 5 s.
- `restaurar` reconvirtió PS_BECA18 desde el release en 7,6 s de reloj, contando la bajada, con la misma `huella_contenido_v1` (`m0-11_restauracion.txt`).

## 5. Ejecutor: p95 y memoria del pool

p95 de `m0-08_tiempos.md` (30 repeticiones, pool precalentado):

| Caso | Dominios | p95 (s) | Pico de memoria (MB) |
|---|---:|---:|---:|
| Microdatos 2024 | 27 | 0,070 | 387 |
| Microdatos 2024 | 99 | 0,148 | 441 |
| 2 años apilados | 96 | 0,367 | 530 |
| 4 años apilados | 192 | 0,868 | 1 176 |
| Sintético en una llamada | 275 | 3,485 | 1 928 |

Lo medido el 10/11/2026 (`tests/inferencia/medir_m11.py 20`):

- **Pool en reposo:** el trabajador precalentado ocupa 247 MB de memoria residente.
- **DuckDB con 1 hilo frente a 2,** en el caso de 99 dominios y 20 repeticiones:

  | Hilos | p50 (s) | p95 (s) | Pico (MB) |
  |---:|---:|---:|---:|
  | 1 | 0,122 | 0,125 | 406 |
  | 2 | 0,118 | 0,122 | 402 |

  La diferencia es de 3 ms y está dentro del ruido. Se queda en 1 hilo por trabajador.

## 6. Tiempo real de `ejecutor_gracia_s`

Se probó una llamada nativa de `svy` de ≈ 5 s (264 000 filas × 330 dominios, sintética) con tiempo suave 1 s y la gracia de producción, 2 s. Se midió lo que pasa desde el tiempo suave hasta que el padre devuelve la falla `tiempo`, ya con el trabajador muerto. Fueron 5 repeticiones, y el pool siguió respondiendo después de cada una.

- **p50 2,05 s; máximo 2,09 s** (gracia configurada: 2,0 s). El exceso de unos 50 ms es el sondeo y la muerte del proceso.
- La gracia no depende del tiempo suave. Con los valores de producción (5 s + 2 s), una llamada colgada se corta a los **≈ 7,05 s**. M0-08 había medido 2,05 s con 1 s + 1 s.

## 7. Parámetros (tarea 4): no cambia ninguno

| Parámetro | Valor | Lo medido | Decisión |
|---|---:|---|---|
| `verificador.dominios_max_llamada` | 100 | 99 dominios: p95 0,148 s, 441 MB | se queda |
| `verificador.anios_apilados_max_llamada` | 4 | 4 años (192 dominios): p95 0,868 s, 1 176 MB | se queda |
| `ejecutor.ejecutor_timeout_s` | 5 | el caso más pesado permitido tarda 0,87 s (≈ 6 veces de margen) | se queda |
| `ejecutor.ejecutor_gracia_s` | 2 | corte real 2,05 s después del suave | se queda |
| `ejecutor.memoria_trabajador_mb` | 1 536 | el caso más pesado permitido llega a 1 176 MB (23 % de margen). Los 275 dominios (1 928 MB) ya los frenan `dominios_max_llamada` y el vigía | se queda |
| `ejecutor.duckdb_threads` | 1 | 1 hilo frente a 2: sin diferencia | se queda |

Ningún valor cambia, así que no hace falta marcar `supuesto: M0-11`. Solo se anotó la medición en el comentario de `ejecutor.duckdb_threads`. **Ojo:** el margen de memoria es justo para 4 años apilados con muchos cortes. Si M1 sube `anios_apilados_max_llamada`, hay que volver a medir.

## Lo que queda pendiente

- La corrida del pool en Linux: `RLIMIT_AS` y `ru_maxrss` en KiB, y la medición del 4 años × 192 dominios.
- Los tokens reales por texto, con el tokenizer de M1.
