# S1-16 — Verificación y cierre de la adenda

## Tareas

1. **Pruebas:**
   - `uv run pytest -q`, que incluye la regresión Q1–Q4.
   - La matriz completa: `uv run python tests/matriz/correr.py --salida salidas/matriz_adenda --reporte backlog/slice-1/evidencia/adenda/matriz.md`. No sobrescribe el reporte del slice (`../evidencia/matriz.md`).
2. **Verificación independiente:**
   - Un subagente nuevo, con el encargo escrito en `../evidencia/adenda/encargo_verificador.md`, comprueba la definición de hecho de la adenda punto por punto.
   - Verifica a mano el factor del IPC 2023→2025 con `dim_ipc`.
   - Relee las respuestas de evolución del gasto, cruce, efecto (Q3), Q1 y los casos de S1-15.
   - Su informe va en `../evidencia/adenda/verificacion.md`. Si hay hallazgos altos o bloqueantes, se corrigen y se vuelve a verificar.
3. **Documentación:**
   - `docs/manual_de_uso.md`:
     - §5: «La evolución del gasto no compara años» pasa a «compara en soles de 2025»;
     - §6: quitar las observaciones resueltas;
     - caso 8 con la salida nueva y caso 12 con el texto nuevo;
     - la línea de estado del inicio: hoy cita la etiqueta `slice-1-cerrado`, que no existe en este repositorio; pasa a «slice 1 y su adenda cerrados» con la etiqueta nueva.
   - `docs/arquitectura.md`: la misma corrección en su línea de versión, y lo nuevo del motor (precios constantes).
   - `backlog/slice-1/evidencia/cierre.md`: una sección «Adenda» con lo resuelto.
   - `docs/estado.md`: la huella nueva del cubo, la fecha de corte y la fila de la fase 5a.
   - `backlog/plan_slices.md`: quitar del slice 2 la deuda del gasto ya resuelta y el aviso «Antes, cerrar la adenda».
   - `docs/decisiones.md`: AD-1 y AD-2 ya están en las filas R-04 y R-03. Solo se editan si lo implementado obliga a precisarlas, sin agregar filas.
4. **Cierre:**
   - Marcar las historias como hechas en el `README.md` de la adenda.
   - Fusionar `slice-1-adenda` a `main` y poner la etiqueta `slice-1-adenda-cerrada`.
   - Subir `main`, la rama y la etiqueta: `git push origin main slice-1-adenda --tags`. Sin `--force`.

## Criterios de aceptación

- [ ] Definición de hecho de la adenda cumplida punto por punto, con enlace a su evidencia.
- [ ] `uv run pytest -q` en verde en `main` tras la fusión (`../evidencia/adenda/pytest_main.txt`).
- [ ] Ningún documento vigente (fuera de `evidencia/`) cita etiquetas o commits que no existan en este repositorio sin decir que son de la carpeta de trabajo.
