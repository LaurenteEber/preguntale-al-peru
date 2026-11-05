# S3-00 — Interfaces del slice 2 que usa la web

5/11/2026, sobre `main` en `e1a0d0f` (slice 2 cerrado).

| Qué se necesita | Dónde está | Qué hay | ¿Hace falta adaptar? |
|---|---|---|---|
| Firma de `interpretar()` | `src/pap/interprete/interpretar.py:420` | `interpretar(texto, motor, *, elegir=None, llm=None, cache_dir=None, registro=DEFECTO) -> dict` | No |
| LLM falso o grabaciones | mismo archivo, `llm=` | Cualquier objeto con `interpretar_crudo(prompt, pregunta_limpia, version_prompt, error_previo=None)`: `pap.interprete.llm.Cliente(raiz, modo="reproducir")` reproduce las grabaciones; las pruebas usan un falso (`tests/interprete/test_interpretar.py:34`) | No |
| Cliente por defecto | `interpretar.py:413` (`_cliente`) | `Cliente(raiz, modo="vivo")`; `PAP_INTERPRETE_MODO=completar` solo para grabar preguntas de prueba | La web pasa su propio cliente (`llm=`) para contar llamadas y aplicar su tope diario (S3-07): adaptador en `src/pap/web/` (tipo A) |
| Carpeta de la caché | `interpretar.py:218` (`_carpeta_cache`) | `cache_dir=` o `interprete.cache_carpeta` (`salidas/interprete/cache`); en pytest, una carpeta temporal (`_CACHE_PYTEST`, línea 38) | No |
| Registro de uso | `interpretar.py:420`, `registro=` | Ruta de `uso.jsonl` (P-03), o None | No |
| Forma del tipo `mensaje` | `interpretar.py:243-252` (`_mensaje`) | `{"tipo": "mensaje", "motivo": <no_es_pregunta · otro_idioma · no_entendida · no_disponible · volver_a_preguntar>, "texto", "cifras": {}}`. **El código ya viene, en `motivo`** | No: se usa `motivo` (no hace falta agregar `codigo`) |
| Aclaración | `interpretar.py` (`_aclaracion`) y `pap.motor.preguntar` | `{"tipo": "aclaracion", "aclaracion": {"motivo", "pregunta", "opciones": [{"n", "etiqueta", …}]}}`; se responde repitiendo con `elegir` (un número o una lista) | No |
| Vía estructurada | `src/pap/motor/preguntar.py:548` | `preguntar_minima(motor, entrada, *, elegir=None, solo_plan=False) -> dict` | No |
| Códigos de salida | `curados/motor/parametros_motor.yaml:123` | `cli.codigo_salida`: respondida 0, no_se_puede 0, aclaracion 2, mensaje 2, no_disponible 3, error 1 | Se leen tal cual (la web los traduce a su estado HTTP en S3-03) |

## Pruebas permanentes del slice 2 que comparan contra archivos fijos (punto 4)

S3-01 y S3-02 las actualizan con la misma aprobación del dueño que el cambio que las mueve:

- `tests/test_cli_preguntar.py::test_via_estructurada_igual_a_la_base_de_s2_00`: compara contra `backlog/slice-2/evidencia/base_estructurada/` (también compara `commit_cubo`, que cambia si se recalcula el cubo en otro commit: en la nube se deja el manifiesto versionado).
- `tests/test_regresion_q1_q4.py` y `tests/interprete/test_cli_texto.py::test_q1_q4_por_texto_con_grabaciones`: comparan contra las referencias de Q1–Q4 del slice 1.
- `tests/interprete/test_evaluacion_grabada.py` y `test_robustez.py`: reproducen `tests/interprete/grabaciones/`. Un cambio del motor no las invalida (la huella es pregunta, modelo y prompt), pero sí cambia las respuestas que se comparan con la vía estructurada.

Los reportes de evaluación y la base estructurada del slice 2 son evidencia histórica: no se regeneran.
