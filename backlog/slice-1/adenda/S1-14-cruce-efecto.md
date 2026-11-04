# S1-14 — Cruce y efecto: textos que no prometen ni contradicen

## Por qué

- **H9:** la respuesta de `cruce` dice «Estas cifras se muestran lado a lado…», pero la capa 1 solo trae el gasto y la anemia queda en una tarjeta con «no se compara con la cifra clave». El contrato permite una sola cifra clave (R-04), así que se corrige el texto, no la estructura.
- **H12:** la respuesta de `efecto` dice «Estos datos muestran qué se gastó y cómo cambió el indicador» y, a la vez, «no podemos mostrar cómo cambió». La primera frase viene de R-CRUCES-07 (`reglas.json`).
- **D-01:** para «Lima», R-TERRITORIO-09 (`ambiguos_conocidos`) ofrece opciones distintas de T-03.

## Tareas

1. **H9:** la capa 1 de `cruce` deja de decir «lado a lado».
   - Dice qué es la cifra clave y que la otra cifra del mismo lugar está en «Más contexto», sin relación causal.
   - La etiqueta de la tarjeta de la otra cifra pasa a «Otra fuente: se muestra junto, no explica la cifra clave». Va en una **clave nueva de `curados/motor/textos/plantillas/cruce_efecto.yaml`**, usada solo por `cruce`. No se edita `comunes.yaml` (`no_se_compara`), que usan todas las plantillas. La respuesta de `efecto` (Q3) no cambia por esta tarea.
   - Es un cambio solo de texto y lo aprueba el agente (`agents.md` §5.1).
2. **H12, frase de efecto (AD-2, aprobada el 4/11/2026):** la nueva oración es «Estos datos muestran qué se gastó y cómo está el indicador; no muestran si el gasto lo cambió.».
   - Está en dos textos de `reglas/propuestas/cruces_lenguaje.json`:
     - el `mensaje_usuario` de R-CRUCES-07, que empieza «Saber si un gasto 'sirvió' requiere…»;
     - `frases_estandar.efecto` («Saber si un gasto o programa funcionó requiere… Estos datos muestran qué se gastó y cómo cambió el indicador, pero no si uno causó lo otro.»).
   - En los dos se reemplaza solo la oración que empieza «Estos datos muestran…»; la primera oración no cambia.
   - `mensaje_usuario` se cambia en `reglas/consolidador/ajustes_dueno.py`, citando AD-2.
   - `frases_estandar` hoy no tiene gancho de ajuste: se agrega uno en `consolida_reglas.py`, junto a donde ya se sobrescriben `prohibidas` y `notas_corrector` de `P['cruces_lenguaje']['lenguaje']`. Lee un diccionario nuevo de `ajustes_dueno.py` (p. ej. `FRASES_ESTANDAR`), con comentario AD-2. No se editan las propuestas a mano.
   - Se actualizan:
     - el span protegido del corpus `reglas/consolidador/pruebas/corpus_auditor.json` (C06);
     - la frase de `docs/especificaciones/contrato_respuesta.md`, que hoy dice que «cómo cambió el indicador» queda como estaba.
   - Se regeneran `reglas.json`, `reglas.md` y `ficha_limites_y_lenguaje.md` con `python3 reglas/consolidador/consolida_reglas.py`. Deben pasar `vp3_checks.py` y `prueba_guardia.py`.
   - La diferencia en Q3 se registra en `../evidencia/regresion/Q3.yaml` y en `tests/referencias/q3.json`, con `aprobado_por: dueño` (AD-2).
3. **H12, porcentaje atribuible:** «En el departamento de Lima solo alrededor del {pct_atribuible} de este gasto…» (`curados/motor/textos/bloques.yaml`, `atribuible`) no dice de qué total es el porcentaje.
   - El denominador es todo el gasto atribuido al departamento 15 (`calculo.py`, `pct_gasto_atribuible`), no el monto de Lima Metropolitana de la tarjeta.
   - El texto pasa a «…alrededor del {pct_atribuible} del gasto atribuido al departamento de Lima se puede ubicar en municipalidades y obras…».
   - Cambia Q3 sin cambiar cifras y solo hace explícito lo que ya se afirmaba. Lo aprueba el agente (`agents.md` §5.1), registrado en `Q3.yaml`.
4. **D-01:** R-TERRITORIO-09 pasa a ofrecer para «Lima» las tres opciones de T-03, en este orden: Lima Metropolitana (provincia de Lima), Lima Región (Lima Provincias) y Callao. Es lo que ya hace el resolver del motor.
   - En `ajustes_dueno.py` hay que cambiar cuatro lugares:
     - `parametros.ambiguos_conocidos`;
     - `parametros.sin_respuesta` («ofreciendo los otros tres» pasa a «los otros dos»);
     - el `casos_borde` y el `mensaje_usuario` agregados para «Lima», que hoy nombran el departamento completo y Lima Metropolitana y Callao;
     - la comprobación `territorio09_lima_orden`, que hoy exige exactamente 4 opciones en el orden viejo.
   - Se cierra D-01 en `../consultas_al_dueno.md`.

## Criterios de aceptación

- [ ] Ninguna respuesta `cruce` de la matriz dice «lado a lado» en la capa 1. La ficha larga puede seguir describiendo el cruce CR-01 «lado a lado» (R-03).
- [ ] La respuesta de `efecto` de Q3 no se contradice. Su diferencia de texto queda en `../evidencia/regresion/Q3.yaml` con `aprobado_por: dueño` y el motivo «AD-2 (dueño, 4/11/2026, fila R-03 de decisiones.md)».
- [ ] `reglas.json` regenerado; `vp3_checks.py` sin cierres abiertos; guardia 0 fallos; `pap validar-reglas` en verde.
