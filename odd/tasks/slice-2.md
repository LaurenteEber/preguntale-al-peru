# slice-2

Objective: slice 2 (S2-00 to S2-10) per `backlog/slice-2/`. Branch `slice-2`, stacked on `slice-1-adenda` (not merged into `main`).
Delivery: one commit or more per story with its ID; push after each story (blocked: 403); PR after the addendum's. Runner: `uv run pytest -q -m "not solo_mac"`.

## Specs

Each spec is the acceptance criteria of its story file (`backlog/slice-2/S2-nn-*.md`, verbatim there) plus the slice definition of done (`backlog/slice-2/README.md`).

## Tasks

| ID | Specs | Route | Status | Commit |
|---|---|---|---|---|
| T0 S2-00 | S2-00 | inline | done | |
| T1 S2-01 | S2-01 | inline | pending | |
| T2 S2-02 | S2-02 | independent subagent (story requires it) | pending | |
| T3 S2-03 | S2-03 | inline | pending | |
| T4 S2-04 | S2-04 | inline; recordings blocked (E-02) | pending | |
| T5–T10 | S2-05..S2-10 | inline; LLM parts blocked (E-02) | pending | |

## Log

- L1 (2026-11-04, user, verbatim): see `odd/tasks/slice-1-adenda.md` L1; L2 «ok, pero usa ODD para la implemenación».
- L2: S2-00 done. No API key and no write access to GitHub (E-01, E-02 in `backlog/slice-2/consultas_al_dueno.md`).
