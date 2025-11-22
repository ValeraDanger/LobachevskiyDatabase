from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

import asyncpg


@dataclass
class AuditEvent:
    id: int
    user_id: Optional[UUID]
    action: str
    entity_type: str
    entity_id: Optional[str]
    meta: Optional[Dict[str, Any]]
    created_at: datetime

    @classmethod
    def from_record(cls, record: asyncpg.Record) -> "AuditEvent":
        return cls(
            id=record["id"],
            user_id=record["user_id"],
            action=record["action"],
            entity_type=record["entity_type"],
            entity_id=record["entity_id"],
            meta=record["meta"],
            created_at=record["created_at"],
        )
