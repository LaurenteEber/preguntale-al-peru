# S1-00 — Preparación: reconstruir con los nombres de T-02 y dejar la base lista

## Por qué

El 2/11/2026 se consolidaron las decisiones y se corrigió la ortografía de 15 nombres de territorio (T-02, `curados/capa0/nombres_mostrados.yaml`). El código ya está cambiado, pero las tablas no se reconstruyeron. Las plantillas por intención (S1-04) toman los nombres de `dim_ubigeo_historico`, y toda la cadena de tablas depende de ella (cada tabla verifica la huella de sus insumos), así que hay que rehacerla entera antes de empezar.

## Tareas

1. En el Mac: `uv sync`. Correr `uv run pytest -q` y guardar la salida en `evidencia/pytest_base.txt` (línea de base, `agents.md` §4).
2. Commitear en `main` los cambios pendientes del 2/11/2026 (`git status`: decisiones, estado, territorio, `nombres_mostrados.yaml`, `reglas.json`, `consolida_reglas.py`, `vp3_checks.py`, documentación, `backlog/`, `agents.md`, `CLAUDE.md`, `curados/motor/parametros_motor.yaml`) y el manifiesto del cubo del 13/10 (`biblioteca/indicadores/manifiesto_p1_indicadores.json`). Mensaje sugerido: «Decisiones consolidadas (2/11/2026), nombres con tildes (T-02), backlog del slice 1». **Excepción a «pytest en verde antes de cada commit»:** este commit puede tener en rojo solo las pruebas que esperan los nombres nuevos (p. ej. «Anguía» en `test_respuesta_p3.py`); quedan en verde tras la tarea 7. Hay que commitear antes de reconstruir porque `pap construir` se niega con `codigo/` sin commitear.
3. Crear la rama `slice-1`.
4. **Respaldo antes de reconstruir** (los Parquet no están en git y al reconstruir se sobrescriben): copiar `biblioteca/dimensiones/*.parquet`, `biblioteca/estandarizada/**/*.parquet` y `biblioteca/indicadores/fact_indicador.parquet` a `biblioteca/_respaldo_pre_s1-00/` (manteniendo las subcarpetas) y agregar esa carpeta a `.gitignore`. No se borra al terminar: lo decide el dueño.
5. Reconstruir la cadena completa, en el orden de `docs/guia_de_operacion.md` §3.3:
   `territorio` → `poblacion` (~3,5 GB de RAM) → `puentes` → `gasto` → `endes` → `enaho` → `mapa_pobreza` → `indicadores` → `uv run pap calcular`.
6. Comprobar que solo cambiaron nombres, con un script de DuckDB contra el respaldo de la tarea 4:
   - **cubo `fact_indicador`:** unir por la clave de `calculo.py` y comparar todas las columnas salvo las de nombre de territorio;
   - **`fact_gasto_territorial`:** totales por año, nivel, departamento y método de ubicación. Es el riesgo concreto: el nombre alterno nuevo «Provincia Constitucional del Callao» entra al emparejamiento de inversiones por nombre (`gasto.py`, `nombres_ubigeo`);
   - **`dim_ubigeo_historico`:** solo deben cambiar `nombre`, `nombre_mostrado`, `nombre_normalizado`, `nombres_alternos`, `fuente_nombre_mostrado` y `version_tabla`, y solo en los 15 ubigeos de `nombres_mostrados.yaml`.
7. `uv run pytest -q` y `uv run pap preguntar tests/fixtures/consultas_piloto/q*.yaml`.
8. Anotar la huella nueva del cubo en `docs/estado.md` (fila «Cubo, validador y motor»).
9. Comprobar en `dim_ubigeo_historico` los datos que el resto del slice supone (los usa S1-02 y S1-08) y guardarlos en `evidencia/s1-00_datos_territorio.txt`:
   - `nombres_alternos` de 060506 (debe incluir «Santa Cruz de Toledo»; si no, consulta tipo C: T-02 no se cumple);
   - cuántos distritos vigentes comparten nombre con otro (los 10 nombres más repetidos, p. ej. «Santa Rosa», «San Juan»);
   - los distritos sin ninguna fila en `fact_sien_hb_ubigeo` 2025.

## Criterios de aceptación

- [ ] Las pruebas T-19 y T-20 de `pap construir territorio` pasan.
- [ ] La comparación de la tarea 6 da 0 diferencias en cifras del cubo y del gasto; se guarda en `evidencia/s1-00_comparacion_cubo.txt`.
- [ ] Q4 dice «Anguía (Chota, Cajamarca)».
- [ ] `uv run pytest -q` en verde, salvo los fallos que ya estaban en `pytest_base.txt` y no tienen que ver con nombres (se anotan, no se arreglan).
- [ ] `estado_actual.md` tiene la huella nueva; `s1-00_datos_territorio.txt` existe.

## Si algo falla

- Si T-19 falla, la fuente cambió: no se toca el YAML a ciegas; se anota en `consultas_al_dueno.md` qué dice la fuente y qué propone.
- **Si cambia alguna cifra del cubo o del gasto, se detiene el slice** y se abre una consulta tipo C con la comparación. Lo más probable es el emparejamiento por nombre de las inversiones del Callao; la propuesta por defecto es excluir de `nombres_ubigeo` los alternos que agrega `nombres_mostrados.yaml`.
