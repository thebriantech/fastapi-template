# FastAPI Template

A production-ready, modular FastAPI project template with a **backend-agnostic database layer** supporting MongoDB, PostgreSQL, MySQL, and MSSQL out of the box.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start (Docker)](#quick-start-docker)
- [Local Development (without Docker)](#local-development-without-docker)
- [Database Configuration](#database-configuration)
- [Switching Database Backends](#switching-database-backends)
- [Multi-Database Setup](#multi-database-setup)
- [Project Structure](#project-structure)
- [Important Warnings](#important-warnings)

---

## Features

- **FastAPI** with modular router structure (auth, users, items, tasks)
- **Backend-agnostic database layer** — swap between MongoDB / PostgreSQL / MySQL / MSSQL via a single env var
- **Abstract base classes** (`BaseDatabaseManager`, `BaseDocument`) for adding custom backends
- **Manager registry** — run multiple databases side-by-side
- **Factory pattern** — `create_db_from_config(cfg)` auto-selects the right backend
- **Connection pooling** and health checks for all backends
- **JWT authentication** with role-based permissions
- **Structured logging** via Loguru
- **Redis** for caching
- **Docker Compose** with health checks for all services
- **Pydantic-settings** for typed, `.env`-driven configuration

---

## Architecture

```
┌─────────────────────────────────────────────┐
│               BaseDocument (ABC)            │   ← abstract CRUD contract
├──────────────────┬──────────────────────────┤
│  MongoDocument   │      SQLDocument         │   ← concrete implementations
│                  ├──────┬───────┬───────────┤
│                  │PgDoc │MyDoc  │MSSQLDoc   │   ← dialect-specific
└────────┬─────────┴──┬───┴───┬───┴─────┬─────┘
         │            │       │         │
   MongoDBManager  PGManager MySQLMgr MSSQLMgr    ← connection managers
         │            │       │         │
         └──────── Registry ──┴─────────┘          ← named manager lookup
                      │
                   Factory                         ← create_db_from_config()
```

---

## Quick Start (Docker)

This is the **recommended** way to run the project. All databases are included.

```bash
# 1. Clone the repository
git clone <repo-url> && cd fastapi-template

# 2. Copy and edit environment variables
cp .env.example .env   # or use the provided .env

# 3. Start all services
docker compose up -d

# 4. Wait for health checks (especially MSSQL ~30s)
docker compose ps

# 5. Create the MSSQL database (one-time setup — see warning below)
docker exec fastapi-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'Password123!' -C \
  -Q "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'project_name') CREATE DATABASE project_name;"

# 6. The API is available at http://localhost:18000
#    Health check: http://localhost:18000/health
```

> **⚠️ MSSQL Database Warning:** Unlike PostgreSQL and MySQL, SQL Server does **not** auto-create databases from environment variables. You **must** run the `sqlcmd` command above after the first `docker compose up` to create the application database. This only needs to be done once — the data persists in the `mssql_data` volume.

---

## Local Development (without Docker)

### Prerequisites

| Dependency | Required for | Install |
|---|---|---|
| **Python 3.10+** | All | `conda create -n fastapi-template python=3.10` |
| **MongoDB 7+** | MongoDB backend | Running instance or Docker |
| **Redis 7+** | Caching | Running instance or Docker |
| **unixODBC** | MSSQL backend | `sudo apt-get install unixodbc-dev` (Debian/Ubuntu) |
| **ODBC Driver 18** | MSSQL backend | See [install instructions](#mssql-odbc-driver-install) below |

### Setup

```bash
# 1. Create and activate the conda environment
conda create -n fastapi-template python=3.10 -y
conda activate fastapi-template

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start the databases you need (e.g. just MongoDB + Redis)
docker compose up -d mongodb redis

# 4. Edit .env — set DB_TYPE and point hosts to localhost
#    DB_TYPE=mongodb
#    MONGODB_HOST=localhost

# 5. Run the dev server
make run-server-dev
# or: uvicorn app.main:server --host 0.0.0.0 --port 3636 --reload
```

### MSSQL ODBC Driver Install

> **⚠️ Warning:** The MSSQL backend requires the **Microsoft ODBC Driver 18 for SQL Server** installed at the OS level. Without it, `pyodbc` will fail with `libodbc.so.2: cannot open shared object file`.

**Ubuntu / Debian:**

```bash
# 1. Install unixODBC
sudo apt-get install -y unixodbc-dev

# 2. Add Microsoft's package repository
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
  | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

# For Ubuntu 24.04 (Noble):
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] \
  https://packages.microsoft.com/ubuntu/24.04/prod noble main" \
  | sudo tee /etc/apt/sources.list.d/mssql-release.list

# For Debian 12 (Bookworm) — used inside Docker:
# echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] \
#   https://packages.microsoft.com/debian/12/prod bookworm main" \
#   | sudo tee /etc/apt/sources.list.d/mssql-release.list

# 3. Install the driver
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18

# 4. Verify
odbcinst -q -d
# Should show: [ODBC Driver 18 for SQL Server]
```

**macOS:**

```bash
brew install unixodbc
brew tap microsoft/mssql-release https://github.com/microsoft/homebrew-mssql-release
brew install msodbcsql18
```

> **⚠️ Note:** The Dockerfile already includes the ODBC driver install for the Docker-based workflow. The steps above are only needed for **local development** outside Docker.

---

## Database Configuration

All configuration is done via environment variables (or `.env` file). The `DB_TYPE` variable selects which backend the app connects to at startup.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DB_TYPE` | `mongodb` | Primary backend: `mongodb`, `postgresql`, `mysql`, `mssql` |
| **MongoDB** | | |
| `MONGODB_HOST` | `localhost` | MongoDB hostname |
| `MONGODB_PORT` | `27017` | MongoDB port |
| `MONGODB_USERNAME` | `admin` | MongoDB username |
| `MONGODB_PASSWORD` | `password` | MongoDB password |
| `MONGODB_AUTH` | `admin` | Auth database |
| `MONGODB_DATABASE` | `project_name` | Default database |
| `MONGODB_MAX_POOL_SIZE` | `50` | Connection pool max |
| `MONGODB_MIN_POOL_SIZE` | `10` | Connection pool min |
| **PostgreSQL** | | |
| `PG_HOST` | `localhost` | PostgreSQL hostname |
| `PG_PORT` | `5432` | PostgreSQL port |
| `PG_USERNAME` | `postgres` | PostgreSQL username |
| `PG_PASSWORD` | `password` | PostgreSQL password |
| `PG_DATABASE` | `project_name` | Default database |
| `PG_POOL_SIZE` | `10` | SQLAlchemy pool size |
| `PG_MAX_OVERFLOW` | `20` | Max overflow connections |
| **MySQL** | | |
| `MYSQL_HOST` | `localhost` | MySQL hostname |
| `MYSQL_PORT` | `3306` | MySQL port |
| `MYSQL_USERNAME` | `root` | MySQL username |
| `MYSQL_PASSWORD` | `password` | MySQL password |
| `MYSQL_DATABASE` | `project_name` | Default database |
| `MYSQL_POOL_SIZE` | `10` | SQLAlchemy pool size |
| `MYSQL_MAX_OVERFLOW` | `20` | Max overflow connections |
| **MSSQL** | | |
| `MSSQL_HOST` | `localhost` | SQL Server hostname |
| `MSSQL_PORT` | `1433` | SQL Server port |
| `MSSQL_USERNAME` | `sa` | SQL Server username |
| `MSSQL_PASSWORD` | `Password123!` | SQL Server password |
| `MSSQL_DATABASE` | `project_name` | Default database |
| `MSSQL_POOL_SIZE` | `10` | SQLAlchemy pool size |
| `MSSQL_MAX_OVERFLOW` | `20` | Max overflow connections |
| `MSSQL_DRIVER` | `ODBC Driver 18 for SQL Server` | ODBC driver name |
| **Redis** | | |
| `REDIS_HOST` | `localhost` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_PASSWORD` | *(empty)* | Redis password |
| **Auth** | | |
| `AUTH_SECRET_KEY` | `change-me` | JWT signing key |
| `AUTH_ALGORITHM` | `HS256` | JWT algorithm |
| `AUTH_EXPIRE_SECONDS` | `3600` | Token TTL in seconds |

---

## Switching Database Backends

Change the primary backend by setting `DB_TYPE` in `.env`:

```bash
# Use PostgreSQL as the primary database
DB_TYPE=postgresql

# Or MySQL
DB_TYPE=mysql

# Or MSSQL
DB_TYPE=mssql

# Default — MongoDB
DB_TYPE=mongodb
```

The factory accepts these aliases:

| `DB_TYPE` value | Backend |
|---|---|
| `mongodb` | MongoDB (pymongo) |
| `postgresql`, `postgres`, `pg` | PostgreSQL (psycopg2 + SQLAlchemy) |
| `mysql`, `mariadb` | MySQL/MariaDB (pymysql + SQLAlchemy) |
| `mssql`, `sqlserver`, `mssqlserver` | SQL Server (pyodbc + SQLAlchemy) |

---

## Multi-Database Setup

You can connect to **multiple databases simultaneously** using the registry:

```python
# In main.py lifespan or anywhere during startup:
from app.db import register_manager
from app.db.factory import create_db_from_config
from app.db.postgresql_manager import PostgreSQLManager

# Primary (from DB_TYPE env var)
primary = create_db_from_config(cfg)
register_manager("default", primary)

# Secondary PostgreSQL alongside MongoDB
pg = PostgreSQLManager()
pg.connect(host="localhost", port=5432, username="postgres",
           password="secret", database="analytics")
register_manager("analytics", pg)
```

Then in your models, point to the right manager:

```python
from app.db.pg_document import PgDocument

class AnalyticsEvent(PgDocument):
    _table_name = "events"
    _manager_alias = "analytics"   # ← uses the "analytics" manager
```

---

## Project Structure

```
app/
├── main.py                  # FastAPI app + lifespan (startup/shutdown)
├── configs/
│   └── config_handler.py    # Pydantic-settings AppConfig + ConfigManager
├── db/
│   ├── base_manager.py      # Abstract BaseDatabaseManager (ABC)
│   ├── base_document.py     # Abstract BaseDocument with CRUD contract
│   ├── registry.py          # Named manager registry
│   ├── factory.py           # create_db_from_config() factory
│   ├── mongodb_manager.py   # MongoDB connection manager
│   ├── mongo_document.py    # MongoDB document (pymongo CRUD)
│   ├── sql_manager.py       # Shared SQLAlchemy manager base
│   ├── sql_document.py      # Shared SQL document base (dict→SQL)
│   ├── postgresql_manager.py # PostgreSQL manager
│   ├── pg_document.py       # PostgreSQL document
│   ├── mysql_manager.py     # MySQL manager
│   ├── mysql_document.py    # MySQL document
│   ├── mssql_manager.py     # MSSQL manager
│   ├── mssql_document.py    # MSSQL document
│   └── mongodb_base.py      # Legacy (kept for backward compat)
├── modules/
│   ├── auth/v1/             # JWT auth + permissions
│   ├── items/v1/            # Items CRUD module
│   ├── tasks/v1/            # Tasks CRUD module
│   └── user/v1/             # User management module
├── logs/
│   └── log_handler.py       # Loguru-based structured logging
└── utils/
    ├── redis.py             # Redis helper
    ├── startup.py           # Startup utilities
    └── status_code.py       # Standard response codes
```

---

## Important Warnings

### ⚠️ MSSQL Requires ODBC Driver at OS Level

The `pyodbc` Python package is just a binding — it needs the actual **Microsoft ODBC Driver 18 for SQL Server** installed on the operating system. This is handled automatically inside Docker (see `Dockerfile`), but for local development you must install it manually. See [MSSQL ODBC Driver Install](#mssql-odbc-driver-install).

### ⚠️ MSSQL Database Must Be Created Manually

SQL Server does not support auto-creating databases via environment variables (unlike PostgreSQL's `POSTGRES_DB` or MySQL's `MYSQL_DATABASE`). After the first `docker compose up`, run:

```bash
docker exec fastapi-mssql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'Password123!' -C \
  -Q "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'project_name') CREATE DATABASE project_name;"
```

### ⚠️ MSSQL Password Policy

SQL Server enforces a strong password policy. The `sa` password must be at least **8 characters** and contain characters from **3 of 4** categories: uppercase, lowercase, digits, symbols. The default `Password123!` satisfies this. If you change it, make sure the new password complies.

### ⚠️ MySQL `cryptography` Package

MySQL 8.0 uses `caching_sha2_password` as the default authentication plugin. The `pymysql` driver requires the Python `cryptography` package to handle this. It is included in `requirements.txt` — do not remove it or MySQL connections will fail with:

```
RuntimeError: 'cryptography' package is required for sha256_password or caching_sha2_password auth methods
```

### ⚠️ MSSQL Docker Image is x86_64 Only

The `mcr.microsoft.com/mssql/server` image only supports **amd64 (x86_64)**. It does **not** run on **Apple Silicon (M1/M2/M3)** natively. On macOS ARM, use Azure SQL Edge instead:

```yaml
# In docker-compose.yml, replace the mssql image:
image: mcr.microsoft.com/azure-sql-edge:latest
```

### ⚠️ Default Credentials Are for Development Only

All default passwords in `.env` and `docker-compose.yml` are **insecure**. Before deploying to production:

1. Change all passwords to strong, unique values
2. Use Docker secrets or a vault for sensitive values
3. Never commit `.env` to version control

---

## Makefile Commands

```bash
make run-server-dev    # Start dev server on port 3636
```

---

## License

MIT