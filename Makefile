HOST ?= 0.0.0.0
PORT ?= 8000

run-server:
	uvicorn app.main:server --host $(HOST) --port $(PORT)

run-server-dev:
	uvicorn app.main:server --host 0.0.0.0 --port 3636 --reload

# ── Docker — environment targets ─────────────────────────────────────────────
# Usage:
#   make dev       — development (hot-reload)
#   make staging   — staging
#   make prod      — production

dev:
	APP_ENV=development DOCKER_TARGET=development docker compose up -d --build

staging:
	APP_ENV=staging docker compose up -d --build

prod:
	APP_ENV=production docker compose up -d --build

# ── Docker — generic targets ─────────────────────────────────────────────────

up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=100

# Start only the databases (no app container)
up-db:
	docker compose up -d mongodb postgres mysql mssql redis

# One-time: create the MSSQL database (SQL Server doesn't auto-create it)
init-mssql:
	@echo "Waiting for MSSQL to be healthy..."
	@until docker exec fastapi-mssql /opt/mssql-tools18/bin/sqlcmd \
		-S localhost -U sa -P '$${MSSQL_PASSWORD:-Password123!}' -C \
		-Q "SELECT 1" -b > /dev/null 2>&1; do \
		echo "  MSSQL not ready yet, retrying in 3s..."; sleep 3; \
	done
	docker exec fastapi-mssql /opt/mssql-tools18/bin/sqlcmd \
		-S localhost -U sa -P '$${MSSQL_PASSWORD:-Password123!}' -C \
		-Q "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '$${MSSQL_DATABASE:-project_name}') CREATE DATABASE [$${MSSQL_DATABASE:-project_name}];"
	@echo "MSSQL database ready."

# Full first-time setup: start all + init MSSQL + create tables
setup: up
	@sleep 5
	$(MAKE) init-mssql
	$(MAKE) init-db
	@echo "All services running. API at http://localhost:18000"

# Initialise SQL tables / MongoDB indexes for all (or specific) backends
# Usage:
#   make init-db                          # all enabled backends
#   make init-db BACKENDS=mongodb,postgresql  # specific backends
init-db:
ifdef BACKENDS
	python -m scripts.init_db --backends $(BACKENDS)
else
	python -m scripts.init_db
endif

# Reset all volumes (DESTRUCTIVE)
reset:
	docker compose down -v
	@echo "All volumes removed."