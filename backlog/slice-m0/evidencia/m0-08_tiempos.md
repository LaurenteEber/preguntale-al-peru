# M0-08 — Tiempos del ejecutor en el Mac

Medido el 09/11/2026 en macOS-27.2-arm64-arm-64bit (arm64), Python 3.12.16, `svy` 0.35.0. **Linux: pendiente** (no se pudo correr aquí).

**Método.** Pool precalentado (spawn) con los valores de `curados/inferencia/parametros.yaml` (`ejecutor.*`: 1 trabajador, DuckDB `threads=1` y `memory_limit=512MB`, `POLARS_MAX_THREADS=RAYON_NUM_THREADS=1`). Cada caso: una corrida de descarte y luego 30 repeticiones; tiempo de pared de `pool.ejecutar(tarea)` (envío de la tarea, lectura de los datos en el trabajador, estimación con `svy` y retorno de las `Estimacion`). Los casos de microdatos pasan por DuckDB endurecido → `.arrow()` → `pl.from_arrow`; los de `endes_nino` y el sintético arman el marco en memoria. El pico es el `ru_maxrss` del trabajador; cada caso corre en un pool nuevo (con el tope subido a 4 096 MB solo para medir; el vigente es 1536 MB).

| Caso | Dominios devueltos | Rep. | p50 (s) | p95 (s) | máx. (s) | Pico de memoria (MB) |
|---|---:|---:|---:|---:|---:|---:|
| microdatos 2024, 27 dominios (≈ 25: 3 departamentos × 9 de área × sexo) | 27 | 30 | 0.066 | 0.070 | 0.090 | 387 |
| microdatos 2024, 99 dominios (≈ 100: 11 departamentos × 9 de área × sexo) | 99 | 30 | 0.122 | 0.148 | 0.149 | 441 |
| endes_nino 2023–2024 apilados (2 años, departamento × área) | 96 | 30 | 0.358 | 0.367 | 0.367 | 530 |
| endes_nino 2021–2024 apilados (4 años, departamento × área) | 192 | 30 | 0.852 | 0.868 | 0.878 | 1176 |
| sintético, 275 dominios en una llamada (220 000 filas) | 275 | 30 | 3.333 | 3.485 | 3.775 | 1928 |
