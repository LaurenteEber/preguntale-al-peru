# S2-01 — Contrato de la interpretación

## Por qué

La frontera con el LLM tiene que ser estrecha y comprobable. El LLM devuelve una **interpretación**: la consulta más las **anclas**, es decir, el fragmento literal de la pregunta que justifica cada valor. Así, el código rechaza todo valor que la persona no haya escrito (`agents.md` §6, criterio 1).

## Tareas

1. **Esquema propio:** `curados/motor/esquemas/interpretacion.schema.json`.
   - Reutiliza por `$ref` los `$defs` de `consulta_minima.schema.json` que sirvan (`anio`).
   - **No** usa `allOf` sobre la consulta mínima: esa exige `intencion` y `territorio`, y aquí pueden faltar para que el código aplique `sin_lugar` y `sin_intencion`.
   - `consulta_minima.schema.json` no cambia.
2. **`resultado`**, uno de:

   | `resultado` | Contiene |
   |---|---|
   | `consulta` | `consulta` y `anclas` |
   | `aclaracion` | `motivo` (`intencion_ambigua` o `varias_preguntas`) y `opciones`: 2 o más consultas completas, cada una con sus anclas |
   | `fuera_de_alcance` | `tipo` (`tema` para un tema que no tenemos; `pregunta` para una pregunta que el motor no responde: un «por qué», una proyección, una opinión) y `pedido` (ancla literal) |
   | `no_es_pregunta` | — |
   | `otro_idioma` | — |

   Las aclaraciones por falta de lugar o por año relativo **no las produce el LLM**: el LLM omite el valor y el código arma la aclaración (S2-05).
3. **La consulta de la interpretación:**
   - `intencion`: opcional, mismo `enum`.
   - `tema`: opcional, mismo `enum`; sin `indicador`.
   - `territorio` y `comparar_con`: opcionales, con dos formas: `{texto}` (sin dígitos, `pattern`) o `{nacional: true}`. Sin ubigeo ni ámbito.
   - Con `identificar_extremo`: `{nivel, dentro_de?}`, y `dentro_de` con las mismas dos formas.
   - `periodo`: las formas de siempre.
   - Sin `pregunta_original` ni `idioma`: los pone el código.
4. **Anclas:** `territorio`, `comparar_con`, `dentro_de`, `nivel`, `anio` (o `desde` y `hasta`), `tema` e `intencion`. Una por cada valor presente. `pedido` no puede tener dígitos.
5. **Sección `interprete:` en `curados/motor/parametros_motor.yaml`**, con los defaults del README marcados `supuesto: S2-01`. La amplían las historias siguientes.
   - El número máximo de opciones se valida en el código contra `interprete.aclaracion_max_opciones`, no en el esquema, para que el dueño lo cambie en una línea.
6. **Mensajes:**
   - Los códigos de error nuevos (`x-error`) van con sus textos a `curados/motor/textos/errores_consulta.yaml`.
   - `otro_idioma` reutiliza el texto existente de `idioma_invalido`.
   - Los demás textos van a `curados/motor/textos/interprete.yaml` (nuevo).
7. **Pruebas** (`tests/interprete/__init__.py` y `tests/interprete/test_contrato.py`):
   - un caso válido y uno inválido por cada `resultado` y por cada restricción del punto 3;
   - las cuatro consultas de `curados/motor/consultas_minimas/`, **sin `pregunta_original` ni `idioma`** y con anclas inventadas para la prueba, validan;
   - Q4 (`identificar_extremo`, `dentro_de: {nacional: true}`) también valida.

## Criterios de aceptación

- [ ] El esquema acepta los cinco resultados y rechaza ubigeo, ámbito, `indicador`, `pregunta_original`, `idioma` y dígitos en el texto de un lugar.
- [ ] `git diff -- curados/motor/esquemas/consulta_minima.schema.json` vacío.
- [ ] La sección `interprete:` existe; ningún texto visible nuevo está en Python.
