from typing import Any, Dict, List, Optional
from uuid import UUID

from database.async_db import AsyncDatabase
from database.managers.base import BaseManager
from database.models.rbac import Department, Role, Permission


class RbacManager(BaseManager):
    def __init__(self, db: AsyncDatabase) -> None:
        super().__init__(db)

    # ------------------- departments -------------------
    async def get_department_by_id(self, dep_id: int) -> Optional[Department]:
        row = await self.db.fetchrow("SELECT * FROM departments WHERE id = $1", dep_id)
        return Department.from_record(row) if row else None

    async def list_departments(self) -> List[Dict[str, Any]]:
        rows = await self.db.fetch(
            """
            SELECT id, code, name
            FROM departments
            ORDER BY name
        """
        )
        return [dict(r) for r in rows]

    # ------------------- roles -------------------
    async def list_roles(self) -> List[Role]:
        rows = await self.db.fetch("SELECT * FROM roles ORDER BY id")
        return [Role.from_record(r) for r in rows]

    async def get_by_code(self, code: str):
        row = await self.db.fetchrow("SELECT * FROM roles WHERE code = $1", code)
        return dict(row) if row else None

    # ------------------- permissions + role_permissions -------------------
    async def list_permissions_for_role(self, role_id: int) -> List[Permission]:
        query = """
            SELECT p.*
            FROM permissions p
            JOIN role_permissions rp ON rp.permission_code = p.code
            WHERE rp.role_id = $1
            ORDER BY p.code
        """
        rows = await self.db.fetch(query, role_id)
        return [Permission.from_record(r) for r in rows]

    async def user_has_permission(self, user_id: UUID, permission_code: str) -> bool:

        query = """
            SELECT 1
            FROM users u
            JOIN roles r ON r.id = u.role_id
            JOIN role_permissions rp ON rp.role_id = r.id
            WHERE u.id = $1 AND rp.permission_code = $2
            LIMIT 1
        """
        row = await self.db.fetchrow(query, user_id, permission_code)
        return row is not None
