from fastapi import APIRouter

from routers import health, order_admin

router = APIRouter()
router.include_router(health.router)
router.include_router(order_admin.router)
