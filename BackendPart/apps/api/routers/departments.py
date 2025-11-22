from fastapi import APIRouter, Depends
from apps.api.deps import get_rbac_manager
from apps.api.schemas.departments import DepartmentResponse
from database.managers.rbac_manager import RbacManager


router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentResponse])
async def list_departments(manager: RbacManager = Depends(get_rbac_manager)):
    return await manager.list_departments()
