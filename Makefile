.PHONY: help install run run-frontend dev test test-frontend test-backend test-one verify migration e2e

help: ## List targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_ -]+:.*## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install backend and frontend dependencies
	uv sync
	cd frontend && bun install

run: ## Apply migrations, then start the backend on port 8091
	uv run alembic upgrade head
	uv run uvicorn backend.main:app --reload --port 8091

run-frontend dev: ## Start the frontend dev server
	cd frontend && bun run dev

test: test-frontend test-backend ## Run frontend and backend unit tests

test-frontend:
	cd frontend && bun test

test-backend:
	uv run pytest

test-one: ## Run one test file: make test-one FILE=tests/test_tables.py
	@test -n "$(FILE)" || { echo "Usage: make test-one FILE=path/to/test_file"; exit 1; }
	@case "$(FILE)" in \
		frontend/*) cd frontend && bun test "./$(patsubst frontend/%,%,$(FILE))" ;; \
		*) uv run pytest "$(FILE)" ;; \
	esac

verify: ## Run all verification gates: make verify [BASE=<commit>]
	@bash .claude/skills/verify/check.sh $(BASE)

migration: ## Create an Alembic migration: make migration MSG="add notes to tables"
	@test -n "$(MSG)" || { echo 'Usage: make migration MSG="what changed"'; exit 1; }
	uv run alembic revision --autogenerate -m "$(MSG)"

# Builds and starts the docker-compose.yml stack, waits for the app to
# accept requests, runs the Playwright suite in e2e/ against it, then tears
# the stack back down (even if the tests fail, so it doesn't leak containers).
e2e: ## Run the Playwright suite against the docker-compose stack
	docker compose up -d --build
	@echo "Waiting for the app to become ready on http://localhost:8091..."
	@i=0; until curl -sf http://localhost:8091/api/venue > /dev/null 2>&1; do \
		i=$$((i + 1)); \
		if [ $$i -ge 60 ]; then \
			echo "Timed out waiting for the app to become ready"; \
			docker compose down; \
			exit 1; \
		fi; \
		sleep 2; \
	done
	(cd e2e && npm install && npx playwright install --with-deps chromium && npm test); \
	status=$$?; \
	docker compose down; \
	exit $$status
