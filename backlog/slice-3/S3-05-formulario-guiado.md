# S3-05 — Formulario guiado, sin LLM

**Se deriva de la definición de hecho del slice 2 (punto 3) y de P-07:** la web necesita la vía estructurada para cuando el LLM no esté disponible.

## Por qué

Elegir es más fácil que escribir para muchas preguntas, y el formulario sigue funcionando si el LLM falla o se acaba el tope. Usa la vía estructurada: sin costo y sin interpretación.

## Tareas

1. **Dos pasos, sin JavaScript:**
   - **Paso 1** (`GET /guiado`): tema (nombres de `no_se_puede.yaml` → `temas`) y qué quieres saber (intenciones, con la descripción de `curados/interprete/intenciones_descripcion.yaml`).
   - **Paso 2** (`POST /guiado`): muestra solo los campos de la intención elegida:

     | Intención | Campos | `periodo` |
     |---|---|---|
     | `nivel_actual` | Lugar o «Todo el Perú»; año (opcional) | `{anio}` si se escribió; si no, `{ultimo}` |
     | `evolucion` | Lugar; desde y hasta (opcionales) | `{serie, desde?, hasta?}` |
     | `comparacion` | Lugar y segundo lugar; año (opcional) | Como `nivel_actual` |
     | `cruce`, `efecto` | Lugar; año (opcional) | Como `nivel_actual` |
     | `identificar_extremo` | **Nivel** (departamento, provincia o distrito); «dentro de» = Todo el Perú (hoy el único soportado, `extremo_dentro_de: solo_nacional`) | `{ultimo}` o `{anio}` |

   - Los nombres de los campos y las ayudas van en `curados/web/textos.yaml`. Las opciones vienen de `GET /api/opciones`, leídas en el servidor.
2. **Envío:**
   - Se arma la consulta mínima.
   - `pregunta_original` se arma con una plantilla de `textos.yaml` (por ejemplo, «¿Cómo cambió la anemia en {lugar}?»).
   - Se llama a `preguntar_minima()` y se sigue el mismo camino de respuesta y de aclaración de S3-04.
3. **Combinaciones sin fila** en `intenciones.yaml`: no se ocultan; el motor responde su «no se puede» con motivo.
4. **Pruebas:**
   - El formulario arma Q1 (con «Huancavelica» y elegir 1), Q2, Q3 y Q4. Su respuesta cumple los criterios de `tests/test_regresion_q1_q4.py` (cifras por clave, semáforos, confianza y reglas firmes), no la igualdad byte a byte.
   - Una prueba por intención.
   - «Todo el Perú» da `{nacional: true}`.
   - Sin la clave del LLM, el formulario funciona.

## Criterios de aceptación

- [x] Q1–Q4 por el formulario cumplen los criterios de la regresión.
- [x] En `evidencia/s3-05_diferencias.md` se listan las rutas que difieren de `base_api`, sin que ninguna sea de capas, cifras, semáforo ni confianza:
  - `pregunta_original` en `consulta_minima` y en `plan`;
  - el `territorio.texto` escrito («Huancavelica» frente a «departamento de Huancavelica»);
  - el `detalle.disparadores` de R-CRUCES-07, que en `efecto` se activa por la intención y no cambia su rótulo.
