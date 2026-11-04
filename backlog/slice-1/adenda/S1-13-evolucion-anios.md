# S1-13 — La evolución muestra los dos años que compara

## Por qué

H11 (revisión de usuario) y N-2 (auditoría): una evolución dice «sin cambio claro entre 2024 y 2025» sin mostrar la cifra de 2024, y con `--hasta 2024` llama «la más reciente» a 2024 aunque existe 2025. Además, A-H6: `evolucion anemia Perú --hasta 2024` responde «no se puede», aunque E-06 permite contar la serie anterior hasta 2024.

## Hoy (4/11/2026)

- `evolucion anemia Perú` dice «ni entre 2024 y 2025 con la forma de medir actual» y solo da la cifra de 2025.
- `evolucion anemia Perú --hasta 2024` responde «no se puede» y llama a 2024 «la más reciente».

## Tareas

1. **H11 (AD-1, aprobada el 4/11/2026):** en toda evolución, «Más contexto» da la cifra del año de comparación junto a la del último año («X % en 2024 y Y % en 2025»).
   - La cifra de comparación entra como **cifra de contexto propia**, con su marcador y su fila en «Para citar y verificar», igual que el gasto de 2023 hoy. No se escribe como valor suelto: todo número visible lleva su cita (P-02).
   - Las cifras ya están en el plan (`comparar_con`).
   - En Q1 se agrega la anemia de 2024 con la forma vigente. Es una diferencia de regresión: se registra con `aprobado_por: dueño` y el motivo «AD-1 (dueño, 4/11/2026, fila R-04 de decisiones.md)», como las entradas de C-01 en `../evidencia/regresion/Q1.yaml`.
   - `tests/test_regresion_q1_q4.py` compara las cifras por clave: se agrega la nueva clave como diferencia aprobada, con el mismo mecanismo que `CLAVE_2022_Q1` (C-01). Se actualiza `tests/referencias/q1.json` solo con lo aprobado.
2. **N-2:** «la más reciente» solo se dice del último año disponible del indicador. Si el periodo pedido termina antes, se dice «hasta {anio}».
3. **A-H6:** en una evolución de anemia ENDES cuyo periodo deja a la forma vigente con **menos de dos años**, se responde con la serie de la forma anterior del periodo pedido (E-06: las dos en paralelo cuando se puede).
   - La cifra clave es la de la forma anterior en el último año del periodo.
   - Si la forma vigente tiene un año dentro del periodo (2024 con `--hasta 2024`), esa cifra va en «Más contexto» con su cita y el «Ojo al leer» dice «con la forma de medir actual solo hay datos desde 2024». Si no tiene ninguno (`--hasta 2018`), solo se nombra en el «Ojo al leer».
   - Si ninguna de las dos formas tiene dos años en el periodo, sigue el «no se puede».
   - Esto es lo que permite responder la evolución que ofrece S1-15 (H7).

## Criterios de aceptación

- [ ] Toda respuesta `evolucion` de la matriz muestra las dos cifras que compara (prueba automática sobre la matriz reducida).
- [ ] `evolucion anemia Perú --hasta 2024` responde con la forma anterior 2015–2024, muestra la cifra vigente de 2024 en «Más contexto» y no llama «la más reciente» a 2024.
- [ ] `evolucion anemia Perú --hasta 2018` responde con la forma anterior 2015–2018.
- [ ] Q1: la única diferencia es la cifra de 2024 en «Más contexto» y su cita, registrada en `../evidencia/regresion/Q1.yaml` con `aprobado_por: dueño` (AD-1). Si cambia algo más, es una consulta tipo C.
