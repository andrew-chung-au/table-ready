# AGENTS.md

<!-- PROJECT: specific to this repo. Changes need human approval (see _docs/agent-kit/process.md). -->

Table Ready: restaurant waitlist app. FastAPI backend, web frontend (bun), SQLite via SQLAlchemy + Alembic, Playwright e2e.
Layout: `backend/`, `frontend/`, `tests/`, `e2e/`, `_docs/`, `_session-summaries/`, `Makefile`, `Dockerfile`, `docker-compose.yml`.

## Commands

- **Install:** `make install`
- **Run:** `make run` (backend on port 8091) and `make run-frontend`
- **Test (all):** `make test`
- **Test (one file):** `make test-one FILE=tests/test_tables.py` (paths under `frontend/` run with bun)
- **Verify:** `make verify`. Tests, whitespace and weakened-test checks; used by the `verify` skill.
- **E2E:** `make e2e`. Starts and stops its own docker-compose stack. Needs Docker running and port 8091 free, so stop `make run` first.
- **New migration:** `make migration MSG="what changed"`

## Project settings

- **Branching:** commit directly to `main`.
- **Push:** only with human approval.
- **Dependencies:** `uv add <package>` for the backend; `bun add <package>` in `frontend/`.

## Project gotchas

- Every model change needs a migration (**New migration** command). Review the generated file before committing.
- Port 8091 is hard-coded in several places. To change it, search the repo for `8091` and update every match. `PORT`/`DEFAULT_PORT` in `backend/config.py` is unused.

<!-- SHARED: copied from _docs/agent-kit/AGENTS.template.md. Change it there first, then copy it here. -->

## Conventions

- The product spec is `_docs/specs.md`. The human owns it: propose changes, and make them only after approval. If it doesn't exist yet, the project is in planning (see `_docs/agent-kit/process.md`).
- Run project commands through `make`. If you need a command that has no target, propose a new Makefile target instead of documenting a raw command.
- When you add or change a Makefile target, propose the matching change to the Commands section of `AGENTS.md`.
- Change only files the current task needs. If you spot an unrelated problem, note it in the session summary instead of fixing it.
- Ask before adding a dependency.
- Stage explicit paths only (`git add path/to/file`). Never use `git add .`, `git add -A`, or `git commit -a`.
- Before each commit, show `git status --short`, `git diff --check`, and the exact paths being staged.
- Don't edit AGENTS.md, CLAUDE.md or `.claude/` without human approval.
- Work isn't done until the `verify` skill reports PASS.
- Working a GitHub issue → `_docs/agent-kit/process.md`. The main session orchestrates; the `pm`, `engineer` and `qa` subagents are in `.claude/agents/`.
