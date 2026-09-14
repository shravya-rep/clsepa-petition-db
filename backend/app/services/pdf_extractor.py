"""
PDF metadata extraction pipeline for CLSEPA petition decisions.

Two formats:
- Mountain View (CSFRA): Structured table on page 1 with case info. Machine-readable.
- East Palo Alto (RSB): Scanned image PDFs. No extractable text.
  Metadata parsed from filename + requires manual entry at upload.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import pdfplumber


@dataclass
class ExtractedDecision:
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
    extraction_method: str = "manual"
    confidence: str = "low"
    warnings: list[str] = field(default_factory=list)


def extract_from_pdf(filepath: str) -> ExtractedDecision:
    """Extract metadata from a petition decision PDF."""
    path = Path(filepath)
    filename = path.name

    # Determine city from directory or filename patterns
    if "Mountain View" in str(path) or "CSFRA" in filename.upper():
        return _extract_mountain_view(filepath, filename)
    elif "East Palo Alto" in str(path) or "RSB" in filename.upper():
        return _extract_east_palo_alto(filepath, filename)
    else:
        # Try MV extraction first (has table), fall back to filename
        result = _extract_mountain_view(filepath, filename)
        if result.confidence == "high":
            return result
        return _extract_from_filename(filename)


def _extract_mountain_view(filepath: str, filename: str) -> ExtractedDecision:
    """Extract from Mountain View CSFRA decisions (structured table on page 1)."""
    result = ExtractedDecision(city="Mountain View", extraction_method="pdfplumber_table")

    try:
        pdf = pdfplumber.open(filepath)
        page = pdf.pages[0]
        tables = page.extract_tables()

        if not tables:
            pdf.close()
            result.warnings.append("No table found on page 1, falling back to text extraction")
            return _extract_mv_from_text(filepath, filename, result)

        table = tables[0]
        table_dict = {}
        for row in table:
            if row and len(row) >= 2 and row[0]:
                key = row[0].strip().rstrip(":").lower()
                val = row[1].strip() if row[1] else ""
                table_dict[key] = val

        # Map table fields
        result.case_number = table_dict.get("rental housing committee case no.", "").strip()
        if not result.case_number:
            result.case_number = table_dict.get("case no", "").strip()

        addr_raw = table_dict.get("address and unit(s) of rental\nproperty", "")
        if not addr_raw:
            addr_raw = table_dict.get("property address", "")
        if addr_raw:
            result.address = addr_raw.replace("\n", ", ").strip()

        unit_raw = table_dict.get("affected unit{s}", "") or table_dict.get("affected unit(s)", "")
        if unit_raw:
            result.unit = unit_raw.strip()

        result.petitioner_name = table_dict.get("petitioner tenant name(s)", "").strip()
        result.respondent_name = table_dict.get("respondent landlord name(s)", "") or table_dict.get("respondent landlord names(s)", "")
        if result.respondent_name:
            result.respondent_name = result.respondent_name.strip()

        result.hearing_officer = table_dict.get("hearing officer", "").strip()

        # Parse dates
        hearing_str = table_dict.get("date(s) of hearing", "") or table_dict.get("dates of hearings", "")
        result.hearing_date = _parse_date(hearing_str)

        decision_str = table_dict.get("date of decision", "")
        result.decision_date = _parse_date(decision_str)

        # Decision type from filename
        result.decision_type = _detect_decision_type(filename)

        result.confidence = "high"
        pdf.close()

    except Exception as e:
        result.warnings.append(f"Table extraction error: {e}")
        result.confidence = "low"

    return result


def _extract_mv_from_text(filepath: str, filename: str, result: ExtractedDecision) -> ExtractedDecision:
    """Fallback: extract MV data from full text (for appeal decisions without tables)."""
    try:
        pdf = pdfplumber.open(filepath)
        full_text = ""
        for page in pdf.pages[:3]:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        pdf.close()

        if not full_text:
            result.warnings.append("No text extractable from PDF")
            result.confidence = "low"
            # Fall back to filename
            fn_result = _extract_from_filename(filename)
            fn_result.city = "Mountain View"
            return fn_result

        # Extract case number (pattern: C22230037 or Petition C22230037)
        case_match = re.search(r"(?:Case\s*(?:No\.?:?\s*)?|Petition\s+)(C?\d{7,8}(?:\s*,\s*C?\d{7,8})*)", full_text, re.IGNORECASE)
        if case_match:
            result.case_number = case_match.group(1).strip()

        # Extract address
        addr_match = re.search(r"(\d+\s+[\w\s]+(?:Street|Avenue|Ave|Drive|Dr|Way|Road|Rd|Boulevard|Blvd)[\w\s,]*Mountain\s*View)", full_text, re.IGNORECASE)
        if addr_match:
            result.address = addr_match.group(1).strip()

        # Extract petitioner
        pet_match = re.search(r'(?:Tenant|Petitioner)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\(', full_text)
        if pet_match:
            result.petitioner_name = pet_match.group(1).strip()

        result.decision_type = _detect_decision_type(filename)
        result.confidence = "medium"

    except Exception as e:
        result.warnings.append(f"Text extraction error: {e}")

    return result


def _extract_east_palo_alto(filepath: str, filename: str) -> ExtractedDecision:
    """
    EPA decisions are scanned images — no text extractable.
    Parse what we can from the filename, rest requires manual entry.
    """
    result = _extract_from_filename(filename)
    result.city = "East Palo Alto"
    result.extraction_method = "filename_only"
    result.warnings.append("EPA PDF is a scanned image; metadata requires manual entry")
    return result


def _extract_from_filename(filename: str) -> ExtractedDecision:
    """Parse metadata from filename patterns."""
    result = ExtractedDecision(confidence="low", extraction_method="filename")

    # Mountain View pattern: StreetName_Number YYYY.MM.DD Type_Redacted.pdf
    mv_match = re.match(
        r"(\w+)_(\d+)\s+(\d{4})\.(\d{2})\.(\d{2})\s+(\w+?)(?:_Redacted)?\.pdf",
        filename, re.IGNORECASE,
    )
    if mv_match:
        street = mv_match.group(1)
        number = mv_match.group(2)
        year, month, day = mv_match.group(3), mv_match.group(4), mv_match.group(5)
        dtype = mv_match.group(6)

        result.city = "Mountain View"
        result.address = f"{number} {street}"
        result.decision_type = _detect_decision_type(dtype)
        result.decision_date = _parse_date(f"{year}-{month}-{day}")
        result.confidence = "medium"
        return result

    # EPA pattern: "Decision Name v Name CaseNumber.pdf"
    epa_match = re.match(r"Decision\s+(\w+)\s+v\s+(\w+)\s+([\d]+)", filename, re.IGNORECASE)
    if epa_match:
        result.city = "East Palo Alto"
        result.petitioner_name = epa_match.group(1)
        result.respondent_name = epa_match.group(2)
        result.case_number = epa_match.group(3)
        result.decision_type = "HODecision"
        return result

    # EPA appeal pattern
    epa_appeal = re.search(r"Appeal\s*Case\s*(\d+)", filename, re.IGNORECASE)
    if epa_appeal:
        result.city = "East Palo Alto"
        result.case_number = epa_appeal.group(1)
        result.decision_type = "AppealDecision"
        return result

    return result


def _detect_decision_type(text: str) -> str:
    """Detect decision type from text/filename."""
    text_lower = text.lower()
    if "remandappeal" in text_lower:
        return "RemandAppealDecision"
    if "appeal" in text_lower:
        return "AppealDecision"
    if "hocp" in text_lower:
        return "HOCPDecision"
    if "hodecision" in text_lower or "ho decision" in text_lower:
        return "HODecision"
    return "HODecision"


def _parse_date(date_str: str) -> Optional[datetime]:
    """Try multiple date formats."""
    if not date_str or not date_str.strip():
        return None
    date_str = date_str.strip()

    formats = [
        "%B %d, %Y",       # November 22, 2023
        "%Y-%m-%d",         # 2023-11-22
        "%Y.%m.%d",         # 2023.11.22
        "%m/%d/%Y",         # 11/22/2023
        "%b %d, %Y",        # Nov 22, 2023
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # Try to find a date pattern in the string
    match = re.search(r"(\w+\s+\d{1,2},?\s+\d{4})", date_str)
    if match:
        for fmt in formats:
            try:
                return datetime.strptime(match.group(1), fmt)
            except ValueError:
                continue

    return None
