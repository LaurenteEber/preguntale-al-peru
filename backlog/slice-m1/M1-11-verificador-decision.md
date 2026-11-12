# M1-11 — Verificador completo, huellas y decisión 1

**Se deriva de** el diseño §12.

## Tareas

1. **Resto de las reglas del §12.1** que M0 no hizo:
   - las variables están en `revisado` (o en `propuesto` solo con `inferencia.admitir_propuesto_en_sombra`, M1-07);
   - `sujeto` y `ventana_referencia` coinciden con lo pedido;
   - el universo del plan es compatible con el `universo_cuestionario`;
   - variables `construida_inei` solo dentro de una receta;
   - submuestras no anidadas → falta estructural;
   - medida no disponible en la fase, total con peso normalizado, año sin ronda → faltas estructurales (los planes de varios años siguen fuera hasta M2);
   - cortes: como máximo uno bajo el departamento y `cortes_max` en total (se recorta y se avisa);
   - conteo previo de casos sin ponderar por dominio: con menos de 25, el dominio se marca para sustitución (solo descarta, nunca aprueba).
2. **Huellas** (`inferencia/huellas.py`): `huella_uy` por año (sha256 de las tuplas `llave_fila`, `u`, `y`, `corte` ordenadas) y cifra puntual ponderada, en DuckDB y sin estimar. Planes con la misma huella son uno solo; si uno es la receta, se conserva la receta. **Cierre anticipado del planificador:** si 2 muestras válidas coinciden en `huella_uy`, se decide sin esperar la tercera (enganche de M1-10).
3. **Diferencia material** entre planes: ≥ 2 pp o ≥ 10 % (parámetros).
4. **Decisión 1** (`inferencia/decision.py`): la tabla del §12.3, fila por fila, y las certezas del §12.4. `no_cubre.yaml` es lo único que permite un «no puedo» por tema. El lugar nunca es un «no puedo»: se sube de nivel.
5. **Salida `indeterminado`:** registra el caso (sin el texto de la pregunta) para revisar el índice.

## Criterios de aceptación

- [ ] Una prueba por cada fila de la tabla de decisión y por cada certeza del §12.4.
- [ ] Dos planes escritos distinto que cuentan a las mismas personas dan la misma `huella_uy`.
- [ ] La huella y la cifra puntual tardan menos de 0,3 s (p95) en el Mac.
- [ ] 0 «no puedo» cuando solo hubo fallas del plan (sale `indeterminado`).

## Fuera

Texto de las aclaraciones (M1-12); alternativas (M1-13).
