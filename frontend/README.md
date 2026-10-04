# Table Ready — frontend

React 19 + TypeScript frontend for **Table Ready**, a restaurant waitlist and table-management app. Built with TanStack Start (file-based routing), TanStack Router, TanStack Query, Vite, Tailwind CSS, and shadcn/radix UI components. It began as a generated prototype and is now wired to the FastAPI backend described below.

## Prerequisites

- `bun` (the repo root installs everything with `make install`)
- The backend running locally (repo root: `make run`), unless you use the mock service below

## Development

```sh
bun install
bun run dev
```

This starts the Vite dev server on `http://localhost:8080`. API calls go to the FastAPI backend at `VITE_API_BASE_URL` (default `http://localhost:8091/api`).

From the repo root you can run `make run-frontend` for this dev server alongside `make run` (backend on `:8091`).

## Backend wiring

- By default the app calls the FastAPI backend. The base URL comes from `VITE_API_BASE_URL` (default `http://localhost:8091/api`; see `.env.example` and `src/services/apiWaitlistService.ts`).
- Set `VITE_USE_MOCK_SERVICE=true` to use the in-browser mock service in `src/services/mockWaitlistService.ts` instead of calling the backend — useful when the backend is unavailable.
- Tests always use the mock regardless of this setting: `src/services/index.ts` selects the mock when `MODE === "test"`.

## Configuration

Copy `.env.example` to `.env` if you need to override defaults:

```bash
cp .env.example .env
```

| Variable | Purpose | Default |
|---|---|---|
| `VITE_API_BASE_URL` | FastAPI backend base URL | `http://localhost:8091/api` |
| `VITE_USE_MOCK_SERVICE` | `true` uses the in-browser mock service instead of the backend | unset (calls the real backend) |

## Tests

```sh
bun test
```

The suite covers guest submission and validation, large-party enquiries, ticket stability, cancellation, notification and return-by behaviour, table compatibility rules, and completion releasing a table. Tests run against the in-browser mock service (`src/services/mockWaitlistService.ts`), so no backend is needed.
