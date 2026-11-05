# Especificación — Intérprete de preguntas en texto libre (slice 2)

Vigente desde el 5/11/2026. Historias: `backlog/slice-2/S2-01` a `S2-06`. Decisiones: P-01, P-03, P-07, T-03.

## 1. Contrato de la interpretación (S2-01)

Esquema: `curados/motor/esquemas/interpretacion.schema.json`. El LLM devuelve uno de cinco resultados:

| `resultado` | Qué trae | Qué hace el código |
|---|---|---|
| `consulta` | `consulta` (como la consulta mínima, con intención y territorio opcionales, sin `pregunta_original` ni `idioma`) y `anclas` | Valida, ancla, completa o aclara lo que falta y llama a `preguntar_minima()` |
| `aclaracion` | `motivo` (`intencion_ambigua` o `varias_preguntas`) y `opciones` (consultas completas con sus anclas) | Opciones ordenadas alfabéticamente, cada una con su «Entendimos» como etiqueta |
| `fuera_de_alcance` | `tipo` (`tema` o `pregunta`) y `pedido` (palabras literales) | «No se puede» del motor (`tema_fuera_del_piloto` o `interprete_fuera_de_alcance`) |
| `no_es_pregunta` | — | Mensaje fijo con la vía estructurada |
| `otro_idioma` | — | Mensaje fijo con la vía estructurada |

**Anclas.** Cada valor de la consulta necesita en `anclas` un fragmento **literal** de la pregunta limpia, en palabras enteras y
seguidas (sin tildes ni mayúsculas; «del» = «de el»), que lo justifique: el lugar copiado tal cual, `nacional` si el ancla
contiene un texto de todo el país, el nivel si el ancla nombra el nivel (o su plural), el año si el ancla lo contiene. Un
valor sin ancla válida se descarta (`interpretacion.descartados`) y se trata como si faltara.

**Lo que falta** (parámetros de `interprete`): sin lugar → aclaración «Todo el Perú / Escribe el lugar» (`sin_lugar`); sin
intención → `nivel_actual` (`sin_intencion`); año relativo o sin ancla → aclaración «El último año con datos / Escribe el
año» (`anios_relativos`, también cuando el LLM omite un año relativo que la pregunta trae, `anios_relativos_frases`).

**Fallas.** Salida inválida → un reintento con el error (`reintentos_si_no_valida`); si vuelve a fallar, mensaje «no
entendimos». Sin clave, caída, tiempo agotado, límite de gasto o tope → mensaje «no disponible». Nunca una respuesta adivinada.

## 2. CLI `--texto` (S2-06)

- `uv run pap preguntar --texto "<pregunta>" [--elegir N[,M]] [--salida <carpeta>]`. `--texto` no se combina con archivos,
  con las opciones directas ni con `--plan`.
- Salida: «Entendimos: …» primero (en `respuesta.json`, la primera clave; en el `.md`, el primer párrafo) y luego la
  respuesta por capas. Una aclaración imprime la pregunta, las opciones y la pista de `--elegir`. Un recorte de la pregunta
  imprime el aviso como primera línea.
- Códigos de salida: los de `cli.codigo_salida` (respondida 0, no se puede 1, aclaración y mensaje 2, error de uso 64).
- `respuesta.json` lleva `interpretacion` (resultado, modelo, `version_prompt`, reintentos, caché, consulta, anclas,
  descartados, avisos, datos personales quitados) y `entendimos`.

## 3. Equivalencia

La respuesta por `--texto` es igual a la de `preguntar_minima(consulta producida, con la misma pregunta_original)`,
salvo `interpretacion`, `entendimos` y las rutas. La vía estructurada no cambió con el slice 2.
