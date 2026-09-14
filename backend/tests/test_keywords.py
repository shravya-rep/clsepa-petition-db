def test_list_keywords_public(client, sample_keywords):
    res = client.get("/api/keywords/")
    assert res.status_code == 200
    assert len(res.json()) == 5


def test_create_keyword_requires_auth(client):
    res = client.post("/api/keywords/", json={"name": "Pest"})
    assert res.status_code == 401


def test_create_keyword_as_admin(client, auth_headers):
    res = client.post("/api/keywords/", json={"name": "Pest Control"}, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Pest Control"


def test_create_duplicate_keyword(client, auth_headers):
    client.post("/api/keywords/", json={"name": "Mold"}, headers=auth_headers)
    res = client.post("/api/keywords/", json={"name": "Mold"}, headers=auth_headers)
    assert res.status_code == 400


def test_delete_keyword(client, auth_headers, sample_keywords):
    kw_id = sample_keywords[0][0]
    res = client.delete(f"/api/keywords/{kw_id}", headers=auth_headers)
    assert res.status_code == 200

    remaining = client.get("/api/keywords/").json()
    assert len(remaining) == 4
