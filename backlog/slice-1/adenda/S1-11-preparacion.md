# S1-11 — Preparar el entorno y la biblioteca

Reescrita el 4/11/2026 para trabajar en Claude Code en la nube (decisión X-11). La reconstrucción desde los crudos ya se hizo en el Mac: dio el cubo `sha256:ba1fbc55…`, y sus Parquet se publicaron en el release `biblioteca-ba1fbc55` de GitHub. Aquí se baja ese paquete y se comprueba.

## Por qué

Los Parquet no van a git. Antes de cambiar el motor, el entorno tiene que tener la misma biblioteca de la migración. Así, cualquier diferencia posterior se atribuye a la adenda y no al entorno.

## Tareas

1. **Entorno:**
   - `uv sync` y `uv run pap --help`.
   - Si no corre, aplicar `agents.md` §8: detenerse y avisar.
2. **Rama:**
   - `git switch -c slice-1-adenda` desde `main`, con `git status` limpio.
   - Crear la carpeta de evidencia: `mkdir -p backlog/slice-1/evidencia/adenda`.
3. **`agents.md` §8 (primer commit de la rama, X-11).** Reemplazar el primer punto («Mac del dueño…») por:
   > Se trabaja en el Mac del dueño o en Claude Code en la nube, con uv y Python 3.12 (`uv sync`; ayuda: `uv run pap --help`). En la nube, la biblioteca se baja con `scripts/bajar_biblioteca.sh` (los Parquet del release de GitHub cuya etiqueta nombra la huella del cubo). `pap construir` desde los crudos solo corre en el Mac, donde está el almacén. Una prueba que necesita los crudos lleva la marca `solo_mac` y se deja fuera en la nube con `-m "not solo_mac"`; la evidencia dice cuántas y cuáles quedaron fuera.
   - Registrar la marca `solo_mac` en `pyproject.toml` (`[tool.pytest.ini_options] markers`).
   - Commit: `S1-11: agents.md §8 para la nube (X-11)`.
4. **Biblioteca:**
   - Correr `bash scripts/bajar_biblioteca.sh > backlog/slice-1/evidencia/adenda/s1-11_biblioteca.txt 2>&1`.
   - Debe terminar con código 0 y «cubo ba1fbc55…».
   - Si falla la descarga (red), es `agents.md` §8: se detiene y se avisa. No se reconstruye nada.
   - Si falla una huella, es una consulta tipo C.
   - Prueba de humo: `uv run pap preguntar curados/motor/consultas_minimas/ --salida salidas/s1-11`. Responde Q1–Q4 sin errores de huella; `insumos.tabla()` comprueba cada Parquet contra su manifiesto.
5. **Respaldo para comparar:**
   - Copiar `biblioteca/indicadores/` y los Parquet de `biblioteca/dimensiones/` a `biblioteca/_respaldo_pre_adenda/`.
   - Esa carpeta está fuera de git (`.gitignore`: `biblioteca/_respaldo*/`).
   - S1-12 compara el cubo nuevo contra esta copia.
   - En la nube, el entorno es efímero: si una sesión nueva no tiene el respaldo, se vuelve a crear con el paso 4 y esta copia, **antes** de correr `pap calcular`.
6. **Base de pruebas:**
   - `uv run pytest -q > backlog/slice-1/evidencia/adenda/pytest_base.txt`. Se esperan 748 en verde.
   - Si fallan pruebas porque necesitan los crudos:
     - se les pone la marca `solo_mac`;
     - se corre `uv run pytest -q -m "not solo_mac"`;
     - la lista de las marcadas se anota al final de `pytest_base.txt`.
   - Solo puede llevar la marca una prueba cuyo fallo diga que falta un archivo de `biblioteca/cruda/`. Cualquier otro fallo se anota en `../consultas_al_dueno.md` y no se arregla (`agents.md` §4).
   - La regresión Q1–Q4 está incluida (`tests/test_regresion_q1_q4.py`).
   - Commit: `S1-11: entorno y biblioteca comprobados`.

## Criterios de aceptación

- [ ] `s1-11_biblioteca.txt` termina con «cubo ba1fbc55…» y Q1–Q4 responden.
- [ ] `pytest_base.txt`: 748 en verde, o 748 menos N con las N `solo_mac` listadas, todas por crudos faltantes.
- [ ] `agents.md` §8 actualizado; existe `biblioteca/_respaldo_pre_adenda/` y no aparece en `git status`.

## No se toca

- `biblioteca/cruda/` y `curados/insumos.lock.yaml`.
- Los manifiestos de `biblioteca/`: en la nube no se reconstruye nada.
- La carpeta de trabajo anterior.
