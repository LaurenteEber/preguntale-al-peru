# Slice M0 — Cimientos del motor de inferencia

Feature tracking for `backlog/slice-m0/` on branch `slice-m0`. Each story file under `backlog/slice-m0/` is the full spec for its task; the slice README holds the definition of done.
Owner waits: K-01 (ZIP list), K-02 (R), K-03 (visto), K-07 (R-ENC-19), K-09 (gh token).

## Specs

- S1: "Implementa el slice M0 siguiendo backlog/slice-m0/README.md" — every story M0-00 … M0-11 meets its «Criterios de aceptación» as written in its file.
- S2: Definition of done = the 10 points of `backlog/slice-m0/README.md` § «Definición de hecho del slice», verbatim there.
- S3: Rules from `AGENTS.md` apply: type C gaps go to `consultas_al_dueno.md` and are never resolved by the agent; no data, curated table or tolerance is adjusted to make a test pass; Q1–Q4, matrix and recorded evaluation must not change.
- S4: K-06 answered by the owner on 9/11/2026: "(a) Stata donde exista, SPSS en 2015–2020".
- S5: Downloads: "Intentalo vos" — the agent tries to download from proyectos.inei.gob.pe once K-01 is approved.

## Tasks

| ID | Story | Specs | Route | Status | Commit |
|---|---|---|---|---|---|
| T1 | M0-00 preparación y base | S1 S3 | inline + explore (interfaces) | done | f51a8ce |
| T2 | M0-00b seguridad A1–A9 y controles | S1 S3 | worker (context backstop) | done except Docker image (daemon off) and D-M0-00b-1 (gitleaks, owner checks); review deferred to M0-11 | 4787964, c1ceaff |
| T3 | M0-01 decisiones, reglas, agents.md | S1 S3 | worker | done (R-ENC-19 waits K-07) | d187ea8 |
| T4 | M0-02 lista, descarga, registro | S1 S4 S5 | worker | done except backup upload + restore (wait K-09) | see git log M0-02 |
| T5 | M0-03 svy 0.35.0 y pyreadstat 1.3.7 | S1 S3 | worker | done; cube byte-identical 010ea965 | c9dbffc |
| T6 | M0-04 conversor y almacén | S1 | worker | done: 34 DTA → Parquet, RSS max 778 MB, hash max 0.68 s; suite 1322 passed | see git log M0-04 |
| T7 | M0-05 índice de variables | S1 | worker | done: 2 856 vars, joins exact, suite 1369 passed; reconverted with full classes (content hashes unchanged) | see git log M0-05 |
| T8 | M0-06 tablas curadas 2024 | S1 S3 | worker + auditor (verify) | done: counts match cube; auditor H-1 citation fixed; K-03 visto pending | see git log M0-06 |
| T9 | M0-07 gramática, verificador, DuckDB | S1 | worker | done: 217 new tests, suite 1620 passed; note: DuckDB allows writes inside allowed dirs (review in M0-11) | see git log M0-07 |
| T10 | M0-08 ejecutor y pool | S1 | worker | done on Mac: equivalence diff 0, 90-row early read ≤ 4.99e-9, suite 1669 passed; Linux pool run pending; memory margin note for M0-11 | see git log M0-08 |
| T11 | M0-09 compuertas y verificador R | S1 | worker + inline | done: gates + 90 rows; R expected values (50 rows, max 1.3e-15); C-M0-09-1 resolved by owner (binaries) | e925215, 2847b2b, see git log |
| T12 | M0-10 recetas 2024 vs cubo | S1 S3 | worker + auditor (verify) | done except `verificado` (K-03): 90 rows diff 0, 21/21 doradas, suite 1769 passed | d89db55 (first half, swept by the owner's commit), see git log M0-10 |
| T13 | M0-11 medición, almacén, cierre | S1 S2 | inline + workers (context backstop) + 9 verify reviewers | done: DoD 10/10 except Linux pool (3) and Docker image (9); suite 1818 passed 1 skipped; PR waits «fusiona» | 75df63b, 51769f7, 620c45c, 4561a29, cierre commit |

## Log

- L1 (9/11/2026): "Ok. Implementa el slice M0 siguiendo backlog/slice-m0/README.md"
- L2: K-06 → "(a) Stata donde exista, SPSS en 2015–2020"; descarga → "Intentalo vos".
- L3: The new design documents were already committed on `main` in `850ba79` ("docs: versión 2 de motor de inferencia") before the branch was created; M0-00 task 1 is satisfied by that commit (the branch starts from it).
- L4: Facts for M0-00b: latest Python 3.12.16 (25/10/2026); python:3.12.16-slim digest sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b; uv 0.13.7 is only 6 days old (3/11) → Docker uses uv 0.13.5 (22/10) to respect the ≥2-week rule; Docker daemon is not running on the Mac; gitleaks, osv-scanner and pip-audit are not installed. Largest registered ZIP: 89.6 MB / 732 MB uncompressed (SIEN), max member 54 MB, max ratio 28.3 — the backlog's «unos 15 MB» is outdated; limits set as supuesto M0-00b.
- L5 (owner, 9/11/2026): "1) ok con k-01; 2) dame los comandos para validar por mi cuenta cuales son esos hallazgos que señalas; 3) no recuerdo que hayamos creado el prototipo de R, pero la carpeta de trabajo anterior es \"SideProject/pregunta-al-peru\"". Prototype found at ~/Documents/SideProjects/pregunta-al-peru/00_proyecto/investigacion/r_verificador/analista/verificar.R. gitleaks findings: grafana-api-key in catalogo/scripts/catalogo_v03_base.json:1927 and catalogo/catalogo_fuentes.json:3567 (commit f98fb753). Native review of M0-00b stopped with lens_context_budget_exceeded (candidate since 2a8f18d too large); owner decision (a) defer to M0-11 / (b) split history still open.
- L6 (owner, 9/11/2026): base regrab for M0-01 → "Sí, regrabá (recomendado)" (regrabar slice-2/base_estructurada y slice-3/base_api con sus scripts y cambiar la aserción max_alternativas a 3); review of M0-00b → "(a) Hacerla en M0-11 (recomendado)" → review mode disabled for this clone; per-part review happens in M0-11.
- L7 (owner, 9/11/2026): D-M0-00b-1 → "No es un secreto: es el enlace público de Power BI «Publicar en la web» del tablero del MEF … Exclúyelo por fingerprint en .gitleaksignore, con un comentario. … No toques la regla ni el historial. Vuelve a correr gitleaks: debe dar 0." Applied (2 identical findings excluded by fingerprint), gitleaks git = 0, verified independently. Full suite before M0-02 commit: first run 1 intermittent failure in tests/web/test_privacidad.py (uvicorn; passed 5/5 alone), rerun 1291 passed, 1 skipped.
- L8: Commit slicing: one commit per story (M0-xx), stories are the reviewable slices; per-part review in M0-11 (owner decision L6).
- L9 (owner, 9/11/2026): "OK, la configuración del entorno de R lo hago yo mismo, avanza con todo lo que no dependa de este". gfortran/survey install is the owner's; R expected values (M0-09 criteria 1–2) wait for it; agent did not use option (b) unaudited binary.
- L10 (owner, 9/11/2026): "Voy a reinstalar la biblioteca de R de verificador_r con binarios y a regenerar renv.lock. Hasta que te avise: no toques verificador_r/, no corras R ni just esperados-r, y no hagas el commit de M0-09. Sigue con lo que no dependa de R." Message arrived after commit e925215 (M0-09) already included verificador_r/; not reverted (history rewrite needs owner consent). verificador_r/ frozen for the agent until the owner says so.
- L11 (owner, 9/11/2026): R env installed with binaries (sonoma-arm64), no gfortran; renv.lock regenerated with real minqa 1.2.8 "en un commit aparte" — the change was in the tree uncommitted, so the agent committed it as 2847b2b on the owner's behalf. Asked: run esperados-r + test_esperados_r.py and close criteria 1–2 (tolerance unchanged); fix README/guia (restore with RENV_CONFIG_CACHE_ENABLED=FALSE and options(pkgType="binary")); test_verificador_r: no Title with «stub», Repository CRAN or RSPM; sha256 of each binary in auditoria_m0-09_r.md; R 4.6.2 (29/10/2026) as exception to the 2-week rule, supuesto M0-09; C-M0-09-1 resolved with date.
- L12: d89db55 (owner, 17:29:20, message «renv.lock con el minqa 1.2.8 real…») does not contain renv.lock (already in 2847b2b); it swept the M0-10 worker's in-progress tracked changes (cli.py, dim_indicador.yaml, parametros.yaml, guía, consultas, equivalencia_m0.py, recetas_m0.py). Not rewritten (needs owner consent); the M0-10 commit adds the new files.
- L13 (10/11/2026): owner: "recupera contexto de engram y continuemos con la implementación". Release `crudos-endes-2024` did not exist; the private repo was empty (GitHub refuses releases in an empty repo), so the agent added a README commit (60e40a0 in the crudos repo) and ran `scripts/respaldar_crudos.sh` (22 files). `pap almacen restaurar --bloque endes-2024` passed (20 resources OK, PS_BECA18 reconverted with identical huella_contenido_v1): `evidencia/m0-11_restauracion.txt`. `liberar` simulation: 11 ZIP, 73.0 MB (`evidencia/m0-11_liberar_simulacion.txt`); nothing freed (owner decides). `scripts/restaurar_crudos.sh` removed (replaced). Restaurar also re-places missing (freed) objects after verifying them (design §6 "reconvertir un bloque liberado obliga a bajarlo antes con pap almacen restaurar").
- L14 (10/11/2026): per-part review: 11/12 approved with observations, M0-11 blocking (H11-1 path in original_filename) fixed in 620c45c; cross-story fixes without figure changes in 4561a29 (H07-1 ejecutar_select, H07-2, H06-2, H09-2, H09-4, H10-1, H00b-5, H02-3). New owner queries C-M0-11-1 (F-04 cap) and C-M0-11-2 (n<50 high CV referencial). `just` not installed: ran scripts/auditar.sh and gitleaks directly (clean). Owner asked "cómo vamos?" mid-run.
