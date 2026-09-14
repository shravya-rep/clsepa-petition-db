import os
import pytest
from app.services.pdf_extractor import (
    extract_from_pdf,
    _extract_from_filename,
    _parse_date,
)


class TestFilenameExtraction:
    def test_mv_ho_decision(self):
        r = _extract_from_filename("California_1556 2023.11.21 HODecision_Redacted.pdf")
        assert r.city == "Mountain View"
        assert r.address == "1556 California"
        assert r.decision_type == "HODecision"
        assert r.decision_date is not None
        assert r.decision_date.year == 2023

    def test_mv_appeal_decision(self):
        r = _extract_from_filename("Wright_1725 2023.10.12 AppealDecision_Redacted.pdf")
        assert r.city == "Mountain View"
        assert r.decision_type == "AppealDecision"

    def test_mv_hocp_decision(self):
        r = _extract_from_filename("Continental_707 2024.03.04 HOCPDecision_Redacted.pdf")
        assert r.decision_type == "HOCPDecision"

    def test_epa_decision(self):
        r = _extract_from_filename("Decision Franklin v WPC 20230001 and 20230002.pdf")
        assert r.city == "East Palo Alto"
        assert r.petitioner_name == "Franklin"
        assert r.case_number == "20230001"

    def test_epa_appeal(self):
        r = _extract_from_filename("2023-01-23 Rent Boards Finding and Decisions Appeal Case 2021056 - 2070 Glen Way Apartment F.pdf")
        assert r.case_number == "2021056"
        assert r.decision_type == "AppealDecision"


class TestDateParsing:
    def test_full_month(self):
        d = _parse_date("November 22, 2023")
        assert d is not None
        assert d.month == 11 and d.day == 22 and d.year == 2023

    def test_iso_format(self):
        d = _parse_date("2023-11-22")
        assert d is not None

    def test_dot_format(self):
        d = _parse_date("2023.11.22")
        assert d is not None

    def test_empty(self):
        assert _parse_date("") is None
        assert _parse_date(None) is None

    def test_garbage(self):
        assert _parse_date("See attached Proof of Service.") is None


class TestFullExtraction:
    """Test against actual PDF files if available."""

    MV_DIR = "/Users/shravya/ThoughtSolution/CLSEPA/given/Mountain View"
    EPA_DIR = "/Users/shravya/ThoughtSolution/CLSEPA/given/East Palo Alto "

    @pytest.mark.skipif(
        not os.path.exists("/Users/shravya/ThoughtSolution/CLSEPA/given/Mountain View"),
        reason="Source PDFs not available",
    )
    def test_mv_california_1556(self):
        r = extract_from_pdf(f"{self.MV_DIR}/California_1556 2023.11.21 HODecision_Redacted.pdf")
        assert r.city == "Mountain View"
        assert r.confidence == "high"
        assert "C22230055" in r.case_number
        assert r.hearing_officer == "Barbara M. Anscher"
        assert r.petitioner_name == "Oralia Belem Zavala Vasquez"

    @pytest.mark.skipif(
        not os.path.exists("/Users/shravya/ThoughtSolution/CLSEPA/given/Mountain View"),
        reason="Source PDFs not available",
    )
    def test_mv_del_medio(self):
        r = extract_from_pdf(f"{self.MV_DIR}/Del Medio_141 2022.11.04 HODecision_Redacted.pdf")
        assert r.city == "Mountain View"
        assert r.hearing_officer is not None

    @pytest.mark.skipif(
        not os.path.exists("/Users/shravya/ThoughtSolution/CLSEPA/given/East Palo Alto "),
        reason="Source PDFs not available",
    )
    def test_epa_franklin(self):
        r = extract_from_pdf(f"{self.EPA_DIR}/Decision Franklin v WPC 20230001 and 20230002.pdf")
        assert r.city == "East Palo Alto"
        assert r.confidence == "low"
        assert len(r.warnings) > 0
