# Issue #2: Pin the Python version to match the Dockerfile

**Date:** 2026-10-04
**Spec version:** 17d076c

## What changed and why

Pinned Python to 3.12 so local, Codespaces and Docker all run the same interpreter. Local venv was on 3.14.5 while the Dockerfile backend stage uses `python3.12-bookworm-slim`. Added `.python-version` (`3.12`), narrowed `requires-python` to `>=3.12,<3.13`, regenerated `uv.lock` under 3.12.

## Files created or modified

- `.python-version` (new, `3.12`)
- `pyproject.toml` (requires-python `>=3.11` → `>=3.12,<3.13`)
- `uv.lock` (regenerated; header `==3.12.*`, pruned non-3.12 wheels)
- Committed as `8ba63af`; issue #2 closed after QA PASS.

## Decisions made by the human

- `requires-python` = `>=3.12,<3.13` (over `==3.12.*` / keep `>=3.11` + pin only).
- `.python-version` content = `3.12` (over full patch pin).
- Approved PM grooming edit, then approved Engineer implementation.
- Decision point: close #2 and human pushes (approved).

## Mismatches with the spec or design docs

None (`_docs/specs.md` does not pin a Python version).

## Commands to validate

- **Test (all):** `make test` — frontend 30 passed, backend 52 passed, 1 deselected (integration).
- **Verify:** `make verify` — PASS (Engineer and QA ran independently).
- **Assert clean:** `make assert-clean` — FAIL only due to pre-existing unrelated `M backend/main.py` (#1 fix, untouched by this issue); HEAD stable at `8ba63af`.

## Proposed AGENTS.md changes

None.

## Temporary changes

None. No processes started, no system changes, no large installs. Ran `make clean-scratch` — `.scratch/` is empty.

## Interruptions

None. PM, Engineer, QA subagents each completed; no blocked commands, no early stops.

## Unrelated problems noticed but not fixed

- `backend/main.py` has a pre-existing uncommitted `Base.metadata.create_all()` fallback fix for #1; left untouched. Tracked for later review in #7.

## Follow-ups for the next session

- Human reviews diff and pushes (per process, only the human pushes).
- Existing dev venvs still need `rm -rf .venv && uv sync` by the human (destructive step named in #2 criterion, not run by agents).
