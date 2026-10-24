from fastapi import APIRouter
from hangarkit import ctx

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "app": ctx.app_slug,
        "user": ctx.user_email,
        "message": "Onboarding checklist backend is ready.",
    }
