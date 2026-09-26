#!/usr/bin/env bash
# Verification gates for a change. Usage: check.sh [BASE]
# BASE defaults to the branch's upstream (all unpushed work), falling back to HEAD.
set -uo pipefail

BASE="${1:-$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || echo HEAD)}"
TESTS=(':(glob)**/test_*.py' ':(glob)**/*_test.py' ':(glob)**/conftest.py'
       ':(glob)**/*.test.*' ':(glob)**/*.spec.*' ':(glob)e2e/**')
fail=0
warn=0

section() { printf '\n== %s ==\n' "$1"; }
test_diff() { git diff -U0 "$BASE" -- "${TESTS[@]}"; }

section "Changes since $BASE"
git diff --stat "$BASE"
untracked=$(git ls-files --others --exclude-standard)
if [ -n "$untracked" ]; then
  echo "Untracked files (not included in the diff):"
  echo "$untracked"
fi

section "Tests (make test)"
if make test; then
  echo "PASS: make test"
else
  echo "FAIL: make test"
  fail=1
fi

section "Whitespace (git diff --check)"
if git diff --check "$BASE"; then
  echo "PASS: no whitespace errors"
else
  echo "FAIL: whitespace errors"
  fail=1
fi

section "Weakened tests"
deleted=$(git diff --name-only --diff-filter=D "$BASE" -- "${TESTS[@]}")
if [ -n "$deleted" ]; then
  echo "FAIL: test files deleted:"
  echo "$deleted"
  fail=1
fi

skips=$(test_diff | grep -E '^\+[^+]' \
  | grep -E 'pytest\.mark\.(skip|xfail)|pytest\.skip\(|\.skip\(|\.only\(|\.todo\(|\bxit\(|\bxdescribe\(' || true)
if [ -n "$skips" ]; then
  echo "FAIL: skip, xfail or focus markers added:"
  echo "$skips"
  fail=1
fi

removed=$(test_diff | grep -E '^-[^-]' | grep -cE 'assert|expect\(' || true)
added=$(test_diff | grep -E '^\+[^+]' | grep -cE 'assert|expect\(' || true)
echo "Assertion lines: $added added, $removed removed"
if [ "$removed" -gt 0 ]; then
  echo "WARN: assertions removed or rewritten; give a reason for each:"
  test_diff | grep -E '^-[^-]' | grep -E 'assert|expect\('
  warn=1
fi

fixtures=$(git diff --name-only "$BASE" -- ':(glob)**/conftest.py')
if [ -n "$fixtures" ]; then
  echo "WARN: test fixtures changed; check they weren't loosened:"
  echo "$fixtures"
  warn=1
fi

section "Result"
if [ "$fail" -ne 0 ]; then
  echo "VERIFY: FAIL"
  exit 1
elif [ "$warn" -ne 0 ]; then
  echo "VERIFY: PASS WITH WARNINGS (each warning needs a reason)"
else
  echo "VERIFY: PASS"
fi