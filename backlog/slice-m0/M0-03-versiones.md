# M0-03 — Versiones: `svy` 0.35.0 y `pyreadstat` 1.3.7

**Se deriva de** F-05 (cada cambio de versión de `svy` es una historia propia, con su regresión) y de `docs/diseno/tecnologias.md` §2 y §5.

## Tareas

1. **`pyproject.toml`** (después de M0-00b, con `exclude-newer` ya activo):
   - `svy==0.35.0` y `pyreadstat==1.3.7`;
   - declarar `pydantic==2.13.5` y `ftfy==6.3.1`;
   - `uv lock`.
   - Se espera `svy-io` 0.7.1 y `svy-rs` 0.19.1 (las ramas 0.8 y 0.20 son de `svy` 0.36). Fuera de esas, no debe entrar ninguna dependencia nueva.
   - `just auditar` en verde sobre el lock nuevo.
2. **Commit** del cambio de `pyproject.toml` y `uv.lock`. `pap calcular` se niega a correr con cambios sin commit.
3. **Regresión del cubo:**
   - `uv run pap calcular` y comparación fila a fila con la copia de M0-00 (`evidencia/fact_indicador_010ea965.parquet`), en la misma máquina;
   - criterio: |dif| ≤ 1e-12 en valor, ee, IC, CV, gl, n, deff y n efectivo;
   - se espera que la huella del Parquet siga siendo `010ea965`. Si cambia, o si cambia una cifra, no se sube la versión y se abre una consulta tipo C.
4. **Q1–Q4, matriz y evaluación grabada:** sin cambios.
5. **`docs/especificaciones/stack.md`:**
   - las versiones nuevas y la política de `svy`;
   - las líneas 37, 67 y 73 sobre el verificador en R, que ahora se activa en M0-09.

La comparación de `svy` 0.35.0 con R `survey` se cierra en M0-09 (criterio 2), cuando ya está el verificador.

## Criterios de aceptación

- [ ] `evidencia/m0-03_regresion_svy.csv`, con la diferencia máxima por columna.
- [ ] Suite en verde.
- [ ] Diff de `uv.lock` en la evidencia.

## Fuera

`svy` 0.36, que cambia la API: será otra historia, después del 11/11/2026, con el adaptador de M0-08 ya en uso.
