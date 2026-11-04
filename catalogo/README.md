# Catálogo de fuentes

| Archivo | Qué es |
|---|---|
| `catalogo_fuentes.json` | Catálogo v2 (418 fuentes): lo leen `pap`, el validador y el consolidador de reglas |
| `catalogo_fuentes.md`, `catalogo_fuentes.csv` | El mismo catálogo para leer y para hojas de cálculo |
| `inferencia_verificada.csv` | Inferencia verificada por fuente × año × módulo (R-ENC-08); se edita en `scripts/` y se publica aquí |
| `scripts/` | Pipeline que regenera todo lo anterior ([scripts/README.md](scripts/README.md)); `just catalogo` lo corre entero |
| `salidas/` | Priorización por olas y estado de la auditoría del catálogo (los genera `scripts/render.py`) |

Esquema de cada registro: [../docs/especificaciones/catalogo.md](../docs/especificaciones/catalogo.md).
