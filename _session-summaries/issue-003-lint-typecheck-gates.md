# Issue #3: Add lint and type-check commands and include them in make verify

**Date:** 2026-10-04
**Spec version:** 17d076c

## What changed and why

Added `make lint` (`uv run ruff check .`) and `make typecheck` (`cd frontend && bunx tsc --noEmit`), set an explicit ruff rule list, fixed all pre-existing errors, and wired both gates into `make verify` via `agent-kit.conf` — so the Stop hook and pre-push hook enforce them. Commits: `4e2126c` (targets + fixes), `9113285` (agent-kit.conf wiring, `HUMAN_APPROVED=1`), `dd69535` (AGENTS.md Lint/Typecheck bullets, `HUMAN_APPROVED=1`).

## Files created or modified

- `Makefile` (lint/typecheck targets + help text), `pyproject.toml` (`[tool.ruff.lint]` select/ignore/extend-immutable-calls), `agent-kit.conf` (`LINT_CMD`/`TYPECHECK_CMD`), `AGENTS.md` (Lint/Typecheck bullets)
- 11 backend source files (import order / UP fixes), 2 frontend files (bracket access for TS4111)
- `_session-summaries/issue-003-lint-typecheck-gates.md` (this file); issue #3 body groomed + `PM:`/`Engineer:`/`QA: PASS` comments; follow-up issue #8 filed

## Decisions made by the human

- Ruff select = option 1: `["E", "F", "UP", "I", "B"]` + `extend-immutable-calls` for `Depends` (over defaults-only / broader set).
- PostToolUse hook split to a follow-up (over keep-in-#3 / drop).
- Test-runner follow-up standardizes on `vitest run` (over `bun test` / defer).
- Approved the specific `agent-kit.conf` wiring change first (`HUMAN_APPROVED=1` commit after gates passed).
- Decision point: approved the Engineer-proposed `AGENTS.md` Lint/Typecheck bullets (`HUMAN_APPROVED=1`); chose to file the test-runner follow-up only (#8) — hook follow-up not filed.

## Mismatches with the spec or design docs

None (`_docs/specs.md` sections 26-27 cover architecture/testing with no lint/type-check requirements).

## Commands to validate

- **Lint:** `make lint` — All checks passed (Engineer and QA ran independently).
- **Typecheck:** `make typecheck` — exit 0, no output.
- **Test (all):** `make test` — frontend 30 passed, backend 52 passed, 1 deselected.
- **Verify:** `make verify` — PASS (tests + PASS: Lint + PASS: Type check, whitespace PASS, weakened tests none).
- **Assert clean:** `make assert-clean` — PASS at `9113285` (before AGENTS.md commit).
- `make help` lists `lint` and `typecheck`.

## Proposed AGENTS.md changes

Applied (approved): added `Lint` and `Typecheck` Commands bullets in `dd69535`. Note: the `Verify` bullet still reads "tests, whitespace and weakened-test checks" — now slightly stale since verify also runs lint/type-check; left as-is (only the two bullets were approved).

## Temporary changes

None. No processes started, no system changes, no large installs. Ran `make clean-scratch` — `.scratch/` is empty.

Files NOT deleted (no permission — recorded per human request, not routine cleanup):
- None in this issue. QA performed no fault-injection edits (would require modifying tracked files, forbidden for QA); Engineer reverted all F401/I001/TS2322 probe edits, tree verified clean.

## Interruptions

None. PM, Engineer, QA subagents each completed; no blocked commands, no early stops. QA subagent returned its `QA: PASS` text without posting (no issue-posting tool in its session); orchestrator posted it verbatim.

## Unrelated problems noticed but not fixed

- `Makefile` (`bun test`) vs `frontend/package.json` (`vitest run`) vs `frontend/README.md` (`bunx vitest run`) three-way disagreement — filed as #8 (vitest recommended).
- PostToolUse auto-lint hook (original #3 step 5) — human chose not to file a follow-up; dropped unless re-raised. Enforcement rests on `make verify` + pre-push hook.
- Frontend `eslint` gate exists in `package.json` but has no make target and unknown backlog — not filed (was "if wanted").
- Final ruff list excludes `E501` (default 88-char limit would reformat ~140 pre-existing lines including protected `_docs/agent-kit` hook scripts); commented in `pyproject.toml`.

## Follow-ups for the next session

- Human reviews diff (`git diff origin/main --stat -- .` plus full diff) and pushes (only the human pushes; pre-push hook re-runs `make verify`). Unpushed: `4e2126c`, `9113285`, `e493845` (#1 summary), `dd69535`, plus this summary.
- Next: issue #8 (test-runner unification) awaits grooming before implementation.
- Standing question: whether to create a tracker for permission-blocked deletion candidates (from #1: `./waitlist.db` handling). No approval given yet.
