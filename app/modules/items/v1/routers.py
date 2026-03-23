from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi_utils.cbv import cbv

from .schemas import ItemCreate, ItemUpdate
from .services import ItemService
from ..models import ItemMongo, ItemPg, ItemMySQL, ItemMSSQL
from app.logs import LogHandler
from app.modules.auth.permissions import access_control

router = APIRouter(prefix="/items", tags=["Items Management — Multi-Backend"])


@cbv(router)
class ItemRouter:
    logger = LogHandler.get_logger("general")

    _mongo_svc = ItemService(ItemMongo, "MongoDB", logger)
    _pg_svc = ItemService(ItemPg, "PostgreSQL", logger)
    _mysql_svc = ItemService(ItemMySQL, "MySQL", logger)
    _mssql_svc = ItemService(ItemMSSQL, "MSSQL", logger)

    _SERVICES = {
        "mongo": _mongo_svc,
        "mongodb": _mongo_svc,
        "pg": _pg_svc,
        "postgresql": _pg_svc,
        "mysql": _mysql_svc,
        "mssql": _mssql_svc,
    }

    def _svc(self, backend: str) -> ItemService:
        svc = self._SERVICES.get(backend)
        if not svc:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown backend '{backend}'. Use: {', '.join(self._SERVICES)}",
            )
        return svc

    @router.post("/{backend}", summary="Create item")
    @access_control()
    async def create_item(self, request: Request, backend: str, data: ItemCreate):
        result = await self._svc(backend).create_item(data.model_dump())
        return JSONResponse(status_code=result["http_code"], content=result["content"])

    @router.get("/{backend}", summary="List all items")
    @access_control()
    async def get_all_items(self, request: Request, backend: str):
        result = await self._svc(backend).get_all_items()
        return JSONResponse(status_code=result["http_code"], content=result["content"])

    @router.get("/{backend}/{item_id}", summary="Get one item")
    @access_control()
    async def get_item(self, request: Request, backend: str, item_id: str):
        result = await self._svc(backend).get_item(item_id)
        return JSONResponse(status_code=result["http_code"], content=result["content"])

    @router.put("/{backend}/{item_id}", summary="Update item")
    @access_control()
    async def update_item(self, request: Request, backend: str, item_id: str, data: ItemUpdate):
        result = await self._svc(backend).update_item(item_id, data.model_dump())
        return JSONResponse(status_code=result["http_code"], content=result["content"])

    @router.delete("/{backend}/{item_id}", summary="Delete item")
    @access_control()
    async def delete_item(self, request: Request, backend: str, item_id: str):
        result = await self._svc(backend).delete_item(item_id)
        return JSONResponse(status_code=result["http_code"], content=result["content"])
