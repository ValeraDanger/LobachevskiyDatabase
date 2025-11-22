import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from database.async_db import AsyncDatabase
from database.managers.base import BaseManager
from database.models.audit import AuditEvent


class AuditManager(BaseManager):
    def __init__(self, db: AsyncDatabase) -> None:
        super().__init__(db)

    # ------------------- audit_events -------------------
    async def log_event(
        self,
        *,
        user_id: Optional[UUID],
        action: str,
        entity_type: str,
        entity_id: Optional[str],
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        meta_json: Optional[str]
        if meta is None:
            meta_json = None
        else:
            meta_json = json.dumps(meta, ensure_ascii=False)

        query = """
        INSERT INTO audit_events (user_id, action, entity_type, entity_id, meta)
        VALUES ($1, $2::audit_action, $3, $4, $5)
        """
        await self.db.execute(query, user_id, action, entity_type, entity_id, meta_json)

    async def get_user_activity_summary(self, user_id: UUID) -> Dict[str, Any]:
        query = """
        SELECT
            COUNT(*) FILTER (WHERE action = 'create_document')   AS documents_created,
            COUNT(*) FILTER (WHERE action = 'update_document')   AS documents_updated,
            COUNT(*) FILTER (WHERE action = 'create_draft')      AS drafts_created,
            COUNT(*) FILTER (WHERE action = 'create_collection') AS collections_created,
            MAX(created_at)                                      AS last_action_at
        FROM audit_events
        WHERE user_id = $1
        """
        row = await self.db.fetchrow(query, user_id)
        if row is None:
            return {
                "documents_created": 0,
                "documents_updated": 0,
                "drafts_created": 0,
                "collections_created": 0,
                "last_action_at": None,
            }
        return dict(row)

    async def get_user_recent_actions(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        query = """
        SELECT action, entity_type, entity_id, meta, created_at
        FROM audit_events
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """
        rows = await self.db.fetch(query, user_id, limit)
        result: List[Dict[str, Any]] = []
        for r in rows:
            row_dict = dict(r)
            meta = row_dict.get("meta")

            if isinstance(meta, str):
                try:
                    row_dict["meta"] = json.loads(meta)
                except json.JSONDecodeError:
                    row_dict["meta"] = None

            result.append(row_dict)

        return result
