def test_register_and_login(client):
    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Darma", "email": "darma@test.com", "password": "secret123"},
    )
    assert res.status_code == 201
    assert res.json()["data"]["email"] == "darma@test.com"
    assert "password" not in res.json()["data"]

    res = client.post(
        "/api/v1/auth/login", json={"email": "darma@test.com", "password": "secret123"}
    )
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user"]["email"] == "darma@test.com"


def test_login_wrong_password_returns_401(client):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Darma", "email": "darma@test.com", "password": "secret123"},
    )
    res = client.post(
        "/api/v1/auth/login", json={"email": "darma@test.com", "password": "wrong"}
    )
    assert res.status_code == 401


def test_duplicate_email_register_returns_409(client):
    payload = {"name": "Darma", "email": "darma@test.com", "password": "secret123"}
    client.post("/api/v1/auth/register", json=payload)
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 409


def test_protected_route_requires_token(client):
    res = client.get("/api/v1/users/me")
    assert res.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    res = client.get("/api/v1/users/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["email"] == "darma@test.com"


def test_refresh_rotates_token_and_old_one_is_revoked(client):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Darma", "email": "darma@test.com", "password": "secret123"},
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": "darma@test.com", "password": "secret123"}
    ).json()["data"]

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert refreshed.status_code == 200

    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert reused.status_code == 401


def test_logout_revokes_refresh_token(client, auth_headers):
    login = client.post(
        "/api/v1/auth/login", json={"email": "darma@test.com", "password": "secret123"}
    ).json()["data"]

    logout_res = client.post("/api/v1/auth/logout", json={"refresh_token": login["refresh_token"]})
    assert logout_res.status_code == 200

    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert reuse.status_code == 401
