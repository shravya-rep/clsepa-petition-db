from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Decision

router = APIRouter(prefix="/api/pdfs", tags=["pdfs"])


@router.get("/{decision_id}")
def serve_pdf(decision_id: UUID, db: Session = Depends(get_db)):
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return FileResponse(
        decision.pdf_path,
        media_type="application/pdf",
        filename=decision.pdf_filename,
    )
