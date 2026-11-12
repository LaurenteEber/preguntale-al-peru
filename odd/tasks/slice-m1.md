# Slice M1 — Planificador (spike), índice enriquecido y fichas

Feature tracking for `backlog/slice-m1/` on branch `slice-m1` (from `main` f76b7eb). Each story file under `backlog/slice-m1/` is the full spec for its task; the slice README holds the owner decisions of 12/11/2026 and the definition of done.
Owner reviews (3 h/week) never block: anything waiting for a visto stays `propuesto`/`revisado` and work continues.

## Specs

- S1: Every story M1-00 … M1-20 meets its «Criterios de aceptación» as written in its file under `backlog/slice-m1/`.
- S2: Definition of done = the 7 points of `backlog/slice-m1/README.md` § «Definición de hecho», verbatim there.
- S3: Rules from `AGENTS.md` and README § «Reglas del slice»: no figure of cube `010ea965` or of the recipes changes (only exception: publication state by C-M0-11-2, measured and reported before applying); the web answers do not change; the LLM picks by ID and produces no numbers; no SQL outside `ejecutar_select`; every new dependency/model enters with its audit; no commit while someone else edits tracked files; type C gaps go to `backlog/slice-m1/consultas_al_dueno.md`.
- S4: Owner decisions of 12/11/2026 = table «Decisiones del dueño del 12/11/2026» of the README; M1-01 applies them.
- S5: "H05-1 está en M1-02, tarea 3; puedes hacerla primero dentro de esa historia."
- S6: "Mis horas de revisión (3 por semana) no frenan el trabajo: lo que espere mi visto queda en propuesto y sigues con lo demás."
- S7: M1-09b (supervisor, owner visto) goes after M1-09; three models to download by the owner; "pásame la lista exacta de archivos y commits de cada modelo cuando tengas las auditorías".

## Tasks

| ID | Story | Specs | Route | Status | Commits |
|---|---|---|---|---|---|
| T0 | M1-00 tarea 1: branch + supervisor documents | S1 | inline | done | dd3d8b3 |
| T1 | M1-02 tarea 3: H05-1 reparar_dos | S1 S3 S5 | inline | in progress | |
| T2 | M1-00 rest (base, plan/estado, descargas, documentos, respaldo, auditorías, parámetros, semilla, consultas) | S1 S3 | inline | pending | |
| T3 | M1-01 decisiones, reglas y tablas curadas | S1 S3 S4 | inline | pending | |
| T4 | M1-02 rest of the debt | S1 S3 | inline | pending | |
| T5 | M1-03 uniones, universo, cortes | S1 S3 | tbd | pending | |
| T6 | M1-04 cuestionarios | S1 | tbd | pending | |
| T7 | M1-05 enriquecimiento | S1 S3 | tbd | pending | |
| T8 | M1-06 fichas, bloques, temas | S1 | tbd | pending | |
| T9 | M1-07 diseño muestral y lote | S1 S6 | tbd | pending | |
| T10 | M1-08 … M1-18 motor (sombra), including M1-09b banco del recuperador (after M1-09) | S1 S3 S7 | tbd | pending | |
| T11 | M1-19 evaluación y medición | S1 S2 | tbd | pending | |
| T12 | M1-20 revisión independiente y cierre | S1 S2 | tbd | pending | |

## Log

- L1 (12/11/2026): owner: "El cambio sin commit en backlog/slice-m1/README.md es del supervisor: es el backlog de M1. También dejó sin commit las 21 historias backlog/slice-m1/M1-00…M1-20 y docs/diseno/fichas.md. Todas las decisiones que pides ya están tomadas y están en la tabla «Decisiones del dueño del 12/11/2026» de ese README: C-M0-11-1, C-M0-11-2, K-03, K-07, los ZIP de 2024 (no se liberan) y las demás consultas abiertas de M0. Las aplica M1-01. Empieza M1: lee backlog/slice-m1/README.md, docs/diseno/fichas.md y agents.md. Crea la rama slice-m1 desde main y haz el primer commit con esos documentos (M1-00). H05-1 está en M1-02, tarea 3; puedes hacerla primero dentro de esa historia. Mis horas de revisión (3 por semana) no frenan el trabajo: lo que espere mi visto queda en propuesto y sigues con lo demás."
- L2: T0 done in dd3d8b3. Base pytest launched (M1-00 tarea 2). H05-1: RED observed (2 tests), fix = per-character replacement of DOS chars next to a letter + box-drawing chars in the mojibake control; 4 263 labels of the 2024 index give identical `curar_etiqueta` and control results with old and new code.
- L3 (12/11/2026): owner: "OK, por mientras, considera lo siguiente: 1) El supervisor agregó una historia nueva, sin commit: backlog/slice-m1/M1-09b-banco-recuperador.md (banco de pruebas del recuperador, con mi visto). Va después de M1-09. Inclúyela en tu próximo commit, agrégala a la tabla de historias del README y a la lista «Del dueño» (ahora son tres modelos por bajar), y pásame la lista exacta de archivos y commits de cada modelo cuando tengas las auditorías. 2) El supervisor también actualizó docs/diseno/tecnologias.md (sección 7.1 nueva y fuentes), sin commit. Inclúyelo en tu próximo commit junto con M1-09b."
- L4 (12/11/2026): owner: "ese último archivo es interno, no debe entrar a git. Continuemos con la implementación" → backlog/slice-m1/guia_dueno_modelos_busqueda.md added to .git/info/exclude. Audits committed 3bd4995. Worker did M1-00 t4–t6 (YAML v0.2.0, 34 tablas, codigo_documento, 5 captures 2026-11-12..-5, supuestos M1-00-s1..s3). Parent did t10 (motor.version, inferencia.modo_interprete, recuperador/planificador/aclaracion/comparacion/alternativas/cache/batch params; batch.tope_lote_usd 20 per K-05). Pool memory test failed once under load (passes alone 3/3): noted for M1-02 t1.
- L5 (12/11/2026): owner: "esos 2 últimos archivos también los ignoramos, no deben pasar a git." → bajar_modelos_busqueda.sh and supervision_seguridad_paquetes_m1.md added to .git/info/exclude.
- L6 (12/11/2026): owner: "por otro lado, estaré fuera por 2 horas, hazme todas las consultas que requieras. ya descargué los modelos por si acaso, están en la bandeja". Models verified: 26/26 SHA-256 OK in biblioteca/cruda/bandeja/hf-*. Answers: (1) C-M0-11-2 when only the publication state changes: "Medir, informar y aplicar"; (2) Docker: "Sí, con colima. Solo requiere start"; (3) live LLM while away: "Sí, dentro de los topes" (US$ 5/día, US$ 20/lote, K-05); (4) "Sí, push sin PR" to origin/slice-m1.
