# Backend - Sistem Pelacakan Alumni

FastAPI + SQLite, mengimplementasikan pseudocode & use case diagram dari Daily Project 2,
dengan skema data alumni yang disesuaikan dengan roster resmi kampus (Daily Project 4).
Autentikasi JWT (access + refresh token, tanpa role) - setiap akun hanya mengelola data
alumni miliknya sendiri.

## Menjalankan

```bash
cd backend
source venv/bin/activate      # venv sudah tersedia di folder ini
pip install -r requirements.txt
cp .env.example .env          # opsional, nilai default sudah masuk akal untuk lokal
uvicorn app.main:app --reload --port 8000
```

Dokumentasi interaktif: http://127.0.0.1:8000/docs

## Menjalankan test

```bash
source venv/bin/activate
python -m pytest -q
```

## Arsitektur (clean architecture, layered)

```
app/
  core/            # config (pydantic-settings) & security (JWT, bcrypt)
  infrastructure/  # SQLAlchemy engine/session & ORM models (persistence)
  repositories/    # akses data per entity, satu-satunya lapisan yang bicara ke ORM
  services/        # use case / business logic - tidak tahu apa-apa soal HTTP
  schemas/         # Pydantic request/response (kontrak I/O API)
  api/v1/          # routing FastAPI - tipis, delegasikan semua logika ke services/
scripts/
  import_alumni.py # impor roster alumni (xlsx/csv) ke akun tertentu
```

Alur ketergantungan satu arah: `api -> services -> repositories -> infrastructure`.
Router tidak pernah menyentuh ORM/session langsung, dan services tidak tahu soal FastAPI/HTTP.

## Skema data alumni (Daily Project 4)

**Data induk** (`Alumni`) - mengikuti kolom roster resmi kampus persis:
`full_name` (Nama Lulusan), `nim`, `tahun_masuk`, `tanggal_lulus`, `fakultas`, `program_studi`.

**Data hasil pelacakan** (`Candidate`) - 8 data target sesuai README Daily Project 4:
`linkedin_url`, `instagram_url`, `facebook_url`, `tiktok_url` (1. sosial media),
`email` (2), `phone` (3), `employer_name` (4. tempat bekerja), `employer_address` (5),
`position` (6), `employment_type` (7. PNS/Swasta/Wirausaha), `employer_social_media` (8).

Setiap `Candidate` adalah temuan hasil riset manual periset (lewat
`POST /alumni/{id}/candidates/manual`) - tidak ada data yang masuk ke tabel ini
lewat proses otomatis apa pun.

### Konfirmasi identitas: "yang terbaru menang"

Sistem tidak melakukan skoring/fusi otomatis. Setiap kali periset menyimpan
kandidat manual baru untuk seorang alumni, kandidat itu langsung menjadi
`Alumni.confirmed_candidate_id` dan status berubah jadi `TERVERIFIKASI_MANUAL`
- menimpa konfirmasi sebelumnya (lihat `tracking_service.add_manual_candidate`).
`confirmed_candidate_id` **bukan duplikasi kolom**, melainkan foreign key ke
`candidates.id` (relasi timbal balik dengan `Candidate.alumni_id`, ditangani
via `post_update=True` di `models.py` karena kedua tabel saling mereferensikan).

Response `GET /api/v1/alumni/{id}` menyertakan `confirmed_candidate_id` dan
`confirmed_profile` (objek kandidat lengkap yang sudah di-resolve) sehingga
pengguna langsung melihat data identitas yang ditemukan pada profil alumni,
tanpa perlu menelusuri daftar kandidat mentah satu per satu. Seluruh kandidat
mentah (termasuk yang tidak terpilih) tetap tersimpan apa adanya di tabel
`candidates` sebagai opsi/riwayat hasil pencarian.

## Impor roster alumni

Data induk (nama/NIM/fakultas/dst.) dari file Excel kampus bisa diimpor langsung -
ini data direktori, bukan hasil pencarian, jadi aman diimpor apa adanya (tetap
tersimpan lokal per akun, tidak pernah dikirim ke luar):

```bash
source venv/bin/activate
python scripts/import_alumni.py --file /path/ke/Alumni.xlsx --email admin@kampus.ac.id --dry-run
python scripts/import_alumni.py --file /path/ke/Alumni.xlsx --email admin@kampus.ac.id
```

Kolom file harus persis: `Nama Lulusan | NIM | Tahun Masuk | Tanggal Lulus | Fakultas | Program Studi`.
Idempotent (baris dengan NIM yang sudah ada di akun tsb dilewati), dan mendukung
`--limit N` untuk uji coba pada sebagian data dulu.

## Catatan jujur soal "Eksekusi Pencarian Multi-Sumber"

Mengambil data sungguhan (sosial media/email/no HP/tempat kerja/dst.) dari LinkedIn/IG/
FB/TikTok memerlukan API resmi berbayar atau kredensial partner dan tunduk pada ToS
masing-masing platform. **Sistem ini secara sengaja TIDAK melakukan pengumpulan data
pribadi otomatis-massal terhadap orang yang bisa diidentifikasi** - ini batas yang
dipegang terlepas dari tujuan pembelajaran/penelitian, karena menyangkut data pribadi
orang sungguhan yang tidak memberi persetujuan untuk diproses dengan cara ini.

