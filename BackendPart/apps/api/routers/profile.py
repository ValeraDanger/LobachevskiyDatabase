from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.deps import (
    get_current_user,
    get_user_manager,
    get_audit_manager,
)
from database.managers.user_manager import UserManager
from database.managers.audit_manager import AuditManager
from apps.api.schemas.profile import (
    ProfileResponse,
    ProfileUpdateRequest,
    ProfileActivityResponse,
    ProfileRecentActionsResponse,
    ProfileRecentAction,
)
from apps.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


def get_profile_service(
    user_manager: UserManager = Depends(get_user_manager),
    audit_manager: AuditManager = Depends(get_audit_manager),
) -> ProfileService:
    return ProfileService(user_manager, audit_manager)


@router.get("/me", response_model=ProfileResponse)
async def get_profile_me(
    user=Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    row = await service.get_profile(user.id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return ProfileResponse(
        id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        middle_name=row["middle_name"],
        email=row["email"],
        phone=row["phone"],
        department_id=row["department_id"],
        department_name=row.get("department_name"),
        role_id=row["role_id"],
        role_name=row.get("role_name"),
        access_levels=row.get("access_levels") or [],
        created_at=row["created_at"],
        last_login_at=row["last_login_at"],
    )


@router.patch("/me", response_model=ProfileResponse)
async def update_profile_me(
    data: ProfileUpdateRequest,
    user=Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    await service.update_profile(
        user_id=user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        middle_name=data.middle_name,
        phone=data.phone,
        department_id=data.department_id,
    )

    row = await service.get_profile(user.id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return ProfileResponse(
        id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        middle_name=row["middle_name"],
        email=row["email"],
        phone=row["phone"],
        department_id=row["department_id"],
        department_name=row.get("department_name"),
        role_id=row["role_id"],
        role_name=row.get("role_name"),
        access_levels=row.get("access_levels") or [],
        created_at=row["created_at"],
        last_login_at=row["last_login_at"],
    )


@router.get("/me/activity", response_model=ProfileActivityResponse)
async def get_profile_activity(
    user=Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
):
    summary = await service.get_activity(user.id)

    return ProfileActivityResponse(
        documents_created=summary.get("documents_created", 0) or 0,
        documents_updated=summary.get("documents_updated", 0) or 0,
        drafts_created=summary.get("drafts_created", 0) or 0,
        collections_created=summary.get("collections_created", 0) or 0,
        last_action_at=summary.get("last_action_at", None),
        last_login_at=user.last_login_at,
    )


@router.get("/me/recent-actions", response_model=ProfileRecentActionsResponse)
async def get_profile_recent_actions(
    user=Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
    limit: int = Query(10, ge=1, le=100),
):
    rows = await service.get_recent_actions(user.id, limit=limit)

    items = [
        ProfileRecentAction(
            action=row["action"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            meta=row["meta"],
            created_at=row["created_at"],
        )
        for row in rows
    ]

    return ProfileRecentActionsResponse(items=items)
