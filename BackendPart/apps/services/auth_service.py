from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4

from database.managers.user_manager import UserManager
from database.managers.rbac_manager import RbacManager

from utils.config import DEFAULT_ROLE

from apps.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class AuthService:
    def __init__(self, user_manager: UserManager, rbac_manager: RbacManager):
        self.user_manager = user_manager
        self.rbac_manager = rbac_manager

    # -------- register --------
    async def register(
        self,
        *,
        first_name: str,
        last_name: str,
        middle_name: str | None,
        department_id: int | None,
        phone: str | None,
        email: str,
        password: str,
    ):
        # username = email
        existing = await self.user_manager.get_user_by_email(email)
        if existing is not None:
            raise ValueError("email_taken")

        username = email
        password_hash = hash_password(password)

        viewer_role = await self.rbac_manager.get_by_code(DEFAULT_ROLE)
        if viewer_role is None:
            raise RuntimeError(f"Default role {DEFAULT_ROLE} not found in DB")

        user = await self.user_manager.create_user(
            username=username,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            email=email,
            phone=phone,
            department_id=department_id,
            role_id=viewer_role["id"],
        )

        return await self._issue_tokens_for_user(user.id)

    # -------- login --------
    async def login(self, email: str, password: str):
        user = await self.user_manager.get_user_by_email(email)
        if not user or not user.is_active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        await self.user_manager.update_last_login(user.id)
        return await self._issue_tokens_for_user(user.id)

    # -------- logout --------
    async def logout(self, refresh_token: str):
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("not_refresh")

        jti = payload.get("jti")
        if not jti:
            raise ValueError("no_jti")

        await self.user_manager.revoke_refresh_token(jti)

    # -------- internal --------
    async def _issue_tokens_for_user(self, user_id: UUID):
        jti = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        await self.user_manager.create_refresh_token(user_id, jti, expires_at)

        access = create_access_token(str(user_id), jti)
        refresh = create_refresh_token(str(user_id), jti)

        return access, refresh
