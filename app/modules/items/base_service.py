"""
Item services — Template Method pattern.

The base ``ItemService`` owns the full CRUD *flow* (DB calls, error
handling, logging, status codes).  It delegates **data-transformation**
to small hook methods that subclasses override per API version.

Adding a new version means:
  1. Subclass ``ItemService``
  2. Override only the hooks whose behaviour changes
  3. Everything else (error handling, logging …) is inherited for free

Hook methods
~~~~~~~~~~~~
+-------------------------------+--------------------------------------------+
| Hook                          | Default behaviour (v1)                     |
+===============================+============================================+
| ``_build_create_payload()``   | Returns dict with core fields              |
| ``_build_update_payload()``   | Strips ``None`` values                     |
| ``_format_item()``            | Strips ``_id``, returns dict as-is         |
| ``_on_after_create()``        | No-op — extend for side-effects            |
| ``_on_after_update()``        | No-op — extend for side-effects            |
| ``_on_after_delete()``        | No-op — extend for side-effects            |
+-------------------------------+--------------------------------------------+
"""

from __future__ import annotations

import uuid
from typing import Type

from app.db.base_document import BaseDocument
from app.utils.status_code import StatusCode


class ItemService:
    """
    Generic CRUD service that works with **any** ``BaseDocument`` subclass.

    Instantiate once per backend:

        pg_service = ItemService(ItemPg, "PostgreSQL", logger)
    """

    def __init__(self, model: Type[BaseDocument], backend_label: str, logger):
        self.model = model
        self.label = backend_label
        self.logger = logger

    # ── Hook methods (override these in version subclasses) ──────────────

    def _build_create_payload(self, data: dict) -> dict:
        """Build the document/row to insert.  Override to add fields."""
        return {
            "item_id": str(uuid.uuid4()),
            "name": data["name"],
            "description": data["description"],
            "price": data["price"],
            "quantity": data["quantity"],
        }

    def _build_update_payload(self, data: dict) -> dict:
        """Build the update dict.  Override to transform or validate."""
        return {k: v for k, v in data.items() if v is not None}

    def _format_item(self, item: dict) -> dict:
        """Format a single item before returning.  Override to reshape."""
        if isinstance(item, dict):
            item.pop("_id", None)
        return item

    def _on_after_create(self, item_id: str, data: dict):
        """Post-create hook — e.g. send event, update cache."""

    def _on_after_update(self, item_id: str, data: dict):
        """Post-update hook."""

    def _on_after_delete(self, item_id: str):
        """Post-delete hook."""

    # ── CRUD operations (own the flow — rarely need overriding) ──────────

    def create_item(self, data: dict = None):
        try:
            payload = self._build_create_payload(data)
            item_id = payload["item_id"]
            self.model.insert_one(payload)
            self._on_after_create(item_id, data)
            self.logger.success(f"[{self.label}] Item '{data['name']}' created successfully")
            status = StatusCode.SUCCESS.value
            status["content"]["detail"] = {
                "item_id": item_id,
                "backend": self.label,
                "message": f"Item '{data['name']}' created successfully",
            }
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.value
            status["content"]["detail"] = str(e)
            return status

    def get_item(self, item_id: str = None):
        try:
            item = self.model.find_one({"item_id": item_id})
            if not item["status"] or len(item["result"]) == 0:
                self.logger.error(f"[{self.label}] Item {item_id} not found")
                status = StatusCode.ITEM_NOT_FOUND_ERROR.value
                status["content"]["detail"] = f"Item {item_id} not found"
                return status
            result = item["result"]
            if isinstance(result, dict):
                result = self._format_item(result)
            elif isinstance(result, list):
                result = [self._format_item(r) for r in result]
            self.logger.success(f"[{self.label}] Item {item_id} found")
            status = StatusCode.SUCCESS.value
            status["content"]["detail"] = result
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.value
            status["content"]["detail"] = str(e)
            return status

    def get_all_items(self):
        try:
            items = self.model.find({})
            if not items["status"]:
                self.logger.error(f"[{self.label}] Failed to retrieve items")
                status = StatusCode.FIND_ITEM_ERROR.value
                status["content"]["detail"] = "Failed to retrieve items"
                return status
            result = items["result"]
            if isinstance(result, list):
                result = [self._format_item(r) for r in result]
            self.logger.success(f"[{self.label}] Found {len(result)} items")
            status = StatusCode.SUCCESS.value
            status["content"]["detail"] = result
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.value
            status["content"]["detail"] = str(e)
            return status

    def update_item(self, item_id: str = None, data: dict = None):
        try:
            item = self.model.find_one({"item_id": item_id})
            if not item["status"] or len(item["result"]) == 0:
                self.logger.error(f"[{self.label}] Item {item_id} not found")
                status = StatusCode.ITEM_NOT_FOUND_ERROR.value
                status["content"]["detail"] = f"Item {item_id} not found"
                return status
            update_data = self._build_update_payload(data)
            if not update_data:
                status = StatusCode.SUCCESS.value
                status["content"]["detail"] = "No fields to update"
                return status
            self.model.update_one({"item_id": item_id}, update_data)
            self._on_after_update(item_id, data)
            self.logger.success(f"[{self.label}] Item {item_id} updated successfully")
            status = StatusCode.SUCCESS.value
            status["content"]["detail"] = f"Item {item_id} updated successfully"
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.value
            status["content"]["detail"] = str(e)
            return status

    def delete_item(self, item_id: str = None):
        try:
            item = self.model.find_one({"item_id": item_id})
            if not item["status"] or len(item["result"]) == 0:
                self.logger.error(f"[{self.label}] Item {item_id} not found")
                status = StatusCode.ITEM_NOT_FOUND_ERROR.value
                status["content"]["detail"] = f"Item {item_id} not found"
                return status
            result = self.model.delete_one({"item_id": item_id})
            if not result["status"]:
                self.logger.error(f"[{self.label}] {result['error']}")
                status = StatusCode.UNKNOWN_ERROR.value
                status["content"]["detail"] = result["error"]
                return status
            self._on_after_delete(item_id)
            self.logger.success(f"[{self.label}] Item {item_id} deleted successfully")
            status = StatusCode.SUCCESS.value
            status["content"]["detail"] = f"Item {item_id} deleted successfully"
            return status
        except Exception as e:
            self.logger.error(f"[{self.label}] {e}")
            status = StatusCode.UNKNOWN_ERROR.value
            status["content"]["detail"] = str(e)
            return status
