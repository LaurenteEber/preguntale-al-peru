# M1-01 tarea 5 — Catálogo: INEI-ENAHO a `ODbL-1.0` (K-08)

**Fecha:** 12/11/2026 · **Quién:** agente · **Historia:** M1-01 tarea 5.

## En sencillo
- `INEI-ENAHO` pasa de «uso libre con cita» a `ODbL-1.0` en el catálogo y en su receta, con las fichas de la Plataforma Nacional de Datos Abiertos (PNDA) de 2023 y 2024 como fuente.
- El catálogo se regeneró **completo con los scripts** (no a mano). Antes se llevó a la fuente de los generadores el cambio manual del `url_portal` de `INS-CENAN-SIEN`, así que la regeneración ya no lo revierte.
- Ninguna cifra, semáforo ni nivel de confianza cambia: es un cambio de licencia y de trazabilidad del catálogo.

## Base de la licencia (leído el 12/11/2026)
Ambas fichas declaran, en el campo «Licencia»: **«Open Data Commons Open Database License (ODbL)»**.
- ENAHO 2023: https://www.datosabiertos.gob.pe/dataset/encuesta-nacional-de-hogares-enaho-2023-instituto-nacional-de-estad%C3%ADstica-e-inform%C3%A1tica-%E2%80%93
- ENAHO 2024: https://www.datosabiertos.gob.pe/dataset/encuesta-nacional-de-hogares-enaho-2024-instituto-nacional-de-estad%C3%ADstica-e-inform%C3%A1tica-%E2%80%93

(Las URL se hallaron con la búsqueda del propio portal, `search/type/dataset?query=enaho`, con el agente de usuario del proyecto. La primera consulta a la API fue bloqueada por el cortafuegos del portal con 418 y no se insistió por esa vía.)

## Qué cambió
- `catalogo/scripts/correcciones_src.py` (→ `correcciones_auditoria.json`, 63 → 65 correcciones):
  1. `INS-CENAN-SIEN`: `url_portal` = colección de informes SIEN en gob.pe (lo que ya tenía el catálogo publicado por un cambio manual; la base v0.3 traía la «Sala nutricional»).
  2. `INEI-ENAHO`: `licencia = ODbL-1.0`, `licencia_texto = «ODbL (datosabiertos.gob.pe)»` (mismo estilo que ENAPRES/ENA), `permite_redistribucion = true` (ya lo era), con las dos fichas como evidencia y K-08 como hallazgo.
- `curados/recetas/INEI-ENAHO.yaml`: `licenses` = `ODbL-1.0`, `license_basis: declarada_en_pagina`, sin `terms_note` (la nota de la TUO Ley 27806 era de la base «norma general»). El bloque `catalogo:` no cambia (no copia la licencia); `incoherencias_catalogo` queda limpia («Coherencia con el catálogo y R-DEP-01: ok»).
- Regenerados con `ingesta_src.py` → `run.py` → `test_catalogo.py` → `render.py` (lo que corre `just catalogo`; `just` no está instalado): `catalogo/catalogo_fuentes.{json,csv,md}`, `catalogo/salidas/priorizacion.md` (421 fuentes en vez de 418; fuera de alcance 84 en vez de 81), `catalogo/scripts/ingesta_verificada.json`. `auditoria_estado.csv` salió idéntico.

## Prueba de que la regeneración completa no revierte nada
Se regeneró en una copia temporal (con `biblioteca/` y `curados/` enlazados) y se comparó fila por fila con el catálogo publicado **antes** de editar. Con las correcciones nuevas, las únicas filas distintas fueron estas (las 421 fuentes coinciden en ID):

| Fuente | Campos que cambian | Por qué |
|---|---|---|
| `INEI-ENAHO` | `licencia`, `licencia_texto`, `correcciones` | K-08 (esta tarea) |
| `INS-CENAN-SIEN` | solo `correcciones` (la traza nueva) | `url_portal` ya es idéntico al publicado: el arreglo funciona |
| `INEI-ENDES` | `fecha_verificacion`, `evidencia_ingesta`, `correcciones` | capturas de la ENDES de M0 y M1-00 que faltaban en `ingesta_verificada.json` (la deuda de `test_ingesta_verificada_al_dia`) |
| `HF-MULTILINGUAL-E5-SMALL`, `HF-GRANITE-EMBEDDING-97M-…-R2`, `HF-GRANITE-EMBEDDING-311M-…-R2` | `estado_datos` `sin_probar` → `descarga_ok`, `estado_ingesta` = `capturada_verificada_piloto`, `evidencia_ingesta`, `correcciones` | los archivos ya están capturados y verificados por huella (12/11/2026); las 3 fuentes siguen en el catálogo, con ola y compuerta sin cambio |

Sin cambios en ola, compuerta de ingesta ni puntaje de ninguna fuente (las recetas HF siguen con `compuerta_ingesta: null`, así que sus bloques `catalogo:` no se tocan).

## Pruebas
- `uv run pytest -q catalogo/scripts/test_catalogo.py`: **5 passed** (incluye `test_ingesta_verificada_al_dia`, que fallaba desde M0).
- `uv run pytest -q tests/ -k "receta or catalogo or registrar or validacion"`: **113 passed, 1755 deselected**.
- `uv run pap recetas validar`: «Coherencia con el catálogo y R-DEP-01: ok».
- `test_catalogo.py` corrido directamente (`uv run python`): 0 errores; las advertencias son las que ya había.
- No se corrió la suite completa (límite de la tarea).

## Para el dueño
Nada nuevo que decidir. Solo queda a la vista que las tres fuentes HF ahora figuran como `descarga_ok` en el catálogo, porque la regeneración refleja las capturas ya verificadas.
