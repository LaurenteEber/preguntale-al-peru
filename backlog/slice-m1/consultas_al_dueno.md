# Slice M1 — Consultas al dueño

## Consultas que bloquean

(ninguna hasta ahora)

## Supuestos aplicados

| ID | Historia | Supuesto (tipo B) | Dónde vive | Cómo cambiarlo |
|---|---|---|---|---|
| M1-00-s1 | M1-00 tarea 5 | El informe «Perú: Indicadores de Resultados de los Programas Presupuestales, 2024 (ENDES)» (`pap_endes2024_ppr.pdf`) lo aportó el dueño y no se conoce una URL oficial. Se registró como `endes-2024-informe-ppr` **sin `download_url`** (solo `access_url` del portal) y con una nota en `known_issues`. Cuando el dueño dé el enlace oficial del INEI, se completa en la lista y se anota en el registro. | `curados/inferencia/descargas/endes_2024.yaml` (`documentos_adicionales`, `url: null`); captura `biblioteca/cruda/capturas/INEI-ENDES/2026-11-12-5` | Editar la fila `url` del YAML y registrar de nuevo con `--url-descarga` |
| M1-00-s2 | M1-00 tarea 5 | El PDF del informe se **copió** (no se movió) desde `bandeja/validacion_doradas/` para no invalidar su `SHA256SUMS`. Queda duplicado en disco hasta que se registren y muevan los 16 PDF de las doradas (deuda de `docs/estado.md`). | `biblioteca/cruda/bandeja/validacion_doradas/` | Al mover los 15 restantes con `--mover`, borrar también este |
| M1-00-s3 | M1-00 tarea 5 | Los nombres de archivo con que se registraron los 3 PDF nuevos de 2024 siguen el patrón de M0-02 (`2024-5-<archivo>.pdf`); la ficha de 2025 conserva `1038-Ficha.pdf`. | `original_filename` de las capturas | Solo cosmético |
| M1-00-s4 | M1-00 t9 / M1-09b t2 | Los 3 modelos de Hugging Face se catalogan como fuentes de apoyo, no de datos: sector «Privado», naturaleza `catalogo_portal`, tema `ciencia_tecnologia_digital`, licencia MIT / Apache-2.0, `estado_datos = sin_probar`. El embudo los deja en la ola `fuera_de_alcance`, con `compuerta_ingesta` vacía y `bloquea_mvp: false`. | `catalogo/scripts/nuevas_fuentes.json`; `curados/recetas/HF-*.yaml` | Cambiar los campos en `nuevas_fuentes.json` y correr `run.py` + `render.py` |
| M1-00-s5 | M1-00 t9 / M1-09b t2 | `retrieved_at` de cada receta = 2026-11-12 (fecha de las auditorías que fijan commit y huellas), porque `owner_file` lo exige. El dueño puede pasar `--consultado` con la fecha real al registrar. | `curados/recetas/HF-*.yaml` | Editar una línea o usar `--consultado` |
| M1-00-s6 | M1-00 t9 / M1-09b t2 | `.onnx` se registra con el tipo `application/octet-stream` (no hay tipo IANA ni firma fija). Los archivos se registran uno por uno con su ruta (la bandeja no recorre subcarpetas) y sin `--mover`. | `src/pap/util.py` (`MEDIATYPES`); `evidencia/m1-00_modelos_fuente.md` | Cambiar el valor de `MEDIATYPES["onnx"]` |
| M1-00-s7 | M1-00 tarea 11 | El conjunto semilla agrega el estrato `directa` (preguntas sin dificultad especial): M1-19 no tiene estrato para ellas. | `tests/inferencia/evaluacion.yaml`; `ESTRATOS` de `tests/inferencia/test_evaluacion_semilla.py` | Reclasificar en el YAML y quitarlo de `ESTRATOS` |
| M1-00-s8 | M1-00 tarea 11 | La semilla tiene 38 preguntas (no «unas 30») para cubrir todos los estratos; 11 son de la partición no vista, asignadas a mano y repartidas entre estratos. | `tests/inferencia/evaluacion.yaml` | Quitar preguntas o cambiar su `particion` |
| M1-00-s9 | M1-00 tarea 11 | Qué se espera en cuatro preguntas dudosas (ver `evidencia/m1-00_semilla.md`): EV-001 anemia sin decir la norma → responde con la receta vigente; EV-011 «chiquitos para su edad» → responde con desnutrición crónica; EV-016 diarrea «la última semana» → aclaración que diga la ventana real de 14 días; EV-034 discapacidad infantil → falta elegir cuál de las seis dificultades. No cambian cifras; fijan qué cuenta como acierto. | `tests/inferencia/evaluacion.yaml` | Cambiar `salida_esperada` o `variables_esperadas` de esa pregunta |

