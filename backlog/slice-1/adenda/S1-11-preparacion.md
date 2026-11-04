# S1-11 — Preparar el repositorio y la biblioteca

## Por qué

El repositorio se migró el 4/11/2026. Los Parquet no van a git, así que en el Mac la biblioteca está incompleta: solo hay algunas tablas de una construcción parcial. Antes de cambiar el motor hay que reconstruirla y comprobar que da lo mismo que la migración. Con eso, cualquier diferencia posterior se puede atribuir a la adenda y no al entorno.

## Tareas

1. **Entorno:** `uv sync` y `uv run pap --help`. Si no corre, aplicar `agents.md` §8 (detenerse y avisar).
2. **Rama:** `git switch -c slice-1-adenda` desde `main`, con `git status` limpio. Crear la carpeta de evidencia: `mkdir -p backlog/slice-1/evidencia/adenda`.
3. **Reconstruir la biblioteca** en este orden, una etapa por comando:
   - `uv run pap construir territorio`
   - `poblacion`
   - `puentes`
   - `gasto` (la más larga: unos 5 minutos)
   - `endes`
   - `enaho`
   - `mapa_pobreza`
   - `indicadores`
   - y al final `uv run pap calcular`.

   Cada etapa se niega si hay cambios sin commit en `src`, `curados`, `tests` o `catalogo/scripts`: eso es a propósito (RP-03), no se usa `--permitir-sucio`.
4. **Comprobar que salió igual:** la construcción reescribe los manifiestos que están en git.
   - Correr, antes del commit, `uv run python backlog/slice-1/adenda/comparar_manifiestos.py > backlog/slice-1/evidencia/adenda/s1-11_reconstruccion.txt`. Compara las huellas de tablas e insumos de cada manifiesto contra las de HEAD e ignora `commit`, fechas y orden.
   - Debe salir con código 0 y con `fact_indicador` = `sha256:ba1fbc55…`.
   - Si alguna huella cambia, es una consulta tipo C (`agents.md` §5): se anota y se detiene la adenda.
   - Commit: `S1-11: biblioteca reconstruida en el Mac`.
5. **Respaldo para comparar:**
   - Copiar `biblioteca/indicadores/` y los Parquet de `biblioteca/dimensiones/` a `biblioteca/_respaldo_pre_adenda/`. Esa carpeta está fuera de git (`.gitignore`: `biblioteca/_respaldo*/`).
   - S1-12 compara el cubo nuevo contra esta copia.
   - No se borra hasta cerrar la adenda; luego lo decide el dueño.
6. **Base de pruebas:**
   - `uv run pytest -q > backlog/slice-1/evidencia/adenda/pytest_base.txt`. Se esperan 748 pruebas en verde.
   - Si hay fallos, se anotan en `../consultas_al_dueno.md` y no se arreglan (`agents.md` §4).
   - La regresión Q1–Q4 está incluida (`tests/test_regresion_q1_q4.py`).

## Criterios de aceptación

- [ ] `comparar_manifiestos.py` sale con código 0 y huella del cubo `ba1fbc55…`; su salida queda en `../evidencia/adenda/s1-11_reconstruccion.txt`.
- [ ] `pytest_base.txt` guardado; `git status` limpio en `slice-1-adenda`.
- [ ] Existe `biblioteca/_respaldo_pre_adenda/` y no aparece en `git status`.

## No se toca

- `biblioteca/cruda/almacen/`: los crudos.
- `curados/insumos.lock.yaml`: no se usa `--actualizar-insumos`.
- La carpeta de trabajo anterior: no forma parte del repositorio.
