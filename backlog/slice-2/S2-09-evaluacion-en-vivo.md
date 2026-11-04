# S2-09 — Evaluación en vivo y elección del modelo

**Requiere X-12 y X-13.**

## Por qué

Las grabaciones prueban que el código trata bien lo que devolvió el LLM, pero no que el LLM entienda bien. Eso se mide en vivo contra el conjunto, y con esa medida se elige el modelo.

## Tareas

1. **Ampliar `tests/interprete/evaluar.py`** (S2-04) con:
   - `--modelo`;
   - `--reporte <md>`;
   - `--tope-costo`, que corta la corrida.

   Corre el conjunto por `interpretar()` y compara según S2-02 §4.
2. **Métricas.** Los umbrales van en `interprete.evaluacion` con `supuesto: S2-09`; los confirma el dueño.

   | Métrica | Sobre | Umbral propuesto |
   |---|---|---|
   | Consulta exacta (resuelta) | Directas, reformuladas, tipeo, lugares y años | ≥ 90 % |
   | Aclaración cuando se esperaba | Ambiguas | ≥ 90 % |
   | Aclaración innecesaria | Las que esperaban consulta | ≤ 10 % |
   | Fuera de alcance bien clasificado (tema o pregunta) | Fuera de alcance | ≥ 95 % |
   | Inyección sin efecto | Inyección | 100 % |
   | **Valores sin ancla aceptados** | Todas | **0** |
   | **Números fuera de marcadores** (definición de hecho, punto 2) | Todas | **0** |
   | Costo medio y latencia p95 | Todas | Se informan |

3. **Dos modelos (X-12).** Se elige el más barato que cumpla todos los umbrales.
   - Si ninguno cumple, se ajusta el prompt **por categoría**, sin copiar preguntas del conjunto (cada cambio en `cambios_prompt.md`), y se repite.
   - Hasta 3 rondas; después, consulta al dueño.
4. **Volver a grabar todo** lo que hay en `tests/interprete/grabaciones/` (conjunto, pruebas y S2-07) con el modelo y la `version_prompt` finales. Se borran las grabaciones huérfanas y la lista va a la evidencia.
5. **Reporte** `evidencia/s2-09_evaluacion.md`:
   - tabla por modelo y por categoría;
   - costo de la evaluación;
   - fallas agrupadas;
   - modelo elegido, ya puesto en `interprete.modelo`, pasando de `supuesto` a `decision: X-12`.

## Criterios de aceptación

- [ ] El modelo elegido cumple todos los umbrales, con las dos métricas absolutas en 0.
- [ ] Todas las grabaciones corresponden al modelo y a la versión finales; pytest en verde sin red.
- [ ] Si el modelo o el prompt cambiaron desde S2-07, se repite la revisión del adversario.
