from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class DocumentViewResponse(BaseModel):
    document_id: UUID
    title: str
    is_actual: bool
    access_levels: List[str]

    department_name: Optional[str]

    version_id: UUID
    uploaded_by: Optional[str]
    upload_date: datetime

    file_name: str
    storage_key: str
