"""
Test configuration and shared fixtures.

Strategy: We bootstrap the app with a minimal config (no real DB),
then use a test-specific FastAPI app that imports patched modules.
The mock document classes replace all DB model classes before any
router or service is imported, so CBV service instances see mock data.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

# ── Minimal env before loading anything ─────────────────────────────────────
os.environ["APP_ENV"] = "development"
os.environ["ENABLED_BACKENDS"] = "mongodb"
os.environ["AUTH_SECRET_KEY"] = "test-secret-key-for-pytest"
os.environ["SUPERUSER_USERNAME"] = "test-admin"
os.environ["DB_TYPE"] = "mongodb"


# ── Bootstrap config ─────────────────────────────────────────────────────────
from app.configs import ConfigManager
ConfigManager.load()

from app.logs.log_handler import setup_logger, LogHandler
LogHandler.set_write_to_file(False)
for _name in ["general", "auth", "user_management"]:
    try:
        setup_logger(
            log_folder="app/logs/logs_data",
            logger_name=_name,
            rotation="200MB",
            retention="7days",
        )
    except Exception:
        pass


# ── In-memory mock document store ────────────────────────────────────────────

class MockDocument:
    """In-memory async CRUD that mirrors BaseDocument."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._store = []

    @classmethod
    def reset(cls):
        cls._store.clear()

    @classmethod
    async def insert_one(cls, document: dict) -> dict:
        cls._store.append(dict(document))
        return {"status": True}

    @classmethod
    async def find_one(cls, query: dict, **kwargs) -> dict:
        for doc in cls._store:
            if all(doc.get(k) == v for k, v in query.items()):
                return {"status": True, "result": dict(doc)}
        return {"status": False, "result": []}

    @classmethod
    async def find(cls, query: dict, **kwargs) -> dict:
        q = query or {}
        results = [dict(d) for d in cls._store
                   if all(d.get(k) == v for k, v in q.items())]
        return {"status": True, "result": results}

    @classmethod
    async def get_all(cls, **kwargs) -> dict:
        return {"status": True, "result": [dict(d) for d in cls._store]}

    @classmethod
    async def update_one(cls, query: dict, update: dict, **kwargs) -> dict:
        for doc in cls._store:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(update)
                return {"status": True, "affected": 1}
        return {"status": True, "affected": 0}

    @classmethod
    async def delete_one(cls, query: dict) -> dict:
        before = len(cls._store)
        cls._store[:] = [d for d in cls._store
                         if not all(d.get(k) == v for k, v in query.items())]
        return {"status": True, "deleted": before - len(cls._store)}

    @classmethod
    async def count(cls, query=None) -> dict:
        q = query or {}
        n = sum(1 for d in cls._store if all(d.get(k) == v for k, v in q.items()))
        return {"status": True, "count": n}

    @classmethod
    async def insert_many(cls, documents, **kwargs) -> dict:
        for doc in documents:
            cls._store.append(dict(doc))
        return {"status": True, "inserted": len(documents)}

    @classmethod
    async def update_many(cls, query, update, **kwargs) -> dict:
        count = 0
        for doc in cls._store:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(update)
                count += 1
        return {"status": True, "affected": count}

    @classmethod
    async def upsert_one(cls, query, document) -> dict:
        r = await cls.update_one(query, document)
        if r.get("affected", 0) == 0:
            return await cls.insert_one({**query, **document})
        return r

    @classmethod
    async def delete_many(cls, query) -> dict:
        return await cls.delete_one(query)

    @classmethod
    async def execute_raw(cls, operation, params=None, **kwargs) -> dict:
        return {"status": True, "result": []}

    @classmethod
    def ensure_indexes(cls) -> None:
        pass

    @classmethod
    def create_index(cls, *args, **kwargs) -> None:
        pass


class ItemStore(MockDocument):
    _store = []

class TaskStore(MockDocument):
    _store = []

class UserStore(MockDocument):
    _store = []


# ── Import all router modules (triggers CBV class creation with real models) ──
# We must import these first, then patch the service instances on CBV classes.
from app.modules.auth.v1.routers import router as _auth_router
from app.modules.user.v1.routers import router as _user_router, UserRouter as _UserRouter
from app.modules.items.v1.routers import router as _items_router, ItemRouter as _ItemRouter
from app.modules.items.v2.routers import router as _items_v2_router
from app.modules.tasks.v1.routers import router as _tasks_router, TaskRouter as _TaskRouter

