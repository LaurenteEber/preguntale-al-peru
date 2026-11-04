# S1-07 — Regresión Q1–Q4

## Por qué

Q1–Q4 pasaron una aceptación independiente (P4) y una revisión de usuario. El motor por intenciones no puede empeorarlas. La prueba se arma en dos fases: comparación de planes desde S1-03 y comparación de respuestas completas desde S1-04. Después se corre en cada historia.

## Tareas

1. **Referencia.** Al cerrar S1-00 (rama `slice-1`, antes de tocar el motor), correr `uv run pap preguntar tests/fixtures/consultas_piloto/q*.yaml --salida <carpeta temporal>` y guardar los cuatro `respuesta.json` en `tests/referencias/q1–q4.json`. No usar `00_proyecto/piloto/p3/respuestas/`: son anteriores a T-02. Si `--salida` aún no existe (S1-06), copiar la salida y restaurar con git los archivos de `p3/respuestas/`.
2. **Clave de cifra.** Las cifras se comparan por `(indicador, anio, nivel, territorio, medida, rol)`, no por `id`. Los `id` que aparezcan en `comparaciones_bloqueadas`, en la ficha y en los resultados de reglas se traducen a esa clave antes de comparar.
3. **Fase 1, desde S1-03** (`tests/test_regresion_q1_q4.py::test_planes`): el plan generado desde la consulta mínima es igual a las cifras de `q1–q4.yaml` por clave, y con la misma comparación (`comparar_con`). Única diferencia esperada: Q1 sin la cifra de 2022 (`anemia_hvca_2022_ant`) y sin la oración del pico en «Más contexto» (decisión del dueño del 3/11/2026, C-01 y E-06). La prueba la trata como diferencia aprobada, registrada en `evidencia/regresion/Q1.yaml` con `aprobado_por: dueño`; no es un `xfail`.
4. **Fase 2, desde S1-04** (`test_respuestas`): la respuesta completa por el camino nuevo (resolver → planificador → plantillas) contra la referencia.
   - **Iguales exactos:** el conjunto de cifras usadas (por clave), sus valores, intervalos y estados; el semáforo de la respuesta; el nivel de confianza; `respuesta_parcial`; las comparaciones bloqueadas; y, por clave de cifra, las reglas con acción `bloquear`, `suprimir`, `agregar_nivel`, `publicar_referencial` o `bloquear_cruce`.
   - **Pueden variar si están aprobadas:** las reglas que solo rotulan, advierten o piden `revision_humana`. Por ejemplo, hoy R-TERRITORIO-09 da un falso «territorio no identificado» en Q1, Q2 y Q4 porque el `nombre_pedido` manual no se empareja; con el resolver eso desaparece y es lo correcto.
   - **Límites:** capa 1 dentro de `respuesta.capa1_palabras_max` (R-04); sin infracciones del corrector (`respuesta.infracciones_corrector`); ningún marcador sin rellenar ni código interno en el texto visible.
   - **Texto:** toda diferencia en las capas 1–3 falla salvo que esté aprobada en `backlog/slice-1/evidencia/regresion/<Q>.yaml` según el criterio de `agents.md` §5.1.
5. Las consultas mínimas de Q1–Q4 (S1-01) ya traen el nivel en el texto («departamento de Huancavelica», «Ayaviri, Melgar»), así que no producen aclaración. La aclaración por homónimo se prueba en S1-02 y S1-06.
6. La prueba **falla** (no se salta) si falta el cubo o la biblioteca: `agents.md` §8.

## Formato de `evidencia/regresion/<Q>.yaml`

```yaml
- capa: capa1.respuesta_corta        # ruta del campo en respuesta.json
  antes: "…texto de la referencia…"
  despues: "…texto nuevo…"
  motivo: "una línea: por qué el cambio es correcto"
  aprobado_por: agente               # agente (criterio §5.1) o dueño
```

## Criterios de aceptación

- [ ] La fase 1 existe desde S1-03 y la fase 2 desde S1-04; las dos están en verde al cerrar cada historia siguiente.
- [ ] Toda diferencia aprobada tiene motivo; ninguna diferencia de cifra, semáforo, confianza ni regla de bloqueo.
