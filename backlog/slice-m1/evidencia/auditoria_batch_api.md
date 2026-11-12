# Auditoría de servicio externo — Batch API de Anthropic

Plantilla de M0-00b adaptada (no es una dependencia de Python: es un servicio que usa el cliente `anthropic`/`httpx` ya aprobado). **Historia:** M1-00 (tarea 8), usada en M1-05 y M1-09b · **Fecha:** 12/11/2026 · **Quién la hizo:** agente

## 1. Qué es y por qué entra
- **Qué hace:** procesa lotes de peticiones al LLM de forma asíncrona y más barata, para el enriquecimiento del índice de variables (fuera de línea, nunca en una respuesta al usuario).
- **Alternativa:** llamadas una por una (más caras, más lentas). No hay dependencia nueva de Python.
- **Dónde se usa:** `src/pap/inferencia/` (enriquecimiento, M1-05 y el texto de búsqueda de M1-09b).

## 2. Qué se envía y qué se guarda
- **Se envían solo textos públicos:** etiquetas, preguntas y categorías de los cuestionarios oficiales. Nunca datos personales ni microdatos (P-03).
- **Retención:** Anthropic guarda los datos del lote 29 días; no hay retención cero para esta API. Por eso solo textos públicos.
- **Costo:** dentro de `batch.tope_lote_usd` (parámetro del YAML); se informa en la evidencia.

## 3. Condiciones de uso (ya aprobadas en la auditoría previa; siguen vigentes)
1. **Clave y Workspace aparte** del servicio web, solo para los lotes. La clave vive en el Llavero del Mac o en una variable de entorno, nunca en archivos del repo (C9: gitleaks).
2. **Borrar cada lote** en Anthropic después de bajar sus resultados, y registrar en la evidencia que se borró (control C13). Si falla el borrado, el trabajo no se da por terminado.
3. El entorno de `Rscript` y de los subprocesos no recibe la clave (control de la auditoría previa).
4. El LLM solo propone texto de búsqueda; nada de lo que escribe entra a una respuesta ni lleva cifras (R-04; M1-09b: «ningún texto enriquecido aparece en una respuesta», con prueba).

## 4. Veredicto
**aprobado con condiciones** (las cuatro de arriba). Sin cambios respecto de `auditoria_seguridad_previa.md`.
- **Revisión siguiente:** al cierre de M1, o si cambian los términos de retención de Anthropic.
