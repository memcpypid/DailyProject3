def test_default_sources_seeded_for_provisioned_user(client, auth_headers):
    res = client.get("/api/v1/sources", headers=auth_headers)
    assert res.status_code == 200
    names = {s["name"] for s in res.json()["data"]}
    assert "LinkedIn" in names
    assert "Instagram" in names
    assert "Facebook" in names
    assert "TikTok" in names
    assert len(names) == 6


def test_create_update_delete_source(client, auth_headers):
    created = client.post(
        "/api/v1/sources",
        json={"name": "Threads", "access_type": "Pencarian publik terbatas", "weight": 0.3},
        headers=auth_headers,
    )
    assert created.status_code == 201
    source_id = created.json()["data"]["id"]

    updated = client.put(
        f"/api/v1/sources/{source_id}", json={"weight": 0.5, "enabled": False}, headers=auth_headers
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["weight"] == 0.5
    assert updated.json()["data"]["enabled"] is False

    deleted = client.delete(f"/api/v1/sources/{source_id}", headers=auth_headers)
    assert deleted.status_code == 200


def test_invalid_weight_rejected(client, auth_headers):
    res = client.post(
        "/api/v1/sources", json={"name": "Bad", "weight": 1.5}, headers=auth_headers
    )
    assert res.status_code == 422
