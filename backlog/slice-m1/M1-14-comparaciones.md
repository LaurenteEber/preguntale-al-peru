# M1-14 — Comparaciones entre grupos

**Se deriva de** el diseño §16.

## Tareas

1. **Una comparación pedida** (dos lugares o dos grupos): `contrast` de `svy` sobre una sola estimación con `by=`; p-valor con gl = mín(gl_a, gl_b); se afirma si p < 0,05 y se muestra el intervalo de la diferencia (R-ENC-11).
2. **Cortes con más de 4 grupos:** prueba global Rao-Scott; si es significativa, pares con Benjamini-Hochberg al 5 % sobre todos los pares de la consulta. En M1, hasta 5 grupos (quintil).
3. **«El más alto»** se responde por grupos semejantes (R-ENC-12), nunca como ranking. Entre departamentos prevalecen los grupos oficiales del INEI (E-08).
4. **Textos:** «es mayor», «es menor» y «no hay diferencia clara», con marcadores. Con más de 3 grupos, la capa 1 muestra el más alto, el más bajo y la frase de la prueba; el resto va a la capa 2 (§19.1).
5. **Entre años:** fuera hasta M2.

## Criterios de aceptación

- [ ] Las comparaciones coinciden con R `survey` en el microdato sintético (1e-9), incluida la prueba Rao-Scott.
- [ ] Anemia por área y por quintil en 2024 sale con su prueba.
- [ ] Una diferencia que no pasa la prueba nunca se redacta como diferencia.
