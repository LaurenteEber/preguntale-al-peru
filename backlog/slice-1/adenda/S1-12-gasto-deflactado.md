# S1-12 — Gasto en soles constantes y su evolución

## Por qué

G-07 fija la serie 2023–2025 como cifra principal del gasto en servicios ex-PAN, pero hoy no se puede comparar entre años:
- el cubo solo trae soles de cada año (`respuesta.py`: `precios = "corrientes"`);
- R-GASTO-12 bloquea toda comparación entre años sin deflactar (`serie_sin_deflactar`).

Deflactar ya está decidido: G-01 y R-GASTO-12, con la serie BCRP PN38705PM (IPC de Lima Metropolitana, promedio anual) y como base el último año cerrado. El IPC está en `biblioteca/dimensiones/dim_ipc.parquet`, columnas `ipc_prom_anual` y `anio_completo`; 2023, 2024 y 2025 están completos.

## Hoy

`evolucion gasto_publico Perú` da solo la cifra de 2025 y menciona 2023 aparte, sin compararlos («En 2023, el gasto… era S/ 2 179,2 millones»).

## Decisiones de diseño de esta historia

Las fija la adenda, con los criterios de `agents.md` §6. No son vacíos.

| Tema | Se hace así | Por qué |
|---|---|---|
| Año base | El mayor año que tiene `anio_completo` en `dim_ipc` **y** filas de gasto en el cubo (hoy 2025). Se calcula, no se fija en el código. Una prueba comprueba que coincide con el que usa el validador (`base = ctx.anio_actual - 1`, `reglas_etapa1_3.py`) | R-GASTO-12 dice «último año cerrado»; si las dos cuentas difieren, el validador bloquearía la respuesta |
| Factor | `factor(t) = ipc_prom_anual(base) / ipc_prom_anual(t)`, leyendo `ipc_prom_anual` (no se recalcula el promedio mensual). Valor esperado 2023→2025: **1,0388706** | Una sola fuente del promedio |
| Forma en el cubo | **Filas nuevas** con `medida = "devengado_constante"`, para `gasto_ex_pan` y `gasto_ex_pan_opcion_c`, en todos los niveles y líneas en que existe `devengado`. `valor` = devengado × factor. PIM y PIA no se deflactan | `CLAVE` sigue siendo única; las filas en soles corrientes quedan iguales |
| Columnas nuevas | `anio_base_deflactor` (entero) y `factor_deflactor` (doble), nulas en las demás filas; `VERSION_TABLA` pasa a `1.2.0` | El esquema cambia: la versión lo dice |
| Motor | Una serie o comparación de gasto entre años pide `devengado_constante` y llena en la `Cifra` `precios = "constantes"`, `anio_base_deflactor` y `factores_deflactor` (en plural, {año: factor}: es el campo que lee el validador). Una cifra de un solo año sigue en soles corrientes | Es lo que el validador ya espera |
| Texto de la capa 1 | El patrón que ya existe para datos sin prueba estadística, `corta_sin_prueba` (`evolucion.yaml`): «pasó de S/ X millones en 2023 a S/ Y millones en 2025, en soles de 2025: aumentó» (o «disminuyó»). R-LENGUAJE-02 (`casos_borde`) permite «aumentó» con registros administrativos. **Sin diferencia ni porcentaje**: no están en el cubo (P-01) | Una sola cifra clave (2025) y el número de partida, los dos del cubo |
| Cifra de 2023 | En la capa 1 y en «Más contexto», en soles de 2025 (S/ 2 263,9 millones). En «Para citar y verificar», el monto nominal de cada año (S/ 2 179,2 millones en 2023) y el factor | Se compara lo comparable; la cita permite verificar contra el MEF |
| «Ojo al leer» | El `mensaje_usuario` de R-GASTO-12 («Montos en soles de {anio_base} (ajustados por inflación)…») | La regla prevalece sobre el texto de la plantilla (`agents.md` §3) |

## Tareas

1. **Cálculo** (`pap calcular`, `src/pap/motor/calculo.py`): las filas y columnas de la tabla de arriba. Si falta un mes del IPC en un año de la serie, se detiene con error.
2. **Motor** (`respuesta.py`, `Motor.cifra`) y **plantilla de evolución del gasto**, según la tabla de arriba:
   - La capa 2 ya no dice «Otro año: no se compara con la cifra clave» para el año de comparación.
   - R-GASTO-18 a 21 siguen aplicando.
3. **Glosario:** «soles constantes» va en `curados/motor/textos/glosario.yaml`.
4. **Documentación:** `docs/especificaciones/contrato_validador.md` (hoy solo dice `precios (corrientes)`) y la descripción del cubo en `docs/arquitectura.md`.
5. **Pruebas:**
   - el factor 2023→2025 reproduce los promedios de `dim_ipc` (1,0388706);
   - el año base coincide con el del validador;
   - `evolucion gasto_publico Perú` compara 2023 con 2025 sin `bloquear_cruce`;
   - una cifra de un solo año sale idéntica a la de antes;
   - Q3 no cambia de cifras (solo usa 2025).

## Criterios de aceptación

- [ ] `uv run pap preguntar --intencion evolucion --tema gasto_publico --territorio "Perú"` da 2023 y 2025 en soles de 2025, sin aviso de R-GASTO-12.
- [ ] Los montos nominales de control no cambian (2 179 / 2 429 / 2 456 millones, G-07) y la conciliación R-GASTO-04 pasa.
- [ ] Un script `../evidencia/adenda/s1-12_comparar.py` compara el cubo nuevo con `biblioteca/_respaldo_pre_adenda/` (S1-11). Las filas que ya existían son iguales en todas las columnas anteriores, salvo `version_tabla`. Su salida y el cálculo del factor quedan en `../evidencia/adenda/s1-12_comparacion_cubo.txt`.
- [ ] Regresión Q1–Q4 sin cambios de cifras.
