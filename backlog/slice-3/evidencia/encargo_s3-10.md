# Encargo S3-10 — Revisor de usuario en el celular

Quién: un subagente nuevo, sin la conversación del implementador. No edita código, datos, textos ni pruebas. Usa la web como la usaría una persona en su celular, toma capturas y entrega su informe.

**No leer:** `src/pap/web/`, `curados/web/`, `curados/interprete/`, `src/pap/interprete/`, `tests/` ni `backlog/` (salvo este encargo y la línea 4 de `backlog/slice-1/evidencia/revision_usuario.md`, con las personas). Sí puede leer `docs/manual_de_uso.md` y `docs/especificaciones/contrato_respuesta.md`.

## Qué hacer

1. **Personas:** las de las revisiones anteriores (`backlog/slice-1/evidencia/revision_usuario.md`, línea 4): madre de Huancavelica o Puno, periodista, regidor o funcionario, estudiante o docente.
2. **Preguntas:** 20 propias, antes de abrir la web. Son 10 para escribir en la caja de texto y 10 para armar con el formulario guiado («elegir paso a paso»). Tratan de anemia, desnutrición crónica, pobreza y gasto público en lugares del Perú, con tus palabras: cuánto hay, cómo cambió, comparar dos lugares, dónde es más alto, si el gasto tuvo efecto. Incluye alguna ambigua y alguna con un lugar homónimo o mal escrito. Inventadas: ningún dato personal real. Se guardan en `backlog/slice-3/evidencia/preguntas_s3-10_usuario.yaml` con la forma `entradas: [{id: w01, persona: …, via: texto|formulario, pregunta: "…"}]`.
3. **Levantar la web en este equipo:** `uv run pap servir --puerto 8765`, en segundo plano y solo en 127.0.0.1 (nunca `--red-local`). Espera a que `http://127.0.0.1:8765/salud` dé 200. Al terminar, detén el proceso.
4. **Usar la web con Playwright** (Python, `uv run python`, Chromium ya instalado), con una ventana de 360 × 780 px y `is_mobile=True`. Toca los ejemplos, escribe en la caja, envía y resuelve las aclaraciones tocando la opción que elegiría la persona. Abre «Más contexto» y «Para citar y verificar», y sigue un enlace a la fuente oficial: solo comprueba que el enlace existe y a dónde lleva, no hace falta abrirlo. Prueba también el formulario guiado. Toma una captura por pregunta (PNG, solo la ventana, no la página entera) en `backlog/slice-3/evidencia/s3-10/`.
5. **Costo:** las preguntas por texto llaman al LLM en vivo. Como mucho 15 envíos por texto en total, contando las aclaraciones y los ejemplos tocados. El tope total es US$ 0,50; si te acercas, detente. El costo sale de lo que crece `salidas/interprete/uso.jsonl` (cuéntalo antes y después). El formulario no usa el LLM.
6. **Nunca** muestres, imprimas ni busques variables de entorno (nada de `env`, `printenv`, `echo $…`, `set -x`). La clave ya está cargada.

## Preguntas que guían la revisión

- ¿Entiende la persona qué se le respondió? ¿Contesta lo que preguntó?
- ¿Encuentra la fuente y el documento oficial?
- ¿Entiende la confianza sin color?
- ¿Sabe qué hacer con una aclaración o con un «no se puede»?
- ¿Algo la lleva a una conclusión falsa?
- En el celular: ¿se lee sin zoom, se toca bien, se ve «Buscando…» mientras espera?

Clasificación de los hallazgos:
- **bloqueante:** la lectura natural es falsa;
- **alto:** una persona probable lo entiende mal;
- **medio:** confunde, pero el texto lo aclara;
- **bajo:** estilo.

## Qué entregar

`backlog/slice-3/evidencia/revision_usuario_s3.md`, en español, con:
- el veredicto: «apto», «apto con observaciones» o «no apto»;
- la tabla de las 20 preguntas: id, persona, vía, resultado (respuesta, aclaración, no se puede o mensaje) y captura;
- los hallazgos numerados, cada uno con su clasificación, la pregunta (por id), la frase exacta, la captura y una propuesta;
- el costo en vivo.

Escribe el archivo tú mismo y devuelve un resumen corto.
