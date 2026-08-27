from types import SimpleNamespace

from app.services import websearch_service


def create_alumni(client, headers, **overrides):
    payload = {
        "full_name": "Muhammad Rizky",
        "nim": "201910370001",
        "tahun_masuk": 2016,
        "tanggal_lulus": "2020-07-01",
        "fakultas": "Teknik",
        "program_studi": "Informatika",
        "name_variations": [],
    }
    payload.update(overrides)
    return client.post("/api/v1/alumni", json=payload, headers=headers).json()["data"]


def test_search_web_without_api_key_returns_clear_error(client, auth_headers, monkeypatch):
    monkeypatch.setattr("app.services.websearch_service.settings.SERPAPI_KEY", "")

    alumni = create_alumni(client, auth_headers)
    res = client.get(f"/api/v1/alumni/{alumni['id']}/search-web", headers=auth_headers)
    assert res.status_code == 400
    assert "SERPAPI_KEY" in res.json()["detail"]


def test_search_web_returns_results_for_human_review(client, auth_headers, monkeypatch):
    monkeypatch.setattr("app.services.websearch_service.settings.SERPAPI_KEY", "fake-key")

    def fake_search_alumni(full_name, extra_context, sources):
        return [
            {
                "title": f"{full_name} - LinkedIn",
                "link": "https://linkedin.com/in/muhammad-rizky",
                "snippet": "Software Engineer at PT Contoh",
                "source": "linkedin.com",
                "queried_source": "LinkedIn",
            }
        ]

    monkeypatch.setattr(websearch_service, "search_alumni", fake_search_alumni)

    alumni = create_alumni(client, auth_headers)
    res = client.get(f"/api/v1/alumni/{alumni['id']}/search-web", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["link"] == "https://linkedin.com/in/muhammad-rizky"

    # Hasil pencarian tidak otomatis tersimpan sebagai kandidat.
    candidates = client.get(f"/api/v1/alumni/{alumni['id']}/candidates", headers=auth_headers).json()["data"]
    assert candidates == []


def test_search_web_unknown_alumni_returns_404(client, auth_headers):
    res = client.get("/api/v1/alumni/does-not-exist/search-web", headers=auth_headers)
    assert res.status_code == 404


def test_search_alumni_uses_source_name_and_weight_to_build_queries(monkeypatch):
    """Nama sumber & bobot kepercayaan sungguhan memengaruhi query ke SerpApi -
    bukan sekadar tampilan di halaman "Sumber Data"."""
    monkeypatch.setattr(websearch_service.settings, "SERPAPI_KEY", "fake-key")

    sources = [
        SimpleNamespace(name="TikTok", weight=0.4),
        SimpleNamespace(name="LinkedIn", weight=0.9),
        SimpleNamespace(name="Mesin Pencari Umum", weight=0.4),
        SimpleNamespace(name="Situs Perusahaan / Berita", weight=0.7),
    ]

    captured = []

    class FakeResponse:
        def __init__(self, link):
            self._link = link

        def raise_for_status(self):
            return None

        def json(self):
            return {"organic_results": [{"title": "t", "link": self._link, "snippet": "s", "source": "x"}]}

    def fake_get(url, params, timeout):
        captured.append(params["q"])
        return FakeResponse(f"https://example.test/{len(captured)}")

    monkeypatch.setattr(websearch_service.httpx, "get", fake_get)

    results = websearch_service.search_alumni("Budi Santoso", "Informatika", sources)

    # Sumber ber-bobot tertinggi (LinkedIn) dipakai lebih dulu, dengan site: filter.
    assert captured[0] == 'site:linkedin.com "Budi Santoso" Informatika'
    assert results[0]["queried_source"] == "LinkedIn"

    # Sumber tanpa domain dikenal (Situs Perusahaan/Berita, Mesin Pencari Umum) hanya
    # menghasilkan SATU query umum (tidak dipanggil dua kali ke SerpApi).
    generic_queries = [q for q in captured if q == '"Budi Santoso" Informatika']
    assert len(generic_queries) == 1

    # TikTok (bobot terendah) tetap kebagian slot karena total sumber di bawah batas.
    assert 'site:tiktok.com "Budi Santoso" Informatika' in captured


def test_search_alumni_caps_total_queries_by_weight(monkeypatch):
    """Saat sumber lebih banyak dari batas, sumber ber-bobot terendah yang dikorbankan."""
    monkeypatch.setattr(websearch_service.settings, "SERPAPI_KEY", "fake-key")

    sources = [
        SimpleNamespace(name="LinkedIn", weight=0.9),
        SimpleNamespace(name="Instagram", weight=0.8),
        SimpleNamespace(name="Facebook", weight=0.7),
        SimpleNamespace(name="TikTok", weight=0.6),
        SimpleNamespace(name="Situs Perusahaan / Berita", weight=0.1),
    ]

    captured = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"organic_results": []}

    def fake_get(url, params, timeout):
        captured.append(params["q"])
        return FakeResponse()

    monkeypatch.setattr(websearch_service.httpx, "get", fake_get)

    websearch_service.search_alumni("Budi Santoso", "", sources)

    assert len(captured) == websearch_service.MAX_QUERIES
    assert not any("Situs Perusahaan" in q or '"Budi Santoso"' == q for q in captured)
