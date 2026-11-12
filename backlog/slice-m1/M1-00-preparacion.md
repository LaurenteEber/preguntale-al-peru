# M1-00 — Preparación, descargas y auditoría de dependencias

**Se deriva de** el diseño §6 y §22, `fichas.md` §4 y `tecnologias.md` §7 y §8b.

## Tareas

1. **Rama `slice-m1`** desde `main` (`f76b7eb` o posterior). El primer commit agrega los documentos que el supervisor dejó sin commit: `docs/diseno/fichas.md` y `backlog/slice-m1/`.
2. **Base:** guardar la salida de pytest (`evidencia/pytest_base.txt`), las latencias base del intérprete y los conteos del índice de M0.
3. **`backlog/plan_slices.md` y `docs/estado.md`:** M0 cerrado (fecha, etiqueta), M1 en curso, y una línea sobre el frente de datos en paralelo (backlog aparte, pendiente). Corregir en `docs/hoja_de_ruta.md` el slice 3, que sigue «en curso».
4. **Ampliar `curados/inferencia/descargas/endes_2024.yaml`** según `fichas.md` §4:
   - `periodo_codigo` y `periodo_nombre` separados;
   - `tablas` por módulo, comprobadas contra los miembros `.dta` de cada ZIP;
   - `codigo_documento` en cada documento, con el número del listado «Consulta por Documentos» del INEI.
5. **Bajar y registrar** (solo `https://proyectos.inei.gob.pe`, como en M0-02):
   - documentos n.º 8 «Manual de la Entrevistadora», n.º 9 «Manual del Antropometrista» y n.º 11 «Identificadores de las bases de datos» de la ENDES 2024;
   - la **ficha técnica de la ENDES 2025** (`url_ficha` del catálogo, código de encuesta de 2025) como recurso `endes-2025-ficha-tecnica`. Comprobar que su texto coincide con el del §3.1 y el §IV que trae `biblioteca/cruda/bandeja/validacion_doradas/pap_endes2025_ppr.pdf` (hojas 134 y 138).
   - Si el Mac no llega al portal, se pide al dueño que los deje en la bandeja.
6. **URL exacta de cada descarga:** comprobar que los recursos de 2024 guardan su `download_url` exacto (la página general del portal es `access_url`) y registrar los nuevos con `--url-descarga`.
   - **Registrar también el informe** `biblioteca/cruda/bandeja/validacion_doradas/pap_endes2024_ppr.pdf` como recurso `endes-2024-informe-ppr` y sumarlo a `descargas/endes_2024.yaml` (es la fuente de las doradas; su registro ya era deuda pendiente en `docs/estado.md`).
7. **Respaldo:** volver a respaldar el bloque `endes-2024` con los documentos nuevos y probar la restauración.
8. **Auditoría de seguridad** de lo que entra en M1, con la plantilla (`backlog/plantillas/auditoria_dependencia.md`) y las condiciones de `backlog/slice-m0/evidencia/auditoria_seguridad_previa.md`: `bm25s`, `PyStemmer`, `onnxruntime` (solo CPU), `tokenizers` (sin `huggingface-hub`, solo `from_file`) y el modelo e5-small (por commit, con SHA256SUMS). Versiones con 2 semanas o más. Batch API: clave y Workspace aparte, lotes borrados al bajar los resultados.
9. **Fuente del modelo de búsqueda:** entrada de catálogo y receta de fuente para `HF-MULTILINGUAL-E5-SMALL` (descarga manual por el dueño; F-05 ya lo aprueba), para que `pap registrar` lo acepte en M1-09.
10. **Parámetros que otras historias necesitan desde el inicio:** `motor.version` por tema (todos en `actual`) en `curados/motor/parametros_motor.yaml`. Los parámetros `inferencia.*`, `recuperador.*`, `planificador.*` y `batch.*` viven en `curados/inferencia/parametros.yaml`.
11. **Conjunto semilla de evaluación:** unas 30 preguntas del agente con cifra oficial y su variable esperada, en `tests/inferencia/evaluacion.yaml` (formato de M1-19). Lo usan M1-05 y M1-09; M1-19 lo completa.
12. **`consultas_al_dueno.md`** del slice, con las consultas abiertas que vienen de M0 ya marcadas como resueltas (tabla del README).

## Criterios de aceptación

- [ ] Rama creada y primer commit con los documentos.
- [ ] `descargas/endes_2024.yaml` validado: las tablas de cada módulo son exactamente los `.dta` de su ZIP (34 en total).
- [ ] Los 4 documentos nuevos y el informe registrados, con su huella y su URL exacta.
- [ ] Bloque `endes-2024` respaldado de nuevo y restauración probada.
- [ ] Auditorías aprobadas en `evidencia/`; `pip-audit` en verde.
- [ ] Suite en verde; el cubo sigue en `010ea965`.

## Fuera

Instalar las dependencias nuevas en el lock (cada una entra en la historia que la usa).
