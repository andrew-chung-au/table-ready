---
name: verify
description: Verify a finished change before calling it done. Use after implementing or refactoring code, before handing work to QA, and when QA checks an issue. Runs the tests, checks the diff for weakened tests, and reports PASS or FAIL with evidence.
---

# Verify a change

Done means the gates were run and their results observed, not that the code looks right.

1. Run `make verify`. It compares against the upstream branch by default, which covers all unpushed work. To check from a specific commit, run `make verify BASE=<commit>`.
2. Read the diff yourself (`git diff <base>`), plus any untracked files the script lists.
3. For every WARN, give a one-line reason it is legitimate, such as "assertion rewritten for the renamed field". If you can't, treat it as a FAIL.
4. Report in this form:

   ```
   Verify: PASS | FAIL
   - make test: <passed and failed counts>
   - whitespace: PASS | FAIL
   - weakened tests: none | <what was found, with your reason for each>
   - files changed: <from the diff stat>
   ```

Don't edit a test to make `make verify` pass unless the issue's acceptance criteria change that behaviour. If you do, say so in the report.