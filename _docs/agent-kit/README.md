# Agent kit

Reusable files for running a project with Claude Code: the workflow, the PM, Engineer and QA subagents, skills and guardrails. Nothing in the kit is specific to one project.

## What's in it

- `_docs/agent-kit/`: the process, task template and `AGENTS.md` template
- `.claude/agents/`: the `pm`, `engineer` and `qa` subagents. `pm` and `qa` have no file-editing tools
- `.claude/skills/verify/`: runs the tests and checks for weakened tests; its gates are in `check.sh`, run by `make verify`
- `.claude/skills/session-summary/`: the naming rule and template for session summaries
- `.claude/skills/setup-project/`: the one-time setup, run as `/setup-project`
- `.claude/settings.json`: asks your approval before agents edit `AGENTS.md`, `CLAUDE.md`, `.claude/` or the spec, or run `git push`; stops agents reading `.env` files
- `.claude/hooks/block_broad_git_add.py`: blocks `git add .`, `git add -A` and `git commit -a`
- `CLAUDE.md`: one line, `@AGENTS.md`

## Starting a project

You need `git`, `make` and `python3` installed.

1. Get the kit into the repo:
   - **New repo:** create it from the kit's GitHub template ("Use this template"), then open it locally or in a codespace.
   - **Existing repo:** copy `_docs/agent-kit/` and `.claude/` into it. Copy `CLAUDE.md` too, unless the repo already has one; setup merges it.
2. Optional: put a product spec at `_docs/specs.md`. Without one, the project starts in planning.
3. Run `claude` in the repo root and type `/setup-project`.
4. Review what it proposes, approve or correct it, then commit.
5. Check that `/hooks` and `/permissions` list the kit's hook and rules.

From there, `AGENTS.md` and `_docs/agent-kit/process.md` take over.

## Improving the kit

When you improve a kit file in one project, make the same change in the kit's template repo so the next project gets it.