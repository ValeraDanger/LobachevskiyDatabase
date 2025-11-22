from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import asyncpg


@dataclass
class User:
    id: UUID
    username: str
    password_hash: str

    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]

    email: Optional[str]
    phone: Optional[str]

    department_id: Optional[int]
    role_id: Optional[int]
    access_levels: List[str]

    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    @classmethod
    def from_record(cls, record: asyncpg.Record) -> "User":
        return cls(
            id=record["id"],
            username=record["username"],
            password_hash=record["password_hash"],
            first_name=record["first_name"],
            last_name=record["last_name"],
            middle_name=record["middle_name"],
            email=record["email"],
            phone=record["phone"],
            department_id=record["department_id"],
            role_id=record["role_id"],
            access_levels=record["access_levels"] or [],
            is_active=record["is_active"],
            created_at=record["created_at"],
            last_login_at=record["last_login_at"],
        )


@dataclass
class RefreshToken:
    id: UUID
    user_id: UUID
    token_jti: str
    expires_at: datetime
    created_at: datetime
    revoked: bool

    @classmethod
    def from_record(cls, record: asyncpg.Record) -> "RefreshToken":
        return cls(
            id=record["id"],
            user_id=record["user_id"],
            token_jti=record["token_jti"],
            expires_at=record["expires_at"],
            created_at=record["created_at"],
            revoked=record["revoked"],
        )
