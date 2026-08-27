def create_alumni(client, headers, **overrides):
    payload = {
        "full_name": "Muhammad Rizky",
        "nim": "201910370001",
        "tahun_masuk": 2016,
        "tanggal_lulus": "2020-07-01",
        "fakultas": "Teknik",
        "program_studi": "Informatika",
        "name_variations": ["M. Rizky", "Rizky M."],
    }
    payload.update(overrides)
    return client.post("/api/v1/alumni", json=payload, headers=headers)


def test_create_and_get_alumni(client, auth_headers):
    res = create_alumni(client, auth_headers)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["status"] == "BELUM_DILACAK"
    assert data["name_variations"] == ["M. Rizky", "Rizky M."]

    detail = client.get(f"/api/v1/alumni/{data['id']}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["full_name"] == "Muhammad Rizky"


def test_list_alumni_pagination(client, auth_headers):
    for i in range(3):
        create_alumni(client, auth_headers, full_name=f"Alumni {i}", nim=f"20191037000{i}")

    res = client.get("/api/v1/alumni?page=1&limit=2", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()["data"]
    assert len(body["alumni"]) == 2
    assert body["pagination"]["total"] == 3
    assert body["pagination"]["has_next"] is True


def test_update_and_delete_alumni(client, auth_headers):
    alumni_id = create_alumni(client, auth_headers).json()["data"]["id"]

    upd = client.put(
        f"/api/v1/alumni/{alumni_id}", json={"fakultas": "Ekonomi dan Bisnis"}, headers=auth_headers
    )
    assert upd.status_code == 200
    assert upd.json()["data"]["fakultas"] == "Ekonomi dan Bisnis"

    delete = client.delete(f"/api/v1/alumni/{alumni_id}", headers=auth_headers)
    assert delete.status_code == 200

    missing = client.get(f"/api/v1/alumni/{alumni_id}", headers=auth_headers)
    assert missing.status_code == 404


def test_alumni_isolated_per_account(client):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Owner A", "email": "a@test.com", "password": "secret123"},
    )
    token_a = client.post(
        "/api/v1/auth/login", json={"email": "a@test.com", "password": "secret123"}
    ).json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    client.post(
        "/api/v1/auth/register",
        json={"name": "Owner B", "email": "b@test.com", "password": "secret123"},
    )
    token_b = client.post(
        "/api/v1/auth/login", json={"email": "b@test.com", "password": "secret123"}
    ).json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    alumni_id = create_alumni(client, headers_a).json()["data"]["id"]

    # Account B must not see account A's alumni, nor A's seeded sources
    forbidden = client.get(f"/api/v1/alumni/{alumni_id}", headers=headers_b)
    assert forbidden.status_code == 404

    list_b = client.get("/api/v1/alumni", headers=headers_b)
    assert list_b.json()["data"]["pagination"]["total"] == 0

    sources_a = client.get("/api/v1/sources", headers=headers_a).json()["data"]
    sources_b = client.get("/api/v1/sources", headers=headers_b).json()["data"]
    ids_a = {s["id"] for s in sources_a}
    ids_b = {s["id"] for s in sources_b}
    assert ids_a.isdisjoint(ids_b)
