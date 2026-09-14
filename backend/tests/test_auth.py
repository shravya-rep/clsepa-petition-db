def test_login_success(client, admin_token):
    assert admin_token is not None
    assert len(admin_token) > 0


def test_login_wrong_password(client):
    res = client.post("/api/auth/login", data={"username": "admin@clsepa.org", "password": "wrong"})
    assert res.status_code == 401


def test_login_nonexistent_user(client):
    res = client.post("/api/auth/login", data={"username": "nobody@test.com", "password": "pass"})
    assert res.status_code == 401


def test_register_requires_admin(client):
    res = client.post("/api/auth/register", json={
        "email": "new@clsepa.org", "password": "pass123", "full_name": "New User"
    })
    assert res.status_code == 401


def test_register_as_admin(client, auth_headers):
    res = client.post("/api/auth/register", json={
        "email": "staff@clsepa.org", "password": "pass123", "full_name": "Staff User"
    }, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "staff@clsepa.org"


def test_register_duplicate_email(client, auth_headers):
    client.post("/api/auth/register", json={
        "email": "dup@clsepa.org", "password": "pass123"
    }, headers=auth_headers)
    res = client.post("/api/auth/register", json={
        "email": "dup@clsepa.org", "password": "pass123"
    }, headers=auth_headers)
    assert res.status_code == 400
