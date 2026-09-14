from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.models import AuditLog, Keyword, User
from app.schemas.schemas import KeywordCreate, KeywordOut

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.get("/", response_model=list[KeywordOut])
def list_keywords(db: Session = Depends(get_db)):
    return db.query(Keyword).order_by(Keyword.name).all()


@router.post("/", response_model=KeywordOut)
def create_keyword(data: KeywordCreate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if db.query(Keyword).filter(Keyword.name == data.name).first():
        raise HTTPException(status_code=400, detail="Keyword already exists")
    keyword = Keyword(name=data.name, description=data.description)
    db.add(keyword)
    db.flush()
    db.add(AuditLog(user_id=admin.id, action="create", entity_type="keyword", entity_id=keyword.id))
    db.commit()
    db.refresh(keyword)
    return keyword


@router.delete("/{keyword_id}")
def delete_keyword(keyword_id: UUID, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    db.add(AuditLog(user_id=admin.id, action="delete", entity_type="keyword", entity_id=keyword.id))
    db.delete(keyword)
    db.commit()
    return {"detail": "Keyword deleted"}
