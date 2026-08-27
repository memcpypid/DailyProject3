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

MAX_QUERIES = 8
RESULTS_PER_QUERY = 6


class WebSearchUnavailable(RuntimeError):
    """SERPAPI_KEY belum diatur, atau SerpApi gagal merespons."""


def _domain_for(source_name: str) -> str | None:
    lowered = source_name.lower()
    for keyword, domain in SOURCE_DOMAINS.items():
        if keyword in lowered:
            return domain
    return None


def _quoted(value) -> str:
    value = str(value or "").strip()
    return f'"{value}"' if value else ""


def _build_queries(alumni: dict, sources: list[Source]) -> list[tuple[str, str, str]]:
    """Bangun query terarah untuk delapan kelompok data Daily Project 4.

    Keenam data induk dipakai sebagai konteks identitas di seluruh rangkaian query.
    Query sengaja tidak dibuat terlalu ketat: nama selalu wajib, sedangkan NIM,
    tahun, fakultas, dan program studi dibagi ke query verifikasi/kontak/pekerjaan
    agar hasil publik yang tidak mencantumkan seluruh atribut masih dapat ditemukan.
    """
    full_name = _quoted(alumni.get("full_name"))
    nim = _quoted(alumni.get("nim"))
    tahun_masuk = _quoted(alumni.get("tahun_masuk"))
    tanggal_lulus = _quoted(alumni.get("tanggal_lulus"))
    fakultas = _quoted(alumni.get("fakultas"))
    program_studi = _quoted(alumni.get("program_studi"))
    academic_context = " ".join(term for term in (program_studi, fakultas) if term)
    compact_context = program_studi or fakultas

    queries: list[tuple[str, str, str]] = []
    generic_sources: list[Source] = []
    for source in sorted(sources, key=lambda s: s.weight, reverse=True):
        domain = _domain_for(source.name)
        if domain:
            queries.append(
                (source.name, f"site:{domain} {full_name} {compact_context}".strip(), "Alamat sosial media")
            )
        else:
            generic_sources.append(source)

    generic_name = generic_sources[0].name if generic_sources else "Mesin Pencari Umum"
    targeted = [
        (
            generic_name,
            " ".join(term for term in (full_name, nim, tahun_masuk, tanggal_lulus, academic_context) if term),
            "Verifikasi identitas alumni",
        ),
        (
            generic_name,
            f'{full_name} {compact_context} (email OR "nomor HP" OR telepon OR WhatsApp)'.strip(),
            "Email dan nomor HP",
        ),
        (
            generic_name,
            f'{full_name} {compact_context} (bekerja OR perusahaan OR instansi OR employer)'.strip(),
            "Tempat dan alamat bekerja",
        ),
        (
            generic_name,
            f'{full_name} {compact_context} (jabatan OR posisi OR position OR PNS OR swasta OR wirausaha)'.strip(),
            "Posisi dan jenis pekerjaan",
        ),
        (
            generic_name,
            f'{full_name} {compact_context} (perusahaan OR instansi) (LinkedIn OR Instagram OR Facebook)'.strip(),
            "Sosial media tempat bekerja",
        ),
    ]
    queries.extend(targeted)

    # Hindari query kosong/duplikat dan batasi biaya panggilan SerpApi.
    unique: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for item in queries:
        if item[1] and item[1] not in seen:
            seen.add(item[1])
            unique.append(item)
    return unique[:MAX_QUERIES]


def search_alumni(alumni: dict, sources: list[Source]) -> list[dict]:
    if not settings.SERPAPI_KEY:
        raise WebSearchUnavailable(
            "Fitur pencarian web belum aktif - atur SERPAPI_KEY di file .env backend "
            "(lihat SERPAPI_KEY di .env.example)."
        )

    results: list[dict] = []
    seen_links: set[str] = set()
    last_error: httpx.HTTPError | None = None

    for source_name, query, target_data in _build_queries(alumni, sources):
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
                    "target_data": target_data,
                    "query": query,
                }
            )

    if not results and last_error is not None:
        raise WebSearchUnavailable(f"Gagal menghubungi layanan pencarian: {last_error}") from last_error

    return results
