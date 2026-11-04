# slice-2

Objective: slice 2 (S2-00 to S2-10) per `backlog/slice-2/`. Branch `slice-2`, stacked on `slice-1-adenda` (not merged into `main`).
Delivery: one commit or more per story with its ID; push after each story (blocked: 403); PR after the addendum's. Runner: `uv run pytest -q -m "not solo_mac"`.

## Specs

Each spec is the acceptance criteria of its story file (`backlog/slice-2/S2-nn-*.md`, verbatim there) plus the slice definition of done (`backlog/slice-2/README.md`).

## Tasks

| ID | Specs | Route | Status | Commit |
|---|---|---|---|---|
| T0 S2-00 | S2-00 | inline | done | cf73eed |
| T1 S2-01 | S2-01 | inline | done | 5043fc1 |
| T2 S2-02 | S2-02 | independent subagent (story requires it) | in progress | 3030a46 (brief) |
| T3 S2-03 | S2-03 | inline | done (cross test waits for S2-02) | 5b37fee |
| T4 S2-04 | S2-04 | inline; recordings blocked (E-02) | partial | 3476a32 |
| T5 S2-05 | S2-05 | delegated writer (context backstop) | in progress | |
| T5–T10 | S2-05..S2-10 | inline; LLM parts blocked (E-02) | pending | |

## Log

- L1 (2026-11-04, user, verbatim): see `odd/tasks/slice-1-adenda.md` L1; L2 «ok, pero usa ODD para la implemenación».
- L2: S2-00 done. No API key and no write access to GitHub (E-01, E-02 in `backlog/slice-2/consultas_al_dueno.md`).
- L3: S2-04 found that structured outputs reject oneOf/if/external $ref/length limits; client sends a simplified schema (E-03). S2-05 delegated (context reason) with fake-LLM tests; recordings blocked by E-02.
