from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentSearchRequest(BaseModel):
    query: str = Field(..., description="Вопрос / поисковый запрос")

    date_from: Optional[date] = Field(None, description="Дата документа с")
    date_to: Optional[date] = Field(None, description="Дата документа по")
    department_ids: Optional[List[int]] = Field(
        None, description="Список id департаментов"
    )
    only_active: bool = Field(
        False,
        description="Только действующие редакции (is_valid = true)",
    )
    tags: Optional[List[str]] = None
    extensions: Optional[List[str]] = None


class DocumentSearchItem(BaseModel):
    document_id: UUID
    title: str
    snippet: str  # текст от РАГ-сервиса
    is_actual: bool
    date: datetime
    tags: List[str] | None


class DocumentSearchResponse(BaseModel):
    query_id: UUID
    answer: str
    items: List[DocumentSearchItem]
