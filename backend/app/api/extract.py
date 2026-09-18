import os
import tempfile

from fastapi import APIRouter, Depends, File, UploadFile
from app.core.security import require_admin
from app.models.models import User
from app.services.pdf_extractor import extract_from_pdf

router = APIRouter(prefix="/api/extract", tags=["extract"])


@router.post("/")
async def extract_pdf_metadata(
    pdf: UploadFile = File(...),
    admin: User = Depends(require_admin),
):
    """Extract metadata from a PDF without saving it. Returns suggested field values."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await pdf.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = extract_from_pdf(tmp_path)
    finally:
        os.unlink(tmp_path)

    return {
        "case_number": result.case_number or "",
        "city": result.city or "",
        "address": result.address or "",
        "unit": result.unit or "",
        "petitioner_name": result.petitioner_name or "",
        "respondent_name": result.respondent_name or "",
        "hearing_date": result.hearing_date.strftime("%Y-%m-%d") if result.hearing_date else "",
        "decision_date": result.decision_date.strftime("%Y-%m-%d") if result.decision_date else "",
        "decision_type": result.decision_type or "HODecision",
        "hearing_officer": result.hearing_officer or "",
        "confidence": result.confidence,
        "warnings": result.warnings,
    }
