# S1-12 — La evolución muestra los dos años que compara

## Por qué

H11 (revisión de usuario) y N-2 (auditoría): una evolución dice «sin cambio claro entre 2024 y 2025» sin mostrar la cifra de 2024, y con `--hasta 2024` llama «la más reciente» a 2024 aunque existe 2025. Además, A-H6: `evolucion anemia Perú --hasta 2024` responde «no se puede», aunque E-06 permite contar la serie anterior hasta 2024.

## Tareas

1. **H11 (según AD-1):** en toda evolución, la tarjeta de la capa 2 da la cifra del año de comparación junto a la del último año («X % en 2024 y Y % en 2025»), con la misma cita. Las cifras ya están en el plan (`comparar_con`). En Q1 se agrega 2024 con la forma vigente: diferencia de regresión con `aprobado_por: dueño` (AD-1).
2. **N-2:** «la más reciente» solo se dice del último año disponible del indicador. Si el periodo pedido termina antes, se dice «hasta {anio}».
3. **A-H6:** en una evolución de anemia ENDES cuyo periodo deja a la forma vigente con un solo año, se responde con la serie de la forma anterior del periodo pedido (E-06: las dos en paralelo cuando se puede). La forma vigente se nombra en «Ojo al leer» («con la forma de medir actual solo hay datos desde 2024»). Si ninguna de las dos tiene dos años, sigue el «no se puede».

## Criterios de aceptación

- [ ] Toda respuesta `evolucion` de la matriz muestra las dos cifras que compara (prueba automática sobre la matriz reducida).
- [ ] `evolucion anemia Perú --hasta 2024` responde con la forma anterior 2015–2024 y no llama «la más reciente» a 2024.
- [ ] Q1: la única diferencia es la tarjeta con 2024, aprobada por el dueño en `../evidencia/regresion/Q1.yaml`.
