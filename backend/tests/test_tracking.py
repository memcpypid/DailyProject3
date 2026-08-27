from tests.test_alumni import create_alumni


def _first_source_id(client, headers):
    sources = client.get("/api/v1/sources", headers=headers).json()["data"]
    return sources[0]["id"]


def test_add_manual_candidate_confirms_identity(client, auth_headers):
    alumni_id = create_alumni(client, auth_headers).json()["data"]["id"]
    source_id = _first_source_id(client, auth_headers)

    res = client.post(
        f"/api/v1/alumni/{alumni_id}/candidates/manual",
        json={
            "source_id": source_id,
            "raw_name": "Muhammad Rizky",
            "linkedin_url": "https://linkedin.com/in/mrizky",
            "employer_name": "PT Contoh Sejahtera",
            "position": "Software Engineer",
        },
        headers=auth_headers,
    )
    assert res.status_code == 201
    candidate = res.json()["data"]
    assert candidate["linkedin_url"] == "https://linkedin.com/in/mrizky"

    detail = client.get(f"/api/v1/alumni/{alumni_id}", headers=auth_headers).json()["data"]
    assert detail["status"] == "TERVERIFIKASI_MANUAL"
    assert detail["confirmed_candidate_id"] == candidate["id"]
    assert detail["confirmed_profile"]["employer_name"] == "PT Contoh Sejahtera"
    assert detail["last_verified_at"] is not None


def test_latest_manual_candidate_wins_confirmation(client, auth_headers):
    alumni_id = create_alumni(client, auth_headers).json()["data"]["id"]
    source_id = _first_source_id(client, auth_headers)

    first = client.post(
        f"/api/v1/alumni/{alumni_id}/candidates/manual",
        json={"source_id": source_id, "raw_name": "Kandidat Pertama"},
        headers=auth_headers,
    ).json()["data"]
    second = client.post(
        f"/api/v1/alumni/{alumni_id}/candidates/manual",
        json={"source_id": source_id, "raw_name": "Kandidat Kedua"},
        headers=auth_headers,
    ).json()["data"]

    detail = client.get(f"/api/v1/alumni/{alumni_id}", headers=auth_headers).json()["data"]
    assert detail["confirmed_candidate_id"] == second["id"]

    candidates = client.get(f"/api/v1/alumni/{alumni_id}/candidates", headers=auth_headers).json()["data"]
    ids = {c["id"] for c in candidates}
    assert ids == {first["id"], second["id"]}


def test_manual_candidate_requires_valid_alumni_and_source(client, auth_headers):
    missing_alumni = client.post(
        "/api/v1/alumni/does-not-exist/candidates/manual",
        json={"source_id": "also-missing"},
        headers=auth_headers,
    )
    assert missing_alumni.status_code == 404

    alumni_id = create_alumni(client, auth_headers).json()["data"]["id"]
    missing_source = client.post(
        f"/api/v1/alumni/{alumni_id}/candidates/manual",
        json={"source_id": "does-not-exist"},
        headers=auth_headers,
    )
    assert missing_source.status_code == 404