Sebelumnya proyek ini punya simulator (`fetch_service.py`) beserta pipeline skoring/
fusi/antrean tinjauan otomatis untuk mendemonstrasikan use case "Eksekusi Pencarian
Multi-Sumber" dari Daily Project 2 tanpa menyentuh data pribadi sungguhan. Simulator
dan seluruh pipeline itu (skoring, fusi bukti, batch tracking, antrean tinjauan) sudah
**dihapus sepenuhnya** dari kode - bukan lagi bagian dari sistem ini, supaya tidak ada
kode yang menyerupai infrastruktur pengumpulan data massal tersisa di repo, sekalipun
hanya untuk skala simulasi. Satu-satunya jalur data sekarang adalah input manual satu
per satu.

**Satu-satunya cara data masuk**: `POST /api/v1/alumni/{id}/candidates/manual`, setelah
periset benar-benar memverifikasi temuan satu alumni pada satu waktu (cara kerja normal
unit alumni kampus). Kandidat manual terbaru yang disimpan otomatis menjadi identitas
terkonfirmasi ("yang terbaru menang", lihat bagian di atas).

### Fitur "Cari di Internet" (pencarian web berbantuan manusia)

`GET /api/v1/alumni/{id}/search-web` (tombol "Cari di Internet" di halaman detail
alumni pada frontend) memanggil [SerpApi](https://serpapi.com/) untuk mencari **satu**
alumni yang sedang dibuka, dan **hanya menampilkan** hasilnya (judul/tautan/cuplikan) -
tidak ada apa pun yang tersimpan ke database dari endpoint ini. Periset membaca hasil
pencarian sungguhan itu sendiri, memilih yang benar-benar cocok, lalu menyimpannya lewat
`POST /candidates/manual` yang sudah terisi otomatis dari hasil yang dipilih (tetap bisa
diedit sebelum disimpan).

Nama & bobot kepercayaan sumber (halaman "Sumber Data") sungguhan dipakai membangun
query ke SerpApi (`websearch_service._build_queries`) - bukan sekadar tampilan: sumber
dengan domain platform yang dikenal (LinkedIn/Instagram/Facebook/TikTok) dibatasi lewat
`site:`, sumber lain (mis. sumber custom, "Situs Perusahaan/Berita") berbagi satu query
umum, dan bobot menentukan urutan prioritas serta sumber mana yang dikorbankan saat
jumlah query dibatasi (`MAX_QUERIES`). Hanya sumber yang `enabled` yang diikutkan. Tiap
hasil menyertakan `queried_source` supaya periset tahu sumber mana yang menemukannya.

Ini sengaja **tidak** dibuat berjalan otomatis untuk banyak/semua alumni sekaligus -
tetap harus satu alumni, satu pencarian, satu peninjauan manusia sebelum data
tersimpan. Lihat catatan jujur di atas soal kenapa itu jadi batasnya.

Aktifkan dengan mengisi `SERPAPI_KEY` di `.env` (lihat `.env.example`). Tanpa key ini,
tombolnya akan menampilkan pesan error yang jelas, bukan diam-diam gagal.

## Struktur error API

Semua error (validasi request, error HTTP terduga seperti 404, dan error tak
terduga) dikembalikan dalam bentuk konsisten `{"detail": "<pesan>"}` lewat
exception handler global di `main.py`, supaya frontend selalu bisa menampilkan
pesan error secara detail lewat `err.response.data.detail`. Error validasi (422)
tambahan menyertakan `errors: [{"field": ..., "message": ...}]` per kolom yang
gagal divalidasi. Error tak terduga (500) dicatat di log server dan direspons
dengan pesan generik ke klien (detail teknis tidak dibocorkan ke frontend).

## Endpoint utama

| Method | Path | Keterangan |
|---|---|---|
| POST | `/api/v1/auth/register` | Registrasi akun baru (otomatis seed 6 sumber default) |
| POST | `/api/v1/auth/login` | Login, dapat access + refresh token |
| POST | `/api/v1/auth/refresh` | Rotasi token |
| POST | `/api/v1/auth/logout` | Cabut refresh token |
| GET/PUT | `/api/v1/users/me` | Profil akun sendiri |
| GET/POST | `/api/v1/alumni` | Daftar (dengan paginasi/pencarian) & tambah alumni |
| GET/PUT/DELETE | `/api/v1/alumni/{id}` | Detail/ubah/hapus alumni |
| POST | `/api/v1/alumni/{id}/candidates/manual` | Simpan temuan hasil riset manual (data sungguhan) |
| GET | `/api/v1/alumni/{id}/candidates` | Riwayat kandidat manual alumni |
| GET | `/api/v1/alumni/{id}/search-web` | Cari referensi via SerpApi (tidak menyimpan apa pun) |
| GET/POST/PUT/DELETE | `/api/v1/sources` | Kelola sumber data & bobot kepercayaan |
| GET | `/api/v1/dashboard/stats` | Statistik ringkas untuk dashboard |
