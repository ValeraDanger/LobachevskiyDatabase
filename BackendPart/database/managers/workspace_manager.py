from datetime import date
import json
from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID

from database.async_db import AsyncDatabase
from database.managers.base import BaseManager
from database.models.workspace import (
    WorkspaceCollection,
    WorkspaceCollectionItem,
)


class WorkspaceManager(BaseManager):
    def __init__(self, db: AsyncDatabase) -> None:
        super().__init__(db)

    # ------------------- workspace_queries -------------------

    async def create_query(
        self,
        *,
        user_id: UUID,
        question: str,
        date_from: Optional[date],
        date_to: Optional[date],
        department_ids: Optional[Sequence[int]],
        only_active: bool,
    ) -> UUID:
        filters: Dict[str, Any] = {
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "department_ids": list(department_ids) if department_ids else None,
            "only_active": only_active,
        }

        query = """
        INSERT INTO workspace_queries (user_id, question, filters)
        VALUES ($1, $2, $3::jsonb)
        RETURNING id
        """

        filters_json = json.dumps(filters, ensure_ascii=False)
        row = await self.db.fetchrow(query, user_id, question, filters_json)
        if row is None:
            raise RuntimeError("Failed to insert workspace_query: no row returned")

        return row["id"]

    async def get_query_by_id(self, query_id: UUID) -> Optional[Dict[str, Any]]:
        query = """
        SELECT id, user_id, question, filters, created_at, updated_at
        FROM workspace_queries
        WHERE id = $1
        """
        row = await self.db.fetchrow(query, query_id)
        return dict(row) if row is not None else None

    async def list_queries_for_user(
        self,
        user_id: UUID,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        query = """
        SELECT id, question, filters, created_at, updated_at
        FROM workspace_queries
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """
        rows = await self.db.fetch(query, user_id, limit)
        return [dict(r) for r in rows]

    # ------------------- workspace_collections -------------------

    async def get_collection_by_id(
        self,
        collection_id: UUID,
    ) -> Optional[WorkspaceCollection]:
        row = await self.db.fetchrow(
            """
            SELECT *
            FROM workspace_collections
            WHERE id = $1
            """,
            collection_id,
        )
        return WorkspaceCollection.from_record(row) if row else None

    async def create_collection(
        self,
        *,
        user_id: UUID,
        name: str,
    ) -> WorkspaceCollection:
        row = await self.db.fetchrow(
            """
            INSERT INTO workspace_collections (user_id, name)
            VALUES ($1, $2)
            RETURNING *
            """,
            user_id,
            name,
        )
        if row is None:
            raise RuntimeError("Failed to create workspace_collection")
        return WorkspaceCollection.from_record(row)

    async def list_collections_for_user(
        self, user_id: UUID
    ) -> List[WorkspaceCollection]:
        query = """
            SELECT *
            FROM workspace_collections
            WHERE user_id = $1
            ORDER BY created_at DESC
        """
        rows = await self.db.fetch(query, user_id)
        return [WorkspaceCollection.from_record(r) for r in rows]

    # ------------------- workspace_collection_items -------------------

    async def list_items_for_collection(
        self, collection_id: UUID
    ) -> List[WorkspaceCollectionItem]:
        query = """
            SELECT *
            FROM workspace_collection_items
            WHERE collection_id = $1
            ORDER BY created_at DESC
        """
        rows = await self.db.fetch(query, collection_id)
        return [WorkspaceCollectionItem.from_record(r) for r in rows]

    async def add_document_to_collection(
        self,
        *,
        collection_id: UUID,
        document_id: UUID,
    ) -> WorkspaceCollectionItem:
        row = await self.db.fetchrow(
            """
            INSERT INTO workspace_collection_items (collection_id, document_id)
            VALUES ($1, $2)
            ON CONFLICT (collection_id, document_id) DO NOTHING
            RETURNING *
            """,
            collection_id,
            document_id,
        )

        if row is None:
            existing = await self.db.fetchrow(
                """
                SELECT *
                FROM workspace_collection_items
                WHERE collection_id = $1 AND document_id = $2
                """,
                collection_id,
                document_id,
            )
            if existing is None:
                raise RuntimeError(
                    "Failed to insert or fetch workspace_collection_item"
                )
            return WorkspaceCollectionItem.from_record(existing)

        return WorkspaceCollectionItem.from_record(row)
