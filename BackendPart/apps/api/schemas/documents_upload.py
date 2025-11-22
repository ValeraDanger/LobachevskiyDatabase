from typing import List, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentUploadFromViewerResponse(BaseModel):
    document_id: UUID
    version_id: UUID


class DocumentModerateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    department_id: int
    access_levels: List[str] = []
    tags: List[str]
    action: Literal["approve", "reject"]


class DocumentModerateResponse(BaseModel):
    document_id: UUID
    version_id: UUID
    document_status: str
    version_status: str
