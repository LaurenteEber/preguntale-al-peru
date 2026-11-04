# S3-07 — Privacidad, abuso y costo

**Se deriva de P-03, P-05 y P-07.** Los límites son parámetros de experiencia (tipo B): el agente los fija como `supuesto: S3-07` (propuesta: 10 preguntas por minuto por IP y 300 llamadas al LLM por día).

## Tareas

1. **Registros** (`src/pap/web/registro.py`):
   - el acceso guarda solo método, ruta, código y tiempo;
   - los errores guardan el tipo de excepción y su código, **sin** el mensaje ni la traza cuando pueden contener la entrada (los mensajes de consulta repiten el lugar escrito);
   - un manejador global evita que una excepción no capturada deje la entrada en el registro de uvicorn;
   - la web no escribe `respuesta.json` en disco.
2. **Límites** (`curados/web/parametros.yaml`, `supuesto: S3-07`):
   - Por IP: N preguntas por minuto → mensaje fijo «Espera un momento».
   - **Tope diario de llamadas al LLM:** cuenta las llamadas reales, reintentos incluidos; los aciertos de caché no cuentan; el día es el de Lima (`America/Lima`). Al llegarlo, la caja de texto avisa y lleva al formulario guiado, que sigue respondiendo.
   - Los contadores viven en memoria y se reinician al reiniciar, lo que basta en local (P-05). En el slice 4 se revisan.
3. **Tamaño:** cuerpo ≤ 8 KB; el texto se recorta según el slice 2.
4. **Pruebas:**
   - **Marcador:** se envían 50 preguntas, por texto (con LLM falso) y por formulario, con una cadena marcadora puesta **en una premisa**, fuera de lugares y temas, para que no sea un ancla. Luego se busca en:
     - los registros de acceso y de error;
     - las trazas;
     - los archivos nuevos de `salidas/` y del directorio de trabajo.

     No debe aparecer. **La caché de interpretaciones (24 h, P-03) queda excluida** de la búsqueda y se nombra en la evidencia.
   - Una excepción forzada con el marcador en el lugar: el registro guarda el tipo, no el texto.
   - Límite por IP; tope diario con un reloj falso que cambia de día; cabeceras presentes (S3-04); cuerpo grande rechazado.

## Criterios de aceptación

- [ ] El marcador no aparece fuera de la caché permitida.
- [ ] Al llegar al tope, el texto libre se desactiva y el formulario sigue respondiendo.
