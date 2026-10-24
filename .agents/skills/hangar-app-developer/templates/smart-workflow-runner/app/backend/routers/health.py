import os

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {
        "ok": True,
        "configured": bool(os.getenv("SMART_ENDPOINT_DEPLOYMENT_HASH_ID") and os.getenv("SMART_ENDPOINT_DEPLOYMENT_KEY")),
    }
