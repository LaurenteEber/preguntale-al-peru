# S2-00 — Preparación

**Requiere X-11.**

## Por qué

El slice se implementa en Claude Code en la nube. Antes de tocar nada hay que comprobar que el entorno reproduce la biblioteca y las pruebas del cierre de la adenda, y guardar la base contra la que se comparará la vía estructurada (S2-06).

## Tareas

1. **Entorno:**
   - `uv sync` y `uv run pap --help`.
   - Biblioteca según X-11.
   - Prueba de humo: `uv run pap preguntar curados/motor/consultas_minimas/ --salida <tmp>`. Responde Q1–Q4 sin errores de huella (`insumos.tabla()`).
   - Si algo falla, `agents.md` §8: se detiene y se avisa.
2. **`agents.md` §8:** se actualiza con lo que decidió X-11:
   - dónde se puede trabajar (Mac, o la nube con el paquete de la biblioteca);
   - qué pruebas corren solo en el Mac y cómo se marcan;
   - que `pap construir` desde los crudos queda solo para el Mac.

   Es la única edición de `agents.md` del slice. Se hace en un commit propio, `S2-00: agents.md §8 según X-11`.
3. **Rama:** `git switch -c slice-2` desde `main` en `slice-1-adenda-cerrada` o después, con `git status` limpio.
4. **Bases:**
   - `uv run pytest -q > backlog/slice-2/evidencia/pytest_base.txt`. Las pruebas solo para el Mac se listan aparte.
   - En `evidencia/s2-00_base.txt`: la huella de `fact_indicador` (la del cierre de la adenda, que el slice no cambia) y la versión de la biblioteca.
   - **Base de la vía estructurada:** copiar a `evidencia/base_estructurada/` los `respuesta.json` de:
     - Q1–Q4 (`curados/motor/consultas_minimas/`);
     - 12 consultas con opciones directas, una por intención, más homónimo, Lima, comparación y «no se puede».
     
     Se guardan con el comando exacto que generó cada uno.
5. **Archivos del slice:** crear `backlog/slice-2/consultas_al_dueno.md` (con «Consultas que bloquean» y «Supuestos aplicados») y `backlog/slice-2/evidencia/`.
6. **Decisiones:** comprobar que X-11 a X-14 están en `docs/decisiones.md`. Si faltan X-12 a X-14, se anota y se avanza solo hasta S2-03.

## Criterios de aceptación

- [ ] `pytest_base.txt`, `s2-00_base.txt` y `base_estructurada/` guardados; la huella es la del cierre de la adenda.
- [ ] `agents.md` §8 dice cómo trabajar en la nube; ninguna prueba se salta en silencio.
- [ ] `git status` limpio en `slice-2`.

## No se toca

`biblioteca/`, `curados/insumos.lock.yaml`, `reglas/` y el motor.
