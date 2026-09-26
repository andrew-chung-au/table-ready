---
name: setup-project
description: One-time setup of the agent kit in a new or existing repo. Inspects the repo and spec, proposes a Makefile and AGENTS.md, and creates them after approval.
disable-model-invocation: true
---

# Set up this project

Run once per repo. Afterwards `AGENTS.md` and `_docs/agent-kit/process.md` run the project, including planning.

Work through these steps in order. Propose everything before creating anything.

1. **Check the kit is present:** `_docs/agent-kit/`, `.claude/settings.json` and `.claude/hooks/block_broad_git_add.py`. If anything is missing, stop and tell the human what to copy in.
2. **Read the spec, if there is one, and inspect the repo.** From `_docs/specs.md` and the files that exist, identify:
   - languages and package managers (for example `pyproject.toml`, `package.json`, `go.mod`)
   - how to install, run and test, and which test framework is used
   - whether there are end-to-end tests, database migrations, a linter or containers
   - any existing Makefile, task runner or scripts
   - any existing `CLAUDE.md` or `AGENTS.md`

   Where the spec names tooling the repo doesn't have yet, follow the spec. If the spec and the repo disagree, or something can't be determined, ask the human.
3. **Propose Makefile targets.** Once the stack is known, every project gets `help`, `install` and `test`. Add `run`, `test-one`, `e2e`, `migration` or `lint` only if the project has, or the spec calls for, that thing. Wrap the project's own commands; don't introduce tools the spec and repo don't use. If a Makefile exists, add to it instead of replacing it. If there is no spec and no code, the stack isn't known yet: propose a Makefile with only `help`.
4. **Propose `AGENTS.md`.** Start from `_docs/agent-kit/AGENTS.template.md`. Fill in the project half from what you found, and write "none" for any command slot the project doesn't have yet. Leave the shared Conventions block unchanged. If the repo already has a `CLAUDE.md` or `AGENTS.md` with content, carry that content into the project half and show where each part went.
5. **Show both proposals to the human and wait for approval.** List anything you guessed or couldn't determine.
6. **After approval**, create or update `Makefile` and `AGENTS.md`, and make `CLAUDE.md` contain one line: `@AGENTS.md`. Run `make help`, and `make test` if it exists, and report the results.
7. **Hand over.** Tell the human setup is done and what comes next, as described in `_docs/agent-kit/process.md`: planning if there is no spec, otherwise building the backlog.

Done when:
- `make help` lists the targets.
- Every command slot in `AGENTS.md` is a make target or "none".
- `make test` runs, if it exists. If the project has no code yet, say so instead.
