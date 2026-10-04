# Issue #9: Remove disconnected Lovable integration from frontend build and config

**Date:** 2026-10-04
**Spec version:** 17d076c (no spec changes since; `git log 17d076c..HEAD -- _docs/specs.md` empty, so no backlog review)

## What changed and why

Removed the disconnected Lovable integration so the frontend builds, runs and tests on the repo's own toolchain. The `@lovable.dev/vite-tanstack-config` wrapper was replaced by an explicit `vite.config.ts`. The editor-only error reporting, the `frontend/AGENTS.md` banner and every `lovable` string in the frontend config, lockfile and backend comment are gone. CORS defaults, routes and the error boundary's visible UI are unchanged. Commits: `cecfca1` (removal), `7b74d18` (QA fix: moved the "no Lovable references" guard out of `frontend/src`).

## Files created or modified

- `frontend/vite.config.ts`: the wrapper is replaced by explicit plugins: Tailwind, tsconfig-paths, TanStack Start (including `importProtection`), nitro for builds only, and React. It keeps the `@` alias, lightningcss, the dedupe/optimizeDeps lists and port 8080. An inline prerender shim of about 40 lines bridges nitro's output to TanStack Start's SPA prerender.
- `frontend/package.json`: removed the wrapper from devDependencies.
- `frontend/bun.lock`:
  - Regenerated with `bun install`.
  - Re-resolved vitest (`bun remove vitest`, then `bun add -d vitest@^5.0.0`, which gave 5.0.3) to clear 19 `lovable-core-prod/sandbox-npm-cache` URLs.
  - Three `@emnapi` entries were re-hoisted at the same versions.
- `frontend/bunfig.toml`: `minimumReleaseAgeExcludes = []`.
- `frontend/src/routes/__root.tsx`: removed the reporter import and call, and the now-empty `useEffect` and its import.
- `backend/config.py`: comment only; the `ALLOWED_ORIGINS` default is byte-identical.
- Deleted: `frontend/AGENTS.md`, `frontend/src/lib/lovable-error-reporting.ts`.
- New tests: `frontend/src/__tests__/viteConfig.test.ts`, `tests/test_config.py`, `tests/test_no_lovable.py`.
- Issue #9 body amended by the PM (criteria 4, 8, 11, 12, Constraints, Out of scope). Follow-up issue #10 filed.

## Decisions made by the human

- Lockfile: re-resolve vitest only (option B), over regenerating the whole lockfile or deferring the leftover URLs.
- Criterion 8: check `.output/public/_shell.html` (the real build output the Dockerfile uses), not `dist/client/index.html`.
- Criterion 12 widened: remove the empty `useEffect` and its import.
- Decision point: all Engineer choices not covered by the issue were accepted as-is:
  - `frontend/AGENTS.md` deleted rather than emptied;
  - the build shim;
  - TanStack devtools, the 1s watch debounce and the Lovable plugins dropped;
  - the three test files outside the issue's file list.
- Clean-install check: `docker compose build` instead of `make e2e`. The human spotted that the empty `.dockerignore` let the first build copy the old local `node_modules`, then deleted `frontend/node_modules`. A rebuild without it passed.
- Follow-up #10 filed. It moves nitro off the cloudflare-module preset and tries to drop the shim, uses Vite's native tsconfig paths, adds a `.dockerignore`, and uses one package manager (bun, as in `make install`) with a frozen lockfile in the Dockerfile.

## Mismatches with the spec or design docs

None (`_docs/specs.md` has no Lovable mentions; no role reported spec notes).

## Commands to validate

- **Verify:** `make verify`: PASS (Engineer, QA, and the orchestrator after a fresh `make install`). 35 frontend and 57 backend tests passed, 1 deselected; lint, typecheck and whitespace pass; 22 assertion lines added, 0 removed.
- **Assert clean:** `make assert-clean`: PASS after both QA runs (HEAD `cecfca1`, then `7b74d18`).
- Build: `bun run build` emits `.output/public/_shell.html` plus assets. `make run-frontend` serves 200 on :8080.
- `docker compose build` with no `frontend/node_modules`: PASS.
- **E2E:** not run. It installs system packages via Playwright; #10 covers the decision.

## Proposed AGENTS.md changes

None.

## Temporary changes

- Dev servers started by the Engineer and QA through PID-recording `.scratch/` scripts were stopped; port 8080 was confirmed closed.
- `docker compose build` (orchestrator) left the `table-ready-app` and `table-ready-migrate` images; no containers are running (`docker compose ps` is empty).
- The human deleted `frontend/node_modules`; the orchestrator restored it with `make install`, and `bun.lock` was unchanged.
- Git-ignored build output remains: `frontend/.output/`, `frontend/.wrangler/`, `frontend/dist/`.
- Ran `make clean-scratch`: `.scratch/` is empty.

## Interruptions

None. Engineer stopped once by design on criterion 4 (lockfile URLs survived `bun install`) and criterion 8 (wrong output path); the human decided, Engineer resumed. QA FAILed once on criterion 6 (the Engineer's own test file in `frontend/src` contained the search term); fixed in `7b74d18`, fresh QA run PASSed. No blocked commands.

## Unrelated problems noticed but not fixed

- Issue #4 ("Build the frontend in Docker with bun and its lockfile") overlapped #10's package-manager item; closed as a duplicate of #10 with the human's approval.
- Gaps in the `tests/test_no_lovable.py` guard, judged minor by QA:
  - it skips folders named `dist` or `.output` at any depth;
  - it doesn't follow symlinks;
  - it reads git-ignored local files.
- `tests/test_config.py` and `tests/test_no_lovable.py` contain the word "lovable", so a future repo-wide search will match them.

## Follow-ups for the next session

- The human reviews the diff (`git diff origin/main --stat -- .` plus the full diff) and pushes. Unpushed: `cecfca1`, `7b74d18`, and this summary.
- #10 needs PM grooming before an Engineer starts. The PM filed it pre-groomed with approved scope; its open points are the `make e2e` system-install approval and the PM's grooming defaults (context under 10 MB, pinned bun image, `e2e/` staying on npm).
- Open issues: #6, #7, #8, #10.
