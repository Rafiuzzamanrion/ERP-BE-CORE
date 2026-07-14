from fastapi import APIRouter

from app.core.config import settings
from app.infrastructure.mongo.client import get_db
from app.modules.auth.router import router as auth_router
from app.modules.categories.router import router as categories_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.products.router import router as products_router
from app.modules.roles.router import permissions_router, roles_router
from app.modules.sales.router import router as sales_router
from app.modules.users.router import router as users_router

router = APIRouter()

router.include_router(auth_router, tags=["Auth"])
router.include_router(users_router, tags=["Users"])
router.include_router(roles_router, tags=["Roles"])
router.include_router(permissions_router, tags=["Permissions"])
router.include_router(categories_router, tags=["Categories"])
router.include_router(products_router, tags=["Products"])
router.include_router(sales_router, tags=["Sales"])
router.include_router(dashboard_router, tags=["Dashboard"])


@router.get("/health")
async def health():
    db_ok = True
    try:
        db = get_db()
        await db.command("ping")
    except Exception:
        db_ok = False

    db_instance = get_db()
    admin_seeded = False
    try:
        count = await db_instance["users"].count_documents({"role": {"$ne": None}})
        admin_seeded = count > 0
    except Exception:
        pass

    return {
        "success": True,
        "message": "Server is running",
        "data": {
            "uptime": "running",
            "database": "connected" if db_ok else "disconnected",
            "adminSeeded": admin_seeded,
            "environment": settings.NODE_ENV,
        },
    }
