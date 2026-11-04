# Pipeline del catálogo de fuentes (v2)

Regenera el catálogo, la priorización y el estado de la auditoría a partir de archivos versionables.

```
python3 ingesta_src.py  # (requiere PyYAML) evidencia de capturas verificadas → ingesta_verificada.json
python3 run.py          # base v0.3 → migración v2 → correcciones → fuentes nuevas → prueba de humo → ingesta verificada → priorización
python3 test_catalogo.py  # validaciones: 0 errores obligatorio antes de publicar
python3 render.py       # escribe catalogo/catalogo_fuentes.{json,csv,md}, catalogo/salidas/priorizacion.md y catalogo/salidas/auditoria/auditoria_estado.csv
```

| Archivo | Qué es |
|---|---|
| `catalogo_v03_base.json` | Catálogo de partida (v0.3, antes de la auditoría). No se edita. |
| `migrar_v2.py` | Migración automática al esquema v2 (años tipados, licencias, URL literal vs. plantilla, base geográfica…). |
| `correcciones_src.py` → `correcciones_auditoria.json` | Correcciones de la auditoría: registro, hallazgo, cambios, evidencia y tipo de validación. **Para corregir un registro, agregar aquí.** |
| `nuevas_fuentes.json` | Fuentes nuevas y correcciones que cerraron vacíos de la capa 0 y de cobertura. |
| `humo_src.py` → `prueba_humo.json` | Resultado de la prueba de humo (descarga real de una muestra) del 5/10/2026. |
| `ingesta_src.py` → `ingesta_verificada.json` | Fuentes con captura completa en `biblioteca/cruda/capturas/`, última verificación «ok» por huella y, si la capa 0 las usa, todas sus huellas de `curados/insumos.lock.yaml` capturadas. Pasan a `estado_datos = descarga_ok`, `compuerta_ingesta = aprobada`, con `estado_ingesta` y `evidencia_ingesta` (decisión del 8/10/2026). **Volver a correrlo tras cada `pap registrar` o `pap verificar`**: `test_catalogo` falla si el JSON no coincide con lo que hoy calcula `evaluar()`, y `run.py` se detiene si el JSON falta. Una verificación solo de tamaño (`--rapido`) no aprueba. El catálogo distingue `base_aprobacion` = `humo` o `captura_verificada`. Las recetas con `desactivada` no se aprueban. |
| `inferencia_verificada.csv` | Tabla curada (se edita a mano, con cita) de la inferencia verificada por fuente × año × módulo para R-ENC-08. `render.py` la publica en `catalogo/`. |
| `prioriza_v2.py` | Reglas del embudo (olas, compuerta de ingesta, puntaje). |
| `test_catalogo.py` | Validaciones bloqueantes y advertencias. |
| `../salidas/auditoria/hallazgos_json/` | Hallazgos de los 6 auditores del catálogo y su asignación a temas (los lee render.py). |

Orden de aplicación: correcciones de investigación → fuentes nuevas → correcciones de auditoría → prueba de humo → ingesta verificada.

Una sola fuente de verdad: la compuerta la calcula este pipeline; el bloque `catalogo:` de las recetas es una copia que `tests/test_recetas_reales.py` compara con `catalogo/catalogo_fuentes.json`.
