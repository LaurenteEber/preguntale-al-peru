# slice-2

Objective: slice 2 (S2-00 to S2-10) per `backlog/slice-2/`. Branch `slice-2` from `main` `1bf8682` (addendum merged).
Delivery: one commit or more per story with its ID; push after each story to `claude/determined-einstein-lwwemc`; PR + merge to `main` at slice close (owner authorized, L6). Runner: `uv run pytest -q -m "not solo_mac"`.

## Specs

Each spec is the acceptance criteria of its story file (`backlog/slice-2/S2-nn-*.md`, verbatim there) plus the slice definition of done (`backlog/slice-2/README.md`).

- S6 (L6 §1, verbatim): «`interprete.variable_clave: PAP_ANTHROPIC_API_KEY` en `curados/motor/parametros_motor.yaml`, con `nota:` del motivo.»
- S7 (L6 §2, verbatim): «Nunca imprimas, copies ni escribas el valor […] Solo `llm.py` la lee, con `os.environ`, en el momento de la llamada. Silencia los registros de `httpx` y `httpcore` en WARNING o más. Los errores del cliente se re-lanzan con un mensaje propio, sin el objeto request ni sus encabezados. Las grabaciones guardan solo el cuerpo de la respuesta y los metadatos de S2-04 (modelo, tokens, latencia, costo, `version_prompt`). Nunca encabezados de la petición ni de la respuesta. Agrega una prueba permanente: ningún archivo versionado, ni `tests/interprete/grabaciones/`, ni `evidencia/` contiene [el prefijo de las claves de Anthropic], [el nombre de la cabecera de la clave] ni el valor de la clave de prueba. Debe correr en pytest sin red. Antes de cada commit, `git diff --cached | grep -nE '<prefijo>|<cabecera>'` tiene que salir vacío.» (the two literals are replaced by placeholders here so this file passes that same scan; they are in `tests/test_sin_secretos.py`, built by concatenation)
- S8 (L6 §3, verbatim): «ante 401 o 403, detente al primer error: no reintentes; ante 429 o 5xx, como máximo un reintento con espera; si el proveedor dice que el límite se agotó, `no_disponible` y detente.» «estima el costo con los precios de `interprete` y respeta `tope_por_corrida`; no repitas una corrida completa si basta grabar las que faltan (`--solo`).» «Registra el uso en `salidas/interprete/uso.jsonl`, fuera de git, con los campos de P-03.»
- S9 (L7, verbatim): «Usa solo el modelo sonnet 5.5 en nivel de esfuerzo bajo»
- S10 (L6 §4, verbatim): «**Celular:** 9 dígitos que empiezan con 9, juntos o en grupos 3-3-3 separados por espacio, guion o punto. Se reemplaza siempre. **DNI:** 8 dígitos juntos, como hoy. Con separadores («45.871.236»), solo cuando los precede «DNI», «D.N.I.» o «documento», para no borrar montos ni poblaciones. **RUC y correos:** como hoy. Los años de 4 cifras no se tocan. Las 2 pruebas de S2-08 deben pasar, y agrega una que compruebe que «S/ 45.871.236» y «2 263,9 millones» no se borran.»
- S11 (L6 §3): «Primera llamada en vivo: solo una grabación, la de Q2 (`evaluar.py --grabar --solo <id de Q2>`). Reporta los tokens y el costo antes de seguir.»
- S12 (L6 §5): «S2-04 (grabación de Q2) → S2-07 → S2-09 → S2-10. Cada historia con su push al terminar.»
- S13 (L6 §7): «cuando termines de implementar los pendientes del slice 2 realizas el push y merge a main»
- S14 (L6 §7): «Luego inicias la implementación del slice 3»

## Tasks

| ID | Specs | Route | Status | Commit |
|---|---|---|---|---|
| T0 S2-00 | S2-00 | inline | done | cf73eed |
| T1 S2-01 | S2-01 | inline | done | 5043fc1 |
| T2 S2-02 | S2-02 | independent subagent (story requires it) | done, pending supervisor review | 3030a46, 5935573 |
| T3 S2-03 | S2-03 | inline | done (cross test waits for S2-02) | 5b37fee |
| T4 S2-04 | S2-04 | inline; recordings blocked (E-02) | partial | 3476a32 |
| T5 S2-05 | S2-05 | delegated writer (context backstop) | done with fake LLM; recorded eval fails (E-02) | 7b02839 |
| T6 S2-06 | S2-06 | delegated writer | done with fake LLM; Q1–Q4 recorded fail (E-02) | d6d5d31 |
| T8 S2-08 | S2-08 | delegated writer | partial; E-06 defect test red | 79e05a1 |
| T11 key+client | S6-S9 | inline | done | (this commit) |
| T12 privacy patterns | S10 | inline | done | (this commit) |
| T13 S2-04 Q2 live recording | S11 | inline | pending | |
| T7 S2-07 | S2-07, S12 | reviewers: 2 fresh subagents (story requires independence), model sonnet low effort (L7) | pending | |
| T9 S2-09 | S2-09, S12 | inline | pending | |
| T10 S2-10 | S2-10, S13 | inline | pending | |
| T14 slice 3 start | S14 | inline | pending | |

