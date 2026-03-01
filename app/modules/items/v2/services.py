"""
Items v2 service — hook overrides only.

Demonstrates how a new API version customises behaviour by overriding
**only the hook methods** from the base ``ItemService``.  The full
CRUD flow (DB calls, error handling, logging, status codes) is
inherited — zero duplication.

To add v3 later, create ``v3/services.py``, subclass ``ItemService``
(or ``ItemServiceV2``), and override only the hooks that change.
"""

from __future__ import annotations

from ..base_service import ItemService


class ItemServiceV2(ItemService):
    """
    V2 customisations:
      - ``_build_create_payload`` — adds ``category``, ``tags``, ``is_active``
      - ``_on_after_create`` — logs extra v2 metadata

    Everything else (get, update, delete, error handling) is inherited as-is.
    """

    def _build_create_payload(self, data: dict) -> dict:
        payload = super()._build_create_payload(data)
        payload.update({
            "category": data.get("category", "general"),
            "tags": data.get("tags", []),
            "is_active": data.get("is_active", True),
        })
        return payload

    def _on_after_create(self, item_id: str, data: dict):
        self.logger.info(
            f"[{self.label}] v2 metadata — category={data.get('category', 'general')}, "
            f"tags={data.get('tags', [])}"
        )
