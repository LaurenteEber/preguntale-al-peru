# S3-04 — Páginas: pregunta, respuesta y aclaración

## Tareas

1. **Plantillas:**
   - Jinja2, en `src/pap/web/plantillas/`.
   - Textos de la interfaz (títulos, botones, ayudas, ejemplos, mensajes de error) en `curados/web/textos.yaml`.
   - Rótulos de sección desde `curados/motor/textos/capas.yaml` → `rotulos` (S3-01).
   - Desde S3-04, la página de inicio enlaza al formulario guiado (`/guiado`), que lo construye S3-05.
2. **Seguridad desde el primer HTML** (antes del JavaScript del punto 6):
   - `Content-Security-Policy` sin orígenes externos (`default-src 'self'`);
   - nada de terceros: ni fuentes, ni scripts, ni analítica;
   - sin cookies.
3. **Inicio** (`GET /`):
   - caja de pregunta;
   - 3 o 4 ejemplos tocables;
   - una línea con los temas de hoy y de dónde salen los datos.
4. **Respuesta** (`POST /preguntar`, formulario HTML, sin JavaScript obligatorio). Bloques en este orden; cada uno sale de un campo de `respuesta.json` y se omite si el campo no viene:

   | # | Bloque | Campo |
   |---|---|---|
   | 1 | Entendimos | `entendimos` (vía texto) |
   | 2 | Respuesta corta | `capa1.respuesta_corta` (en «no se puede» va primero, R-04) |
   | 3 | Cifra clave y su fuente | `capa1.cifra_clave` |
   | 4 | Lo más cercano que sí tenemos | `capa1.lo_mas_cercano`, `alternativas` y `temas_disponibles` («no se puede») |
   | 5 | Ojo al leer | `capa1.ojo_al_leer` |
   | 6 | Confianza | **solo `capa1.confianza.texto`**, sin color ni clase CSS por nivel; nunca el rótulo técnico de la ficha (R-05) |
   | 7 | ¿Qué puedo hacer? | `capa1.que_hacer` (con su nota si no está revisado) |
   | 8 | `<details>` Más contexto | `capa2.mas_contexto`, `capa2.avisos` y `capa2.limites` |
   | 9 | `<details>` Para citar y verificar | `capa3.para_citar` (con su `url`, S3-01), `capa3.glosario` y el rótulo de versión |

   **Sin bloque de «ficha técnica»:** es para auditoría (`contrato_respuesta.md`).
5. **Aclaración:**
   - Muestra la pregunta y un botón por opción.
   - Cada botón **reenvía la misma entrada con `elegir` acumulado**:
     - si la pregunta vino por texto, `{texto, elegir}`: usa la caché de 24 h del slice 2, que no reinterpreta;
     - si vino del formulario, `{consulta, elegir}`.

     La entrada viaja en campos ocultos del formulario. Así, la respuesta final es la misma que da `--texto … --elegir` y conserva `entendimos`.
   - Si la caché venció, sale el mensaje del slice 2 («la pregunta venció; escríbela de nuevo»), con la caja de texto.
6. **Mensajes** (`tipo: mensaje`): el texto fijo. Si el LLM no está disponible o se llegó al tope, lleva el enlace al formulario guiado.
7. **«Buscando…»:** al enviar, el botón se desactiva y aparece «Buscando…». Es el único JavaScript, desde un archivo propio (`/estatico/app.js`), y la página funciona igual sin él.
8. **Estilo:**
   - un solo CSS propio;
   - móvil primero;
   - letra base ≥ 16 px;
   - contraste AA en modo claro y oscuro (`prefers-color-scheme`).
9. **Pruebas:**
   - Orden de los bloques para Q1–Q4 y para un «no se puede».
   - Confianza sin clase por nivel y sin el rótulo de la ficha.
   - Aclaración con dos lugares, `elegir` acumulado de «1» a «1,2».
   - Funciona sin JavaScript (petición sin JS).
   - **Ningún número fuera del JSON:**
     - se toma el texto de todos los nodos del `<body>`, incluido el contenido de `<details>` cerrados, sin `script`, `style` ni atributos;
     - se extraen los números con `\d[\d  .,]*`;
     - cada uno tiene que aparecer, como cadena, en algún texto ya escrito del JSON (`entendimos`, campos de texto de `capa1` a `capa3`, rótulo de versión) o de los YAML de textos;
     - **no valen** los campos numéricos crudos del JSON (`valor`, `ic_inf`…) ni la huella;
     - lo que repite la pregunta de la persona se comprueba aparte: solo puede aparecer en el bloque «Entendimos» o en el eco de la aclaración, marcado como lo que ella escribió.

## Criterios de aceptación

- [x] La prueba de números está en verde para Q1–Q4, la matriz reducida y el conjunto con grabaciones.
- [x] Ningún texto visible escrito en HTML ni en Python.
