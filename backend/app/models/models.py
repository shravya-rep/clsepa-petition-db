import uuid as uuid_mod
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Table,
    Text,
    TypeDecorator,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class GUID(TypeDecorator):
    """Cross-database UUID type. Uses PostgreSQL UUID, falls back to CHAR(36)."""
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid_mod.UUID):
            return uuid_mod.UUID(str(value))
        return value


# Many-to-many: decisions <-> keywords
decision_keywords = Table(
    "decision_keywords",
    Base.metadata,
    Column("decision_id", GUID(), ForeignKey("decisions.id", ondelete="CASCADE"), primary_key=True),
    Column("keyword_id", GUID(), ForeignKey("keywords.id", ondelete="CASCADE"), primary_key=True),
)


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(GUID(), primary_key=True, default=uuid_mod.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    decisions = relationship("Decision", secondary=decision_keywords, back_populates="keywords")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(GUID(), primary_key=True, default=uuid_mod.uuid4)

    # Case info
    case_number = Column(String(100), nullable=True, index=True)
    city = Column(String(50), nullable=False, index=True)
    address = Column(String(255), nullable=True)
    unit = Column(String(50), nullable=True)

    # Parties
    petitioner_name = Column(String(255), nullable=True)
    respondent_name = Column(String(255), nullable=True)

    # Dates
    hearing_date = Column(DateTime, nullable=True)
    decision_date = Column(DateTime, nullable=True)

    # Decision details
    decision_type = Column(String(100), nullable=True)
    hearing_officer = Column(String(255), nullable=True)
    outcome_summary = Column(Text, nullable=True)
    amount_awarded = Column(Numeric(10, 2), nullable=True)

    # PDF storage
    pdf_filename = Column(String(500), nullable=False)
    pdf_path = Column(String(1000), nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    uploaded_by = Column(GUID(), ForeignKey("users.id"), nullable=True)

    # Relationships
    keywords = relationship("Keyword", secondary=decision_keywords, back_populates="decisions")
    uploader = relationship("User", back_populates="uploads")


class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid_mod.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    uploads = relationship("Decision", back_populates="uploader")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid_mod.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(GUID(), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
