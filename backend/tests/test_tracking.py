from tests.test_alumni import create_alumni


def _first_source_id(client, headers):
    sources = client.get("/api/v1/sources", headers=headers).json()["data"]
    return sources[0]["id"]


def test_add_manual_candidate_is_scored_then_can_be_confirmed(client, auth_headers):
    alumni_id = create_alumni(client, auth_headers).json()["data"]["id"]
    source_id = _first_source_id(client, auth_headers)

    res = client.post(
        f"/api/v1/alumni/{alumni_id}/candidates/manual",
        json={
            "source_id": source_id,
            "raw_name": "Muhammad Rizky",
            "linkedin_url": "https://linkedin.com/in/mrizky",
            "instagram_url": "https://instagram.com/mrizky",
            "facebook_url": "https://facebook.com/mrizky",
            "tiktok_url": "https://tiktok.com/@mrizky",
            "email": "rizky@example.com",
            "phone": "081234567890",
            "employer_name": "PT Contoh Sejahtera",
            "employer_address": "Jl. Contoh No. 1, Malang",
            "position": "Software Engineer",
            "employment_type": "Swasta",
            "employer_social_media": "https://instagram.com/ptcontoh",
        },
        headers=auth_headers,
    )
    assert res.status_code == 201
    candidate = res.json()["data"]
    assert candidate["linkedin_url"] == "https://linkedin.com/in/mrizky"
    assert candidate["instagram_url"] == "https://instagram.com/mrizky"
    assert candidate["facebook_url"] == "https://facebook.com/mrizky"
    assert candidate["tiktok_url"] == "https://tiktok.com/@mrizky"
    assert candidate["email"] == "rizky@example.com"
    assert candidate["phone"] == "081234567890"
    assert candidate["employer_address"] == "Jl. Contoh No. 1, Malang"
    assert candidate["employment_type"] == "Swasta"
    assert candidate["employer_social_media"] == "https://instagram.com/ptcontoh"

    detail = client.get(f"/api/v1/alumni/{alumni_id}", headers=auth_headers).json()["data"]
    assert candidate["name_score"] == 100
    assert 0 <= candidate["match_score"] <= 100

    review = client.post(
        f"/api/v1/alumni/{alumni_id}/candidates/{candidate['id']}/review",
        json={"decision": "ACCEPT"}, headers=auth_headers,
    )
    assert review.status_code == 200
    detail = client.get(f"/api/v1/alumni/{alumni_id}", headers=auth_headers).json()["data"]
    assert detail["status"] == "TERVERIFIKASI_MANUAL"
    assert detail["confirmed_candidate_id"] == candidate["id"]
    assert detail["confirmed_profile"]["employer_name"] == "PT Contoh Sejahtera"
    assert detail["last_verified_at"] is not None


def test_manual_review_decision_controls_confirmation(client, auth_headers):
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

    client.post(f"/api/v1/alumni/{alumni_id}/candidates/{first['id']}/review",
                json={"decision": "ACCEPT"}, headers=auth_headers)
    client.post(f"/api/v1/alumni/{alumni_id}/candidates/{second['id']}/review",
                json={"decision": "REJECT"}, headers=auth_headers)
    detail = client.get(f"/api/v1/alumni/{alumni_id}", headers=auth_headers).json()["data"]
    assert detail["status"] == "TIDAK_DITEMUKAN"
    assert detail["confirmed_candidate_id"] is None

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


def test_cross_source_evidence_raises_fused_score(client, auth_headers):
    alumni_id = create_alumni(client, auth_headers).json()["data"]["id"]
    sources = client.get("/api/v1/sources", headers=auth_headers).json()["data"]
    first = client.post(
        f"/api/v1/alumni/{alumni_id}/candidates/manual",
        json={"source_id": sources[0]["id"], "raw_name": "Muhammad Rizky", "email": "rizky@example.com"},
        headers=auth_headers,
    ).json()["data"]
    second = client.post(
        f"/api/v1/alumni/{alumni_id}/candidates/manual",
        json={"source_id": sources[1]["id"], "raw_name": "Muhammad Rizky", "email": "rizky@example.com"},
        headers=auth_headers,
    ).json()["data"]
    assert second["evidence_count"] == 2
    base_score = (
        second["name_score"] * 0.40
        + second["affiliation_score"] * 0.30
        + second["timeline_score"] * 0.15
        + second["field_score"] * 0.15
    )
    assert second["match_score"] == round(base_score + 5, 2)
