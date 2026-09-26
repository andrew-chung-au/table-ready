---
name: session-summary
description: Write the session summary at the end of an orchestrator session, whether it was issue work, planning or a backlog review.
---

# Write the session summary

1. Name the file in `_session-summaries/`:
   - issue work: `issue-<NNN>-<short-name>.md`, with the issue number padded to three digits, for example `issue-004-sqlite-persistence.md`
   - planning or a backlog review: `planning-<YYYY-MM-DD>-<short-name>.md`
2. Get the spec version with `git log -1 --format=%h -- _docs/specs.md`. If there is no spec yet, write "none".
3. Fill in [template.md](template.md). Keep each section to a few lines, and write "none" rather than leaving a section out.
4. Commit it on its own: `git add _session-summaries/<file>`, with a message like "Add session summary for issue #004".