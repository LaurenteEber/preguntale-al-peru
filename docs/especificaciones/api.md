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

## Páginas HTML (S3-04)

Las páginas usan la misma función que `POST /api/preguntar` (mismas validaciones, mismo candado, mismos estados HTTP); `/api/*` no cambia. Textos en `curados/web/textos.yaml` (`paginas`, `mensajes`) y rótulos en `curados/motor/textos/capas.yaml` → `rotulos`.

| Ruta | Entrada | Salida |
|---|---|---|
| `GET /` | — | Inicio: caja de pregunta, ejemplos tocables, temas de hoy y fuentes, enlace a `/guiado` |
| `POST /preguntar` | Formulario: `texto` o `consulta` (JSON en un campo oculto), `elegir` (acumulado, «1,2») y `n` (el botón pulsado de una aclaración) | Página de respuesta, aclaración o aviso, con el estado HTTP de `/api/preguntar` |
| `GET /estatico/app.js`, `/estatico/estilo.css` | — | El único JavaScript («Buscando…») y el único CSS |

Cabeceras de las páginas y los archivos propios: `Content-Security-Policy` (`curados/web/parametros.yaml` → `paginas.csp`, `default-src 'self'`), `Referrer-Policy: no-referrer`, `X-Content-Type-Options: nosniff`. Ninguna respuesta pone cookies. Bloques de respuesta, en orden: Entendimos, respuesta corta (primero en «no se puede»), cifra clave, lo más cercano, ojo al leer, confianza (solo `capa1.confianza.texto`), qué hacer, «Más contexto» y «Para citar y verificar» (desplegables cerrados). Sin ficha técnica.

## Formulario guiado (S3-05)

Dos pasos, sin LLM y sin JavaScript. Las opciones salen de lo mismo que `GET /api/opciones` (leídas en el servidor); los campos de cada intención, de `curados/web/parametros.yaml` → `guiado`; los textos, de `curados/web/textos.yaml` → `guiado`.

| Ruta | Entrada | Salida |
|---|---|---|
| `GET /guiado` | — | Paso 1: tema y qué quieres saber (con la descripción de cada intención) |
| `POST /guiado` | Paso 1: `tema`, `intencion`. Paso 2: además `paso=2` y los campos de la intención: `lugar` o `lugar_nacional` («Todo el Perú»), `lugar2` o `lugar2_nacional` (comparación), `anio`, `desde`, `hasta`, `nivel` (extremo; «dentro de» siempre Todo el Perú) | Sin `paso`: el formulario del paso 2 solo con los campos de esa intención. Con `paso=2`: arma la consulta mínima (`pregunta_original` con una plantilla de `textos.yaml`) y responde igual que `POST /preguntar` (respuesta, aclaración o aviso, mismo estado HTTP) |

`periodo`: `{anio}` si se escribió el año y si no `{ultimo}`; en `evolucion`, `{serie, desde?, hasta?}`. Errores de llenado (falta el lugar, lugar y «Todo el Perú» a la vez, año que no es de cuatro cifras, nivel inválido) vuelven al paso 2 con 422 y su texto, sin llamar al motor. Una combinación sin fila en `intenciones.yaml` no se oculta: el motor responde su «no se puede».
