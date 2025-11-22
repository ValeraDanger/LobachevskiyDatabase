from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


class ProfileResponse(BaseModel):
    id: UUID

    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]

    email: Optional[EmailStr]
    phone: Optional[str]

    department_id: Optional[int]
    department_name: Optional[str] = None

    role_id: Optional[int]
    role_name: Optional[str] = None

    access_levels: List[str] = []

    created_at: datetime
    last_login_at: Optional[datetime]


class ProfileUpdateRequest(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    middle_name: Optional[str] = None

    phone: str = Field(..., min_length=3)
    department_id: int = Field(..., ge=1)


class ProfileActivityResponse(BaseModel):
    documents_created: int
    documents_updated: int
    drafts_created: int
    collections_created: int

    last_action_at: Optional[datetime]
    last_login_at: Optional[datetime]


class ProfileRecentAction(BaseModel):
    action: str
    entity_type: str
    entity_id: Optional[str]
    created_at: datetime
    meta: Optional[dict]


class ProfileRecentActionsResponse(BaseModel):
    items: List[ProfileRecentAction]
