# FastAPI Template

A production-ready, modular FastAPI project template with an **async-native database layer** supporting MongoDB, PostgreSQL, MySQL, and MSSQL out of the box.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start (Docker)](#quick-start-docker)
- [Local Development (without Docker)](#local-development-without-docker)
- [Configuration](#configuration)
- [Switching Database Backends](#switching-database-backends)
- [Adding Custom Config Keys](#adding-custom-config-keys)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Makefile Commands](#makefile-commands)
- [Important Warnings](#important-warnings)

---

## Features

- **FastAPI** with modular router structure (auth, users, items, tasks)
- **Async-native database layer** — Motor, asyncpg, aiomysql drivers; all service methods are `async def`
- **Backend-agnostic** — swap between MongoDB / PostgreSQL / MySQL / MSSQL via config
- **Abstract base classes** (`BaseDatabaseManager`, `BaseDocument`) for adding custom backends
- **Manager registry** — run multiple databases side-by-side
- **Connection pooling** and health checks for all backends
- **YAML-first config** — single `config.yaml` with per-environment sections; env vars override any value
- **JWT authentication** with role-based permissions
- **Structured logging** via Loguru
- **Redis** for caching
- **Docker Compose** — dev (code mount + hot-reload) and production (code baked in) via override file
- **Global exception handlers** — consistent JSON error responses
- **Versioned APIs** — v1 and v2 demonstrate the Template Method pattern for adding API versions
- **Test suite** — pytest with in-memory async mocks, no real DB required

---

## Architecture

```
BaseDocument (ABC, async)
├── MongoDBDocument           ← Motor (AsyncIOMotorClient)
├── SQLDocument (async base)
│   ├── PostgreSQLDocument    ← SQLAlchemy asyncio + asyncpg
│   └── MySQLDocument         ← SQLAlchemy asyncio + aiomysql
└── MSSQLDocument             ← thread-executor wrapper (no native async MSSQL driver)
```

Every service method is `async def` and calls the model directly with `await`:

```python
async def create_item(self, data: dict):
    await self.model.insert_one(payload)
```

---

## Quick Start (Docker)

This is the **recommended** way to run the project. All databases are included.

```bash
# 1. Clone the repository
git clone <repo-url> && cd fastapi-template

# 2. Start all services (dev mode — code mounted, hot-reload active)
make dev
# or: docker compose up -d --build

# 3. Wait for health checks (MSSQL takes ~30s)
docker compose ps

# 4. Create the MSSQL database (one-time setup — see warning below)
make init-mssql

# 5. API is available at http://localhost:18000
#    Docs:         http://localhost:18000/docs
#    Health check: http://localhost:18000/health
```

### Production / Staging

```bash
# Staging — no code mount, code baked into image
make staging

# Production
make prod

# Or explicitly (skip docker-compose.override.yml)
APP_ENV=production docker compose -f docker-compose.yml up -d --build
```

> **MSSQL Database Warning:** Unlike PostgreSQL and MySQL, SQL Server does **not** auto-create databases from environment variables. Run `make init-mssql` after the first `docker compose up`. This only needs to be done once — the data persists in the `mssql_data` volume.

---

## Local Development (without Docker)

### Prerequisites

| Dependency | Required for | Install |
|---|---|---|
| **Python 3.10+** | All | `conda create -n fastapi-template python=3.10` |
| **MongoDB 7+** | MongoDB backend | Running instance or Docker |
| **Redis 7+** | Caching | Running instance or Docker |
| **unixODBC** | MSSQL backend | `sudo apt-get install unixodbc-dev` |
| **ODBC Driver 18** | MSSQL backend | See [MSSQL ODBC Driver Install](#mssql-odbc-driver-install) |

### Setup

```bash
# 1. Create and activate conda environment
conda create -n fastapi-template python=3.10 -y
conda activate fastapi-template

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start only the databases
docker compose up -d mongodb redis

# 4. Edit app/configs/config.yaml — set hosts to localhost in the development section

# 5. Run the dev server
make run-server-dev
# or: uvicorn app.main:server --host 0.0.0.0 --port 3636 --reload
```

### MSSQL ODBC Driver Install

> **Warning:** The MSSQL backend requires the **Microsoft ODBC Driver 18 for SQL Server** installed at the OS level.

**Ubuntu / Debian:**

```bash
sudo apt-get install -y unixodbc-dev
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
  | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] \
  https://packages.microsoft.com/ubuntu/24.04/prod noble main" \
  | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update && sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

**macOS:**

```bash
brew install unixodbc
brew tap microsoft/mssql-release https://github.com/microsoft/homebrew-mssql-release
brew install msodbcsql18
```

---

## Configuration

All configuration is in **`app/configs/config.yaml`** — a single file with per-environment sections. Environment variables override any YAML value at runtime.

### How It Works

```
Load order (highest priority first):
  1. Environment variables    ← MONGODB_PASSWORD=secret, AUTH_SECRET_KEY=...
  2. config.yaml[APP_ENV]     ← the section matching APP_ENV (default: development)
```

Switch environment by setting `APP_ENV`:

```bash
APP_ENV=production uvicorn app.main:server ...
APP_ENV=staging docker compose -f docker-compose.yml up
```

### config.yaml structure

```yaml
_defaults: &defaults        # shared base (YAML anchor)
  app_port: 8000
  mongodb_host: localhost
  ...

development:
  <<: *defaults             # inherit all defaults
  log_write_to_file: false  # override only what differs
  auth_expire_seconds: 86400

staging:
  <<: *defaults
  mongodb_host: mongodb     # docker service name

production:
  <<: *defaults
  mongodb_host: mongodb
  mongodb_max_pool_size: 100
```

### Key Config Fields

| Field | Description |
|---|---|
| `app_env` | Active environment: `development`, `staging`, `production` |
| `db_type` | Backend used by the auth module: `mongodb`, `postgresql`, `mysql`, `mssql` |
| `enabled_backends` | Backends connected at startup: comma-separated or `all` |
| `mongodb_host` / `_port` / `_database` | MongoDB connection |
| `pg_host` / `_port` / `_database` | PostgreSQL connection |
| `mysql_host` / `_port` / `_database` | MySQL connection |
| `mssql_host` / `_port` / `_database` | MSSQL connection |
| `auth_secret_key` | JWT signing secret — **always override via env var** |
| `auth_expire_seconds` | JWT token TTL |
| `superuser_username` | Username with superuser privileges |

### Overriding with Environment Variables

Any field can be overridden at runtime using its uppercased name:

```bash
MONGODB_PASSWORD=secret AUTH_SECRET_KEY=my-key APP_ENV=production uvicorn app.main:server
```

In Docker:
```yaml
# docker-compose.yml environment block
- MONGODB_PASSWORD=${MONGODB_PASSWORD:-password}
- AUTH_SECRET_KEY=${AUTH_SECRET_KEY:-change-me}
```

---

## Switching Database Backends

Change `db_type` and `enabled_backends` in `config.yaml` (or via env var):

```yaml
development:
  db_type: postgresql
  enabled_backends: postgresql
```

Or at runtime:
```bash
DB_TYPE=postgresql ENABLED_BACKENDS=postgresql uvicorn app.main:server
```

| `db_type` value | Backend |
|---|---|
| `mongodb` | MongoDB (Motor) |
| `postgresql`, `postgres`, `pg` | PostgreSQL (asyncpg) |
| `mysql`, `mariadb` | MySQL (aiomysql) |
| `mssql` | SQL Server (thread-executor) |

---

## Adding Custom Config Keys

Add any key to `config.yaml` — it doesn't need to be declared in `AppConfig`:

```yaml
development:
  <<: *defaults
  feature_flag_x: true
  external_api_url: "https://api.example.com"
```

Access it anywhere:

```python
ConfigManager.config.get("feature_flag_x")           # None if missing
ConfigManager.config.get("external_api_url", "")      # with default
ConfigManager.config.feature_flag_x                   # direct attribute
```

---

## Error Handling

### HTTP Status Codes

| Status | When |
|---|---|
| `200` | Success |
| `401` | Missing or invalid JWT token |
| `403` | Insufficient permissions (superuser required) |
| `404` | Item / user not found |
| `409` | Item already exists (duplicate) |
| `422` | Request validation failed (Pydantic) |
| `500` | Unexpected server error |

### Response Format

All errors return a consistent JSON body:

```json
{ "code": "VALIDATION_ERROR", "description": "Request validation failed", "detail": [...] }
{ "code": "ERR_UNKNOWN",       "description": "An unexpected error occurred.", "detail": null }
```

---

## Testing

The test suite uses in-memory async mock stores — **no real database required**.

```bash
# Run all tests
pytest

# Verbose
pytest -v

# Single file
pytest tests/test_auth.py -v
```

### Test Coverage

| File | What it tests |
|---|---|
| `tests/test_auth.py` | Login (success / wrong password / missing user), check-login |
| `tests/test_items.py` | Items CRUD — create, get, list, update, delete; auth guards; 404s |
| `tests/test_tasks.py` | Tasks CRUD; assignee filter |
| `tests/test_users.py` | Registration (duplicate / missing fields), delete (superuser guard) |

### How Tests Work

`tests/conftest.py` patches the CBV router service instances with `MockDocument` — in-memory Python lists that implement the full async `BaseDocument` interface. No real DB connection is made.

```python
# After router import, replace service instances on the CBV class
_mock_item_svc = ItemService(ItemStore, "Mock", logger)
ItemRouter._SERVICES = {k: _mock_item_svc for k in ["mongo", "mongodb", ...]}
```

---

## Project Structure

```
app/
├── main.py                      # FastAPI app + lifespan + global error handlers
├── configs/
│   ├── config.yaml              # All config — one file, per-environment sections
│   └── __init__.py              # Re-exports ConfigManager from app.utils
├── utils/
│   ├── config_manager.py        # AppConfig + YamlConfigSource + ConfigManager
│   └── status_code.py           # Standard response codes enum
├── db/
│   ├── base_manager.py          # Abstract BaseDatabaseManager
│   ├── base_document.py         # Abstract BaseDocument — async CRUD contract
│   ├── registry.py              # Named manager registry
│   ├── factory.py               # create_db_from_config() factory
│   ├── mongodb_manager.py       # MongoDB async manager (Motor)
│   ├── mongodb_document.py      # MongoDB async document
│   ├── sql_manager.py           # SQLAlchemy async manager base
│   ├── postgresql_manager.py    # PostgreSQL async manager (asyncpg)
│   ├── postgresql_document.py   # PostgreSQL async document
│   ├── mysql_manager.py         # MySQL async manager (aiomysql)
│   ├── mysql_document.py        # MySQL async document
│   ├── mssql_manager.py         # MSSQL sync manager (pyodbc)
│   ├── mssql_document.py        # MSSQL async document (thread-executor)
│   └── _mssql_sync_document.py  # MSSQL sync internals (used by executor)
├── modules/
│   ├── auth/
│   │   ├── permissions.py       # access_control decorator
│   │   ├── services.py          # AuthService (async)
│   │   ├── utils.py             # JWT / bcrypt helpers
│   │   └── v1/routers.py        # Auth endpoints
│   ├── items/
│   │   ├── models.py            # ItemMongo / ItemPg / ItemMySQL / ItemMSSQL
│   │   ├── base_service.py      # ItemService (async)
│   │   ├── v1/                  # Items v1 API
│   │   └── v2/                  # Items v2 API (extra fields)
│   ├── tasks/
│   │   ├── models.py            # TaskMongo / TaskPg / TaskMySQL / TaskMSSQL
│   │   ├── base_service.py      # TaskService (async)
│   │   └── v1/                  # Tasks v1 API
│   └── user/
│       ├── models.py            # UserMongo / UserPg / UserMySQL / UserMSSQL
│       ├── base_service.py      # UserService (async)
│       └── v1/                  # User management API
└── logs/
    └── log_handler.py           # Loguru structured logging

tests/
├── conftest.py                  # Shared fixtures + in-memory async mocks
├── test_auth.py
├── test_items.py
├── test_tasks.py
└── test_users.py

scripts/
└── new_project.sh               # Bootstrap a new project from this template

docker-compose.yml               # Base config (production — code baked into image)
docker-compose.override.yml      # Dev overrides (auto-merged — code mount + hot-reload)
Dockerfile                       # Multi-stage: base → dependencies → development / production
```

---

## Makefile Commands

```bash
# Local server
make run-server-dev        # uvicorn on port 3636 with --reload
make run-server            # uvicorn on port 8000

# Docker — environment
make dev                   # dev mode (auto-merges override: code mount + hot-reload)
make staging               # staging (no override, code baked in)
make prod                  # production (no override, code baked in)

# Docker — generic
make up                    # docker compose up -d
make down                  # docker compose down
make ps                    # show running containers
make logs                  # tail logs
make up-db                 # start databases only (no app)

# Setup
make init-mssql            # create MSSQL database (one-time, after first up)
make setup                 # full first-time setup: up + init-mssql
make reset                 # tear down + delete all volumes (DESTRUCTIVE)

# Project
make new-project           # bootstrap a new project from this template
```

---

## Important Warnings

### MSSQL Requires ODBC Driver at OS Level

`pyodbc` needs the **Microsoft ODBC Driver 18 for SQL Server** installed on the OS. Docker handles this automatically. For local dev outside Docker, install it manually (see [MSSQL ODBC Driver Install](#mssql-odbc-driver-install)).

### MSSQL Database Must Be Created Manually

SQL Server does not auto-create databases via environment variables. After the first `docker compose up`, run `make init-mssql` once. Data persists in the `mssql_data` Docker volume.

### MSSQL Password Policy

The `sa` password must be ≥8 characters and include characters from 3 of 4 categories: uppercase, lowercase, digits, symbols. The default `Password123!` satisfies this.

### MSSQL Has No Mature Async Driver

`MSSQLDocument` wraps sync pyodbc calls in `asyncio.run_in_executor()`. This avoids blocking the event loop but does not give the same throughput as true async I/O.

### MySQL `cryptography` Package

MySQL 8.0 uses `caching_sha2_password` by default. The `cryptography` package in `requirements.txt` is required by `pymysql`. Do not remove it.

### MSSQL Docker Image is x86_64 Only

`mcr.microsoft.com/mssql/server` does not run on Apple Silicon. On macOS ARM, use Azure SQL Edge:

```yaml
# docker-compose.yml
image: mcr.microsoft.com/azure-sql-edge:latest
```

### Secrets Must Not Be Committed

Override `auth_secret_key` and all passwords via environment variables before deploying. Never commit real credentials to version control.

---

## License

MIT
