from dataclasses import dataclass
from typing import Optional

import asyncpg


@dataclass
class Department:
    id: int
    code: str
    name: str

    @classmethod
    def from_record(cls, record: asyncpg.Record) -> "Department":
        return cls(
            id=record["id"],
            code=record["code"],
            name=record["name"],
        )


@dataclass
class Role:
    id: int
    code: str
    name: str
    description: Optional[str]

    @classmethod
    def from_record(cls, record: asyncpg.Record) -> "Role":
        return cls(
            id=record["id"],
            code=record["code"],
            name=record["name"],
            description=record["description"],
        )


@dataclass
class Permission:
    code: str
    description: Optional[str]

    @classmethod
    def from_record(cls, record: asyncpg.Record) -> "Permission":
        return cls(
            code=record["code"],
            description=record["description"],
        )


@dataclass
class RolePermission:
    role_id: int
    permission_code: str

    @classmethod
    def from_record(cls, record: asyncpg.Record) -> "RolePermission":
        return cls(
            role_id=record["role_id"],
            permission_code=record["permission_code"],
        )
