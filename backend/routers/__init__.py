from routers.auth import router as auth_router
from routers.admin import router as admin_router
from routers.staff import router as staff_router
from routers.delegate import router as delegate_router

__all__ = ["auth_router", "admin_router", "staff_router", "delegate_router"]
