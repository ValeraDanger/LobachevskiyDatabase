from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .documents import router as documents_router
from .workspace import router as workspace_router
from .health import router as health_router
from .profile import router as profile_router
from .departments import router as departments_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(documents_router)
router.include_router(profile_router)
router.include_router(workspace_router)
router.include_router(users_router)
router.include_router(departments_router)
