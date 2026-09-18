import json
import os
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.models import AuditLog, Decision, Keyword, User
from app.schemas.schemas import DecisionOut, DecisionUpdate

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


# --- Public endpoints ---

@router.get("/", response_model=list[DecisionOut])
def search_decisions(
    keyword: Optional[str] = Query(None, description="Keyword/category name to filter by"),
    city: Optional[str] = Query(None, description="City: 'East Palo Alto' or 'Mountain View'"),
    decision_type: Optional[str] = Query(None, description="e.g. HODecision, AppealDecision"),
    date_from: Optional[str] = Query(None, description="Filter decisions from this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter decisions up to this date (YYYY-MM-DD)"),
    q: Optional[str] = Query(None, description="Search case number or address"),
    db: Session = Depends(get_db),
):
    query = db.query(Decision).options(joinedload(Decision.keywords))

    if keyword:
        query = query.join(Decision.keywords).filter(Keyword.name.ilike(f"%{keyword}%"))
    if city:
        query = query.filter(Decision.city.ilike(f"%{city}%"))
    if decision_type:
        query = query.filter(Decision.decision_type.ilike(f"%{decision_type}%"))
    if date_from:
        query = query.filter(Decision.decision_date >= date_from)
    if date_to:
        query = query.filter(Decision.decision_date <= date_to)
    if q:
        query = query.filter(
            or_(
                Decision.case_number.ilike(f"%{q}%"),
                Decision.address.ilike(f"%{q}%"),
            )
        )

    return query.order_by(Decision.decision_date.desc()).all()


@router.get("/{decision_id}", response_model=DecisionOut)
def get_decision(decision_id: UUID, db: Session = Depends(get_db)):
    decision = db.query(Decision).options(joinedload(Decision.keywords)).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


# --- Admin endpoints ---

@router.post("/", response_model=DecisionOut)
async def create_decision(
    pdf: UploadFile = File(...),
    data: str = Form(..., description="JSON string of decision metadata"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        metadata = json.loads(data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in data field")

    os.makedirs(settings.PDF_UPLOAD_DIR, exist_ok=True)
    safe_filename = pdf.filename.replace("/", "_").replace("\\", "_")

    # Duplicate detection
    existing = db.query(Decision).filter(Decision.pdf_filename == safe_filename).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"A decision with this filename already exists: {safe_filename}")

    pdf_path = os.path.join(settings.PDF_UPLOAD_DIR, safe_filename)

    content = await pdf.read()
    with open(pdf_path, "wb") as f:
        f.write(content)

    keyword_ids = metadata.pop("keyword_ids", [])
    keywords = db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all() if keyword_ids else []

    # Parse date strings to datetime objects
    for date_field in ("hearing_date", "decision_date"):
        if date_field in metadata and isinstance(metadata[date_field], str):
            try:
                metadata[date_field] = datetime.fromisoformat(metadata[date_field])
            except ValueError:
                metadata[date_field] = None

    decision = Decision(
        pdf_filename=safe_filename,
        pdf_path=pdf_path,
        uploaded_by=admin.id,
        **metadata,
    )
    decision.keywords = keywords
    db.add(decision)
    db.flush()

    db.add(AuditLog(
        user_id=admin.id,
        action="create",
        entity_type="decision",
        entity_id=decision.id,
        details=f"Uploaded {safe_filename}",
    ))
    db.commit()
    db.refresh(decision)
    return decision


@router.put("/{decision_id}", response_model=DecisionOut)
def update_decision(
    decision_id: UUID,
    updates: DecisionUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    update_data = updates.model_dump(exclude_unset=True)
    keyword_ids = update_data.pop("keyword_ids", None)

    for field, value in update_data.items():
        setattr(decision, field, value)

    if keyword_ids is not None:
        decision.keywords = db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()

    db.add(AuditLog(
        user_id=admin.id,
        action="update",
        entity_type="decision",
        entity_id=decision.id,
        details=f"Updated fields: {', '.join(update_data.keys())}",
    ))
    db.commit()
    db.refresh(decision)
    return decision


@router.delete("/{decision_id}")
def delete_decision(
    decision_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    if os.path.exists(decision.pdf_path):
        os.remove(decision.pdf_path)

    db.add(AuditLog(
        user_id=admin.id,
        action="delete",
        entity_type="decision",
        entity_id=decision.id,
        details=f"Deleted {decision.pdf_filename}",
    ))
    db.delete(decision)
    db.commit()
    return {"detail": "Decision deleted"}
