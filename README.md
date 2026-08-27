# Daily Project 3 — Sistem Pelacakan Alumni

| Identitas | Keterangan |
|---|---|
| Nama | M. Darma Putra Ramadhan |
| NIM | 202210370311375 |
| Kelas | Rekayasa Kebutuhan A |

## Deskripsi

Daily Project 3 merupakan implementasi web dari rancangan Sistem Pelacakan Alumni pada
Daily Project 2. Aplikasi terdiri dari frontend Vue 3 dan backend FastAPI dengan basis
data SQLite. Sistem mendukung autentikasi, pengelolaan data alumni, impor roster,
pengelolaan sumber pencarian, pencarian web berbantuan manusia, pencatatan kandidat
manual, serta statistik dashboard.

Pengumpulan data pribadi tidak dijalankan secara otomatis dan massal. Hasil pencarian
web hanya ditampilkan untuk ditinjau oleh pengguna; data baru disimpan setelah pengguna
memverifikasi dan memasukkannya secara manual.

## Tautan Produk

| Kebutuhan | Tautan | Status |
|---|---|---|
| Source code GitHub | [github.com/memcpypid/DailyProject3](https://github.com/memcpypid/DailyProject3) | Tersedia |
| Publikasi web | Belum tersedia | Perlu melakukan deployment frontend dan backend, lalu mengganti teks ini dengan URL aplikasi |

> Catatan: URL deployment belum ditemukan di workspace. Tautan publikasi web wajib
> dilengkapi setelah frontend dan backend berhasil di-deploy.

## Teknologi

| Bagian | Teknologi |
|---|---|
| Frontend | Vue 3, Vite, Pinia, Vue Router, Axios, Tailwind CSS |
| Backend | FastAPI, SQLAlchemy, Pydantic, JWT |
| Database | SQLite |
| Pengujian | Pytest, FastAPI TestClient |

## Menjalankan Aplikasi

### Backend

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Dokumentasi API tersedia di `http://127.0.0.1:8000/docs`.

### Frontend

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

Frontend menggunakan API pada `http://localhost:8000` secara default.

## Pengujian

Pengujian dilakukan pada 27 Agustus 2026. Status **Lulus** hanya diberikan pada skenario
yang benar-benar tercakup oleh test otomatis dan berhasil dijalankan.

### Tabel Kasus Uji Backend

| ID | Aspek kualitas | Skenario pengujian | Hasil yang diharapkan | Hasil aktual | Status |
|---|---|---|---|---|---|
| AUTH-01 | Fungsionalitas | Registrasi, login, dan membaca profil pengguna aktif | Akun dapat dibuat, login menghasilkan token, dan profil pengguna dikembalikan | Sesuai harapan | Lulus |
| AUTH-02 | Keamanan | Login menggunakan kata sandi salah | API menolak permintaan dengan HTTP 401 | Sesuai harapan | Lulus |
| AUTH-03 | Integritas data | Registrasi menggunakan email yang sudah terdaftar | API menolak duplikasi dengan HTTP 409 | Sesuai harapan | Lulus |
| AUTH-04 | Keamanan | Mengakses endpoint terlindungi tanpa token | API menolak akses | Sesuai harapan | Lulus |
| AUTH-05 | Keamanan | Melakukan refresh token dan memakai kembali token lama | Token baru diterbitkan dan token lama dicabut | Sesuai harapan | Lulus |
| AUTH-06 | Keamanan | Logout lalu menggunakan refresh token yang telah dicabut | Refresh token tidak dapat dipakai kembali | Sesuai harapan | Lulus |
| ALM-01 | Fungsionalitas | Membuat dan membaca detail alumni | Data tersimpan dan detail yang benar dikembalikan | Sesuai harapan | Lulus |
| ALM-02 | Fungsionalitas | Menampilkan daftar alumni dengan paginasi | Daftar dan metadata paginasi dikembalikan dengan benar | Sesuai harapan | Lulus |
| ALM-03 | Fungsionalitas | Memperbarui lalu menghapus data alumni | Perubahan tersimpan dan data dapat dihapus | Sesuai harapan | Lulus |
| ALM-04 | Keamanan dan privasi | Akun lain mencoba mengakses data alumni pengguna | Data terisolasi untuk setiap akun | Sesuai harapan | Lulus |
| IMP-01 | Fungsionalitas | Mengimpor roster dari berkas XLSX valid | Baris valid dibuat sebagai data alumni | Sesuai harapan | Lulus |
| IMP-02 | Keandalan | Mengimpor kembali NIM yang sama | Impor bersifat idempoten dan melewati NIM yang sudah ada | Sesuai harapan | Lulus |
| IMP-03 | Integritas data | Berkas impor memuat NIM ganda | Duplikasi di dalam berkas terdeteksi | Sesuai harapan | Lulus |
| IMP-04 | Keandalan | Menjalankan impor dalam mode `dry-run` | Validasi berjalan tanpa menyimpan data | Sesuai harapan | Lulus |
| IMP-05 | Fungsionalitas | Mengimpor data menggunakan batas jumlah baris | Jumlah baris yang diproses mengikuti nilai `limit` | Sesuai harapan | Lulus |
| IMP-06 | Validasi | Mengimpor berkas dengan kolom wajib yang hilang | Berkas ditolak dengan pesan kesalahan | Sesuai harapan | Lulus |
| IMP-07 | Validasi | Mengimpor ekstensi berkas yang tidak didukung | Berkas ditolak | Sesuai harapan | Lulus |
| IMP-08 | Keamanan | Mengakses impor tanpa autentikasi | Permintaan ditolak | Sesuai harapan | Lulus |
| IMP-09 | Integritas data | Baris impor tidak memiliki nama atau NIM | Baris tidak valid dilewati | Sesuai harapan | Lulus |
| SRC-01 | Fungsionalitas | Registrasi akun baru | Enam sumber data default otomatis dibuat | Sesuai harapan | Lulus |
| SRC-02 | Fungsionalitas | Membuat, mengubah, dan menghapus sumber data | Seluruh operasi CRUD sumber berhasil | Sesuai harapan | Lulus |
| SRC-03 | Validasi | Menyimpan bobot kepercayaan di luar rentang valid | Data ditolak oleh validasi | Sesuai harapan | Lulus |
| TRK-01 | Fungsionalitas | Menambahkan kandidat hasil verifikasi manual | Kandidat menjadi identitas alumni terkonfirmasi | Sesuai harapan | Lulus |
| TRK-02 | Konsistensi | Menambahkan kandidat manual baru pada alumni yang sama | Kandidat terbaru menggantikan konfirmasi sebelumnya | Sesuai harapan | Lulus |
| TRK-03 | Validasi | Menambahkan kandidat dengan alumni atau sumber yang tidak valid | Permintaan ditolak | Sesuai harapan | Lulus |
| WEB-01 | Keandalan | Pencarian web dijalankan tanpa `SERPAPI_KEY` | API mengembalikan pesan konfigurasi yang jelas | Sesuai harapan | Lulus |
| WEB-02 | Fungsionalitas dan privasi | Pencarian web satu alumni menghasilkan referensi | Hasil dikembalikan untuk tinjauan manusia tanpa disimpan otomatis | Sesuai harapan | Lulus |
| WEB-03 | Validasi | Pencarian web untuk alumni yang tidak ada | API mengembalikan HTTP 404 | Sesuai harapan | Lulus |
| WEB-04 | Ketertelusuran | Membentuk query dari nama dan bobot sumber | Query memakai konfigurasi sumber yang aktif | Sesuai harapan | Lulus |
| WEB-05 | Efisiensi | Jumlah query melebihi batas maksimum | Query dibatasi dan sumber berbobot lebih tinggi diprioritaskan | Sesuai harapan | Lulus |

### Tabel Verifikasi Teknis

| ID | Aspek kualitas | Perintah | Hasil aktual | Status |
|---|---|---|---|---|
| VER-01 | Keandalan backend | `cd backend && ./venv/bin/python -m pytest -q` | 31 test lulus dalam 11,89 detik; terdapat 1 peringatan deprecasi dari FastAPI TestClient | Lulus |
| VER-02 | Build frontend | `cd frontend && npm run build` | Build produksi Vite berhasil; 1.913 modul ditransformasi | Lulus |

### Ringkasan Hasil

| Komponen | Lulus | Gagal | Total |
|---|---:|---:|---:|
| Test otomatis backend | 31 | 0 | 31 |
| Verifikasi build frontend | 1 | 0 | 1 |
| **Keseluruhan** | **32** | **0** | **32** |

### Cakupan yang Belum Diuji

| Aspek | Pengujian lanjutan yang diperlukan |
|---|---|
| Usability | Uji tugas dengan pengguna: login, mencari alumni, menambah temuan manual, dan membaca hasil |
| Performa | Uji waktu respons API dan beban bersamaan pada ukuran roster representatif |
| Kompatibilitas | Uji antarmuka pada Chrome, Firefox, Safari, serta ukuran layar desktop dan mobile |
| Keamanan lanjutan | Audit dependensi, pengujian rate limit, konfigurasi produksi, dan pengujian penetrasi |
| Deployment | Smoke test terhadap URL frontend dan backend setelah aplikasi dipublikasikan |

## Struktur Proyek

```text
DailyProject3/
├── backend/   # API FastAPI, database, service, repository, dan test
├── frontend/  # Aplikasi Vue 3
└── README.md  # Dokumentasi dan hasil pengujian
```

Dokumentasi teknis lebih rinci tersedia pada
[`backend/README.md`](backend/README.md), [`frontend/README.md`](frontend/README.md),
dan [`deploy/README.md`](deploy/README.md).
# DailyProject3
