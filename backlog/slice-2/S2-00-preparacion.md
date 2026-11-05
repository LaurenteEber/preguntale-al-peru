# S2-00 — Preparación

**Requiere el cierre de la adenda** (`agents.md` §8 ya está adaptado a la nube desde S1-11; F-05).

## Por qué

El slice se implementa en Claude Code en la nube. Antes de tocar nada hay que comprobar que el entorno reproduce la biblioteca y las pruebas del cierre de la adenda, y guardar la base contra la que se comparará la vía estructurada (S2-06).

## Tareas

1. **Entorno:**
   - `uv sync` y `uv run pap --help`.
   - Biblioteca: `bash scripts/bajar_biblioteca.sh` (F-05).
   - Prueba de humo: `uv run pap preguntar curados/motor/consultas_minimas/ --salida <tmp>`. Responde Q1–Q4 sin errores de huella (`insumos.tabla()`).
   - Si algo falla, `agents.md` §8: se detiene y se avisa.
2. **`agents.md` §8:** ya lo actualizó S1-11 (F-05). Solo se comprueba; esta historia no lo edita.
3. **Rama:** `git switch -c slice-2` desde `main` en `slice-1-adenda-cerrada` o después, con `git status` limpio. Si la adenda quedó en un PR que el dueño aún no fusiona, `slice-2` nace de la punta de `slice-1-adenda` (con S1-16 en verde) y se anota en `consultas_al_dueno.md`; el PR del slice 2 se abre después del de la adenda.
4. **Bases:**
   - `uv run pytest -q > backlog/slice-2/evidencia/pytest_base.txt`. Las pruebas solo para el Mac se listan aparte.
   - En `evidencia/s2-00_base.txt`: la huella de `fact_indicador` (la del cierre de la adenda, que el slice no cambia) y la versión de la biblioteca.
   - **Base de la vía estructurada:** copiar a `evidencia/base_estructurada/` los `respuesta.json` de:
     - Q1–Q4 (`curados/motor/consultas_minimas/`);
     - 12 consultas con opciones directas, una por intención, más homónimo, Lima, comparación y «no se puede».
     
     Se guardan con el comando exacto que generó cada uno.
5. **Archivos del slice:** crear `backlog/slice-2/consultas_al_dueno.md` (con «Consultas que bloquean» y «Supuestos aplicados») y `backlog/slice-2/evidencia/`.
6. **Antes de empezar:** leer `../slice-1/evidencia/cierre.md` §Adenda y anotar en el README del slice lo que cambie. Comprobar que la variable de la clave de la API existe en el entorno (sin imprimirla); si no, se anota en `consultas_al_dueno.md` y se sigue hasta S2-03.

## Criterios de aceptación

- [ ] `pytest_base.txt`, `s2-00_base.txt` y `base_estructurada/` guardados; la huella es la del cierre de la adenda.
- [ ] Ninguna prueba se salta en silencio (las `solo_mac` están listadas).
- [ ] `git status` limpio en `slice-2`.

## No se toca

`biblioteca/`, `curados/insumos.lock.yaml`, `reglas/` y el motor.
