import io

import pandas as pd
import pytest


def _make_xlsx(rows: list[dict]) -> bytes:
    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    return buffer.getvalue()


SAMPLE_ROWS = [
    {
        "Nama Lulusan": "Catur Rahmani Oktavia",
        "NIM": "95620625",
        "Tahun Masuk": 1995,
        "Tanggal Lulus": "1 Juli 2000",
        "Fakultas": "Ekonomi",
        "Program Studi": "Akuntansi",
    },
    {
        "Nama Lulusan": "Indayati",
        "NIM": "95620626",
        "Tahun Masuk": 1995,
        "Tanggal Lulus": "1 Juli 2000",
        "Fakultas": "Ekonomi",
        "Program Studi": "Akuntansi",
    },
]


def test_import_creates_alumni_from_xlsx(client, auth_headers):
    content = _make_xlsx(SAMPLE_ROWS)
    res = client.post(
        "/api/v1/alumni/import",
        files={"file": ("alumni.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_rows"] == 2
    assert data["created"] == 2
    assert data["skipped_duplicate"] == 0

    listing = client.get("/api/v1/alumni?limit=10", headers=auth_headers).json()["data"]
    assert listing["pagination"]["total"] == 2
    names = {a["full_name"] for a in listing["alumni"]}
    assert names == {"Catur Rahmani Oktavia", "Indayati"}
    tanggal = {a["tanggal_lulus"] for a in listing["alumni"]}
    assert tanggal == {"2000-07-01"}  # parsing "1 Juli 2000" berhasil


def test_import_is_idempotent_by_nim(client, auth_headers):
    content = _make_xlsx(SAMPLE_ROWS)
    client.post(
        "/api/v1/alumni/import",
        files={"file": ("alumni.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    res2 = client.post(
        "/api/v1/alumni/import",
        files={"file": ("alumni.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    data = res2.json()["data"]
    assert data["created"] == 0
    assert data["skipped_duplicate"] == 2
    assert data["skipped_duplicate_in_db"] == 2
    assert data["skipped_duplicate_in_file"] == 0


def test_import_detects_duplicate_nim_within_same_file(client, auth_headers):
    rows = SAMPLE_ROWS + [dict(SAMPLE_ROWS[0])]  # NIM 95620625 muncul dua kali di file yang sama
    content = _make_xlsx(rows)
    res = client.post(
        "/api/v1/alumni/import",
        files={"file": ("alumni.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    data = res.json()["data"]
    assert data["created"] == 2
    assert data["skipped_duplicate"] == 1
    assert data["skipped_duplicate_in_file"] == 1
    assert data["skipped_duplicate_in_db"] == 0
    assert any("duplikat di file" in err for err in data["errors"])


def test_import_dry_run_does_not_persist(client, auth_headers):
    content = _make_xlsx(SAMPLE_ROWS)
    res = client.post(
        "/api/v1/alumni/import?dry_run=true",
        files={"file": ("alumni.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert res.json()["data"]["created"] == 2

    listing = client.get("/api/v1/alumni", headers=auth_headers).json()["data"]
    assert listing["pagination"]["total"] == 0


def test_import_respects_limit(client, auth_headers):
    content = _make_xlsx(SAMPLE_ROWS)
    res = client.post(
        "/api/v1/alumni/import?limit=1",
        files={"file": ("alumni.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    data = res.json()["data"]
    assert data["total_rows"] == 1
    assert data["created"] == 1


def test_import_rejects_missing_columns(client, auth_headers):
    content = _make_xlsx([{"Nama Lulusan": "Tanpa NIM"}])
    res = client.post(
        "/api/v1/alumni/import",
        files={"file": ("alumni.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert res.status_code == 400
    assert "Kolom" in res.json()["detail"]


def test_import_rejects_unsupported_extension(client, auth_headers):
    res = client.post(
        "/api/v1/alumni/import",
        files={"file": ("alumni.txt", b"hello", "text/plain")},
        headers=auth_headers,
    )
    assert res.status_code == 400


def test_import_requires_auth(client):
    content = _make_xlsx(SAMPLE_ROWS)
    res = client.post(
        "/api/v1/alumni/import",
        files={"file": ("alumni.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert res.status_code == 401


def test_import_skips_rows_with_missing_name_or_nim(client, auth_headers):
    rows = SAMPLE_ROWS + [
        {
            "Nama Lulusan": None,
            "NIM": "999",
            "Tahun Masuk": 2000,
            "Tanggal Lulus": "1 Juli 2004",
            "Fakultas": "Teknik",
            "Program Studi": "Sipil",
        }
    ]
    content = _make_xlsx(rows)
    res = client.post(
        "/api/v1/alumni/import",
        files={"file": ("alumni.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    data = res.json()["data"]
    assert data["created"] == 2
    assert data["skipped_invalid"] == 1
    assert len(data["errors"]) == 1
