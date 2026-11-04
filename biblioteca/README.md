# Biblioteca de datos curados

| Carpeta | Contenido |
|---|---|
| `cruda/` | Originales intocables. Según `especificacion_cruda.md`: `almacen/` (archivos por huella SHA-256), `capturas/` (`datapackage.json` de cada obtención), `bandeja/` (descargas manuales por registrar), `solicitudes/` (Ley 27806) y `verificaciones.jsonl` |
| `estandarizada/` | Mismas tablas en Parquet, con ubigeo INEI validado, año y nombres de columna comunes. `gasto/` (base del MEF por año), `encuestas/` (`endes_nino`, `enaho_sumaria`) y `mapa_pobreza/` (`fact_mapa_pobreza`), con manifiestos y tablas de revisión en git (S4, 9/10/2026; ver `reglas/especificaciones_capa0.md`) |
| `dimensiones/` | Capa 0: ubigeo histórico, ámbitos, dominios, población, puentes (IPRESS, IE, CUI, unidad ejecutora), estructura programática |
| `indicadores/` | Indicadores calculados, cada uno con su ficha (fórmula, denominador, nivel válido, límites) |

Documentos: `especificacion_cruda.md` (contrato de metadatos y recetas), `analisis_archivo_propio_estadisticas_sociales.md` (archivo propio del dueño).

Los datos no se versionan en git; sí sus metadatos (`capturas/`, `verificaciones.jsonl`), las recetas y el código que los produce.
