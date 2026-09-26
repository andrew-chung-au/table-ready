#!/usr/bin/env python3
"""Claude Code Stop / SubagentStop hook: don't let Claude finish while `make verify` fails.

- Skips when nothing changed since the upstream branch, or only Markdown changed.
- Skips when the code is identical to the last state that passed.
- Exit 2 blocks the stop and shows Claude the failure, so it fixes it.
- After MAX_BLOCKS failed attempts in one session it lets Claude stop and
  warns the human instead, so an unfixable failure can't loop forever.
Full output of the last run: .verify/last-run.log
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

MAX_BLOCKS = 3
STATE = Path(".verify")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, errors="replace"
    ).stdout


def base() -> str:
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}").strip()
    return upstream or "HEAD"


def not_state(paths: list[str]) -> list[str]:
    return [p for p in paths if p and not p.startswith(".verify/")]


def fingerprint(untracked: list[str]) -> str:
    h = hashlib.sha256()
    h.update(git("rev-parse", "HEAD").encode())
    h.update(git("diff", "HEAD", "--binary").encode())
    for path in sorted(untracked):
        h.update(path.encode())
        try:
            h.update(Path(path).read_bytes())
        except OSError:
            pass
    return h.hexdigest()


def main() -> None:
    payload = json.load(sys.stdin)
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR", "."))

    untracked = not_state(git("ls-files", "--others", "--exclude-standard").splitlines())
    changed = not_state(git("diff", "--name-only", base()).splitlines()) + untracked
    if not changed or all(p.endswith(".md") for p in changed):
        sys.exit(0)

    STATE.mkdir(exist_ok=True)
    last_pass = STATE / "last-pass"
    fp = fingerprint(untracked)
    if last_pass.exists() and last_pass.read_text() == fp:
        sys.exit(0)

    result = subprocess.run(["make", "verify"], capture_output=True, text=True, errors="replace")
    log = result.stdout + result.stderr
    (STATE / "last-run.log").write_text(log)
    blocks_file = STATE / f"stop-blocks-{payload.get('session_id', 'unknown')}"

    if result.returncode == 0:
        last_pass.write_text(fp)
        blocks_file.unlink(missing_ok=True)
        sys.exit(0)

    blocks = int(blocks_file.read_text()) if blocks_file.exists() else 0
    if blocks >= MAX_BLOCKS:
        print(json.dumps({
            "systemMessage": f"make verify is still failing after {MAX_BLOCKS} fix attempts. "
                             "Claude was allowed to stop; see .verify/last-run.log."
        }))
        sys.exit(0)

    blocks_file.write_text(str(blocks + 1))
    tail = "\n".join(log.splitlines()[-60:])
    print(
        "make verify failed, so this work isn't done. Fix the failures below, then finish. "
        "Don't weaken tests to make them pass. Full log: .verify/last-run.log\n\n" + tail,
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
