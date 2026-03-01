# Module registry
# Import all module routers here for easy access

from .auth import auth_router
from .user import user_management_router
from .items import items_router, items_v2_router
from .tasks import tasks_router
