# S1-16 — Verificación y cierre de la adenda

## Tareas

1. Correr `uv run pytest -q`, la regresión Q1–Q4 y la matriz completa (`--salida salidas/matriz_adenda --reporte backlog/slice-1/evidencia/adenda/matriz.md`, sin sobrescribir el reporte del slice).
2. **Verificación independiente:** un subagente nuevo, con encargo escrito en `../evidencia/adenda/encargo_verificador.md`, comprueba la definición de hecho de la adenda punto por punto. Verifica a mano el factor del IPC 2023→2025 y relee las respuestas de evolución del gasto, cruce, efecto y Q1. Su informe va en `../evidencia/adenda/verificacion.md`. Hallazgos altos o bloqueantes: se corrigen y se vuelve a verificar.
3. **Documentación:**
   - `docs/manual_de_uso.md`: §5 («La evolución del gasto no compara años» pasa a «compara en soles de 2025»), §6 (quitar las observaciones resueltas), caso 8 con la salida nueva y caso 12 con el texto nuevo;
   - `backlog/slice-1/evidencia/cierre.md`: una sección «Adenda» con lo resuelto;
   - `docs/estado.md`: huella nueva del cubo;
   - `backlog/plan_slices.md`: quitar del slice 2 la deuda del gasto ya resuelta;
   - `docs/decisiones.md`: si AD-1 o AD-2 cambian una decisión, editar su fila (R-04 o R-01), sin agregar filas.
4. Marcar las historias como hechas en `README.md` de la adenda, fusionar `slice-1-adenda` a `main` y poner la etiqueta `slice-1-adenda-cerrada`.

## Criterios de aceptación

- [ ] Definición de hecho de la adenda cumplida punto por punto, con enlace a su evidencia.
- [ ] `uv run pytest -q` en verde en `main` tras la fusión (`../evidencia/adenda/pytest_main.txt`).
