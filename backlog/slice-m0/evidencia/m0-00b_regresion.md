# M0-00b — Regresión (tarea 5)

Sobre el commit `4787964` (lock nuevo: Pillow 13.0.0, certifi 2026.10.23, python-multipart 0.0.32, opentelemetry-api 1.45.1, pytest-socket 0.8.1; lectura de ZIP con `abrir_zip_seguro`).

- `uv run pap calcular` (11 s): sha256 del cubo `010ea965381c28c374f31692748204ea5f4e82e1ebf97ff46bc757d947ace66f`, **idéntico byte a byte** a `fact_indicador_010ea965.parquet` (copia de M0-00). Con la misma huella, |dif| = 0 en todas las columnas.
- Suite completa (incluye `test_regresion_q1_q4.py`, la matriz reducida de `test_matriz_cobertura.py` y la evaluación grabada de `tests/interprete/`): `1280 passed, 1 skipped in 894.81s` (base: 1258 + 22 pruebas nuevas de M0-00b).
- Q1–Q4, matriz y evaluación grabada: sin cambios (las pruebas comparan contra sus referencias).
