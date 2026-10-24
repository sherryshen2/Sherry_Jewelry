from fastapi import APIRouter

from routers.health import router as health_router
from routers.metrics import router as metrics_router
from routers.tasks import router as tasks_router

router = APIRouter()
router.include_router(health_router)
router.include_router(tasks_router)
router.include_router(metrics_router)
