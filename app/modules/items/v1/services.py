"""
Items v1 service.

V1 uses the base ``ItemService`` as-is — no overrides needed.
Re-exported here so the router always imports from its own package.

If v1 later needs custom logic, subclass ``ItemService`` here instead
of editing ``base_service.py`` (which would affect all versions).
"""

from ..base_service import ItemService

__all__ = ["ItemService"]
