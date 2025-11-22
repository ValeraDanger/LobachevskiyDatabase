from dataclasses import dataclass
from datetime import datetime, date
from typing import Any, Dict, Optional
from uuid import UUID

import asyncpg


@dataclass
class DocumentVersion:
    id: UUID
    document_id: UUID
    version: int

    file_name: str
    file_type: str
    file_size: int
    storage_key: str

    upload_date: datetime
    uploaded_by_id: Optional[UUID]

    status: str
    valid_from: Optional[date]
    valid_to: Optional[date]
    change_notes: Optional[str]
    metadata: Optional[Dict[str, Any]]

    is_current: bool

    @classmethod
    def from_record(cls, record: asyncpg.Record) -> "DocumentVersion":
        return cls(
            id=record["id"],
            document_id=record["document_id"],
            version=record["version"],
            file_name=record["file_name"],
            file_type=record["file_type"],
            file_size=record["file_size"],
            storage_key=record["storage_key"],
            upload_date=record["upload_date"],
            uploaded_by_id=record["uploaded_by_id"],
            status=record["status"],
            valid_from=record["valid_from"],
            valid_to=record["valid_to"],
            change_notes=record["change_notes"],
            metadata=record["metadata"],
            is_current=record["is_current"],
        )
