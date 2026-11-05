# API de la web (S3-03)

Servicio FastAPI, un solo proceso, sobre el mismo motor. Un candado envuelve toda llamada a `interpretar()` o `preguntar_minima()`. Textos en `curados/web/textos.yaml`, parámetros en `curados/web/parametros.yaml`. No hay ningún `GET` que lleve la pregunta.

| Ruta | Entrada | Salida |
|---|---|---|
| `POST /api/preguntar` | JSON `{texto, elegir?}` o `{consulta, elegir?}` (uno solo de los dos). `elegir`: un número o una lista, acumulada en el orden de las aclaraciones | El `respuesta.json` del motor sin cambios |
| `GET /api/opciones` | — | `temas`, `intenciones`, `niveles` (con rótulo) y `ejemplos` |
| `GET /api/version` | — | `Motor.version()` más `rotulo`: «Biblioteca {huella corta del cubo}, construida el {fecha}» |
| `GET /salud` | — | `{"estado": "ok"}` o 503 `{"estado": "preparando"}` |

## Códigos HTTP

Derivados de `cli.codigo_salida` (`curados/motor/parametros_motor.yaml`) y del tipo `mensaje` (el código va en `motivo`). El cuerpo es siempre el JSON del motor; el estado HTTP dice si hubo respuesta.

| Caso | CLI | HTTP | Cuerpo |
|---|---|---|---|
| `respuesta`, `no_se_puede`, `aclaracion` | 0, 0, 2 | 200 | respuesta del motor |
| `mensaje` (`no_es_pregunta`, `otro_idioma`, `no_entendida`, `volver_a_preguntar`) | 2 | 200 | mensaje fijo del intérprete |
| `mensaje` con `motivo: no_disponible` | 3 | 503 | mensaje fijo del intérprete |
| Servicio preparándose | — | 503 | `{"tipo": "mensaje", "motivo": "preparando", "texto": «Estamos preparando el servicio…»}` |
| `ConsultaInvalida` | 1 | 422 | `{"tipo": "error", "motivo": "consulta_invalida", "texto"}` |
| `EleccionInvalida` | 1 | 422 | `{"tipo": "error", "motivo": "eleccion_invalida", "texto"}` |
| Cuerpo mal formado, texto demasiado largo, `elegir` fuera de límites | — | 422 | `solicitud_invalida` o `texto_muy_largo` |
| `GET` sobre `/api/preguntar` | — | 405 | `metodo_no_permitido` |
| Error inesperado | — | 500 | `error_interno` |

Los textos de error son de la web; el detalle de la excepción (sin la pregunta) va al registro y nunca a la respuesta.
