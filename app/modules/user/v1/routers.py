from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi_utils.cbv import cbv

from .schemas import UserRegister
from .services import UserService
from ..models import UserMongo, UserPg, UserMySQL, UserMSSQL
from app.logs import LogHandler
from app.modules.auth.permissions import access_control

router = APIRouter(prefix="/users", tags=["Users Management — Multi-Backend"])


@cbv(router)
class UserRouter:
    logger = LogHandler.get_logger("user_management")

    _mongo_svc = UserService(UserMongo, "MongoDB", logger)
    _pg_svc = UserService(UserPg, "PostgreSQL", logger)
    _mysql_svc = UserService(UserMySQL, "MySQL", logger)
    _mssql_svc = UserService(UserMSSQL, "MSSQL", logger)

    _SERVICES = {
        "mongo": _mongo_svc,
        "mongodb": _mongo_svc,
        "pg": _pg_svc,
        "postgresql": _pg_svc,
        "mysql": _mysql_svc,
        "mssql": _mssql_svc,
    }

    def _svc(self, backend: str) -> UserService:
        svc = self._SERVICES.get(backend)
        if not svc:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown backend '{backend}'. Use: {', '.join(self._SERVICES)}",
            )
        return svc

    @router.post("/{backend}/register", summary="Register user")
    @access_control(open=True)
    def user_register(self, request: Request, backend: str, data: UserRegister):
        result = self._svc(backend).user_register(data.dict())
        return JSONResponse(status_code=result["http_code"], content=result["content"])

    @router.delete("/{backend}/delete/{username}", summary="Delete user")
    @access_control(superuser=True)
    def user_delete(self, request: Request, backend: str, username: str):
        result = self._svc(backend).user_delete(username)
        return JSONResponse(status_code=result["http_code"], content=result["content"])