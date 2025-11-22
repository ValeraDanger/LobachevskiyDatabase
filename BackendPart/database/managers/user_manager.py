from typing import Any, Dict, Optional
from uuid import UUID

from database.async_db import AsyncDatabase
from database.managers.base import BaseManager
from database.models.user import User, RefreshToken


class UserManager(BaseManager):
    def __init__(self, db: AsyncDatabase) -> None:
        super().__init__(db)

    # ------------------- users -------------------
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        row = await self.db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return User.from_record(row) if row else None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        row = await self.db.fetchrow(
            "SELECT * FROM users WHERE username = $1", username
        )
        return User.from_record(row) if row else None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        row = await self.db.fetchrow("SELECT * FROM users WHERE email = $1", email)
        return User.from_record(row) if row else None

    async def create_user(
        self,
        *,
        username: str,
        password_hash: str,
        first_name: Optional[str],
        last_name: Optional[str],
        middle_name: Optional[str],
        email: str,
        phone: Optional[str],
        department_id: Optional[int],
        role_id: Optional[int] = None,
    ) -> User:
        query = """
        INSERT INTO users (
            username, password_hash,
            first_name, last_name, middle_name,
            email, phone, department_id, role_id
        )
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
        RETURNING *
        """
        row = await self.db.fetchrow(
            query,
            username,
            password_hash,
            first_name,
            last_name,
            middle_name,
            email,
            phone,
            department_id,
            role_id,
        )
        if row is None:
            raise RuntimeError("Failed to insert user")
        return User.from_record(row)

    async def update_last_login(self, user_id: UUID) -> None:
        await self.db.execute(
            "UPDATE users SET last_login_at = now() WHERE id = $1",
            user_id,
        )

    async def get_user_profile_row(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        query = """
        SELECT
            u.*,
            d.name AS department_name,
            r.name AS role_name
        FROM users u
        LEFT JOIN departments d ON d.id = u.department_id
        LEFT JOIN roles r ON r.id = u.role_id
        WHERE u.id = $1
        """
        row = await self.db.fetchrow(query, user_id)
        return dict(row) if row else None

    async def update_user_profile(
        self,
        user_id: UUID,
        *,
        first_name: str,
        last_name: str,
        middle_name: Optional[str],
        phone: str,
        department_id: int,
    ) -> User:
        query = """
        UPDATE users
        SET
            first_name   = $2,
            last_name    = $3,
            middle_name  = $4,
            phone        = $5,
            department_id = $6
        WHERE id = $1
        RETURNING *
        """
        row = await self.db.fetchrow(
            query,
            user_id,
            first_name,
            last_name,
            middle_name,
            phone,
            department_id,
        )
        if row is None:
            raise RuntimeError("Failed to update user profile")
        return User.from_record(row)

    # ------------------- refresh_tokens -------------------
    async def create_refresh_token(
        self,
        user_id: UUID,
        token_jti: str,
        expires_at,
    ) -> RefreshToken:
        query = """
            INSERT INTO refresh_tokens (user_id, token_jti, expires_at)
            VALUES ($1, $2, $3)
            RETURNING *
        """
        row = await self.db.fetchrow(query, user_id, token_jti, expires_at)
        if row is None:
            raise RuntimeError("Failed to insert refresh token")
        return RefreshToken.from_record(row)

    async def get_refresh_token(self, token_jti: str) -> Optional[RefreshToken]:
        row = await self.db.fetchrow(
            """
            SELECT * FROM refresh_tokens
            WHERE token_jti = $1
            """,
            token_jti,
        )
        return RefreshToken.from_record(row) if row else None

    async def revoke_refresh_token(self, token_jti: str) -> None:
        await self.db.execute(
            "UPDATE refresh_tokens SET revoked = true WHERE token_jti = $1",
            token_jti,
        )

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self.db.execute(
            "UPDATE refresh_tokens SET revoked = true WHERE user_id = $1",
            user_id,
        )
