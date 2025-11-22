from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg


@dataclass
class DocumentMetadataVersion:
    document_version_id: UUID
    changed_at: datetime
    changed_by_id: Optional[UUID]

    title: str
    description: Optional[str]
    category: Optional[str]
    department_id: Optional[int]
    access_levels: List[str]
    tags: List[str]
    is_valid: bool
    metadata: Optional[Dict[str, Any]]

    @classmethod
    def from_record(cls, record: asyncpg.Record) -> "DocumentMetadataVersion":
        return cls(
            document_version_id=record["document_version_id"],
            changed_at=record["changed_at"],
            changed_by_id=record["changed_by_id"],
            title=record["title"],
            description=record["description"],
            category=record["category"],
            department_id=record["department_id"],
            access_levels=record["access_levels"] or [],
            tags=record["tags"] or [],
            is_valid=record["is_valid"],
            metadata=record["metadata"],
        )
