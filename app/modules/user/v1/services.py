"""
User v1 service.

V1 uses the base ``UserService`` as-is — no overrides needed.
Re-exported here so the router always imports from its own package.
"""

from ..base_service import UserService

__all__ = ["UserService"]
