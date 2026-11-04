# S3-03 — Servicio: FastAPI sobre el mismo motor

**Se deriva de F-05 y `stack.md`** (FastAPI + DuckDB en solo lectura).

## Tareas

1. **Dependencias:** `uv add fastapi uvicorn python-multipart jinja2`. `uv.lock` cambia solo por estas y sus dependencias.
2. **Aplicación:** `src/pap/web/app.py` con `crear_app(raiz, *, llm=None, dir_cache=None, precalentar=True)`. `llm` y `dir_cache` se pasan al intérprete con el adaptador de S3-00, para las pruebas con grabaciones.
3. **Arranque:**
   - se cargan el contexto y el `Motor` (unos 1,1 s);
   - el **precalentamiento corre en un hilo aparte**: responde las consultas de `curados/web/precalentar.yaml` (Q1–Q4 y una por intención, sacadas de la matriz);
   - mientras corre, `/salud` responde 503 «preparando» y las preguntas, el mensaje fijo «Estamos preparando el servicio…».
4. **Concurrencia:** un solo proceso. **Un candado envuelve toda llamada a `interpretar()` o `preguntar_minima()`.** El slice 2 no separa la llamada al LLM del motor, así que el LLM queda dentro del candado. En local (P-05) basta; en el slice 4 se revisa. Las cachés perezosas del motor solo se tocan con el candado tomado.
5. **Rutas:**

   | Ruta | Entrada | Salida |
   |---|---|---|
   | `POST /api/preguntar` | JSON `{texto, elegir?}` o `{consulta, elegir?}`. `elegir` es una lista de números, acumulada en el orden de las aclaraciones | El `respuesta.json` sin cambios |
   | `GET /api/opciones` | — | Temas, intenciones, niveles y ejemplos, de los YAML del motor y de `curados/web/textos.yaml` |
   | `GET /api/version` | — | `Motor.version()` más un rótulo legible armado en `textos.yaml`: «Biblioteca {huella corta del cubo}, construida el {fecha}» |
   | `GET /salud` | — | `ok` o `preparando` |

   - **Sin GET que lleve la pregunta.**
   - Errores: `ConsultaInvalida` y `EleccionInvalida` traen textos pensados para la terminal («repite el comando con --elegir…»). La web **no los muestra**: responde con mensajes propios de `curados/web/textos.yaml` según el tipo de excepción y su `codigos` cuando lo tenga. El detalle va al registro, sin la pregunta (S3-07).
   - Códigos HTTP: tabla en `docs/especificaciones/api.md` (nuevo), derivada de `cli.codigo_salida` y del tipo `mensaje`.
6. **Parámetros:** `curados/web/parametros.yaml` (puertos, tiempos máximos, límites, objetivos), cada uno con `decision:` o `supuesto: S3-xx`.
7. **Imports permitidos** en `src/pap/web/`:
   - `pap.motor.validador.contexto.cargar_contexto`;
   - `pap.motor.respuesta.Motor`;
   - `pap.motor.preguntar` (`preguntar_minima`, `EleccionInvalida`);
   - `pap.motor.consulta.ConsultaInvalida`;
   - `pap.motor.plantillas` (`textos`, `parametros`);
   - `pap.motor.formato` (solo para S3-04, si hace falta);
   - el intérprete del slice 2 (`interpretar` y su adaptador).

   Una prueba lee los imports y falla con cualquier otro de `pap.motor` o `pap.capa0`.
8. **Pruebas** (`tests/web/`, `TestClient`, sin red ni clave):
   - **Equivalencia:** `POST /api/preguntar` devuelve **exactamente** el JSON de `evidencia/base_api/` (S3-02) para todos sus casos, **sin exclusiones**. En la vía por texto, cada comparación usa una carpeta de caché nueva (`dir_cache` temporal), para que el campo del slice 2 que dice si la interpretación vino de la caché salga igual que en la base. Si otro campo cambia entre corridas (no debería), se nombra y se justifica en la evidencia.
   - `elegir` acumulado en una comparación con dos aclaraciones.
   - `/salud` antes y después del precalentamiento.
   - Las excepciones dan mensajes de `textos.yaml`, nunca «--elegir».
   - No hay GET con texto.
   - El candado: dos peticiones simultáneas dan las mismas respuestas que en serie.

## Criterios de aceptación

- [ ] La equivalencia sin exclusiones está en verde.
- [ ] Ningún texto de la terminal llega a una respuesta HTTP.
- [ ] La prueba de imports está en verde.
