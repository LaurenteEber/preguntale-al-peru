# S1-13 — Cruce y efecto: textos que no prometen ni contradicen

## Por qué

- **H9:** la respuesta de `cruce` dice «Estas cifras se muestran lado a lado…», pero la capa 1 solo trae el gasto y la anemia queda en una tarjeta con «no se compara con la cifra clave». El contrato permite una sola cifra clave (R-04), así que se corrige el texto, no la estructura.
- **H12:** la respuesta de `efecto` dice «Estos datos muestran qué se gastó y cómo cambió el indicador» y, a la vez, «no podemos mostrar cómo cambió». La primera frase viene de R-CRUCES-07 (`reglas.json`).
- **D-01:** para «Lima», R-TERRITORIO-09 (`ambiguos_conocidos`) ofrece opciones distintas de T-03.

## Tareas

1. **H9:** en la plantilla `cruce_efecto` (textos en `curados/motor/textos/plantillas/`), la capa 1 de `cruce` deja de decir «lado a lado». Dice qué es la cifra clave y que la otra cifra del mismo lugar está en «Más contexto», sin relación causal. La tarjeta de la otra cifra cambia «no se compara con la cifra clave» por «otra fuente: se muestra junto, no explica la cifra clave». Cambio solo de texto: lo puede aprobar el agente (`agents.md` §5.1).
2. **H12 (según AD-2):** cambiar la frase estándar de R-CRUCES-07 con `consolida_reglas.py` (bloque de ajustes del dueño, citando AD-2). Regenerar `reglas.json` y `reglas.md`; deben pasar `vp3_checks.py` y `prueba_guardia.py`. Revisar también «En el departamento de Lima solo alrededor del 5 % de este gasto…» (ambigua, H12): debe decir de qué total es el 5 %.
3. **D-01:** en el mismo paso del consolidador, `ambiguos_conocidos` de R-TERRITORIO-09 para «Lima» pasa a Lima Metropolitana, Lima Región y Callao (T-03). Cerrar D-01 en `../consultas_al_dueno.md`.
4. Si el dueño no aprueba AD-2, la tarea 2 queda sin hacer y la plantilla de efecto no repite la frase en la capa 1 (solo en la ficha técnica).

## Criterios de aceptación

- [ ] Ninguna respuesta `cruce` de la matriz dice «lado a lado» con una sola cifra en la capa 1.
- [ ] La respuesta de `efecto` de Q3 no se contradice. Su diferencia de texto queda aprobada (`aprobado_por: dueño`, AD-2).
- [ ] `reglas.json` regenerado; `vp3_checks.py` sin cierres abiertos; guardia 0 fallos; `pap validar-reglas` en verde.
