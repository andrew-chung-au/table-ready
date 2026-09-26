# Setting up a new project with the agent kit

The agent kit is `_docs/agent-kit/` plus `.claude/`. Nothing in them is specific to one project.

1. Copy `_docs/agent-kit/` and `.claude/` into the new repo.
2. Create a `Makefile` with the standard targets: `help`, `install`, `run`, `test`, `test-one`, `e2e`, and `migration` if the project has a database. A target that doesn't apply prints "not used in this project" and exits 0.
3. Copy `_docs/agent-kit/AGENTS.template.md` to `AGENTS.md` at the repo root. Fill in the project half; leave the shared Conventions block unchanged.
4. Create `CLAUDE.md` at the repo root containing one line: `@AGENTS.md`.
5. Put the product spec in `_docs/specs.md`.
6. Create an empty `_session-summaries/` folder.
7. Make the hook executable: `chmod +x .claude/hooks/block_broad_git_add.py`.
8. Start Claude Code in the repo and check `/hooks` and `/permissions` list the kit's hook and rules.

When you improve a kit file in one project, copy the change back to your master copy of the kit so the next project gets it.