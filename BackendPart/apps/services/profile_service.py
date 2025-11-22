from uuid import UUID

from database.managers.user_manager import UserManager
from database.managers.audit_manager import AuditManager


class ProfileService:
    def __init__(self, user_manager: UserManager, audit_manager: AuditManager):
        self.user_manager = user_manager
        self.audit_manager = audit_manager

    async def get_profile(self, user_id: UUID):
        return await self.user_manager.get_user_profile_row(user_id)

    async def update_profile(
        self,
        user_id: UUID,
        *,
        first_name: str,
        last_name: str,
        middle_name: str | None,
        phone: str,
        department_id: int,
    ):
        return await self.user_manager.update_user_profile(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            phone=phone,
            department_id=department_id,
        )

    async def get_activity(self, user_id: UUID):
        return await self.audit_manager.get_user_activity_summary(user_id)

    async def get_recent_actions(self, user_id: UUID, limit: int = 10):
        return await self.audit_manager.get_user_recent_actions(user_id, limit)
