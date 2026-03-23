from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi_utils.cbv import cbv

from .schemas import TaskCreate, TaskUpdate
from .services import TaskService
from ..models import TaskMongo, TaskPg, TaskMySQL, TaskMSSQL
from app.logs import LogHandler
from app.modules.auth.permissions import access_control

router = APIRouter(prefix="/tasks", tags=["Tasks Management — Multi-Backend"])


@cbv(router)
class TaskRouter:
    logger = LogHandler.get_logger("general")

    _mongo_svc = TaskService(TaskMongo, "MongoDB", logger)
    _pg_svc = TaskService(TaskPg, "PostgreSQL", logger)
    _mysql_svc = TaskService(TaskMySQL, "MySQL", logger)
    _mssql_svc = TaskService(TaskMSSQL, "MSSQL", logger)

    _SERVICES = {
        "mongo": _mongo_svc,
        "mongodb": _mongo_svc,
        "pg": _pg_svc,
        "postgresql": _pg_svc,
        "mysql": _mysql_svc,
        "mssql": _mssql_svc,
    }

    def _svc(self, backend: str) -> TaskService:
        svc = self._SERVICES.get(backend)
        if not svc:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown backend '{backend}'. Use: {', '.join(self._SERVICES)}",
            )
        return svc

    @router.post("/{backend}", summary="Create task")
    @access_control()
    async def create_task(self, request: Request, backend: str, data: TaskCreate):
        result = await self._svc(backend).create_task(data.model_dump())
        return JSONResponse(status_code=result["http_code"], content=result["content"])

    @router.get("/{backend}", summary="List all tasks")
    @access_control()
    async def get_all_tasks(self, request: Request, backend: str):
        result = await self._svc(backend).get_all_tasks()
        return JSONResponse(status_code=result["http_code"], content=result["content"])

    @router.get("/{backend}/assignee/{assignee}", summary="Tasks by assignee")
    @access_control()
    async def get_tasks_by_assignee(self, request: Request, backend: str, assignee: str):
        result = await self._svc(backend).get_tasks_by_assignee(assignee)
        return JSONResponse(status_code=result["http_code"], content=result["content"])

    @router.get("/{backend}/{task_id}", summary="Get one task")
    @access_control()
    async def get_task(self, request: Request, backend: str, task_id: str):
        result = await self._svc(backend).get_task(task_id)
        return JSONResponse(status_code=result["http_code"], content=result["content"])

    @router.put("/{backend}/{task_id}", summary="Update task")
    @access_control()
    async def update_task(self, request: Request, backend: str, task_id: str, data: TaskUpdate):
        result = await self._svc(backend).update_task(task_id, data.model_dump())
        return JSONResponse(status_code=result["http_code"], content=result["content"])

    @router.delete("/{backend}/{task_id}", summary="Delete task")
    @access_control()
    async def delete_task(self, request: Request, backend: str, task_id: str):
        result = await self._svc(backend).delete_task(task_id)
        return JSONResponse(status_code=result["http_code"], content=result["content"])
