from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import asyncpg


@dataclass
class WorkspaceCollection:
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime

    @classmethod
    def from_record(cls, record: asyncpg.Record) -> "WorkspaceCollection":
        return cls(
            id=record["id"],
            user_id=record["user_id"],
            name=record["name"],
            created_at=record["created_at"],
        )


@dataclass
class WorkspaceCollectionItem:
    id: UUID
    collection_id: UUID
    document_id: UUID
    created_at: datetime

    @classmethod
    def from_record(cls, record: asyncpg.Record) -> "WorkspaceCollectionItem":
        return cls(
            id=record["id"],
            collection_id=record["collection_id"],
            document_id=record["document_id"],
            created_at=record["created_at"],
        )
