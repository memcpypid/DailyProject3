"""Pencarian web berbantuan manusia ("Cari di Internet").

Modul ini benar-benar memanggil mesin pencari sungguhan (lewat SerpApi) untuk
SATU alumni yang sedang dibuka periset - bukan pipeline otomatis untuk
banyak/semua alumni sekaligus. Hasil
pencarian hanya DITAMPILKAN ke periset; tidak ada apa pun yang tersimpan ke
database dari modul ini. Periset yang membaca hasilnya dan memutuskan sendiri
data mana yang benar sebelum menyimpannya lewat endpoint input manual yang
sudah ada (`POST /alumni/{id}/candidates/manual`).

Daftar Sumber Data (nama & bobot kepercayaan yang diatur periset di halaman
"Sumber Data") sungguhan dipakai di sini untuk membangun query - bukan
sekadar tampilan: sumber dengan domain platform yang dikenal (LinkedIn,
Instagram, Facebook, TikTok) dibatasi lewat `site:`, dan bobot menentukan
sumber mana yang diprioritaskan saat jumlah query dibatasi.
"""

import httpx

from app.core.config import get_settings
from app.infrastructure.models import Source

settings = get_settings()

SOURCE_DOMAINS = {
    "linkedin": "linkedin.com",
    "instagram": "instagram.com",
    "facebook": "facebook.com",
    "tiktok": "tiktok.com",
}

MAX_QUERIES = 4
RESULTS_PER_QUERY = 6


class WebSearchUnavailable(RuntimeError):
    """SERPAPI_KEY belum diatur, atau SerpApi gagal merespons."""


def _domain_for(source_name: str) -> str | None:
    lowered = source_name.lower()
    for keyword, domain in SOURCE_DOMAINS.items():
        if keyword in lowered:
            return domain
    return None


def _build_queries(full_name: str, extra_context: str, sources: list[Source]) -> list[tuple[str, str]]:
    """Bangun daftar (nama_sumber, query) terurut dari bobot kepercayaan tertinggi.

    Sumber dengan domain dikenal dibatasi lewat `site:`. Sumber lain (mis.
    "Situs Perusahaan/Berita", "Mesin Pencari Umum", atau sumber custom
    buatan periset) berbagi satu query umum - dipilih dari sumber ber-bobot
    tertinggi di antara mereka, supaya tidak ada dua query identik yang
    dikirim dua kali ke SerpApi.
    """
    base = f'"{full_name}" {extra_context}'.strip()
    queries: list[tuple[str, str]] = []
    generic_added = False
    for source in sorted(sources, key=lambda s: s.weight, reverse=True):
        if len(queries) >= MAX_QUERIES:
            break
        domain = _domain_for(source.name)
        if domain:
            queries.append((source.name, f"site:{domain} {base}"))
        elif not generic_added:
            queries.append((source.name, base))
            generic_added = True
    if not queries:
        queries.append(("Mesin Pencari Umum", base))
    return queries


def search_alumni(full_name: str, extra_context: str, sources: list[Source]) -> list[dict]:
    if not settings.SERPAPI_KEY:
        raise WebSearchUnavailable(
            "Fitur pencarian web belum aktif - atur SERPAPI_KEY di file .env backend "
            "(lihat SERPAPI_KEY di .env.example)."
        )

    results: list[dict] = []
    seen_links: set[str] = set()
    last_error: httpx.HTTPError | None = None

    for source_name, query in _build_queries(full_name, extra_context, sources):
        try:
            response = httpx.get(
                settings.SERPAPI_BASE_URL,
                params={"q": query, "api_key": settings.SERPAPI_KEY, "num": RESULTS_PER_QUERY},
                timeout=10.0,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            last_error = exc
            continue

        for item in payload.get("organic_results", []):
            link = item.get("link", "")
            if not link or link in seen_links:
                continue
            seen_links.add(link)
            results.append(
                {
                    "title": item.get("title", ""),
                    "link": link,
                    "snippet": item.get("snippet", ""),
                    "source": item.get("source", ""),
                    "queried_source": source_name,
                }
            )

    if not results and last_error is not None:
        raise WebSearchUnavailable(f"Gagal menghubungi layanan pencarian: {last_error}") from last_error

    return results
