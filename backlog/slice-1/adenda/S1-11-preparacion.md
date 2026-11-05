# S1-11 — Preparar el entorno y la biblioteca

Reescrita el 4/11/2026 para trabajar en Claude Code en la nube (decisión F-05). La reconstrucción desde los crudos ya se hizo en el Mac: dio el cubo `sha256:ba1fbc55…`, y sus Parquet se publicaron en el release `biblioteca-ba1fbc55` de GitHub. Aquí se baja ese paquete y se comprueba.

## Por qué

Los Parquet no van a git. Antes de cambiar el motor, el entorno tiene que tener la misma biblioteca de la migración. Así, cualquier diferencia posterior se atribuye a la adenda y no al entorno.

## Tareas

1. **Entorno:**
   - `uv sync` y `uv run pap --help`.
   - Si no corre, aplicar `agents.md` §8: detenerse y avisar.
2. **Rama:**
   - `git switch -c slice-1-adenda` desde `main`, con `git status` limpio.
   - Crear la carpeta de evidencia: `mkdir -p backlog/slice-1/evidencia/adenda`.
3. **`agents.md` §8 (primer commit de la rama, F-05).** Reemplazar el primer punto («Mac del dueño…») por:
   > Se trabaja en el Mac del dueño o en Claude Code en la nube, con uv y Python 3.12 (`uv sync`; ayuda: `uv run pap --help`). En la nube, la biblioteca se baja con `scripts/bajar_biblioteca.sh` (los Parquet del release de GitHub cuya etiqueta nombra la huella del cubo). `pap construir` desde los crudos solo corre en el Mac, donde está el almacén. Una prueba que necesita los crudos lleva la marca `solo_mac` y se deja fuera en la nube con `-m "not solo_mac"`; la evidencia dice cuántas y cuáles quedaron fuera. En la nube, todo «`uv run pytest -q`» del backlog se corre como «`uv run pytest -q -m "not solo_mac"`».
   - Registrar la marca `solo_mac` en `pyproject.toml` (`[tool.pytest.ini_options] markers`).
   - Commit: `S1-11: agents.md §8 para la nube (F-05)`.
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
6. **Base de pruebas.** Ensayo del supervisor (4/11/2026, clon de `main` más el release en un contenedor como el de la nube): `pytest -q` da **714 passed, 12 skipped, 2 failed y 20 errors**. Las 34 que no pasan necesitan crudos de `biblioteca/cruda/almacen/` (`FileNotFoundError`, `IOException: No files found`, o se saltan con «faltan insumos»):

   | Archivo | Pruebas | Cómo marcarlas |
   |---|---|---|
   | `tests/test_gasto.py` | 9 de 10, todas salvo la que pasa (error en la fixture) | Por prueba |
   | `tests/test_inversiones_ubicacion.py` | 11 de 12 (error en la fixture) | Por prueba |
   | `tests/test_territorio.py` | 5 de 9 (líneas 41, 65, 77, 90, 100) | Por prueba |
   | `tests/test_s4_insumos.py` | las 4 | `pytestmark` del módulo |
   | `tests/test_puentes.py` | las 3 | `pytestmark` del módulo |
   | `tests/test_poblacion.py` | `test_construccion_real` | Por prueba |
   | `tests/test_sien.py` | `test_s04_conservacion_contra_el_crudo` | Por prueba |

   - Se marcan esas 34 con `@pytest.mark.solo_mac` (o `pytestmark`), sin tocar su contenido.
   - En la nube: `uv run pytest -q -m "not solo_mac" > backlog/slice-1/evidencia/adenda/pytest_base.txt`. Se espera **714 passed, 34 deselected, 0 skipped, 0 failed, 0 errors**. Al final del archivo va la lista de las 34.
   - Si el número no coincide, o falla alguna prueba no listada, se anota en `../consultas_al_dueno.md` y no se arregla (`agents.md` §4).
   - La regresión Q1–Q4 está incluida y pasa en la nube (`tests/test_regresion_q1_q4.py`).
   - Commit: `S1-11: entorno, biblioteca y marca solo_mac comprobados`.

## Criterios de aceptación

- [ ] `s1-11_biblioteca.txt` termina con «cubo ba1fbc55…» y Q1–Q4 responden.
- [ ] `pytest_base.txt`: 714 passed y 34 deselected (`solo_mac`), con la lista; en el Mac, `uv run pytest -q` sigue en 748.
- [ ] `agents.md` §8 actualizado; existe `biblioteca/_respaldo_pre_adenda/` y no aparece en `git status`.

## No se toca

- `biblioteca/cruda/` y `curados/insumos.lock.yaml`.
- Los manifiestos de `biblioteca/`: en la nube no se reconstruye nada.
- La carpeta de trabajo anterior.
