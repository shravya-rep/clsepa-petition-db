import base64
import io
import json
import os
import re
import tempfile

import pdfplumber
from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import settings
from app.core.security import require_admin
from app.models.models import User
from app.services.pdf_extractor import extract_from_pdf

router = APIRouter(prefix="/api/extract", tags=["extract"])

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def _ai_extract(tmp_path: str, pdfplumber_result: dict) -> dict:
    """Use Claude AI to fill missing fields and generate summary."""
    if not ANTHROPIC_API_KEY:
        return pdfplumber_result

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    except Exception:
        return pdfplumber_result

    # Read PDF text
    pdf = pdfplumber.open(tmp_path)
    text = ""
    for page in pdf.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"

    # If no text (scanned image), use vision
    if not text.strip():
        images = []
        for page in pdf.pages[:6]:
            img = page.to_image(resolution=200)
            buf = io.BytesIO()
            img.original.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            images.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": b64},
            })
        pdf.close()

        content = images + [{"type": "text", "text": """Extract ALL fields from this scanned legal petition decision. Return ONLY valid JSON:

- case_number: Case/petition number(s)
- city: "East Palo Alto" or "Mountain View"
- address: Property address
- unit: Unit/apartment number
- petitioner_name: Tenant name(s)
- respondent_name: Landlord/property owner name
- hearing_date: Hearing date in YYYY-MM-DD
- decision_date: Decision date in YYYY-MM-DD
- decision_type: One of "HODecision", "AppealDecision", "HOCPDecision", "RemandAppealDecision"
- hearing_officer: Name of hearing officer/examiner, or "Rental Housing Committee" for committee decisions
- amount_awarded: Total dollar amount awarded/rebated as a number (e.g. 1100.00). null if none.
- outcome_summary: One short sentence (max 20 words). Format: "Petition [granted/denied]. [Key outcome]." Example: "Petition granted. Rent reduced 10% for mold and plumbing issues, $1,100 rebate ordered."
- suggested_keywords: Array of applicable issue categories from this list ONLY: ["Mold", "Plumbing", "Electrical", "Heat", "Rent Overcharge", "Habitability", "Code Violations", "Pest Infestation", "Water", "Appliance", "Structural", "Common Area Maintenance", "Security", "Carpet", "Patio", "Smoke Detectors", "Rent Reduction", "Rent Rebate"]. Select all that apply based on the issues discussed.

If cannot determine, use null."""}]
    else:
        pdf.close()
        # Send beginning + end of document (signatures are at the end)
        if len(text) > 10000:
            doc_text = text[:5000] + "\n...\n" + text[-5000:]
        else:
            doc_text = text

        content = [{"type": "text", "text": f"""Extract ALL fields from this legal petition decision. Return ONLY valid JSON:

- case_number: Case/petition number(s)
- city: "East Palo Alto" or "Mountain View"
- address: Property address
- unit: Unit/apartment number
- petitioner_name: Tenant name(s)
- respondent_name: Landlord/property owner name
- hearing_date: Hearing date in YYYY-MM-DD
- decision_date: Decision date in YYYY-MM-DD
- decision_type: One of "HODecision", "AppealDecision", "HOCPDecision", "RemandAppealDecision"
- hearing_officer: Name of hearing officer/examiner who signed the decision (check signature lines at the end), or "Rental Housing Committee" for committee decisions
- outcome_summary: One short sentence (max 20 words). Format: "Petition [granted/denied]. [Key outcome]." Example: "Petition granted. Rent reduced 10% for mold and plumbing issues, $1,100 rebate ordered." What were the main issues?

If cannot determine, use null.

DOCUMENT:
{doc_text}"""}]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{"role": "user", "content": content}],
        )
        result_text = response.content[0].text.strip()
        json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
        if json_match:
            ai_data = json.loads(json_match.group())
            # Merge: AI fills in what pdfplumber missed
            for key, val in ai_data.items():
                if val is not None and (not pdfplumber_result.get(key) or key in ("suggested_keywords", "amount_awarded", "outcome_summary")):
                    pdfplumber_result[key] = val
            return pdfplumber_result
    except Exception:
        pass

    return pdfplumber_result


@router.post("/")
async def extract_pdf_metadata(
    pdf: UploadFile = File(...),
    admin: User = Depends(require_admin),
):
    """Extract metadata from a PDF. Uses pdfplumber first, then Claude AI to fill gaps."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await pdf.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = extract_from_pdf(tmp_path)

        extracted = {
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
            "outcome_summary": "",
            "confidence": result.confidence,
            "warnings": result.warnings,
        }

        # Check if any fields are missing
        key_fields = ["case_number", "respondent_name", "hearing_officer", "decision_date"]
        has_gaps = any(not extracted.get(f) for f in key_fields)

        # Always run AI for summary, and for any missing fields
        if ANTHROPIC_API_KEY and (has_gaps or not extracted.get("outcome_summary")):
            extracted = _ai_extract(tmp_path, extracted)
            if extracted.get("outcome_summary"):
                extracted["confidence"] = "high"
                extracted["warnings"] = []
    finally:
        os.unlink(tmp_path)

    return extracted
