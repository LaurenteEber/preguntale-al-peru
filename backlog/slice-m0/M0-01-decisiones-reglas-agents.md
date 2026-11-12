# M0-01 — Decisiones, reglas y `agents.md`

**Se deriva de** `docs/diseno/motor_inferencia.md` §26.1 y §26.2, con las decisiones del dueño del 8 y el 9 de noviembre de 2026. Es la única historia que edita `docs/decisiones.md` y `agents.md`.

## Tareas

1. **`docs/decisiones.md`:** aplicar la tabla del §26.1.
   - **Cómo editar:** en cada fila se agrega o se cambia **solo** lo que dice «Qué se agrega o cambia», y el resto de la fila se conserva.
   - **Fecha:** 8/11/2026 o 9/11/2026, según el día de la decisión. Son del 9/11 las de X-24 (T-04) y el respaldo (F-03).
   - **Filas nuevas:** R-08, X-23 (pendiente) y X-24 (decidida).
   - **X-05:** queda pendiente, con su nota.
   - **F-03 y F-04 (además):** el repo privado de crudos y la auditoría de seguridad, con fecha 9/11/2026.
   - **X-22:** se borra la fila por decisión del dueño (§26.1). Sus citas pasan a T-03 en `curados/motor/parametros_motor.yaml`, `src/pap/motor/territorio.py`, `src/pap/motor/preguntar.py`, `curados/motor/textos/territorio.yaml` y `docs/manual_de_uso.md`. Los nombres de los archivos de prueba (`test_x22_*.py`) no se cambian.
2. **Reglas, con el consolidador.** Se agrega al final de `reglas/consolidador/ajustes_dueno.py` un bloque `# ==== Motor de inferencia, M0-01 (dueño, 8/11/2026)` con:
   1. `CAMPOS_REGLAS += [('R-LENGUAJE-05', 'parametros.max_alternativas', 3)]`;
   2. la cláusula de Benjamini-Hochberg en `R-ENC-11.parametros.comparaciones_multiples` («con más de 4 grupos: prueba global y luego pares con BH al 5 % sobre todos los pares de la consulta»), con el mecanismo de parches del consolidador;
   3. **R-ENC-19 (no respuesta del ítem):** **solo si el dueño aprueba K-07**. Si aún no está aprobada, no se agrega y se deja anotado.

   Después se corren `python3 reglas/consolidador/consolida_reglas.py`, `vp3_checks.py` y `prueba_guardia.py`, y se actualiza el conteo de reglas en `agents.md`.
3. **`agents.md`:**
   - aplicar el §26.2 (§7, nuevo §5.2, §5.1 ampliado, estados del índice y §2), incluidas las tres frases nuevas del §7: auditoría de seguridad, crudos fuera del repo público y código de terceros;
   - en el §8, la marca `regresion_microdatos` y el comando de la nube (`-m "not solo_mac and not navegador and not regresion_microdatos"`).
4. **`docs/estado.md` y `docs/hoja_de_ruta.md`:** el siguiente trabajo es el motor (M0–M5) y la beta pasa a M4.

## Criterios de aceptación

- [ ] Cada fila editada tiene su diff en `evidencia/m0-01_decisiones.md`.
- [ ] `reglas.json` regenerado, con el diff de las reglas en la evidencia; `vp3_checks` y `prueba_guardia` en verde.
- [ ] Suite, Q1–Q4 y matriz sin cambios. El motor actual arma como máximo 2 alternativas (`preguntar.py:276-289`), así que `max_alternativas: 3` no cambia sus respuestas. Si alguna cambia, es tipo C.
- [ ] `agents.md` tiene el §5.2, las frases nuevas del §7 y la marca en el §8.

## Fuera

Usar las reglas nuevas en el motor actual: las usa el motor nuevo desde M0-09.
