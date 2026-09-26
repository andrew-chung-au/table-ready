# AGENTS.md

<!-- PROJECT: specific to this repo. Changes need human approval (see _docs/agent-kit/process.md). -->

<Project name>: <one line on what it is and the stack>.
Layout: <top-level folders and key files>.
Product spec: `_docs/specs.md`.

## Commands

<!-- Every slot points to a make target. Write "none" for a slot the project doesn't use. -->

- **Install:** `make install`
- **Run:** `make run`
- **Test (all):** `make test`
- **Test (one file):** `make test-one FILE=<example path>`
- **E2E:** `make e2e` <prerequisites, or "none">
- **New migration:** `make migration MSG="what changed"` <or "none">

## Project settings

- **Branching:** <e.g. commit directly to `main` / short-lived `feat/...` branches merged by PR>
- **Push:** <e.g. only with human approval>
- **Dependencies:** <the command for adding each kind of dependency>

## Project gotchas

- <Things an agent would get wrong without being told. Delete this section if there are none.>

<!-- SHARED: copied from _docs/agent-kit/AGENTS.template.md. Change it there first, then copy it here. -->

## Conventions

- Run project commands through `make`. If you need a command that has no target, propose a new Makefile target instead of documenting a raw command.
- Change only files the current task needs. If you spot an unrelated problem, note it in the session summary instead of fixing it.
- Ask before adding a dependency.
- Stage explicit paths only (`git add path/to/file`). Never use `git add .`, `git add -A`, or `git commit -a`.
- Before each commit, show `git status --short`, `git diff --check`, and the exact paths being staged.
- Don't edit AGENTS.md, CLAUDE.md or `.claude/` without human approval.
- Working a GitHub issue → `_docs/agent-kit/process.md`. The main session orchestrates; subagents follow their role file in `_docs/agent-kit/team/`.