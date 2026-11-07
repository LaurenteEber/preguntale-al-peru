# S3-07 — Privacidad, abuso y costo

## Qué se registra (P-03)

| Registro | Qué guarda | Qué no guarda |
|---|---|---|
| Acceso de la web (`pap.web.acceso`) | método, ruta, código y tiempo en milisegundos | la consulta de la URL (`?…`), el cuerpo, la IP |
| Error de la web (`pap.web`) | el tipo de la excepción (`ValueError`…) | el mensaje de la excepción y la traza |
| Acceso de uvicorn (`uvicorn.access`) | nada: se descarta (ponía la URL con su consulta) | — |
| Error de uvicorn (`uvicorn.error`) | el tipo, sin traza | el mensaje y la traza |
| Uso del intérprete (`salidas/interprete/uso.jsonl`, ya existía en el slice 2) | huella SHA-256 de la pregunta, consulta con los lugares como «…», resultado, modelo, tokens y costo | el texto de la pregunta |

Una excepción que ningún `except` atrapó la atrapa la guardia (`src/pap/web/registro.py`) antes de uvicorn: responde 500 con el texto `error_interno` y las cabeceras de S3-04, y registra solo el tipo. La web no escribe `respuesta.json` ni ningún otro archivo. No hay cookies ni orígenes externos.

## Dónde vive la pregunta

El **único** lugar con rastro de la pregunta es la **caché de interpretaciones de 24 h** (P-03): `salidas/interprete/cache/<huella>.json` (fuera de git; en las pruebas, una carpeta temporal). Su nombre es la huella de la pregunta limpia; guarda la interpretación y sus «anclas», que son fragmentos literales de la pregunta (la intención, el tema y el lugar), no la pregunta entera. La búsqueda del marcador la deja fuera, como pide la historia; aun así el marcador, puesto en una premisa que no es ancla, no llegó a ella.

## Límites (todos `supuesto: S3-07` en `curados/web/parametros.yaml` → `limites`)

| Parámetro | Valor | Efecto |
|---|---|---|
| `preguntas_por_minuto_por_ip` | 10 | ventana deslizante de 60 s; al pasarse, 429 y «Espera un momento.» (`motivo: espera_un_momento`). El paso 1 del guiado no cuenta |
| `llamadas_llm_por_dia` | 300 | peticiones reales al proveedor, reintentos incluidos; los aciertos de caché no cuentan. Al llegarlo, `motivo: tope_diario` (503): la caja y los ejemplos se desactivan con el mensaje y el enlace a `/guiado`, y el guiado y la API estructurada siguen respondiendo |
| `zona_horaria` | `America/Lima` | el día del tope empieza a las 00:00 de Lima, no de UTC |
| `cuerpo_max_bytes` | 8192 | 413 `cuerpo_muy_grande`, también sin `Content-Length` |

Costo de referencia: US$ 0,0024 por pregunta con la caché del proveedor caliente y 0,018 sin ella → como máximo US$ 0,72 a 5,40 por día con 300 llamadas. Los contadores viven en memoria y se reinician al reiniciar (P-05); el slice 4 los revisa. `tope_diario` es el motivo que S3-04 había dejado como supuesto `S3-04-b`; queda confirmado y coincide con `paginas.mensajes_con_enlace_guiado`.

**Cómo se cuentan las llamadas:** `LlmContado` (`src/pap/web/limites.py`) envuelve al LLM que recibe `interpretar()`. El reintento por interpretación inválida llega como otra llamada y se cuenta. El reintento HTTP del proveedor ocurre dentro de `Cliente`, así que se agregó un contador `Cliente.intentos_http` (2 líneas en `src/pap/interprete/llm.py`, con su prueba): es lo mínimo que permite contar peticiones reales; una grabación reproducida o la falta de clave suman 0. Además, `interpretar.crear_cliente` (alias público de `_cliente`) para el caso sin `llm`.

## Pruebas

- `tests/web/test_privacidad.py`: 50 preguntas por texto (LLM falso, marcador en una premisa), las mismas por el formulario de la caja y 50 por el guiado (otro marcador en el lugar); se busca en registros, trazas, stdout/stderr, archivos nuevos o cambiados del repositorio (incluido `salidas/`) y del directorio de trabajo, y en el registro de uso: no aparece. Excepciones forzadas con el marcador (en la consulta y no capturada): se guarda el tipo y no el texto. Prueba con uvicorn de verdad (servidor en un hilo): ni el acceso ni el error de uvicorn traen el marcador, URL con marcador en la consulta incluida.
- `tests/web/test_limites.py`: límite por IP (API, páginas, guiado, ventana, otra IP); tope diario (aciertos de caché, reintento HTTP del cliente real con transporte de prueba, reintento por interpretación inválida, reloj falso que cruza el día de Lima y la medianoche de UTC que no reinicia); caja desactivada con mensaje y enlace y guiado respondiendo; cuerpo grande (tres rutas y sin `Content-Length`); cabeceras sin cookies.
- `tests/interprete/test_llm.py`: `intentos_http`.
- Corrida: `uv run pytest -q tests/web tests/interprete tests/test_sin_secretos.py` → ver el cierre del mensaje de la historia (17 fallos en `test_guiado.py` por el límite por IP: su fixture, fuera de la superficie de esta historia, necesita `app.state.limites.por_minuto = 10 ** 9`; con el límite anulado pasan 41/41).

Suite completa en el Mac (6/11/2026, antes del commit): 1154 pasan, 0 fallan.
