from fastapi import APIRouter

from bot.routes import router as seatalk_bot_router

router = APIRouter()
router.include_router(seatalk_bot_router)
