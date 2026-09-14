"""
Migrate existing petition decision PDFs into the database.

Usage:
    python migrate_decisions.py /path/to/given/directory

Processes all PDFs in Mountain View/ and East Palo Alto/ subdirectories.
Extracts metadata automatically where possible (MV), flags manual review for EPA.
Copies PDFs to the uploads directory.
"""

import os
import shutil
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import Decision
from app.services.pdf_extractor import extract_from_pdf


def migrate(source_dir: str):
    source = Path(source_dir)
    if not source.exists():
        print(f"Source directory not found: {source}")
        sys.exit(1)

    os.makedirs(settings.PDF_UPLOAD_DIR, exist_ok=True)
    db = SessionLocal()

    pdf_files = list(source.rglob("*.pdf"))
    # Exclude non-decision files
    pdf_files = [f for f in pdf_files if "RFP" not in f.name and "Proposal" not in f.name]

    print(f"Found {len(pdf_files)} PDF files to migrate.\n")

    migrated = 0
    skipped = 0
    needs_review = []

    for pdf_path in sorted(pdf_files):
        filename = pdf_path.name

        # Skip duplicates
        existing = db.query(Decision).filter(Decision.pdf_filename == filename).first()
        if existing:
            print(f"  SKIP (exists): {filename}")
            skipped += 1
            continue

        # Extract metadata
        result = extract_from_pdf(str(pdf_path))

        # Copy PDF to uploads
        dest_path = os.path.join(settings.PDF_UPLOAD_DIR, filename)
        if not os.path.exists(dest_path):
            shutil.copy2(str(pdf_path), dest_path)

        # Create decision record
        decision = Decision(
            case_number=result.case_number,
            city=result.city or "Unknown",
            address=result.address,
            unit=result.unit,
            petitioner_name=result.petitioner_name,
            respondent_name=result.respondent_name,
            hearing_date=result.hearing_date,
            decision_date=result.decision_date,
            decision_type=result.decision_type,
            hearing_officer=result.hearing_officer,
            pdf_filename=filename,
            pdf_path=dest_path,
        )
        db.add(decision)
        migrated += 1

        status = "OK" if result.confidence == "high" else "REVIEW"
        if result.confidence != "high":
            needs_review.append((filename, result.warnings))

        print(f"  [{status}] {filename}")
        print(f"         city={result.city}, case={result.case_number}, "
              f"addr={result.address}, conf={result.confidence}")

    db.commit()
    db.close()

    print(f"\n{'='*60}")
    print(f"Migration complete: {migrated} migrated, {skipped} skipped")
    print(f"Total in database: {migrated + skipped}")

    if needs_review:
        print(f"\n{len(needs_review)} decisions need manual review:")
        for fname, warnings in needs_review:
            print(f"  - {fname}")
            for w in warnings:
                print(f"    {w}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_decisions.py /path/to/given/directory")
        sys.exit(1)
    migrate(sys.argv[1])
