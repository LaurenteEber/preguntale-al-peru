# S3-08 — Rendimiento

Medido con `uv run python tests/web/medir.py --vivo 20 --tope-costo 0.50 --json backlog/slice-3/evidencia/s3-08/medicion.json` (semilla 3008), en el Mac del dueño, con el servicio precalentado (el hilo de precalentamiento ya terminó) y el límite por IP desactivado. Mide en el mismo proceso, por la app (TestClient); aparte, una muestra con uvicorn de verdad. Salida en bruto: `s3-08/medicion.txt` y `.json` (el registro de accesos, en `medicion.stderr.log`). Tiempos en segundos.

## Resultados

| Vía | n | p50 | p95 | máx |
|---|---|---|---|---|
| **Estructurada**, página HTML (total) | 200 | 0,037 | 0,268 | 0,328 |
| · motor | 200 | 0,034 | 0,264 | 0,325 |
| · página (render y validación) | 200 | 0,003 | 0,003 | 0,027 |
| Estructurada, API JSON (total) | 200 | 0,036 | 0,262 | 0,426 |
| **Texto con grabaciones (sin LLM)**, total | 158 | 0,302 | 0,812 | 0,901 |
| · intérprete (código propio) | 158 | 0,266 | 0,362 | 0,491 |
| · motor | 158 | 0,033 | 0,526 | 0,617 |
| · página | 158 | 0,003 | 0,003 | 0,004 |
| **Texto en vivo (LLM)**, total | 20 | 1,879 | 3,132 | 4,477 |
| · LLM (proveedor) | 20 | 1,580 | 2,897 | 4,242 |
| · intérprete (código propio) | 20 | 0,268 | 0,352 | 0,398 |
| · motor | 20 | 0,035 | 0,299 | 0,893 |
| · página | 20 | 0,003 | 0,004 | 0,005 |
| uvicorn real, API JSON | 50 | 0,035 | 0,252 | 0,292 |
| uvicorn real, página HTML | 50 | 0,036 | 0,253 | 0,290 |

Notas:
- La vía estructurada son 200 respuestas: los 60 casos de la matriz reducida repetidos y mezclados con la semilla. Todas dieron 200.
- Los 158 del conjunto de evaluación por texto usan las grabaciones: no se llama a ningún proveedor; ninguna dio error por falta de grabación.
- HTTP real casi no suma: con uvicorn los p50 y p95 son iguales a los del proceso (diferencia menor que el ruido).
- La parte del motor que domina son las consultas de cruce y efecto con territorios chicos (p. ej. `gasto_publico|cruce|Llaylla`, `anemia|efecto|Luya`), de 0,3 a 0,45 s.
- Una corrida anterior, igual salvo que no registraba el uso, dio en vivo p50 2,02 · p95 2,65 · máx 3,94 (`s3-08/corrida2_sin_registro_de_uso.txt`). Con 20 preguntas el p95 es casi el segundo valor más alto: varía de una corrida a otra (2,6 a 3,1 s); la latencia del proveedor es lo que se mueve.

## Objetivos (`curados/web/parametros.yaml`, sección `rendimiento`)

| Objetivo | Valor | Origen | Medido | ¿Se cumple? |
|---|---|---|---|---|
| Sin LLM, p95 | < 2 s | `decision:` `plan_slices.md` (fila del slice 3) | estructurada 0,27 s; texto con grabaciones 0,81 s | **Sí** |
| Texto libre, p95 | ≤ 3,5 s | `supuesto: S3-08`: p95 del LLM en S2-09 (2,5 s) + 1 s | 3,13 s (otra corrida: 2,65 s) | **Sí**, con poco margen en la peor corrida |
| Texto libre, máximo | ≤ 10 s | `supuesto: S3-08` | 4,48 s | **Sí** |
| Arranque hasta `/salud` 200 | ≤ 30 s | `supuesto: S3-08` | 4,2 a 4,7 s (3 arranques); 24,9 s el primero tras sincronizar las dependencias, con los archivos aún fríos | **Sí** |

El máximo de 10 s sale de la tarea 2 de la historia; el tiempo máximo del proveedor está en `interprete.tiempo_max_segundos`.

## Arranque

Procesos nuevos, desde lanzar `python` (imports y uvicorn incluidos) hasta `/salud` 200: 4,7 · 4,2 · 4,2 s. `crear_app` más el precalentamiento (módulos ya cargados): 3,4 s. En una corrida previa, cuyo primer arranque fue en frío tras `uv sync`, tardó 24,9 s y los dos siguientes 4,3 y 4,2 s (`s3-08/primera_corrida_sin_llm.txt`). Cumple, pero un arranque en frío está cerca del límite de 30 s.

## Costo de la corrida en vivo (tope US$ 0,50 por corrida; el dueño autorizó como máximo US$ 0,50 en total)

- Modelo `claude-sonnet-5-5`, esfuerzo `low` (los configurados, sin cambiar). Modo «vivo»: no graba, `tests/interprete/grabaciones/` no cambió.
- 20 preguntas del conjunto elegidas con la semilla (ids en `medicion.txt`); 21 llamadas al proveedor (un reintento).
- Según el cambio en `salidas/interprete/uso.jsonl` (21 líneas) y según el cliente: **US$ 0,0500**.
- Una corrida anterior (la de arriba, que no registraba el uso): US$ 0,0688 según el cliente (21 llamadas). Gasto vivo total de S3-08: **≈ US$ 0,12**, bajo el tope.

## Caché de respuestas

No hace falta: se cumplen todos los objetivos, así que no se creó `src/pap/web/cache.py` ni más consultas de precalentamiento (tarea 3 de la historia). No se cambió el motor ni el cubo.

## Supuestos (`supuesto: S3-08`)

1. Texto libre p95 ≤ 3,5 s (2,5 + 1).
2. Texto libre máximo ≤ 10 s.
3. Arranque ≤ 30 s.
4. Semilla de la medición: 3008; 20 preguntas en vivo; 50 en la muestra con uvicorn.

Suite completa en el Mac (6/11/2026, antes del commit): 1211 pasan, 1 se salta (capturas de S3-06), 0 fallan.