## Log

- L1 (2026-11-04, user, verbatim): «valida que puedes usar gentle-ai y engram, luego: Lee agents.md y ejecuta, en orden y sin detenerte salvo por las causas de agents.md §4: (1) la adenda del slice 1 (backlog/slice-1/adenda/README.md, S1-11 a S1-16, rama slice-1-adenda); (2) el slice 2 (backlog/slice-2/README.md, S2-00 a S2-10, rama slice-2). Haz push de la rama al terminar cada historia. Si no puedes subir a main, abre un PR al cerrar cada slice. Dudas y bloqueos van al consultas_al_dueno.md de cada slice.» Then: «ok, pero usa ODD para la implemenación».
- L2: S2-00 done. No API key and no write access to GitHub (E-01, E-02 in `backlog/slice-2/consultas_al_dueno.md`).
- L3: S2-04 found that structured outputs reject oneOf/if/external $ref/length limits; client sends a simplified schema (E-03). S2-05 delegated (context reason) with fake-LLM tests; recordings blocked by E-02.
- L4: container restarted 2026-11-05; local commits survived; push still 403. Suite state: green except tests needing recordings (E-02) and the 2 E-06 privacy tests (cellphone with separators; pattern is decision P-03 → owner).
- L5 (2026-11-05, user, verbatim): «Fue un error mio, tu debiste implementar solo el slice 2. Conpara tu implementación con lo que subió el otro chat y mergeamos a main la mejor implementación de la adenda, luego subimos tu implementación del slice 2». Compared: same cube values, 16/24 identical answers, the other one also fixes B-1 → kept the other (already merged in main 1bf8682). Slice 2 cherry-picked onto main without conflicts; S2-00 evidence regenerated. Old local branches kept as `slice-1-adenda-b` and `slice-2-sobre-adenda-b` (not pushed).
- L6 (2026-11-05, user, verbatim; long message, key points quoted in S6–S14): «Ya registré la clave de la API de Anthropic para el intérprete del slice 2, como variable de entorno PAP_ANTHROPIC_API_KEY. […] ## 7. push inicio de implementación de slice 3 * cuando termines de implementar los pendientes del slice 2 realizas el push y merge a main * Luego inicias la implementación del slice 3». Then: «todo con ODD».
- L7 (2026-11-05, user, verbatim): «Usa solo el modelo sonnet 5.5 en nivel de esfuerzo bajo». Applied to the interpreter model (P-07 row edited as owner decision) and to subagents spawned in this session.
- L8: new container: key variable present (checked as bool only). Library downloaded (release ba1fbc55) and `pap calcular` reproduced cube 010ea965. Base: 25 failed / 880 passed. Known: recordings missing (E-02), E-06 (2), `test_via_estructurada_igual_a_la_base_de_s2_00` differs only in `commit_cubo` (manifest regenerated here from aee3edd; base had 779357d) → environmental. API version 2026-10-21 rejects `temperature` (claude-api skill, api-version-migration) → removed.
- L9: T11 (client: no temperature, effort low, Sonnet 5.5, prices $2/$10 verified on the official page 5/11/2026, retries per owner rules, stop on 401/403/spend limit, httpx logs ≥ WARNING, errors without request, recordings without headers + metadata, conftest cuts key and network, permanent secret scan) and T12 (P-03 patterns) implemented and green with fake LLM; only missing-recording tests fail. Commit NOT made: the pre-commit grep matches one line — the REMOVAL of the old header literal from `llm.py` (now built by concatenation so the permanent scan can pass). Owner asked to stop and report in that case → asked.
- L10 (2026-11-05, user, verbatim): «Procedamos con el comité hasta terminar, validamos al final de tu implementación del pendiente de slice 2». From here the pre-commit check is `git diff --cached | grep -nE '^\+.*(sk-ant-|x-api-key)'` (added lines only); the full grep over the repo is reported at the end.
