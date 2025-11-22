from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/ping")
async def ping():
    return {"status": "ok", "version": "0.1.0"}