## Consultas que vienen de M0 (resueltas)

El dueño las decidió el 12/11/2026: tabla «Decisiones del dueño del 12/11/2026» de `README.md`. Las aplica M1-01, salvo donde se indica.

| ID | Qué preguntaba | Decisión | La aplica |
|---|---|---|---|
| K-01 | Lista de descargas | Revisada y ampliada: documentos n.º 8, 9 y 11 de la ENDES 2024, ficha técnica de la ENDES 2025 e informe de programas presupuestales de 2024 | M1-00 (hecho: `evidencia/m1-00_documentos.md`) |
| K-03 | Visto a las tablas curadas de M0-06 y a las 3 recetas | Visto: pasan a `verificado` | M1-01 |
| K-04 | Horas de revisión del dueño | 3 por semana; no frenan el trabajo (lo que espera un visto queda en `propuesto` o `revisado`) | todo el slice |
| K-05 | Tope del LLM | US$ 5 por día y US$ 20 por lote de enriquecimiento | M1-00 (`batch.tope_lote_usd`) y M1-01 |
| K-07 | Umbrales de R-ENC-19 | Aviso si pasa de 5 %; «aproximada» si pasa de 20 % | M1-01 |
| K-08 | Licencia de la ENAHO | Parquet publicados año por año solo si la ficha del año declara ODbL; si no, repo privado; catálogo INEI-ENAHO a `ODbL-1.0` | M1-01 |
| C-M0-05-2 | 341 filas de REC93DVdisciplina sin la mujer en REC0111 | Se excluyen de todo cálculo de disciplina infantil, con nota y prueba | M1-01 |
| C-M0-06-1 | Conglomerados repetidos 2024–2025 | `conglomerados_repetidos` (HV001), con cita a la ficha técnica de la ENDES 2025 (§3.1 y §IV) | M1-01 (ficha registrada en M1-00) |
| C-M0-06-2 | Tramos de edad | Los del INEI: anemia 6–8, 9–11, 12–17, 18–23 y 24–35 meses; desnutrición crónica menores de 36 y 36–59 meses | M1-01 y M1-03 |
| C-M0-06-3 | «Costa» | «Lima metropolitana» + «Resto Costa» de SHREGION; la categoría 1 se rotula «Lima Metropolitana y Callao» | M1-01 |
| C-M0-06-4 | HV270 y V190 | Se aceptan con el rótulo del INEI, «quintil de bienestar»; la duda de versión queda como nota | M1-01 |
| C-M0-11-1 | Tope de F-04 | 2 GB en el Mac y 1,5 GB en el repo privado; si un bloque lo pasa, se detiene y se consulta | M1-01 |
| C-M0-11-2 | 25 a 49 casos con CV alto | Los límites de precisión (R-ENC-03 y R-ENC-04) se aplican también con 25 a 49 casos | M1-01 (se mide e informa antes de aplicar) |
| D-M0-10-1, D-M0-03-1, D-M0-05-1 | Notas de M0 | Aceptadas; D-M0-10-1 se corrige en M1-03 | M1-03 |
| Liberar ZIP de 2024 | — | No por ahora | — |

## Deuda anotada (no bloquea)

- **`catalogo/scripts/test_catalogo.py::test_ingesta_verificada_al_dia` falla desde M0** («desactualizado: INEI-ENDES»), ya en `main`: las capturas de la ENDES de M0 y M1-00 no se pasaron a `ingesta_verificada.json`. Esa prueba está fuera de `testpaths`, por eso la suite no la ve. Se arregla con `just catalogo` (`ingesta_src.py` + `run.py` + `render.py`), pero la regeneración completa revertiría el cambio manual del `url_portal` de INS-CENAN en el catálogo publicado: primero hay que llevar ese cambio a la fuente de los generadores. Propuesta: hacerlo en la próxima historia que toque el catálogo, junto con regenerar `catalogo/salidas/priorizacion.md` y `auditoria_estado.csv`.
