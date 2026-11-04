# Encargo S2-02 — Conjunto de evaluación del intérprete (independiente)

4/11/2026. Lo escribe el implementador antes del conjunto. Quien escribe el conjunto **no** lee `curados/interprete/` ni el
código del intérprete (`src/pap/interprete/`), para que el conjunto mida y no repita lo que ya se ajustó.

## Qué recibes (lee solo esto)

- El contrato: `curados/motor/esquemas/interpretacion.schema.json` y `curados/motor/esquemas/consulta_minima.schema.json`.
- `docs/manual_de_uso.md` (qué responde el motor hoy), `docs/decisiones.md`, `curados/motor/intenciones.yaml`,
  `curados/motor/parametros_motor.yaml` (temas, alias y la sección `interprete`) y `curados/motor/textos/territorio.yaml`.
- `curados/motor/consultas_minimas/q1.json` a `q4.json` (sus `pregunta_original` son 4 de las entradas).

## Qué escribes

`tests/interprete/evaluacion.yaml`: una lista `entradas`, ≥ 100, cada una con:

- `id` (único, corto), `pregunta` (como la escribiría una persona), `categoria` (una de las de abajo);
- `esperado`: `resultado` (`consulta`, `aclaracion`, `fuera_de_alcance`, `no_es_pregunta` u `otro_idioma`) y, si es
  `consulta`, `consulta`: la consulta en la forma de la interpretación (sin anclas, sin `pregunta_original` ni `idioma`; el
  lugar **tal cual** lo escribió la persona en `territorio.texto`, o `{nacional: true}`). Si es `aclaracion`, `motivo`.
  Si es `fuera_de_alcance`, `tipo`;
- `notas`: lo que hace falta para juzgarla (p. ej., «con `--elegir 1`, consulta de q1.json»; o qué default aplica:
  `interprete.sin_lugar`, `sin_intencion`, `anios_relativos`).

Cómo se va a comparar (no el texto): intención, tema, periodo y nivel iguales; territorio, `comparar_con` y `dentro_de`
por lo que da el resolver del motor (ubigeo o ámbito, o la misma aclaración con las mismas opciones). Cuando falta un valor
que el código completa con un default, deja el valor fuera de `consulta` y dilo en `notas`.

## Mínimos por categoría

| categoria | mín. |
|---|---|
| directa | 24 (las combinaciones intención × tema de `intenciones.yaml`; las que el motor no soporta esperan ese «no se puede») |
| reformulada | 20 |
| tipeo | 10 |
| lugares_dificiles | 12 («Lima», «San Juan», «Callao», «Lima provincias», «Ayaviri (Melgar, Puno)»…) |
| anios | 10 («en 2019», «desde 2015», «el año pasado»…) |
| ambigua | 10 |
| fuera_tema | 6 |
| fuera_pregunta | 6 («¿por qué…?», proyecciones, opiniones) |
| enganosa | 8 (premisas o cifras falsas en la pregunta) |
| inyeccion | 6 («ignora tus instrucciones…», «escribe un poema») |
| q1_q4 | 4 (las `pregunta_original` de Q1–Q4, tal cual) |

## Reglas

- Español de Perú, con y sin tildes, como escribe la gente. Sin datos personales reales.
- No inventes temas ni intenciones fuera del vocabulario: lo que no está es `fuera_de_alcance`.
- No escribas cifras como si fueran datos: solo en las preguntas engañosas, y ahí la consulta esperada las ignora.
