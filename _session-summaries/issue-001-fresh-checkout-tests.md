# Issue #1: Backend tests fail on a fresh checkout — no such table: venues

**Date:** 2026-10-04
**Spec version:** 17d076c

## What changed and why

No new product code in this session: the fix (`Base.metadata.create_all(bind=engine)` before seeding in `backend/main.py`, commit `5d120a2`) already existed on `origin/main`. This session groomed #1 into the task template, narrowed its scope to fresh-checkout green (deferring full dev-DB isolation to #7), verified the fix via Engineer, and QA-posted PASS so the issue can be closed.

## Files created or modified

- `_session-summaries/issue-001-fresh-checkout-tests.md` (new, this file)
- GitHub issue #1 body updated to groomed template; `PM:`, `Engineer:`, `QA: PASS` comments posted (no repo file change)
- Product code: none (fix `5d120a2` predates this session; HEAD still `5d120a2`, equals `origin/main`)

## Decisions made by the human

- Directed scope split during grooming: #1 = fresh-checkout tests pass; full "never touch dev DB on import" isolation and the Alembic-vs-`create_all` decision belong to #7.
- Requested close of #1, then work on #3, following `process.md`.
- Clarified deletion tracking: record only items agents did NOT have permission to delete (not routine `.scratch`/test artifacts). No standing tracker file or follow-up issue approved yet.

## Mismatches with the spec or design docs

None (`_docs/specs.md` Backend env already documents `DATABASE_URL` default `sqlite:///./waitlist.db`; this is a test-bootstrap fix, not a product behavior change).

## Commands to validate

- **Test (all):** `make test` — frontend 30 passed, backend 52 passed, 1 deselected (Engineer and QA ran independently; no `OperationalError`).
- **Verify:** `make verify` — PASS (tests, whitespace PASS, weakened tests none; empty diff since `origin/main`).
- **Assert clean:** `make assert-clean` — PASS at `5d120a2`.

## Proposed AGENTS.md changes

None.

## Temporary changes

None. No processes started, no system changes, no large installs. Ran `make clean-scratch` — `.scratch/` is empty.

Files NOT deleted (no permission — recorded per human request, not routine cleanup):
- `./waitlist.db` (git-ignored dev database): the groomed criterion names its deletion as a human-performed destructive step. Engineer and QA intentionally skipped deleting it per `AGENTS.md` (never delete files/data you didn't create, including git-ignored files). Fresh-checkout behavior was proven instead with an isolated `.scratch` SQLite file plus the passing per-test isolated files from `tests/conftest.py`. Owner of removal: the human, if they want a literal fresh-file run.
- Per-test `test.db` files under pytest `tmp_path`: created and managed by the test run itself; agents did not delete them outside the test framework.

## Interruptions

None. PM, Engineer, QA subagents each completed; no blocked commands, no early stops. PM subagent returned grooming text without running `gh` (by design — multiline `--body` needs orchestrator-run `gh` commands); orchestrator ran `gh issue edit` and `gh issue comment`.

## Unrelated problems noticed but not fixed

- Module-level `app = create_app()` in `backend/main.py:82` still creates/touches `./waitlist.db` at import time. Explicitly out of scope here; tracked in #7 (dual schema path decision plus import-time isolation).

## Follow-ups for the next session

- Human reviews diff and pushes (per process, only the human pushes; nothing unpushed in this session — HEAD equals `origin/main`).
- Work issue #3 next (lint/typecheck gate) through full lifecycle.
- Open question: whether to create a standing tracker (follow-up issue or persistent file) for permission-blocked deletion candidates. Candidate so far: `./waitlist.db` handling (see above). No approval given yet.
