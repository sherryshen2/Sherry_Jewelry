from fastapi import APIRouter
from hangarkit import ctx, table

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "app": ctx.app_slug,
        "user": ctx.user_email,
        "request_id": ctx.request_id,
    }


@router.get("/summary")
def summary():
    releases = table("releases").list(sort="-version", perPage=100)
    verifications = table("verifications").list(sort="-updated_at", perPage=100)
    latest = verifications[0] if verifications else None
    verified_count = len([item for item in verifications if item.get("status") == "Verified"])
    if latest:
        release = latest.get("release_version") or "latest release"
        status = latest.get("status") or "Not verified"
        return {
            "release_count": len(releases),
            "verification_count": len(verifications),
            "verified_count": verified_count,
            "message": f"{release} is {status}. {verified_count}/{len(verifications)} release(s) verified.",
        }
    return {
        "release_count": len(releases),
        "verification_count": 0,
        "verified_count": 0,
        "message": "No release verification has been saved yet.",
    }
