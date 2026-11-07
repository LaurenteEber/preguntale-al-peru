# S3-06 — Accesibilidad y celular: evidencia

Hecha por el agente, con Chromium (Playwright) y axe-core 4.14.0 (`tests/web/vendor/`, huella en `AXE_VERSION.txt` y comprobada por una prueba). Prueba: `tests/web/test_accesibilidad.py` (marca `navegador`, registrada en `pyproject.toml`). Corrida: `uv run pytest -q tests/web tests/test_sin_secretos.py` → 170 pasaron, 1 se salta (la que genera las capturas, solo con `PAP_CAPTURAS=1`).

Nota X-22 (6/11/2026): la historia pide la aclaración con «Huancavelica»; ya no aclara (un departamento a secas se responde como departamento). Se usa «Abancay» (hay una provincia y un distrito con ese nombre).

## axe: 0 fallas graves o críticas

Se revisó cada página con los `<details>` abiertos, a 360 px y 1280 px, en modo claro y oscuro (`prefers-color-scheme` emulado). Resultado: **0 fallas de cualquier gravedad** en las 9 páginas × 2 anchos × 2 modos (36 corridas), más el inicio con el tope diario alcanzado. La regla de contraste (`color-contrast`) sí se evaluó (de 5 a 71 nodos por página, sin «incompletos»). La prueba comprueba que cada corrida llegó a la página pedida y que el fondo oscuro se aplicó.

| Página | 360 px claro | 360 px oscuro | 1280 px claro | 1280 px oscuro |
|---|---|---|---|---|
| Inicio | 0 | 0 | 0 | 0 |
| Guiado, paso 1 | 0 | 0 | 0 | 0 |
| Guiado, paso 2 | 0 | 0 | 0 | 0 |
| Respuesta Q1 | 0 | 0 | 0 | 0 |
| Respuesta Q3 | 0 | 0 | 0 | 0 |
| Aclaración (Abancay) | 0 | 0 | 0 | 0 |
| «No se puede» (cruce, Puno) | 0 | 0 | 0 | 0 |
| Mensaje (sin intérprete: `no_disponible`) | 0 | 0 | 0 | 0 |
| Error (opción inválida, 422) | 0 | 0 | 0 | 0 |
| Inicio con tope diario | 0 | 0 | — | — |

No hizo falta cambiar plantillas ni CSS: las páginas de S3-04, S3-05 y S3-07 ya cumplían.

## Lista manual (automatizada con Playwright)

| Comprobación | Resultado | Prueba |
|---|---|---|
| Todo se usa con teclado; el foco se ve | Con Tab se llega a todos los enlaces, botones y campos (inicio, guiado 2, respuesta, aclaración, mensaje); cada foco tiene contorno de 3 px. Captura: [foco_inicio_360.png](s3-06/foco_inicio_360.png) | `test_todo_se_alcanza_con_el_teclado_y_el_foco_se_ve` |
| Zoom al 200 % | Sin barra horizontal ni elementos fuera de la pantalla a 180 px CSS (360 px al 200 %) y a 640 px (1280 px al 200 %); la letra base al 200 % tampoco corta la respuesta. Captura: [zoom200_respuesta_q1_360.png](s3-06/zoom200_respuesta_q1_360.png) | `test_zoom_200_por_ciento_sin_perder_contenido`, `test_tamano_de_letra_al_200_por_ciento_sigue_legible` |
| `lang="es"` y título | Todas las páginas | `test_lengua_titulo_y_encabezados_en_orden` |
| Encabezados en orden | Un solo `h1`, sin saltos de nivel hacia abajo, un solo `<main>` | ídem |
| `<details>` se anuncian | `summary` es el primer hijo; Enter abre y cierra; el árbol de accesibilidad los da como grupo | `test_details_tienen_summary_y_se_abren_con_el_teclado` |
| Confianza sin color (R-05) | Es una frase, sin clase por nivel, sin ícono y con el mismo color que el resto del texto | `test_la_confianza_se_entiende_sin_color` |
| Los enlaces dicen a dónde llevan | Ningún enlace de menos de 6 letras ni «aquí», «ver», «más» | `test_los_enlaces_dicen_a_donde_llevan` |
| Contraste AA claro y oscuro | axe sin fallas de contraste en las dos paletas | tabla de arriba |
| Botones y campos ≥ 44 px de alto | Inicio, guiado 2 y aclaración | `test_objetivos_tactiles_de_44_px` |

Capturas a 360 px (PNG, claro y oscuro de cada página), en `backlog/slice-3/evidencia/s3-06/`: `<página>_<claro|oscuro>_360.png` con página = `inicio`, `guiado_paso1`, `guiado_paso2`, `respuesta_q1`, `respuesta_q3`, `aclaracion`, `no_se_puede`, `mensaje`, `error` (nombres `light` y `dark`). Ejemplos: [inicio](s3-06/inicio_light_360.png), [respuesta Q1](s3-06/respuesta_q1_light_360.png), [aclaración](s3-06/aclaracion_light_360.png), [mensaje](s3-06/mensaje_dark_360.png).

## Peso

Respuesta de Q1: **6 470 bytes** (≈ 6,3 KB) sin comprimir; el límite es 100 KB. Sin `<img>`, sin `<svg>` ni `url(` en el HTML (`test_q1_pesa_menos_de_100_kb_y_no_hay_imagenes`).

## Supuestos (tipo B)

Sin parámetros nuevos de motor. Decisiones de la prueba, no visibles para el usuario: axe 4.14.0 fija; el contexto de Playwright usa `bypass_csp` solo para inyectar axe (la CSP de la app no cambió y sigue probada en `test_paginas.py`); «zoom al 200 %» se prueba como viewport de 180 px y 640 px CSS con escala 2.

## Consultas abiertas

Ninguna.

Suite completa en el Mac (6/11/2026, antes del commit): 1211 pasan y 1 se salta, que solo genera capturas cuando se corre con `PAP_CAPTURAS=1`. Fallan 0.
