from fastapi import APIRouter

from hangarkit import ctx

from schemas import HealthResponse
from services.starter_info import health_message

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app=ctx.app_slug,
        route="/health",
        message=health_message(),
    )
