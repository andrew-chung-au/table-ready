# Issue #5: Update READMEs for the current architecture and agent workflow

**Date:** 2026-10-04
**Spec version:** 17d076c (no spec changes since; `git log 17d076c..HEAD -- _docs/specs.md` empty, so no backlog review)

## What changed and why

Rewrote the three stale docs named in the issue so they describe the current stack (FastAPI + TanStack Start, SQLite/Postgres via SQLAlchemy + Alembic, `bun` for the frontend) and added a short factual "How this project is built (AI-assisted)" section to the root README. Human direction applied: recruiter-facing tone, but every workflow sentence verifiable in a linked file — no metrics, hype, or deployed/CI-CD claims. Commits: `18d8407` (pyproject.toml), `d82702f` (frontend README), `42e2c0a` (root README).

## Files created or modified

- `pyproject.toml` (description only): "in-memory store" → "SQLite + PostgreSQL via SQLAlchemy, migrations with Alembic" (human decision Q1: option 1).
- `frontend/README.md`: removed all Lovable marketing/prototype claims and npm/npx/nvm instructions; documents FastAPI wiring (`VITE_API_BASE_URL`, `:8091`), `VITE_USE_MOCK_SERVICE=true` semantics, tests-always-use-mock, bun commands matching `package.json` + `Makefile`. History sentence names no vendor (human decision Q2: option 1).
- `README.md`: fixed `./` tree prefix, `_docs/agent-kit/process.md` paths, removed testing-guidelines/design-system required-reading claims, rewrote the AGENTS.md summary to match current `AGENTS.md`, switched setup to existing make targets, added §8 AI-assisted-build section (human decision Q3: option 1, short section).
- `_session-summaries/issue-005-readme-refresh.md` (this file); issue #5 body groomed + `PM:`/`Engineer:`/`QA: PASS` comments; follow-up issue #9 filed.

## Decisions made by the human

- pyproject.toml: "SQLite + PostgreSQL" wording (over SQLite-only as filed).
- Lovable attribution: remove marketing, at most one factual past-tense sentence (over keep-section / remove-every-mention).
- AI-workflow section: short section with link list (over longer showcase / link-only).
- Decision point: file follow-up issue #9 for remaining Lovable references (`frontend/AGENTS.md` banner, `vite.config.ts`, `package.json`, plus `bunfig.toml`, `lovable-error-reporting.ts`, `backend/config.py` comment found during grooming); human clarified the Lovable sync is disconnected and the Lovable-hosted copy is obsolete so removal is correct, and required no audience-referring language in the new ticket. Engineer choices in #5 otherwise accepted as-is.

## Mismatches with the spec or design docs

None (`_docs/specs.md` needs no change; Engineer and QA reported no spec notes).

## Commands to validate

- **Test (all):** `make test` — frontend 30 passed, backend 52 passed + 1 deselected (integration marker).
- **Lint:** `make lint` — PASS. **Typecheck:** `make typecheck` — PASS.
- **Verify:** `make verify` — PASS (Engineer and QA ran independently).
- **Assert clean:** `make assert-clean` — PASS at `42e2c0a`, HEAD unmoved after QA.
- E2E skipped (docs-only change, no user-facing behaviour; recorded in QA verdict).

## Proposed AGENTS.md changes

None.

## Temporary changes

None. No processes started, no system changes, no large installs. Ran `make clean-scratch` — `.scratch/` is empty.

## Interruptions

None. PM, Engineer, QA subagents each completed; no blocked commands, no early stops. Engineer and QA subagents returned comment text without posting (no issue-posting tool in their sessions); orchestrator posted each verbatim. PM decision questions were answered by the human with the recommendations chosen (plus Lovable-sync clarification that shaped #9).

## Unrelated problems noticed but not fixed

- Remaining Lovable references outside #5's scope — filed as #9 (see Decisions).
- `docs/ai-usage-report.md` stays a dated historical record by design; not rewritten.

## Follow-ups for the next session

- Human reviews diff (`git diff origin/main --stat -- .` plus full diff) and pushes (only the human pushes; pre-push hook re-runs `make verify`). Unpushed: `18d8407`, `d82702f`, `42e2c0a`, plus this summary.
- Next: issue #9 (Lovable removal) awaits grooming before implementation (draft body created it groomed; Engineer still needs to verify the Vite plugin subset).
- Open issues remaining: #4, #6, #7, #8, #9.
