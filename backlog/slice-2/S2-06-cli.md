# S2-06 — CLI `--texto`

## Por qué

Es la primera forma de usar el intérprete de punta a punta, y la base de la revisión temprana (S2-07).

## Tareas

1. **`pap preguntar --texto "¿Cuánta anemia hay en Puno?"`.**
   - Excluyente con los archivos y con `--intencion`, `--tema`, `--territorio`…; combinarlos es un error de uso con mensaje.
   - `--elegir` según S2-05 §2.
   - Mensajes en `curados/motor/textos/cli.yaml`.
2. **Códigos de salida.** `cmd_preguntar` deja de usar su diccionario fijo y lee `cli.codigo_salida` de `parametros_motor.yaml`, al que se agregan las filas nuevas:

   | Resultado | `tipo` en el JSON | Código | ¿Escribe `respuesta.json` y `.md`? | Texto |
   |---|---|---|---|---|
   | Respuesta / no se puede (incluye fuera de alcance) | `respuesta` / `no_se_puede` | 0 | sí | El del motor, con `entendimos` primero |
   | Aclaración (intérprete o territorio) | `aclaracion` | 2 | no (como hoy) | Pregunta y opciones |
   | `no_es_pregunta`, `otro_idioma`, `no_entendida` | `mensaje` | 2 | no | `interprete.yaml` / `idioma_invalido`, siempre con la vía estructurada como salida |
   | `no_disponible` (sin clave, caída, tiempo, límite) | `mensaje` | 3 | no | `interprete.yaml` |
   | Error de uso | — | 1 | no | `cli.yaml` |

   El aviso de recorte (S2-04) va como una línea más, antes de la respuesta.
3. **`respuesta.json`:**
   - campo `entendimos`, **fuera de las capas**: no cuenta para `capa1_palabras_max`; el `.md` lo imprime primero;
   - bloque `interpretacion`: `resultado`, consulta producida, anclas, modelo, `version_prompt`, reintentos y si vino de la caché;
   - lo que se guarda de la pregunta, según X-14.
4. **Contrato:** agregar a `docs/especificaciones/contrato_respuesta.md`:
   - el campo `entendimos`;
   - el tipo `mensaje`;
   - los motivos `interprete_*` de `aclaracion`;
   - el motivo `interprete_fuera_de_alcance`.

   Es una extensión: lo existente no cambia.
5. **Pruebas** (`tests/test_cli_preguntar.py` extendido, con grabaciones):
   - una por fila de la tabla;
   - Q1–Q4 por `--texto` (Q1: aclaración y luego `--elegir 1`);
   - combinar opciones da error;
   - el corrector no tiene infracciones en `entendimos` ni en los textos de `interprete.yaml`.

## Criterios de aceptación

- [ ] Q1–Q4 por `--texto` (con `--elegir` donde corresponde) cumplen los criterios de `test_regresion_q1_q4.py`.
- [ ] Vía estructurada: los `respuesta.json` coinciden con `evidencia/base_estructurada/` (S2-00), salvo rutas.
- [ ] Códigos de salida leídos del YAML; `no_disponible` sale con 3.
