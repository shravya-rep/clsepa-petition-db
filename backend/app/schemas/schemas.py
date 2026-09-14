from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


# --- Keywords ---

class KeywordBase(BaseModel):
    name: str
    description: Optional[str] = None


class KeywordCreate(KeywordBase):
    pass


class KeywordOut(KeywordBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# --- Decisions ---

class DecisionBase(BaseModel):
    case_number: Optional[str] = None
    city: str
    address: Optional[str] = None
    unit: Optional[str] = None
    petitioner_name: Optional[str] = None
    respondent_name: Optional[str] = None
    hearing_date: Optional[datetime] = None
    decision_date: Optional[datetime] = None
    decision_type: Optional[str] = None
    hearing_officer: Optional[str] = None
    outcome_summary: Optional[str] = None
    amount_awarded: Optional[float] = None


class DecisionCreate(DecisionBase):
    keyword_ids: list[UUID] = []


class DecisionUpdate(BaseModel):
    case_number: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    unit: Optional[str] = None
    petitioner_name: Optional[str] = None
    respondent_name: Optional[str] = None
    hearing_date: Optional[datetime] = None
    decision_date: Optional[datetime] = None
    decision_type: Optional[str] = None
    hearing_officer: Optional[str] = None
    outcome_summary: Optional[str] = None
    amount_awarded: Optional[float] = None
    keyword_ids: Optional[list[UUID]] = None


class DecisionOut(DecisionBase):
    id: UUID
    pdf_filename: str
    keywords: list[KeywordOut] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DecisionSearch(BaseModel):
    keyword: Optional[str] = None
    city: Optional[str] = None
    decision_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    query: Optional[str] = None  # search case number or address


# --- Auth ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str]
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Audit ---

class AuditLogOut(BaseModel):
    id: UUID
    action: str
    entity_type: str
    entity_id: UUID
    details: Optional[str]
    timestamp: datetime
    user: UserOut

    class Config:
        from_attributes = True
