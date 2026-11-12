# M0-04 — Tamaño, memoria y tiempo de la conversión de la ENDES 2024

Medido el 9/11/2026 en el Mac del dueño (16 GB de RAM, macOS) con `uv run pap microdatos convertir --encuesta ENDES --anio 2024`. Datos: `biblioteca/microdatos/ENDES/2024/manifiesto.json` (campos `bytes_parquet`, `rss_max_mb`, `segundos_conversion`, `segundos_huella`). El RSS es el máximo del subproceso lector (`ru_maxrss`, que incluye leer, escribir el Parquet y calcular la huella).

| Archivo | ZIP | DTA (MB) | Parquet (MB) | Filas | Columnas | RSS máx. (MB) | Conversión (s) | Huella (s) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| CSALUD01 | 968-Modulo1640.zip | 70.5 | 1.78 | 34 018 | 259 | 569 | 1.6 | 0.68 |
| CSALUD08 | 968-Modulo1640.zip | 18.3 | 0.69 | 41 309 | 54 | 288 | 0.5 | 0.23 |
| DIT | 968-Modulo1634.zip | 10.0 | 0.28 | 19 245 | 65 | 255 | 0.3 | 0.09 |
| PS_BECA18 | 968-Modulo1641.zip | 0.0 | 0.00 | 48 | 11 | 169 | 0.1 | 0.01 |
| PS_COMEDOR | 968-Modulo1641.zip | 0.1 | 0.01 | 1 437 | 11 | 170 | 0.1 | 0.01 |
| PS_PENSION65 | 968-Modulo1641.zip | 0.2 | 0.02 | 2 745 | 11 | 171 | 0.1 | 0.01 |
| PS_QALIWARMA | 968-Modulo1641.zip | 1.8 | 0.11 | 18 984 | 12 | 186 | 0.1 | 0.04 |
| PS_TRABAJA | 968-Modulo1641.zip | 0.0 | 0.00 | 78 | 11 | 169 | 0.1 | 0.01 |
| PS_VL | 968-Modulo1641.zip | 0.9 | 0.06 | 9 824 | 11 | 176 | 0.1 | 0.03 |
| PS_WAWAWASI | 968-Modulo1641.zip | 0.1 | 0.01 | 725 | 11 | 169 | 0.1 | 0.01 |
| Programas_Sociales_x_Hogar | 968-Modulo1641.zip | 5.7 | 0.21 | 34 018 | 21 | 209 | 0.2 | 0.09 |
| RE223132 | 968-Modulo1632.zip | 41.3 | 1.06 | 34 252 | 151 | 401 | 1.0 | 0.33 |
| RE516171 | 968-Modulo1635.zip | 23.4 | 0.93 | 34 252 | 86 | 312 | 0.7 | 0.30 |
| RE758081 | 968-Modulo1636.zip | 54.8 | 0.51 | 34 252 | 200 | 440 | 1.0 | 0.29 |
| REC0111 | 968-Modulo1631.zip | 31.3 | 1.29 | 37 117 | 105 | 372 | 1.0 | 0.51 |
| REC21 | 968-Modulo1632.zip | 17.1 | 0.74 | 60 693 | 36 | 261 | 0.6 | 0.26 |
| REC41 | 968-Modulo1633.zip | 23.6 | 0.53 | 19 751 | 149 | 359 | 0.6 | 0.21 |
| REC42 | 968-Modulo1634.zip | 46.8 | 1.33 | 34 252 | 171 | 411 | 1.0 | 0.36 |
| REC43 | 968-Modulo1634.zip | 26.9 | 0.64 | 19 751 | 170 | 375 | 0.6 | 0.21 |
| REC44 | 968-Modulo1638.zip | 5.6 | 0.78 | 19 751 | 36 | 218 | 0.3 | 0.13 |
| REC82 | 968-Modulo1636.zip | 19.5 | 1.19 | 171 260 | 6 | 275 | 0.5 | 0.15 |
| REC83 | 968-Modulo1637.zip | 23.0 | 0.59 | 141 805 | 21 | 295 | 0.5 | 0.22 |
| REC84DV | 968-Modulo1637.zip | 60.9 | 0.75 | 34 252 | 222 | 523 | 1.1 | 0.26 |
| REC91 | 968-Modulo1631.zip | 102.6 | 1.77 | 37 117 | 345 | 778 | 2.4 | 0.64 |
| REC93DVdisciplina | 968-Modulo1639.zip | 2.5 | 0.14 | 15 462 | 20 | 192 | 0.2 | 0.03 |
| REC94 | 968-Modulo1633.zip | 9.9 | 0.32 | 19 751 | 63 | 248 | 0.4 | 0.12 |
| REC95 | 968-Modulo1634.zip | 47.9 | 1.91 | 19 751 | 302 | 581 | 1.2 | 0.54 |
| RECH0 | 968-Modulo1629.zip | 14.8 | 0.58 | 37 390 | 45 | 264 | 0.5 | 0.19 |
| RECH1 | 968-Modulo1629.zip | 52.3 | 1.00 | 135 045 | 37 | 348 | 1.2 | 0.41 |
| RECH23 | 968-Modulo1630.zip | 39.3 | 1.04 | 37 390 | 131 | 409 | 1.0 | 0.38 |
| RECH4 | 968-Modulo1629.zip | 24.7 | 0.54 | 135 045 | 23 | 298 | 0.8 | 0.27 |
| RECH5 | 968-Modulo1638.zip | 12.5 | 1.07 | 38 488 | 41 | 254 | 0.4 | 0.22 |
| RECH6 | 968-Modulo1638.zip | 7.2 | 0.80 | 20 290 | 44 | 226 | 0.3 | 0.15 |
| RECHM | 968-Modulo1629.zip | 0.2 | 0.02 | 3 002 | 9 | 171 | 0.1 | 0.01 |

**Total:** 34 archivos en 13 ZIP. ZIP en disco: 88.0 MB. DTA descomprimidos: 795.6 MB. Parquet: 22.7 MB (2.9 % del DTA). Tiempo de conversión: 21 s sumando archivos (comando completo: 49 s de reloj).

## Criterios de M0-04

- RSS máximo por archivo < 1,5 GB (1 536 MB): **cumple**. Máximo 778 MB (REC91).
- Huella de contenido en < 5 s por archivo: **cumple**. Máximo 0.68 s (CSALUD01).
- Tamaño por archivo y total: en la tabla de arriba.

## Notas

- El diseño estimaba 50–100 MB de Parquet para la ENDES 2024 (§6); lo medido es bastante menos. La proyección 2015–2025 del diseño queda por encima de lo que se espera.
- Ningún archivo pasó de 200 MB (el mayor, REC91, tiene 102,6 MB), así que ninguno se leyó por bloques; esa ruta está probada con archivos sintéticos.
- RLIMIT_AS no se hace cumplir en macOS (el conversor lo detecta y lo deja en el manifiesto: `rlimit_as_aplicado: false`). El tope real de memoria allí es el vigilante de RSS (3 072 MB, sondeo cada 0,2 s); RLIMIT_CPU (900 s) y el tope de tiempo (1 800 s) sí se aplican. La prueba `test_vigilante_mata_al_subproceso_que_pasa_el_tope_de_memoria` lo verifica.
- Ningún DTA de 2024 trae perdidos extendidos (.a–.z): `perdidos` está vacío en los 34 archivos, así que ninguna receta ve cambiar un universo por esta conversión.
- Todos los DTA son formato 118 (UTF-8 declarado por el formato): no se usó el respaldo `WINDOWS-1252`, probado con un archivo sintético de formato 115.