# ── Patch get_user_model in auth modules ─────────────────────────────────────
import app.modules.user.models as _user_models
import app.modules.auth.permissions as _permissions_mod
import app.modules.auth.services as _auth_services_mod

_user_models.get_user_model = lambda: UserStore
_permissions_mod.get_user_model = lambda: UserStore
_auth_services_mod.get_user_model = lambda: UserStore

# ── Replace CBV service instances with mock-backed services ──────────────────
# CBV class-body runs at import time with the real model classes, so we must
# replace the service instances *after* import rather than patching model attrs.
from app.modules.items.base_service import ItemService
from app.modules.tasks.base_service import TaskService
from app.modules.user.base_service import UserService

_svc_logger = LogHandler.get_logger("general")

_mock_item_svc = ItemService(ItemStore, "Mock", _svc_logger)
_ITEM_SERVICES = {k: _mock_item_svc for k in ["mongo", "mongodb", "pg", "postgresql", "mysql", "mssql"]}
_ItemRouter._mongo_svc = _mock_item_svc
_ItemRouter._pg_svc = _mock_item_svc
_ItemRouter._mysql_svc = _mock_item_svc
_ItemRouter._mssql_svc = _mock_item_svc
_ItemRouter._SERVICES = _ITEM_SERVICES

_mock_task_svc = TaskService(TaskStore, "Mock", _svc_logger)
_TASK_SERVICES = {k: _mock_task_svc for k in ["mongo", "mongodb", "pg", "postgresql", "mysql", "mssql"]}
_TaskRouter._mongo_svc = _mock_task_svc
_TaskRouter._pg_svc = _mock_task_svc
_TaskRouter._mysql_svc = _mock_task_svc
_TaskRouter._mssql_svc = _mock_task_svc
_TaskRouter._SERVICES = _TASK_SERVICES

_mock_user_svc = UserService(UserStore, "Mock", _svc_logger)
_USER_SERVICES = {k: _mock_user_svc for k in ["mongo", "mongodb", "pg", "postgresql", "mysql", "mssql"]}
_UserRouter._mongo_svc = _mock_user_svc
_UserRouter._pg_svc = _mock_user_svc
_UserRouter._mysql_svc = _mock_user_svc
_UserRouter._mssql_svc = _mock_user_svc
_UserRouter._SERVICES = _USER_SERVICES

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def make_test_app() -> FastAPI:
    app = FastAPI(title="Test App")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def _val_err(request, exc):
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION_ERROR",
                "description": "Request validation failed",
                "detail": exc.errors(),
            },
        )

    prefix = "/api/v1"
    app.include_router(_auth_router, prefix=prefix)
    app.include_router(_user_router, prefix=prefix)
    app.include_router(_items_router, prefix=prefix)
    app.include_router(_items_v2_router, prefix=prefix.replace("/v1", "/v2"))
    app.include_router(_tasks_router, prefix=prefix)
    return app


test_app = make_test_app()


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client():
    with TestClient(test_app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_stores():
    """Clear all in-memory stores before each test."""
    ItemStore.reset()
    TaskStore.reset()
    UserStore.reset()
    yield


@pytest.fixture
def plain_password():
    return "TestPass123!"


@pytest.fixture
def registered_user(plain_password):
    from app.modules.auth.utils import get_password_hash
    user = {
        "username": "testuser",
        "user_group": "users",
        "email": "test@example.com",
        "hashed_password": get_password_hash(plain_password),
    }
    UserStore._store.append(dict(user))
    return user


@pytest.fixture
def admin_user(plain_password):
    from app.modules.auth.utils import get_password_hash
    user = {
        "username": "test-admin",
        "user_group": "admin",
        "email": "admin@example.com",
        "hashed_password": get_password_hash(plain_password),
    }
    UserStore._store.append(dict(user))
    return user


@pytest.fixture
def user_token(registered_user):
    from app.modules.auth.utils import create_access_token
    return create_access_token({"sub": registered_user["username"]})


@pytest.fixture
def admin_token(admin_user):
    from app.modules.auth.utils import create_access_token
    return create_access_token({"sub": admin_user["username"]})


@pytest.fixture
def auth_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
