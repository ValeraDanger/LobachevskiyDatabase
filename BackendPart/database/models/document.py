from dataclasses import dataclass
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from uuid import UUID

import asyncpg


@dataclass
class Document:
    id: UUID
    title: str
    description: Optional[str]
    category: Optional[str]

    department_id: Optional[int]
    access_levels: List[str]
    tags: List[str]

    uploaded_by_id: Optional[UUID]
    author: Optional[str]

    status: str
    is_valid: bool
    current_version: Optional[int]

    metadata: Optional[Dict[str, Any]]
    upload_date: datetime
    last_modified: Optional[datetime]

    @classmethod
    def from_record(cls, record: asyncpg.Record) -> "Document":
        return cls(
            id=record["id"],
            title=record["title"],
            description=record["description"],
            category=record["category"],
            department_id=record["department_id"],
            access_levels=record["access_levels"] or [],
            tags=record["tags"] or [],
            uploaded_by_id=record["uploaded_by_id"],
            author=record["author"],
            status=record["status"],
            is_valid=record["is_valid"],
            current_version=record["current_version"],
            metadata=record["metadata"],
            upload_date=record["upload_date"],
            last_modified=record["last_modified"],
        )