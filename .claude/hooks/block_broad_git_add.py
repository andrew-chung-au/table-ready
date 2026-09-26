#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block broad staging.

Claude Code sends the pending Bash tool call as JSON on stdin.
Exit 2 blocks the call and shows stderr to Claude; exit 0 lets it run.
"""
import json
import re
import shlex
import sys

BROAD_ADD_ARGS = {".", "./", "-A", "--all"}


def tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def git_subcommand(toks: list[str]) -> tuple[str | None, list[str]]:
    """Return (subcommand, args), skipping git global options such as -C <dir>."""
    if not toks or toks[0] != "git":
        return None, []
    i = 1
    while i < len(toks) and toks[i].startswith("-"):
        i += 2 if toks[i] in ("-C", "-c") else 1
    if i >= len(toks):
        return None, []
    return toks[i], toks[i + 1 :]


def is_broad(segment: str) -> bool:
    sub, args = git_subcommand(tokens(segment.strip().lstrip("(").rstrip(")")))
    if sub == "add":
        return any(a in BROAD_ADD_ARGS for a in args)
    if sub == "commit":
        # -a / --all / combined short flags such as -am stage every tracked change
        return any(
            a == "--all" or (a.startswith("-") and not a.startswith("--") and "a" in a)
            for a in args
        )
    return False


def main() -> None:
    payload = json.load(sys.stdin)
    command = payload.get("tool_input", {}).get("command", "")
    for segment in re.split(r"&&|\|\||[;|\n]", command):
        if is_broad(segment):
            print(
                "Blocked by project hook: stage explicit paths only "
                "(e.g. `git add backend/main.py`), and don't use `git commit -a`.",
                file=sys.stderr,
            )
            sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
