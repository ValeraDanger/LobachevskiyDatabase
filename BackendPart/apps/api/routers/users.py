from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from database.managers.user_manager import UserManager
from apps.api.deps import get_user_manager

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
async def get_user(
    user_id: UUID,
    user_manager: UserManager = Depends(get_user_manager),
):
    user = await user_manager.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "firstName": user.first_name,
        "lastName": user.last_name,
        "middleName": user.middle_name,
        "phone": user.phone,
        "departmentId": user.department_id,
        "roleId": user.role_id,
        "accessLevels": user.access_levels,
    }
