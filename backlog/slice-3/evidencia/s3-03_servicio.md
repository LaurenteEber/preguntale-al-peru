# S3-03 — Servicio FastAPI sobre el mismo motor: evidencia

5/11/2026. Código en `src/pap/web/app.py`; textos y parámetros en `curados/web/`; especificación en `docs/especificaciones/api.md`; pruebas en `tests/web/test_servicio.py`.

## Criterios de aceptación

- [x] **Equivalencia sin exclusiones.** `test_equivalencia_via_estructurada[q|matriz]` (5 + 60 casos) y `test_equivalencia_via_texto_con_cache_nueva_por_comparacion` (los 140 casos de la evaluación, con una carpeta de caché nueva por comparación y las grabaciones en modo «reproducir») comparan el JSON de `POST /api/preguntar` con `evidencia/base_api/` igualdad exacta. Ningún campo cambió entre corridas, así que no hay nada que justificar.
- [x] **Ningún texto de la terminal llega a una respuesta HTTP.** `test_errores_con_textos_de_la_web_sin_texto_de_terminal` y `test_eleccion_invalida_usa_el_texto_de_la_web`: ni «--elegir» ni «comando» en ninguna respuesta de error; los mensajes salen de `curados/web/textos.yaml`.
- [x] **Prueba de imports.** `test_imports_permitidos_en_pap_web` lee los imports de `src/pap/web/` y falla con cualquier `pap.motor` / `pap.capa0` fuera de la lista del punto 7 (más el adaptador `pap.interprete.llm` y `pap.interprete.interpretar`).

## Otras pruebas

- `elegir` acumulado con dos aclaraciones (Ayaviri contra Ayaviri): `[]` y `[1]` dan aclaración, `[1, 2]` responde.
- `/salud` y las preguntas: 503 «Estamos preparando el servicio…» mientras corre el precalentamiento (hilo aparte) y 200 después.
- Sin `GET` con la pregunta: la prueba revisa las rutas; `GET /api/preguntar` da 405.
- Candado: ocho peticiones simultáneas dan lo mismo que en serie; otra prueba comprueba que `preguntar_minima` se llama con el candado tomado.
- `/api/opciones` y `/api/version` (rótulo «Biblioteca {huella corta}, construida el {fecha}»).

## Comandos

- `uv run pytest -q tests/web -p no:cacheprovider`: 13 pasan.
- Suite completa: ver el final de este archivo.

## Notas

- La rama de S3-03 se fusionó con la de S3-01/S3-02 (`965280f`) porque la base de la web sale del motor con las decisiones de S3-01.
- El intérprete usa su registro de uso por defecto (`salidas/interprete/uso.jsonl`, desactivado en pytest); S3-07 decide cómo se registra en la web.
- Supuestos nuevos: S3-03-a a S3-03-d en `consultas_al_dueno.md`.
