# M1-13 — Sustitución automática y alternativas

**Se deriva de** el diseño §17.

## Tareas

1. **Decisión 2** (`inferencia/alternativas.py`):
   - lugar fuera de inferencia → el nivel que lo contiene (R-ENC-06);
   - grupo o cifra suprimidos → en orden: el mismo subgrupo a nivel nacional; el mismo subgrupo dentro de su región natural (región natural es un corte, no un nivel de `territorios.yaml`: se calcula a nivel nacional con ese corte); el territorio sin desagregar. El paso de agrupar años queda para M2 (hay un solo año);
   - cada paso se calcula y pasa por las compuertas; se usa el primero que pasa; si ninguno, «no puedo» por precisión.
2. **Nunca automático:** otro año, otra población u otro concepto.
3. **Bloque `sustitucion`** en la respuesta: pedido, mostrado y motivo, en palabras sencillas.
4. **Alternativas** (hasta 3, `max_alternativas`): cada una cambia una dimensión, en el orden del §17.2; se calculan de verdad (en memoria por petición; con la caché de M1-17 cuando exista) y pasan las compuertas antes de ofrecerse; cada botón dice qué cambia. La quinta dimensión (otra fuente) ofrece el SIEN para anemia por distrito, por el camino actual.

## Criterios de aceptación

- [ ] Casos de prueba: Huancavelica rural, distrito de Ate y un año sin ronda.
- [ ] Ninguna alternativa ofrecida está suprimida.
- [ ] ≥ 80 % de los «no puedo» del conjunto de evaluación llevan alguna alternativa (se mide en M1-19).
