# M1-04 — Lote con el LLM (Batch API): estado, costo y cómo reanudarlo

Fecha: 12/11/2026 · Quién: agente · **El lote real NO se corrió** (falta la clave de lotes). Todo lo demás está hecho y probado con un proveedor falso.

## 1. Por qué no se llamó a la Batch API

La auditoría (`auditoria_batch_api.md`, condición 1) exige una **clave y un Workspace aparte** del servicio web, solo para los lotes. Se revisó, sin mostrar ningún valor:

- el cliente del LLM (`src/pap/interprete/llm.py`) solo lee la variable del servicio web (`interprete.variable_clave`);
- en la configuración del proyecto no había **ninguna** variable para la clave de lotes (ni en `parametros_motor.yaml`, ni en `curados/inferencia/parametros.yaml`, ni en el `justfile` o el `Dockerfile`);
- en el entorno de esta sesión no existe ninguna variable con ese propósito.

Reutilizar la clave del servicio web habría roto la condición 1, así que **no se llamó a nada**. Lo que sí quedó listo:

- `batch.variable_clave` en `curados/inferencia/parametros.yaml`: nombre propuesto `PAP_ANTHROPIC_BATCH_KEY` (supuesto M1-04). El dueño crea la clave en un Workspace aparte de la consola de Anthropic y la pone con ese nombre en su entorno o su Llavero; nunca en un archivo del repo.
- `ClienteLote` (`src/pap/interprete/llm.py`): se niega a correr sin esa clave (`sin_clave_lote`) y también si el nombre de la variable fuera el del servicio web (`clave_compartida`). Prueba: `tests/interprete/test_llm_lote.py`.
- `pap cuestionarios lote` revisa que la variable exista **antes de hacer nada** y, si falta, lo dice y termina sin llamar.

## 2. Costo (estimado, no real)

Costo máximo calculado con los textos reales (precios de Sonnet 5.5 con el 50 % de descuento de la Batch API; entrada estimada por caracteres con margen; salida al máximo de tokens):

| Alcance | Variables | Pasada 1 (vincular) | Pasada 2 (verificar), peor caso | Total máximo |
|---|---|---|---|---|
| RECH6, REC43 y REC0111 | 271 | US$ 0,88 | US$ 0,33 | **≈ US$ 1,2** |
| Todas las pendientes de las 34 tablas | 2 339 | US$ 7,22 | US$ 2,83 | **≈ US$ 10** |

Cada pasada es un lote y el tope `batch.tope_lote_usd` (US$ 20) se revisa **antes de crear** cada uno: si el máximo lo pasa, el lote no se crea (prueba `test_un_lote_que_pasa_el_tope_no_se_crea`). El costo real se guardará en `estado_lote.json` (campo `gasto_usd`) y se informará aquí cuando se corra. **Costo real: no hay (no se corrió).**

## 3. Cómo se corre cuando exista la clave

```
export PAP_ANTHROPIC_BATCH_KEY=…            # clave del Workspace de lotes; no se escribe en ningún archivo
uv run pap cuestionarios lote --tablas RECH6,REC43,REC0111     # primero las tres tablas de la medición (≈ US$ 1,2 máx.)
uv run pap cuestionarios lote                                  # después, todo lo pendiente
uv run pap cuestionarios aplicar && uv run pap cuestionarios informe
```

Si el proceso se corta, se vuelve a correr **el mismo comando**: retoma el lote ya creado (no crea otro), baja solo lo que falte y borra el lote en Anthropic al final. Si el borrado falla, el comando termina con error y la siguiente corrida solo repite el borrado.

## 4. Lo que se probó (proveedor falso, sin red ni clave)

`tests/inferencia/test_m104_lote.py` (8 pruebas) y `tests/interprete/test_llm_lote.py` (8 pruebas):

| Comportamiento | Prueba |
|---|---|
| Dos lotes (vincular y verificar); ambos borrados; costo guardado | `test_el_lote_completo_vincula_verifica_y_borra_los_dos_lotes` |
| El `batch_id` ya está guardado cuando muere la consulta de estado; la reanudación no crea otro lote | `test_el_batch_id_queda_guardado_antes_de_consultar_el_estado_y_la_corrida_se_reanuda` |
| **Corte a la mitad** de la descarga de resultados (1 de 3): no se borra el lote; al reanudar sin duplicados y con el mismo resultado que una corrida entera | `test_si_se_corta_a_la_mitad_de_los_resultados_la_reanudacion_da_lo_mismo_que_una_corrida_entera` |
| Falla el borrado: no se da por terminado; la reanudación solo borra | `test_si_falla_el_borrado_el_trabajo_no_se_da_por_terminado_y_la_reanudacion_solo_borra` |
| Un lote sobre el tope no se crea | `test_un_lote_que_pasa_el_tope_no_se_crea` |
| Un ID que el modelo inventa vale «ninguna», nunca un vínculo | `test_un_id_que_el_modelo_inventa_…` |
| Sin secretos en los archivos; estado de otra corrida no se mezcla | `test_las_peticiones_solo_llevan_…`, `test_el_estado_de_otra_corrida_…` |
| Cliente HTTP: forma de las peticiones, estado, resultados, borrado, sin clave, sin filtrar la clave en errores | `tests/interprete/test_llm_lote.py` |

**RED y GREEN:** las pruebas de lote, de `ClienteLote` y de la puerta de publicación (`texto_publicable`) se escribieron antes del código y se vio el rojo (módulo o clase inexistente) antes de implementar. **Excepción honesta:** en las piezas de extracción y medición (`test_m104_parquet.py`, `test_m104_medicion.py`, la parte de matrices de `test_m104_pdf.py`) el código se escribió antes que la prueba, así que para ellas no hay rojo observado; sí quedaron probadas en verde.

## 5. Lo que el LLM puede y no puede hacer aquí

- Solo elige entre IDs de una lista (c01…c20) o dice «ninguna»; el código descarta cualquier ID que no esté en la lista.
- Una segunda llamada verifica; sin las dos, no hay vínculo.
- Todo vínculo queda `propuesto`. Ningún texto de pregunta entra a una respuesta pública: `indice.texto_publicable` solo lo entrega si la variable está `revisado` o `verificado`, y una prueba vigila que `motor/`, `web/` e `interprete/` no lean esos campos.
- Solo viajan textos públicos (etiquetas, categorías y preguntas de los cuestionarios oficiales). Nunca microdatos.

## 6. Pendiente

Ver `m1-04_vinculos.md`: sin el lote, las variables de las recetas no llegan al 95 % de texto vinculado (la meta de `tecnologias.md` §6 queda **sin medir**, no incumplida).
