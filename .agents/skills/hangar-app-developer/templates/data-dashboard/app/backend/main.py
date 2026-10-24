from fastapi import APIRouter

from routers.dashboard import router as dashboard_router

router = APIRouter()
router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])


@router.get("/health")
def health():
    return {
        "ok": True,
        "sources": ["local", "csv", "google_sheets", "datasuite"],
    }
