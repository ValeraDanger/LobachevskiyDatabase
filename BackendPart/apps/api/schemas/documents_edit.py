from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class DocumentEditRequest(BaseModel):
    title: str
    department_id: Optional[int]
    category: Optional[str]
    access_levels: List[str]
    tags: List[str]
    comment: Optional[str] = None


class DocumentEditResponse(BaseModel):
    document_id: UUID
    version_id: UUID

    version: int

    title: str
    department_id: Optional[int]
    category: Optional[str]
    access_levels: List[str]
    tags: List[str]

    is_actual: bool
    upload_date: datetime
    uploaded_by: Optional[str]
    file_name: str
    storage_key: str

    change_notes: Optional[str]
