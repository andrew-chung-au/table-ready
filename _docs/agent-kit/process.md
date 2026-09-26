# Development process

How work moves from idea to done in Claude Code. Project-specific values (commands, branching, push policy) are in `AGENTS.md`; this file refers to them by their bold labels, such as **Verify**.

## Start of every session

Before picking up work, the orchestrator checks the spec:

1. **No `_docs/specs.md`:** the project is in planning. See Planning.
2. **The spec changed since the last session:** take the spec version recorded in the latest session summary and run `git log --oneline <version>..HEAD -- _docs/specs.md`. If that lists any commits, run a backlog review (see Backlog) before starting an issue. If no summary records a version yet, skip this check.
3. **Otherwise:** continue with the lifecycle.

## Planning

Planning produces or revises `_docs/specs.md`. The human may write it outside the repo, or draft it with Claude (for example in plan mode).

- When Claude helps with planning, it proposes spec text; the human approves it before it's written.
- No issues are created and no product code is written until the spec exists.
- Commit spec changes on their own, with a message saying what changed.

Mid-project changes and new versions (v2) work the same way: revise the spec, then review the backlog.

## Backlog

- Tasks are GitHub issues, worked one at a time.
- **Building the backlog:** when there are no open issues and the spec has parts not yet built, the `pm` subagent proposes new issues from the spec.
- **Reviewing the backlog:** when the spec has changed, the `pm` subagent compares the change with existing issues and proposes new issues, edits to open issues, and open issues to close as not planned.
- The human approves the proposal before any issue is created, edited or closed.
- After grooming, every issue follows `_docs/agent-kit/task-template.md`.
- Read the acceptance criteria before starting work and before closing the issue.

## Roles

Each role is a Claude Code subagent in `.claude/agents/`:

- **`pm`** builds and reviews the backlog, and grooms an issue before anyone implements it. It has no file-editing tools.
- **`engineer`** implements one groomed issue and runs the `verify` skill before handing over.
- **`qa`** checks the result against the acceptance criteria and runs `verify` independently. It has no file-editing tools.

## Orchestrator

The main session is the orchestrator. It launches `pm`, `engineer` and `qa` and gives each the issue number. It does not plan the backlog, groom, implement or test itself.

## Lifecycle

1. Pick the next open issue. If there are none, build the backlog (see Backlog).
2. `pm` grooms it. Never skip this step.
3. `engineer` implements it and runs `verify`. A Stop hook also runs `make verify` whenever Claude tries to finish, and blocks it while verify fails.
4. `qa` verifies it against the acceptance criteria.
5. On FAIL, go back to step 3 with the QA comment as input.
6. On PASS, if `engineer` proposed AGENTS.md changes, show them to the human as a diff. Apply them only after approval, in their own commit.
7. Write the session summary with the `session-summary` skill.
8. Close the issue. Only the orchestrator closes issues: after QA posts PASS, or as not planned after the human approves a backlog review.
9. Repeat until the backlog is empty and every part of the spec is built.

## Commits

- Make small, focused commits at logical milestones, not one large commit at the end.
- Commit messages say what changed and why.
- Staging and pre-commit checks follow the Conventions in `AGENTS.md`.
- Branching and pushing follow the **Branching** and **Push** settings in `AGENTS.md`.
- Before approving a push, the human reads `git diff origin/main --stat`, then `git diff origin/main`, and asks about any changed file outside the issue's Constraints. A clean QA report is not proof of a clean diff.

## Definition of done

An issue is done when:

- `verify` reports PASS and QA has posted PASS, so every acceptance criterion is met.
- The changes are committed, and pushed if the **Push** setting allows.
- Docs affected by the change are updated, and any AGENTS.md change has human approval.
- The session summary is written.
- The orchestrator has closed the issue.
