# S3-05 — Diferencias de Q1–Q4 por el formulario frente a `base_api`

Se envió cada consulta por `POST /guiado` (paso 2) y se comparó el `respuesta.json` con `backlog/slice-3/evidencia/base_api/q/<q>/respuesta.json`, ruta por ruta. Lo hace `tests/web/test_guiado.py::test_diferencias_con_la_base_api_solo_las_permitidas`.

Datos del formulario: Q1 «Huancavelica» (evolución, anemia); Q2 «Ayaviri, Melgar»; Q3 «San Juan de Lurigancho» (efecto, gasto público); Q4 nivel «distrito» (pobreza).

## Rutas que difieren

| Ruta (en las cuatro) | Qué cambia | ¿Permitida? |
|---|---|---|
| `consulta_minima.pregunta_original`, `plan.consulta_minima.pregunta_original`, `consulta.consulta_minima.pregunta_original` | la pregunta armada con la plantilla de `textos.yaml` (p. ej. «¿Cómo ha cambiado la anemia en Huancavelica?») | sí |
| `consulta.pregunta`, `plan.pregunta` | copias de `pregunta_original` (la backlog nombra solo `consulta_minima` y `plan`; son el mismo texto) | sí, mismo caso |
| `consulta_minima.territorio.texto`, `plan.consulta_minima.territorio.texto`, `consulta.consulta_minima.territorio.texto` (**solo Q1**) | «Huancavelica» frente a «departamento de Huancavelica» | sí |

Q2, Q3 y Q4 no tienen más diferencias. Ninguna ruta de `cifras`, `semaforo_respuesta`, `respuesta_parcial`, `resultados_respuesta`, `texto` ni `capas.capa1`/`capa3` cambia.

## Lo que la historia esperaba y no ocurre

- `detalle.disparadores` de R-CRUCES-07 (Q3, `efecto`): **no difiere**; la base ya se tomó con el motor de S3-01b y el formulario da lo mismo. Nada que listar.

## Hallazgo (tipo C: no se resuelve aquí)

**Q1 por el formulario cambia `capas.capa2.avisos`** (de `[]` a un aviso): «Respondimos por el departamento de Huancavelica. Si buscabas la provincia o el distrito de Huancavelica, pregúntalo así: «provincia de Huancavelica» o «distrito de Huancavelica».» (`curados/motor/textos/territorio.yaml`).

- Causa: la historia dice «con “Huancavelica” y elegir 1», pero la decisión X-22 (6/11/2026) hace que «Huancavelica» a secas se responda como departamento, sin aclaración, y el motor agrega ese aviso. La base usaba «departamento de Huancavelica», que no lo trae. Por precedencia (AGENTS §3, X-22 gana al backlog) el formulario usa «Huancavelica» **sin** elegir; el caso con aclaración se prueba aparte con «Abancay» + elegir 1 (`q1_abancay_elegir_1`), que sí da lo mismo que su base en capas, cifras y semáforo.
- Es una frase nueva que la respuesta de la base no decía (AGENTS §5.1, condición 2), así que el agente no la aprueba. `tests/test_regresion_q1_q4.py::test_respuestas` para Q1 falla con «diferencias sin aprobar» si se le pasa la respuesta con ese aviso; la prueba del formulario retira ese único aviso (y comprueba que es el único) antes de aplicar los criterios.
- Propuesta al dueño: aprobar el aviso en `backlog/slice-1/evidencia/regresion/Q1.yaml` (capa `capa2.avisos[0]`), o confirmar que la regresión Q1 sigue usando «departamento de Huancavelica».
