from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class CollectionDocument(BaseModel):
    document_id: UUID
    title: str
    department_id: Optional[int]
    access_levels: List[str]
    tags: List[str]
    is_actual: bool
    upload_date: datetime


class CollectionWithDocuments(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    documents_count: int
    documents: List[CollectionDocument]


class CollectionCreateRequest(BaseModel):
    name: str


class CollectionCreateResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime

class CollectionAddDocumentRequest(BaseModel):
    document_id: UUID


class CollectionAddDocumentResponse(BaseModel):
    collection_id: UUID
    document_id: UUID
    created_at: datetime

