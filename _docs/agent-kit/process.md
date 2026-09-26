# Development process

How work moves from backlog to done. Project-specific values (commands, branching, push policy, where the spec lives) are in `AGENTS.md`; this file refers to them by their bold labels, such as **Test (all)**.

## Backlog

- Tasks are GitHub issues, worked one at a time.
- After grooming, every issue follows `_docs/agent-kit/task-template.md`.
- Read the acceptance criteria before starting work and before closing the issue.

## Roles

- **PM** grooms an issue before anyone implements it. Follows `_docs/agent-kit/team/pm.md`.
- **Engineer** implements one groomed issue. Follows `_docs/agent-kit/team/software-engineer.md`.
- **QA** checks the result against the acceptance criteria. Follows `_docs/agent-kit/team/qa-engineer.md`.

## Orchestrator

The main session is the orchestrator. It launches the PM, Engineer and QA as subagents and gives each the issue number. It does not groom, implement or test itself.

## Lifecycle

1. Pick the next open issue.
2. PM grooms it. Never skip this step.
3. Engineer implements it.
4. QA verifies it.
5. On FAIL, go back to step 3 with the QA comment as input.
6. On PASS, if the Engineer proposed AGENTS.md changes, show them to the human as a diff. Apply them only after approval, in their own commit.
7. Write the session summary.
8. Close the issue. Only the orchestrator closes issues, and only after QA posts PASS.
9. Repeat until the backlog is empty.

## Commits

- Make small, focused commits at logical milestones, not one large commit at the end.
- Commit messages say what changed and why.
- Staging and pre-commit checks follow the Conventions in `AGENTS.md`.
- Branching and pushing follow the **Branching** and **Push** settings in `AGENTS.md`.

## Session summaries

Each orchestrator session writes one file to `_session-summaries/`, named `issue-<NNN>-<short-name>.md`: the issue number padded to three digits, then a short hyphenated description. Example: `issue-004-sqlite-persistence.md`.

Each summary includes:

- What changed and why.
- Files created or modified.
- Mismatches with the product spec or other design docs.
- Commands to validate, using the labels from `AGENTS.md`.
- Proposed AGENTS.md changes, or "none".
- Unrelated problems noticed but not fixed.
- Follow-ups or decisions for the next session.

## Definition of done

An issue is done when:

- QA has posted PASS, so every acceptance criterion is met.
- The changes are committed, and pushed if the **Push** setting allows.
- Docs affected by the change are updated, and any AGENTS.md change has human approval.
- The session summary is written.
- The orchestrator has closed the issue.