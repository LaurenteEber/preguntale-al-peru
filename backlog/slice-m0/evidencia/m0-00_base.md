# M0-00 — Base medida (9/11/2026, Mac del dueño)

- **Rama:** `slice-m0`, creada desde `main` en `850ba79` («docs: versión 2 de motor de inferencia»). Ese commit ya traía los documentos nuevos (`docs/diseno/`, `backlog/README.md`, `backlog/plan_slices.md`, `backlog/slice-m0/` y `backlog/slice-m1/`), así que la rama parte de ellos y la tarea 1 queda cumplida sin un commit aparte.
- **pytest completo:** 1258 pasan, 1 se salta, 0 fallan; 900,7 s (15 min) → `pytest_base.txt`.
- **Cubo:** `biblioteca/indicadores/fact_indicador.parquet` con sha256 `010ea965381c28c374f31692748204ea5f4e82e1ebf97ff46bc757d947ace66f`.
- **Copia del cubo:** `evidencia/fact_indicador_010ea965.parquet`, fuera de git (`backlog/**/evidencia/*.parquet` en `.gitignore`), con la misma huella.
- **Filas de 2024:** `m0-00_filas_cubo_2024.csv`, 90 filas (3 indicadores × 30: 1 nacional, 2 de área, 24 departamentos sin el Callao, Lima Metropolitana, Lima Región y Callao).
- **Estados (oráculo de M0-09):** `m0-00_estados_cubo.csv`, armado con `m0-00_estados_cubo.py` sobre las funciones de `reglas_etapa4.py`: 85 publicables y 5 referenciales (DCI por R-ENC-04).
- **Interfaces:** `m0-00_interfaces.md`.
