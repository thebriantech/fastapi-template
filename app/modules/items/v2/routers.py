"""
Items v2 router.

Demonstrates the versioning pattern:
  - Schemas come from ``v2.schemas`` (new fields: category, tags, is_active)
  - Service is ``ItemServiceV2`` (overrides create/update for new fields)
  - Models are reused from the module root (same DB tables / collections)
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi_utils.cbv import cbv

from .schemas import ItemCreate, ItemUpdate
from .services import ItemServiceV2
from ..models import ItemMongo, ItemPg, ItemMySQL, ItemMSSQL
from app.logs import LogHandler
from app.modules.auth.permissions import access_control

router = APIRouter(prefix="/items", tags=["Items Management v2 — Multi-Backend"])


@cbv(router)
class ItemRouterV2:
    logger = LogHandler.get_logger("general")

    _mongo_svc = ItemServiceV2(ItemMongo, "MongoDB", logger)
    _pg_svc = ItemServiceV2(ItemPg, "PostgreSQL", logger)
    _mysql_svc = ItemServiceV2(ItemMySQL, "MySQL", logger)
    _mssql_svc = ItemServiceV2(ItemMSSQL, "MSSQL", logger)

    _SERVICES = {
        "mongo": _mongo_svc,
        "mongodb": _mongo_svc,
        "pg": _pg_svc,
        "postgresql": _pg_svc,
        "mysql": _mysql_svc,
        "mssql": _mssql_svc,
    }

    def _svc(self, backend: str) -> ItemServiceV2:
        svc = self._SERVICES.get(backend)
        if not svc:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown backend '{backend}'. Use: {', '.join(self._SERVICES)}",
            )
        return svc

    @router.post("/{backend}", summary="Create item (v2)")
    @access_control()
    def create_item(self, request: Request, backend: str, data: ItemCreate):
        result = self._svc(backend).create_item(data.dict())
        return JSONResponse(status_code=result["http_code"], content=result["content"])

    @router.get("/{backend}", summary="List all items (v2)")
    @access_control()
    def get_all_items(self, request: Request, backend: str):
        result = self._svc(backend).get_all_items()
        return JSONResponse(status_code=result["http_code"], content=result["content"])

    @router.get("/{backend}/{item_id}", summary="Get one item (v2)")
    @access_control()
    def get_item(self, request: Request, backend: str, item_id: str):
        result = self._svc(backend).get_item(item_id)
        return JSONResponse(status_code=result["http_code"], content=result["content"])

    @router.put("/{backend}/{item_id}", summary="Update item (v2)")
    @access_control()
    def update_item(self, request: Request, backend: str, item_id: str, data: ItemUpdate):
        result = self._svc(backend).update_item(item_id, data.dict())
        return JSONResponse(status_code=result["http_code"], content=result["content"])

    @router.delete("/{backend}/{item_id}", summary="Delete item (v2)")
    @access_control()
    def delete_item(self, request: Request, backend: str, item_id: str):
        result = self._svc(backend).delete_item(item_id)
        return JSONResponse(status_code=result["http_code"], content=result["content"])
