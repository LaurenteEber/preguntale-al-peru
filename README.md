# Pregúntale al Perú

Responde preguntas sobre problemas del país con **cifras de fuentes públicas oficiales** (INEI, MEF, INS), por territorio y con los **límites de cada cifra**. Cuando los datos no alcanzan, la respuesta dice primero lo que no se puede saber.

```bash
uv sync
uv run pap preguntar --intencion evolucion --tema anemia --territorio "departamento de Huancavelica"
```

**Hoy:** motor por intenciones sobre 9 indicadores (anemia, desnutrición crónica, pobreza monetaria y gasto en servicios de salud y nutrición infantil), desde la Terminal. **Siguiente:** intérprete de preguntas en lenguaje natural (slice 2) y web (slice 3). Detalle: [docs/estado.md](docs/estado.md) y [docs/hoja_de_ruta.md](docs/hoja_de_ruta.md).

## Principios

- Ningún número sale de un LLM: todo número viene de consultas deterministas sobre datos curados.
- Solo fuentes y citas oficiales; cada cifra se valida contra las cifras publicadas («doradas»).
- Cada respuesta dice qué no permite concluir y con qué confianza.

## Estructura

| Carpeta | Qué hay |
|---|---|
| `src/pap/` | El paquete y la CLI `pap`: ingesta de crudos, construcción de la biblioteca, cubo de indicadores, validador de reglas y motor de respuestas |
| `tests/` | Pruebas (`uv run pytest -q`), casos del validador, regresión Q1–Q4 y matriz de cobertura |
| `curados/` | Lo que se edita a mano y se versiona: tablas curadas (`capa0/`), textos y parámetros del motor (`motor/`), recetas de descarga (`recetas/`) y generadores de tablas curadas |
| `reglas/` | Reglas de publicación y atribución (`reglas.json`, `reglas.md`) y su consolidador |
| `catalogo/` | Catálogo de 418 fuentes públicas y su pipeline |
| `biblioteca/` | Datos: crudos por huella y tablas Parquet. En git solo van los metadatos; los datos se reconstruyen |
| `docs/` | Manual, guía de operación, arquitectura, decisiones, especificaciones y guías |
| `backlog/` | Plan por slices y backlog de cada slice |

## Documentación

Empieza por [docs/README.md](docs/README.md). Para usar el sistema: [docs/manual_de_uso.md](docs/manual_de_uso.md). Para mantener los datos: [docs/guia_de_operacion.md](docs/guia_de_operacion.md). Para trabajar con un agente de código: [agents.md](agents.md).

## Datos

Los crudos y las tablas Parquet no están en git. Con los crudos en `biblioteca/cruda/almacen/` (huellas fijadas en `curados/insumos.lock.yaml`), toda la biblioteca se reconstruye con `pap construir` y `pap calcular` (orden en la guía de operación). Los datos de origen se rigen por los términos de cada entidad publicadora.
