# S1-11 — Gasto en soles constantes y su evolución

## Por qué

G-07 fija la serie 2023–2025 como cifra principal del gasto en servicios ex-PAN, pero hoy no se puede comparar: el cubo solo trae soles de cada año (`respuesta.py`: `precios = "corrientes"`), y R-GASTO-12 bloquea toda comparación entre años sin deflactar (`serie_sin_deflactar`). Deflactar ya está decidido: G-01 y R-GASTO-12, con la serie BCRP PN38705PM (IPC de Lima Metropolitana, promedio anual) y como base el último año cerrado. El IPC está en `biblioteca/dimensiones/dim_ipc.parquet` (2010-01 a 2026-08).

## Tareas

1. **Cálculo** (`pap calcular`, `motor/calculo.py`): para `gasto_ex_pan` y `gasto_ex_pan_opcion_c`, agregar las filas o columnas en soles constantes, con la fórmula de R-GASTO-12:
   - `monto_real(t) = monto_nominal(t) × IPC_prom(base) / IPC_prom(t)`;
   - base = último año cerrado con gasto (hoy 2025);
   - se guardan `precios`, `anio_base_deflactor` y `factor_deflactor` por año.

   Los valores en soles corrientes no cambian. El año base se lee de R-GASTO-12 (`parametros`) y de `dim_ipc`, nunca se fija en el código. Si falta un mes del IPC de un año, se detiene con error (R-GASTO-12: el año en curso usa los meses disponibles, pero aquí todos los años son cerrados).
2. **Motor** (`respuesta.py`, `Motor.cifra`): una serie o una comparación de gasto entre años pide la medida en constantes y llena `precios = "constantes"`, `anio_base_deflactor` y los factores. Una cifra de un solo año sigue en soles corrientes, rotulada.
3. **Plantilla de evolución del gasto:**
   - La capa 1 dice cuánto cambió en términos reales, como diferencia y en porcentaje (dato administrativo: no hay prueba estadística; se usa el verbo que ya usa el motor para registros).
   - El «Ojo al leer» explica que los montos están «en soles de 2025, descontando la inflación».
   - La cita da el monto nominal de cada año y el factor.
   - La capa 2 ya no dice «Otro año: no se compara con la cifra clave».
   - R-GASTO-18 a 21 siguen aplicando.
4. **Ficha y glosario:** el término «soles constantes» va en el glosario (`curados/motor/textos/glosario.yaml`).
5. **Pruebas:**
   - los factores reproducen el IPC del BCRP: comprobar a mano el factor 2023→2025 con los promedios de `dim_ipc` y dejar el cálculo en la evidencia;
   - `evolucion gasto Perú` compara 2023 con 2025 sin `bloquear_cruce`;
   - una cifra de un solo año sale idéntica a la de antes;
   - Q3 no cambia de cifras (solo usa 2025).

## Criterios de aceptación

- [ ] `uv run pap preguntar --intencion evolucion --tema gasto --territorio "Perú"` da 2023 y 2025 en soles de 2025, con el cambio real, sin aviso de R-GASTO-12.
- [ ] Los montos nominales de control no cambian (2 179 / 2 429 / 2 456 millones, G-07): la conciliación R-GASTO-04 pasa.
- [ ] La huella del cubo cambia solo por las filas o columnas nuevas. Se compara contra la de antes, como en S1-00, y queda en `../evidencia/adenda/s1-11_comparacion_cubo.txt` con el cálculo de los factores.
- [ ] Regresión Q1–Q4 sin cambios de cifras.
