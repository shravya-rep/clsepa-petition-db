import json
import io


def _create_decision(client, auth_headers, keywords=None, **overrides):
    """Helper to create a decision via the API."""
    metadata = {
        "city": "Mountain View",
        "case_number": "C22230001",
        "address": "141 Del Medio",
        "decision_type": "HODecision",
        "decision_date": "2023-01-15",
    }
    if keywords:
        metadata["keyword_ids"] = keywords
    metadata.update(overrides)

    pdf_content = b"%PDF-1.4 test content"
    files = {"pdf": ("test_decision.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {"data": json.dumps(metadata)}

    return client.post("/api/decisions/", files=files, data=data, headers=auth_headers)


def test_create_decision(client, auth_headers):
    res = _create_decision(client, auth_headers)
    assert res.status_code == 200
    d = res.json()
    assert d["city"] == "Mountain View"
    assert d["case_number"] == "C22230001"


def test_create_decision_with_keywords(client, auth_headers, sample_keywords):
    kw_ids = [sample_keywords[0][0], sample_keywords[1][0]]
    res = _create_decision(client, auth_headers, keywords=kw_ids)
    assert res.status_code == 200
    assert len(res.json()["keywords"]) == 2


def test_create_decision_requires_auth(client):
    pdf_content = b"%PDF-1.4 test"
    files = {"pdf": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    data = {"data": json.dumps({"city": "Mountain View"})}
    res = client.post("/api/decisions/", files=files, data=data)
    assert res.status_code == 401


def test_list_decisions_public(client, auth_headers):
    _create_decision(client, auth_headers, case_number="C001")
    _create_decision(client, auth_headers, case_number="C002", city="East Palo Alto")

    res = client.get("/api/decisions/")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_filter_by_city(client, auth_headers):
    _create_decision(client, auth_headers, case_number="C001", city="Mountain View")
    _create_decision(client, auth_headers, case_number="C002", city="East Palo Alto")

    res = client.get("/api/decisions/?city=Mountain View")
    data = res.json()
    assert len(data) == 1
    assert data[0]["city"] == "Mountain View"


def test_filter_by_keyword(client, auth_headers, sample_keywords):
    mold_id = sample_keywords[0][0]
    _create_decision(client, auth_headers, case_number="C001", keywords=[mold_id])
    _create_decision(client, auth_headers, case_number="C002")

    res = client.get("/api/decisions/?keyword=Mold")
    data = res.json()
    assert len(data) == 1
    assert data[0]["case_number"] == "C001"


def test_search_by_address(client, auth_headers):
    _create_decision(client, auth_headers, case_number="C001", address="141 Del Medio")
    _create_decision(client, auth_headers, case_number="C002", address="511 Central Ave")

    res = client.get("/api/decisions/?q=Central")
    data = res.json()
    assert len(data) == 1
    assert "Central" in data[0]["address"]


def test_get_single_decision(client, auth_headers):
    create_res = _create_decision(client, auth_headers)
    decision_id = create_res.json()["id"]

    res = client.get(f"/api/decisions/{decision_id}")
    assert res.status_code == 200
    assert res.json()["id"] == decision_id


def test_update_decision(client, auth_headers):
    create_res = _create_decision(client, auth_headers)
    decision_id = create_res.json()["id"]

    res = client.put(f"/api/decisions/{decision_id}", json={
        "outcome_summary": "Rent reduced by 5%",
        "amount_awarded": 396.76,
    }, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["outcome_summary"] == "Rent reduced by 5%"
    assert res.json()["amount_awarded"] == 396.76


def test_delete_decision(client, auth_headers):
    create_res = _create_decision(client, auth_headers)
    decision_id = create_res.json()["id"]

    res = client.delete(f"/api/decisions/{decision_id}", headers=auth_headers)
    assert res.status_code == 200

    res = client.get(f"/api/decisions/{decision_id}")
    assert res.status_code == 404


def test_delete_requires_admin(client, auth_headers):
    create_res = _create_decision(client, auth_headers)
    decision_id = create_res.json()["id"]

    res = client.delete(f"/api/decisions/{decision_id}")
    assert res.status_code == 401
